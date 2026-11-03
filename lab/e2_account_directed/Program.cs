using System.Net;
using E2.OrleansLab;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Orleans;
using Orleans.Configuration;
using Orleans.Hosting;

// Separate disposable observer host. The referenced financial grain and SQL
// ledger are compiled from their unmodified source, never copied or replaced.
if (Environment.GetEnvironmentVariable("E2_ACCOUNT_DIRECTED_TEST") != "1" || args.Length != 3 || args[0] != "cluster" || args[1] != "silo" ||
    args[2] is not ("primary" or "secondary") ||
    Environment.GetEnvironmentVariable("E2_ACTIVATION_OBSERVATION_TEST") != "1" ||
    Environment.GetEnvironmentVariable("E2_CLUSTER_TEST") != "1" ||
    Environment.GetEnvironmentVariable("E2_NETWORK_TEST") != "1" ||
    Environment.GetEnvironmentVariable("E2_CLUSTER_PROVIDER") != "adonet")
    throw new InvalidOperationException("DirectedSilo requires the exact disposable E2 fixture");

var role = args[2];
var address = role == "primary" ? "10.78.30.11" : "10.78.30.12";
if (Environment.GetEnvironmentVariable("E2_ADVERTISED_IP") != address)
    throw new InvalidOperationException("Unexpected observer fixture address");

string Connection(string variable)
{
    var value = Environment.GetEnvironmentVariable(variable)
        ?? throw new InvalidOperationException("Missing " + variable);
    var info = new NpgsqlConnectionStringBuilder(value);
    if (info.Host != "10.78.30.10" || info.Database != "e2lab" || info.Port != 5432)
        throw new InvalidOperationException("Observer connections require disposable e2lab");
    return value;
}

var connection = Connection("E2_PG_NPGSQL");
var membership = Connection("E2_MEMBERSHIP_NPGSQL");
var builder = Host.CreateApplicationBuilder();
builder.Logging.ClearProviders();
builder.Services.AddSingleton<NpgsqlDataSource>(_ => new NpgsqlDataSourceBuilder(connection).Build());
builder.Services.AddSingleton<IDurableLedger, PgDurableLedger>();
builder.Services.AddSingleton<IIncomingGrainCallFilter, DirectedTransferObserver>();
builder.UseOrleans(silo => silo
    .UseAdoNetClustering(options =>
    {
        options.Invariant = "Npgsql";
        options.ConnectionString = membership;
    })
    .Configure<ClusterOptions>(options =>
    {
        options.ServiceId = "e2-multiprocess-lab";
        options.ClusterId = "e2-f10-podman-bridge";
    })
    .ConfigureEndpoints(siloPort: role == "primary" ? 11150 : 11151,
        gatewayPort: role == "primary" ? 30050 : 30051,
        advertisedIP: IPAddress.Parse(address), listenOnAnyHostAddress: true));
using var host = builder.Build();
await host.StartAsync();
DirectedTransferObserver.Ready();
Console.WriteLine("E2_PLACEMENT_STRATEGY:" +
    host.Services.GetRequiredService<Orleans.Runtime.PlacementStrategy>().GetType().FullName);
Console.WriteLine("E2_SILO_READY:" + role + ":" + Environment.ProcessId);
Console.Out.Flush();
await host.WaitForShutdownAsync();
