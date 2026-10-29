**English** · [Español](../../es/anexos/anexo-a-un-laboratorio-que-pueda-contradecirnos.md)

[← Annexes](README.md) · [Contents](../README.md) · [Annex B · Lab contract →](annex-b-lab-contract.md)

# Annex A · A lab that can prove us wrong

> [!NOTE]
> In this repository the lab lives in the [`lab/`](../../../lab/README.md) folder. The commands in this text are run from there.

## What it sets out to demonstrate

The lab is not built to convince but to be contradicted. It makes three claims, and each can fall if someone finds the counterexample.

The first: an executable COBOL program and a .NET 10 implementation can be compared against a **third, approved expectation**, so that two programs agreeing on an error also fail. The second: a gate that distinguishes **PASS, FAIL and INCONCLUSIVE**, and separates correct from authorized, blocks every deliberate defect and every missing piece of evidence in the set. The third: **isolated functional equivalence says nothing about concurrency**; the transfer module shows what must hold when two processes compete for a balance, a client resends or a process dies after the debit.

## What you need

The recommended route only needs **Podman**. On Linux it installs from the package manager; on macOS and Windows, with Podman Desktop or `podman machine`. Podman runs without a daemon and without administrator privileges, so the files the container writes to `results/` belong to your user.

The native route needs Ubuntu 24.04 or WSL2 with the .NET 10 SDK, GnuCOBOL 3, Python 3 and the native SQLite library. The banking module loads `libsqlite3.so.0` through P/Invoke, so on Windows it must run in WSL2 or in the container.

For the offline checks, Python 3 is enough.

## Running with Podman

**Listing A.1 · Starting with Podman** — *Executed by design · recipe not built here*

```bash
# Linux, macOS or WSL
bash scripts/run-podman.sh          # guided walkthrough, with pauses
bash scripts/run-podman.sh --auto   # everything, including the banking module

# Windows PowerShell
pwsh scripts/run-podman.ps1
pwsh scripts/run-podman.ps1 -Auto

# By hand
podman build -t cobol-modernization-lab -f Containerfile .
podman run --rm -it --network=none -v "$PWD/results:/work/results:Z" cobol-modernization-lab
```

The build needs network access once: the base image, the packages and the .NET restore. The lab itself runs with `--network=none`: no model, no key and no remote calls. The `:Z` option relabels the volume on SELinux systems and is harmless elsewhere. The base image tag is mutable; pin a digest before measuring anything you want to reproduce.

The reference run is native on Linux. The Podman recipe is built and run by the `podman` continuous integration job; if it behaves differently on your machine, that reproduction report is exactly the evidence the lab asks for.

## Native run

```bash
sudo apt-get update
sudo apt-get install -y gnucobol3 python3 libsqlite3-0 gcc
python3 walkthrough.py                 # guided
python3 walkthrough.py --auto --bank   # everything
```

The `DOTNET` and `COBC` variables let you use other executables.

## The walkthrough, step by step

| Step | Command | What you should see |
|---|---|---|
| 0 | `python3 tools/verify_offline.py` | `VERIFY: PASS`: correct anchor, 58/58 cases agree with the independent implementation, negative control rejected |
| 1 | `walkthrough.py`, step 1 | The `fee.cob` source with its `REDEFINES` |
| 2 | `python3 cobol_local.py legacy/fee.cob --input 0000002500200Y` | The `cobc -x -free` command and the output `APPROVE\|00000001` |
| 3 | `walkthrough.py`, step 3 | The C# candidate and its mutation modes |
| 4 | `python3 run.py` | Ten controls with the verdicts of chapter [27](../part-6-lab/27-making-the-error-visible.md) and exit code 0 |
| 5 | `walkthrough.py`, step 5 | The table of verdicts and deliveries |
| 6 | `python3 bank_test.py` | `status: PASS`, nine controls and six true invariants |
| 7 | `python3 tools/coordinated_omission_demo.py` | A p99 of 1 ms in the closed loop versus 451 ms in the open loop |

The gate's exit codes are part of the contract: 0 for the synthetic permission, 2 for FAIL, 3 for INCONCLUSIVE and 4 for correct behaviour without a mandate. `run.py` ends with 0 when every control, including the expected blocks, behaves as it should.

## The optional warm-up

`examples/commission-three-way/` contains the first, smaller lab: a commission with an implied decimal point (`PIC 9(8)V99`), an approved CSV baseline, a Python oracle that compares baseline against COBOL, baseline against .NET and COBOL against .NET, a rounding mutant that must exit with code 2 and an in-memory race where `SemaphoreSlim` protects two withdrawals within one process and nothing more. It runs with `bash examples/commission-three-way/run.sh`. It is not part of the reference run; its baseline is consistent with the written policy and the mutant differs in four of the eight cases.

## What it does not prove

There is no REA integration, no autonomous agent, no actor cluster, no production SQL engine, no row locking, no SQL deadlock, no two-phase commit, no failover, no power-loss test, no Azure deployment and no real outbox publisher. There is no measured mainframe baseline. It does not demonstrate industrial effectiveness or independence between people: the components are separate processes, but they were built in the same piece of work.

The baseline hash and its anchor live in the same writable package. In production they must sit outside the builder's reach and be bound to a real approval. The mandate is synthetic.

## Where it grows

The file `docs/EXPERIMENT_PROTOCOL.md` describes four experiments that are designed and not executed. E1 ports the banking module to an engine with row locking and adds deadlock victims, write skew and pool exhaustion. E2 implements the same contract with Orleans actors that coordinate and a ledger that commits, under uniform and skewed distributions and with one account receiving half the traffic. E3 compares Azure, a local server with its second unit and a hybrid configuration with the same performance contract. E4 has an agent build the candidate with writes limited to `Candidate/` and compares tests written by the agent, an independent oracle and an oracle qualified by mutations.

---

[← Annexes](README.md) · [Contents](../README.md) · [Annex B · Lab contract →](annex-b-lab-contract.md)
