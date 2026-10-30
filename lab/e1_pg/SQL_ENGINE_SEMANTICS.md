# SQLite and PostgreSQL: equivalent business outcomes, different execution semantics

This document describes the **observed synthetic E1b contract** and its limits.
It does not claim equivalence between SQLite and PostgreSQL execution engines,
or a production-grade banking transaction implementation. Source code, tests
and reproduction instructions are **English only**.

## Compared implementations

| Property | Protected .NET 10 / SQLite reference | Experimental .NET 10 / PostgreSQL 16 candidate |
|---|---|---|
| Transaction admission | `BEGIN IMMEDIATE` acquires SQLite's writer reservation before the transfer's reads | Ordinary PostgreSQL transaction; account rows explicitly locked with `SELECT ... FOR UPDATE` |
| Write concurrency | One writer at a time in the SQLite WAL database | Multiple writers can update disjoint rows; contention is per locked account, advisory operation ID and database resources |
| Lock ordering | No canonical per-row lock order: SQLite serializes writers | Account IDs are sorted before `FOR UPDATE`, reducing reversed-order deadlock opportunities |
| Retryable conflict | SQLite busy/locked errors 5/6 handled after rollback | SQLSTATE `40P01`, `40001`, `55P03` and `23505` trigger a **whole-transaction** retry |
| Attempt limits | 12 attempts, `sqlite3_busy_timeout(100ms)` and a short randomized backoff | 6 attempts, `SET LOCAL lock_timeout = '750ms'` and deterministic incremental backoff |
| Operation ID | Lookup and insert in the serialized SQLite write transaction; primary key blocks duplicate IDs | Transactional advisory lock keyed by operation ID, lookup plus primary key; retry after unique conflicts |
| Account invariant | Conditional debit and database nonnegative constraint | Conditional debit and database nonnegative constraint |
| Durable write unit | Account debit/credit, operation, two postings and outbox in one SQLite transaction | Account debit/credit, operation, two postings and outbox in one PostgreSQL transaction |
| Failure simulation | Exceptions and process exit before commit; exit 92 after committed response is deliberately lost | Same fault *intent* and exit codes; JDBC-style or exact storage durability is **not** implied |
| Isolation anomalies | SQLite's single-writer behavior does not establish PostgreSQL row-level isolation | PostgreSQL `READ COMMITTED` can exhibit write skew on a separately constructed duty invariant; E1a checks `SERIALIZABLE` / `40001` |

The two candidates **do not share identical locking, timeout, retry-count,
scheduling, throughput or crash-durability guarantees**. Equal results for
specific operations are contractual observations, not a proof of equivalence
for every possible schedule.

## Observed test results

- The [unchanged SQLite reference](../Bank/Program.cs) and the
  [PostgreSQL candidate](PgBank/Program.cs) were exercised by
  [test_reference_parity.py](test_reference_parity.py) using the same **16
  sequential commands**. The harness compared all four persisted tables
  after each operation and called an independent read-only PostgreSQL
  accounting oracle. See the [original CI observation](../../evidence/runs/e1b-reference-parity.json).
- In an additional scenario, the SQLite writer lock and PostgreSQL account
  row lock were each released while their respective client was retrying.
  The SQLite reference observed a busy retry. PostgreSQL observed
  `55P03` and subsequently committed once. This is **functional
  recovery equivalence**, not identical lock timing.
- The earlier [E1b extended observation](../../evidence/runs/e1b-extended.json)
  confirms bounded Npgsql lock-retry exhaustion with no partial ledger
  mutation and an independent oracle rejecting deliberately corrupted
  postings.
- The [E1a experiment](../../evidence/runs/e1a.json) separately demonstrates
  a real `40P01` deadlock, `40001` serialization failures, and the
  danger of using `READ COMMITTED` for a cross-row invariant.

All evidence is from synthetic Linux GitHub Actions/Podman experiments.
The E1 experiment remains **partially verified**, and issue
[#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6)
remains open.

## Outstanding gates

1. **Multiprocess logical-workload parity:** compare the reference's
   `uniform` and `hot` workloads for 1/2/4/8 workers, with the same
   operations and independent accounting controls. Distinguish an SQLite
   *worker process* from a PostgreSQL *service replica* and report no
   throughput-equivalence conclusion based on different launch models.
2. **Evidence granularity and reproducibility:** retain full independent
   oracle verdict vectors and negative-control outputs per comparison,
   plus exact runtime/container digests and case manifests.
3. **SQL Server:** isolation, deadlocks, retries and failure semantics
   require their own implementation and test run under issue #7.
4. **Operational capacity:** WAL checkpointing, PostgreSQL MVCC/VACUUM,
   transaction-log storage, connection limits, replication, power loss,
   backup/recovery, mainframe workload and branch WAN remain outside this
   synthetic experiment.

## Primary technical references

- [SQLite WAL mode](https://www.sqlite.org/wal.html)
- [SQLite transaction control](https://www.sqlite.org/lang_transaction.html)
- [PostgreSQL 16: explicit locking](https://www.postgresql.org/docs/16/explicit-locking.html)
- [PostgreSQL 16: transaction isolation](https://www.postgresql.org/docs/16/transaction-iso.html)
- [PostgreSQL 16: serialization failure handling](https://www.postgresql.org/docs/16/mvcc-serialization-failure-handling.html)

The actual reference and candidate implementations are the definitive
record of **what this repository tests**; documentation about a database's
possible features must not be confused with features exercised here.
