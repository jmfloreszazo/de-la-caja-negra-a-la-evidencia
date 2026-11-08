#!/usr/bin/env python3
"""Reproduce local synthetic experiments in fresh Linux checkouts, retaining failures."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import traceback

REPO = Path(__file__).resolve().parents[2]
SCOPES = ("lab", "scripts/azure/run-experiment.sh", "scripts/azure/e4-inputs.py",
          "scripts/azure/run-e4-replay.sh", "global.json", "NuGet.Config",
          "Directory.Build.props", "Directory.Build.targets", "Directory.Packages.props")
EXPERIMENTS = ("core", "e1", "e1-sqlserver", "e2", "e2-cluster", "e3", "m1", "m2", "e4-prerequisite")
DEFAULTS = ("core", "e1", "e2-cluster", "m2", "e4-prerequisite")
# `e4-replay` is accepted by scripts/azure/run-experiment.sh but intentionally not offered here: it
# needs two explicit external inputs (a recorded model attempt and verified legacy results) and a
# root supervisor that drops to an unprivileged user. See lab/e4_agents/README.md for the manual path.
LAUNCHER_ONLY = ("e4-replay",)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def git(repo, *arguments):
    return subprocess.check_output(["git", "-C", str(repo), *arguments])


def source_paths(repo):
    paths = git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard",
                "--", *SCOPES).decode().split("\0")
    return sorted(set(path for path in paths if path))


def overlay_worktree(repo, checkout, paths):
    for relative in paths:
        source, target = repo / relative, checkout / relative
        if not source.resolve().is_relative_to(repo.resolve()) or source.is_symlink():
            raise ValueError(f"Source links outside the snapshot are not supported: {relative}")
        if not target.parent.resolve().is_relative_to(checkout.resolve()):
            raise ValueError(f"Snapshot destination leaves its checkout: {relative}")
        if target.is_symlink():
            target.unlink()
        if source.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        elif not source.exists():
            target.unlink(missing_ok=True)
        else:
            raise ValueError(f"Expected a regular source file: {relative}")


def run_command(command, cwd, folder, name, environment, timeout):
    record = {"argv": command, "cwd": str(cwd), "exitCode": None, "timedOut": False,
              "startedUtc": datetime.now(timezone.utc).isoformat(),
              "stdout": name + ".stdout", "stderr": name + ".stderr"}
    with (folder / record["stdout"]).open("wb") as out, (folder / record["stderr"]).open("wb") as err:
        with subprocess.Popen(command, cwd=cwd, env=environment, stdout=out, stderr=err,
                              start_new_session=True) as process:
            try:
                record["exitCode"] = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                record["timedOut"] = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    record["exitCode"] = process.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    record["exitCode"] = process.wait()
    record["finishedUtc"] = datetime.now(timezone.utc).isoformat()
    record["passed"] = record["exitCode"] == 0 and not record["timedOut"]
    return record


def verify_artifacts(output):
    report = json.loads((output / "campaign.json").read_text())
    for relative, expected in report["artifactSha256"].items():
        path = output / relative
        if not path.resolve().is_relative_to(output.resolve()) or path.is_symlink():
            raise ValueError(f"Artifact leaves the evidence directory: {relative}")
        if sha(path) != expected:
            raise ValueError(f"Artifact digest mismatch: {relative}")
    return {"integrity": "PASS", "campaignStatus": report["status"],
            "verifiedArtifacts": len(report["artifactSha256"])}


def validate_request(repo, output, experiments, include_worktree, accept_license):
    if len(experiments) != len(set(experiments)):
        raise ValueError("An experiment may appear only once in a campaign")
    if "e4-prerequisite" in experiments:
        if "core" not in experiments or experiments.index("core") > experiments.index("e4-prerequisite"):
            raise ValueError("E4 prerequisites require a successful core stage earlier in the campaign")
    if "e1-sqlserver" in experiments and not accept_license:
        raise ValueError("SQL Server requires explicit --accept-sqlserver-license")
    if output.exists():
        raise ValueError("Output already exists; preserve the previous attempt and choose a new path")
    if output.is_relative_to(repo) and not output.is_relative_to(repo / "lab/results"):
        raise ValueError("Output must be outside the repository or under ignored lab/results")
    dirty = bool(git(repo, "status", "--porcelain", "--untracked-files=all", "--", *SCOPES).strip())
    if dirty and not include_worktree:
        raise ValueError("Lab sources are dirty; use a clean checkout or explicitly --include-working-tree")
    return dirty


def reproduce(args):
    if platform.system() != "Linux":
        raise ValueError("Execute inside Linux or WSL; native Windows/macOS execution is not claimed")
    if "e4-prerequisite" in args.experiments and os.getuid() == 0:
        raise ValueError("E4 prerequisites require a non-root user")
    output = args.output.resolve()
    dirty = validate_request(REPO, output, args.experiments, args.include_working_tree,
                             args.accept_sqlserver_license)
    dependencies = ["git", "bash", "dotnet", "python3", args.engine]
    if "core" in args.experiments:
        dependencies.append(os.environ.get("COBC", "cobc"))
    for executable in dependencies:
        if shutil.which(executable) is None:
            raise ValueError(f"Required executable is missing: {executable}; install it before running")
    commit = git(REPO, "rev-parse", "HEAD").decode().strip()
    paths = source_paths(REPO)
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(Path(__file__), output / "collector.py")
    report = {
        "schemaVersion": 1, "status": "FAIL", "classification": "LOCAL_SYNTHETIC_CAMPAIGN_NOT_E1_E4_ACCEPTANCE",
        "sourceCommit": commit, "worktreeDirty": dirty, "includeWorkingTree": args.include_working_tree,
        "collectorSha256": sha(output / "collector.py"),
        "ciRunId": None, "azureDeployment": "NOT_EXECUTED", "githubActions": "NOT_EXECUTED",
        "liveAgentRuns": 0, "engine": args.engine,
        "host": {"platform": platform.platform(), "python": sys.version,
                 "isWsl": "microsoft" in platform.release().lower()},
        "toolchainEnvironment": {name: os.environ[name] for name in (
            "DOTNET", "DOTNET_ROOT", "COBC", "COB_CONFIG_DIR", "COB_COPY_DIR",
            "COB_CFLAGS", "COB_LIBS", "LD_LIBRARY_PATH") if name in os.environ},
        "startedUtc": datetime.now(timezone.utc).isoformat(),
        "stages": [{"experiment": name, "status": "NOT_RUN", "commands": []} for name in args.experiments],
        "limitations": [
            "Synthetic single-host controls, not bank capacity, distributed HA or E1-E4 acceptance.",
            "E4 is known-candidate isolation and mutation qualification, not a live-agent comparison.",
            "Mutable package feeds and image tags are not a bit-reproducible build or an SBOM.",
            "Source snapshot plus hashes records working-tree bytes separately from the base commit.",
        ],
    }
    environment = os.environ.copy()
    environment["CONTAINER_ENGINE"] = args.engine
    environment.pop("ACCEPT_EULA", None)
    if args.accept_sqlserver_license:
        environment["ACCEPT_EULA"] = "Y"
    try:
        with tempfile.TemporaryDirectory(prefix="book-campaign-") as directory:
            root = Path(directory)
            snapshot = root / "snapshot"
            subprocess.run(["git", "-c", "core.autocrlf=false", "clone", "--quiet",
                            "--no-hardlinks", "--no-checkout", str(REPO), str(snapshot)], check=True)
            git(snapshot, "-c", "core.autocrlf=false", "checkout", "--quiet", "--detach", commit)
            if args.include_working_tree:
                overlay_worktree(REPO, snapshot, paths)
            captured = {relative: sha(snapshot / relative) for relative in source_paths(snapshot)
                        if (snapshot / relative).is_file()}
            report["sourceSha256"] = captured
            with tarfile.open(output / "source.tar.gz", "x:gz") as archive:
                for relative in captured:
                    archive.add(snapshot / relative, arcname=relative, recursive=False)
            environment["SOURCE_HEAD_SHA"] = commit
            environment["SOURCE_ARCHIVE_SHA256"] = sha(output / "source.tar.gz")
            environment["SOURCE_WORKTREE_DIRTY"] = str(dirty).lower()
            environment["EXPERIMENT_HOST"] = "LOCAL_LINUX"
            for stage in report["stages"]:
                name = stage["experiment"]
                folder = output / name
                folder.mkdir()
                stage["status"] = "FAIL"
                with tempfile.TemporaryDirectory(prefix="stage-", dir=root) as stage_directory:
                    checkout = Path(stage_directory) / "source"
                    shutil.copytree(snapshot, checkout)
                    if name == "e4-prerequisite":
                        command = [sys.executable, "lab/e4_agents/qualify.py", "--engine", args.engine,
                                   "--legacy-results", str(output / "core/results"),
                                   "--output", str(folder / "qualification")]
                    else:
                        command = ["bash", "scripts/azure/run-experiment.sh", name, str(folder / "runtime")]
                    try:
                        observation = run_command(command, checkout, folder, "execution", environment,
                                                  args.timeout_seconds)
                        stage["commands"].append(observation)
                    finally:
                        results = checkout / "lab/results"
                        if results.exists():
                            shutil.copytree(results, folder / "results")
                        virtualenv = folder / "venv"
                        if virtualenv.is_dir() and not virtualenv.is_symlink():
                            shutil.rmtree(virtualenv)
                    if not observation["passed"]:
                        raise RuntimeError(f"{name} failed; preserve {folder} before retrying")
                    if name == "core":
                        audit_command = [sys.executable, "-c",
                            "import json,sys; sys.path.insert(0,'lab/tools'); "
                            "from audit_host_results import audit; print(json.dumps(audit(sys.argv[1])))",
                            str(folder / "results")]
                        audited = run_command(audit_command, checkout, folder, "independent-audit",
                                              environment, 60)
                        stage["commands"].append(audited)
                        if not audited["passed"]:
                            raise RuntimeError("Independent core accounting audit failed")
                        stage["independentAudit"] = json.loads((folder / "independent-audit.stdout").read_text())
                    if name == "e4-prerequisite":
                        qualification = json.loads((folder / "qualification/qualification.json").read_text())
                        if qualification["status"] != "QUALIFICATION_PASS_NOT_AGENT_ACCEPTANCE":
                            raise RuntimeError("E4 prerequisites did not qualify")
                    for relative, expected in captured.items():
                        if sha(checkout / relative) != expected:
                            raise RuntimeError(f"Executed source changed during {name}: {relative}")
                stage["status"] = "PASS"
                print(f"{name}: PASS (local synthetic controls only)", flush=True)
        report["status"] = "LOCAL_CAMPAIGN_PASS_NOT_EXPERIMENT_ACCEPTANCE"
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError):
        report["failure"] = traceback.format_exc()
        raise
    finally:
        report["finishedUtc"] = datetime.now(timezone.utc).isoformat()
        report["artifactSha256"] = {
            path.relative_to(output).as_posix(): sha(path)
            for path in output.rglob("*") if path.is_file() and path != output / "campaign.json"
        }
        save(output / "campaign.json", report)
    print(json.dumps(verify_artifacts(output), indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="New immutable campaign directory")
    parser.add_argument("--engine", choices=("docker", "podman"))
    parser.add_argument("--experiments", nargs="+", choices=EXPERIMENTS, default=list(DEFAULTS))
    parser.add_argument("--include-working-tree", action="store_true",
                        help="Explicitly capture current lab/launcher files, including untracked source")
    parser.add_argument("--accept-sqlserver-license", action="store_true",
                        help="Accept SQL Server Developer terms for an explicitly selected e1-sqlserver stage")
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--verify", type=Path, help="Check captured artifact hashes without executing anything")
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify_artifacts(args.verify.resolve()), indent=2))
        return
    if not args.output or not args.engine:
        parser.error("Execution requires --output and an explicit --engine")
    if not 60 <= args.timeout_seconds <= 3600:
        parser.error("--timeout-seconds must be between 60 and 3600")
    reproduce(args)


if __name__ == "__main__":
    main()
