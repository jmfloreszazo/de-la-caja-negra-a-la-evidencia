## Evidence sheet

**What changes and why**

<!-- One idea per PR. Closes #NN -->

**Type**

- [ ] Erratum
- [ ] Content
- [ ] Translation fix
- [ ] Diagram
- [ ] Lab
- [ ] Repository infrastructure

**Evidence**

<!-- Source with consultation date, command output, rendered diagram... -->

**Language policy**

- [ ] All source code, comments, tests, project READMEs, CLI help and engineering artifacts are in English
- [ ] Any new/changed chapter is maintained in **both Spanish and English** (`book/es/` and `book/en/`)
- [ ] All code listings embedded in both book editions remain **in English**, including code comments and examples
- [ ] No localized README or duplicated project documentation has been added under `lab/`
- [ ] `python3 scripts/check_language_policy.py` passed; [policy](../docs/LANGUAGE_POLICY.md) reviewed

**Checks**

- [ ] The change is in both `book/es/` and `book/en/` (or it does not touch the book)
- [ ] `python3 scripts/build.py` — `book/es.md` and `book/en.md` regenerated
- [ ] `python3 scripts/check.py` — links, es/en sync and generated files
- [ ] `npx markdownlint-cli2 "**/*.md"`
- [ ] `python3 scripts/render_figures.py` if I touched a diagram source (and I committed the new PNG)
- [ ] `python3 lab/tools/verify_offline.py` if I touched the lab
- [ ] New listings carry a label (Executed, Verified or Illustrative)
- [ ] I did not modify `lab/contracts/`, `lab/Gate/` or `lab/reference-results/` without an approved issue

**What I still do not know**

<!-- An honest INCONCLUSIVE helps more than a forced PASS. -->
