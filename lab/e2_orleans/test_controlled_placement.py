#!/usr/bin/env python3
"""C01 controlled alternative: reject one-sided activation; prove recovery.

Never change the historical C01 precondition, accepted grain or SQL ledger.
Each negative/positive case starts a fresh disposable four-namespace fixture.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import test_podman_network as fx
from placement_contract import classify_placement
from test_e2 import command
from oracle import verify

OUT = fx.OUT / "c01-controlled"
OUT.mkdir(parents=True, exist_ok=True)


def utc():
    return datetime.now(timezone.utc).isoformat()


def wait_for(observe, description, timeout=100):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = observe()
        if value:
            return value
        time.sleep(0.5)
    raise AssertionError("Timed out: " + description)


def generations():
    with fx.connect() as db:
        rows = db.execute("SELECT Address,Port,Generation,Status FROM OrleansMembershipTable "
                          "WHERE DeploymentId='e2-f10-podman-bridge' ORDER BY Port,Generation").fetchall()
    return [list(row) for row in rows]


def oracle_counts(expected):
    actual = fx.business_counts()
    assert actual == dict(zip(("committedOperations", "postings", "outboxEvents"), expected)), actual
    oracle = verify()
    assert len(oracle) == 7 and all(value is True for value in oracle.values()), oracle
    return {"effects": actual, "oracle": oracle}


def controlled_probe(mode):
    result = json.loads(fx.podman("exec", "e2f10-client", "dotnet", "/app/OrleansLab.dll",
                                  "cluster", "client", "controlled-probe", mode, timeout=85))
    assert result["status"] == "CONTROLLED_PROBED"
    assert result["financialCommandsDispatched"] == 0 and result["placementHintRetained"] is False
    assert set(map(int, result["accountHostNodes"])) == set(range(1, 17))
    return result


def node_map(probe):
    return {int(key): value.split(":", 1)[0] for key, value in probe["accountHostNodes"].items()}


def exercise(kind, report):
    directory = OUT / kind
    directory.mkdir(exist_ok=True)
    case = {"kind": kind, "status": "STARTED", "startUtc": utc()}
    report["cases"].append(case)
    created, network = [], False
    try:
        fx.podman("network", "create", "--subnet", "10.78.30.0/24", fx.NETWORK)
        network = True
        fx.start("e2f10-pg", "-e", "POSTGRES_PASSWORD=e2local", "-e", "POSTGRES_DB=e2lab",
                 "-p", "127.0.0.1:55435:5432", fx.POSTGRES, app=False)
        created.append("e2f10-pg")
        case["startup"] = fx.wait_disposable_sql_ready(output_dir=directory)
        fx.reset()
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as install_membership
        install_membership()
        for role in ("primary", "secondary"):
            name = "e2f10-" + role
            fx.start(name, "--entrypoint", "dotnet", fx.IMAGE, "/app/OrleansLab.dll",
                     "cluster", "silo", role, silo_ip=fx.NODES[name])
            created.append(name)
            fx.wait_silo(name, role, seconds=110)
            logs = fx.podman("logs", name)
            assert "E2_PLACEMENT_STRATEGY:Orleans.Runtime.ResourceOptimizedPlacement" in logs, logs
            case.setdefault("siloStartupLogs", {})[name] = logs[-5000:]
        fx.start("e2f10-client", "--entrypoint", "sleep", fx.IMAGE, "600")
        created.append("e2f10-client")
        case["namespaces"] = {name: fx.namespace_id(name) for name in created}
        assert len(set(case["namespaces"].values())) == 4
        case["containerIds"] = {name: fx.podman("inspect", "-f", "{{.Id}}", name) for name in created}
        case["hostProcessIds"] = {name: int(fx.podman("inspect", "-f", "{{.State.Pid}}", name)) for name in created}
        assert len(set(case["hostProcessIds"].values())) == 4
        case["images"] = json.loads(fx.podman("image", "inspect", fx.POSTGRES, fx.IMAGE))
        case["membershipBefore"] = fx.persisted_membership()
        case["generationsBefore"] = generations()
        assert {row[2]: row[3] for row in case["membershipBefore"]["rows"]} == {11150: 3, 11151: 3}
        case["initialSql"] = oracle_counts((0, 0, 0))
        mode = "secondary-only" if kind == "negative" else "alternating"
        first = controlled_probe(mode)
        case["firstControlledProbe"] = first
        initial_nodes = node_map(first)
        requested = {int(k): v for k, v in first["requestedNodeNames"].items()}
        assert initial_nodes == requested, (initial_nodes, requested)
        classification = classify_placement(initial_nodes, set(range(1, 17)),
                                            fx.persisted_membership(), require_dual=True)
        case["classification"] = classification
        if kind == "negative":
            assert not classification["placementSatisfiesPrecondition"]
            assert set(initial_nodes.values()) == {"e2f10-secondary"}
            # A new client and different hints cannot relocate existing keys.
            repeated = controlled_probe("alternating")
            case["repeatWithAlternatingHints"] = repeated
            assert node_map(repeated) == initial_nodes
            assert len(set(repeated["requestedNodeNames"].values())) == 2
            again = classify_placement(node_map(repeated), set(range(1, 17)),
                                       fx.persisted_membership(), require_dual=True)
            assert not again["placementSatisfiesPrecondition"]
            case["finalSql"] = oracle_counts((0, 0, 0))
            case["result"] = "EXPECTED_DUAL_PLACEMENT_REJECTION_NO_FINANCIAL_TEST"
        else:
            assert classification["placementSatisfiesPrecondition"]
            assert classification["siloCounts"] == {"e2f10-primary": 8, "e2f10-secondary": 8}
            # All subsequent calls use normal clients with no placement hints.
            ordinary = fx.client("probe")
            assert node_map(ordinary) == initial_nodes
            case["ordinaryClientProbeAfterSeeding"] = ordinary
            result = fx.client("execute", [command("c01-controlled-before-secondary", 2, 1, 10),
                                           command("c01-controlled-before-primary", 1, 2, 20)])
            assert [r["status"] for r in result["results"]] == ["COMMITTED", "COMMITTED"]
            assert [r["actualSiloNodeIdentity"].split(":", 1)[0] for r in result["results"]] == [
                "e2f10-secondary", "e2f10-primary"]
            case["beforeKillResults"] = result
            case["beforeKillSql"] = oracle_counts((2, 4, 2))
            case["killUtc"] = utc()
            fx.podman("kill", "--signal", "SIGKILL", "e2f10-secondary")
            case["secondaryExitCode"] = int(fx.podman("inspect", "-f", "{{.State.ExitCode}}", "e2f10-secondary"))
            assert case["secondaryExitCode"] == 137
            survivor, nodes = fx.probe_hosts(False)
            assert set(nodes.values()) == {"e2f10-primary"} and nodes[2] == "e2f10-primary"
            case["survivorProbe"] = survivor
            case["membershipAfterKill"] = fx.persisted_membership()
            case["generationsAfterKill"] = generations()
            assert {row[2]: row[3] for row in case["membershipAfterKill"]["rows"]} == {11150: 3, 11151: 6}
            assert case["membershipAfterKill"]["version"] > case["membershipBefore"]["version"]
            replay = fx.client("execute", [command("c01-controlled-before-secondary", 2, 1, 10),
                                           command("c01-controlled-after-kill", 2, 1, 5)])
            assert [r["status"] for r in replay["results"]] == ["DUPLICATE_COMMITTED", "COMMITTED"]
            assert all(r["actualSiloNodeIdentity"].startswith("e2f10-primary:") for r in replay["results"])
            case["replayResults"] = replay
            case["afterKillSql"] = oracle_counts((3, 6, 3))
            durable_before_restart = fx.postgres_snapshot()
            old_generation = next(row[2] for row in case["generationsBefore"] if row[1] == 11151)
            # A fresh container means old READY log lines cannot fake restart.
            fx.podman("rm", "-f", "e2f10-secondary")
            fx.start("e2f10-secondary", "--entrypoint", "dotnet", fx.IMAGE,
                     "/app/OrleansLab.dll", "cluster", "silo", "secondary",
                     silo_ip=fx.NODES["e2f10-secondary"])
            fx.wait_silo("e2f10-secondary", "secondary", seconds=110)
            new_id = fx.podman("inspect", "-f", "{{.Id}}", "e2f10-secondary")
            assert new_id != case["containerIds"]["e2f10-secondary"]

            def restarted_membership():
                rows = generations()
                active = [r for r in rows if r[3] == 3]
                return rows if (len(active) == 2 and {r[1] for r in active} == {11150, 11151}
                                and any(r[1] == 11151 and r[2] != old_generation and r[3] == 3 for r in rows)) else None
            case["generationsAfterRestart"] = wait_for(restarted_membership, "fresh secondary Active membership")
            assert any(r[1] == 11151 and r[2] == old_generation and r[3] == 6
                       for r in case["generationsAfterRestart"])
            case["restartedSecondaryContainerId"] = new_id
            case["restartedSecondaryHostPid"] = int(fx.podman("inspect", "-f", "{{.State.Pid}}", "e2f10-secondary"))
            assert case["restartedSecondaryHostPid"] != case["hostProcessIds"]["e2f10-secondary"]
            case["restartObservedUtc"] = utc()
            assert fx.postgres_snapshot() == durable_before_restart
            case["finalSql"] = oracle_counts((3, 6, 3))
            case["result"] = "CONTROLLED_DUAL_PLACEMENT_SIGKILL_REPLAY_AND_FRESH_SECONDARY_REJOIN"
        case["status"] = "PASS"
    finally:
        case["endUtc"] = utc()
        if case["status"] != "PASS":
            fx.preserve_startup_failure("controlled-" + kind, case.get("error", "incomplete"), created)
        for name in reversed(created):
            fx.podman("rm", "-f", name, check=False, timeout=50)
        if network:
            fx.podman("network", "rm", fx.NETWORK, check=False, timeout=50)


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1"
    assert os.environ.get("E1_PG_DSN") == "host=127.0.0.1 port=55435 dbname=e2lab user=postgres password=e2local"
    cohort = os.environ.get("C01_COHORT")
    assert cohort in ("1", "2", "3")
    root = fx.LAB.parent
    paths = [fx.HERE / "test_controlled_placement.py", fx.HERE / "test_podman_network.py",
             fx.HERE / "placement_contract.py", fx.HERE / "OrleansLab/ControlledPlacementProbe.cs",
             fx.HERE / "OrleansLab/ClusterModes.cs", fx.HERE / "OrleansLab/Contracts.cs",
             fx.HERE / "OrleansLab/PgDurableLedger.cs", root / ".github/workflows/e2-c01-controlled.yml"]
    report = {"status": "FAIL", "protocol": "C01_TEST_ONLY_PLACEMENT_HINT_NEGATIVE_POSITIVE_V1",
              "sourceHeadSha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "cohort": cohort, "runnerName": os.environ.get("RUNNER_NAME"), "runnerHost": os.uname().nodename, "startUtc": utc(),
              "cases": [], "physicalHostsPerCase": 1,
              "sourceSha256": {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
              "historicalCauseExplained": False,
              "limitations": "Test-only placement seeding; does not explain original default-policy "
              "concentration, change accepted grain/ledger, prove physical HA, in-flight COMMIT "
              "failure, partitions, RTO SLA, sustained capacity or overall E2 acceptance."}
    try:
        for kind in ("negative", "positive"):
            exercise(kind, report)
        report["status"] = "PASS"
    except Exception as exc:
        report["error"] = repr(exc)
        raise
    finally:
        report["endUtc"] = utc()
        (OUT / "controlled-placement-summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
