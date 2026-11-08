**English** · [Español](../es/00c-como-leer-este-libro.md)

[← Prologue](00b-prologue.md) · [Contents](README.md) · [Part I · Before translating →](part-1-before-translating/README.md)

# How to read this book

The common thread is one concrete transformation: moving from inherited behaviour we observe to an implementation whose result we can accept within a defined scope. Along the way come three questions every steering committee eventually asks —what does the system really do?, how do we know the new one does the same?, will it survive month-end close?— and a fourth that almost nobody asks in time: who has the authority to accept the risk that remains?

| Part | Question it answers |
|---|---|
| I · Before translating | What we are really preserving and why changing the language is not enough |
| II · Archaeology, knowledge and authority | How to recover evidence from the legacy with agents without mistaking hypotheses for facts |
| III · Oracles: the right to accept | How to decide that a candidate complies, separating correctness from authorization |
| IV · Patterns that replace responsibilities | Which modern mechanism replaces each mainframe guarantee, and when it does not |
| V · Capacity | How to approach what a mainframe delivers without converting MIPS into vCPUs |
| VI · The lab | How all of the above looks in code you can run and break |
| VII · From evidence to the organization | How to take it into the SDLC, a plan and a decision you can defend |

A technology leader will find criteria to scope a modernization, ask for useful evidence and know when not to migrate. An architect will find trust boundaries, contracts, patterns with their conditions of use and coexistence decisions. A developer will be able to run the COBOL, change the C# and watch the effect of those changes on a gate that will not be talked into anything. The same case ties the three perspectives together.

You can read it in order or by parts. If you are in a hurry about performance, Part V stands on its own. If you want to see the code first, start with Part VI and Annex [A](annexes/annex-a-a-lab-that-can-prove-us-wrong.md) and come back to the reasons later. If you have a budget to defend, chapters [33](part-7-organization/33-modernization-plan-first-a-capability-test-then-a-bet.md), [35](part-7-organization/35-when-i-would-not-migrate.md) and [37](part-7-organization/37-the-new-modernization-contract.md) were written for that.

Numbered references in square brackets point to Annex [G](annexes/annex-g-sources-and-scope-of-the-research.md). The complete code, the commands and the reference results are in the accompanying lab. The first-edition identifier is 29 October 2026; the [archival research release](../../docs/releases/v2026.11.05.md) preserves the later closeout of 5 November without turning partial experiments into accepted results.

## Authorship and responsibility

This book is written by **José María Flores Zazo**, author of [jmfloreszazo.com](https://jmfloreszazo.com). The first-person arguments and editorial decisions belong to the author. Tools used to prepare, translate or check the material do not acquire authorship or authority to approve its conclusions.

## Reading is not the same as reproducing

I distinguish four things a reader can verify. None substitutes for the next:

| Scope | Reproduction entry point | What success establishes |
|---|---|---|
| Manuscript and figures | [Repository checks](../../README.md#reproduce-by-scope) and [PDF build](../../docs/PDF.md) | Paired structure, current generated text and a buildable edition; not full editorial approval or byte-identical PDFs |
| Preserved reference run | [Python-only lab checks](../../lab/README.md#checks-you-can-run-with-python-only) | Original contract hashes, 58 independently recomputed expectations and accounting checks on historical databases; not a new COBOL/.NET execution |
| Fresh synthetic execution | [Host reproduction protocol](../../lab/docs/HOST_REPRODUCTION.md) | The named walkthrough and independent audit on a recorded host and image; not all repository experiments |
| Extended experiments | [Evidence matrix](../../docs/EVIDENCE.md) and each experiment's runbook | Only the recorded workload, environment, controls and observed verdict; no mainframe, Azure or production equivalence by inference |

For a reproducible result, preserve the exact source commit, local changes if any, tool versions, command, exit code, raw output and independent oracle. Preserve failed attempts too. A missing runtime or unexecuted platform is a limitation to report, not a successful reproduction. E1/E2 remain partially verified. E3 and E4 have bounded single-VM demonstrations on Azure (chapters 25 bis and 29) that are recorded as `demonstrated_not_accepted`: real executions, not acceptance studies.

---

[← Prologue](00b-prologue.md) · [Contents](README.md) · [Part I · Before translating →](part-1-before-translating/README.md)
