#!/usr/bin/env python3
"""Validate immutable, sanitized E1 CI snapshots before publication."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"evidence/runs"
EXPECTED={"E1a":11,"E1b":7}

for name,controls in EXPECTED.items():
    file=BASE/(name.lower()+".json")
    record=json.loads(file.read_text(encoding="utf-8"))
    data=record["observation"]
    assert record["schemaVersion"]==1 and record["experiment"]==name
    assert re.fullmatch(r"[0-9a-f]{40}",record["sourceCommit"])
    assert record["runId"]>0 and record["jobId"]>0
    assert record["url"].endswith("/"+str(record["runId"]))
    assert record["classification"]=="EXECUTED_SNAPSHOT_NOT_MAINFRAME_BENCHMARK"
    assert data["status"]=="PASS"
    assert len(data["controls"])==controls
    assert all(x["status"]=="PASS" for x in data["controls"].values())
    for relative,expected in data["sourceSha256"].items():
        original=ROOT/"lab"/"e1_pg"/relative
        assert original.is_file(), original
        actual=hashlib.sha256(original.read_bytes()).hexdigest()
        assert actual==expected,(relative,expected,actual)
    if name=="E1a":
        assert "40P01" in str(data["controls"]["deadlockVictimRetried"])
        assert "40001" in str(data["controls"]["writeSkewPrevented"])
        assert data["controls"]["oracleRejectsCorruptLedger"]["detected"]
    else:
        assert data["parity"]["persistedStateEqual"] is True
        assert data["controls"]["candidateParity"]["status"]=="PASS"
    print(name,": verified snapshot from run",record["runId"],"with",controls,"controls")
print("E1 OBSERVATION SNAPSHOTS: PASS")
