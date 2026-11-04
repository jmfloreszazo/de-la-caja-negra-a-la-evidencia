# Full-lab host reproduction protocol

Tracks #11. This protocol prepares a reviewable run on a named host; it does not label an unexecuted platform as supported. The Linux container executes the synthetic COBOL/.NET/SQLite walkthrough, including its in-memory capability example. It does not run every PostgreSQL/Orleans/channel experiment in this repository. The existing financial implementations and accounting oracle remain unchanged.

## What counts as a result

| Result | Meaning |
| --- | --- |
| `INCONCLUSIVE`, exit 2 | Podman is absent or the selected engine cannot be queried; no lab PASS |
| `READY`, exit 0 | Preflight reached the engine; the lab was not executed |
| `FAIL`, exit 1 | Execution, timeout, provenance or independent output verification failed |
| `PASS`, exit 0 | The complete named synthetic walkthrough and host-side audit passed on this recorded host/engine/image |

A successful unit test or the Python codec exercise from #88 is not a full container reproduction. The collector's tests run on three hosted operating systems; the dedicated execution job runs the container on Linux only. macOS/Podman-machine and Windows/WSL2 full runs remain external validation until their original reports exist.

## Prepare the exact checkout and engine

Use a clean clone at an explicitly recorded commit. Untracked files in the repository also block execution; generated ignored results are allowed. Keep the clone/output in a host directory shared with the selected Podman engine. The collector does not install Podman, create/start a VM, select a connection, change rootless/rootful settings or reset an existing machine.

| Host | Preparation and topology to record |
| --- | --- |
| Linux | Install Podman and verify `podman info`. Record native versus VM/remote execution; rootless versus rootful is in the engine-host log. |
| macOS | Install Podman using its official instructions, initialize/start a machine if needed, then record the selected provider, architecture, VM resources and host-directory sharing. |
| Windows/WSL2 | From PowerShell, retain `wsl --version` and `wsl -l -v`; use a WSL2 distribution with a working Podman engine and clone into its Linux home directory. Run Python inside that distribution; the report host is Linux/WSL, not native Windows. |
| Windows native client | A separate optional variant: initialize/start a supported Podman machine and run the collector with Windows Python. Record its selected provider and shares. This does not substitute for the WSL2 variant. |

Podman documents that macOS/Windows clients require a Linux VM; provider availability depends on the installed version. GitHub documents a nested-virtualization limitation for its arm64 macOS runners. These are reasons to use a suitable local/dedicated host for this VM test, not proof that every Actions topology is incapable. Actions can orchestrate an independently provisioned host. No VM was attempted merely by running collector unit tests.

Primary sources, consulted 4 November 2026:

- [Podman machine](https://docs.podman.io/en/stable/markdown/podman-machine.1.html).
- [Podman run and volume options](https://docs.podman.io/en/stable/markdown/podman-run.1.html). Remote engine paths/shares must be checked explicitly.
- [GitHub-hosted runners reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), arm64 macOS limitations. These moving documentation pages do not establish the user's installed product versions.

## Execute one fresh attempt

From the repository root on Linux/macOS/WSL2:

```bash
git rev-parse HEAD
git status --short
python3 lab/tools/reproduce_host.py
python3 lab/tools/reproduce_host.py --execute
```

With Windows Python, use `python` in place of `python3`. Each invocation creates a new directory under `lab/results/host-reproduction/`; it prints the report path. A preflight and an execution are separate attempts. `--output` can select a new path; an existing directory is refused so a failed attempt is never overwritten. Keep output outside the repository or under the ignored results directory.

Build requires network for the base image, packages and restore. The actual walkthrough runs with `--network=none`. The collector builds a uniquely tagged image, records its content-addressed image ID and architecture, runs that ID, and mounts only the fresh output directory at `/work/results`. It records command arguments, exit codes, timeouts and separate raw stdout/stderr files. Cleanup targets only its own uniquely named container; the image stays available for review. The base tag and package feeds remain mutable: retain the build log and image identity; this is not a bit-reproducible build or an SBOM. No timing result should be compared as a cross-host capacity benchmark.

## Independent acceptance and evidence

The host-side audit reads 58 raw COBOL/candidate observations against the fixed expected contract; it checks all ten gate verdict/exit/release combinations, including `PASS` without a mandate still blocking release. It independently reruns the existing read-only six-predicate accounting oracle on nine fresh positive SQLite databases and one deliberately corrupt database. It verifies bank source hashes against the host checkout. This reuses the original oracle function without changing it or importing the reference-run execution code.

Review `report.json`, all raw logs, image identity, `outputs/summary.json`, every raw gate report/observation, `outputs/bank/summary.json`, and the SQLite databases with their WAL/SHM companions. The report preserves host OS/architecture, engine identity, declared/source checkout SHA, all tracked lab source hashes and hashes of captured artifacts. Record the VM/provider/WSL configuration alongside the report. Archive the entire attempt directory without altering originals; preserve failed attempts before a correction or retry. A missing/corrupt file or a missing expected database must block acceptance.

Use exactly the same pinned source and acceptance criteria on Linux, macOS/Podman-machine and Windows/WSL2. A `PASS` is limited to that host, architecture, engine and image. If a bind mount, architecture, native SQLite library or compiler fails, retain the original stage logs; make an isolated corrective change and repeat under a new source/attempt identity. Do not replace a missing target-host run with the Linux result. These external runs remain non-blocking for book/lab integration and do not grant production approval.
