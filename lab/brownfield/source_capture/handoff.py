#!/usr/bin/env python3
"""Pure, source-neutral *synthetic* snapshot/log handoff oracle for #58.

This is NOT a CDC connector or parser, real source observation, customer
acceptance, financial authorization or a native platform test. The fixture
provides its own independently declared source commits for comparison.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATALOG = json.loads((HERE / "capture_catalog.json").read_text(encoding="utf-8"))
LABEL = "SYNTHETIC_SOURCE_SNAPSHOT_LOG_HANDOFF_NOT_VENDOR_NATIVE"
ROOT_KEYS = {
    "schemaVersion", "classification", "sourceFamily", "sourceEpoch",
    "nativeCaptureExecuted", "customerApproval", "initialBalances",
    "sourceCommits", "abortedOperationIds", "snapshot", "capture", "target",
}
TX_KEYS = {"sequence", "operationId", "debit", "credit", "amountMinor"}
SNAPSHOT_KEYS = {"sourceEpoch", "cutSequence", "balances"}
CAPTURE_KEYS = {
    "sourceEpoch", "resumeAfterSequence", "oldestRetainedSequence",
    "observedHeadSequence", "events",
}
TARGET_KEYS = {"sourceEpoch", "appliedSequence", "balances"}
ACCOUNT_KEYS = {"A1", "A2", "A3", "A4"}
MAX_EVENTS = 256


def _result(status, problems, expected_count, reported):
    """Even a good synthetic fixture NEVER promotes business or native gates."""
    return {
        "status": status,
        "classification": "REFERENCE_TRACE_ONLY_NOT_NATIVE_OR_BANK_PROOF",
        "errors": sorted(set(problems)),
        "sourceCommits": expected_count,
        "capturedEvents": reported,
        "nativeCaptureTestExecuted": False,
        "independentCustomerSourceOracle": False,
        "externalEffectsReconciled": False,
        "productionApproved": False,
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
    }


def _strict(record, fields, label, errors):
    if not isinstance(record, dict):
        errors.append(f"{label}: expected object")
        return False
    if set(record) != fields:
        errors.append(f"{label}: wrong field set {sorted(set(record) ^ fields)}")
        return False
    return True


def _balance_map(record, label, errors):
    if not isinstance(record, dict) or set(record) != ACCOUNT_KEYS:
        errors.append(f"{label}: exactly four known synthetic accounts required")
        return None
    if any(type(value) is not int or value < 0 or value > 10_000_000
           for value in record.values()):
        errors.append(f"{label}: amounts must be bounded nonnegative integers")
        return None
    if sum(record.values()) != 400_000:
        errors.append(f"{label}: financial conservation fixture mismatch")
        return None
    return dict(record)


def _tx(row, label, errors):
    if not _strict(row, TX_KEYS, label, errors):
        return None
    if (type(row["sequence"]) is not int or row["sequence"] < 1
            or type(row["amountMinor"]) is not int
            or not 1 <= row["amountMinor"] <= 100_000
            or row["debit"] not in ACCOUNT_KEYS or row["credit"] not in ACCOUNT_KEYS
            or row["debit"] == row["credit"]
            or not isinstance(row["operationId"], str)
            or not 3 <= len(row["operationId"]) <= 64):
        errors.append(f"{label}: invalid sequence/account/value/ID")
        return None
    return row


def _replay(initial, rows, label, errors):
    balances = dict(initial)
    for i, item in enumerate(rows):
        if balances[item["debit"]] < item["amountMinor"]:
            errors.append(f"{label}[{i}]: insufficient funds")
            return None
        balances[item["debit"]] -= item["amountMinor"]
        balances[item["credit"]] += item["amountMinor"]
    if sum(balances.values()) != sum(initial.values()):
        errors.append(f"{label}: unbalanced transfer")
        return None
    return balances


def assess(record: object, catalog: dict = CATALOG) -> dict:
    """Compare *fixture supplied* source history, snapshot, stream and target.

    A reference trace can be internally consistent while completely unrelated
    to a real mainframe. No source bytes or owner signing are checked here.
    """
    errors, rejected = [], []
    if not _strict(record, ROOT_KEYS, "root", errors):
        return _result("INVALID", errors, 0, 0)
    if record["schemaVersion"] != 1 or record["classification"] != LABEL:
        errors.append("Fixture classification/schema not accepted")
    if record["nativeCaptureExecuted"] is not False or record["customerApproval"] is not False:
        errors.append("Fixture may not self-assert native capture or bank approval")
    if record["sourceFamily"] not in catalog["families"]:
        errors.append("Unknown source family: use the platform assessment catalog")
    epoch = record["sourceEpoch"]
    if not isinstance(epoch, str) or not 3 <= len(epoch) <= 64:
        errors.append("Invalid synthetic source epoch")
    initial = _balance_map(record["initialBalances"], "initialBalances", errors)
    commits = record["sourceCommits"]
    if not isinstance(commits, list) or not 1 <= len(commits) <= MAX_EVENTS:
        errors.append("Source fixture requires 1..256 committed events")
        commits = []
    checked = []
    used_ids = set()
    for i, event in enumerate(commits):
        item = _tx(event, f"sourceCommits[{i}]", errors)
        if item is not None:
            if item["sequence"] != i + 1:
                rejected.append("SOURCE_COMMIT_SEQUENCE_NOT_CONTIGUOUS")
            if item["operationId"] in used_ids:
                rejected.append("DUPLICATE_SOURCE_OPERATION")
            used_ids.add(item["operationId"])
            checked.append(item)
    aborted = record["abortedOperationIds"]
    if (not isinstance(aborted, list) or
            any(not isinstance(x, str) or len(x) < 3 for x in aborted)):
        errors.append("Invalid abortedOperationIds")
        aborted = []
    if len(aborted) != len(set(aborted)) or used_ids.intersection(aborted):
        rejected.append("ABORTED_OPERATION_REUSED_OR_COMMITTED")
    snapshot = record["snapshot"]
    capture = record["capture"]
    target = record["target"]
    good = (_strict(snapshot, SNAPSHOT_KEYS, "snapshot", errors)
            and _strict(capture, CAPTURE_KEYS, "capture", errors)
            and _strict(target, TARGET_KEYS, "target", errors))
    if not good or errors:
        return _result("INVALID", errors, len(commits), 0)
    for name, item in (("snapshot", snapshot), ("capture", capture), ("target", target)):
        if item["sourceEpoch"] != epoch:
            rejected.append(f"{name.upper()}_SOURCE_EPOCH_CHANGED")
    cut, resume = snapshot["cutSequence"], capture["resumeAfterSequence"]
    last = capture["observedHeadSequence"]
    oldest = capture["oldestRetainedSequence"]
    applied = target["appliedSequence"]
    for name, value in (("cut", cut), ("resume", resume), ("last", last),
                        ("oldest", oldest), ("applied", applied)):
        if type(value) is not int or value < 0 or value > MAX_EVENTS:
            errors.append(name + ": invalid sequence")
    if errors:
        return _result("INVALID", errors, len(commits), 0)
    if not 0 <= cut <= len(commits):
        rejected.append("SNAPSHOT_CUT_BEYOND_SOURCE_LOG")
    if resume != cut:
        rejected.append("RESUME_CURSOR_NOT_EQUAL_SNAPSHOT_CUT")
    if oldest > cut + 1:
        rejected.append("REQUIRED_JOURNAL_HISTORY_EXPIRED")
    if oldest < 1:
        rejected.append("INVALID_LOG_RETENTION_POSITION")
    if last != len(commits):
        rejected.append("OBSERVED_HEAD_DOES_NOT_MATCH_SOURCE_FIXTURE")
    if applied != last:
        rejected.append("TARGET_CURSOR_MISMATCH")
    s_bal = _balance_map(snapshot["balances"], "snapshot.balances", errors)
    t_bal = _balance_map(target["balances"], "target.balances", errors)
    events = capture["events"]
    if not isinstance(events, list) or len(events) > MAX_EVENTS:
        errors.append("capture.events must be a bounded list")
        events = []
    validated_events = []
    for index, item in enumerate(events):
        valid = _tx(item, f"capture.events[{index}]", errors)
        if valid is not None:
            validated_events.append(valid)
            if valid["operationId"] in aborted:
                rejected.append("ABORTED_OPERATION_CAPTURED")
    if errors:
        return _result("INVALID", errors, len(commits), len(events))
    if len(checked) != len(commits) or initial is None or s_bal is None or t_bal is None:
        return _result("INVALID", errors or ["Incomplete source trace"],len(commits),len(events))
    if not (0 <= cut <= len(commits)):
        return _result("REJECT", rejected, len(commits), len(events))
    expected_cut = _replay(initial, checked[:cut], "sourceSnapshot", errors)
    if expected_cut != s_bal:
        rejected.append("SNAPSHOT_BALANCES_MISMATCH_SOURCE_CUT")
    expected_tail = checked[cut:]
    if len(events) != len(expected_tail):
        rejected.append("CAPTURED_TAIL_COUNT_MISMATCH")
    if events != expected_tail:
        rejected.append("CAPTURED_EVENTS_NOT_IDENTICAL_TO_SOURCE_COMMITS")
    sequences = [item["sequence"] for item in validated_events]
    if sequences != list(range(cut + 1, last + 1)):
        rejected.append("CAPTURED_SEQUENCE_GAP_DUPLICATE_OR_REORDER")
    actual_final = _replay(initial, checked, "sourceFinal", errors)
    captured_final = _replay(s_bal, validated_events, "captureReplay", errors)
    if actual_final != t_bal or captured_final != t_bal:
        rejected.append("TARGET_BALANCES_DO_NOT_MATCH_REPLAY")
    if errors:
        return _result("INVALID", errors, len(commits), len(events))
    return _result("REJECT" if rejected else "PASS_SYNTHETIC_HANDOFF_ORACLE",
                   rejected, len(commits), len(events))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    args = parser.parse_args()
    try:
        trace = json.loads(args.trace.read_text(encoding="utf-8"))
        result = assess(trace)
    except (OSError, ValueError, TypeError) as ex:
        result = _result("INVALID", ["Input cannot be read: " + str(ex)], 0, 0)
    print(json.dumps(result, sort_keys=True, indent=2))
    return {"PASS_SYNTHETIC_HANDOFF_ORACLE": 0, "REJECT": 2, "INVALID": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
