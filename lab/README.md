# COBOL → .NET 10 modernization evidence lab

Companion lab for the book *De la caja negra a la evidencia* (Spanish) by **José María Flores Zazo** · GnuCOBOL · .NET 10 · SQLite · Python · Podman

> **What this lab is for**
> A demo shows that something is possible. Evidence shows that a property holds. This lab lets you run a real COBOL program, compare it with a C# candidate, watch an Oracle Gate block deliberate defects, and then push a transfer service through races, duplicates, crashes and lock waits, checking the persisted ledger independently.

It is small on purpose. You can read every file in an afternoon, change one line and see which property stops holding. It is **not** a mainframe emulator, a migration tool or a capacity benchmark. Section [What this lab does not prove](#what-this-lab-does-not-prove) is part of the deliverable, not a disclaimer.

## Three claims you can try to contradict

1. A COBOL program and a .NET 10 implementation can be compared against a **third, approved expectation**, so that two programs agreeing on a wrong answer still fail.
2. A gate that distinguishes **PASS, FAIL and INCONCLUSIVE**, and that separates *correct* from *authorized*, blocks every deliberate defect and every missing piece of evidence in the suite.
3. **Functional equivalence in isolation says nothing about concurrency.** The transfer module shows what has to hold once two processes compete for the same balance, a client resends, or a process dies after the debit.

## Quick start with Podman (recommended)

Podman runs rootless and daemonless, so the files written to `results/` belong to your user.

Linux, macOS (with `podman machine`) or WSL:

```bash
bash scripts/run-podman.sh          # guided, pauses between steps
bash scripts/run-podman.sh --auto   # everything, including the bank module, no pauses
```

Windows PowerShell (Podman Desktop or `podman machine`):

```powershell
pwsh scripts/run-podman.ps1
pwsh scripts/run-podman.ps1 -Auto
```

Or by hand:

```bash
podman build -t cobol-modernization-lab -f Containerfile .
podman run --rm -it --network=none -v "$PWD/results:/work/results:Z" cobol-modernization-lab
podman run --rm --network=none -v "$PWD/results:/work/results:Z" cobol-modernization-lab \
       python3 walkthrough.py --auto --bank
```

The build needs network once (base image, `apt`, `dotnet restore`). The lab itself runs with `--network=none`: no model, no API key, no remote call. `:Z` relabels the volume on SELinux hosts and is harmless elsewhere. The base tag `mcr.microsoft.com/dotnet/sdk:10.0-noble` is mutable: pin a digest before measuring anything you want to reproduce.

> **Container recipe.** The reference run below was executed natively on Linux. The `Containerfile` and the Podman scripts are validated by the `podman` job of the repository's CI; a reproduction report from your machine is the best evidence you can add.

## Native start (Ubuntu 24.04 or WSL2)

Install the .NET 10 SDK following Microsoft's instructions and check `dotnet --version`. Then:

```bash
sudo apt-get update
sudo apt-get install -y gnucobol3 python3 libsqlite3-0 gcc
python3 walkthrough.py                 # guided
python3 walkthrough.py --auto --bank   # everything
```

Use the `DOTNET` and `COBC` environment variables to point to other executables. The bank module loads `libsqlite3.so.0` through P/Invoke, so it needs Linux (natively, in WSL2 or in the container).

## Checks you can run with Python only

```bash
python3 tools/verify_offline.py
```

No compiler and no SDK required. It verifies the baseline anchor, recomputes all 58 expected outputs with a **third independent implementation** of the written policy, reports which sources are byte-identical to the reference run, and re-runs the accounting oracle on the persisted reference databases (the corrupted negative control must be rejected).

```bash
python3 tools/coordinated_omission_demo.py
```

A deterministic simulation of why a closed-loop load test hides a 500 ms stall that an open-loop test exposes. It is a simulation, not a measurement.

## Module 1 · Run your COBOL locally

```bash
python3 cobol_local.py legacy/fee.cob --input 0000002500200Y
# expected: APPROVE|00000001
```

GnuCOBOL is a compiler plus runtime: `cobol_local.py` compiles with `cobc -x -free` into a temporary directory and runs the native binary with your input on stdin. It is a launcher, not an interpreter. Pass `--fixed` for fixed-format sources. It supports console programs that read stdin; sources with CICS, Db2, copybook libraries or vendor dialects need their own environment and options.

The input record has 14 characters: 8 digits of amount in cents, 5 digits of rate in basis points, and `Y`/`N` for an active customer. `REDEFINES` interprets the same 14 bytes as three fields.

## Module 2 · Equivalence and the Oracle Gate

```bash
python3 run.py
```

It compiles the COBOL program and two .NET 10 processes (`Candidate`, `Gate`), runs the **58 cases** of `contracts/cases.json` against both programs, and lets the gate compare every observation with the approved expectation. The baseline is anchored by `contracts/cases.sha256`.

| Control | What changes | Verdict | Delivery | Gate exit code |
|---|---|---|---|---|
| `none` | Correct candidate | PASS | SIMULATED_ALLOW | 0 |
| `round-even` | Banker's rounding (`MidpointRounding.ToEven`) | FAIL | BLOCK | 2 |
| `wrong-threshold` | Review threshold 1,200,000 instead of 1,000,000 | FAIL | BLOCK | 2 |
| `approve-inactive` | Inactive customers no longer rejected | FAIL | BLOCK | 2 |
| `missing-evidence` | One candidate observation removed | INCONCLUSIVE | BLOCK | 3 |
| `missing-case` | One case removed | INCONCLUSIVE | BLOCK | 3 |
| `duplicate-case` | One case duplicated | INCONCLUSIVE | BLOCK | 3 |
| `invalid-anchor` | Wrong baseline digest | INCONCLUSIVE | BLOCK | 3 |
| `no-mandate` | Correct candidate, no mandate | PASS | BLOCK | 4 |
| `equal-but-wrong` | COBOL and C# agree on a wrong result | FAIL | BLOCK | 2 |

`run.py` exits with 0 when every control, including the expected blocks, behaves as listed. `SIMULATED_ALLOW` is a lab label: nothing is deployed, signed or published.

The 58 cases are 14 explicit boundary and behaviour cases, 40 generated with a fixed seed and 4 invalid 14-character records. They are inputs of **one synthetic capability**, not 58 independent projects.

## Module 3 · Transfers, locks and failures

```bash
python3 bank_test.py
```

Independent .NET processes run transfers against a real SQLite database (WAL, `synchronous=FULL`) through its native library; a Python verifier reads the persisted data on its own. Writes are serialized by the engine with `BEGIN IMMEDIATE`, and the processes compete for that resource.

| Control | What must hold |
|---|---|
| `overdraftRace` | Two concurrent withdrawals of 70,000 from 100,000: exactly one commits |
| `duplicateAndConflict` | Eight concurrent requests with one identity: one effect, seven duplicates; same key with another amount: conflict, no second effect |
| `exceptionRollback` | Exception after the debit: the transaction rolls back |
| `processCrashRecovery` | Process exits abruptly after the debit: no partial charge survives |
| `commitWithoutResponse` | Commit then exit without answering: the resend recovers the decision without duplicating it |
| `lockWaitAndRetry` | A lock held by another process: wait and bounded retries succeed |
| `boundedRetries` | Retries exhausted: failure is reported and balances are untouched |
| `accountingInvariants` | Non-negative balances, conserved total, two balanced postings per operation, balance ↔ history agreement, one outbox row per commit |
| `oracleRejectsCorruptLedger` | A posting deleted on purpose: the oracle must reject the history |

The runs with 1, 2, 4 and 8 processes are **small closed-loop local observations** that include process launch time. They are not a sustained capacity test and cannot convert MIPS into vCPU. `results/bank/negative-control.db` is corrupted on purpose.

## Module 0 · Optional warm-up: three-way commission oracle

```bash
bash examples/commission-three-way/run.sh
```

A first, smaller lab: a commission computed with an implied decimal point (`PIC 9(8)V99`), an approved CSV baseline, a Python oracle that checks *baseline vs COBOL*, *baseline vs .NET* and *COBOL vs .NET*, a rounding mutant that must exit with code 2, and an **in-process race** where `SemaphoreSlim` fixes two withdrawals inside one process and nothing else. It was **not** part of the reference run. See its README.

## Capacity is a contract, not a number

`performance-contract.json` starts as `UNCONFIGURED`. Null values cannot produce PASS. Before any capacity trial, the service owner must fill in offered load, committed transfers per second, end-to-end p99, durability and replication policy, RPO/RTO, load with one node lost and the dataset and hot-key distribution. The local SQLite measurements do **not** satisfy this contract. `docs/EXPERIMENT_PROTOCOL.md` describes the next experiments (SQL engine with row locking, Orleans, Azure vs on-premises).

## Risk catalog

`risk-catalog/risk_catalog_100.md` and `.json` list one hundred modernization risks (R001–R100). For each one: an application option, an infrastructure capability and an oracle. It is not a frequency ranking and none of the entries is marked as solved in production. `owner` and `evidence` start empty so you can use it in a real assessment.

## Taking it into your SDLC

`ci/github-actions.yml` runs the walkthrough with the bank module and keeps `results/` as a build artifact. Copy it to `.github/workflows/` in the repository where you want it. This package has not created a pull request or enabled CI anywhere.

## Repository layout

```
legacy/fee.cob              synthetic COBOL service (REDEFINES, COMP-3, ROUNDED, ON SIZE ERROR)
Candidate/                  C# implementation with deliberate mutation modes
Gate/                       .NET contract evaluator: PASS / FAIL / INCONCLUSIVE + mandate
Bank/                       SQL transfers with idempotency, double-entry postings and outbox
contracts/                  58 approved cases and their SHA-256 anchor
run.py                      equivalence run and gate controls
bank_test.py                concurrency, recovery and local measurements
walkthrough.py              guided tour
cobol_local.py              compile and run a console COBOL source
tools/                      offline verification and coordinated-omission simulation
examples/commission-three-way/  warm-up lab (not in the reference run)
architecture/               SQL Server / Azure SQL ledger design sketch (not executed)
risk-catalog/               R001–R100
performance-contract.json   capacity contract template
ci/                         CI template
docs/                       step-by-step guide and experiment protocol
reference-results/          evidence from the reference run, unchanged
Containerfile, scripts/     Podman recipe and launch scripts
```

## Reference run and provenance

Native Linux execution on **29 October 2026** with .NET SDK 10.0.403 and `cobc (GnuCOBOL) 3.1.2.0`: 58 cases compared, ten gate controls with the expected verdicts, bank module PASS with all six invariants true. The C# process used SQLite 3.45.1 and the Python verifier 3.53.1; the difference is recorded rather than hidden. Raw outputs, source hashes and the databases are in `reference-results/`, see `reference-results/PROVENANCE.md`.

`tools/verify_offline.py` shows that every core source (`fee.cob`, `Candidate`, `Gate`, `Bank`, `run.py`, `bank_test.py`, `cases.json`) is byte-identical to the one hashed in that run. `walkthrough.py` and `cobol_local.py` were translated to English afterwards (user-facing strings only), so their hashes differ. A new run produces its own evidence in `results/`.

## What this lab does not prove

There is no REA integration, no autonomous agent in the loop, no actor cluster, no production SQL engine, no row-level locking, no SQL deadlock, no two-phase commit, no database failover, no power-loss test, no Azure deployment and no real outbox publisher. There is no measured mainframe baseline. It does not demonstrate industrial effectiveness, and the components, although separate processes, were built in the same piece of work, so it does not demonstrate independence between people.

The baseline hash and its anchor live in the same writable package. In production they must sit outside the builder's write scope and be bound to a real approval. The mandate is synthetic. The COBOL program does not cover CICS, Db2, JCL, EBCDIC, negative amounts or cross-platform COMP-3 file interchange.

## License

Original lab code: MIT, see `LICENSE`. GnuCOBOL, .NET, SQLite, Podman and the base images keep their own licenses; their binaries are not distributed in this package.
