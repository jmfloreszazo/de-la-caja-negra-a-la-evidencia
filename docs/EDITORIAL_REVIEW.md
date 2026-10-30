# Editorial review and evidence register

**English** · [Español](EDITORIAL_REVIEW.es.md)

This document is for the **next editorial iteration**. It does not modify the already published [v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29), its attribution or its results. It turns criticism into verifiable hypotheses instead of repeating outdated assumptions.

## Verified status

| Claim | Status as of 30 October 2026 | Evidence and limitation |
|---|---|---|
| Repository and release are accessible to authorized collaborators | Verified | The repository remains private; [release v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29) has the ES/EN PDF and Markdown editions. Public access has not been approved. |
| Book checks ran in CI | Verified | [Book PR #2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252122) passed Markdown, links, bilingual sync and diagrams |
| The laboratory ran on GitHub Actions | Verified | [Lab PR #2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252152) passed offline, native and Podman jobs on Linux runners |
| Both PDFs build | Verified | [Book PDF preview](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252098) and release assets |
| Portability on every Linux/macOS/Windows workstation | Awaiting independent reproduction | Hosted Linux CI does not prove every local setup |
| *Illustrative* listings compiled | Not evidenced | Inventory, compile and record results before changing their labels |
| E1a: PostgreSQL row locking and persisted accounting oracle | Executed in CI | [Run #40919268337](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337), synthetic Linux tests with real PostgreSQL, independent negative controls; not production parity. |
| E1b: .NET 10/Npgsql state and failure parity | Executed for a subset | [Run #40919773614](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) compares a tested subset against the Python/PostgreSQL candidate; full SQLite reference parity remains [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6). |
| E1 overall | Partially verified | E1c SQL Server [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) and full functional parity remain pending. No overall E1 PASS. |
| M1/M2 local transport tests | Executed in CI | [M1](../evidence/runs/M1.md) isolates RPC overhead; [M2](../evidence/runs/M2.md) tests 20 durable cases on one runner, not Azure, TLS, WAN or distributed scale. |
| E2: Orleans; E3: Azure/on-prem; E4: agents behind the oracle | Designed, not executed | Not equivalent to production guarantees or capacity measurements |
| Full native-level English style and idiom | Specialist review pending | `scripts/check.py` verifies structure, not language quality |

**Publication boundary:** the findings added in draft [PR #5](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/5) are not present in the published `v2026.10.29` release. Its release assets and version remain unchanged.

## Quality gates

| Priority | Work | Exit condition | Status |
|---|---|---|---|
| P0 | Correct outdated claims on release, Podman and CI | Links to runs; distinguish Linux CI from cross-platform reproduction | Done in this branch |
| P0 | Seven-chapter fast path without changing the manuscript | Working links, aligned ES/EN choices and preserved argument | Done in this branch |
| P1 | Audit repetition of locks, transfers, equivalence and mandates | Exact chapter/passage overlap matrix, author-approved cuts | Pending |
| P1 | Check claims attributed to the author's published articles | Read primary passage, record scope and either support or correct each claim | Pending |
| P1 | Native-level English review (start with prologue and Part I) | Concrete editorial suggestions that preserve the author's voice | Pending |
| P2 | Complete E1 parity and SQL Server coverage | Keep verified E1a/E1b subset; execute missing SQLite-equivalence checks [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) and SQL Server controls [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) | Partially executed; completion pending |
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
