# C2 directional controller-stream suppression — original observation

[Español](BROWNFIELD-CONTROLLER-PARTITION.es.md). Tracks #58/#32. This is a bounded synthetic engineering slice, not bank cutover approval.

Original [run 41792899739](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41792899739), source/checkout `a9ae65dcf0704147d99b2af16fae4a538daa0189`, passed all four new cases. The unchanged [original ZIP](../brownfield/c2-directional-original.zip), artifact `13303828084`, has SHA-256 `7c402c85cdee0b3481edeac5a2a6518f2843b419887d7537014c256ec373a523`. It also retains the original journal and TCP-session-loss outputs from the same job; do not relabel earlier archived experiments as this source.

The declared [protocol](../../lab/brownfield/journal/PARTITION_CONTRACT.md) crosses Python legacy/.NET candidate with two directions of opaque application-stream suppression. The relay consumes/discards bytes without closing the existing sockets. TCP acknowledges the proxy's reads: this is not a kernel packet-loss emulator or an independent physical network fault.

## What was observed

| Writer | Suppressed direction | Tagged query at server | Controller state after separate financial COMMIT | Final financial effect |
|---|---|---|---|---|
| Legacy | Client to server | Not received | idle in transaction | 1 decision / 2 postings / 1 outbox |
| Legacy | Server to client | Received; client reply absent | idle | 1 / 2 / 1 |
| Candidate | Client to server | Not received | idle in transaction | 1 / 2 / 1 |
| Candidate | Server to client | Received; client reply absent | idle | 1 / 2 / 1 |

Before releasing the financial SQL barrier, independent SQL observed the adapter's real lock wait and zero visible decision/posting/outbox. Controller holder sessions remained alive and idle in transaction during a sampled interval of at least one second; original PIDs, queries and directional counters are retained. Both fresh admission and writer-switch attempts failed during suppression, without changing authority. The gateway was externally SIGKILLed (-9), while the financial child remained in flight.

Releasing the barrier allowed a durable financial effect in the separate ledger while suppression remained active. The admission was still DISPATCHING before recovery. Thus an absent client reply did not mean absent financial COMMIT. The observed idle/idle-in-transaction distinction is specific to these four attempts; it is not a universal driver or timeout guarantee.

Recovery explicitly closed all relay sessions and allowed fresh connections. Reconciliation then found COMMITTED; identical replay returned DUPLICATE_COMMITTED without additional entries. Both ledger snapshots pass ten original SQL oracle predicates each. Two altered observation copies—false absence of financial effect and false automatic recovery—were rejected; the originals are unchanged.

## Reproduction and audit

The existing C2 workflow executes the original journal matrix and connection-loss campaign before the new four-case script. The [English lab guide](../../lab/brownfield/journal/README.md) describes disposable setup. The original environment includes .NET SDK 10.0.403, Python 3.12, PostgreSQL 16.13, Ubuntu 24.04 and one runner; exact versions/image/container identities are retained in `provenance.txt` inside the ZIP.

Run `python3 scripts/check_c2_directional_observations.py` to audit the archive, thirteen historical source hashes, raw PID/query observations, all persisted snapshots and both rejected mutants. A shallow checkout needs the original source commit fetched first. The auditor extracts the historical dependency-free oracle function from its original file rather than importing database connection code or changing the protected oracle.

## Remaining acceptance

G2 stays INCONCLUSIVE and G6 BLOCK. No claim of transparent recovery, immediate financial cancellation, physical HA, native mainframe behavior, sustained capacity or a real bank-owned admission fence is made. True packet suppression/retransmission, keepalive/timeout/lock-lifetime budgets, symmetric faults, independent hosts, source-side fencing, external payment effects and approved owner policies remain follow-ups in #58. External validation does not block this clearly bounded merge.
