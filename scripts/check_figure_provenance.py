#!/usr/bin/env python3
"""Guard the functional-first Mermaid/PNG provenance for the four book figures.

This checks source/hash/theme agreement and the PNG container header. It cannot
prove pixel identity or security approval; the official Mermaid render job
separately verifies that every source renders.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import struct
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIGURES = ("agent_chain", "c4_containers")
LANGUAGES = ("es", "en")
VERSION = b"1"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def expected_fingerprint(source: bytes, accent: list[str], theme: bytes, css: bytes) -> str:
    source_hash = hashlib.sha256(source + json.dumps(accent).encode()).hexdigest()
    theme_hash = hashlib.sha256(theme + css + VERSION).hexdigest()
    return source_hash + theme_hash


def problems(root: pathlib.Path) -> list[str]:
    folder = root / "book/figures"
    try:
        records = json.loads((folder / "hashes.json").read_text(encoding="utf-8"))
        accents = json.loads((folder / "accents.json").read_text(encoding="utf-8"))
        theme = (folder / "theme.json").read_bytes()
        css = (folder / "theme.css").read_bytes()
    except (OSError, ValueError) as exc:
        return [f"Figure provenance metadata unavailable: {exc}"]
    errors = []
    for name in FIGURES:
        for lang in LANGUAGES:
            key = f"{lang}/{name}"
            source = folder / "src" / lang / f"{name}.mmd"
            image = folder / lang / f"{name}.png"
            if not source.is_file() or not image.is_file():
                errors.append(f"{key}: missing paired source or PNG")
                continue
            if not isinstance(accents.get(name), list):
                errors.append(f"{key}: missing accent metadata")
                continue
            expected = expected_fingerprint(source.read_bytes(), accents[name], theme, css)
            if records.get(key) != expected:
                errors.append(f"{key}: source/theme fingerprint mismatch; rerender with scripts/render_figures.py")
            raw = image.read_bytes()
            if len(raw) < 33 or raw[:8] != PNG_MAGIC or raw[12:16] != b"IHDR":
                errors.append(f"{key}: not a PNG image")
                continue
            width, height = struct.unpack(">II", raw[16:24])
            if not (width >= 100 and height >= 100):
                errors.append(f"{key}: implausible image dimensions ({width}x{height})")
    return errors


def self_test() -> None:
    assert expected_fingerprint(b"abc", [], b"theme", b"css") != expected_fingerprint(b"abcd", [], b"theme", b"css")
    with tempfile.TemporaryDirectory() as temp:
        root = pathlib.Path(temp)
        folder = root / "book/figures"
        (folder / "src/es").mkdir(parents=True)
        (folder / "src/en").mkdir(parents=True)
        (folder / "es").mkdir(parents=True)
        (folder / "en").mkdir(parents=True)
        (folder / "theme.json").write_bytes(b"theme")
        (folder / "theme.css").write_bytes(b"css")
        (folder / "accents.json").write_text(json.dumps({n: [] for n in FIGURES}))
        records = {}
        png = PNG_MAGIC + b"\x00\x00\x00\x0dIHDR" + struct.pack(">II", 100, 100) + b"\x08\x06\x00\x00\x00" + b"\x00\x00\x00\x00" + b"\x00\x00\x00\x00"
        for name in FIGURES:
            for lang in LANGUAGES:
                data = f"{lang}/{name}".encode()
                (folder / "src" / lang / f"{name}.mmd").write_bytes(data)
                (folder / lang / f"{name}.png").write_bytes(png)
                records[f"{lang}/{name}"] = expected_fingerprint(data, [], b"theme", b"css")
        (folder / "hashes.json").write_text(json.dumps(records))
        assert not problems(root)
        (folder / "src/es/agent_chain.mmd").write_bytes(b"changed")
        assert any("fingerprint mismatch" in e for e in problems(root))
        (folder / "src/es/agent_chain.mmd").write_bytes(b"es/agent_chain")
        (folder / "es/agent_chain.png").write_bytes(b"fake")
        assert any("not a PNG" in e for e in problems(root))
    print("FIGURE PROVENANCE SELF-TEST: PASS")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    issues = problems(ROOT)
    for issue in issues:
        print("FAIL", issue)
    print(f"FIGURE PROVENANCE: {'FAIL' if issues else 'PASS'} ({2 * len(FIGURES)} targeted diagrams)")
    raise SystemExit(bool(issues))
