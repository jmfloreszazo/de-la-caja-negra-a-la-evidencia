using System.Text.Json;
using Microsoft.Data.SqlClient;

// Independent, SQL read-only oracle: does not import or call SqlBank business
// logic and never issues DML. The test harness owns the negative mutation.
if (args.Length != 0) return 4;
try
{
    var password = Environment.GetEnvironmentVariable("E1_SQL_PASSWORD")
        ?? throw new InvalidOperationException("E1_SQL_PASSWORD is required");
    var builder = new SqlConnectionStringBuilder
    {
        DataSource = Environment.GetEnvironmentVariable("E1_SQL_HOST")
            ?? "127.0.0.1,14333",
        InitialCatalog = "E1SqlLab",
        UserID = "sa", Password = password,
        Encrypt = SqlConnectionEncryptOption.Mandatory,
        TrustServerCertificate = true, Pooling = false,
        ApplicationName = "E1c-Independent-ReadOnly-Oracle"
    };
    using var db = new SqlConnection(builder.ConnectionString);
    db.Open();
    // Snapshot gives a consistent read-only point-in-time view, provided
    // that the lab initialized ALLOW_SNAPSHOT_ISOLATION.
    using var tx = db.BeginTransaction(System.Data.IsolationLevel.Snapshot);
    long Number(string sql)
    {
        using var cmd = new SqlCommand(sql, db, tx) { CommandTimeout = 15 };
        return Convert.ToInt64(cmd.ExecuteScalar());
    }
    var vectors = new Dictionary<string, bool>
    {
        ["nonnegative"] = Number(
            "SELECT COUNT(*) FROM dbo.accounts WHERE balance<0") == 0,
        ["conserved"] = Number(
            "SELECT SUM(balance) FROM dbo.accounts") == 1_600_000,
        ["balancedPostings"] = Number(
            "SELECT COUNT(*) FROM (SELECT op FROM dbo.postings GROUP BY op " +
            "HAVING SUM(delta)<>0 OR COUNT(*)<>2) bad") == 0,
        ["twoPostingsPerCommit"] = Number(
            "SELECT COUNT(*) FROM dbo.operations o WHERE o.status=N'COMMITTED' " +
            "AND (SELECT COUNT(*) FROM dbo.postings p WHERE p.op=o.id)<>2") == 0,
        ["noPostingsForRejection"] = Number(
            "SELECT COUNT(*) FROM dbo.operations o WHERE o.status=N'REJECTED' " +
            "AND EXISTS (SELECT 1 FROM dbo.postings p WHERE p.op=o.id)") == 0,
        ["outboxAtomic"] = Number(
            "SELECT COUNT(*) FROM dbo.operations o " +
            "WHERE o.status=N'COMMITTED' AND NOT EXISTS " +
            "(SELECT 1 FROM dbo.outbox b WHERE b.op=o.id)") == 0 &&
            Number(
            "SELECT COUNT(*) FROM dbo.outbox b JOIN dbo.operations o ON b.op=o.id " +
            "WHERE o.status<>N'COMMITTED'") == 0,
        ["projectionAgrees"] = Number(
            "SELECT COUNT(*) FROM dbo.accounts a WHERE a.balance<>100000+" +
            "ISNULL((SELECT SUM(p.delta) FROM dbo.postings p WHERE p.account=a.id),0)")
            == 0
    };
    tx.Commit();
    Console.WriteLine(JsonSerializer.Serialize(new
    {
        status = vectors.Values.All(x => x) ? "PASS" : "REJECTED",
        checks = vectors
    }));
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message);
    return 5;
}
