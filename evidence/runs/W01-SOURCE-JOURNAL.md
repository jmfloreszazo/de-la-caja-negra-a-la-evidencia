# W01 — Original source-owned journal experiment: bounded PASS

**Evidence date: 4 November 2026.** [Español](W01-SOURCE-JOURNAL.es.md) · [PR #94](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/94) · [original GitHub Actions run #41864738886](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738886)

## Status and reproducibility

**`PASS_BOUNDED_SYNTHETIC_TESTS`: 22 of 22 actually executed real-PostgreSQL tests passed; zero unexpected failures.** This is a **synthetic source-owned journal** experiment, **not** real DB2/VSAM/IMS/CICS CDC, mainframe fencing, financial read linearizability, or bank production acceptance.

| Evidence field | Value |
| --- | --- |
| Exact PR-head source/checkout SHA | `80c45437312030a8abe90e0c3fdaa85a00c3056a` |
| Merged main commit | `69bb2e92fbfac66038d6ce1ca3234b020feb2d52` |
| Original run / job | `41864738886` / `126695939112` |
| Original Actions artifact | `13341603193`, `w01-owner-journal-original-not-mainframe-cdc`, 3184 bytes |
| GitHub-reported artifact ZIP SHA-256 | `3019a6d70d928c71efa206d70d46cf362d85351f896e224debd6063951121806` |
| Independently recomputed downloaded original ZIP SHA-256 | `3019a6d70d928c71efa206d70d46cf362d85351f896e224debd6063951121806` — **MATCH** |
| ZIP integrity | CRC validated for all three members: `test-original.log`, `feed-original.json`, `provenance.txt` |
| Test environment | Python 3.12.16; Podman 4.9.3; PostgreSQL 16.13 image; two separate PostgreSQL container servers on **one hosted Ubuntu runner** |
| Original artifact expiry | Initially 2 February 2027, subject to GitHub retention |

The original ZIP was **downloaded**, its SHA-256 independently recalculated, and its JSON, original test output and provenance inspected. [Machine-readable manifest](w01-source-journal-pr94-original-ci-summary.json) preserves original report, SHA, metadata and recorded source-file digests. [Original timestamped CI excerpt](W01-SOURCE-JOURNAL-PR94-CI-EXCERPT.log) preserves selected unchanged lines; it is not a byte-for-byte replacement for the ZIP. This evidence record does **not** relabel the original PR-head run as a run on the merge commit.

## What was actually tested

The original runner reported twenty-two `... ok` cases, including:

- Atomic source COMMIT of two postings, outbox, source clock and source journal; source rollback produces no financial side effects.
- Consistent MVCC snapshot bootstrap, transactionally applied target balances/cursor and incremental catch-up including a COMMIT after snapshot capture.
- Missing or deleted historical sequence, changed hash or broken hash-chain predecessor, a recomputed but semantically incorrect before-image, and corrupted target accounts: **rejected**.
- Injected failure after target row mutations but before cursor COMMIT: both row changes and cursor roll back, and retry succeeds.
- Nonprivileged source `w01_feed_reader` cannot mutate financial or journal tables or inspect private operations; a superuser source DSN is rejected.
- Eight concurrent synthetic source writers on disjoint accounts retain one ordered journal, through an acknowledged **global source clock-row lock**.
- Independent bounded full-history reconciliation detects nonjournaled privileged source changes and deletion of already-consumed history that tail-only polling may miss.

On the **same original PR-head SHA**, the Premerge, Lab, Book, Brand, Evidence claims and legacy W01 snapshot workflows also completed **SUCCESS**; their original run IDs remain in [the dated checkpoint](../../docs/W01_SOURCE_JOURNAL_CHECKPOINT.md). No new tag or release was generated.

**Known log labeling error:** the last workflow `print(...)` line says **“20/20”**, but its explicit gate assertion and the source-run JSON both require and report `testsRun=testsPlanned=passed=22`; all 22 named cases occur in the original test output. The contradictory static print is an **output-label typo**, not a missing test. A subsequent attempt to edit that workflow message was blocked by connector security controls; the original log is intentionally unmodified.

## Limits and gating

The system has a 16-account/256-event synthetic ceiling, one hosted physical fault domain, a privileged **test-only** source writer, a manually constructed PostgreSQL journal and no independent bank source attestation. SHA-256 hash chains are not external signatures and do not stop a privileged writer rewriting history. Audit is explicit rather than continuous. A read of source clock followed by a projection read is not linearizable. No native CDC log position/retention, recovery from platform-level failover, performance envelope, bank Golden Master or real writer fence is established.

**TODM G2 remains `INCONCLUSIVE`, G6 `BLOCK`.** E2 remains `partially_verified`; #8 is closed administratively, #32 completed for research only, #58 **OPEN** for customer-controlled proof, #53 frozen. This laboratory PASS is **not** bank acceptance.
