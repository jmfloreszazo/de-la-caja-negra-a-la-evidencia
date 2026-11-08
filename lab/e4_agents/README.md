# E4: isolation qualification and live builder pilot

The `qualify.py` prerequisite is **not a live-agent experiment and does not complete E4**. It verifies
the execution boundary needed before submitting model-generated candidates.
No model endpoint is called and no human-review time or model cost is invented.

The supervisor runs as a non-root Linux/WSL user. Candidate execution receives
only its disposable writable directory, not the reference cases, verifier,
repository, credentials or Docker socket. Containers have no network, a
read-only root filesystem, dropped capabilities, no new privileges and bounded
CPU, memory and process counts. Runtime temporary storage is a bounded tmpfs;
disposable build storage is confined to the output directory. Containers share
the host kernel: do not claim a kernel-exploit
security boundary.

A separate probe actually attempts writes to the original contract, verifier
and root filesystem while mounted read-only. Those writes must fail and a
candidate-directory write must succeed. Original protected files are hashed
before and after the entire run. The independent gate runs separately, with
only read-only inputs. Its authority remains **DEMO_ONLY / SIMULATED_ALLOW**.

## Reproduce

First execute the existing real COBOL/.NET fee laboratory and retain its
`summary.json` and `none-observations.json`. The qualifier requires these
observations and checks their contract/source hashes; it never substitutes
expected answers for a claimed COBOL execution.

On Linux/WSL, with Docker available:

```bash
docker pull mcr.microsoft.com/dotnet/sdk@sha256:c7445f141c04f1a6b454181bd098dcfa606c61ba0bd213d0a702489e5bd4cd71
python3 lab/e4_agents/qualify.py \
  --legacy-results /path/to/verified/lab/results \
  --output /path/to/new/e4-qualification
```

The output directory must not already exist. Docker is the locally verified
engine and remains the default for both `qualify.py` and `live.py evaluate`.
`--engine podman` uses rootless `--userns keep-id` so the supervisor's non-root
UID can write its disposable bind mounts. Automatic read-only tmpfs mounts and
host proxy-variable forwarding are disabled. Podman 4.9.3 expands `CapDrop`
into individual capability names; the evaluator checks the actual empty
`EffectiveCaps` and `BoundingCaps` sets instead of requiring Docker's `ALL`
marker. Missing capability fields fail closed (explicit JSON null represents
an empty Go slice). Bind sources, destinations and permissions must match
exactly; extra mounts, including volumes or credential/socket mounts, fail.
CPU, memory, PID, network and root-filesystem checks are not relaxed.
Podman compatibility has synthetic regression coverage, but requires an actual
runner execution before claiming Azure or Podman qualification. Record the actual
engine and image inspection produced by your run. The pinned
image contains SDK 10.0.100. Restore uses an empty package-source configuration
and disabled networking; both projects depend only on the bundled framework.

The known-good reference candidate must pass all frozen cases. The three
existing deterministic mutants (`round-even`, `wrong-threshold`,
`approve-inactive`) must fail the external gate. This qualifies those specific
negative controls, not arbitrary future defects.

The supervisor checks the requested isolation settings before starting each
container and again after execution. It retains its exact source, image
inspection, commands, container configurations, stdout/stderr and the source
hashes of reused observations. Timeouts retain partial logs; cleanup failures
are errors, not successful qualification. This harness runs only the known
reference sources and mutants, not arbitrary untrusted model-generated code.

Run the synthetic regression controls separately:

```bash
python3 -m unittest discover -s lab/e4_agents -p test_qualify.py -v
```

### Exported trees and the Azure Linux runner

A source tree without `.git` requires **all three** launcher-provided variables:
`SOURCE_HEAD_SHA` (40 hexadecimal digits), `SOURCE_ARCHIVE_SHA256` (64
hexadecimal digits), and `SOURCE_WORKTREE_DIRTY` (`true`, `false`, `0`, or `1`).
Partial, malformed or missing export metadata is rejected before creating an
output directory. The launcher must hash the exact archive it transferred and
capture the source commit and dirty state when creating that archive. Do not
invent values or use a clean commit hash to imply the exported worktree was clean.

These values are recorded as `launcher-attested-export`, **not** as an archive
hash independently verified by the evaluator. The extracted tree alone cannot
reconstruct the original archive bytes. With `.git`, actual Git commit/dirty
state is used; conflicting supplied metadata is rejected. Neither source
metadata nor an Azure model endpoint proves that candidate execution was in
Azure. Reports include observed supervisor OS/kernel, hostname, architecture,
Python, UID/GID, and raw `engine-info.json` plus engine version/image inspection.
`executionLocation` stays `unverified`; use the launcher/resource evidence to
establish cloud location, and distinguish supervisor and engine hosts.

From the exported source root, as `laboperator` (not root), with the launcher
variables already exported and the pinned image already present. The two input
folders below are **not in the repository**: `<attempt>` is the recorded model
attempt (`attempt-01/` inside `e4-live-builder-2026-11-08.zip`) and `<legacy>` is
a verified core run's `results/` folder (for example from
`azure-single-vm-2026-11-07.zip`). Archive names and digests are listed in
[`docs/DIST_MANIFEST.md`](../../docs/DIST_MANIFEST.md). Any fresh `core` run from
`scripts/azure/run-experiment.sh core <dir>` also yields a valid `<legacy>`.

