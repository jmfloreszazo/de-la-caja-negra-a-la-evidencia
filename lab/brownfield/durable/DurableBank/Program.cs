using System.Data;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Npgsql;

// A disposable synthetic brownfield capability lab. This is not a bank gateway,
// a mainframe fence, a mandate engine, or a TODM G6 release authorization.
try
{
    if (Environment.GetEnvironmentVariable("BROWNFIELD_DISPOSABLE") != "YES")
        throw new InvalidOperationException("Explicit disposable-only opt-in is required.");
    string connectionString = Environment.GetEnvironmentVariable("BROWNFIELD_PG_NPGSQL")
        ?? throw new InvalidOperationException("BROWNFIELD_PG_NPGSQL is required.");
    var builder = new NpgsqlConnectionStringBuilder(connectionString);
    if (builder.Database is null || builder.Database != "bf_lab")
        throw new InvalidOperationException("The database must be the dedicated bf_lab fixture.");
    if (args.Length == 0) return 4;

    if (args[0] == "transfer" && args.Length is >= 7 and <= 8)
    {
        var result = Transfer(connectionString, args[1],
            int.Parse(args[2], CultureInfo.InvariantCulture),
            int.Parse(args[3], CultureInfo.InvariantCulture),
            long.Parse(args[4], CultureInfo.InvariantCulture), args[5],
            long.Parse(args[6], CultureInfo.InvariantCulture),
            args.Length == 8 ? args[7] : "none");
        Console.WriteLine(Json(result));
        return result.Status == "RETRY_EXHAUSTED" ? 7 : 0;
    }
    if (args[0] == "balance" && args.Length == 3)
    {
        Console.WriteLine(Json(Balance(connectionString,
            int.Parse(args[1], CultureInfo.InvariantCulture),
            long.Parse(args[2], CultureInfo.InvariantCulture))));
        return 0;
    }
    if (args[0] == "switch" && args.Length == 6)
    {
        Console.WriteLine(Json(SwitchWriter(connectionString, args[1],
            long.Parse(args[2], CultureInfo.InvariantCulture), args[3],
            long.Parse(args[4], CultureInfo.InvariantCulture),
            long.Parse(args[5], CultureInfo.InvariantCulture))));
        return 0;
    }
    return 4;
}
catch (Exception ex)
{
    Console.Error.WriteLine($"{ex.GetType().Name}: {ex.Message}");
    return 5;
}

static string Json(object value) => JsonSerializer.Serialize(value,
    new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

static bool ValidWriter(string writer) => writer is "legacy" or "candidate";

static string Fingerprint(int source, int destination, long amount)
{
    // Exact decimal integer values, fixed scope and currency. This is a fixture
    // fingerprint and deliberately does not attest real customer authorization.
    string canonical = $"v1|source={source}|destination={destination}|amountMinor={amount}|currency=EUR|mandate=SYNTHETIC";
    return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical)))
        .ToLowerInvariant();
}

