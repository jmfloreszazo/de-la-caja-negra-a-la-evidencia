# SQL Server E1c: transactional semantics versus PostgreSQL and SQLite

**Observed synthetic scope:** actual SQL Server 2022 Developer container
(build 16.0.4305.5), .NET 10.0.403, Microsoft.Data.SqlClient 7.1.1,
one GitHub-hosted Linux runner with disposable, invented ledger data.
The [first E1c CI experiment](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41040632819)
and its [original JSON snapshot](../../evidence/runs/e1c-sqlserver-initial.json)
are evidence of the precise tests below, not production certification.

## Key distinctions

| Concern | Protected SQLite reference | PostgreSQL E1a/E1b | SQL Server E1c |
|---|---|---|---|
| Write locking | WAL `BEGIN IMMEDIATE`, one writer | Explicit row `FOR UPDATE`; multiple non-conflicting row writers | `UPDLOCK, ROWLOCK` reads; distinct row writers and lock-manager escalation rules |
| Request ID serialization | Single writer plus primary key | Transaction advisory lock keyed to operation ID plus unique constraint | Transaction-owned `sp_getapplock` per operation ID plus primary key |
| Deadlock retry | SQLite busy/locked (`5`/`6`), not a two-row deadlock | `40P01`, full transaction retry | Error **`1205`**, full transaction retry observed in opposite-order account locks |
| Lock timeout | Busy timeout + bounded process retry | `55P03` under `lock_timeout` | Error **`1222`** under `SET LOCK_TIMEOUT 750`; six failed attempts observed |
| Serializable conflict | Writers serialized; not a row-isolation analogy | `40001` serialization failure in E1a | `SERIALIZABLE` read-range locks produced an observed **`1205`** victim, which retried |
| Unsafe concurrency control | Single-writer behavior is not proof of a cross-row serializable solution | E1a demonstrates `READ COMMITTED` write skew on duty rows | E1c demonstrates **`SNAPSHOT` write skew**, with both duty rows disabled |
| Idempotency | Unique key in transaction | Unique key and transaction advisory lock | Unique key and `sp_getapplock` inside the SQL transaction |
| Local atomicity | Debit, credit, operation, postings and outbox in SQLite commit | Same local SQL contract on PostgreSQL | Same local SQL contract on SQL Server |
| Pool pressure | SQLite single-writer is not a SQL client pool | E1a: bounded psycopg pool | E1c: two-slot SqlClient pool, third lease rejected |
| Concurrency benchmark | Different process model | Different process model | Different process model, so no cross-engine throughput conclusion |

**Do not convert SQL error codes mechanically.** In particular,
SQL Server `1205` can arise from lock conversion when `SERIALIZABLE`
transactions both read and later update rows. PostgreSQL `40001`
reports serialization failure under SSI. These are observed differences
in the specific duty-row negative control, **not universal mappings**.

## Actual observed E1c controls

The original [successful E1c job](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41040632819)
recorded:

1. **16 matching sequential reference outcomes:** all four tables
   (accounts, operations, postings, outbox) match between the unchanged
   .NET/SQLite reference and SQL Server after each step. The independent
   SQL Server oracle passes at every checkpoint.
2. **Deadlock:** one opposing transfer received `1205`, retried once
   and committed; the other committed without retry. Both postings
   and the outbox remained consistent.
3. **Timeout exhaustion:** six genuine `1222` lock timeouts produced
   `RETRY_EXHAUSTED` without a persisted operation or postings.
   Release of a separate account lock during retries was also tested.
4. **Isolation anomaly:** two concurrent `SNAPSHOT` transactions
   each saw two active operators, updated different duty rows and left
   zero active. Under `SERIALIZABLE`, one transaction was a `1205`
   victim, retried, and the duty invariant retained one active row.
5. **Independent negative oracle:** all seven persisted ledger
   invariants were true before and after restoration. Deleting a
   posting made `balancedPostings`, `twoPostingsPerCommit` and
   `projectionAgrees` false; the other four invariants remained true.
6. **Concurrency and pool:** independent processes preserved nonnegative
   balances during overdraft competition and made only one durable
   effect per duplicate request ID. A third connection on the two-slot
   SqlClient pool failed within the bound.

The application deliberately uses a **test-only SA account** on
`127.0.0.1`. TLS is mandatory, but the self-signed container certificate
is trusted only by an explicit, non-production testing exception.
The fixture tool accepts mutation commands only with
`E1_SQL_TEST_ADMIN=YES_DISPOSABLE`.

## Known exclusions and outstanding gates

- SQL Server E1c is tested for these defined synthetic functional
  and isolation cases, **not** for every possible schedule, row-lock
  escalation, failover mode, edition, database compatibility level,
  transaction-log durability or SQL Agent/batch workload.
- The SQLite reference's separate uniform/hot **960-transfer** matrix
  is evidenced for PostgreSQL E1b, not automatically for SQL Server
  E1c. E1c would need an additional matching SQL Server load run to
  claim that matrix.
- No test equates CICS/Db2 transaction semantics, mainframe MIPS,
  Azure SQL or SQL Managed Instance availability, branch/WAN latency,
  or production RPO/RTO to this local SQL Server container.
- The SQL Server image tag `2022-latest` can move. Retain its digest
  from original CI artifacts, and prefer digest pinning for later
  independent reproduction. The schema and test data are disposable.

## Primary references

- [SQL Server 2022 container quickstart](https://learn.microsoft.com/en-us/sql/linux/install-upgrade/quickstart-install-docker?view=sql-server-linux-ver16)
- [Microsoft.Data.SqlClient 7.1.1](https://www.nuget.org/packages/Microsoft.Data.SqlClient/7.1.1)
- [SQL Server transaction isolation guide](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql)
- [SQL Server lock timeout guide](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-lock-timeout-transact-sql)
- [PostgreSQL/SQLite E1b semantics](../e1_pg/SQL_ENGINE_SEMANTICS.md)

**The scope of a verified synthetic experiment is not a release or
authorization to merge.** E1 overall remains partially verified while
the branch and editorial gates remain open.
