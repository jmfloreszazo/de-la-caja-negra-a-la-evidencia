"""Conservative source reconnaissance for a restricted COBOL/CICS/SQL/JCL subset.

This is NOT a general COBOL/JCL parser. A source reference is an inferred
static dependency, never proof of a runtime or business boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

SUFFIXES = {".cbl": "cobol", ".cob": "cobol", ".cpy": "copybook", ".jcl": "jcl"}
TOKEN = r"[A-Z0-9_@$#-]+"
REF = re.compile(r"\s*(?:(['\"])([^'\"\r\n]+)\1|(" + TOKEN + r"))", re.I)
PROGRAM_ID = re.compile(r"\bPROGRAM-ID\s*\.\s*(" + TOKEN + r")", re.I)
KEYWORDS = re.compile(r"\b(CALL|COPY|EXEC\s+(?:SQL|CICS))\b", re.I)
SQL_READ = re.compile(r"\b(?:FROM|JOIN)\s+(" + TOKEN + r"(?:\." + TOKEN + r")?)\b", re.I)
SQL_WRITE = re.compile(r"\b(?:UPDATE|INSERT\s+INTO|DELETE\s+FROM)\s+(" + TOKEN + r"(?:\." + TOKEN + r")?)\b", re.I)
CICS = re.compile(r"\b(?:LINK|XCTL)\s+PROGRAM\s*\(\s*(?:(['\"])([^'\"]+)\1|(" + TOKEN + r"))\s*\)", re.I)
JCL_EXEC = re.compile(r"\bEXEC\s+(?:PGM|PROC)\s*=\s*([^,\s]+)", re.I)
JCL_DD = re.compile(r"\bDD\s+.*?\bDSN\s*=\s*([^,\s]+)", re.I)
JCL_INCLUDE = re.compile(r"\bINCLUDE\s+MEMBER\s*=\s*([^,\s]+)", re.I)


def _mask_quoted(line: str) -> str:
    """Mask literals and inline comments while preserving token positions."""
    output = []
    i = 0
    while i < len(line):
        c = line[i]
        if line[i:i + 2] == "*>":
            output.extend(" " * (len(line) - i))
            break
        if c in "'\"":
            quote = c
            start = i
            i += 1
            while i < len(line):
                if line[i] == quote:
                    if i + 1 < len(line) and line[i + 1] == quote:
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            output.extend(" " * (i - start))
        else:
            output.append(c)
            i += 1
    return "".join(output)


def _cobol_lines(content: str):
    for idx, line in enumerate(content.splitlines(), 1):
        fixed = (len(line) >= 7 and
                 all(c.isdigit() or c == " " for c in line[:6]) and
                 line[6] in " */-D")
        if fixed:
            if line[6] in "*/D":
                continue
            logical = line[7:72]
        else:
            logical = line
        masked = _mask_quoted(logical)
        if masked.strip():
            yield idx, logical, masked


def _parse_ref(text: str):
    m = REF.match(text)
    if not m:
        return None, "unrecognized"
    raw = (m.group(2) or m.group(3)).strip()
    if not raw or raw.startswith((":", "&")):
        return None, "unresolved"
    if m.group(3) and not re.fullmatch(TOKEN, raw, flags=re.I):
        return None, "unrecognized"
    return raw.upper(), "literal" if m.group(2) else "identifier"


def discover(root: Path) -> dict:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Input root must be a directory")
    paths = sorted(p for p in root.rglob("*") if p.suffix.lower() in SUFFIXES)
    nodes = {}
    edges = []
    alerts = []
    sources = []

    def node(kind, name):
        ident = f"{kind}:{name.upper()}"
        nodes.setdefault(ident, {"id": ident, "kind": kind})
        return ident

    def edge(origin, target, kind, path, lineno, digest):
        edges.append({"source": origin, "target": target, "relation": kind,
                      "evidence": "static", "confidence": "inferred",
                      "observedAt": f"static:{path}:{lineno}:{digest}",
                      "atomicGroup": None, "file": path, "line": lineno})

    def alert(origin, kind, path, lineno, value):
        alerts.append({"node": origin, "classification": "needs_human_review",
                       "reason": kind, "file": path, "line": lineno,
                       "token": value})

    for file in paths:
        if file.is_symlink() or not file.resolve().is_relative_to(root):
            raise ValueError("Symlinks and files outside root are forbidden")
        rel = file.relative_to(root).as_posix()
        raw = file.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        sources.append({"path": rel, "sha256": digest, "bytes": len(raw)})
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"{rel} must be explicitly transcoded to UTF-8") from exc
        kind = SUFFIXES[file.suffix.lower()]
        owner = node("job" if kind == "jcl" else
                     "copybook" if kind == "copybook" else
                     "program", file.stem)
        if kind == "jcl":
            for lineno, text in enumerate(content.splitlines(), 1):
                if not text.startswith("//") or text.startswith("//*"):
                    continue
                record = text[2:].strip()
                for regex, destination, relationship in (
                    (JCL_EXEC, "program", "executes"),
                    (JCL_DD, "dataset", "uses_dataset"),
                    (JCL_INCLUDE, "procedure", "includes_procedure"),
                ):
                    match = regex.search(record)
                    if not match:
                        continue
                    token = match.group(1).strip("'\"")
                    if not token or any(mark in token for mark in ("&", "*", "?")):
                        alert(owner, "unresolved_jcl_substitution", rel, lineno, token)
                    else:
                        edge(owner, node(destination, token), relationship, rel, lineno, digest)
            continue
        for lineno, logical, masked in _cobol_lines(content):
            identity = PROGRAM_ID.search(masked)
            if identity:
                canonical = node("program", identity.group(1))
                if canonical != owner:
                    edge(owner, canonical, "declares_program", rel, lineno, digest)
                owner = canonical
            for keyword in KEYWORDS.finditer(masked):
                key = re.sub(r"\s+", " ", keyword.group().upper())
                if key in ("CALL", "COPY"):
                    target, classification = _parse_ref(logical[keyword.end():])
                    if not target or (key == "CALL" and classification == "identifier"):
                        alert(owner, "unresolved_dynamic_call" if key == "CALL"
                              else "unresolved_copy", rel, lineno,
                              target or logical[keyword.end():].strip()[:40])
                    else:
                        edge(owner, node("program" if key == "CALL" else "copybook", target),
                             "calls" if key == "CALL" else "includes", rel, lineno, digest)
                elif key in ("EXEC SQL", "EXEC CICS"):
                    match = re.search(r"\bEND-EXEC\b", masked[keyword.end():], re.I)
                    if not match:
                        alert(owner, "unparsed_multiline_sql" if key == "EXEC SQL"
                              else "unparsed_multiline_cics", rel, lineno, key)
                        continue
                    statement = logical[keyword.end():keyword.end() + match.start()]
                    if key == "EXEC SQL":
                        for m in SQL_READ.finditer(statement):
                            edge(owner, node("table", m.group(1)),
                                 "reads_table", rel, lineno, digest)
                        for m in SQL_WRITE.finditer(statement):
                            edge(owner, node("table", m.group(1)),
                                 "writes_table", rel, lineno, digest)
                    else:
                        for m in CICS.finditer(statement):
                            target = m.group(2) or m.group(3)
                            if m.group(3):
                                alert(owner, "unresolved_cics_program", rel, lineno, target)
                            else:
                                edge(owner, node("program", target),
                                     "cics_transfers_control", rel, lineno, digest)
    return {"schemaVersion": 1, "status": "STATIC_RECONNAISSANCE_NOT_COMPLETE",
            "sources": sources,
            "nodes": sorted(nodes.values(), key=lambda n: n["id"]),
            "edges": sorted(edges, key=lambda e: (e["file"], e["line"], e["relation"], e["target"])),
            "alerts": sorted(alerts, key=lambda a: (a["file"], a["line"], a["reason"]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="Synthetic UTF-8 source directory, read only")
    args = parser.parse_args()
    try:
        result = discover(args.root)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "INVALID", "reason": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["alerts"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
