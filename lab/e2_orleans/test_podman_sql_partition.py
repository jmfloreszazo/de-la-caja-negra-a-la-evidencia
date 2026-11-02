#!/usr/bin/env python3
"""E2-F10-C03: isolate a LIVE secondary silo from SQL, not from Orleans.

Two private Podman bridges on one Linux host. Inject real 100% egress loss
on the secondary's SQL interface only. An independent observer must see an
unhealthy fresh SQL probe, healthy APP transport, no unacknowledged durable
effects during the cut, and an unchanged seven-invariant PostgreSQL oracle.

This is NOT proof of multi-host HA, fencing, bounded recovery, or MIPS parity.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import test_podman_network as fx
import test_podman_disconnect as c02
from test_e2 import command
from oracle import verify

P = fx.podman
OUT = fx.LAB / "results" / "e2f10" / "c03"
OUT.mkdir(parents=True, exist_ok=True)
OPERATION = "e2-f10-c03-sql-unavailable"


def network_check(name):
    report = json.loads(P(
        "exec", name, "dotnet", "/app/OrleansLab.dll",
        "cluster", "network-check-sql", timeout=30
    ))
    assert report["status"] == "PROBED", report
    return report


def wait_database(name, expected, timeout=35):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = network_check(name)
        if last["databaseHealthy"] is expected:
            return last
        time.sleep(1)
    raise AssertionError(
        "Fresh SQL probe did not reach expected health: " +
        json.dumps({"name": name, "expected": expected, "last": last})
    )


def victim_sql_interface():
    addresses = c02.net_tool("ip", "-o", "-4", "addr", "show")
    matches = re.findall(
        r"^\s*\d+:\s+([^\s:]+)\s+inet\s+10\.78\.31\.12/",
        addresses, re.MULTILINE
    )
    assert len(matches) == 1 and matches[0] != "lo", addresses
    return matches[0]


def operation_count():
    # The host uses its independent loopback-to-Podman PostgreSQL port.
    with fx.connect() as db:
        return db.execute(
            "SELECT COUNT(*) FROM operations WHERE id=%s", (OPERATION,)
        ).fetchone()[0]


def snapshot():
    oracle = verify()
    assert len(oracle) == 7 and all(v is True for v in oracle.values()), oracle
    return {"businessEffects": fx.business_counts(), "oracle": oracle,
            "isolatedOperationRows": operation_count()}


def diagnostic(stage, error, names, interface):
    report = {
        "experiment": "E2-F10-C03-Live-Silo-SQL-Partition",
        "status": "FAIL", "stage": stage, "error": repr(error),
        "timestamp": c02.stamp(), "interface": interface,
        "classification": "FAILED_RUN_NO_VERIFIED_CLAIM",
        "containers": {}
    }
    for name in names:
        try:
            report["containers"][name] = {
                "inspect": c02.inspect(name),
                "logsTail": P("logs", name, check=False)[-6500:]
            }
        except Exception as ex:
            report["containers"][name] = {"error": repr(ex)}
    try:
        report["ledger"] = snapshot()
        report["sqlMembership"] = fx.persisted_membership()
    except Exception as ex:
        report["databaseInspectionError"] = repr(ex)
    (OUT / "e2-f10-c03-failure.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1", "Explicit opt-in required"
    assert os.environ.get("E1_PG_DSN") and "55435" in os.environ["E1_PG_DSN"]
    assert (fx.APP_DIR / "OrleansLab.dll").is_file()
    names, networks = [], []
    old_connection = fx.CONN
    fx.CONN = c02.SQL_DSN
    stage = "setup"
    interface = None
    active_fault = False
    try:
        for name, subnet in (
            (fx.NETWORK, "10.78.30.0/24"),
            (c02.SQL_NETWORK, "10.78.31.0/24")
        ):
            P("network", "create", "--subnet", subnet, name)
            networks.append(name)

        fx.start("e2f10-pg", "-e", "POSTGRES_PASSWORD=e2local",
                 "-e", "POSTGRES_DB=e2lab",
                 "-p", "127.0.0.1:55435:5432", fx.POSTGRES, app=False)
        names.append("e2f10-pg")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-pg"],
          c02.SQL_NETWORK, "e2f10-pg")
        # Preserve the C03 original SQL-only fault semantics: this startup
        # preflight happens BEFORE the network cut and financial requests.
        fx.wait_disposable_sql_ready(case="c03", output_dir=OUT)
        fx.reset()
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as install
        install()

        for role in ("primary", "secondary"):
            name = "e2f10-" + role
            # SQL network must be attached before first ADO.NET discovery.
            fx.start(
                name, "--entrypoint", "sh", fx.IMAGE, "-c",
                "sleep 12; exec dotnet /app/OrleansLab.dll cluster silo " + role,
                silo_ip=fx.NODES[name]
            )
            names.append(name)
            P("network", "connect", "--ip", c02.SQL_IPS[name],
              c02.SQL_NETWORK, name)
            fx.wait_silo(name, role, seconds=110)

        fx.start("e2f10-client", "--entrypoint", "sleep", fx.IMAGE, "600")
        names.append("e2f10-client")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-client"],
          c02.SQL_NETWORK, "e2f10-client")

        stage = "verify-independent-topology"
        namespaces = {name: fx.namespace_id(name) for name in names}
        assert len(set(namespaces.values())) == 4, namespaces
        inspections = {name: c02.inspect(name) for name in names}
        for name in names:
            assert inspections[name]["status"] == "running"
            assert inspections[name]["networks"][fx.NETWORK] == fx.NODES[name]
            assert inspections[name]["networks"][c02.SQL_NETWORK] == c02.SQL_IPS[name]

        initial_secondary = wait_database("e2f10-secondary", True)
        initial_primary = wait_database("e2f10-primary", True)
        initial_client = wait_database("e2f10-client", True)
        assert all(
            (r["primaryGatewayReachable"], r["secondaryGatewayReachable"])
            == (True, True)
            for r in (initial_secondary, initial_primary, initial_client)
        )

        _, placement = fx.probe_hosts(True)
        source = next(k for k,v in placement.items() if v == "e2f10-secondary")
        target = next(k for k,v in placement.items() if v == "e2f10-primary")
        membership_before = fx.persisted_membership()
        assert {int(r[2]): int(r[3]) for r in membership_before["rows"]} == {
            11150: 3, 11151: 3
        }
        baseline = fx.client("execute", [
            command("e2-f10-c03-before", source, target, 10)
        ])
        assert baseline["results"][0]["status"] == "COMMITTED", baseline
        assert baseline["results"][0]["actualSiloNodeIdentity"].startswith(
            "e2f10-secondary:"
        ), baseline
        before = snapshot()
        assert before["businessEffects"] == {
            "committedOperations": 1, "postings": 2, "outboxEvents": 1
        }, before
        assert before["isolatedOperationRows"] == 0

        stage = "inject-sql-only-packet-loss"
        interface = victim_sql_interface()
        original_qdisc = c02.qdisc(interface)
        image_id = P("image", "inspect", "-f", "{{.Id}}", c02.NET_TOOL_IMAGE)
        fault_start = c02.stamp()
        active_fault = True
        cut_qdisc = c02.inject_loss(interface)

        stage = "verify-live-silo-sql-loss-and-app-preservation"
        secondary_cut = wait_database("e2f10-secondary", False)
        primary_cut = wait_database("e2f10-primary", True)
        client_cut = wait_database("e2f10-client", True)
        assert all(
            (r["primaryGatewayReachable"], r["secondaryGatewayReachable"])
            == (True, True)
            for r in (secondary_cut, primary_cut, client_cut)
        ), "APP bridge must remain reachable during SQL-only isolation"
        victim_cut = c02.inspect("e2f10-secondary")
        assert victim_cut["id"] == inspections["e2f10-secondary"]["id"]
        assert victim_cut["pidOnHost"] == inspections["e2f10-secondary"]["pidOnHost"]
        assert victim_cut["status"] == "running"
        assert victim_cut["networks"] == inspections["e2f10-secondary"]["networks"]

        stage = "attempt-orleans-transaction-under-sql-cut"
        request = command(OPERATION, source, target, 7)
        client_observation = {"acknowledgedCommitted": False}
        try:
            reply = fx.client("execute", [request], timeout=52)
            client_observation = {"kind": "response", "payload": reply,
                                  "acknowledgedCommitted": any(
                                      x["status"] == "COMMITTED"
                                      for x in reply.get("results", [])
                                  )}
        except (RuntimeError, subprocess.TimeoutExpired) as ex:
            # No client acknowledgement is not proof of a rollback: the SQL
            # observer below is authoritative and recovery must replay the ID.
            client_observation = {
                "kind": "client_exception_or_timeout",
                "exceptionType": type(ex).__name__,
                "transportCause": repr(ex.__cause__)[-6000:],
                "acknowledgedCommitted": False,
                "outcomeSemantics": "UNKNOWN_UNTIL_INDEPENDENT_SQL_RECONCILIATION"
            }
        assert not client_observation["acknowledgedCommitted"], client_observation
        # Require actual grain execution rather than only a failed gateway.
        victim_logs = P("logs", "e2f10-secondary", check=False)
        # An Orleans timeout includes the actual remote activation and its
        # running call, even when Npgsql is still waiting and has not yet
        # thrown on the silo. Do not require a premature grain exception.
        transport = client_observation.get("transportCause", "")
        observed_execution = (
            "E2_F10_GRAIN_EXCEPTION:" in victim_logs
            or (
                "System.TimeoutException" in transport
                and "IsExecuting: True" in transport
                and "Activation: S10.78.30.12:" in transport
                and "IAccountGrain.Transfer" in transport
                and (
                    f"account/{source}" in transport
                    or f"account/{source:X}" in transport
                )
            )
        )
        assert observed_execution, (
            "No direct proof that the isolated silo executed the financial call",
            client_observation, victim_logs[-3500:]
        )
        cut_state = snapshot()
        assert cut_state == before, (
            "A durable business effect appeared while its silo SQL was cut",
            before, cut_state
        )
        membership_during = fx.persisted_membership()

        stage = "restore-sql-egress"
        restored_qdisc = c02.clear_loss(interface)
        active_fault = False
        restored_secondary = wait_database("e2f10-secondary", True)
        assert (restored_secondary["primaryGatewayReachable"],
                restored_secondary["secondaryGatewayReachable"]) == (True, True)

        stage = "reconcile-and-replay-stable-operation-id"
        replay = fx.client("execute", [request], timeout=80)
        assert replay["results"][0]["status"] in (
            "COMMITTED", "DUPLICATE_COMMITTED"
        ), replay
        # A previously unacknowledged request may have been queued and then
        # committed after restoration. Both cases must converge to one effect.
        time.sleep(2)
        after = snapshot()
        assert after["isolatedOperationRows"] == 1, after
        assert after["businessEffects"] == {
            "committedOperations": 2, "postings": 4, "outboxEvents": 2
        }, after
        membership_after = fx.persisted_membership()
        remaining = c02.inspect("e2f10-secondary")

        output = {
            "schemaVersion": 1,
            "experiment": "E2-F10-C03-Live-Secondary-SQL-Partition",
            "status": "PASS",
            "classification": "SQL_ONLY_TC_NETEM_CUT_ONE_HOST_NOT_DISTRIBUTED_HA",
            "topology": {"namespaceIds": namespaces,
                         "containerInspectionBefore": inspections},
            "netTool": {"image": c02.NET_TOOL_IMAGE, "imageId": image_id},
            "sqlBridgeInterface": interface,
            "qdiscBefore": original_qdisc,
            "qdiscDuring": cut_qdisc,
            "qdiscAfter": restored_qdisc,
            "faultStartUtc": fault_start,
            "clientBefore": initial_client,
            "secondaryBefore": initial_secondary,
            "secondaryDuring": secondary_cut,
            "primaryDuring": primary_cut,
            "clientDuring": client_cut,
            "secondaryAfter": restored_secondary,
            "sameLiveSiloDuring": victim_cut,
            "sameSiloAfter": remaining,
            "sourceAccountGrainBefore": source,
            "sourceAccountHostBefore": placement[source],
            "clientAttemptDuringSqlLoss": client_observation,
            "independentSqlBefore": before,
            "independentSqlDuring": cut_state,
            "independentSqlAfter": after,
            "sqlMembershipBefore": membership_before,
            "sqlMembershipDuring": membership_during,
            "sqlMembershipAfter": membership_after,
            "replayStatus": replay["results"][0]["status"],
            "sourceSha256": {
                str(path.relative_to(fx.LAB)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in (
                    fx.HERE / "test_podman_sql_partition.py",
                    fx.HERE / "test_podman_disconnect.py",
                    fx.HERE / "test_podman_network.py",
                    fx.HERE / "OrleansLab/ClusterModes.cs",
                    fx.HERE / "OrleansLab/PgDurableLedger.cs"
                )
            },
            "limitations": (
                "One physical GitHub runner, four network namespaces, two "
                "private bridges, one NON-HA SQL container. SQL-only 100% "
                "packet loss on one live silo, an attempted Orleans transfer "
                "and independently observed zero durable effects during "
                "isolation, then one durable stable-ID result after recovery. "
                "Client timeout is never classified as confirmed rollback. "
                "No split-brain/fencing proof, symmetric partition, database "
                "HA, production recovery SLA, sustained TPS or MIPS parity."
            )
        }
        (OUT / "e2-f10-c03-sql-partition.json").write_text(
            json.dumps(output, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "experiment": output["experiment"], "status": "PASS",
            "sqlDuringCut": secondary_cut["databaseHealthy"],
            "appGatewaysRemainReachable": True,
            "businessEffects": after["businessEffects"],
            "replayStatus": output["replayStatus"],
            "oracle": after["oracle"], "limitations": output["limitations"]
        }, indent=2))
    except Exception as ex:
        diagnostic(stage, ex, names, interface)
        raise
    finally:
        if active_fault and interface:
            try:
                c02.net_tool("tc", "qdisc", "del", "dev", interface, "root")
            except Exception as ex:
                print("E2_F10_C03_FAULT_CLEANUP_ERROR", repr(ex))
        fx.CONN = old_connection
        for name in reversed(names):
            P("rm", "-f", name, check=False, timeout=60)
        for name in reversed(networks):
            P("network", "rm", name, check=False, timeout=60)


if __name__ == "__main__":
    main()
