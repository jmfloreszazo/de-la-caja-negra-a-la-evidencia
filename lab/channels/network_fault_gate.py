#!/usr/bin/env python3
"""Strict offline per-hop ATM/switch/core failure-trace consistency oracle.

All traces and their "source" snapshots are fictional, with no TCP partition,
ISO 8583, native switch, issuer, cash device or independent customer evidence.
No output grants permission to retry under a new ID, debit, dispense, reverse,
switch a writer or approve stand-in. The incumbent source remains authoritative.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLASSIFICATION = "SYNTHETIC_PER_HOP_NETWORK_FAULT_TRACE_NOT_PHYSICAL_PARTITION"
ROOT_KEYS = {
    "schemaVersion", "classification", "policy", "nativeNetworkExecution",
    "bankAuthorization", "deviceHardwareObserved", "scenarios",
}
SCENARIO_KEYS = {
    "id", "operationId", "sourceEpoch", "activeEpoch", "amountMinor",
    "issuerDecision", "deviceState", "deviceDispensedMinor",
    "deviceJournalId", "ledgerPostedMinor", "events",
}
EVENT_KEYS = {"step", "kind", "link", "sourceEpoch"}
LINKS = {"ATM_SWITCH", "SWITCH_CORE", "ISSUER", "DEVICE", "CONTROL"}
KINDS = {
    "ATM_REQUEST": "ATM_SWITCH",
    "ATM_SWITCH_DELIVERED": "ATM_SWITCH",
    "SWITCH_CORE_DELIVERED": "SWITCH_CORE",
    "ISSUER_COMMITTED": "ISSUER",
    "LINK_DOWN": "network",
    "LINK_UP": "network",
    "ATM_REQUEST_DROPPED": "ATM_SWITCH",
    "SWITCH_CORE_DROPPED": "SWITCH_CORE",
    "ISSUER_REPLY_LOST": "SWITCH_CORE",
    "ISSUER_STATUS_CONFIRMED": "ISSUER",
    "ATM_APPROVAL_DELIVERED": "ATM_SWITCH",
    "DEVICE_COMMAND_SENT": "DEVICE",
    "DEVICE_RESPONSE_UNKNOWN": "DEVICE",
    "DEVICE_JOURNAL_FINAL": "DEVICE",
    "FINAL_LEDGER_POSTING": "ISSUER",
    "LATE_ADVICE": "SWITCH_CORE",
    "WRITER_CUTOVER": "CONTROL",
    "LATE_OLD_REPLY": "SWITCH_CORE",
    "STAND_IN_REQUEST_DENIED": "CONTROL",
}


def summary(status, errors, outcomes=None):
    return {
        "status": status,
        "errors": sorted(set(errors)),
        "outcomes": outcomes or {},
        "classification": "OFFLINE_TRACE_ONLY_NO_REAL_NETWORK_PARTITION",
        "physicalLinkCutTested": False,
        "nativeIssuerLogAuthenticated": False,
        "physicalCashJournalAuthenticated": False,
        "delegatedStandInAuthority": False,
        "automaticAuthorizationAllowed": False,
        "automaticDispenseAllowed": False,
        "automaticPostingAllowed": False,
        "automaticReversalAllowed": False,
        "cohortWriterCutoverAuthorized": False,
        "productionApproved": False,
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
    }


def exact(value, keys, path, errors):
    if not isinstance(value, dict) or set(value) != keys:
        errors.append(path + ": unexpected or missing fields")
        return False
    return True


def ident(value):
    return isinstance(value, str) and 3 <= len(value) <= 80 and value == value.strip()


def nonnegative(value):
    return type(value) is int and 0 <= value <= 1_000_000


def analyze_case(case):
    invalid, blocked = [], []
    if not exact(case, SCENARIO_KEYS, "scenario", invalid):
        return "INVALID", invalid, "NOT_EVALUATED"
    for key in ("id", "operationId", "sourceEpoch", "activeEpoch"):
        if not ident(case[key]):
            invalid.append("Invalid identity " + key)
    if not nonnegative(case["amountMinor"]) or case["amountMinor"] == 0:
        invalid.append("Invalid requested cash amount")
    if case["issuerDecision"] not in ("APPROVED", "NOT_OBSERVED"):
        invalid.append("Only declared core approval or absence of proof supported")
    if case["deviceState"] not in ("NOT_SENT", "UNKNOWN", "FINAL"):
        invalid.append("Invalid device outcome")
    device = case["deviceDispensedMinor"]
    journal = case["deviceJournalId"]
    if case["deviceState"] == "FINAL":
        if not nonnegative(device) or not ident(journal):
            invalid.append("Final device requires bounded cash amount and journal identity")
    elif device is not None or journal is not None:
        invalid.append("Nonfinal device may not claim cash amount or journal ID")
    if not nonnegative(case["ledgerPostedMinor"]):
        invalid.append("Ledger posting must be bounded integer minor units")
    events = case["events"]
    if not isinstance(events, list) or not 1 <= len(events) <= 100:
        invalid.append("Event trace must contain 1..100 observations")
        return "INVALID", invalid, "NOT_EVALUATED"
    for i, ev in enumerate(events):
        if not exact(ev, EVENT_KEYS, f"events[{i}]", invalid):
            continue
        if (type(ev["step"]) is not int or ev["step"] != i + 1
                or ev["kind"] not in KINDS or ev["link"] not in LINKS
                or not ident(ev["sourceEpoch"])):
            invalid.append(f"events[{i}]: invalid step/kind/link/epoch")
        elif ((KINDS[ev["kind"]] == "network"
               and ev["link"] not in ("ATM_SWITCH", "SWITCH_CORE"))
              or (KINDS[ev["kind"]] != "network"
                  and ev["link"] != KINDS[ev["kind"]])):
            invalid.append(f"events[{i}]: event assigned to wrong hop")
    if invalid:
        return "INVALID", invalid, "NOT_EVALUATED"

    link = {"ATM_SWITCH": True, "SWITCH_CORE": True}
    observed = set()
    cutover = False
    late_old = False
    trace = []
    for i, ev in enumerate(events):
        kind, hop = ev["kind"], ev["link"]
        prefix = f"events[{i}].{kind}"
        if kind == "WRITER_CUTOVER":
            if case["activeEpoch"] == case["sourceEpoch"]:
                blocked.append("CUTOVER_WITHOUT_NEW_WRITER_EPOCH")
            if "ISSUER_COMMITTED" not in observed:
                blocked.append("CUTOVER_BEFORE_ORIGINAL_ISSUER_DECISION")
            if cutover:
                blocked.append("DUPLICATE_WRITER_CUTOVER")
            if ev["sourceEpoch"] != case["activeEpoch"]:
                blocked.append("CUTOVER_EPOCH_NOT_ACTIVE_OWNER")
            cutover = True
        elif ev["sourceEpoch"] != case["sourceEpoch"]:
            blocked.append("FOREIGN_SOURCE_EPOCH_IN_OPERATION")
        if kind in ("LINK_DOWN", "LINK_UP"):
            link[hop] = kind == "LINK_UP"
        if kind == "ATM_REQUEST":
            if "ATM_REQUEST" in observed:
                blocked.append("SECOND_ATM_ORIGINAL_REQUEST")
            if not link["ATM_SWITCH"]:
                blocked.append("ATM_REQUEST_DURING_LINK_PARTITION")
        if kind == "ATM_SWITCH_DELIVERED":
            if not link["ATM_SWITCH"] or "ATM_REQUEST" not in observed:
                blocked.append("ATM_SWITCH_RECEIVE_WITHOUT_WORKING_PATH_OR_SEND")
        if kind == "SWITCH_CORE_DELIVERED":
            if (not link["SWITCH_CORE"] or "ATM_SWITCH_DELIVERED" not in observed):
                blocked.append("CORE_RECEIVE_WITHOUT_AUTHORIZED_PATH")
        if kind == "ISSUER_COMMITTED":
            if "SWITCH_CORE_DELIVERED" not in observed or cutover:
                blocked.append("ISSUER_COMMIT_WITHOUT_SOURCE_REQUEST_OR_AFTER_CUTOVER")
            if "ISSUER_COMMITTED" in observed:
                blocked.append("DUPLICATE_ISSUER_COMMIT")
        if kind == "ATM_REQUEST_DROPPED":
            if link["ATM_SWITCH"] or "ATM_REQUEST" not in observed:
                blocked.append("ATM_SWITCH_DROP_WITHOUT_PARTITION_AND_REQUEST")
        if kind == "SWITCH_CORE_DROPPED":
            if link["SWITCH_CORE"] or "ATM_SWITCH_DELIVERED" not in observed:
                blocked.append("SWITCH_CORE_DROP_WITHOUT_PARTITION_AND_REQUEST")
        if kind == "ISSUER_REPLY_LOST":
            if "ISSUER_COMMITTED" not in observed or link["SWITCH_CORE"]:
                blocked.append("LOST_CORE_REPLY_WITHOUT_COMMIT_OR_PARTITION")
        if kind == "ISSUER_STATUS_CONFIRMED":
            if ("ISSUER_COMMITTED" not in observed or "ISSUER_REPLY_LOST" not in observed
                    or not link["SWITCH_CORE"] or cutover):
                blocked.append("STATUS_RECOVERY_WITHOUT_ORIGINAL_COMMIT_AND_RESTORED_PATH")
        if kind == "ATM_APPROVAL_DELIVERED":
            if ("ISSUER_COMMITTED" not in observed or not link["ATM_SWITCH"]
                    or cutover):
                blocked.append("ATM_APPROVAL_WITHOUT_ISSUER_OR_PATH")
        if kind == "DEVICE_COMMAND_SENT":
            if "ATM_APPROVAL_DELIVERED" not in observed or cutover:
                blocked.append("DISPENSE_COMMAND_WITHOUT_ORIGINAL_APPROVAL")
            if "DEVICE_COMMAND_SENT" in observed:
                blocked.append("DUPLICATE_PHYSICAL_DISPENSE_COMMAND")
        if kind in ("DEVICE_RESPONSE_UNKNOWN", "DEVICE_JOURNAL_FINAL"):
            if "DEVICE_COMMAND_SENT" not in observed:
                blocked.append("DEVICE_RESULT_WITHOUT_COMMAND")
        if kind == "DEVICE_RESPONSE_UNKNOWN":
            if link["ATM_SWITCH"]:
                blocked.append("UNKNOWN_DEVICE_RESPONSE_WITHOUT_LOST_CHANNEL")
        if kind == "FINAL_LEDGER_POSTING":
            if "DEVICE_JOURNAL_FINAL" not in observed or cutover:
                blocked.append("FINANCIAL_POSTING_BEFORE_FINAL_DEVICE_PROOF")
            if "FINAL_LEDGER_POSTING" in observed:
                blocked.append("DUPLICATE_LEDGER_POSTING_EVENT")
        if kind == "LATE_ADVICE":
            if "DEVICE_COMMAND_SENT" not in observed:
                blocked.append("NETWORK_ADVICE_WITHOUT_ORIGINAL_DEVICE_COMMAND")
        if kind == "LATE_OLD_REPLY":
            late_old = True
            if not cutover or ev["sourceEpoch"] != case["sourceEpoch"]:
                blocked.append("OLD_REPLY_NOT_ISOLATED_AFTER_CUTOVER")
        if kind == "STAND_IN_REQUEST_DENIED":
            if link["SWITCH_CORE"]:
                blocked.append("STAND_IN_TEST_WITHOUT_UNREACHABLE_CORE")
            if "STAND_IN_REQUEST_DENIED" in observed:
                blocked.append("DUPLICATE_STAND_IN_DECISION")
        observed.add(kind)
        trace.append(prefix)
    if "ATM_REQUEST" not in observed:
        blocked.append("NO_ORIGINAL_OPERATION_REQUEST")

    core_proof = "ISSUER_COMMITTED" in observed
    if (case["issuerDecision"] == "APPROVED") != core_proof:
        blocked.append("ISSUER_SNAPSHOT_CONTRADICTS_COMMIT_TRACE")
    if case["deviceState"] == "NOT_SENT" and "DEVICE_COMMAND_SENT" in observed:
        blocked.append("DEVICE_NOT_SENT_CONTRADICTS_TRACE")
    if case["deviceState"] == "UNKNOWN" and (
            "DEVICE_RESPONSE_UNKNOWN" not in observed or
            "DEVICE_JOURNAL_FINAL" in observed):
        blocked.append("DEVICE_UNKNOWN_CONTRADICTS_TRACE")
    if case["deviceState"] == "FINAL" and "DEVICE_JOURNAL_FINAL" not in observed:
        blocked.append("DEVICE_FINAL_MISSING_JOURNAL_EVENT")
    if case["deviceState"] != "FINAL" and "DEVICE_JOURNAL_FINAL" in observed:
        blocked.append("FINAL_JOURNAL_CONTRADICTS_DEVICE_STATE")
    if case["deviceState"] == "FINAL" and device > case["amountMinor"]:
        blocked.append("DISPENSE_MORE_THAN_ISSUER_APPROVAL")
    expected_ledger = device if case["deviceState"] == "FINAL" else 0
    if case["ledgerPostedMinor"] != expected_ledger:
        blocked.append("LEDGER_DOES_NOT_MATCH_FINAL_DEVICE_CASH")
    if (case["ledgerPostedMinor"] > 0) != ("FINAL_LEDGER_POSTING" in observed):
        blocked.append("LEDGER_POSTING_TRACE_MISMATCH")
    if case["activeEpoch"] != case["sourceEpoch"] and not cutover:
        blocked.append("OWNER_EPOCH_CHANGED_WITHOUT_CUTOVER_WITNESS")
    if case["activeEpoch"] == case["sourceEpoch"] and late_old:
        blocked.append("LATE_OLD_REPLY_WITHOUT_NEW_OWNER")
    if "STAND_IN_REQUEST_DENIED" in observed and (
            core_proof or case["ledgerPostedMinor"] != 0 or
            case["deviceState"] != "NOT_SENT"):
        blocked.append("UNAUTHORIZED_STAND_IN_FINANCIAL_EFFECT")
    if blocked:
        return "REJECT", blocked, "BLOCKED_CORRUPT_OR_UNSUPPORTED_TRACE"
    if cutover:
        return "PASS", [], "QUARANTINED_OLD_OWNER_REPLY"
    if "STAND_IN_REQUEST_DENIED" in observed:
        return "PASS", [], "STAND_IN_DENIED"
    if case["deviceState"] == "UNKNOWN":
        return "PASS", [], "CASH_UNKNOWN_NO_REDISPENSE"
    if case["deviceState"] == "FINAL":
        return "PASS", [], (
            "PARTIAL_CASH_RECONCILED_SYNTHETICALLY"
            if device < case["amountMinor"] else "FULL_CASH_RECONCILED_SYNTHETICALLY")
    if core_proof and "ISSUER_STATUS_CONFIRMED" in observed:
        return "PASS", [], "AUTHORIZATION_RECOVERED_BY_STATUS"
    if core_proof:
        return "PASS", [], "AUTHORIZATION_KNOWN_ONLY_TO_ISSUER"
    return "PASS", [], "NO_CORE_AUTHORIZATION_EVIDENCE"


def assess(data):
    invalid, rejected, outcomes = [], [], {}
    if not exact(data, ROOT_KEYS, "root", invalid):
        return summary("INVALID", invalid)
    if data["schemaVersion"] != 1 or data["classification"] != CLASSIFICATION:
        invalid.append("Unrecognized schema or synthetic classification")
    if data["policy"] != "NO_STANDIN_DELEGATION":
        invalid.append("Cannot fabricate delegated offline issuer policy")
    for field in ("nativeNetworkExecution", "bankAuthorization", "deviceHardwareObserved"):
        if data[field] is not False:
            invalid.append(field + " cannot self-attest production evidence")
    cases = data["scenarios"]
    if not isinstance(cases, list) or not 1 <= len(cases) <= 64:
        invalid.append("Expected 1..64 synthetic test scenarios")
        return summary("INVALID", invalid)
    used_ops = set()
    used_ids = set()
    used_journals = set()
    for index, case in enumerate(cases):
        status, errors, outcome = analyze_case(case)
        if status == "INVALID":
            invalid.extend(f"scenario[{index}]: {e}" for e in errors)
            continue
        if not ident(case["id"]) or case["id"] in used_ids:
            rejected.append("REUSED_OR_INVALID_SCENARIO_ID")
        used_ids.add(case["id"])
        if case["operationId"] in used_ops:
            rejected.append("REUSED_OPERATION_ACROSS_SCENARIOS")
        used_ops.add(case["operationId"])
        if case["deviceJournalId"] is not None:
            if case["deviceJournalId"] in used_journals:
                rejected.append("REUSED_PHYSICAL_JOURNAL_ID")
            used_journals.add(case["deviceJournalId"])
        if status == "REJECT":
            rejected.extend(f"{case['id']}: {e}" for e in errors)
        outcomes[case["id"]] = outcome
    if invalid:
        return summary("INVALID", invalid)
    return summary("REJECT" if rejected else "PASS_SYNTHETIC_HOP_CONSISTENCY",
                   rejected, outcomes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    try:
        result = assess(json.loads(args.fixture.read_text(encoding="utf-8")))
    except (ValueError, OSError) as exc:
        result = summary("INVALID", [f"Unreadable fixture: {exc}"])
    print(json.dumps(result, sort_keys=True, indent=2))
    return {"PASS_SYNTHETIC_HOP_CONSISTENCY": 0, "REJECT": 2, "INVALID": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
