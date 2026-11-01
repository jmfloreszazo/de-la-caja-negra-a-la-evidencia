# Durable brownfield slice: one SQL authority is not yet a bank cutover

**State: proposed executable implementation; no original PostgreSQL CI result yet.**

CAP-007 (internal transfer) and CAP-005 (booked balance) are being rewritten
from a **legacy-defined capability contract**, not from COBOL syntax. This
remains brownfield because existing interfaces, rules, balances, settlement
calendars and the incumbent system define what must be preserved. Creating a
new .NET component does not turn the program into greenfield engineering.

## Explicit claim boundary

The candidate in [the laboratory](../lab/brownfield/durable/README.md) stores
one logical authority row in disposable PostgreSQL and fences transfers by
writer and epoch inside a single SQL transaction. Per-operation fingerprint,
paired postings, outbox and account balances are atomic. A separate clock
records decided commands and allows a version-minimum check for authoritative
balance queries. The orchestration supports a synthetic writer switch and
switch-back, holding a database-exclusive fence until earlier commands finish.

This **does not mean** that a real CICS/Db2/COBOL incumbent has stopped
writing, that two authoritative stores agree, or that rollback of a production
cutover is safe. The labels `legacy` and `candidate` are modes of the **same**
synthetic SQL engine. They are not independent bank implementations.
The synthetic G6 field is always `BLOCK`.

## Failure hypotheses to falsify

| Control | Required external observation | Limit |
| --- | --- | --- |
| Before COMMIT | SIGKILL after observable uncommitted debit; no SQL row/posting effect; identical-ID retry commits once | One local PostgreSQL instance |
| After COMMIT | Process disappears before reply; SQL decision survives and identical-ID replay is duplicate | Lost reply, not all network partitions |
| Concurrent hot key | Multiple independent client processes; no negative balances or partial postings | Fixed, tiny fixture, no capacity claim |
| Cutover | Old epoch rejected for a new operation, already decided ID remains duplicate | Does not fence an external legacy writer |
| Balance freshness | `BELOW_MINIMUM_VERSION` for an unavailable version | Direct authority, **not** an asynchronous projection |
| Corrupted posting | Independent SQL oracle fails before restoration | Mutated disposable data only |

## Independent acceptance ladder

1. **Code review**: review SQL lock order, fingerprint coverage, idempotency,
   retransmissions, rejection semantics, data types and amount boundaries.
2. **Original CI run**: actual .NET 10 and PostgreSQL 16 execution, captured
   source SHA, database image digest, build logs, test JSON and negative cases.
3. **Business G2**: obtain approved customer-specific behavior, mandate and
   interface contract. An observed Golden Master alone is not policy approval.
4. **Coexistence**: actual old/new adapters, controlled source authority,
   independent durable two-side reconciliation, cutover rehearsal and rollback
   vetoes.
5. **TODM G6**: real accountable human signoff for an exact build/environment,
   never inferred from technical CI success.

Until steps 2–5 exist, classify the work as **SOURCE IMPLEMENTED /
EVIDENCE INCONCLUSIVE / BUSINESS APPROVAL BLOCKED**. E2 remains separately
`partially_verified`, and no published release is changed.

Tracked by [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).
