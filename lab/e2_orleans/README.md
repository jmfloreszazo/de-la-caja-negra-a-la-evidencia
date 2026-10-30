# E2 · Orleans-led account coordination (planned experiment)

**NOT IMPLEMENTED OR EXECUTED.** E2 has no passing Orleans CI test,
throughput result or production claim. Its detailed executable acceptance
contract is in [EXPERIMENT_PROTOCOL.md](EXPERIMENT_PROTOCOL.md). This
engineering laboratory and all future source, fixtures and READMEs are
**English only**.

## Why this experiment exists

E1 has established synthetic functional equivalence for the protected
SQLite reference and the PostgreSQL/SQL Server candidates, with original
CI evidence and independent accounting oracles. E2 asks a narrower and
falsifiable question: whether Orleans virtual actors can coordinate
account-keyed requests while **leaving debit, credit, postings, idempotent
operation record and outbox in one authoritative database transaction**.

The account grain does **not** own an ACID transaction spanning multiple
grains. It must never be used as a substitute for PostgreSQL locking,
conditional debit or operation-ID uniqueness.

## Planned implementation order

1. Pin `Microsoft.Orleans.Server` **10.4.0** and compatible Orleans
   packages for .NET 10, preserve dependency-lock fingerprints.
2. Extract the existing PostgreSQL E1b transfer logic behind one durable
   interface shared by both direct-ledger and Orleans-routed paths;
   preserve SQL isolation, retries and outbox semantics.
3. Add a non-reentrant account-keyed grain. No separate actor-local
   balance may become the source of truth.
4. Compare the original 16-account E1 behavior and failure contracts
   with independent SQL snapshots and the seven-invariant oracle.
5. Exercise deliberately unsafe cross-grain split writes and reentrancy
   only in disposable **negative-control fixtures**.
6. Prepare fixed uniform/hot operation lists: 1,000 benchmark accounts
   with exactly 50 hot accounts (5%) and another profile where one
   account receives 50% of request intents.
7. Compare baseline versus Orleans at equal offered load, transport and
   SQL pool settings; preserve full raw outcomes, p50/p95/p99 and
   committed transfers per second.
8. Run silo-failure and lost-response recovery, then independent
   oracle and mutation detection before any evidence promotion.

## Evidence and release policy

No E2 claims may enter the verified evidence registry until actual
GitHub Actions and a controlled Podman runtime execute the contract.
The current GitHub Actions issue (jobs terminating before runner
assignment) is an external CI gate and is **not** a passed E2 test.

Do not modify the protected original E1 tests or publish, tag, merge,
or open the repository without the maintainer's authorization.

See [issue #8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8)
and the [global experiment roadmap](../../docs/EXPERIMENT_ROADMAP.md).
