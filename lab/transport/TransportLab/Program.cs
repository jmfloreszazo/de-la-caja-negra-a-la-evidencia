using System.Diagnostics;
using System.Reflection;
using System.Text.Json;
using System.Net.Http.Json;
using System.Net;
using Grpc.Core;
using Grpc.Net.Client;
using Microsoft.AspNetCore.Server.Kestrel.Core;
using BankTransport;

if (args.Length == 0)
{
    Console.Error.WriteLine("Usage: server [port] | benchmark [port] [requests] [concurrency] [output]");
    return 2;
}
if (args[0] == "server")
{
    int port = args.Length > 1 ? int.Parse(args[1]) : 5088;
    var builder = WebApplication.CreateBuilder(args);
    builder.Logging.ClearProviders();
    builder.WebHost.ConfigureKestrel(k =>
        k.ListenLocalhost(port, listen => listen.Protocols = HttpProtocols.Http2));
    builder.Services.AddGrpc();
    var app = builder.Build();
    app.MapGrpcService<TransferGrpcService>();
    app.MapPost("/v1/transfer", (TransferCommand request) =>
        Results.Json(Policy.Evaluate(request.OperationId, request.Source,
                                     request.Destination, request.AmountCents)));
    app.MapGet("/health", () => Results.Ok(new { ok = true }));
    await app.RunAsync();
    return 0;
}
if (args[0] != "benchmark" || args.Length < 5)
{
    Console.Error.WriteLine("Usage: benchmark PORT REQUESTS CONCURRENCY OUTPUT");
    return 2;
}
int listenPort = int.Parse(args[1]), requestCount = int.Parse(args[2]),
    concurrency = int.Parse(args[3]);
if (requestCount is < 100 or > 10000 || concurrency is < 1 or > 64)
    throw new ArgumentException("Benchmark limits: 100..10000 requests, 1..64 concurrency.");
