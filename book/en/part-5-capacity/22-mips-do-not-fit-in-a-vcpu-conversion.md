**English** · [Español](../../es/parte-5-capacidad/22-los-mips-no-caben-en-una-conversion-de-vcpu.md)

[← Part V · Capacity: MIPS, concurrency and platform](README.md) · [Contents](../README.md) · [Chapter 23 · Concurrency that makes use of the machine →](23-concurrency-that-makes-use-of-the-machine.md)

# Chapter 22 · MIPS do not fit in a vCPU conversion

> [!IMPORTANT]
> **Chapter thesis.** A MIPS figure gives context about an environment; it is not an amount of business work we can spread across x86 cores. The comparison that matters is expressed in committed operations, latencies per class, batch windows and recovery times.

## What we are trying to match

The question that worries me most when taking a workload off a mainframe is not whether the new program compiles. It is whether it can sustain operations when close, the activity peak and a failure arrive at the same time. The old system may have been solving that combination for years through an integration the application barely makes visible.

A MIPS figure offers a reference about an environment. It does not represent a universal amount of business work we can spread across vCPUs of another architecture. IBM explains that its LSPR ratios depend on specific workloads and configurations, and that I/O, software and the characteristics of the work can change real results [14]. I would use that reference to put capacity in context, never as a purchasing table for x86 servers.

The comparison I need has business units: confirmed transfers per second, queries with their latency, policies processed within the window, pending incidents and recovery time. Each measure must preserve the semantics. Confirming a transfer in memory and returning HTTP 200 is not the same as confirming its durable record with the agreed replication policy.

Nor does an average tell the whole story. We can increase total throughput and badly worsen the experience of a high-contention account. We need percentiles per type of operation, errors, business rejections, retries and queue age. The peak of one class must not hide inside the average of cheaper ones.

## What changes when we change architecture

I would not propose sizing by saying "one MIPS is so many operations per second on x86". MIPS is a metric dependent on the platform, the definition used and the characteristics of the workload; MSU is used in IBM environments for measurement and capacity/licensing, but it is not a universal unit of cloud CPU either. The relationship between instructions, latency and I/O changes when we transform the architecture. A local `CALL` can end up as HTTP. A Db2 access in the same environment can become network and TLS. An optimization of packed decimals can become another representation and another execution path.

## Recovering a workload footprint

Before sizing I would ask the mainframe team for a representative capture of activity and its conditions. IBM documents RMF tools and CICS monitoring records that allow observing resources, CPU and waits per transaction [15]. The systems team must interpret that data: an LPAR with capped capacity, a particular mix of engines and specific WLM priorities do not reduce to the machine's nominal CPU.

The footprint must distinguish interactive operations, batch, queries and work delegated to other subsystems. It must also identify the active data volume, access distributions, hot accounts and commitments between processes. The hour of highest CPU does not have to be the hour of worst latency.

I would keep normal days and critical periods, according to the business: close, month-end or exceptional events. I would not ask for a universal observation period. I would ask for evidence that the set covers the situations for which we are going to commit capacity.

A useful inventory for sizing contains the following:

| Dimension | Evidence we need | Decision it enables |
|---|---|---|
| Work | Rates per operation and request sizes | Mix and load generator |
| CPU | Consumption and distribution per class | Compute budget |
| Waiting | Locks, log, I/O and dependencies | Priority bottleneck |
| Data | Active volume, cardinality and skew | Memory and indexes |
| Batch | Dependencies, partitions and duration | Critical path and window |
| Recovery | Failures, restart, agreed RTO and RPO | Redundancy and tests |

![Figure 22.1 · From the mainframe to a candidate configuration: the workload footprint feeds a demand model that only a trial can confirm.](../../figures/en/capacity_flow.png)

*Figure 22.1 · From the mainframe to a candidate configuration: the workload footprint feeds a demand model that only a trial can confirm.*

## A calculation that helps without pretending to be precise

Suppose, as an exercise, that a test on the target measures one millisecond of application CPU per operation and that we need 8,000 operations per second. That demand consumes eight seconds of CPU per second. At an illustrative sixty per cent utilization target we would need roughly fourteen effective cores for that parallelizable part of the application.

The calculation does not yet include the database, garbage collection, encryption, instrumentation, imbalances, reserves or redundancy. Nor does it allow replacing the millisecond measured on the target with a millisecond observed on z/OS. The goal is to build a model we can correct with measurements, not to pretend sizing is finished.

Another useful relationship connects throughput, mean duration and work in progress. At 10,000 operations per second and a stable mean duration of 25 milliseconds, there are about 250 operations in progress on average. That does not mean we should open 250 SQL connections. Duration changes when contention increases, and part of that work may be waiting outside the database.

Separating CPU demand from waiting and I/O avoids buying power to solve a queue caused by a serialized resource. A bigger server can be a solution; first we need to show which resource is limiting capacity.

> **A bigger server can be the solution. First you have to show which resource is limiting capacity.**

---

[← Part V · Capacity: MIPS, concurrency and platform](README.md) · [Contents](../README.md) · [Chapter 23 · Concurrency that makes use of the machine →](23-concurrency-that-makes-use-of-the-machine.md)
