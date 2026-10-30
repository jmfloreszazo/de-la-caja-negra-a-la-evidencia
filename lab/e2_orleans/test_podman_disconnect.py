#!/usr/bin/env python3
"""E2-F10-C02: real transport-bridge partition while SQL stays reachable.

This is a disposable single-host Podman experiment. We physically detach
a LIVE Orleans silo from its transport bridge, keep a separate SQL bridge
attached, verify both directions of transport loss with TCP, and measure
reconnection. It does NOT claim multi-host HA or automatic Orleans healing.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
import time

import test_podman_network as fx
from test_e2 import command, postgres_snapshot
from oracle import verify

SQL_NETWORK = "e2f10-sql"
SQL_ADDRESS = "10.78.31.10"
SQL_IPS = {
    "e2f10-pg": SQL_ADDRESS,
    "e2f10-primary": "10.78.31.11",
    "e2f10-secondary": "10.78.31.12",
    "e2f10-client": "10.78.31.13",
}
SQL_DSN = (
    "Host=10.78.31.10;Port=5432;Database=e2lab;"
    "Username=postgres;Password=e2local;Pooling=true;Maximum Pool Size=32;"
    "GSS Encryption Mode=Disable"
)
P = fx.podman
OUT = fx.LAB / "results" / "e2f10" / "c02"
OUT.mkdir(parents=True, exist_ok=True)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def inspect(name):
    data = json.loads(P("inspect", name))[0]
    return {
        "id": data["Id"],
        "pidOnHost": int(data["State"]["Pid"]),
        "status": data["State"]["Status"],
        "networks": {
            key: value["IPAddress"] for key, value in
            data["NetworkSettings"]["Networks"].items()
        },
    }


def check(name):
    raw = P("exec", name, "dotnet", "/app/OrleansLab.dll",
            "cluster", "network-check", timeout=30)
    result = json.loads(raw)
    assert result["status"] == "PROBED"
    assert result["databaseHealthy"] is True
    return result


def wait_transport(name, expected, max_seconds=20):
    last = None
    for _ in range(max_seconds):
        last = check(name)
        assert last["databaseHealthy"] is True
        if (last["primaryGatewayReachable"],
                last["secondaryGatewayReachable"]) == expected:
            return last
        time.sleep(1)
    raise AssertionError(
        "Actual TCP transport state did not match expected isolated/healthy "
        "endpoints: " + json.dumps(last)
    )


def membership():
    return fx.persisted_membership()


def accounting():
    oracle = verify()
    assert len(oracle) == 7 and all(value is True
                                    for value in oracle.values()), oracle
    return {"effects": fx.business_counts(), "oracle": oracle}


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1"
    assert os.environ.get("E1_PG_DSN") and "55435" in os.environ["E1_PG_DSN"]
    assert (fx.APP_DIR / "OrleansLab.dll").is_file()
    fx.CONN = SQL_DSN
    containers = []
    networks = []
    injection = None
    try:
        P("network", "create", "--subnet", "10.78.30.0/24", fx.NETWORK)
        networks.append(fx.NETWORK)
        P("network", "create", "--subnet", "10.78.31.0/24", SQL_NETWORK)
        networks.append(SQL_NETWORK)

        fx.start(
            "e2f10-pg", "-e", "POSTGRES_PASSWORD=e2local",
            "-e", "POSTGRES_DB=e2lab",
            "-p", "127.0.0.1:55435:5432", fx.POSTGRES, app=False
        )
        containers.append("e2f10-pg")
        P("network", "connect", "--ip", SQL_IPS["e2f10-pg"],
          SQL_NETWORK, "e2f10-pg")

        for _ in range(70):
            ready = P("exec", "e2f10-pg", "pg_isready", "-U",
                      "postgres", "-d", "e2lab", check=False)
            if "accepting connections" in ready:
                break
            time.sleep(1)
        else:
            raise AssertionError("Disposable PostgreSQL was not ready")

        fx.reset()
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as setup_schema
        setup_schema()
        initial = postgres_snapshot()

        # Attach the SQL-only bridge BEFORE starting Orleans; the startup
        # delay is explicit so no connection can be attributed to a race.
        for role in ("primary", "secondary"):
            name = "e2f10-" + role
            fx.start(
                name, "--entrypoint", "sh", fx.IMAGE,
                "-c", "sleep 12; exec dotnet /app/OrleansLab.dll cluster silo " + role,
                silo_ip=fx.NODES[name]
            )
            containers.append(name)
            P("network", "connect", "--ip", SQL_IPS[name], SQL_NETWORK, name)
            fx.wait_silo(name, role, seconds=110)

        fx.start("e2f10-client", "--entrypoint", "sleep", fx.IMAGE, "600")
        containers.append("e2f10-client")
        P("network", "connect", "--ip", SQL_IPS["e2f10-client"],
          SQL_NETWORK, "e2f10-client")
        identities = {name: fx.namespace_id(name) for name in containers}
        assert len(set(identities.values())) == 4, identities
        before_states = {name: inspect(name) for name in containers}
        for name in containers:
            assert before_states[name]["status"] == "running"
            assert before_states[name]["networks"][fx.NETWORK] == fx.NODES[name]
            assert before_states[name]["networks"][SQL_NETWORK] == SQL_IPS[name]

        healthy_client = wait_transport("e2f10-client", (True, True))
        healthy_secondary = wait_transport("e2f10-secondary", (True, True))
        first_probe, placements = fx.probe_hosts(True)
        primary_key = next(key for key, host in placements.items()
                           if host == "e2f10-primary")
        secondary_key = next(key for key, host in placements.items()
                             if host == "e2f10-secondary")
        before_membership = membership()
        assert {int(row[2]): int(row[3])
                for row in before_membership["rows"]} == {11150: 3, 11151: 3}

        first = fx.client("execute", [
            command("e2-f10-c02-baseline", primary_key, secondary_key, 10)
        ])
        assert first["results"][0]["status"] == "COMMITTED", first
        before_fault = accounting()
        assert before_fault["effects"] == {
            "committedOperations": 1, "postings": 2, "outboxEvents": 1
        }
        victim_before = inspect("e2f10-secondary")

        # A real bridge DISCONNECT: do NOT stop, pause, kill, restart or
        # remove the Orleans process and do NOT touch the SQL-only bridge.
        injection = {"command": "podman network disconnect",
                     "network": fx.NETWORK, "container": "e2f10-secondary",
                     "disconnectedUtc": stamp(),
                     "monotonicStarted": time.monotonic()}
        P("network", "disconnect", fx.NETWORK, "e2f10-secondary",
          timeout=40)
        cut_state = inspect("e2f10-secondary")
        assert cut_state["id"] == victim_before["id"]
        assert cut_state["pidOnHost"] == victim_before["pidOnHost"]
        assert cut_state["status"] == "running", cut_state
        assert fx.NETWORK not in cut_state["networks"], cut_state
        assert cut_state["networks"][SQL_NETWORK] == SQL_IPS["e2f10-secondary"]
        isolated_client = wait_transport("e2f10-client", (True, False))
        isolated_secondary = wait_transport("e2f10-secondary", (False, False))
        assert isolated_secondary["databaseHealthy"] is True
        assert isolated_client["databaseHealthy"] is True
        isolated_membership = membership()
        isolated_accounting = accounting()
        assert isolated_accounting["effects"] == before_fault["effects"], (
            "Network disruption must not create financial effects"
        )
        assert inspect("e2f10-secondary")["pidOnHost"] == victim_before["pidOnHost"]
        injection["isolationObservedAfterSeconds"] = round(
            time.monotonic() - injection["monotonicStarted"], 3)
        injection["reconnectRequestedUtc"] = stamp()

        P("network", "connect", "--ip", fx.NODES["e2f10-secondary"],
          fx.NETWORK, "e2f10-secondary", timeout=40)
        rejoined = inspect("e2f10-secondary")
        assert rejoined["id"] == victim_before["id"]
        assert rejoined["pidOnHost"] == victim_before["pidOnHost"]
        assert rejoined["status"] == "running"
        assert rejoined["networks"][fx.NETWORK] == fx.NODES["e2f10-secondary"]
        assert rejoined["networks"][SQL_NETWORK] == SQL_IPS["e2f10-secondary"]
        restored_client = wait_transport("e2f10-client", (True, True))
        restored_secondary = wait_transport("e2f10-secondary", (True, True))
        injection["tcpRestoredAfterSeconds"] = round(
            time.monotonic() - injection["monotonicStarted"], 3)
        restored_membership = membership()

        # Only claim SQL correctness and actual endpoint restoration here.
        # Orleans membership may remain Active, mark the silo Dead, or need
        # supervised restart before admitting new grains. Do not rewrite
        # that observation as verified Orleans application recovery.
        final_accounting = accounting()
        assert final_accounting["effects"] == before_fault["effects"]
        assert postgres_snapshot() != initial

        report = {
            "schemaVersion": 1,
            "experiment": "E2-F10-C02-Real-Podman-Transport-Partition",
            "status": "PASS",
            "classification": (
                "LIVE_SILO_NETWORK_DETACH_WITH_SEPARATE_SQL_BRIDGE_"
                "SINGLE_PHYSICAL_CI_HOST"
            ),
            "containerBefore": before_states,
            "networkNamespaceIds": identities,
            "originalOrleansPlacement": placements,
            "sourceAccountPreviouslyOnPrimary": primary_key,
            "sourceAccountPreviouslyOnSecondary": secondary_key,
            "healthyClient": healthy_client,
            "healthySecondary": healthy_secondary,
            "membershipBefore": before_membership,
            "actualInjection": injection,
            "isolatedSiloState": cut_state,
            "isolatedClient": isolated_client,
            "isolatedSecondary": isolated_secondary,
            "membershipDuringPartition": isolated_membership,
            "accountingDuringPartition": isolated_accounting,
            "rejoinedSiloState": rejoined,
            "restoredClient": restored_client,
            "restoredSecondary": restored_secondary,
            "membershipAfterReconnect": restored_membership,
            "accountingAfterReconnect": final_accounting,
            "businessEffectsUnchangedDuringPartition": True,
            "observedOrleansPostReconnectBusinessRecovery": "NOT_TESTED",
            "sources": {
                str(path.relative_to(fx.LAB)): hashlib.sha256(
                    path.read_bytes()).hexdigest()
                for path in (
                    fx.HERE / "test_podman_disconnect.py",
                    fx.HERE / "OrleansLab/ClusterModes.cs",
                    fx.HERE / "test_podman_network.py",
                )
            },
            "limitations": (
                "FOUR Podman network namespaces, TWO separate private bridges, "
                "ONE physical Linux CI host. The Orleans transport bridge was "
                "really detached and restored while the secondary process "
                "and its SQL-only network remained alive. TCP+SQL liveness, "
                "unchanged durable ledger effects, and 7/7 accounting oracle "
                "were observed. This proves neither Orleans automatic service "
                "convergence under split brain nor a cross-physical-node HA "
                "property. No intentionally submitted commands during the "
                "partition, no production RTO, DB HA or mainframe equivalence."
            )
        }
        target = OUT / "e2-f10-c02-transport-partition.json"
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "experiment": report["experiment"],
            "status": report["status"],
            "actualNetworkDisconnect": True,
            "siloPidUnchanged": True,
            "sqlStillReachableDuringPartition": True,
            "clientOrleansTransportBefore": [
                healthy_client["primaryGatewayReachable"],
                healthy_client["secondaryGatewayReachable"],
            ],
            "clientOrleansTransportDuring": [
                isolated_client["primaryGatewayReachable"],
                isolated_client["secondaryGatewayReachable"],
            ],
            "clientOrleansTransportAfter": [
                restored_client["primaryGatewayReachable"],
                restored_client["secondaryGatewayReachable"],
            ],
            "businessEffects": final_accounting["effects"],
            "oracles": final_accounting["oracle"],
            "unverifiedApplicationRecovery": True
        }, indent=2))
    except Exception as exc:
        # MUST preserve raw failure-state evidence BEFORE finally deletes
        # containers and the network. A failed reconnection is not a pass.
        diagnostic = {
            "experiment": "E2-F10-C02-failed-probe",
            "status": "FAIL",
            "timestamp": stamp(),
            "error": repr(exc),
            "injection": injection,
            "containers": {},
            "membership": None,
            "businessEffects": None,
            "oracle": None,
            "notes": (
                "Live containers are inspected before teardown. This is a "
                "failure artifact, not successful partition-recovery proof."
            )
        }
        for node in containers:
            try:
                diagnostic["containers"][node] = {
                    "inspection": inspect(node),
                    "lastLogs": P("logs", node, check=False)[-8000:]
                }
            except Exception as inspect_exc:
                diagnostic["containers"][node] = {
                    "inspectionError": repr(inspect_exc)
                }
        try:
            diagnostic["membership"] = membership()
        except Exception as sql_exc:
            diagnostic["membershipError"] = repr(sql_exc)
        try:
            diagnostic["businessEffects"] = fx.business_counts()
            diagnostic["oracle"] = verify()
        except Exception as oracle_exc:
            diagnostic["oracleError"] = repr(oracle_exc)
        (OUT / "e2-f10-c02-failure-diagnostic.json").write_text(
            json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8"
        )
        raise
    finally:
        for name in reversed(containers):
            P("rm", "-f", name, timeout=45, check=False)
        for name in reversed(networks):
            P("network", "rm", name, timeout=45, check=False)


if __name__ == "__main__":
    main()
