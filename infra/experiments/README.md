# Azure experiment infrastructure

Local Bicep and PowerShell entrypoints for the book's experimental work. No
GitHub workflow is added or dispatched. No source, oracle, threshold, edition
number or E1-E4 evidence status is changed by a deployment.

The [first real Azure execution](../../evidence/runs/azure-single-vm-2026-11-07.json)
deployed this infrastructure in North Europe and passed core, E1, extended E2
and all 20 M2 cases. The original West Europe eligibility rejection and the
first M2 attempt's inherited provenance-label problem are retained separately.
The runner was deallocated after evidence download; VMSS capacity remained
zero. This is verified single-VM execution, not distributed E3 or live E4.

## What this implements

- Ubuntu 24.04 runner VM, private NIC and no public SSH endpoint.
- An independent Uniform VM Scale Set with explicit capacities **0/1/2/4/8/16**.
  Workers do not share the runner's CPU. VM instances are not proof of
  independent physical hosts; capture actual placement before fault claims.
- Separate runner, worker and delegated database subnets; outbound NAT for
  package installation, Azure authentication and artifact access.
- Optional private PostgreSQL 16 Flexible Server with **Entra-only**
  authentication and opt-in same-zone or zone-redundant HA.
- OAuth-only Blob Storage: source inputs and evidence in separate private
  containers, versioning and 30-day soft deletion. The authenticated storage
  endpoint is publicly reachable so an authorized local operator can upload
  sources without a VPN. It is not a private-endpoint-only storage design.
- Runner identity has source-container read access and evidence-container write
  access, not subscription Contributor. Worker identity has no data roles yet.
- Monthly actual/forecast budget notifications. **An alert is not a spending
  cap**, and the expiration tag does not automatically delete anything.
- Root-only cloud-init bootstrap, pinned .NET SDK 10.0.100, Podman, Python,
  GnuCOBOL and Azure CLI. Package versions and the installer hash are recorded.

## Execution boundary

| Entry point | Runs on the Azure runner | What it does not establish |
|---|---|---|
| `core` | Existing COBOL/.NET/SQLite walkthrough and bank controls | Mainframe equivalence or cloud capacity |
| `e1` | PostgreSQL, .NET differential, SQLite parity, oracle vectors and multiprocess parity | SQL Server, managed-database equivalence, HA or power-loss durability |
| `e2` | Existing Orleans synthetic functional/parity harness | Multi-VM silos, stable saturation or automatic recovery |
| `e2-cluster` | Two silo processes, both membership providers and pre/post-COMMIT process failures | Physical-node HA or a production recovery SLA |
| `e1-sqlserver` | Consent-gated SQL Server core and worker suites; not executed in this Azure campaign | SQL Server license consent, HA or capacity acceptance |
| `m1` | REST/gRPC transport-only loopback profiles at concurrency 8 and 32, with independent response checks | Ledger throughput, TLS, WAN or distributed E3 capacity |
| `m2` | Existing 20 REST/gRPC trials with independent SQL oracles | Distributed replicas, TLS or open-loop cloud benchmark |
| `e3` | Exploratory open-loop ledger trial: preregistered synthetic rates, one service process killed and restarted, every offer outcome recorded, independent SQL reconciliation | An approved capacity contract, sustained capacity ceiling, physical-node HA, mainframe or on-premises comparison |
| `e4-replay` | Isolated evaluation of a **recorded** model response under rootless Podman: self-tests, 58 frozen cases, mutation qualification, protected-write denial | A new model inference, a comparative agent population, human-review time or cost |

These are **Azure-hosted single-VM synthetic smoke runs**, using a disposable
loopback-only PostgreSQL container. Scaling the VMSS creates machines, **not
application replicas**. The managed database is provisioned for a subsequent
distributed adapter; these destructive local harnesses never silently point
at it. E4 agent isolation is not implemented by placing an agent on this
root-capable runner.

