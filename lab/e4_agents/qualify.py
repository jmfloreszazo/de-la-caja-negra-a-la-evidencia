#!/usr/bin/env python3
"""Qualify candidate isolation and the existing gate; never simulate an agent run."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import uuid

LAB = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "mcr.microsoft.com/dotnet/sdk@sha256:c7445f141c04f1a6b454181bd098dcfa606c61ba0bd213d0a702489e5bd4cd71"
MODES = ("none", "round-even", "wrong-threshold", "approve-inactive")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_legacy(results, cases):
    summary = json.loads((results / "summary.json").read_text())
    rows = json.loads((results / "none-observations.json").read_text())
    if summary["status"] != "PASS" or summary["baselineSha256"] != sha(LAB / "contracts/cases.json"):
        raise ValueError("Legacy evidence must be a successful run of the current frozen contract")
    for source in ("legacy/fee.cob", "Gate/Program.cs", "Candidate/Program.cs"):
        if summary["sourceSha256"][source] != sha(LAB / source):
            raise ValueError(f"Legacy evidence source differs: {source}")
    expected = {case["id"]: case["expected"] for case in cases}
    if len(rows) != len(cases) or {row["id"] for row in rows} != set(expected):
        raise ValueError("Legacy evidence has missing, unknown or duplicate cases")
    if any(row["legacy"] != expected[row["id"]] for row in rows):
        raise ValueError("Legacy evidence does not satisfy the frozen contract")
    return {row["id"]: row["legacy"] for row in rows}


def source_provenance():
    """Separate locally observed Git state from launcher-attested export metadata."""
    names = ("SOURCE_HEAD_SHA", "SOURCE_ARCHIVE_SHA256", "SOURCE_WORKTREE_DIRTY")
    supplied = {name: os.environ[name] for name in names if name in os.environ}
    if supplied and len(supplied) != len(names):
        raise ValueError("Supply SOURCE_HEAD_SHA, SOURCE_ARCHIVE_SHA256 and SOURCE_WORKTREE_DIRTY together")
    exported = None
    if supplied:
        head, archive, dirty = (supplied[name] for name in names)
        if not re.fullmatch(r"[0-9a-fA-F]{40}", head):
            raise ValueError("SOURCE_HEAD_SHA must be a full 40-digit hexadecimal Git commit")
        if not re.fullmatch(r"[0-9a-fA-F]{64}", archive):
            raise ValueError("SOURCE_ARCHIVE_SHA256 must be a 64-digit hexadecimal SHA-256")
        if dirty not in ("true", "false", "0", "1"):
            raise ValueError("SOURCE_WORKTREE_DIRTY must be true, false, 0 or 1")
        exported = {"sourceCommit": head.lower(), "sourceArchiveSha256": archive.lower(),
                    "worktreeDirty": dirty in ("true", "1")}
    # Do not accidentally discover a parent repository around an exported tree.
    if (LAB.parent / ".git").exists():
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=LAB.parent, text=True).strip()
        dirty = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=LAB.parent, text=True).strip())
        if exported and (exported["sourceCommit"] != head or exported["worktreeDirty"] != dirty):
            raise ValueError("SOURCE metadata conflicts with observed Git state")
        return {"sourceCommit": head, "worktreeDirty": dirty,
                "sourceProvenance": "local-git", "sourceArchiveSha256": None}
    if exported is None:
        raise ValueError("Exported source without .git requires all three SOURCE provenance variables")
    return {**exported, "sourceProvenance": "launcher-attested-export",
            "sourceArchiveVerifiedByEvaluator": False}


def host_provenance(engine):
    return {"system": platform.system(), "release": platform.release(),
            "version": platform.version(), "machine": platform.machine(),
            "node": platform.node(), "uid": os.getuid(), "gid": os.getgid(),
            "pythonVersion": platform.python_version(), "containerEngine": engine,
            "executionLocation": "unverified",
            "note": "Observed supervisor host; engine-info.json identifies the engine host. "
                    "Source metadata and an Azure model endpoint do not establish Azure execution."}


class Containers:
    def __init__(self, engine, image, output):
        if engine not in ("docker", "podman"):
            raise ValueError("Choose docker or podman explicitly")
        self.engine, self.image, self.output = engine, image, output
        self.commands = []

    def command(self, arguments, **kwargs):
        self.commands.append([self.engine, *arguments])
        return subprocess.run([self.engine, *arguments], capture_output=True,
                              text=True, timeout=180, **kwargs)

    def inspect_policy(self, identifier, name, mounts):
        inspection = self.command(["inspect", identifier])
        if inspection.returncode:
            raise RuntimeError(f"Cannot verify container configuration: {inspection.stderr}")
        (self.output / (name + ".json")).write_text(inspection.stdout, encoding="utf-8")
        state = json.loads(inspection.stdout)[0]
        config = state["HostConfig"]
        one_cpu = (config.get("NanoCpus") == 1_000_000_000 or
                   (config.get("CpuPeriod", 0) > 0 and
                    config.get("CpuQuota") == config["CpuPeriod"]))
        expected_mounts = {target: (str(source.resolve()), writable) for source, target, writable in mounts}
        actual_mounts = {mount["Destination"]: (mount.get("Source"), mount["RW"])
                         for mount in state["Mounts"] if mount["Type"] == "bind"}
        capabilities_dropped = "ALL" in (config.get("CapDrop") or [])
        if self.engine == "podman":
            # Podman 4.9 expands CapDrop relative to its defaults, not to ALL.
            # Verify the actual OCI capability sets; absent fields are not empty sets.
            capabilities_dropped = (all(key in state and state[key] in ([], None)
                                        for key in ("EffectiveCaps", "BoundingCaps"))
                                    and not config.get("CapAdd"))
        if (not config["ReadonlyRootfs"] or config["NetworkMode"] != "none"
                or config["Privileged"] or state["Config"]["User"] != f"{os.getuid()}:{os.getgid()}"
                or not capabilities_dropped
                or "no-new-privileges" not in config.get("SecurityOpt", [])
                or config["Memory"] != 1_073_741_824 or config["PidsLimit"] != 128
                or not one_cpu or config.get("PidMode", "") == "host"
                or any(mount["Type"] != "bind" for mount in state["Mounts"])
                or len(state["Mounts"]) != len(expected_mounts)
                or actual_mounts != expected_mounts
                or (self.engine == "podman" and config.get("UsernsMode") != "private")):
            raise RuntimeError("Container isolation configuration differs from the requested policy")
        return state

    def run(self, name, mounts, command, input_text=None, expected_exit=0):
        args = [
            "create", "-i", "--name", "book-e4-" + uuid.uuid4().hex,
            "--read-only", "--network", "none", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges", "--pids-limit", "128",
            "--memory", "1g", "--cpus", "1",
            "--user", f"{os.getuid()}:{os.getgid()}",
            "--tmpfs", "/tmp:rw,nosuid,size=134217728",
        ]
        if self.engine == "podman":
            # Map the non-root supervisor UID to itself so disposable bind mounts
            # stay writable without chmod/chown or exposing the host root identity.
            args.extend(("--userns", "keep-id", "--read-only-tmpfs=false", "--http-proxy=false"))
        for value in ("DOTNET_CLI_HOME=/tmp/dotnet", "NUGET_PACKAGES=/tmp/nuget",
                      "DOTNET_CLI_TELEMETRY_OPTOUT=1", "DOTNET_NOLOGO=1",
                      "DOTNET_SKIP_FIRST_TIME_EXPERIENCE=1"):
            args.extend(("--env", value))
        for source, target, writable in mounts:
            args.extend(("--mount", f"type=bind,src={source},dst={target}" +
                         ("" if writable else ",readonly")))
        created = self.command([*args, self.image, *command])
        if created.returncode:
            raise RuntimeError(f"Container creation failed: {created.stderr}")
        identifier = created.stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{64}", identifier):
            raise RuntimeError("Engine did not return a full owned container ID")
        try:
            self.inspect_policy(identifier, name + ".created", mounts)
            try:
                result = self.command(["start", "-a", "-i", identifier], input=input_text)
            except subprocess.TimeoutExpired as error:
                for suffix, value in ((".stdout", error.stdout), (".stderr", error.stderr)):
                    text = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
                    (self.output / (name + suffix)).write_text(text, encoding="utf-8")
                (self.output / (name + ".timeout.json")).write_text(
                    json.dumps({"timeoutSeconds": error.timeout}) + "\n", encoding="utf-8")
                raise
            (self.output / (name + ".stdout")).write_text(result.stdout, encoding="utf-8")
            (self.output / (name + ".stderr")).write_text(result.stderr, encoding="utf-8")
            state = self.inspect_policy(identifier, name + ".container", mounts)
            if state["State"]["Running"] or state["State"]["ExitCode"] != expected_exit:
                raise RuntimeError(f"{name}: unexpected container exit; inspect retained logs")
            if result.returncode not in (0, expected_exit):
                raise RuntimeError(f"{name}: engine command failed with {result.returncode}")
            return result.stdout
        finally:
            removed = self.command(["rm", "-f", identifier])
            if removed.returncode:
                raise RuntimeError(f"Failed to remove owned container {identifier}: {removed.stderr}")


def qualify(legacy_results, output, engine, image):
    if platform.system() != "Linux" or os.getuid() == 0:
        raise RuntimeError("Run as a non-root Linux/WSL user with container-engine access")
    if engine not in ("docker", "podman"):
        raise ValueError("Choose docker or podman explicitly")
    provenance = source_provenance()
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(Path(__file__), output / "qualifier.py")
    protected = [LAB / path for path in (
        "contracts/cases.json", "contracts/cases.sha256",
        "Gate/Program.cs", "Gate/Gate.csproj", "Candidate/Program.cs", "Candidate/Candidate.csproj",
    )]
    original = {str(path.relative_to(LAB)): sha(path) for path in protected}
    report = {
        "schemaVersion": 1, "classification": "E4_PREREQUISITE_QUALIFICATION_NOT_LIVE_AGENT_EVIDENCE",
        "status": "FAIL", "startedUtc": datetime.now(timezone.utc).isoformat(),
        "liveAgentRuns": 0, **provenance, "host": host_provenance(engine),
        "qualifierSha256": sha(output / "qualifier.py"),
        "protectedSha256": original, "candidateGateReports": {},
        "model": None, "modelTokens": None, "humanReviewSeconds": None,
        "costPerAcceptedChange": None,
        "limitations": [
            "No model or agent is invoked; no E4 task-level defect or false-block rate is estimated.",
            "Known reference candidate and three deterministic mutants, not universal mutation coverage.",
            "Containers share a host kernel; this is not protection against kernel exploits.",
            "The existing gate grants DEMO_ONLY / SIMULATED_ALLOW, never production authority.",
            "Legacy observations are reused from the explicitly supplied real COBOL run, not fabricated.",
        ],
    }
    containers = Containers(engine, image, output)
    try:
        anchor = (LAB / "contracts/cases.sha256").read_text().strip()
        if sha(LAB / "contracts/cases.json") != anchor:
            raise ValueError("Frozen contract digest mismatch")
        cases = json.loads((LAB / "contracts/cases.json").read_text())
        legacy = read_legacy(legacy_results, cases)
        for name in ("summary.json", "none-observations.json"):
            shutil.copyfile(legacy_results / name, output / ("legacy-" + name))
        report["legacyInputSha256"] = {
            name: sha(legacy_results / name) for name in ("summary.json", "none-observations.json")
        }
        version = containers.command(["version"])
        if version.returncode:
            raise RuntimeError(f"Container engine unavailable: {version.stderr}")
        (output / "engine-version.txt").write_text(version.stdout, encoding="utf-8")
        info = containers.command(["info", "--format", "{{json .}}"])
        (output / "engine-info.json").write_text(info.stdout, encoding="utf-8")
        if info.returncode:
            raise RuntimeError(f"Cannot record engine host provenance: {info.stderr}")
        inspected = containers.command(["image", "inspect", image])
        if inspected.returncode:
            raise RuntimeError(f"SDK image is missing; pull the documented image first: {inspected.stderr}")
        (output / "sdk-image.json").write_text(inspected.stdout, encoding="utf-8")
        with tempfile.TemporaryDirectory(prefix="book-e4-", dir=output) as directory:
            root = Path(directory)
            candidate, gate, policy = (root / name for name in ("Candidate", "Gate", "policy"))
            for path in (candidate, gate, policy):
                path.mkdir()
            for name in ("Program.cs", "Candidate.csproj"):
                shutil.copyfile(LAB / "Candidate" / name, candidate / name)
            for name in ("Program.cs", "Gate.csproj"):
                shutil.copyfile(LAB / "Gate" / name, gate / name)
            (policy / "NuGet.Config").write_text(
                "<configuration><packageSources><clear /></packageSources></configuration>\n")
            probe = """set -eu
