**English** · [Español](../../es/anexos/anexo-i-campanas-de-evidencia-y-limites.md)

[← Annex H · Beyond COBOL](annex-h-beyond-cobol.md) · [Contents](../README.md)

# Annex I · Evidence campaigns and validation limits

I want the chapters to tell a readable story: what failed, what I decided and what might prove me wrong. This is the other half of that work—the experimental record. I will not turn inconclusive observations into PASS or hide the first failures to make the story more convincing.

Every result belongs to a code version, a host and a declared experimental contract. Two containers are not two data centres, and durable SQL is not bank certification. The architecture argument belongs to [channels](../part-4-patterns/21a-channels-atm-and-the-core.md) and [transfers](../part-6-lab/28-transfers-locks-and-failures-locally.md); this annex keeps the evidence provenance.

## I. Channels: cash, failures and transport

### Late advice, reversal and cash: correlation is not authorization

Consider a withdrawal authorized for 100.00 monetary units: the device attests that **60.00** was dispensed, but a switch may still carry an advice referring to the original requested 100.00. The ledger posts 60.00, and a full reversal request then arrives. It is wrong to infer either "post 100" or "credit 100" automatically. We need to establish what cash was physically available, which financial posting was committed, whether a message is merely a request, and who can adjudicate the discrepancy. A reversal request is not an executed ledger reversal.

The paired [EN research dossier](../../../docs/research/channel-late-advice.en.md) ([ES](../../../docs/research/channel-late-advice.es.md)) puts this against public ATM dispute guidance and conditional stand-in policies. The [channel forensic oracle](../../../lab/channels/advice_gate.py) adds a **fully synthetic, offline** four-instruction test with no database mutations:

| Synthetic observation | Correct oracle result | Never allowed |
| --- | --- | --- |
| Device dispenses 60 of 100 approved; identical late advice repeated | `MATCHED_PARTIAL_CASH` | Create a second posting or dispense |
| Device remains UNKNOWN; network advice says 80 | `UNKNOWN_REQUIRES_DEVICE_EVIDENCE` | Treat advice as physical confirmation or posting authority |
| Final device journal says zero; late reversal requested | `FINAL_ZERO_CASH` | Claim the requested reversal is booked |
| Core is unreachable with no issuer-delegated authority | `STAND_IN_DENIED` | Invent an offline issuer or cash authorization |

Neither STAN nor RRN alone is a durable financial identity. Retain the original **operation ID**, authorization, terminal, network context and source incarnation. STAN can be reused; a network message ID replayed with a different payload is a conflict, not idempotency. A request to reverse the whole amount after partial physical cash delivery must trigger review and a negative oracle for a false credit.

This is **not** a certified ISO 8583 implementation or a real ATM simulator. The new check has invented data: it **does not authenticate device journal entries, issuer policies, network settlement or actual bank operations**. It complements the prior ten native .NET 10/PostgreSQL experiments without treating their results as card-network certification. Even if the Python checks pass, no automatic dispense, posting or reversal is permitted; **TODM G2 INCONCLUSIVE / G6 BLOCK**.

### There is no generic network failure: locate the hop and decision

A channel “timeout” can conceal different financial states. If **ATM→switch** fails before delivery, no original authorization is demonstrated. If **switch→core** drops the request before the issuer receives it, the switch cannot invent account authority or dispense cash. If the core durably committed and **only its reply** was lost, starting a new operation ID risks a duplicate effect. Recovery queries the **actual decision owner under the original identity**; approval does not prove physical cash.

The [EN per-hop failure dossier](../../../docs/research/channel-hop-failures.en.md) ([ES](../../../docs/research/channel-hop-failures.es.md)) adds seven fictional traces and forty negative controls. It extends the previous partial-cash and late-advice examples without duplicating the core simulator.

| Scenario | Synthetic oracle outcome | Forbidden inference or action |
| --- | --- | --- |
| H01: ATM→switch request not delivered | `NO_CORE_AUTHORIZATION_EVIDENCE` | Treat timeout as a confirmed decline or success |
| H02: switch→core request not delivered | `NO_CORE_AUTHORIZATION_EVIDENCE` | Invent stand-in authority |
| H03: issuer COMMIT, lost ACK, status recovered on restored link | `AUTHORIZATION_RECOVERED_BY_STATUS` | Start another operation identity or infer cash delivery |
| H04: approval and device command, ATM↔switch fails | `CASH_UNKNOWN_NO_REDISPENSE` | Re-send dispense while journal remains unknown |
| H05: old owner replies after writer epoch changes | `QUARANTINED_OLD_OWNER_REPLY` | Allow old host to create another posting |
| H06: partial cash and fictional ledger agree | `PARTIAL_CASH_RECONCILED_SYNTHETICALLY` | Present fictional agreement as hardware proof |
| H07: core outage with undelegated stand-in request | `STAND_IN_DENIED` | Authorize offline credit or dispense |

