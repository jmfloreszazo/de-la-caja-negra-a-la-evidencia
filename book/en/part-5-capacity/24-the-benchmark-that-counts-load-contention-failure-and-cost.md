**English** · [Español](../../es/parte-5-capacidad/24-el-benchmark-que-vale-carga-contencion-fallo-y-coste.md)

[← Chapter 23 · Concurrency that makes use of the machine](23-concurrency-that-makes-use-of-the-machine.md) · [Contents](../README.md) · [Chapter 25 · Azure or a huge machine at the customer's site →](25-azure-or-a-huge-machine-at-the-customer-s-site.md)

# Chapter 24 · The benchmark that counts: load, contention, failure and cost

> [!IMPORTANT]
> **Chapter thesis.** A banking benchmark needs more than one number: uniform, skewed and mixed loads, fault injection, cost, and a way of generating load that does not hide congestion. A TPS improvement that loses guarantees is not an improvement.

A banking benchmark needs more than one number. I would define three families of load. **Uniform**: operations spread over many accounts, favourable to parallelization. **Skewed**: a small proportion of accounts concentrates much of the traffic, revealing hotspots. **Mixed**: online transactions, queries and batch at the same time, reproducing competition for CPU and storage. The proportions must be derived from telemetry or declared synthetic.

I would measure sustained and peak TPS, p50/p95/p99, batch time, error rate, aborts and retries, CPU and memory consumption, database waits, network, IOPS, cost per million operations and recovery time. Queues matter: an API can keep answering quickly the requests it accepts while losing or delaying the rest. We must account for offered, completed and rejected traffic.

The second half is **fault injection**: killing the process before and after the commit, cutting connectivity to the database, duplicating messages, delaying responses, changing the leader, retrying transfers, restoring from a checkpoint and checking reconciliation. Results are published with code version, hardware specification, topology, data seed, scripts and configuration. A pretty dashboard without those details is just another demo.

Agents could optimize the implementation or propose partitions, but their changes go through exactly the same oracles again. They must not quietly touch the reference data or lower the isolation to get more throughput. **A TPS improvement that loses guarantees is not an improvement**.

## From a useful benchmark to a misleading one

For capacity acceptance I would use a generator with a controlled arrival rate and measure from the scheduled send time. A closed-loop client involuntarily reduces pressure when the server slows down and can hide the real accumulation of work, a phenomenon known as coordinated omission.

I would record requests offered, admitted, committed, rejected by the business, failed and pending. Percentiles must show which population they include. I would not discard timeouts to improve the p99. A high throughput of rejections does not prove the capacity to commit transfers.

I would separate warm-up from measurement, repeat runs and keep their variability. The recovery load and the batch mix would have their own tests. Only then could we state which architecture approaches the mainframe's operational commitment and which differences remain open.

It is the same discipline I imposed on myself when comparing two agents hosted on Microsoft Foundry, one on .NET 10 and the other on Python: same region, same quota, same resource envelope and a single real variable, the runtime. A benchmark that changes two things at once measures nothing, and the "how I measured it" is where a benchmark wins or loses its credibility [45].

## An example you can run: coordinated omission

Coordinated omission is easier to understand by seeing it. The lab includes a deterministic simulation, with no network, no real waiting and no randomness: a server with one millisecond of service time that stops for 500 ms just once —think of a long lock, a log flush or a garbage collector pause. We measure it twice. In a closed loop, one client sends the next request when it receives the previous response. In an open loop, requests are scheduled at 500 per second and latency is measured from the moment they *should* have been sent, as wrk2 does [39].

**Listing 24.1 · tools/coordinated_omission_demo.py** — *Executed · simulation*

```text
$ python3 tools/coordinated_omission_demo.py
Same server, one 500 ms stall at t=4.0s, 1 ms service time.

mode                          req    req/s     p50     p95      p99      max  >100ms
------------------------------------------------------------------------------------
closed-loop (1 client)       9500    950.0     1.0     1.0      1.0    501.0       1
open-loop (500/s)            5000    500.1     1.0   251.0    451.0    501.0     401
```

![Figure 24.1 · Maximum latency per 100 ms interval in the simulation. In red, the open loop: the queue takes half a second to drain. In blue, the closed loop: a single spike and nothing else.](../../figures/en/omission_chart.png)

*Figure 24.1 · Maximum latency per 100 ms interval in the simulation. In red, the open loop: the queue takes half a second to drain. In blue, the closed loop: a single spike and nothing else.*

The closed loop reports a p99 of one millisecond and almost twice the throughput. It does not lie about the requests it measured; it lies by omission, because its only client was waiting while the server was stopped and stopped offering load. The open loop reveals that 401 requests exceeded 100 ms. That is the congestion a real customer would see at month-end close.

It is a simulation, not a measurement: it shows why a capacity trial must control the arrival rate and measure from the scheduled send.

> **A high throughput of rejections does not prove the capacity to commit transfers.**

---

[← Chapter 23 · Concurrency that makes use of the machine](23-concurrency-that-makes-use-of-the-machine.md) · [Contents](../README.md) · [Chapter 25 · Azure or a huge machine at the customer's site →](25-azure-or-a-huge-machine-at-the-customer-s-site.md)
