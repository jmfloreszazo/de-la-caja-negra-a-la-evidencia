# Experimental completion roadmap (E1–E4)

This is an **engineering execution plan**, not a new book edition. Every experiment starts unverified and must produce an independent, inspectable result before the status in `evidence/claims.json` may change. Core COBOL/SQLite reference snapshots remain pinned.

| Phase | Work | Exit gate | State | Tracking |
| --- | --- | --- | --- | --- |
| E1a | PostgreSQL 16 using Podman: row locks, real deadlock, serialization anomaly, pool exhaustion, persisted oracle | Real CI execution; negative controls must fail when corrupted | [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337) on PostgreSQL 16.13 | — |
| E1b | Port the transactional candidate to .NET 10 (Npgsql); compare original synthetic workload | Differential persisted-state, failure and concurrency tests under real PostgreSQL | [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) for tested subset; full SQLite parity remains | [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) |
| E1c | Repeat with SQL Server, isolating vendor-specific semantics | Deadlock/timeout/unique-key retry protocol and isolation documented | Not implemented | [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) |
| E2 | Orleans grains keyed by account coordinating the same durable ledger | Same E1 functional verdicts; hot-key distributions with quantified saturation | Not implemented | [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) |
| E3 | Azure vs on-prem/hybrid on a **filled and approved** capacity contract | Open-loop offered load, committed TPS, p99, fail-one-node, durability and cost; never MIPS-to-vCPU extrapolation | Not implemented | [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9) |
| E4 | Agent candidate limited to write scope; independent gate and mutation-qualified comparisons | Proven source isolation, false accept/reject rates and human review cost; negative cases | Not implemented | [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) |
| Reproduction | Linux/Windows/macOS, listings marked Illustrative, COMP-3/EBCDIC examples | Versioned repeatable commands and independent artifacts | Not implemented | [#11](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/11) |

## Decision log

- **E1a:** PostgreSQL 16.13, real deadlock / write-skew / pool and independent-oracle tests — [CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337).
- **E1b implemented subset:** .NET 10 + Npgsql persisted-state differential and selected fault/concurrency cases — [CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614). Full reference parity remains tracked in [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6).
- These checks prove only the listed synthetic scenarios. **Overall E1 remains unverified** pending completion of all gates; E2–E4 have not been executed.

## Acceptance rules

1. Record `commit SHA`, container digest, tool versions, workload configuration, commands, errors and **negative-control outcome**.
2. Keep observed results distinct from hypotheses and proposed target values; a failed experiment is useful evidence, not an excuse to change the threshold.
3. Use an independent read-only oracle that does not share the candidate's decision function.
4. Preserve existing benchmark constraints: `lab/performance-contract.json` is `UNCONFIGURED`; it must not be converted to PASS based on synthetic local runs.
5. No status promotion for E1–E4 and no release without a complete acceptance record and editorial approval.
6. E1a validates PostgreSQL behavior using a Python harness; E1b validates an independent .NET 10/Npgsql candidate on a controlled subset. Neither proves SQL Server parity or production/mainframe capacity.

See [E1 protocol](../lab/docs/EXPERIMENT_PROTOCOL.md) and [ES/EN evidence matrices](EVIDENCE.md).
