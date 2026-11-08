"""Verify the 8 November 2026 Azure E1-E4 campaign archives without promoting scientific acceptance.

    python3 scripts/evidence/verify_azure_e1_e4.py [--campaign lab/results/azure-e1-e4-20261108]

Checks source and raw archive hashes and Azure instance metadata, re-derives the
experiment-level checks and semantically compares evidence/runs/azure-e1-e4-2026-11-08.json.
Verification is read-only by default; --write-summary creates a missing summary only.
The campaign folder is ignored by Git; this script is tracked so the derivation is reproducible by
anyone who holds a copy of the archive listed in docs/DIST_MANIFEST.md."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from _checks import compare_summary, require

ROOT = Path(__file__).resolve().parents[2]
_parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
_parser.add_argument("--campaign", type=Path, default=ROOT / "lab/results/azure-e1-e4-20261108")
_parser.add_argument('--write-summary', action='store_true', help='Create a missing summary; never overwrite an existing record')
args = _parser.parse_args()
HERE = args.campaign.resolve()
if not HERE.is_dir():
    raise SystemExit(f"Campaign folder not found: {HERE} (extract the archive from docs/DIST_MANIFEST.md first)")
RUNS = HERE / "runs"
RUN_IDS = ("e1-azure-20261108-01", "e2-cluster-azure-20261108-01",
           "e3-azure-20261108-01", "e4-replay-azure-20261108-01", "e4-replay-azure-20261108-02")


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


records = []
for run_id in RUN_IDS:
    source, raw = RUNS / run_id, RUNS / (run_id + "-evidence")
    request, completion = load(source / "request.json"), load(raw / "completion.json")
    require(request["sourceSha256"] == completion["sourceSha256"] == sha(source / "source.tar"), 'request["sourceSha256"] == completion["sourceSha256"] == sha(source / "source.tar")')
    manifest = load(source / "source.json")
    with tarfile.open(source / "source.tar") as archive:
        require(set(archive.getnames()) == set(manifest["sourceSha256"]), 'set(archive.getnames()) == set(manifest["sourceSha256"])')
        for name, digest in manifest["sourceSha256"].items():
            require(hashlib.sha256(archive.extractfile(name).read()).hexdigest() == digest, 'hashlib.sha256(archive.extractfile(name).read()).hexdigest() == digest')
    with tarfile.open(RUNS / (run_id + "-evidence.tar.gz")) as archive:
        for member in archive.getmembers():
            if member.isfile():
                require(hashlib.sha256(archive.extractfile(member).read()).hexdigest() == sha(raw / member.name), 'hashlib.sha256(archive.extractfile(member).read()).hexdigest() == sha(raw / member.name)')
    instance = load(raw / "azure-instance.json")["compute"]
    require(instance["name"] == "bookev1107-runner" and instance["location"] == "northeurope", 'instance["name"] == "bookev1107-runner" and instance["location"] == "northeurope"')
    require(instance["subscriptionId"] == "7a84bc78-1d1e-4294-a7c4-760dc607b5de", 'instance["subscriptionId"] == "7a84bc78-1d1e-4294-a7c4-760dc607b5de"')
    failed = run_id == "e4-replay-azure-20261108-01"
    require((completion["workloadExitCode"] != 0) == failed, '(completion["workloadExitCode"] != 0) == failed')
    require(completion["artifactPreparationExitCode"] == 0, 'completion["artifactPreparationExitCode"] == 0')
    if "e4-replay" in run_id:
        require(request["e4InputSha256"] == sha(source / "e4-inputs.tar"), 'request["e4InputSha256"] == sha(source / "e4-inputs.tar")')
        require(request["newModelInvocation"] is False, 'request["newModelInvocation"] is False')
    else:
        phases = load(raw / "postgres-completion.json")
        require(set(phases) == {"workloadExitCode", "logExitCode", "dumpExitCode", "cleanupExitCode"}, 'set(phases) == {"workloadExitCode", "logExitCode", "dumpExitCode", "cleanupExitCode"}')
        require(all(value == 0 for value in phases.values()), 'all(value == 0 for value in phases.values())')
    records.append({"runId": run_id, "sourceCommit": completion["sourceCommit"],
                    "sourceArchiveSha256": completion["sourceSha256"], "worktreeDirty": completion["worktreeDirty"],
                    "rawArchiveSha256": sha(RUNS / (run_id + "-evidence.tar.gz")),
                    "workloadExitCode": completion["workloadExitCode"], "vmId": instance["vmId"]})
e1 = RUNS / "e1-azure-20261108-01-evidence/results/e1"
for name in ("summary.json", "summary-dotnet.json", "reference-parity-summary.json",
             "oracle-vectors-summary.json", "multiprocess-parity-summary.json"):
    require(load(e1 / name)["status"] == "PASS", 'load(e1 / name)["status"] == "PASS"')
matrix = load(e1 / "multiprocess-parity-summary.json")["cases"]
require(len(matrix) == 8 and sum(case["operations"] for case in matrix) == 960, 'len(matrix) == 8 and sum(case["operations"] for case in matrix) == 960')
require(all(case["persistedParity"] and all(case["oracle"].values()) for case in matrix), 'all(case["persistedParity"] and all(case["oracle"].values()) for case in matrix)')
e2 = RUNS / "e2-cluster-azure-20261108-01-evidence/results/e2"
for name in ("e2-smoke", "e2-deadlock", "e2-workloads", "e2-process-crash", "e2-multiprocess", "e2-adonet-recovery", "e2-inflight-sql-commit"):
    require(load(e2 / (name + ".json"))["status"] == "PASS", 'load(e2 / (name + ".json"))["status"] == "PASS"')
for name in ("e2-multiprocess", "e2-adonet-recovery"):
    report = load(e2 / (name + ".json"))
    require(report["actualSecondaryExitSignal"] == "SIGKILL", 'report["actualSecondaryExitSignal"] == "SIGKILL"')
    require(all(report["independentSqlOracle"].values()), 'all(report["independentSqlOracle"].values())')
    require(len({report["primarySiloPid"], report["secondarySiloPid"], report["initialExternalClientPid"]}) == 3, 'len({report["primarySiloPid"], report["secondarySiloPid"], report["initialExternalClientPid"]}) == 3')
require(load(e2 / "e2-workloads.json")["controls"]["sixHundredDurableCommittedTransfers"] == "PASS", 'load(e2 / "e2-workloads.json")["controls"]["sixHundredDurableCommittedTransfers"] == "PASS"')
e3_folder = RUNS / "e3-azure-20261108-01-evidence/results/e3"
e3 = load(e3_folder / "summary.json")
require(e3["classification"] == "EXPLORATORY_SYNTHETIC_NOT_E3_CAPACITY_ACCEPTANCE", 'e3["classification"] == "EXPLORATORY_SYNTHETIC_NOT_E3_CAPACITY_ACCEPTANCE"')
require(e3["status"] == "EXPLORATORY_COMPLETED" and not e3["capacityAcceptance"] and not e3["errors"], 'e3["status"] == "EXPLORATORY_COMPLETED" and not e3["capacityAcceptance"] and not e3["errors"]')
for name, digest in e3["artifactSha256"].items():
    require(sha(e3_folder / name) == digest, 'sha(e3_folder / name) == digest')
require(e3["measurement"]["offered"] == 720, 'e3["measurement"]["offered"] == 720')
require(e3["measurement"]["outcomes"] == {"ACK_COMMITTED": 668, "FAILED_CONNECT": 48, "MISSED_SCHEDULE": 4}, 'e3["measurement"]["outcomes"] == {"ACK_COMMITTED": 668, "FAILED_CONNECT": 48, "MISSED_SCHEDULE": 4}')
require(e3["reconciliation"]["consistent"] and e3["reconciliation"]["persistedCommits"] == 668, 'e3["reconciliation"]["consistent"] and e3["reconciliation"]["persistedCommits"] == 668')
require(all(e3["oracleAfter"].values()) and all(e3["negativeControl"]["restoredOracle"].values()), 'all(e3["oracleAfter"].values()) and all(e3["negativeControl"]["restoredOracle"].values())')
require(set(e3["negativeControl"]["detected"]) == {"balancedPostings", "projectionAgrees", "twoPostingsPerCommit"}, 'set(e3["negativeControl"]["detected"]) == {"balancedPostings", "projectionAgrees", "twoPostingsPerCommit"}')
require(e3["recovery"]["recoveredServiceAcknowledgedCommit"], 'e3["recovery"]["recoveredServiceAcknowledgedCommit"]')
e4_folder = RUNS / "e4-replay-azure-20261108-02-evidence/e4-results"
e4 = load(e4_folder / "evaluation/evaluation.json")
qualification = load(e4_folder / "qualification/qualification.json")
require(e4["status"] == "EVALUATED" and e4["cases"] == 58, 'e4["status"] == "EVALUATED" and e4["cases"] == 58')
require(e4["selfTests"] == {"status": "PASS", "cases": 16}, 'e4["selfTests"] == {"status": "PASS", "cases": 16}')
require(e4["independentGate"]["verdict"] == "PASS" and e4["independentGate"]["authority"] == "DEMO_ONLY", 'e4["independentGate"]["verdict"] == "PASS" and e4["independentGate"]["authority"] == "DEMO_ONLY"')
require(e4["protectedUnchanged"] and qualification["protectedUnchanged"], 'e4["protectedUnchanged"] and qualification["protectedUnchanged"]')
require(e4["host"]["uid"] == 1000 and e4["host"]["containerEngine"] == "podman", 'e4["host"]["uid"] == 1000 and e4["host"]["containerEngine"] == "podman"')
require(qualification["knownMutantsKilled"] == 3 and qualification["writeScope"]["protectedWritesDenied"] == 3, 'qualification["knownMutantsKilled"] == 3 and qualification["writeScope"]["protectedWritesDenied"] == 3')
require(e4["sourceArchiveSha256"] == records[-1]["sourceArchiveSha256"], 'e4["sourceArchiveSha256"] == records[-1]["sourceArchiveSha256"]')
for name, digest in e4["protectedSha256"].items():
    require(sha(ROOT / "lab" / name) == digest, 'sha(ROOT / "lab" / name) == digest')
summary = {
    "schemaVersion": 1, "classification": "EXECUTED_AZURE_E1_E4_DEMONSTRATIONS_NOT_GLOBAL_ACCEPTANCE",
    "sourceCommit": records[-1]["sourceCommit"], "runs": records,
    "resourceGroup": "rg-book-evidence-20261107", "region": "northeurope", "vmSize": instance["vmSize"],
    "e1": {"controls": "PASS", "workerTransfers": 960},
    "e2": {"controls": "PASS", "matchedWorkloadTransfers": 600, "membershipProviders": 2,
           "fault": "PROCESS_SIGKILL_NOT_PHYSICAL_NODE_LOSS"},
    "e3": {"status": e3["status"], "offers": 720, "persistedCommits": 668,
           "connectionFailures": 48, "missedSchedule": 4, "independentOracle": "PASS",
           "recoveryCommitted": True, "capacityAcceptance": False},
    "e4": {"status": "AZURE_REPLAY_VERIFIED", "candidateSha256": e4["candidateSha256"],
           "modelCallsInThisCampaign": 0, "originalModelCalls": 1, "selfTests": 16,
           "frozenCases": 58, "knownMutantsRejected": 3, "protectedWritesDenied": 3,
           "supervisorUid": 1000, "engine": "podman", "protectedUnchanged": True},
    "retainedFailures": [{"runId": "e4-replay-azure-20261108-01",
                          "reason": "Nonroot Podman inherited root-private working directory; fixed by entering accessible copy before user commands."}],
    "githubActions": "NOT_EXECUTED", "ciRunId": None,
    "limitations": ["One Azure VM; no physical-node HA, TLS/WAN or mainframe comparison.",
                    "E3 synthetic exploratory rates are not approved bank capacity targets.",
                    "E4 replays an existing real model response; no new inference or human-review measurement.",
                    "TODM technical checks cannot substitute for accountable business/release authorization."],
}
path = ROOT / "evidence/runs/azure-e1-e4-2026-11-08.json"
compare_summary(path, summary, write_summary=args.write_summary)
print(json.dumps({"verifiedRuns": len(records), "summary": str(path)}, indent=2))
