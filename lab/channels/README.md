# Synthetic channels and cash reconciliation

This bounded teaching fixture has a native .NET 10 HTTP core and **two separate PostgreSQL 16.13 containers on one host**. One database owns balances/holds/postings/outbox; the other owns the simulated dispenser journal and stock. Read [the preregistered contract](CONTRACT.md) before interpreting results. The first native acceptance campaign passed ten cases and two mutation controls. The original startup failures and exact source/run identities are retained in the [evidence checkpoint](../../docs/CHANNELS_CHECKPOINT_2026-11-03.md).

## Run

Requirements: Linux, Podman, .NET 10 SDK, Python 3.12 and dependencies from `lab/e1_pg/requirements.txt`. From the repository root, run `python3 lab/channels/run.py`. The driver creates its own containers, refuses port conflicts, records image identity, publishes the native host and removes only containers whose IDs it created. Fixed loopback SQL ports are 55442/55443; HTTP chooses a free port from 55444–55463 and records it. The driver never terminates an unrelated listener. Never run this fixture against existing databases. `CHANNELS_DISPOSABLE=YES` and an exact fixture identity protect individual adapters; the driver explicitly enables its disposable environment.

The original report and raw logs are written under `lab/results/channels/`, including failures. The report retains offered intents, HTTP observations, both SQL snapshots, compiler output, SDK/container versions, seven independent oracle groups and deliberate negative controls. CI uploads `channels-synthetic-original` even when the campaign fails. A post-COMMIT HTTP abort is exercised over an actual socket. External SIGKILL tests separately interrupt the device response after its commit and the core before its financial commit. The device outcome must survive the latter because the stores are separate.

## Offline advice/reversal forensic oracle (separate from native SQL fixture)

**Original bounded synthetic gate: 33/33 PASS** in [Actions #42024266243](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42024266243), [EN original-run audit](../../evidence/runs/CHANNEL-ADVICE.md) / [ES](../../evidence/runs/CHANNEL-ADVICE.es.md). The GitHub-reported artifact checksum is preserved in the audit; its ZIP has **not been independently downloaded and rehashed**. These are pure-Python fictional scenarios, not a bank protocol test.

The [paired EN](../../docs/research/channel-late-advice.en.md) / [ES](../../docs/research/channel-late-advice.es.md) research adds an **offline fictional** network-advice correlation experiment. It does not emulate ISO 8583, NDC/DDC, a real ATM, physical hardware journal or a bank-approved stand-in service. The original .NET 10/two-PostgreSQL native campaign and archived observations are unchanged.

```bash
python3 lab/channels/advice_gate.py lab/channels/advice_fixture.json
python3 -m unittest discover -s lab/channels -p 'test_advice_gate.py' -v
```

The baseline has four operations: partial final cash (posted amount only), cash UNKNOWN (no posting), final zero cash, and **denied stand-in because issuer delegation does not exist**. It includes an identical repeated advice and an advice with a reused short STAN-like value across terminals. Adversarial cases reject a changed payload under the same message ID, wrong RRN/terminal/authorization, mismatched cash and ledger, duplicate posting, reversal against partially dispensed notes, and self-asserted stand-in approval.

CLI exit 0 = `PASS_SYNTHETIC_CORRELATION_ONLY` (consistency of fictional observations); 2 = `REJECT`; 3 = `INVALID`. **Every** result says `safeToAutoPost=false`, `safeToAutoReverse=false`, `safeToAutoDispense=false`, `productionApproved=false`, and TODM G2 INCONCLUSIVE/G6 BLOCK. Do not use this forensic checker to drive any financial state transition. A complete fake but internally consistent trace could pass. The device and core real source evidence is not authenticated.

## Offline per-hop transport failure trace oracle (not physical network injection)

**Original CI: 40/40 PASS** over seven fictional scenarios in [Actions #42028436325](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42028436325). [Original EN audit](../../evidence/runs/CHANNEL-HOP-FAULTS.md) · [ES audit](../../evidence/runs/CHANNEL-HOP-FAULTS.es.md). The archived SHA-256 is GitHub-reported metadata, **not independently checked ZIP bytes**; the result is logical-trace consistency only, not an actual TCP partition or a bank approval.


The separate [EN study](../../docs/research/channel-hop-failures.en.md) / [ES](../../docs/research/channel-hop-failures.es.md) maps **seven fictional ATM/switch/core/writer-epoch cases** and **40 positive/adversarial Python tests**. The fixture contains declared events for logical `ATM_SWITCH`, `SWITCH_CORE`, `ISSUER`, `DEVICE` and `CONTROL`; it compares them with a separately declared *fictional* issuer decision, device journal state, posted amount and active writer epoch.

```bash
python3 lab/channels/network_fault_gate.py lab/channels/network_fault_fixture.json
python3 -m unittest discover -s lab/channels -p 'test_network_fault_gate.py' -v
```

Exit 0 = `PASS_SYNTHETIC_HOP_CONSISTENCY` (fictional event/snapshot agreement); 2 = `REJECT`, 3 = `INVALID`. This module **does not open or cut a TCP connection**, observe mainframe UOW, interact with physical cash, implement ISO 8583 or authorize a source writer cutover. Its source epoch is a *correlation label*, not a bank-owned fence. It never authorizes cash, posting, reversal, duplicate retry, offline stand-in or deployment. All outputs keep G2 INCONCLUSIVE, G6 BLOCK.

This is additive to the existing ten native .NET 10/SQL/device-emulator cases and the 33 earlier fictional advice/reversal controls. None of those previous observations has been overwritten. Future real per-hop packet loss/failure injection needs authentic independent issuer/device evidence and customer-approved rulebooks.

## Scope

Amounts are integer cents and policies are invented for this example. The device atomically records simulated stock and journal in its own SQL transaction: **this is an emulator assumption, not proof of atomic physical cash delivery**. A partial dispense posts its actual amount; absent evidence retains UNKNOWN and the hold. Idempotent reconciliation uses the original command ID. No approved offline authorization exists; a caller must not invoke the device without core authorization and preparation.

The Python oracle reads SQL snapshots without invoking the C# decision logic. It checks account projection, conservation, offered intent, paired postings, financial outbox, holds/availability and device reconciliation. Mutation controls change copies of observations, leaving original snapshots intact. This is functionality and fault-injection evidence, not a capacity, bank-policy, mainframe, security, ISO 8583, NDC/DDC, PCI/EMV, HSM or physical-HA claim.

For a realistic follow-up, obtain issuer-approved authorization/partial-cash/expiry/reversal/stand-in rules, authenticated device journals with physical delivery and retract/reject evidence, certified transport/protocol endpoints, actual account ownership/fencing and a migration cohort. Preregister expected outcomes, recovery operator actions and reconciliation deadlines. Replay on dedicated external equipment and retain raw device/network/core evidence. Those external activities are non-blocking residuals of issue #30; this fixture cannot supply their evidence.
