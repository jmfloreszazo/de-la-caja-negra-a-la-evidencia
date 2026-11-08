"""Bounded decision tables, single-token traces and baseline byte checks; no approval engine."""

import argparse
import hashlib
import json
import re
from fractions import Fraction
from pathlib import Path, PureWindowsPath


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), "Expected an object")
    require(set(required) <= value.keys(), "Missing fields: " + str(sorted(set(required) - value.keys())))
    require(value.keys() <= set(required) | set(optional), "Unknown fields: " + str(sorted(value.keys() - set(required) - set(optional))))


def text(value):
    require(isinstance(value, str) and bool(value.strip()), "Expected nonempty text")


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,79}", value), "Invalid identifier")


def items(value):
    require(isinstance(value, list) and 0 < len(value) <= 1000, "Expected 1..1000 list items")
    return value


def unique(values):
    require(len(values) == len(set(values)), "Duplicate identifiers or values")


def safe_path(root, name):
    text(name)
    win = PureWindowsPath(name)
    parts = re.split(r"[\\/]", name)
    require(not win.drive and not win.root and all(p not in ("", ".", "..") for p in parts), "Path must be confined and relative")
    require(not any(":" in p for p in parts), "Device/stream paths are unsupported")
    root = Path(root).resolve()
    target = root.joinpath(*parts)
    current = root
    for part in parts:
        current = current / part
        require(not current.is_symlink() and not (hasattr(current, "is_junction") and current.is_junction()), "Links are unsupported")
    require(target.resolve().is_relative_to(root), "Path escapes root")
    return target


def number(value, kind):
    if kind == "integer":
        require(type(value) is int and abs(value) < 10**18, "Integer must have at most 18 digits; booleans are not integers")
        return Fraction(value)
    require(isinstance(value, str) and re.fullmatch(r"-?(0|[1-9][0-9]{0,17})(\.[0-9]{1,8})?", value), "Decimal must be a plain string with <=18 integer and <=8 fractional digits")
    return Fraction(value)


def value_check(value, spec):
    kind = spec["type"]
    if kind in ("integer", "decimal"):
        number(value, kind)
    elif kind == "string":
        require(isinstance(value, str), "Expected string")
    else:
        require(type(value) is bool, "Expected boolean")
    if "enum" in spec:
        require(value in spec["enum"], "Value outside enum")
    return value


def schema(spec):
    fields(spec, ["type"], ["enum"])
    require(spec["type"] in ("integer", "decimal", "string", "boolean"), "Unknown value type")
    if "enum" in spec:
        values = items(spec["enum"])
        for value in values:
            value_check(value, {"type": spec["type"]})
        unique(values)


def predicate(pred, inputs):
    fields(pred, ["variable", "operator", "value"])
    require(isinstance(pred["variable"], str) and pred["variable"] in inputs, "Unknown predicate variable")
    spec = inputs[pred["variable"]]
    allowed = ("eq", "ne", "lt", "le", "gt", "ge") if spec["type"] in ("integer", "decimal") else ("eq", "ne")
    require(pred["operator"] in allowed, "Unknown/unsupported predicate operator")
    value_check(pred["value"], spec)


def expression(expr, output, inputs):
    require(isinstance(expr, dict), "Expected output expression")
    if "constant" in expr:
        fields(expr, ["constant"])
        value_check(expr["constant"], output)
        return
    fields(expr, ["operation", "variables", "divisor", "scale", "rounding"])
    require(expr["operation"] == "multiplyDivide", "Unknown output operation")
    require(output["type"] in ("integer", "decimal"), "Arithmetic output must be numeric")
    require(isinstance(expr["variables"], list) and len(expr["variables"]) == 2, "multiplyDivide requires exactly two variables")
    for name in expr["variables"]:
        require(isinstance(name, str) and name in inputs and inputs[name]["type"] in ("integer", "decimal"), "Unknown/non-numeric arithmetic variable")
    require(number(expr["divisor"], "decimal") != 0, "Divisor cannot be zero")
    require(type(expr["scale"]) is int and 0 <= expr["scale"] <= 8, "Scale must be 0..8")
    require(output["type"] != "integer" or expr["scale"] == 0, "Integer output requires scale zero")
    require(expr["rounding"] in ("HALF_UP", "HALF_EVEN", "DOWN"), "Explicit rounding must be HALF_UP, HALF_EVEN or DOWN")


