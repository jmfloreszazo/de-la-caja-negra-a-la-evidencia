#!/usr/bin/env python3
"""Four original 60s hot-key trials at 40/80 offered/s, not capacity proof.

Actual COMMIT timestamps are independent PostgreSQL evidence. Overload
loss/ambiguity is retained as an observed result, never silently retried.
Any broken SQL invariant, accounting cardinality or impossible ACK fails CI.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

import test_b05_sql_commit_window as base
import test_podman_network as fx
import test_podman_disconnect as c02
from b05_arrival_contract import generate
from b05_sweep_analysis import summarize
from oracle_workload import verify

P = fx.podman
OUT = fx.OUT / "b05-sweep-40-80"
OUT.mkdir(parents=True, exist_ok=True)
PROFILE = "five_percent_hot"
RATES = (40, 80)
ROUTES = ("direct", "orleans")
WARMUP_SECONDS = 1
MEASUREMENT_SECONDS = 60
COOLDOWN_SECONDS = 1


def sql_state():
    """SQL is the authority even if the client reports a timeout/exception."""
    state = base.accounts_sql()
    assert len(state["accounts"]) == 1000
    checks = verify()
    assert len(checks) == 7 and all(checks.values()), checks
    with fx.connect() as db:
        assert db.execute("SHOW track_commit_timestamp").fetchone()[0] == "on"
        rows = db.execute(
            "SELECT id,status,pg_xact_commit_timestamp(xmin) "
            "FROM operations ORDER BY id"
        ).fetchall()
    canonical = json.dumps(
        state, separators=(",", ":"), sort_keys=True, default=str
    ).encode("utf-8")
    return {
        "operations": rows,
        "postings": state["postings"],
        "outbox": state["outbox"],
        "stateSha256": hashlib.sha256(canonical).hexdigest(),
        "sevenOracles": checks
    }


def pg_database_counters():
    """Supplemental whole-database counters, NOT business COMMIT counts."""
    with fx.connect() as db:
        record = db.execute(
            "SELECT xact_commit,xact_rollback,deadlocks,blks_read,"
            "blks_hit,temp_files,tup_inserted "
            "FROM pg_stat_database WHERE datname='e2lab'"
        ).fetchone()
        assert record is not None
    names = ("xactCommitAllSessions", "xactRollbackAllSessions",
             "deadlocks", "blocksRead", "blocksHit",
             "tempFiles", "tuplesInserted")
    return dict(zip(names, map(int, record)))


def run_client(route, vector_path):
    raw = P(
        "exec", "e2f10-client", "dotnet", "/app/OrleansLab.dll",
        "cluster", "benchmark", route, "replay",
        "/fixtures/b05-sweep-40-80/" + vector_path.name,
        timeout=195
    )
    result = json.loads(raw)
    assert result["experiment"] == "E2-B05-Independent-SQL-Commit-Window"
    assert result["status"] == "OBSERVED_COMMIT_WINDOW_PROBE_NOT_CAPACITY"
    assert result["route"] == route
    return result


def original_failure(error, stage, containers):
    # Failure snapshots are never a PASS artifact.
    details = {
        "experiment": "E2-B05-40-80-Offer-Rate-Sweep",
        "status": "ORIGINAL_FAIL_NOT_CAPACITY",
        "stage": stage,
        "error": repr(error),
        "timestampUtc": datetime.now(timezone.utc).isoformat(),
        "rawClientTracesPreservedBeforeSubsequentOracleChecks": True,
        "containers": {},
    }
    for name in containers:
        try:
            details["containers"][name] = {
                "inspect": c02.inspect(name),
                "logsTail": P("logs", name, check=False)[-8000:]
            }
        except Exception as inspection_error:
            details["containers"][name] = {
                "inspectionError": repr(inspection_error)
            }
    (OUT / "b05-sweep-original-failure.json").write_text(
        json.dumps(details, indent=2, default=str) + "\n",
        encoding="utf-8"
    )


def main():
    assert os.environ.get("E2_NETWORK_TEST") == "1"
    assert "55435" in os.environ.get("E1_PG_DSN", "")
    assert fx.APP_DIR.joinpath("OrleansLab.dll").is_file()
    old_conn = fx.CONN
    fx.CONN = c02.SQL_DSN
    containers, networks = [], []
    stage = "initialize"
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
        stage = "independent-sql-startup"
        readiness = fx.wait_disposable_sql_ready(case="b05", output_dir=OUT)
        fx.reset()
        clock_before = base.independent_commit_clock_check()
        os.environ["E2_POSTGRES_CONTAINER"] = "e2f10-pg"
        from setup_adonet_membership import main as install_membership
        install_membership()

        stage = "two-silos"
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
            "--entrypoint", "sleep", fx.IMAGE, "900"
        )
        containers.append("e2f10-client")
        P("network", "connect", "--ip", c02.SQL_IPS["e2f10-client"],
          c02.SQL_NETWORK, "e2f10-client")
        namespaces = {n: fx.namespace_id(n) for n in containers}
        assert len(set(namespaces.values())) == 4, namespaces
        membership = fx.persisted_membership()
        assert {int(row[2]): int(row[3]) for row in membership["rows"]} == {
            11150: 3, 11151: 3
        }

        observations = []
        for rate in RATES:
            vector = generate(
                PROFILE, rate, WARMUP_SECONDS, MEASUREMENT_SECONDS,
                COOLDOWN_SECONDS, 20261031, 0
            )
            assert vector["totalOfferedRequests"] == rate * 62
            input_file = OUT / (f"{PROFILE}-{rate}tps-r0-input.json")
            input_file.write_text(
                json.dumps(vector, indent=2) + "\n", encoding="utf-8"
            )
            paired = {}
            for route in ROUTES:
                stage = f"{rate}-offered-per-second-{route}"
                # Between trials only. There is NO retry of financial work.
                fx.reset()
                with fx.connect() as db:
                    db.execute(
                        "INSERT INTO accounts(id,balance) "
                        "SELECT n,100000 FROM generate_series(17,1000) n"
                    )
                checks = verify()
                assert len(checks) == 7 and all(checks.values()), checks
                stats_before = pg_database_counters()
                client = run_client(route, input_file)
                # Always preserve the original client output BEFORE checking
                # any offered/ACK/durable sample outcome.
                (OUT / f"{PROFILE}-{rate}tps-r0-{route}-client.json").write_text(
                    json.dumps(client, indent=2) + "\n", encoding="utf-8"
                )
                sql = sql_state()
                result = summarize(
                    vector, client, sql["operations"], sql["postings"],
                    sql["outbox"], sql["sevenOracles"]
                )
                stats_after = pg_database_counters()
                clock_after = base.independent_commit_clock_check()
                assert result["offered"] == rate * 62
                assert result["measurementPhaseOffered"] == rate * 60
                assert result["capacityEvidence"] is False
                observation = {
                    "profile": PROFILE,
                    "route": route,
                    "offeredRatePerSecond": rate,
                    "repetition": 0,
                    "sourceVectorSha256": vector["offeredVectorSha256"],
                    "originalClient": client,
                    "originalIndependentResult": result,
                    "independentSqlStateSha256": sql["stateSha256"],
                    "sqlDatabaseCountersBefore": stats_before,
                    "sqlDatabaseCountersAfter": stats_after,
                    "sqlClockAfter": clock_after
                }
                (OUT / f"{PROFILE}-{rate}tps-r0-{route}-observation.json").write_text(
                    json.dumps(observation, indent=2) + "\n", encoding="utf-8"
                )
                paired[route] = observation
                observations.append(observation)

            assert paired["direct"]["sourceVectorSha256"] == (
                paired["orleans"]["sourceVectorSha256"]
            )
            if all(
                row["originalIndependentResult"]["sqlDurableCommittedByRunEnd"]
                == row["originalIndependentResult"]["offered"]
                for row in paired.values()
            ):
                # Only fully durably completed matched trials have a
                # comparable identical ledger state. Failure/overload is
                # an observation, not a fabricated equivalence pass.
                assert paired["direct"]["independentSqlStateSha256"] == (
                    paired["orleans"]["independentSqlStateSha256"]
                ), ("Complete-workload route parity failed", rate)

        final = {
            "schemaVersion": 1,
            "experiment": "E2-B05-40-80-Offer-Rate-Sweep",
            "status": "OBSERVED_BOUNDED_SWEEP_WITH_SQL_ORACLES_NOT_CAPACITY",
            "capacityEvidence": False,
            "sourceCommitHashes": {
                str(path.relative_to(fx.LAB)): hashlib.sha256(
                    path.read_bytes()
                ).hexdigest() for path in (
                    fx.HERE / "b05_sweep_analysis.py",
                    fx.HERE / "test_b05_rate_sweep.py",
                    fx.HERE / "b05_arrival_contract.py",
                    fx.HERE / "OrleansLab/B05LoadClient.cs",
                    fx.HERE / "OrleansLab/PgDurableLedger.cs",
                    fx.HERE / "oracle_workload.py",
                )
            },
            "predeclared": {
                "profile": PROFILE, "routes": list(ROUTES),
                "ratesOfferedPerSecond": list(RATES),
                "repetitionsPerRateAndRoute": 1,
                "warmupSeconds": WARMUP_SECONDS,
                "measurementSeconds": MEASUREMENT_SECONDS,
                "cooldownSeconds": COOLDOWN_SECONDS,
                "clientMaximumInFlight": 32,
                "expectedScheduledOffers": sum(
                    rate * (WARMUP_SECONDS + MEASUREMENT_SECONDS + COOLDOWN_SECONDS)
                    * len(ROUTES) for rate in RATES
                )
            },
            "topology": {
                "physicalLinuxHostCount": 1,
                "podmanNetworkNamespaces": namespaces,
                "twoSilosPersistentThroughTrialSeries": True,
                "databaseIsAuthoritative": True,
                "databaseIsHA": False
            },
            "sqlStartupReadiness": readiness,
            "sqlHostClockBefore": clock_before,
            "originalMembership": membership,
            "trials": observations,
            "limitations": (
                "Only one physical host and one repetition per route/rate, "
                "with 60s measured windows. At most two offered load points "
                "40/80/s on 50 eligible hot source accounts. SQL rates use "
                "PostgreSQL server COMMIT stamps and bounded one-host UTC "
                "brackets, but neither a capacity knee, production p99 nor "
                "mainframe MIPS equivalence follows. ACK-only percentiles "
                "exclude missed and ambiguous work; retain censoring. "
                "SQL pg_stat_database counters include test/oracle traffic "
                "and are NOT independently attributable business COMMITs."
            )
        }
        expected_count = sum(
            rate * (WARMUP_SECONDS + MEASUREMENT_SECONDS + COOLDOWN_SECONDS)
            * len(ROUTES) for rate in RATES
        )
        observed_count = sum(
            row["originalIndependentResult"]["offered"] for row in observations
        )
        assert len(observations) == len(RATES) * len(ROUTES) == 4
        assert expected_count == observed_count == 14880, (
            "Predeclared total offered commands MUST include both routes",
            expected_count, observed_count
        )
        (OUT / "b05-sweep-summary.json").write_text(
            json.dumps(final, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps({
            "experiment": final["experiment"],
            "status": final["status"],
            "trialCount": len(observations),
            "scheduledRequests": sum(
                row["originalIndependentResult"]["offered"]
                for row in observations
            ),
            "durableCommitsByRunEnd": sum(
                row["originalIndependentResult"]["sqlDurableCommittedByRunEnd"]
                for row in observations
            ),
            "observedLoss": [
                (row["route"], row["offeredRatePerSecond"],
                 row["originalIndependentResult"]["missed"],
                 row["originalIndependentResult"]["ambiguous"])
                for row in observations
            ],
            "capacityEvidence": False
        }, indent=2))
    except Exception as err:
        original_failure(err, stage, containers)
        raise
    finally:
        fx.CONN = old_conn
        for name in reversed(containers):
            P("rm", "-f", name, check=False, timeout=60)
        for name in reversed(networks):
            P("network", "rm", name, check=False, timeout=60)


if __name__ == "__main__":
    main()
