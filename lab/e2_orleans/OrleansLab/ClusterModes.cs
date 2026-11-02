using System.Net;
using System.Net.Sockets;
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
        ContainerFixture ? "e2-f10-podman-bridge" :
        Environment.GetEnvironmentVariable("E2_INFLIGHT_TEST") == "1" &&
        Environment.GetEnvironmentVariable("E2_CLUSTER_INSTANCE") is
            ("e2-inflight-pre" or "e2-inflight-post")
        ? Environment.GetEnvironmentVariable("E2_CLUSTER_INSTANCE")!
        : "e2-local-recovery";
    private static bool ContainerFixture =>
        Environment.GetEnvironmentVariable("E2_NETWORK_TEST") == "1" &&
        Environment.GetEnvironmentVariable("E2_CLUSTER_TEST") == "1" &&
        Environment.GetEnvironmentVariable("E2_CLUSTER_PROVIDER") == "adonet";

    private static bool DisposableHost(string? host) =>
        host is "127.0.0.1" or "localhost" ||
        (ContainerFixture && (host is "e2f10-pg" or "10.78.30.10" or "10.78.31.10"));

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
        if (info.Database != "e2lab" || !DisposableHost(info.Host))
            throw new InvalidOperationException(
                "Membership requires disposable loopback e2lab or explicitly opted-in e2f10-pg container");
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
        if (info.Database != "e2lab" || !DisposableHost(info.Host))
            throw new InvalidOperationException(
                "The cluster fixture requires disposable loopback e2lab or opted-in e2f10-pg");

        // A separate, explicitly disposable load-generator process.
        // These observations are a short functional smoke, never B05 capacity.
        if (args.Length == 4 && args[0] == "benchmark" &&
            args[1] is "direct" or "orleans" &&
            args[2] == "replay" && File.Exists(args[3]) &&
            ContainerFixture)
            return await B05LoadClient.Run(
                args[1], args[3], conn,
                args[1] == "orleans" ? MembershipConnection() : null,
                Service, Cluster);

        if (args.Length == 1 && args[0] == "network-check" && ContainerFixture)
            return await RunNetworkCheck(conn, observeDatabaseFailure: false);
        if (args.Length == 1 && args[0] == "network-check-sql" && ContainerFixture)
            return await RunNetworkCheck(conn, observeDatabaseFailure: true);

        if (args.Length == 2 && args[0] == "silo" && (args[1] is "primary" or "secondary"))
            return await RunSilo(conn, args[1]);
        if (args.Length == 2 && args[0] == "client" && args[1] == "probe")
            return await RunClient(null);
        // Diagnostic-only fresh grain activation probe: no ledger writes.
        // The original 1..16 financial-account probe and its acceptance gate
        // remain unchanged. Exactly 17..64, only on disposable CI networks.
        if (ContainerFixture && args.Length == 4 &&
            args[0] == "client" && args[1] == "probe-range" &&
            args[2] == "17" && args[3] == "48")
            return await RunClient(null, probeStart: 17, probeCount: 48);
        if (args.Length == 3 && args[0] == "client" && args[1] == "execute" &&
            File.Exists(args[2]))
            return await RunClient(args[2]);

        Console.Error.WriteLine("Usage: cluster silo <primary|secondary> | cluster client probe | cluster client execute <scenario.json>");
        return 4;
    }

    private static IPAddress AdvertisedAddress(string role)
    {
        if (!ContainerFixture)
            return IPAddress.Loopback;
        // No arbitrary advertised addresses or public endpoints. This is
        // an explicitly disposable Podman bridge, NOT a production mode.
        var expected = role == "primary" ? "10.78.30.11" : "10.78.30.12";
        if (Environment.GetEnvironmentVariable("E2_ADVERTISED_IP") != expected)
            throw new InvalidOperationException(
                "E2-F10 silo must advertise the exact fixed private bridge address");
        return IPAddress.Parse(expected);
    }

    // F10 checks a live silo's separate SQL network and exact private
    // Orleans transport bridge. TCP reachability is NOT grain rebalancing.
    private static async Task<int> RunNetworkCheck(
        string conn, bool observeDatabaseFailure)
    {
        // Preserve the strict original C01/C02 network-check contract.
        // C03 explicitly opts into a bounded fresh connection because the
        // SQL outage itself is its measured fault.
        var databaseHealthy = false;
        if (!observeDatabaseFailure)
        {
            using var dataSource = NpgsqlDataSource.Create(conn);
            await using var command = dataSource.CreateCommand("SELECT 1");
            var value = await command.ExecuteScalarAsync();
            if (Convert.ToInt32(value) != 1)
                throw new InvalidOperationException("Disposable SQL health probe failed");
            databaseHealthy = true;
        }
        else
        {
            try
            {
                var configured = new NpgsqlConnectionStringBuilder(conn)
                {
                    Pooling = false,
                    Timeout = 8,
                    CommandTimeout = 8
                };
                await using var connection = new NpgsqlConnection(configured.ConnectionString);
                using var deadline = new CancellationTokenSource(TimeSpan.FromSeconds(16));
                await connection.OpenAsync(deadline.Token);
                await using var command = new NpgsqlCommand("SELECT 1", connection);
                databaseHealthy =
                    Convert.ToInt32(await command.ExecuteScalarAsync(deadline.Token)) == 1;
            }
            catch (Exception ex) when (
                ex is NpgsqlException or TimeoutException or OperationCanceledException)
            {
                // Probe health is false; independent SQL state remains authoritative.
            }
        }

        static async Task<bool> CanConnect(IPAddress address, int port)
        {
            using var socket = new TcpClient();
            using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(2));
            try
            {
                await socket.ConnectAsync(address, port, timeout.Token);
                return true;
            }
            catch (SocketException) { return false; }
            catch (OperationCanceledException) { return false; }
        }

        var primaryReachable = await CanConnect(
            IPAddress.Parse("10.78.30.11"), PrimaryGatewayPort);
        var secondaryReachable = await CanConnect(
            IPAddress.Parse("10.78.30.12"), SecondaryGatewayPort);
        Console.WriteLine(JsonSerializer.Serialize(new {
            experiment = "E2-F10-C02-Transport-Partition-Probe",
            status = "PROBED",
            hostIdentity = Environment.MachineName,
            databaseHealthy,
            primaryGatewayReachable = primaryReachable,
            secondaryGatewayReachable = secondaryReachable
        }, JsonOptions));
        return 0;
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
                    advertisedIP: AdvertisedAddress(role),
                    listenOnAnyHostAddress: ContainerFixture));
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

    private static async Task<int> RunClient(
        string? scenarioPath, int probeStart = 1, int probeCount = 16)
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
                var nodes = new Dictionary<int, string>();
                if (!((probeStart == 1 && probeCount == 16) ||
                      (ContainerFixture && probeStart == 17 && probeCount == 48)))
                    throw new InvalidOperationException(
                        "Unapproved test-only grain placement diagnostic range");
                for (var account = probeStart; account < probeStart + probeCount; account++)
                {
                    // Host identity only. No Transfer command or SQL business
                    // operation is executed for diagnostic-only keys 17..64.
                    var grain = cluster.GetGrain<IAccountGrain>(account);
                    hosts.Add(account, await grain.HostProcessId());
                    nodes.Add(account, await grain.HostNodeIdentity());
                }
                Console.WriteLine(JsonSerializer.Serialize(new {
                    experiment = "E2-Two-Independent-OS-Silos",
                    status = "PROBED",
                    diagnosticOnly = probeStart == 17,
                    probeStart,
                    probeCount,
                    clientPid = Environment.ProcessId,
                    accountHostPids = hosts,
                    accountHostNodes = nodes,
                    clientNodeIdentity = Environment.MachineName + ":" + Environment.ProcessId
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
                    actualSiloProcessId = await grain.HostProcessId(),
                    actualSiloNodeIdentity = await grain.HostNodeIdentity()
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
