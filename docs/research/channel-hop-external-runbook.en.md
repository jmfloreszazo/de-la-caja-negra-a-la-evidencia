# H01/H02 external-host execution plan (not yet executed)

**Status:** design and reproducibility checklist. The real experiment is NOT_EXECUTED. Tracks #30 and builds upon the existing single-host native 14-case fixture.

## Preconditions
- Use three isolated hosts or clearly declared, separately operated VMs: synthetic caller, gateway/fault injector, .NET 10 core. The PostgreSQL service and read-only evidence observer must have explicitly named separate roles. Distinct VMs sharing a physical server do not establish independent physical fault domains.
- Use disposable synthetic accounts and a reserved lab-only network. No production endpoints, real ATM device, issuer approval, HSM/PIN data or financial instruments.
- Require operator-controlled allowlists and mutual transport authentication at the host/network boundary. **Do not repurpose the loopback-only `OneShotTransportFault` as a remotely exposed unauthenticated listener.** Its strict loopback-only restriction is an intentional safety property.
- Observe the actual deployed SHA (Git SHA-1 40 hex or SHA-256 64 hex), container digests, .NET/PostgreSQL/OS versions, time-sync uncertainty and UTC plus monotonic per-host records. Local monotonic clocks cannot be compared across hosts without a documented correlation method.
- Establish a read-only, independently executed SQL query for operation identity/fingerprint, decisions, exactly two compensating postings, exactly one outbox record, hold/balance and any unknown states.

## Order of operations

1. Preflight network isolation and fail-closed authentication; record inventory before sending any synthetic request.
2. H01-a: drop caller→gateway before gateway receives the request. Verify that no owner transaction exists *as observed*, not merely that caller timed out.
3. H01-b: allow one owner commit and suppress the return before caller observes it. Before replay, capture the independent SQL snapshot and gateway/owner logs.
4. H02-a: drop gateway→core before delivery. Record actual socket and core observations.
5. H02-b: interrupt only the gateway/core response *after* owner's durable COMMIT, then query status and replay the **same** operation ID and fingerprint.
6. In each case inject same-ID retry and conflicting-fingerprint retry. Reject duplicate financial effect, unauthorized automatic cash dispensing/reversal, or a new writer authority on UNKNOWN.
7. Preserve all FAIL/INCONCLUSIVE runs and unmodified original logs. Collect at least six per-case files: fault/client/gateway/core/SQL/oracle logs, each with SHA-256, in a portable bundle.
8. Run `python3 scripts/check_channel_hop_campaign.py <bundle>/manifest.json` only after collection. Structural readiness is **not a distributed PASS**. An independent operator must validate packet paths, source logs, timestamps, topology, database authority and original bytes.

## Interpretation
Single-host Actions validates only the checker and its negative controls. No production approval, true multi-host run, original mainframe UOW, ISO 8583, real issuer/device, physical HA, bank business policy or capacity parity is asserted. TODM G2 INCONCLUSIVE and G6 BLOCK are mandatory. Never promote a release because this intake gate passes.
