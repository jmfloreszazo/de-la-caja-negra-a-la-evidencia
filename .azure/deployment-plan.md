# Azure demonstration deployment

> **Status:** Deployed · runner deallocated
> Infrastructure deployed 7 November and revalidated (no redeploy) 8 November 2026. All planned
> demonstrations have run; the runner is `PowerState/deallocated` and the VMSS has capacity 0.
> Disk, NAT, public IP and storage remain billable until the group is deleted by the author.

## 1. Project overview

Deploy the existing book experiment infrastructure and execute real synthetic
demonstrations, preserving original results and failures. Author:
Jose Maria Flores Zazo, jmfloreszazo.com.

The user explicitly authorized resource creation in Azure MVP Subscription -
Prod on 7 November 2026. No GitHub push, Actions, release, merge, or changes to
existing production resources are authorized by this deployment.

## 2. Requirements

- Subscription: `7a84bc78-1d1e-4294-a7c4-760dc607b5de`.
- Tenant: `f0eff2df-e4c1-4b90-870a-5f6ab6a6604b`.
- Resource region: North Europe. West Europe validation was rejected by Azure
  (`RequestDisallowedByAzure`, new customers not accepted); the failed attempt
  is retained. The resource-group metadata remains in West Europe.
- Classification: disposable development demonstrations, not production banking.
- Dedicated resource group: `rg-book-evidence-20261107`.
- Initial capacity: one D4s_v5 runner, zero VMSS workers, no managed PostgreSQL.
- Cost policy: minimize running time; deallocate the runner after evidence
  collection. A monthly alert of 100 subscription-currency units is a
  notification, not a spending cap. Disks, NAT and storage continue to cost money.
- Budget notification: authenticated operator `jmfloreszazo@outlook.com`.
- No public SSH endpoint; dedicated local SSH key and managed identities.
- SQL Server licensing and production capacity acceptance remain separate.

## 3. Components

Existing Bicep in `infra/experiments`, operator in `scripts/azure/lab.ps1`,
guest orchestration in `scripts/azure/remote-run.sh` and
`scripts/azure/run-experiment.sh`. Real local core/E1/E2/M2 executions have
passed; Azure execution remains unverified until deployed and run.

## 4. Recipe

Bicep with Azure CLI. Reuse existing infrastructure, not an azd migration.

## 5. Architecture

Private runner VM, zero-capacity Uniform VMSS, private subnets, inbound-deny
NSG, NAT egress/public IP, user-assigned managed identities, OAuth-only blob
storage and resource-group budget. Optional managed PostgreSQL stays disabled.
Fault fixtures run against dedicated disposable PostgreSQL containers.

## 6. Provisioning checks

- Authentication: interactive login succeeded; explicit subscription enabled.
- Dsv5 quota: 0 used / 65 vCPUs; requested 4.
- Regional compute quota: 0 used / 67 vCPUs; requested 4.
- VM quota: 0 used / 25000; requested 1.
- D4s_v5: no regional restrictions returned.
- Network: 0/100 public IPs, 0/1000 VNets, 0/5000 NSGs; one of each requested.
- NAT quota: 100; one requested. Storage: 0/250 accounts; one requested.
- Required Compute/Network/Storage/ManagedIdentity/Consumption providers registered.
- Dedicated empty group was absent and has now been created successfully.
- Operator has subscription Owner and permission to assign scoped roles.
- Effective policy assignment: Security Center built-in initiative; ARM policy
  evaluation remains part of validation. No exemption will be created.
- Remaining checks: ARM validation and WhatIf.
- North Europe fallback: ARM validation succeeded. Regional cores and Dsv5
  quotas both 0/65; network IPs 0/100, VNets 0/1000; storage 0/250.
- Review date: 2026-11-09; this is not an automatic deletion schedule.

## 7. Validation proof

- All validation checks pass: PASS for North Europe.
  - Core validation: CLI, authentication, Bicep build, ARM validate and WhatIf.
  - Azure Policy validation.
  - Run operator and guest regression controls.
  - Validate ARM deployment and inspect WhatIf for create-only changes.
  - Verify least-privilege storage role assignments and caller permissions.
  - Record exact commands and outputs under ignored local evidence storage.
- Prior local campaign: `evidence/runs/local-public-campaign-2026-11-07.json`.
- Real validation command:
  `validate-deployment.ps1 -Scope group -ResourceGroup rg-book-evidence-20261107
  -Subscription 7a84bc78-1d1e-4294-a7c4-760dc607b5de
  -Template infra/experiments/main.bicep
  -Parameters lab/results/azure-live-20261107/parameters.json`
  returned OVERALL PASS; WhatIf: 17 creates, zero modifications/deletions.
- `pwsh -NoProfile -File scripts/azure/lab.ps1 -Action Build`: PASS.
- `pwsh -NoProfile -File scripts/azure/test-lab.ps1`: PASS, 35 offline checks.
- `python3 -m unittest discover -s scripts/azure -p test_shell.py -v`:
  PASS, 22 controls under WSL.
- Static RBAC: runner identity reads only the source container and writes
  only the evidence container. Zero-capacity worker identity has no data
  roles until a worker workload requires them. Operator source/evidence
  data roles will be granted at container scope after deployment.
- Proof logs: `lab/results/azure-live-20261107/validation-1.log` (preserved
  regional rejection), `north-europe-validation.log`, `validation-2.log`.
- No guest experiment or deployment success is claimed yet.

### 8 November revalidation for the E1–E4 follow-up

