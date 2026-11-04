# Source snapshot/log handoff — original 26-case synthetic oracle

**4 November 2026 · issue #58 · original PR #96 head.** [Español](SOURCE-HANDOFF.es.md) · [research protocol](../../docs/research/source-capture-handoff.en.md) · [original Actions run](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394).

## Audited technical result

**PASS_BOUNDED_SYNTHETIC_HANDOFF: 26/26 positive and adversarial Python tests passed; zero unexpected failures or skipped tests.** Source and checkout SHA: `63c2e2119d662569b92bb99791a4eb4d471355e4`. Original CI job `126849132395` on [run #41908404394](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394).

**Original artifact downloaded and checked independently:** `source-capture-handoff-synthetic-only-original` (GitHub artifact `13360258324`, **2099 bytes**). SHA-256 computed from the original downloaded ZIP:
`b15bf9d394d53f93280e707c9df538420ea22f53eeeb6d0a3c87b77aad0e943c`
which **matches GitHub's published artifact digest**. ZIP CRC verification passed on all three members: `original-result.json`, `test-original.log`, `provenance.txt`. Original runner: Python 3.12.15 and Ubuntu hosted Linux x86_64. Artifact is subject to GitHub retention (initial expiry 2 February 2027).

The original JSON reports `testsRun=testsPlanned=26`, `unexpectedFailures=0`, `skipped=0`, `nativeSourceCaptureExecuted=false`, `customerEvidenceBytesChecked=false`, `externalEffectOracle=false`, `realSourceWriterFence=false`, and `productionApproved=false`. The [machine-readable audit](source-handoff-pr96-audited-original.json) retains GitHub metadata and source file digests from the original runner, and the [selected timestamped test log](SOURCE-HANDOFF-PR96-ORIGINAL-CI-EXCERPT.log) retains all 26 original named test results. The latter is a **verbatim excerpt, not the original ZIP**.

## The actual observed boundaries

The **source trace is supplied by a synthetic fixture**, not a real mainframe. Tests verify source commit-to-snapshot consistency, resume cursor, remaining journal retention, exact event identity/order, refusal of missing/duplicate/reordered events, rejected aborted operations, source incarnation, target balances, numeric limits, invalid schema, and fabricated approval fields. The example models four synthetic accounts and five committed transfers with a cut at sequence 2 and a captured tail of sequences 3–5. These are **internal consistency checks**, not source authenticity.

This fixture does not establish true source commit order, CICS/UOR and Db2 log transaction grouping, VSAM or IMS batch completeness, IBM i receiver retention, Fujitsu platform semantics, physical source failover, external cash effects, privilege-controlled source fencing, bank load/SLO or approved Golden Master. A consistently **fabricated** source/capture pair could still pass. Reproduction against an independently authenticated bank-owned origin is still required.

**No banking signoff:** TODM **G2 = INCONCLUSIVE / G6 = BLOCK**. E2 remains `partially_verified`. Issue #58 stays OPEN; #32 completed for research, #53 frozen. No release/tag or customer cutover authorization follows from this synthetic test.

This record reflects **the original exact PR-head job**, not a claim of re-executing it on a later documentation or merge commit.