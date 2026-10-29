# Changelog

Editions use calendar versioning: `vYYYY.MM.DD`.

## v2026.10.29 · First open edition

- Complete book in Spanish (original) and English, with the same structure: 37 chapters in seven parts, an epilogue and seven annexes.
- The whole book on one page per language, `book/es.md` and `book/en.md`, generated from the chapters by `scripts/build.py`.
- 41 Mermaid diagrams per language: C4 context, container and deployment; UML sequence, state and class; ER; gitGraph; flowcharts and charts.
- `scripts/check.py`: links, strict Spanish/English sync and generated files, enforced in CI.
- Lab in English with Podman, offline verification and a coordinated omission simulation; core code identical to the reference run of 29/10/2026.
- Contribution guide, governance, templates, CODEOWNERS over the oracle and one-command GitHub setup.

Pending: reproduction reports of the Podman image on real machines and compiling the illustrative listings.
