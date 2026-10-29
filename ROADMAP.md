# Open roadmap

**English** · [Español](ROADMAP.es.md)

Work the book leaves open and the community can move forward. Each line shows its label. The seed issues are created by `scripts/setup_github.sh` and grouped in the milestone "v2026.11 · Community review".

## Validate what could not be validated

| Task | Why it matters | Label |
|---|---|---|
| Build the Podman image on Linux, macOS and Windows and share the report | CI validates the recipe; real machines are what counts | `reproduction`, `good first issue` |
| Reproduce the full lab beyond hosted Linux CI and publish conditions/report | [Offline/native/Podman CI](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252152) already passed; independent cross-platform reproductions remain | `reproduction` |
| Compile the *Illustrative* listings in a sample project and promote those that pass to *Verified* | Today they are reasoning fragments; some deserve to be code | `lab`, `good first issue` |

## Experiments designed and not executed

Described in [`lab/docs/EXPERIMENT_PROTOCOL.md`](lab/docs/EXPERIMENT_PROTOCOL.md).

| Experiment | Question | Label |
|---|---|---|
| E1 · SQL engine with row locking | Do the controls hold with deadlock victims, write skew and pool exhaustion? | `experiment` |
| E2 · Actors that coordinate, a ledger that commits | What does Orleans add over E1 with uniform and skewed accounts and a hot account? | `experiment` |
| E3 · Azure, on-premises and hybrid with the same contract | Which configuration meets the contract with one unit lost, and at what cost? | `experiment` |
| E4 · Agents under the gate | Does the independent oracle reduce accepted defects compared with the agent's own tests? | `experiment` |

## Lab: next katas

- Turn the COMP-3 codec of chapter 15 into a module with its test vectors.
- Add an EBCDIC adapter with an explicit CCSID and ordering cases.
- Extend the contract with negative amounts and a matrix of compiler options.
- Port the accounting oracle to .NET to have two independent verifiers.

## Book

- Keep the Spanish and English editions in sync (`scripts/check.py` enforces it), and welcome other languages with the same structure.
- Expand the glossary and the risk catalog (R101 onwards) with real evidence.
- Real anonymized cases, with explicit permission and no identifiable customer figures.
