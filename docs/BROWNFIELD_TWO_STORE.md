# Brownfield coexistence: moving authority, not translating COBOL

**Status: proposed two-store experiment.** The source code is implemented;
only a successful original GitHub Actions run can establish its test results.

## Architecture and scope

The **synthetic legacy** is a separate process speaking a small black-box
transfer/balance contract and persisting to its own PostgreSQL database with
different table and column names. The **new capability** is the existing
.NET 10/Npgsql candidate in a *different* PostgreSQL database and container.
These are independent logical ledgers but not separate physical failure
domains, real CICS/Db2 semantics or customer-approved rules.

A shared database authority in the candidate environment admits just one
writer/epoch. Both modeled writers honor the shared lock while committing to
their *own* database. This is cooperative fencing, not 2PC: if an actual legacy
processor can bypass the controller, it may still post after cutover.

## Before the writer moves

1. Discover the capability behavior; capture both observed responses and
   separately approved business rules. This fixture has no customer Golden
   Master and no mandate.
2. Run read-only shadow predictions without publishing a second debit or
   outbox event. A stale read-only mirror can disagree: that is a reason to
   stop, not to normalize away the difference.
3. Stage a consistent source SQL snapshot into the non-authoritative target
   with the writer-switch lock held. Include all account versions, accepted
   and rejected operation IDs, fingerprints, postings, outbox and watermark.
4. Independently compare all five state dimensions and both ledger oracles.
   Reject the cutover on any mismatch or new source decision after staging.
5. Increment the shared authority epoch. Old-epoch commands from a
   *cooperating* legacy adapter must be rejected.

## Rollback is not a harmless switch

If the candidate has already posted new decisions, the old ledger is
outdated. Switching traffic back would resurrect obsolete balances and
potentially double-post a replay. This experiment therefore blocks rollback
with `FORWARD_FIX_REQUIRED` when the complete two-store state no longer
matches. A real bank needs a signed forward remediation or a separately
verified reverse-migration procedure, including external side effects and
settlement state; those are not implemented.

| Counterexample | Required result |
| --- | --- |
| Legacy writes after staging | CUTOVER BLOCKED |
| Missing target outbox event | CUTOVER BLOCKED |
| Late legacy operation after epoch change | FENCED |
| Replay after lost response | Durable duplicate, no second posting |
| Candidate-origin write followed by rollback | FORWARD FIX REQUIRED |
| Rogue direct legacy SQL write bypassing ACL | Detected by oracle; **not** prevented |

## TODM and remaining engineering gates

G0/G1 scope and provenance are synthetic. G2 business baseline is
`INCONCLUSIVE`. G4 construction and G5 technical negative oracles are
eligible only after source-head CI execution. G6 remains **BLOCK**.
Cross-database transaction interruption, journaled unknown outcomes,
external IBM Z fencing, capture/change streams, true fault isolation,
recovery-point evidence, operational SLAs and human business approval
remain open in [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).

Source, tests and [reproduction README](../lab/brownfield/coexistence/README.md)
are English only; this engineering narrative is paired with its Spanish
version. No release/tag change.
