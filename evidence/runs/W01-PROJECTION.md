# W01 CAP-005 — original PostgreSQL projection/fallback run (4 November 2026)

[Español](W01-PROJECTION.es.md) · [W01 design and limitations](../../docs/research/w01-projection.en.md) · [Merged PR #92](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/92)

## Verified bounded claim

**`PASS_BOUNDED_SYNTHETIC_TESTS` — sixteen real-PostgreSQL tests passed on an exact PR-head checkout.** This is **not** a global migration or banking PASS.

- **Original run:** [Actions W01 #41853096276](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096276); original job `126654375641`.
- **Exact source/checkout SHA:** `730b40a241986fbd4975d60285bd1b149ec743f3` (both equal in original test JSON).
- **Merge commit:** `ce96fa0f4c8f4be950f08b67d8ae8e6049878e20`. The original PR-head run is **not** relabeled a merged-main result.
- **Original GitHub Actions artifact:** ID `13334909404`, `w01-postgresql-synthetic-original-not-bank-approved`, **2462 bytes**. GitHub artifact metadata publishes ZIP `sha256:c467243029ca0f37d0683c59f1b5fd242a01874eb73182ca475beecf5c8ad2ca`; originally expires 2 February 2027. That archive digest is from GitHub metadata and is **not claimed to have been independently recomputed by this documentation commit**.
- **Permanent source-exact transcript:** [verbatim selected original CI job log lines](W01-PR92-ORIGINAL-CI-EXCERPT.log) (16 tests and the independent post-test gate); [machine-readable transcription and original artifact metadata](w01-pr92-original-ci-summary.json). The log excerpt is **not** the entire CI job output; the JSON was transcribed from the original CI log and is **not the binary ZIP**.
- **Host/storage scope:** two real PostgreSQL 16.13 server clusters (different `pg_control_system()` system identifiers), each in a Podman container, on **one** GitHub-hosted Ubuntu 24.04 runner. Distinct cluster IDs do **not** imply independent physical fault domains.
- **Environment:** original source reports Python 3.12.15; test code, exact output, Podman version, PostgreSQL image identity, host identity and full logs are available through the original Actions artifact.

## Test controls — original CI result

| Group | Original test IDs and observed PASS |
| --- | --- |
| Baseline and ledger | 01 empty projection fallback; 02 initial rebuild, source read-only and independent ledger oracle; 16 no source-table mutation on repeated reads |
| Source COMMIT and freshness | 03 actual transfer COMMIT causes stale fallback; 04 refresh catches up and repeated operation ID is idempotent; 05 client minimum watermark uses source; 06 impossible minimum blocks |
| Corruption and rollback of stale state | 07 projection corruption forces fallback then explicit repair; 08 unversioned source edit is rejected by **refresh**; 09 source watermark regression is rejected |
| Availability refusal | 10 projection unavailable → authoritative fallback; 11 source clock unavailable → BLOCK; 12 source fallback unavailable → BLOCK |
| Safety and topology | 13 invalid parameters refused; 14 nonloopback address/opt-in guard refused; 15 PostgreSQL system identifiers distinct |

**All 16 test cases PASS, zero unexpected FAIL/ERROR**, as shown in the original job log. Deliberately invalid scenarios are successful **negative controls** because the application rejects the unsafe behavior. This does not mean the failure itself has been cured or that a banking production acceptance gate passed.

The independent SQL test oracle checks balance conservation, two equal/opposite postings per accepted source operation, one outbox, source clock and bounded account revisions. The projector opens source transactions **read-only** and writes only to the separate projection database. Source test writes are from a different test-only actor and commit ledger, postings, outbox and clock atomically.

## Important unresolved limitation (must not be softened)

A read first samples the source clock, then reads the projection. The source can COMMIT immediately **after** that sample. Therefore the label `PROJECTION_OBSERVED_CURRENT` means **current relative to the observed clock sample**, not an authoritative linearizable balance. A noncooperative writer that changes source balances without increasing the clock cannot be detected by watermark-only reads at query time; the **next refresh** rejects same-clock divergent source data. A production program must enforce source-owned version discipline, a verified CDC/snapshot-cutover protocol, client consistency rules, authorization, safe lag budget, resnapshot/recovery, and real customer oracles.

No streaming CDC, no physical HA, no measurable production throughput improvement, no cash authorization, no real mainframe or bank-owned source fencing, no actual Golden Master and no production SLO are proven. TODM **G2 = INCONCLUSIVE**, **G6 = BLOCK**. The catalog's 30 reference capabilities remain hypotheses; #32/#58 stay open; closed E2 #8 and frozen #53 remain unchanged. No release or tag follows from this result.

## Companion CI gates

On the same PR-head SHA, [Premerge #41853095794](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853095794), [Lab #41853095727](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853095727) (offline/native/Podman), and [Functional extraction waves #41853096032](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096032) succeeded. [Book #41853096066](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096066) had Markdown/links/ES-EN jobs successful when this observation was written; diagram status should be checked in the linked original run before claiming its full completion. The source PR did **not** alter any figure or generated chapter.
