# Repository language policy

The repository contains **one bilingual book** and **English-only software projects**. This is a permanent contribution and release requirement, not a one-time translation task.

| Material | Language | Where |
|---|---|---|
| Original book, chapters, prose, annexes, figure labels and generated PDF/Markdown | **Spanish and English**, complete and structurally synchronized | `book/es/`, `book/en/`, `book/es.md`, `book/en.md` |
| Code examples printed in either edition | **English in BOTH editions** (identifiers, comments, messages, sample filenames and README excerpts) | Fenced code blocks in `book/es/` and `book/en/` |
| Executable projects and labs | **English only**: source, comments, tests, assertions, CLI, README, examples and instructions | `lab/` |
| Automation and developer tooling | **English only**: scripts, workflows, pipeline logs, diagnostics, issue/PR templates and source-level documentation | `scripts/`, `.github/`, automation configuration |
| Machine-readable evidence | **English only**: fields, status values, run IDs, artifact names and test labels | `evidence/claims.json`, `evidence/runs/*.json`, CI artifacts |
| Reader-facing book site and commentary | May be **bilingual** when it accompanies the two editions, not when it documents a software project | Root `README.md` / `README.es.md`, `ROADMAP`, editorial notes, bilingual explanatory research/evidence reports under `docs/` or `evidence/runs/` |

## Rules for new work

1. Write **all new code and engineering documentation in English**. Do not add `README.es.md`, `*.es.md` or duplicated translated documentation under `lab/`. A project must have one canonical English `README.md`; references from the Spanish book should point to that English project README when reproduction instructions are needed.
2. For substantive book content, update **both** `book/es/` and `book/en/`. Source code inside the Spanish book **remains in English**. Narrative paragraphs, headings and diagram labels are translated, not the code.
3. Keep full experimental evidence with the code project in **language-neutral JSON / English identifiers**, and write any bilingual interpretation in the **book's reader-facing layer** (or its companion evidence reports). Code-project README files remain English only.
4. Treat filenames, paths, test names, issue titles, commit messages, protocols, status enums, infrastructure labels, warnings and error messages as engineering interfaces: **English by default**. Proper nouns, quoted third-party material and intentional locale-test data are exceptions; they must be explicitly justified.
5. Maintain authorship: José María Flores Zazo retains final editorial authority. Translating or reviewing a chapter does not transfer authorship or authorization to an agent.
6. Before review, run:
   ```bash
   python3 scripts/check_language_policy.py
   python3 scripts/check.py
   ```
   The first check enforces project structure and catches common accidental Spanish engineering prose; the second checks book synchronization, relative links, figures and generated editions. **Automated checks do not replace a human language and code review.**

## Boundary examples

- ✅ `lab/durable_rpc/README.md` contains setup, usage and warnings in English.
- ✅ `book/es/.../25a-....md` explains M2 in Spanish; `book/en/.../25a-....md` explains M2 in English.
- ✅ `book/es/` and `book/en/` both show the same C# identifiers, SQL, proto contracts and CLI examples **in English**.
- ✅ `evidence/runs/m2-full-summary.json` contains original numeric observations and English machine-readable fields.
- ❌ `lab/durable_rpc/README.es.md` or Spanish comments in `Program.cs`.
- ❌ Changing only one edition, translating API identifiers in the Spanish edition or using untranslated Spanish prose as a .NET project's README.

**This policy applies to all future branches and PRs, including experiments E1–E4, infrastructure pricing and gRPC benchmarks.**
