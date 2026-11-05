# Channel per-hop logical failures — original 40-case synthetic audit

[Español](CHANNEL-HOP-FAULTS.es.md) · [Research EN](../../docs/research/channel-hop-failures.en.md) · [PR #99](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/99).

**Original 5 November 2026 result: 40/40 Python controls PASS on seven fictional hop event traces. No physical network cut or bank authorization.**

## Original source/run provenance

- [Actions #42028436325](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42028436325), job `127248415098`, exact original source and checkout SHA `8bec46074a50daa5d08ecc174662e837cad8ab8c`.
- The original job log shows **40 named tests passed**, `Ran 40 tests`, zero unexpected failures, and `PASS_40_SYNTHETIC_HOP_CONTROLS`. The [selected original job log](CHANNEL-HOP-PR99-ORIGINAL-CI-EXCERPT.log) retains timestamped lines verbatim; it is not a complete workflow archive.
- GitHub published artifact ID `13415051431`, name `channel-hop-faults-synthetic-original-not-physical`, size **2,637 bytes**, checksum `sha256:3ac341c70ccf4a17db27a8218f299768ff64f7c782cedb5cebec62ed66ad2101`, initially expiring 3 February 2027. **The ZIP bytes have not been independently rehashed or inspected** in this record. This is GitHub-reported metadata, not an independent ZIP integrity audit. [Machine-readable provenance](channel-hop-pr99-original-ci-summary.json).
- The first Book run for this increment failed **MD012** on two excess blank lines in the roadmaps. Those defects were corrected in later commits; the original failed run stays FAIL. The code tests were separate and successful.

## Seven observations, seven strictly limited outcomes

| ID | Fictional event sequence | Result |
| --- | --- | --- |
| H01 | ATM→switch request lost before switch delivery | `NO_CORE_AUTHORIZATION_EVIDENCE` |
| H02 | Switch→core request dropped before issuer delivery | `NO_CORE_AUTHORIZATION_EVIDENCE` |
| H03 | Issuer COMMIT, reply lost on switch/core hop; link restored; original issuer status confirmed | `AUTHORIZATION_RECOVERED_BY_STATUS` |
| H04 | Device command sent, ATM↔switch link down, device reply unavailable and late advice received | `CASH_UNKNOWN_NO_REDISPENSE` |
| H05 | Writer epoch changes; reply from old writer arrives afterward | `QUARANTINED_OLD_OWNER_REPLY` |
| H06 | Partial device cash (6,000/10,000) and posted ledger amount match in a fictional snapshot | `PARTIAL_CASH_RECONCILED_SYNTHETICALLY` |
| H07 | Core unavailable; switch requests stand-in but issuer delegation missing | `STAND_IN_DENIED` |

The negative controls reject impossible message delivery over a DOWN link, issuer decisions without source request, invented status after reply loss, duplicate dispense/ledger posting, physical outcome silently changed from UNKNOWN, stale writer epochs, false cutover witnesses, and synthetic assertions of bank/device/network execution.

**No result authorizes financial activity:** `physicalLinkCutTested=false`, `nativeIssuerLogAuthenticated=false`, `physicalCashJournalAuthenticated=false`, `delegatedStandInAuthority=false`, `automaticAuthorizationAllowed=false`, `automaticDispenseAllowed=false`, `automaticPostingAllowed=false`, `automaticReversalAllowed=false`, `cohortWriterCutoverAuthorized=false`, `productionApproved=false`, TODM **G2 INCONCLUSIVE / G6 BLOCK**.

This is **a trace-model check only**, not a real TCP partition, a measured failover, a physical ATM journal, scheme message validation, source-owned fencing, authentic issuer/Db2/CICS/IMS commit, or banking acceptance. A wholly invented but internally consistent trace can pass. The existing native .NET 10/two-PostgreSQL channels experiment, synthetic 33-case late advice gate, earlier Book and PDF experiments all retain **separate scope and original provenance**. Keep #30 open for actual per-hop failure injection and full L01–L16 customer acceptance, #53 frozen, E2 `partially_verified`. No release.
