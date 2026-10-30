#!/usr/bin/env python3
"""Export independently checked E1b accounting oracle vectors.

This harness deliberately corrupts and restores a posting in a disposable
PostgreSQL database after test_reference_parity.py. It does not modify the
candidate application, source reference, or independent read-only oracle.
"""
import hashlib
import json
from pathlib import Path
import platform
import sys

from ledger import connect
from oracle import verify

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "results" / "e1"
OUT.mkdir(parents=True, exist_ok=True)
EXPECTED = {
    "nonnegative", "conserved", "balancedPostings",
    "twoPostingsPerCommit", "noPostingsForRejection",
    "outboxAtomic", "projectionAgrees"
}


def check_vector(values, expected):
    assert set(values) == EXPECTED, values
    assert all(isinstance(result, bool) for result in values.values())
    assert all(values.values()) is expected, values
    return values


def main():
    # The direct reference parity runner must have completed first.
    with connect() as db:
        op_count = db.execute("SELECT COUNT(*) FROM operations").fetchone()[0]
        posting = db.execute(
            "SELECT op,account,delta FROM postings "
            "WHERE op='unblocked' ORDER BY account LIMIT 1"
        ).fetchone()
        version = db.execute("SHOW server_version").fetchone()[0]
    assert op_count == 6 and posting is not None, (
        "Run test_reference_parity.py first on this disposable database",
        op_count, posting
    )

    before = check_vector(verify(), True)

    # Write the negative control through an independent test transaction.
    # The oracle itself remains strictly read-only and source-independent.
    try:
        with connect() as db:
            db.execute(
                "DELETE FROM postings WHERE op=%s AND account=%s",
                (posting[0], posting[1])
            )
        corrupted = verify()
        assert set(corrupted) == EXPECTED, corrupted
        assert corrupted["twoPostingsPerCommit"] is False, corrupted
        assert corrupted["projectionAgrees"] is False, corrupted
        assert corrupted["balancedPostings"] is False, corrupted
    finally:
        # Never leave the experiment database in a corrupted state.
        with connect() as db:
            db.execute(
                "INSERT INTO postings(op,account,delta) VALUES(%s,%s,%s)",
                posting
            )

    restored = check_vector(verify(), True)
    assert before == restored
    report = {
        "schemaVersion": 1,
        "experiment": "E1b-independent-oracle-negative-control",
        "status": "PASS",
        "classification": "SYNTHETIC_LEDGER_ORACLE_NOT_PRODUCTION_CAPACITY",
        "controls": {
            "sevenInvariantsBefore": "PASS",
            "deliberateCorruptionRejected": "PASS",
            "sevenInvariantsRestored": "PASS"
        },
        "originalOperationCount": op_count,
        "targetPosting": {
            "operation": posting[0],
            "account": posting[1],
            "delta": posting[2]
        },
        "vectors": {
            "before": before,
            "corrupted": corrupted,
            "restored": restored
        },
        "sourceSha256": {
            name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in (
                "schema.sql", "oracle.py", "test_oracle_vectors.py",
                "test_reference_parity.py"
            )
        },
        "environment": {
            "postgresVersion": version,
            "pythonVersion": platform.python_version(),
            "runtime": "GitHub Actions disposable Linux runner / Podman"
        },
        "limitations": (
            "Synthetic one-database negative control, not full transaction "
            "fault coverage, vendor equivalence, power-loss durability or "
            "mainframe/Azure capacity evidence."
        )
    }
    (OUT / "oracle-vectors-summary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
