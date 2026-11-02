using System.Diagnostics;
using System.Net;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Orleans;
using Orleans.Configuration;
using Orleans.Hosting;
using Orleans.Runtime;

namespace E2.OrleansLab;

// Isolated C05 observer: fixed gateway, bounded requests, no placement hints.
// A timeout after dispatch is ambiguous. PostgreSQL alone resolves effects.
public static class PartitionProbeClient
{
    public static async Task<int> Run(string connection, string service, string cluster,
                                      string gateway, string input)
    {
        var info = new NpgsqlConnectionStringBuilder(connection);
        if (Environment.GetEnvironmentVariable("E2_C05_TEST") != "1" ||
            info.Host != "10.78.30.10" || info.Database != "e2lab" ||
            service != "e2-multiprocess-lab" || cluster != "e2-f10-podman-bridge" ||
            gateway is not ("primary" or "secondary") ||
            (input != "observe" && !File.Exists(input)))
            throw new InvalidOperationException("C05 requires the exact disposable private fixture");

        var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true,
                                                  PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
        var clock = Stopwatch.StartNew();
        var output = new Dictionary<string, object?>
        {
            ["gateway"] = gateway, ["status"] = "STARTED", ["financialCommandsDispatched"] = 0,
            ["clientPid"] = Environment.ProcessId, ["startUtc"] = DateTimeOffset.UtcNow,
            ["placementHintsUsed"] = false
        };
        var builder = Host.CreateApplicationBuilder();
        builder.Logging.ClearProviders();
        builder.UseOrleansClient(client => client.UseStaticClustering(new IPEndPoint(
                IPAddress.Parse(gateway == "primary" ? "10.78.30.11" : "10.78.30.12"),
                gateway == "primary" ? 30050 : 30051))
            .Configure<ClusterOptions>(o => { o.ServiceId = service; o.ClusterId = cluster; }));
        using var host = builder.Build();
        var phase = "STARTUP";
        try
        {
            await host.StartAsync().WaitAsync(TimeSpan.FromSeconds(15));
            var client = host.Services.GetRequiredService<IClusterClient>();
            if (input == "observe")
            {
                phase = "CATALOG_OBSERVATION";
                var manager = client.GetGrain<IManagementGrain>(0);
                var hosts = await manager.GetHosts(false).WaitAsync(TimeSpan.FromSeconds(8));
                output["membershipView"] = hosts.Select(h => new
                    { address = h.Key.ToString(), status = h.Value.ToString() }).ToArray();
                // A management response is not an atomic simultaneous-activation census.
                var rows = await manager.GetDetailedGrainStatistics()
                    .WaitAsync(TimeSpan.FromSeconds(8));
                output["catalogRows"] = rows.Where(r => r.GrainType.Contains("AccountGrain"))
                    .Select(r => new { grainId = r.GrainId.ToString(), r.GrainType,
                                       siloAddress = r.SiloAddress.ToString() }).ToArray();
                output["status"] = "OBSERVED";
            }
            else
            {
                var scenario = JsonSerializer.Deserialize<Scenario>(await File.ReadAllTextAsync(input), options)
                    ?? throw new ArgumentException("Missing C05 scenario");
                if (scenario.Route != "orleans" || scenario.Commands.Count != 1 ||
                    !PgDurableLedger.Valid(scenario.Commands[0]) || scenario.Commands[0].Fault != "none")
                    throw new ArgumentException("Exactly one ordinary valid C05 command is required");
                var command = scenario.Commands[0];
                output["command"] = command;
                phase = "FINANCIAL_DISPATCH";
                output["financialCommandsDispatched"] = 1;
                var result = await client.GetGrain<IAccountGrain>(command.SourceAccountId)
                    .Transfer(command).WaitAsync(TimeSpan.FromSeconds(8));
                // Do not make a later identity RPC a condition for preserving the ACK.
                output["result"] = result;
                output["status"] = "ACKNOWLEDGED";
            }
        }
        catch (Exception ex)
        {
            output["status"] = phase == "STARTUP" ? "STARTUP_UNAVAILABLE" :
                phase == "FINANCIAL_DISPATCH" ? "DISPATCH_AMBIGUOUS" : "OBSERVATION_UNAVAILABLE";
            output["exceptionType"] = ex.GetType().FullName;
            output["error"] = ex.Message;
        }
        output["phase"] = phase;
        output["elapsedSeconds"] = clock.Elapsed.TotalSeconds;
        output["endUtc"] = DateTimeOffset.UtcNow;
        Console.WriteLine(JsonSerializer.Serialize(output, options));
        Console.Out.Flush();
        // Timed-out RPC tasks may still be outstanding. Terminate only this
        // disposable client; server-side effects remain unknown until SQL audit.
        Environment.Exit(0);
        return 0;
    }
}
