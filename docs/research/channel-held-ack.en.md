# Late owner ACK overtaken by concurrent recovery: a real localhost TCP test

**5 November 2026 · issue #30 · bounded native `.NET 10 + two PostgreSQL` experiment.** [Español](channel-held-ack.es.md) · [Prior real loopback experiment](channel-loopback-transport.en.md) · [Native contract](../../lab/channels/CONTRACT.md).

## Why a single successful retry is insufficient

The earlier native transport lab [#100](../../evidence/runs/CHANNEL-LOOPBACK-TCP.md) demonstrated that a lost core response does not necessarily mean a failed transfer. But it only queried and retried the original operation sequentially **after** the old proxy response had already been dropped or delayed. This does not exercise the stronger temporal risk: while the old approval is still held in flight, multiple clients, branch terminals or gateways may race to recover or repeat the original command.

The new test uses a real TCP client, a one-shot loopback proxy and the existing real `.NET 10` API with its PostgreSQL financial store. The proxy forwards one original fictional `POST /transfer` using the original durable `operationId`, **observes HTTP 200 after the owner's database commit**, and blocks the old response on a bounded synchronization event. The initial client sees an actual socket timeout. Before the old reply is released, the test performs an original-operation status query, starts **eight concurrent real HTTP requests using the same ID and identical fingerprint**, and submits a **ninth conflicting request** using the same ID with a different amount.

Only after collecting the status, concurrent responses and read-only SQL evidence does the harness signal release of the held old reply. Within one host, source/response/recovery/release observations use `time.monotonic_ns`, allowing an explicit temporal assertion. These clocks are **not** comparable to hardware timestamps from bank, card network, switch or physically separate machines.

## Required observations and fail-closed logic

| Moment | Independent / original observation | Required invariant |
| --- | --- | --- |
| Original upstream reply before client receives it | Proxy has forwarded the bounded POST, read HTTP 200; SQL already shows one COMMITTED operation, two paired postings and one outbox | This is a **committed financial effect**, not a client-visible success |
| First client times out, response held in proxy | Python HTTP client captures `UNKNOWN`; proxy's release event is unset | Timeout cannot be treated as issuer decline or cash event |
| Original status query | `GET /operations/{originalId}` reads `COMMITTED` from the fictional SQL owner | Query must retain the same source operation identity |
| Eight concurrent same-ID replays | Eight HTTP clients obtain `COMMITTED`, `duplicate=true`, `postedCents=6000` | **Exactly one** original operation, two financial postings and one outbox persist |
| Changed-amount same-ID request | API returns `ID_CONFLICT` | Idempotency key is **bound to intent**, not permission to change its amount |
| Old response finally released | Proxy records that recovery completed **before** old ACK release | The original late reply cannot create another COMMIT |
| After-recovery independent SQL audit | Read-only oracle checks financial conservation, projection, postings, holds, outbox, identity and device separation | No negative effect hidden behind one correct aggregate balance |

The independently written [native report validator](../../scripts/check_channel_transport.py) crosschecks actual proxy stage and timestamps, original offered operation ID, the 8 HTTP responses (not just a caller's summary flag), the conflicting HTTP payload and `ID_CONFLICT`, SQL snapshots both before retries and **before release**, and the final ledger. The [adversarial mutation tests](../../scripts/test_channel_transport_evidence.py) reject fabricated response ordering, missing replays, false duplicate flags, altered IDs, extra postings, false conflict approval and impossible timestamps.

The new case is `tcp-held-reply-concurrent-recovery`; the native driver now has **14 total cases** (original 10 plus four local TCP interventions), with **18** standalone proxy guards and **26** report-evidence checks. The workflow archives original observations even on failure and checks exact source SHA. The numbers are a planned test contract until a specific original GitHub Actions result is linked and verified.

## Interpretation and migration decision

This is more realistic **client concurrency over actual local sockets** than the pure JSON event model. It still does **not** prove a network switch, ISO 8583, real ATM device, inter-host WAN partition, CICS/Db2 transaction semantics, production retry retention, actual authorization/settlement, protected device journal, original-source writer fencing or bank-approved cutover. Both PostgreSQL databases and the core run on the same host/failure domain. A true CICS/IMS or external switch may have different message identity and retry semantics; an issuer must own the end-to-end rulebook.

The benchmark is **correctness under one bounded source and transport race, not throughput/MIPS or HA**. Do not extrapolate from eight local clients to bank capacity or exactly-once external cash delivery. No stand-in authorization or automatic posting/reversal/dispense is approved. TODM **G2 INCONCLUSIVE / G6 BLOCK**, E2 `partially_verified`, #30 stays open and frozen #53 unchanged. No new release or production change.