static TransferResult Transfer(string dsn, string id, int source, int destination,
    long amount, string writer, long expectedEpoch, string fault)
{
    if (!Regex.IsMatch(id, "^[A-Za-z0-9-]{1,80}$", RegexOptions.CultureInvariant)
        || source is < 1 or > 16 || destination is < 1 or > 16
        || source == destination || amount is <= 0 or > 1_000_000_000_000L
        || !ValidWriter(writer) || expectedEpoch < 1)
        throw new ArgumentException("Invalid synthetic transfer scope.");
    if (fault is not ("none" or "crash-before-commit" or "pause-before-commit" or "lost-ack"))
        throw new ArgumentException("Unsupported fault injection.");

    string fingerprint = Fingerprint(source, destination, amount);
    var sqlstates = new List<string>();
    for (int attempt = 0; attempt < 6; attempt++)
    {
        try
        {
            using var conn = new NpgsqlConnection(dsn);
            conn.Open();
            using var tx = conn.BeginTransaction(IsolationLevel.ReadCommitted);
            Exec(tx, "SET LOCAL lock_timeout = '750ms'");

            // Shared row lock prevents an epoch switch before this transaction
            // has finished. The commit clock is a DIFFERENT row, avoiding
            // upgrade deadlocks between concurrent shared authority readers.
            var authority = Authority(tx, "FOR SHARE");
            Exec(tx, "SELECT pg_advisory_xact_lock(hashtextextended($1, 0))", id);
            var existing = Existing(tx, id);
            if (existing is not null)
            {
                string duplicate = existing.Value.fingerprint == fingerprint
                    ? "DUPLICATE_" + existing.Value.status : "ID_CONFLICT";
                tx.Commit();
                return new TransferResult(duplicate, Clock(conn), sqlstates.Count, sqlstates);
            }
            if (authority.writer != writer || authority.epoch != expectedEpoch)
            {
                tx.Rollback();
                return new TransferResult("FENCED_WRITER_OR_EPOCH", -1, sqlstates.Count, sqlstates);
            }

            foreach (int account in new[] { source, destination }.Order())
            {
                if (Scalar(tx, "SELECT id FROM brownfield.accounts WHERE id=$1 FOR UPDATE", account) is null)
                {
                    tx.Rollback();
                    return new TransferResult("MISSING_ACCOUNT", -1, sqlstates.Count, sqlstates);
                }
            }
            int debited = Exec(tx,
                "UPDATE brownfield.accounts SET balance=balance-$1 WHERE id=$2 AND balance >= $1",
                amount, source);
            string verdict = debited == 1 ? "COMMITTED" : "REJECTED";
            if (debited == 1)
            {
                if (fault == "crash-before-commit") Environment.Exit(91);
                if (fault == "pause-before-commit")
                {
                    Console.WriteLine("UNCOMMITTED_DEBIT_APPLIED");
                    Console.Out.Flush();
                    Thread.Sleep(TimeSpan.FromSeconds(20));
                }
                Exec(tx, "UPDATE brownfield.accounts SET balance=balance+$1 WHERE id=$2",
                    amount, destination);
            }
            Exec(tx, @"INSERT INTO brownfield.operations
                (id, fingerprint, writer, epoch, src, dst, amount, status)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)",
                id, fingerprint, writer, expectedEpoch, source, destination, amount, verdict);

            long watermark = Convert.ToInt64(Scalar(tx,
                @"UPDATE brownfield.commit_clock SET watermark=watermark+1
                  WHERE id=1 RETURNING watermark") ?? 0L);
            if (debited == 1)
            {
                Exec(tx, "UPDATE brownfield.accounts SET version=$1 WHERE id IN ($2,$3)",
                    watermark, source, destination);
                Exec(tx, @"INSERT INTO brownfield.postings(operation_id,account_id,delta)
                           VALUES ($1,$2,$3),($1,$4,$5)",
                    id, source, -amount, destination, amount);
                Exec(tx, "INSERT INTO brownfield.outbox(operation_id,event_type) VALUES ($1,$2)",
                    id, "TransferCommitted");
            }
            tx.Commit();
            if (fault == "lost-ack" && verdict == "COMMITTED") Environment.Exit(92);
            return new TransferResult(verdict, watermark, sqlstates.Count, sqlstates);
        }
        catch (PostgresException ex) when (ex.SqlState is "40P01" or "40001" or "55P03")
        {
            sqlstates.Add(ex.SqlState);
            Thread.Sleep(25 * (attempt + 1));
        }
    }
    return new TransferResult("RETRY_EXHAUSTED", -1, sqlstates.Count, sqlstates);
}

static object Balance(string dsn, int account, long minimumVersion)
{
    if (account is < 1 or > 16 || minimumVersion < 0)
        throw new ArgumentException("Invalid balance query.");
    using var conn = new NpgsqlConnection(dsn);
    conn.Open();
    using var tx = conn.BeginTransaction(IsolationLevel.RepeatableRead);
    long watermark = Convert.ToInt64(Scalar(tx,
        "SELECT watermark FROM brownfield.commit_clock WHERE id=1") ?? 0L);
    using var cmd = Command(tx,
        "SELECT balance,version FROM brownfield.accounts WHERE id=$1", account);
    using var reader = cmd.ExecuteReader();
    if (!reader.Read()) return new { status = "MISSING_ACCOUNT", watermark };
    long balance = reader.GetInt64(0), changedAt = reader.GetInt64(1);
    return new
    {
        status = watermark < minimumVersion ? "BELOW_MINIMUM_VERSION" : "AUTHORITATIVE",
        balanceMinor = balance, accountVersion = changedAt, watermark,
        source = "DISPOSABLE_POSTGRESQL_NOT_PROJECTION"
    };
}

static object SwitchWriter(string dsn, string expectedWriter, long expectedEpoch,
    string targetWriter, long expectedWatermark, long expectedOperationCount)
{
    if (!ValidWriter(expectedWriter) || !ValidWriter(targetWriter)
        || expectedWriter == targetWriter || expectedEpoch < 1
        || expectedWatermark < 0 || expectedOperationCount < 0)
        throw new ArgumentException("Invalid synthetic cutover request.");
    using var conn = new NpgsqlConnection(dsn);
    conn.Open();
    using var tx = conn.BeginTransaction();
    // Exclusive lock must wait for every transfer's FOR SHARE fence to finish.
    var current = Authority(tx, "FOR UPDATE");
    long watermark = Convert.ToInt64(Scalar(tx,
        "SELECT watermark FROM brownfield.commit_clock WHERE id=1") ?? 0L);
    long count = Convert.ToInt64(Scalar(tx,
        "SELECT count(*) FROM brownfield.operations") ?? 0L);
    long committed = Convert.ToInt64(Scalar(tx,
        "SELECT count(*) FROM brownfield.operations WHERE status='COMMITTED'") ?? 0L);
    long postings = Convert.ToInt64(Scalar(tx,
        "SELECT count(*) FROM brownfield.postings") ?? 0L);
    long outbox = Convert.ToInt64(Scalar(tx,
        "SELECT count(*) FROM brownfield.outbox") ?? 0L);
    bool consistent = watermark == count && postings == 2 * committed
        && outbox == committed;
    if (current.writer != expectedWriter || current.epoch != expectedEpoch
        || watermark != expectedWatermark || count != expectedOperationCount
        || !consistent)
    {
        tx.Rollback();
        return new { status = "CUTOVER_BLOCKED", current.writer, current.epoch,
            watermark, count, consistent, todmG6 = "BLOCK" };
    }
    Exec(tx, "UPDATE brownfield.authority SET writer=$1,epoch=epoch+1 WHERE id=1", targetWriter);
    tx.Commit();
    return new { status = "SYNTHETIC_SWITCH", writer = targetWriter,
        epoch = expectedEpoch + 1, watermark, count, todmG6 = "BLOCK" };
}

static (string writer, long epoch) Authority(NpgsqlTransaction tx, string lockClause)
{
    // The lock clause is an internal constant from two explicit call sites.
    using var cmd = Command(tx,
        "SELECT writer,epoch FROM brownfield.authority WHERE id=1 " + lockClause);
    using var reader = cmd.ExecuteReader();
    if (!reader.Read()) throw new InvalidOperationException("Authority not initialized.");
    return (reader.GetString(0), reader.GetInt64(1));
}

static (string fingerprint, string status)? Existing(NpgsqlTransaction tx, string id)
{
    using var cmd = Command(tx,
        "SELECT fingerprint,status FROM brownfield.operations WHERE id=$1", id);
    using var reader = cmd.ExecuteReader();
    return reader.Read() ? (reader.GetString(0), reader.GetString(1)) : null;
}

static long Clock(NpgsqlConnection conn)
{
    using var cmd = new NpgsqlCommand("SELECT watermark FROM brownfield.commit_clock WHERE id=1", conn);
    return Convert.ToInt64(cmd.ExecuteScalar() ?? 0L);
}

static NpgsqlCommand Command(NpgsqlTransaction tx, string sql, params object[] values)
{
    var cmd = new NpgsqlCommand(sql, tx.Connection, tx);
    foreach (var value in values) cmd.Parameters.Add(new NpgsqlParameter { Value = value });
    return cmd;
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

record TransferResult(string Status, long Watermark, int Retries, List<string> RetrySqlstates);
