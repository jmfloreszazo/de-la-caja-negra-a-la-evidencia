# E2-F10-C01: dual-silo grain placement diagnostic — NOT physical HA

**Status: implementation candidate, not original-CI evidence.** This diagnostic is deliberately limited to disposable E2-F10 Podman networks and does not modify accepted ledger transactions, Orleans actor placement policies, or the C01 financial recovery acceptance conditions.

## Original negative and scientific question

On original [C01 run #41210325811](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41210325811), the two silo gateways and PostgreSQL were reachable, yet **all 16 probed account grains were activated on secondary**. The test properly rejected its required two-silo placement precondition. A subsequent successful fresh C01 CI run did not explain the original failure. Original failure and artifact are retained in [issue #44](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/44).

Orleans grain placement is not guaranteed to distribute any fixed small set of IDs across every available silo. Repeating a client probe of the **same activated grain keys** cannot be treated as a new random placement sample. Both membership rows being Active or both gateways reachable does not establish that both silos host the sixteen requested grain activations.

## Proposed new diagnostic (no change in acceptance)

- Existing **financial-account IDs 1..16** must still have a verified original primary-hosted account and an original secondary-hosted account before testing secondary SIGKILL, reactivation and idempotent ledger replay.
- If that precondition fails after the existing bounded observation period, preserve original account mapping and the original negative C01 run. Never mark it as a successful financial failure test.
- Read independent PostgreSQL membership rows. Query **fresh diagnostic grain keys 17..64 exactly once**, using only `HostProcessId()` and `HostNodeIdentity()` — **never** `Transfer()`. This identifies whether the placement concentration also occurs for *new activations*, but these diagnostic IDs are NEVER substituted into the banking transfer fixture.
- Save the complete account placement, membership statuses, new-activation distribution and both original silo log tails to `lab/results/e2f10/e2-f10-c01-placement-negative-original.json`. The original C01 negative result remains a hard failure. A failure of the fresh-key probe itself is recorded without erasing the original failure.
- The identity-only command is opt-in and limited to `cluster client probe-range 17 48`, `E2_CLUSTER_TEST=1`, private Podman / ADO.NET fixture and expected disposable PostgreSQL `e2lab`. It is not available to production or arbitrary cluster endpoints.
- The nine offline negative controls ensure all-primary/all-secondary distributions **fail** the two-silo placement precondition, both healthy membership rows do **not** imply dual placement, stale membership fails, unknown silos/partial IDs fail, and post-kill primary-only placement is distinct from a two-silo startup.
- The original C01 recovery/7-of-7 SQL oracle and the original one-physical-host limitation remain unchanged.

## Still unverified / E2 closure gates

This instrumentation alone **does not fix Orleans placement or prove C01 repeatability**. Require new original CI with the source SHA, source artifact and negative-case provenance. Diagnose why fixed 1..16 keys concentrate on secondary before claiming a stable dual-placement baseline. Keep issue #44 open until controlled negative/positive experiments and a bounded repeated fresh-runner cohort document the cause or an explicit test-only placement mechanism is proven.

F10-C04 client-gateway isolation PR #34 remains **DRAFT and UNVERIFIED**, not part of this diagnostic. A separate physical-host HA test, symmetric/asymmetric partition, client gateway isolation, and C05/C06 recovery gates remain outstanding under issue #24. B05 load-to-saturation remains outstanding under #25; neither a C01 success nor multiple Podman namespaces prove a production mainframe MIPS/SLA equivalence.

All lab code and documentation English. Book results must be published in Spanish and English. Published release `v2026.10.29` untouched.
