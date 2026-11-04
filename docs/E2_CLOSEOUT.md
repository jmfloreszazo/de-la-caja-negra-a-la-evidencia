# E2 Orleans — bounded-campaign closeout (4 November 2026)

**Disposition:** the repository's **hosted-CI E2 experiment campaign is closed at its deliberately bounded scope**. **Scientific acceptance remains PARTIALLY_VERIFIED.** This is **not** a claim that distributed Orleans capacity, natural recovery, physical high availability, or banking production readiness have passed. Close tracker [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) as **not planned within this campaign**, rather than as successful completion of its external acceptance criteria.

## Evidence preserved and accepted within the bounded scope

| Slice | Original evidence / verified observation | Acceptance boundary |
| --- | --- | --- |
| PostgreSQL ADO.NET membership, process death and authoritative transfer ledger | [Original run 41098437285](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41098437285); 2 active membership rows, secondary death, recovered surviving route, idempotent replay and independently checked 7/7 financial predicates | Two silo processes share one hosted runner and one database |
| In-flight SQL transaction and post-commit replay | [Original run 41102529778](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41102529778); real pre-commit termination and post-commit duplicate resolution with independent SQL oracle | Process crash, **not** storage power failure or distributed database HA |
| Directed packet-loss controls and ledger reconciliation | [C05/C06 report](../evidence/runs/E2-C05-C06-DIRECTIONAL.md); direction/PCAP evidence and 7/7 SQL invariants | Bounded controlled packet faults, **not** proof of global exclusive activation |
| Controlled activation and service observations | [C01 controlled fixture](../evidence/runs/E2-C01-CONTROLLED.md) and [directed account observations](../evidence/runs/E2-ACCOUNT-DIRECTED.md); **2 positive directed witnesses and 4 INCONCLUSIVE** are preserved | Natural placement and continuous unassisted recovery **not established** |
| Long partition rehearsal | [Audited long schedule](../evidence/runs/E2-LONG-PARTITION.md), [run 41607407356](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41607407356); two bounded cases after explicit silo recreation, 14 paired samples over about 66 seconds | The 120-second schedule included earlier secondary exit; **not 120 seconds of continuous dual-silo service**, automatic recovery or production RTO |
| Direct admission / load diagnostics | [B05 diagnostic](../evidence/runs/B05-DISPATCH-DIAGNOSTIC.md); 119,040 offered, 118,887 SQL commits and 153 cap-32 admission misses, 42 financial checks | No accepted sustained capacity knee, comparable Orleans scaling or production p99 |
| Observation integrity and negative outcomes | [Placement report](../evidence/runs/E2-PLACEMENT-OBSERVATION.md); original failed provider executions and zero-effect negatives retained | Failed/inconclusive attempts are never changed to PASS |

All original source identities, CI runs, artifact manifests and negative controls remain source evidence. These records are scoped synthetic experiments; **they do not observe a customer mainframe**.

## Unmet acceptance: deliberately NOT declared PASS

1. **Sustained capacity:** separate generator, silo and SQL hosts; reproducible load, external driver and comparable direct/Orleans p99, pool waits and hot keys.
2. **Natural lifecycle/recovery:** ordinary grain without artificial gates, verified simultaneous/lifecycle observations, controlled clock uncertainty, and recovery without operator-assisted silo recreation across longer partitions.
3. **Independent failure domains/durability:** distinct hosts/zones, replicated/failover SQL, host/zone failures and acknowledged-operation reconciliation.
4. **Customer contract/authorization:** approved business rules, baseline traces and deployment mandate.

The **exact prerequisites, hardware topology, source changes, mandatory experiments X00–X08, raw evidence schema and deterministic acceptance rules needed for a future global scientific PASS** are in [E2 Full PASS Protocol (English)](E2_FULL_PASS_PROTOCOL.md) / [Español](E2_FULL_PASS_PROTOCOL.es.md). The original engineering gaps are detailed in [EXTERNAL_VALIDATION.md](EXTERNAL_VALIDATION.md). These remain requirements **for any future stronger claim**, not work counted as finished. Historical STARTUP/placement causes remain unknown. TODM **G2 = INCONCLUSIVE** and **G6 = BLOCK**. The performance contract remains **UNCONFIGURED**; no banking deployment, release approval, or MIPS/vCPU equivalence follows from this closeout.

## Separate PR #89 — not E2 acceptance

[PR #89](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/89), merged into main as `1f2fbe6172b850a6758bc629c6d9f4ff26b4d0f4`, adds a **different** full synthetic walkthrough reproduction. Its [Linux Podman run 41814281042](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41814281042) reports PASS with an original artifact and host-side SQLite audit. macOS and Windows passed collector unit tests only; full native platform reproductions are not claimed. **This result does not upgrade E2 HA/capacity or Orleans placement.**

## Terminal administrative action

- The previously delivered E2 implementation/diagnostic PRs are integrated, and the archived observations remain immutable.
- [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) is closed **NOT_PLANNED** for external acceptance under this bounded campaign. It is **not closed as fully verified**.
- No live E2 execution gate is removed or weakened. The evidence claim state stays `partially_verified`; any future capacity, natural recovery, or physical HA acceptance needs a **new separately approved external campaign** with its own evidence and issue.
- Do not use the closed issue to imply those unexecuted claims passed.
- [Spanish closeout](E2_CLOSEOUT.es.md).