def validate_model(model):
    require(isinstance(model, dict), "Expected model object")
    kind = model.get("kind")
    require(kind in ("decisionTable", "processTrace"), "Unknown model kind")
    common = ["profileVersion", "kind", "id", "version", "baselineId", "sources", "adrs"]
    extra = ["hitPolicy", "inputs", "outputs", "rules"] if kind == "decisionTable" else ["states", "start", "ends", "transitions"]
    fields(model, common + extra)
    require(type(model["profileVersion"]) is int and model["profileVersion"] == 1, "Unsupported profile version")
    for key in ("id", "version", "baselineId"):
        identifier(model[key])
    for key in ("sources", "adrs"):
        links = items(model[key])
        for link in links:
            fields(link, ["id", "path"])
            identifier(link["id"])
            safe_path(Path.cwd(), link["path"])
        unique([link["id"] for link in links])
    if kind == "decisionTable":
        require(model["hitPolicy"] in ("UNIQUE", "FIRST"), "Only UNIQUE/FIRST are implemented")
        for key in ("inputs", "outputs"):
            require(isinstance(model[key], dict) and 0 < len(model[key]) <= 100, "Expected 1..100 named fields")
            for name, spec in model[key].items():
                identifier(name)
                schema(spec)
        rules = items(model["rules"])
        for rule in rules:
            fields(rule, ["id", "when", "then"])
            identifier(rule["id"])
            require(isinstance(rule["when"], list) and len(rule["when"]) <= 100, "Conditions must be a list of <=100 predicates")
            for pred in rule["when"]:
                predicate(pred, model["inputs"])
            fields(rule["then"], model["outputs"].keys())
            for name, expr in rule["then"].items():
                expression(expr, model["outputs"][name], model["inputs"])
        unique([rule["id"] for rule in rules])
    else:
        states = items(model["states"])
        for state in states:
            identifier(state)
        unique(states)
        identifier(model["start"])
        require(model["start"] in states, "Unknown start state")
        for end in items(model["ends"]):
            identifier(end)
            require(end in states and end != model["start"], "Unknown end or start is end")
        unique(model["ends"])
        edges = items(model["transitions"])
        for edge in edges:
            require(isinstance(edge, list) and len(edge) == 2, "Transition must be [from, to]")
            for state in edge:
                identifier(state)
                require(state in states, "Unknown transition state")
            require(edge[0] not in model["ends"] and edge[1] != model["start"], "Ends are terminal and start has no incoming transitions")
        unique([tuple(edge) for edge in edges])
        reached = {model["start"]}
        finishing = set(model["ends"])
        for _ in states:
            reached.update(b for a, b in edges if a in reached)
            finishing.update(a for a, b in edges if b in finishing)
        require(reached == set(states) and finishing == set(states), "Every state must be reachable and able to reach an end")
    return model


def report(status, reason, model=None, **details):
    result = {"status": status, "reason": reason, "productionApproved": False, **details}
    if model:
        result.update(modelId=model["id"], modelVersion=model["version"], baselineId=model["baselineId"])
    return result


def matches(pred, values, inputs):
    left, right = values[pred["variable"]], pred["value"]
    kind = inputs[pred["variable"]]["type"]
    if kind in ("integer", "decimal"):
        left, right = number(left, kind), number(right, kind)
    op = pred["operator"]
    if op == "eq":
        return left == right
    if op == "ne":
        return left != right
    if op == "lt":
        return left < right
    if op == "le":
        return left <= right
    if op == "gt":
        return left > right
    return left >= right


def calculate(expr, output, inputs, values):
    if "constant" in expr:
        return expr["constant"]
    a, b = expr["variables"]
    raw = number(values[a], inputs[a]["type"]) * number(values[b], inputs[b]["type"]) / number(expr["divisor"], "decimal")
    scaled = abs(raw) * 10**expr["scale"]
    whole, remainder = divmod(scaled.numerator, scaled.denominator)
    double = 2 * remainder
    if expr["rounding"] == "HALF_UP":
        whole += double >= scaled.denominator
    elif expr["rounding"] == "HALF_EVEN":
        whole += double > scaled.denominator or (double == scaled.denominator and whole % 2 == 1)
    signed = -whole if raw < 0 else whole
    if output["type"] == "integer":
        return value_check(signed, output)
    scale = expr["scale"]
    digits = str(abs(signed)).zfill(scale + 1)
    result = ("-" if signed < 0 else "") + (digits[:-scale] + "." + digits[-scale:] if scale else digits)
    return value_check(result, output)


def evaluate(model, values):
    validate_model(model)
    require(model["kind"] == "decisionTable", "Expected decision table")
    require(isinstance(values, dict), "Inputs must be an object")
    require(values.keys() <= model["inputs"].keys(), "Unknown input variables")
    for name, value in values.items():
        value_check(value, model["inputs"][name])
    if values.keys() != model["inputs"].keys():
        return report("INCONCLUSIVE", "Missing inputs", model, missing=sorted(model["inputs"].keys() - values.keys()))
    hits = [rule for rule in model["rules"] if all(matches(p, values, model["inputs"]) for p in rule["when"])]
    if not hits:
        return report("INCONCLUSIVE", "No matching rule; table coverage is not proven", model)
    if model["hitPolicy"] == "UNIQUE" and len(hits) != 1:
        return report("FAIL", "Overlapping UNIQUE matches", model, matchedRules=[r["id"] for r in hits])
    selected = hits[0]
    outputs = {name: calculate(expr, model["outputs"][name], model["inputs"], values) for name, expr in selected["then"].items()}
    return report("PASS", "Bounded decision evaluated; not candidate equivalence", model, matchedRules=[r["id"] for r in hits], selectedRule=selected["id"], outputs=outputs)


