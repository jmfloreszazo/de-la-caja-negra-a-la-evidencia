#!/usr/bin/env python3
"""B05 external-process open-loop replay, independent SQL ledger smoke.

One Linux runner, four separate Podman namespaces (SQL, two silos, client).
Actual durable effects, NOT Orleans acknowledgements, determine correctness.
A 4-second, 20-offers/s reproduction is NOT a sustained capacity benchmark.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone

import test_podman_network as fx
import test_podman_disconnect as c02
from b05_arrival_contract import generate
from oracle_workload import verify

P = fx.podman
OUT = fx.OUT / "b05-smoke"
OUT.mkdir(parents=True, exist_ok=True)
PROFILE_NAMES = ("uniform", "five_percent_hot")
ROUTES = ("direct", "orleans")


def accounts_sql():
    """Independent persistent SQL snapshot; never infer from client ACK."""
    with fx.connect() as db:
        return {
            "accounts": db.execute(
                "SELECT id,balance FROM accounts ORDER BY id").fetchall(),
            "operations": db.execute(
                "SELECT id,src,dst,amount,status FROM operations ORDER BY id"
            ).fetchall(),
            "postings": db.execute(
                "SELECT op,account,delta FROM postings ORDER BY op,account"
            ).fetchall(),
            "outbox": db.execute(
                "SELECT op,event FROM outbox ORDER BY op").fetchall(),
        }


def observed_sql(vector):
    operation_ids = {x["operationId"] for x in vector["operations"]}
    state = accounts_sql()
    matches = {
        "committed": {
            op[0] for op in state["operations"] if op[4] == "COMMITTED"
        },
        "rejected": {
            op[0] for op in state["operations"] if op[4] == "REJECTED"
        },
        "posted": {op[0] for op in state["postings"]},
        "outboxed": {op[0] for op in state["outbox"]},
    }
    assert len(state["accounts"]) == 1000, "Not the required 1000-account fixture"
    assert matches["committed"] == operation_ids, matches
    assert not matches["rejected"], matches
    assert matches["posted"] == operation_ids, matches
    assert matches["outboxed"] == operation_ids, matches
    assert len(state["operations"]) == len(operation_ids), matches
    assert len(state["postings"]) == len(operation_ids) * 2
    assert len(state["outbox"]) == len(operation_ids)
    checks = verify()
    assert len(checks) == 7 and all(checks.values()), checks
    canonical = json.dumps(
        state, separators=(",", ":"), sort_keys=True, default=str
    ).encode("utf-8")
    return {
        "durableCommittedOperationCount": len(matches["committed"]),
        "postingCount": len(state["postings"]),
        "outboxCount": len(state["outbox"]),
        "stateSha256": hashlib.sha256(canonical).hexdigest(),
        "independentSqlOracle": checks
    }


def run_client(route, input_file):
    """One persistent client process per full, route-neutral arrival vector."""
    raw = P(
        "exec", "e2f10-client", "dotnet", "/app/OrleansLab.dll",
        "cluster", "benchmark", route, "replay",
        "/fixtures/b05-smoke/" + input_file.name,
        timeout=170
    )
    result = json.loads(raw)
    assert result["experiment"] == "E2-B05-External-Open-Loop-Smoke", result
    assert result["route"] == route
    assert result["status"] == "OBSERVED_NOT_SUSTAINED_CAPACITY"
    return result


def summarize_client(vector, result):
    offers = vector["operations"]
    samples = result["samples"]
    assert [x["operationId"] for x in samples] == [
        x["operationId"] for x in offers], "Input order or IDs lost"
    assert len(samples) == result["offered"] == len(offers)
    assert result["dispatched"] == len(offers)
    assert result["missed"] == result["ambiguous"] == 0
    assert result["acknowledgedCommitted"] == len(offers)
    latencies_ms = []
    dispatch_lateness_ms = []
    for offer, sample in zip(offers, samples):
        assert sample["scheduledAtNs"] == offer["scheduledAtNs"]
        assert sample["phase"] == offer["phase"]
        assert sample["clientOutcome"] == "ACKNOWLEDGED", sample
        assert sample["ledgerStatus"] == "COMMITTED", sample
        dispatched = sample["dispatchedAtNs"]
        completed = sample["completedAtNs"]
        assert isinstance(dispatched, int) and isinstance(completed, int)
        assert offer["scheduledAtNs"] <= dispatched <= completed
        dispatch_lateness_ms.append(
            (dispatched - offer["scheduledAtNs"]) / 1_000_000
        )
        latencies_ms.append(
            (completed - offer["scheduledAtNs"]) / 1_000_000
        )
    sorted_latency = sorted(latencies_ms)

    def percentile(p):
        rank = (len(sorted_latency) - 1) * p / 100
        low, high = int(rank), min(len(sorted_latency) - 1, int(rank) + 1)
        return round(
            sorted_latency[low] + (sorted_latency[high] - sorted_latency[low])
            * (rank - low), 3
        )

    return {
        "scheduled": len(offers),
        "dispatched": result["dispatched"],
        "missed": result["missed"],
        "ambiguous": result["ambiguous"],
        "acknowledgedCommitted": result["acknowledgedCommitted"],
        "smokeOnlyLatencyFromScheduledMs": {
            "p50": percentile(50), "p95": percentile(95),
            "p99": percentile(99), "max": round(sorted_latency[-1], 3)
        },
        "p95DispatchLatenessMs": round(
            sorted(dispatch_lateness_ms)[int((len(offers) - 1) * .95)], 3
        )
    }


def diagnose(error, step, containers):
    report = {
        "experiment": "E2-B05-External-Client-Open-Loop-Smoke",
        "status": "FAIL",
        "failureStage": step,
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "error": repr(error),
        "classification": "ORIGINAL_NEGATIVE_RUN_NOT_CAPACITY_EVIDENCE",
        "containers": {}
    }
    for name in containers:
        try:
            report["containers"][name] = {
                "inspection": c02.inspect(name),
                "logsTail": P("logs", name, check=False)[-7500:],
            }
        except Exception as inspection_error:
            report["containers"][name] = {
                "diagnosticError": repr(inspection_error)
            }
    try:
        report["sqlSnapshot"] = observed_raw_sql_diagnostic()
    except Exception as sql_error:
        report["sqlInspectionFailure"] = repr(sql_error)
    (OUT / "e2-b05-smoke-original-failure.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


def observed_raw_sql_diagnostic():
    with fx.connect() as db:
        return {
            "operations": db.execute("SELECT COUNT(*) FROM operations").fetchone()[0],
            "postings": db.execute("SELECT COUNT(*) FROM postings").fetchone()[0],
            "outbox": db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0],
            "accounts": db.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
        }


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1"
    assert "55435" in os.environ.get("E1_PG_DSN", "")
    assert fx.APP_DIR.joinpath("OrleansLab.dll").is_file()
    old_conn = fx.CONN
    fx.CONN = c02.SQL_DSN
    containers, networks = [], []
    step = "initialization"
    try:
        for network, subnet in (
            (fx.NETWORK, "10.78.30.0/24"),
            (c02.SQL_NETWORK, "10.78.31.0/24")
        ):
            P("network", "create", "--subnet", subnet, network)
            networks.append(network)

        fx.start(
            "e2f10-pg", "-e", "POSTGRES_PASSWORD=e2local",
            "-e", "POSTGRES_DB=e2lab", "-p", "127.0.0.1:55435:5432",
            fx.POSTGRES, app=False
        )
        containers.append("e2f10-pg")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-pg"],
          c02.SQL_NETWORK, "e2f10-pg")

        step = "postgresql-two-independent-host-sessions"
        readiness = fx.wait_disposable_sql_ready(case="b05", output_dir=OUT)
        assert readiness["status"] == "READY"
        fx.reset()
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as install_membership
        install_membership()

        step = "start-independent-orleans-silos"
        for role in ("primary", "secondary"):
            name = "e2f10-" + role
            fx.start(
                name, "-e", "E2_MAX_ACCOUNT_ID=1000",
                "--entrypoint", "sh", fx.IMAGE, "-c",
                "sleep 12; exec dotnet /app/OrleansLab.dll cluster silo " + role,
                silo_ip=fx.NODES[name]
            )
            containers.append(name)
            P("network", "connect", "--ip", c02.SQL_IPS[name],
              c02.SQL_NETWORK, name)
            fx.wait_silo(name, role, seconds=110)
        fx.start(
            "e2f10-client", "-e", "E2_MAX_ACCOUNT_ID=1000",
            "-e", "E2_B05_SMOKE=1", "--entrypoint", "sleep",
            fx.IMAGE, "600"
        )
        containers.append("e2f10-client")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-client"],
          c02.SQL_NETWORK, "e2f10-client")
        ids = {name: fx.namespace_id(name) for name in containers}
        assert len(set(ids.values())) == 4, ids
        initial = {name: c02.inspect(name) for name in containers}
        for name, inspect in initial.items():
            assert inspect["status"] == "running"
            assert inspect["networks"][fx.NETWORK] == fx.NODES[name]
            assert inspect["networks"][c02.SQL_NETWORK] == c02.SQL_IPS[name]
        membership = fx.persisted_membership()
        assert {int(r[2]): int(r[3]) for r in membership["rows"]} == {
            11150: 3, 11151: 3
        }, membership

        step = "bounded-live-open-loop-replay"
        observations = []
        for profile in PROFILE_NAMES:
            vector = generate(profile, 20, 1, 2, 1, 20261031, 0)
            assert vector["status"] == "GENERATED_NOT_EXECUTED"
            file = OUT / (profile + "-original-input.json")
            file.write_text(
                json.dumps(vector, indent=2) + "\n", encoding="utf-8"
            )
            route_snapshots = []
            for route in ROUTES:
                # The ledger reset is allowed between measured runs, not
                # within them. Membership tables remain alive.
                fx.reset()
                with fx.connect() as db:
                    db.execute(
                        "INSERT INTO accounts(id,balance) "
                        "SELECT n,100000 FROM generate_series(17,1000) n"
                    )
                assert all(verify().values())
                step = "replay-" + profile + "-" + route
                result = run_client(route, file)
                # Preserve every original sample BEFORE assertions; a
                # failed timing contract must remain fully inspectable.
                (OUT / (profile + "-" + route + "-raw-client.json")).write_text(
                    json.dumps(result, indent=2) + "\n", encoding="utf-8"
                )
                client_summary = summarize_client(vector, result)
                sql = observed_sql(vector)
                assert sql["durableCommittedOperationCount"] == len(
                    vector["operations"]
                )
                observation = {
                    "profile": profile, "route": route,
                    "rawClient": result,
                    "clientSummary": client_summary,
                    "independentSql": sql,
                    "offeredVectorSha256": vector["offeredVectorSha256"]
                }
                route_snapshots.append(sql["stateSha256"])
                observations.append(observation)
                (OUT / (profile + "-" + route + "-raw-observation.json")).write_text(
                    json.dumps(observation, indent=2) + "\n", encoding="utf-8"
                )
            assert route_snapshots[0] == route_snapshots[1], (
                "Direct and Orleans durable persisted SQL states differ",
                profile, route_snapshots
            )

        final = {
            "schemaVersion": 1,
            "experiment": "E2-B05-External-Client-Open-Loop-Smoke",
            "status": "PASS_SMOKE_NOT_SUSTAINED_CAPACITY",
            "classification": "FOUR_SECOND_REPLAY_SINGLE_HOST_FOUR_NETNS",
            "timestampUtc": datetime.now(timezone.utc).isoformat(),
            "topology": {
                "physicalHostCount": 1,
                "distinctNetworkNamespaces": ids,
                "primaryAndSecondarySilos": initial,
                "clientRunsInSeparateProcess": True,
                "databaseIsAuthoritative": True,
                "databaseServerIsHA": False
            },
            "sqlStartupReadiness": readiness,
            "adoNetMembership": membership,
            "runs": observations,
            "sourceSha256": {
                str(path.relative_to(fx.LAB)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest() for path in (
                    fx.HERE / "b05_arrival_contract.py",
                    fx.HERE / "test_b05_external_smoke.py",
                    fx.HERE / "OrleansLab/B05LoadClient.cs",
                    fx.HERE / "OrleansLab/ClusterModes.cs",
                    fx.HERE / "OrleansLab/PgDurableLedger.cs",
                    fx.HERE / "oracle_workload.py",
                )
            },
            "limitations": (
                "Exactly two profiles x two routes x 80 scheduled offers = "
                "320 real small requests; all on ONE host with separate "
                "Podman namespaces. This is only a four-second open-loop "
                "functional integration smoke with durable SQL parity and "
                "7/7 independent oracle per run. Client p99 is descriptive "
                "for 80 offers and NOT a sustained capacity percentile. "
                "No capacity saturation, 3+ repetitions, independent physical "
                "load host, production failure domains, Azure TCO or mainframe "
                "MIPS/TPS equivalence."
            )
        }
        (OUT / "e2-b05-smoke-summary.json").write_text(
            json.dumps(final, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "experiment": final["experiment"],
            "status": final["status"],
            "realSmokeRuns": len(observations),
            "totalScheduledOffers": sum(
                x["clientSummary"]["scheduled"] for x in observations
            ),
            "allIndependentOracles": "7/7 each",
            "limitations": final["limitations"]
        }, indent=2))
    except Exception as ex:
        diagnose(ex, step, containers)
        raise
    finally:
        fx.CONN = old_conn
        for name in reversed(containers):
            P("rm", "-f", name, check=False, timeout=60)
        for name in reversed(networks):
            P("network", "rm", name, check=False, timeout=60)


if __name__ == "__main__":
    main()