The [E1-E4 roadmap](../../docs/EXPERIMENT_ROADMAP.md) remains authoritative.
E3 still needs a filled and approved performance contract, services on the
worker nodes, shared durable ledger, equivalent TLS for REST/gRPC, open-loop
load from the separate runner, uniform/hot keys, N-1 recovery, independent
persisted-state audit and dated cost per committed transfer. On-premises,
hybrid and banking WAN measurements are separate requirements. Neither a
successful Bicep build nor a green smoke run promotes an evidence claim.

## Validate locally, without Azure resources

Requirements: PowerShell 7.4+, Git, Azure CLI with Bicep installed; Bash for shell
syntax checks. Run from the repository root:

```powershell
pwsh -NoProfile -File scripts/azure/lab.ps1 -Action Build
pwsh -NoProfile -File scripts/azure/test-lab.ps1
```

```bash
bash -n scripts/azure/remote-run.sh
bash -n scripts/azure/run-experiment.sh
python3 -m unittest discover -s scripts/azure -p test_shell.py -v
```

The default action is **Build**. It compiles locally into ignored
`lab/results/azure/main.json`. Parameter placeholders are intentionally invalid
for deployment. Offline checks are not ARM validation, a quota reservation or
an executed Azure run.

## Choose context and budget before deploying

1. Choose a subscription, region and dedicated disposable resource group.
   The deployer needs resource creation and role-assignment permissions.
   Register Compute, Network, Storage, ManagedIdentity, Consumption and,
   if enabled, DBforPostgreSQL providers.
2. Check regional availability and vCPU quota for the runner **plus** the
   largest intended worker count. At `Standard_D4s_v5`, runner + 16 workers
   requests 68 vCPUs; this is arithmetic, not available capacity.
3. Check current prices for compute, disks, NAT, its public egress IP, storage,
   traffic, and optional PostgreSQL/HA. Budget amounts use the subscription's
   billing currency, not an assumed EUR/USD currency.
4. Copy `example.parameters.json` outside tracked source. Set a public SSH
   key, future review date, real budget email and approved alert amount.
   Choose supported `workerZones` if testing zones. Select a resolved Ubuntu
   image version for a controlled campaign instead of the default `latest`.
5. To enable PostgreSQL, set `enableManagedPostgres=true` and supply
   `databaseAdminObjectId`, `databaseAdminName` and `databaseAdminType`.
   Review its separate SKU/HA costs and Entra database-role setup. No database
   password or application identity privilege is manufactured automatically.

Example operator variables; replace all values before executing:

```powershell
$subscription = '<subscription-guid>'
$group = 'booklab-experiments'
$region = '<approved-region>'
$parameters = '<absolute-path-to-completed-parameters.json>'
```

`WhatIf` requires an existing group tagged `purpose=book-experiments`.
Creating that empty dedicated group is an explicit operator action:

```powershell
az group create --subscription $subscription --name $group --location $region `
  --tags purpose=book-experiments owner=jmfloreszazo.com
pwsh -File scripts/azure/lab.ps1 -Action WhatIf -SubscriptionId $subscription `
  -ResourceGroup $group -ParametersFile $parameters
pwsh -File scripts/azure/lab.ps1 -Action Deploy -SubscriptionId $subscription `
  -ResourceGroup $group -Location $region -ParametersFile $parameters -Apply
```

`Deploy` can also create the dedicated group, runs WhatIf, and persists the ARM
response. **`-Apply` is explicit approval of the deployment and its costs**;
WhatIf is not an interactive approval gate. Use the separate WhatIf command
first. Existing groups without the purpose tag are rejected. Default worker
count is zero and managed PostgreSQL is disabled, but the runner, disks and
network still cost money.

Provisioning success is not guest readiness: `Run` waits for cloud-init and
requires its completion marker. Use Azure Run Command/boot diagnostics for
bootstrap errors; no public management port is opened.

## Scale deliberately

```powershell
pwsh -File scripts/azure/lab.ps1 -Action Scale -SubscriptionId $subscription `
  -ResourceGroup $group -Capacity 2 -Apply
pwsh -File scripts/azure/lab.ps1 -Action Status -SubscriptionId $subscription `
  -ResourceGroup $group
