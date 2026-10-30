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
| `E1A` | Real PostgreSQL: row locks, 40P01 deadlock, 40001 write skew and independent oracle | **Executed in CI** | Synthetic Linux/Podman test, not a performance benchmark or production banking system. E1 remains incomplete. | [Run #40919268337](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337) |
| `E1B` | .NET 10/Npgsql candidate: PostgreSQL state and failure parity | **Executed in CI** | Differential parity for the tested subset versus the Python candidate; does not cover the entire SQLite lab or SQL Server. | [Run #40919773614](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) |
| `E1` | SQL row locks, deadlocks and write skew | **Partially verified (E1a + E1b)** | E1a/E1b verified; full parity and SQL Server remain open | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E2` | Orleans and ledger under different load distributions | **Designed, NOT executed** | No executed E2 benchmark against E1 | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E3` | Azure vs on-premises and hybrid benchmark | **Designed, NOT executed** | No capacity, cost or failure experiment using a real contract | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E4` | Comparison of agents behind an independent oracle | **Designed, NOT executed** | No executed E4 evaluation of defects and cost | [Protocol, not a result](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `CROSS-PLATFORM` | Independent reproduction on macOS/Windows | **Reproduction pending** | Only Linux CI execution has been verified | [Protocol, not a result](../ROADMAP.md) |
| `ILLUSTRATIVE` | Compilation of all Illustrative examples | **Reproduction pending** | No exhaustive verification of these listings exists | [Protocol, not a result](../ROADMAP.md) |

## Supplemental experiment observations in draft PR #5

- **M1 (29 October 2026):** [raw transport-only evidence and measured results](../evidence/runs/M1.md), .NET 10 HTTP/2 loopback, without SQL durability, TLS or WAN. This is **not** evidence of committed banking TPS.
- **M2 (30 October 2026):** [20 durable PostgreSQL test cases and independent oracle results](../evidence/runs/M2.md) on a **single hosted runner and shared database**, with REST/JSON and gRPC/Protobuf. Observed local contention does not establish distributed horizontal scalability or E3.

These observations belong to [draft PR #5](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/5), not to published release `v2026.10.29`. They do not promote any E1–E4 overall claim.

## How to interpret the matrix

**Executed in CI** means the linked workflow succeeded on a GitHub-hosted Linux runner. It is not a production operating guarantee.

**Designed, NOT executed** means there is an experiment protocol and acceptance criteria, but no accepted experimental result. This applies to E2, E3 and E4; E1 is **partially verified** through E1a/E1b, not complete.

**Partially verified** means some subtests have their own passing CI but the overall experiment has not met all acceptance criteria; E1a/E1b do not establish E1c or mainframe capacity.

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

The [E1–E4 experiment protocol](../lab/docs/EXPERIMENT_PROTOCOL.md) defines acceptance criteria, not execution evidence. The E1a/E1b and M1/M2 results above are separately recorded and retain their narrow test scope.
