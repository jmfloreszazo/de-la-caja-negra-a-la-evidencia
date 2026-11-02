using System.Diagnostics;
using System.Text.Json;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Npgsql;
using Orleans;
using Orleans.Configuration;
using Orleans.Hosting;

namespace E2.OrleansLab;

// This is a bounded B05 external-client SMOKE harness, not sustained capacity
// or a reference mainframe benchmark. PostgreSQL remains the single ledger.
internal static class B05LoadClient
{
    private const int MaximumOffers = 120;
    private const int MaximumPilotOffers = 2_000;
    private const int MaximumCommitWindowOffers = 5_000;
    private const int MaximumOverloadOffers = 20_000;
    private const int MaximumInflight = 32;
    private static readonly JsonSerializerOptions Options = new()
    {
        PropertyNameCaseInsensitive = true,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    internal sealed record Offer(
        string OperationId, string Phase, long ScheduledAtNs,
        int SourceAccountId, int TargetAccountId, long AmountCents,
        string Fault);
    internal sealed record Vector(
        string Status, bool CapacityEvidence, int AccountCount,
        int OfferedRatePerSecond, int TotalOfferedRequests,
        List<Offer> Operations);
    internal sealed record Sample(
        string OperationId, string Phase, long ScheduledAtNs,
        long? DispatchedAtNs, long? CompletedAtNs,
        string ClientOutcome, string? LedgerStatus, int Retries,
        string? ErrorType);

    private static long Ns(Stopwatch clock) =>
        (long)(clock.ElapsedTicks * (1_000_000_000.0 / Stopwatch.Frequency));

    internal static async Task<int> Run(
        string route, string file, string conn, string? membership,
        string service, string cluster)
    {
        var pilot = Environment.GetEnvironmentVariable("E2_B05_REPEATABILITY") == "1";
        var commitWindow = Environment.GetEnvironmentVariable("E2_B05_COMMIT_WINDOW") == "1";
        var overload = Environment.GetEnvironmentVariable("E2_B05_OVERLOAD_SWEEP") == "1";
        if (overload && (!commitWindow || pilot))
            throw new InvalidOperationException("B05 overload must be an isolated SQL COMMIT-window mode");
        if (pilot && commitWindow)
            throw new InvalidOperationException("Mutually exclusive B05 experimental modes");
        if (Environment.GetEnvironmentVariable("E2_B05_SMOKE") != "1" ||
            Environment.GetEnvironmentVariable("E2_NETWORK_TEST") != "1" ||
            Environment.GetEnvironmentVariable("E2_MAX_ACCOUNT_ID") != "1000")
            throw new InvalidOperationException(
                "B05 requires explicit disposable Podman and 1000-account opt-in");
        if (route is not ("direct" or "orleans"))
            throw new ArgumentException("Only direct/orleans B05 paths are allowed");

        var vector = JsonSerializer.Deserialize<Vector>(
            await File.ReadAllTextAsync(file), Options)
            ?? throw new InvalidOperationException("Missing B05 vector");
        if (vector.Status != "GENERATED_NOT_EXECUTED" ||
            vector.CapacityEvidence || vector.AccountCount != 1000 ||
            vector.OfferedRatePerSecond < 1 ||
            vector.OfferedRatePerSecond > (overload ? 320 : 100) ||
            (overload && vector.OfferedRatePerSecond is not (160 or 320)) ||
            vector.Operations is null ||
            vector.Operations.Count != vector.TotalOfferedRequests ||
            vector.Operations.Count < 1 ||
            vector.Operations.Count > (overload ? MaximumOverloadOffers :
                commitWindow ? MaximumCommitWindowOffers :
                pilot ? MaximumPilotOffers : MaximumOffers))
            throw new InvalidOperationException("Unaccepted bounded B05 vector");

        long previous = -1;
        var ids = new HashSet<string>(StringComparer.Ordinal);
        foreach (var operation in vector.Operations)
        {
            var cmd = new TransferCommand(
                operation.OperationId, operation.SourceAccountId,
                operation.TargetAccountId, operation.AmountCents, operation.Fault);
            if (!PgDurableLedger.Valid(cmd) ||
                operation.Phase is not ("warmup" or "measurement" or "cooldown") ||
                operation.ScheduledAtNs <= previous ||
                operation.ScheduledAtNs > (commitWindow ? 90_000_000_000L :
                    pilot ? 60_000_000_000L : 10_000_000_000L) ||
                !ids.Add(operation.OperationId))
                throw new InvalidOperationException(
                    "Invalid, duplicate or unbounded B05 scheduled offer");
            previous = operation.ScheduledAtNs;
        }

        var builder = Host.CreateApplicationBuilder();
        builder.Logging.ClearProviders();
        builder.Services.AddSingleton<NpgsqlDataSource>(
            _ => new NpgsqlDataSourceBuilder(conn).Build());
        builder.Services.AddSingleton<IDurableLedger, PgDurableLedger>();
        if (route == "orleans")
        {
            if (membership is null)
                throw new InvalidOperationException(
                    "ADO.NET membership required for isolated external client");
            builder.UseOrleansClient(client => client
                .UseAdoNetClustering(opt =>
                {
                    opt.Invariant = "Npgsql";
                    opt.ConnectionString = membership;
                })
                .Configure<ClusterOptions>(opt =>
                {
                    opt.ServiceId = service;
                    opt.ClusterId = cluster;
                }));
        }

        using var host = builder.Build();
        await host.StartAsync();
        try
        {
            var ledger = host.Services.GetRequiredService<IDurableLedger>();
            var grains = route == "orleans"
                ? host.Services.GetRequiredService<IClusterClient>()
                : null;
            // Bracket the monotonic clock origin with two UTC samples. The
            // independent SQL oracle computes conservative in-window commit
            // bounds using these anchors and PostgreSQL commit timestamps.
            var clockOriginUtcBefore = DateTimeOffset.UtcNow;
            var clock = Stopwatch.StartNew();
            var clockOriginUtcAfter = DateTimeOffset.UtcNow;
            using var capacity = new SemaphoreSlim(MaximumInflight);
            var samples = new List<Task<Sample>>(vector.Operations.Count);

            async Task<Sample> ExecuteOne(Offer offer, long dispatchedAt)
            {
                try
                {
                    var command = new TransferCommand(
                        offer.OperationId, offer.SourceAccountId,
                        offer.TargetAccountId, offer.AmountCents, offer.Fault);
                    var outcome = route == "direct"
                        ? await ledger.Transfer(command)
                        : await grains!.GetGrain<IAccountGrain>(
                            command.SourceAccountId).Transfer(command);
                    return new Sample(
                        offer.OperationId, offer.Phase, offer.ScheduledAtNs,
                        dispatchedAt, Ns(clock), "ACKNOWLEDGED", outcome.Status,
                        outcome.Retries, null);
                }
                catch (Exception exception)
                {
                    // Exception/timeouts may conceal a SQL COMMIT. Never
                    // translate them into a confirmed rollback or no-op.
                    return new Sample(
                        offer.OperationId, offer.Phase, offer.ScheduledAtNs,
                        dispatchedAt, Ns(clock), "AMBIGUOUS_EXCEPTION",
                        null, 0, exception.GetType().Name);
                }
                finally
                {
                    capacity.Release();
                }
            }

            foreach (var offer in vector.Operations)
            {
                // Task.Delay may wake BEFORE the requested monotonic
                // deadline because of timer resolution. Never declare a
                // scheduled offer dispatched early; recheck the clock.
                long remainingNs;
                while ((remainingNs = offer.ScheduledAtNs - Ns(clock)) > 0)
                {
                    if (remainingNs > 2_000_000L)
                        await Task.Delay(TimeSpan.FromMilliseconds(
                            (remainingNs - 1_000_000L) / 1_000_000.0));
                    else
                        await Task.Yield();
                }
                var dispatchedAt = Ns(clock);
                if (!capacity.Wait(0))
                {
                    // No waiting for a free slot: open-loop offered arrivals
                    // must not become a closed-loop workload under overload.
                    samples.Add(Task.FromResult(new Sample(
                        offer.OperationId, offer.Phase, offer.ScheduledAtNs,
                        null, null, "MISSED_OFFER_INFLIGHT_LIMIT",
                        null, 0, null)));
                    continue;
                }
                samples.Add(ExecuteOne(offer, dispatchedAt));
            }

            var observed = await Task.WhenAll(samples);
            clock.Stop();
            var acknowledgedCommits = observed.Count(s =>
                s.ClientOutcome == "ACKNOWLEDGED" &&
                s.LedgerStatus == "COMMITTED");
            var report = new
            {
                schemaVersion = 1,
                experiment = overload
                    ? "E2-B05-160-320-Offer-Rate-Overload"
                    : commitWindow ? "E2-B05-Independent-SQL-Commit-Window"
                    : pilot ? "E2-B05-External-Repeatability-Pilot"
                    : "E2-B05-External-Open-Loop-Smoke",
                classification = overload
                    ? "SINGLE_HOST_FINITE_OVERLOAD_SWEEP_NOT_CAPACITY"
                    : commitWindow ? "SINGLE_HOST_FIRST_60_SECOND_COMMIT_TIME_SLICE_NOT_CAPACITY"
                    : pilot ? "BOUNDED_MULTIRUN_ONE_HOST_NOT_CAPACITY"
                    : "SHORT_SINGLE_HOST_BOUNDED_NOT_CAPACITY",
                route,
                status = overload
                    ? "OBSERVED_OVERLOAD_SWEEP_NOT_CAPACITY"
                    : commitWindow ? "OBSERVED_COMMIT_WINDOW_PROBE_NOT_CAPACITY"
                    : pilot ? "OBSERVED_REPEATABILITY_PILOT_NOT_CAPACITY"
                    : "OBSERVED_NOT_SUSTAINED_CAPACITY",
                independentExternalProcessId = Environment.ProcessId,
                hostIdentity = Environment.MachineName,
                offered = vector.TotalOfferedRequests,
                dispatched = observed.Count(s => s.DispatchedAtNs.HasValue),
                missed = observed.Count(s => s.ClientOutcome.StartsWith("MISSED_")),
                acknowledgedCommitted = acknowledgedCommits,
                ambiguous = observed.Count(s => s.ClientOutcome == "AMBIGUOUS_EXCEPTION"),
                runWallClockNs = Ns(clock),
                clockOriginUtcBefore = clockOriginUtcBefore.ToString("O"),
                clockOriginUtcAfter = clockOriginUtcAfter.ToString("O"),
                samples = observed,
                limits = overload
                    ? "One physical Linux host, exactly 160/320 offered intents/s with 60-second SQL COMMIT observation, 32 maximum inflight and finite 20,000-offer/trial cap. Missed and ambiguous work must be retained. No saturation-capacity guarantee, production p99, physical HA or IBM Z/MIPS parity."
                    : commitWindow ? "One physical Linux host, bounded 60-second SQL COMMIT-time probe. Timestamp tracking must be enabled on the disposable PostgreSQL instance and independently audited. PostgreSQL and .NET share the same host wall clock; this is not a multi-host clock-synchronization proof. No durable capacity ceiling, MIPS parity or production p99."
                    : pilot
                    ? "A bounded repeated fixed-clock pilot on ONE Linux host, not a production system or an independent load host. No sustainable capacity limit, SLA p99, mainframe MIPS or cross-host scaling. Only SQL can confirm business effects."
                    : "One physical Linux host with separate Podman processes and namespaces. Bounded four-second replay only. No sustained throughput ceiling, mainframe MIPS or production p99 claim. Acknowledgements are NOT a substitute for the independent PostgreSQL oracle."
            };
            Console.WriteLine(JsonSerializer.Serialize(report, Options));
            return 0;
        }
        finally
        {
            await host.StopAsync();
        }
    }
}
