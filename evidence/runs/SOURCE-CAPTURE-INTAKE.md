# Source-native CDC owner intake — bounded original structural evidence

**4 November 2026.** [Español](SOURCE-CAPTURE-INTAKE.es.md) · [PR #95 merged](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/95) · [issue #58 OPEN](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)

## Exact result: metadata validation, not native source execution

The original [Source capture owner intake CI run #41898291348](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41898291348), original job `126813593665`, completed SUCCESS with **22/22 structural/adversarial Python tests** and no unexpected errors. The sample assessment returned the intended `NOT_READY` refusal, **7/7 source families UNKNOWN**, `nativeCaptureTestExecuted=false`, `evidenceBytesVerified=false`, `todmG2=INCONCLUSIVE`, `todmG6=BLOCK` and `productionApproved=false`.

- Exact **PR source head** at test: `e23d5a8dd071655b87e504de2dac255438a534d0`.
- Actual GitHub Actions **PR test-merge checkout**, separate from the source head: `172158b898475d0bf85613ffde8b373e6c9df255`. The log identifies its merged parent as source head `e23d5a...` into `2269d4af09fa4e86da1709bfe35a5d41be410c96`.
- Actual merge to main after CI: `18440bd2afc3b62c409fdf93ab2360eb1ba25978`. **Do not mislabel the test-merge result as an independent execution of that merge commit.**
- [Original timestamped test lines preserved](SOURCE-CAPTURE-PR95-ORIGINAL-CI-EXCERPT.log) in Git, with all 22 `ok`, `Ran 22 tests` and catalog/example refusal lines. This is a **selected log excerpt**, not the complete job text or a downloaded original ZIP.
- The original CI workflow **did not upload a source-capture artifact ZIP**. Do not claim independent ZIP checksum, raw vendor-log evidence or installed product execution.
- The primary IBM documentation rows in `lab/brownfield/source_capture/capture_catalog.json` were checked against search-indexed documentation excerpts. Some direct IBM Docs URLs returned HTTP 403; these access restrictions remain recorded, not silently upgraded to full-document reads.

## Observed controls and limitations

The unit suite checked the seven named capture paths for Db2 for z/OS, VSAM via CICS, batch VSAM non-RLS, IMS online, IMS DL/I batch, IBM i journals and unverified Fujitsu/other platforms; missing and duplicate paths; explicit source-owner exclusion evidence; capture product/version and per-platform proof claims; invalid pointer hashes/URLs; and false G2/G6/PASS assertions.

A **syntactically complete collection of fake evidence references** can intentionally produce `READY_FOR_INDEPENDENT_REVIEW`: this is a *metadata-shaped declaration*, not any verification of those bytes or an approval. The program never contacts a bank, vendor log, recovery journal, MQ queue or licensed CDC product. It also does not capture the business consequences of ATM cash, network settlement or the actual incumbent's privileged writes.

The original [W01 journal 22/22 real PostgreSQL technical proof](W01-SOURCE-JOURNAL.md) remains a separate synthetic experiment and cannot be transferred to native Db2/VSAM/IMS/IBM i evidence.

**Scientific disposition:** `STRUCTURAL_INTAKE_TESTS_PASS`; `NATIVE_CAPTURE_NOT_EXECUTED`; `BANK_SOURCE_FENCE_NOT_PROVEN`; `BUSINESS_APPROVAL_NOT_OBTAINED`. TODM **G2 INCONCLUSIVE, G6 BLOCK**. E2 remains `partially_verified`; #8 closed administratively, #32 completed for method, #58 OPEN, #53 frozen. No new release is authorized.

## Next genuine customer-side evidence

A named system owner must identify installed OS/DB/version and all write paths, reconcile online/batch/load/offline/privileged coverage, obtain a source-authoritative snapshot/log handoff and independent replay/retention proof, and execute negative scenarios on **actual native** logs with safe change approval. Independent reviewers must reconcile paired postings, external effects and source-side fencing before either G2/G6 can advance. The [source-fencing protocol](../../docs/BROWNFIELD_SOURCE_FENCE.md) remains the boundary.

