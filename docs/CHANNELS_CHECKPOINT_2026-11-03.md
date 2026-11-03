# Channel/core checkpoint — 3 November 2026

Tracks [#30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30), including the retained #29 scope. This is the first bounded channel increment; #30 remains open. [Español](CHANNELS_CHECKPOINT_2026-11-03.es.md).

## Original native evidence

| Original campaign | Source | Outcome and boundary |
|---|---|---|
| [41710509139](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41710509139) | `b057a875fc1485ae804222d7035e4d602271bbaf` | FAIL before cases: Python helper shadowed the HTTP module; native compilation succeeded |
| [41711114693](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41711114693) | `dd6cbb5c455907d6555fd1196f504be73eadc7eb` | PASS: ten cases, seven independent SQL oracle groups and two rejected mutants |
| [41711512319](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41711512319) | `1b206b137074c3ab175c4234d8f69780217fbb97` | FAIL before cases: Unix-socket readiness raced PostgreSQL's temporary initialization server; changed to TCP readiness |
| [41711792802](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41711792802) | `065b82b3b1b6ac2f8b7a1dab0622afbf08719732` | FAIL before cases: occupied HTTP port; the same SHA passed its PR run. Changed to a free bounded loopback port without terminating unrelated processes |

The four unchanged ZIPs live in [evidence/channels](../evidence/channels/). `scripts/check_channel_observations.py` verifies their SHA-256 digests, forty historical source hashes, original outcomes, actual amounts and raw SQL snapshots, and independently replays the seven oracle groups plus both mutants. A green repetition does not replace either failure.

The original successful environment was .NET SDK 10.0.403, Python 3.12.16, Podman 4.9.3 and PostgreSQL 16.13. Two containers share one GitHub Actions host. The report retains the resolved image identity, SQL durability settings, offered instructions, actual HTTP observations, compiler output, process markers, core logs, device logs and snapshots of both stores.

## Observed functionality

- Full, partial (requested 6,000 / delivered 4,000) and final-zero cash decisions; one financial effect under identical retries and rejection of changed intent.
- A device process killed externally after its own commit; core UNKNOWN and its hold survive until reconciliation with the original command.
- A core process killed externally before the financial commit; its SQL changes roll back while the separate device outcome survives. Restart posts once.
- Actual socket response loss after settlement/digital COMMIT; status/replay resolve the original operation without another debit.
- Competing 6,000 ATM/mobile requests against 10,000: one financial winner, one decline.
- Undispatched expiry releases the hold; pending expiry and absent journal retain UNKNOWN and the hold.
- Conserved extra cash postings and a false final decision without entries/outbox are rejected by the independent oracle. Mutants change copies; original observations remain intact.

The companion chapter in both editions adds six architecture variants, six paired diagrams (two architectures/four sequences), a withdrawal decision table, pattern tradeoffs, seven-oracle mapping and a channel-to-retirement matrix. Primary sources distinguish IBM's educational Bank of Z, CICS task/UOW semantics and CSFi's commercial stand-in example. No claim is made about an unidentified bank's deployed architecture.

## Residual validation, without blocking this increment

The emulator atomically records stock and a final journal row in device SQL. Physical notes do not participate in that transaction. No real terminal, switch/network profile, ISO 8583/NDC/DDC certification, HSM/PIN/EMV, authenticated transport or bank-approved chart of accounts is exercised. There are zero approved business requirements and no production release authorization. Stand-in is denied by design; a real issuer's permitted policy is outside this fixture. The initial script does not yet exercise a complete unavailable-core/stand-in campaign.

For external validation, replace the device assumption with instrumented delivery/retract/reject outcomes and authoritative journals; obtain issuer-approved partial/zero/expiry/reversal/dispute rules and delegated budgets; test separate network hops, protocol correlation and late messages; and exercise source-side ownership fencing, cohort cutover and recovery operators. Preregister deadlines and expected results, preserve original failures and reconcile physical, network and ledger records. Capacity, WAN costs, physical HA, source differential/Golden Master approval and the remaining #30/#29 channel matrix stay pending. The book release/version is unchanged.

## Bounded PDF review

[Run 41713039344](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41713039344), source `d3d01ec01bb55c460d106eee0a6b7424d0aaa82b`, produced 156 ES pages and 152 EN pages, with 47 diagrams plus cover per edition. All twelve channel-diagram pages were visually reviewed. Each of the six captions shares a page with its image in both languages; orphaned C.3/C.6 captions were corrected with print grouping and a focused regression. The [review record](../evidence/channels/pdf-review.json) retains ZIP/PDF/input SHA-256 identities, image locations and two PNG samples. This reviews the added material, not the entire book again.
