# Editorial review and evidence register

**English** · [Español](EDITORIAL_REVIEW.es.md)

This document is for the **next editorial iteration**. It does not modify the already published [v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29), its attribution or its results. It turns criticism into verifiable hypotheses instead of repeating outdated assumptions.

## Verified status

| Claim | Status as of 2 November 2026 | Evidence and limitation |
|---|---|---|
| Repository and publications | Public | Stable v2026.10.29 and research pre-release v2026.10.31-rc1; PDFs freeze their tags, not current main. |
| Book and lab on main | CI executed | [Commit 279ca566](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/commit/279ca5662dd870c0f1bb7dab7d1474f346904df3): seven applicable workflows succeeded; Release deliberately skipped. |
| Published PDFs | Generated for their tags | Later brownfield changes are not automatically included; the next preview still needs generation and visual review. |
| E1 PostgreSQL/SQL Server | Partially verified | Synthetic parity, concurrency, deadlocks and negative controls executed; no production capacity, HA or mainframe equivalence. |
| E2 Orleans | Partially verified | Inter-silo recovery and process/network faults executed on one host; Asymmetric faults, sustained capacity and physical fault domains remain. |
| Brownfield C2/C3 | Executed slices | [C2 main #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630): 20 controls and both SQL oracles 10/10. No real incumbent fence or G2/G6 acceptance. |
| M1/M2 | Executed in local CI | Twenty durable M2 cases; no Azure benchmark, comparable TLS, WAN or distributed scale. |
| E3 and E4 | Designed, not executed as complete experiments | Prices, WAN models and agent examples do not satisfy their acceptance gates. |
| Portability and Illustrative listings | Reproduction/compilation pending | Linux CI does not prove every workstation or compile every fragment. |
| Full native-level English style and idiom | Specialist review pending | Automated synchronization validates structure, not translation or style. |

**Publication boundary:** PR #5 is merged. Stable and historical publications retain their original assets; the current manuscript includes later work.

## Quality gates

| Priority | Work | Exit condition | Status |
|---|---|---|---|
| P0 | Correct outdated claims on release, Podman and CI | Links to runs; distinguish Linux CI from cross-platform reproduction | Integrated; status reconciled in this review |
| P0 | Seven-chapter fast path without changing the manuscript | Working links, aligned ES/EN choices and preserved argument | Integrated; status reconciled in this review |
| P1 | Audit repetition of locks, transfers, equivalence and mandates | Exact chapter/passage overlap matrix, author-approved cuts | Pending |
| P1 | Check claims attributed to the author's published articles | Read primary passage, record scope and either support or correct each claim | Pending |
| P1 | Native-level English review (start with prologue and Part I) | Concrete editorial suggestions that preserve the author's voice | Pending |
| P2 | Complete E1 parity and SQL Server coverage | Preserve executed E1a/E1b/E1c evidence and specify outstanding overall gates; historical SQLite parity tracking [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) and SQL Server [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) | Partially executed; completion pending |
| P2 | Compile *Illustrative* examples | Per-example compiler, test, verdict and provenance; no promotion without execution | Pending |
| P2 | Non-CI reproduction | Linux, macOS and Windows/WSL records with pinned versions | Pending |

## Editorial standard: precision before a percentage

Do not impose an automatic 15–20% cut. Length alone does not prove redundancy. First document **which passages repeat the same proposition without introducing a new decision criterion**. Similar themes can legitimately recur across distinct invariants, architectural layers or experiments. No broad rewrite without the author's review and bilingual synchronization.

## Primary-source citation checks

- **[44], AHP.** The [original article](https://jmfloreszazo.com/agent-host-protocol-ahp-por-que-el-host-y-no-tu-editor-es-el-dueno-del-estado-de-la-sesion/) does support the claim that the host owns session state and clients are views. Chapter 8 uses that as an analogy; it must not be presented as proof of modernization record authority.
- **[45], Hosted Agents .NET/Python.** The [original article](https://jmfloreszazo.com/benchmark-dos-hosted-agents-mismo-foundry-net-10-lts-vs-python-3-12/) measures sequential latency under light load. It explicitly does **not** establish peak throughput or saturation; do not extrapolate to MIPS.
- **[1], From Leviathan to Autopilot** and **[41], governed harness**: match each book claim to the source passage, not merely its title or summary.
- Annex G mixes documentation, external research, opinion and lab results: assess conclusions against the actual class of evidence.

## Authorship and editorial responsibility

The author confirms having read the book. Remaining editorial work is about precision and quality, **not evidence that the author has not read it**. Authorship cannot be inferred merely from which tools were used during preparation. Statements about writing processes are for the author to decide, not for reviewers to insert by assumption.

**Do not change `CITATION.cff`, the edition identifier, attribution, licenses or release** in this branch.
