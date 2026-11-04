# W01 source-owned synthetic journal — integrated, NOT executed

**Checkpoint: 4 November 2026.** [Español](W01-SOURCE-JOURNAL-CHECKPOINT.es.md) · [PR #94 merged](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/94) · [Issue #58 still OPEN](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)

## Evidence classification and exact integration

- **Code integrated to main:** merge commit `69bb2e92fbfac66038d6ce1ca3234b020feb2d52`, exact PR head `80c45437312030a8abe90e0c3fdaa85a00c3056a`.
- **Actual test status when integrated:** `NOT_EXECUTED_CI_QUEUED`; the relevant GitHub-hosted workflows had **all remained QUEUED**. Neither 22/22 test PASS nor a partial test PASS is asserted.
- **Original pending runs:** [W01 source journal #41864738886](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738886); [Premerge #41864738991](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738991); [Lab #41864739021](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739021); [Book #41864739153](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739153); [W01 existing read-model #41864739079](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739079); [Evidence #41864739038](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739038); [Brand #41864738914](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738914). These links document **scheduled work only**, not successful evidence.
- **Evidence matrix:** [EN](EVIDENCE.md) / [ES](EVIDENCE.es.md), claim `BROWNFIELD-W01-FEED` explicitly marked IMPLEMENTED / NOT EXECUTED. The historical original W01 16/16 and 20/20 test campaigns remain separately preserved; their PASS cannot be reused as proof of this new code.

## What was implemented (not yet established by experiment)

`lab/brownfield/w01_feed/` adds a synthetic transactional source journal, initial repeatable-read MVCC snapshot cut, target digest+cursor committed together, sequential bounded replay with before/after image validation and SHA-256 hash chaining, missing-event refusal, target rollback injection and explicit bounded independent source/target reconciliation. The source test writer locks `legacy.clock` **before** selecting its previous hash to avoid races among concurrent disjoint-account writers, but this is a **single-row serialization bottleneck**, not high-throughput banking design. The separate source reader has SELECT-only grants in the fixture.

There are **22 written test cases**, including a new parallel 8-writer scenario and a tampered before-image whose digest is recomputed. These are **proposed negative controls**, not observed results. The full scan is capped to 256 synthetic operations and 16 accounts. The test harness owns the privileged PostgreSQL source writer; no source-side mainframe ownership is proven.

## How a real PASS for this bounded slice would be obtained

Follow the [Podman runbook](../lab/brownfield/w01_feed/README.md) on two **new disposable, locally bound** PostgreSQL 16.13 instances named `bf_legacy` (port 55438) and `bf_projection` (port 55442). The test harness executes destructive resets; **do not use customer/shared databases**. Ensure `W01_DISPOSABLE=YES` and the five exact test DSNs from the runbook.

```bash
python3 lab/brownfield/w01_feed/test_feed.py
cat lab/results/brownfield/w01-feed/feed-original.json
```

Do not run a supposedly successful `feed.py audit` after the whole suite: the last test **intentionally leaves a forged before-image** for its negative check. To demonstrate a clean audit, bootstrap a new pristine fixture separately.

The bounded technical gate requires an actually executed `22/22` with zero unexpected FAIL/ERROR, all negative refusals, original stdout/stderr, an independently inspectable test JSON, exact source and checkout commit hashes, Podman/PostgreSQL image identity, per-source hashes, and the GitHub artifact attached to the corresponding run. A job started from a newer or different SHA is a **different** execution, never the result of this initial PR-head. If CI later runs, update the matrix only after observing the original job/artifact; if it fails, keep FAIL/BLOCK with the defect and corrective PR rather than assuming a PASS.

## Scientific and migration limits

This is not a DB2 log reader, real source CDC, persistent stream-subscription recovery, signed/immutable journal, bank-scale log retention, physically independent HA, authorized business Golden Master or bank-controlled source fence. A privileged writer can rewrite the synthetic history or change balances without a version; a tail-only consumer may not notice until full audit. The original W01 balance read remains **nonlinearizable**.

**No global experiment or bank approval:** TODM G2 = `INCONCLUSIVE`, G6 = `BLOCK`; E2 remains `partially_verified`; issue #8 remains administratively closed, #32 completed for method only, #58 OPEN for actual source/business acceptance, #53 frozen. No book release or tag is authorized by this integration.
