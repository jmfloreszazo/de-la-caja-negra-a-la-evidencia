"""Fail-closed coverage accounting; source presence is not verified business semantics."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KINDS = {"EXISTING_SYNTHETIC_EVIDENCE", "NOT_DEMONSTRATED", "DESIGN_HYPOTHESIS_ONLY"}
EXPECTED_FIELDS = {"id", "cap", "requirement", "status", "sources", "nextGate"}
DOC_FIELDS = {"schemaVersion", "title", "classification", "context", "immutableBaselines",
              "g6Authorization", "capabilities", "assumptions"}


class GapError(ValueError):
    pass


def evaluate(document: dict, root: Path = ROOT) -> dict:
    if not isinstance(document, dict) or set(document) != DOC_FIELDS:
        raise GapError("Unexpected or missing catalog fields")
    if document["schemaVersion"] != "brownfield-gap-1":
        raise GapError("Unsupported contract version")
    if (document["context"] != "BROWNFIELD_MODERNIZATION" or
        document["classification"] != "RESEARCH_INVENTORY_NOT_PRODUCTION_APPROVAL" or
        document["g6Authorization"] != "BLOCK"):
        raise GapError("Business authority or experimental scope cannot be promoted by this catalog")
    if not all(isinstance(document[k], str) and document[k].strip() for k in ("title",)):
        raise GapError("Missing catalog title")
    if not isinstance(document["assumptions"], list) or not document["assumptions"]:
        raise GapError("Limitations must be documented")
    if not all(isinstance(x, str) and x.strip() for x in document["assumptions"]):
        raise GapError("Malformed limitation")
    if not isinstance(document["immutableBaselines"], list) or not document["immutableBaselines"]:
        raise GapError("Protected baseline references required")
    paths = set()

    def require_source(rel: str) -> None:
        if not isinstance(rel, str) or not rel or rel.startswith("/") or "\\" in rel:
            raise GapError("Invalid source path")
        source = (root / rel).resolve()
        if not source.is_relative_to(root.resolve()) or not source.is_file():
            raise GapError(f"Unresolvable or unsafe source: {rel}")
        paths.add(rel)

    for path in document["immutableBaselines"]:
        require_source(path)

    capabilities = document["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        raise GapError("Non-empty capability inventory required")
    ids = set()
    statuses = Counter()
    for item in capabilities:
        if not isinstance(item, dict) or set(item) != EXPECTED_FIELDS:
            raise GapError("Malformed requirement record")
        ident = item["id"]
        if not isinstance(ident, str) or not re.fullmatch(r"BF-\d{3}", ident) or ident in ids:
            raise GapError("Duplicate or invalid stable requirement ID")
        ids.add(ident)
        if item["cap"] not in {"CAP-007", "CAP-005"}:
            raise GapError("Out-of-scope capability")
        if item["status"] not in KINDS:
            raise GapError("Unsupported status; this gate cannot grant approval")
        for key in ("requirement", "nextGate"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise GapError(f"{ident}: {key} is required")
        sources = item["sources"]
        if not isinstance(sources, list) or len(sources) != len(set(sources)):
            raise GapError(f"{ident}: invalid or repeated evidence source")
        if item["status"] == "NOT_DEMONSTRATED" and sources:
            raise GapError(f"{ident}: no proof is claimed; remove misleading sources")
        if item["status"] != "NOT_DEMONSTRATED" and not sources:
            raise GapError(f"{ident}: technical/design claim must cite its input")
        for path in sources:
            require_source(path)
        statuses[item["status"]] += 1

    if not {x["cap"] for x in capabilities} == {"CAP-007", "CAP-005"}:
        raise GapError("Both target capabilities required")
    return {
        "scope": "SYNTHETIC_GAP_ACCOUNTING_ONLY",
        "requirements": len(capabilities),
        "statuses": dict(sorted(statuses.items())),
        "trackedSourcePaths": len(paths),
        "bankApprovedRequirements": 0,
        "productionEquivalent": False,
        "todmG6": "BLOCK",
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.catalog.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, GapError) as ex:
        print(json.dumps({"status": "REJECTED", "reason": str(ex)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