printf 'allowed\\n' > /candidate/write-probe.txt
for target in /protected/contracts/cases.json /protected/Gate/Program.cs /forbidden-write; do
    if printf 'forbidden\\n' >> "$target"; then
        echo "Unexpected writable protected target: $target" >&2
        exit 23
    fi
    printf 'DENIED %s\\n' "$target"
done
"""
            stdout = containers.run("write-boundary", [
                (candidate, "/candidate", True),
                (LAB / "contracts", "/protected/contracts", False),
                (LAB / "Gate", "/protected/Gate", False),
            ], ["sh", "-c", probe])
            if stdout.count("DENIED ") != 3 or (candidate / "write-probe.txt").read_text() != "allowed\n":
                raise RuntimeError("Write-scope probe did not exercise every required boundary")
            report["writeScope"] = {"protectedWritesAttempted": 3, "protectedWritesDenied": 3,
                                    "candidateWriteSucceeded": True}
            for project, source in (("Candidate", candidate), ("Gate", gate)):
                containers.run("build-" + project.lower(), [
                    (source, "/work", True), (policy, "/policy", False),
                ], ["dotnet", "build", f"/work/{project}.csproj", "-c", "Release", "-m:1",
                    "--disable-build-servers", "-p:RestoreConfigFile=/policy/NuGet.Config"])
            for mode in MODES:
                stdout = containers.run("candidate-" + mode, [(candidate, "/candidate", True)],
                    ["dotnet", "/candidate/bin/Release/net10.0/Candidate.dll", mode],
                    "\n".join(case["input"] for case in cases) + "\n")
                values = stdout.splitlines()
                if len(values) != len(cases):
                    raise RuntimeError("Candidate output count does not match the frozen input set")
                observations = [{"id": case["id"], "legacy": legacy[case["id"]], "candidate": value}
                                for case, value in zip(cases, values, strict=True)]
                observation_file = output / (mode + "-observations.json")
                observation_file.write_text(json.dumps(observations, indent=2) + "\n")
                verdict = json.loads(containers.run("gate-" + mode, [
                    (gate / "bin/Release/net10.0", "/gate", False),
                    (LAB / "contracts", "/contracts", False),
                    (observation_file, "/observations.json", False),
                ], ["dotnet", "/gate/Gate.dll", "/contracts/cases.json", anchor,
                    "/observations.json", "demo-authorized"], expected_exit=0 if mode == "none" else 2))
                expected = "PASS" if mode == "none" else "FAIL"
                release = "SIMULATED_ALLOW" if mode == "none" else "BLOCK"
                if (verdict["verdict"] != expected or verdict["authority"] != "DEMO_ONLY"
                        or verdict["release"] != release):
                    raise RuntimeError(f"Gate failed qualification for {mode}")
                report["candidateGateReports"][mode] = verdict
            report["casesPerCandidate"] = len(cases)
            report["knownMutantsKilled"] = 3
            report["status"] = "QUALIFICATION_PASS_NOT_AGENT_ACCEPTANCE"
    finally:
        after = {str(path.relative_to(LAB)): sha(path) for path in protected}
        report["protectedUnchanged"] = after == original
        if after != original:
            report["status"] = "FAIL"
        report["commands"] = containers.commands
        report["finishedUtc"] = datetime.now(timezone.utc).isoformat()
        (output / "qualification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        if after != original:
            raise RuntimeError("Protected sources changed during qualification")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--engine", choices=("docker", "podman"), default="docker")
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    args = parser.parse_args()
    report = qualify(args.legacy_results.resolve(), args.output.resolve(), args.engine, args.image)
    print(json.dumps({key: report[key] for key in
                     ("status", "liveAgentRuns", "casesPerCandidate", "knownMutantsKilled", "protectedUnchanged")}, indent=2))


if __name__ == "__main__":
    main()
