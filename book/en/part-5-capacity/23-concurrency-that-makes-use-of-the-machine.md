**English** · [Español](../../es/parte-5-capacidad/23-concurrencia-que-aprovecha-la-maquina.md)

[← Chapter 22 · MIPS do not fit in a vCPU conversion](22-mips-do-not-fit-in-a-vcpu-conversion.md) · [Contents](../README.md) · [Chapter 24 · The benchmark that counts: load, contention, failure and cost →](24-the-benchmark-that-counts-load-contention-failure-and-cost.md)

# Chapter 23 · Concurrency that makes use of the machine

> [!IMPORTANT]
> **Chapter thesis.** Parallelize what is independent, limit what saturates and do not confuse asynchrony with capacity. The hot account and network round trips set ceilings no hardware removes.

## Async does not add capacity to a saturated resource

In .NET, asynchronous waiting can free threads while a dependency responds. It does not by itself reduce the time a transaction holds a lock, nor does it increase the commits the storage supports.

Opening thousands of tasks against a limited database shifts the waiting to connections, memory and timeouts. I prefer limited, observable admission: how many operations we accept in progress, how long they can wait and what answer we give when the budget is exceeded.

A bounded queue lets us apply pressure on the producer. `Channel` offers a local construct for that [23]. If we need survival across process crashes, the queue needs persistence or a protocol that allows the work to be rebuilt. An in-memory queue is not a durable broker.

It is also worth distinguishing compute parallelism from I/O concurrency. Running each SQL query inside `Task.Run` does not make the engine faster. Blocking threads with `.Result` or `.Wait()` can worsen the service's capacity. The profiler must show where we consume CPU and where we wait.

## Bounded admission in .NET

This is the pattern I would put at the edge of a transfer service: a bounded queue, an explicit answer when it is full and a number of consumers adjusted to what the engine can commit, not to the number of cores.

**Listing 23.1 · Backpressure with a bounded Channel and explicit rejection** — *Illustrative*

```csharp
var queue = Channel.CreateBounded<TransferCommand>(
    new BoundedChannelOptions(capacity: 2_000)
{
    FullMode = BoundedChannelFullMode.Wait,   // pressure on the producer
    SingleReader = false,
    SingleWriter = false
});

// At the HTTP edge: if it does not fit now, say so now.
app.MapPost("/transfers", (TransferCommand cmd) =>
    queue.Writer.TryWrite(cmd)
        ? Results.Accepted($"/transfers/{cmd.OperationId}")
        : Results.StatusCode(StatusCodes.Status429TooManyRequests));

// Consumers limited by the ledger's commit capacity.
for (var i = 0; i < ledgerConcurrency; i++)
{
    _ = Task.Run(async () =>
    {
        await foreach (var cmd in queue.Reader.ReadAllAsync(stoppingToken))
            await ledger.TransferAsync(cmd, stoppingToken);
    });
}
```

![Figure 23.1 · Bounded admission: what does not fit is rejected now, instead of timing out later.](../../figures/en/admission.png)

*Figure 23.1 · Bounded admission: what does not fit is rejected now, instead of timing out later.*

An honest warning: this fragment answers `202 Accepted` over an in-memory queue. If the process crashes, admitted and unconfirmed requests are lost. It is only acceptable if the client resends with the same operation identity —and the ledger deduplicates it— or if the queue is durable. Admitting is not confirming, and the contract must say what each response means.

## The hot account sets a ceiling

Suppose an entity requires four milliseconds of sequential work per operation. Without overlapping that work or changing the contract, its ideal ceiling is close to 250 operations per second. Adding nodes for other entities does not remove that serial section of the same entity.

We can shrink the critical section, move prior calculations out of it or group work when that is semantically valid. We may also find the entity was defined too broadly. What I would not do is split it just to improve the benchmark if that means we stop protecting the rule.

Amdahl's law gives a similar warning about a program: a sequential part limits the improvement obtainable by adding processors. With ten per cent strictly sequential, the ideal speed-up limit is close to ten times even with an enormous number of processors. The real system adds communication and coordination.

## Few calls that do useful work

If an operation makes fifty strictly sequential network round trips of two milliseconds each, it spends around a hundred milliseconds on those trips alone, before adding processing. It is an arithmetic example, not an Azure measurement.

The answer may be to reduce trips, use set operations, revisit the contract or bring application and data closer. The most powerful server does not remove the latency of a dependency we keep querying the same way.

When optimizing I would avoid accumulating the whole set in memory without a limit. Batched reads, streaming, cancellation, memory limits and suitable indexes can contribute more than a bigger machine. Each change must preserve the result and pass the oracles again.

> **Async frees threads. It does not add commits to the storage or shorten the time a transaction holds a lock.**

---

[← Chapter 22 · MIPS do not fit in a vCPU conversion](22-mips-do-not-fit-in-a-vcpu-conversion.md) · [Contents](../README.md) · [Chapter 24 · The benchmark that counts: load, contention, failure and cost →](24-the-benchmark-that-counts-load-contention-failure-and-cost.md)
