#!/usr/bin/env python3
"""E2-F07: two independent Orleans silo OS processes and an external client.

Development clustering on loopback proves local membership, remote grain
placement, a real secondary process SIGKILL, and ledger recovery by replay.
It does NOT prove production multi-node failover or an in-flight SQL crash.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

from test_e2 import APP, HERE, LAB, OUT, command, oracle, postgres_snapshot, reset
from ledger import connect

PROVIDER = os.environ.get("E2_CLUSTER_PROVIDER", "development")
assert PROVIDER in ("development", "adonet"), "Unknown cluster provider"
MAX_JOIN_SECONDS = 100
MAX_RECOVERY_SECONDS = 150
SOURCE_FILES = [
    HERE / "test_multiprocess.py",
    HERE / "setup_adonet_membership.py",
    HERE / "OrleansLab/ClusterModes.cs",
    HERE / "OrleansLab/Contracts.cs",
    HERE / "OrleansLab/PgDurableLedger.cs",
]


def call_client(mode, commands=None, timeout=45):
    assert mode in ("probe", "execute")
    args = ["dotnet", str(APP), "cluster", "client", mode]
    path = None
    if mode == "execute":
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".json", dir=OUT,
            prefix="e2-cluster-", delete=False
        ) as output:
            json.dump({"route": "orleans", "concurrent": False,
                       "commands": commands}, output)
            path = Path(output.name)
        args.append(str(path))
    try:
        result = subprocess.run(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, timeout=timeout, env=os.environ
        )
        if result.returncode != 0:
            raise RuntimeError(
                "External Orleans client exited " + str(result.returncode) +
                ": " + result.stderr[-2500:] + " / " + result.stdout[-1500:])
        return json.loads(result.stdout)
    finally:
        if path is not None:
            path.unlink(missing_ok=True)


def wait_ready(process, filename, role, timeout=65):
    deadline = time.monotonic() + timeout
    marker = "E2_SILO_READY:" + role + ":" + str(process.pid)
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(role + " exited early: " +
                               filename.read_text(encoding="utf-8")[-3000:])
        if marker in filename.read_text(encoding="utf-8"):
            return
        time.sleep(0.3)
    raise TimeoutError("No process-ready marker: " + role +
                       " / " + filename.read_text(encoding="utf-8")[-1500:])


def inspect_db():
    with connect() as db:
        return {
            "operations": db.execute(
                "SELECT id,status FROM operations ORDER BY id").fetchall(),
            "postings": db.execute("SELECT COUNT(*) FROM postings").fetchone()[0],
            "outbox": db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]
        }


def read_membership():
    """Verify the official Orleans ADO.NET membership rows, not the ledger."""
    if PROVIDER != "adonet":
        return None
    with connect() as db:
        keys = db.execute(
            "SELECT COUNT(*) FROM OrleansQuery "
            "WHERE QueryKey ILIKE '%Membership%' OR QueryKey ILIKE '%Gateway%'"
        ).fetchone()[0]
        rows = db.execute(
            "SELECT DeploymentId,Address,Port,Generation,Status,ProxyPort "
            "FROM OrleansMembershipTable ORDER BY Port,Generation"
        ).fetchall()
        versions = db.execute(
            "SELECT DeploymentId,Version "
            "FROM OrleansMembershipVersionTable ORDER BY DeploymentId"
        ).fetchall()
    return {
        "providerQueryCount": keys,
        "membershipRows": [list(x) for x in rows],
        "versions": [list(x) for x in versions]
    }


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def main():
    assert APP.exists(), "Build OrleansLab Release before E2-F07"
    assert os.environ.get("E2_CLUSTER_TEST") != "1", (
        "Parent runner should not globally enable this fixture"
    )
    reset()
    initial = postgres_snapshot()
    if PROVIDER == "adonet":
        installed = read_membership()
        assert installed["providerQueryCount"] >= 3, installed
        assert not installed["membershipRows"], (
            "ADO.NET membership must start from a fresh disposable catalog",
            installed
        )
    original_env = os.environ.copy()
    os.environ["E2_CLUSTER_TEST"] = "1"
    if PROVIDER == "adonet":
        os.environ["E2_MEMBERSHIP_NPGSQL"] = os.environ["E2_PG_NPGSQL"]
    fixture_env = os.environ.copy()
    primary = secondary = None
    try:
        with tempfile.TemporaryDirectory(prefix="e2-two-silos-") as td:
            root = Path(td)
            first_log = root / "primary.log"
            second_log = root / "secondary.log"
            with first_log.open("w+", encoding="utf-8") as a, second_log.open(
                "w+", encoding="utf-8"
            ) as b:
                primary = subprocess.Popen(
                    ["dotnet", str(APP), "cluster", "silo", "primary"],
                    stdout=a, stderr=subprocess.STDOUT, text=True,
                    env=fixture_env
                )
                wait_ready(primary, first_log, "primary")
                secondary = subprocess.Popen(
                    ["dotnet", str(APP), "cluster", "silo", "secondary"],
                    stdout=b, stderr=subprocess.STDOUT, text=True,
                    env=fixture_env
                )
                wait_ready(secondary, second_log, "secondary")
                # Use newly activated keys after cluster membership converges.
                time.sleep(8)
                started = time.monotonic()
                observed = None
                while time.monotonic() - started < MAX_JOIN_SECONDS:
                    try:
                        probe = call_client("probe", timeout=35)
                        ids = {int(k): int(v) for k, v in probe["accountHostPids"].items()}
                        if {primary.pid, secondary.pid}.issubset(set(ids.values())):
                            observed = (probe, ids)
                            break
                    except (RuntimeError, subprocess.TimeoutExpired):
                        pass
                    time.sleep(2)
                if observed is None:
                    raise AssertionError(
                        "Cannot establish that BOTH independent silos host grains: " +
                        first_log.read_text(encoding="utf-8")[-1500:] + " / " +
                        second_log.read_text(encoding="utf-8")[-1500:]
                    )
                probe, ids = observed
                sql_membership_before = read_membership()
                if PROVIDER == "adonet":
                    members = sql_membership_before["membershipRows"]
                    # An independently read, persistent SQL membership table
                    # must register both silo endpoints and their gateway ports.
                    assert {11150, 11151}.issubset(
                        {int(row[2]) for row in members}
                    ), sql_membership_before
                    assert {30050, 30051}.issubset(
                        {int(row[5]) for row in members if row[5] is not None}
                    ), sql_membership_before
                    assert all(row[0] == "e2-local-recovery" for row in members)
                    assert sql_membership_before["versions"], sql_membership_before
                assert probe["clientPid"] not in (primary.pid, secondary.pid)
                source_secondary = next(k for k, v in ids.items() if v == secondary.pid)
                source_primary = next(k for k, v in ids.items() if v == primary.pid)
                workload = [
                    command("e2-multi-before-secondary", source_secondary, source_primary, 10),
                    command("e2-multi-before-primary", source_primary, source_secondary, 20),
                ]
                pre = call_client("execute", workload, timeout=70)
                assert [x["status"] for x in pre["results"]] == [
                    "COMMITTED", "COMMITTED"
                ], pre
                assert [x["actualSiloProcessId"] for x in pre["results"]] == [
                    secondary.pid, primary.pid
                ], pre
                assert pre["clientPid"] not in (primary.pid, secondary.pid)
                assert inspect_db()["postings"] == 4
                assert inspect_db()["outbox"] == 2
                assert all(oracle().values())

                # This is an actual SIGKILL of a SEPARATE Orleans server OS
                # process. There is deliberately no in-flight SQL transaction.
                secondary.kill()
                assert secondary.wait(timeout=15) == -signal.SIGKILL
                assert primary.poll() is None
                started_recovery = time.monotonic()
                reassigned = None
                failures = []
                while time.monotonic() - started_recovery < MAX_RECOVERY_SECONDS:
                    try:
                        later = call_client("probe", timeout=40)
                        found = {int(k): int(v)
                                 for k, v in later["accountHostPids"].items()}
                        if found[source_secondary] == primary.pid:
                            reassigned = later
                            break
                    except (RuntimeError, subprocess.TimeoutExpired) as ex:
                        failures.append(str(ex)[:250])
                    time.sleep(2)
                if reassigned is None:
                    raise AssertionError(
                        "The dead silo grain did not reactivate on the surviving silo; " +
                        "no functional failover evidence. Recent errors: " +
                        repr(failures[-5:])
                    )
                follow_up = call_client("execute", [
                    command("e2-multi-before-secondary", source_secondary, source_primary, 10),
                    command("e2-multi-after-kill", source_secondary, source_primary, 5)
                ], timeout=70)
                assert [x["status"] for x in follow_up["results"]] == [
                    "DUPLICATE_COMMITTED", "COMMITTED"
                ], follow_up
                assert all(x["actualSiloProcessId"] == primary.pid
                           for x in follow_up["results"]), follow_up
                db = inspect_db()
                assert db["operations"] == [
                    ("e2-multi-after-kill", "COMMITTED"),
                    ("e2-multi-before-primary", "COMMITTED"),
                    ("e2-multi-before-secondary", "COMMITTED")
                ], db
                assert db["postings"] == 6 and db["outbox"] == 3
                assert all(oracle().values())
                after = postgres_snapshot()
                assert after != initial
                sql_membership_after = read_membership()
                if PROVIDER == "adonet":
                    # Verify the actual persisted membership transition.
                    # Orleans 10.4.0 defines Active=3 and Dead=6.
                    before_ports = {
                        int(row[2]): int(row[4])
                        for row in sql_membership_before["membershipRows"]
                    }
                    after_ports = {
                        int(row[2]): int(row[4])
                        for row in sql_membership_after["membershipRows"]
                    }
                    assert before_ports == {11150: 3, 11151: 3}, (
                        "Both silos must start active", before_ports
                    )
                    assert after_ports == {11150: 3, 11151: 6}, (
                        "Persistent SQL must mark killed secondary dead",
                        after_ports
                    )
                    before_version = int(sql_membership_before["versions"][0][1])
                    after_version = int(sql_membership_after["versions"][0][1])
                    assert after_version > before_version, (
                        "Membership ETag/version must advance", before_version,
                        after_version
                    )

                outcome = {
                    "schemaVersion": 1,
                    "experiment": (
                        "E2-ADO-NET-Persistent-SQL-Membership-SIGKILL"
                        if PROVIDER == "adonet" else
                        "E2-Independent-Process-Orleans-Secondary-SIGKILL"
                    ),
                    "membershipProvider": PROVIDER,
                    "sqlMembershipBeforeKill": sql_membership_before,
                    "sqlMembershipAfterRecovery": sql_membership_after,
                    "status": "PASS",
                    "classification": (
                        "SYNTHETIC_PERSISTENT_ADONET_MEMBERSHIP_ONE_HOST_NOT_PHYSICAL"
                        if PROVIDER == "adonet" else
                        "SYNTHETIC_TWO_SILOS_ONE_HOST_DEVELOPMENT_CLUSTER_NOT_PHYSICAL"
                    ),
                    "primarySiloPid": primary.pid,
                    "secondarySiloPid": secondary.pid,
                    "initialExternalClientPid": probe["clientPid"],
                    "initialPlacement": ids,
                    "sourceAccountPreviouslyOnSecondary": source_secondary,
                    "sourceAccountOnPrimary": source_primary,
                    "actualSecondaryExitSignal": "SIGKILL",
                    "grainReactivatedOnPrimary": True,
                    "idempotentRecoveredReplay": "DUPLICATE_COMMITTED",
                    "newOperationAfterSiloDeath": "COMMITTED",
                    "businessEffects": {
                        "committedOperations": 3, "postings": 6,
                        "outboxEvents": 3
                    },
                    "independentSqlOracle": oracle(),
                    "stateSha256": hashlib.sha256(json.dumps(
                        after, separators=(",", ":"), ensure_ascii=True
                    ).encode("utf-8")).hexdigest(),
                    "sourceSha256": {
                        str(path.relative_to(LAB)):
                            hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in SOURCE_FILES
                    },
                    "limitations": (
                        "Two different Orleans silo OS processes and an external "
                        "client on ONE Linux runner. Provider=" + PROVIDER +
                        "; loopback transport, killed secondary AFTER the first "
                        "client response, not during COMMIT. Not independently "
                        "provisioned nodes, production membership provider, "
                        "in-flight failover SLA, stress benchmark or mainframe equivalence."
                    )
                }
                output_name = (
                    "e2-adonet-recovery.json" if PROVIDER == "adonet"
                    else "e2-multiprocess.json"
                )
                (OUT / output_name).write_text(
                    json.dumps(outcome, indent=2) + "\n", encoding="utf-8")
                print(json.dumps(outcome, indent=2))
    finally:
        if secondary is not None:
            stop(secondary)
        if primary is not None:
            stop(primary)
        os.environ.clear()
        os.environ.update(original_env)


if __name__ == "__main__":
    main()
