# Open roadmap — evidence-based checkpoint (4 November 2026)

**English** · [Español](ROADMAP.es.md)

This is the **repository development roadmap**, not a declaration of production bank readiness. The canonical claim statuses live in [evidence/claims.json](evidence/claims.json), and the engineering acceptance protocol is in [docs/EXPERIMENT_ROADMAP.md](docs/EXPERIMENT_ROADMAP.md). Observed, simulated, proposed and business-approved results must remain distinguishable. All code, source and lab READMEs are English-only; the book is maintained in ES/EN.

## Exact position in the active plan

**Increments #83–#87 are integrated: editorial listings, channels, platform-contract seed, source-platform interview and directional controller-stream observations.** The next bounded editorial slice, #88, addresses EBCDIC/CCSID field boundaries. Remaining platform/channel coverage and owner-approved functional discovery stay open; external capacity/HA validation does not block the book.

| E2 substep | Current status | Remaining claim validation (non-blocking for integration) |
| --- | --- | --- |
| C01: controlled fixture | Integrated, PR #72; #44 closed on that alternative | Historical cause is not claimed resolved |
| C05/C06: short cuts | Integrated, PR #73; PCAP/SQL audited | Do not extrapolate to long partitions or physical HA |
| Provider-specific diagnostics | Integrated, PR #76; real controls retain FAIL and zero effects | Natural placement investigation is consolidated in external backlog #8 |
| Scheduled 120s cut and sampled recovery >=60s | **Bounded verification, [PR #77](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/77)** | Two original cases PASS and audited; next: concurrent activations; not continuous recovery |
| Concurrent-activation behavior | [Directed trial and stderr repeat](evidence/runs/E2-ACCOUNT-DIRECTED.md), PR #80: 2 positive envelope witnesses / 4 INCONCLUSIVE; membership fatal path observed | Repeatability and natural lifecycle/partition acceptance remain open; capacity #25 can proceed independently |
| Sustained capacity and bottleneck | Three-cohort direct admission diagnostic integrated with PR #81; external #25 follow-up | Comparable saturation and COMMIT/p99; existing pilots do not close this gate |
| Physical domains and HA | Pending | Execution/evidence on independent hosts and fault domains |

E2's **bounded hosted-CI campaign is administratively closed**, while its scientific claim remains **partially verified**. A future technical PASS would require the separate [distributed E2 acceptance protocol](docs/E2_FULL_PASS_PROTOCOL.md) (X00–X08, physical fault domains, SQL failover and independent audit), **not active E2 work**. [E2 closeout and excluded acceptance](docs/E2_CLOSEOUT.md) records the retained results, missing distributed validation and the closure of #8 as NOT_PLANNED rather than PASS. The long experiment in PR #77 does not establish automatic or continuous recovery.

## Position now

| Workstream | Observed status | Remaining work / claim acceptance |
| --- | --- | --- |
| Book, bilingual diagrams and CI | **Integrated**: 37 numbered chapters, chapter 25 bis and two companion chapters, 47 diagrams per language, bilingual chapter 28 coexistence discussion, reproducible PDF preview; latest premerge checks PASS | Editorial/source review, full illustrative listing coverage, cross-platform reproducibility; a preview is not a release |
| E1 PostgreSQL and SQL Server | **Partially verified**: real disposable SQL CI and independent oracles, .NET 10 parity slices, concurrency and negative cases | Full E1 business scope, power-loss/HA, customer-specific contract, production load |
| E2 Orleans | **Bounded campaign CLOSED; scientific status PARTIALLY_VERIFIED**: one-host Podman multi-process/multi-silo slices, PostgreSQL membership, durable ledger checks and selected faults and load; [closeout](docs/E2_CLOSEOUT.md) | Natural activation/recovery, physical hosts/HA and sustained capacity remain **unverified and excluded**, not PASS; #8 closed NOT_PLANNED |
| CAP-007/005 brownfield replacement | **Synthetic slices CI-verified and merged**: SQL writer epoch, .NET 10 durable transactions, black-box legacy adapter, two distinct PostgreSQL containers/stores, shadow, reconciliation and rollback veto. [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) | Further controller partition/timing windows under #58, beyond the four #87 application-stream cases, true incumbent-side writer fence, customer policy/mandates/Golden Master, TODM G2/G6 approval |
| Business-capability decomposition | **Synthetic inventory**: 30 capability hypotheses in 12 domains, functional-first rewrite; [#32](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/32) | Real authorized traces, owner-approved policies, target domains and independent acceptance; no mandatory COBOL parser and no 1:1 rewrite |
| E3 on-prem/Azure/hybrid | **Designed, not capacity-verified**: M1/M2 transport smoke, dated Azure price references and WAN model are inputs, not E3 PASS; [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9), [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) | Approved workload, open-loop saturation/commits/p99, failure domains, WAN, fair TLS gRPC/REST and dated comparable end-to-end TCO |
| E4 agent-based modernization | **Designed, not executed/accepted as E4**; [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) | Bounded agent write authority, reproducible proposal/evaluation, mutation-qualified Oracle Gates, independent review and approval |
| Mainframe OS, channels and architecture research | **In progress**: [#17](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/17), [#18](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/18), [#28](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/28), [#30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30) | Vendor-backed claim comparison, OS/I-O and Db2/CICS/IMS semantics, ATM/mobile/web/branch, batch, offline queues and decomissioning patterns |
| Platform maintenance | **Open**: lab refactor [#15](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/15), main ruleset [#16](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/16) (explicitly deferred), OS reproduction [#11](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/11) | Preserve checks, links, raw evidence and original source identity before changing layout/protection |

## Completed incremental sequence

- [PR #59](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/59): twelve-scenario brownfield evidence gap inventory; synthetic tests and business approval remain separate.
- [PR #60](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/60): in-memory fail-closed cutover rehearsal. **Not** a durable transaction or external legacy fence.
- [PR #61](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/61) and [#62](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/62): SQL-persistent .NET 10/Npgsql CAP-007/005, actual process kill and lost response; checked original merged-main source identity.
- [PR #63](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/63): black-box simulated legacy in a distinct PostgreSQL container, independently reconciled with the candidate; read-only shadow and failed rollback after candidate-origin decisions; chapter 28 updated in both languages. The **exact integrated main SHA** is `d04623e8c276bedda9918e87a09fa0c3f9da1f6a`; original [two-store main CI #41340310748](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41340310748) PASS. Both ledger oracles returned 10/10; the legacy and candidate ended with 8 and 10 recorded decisions respectively. That divergence appropriately **blocked** rollback.
- The original [ES/EN evidence pair](evidence/runs/BROWNFIELD-TWO-STORE.md) / [Spanish](evidence/runs/BROWNFIELD-TWO-STORE.es.md) records the first PR check-out provenance mismatch and the corrected exact-SHA rerun; keep the negative history.

All of these are **synthetic engineering results**; no real bank behavior was observed and TODM G2 remains INCONCLUSIVE and G6 BLOCK. Physical host separation is not established by two Podman containers on one runner.

- PR #66/#68/#69: durable journal, capability gateway and persisted enrollment. On `279ca566`, [C2 main #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630) passed 20 controls and both SQL oracles 10/10. The [original 19-control run](evidence/runs/BROWNFIELD-C2-RECOVERY.md) retains its original coverage. Seven applicable workflows passed on that main; Release skipped.

## Next execution order (not dates or percentage-complete estimates)

**New bounded #30 block:** [ATM↔switch↔core hop failures](docs/research/channel-hop-failures.en.md) ([ES](docs/research/channel-hop-failures.es.md)): seven fictional event traces and **40/40 Python controls passed in CI** ([original audit](evidence/runs/CHANNEL-HOP-FAULTS.md)) for undelivered instructions, COMMIT with lost ACK, UNKNOWN device cash, stale old-owner replies and denied stand-in. **No actual TCP partitions or bank approval**; it supplements the earlier native SQL and 33-case advice experiments. #30 stays open for real transport fault injection and wider channel coverage.

**Channels #30 verified bounded increment:** the [late-advice forensic oracle](docs/research/channel-late-advice.en.md) ([ES](docs/research/channel-late-advice.es.md)) passed **33/33 offline synthetic controls** ([original audit](evidence/runs/CHANNEL-ADVICE.md)). It does not reclassify the ten earlier native SQL cases or establish certified ISO 8583, real cash, financial reversals or delegated stand-in approval. #30 remains open for its larger scope.

1. Strengthen platform contracts and manufacturer-aware patterns in #17/#18/#28. **New bounded increment:** [EN 11-contract/discovery matrix](docs/research/vendor-runtime-contracts.en.md) ([ES](docs/research/vendor-runtime-contracts.es.md)), ten IBM/Unisys/Fujitsu references, and 25 catalog-integrity controls; Chapters 1/13 expanded in both languages. Full vendor coverage, architecture figures and native source tests remain open. Metadata checks do not grant bank acceptance.
2. The [snapshot-to-journal handoff oracle](docs/research/source-capture-handoff.en.md) ([ES](docs/research/source-capture-handoff.es.md)) adds **26/26 exact-head CI verified** offline synthetic consistency controls ([original audit](evidence/runs/SOURCE-HANDOFF.md)) with no native source execution or bank approval. The [source-native CDC assessment](docs/research/source-native-capture-assessment.en.md) ([ES](docs/research/source-native-capture-assessment.es.md)) adds a fail-closed 7-family discovery intake and 22 adverse **metadata** checks for IBM Db2/VSAM/IMS/IBM i and unknown other vendors. It does not run or certify native vendor CDC. The [synthetic source-owned journal follow-up](docs/research/w01-source-journal.en.md) ([ES](docs/research/w01-source-journal.es.md)) **passed 22/22 real PostgreSQL tests on the exact PR SHA** ([original independently hashed artifact audit](evidence/runs/W01-SOURCE-JOURNAL.md)); it covers bounded 16-account source sequencing/catch-up and transactional cursor, **not** real CDC, physical HA or business approval. Apply the completed research/method deliverable [#32](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/32) to the still-open **#58 source-side acceptance** work; extraction waves and owner-approved behavior must be proven against real customer evidence. The [W01 source-reader permission follow-up](docs/research/w01-reader-identity.en.md) ([ES](docs/research/w01-reader-identity.es.md)) now has **20/20 original PostgreSQL tests PASS** ([permanent audit](evidence/runs/W01-READER.md)) for a SQL-enforced non-writing reader, without implying real incumbent fencing. The [W01 executable PostgreSQL read-projection follow-up](docs/research/w01-projection.en.md) ([ES](docs/research/w01-projection.es.md)) **passed 16/16 exact-PR-head real SQL controls** ([permanent evidence](evidence/runs/W01-PROJECTION.md)); it adds bounded snapshot/watermark/fail-closed fallback without claiming CDC, linearizability, approved funds or production performance. New [ES](docs/research/mainframe-extraction-waves.es.md) / [EN](docs/research/mainframe-extraction-waves.en.md) synthetic wave screens contrast read-model/ACL candidates with rejected atomic-ledger and batch cuts; structural candidate does not mean business authorization. The [source-enforced authority acceptance protocol](docs/BROWNFIELD_SOURCE_FENCE.md) adds a structural fail-closed inventory and 12 future negative scenarios; it is **not** a real source fence, approved Golden Master or bank cutover PASS.
3. Complete remaining channel #30 scenarios: unavailable core, late messages, per-hop faults, stand-in and route cutover.
4. Finish editorial/reproduction #11: full idiom/bibliography/overlap review, remaining listings, EBCDIC and real OS reproduction.
5. Reorganize laboratory entry/layout #15 while preserving protected paths and original evidence.
6. Execute agent-versus-independent-oracle E4 #10 within a declared write scope.
7. E2 #8 is closed NOT_PLANNED for its unexecuted external campaign; preserve its [scientific limitations](docs/E2_CLOSEOUT.md). Keep E3 #9 and its WAN/TCO validation separately open; no physical HA or capacity acceptance is inferred.

**Frozen:** [#53](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/53) confidential computing/clean-room research is postponed by explicit decision. Do not include it in the active execution sequence without renewed instruction. Branch protection [#16](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/16) is also deferred but remains open.

## Publication boundary

The published first edition is [`v2026.10.29`](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29); the [`v2026.10.31-rc1` research pre-release](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.31-rc1) is a separate **published pre-release**, not the latest stable edition. Subsequent main merges and green PDF preview jobs do **not** publish another release automatically. Release only by an explicitly authorized release action and its controlled workflow.

**Evidence rule:** do not promote an entire phase from a successful subset. Preserve exact source/checkout SHA, run ID, container digest, negative original observations and provenance for every supported claim. No production or bank approval is inferred from CI.

C04 now has [bounded original evidence](evidence/runs/E2-C04-GATEWAY.md): fresh-client fallback, dual cut and 7/7 reconciliation. It neither closes overall E2 nor explains the historical C01 failure.

C01 has a [controlled alternative verified in three jobs](evidence/runs/E2-C01-CONTROLLED.md). The original failure retains its classification and its cause remains unproven; no placement-policy fix is claimed.

C05/C06 now have [two bounded directional packet-loss observations](evidence/runs/E2-C05-C06-DIRECTIONAL.md), including original PCAPs, SQL reconciliation and measured first acknowledgements without restarts. The later long-schedule evidence is documented separately; these short cuts do not retrospectively extend their scope.

Loopback ADO.NET dual-host placement failed separately in broad validation; [#74](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/74) tracks that unresolved precondition. Its original ZIP/log remain preserved alongside C05/C06 evidence.

Issue #74 observation persistence now has [two real induced controls](evidence/runs/E2-PLACEMENT-OBSERVATION.md): provider-specific failed attempts retain their own maps/logs without borrowing earlier PASS results. Natural placement concentration remains unresolved.

The [audited long experiment](evidence/runs/E2-LONG-PARTITION.md) retains two initial failures and two corrected cases: 120s schedule, earlier secondary exit, assisted recovery and 14 pairs across about 66s. It does not establish continuous service or physical HA.

B05 #25 now has a [three-cohort direct admission diagnostic](evidence/runs/B05-DISPATCH-DIAGNOSTIC.md): 119,040 offers, 118,887 SQL commits, 153 exact cap-32 admission misses and no misses at cap 128, with 42 financial invariant checks. This does not establish backend saturation, Orleans scaling or the historical warmup cause; sustained capacity and bottleneck attribution remain open.

The external-validation protocol records what a single-runner fixture cannot establish, what remains merely untested, and the host/clock/driver/telemetry changes needed for stronger claims. E2 stays partially verified while editorial work proceeds independently. No release is authorized by this integration decision.

## Consolidated closeout — 3 November 2026

See the [branch/issue closeout and ordered remaining work](docs/PROJECT_CLOSEOUT.md): nine delivered/overlapping trackers closed; remaining E2 validation is consolidated in #8, E3 in #9, brownfield in #58 and channels in #30. Historical #24/#25/#74/#64/#12 references are provenance, not additional active work queues. #16/#53 remain frozen. The cleanup manifest preserves all reviewed branch tips and archives non-ancestor histories before any ref removal.

Editorial checkpoint PR #83: 17 bilingual code/config drifts corrected; all 32 listings inventoried, 58 printed COBOL cases plus bounded rounding/COMP-3 checks passed with archived original provenance. PDF listing/caption pagination and gray-series captions corrected; 10 pages visually sampled. See the [editorial record](docs/EDITORIAL_CHECKPOINT_2026-11-03.md). #11 remains open for full contextual listing, EBCDIC and platform reproduction; this is not a release or full native-English certification.

Channel increment #30: paired companion chapter, six diagrams per edition, ten native synthetic cases and two rejected oracle mutations. Original failures, physical-device assumptions and remaining network/stand-in/cutover work are recorded in the [channel checkpoint](docs/CHANNELS_CHECKPOINT_2026-11-03.md).

Platform-contract seed: ten documented rows, three platform contexts, four unverified discovery families and six catalog-integrity mutation controls. Native platform execution and migration equivalence remain unverified; see the [scope ADR](docs/PLATFORM_CONTRACTS_ADR.md).

Brownfield #58 now has a bounded directional controller-stream observation: four native SQL cases and two rejected observation mutants, with an explicit recovery reset. [Original evidence](evidence/runs/BROWNFIELD-CONTROLLER-PARTITION.md). Platform catalog coverage remains partial; real source fencing and owner approval remain open.

Editorial #11: bounded EBCDIC/CCSID kata with 36 checks per hosted OS and four rejected result transformations; original Linux/macOS/Windows artifacts and exact checkout-line-ending audit retained. This does not establish full Podman/WSL2 portability or native host conversion. See the [checkpoint](docs/EBCDIC_CHECKPOINT_2026-11-04.md).
