# Experimental completion roadmap (E1–E4)

This is an **English-only engineering execution plan**, not a new book edition. Every executable lab and its README stays in English; the book itself is maintained in both Spanish and English (see [language policy](LANGUAGE_POLICY.md)). Every experiment starts unverified and must produce an independent, inspectable result before the status in `evidence/claims.json` may change. Core COBOL/SQLite reference snapshots remain pinned.

| Phase | Work | Exit gate | State | Tracking |
| --- | --- | --- | --- | --- |
| E1a | PostgreSQL 16 using Podman: row locks, real deadlock, serialization anomaly, pool exhaustion, persisted oracle | Real CI execution; negative controls must fail when corrupted | [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337) on PostgreSQL 16.13 | — |
| E1b | Port the transactional candidate to .NET 10 (Npgsql); compare original synthetic workload | Differential persisted-state, failure and concurrency tests under real PostgreSQL | [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) for initial 7 controls and [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) for extended 10 controls and [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923) for direct SQLite↔PostgreSQL 16-case parity with lock release; [960-transfer uniform/hot functional worker-matrix CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329); SQL Server parity and production durability remain | [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) |
| E1c | SQL Server 2022 Developer under Podman and independent .NET 10/SqlClient candidate | 16 SQLite/SQL Server persisted-state cases, genuine `1205` deadlock, bounded `1222`, SNAPSHOT write skew, SERIALIZABLE defense, two-slot pool and independent negative oracle | [SQL Server core CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41041573996) (10 controls) and [original 960-transfer per-transfer-process CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) and [stronger 960-transfer persistent-worker CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791), eight cases each, 7/7 independent oracle checks. HA, power loss, cross-engine performance and mainframe capacity untested | [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) |
| E2 | Orleans grains keyed by account, using the **same authoritative E1 PostgreSQL transaction** (no cross-grain ACID claim) | E1 functional parity, independent negative oracle, uniform and fixed hot-key distributions, bounded failure recovery and committed-work metrics | [Protocol designed](../lab/e2_orleans/EXPERIMENT_PROTOCOL.md); **not implemented or executed**. CI runner availability is a current blocker | [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) |
| E3 | Azure vs on-prem/hybrid on a **filled and approved** capacity contract | Open-loop offered load, committed TPS, p99, fail-one-node, durability and cost; never MIPS-to-vCPU extrapolation | Not implemented | [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9) |
| E4 | Agent candidate limited to write scope; independent gate and mutation-qualified comparisons | Proven source isolation, false accept/reject rates and human review cost; negative cases | Not implemented | [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) |
| Reproduction | Linux/Windows/macOS, listings marked Illustrative, COMP-3/EBCDIC examples | Versioned repeatable commands and independent artifacts | Not implemented | [#11](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/11) |

## M1: reproducible gRPC / REST transport study

A [first executable .NET 10 microbenchmark](../lab/transport/README.md) compares **HTTP/2 REST/JSON versus HTTP/2 gRPC/Protobuf** against an identical stateless business decision, using an independent response oracle and CI artifacts. This only isolates protocol/serialization overhead: no SQL commit, real WAN, TLS or replica scaling is measured. **It is not an E3 result.** Follow up under [issue #12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) with TLS equivalence, PostgreSQL durability, 1/2/4/8/16 replicas, hot-key loads and cost per correct committed transfer.

## M2: PostgreSQL-durable REST versus gRPC, single-host horizontal smoke

[Source and reproduction instructions](../lab/durable_rpc/README.md). The experimental harness shares one real PostgreSQL 16 database between 1, 2, 4, 8 and 16 .NET 10 service processes, running REST/JSON and gRPC/Protobuf over HTTP/2 on localhost. It separately compares uniform and 50%-hot-key traffic. An **independent SQL oracle reads committed balances, postings and outbox** after every case and rejects deliberate corruption. Machine-generated reports show committed transactions/s and p99.

**Deliberate classification**: local single-host / one database / 256 operations per scenario / closed-loop / no TLS. This is an experimental smoke test, not a cloud or mainframe benchmark; M2 does not complete E1 or E3. Follow on with real distributed infrastructure, TLS, open-loop load, failover and dated TCO in [issue #12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12).

## M2 verified local evidence · 30 October 2026

[ES experimental report](../evidence/runs/M2.es.md) · [EN report](../evidence/runs/M2.md) · [full original CI result committed to Git](../evidence/runs/m2-full-summary.json) · [run #41016081107](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41016081107).

**All 20 synthetic SQL-backed cases passed**, with an independent read-only oracle after each case and a negative control rejecting a corrupted ledger. Observed throughput **fell** when multiple Kestrel processes competed for one hosted runner and one PostgreSQL database. This is **local smoke evidence**, not a mainframe or Azure scaling benchmark and not a basis to claim gRPC superiority. **E3 remains unexecuted.** The next gate is distributed replicas on separate nodes, equal TLS, an open-loop load generator, durability/failure injection, and dated TCO.

## Horizontal-first architecture and dated economics (new mandatory gates)

**Do not replace the mainframe with a single enormous VM by default.** The workload must first be partitioned by business invariants and tested with horizontal replica counts 1/2/4/8/16 under fixed offered load. Candidate deployments: VM Scale Sets, AKS, Azure Container Apps and App Service, plus a viable on-premises baseline. Measure bottlenecks at the authoritative ledger, hot-key contention, CPU, memory, logging, quotas and WAN p99. Vertical scale remains a measured option for intrinsically serialized components, not the default answer.

**Internal transport:** perform a fair gRPC/Protobuf (HTTP/2/TLS) versus REST/JSON experiment with the same .NET 10 business commands, transport security, network path and negative controls; monitor channel reuse, per-RPC distribution, message size, deadlines, CPU, throughput and tail latency. Prefer asynchronous Service Bus/outbox/KEDA for long-running work that must not create synchronous call chains. Record the cost per successful durable transfer.

**Pricing:** [ES](PRICING.es.md) / [EN](PRICING.md) + [dated catalog](../lab/cost/dated_prices.json) + [Azure Retail API observation job](../.github/workflows/infrastructure-pricing.yml). Every number must carry **source, date, currency, region, SKU, billing method and exclusions**. IBM/Unisys/on-premises TCO need vendor quotes and power/space/DR/operation. No estimate should replace a bank-approved workload contract. The E3 issue [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9) tracks the final comparison.

## WAN and infrastructure evidence gate (E3)

The [bilingual WAN field-measurement protocol](NETWORK_PROTOCOL.md) is a required part of issue [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9). Its [deterministic network model](../lab/network/wan_model.py) is explicitly hypothetical and must not be used to promote E3. Compare branch-to-screen p50/p95/p99, TN3270 or HTTP paths, WAN loss, gateway hops and failover alongside ledger durability and accounting invariants.

## Decision log

- **E1a:** PostgreSQL 16.13, real deadlock / write-skew / pool and independent-oracle tests — [CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337).
- **E1b implemented subset:** .NET 10 + Npgsql persisted-state differential and selected fault/concurrency cases — [initial 7-control CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614), [extended 10-control CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879). The extension proves bounded `55P03` exhaustion, post-timeout idempotent recovery, and oracle rejection of deliberate ledger corruption. [Both original snapshots](../evidence/runs/README.md) remain versioned independently. The tested E1b synthetic reference contract, including the [960-transfer uniform/hot worker matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329), passed. [Issue #6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) remains open until author-approved integration.
- **E1c completed synthetic gates:** .NET 10/SQL Server 2022 Developer core, real `1205` and `1222` errors, isolation negatives and independent oracle, plus the [960-transfer worker matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) and a [persistent-worker follow-up](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791). [Issue #7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) remains open until authorized integration.
- These checks prove **only** the synthetic scenarios listed. **Overall E1 stays partially verified:** production-scale performance, power-loss durability, HA/failover and bank/mainframe equivalence have not been accepted. E2–E4 have not been executed.

## Acceptance rules

1. Record `commit SHA`, container digest, tool versions, workload configuration, commands, errors and **negative-control outcome**.
2. Keep observed results distinct from hypotheses and proposed target values; a failed experiment is useful evidence, not an excuse to change the threshold.
3. Use an independent read-only oracle that does not share the candidate's decision function.
4. Preserve existing benchmark constraints: `lab/performance-contract.json` is `UNCONFIGURED`; it must not be converted to PASS based on synthetic local runs.
5. No status promotion for E1–E4 and no release without a complete acceptance record and editorial approval.
6. E1a validates PostgreSQL behavior using a Python harness; E1b validates an independent .NET 10/Npgsql candidate on a controlled subset. Neither proves SQL Server parity or production/mainframe capacity.

See [E1 protocol](../lab/docs/EXPERIMENT_PROTOCOL.md) and [ES/EN evidence matrices](EVIDENCE.md).
