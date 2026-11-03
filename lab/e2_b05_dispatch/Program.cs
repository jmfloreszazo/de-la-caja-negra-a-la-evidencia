using System.Diagnostics;
using System.Text.Json;
using E2.OrleansLab;
using Npgsql;

if (Environment.GetEnvironmentVariable("E2_DISPATCH_DIAGNOSTIC") != "1" ||
    Environment.GetEnvironmentVariable("E2_MAX_ACCOUNT_ID") != "1000" ||
    args.Length != 2 || !File.Exists(args[0]) || args[1] is not ("32" or "128"))
    throw new InvalidOperationException("Exact disposable dispatch diagnostic opt-in required");
var configured = Environment.GetEnvironmentVariable("E2_DISPATCH_NPGSQL")
    ?? throw new InvalidOperationException("Missing diagnostic connection");
var info = new NpgsqlConnectionStringBuilder(configured);
if (info.Host != "127.0.0.1" || info.Port != 55439 || info.Database != "e2dispatch" ||
    info.Username != "postgres" || !info.Pooling || info.MaxPoolSize != 32)
    throw new InvalidOperationException("Only the fixed loopback e2dispatch / pool-32 fixture is allowed");
var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true,
    PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
var vector = JsonSerializer.Deserialize<Vector>(await File.ReadAllTextAsync(args[0]),options)
    ?? throw new InvalidOperationException("Missing vector");
if (vector.Status != "GENERATED_NOT_EXECUTED" || vector.CapacityEvidence ||
    vector.AccountCount != 1000 || vector.OfferedRatePerSecond != 320 ||
    vector.TotalOfferedRequests != 19840 || vector.Operations.Count != 19840)
    throw new InvalidOperationException("Exactly 320/s and 1+60+1 seconds are required");
long previous = -1;
var ids = new HashSet<string>(StringComparer.Ordinal);
foreach (var offer in vector.Operations)
{
    if (offer.ScheduledAtNs <= previous || offer.ScheduledAtNs >= 62_000_000_000L ||
        !ids.Add(offer.OperationId) || !PgDurableLedger.Valid(offer.Command()) ||
        offer.Phase is not ("warmup" or "measurement" or "cooldown") || offer.Fault != "none")
        throw new InvalidOperationException("Invalid fixed diagnostic offer");
    previous = offer.ScheduledAtNs;
}

await using var source = new NpgsqlDataSourceBuilder(configured).Build();
var ledger = new PgDurableLedger(source);
var maximum = int.Parse(args[1]);
using var slots = new SemaphoreSlim(maximum);
var gate = new object();
var trace = new List<SlotEvent>(vector.Operations.Count * 4);
var pending = new List<Task<Sample>>(vector.Operations.Count);
long sequence = 0;
int active = 0;
long Ns(Stopwatch clock) => (long)(clock.ElapsedTicks * (1_000_000_000.0 / Stopwatch.Frequency));
var process = Process.GetCurrentProcess();
var cpuBefore = process.TotalProcessorTime.TotalMilliseconds;
var gcBefore = Enumerable.Range(0,3).Select(GC.CollectionCount).ToArray();
var utcBefore = DateTimeOffset.UtcNow;
var clock = Stopwatch.StartNew();
var utcAfter = DateTimeOffset.UtcNow;

async Task<Sample> ExecuteOne(int index, Offer offer, long decision)
{
    string outcome, status;
    string? error = null;
    int retries = 0;
    try
    {
        var result = await ledger.Transfer(offer.Command());
        outcome = "ACKNOWLEDGED";
        status = result.Status;
        retries = result.Retries;
    }
    catch (Exception exception)
    {
        outcome = "AMBIGUOUS_EXCEPTION";
        status = "";
        error = exception.GetType().FullName;
    }
    long completed, released;
    lock (gate)
    {
        completed = Ns(clock);
        trace.Add(new(++sequence,index,"COMPLETE",completed,active));
        slots.Release();
        --active;
        released = Ns(clock);
        trace.Add(new(++sequence,index,"RELEASE",released,active));
    }
    return new(offer.OperationId,offer.Phase,offer.ScheduledAtNs,decision,decision,
        completed,released,outcome,status.Length==0?null:status,retries,error);
}

