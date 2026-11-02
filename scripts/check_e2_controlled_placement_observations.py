#!/usr/bin/env python3
"""Audit three original controlled C01 cohorts without promoting default HA."""
from pathlib import Path
import ast
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "evidence/runs"
SOURCE = "47ed0a087717ec6c02f64a173a63ee597a919f75"
DIGESTS = {
    1: "7b426f22055aa3567b5055f0ba9edf20c975282848d335a5a84f8fc8f1790898",
    2: "451da1a89d243bed2b8d4829ac93c4c4a0feb1b327201658e234098c4a50ccb5",
    3: "da90c8a0be90c534ddd4f5c7eea9474b1cc22f1e243ef5f78be9ea0e193a3dcc",
}
ACCEPTED_CORE = {
    "lab/e2_orleans/OrleansLab/Contracts.cs": "f3afb0096a594e8ec18a29f8775de21ab0df40ebc55c89ad3486ef2f4cc943e0",
    "lab/e2_orleans/OrleansLab/PgDurableLedger.cs": "50f4a26e74ee28f754dd39854098bd4333f8cef2faf2d39d269e38a8db4581ff",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def zipped_original(stem, digest, member_suffix):
    path = RUNS / (stem + ".zip")
    require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, "Original ZIP changed")
    with zipfile.ZipFile(path) as archive:
        members = [n for n in archive.namelist() if n.endswith(member_suffix)]
        require(len(members) == 1, "Ambiguous original summary")
        raw = archive.read(members[0])
        require(raw == (RUNS / (stem + ".json")).read_bytes(), "Original extracted JSON changed")
        return json.loads(raw), archive.read(next(n for n in archive.namelist()
                                                 if n.endswith("provenance.txt"))).decode() if (
            any(n.endswith("provenance.txt") for n in archive.namelist())) else None


def nodes(probe):
    result = {int(k): value.split(":", 1)[0] for k, value in probe["accountHostNodes"].items()}
    require(set(result) == set(range(1, 17)), "Original financial account range changed")
    require(probe["financialCommandsDispatched"] == 0 and probe["placementHintRetained"] is False,
            "Identity probe cannot send financial commands or retain hints")
    return result


def sql(observation, expected):
    require(observation["effects"] == dict(zip(("committedOperations", "postings", "outboxEvents"), expected)),
            "Incorrect durable cardinality")
    require(len(observation["oracle"]) == 7 and all(v is True for v in observation["oracle"].values()),
            "Independent accounting oracle failed")


