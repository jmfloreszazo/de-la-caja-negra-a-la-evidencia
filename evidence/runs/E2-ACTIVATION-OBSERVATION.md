# E2 · Activation request envelopes and durable effects

**Two bounded observations audited, 3 November 2026; E2 remains partial.**

[Original run #41619587080](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41619587080),
source/checkout `362ee5a7537e1523caad2bd7033ec7a99977ac2d`.
The separate observer host references the unchanged financial grain/ledger.
Logging affects timing: these results describe this host, not earlier runs.

| Observation | Primary outbound blocked | Secondary outbound blocked |
| --- | --- | --- |
| Original job / artifact | 125861600757 / 13223905279 | 125861600090 / 13223137998 |
| ZIP bytes / source hashes audited | 39139 / 77 | 39919 / 77 |
| Recorded process/container generations | 4 | 4 |
| Complete Transfer request envelopes | 38 | 39 |
| Incomplete envelopes / incomparable candidate pairs | 0 / 0 | 0 / 0 |
| Overlaps across distinct activations of the same grain | 0 | 0 |
| COMMITTED / DUPLICATE_COMMITTED / ID_CONFLICT | 3 / 30 / 5 | 3 / 30 / 6 |
| Recovery mode | Both silos recreated | Both silos recreated |
| Recovery criteria after rule restoration, seconds | 60.578 | 57.816 |
| 14 paired replay samples: actual span, seconds | 66.334 | 66.043 |
| Final operations / postings / outbox; SQL invariants | 3 / 6 / 3; 7/7 | 3 / 6 / 3; 7/7 |

The fault schedules lasted 120.000119 and 120.000090 seconds. The schedule
does not prove both silos stayed alive throughout it. Each case used **one
physical host**. Every ACK has a compatible recorded completion and reconciles
with SQL; both cases retained amount 37 for the contested ID.

Full logs were saved before old/new container removal. They contain actual
Orleans activation IDs, grain/call IDs, process sessions and sequences,
payload/result, monotonic ticks/frequency, boot ID and time namespace. Four
distinct sessions per case distinguish repeated container PID 1. Identical
boot/time namespace and frequency allowed within-case clock comparisons.
An idle generation's readiness marker does not imply financial-call coverage.

**No positive concurrent-activation case was observed.** The 38/39 complete
request envelopes have no detected overlap across distinct activations of the
same grain. This does not establish global exclusivity, activation lifetimes,
absence of split brain or absence of unobserved requests. Even a positive
filter-envelope overlap would not measure simultaneous SQL execution.
The next #24 gate remains a targeted positive concurrent-activation scenario
with independent SQL acceptance. #25 sustained capacity and independent
physical domains also remain open.

## Original bytes and reproduction

- [Primary ZIP](e2-activation-primary-original.zip) / [byte-identical summary](e2-activation-primary-original.json): SHA-256 `9ffb4ef62e7ee040a139490b3dc3dc6df46fdeff6fedbfd9a07a5b92b1213e62`.
- [Secondary ZIP](e2-activation-secondary-original.zip) / [byte-identical summary](e2-activation-secondary-original.json): SHA-256 `84ee1d79ed0021dc7fb9c3e7a81f270c78076bee7ccaddd3631f5c80d5470368`.

The [offline auditor](../../scripts/check_e2_activation_observations.py) pins
both digests, checks all 77 hashes against the original Git commit, recomputes
log intervals, reconciles successful results/ACKs with SQL, checks sampled
recovery and parses original PCAP bytes. It never extracts or rewrites a ZIP.

G2 INCONCLUSIVE/G6 BLOCK; #53 frozen; no release/tag change.

[Español](E2-ACTIVATION-OBSERVATION.es.md) · [Protocol](../../lab/e2_activation_observer/README.md)
