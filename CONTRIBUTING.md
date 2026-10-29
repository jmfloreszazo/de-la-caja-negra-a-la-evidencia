# Contributing

> [!IMPORTANT]
> This repository is governed like the book it contains: every change brings its reason and, whenever possible, its proof. Nobody approves their own oracle, and an honest `INCONCLUSIVE` is worth more than a forced `PASS`.

You do not need to write a chapter to help. A well-reported erratum, a report that the lab does not start on your Mac or a clearer diagram improve the book as much as a new section. Questions are welcome in Spanish or English in [Discussions](../../discussions); everything else in the repository is written in English so that anyone can take part.

## Choose your path

| If you are… | Your best first contribution | Time | Label |
|---|---|---|---|
| A curious reader | Report an erratum or ask in Discussions | 15 minutes | `errata` |
| Anyone with Podman | Run the lab and open a reproduction report, also if it fails | 30 minutes | `reproduction` |
| Bilingual (Spanish/English) | Review the English version of one part against the Spanish original | An afternoon | `i18n` |
| A .NET developer | Compile an *Illustrative* listing and promote it to *Verified* | An afternoon | `lab` |
| A COBOL or mainframe veteran | Review Parts I and IV, add a real risk to the catalog | An afternoon | `risk` |
| An architect | Improve a C4 diagram, propose an ADR or discuss a pattern | An afternoon | `diagram`, `proposal` |
| Performance, SRE or data | Run one of the experiments E1–E3 | A weekend | `experiment` |
| A researcher | Design or run experiment E4 with agents under the gate | Several weeks | `experiment` |

Issues labelled `good first issue` are meant for getting started. The [roadmap](ROADMAP.md) holds the bigger work.

## Your first contribution in 15 minutes

**From the browser.** Open the file on GitHub, press the pencil, make the change and choose "Create a new branch and start a pull request". GitHub creates the fork and the branch for you.