def main():
    historical, _ = zipped_original("e2-c01-original-one-sided",
        "91e19d4c5e2d84874b0f4c79ce0afde57dae43b9dc1d21a4861bfadfcc5ae097",
        "e2-f10-c01-failure-diagnostic.json")
    require(historical["status"] == "FAIL", "Historical default-placement failure must remain FAIL")
    mapping = ast.literal_eval(re.search(r"Grain placement not achieved: (\{.*\})", historical["error"]).group(1))
    require(set(mapping) == set(range(1, 17)) and set(mapping.values()) == {"e2f10-secondary"},
            "Historical one-sided mapping changed")
    api_path = RUNS / "e2-c01-controlled-jobs-api.json"
    require(hashlib.sha256(api_path.read_bytes()).hexdigest() ==
            "e2ceb01c41f1e043e550581d46237647b2f9e186f7188aecef7ccbc1c95aba6c", "Jobs API snapshot changed")
    jobs = json.loads(api_path.read_text())["jobs"]
    require(len(jobs) == 3 and len({j["runner_id"] for j in jobs}) == 3, "Need three assigned runner jobs")
    require(all(j["status"] == "completed" and j["conclusion"] == "success" and
                j["head_sha"] == SOURCE and j["run_id"] == 41523019075 for j in jobs), "Not three original successes")
    allocated = {j["name"]: j["runner_name"] for j in jobs}
    runner_names, recorded_hosts, initial_container_ids = set(), set(), set()
    for cohort, digest in DIGESTS.items():
        report, provenance = zipped_original(f"e2-c01-controlled-{cohort}-original", digest,
                                              "controlled-placement-summary.json")
        require(report["status"] == "PASS" and report["sourceHeadSha"] == SOURCE and
                report["cohort"] == str(cohort), "Cohort/source mismatch")
        require("source_head_sha=" + SOURCE in provenance and "checkout_sha=" + SOURCE in provenance,
                "Original checkout provenance mismatch")
        require(report["runnerName"] == allocated[f"C01 controlled placement cohort {cohort}"], "Wrong allocated runner")
        runner_names.add(report["runnerName"])
        recorded_hosts.add(report["runnerHost"])
        require(report["physicalHostsPerCase"] == 1 and report["historicalCauseExplained"] is False,
                "Do not promote physical HA or historical root-cause explanation")
        require(all(report["sourceSha256"][p] == h for p, h in ACCEPTED_CORE.items()), "Accepted actor/ledger changed")
        negative, positive = report["cases"]
        require([c["kind"] for c in report["cases"]] == ["negative", "positive"] and
                all(c["status"] == "PASS" for c in report["cases"]), "Incomplete original cases")
        for case in (negative, positive):
            initial_container_ids.update(case["containerIds"].values())
            require(len(set(case["namespaces"].values())) == 4 and len(set(case["hostProcessIds"].values())) == 4,
                    "Missing independent namespace/process observations")
            require({row[2]: row[3] for row in case["membershipBefore"]["rows"]} == {11150: 3, 11151: 3},
                    "Initial membership not two Active silos")
            require(all("E2_PLACEMENT_STRATEGY:Orleans.Runtime.ResourceOptimizedPlacement" in log
                        for log in case["siloStartupLogs"].values()), "Actual default policy not observed")
        require(set(nodes(negative["firstControlledProbe"]).values()) == {"e2f10-secondary"}, "Missing controlled negative")
        require(nodes(negative["repeatWithAlternatingHints"]) == nodes(negative["firstControlledProbe"]),
                "Repeated hints cannot be presented as redistribution")
        require(len(set(negative["repeatWithAlternatingHints"]["requestedNodeNames"].values())) == 2,
                "Second probe did not request alternating targets")
        require(negative["classification"]["placementSatisfiesPrecondition"] is False and
                negative["classification"]["financialTransferTestPerformed"] is False, "Negative misclassified")
        sql(negative["finalSql"], (0, 0, 0))
        expected_nodes = {key: "e2f10-primary" if key % 2 else "e2f10-secondary" for key in range(1, 17)}
        require(nodes(positive["firstControlledProbe"]) == expected_nodes and
                positive["classification"]["siloCounts"] == {"e2f10-primary": 8, "e2f10-secondary": 8},
                "Positive placement is not 8/8")
        require(positive["classification"]["placementSatisfiesPrecondition"] is True, "Positive gate failed")
        require([r["status"] for r in positive["beforeKillResults"]["results"]] == ["COMMITTED", "COMMITTED"],
                "Missing original durable operations")
        sql(positive["beforeKillSql"], (2, 4, 2))
        require(positive["secondaryExitCode"] == 137 and
                all(v.startswith("e2f10-primary:") for v in positive["survivorProbe"]["accountHostNodes"].values()),
                "No real secondary SIGKILL/reactivation proof")
        require([r["status"] for r in positive["replayResults"]["results"]] == ["DUPLICATE_COMMITTED", "COMMITTED"],
                "Stable-ID replay failed")
        sql(positive["afterKillSql"], (3, 6, 3))
        sql(positive["finalSql"], (3, 6, 3))
        old_generation = next(r[2] for r in positive["generationsBefore"] if r[1] == 11151)
        rows = positive["generationsAfterRestart"]
        require(any(r[1:] == [11151, old_generation, 6] for r in rows) and
                any(r[1] == 11151 and r[2] != old_generation and r[3] == 3 for r in rows), "Missing dead/new generation")
        require(positive["restartedSecondaryContainerId"] != positive["containerIds"]["e2f10-secondary"] and
                positive["restartedSecondaryHostPid"] != positive["hostProcessIds"]["e2f10-secondary"],
                "Restart was not a fresh process/container")
    require(len(runner_names) == 3, "Runner allocations not distinct")
    require(len(initial_container_ids) == 24, "The six fixtures must have distinct initial containers")
    print(f"C01 CONTROLLED ORIGINAL AUDIT: PASS (3 runner allocations, {len(recorded_hosts)} hostname label(s); historical cause unknown, E2 partial)")


if __name__ == "__main__":
    main()
