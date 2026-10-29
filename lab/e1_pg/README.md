# E1 · PostgreSQL row-locking evidence lab

This is the **first executable slice** of [E1](../docs/EXPERIMENT_PROTOCOL.md). It runs against a real PostgreSQL 16 instance, using Podman for the database. It is **not yet the completed E1**. An independent .NET 10/Npgsql candidate is in `PgBank/`, but the original SQLite test-suite and SQL Server remain further gates.

The [Npgsql 10.0.3](https://www.nuget.org/packages/Npgsql/10.0.3) candidate is validated by running `python3 lab/e1_pg/test_dotnet.py` after installing .NET 10 SDK. The test resets the disposable database between Python and C# runs and compares persisted account, operation, posting and outbox state. It also runs concurrent and injected-failure cases.

The protected reference ledger under `lab/Bank/`, `lab/bank_test.py` and `lab/reference-results/` remains untouched.

## Run

From the repository root, on a machine with Podman and Python 3:

```bash
podman run -d --name e1-postgres \
  -e POSTGRES_PASSWORD=e1local -e POSTGRES_DB=e1lab \
  -p 127.0.0.1:55432:5432 docker.io/library/postgres:16.13
python3 -m pip install -r lab/e1_pg/requirements.txt
export E1_PG_DSN="host=127.0.0.1 port=55432 dbname=e1lab user=postgres password=e1local"
python3 lab/e1_pg/test_e1.py
podman rm -f e1-postgres
```

The password and port are **local development-only**. Never use these credentials on a shared host, exposed address or production database. `test_e1.py` **drops and recreates tables** and must only run on a disposable database. It records its run in `lab/results/e1/` (ignored by Git). The CI uploads the report as an artifact.

## What is tested

- Concurrent withdrawals preserve nonnegative balances with PostgreSQL row locks.
- Idempotency and operation-ID conflicts; outbox and two-sided ledger in one transaction.
- Exception/crash before commit, lost acknowledgment after commit.
- **Real deadlock:** two connections lock accounts in reversed order; a victim receives SQLSTATE `40P01` and retries the **whole** transaction.
- **Write skew:** an intentionally unsafe `READ COMMITTED` example violates an independent invariant; `SERIALIZABLE` detects conflict (`40001`) and, on retry, preserves the invariant.
- Pool saturation with a bounded `psycopg_pool` pool.
- Lock-timeout exhaustion (`55P03`) reports an inconclusive/rejected attempt without a partial debit.
- Independent SQL oracle rejects deliberately corrupted persisted postings.

## Evidence boundary

This is a **synthetic PostgreSQL/Python experimental candidate**. Its results are not a statement that a mainframe's MIPS, CICS/Db2 transactions, durability under power loss or cloud failover have been matched. Nor is this cross-engine equality proof: the .NET 10 PostgreSQL candidate, equivalence to the SQLite baseline and full fault matrix remain open.

See [E1 acceptance gates](../../docs/EXPERIMENT_ROADMAP.md). `evidence/claims.json` must continue to classify E1 as **designed, not fully executed** until those gates pass and a reviewer approves the promotion.

PostgreSQL describes `40001` as a serialization failure and `40P01` as a deadlock; both require careful whole-transaction retry, not replaying a failed statement. The authoritative documentation is [PostgreSQL 16: serialization failure handling](https://www.postgresql.org/docs/16/mvcc-serialization-failure-handling.html).
