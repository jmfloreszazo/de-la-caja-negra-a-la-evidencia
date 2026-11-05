# Real loopback TCP interruption around a disposable .NET 10 financial core

[Español](channel-loopback-transport.es.md) · [Issue #30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30) · [Native fixture contract](../../lab/channels/CONTRACT.md) · [Previous fictional hop oracle](channel-hop-failures.en.md)

**Research cut: 5 November 2026. This is real localhost TCP behavior, not a physical ATM, bank switch, independent WAN failure domain, or production bank acceptance.**

## What changes from the seven JSON-only hop traces

The earlier [40-case per-hop trace model](channel-hop-failures.en.md) tested *consistency of declared events*. In this increment, we insert a one-shot **raw TCP proxy** on `127.0.0.1` between the Python HTTP client and the **existing .NET 10 ChannelsLab API**, backed by the original two separate disposable PostgreSQL stores. The proxy binds a random local port, only forwards `POST /transfer` to the already established fixed local core port, and closes its sockets. The independently read-only SQL oracle still reads accounts, operations, postings, outbox, holds and the synthetic device store.

The proxy deliberately preserves a single `operationId` and the original command body. It refuses non-loopback destinations, non-declared core ports, extra routes, oversized or streaming requests, unknown fault modes and a non-disposable process. It hashes the received HTTP bytes; **it does not archive the raw request or any customer credentials**. No production service endpoint is configurable. The transfer is an invented `6,000`-cent movement from fictional account 1 to 2, not a real bank command.

## Three new native cases on an actual local TCP socket

| Case | Actual transport intervention | Independent authority observation | Required client recovery |
| --- | --- | --- | --- |
| `tcp-drop-before-forward` | Client sends a real TCP request; proxy reads it and sends TCP reset **without opening any upstream connection** | Read-only SQL observes no operation, posting or outbox before retry | The original operation identity is reused; a first legitimate COMMIT creates one pair of postings |
| `tcp-drop-after-owner-response` | Proxy forwards original request, sees .NET's HTTP 200 response **after CommitAsync**, then resets client socket without forwarding response | Before retry, SQL already shows one COMMITTED operation, two paired postings and one outbox row | Client observes UNKNOWN; issuer-authoritative status query then same-ID replay returns `duplicate=true`, with no second effect |
| `tcp-delay-owner-response` | Proxy receives upstream HTTP 200 after COMMIT but intentionally waits 0.8 s, beyond client's 0.15 s timeout | SQL confirms original COMMIT and exactly one financial event | Client observes a timeout; authoritative status + same-ID replay do not create a duplicate |

The integration driver preserves the **original ten native channel scenarios** (including device response lost, partial dispense, actual server SIGKILL before commit, and race between ATM and mobile). This adds three distinct network interventions and does not rewrite earlier result files or pretend that a TCP reply loss equals lost physical cash. All three new cases use **digital transfers**, not physical dispenser commands. The read-only [post-run transport evidence verifier](../../scripts/check_channel_transport.py) explicitly requires the raw proxy stage witness, the client's UNKNOWN observation, the original SQL snapshot **before replay**, the independent financial oracle and the final ledger state after replay. The 14 fast [proxy refusal tests](../../lab/channels/test_transport_proxy.py) separately exercise input rejection, loopback-only binding and an actual pre-forward TCP reset.

**Executed evidence:** [original run #42033452330](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42033452330) passed **14/14 proxy safety cases, 13/13 native channel cases and the independent read-only SQL transport gate**. [Strengthened run #42034784257](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42034784257) additionally passed **18/18 original-evidence controls** (17 forged mutations correctly refused). Full [EN audit](../../evidence/runs/CHANNEL-LOOPBACK-TCP.md) / [ES](../../evidence/runs/CHANNEL-LOOPBACK-TCP.es.md) preserves original SHAs and limitations; neither ZIP artifact was independently rehashed.

## What the PASS can and cannot mean

The proxy test provides evidence of a **real local TCP socket reset or response delay** using disposable .NET and PostgreSQL. It is **not** a kernel-level `tc netem` injection, packet loss between hosts, a network-switch failure, a disconnected branch, a certified ISO 8583 endpoint, a CICS/Db2 mainframe UOW, a real issuer query, or physical ATM cash delivery. The two database containers still share one host and failure domain. The status query is only authoritative **within the fictional SQL fixture**. Confirmation of an HTTP 200 response header is combined with an independent SQL snapshot; it does not turn the proxy into a trusted host log.

A controlled *before-forward* witness can establish that **this test proxy never contacted the application**, but it is not a universal client-side guarantee: in a real network, a timeout alone cannot tell whether the server committed. Retrying under a **new identity** would be unsafe. The bank must approve the identity, response ambiguity, timeout, retention and dispute policies, and independently authenticate the original source decision and physical effects.

### Operational acceptance still missing

To represent real channel operation, a source owner must provide isolated ATM/switch/issuer components under a sanctioned test network, independently collected raw TCP and authenticated application traces with monotonic/timestamp limitations, fault injections between actual hosts/ports, durable issuer COMMIT log and device dispense/retract journal, card-network retry/stand-in/reversal rules, and evidence of incumbent source fencing across all writers. Physical network partitions, switch or HSM behavior, fault-domain independent recovery and business risk acceptance remain **open external evidence**, not hidden PASS criteria.

Even when the bounded native campaign passes, every outcome must retain **TODM G2 = INCONCLUSIVE, G6 = BLOCK**, **no bank cutover**, no production financial authority, E2 `partially_verified` and frozen issue #53. The release remains unchanged.
