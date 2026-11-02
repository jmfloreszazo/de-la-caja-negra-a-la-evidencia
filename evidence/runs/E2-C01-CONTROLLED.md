# C01 · Controlled placement, one-sided rejection and recovery

**Original synthetic evidence, 2 November 2026. E2 remains partially verified.**

[Run #41523019075](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41523019075)
passed all three cohorts on source/checkout
`47ed0a087717ec6c02f64a173a63ee597a919f75`. Original job IDs were
`125543545505`, `125543544991` and `125543546197`.

## Originals and audit

| Cohort | Assigned runner ID | Original artifact | Bytes | ZIP SHA-256 |
| --- | --- | --- | --- | --- |
| 1 | 1000006956 | 13179390478 | 21020 | 7b426f22055aa3567b5055f0ba9edf20c975282848d335a5a84f8fc8f1790898 |
| 2 | 1000006953 | 13177724656 | 21623 | 451da1a89d243bed2b8d4829ac93c4c4a0feb1b327201658e234098c4a50ccb5 |
| 3 | 1000006961 | 13177439210 | 21299 | da90c8a0be90c534ddd4f5c7eea9474b1cc22f1e243ef5f78be9ea0e193a3dcc |

Unmodified ZIPs: [1](e2-c01-controlled-1-original.zip),
[2](e2-c01-controlled-2-original.zip), [3](e2-c01-controlled-3-original.zip).
Unchanged extracted JSON: [1](e2-c01-controlled-1-original.json),
[2](e2-c01-controlled-2-original.json), [3](e2-c01-controlled-3-original.json).
All three digests and each cohort's 61 full provenance source hashes were
recomputed. The [jobs API snapshot](e2-c01-controlled-jobs-api.json) records
allocation metadata, **not an experiment artifact**. Runner IDs differ, but
all three hostnames are `runnervm48cm3`: no physical independence is inferred.
The six fresh fixtures have 24 distinct initial container IDs, plus three
recreated secondaries.

## Results in all three cohorts

| Control | Result in all three cohorts |
| --- | --- |
| 16 accounts seeded only on secondary; both members Active | Correct dual-placement rejection; 0 operations/0 postings/0 outbox; oracle 7/7 |
| New client requests alternating hints for those existing activations | All 16 remain on secondary; dual-placement gate still rejected |
| Fresh fixture with alternating account 1..16 seeding | 8 on primary, 8 on secondary; independently observed by a normal unhinted client |
| Two transfers from their original hosts | COMMITTED on secondary and primary; 2/4/2 SQL effects |
| Secondary SIGKILL after acknowledgement | Exit 137; reactivation on primary; secondary membership Active 3 to Dead 6 |
| Stable-ID replay and new transfer | DUPLICATE_COMMITTED then COMMITTED; 3 operations/6 postings/3 outbox; oracle 7/7 |
| Secondary rejoins | New container, PID and generation; old Dead generation retained; ledger unchanged |

## Historical failure remains unchanged

The [original failed ZIP](e2-c01-original-one-sided.zip), artifact
`13046077362`, 2520 bytes, SHA-256
`91e19d4c5e2d84874b0f4c79ce0afde57dae43b9dc1d21a4861bfadfcc5ae097`,
and [unchanged JSON](e2-c01-original-one-sided.json) belong to run
`41210325811`, source `ba4aa1d783e8698bfc7e047fec389f8ef0e82f13`.
The error field preserves all 16 accounts on secondary. The stage field was
stale at `adonet-membership-setup`: that source did not update the phase before
probe_hosts. It does not establish SQL-startup failure or an accounting defect.
That original metadata is not rewritten.

## Interpretation and limits

This verifies the **controlled-fixture alternative** preregistered in #44.
Orleans 10.4.0 compatible-silo hints seed only new activations; they do not
change accepted AccountGrain, its non-reentrancy, the ledger or the observed
ResourceOptimizedPlacement default policy. Subsequent financial clients do
not use hints.

**The original concentration's cause remains unproven.** The old default
placement test and its rejection remain intact. Three jobs with fresh fixtures
do not establish cross-physical-domain HA, asymmetric partitions, in-flight
COMMIT/ACK faults, RTO/RPO, sustained capacity or mainframe equivalence.
G2=INCONCLUSIVE and G6=BLOCK. #53 frozen; no release change.

[Español](E2-C01-CONTROLLED.es.md) · [Protocol and pinned official sources](../../lab/e2_orleans/C01_CONTROLLED_PROTOCOL.md)
