# Brownfield CAP-007 / CAP-005 implementation gap

**This directory does not implement a new banking system.** It establishes what has already been shown in controlled synthetic PostgreSQL experiments and, more importantly, what has **not** been demonstrated for a brownfield replacement of real mainframe capabilities.

## Existing engineering assets

- [E1 PostgreSQL .NET implementation](../e1_pg/PgBank/Program.cs): a transactionally durable synthetic transfer using Npgsql with operation ID, balanced postings and outbox. Its documented fault hooks distinguish crash before COMMIT from lost reply after COMMIT; the existing E1 tests are the source for any actual tested claim.
- [E1 PostgreSQL schema](../e1_pg/schema.sql): synthetic ledger authority, not a customer account schema.
- [CAP-007 / CAP-005 prototype specification](../greenfield/spec.md): historical path; intentionally sequential and **in-memory**.
- [TODM-inspired assurance](../greenfield/todm_assurance.py): a bounded G0–G7 stage mapping, not the full TODM engine; its G6 stays BLOCK without independent business approval.
- [Gap matrix](capability_gap.json): twelve explicitly scoped technical/functional gaps, including real SQL commit evidence **but missing** customer authorization, compatibility, durable balance/projection freshness, cutover, rollback and business release approval.

The name `lab/greenfield` is retained temporarily for repository compatibility. **The migration context is brownfield.** Writing replacement code from scratch does not change the ownership of incumbent business rules, interfaces, data, audit and transition risks.

## Run

```bash
python3 -m unittest discover -s lab/brownfield -p 'test_*.py' -v
python3 lab/brownfield/gap_gate.py lab/brownfield/capability_gap.json
```

The evaluator reports **zero business-approved requirements**, `productionEquivalent=false` and `todmG6=BLOCK`. It validates catalog structure, source lineage and protected negative assumptions only. Referencing a source file does not prove the stated technical behavior and a synthetic E1 PASS does not authorize migration of a real bank.

## Next concrete deliverable

Implement a customer-independent **synthetic brownfield coexistence** contract and a PostgreSQL-backed CAP-007/005 replacement, reusing the proven E1 transaction ideas instead of translating COBOL or changing archived baselines. Define an ACL/gateway that can select the legacy simulation or new candidate **with exactly one financial writer**. Run fault injection before/after SQL COMMIT, retained operation ID, independent persisted-ledger oracle, stale balance watermark tests and controlled cutover/rollback.

For productization the team must obtain approved policy and actual business owner mandates. No dataset containing real financial information may be committed to the public repository. E2 Orleans and E3 cloud scale remain separate, benchmark-controlled decisions.

See [issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).
