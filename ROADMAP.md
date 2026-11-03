# Open roadmap — evidence-based checkpoint (3 November 2026)

**English** · [Español](ROADMAP.es.md)

This is the **repository development roadmap**, not a declaration of production bank readiness. The canonical claim statuses live in [evidence/claims.json](evidence/claims.json), and the engineering acceptance protocol is in [docs/EXPERIMENT_ROADMAP.md](docs/EXPERIMENT_ROADMAP.md). Observed, simulated, proposed and business-approved results must remain distinguishable. All code, source and lab READMEs are English-only; the book is maintained in ES/EN.

## Exact position in the active plan

**We are at execution-order step 4: E2, long partitions and recovery under #24.** Steps 1 and 3 continue with every increment: evidence and paired chapter 28. C2 retains its own acceptance gates; its synthetic tests do not establish a real bank writer fence.

| E2 substep | Current status | Gate before advancing |
| --- | --- | --- |
| C01: controlled fixture | Integrated, PR #72; #44 closed on that alternative | Historical cause is not claimed resolved |
| C05/C06: short cuts | Integrated, PR #73; PCAP/SQL audited | Do not extrapolate to long partitions or physical HA |
| Provider-specific diagnostics | Integrated, PR #76; real controls retain FAIL and zero effects | #74 remains open for natural placement investigation |
| Scheduled 120s cut and sampled recovery >=60s | **In progress, [PR #77](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/77)** | Two original cases PASS and audited; assisted recovery, secondary exited before 120s; final review before merge |
| Concurrent-activation behavior | Pending | Explicit observations and SQL oracle; do not assume global actor exclusivity |
| Sustained capacity and bottleneck | Pending, #25 | Comparable saturation and COMMIT/p99; existing pilots do not close this gate |
| Physical domains and HA | Pending | Execution/evidence on independent hosts and fault domains |

E2 remains **partially verified**. The long experiment has bounded audited evidence in PR #77, not yet merged; it does not establish automatic or continuous recovery. No percentage-complete estimates or completion dates are invented.

## Position now

| Workstream | Observed status | What still blocks completion |
| --- | --- | --- |
| Book, bilingual diagrams and CI | **Integrated**: 37 numbered chapters plus two companion chapters, 41 diagrams per language, bilingual chapter 28 coexistence discussion, reproducible PDF preview; latest premerge checks PASS | Editorial/source review, full illustrative listing coverage, cross-platform reproducibility; a preview is not a release |
| E1 PostgreSQL and SQL Server | **Partially verified**: real disposable SQL CI and independent oracles, .NET 10 parity slices, concurrency and negative cases | Full E1 business scope, power-loss/HA, customer-specific contract, production load |
| E2 Orleans | **Partially verified, actually executed**: one-host Podman multi-process/multi-silo slices, PostgreSQL membership, durable ledger checks and selected failures and load; see [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) | concurrent-activation observations/long-partition recovery, physical hosts/HA and sustained capacity [#25](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/25) |
| CAP-007/005 brownfield replacement | **Synthetic slices CI-verified and merged**: SQL writer epoch, .NET 10 durable transactions, black-box legacy adapter, two distinct PostgreSQL containers/stores, shadow, reconciliation and rollback veto. [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) | In-flight controller partitions and remaining journal recovery [#64](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/64), true incumbent-side writer fence, customer policy/mandates/Golden Master, TODM G2/G6 approval |
| Business-capability decomposition | **Synthetic inventory**: 30 capability hypotheses in 12 domains, functional-first rewrite; [#32](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/32) | Real authorized traces, owner-approved policies, target domains and independent acceptance; no mandatory COBOL parser and no 1:1 rewrite |
| E3 on-prem/Azure/hybrid | **Designed, not capacity-verified**: M1/M2 transport smoke, dated Azure price references and WAN model are inputs, not E3 PASS; [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9), [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) | Approved workload, open-loop saturation/commits/p99, failure domains, WAN, fair TLS gRPC/REST and dated comparable end-to-end TCO |
| E4 agent-based modernization | **Designed, not executed/accepted as E4**; [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) | Bounded agent write authority, reproducible proposal/evaluation, mutation-qualified Oracle Gates, independent review and approval |
| Mainframe OS, channels and architecture research | **In progress**: [#17](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/17), [#18](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/18), [#28](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/28), [#29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/29), [#30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30) | Vendor-backed claim comparison, OS/I-O and Db2/CICS/IMS semantics, ATM/mobile/web/branch, batch, offline queues and decomissioning patterns |
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

1. Reconcile the ES/EN book and documentation against evidence; preserve original SHAs and outcomes.
2. Complete C2 #64: in-flight partitions, lock loss and response windows; business acceptance and real source fence remain under #58/#32.
3. Update chapter 28 with contract, implementation, failure, correction, evidence and limits.
4. Complete bounded E2 #8/#24/#25 gates: concurrent-activation observations/long-partition recovery, load repetitions, bottleneck diagnosis and physical fault domains.
5. Prepare the next-edition preview: English review, citations, overlap, listings and ES/EN visual QA; publish only after the authorized editorial cut.
6. Execute E3 #9/#12 with comparable workload, infrastructure, WAN and TCO; then E4 #10.

**Frozen:** [#53](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/53) confidential computing/clean-room research is postponed by explicit decision. Do not include it in the active execution sequence without renewed instruction. Branch protection [#16](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/16) is also deferred but remains open.

## Publication boundary

The published first edition is [`v2026.10.29`](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29); the [`v2026.10.31-rc1` research pre-release](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.31-rc1) is a separate **published pre-release**, not the latest stable edition. Subsequent main merges and green PDF preview jobs do **not** publish another release automatically. Release only by an explicitly authorized release action and its controlled workflow.

**Evidence rule:** do not promote an entire phase from a successful subset. Preserve exact source/checkout SHA, run ID, container digest, negative original observations and provenance for every supported claim. No production or bank approval is inferred from CI.

C04 now has [bounded original evidence](evidence/runs/E2-C04-GATEWAY.md): fresh-client fallback, dual cut and 7/7 reconciliation. It neither closes overall E2 nor explains the historical C01 failure.

C01 has a [controlled alternative verified in three jobs](evidence/runs/E2-C01-CONTROLLED.md). The original failure retains its classification and its cause remains unproven; no placement-policy fix is claimed.

C05/C06 now have [two bounded directional packet-loss observations](evidence/runs/E2-C05-C06-DIRECTIONAL.md), including original PCAPs, SQL reconciliation and measured first acknowledgements without restarts. Exclusive activation, long partitions and sustained stable recovery remain open.

Loopback ADO.NET dual-host placement failed separately in broad validation; [#74](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/74) tracks that unresolved precondition. Its original ZIP/log remain preserved alongside C05/C06 evidence.

Issue #74 observation persistence now has [two real induced controls](evidence/runs/E2-PLACEMENT-OBSERVATION.md): provider-specific failed attempts retain their own maps/logs without borrowing earlier PASS results. Natural placement concentration remains unresolved.

The [audited long experiment](evidence/runs/E2-LONG-PARTITION.md) retains two initial failures and two corrected cases: 120s schedule, earlier secondary exit, assisted recovery and 14 pairs across about 66s. It does not establish continuous service or physical HA.
