# Greenfield capabilities: transfer and booked balance (.NET 10)

**Purpose:** program a new system from business behavior, not convert COBOL. No parser.

This is an intentionally **synthetic sequential in-memory prototype**. It proves neither durability/SQL COMMIT nor bank-grade authentication, isolation, availability, real account rules or production load. The scenario is a research hypothesis, not an approved banking specification.

## Run with .NET 10 and Python 3

From `lab/` after `dotnet restore greenfield/Greenfield.csproj`:

```bash
python3 -m unittest discover -s greenfield -p 'test_*.py' -v
python3 greenfield/run_contract.py
```

The first command runs the Python negative controls for the independent reference oracle; the second invokes the **new .NET 10 implementation** and rejects any divergence from the golden outcomes. All code, comments, Gherkin and READMEs are English only.

## What the fixture distinguishes

`APPLIED`, `DUPLICATE_APPLIED`, `ID_CONFLICT`, `REJECTED_INSUFFICIENT`, `REJECTED_UNAUTHORIZED`, `UNKNOWN_AFTER_APPLY`, `STALE_PROJECTION`, and `BOOKED`/`PROJECTED_BALANCE`. The ambiguous-response step simulates a lost **in-memory** acknowledgment, not loss of a committed SQL response.

A candidate fails if it duplicates postings, breaks conservation, omits outbox, lies about the projection watermark or treats an unapproved request as applied. Read the [intent](intent.md), [specification](spec.md) and [Gherkin scenarios](acceptance.feature).

## Release and evidence

This lab is independent of the historical E1/E2 financial baseline. The 12-step synthetic contract provides no real mainframe comparison. Do not market it as CAP-005 or CAP-007 accepted at a bank. Record exact PR SHA, original CI logs and both positive and deliberately failing negative controls. Published `v2026.10.29` must remain untouched.

## TODM and Golden Master are intentionally different

- **Golden Master / Characterization Testing** observes what the incumbent *actually does*; it is not the source of approved business truth. The included `contracts/golden_master_synthetic.json` is a **fabricated demonstration** with one matching observation and one deliberately contradictory stale-projection response, NOT captured COBOL output.
- **TODM** [research v1.5](https://github.com/jmfloreszazo/TODM) governs G0 scope, G1 discovery, G2 baseline approval, G3 oracle qualification, G4 bounded construction, G5 independent verification, G6 release authorization and G7 controlled evolution. The local `todm_assurance.py` is an explicitly **TODM-inspired stage mapping**, NOT the official TODM demo/cryptographic attestation engine.
- In this synthetic case, **G5 may PASS while G6 must BLOCK**: business owner, signed G2 baseline, approved mandate and independent release signoff are absent. An observed Golden Master discrepancy does not silently rewrite the expected behavior.
- Tests deliberately corrupt the Golden Master, expected provenance and candidate outputs. A local SHA-256 only fingerprints evidence and **is not a digital signature or an approval**.
- A real modernization environment may use a [client/provider confidential-computing study](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/53), but a TEE alone never certifies TODM approval or suppresses sensitive outputs.

The original synthetic `GREENFIELD CONTRACT: PASS` remains a **technical comparison only**. The new `TODM_ASSURANCE: G5=PASS G6=BLOCK` status is the *expected* safe result, not a contradiction.

## Editorial architecture cross-reference

The paired [Spanish Chapter 7](../../book/es/parte-2-arqueologia-y-autoridad/07-legacy-archaeology-asistida-por-agentes.md) and [English Chapter 7](../../book/en/part-2-archaeology-and-authority/07-legacy-archaeology-assisted-by-agents.md) now visualize functional discovery first, a separate Golden Master observation lane, optional source archaeology, independent TODM oracles, and G6 human authorization. The paired C4 container figures in Chapter 11 explain the same boundary. A diagram is an architectural hypothesis, **not security isolation, an approved business baseline, or permission to release a banking system**.
