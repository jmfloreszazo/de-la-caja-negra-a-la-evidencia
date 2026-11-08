# Pinned TODM evidence validation

This standard-library-only adapter applies the actual [TODM methodology](https://github.com/jmfloreszazo/TODM/tree/61354abc03e73fbf258b6e8d66e35678da134ef8), version 1.5.0, to explicitly bounded E1–E4 evidence. José María Flores Zazo retains authorship and release authority. This is a **local implementation of a pinned public methodology, not a certified TODM engine, generic OMG interpreter, identity provider, or production authorization service**.

## What is executed

- `validate.py` verifies exact artifact bytes and evaluates supported independent observations, not just a top-level `PASS` string.
- E1 reads all seven independent ledger invariants, control verdicts, and before/corrupted/restored oracle qualification vectors.
- E2 supports `E2-Orleans-Actual-Cohost-Process-Kill`: four distinct route/fault combinations, actual SIGKILL exit codes, durable counts, independent invariants, and negative split qualification. Other E2 shapes fail closed.
- E3 supports the explicit `EXPLORATORY_SYNTHETIC_NOT_E3_CAPACITY_ACCEPTANCE` report. It independently reconstructs all seven ledger invariants from the actual account/operation/posting/outbox snapshot, additionally checks request-to-posting correspondence and fixture structure, reconciles every actual offer against the preregistered offer and durable record, verifies counters and raw acknowledgment payloads, and checks the SIGKILL/restart/recovery timeline. It genuinely removes a posting from a copy of that snapshot to qualify its checker. Before/after invariants, surviving service, errors and restored negative-control evidence are also required. This **does not** accept capacity, p99, banking SLA, or physical HA. Missing or unknown shapes remain inconclusive.
- E4 independently recomputes every candidate and legacy observation against bound frozen cases. Qualification also recomputes the reference and three actual mutant observation files; their report status alone is insufficient. It does not execute generated code.
- `governance.py` executes **the actual upstream** `parse_time`, `authority_verdict`, and `release_verdict` function bodies from `demo/scripts/governance.py`. AST selection excludes upstream imports and its unrelated demo runner; function bodies are unchanged. `vendor/provenance.json` records the upstream revision, paths, and exact SHA256. The complete unmodified source and MIT license are retained under `vendor/`.

The upstream [README gate definition](https://github.com/jmfloreszazo/TODM/blob/61354abc03e73fbf258b6e8d66e35678da134ef8/README.md) and [two-plane governance implementation](https://github.com/jmfloreszazo/TODM/blob/61354abc03e73fbf258b6e8d66e35678da134ef8/demo/scripts/governance.py) are the semantic references. The artifact bundle schema below is this repository's adapter interface, **not an upstream TODM standard**.

## Run offline from the repository root

```powershell
python -m unittest lab.todm_validation.test_validate -v
python lab\todm_validation\validate.py --manifest lab\todm_validation\examples\historical-bundle.json
python lab\todm_validation\validate.py --synthetic-governance
```

`examples/historical-bundle.json` binds retained real E1/E2 reports from `azure-live-20261107` and the E4 evaluation replay and qualification from `e4-live-20261108`. `examples/historical-replay.json` records the executed adapter result: the three **bounded evaluations PASS; every release is BLOCK and methodology completion is INCONCLUSIVE**. Missing retained files on another checkout will fail closed; they are not downloaded or recreated. E1/E2 are retained SQL-oracle observations, not a fresh database verification. E4 is a fresh offline comparison of retained raw outputs, not another model run. Historical provenance and limitations remain present; no CI run ID is invented.

`examples/synthetic-governance.json` contains a separate executed 12-case upstream demonstration: missing principal, unknown principal, missing time, expired time, wrong action/scope, absent/revoked mandate, missing approval, failed/inconclusive oracle, and synthetic allow. Its `SIMULATED_ALLOW` is never applied to experiment releases.

CLI exit codes are **0 = bounded evaluation PASS, 1 = FAIL, 2 = INCONCLUSIVE or invalid input**. Exit zero never means release authorization. `--output` writes a new file exclusively and refuses overwrites. Without it the report goes to stdout. `--root` is an explicit artifact root (default: current working directory), not the manifest's directory. No network, database, Azure, model, or deployment operations occur.

## Actual-bundle qualification output directory

`qualify_bundle.py --root <bundle> --output <directory>` requires a **new directory strictly inside the bundle root**. Relative output paths resolve against the current working directory, so change into the bundle root and use `--root . --output qualification-next`. The controls refer to their mutated copies through bundle-relative paths. External output directories are unsupported; the current CLI rejects them with exit code 2 and a clear JSON error before creating directories or writing files. Copy completed qualification output elsewhere afterward if needed.

Immutable snapshot 03 predates this preflight guard: its documented in-root command remains valid, but an external output path can fail after partial writes. Preserve any such failed-run evidence separately; do not modify snapshot 03 to retrofit this fix.

## Explicit bundle schema

Top-level required fields:

- `schemaVersion`: `1`
- `kind`: `TODM_EVIDENCE_BUNDLE`
- `upstreamCommit`: `61354abc03e73fbf258b6e8d66e35678da134ef8`
- `experiments`: nonempty list, unique `experiment` IDs

Each experiment contains `experiment`, `scope`, nonempty `risk`, nonempty `limitations`, optional original `provenance`, and `artifacts`. Supported scopes are fixed:

| Experiment | Scope |
|---|---|
| E1 | `postgres-concurrency-slice` |
| E2 | `single-cohost-process-kill` |
| E3 | `single-host-exploratory-recovery` |
| E4 | `frozen-case-builder-pilot` |

Each artifact is an object with a unique `id`, safe relative `path`, lowercase 64-digit `sha256`, and `role` (`source`, `contract`, `raw`, `report`, or `qualification`). Each experiment requires source, contract, raw and report roles. Optional `document` selects JSON adapters: `report`, `qualification`, `observations`, `cases`, `ledger`, `offers`, `planned`, or `qualification.none`, `qualification.round-even`, `qualification.wrong-threshold`, `qualification.approve-inactive`. E3 requires `report=summary.json`, `ledger=ledger-snapshot.json`, `offers=offers.json`, and `planned=offers-planned.json` from the same run. The report and qualification must have the documented experiment-specific shapes. See the complete historical manifest for an executable example.

Every source/protected/candidate/qualifier/legacy-input/artifact digest explicitly claimed by parsed reports must match supplied bound bytes. E3 additionally binds `source.fileSha256`, validates `source.sourceSetSha256`, and requires the reported host, binary and runtime artifacts. Supply snapshots from the original run when working-tree bytes changed. Do not substitute current files or rewrite old recorded hashes. Duplicate artifact IDs, paths, document names, JSON keys, absent files, changed bytes, symlinks/junctions, traversal, absolute/device/ADS paths and non-finite JSON values are rejected.

To seal a deliberately enumerated inventory, start with the same schema and omit only `sha256` values for new artifacts:

```powershell
python lab\todm_validation\bundle.py --spec lab\todm_validation\examples\my-inventory.json --output lab\todm_validation\examples\my-bundle.json
python lab\todm_validation\validate.py --manifest lab\todm_validation\examples\my-bundle.json --output lab\todm_validation\examples\my-replay.json
```

The sealer never discovers files or approves a baseline. It refuses to reseal any existing SHA256 that differs. Inventories and outputs must be explicitly chosen by the operator. Source content hashes identify bytes, not trusted authorship; a malicious party replacing both manifest and evidence can forge a coherent local bundle. There is deliberately **no approval import/verification interface** until an external trust root and authentication contract are designed.

## G0–G7 interpretation and authority boundary

| Gate | Local evidence evaluated | What is not inferred |
|---|---|---|
| G0 scope/risk | Exact adapter scope, explicit risk/limitations | Complete experiment protocol acceptance |
| G1 evidence discovery | Enumerated artifacts, hashes, source claims | Authentic producer or signed provenance |
| G2 baseline approval | Always INCONCLUSIVE | A digest is not an independent approval |
| G3 oracle qualification | Bound positive, negative, restored/mutant observations | Universal completeness or certification |
| G4 bounded construction | Source/construction evidence binding | New execution or permission to build/deploy |
| G5 independent verification | Supported independent vectors or frozen-case replay | Builder self-test success as authority |
| G6 release authorization | Always INCONCLUSIVE and BLOCK | Local approval, signature, role, or mandate strings |
| G7 drift/evolution | One-time byte integrity only; always INCONCLUSIVE | Continuous monitoring or evolution approval |

Negative verdict precedence is **FAIL > INCONCLUSIVE > PASS**. Reports separate `oracleVerdict`, `qualificationVerdict`, `evaluationVerdict`, `methodologyVerdict`, `authorityVerdict` and `releaseOutcome`. Thus detected corruption cannot disappear behind missing authority, and successful verification cannot create authority. Every experiment emits all eight gates even when blocked.

## Qualification and remaining gaps

Unit tests genuinely corrupt bytes, delete source files, omit oracle/qualification data, flip independent invariants despite `status: PASS`, inject wrong candidate outputs, duplicate IDs, mutate source bindings, forge local approval, and exercise invalid inputs and upstream mandate time/revocation semantics. Test scratch files are created and removed only inside this lab.

Historical E1/E2 raw counters were not reconstructed from database snapshots here. The actual E3 Azure run `e3-azure-20261108-01` was independently replayed from 720 offers and the ledger containing 668 durable commits: raw adapter verification and its mutation qualification both PASS. `examples/e3-raw-replay.json` records that bounded result and hashes; this is explicitly **not full bundle validation**, since campaign source/runtime bindings still need supplying. E3 is not included in the historical bundle: the current campaign must supply its actual summary and **all** recorded source/raw/runtime artifacts. No full E1–E4 population acceptance, production identity, signed baseline, business approval, release authorization, continuous drift monitor, cloud capacity, or mainframe equivalence is claimed. Local tests qualify this adapter only, not those missing controls.
