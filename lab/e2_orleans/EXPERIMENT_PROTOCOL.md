# E2 · Orleans coordination over an authoritative durable ledger

**Status: partially verified synthetic E2 slices, NOT an accepted overall E2 experiment.** The original single-silo functional, fixed-seed 1,000-account workload and genuine local-cohost SIGKILL slices passed CI independently. Multi-silo failover, cross-grain circular-call negative controls, sustained capacity characterization and real mainframe equivalence remain untested. This is an English-only engineering
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

## E2-F10-C02 · Actual packet-loss partition with the same live silo

**Original Linux tc/netem experiment CI [#41132190043](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41132190043) passed** at source commit `10c5e0cc6d300af0cc23cff448f0214100e1036c` and uploaded the [immutable complete original artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41132190043/artifacts/13013089253) (ZIP SHA-256 `fc58f27ca4f4b0a695c5a21e54553d6292ac6f4d388d867ad3e446045f8c6583`). Its [archived result](../../evidence/runs/e2-orleans-live-network-loss.json) is narrowly `ci_verified`; E2 overall remains `partially_verified` because in-fault business commands, convergence, fencing, sustained capacity and physical HA are not established. A prior
negative-control attempt used `podman network disconnect`; that actual
experiment **stopped the secondary container** (host PID zero and ADO.NET
status Dead 6). Its raw failure record remains in CI
[#41131370049](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41131370049)
([artifact #13012863038](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41131370049/artifacts/13012863038)).
It is **not** accepted as evidence of a network partition with a live silo.

The revised, deliberately opt-in experiment uses four Podman network
namespaces on ONE physical Linux runner and two separate private bridges:
`e2f10-net` (application transport, `10.78.30.0/24`) and
`e2f10-sql` (PostgreSQL/ADO.NET, `10.78.31.0/24`).
A temporary, test-only `nicolaka/netshoot:v0.13` helper joins the
secondary silo's **existing network namespace**, discovers the exact
interface carrying `10.78.30.12`, and executes
`tc qdisc replace dev <interface> root netem loss 100%`.
This drops packets **egressing the application's bridge**, while its SQL
interface and all container memberships remain untouched.

Independent probes must establish: both gateways reachable initially;
with packet loss, external client reaches primary but **not secondary**;
secondary reaches **neither remote primary** (the local self gateway can
still be reachable through loopback); secondary still connects to
PostgreSQL and is the **same running OS process** and container ID.
No financial commands are sent while packet loss is active. The test
then removes the exact qdisc and requires complete restored TCP
reachability, unchanged process/container/network identity, unchanged
durable posting/outbox cardinality, 7/7 independent Oracle Gates and
unaltered SQL access. Original CI artifacts retain qdisc state,
network identities, ADO.NET membership observations and source hashes.
On failure they retain pre-teardown diagnostics instead of inventing a
passing outcome.

```bash
# Dedicated GitHub Actions job publishes .NET and pulls the test-only
# netshoot image. Only disposable, private Podman namespaces are allowed.
E2_NETWORK_TEST=1 \
  E1_PG_DSN='host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local' \
  python3 lab/e2_orleans/test_podman_disconnect.py
```

**Strict limits:** `tc/netem` packet loss is a real Linux network
impairment but NOT a physical-host network cut, verified Orleans
application recovery, split-brain fencing, in-flight transactional
resilience or a measured production RTO. SQL remains reachable by a
second intentionally configured bridge. Separate C03 tests must send
real commands under partition and verify the post-heal grain/ledger
semantics. E2 remains `partially_verified`.

## E2-F10-C01 · Routable Orleans cluster across Podman network namespaces

**Original CI [#41126502385](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41126502385) passed** on source `0aff6e22eecece2157cf867eddece5d9b7964ccc`, uploading [the unmodified original raw observation](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41126502385/artifacts/13010797803) (artifact ZIP SHA-256 `840842e3549ed3bf23b0fbeff3e4b0133dae0f5c086bcade7fb168f413e8c6be`). The [archived evidence summary](../../evidence/runs/e2-orleans-podman-network.json) and an independent validator pin precisely this **single physical CI runner** result; overall E2 remains `partially_verified`.
A single GitHub Actions runner starts four **independently network-namespaced**
Podman containers: PostgreSQL 16.13, a primary Orleans 10.4.0 silo, a
secondary silo, and an independent client. All use a private bridge
`e2f10-net` (test-only `10.78.30.0/24`); no Orleans silo/gateway endpoint
is published on a public host interface.

The silos use `Microsoft.Orleans.Clustering.AdoNet` 10.4.0 with a
**shared durable PostgreSQL SQL membership catalog**, installed from the
two exact upstream SQL blobs with SHA verification. Each silo advertises
its actual Podman bridge address (`10.78.30.11` and `10.78.30.12`)
and binds to all container-local listening addresses; the external client
uses ADO.NET gateway discovery, not a hardcoded gateway list. We inspect
each container ID, address and `/proc/self/ns/net` identity, and require
**four different network namespace identities**.

The initial probe must observe account grains on **both** silo hostnames;
each issues a distinct committed transfer via the external client. After
actual secondary-container `SIGKILL` (exit 137), a formerly
secondary-hosted grain must reactivate on primary, and the PostgreSQL
membership catalog must persist its `Active (3)` → `Dead (6)`
transition with an increasing version. Stable-operation-ID replay must
be `DUPLICATE_COMMITTED`, and a new transfer must `COMMITTED`. The
original raw CI artifact includes the topology, container/network
namespace IDs, advertised addresses, SQL membership before/after,
source hashes and 7/7 independent accounting-oracle outcomes.

```bash
# The dedicated CI workflow installs dependencies and builds the app.
# Safe local reproduction requires disposable Podman and free 55435.
E2_NETWORK_TEST=1 \
  E1_PG_DSN='host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local' \
  python3 lab/e2_orleans/test_podman_network.py
```

**Strict nonclaims:** four network namespaces on **ONE physical Linux
runner** do not prove independently provisioned servers or failure
domains. This C01 baseline tests genuine addressable container
endpoints and real container death **after** a response, **NOT** injected
silo-to-silo partitions, network blackholes, split-brain/fencing,
multi-host failover or any performance/mainframe equivalence.
Follow-on F10-C02/03 will introduce controlled network-specific faults,
preserving independent original evidence per slice. See issue #24.

## E2-F09 · Deterministic in-flight SQL transaction failure (CI-verified single-host scope)

**Goal:** distinguish a real database transaction aborted by the death of
the *executing Orleans silo* from an already durably committed transaction
whose server dies before acknowledging the caller. These are different
failure boundaries and must be reported separately.

The test runs two independent Orleans 10.4.0 silo **OS processes**,
an external client, and the version-matched PostgreSQL ADO.NET membership
provider. Both scenarios use a disposable PostgreSQL 16.13 database:

1. **Before COMMIT:** an opt-in, exact-command test fixture
   (`E2_INFLIGHT_TEST=1`, operation `e2-inflight-pre`, 47 cents) first
   updates the source balance inside one uncommitted SQL transaction,
   then waits on a fixed PostgreSQL transaction advisory lock. The
   independent Python process holds that lock, checks that
   `pg_stat_activity.wait_event_type='Lock'` identifies the actual
   backend waiting on `pg_advisory_xact_lock(720260301)`, and verifies
   zero *visible* operation/posting/outbox records. It sends **SIGKILL
   to the executing secondary silo**, verifies that SQL rolled back,
   kills the ambiguous original external client, then releases the
   barrier. An automatic Orleans retry after node loss may legitimately
   execute on the survivor; the invariant is **at most one durable
   effect**, not a promise that the client will see a specific error.
2. **After COMMIT/before original server reply:** the executing secondary
   silo self-terminates with actual SIGKILL immediately *after* a
   complete database COMMIT for operation `e2-inflight-post`.
   A read-only SQL check must find exactly one operation, two postings
   and one outbox event, irrespective of what the ambiguous caller saw.

In each case, require SQL membership to transition from
`primary=3/secondary=3` to `primary=3/secondary=6` with increased
version, the former secondary grain on the surviving primary, stable
operation-ID replay, a new committed operation, exactly two final
business operations/four postings/two outbox records and **7/7**
independent accounting Oracle Gates. The two cases use separate
cluster IDs to avoid stale deployment membership.

```bash
# Run after the existing E2 disposable Podman PostgreSQL bootstrap
# and official Orleans v10.4.0 ADO.NET membership-schema installation.
E2_CLUSTER_PROVIDER=adonet python3 lab/e2_orleans/test_inflight.py
```

**Original CI [#41102529778](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41102529778) succeeded** at source commit `e52d3a1abcdbeb39e4c6c6e7de4ce5b85ab1008b`, uploading [the complete original raw file](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41102529778/artifacts/12999297273) (artifact ZIP SHA-256 `be96c779d1aba7383b9710d8800bea1621ddc9bdf288c07fc5430e5b43e67cf9`). [Archived repo observation](../../evidence/runs/e2-orleans-inflight-sql-commit.json) records the two outcomes and strict one-physical-host limitation. This narrowly verified slice does **not** change the overall E2 `partially_verified` status.
The artificial advisory gate proves a *particular* in-flight SQL
failure boundary; it is not a naturally occurring banking workload,
a cross-physical-node fault, persistent client retries across process
crashes, PostgreSQL HA, a production RTO, or mainframe capacity.

## E2-F08 · Pinned PostgreSQL ADO.NET membership (CI-verified local-process slice)

This separate functional trial keeps **the same authoritative SQL ledger**,
nonreentrant account grain and two external silo OS processes used in E2-F07,
but changes only the **Orleans membership and client gateway discovery**
mechanism from development/static clustering to
`Microsoft.Orleans.Clustering.AdoNet 10.4.0` using the `Npgsql`
provider invariant.

Run `setup_adonet_membership.py` against an **explicitly disposable**
PostgreSQL 16.13 Podman database (`e2lab`). It downloads the **two official
Orleans v10.4.0 vendor scripts** from the immutable upstream commit
`d114d7522a53b8cce4c6b97d44293e5c7273d766`, verifies both raw
Git blob SHAs before executing them with `psql ON_ERROR_STOP=1`, and writes
the original provenance including SHA-256 to
`lab/results/e2/e2-adonet-official-scripts.json`.

- `src/AdoNet/Shared/PostgreSQL-Main.sql` —
  Git blob `e4f78c86342297b7c7ffeb271b7be066e08f3508`
- `src/AdoNet/Orleans.Clustering.AdoNet/PostgreSQL-Clustering.sql` —
  Git blob `e90af40c886a47ea9ea4e84f640c48b572cee494`

The provider must register two silo endpoints in the **actual SQL
OrleansMembershipTable** with distinct gateway ports. An independent
client must find grains on **both** hosts through ADO.NET discovery.
After a real `SIGKILL` of the secondary (deliberately **after** its
first durable transfer replied), the surviving primary must host the
reactivated grain, stable-ID replay must be `DUPLICATE_COMMITTED`,
the next transfer must `COMMITTED`, and the independent seven-invariant
SQL ledger oracle must remain green with exactly 3 committed operations,
6 postings and 3 outbox events. Both pre-failure and post-recovery
membership rows and versions must be archived as raw JSON.

```bash
python3 lab/e2_orleans/setup_adonet_membership.py
E2_CLUSTER_PROVIDER=adonet python3 lab/e2_orleans/test_multiprocess.py
```

**Original CI [#41098437285](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41098437285) passed** with the [raw, unmodified artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41098437285/artifacts/12996714385) and [archived observation](../../evidence/runs/e2-orleans-adonet-membership.json). The membership table actually changed from active (3) to dead (6) for the secondary, while its version advanced from 4 to 5. This remains a one-physical-runner local-process test, NOT full E2 acceptance.
The PostgreSQL membership catalog is **not** grain/account persistence.
Both processes still share **one GitHub-hosted physical runner** and a
single PostgreSQL instance. This is a persistent membership backend, not
evidence of a cluster across failure domains, network partition recovery,
in-flight SQL COMMIT death, sustained TPS or mainframe equivalence.

Primary documentation:
- [Orleans ADO.NET database configuration](https://learn.microsoft.com/dotnet/orleans/host/configuration-guide/adonet-configuration)
- [Orleans ADO.NET clustering 10.4.0 package](https://www.nuget.org/packages/Microsoft.Orleans.Clustering.AdoNet/10.4.0)
- [Upstream Orleans v10.4.0 SQL source](https://github.com/dotnet/orleans/tree/v10.4.0/src/AdoNet)

## Two independent Orleans silo processes — E2-F07 (verified local-process slice)

This next, **deliberately limited** experiment extends the previously
co-hosted Orleans smoke test. A Python orchestrator starts:

1. A primary .NET Orleans silo process on silo port `11150`, gateway
   `30050`.
2. A distinct secondary .NET Orleans silo process on silo port
   `11151`, gateway `30051`.
3. One or more **separate external Orleans client processes**, configured
   with both static gateways.

The silos use Orleans **development** membership on loopback, and both
share the same disposable authoritative PostgreSQL `e2lab` ledger.
The test probes the **actual OS PID** hosting each account grain and
requires that grains reside on **both** silos. It performs real
transfers through both remote grain activations, then sends a genuine
`SIGKILL` to the secondary silo **after** those transactions finish.
The next external client must see the original secondary-owned grain
reactivate on the surviving primary. Stable-ID replay must yield
`DUPLICATE_COMMITTED`; a new transfer must commit exactly once.
The seven independent SQL invariants and the operation/posting/outbox
cardinality must all pass.

```bash
python3 lab/e2_orleans/test_multiprocess.py
```

The `E2_CLUSTER_TEST=1` switch is supplied only to spawned test
processes, not ordinary clients or accepted one-silo workloads.
[Original CI #41084584229](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41084584229) verified this slice. The [archived observation](../../evidence/runs/e2-orleans-multiprocess.json) references the [unaltered complete raw artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41084584229/artifacts/12991930047). The results prove **two independent local silo OS processes**, one external client, genuine secondary SIGKILL and bounded post-response grain reactivation. They do **not** prove separate physical nodes, production ADO.NET cluster membership, in-flight grain failover at SQL commit, capacity scaling, an RTO SLA or mainframe equivalence. Those remain separate E2 acceptance gates.

Official implementation references:
- [Orleans: run an application](https://learn.microsoft.com/dotnet/orleans/deployment/)
- [Orleans: typical development clustering configurations](https://learn.microsoft.com/dotnet/orleans/host/configuration-guide/typical-configurations)
- [Orleans: reliable ADO.NET clustering](https://learn.microsoft.com/dotnet/orleans/host/configuration-guide/configuring-ado-dot-net-providers)

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