```

Repeat with 1, 2, 4, 8 or 16 only after workload readiness and quota/cost checks.
Do not silently enable CPU autoscaling during fixed-replica experiments.
Scale records include instance provisioning information, not an application
readiness verdict. Changing the VMSS model does not update existing guests
under its manual upgrade policy. Redeploying the template applies the
`workerCount` in the parameter file; keep it synchronized with the intended
capacity and inspect WhatIf for unintended scale-in.
`Deploy`, like `Scale`, refuses a capacity reduction without `-AllowScaleIn`.
It also rejects changing the prefix when another scale set exists in the group.

Scale-in deletes instances and local state. Stop work and export evidence first:

```powershell
pwsh -File scripts/azure/lab.ps1 -Action Scale -SubscriptionId $subscription `
  -ResourceGroup $group -Capacity 0 -Apply -AllowScaleIn
```

## Run existing experiments and retain evidence

The interactive operator also needs **Storage Blob Data Contributor** on the
`source` container and **Storage Blob Data Reader** on the `evidence` container.
Azure management-plane Contributor alone does not grant those data permissions.
Grant these roles explicitly to the operator's Entra object ID with
`az role assignment create --assignee-object-id ... --assignee-principal-type User
--role ... --scope <container-resource-id>` (use the actual principal type).
Allow RBAC propagation before a run; authentication failures stop execution.

`Run` exports **committed HEAD** with `git archive`; tracked lab edits are
rejected until committed locally. No push is needed. Untracked files, local
settings, credentials and installed dependencies are not uploaded. The archive
SHA-256 and exact local launcher hash are recorded separately. Do not commit
secrets. The exported snapshot must already contain the chosen lab.

For explicitly authorized local, unpublished lab edits, `-IncludeWorkingTree`
exports a source-only snapshot without committing or pushing. It includes
tracked and non-ignored untracked lab files plus the experiment launcher and
root .NET build configuration. Review these inputs before upload. The base
commit, dirty status, every source hash and archive hash are retained in the
local run directory; guest reports distinguish the archive from a committed
release. This mode requires Python 3.11+ available as `python` on the operator.
No Git credentials, Git metadata or ignored results are exported.

WhatIf uses `--no-pretty-print` so Azure CLI returns machine-readable JSON;
its default human-readable output is not parsed as deployment evidence.

```powershell
pwsh -File scripts/azure/lab.ps1 -Action Run -SubscriptionId $subscription `
  -ResourceGroup $group -Experiment e1 -RunId e1-azure-001 -Apply
pwsh -File scripts/azure/lab.ps1 -Action Download -SubscriptionId $subscription `
  -ResourceGroup $group -RunId e1-azure-001
```

Use `core`, `e1`, `e1-sqlserver`, `e2`, `e2-cluster`, `e3`, `e4-replay`, `m1` or `m2`.
Only one run owns a runner at a time. Each database run has
a fresh source tree and disposable database; the shell owns and removes only
its uniquely named database container. SQL destructive controls never target
the managed PostgreSQL server. The workload is limited to 60 minutes.

For PostgreSQL runs, creation and startup are separate: cleanup is armed before
startup and addresses the full owned container ID, never a reused name. Startup
and readiness probes are bounded. The launcher retains readiness output, database
logs, dump diagnostics and `postgres-completion.json` with separate workload,
log, dump and cleanup exit codes. A skipped dump is `null`, not success.
After readiness, collection is attempted even when the workload fails. Log
collection, dump or removal failure cannot produce a successful launch; the
original workload failure takes precedence when multiple phases fail.

