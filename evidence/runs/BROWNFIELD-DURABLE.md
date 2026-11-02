# Brownfield durable SQL — original PR #61 synthetic evidence

**Scope:** one disposable PostgreSQL 16.13 database on a single GitHub-hosted
Ubuntu 24.04 Linux runner; .NET SDK 10.0.403 / Npgsql 10.0.3; no external bank.
This document records **what actually ran** rather than promising a future test.

- Original [Actions run #41323384008](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41323384008): **PASS**; independent SQL test step and artifact upload both completed successfully.
- Exact tested PR source HEAD: `531a221a6f8cbd625f1c8abe2c0f7b419b6f762d` (before this evidence-only commit).
- Original GitHub Actions artifact ID: `13089779910`, named `brownfield-synthetic-postgresql-not-business-g6`; SHA-256 of original downloaded ZIP: `dc40553f52f5c7fc2d7e4e7bb6e224ea348702e1786d070bdde6b0831b4b31bb`.
- [Original JSON report, transcribed byte-for-byte from the runner's log](brownfield-durable-pr61-original-summary.json): 1,924 bytes; SHA-256 of the artifact's JSON file `dcded8e7f7bb4bdbe77fb68acb8b815521858790354c0754760591f269aa903a`.
- The original ZIP also contains the `build.log` (0 warnings, 0 errors) and `provenance.txt` (runner OS, .NET, Podman 4.9.3, source/checkout SHAs and PostgreSQL image IDs/digests). Download through the original Actions run, not a generated re-run of the test.

## Observed matrix (all from the original JSON)

| Observation | Value |
| --- | --- |
| Operations | 15 (11 COMMITTED, 4 REJECTED) |
| Double-entry postings / outbox | 22 / 11 |
| Global watermark / final writer epoch | 15 / `legacy`, 3 |
| Independent SQL accounting checks | 11/11 TRUE |
| Negative corrupted-posting control | Rejected by independent oracle, then restored |
| External pre-COMMIT `SIGKILL` | PASS under one disposable PostgreSQL connection |
| Exit after SQL COMMIT before ACK | PASS with same-ID duplicate replay |
| Hot-account, stale version, writer fence and simulated rollback | PASS at fixture scale |
| TODM G6 | BLOCK |

**Limitations:** data are synthetic, account scope is fixed at 16, there is
only one SQL authority and one host. The `legacy` and `candidate` routes are
modes of the same implementation. Neither physical HA, real mainframe
coexistence, independent source/target DB reconciliation, production banking
policy, throughput parity, nor a business-approved Golden Master is shown.

**Integrity model:** the versioned JSON is an exact extract of original runner
output. The original Actions artifact and its SHA-256 remain the authoritative
evidence package. Later green workflows cannot retroactively change the
tested-source identity for this observation.
