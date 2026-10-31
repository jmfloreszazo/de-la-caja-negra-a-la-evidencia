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
