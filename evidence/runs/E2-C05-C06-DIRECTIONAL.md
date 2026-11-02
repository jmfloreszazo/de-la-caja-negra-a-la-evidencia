# C05/C06 · One-way packets, uncertain response and SQL reconciliation

**Original synthetic CI verified, 2 November 2026. E2 remains partially verified.**

[Run #41528812921](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41528812921)
on source/checkout `958961906de0ca5d3945d410c64d465ba7d34a3e` passed
both jobs: primary block `125563418932`, secondary block `125563419503`.
Each case uses four distinct namespaces on one physical host. Two assigned
runner jobs with the same hostname label `runnervm48cm3` do not establish
independent physical failure domains.

## Unchanged originals and independent audit

| Direction blocked | Original artifact | Bytes | ZIP SHA-256 |
| --- | --- | --- | --- |
| primary → secondary | 13180394069 | 22094 | 06d471e856c514b4007f8dc54e1c975de0801a7bc67048d97e71868534d08d6f |
| secondary → primary | 13181810454 | 21662 | 8c865621cae8b72c4d66bb46aabfd1e76e3cbe4ba5ad7364fda3c09148706c73 |

Original ZIPs: [primary](e2-c05-c06-primary-original.zip),
[secondary](e2-c05-c06-secondary-original.zip). Byte-identical JSON extractions:
[primary](e2-c05-c06-primary-original.json), [secondary](e2-c05-c06-secondary-original.json).
Both ZIP digests and all 64 original provenance source hashes per job were
recomputed against the exact source commit. Accepted AccountGrain/Contracts
and PgDurableLedger remain unchanged. The offline checker independently parses
the original PCAP records, rather than trusting the summary's decoded text.

## Measured results

| Observation | Primary outbound blocked | Secondary outbound blocked |
| --- | --- | --- |
| Observed fault interval | 46.0143 s | 45.7963 s |
| Rule-matched dropped TCP packets | 83 | 81 |
| Identical allowed packets seen at both endpoints | 11 | 10 |
| Blocked-direction packets at the receiving endpoint during capture | 0 | 0 |
| Primary-gateway command: same ID, amount 31 | Dispatched timeout, ambiguous | Dispatched timeout, ambiguous |
| Secondary-gateway command: same ID, amount 37 | COMMITTED | COMMITTED |
| SQL during fault, including baseline | 2 operations / 4 postings / 2 outbox | 2 / 4 / 2 |
| Management catalogs during fault | Both unavailable | Both unavailable |
| First acknowledged attempts through both gateways after restoration | 1.6926 s | 1.1831 s |
| Silo recovery | Network restoration only; same containers/PIDs/generations | Same |
| Final SQL after replay, conflict and new command | 3 / 6 / 3; 7/7 oracles | 3 / 6 / 3; 7/7 oracles |

The DROP matches only silo TCP ports 11150/11151 in one namespace's OUTPUT
chain. SQL and gateway ports remain reachable from both silos and the client.
Both attempted TCP handshakes fail: one-way packet loss also removes the
return traffic that TCP needs. Native dumpcap autostops after 45 seconds;
original PCAPs, decoded text, image IDs and exact rules are inside each ZIP.
The original 8/8 controlled placement is identity-only; financial clients use
no hints and a single fixed gateway each. Ingress selection does not prove
which activation executed an ambiguous request.

SQL independently recorded amount 37 as the contested winner. After restoring
exact firewall baselines, identical-payload replay returned DUPLICATE_COMMITTED,
different-payload replay returned ID_CONFLICT and one new command COMMITTED.
All seven SQL invariants held. A dispatched timeout does not imply rollback;
an unavailable management catalog does not imply an empty catalog or exclusive
activation. Both recorded generations remained Active throughout the sampled
membership observations; no death/reincarnation or simultaneous activation is
claimed from this run.

## Four earlier failed jobs remain failures

Run #41527647221, source `5a260594c159c109cccf49f2f9f8287a37d18e10`,
failed before Orleans because the shared SQL helper did not admit `c05`.
Originals: [primary ZIP](e2-c05-first-preflight-primary.zip) /
[JSON](e2-c05-first-preflight-primary.json),
[secondary ZIP](e2-c05-first-preflight-secondary.zip) /
[JSON](e2-c05-first-preflight-secondary.json).

Run #41528077816, source `72d93aee4cf148ade04c8e1979bc60d7439bdb75`,
reached actual loss and 2/4/2 SQL, then failed because rootless crun denied
host-side SIGINT to tcpdump. Originals, including incomplete PCAPs:
[primary ZIP](e2-c05-second-capture-primary.zip) /
[JSON](e2-c05-second-capture-primary.json),
[secondary ZIP](e2-c05-second-capture-secondary.zip) /
[JSON](e2-c05-second-capture-secondary.json).
All four ZIP digests and original extractions are pinned by the checker;
their 64-source provenance hashes were also audited. The correction uses a
native capture timer, without expanded runtime permissions or weakened
financial assertions. These failures are not retrospectively passing tests.

## Acceptance boundary

This verifies **two bounded directional packet-loss cases, SQL reconciliation
and measured first acknowledgements after restoration**. It does not establish
exclusive activation, absence of split brain, fencing, long-partition recovery,
sustained stable service, independent physical HA, production RTO/RPO,
PostgreSQL HA, capacity saturation or MIPS equivalence. The 240s experiment
bound is not a production promise; the assisted-restart branch was not exercised.
Keep #24 open for those remaining activation/recovery gates, #25 for sustained
capacity, G2 INCONCLUSIVE/G6 BLOCK and #53 frozen. No release/tag change.

[Español](E2-C05-C06-DIRECTIONAL.es.md) · [Protocol and pinned sources](../../lab/e2_orleans/F10_C05_C06_PROTOCOL.md)

## Separate loopback ADO.NET regression remains open

Broad validation run #41528813076 on the same source failed in
`test_multiprocess.py:174` because the ADO.NET loopback case could not prove
both silos hosted grains before SIGKILL. This is not a C05/C06 case or a
proven accounting defect. [Issue #74](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/74)
tracks the unresolved precondition and missing failure-specific diagnostic.
The [original regression ZIP](e2-c05-loopback-placement-failure-original.zip)
(artifact 13180837720, 10124 bytes) has SHA-256
`55bed14ebac7f582b3d29a9dc13e97c6c75f11a48c64bfdf12a7b18db9fe5332`.
It contains a valid earlier development-provider PASS, correctly identified
by provider/filename, and no ADO.NET success file. The
[decoded API job-log snapshot](e2-c05-loopback-placement-failure-job.log),
SHA-256 `677bad5736b70539523349d9da3dde0cf8fad5ee0c398d2077e337ca90b7440a`,
retains the later failed ADO.NET step. A later successful source run would
not explain or erase this negative.

## Container default-policy rejection during final-source regression

Run #41530411861 on `31945c91622ada4863d7058519f3533771f1147a`
failed its strict historical C01 prerequisite: all 16 original accounts were
on primary. [Original ZIP](e2-c05-default-baseline-failure-original.zip),
artifact 13180848622, 4506 bytes, SHA-256
`e9a703eaf4aec8cf1269ab953ea0ecce306fdb521be1163f3fd13c0ae3cb728a`;
[unchanged placement-negative extraction](e2-c05-default-baseline-failure-original.json).
This is a prerequisite rejection, not a financial failure; the startup stage
field is stale. The C01 acceptance workflow now explicitly runs the previously
verified controlled negative/positive alternative, retaining the original
strict default-policy test as an explicit manual diagnostic. No assertion,
accounting oracle or default runtime policy is weakened. C05/C06 on this final
source passed separately; the cause of default concentration remains unknown.
