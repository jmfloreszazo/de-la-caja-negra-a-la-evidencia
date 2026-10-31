#!/usr/bin/env python3
"""E2-F10-C04: client-side gateway loss with live Orleans silos and SQL.

Use a disposable, four-namespace Podman fixture on ONE physical CI host.
Block only the external client's outbound TCP traffic to one, then both
Orleans gateways; retain SQL and silo-to-silo access throughout. Prove an
independent surviving-gateway path, an unacknowledged request under total
gateway loss, then stable-operation-ID recovery and SQL oracle invariants.

This is NOT proof of in-flight acknowledgement loss, network fencing,
physical HA, an RTO SLA, sustained throughput, or MIPS equivalence.
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
OUT = fx.LAB / "results" / "e2f10" / "c04"
OUT.mkdir(parents=True, exist_ok=True)
GATEWAYS = (
    ("10.78.30.11", "30050"),
    ("10.78.30.12", "30051"),
)
BLOCKED_OPERATION = "e2-f10-c04-unacknowledged"
ONE_GATEWAY_OPERATION = "e2-f10-c04-fallback"
BASELINE_OPERATION = "e2-f10-c04-baseline"


def stamp():
    return c02.stamp()


def helper(*args, timeout=50):
    return P(
        "run", "--rm", "--network", "container:e2f10-client",
        "--cap-add", "NET_ADMIN", "--entrypoint", args[0],
        c02.NET_TOOL_IMAGE, *args[1:], timeout=timeout
    )


def client_check():
    state = json.loads(P(
        "exec", "e2f10-client", "dotnet", "/app/OrleansLab.dll",
        "cluster", "network-check-sql", timeout=30
    ))
    assert state["status"] == "PROBED", state
    assert state["databaseHealthy"] is True, state
    return state


def await_gateways(primary, secondary, timeout=22):
    deadline = time.monotonic() + timeout
    observation = None
    while time.monotonic() < deadline:
        observation = client_check()
        if (
            observation["primaryGatewayReachable"] is primary
            and observation["secondaryGatewayReachable"] is secondary
        ):
            return observation
        time.sleep(0.5)
    raise AssertionError(
        "TCP fault did not produce expected gateway reachability: " +
        json.dumps({"expected": [primary, secondary], "actual": observation})
    )


def rules():
    return helper("iptables", "-w", "3", "-S", "OUTPUT")


def add_drop(index):
    address, port = GATEWAYS[index]
    helper(
        "iptables", "-w", "3", "-I", "OUTPUT", "1",
        "-d", address, "-p", "tcp", "--dport", port, "-j", "DROP"
    )
    observed = rules()
    fragment = "-d " + address + "/32 -p tcp -m tcp --dport " + port + " -j DROP"
    assert fragment in observed, (fragment, observed)
    return observed


def remove_drop(index):
    address, port = GATEWAYS[index]
    helper(
        "iptables", "-w", "3", "-D", "OUTPUT",
        "-d", address, "-p", "tcp", "--dport", port, "-j", "DROP"
    )
    observed = rules()
    fragment = "-d " + address + "/32 -p tcp -m tcp --dport " + port + " -j DROP"
    assert fragment not in observed, observed
    return observed


def count_operation(op_id):
    with fx.connect() as db:
        return {
            "operationRows": db.execute(
                "SELECT COUNT(*) FROM operations WHERE id=%s", (op_id,)
            ).fetchone()[0],
            "postingRows": db.execute(
                "SELECT COUNT(*) FROM postings WHERE op=%s", (op_id,)
            ).fetchone()[0],
            "outboxRows": db.execute(
                "SELECT COUNT(*) FROM outbox WHERE op=%s", (op_id,)
            ).fetchone()[0],
        }


def assert_operation(op_id, expected):
    actual = count_operation(op_id)
    assert actual == expected, (op_id, expected, actual)
    return actual


def accounting():
    oracle = verify()
    assert len(oracle) == 7 and all(x is True for x in oracle.values()), oracle
    return {
        "effects": fx.business_counts(),
        "blockedOperation": count_operation(BLOCKED_OPERATION),
        "independentSqlOracles": oracle,
    }


def membership():
    state = fx.persisted_membership()
    statuses = {int(row[2]): int(row[3]) for row in state["rows"]}
    assert statuses == {11150: 3, 11151: 3}, state
    return state


def failure(stage, error, containers, installed):
    diagnostic = {
        "experiment": "E2-F10-C04-External-Client-Gateway-Loss",
        "status": "FAIL",
        "stage": stage,
        "error": repr(error),
        "timestampUtc": stamp(),
        "installedGatewayDropIndices": sorted(installed),
        "containers": {},
        "classification": "NEGATIVE_OR_INCOMPLETE_NOT_VERIFIED"
    }
    for name in containers:
        try:
            diagnostic["containers"][name] = {
                "inspection": c02.inspect(name),
                "logsTail": P("logs", name, check=False)[-3500:]
            }
        except Exception as ex:
            diagnostic["containers"][name] = {"error": repr(ex)}
    try:
        diagnostic["accounting"] = accounting()
        diagnostic["membership"] = fx.persisted_membership()
    except Exception as ex:
        diagnostic["observerFailure"] = repr(ex)
    try:
        diagnostic["iptablesOutput"] = rules()
    except Exception as ex:
        diagnostic["netfilterFailure"] = repr(ex)
    (OUT / "e2-f10-c04-failure.json").write_text(
        json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8"
    )


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1"
    assert os.environ.get("E1_PG_DSN") and "55435" in os.environ["E1_PG_DSN"]
    assert (fx.APP_DIR / "OrleansLab.dll").is_file()
    old_conn = fx.CONN
    fx.CONN = c02.SQL_DSN
    containers, networks, installed = [], [], set()
    stage = "setup"
    try:
        for network, subnet in (
            (fx.NETWORK, "10.78.30.0/24"),
            (c02.SQL_NETWORK, "10.78.31.0/24")
        ):
            P("network", "create", "--subnet", subnet, network)
            networks.append(network)

        fx.start(
            "e2f10-pg", "-e", "POSTGRES_PASSWORD=e2local",
            "-e", "POSTGRES_DB=e2lab",
            "-p", "127.0.0.1:55435:5432", fx.POSTGRES, app=False
        )
        containers.append("e2f10-pg")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-pg"],
          c02.SQL_NETWORK, "e2f10-pg")
        # Two actual host-side SQL sessions must succeed before the schema
        # reset; pg_isready alone can precede a working host-port connection.
        # This is startup readiness, NOT the C04 gateway-fault result.
        readiness = fx.wait_disposable_sql_ready(case="c04", output_dir=OUT)
        assert readiness["status"] == "READY"
        fx.reset()
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as install_membership
        install_membership()

        for role in ("primary", "secondary"):
            name = "e2f10-" + role
            fx.start(
                name, "--entrypoint", "sh", fx.IMAGE, "-c",
                "sleep 12; exec dotnet /app/OrleansLab.dll cluster silo " + role,
                silo_ip=fx.NODES[name]
            )
            containers.append(name)
            P("network", "connect", "--ip", c02.SQL_IPS[name],
              c02.SQL_NETWORK, name)
            fx.wait_silo(name, role, seconds=110)

        fx.start("e2f10-client", "--entrypoint", "sleep", fx.IMAGE, "600")
        containers.append("e2f10-client")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-client"],
          c02.SQL_NETWORK, "e2f10-client")

        stage = "healthy-baseline"
        namespaces = {name: fx.namespace_id(name) for name in containers}
        assert len(set(namespaces.values())) == 4, namespaces
        before_inspection = {name: c02.inspect(name) for name in containers}
        for name, state in before_inspection.items():
            assert state["status"] == "running"
            assert state["networks"][fx.NETWORK] == fx.NODES[name]
            assert state["networks"][c02.SQL_NETWORK] == c02.SQL_IPS[name]
        initial = await_gateways(True, True)
        before_rules = rules()
        image_id = P("image", "inspect", "-f", "{{.Id}}", c02.NET_TOOL_IMAGE)
        server_probe, placement = fx.probe_hosts(True)
        source = next(k for k, v in placement.items() if v == "e2f10-primary")
        target = next(k for k, v in placement.items() if v == "e2f10-secondary")
        membership_initial = membership()
        baseline = fx.client("execute", [
            command(BASELINE_OPERATION, source, target, 13)
        ])
        assert baseline["results"][0]["status"] == "COMMITTED", baseline
        start_accounting = accounting()
        assert start_accounting["effects"] == {
            "committedOperations": 1, "postings": 2, "outboxEvents": 1
        }, start_accounting
        assert start_accounting["blockedOperation"] == {
            "operationRows": 0, "postingRows": 0, "outboxRows": 0
        }

        # Only the external CLIENT is cut from the PRIMARY gateway.
        # Secondary gateway and both independent silo transports remain up.
        stage = "single-gateway-client-block"
        installed.add(0)
        single_rules = add_drop(0)
        single_probe = await_gateways(False, True)
        assert single_probe["databaseHealthy"] is True
        primary_during = c02.check("e2f10-primary")
        secondary_during = c02.check("e2f10-secondary")
        assert all(
            x["primaryGatewayReachable"] and x["secondaryGatewayReachable"]
            for x in (primary_during, secondary_during)
        ), "Fault must be limited to the external client namespace"

        # A transaction for a grain on primary must be routable through the
        # still-accessible secondary gateway. The ledger is the source of truth.
        fallback = fx.client("execute", [
            command(ONE_GATEWAY_OPERATION, source, target, 17)
        ], timeout=80)
        assert fallback["results"][0]["status"] == "COMMITTED", fallback
        assert fallback["results"][0]["actualSiloNodeIdentity"].startswith(
            "e2f10-primary:"
        ), fallback
        single_accounting = accounting()
        assert single_accounting["effects"] == {
            "committedOperations": 2, "postings": 4, "outboxEvents": 2
        }, single_accounting
        one_gateway_operation = assert_operation(ONE_GATEWAY_OPERATION, {
            "operationRows": 1, "postingRows": 2, "outboxRows": 1
        })
        membership_single = membership()

        # Block the remaining secondary gateway FROM CLIENT ONLY. A fresh
        # client invocation is expected to have no functioning gateway.
        stage = "both-client-gateways-blocked"
        installed.add(1)
        double_rules = add_drop(1)
        all_down = await_gateways(False, False)
        assert all_down["databaseHealthy"] is True
        both_cut_at = stamp()
        during_before = accounting()
        request = command(BLOCKED_OPERATION, source, target, 19)
        failure_observation = None
        try:
            reply = fx.client("execute", [request], timeout=70)
            failure_observation = {
                "kind": "client_response",
                "result": reply,
                "acknowledgedCommitted": any(
                    x["status"] in ("COMMITTED", "DUPLICATE_COMMITTED")
                    for x in reply.get("results", [])
                )
            }
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            failure_observation = {
                "kind": "client_failure_or_timeout",
                "exceptionType": type(error).__name__,
                "cause": repr(error.__cause__)[-7000:],
                "acknowledgedCommitted": False,
                "semantics": "REQUEST_NOT_ACKNOWLEDGED_NO_ROLLBACK_INFERRED"
            }
        assert not failure_observation["acknowledgedCommitted"], failure_observation
        assert failure_observation["kind"] == "client_failure_or_timeout", (
            "A non-COMMITTED response is insufficient proof of gateway loss",
            failure_observation
        )
        cause = failure_observation["cause"].casefold()
        # "OrleansLab.dll" appears in every client command, including
        # unrelated crashes, so matching the project name is NOT evidence.
        expected_transport_diagnostics = (
            "no gateways", "gateway connection", "gateway",
            "system.timeoutexception", "orleansexception",
            "could not connect", "unable to connect"
        )
        assert any(
            marker in cause for marker in expected_transport_diagnostics
        ), (
            "An unrelated client exception must never pass as gateway isolation",
            failure_observation
        )
        during_after = accounting()
        assert during_after == during_before, (
            "No durable effect is permitted during complete client gateway cut",
            during_before, during_after
        )
        assert during_after["blockedOperation"] == {
            "operationRows": 0, "postingRows": 0, "outboxRows": 0
        }
        # A single immediate query could miss delayed effects. Sample SQL
        # repeatedly while BOTH outbound gateway cuts are still active.
        repeated_observations = []
        for _ in range(3):
            time.sleep(1)
            observation = accounting()
            assert observation == during_before, (
                "Unexpected durable SQL change under confirmed gateway cut",
                observation, during_before
            )
            repeated_observations.append(observation)
        membership_cut = membership()
        alive_during = {name: c02.inspect(name) for name in containers}
        for name in containers:
            assert alive_during[name]["id"] == before_inspection[name]["id"]
            assert alive_during[name]["pidOnHost"] == before_inspection[name]["pidOnHost"]
            assert alive_during[name]["status"] == "running"

        stage = "restore-both-client-gateways"
        # Remove in reverse order. The first removal must re-establish only
        # secondary gateway reachability before we restore primary.
        restored_secondary_rule = remove_drop(1)
        installed.remove(1)
        single_after = await_gateways(False, True)
        restored_primary_rule = remove_drop(0)
        installed.remove(0)
        fully_restored = await_gateways(True, True)
        assert fully_restored["databaseHealthy"] is True
        assert membership()["rows"] == membership_initial["rows"]

        stage = "reconcile-identical-operation-id"
        replay = fx.client("execute", [request], timeout=80)
        assert replay["results"][0]["status"] == "COMMITTED", replay
        duplicate = fx.client("execute", [request], timeout=80)
        assert duplicate["results"][0]["status"] == "DUPLICATE_COMMITTED", duplicate
        final = accounting()
        assert final["effects"] == {
            "committedOperations": 3, "postings": 6, "outboxEvents": 3
        }, final
        assert final["blockedOperation"] == {
            "operationRows": 1, "postingRows": 2, "outboxRows": 1
        }, final
        final_baseline = assert_operation(BASELINE_OPERATION, {
            "operationRows": 1, "postingRows": 2, "outboxRows": 1
        })
        final_fallback = assert_operation(ONE_GATEWAY_OPERATION, {
            "operationRows": 1, "postingRows": 2, "outboxRows": 1
        })
        membership_final = membership()
        final_inspection = {name: c02.inspect(name) for name in containers}

        evidence = {
            "schemaVersion": 1,
            "experiment": "E2-F10-C04-External-Client-Gateway-Partition",
            "status": "PASS",
            "classification": "CLIENT_OUTPUT_GATEWAY_DROP_SINGLE_HOST_SQL_PRESERVED",
            "topology": {
                "namespaces": namespaces, "containerStatesBefore": before_inspection,
                "containerStatesDuring": alive_during,
                "containerStatesAfter": final_inspection,
                "privateBridgeCount": 2, "physicalHostCount": 1
            },
            "disposablePostgresStartup": readiness,
            "tool": {"image": c02.NET_TOOL_IMAGE, "id": image_id},
            "clientOutputRulesBefore": before_rules,
            "clientOutputRulesSingleCut": single_rules,
            "clientOutputRulesBothCut": double_rules,
            "clientOutputRulesFirstRestored": restored_secondary_rule,
            "clientOutputRulesFinal": restored_primary_rule,
            "clientNetworkInitial": initial,
            "clientNetworkSingleCut": single_probe,
            "clientNetworkBothCut": all_down,
            "clientNetworkSecondaryRestored": single_after,
            "clientNetworkFullyRestored": fully_restored,
            "siloNetworkDuringClientSingleCut": {
                "primary": primary_during, "secondary": secondary_during
            },
            "sourceGrainOriginalHost": placement[source],
            "sourceAccountId": source,
            "targetAccountId": target,
            "healthyBaseline": baseline["results"],
            "survivingGatewayFinancialResult": fallback["results"],
            "clientAttemptWhenBothGatewaysLost": failure_observation,
            "bothGatewayLossTimestampUtc": both_cut_at,
            "independentSqlInitial": start_accounting,
            "independentSqlSingleGatewayCut": single_accounting,
            "survivingGatewayOperationCardinality": one_gateway_operation,
            "independentSqlBeforeAndDuringFullCut": during_after,
            "repeatedSqlObservationsDuringFullCut": repeated_observations,
            "independentSqlAfterRestore": final,
            "baselineOperationCardinalityAfterRecovery": final_baseline,
            "fallbackOperationCardinalityAfterRecovery": final_fallback,
            "replayStatus": replay["results"][0]["status"],
            "secondReplayStatus": duplicate["results"][0]["status"],
            "membershipBefore": membership_initial,
            "membershipSingleCut": membership_single,
            "membershipBothCut": membership_cut,
            "membershipAfter": membership_final,
            "sourceSha256": {
                str(path.relative_to(fx.LAB)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
                for path in (
                    fx.HERE / "test_client_gateway_partition.py",
                    fx.HERE / "test_podman_network.py",
                    fx.HERE / "test_podman_disconnect.py",
                    fx.HERE / "OrleansLab/ClusterModes.cs"
                )
            },
            "limitations": (
                "This is ONE physical Linux CI host and four namespaces, "
                "NOT independent failure domains or production gateway HA. "
                "A single gateway cut demonstrates fallback for a fresh "
                "client to the surviving gateway; a dual cut can fail during "
                "client startup BEFORE delivery to any grain. Neither cut "
                "proves an in-flight ACK was lost after COMMIT. SQL remains "
                "healthy; no transaction is allowed to commit during a "
                "confirmed full gateway cut. The identical operation ID is "
                "committed once AFTER restoring both gateways and replayed "
                "idempotently. Does not prove multi-host HA, fencing, RTO, "
                "sustained TPS, end-to-end costs or mainframe MIPS."
            )
        }
        (OUT / "e2-f10-c04-client-gateway.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "experiment": evidence["experiment"], "status": "PASS",
            "singleGatewayFallback": fallback["results"][0]["status"],
            "bothGatewayCutSqlHealthy": all_down["databaseHealthy"],
            "clientRequestDuringDualCut": failure_observation["kind"],
            "operationReconciled": replay["results"][0]["status"],
            "idempotentReplay": duplicate["results"][0]["status"],
            "finalSql": final, "limitations": evidence["limitations"]
        }, indent=2))
    except Exception as error:
        failure(stage, error, containers, installed)
        raise
    finally:
        for index in sorted(installed, reverse=True):
            try:
                remove_drop(index)
            except Exception as cleanup_error:
                print("E2_F10_C04_CLEANUP_RULE_FAILED", index, repr(cleanup_error))
        fx.CONN = old_conn
        for name in reversed(containers):
            P("rm", "-f", name, check=False, timeout=60)
        for network in reversed(networks):
            P("network", "rm", network, check=False, timeout=60)


if __name__ == "__main__":
    main()
