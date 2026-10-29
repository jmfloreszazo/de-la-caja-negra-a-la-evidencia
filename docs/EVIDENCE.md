# Evidence matrix and boundaries

**English** · [Español](EVIDENCE.es.md)

**Principle:** publishing, executing and designing are different. Readers should know precisely what has been demonstrated and what remains open.

| ID | Claim | Status | Limit | Provenance |
|---|---|---|---|---|
| `BOOK-CI` | ES/EN sync, links, Markdown and diagrams | **Executed in CI** | Structural validation, not a certification of translation quality | [Workflow #40901043531](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043531) |
| `ORACLE-LAB` | COBOL/.NET contract lab and Oracle Gate | **Executed in CI** | 58 synthetic cases; not equivalence for a real banking system | [Workflow #40901043412](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043412) |
| `SQLITE-LAB` | Accounting invariants and concurrency on SQLite | **Executed in CI** | Does not demonstrate PostgreSQL/SQL Server row locks or mainframe-scale throughput | [Workflow #40901043412](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043412) |
| `PODMAN-CI` | Container and lab executed with Podman in Linux CI | **Executed in CI** | Ubuntu CI does not establish universal portability | [Workflow #40901043412](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043412) |
| `RELEASE-BOOK` | ES/EN PDF and Markdown editions published | **Published** | A published artifact does not verify every claim it contains | [v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29) |
| `E1` | SQL row locks, deadlocks and write skew | **Designed, NOT executed** | PostgreSQL/SQL Server E1 has no validated execution | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E2` | Orleans and ledger under different load distributions | **Designed, NOT executed** | No executed E2 benchmark against E1 | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E3` | Azure vs on-premises and hybrid benchmark | **Designed, NOT executed** | No capacity, cost or failure experiment using a real contract | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E4` | Comparison of agents behind an independent oracle | **Designed, NOT executed** | No executed E4 evaluation of defects and cost | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `CROSS-PLATFORM` | Independent reproduction on macOS/Windows | **Reproduction pending** | Only Linux CI execution has been verified | [Protocol, not a result](../ROADMAP.md) |
| `ILLUSTRATIVE` | Compilation of all Illustrative examples | **Reproduction pending** | No exhaustive verification of these listings exists | [Protocol, not a result](../ROADMAP.md) |

## How to interpret the matrix

**Executed in CI** means the linked workflow succeeded on a GitHub-hosted Linux runner. It is not a production operating guarantee.

**Designed, NOT executed** means there is an experiment protocol and acceptance criteria, but no experimental result. This explicitly includes E1–E4.

**Published** establishes that release assets exist; it does not validate all their technical assertions.

## Updating states with evidence

The structured registry is [`evidence/claims.json`](../evidence/claims.json). Promoting E1, E2, E3 or E4 requires a reproducible execution, source version, acceptance criteria, negative controls and accessible results. Invented PASS verdicts and isolated demos are not capacity evidence.

Check the local contract:

```bash
python3 scripts/check_evidence.py
```

The **live** CI check also verifies the source commit, successful jobs and release assets against the GitHub API:

```bash
GITHUB_TOKEN=... python3 scripts/check_evidence.py --online
```

The [E1–E4 experiment protocol](../lab/docs/EXPERIMENT_PROTOCOL.md) defines future tests; it is not evidence that they took place.
