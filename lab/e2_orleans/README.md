# E2 · Orleans-led account coordination (planned experiment)

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

## Planned implementation order

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
additional Orleans reentrancy negative control is still pending.

## Evidence and release policy

No E2 claims may enter the verified evidence registry until actual
GitHub Actions and a controlled Podman runtime execute the contract.
GitHub-hosted runners are now executing E2 on the public repository. Historical smoke and workload runs were archived separately and can be reviewed under `evidence/runs/`. Subsequent E2 fault-injection and capacity claims must each be independently validated, not inferred from the initial green runs.

Do not modify the protected original E1 tests or publish, tag, merge,
or open the repository without the maintainer's authorization.

See [issue #8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8)
and the [global experiment roadmap](../../docs/EXPERIMENT_ROADMAP.md).
