# E2 · Orleans-led account coordination (partially verified experiment)

**SINGLE-SILO FUNCTIONAL AND FIXED-WORKLOAD SLICES VERIFIED IN CI; OVERALL E2 NOT ACCEPTED.** The .NET 10/Orleans 10.4.0 co-hosted silo shares one authoritative PostgreSQL ledger across the direct and grain-routed paths. [Functional smoke #41053628769](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41053628769) passed five controls. [Seeded workload #41055928136](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41055928136) passed six route/profile runs with 600 committed transfers. No sustained capacity ceiling, multiple-silo or production proof exists. Its detailed executable acceptance
contract is in [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md). This
engineering laboratory and all future source, fixtures and READMEs are
**English only**.

## Why this experiment exists

E1 has established synthetic functional equivalence for the protected
SQLite reference and the PostgreSQL/SQL Server candidates, with original
CI evidence and independent accounting oracles. E2 asks a narrower and
falsifiable question: whether Orleans virtual actors can coordinate
account-keyed requests while **leaving debit, credit, postings, idempotent
operation record and outbox in one authoritative database transaction**.

The account grain does **not** own an ACID transaction spanning multiple
grains. It must never be used as a substitute for PostgreSQL locking,
conditional debit or operation-ID uniqueness.

## Engineering roadmap and remaining acceptance work

1. Pin `Microsoft.Orleans.Server` **10.4.0** and compatible Orleans
   packages for .NET 10, preserve dependency-lock fingerprints.
2. Extract the existing PostgreSQL E1b transfer logic behind one durable
   interface shared by both direct-ledger and Orleans-routed paths;
   preserve SQL isolation, retries and outbox semantics.
3. Add a non-reentrant account-keyed grain. No separate actor-local
   balance may become the source of truth.
4. Compare the original 16-account E1 behavior and failure contracts
   with independent SQL snapshots and the seven-invariant oracle.
5. Exercise deliberately unsafe cross-grain split writes and reentrancy
   only in disposable **negative-control fixtures**.
6. Prepare fixed uniform/hot operation lists: 1,000 benchmark accounts
   with exactly 50 hot accounts (5%) and another profile where one
   account receives 50% of request intents.
7. Compare baseline versus Orleans at equal offered load, transport and
   SQL pool settings; preserve full raw outcomes, p50/p95/p99 and
   committed transfers per second.
8. Run silo-failure and lost-response recovery, then independent
   oracle and mutation detection before any evidence promotion.

## Crossed-transfer regression gate

`test_e2.py` additionally exercises 32 concurrent, evenly balanced A→B and B→A transfers through each of the direct and Orleans routes. The required checks are all 32 durable commits, exactly 64 postings and 32 outbox events, unchanged opening balances for both accounts, equal persisted snapshots and seven independent SQL invariants. This exercises competing source-account requests, **not** an artificially induced PostgreSQL 40P01 deadlock, Orleans reentrancy or multi-silo failover. [CI #41059475191](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41059475191) passed this gate, with [the archived summary](../../evidence/runs/e2-orleans-crossed.json) and the [unaltered original raw artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41059475191/artifacts/12977474457).

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

## Unsafe Orleans reentrancy negative control

The isolated `UnsafeReentrantCounterGrain` deliberately uses Orleans
`[Reentrant]`, reads a stale in-memory value, waits for 16 overlapping
requests, and writes that stale value back. It is invoked only through
the separate `negative-reentrancy` test mode. The expected unsafe result
is **16 accepted method calls but actor-local value 1**, with no ledger
changes and all seven independent PostgreSQL invariants still valid.
This test is **not** evidence of a cross-grain transaction, a real
deadlock or persistence failure. The accepted `AccountGrain` is never
marked reentrant. [CI #41060526872](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41060526872) verified this negative result. The [archived observation](../../evidence/runs/e2-orleans-reentrancy.json) links to its [original, unmodified CI artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41060526872/artifacts/12978961633).

## E2-B05 · Real external open-loop functional smoke (NOT sustained capacity)

**Original GitHub-hosted [CI #41196070831](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41196070831) passed**, source SHA `e545b861045d3a6f6bee9262028fd05fb5bb9c63`, raw [artifact #13040601633](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41196070831/artifacts/13040601633) with independently verified ZIP SHA-256 `6b2ba79ed6379118a20b890050d198862443d248aaf2cf7fc5d271bc84afa4c0`. See [registered evidence](../../evidence/runs/e2-b05-external-smoke.json), [strict validator](../../scripts/check_e2_b05_external_smoke.py) and [preregistered experiment](B05_EXTERNAL_SMOKE_PROTOCOL.md). The original [negative timing run #41195913857](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41195913857) is retained, not counted as a pass.

A persistent **external client process in its own Podman network namespace** replayed the same prescheduled requests through the direct PostgreSQL and Orleans routes while two silos remained alive. Across two profiles and two routes, **320/320 requests dispatched and independently committed**, with **640 postings and 320 outbox rows**, **7/7 independent SQL Oracle Gates per run** and identical persisted-state hashes between routes for each profile. The scheduling clock was corrected to prevent early dispatch, and all original per-request offset vectors are retained.

**Strict scope:** only 4 seconds/80 offers per route/profile and one trial per point, all on **one physical Linux host**. This is not evidence of sustained throughput, a representative p99, saturated hot-account capacity, separate-host HA, production failover, dated Azure TCO or mainframe MIPS equivalence. Do not rank Orleans versus direct by these short latency samples. Issue #25 remains OPEN, overall E2 remains `partially_verified`.

## E2-F10-C03 · Actual SQL-only packet loss on a live Orleans silo

**Original CI [#41136779085](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41136779085) passed** on source `c91959521e7b10934f10f47e30f09496f555056a`. Its [complete unmodified original artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41136779085/artifacts/13017097945) was independently downloaded and SHA-256 verified (`9d66d1168d311e4363ef333a2707a29310845a60527c9deb2b053355628b28fe`). See the [archived summary](../../evidence/runs/e2-orleans-sql-partition.json), the [offline evidence validator](../../scripts/check_e2_sql_partition_observations.py) and the [experiment protocol](F10_C03_PROTOCOL.md).

This distinct C03 test drops 100% of packets on the secondary silo's
**SQL-only** interface while keeping the original secondary process alive
(PID 4090) and both Orleans gateways reachable. An independent client
targets a grain actually executing on the SQL-isolated silo: its 30-second
timeout reports an **ambiguous, unacknowledged request**, not a proven
rollback. The separate SQL observer confirms **zero new committed operations,
postings or outbox events while isolated**. Following SQL-network repair,
repeating the same operation ID commits exactly once; the final ledger has
2 operations, 4 postings and 2 outbox events, with 7/7 independent
accounting invariants. All four containers still share **one physical Linux
runner and one non-HA PostgreSQL instance**.

```bash
E2_NETWORK_TEST=1 \
  E1_PG_DSN='host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local' \
  python3 lab/e2_orleans/test_podman_sql_partition.py
```

**Scope limit:** C03 proves this narrow application-vs-SQL network failure
and durable ledger observation. It does not prove asymmetric network
partitions, fencing/split-brain safety, multi-node HA, availability SLO,
sustained capacity or mainframe MIPS parity. E2 remains `partially_verified`.

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
second intentionally configured bridge. The independent C03 test above covers a different SQL-only failure
with an actual in-flight Orleans client command. E2 remains `partially_verified`.

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
Separate F10-C02 and F10-C03 network fault slices now have original
CI evidence, but asymmetric cuts and distributed HA remain pending.
See issue #24.

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

## Reproduce the verified 1,000-account synthetic slice

Run from the repository root, with PostgreSQL 16.13 in a disposable Podman
container, the .NET 10 SDK, the E1 PostgreSQL oracle requirements installed
and both `E1_PG_DSN` and `E2_PG_NPGSQL` pointing to the **same** `e2lab`
database on loopback (see [E2 workflow](../../.github/workflows/e2-orleans.yml)).

```bash
dotnet build lab/Bank/Bank.csproj -c Release
dotnet build lab/e1_pg/PgBank/PgBank.csproj -c Release
dotnet build lab/e2_orleans/OrleansLab/OrleansLab.csproj -c Release
python3 lab/e2_orleans/test_e2.py
python3 lab/e2_orleans/test_workloads.py
python3 scripts/check_e2_observations.py
python3 scripts/check_e2_workload_observations.py
```

The workload creates **1,000 synthetic accounts**, selects exactly **50**
as a 5%-of-accounts hot set (80% of intents target that set), and tests a
separate profile with one account receiving exactly **50%** of the requests.
Each profile runs 100 requests through both direct ledger and Orleans on
the **same** local PostgreSQL; each candidate's four persisted tables and
seven read-only oracle invariants must agree. A fixed seed `20261030`
generates the requests, with synthetic 3 ms intent spacing.

The [machine-readable observation summary](../../evidence/runs/e2-orleans-workload-summary.json)
records exact run, job, artifact, source commits, latency percentiles and
matching state checksums. The [unaltered original full JSON artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41055928136/artifacts/12977285976)
retains the raw six-run metrics and environment fingerprints. **The
measured p95/p99 are from one co-located local runner and must not be
presented as an Orleans scaling advantage or production SLA.**

## Real single-cohost process-death control

The [original run #41056976342](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41056976342)
hard-killed the **actual** co-hosted Orleans/.NET process using SIGKILL
through both the direct-ledger and grain-routed paths. For each route,
the run injected death both **before** and **after** PostgreSQL COMMIT.

- Before COMMIT: the connection terminated and **zero** operation,
  posting or outbox rows persisted; fresh-host retry committed once.
- After COMMIT: the original operation, **two** postings and **one**
  outbox row persisted; fresh-host retry returned
  `DUPLICATE_COMMITTED` with no second debit.
- An isolated **deliberately unsafe split-SQL debit** failed the
  independent `conserved` and `projectionAgrees` invariants, and
  restoring the row made all seven pass.

Run the recorded controls on the same disposable E2 PostgreSQL fixture:

```bash
python3 lab/e2_orleans/test_process_crash.py
python3 scripts/check_e2_process_kill_observations.py
```

The [complete original vectors](../../evidence/runs/e2-orleans-process-kill.json)
retain the SIGKILL exit codes, four post-death states, recovery outcomes,
original job/artifact IDs, source SHA-256 manifest and independent oracle.
**This is one local process dying, not multi-silo reassignment, quorum
recovery, node failure, power loss, or production durability certification.**
The negative split is a SQL fixture, not production actor code; an
additional **cross-grain circular-call/reentrancy** negative control is still pending; the isolated actor-local stale-state fixture is verified separately.

## Evidence and release policy

No E2 claims may enter the verified evidence registry until actual
GitHub Actions and a controlled Podman runtime execute the contract.
GitHub-hosted runners are now executing E2 on the public repository. Historical smoke and workload runs were archived separately and can be reviewed under `evidence/runs/`. Subsequent E2 fault-injection and capacity claims must each be independently validated, not inferred from the initial green runs.

Do not modify the protected original E1 tests or publish, tag, merge,
or open the repository without the maintainer's authorization.

See [issue #8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8)
and the [global experiment roadmap](../../docs/EXPERIMENT_ROADMAP.md).
