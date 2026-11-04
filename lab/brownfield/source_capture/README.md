# Native-source CDC discovery intake — bank source proof is still missing

**English-only executable gate.** [Research EN](../../../docs/research/source-native-capture-assessment.en.md) · [Research ES](../../../docs/research/source-native-capture-assessment.es.md) · [Issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).

This is an **assessment/interview**, not a COBOL parser, IBM mainframe emulator, Db2/VSAM/IMS/IBM i/Fujitsu data connector, CDC pipeline, direct writer fence or customer acceptance.

The dated [capture catalog](capture_catalog.json) cites primary IBM documentation for six different platform/write-path families and explicitly leaves the Fujitsu/other branch **NOT_VERIFIED**. Each source is a **version-scoped documentation reference**; it does not prove installed software, product support on any bank estate, workload coverage or current licensing. Customers may have a mix of stores and online, batch, offline and privileged access in one estate.

## Synthetic snapshot/log continuity oracle (separate, offline)

**Original 26/26 synthetic CI PASS:** [run #41908404394](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41908404394), [EN exact-head audit](../../../evidence/runs/SOURCE-HANDOFF.md) / [ES](../../../evidence/runs/SOURCE-HANDOFF.es.md). The original ZIP was downloaded and SHA-256 independently rechecked; no actual vendor source has been tested.

The [source-neutral handoff protocol](../../../docs/research/source-capture-handoff.en.md) ([ES](../../../docs/research/source-capture-handoff.es.md)) compares an **independently declared synthetic source commit history** with an MVCC snapshot bookmark, captured tail and target replay. It is **not** a native vendor log reader. The 26 dedicated negative/positive cases reject missing/reordered events, expired retention, a mismatched snapshot cut, stale target, wrong source epoch and attempted banking self-approval.

```bash
python3 -m unittest discover -s lab/brownfield/source_capture -p 'test_handoff.py' -v
python3 lab/brownfield/source_capture/handoff.py \
  lab/brownfield/source_capture/handoff.example.json
# exit 0 = internal SYNTHETIC handoff consistency only
# exit 2 = REJECT; exit 3 = INVALID
```

The sample contains **four fictional accounts and five fictional committed transfers**. No customer data is read, no source evidence is authenticated and all outputs maintain G2 INCONCLUSIVE/G6 BLOCK. A wholly fabricated but internally coherent source/capture pair can PASS; use an independently attested bank-owned source oracle before assigning a broader claim.

## Run

```bash
python3 -m unittest discover -s lab/brownfield/source_capture -p 'test_*.py' -v
python3 lab/brownfield/source_capture/assess.py \
  lab/brownfield/source_capture/intake.example.json
# Exit 2 is REQUIRED: all seven source-family paths are UNKNOWN.
# Exit 3 is INVALID input; exit 0 means declaration shape ready for
# independent external review, NEVER a mainframe or banking PASS.
```

Use a **private** working copy of the intake when interviewing a bank; never commit customer configuration, account details, infrastructure credentials, personal information, logs or raw data to a public repository. The sample is intentionally unknown.

Each path has a typed applicability `UNKNOWN`, `IN_SCOPE`, or `OUT_OF_SCOPE`; if excluded it needs a **source-owner exclusion evidence pointer**, not an unsupported assumption. If active it needs an identified, versioned product and **generic plus platform-specific proof references**. A proof pointer is `{uri, sha256, claim}`; **the gate neither fetches nor authenticates the referenced bytes**, and a syntactically valid SHA-256 cannot prove authenticity, coverage or signoff. Unknown paths must contain no proof, named capture product or exclusion.

### Generic evidence required for each applicable path

The path-specific capture engine and actual DBA/operator owner must reconcile: (1) committed ordering and recoverable UOR, (2) the snapshot-to-log handoff, (3) bookmark restart/retention, (4) deduplication/gap detection, (5) online/batch/utility/load/offline completeness, (6) schema/CCSID/images, (7) privileged source writer fencing, (8) independent financial and external-effect reconciliation, and (9) adversarial recovery and independent signoff.

**Platform-specific questions** come from catalog keys. Examples:
- Db2 z/OS: check DCC-enabled source tables, CDC log consumers/IFCID, LOB/XML specifics, Db2 data sharing/log position, utilities and bulk loads;
- VSAM CICS: verify LOGREPLICATE, LOGSTREAMID, CICS region/resource/log tie-ups, RLS and load-mode path;
- VSAM batch non-RLS: verify CICS VR configuration and that every JCL direct/batch/load writer is actually captured;
- IMS online: DBD EXIT/DBDGEN, RECON and online/archive logs, source subsystem ordering;
- IMS DL/I batch: DBRC=Y, DFSFLGX0, permanent IEFRDER, batch-step availability/ordering latency;
- IBM i: STRJRNPF and record image options, journal receiver continuity, remote filters, commitment-control configuration;
- Fujitsu/other: exact installed OS/database family and dated primary support contract must be obtained **first**; no mechanism may be inferred by analogy.

These are **questions to test**, not assertions that a named system already implements the mechanisms.

## Interpret the statuses

| Status | Meaning | Business authority |
| --- | --- | --- |
| `INVALID` (exit 3) | Schema mismatch, unrecognized platform/extra field or attempted false PASS | None |
| `NOT_READY` (exit 2) | Source family, approvals, vendor constraints or evidence pointers still missing | None |
| `READY_FOR_INDEPENDENT_REVIEW` (exit 0) | **Only** all declared metadata/reference shapes are present; no bytes verified | None |

Even an **all-fake, syntactically complete** input can reach `READY_FOR_INDEPENDENT_REVIEW`; this is not evidence acceptance. Every output permanently has `nativeCaptureTestExecuted=false`, `evidenceBytesVerified=false`, `bankSourceWriterFenceProven=false`, `productionApproved=false`, **TODM G2 INCONCLUSIVE / G6 BLOCK**.

The exact source-side proof remains a different process: bank-approved documentation and safe access, native platform logs from each real online/batch/privileged writer, source-controlled cutover authority, verified bytes/retention, lineage, batch load/restart negative cases, physically independent recovery when relevant, Oracle Gates and owner approval. See [fencing acceptance](../../../docs/BROWNFIELD_SOURCE_FENCE.md). The earlier [W01 journal 22/22 PASS](../../../evidence/runs/W01-SOURCE-JOURNAL.md) is only a synthetic PostgreSQL technical baseline, **not proof of any native capture path**.
