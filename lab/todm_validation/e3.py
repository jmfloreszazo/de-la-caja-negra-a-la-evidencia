"""Independent offline reconciliation of the bounded E3 PostgreSQL fixture."""
from __future__ import annotations

from collections import Counter, defaultdict
import copy


class ShapeError(ValueError):
    pass


def ledger_vectors(snapshot):
    if not isinstance(snapshot, dict):
        raise ShapeError("E3 ledger snapshot missing")
    widths = {"accounts": 2, "operations": 5, "postings": 3, "outbox": 2}
    for table, width in widths.items():
        rows = snapshot.get(table)
        if not isinstance(rows, list) or any(not isinstance(row, list) or len(row) != width for row in rows):
            raise ShapeError("Invalid E3 snapshot table: " + table)
    accounts = snapshot["accounts"]
    operations = snapshot["operations"]
    postings = snapshot["postings"]
    outbox = snapshot["outbox"]
    if any(type(key) is not int or type(balance) is not int for key, balance in accounts):
        raise ShapeError("Invalid E3 account values")
    if any(not isinstance(row[0], str) or any(type(v) is not int for v in row[1:4]) or row[4] not in ("COMMITTED", "REJECTED") for row in operations):
        raise ShapeError("Invalid E3 operation values")
    if any(not isinstance(op, str) or type(account) is not int or type(delta) is not int for op, account, delta in postings):
        raise ShapeError("Invalid E3 posting values")
    if any(not isinstance(op, str) or not isinstance(event, str) for op, event in outbox):
        raise ShapeError("Invalid E3 outbox values")
    by_operation, deltas = defaultdict(list), defaultdict(int)
    for op, account, delta in postings:
        by_operation[op].append((account, delta))
        deltas[account] += delta
    operation_map = {row[0]: row for row in operations}
    account_map = dict(accounts)
    outbox_counts = Counter(op for op, _ in outbox)
    return {
        "nonnegative": all(balance >= 0 for _, balance in accounts),
        "conserved": sum(balance for _, balance in accounts) == 1600000,
        "balancedPostings": all(len(rows) == 2 and sum(delta for _, delta in rows) == 0 for rows in by_operation.values()),
        "twoPostingsPerCommit": all(len(by_operation[op]) == 2 for op, _, _, _, status in operations if status == "COMMITTED"),
        "noPostingsForRejection": all(not by_operation[op] for op, _, _, _, status in operations if status == "REJECTED"),
        "outboxAtomic": all(outbox_counts[op] == 1 for op, _, _, _, status in operations if status == "COMMITTED")
            and all(op in operation_map and operation_map[op][4] == "COMMITTED" and event == "TransferCommitted" for op, event in outbox),
        "projectionAgrees": all(balance == 100000 + deltas[key] for key, balance in accounts),
        "fixtureStructure": len(accounts) == 16 and set(account_map) == set(range(1, 17))
            and len(operation_map) == len(operations) and len({(op, account) for op, account, _ in postings}) == len(postings)
            and all(op in operation_map and account in account_map for op, account, _ in postings),
        "postingMatchesRequest": all(src != dst and amount > 0 and src in account_map and dst in account_map
            and (status != "COMMITTED" or sorted(by_operation[op]) == sorted([(src, -amount), (dst, amount)]))
            for op, src, dst, amount, status in operations),
    }


