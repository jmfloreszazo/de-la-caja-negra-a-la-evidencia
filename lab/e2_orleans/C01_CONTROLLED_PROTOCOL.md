# C01 controlled activation fixture — issue #44

**SOURCE CANDIDATE: no accepted controlled-fixture execution yet.** This is a
separately preregistered experiment, not a weakened historical C01 assertion.
It addresses the controlled-alternative exit in #44; it does not identify why
the original default-policy run concentrated sixteen keys on secondary.

## Mechanism verified against the official source

Orleans 10.4.0, upstream commit
`d114d7522a53b8cce4c6b97d44293e5c7273d766`, uses
[resource-optimized placement by default](https://github.com/dotnet/orleans/blob/d114d7522a53b8cce4c6b97d44293e5c7273d766/src/Orleans.Runtime/Hosting/DefaultSiloServices.cs).
Its [placement director](https://github.com/dotnet/orleans/blob/d114d7522a53b8cce4c6b97d44293e5c7273d766/src/Orleans.Runtime/Placement/ResourceOptimizedPlacementDirector.cs)
honors a compatible-silo
[request-context hint](https://github.com/dotnet/orleans/blob/d114d7522a53b8cce4c6b97d44293e5c7273d766/src/Orleans.Core/Placement/IPlacementDirector.cs).
The upstream [placement test](https://github.com/dotnet/orleans/blob/d114d7522a53b8cce4c6b97d44293e5c7273d766/test/Grains/TestInternalGrains/TestGrain.cs)
uses the same hint/remove pattern. A hint is not a financial lock, a request
admission or a command to relocate an already active grain.

The new identity-only CLI is restricted to the exact private C01 ADO.NET
fixture, fixed cluster/service IDs, two Active silo endpoints and account keys
1..16. It reads real generation-bearing silo addresses from management and
sets a hint only while requesting HostNodeIdentity/HostProcessId. It clears
the context in finally. Accepted AccountGrain, its non-reentrancy and the
PostgreSQL ledger are unchanged. Normal clients do not set hints.

## Predeclared controls and acceptance

1. Three matrix cohorts run as separate fresh GitHub-hosted jobs, with no
   fail-fast cancellation and all failures archived. Each cohort uses fresh
   four-namespace fixtures for its negative and positive cases. Record source
   and checkout SHA, runner name/hostname, image digests and file hashes.
2. **Negative:** seed financial account IDs 1..16 on secondary only while both
   SQL membership rows are Active. The unchanged require_dual classifier must
   reject that legitimate concentration. Identity probes make no Transfer
   calls and independent SQL must remain at 0 operations/0 postings/0 outbox,
   with 7/7 accounting oracles. A new alternating-hint probe must still observe
   the existing secondary activations, not pretend that retries redistribute
   them. No bank-transaction failure is inferred from this expected rejection.
3. **Positive:** reset the entire fixture; seed odd keys on primary and even
   keys on secondary. Require observed 8/8 placement, real SQL membership and
   exact original 1..16 cardinality. A normal new client without hints must
   observe the same mapping before two durable transfers, whose source grains
   must run on their independently proven original hosts.
4. Kill secondary with actual SIGKILL/137 after acknowledged transfers. Require
   reactivation on primary, membership 3-to-6 and version advance, identical-ID
   DUPLICATE_COMMITTED and a new COMMITTED command. Exact SQL effects are
   3 operations/6 postings/3 outbox with seven independent invariants.
5. Recreate secondary as a fresh container, keeping the original ledger.
   Require a new container ID, new Active SQL membership generation, retained
   old Dead generation and unchanged persisted business tables/oracles. Never
   accept an old READY log as proof of restart.
6. Accept this **controlled fixture** only if all three original cohorts pass
   on the same source SHA and their original artifacts are audited. Preserve
   the original one-sided failure archive: run #41210325811, source
   `ba4aa1d783e8698bfc7e047fec389f8ef0e82f13`, artifact `13046077362`,
   SHA-256 `91e19d4c5e2d84874b0f4c79ce0afde57dae43b9dc1d21a4861bfadfcc5ae097`.

## What must remain unclaimed

Each case has ONE physical runner and one non-HA PostgreSQL container. Three
fresh runner jobs are repetitions, not a cross-host HA deployment. No original
root-cause explanation, default placement-policy fix, in-flight COMMIT/ACK
loss, asymmetric partition, production RTO/RPO, sustained-capacity ceiling or
mainframe equivalence is established. Overall E2 stays partially_verified,
G2 INCONCLUSIVE/G6 BLOCK, #53 frozen and release/tag identifiers unchanged.
The older default-placement C01 test and its rejection remain intact.
