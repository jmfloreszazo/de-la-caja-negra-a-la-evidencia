# Experiment protocol for the next tiers

The current lab demonstrates mechanisms. The experiments below are designed, not executed. Each must produce its own evidence before anyone quotes a result.

## E1 · Row-locking SQL engine

Port `Bank/` to PostgreSQL or SQL Server with a conditional debit, a uniqueness constraint on the operation identity, double-entry postings and an outbox row in one local transaction. Add what SQLite cannot show: two transfers locking accounts in opposite order (deadlock victim + bounded full retry with the same identity), serializable vs snapshot behaviour on a multi-row invariant, and a connection pool sized below the offered concurrency.

Acceptance: every control of `bank_test.py`, plus `deadlockVictimRetried`, `writeSkewPrevented` and `poolExhaustionBounded`, evaluated by a verifier that only reads persisted state.

## E2 · Actors as coordinators, ledger as source of truth

Implement the same contract with Orleans grains keyed by account. The grain serializes requests per account; the debit/credit still commits in one SQL transaction (or in Orleans transactional state, declared explicitly). Compare with E1 under three distributions: uniform, 5 % of traffic on hot accounts, and one account receiving 50 % of traffic.

Acceptance: identical functional verdicts to E1; report committed transfers/s, p99 per operation class, conflicts, retries, and the throughput ceiling of the hottest key.

## E3 · Azure vs on-premises with the same contract

Fill `performance-contract.json` from a real workload footprint (RMF/SMF, CICS monitoring, batch windows). Run the same generator (open loop, controlled arrival rate, latency from intended send time), dataset, durability policy and failure injections on: (a) an Azure configuration with a managed SQL engine and synchronous replica if the contract requires it, (b) an on-premises server with its second unit, and (c) a hybrid keeping the core on the mainframe.

Acceptance: a configuration passes only if it meets the contract *with one unit lost*, drains the backlog within the agreed time, and keeps every functional and accounting invariant. Report cost per million committed transfers.

## E4 · Agents under the gate

Give an agent the public contract and write access only to `Candidate/`. Keep `contracts/` and `Gate/` outside its write scope (separate repository or protected path, verified by trying). Record model, prompt, tools, budget and every attempt. Compare: tests written by the agent, independent oracle, independent oracle + mutation qualification.

Acceptance: report accepted defects, false blocks, human review time and cost per accepted change, at task level, including failed and inconclusive runs.
