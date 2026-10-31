"""Fail-closed placement preconditions for isolated E2-F10-C01 probes.

Orleans grain placement is neither financial COMMIT authority nor physical HA.
A successful reachability check alone cannot prove both silos host grains.
"""


def classify_placement(nodes: dict, expected_accounts: set[int],
                       membership: dict, require_dual: bool) -> dict:
    observed = {int(k): str(v).split(":", 1)[0]
                for k, v in nodes.items()}
    if set(observed) != expected_accounts:
        raise AssertionError("Placement sample cardinality/keys changed")
    allowed = {"e2f10-primary", "e2f10-secondary"}
    if not set(observed.values()) <= allowed:
        raise AssertionError("Unknown silo hosting a sampled grain")
    rows = membership.get("rows")
    if not isinstance(rows, list):
        raise AssertionError("Missing independent SQL membership rows")
    statuses = {int(row[2]): int(row[3]) for row in rows}
    expected = ({11150: 3, 11151: 3} if require_dual
                else {11150: 3, 11151: 6})
    if statuses != expected:
        raise AssertionError("SQL membership does not meet preregistered state")
    occupied = set(observed.values())
    placement_ok = (
        occupied == allowed if require_dual
        else occupied == {"e2f10-primary"}
    )
    return {
        "classification": (
            "PLACEMENT_PRECONDITION_SATISFIED"
            if placement_ok else "PLACEMENT_PRECONDITION_NOT_SATISFIED"
        ),
        "financialTransferTestPerformed": False,
        "bankLedgerEffectClaim": False,
        "placementSatisfiesPrecondition": placement_ok,
        "membershipStatuses": statuses,
        "accountsSampled": len(observed),
        "siloCounts": {
            silo: sum(name == silo for name in observed.values())
            for silo in ("e2f10-primary", "e2f10-secondary")
        },
        "accountsBySilo": {
            silo: sorted(
                account for account, host in observed.items() if host == silo
            ) for silo in ("e2f10-primary", "e2f10-secondary")
        },
        "reason": (
            "Sampled grain activations on each expected silo required; "
            "network reachability does not prove placement. Fresh-key "
            "identity probes are diagnostic only; they do NOT replace the "
            "original financial-account 1..16 precondition."
        ),
    }