```bash
: "${SOURCE_HEAD_SHA:?launcher source commit required}"
: "${SOURCE_ARCHIVE_SHA256:?launcher archive digest required}"
: "${SOURCE_WORKTREE_DIRTY:?launcher dirty state required}"
python3 lab/e4_agents/live.py evaluate --engine podman \
  --attempt <attempt> \
  --legacy-results <legacy> \
  --output lab/results/e4-podman-replay
python3 lab/e4_agents/qualify.py --engine podman \
  --legacy-results <legacy> \
  --output lab/results/e4-podman-qualification
```

On the Azure runner this is wrapped by `scripts/azure/run-e4-replay.sh`, which
receives both inputs from the operator's digest-bound `e4-inputs.tar`.

Both output directories must be new. Disposable build directories are created
under the output directory and removed after execution. Evaluation only replays
the retained candidate; it never requests a model. Model authentication and
inference remain exclusively in the separate supervisor `request` command.

Rootless Podman requires subordinate UID/GID mappings, a usable user namespace,
and delegated cgroup controllers capable of enforcing the requested CPU,
memory and PID limits (normally cgroup v2). The output directory and all bind
inputs must be accessible to `laboperator`. Missing controllers/mappings,
permission or SELinux denials, unavailable images, or incompatible inspection
metadata are blockers, not reasons to run privileged, use host networking,
remove limits, relabel protected inputs, or expose credentials. No fallback to
rootful Docker/Podman is performed. Container boundaries still share a kernel.

## Remaining E4 work

The [recorded local qualification](../../evidence/runs/local-e4-qualification-2026-11-07.json)
passed 58 cases for the reference candidate and rejected all three known
mutants. All three protected writes were denied, the candidate write succeeded,
and protected hashes were unchanged. Thirteen regression controls passed.
Full logs and configurations remain in the local archive identified by that
summary; they have not been uploaded to GitHub.

Live model requests, prompts, tool access, token/cost budgets and every attempt
must still be recorded. Compare agent-written tests against the independent
oracle and mutation-qualified oracle at task level. Measure accepted defects,
false blocks and actual human review time. An authenticated model, review
process and budget are prerequisites; a successful qualification is not an
agent success rate or release approval.

## Live Azure builder pilot

`live.py` adds a separate, bounded model-driven workflow. It sends only a
synthetic public fee contract, never repository sources, reserved cases,
credentials or verifier output. The model supplies C# source and its own test
vectors. The supervisor compiles and executes the candidate in the same pinned,
network-disabled, non-root container boundary. Build output is bounded and the
candidate receives no Docker socket or model credential. A container is not a
kernel-exploit security boundary.

Authenticate Azure CLI with an identity authorized to invoke your existing
deployment. The request command runs on Windows or Linux; evaluation requires
non-root Linux/WSL with Docker (default) or explicitly selected Podman and the
already-pulled pinned SDK image.

```bash
python3 lab/e4_agents/live.py request \
  --endpoint https://YOUR-ACCOUNT.cognitiveservices.azure.com \
  --model YOUR-DEPLOYMENT --subscription YOUR-SUBSCRIPTION \
  --output lab/results/e4-pilot/attempt-01
python3 lab/e4_agents/live.py evaluate \
  --attempt lab/results/e4-pilot/attempt-01 \
  --legacy-results /path/to/verified/core/results
```

In Windows PowerShell, use `python` for the request command and run evaluation
with `wsl -- python3`. The token stays in supervisor memory; it is not written
into the request, response, container environment or archive. Endpoint redirects
are forbidden. HTTP errors retain their response and fail the command.

For a repair, create a new output directory and pass `--previous` pointing to
the preceding attempt. Only the model's previous source/tests and its own
build/test feedback are supplied, not the independent gate findings. There
are at most three requests per chain, each capped at 4,000 completion tokens.
No automatic HTTP retry spends additional tokens. A new endpoint or model
requires a separate condition. Do not select only successful chains for reports.

The [first recorded live pilot](../../evidence/runs/e4-live-builder-2026-11-08.json)
used one actual Azure request, generated 16 tests, and passed all 58 frozen
cases. Its test suite accepted the reference and rejected all three known
mutants. The separate independent gate qualification also passed. A second
local evaluation reused the exact response; it was **not a second model run**.
The response reported 269 input and 2,279 completion tokens, 2,548 total.
Those are observed usage counts, not invoiced cost.

The model was hosted in Azure; candidate execution was local WSL/Docker.
This is a fixed supervisor workflow, not an autonomous tool-selecting agent or
a full E4 comparative study. One successful task is not a population success
rate. Human review time and cost per accepted change remain unmeasured.
Original deterministic qualification archives still correctly record zero
live calls in those earlier campaigns.

```bash
python3 -m unittest discover -s lab/e4_agents -p 'test_*.py' -v
```
