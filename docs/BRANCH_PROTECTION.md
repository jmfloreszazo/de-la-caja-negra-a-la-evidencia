# Protecting main: actionable ruleset configuration

**Status:** automation and documentation only. This repository currently reports **no active rulesets** from GitHub API `GET /repos/{owner}/{repo}/rulesets`. A passing GitHub Actions job **does not** enforce branch protection until the repository owner activates the ruleset.

## Unconditional status check

`.github/workflows/premerge.yml` triggers on **all pull requests**, push to `main`, and manual dispatch. It does **not** use `paths:` filters, unlike the optional Book and Lab workflows. The sole stable required job is called `premerge-gate`.

It validates:

1. Book/language policy, ES/EN parity, generated single-page books, source-level evidence links and figure provenance if installed.
2. Evidence claim statuses and reference consistency in **offline** mode, without implying online attestation.
3. Python-only baseline checks, reference data/accounting oracle, mainframe decomposition negative controls and brownfield candidate TODM/Golden Master gates.

It does **not** replace the full Book Mermaid/PDF render, native GnuCOBOL/.NET, Podman or online GitHub provenance audit. These remain task-specific CI and release gates.

## Owner action required to enforce (issue #16)

Open [Settings → Rules → Rulesets](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/settings/rules) and create an **Active** branch ruleset targeting exactly `main`:

- Block force pushes and branch deletion.
- Require pull request before merge, resolve conversations, and require the check **`premerge-gate`** from GitHub Actions (select it only after this PR has merged and the job is visible).
- No bypass for normal pushes. Allow normal merge commits to preserve source and original CI evidence.
- Do not require other workflows with `paths:` filters globally; a skipped required check can block unrelated PRs.
- With a single maintainer, requiring approvals from a distinct reviewer may block all PRs. Choose explicit review governance appropriate to available authorized reviewers; document the trade-off.
- Do not set **Lock branch**: that prohibits merges and is not equivalent to protected PR flow.

**Evidence required to close issue #16:** read back the `Active` ruleset via API, confirm the check is required, verify rejection of force-push/direct push without destructive testing, and run a documentation-only and lab-only PR to confirm `premerge-gate` appears. Screenshots or API response should preserve rule ID and target/ref. Without those checks, mark #16 **partially implemented**, not resolved.

## Reproduction

```bash
python3 scripts/check_language_policy.py --self-test
python3 scripts/check_language_policy.py
python3 scripts/check.py
python3 scripts/check_evidence.py
python3 lab/tools/verify_offline.py
```

No release or tag is modified by this workflow.