def reconcile(report, documents):
    snapshot = documents.get("ledger")
    offers, planned = documents.get("offers"), documents.get("planned")
    checks = ledger_vectors(snapshot)
    if not isinstance(offers, list) or not isinstance(planned, list) or not planned:
        raise ShapeError("Actual and preregistered E3 offers required")
    required = ("operationId", "index", "src", "dst", "amountCents", "phase", "ratePerSecond", "replica", "scheduledSeconds")
    for rows in (offers, planned):
        if any(not isinstance(row, dict) or any(key not in row for key in required) or not isinstance(row["operationId"], str) for row in rows):
            raise ShapeError("Incomplete E3 offered request")
    actual_map = {row["operationId"]: row for row in offers}
    planned_map = {row["operationId"]: row for row in planned}
    operations = {row[0]: row for row in snapshot["operations"]}
    checks["plannedCoverage"] = len(actual_map) == len(offers) == len(planned) == len(planned_map) and set(actual_map) == set(planned_map)
    checks["plannedRequestsUnchanged"] = all(key in actual_map and all(actual_map[key][field] == row[field] for field in required) for key, row in planned_map.items())
    checks["noUnplannedPersistedOperations"] = set(operations).issubset(actual_map)
    acknowledged = set()
    checks["reconciledOffers"] = True
    allowed_outcomes = {"ACK_COMMITTED", "ACK_REJECTED", "AMBIGUOUS_TIMEOUT", "AMBIGUOUS_RESPONSE", "FAILED_CONNECT", "FAILED_RPC", "MISSED_SCHEDULE"}
    for key, offer in actual_map.items():
        outcome = offer.get("outcome")
        operation = operations.get(key)
        if outcome not in allowed_outcomes or offer.get("persistedStatus") != (operation[4] if operation else "ABSENT"):
            checks["reconciledOffers"] = False
        if operation and tuple(operation[1:4]) != (offer["src"], offer["dst"], offer["amountCents"]):
            checks["reconciledOffers"] = False
        if outcome == "ACK_COMMITTED":
            acknowledged.add(key)
            response = offer.get("response")
            if not operation or operation[4] != "COMMITTED" or not isinstance(response, dict) or response.get("operationId") != key or response.get("amountCents") != offer["amountCents"] or response.get("status") not in ("COMMITTED", "DUPLICATE_COMMITTED"):
                checks["reconciledOffers"] = False
        if outcome == "ACK_REJECTED" and (not operation or operation[4] != "REJECTED"):
            checks["reconciledOffers"] = False
        if outcome == "MISSED_SCHEDULE" and operation:
            checks["reconciledOffers"] = False
    committed = {key for key, row in operations.items() if row[4] == "COMMITTED"}
    observed_counts = {"persistedCommits": len(committed), "persistedOperations": len(operations),
                       "unacknowledgedPersistedCommits": len(committed - acknowledged)}
    reconciliation = report.get("reconciliation", {})
    checks["reconciliationCounters"] = all(reconciliation.get(key) == value for key, value in observed_counts.items())
    measurement = report.get("measurement", {})
    checks["measurementCounters"] = measurement.get("offered") == len(offers) and measurement.get("outcomes") == dict(Counter(row.get("outcome") for row in offers))
    events = report.get("processEvents")
    if not isinstance(events, list) or any(not isinstance(event, dict) for event in events):
        raise ShapeError("E3 process events missing")
    killed = [event for event in events if event.get("action") == "KILL_PROCESS"]
    restarted = [event for event in events if event.get("action") == "RESTART_PROCESS"]
    healthy = [event for event in events if event.get("action") == "RECOVERY_HEALTHY"]
    checks["recoveryTimeline"] = False
    checks["rawRecoveryAcknowledgment"] = False
    if len(killed) == len(restarted) == len(healthy) == 1:
        kill, restart, health = killed[0], restarted[0], healthy[0]
        times = [event.get("actualSeconds") for event in (kill, restart, health)]
        if all(type(value) in (int, float) and value >= 0 for value in times):
            checks["recoveryTimeline"] = times[0] < times[1] <= times[2] and kill.get("exitCode") == -9 and kill.get("replica") == restart.get("replica") == health.get("replica") == 0 and kill.get("pid") != restart.get("pid") == health.get("pid")
            checks["rawRecoveryAcknowledgment"] = report.get("recovery", {}).get("healthySeconds") == times[2] and any(row.get("replica") == 0 and row.get("outcome") == "ACK_COMMITTED" and type(row.get("dispatchSeconds")) in (int, float) and row["dispatchSeconds"] >= times[2] for row in offers)
    # Mutate a copy of the actual bound snapshot, never the original artifact.
    mutation = copy.deepcopy(snapshot)
    if not mutation["postings"]:
        raise ShapeError("No actual posting to qualify the E3 snapshot checker")
    mutation["postings"].pop()
    bad = ledger_vectors(mutation)
    qualified = not bad["twoPostingsPerCommit"] and not bad["projectionAgrees"]
    return checks, qualified