- `validate-deployment.ps1 -Scope group -ResourceGroup rg-book-evidence-20261107
  -Subscription 7a84bc78-1d1e-4294-a7c4-760dc607b5de
  -Template infra/experiments/main.bicep
  -Parameters lab/results/azure-live-20261107/parameters.json`: OVERALL PASS.
  Original output: `lab/results/azure-e1-e4-20261108/validation.log`.
- The helper's displayed Create/Modify/Delete totals count property-level
  changes as well. The separately retained raw WhatIf has **0 resource creates,
  11 modifications, 0 resource deletes, 5 no-change and 1 ignored resource**.
  Its proposed defaults/budget/identity-expression deltas are not applied:
  this campaign reuses existing infrastructure, rather than redeploying it.
- `pwsh -NoProfile -File scripts/azure/lab.ps1 -Action Build
  -OutputDirectory lab/results/azure-e1-e4-20261108/build`: PASS.
- `python3 -m unittest discover -s scripts/azure -p test_shell.py -v`:
  PASS, 31 guest controls, including PostgreSQL startup/collection failures.
- `pwsh -NoProfile -File scripts/azure/test-lab.ps1`: PASS, 38 checks.
- Effective policy review includes inherited MFA requirements for writes and
  deletes, the West Europe restriction, and Security Center audit policies.
  No exemption or policy change is requested; North Europe ARM validation passed.
- Static roles rechecked: runner reads the source blob container and writes the
  evidence container; the zero-capacity workers perform no data operations.
  The existing guest uses managed identity, never an account key.
- This validates the infrastructure and existing launcher, not yet the new E3
  exploratory harness or Azure-hosted E4 candidate execution. Their tests and
  execution records must be added separately before claiming success.

## 8. Execution and verification

Deploy only after validation. Verify VM provisioning and cloud-init readiness,
grant the authenticated operator scoped evidence/source blob roles if required,
run core/E1/E2/M2 with exact source provenance, download and independently verify
evidence. Preserve failed attempts. Deallocate the runner after collection.
Never promote a single-VM smoke run to distributed E3 or live-agent E4 acceptance.

## 9. Actual outcome

- Deployment `book-experiments`: Succeeded in North Europe.
- Bootstrap verified in the guest: .NET 10.0.100, Python 3.12.3, Podman 4.9.3,
  GnuCOBOL 3.1.2.0.
- Runner and operator container-scoped blob roles verified in live Azure.
- Core, E1, extended E2 and M2 executed successfully; original archives
  downloaded and verified. Core databases independently audited off-VM.
- First M2 run retained inaccurate inherited host labels; a separate full
  repeat passed with corrected Azure and source-archive provenance.
- Runner final state: `PowerState/deallocated`. VMSS capacity 0, actual instances
  `[]`. No compute left running by this campaign. Disk/NAT/IP/storage remain.
- Full observations: `evidence/runs/azure-single-vm-2026-11-07.json`.
- No GitHub push, Actions, version bump, release or merge occurred.
- E3 distributed capacity, mainframe comparison and live-agent E4 remain open.

## 10. Separate follow-up demonstrations

- One existing Foundry model invocation generated a C# candidate and 16 tests;
  local isolated evaluation passed 58 frozen cases and known-mutant controls.
  See `evidence/runs/e4-live-builder-2026-11-08.json`. This did not modify the
  Foundry deployment or measure human review cost.
- The same runner was started for M1, then deallocated again after the original
  evidence was downloaded. Two concurrency profiles passed, 20,000 measured
  loopback responses, zero response errors. No database was started for M1.
- Final state is retained under `lab/results/azure-m1-20261108/deployment`.
  The first deallocation call was refused by the operator's interruption guard;
  the acknowledged retry succeeded after workload completion and evidence download.
- E3 readiness returned `INCONCLUSIVE / BLOCK` with the original contract
  unchanged. No on-premises/mainframe capacity measurement is implied.

## 11. Executed E1–E4 and TODM follow-up, 8 November

- Existing infrastructure reused, not redeployed. E1 repeated 960-transfer
  parity; extended E2 repeated both membership providers and 600 workload
  transfers with independent SQL checks.
- Exploratory E3 offered 720 operations across fixed 20/40/60 per-second phases:
  668 committed, 48 connection failures and four missed schedules. A killed
  service process was restarted and committed again. Accounting and negative
  controls passed; no distributed capacity acceptance is inferred.
- E4 replay ran as UID 1000 with rootless Podman on the Azure runner: 16 own
  tests, 58 frozen cases, three rejected mutants and three denied protected
  writes. This reused the original model response, with no new inference.
- The initial E4 root-private-working-directory failure remains archived;
  a fresh accessible-directory retry passed. User-manager lingering and the
  pinned rootless image cache remain on the isolated VM.
- TODM rejected an incomplete E3 runtime inventory. Sixteen original runtime
  artifacts were retrieved from the preserved Azure build tree and matched
  their recorded hashes. No rebuilt substitute or overwritten evidence was used.
- The complete portable TODM bundle was replayed on Azure: all four bounded
  technical evaluations passed, eight actual-input negative controls and twelve
  synthetic upstream mandate cases passed. Methodology remains INCONCLUSIVE;
  release remains BLOCK. The first qualification command's unsupported output
  path failure is retained separately from the successful in-root retry.
- Evidence: `evidence/runs/azure-e1-e4-2026-11-08.json` and
  `evidence/runs/todm-azure-2026-11-08.json`.
- Final status after all downloads: runner `PowerState/deallocated`, VMSS
  capacity 0. Disk/NAT/IP/storage still incur charges. No GitHub Actions,
  release, merge or production acceptance was performed by this campaign.
