# E2 · Directed incoming requests on ordinary AccountGrain activations

**Mixed first trial: secondary-outbound positive witness, primary-outbound INCONCLUSIVE. E2 stays partial.**

[Original run #41634279617](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41634279617),
source/checkout `bfc7662df377632a34d1fb076cdc2de0291e4021`.
The aggregate workflow failed because the predeclared primary-outbound target
returned exit 2, not because that case is retrospectively called PASS.

| Original observation | Primary outbound blocked | Secondary outbound blocked |
| --- | --- | --- |
| Job / artifact | 125911380313 / 13230102837 | 125911380060 / 13230017227 |
| ZIP bytes / source hashes audited | 47665 / 84 | 53204 / 84 |
| Directed target | INCONCLUSIVE_NO_LIVE_OVERLAP | PASS_DIRECTED_REQUEST_OVERLAP |
| Complete request envelopes / additional client outcomes | 37 / 19 | 51 / 25 |
| Incomplete envelopes / observed overlaps | 0 / 0 | 0 / 1 |
| Specific ordinary-grain witness overlap | None | 5.059981 ms |
| Final operations / postings / outbox; independent invariants | 3 / 6 / 3; 7/7 | 3 / 6 / 3; 7/7 |
| Recovery mode | Both silos explicitly recreated | Both silos explicitly recreated |
| Recovery criteria after rule removal, seconds | 59.802 | 60.059 |
| 14 paired replay samples: actual span, seconds | 66.301 | 66.266 |

## What the positive witness establishes

The ordinary financial `AccountGrain`, SQL ledger and default placement are
unchanged. A separate test filter deliberately holds one secondary request
**before** invoking the financial method. Under the verified secondary OUTPUT
DROP, another primary-hosted activation accepted a request for `account/2`.
The witness retains distinct actual activation/session IDs, both original
processes sampled running and the original DROP rule present. The specific
old/new envelopes overlap and both complete successfully. SQL contains one
contested operation for amount 31. The primary request COMMITTED; the released
old request returned DUPLICATE_COMMITTED. Additional amount-37 attempts were
reconciled against the same durable winner; no extra posting/outbox effect
was accepted. Every recorded ACK is checked against persisted SQL.

This establishes a **directed incoming-envelope witness**, not concurrent
execution of both SQL transactions. The pre-invoke delay changes timing; it
does not demonstrate natural unmodified partition behavior or simultaneous
globally Active activation lifecycles. Both jobs use one physical host each.

## Limitations and retained negative history

The primary-outbound case did not produce the required live witness. It stays
INCONCLUSIVE; its financial/recovery checks do not turn that target into PASS.
Each case later observed the blocked silo exited with **code 139**. Cause is
not established here. This first collector retained full silo stdout but **not
stderr**; its ZIPs are unchanged and the gap is explicit. Consequently no full
process-diagnostic completeness or overall partition acceptance is claimed.
A correction captures both streams before every removal; its repeat requires
separate original evidence and audit. No criteria are relaxed to obtain overlap.

## Repeat with both log streams retained

[Run #41635681137](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41635681137),
exact source/checkout `c1d174d263b453c9e1a55420f90ad42f091ef88a`, retains
stdout **and stderr** before each old/new silo removal. Both directions returned
INCONCLUSIVE_NO_LIVE_OVERLAP: 37 complete envelopes each, zero incomplete calls
and zero overlaps; 21/19 additional client outcomes. SQL/recovery acceptance
remained 3/6/3, 7/7 independent invariants and 14 paired replay samples. The
earlier 5.06ms witness was therefore **not reproduced in this repeat**.

In both repeat jobs, primary stderr records MembershipTableManager declaring
the local silo Dead according to membership and entering KillMyselfLocally /
FatalErrorHandler. SQL membership also records that primary generation as
Dead (6); the sampled container later has exit code 139. This identifies the
observed fatal membership path in these repeats. It does not establish why
that victim was selected across all directional cases or retroactively explain
the first run's missing stderr. Both silos were explicitly recreated for recovery.

| Repeat artifact | Bytes | ZIP SHA-256 |
| --- | --- | --- |
| Primary 13231480372 | 51039 | 5a40e80ef394005b3e6dbffb9299472fd5204a64750488ed7ae79d961b28b375 |
| Secondary 13230786131 | 50537 | a25d19553937f309801eeb094b048c48203a6ac40a823822510a44ea9b6231f1 |

[Primary repeat ZIP](e2-account-directed-primary-stderr-original.zip) /
[summary](e2-account-directed-primary-stderr-original.json) and
[secondary repeat ZIP](e2-account-directed-secondary-stderr-original.zip) /
[summary](e2-account-directed-secondary-stderr-original.json) remain unchanged.
The auditor verifies both streams, 84 source hashes per repeat, financial
reconciliation and the fatal-path evidence. Across all four originals there is
**one directed positive and three INCONCLUSIVE outcomes**. The experimental
workflow remains red where exit 2 was required; archive-audit PASS is separate.
Keep lifecycle/partition acceptance open. Capacity #25 can proceed independently.

## Original bytes and reproduction

- [Primary ZIP](e2-account-directed-primary-original.zip) / [byte-identical summary](e2-account-directed-primary-original.json): SHA-256 `d1543a98505cef134efab17dedc263678ba1fc2cb09c1343787f1f85233ea5ac`.
- [Secondary ZIP](e2-account-directed-secondary-original.zip) / [byte-identical summary](e2-account-directed-secondary-original.json): SHA-256 `e018ad1f5d738ba3c1f21e119dd08b63dd60dc47f5dc29c95899b9423f61e5e5`.

The [offline auditor](../../scripts/check_e2_account_directed.py) checks both ZIP
digests, summary identity, all 84 original source hashes, stdout logs/intervals,
actual witness/process IDs, packet bytes, SQL/ACK reconciliation and sampled
recovery. Its PASS means those archived observations verify, **not** that both
directed targets pass or that missing stderr was recovered. Natural lifecycle
semantics, capacity #25, unassisted recovery and physical HA remain separate.

[Español](E2-ACCOUNT-DIRECTED.es.md) · [Preregistered protocol](../../lab/e2_account_directed/README.md)
