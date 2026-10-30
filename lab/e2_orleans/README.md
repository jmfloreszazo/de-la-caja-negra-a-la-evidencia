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
