# ATM late advice and cash uncertainty — original synthetic 33-case run

[Español](CHANNEL-ADVICE.es.md) · [PR #98](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/98) · [Original Actions #42024266243](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42024266243) · [EN protocol](../../docs/research/channel-late-advice.en.md).

**5 November 2026. Classification: PASS_33_SYNTHETIC_ADVICE_CHECKS, NOT physical ATM, card-network or bank acceptance.**

## Exact original execution

The original GitHub Actions job `127234409728` ran **33 of 33 Python positive and adversarial tests with zero unexpected errors** on source and checkout SHA `291829f8cda34604f692a03dff6794f6cec0f51c`. The checks cover repeated identical messages; reused STAN-like numbers across terminals; conflicting retransmission under one message ID; mismatched authorization, terminal, RRN-like reference, source epoch, and authorized amount; absent, zero and partial physical results; duplicated/posting-for-unknown financial effects; stale reversal after partial dispense; and false stand-in delegation claims.

Original fixture decisions were:
- `CASH-001: MATCHED_PARTIAL_CASH` (10,000 requested, 6,000 fictional device proof and posting).
- `CASH-002: UNKNOWN_REQUIRES_DEVICE_EVIDENCE` (8,000 requested, no final physical result and no posting, despite an advice).
- `CASH-003: FINAL_ZERO_CASH` (5,000 requested, device final zero, a reversal **request**, not an executed reversal).
- `CASH-004: STAND_IN_DENIED` (issuer delegation missing; no alternate authorization).

[Selected unchanged 33 original log lines](CHANNEL-ADVICE-PR98-ORIGINAL-CI-EXCERPT.log) preserve original timestamps. [Machine-readable original result and provenance](channel-advice-pr98-original-ci-summary.json) preserves the exact SHA and explicit limitations.

The original Actions artifact `channels-advice-synthetic-original-not-iso8583-or-cash`, ID `13412439030`, was reported by GitHub at **2371 bytes** with SHA-256 `4cc2ea7009d514e462cab8a173bc6fae2c5c36804ef7af49c79e9441151d0950`. **The ZIP was not independently downloaded or rehashed** in this record; this digest is GitHub-published metadata only, not an independent audit of its bytes.

## Invariants and limits

All results, including a synthetic PASS, say `safeToAutoDispense=false`, `safeToAutoPost=false`, `safeToAutoReverse=false`, `productionApproved=false`, `realCardNetworkTested=false`, `physicalDeviceJournalAuthenticated=false`, `standInDelegationApproved=false`. The module **does not** commit or authorize financial changes. A wholly invented but coherent authorization/device/posting/late-message set could PASS.

This is distinct from the existing [native two-store channel experiment](../../docs/CHANNELS_CHECKPOINT_2026-11-03.md), which tests actual .NET 10 HTTP, two PostgreSQL servers and process kills **under a separate synthetic cash-device assumption**. A green repeat of that experiment cannot establish real bank ATM/cash transfer proof, certified ISO 8583/NDC/DDC, current card scheme contract, switch policy, PCI PIN/HSM, physically independent HA or owner-approved partial/reversal/stand-in rules.

For banking acceptance, obtain bank-authorized original switch messages, issuer state and posting oracle, physical device dispense/retract journals and outcome protocol, conflict/late-delivery retention and approved stand-in delegation; test a physical network/device under real fault injection with an independently reviewed policy. **#30 remains OPEN** with the wider L01–L16 and channel checklist. No new release. TODM **G2 INCONCLUSIVE / G6 BLOCK**, E2 remains `partially_verified`.
