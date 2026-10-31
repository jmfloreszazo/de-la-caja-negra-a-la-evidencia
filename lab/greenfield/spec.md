# Specification — CAP-007 + CAP-005 version 0.1

Classification: synthetic/unapproved, based on the reference hypotheses in PR #51.

## Inputs and contract
All financial amounts are integer minor currency units, nonnegative starting balances and positive transfer values. This fixture uses two synthetic accounts `A` and `B` and explicitly lacks currency conversion, holds, card authorizations, overdraft products and legal mandates.

`Transfer(operationId, source, target, amount, authorized, reply)`:
- `APPLIED`: a new valid authorized transfer updates both balances, creates two offsetting postings, one outbox reference and advances the logical version exactly once.
- `DUPLICATE_APPLIED`: exact replay of an applied operation (including authorization flag in this *synthetic* request fingerprint) has no additional effect.
- `ID_CONFLICT`: the same operation ID with a different fingerprint never applies.
- `REJECTED_UNAUTHORIZED`: a synthetic authorization flag is false; no state change. This is *not* a real authorization mechanism.
- `REJECTED_INSUFFICIENT`: source balance is too low; no state change.
- `UNKNOWN_AFTER_APPLY`: the process has applied its in-memory update but intentionally simulates losing the reply; a stable-ID replay still returns `DUPLICATE_APPLIED`. Not a durable crash/restart test.

`Balance(account, source, minimumVersion)`:
- For `authoritative`, return `BOOKED` and balance only if version >= requested watermark. Otherwise `UNAVAILABLE_VERSION`.
- For `projection`, refuse stale data with `STALE_PROJECTION`; after an explicit `project` action captures current state, return `PROJECTED_BALANCE` with its own version. **Projection is never authorized available funds**.

## State invariants and independent acceptance
- Currency is not mixed; sum of all booked minor units is conserved in this closed synthetic system.
- For each applied operation, exactly two nonzero, opposite postings affect distinct accounts.
- One unique outbox record per applied operation.
- No negative account balance or arithmetic overflow accepted.
- Logical version increments once per new applied operation; duplicate/conflicting/rejected commands do not advance it.
- Projection version cannot exceed authoritative version; insufficient freshness must not be concealed.
- An independent, manually curated gold record covers twelve commands/read observations in `contracts/cap007_cap005_synthetic.json`.
- Python oracle verifies exact expected results **and** independently recomputes ledger postings, conservation and outbox cardinalities; thirteen negative-control tests validate the oracle.

## Deliberate omissions / architecture gates
Real accounts require: authenticated principals, delegated mandates and policy versions; idempotency for rejected requests; debit/credit & outbox transactional storage; posting reversal lifecycle; source and target account existence; overdraft/holds and available funds; multi-currency value date; p99/SLO, RTO/RPO; network partitions; concurrent commands and retry deadlines; EOD and reconciliation. These remain explicit **not implemented** requirements, not implicit claims.
