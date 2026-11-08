"""Seal an explicitly enumerated local artifact inventory, without approving it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .validate import safe_path, strict_json
except ImportError:
    from validate import safe_path, strict_json


def seal(specification, root):
    result = strict_json(json.dumps(specification))
    for experiment in result["experiments"]:
        for item in experiment["artifacts"]:
            raw = safe_path(Path(root).resolve(), item["path"]).read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            if "sha256" in item and item["sha256"] != digest:
                raise ValueError("Refusing to reseal a changed artifact: " + item["id"])
            item["sha256"] = digest
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--root", default=Path.cwd(), type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        manifest = seal(strict_json(args.spec.read_bytes()), args.root)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(manifest, indent=2) + "\n")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"error": str(exc), "releaseOutcome": "BLOCK"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
