#!/usr/bin/env python3
"""Independently audit one original live .NET/SQL loopback-TCP fault report.

Consumes saved original run.py JSON; DOES NOT trust a summary PASS alone.
Does not contact a customer, operate an ATM, reconstruct bank authorization
or imply an actual WAN/kernel physical partition.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REQUIRED = {
    "tcp-drop-before-forward": "drop_before_forward",
    "tcp-drop-after-owner-response": "drop_after_upstream_reply",
    "tcp-delay-owner-response": "delay_after_upstream_reply",
    "tcp-held-reply-concurrent-recovery": "hold_until_recovery",
}


def validate(report: dict) -> list[str]:
    problems = []
    if not isinstance(report, dict) or report.get("status") != "PASS":
        return ["Native original report missing or not PASS"]
    scope = report.get("scope")
    extra = report.get("transport_scope")
    if not isinstance(scope, dict) or not isinstance(extra, dict):
        return ["Original reports missing explicit fixture scope"]
    for key in ("physical_cash", "bank_policy_approved", "protocol_certified",
                "capacity_claim", "physical_ha"):
        if scope.get(key) is not False:
            problems.append("Unsafe original scope flag: " + key)
    if scope.get("synthetic") is not True:
        problems.append("Original money fixture is not declared synthetic")
    if extra.get("real_loopback_tcp") is not True or extra.get("controlled_proxy_faults") != 4:
        problems.append("Four real local socket faults not recorded")
    for key in ("real_eth_wan_partition", "real_atm_switch", "real_cash",
                "bank_policy_approved", "production_approved"):
        if extra.get(key) is not False:
            problems.append("Claim exceeds loopback scope: " + key)
    if extra.get("todmG2") != "INCONCLUSIVE" or extra.get("todmG6") != "BLOCK":
        problems.append("Migration gate was artificially promoted")
    source = os.environ.get("SOURCE_HEAD_SHA")
    if source and (report.get("checkout_sha") != source or report.get("source_sha") != source):
        problems.append("Original source/checkout SHA did not match Actions head")
    cases = report.get("cases")
    if not isinstance(cases, list):
        return problems + ["Missing original per-case observations"]
    by_name = {case.get("name"): case for case in cases if isinstance(case, dict)}
    if len(by_name) != len(cases) or len(cases) != 14:
        problems.append("Expected 14 distinct native cases: original 10 plus 4 TCP cases")
    for name, mode in REQUIRED.items():
        case = by_name.get(name)
        if not case or case.get("status") != "PASS":
            problems.append("Missing or failed real transport case: " + name)
            continue
        witness = case.get("transport_witness")
        before = case.get("before_retry_snapshot")
        after = case.get("snapshot")
        observations = case.get("http")
        if not isinstance(witness, dict) or not isinstance(before, dict) or not isinstance(after, dict):
            problems.append(name + ": missing raw proxy or SQL witness")
            continue
        if (witness.get("mode") != mode
                or witness.get("real_loopback_socket_used") is not True
                or witness.get("physical_link_partition_tested") is not False
                or witness.get("native_bank_issuer_tested") is not False
                or witness.get("physical_cash_device_tested") is not False
                or witness.get("production_approved") is not False
                or not isinstance(witness.get("request_sha256"), str)
                or len(witness["request_sha256"]) != 64
                or not isinstance(witness.get("request_bytes"), int)
                or witness["request_bytes"] <= 0):
            problems.append(name + ": proxy witness lacks source, limits or actual request bytes")
        if (not isinstance(observations, list) or not observations
                or observations[0].get("route") != "transfer"
                or observations[0].get("client_status") != "UNKNOWN"
                or observations[0].get("code") is not None):
            problems.append(name + ": HTTP client did not genuinely observe lost/late response")
        core_before = before.get("core", {})
        core_after = after.get("core", {})
        for key in ("operations", "postings", "outbox"):
            if not isinstance(core_before.get(key), list) or not isinstance(core_after.get(key), list):
                problems.append(name + ": no read-only original SQL snapshot of " + key)
        if name == "tcp-drop-before-forward":
            if witness.get("upstream_connected") is not False or witness.get("request_forwarded") is not False:
                problems.append(name + ": drop before forwarding nevertheless contacted owner")
            if any(core_before.get(key) for key in ("operations", "postings", "outbox")):
                problems.append(name + ": lost request caused original issuer money effect")
            if not (len(observations) >= 2 and observations[1].get("response", {}).get("duplicate") is False):
                problems.append(name + ": first safe retry did not use original identity")
        else:
            if (witness.get("upstream_connected") is not True
                    or witness.get("request_forwarded") is not True
                    or witness.get("upstream_response_status") != 200
                    or witness.get("upstream_response_headers_seen") is not True
                    or case.get("oracle_before_retry", {}).get("status") != "PASS"):
                problems.append(name + ": original core commit+oracle before retry unverified")
            if (len(core_before.get("operations", [])) != 1
                    or core_before["operations"][0].get("state") != "COMMITTED"
                    or len(core_before.get("postings", [])) != 2
                    or len(core_before.get("outbox", [])) != 1):
                problems.append(name + ": original core COMMIT absent/duplicated before retry")
            if not (len(observations) >= 3
                    and observations[1].get("response", {}).get("state") == "COMMITTED"
                    and observations[2].get("response", {}).get("duplicate") is True):
                problems.append(name + ": original idempotent status/replay chain is missing")
        if mode not in ("delay_after_upstream_reply", "hold_until_recovery") and witness.get("downstream_response_bytes") != 0:
            problems.append(name + ": proxy may have delivered an HTTP response")
        if mode == "delay_after_upstream_reply" and witness.get("delay_seconds") != 0.8:
            problems.append(name + ": bounded delay witness absent")
        if name == "tcp-held-reply-concurrent-recovery":
            held = case.get("held_recovery")
            if not isinstance(held, dict):
                problems.append(name + ": held-reply recovery witness missing")
            else:
                times = (
                    witness.get("upstream_reply_seen_monotonic_ns"),
                    held.get("recovery_completed_monotonic_ns"),
                    witness.get("release_signalled_monotonic_ns"),
                    witness.get("response_release_monotonic_ns"),
                )
                if (not all(type(t) is int and t > 0 for t in times)
                        or not (times[0] < times[1] <= times[2] <= times[3])):
                    problems.append(name + ": old response was not held beyond status/retries")
                burst = held.get("replay_results")
                if (held.get("status_state") != "COMMITTED" or
                        held.get("replay_count") != 8 or
                        not isinstance(burst, list) or len(burst) != 8 or
                        not all(isinstance(b, dict) and
                                b.get("state") == "COMMITTED" and
                                b.get("duplicate") is True and
                                b.get("postedCents") == 6000 for b in burst)):
                    problems.append(name + ": eight concurrent original-ID replays not witnessed")
                if held.get("conflict_result", {}).get("status") != "ID_CONFLICT":
                    problems.append(name + ": changed-amount financial replay not refused")
                early = held.get("sql_before_old_ack")
                if not isinstance(early, dict) or not isinstance(early.get("core"), dict):
                    problems.append(name + ": SQL state before old response release missing")
                else:
                    source = early["core"]
                    if (len(source.get("operations", [])) != 1 or
                            len(source.get("postings", [])) != 2 or
                            len(source.get("outbox", [])) != 1 or
                            source["operations"][0].get("state") != "COMMITTED"):
                        problems.append(name + ": multiple financial effects before old reply release")
                if not isinstance(observations, list) or len(observations) != 11:
                    problems.append(name + ": missing concurrent HTTP and conflict observations")
                else:
                    originals = case.get("offered", {})
                    if not isinstance(originals, dict) or len(originals) != 1:
                        problems.append(name + ": original operation intent absent")
                    else:
                        original_id = next(iter(originals))
                        if (observations[1].get("route") != "operations/" + original_id
                                or observations[1].get("response", {}).get("state") != "COMMITTED"
                                or any(o.get("route") != "transfer" or
                                       o.get("request", {}).get("operationId") != original_id or
                                       o.get("response", {}).get("duplicate") is not True
                                       for o in observations[2:10])
                                or observations[10].get("request", {}).get("operationId") != original_id
                                or observations[10].get("request", {}).get("amountCents") != 5000
                                or observations[10].get("response", {}).get("status") != "ID_CONFLICT"):
                            problems.append(name + ": ambiguous original-ID, burst or conflict chain")
        if case.get("oracle", {}).get("status") != "PASS":
            problems.append(name + ": independent SQL financial oracle not PASS after replay")
        if (len(core_after.get("operations", [])) != 1
                or len(core_after.get("postings", [])) != 2
                or len(core_after.get("outbox", [])) != 1):
            problems.append(name + ": duplicate operation/posting/outbox after retry")
        balances = core_after.get("accounts", [])
        if not isinstance(balances, list) or {r["id"]: r["balance"] for r in balances} != {
                1: 4000, 2: 16000, 3: 0}:
            problems.append(name + ": missing conserved financial balance after transport fault")
        if after.get("device", {}).get("device_commands") != []:
            problems.append(name + ": digital transport probe unexpectedly invoked cash device")
    if any(c.get("status") != "PASS" for c in cases if isinstance(c, dict)):
        problems.append("Any original native case failed")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        errors = validate(report)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        errors = ["Unreadable or invalid original report: " + str(exc)]
    result = {
        "status": "PASS_BOUNDED_LIVE_LOOPBACK_TRANSPORT" if not errors else "REJECT",
        "errors": errors,
        "realLoopbackTcpSocketTested": not errors,
        "physicalWanPartitionTested": False,
        "realAtmOrCardNetworkTested": False,
        "bankAcceptance": False,
        "todmG2": "INCONCLUSIVE", "todmG6": "BLOCK",
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
