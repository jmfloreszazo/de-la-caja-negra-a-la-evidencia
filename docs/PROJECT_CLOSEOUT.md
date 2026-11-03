# Project closeout checkpoint — 3 November 2026

The author requested branch hygiene, incremental issue closure and a concrete remaining-work list. PRs #78–#81 are merged into main `fa0cd64355a3b75c18226ea78da149358d9531b2`. No research result is promoted by this administrative cleanup. E2 remains partially verified and the performance contract remains UNCONFIGURED.

## Branch review and recovery

The reviewed inventory contains 28 remote branches including main. The cleanup plan retires 27 work refs: 21 ancestors of main, four tips with trees byte-identical to their recorded merged commits, and two superseded/unmerged duplicates (#46/#67). Those last two are **archived, not merged**; their variants must not be silently reintroduced as accepted source. There are no open feature PRs at this checkpoint.

The [immutable manifest](../evidence/maintenance/branch-closeout-2026-11-03.json) records every branch/tip/proof and the SHA256 of a [Git recovery bundle](../evidence/maintenance/branch-closeout-2026-11-03.bundle). All six non-ancestor histories are retained in that bundle; the other 21 tips are reachable from main. The release preview tip also remains reachable through its published tag. No tag or release is removed.

The one-time repository workflow validates all proofs, closed-PR states, exact current tip SHA and absence of an open PR before any deletion. Git pushes use atomic force-with-lease checks for the exact reviewed SHA; a changed ref is not deleted. The maintenance branch is removed only after verifying its own exact merged PR. The workflow result and a fresh branches API inventory establish actual completion, not this planned count alone.

| Reviewed branch | Proof | PR |
| --- | --- | --- |
| `book/functional-first-diagrams-54` | ancestor_of_main | #55 |
| `ci/brownfield-postmerge-evidence-58` | identical_merged_tree | #62 |
| `ci/unconditional-premerge-gate-16` | ancestor_of_main | #57 |
| `docs/e2-b05-40-80-sql-evidence` | superseded_archived | #46 |
| `docs/roadmap-evidence-rebaseline-2026-11-01` | ancestor_of_main | #65 |
| `experiment/b05-dispatch-diagnostics-25` | ancestor_of_main | #81 |
| `experiment/brownfield-c2-durable-fence-recovery` | ancestor_of_main | #69 |
| `experiment/c01-controlled-placement-44` | ancestor_of_main | #72 |
| `experiment/c05-c06-directional-partition-24` | ancestor_of_main | #73 |
| `experiment/e2-account-directed-24` | ancestor_of_main | #80 |
| `experiment/e2-activation-observation-24` | ancestor_of_main | #78 |
| `experiment/e2-f10-c04-client-gateways` | ancestor_of_main | #34 |
| `experiment/e2-long-partition-24` | ancestor_of_main | #77 |
| `experiment/e2-observer-calibration-24` | ancestor_of_main | #79 |
| `experiment/e2-placement-observation-74` | ancestor_of_main | #76 |
| `feature/brownfield-c2-admission-journal-64` | ancestor_of_main | #66 |
| `feature/brownfield-capability-gateway-58` | identical_merged_tree | #68 |
| `feature/brownfield-cutover-rehearsal-58` | identical_merged_tree | #60 |
| `feature/brownfield-durable-authority-58` | identical_merged_tree | #61 |
| `feature/brownfield-two-store-coexistence-58` | superseded_archived | #67 |
| `feature/c2-inflight-controller-link` | ancestor_of_main | #70 |
| `feature/greenfield-cap007-cap005-contract` | ancestor_of_main | #52 |
| `fix/pdf-alert-markers` | ancestor_of_main | #71 |
| `release/v2026.10.31-research-preview` | ancestor_of_main | #56 |
| `research/brownfield-cap007-005-gap-58` | ancestor_of_main | #59 |
| `research/mainframe-decomposition-contract-32` | ancestor_of_main | #50 |
| `research/mainframe-static-archaeology-32` | ancestor_of_main | #51 |

To recover a preserved variant after fetching main:

```bash
git fetch origin main
git bundle verify evidence/maintenance/branch-closeout-2026-11-03.bundle
git bundle list-heads evidence/maintenance/branch-closeout-2026-11-03.bundle
# Choose one listed ref explicitly; recovery creates a new local branch.
git fetch evidence/maintenance/branch-closeout-2026-11-03.bundle refs/remotes/origin/docs/e2-b05-40-80-sql-evidence:refs/heads/recovered/b05-duplicate
```

## Issue closure and retained obligations

Nine issues were closed; 13 remain open, including two explicitly frozen items. Closed does not mean that every historical checkbox became an executed PASS.

| Closed | Disposition | Remaining work retained in |
| --- | --- | --- |
| #13 | Hosted-runner outage resolved; original successful recovery records preserved | #15 public-history/license/image review remains unperformed |
| #35 | SQL readiness and diagnostic implementation delivered in #36; no zero-flakiness claim | #8 further E2 acceptance |
| #75 | Non-blocking service-status anomaly archived without a root-cause claim | #15 recurrence/escalation handling |
| #74 | Provider-specific observation persistence and negatives delivered in #76 | #8 natural placement/lifecycle investigation |
| #64 | Durable journal and bounded controller-loss/recovery implementation delivered | #58 remaining timing windows, real fence and business approval |
| #29 | Overlapping channels work consolidated; full original checklist retained | #30 all unchecked CH requirements |
| #24 | Bounded partition/calibration/directed observation implementation delivered | #8 natural/continuous recovery and physical-domain acceptance |
| #25 | Hosted pilot/diagnostic delivered; separate capacity tracker retired | #8 unexecuted sustained capacity, bottleneck and service p99 |
| #12 | Local M1/M2 prerequisite delivered; duplicate distributed tracker retired | #9 TLS/distributed load/failover/WAN/TCO acceptance |

## What remains, in execution order

| Order | Work | Tracker / completion boundary |
| --- | --- | --- |
| 1 | Editorial/source review of both editions, listings, citations, overlaps and visual PDF QA; cross-platform reproduction | #11; integration previews do not authorize a release |
| 2 | One complete channel/core treatment and synthetic ATM/digital-channel lab, preserving physical dispense versus financial COMMIT | #30 incorporates #29 |
| 3 | Mainframe OS/I-O/transaction semantics and vendor-backed capability-to-pattern catalogue | #17/#18/#28; not three competing implementations of the same lab |
| 4 | Functional decomposition and bounded brownfield coexistence follow-up | #32/#58; real traces, source-side fence and TODM G2/G6 remain external approval |
| 5 | Dedicated lab organization/entrypoint refactor and consolidated maintenance review | #15; preserve every protected path/hash or provide an explicit compatibility plan |
| External backlog | Stronger E2 capacity/activation/HA and E3 distributed WAN/TCO campaigns | #8/#9, [external protocol](EXTERNAL_VALIDATION.md); non-blocking for editorial progress |
| Later experiment | Agent proposal versus independent mutation-qualified Oracle Gate | #10; not yet accepted as E4 |
| Frozen | Main branch ruleset; confidential computing/clean rooms | #16/#53; excluded until renewed instruction |

Use one short-lived branch per concrete deliverable and remove it after verified integration. Do not keep merged branches alive merely to preserve experimental provenance: immutable source commits, raw artifacts and the recovery bundle provide that record.
