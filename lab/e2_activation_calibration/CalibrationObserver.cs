using System.Diagnostics;
using System.Text.Json;
using E2.OrleansLab;
using Orleans;

// Records invocation envelopes, not SQL transaction or activation lifetimes.
// The diagnostic grain adds a barrier; this filter only records its envelope.
public sealed class CalibrationObserver : IIncomingGrainCallFilter
{
    private static readonly object Gate = new();
    private static readonly string Session = Guid.NewGuid().ToString("N");
    private static readonly string Boot = File.ReadAllText("/proc/sys/kernel/random/boot_id").Trim();
    private static readonly string TimeNamespace = new FileInfo("/proc/self/ns/time").LinkTarget
        ?? throw new InvalidOperationException("Linux time namespace identity is required");
    private static long sequence;

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
        if (context.Grain is not CalibrationGrain || context.MethodName != nameof(ICalibrationGrain.Transfer))
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
