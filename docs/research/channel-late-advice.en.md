# Late ATM advice: why network replies cannot settle physical cash

**Issue #30 · 5 November 2026 · research and falsifiable synthetic lab only.** [Español](channel-late-advice.es.md) · [Existing native two-store channels checkpoint](../CHANNELS_CHECKPOINT_2026-11-03.md) · [Forensic source](../../lab/channels/advice_gate.py).

## Four distinct authorities and five distinct identifiers

The **ATM/dispenser** observes physical notes and may maintain its own electronic journal; the **ATM switch/network** transports authorization/advice/reversal records; an **issuer-authoritative core** owns holds, posted accounting entries and operation status; a **scheme/processor** has distinct authorization, clearing/settlement and dispute obligations. Their records can arrive late, out of order or in duplicate. An authorization is neither a delivery proof nor an accounting settlement.

The fictional lab deliberately keeps **operationId**, **authorizationId**, **terminalId**, **networkTrace** (illustrative STAN-like field) and **retrievalReference** (illustrative RRN-like field) distinct. A short network trace number can be reused between terminals or times: it is **not a globally unique durable financial key**. The correlation boundary must preserve the original operation, issuer epoch, routing context and real provider profile; a synthetic JSON structure is not a certified ISO 8583, NDC/DDC or card-brand implementation.

A [Visa public dispute guideline (2024)](https://www.visa.mn/content/dam/VCOM/global/support-legal/documents/merchants-dispute-management-guidelines.pdf) describes nonreceipt or partial receipt of ATM cash and asks for a cash-disbursement record and/or credit/reversal evidence. This supports the requirement to reconcile device data, not automatic acceptance of a network message as definitive physical proof. [NCR's 2021 security advisory](https://assets-global.website-files.com/64a2be73942e1d57fed077f3/65296c8ffb7b891a9f5d48d5_NCR_Security_Advisory_2021_02_TRF_Rev_1.0.pdf) also illustrates the risk of host reversal policy when cash is actually accessible to a cardholder. These documents **do not specify or approve this fictional bank's accounting policy**.

## Adversarial scenario contract

| Source authorization / device / message | Adjudication | Forbidden inference |
| --- | --- | --- |
| CORE approved 10,000 minor units; device proves 6,000; financial posting is 6,000; duplicate identical advice | `MATCHED_PARTIAL_CASH` | No second dispense or posting for the repeated network message |
| CORE approved 8,000; physical device command status `UNKNOWN`; advice arrives saying 8,000 | `UNKNOWN_REQUIRES_DEVICE_EVIDENCE` | Do not treat advice as proof of cash or auto-post zero/full value |
| CORE approved 5,000; final device journal says zero; a reversal request arrives | `FINAL_ZERO_CASH` | Reversal **request** is not a ledger reversal COMMIT |
| Core unavailable; a hypothetical switch requests stand-in but **no issuer delegation exists** | `STAND_IN_DENIED` | No automatic offline authorization, debit or physical dispense |

A **full reversal request after partially dispensed cash** is a mandatory review/block condition. A contradictory advice amount, reused network message ID with a changed payload, duplicate ledger posting, wrong terminal/authorization/RRN context, missing device journal, stale source identity or unauthorized stand-in approval must also fail closed. Actual policy for partial cash and chargebacks depends on the issuer, scheme, network and hardware.

Public [Mastercard transaction-processing rules (2025 edition)](https://www.mastercard.us/content/dam/public/mastercardcom/na/global-site/documents/transaction-processing-rules.pdf) describe timeouts and issuer-designated stand-in routing in specified contexts; [CSFi's product documentation](https://www.csfi.com/ezswitch-2/) describes a candidate stand-in design using card limits and positive-balance files. Neither proves that **any** real bank delegated stand-in for cash. The fixture intentionally **denies** such delegation, even if its JSON is edited to claim approval.

## What the tests prove — and do not

The [English-only test suite](../../lab/channels/test_advice_gate.py) has **33/33 original CI-executed positive and negative cases** ([original EN audit](../../evidence/runs/CHANNEL-ADVICE.md) · [ES](../../evidence/runs/CHANNEL-ADVICE.es.md) · [run #42024266243](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42024266243)). It checks malformed or duplicated identities, mismatched journal and posting amounts, replay/contradictory messages, journal unknown-versus-zero, reversal requiring investigation and rejected stand-in self-approval. The tool never connects to real bank equipment or network, writes no financial record, has no trusted signing roots and does not verify the original source bytes. **A coherent fictional fixture can PASS.** Even on PASS all flags remain `safeToAutoPost=false`, `safeToAutoReverse=false`, `safeToAutoDispense=false`, `productionApproved=false`, **TODM G2 INCONCLUSIVE / G6 BLOCK**.

This is deliberately **additive** to the already verified .NET 10 + PostgreSQL + Podman two-store channel lab and its seven independent financial oracle groups. It does not replace those original SQL/device experiments or change their archived failures. A real acceptance campaign requires the issuer-approved rulebook, signed or owner-attested original device journal and physical notes/retract events, actual switch message fields and STAN/RRN reuse semantics, authenticated issuer/processor events, end-to-end replay and recovery, physical network partitions, external disputes, trace identity and protected PCI/HSM boundaries. Use **masked/fictional** data in the public lab. No new release or bank cutover is authorized.
