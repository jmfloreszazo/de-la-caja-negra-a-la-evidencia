# C2 · Durable admission/UNKNOWN journal — original CI evidence

**Verified technical slice only, 1 November 2026.** Original [GitHub Actions run #41342450730](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41342450730) completed successfully on exact source HEAD `8dc391d276724726eca68373150dfceaf1e291e0`; original job ID `124955148855`.

- [Machine-readable log-extracted observation](brownfield-c2-pr66-ci-log-extracted.json) includes the actual controls and both SQL oracles. It is **transcribed from the original CI text log**, not a purported raw artifact ZIP.
- Original uploaded artifact ID **13098480178**, name `brownfield-c2-journal-synthetic-g6-block`, size **3145 bytes**. GitHub-reported ZIP SHA-256: `e0479df604fd607825a794b2b00a3487d9103cbc46aa8887d897f6f1a6175827`.
- The run produced `status=PASS` with **11 completed controls**: real process exits, lost ACK replay, forged terminal decision failure, controller loss, strict adapter admission checks and opt-out bypass detection.
- Final `lastJournalAudit.passed=false` is **intentional negative evidence**, not a false overall PASS: `J-ADMIT-DEAD` and `J-DISPATCH-DEAD` remain UNKNOWN, and opt-out `J-DIRECT-BYPASS` is flagged as unjournaled. Both source and target ledger oracles were true.

**Limitations:** This is three disposable PostgreSQL containers on ONE Linux CI host, not three fault domains or a genuine CICS/Db2 fence. Strict mode is opt-in, authority updates are not atomic across databases, and no real customer mandate or business Golden Master has been approved. G2=INCONCLUSIVE, G6=BLOCK. #64/#58 stay open, #53 frozen. Source HEAD provenance is historical: subsequent doc changes have different SHAs. No release/tag update.
