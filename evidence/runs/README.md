# Executed evidence · E1 PostgreSQL and .NET 10

**Brownfield C2 original journal evidence:** [EN CI provenance and limitations](BROWNFIELD-JOURNAL.md) · [log-extracted observations](brownfield-c2-pr66-ci-log-extracted.json). Technical synthetic slice only; unresolved and bypass negatives remain intentional, G6=BLOCK.

This is **experimental evidence**, not a benchmark or a claim of mainframe equivalence. The accompanying JSON files were extracted from the result blocks emitted by **real GitHub Actions runs**. They are neither reconstructed screenshots nor fabricated example results.

| Test | E1a · PostgreSQL/Python | E1b · PostgreSQL/.NET 10 |
|---|---|---|
| Provenance | [CI #40921291469](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40921291469) | [CI #40919773614](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) |
| Versioned evidence | [e1a.json](e1a.json) | [e1b.json](e1b.json) |
| Verdict | PASS, 11 controls | PASS, 7 controls |
| Real contention | `40P01` observed and full transaction retried | Concurrent transfers; no claim of identical deadlock coverage |
| Isolation anomaly | `READ COMMITTED` breaks invariant; `SERIALIZABLE` raises `40001` and retries | Not covered in this subset |
| Ledger and outbox | Independent SQL oracle verifies conservation, postings and outbox | Persistent-state Python/C# comparison and external oracle |
| Negative control | Intentional removal of a posting detected | Independent oracle reused after C# cases |
| Tested environment | PostgreSQL 16.13, Linux/Podman runner | .NET 10, Npgsql 10.0.3 and PostgreSQL |
| Not demonstrated | Production load, MIPS, CICS, distributed recovery | All SQLite contract controls and SQL Server |

## SQL Server E1c: full synthetic worker-matrix result · 30 October 2026

[Original successful CI #41042317263](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) · [versioned machine-readable execution](e1c-sqlserver-worker-parity.json). The unchanged .NET 10/SQLite reference and an independent .NET 10/SQL Server 2022 Developer candidate performed eight synthetic uniform/hot-account scenarios with **1, 2, 4 and 8 workers, 32 commands per worker**. Across all eight cases, **960 transfers were committed by each candidate**, all four persisted tables matched and each of the seven independent accounting invariants returned true. The preserved record contains the exact run and job, original artifact ID, source and merge-checkout SHAs, source hashes and case-level results.

The earlier [E1c initial 8-control run](e1c-sqlserver-initial.json) and [10-control extension](e1c-sqlserver-extended.json) independently demonstrate real SQL Server `1205` deadlock retries, six bounded `1222` lock timeouts, `SNAPSHOT` write-skew negative control, `SERIALIZABLE` defense, rejected ledger corruption, database uniqueness, and a separate SqlClient `-2` command timeout. The old E1a/E1b rows above describe their **original historical runs only**.

**Scope boundary:** SQLite's long-lived workers differ from SQL Server's per-transfer .NET CLI processes. This is functional/accounting parity within the exact synthetic matrix, **not** latency, throughput, production bank, power-loss durability, SQL Server HA or mainframe MIPS evidence. Overall E1 is still marked partially verified and the branch is not merged.

## Extended E1b observation · 30 October 2026

The original [7-control E1b record](e1b.json) remains unchanged. A **separate, actual GitHub Actions execution** added three controls to the .NET 10/Npgsql candidate: bounded `55P03` lock retry exhaustion (six attempts with no ledger side effects), successful retry and idempotency after unlocking, and an independent SQL oracle rejecting a deliberately corrupted .NET posting before the posting was restored.

[Immutable extended record](e1b-extended.json) · [GitHub Actions run #41024101879](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) · [original job and raw artifact](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879).

**Observed: PASS for all 10 controls.** The original 7-control execution is historical and its source digest is pinned to its 2026-10-29 commit; the extended record's source digests are matched to the current branch. The offline validator does **not** pretend that the historical test script equals the updated one. Neither result completes the full SQLite reference contract, E1c, or E1 overall.

## Direct SQLite ↔ PostgreSQL contract parity · 30 October 2026

The new [immutable E1b-reference-parity JSON](e1b-reference-parity.json) preserves the **actual** [CI run #41031578923](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923), its job and artifact identifiers, source commit, original checkout, source hashes, 16 individual cases and tool versions. The original **unchanged .NET 10/SQLite executable** and the **.NET 10/Npgsql PostgreSQL executable** received identical synthetic operations. After **each** case, balances, operation records, postings and outbox matched, with a passing independent PostgreSQL accounting oracle.

Coverage includes committed/rejected and duplicate operations, conflicting IDs, invalid inputs, exceptions and process death before commit, lost acknowledgment after commit and subsequent safe replay. A real SQLite write lock and a PostgreSQL row lock were each released while their respective clients retried; PostgreSQL observed `55P03` and then committed once. The six control groups and all 16 sequential cases passed.

**Not demonstrated:** the entire SQLite multiprocess workload matrix, identical lock implementations or timings, SQL Server equivalence, durability after power loss, WAN, or mainframe throughput. The earlier E1b records remain intact. E1 remains partially verified.

## Full independent oracle verdict vectors · 30 October 2026

[Recorded run #41032714628](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41032714628) · [Original before/corrupted/restored vectors](e1b-oracle-vectors.json). The separate read-only PostgreSQL oracle checks seven invariants after the direct cross-engine test. All seven passed initially. Removing one actual committed posting triggered exactly **three failures**: `balancedPostings`, `twoPostingsPerCommit` and `projectionAgrees`. Restoring that same row returned all seven to PASS. The unchanged original run, manifest and CI artifact are preserved.

This is a **single-database negative control**, not a simulation of production failures or a proof of mainframe capacity. The E1b reference and candidate code hashes are checked without rewriting earlier observations. E1 remains partially verified.

## Reproducibility manifest · 30 October 2026

[Versioned runtime manifest](e1b-runtime-manifest.json) · [successful CI run #41033595770](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41033595770). The evidence includes Python, .NET SDK, Npgsql, psycopg, native SQLite, PostgreSQL and Podman versions; the PostgreSQL image ID and registry SHA-256 digests; six source hashes; and separate **PR source HEAD** and temporary **GitHub merge checkout** identifiers. An online CI check validates the originating job. These details enable narrower reproduction but do not establish cross-platform portability or operational equivalence.

## Complete reference worker-matrix parity · 30 October 2026

[Original 960-transfer execution](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329) · [machine-readable result](e1b-multiprocess-parity.json). All **eight** synthetic workload cases passed: uniform and hot-account traffic, each with 1, 2, 4 and 8 SQLite reference workers and **32 operations per worker**. The .NET 10 PostgreSQL candidate replayed the same operation IDs, source/destination accounts and amounts concurrently. For every case, operations, balances, postings and outbox matched, and all seven independent PostgreSQL accounting invariants passed. Both candidates committed all **960 logical transfers**.

The SQLite reference used its original **long-lived worker processes**; the PostgreSQL test used separate .NET CLI processes per transfer. Consequently, the harness time, launch costs, retries and any latency/throughput values are **not** comparable performance measurements. The synthetic accounting contract is now covered for the reference's uniform/hot worker matrix; SQL Server and mainframe operational capacity remain outside E1b.

## Three inspectable findings

1. **Recovered deadlock:** PostgreSQL returned `40P01`; the whole transaction was retried and both transfers ultimately committed without duplicate postings.
2. **Isolation matters:** the negative control left zero active operators under `READ COMMITTED`. With `SERIALIZABLE`, one stayed active and two `40001` failures were observed.
3. **An oracle that contradicts:** removing a posting made the independent read-only checker reject the ledger via `balancedPostings`, `projectionAgrees` and `twoPostingsPerCommit`.

**Offline evidence-integrity check:**

```bash
python3 scripts/check_e1_observations.py
```

The checker validates recorded controls, current source SHA-256 values for current-code observations, and the pinned commit/source manifest of the historical E1b observation; it does not byte-match historical sources against updated code. Each JSON preserves `runId`, `jobId`, source commit, limitations and observations. The elapsed time reflects only **this synthetic test**, not production transactional latency.

The overall experiment remains **E1 partially verified**: E1c and comprehensive reference-contract parity are outstanding.

[C2: in-flight controller TCP loss](BROWNFIELD-CONTROLLER-LOSS.md): two original cases, unchanged ZIP and JSON; no bank acceptance.

## W01 CAP-005 — independent PostgreSQL read projection, 4 November 2026

[Original PR-head CI 41853096276](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096276) passed **16/16** real PostgreSQL synthetic snapshot/watermark/fallback controls, including actual committed source transfers, stale projection, corrupt read model, source clock bypass/regression and failure refusals. [EN audit](W01-PROJECTION.md) · [ES audit](W01-PROJECTION.es.md) · [selected verbatim CI test log](W01-PR92-ORIGINAL-CI-EXCERPT.log) · [machine-readable provenance](w01-pr92-original-ci-summary.json). Two PostgreSQL clusters ran on **one hosted physical runner**; this result establishes neither CDC, linearizable financial reads, actual mainframe authority, production HA nor TODM G2/G6 acceptance. The Actions ZIP artifact has finite retention and the log excerpt/JSON are retained in Git with explicit transcription limits.

## W01 source-owned PostgreSQL journal — 4 November 2026

**Audited exact PR-head result: 22/22 real PostgreSQL tests PASS (synthetic, not bank CDC).** [Original run #41864738886](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738886) on source `80c45437312030a8abe90e0c3fdaa85a00c3056a`; merged by PR #94 as `69bb2e92fbfac66038d6ce1ca3234b020feb2d52`. The original artifact ZIP was downloaded and its SHA-256 independently recomputed: `3019a6d70d928c71efa206d70d46cf362d85351f896e224debd6063951121806` (matches GitHub's digest), with member CRC verification. See [EN original-run report](W01-SOURCE-JOURNAL.md) · [ES report](W01-SOURCE-JOURNAL.es.md) · [original timestamped CI excerpt](W01-SOURCE-JOURNAL-PR94-CI-EXCERPT.log) · [machine-readable original ZIP audit](w01-source-journal-pr94-original-ci-summary.json). Checks cover source transaction/journal atomicity, snapshot cut, replay with cursor transactionality, gaps/hash/semantic negatives, source rollback, privilege rejection and eight synthetic concurrent writers. **Not** authentic Db2/IMS/CICS CDC, bank-owned fencing, physical HA, linearizable reads, production capacity or G2/G6 approval. The earlier [not-yet-executed checkpoint](../../docs/W01_SOURCE_JOURNAL_CHECKPOINT.md) is retained with an explicit superseding update.

## Source-native CDC owner intake — 4 November 2026

[Original GitHub Actions run #41898291348](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41898291348) completed **22/22 fail-closed structural Python intake tests**, checking source path coverage and declaration integrity for Db2 z/OS, VSAM CICS/batch, IMS online/DL/I, IBM i and unverified other vendors. [EN audited original CI evidence](SOURCE-CAPTURE-INTAKE.md) · [ES evidence](SOURCE-CAPTURE-INTAKE.es.md) · [selected timestamped test log](SOURCE-CAPTURE-PR95-ORIGINAL-CI-EXCERPT.log). CI used the PR **test-merge** checkout, distinct from the PR source head and main merge commit; no artifact ZIP was produced by this workflow. **This is not source-native CDC execution**: all seven example paths remain UNKNOWN, references are not byte-verified, Fujitsu/other support remains unverified, and G2/G6 remain INCONCLUSIVE/BLOCK. The earlier source-owned W01 22/22 PostgreSQL journal experiment is a separately scoped synthetic ledger proof.

## Snapshot-to-journal continuity oracle — original synthetic 26/26 PASS

[Original exact-head Actions #41908404394](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394) ran **26 Python positive/adversarial checks** over the independent *synthetic* four-account, five-commit snapshot/tail fixture; all passed. Original ZIP artifact `13360258324` downloaded and independently rehashed to SHA-256 `b15bf9d394d53f93280e707c9df538420ea22f53eeeb6d0a3c87b77aad0e943c` (matches GitHub metadata), member CRC PASS. [EN original-run audit](SOURCE-HANDOFF.md) · [ES audit](SOURCE-HANDOFF.es.md) · [original timestamped CI excerpt](SOURCE-HANDOFF-PR96-ORIGINAL-CI-EXCERPT.log) · [machine-readable ZIP audit](source-handoff-pr96-audited-original.json). An internally coherent fixture cannot establish real source authenticity, native Db2/VSAM/IMS/IBM i/Fujitsu CDC, external financial effects, HA, performance or G2/G6 approval. [The 22-test vendor-native *metadata* intake](SOURCE-CAPTURE-INTAKE.md) remains a separate evidence claim.

## Vendor runtime contracts — 11 documented/discovery rows, 25 metadata tests

[Original metadata integrity run #41914291930](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41914291930), exact source/checkout `7dde2c7cff508206c2f154a4e55de798d4cff78c`, passed **25/25** conservative schema/mutation tests over 11 contract/discovery rows and ten dated vendor references. GitHub's original artifact `13365075026` reports SHA-256 `fb3ec79701bfc325fdf93e597b777f44dad5003e66f72c26be409c2d0e54c987`; the ZIP was **not independently downloaded/rehashed** for this record. [EN scoped audit](VENDOR-RUNTIME-CONTRACTS.md) · [ES](VENDOR-RUNTIME-CONTRACTS.es.md) · [original timestamped case excerpt](VENDOR-RUNTIME-PR97-ORIGINAL-CI-EXCERPT.log) · [machine-readable manifest](vendor-runtime-pr97-original-ci-summary.json). The earlier original [negative-test fixture failure #41914127029](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41914127029) remains **FAIL**, not retconned. IBM indexed/direct 403, Unisys technical full text, Fujitsu 2018 historical; no vendor-native workload, migration equivalence, mainframe performance, customer source data, or TODM G2/G6 signoff is proven.

## ATM late advice/UNKNOWN/reversal forensic gate — original 33 synthetic controls

[Original exact-head run #42024266243](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42024266243) exercised **33/33** pure-Python cases, zero unexpected errors, against a four-operation fictional authorization/device/posting/network trace. [Original EN scientific/evidence report](CHANNEL-ADVICE.md) · [ES report](CHANNEL-ADVICE.es.md) · [selected timestamped job log](CHANNEL-ADVICE-PR98-ORIGINAL-CI-EXCERPT.log) · [machine-readable original result](channel-advice-pr98-original-ci-summary.json).

The original run source/checkout was `291829f8cda34604f692a03dff6794f6cec0f51c`; GitHub reported the original ZIP as artifact `13412439030`, 2371 bytes, SHA-256 `4cc2ea7009d514e462cab8a173bc6fae2c5c36804ef7af49c79e9441151d0950`. **ZIP bytes were not independently downloaded/rehashed.** Synthetic checks recognize partial cash, unknown physical outcome, zero cash, message replay and denied stand-in; they **cannot** operate a physical ATM or bank core or authorize posting/reversal, and they do not prove ISO 8583/card network operation. TODM G2 INCONCLUSIVE/G6 BLOCK; #30 still open. Previous native .NET/two-PostgreSQL channel evidence is preserved separately.

## Channel per-hop failures — 40 original synthetic controls

**Original exact PR-head [Actions #42028436325](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42028436325): 40/40 Python adversarial checks PASS** over 7 logical ATM/switch/core fault histories, source/checkout `8bec46074a50daa5d08ecc174662e837cad8ab8c`. [EN original audit](CHANNEL-HOP-FAULTS.md) · [ES](CHANNEL-HOP-FAULTS.es.md) · [selected original timestamped CI lines](CHANNEL-HOP-PR99-ORIGINAL-CI-EXCERPT.log) · [machine-readable original-run record](channel-hop-pr99-original-ci-summary.json). GitHub published artifact `13415051431`, 2637 bytes, ZIP SHA-256 `3ac341c70ccf4a17db27a8218f299768ff64f7c782cedb5cebec62ed66ad2101`: **reported digest only**, original ZIP not independently rehashed. The first Book Markdown check failed MD012 in the ES/EN roadmaps, fixed on a later commit; the earlier failed run remains FAIL.

This oracle **does not physically interrupt a TCP link**, authenticate issuer/device journals, authorize bank stand-in or migrate a core writer. It complements rather than replaces native .NET/two-PostgreSQL and 33-case advice experiments. Every output explicitly blocks automatic money movement, writer cutover and production and keeps TODM G2 INCONCLUSIVE/G6 BLOCK. #30 stays open; no release or bank acceptance.
