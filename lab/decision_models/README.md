# Bounded decision models for COBOL migration

A Python standard-library-only toolkit for explicit decision tables, sequential process observations, ADR traceability and baseline byte verification. All new artifacts live here; protected oracle snapshots and `lab/todm_validation` are unchanged. Repository authorship and editorial authority remain with José María Flores Zazo. No installation, network, Azure operation or workflow service is needed. Tested with Python 3.13; implementation requires Python 3.10+.

**The source of acceptance truth is an accountable, scoped, approved baseline. A diagram, model, ADR, legacy executable, hash or `approved` flag is not sufficient.** The examples are synthetic and unapproved. This tool always reports `productionApproved: false`, even for business `APPROVE`, a PASS trace or an approval claim set to true.

## Run from the repository root

```powershell
python -m unittest lab.decision_models.test_toolkit -v
python lab\decision_models\toolkit.py validate lab\decision_models\examples\fee-decision.json
python lab\decision_models\toolkit.py validate lab\decision_models\examples\fee-process.json
python lab\decision_models\toolkit.py evaluate lab\decision_models\examples\fee-decision.json --input lab\decision_models\examples\fee-input.json
python lab\decision_models\toolkit.py check-trace lab\decision_models\examples\fee-process.json --input lab\decision_models\examples\fee-trace.json
python lab\decision_models\toolkit.py check-baseline lab\decision_models\examples\baseline.json --root lab\decision_models
python lab\decision_models\toolkit.py export lab\decision_models\examples\fee-decision.json
```

All commands above should exit 0. The half-cent input yields `feeCents: 1`, `resultCode: APPROVE`, `status: PASS`, **not** production approval. `export` writes deterministic, sorted/indented JSON for this local profile, **not OMG XML** and not a validation report. Its bytes are reproducible; this is not RFC 8785 canonicalization. An exported model must still be approved/bound separately.

Negative and incomplete examples deliberately use nonzero exit codes:

```powershell
python lab\decision_models\toolkit.py evaluate lab\decision_models\examples\fee-decision.json --input lab\decision_models\examples\fee-input-incomplete.json
python lab\decision_models\toolkit.py check-trace lab\decision_models\examples\fee-process.json --input lab\decision_models\examples\fee-trace-incomplete.json
python lab\decision_models\toolkit.py check-trace lab\decision_models\examples\fee-process.json --input lab\decision_models\examples\fee-trace-invalid.json
```

The first two exit **2 / INCONCLUSIVE**; the last exits **1 / FAIL**. Run these individually, not behind `&&` expecting all-zero success. Missing observations differ from contradictory observations. Malformed JSON, unsupported constructs, schema errors, invalid transitions and hash mismatches fail (exit 1). Missing baseline artifacts are inconclusive (exit 2). Profile-valid data/evaluation/trace/byte agreement pass only their named bounded check (exit 0). CLI usage errors are argparse exit 2, not evaluation reports.

`--output <new-file>` exclusively creates a report or export; existing files are never overwritten. Without it, output is JSON on stdout. Artifact paths in models/manifests are relative to the explicit baseline `--root` (default current directory), not the manifest location. JSON links use portable slash-separated paths; CLI examples use Windows separators. Traversal, absolute/device/stream paths and links are rejected. The local `.gitattributes` preserves LF bytes across checkouts for hash stability. No sealing command auto-refreshes hashes: create a new reviewed inventory instead of concealing mismatches.

## Implemented profiles, not standards conformance

These schemas and semantics are **local version-1 profiles inspired by DMN/BPMN**, not DMN/FEEL interpreters, BPMN execution engines, OMG interchange schemas or certified TODM implementations. Unknown fields are rejected rather than ignored. `validate` checks structure, references and process graph reachability; it does **not** establish all-input decision coverage, disjointness, correctness, authority, or source/ADR file existence. Use `check-baseline` for actual linked bytes.

### Common model fields

Required: `profileVersion: 1`, `kind`, `id`, `version`, `baselineId`, nonempty `sources` and `adrs`. Each link is exactly `{id, path}`. IDs/versions use `[A-Za-z][A-Za-z0-9_.-]{0,79}` (for example `v1`). Models, sources and ADRs have stable IDs; a model change requires review and explicit versioning, not implicit “latest”. See [fee decision](examples/fee-decision.json) and [fee process](examples/fee-process.json) for complete editable input fixtures. Validators are executable schema definitions in [toolkit.py](toolkit.py).

### Decision-table profile

- `kind: decisionTable`; `hitPolicy: UNIQUE` or `FIRST`.
- `inputs` and `outputs` are nonempty maps of names to `{type, enum?}`. Types: `integer`, `decimal`, `string`, `boolean`. Optional enum restricts values; numeric comparison uses exact values. Integers are JSON integers (not booleans) with absolute value below 10^18. Decimal inputs/constants/divisors are plain strings with up to 18 integer and 8 fractional digits; floats, exponent notation, leading plus signs, nonfinite values and implicit conversions are rejected.
- `rules` is a nonempty ordered list of `{id, when, then}`. `when` is a conjunction of `{variable, operator, value}`. Empty `when` means true. Operators: `eq`, `ne`, and numeric-only `lt`, `le`, `gt`, `ge`. OR is represented by separate rules, not expressions or scripts. No `eval`, imports or execution from model data.
- `then` supplies every output exactly once, either `{constant: value}` or the sole arithmetic operation `{operation: multiplyDivide, variables: [a,b], divisor: "10000", scale: 0, rounding: HALF_UP}`. Exactly two declared numeric inputs are multiplied and divided by a nonzero decimal-string constant. Rational arithmetic avoids binary floating point and ambient decimal precision; rounding happens once at the output boundary. Scale is 0..8; integer outputs require zero. HALF_UP ties round away from zero, HALF_EVEN ties round to an even final digit, DOWN truncates toward zero. Output bounds/enums are checked too.
- UNIQUE rejects two or more matching rules **on the evaluated input**. FIRST reports all matches but selects the first. No match or missing input gives INCONCLUSIVE. Static validation does not solve overlap/coverage. The fee example uses FIRST to preserve invalid-input priority before inactivity; the final default rule intentionally overlaps earlier rules.

