# W01 — A read projection does not own the balance

**Issue #32 · Brownfield implementation note · 4 November 2026.** [Español](w01-projection.es.md). **Scope:** two independent PostgreSQL 16.13 server containers on **one** Linux host, one synthetic legacy ledger and one nonauthoritative read projection. An executable real-PostgreSQL experiment, **not** IBM Z, CICS, IMS, Db2, production bank data, physical HA or customer acceptance.

## Hypothesis and why W01 is the first extraction

W01 selects CAP-005 (balance enquiry) from the 30 **unobserved** reference capabilities. The customer-visible read may be decoupled without moving the CAP-007 ledger writer. **But** booked balance, available funds, authorization and ATM cash dispensing are separate contracts. W01 returns a booked balance for synthetic demonstration, **never spendable/authoritative funds**. A real customer must establish permissions, acceptable staleness, exceptions, SLO and the meaning of as-of versions before using a projection.

The baseline is a deliberately synthetic **legacy PostgreSQL schema**, not an emulated mainframe. The existing legacy financial tables are only modified by a separate *test-only* fixture writer that increments the source clock **inside the same SQL transaction** as paired postings/outbox. The **projection application** only opens source transactions as `REPEATABLE READ READ ONLY`.

## Execution design

```text
  Test-only source transfer
         │  single financial COMMIT + source sequence
         ▼
  PostgreSQL bf_legacy (port 55438)     ← authoritative
   legacy.accounts + legacy.clock
         │
         ├─ consistent READ ONLY snapshot ──→ refresh worker
         │                                      │
         │                               single target COMMIT
         │                                      ▼
         │                           PostgreSQL bf_projection (55442)
         │                            accounts + watermark + digest
         │                                      │
         └─ source clock sample ───────┬──────→ read decision
                                      ├ current integrity-checked → projection
                                      └ stale/corrupt/unavailable → source fallback
                                                                or BLOCK
```

There is **no CDC/event transport or incremental catch-up**. Refresh reads all 16 synthetic accounts and the source clock from one consistent PostgreSQL snapshot, then replaces the projection and its watermark in a **single target transaction**. A repeated snapshot rebuild is idempotent. At the same source watermark, changed source balances cause refresh to refuse an **unversioned source mutation**. At a lower clock, refresh refuses regression. A tampered projection is refused on reads by checking its complete digest and is only repaired by explicit rebuild.

### Read decisions

| Condition | Response | Important limitation |
| --- | --- | --- |
| Integrity-checked projection clock equals sampled source clock, and meets client minimum | `PROJECTION_OBSERVED_CURRENT` | A source commit immediately **after** clock sampling may make it stale; **not linearizable** |
| Projection absent, stale, tampered or unavailable; source snapshot healthy | `AUTHORITATIVE_FALLBACK` | The source snapshot is consistent, but this has no customer authentication or business approval |
| Client minimum watermark greater than source clock | `BLOCKED_MINIMUM_WATERMARK` | Never silently discard the requested freshness condition |
| Source clock unreachable | `BLOCKED_SOURCE_UNAVAILABLE` | Never serve potentially stale account funds as if current |
| Fallback source snapshot unavailable or inconsistent | `BLOCKED_FALLBACK_UNAVAILABLE` | Fail closed; no last-known balance masked as current |
| Source changes without advancing its declared clock | Rebuild refuses `UNVERSIONED_SOURCE_MUTATION` | **Watermark-only reads cannot detect this bypass at query time.** Must prove actual source-side writer discipline before any production trust |

The client-supplied minimum watermark is a synthetic test input, not a substitute for causally bound read-your-writes tokens or certified global transaction order. Reads first sample source sequence, then projection state; this is not an atomic cross-database read. The source clock round-trip also means **no capacity/p99 improvement is asserted**. A real read model would need explicit CDC/resnapshot boundary, ordering/gap detection, source-owned version semantics, authentication, latency budget, and freshness/authorization SLO.

## Verification and evidence contract

The [English-only lab](../../lab/brownfield/w01_projection/README.md) runs in Podman and requires exact disposable databases `bf_legacy:55438` and `bf_projection:55442`, with the `W01_DISPOSABLE=YES` guard. Tests reset only these named disposable schemas; never point them at real financial data.

The new independent test suite covers *first refresh, stale fallback after a real committed SQL transfer, idempotent rebuild, minimum-watermark refusal, projection corruption/repair, changed source at unchanged clock, clock regression, primary and fallback unavailable, input/endpoint safety, independent PostgreSQL cluster identities, and no source mutation by projection*. It also verifies a persisted financial oracle (balance conservation, two postings, single outbox, clock consistency and bounded account revisions). CI records exact source/checkout SHA, PostgreSQL image/runtime identities, original stdout/stderr, per-run JSON and negative cases as downloadable artifacts **whether the test succeeds or fails**. These are **synthetic functional observations**, not MIPS parity, throughput, automatic failover or real bank semantics.

**TODM G2 = INCONCLUSIVE and G6 = BLOCK** regardless of a green CI run. The prototype has no approved policy or Golden Master. The previous [wave gate](mainframe-extraction-waves.en.md) is a structural screen; this PostgreSQL lab exercises a *bounded implementation mechanism*. Neither can certify the customer source or replace [real incumbent fencing acceptance](../BROWNFIELD_SOURCE_FENCE.md). A future full W01 acceptance must prove the real legacy source clock, unbypassable source-owned writes, CDC/gap or snapshot boundaries, client consistency policies, load and failure behavior, authorization, real reconciliation and independent owner signoff.

## Result scope

Until there is an original exact-SHA CI run, the new code is **a candidate with tests pending**, not an executed result. After CI succeeds, cite its original action URL and artifact, not merely the presence of this file. This increment does not close #32 or #58, change E2, authorize a release, or reactivate frozen #53.
