#!/usr/bin/env python3
"""Bounded forensic correlation for fictional ATM advice and cash journals.

Not ISO 8583, NDC/DDC, card certification, a bank policy, a stand-in
authorization service, an authenticated device proof or a financial posting
engine. No decision here is permission to dispense, post or reverse money.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCHEMA = "SYNTHETIC_CHANNEL_OBSERVATIONS_NO_NETWORK_OR_DEVICE_AUTHENTICITY"
ROOT = {
    "schemaVersion", "classification", "sourceEpoch", "customerApproval",
    "nativeNetworkTested", "standInDelegationApproved", "authorizations",
    "deviceOutcomes", "corePostings", "networkMessages",
}
AUTH = {
    "operationId", "authorizationId", "terminalId", "networkTrace",
    "retrievalReference", "requestedMinor", "route", "decision",
}
DEVICE = {
    "operationId", "commandId", "terminalId", "deviceJournalId",
    "state", "dispensedMinor",
}
POSTING = {"operationId", "postingId", "amountMinor"}
MESSAGE = {
    "messageId", "operationId", "authorizationId", "terminalId",
    "networkTrace", "retrievalReference", "messageType", "amountMinor",
}


def report(status: str, problems: list[str], outcomes=None):
    return {
        "status": status,
        "errors": sorted(set(problems)),
        "outcomes": outcomes or {},
        "classification": "SYNTHETIC_CORRELATION_ONLY_NO_AUTO_FINANCIAL_EFFECT",
        "realCardNetworkTested": False,
        "physicalDeviceJournalAuthenticated": False,
        "originalIssuerDataVerified": False,
        "standInDelegationApproved": False,
        "safeToAutoDispense": False,
        "safeToAutoPost": False,
        "safeToAutoReverse": False,
        "productionApproved": False,
        "todmG2": "INCONCLUSIVE",
        "todmG6": "BLOCK",
    }


def fields(obj, expected, label, errors):
    if not isinstance(obj, dict) or set(obj) != expected:
        errors.append(label + ": invalid or unexpected fields")
        return False
    return True


def identity(value):
    return isinstance(value, str) and 3 <= len(value) <= 64 and value.strip() == value


def amount(value, allow_zero=False):
    return (type(value) is int and (0 if allow_zero else 1) <= value <= 1_000_000)


def rows(record, key, keys, errors):
    value = record[key]
    if not isinstance(value, list) or len(value) > 256:
        errors.append(key + ": expected bounded array")
        return []
    for i, row in enumerate(value):
        fields(row, keys, f"{key}[{i}]", errors)
    return value


def assess(data):
    errors, blockers, outcomes = [], [], {}
    if not fields(data, ROOT, "root", errors):
        return report("INVALID", errors)
    if data["schemaVersion"] != 1 or data["classification"] != SCHEMA:
        errors.append("Unrecognized synthetic evidence classification")
    if any(data[k] is not False for k in (
            "customerApproval", "nativeNetworkTested", "standInDelegationApproved")):
        errors.append("Fixture may not self-certify bank/network/stand-in permission")
    if not identity(data["sourceEpoch"]):
        errors.append("Invalid issuer epoch")
    auths = rows(data, "authorizations", AUTH, errors)
    devices = rows(data, "deviceOutcomes", DEVICE, errors)
    postings = rows(data, "corePostings", POSTING, errors)
    messages = rows(data, "networkMessages", MESSAGE, errors)
    if errors:
        return report("INVALID", errors)

    by_op, auth_ids, receipts = {}, set(), set()
    for i, row in enumerate(auths):
        if (not all(identity(row[k]) for k in (
                "operationId", "authorizationId", "terminalId",
                "networkTrace", "retrievalReference")) or
                not amount(row["requestedMinor"]) or
                row["route"] not in ("CORE", "STAND_IN") or
                row["decision"] not in ("APPROVED", "DENIED")):
            errors.append(f"authorizations[{i}]: invalid identity, amount or decision")
            continue
        op = row["operationId"]
        if op in by_op or row["authorizationId"] in auth_ids:
            blockers.append("DUPLICATE_OPERATION_OR_AUTHORIZATION_ID")
        by_op[op] = row
        auth_ids.add(row["authorizationId"])
        if row["route"] == "STAND_IN" and row["decision"] != "DENIED":
            blockers.append("UNAUTHORIZED_STAND_IN_APPROVAL")
        if row["route"] == "CORE" and row["decision"] != "APPROVED":
            # A core denial could be modeled separately, but the original
            # fixture only admits approved core or denied stand-in operations.
            blockers.append("UNEXPECTED_CORE_DECISION")
    if not 1 <= len(auths) <= 256:
        errors.append("At least one bounded authorization required")

    by_device = {}
    for i, row in enumerate(devices):
        if (not all(identity(row[k]) for k in ("operationId", "commandId", "terminalId"))
                or row["state"] not in ("FINAL", "UNKNOWN")
                or (row["state"] == "FINAL" and (
                    not identity(row["deviceJournalId"]) or
                    not amount(row["dispensedMinor"], allow_zero=True)))
                or (row["state"] == "UNKNOWN" and (
                    row["deviceJournalId"] is not None or
                    row["dispensedMinor"] is not None))):
            errors.append(f"deviceOutcomes[{i}]: untrusted journal shape")
            continue
        if row["operationId"] in by_device:
            blockers.append("MULTIPLE_DEVICE_OUTCOMES_ONE_OPERATION")
        by_device[row["operationId"]] = row
        if row["state"] == "FINAL":
            if row["deviceJournalId"] in receipts:
                blockers.append("DUPLICATED_DEVICE_JOURNAL_ID")
            receipts.add(row["deviceJournalId"])

    by_post = {}
    post_ids = set()
    for i, row in enumerate(postings):
        if not all(identity(row[k]) for k in ("operationId", "postingId")) or not amount(row["amountMinor"]):
            errors.append(f"corePostings[{i}]: malformed financial posting")
            continue
        if row["operationId"] in by_post or row["postingId"] in post_ids:
            blockers.append("DUPLICATE_FINANCIAL_POSTING")
        by_post[row["operationId"]] = row
        post_ids.add(row["postingId"])

    seen_messages = {}
    message_types = ("ADVICE", "REVERSAL_REQUEST", "RETRY", "STAND_IN_REQUEST")
    advisory = {}
    for i, row in enumerate(messages):
        if (not all(identity(row[k]) for k in (
                "messageId", "operationId", "authorizationId",
                "terminalId", "networkTrace", "retrievalReference"))
                or row["messageType"] not in message_types
                or not amount(row["amountMinor"])):
            errors.append(f"networkMessages[{i}]: malformed network observation")
            continue
        mid = row["messageId"]
        if mid in seen_messages:
            if row != seen_messages[mid]:
                blockers.append("CONFLICTING_NETWORK_MESSAGE_REPLAY")
            continue  # byte-identical duplicate delivery is a no-op.
        seen_messages[mid] = row
        op = row["operationId"]
        base = by_op.get(op)
        if base is None:
            blockers.append("UNKNOWN_NETWORK_OPERATION")
            continue
        # STAN/RRN are *correlation fields*, not durable operation identity.
        # Do not enforce global STAN uniqueness; match the whole context.
        if any(row[k] != base[k] for k in (
                "authorizationId", "terminalId", "networkTrace",
                "retrievalReference")):
            blockers.append("NETWORK_CONTEXT_DOES_NOT_MATCH_OPERATION")
        if row["amountMinor"] > base["requestedMinor"]:
            blockers.append("NETWORK_AMOUNT_EXCEEDS_ORIGINAL_INTENT")
        if row["messageType"] == "STAND_IN_REQUEST" and base["route"] != "STAND_IN":
            blockers.append("STAND_IN_REQUEST_CONTEXT_MISMATCH")
        if row["messageType"] != "STAND_IN_REQUEST" and base["route"] == "STAND_IN":
            blockers.append("DENIED_STAND_IN_HAS_FINANCIAL_ADVICE")
        advisory.setdefault(op, []).append(row)

    if errors:
        return report("INVALID", errors)
    for op in set(by_device) | set(by_post):
        if op not in by_op:
            blockers.append("UNOWNED_DEVICE_OR_FINANCIAL_EFFECT")

    for op, auth in by_op.items():
        dev, post = by_device.get(op), by_post.get(op)
        adv = advisory.get(op, [])
        if auth["route"] == "STAND_IN":
            if dev or post:
                blockers.append("DENIED_STAND_IN_CREATED_EFFECT")
            outcomes[op] = "STAND_IN_DENIED"
            continue
        if not dev:
            blockers.append("AUTHORIZED_WITHOUT_DEVICE_OUTCOME_RECORD")
            outcomes[op] = "UNKNOWN_REQUIRES_DEVICE_EVIDENCE"
            continue
        if dev["commandId"] != "cash/" + op or dev["terminalId"] != auth["terminalId"]:
            blockers.append("DEVICE_COMMAND_OR_TERMINAL_MISMATCH")
        if dev["state"] == "UNKNOWN":
            outcomes[op] = "UNKNOWN_REQUIRES_DEVICE_EVIDENCE"
            if post:
                blockers.append("FINANCIAL_POSTING_WITH_UNKNOWN_CASH")
            # Advice is never device confirmation: no automatic posting.
        elif dev["dispensedMinor"] > auth["requestedMinor"]:
            blockers.append("DISPENSE_EXCEEDS_AUTHORIZED_AMOUNT")
        elif dev["dispensedMinor"] == 0:
            outcomes[op] = "FINAL_ZERO_CASH"
            if post:
                blockers.append("POSTING_FOR_ZERO_CASH")
        else:
            outcomes[op] = "MATCHED_PARTIAL_CASH" if (
                dev["dispensedMinor"] < auth["requestedMinor"]) else "MATCHED_FULL_CASH"
            if not post:
                blockers.append("DISPENSE_WITHOUT_MATCHING_FINANCIAL_POSTING")
            elif post["amountMinor"] != dev["dispensedMinor"]:
                blockers.append("FINANCIAL_AMOUNT_DIFFERS_FROM_DEVICE_JOURNAL")
        # Contradictory late advice is reviewable, not a reversal command.
        for msg in adv:
            if msg["messageType"] == "ADVICE" and dev["state"] == "FINAL" and (
                    msg["amountMinor"] != dev["dispensedMinor"]):
                blockers.append("LATE_ADVICE_DISAGREES_WITH_FINAL_DEVICE_PROOF")
            if msg["messageType"] == "REVERSAL_REQUEST" and (
                    dev["state"] == "UNKNOWN" or dev["dispensedMinor"] > 0):
                outcomes[op] = "MANUAL_REVIEW_REVERSAL_VS_DEVICE"
                blockers.append("REVERSAL_REQUEST_NEEDS_AUTHORIZED_MANUAL_DECISION")
    return report("REJECT" if blockers else "PASS_SYNTHETIC_CORRELATION_ONLY",
                  blockers, outcomes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.fixture.read_text(encoding="utf-8"))
        result = assess(data)
    except (OSError, ValueError) as ex:
        result = report("INVALID", [f"Unable to read fixture: {ex}"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return {"PASS_SYNTHETIC_CORRELATION_ONLY": 0, "REJECT": 2, "INVALID": 3}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