### Process-trace profile

- `kind: processTrace`, unique string `states`, one `start`, nonempty unique `ends`, and unique `[from, to]` `transitions`.
- Every state must be reachable from start and able to reach an end. Start has no incoming transitions; ends are terminal. Sequential loops are allowed if an exit is possible.
- A trace is exactly `{modelId, modelVersion, states: [...]}`. Empty trace/missing terminal observation is INCONCLUSIVE. Unknown states, wrong start/version, forbidden transitions, or events after an end fail.
- Only a single observed state sequence is checked. There are no BPMN gateways, tokens, concurrency, conditions, tasks, timers, compensation, event correlation or side effects. The example does not execute a decision or verify that its result selects the correct process branch. Map real observations explicitly; do not manufacture a passing trace from the model.

Lists are bounded (generally 1..1000; predicates <=100; trace <=10000). This is small offline tooling, not a hardened untrusted-file service or arbitrary workflow engine.

## ADR and baseline traceability

- [ADR template](adr/TEMPLATE.md): decision rationale, alternatives, accountable owner, source/model versions, independent checks and change control.
- [ADR-001](adr/ADR-001-bounded-profiles.md): actual proposed selection, reasons for FIRST, alternatives and limitations.
- [Contract](examples/fee-contract.md): public fee behavior interpreted at a parsed-input boundary, not a COBOL record parser.
- [Independent cases](examples/fee-cases.json): manually curated arithmetic and domain cases, not generated by the evaluator or copied from protected expectations. Tests compare the executable model to these fixed expectations and verify three deliberately wrong variants (rounding, threshold, inactivity) disagree.
- [Baseline manifest](examples/baseline.json): explicit SHA256 inventory of source, ADR, models and cases. It binds the case bytes but does not itself execute cases; unit tests do that. Model ID/kind/baselineId and source/ADR IDs, paths and roles are cross-checked. The manifest's own version and each model version remain distinct. It is not signed or independently authenticated. Even `approvalClaim.approved: true` cannot establish truth, independence, mandate or approval; `authorityStatus` remains INCONCLUSIVE. A rehashed malicious bundle can pass byte checks.

To adapt: write a reviewed capability contract, independent expected cases, decision/process models and ADR; enumerate exact SHA256 bytes and links in a new baseline; run tests and all CLI checks. For a file digest use `Get-FileHash -Algorithm SHA256 <file>` and record lowercase hex. Freeze and approve the baseline through external accountable governance before acceptance; preserve prior versions and protected oracle snapshots. Do not treat an unassigned owner or documentary status as approval.

## TODM gate versus golden master

Use these results as **additional bounded observations**, not replacements for the [pinned TODM adapter](../todm_validation/README.md). This tool does not emit that adapter's evidence-bundle schema and does not silently integrate with it. A separately reviewed integration must preserve original raw outputs, exact commands, environment, CI/run identity if any, source/model/case hashes, limitations and independent oracle provenance. Establish artifact authentication, actor/mandate/scope/approval checks and fail-closed release policy separately. Do not turn this tool's exit zero into a TODM release or E1-E4 completion claim.

Golden-master comparison answers whether a candidate repeats observed legacy outputs, including possible defects. Model/case comparison answers whether the candidate meets the **approved normative baseline** within tested scope. Execute candidate and legacy adapters independently, retain their raw observations, compare each to independently approved expected cases, and investigate disagreements rather than “fixing” the oracle to match either. This toolkit executes neither a candidate nor COBOL; adapter/parser and full equivalence qualification remain separate work.

## Other modeling approaches: documentation mappings only

| Approach | Useful mapping | Execution here |
|---|---|---|
| SBVR | Reviewed vocabulary, business facts and rule IDs in the contract/ADR | Not implemented; no natural-language rule parsing |
| CMMN | Discretionary case tasks, evidence/approval responsibilities | Not implemented; do not flatten discretionary tasks into claimed workflow semantics |
| OCL | Explicit invariants and pre/postconditions linked to independent assertions | Not implemented; no OCL expression evaluation |
| DMN | Visible table rules, hit policy, typed operands and output rounding | Only the local JSON profile above |
| BPMN | Named sequential obligations and observed transitions | Only the local single-sequence checker above |

## Retained local example outputs

`examples/result-*.json` are small **executed local synthetic demonstration outputs**, not approved expected fixtures, a live business experiment, Azure/mainframe evidence or an E1-E4 run. Their exact generation commands and interpreter are recorded in [demo-run.json](examples/demo-run.json). Independently specified expectations remain solely in `fee-cases.json`. No CI run ID, external approval or trusted execution provenance is invented. Reports contain model IDs/versions but are not self-authenticating evidence; bind raw reports and the actual tool/source revision separately in any real campaign.
