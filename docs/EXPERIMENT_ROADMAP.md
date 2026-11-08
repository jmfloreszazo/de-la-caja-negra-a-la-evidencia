# Experimental completion roadmap (E1–E4)

This is an **English-only engineering execution plan**, not a new book edition. Every executable lab and its README stays in English; the book itself is maintained in both Spanish and English (see [language policy](LANGUAGE_POLICY.md)). Every experiment starts unverified and must produce an independent, inspectable result before the status in `evidence/claims.json` may change. Core COBOL/SQLite reference snapshots remain pinned.

| Phase | Work | Exit gate | State | Tracking |
| --- | --- | --- | --- | --- |
| E1a | PostgreSQL 16 using Podman: row locks, real deadlock, serialization anomaly, pool exhaustion, persisted oracle | Real CI execution; negative controls must fail when corrupted | [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337) on PostgreSQL 16.13 | — |
| E1b | Port the transactional candidate to .NET 10 (Npgsql); compare original synthetic workload | Differential persisted-state, failure and concurrency tests under real PostgreSQL | [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) for initial 7 controls and [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) for extended 10 controls and [PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923) for direct SQLite↔PostgreSQL 16-case parity with lock release; [960-transfer uniform/hot functional worker-matrix CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329); Production power-loss durability, HA and approved bank contract remain | [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) |
| E1c | SQL Server 2022 Developer under Podman and independent .NET 10/SqlClient candidate | 16 SQLite/SQL Server persisted-state cases, genuine `1205` deadlock, bounded `1222`, SNAPSHOT write skew, SERIALIZABLE defense, two-slot pool and independent negative oracle | [SQL Server core CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41041573996) (10 controls) and [original 960-transfer per-transfer-process CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) and [stronger 960-transfer persistent-worker CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791), eight cases each, 7/7 independent oracle checks. HA, power loss, cross-engine performance and mainframe capacity untested | [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) |
| E2 | Orleans grains keyed by account, using the **same authoritative E1 PostgreSQL transaction** (no cross-grain ACID claim) | E1 functional parity, independent negative oracle, uniform and fixed hot-key distributions, bounded failure recovery and committed-work metrics | [Partially verified original SQL/Orleans CI](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8): multi-process two-silo Podman tests, SQL membership, selected network failures and load under one Linux runner. **Not fully accepted**; concurrent-activation observations, continuous unassisted recovery, physical hosts, sustained saturation and HA remain open; bounded long-schedule assisted recovery is documented separately | [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) |
| E3 | Azure vs on-prem/hybrid on a **filled and approved** capacity contract | Open-loop offered load, committed TPS, p99, fail-one-node, durability and cost; never MIPS-to-vCPU extrapolation | Azure single-VM exploratory open-loop/process-failure slice executed; approved comparative capacity gate remains open | [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9) |
| E4 | Agent candidate limited to write scope; independent gate and mutation-qualified comparisons | Proven source isolation, false accept/reject rates and human review cost; negative cases | Isolation qualification and one real Azure builder task verified; full comparative study and human review cost remain open | [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) |
| Reproduction | Linux/Windows/macOS, listings marked Illustrative, COMP-3/EBCDIC examples | Versioned repeatable commands and independent artifacts | Not implemented | [#11](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/11) |

## Azure infrastructure and separately recorded executions

[Bicep and operator runbook](../infra/experiments/README.md) provide a private
runner, VM Scale Set capacity controls (0/1/2/4/8/16), opt-in private managed
PostgreSQL, evidence storage and budget notifications. Existing core/E1/E2/M2
synthetic harnesses can be launched on the Azure runner with source hashes and
failure artifacts. Those launches remain single-VM smoke runs: VMSS provisioning
does not install distributed replicas, and the managed database is not silently
substituted for the disposable local PostgreSQL used by fault fixtures.
Distributed TLS/open-loop/N-1 acceptance, live E4 evaluation and Azure validation
remain separate gates. No E1-E4 claim is promoted by this preparation.

The [7 November local reproduction](../evidence/runs/local-reproduction-2026-11-07.json)
executed core, PostgreSQL E1, co-located functional Orleans E2 and the complete
20-case M2 smoke matrix under WSL/Docker. Independent negative controls passed.
It preserves three failed launcher attempts, the successful reruns, source
patch hashes and the distinction from original CI evidence. The full archive
remains local; no Azure deployment or final E1-E4 promotion occurred.

The [additional local E2 recovery campaign](../evidence/runs/local-e2-cluster-2026-11-07.json)
also passed the opt-in `e2-cluster` sequence: actual SQL deadlocks, six matched
workload runs/600 durable transfers, co-host process kills, development and
ADO.NET two-silo recovery, and two pre/post-COMMIT in-flight termination cases.
Silos and client were distinct OS processes on one physical host. These
observations do not establish physical-node HA, sustained capacity or an RTO.
Azure quota validation remains blocked by expired CLI authentication; public
retail price retrieval is not deployment authorization or a complete budget.

The [local E4 prerequisite qualification](../evidence/runs/local-e4-qualification-2026-11-07.json)
ran 58 frozen cases per candidate, accepted the reference and rejected all three
known mutants using the independent DEMO_ONLY gate. Actual attempted writes to
the original contract, verifier and container root filesystem were denied;
the candidate-directory write succeeded and protected hashes remained unchanged.
Thirteen synthetic regression controls separately passed. The
[reproduction harness](../lab/e4_agents/README.md) preserves its exact source,
container settings and real reused COBOL observations. **Live agent runs: zero.**
No accepted-defect rate, false-block rate, human review duration or model cost
has been measured. Authenticated model access and an approved campaign remain
required; this does not promote E4 to accepted.

The [first executed Azure campaign](../evidence/runs/azure-single-vm-2026-11-07.json)
now verifies the prepared Bicep and core/E1/extended-E2/M2 workloads on a private
North Europe D4s_v5 VM. West Europe rejected regional eligibility; the original
failed validation is retained. The accepted WhatIf had 17 creates, zero edits
and zero deletes. Core passed its independent downloaded-database audit;
E1 passed the 960-transfer worker matrix; E2 committed 600 matched-workload
transfers and recovered after actual process kills; M2 passed 20 cases with
256 durable commits each. A full M2 repeat corrected inherited host labels,
without rewriting the first raw attempt. This is Azure execution, **not E3
distributed capacity/HA acceptance or a live-agent E4 campaign**. The runner
was subsequently deallocated and VMSS remained at zero instances. Storage,
disk and NAT-related charges remain; actual billing was not estimated as fact.

The [8 November live builder pilot](../evidence/runs/e4-live-builder-2026-11-08.json)
invoked an existing Azure model once using only the public synthetic contract.
The generated C# candidate passed its 16 self-authored tests and all 58 frozen
cases under local WSL/Docker isolation. Its tests accepted the reference and
rejected all three known mutants; the independent gate's mutation qualification
also passed. A replay reused the same response, not another model call.
Recorded usage was 269 input plus 2,279 completion tokens. This is a fixed
model-driven workflow, not proof of autonomous agent superiority, a task
population defect rate or measured human review cost. E4 acceptance stays open.

The [separate Azure M1 execution](../evidence/runs/azure-m1-2026-11-08.json)
adds the transport-only study to the common launcher. Both concurrency profiles
(8 and 32) passed: eight measured rounds, 20,000 replies, zero response errors
and both negative controls detected. Loopback on an Azure VM is still not
distributed transport, TLS/WAN or ledger capacity. The runner was deallocated
again after evidence download.

The [executed E3 readiness check](../evidence/runs/e3-readiness-2026-11-08.json)
returned `INCONCLUSIVE / BLOCK`, exit 3: all 14 capacity fields remain empty
and status remains `UNCONFIGURED`. This is a reproduced refusal to infer
capacity, **not an E3 load trial**. Owner approval, comparable on-prem/mainframe
access and the external measurement protocol cannot be supplied by synthetic
defaults.

### E1–E4 Azure follow-up, 8 November

The [new campaign](../evidence/runs/azure-e1-e4-2026-11-08.json) repeats E1 and
extended E2 with explicit PostgreSQL collection/cleanup outcomes. E1 passed
960 transfers; E2 passed 600 matched-workload transfers and both membership
providers. A local E1/E2/M2 repetition independently passed before cloud execution.

The [E3 exploratory harness](../lab/e3_capacity/README.md) now executes actual
open-loop offers and a process restart on Azure: 720 offers, 668 commits,
48 connection failures and four missed schedules. All outcomes remain recorded;
seven independent accounting checks and negative corruption control passed.
This is not a sustained capacity ceiling or physical-node HA. The approved
Azure/on-prem/mainframe comparison is still unexecuted.

E4 now includes candidate evaluation on the Azure VM using nonroot Podman,
not only Azure-hosted inference. It replays the original response: 16 self-tests,
58 frozen cases, three rejected mutants and three denied protected writes.
An initial working-directory permission failure is retained separately. This
replay performs zero new model calls and does not add an independent study task.

### TODM validation is an executable evidence check

The [TODM adapter](../lab/todm_validation/README.md) follows the pinned upstream
methodology and retains its MIT attribution. Explicit inventories bind actual
contracts, sources, runtime bytes and raw observations. Per-experiment G0–G7
reports distinguish technical oracle verdicts from approval and release.
Untrusted local approvals do not grant G2/G6 authority.

The first complete-input attempt rejected E3 because five runtime digests had
no matching original bytes in the downloaded archive. Original binaries were
retrieved separately from the retained Azure source tree with matching hashes;
no rebuild was substituted and the rejected bundle remains immutable. Negative
controls additionally cover altered bytes, missing evidence, false invariants
and authority failures. This is demonstrated fail-closed evidence handling,
not certification of production TODM or a comparative effectiveness study.

The [Azure-side TODM replay](../evidence/runs/todm-azure-2026-11-08.json)
then verified 134 snapshot files and 108 artifact bindings. E1–E4 bounded
technical evaluations passed; eight actual-input negative controls and twelve
synthetic upstream mandate cases passed. Aggregate methodology remains
`INCONCLUSIVE`, release `BLOCK`. The failed external-output-path invocation
and successful in-root qualification retry are preserved separately. The VM
was deallocated after all evidence downloads; residual storage/network costs remain.

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
- **E1b implemented subset:** .NET 10 + Npgsql persisted-state differential and selected fault/concurrency cases — [initial 7-control CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614), [extended 10-control CI PASS](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879). The extension proves bounded `55P03` exhaustion, post-timeout idempotent recovery, and oracle rejection of deliberate ledger corruption. [Both original snapshots](../evidence/runs/README.md) remain versioned independently. The tested E1b synthetic reference contract, including the [960-transfer uniform/hot worker matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329), passed. [Issue #6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) was integrated; its historical issue does not establish global E1 acceptance.
- **E1c completed synthetic gates:** .NET 10/SQL Server 2022 Developer core, real `1205` and `1222` errors, isolation negatives and independent oracle, plus the [960-transfer worker matrix](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) and a [persistent-worker follow-up](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791). [Issue #7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) was integrated; its historical issue does not establish global E1 acceptance.
- These checks prove **only** the synthetic scenarios listed. **Overall E1 stays partially verified:** production-scale performance, power-loss durability, HA/failover and bank/mainframe equivalence have not been accepted. E2 has verified synthetic CI slices but remains **partially verified**; E3 and E4 are still designed, not executed as complete experiments.

## Brownfield CAP-007/CAP-005 coexistence checkpoint — 1 November 2026

The functional-first brownfield line is separately tracked by [#32](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/32), [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) and [#64](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/64). **This is not E1/E2/E3/E4 acceptance by relabeling.**

- [PR #60](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/60): in-memory writer/epoch and cutover rehearsal; only synthetic control-model evidence.
- [PRs #61–#62](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/61): real PostgreSQL 16/.NET 10/Npgsql transfers, persisted ledger/postings/outbox and precommit SIGKILL versus COMMIT-before-lost-ACK. Dedicated postmerge SQL CI on exact main SHA; no external CICS fence or G6 authorization.
- [PR #63](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/63): two **logical** PostgreSQL stores, black-box simulated legacy process, read-only shadow, staged snapshot, complete two-store reconciliation, cooperative writer fencing and blocked rollback after candidate-origin decisions. Exact merged-main SHA `d04623e8c276bedda9918e87a09fa0c3f9da1f6a`; [SQL workflow #41340310748](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41340310748) PASS. Original ES/EN source-run reports: [EN](../evidence/runs/BROWNFIELD-TWO-STORE.md) / [ES](../evidence/runs/BROWNFIELD-TWO-STORE.es.md).
- **Historical next step at PR #63:** [#64](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/64) persistent admission/UNKNOWN journal for a router across process failures and stale epochs; bank-controlled source-side writer fence and independent business contract/Golden Master acceptance under #58. TODM G2 remains INCONCLUSIVE and G6 BLOCK.
- At the original two-store checkpoint, exactly **two containers on one hosted Linux machine** do not establish physically independent fault domains, production banking semantics, IBM Z MIPS equivalence, RTO/RPO or Azure TCO. No release was created by #60–#63.

### Current brownfield checkpoint — 2 November 2026

PR #66 added the three-store admission journal; #68 added capability gateway
controls; #69 persisted adapter enrollment and interrupted-transition recovery.
On merged main `279ca5662dd870c0f1bb7dab7d1474f346904df3`, original
[C2 run #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630)
passed **20 controls**, both independent SQL oracles 10/10. Seven applicable
main workflows succeeded; Release was skipped. The earlier 19-control ZIP
remains an independent, immutable observation. In-flight controller partitions,
lock-loss windows, external side effects, real bank-owned fencing and G2/G6
approval are still open. Three SQL containers share one physical runner.
Clean-room/confidential-computing issue #53 and branch protection #16 remain
deferred. Published stable and research tags have not changed.

### E2 specific status correction

[E2 issue #8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) has actual original CI results: Orleans 10.4.0, durable PostgreSQL and ADO.NET membership, process loss/ambiguous response, network-fault scopes and selected 20/40/80 offered-rate observations. These establish **bounded tested behaviors only**, not an accepted sustained capacity ceiling, two physical hosts or production HA. [sustained benchmark #25](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/25), concurrent-activation observations, continuous unassisted recovery and physical-host tests remain required for their associated scientific claims, but are non-blocking for book/lab integration under the author's 3 November decision. No blanket E2 PASS is permitted.

## Acceptance rules

1. Record `commit SHA`, container digest, tool versions, workload configuration, commands, errors and **negative-control outcome**.
2. Keep observed results distinct from hypotheses and proposed target values; a failed experiment is useful evidence, not an excuse to change the threshold.
3. Use an independent read-only oracle that does not share the candidate's decision function.
4. Preserve existing benchmark constraints: `lab/performance-contract.json` is `UNCONFIGURED`; it must not be converted to PASS based on synthetic local runs.
5. No status promotion for E1–E4 and no release without a complete acceptance record and editorial approval.
6. E1a validates PostgreSQL behavior using a Python harness; E1b validates an independent .NET 10/Npgsql candidate on a controlled subset. E1c supplies separate synthetic SQL Server parity evidence; none establishes production/mainframe capacity.

See [E1 protocol](../lab/docs/EXPERIMENT_PROTOCOL.md) and [ES/EN evidence matrices](EVIDENCE.md).

C05/C06 now have [audited short directional packet-loss cases](../evidence/runs/E2-C05-C06-DIRECTIONAL.md). They do not establish exclusive activation or sustained stable service. A later [long-schedule audit](../evidence/runs/E2-LONG-PARTITION.md) verifies only assisted recovery with 14 paired samples across about 66s after earlier secondary exit; it does not retrospectively extend the short-case scope.

The [directed ordinary-grain trial](../evidence/runs/E2-ACCOUNT-DIRECTED.md) in PR #80 records two positive incoming-envelope witnesses and four INCONCLUSIVE originals across three archived campaigns. The third campaign reproduces a secondary-outbound witness with both log streams retained, while all three primary-outbound cases remain inconclusive. The added pre-invoke delay changes timing; natural lifecycle/partition acceptance and repeatability remain open. The repeat identifies a fatal membership path after the local silo is recorded Dead. Sustained-capacity work under #25 may proceed independently without closing these gates.

B05 #25 now has a [three-cohort direct admission diagnostic](../evidence/runs/B05-DISPATCH-DIAGNOSTIC.md): 119,040 offers, 118,887 SQL commits, 153 exact cap-32 admission misses and no misses at cap 128, with 42 financial invariant checks. This does not establish backend saturation, Orleans scaling or the historical warmup cause; sustained capacity and bottleneck attribution remain open.

## Integration decision — 3 November 2026

The author authorized merging the bounded E2 observations, calibration, directed trials and B05 diagnostic (PRs #78–#81). Unmet external claims no longer block book/lab integration or the next editorial work. E2 remains scientifically partially verified; E2 #8 is closed NOT_PLANNED for the excluded external campaign, with no stronger claim: see [bounded E2 closeout](E2_CLOSEOUT.md). The historical #24/#25 references are evidence provenance, not additional open E2 work. The [external-validation protocol](EXTERNAL_VALIDATION.md) specifies topology, code changes, clock uncertainty, load/fault design, independent oracles and evidence required for stronger claims. No failure is relabeled and no production acceptance or release is implied.

A future **global E2 scientific PASS** has a [complete separately authorized X00–X08 campaign protocol](E2_FULL_PASS_PROTOCOL.md) ([ES](E2_FULL_PASS_PROTOCOL.es.md)); no external run has been made under that specification. This is **not** a new active E2 issue, and #8 remains closed `not_planned`.

## Administrative consolidation — 3 November 2026

The [closeout register](PROJECT_CLOSEOUT.md) records the retired implementation/duplicate trackers. External E2 criteria from #24/#25/#74 remain in #8; distributed M1/M2/E3 criteria from #12 remain in #9; C2 remainder #64 is in #58. Issue closure is not experimental status promotion. Original source/run identifiers and all FAIL/INCONCLUSIVE artifacts remain unchanged.
