#!/usr/bin/env python3
"""Validate transport-only report; do not permit promoting this to E3."""
import json
from pathlib import Path
import sys
p=Path(sys.argv[1] if len(sys.argv)>1 else "lab/results/transport/report.json")
d=json.loads(p.read_text(encoding="utf-8"))
assert d["schemaVersion"]==1
assert d["classification"]=="EXECUTED_LOCALHOST_TRANSPORT_ONLY_NOT_LEDGER_OR_MAINFRAME"
assert "HTTP/2 plaintext" in d["environment"]["httpTransport"]
assert d["negativeOracleControl"]=="PASS"
assert d["workload"]["closedLoop"] is True
assert "No durable ledger" in d["workload"]["claims"]
ts=d["trials"]
assert len(ts)==4
assert [t["protocol"] for t in ts]==["grpc","rest","rest","grpc"]
assert all(t["errors"]==0 for t in ts)
assert all(t["requests"]==d["workload"]["requestsPerRound"] for t in ts)
assert all(t["repliesPerSecond"]>0 and 0<=t["p50Ms"]<=t["p95Ms"]<=t["p99Ms"] for t in ts)
assert d["environment"]["tlsAndNetwork"].startswith("NOT TESTED")
print("TRANSPORT EXPERIMENT: PASS (loopback only; no database or WAN)")
