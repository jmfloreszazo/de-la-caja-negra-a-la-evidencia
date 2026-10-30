using System.Diagnostics;
using System.Net;
using System.Net.Http.Json;
using System.Reflection;
using System.Text.Json;
using Grpc.Core;
using Grpc.Net.Client;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using Npgsql;
using DurableRpc;

if (args.Length == 0)
{
    Console.Error.WriteLine("Usage: server PORT | benchmark PROTOCOL REPLICAS DISTRIBUTION COUNT CONCURRENCY OUTPUT");
    return 2;
}
if (args[0] == "server")
{
    int port = int.Parse(args[1]);
    var builder = WebApplication.CreateBuilder(args);
    builder.Logging.ClearProviders();
    builder.WebHost.ConfigureKestrel(k =>
        k.ListenLocalhost(port, opts => opts.Protocols = HttpProtocols.Http2));
    builder.Services.AddGrpc();
    builder.Services.AddSingleton<PgLedger>();
    var app = builder.Build();
    app.MapGet("/health", () => Results.Ok(new { ok = true }));
    app.MapPost("/transfer", async (TransferCommand command, PgLedger ledger, CancellationToken ct)
        => Results.Json(await ledger.ExecuteAsync(command, ct)));
    app.MapGrpcService<LedgerGrpcService>();
    await app.RunAsync();
    return 0;
}
if (args[0] != "benchmark" || args.Length != 7)
    throw new ArgumentException("benchmark PROTOCOL REPLICAS DISTRIBUTION COUNT CONCURRENCY OUTPUT");

string protocol = args[1], distribution = args[3], filename = args[6];
int replicas = int.Parse(args[2]), requests = int.Parse(args[4]),
    concurrency = int.Parse(args[5]);
if (!new[] { "grpc", "rest" }.Contains(protocol) ||
    !new[] { "uniform", "hot" }.Contains(distribution) ||
    replicas is < 1 or > 16 || requests is < 100 or > 10000 ||
    concurrency is < 1 or > 64)
    throw new ArgumentException("Invalid bounded experiment arguments");