for (var index=0;index<vector.Operations.Count;index++)
{
    var offer = vector.Operations[index];
    long remaining;
    while ((remaining = offer.ScheduledAtNs - Ns(clock)) > 0)
    {
        if (remaining > 2_000_000L)
            await Task.Delay(TimeSpan.FromMilliseconds((remaining-1_000_000L)/1_000_000.0));
        else
            await Task.Yield();
    }
    long decision;
    bool admitted;
    lock (gate)
    {
        decision = Ns(clock);
        admitted = slots.Wait(0);
        if (admitted)
        {
            ++active;
            trace.Add(new(++sequence,index,"ADMIT",decision,active));
        }
        else
        {
            trace.Add(new(++sequence,index,"MISS",decision,active));
        }
    }
    pending.Add(admitted ? ExecuteOne(index,offer,decision) :
        Task.FromResult(new Sample(offer.OperationId,offer.Phase,offer.ScheduledAtNs,
            decision,null,null,null,"MISSED_OFFER_INFLIGHT_LIMIT",null,0,null)));
}
var samples = await Task.WhenAll(pending);
clock.Stop();
process.Refresh();
Console.WriteLine(JsonSerializer.Serialize(new {
    schemaVersion=1, experiment="E2_B05_DISPATCH_DIAGNOSTIC_V1",
    capacityEvidence=false, route="direct", maximumInflight=maximum, npgsqlMaximumPoolSize=32,
    independentExternalProcessId=Environment.ProcessId, hostIdentity=Environment.MachineName,
    offered=samples.Length, dispatched=samples.Count(s=>s.DispatchedAtNs.HasValue),
    missed=samples.Count(s=>s.ClientOutcome=="MISSED_OFFER_INFLIGHT_LIMIT"),
    ambiguous=samples.Count(s=>s.ClientOutcome=="AMBIGUOUS_EXCEPTION"),
    acknowledgedCommitted=samples.Count(s=>s.ClientOutcome=="ACKNOWLEDGED"&&s.LedgerStatus=="COMMITTED"),
    clockOriginUtcBefore=utcBefore.ToString("O"),clockOriginUtcAfter=utcAfter.ToString("O"),
    runWallClockNs=Ns(clock),cpuMilliseconds=process.TotalProcessorTime.TotalMilliseconds-cpuBefore,
    peakWorkingSetBytes=process.PeakWorkingSet64,
    gcCollections=Enumerable.Range(0,3).Select(i=>GC.CollectionCount(i)-gcBefore[i]).ToArray(),
    samples, slotEvents=trace,
    limitations="Instrumented direct-only admission diagnostic on one physical host. No pool-wait attribution, saturation ceiling, Orleans comparison, production p99 or MIPS equivalence."
},options));

public sealed record Offer(string OperationId,string Phase,long ScheduledAtNs,
    int SourceAccountId,int TargetAccountId,long AmountCents,string Fault)
{
    public TransferCommand Command()=>new(OperationId,SourceAccountId,TargetAccountId,AmountCents,Fault);
}
public sealed record Vector(string Status,bool CapacityEvidence,int AccountCount,
    int OfferedRatePerSecond,int TotalOfferedRequests,List<Offer> Operations);
public sealed record Sample(string OperationId,string Phase,long ScheduledAtNs,long DecisionAtNs,
    long? DispatchedAtNs,long? CompletedAtNs,long? SlotReleasedAtNs,
    string ClientOutcome,string? LedgerStatus,int Retries,string? ErrorType);
public sealed record SlotEvent(long Sequence,int OfferIndex,string Kind,long AtNs,int ActiveSlots);
