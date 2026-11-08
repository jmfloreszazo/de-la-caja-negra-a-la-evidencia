"""Verify preserved original source bytes, never substitute current code for a past run."""
import hashlib
from pathlib import PurePosixPath
import re


def verify_historical_source(root, commit, path, expected):
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Historical source requires a full commit SHA")
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("Historical source requires a SHA256 digest")
    relative = PurePosixPath(path)
    if relative.is_absolute() or ".." in relative.parts or "\\" in path or ":" in path:
        raise ValueError("Historical source requires a relative repository path")
    raw = (root / "evidence" / "historical-source" / commit / relative).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected:
        raise ValueError(f"Historical source mismatch: {commit}:{path}: {expected} != {actual}")
