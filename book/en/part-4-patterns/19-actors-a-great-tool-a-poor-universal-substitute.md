**English** · [Español](../../es/parte-4-patrones/19-actores-una-gran-herramienta-un-mal-sustituto-universal.md)

[← Chapter 18 · Distributing without breaking the books](18-distributing-without-breaking-the-books.md) · [Contents](../README.md) · [Chapter 20 · Batch and parallelism: speeding up without changing the result →](20-batch-and-parallelism-speeding-up-without-changing-the.md)

# Chapter 19 · Actors: a great tool, a poor universal substitute

> [!IMPORTANT]
> **Chapter thesis.** The actor pattern fits very well for coordinating entities with identity —accounts, policies, case files— and parallelizing across them. It does not replace the ledger, it does not make a transfer between two actors atomic and it does not speed up a hot account.

## When they fit

Actors are useful when we have many entities with identity, state and behaviour, and when a large part of their operations can be resolved locally. A policy, a loan or a case file can fit. So can an account, if we define precisely which operations affect only that account and which need a coordinator.

The unit I would migrate is a business capability. I would not automatically turn every COBOL program, paragraph or record into an actor. A legacy technical call may mix several responsibilities; distributing it without discovering them turns memory coupling into network coupling.

At first I would keep an interface that allows comparing legacy and new implementation. For example, a policy actor can coordinate requests and still call a COBOL routine to calculate a premium. When a new implementation passes the corresponding contract, we can change the calculation while keeping the identity and control of the process.

The actor pattern fits especially well when we can identify an entity with stable identity —account, policy, contract— and want to coordinate its operations without blocking every entity at once. An actor receives messages and evolves its state; millions of different identities can spread their work across nodes. Dapr Actors [26] and Microsoft Orleans [24] offer virtual actor implementations. On .NET 10, Orleans deserves first evaluation when the solution is fundamentally C#; Dapr can be interesting if the environment is polyglot or combines other building blocks.

The temptation is to create an `AccountActor` and consider banking solved. It is not so. The unit of isolation is the actor, not necessarily the whole of a transaction involving two accounts. Nor can we confuse an in-memory activation with a durable accounting record. Orleans has an optional model of ACID transactions over persisted state under specific conditions and providers [25]; that does not mean every write to an external database or every message is automatically included.

I would separate at least three responsibilities: an **actor or coordinator per identity** to limit conflicts and simplify sequential logic; an **accounting service** with a proven ACID boundary for movements; and **projections** for queries and analytics. The source of truth for money must be clearly defined, preferably in an auditable ledger. If the actor uses a cached copy of the balance, it must invalidate or reconcile it after the commit.

![Figure 19.1 · Actors per account: parallelism across identities, order within each one. Durability and atomicity are guaranteed by the ledger.](../../figures/en/actors.png)

*Figure 19.1 · Actors per account: parallelism across identities, order within each one. Durability and atomicity are guaranteed by the ledger.*

## What the runtime provides and what remains open

By default, Orleans runs a grain activation with complete requests without interleaving them. Its documentation explains that enabling reentrancy allows turns to interleave and requires reasoning about state across `await` points [24]. It also shows that cyclic calls can cause waits that end in a timeout. So the actor model removes part of the concurrency problem; it does not remove every lock.

Orleans provides ACID transactions over grains' transactional state and requires specific participants and storage to be configured [25]. That guarantee does not, by declaration, cover any SQL write or broker call made in the middle of the method. The set of participants in a transaction must be identified.

Dapr provides virtual actors with identity, state and turn-based execution [26]. Persistence and the guarantees of the operation depend on its configuration and the API used. For a transfer between actors I would not assume an implicit global ACID transaction: I would have to design and test the mechanism that implements it.

The actor model has a physical limitation: a hot account. If a single corporate customer concentrates hundreds of thousands of operations, serializing them all in one actor can become the system's bottleneck. The options are to study the order really required, split sub-accounts or partitions when the domain allows it, batch operations or move control to a transactional database. **I would not fragment a financial invariant just to improve the benchmark**.

A common mistake is to declare an actor reentrant to gain parallelism without analysing state across `await`. Orleans processes a grain's requests non-reentrantly by default; reentrancy allows interleaving and changes the conditions for reasoning [24]. Tests must include precisely that interleaving.

## An actor that orders and a ledger that decides

This is how I would approach it in Orleans: the grain serializes its account's requests and delegates the decision to a local ledger transaction. The grain does not keep the balance as its source of truth.

**Listing 19.1 · Orleans: the actor coordinates, the ledger commits** — *Illustrative*

