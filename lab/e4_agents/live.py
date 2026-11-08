#!/usr/bin/env python3
"""Bounded Azure builder requests and separately isolated candidate evaluation."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

from qualify import (Containers, DEFAULT_IMAGE, LAB, MODES, host_provenance,
                     read_legacy, sha, source_provenance)

PROMPT = """Implement a synthetic fee calculator from scratch in C#/.NET 10.
Return a JSON object with exactly two fields: program (complete Program.cs text)
and tests (1 to 64 objects, each with input and expected strings).
Use only framework libraries. No files, network, subprocesses or external packages.
The program reads stdin lines until EOF and writes exactly one result per line.
The input is exactly 14 ASCII characters: eight amount digits, five rate digits,
then Y or N. Any other input, including a rate above 10000, returns
INVALID|00000000. Validate the entire input before checking activity.
N returns REJECT|00000000. For Y, calculate fee = amount * rate / 10000,
rounded to the nearest integer with exact half rounded away from zero.
An amount strictly greater than 1000000 returns REVIEW, otherwise APPROVE.
Append | and the fee as exactly eight decimal digits, with leading zeroes.
Do not trim input or accept non-ASCII digits. No labels or diagnostics on stdout.
Write your own boundary and invalid-input tests. You cannot see or modify the
independent acceptance cases or evaluator. Only your generated source and own
test feedback may be used for repairs. This is a didactic task, not bank approval.
"""
MAX_REQUESTS = 3
MAX_COMPLETION_TOKENS = 4000


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_payload(content):
    value = json.loads(content)
    if not isinstance(value, dict) or set(value) != {"program", "tests"}:
        raise ValueError("Expected exactly program and tests")
    if not isinstance(value["program"], str) or not 1 <= len(value["program"]) <= 32000:
        raise ValueError("Program must contain 1..32000 characters")
    tests = value["tests"]
    if not isinstance(tests, list) or not 1 <= len(tests) <= 64:
        raise ValueError("Expected 1..64 self-authored test vectors")
    for test in tests:
        if (not isinstance(test, dict) or set(test) != {"input", "expected"}
                or not isinstance(test["input"], str) or len(test["input"]) > 128
                or "\n" in test["input"] or "\r" in test["input"]
                or not isinstance(test["expected"], str)
                or not re.fullmatch(r"(INVALID|REJECT|REVIEW|APPROVE)\|[0-9]{8}", test["expected"])):
            raise ValueError("Invalid self-authored test vector")
    return value


def endpoint_url(endpoint):
    url = urllib.parse.urlsplit(endpoint)
    if (url.scheme != "https" or not url.hostname or url.username or url.password
            or url.port is not None or url.query or url.fragment or url.path not in ("", "/")
            or not any(url.hostname.endswith(suffix)
                       for suffix in (".openai.azure.com", ".cognitiveservices.azure.com"))):
        raise ValueError("Use an HTTPS Azure model account endpoint without credentials or path")
    return endpoint.rstrip("/") + "/openai/v1/chat/completions"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Model endpoint redirects are forbidden")


def request(args):
    url = endpoint_url(args.endpoint)
    messages = [{"role": "user", "content": PROMPT}]
    attempt = 1
    if args.previous:
        previous = load(args.previous / "request.json")
        attempt = previous["attempt"] + 1
        if previous["endpoint"] != url or previous["body"]["model"] != args.model:
            raise ValueError("A model or endpoint change requires a new experimental condition")
        response = load(args.previous / "response.json")
        feedback = load(args.previous / "evaluation/self-feedback.json")
        messages = previous["body"]["messages"] + [
            {"role": "assistant", "content": response["choices"][0]["message"]["content"]},
            {"role": "user", "content": "Repair using only this self-test feedback. Return the same JSON shape:\n"
             + json.dumps(feedback)},
        ]
    if attempt > MAX_REQUESTS:
        raise ValueError("Three-request campaign budget exhausted")
    args.output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(Path(__file__), args.output / "live.py")
    body = {"model": args.model, "messages": messages,
            "response_format": {"type": "json_object"},
            "max_completion_tokens": MAX_COMPLETION_TOKENS}
    record = {"attempt": attempt, "endpoint": url, "subscriptionId": args.subscription, "body": body,
              "startedUtc": datetime.now(timezone.utc).isoformat(),
              "sourceSha256": sha(Path(__file__)), "status": "FAILED",
              "maxRequests": MAX_REQUESTS, "maxOutputTokensTotal": MAX_REQUESTS * MAX_COMPLETION_TOKENS}
    save(args.output / "request.json", record)
    cli = shutil.which("az")
    if not cli:
        raise RuntimeError("Azure CLI is required; authenticate before requesting a model")
    token = subprocess.run(
        [cli, "account", "get-access-token", "--subscription", args.subscription,
         "--resource", "https://cognitiveservices.azure.com/", "--output", "json"],
        capture_output=True, text=True, timeout=60, check=True)
    bearer = json.loads(token.stdout)["accessToken"]
    started = time.monotonic()
    try:
        http = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers={
            "Authorization": "Bearer " + bearer, "Content-Type": "application/json"})
        with urllib.request.build_opener(NoRedirect).open(http, timeout=180) as result:
            raw = result.read(1_048_577)
            (args.output / "response.json").write_bytes(raw)
            if len(raw) > 1_048_576:
                raise ValueError("Model response exceeds the evidence size limit")
            response = json.loads(raw)
            record["requestId"] = result.headers.get("apim-request-id")
        choice = response["choices"][0]
        if choice["finish_reason"] != "stop":
            raise ValueError("Model response did not finish normally")
        payload = candidate_payload(choice["message"]["content"])
        save(args.output / "candidate.json", payload)
        record.update(status="RECEIVED", model=response["model"], usage=response["usage"])
    except urllib.error.HTTPError as error:
        (args.output / "http-error.txt").write_bytes(error.read(65536))
        record["httpStatus"] = error.code
        raise
    finally:
        record["elapsedSeconds"] = time.monotonic() - started
        record["finishedUtc"] = datetime.now(timezone.utc).isoformat()
        save(args.output / "request.json", record)
    print(json.dumps({key: record[key] for key in ("status", "attempt", "model", "usage")}))


def bounded(command):
    # Redirect inside the bounded tmpfs, not the writable source mount.
    return ["sh", "-c", 'set +e; "$@" > /tmp/out 2>/tmp/err; status=$?; '
            'head -c 65536 /tmp/out; head -c 65536 /tmp/err >&2; '
            '[ "$(wc -c < /tmp/out)" -le 65536 ] || exit 97; '
            '[ "$(wc -c < /tmp/err)" -le 65536 ] || exit 97; exit "$status"', "bounded", *command]


def evaluate(args):
    if platform.system() != "Linux" or os.getuid() == 0:
        raise RuntimeError("Evaluation requires a non-root Linux user with container-engine access")
    provenance = source_provenance()
    output = args.output.resolve() if args.output else (args.attempt / "evaluation").resolve()
    output.mkdir(parents=True, exist_ok=False)
    payload = candidate_payload(json.dumps(load(args.attempt / "candidate.json")))
    cases = load(LAB / "contracts/cases.json")
    legacy = read_legacy(args.legacy_results, cases)
    protected = {str(p.relative_to(LAB)): sha(p) for folder in ("contracts", "Gate", "Candidate")
                 for p in (LAB / folder).iterdir() if p.is_file()}
    containers = Containers(args.engine, DEFAULT_IMAGE, output)
    report = {"classification": "LIVE_MODEL_BUILDER_PILOT_NOT_E4_ACCEPTANCE",
              "status": "FAILED", "humanReviewSeconds": None, "actualBilledCost": None,
              **provenance, "host": host_provenance(args.engine),
              "legacyInputSha256": {name: sha(args.legacy_results / name)
                                    for name in ("summary.json", "none-observations.json")},
              "startedUtc": datetime.now(timezone.utc).isoformat(),
              "sourceSha256": {name: sha(LAB / "e4_agents" / name) for name in ("live.py", "qualify.py")},
              "candidateSha256": sha(args.attempt / "candidate.json"),
              "protectedSha256": protected, "cases": len(cases),
              "limitations": ["One synthetic task, not a population success rate.",
                             "Evaluation replays a retained candidate; no model inference is performed.",
                             "Host facts are recorded; Azure candidate execution requires external provenance.",
                             "No human-review timing or invoiced model cost was measured.",
                             "Containers share the host kernel. No arbitrary-code security certification.",
                             "Frozen-case agreement is not universal correctness or production authorization."]}
    shutil.copyfile(Path(__file__), output / "live.py")
    shutil.copyfile(LAB / "e4_agents/qualify.py", output / "qualify.py")
    try:
        for name, command in (("engine-version.txt", ["version"]),
                              ("engine-info.json", ["info", "--format", "{{json .}}"]),
                              ("sdk-image.json", ["image", "inspect", DEFAULT_IMAGE])):
            result = containers.command(command)
            (output / name).write_text(result.stdout, encoding="utf-8")
            if result.returncode:
                raise RuntimeError(f"Container prerequisite failed: {result.stderr}")
        with tempfile.TemporaryDirectory(prefix="book-live-builder-", dir=output) as directory:
            root = Path(directory)
            candidate, reference, gate, policy = (root / name for name in ("candidate", "reference", "gate", "policy"))
            for path in (candidate, reference, gate, policy):
                path.mkdir()
            (candidate / "Program.cs").write_text(payload["program"], encoding="utf-8")
            shutil.copyfile(LAB / "Candidate/Candidate.csproj", candidate / "Candidate.csproj")
            for name in ("Program.cs", "Candidate.csproj"):
                shutil.copyfile(LAB / "Candidate" / name, reference / name)
            for name in ("Program.cs", "Gate.csproj"):
                shutil.copyfile(LAB / "Gate" / name, gate / name)
            (policy / "NuGet.Config").write_text(
                "<configuration><packageSources><clear /></packageSources></configuration>\n")
            for name, folder, project in (("candidate", candidate, "Candidate"),
                                          ("reference", reference, "Candidate"), ("gate", gate, "Gate")):
                try:
                    containers.run("build-" + name, [(folder, "/work", True), (policy, "/policy", False)],
                        bounded(["dotnet", "build", f"/work/{project}.csproj", "-c", "Release", "-m:1",
                                 "--disable-build-servers", "-p:RestoreConfigFile=/policy/NuGet.Config"]))
                except (RuntimeError, subprocess.SubprocessError):
                    if name == "candidate":
                        diagnostics = {stream: (output / ("build-candidate." + stream)).read_text()
                                       for stream in ("stdout", "stderr")
                                       if (output / ("build-candidate." + stream)).exists()}
                        save(output / "self-feedback.json", {"status": "BUILD_ERROR", **diagnostics})
                    raise
            def execute(name, folder, inputs, mode="none"):
                return containers.run(name, [(folder, "/candidate", False)],
                    bounded(["dotnet", "/candidate/bin/Release/net10.0/Candidate.dll", mode]),
                    "\n".join(inputs) + "\n").splitlines()

            tests = payload["tests"]
            values = execute("self-tests", candidate, [test["input"] for test in tests])
            expected = [test["expected"] for test in tests]
            feedback = {"status": "PASS" if values == expected else "FAIL",
                        "expected": expected, "actual": values}
            save(output / "self-feedback.json", feedback)
            report["selfTests"] = {"status": feedback["status"], "cases": len(tests)}
            controls = {}
            for mode in MODES:
                actual = execute("self-tests-" + mode, reference, [test["input"] for test in tests], mode)
                controls[mode] = {"acceptedBySelfTests": actual == expected}
            report["selfTestControls"] = controls
            values = execute("frozen-cases", candidate, [case["input"] for case in cases])
            rows = [{"id": case["id"], "legacy": legacy[case["id"]], "candidate": value}
                    for case, value in zip(cases, values)]
            observation = output / "observations.json"
            save(observation, rows)
            if len(values) > len(cases):
                raise ValueError("Candidate returned extra frozen-case output")
            mismatch = any(row["candidate"] != cases[index]["expected"] for index, row in enumerate(rows))
            expected_exit = 2 if mismatch else 3 if len(values) != len(cases) else 0
            verdict = json.loads(containers.run("independent-gate", [
                (gate / "bin/Release/net10.0", "/gate", False), (LAB / "contracts", "/contracts", False),
                (observation, "/observations.json", False)],
                ["dotnet", "/gate/Gate.dll", "/contracts/cases.json",
                 sha(LAB / "contracts/cases.json"), "/observations.json", "demo-authorized"],
                expected_exit=expected_exit))
            report["independentGate"] = verdict
            report["status"] = "EVALUATED"
    except (RuntimeError, ValueError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
        raise
    finally:
        report["protectedUnchanged"] = all(sha(LAB / name) == digest for name, digest in protected.items())
        report["commands"] = containers.commands
        report["finishedUtc"] = datetime.now(timezone.utc).isoformat()
        save(output / "evaluation.json", report)
        if not report["protectedUnchanged"]:
            raise RuntimeError("Protected inputs changed")
    print(json.dumps({key: report[key] for key in
                     ("status", "selfTests", "selfTestControls", "independentGate", "protectedUnchanged")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    remote = commands.add_parser("request")
    remote.add_argument("--endpoint", required=True)
    remote.add_argument("--model", required=True)
    remote.add_argument("--subscription", required=True)
    remote.add_argument("--output", type=Path, required=True)
    remote.add_argument("--previous", type=Path)
    local = commands.add_parser("evaluate")
    local.add_argument("--engine", choices=("docker", "podman"), default="docker")
    local.add_argument("--attempt", type=Path, required=True)
    local.add_argument("--legacy-results", type=Path, required=True)
    local.add_argument("--output", type=Path, help="New evaluation directory; never overwrites an earlier evaluation")
    args = parser.parse_args()
    if args.command == "request":
        request(args)
    else:
        args.attempt = args.attempt.resolve()
        evaluate(args)


if __name__ == "__main__":
    main()
