# Platform contracts: placement and evidence scope

[Español](PLATFORM_CONTRACTS_ADR.es.md). Tracks #17/#18/#28; this bounded increment does not close those issues.

## Decision

Expand existing Chapter 1 with platform-layer attribution, a proposed end-to-end observation trace, read/write assessment designs and an operator/DBA questionnaire. Expand Chapter 13 with three platform contexts and pattern-selection decisions. Keep capacity/pricing/WAN in Chapter 25 bis, detailed channel/device behavior in its companion and the 100 risks in Annex E. Link rather than duplicate those treatments. Add primary references [51]–[59] and an English structured catalog under `research/platform-contracts/`.

This avoids another chapter that would repeat the platform/capacity introduction. Both editions have equivalent sections, tables, references and navigation links. The number of numbered/companion chapters and the 47 diagrams per edition do not change. Generated editions are rebuilt; previews are checked without changing the published version or release.

## Evidence boundary

Ten rows distinguish documented behavior from native execution and verified migration. IBM material accessed through search indexing is marked accordingly, including a direct-reader HTTP 403. MCP/ePortal pages were read directly. Publication dates remain null when not supplied; version scope does not establish current support, availability or installed configuration. Sources are paraphrased, not copied as manuals.

The schema validator executes six negative catalog mutations. It checks attribution, version/source metadata, missing failure/oracle fields and evidence inflation. These tests do not execute or emulate IBM Z, z/OS, Db2 for z/OS, MCP or OS 2200; no native source-target differential result or production approval is claimed. Example workload counts are preregisterable designs, not observed rates or service levels.

## Remaining parent scope

Issue #17 retains deeper execution/memory/I/O/Db2/dataset/security/operations research, the requested paired architecture diagrams, actual measurements and SME review. #18 retains complete manufacturer/subsystem coverage, runnable semantic-gap controls and installation-specific evidence. #28 retains its 236 entries, fifteen category matrices, diagrams and runnable batch/offline/CDC/cross-border worked examples. Discovery rows remain NOT_VERIFIED. Unknown customer data and external hardware tests are documented follow-ups; they do not block integrating this bounded research.

The roadmap now reflects #83/#84 and 47 figures, and places platform contracts before the remaining decomposition/channel/editorial/refactor/agent work. #16/#53 stay frozen.

## Original CI observation

[Run 41721242997](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41721242997) passed all six catalog-integrity controls. The [original ZIP](../evidence/platform-contracts/catalog-integrity-original.zip) and [provenance](../evidence/platform-contracts/provenance.json) retain source head `9f6d20267e137ff8de3c1559e8c2dbdc433215fa` and PR test checkout `32a2956826ffb0ec1c0e4f0629af5f444722570c` separately. The temporary commit object is archived so the audit does not depend on preserving an ephemeral GitHub ref. It checks object identity, parentage, identical trees and three historical source hashes. The result remains metadata-only and does not validate native vendor behavior.

## Bounded visual review

The [PDF from run 41722105250](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41722105250) has 160 ES pages and 156 EN pages, with 47 diagrams plus cover per edition. Ten pages covering the expanded material were visually reviewed. The [record](../evidence/platform-contracts/pdf-review.json) retains ZIP/PDF SHA-256 identities, one hundred render inputs and two samples. PR test checkout `5f1e96272c25048db9cf74fe48f19bafafffea81` and source head `22cd0f3d650623cdcbe6b59127be0725fa409498` have identical trees. Citation/blank-line formatting found by the initial lint was corrected; this does not certify full-book editorial quality or native platform execution.
