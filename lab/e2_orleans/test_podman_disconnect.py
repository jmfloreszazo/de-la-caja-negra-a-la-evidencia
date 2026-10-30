#!/usr/bin/env python3
"""E2-F10-C02: 100% packet loss on a LIVE silo transport NIC (not detachment).

The Orleans and SQL bridges remain physically configured throughout this
test. The traffic fault is an actual Linux tc/netem qdisc on the victim
container's transport interface, injected by a disposable netshoot helper
sharing its network namespace. A separate SQL bridge remains unaffected.
ONE physical CI host, not independently provisioned fault domains.
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time

import test_podman_network as fx
from test_e2 import command, postgres_snapshot
from oracle import verify

SQL_NETWORK = "e2f10-sql"
SQL_IPS = {
    "e2f10-pg": "10.78.31.10",
    "e2f10-primary": "10.78.31.11",
    "e2f10-secondary": "10.78.31.12",
    "e2f10-client": "10.78.31.13",
}
SQL_DSN = (
    "Host=10.78.31.10;Port=5432;Database=e2lab;"
    "Username=postgres;Password=e2local;Pooling=true;Maximum Pool Size=32;"
    "GSS Encryption Mode=Disable"
)
# A deliberately disposable test-network tool; record its actual image ID.
NET_TOOL_IMAGE = "docker.io/nicolaka/netshoot:v0.13"
OUT = fx.LAB / "results" / "e2f10" / "c02"
OUT.mkdir(parents=True, exist_ok=True)
P = fx.podman


def stamp():
    return datetime.now(timezone.utc).isoformat()


def inspect(name):
    data = json.loads(P("inspect", name))[0]
    return {
        "id": data["Id"],
        "pidOnHost": int(data["State"]["Pid"]),
        "status": data["State"]["Status"],
        "exitCode": int(data["State"]["ExitCode"]),
        "networks": {
            key: value["IPAddress"] for key, value in
            data["NetworkSettings"]["Networks"].items()
        },
    }


def check(name):
    result = json.loads(P(
        "exec", name, "dotnet", "/app/OrleansLab.dll",
        "cluster", "network-check", timeout=32
    ))
    assert result["status"] == "PROBED"
    assert result["databaseHealthy"] is True, (name, result)
    return result


def wait_transport(name, expected, timeout=18):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = check(name)
        assert last["databaseHealthy"] is True
        if (last["primaryGatewayReachable"],
                last["secondaryGatewayReachable"]) == expected:
            return last
        time.sleep(0.4)
    raise AssertionError(
        "TCP did not satisfy observed transport partition/restoration: "
        + json.dumps({"node":name,"expected":expected,"observed":last})
    )


def accounting():
    oracle = verify()
    assert len(oracle) == 7 and all(v is True for v in oracle.values()), oracle
    return {"effects": fx.business_counts(), "oracle": oracle}


def net_tool(command, *args, timeout=90):
    # The helper is never exposed to external addresses. It joins the
    # victim's existing netns without changing its network memberships.
    return P(
        "run", "--rm", "--network", "container:e2f10-secondary",
        "--cap-add", "NET_ADMIN", "--entrypoint", command,
        NET_TOOL_IMAGE, *args, timeout=timeout
    )


def victim_transport_interface():
    output = net_tool("ip", "-o", "-4", "addr", "show")
    matching = []
    for line in output.splitlines():
        matched = re.search(
            r"^\s*\d+:\s+([^\s:]+)\s+inet\s+10\.78\.30\.12/", line
        )
        if matched:
            matching.append(matched.group(1))
    assert len(matching) == 1, (
        "Cannot uniquely identify the victim APP bridge interface", output
    )
    assert matching[0] != "lo", matching
    return matching[0]


def qdisc(dev):
    return net_tool("tc", "qdisc", "show", "dev", dev)


def inject_loss(dev):
    net_tool("tc", "qdisc", "replace", "dev", dev,
             "root", "netem", "loss", "100%")
    observed = qdisc(dev)
    assert "netem" in observed and "loss 100%" in observed, observed
    return observed


def clear_loss(dev):
    net_tool("tc", "qdisc", "del", "dev", dev, "root")
    observed = qdisc(dev)
    assert "netem" not in observed, observed
    return observed


def failure_report(error, containers, stage, fault_dev):
    record = {
        "experiment":"E2-F10-C02-live-silo-packet-loss",
        "status":"FAIL",
        "stage":stage,
        "timestamp":stamp(),
        "error":repr(error),
        "interface":fault_dev,
        "containers":{},
        "sqlMembership":None,
        "businessEffects":None,
        "oracle":None,
        "classification":"ORIGINAL_FAILED_FAULT_EVIDENCE_NOT_ACCEPTED"
    }
    for name in containers:
        try:
            record["containers"][name] = {
                "inspection":inspect(name),
                "lastLogs":P("logs", name, check=False)[-7000:]
            }
        except Exception as exc:
            record["containers"][name] = {"inspectionError":repr(exc)}
    try:
        record["sqlMembership"] = fx.persisted_membership()
        record["businessEffects"] = fx.business_counts()
        record["oracle"] = verify()
    except Exception as exc:
        record["sqlError"] = repr(exc)
    (OUT / "e2-f10-c02-failure-diagnostic.json").write_text(
        json.dumps(record, indent=2)+"\n",encoding="utf-8"
    )


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1"
    assert os.environ.get("E1_PG_DSN") and "55435" in os.environ["E1_PG_DSN"]
    assert (fx.APP_DIR / "OrleansLab.dll").is_file()
    containers = []
    networks = []
    stage = "setup"
    interface = None
    active_fault = False
    old_connection = fx.CONN
    fx.CONN = SQL_DSN
    try:
        for name,subnet in (
            (fx.NETWORK,"10.78.30.0/24"),
            (SQL_NETWORK,"10.78.31.0/24")
        ):
            P("network","create","--subnet",subnet,name)
            networks.append(name)
        fx.start(
            "e2f10-pg", "-e", "POSTGRES_PASSWORD=e2local",
            "-e", "POSTGRES_DB=e2lab",
            "-p", "127.0.0.1:55435:5432", fx.POSTGRES, app=False
        )
        containers.append("e2f10-pg")
        P("network","connect","--ip",SQL_IPS["e2f10-pg"],
          SQL_NETWORK,"e2f10-pg")
        for _ in range(65):
            if "accepting connections" in P(
                "exec","e2f10-pg","pg_isready","-U","postgres",
                "-d","e2lab",check=False
            ):
                break
            time.sleep(1)
        else:
            raise AssertionError("Disposable PostgreSQL not ready")
        fx.reset()
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as install
        install()
        baseline_state = postgres_snapshot()

        # Explicit startup delay is needed because Podman attaches the
        # private SQL-only network BEFORE ADO.NET first opens the database.
        for role in ("primary","secondary"):
            name = "e2f10-" + role
            fx.start(
                name, "--entrypoint","sh",fx.IMAGE,
                "-c","sleep 12; exec dotnet /app/OrleansLab.dll cluster silo "+role,
                silo_ip=fx.NODES[name]
            )
            containers.append(name)
            P("network","connect","--ip",SQL_IPS[name],SQL_NETWORK,name)
            fx.wait_silo(name,role,seconds=110)

        fx.start("e2f10-client","--entrypoint","sleep",fx.IMAGE,"600")
        containers.append("e2f10-client")
        P("network","connect","--ip",SQL_IPS["e2f10-client"],
          SQL_NETWORK,"e2f10-client")
        namespaces = {name:fx.namespace_id(name) for name in containers}
        assert len(set(namespaces.values())) == 4, namespaces
        initial = {name:inspect(name) for name in containers}
        for name,state in initial.items():
            assert state["status"] == "running"
            assert state["networks"][fx.NETWORK] == fx.NODES[name]
            assert state["networks"][SQL_NETWORK] == SQL_IPS[name]
        stage="preflight"
        healthy_client=wait_transport("e2f10-client",(True,True))
        healthy_secondary=wait_transport("e2f10-secondary",(True,True))
        _,placement=fx.probe_hosts(True)
        primary_key=next(k for k,v in placement.items() if v=="e2f10-primary")
        secondary_key=next(k for k,v in placement.items() if v=="e2f10-secondary")
        initial_membership=fx.persisted_membership()
        assert {int(r[2]):int(r[3]) for r in initial_membership["rows"]} == {
            11150:3,11151:3
        }
        first=fx.client("execute",[
            command("e2-f10-c02-baseline",primary_key,secondary_key,10)
        ])
        assert first["results"][0]["status"]=="COMMITTED", first
        before=accounting()
        assert before["effects"]=={
            "committedOperations":1,"postings":2,"outboxEvents":1
        }
        secondary_before=inspect("e2f10-secondary")
        assert secondary_before["pidOnHost"] > 0

        stage="fault-tool-discovery"
        interface=victim_transport_interface()
        before_qdisc=qdisc(interface)
        tool_image_id=P("image","inspect","-f","{{.Id}}",NET_TOOL_IMAGE)

        stage="packet-loss-injection"
        fault_started=time.monotonic()
        fault_utc=stamp()
        # Link and host process are STILL present. Only packets egressing
        # the app bridge are dropped, including SYN-ACK to the client.
        active_fault=True
        during_qdisc=inject_loss(interface)
        stage="during-real-packet-loss"
        isolated_client=wait_transport("e2f10-client",(True,False))
        # The secondary's own local gateway is reachable via loopback
        # kernel routing, while the remote primary gateway is blocked.
        isolated_secondary=wait_transport("e2f10-secondary",(False,True))
        secondary_during=inspect("e2f10-secondary")
        assert secondary_during["status"]=="running",secondary_during
        assert secondary_during["id"]==secondary_before["id"]
        assert secondary_during["pidOnHost"]==secondary_before["pidOnHost"]
        assert secondary_during["networks"]==secondary_before["networks"]
        membership_during=fx.persisted_membership()
        during=accounting()
        assert during["effects"]==before["effects"]
        observed_loss_seconds=round(time.monotonic()-fault_started,3)

        stage="restore-packet-transmission"
        restored_qdisc=clear_loss(interface)
        active_fault=False
        stage="post-recovery"
        restored_client=wait_transport("e2f10-client",(True,True))
        restored_secondary=wait_transport("e2f10-secondary",(True,True))
        secondary_after=inspect("e2f10-secondary")
        assert secondary_after["status"]=="running",secondary_after
        assert secondary_after["id"]==secondary_before["id"]
        assert secondary_after["pidOnHost"]==secondary_before["pidOnHost"]
        assert secondary_after["networks"]==secondary_before["networks"]
        membership_after=fx.persisted_membership()
        final=accounting()
        assert final["effects"]==before["effects"]
        assert postgres_snapshot()!=baseline_state

        output={
            "schemaVersion":1,
            "experiment":"E2-F10-C02-Real-Live-Silo-100Percent-Packet-Loss",
            "status":"PASS",
            "classification":"TC_NETEM_LIVE_SILO_APP_EGRESS_DROP_SQL_PRESERVED_SINGLE_HOST",
            "actualFourNetworkNamespaceIds":namespaces,
            "transportInterfaces":{"victim":interface,
                "qdiscBefore":before_qdisc,
                "qdiscDuring":during_qdisc,
                "qdiscAfter":restored_qdisc},
            "netTool":{"image":NET_TOOL_IMAGE,"actualImageId":tool_image_id},
            "victimBefore":secondary_before,
            "victimDuring":secondary_during,
            "victimAfter":secondary_after,
            "faultStartUtc":fault_utc,
            "secondsToObservePacketLoss":observed_loss_seconds,
            "initialTCP":{"client":healthy_client,"secondary":healthy_secondary},
            "isolatedTCP":{"client":isolated_client,"secondary":isolated_secondary},
            "restoredTCP":{"client":restored_client,"secondary":restored_secondary},
            "sqlReachableDuringFault":True,
            "sqlMembershipBefore":initial_membership,
            "sqlMembershipDuring":membership_during,
            "sqlMembershipAfter":membership_after,
            "businessCountsBefore":before["effects"],
            "businessCountsDuring":during["effects"],
            "businessCountsAfter":final["effects"],
            "sqlOraclesBefore":before["oracle"],
            "sqlOraclesDuring":during["oracle"],
            "sqlOraclesAfter":final["oracle"],
            "orleansApplicationConvergence":"NOT_TESTED",
            "sourceSha256":{
                str(path.relative_to(fx.LAB)):hashlib.sha256(
                    path.read_bytes()).hexdigest()
                for path in (
                    fx.HERE/"test_podman_disconnect.py",
                    fx.HERE/"test_podman_network.py",
                    fx.HERE/"OrleansLab/ClusterModes.cs"
                )
            },
            "limitations":(
                "ONE physical Linux host with four Podman namespaces, "
                "TWO separate private bridges. A Linux tc/netem 100% "
                "egress packet-loss qdisc on the secondary's APP interface "
                "is a real packet fault, NOT podman network disconnect. "
                "The secondary process remains running and its SQL bridge "
                "continues to work. No financial commands are sent during "
                "the fault. This does not test Orleans service convergence, "
                "in-flight effects, split-brain fencing, physical HA, "
                "production recovery SLO, DB HA or mainframe MIPS."
            )
        }
        path=OUT/"e2-f10-c02-packet-loss.json"
        path.write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({
            "experiment":output["experiment"],"status":"PASS",
            "sameLiveSilo":True,"actualPacketLoss":"100%",
            "sqlReachableDuringFault":True,
            "clientBefore":healthy_client,"clientDuring":isolated_client,
            "clientAfter":restored_client,"accounting":final,
            "limitations":output["limitations"]
        },indent=2))
    except Exception as error:
        failure_report(error, containers, stage, interface)
        raise
    finally:
        # Always attempt to restore the live interface before teardown.
        if active_fault and interface:
            try:
                net_tool("tc","qdisc","del","dev",interface,"root")
            except Exception as recovery_error:
                print("E2_F10_C02_FAULT_CLEANUP_FAILED:",repr(recovery_error))
        fx.CONN=old_connection
        for name in reversed(containers):
            P("rm","-f",name,check=False,timeout=60)
        for name in reversed(networks):
            P("network","rm",name,check=False,timeout=60)


if __name__ == "__main__":
    main()
