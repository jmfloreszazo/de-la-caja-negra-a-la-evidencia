# Final research closeout — 5 November 2026

**English** · [Español](FINAL_CLOSEOUT.es.md)

> **Publication closure is not scientific PASS or production approval.** This repository is closing a bounded, reproducible research/book edition at the author's direction. Unexecuted or incomplete acceptance campaigns are explicitly *excluded*, never silently marked successful.

## What is delivered

- A full bilingual manuscript (Spanish and English) with chapters, annexes, diagrams, architectural alternatives and paired Markdown/PDF editions.
- English-only executable examples and runbooks using GnuCOBOL, .NET 10, SQL and Podman; the author's position is **functional-first brownfield replacement**, not a mandatory parser or one-to-one source translation.
- Observed synthetic results for independent accounting oracles, PostgreSQL/SQL Server transactions, Orleans experiments, brownfield coexistence and bounded single-host TCP fault/recovery scenarios.
- Primary vendor-oriented research on IBM Z/z/OS, Db2, CICS, IMS, VSAM, IBM i, Unisys and historically documented Fujitsu capabilities, with explicit gaps for unverified platforms.
- A documented distinction among observed Golden Master outputs, independently approved functional requirements, TODM/oracle controls and a production release decision.

## Terminal experiment dispositions

| Experiment | Administrative disposition | Scientific evidence boundary | Explicitly not established |
| --- | --- | --- | --- |
| **E1** PostgreSQL, SQL Server and .NET 10 | **CLOSED — bounded implemented research** | Original CI validates named synthetic SQL locks, deadlocks, write skew, accounting invariants, crash/replay and limited concurrency/parity cases | Full mainframe-equivalent functionality, power-loss durability, physical HA, bank-approved rulebook or production throughput |
| **E2** Orleans/PostgreSQL | **CLOSED — bounded campaign, already closed under #8** | `partially_verified`; original single-host multi-process, ledger and selected partition/recovery/load evidence remains intact | Continuous natural recovery, separate physical failure domains, SQL HA or a global scientific PASS; [future X00–X08 protocol](E2_FULL_PASS_PROTOCOL.md) remains archival |
| **E3** Azure/on-prem/hybrid | **CLOSED — not executed as comparable system benchmark** | M1/M2 local transport/SQL smoke, hypothetical WAN model and dated Azure catalog entries are inputs only | Approved mainframe workload baseline, comparable open-loop TPS/p99, failure/DR and full TCO; **no MIPS-to-vCPU equivalence** |
| **E4** live agents and independent Oracle Gates | **CLOSED — not executed as E4 acceptance study** | Oracle Gate / mutation and governance patterns are demonstrated in deterministic synthetic lab slices | A controlled live-model agent campaign, comparative defect-detection study, model cost and independently accepted agent performance |

**Critical:** `evidence/claims.json` retains its original scientific statuses (`E1/E2: partially_verified`, `E3/E4: designed_not_executed`). Administrative closure does **not** change those machine-readable claims or fabricate runs. More complete work would require a separately authorized new study.

## Other book/lab scope frozen at publication

| Area | Included as research or bounded lab | Excluded from this closure |
| --- | --- | --- |
| Brownfield CAP-005/007, #58 | Durable .NET/PostgreSQL, synthetic legacy coexistence, shadow, rollback veto, controller admission and limited partition observation | A real bank-owned source writer fence, authenticated business/Golden Master policy, external financial effects, approval of TODM G2/G6 |
| Banking channels, #30 | Original single-host .NET/PostgreSQL TCP recovery with SQL oracles; H01/H02 external evidence intake/runbook | Actual multi-host hop campaign, certified ATM/switch/issuer/CICS/Db2, physical cash, ISO 8583 and delegated stand-in |
| OS/vendor/pattern research, #17/#18/#28 | Source-scoped catalog and semantic-replacement guidance | Exhaustive manufacturer matrices, installed native engines, full 236-behavior coverage and customer SME signoff |
| Lab/reproduction, #11/#15 | Existing preserved source, historical artifacts and tested CI entry points | Full native macOS/Windows reproducibility, every illustrative listing compiled in context, broad path/layout refactoring |

The related active research/maintenance issues can be closed as **not planned for this edition** after publication, without implying their original acceptance checklists have been met. Frozen future issues **#16 main protection** and **#53 clean rooms/confidential computing** retain their previous on-hold disposition and are explicitly not activated.

## Publication and verification criteria

1. The closing PR must pass its exact-head Premerge, Book, evidence-claims and PDF-preview checks, as applicable. No release is inferred from green PR checks.
2. Merge the closing revision into `main` with an exact SHA. Existing original experiments and release tags are immutable.
3. The dedicated final release workflow must build and attach **ES and EN PDFs** plus both full-book Markdown files under the new archival tag `v2026.11.05`. The first-edition **interior/cover identifier v2026.10.29 remains historical branding** in this archival research snapshot; the release tag identifies the **final repository research freeze**, not a fully redesigned second typographic edition.
4. Verify the actual GitHub Release and assets before reporting publication as complete. A CI PASS is not blanket editorial certification: native-English review, bibliographic completeness and all-page visual proof remain limited.
5. Only then close active edition trackers, using **not planned** where scope was deliberately excluded. Original evidence, failed hypotheses and external protocols remain published as the scientific boundary.

**Post-publication scope:** no further development is scheduled in this edition. Any resumed technical or bank-specific program must define a new version, workload contract, owner, sources, independent oracles, actual infrastructure and explicit business approval. The title's claim remains *evidence*, not mainframe parity.
