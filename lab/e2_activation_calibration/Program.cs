using System.Text.Json;
using E2.OrleansLab;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Orleans;
using Orleans.Configuration;
using Orleans.Hosting;

if (Environment.GetEnvironmentVariable("E2_CALIBRATION_TEST") != "1" ||
    args.Length != 1 || args[0] is not ("single" or "positive"))
    throw new InvalidOperationException("Explicit disposable calibration opt-in and mode required");
var connection = Environment.GetEnvironmentVariable("E2_CALIBRATION_NPGSQL")
    ?? throw new InvalidOperationException("Missing calibration connection");
var info = new NpgsqlConnectionStringBuilder(connection);
if (info.Host != "127.0.0.1" || info.Port != 55438 || info.Database != "e2calibration" ||
    info.Username != "postgres")
    throw new InvalidOperationException("Only the fixed disposable loopback fixture is permitted");
var mode = args[0];
var builder = Host.CreateApplicationBuilder();
builder.Logging.ClearProviders();
builder.Services.AddSingleton<NpgsqlDataSource>(_ => new NpgsqlDataSourceBuilder(connection).Build());
builder.Services.AddSingleton<IDurableLedger, PgDurableLedger>();
builder.Services.AddSingleton<IIncomingGrainCallFilter, CalibrationObserver>();
builder.UseOrleans(silo => silo.UseLocalhostClustering(
    siloPort: 11238, gatewayPort: 30238, serviceId: "e2-calibration",
    clusterId: "e2-calibration-" + mode)
    .Configure<ClusterOptions>(o => { o.ServiceId = "e2-calibration"; o.ClusterId = "e2-calibration-" + mode; }));
using var host = builder.Build();
await host.StartAsync();
CalibrationObserver.Ready();
var client = host.Services.GetRequiredService<IClusterClient>();
var grain = client.GetGrain<ICalibrationGrain>(1);
var commands = new[] { new TransferCommand("e2-observer-calibration", 1, 2, 31),
                       new TransferCommand("e2-observer-calibration", 1, 2, 37) };
try
{
    if (mode == "single")
    {
        try
        {
            await grain.Transfer(commands[0]).WaitAsync(TimeSpan.FromSeconds(12));
            throw new InvalidOperationException("Single-request barrier unexpectedly passed");
        }
        catch (TimeoutException)
        {
            Console.WriteLine("E2_CALIBRATION_RESULTS:" + JsonSerializer.Serialize(new
            { mode, status = "EXPECTED_BARRIER_TIMEOUT", financialCommandsExpected = 0 }));
        }
    }
    else
    {
        var first = grain.Transfer(commands[0]);
        await CalibrationGrain.FirstEntry.WaitAsync(TimeSpan.FromSeconds(8));
        var second = grain.Transfer(commands[1]);
        var outcomes = await Task.WhenAll(first, second).WaitAsync(TimeSpan.FromSeconds(25));
        if (outcomes.Count(r => r.Status == "COMMITTED") != 1 ||
            outcomes.Count(r => r.Status == "ID_CONFLICT") != 1)
            throw new InvalidOperationException("One COMMITTED and one ID_CONFLICT are required");
        var winner = Array.FindIndex(outcomes, r => r.Status == "COMMITTED");
        var replay = await grain.Transfer(commands[winner]);
        var conflict = await grain.Transfer(commands[1 - winner]);
        if (replay.Status != "DUPLICATE_COMMITTED" || conflict.Status != "ID_CONFLICT")
            throw new InvalidOperationException("Replay/conflict contract failed");
        Console.WriteLine("E2_CALIBRATION_RESULTS:" + JsonSerializer.Serialize(new
        { mode, status = "COMPLETED", commands, outcomes, winner, replay, conflict }));
    }
}
finally
{
    Console.Out.Flush();
    await host.StopAsync();
}
