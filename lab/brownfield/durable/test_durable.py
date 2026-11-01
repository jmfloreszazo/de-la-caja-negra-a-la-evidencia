#!/usr/bin/env python3
"""Destructive-in-disposable-DB external process tests; never use customer data.

Run only with BROWNFIELD_DISPOSABLE=YES and isolated bf_* database credentials.
This script tests a synthetic CAP-007/CAP-005 slice, not real legacy coexistence.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

import psycopg
from oracle import observe

HERE = Path(__file__).resolve().parent
DLL = HERE / "DurableBank" / "bin" / "Release" / "net10.0" / "DurableBank.dll"
DOTNET = os.environ.get("DOTNET", "dotnet")
DSN = os.environ["BROWNFIELD_PG_DSN"]
CONN = os.environ["BROWNFIELD_PG_NPGSQL"]
OUT = HERE.parent.parent / "results" / "brownfield"


def require_disposable() -> None:
    if os.environ.get("BROWNFIELD_DISPOSABLE") != "YES":
        raise RuntimeError("Explicit BROWNFIELD_DISPOSABLE=YES is mandatory.")
    with psycopg.connect(DSN, autocommit=True) as db:
        name = db.execute("SELECT current_database()").fetchone()[0]
        if not name.startswith("bf_"):
            raise RuntimeError("Refusing destructive setup outside a bf_* database")
        if name != psycopg.conninfo.conninfo_to_dict(DSN)["dbname"]:
            raise RuntimeError("Cannot establish the intended disposable database")


def reset() -> None:
    """All destructive operations are limited to the validated disposable DB."""
    with psycopg.connect(DSN, autocommit=True) as db:
        db.execute("DROP SCHEMA IF EXISTS brownfield CASCADE")
        db.execute((HERE / "schema.sql").read_text(encoding="utf-8"))


def execute(*args: object, expected: int = 0) -> dict:
    command = [DOTNET, str(DLL), *map(str, args)]
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=45, env=os.environ)
    assert result.returncode == expected, (command, result.returncode, result.stdout, result.stderr)
    return json.loads(result.stdout) if expected == 0 else {}


def transfer(op_id: str, source: int, dest: int, amount: int,
             writer: str = "legacy", epoch: int = 1, fault: str = "none",
             expected: int = 0) -> dict:
    return execute("transfer", op_id, source, dest, amount, writer, epoch, fault,
                   expected=expected)


def exact(sql: str, *params: object) -> object:
    with psycopg.connect(DSN, autocommit=True) as db:
        return db.execute(sql, params).fetchone()[0]


def require_oracle(label: str) -> dict:
    result = observe(DSN)
    assert result["passed"], (label, result)
    return result


def test_precommit_sigkill() -> None:
    """Kill the process while an actual, uncommitted SQL debit is open."""
    command = [DOTNET, str(DLL), "transfer", "KILL-PRECOMMIT",
               "3", "4", "400", "legacy", "1", "pause-before-commit"]
    before = exact("SELECT balance FROM brownfield.accounts WHERE id=3")
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, env=os.environ,
                               bufsize=1)
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        events = selector.select(timeout=35)
        assert events, "No precommit observation: test must not claim SIGKILL evidence"
        marker = process.stdout.readline().strip()
        assert marker == "UNCOMMITTED_DEBIT_APPLIED", marker
        process.kill()  # SIGKILL on Linux, independent of candidate exception handling.
        process.wait(timeout=10)
        assert process.returncode < 0, process.returncode
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)
        selector.close()
        process.stdout.close()
        assert process.stderr is not None
        process.stderr.close()
    assert exact("SELECT balance FROM brownfield.accounts WHERE id=3") == before
    assert exact("SELECT count(*) FROM brownfield.operations WHERE id=%s",
                 "KILL-PRECOMMIT") == 0
    assert transfer("KILL-PRECOMMIT", 3, 4, 400)["status"] == "COMMITTED"


def test_negative_oracle_control() -> None:
    """Deliberately corrupt an isolated fixture and require an independent FAIL."""
    with psycopg.connect(DSN, autocommit=True) as db:
        original = db.execute(
            "DELETE FROM brownfield.postings "
            "WHERE operation_id='TX-BASE' AND account_id=1 "
            "RETURNING operation_id,account_id,delta"
        ).fetchone()
    assert original is not None
    try:
        after = observe(DSN)
        assert not after["passed"], "Corrupted posting was incorrectly accepted"
        assert not after["checks"]["pairedCommittedPostings"]
        assert not after["checks"]["balancesMatchPostings"]
    finally:
        with psycopg.connect(DSN, autocommit=True) as db:
            db.execute("INSERT INTO brownfield.postings "
                       "(operation_id,account_id,delta) VALUES (%s,%s,%s)", original)
    require_oracle("oracle-restored")


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    require_disposable()
    OUT.mkdir(parents=True, exist_ok=True)
    build = subprocess.run([DOTNET, "build", str(HERE / "DurableBank"),
                            "-c", "Release", "-m:1", "--disable-build-servers"],
                           capture_output=True, text=True, timeout=240)
    (OUT / "build.log").write_text(build.stdout + build.stderr, encoding="utf-8")
    assert build.returncode == 0, "DurableBank failed to build; see build.log"
    reset()

    assert transfer("TX-BASE", 1, 2, 100)["status"] == "COMMITTED"
    assert transfer("TX-BASE", 1, 2, 100)["status"] == "DUPLICATE_COMMITTED"
    assert transfer("TX-BASE", 1, 2, 101)["status"] == "ID_CONFLICT"
    assert transfer("TX-REJECT", 1, 2, 200_000)["status"] == "REJECTED"
    assert transfer("TX-REJECT", 1, 2, 200_000)["status"] == "DUPLICATE_REJECTED"
    require_oracle("baseline")

    transfer("TX-LOST-ACK", 2, 1, 200, fault="lost-ack", expected=92)
    assert exact("SELECT count(*) FROM brownfield.operations WHERE id=%s",
                 "TX-LOST-ACK") == 1
    assert transfer("TX-LOST-ACK", 2, 1, 200)["status"] == "DUPLICATE_COMMITTED"
    assert exact("SELECT count(*) FROM brownfield.postings WHERE operation_id=%s",
                 "TX-LOST-ACK") == 2
    require_oracle("after-lost-ack")

    transfer("TX-CRASH", 3, 4, 100, fault="crash-before-commit", expected=91)
    assert exact("SELECT count(*) FROM brownfield.operations WHERE id=%s",
                 "TX-CRASH") == 0
    assert transfer("TX-CRASH", 3, 4, 100)["status"] == "COMMITTED"
    test_precommit_sigkill()
    require_oracle("after-sigkill")

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(transfer, f"HOT-{i}", 5, 6, 20_000)
                   for i in range(8)]
        statuses = sorted(f.result(timeout=45)["status"] for f in futures)
    assert statuses == ["COMMITTED"] * 5 + ["REJECTED"] * 3, statuses
    assert exact("SELECT balance FROM brownfield.accounts WHERE id=5") == 0
    state = require_oracle("after-hot-account")

    assert execute("balance", 1, 1_000_000)["status"] == "BELOW_MINIMUM_VERSION"
    assert execute("balance", 1, state["watermark"])["status"] == "AUTHORITATIVE"

    stale = execute("switch", "legacy", 1, "candidate", state["watermark"] + 1,
                    state["operationCount"])
    assert stale["status"] == "CUTOVER_BLOCKED" and stale["todmG6"] == "BLOCK"
    switched = execute("switch", "legacy", 1, "candidate",
                       state["watermark"], state["operationCount"])
    assert (switched["status"], switched["epoch"], switched["todmG6"]) == (
        "SYNTHETIC_SWITCH", 2, "BLOCK")
    assert transfer("FENCED-OLD", 7, 8, 10)["status"] == "FENCED_WRITER_OR_EPOCH"
    assert transfer("TX-BASE", 1, 2, 100, "candidate", 2)["status"] == "DUPLICATE_COMMITTED"
    assert transfer("CANDIDATE-ONE", 7, 8, 10, "candidate", 2)["status"] == "COMMITTED"
    state = require_oracle("after-synthetic-switch")
    rollback = execute("switch", "candidate", 2, "legacy",
                       state["watermark"], state["operationCount"])
    assert rollback["status"] == "SYNTHETIC_SWITCH" and rollback["epoch"] == 3
    assert transfer("FENCED-CANDIDATE", 7, 8, 10, "candidate", 2)["status"] == "FENCED_WRITER_OR_EPOCH"
    assert transfer("LEGACY-RETURN", 7, 8, 10, "legacy", 3)["status"] == "COMMITTED"

    test_negative_oracle_control()
    final = require_oracle("final")
    assert final["operationCount"] == 17, final
    sha256 = {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (HERE / "schema.sql", HERE / "oracle.py",
                        HERE / "DurableBank" / "Program.cs",
                        HERE / "DurableBank" / "DurableBank.csproj",
                        HERE / "test_durable.py")}
    report = {
        "status": "PASS",
        "classification": "EXECUTED_SYNTHETIC_DISPOSABLE_ONLY",
        "startedUtc": started,
        "endedUtc": datetime.now(timezone.utc).isoformat(),
        "sourceSha256": sha256,
        "oracle": final,
        "controls": ["idempotency", "fingerprintConflict", "insufficientFunds",
                     "commitLostAckRestartReplay", "processExitPrecommit",
                     "realSigkillPrecommit", "concurrentHotAccount",
                     "sqlAuthorityEpochCutover", "rollbackFencing",
                     "authoritativeVersionRead", "corruptionRejected"],
        "limitations": "No real COBOL, cross-store reconciliation, approved mandate, "
                       "G6 release, distributed HA, measured bank SLO or MIPS equivalence.",
    }
    (OUT / "durable-summary.json").write_text(json.dumps(report, indent=2) + "\n",
                                               encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
