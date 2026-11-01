# Open roadmap

**English** · [Español](ROADMAP.es.md)

Work the book leaves open and the community can move forward. Each line shows its label. Issues [#6–#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues) remain open and have no milestone assigned. Preparing a future public edition requires the author's explicit review and authorization; this document does not set a publication date.

## Validate what could not be validated

| Task | Why it matters | Label |
|---|---|---|
| Build the Podman image on Linux, macOS and Windows and share the report | CI validates the recipe; real machines are what counts | `reproduction`, `good first issue` |
| Reproduce the full lab beyond hosted Linux CI and publish conditions/report | [Offline/native/Podman CI](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252152) already passed; independent cross-platform reproductions remain | `reproduction` |
| Compile the *Illustrative* listings in a sample project and promote those that pass to *Verified* | Today they are reasoning fragments; some deserve to be code | `lab`, `good first issue` |

## Experiments: observed evidence and outstanding gates

The overall protocol is in [`lab/docs/EXPERIMENT_PROTOCOL.md`](lab/docs/EXPERIMENT_PROTOCOL.md), with detailed gates in [`docs/EXPERIMENT_ROADMAP.md`](docs/EXPERIMENT_ROADMAP.md). [PR #5](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/5) is merged. Later evidence must cite its exact original run and source SHA; merging a PR does not retroactively change the published `v2026.10.29` edition.

| Phase | Verified state and limits | Tracking |
|---|---|---|
| E1a · PostgreSQL 16 under Podman | Executed in CI: deadlocks, isolation and persisted oracle; not a banking-capacity or complete-E1 claim. | [Evidence](evidence/runs/README.md) |
| E1b · .NET 10/Npgsql | Initial 7-control and extended [10-control E1b CI run](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) passed; [16-case direct SQLite/PostgreSQL parity + lock release](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923) also passed. The [960-transfer 1/2/4/8 uniform/hot reference matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329) passed for PostgreSQL; SQL Server E1c subsequently passed its own [960-transfer synthetic matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) and stronger [persistent-worker matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791). Both remain synthetic, not cross-engine throughput/mainframe benchmarks. | [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) |
| E1c · SQL Server | [Executed SQL Server 2022 CI](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41040632819): 16 reference cases, real 1205 deadlock retry, bounded 1222 timeouts, SNAPSHOT negative and SERIALIZABLE defense, independent oracle. Also passed the [960-transfer eight-case SQL Server functional matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) with all four persisted tables matching and seven independent invariants passing.  The [persistent .NET worker follow-up CI #41043087791](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791) independently repeated all eight cases with 960 committed operations and oracle PASS. Production failures, failover and cross-engine throughput remain untested. | [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) |
| M1 · non-durable gRPC/REST | Executed localhost microbenchmark; neither banking transaction nor WAN benchmark. | [Report](evidence/runs/M1.md) · [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) |
| M2 · PostgreSQL-backed gRPC/REST | Twenty durable cases executed on one runner with one shared database; no distributed-scale claim. | [Report](evidence/runs/M2.md) · [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) |
| E2 · Orleans with durable ledger | **Partially executed in original CI**: PostgreSQL membership, SIGKILL, network partitions and bounded synthetic open-loop pilots. Comparable sustained capacity, remaining F10 cases, independent physical hosts and full E2 acceptance are missing. C04 remains draft without its own CI. | [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) · [#24](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/24) · [#25](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/25) |
| E3 · Azure, on-premises and hybrid | Designed, not executed. Dated reference prices and illustrative models exist, but no approved comparative benchmark. | [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9) · [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) |
| E4 · Agents behind Oracle Gates | Designed, not executed. | [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) |

**Completion rule:** E1 becomes verified only after full functional parity and outstanding gates; E2–E4 require independent oracles, negative controls and reproducible evidence. Green CI checks do not authorize a release.

## Priority: CAP-007/CAP-005 brownfield modernization

This starts from an existing COBOL estate and business contracts. It is neither
greenfield nor a 1:1 syntax translation. PRs #59–#63 delivered a persistent
.NET 10/PostgreSQL candidate, two-store SQL reconciliation, non-posting shadow
and synthetic cutover/rollback. [Issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)
remains open: no real mainframe-side writer fence has been demonstrated.

[PR #66, C2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/66)
adds a third disposable PostgreSQL admission/UNKNOWN journal, real process
crashes, independent SQL recovery and an opt-in cooperative adapter fence.
Its original opt-in bypass and non-atomic authority updates remain historical
limitations of that exact source SHA. The [C2 follow-up](lab/brownfield/journal/README.md)
adds SQL-persisted adapter enrollment, a durable traffic freeze and exact-intent
forward recovery with external SIGKILL controls. It requires its own original
CI evidence; it is not atomic cross-database COMMIT or real incumbent fencing.
TODM G2=INCONCLUSIVE and G6=BLOCK; this does not create another release.

Next: complete controller-partition and real source-fence acceptance under
[#64](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/64),
finish E2, benchmark E3 across Azure/on-premises/hybrid using horizontal-first
scale, internal gRPC and dated TCO, then E4 with agents behind Oracle Gates.
Clean-room/confidential-computing [#53](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/53)
remains **frozen for a future version**.

## Lab: next katas

- Turn the COMP-3 codec of chapter 15 into a module with its test vectors.
- Add an EBCDIC adapter with an explicit CCSID and ordering cases.
- Extend the contract with negative amounts and a matrix of compiler options.
- Port the accounting oracle to .NET to have two independent verifiers.

## Book

- Keep the Spanish and English editions in sync (`scripts/check.py` enforces it), and welcome other languages with the same structure.
- Expand the glossary and the risk catalog (R101 onwards) with real evidence.
- Real anonymized cases, with explicit permission and no identifiable customer figures.
