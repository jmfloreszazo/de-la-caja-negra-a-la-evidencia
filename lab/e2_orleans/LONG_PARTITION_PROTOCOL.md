# E2 — 120-second directional fault schedule and sampled recovery

Status: **bounded original CI verified; assisted recovery and sampled stability only**. Issue #24.
Original source `ee1e883e5e23d651e3408a90f8ec12fd9f7a2d58`, run #41607407356.
See [audited original outcomes](../../evidence/runs/E2-LONG-PARTITION.md).
No historical evidence is rewritten. E2 stays partially_verified; #53 remains
frozen and release/tag identifiers stay unchanged.

## Topology and scope

Two fresh matrix jobs schedule opposite one-way silo TCP faults. Each job has
one PostgreSQL 16.13, two Orleans 10.4.0 ADO.NET silos, an external client and
four distinct namespaces on one physical host. Reuse the verified short-case
helpers and test-only fixed-gateway client without modifying them or the
accepted C# grain/ledger/default policy. Shared helper output paths are reused
only inside the fresh job; the result is `long-partition-summary.json`, not a
short-case result. Record exact source/checkout, file hashes, images and runner.

Two fixed NET_ADMIN/NET_RAW observer sidecars are created while their targets
are known running. Subsequent queries use `podman exec` in those existing
sidecars, never a new dependency container against a possibly stopped silo.
The observers retain the original network namespaces and record target
identity/liveness before and after each command. They do not make an exited
silo healthy. Remove completed capture containers and then observer sidecars
before any explicit target recreation; recreate observers only after the new
silos are ready. These are test-local observers with unchanged capabilities,
not independent physical fault domains.

## Fixed acceptance before any original run

1. Require real disposable SQL readiness, two Active membership generations,
   exact identity-only 8/8 seeding on original keys 1..16, then one ordinary
   baseline COMMITTED operation with SQL 1/2/1 and seven independent invariants.
2. Apply the same exact one-way OUTPUT DROP for silo TCP ports 11150/11151.
   Leave SQL/gateway rules unchanged. Verify initial SQL and both gateways
   from both silos and client. Capture both endpoints using native 45s autostop,
   real SYN probes and original PCAPs; require matching allowed-direction
   packets at both endpoints, no blocked-direction arrivals, failed handshakes
   and a positive DROP counter. One-way packet loss can break TCP from both sides.
3. Hold the **fault schedule for at least 120 and at most 180 observed seconds**.
   Sample actual process/container liveness, membership generations, SQL effects,
   all seven oracles and the live namespace's exact rule, targeting 2s cadence.
   Blocking client calls can delay samples: retain actual timestamps, not an
   invented uniform series. A silo can stop itself and lose its namespace;
   record that explicitly. Do not call 120s scheduled outage proof of 120s
   live-silo packet loss if a process or namespace disappeared earlier.
4. Offer the contested stable ID with amounts 31 and 37 concurrently through
   different fixed gateways early in the cut, then again after 60s. Record
   ACK, pre-dispatch startup unavailability or post-dispatch ambiguity. Parent
   timeouts, crashes or invalid JSON fail the experiment. SQL may hold zero
   or one contested operation; every acknowledged payload must agree with SQL,
   with no extra operation/posting/outbox cardinality. No new unique IDs during
   the cut. Management catalogs are recorded but can be unavailable/non-atomic;
   they never prove exclusive or simultaneous activation.
5. Restore the exact old OUTPUT baseline if the target namespace is still live.
   If the target exited, distinguish restoring the pinned original namespace
   from application recovery; retain the exact observed rule baseline.
   Allow at most two paired bounded fresh-client attempts without operator
   recreation. If paired ACKs, two Active members and both running processes
   are not observed, explicitly recreate **both** silos, preserving the ledger
   and old membership generations. Require two Active restored generations and
   exact firewall baselines. This is assisted recovery after bounded attempts,
   not proof that restart was necessary or that unassisted recovery was impossible.
6. Record first paired ACK separately from the time all recovery criteria hold;
   require the latter within a **300s experiment bound** from restoration.
   Reconcile the actual winning payload by SQL. Require identical replay
   DUPLICATE_COMMITTED, different-payload ID_CONFLICT and one new COMMITTED
   operation; exact final effects 3 operations/6 postings/3 outbox and 7/7 oracles.
7. Require **14 consecutive paired replay samples** targeting 5s apart, over an
   actual first-to-last observation span of **at least 60 and at most 150s**.
   Every sample must ACK DUPLICATE_COMMITTED through both gateways, keep SQL
   3/6/3 with all seven invariants, retain the same current container/PID state
   and two Active members. Actual adjacent observation gaps must be <=10s.
   Any uncertainty, invariant failure or flap fails this window; never reset
   the clock until a later sequence happens to pass. This is sampled stability,
   not uninterrupted availability between samples or a production latency SLA.
8. Retain all original PASS/FAIL reports, incomplete observations, PCAPs, firewall
   states, membership, process states, client outcomes and logs before correction.
   Accept only this bounded slice after both original jobs pass and independent
   artifact/source/PCAP/SQL audit. Never promote the whole E2 phase.

## Remaining gates

No exclusive-activation, fencing, physical failure-domain, PostgreSQL HA,
production RTO/RPO, capacity ceiling, MIPS equivalence or banking acceptance is
established. The historical default-placement cause remains open under #74.
The short-case original evidence and its stricter observed-scope claims remain
unchanged. Publish paired ES/EN interpretation only after actual original CI.

## First original attempt retained — instrumentation failures

Run #41605736830 on `62d78fbddc206babbe3cbd28630f33464271d619`
failed both cases during restoration. Primary-block case reached the explicit
recreation branch but Podman refused to remove a silo with dependent capture
containers. Secondary-block case had already observed secondary exit and Dead
membership, then a later direct helper/delete path reported a missing rule.
Do not call that a completed recovery or infer passive healing from it.
The prototype created transient namespace helpers; their lifecycle was not
adequately separated from an exited target. Podman documents dependency
startup in its [run reference](https://docs.podman.io/en/v4.3/markdown/podman-run.1.html).
That does not by itself prove the precise cause of this particular transition.

Original ZIPs/JSON extractions are retained unchanged under
`evidence/runs/e2-long-first-{primary,secondary}-original.*`.
Primary artifact 13217031754, SHA-256
`eb47f2302c5ddb880de2857e4c8e6d694518b1aeaae3cc8b2aa54572bbfc4439`;
secondary artifact 13216048812, SHA-256
`52b51a65c1dd918d9d3c7778bda34fdb77a6032294c5366cb02b2da911a09e4e`.
All 70 provenance source hashes per original were independently audited.
The correction uses existing observers and explicit dependency cleanup; it
does not change the SQL, stability, financial or timing acceptance criteria.
The original short-case assisted branch was not exercised in its accepted
source; its dependency cleanup also needs separate validation before any
broader assisted-recovery claim.