var children = new List<Process>();
var http = new List<HttpClient>();
var channels = new List<GrpcChannel>();
var grpcClients = new List<LedgerApi.LedgerApiClient>();
try
{
    var dll = Assembly.GetExecutingAssembly().Location;
    int firstPort = 5600;
    for (int i = 0; i < replicas; i++)
    {
        var psi = new ProcessStartInfo("dotnet")
        {
            UseShellExecute = false,
            RedirectStandardError = true,
            RedirectStandardOutput = true
        };
        psi.ArgumentList.Add(dll);
        psi.ArgumentList.Add("server");
        psi.ArgumentList.Add((firstPort + i).ToString());
        children.Add(Process.Start(psi) ?? throw new InvalidOperationException("Child launch failed"));
        var client = new HttpClient(new SocketsHttpHandler
        {
            EnableMultipleHttp2Connections = true,
            PooledConnectionLifetime = TimeSpan.FromMinutes(3)
        });
        client.DefaultRequestVersion = HttpVersion.Version20;
        client.DefaultVersionPolicy = HttpVersionPolicy.RequestVersionExact;
        client.Timeout = TimeSpan.FromSeconds(20);
        http.Add(client);
        var chan = GrpcChannel.ForAddress($"http://127.0.0.1:{firstPort+i}",
            new GrpcChannelOptions { HttpClient = client, DisposeHttpClient = false });
        channels.Add(chan);
        grpcClients.Add(new LedgerApi.LedgerApiClient(chan));
    }
    for (int i = 0; i < replicas; i++)
    {
        bool ready = false;
        for (int attempt = 0; attempt < 150; attempt++)
        {
            if (children[i].HasExited)
                throw new Exception($"Service {i} exited with {children[i].ExitCode}: "
                    + await children[i].StandardError.ReadToEndAsync());
            try
            {
                using var response = await http[i].GetAsync($"http://127.0.0.1:{firstPort+i}/health");
                ready = response.IsSuccessStatusCode && response.Version.Major == 2;
                if (ready) break;
            }
            catch (HttpRequestException) { }
            await Task.Delay(100);
        }
        if (!ready) throw new TimeoutException($"Service replica {i} not ready");
    }
    var latencies = new double[requests];
    var counts = new int[replicas];
    int failures = 0, commits = 0;
    string[] errorExamples = new string[3];
    using var limiter = new SemaphoreSlim(concurrency);
    var total = Stopwatch.StartNew();
    await Task.WhenAll(Enumerable.Range(0, requests).Select(async index =>
    {
        await limiter.WaitAsync();
        try
        {
            var command = MakeCommand(index, distribution, protocol, replicas);
            int selected = index % replicas;
            var stopwatch = Stopwatch.StartNew();
            TransferDecision result;
            if (protocol == "grpc")
            {
                var response = await grpcClients[selected].TransferAsync(new TransferInput
                {
                    OperationId = command.OperationId,
                    Src = command.Src, Dst = command.Dst, AmountCents = command.AmountCents
                }, deadline: DateTime.UtcNow.AddSeconds(20));
                result = new TransferDecision(response.OperationId,response.Status,response.AmountCents);
            }
            else
            {
                using var message = new HttpRequestMessage(HttpMethod.Post,
                    $"http://127.0.0.1:{firstPort+selected}/transfer")
                {
                    Version = HttpVersion.Version20,
                    VersionPolicy = HttpVersionPolicy.RequestVersionExact,
                    Content = JsonContent.Create(command)
                };
                using var response = await http[selected].SendAsync(message);
                response.EnsureSuccessStatusCode();
                if (response.Version.Major != 2)
                    throw new InvalidOperationException("REST was not sent over HTTP/2");
                result = await response.Content.ReadFromJsonAsync<TransferDecision>()
                    ?? throw new Exception("Missing transfer response");
            }
            stopwatch.Stop();
            latencies[index] = stopwatch.Elapsed.TotalMilliseconds;
            if (result.OperationId != command.OperationId || result.Status != "COMMITTED" ||
                result.AmountCents != command.AmountCents)
                throw new Exception($"Unexpected result: {result}");
            Interlocked.Increment(ref commits);
            Interlocked.Increment(ref counts[selected]);
        }
        catch (Exception ex)
        {
            int n = Interlocked.Increment(ref failures);
            if (n <= 3) errorExamples[n-1] = ex.GetType().Name + ": " + ex.Message;
        }
        finally { limiter.Release(); }
    }));
    total.Stop();
    Array.Sort(latencies);
    double p(double q) => Math.Round(latencies[Math.Clamp(
        (int)Math.Ceiling(q * latencies.Length)-1,0,latencies.Length-1)],3);
    var report = new
    {
        schemaVersion = 1,
        classification = "M2_LOCAL_SINGLE_HOST_POSTGRES_DURABLE_SMOKE_NOT_CLOUD_OR_MAINFRAME",
        timestampUtc = DateTimeOffset.UtcNow,
        sourceCommit = Environment.GetEnvironmentVariable("GITHUB_SHA") ?? "local",
        experiment = new
        {
            protocol, distribution, replicas, requests, concurrency,
            committed = commits, failures,
            errorExamples = errorExamples.Where(x => x is not null).ToArray(),
            perReplicaCommits = counts,
            durableCommittedPerSecond = Math.Round(commits/total.Elapsed.TotalSeconds,2),
            elapsedSeconds = Math.Round(total.Elapsed.TotalSeconds,4),
            p50Ms = p(.50), p95Ms = p(.95), p99Ms = p(.99),
            closedLoop = true,
            noTls = true,
            onlyOneGitHubRunner = true
        },
        environment = new
        {
            runtime = Environment.Version.ToString(), processors = Environment.ProcessorCount,
            os = Environment.OSVersion.ToString(),
            database = "PostgreSQL 16.13 on Podman loopback, one instance shared by all service processes",
            transport = "HTTP/2 plaintext (h2c) for REST and gRPC",
            caveat = "No Azure VMs, cluster autoscaler, WAN or failover were tested"
        }
    };
    var path = Path.GetFullPath(filename);
    Directory.CreateDirectory(Path.GetDirectoryName(path)!);
    await File.WriteAllTextAsync(path,
        JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+"\n");
    Console.WriteLine(JsonSerializer.Serialize(report));
    return failures == 0 && commits == requests ? 0 : 8;
}
finally
{
    foreach (var channel in channels) channel.Dispose();
    foreach (var client in http) client.Dispose();
    foreach (var child in children)
    {
        if (!child.HasExited)
        {
            child.Kill(entireProcessTree: true);
            await child.WaitForExitAsync();
        }
        child.Dispose();
    }
}

static TransferCommand MakeCommand(int i, string distribution, string protocol, int replicas)
{
    int src, dst;
    if (distribution == "hot" && i % 2 == 0)
    {
        src = 1; dst = 2;
    }
    else
    {
        src = 3 + (i % 14);
        dst = src == 16 ? 3 : src + 1;
    }
    return new TransferCommand($"m2-{protocol}-{distribution}-{replicas}-{i}",
        src,dst,1+(i%4));
}

public record TransferCommand(string OperationId, int Src, int Dst, long AmountCents);
public record TransferDecision(string OperationId, string Status, long AmountCents);

