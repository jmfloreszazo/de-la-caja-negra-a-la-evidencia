# E2-F10-C04 — External-client gateway isolation

Status: **implementation candidate, NOT verified evidence**. This protocol records the proposed experiment; no GitHub-hosted C04 run has passed. The attempted creation of the dedicated C04 Actions workflow was blocked by the connected tool's safety controls. Do not work around the block or report it as CI execution.

## Hypothesis and narrow scope

When only the **external Orleans client's** outbound gateway connections are interrupted, the PostgreSQL ledger must remain the authority for all durable effects. Cutting one gateway should allow a fresh client to route through the surviving gateway (including a grain hosted on the other silo). Cutting both gateways should remove the client's ability to obtain an acknowledgement; the independent SQL observer, not timeout semantics, must determine whether any transfer was committed.

The test targets a disposable, single physical Ubuntu runner with four isolated Podman namespaces (PostgreSQL 16.13, two Orleans 10.4.0 ADO.NET silos and a separate client). The APP and SQL bridges have distinct private subnets. The client only receives test-local outbound firewall rules. The silos and database must remain alive.

## Predeclared acceptance

1. Inspect and record four distinct network namespaces, container IDs, fixed addresses and actual process IDs; verify both ADO.NET membership rows active and both client gateways reachable.
2. Commit a baseline transaction and require 1 operation / 2 postings / 1 outbox event and seven independent SQL oracles.
3. Block **only the external client's primary gateway** TCP destination and prove secondary gateway and PostgreSQL remain reachable. A **fresh client process in the same isolated client container/network namespace** must commit a transaction to a grain confirmed on the primary silo through the remaining gateway. Require 2/4/2 durable effects, exact 1 operation/2 postings/1 outbox for this individual operation, and SQL oracle 7/7. This is a fresh-client fallback case, not seamless recovery of an already-connected client.
4. Block the secondary client gateway as well. Verify both endpoints are unreachable from the client while both are healthy from the silo namespaces; the client retains SQL connectivity. Attempt a new operation with a stable ID. Require an **actual transport-related client exception or timeout**; a normal non-COMMITTED business response is insufficient. Reject unrelated process/runtime errors; the test must never match the application name alone as evidence of a gateway outage. Inspect authoritative SQL before and after the attempted request and at three additional one-second intervals **while both cuts remain active**. Require no new operation/posting/outbox rows. A startup failure is **not** a proven in-flight financial-request failure.
5. Remove both rules, prove client gateway recovery, and retry the identical operation ID. Require COMMITTED, followed by DUPLICATE_COMMITTED, and exactly 3 operations / 6 postings / 3 outbox rows in total. Each of the baseline, fallback and retried operations must individually have exactly 1 operation / 2 postings / 1 outbox row. SQL oracles remain 7/7.
6. Persist **unmodified** original PASS or FAIL observations, fault rules, timing, command responses, membership snapshots, source hashes and CI run/head SHA. Any failure or inability to inject a real network fault fails the slice; there is no synthetic PASS.
7. Verify pre-existing E2-F10-C01/C02/C03 regressions. Publish an ES/EN book interpretation only after successful original CI and independent artifact audit.

## Security and evidence boundaries

- Run against **disposable private** Podman networks only; this is not intended for production, live banking networks or third-party hosts.
- Use no public interfaces or endpoints, never bypass host authorization or tool security controls.
- Fail closed on missing netfilter permissions or unavailable CI, preserving diagnostics for inspection.
- Do not infer a rollback from a client timeout, and do not infer physical host HA or fencing from network namespaces.
- This does not establish post-COMMIT response loss, asymmetric split-brain behavior, independent physical failure domains, RTO, sustained capacity, or mainframe MIPS equivalence.
- Maintain the published release v2026.10.29 unchanged, and keep E2 overall partially_verified.

## Implementation status

Candidate source: lab/e2_orleans/test_client_gateway_partition.py.

The dedicated workflow is **not committed** due to the safety block reported above. CI must not be claimed as passing. Source code and technical documentation remain English; editorial book content will be Spanish and English.
## Previous C01 baseline regression

Draft PR #34's original C01 workflow attempt failed during the disposable PostgreSQL first SQL connection, before Orleans startup. The bounded retry of the failed job passed. Preserve both outcomes; the cause is not established. Track root-cause investigation and diagnostic readiness hardening in [issue #35](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/35), separately from this C04 slice. C01 rerun success must never be counted as an executed C04 test.
