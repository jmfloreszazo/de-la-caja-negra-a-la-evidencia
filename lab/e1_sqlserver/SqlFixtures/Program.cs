using System.Data;
using System.Text.Json;
using Microsoft.Data.SqlClient;

// Test-only destructive fixtures, independently compiled from SqlBank and
// SqlOracle. Never connect to any non-disposable SQL Server instance.
if (Environment.GetEnvironmentVariable("E1_SQL_TEST_ADMIN") != "YES_DISPOSABLE")
{
    Console.Error.WriteLine("Destructive fixtures require E1_SQL_TEST_ADMIN=YES_DISPOSABLE");
    return 4;
}
if (args.Length == 0) return 4;
try
{
    var builder = new SqlConnectionStringBuilder
    {
        DataSource = Environment.GetEnvironmentVariable("E1_SQL_HOST")
            ?? "127.0.0.1,14333",
        InitialCatalog = "E1SqlLab",
        UserID = "sa",
        Password = Environment.GetEnvironmentVariable("E1_SQL_PASSWORD")
            ?? throw new InvalidOperationException("Missing disposable lab password"),
        Encrypt = SqlConnectionEncryptOption.Mandatory,
        TrustServerCertificate = true,
        ConnectTimeout = 3,
        Pooling = false
    };
    if (!builder.DataSource.StartsWith("127.0.0.1,"))
        throw new InvalidOperationException("Only loopback test SQL Server is allowed");
    using var db = new SqlConnection(builder.ConnectionString);
    db.Open();

    if (args[0] == "corrupt")
    {
        using var tx = db.BeginTransaction();
        using var read = new SqlCommand(
            "SELECT TOP (1) op,account,delta FROM dbo.postings ORDER BY op,account",
            db, tx);
        string op;
        int account;
        long delta;
        using (var reader = read.ExecuteReader())
        {
            if (!reader.Read()) throw new InvalidOperationException("No posting");
            op = reader.GetString(0);
            account = reader.GetInt32(1);
            delta = reader.GetInt64(2);
        }
        using var remove = new SqlCommand(
            "DELETE dbo.postings WHERE op=@op AND account=@account", db, tx);
        remove.Parameters.AddWithValue("@op", op);
        remove.Parameters.AddWithValue("@account", account);
        if (remove.ExecuteNonQuery() != 1) throw new InvalidOperationException("Delete failed");
        tx.Commit();
        Console.WriteLine(JsonSerializer.Serialize(new { op, account, delta }));
        return 0;
    }
    if (args[0] == "restore" && args.Length == 4)
    {
        using var cmd = new SqlCommand(
            "INSERT dbo.postings(op,account,delta) VALUES(@op,@account,@delta)", db);
        cmd.Parameters.AddWithValue("@op", args[1]);
        cmd.Parameters.AddWithValue("@account", int.Parse(args[2]));
        cmd.Parameters.AddWithValue("@delta", long.Parse(args[3]));
        if (cmd.ExecuteNonQuery() != 1) throw new InvalidOperationException("Restore failed");
        Console.WriteLine("{\"status\":\"RESTORED\"}");
        return 0;
    }
    if (args[0] == "reset-duty")
    {
        using var cmd = new SqlCommand("UPDATE dbo.duty SET active=1", db);
        if (cmd.ExecuteNonQuery() != 2) throw new InvalidOperationException("Duty seed missing");
        return 0;
    }
    if (args[0] == "duty-count")
    {
        using var cmd = new SqlCommand(
            "SELECT COUNT(*) FROM dbo.duty WHERE active=1", db);
        Console.WriteLine(JsonSerializer.Serialize(new {
            remainingActive = Convert.ToInt32(cmd.ExecuteScalar())
        }));
        return 0;
    }
    if (args[0] == "disable-duty" && args.Length == 3)
    {
        int id = int.Parse(args[1]);
        var isolation = args[2] switch
        {
            "snapshot" => IsolationLevel.Snapshot,
            "serializable" => IsolationLevel.Serializable,
            _ => throw new ArgumentException("Invalid isolation")
        };
        var retries = new List<int>();
        for (int attempt = 0; attempt < 5; attempt++)
        {
            try
            {
                using var session = new SqlConnection(builder.ConnectionString);
                session.Open();
                using var tx = session.BeginTransaction(isolation);
                using var count = new SqlCommand(
                    "SELECT COUNT(*) FROM dbo.duty WHERE active=1", session, tx);
                var active = Convert.ToInt32(count.ExecuteScalar());
                if (attempt == 0)
                {
                    using var delay = new SqlCommand("WAITFOR DELAY '00:00:01'", session, tx);
                    delay.ExecuteNonQuery();
                }
                string status;
                if (active == 2)
                {
                    using var update = new SqlCommand(
                        "UPDATE dbo.duty SET active=0 WHERE id=@id", session, tx);
                    update.Parameters.AddWithValue("@id", id);
                    if (update.ExecuteNonQuery() != 1) throw new InvalidOperationException("Duty missing");
                    status = "DISABLED";
                }
                else status = "SKIPPED";
                tx.Commit();
                Console.WriteLine(JsonSerializer.Serialize(new {
                    status, retries = retries.Count, retrySqlErrors = retries
                }));
                return 0;
            }
            catch (SqlException ex) when (ex.Number is 1205 or 3960)
            {
                retries.Add(ex.Number);
                Thread.Sleep(30*(attempt+1));
            }
        }
        throw new InvalidOperationException("Duty retry limit reached");
    }
    if (args[0] == "pool")
    {
        // Deliberately constrain a real client connection pool to 2 leases;
        // an independent third Open must fail promptly and not hang forever.
        var pool = new SqlConnectionStringBuilder(builder.ConnectionString)
        {
            Pooling = true,
            MinPoolSize = 0,
            MaxPoolSize = 2,
            ConnectTimeout = 2,
            ApplicationName = "E1c-Two-Connection-Pool"
        };
        using var first = new SqlConnection(pool.ConnectionString);
        using var second = new SqlConnection(pool.ConnectionString);
        first.Open();
        second.Open();
        try
        {
            using var third = new SqlConnection(pool.ConnectionString);
            third.Open();
            throw new InvalidOperationException("A third pool lease incorrectly succeeded");
        }
        catch (InvalidOperationException ex) when (
            ex.Message.Contains("pool", StringComparison.OrdinalIgnoreCase) &&
            !ex.Message.Contains("incorrectly", StringComparison.OrdinalIgnoreCase))
        {
            Console.WriteLine("{\"status\":\"POOL_EXHAUSTED\",\"maxConnections\":2}");
            return 0;
        }
    }
    return 4;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message);
    return 5;
}
