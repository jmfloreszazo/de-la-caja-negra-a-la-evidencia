**English** · [Español](../../es/parte-4-patrones/17-de-los-locks-del-mainframe-al-control-explicito-de.md)

[← Chapter 16 · Data ownership](16-data-ownership.md) · [Contents](../README.md) · [Chapter 18 · Distributing without breaking the books →](18-distributing-without-breaking-the-books.md)

# Chapter 17 · From mainframe locks to explicit concurrency control

> [!IMPORTANT]
> **Chapter thesis.** Locks, isolation and the unit of work are not properties of COBOL: the environment provides them, and they do not travel with a translation. We must state the invariant, choose the mechanism that protects it and prove it with concurrent histories.

This chapter should be open next to the code, not only in an architecture meeting. The user sees a withdrawal approved or declined. The engineer has to know what happens when two withdrawals arrive at the same time, when the process dies just before the commit or when a client retries because it lost the response.

In Db2 for z/OS, the UR, CS, RS and RR levels offer different isolation and contention trade-offs [37]. In CICS, the concept of a unit of work organizes which recoverable resources are committed together [16]. They are not intrinsic properties of COBOL and they do not travel automatically when converting it to C#. That is why, before choosing the technology, I state the invariant: "no withdrawal is committed that leaves the account below the permitted balance", "an operation identifier produces only one posting", "the total of debits and credits in a transfer is preserved".

## From the COBOL statement to the unit of work

COBOL expresses logic and representations. The transactional guarantees an application experiences may come from CICS, Db2, IMS, recoverable VSAM, resource managers and their configurations. IBM describes units of work and syncpoints that allow committing or backing out changes to recoverable resources [16]. The migration must discover where that unit begins and ends and who coordinates its recovery.

If I translate the statements and replace each access with an independent remote call, I may lose a guarantee that was previously implicit in the environment. The new program will return similar results in the normal examples and fail the moment an intermediate operation does not finish.

Take a transfer. The debit, the credit, the postings and the operation identity must belong to a coherent boundary. If the operation must be atomic, the system cannot leave a confirmed debit without its matching credit. If the design allows intermediate states, we must represent them and restrict how they affect the available balance.

The first artifact I would ask the team for is the transactional map, in addition to the call map. It must show the participating resources, order, isolation, commit, rollback, timeouts, restart points and behaviour when the response is lost.

## Four mechanisms and what they do not guarantee

**Pessimistic locking** is an option when the probability of conflict is high and we must prevent concurrent updates before executing. **Optimistic concurrency** uses a version and rejects writes over a state that has changed. **Serializable** protects certain composite invariants at the cost of more contention, aborts or retries; its concrete guarantees depend on the engine. **Distributed locks** can coordinate external work, but they do not by themselves replace a database transaction: with expirations, partitions or pauses we need *fencing tokens* to stop an old owner from continuing to write. **Actors** normally serialize execution per identity, but that in-memory serialization is not a durable commit.

For an accounting transfer within a single relational database I would initially choose a short transaction that includes: validation, idempotent registration, debit and credit postings, update of derived balances if applicable and the outbox. If the accounts live in different banks or ledgers, we must recognize another boundary and use a clearing house, a coordinator or another suitable business protocol. I would not introduce a saga to pretend an interbank transfer is already atomic.

![Figure 17.1 · The transfer as a local unit of work: idempotency, conditional debit, credit, postings and outbox are committed together or nothing is committed.](../../figures/en/transfer_seq.png)

*Figure 17.1 · The transfer as a local unit of work: idempotency, conditional debit, credit, postings and outbox are committed together or nothing is committed.*

## A lock is not a deadlock

A lock makes an operation wait because another holds an incompatible resource. It can be the right mechanism to protect a rule. A deadlock appears when dependencies form a cycle that prevents progress.

Imagine a transfer from A to B locks A first and another from B to A locks B first. If both then wait for the other account, we have the cycle. Accessing accounts in a consistent global order reduces this cause of deadlock. It does not eliminate every possible cycle in an engine: indexes, keys and other resources also take part.

![Figure 17.2 · A deadlock and its way out: a victim, a complete retry with the same identity and a global order so the cycle never forms.](../../figures/en/deadlock_seq.png)

*Figure 17.2 · A deadlock and its way out: a victim, a complete retry with the same identity and a global order so the cycle never forms.*

PostgreSQL documents deadlock detection and recommends a consistent order when acquiring several locks [17]. The protocol must expect the engine to abort a victim. The application decides whether it can repeat the whole operation, with the same identity and a limited budget. Retrying indefinitely turns a conflict into a storm.

A timeout has an additional ambiguity: perhaps the commit happened and the response was lost. Retrying with a new identity may duplicate the effect. That is why business idempotency must allow querying the result and distinguishing a resend from a different request that reuses the same key.

In the concurrency lab we will distinguish **safety** (never violating an invariant), **liveness** (finishing without blocking indefinitely) and **performance** (progressing at a sufficient rate). They are different properties and all of them must be verified.

## The transfer written for an engine with row locking

The lab uses SQLite, which serializes writes and therefore cannot show a row deadlock. This is how I would write the same operation in SQL Server or Azure SQL, extending the lab sketch `architecture/ledger_transaction.sql`. The decisions are commented in the code itself.

**Listing 17.1 · Transfer in T-SQL: idempotency, global lock order, conditional debit and outbox** — *Illustrative*

