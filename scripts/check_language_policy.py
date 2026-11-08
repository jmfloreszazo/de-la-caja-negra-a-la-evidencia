#!/usr/bin/env python3
"""Check bilingual-book / English-only software-project language boundaries.

This is a deterministic structure and accidental-localization guard, not a
general natural-language classifier. A bilingual editorial review is still
required for complete prose quality and embedded code samples.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAB = ROOT / "lab"

# High-confidence, non-technical Spanish phrases that should never appear
# in engineering README files. We deliberately do not ban accented proper
# names, localized test fixtures, or the Spanish title of the book.
SPANISH_PROSE = re.compile(
    r"\b(?:"
    r"Español|"
    r"Ejecución local|"
    r"Se ejecutan|"
    r"Siguientes experimentos|"
    r"Siguientes puertas|"
    r"En CI se ejecutan|"
    r"El oráculo de pruebas|"
    r"Los JSON contienen|"
    r"Los resultados|"
    r"El mismo servicio|"
    r"Este laboratorio permite|"
    r"Próxima puerta"
    r")\b",
    re.IGNORECASE,
)

FENCE = re.compile(r'^```([^\n]*)\n(.*?)^```[ \t]*$', re.M | re.S)

def code_pair_errors(english: str, spanish: str) -> list[str]:
    """Keep executable/config examples canonical; translated diagrams are prose."""
    en, es = list(FENCE.finditer(english)), list(FENCE.finditer(spanish))
    if len(en) != len(es):
        return ['different fenced-block counts']
    issues = []
    for index,(left,right) in enumerate(zip(en,es),1):
        if left[1] != right[1]:
            issues.append(f'block {index}: different languages')
        elif left[1] not in ('text','markdown') and left[2] != right[2]:
            issues.append(f'block {index}: executable/config code differs between editions')
    return issues

def errors(root: pathlib.Path) -> list[str]:
    problems = []
    lab = root / "lab"
    if not lab.is_dir():
        return ["lab/ is missing"]

    # Only policy-check what the repository tracks or would track: ignored caches
    # (lab/results, node_modules, virtualenvs) carry third-party READMEs in any language.
    docs = sorted(p for p in lab.rglob("*.md")
                  if "node_modules" not in p.parts and not p.is_relative_to(lab / "results"))
    for path in docs:
        rel = path.relative_to(root)
        if path.name.endswith(".es.md") or path.name.endswith(".español.md"):
            problems.append(f"{rel}: translated lab documentation is forbidden; keep one English README")
            continue

        text = path.read_text(encoding="utf-8")
        m = SPANISH_PROSE.search(text)
        if m:
            problems.append(f"{rel}: unexpected Spanish engineering prose: {m.group(0)!r}")
        if re.search(r"\]\(README\.es\.md\)", text, re.IGNORECASE):
            problems.append(f"{rel}: link to a translated lab README")

    # The M1 and M2 projects are the current policy canaries. New labs must
    # follow the same pattern, even though we cannot know every future name.
    for project in ("transport", "durable_rpc"):
        required = lab / project / "README.md"
        if not required.is_file():
            problems.append(f"lab/{project}/README.md: missing canonical English project README")

    for p in (root / "book" / "es", root / "book" / "en"):
        if not p.is_dir():
            problems.append(f"{p.relative_to(root)}: missing book edition")
    if not (root / "AGENTS.md").is_file():
        problems.append("AGENTS.md: required contribution rules missing")
    if not (root / "docs/LANGUAGE_POLICY.md").is_file():
        problems.append("docs/LANGUAGE_POLICY.md: language policy missing")
    for english in sorted((root/'book/en').rglob('*.md')):
        if english.name in ('README.md','diagrams.md'):
            continue
        text = english.read_text(encoding='utf-8')
        link = re.search(r'\]\(([^)]+\.md)\)',text.splitlines()[0]) if text else None
        if not link:
            continue  # The structural checker reports missing counterparts.
        spanish = (english.parent/link[1]).resolve()
        if spanish.is_file():
            for issue in code_pair_errors(text,spanish.read_text(encoding='utf-8')):
                problems.append(f'{english.relative_to(root)}: {issue}')
    return problems

def self_test() -> None:
    # Check that the accidental Spanish content detector is genuinely active.
    assert SPANISH_PROSE.search("Ejecución local")
    assert SPANISH_PROSE.search("Se ejecutan 20 casos")
    assert not SPANISH_PROSE.search("A .NET 10 ledger and José María Flores Zazo")
    assert code_pair_errors('```csharp\n// English\n```','```csharp\n// traducido\n```')
    assert code_pair_errors('```json\n{}\n```','```yaml\n{}\n```')
    assert not code_pair_errors('```text\nBranch\n```','```text\nSucursal\n```')
    assert not code_pair_errors('```python\nx=1\n```','```python\nx=1\n```')
    print("LANGUAGE POLICY SELF-TEST: PASS")

if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    issues = errors(ROOT)
    if issues:
        for problem in issues:
            print("FAIL", problem)
        print(f"LANGUAGE POLICY: FAIL ({len(issues)} issue(s))")
        raise SystemExit(1)
    print("LANGUAGE POLICY: PASS (English software docs; paired Spanish/English book folders)")
