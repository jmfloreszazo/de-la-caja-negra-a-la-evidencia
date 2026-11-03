# E2 ordinary AccountGrain directed partition probe

Status: first run has one directed positive / one INCONCLUSIVE; the corrected
stdout/stderr repeat has two INCONCLUSIVE cases. See the
[paired evidence](../../evidence/runs/E2-ACCOUNT-DIRECTED.md). Repeatability is
not established across both directions and E2 stays partial. A third archived
campaign adds a second secondary-outbound positive witness with both log
streams retained; the primary-outbound case remains inconclusive. The total
is 2 positive witnesses / 4 INCONCLUSIVE outcomes. This trial depends on PRs #78/#79; their
stateless-worker calibration remains a distinct control. Software/lab docs are English.

## Fixed question and injected condition

Can two distinct actual ordinary AccountGrain activation IDs for key 2 have
overlapping complete incoming request envelopes while the original silo
processes are still running under a verified one-way network fault?

The accepted AccountGrain, SQL ledger, default placement and stock 120-second
schedule are unchanged. A **separate DirectedSilo incoming-call filter** holds
exactly the first secondary-hosted ordinary command for the existing contested
ID, source 2, target 1, amount 31. This delay is **before context.Invoke and
before the financial method/SQL**, with a 170s upper bound. The original
controlled identity-only placement is used; no financial placement hints,
stateless workers, reentrancy, lifecycle tuning or forged activation IDs are added.

The old call must emit a real gate marker before the stock fault clock starts.
After the exact one-way rule is installed, two bounded background workers
offer amount 37 through the original primary fixed-gateway client, at most
12 attempts each. Unique input files prevent concurrent payload overwrites.
Requests always reuse the same contested ID; timeouts remain ambiguous.

A passive monitor reads logs and actual original container/process identity.
It can release the old call only after a primary BEGIN for that same grain key
with a distinct activation/session is observed, neither original process has
been replaced/exited, and the held old call has no observed END/ERROR. The
original gate is always released at restoration/cleanup even if no witness
appears. Original helper containers retain the established passive lifecycle.

## Fixed acceptance and failures

Both directions run in fresh jobs. Retain all rules, native packet captures,
SQL/membership/liveness data, source/checkout hashes, runtime and image identity,
all client outcomes and complete logs before any old/new silo is removed.
No missing instrumentation, subprocess timeout or malformed output is success.

Require every stock long-schedule, recovery and seven-oracle SQL criterion,
plus all additional acknowledged probe payloads/results reconciled with SQL.
Positive status **PASS_DIRECTED_REQUEST_OVERLAP** additionally requires the
specific old/new witness calls to have complete successful filter results,
the same grain ID, distinct activation IDs, comparable kernel/time clocks and
a strict positive interval intersection. An incomplete old request or a new
activation only after old-process exit cannot substitute for that witness.

If the instrumented schedule and SQL gates pass but no live witness appears,
record **INCONCLUSIVE_NO_LIVE_OVERLAP** (exit 2), never relabel it PASS. Preserve
FAIL outcomes separately. Do not tune acceptance or change financial code to
force a positive result. Contract tests reject dead/recreated old nodes,
completed old calls, wrong keys, identical activation IDs and incomplete/errors.

## Interpretation boundary

The added filter delay changes request timing. A positive result would show
complete **directed incoming envelopes** on ordinary-grain activation IDs,
with authoritative SQL reconciliation. It would not be a natural unmodified
partition experiment, proof of globally Active lifecycle overlap, simultaneous
SQL execution, global exclusivity, physical HA, capacity or bank acceptance.
Each job uses one physical host. E2 stays partial and old evidence is unchanged.
If both cases are inconclusive, retain that result and keep #24 open; independent
sustained-capacity work under #25 may proceed without closing this gate.

## Local contract checks

```bash
python3 -m unittest discover -s lab/e2_account_directed -p test_probe_contract.py -v
```

The dedicated CI workflow runs mandatory language/book checks, publishes the
original client and separate host, then executes this exact preregistered
protocol. No book finding or release/tag is promoted by preparing source.

## Source regression versus an original campaign

PR checks always compile this host, run the adversarial witness contracts and
validate the paired book. A separate archive-audit workflow verifies the frozen
original ZIPs, including legitimate INCONCLUSIVE outcomes. New live 120s
campaigns use explicit workflow_dispatch. Documentation-only revisions do not
launch another original campaign. Manual invocation uses the same acceptance
criteria, bounded probes, raw reports and exit 2 for INCONCLUSIVE; nothing is
converted to PASS. Previously red original workflow conclusions remain red.
A skipped live matrix on a source-only PR is not a successful partition test.