```sql
CREATE OR ALTER PROCEDURE dbo.Transfer
    @OperationId uniqueidentifier, @From nvarchar(64), @To nvarchar(64),
    @Amount decimal(19,4)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;               -- any error rolls back the whole transaction
    BEGIN TRANSACTION;

    -- 1. Idempotency: a resend with the same identity sees the previous decision.
    IF EXISTS (SELECT 1 FROM dbo.Operations WITH (UPDLOCK, HOLDLOCK)
               WHERE OperationId = @OperationId)
    BEGIN
        COMMIT;  SELECT 'DUPLICATE' AS Result;  RETURN;
    END;

    -- 2. Global order: always lock the account with the lower key first.
    DECLARE @First nvarchar(64)  = IIF(@From < @To, @From, @To),
            @Second nvarchar(64) = IIF(@From < @To, @To, @From),
            @Touch int;
    SELECT @Touch = 1 FROM dbo.Accounts WITH (UPDLOCK, ROWLOCK) WHERE AccountId = @First;
    SELECT @Touch = 1 FROM dbo.Accounts WITH (UPDLOCK, ROWLOCK) WHERE AccountId = @Second;

    -- 3. The rule is evaluated where it is committed.
    UPDATE dbo.Accounts SET Balance = Balance - @Amount
     WHERE AccountId = @From AND Balance >= @Amount;
    IF @@ROWCOUNT = 0
    BEGIN
        INSERT dbo.Operations (OperationId, OperationType, Status)
        VALUES (@OperationId, 'TRANSFER', 'REJECTED');
        COMMIT;  SELECT 'REJECTED' AS Result;  RETURN;
    END;

    UPDATE dbo.Accounts SET Balance = Balance + @Amount WHERE AccountId = @To;

    -- 4. Operation, double entry and pending event: all or nothing.
    INSERT dbo.Operations (OperationId, OperationType, Status)
    VALUES (@OperationId, 'TRANSFER', 'COMMITTED');
    INSERT dbo.LedgerEntries (OperationId, AccountId, SignedAmount)
    VALUES (@OperationId, @From, -@Amount), (@OperationId, @To, @Amount);
    INSERT dbo.Outbox (OperationId, Payload)
    VALUES (@OperationId, N'{"type":"TransferCommitted"}');

    COMMIT;
    SELECT 'COMMITTED' AS Result;
END;
```

Two nuances. Besides detecting the duplicate, the lab compares the content of the mandate: the same identity with a different amount is a conflict, not a resend. And the global order reduces one cause of deadlock, but not all of them: indexes, lock escalation and other resources can close cycles. That is why the client needs a bounded retry that keeps the identity.

**Listing 17.2 · Retry with a budget and the same identity when chosen as a deadlock victim** — *Illustrative*

```csharp
public async Task<TransferResult> TransferAsync(TransferCommand cmd, CancellationToken ct)
{
    const int maxAttempts = 5;
    for (var attempt = 1; ; attempt++)
    {
        try
        {
            // Same OperationId on every attempt.
            return await _ledger.ExecuteTransferAsync(cmd, ct);
        }
        catch (SqlException ex) when (ex.Number == 1205 && attempt < maxAttempts)
        {
            var backoffMs = Math.Min(200, 10 * (1 << attempt))
                            + Random.Shared.Next(0, 10);
            await Task.Delay(backoffMs, ct);    // jitter; never infinite
        }
    }
}
```

In PostgreSQL the equivalent is triggered by serialization and deadlock failures (SQLSTATE `40001` and `40P01`), and its documentation insists on repeating the whole transaction, not the last statement [18]. When the budget runs out, the service reports the failure and does not invent a result: that is exactly what the lab's `boundedRetries` control checks.

## Choosing isolation with an anomaly in mind

It is not enough to say we use ACID. We must identify which concurrent observations the operation tolerates. Two transactions can read that there is enough balance and make incompatible decisions if their validation and their write are not adequately protected.

A conditional debit executed by the engine, a version check, explicit locks or serializable isolation are possible mechanisms. The choice depends on the set of rows and predicates that sustain the rule. A per-row condition does not guarantee a constraint over a group of accounts.

The PostgreSQL documentation distinguishes snapshot from serializable and requires preparing the complete retry when serialization fails [18]. SQL Server offers its own locking and versioning modes [19]. I would not assume that two options with similar names behave identically in different engines.

When designing I would separate three dimensions: what data an operation can observe, which writes it can commit and what result the client sees. A sequential test does not necessarily reveal a breach of any of them.

## An acceptance sequence

A transfer contract should state what it means to accept, to reject and to not yet know the result. I would define the idempotency key and its scope, the currency, the scale, the handling of insufficient funds and the order of observable states.

Then I would write concurrent histories that could contradict it. Two withdrawals competing for the same available balance. The same mandate sent several times. A crash between the debit and the credit. A commit followed by a lost response. A recovery that repeats an already accepted request.

The oracle must examine the state and the history, not just the global total. Preserving the total amount of money is necessary in our synthetic case, but it allows errors such as charging the wrong account. We also need a correspondence between each operation and its postings and reconciliation of balances with the history.

> **Safety, liveness and performance are different properties. A sequential test proves none of them under concurrency.**

---

[← Chapter 16 · Data ownership](16-data-ownership.md) · [Contents](../README.md) · [Chapter 18 · Distributing without breaking the books →](18-distributing-without-breaking-the-books.md)
