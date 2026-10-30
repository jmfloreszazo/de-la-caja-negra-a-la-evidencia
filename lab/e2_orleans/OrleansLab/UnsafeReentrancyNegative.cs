using Orleans;
using Orleans.Concurrency;

namespace E2.OrleansLab;

// DISPOSABLE NEGATIVE CONTROL ONLY: deliberately unsafe reentrant actor-local
// state. Never use this interface/grain for transfers or authoritative money.
public interface IUnsafeReentrantCounterGrain : IGrainWithIntegerKey
{
    Task<int> UnsafeIncrementWithStaleRead(int expectedParallelCalls);
    Task<int> GetUnsafeValue();
}

[Reentrant]
public sealed class UnsafeReentrantCounterGrain : Grain, IUnsafeReentrantCounterGrain
{
    private int _unsafeValue;
    private int _arrivals;

    public async Task<int> UnsafeIncrementWithStaleRead(int expectedParallelCalls)
    {
        if (expectedParallelCalls != 16)
            throw new ArgumentException("Only the isolated 16-request fixture is allowed");

        // The deliberately stale snapshot is read before the first await.
        var staleValue = _unsafeValue;
        ++_arrivals;
        var wait = System.Diagnostics.Stopwatch.StartNew();
        while (_arrivals < expectedParallelCalls && wait.Elapsed < TimeSpan.FromSeconds(10))
            await Task.Delay(10);

        if (_arrivals != expectedParallelCalls)
            throw new InvalidOperationException("Reentrant test barrier not reached");

        // Reentrancy allows 16 requests to resume with the same stale value.
        // The visible loss is the intentionally failing behavior under test.
        _unsafeValue = staleValue + 1;
        return _unsafeValue;
    }

    public Task<int> GetUnsafeValue() => Task.FromResult(_unsafeValue);
}