```csharp
public interface IAccountGrain : IGrainWithStringKey
{
    Task<DebitDecision> DebitAsync(DebitCommand command);
}

// No [Reentrant]: each request finishes before the next one starts.
public sealed class AccountGrain(ILedger ledger) : Grain, IAccountGrain
{
    public Task<DebitDecision> DebitAsync(DebitCommand command) =>
        // The actor provides order; the ledger provides decision and durability.
        ledger.DebitAsync(this.GetPrimaryKeyString(),
                          command.OperationId, command.Amount);
}

[GenerateSerializer]
public sealed record DebitCommand([property: Id(0)] Guid OperationId,
                                  [property: Id(1)] decimal Amount);

[GenerateSerializer]
public sealed record DebitDecision([property: Id(0)] Guid OperationId,
                                   [property: Id(1)] string Status);
```

What this fragment avoids is as important as what it does. It does not call from account A's actor to account B's actor to "complete" the transfer: two transfers crossing in opposite directions, with non-reentrant actors, can wait for each other until the timeout, as Orleans' own documentation warns [24]. The transfer that crosses two accounts goes through the accounting boundary.

![Figure 19.2 · What to avoid: two crossing transfers between non-reentrant actors wait for each other until the timeout.](../../figures/en/actor_cycle.png)

*Figure 19.2 · What to avoid: two crossing transfers between non-reentrant actors wait for each other until the timeout.*

## The transfer that crosses two actors

I would consider three options. A SQL boundary keeps debit and credit in a local transaction and the actors coordinate access. An Orleans transaction uses its transactional state for the participants it covers. A reservation or saga protocol explicitly represents steps and intermediate states accepted by the business.

The first can simplify reconciliation and leverage an engine we already know. The second integrates coordination into the grain model and requires evaluating storage, conflicts and recovery. The third can fit heterogeneous participants, at the cost of different semantics we must not hide.

| Situation | Possible role of actors | Essential check |
|---|---|---|
| Changes to a policy | Serialize by identity | Idempotency and persistence |
| Independent batch calculation | Coordinate partitions or use workers | Cost compared with batch processing |
| Transfer between accounts | Coordinate participants | Atomicity or accepted protocol |
| Aggregate query over millions of entities | Feed a projection | Freshness and reconciliation of the read |
| One entity concentrates almost all load | Keep local order | Per-key ceiling and queues |
| Gradual migration | Stable facade over legacy and target | One write authority per phase |

## Actors versus partitions

The difference is not aesthetic. If work can be grouped by account but each operation is a short command, an actor provides a natural unit of coordination. If we must close interest on ten million accounts within a given window, individual actors could add unnecessary overhead. There, a partitioned batch that loads blocks, calculates in memory and commits checkpoints may perform better. A modern architecture must not replace one effective specialization with another equally rigid one.

## How to demonstrate their usefulness

I would compare a simple database solution, an actor-based solution and the observed legacy load. I would keep the same rules, data and commit guarantees. I would measure throughput, p99, number of conflicts, consumption, recovery and operating cost.

I would add activation failures, duplicate messages, lost responses and the loss of a node. I would also test that an external call returning late does not apply a stale change. The test must observe the persisted state and the history, as well as the actor's response.

The banking lab uses local SQL transactions and now includes a real Orleans silo co-hosted in a single .NET 10 process. It does not yet include a multi-node Orleans cluster or a Dapr comparison; the measured boundary is a synthetic accounting contract on one hosted runner.

### E2: from architectural reasoning to evidence

The [E2 laboratory](../../../lab/e2_orleans/README.md) uses the exact same authoritative PostgreSQL transaction for the direct and grain-routed paths. The [original functional run](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41053628769) passed 15 cases per path, including idempotency, concurrent overdraft and seven independent accounting invariants. A separate [synthetic workload run](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41055928136) committed 600 transfers over six cases involving 1,000 accounts: uniform traffic, exactly 50 hot accounts out of 1,000 (5%), and one account receiving 50% of intent. The persisted account, operation, posting and outbox states matched between both paths.

In the [abrupt process termination experiment](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41056976342), the real co-hosted process was killed with `SIGKILL` before and after PostgreSQL commit, through both the direct and Orleans paths. The pre-commit death left no operation; the post-commit death retained exactly one operation, two postings and an outbox event, and replay was idempotent. An intentionally partial SQL mutation was also rejected by the independent oracle. Multi-silo reassignment and physical node failure were not tested.

The experiment does not prove Orleans increases throughput. In fact, its p95 exceeded the direct path in all three small 100-request profiles. One local run is insufficient evidence for sustained throughput, production p99 or mainframe MIPS equivalence. An actor-based design must justify its operational value with actual workload, failure and cost data, not the assumption that per-account sequencing automatically provides scale.

> **I would not fragment a financial invariant just to improve the benchmark.**

---

[← Chapter 18 · Distributing without breaking the books](18-distributing-without-breaking-the-books.md) · [Contents](../README.md) · [Chapter 20 · Batch and parallelism: speeding up without changing the result →](20-batch-and-parallelism-speeding-up-without-changing-the.md)
