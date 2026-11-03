# E2 · A failed provider must retain its own evidence

**Original observation controls verified, 3 November 2026. E2 remains partial.**

[Run #41601478234](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41601478234)
on source/checkout `c547c3f34badda0cb57ab0b496917dadb1485b04` passed both
parent controls: development job `125801005081`, ADO.NET job `125801005414`.
These are two fresh runner jobs, each on one physical host, not a multi-host test.

## Unmodified original artifacts

| Provider | Original artifact | Bytes | ZIP SHA-256 |
| --- | --- | --- | --- |
| development | 13214437651 | 17676 | 56db17efe633841faee910d62b64f51cc8ee100700a3b2c8489310d557d98fb8 |
| adonet | 13214985556 | 18515 | 1d06e1c7541b5a14f515bf720911302ec72dd3ce0383e042e5fc45f7eb818035 |

ZIPs: [development](e2-loopback-observation-development-original.zip),
[adonet](e2-loopback-observation-adonet-original.zip). Byte-identical parent
summary extractions: [development](e2-loopback-observation-development-original.json),
[adonet](e2-loopback-observation-adonet-original.json).
Both archive digests and all 69 provenance source hashes per job were recomputed
against the exact original commit. Copied silo logs and JSONL journals were
also independently checked by SHA-256. Each original archive contains its
child FAIL, manifest, journal, original log snapshots and exact provenance.

## What actually ran

| Observation | development | adonet |
| --- | --- | --- |
| Actual first-probe placement, primary / secondary | 7 / 9 | 10 / 6 |
| Child outcome after intentional first-probe rejection | FAIL, exit 1 | FAIL, exit 1 |
| Failure phase | placement-convergence | placement-convergence |
| Original financial account IDs | 1..16 | 1..16 |
| Financial invocations, commands, SIGKILL | 0 / 0 / none | 0 / 0 / none |
| Independent operations / postings / outbox | 0 / 0 / 0 | 0 / 0 / 0 |
| SQL accounting oracles | 7/7 | 7/7 |
| SQL membership | Not applicable | Both generation-bearing members Active |
| Observed runtime placement strategy | ResourceOptimizedPlacement | ResourceOptimizedPlacement |
| Journal events | Six, sequential, one execution ID | Six, sequential, another execution ID |

The parent opted into an exception immediately after the first real 1..16
identity probe. Both original maps happened to span the two servers. This
**does not reproduce the natural one-sided historical failure**; it tests
whether the failure recorder preserves the real map without changing it.
Actual server PIDs, independent client PID, full client stdout/stderr,
membership snapshots and policy/ready logs are retained. Observer failures
are explicit errors; they are not replaced with empty successful results.

A byte-identical valid historical development PASS from the previously
[preserved regression archive](e2-c05-loopback-placement-failure-original.zip)
was deliberately supplied as an **old input**, not generated as a new success.
Its SHA-256 is `a5c3e12d6307101a5d14ebe81cabed4e19882b2932db2288a24cb14277f9ba4d`.
The new execution manifests remain FAIL and reference their own failure files;
neither claims that old PASS as this job's result. The parent reports
NEGATIVE_CONTROL_VERIFIED, not failover or financial transaction PASS.

## Scope and remaining question

The strict dual-PID assertion, original keys, wait budgets, financial calls,
SIGKILL behavior and accepted C# grain/ledger/default policy are unchanged.
The optional client observer preserves the default in-flight helper path.
Each normal attempt now writes provider/execution-specific records and, if
successful, a manifest bound to its provider's newly written success file.
Raw log copies are failure-time snapshots taken before process cleanup.

This verifies **observation persistence and provider/result provenance**.
It does not explain the earlier default concentration, prove exclusive
activation, reproduce a spontaneous placement anomaly, establish failover,
physical HA, long-partition recovery, sustained capacity or overall E2
acceptance. Issue #74 stays open for the natural-placement investigation.
G2 INCONCLUSIVE/G6 BLOCK; #53 frozen; no release/tag change.

[Español](E2-PLACEMENT-OBSERVATION.es.md) · [Protocol](../../lab/e2_orleans/LOOPBACK_OBSERVATION_PROTOCOL.md)
