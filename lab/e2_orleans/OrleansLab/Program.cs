using System.Diagnostics;
using System.Text.Json;
using E2.OrleansLab;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Orleans;

// Isolated deliberately unsafe actor-state negative control. No SQL ledger
// command is executed in this mode; never use this route for business transfers.
if (args is ["negative-reentrancy"])
{
    const int expectedCalls = 16;
    var negativeBuilder = Host.CreateApplicationBuilder(args);
    negativeBuilder.Logging.ClearProviders();
    negativeBuilder.UseOrleans(silo => silo.UseLocalhostClustering());
    using var negativeHost = negativeBuilder.Build();
    await negativeHost.StartAsync();
    try
    {
        var client = negativeHost.Services.GetRequiredService<IClusterClient>();
        var grain = client.GetGrain<IUnsafeReentrantCounterGrain>(12345);
        var observedResponses = await Task.WhenAll(
            Enumerable.Range(0, expectedCalls).Select(
                _ => grain.UnsafeIncrementWithStaleRead(expectedCalls)));
        var persistedOnlyInMemory = await grain.GetUnsafeValue();
        if (observedResponses.Length != expectedCalls ||
            observedResponses.Any(value => value != 1) ||
            persistedOnlyInMemory != 1)
            throw new InvalidOperationException(
                "The isolated reentrant negative control did not demonstrate lost updates");
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            experiment = "E2-Orleans-Reentrant-Unsafe-Actor-State",
            status = "NEGATIVE_CONTROL_DETECTED",
            concurrentCalls = expectedCalls,
            expectedIfAtomic = expectedCalls,
            observedActorLocalValue = persistedOnlyInMemory,
            lostUpdates = expectedCalls - persistedOnlyInMemory,
            durableSqlTransfers = 0,
            limitation = "Deliberately unsafe in-memory demonstration only; not a cross-grain SQL transaction, deadlock, or multi-silo failover"
        }, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase }));
    }
    finally
    {
        await negativeHost.StopAsync();
    }
    return 0;
}

if (args.Length != 2 || args[0] != "run" || !File.Exists(args[1]))
{
    Console.Error.WriteLine("Usage: OrleansLab run <scenario.json>");
    return 4;
}

try
{
    var definition = JsonSerializer.Deserialize<Scenario>(
        await File.ReadAllTextAsync(args[1]),
        new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
    if (definition?.Commands is null ||
        definition.Route is not ("direct" or "orleans") ||
        definition.Commands.Count is < 1 or > 256)
        throw new ArgumentException("Scenario route/commands invalid");

    var connection = Environment.GetEnvironmentVariable("E2_PG_NPGSQL")
        ?? throw new ArgumentException("E2_PG_NPGSQL is required");
    var connInfo = new NpgsqlConnectionStringBuilder(connection);
    if (connInfo.Database != "e2lab" ||
        connInfo.Host is not ("127.0.0.1" or "localhost"))
        throw new InvalidOperationException("Only a loopback disposable e2lab database is allowed");

    var builder = Host.CreateApplicationBuilder(args);
    builder.Logging.ClearProviders();
    builder.Services.AddSingleton<NpgsqlDataSource>(
        _ => new NpgsqlDataSourceBuilder(connection).Build());
    builder.Services.AddSingleton<IDurableLedger, PgDurableLedger>();
    builder.UseOrleans(silo => silo.UseLocalhostClustering());

    using var host = builder.Build();
    await host.StartAsync();
    try
    {
        var ledger = host.Services.GetRequiredService<IDurableLedger>();
        var grains = host.Services.GetRequiredService<IClusterClient>();

        async Task<TransferResult> Execute(TransferCommand command)
        {
            if (!PgDurableLedger.Valid(command))
                return new TransferResult("INVALID", 0, [], "input-validation");

            return definition.Route == "direct"
                ? (await ledger.Transfer(command)) with { HandledBy = "direct-ledger" }
                : await grains.GetGrain<IAccountGrain>(command.SourceAccountId)
                    .Transfer(command);
        }

        var clock = Stopwatch.StartNew();
        async Task<TimedResult> TimedExecution(TransferCommand command)
        {
            if (command.ArrivalOffsetMs is < 0 or > 30000)
                throw new ArgumentException("Invalid offered arrival offset");
            if (definition.Concurrent && command.ArrivalOffsetMs > 0)
            {
                var delay = command.ArrivalOffsetMs - clock.Elapsed.TotalMilliseconds;
                if (delay > 0)
                    await Task.Delay(TimeSpan.FromMilliseconds(delay));
            }
            var dispatchedAtMs = clock.Elapsed.TotalMilliseconds;
            var request = Stopwatch.StartNew();
            var result = await Execute(command);
            return new TimedResult(result,
                Math.Round(dispatchedAtMs, 3),
                Math.Round(request.Elapsed.TotalMilliseconds, 3),
                Math.Round(clock.Elapsed.TotalMilliseconds, 3));
        }

        TimedResult[] samples;
        if (definition.Concurrent)
        {
            samples = await Task.WhenAll(definition.Commands.Select(TimedExecution));
        }
        else
        {
            var result = new List<TimedResult>();
            foreach (var command in definition.Commands)
                result.Add(await TimedExecution(command));
            samples = [..result];
        }

        var outcomes = samples.Select(sample => sample.Result).ToArray();
        Console.WriteLine(JsonSerializer.Serialize(new
        {
            experiment = "E2-orleans-ledger",
            route = definition.Route,
            concurrent = definition.Concurrent,
            sourceOfTruth = "postgresql-transaction",
            results = outcomes,
            timing = samples.Select(sample => new {
                sample.DispatchedAtMs, sample.ElapsedMs, sample.CompletedAtMs
            }).ToArray()
        }, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase }));
    }
    finally
    {
        await host.StopAsync();
    }
    return 0;
}
catch (Exception ex)
{
    Console.Error.WriteLine(ex.GetType().Name + ": " + ex.Message);
    return 5;
}

internal sealed record Scenario(string Route, bool Concurrent, List<TransferCommand> Commands);

internal sealed record TimedResult(TransferResult Result, double DispatchedAtMs, double ElapsedMs, double CompletedAtMs);
