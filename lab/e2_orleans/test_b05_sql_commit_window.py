#!/usr/bin/env python3
"""B05 60-second independent PostgreSQL COMMIT-timestamp pilot, not capacity.

One Linux runner, four separate Podman namespaces (SQL, two silos, client).
Actual durable effects, NOT Orleans acknowledgements, determine correctness.
Each test uses 60 measured seconds, 1 warmup, 1 cooldown. PostgreSQL 16
track_commit_timestamp is explicitly enabled in disposable Podman.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime, timezone, timedelta

import test_podman_network as fx
import test_podman_disconnect as c02
from b05_arrival_contract import generate
from oracle_workload import verify

P = fx.podman
OUT = fx.OUT / "b05-commit-window"
OUT.mkdir(parents=True, exist_ok=True)
PROFILE_NAMES = ("uniform", "five_percent_hot")
ROUTES = ("direct", "orleans")
RATES = (20,)
REPETITIONS = (0,)
WARMUP_SECONDS = 1
MEASUREMENT_SECONDS = 60
COOLDOWN_SECONDS = 1


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
        "/fixtures/b05-commit-window/" + input_file.name,
        timeout=170
    )
    result = json.loads(raw)
    assert result["experiment"] == "E2-B05-Independent-SQL-Commit-Window", result
    assert result["route"] == route
    assert result["status"] == "OBSERVED_COMMIT_WINDOW_PROBE_NOT_CAPACITY"
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
        "experiment": "E2-B05-Independent-SQL-Commit-Window",
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
    (OUT / "e2-b05-commit-window-original-failure.json").write_text(
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


def independent_commit_clock_check():
    """A bounded, same-Linux-host wall-clock sample; fail on clock drift."""
    before = datetime.now(timezone.utc)
    with fx.connect() as db:
        mode = db.execute("SHOW track_commit_timestamp").fetchone()[0]
        db_clock = db.execute("SELECT clock_timestamp()").fetchone()[0]
    after = datetime.now(timezone.utc)
    assert mode == "on", ("PostgreSQL commit tracking disabled", mode)
    assert before - timedelta(milliseconds=100) <= db_clock <= (
        after + timedelta(milliseconds=100)
    ), ("Clock skew: client and PostgreSQL wall clocks not comparable",
        before.isoformat(), db_clock.isoformat(), after.isoformat())
    return {
        "hostUtcBefore": before.isoformat(),
        "serverUtc": db_clock.isoformat(),
        "hostUtcAfter": after.isoformat(),
        "postgresTrackCommitTimestamp": mode,
        "maximumAllowedClockSkewMs": 100,
        "topologyAssumption": "SAME_PHYSICAL_LINUX_HOST_ONLY"
    }


def committed_inside_window(vector, result):
    """Authoritative SQL COMMIT timestamps, not client ACK completion times.

    The monotonic zero lies within a wall-clock UTC capture bracket.
    Conservative min/max counts handle bracket uncertainty rather than
    inventing a perfectly synchronized beginning/end of measurement.
    """
    before = datetime.fromisoformat(result["clockOriginUtcBefore"])
    after = datetime.fromisoformat(result["clockOriginUtcAfter"])
    assert before.tzinfo is not None and after.tzinfo is not None
    assert before <= after and (after - before).total_seconds() < .1
    t0 = before + timedelta(seconds=WARMUP_SECONDS)
    t1 = after + timedelta(seconds=WARMUP_SECONDS)
    t2 = before + timedelta(seconds=WARMUP_SECONDS + MEASUREMENT_SECONDS)
    t3 = after + timedelta(seconds=WARMUP_SECONDS + MEASUREMENT_SECONDS)
    allowed_ids = {o["operationId"] for o in vector["operations"]}
    phase_by_id = {
        o["operationId"]: o["phase"] for o in vector["operations"]
    }
    measurement_ids = {
        op_id for op_id, phase in phase_by_id.items()
        if phase == "measurement"
    }
    with fx.connect() as db:
        assert db.execute(
            "SHOW track_commit_timestamp").fetchone()[0] == "on"
        rows = db.execute(
            "SELECT id, pg_xact_commit_timestamp(xmin) "
            "FROM operations WHERE status='COMMITTED' ORDER BY id"
        ).fetchall()
    assert len(rows) == len(allowed_ids)
    assert {row[0] for row in rows} == allowed_ids
    assert all(row[1] is not None for row in rows), (
        "Missing server-recorded commit timestamp; cannot claim in-window rate"
    )
    # A deliberate rollback/retry may produce no row, but this scenario
    # explicitly requires ALL unique IDs durably COMMITTED by run end.
    strict = sum(t1 <= timestamp < t2 for _, timestamp in rows)
    possible = sum(t0 <= timestamp < t3 for _, timestamp in rows)
    measurement_strict = sum(
        op_id in measurement_ids and t1 <= timestamp < t2
        for op_id, timestamp in rows
    )
    measurement_possible = sum(
        op_id in measurement_ids and t0 <= timestamp < t3
        for op_id, timestamp in rows
    )
    assert 0 <= strict <= possible <= len(rows)
    assert 0 <= measurement_strict <= measurement_possible <= len(measurement_ids)
    return {
        "source": "postgresql-16-pg_xact_commit_timestamp(operations.xmin)",
        "serverConfig": "track_commit_timestamp=on",
        "clockAlignment": "one-linux-host-utc-bracket-plus-server-clock-samples",
        "timeBoundaryUncertaintySeconds": round((after - before).total_seconds(), 6),
        "certainWindowStartUtc": t1.isoformat(),
        "certainWindowEndUtc": t2.isoformat(),
        "possibleWindowStartUtc": t0.isoformat(),
        "possibleWindowEndUtc": t3.isoformat(),
        "measurementDurationSeconds": MEASUREMENT_SECONDS,
        "allDurableCommitTimestampsPresent": True,
        "originalServerCommitTimestampsByOperation": [
            {
                "operationId": op_id,
                "sourcePhase": phase_by_id[op_id],
                "postgresCommitTimestampUtc": committed_at.isoformat()
            }
            for op_id, committed_at in rows
        ],
        "serverCommitsCertainlyWithinWindow": strict,
        "serverCommitsPossiblyWithinWindow": possible,
        "certainServerCommitsPerMeasurementSecond": round(
            strict / MEASUREMENT_SECONDS, 4
        ),
        "possibleServerCommitsPerMeasurementSecond": round(
            possible / MEASUREMENT_SECONDS, 4
        ),
        "measurementPhaseIntents": len(measurement_ids),
        "measurementPhaseCommitsCertainInsideWindow": measurement_strict,
        "measurementPhaseCommitsPossibleInsideWindow": measurement_possible,
        "measurementPhaseDurableByRunEnd": len(measurement_ids),
        "commitTimestampOrigin": "server-UTC-transaction-commit-not-client-ACK",
        "limits": (
            "The database server and client share one physical Linux wall "
            "clock; this is not a distributed clock-alignment or sustainable "
            "capacity proof. PostgreSQL commit timestamp availability "
            "depends on track_commit_timestamp and surviving xid history."
        ),
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
            fx.POSTGRES, "postgres", "-c",
            "track_commit_timestamp=on", app=False
        )
        containers.append("e2f10-pg")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-pg"],
          c02.SQL_NETWORK, "e2f10-pg")

        step = "postgresql-two-independent-host-sessions"
        readiness = fx.wait_disposable_sql_ready(case="b05", output_dir=OUT)
        assert readiness["status"] == "READY"
        fx.reset()
        postgresql_clock_before = independent_commit_clock_check()
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
            "-e", "E2_B05_SMOKE=1", "-e", "E2_B05_COMMIT_WINDOW=1",
            "--entrypoint", "sleep",
            fx.IMAGE, "900"
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

        step = "bounded-single-rate-60-second-postgres-commit-window"
        observations = []
        for profile in PROFILE_NAMES:
            for offered_rate in RATES:
                for repetition in REPETITIONS:
                    vector = generate(
                        profile, offered_rate, WARMUP_SECONDS,
                        MEASUREMENT_SECONDS, COOLDOWN_SECONDS,
                        20261031, repetition
                    )
                    assert vector["status"] == "GENERATED_NOT_EXECUTED"
                    trial_id = (
                        profile + "-" + str(offered_rate) + "tps-r"
                        + str(repetition)
                    )
                    input_file = OUT / (trial_id + "-input.json")
                    input_file.write_text(
                        json.dumps(vector, indent=2) + "\n",
                        encoding="utf-8"
                    )
                    route_snapshots = []
                    for route in ROUTES:
                        # Reset only BETWEEN trials; no hidden retries or
                        # database reset inside a measured workload.
                        fx.reset()
                        with fx.connect() as db:
                            db.execute(
                                "INSERT INTO accounts(id,balance) "
                                "SELECT n,100000 FROM generate_series(17,1000) n"
                            )
                        assert len(verify()) == 7 and all(verify().values())
                        step = "replay-" + trial_id + "-" + route
                        result = run_client(route, input_file)
                        # Archive raw client samples before every possible
                        # accounting/timing assertion (including failures).
                        raw_file = OUT / (trial_id + "-" + route + "-client.json")
                        raw_file.write_text(
                            json.dumps(result, indent=2) + "\n",
                            encoding="utf-8"
                        )
                        client_summary = summarize_client(vector, result)
                        sql = observed_sql(vector)
                        postgres_commit_window = committed_inside_window(vector, result)
                        postgresql_clock_after = independent_commit_clock_check()
                        assert sql["durableCommittedOperationCount"] == len(
                            vector["operations"]
                        )
                        measurement = [
                            sample for sample in result["samples"]
                            if sample["phase"] == "measurement"
                        ]
                        assert len(measurement) == (
                            offered_rate * MEASUREMENT_SECONDS
                        )
                        assert all(
                            sample["clientOutcome"] == "ACKNOWLEDGED"
                            and sample["ledgerStatus"] == "COMMITTED"
                            for sample in measurement
                        ), measurement
                        # The numerator is independently reconciled SQL at
                        # run end; it is NOT the measured in-window COMMIT rate.
                        observation = {
                            "profile": profile,
                            "offeredRatePerSecond": offered_rate,
                            "repetition": repetition,
                            "route": route,
                            "offeredVectorSha256": vector["offeredVectorSha256"],
                            "rawClient": result,
                            "clientSummary": client_summary,
                            "measurementPhaseScheduledOffers": len(measurement),
                            "measurementPhaseDurationSeconds": MEASUREMENT_SECONDS,
                            "measurementPhaseDurableByRunEnd": len(measurement),
                            "serverRecordedCommitWindow": postgres_commit_window,
                            "serverClockAfterTrial": postgresql_clock_after,
                            "independentSql": sql
                        }
                        route_snapshots.append(sql["stateSha256"])
                        observations.append(observation)
                        (
                            OUT / (trial_id + "-" + route + "-observation.json")
                        ).write_text(
                            json.dumps(observation, indent=2) + "\n",
                            encoding="utf-8"
                        )
                    assert route_snapshots[0] == route_snapshots[1], (
                        "Matched direct and Orleans persistent SQL state differs",
                        trial_id, route_snapshots
                    )

        final = {
            "schemaVersion": 1,
            "experiment": "E2-B05-Independent-SQL-Commit-Window",
            "status": "PASS_60_SECOND_COMMIT_TIMESTAMP_SLICE_NOT_CAPACITY",
            "capacityEvidence": False,
            "classification": "FOUR_60_SECOND_TRIALS_ONE_PHYSICAL_HOST",
            "timestampUtc": datetime.now(timezone.utc).isoformat(),
            "predeclared": {
                "profiles": list(PROFILE_NAMES),
                "offeredRatesPerSecond": list(RATES),
                "routes": list(ROUTES),
                "repetitionsPerPoint": len(REPETITIONS),
                "warmupSeconds": WARMUP_SECONDS,
                "measurementSeconds": MEASUREMENT_SECONDS,
                "cooldownSeconds": COOLDOWN_SECONDS,
                "maximumClientInFlight": 32,
                "clientClockWallBracketing": True,
                "postgresCommitTimestampsIndependentOfClientAck": True
            },
            "topology": {
                "physicalHostCount": 1,
                "distinctPodmanNetworkNamespaces": ids,
                "primaryAndSecondarySilos": initial,
                "clientRunsInSeparateProcess": True,
                "databaseIsAuthoritative": True,
                "databaseServerIsHA": False
            },
            "postgresqlStartupClockComparison": postgresql_clock_before,
            "sqlStartupReadiness": readiness,
            "adoNetMembership": membership,
            "runs": observations,
            "sourceSha256": {
                str(path.relative_to(fx.LAB)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest() for path in (
                    fx.HERE / "b05_arrival_contract.py",
                    fx.HERE / "test_b05_sql_commit_window.py",
                    fx.HERE / "test_b05_repeatability.py",
                    fx.HERE / "OrleansLab/B05LoadClient.cs",
                    fx.HERE / "OrleansLab/ClusterModes.cs",
                    fx.HERE / "OrleansLab/PgDurableLedger.cs",
                    fx.HERE / "oracle_workload.py"
                )
            },
            "limitations": (
                "Only four 62-second trials, each with sixty measurement "
                "seconds at one 20-intents-per-second offered load, and "
                "ONE physical Linux runner. PostgreSQL transaction commit "
                "timestamps are independently read and counted in a "
                "conservative UTC bracket under same-host clock checks; "
                "this is NOT an independently hosted reference timestamp "
                "or production SLO. No saturation sweep, 3+ independent "
                "cohorts, cross-host HA, Azure TCO or mainframe MIPS parity."
            )
        }
        (OUT / "e2-b05-commit-window-summary.json").write_text(
            json.dumps(final, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "experiment": final["experiment"],
            "status": final["status"],
            "independentlyTimedCommitRuns": len(observations),
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
