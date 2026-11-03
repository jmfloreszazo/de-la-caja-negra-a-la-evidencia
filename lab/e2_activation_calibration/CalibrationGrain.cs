using E2.OrleansLab;
using Orleans;
using Orleans.Concurrency;

public interface ICalibrationGrain : IGrainWithIntegerKey
{
    Task<TransferResult> Transfer(TransferCommand command);
}

// Deliberate observer calibration: multiple workers are allowed by design.
// This is NOT the accepted AccountGrain and never establishes split brain.
[StatelessWorker(maxLocalWorkers: 2)]
public sealed class CalibrationGrain(IDurableLedger ledger) : Grain, ICalibrationGrain
{
    private static int arrivals;
    private static readonly TaskCompletionSource<bool> Entered =
        new(TaskCreationOptions.RunContinuationsAsynchronously);
    public static Task FirstEntry => Entered.Task;
    private static readonly TaskCompletionSource<bool> Both =
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    public async Task<TransferResult> Transfer(TransferCommand command)
    {
        if (Environment.GetEnvironmentVariable("E2_CALIBRATION_TEST") != "1" ||
            this.GetPrimaryKeyLong() != 1 || command.OperationId != "e2-observer-calibration" ||
            command.SourceAccountId != 1 || command.TargetAccountId != 2 ||
            command.AmountCents is not (31 or 37) || command.Fault != "none")
            throw new InvalidOperationException("Only the exact calibration command is permitted");
        Entered.TrySetResult(true);
        if (Interlocked.Increment(ref arrivals) == 2)
            Both.TrySetResult(true);
        // The first request remains busy until a second activation enters.
        // One request must time out before any ledger call is made.
        await Both.Task.WaitAsync(TimeSpan.FromSeconds(5));
        return await ledger.Transfer(command);
    }
}
