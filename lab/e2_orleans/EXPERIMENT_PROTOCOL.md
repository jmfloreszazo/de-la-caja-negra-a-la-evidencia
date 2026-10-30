# E2 · Orleans coordination over an authoritative durable ledger

**Status: partially verified on an unmerged branch, NOT an accepted E2 experiment.** The original single-silo functional, fixed-seed 1,000-account workload and genuine local-cohost SIGKILL slices passed CI independently. Multi-silo failover, cross-grain circular-call negative controls, sustained capacity characterization and real mainframe equivalence remain untested. This is an English-only engineering
protocol for [issue #8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8).
It must not be promoted to executed evidence merely because the
architecture, examples or build manifests exist.

## Purpose and falsifiable hypothesis

Question: can virtual account actors reduce coordination overhead or
make hot-account saturation easier to diagnose **without compromising**
the independent E1 ledger invariants?

- **H0:** Orleans adds no sustained committed-transfer throughput benefit
  under the exact same business commands, persisted SQL transaction,
  transport and offered-load conditions.
- **H1:** Orleans provides measurable coordination or operational
  advantages in at least one prespecified workload, while preserving
  exactly the same durable outcome and oracle verdicts.
- Report neutral or worse results. A correct negative result is a
  successful experiment, not a reason to change the workload.

The tested package baseline will be **Microsoft.Orleans.Server 10.4.0**
and its matching first-party 10.4.0 package family, with .NET 10.
Pin exact package versions and restore-lock hashes before executing.
The original E1b PostgreSQL 16 ledger remains the system of record.

## Required architecture

```text
Client / workload generator (operation ID, source, destination, amount)
     |
     +-- baseline path --> Same durable transfer service --> PostgreSQL
     |
     +-- E2 path -------> Orleans AccountGrain(source account)
                              |
                              +--> Same durable transfer service --> PostgreSQL
                                                            |
                                                            +--> operation row
                                                            +--> debit and credit
                                                            +--> two postings
                                                            +--> outbox event
                                                            +--> COMMIT
     |
Independent read-only SQL oracle --> accounts + operations + postings + outbox
```

**Critical safety rule:** an account grain is a coordination/placement
boundary, **not** a distributed transaction or durable account balance.
Never independently debit two grains and then imply a cross-grain ACID
commit. The single PostgreSQL transaction owns debit, credit, operation
identity, double postings and outbox together.

Keep grain methods **non-reentrant** for the accepted baseline. Grains
are single-threaded **within an activation**, not globally distributed
database locks and not proof of per-account integrity through failover,
duplicate activations or direct writes outside the silo. Do not hold
cross-grain blocking calls while waiting for a reciprocal grain. In
particular, avoid A->B->A cycles. Database uniqueness, conditional
debit, row ordering and retryable full-transaction failures are final
safety controls. A separate negative-control variant must deliberately
show that a local actor-only balance and/or unsafe reentrancy does **not**
provide the ledger invariant.

### Contract

```csharp
public sealed record TransferCommand(
    string OperationId, int SourceAccountId, int TargetAccountId, long AmountCents);

public sealed record TransferOutcome(
    string Status, int RetryCount, string? FailureCode);
```

Both paths accept the same command IDs, account IDs, amounts and fault
schedules. The grain may invoke the same durable E1b transfer service
once, then return its authoritative persisted outcome. It must not
manufacture or cache an independent success. Ambiguous acknowledgments
must be resolved by the persisted operation-ID lookup; retries are
idempotent.

Do not let the grain and durable-ledger baseline use different SQL
isolation, pool size, max retries, outbox semantics or driver configuration
in a performance comparison.

## Required experiments and gates

| ID | Experiment | Exit condition |
| --- | --- | --- |
| E2-F01 | Protected 16-account E1 sequential reference suite | Same statuses and all four persisted tables; 7/7 independent oracle verdicts |
| E2-F02 | Parallel duplicate IDs and two-source overdraft race | One durable effect per operation ID, no negative balances |
| E2-F03 | Lost response after commit; replay and competing retries | Exactly once **durable business effect** via operation-ID idempotency (not exactly-once message delivery) |
| E2-F04 | Opposite-account transfers and database deadlock | Crossed transfer parity **CI-verified**; a separate opt-in PostgreSQL 40P01 deadlock + full-transaction retry test is **CI-verified in run #41072089559**. Safe ordered locks remain the default |
| E2-F05 | Crash a grain/silo before SQL commit; restart | No partial SQL state; retry succeeds or remains a recorded failure |
| E2-F06 | Crash a grain/silo after SQL commit, before response | Recovered persisted COMMITTED outcome; no duplicate debit/posting/outbox |
| E2-N01 | Unsafe two-grain independent debit/credit, isolated disposable fixture | Independent oracle **rejects** non-atomic split; candidate must never use this design |
| E2-N02 | Deliberately reentrant state change or circular grain call in isolated negative control | Deliberate reentrant actor-local lost-update fixture **CI-verified in run #41060526872** (16 calls, 15 lost updates, no ledger writes). Cross-grain circular calls/deadlock remain untested; accepted AccountGrain stays non-reentrant |
| E2-B01 | Uniform workload on 16 E1 accounts | Same commands, arrival pattern, TLS/security, database, Npgsql pool and offered load across baseline and Orleans |
| E2-B02 | 5% hot accounts | Seed 1,000 distinct **synthetic** accounts and select exactly 50 hot accounts; report the precise skew and seed |
| E2-B03 | One account receives 50% of request intents | Prespecified seed and distribution; report hot-key queueing, rejection and correctly committed work |
| E2-B04 | 1/2/4/8/16 silo or service-node scenarios | Only classify as distributed scaling when workers actually run on separate nodes, not more processes on one runner |
| E2-O01 | Independent SQL accounting oracle after **each** case | 7/7 invariants plus deliberate corrupted-posting rejection, source-independent implementation |
| E2-R01 | CI and immutable provenance | Raw results, SHA, image/package digests, versions, workload seed, negative controls, original run and environment |

**Important workload distinction:** the 16-account reference fixture
cannot represent exactly 5% hot accounts; 5% of 16 is 0.8. Do not round
and call it 5%. Use a separate 1,000-account benchmark fixture with
exactly 50 hot accounts, keeping the 16-account E1 reference contract
separate. Use fixed operation lists so both paths see the same attempted
operations; count rejected transfers and idempotent replays separately
from durable committed transfers.

## Load and reporting rules

- For functional parity, replay the same event list, fault schedule and
  database seed; compare persisted balances, operation identity,
  postings and outbox **after every case**.
- For performance, maintain a reusable client/transport for *both* paths.
  Do not compare a long-lived Orleans silo to a per-transfer CLI launch.
  Use offered-load/open-loop pacing, connection reuse and coordinated-
  omission handling; record warm-up, run duration, sample size and
  clock boundaries.
- Record attempted/s, **durably committed transfers/s**, p50/p95/p99,
  timeouts, per-account queue delay, SQL deadlock and retry counts,
  CPU/memory, GC, client and SQL connection pool occupancy and
  retransmission outcomes. Do not equate actor messages/s with banking TPS.
- Report per-account hot-key saturation and whether it moves bottlenecks
  from SQL lock contention to a grain queue. Keep raw timestamps and
  observations, not just a summary percentage.
- Compare two groups separately: one-silo local smoke, and separately
  instrumented physical-node trials. Neither is a mainframe MIPS result.
- Use the **same independent seven-invariant SQL oracle** as E1 on
  each case and a negative corrupted-ledger fixture independent of the
  candidate grain code.

## Real PostgreSQL deadlock and whole-transaction retry fixture

A deliberately unsafe **test-only** first attempt acquires the source
account's PostgreSQL row lock, synchronizes two opposing transactions
and then requests the other account's row. A real PostgreSQL deadlock
detector must abort one transaction with `40P01`. The failed operation
must retry its **entire** SQL transaction using the normal ordered
locking path, preserving the authoritative ledger.

Only `E2_ENABLE_DEADLOCK_FIXTURE=1`, two exact synthetic IDs,
account pairs 1→2 / 2→1 and amount 41 cents can activate the
unsafe path; the fixture rejects commands otherwise.

```bash
python3 lab/e2_orleans/test_deadlock.py
```

The gate requires one real `40P01` victim per route, both transfers
committed, exactly two operations/four postings/two outbox events,
idempotent stable-ID replay, payload-conflict rejection, matching
four-table SHA across routes and seven independent SQL invariants.
**The fixture passed [original CI #41072089559](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41072089559)** with the [archived observation](../../evidence/runs/e2-orleans-deadlock.json) and [raw original artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41072089559/artifacts/12985901039). It is not evidence of a natural deadlock rate, multi-silo failover or mainframe capacity.

## Failure and cancellation semantics

Do not promise exactly-once delivery. Treat a client timeout or silo loss
as an **ambiguous outcome** and resolve by stable operation ID in the
authoritative ledger. Repeated command IDs with different payloads must
be rejected. An Orleans grain's in-memory state is disposable, caches are
invalidated on recovery and silo restart must not reconstruct balances
by guessing. No two-phase distributed commit across grains is used in
the accepted implementation.

## Evidence, safety and acceptance

The laboratory should be runnable under Podman using generated synthetic
data only. No production secrets, customer identifiers or mainframe data.
Never mutate the protected E1/COBOL/SQLite reference or overwrite prior
E1a/E1b/E1c evidence. A failure in this experiment must stay red and its
cause must be recorded rather than changing test expectations silently.

**The umbrella E2 claim is `partially_verified` in `evidence/claims.json`; it is NOT an overall PASS.** Individually archived E2-SMOKE, E2-LOAD and E2-PROCESS-KILL records point to original CI runs, and the original artifacts must remain reviewable. The 32-command crossed-transfer regression for both routes passed [CI #41059475191](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41059475191) with independent SQL oracles and matching snapshots; this does NOT demonstrate a deliberately induced deadlock, actor reentrancy or real distributed Orleans failover. The outstanding capacity, reentrancy and multi-node gates need separate original CI evidence and independent review.

### References

- [Microsoft Orleans request scheduling](https://learn.microsoft.com/dotnet/orleans/grains/request-scheduling)
- [Microsoft Orleans migration guidance](https://learn.microsoft.com/dotnet/orleans/migration-guide)
- [Microsoft.Orleans.Server 10.4.0](https://www.nuget.org/packages/Microsoft.Orleans.Server/10.4.0)
- [E1 experiment protocol](../docs/EXPERIMENT_PROTOCOL.md)
- [E1b PostgreSQL ledger](../e1_pg/README.md)
- [E2 tracking issue](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8)