def check_trace(model, trace):
    validate_model(model)
    require(model["kind"] == "processTrace", "Expected process trace model")
    fields(trace, ["modelId", "modelVersion", "states"])
    require(trace["modelId"] == model["id"] and trace["modelVersion"] == model["version"], "Trace model/version mismatch")
    states = trace["states"]
    require(isinstance(states, list) and len(states) <= 10000, "Trace must be a list of <=10000 states")
    if not states:
        return report("INCONCLUSIVE", "No trace observations", model)
    require(all(isinstance(state, str) and state in model["states"] for state in states), "Unknown observed state")
    require(states[0] == model["start"], "Trace does not begin at start")
    for a, b in zip(states, states[1:]):
        require([a, b] in model["transitions"], "Invalid transition: " + a + " -> " + b)
    if states[-1] not in model["ends"]:
        return report("INCONCLUSIVE", "Missing terminal end observation", model)
    return report("PASS", "Single-token trace conforms; decision outcomes and runtime provenance are not checked", model)


def reject_constant(value):
    raise Invalid("Non-finite and floating JSON numbers are unsupported; use decimal strings")


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def load(path):
    with Path(path).open(encoding="utf-8") as stream:
        return json.load(stream, object_pairs_hook=object_pairs, parse_float=reject_constant, parse_constant=reject_constant)


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False) + "\n"


def check_baseline(manifest, root):
    fields(manifest, ["profileVersion", "id", "version", "scope", "accountableOwner", "approvalClaim", "artifacts"])
    require(type(manifest["profileVersion"]) is int and manifest["profileVersion"] == 1, "Unsupported baseline profile")
    identifier(manifest["id"])
    identifier(manifest["version"])
    text(manifest["scope"])
    text(manifest["accountableOwner"])
    fields(manifest["approvalClaim"], ["approved", "record"])
    require(type(manifest["approvalClaim"]["approved"]) is bool, "approved claim must be boolean")
    text(manifest["approvalClaim"]["record"])
    artifacts = items(manifest["artifacts"])
    by_id, by_path, models = {}, set(), []
    for artifact in artifacts:
        fields(artifact, ["id", "role", "path", "sha256"])
        identifier(artifact["id"])
        require(artifact["role"] in ("source", "adr", "decisionTable", "processTrace", "cases"), "Unknown artifact role")
        require(isinstance(artifact["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]), "Expected lowercase SHA256")
        path = safe_path(root, artifact["path"])
        require(artifact["id"] not in by_id and path not in by_path, "Duplicate artifact ID/path")
        by_id[artifact["id"]] = artifact
        by_path.add(path)
        if not path.is_file():
            return report("INCONCLUSIVE", "Missing baseline artifact", artifactId=artifact["id"])
        require(hashlib.sha256(path.read_bytes()).hexdigest() == artifact["sha256"], "Baseline hash mismatch: " + artifact["id"])
        if artifact["role"] in ("decisionTable", "processTrace"):
            model = validate_model(load(path))
            require(model["id"] == artifact["id"] and model["kind"] == artifact["role"], "Artifact model identity/role mismatch")
            require(model["baselineId"] == manifest["id"], "Wrong model baseline link")
            models.append(model)
    require(bool(models), "Baseline requires at least one model")
    for model in models:
        for key, role in (("sources", "source"), ("adrs", "adr")):
            for link in model[key]:
                artifact = by_id.get(link["id"])
                require(artifact is not None and artifact["role"] == role and safe_path(root, artifact["path"]) == safe_path(root, link["path"]), "Unbound source/ADR link: " + link["id"])
    return report("PASS", "Bytes and model links match; source truth and authority are not verified", baselineId=manifest["id"], baselineVersion=manifest["version"], authorityStatus="INCONCLUSIVE", approvalClaimVerified=False, artifactCount=len(artifacts))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "evaluate", "check-trace", "export", "check-baseline"))
    parser.add_argument("file", help="Model JSON or baseline manifest")
    parser.add_argument("--input", help="Decision inputs or trace JSON")
    parser.add_argument("--root", default=".", help="Baseline artifact root (default: current directory)")
    parser.add_argument("--output", help="New report/export file; never overwritten")
    args = parser.parse_args(argv)
    try:
        require((args.command in ("evaluate", "check-trace")) == bool(args.input), "--input is required only for evaluate/check-trace")
        model = load(args.file)
        if args.command == "check-baseline":
            result = check_baseline(model, args.root)
        elif args.command == "evaluate":
            result = evaluate(model, load(args.input))
        elif args.command == "check-trace":
            result = check_trace(model, load(args.input))
        else:
            validate_model(model)
            result = model if args.command == "export" else report("PASS", "Profile structure valid; coverage/overlap and authority not proven", model)
        if args.output:
            with Path(args.output).open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(canonical(result))
        else:
            print(canonical(result), end="")
        return {"PASS": 0, "FAIL": 1, "INCONCLUSIVE": 2}.get(result.get("status"), 0)
    except (Invalid, ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
        print(canonical(report("FAIL", str(exc))), end="")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
