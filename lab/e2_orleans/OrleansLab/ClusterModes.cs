using System.Net;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Orleans;
using Orleans.Configuration;
using Orleans.Hosting;

namespace E2.OrleansLab;

/// <summary>
/// Two real OS-hosted silos and a distinct Orleans client. Membership uses
/// Orleans development clustering on loopback ONLY. Not production clustering,
/// not separate physical nodes, and not a production failover claim.
/// </summary>
public static class ClusterModes
{
    private const int PrimarySiloPort = 11150;
    private const int PrimaryGatewayPort = 30050;
    private const int SecondarySiloPort = 11151;
    private const int SecondaryGatewayPort = 30051;
    private const string Service = "e2-multiprocess-lab";
    // Only the isolated E2-F09 fixture may choose a different deployment
    // identity; this avoids stale membership records between failure cases.
    private static string Cluster =>
        Environment.GetEnvironmentVariable("E2_INFLIGHT_TEST") == "1" &&
        Environment.GetEnvironmentVariable("E2_CLUSTER_INSTANCE") is
            ("e2-inflight-pre" or "e2-inflight-post")
        ? Environment.GetEnvironmentVariable("E2_CLUSTER_INSTANCE")!
        : "e2-local-recovery";
    // Switching providers is a test-fixture choice, not a change in
    // account authority or a different durable transfer implementation.
    private static bool AdoNet =>
        Environment.GetEnvironmentVariable("E2_CLUSTER_PROVIDER") == "adonet";

    private static string MembershipConnection()
    {
        var connection = Environment.GetEnvironmentVariable("E2_MEMBERSHIP_NPGSQL")
            ?? throw new InvalidOperationException(
                "An explicitly configured E2_MEMBERSHIP_NPGSQL is required for ADO.NET membership");
        var info = new NpgsqlConnectionStringBuilder(connection);
        if (info.Database != "e2lab" ||
            info.Host is not ("127.0.0.1" or "localhost"))
            throw new InvalidOperationException(
                "The disposable membership database must be e2lab over loopback");
        return connection;
    }
    private static readonly JsonSerializerOptions JsonOptions =
        new() { PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                 PropertyNameCaseInsensitive = true };

    public static async Task<int> Run(string[] args)
    {
        if (Environment.GetEnvironmentVariable("E2_CLUSTER_TEST") != "1")
        {
            Console.Error.WriteLine("The isolated E2 cluster fixture must be opted in");
            return 6;
        }
        var conn = Environment.GetEnvironmentVariable("E2_PG_NPGSQL")
            ?? throw new InvalidOperationException("E2_PG_NPGSQL is required");
        var info = new NpgsqlConnectionStringBuilder(conn);
        if (info.Database != "e2lab" ||
            info.Host is not ("127.0.0.1" or "localhost"))
            throw new InvalidOperationException("The cluster fixture requires a disposable loopback e2lab database");

        if (args.Length == 2 && args[0] == "silo" && (args[1] is "primary" or "secondary"))
            return await RunSilo(conn, args[1]);
        if (args.Length == 2 && args[0] == "client" && args[1] == "probe")
            return await RunClient(null);
        if (args.Length == 3 && args[0] == "client" && args[1] == "execute" &&
            File.Exists(args[2]))
            return await RunClient(args[2]);

        Console.Error.WriteLine("Usage: cluster silo <primary|secondary> | cluster client probe | cluster client execute <scenario.json>");
        return 4;
    }

