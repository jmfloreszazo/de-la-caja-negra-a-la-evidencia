**English** · [Español](../../es/parte-5-capacidad/25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md)

[← Chapter 25 · Azure or a huge machine at the customer's site](25-azure-or-a-huge-machine-at-the-customer-s-site.md) · [Contents](../README.md) · [Part VI · The lab →](../part-6-lab/README.md)

# Chapter 25 bis · Infrastructure versus a current mainframe: on-premises, Azure and the branch network

> **Thesis.** You do not replace a mainframe with a box that has more cores. You replace an entire operational service: transactional computing, I/O, isolation, durable commit, continuity and the response seen by a branch that may be thousands of kilometres away. Equivalence is an end-to-end test, not a marketing-specification comparison.

This chapter supplements [chapter 25](25-azure-or-a-huge-machine-at-the-customer-s-site.md) with named market references and a falsifiable architecture protocol. **Manufacturer data checked in October 2026; our measured performance against those machines: none.**

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

## Dated prices, not a deceptive vCPU-to-mainframe TCO

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

## Our evidence: what exists and what does not

This branch does contain [versioned E1a/E1b observations](../../../evidence/runs/README.md): real `40P01` deadlock, `40001` serialization, a corruption-detecting independent oracle and partial .NET 10/Npgsql parity on PostgreSQL. **There is not yet any benchmark on IBM z17, LinuxONE, Dorado 8590, Azure Mdsv3 or EPYC**, nor measurements from a real distant branch. The evidence registry must not promote those comparisons without reproducible load, approved SLOs and on-site measurements.

> The winning architecture is not the one that runs fastest inside the data centre. It is the one that commits the correct operation and delivers the answer back to the branch even when the worst WAN day meets the month-end close.

---

[← Chapter 25 · Azure or a huge machine at the customer's site](25-azure-or-a-huge-machine-at-the-customer-s-site.md) · [Contents](../README.md) · [Part VI · The lab →](../part-6-lab/README.md)
