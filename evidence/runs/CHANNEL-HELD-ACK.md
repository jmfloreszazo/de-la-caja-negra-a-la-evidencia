# Original evidence: held upstream TCP ACK and eight concurrent recoveries

[Español](CHANNEL-HELD-ACK.es.md) · [Technical contract EN](../../docs/research/channel-held-ack.en.md) · [Actual original GitHub Actions #42052288542](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42052288542) · [PR #101](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/101).

**5 November 2026: bounded PASS on actual localhost TCP plus synthetic .NET 10/PostgreSQL financial authority; NOT a production financial, device, issuer or WAN test.**

## Original execution, not a projected plan

- **Source and checkout:** `67981c24d9164f8952e1e24ce8ecd1ec4bb582ff`; original run `42052288542`, job `127331264991`.
- **18/18** real-socket proxy/held-ACK guard checks **PASS**; **14/14** native .NET 10 + two disposable PostgreSQL channel cases **PASS** (historical 10, prior three TCP interventions, one new held-ACK race).
- **Independent read-only transport/SQL gate:** `PASS_BOUNDED_LIVE_LOOPBACK_TRANSPORT`.
- **27/27** original-evidence controls **PASS**: one valid original report and **26 deliberately corrupted variants rejected**. New negatives include fake release order, missing concurrent retries, false duplicate flags, changed operation identity, double financial posting before old ACK release, false conflict approval and a fabricated eight-way start barrier. Actual named checks and timestamped original result lines are retained in the [job-log excerpt](CHANNEL-HELD-ACK-PR101-ORIGINAL-CI-EXCERPT.log); the complete original output is retained separately by GitHub Actions.

The original run's `channels-synthetic-original` artifact has ID `13426084608`, size **23,371 bytes**, GitHub-reported SHA-256 `d012bf14f8e6e58a724df819d413dc0b765ecad4cb0ec4788078f400c281fa6b`, initial expiry **3 February 2027**. This digest is **GitHub-published metadata, not independently calculated from downloaded ZIP bytes**. [Machine-readable original-run provenance](channel-held-ack-pr101-original-ci-summary.json).

## What the new fourth real transport case checks

1. The real proxy accepts an original `POST /transfer`, forwards it to the actual disposable .NET server and sees HTTP 200 after its PostgreSQL COMMIT. **It withholds this old reply.**
2. The original client experiences a genuine TCP timeout and reports UNKNOWN. The read-only SQL snapshot **already** has **one COMMITTED operation, two paired postings and one outbox event**.
3. An owner-status GET returns COMMITTED. **Eight TCP clients synchronize their request launch with an eight-party barrier** and repeat the **same operation ID and intent**. All must return COMMITTED with `duplicate=true`; the result is not extrapolated from a purely fictional JSON trace.
4. A changed-amount command using that original operation ID must return `ID_CONFLICT`. The independent SQL snapshot **before the old ACK is released** still contains one decision, exactly two postings and one outbox.
5. Only after these recoveries does the driver release the old upstream reply. Monotonic timestamps taken on the **same host** establish original HTTP 200 before recovery completion before release. A final read-only SQL audit preserves the fictional account balances **4,000 / 16,000 / 0 cents**, without any cash-device command.

The original operation identity and fingerprints are required for recovery; this validates a narrow locally executed idempotency policy, not a universal exactly-once payment guarantee.

## Independent limits

These are **actual single-host loopback TCP sockets**, real disposable .NET 10 HTTP and PostgreSQL transactions, but **no real multi-host WAN partition, kernel packet-loss campaign, card ATM/switch, original CICS/IMS/Db2 issuer UOW, PIN/HSM, actual physical dispenser/retract journal, bank authorization, external reconciliation, source-owned writer fence, production capacity or live cutover**. The old reply is held by a testing proxy under operator control; no vendor network behavior or physical device was measured. Eight local clients are not a MIPS/throughput result.

Keep issue #30 **OPEN** for bank/network/physical acceptance and #58 open for real host fencing. TODM **G2 INCONCLUSIVE / G6 BLOCK**, E2 `partially_verified`, #53 frozen. No new release or bank authority.
