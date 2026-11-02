using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Orleans;
using Orleans.Configuration;
using Orleans.Hosting;
using Orleans.Runtime;
using Orleans.Runtime.Placement;

namespace E2.OrleansLab;

// Test-only activation seeding, never financial authority or a default policy.
// Ordinary clients and the accepted AccountGrain/SQL transaction are unchanged.
public static class ControlledPlacementProbe
{
    public static async Task<int> Run(string membership, string service, string cluster, string mode)
    {
        var info = new NpgsqlConnectionStringBuilder(membership);
        if (Environment.GetEnvironmentVariable("E2_NETWORK_TEST") != "1" ||
            Environment.GetEnvironmentVariable("E2_CLUSTER_TEST") != "1" ||
            Environment.GetEnvironmentVariable("E2_CLUSTER_PROVIDER") != "adonet" ||
            info.Database != "e2lab" || info.Host != "10.78.30.10" ||
            service != "e2-multiprocess-lab" || cluster != "e2-f10-podman-bridge" ||
            mode is not ("secondary-only" or "alternating"))
            throw new InvalidOperationException("Controlled placement requires the exact disposable C01 fixture");

        var builder = Host.CreateApplicationBuilder();
        builder.Logging.ClearProviders();
        builder.UseOrleansClient(client => client
            .UseAdoNetClustering(options =>
            {
                options.Invariant = "Npgsql";
                options.ConnectionString = membership;
            })
            .Configure<ClusterOptions>(options =>
            {
                options.ServiceId = service;
                options.ClusterId = cluster;
            }));
        using var host = builder.Build();
        await host.StartAsync();
        try
        {
            var client = host.Services.GetRequiredService<IClusterClient>();
            var manager = client.GetGrain<IManagementGrain>(0);
            var hosts = await manager.GetHosts(onlyActive: true);
            if (hosts.Count != 2 || hosts.Values.Any(value => value != SiloStatus.Active))
                throw new InvalidOperationException("Exactly two active C01 silos are required");
            var primary = hosts.Keys.Single(s => s.Endpoint.Address.ToString() == "10.78.30.11"
                                                 && s.Endpoint.Port == 11150);
            var secondary = hosts.Keys.Single(s => s.Endpoint.Address.ToString() == "10.78.30.12"
                                                   && s.Endpoint.Port == 11151);
            // Bounded membership propagation delay; not a placement retry or
            // a financial retry. Observed host identities remain mandatory.
            await Task.Delay(TimeSpan.FromSeconds(2));
            var nodes = new Dictionary<int, string>();
            var pids = new Dictionary<int, int>();
            var requested = new Dictionary<int, string>();
            var addresses = new Dictionary<int, string>();
            for (int key = 1; key <= 16; key++)
            {
                var target = mode == "secondary-only" || key % 2 == 0 ? secondary : primary;
                requested[key] = target.Equals(primary) ? "e2f10-primary" : "e2f10-secondary";
                addresses[key] = target.ToString();
                RequestContext.Set(IPlacementDirector.PlacementHintKey, target);
                try
                {
                    // Identity methods ONLY. No Transfer() or ledger write.
                    var grain = client.GetGrain<IAccountGrain>(key);
                    nodes[key] = await grain.HostNodeIdentity();
                    pids[key] = await grain.HostProcessId();
                }
                finally
                {
                    RequestContext.Remove(IPlacementDirector.PlacementHintKey);
                }
            }
            Console.WriteLine(JsonSerializer.Serialize(new
            {
                status = "CONTROLLED_PROBED",
                mode,
                accountHostNodes = nodes,
                accountHostPids = pids,
                requestedNodeNames = requested,
                requestedSiloAddresses = addresses,
                activeHosts = hosts.Keys.Select(s => s.ToString()).Order().ToArray(),
                financialCommandsDispatched = 0,
                placementHintRetained = RequestContext.Get(IPlacementDirector.PlacementHintKey) is not null,
                mechanism = "C01_TEST_ONLY_COMPATIBLE_SILO_PLACEMENT_HINT",
                limitation = "Hints select new activations only; they do not relocate existing grains or authorize SQL COMMIT"
            }));
            return 0;
        }
        finally
        {
            RequestContext.Remove(IPlacementDirector.PlacementHintKey);
            await host.StopAsync();
        }
    }
}
