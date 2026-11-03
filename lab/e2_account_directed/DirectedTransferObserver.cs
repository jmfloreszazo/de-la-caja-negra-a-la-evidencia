using System.Diagnostics;
using System.Text.Json;
using E2.OrleansLab;
using Orleans;

// Records invocation envelopes, not SQL transaction or activation lifetimes.
// This separate test filter deliberately delays one pre-invoke request.
// The accepted AccountGrain and SQL transaction remain unchanged.
public sealed class DirectedTransferObserver : IIncomingGrainCallFilter
{
    private static readonly object Gate = new();
    private static readonly string Session = Guid.NewGuid().ToString("N");
    private static readonly string Boot = File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim();
    private static readonly string TimeNamespace = new FileInfo("/proc/self/ns/time").LinkTarget
        ?? throw new InvalidOperationException("Linux time namespace identity is required");
    private static long sequence;
    private static int gateClaimed;

    public static void Ready()
    {
        Console.WriteLine("E2_TRANSFER_OBSERVER_READY:" + JsonSerializer.Serialize(new
        {
            schemaVersion = 1, session = Session, node = Environment.MachineName,
            pid = Environment.ProcessId, bootId = Boot, timeNamespace = TimeNamespace,
            frequency = Stopwatch.Frequency
        }));
        Console.Out.Flush();
    }

    public async Task Invoke(IIncomingGrainCallContext context)
    {
        if (context.Grain is not AccountGrain || context.MethodName != nameof(IAccountGrain.Transfer))
        {
            await context.Invoke();
            return;
        }
        var command = context.Request.GetArgument(0) as TransferCommand
            ?? throw new InvalidOperationException("Missing observed TransferCommand");
        var call = Guid.NewGuid().ToString("N");
        var activation = context.TargetContext.ActivationId.ToString();
        var grain = context.TargetId.ToString();
        void Record(string kind, string? result, string? exception)
        {
            lock (Gate)
            {
                Console.WriteLine("E2_TRANSFER_OBSERVER:" + JsonSerializer.Serialize(new
                {
                    schemaVersion = 1, session = Session, sequence = ++sequence,
                    node = Environment.MachineName, pid = Environment.ProcessId,
                    bootId = Boot, timeNamespace = TimeNamespace,
                    frequency = Stopwatch.Frequency, tick = Stopwatch.GetTimestamp(),
                    utc = DateTimeOffset.UtcNow, kind, callId = call,
                    activationId = activation, grainId = grain,
                    operationId = command.OperationId, source = command.SourceAccountId,
                    target = command.TargetAccountId, amount = command.AmountCents,
                    result, exception
                }));
                Console.Out.Flush();
            }
        }
        Record("BEGIN", null, null);
        try
        {
            if (Environment.GetEnvironmentVariable("E2_ACCOUNT_DIRECTED_TEST") == "1" &&
                Environment.MachineName == "e2f10-secondary" &&
                command.OperationId == "c05-contested-id" && command.SourceAccountId == 2 &&
                command.TargetAccountId == 1 && command.AmountCents == 31 &&
                Interlocked.CompareExchange(ref gateClaimed, 1, 0) == 0 &&
                !File.Exists("/probe/release-secondary"))
            {
                if (!Directory.Exists("/probe"))
                    throw new InvalidOperationException("Missing disposable directed-gate volume");
                var identity = new { session = Session, node = Environment.MachineName,
                    pid = Environment.ProcessId, callId = call, activationId = activation,
                    grainId = grain, tick = Stopwatch.GetTimestamp() };
                Console.WriteLine("E2_ACCOUNT_GATE_WAIT:" + JsonSerializer.Serialize(identity));
                Console.Out.Flush();
                var wait = Stopwatch.StartNew();
                while (!File.Exists("/probe/release-secondary"))
                {
                    if (wait.Elapsed > TimeSpan.FromSeconds(170))
                        throw new TimeoutException("Directed pre-invoke gate deadline");
                    await Task.Delay(50);
                }
                Console.WriteLine("E2_ACCOUNT_GATE_RELEASE:" + JsonSerializer.Serialize(new {
                    session = Session, callId = call, activationId = activation, grainId = grain,
                    node = Environment.MachineName, pid = Environment.ProcessId,
                    tick = Stopwatch.GetTimestamp() }));
                Console.Out.Flush();
            }
            await context.Invoke();
            Record("END", (context.Result as TransferResult)?.Status, null);
        }
        catch (Exception error)
        {
            Record("ERROR", null, error.GetType().FullName);
            throw;
        }
    }
}
