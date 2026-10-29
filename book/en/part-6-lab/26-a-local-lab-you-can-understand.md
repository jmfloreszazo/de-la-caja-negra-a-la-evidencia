**English** · [Español](../../es/parte-6-laboratorio/26-un-laboratorio-local-que-se-puede-entender.md)

[← Part VI · The lab: from demo to evidence](README.md) · [Contents](../README.md) · [Chapter 27 · Making the error visible →](27-making-the-error-visible.md)

# Chapter 26 · A local lab you can understand

> [!IMPORTANT]
> **Chapter thesis.** Real COBOL, a C# candidate, an independent gate and a pinned contract, run locally without calling any model. How easy it is to reproduce should help us see the real difficulty more clearly.

> [!NOTE]
> In this repository the lab lives in the [`lab/`](../../../lab/README.md) folder. The commands in this text are run from there.

## The teaching case

The service receives a fourteen-character record. The first eight represent the amount in cents; the next five, the rate in basis points; the last indicates whether the customer is active. Accepted values are zero to 99,999,999 cents, zero to 10,000 basis points and the states Y or N.

An inactive customer receives REJECT with a zero fee. An active customer receives REVIEW when the amount exceeds 1,000,000 cents; at the exact threshold it receives APPROVE. The fee is calculated for active customers with the rounding described in chapter [12](../part-3-oracles/12-cobol-and-c-must-agree-on-meaning.md). Fixed-width records that contain invalid characters or an out-of-range rate return INVALID and a zero fee.

The policy is fictional and we chose it because it lets us study rule priority, comparison boundaries, representation and rounding within a small program.

The contract includes 58 cases: fourteen explicit boundary and behaviour cases, forty cases generated with a fixed seed and four invalid fourteen-character records. They are inputs of one synthetic capability, not 58 independent projects or a sample of enterprise applications.

This is the complete program. It is worth reading slowly: in 40 lines you will find `REDEFINES`, a `COMP-3` field, `ROUNDED`, `ON SIZE ERROR` and a rule priority that is not the one you would intuitively write.

**Listing 26.1 · legacy/fee.cob** — *Executed*

```cobol
identification division.
program-id. fee.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
01 raw-input pic x(14).
01 request-fields redefines raw-input.
   05 amount-cents pic 9(8).
   05 rate-bps pic 9(5).
   05 customer-active pic x.
01 fee-cents pic 9(8) comp-3.
01 fee-display pic 9(8).
01 result-code pic x(7).
procedure division.
    accept raw-input
    move 0 to fee-cents fee-display
    evaluate true
      when amount-cents is not numeric
      when rate-bps is not numeric
      when customer-active not = 'Y' and not = 'N'
        move 'INVALID' to result-code
      when rate-bps > 10000
        move 'INVALID' to result-code
      when customer-active = 'N'
        move 'REJECT' to result-code
      when other
        compute fee-cents rounded = amount-cents * rate-bps / 10000
          on size error
            move 'INVALID' to result-code
          not on size error
            move fee-cents to fee-display
            if amount-cents > 1000000
              move 'REVIEW' to result-code
            else
              move 'APPROVE' to result-code
            end-if
        end-compute
    end-evaluate
    display trim(result-code) '|' fee-display
    goback.
```

## What running COBOL locally means

GnuCOBOL provides the compiler and runtime used in the lab. The command `cobc -x -free` generates an executable from the source [10]. I do not present it as a pure interpreter. The guided walkthrough hides part of the repetitive mechanics, but shows the command and the result so the reader knows what is happening.

The package contains the COBOL source, a C# candidate implementation, an independent gate as a .NET process, the pinned cases and a Python orchestrator. Python launches the programs and keeps the observations. The acceptance decision is computed by the .NET gate.

There is a reason to keep the demo free of calls to a remote model: reproducing the behaviour must not depend on the provider answering the same way or on having a key. The lab was built with AI assistance, but its execution includes no autonomous agent and no REA integration. Those extensions are described later as additional work.

## Two ways to go through it

The full run prepares the binaries, executes cases and controls and saves the reports. The guided mode stops between steps: it explains the record, shows the COBOL, runs an example, shows the candidate translation and ends with the gates.

The native route needs Python, the .NET 10 SDK and GnuCOBOL. The package also includes a Podman recipe that brings them together in an image and runs the lab with no network. The exact commands are in Annex [A](../annexes/annex-a-a-lab-that-can-prove-us-wrong.md) and the README. It is important to distinguish the verified native execution from a container recipe that must be validated on the machine where it is built.

At the end, the reader has result files they can open and compare. They do not need to trust a screenshot. They can change an implementation, repeat the walkthrough and examine which property stopped holding.

## What's in the box

**Listing 26.2 · Lab structure (in English)** — *Executed*

```text
legacy/fee.cob              synthetic COBOL service
Candidate/                  C# implementation with deliberate mutation modes
Gate/                       .NET evaluator: PASS / FAIL / INCONCLUSIVE + mandate
Bank/                       SQL transfers with idempotency, double entry and outbox
contracts/                  58 approved cases and their SHA-256 anchor
run.py · bank_test.py       equivalence and controls · concurrency and recovery
walkthrough.py              guided walkthrough
cobol_local.py              compile and run a console COBOL source
tools/                      offline verification and coordinated omission simulation
examples/                   warm-up lab: three-way oracle
risk-catalog/               R001–R100
reference-results/          evidence from the reference run, unmodified
Containerfile · scripts/    Podman recipe and launchers
```

![Figure 26.1 · The lab inside a Podman container with no network: who runs what and who decides.](../../figures/en/lab_c4.png)

*Figure 26.1 · The lab inside a Podman container with no network: who runs what and who decides.*

## Before compiling anything

Some checks need neither GnuCOBOL nor .NET, and it is worth doing them first. `tools/verify_offline.py` checks the baseline anchor, recomputes the 58 expected results with a third implementation of the written policy, reports which sources are byte-identical to those of the reference run and runs the accounting oracle again over the persisted databases.

**Listing 26.3 · Offline verification (abridged output)** — *Executed*

```text
[1] baseline anchor ............ OK
[2] independent policy ......... 58/58 cases agree
[3] provenance against the reference run (29 Oct 2026, native Linux):
    Bank/Program.cs                  identical
    Candidate/Program.cs             identical
    Gate/Program.cs                  identical
    legacy/fee.cob                   identical
    run.py                           identical
    walkthrough.py                   changed since reference run
[4] ledger oracle on reference databases:
    acceptance.db            PASS                                     as expected
    negative-control.db      REJECTED balancedPostings,twoPostingsPerCommit,projectionAgrees as expected

VERIFY: PASS (offline checks only; run.py and bank_test.py still require GnuCOBOL and .NET 10)
```

If the independent implementation disagreed with a case, I would stop there. It would mean the contract or my reading of the contract is wrong, and no amount of C# would fix that.

> **You do not need to trust a screenshot. You can change a line, repeat the walkthrough and see which property stops holding.**

---

[← Part VI · The lab: from demo to evidence](README.md) · [Contents](../README.md) · [Chapter 27 · Making the error visible →](27-making-the-error-visible.md)
