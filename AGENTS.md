# Agent and contributor instructions

This repository is authored and governed by José María Flores Zazo. Do not claim independent authorship, modify the release version or merge branches without explicit approval.

## Mandatory language rules

Read [the language policy](docs/LANGUAGE_POLICY.md) before making changes.

- **Software projects: English only**. This includes code, inline comments, tests, names, CLI flags, errors, log messages, developer documentation and every `lab/**/README.md`.
- **Book: Spanish AND English**. Every substantive change under `book/es/` must be mirrored under `book/en/` and vice versa.
- **Code samples in the book: English in both editions**. Never translate identifiers, commands, protocol fields or code comments into Spanish.
- **Evidence: English machine data**. Keep raw results intact, with original CI run ID, commit, environment, limitations, provenance and independent oracle. Reader-facing explanations may be bilingual but must not change raw observations.
- Run `python3 scripts/check_language_policy.py` and `python3 scripts/check.py` before proposing a PR. CI enforces both.

## Safety and provenance

Leave protected oracle/reference snapshots unchanged unless change control is approved. Distinguish executed tests from planned E1–E4 work, and localhost smoke tests from Azure or mainframe performance. No version bump, release or merge without explicit authorization.
