# E1c · SQL Server transactional evidence lab

This is a **disposable, synthetic SQL Server 2022 Developer experiment**,
not a mainframe, Azure, production bank, or capacity benchmark. The
repository uses **Podman**, not a Docker daemon. Engineering documentation,
tests, scripts and code are **English only**.

## Components

- `SqlBank/`: an independently implemented .NET 10 / Microsoft.Data.SqlClient
  7.1.1 transactional candidate, with account row locks, operation-ID
  application lock and unique constraint, two-sided postings and atomic outbox.
- `SqlOracle/`: a separately compiled **read-only SQL** accounting oracle
  checking seven persisted invariants; no business-function dependency.
- `SqlFixtures/`: an independent disposable-only negative mutation, duty
  isolation anomaly and two-slot SQL client-pool test tool.
- `schema.sql`: disposable 16-account ledger and two-row duty invariant.
- `test_e1c.py`: checks the unchanged SQLite reference and SQL Server, then
  concurrent withdrawals, duplicate requests, timeouts, real deadlocks,
  SNAPSHOT versus SERIALIZABLE, and deliberate ledger corruption.
- `.github/workflows/e1-sqlserver.yml`: actual Linux/Podman CI, original
  machine-readable artifacts and complete job logs.

The .NET projects pin `Microsoft.Data.SqlClient 7.1.1` and a patched
`System.Security.Cryptography.Pkcs 10.0.14`. NuGet vulnerability audit and
`TreatWarningsAsErrors` remain enabled.

## Requirements and local reproduction

Use .NET 10 SDK, Python 3.12+, Podman and a dedicated loopback SQL Server
container. SQL Server Developer has licensing conditions for development
and testing: review Microsoft's terms before accepting `ACCEPT_EULA=Y`.

These instructions are **destructive** to the purpose-created `E1SqlLab`
database. Never run against shared or customer systems.

```bash
export E1_SQL_PASSWORD='ChooseAnIndependentStrongLocalTestPassword!'
export E1_SQL_HOST='127.0.0.1,14333'
podman run -d --name e1-sqlserver --memory=4g \
  -e ACCEPT_EULA=Y -e MSSQL_PID=Developer \
  -e MSSQL_SA_PASSWORD="$E1_SQL_PASSWORD" \
  -p 127.0.0.1:14333:1433 \
  mcr.microsoft.com/mssql/server:2022-latest

dotnet build lab/Bank/Bank.csproj -c Release
dotnet build lab/e1_sqlserver/SqlBank/SqlBank.csproj -c Release
dotnet build lab/e1_sqlserver/SqlOracle/SqlOracle.csproj -c Release
dotnet build lab/e1_sqlserver/SqlFixtures/SqlFixtures.csproj -c Release

dotnet lab/e1_sqlserver/SqlBank/bin/Release/net10.0/SqlBank.dll version
python3 lab/e1_sqlserver/test_e1c.py
podman rm -f e1-sqlserver
```

The container must finish initialization before the version check succeeds.
The workflow generates and masks its own throwaway SA password. No
production credentials or customer records belong in this lab. Source and
schema are intentionally constrained to a dedicated test database and
loopback access.

## Full uniform/hot workload reproduction

After building both the unchanged SQLite reference and SQL Server candidate
and starting the disposable database, run:

```bash
python3 lab/e1_sqlserver/test_e1c.py
python3 lab/e1_sqlserver/test_worker_parity.py
python3 scripts/check_e1c_worker_observations.py
```

The second command resets the disposable `E1SqlLab` database for every
case. It validates 960 synthetic transfers per candidate across 1, 2, 4
and 8 workers with uniform and hot-account traffic. All four persisted
tables must match in every case and all seven independent ledger
invariants must pass. Original CI evidence is versioned separately from
the core E1c controls. Different worker process-launch models prevent
cross-engine throughput or latency comparisons.

## Evidence and acceptance boundaries

The [original E1c SQL Server 2022 CI run #41040632819](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41040632819) **executed and passed** all eight synthetic control groups. The [versioned source/output record](../../evidence/runs/e1c-sqlserver-initial.json) preserves the exact job, source commit, test SHA-256 values and individual observations. The controls below were observed in that run:

1. Sequential and persisted parity with the **unchanged** SQLite .NET 10
   baseline: committed, rejected, duplicate/operation-ID conflicts, invalid
   operations, crash/exception before commit and lost response after commit.
2. Concurrent overdraft and duplicate handling using separate .NET processes.
3. SQL Server `1222` lock timeout with bounded complete transaction retries,
   a lock released while retrying and no partial writes after exhaustion.
4. A real SQL Server deadlock victim, error `1205`, followed by a bounded
   **whole transaction** retry and independent ledger verification.
5. A deliberately unsafe **SNAPSHOT write-skew** duty rule, contrasted with
   **SERIALIZABLE** on the same two duty records.
6. A two-slot `SqlClient` pool that rejects a third lease promptly.
7. Seven independent ledger invariants with a deliberately deleted posting
   that the separate read-only oracle must reject and then accept after
   exact restoration.

The candidate uses `sp_getapplock` with transaction ownership for the
operation-ID critical section and canonical `UPDLOCK` account order. The
primary key still guards identity. Retryable SQL Server errors are `1205`,
`1222`, `2601`, `2627` and `3960`; these do not map one-to-one onto
PostgreSQL SQLSTATE `40P01`, `40001` or `55P03`, nor SQLite's single-writer
behavior.

`Encrypt=Mandatory` with `TrustServerCertificate=true` applies **only**
to this ephemeral loopback experiment. A production design needs managed
identities or securely governed credentials and certificate validation.

**Do not infer bank-grade durability, real CICS/Db2 behavior, power-loss
recovery, Azure availability, linear horizontal scaling, or MIPS parity
from this synthetic experiment.**

For SQL Server-specific locks, error numbers and isolation outcomes versus PostgreSQL and the protected SQLite baseline, see [engine semantics](SQL_ENGINE_SEMANTICS.md). **The 16-case core contract and the additional full 960-transfer uniform/hot worker matrix have both been executed on SQL Server.** [Original full-matrix CI #41042317263](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) and [versioned raw evidence](../../evidence/runs/e1c-sqlserver-worker-parity.json) show matching persisted accounting outcomes in all eight cases, with seven independent invariants passing. SQLite uses long-lived worker processes while SQL Server starts a .NET process for each transfer; cross-engine latency and throughput are **not comparable**.

Source references: [Microsoft SQL Server Linux containers](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker?view=sql-server-linux-ver16),
[SqlClient package](https://www.nuget.org/packages/Microsoft.Data.SqlClient/7.1.1),
[PostgreSQL/SQLite evidence](../e1_pg/README.md), and
[experimental roadmap](../../docs/EXPERIMENT_ROADMAP.md).
