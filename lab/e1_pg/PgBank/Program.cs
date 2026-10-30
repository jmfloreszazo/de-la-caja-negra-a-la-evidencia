using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using Npgsql;

// E1b: same persisted contract as E1a, but an independent .NET 10 / Npgsql
// candidate. A passing parity test is not a mainframe capacity benchmark.
if (args.Length == 0) return 4;
var conninfo = Environment.GetEnvironmentVariable("E1_PG_NPGSQL")
    ?? "Host=127.0.0.1;Port=55432;Database=e1lab;Username=postgres;Password=e1local;Pooling=false";
if (args[0] == "version")
{
    using var db = new NpgsqlConnection(conninfo);
    db.Open();
    using var cmd = new NpgsqlCommand("SHOW server_version", db);
    Console.WriteLine(cmd.ExecuteScalar());
    return 0;
}
if (args[0] != "transfer" || args.Length < 5) return 4;
try
{
    var op = args[1];
    int src = int.Parse(args[2]), dst = int.Parse(args[3]);
    long amount = long.Parse(args[4]);
    var fault = args.Length > 6 && args[5] == "--fault" ? args[6] : "none";
    var result = Run(conninfo, op, src, dst, amount, fault);
    Console.WriteLine(JsonSerializer.Serialize(result));
    return result.status == "RETRY_EXHAUSTED" ? 7 : 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.Message);
    return 5;
}

static Outcome Run(string connectString, string op, int src, int dst, long amount, string fault)
{
    if (!Regex.IsMatch(op, "^[A-Za-z0-9-]{1,80}$") ||
        src is < 1 or > 16 || dst is < 1 or > 16 || src == dst ||
        amount is <= 0 or > 1_000_000_000_000)
        throw new ArgumentException("Invalid transfer parameters");
    if (!new[] { "none", "throw-after-debit", "crash-after-debit", "lost-response" }.Contains(fault))
        throw new ArgumentException("Unsupported fault");
    var watch = Stopwatch.StartNew();
    var retried = new List<string>();
    for (int attempt = 0; attempt < 6; attempt++)
    {
        try
        {
            using var db = new NpgsqlConnection(connectString);
            db.Open();
            using var tx = db.BeginTransaction();
            Exec(tx, "SET LOCAL lock_timeout = '750ms'");
            Exec(tx, "SELECT pg_advisory_xact_lock(hashtextextended($1,0))", op);
            var old = Rows(tx, "SELECT src,dst,amount,status FROM operations WHERE id=$1", op);
            string verdict;
            if (old.Count != 0)
            {
                var r = old[0];
                var same = Convert.ToInt32(r[0]) == src &&
                           Convert.ToInt32(r[1]) == dst &&
                           Convert.ToInt64(r[2]) == amount;
                verdict = same ? "DUPLICATE_" + r[3] : "ID_CONFLICT";
            }
            else
            {
                foreach (var id in new[] { src, dst }.Order())
                {
                    if (Scalar(tx, "SELECT id FROM accounts WHERE id=$1 FOR UPDATE", id) is null)
                        throw new InvalidOperationException("Account missing");
                }
                var affected = Exec(tx,
                    "UPDATE accounts SET balance=balance-$1 WHERE id=$2 AND balance >= $1",
                    amount, src);
                if (affected == 1)
                {
                    if (fault == "throw-after-debit")
                        throw new InvalidOperationException("Injected exception after debit");
                    if (fault == "crash-after-debit") Environment.Exit(91);
                    Exec(tx, "UPDATE accounts SET balance=balance+$1 WHERE id=$2",
                        amount, dst);
                }
                verdict = affected == 1 ? "COMMITTED" : "REJECTED";
                Exec(tx,
                    "INSERT INTO operations(id,src,dst,amount,status) VALUES($1,$2,$3,$4,$5)",
                    op, src, dst, amount, verdict);
                if (affected == 1)
                {
                    Exec(tx,
                        "INSERT INTO postings(op,account,delta) VALUES($1,$2,$3),($1,$4,$5)",
                        op, src, -amount, dst, amount);
                    Exec(tx, "INSERT INTO outbox(op,event) VALUES($1,$2)",
                        op, "TransferCommitted");
                }
            }
            tx.Commit();
            if (fault == "lost-response" && verdict == "COMMITTED")
                Environment.Exit(92);
            return new Outcome(verdict, retried.Count,
                Math.Round(watch.Elapsed.TotalMilliseconds, 3), retried);
        }
        catch (PostgresException ex) when (new[] { "40P01", "40001", "55P03", "23505" }
            .Contains(ex.SqlState))
        {
            retried.Add(ex.SqlState);
            Thread.Sleep(25 * (attempt + 1));
        }
    }
    return new Outcome("RETRY_EXHAUSTED", retried.Count,
        Math.Round(watch.Elapsed.TotalMilliseconds, 3), retried);
}

static NpgsqlCommand Command(NpgsqlTransaction tx, string sql, params object[] values)
{
    var command = new NpgsqlCommand(sql, tx.Connection, tx);
    foreach (var value in values)
        command.Parameters.Add(new NpgsqlParameter { Value = value });
    return command;
}
static int Exec(NpgsqlTransaction tx, string sql, params object[] values)
{
    using var cmd = Command(tx, sql, values);
    return cmd.ExecuteNonQuery();
}
static object? Scalar(NpgsqlTransaction tx, string sql, params object[] values)
{
    using var cmd = Command(tx, sql, values);
    return cmd.ExecuteScalar();
}
static List<object[]> Rows(NpgsqlTransaction tx, string sql, params object[] values)
{
    using var cmd = Command(tx, sql, values);
    using var reader = cmd.ExecuteReader();
    var rows = new List<object[]>();
    while (reader.Read())
    {
        var row = new object[reader.FieldCount];
        reader.GetValues(row);
        rows.Add(row);
    }
    return rows;
}
record Outcome(string status, int retries, double elapsedMs, List<string> retry_sqlstates);
