#!/usr/bin/env python3
"""Deterministic regression guard for the functional-first book method.

This verifies a limited editorial contract, not full semantic or translation
quality. Structural ES/EN parity and generated-file consistency are checked
separately by scripts/check.py.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

PAIRS = {
    "archaeology": (
        "book/es/parte-2-arqueologia-y-autoridad/06-rea-y-la-arqueologia-que-deja-rastro.md",
        "book/en/part-2-archaeology-and-authority/06-rea-and-archaeology-that-leaves-a-trail.md",
    ),
    "agents": (
        "book/es/parte-2-arqueologia-y-autoridad/07-legacy-archaeology-asistida-por-agentes.md",
        "book/en/part-2-archaeology-and-authority/07-legacy-archaeology-assisted-by-agents.md",
    ),
    "gate": (
        "book/es/parte-6-laboratorio/29-incorporar-agentes-sin-permitir-que-escriban-el-aprobado.md",
        "book/en/part-6-lab/29-bringing-in-agents-without-letting-them-write-the-approval.md",
    ),
    "decomposition": (
        "book/es/parte-2-arqueologia-y-autoridad/07a-descomponer-el-mainframe-con-evidencia.md",
        "book/en/part-2-archaeology-and-authority/07a-decomposing-a-mainframe-with-evidence.md",
    ),
}

REQUIRED = {
    ("archaeology", "es"): ("mapa de capacidades", "parser", "aprobada"),
    ("archaeology", "en"): ("business capability", "parser", "approved"),
    ("agents", "es"): ("descubrimiento funcional", "investigación técnica opcional", "baseline"),
    ("agents", "en"): ("functional discovery", "optional technical investigation", "baseline"),
    ("gate", "es"): ("programar desde cero", "TODM", "Golden Master"),
    ("gate", "en"): ("implement the capability from scratch", "TODM", "Golden Master"),
    ("decomposition", "es"): ("Event Storming", "Event Sourcing", "CANDIDATE_ONLY"),
    ("decomposition", "en"): ("Event Storming", "Event Sourcing", "CANDIDATE_ONLY"),
}

# These formulations would regress to the old parser-first migration contract.
FORBIDDEN = {
    ("agents", "es"): ("propongo una cadena de agentes especializados", "parser y grafo de dependencias"),
    ("agents", "en"): ("parser and dependency graph", "the cobol analyser generates an ast"),
    ("gate", "es"): ("evaluaría primero el parser", "traducirlas a c#"),
    ("gate", "en"): ("first evaluate the parser", "translate them into c#"),
}

def problems(root: pathlib.Path) -> list[str]:
    issues = []
    for group, pair in PAIRS.items():
        for lang, relative in zip(("es", "en"), pair):
            path = root / relative
            if not path.is_file():
                issues.append(f"{relative}: missing paired manuscript chapter")
                continue
            content = path.read_text(encoding="utf-8").casefold()
            for phrase in REQUIRED[(group, lang)]:
                if phrase.casefold() not in content:
                    issues.append(f"{relative}: missing required functional-first concept {phrase!r}")
            for phrase in FORBIDDEN.get((group, lang), ()):
                if phrase.casefold() in content:
                    issues.append(f"{relative}: forbidden parser-first prescription {phrase!r}")
    if (root / "lab/decomposition/static_scan.py").exists():
        issues.append("lab/decomposition/static_scan.py: abandoned parser accidentally restored")
    return issues

def self_test() -> None:
    import tempfile
    from unittest.mock import patch

    # Test the simple detection rules using deliberately contradictory prose.
    assert "parser and dependency graph" in FORBIDDEN[("agents", "en")]
    assert "evaluaría primero el parser" in FORBIDDEN[("gate", "es")]
    with tempfile.TemporaryDirectory() as temp:
        base = pathlib.Path(temp)
        for (group, lang), phrases in REQUIRED.items():
            relative = PAIRS[group][0 if lang == "es" else 1]
            file = base / relative
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(" ".join(phrases), encoding="utf-8")
        assert not problems(base)
        bad = base / PAIRS["agents"][1]
        bad.write_text(bad.read_text(encoding="utf-8") + " parser and dependency graph", encoding="utf-8")
        assert any("parser-first" in issue for issue in problems(base))
    print("FUNCTIONAL-FIRST GUARD SELF-TEST: PASS")

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    errors = problems(ROOT)
    for error in errors:
        print("FAIL", error)
    print(f"FUNCTIONAL-FIRST GUARD: {'FAIL' if errors else 'PASS'} ({len(PAIRS)} paired chapters)")
    raise SystemExit(bool(errors))