    private static async Task<int> RunSilo(string conn, string role)
    {
        var port = role == "primary" ? PrimarySiloPort : SecondarySiloPort;
        var gateway = role == "primary" ? PrimaryGatewayPort : SecondaryGatewayPort;
        var builder = Host.CreateApplicationBuilder();
        builder.Logging.ClearProviders();
        builder.Services.AddSingleton<NpgsqlDataSource>(
            _ => new NpgsqlDataSourceBuilder(conn).Build());
        builder.Services.AddSingleton<IDurableLedger, PgDurableLedger>();
        // A primary development silo must use null, not its own endpoint.
        // The secondary joins the explicitly designated primary endpoint.
        // UseLocalhostClustering binds/advertises loopback consistently.
        IPEndPoint? primary = role == "primary"
            ? null
            : new IPEndPoint(IPAddress.Loopback, PrimarySiloPort);
        if (AdoNet)
        {
            var membershipConnection = MembershipConnection();
            builder.UseOrleans(silo => silo
                .UseAdoNetClustering(options =>
                {
                    options.Invariant = "Npgsql";
                    options.ConnectionString = membershipConnection;
                })
                .Configure<ClusterOptions>(options =>
                {
                    options.ServiceId = Service;
                    options.ClusterId = Cluster;
                })
                .ConfigureEndpoints(siloPort: port, gatewayPort: gateway,
                    advertisedIP: IPAddress.Loopback));
        }
        else
        {
            builder.UseOrleans(silo => silo.UseLocalhostClustering(
                siloPort: port, gatewayPort: gateway,
                primarySiloEndpoint: primary, serviceId: Service, clusterId: Cluster));
        }
        using var host = builder.Build();
        await host.StartAsync();
        Console.WriteLine("E2_SILO_READY:" + role + ":" + Environment.ProcessId);
        Console.Out.Flush();
        await host.WaitForShutdownAsync();
        return 0;
    }

    private static async Task<int> RunClient(string? scenarioPath)
    {
        var builder = Host.CreateApplicationBuilder();
        builder.Logging.ClearProviders();
        if (AdoNet)
        {
            var membershipConnection = MembershipConnection();
            builder.UseOrleansClient(client => client
                .UseAdoNetClustering(options =>
                {
                    options.Invariant = "Npgsql";
                    options.ConnectionString = membershipConnection;
                })
                .Configure<ClusterOptions>(options =>
                {
                    options.ServiceId = Service;
                    options.ClusterId = Cluster;
                }));
        }
        else
        {
            builder.UseOrleansClient(client => client
                .UseStaticClustering(
                    new IPEndPoint(IPAddress.Loopback, PrimaryGatewayPort),
                    new IPEndPoint(IPAddress.Loopback, SecondaryGatewayPort))
                .Configure<ClusterOptions>(options =>
                {
                    options.ServiceId = Service;
                    options.ClusterId = Cluster;
                }));
        }
        using var host = builder.Build();
        await host.StartAsync();
        try
        {
            var cluster = host.Services.GetRequiredService<IClusterClient>();
            if (scenarioPath is null)
            {
                var hosts = new Dictionary<int, int>();
                for (var account = 1; account <= 16; account++)
                    hosts.Add(account, await cluster.GetGrain<IAccountGrain>(account).HostProcessId());
                Console.WriteLine(JsonSerializer.Serialize(new {
                    experiment = "E2-Two-Independent-OS-Silos",
                    status = "PROBED",
                    clientPid = Environment.ProcessId,
                    accountHostPids = hosts
                }, JsonOptions));
                return 0;
            }
            var scenario = JsonSerializer.Deserialize<Scenario>(
                await File.ReadAllTextAsync(scenarioPath), JsonOptions)
                ?? throw new ArgumentException("Missing scenario");
            if (scenario.Route != "orleans" || scenario.Commands.Count is < 1 or > 16)
                throw new ArgumentException("External cluster client accepts 1..16 Orleans commands only");

            var outcome = new List<object>();
            foreach (var cmd in scenario.Commands)
            {
                if (!PgDurableLedger.Valid(cmd))
                    throw new ArgumentException("Invalid synthetic transfer");
                var grain = cluster.GetGrain<IAccountGrain>(cmd.SourceAccountId);
                var result = await grain.Transfer(cmd);
                outcome.Add(new {
                    command = cmd.OperationId, result.Status, result.Retries,
                    result.RetrySqlStates, result.HandledBy,
                    actualSiloProcessId = await grain.HostProcessId()
                });
            }
            Console.WriteLine(JsonSerializer.Serialize(new {
                experiment = "E2-Two-Independent-OS-Silos",
                status = "EXECUTED",
                clientPid = Environment.ProcessId,
                results = outcome
            }, JsonOptions));
            return 0;
        }
        finally
        {
            await host.StopAsync();
        }
    }
}
