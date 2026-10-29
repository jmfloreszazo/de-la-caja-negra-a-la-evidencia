# Governance

A book about separating the capacity to act from the authority to accept has to apply the same rule to itself. This document says who decides what, how, and where it is written down.

## Roles

| Role | Who | Can | Cannot |
|---|---|---|---|
| Author and maintainer | [@jmfloreszazo](https://github.com/jmfloreszazo) | Final editorial decision, custody of the lab oracle, publishing editions | Merge his own changes to `lab/contracts/` or `lab/Gate/` without leaving the issue and the reason in writing |
| Area reviewer | Contributors with a track record in one area (translation, lab, diagrams, risks) | Approve PRs in their area | Approve changes to the oracle or to the author's voice outside their area |
| Contributor | Anyone who opens an issue or a PR | Propose, fix, reproduce, translate, discuss | Approve their own PR |

Area reviewers are invited by the maintainer after several merged contributions in that area. The role is announced in Discussions and reflected in `.github/CODEOWNERS`.

## How decisions are made

| Type of change | Path | Who decides |
|---|---|---|
| Erratum, link, formatting | PR with one review | An area reviewer or the maintainer |
| Translation | PR with one review, `check.py` green | A translation reviewer or the maintainer |
| Diagram | PR with one review and the diagrams rendered in CI | An area reviewer or the maintainer |
| Substantial content | "Proposal" issue, at least seven days of conversation, then a PR | The maintainer, with the reason written in the issue |
| Lab oracle (`contracts/`, `Gate/`, `reference-results/`) | Approved issue, negative control included, CODEOWNERS review | The maintainer, never the proposer alone |
| Governance, licenses, code of conduct | Issue open for at least fourteen days | The maintainer, with the reason written down |

Disagreements are resolved with evidence: a source, an experiment or a case that contradicts the proposal. If they persist after that, the maintainer decides and leaves the decision and its reason in the issue, as he would with an ADR. A decision can be reopened if new evidence appears.

## Editions

The book is published in editions with calendar versioning: `vYYYY.MM.DD`. Each edition has its entry in the [CHANGELOG](CHANGELOG.md) and, when it is tagged, continuous integration attaches the whole book as a single Markdown file per language (`book/es.md` and `book/en.md`) to the release. An edition is only published with every workflow green, which includes the Spanish and English editions being in sync.

## Conduct

The [code of conduct](CODE_OF_CONDUCT.md) applies in every space of the project. Enforcing it is the maintainer's responsibility, who may delegate to area reviewers.
