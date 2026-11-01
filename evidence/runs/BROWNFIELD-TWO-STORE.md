# BROWNFIELD-COEXISTENCE-C01 — original two-store source-head evidence

**Classification:** SYNTHETIC_TWO_POSTGRESQL_CONTAINERS_SINGLE_RUNNER.
**Decision:** narrowly verified technical sample; **not** real IBM Z/COBOL
coexistence, business acceptance, a production cutover, HA or rollback approval.

## Original CI identity

- Original exact-head [GitHub Actions run #41339443735](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41339443735) — **PASS**, 1 November 2026.
- Tested PR source SHA: `d0abda29878d66d5276247ac4e32ac879e110b6d`.
- The downloaded runner `provenance.txt` explicitly reports both
  `source_head_sha` and `checkout_sha` as the same SHA, with a hard-failing
  comparison in the workflow.
- Original artifact ID: `13096162996`, name
  `brownfield-two-store-synthetic-not-mainframe-g6`.
  SHA-256 of original ZIP:
  `32b860aa24ea057b1faf25f3181fc9981dd8e2fcc3facc3d637cc8d2e76945cc`.
- [Versioned runner JSON report](brownfield-two-store-pr63-original-summary.json)
  copied verbatim from the original job log. The original ZIP's
  `two-store-summary.json` has SHA-256
  `d26ae90fd73e6647400cd4e3812a8e7ca1bb37521bb0a88f7ad4dc28fbbfeabb`.
  The ZIP also contains `build.log` and `provenance.txt`, including both
  Podman container IDs, pinned image identity, runner versions and source SHAs.

## Actual observed bounds

| Independent observation | Original CI result |
| --- | --- |
| Source ledger (legacy adapter) | 8 recorded decisions |
| Target ledger (.NET 10) | 10 recorded decisions |
| Legacy ledger oracle | 10/10 true |
| Target ledger oracle | 10/10 true |
| Mismatch after legacy drift / missing outbox | Cutover rejected |
| Read-only shadow | No double postings; stale prediction surfaced |
| Old-epoch legacy operation | Fenced by cooperative controller |
| Before candidate-origin writes | Synthetic rollback allowed after exact reconciliation |
| After two candidate-origin decisions | Rollback rejected: `FORWARD_FIX_REQUIRED` |
| Direct SQL bypass of cooperative fence | Detected by independent oracle; **not prevented** |
| TODM G2 / G6 | INCONCLUSIVE / BLOCK |

## Preserve the initial negative provenance observation

Initial [run #41339301269](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41339301269)
also passed the same tests, but its default PR checkout was a *temporary
GitHub merge commit* (`checkout_sha=78d1140f14540561a18a84f69aa3ffa079e79c25`)
while the recorded source branch was
`6f1edc4183808a43e70b7bc0343ebae2cd378607`.
This result is **not** used to claim an exact-source-HEAD execution.
The workflow was corrected to checkout and assert the actual PR source SHA;
the second original run above is the exact-SHA evidence.

**Missing:** production IBM Z fencing; durable gateway admission/UNKNOWN
journal; distributed XA/2PC alternatives and partial-copy recovery; cross-node
HA, externalized customer rules, approved Golden Master, TODM G2/G6.
Issue [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)
remains open. No release update.
