# Changelog

Editions use calendar versioning: `vYYYY.MM.DD`.

## v2026.11.05 · Final bounded research closeout

- Final bilingual research/book source snapshot, preserving the historical first-edition cover identity `v2026.10.29` (this tag freezes the research project rather than a second redesigned edition).
- Bounded synthetic E1 and E2 evidence retained as `partially_verified`; E3 and E4 acceptance studies closed as `designed_not_executed`, not represented as PASS.
- Brownfield, channel, vendor and architectural research consolidated with [English final limitations](docs/FINAL_CLOSEOUT.md) / [Spanish](docs/FINAL_CLOSEOUT.es.md).
- No mainframe/production parity, real source-side bank fence, HA, ISO 8583/device certification or G2/G6 release authority inferred.
- Publication is gated on the release workflow producing two complete PDF books and two Markdown books; original evidence and historical releases remain immutable.


## v2026.10.31-rc1 · Functional-first research preview (pre-release)

- Bilingual companion chapter on mainframe decomposition and evidence-aware Oracle Gates (#50).
- Business-first capability discovery: 30 **unverified** hypotheses across 12 domains; no mandatory source parser (#51).
- .NET 10 **synthetic in-memory** transfer/balance candidate, independent Python oracles, TODM-inspired G0–G7, separate Golden Master and 66 adversarial Python tests (#52).
- Independent verification, ES/EN generated volumes, PDF previews and parser-first regression guard.
- Does **not** claim a new numbered editorial edition or a production-ready banking migration. The first-edition cover identity remains `v2026.10.29`; see [ES/EN research preview notes](docs/releases/v2026.10.31-rc1.md).
- Production oracles, durable SQL, owner sign-off, confidentiality PoC and renewed diagram artwork remain open.

## v2026.10.29 · First open edition

- Complete book in Spanish (original) and English, with the same structure: 37 chapters in seven parts, an epilogue and seven annexes.
- The whole book on one page per language, `book/es.md` and `book/en.md`, generated from the chapters by `scripts/build.py`.
- 41 Mermaid diagrams per language: C4 context, container and deployment; UML sequence, state and class; ER; gitGraph; flowcharts and charts.
- `scripts/check.py`: links, strict Spanish/English sync and generated files, enforced in CI.
- Lab in English with Podman, offline verification and a coordinated omission simulation; core code identical to the reference run of 29/10/2026.
- Contribution guide, governance, templates, CODEOWNERS over the oracle and one-command GitHub setup.

Pending: reproduction reports of the Podman image on real machines and compiling the illustrative listings.