On exit, logs have a 10-second limit, the dump 30 seconds and removal 10 seconds,
each with a 2-second kill grace. This fits inside the remote supervisor's
60-second termination grace. A timed-out dump is retained as partial evidence,
not a restorable backup claim, and removal is still attempted. If the engine
cannot remove its container, the nonzero exit, full ID and diagnostics require
operator follow-up. No launcher can promise cleanup after host power loss or
an immediate supervisor kill.

### E3 exploratory load and E4 isolated replay

`-Experiment e3` runs the [open-loop exploratory harness](../../lab/e3_capacity/README.md)
against its own schema in the disposable PostgreSQL fixture. It records each
scheduled offer, failed/missed/ambiguous outcomes, actual process kill/restart,
persisted operation reconciliation and independent accounting checks. Its fixed
synthetic rates are not approved capacity targets. All processes still share
one VM; no TLS/WAN, managed-database failover or physical-node HA is claimed.
The private schema is removed after its JSON ledger snapshot is collected;
the launcher's final database dump is not a replacement for that snapshot.

`-Experiment e4-replay` evaluates a **recorded real model response** on the Azure
runner without another model invocation. Both input directories are explicit:

```powershell
pwsh -File scripts/azure/lab.ps1 -Action Run -SubscriptionId $subscription `
  -ResourceGroup $group -Experiment e4-replay -RunId e4-replay-azure-001 `
  -E4AttemptDirectory '<recorded-model-attempt>' `
  -E4LegacyResults '<verified-core-results>' -IncludeWorkingTree -Apply
```

Only five allowlisted JSON files are packed: model request/response/candidate,
legacy summary and observations. Candidate/response equality and usage are
checked before upload; a separate digest binds the replay inputs. Unexpected
archive members, links and oversized inputs are rejected before extraction.
The actual frozen contract/source hashes are checked again by the evaluator.

The root supervisor starts the `laboperator` user manager and enables lingering
for rootless Podman. It copies readable sources/inputs to a fresh temporary
working directory, but keeps protected sources root-owned. Only result folders
are owned by the nonroot user. A clean user environment contains no Azure token;
the pinned SDK image is pulled into the user's Podman store only if missing.
Qualification and evaluation enforce no network, read-only root filesystem,
nonroot keep-id mapping and bounded CPU/memory/PIDs. Credentials and the container
socket are never mounted into the candidate. Kernel isolation is not certified.

Evidence includes user/engine/image metadata, attempted protected writes,
mutation controls, self-tests, external gate findings and original model usage.
Azure instance metadata plus the request/source/input archive hashes establish
cloud placement externally; an evaluator's host label alone does not.
`e4-replay` must not be counted as another live-model run. If result collection
fails, the temporary original remains for recovery rather than being deleted.
The rootless SDK cache and lingering user manager persist on this isolated
runner; VM deallocation stops their compute usage without deleting evidence.

`e1-sqlserver` runs the existing SQL Server 2022 Developer core and persistent
worker-parity suites, not PostgreSQL. Read the
[SQL Server lab requirements and license conditions](../../lab/e1_sqlserver/README.md)
first. Both license acceptance and Azure workload approval are explicit:

```powershell
pwsh -File scripts/azure/lab.ps1 -Action Run -SubscriptionId $subscription `
  -ResourceGroup $group -Experiment e1-sqlserver -RunId e1c-azure-001 `
  -AcceptSqlServerLicense -Apply
