"""Accept only the C04 client's explicit pre-dispatch startup deadline."""
import json


def classify_startup_deadline(returncode, stderr):
    if returncode != 74:
        raise AssertionError("Not the bounded C04 client exit code")
    try:
        result = json.loads(stderr)
    except (ValueError, TypeError) as exc:
        raise AssertionError("Missing structured C04 client diagnostic") from exc
    expected = {"status": "CLIENT_STARTUP_DEADLINE",
                "phase": "BEFORE_FINANCIAL_DISPATCH", "deadlineSeconds": 20,
                "financialCommandsDispatched": 0}
    if result != expected or type(result.get("financialCommandsDispatched")) is not int:
        raise AssertionError("Unrelated or post-dispatch client failure")
    return {"kind": "client_failure_or_timeout", "exitCode": returncode,
            "diagnostic": result, "acknowledgedCommitted": False,
            "semantics": "CLIENT_STARTUP_DEADLINE_NO_FINANCIAL_DISPATCH_NO_ROLLBACK_INFERRED"}
