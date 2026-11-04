# Vendor-specific runtime contracts — original bounded metadata run

[Español](VENDOR-RUNTIME-CONTRACTS.es.md) · [PR #97](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/97) · [Source catalog](../../research/vendor-runtime-contracts/catalog.json) · [ES/EN research](../../docs/research/vendor-runtime-contracts.en.md)

**Evidence captured: 4 November 2026. The classification is METADATA_ONLY, never native-vendor verification.**

## Original executed evidence

- [Original GitHub Actions run #41914291930](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41914291930), job `126869737831`, exact source/check-out SHA `7dde2c7cff508206c2f154a4e55de798d4cff78c`.
- **25/25 catalog-integrity tests PASS** (one baseline and 24 hostile mutations), with no unexpected failure. The original runner checked a source corpus of **10 dated vendor references and 11 scoped records/discovery placeholders**. [Selected original timestamped log lines](VENDOR-RUNTIME-PR97-ORIGINAL-CI-EXCERPT.log) record the 25 named results.
- GitHub uploaded artifact ID `13365075026`, `vendor-runtime-contract-metadata-original-not-native`, 1847 bytes, GitHub-reported ZIP SHA-256 `fb3ec79701bfc325fdf93e597b777f44dad5003e66f72c26be409c2d0e54c987`, initial expiry 2 February 2027. **The ZIP bytes were not downloaded and independently rehashed for this record**; this hash is published metadata only. [Machine-readable original-run summary](vendor-runtime-pr97-original-ci-summary.json).
- **Prior failure preserved:** [original run #41914127029](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41914127029) had an incorrectly constructed *adversarial test*: an OS 2200 record linked a source from the same Unisys vendor, whereas the test expected a cross-vendor refusal. That original run remains **FAIL**, was corrected to actually cross IBM vs Unisys and rerun. It is not retroactively marked PASS.

## What passed and what did not

The schema rejects ungrounded vendor references, misleading historical sources, missing source/version, missing failure control or oracle, invented dates, unsupported/absent status inferred from unknown, and false `native_execution`, equivalence, production SLO or bank approval. The original metadata result records `PASS_METADATA_INTEGRITY_25_CASES`, `nativeExecution=false`, `parityVerified=false`, `productionApproved=false` and TODM `G2 INCONCLUSIVE / G6 BLOCK`.

This result is **not** a native IBM Z/z/OS, Db2 for z/OS, IBM i, ClearPath MCP, OS 2200, Fujitsu GS21, NEC or Bull GCOS test. It did not read customer programs, execute COBOL or log capture, validate actual installed versions, demonstrate operational parity or measure MIPS/vCPU, latency, RPO or RTO. IBM Docs were indexed but blocked on direct read with HTTP 403; the recorded Unisys pages were full-text, and the Fujitsu material is an **archived 2018 announcement**. Those access differences remain visible in the catalog.

The paired whole-book chapters 1 and 13 and the derived `book/es.md`/`book/en.md` editions are editorial outputs, not runtime evidence. This increment does not close #17, #18 or #28 (the broader 236-entry architecture scope remains), #58 (real source writer fencing), or frozen #53. It does not create a release or promote a bank gate.