public sealed class PgLedger
{
    private readonly string _dsn = Environment.GetEnvironmentVariable("E1_PG_NPGSQL")
        ?? throw new InvalidOperationException("E1_PG_NPGSQL must refer to a disposable database.");
    public async Task<TransferDecision> ExecuteAsync(TransferCommand command,CancellationToken ct)
    {
        if (command.OperationId.Length is < 1 or > 80 ||
            !command.OperationId.All(c => char.IsAsciiLetterOrDigit(c) || c=='-') ||
            command.Src is < 1 or > 16 || command.Dst is < 1 or > 16 ||
            command.Src == command.Dst || command.AmountCents is <= 0 or > 1_000_000_000_000)
            return new TransferDecision(command.OperationId,"INVALID",0);

        for (int attempt=0;attempt<8;attempt++)
        {
            try
            {
                await using var db = new NpgsqlConnection(_dsn);
                await db.OpenAsync(ct);
                await using var tx = await db.BeginTransactionAsync(ct);
                await Scalar(tx,"SET LOCAL lock_timeout = '3000ms'");
                await Scalar(tx,"SELECT pg_advisory_xact_lock(hashtextextended($1,0))",
                    command.OperationId);
                var prior = await Row(tx,
                    "SELECT src,dst,amount,status FROM operations WHERE id=$1",
                    command.OperationId);
                string status;
                if (prior is not null)
                {
                    bool same = Convert.ToInt32(prior[0])==command.Src &&
                                Convert.ToInt32(prior[1])==command.Dst &&
                                Convert.ToInt64(prior[2])==command.AmountCents;
                    status = same ? "DUPLICATE_"+Convert.ToString(prior[3]) : "ID_CONFLICT";
                }
                else
                {
                    foreach (var acct in new[] {command.Src,command.Dst}.Order())
                        if (await Scalar(tx,"SELECT id FROM accounts WHERE id=$1 FOR UPDATE",acct) is null)
                            throw new InvalidOperationException("Account not found");
                    int debited = await Exec(tx,
                        "UPDATE accounts SET balance=balance-$1 WHERE id=$2 AND balance >= $1",
                        command.AmountCents, command.Src);
                    if (debited==1)
                        await Exec(tx,"UPDATE accounts SET balance=balance+$1 WHERE id=$2",
                            command.AmountCents,command.Dst);
                    status = debited==1 ? "COMMITTED" : "REJECTED";
                    await Exec(tx,
                        "INSERT INTO operations(id,src,dst,amount,status) VALUES($1,$2,$3,$4,$5)",
                        command.OperationId,command.Src,command.Dst,command.AmountCents,status);
                    if (debited==1)
                    {
                        await Exec(tx,
                            "INSERT INTO postings(op,account,delta) VALUES($1,$2,$3),($1,$4,$5)",
                            command.OperationId,command.Src,-command.AmountCents,
                            command.Dst,command.AmountCents);
                        await Exec(tx,
                            "INSERT INTO outbox(op,event) VALUES($1,$2)",
                            command.OperationId,"TransferCommitted");
                    }
                }
                await tx.CommitAsync(ct);
                return new TransferDecision(command.OperationId,status,
                    status is "COMMITTED" or "DUPLICATE_COMMITTED" ? command.AmountCents : 0);
            }
            catch (PostgresException e) when (e.SqlState is "40P01" or "40001" or "55P03")
            {
                await Task.Delay(15*(attempt+1),ct);
            }
        }
        return new TransferDecision(command.OperationId,"RETRY_EXHAUSTED",0);
    }
    private static NpgsqlCommand Command(NpgsqlTransaction tx,string sql,params object[] values)
    {
        var c=new NpgsqlCommand(sql,tx.Connection,tx);
        foreach(var value in values)c.Parameters.Add(new NpgsqlParameter{Value=value});
        return c;
    }
    private static async Task<int> Exec(NpgsqlTransaction tx,string sql,params object[] values)
    {
        using var c=Command(tx,sql,values);
        return await c.ExecuteNonQueryAsync();
    }
    private static async Task<object?> Scalar(NpgsqlTransaction tx,string sql,params object[] values)
    {
        using var c=Command(tx,sql,values);
        return await c.ExecuteScalarAsync();
    }
    private static async Task<object[]?> Row(NpgsqlTransaction tx,string sql,params object[] values)
    {
        using var c=Command(tx,sql,values);
        using var reader=await c.ExecuteReaderAsync();
        if (!await reader.ReadAsync())return null;
        var row=new object[reader.FieldCount];
        reader.GetValues(row);
        return row;
    }
}

public sealed class LedgerGrpcService(PgLedger ledger) : LedgerApi.LedgerApiBase
{
    public override async Task<TransferOutput> Transfer(TransferInput input,ServerCallContext context)
    {
        var result=await ledger.ExecuteAsync(
            new TransferCommand(input.OperationId,input.Src,input.Dst,input.AmountCents),
            context.CancellationToken);
        return new TransferOutput
        {
            OperationId=result.OperationId,Status=result.Status,AmountCents=result.AmountCents
        };
    }
}
