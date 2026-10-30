using Orleans;

namespace E2.OrleansLab;

// Orleans serialization metadata applies only to messages, not database state.
// The PostgreSQL ledger is the authoritative source of account balances.
[GenerateSerializer]
public sealed record TransferCommand(
    [property: Id(0)] string OperationId,
    [property: Id(1)] int SourceAccountId,
    [property: Id(2)] int TargetAccountId,
    [property: Id(3)] long AmountCents,
    [property: Id(4)] string Fault = "none",
    [property: Id(5)] int ArrivalOffsetMs = 0);

[GenerateSerializer]
public sealed record TransferResult(
    [property: Id(0)] string Status,
    [property: Id(1)] int Retries,
    [property: Id(2)] string[] RetrySqlStates,
    [property: Id(3)] string HandledBy);

public interface IAccountGrain : IGrainWithIntegerKey
{
    Task<TransferResult> Transfer(TransferCommand command);
}

public interface IDurableLedger
{
    Task<TransferResult> Transfer(TransferCommand command);
}

public sealed class AccountGrain(IDurableLedger ledger) : Grain, IAccountGrain
{
    // No [Reentrant] attribute. This activation queues its requests.
    // Cross-account atomicity is entirely the responsibility of PostgreSQL.
    public async Task<TransferResult> Transfer(TransferCommand command)
    {
        if (command.SourceAccountId != this.GetPrimaryKeyLong())
            throw new ArgumentException("Grain key must equal the source account");

        var committedOutcome = await ledger.Transfer(command);
        return committedOutcome with { HandledBy = $"grain-{this.GetPrimaryKeyLong()}" };
    }
}
