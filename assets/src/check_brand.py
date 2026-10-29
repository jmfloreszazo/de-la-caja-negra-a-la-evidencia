#!/usr/bin/env python3
"""Lightweight, dependency-free check for the approved V5 artwork and references."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets"
problems = []


def require(condition, message):
    if not condition:
        problems.append(message)


def read(path):
    if not path.is_file():
        problems.append(f"Missing: {path.relative_to(ROOT)}")
        return ""
    return path.read_text(encoding="utf-8")


def svg(name, w, h):
    p = ASSETS / name
    markup = read(p)
    if not markup:
        return
    try:
        el = ET.fromstring(markup)
        require(el.tag == "{http://www.w3.org/2000/svg}svg", f"Invalid SVG root: {name}")
        require(el.get("viewBox") == f"0 0 {w} {h}", f"Incorrect viewBox: {name}")
    except ET.ParseError as exc:
        problems.append(f"Invalid SVG XML: {name}: {exc}")


for name, width, height in [
    ("cover-es.svg", 1600, 2400),
    ("cover-en.svg", 1600, 2400),
    ("social-preview.svg", 1280, 640),
    ("mark.svg", 512, 512),
    ("icon-b-dark.svg", 512, 512),
    ("symbol-primary.svg", 1000, 620),
]:
    svg(name, width, height)

for lang, title, word in [
    ("es", "# De la caja negra a la evidencia", "Icono variante B"),
    ("en", "# From Black Box to Evidence", "Variant B"),
]:
    root_readme = read(ROOT / ("README.es.md" if lang == "es" else "README.md"))
    require(root_readme.startswith(title + "\n"), f"Incorrect {lang} README heading")
    header = root_readme[:650]
    require("<picture>" in header and "</picture>" in header, f"Missing responsive {lang} brand icon")
    require('srcset="assets/icon-b-dark.svg"' in header, f"Missing {lang} dark icon")
    require('src="assets/mark.svg"' in header, f"Missing {lang} light icon")
    require(word in header, f"Missing {lang} icon accessibility label")
    require(header.index("<picture>") < header.find("\n**", len(title)) if "\n**" in header else False,
            f"Icon must appear directly under the {lang} title, before introduction")
    book_index = read(ROOT / "book" / lang / "README.md")
    require(f"../../assets/cover-{lang}.svg" in book_index, f"Book {lang} must embed matching SVG cover")
    logo = read(ASSETS / f"logo-{lang}-light.svg")
    require("#D9232E" in logo, f"Missing approved red accent in {lang} lockup")

for name in ["mark-512.png", "cover-es.png", "cover-en.png", "social-preview.png"]:
    require((ASSETS / name).is_file(), f"Missing PNG: {name}")

require(read(ASSETS / "symbol-primary.svg") != read(ASSETS / "mark.svg"),
        "Primary symbol and B icon must remain distinct assets")

if problems:
    for problem in problems:
        print("BRAND FAIL:", problem)
    sys.exit(1)
print("BRAND REFERENCE CHECK: PASS")
