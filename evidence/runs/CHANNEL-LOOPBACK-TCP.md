# Real loopback TCP / .NET 10 / PostgreSQL recovery — original bounded CI evidence

[Español](CHANNEL-LOOPBACK-TCP.es.md) · [Issue #30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30) · [Research EN](../../docs/research/channel-loopback-transport.en.md) · [Original CI run](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42034784257).

**5 November 2026. Actual single-host 127.0.0.1 TCP socket loss/delay was executed against a disposable .NET 10 API and PostgreSQL transactions. No real ATM, financial issuer, WAN partition or production approval.**

## Executed and independently checked

[Initial native run #42033452330](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42033452330), job `127265416676`, source/checkout `6b742fdef4d0b2c134b7dc41fbb94c57acd8c599`: **14/14 one-shot TCP proxy safety controls PASS; native driver 13/13 cases PASS; original read-only SQL and socket-stage gate `PASS_BOUNDED_LIVE_LOOPBACK_TRANSPORT`**. The ten historically accepted native cases were preserved, with three new, separately labeled TCP interventions. [Initial original-run log excerpt](CHANNEL-LOOPBACK-PR100-ORIGINAL-CI-EXCERPT.log).

[Strengthened native run #42034784257](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42034784257), job `127269987076`, exact source/checkout `1a4effced7b5bad20ef117a3b20d0917a7f5673e`: **14/14 proxy tests PASS, 13/13 native cases PASS, independent SQL/transport gate PASS and 18/18 original-evidence tests PASS** (one true original plus **17 deliberately forged or corrupted evidence mutations** which the validator must reject). [Original timestamped excerpt](CHANNEL-LOOPBACK-PR100-EVIDENCE-MUTANTS-CI-EXCERPT.log).

The 17 adversarial modifications include false production/WAN authority, supposed upstream traffic for a pre-forward drop, invented postings, fake client success, missing original COMMIT, deleted outbox, a fake idempotency flag, a conservation-preserving balance manipulation, duplicate final posting, false physical network success, and false SHA provenance. The test suite mutates copies **after the source run**, not the saved originals.

## Exact transport stages and durable financial observations

| Case | Original client/socket observation | Independent SQL observation | Recovery |
| --- | --- | --- | --- |
| `tcp-drop-before-forward` | Client opens loopback socket; proxy records request then resets it without any upstream connection; client UNKNOWN | Before replay: zero operations/postings/outbox | Same operation ID, **first** COMMIT creates one operation/two postings/one outbox |
| `tcp-drop-after-owner-response` | Proxy forwards request; receives core HTTP 200 produced after .NET `CommitAsync`; resets client socket without forwarding HTTP reply; client UNKNOWN | Before replay: one COMMITTED operation, exactly two postings, one outbox | Status query on original operation ID + replay `duplicate=true`; unchanged financial effect |
| `tcp-delay-owner-response` | Actual upstream HTTP 200 delayed **0.8 s** beyond real client timeout **0.15 s** | Before replay: original COMMIT and exactly one outbox, two postings | Status query and original-ID replay, no second transfer |

Each after-recovery original SQL snapshot has fictional account balances **4,000 / 16,000 / 0 cents**, with exactly one transfer and one outbox row; the read-only independent ledger oracle reports PASS. These are **synthetic digital transfers**. No dispenser command or real cash delivery occurs. The proxy stores request SHA-256, stages, transport status and byte counts, but not raw command bodies; the original driver preserves HTTP observations and full SQL snapshots in the workflow artifact.

GitHub published the initial workflow artifact `13417117169` (21,334 bytes), SHA-256 `433e46a9c72b87634d3b3c966ecb27f00dc981d663ef22c00e6e9a323fdc5eec`, and strengthened artifact `13418031808` (21,972 bytes), SHA-256 `c794a6739fe050d69df22de37f8883c1280b88dd03fd7131a84be34952939118`, with initial expiration 3 February 2027. **Both digests are GitHub-reported artifact metadata; neither ZIP was independently downloaded and rehashed in this audit.** The full originals, raw app/device logs and SQL snapshots are in those original workflow artifacts. The [machine-readable audit](channel-loopback-pr100-original-ci-summary.json) retains metadata and scope.

## What this evidence does not support

This is actual local socket manipulation between Python and the synthetic .NET transfer API, **not kernel `tc netem` packet injection**, a real inter-host TCP/WAN loss, physical HA, a deployed ATM, a card switch, a customer bank, an issuer policy, an IBM CICS/Db2 UOW, native source fencing or actual notes being dispensed. The C# core and two PostgreSQL containers remain in a **single failure domain**. The synthetic operation-ID and SQL-replay policy are *not bank certified*.

The independent oracle establishes the bounded financial effects **inside the disposable fixture**, not the completeness of a real bank's online, batch and privileged writers. It is not valid to infer that a client-only timeout always means no COMMIT or that a new operation ID is safe. Any real authorization, stand-in, posting, reversal, hardware, remote-network and cutover checks remain with the source owner and customer policy. **TODM G2 INCONCLUSIVE / G6 BLOCK**, E2 `partially_verified`; #30 and #58 remain OPEN, #53 frozen. No new release/tag or production cutover.
