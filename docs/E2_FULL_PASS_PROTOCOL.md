# E2 — Protocol for a global distributed scientific PASS

**Protocol v1.0 · 4 November 2026.** This is a **future campaign design, not an executed result**. The bounded hosted-CI E2 campaign is closed; the scientific status remains `partially_verified`. [Spanish version](E2_FULL_PASS_PROTOCOL.es.md) · [E2 closure](E2_CLOSEOUT.md).

> Closing [issue #8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) as `not_planned` closed the remaining work for the **bounded campaign**, not the unsatisfied scientific claims. Any global PASS requires a **new, separately authorized distributed campaign**, its own issue, infrastructure, evidence and independent decision. This protocol is not an active E2 backlog item.

## 1. Define the claim, its scope, and the result vocabulary

**E2-TECH-PASS** means that, against a preregistered and approved technical workload, Orleans grains coordinating an authoritative PostgreSQL financial transaction demonstrate functional correctness, seven independent ledger invariants, offered-load performance, repeatability, natural grain lifecycle, and bounded recovery/durability across independent silo, network, host and database failures.

**E2-BANK-PASS** requires *additional* authorized incumbent traces, customer-owned business semantics, approved production SLOs, target-environment security/operations, independent business acceptance and TODM governance. A synthetic technical PASS is not a banking deployment approval, mainframe equivalence or MIPS-to-vCPU sizing proof.

**PASS:** Every mandatory applicable X00–X08 gate is independently evidenced, repeated and within preregistered thresholds; all negative controls reject deliberate faults. **FAIL:** A demonstrated financial/safety violation, acknowledged write lost outside the agreed RPO policy, contradictory primary writers, mandatory service threshold violation, or invalid negative control. **INCONCLUSIVE:** Missing evidence, unsupported topology, unbounded clock uncertainty, missing approved threshold or unresolved mandatory observation. **BLOCK:** Do not upgrade `evidence/claims.json`, issue a production approval, or promote a scientific claim without the independent gate decision.

A project team may approve a synthetic contract for **research-level TECH-PASS**; only an actual customer's approved contract can support customer-specific BANK-PASS. Historical FAIL and INCONCLUSIVE runs remain unchanged.

## 2. Approved input contract — mandatory before infrastructure testing

The current [`lab/performance-contract.json`](../lab/performance-contract.json) is `UNCONFIGURED`. Do **not** guess thresholds or relabel null values. Freeze a versioned, signed, immutable **per-campaign copy** with:

| Required area | Preregistered values |
| --- | --- |
| Scope and authority | Campaign ID, TECH/BANK claim, responsible owner, independent reviewer, budget, safety authorization and approved acceptance decision rule |
| Reproducibility | Exact source and oracle SHA, image digests, .NET/Orleans/PostgreSQL versions, effective runtime and DB configuration |
| Business/workload | Synthetic or approved real traces, initial balances, transfer mix and sizes, rejection profiles, fixed IDs/seeds, uniform, 5%-hot, single-hot and crossed transfers |
| Service contract | Offered requests/s, minimum **correct durable committed** transfers/s, *all-offer* end-to-end p99, error and deadline budget, run duration, warmup and drain |
| Correctness | Seven immutable SQL/accounting predicates, ACK/COMMIT/UNKNOWN meanings, stable operation ID, conflicts, double posting and idempotent recovery rules |
| Fault and durability objectives | Effective SQL/WAL/replication policy, RPO/RTO, surviving-host capacity requirement, tolerance for ambiguous outcomes and outage intervals |
| Statistics and provenance | Fresh repetitions, reporting/aggregation policy, actual clock offset/uncertainty, physical fault domains, resource quotas and trace retention |
| Security | TLS, identities, approved endpoint/host allowlists, test-only secrets, isolated control plane and permitted fault targets |

No RPS, p99, RPO or RTO number in this document is a customer-approved threshold. The acceptance contract must exist **before results are observed**. A future external claim cannot be established by silently modifying this file after measuring.

## 3. Physical reference topology

```text
    Independent load host A ---+
                               +-- TLS / gateways --- Orleans silo A (fault domain A)
    Independent load host B ---+                 +--- Orleans silo B (fault domain B)
                                                      |
                                           authoritative transactions
                                                      |
                                          PostgreSQL primary (domain C)
                                                      | replication policy
                                          PostgreSQL standby (domain D)
                                                      |
                                       independent quorum/fencing control

                  Separate fault controller / clocks / observability / SQL oracle
```

- Use **two actually independent physical fault domains** for silo hosts, not two containers on one runner or two VMs sharing an unacknowledged host/storage failure domain. Record anti-affinity, node/zone identity and actual placement.
- Use PostgreSQL with independent primary and standby domains, observed replication and safe primary-election/fencing. A managed HA offering qualifies only when its real failover behavior, durability policy and domains are evidenced. An HA label alone is not proof.
- Keep the load generator away from application/DB bottleneck resources, and prove it can sustain the offered schedule against a calibrated sink. Two generators are preferable under high demand.
- Use an observation/control plane that survives the injected network fault; capture both-end packet streams, DB state, complete process/activation generations and clock uncertainty.
- Record effective Orleans ServiceId, ClusterId, ADO.NET membership, advertised addresses, TLS, DNS, CPU/memory/IOPS and database configuration. Do not use development membership to infer physical HA.

**Illustrative, not a procurement requirement:** 2+ silo nodes, 2 database hosts plus a quorum/fencing mechanism, 1–2 load nodes and an isolated control/audit domain. If independent domains cannot be proven, **limit the claim** to process/network behavior.

## 4. Actual source and infrastructure changes needed

Add a separate proposed `lab/e2_external/` harness (the path **does not exist just because it is specified here**). Keep frozen historical runs and original accounting oracle unchanged.

| Proposed unit | Required change | Mandatory evidence |
| --- | --- | --- |
| `contract.py` / preflight | Read and hash approved contract, validate all non-null thresholds, source/images, allowed hosts, effective fault domains, credentials, TLS, clock and sink calibration. Fail closed on unknown fixture | Signed/config-bound `preflight.json` READY/FAIL/INCONCLUSIVE |
| `remote_driver/` | New **open-loop**, external-endpoint driver recording every scheduled offer, admission, dispatch, deadline, ACK/reject/UNKNOWN and SQL outcome; monotonic schedule, bounded retries using original operation ID | Raw per-offer JSONL, including unserved and late offers |
| `distributed_fixture/` | Replace local `podman exec`, inspect, file-sharing and process assumptions **in the new harness** with authenticated host controllers and explicit process generations. Do **not** relax fixed local DSN checks in [B05 run.py](../lab/e2_b05_dispatch/run.py) or alter [directed probe](../lab/e2_account_directed/run_probe.py) history | Host/runtime/source/image manifest and complete original stdout/stderr |
| `activation_observer/` | Observe **normal AccountGrain lifecycle**, key, activation ID, silo, membership version, BEGIN/END/errors, without pre-invoke delay or artificially placed actors | Complete natural placement and overlap/relocation traces |
| `metrics/` | Correlate offered/admitted/committed operations, pool acquisition, SQL waits/locks/WAL, CPU, GC, memory, queues, network loss, gateway results; use OpenTelemetry where appropriate | Time-bound raw service + infrastructure metrics |
| `fault_controller/` | Safely inject separate silo process, directional network, entire host/zone and SQL-primary failover faults with allowlists and verified restoration | Exact fault commands, timestamps, both-side PCAP and before/after state |
| `sql_oracle/` and `auditor/` | **Reuse unchanged seven independent financial predicates**, deliberate corruption negatives; correlate offered IDs, client ACK, persisted COMMIT, SQL membership, failover and unresolved UNKNOWN cases | Oracle failures on corrupt controls; gate-specific independent verdict |
| `runner/` and `archive/` | Unique, immutable attempt directories, source/image digests, complete negative and failed history, raw artifact hashing and review signatures | Attestable source→run→evidence chain |

Use isolated reproducible dedicated/self-hosted infrastructure (IaC or documented manual allocation) and a manually authorized live campaign. GitHub Actions may **orchestrate** the environment and run schema/unit CI, but a green workflow on several ordinary hosted runners does not prove physical HA.

## 5. Mandatory X00–X08 acceptance matrix

| Gate | Experiment to execute | What must be established |
| --- | --- | --- |
| **X00: contract/provenance** | Verify prior approval, source/oracle/images, physical topology, time sync with uncertainty, TLS/identity and load-generator headroom | Full, reproducible, approved and correctly bounded fixture; else INCONCLUSIVE |
| **X01: parity and accounting** | Identical seeded vectors through direct SQL and Orleans: overdraft race, crossed transfers, duplicates, conflicting IDs, timeout and UNKNOWN | Matching contractual outcomes, one accepted financial effect per ID, 7/7 independent SQL predicates; negative corruption rejected |
| **X02: natural placement** | Ordinary AccountGrain join/leave/activation with both client gateways and complete observed generations, **no pre-invoke hold** | Natural lifecycle/relocation observable with definitive time/process identity |
| **X03: network partitions** | A→B and B→A one-way cuts and bidirectional isolation while both silo processes are observed alive; independent SQL audit | No duplicate authoritative effects or contradictory accepted outcomes; all ambiguous IDs reconciled. Do **not** infer global single-activation exclusivity during partitions |
| **X04: unassisted recovery** | Kill silo process, lose independent silo host and exercise a prolonged partition **without manual silo recreation**, then replay same IDs and send new work | Satisfies contracted RTO/degraded service and 7/7 invariants. A manually recreated silo is **ASSISTED**, not an unassisted PASS |
| **X05: sustained load/capacity** | Direct vs Orleans with same SQL transaction/durability/resource limits; 1/2/4/8/16 silo configurations when feasible; uniform, hot, single-hot and crossed offered load, step sweeps | Agreed correct durable COMMIT TPS, all-offer p99 and miss/error/deadline rates; repeated demonstrable bottleneck. Linear scaling is **not** a required universal property |
| **X06: physical HA/SQL failover** | Actual independent host/zone failure, separately PostgreSQL-primary outage, leader fencing/standby recovery and ACK/UNKNOWN reconciliation | Effective contracted RPO/RTO/one-node-lost service met, no contradictory writers, no disallowed loss of acknowledged operations, 7/7 SQL invariants |
| **X07: negative oracle integrity** | Corrupt postings, duplicate/conflict ID conditions, remove manifest or trace, independently inspect persisted SQL | Every deliberate invalid state is rejected, never inherited as PASS from a previous attempt |
| **X08: replication/review** | Fresh repetitions in preregistered order, no best-run selection, review all raw traces/source/digests/clock bounds | Complete repeatable evidence reviewed independently, signed decision and explicit declared scope |

### Important measurement boundaries

**Activation and partitions:** both processes being *alive* is not proof that both served concurrent transactions. Record process generations, activation IDs, incoming call BEGIN/END and both ends of network faults. If clocks cannot prove actual positive overlap after subtracting uncertainty, classify the overlap witness INCONCLUSIVE, even if financial SQL correctness has independent evidence. Concurrent activation does not automatically mean double financial posting; the SQL effects decide.

**SQL durability:** capture *effective* `synchronous_commit`, `synchronous_standby_names`, WAL, replication lag, timeline and fencing. Asynchronous replication can lose acknowledged updates on failover; do not assert RPO=0 for an incompatible policy. Audit operations acknowledged before failure, UNKNOWN during failure and replay after promotion. A successful endpoint change does not alone demonstrate durable recovery.

**All-offer service p99:** time from each **scheduled send** to a valid response, including admission delay, queue and timeouts, rather than computing a survivor-only ACK percentile that hides overload. Count missed and deadline-failed offers in the service denominator. For timed-out offers, report bounded/censored latency and the contractual deadline failure separately. Prove load generator headroom and measure Npgsql pool wait before attributing a bottleneck to Orleans/CPU.

**Time and statistics:** synchronize wall clocks with measured offset/uncertainty before and after runs, preserve host-local monotonic intervals and avoid comparing cross-host timestamps without bounded uncertainty. Re-run fresh, varied configurations and retain every FAIL/INCONCLUSIVE. The original source's artificial directed filters are diagnostics, **not** natural lifecycle evidence.

## 6. Proposed execution phases (not yet executed)

| Phase | Deliverable | Exit criterion |
| --- | --- | --- |
| **P0** | Approved TECH contract, synthetic data, security/fault authorization, budget | X00 preflight READY, scope explicitly bounded |
| **P1** | Distinct physical hosts/domains, PostgreSQL HA+fencing, TLS/control/telemetry | Proven independent identities and effective SQL durability settings |
| **P2** | External driver/fixture/oracle/negative controls implemented | X01 and X07 prove integrity before any performance claim |
| **P3** | Reproducible direct/Orleans baseline and ordinary lifecycle | X01, X02 and complete telemetry |
| **P4** | One-way/bidirectional cuts, SIGKILL, long partition and **natural** recovery | X03/X04 independent financial and temporal evidence |
| **P5** | Offered-load and silo-count matrix, hot-key limits and bottlenecks | X05 thresholds and repetitions |
| **P6** | Silo host/zone and SQL failover with independent reconciliation | X06/X07 complete |
| **P7** | Independent raw-evidence audit and acceptance decision | X08; only then consider scoped TECH-PASS |

**Suggested initial design, not an acceptance standard:** at least three **fresh** repetitions/configuration, five-minute warmup, fifteen-minute steady interval and bounded drain, varied preregistered order. Retain warmup and overload; add long soak or more repetitions if variability and the signed contract warrant it. Never choose acceptance thresholds after viewing the data.

**Safety:** faults only against labeled, expendable, explicitly approved test resources; use an endpoint allowlist, isolated secrets/control plane, restore/abort steps and an authorized operator. Real storage power-loss validation requires a purpose-built disposable hardware/storage setup, not a shared environment.

## 7. Evidence directory and independent reporting

Suggested layout (**schema proposal; no results implied**):

```text
evidence/external-e2/<campaign-id>/<run-id>/
  contract-approved.json       # Signed scope and thresholds
  provenance.json              # Git SHA, oracle, tool and image digests
  topology.json                # Hosts, physical domains, SQL replicas and quorum
  clocks.json                  # Observed offsets/uncertainty
  offers.jsonl                 # EVERY offered operation and transition
  client-logs/                 # Original client stdout/stderr/traces
  silo-logs/                   # Every host, process and activation generation
  network/                     # Fault commands, PCAP both ends, counters
  postgres/                    # WAL, replication, membership, snapshots
  metrics/                     # CPU, GC, queue/pool/SQL/network observations
  oracle.json                  # Seven predicates, negative control and ID audit
  assessment.json              # X00–X08 PASS/FAIL/INCONCLUSIVE
  manifest.sha256              # Exact immutable evidence inventory
  review.md                    # Independent reviewer and scoped verdict
```

Large original artifacts may be stored outside Git **only with** durable verifiable URLs, SHA-256 and retention policy; commit the immutable evidence index. No missing or failed attempt may be silently discarded or overwritten. Service totals must be reproducible from **raw offered IDs, acknowledgements and SQL commits**, not only from service-provided summaries.

## 8. Independent PASS rule

```text
if the approved contract is absent/unconfigured:      INCONCLUSIVE
if a mandatory observation or original is missing:    INCONCLUSIVE
if a financial/safety invariant is violated:          FAIL
if a contractual service/durability SLO is violated:  FAIL
if a required negative control incorrectly passes:   FAIL
if time/domain certainty prevents a mandatory claim:  INCONCLUSIVE
if any mandatory gate X00-X08 is not PASS:             FAIL or INCONCLUSIVE
else:                                                  E2_TECH_PASS
```

All required repetitions, rather than only averages, are assessed against the preregistered rule. Distinguish ACK, COMMITTED, rejected business operation, timed-out offer and UNKNOWN; compare failures against the approved RPO semantics. An auditor can establish financial correctness while an activation-overlap claim remains inconclusive.

The independent reviewer signs the result and its limits. Only **after** reviewing complete originals may a separate decision propose an update to `evidence/claims.json`. Do not rewrite historical `partially_verified` attempts or reframe the closed #8. **E2_TECH_PASS ≠ E2_BANK_PASS ≠ permission to publish or deploy**, and TODM G2/G6 require their own authority.

## 9. Explicit future work, not active E2 tasks

1. Approve an immutable quantitative TECH contract and supply genuine distributed resources.
2. Authorize a separate issue/PR for the external harness, remote driver, lifecycle observations and audit.
3. Establish independently tested fault domains, PostgreSQL failover/fencing and effective durability guarantees.
4. Run and archive X00–X08, including negative and failed attempts.
5. Require independent acceptance before any scoped global PASS.

The existing E2 campaign and issue #8 remain **closed**. Book, brownfield and the rest of the roadmap are not blocked. [Current E2 closeout](E2_CLOSEOUT.md) · [hosted-CI limitations and prerequisite code changes](EXTERNAL_VALIDATION.md).

## 10. Product references (not experimental evidence)

- [Orleans documentation](https://learn.microsoft.com/en-us/dotnet/orleans/): grain lifecycle, clustering, placement and observability context.
- [PostgreSQL high availability and replication](https://www.postgresql.org/docs/current/high-availability.html).
- [PostgreSQL WAL/runtime commit configuration](https://www.postgresql.org/docs/current/runtime-config-wal.html).

These references document available mechanisms; they do **not** establish that this campaign has run or that those mechanisms passed.