string outputFile = args[4];
string binaryPath = Assembly.GetExecutingAssembly().Location;
var psi = new ProcessStartInfo("dotnet")
{
    UseShellExecute = false,
    RedirectStandardOutput = true,
    RedirectStandardError = true
};
psi.ArgumentList.Add(binaryPath);
psi.ArgumentList.Add("server");
psi.ArgumentList.Add(listenPort.ToString());
using var server = Process.Start(psi) ?? throw new Exception("Failed to launch loopback server.");
try
{
    string root = $"http://127.0.0.1:{listenPort}";
    using var http = new HttpClient(new SocketsHttpHandler
    {
        EnableMultipleHttp2Connections = true,
        PooledConnectionLifetime = TimeSpan.FromMinutes(5)
    });
    http.DefaultRequestVersion = HttpVersion.Version20;
    http.DefaultVersionPolicy = HttpVersionPolicy.RequestVersionExact;
    http.Timeout = TimeSpan.FromSeconds(10);
    bool ready = false;
    for (int n = 0; n < 100; n++)
    {
        if (server.HasExited)
            throw new Exception($"Server exited prematurely with {server.ExitCode}: "
                + await server.StandardError.ReadToEndAsync());
        try
        {
            using var res = await http.GetAsync(root + "/health");
            ready = res.IsSuccessStatusCode && res.Version.Major == 2;
            if (ready) break;
        }
        catch (HttpRequestException) { }
        await Task.Delay(100);
    }
    if (!ready) throw new Exception("HTTP/2 loopback server did not become ready.");
    using var channel = GrpcChannel.ForAddress(root, new GrpcChannelOptions
    {
        HttpClient = http
    });
    var grpc = new TransferApi.TransferApiClient(channel);

    async Task<(string id, string status, long accepted)> RestAsync(TransferCommand command)
    {
        using var msg = new HttpRequestMessage(HttpMethod.Post, root + "/v1/transfer")
        {
            Version = HttpVersion.Version20,
            VersionPolicy = HttpVersionPolicy.RequestVersionExact,
            Content = JsonContent.Create(command)
        };
        using var response = await http.SendAsync(msg);
        response.EnsureSuccessStatusCode();
        if (response.Version.Major != 2)
            throw new InvalidOperationException("REST not using HTTP/2.");
        var parsed = await response.Content.ReadFromJsonAsync<TransferDecision>();
        if (parsed is null) throw new Exception("REST response missing");
        return (parsed.OperationId, parsed.Status, parsed.AcceptedCents);
    }

    async Task<(string id, string status, long accepted)> GrpcAsync(TransferCommand command)
    {
        var request = new TransferRequest
        {
            OperationId = command.OperationId, Source = command.Source,
            Destination = command.Destination, AmountCents = command.AmountCents
        };
        var response = await grpc.SubmitAsync(request,
            deadline: DateTime.UtcNow.AddSeconds(10));
        return (response.OperationId, response.Status, response.AcceptedCents);
    }

    // An independent expected-value function validates the transport results.
    // Deliberately wrong results must be rejected before any benchmark starts.
    var rejected = new TransferCommand("negative-control", 1, 1, 123);
    if (Oracle.IsValid(rejected, ("negative-control", "ACCEPTED", 123)))
        throw new Exception("Negative control failed: oracle accepted a wrong decision.");
    if (!Oracle.IsValid(rejected, ("negative-control", "REJECTED", 0)))
        throw new Exception("Oracle rejects a valid negative case.");

    var commands = Enumerable.Range(0, requestCount)
        .Select(n =>
        {
            int source = n % 16 + 1;
            int target = n % 29 == 0 ? source : source % 16 + 1;
            long cents = n % 19 == 0 ? 0L : 125L + n % 500;
            return new TransferCommand("micro-" + n, source, target, cents);
        }).ToArray();

    async Task<Trial> MeasureAsync(string protocol, bool warmup = false)
    {
        var send = protocol == "grpc" ?
            (Func<TransferCommand, Task<(string id, string status, long accepted)>>)GrpcAsync : RestAsync;
        var observations = new double[commands.Length];
        int errors = 0;
        using var limiter = new SemaphoreSlim(concurrency);
        var total = Stopwatch.StartNew();
        await Task.WhenAll(commands.Select(async (cmd, index) =>
        {
            await limiter.WaitAsync();
            try
            {
                var watch = Stopwatch.StartNew();
                var response = await send(cmd);
                watch.Stop();
                observations[index] = watch.Elapsed.TotalMilliseconds;
                if (!Oracle.IsValid(cmd, response)) Interlocked.Increment(ref errors);
            }
            catch (Exception ex)
            {
                Interlocked.Increment(ref errors);
                if (!warmup && errors <= 3) Console.Error.WriteLine(protocol + " error: " + ex.Message);
            }
            finally { limiter.Release(); }
        }));
        total.Stop();
        if (errors > 0) throw new Exception($"{protocol} failed: {errors} invalid or missing replies");
        Array.Sort(observations);
        double Percentile(double q) => observations[Math.Clamp(
            (int)Math.Ceiling(q * observations.Length) - 1, 0, observations.Length - 1)];
        return new Trial(protocol, commands.Length, concurrency, errors,
            Math.Round(total.Elapsed.TotalSeconds, 4),
            Math.Round(commands.Length / total.Elapsed.TotalSeconds, 2),
            Math.Round(Percentile(.50), 3), Math.Round(Percentile(.95), 3),
            Math.Round(Percentile(.99), 3));
    }
    // Warm up both paths. Alternate A/B to reduce systematic ordering bias.
    await MeasureAsync("rest", true);
    await MeasureAsync("grpc", true);
    var trials = new List<Trial>();
    foreach (var protocol in new[] { "grpc", "rest", "rest", "grpc" })
        trials.Add(await MeasureAsync(protocol));
    var report = new
    {
        schemaVersion = 1,
        classification = "EXECUTED_LOCALHOST_TRANSPORT_ONLY_NOT_LEDGER_OR_MAINFRAME",
        createdAtUtc = DateTimeOffset.UtcNow,
        sourceCommit = Environment.GetEnvironmentVariable("GITHUB_SHA") ?? "local",
        environment = new
        {
            dotnet = Environment.Version.ToString(),
            os = Environment.OSVersion.ToString(),
            processorCount = Environment.ProcessorCount,
            httpTransport = "HTTP/2 plaintext (h2c), loopback only, both protocols",
            grpcLibrary = "Grpc.AspNetCore 2.84.0; Grpc.Net.Client 2.84.0",
            tlsAndNetwork = "NOT TESTED, next experiment must use equivalent TLS and network path"
        },
        protocol = "same Kestrel process, same business function, typed payload vs JSON, independent result oracle",
        workload = new
        {
            requestsPerRound = requestCount,
            concurrency, warmup = true, order = "gRPC, REST, REST, gRPC",
            closedLoop = true,
            claims = "No durable ledger, WAN, Kubernetes, autoscale or mainframe throughput was measured"
        },
        negativeOracleControl = "PASS",
        trials
    };
    string? directory = Path.GetDirectoryName(Path.GetFullPath(outputFile));
    if (directory is not null) Directory.CreateDirectory(directory);
    await File.WriteAllTextAsync(outputFile,
        JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }) + "\n");
    Console.WriteLine(JsonSerializer.Serialize(report, new JsonSerializerOptions { WriteIndented = true }));
    return 0;
}
finally
{
    if (!server.HasExited)
    {
        server.Kill(entireProcessTree: true);
        await server.WaitForExitAsync();
    }
}

public record TransferCommand(string OperationId, int Source, int Destination, long AmountCents);
public record TransferDecision(string OperationId, string Status, long AcceptedCents);
public record Trial(string Protocol, int Requests, int Concurrency, int Errors,
                    double ElapsedSeconds, double RepliesPerSecond,
                    double P50Ms, double P95Ms, double P99Ms);

public static class Policy
{
    public static TransferDecision Evaluate(string id, int source, int destination, long cents)
    {
        bool accept = !string.IsNullOrWhiteSpace(id) &&
                      source is >= 1 and <= 16 && destination is >= 1 and <= 16 &&
                      source != destination && cents > 0 && cents <= 1_000_000;
        return new TransferDecision(id, accept ? "ACCEPTED" : "REJECTED",
                                    accept ? cents : 0);
    }
}
public static class Oracle
{
    public static bool IsValid(TransferCommand c, (string id, string status, long accepted) result)
    {
        bool valid = !string.IsNullOrWhiteSpace(c.OperationId) &&
                     c.Source > 0 && c.Source <= 16 && c.Destination > 0 &&
                     c.Destination <= 16 && c.Source != c.Destination &&
                     c.AmountCents is > 0 and <= 1_000_000;
        return result.id == c.OperationId &&
               result.status == (valid ? "ACCEPTED" : "REJECTED") &&
               result.accepted == (valid ? c.AmountCents : 0);
    }
}
public class TransferGrpcService : TransferApi.TransferApiBase
{
    public override Task<TransferReply> Submit(TransferRequest req, ServerCallContext context)
    {
        var result = Policy.Evaluate(req.OperationId, req.Source, req.Destination, req.AmountCents);
        return Task.FromResult(new TransferReply
        {
            OperationId = result.OperationId, Status = result.Status,
            AcceptedCents = result.AcceptedCents
        });
    }
}
