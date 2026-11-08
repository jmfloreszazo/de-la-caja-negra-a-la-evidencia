using System.Net;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Npgsql;

if (Environment.GetEnvironmentVariable("E3_DISPOSABLE_FIXTURE") != "YES")
    throw new InvalidOperationException("E3_DISPOSABLE_FIXTURE=YES is required for this loopback-only fixture.");
var connection = new NpgsqlConnectionStringBuilder(
    Environment.GetEnvironmentVariable("E1_PG_NPGSQL")
    ?? throw new InvalidOperationException("E1_PG_NPGSQL is required."));
if (connection.Host != "127.0.0.1" || string.IsNullOrWhiteSpace(connection.Database) ||
    new[] { "postgres", "template0", "template1" }.Contains(connection.Database) ||
    !string.IsNullOrEmpty(connection.Options) || !string.IsNullOrEmpty(connection.SearchPath))
    throw new InvalidOperationException("Use an explicit disposable database on 127.0.0.1 without Options or SearchPath.");
if (args is ["describe"])
{
    Console.WriteLine(JsonSerializer.Serialize(new {
        host = connection.Host, port = connection.Port,
        database = connection.Database, username = connection.Username
    }));
    return;
}
if (args.Length != 2 || args[0] != "server" || !int.TryParse(args[1], out int port) ||
    port is < 1024 or > 65535)
    throw new ArgumentException("Usage: describe | server PORT");
string schema = Environment.GetEnvironmentVariable("E3_PG_SCHEMA") ?? "";
if (!Regex.IsMatch(schema, "^e3_[a-f0-9]{32}$"))
    throw new InvalidOperationException("An owned E3_PG_SCHEMA is required.");
connection.SearchPath = schema;
connection.ApplicationName = schema;
connection.Timeout = 3;
connection.CommandTimeout = 3;
connection.MaxPoolSize = 16;
connection.Options = "-c statement_timeout=3000 -c lock_timeout=1000";
Environment.SetEnvironmentVariable("E1_PG_NPGSQL", connection.ConnectionString);
await using (var db = new NpgsqlConnection(connection.ConnectionString))
{
    await db.OpenAsync();
    await using var check = new NpgsqlCommand("SELECT COUNT(*) FROM accounts", db);
    if (Convert.ToInt32(await check.ExecuteScalarAsync()) != 16)
        throw new InvalidOperationException("The isolated E1 fixture must contain exactly 16 accounts.");
}
var builder = WebApplication.CreateBuilder(args);
builder.Logging.ClearProviders();
builder.WebHost.ConfigureKestrel(k => k.Listen(IPAddress.Loopback, port,
    options => options.Protocols = HttpProtocols.Http1));
builder.Services.AddSingleton<PgLedger>();
var app = builder.Build();
app.MapGet("/health", () => Results.Ok(new { pid = Environment.ProcessId, schema }));
app.MapPost("/transfer", async (TransferCommand command, PgLedger ledger, CancellationToken ct)
    => Results.Json(await ledger.ExecuteAsync(command, ct)));
await app.RunAsync();