**From the terminal**, with [GitHub CLI](https://cli.github.com):

```bash
gh repo fork jmfloreszazo/de-la-caja-negra-a-la-evidencia --clone
cd de-la-caja-negra-a-la-evidencia
git switch -c errata/ch-17-deadlock

# edit the chapter in BOTH languages:
#   book/es/parte-4-patrones/17-...md  and  book/en/part-4-patterns/17-...md

python3 scripts/build.py      # regenerate book/es.md and book/en.md
python3 scripts/check.py      # links, es/en sync, generated files
npx markdownlint-cli2 "**/*.md"

git commit -am "fix(errata): correct the lock order in chapter 17"
gh pr create --fill
```

## Two languages, one book

This is the rule that keeps the project simple: **the book exists in Spanish (`book/es/`, the original) and English (`book/en/`), and both must always say the same thing.**

- A change to the content goes into both languages **in the same pull request**. If you only speak one, open the PR anyway and ask for help with the other in the description; it will not be merged until both are done.
- `book/es.md` and `book/en.md` are generated. Never edit them by hand: run `python3 scripts/build.py` and commit them with your change.
- `python3 scripts/check.py` compares every page with its counterpart: sections, tables, listings, code blocks and their languages, diagram types, cited references and linked chapters. CI runs it on every pull request and blocks the merge if anything drifts.
- Diagrams are sources in `book/figures/src/es/` and `book/figures/src/en/` with the same identifier; `check.py` verifies that every page uses the same figures in both languages.
- Executed code is quoted exactly as it ran. Comments in illustrative code are translated.
- Spanish text uses Spain's conventions: angular quotes «así» and a dot as the thousands separator. English text uses British spelling.

## What happens after you open the pull request

1. CI runs markdownlint, `check.py` and the diagrams; if you touch `lab/`, the lab as well. A red pull request is not merged, but the messages say exactly what is missing.
2. A person reviews it. The goal is a first answer within a week; a friendly reminder is welcome if it does not come.
3. The review ends in "approved", "changes requested" or "not yet" with a concrete question. All three are progress.
4. Once merged, your name goes into [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md) and the change into the [CHANGELOG](CHANGELOG.md).

## What you can contribute

| Contribution | Start with | What it needs to get in |
|---|---|---|
| Erratum | "Erratum" issue or a direct PR | The current text, the corrected one, in both languages, and the source if it is a figure |
| Translation fix | "Translation" issue or a PR | The pair of pages and what differs |
| Reproduction report | "Reproduction report" issue | Operating system, versions, command and full output, also if it failed |
| New risk or evidence | "Modernization risk" issue | Application option, infrastructure capability and the test that could refute them |
| Diagram | PR | Valid Mermaid in both languages, a caption and the right type (below) |
| New content | "Content proposal" issue first | Sources with consultation date and a clear place in the structure |
| Lab experiment | Issue following [`lab/docs/EXPERIMENT_PROTOCOL.md`](lab/docs/EXPERIMENT_PROTOCOL.md) | Negative controls and raw results, including failed runs |

## Text rules

The book is written in the first person by its author, and corrections are integrated into that voice. A substantial contribution with its own judgement goes in signed, in both languages:

```markdown
> [!NOTE]
> **Contribution by @your-user.** Your text, with its sources.
```

- Every listing carries a label: *Executed* (part of the lab, with a recorded run), *Verified* (logic checked with an independent implementation) or *Illustrative* (neither compiled nor executed).
- New sources go to Annex G with a consultation date.
- No confidential or identifiable customer data.

## Diagram rules

Every diagram is a Mermaid source in `book/figures/src/es/<id>.mmd` and `book/figures/src/en/<id>.mmd`, rendered as a PNG with the book's visual identity (ink background, graphite nodes, red only for what matters) by `scripts/render_figures.py`. Chapters show the image with an italic caption underneath. One diagram, one idea.

- Edit the source in both languages; keep the same identifier and structure, change only the labels.
- Do not add colours or `%%{init}%%` directives to a source: the theme lives in `book/figures/theme.json` and `theme.css`.
- Run `python3 scripts/render_figures.py` and commit the new PNG files with the source. Install `fonts-noto-cjk` so your images match the rest.

| What you want to show | Diagram type |
|---|---|
| People and systems around the modernization | C4 context (`C4Context`) |
| Responsibilities and boundaries inside a solution | C4 container (`C4Container`) |
| Where each piece runs: Azure, data centre, mainframe | C4 deployment (`C4Deployment`) |
| Interactions over time, failures and retries | UML sequence (`sequenceDiagram`) |
| Life cycles: verdicts, partitions, coexistence | UML state (`stateDiagram-v2`) |
| Code and data models | UML class (`classDiagram`) and entity-relationship (`erDiagram`) |
| Decisions and flows | `flowchart` |
| Measured or simulated data | `xychart-beta`, always with the table of values |

Rendering needs `npm i -g @mermaid-js/mermaid-cli`; CI checks every source with `python3 scripts/render_figures.py --check`.

## Lab rules

- `lab/contracts/` and `lab/Gate/` are the oracle. Changing them requires an approved issue and a CODEOWNERS review: nobody approves their own oracle.
- A new control comes with its negative control: something that must make the gate fail, and does.
- `lab/reference-results/` is historical evidence and is never modified. New runs are shared in a reproduction report.
- If you change lab files, regenerate `lab/SHA256SUMS.txt`.

## Commits and branches

[Conventional Commits](https://www.conventionalcommits.org/) with these types: `docs(ch-NN)`, `fix(errata)`, `diagram(ch-NN)`, `i18n(ch-NN)`, `feat(lab)`, `test(lab)`, `ci` and `chore`. Branches follow the same pattern: `errata/ch-17-deadlock`, `i18n/part-3`, `lab/e1-postgresql`.

## Review checklist

1. Is it true and supported? A source, an experiment or the word "proposal".
2. Is it in both languages, and does `check.py` pass?
3. Does it respect listing labels and diagram types?
4. Is it small and reversible?
5. Does it improve the reading?

## License of contributions

By opening a pull request you agree that your contribution to the text is published under CC BY-SA 4.0 and your contribution to the code under MIT. See [LICENSE.md](LICENSE.md); decisions follow [GOVERNANCE.md](GOVERNANCE.md).

> **A small contribution with evidence is worth more than a big one with opinion.**