```

No license consent is inferred from `-Apply`. A missing consent flag is
rejected before contacting Azure. `-SqlServerImage` accepts an official
SQL Server 2022 tag or repository digest; the runtime additionally checks
server major version 16. The 4-GiB container uses a generated throwaway
password and a random loopback port. Logs, a final JSON table snapshot and
a checksummed `E1SqlLab` backup are collected before the owned container is
removed by immutable ID, including after a failed test. Backup or cleanup
failure cannot produce success. If startup fails before readiness, logs and
exit codes are retained but no database backup can be promised.

This new launcher mode is offline-regression-tested only; a real run still
requires license acceptance. It is not new Azure, SQL Server or E1 acceptance
evidence. Historical SQL Server CI observations remain separate and unchanged.

`e2` retains the short co-located functional suite. `e2-cluster` additionally
runs real deadlocks, fixed workloads, process crashes, two-silo tests with both
development and ADO.NET membership, and pre/post-COMMIT in-flight kills. These
are separate OS processes on one host, not physical-node HA or E2 acceptance.
The vendor membership installer verifies pinned upstream Git blob hashes. It
accepts the launcher's unique container only after checking its experiment
label, database name, running state and loopback port binding, then addresses
that container by its full immutable ID.

Input/output blobs cannot be overwritten by the operator commands. Failures
are uploaded as evidence too when authentication/storage remain available.
The run archive contains raw execution logs, existing harness results,
PostgreSQL logs and dump, Azure instance metadata, package/runtime provenance
and workload/artifact exit codes. A missing completion marker, guest failure,
collection failure or upload failure is an error, even if Azure CLI reports
management-plane success. If upload fails, preserve the local Run Command
response and recover the run directory from the VM before deallocation.

The PostgreSQL default tag is mutable; record its resolved digest and use
`-PostgresImage docker.io/library/postgres@sha256:<recorded-digest>` for a replay.
The Ubuntu image, native repositories and bootstrap installer also require
version/hash review for strict replay. This preparation does not claim
bit-identical environments from mutable upstream packages.

For local Linux/WSL verification of the same launcher, explicitly set
`CONTAINER_ENGINE=docker` when Docker is available instead of Podman. Both
paths record the engine version and image repository digest. This does not
change the Azure bootstrap's default Podman runtime or turn local execution
into Azure evidence.

Use a fresh disposable source checkout for each local run: existing harnesses
write under `lab/results/e1`, `lab/results/e2` or `lab/results/m2`. Install the
documented .NET 10 SDK and Python/venv prerequisites first (plus GnuCOBOL for
`core`). From that checkout's root, for example:

```bash
CONTAINER_ENGINE=docker bash scripts/azure/run-experiment.sh m2 \
  "$PWD/lab/results/local-m2/evidence"
```

Keep the source commit and any local source patch, launcher, console output,
`lab/results/m2` and the supplied evidence directory together. The dump contains
the final database state; each matrix case has its own independent oracle
result. Do not mix local metrics with the historical CI series or promote them
to distributed capacity evidence.

Evidence includes private topology metadata: keep it in access-controlled
storage and ignored local results, not in public commits. Blob versioning is
not WORM storage or an E4 authorization boundary; the runner can write evidence.

## Pause and retire

```powershell
pwsh -File scripts/azure/lab.ps1 -Action Deallocate -SubscriptionId $subscription `
  -ResourceGroup $group -Apply -AllowScaleIn
pwsh -File scripts/azure/lab.ps1 -Action Start -SubscriptionId $subscription `
  -ResourceGroup $group -Apply
```

Deallocation still charges for disks, NAT, its public IP, storage and optional
PostgreSQL. Scaling workers to zero does not stop the runner or database.
There is deliberately no unattended deletion command. Export and verify the
evidence, obtain approval, then remove only the dedicated resource group.
Review the expiration tag and budget alerts; neither enforces shutdown.

## References

- [VM Scale Sets Bicep reference](https://learn.microsoft.com/azure/templates/microsoft.compute/virtualmachinescalesets)
- [PostgreSQL Flexible Server Bicep reference](https://learn.microsoft.com/azure/templates/microsoft.dbforpostgresql/2024-08-01/flexibleservers)
- [Linux VM Run Command limitations](https://learn.microsoft.com/azure/virtual-machines/linux/run-command)
- [Azure budget behavior](https://learn.microsoft.com/azure/cost-management-billing/costs/tutorial-acm-create-budgets)
