"""Execute selected, hash-verified upstream synthetic governance functions."""
from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
from pathlib import Path

PIN = "61354abc03e73fbf258b6e8d66e35678da134ef8"
VENDOR = Path(__file__).parent / "vendor"


def upstream_functions():
    provenance = json.loads((VENDOR / "provenance.json").read_text(encoding="utf-8"))
    if provenance["commit"] != PIN:
        raise ValueError("Unexpected upstream revision")
    raw = (VENDOR / "governance.py").read_bytes()
    recorded = next(item["sha256"] for item in provenance["files"] if item["path"] == "governance.py")
    if hashlib.sha256(raw).hexdigest() != recorded:
        raise ValueError("Vendored upstream source changed")
    names = {"parse_time", "authority_verdict", "release_verdict"}
    nodes = [node for node in ast.parse(raw).body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in nodes} != names:
        raise ValueError("Upstream governance functions missing")
    namespace = {"dt": dt}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(VENDOR / "governance.py"), "exec"), namespace)
    return namespace


def demonstrate():
    upstream = upstream_functions()
    mandates = {"mandates": {"fixture-reviewer": {
        "actions": ["release"], "scopes": ["synthetic:E1"], "revoked": False,
        "validFrom": "2026-11-01T00:00:00Z", "validUntil": "2026-12-01T00:00:00Z",
    }}}
    base = {"principal": "fixture-reviewer", "action": "release", "scope": "synthetic:E1", "at": "2026-11-08T00:00:00Z"}
    approval = {"kind": "DEMO_SIMULATED", "approved": True, "approverRole": "release-owner"}
    scenarios = [
        ("synthetic-allow", base, mandates, "PASS", approval, "PASS", "SIMULATED_ALLOW"),
        ("missing-principal", {k: v for k, v in base.items() if k != "principal"}, mandates, "PASS", approval, "INCONCLUSIVE", "BLOCK"),
        ("unknown-principal", dict(base, principal="builder"), mandates, "PASS", approval, "FAIL", "BLOCK"),
        ("missing-time", {k: v for k, v in base.items() if k != "at"}, mandates, "PASS", approval, "INCONCLUSIVE", "BLOCK"),
        ("expired", dict(base, at="2026-12-01T00:00:00Z"), mandates, "PASS", approval, "FAIL", "BLOCK"),
        ("wrong-scope", dict(base, scope="production"), mandates, "PASS", approval, "FAIL", "BLOCK"),
        ("wrong-action", dict(base, action="deploy"), mandates, "PASS", approval, "FAIL", "BLOCK"),
        ("missing-mandate", base, {"mandates": {}}, "PASS", approval, "FAIL", "BLOCK"),
        ("missing-approval", base, mandates, "PASS", None, "PASS", "BLOCK"),
        ("oracle-failed", base, mandates, "FAIL", approval, "PASS", "BLOCK"),
        ("oracle-inconclusive", base, mandates, "INCONCLUSIVE", approval, "PASS", "BLOCK"),
    ]
    revoked = json.loads(json.dumps(mandates))
    revoked["mandates"]["fixture-reviewer"]["revoked"] = True
    scenarios.append(("revoked", base, revoked, "PASS", approval, "FAIL", "BLOCK"))
    rows = []
    for name, request, registry, oracle, signoff, authority_expected, release_expected in scenarios:
        authority = upstream["authority_verdict"](registry, request)
        release = upstream["release_verdict"](oracle, authority["verdict"], signoff)
        matched = (authority["verdict"], release["outcome"]) == (authority_expected, release_expected)
        rows.append({"case": name, "request": request, "oracleVerdict": oracle,
                     "authority": authority, "release": release, "expectationMatched": matched})
    return {"classification": "SYNTHETIC_UPSTREAM_GOVERNANCE_NOT_PRODUCTION_AUTHORITY",
            "upstreamCommit": PIN, "cases": rows, "passed": all(row["expectationMatched"] for row in rows)}
