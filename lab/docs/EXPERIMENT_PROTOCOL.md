# Experiment protocol for the next tiers

The current lab demonstrates mechanisms. The sections below define the acceptance
protocol, not a blanket claim that every gate has been executed or passed.
See the [execution roadmap](../../docs/EXPERIMENT_ROADMAP.md) for separately
recorded runs and outstanding gates.

## E1 · Row-locking SQL engine

Port `Bank/` to PostgreSQL or SQL Server with a conditional debit, a uniqueness constraint on the operation identity, double-entry postings and an outbox row in one local transaction. Add what SQLite cannot show: two transfers locking accounts in opposite order (deadlock victim + bounded full retry with the same identity), serializable vs snapshot behaviour on a multi-row invariant, and a connection pool sized below the offered concurrency.

Acceptance: every control of `bank_test.py`, plus `deadlockVictimRetried`, `writeSkewPrevented` and `poolExhaustionBounded`, evaluated by a verifier that only reads persisted state.

## E2 · Actors as coordinators, ledger as source of truth

Implement the same contract with Orleans grains keyed by account. The grain serializes requests per account; the debit/credit still commits in one SQL transaction (or in Orleans transactional state, declared explicitly). Compare with E1 under three distributions: uniform, 5 % of traffic on hot accounts, and one account receiving 50 % of traffic.

Acceptance: identical functional verdicts to E1; report committed transfers/s, p99 per operation class, conflicts, retries, and the throughput ceiling of the hottest key.

## E3 · Azure vs on-premises with the same contract

Fill `performance-contract.json` from a real workload footprint (RMF/SMF, CICS monitoring, batch windows). Run the same generator (open loop, controlled arrival rate, latency from intended send time), dataset, durability policy and failure injections on: (a) an Azure configuration with a managed SQL engine and synchronous replica if the contract requires it, (b) an on-premises server with its second unit, and (c) a hybrid keeping the core on the mainframe.

Acceptance: a configuration passes only if it meets the contract *with one unit lost*, drains the backlog within the agreed time, and keeps every functional and accounting invariant. Report cost per million committed transfers.

Run the read-only readiness check before planning a capacity trial:

```bash
python3 lab/tools/check_capacity_readiness.py --output /path/to/new/readiness.json
```

Exit code **3** means `INCONCLUSIVE / BLOCK`, not a crashed measurement.
The [recorded preflight](../../evidence/runs/e3-readiness-2026-11-08.json)
found all 14 required capacity fields empty and status `UNCONFIGURED`.
The original contract is untouched. Even fully populated values produce only
`EXTERNAL_REVIEW_REQUIRED`, never capacity acceptance: this checker does not
authenticate approval, run load or replace external measurements.

The separately recorded [exploratory E3 harness](../e3_capacity/README.md)
executes open-loop offers and process failure on one Azure VM. It records
misses, failures, recovery and independent ledger reconciliation, but explicitly
does not satisfy the comparative acceptance contract above. Runtime binaries
must accompany their hashes, not merely appear in an inventory.

## E4 · Agents under the gate

Give an agent the public contract and write access only to `Candidate/`. Keep `contracts/` and `Gate/` outside its write scope (separate repository or protected path, verified by trying). Record model, prompt, tools, budget and every attempt. Compare: tests written by the agent, independent oracle, independent oracle + mutation qualification.

Acceptance: report accepted defects, false blocks, human review time and cost per accepted change, at task level, including failed and inconclusive runs.

The [live builder pilot](../e4_agents/README.md#live-azure-builder-pilot) exercises
one task using actual Azure inference and local isolated candidate execution.
Its self-tests and independent gate results are recorded separately. It does
not estimate population defect rates or replace the human-review and cost
measurements required by this acceptance protocol. A later Azure replay moves
the same candidate/evaluator into rootless Podman on the runner; replay is not
another model call or an independent task.

## TODM evidence validation across experiments

Use the [digest-bound TODM adapter](../todm_validation/README.md) to evaluate
explicit evidence inventories. Keep technical verdict, qualification, authority,
and release separate. The [recorded Azure validation](../../evidence/runs/todm-azure-2026-11-08.json)
passes the bounded E1–E4 checks and negative controls while keeping release
`BLOCK` and methodological acceptance `INCONCLUSIVE`. No local manifest field
can authenticate an accountable business owner or authorize production.

For a portable captured bundle, run from its root:

```bash
python3 adapter/lab/todm_validation/validate.py --manifest manifest.json --root . --output validation-new.json
python3 adapter/lab/todm_validation/qualify_bundle.py --root . --output qualification-new
```

The qualification output must be a fresh path inside that root. Preserve the
original bundle, failed attempts and separate recovery supplements; do not
rewrite old evidence or replace missing runtime bytes with a new build.
