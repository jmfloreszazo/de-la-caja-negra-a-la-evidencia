#!/usr/bin/env python3
"""E2-F09: real in-flight SQL SIGKILL with distinct Orleans silo/client PIDs.

Synthetic tests only, one Linux runner with Orleans 10.4.0 ADO.NET SQL
membership. Never label this physically separated HA, an RTO/SLA, or MIPS.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

# Provider selection is checked by imported test_multiprocess at import time.
assert os.environ.get("E2_CLUSTER_PROVIDER") == "adonet", (
    "E2-F09 requires ADO.NET membership, not the development provider"
)
from test_e2 import APP, HERE, LAB, OUT, command, postgres_snapshot, reset
from test_multiprocess import call_client, wait_ready, stop, read_membership
from test_process_crash import counts
from ledger import connect
from oracle import verify

LOCK_ID = 720260301
CASES = ("pre", "post")
RAW = OUT / "e2-inflight-sql-commit.json"


def assert_oracle():
    result = verify()
    assert len(result) == 7 and all(result.values()), result
    return result


def cluster_probe(primary, secondary, seconds=125):
    start = time.monotonic()
    last = "not queried"
    while time.monotonic() - start < seconds:
        assert primary.poll() is None, "Primary silo unexpectedly died"
        try:
            data = call_client("probe", timeout=28)
            hosts = {int(k): int(v) for k, v in data["accountHostPids"].items()}
            if secondary is None:
                if all(p == primary.pid for p in hosts.values()):
                    return data, hosts
            elif {primary.pid, secondary.pid}.issubset(set(hosts.values())):
                return data, hosts
        except (RuntimeError, subprocess.TimeoutExpired) as exc:
            last = str(exc)[-500:]
        time.sleep(2)
    raise AssertionError(
        "No observed two-silo membership/reassignment before timeout: " + last
    )


def sql_wait_for_blocked_transaction(blocker, process, op, timeout=32):
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        assert process.poll() is None, (
            "External client ended before SQL advisory lock wait was observed"
        )
        with connect() as db:
            blocked = db.execute(
                "SELECT pid,wait_event_type,wait_event,state,query "
                "FROM pg_stat_activity "
                "WHERE datname='e2lab' AND wait_event_type='Lock' "
                "AND query LIKE '%pg_advisory_xact_lock(720260301)%' "
                "AND pid<>pg_backend_pid() ORDER BY pid"
            ).fetchall()
            if blocked:
                # The already executed debit remains uncommitted and thus
                # invisible to this independent read-only SQL session.
                assert counts(op) == {
                    "operations": 0, "postings": 0, "outbox": 0
                }
                return {
                    "sqlBackendPid": int(blocked[0][0]),
                    "waitEventType": blocked[0][1],
                    "waitEvent": blocked[0][2],
                    "sqlTransactionState": blocked[0][3],
                    "blockedStatement": "pg_advisory_xact_lock(720260301)",
                    "invisibleBusinessEffectsBeforeKill": True
                }
        time.sleep(0.15)
    raise AssertionError("Failed to observe the live in-transaction advisory-lock wait")


def open_external_client(item):
    fd = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".json",
        prefix="e2-f09-", dir=OUT, delete=False
    )
    try:
        json.dump({"route": "orleans", "concurrent": False,
                   "commands": [item]}, fd)
    finally:
        fd.close()
    path = Path(fd.name)
    proc = subprocess.Popen(
        ["dotnet", str(APP), "cluster", "client", "execute", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=os.environ.copy()
    )
    return proc, path


def close_client(client, hard=False):
    if hard and client.poll() is None:
        client.kill()
    try:
        stdout, stderr = client.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        client.kill()
        stdout, stderr = client.communicate(timeout=10)
    return {
        "exitCode": client.returncode,
        "lastStdout": stdout[-900:],
        "lastStderr": stderr[-900:]
    }


def membership_transition(before):
    current = read_membership()
    assert current is not None
    b = {int(r[2]): int(r[4]) for r in before["membershipRows"]}
    a = {int(r[2]): int(r[4]) for r in current["membershipRows"]}
    assert b == {11150: 3, 11151: 3}, b
    assert a == {11150: 3, 11151: 6}, a
    assert int(current["versions"][0][1]) > int(before["versions"][0][1])
    return {
        "before": before, "after": current,
        "transition": "primary Active 3; secondary Active 3 -> Dead 6",
        "versionAdvanced": True
    }


def run_case(case):
    reset()
    before_state = postgres_snapshot()
    os.environ["E2_CLUSTER_INSTANCE"] = "e2-inflight-" + case
    os.environ["E2_CLUSTER_TEST"] = "1"
    os.environ["E2_INFLIGHT_TEST"] = "1"
    os.environ["E2_MEMBERSHIP_NPGSQL"] = os.environ["E2_PG_NPGSQL"]
    env = os.environ.copy()

    primary = secondary = client = blocker = None
    try:
        with tempfile.TemporaryDirectory(prefix="e2-f09-" + case + "-") as td:
            p_path = Path(td) / "primary.log"
            s_path = Path(td) / "secondary.log"
            with p_path.open("w+", encoding="utf-8") as p_log, s_path.open(
                "w+", encoding="utf-8"
            ) as s_log:
                primary = subprocess.Popen(
                    ["dotnet", str(APP), "cluster", "silo", "primary"],
                    stdout=p_log, stderr=subprocess.STDOUT, env=env
                )
                wait_ready(primary, p_path, "primary", timeout=90)
                secondary = subprocess.Popen(
                    ["dotnet", str(APP), "cluster", "silo", "secondary"],
                    stdout=s_log, stderr=subprocess.STDOUT, env=env
                )
                wait_ready(secondary, s_path, "secondary", timeout=90)
                time.sleep(6)
                probe, hosts = cluster_probe(primary, secondary)
                source = next(k for k, pid in hosts.items() if pid == secondary.pid)
                target = next(k for k, pid in hosts.items() if pid == primary.pid)
                assert probe["clientPid"] not in (primary.pid, secondary.pid)
                before_membership = read_membership()
                assert before_membership is not None

                op = "e2-inflight-" + case
                amount = 47 if case == "pre" else 49
                fault = "gate-after-debit" if case == "pre" else "kill-after-commit"
                item = command(op, source, target, amount, fault)
                lock_observation = None
                if case == "pre":
                    blocker = connect()
                    blocker.execute("SELECT pg_advisory_lock(%s)", (LOCK_ID,))
                client, scenario_file = open_external_client(item)
                executing_client_pid = client.pid
                assert executing_client_pid not in (primary.pid, secondary.pid)
                try:
                    if case == "pre":
                        lock_observation = sql_wait_for_blocked_transaction(
                            blocker, client, op
                        )
                        # This is an externally initiated SIGKILL of the
                        # ACTUAL silo process while its PostgreSQL backend is
                        # waiting inside an uncommitted debit transaction.
                        secondary.kill()
                        assert secondary.wait(timeout=12) == -signal.SIGKILL
                        # Prevent this particular external client from
                        # scheduling additional attempts while releasing gate.
                        client_info = close_client(client, hard=True)
                        client = None
                        assert counts(op) == {
                            "operations": 0, "postings": 0, "outbox": 0
                        }, "Uncommitted SQL must be rolled back after death"
                        blocker.execute(
                            "SELECT pg_advisory_unlock(%s)", (LOCK_ID,)
                        )
                        blocker.close()
                        blocker = None
                    else:
                        # Only the second silo is allowed to kill itself.
                        # The operation has already passed PostgreSQL COMMIT,
                        # but its originating server cannot acknowledge it.
                        assert secondary.wait(timeout=70) == -signal.SIGKILL, (
                            "The executing silo did not die after COMMIT",
                            s_path.read_text(encoding="utf-8")[-1200:]
                        )
                        client_info = close_client(client, hard=False)
                        client = None
                        assert counts(op) == {
                            "operations": 1, "postings": 2, "outbox": 1
                        }, "Committed SQL effects must survive silo death"
                finally:
                    scenario_file.unlink(missing_ok=True)

                recovered_probe, recovered_hosts = cluster_probe(
                    primary, None, seconds=130
                )
                assert recovered_hosts[source] == primary.pid
                membership = membership_transition(before_membership)
                # Some Orleans client implementations may retry the ambiguous
                # pre-commit command automatically on the survivor. Either
                # 0 or 1 business effect is acceptable; NEVER partial or >1.
                before_explicit = counts(op)
                assert before_explicit in (
                    {"operations": 0, "postings": 0, "outbox": 0},
                    {"operations": 1, "postings": 2, "outbox": 1}
                ), before_explicit
                if case == "post":
                    assert before_explicit["operations"] == 1
                if case == "pre":
                    # The fixture fault is not replayed; user workflows
                    # resolve the stable operation ID using normal commands.
                    assert_oracle()
                results = call_client(
                    "execute", [command(op, source, target, amount)],
                    timeout=55
                )["results"]
                expected = (
                    "COMMITTED" if before_explicit["operations"] == 0
                    else "DUPLICATE_COMMITTED"
                )
                assert len(results) == 1 and results[0]["status"] == expected, (
                    case, expected, results
                )
                duplicate = call_client(
                    "execute", [command(op, source, target, amount)]
                )["results"]
                assert duplicate[0]["status"] == "DUPLICATE_COMMITTED"
                after_new = call_client("execute", [
                    command("e2-f09-" + case + "-new", source, target, 5)
                ])["results"]
                assert after_new[0]["status"] == "COMMITTED"
                assert counts(op) == {
                    "operations": 1, "postings": 2, "outbox": 1
                }
                with connect() as db:
                    committed = db.execute(
                        "SELECT COUNT(*) FROM operations WHERE status='COMMITTED'"
                    ).fetchone()[0]
                    posting_count = db.execute(
                        "SELECT COUNT(*) FROM postings"
                    ).fetchone()[0]
                    outbox_count = db.execute(
                        "SELECT COUNT(*) FROM outbox"
                    ).fetchone()[0]
                assert (committed, posting_count, outbox_count) == (2, 4, 2)
                after_state = postgres_snapshot()
                assert after_state != before_state
                verified = assert_oracle()
                return {
                    "case": case, "status": "PASS",
                    "actualSiloProcessIds": {
                        "primary": primary.pid, "secondary": secondary.pid
                    },
                    "originalExternalClientProcessId": executing_client_pid,
                    "initialProbeClientProcessId": probe["clientPid"],
                    "victimSourceAccount": source,
                    "targetAccount": target,
                    "observedUncommittedSqlGate": lock_observation,
                    "actualSecondaryExitSignal": "SIGKILL",
                    "originalExternalClient": client_info,
                    "resultBeforeExplicitRecovery": before_explicit,
                    "explicitRecoveryStatus": expected,
                    "replayAfterRecovery": duplicate[0]["status"],
                    "newTransferStatus": after_new[0]["status"],
                    "survivorHostedFormerVictimGrain": (
                        recovered_hosts[source] == primary.pid
                    ),
                    "membership": membership,
                    "businessEffects": {
                        "committedOperations": committed,
                        "postings": posting_count,
                        "outboxEvents": outbox_count
                    },
                    "oracle": verified,
                    "stateSha256": hashlib.sha256(json.dumps(
                        after_state, separators=(",", ":"), ensure_ascii=True
                    ).encode()).hexdigest()
                }
    finally:
        if client is not None:
            close_client(client, hard=True)
        if blocker is not None:
            blocker.execute("SELECT pg_advisory_unlock(%s)", (LOCK_ID,))
            blocker.close()
        if secondary is not None:
            stop(secondary)
        if primary is not None:
            stop(primary)
        time.sleep(2)


def main():
    assert APP.is_file(), "Build the .NET 10 Orleans binary first"
    assert os.environ.get("E2_INFLIGHT_TEST") != "1", (
        "Parent test runner must not globally enable injection"
    )
    assert os.environ.get("E2_PG_NPGSQL"), "Disposable ledger DSN is required"
    original = os.environ.copy()
    try:
        cases = [run_case(case) for case in CASES]
    finally:
        os.environ.clear()
        os.environ.update(original)

    assert len(cases) == 2 and all(row["status"] == "PASS" for row in cases)
    report = {
        "schemaVersion": 1,
        "experiment": "E2-F09-SQL-InFlight-Silo-SIGKILL",
        "status": "PASS",
        "classification": (
            "SYNTHETIC_ADONET_TWO_SILOS_SINGLE_HOST_NOT_PHYSICAL_FAILOVER"
        ),
        "cases": cases,
        "sourceSha256": {
            str(path.relative_to(LAB)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest() for path in [
                HERE / "test_inflight.py",
                HERE / "OrleansLab/PgDurableLedger.cs",
                HERE / "OrleansLab/ClusterModes.cs",
                HERE / "OrleansLab/Contracts.cs",
            ]
        },
        "limitations": (
            "Actual separate-process silo SIGKILL while SQL debit transaction "
            "is blocked on a deliberately injected advisory gate, and actual "
            "self-kill immediately after SQL COMMIT before the original silo "
            "can reply. Both silos and client on ONE Linux host; one PostgreSQL "
            "database; no physical-node failure, network partition, DB crash, "
            "production RTO, sustained capacity or mainframe equivalence. "
            "Automatic client retry may commit the pre-commit operation "
            "on the survivor; the ledger invariant requires at most one effect."
        )
    }
    RAW.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": report["experiment"], "status": report["status"],
        "cases": [{
            "case": x["case"],
            "observedUncommittedSqlGate": bool(x["observedUncommittedSqlGate"]),
            "actualSecondaryExitSignal": x["actualSecondaryExitSignal"],
            "explicitRecoveryStatus": x["explicitRecoveryStatus"],
            "businessEffects": x["businessEffects"],
            "membershipTransition": x["membership"]["transition"],
            "independentSqlOracle": x["oracle"],
        } for x in cases]
    }, indent=2))


if __name__ == "__main__":
    main()
