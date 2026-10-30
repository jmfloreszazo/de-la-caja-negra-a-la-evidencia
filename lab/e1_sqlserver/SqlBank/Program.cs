using System.Data;
using System.Diagnostics;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Data.SqlClient;

// E1c: disposable SQL Server 2022 transaction candidate, not a mainframe
// capacity test. Never connect the experiment to customer or shared databases.
const string DatabaseName = "E1SqlLab";
if (args.Length == 0) return 4;
try
{
    var command = args[0];
    if (command == "version")
    {
        using var db = Open("master");
        using var query = new SqlCommand(
            "SELECT CONVERT(NVARCHAR(128), SERVERPROPERTY('ProductVersion'))", db);
        Console.WriteLine(query.ExecuteScalar());
        return 0;
    }
    if (command == "init" && args.Length == 2)
    {
        using (var master = Open("master"))
        {
            Exec(master, null,
                "IF DB_ID(N'E1SqlLab') IS NULL EXEC(N'CREATE DATABASE [E1SqlLab]')");
            Exec(master, null, "ALTER DATABASE [E1SqlLab] SET ALLOW_SNAPSHOT_ISOLATION ON");
        }
        using var db = Open(DatabaseName);
        using var script = new SqlCommand(File.ReadAllText(args[1]), db)
        {
            CommandTimeout = 60
        };
        script.ExecuteNonQuery();
        Console.WriteLine("{\"status\":\"INITIALIZED\"}");
        return 0;
    }
    if (command == "snapshot")
    {
        using var db = Open(DatabaseName);
        var result = new Dictionary<string, List<object?[]>>();
        foreach (var (name, sql) in new[]
        {
            ("accounts", "SELECT id,balance FROM dbo.accounts ORDER BY id"),
            ("operations", "SELECT id,src,dst,amount,status FROM dbo.operations ORDER BY id"),
            ("postings", "SELECT op,account,delta FROM dbo.postings ORDER BY op,account"),
            ("outbox", "SELECT op,event FROM dbo.outbox ORDER BY op")
        })
        {
            var rows = new List<object?[]>();
            using var cmd = new SqlCommand(sql, db);
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                var row = new object?[reader.FieldCount];
                reader.GetValues(row);
                rows.Add(row);
            }
            result[name] = rows;
        }
        Console.WriteLine(JsonSerializer.Serialize(result));
        return 0;
    }
    if (command == "hold-account" && args.Length == 3)
    {
        var id = int.Parse(args[1]);
        var milliseconds = int.Parse(args[2]);
        if (id is < 1 or > 16 || milliseconds is < 1 or > 30000)
            throw new ArgumentException("Invalid disposable lock parameters");
        using var db = Open(DatabaseName);
        using var tx = db.BeginTransaction(IsolationLevel.ReadCommitted);
        _ = Scalar(tx, "SELECT balance FROM dbo.accounts WITH (UPDLOCK, ROWLOCK) WHERE id=@p0", id)
            ?? throw new InvalidOperationException("Missing lock account");
        Console.WriteLine("LOCKED");
        Console.Out.Flush();
        Thread.Sleep(milliseconds);
        tx.Commit();
        return 0;
    }
    if (command == "transfer" && args.Length >= 5)
    {
        var options = new Dictionary<string, string>();
        if ((args.Length - 5) % 2 != 0) return 4;
        for (int i = 5; i < args.Length; i += 2)
            options.Add(args[i], args[i + 1]);
        if (options.Keys.Any(key => key is not ("--fault" or "--lock-order" or "--pause-first-lock")))
            return 4;
        var op = args[1];
        var src = int.Parse(args[2]);
        var dst = int.Parse(args[3]);
        var amount = long.Parse(args[4]);
        var fault = options.GetValueOrDefault("--fault", "none");
        var order = options.GetValueOrDefault("--lock-order", "canonical");
        var pause = int.Parse(options.GetValueOrDefault("--pause-first-lock", "0"));
        var outcome = Transfer(op, src, dst, amount, fault, order, pause);
        Console.WriteLine(JsonSerializer.Serialize(outcome));
        return outcome.status == "RETRY_EXHAUSTED" ? 7 : 0;
    }
    return 4;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message);
    return 5;
}

static SqlConnection Open(string catalog)
{
    var password = Environment.GetEnvironmentVariable("E1_SQL_PASSWORD");
    if (string.IsNullOrWhiteSpace(password))
        throw new InvalidOperationException("E1_SQL_PASSWORD is required");
    var builder = new SqlConnectionStringBuilder
    {
        DataSource = Environment.GetEnvironmentVariable("E1_SQL_HOST") ?? "127.0.0.1,14333",
        InitialCatalog = catalog,
        UserID = "sa",
        Password = password,
        Encrypt = SqlConnectionEncryptOption.Mandatory,
        TrustServerCertificate = true, // Disposable loopback lab ONLY.
        ConnectTimeout = 15,
        Pooling = false,
        ApplicationName = "E1c-Disposable-Synthetic-Lab"
    };
    var db = new SqlConnection(builder.ConnectionString);
    db.Open();
    return db;
}

static SqlCommand Command(SqlConnection db, SqlTransaction? tx, string text,
    params object[] values)
{
    var cmd = new SqlCommand(text, db, tx) { CommandTimeout = 15 };
    for (int i = 0; i < values.Length; i++)
        cmd.Parameters.AddWithValue("@p" + i, values[i]);
    return cmd;
}