**Routing is not source fencing.** A real change of authoritative writer from a host capability to .NET/SQL requires proof that the previous owner **can no longer commit the same operation**, including batch, privileged and disconnected paths. The fixture's `sourceEpoch` field is only a correlation marker, not a cryptographic lock or independent proof of revocation.

Nor does CICS UOW equal an HTTP transaction: a CICS task can have multiple syncpoints, with atomicity scoped to recoverable resources in each UOW. Network authorization and physical notes are external boundaries. See [IBM CICS syncpoints](https://www.ibm.com/docs/en/cics-ts/6.x?topic=work-synchronization-points) and [Azure transient fault guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults).

The [lab Python trace oracle](../../../lab/channels/network_fault_gate.py) **only checks declared JSON events**. It does not disconnect TCP sockets, execute a certified card protocol, contact an issuer or post to a financial ledger. A PASS shows consistency of this model, not a network guarantee. Real acceptance requires independent per-hop loss/reconnection injection, native issuer COMMIT logs, original retry identity, authenticated device journals, reconciliation and business-owner approval. **No fixture outcome authorizes automatic cash, reversal, posting, writer cutover or stand-in.** TODM G2 `INCONCLUSIVE`, G6 `BLOCK`.

### First real transport test: local TCP and the core COMMIT

The preceding H01–H07 tests represented disconnected hops with JSON events. The next experimental step uses **actual loopback TCP sockets**. An ephemeral one-shot proxy accepts the HTTP client's request, drops or forwards it to the existing **.NET 10** API, and observes the upstream response. The core commits in PostgreSQL while an independent Python oracle reads its tables and the separate synthetic device store. These are **real processes and sockets** but still run on **one host**: not a physical partition between branches, switch and mainframe.

| Transport test | Actual intervention | Independent assertion |
| --- | --- | --- |
| Request dropped before forwarding | Proxy accepts a real socket and resets it **without contacting the core** | Original SQL remains empty before recovery; same operation ID can commit once |
| Reply dropped after COMMIT | Proxy forwards request, observes HTTP 200 produced **after `CommitAsync`**, then resets the client socket without forwarding any response | Client sees `UNKNOWN` while SQL already has one committed operation, two paired postings and one outbox; original-status query and same-ID replay create no second effect |
| Reply delayed beyond client timeout | Proxy waits 0.8 s after upstream response versus a real client timeout of 0.15 s | Client sees timeout but the owner's original decision remains queryable and cannot be posted twice |

All three new cases are **fictional digital transfers**, not actual cash withdrawals. The existing ten native cases remain, including partial simulated cash, post-COMMIT failures, external `SIGKILL` and ATM/mobile competition. The [EN research protocol](../../../docs/research/channel-loopback-transport.en.md) ([ES](../../../docs/research/channel-loopback-transport.es.md)) documents scope, test replay, the proxy's fourteen safety checks and eighteen baseline/adversarial original-evidence controls.

**A client timeout alone does not prove absence of COMMIT.** The pre-forward drop has stronger evidence only because **our controlled proxy never opened an upstream socket and SQL was observed empty**. That independent proof may be unavailable in a real bank network. Retain the same durable `operationId` when querying status and, subject to the source owner's policy, retrying an ambiguous command.

This increment exercises **real local TCP interruption against durable SQL**, not `tc netem`, cross-host WAN failures, certified ISO 8583, CICS or authentic dispenser journals; it is not a MIPS/capacity benchmark. One financial writer must remain authoritative across all channels. Customer acceptance still requires native source signatures, owner policy, network evidence, source fencing and independent physical failure domains. **G2 INCONCLUSIVE, G6 BLOCK**, no banking cutover approval.

### Held original reply versus eight concurrent recoveries

The preceding experiment lost or delayed an ACK and then queried the core. It left a more difficult channel boundary untested: **the original response is still in flight while multiple clients concurrently try to recover the same operation**. One sequential retry does not establish safety under this race.

The [EN research contract](../../../docs/research/channel-held-ack.en.md) ([ES](../../../docs/research/channel-held-ack.es.md)) uses a deterministic barrier over **actual local TCP sockets**. A proxy forwards the original `POST /transfer` to the existing .NET 10 API, observes its HTTP 200 after PostgreSQL COMMIT, then holds the response. The first client experiences a real timeout. Before the old reply is released, the driver queries the fictional owner's authoritative status and launches **eight concurrent clients using the same `operationId` and intent fingerprint**. A ninth request with the original ID but a different amount must be rejected.

| Boundary | Original observation | Required independent oracle |
| --- | --- | --- |
| Fictional issuer | COMMIT confirmed while HTTP 200 is held | One operation, two postings and one outbox before retries |
| First client | Timeout and `UNKNOWN` | No new financial identity invented |
| Eight concurrent clients | Eight `COMMITTED` responses with `duplicate=true` | Still one durable decision and no second posting |
| Changed-amount attempt | `ID_CONFLICT` | Identity is bound to business intent |
| Late old ACK release | Monotonic timestamp after recovery | Old reply cannot open a new financial transition |

The [independent verifier](../../../scripts/check_channel_transport.py) checks original HTTP observations and intent, the order of real events **before the old response is released**, the read-only SQL snapshots and final ledger. The negative tests forge the timestamp sequence, replay identity or a duplicate posting and must be rejected. The fixture now contains **14 native scenarios**, **18 proxy guards and 27 original-evidence checks**.

**Architecture conclusion:** channel-visible response status must not be confused with the durable financial decision of the source owner. An old reply can arrive after recovery; **it is not a new authorization** and does not justify an automatic reversal. Idempotency must bind identity **and** intent and rely on the authoritative durable operation record.

The experiment uses `localhost` TCP and disposable PostgreSQL, **not** a certified ATM switch, ISO 8583, CICS, a cash device or a cross-host WAN partition. **Eight local clients do not establish MIPS equivalence or capacity.** Monotonic timestamps are only comparable within this host. Real issuer attestations, physical effects, incumbent writer fencing and owner-approved rules remain open. TODM G2 `INCONCLUSIVE` / G6 `BLOCK`.

## II. Orleans: partitions and activations

### C01 · Control placement to make recovery testable

The [original failure and three controlled cohorts](../../../evidence/runs/E2-C01-CONTROLLED.md)
separate an experimental precondition from an accounting defect. The historical
case observed all 16 accounts on secondary and correctly rejected its dual-host
requirement. Repeating the same queries was not a new placement sample:
existing activations could remain where they were.

The test client uses placement hints only to activate and observe account keys
1..16. In the negative control, all 16 were on secondary, the dual gate rejected
them and no financial operations occurred. Alternating hints from another
client did not redistribute them. A fresh fixture had observed 8/8 placement;
subsequent financial clients used no hints and the same accepted AccountGrain
and SQL ledger.

All three cohorts verified actual secondary SIGKILL, reactivation on primary,
idempotent replay, three operations/six postings/three outbox events and seven
invariants. A fresh secondary container then rejoined with a new Active
generation while the previous one remained Dead, without changing the ledger.
Assigned runner IDs differed; hostnames repeat and each case still uses one
machine. No physical HA is established.

This is the controlled-fixture alternative preregistered for C01. **The
historical concentration's cause remains unexplained**, the old test retains
its rejection and the runtime default policy is unchanged. Placement hints
also confer no financial authority: PostgreSQL still owns the effects. E2
remains partially verified.

#### Record failure without borrowing an earlier PASS

A successful `development` file does not prove that the later ADO.NET attempt
completed. The [observation follow-up](../../../evidence/runs/E2-PLACEMENT-OBSERVATION.md)
creates a journal per provider and execution, retains each map, membership and
logs before process cleanup, and records the exact failure phase. An
unavailable query remains an error; it is not converted into an empty list.

Two original controls deliberately aborted after the first real 1..16 identity
probe. Primary/secondary maps were 7/9 and 10/6: **they did not reproduce the
historical one-sided concentration**. Both children kept FAIL/exit 1, without
financial commands or SIGKILL, with zero effects and seven SQL oracles. The
parent verified failure preservation and kept the older PASS as control input.

This verifies the recorder, not placement policy or recovery. Future natural
failures will have their own evidence; the historical cause remains unproven
and E2 remains partially verified.

### C04 · The client loses its gateways, the ledger retains authority

The [original C04 test](../../../evidence/runs/E2-C04-GATEWAY.md) cuts only
the external Orleans client's gateway egress: first primary, then both. With
one gateway available, a fresh client committed through secondary to a grain
hosted on primary. Under the dual cut, both silos and PostgreSQL remained
reachable from one another.

The first attempt failed because an outer 70-second timeout did not identify
the application phase. Its negative ZIP is preserved. The corrected mode
observes a startup deadline before financial dispatch: exit 74 after 20.8509
seconds. No new effects appeared during the cut, including three additional
SQL samples. After restoring the original network rules, the same ID committed
and its replay was a duplicate; final state was three operations, six postings
and three outbox events, with oracle 7/7.

This is fresh-client startup unavailability, **not ACK loss after COMMIT**.
Four namespaces share one runner; the result neither explains the historical
C01 placement failure nor establishes physical domains, sustained capacity or
a production RTO. E2 remains partially verified.

### C05/C06 · Packet direction does not decide what committed

The [directional partition test](../../../evidence/runs/E2-C05-C06-DIRECTIONAL.md)
starts from observed 8/8 placement and blocks inter-silo TCP egress in one
direction at a time. SQL and gateways remain reachable. The 45-second captures
confirm identical packets at both endpoints in the allowed direction and
none received in the blocked direction. Failed TCP connections initiated from
both sides do not make the cut symmetric: they also need return traffic.

Two clients using different gateways send the same ID with amounts 31 and 37.
In both orientations, the first times out after dispatch and the second gets
COMMITTED; SQL identifies amount 37 as the winner. Management catalogs do not
respond during the cut: **an unavailable view is not an empty list** and does
not establish exclusive activation.

| Egress blocked | Observed fault | First acknowledged attempts through both gateways after restoration |
|---|---|---|
| Primary to secondary | 46.0143 s | 1.6926 s |
| Secondary to primary | 45.7963 s | 1.1831 s |

After the original rules are restored, neither silo restarts and their
containers, PIDs and generations remain unchanged. Identical replay returns
DUPLICATE_COMMITTED, the different amount ID_CONFLICT and a new command
COMMITTED. Each case ends with three operations, six postings and three outbox
events, with seven passing SQL invariants. Four earlier failures remain
preserved: two setup failures and two capture-shutdown failures; they are not
retrospectively converted into successes.

These are observed first acknowledged attempts, **not an RTO or sustained
stable service**. One host per case, two short cuts and catalog samples do not
establish absence of split brain, fencing or long-partition recovery. Those
gates, sustained capacity and physical domains remain open. E2 remains
partially verified.

### Long fault · Assisted recovery with bounded observations

The [original evidence](../../../evidence/runs/E2-LONG-PARTITION.md) adds two
120-second directional fault schedules. In both, the secondary silo exited
before the deadline: retaining a rule in a pinned namespace does not mean both
silos stayed alive. Two paired attempts did not restore the secondary gateway;
the protocol chose explicit recreation of both silos, preserving the ledger
and recording new generations. The first paired ACK arrived 58.484 and 59.211
seconds after rule removal.

Then 14 replay pairs across about 66 seconds retained the same containers/PIDs,
two Active members, SQL 3/6/3 and seven invariants. Identical replay returned
DUPLICATE_COMMITTED; changed payload returned ID_CONFLICT. This is sampled
stability after assisted recovery, not continuous availability, restart
necessity, production RTO, exclusive activation or physical HA. Both initial
instrumentation failures remain archived as FAIL; the correction separated
diagnostic lifetimes without weakening financial acceptance criteria.

### Activations · Observe calls without confusing them with exclusivity

The [separate observer](../../../evidence/runs/E2-ACTIVATION-OBSERVATION.md)
added an incoming-call filter to the test host, retaining the unchanged
financial grain and ledger. Two original cases recorded 38 and 39 complete
Transfer envelopes with activation IDs, process sessions and monotonic clocks.
Logs were retained before silo recreation. Every acknowledged result reconciled
with SQL: three operations, six postings, three outbox events and seven
invariants in each case.

No incomplete envelopes or overlaps across distinct activations of the same
grain were observed. This does not establish global exclusivity: the filter
measures request envelopes, not entire activation lifetimes or simultaneous
SQL transactions. A targeted positive concurrent-activation scenario with
independent SQL acceptance remains pending. Each case used one physical host
and assisted recovery; E2 remains partially verified.

### Directed delay · One positive witness does not establish repeatability

The [directed ordinary-grain trial](../../../evidence/runs/E2-ACCOUNT-DIRECTED.md)
held an old request in a separate filter before invoking the financial method.
It changed neither AccountGrain, ledger nor default placement. One case showed
two complete request envelopes on distinct activation IDs for the same key,
overlapping 5.06ms with the fault rule present: the new request committed amount
31 and the old request returned DUPLICATE_COMMITTED after release. SQL retained
one durable effect and rejected incompatible payloads.

The opposite direction was inconclusive. The first collector omitted stderr;
after correction, both repeated cases were also inconclusive. One positive
witness across those four observations. A third campaign observed another
4.68ms overlap with full stderr: two directed positives and four inconclusive
outcomes in total, partially reproduced only in the secondary-outbound case. In the
repeats, stderr and SQL identify a fatal membership path: the primary discovers
itself Dead, enters KillMyselfLocally and exits with code 139. Victim selection
across directional partitions remains incompletely explained.

Every case ended with assisted recovery, three operations, six postings,
three outbox events and seven invariants. The delay is artificial and measures
incoming requests, not simultaneous Active lifecycles or simultaneous SQL
transactions. Inconclusive originals retain their classification. E2 remains
partial; sustained capacity and physical domains are independent gates.

## III. Brownfield: authority and recovery

### C2 · An unknown reply requires a durable admission journal

The earlier coexistence experiment can compare two stores, but it leaves
a separate failure mode: **COMMIT may be durable even when no ACK arrives**.
Treating a timeout as rejection and retrying on a second writer can duplicate
the financial effect. C2 therefore adds a third disposable PostgreSQL
database, `bf_control`, with an admission journal independent of both
ledgers. Each CAP-007 request records its stable ID, request hash, writer,
epoch and state before remote execution.

A request moves from `ADMITTED` to `DISPATCHING` and, when its reply
disappears, to `UNKNOWN`. Only an independent SQL inspection of the
persisted operation, paired postings and outbox may finalize
`COMMITTED` or `REJECTED`. Missing SQL rows in both stores **do not
prove rejection**: the journal remains UNKNOWN and cutover is blocked.

The three-container experiment kills real processes after admission,
before remote dispatch and after COMMIT but before the gateway receives
the result. It also forges a terminal journal state and verifies that the
independent oracle rejects promotion. The cooperating Python legacy
adapter and .NET 10 candidate can require the C2 controller and hold a
shared authority row lock through financial COMMIT. The
[original C2 CI run](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41341644829)
is tied to one exact source SHA. It is not bank acceptance.

**At that original C2 source SHA:** strict C2 mode
requires a matching `DISPATCHING` journal admission at both adapters and
rejects direct unadmitted commands. Deliberately disabling this opt-in
allows direct unjournaled posts: the oracle detects that configuration
bypass but cannot prevent it. Nor do the
controller and candidate authority epochs change atomically across two
PostgreSQL servers. A cooperative lock cannot revoke a real CICS/Db2
writer's authority. External fencing, split-authority crash repair,
third-party side-effect reconciliation, cross-host tests and approved
business policy remain missing. TODM G2=INCONCLUSIVE and G6=BLOCK.

### C2 follow-up · Persist the fence and freeze interrupted transitions

The [journal follow-up](../../../lab/brownfield/journal/README.md) changes
two engineering assumptions without changing business authority. Enrollment
is stored in SQL: removing a process variable can no longer disable admission
checks in either cooperating adapter. Fresh historical fixtures remain
unenrolled, and privileged direct SQL remains outside that enforcement.

Before changing either writer epoch, the coordinator commits a durable
`PREPARED` intent and `mode=SWITCHING`. Both adapters and the gateway refuse
new financial commands until independent ledger and journal reconciliation
allows the controller to complete that exact transition.

| Durable boundary | Controller | Candidate authority | New admission |
|---|---|---|---|
| Intent prepared | legacy / e / SWITCHING | legacy / e | Blocked |
| Candidate authority committed | legacy / e / SWITCHING | candidate / e+1 | Blocked |
| Reconciliation completed | candidate / e+1 / ACTIVE | candidate / e+1 | Allowed with matching admission |

The protocol independently sends `SIGKILL` after each of the first two
boundaries and restarts recovery. An unexpected epoch or missing outbox must
leave traffic frozen; a missing response cannot choose the next writer.
Candidate-origin decisions still veto rollback. This closes specific
cooperative crash windows through durable intent and forward recovery,
**not atomic COMMIT across databases**. The [original follow-up CI](../../../evidence/runs/BROWNFIELD-C2-RECOVERY.md)
passed 19 controls, preserving its raw ZIP and the initial failed concurrency
run. The later [run #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630),
on main `279ca566`, passed 20 controls and both SQL oracles 10/10; this is a
separate observation, not retrospective coverage attributed to that ZIP. Later code still requires its own exact-source CI evidence; historical
observations cannot validate a different checkout.
In-flight network partitions, real incumbent revocation, external payment
effects and approved business policy remain separate acceptance gates.
G2=INCONCLUSIVE and G6=BLOCK.

### C2 · Losing the controller after a financial operation has started

The [new TCP-cut protocol](../../../lab/brownfield/journal/README.md) targets
a different window from an unreachable controller before execution. A test
trigger holds the financial operation before COMMIT; an independent SQL
session must observe the real lock wait. A relay closes controller TCP
connections and refuses reconnects; an external process then kills the gateway
while leaving its adapter in flight. This is neither a silent nor asymmetric
partition; all three PostgreSQL containers still share one runner.

The contract requires UNKNOWN and a writer-switch veto until a durable
decision is observed. After releasing the barrier, the cooperative model can
commit its financial transaction even after losing the controller session.
SQL reconciliation must precede replay: one decision, two postings and one
outbox event. Losing a lock in another database does not atomically cancel
financial COMMIT. CI must fail if observations contradict the contract.

[Original run #41511782428](../../../evidence/runs/BROWNFIELD-CONTROLLER-LOSS.md)
passed both cases: Python legacy and .NET candidate. SQL confirmed session
loss; UNKNOWN vetoed the switch and later reconciliation found one decision,
two postings and one outbox event per case, with both SQL oracles 10/10.
The original ZIP preserves source/checkout and ten source hashes. This bounded
evidence does not close #64 or establish bank fencing, RTO/RPO or production
migration.
G2=INCONCLUSIVE and G6=BLOCK.

### C2 · A live connection does not mean a known decision

The next [original campaign](../../../evidence/runs/BROWNFIELD-CONTROLLER-PARTITION.md) keeps controller sockets open while discarding opaque stream bytes in one direction. Four cases cross the legacy/candidate writers with each direction. A tagged SQL probe, observed outside the relay, distinguishes a request that never reached the server from a response that never reached the client. This application relay acknowledges TCP reads; it is not a kernel packet-loss emulator.

All four cases passed on their recorded source. Before releasing the financial barrier, controller holder sessions remained alive and financial decisions were absent. New admission and cutover attempts failed without changing authority. After the gateway was externally killed and the barrier released, each ledger still committed exactly one decision, two postings and one outbox. In these attempts, suppressing requests left the controller session in transaction; suppressing replies left it idle after the separate financial COMMIT. An open socket or missing response cannot decide what another database committed.

Recovery explicitly resets connections before reconciliation; discarded protocol bytes cannot safely be resumed as a complete stream. Both SQL oracles pass ten checks each, replay adds no effect and two deliberately false observation claims are rejected. This demonstrates neither automatic recovery nor a real incumbent-side fence. Actual packet retransmission, timeout/lock budgets, symmetric faults and independent physical hosts remain external validation. G2=INCONCLUSIVE and G6=BLOCK.

## IV. Admission and external validation

### B05: distinguish admission limits from backend capacity

The [direct admission diagnostic](../../../evidence/runs/B05-DISPATCH-DIAGNOSTIC.md) adds three runner cohorts at 320 offered/s with 60-second measurement phases. Each paired trial keeps the PostgreSQL connection pool at 32 and changes client admission from 32 to 128 slots, reversing the order in one cohort. Exact admission/completion/release events and independent SQL commit timestamps replace retrospective occupancy estimates.

Across six trials, 119,040 offers yielded 118,887 durable commits and 153 admission misses: 129 during warmup and 24 during measurement. All misses occurred at exactly 32 active slots. The three 128-slot trials admitted every offer. All seven financial invariants held in each trial. One 32-slot trial recorded 319.6 certain SQL commits/s; the others recorded 320.0000–320.0167/s in the independent SQL window, whose boundaries differ from offer phases.

This is evidence of an admission-policy effect in this instrumented direct-client setup, not a backend capacity ceiling or an explanation of the older 12 misses. Pool-acquisition waits remain unmeasured; runner noise and instrumentation affect timing. Orleans routing, sustained scaling and bottleneck attribution under #25 remain open. The frozen archive audit is distinct from a new live campaign; a skipped live matrix proves nothing about capacity.

### Integrate bounded evidence and defer external validation explicitly

On 3 November 2026, the author authorized integration of the E2 observations and B05 diagnostic without requiring hosted CI to establish every production claim first. The [external-validation protocol](../../../docs/EXTERNAL_VALIDATION.md) keeps the exact remaining work reviewable. Missing external measurements no longer block book/lab integration or editorial progress. E2 remains partially verified; this decision does not turn an INCONCLUSIVE result into PASS or authorize banking deployment.

A single hosted runner can test real SQL, distinct processes, logical partitions and independent reconciliation. It cannot make those containers physically independent. Capacity and natural activation observations are not intrinsically impossible in Actions; the present campaigns simply do not establish them. Actions can orchestrate dedicated infrastructure or self-hosted runners. The important distinction is the actual topology and evidence, not the orchestration product.

| Pending claim | More realistic experiment | Required harness change |
| --- | --- | --- |
| Sustained capacity and bottleneck (#25) | Separate load, silo and SQL hosts; identical direct/Orleans vectors; 1/2/4/8/16 silos, fixed durability and repeated rate sweeps | New external-endpoint driver with fixture allowlist; measure scheduling, queues, connection acquisition, SQL waits/WAL/storage and per-host resources |
| Natural activation and continuous recovery (#24) | Ordinary grains without injected pre-invoke delay; directional faults on actual interfaces; unassisted recovery | Replace local container assumptions with explicit remote process identities; retain lifecycle events, both log streams and PCAPs; bound clock uncertainty |
| Physical HA and durability (#8/#9) | Recorded independent failure domains; separate host loss, network partition and database failover | Record replication/acknowledgement policy and reconcile ambiguous IDs; dedicated disposable hardware for storage power-loss tests |
| WAN, transport and economics (#9/#12) | Actual branch/backend paths with equal TLS/authentication for gRPC and REST; dated total cost per correct durable transfer | Separate controlled impairment from field observations; capture DNS, gateways, reused channels, deadlines and operating/DR cost |
| Banking cutover (#32/#58/#64) | Owner-approved contract, authorized traces and a real incumbent-side writer fence | Connect an approved adapter, reconcile external effects and repeat in-flight/UNKNOWN/rollback controls; retain TODM G2/G6 approval |

The existing B05 probe deliberately checks an exact loopback DSN; changing an environment variable alone cannot make it a distributed benchmark. Keep the frozen fixture and add a separately identified driver. Remote monotonic timestamps cannot be directly compared: record host clock offset and uncertainty, require a positive overlap even after uncertainty bounds, and otherwise retain INCONCLUSIVE.

The proposed external study starts by reproducing 320 offered/s, then uses at least three repetitions per configuration, fixed seeded uniform/hot/crossed profiles and preregistered load points around degradation. A suggested initial schedule separates 5 minutes of warmup, 15 minutes of steady measurement and bounded drain; these are proposed study durations, not results or production acceptance thresholds. Prove spare generator capacity first, include every missed/late/ambiguous offer in service outcomes, and preserve warmup rather than cropping it away. Keep pool, retries, timeouts and durability fixed while changing one factor. Measure queue growth and attributable resources before declaring a capacity knee.

Archive every original attempt with exact source, host/domain map, clock uncertainty, environment, workload, raw logs and independent SQL oracles. Preserve all seven financial invariants and corruption controls. Source and archive regressions remain integration checks; original live campaigns retain their existing manual invocation and exit behavior. A skipped campaign proves nothing about capacity. Stronger claims remain conditional on their own acceptance record, while development proceeds. Publication retains its separate authorization.

---

[← Annex H · Beyond COBOL](annex-h-beyond-cobol.md) · [Contents](../README.md)
