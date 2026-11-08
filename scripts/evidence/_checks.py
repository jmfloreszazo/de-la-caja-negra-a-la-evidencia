"""Fail-closed checks shared by the campaign summary CLIs."""
import json


def require(condition, message):
    if not condition:
        raise SystemExit("Verification failed: " + message)


def compare_summary(path, expected, *, write_summary=False):
    """Compare parsed JSON; only explicitly create a missing summary, never replace it."""
    if path.exists():
        actual = json.loads(path.read_text(encoding="utf-8-sig"))
        require(actual == expected, f"summary differs semantically: {path}")
    elif write_summary:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(expected, indent=2) + "\n")
    else:
        raise SystemExit(f"Verification incomplete: summary missing: {path} (use --write-summary to create it)")
