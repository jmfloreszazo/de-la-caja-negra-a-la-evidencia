"""Independent acceptance oracle for a deliberately synthetic functional greenfield slice.

Contract is specified as explicit golden outcomes by a different authoring route.
Never mistake this checker for bank authorization, production durability, or policy signoff.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

class OracleFailure(AssertionError):
    pass


def verify(contract: dict, observed: dict) -> None:
    if contract.get("classification") != "SYNTHETIC_UNAPPROVED_CAPABILITY_CONTRACT":
        raise OracleFailure("Only explicitly synthetic input is accepted")
    expected = contract.get("expected")
    if not isinstance(expected, dict) or not isinstance(observed, dict):
        raise OracleFailure("Missing expected or observed results")
    if set(observed) != set(expected):
        raise OracleFailure("Unexpected or missing result fields")
    if observed != expected:
        raise OracleFailure("Candidate output contradicts independently specified golden outcomes")

    initial = contract["initialBalances"]
    final = observed["balances"]
    if set(initial) != set(final) or any(type(n) is not int or n < 0 for n in final.values()):
        raise OracleFailure("Invalid account authority")
    if sum(initial.values()) != sum(final.values()):
        raise OracleFailure("Money conservation failed")

    postings = observed["postings"]
    per_op = defaultdict(list)
    per_account = Counter()
    for p in postings:
        if set(p) != {"operationId", "account", "delta"} or p["account"] not in initial:
            raise OracleFailure("Posting schema or account invalid")
        if type(p["delta"]) is not int or not p["delta"]:
            raise OracleFailure("Zero or malformed posting")
        per_op[p["operationId"]].append(p)
        per_account[p["account"]] += p["delta"]
    if any(len(rows) != 2 or sum(x["delta"] for x in rows) != 0 or rows[0]["account"] == rows[1]["account"]
           for rows in per_op.values()):
        raise OracleFailure("Nonbalanced or duplicate financial effects")
    if any(final[account] != initial[account] + per_account[account] for account in initial):
        raise OracleFailure("Ledger projection mismatch")

    outbox = observed["outbox"]
    if not isinstance(outbox, list) or len(outbox) != len(set(outbox)) or set(outbox) != set(per_op):
        raise OracleFailure("Outbox does not match applied operations")
    if observed["version"] != len(per_op):
        raise OracleFailure("Applied operation version mismatch")
    if not (0 <= observed["projectionVersion"] <= observed["version"]):
        raise OracleFailure("Projection watermark inconsistent")


def load_contract(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
