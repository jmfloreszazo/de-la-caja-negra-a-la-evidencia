# E2 · Long fault schedules with assisted, sampled recovery

**Bounded original evidence verified, 3 November 2026. E2 remains partial.**

[Original run #41607407356](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41607407356),
source and checkout `ee1e883e5e23d651e3408a90f8ec12fd9f7a2d58`.
Two fresh jobs; **one physical host per case**, not independent failure domains.

| Case / caso | Job | Artifact | Bytes | ZIP SHA-256 |
| --- | --- | --- | --- | --- |
| primary outbound | 125820594636 | 13217388632 | 28255 | 999f2612e6a032305e0a7dc58b30e7cecbe8670626ce976f924e06c5141b46d0 |
| secondary outbound | 125820594983 | 13217885893 | 28677 | a0f2ed8039afae94eadf2bb1f255f0887c4fa69553cb16717229233aa201f922 |

Unmodified ZIPs and byte-identical summary extractions:
[primary ZIP](e2-long-primary-original.zip) / [JSON](e2-long-primary-original.json),
[secondary ZIP](e2-long-secondary-original.zip) / [JSON](e2-long-secondary-original.json).
Both ZIP digests and all 70 provenance source hashes per job were recomputed
against the exact source commit. The offline auditor also parses original
PCAP bytes, matches allowed-direction TCP packets at both endpoints and finds
no blocked-direction arrivals during the initial 45-second capture.
The capture covers the initial window, not the entire fault schedule.

## Observed outcomes

| Observation | Primary outbound blocked | Secondary outbound blocked |
| --- | --- | --- |
| Fault schedule, seconds | 120.000110 | 120.000121 |
| Last sample with secondary running, start–end seconds | 65.844–66.205 | 66.486–66.786 |
| First sample with secondary exited, start–end seconds | 68.205–68.475 | 68.786–69.081 |
| Final DROP packet counter in pinned namespace | 125 | 135 |
| Target at rule removal | Primary running | Secondary exited |
| Two unassisted paired attempts | Secondary gateway unavailable before dispatch | Secondary gateway unavailable before dispatch |
| Recovery mode | Both silos explicitly recreated | Both silos explicitly recreated |
| First paired ACK after rule restoration, seconds | 58.484 | 59.211 |
| Recovery criteria satisfied, seconds | 58.484 | 59.211 |
| Stable replay samples | 14 pairs | 14 pairs |
| First-to-last sampled span, seconds | 66.152 | 66.129 |
| Final operations / postings / outbox | 3 / 6 / 3 | 3 / 6 / 3 |
| SQL invariants at every recovery sample | 7/7 | 7/7 |

Sample start/end brackets are observation intervals, not exact process-death
timestamps. Both cases observed the secondary exit before the 120-second
schedule ended. The existing diagnostic sidecars retained the original network
namespaces and DROP rules after process exit. Thus **120 seconds describes the
scheduled fault, not 120 seconds with both silos alive**. Namespace restoration
with an exited target is not application recovery. Diagnostic command records
retain target identity and before/after liveness; none records an exited target
becoming running during diagnostic execution.

Both cases used controlled, identity-only 8/8 placement over keys 1..16 before
ordinary financial commands. Initial SQL was 0/0/0, baseline 1/2/1. Contending
requests used the same ID with amounts 31 and 37 through different gateways;
SQL retained only amount 37. All ACKs reconcile with that durable winner;
post-dispatch uncertainty does not imply rollback. Identical replay returned
DUPLICATE_COMMITTED, changed payload ID_CONFLICT, and one new ID COMMITTED.

After two bounded unassisted attempts, the protocol chose operator-assisted
recreation of both silos. Both container IDs and membership generations changed;
the ledger survived. This demonstrates that assisted path, not restart necessity,
unassisted impossibility, automatic failover or a production RTO. Accepted C#,
SQL oracle, default placement policy and short-case helpers are unchanged.
Completed capture dependencies and diagnostic sidecars were removed before
recreation; new observers were attached only to ready replacements.

The 14 paired replay samples retained the same recovered container/PID states,
two Active members, SQL 3/6/3 and all seven invariants. Every pair acknowledged
DUPLICATE_COMMITTED; actual adjacent sample gaps were at most 10 seconds.
This is **sampled stability**, not continuous availability between observations,
a sustained-load benchmark, exclusive activation, absence of split brain,
PostgreSQL HA or multi-host resilience. Catalog snapshots are non-atomic.

## Original failures remain failures

[First run #41605736830](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41605736830),
source `62d78fbddc206babbe3cbd28630f33464271d619`, failed both cases.
[Primary ZIP](e2-long-first-primary-original.zip) / [JSON](e2-long-first-primary-original.json):
recreation was refused because stopped capture containers still depended on the silo.
[Secondary ZIP](e2-long-first-secondary-original.zip) / [JSON](e2-long-first-secondary-original.json):
a direct transient helper/restore path reported a missing rule after observed
secondary exit. Its exact lifecycle cause is not established. Neither is a
successful recovery. Original hashes and source audit are retained in the
[protocol](../../lab/e2_orleans/LONG_PARTITION_PROTOCOL.md).
The correction separated diagnostic lifetimes and dependency cleanup; it did
not relax the original SQL, timing or sampled-stability requirements.

Next within #24: observe concurrent activation behavior explicitly with SQL
acceptance; do not assume global actor exclusivity. #25 sustained capacity,
independent physical domains and #74 natural-placement cause remain open.
G2 INCONCLUSIVE/G6 BLOCK; #53 frozen; no release or tag change.

[Español](E2-LONG-PARTITION.es.md) · [Auditor](../../scripts/check_e2_long_partition_observations.py)
