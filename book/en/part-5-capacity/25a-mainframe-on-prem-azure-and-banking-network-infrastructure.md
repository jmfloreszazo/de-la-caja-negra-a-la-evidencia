**English** · [Español](../../es/parte-5-capacidad/25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md)

[← Chapter 25 · Azure or a huge machine at the customer's site](25-azure-or-a-huge-machine-at-the-customer-s-site.md) · [Contents](../README.md) · [Part VI · The lab →](../part-6-lab/README.md)

# Chapter 25 bis · Infrastructure versus a current mainframe: on-premises, Azure and the branch network

> **Thesis.** You do not replace a mainframe with a box that has more cores. You replace an entire operational service: transactional computing, I/O, isolation, durable commit, continuity and the response seen by a branch that may be thousands of kilometres away. Equivalence is an end-to-end test, not a marketing-specification comparison.

This chapter supplements [chapter 25](25-azure-or-a-huge-machine-at-the-customer-s-site.md) with named market references and a falsifiable architecture protocol. **Manufacturer data checked in October 2026; our measured performance against those machines: none.** What we *have* measured—on one Azure VM, with synthetic load—is described in its own sections after the comparison protocol, so that the reader does not mistake it for that comparison.

## Real systems, real published specifications, and a comparison we cannot yet make

| Market reference | Vendor-published capability | What it means and does NOT establish |
|---|---|---|
| [IBM z17 ME1](https://www.ibm.com/products/z17) | Up to **208 engines**, **64 TB** memory, **5.5 GHz** Telum II | Mission-critical IBM Z; 208 configurable engines are not 208 x86 vCPUs and not verified TPS |
| [IBM LinuxONE Emperor 5](https://www.ibm.com/downloads/documents/us-en/1227cc9e78cb9240) | Up to **208 engines**, **64 TB**, **5.5 GHz** | IBM Z-class system centred on Linux; not an automatic replacement for z/OS/CICS/Db2 and not an independent throughput benchmark |
| [Unisys ClearPath Forward Dorado 8590](https://www.unisys.com/siteassets/collateral/pi-sheet/pi-200145-clearpathforwarddorado8590.pdf) | Published **200–8,400 monthly MIPS** scale and **12,000 MIPS ceiling** per OS 2200 partition; **925 single-thread MIPS** | **Vendor-specific MIPS** and product model. These figures cannot be directly compared with IBM Z or x86 vCPUs |
| [Azure Mdsv3 Very High Memory](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/memory-optimized/mdsv3-vhm-series) | Published **896–1,792 vCPUs**, up to **30,400 GiB**, up to **185 Gbit/s** network and **8 GB/s** remote disk throughput | VM specification, not a ledger commit-throughput guarantee or evidence that a region, quota or budget supports it |
| [On-premises AMD EPYC 9965 node](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9965.html) | **192 cores/384 threads per socket**, 1P/2P support, 12 DDR5 channels and up to 3.7 GHz turbo | A physical-server candidate. Two sockets could deliver **384 physical cores**, but not 384 IBM engines or mainframe-class resilience |

Core counts, memory, clock rate, vendor MIPS and network bandwidth **come from product specifications, not from our laboratory measurements**. IBM z17 and LinuxONE are related architectural families: they are not two independent benchmark observations. IBM's [zPCR](https://www.ibm.com/support/pages/getting-started-ibm-z-processor-capacity-reference) helps model IBM Z configurations; it is not a universal MIPS/vCPU conversion table.

A real migration first needs a **workload fingerprint**: CICS/TPS curves, MSU/zIIP use, CPU per transaction, hot-key distribution, Db2/VSAM I/O, real data volume, operation-level p99, batch windows, synchronous dependencies, recovery and cost. Without this, hardware equivalence claims are advertising.

## A banking branch is far away: WAN latency is part of the transaction

A 3270 screen can have a markedly different network profile from an SPA that makes twelve REST calls. IBM documents that contemporary clients commonly reach z/OS using **TN3270/TN3270E over TCP/IP**, and that an internal CICS response metric **does not include** the full communication path to the user's screen ([3270 connections](https://www.ibm.com/docs/en/cics-ts/6.x?topic=security-3270-connections-zos); [response time caveat](https://www.ibm.com/docs/en/cics-ts/6.x?topic=constraints-observing-response-time)). **Never confuse CICS internal response time with branch-to-screen response time.**

Physics remains relevant after buying ExpressRoute: light travels at roughly 200,000 km/s in fibre. **1,000 km of actual fibre** imposes an ideal round-trip lower bound near **10 ms**, before queuing, network devices, inspection, indirect routes and application work. This is not a measured banking WAN link. Microsoft emphasises that the **real fibre path and distance** dominate WAN latency ([ExpressRoute guidance](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-troubleshooting-network-performance)).

### Latency budget: keyboard to rendered response

The budget does not stop at an application returning `HTTP 200`:

**Listing 25a.1 · Branch-to-ledger path** — *Illustrative topology*

```text
Branch / TN3270 or browser
  | LAN + SD-WAN/MPLS/VPN + provider + routing + TLS
  v
Entry point / gateway / authentication / fraud control
  | routing, admission control, queue, service hop(s)
  v
.NET 10 / CICS coexistence adapter
  | hot-key lock + commit log + synchronous replica
  v
Authoritative ledger / outbox
  | response + network return + screen rendering
  v
Branch employee
```

Measure WAN RTT, session/TLS setup, authentication, queue time, application service, lock acquisition, durable log commit and rendering as separate factors. **The p99 of a sum is generally not the sum of component p99 values**; directly sample the complete user operation with correlated traces.

**Illustrative, NOT observed:** assume a 35 ms branch RTT. If a screen makes four extra sequential round trips to a central server, those trips alone can add roughly **140 ms** to the critical path, before CPU, database work or jitter. A single coarse-grained business command can remove most of that chattiness without relaxing durable-commit or acceptance semantics. **Reducing round trips may matter more than doubling cores.**

### Four entrance routes to compare

| Route | How to test it | Main hazard |
|---|---|---|
| Branch → bank WAN → on-premises data centre → CICS | TN3270/host transaction, RTT and real screen-time percentiles by branch | Legacy frontends, sessions, concentration points, host contention |
| Branch → SD-WAN → ExpressRoute → Azure | Connection Monitor from representative locations, business HTTPS call, application p99 and retries | Physical distance, circuit, gateway, inspection and extra hops |
| Branch → SD-WAN → Azure Virtual WAN hub → application | Effective routes, vHub/NVA, link failover, double inspection, packet loss | Hairpins, consolidation and NVA/gateway limits |
| Branch → local integration edge → core in Azure | Single authorised command, idempotency key, outbox and visible outcome | Link interruption, duplicate confirmation, inconsistent or pending state |

[ExpressRoute](https://learn.microsoft.com/en-us/azure/networking/hybrid-connectivity/hybrid-connectivity) offers private and more predictable connectivity, **not teleportation**. [FastPath](https://learn.microsoft.com/en-us/azure/expressroute/about-fastpath) can reduce gateway hops where eligibility permits. [Virtual WAN/SD-WAN](https://learn.microsoft.com/en-us/azure/virtual-wan/sd-wan-connectivity-architecture) can connect branches, but every security insertion and network hop should be measured. Avoid *hairpinning* between Azure VNets through ExpressRoute where suitable peering exists ([mission-critical guidance](https://learn.microsoft.com/en-us/azure/well-architected/mission-critical/mission-critical-networking-connectivity)).

**Crucially:** a branch edge may cache authorised reads, submit a command and show its state; it **must not confirm a debit/credit as final without an authoritative ledger commit**. A lost connection means PENDING/INCONCLUSIVE, later reconciliation and one idempotent effect—not an invented balance.

## Azure: scale out first, not up to a single enormous VM

The specifications above are **physical reference points**, not a strategy of choosing the biggest Azure VM as a mainframe replacement. The primary hypothesis is to **decompose at transactional boundaries and scale independently parallelisable work**, with an explicit authoritative ledger.

| Candidate | Horizontal scaling that is genuinely available | What does NOT magically scale |
|---|---|---|
| VM Scale Sets | Multiple homogeneous VMs, health probes and instance autoscaling without Kubernetes | Stateful monoliths, distributed commits, hot-key contention |
| AKS Standard / Automatic | Service replicas; HPA, KEDA for queues, Cluster Autoscaler/NAP for nodes; deployment isolation | Database, synchronous log, IOPS and contention on a single account; more pods can worsen lock pressure |
| Azure Container Apps Consumption / Dedicated | HTTP-concurrency replicas, event-driven KEDA jobs without cluster operations | Minimum replicas, cold starts, long sessions and stateful actors; **Dapr Actors cannot scale to zero** |
| App Service Premium v3 | Managed plan-instance scale-out and autoscale | Multiple apps sharing the same plan, sessions and common state |
| Orleans | Partitioning by grain identity within a horizontally scaled runtime | A hot grain remains serial; cross-account atomicity does not arise from grains automatically |

Microsoft distinguishes [HPA, VPA, Cluster Autoscaler, NAP and KEDA](https://learn.microsoft.com/en-us/azure/aks/concepts-scale). Horizontal compute scaling needs a **ledger saturation experiment**: 1, 2, 4, 8 and 16 replicas under open-loop offered load, fixed hot-key distribution, committed transactions/s and end-to-end p99. If doubling pods does not increase confirmed commits, the actual bottleneck is downstream. [Container Apps scaling](https://learn.microsoft.com/en-us/azure/container-apps/scale-app) also has its own trigger and stateful-app constraints.

**Candidate flow**: branch → authenticated business API (WAF, idempotency key) → stateless co-located gRPC commands → ledger-owner service and its transactional database; use Service Bus/outbox and KEDA workers for deferrable work. CQRS reads require explicit consistency semantics. A business confirmation follows a durable commit; a lost response is **INCONCLUSIVE** until looked up using its operation identity.

### Internal gRPC: underused, but not mandatory

gRPC normally operates on **HTTP/2 and TLS**. It is inaccurate to frame gRPC and HTTPS as exclusive alternatives. The relevant test is **gRPC/Protobuf versus REST/JSON with equivalent transport, topology and security**.

- **Good candidates:** typed, versioned binary contracts, frequent co-located synchronous calls, meaningful streaming and C#-to-C# service integration.
- **Poor candidates:** browser-native external APIs without a deliberate gateway, long-running operations best modelled by durable messaging, and operations that must remain one database transaction.
- **Required controls:** protobuf compatibility, propagated deadlines, cancellation, mTLS/workload identity, OpenTelemetry, size limits, safe retries/idempotency, circuit breakers and overload admission.
- **Pitfalls:** long-lived HTTP/2 channels can skew pod distribution; unbounded streams, protocol downgrade at gateways and retry storms can degrade p99.

[Container Apps internal networking](https://learn.microsoft.com/en-us/azure/container-apps/connect-apps) requires **end-to-end HTTP/2** for gRPC and may involve Envoy. In AKS, measure the actual ingress/service-mesh TLS path and RPC load balancing: a Kubernetes `Service` alone does not guarantee per-RPC balancing across long-lived gRPC channels.

Compare offered load, committed TPS, p50/p95/p99, CPU and allocated MB per request, bytes transferred, network hops, live connections, errors/retries, memory and total infrastructure cost under the **same business contract and independent oracle**. Do not assume a faster serializer implies a faster durable transaction.

### First M1 evidence: transport is not the ledger

The [executed M1 study](../../../evidence/runs/M1.md) compared gRPC/Protobuf with REST/JSON using **HTTP/2 on loopback without TLS or a database**, under .NET 10. GitHub recorded 2,500 requests per trial at concurrency 8 and 32. Both paths returned oracle-correct results, but **gRPC did not show consistent p99 superiority**. A smaller transport payload does not prove a faster banking commit; the next experiment must include durable persistence, equivalent TLS and per-replica distribution.

### M2 · When sixteen service processes are slower than one

The [executed M2 evidence](../../../evidence/runs/M2.md) connects **REST and gRPC to the same durable PostgreSQL ledger**. On one hosted runner, the 20-scenario matrix (1/2/4/8/16 processes, two protocols, uniform and hot-account traffic) achieved **20 accounting PASS results**: 256 commits, 512 postings and 256 outbox entries per scenario. Adding processes **did not improve throughput** on this constrained machine and shared database. The results and chart are versioned. **This is not an Azure scale-out benchmark**: independent nodes, TLS, open-loop traffic and failover still need testing.

### Reproduce first, then deploy, then measure distributed capacity

The [experiment infrastructure and runbook](../../../infra/experiments/README.md) separate these three steps. The same core, PostgreSQL E1, functional Orleans E2 and M2 harnesses can run locally or on an Azure runner, retaining logs, independent oracle results and runtime provenance. **The Bicep infrastructure has only been compiled and checked locally; it has not been deployed or measured in Azure.**

The template prepares private networking, evidence storage and a VM Scale Set with 0/1/2/4/8/16 instances. Provisioning instances does **not** install distributed application replicas. The optional managed PostgreSQL server is not the disposable database destroyed by the functional tests. Real E3 acceptance still needs an approved capacity contract, equivalent TLS, separate service and load-generator nodes, open-loop traffic, N-1 recovery and measured costs. A reproducible local PASS proves only the controls it actually exercised.

On **7 November 2026**, a [new local reproduction](../../../evidence/runs/local-reproduction-2026-11-07.json) on WSL/Docker passed 11 PostgreSQL/Python controls, 10 .NET controls, 16 sequential parity cases and the eight-case/960-transfer functional worker matrix. The co-located Orleans harness passed seven functional controls; M2 passed all 20 scenarios with 256 commits each. Independent oracles rejected deliberate ledger corruption. Three failed launcher attempts are retained alongside the successful reruns, rather than erased. This campaign ran neither GitHub Actions nor Azure, and does not complete E1–E4 acceptance; its full logs, dumps and source patches are retained in a local evidence archive.

A [subsequent local E2 campaign](../../../evidence/runs/local-e2-cluster-2026-11-07.json) also passed the real deadlock fixture, six matched workload runs with 600 durable transfers, and actual process termination controls. Two separate silo processes and an external client recovered after killing the secondary, with both development and PostgreSQL ADO.NET membership. Two additional cases exercised termination before and immediately after SQL COMMIT. The independent SQL oracle passed after recovery. **These are real process-failure observations on one physical host, not physical-node HA, a production recovery SLA or final E2 acceptance.**

A [local E4 prerequisite qualification](../../../evidence/runs/local-e4-qualification-2026-11-07.json) then exercised 58 frozen cases per candidate in separate, non-root, network-disabled containers. The independent gate accepted the reference candidate and rejected the three known mutants: rounding, threshold and inactive-account approval. Three actual write attempts against the original contract, verifier and container root filesystem were denied; writing to the disposable candidate directory succeeded. Protected source hashes remained unchanged. The [reproduction harness](../../../lab/e4_agents/README.md) retains the exact supervisor source, container inspections and the real COBOL observations reused from the earlier core run; it does not invent a new COBOL execution. Thirteen separate synthetic regression controls also passed.

**This is prerequisite evidence, not E4 acceptance.** No live agent or model was invoked, and no accepted-defect rate, false-block rate, human review duration or model cost was measured. The gate retains `DEMO_ONLY / SIMULATED_ALLOW` authority for the good candidate and blocks the mutants; it does not authorize a production release. The containers share the host kernel, and this campaign only executed the known reference sources and mutants, not arbitrary model-generated code.

The repository also provides a [local campaign collector](../../../lab/tools/reproduce_campaign.py), with [setup instructions](../../../lab/README.md#reproduce-the-local-multi-experiment-campaign). A [complete recorded invocation](../../../evidence/runs/local-public-campaign-2026-11-07.json) passed core, PostgreSQL E1, extended E2, M2 and the E4 prerequisite, retaining 331 source-file hashes and verifying 226 captured artifacts. This makes the sequence reproducible without the author's session-specific helpers:

```bash
python3 lab/tools/reproduce_campaign.py \
  --engine docker --output lab/results/campaign-001
python3 lab/tools/reproduce_campaign.py --verify lab/results/campaign-001
```

The normal command requires clean lab sources. For unpublished local changes, explicitly add `--include-working-tree`: the collector saves the executed source snapshot separately from the base commit. Each stage runs in a fresh Linux temporary checkout; failed attempts are retained rather than overwritten. Artifact integrity does not turn a failed run into a successful one or local controls into Azure acceptance. SQL Server remains opt-in and requires its separate license consent.

## Dated prices, not a deceptive vCPU-to-mainframe TCO

The official Azure API retrieval on **29 October 2026 at 18:26 UTC** (West Europe, Linux, pay-as-you-go, indicative EUR) returned **D4as_v5 €0.1830/h**, **D4s_v5 €0.2024/h** and **D8as_v5 €0.3661/h**. Three always-on D4as_v5 workers for 730 hours represent **€400.77/month of compute alone**; six represent **€801.54/month**, excluding database, disks, networking and redundancy. Exact meters, `effectiveStartDate` and CI source are in the linked registry.

The [dated pricing comparison, 29 Oct 2026](../../../docs/PRICING.md) and [structured catalog](../../../lab/cost/dated_prices.json) contain source-linked prices, a reproducible 3–6-worker comparison and public AMD EPYC CPU references. IBM/Unisys require contractual **RFQs** and are left unpriced, never set to zero.

Comparing a single giant Azure VM with a whole mainframe—or pricing three AKS nodes and calling the result complete TCO—is invalid. Real costs have at least three layers: **scalable computation**, **durable authoritative data**, and **branch network plus operations/continuity**. Compare cost per million **durably committed, oracle-correct transfers**, not headline VM-hour cost. Every recorded monetary value has its source, observation date, currency and exclusions.

## Three candidate infrastructure blueprints

| Architecture | Candidate topology (NOT approved sizing) | Likely bottleneck |
|---|---|---|
| **Mission-critical on-premises** | Two or more dense physical x86 nodes (e.g. EPYC), HA SQL boundary, enterprise NVMe, 25/100 GbE, replication and secondary site, accessed through the bank WAN | Durable log, locks, NUMA, NIC, replica acknowledgement, N-1 maintenance |
| **Azure transactional** | .NET 10 in VMs/AKS/App Service as justified, SQL HA near the application, Private Link/ExpressRoute, regional entry/gateway as appropriate, end-to-end tracing | VM and quotas, VM **and** disk IOPS, log throughput, failover RTO, gateway, zone dependency |
| **Hybrid coexistence** | Authorised facade before preserved CICS/Db2, new capabilities on Azure/on-premises, gateway contracts, outbox and unambiguous ledger ownership | Cross-site chattiness, distributed commits, backlog, reconciliation and duplicated business semantics |

I would not put the application in one region and require a synchronous ledger commit across an ocean. If every transaction must coordinate between both sites, that **latency enters p99 and caps achievable throughput**, however many cores are added. Aim to reduce serial dependencies, co-locate authoritative data with critical compute and partition by domain without breaking accounting boundaries. On-premises also needs a second site and an actual node-loss exercise.

## A branch-centred acceptance contract

Before comparing, choose an approved representative sample: nearby urban branch, regional branch, international branch, degraded link and operation after failover. Do not assign RTT or SLA from an architecture desk. Measure **p50/p95/p99 per operation and per site**, distinct from host-internal CICS time, plus packet loss, jitter, DNS, TLS, session, locks, durable log, replica acknowledgement, backlog age, timeouts and retries.

Run with **online + batch**, hot keys, replication and peaks; repeat with **injected** 0.1% and 0.5% loss (not observed production rates), configured jitter and removal of a link or instance. Every run must persist source SHA, region/route config, client/server versions, distributions, cost and independent oracle verdict. [Azure Connection Monitor](https://learn.microsoft.com/en-us/azure/network-watcher/connection-monitor-overview) can observe RTT and loss, but a TCP/ICMP probe **cannot replace** measured business-transaction latency.

Accept only when **business results, durable completion, recovery and perceived latency** meet the approved contract—not when isolated TPS looks impressive. A fast network with a wrong ledger is useless; a correct ledger with unacceptable branch response also fails.

## Executed Azure demonstration: evidence, not a capacity claim

The [first real Azure campaign](../../../evidence/runs/azure-single-vm-2026-11-07.json) deployed the Bicep into a dedicated resource group in the author's authorized subscription. West Europe rejected new resources for this subscription despite available vCPU quota. That failed validation was retained; North Europe passed ARM validation and What-If, with 17 creations and no modifications or deletions of existing resources. The actual runner was one private `Standard_D4s_v5` VM, using Podman, PostgreSQL 16.13, .NET SDK 10.0.100 and GnuCOBOL 3.1.2. The VMSS had zero workers.

The following are **executed observations**, not planned tests or mocked infrastructure:

- **Core:** 58 COBOL/.NET cases and ten gate controls. After downloading the original SQLite databases, the host-side independent audit accepted nine correct databases and rejected the deliberately corrupted one. The rounding mutant was blocked on `C003`.
- **E1 PostgreSQL:** 11 Python controls, ten .NET controls, 16 sequential parity cases and the eight-case/960-transfer worker matrix passed. The independent ledger oracle rejected deliberate posting corruption.
- **E2:** six matched workload runs committed 600 transfers. Two silo processes and a separate client recovered after an actual secondary-process `SIGKILL`, with both development and PostgreSQL ADO.NET membership. Seven independent SQL invariants passed after recovery. Two additional cases exercised termination before and immediately after COMMIT.
- **M2:** all 20 REST/gRPC, uniform/hot and 1/2/4/8/16-process cases passed. Every case had 256 durable commits, 512 postings and 256 outbox entries; the independent negative control detected corruption and verified restoration.

The original source archives, file hashes, Azure instance metadata, runtime logs, SQL dumps and downloaded evidence are retained. The first M2 attempt passed its numerical controls but still emitted inherited labels claiming a GitHub runner and denying Azure execution. Those raw files were not corrected retroactively: the report producer was fixed and a separate full repeat passed with explicit Azure host and source-archive provenance. No GitHub Actions were launched.

**Cloud hosting does not turn a single-host test into E3 acceptance.** M2's replicas were processes on the same VM; there was no cross-machine failover, WAN/TLS equivalence, approved bank capacity contract or mainframe comparison. E4 still had no live-agent campaign. After downloading the evidence, the runner was verified **deallocated**, with zero worker instances. Its disk, NAT gateway, public IP and storage remained billable. A monthly budget alert is not a spending cap, and actual billed cost was not invented from public price meters.

## An additional Azure transport run and an explicit E3 refusal

The [8 November Azure M1 run](../../../evidence/runs/azure-m1-2026-11-08.json)
compared REST/JSON and gRPC/Protobuf at concurrency 8 and 32: eight alternating
rounds of 2,500 requests, **20,000 measured replies, zero response errors**.
Both negative controls passed. Sources and per-round latencies were retained;
the North Europe runner was deallocated after download.

The traffic remained **HTTP/2 without TLS over loopback**, with no durable
ledger. Azure identifies the host, not a WAN path. These short closed-loop
observations neither establish banking TPS nor a universal transport winner.

The [reproducible E3 preflight](../../../evidence/runs/e3-readiness-2026-11-08.json)
returned `INCONCLUSIVE / BLOCK`, exit 3: all 14 required capacity fields
were empty, status `UNCONFIGURED`. The
[command](../../../lab/docs/EXPERIMENT_PROTOCOL.md) retains the contract hash
and missing prerequisites, without inventing targets. This is not a load
experiment: even a populated contract requires external review and comparable
Azure, on-premises and mainframe measurements.

## E1–E4 on the Azure runner: four different demonstrations

The [8 November follow-up](../../../evidence/runs/azure-e1-e4-2026-11-08.json)
repeated PostgreSQL E1 and extended Orleans E2 after hardening evidence
collection. E1 again passed its 960-transfer matrix; E2 passed both membership
providers, 600 matched-workload transfers and controlled process failures.
Logs, database dumps and cleanup now have separate exit codes: losing evidence
cannot silently turn a run green.

E3 then executed an **exploratory open-loop** ledger trial, not just the earlier
readiness check. Three fixed phases offered 20, 40 and 60 requests/s for six
seconds each. Of **720 scheduled offers, 668 committed**, 48 failed to connect
and four missed their schedule. A service process was killed at eight seconds
and restarted at ten; the replacement subsequently committed work. All seven
accounting checks passed, and deleting a posting triggered three violations
before restoration. Every failed or missed offer remains in the denominator.
The ACK-only p99 is not the p99 of all offered work, and the nominal-window
commit rate is not a sustained capacity ceiling.

All services and the disposable database shared one VM. The authoritative
snapshot was captured before removing the trial's private schema; the later
database dump does not restore that removed schema. Neither process recovery
nor `synchronous_commit=on` proves physical-node HA, a bank RPO/RTO or a
mainframe comparison. The original capacity contract remains unconfigured.

E4 also moved **candidate execution** to Azure: rootless Podman, supervisor UID
1000, no candidate network or credentials, and read-only protected inputs.
It replayed the existing real model response from chapter 29, rather than
counting another inference. The candidate passed 16 self-tests and 58 frozen
cases; qualification rejected three mutants and denied three protected writes.
The first attempt failed because the nonroot process inherited a root-private
working directory. That original is retained beside the corrected run, not
rewritten. Azure instance metadata, source archives and the separate replay
input digest bind the observed execution to its inputs.

## What Azure actually shows

The following are **real projected Azure CLI outputs**, captured on
**8 November 2026, 10:03 UTC**, not portal screenshots or recreated UI.
The [capture manifest](../../../evidence/runs/azure-cli-2026-11-08/capture.json)
retains all six exact commands, timestamps, exit codes and stdout hashes; the
[resource inventory](../../../evidence/runs/azure-cli-2026-11-08/resources.json)
identifies the deployed infrastructure. The
[read-only collector](../../../scripts/azure/capture-book-evidence.ps1) lets
readers repeat this against their own deployment without starting any VM.

The [deployment response](../../../evidence/runs/azure-cli-2026-11-08/deployment.json)
reports infrastructure success, **not application or experiment correctness**:

```json
{
  "name": "book-experiments",
  "state": "Succeeded",
  "timestamp": "2026-11-07T23:17:25.358088+00:00"
}
```

The [runner response](../../../evidence/runs/azure-cli-2026-11-08/runner.json)
shows the resource and its state after collecting the experiments:

```json
{
  "location": "northeurope",
  "name": "bookev1107-runner",
  "size": "Standard_D4s_v5",
  "statuses": [
    "ProvisioningState/succeeded",
    "PowerState/deallocated"
  ]
}
```

The [scale-set response](../../../evidence/runs/azure-cli-2026-11-08/workers.json)
records capacity zero, and its separate instance query returns an empty array.
The [storage response](../../../evidence/runs/azure-cli-2026-11-08/storage.json)
reports HTTPS-only access, minimum TLS 1.2, shared-key access disabled and
anonymous blob access disabled. Those settings do not certify every permission
or network path. A deallocated VM also does not mean a zero bill: managed disk,
NAT, public IP and storage remain. This dated control-plane capture complements,
but cannot replace, the original workload artifacts and independent oracles.

## Our evidence: what exists and what does not

This branch does contain [versioned E1a/E1b observations](../../../evidence/runs/README.md): real `40P01` deadlock, `40001` serialization, a corruption-detecting independent oracle and partial .NET 10/Npgsql parity on PostgreSQL. It also contains the Azure records described above—one D4s_v5 VM, synthetic workloads, every run downloaded and hashed—registered as `demonstrated_not_accepted` in the [evidence matrix](../../../docs/EVIDENCE.md).

**There is not yet any benchmark on IBM z17, LinuxONE, Dorado 8590, Azure Mdsv3 or EPYC**, no second site, no measurements from a real distant branch, and the capacity contract is still unconfigured. The evidence registry must not promote those comparisons without reproducible load, approved SLOs and on-site measurements. The Azure runs tell us the mechanisms work where we put them; they do not tell us how the bank's month-end behaves.

> The winning architecture is not the one that runs fastest inside the data centre. It is the one that commits the correct operation and delivers the answer back to the branch even when the worst WAN day meets the month-end close.

---

[← Chapter 25 · Azure or a huge machine at the customer's site](25-azure-or-a-huge-machine-at-the-customer-s-site.md) · [Contents](../README.md) · [Part VI · The lab →](../part-6-lab/README.md)
