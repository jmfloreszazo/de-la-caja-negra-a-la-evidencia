# W01 — From full snapshots to a source-owned transactional journal

**Issue #58 · 4 November 2026 · Brownfield research, NOT mainframe CDC or bank acceptance.** [Español](w01-source-journal.es.md). Companion [executed W01 PostgreSQL projection](w01-projection.en.md) and [read-role proof](w01-reader-identity.en.md).

## Why this increment exists

W01's original read model took full PostgreSQL snapshots, checked a sampled source clock and fell back to the legacy database on stale/corrupt data. Its 20-case follow-up established **SQL-enforced SELECT-only credentials**. Neither proved that the source emits a complete, replayable journal, that an initial snapshot aligns with subsequent changes, or that failures cannot publish partial target state.

The new experiment builds a **synthetic transactional change journal in the source fixture**, with 20 real-PostgreSQL test scenarios. It does not use a COBOL parser or assume a particular IBM Z, IBM i, Fujitsu, BS2000, IMS, CICS or Db2 change-capture mechanism.

## Architecture and invariants

```text
              TEST-ONLY authorized source writer
                            │
         ONE PostgreSQL source COMMIT (not cross-DB)
         ledger + paired postings + outbox
             + source clock + source journal
                            │
                     source-owned cut
                 RR read-only source snapshot
                            │
                [16 balances + clock + hash]
                            │
                   target atomic bootstrap
                            │
                target balances + source cursor
                            │
           source tail: seq+1, seq+2, ... seq+n
                     verified and replayed
                            │
               ONE target SQL COMMIT per batch
                            │
            explicit full-history reconciliation
```

The source journal stores **committed** event sequences, operation IDs, both account before/after images and a hash chain. Its test producer advances `legacy.clock` in the **same SQL COMMIT** as financial postings, outbox and event. It deliberately does *not* use `BIGSERIAL` for gap-free sequencing: aborted PostgreSQL transactions may consume sequence values without committing an event.

The source reader has SELECT on balances, clock and journal only; **no financial DML privilege**. The target uses its own PostgreSQL transaction to atomically publish applied balances, cursor, head hash and digest; a simulated crash after row updates but before cursor publication rolls all target changes back.

At bootstrap the reader captures source balances, cursor and full bounded history in one `REPEATABLE READ` snapshot. A later source COMMIT belongs to a later catch-up batch. Replay checks missing sequence numbers, predecessor hashes, tampered content, unchanged-account before images and target integrity; it refuses an unknown or corrupted history instead of silently jumping to the current source balance.

**Independent audit** reconstructs the 16-account synthetic history from known fixture genesis, checks balance conservation and compares the source state with the projection only when cursors coincide. Historical journal deletion or an out-of-band privileged source mutation is detected by this independent sweep, **not necessarily by a tail-only consumer**. SHA-256 detects accidental change but a privileged source administrator could rewrite an entire chain; **not cryptographic provenance**.

## Refusal matrix

| Scenario | Required result |
| --- | --- |
| Missing event between applied cursor and observed source clock | **BLOCK; cursor unchanged** |
| Journal hash altered or predecessor chain inconsistent | **BLOCK; target transaction rollback** |
| Source COMMIT after snapshot capture and before target installation | Safe later **catch-up**, not mistaken for bootstrap |
| Target crash between updating balances and cursor | **Both rolled back**, replay on next attempt |
| Source transaction rolls back before event COMMIT | **No financial posting, outbox, clock or event** |
| Target accounts modified outside cursor contract | **BLOCK** using target digest and before-image checks |
| Source ledger modified without a new event/version | **Explicit audit BLOCK**, while tail-only polling may miss it |
| History deleted behind the current cursor | **Audit BLOCK**; tail-only no-op is not sufficient |
| Reader tries UPDATE or access to private transactions | PostgreSQL **permission denied** |
| Second bootstrap over applied state | **BLOCK**, no cursor rewind |

## Acceptance boundary: synthetic journal vs actual CDC

This experiment has no WAL decoding, replication slot, DB2 log reader, MQ capture, IMS/CICS source hook, offset retention guarantee, source restart/warm-up process, checkpoint lease, independent failover topology or externally signed source anchor. It replays **at most 256 synthetic operations** and audits an all-16-account fixture. This is not a scale/performance benchmark. Real CDC is product/version specific and must define (among other items): snapshot/log rendezvous, transaction commit order, delete/update handling, schema evolution, gaps/retention/rewind, privileged/batch/offline writers, recovery, topology, privacy and independent financial reconciliation.

A green 20-case synthetic run is evidence **for the explicitly implemented contract**, not proof that a mainframe source can provide those events. A source clock sampled before target read still permits a later source COMMIT: W01 remains **nonlinearizable**. The prior W01 read interface is unchanged by this sibling laboratory; it is a **separate architectural experiment**, not a production replacement.

The real incumbent-owned fence and accounting acceptance remain [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) and the [source-fence protocol](../BROWNFIELD_SOURCE_FENCE.md). TODM **G2 INCONCLUSIVE / G6 BLOCK**, no released banking cutover. E2 remains `partially_verified`, its #8 administratively closed, and frozen #53 unchanged.

## Reproducibility

Execute the [Podman laboratory](../../lab/brownfield/w01_feed/README.md). The original-head GitHub Actions artifact and any adverse results must be linked here **after** the workflow runs, with exact source SHA, test counts and raw-log provenance; documentation alone is not a PASS.