static int Exec(SqlConnection db, SqlTransaction? tx, string text,
    params object[] values)
{
    using var cmd = Command(db, tx, text, values);
    return cmd.ExecuteNonQuery();
}

static object? Scalar(SqlTransaction tx, string text, params object[] values)
{
    using var cmd = Command(tx.Connection!, tx, text, values);
    return cmd.ExecuteScalar();
}

static Outcome Transfer(string op, int src, int dst, long amount,
    string fault, string order, int pause)
{
    if (!Regex.IsMatch(op, @"\A[A-Za-z0-9-]{1,80}\z") ||
        src is < 1 or > 16 || dst is < 1 or > 16 ||
        src == dst || amount is <= 0 or > 1_000_000_000_000)
        throw new ArgumentException("Invalid transfer");
    if (fault is not ("none" or "throw-after-debit" or
                      "crash-after-debit" or "lost-response"))
        throw new ArgumentException("Unsupported injected fault");
    if (order is not ("canonical" or "source-first") || pause is < 0 or > 2500)
        throw new ArgumentException("Unsupported test lock order/pause");

    var started = Stopwatch.StartNew();
    var retryNumbers = new List<int>();
    for (var attempt = 0; attempt < 6; attempt++)
    {
        try
        {
            using var db = Open("E1SqlLab");
            using var tx = db.BeginTransaction(IsolationLevel.ReadCommitted);
            Exec(db, tx, "SET LOCK_TIMEOUT " + (order == "source-first" ? "6000" : "750"));
            // An application transaction lock serializes idempotent operations.
            // The unique constraint is still the final consistency defense.
            var lockResult = Convert.ToInt32(Scalar(tx,
                "DECLARE @rc INT; EXEC @rc=sp_getapplock " +
                "@Resource=@p0, @LockMode='Exclusive', " +
                "@LockOwner='Transaction', @LockTimeout=750; SELECT @rc",
                "e1c:" + op));
            if (lockResult < 0)
                throw new ApplicationLockTimeoutException();

            using var prior = Command(db, tx,
                "SELECT src,dst,amount,status FROM dbo.operations WHERE id=@p0", op);
            object[]? old = null;
            using (var reader = prior.ExecuteReader())
            {
                if (reader.Read())
                {
                    old = new object[4];
                    reader.GetValues(old);
                }
            }
            string verdict;
            if (old is not null)
            {
                bool same = Convert.ToInt32(old[0]) == src &&
                            Convert.ToInt32(old[1]) == dst &&
                            Convert.ToInt64(old[2]) == amount;
                verdict = same ? "DUPLICATE_" + old[3] : "ID_CONFLICT";
            }
            else
            {
                var ordered = order == "canonical"
                    ? new[] { src, dst }.Order().ToArray()
                    : new[] { src, dst };
                for (int i = 0; i < ordered.Length; i++)
                {
                    var found = Scalar(tx,
                        "SELECT balance FROM dbo.accounts WITH (UPDLOCK,ROWLOCK) WHERE id=@p0",
                        ordered[i]);
                    if (found is null)
                        throw new InvalidOperationException("Account missing");
                    if (i == 0 && attempt == 0 && pause != 0)
                        Thread.Sleep(pause);
                }
                var affected = Exec(db, tx,
                    "UPDATE dbo.accounts SET balance=balance-@p0 " +
                    "WHERE id=@p1 AND balance>=@p0", amount, src);
                if (affected == 1)
                {
                    if (fault == "throw-after-debit")
                        throw new InvalidOperationException("Injected exception after debit");
                    if (fault == "crash-after-debit")
                        Environment.Exit(91);
                    Exec(db, tx,
                        "UPDATE dbo.accounts SET balance=balance+@p0 WHERE id=@p1",
                        amount, dst);
                }
                verdict = affected == 1 ? "COMMITTED" : "REJECTED";
                Exec(db, tx,
                    "INSERT dbo.operations(id,src,dst,amount,status) " +
                    "VALUES(@p0,@p1,@p2,@p3,@p4)", op, src, dst, amount, verdict);
                if (affected == 1)
                {
                    Exec(db, tx,
                        "INSERT dbo.postings(op,account,delta) VALUES" +
                        "(@p0,@p1,@p2),(@p0,@p3,@p4)",
                        op, src, -amount, dst, amount);
                    Exec(db, tx, "INSERT dbo.outbox(op,event) VALUES(@p0,@p1)",
                        op, "TransferCommitted");
                }
            }
            tx.Commit();
            if (fault == "lost-response" && verdict == "COMMITTED")
                Environment.Exit(92);
            return new Outcome(verdict, retryNumbers.Count,
                Math.Round(started.Elapsed.TotalMilliseconds, 3), retryNumbers);
        }
        catch (SqlException ex) when (ex.Number is 1205 or 1222 or 2601 or 2627 or 3960)
        {
            retryNumbers.Add(ex.Number);
            if (attempt < 5) Thread.Sleep(25 * (attempt + 1));
        }
        catch (ApplicationLockTimeoutException)
        {
            retryNumbers.Add(-1);
            if (attempt < 5) Thread.Sleep(25 * (attempt + 1));
        }
    }
    return new Outcome("RETRY_EXHAUSTED", retryNumbers.Count,
        Math.Round(started.Elapsed.TotalMilliseconds, 3), retryNumbers);
}

sealed class ApplicationLockTimeoutException : Exception { }
record Outcome(string status, int retries, double elapsedMs, List<int> retrySqlErrors);
