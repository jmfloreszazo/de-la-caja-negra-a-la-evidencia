#!/usr/bin/env python3
"""Rasterise editable SVG brand assets. Requires cairosvg; no hard-coded browser paths."""
from pathlib import Path
import argparse, io, sys
try:
    import cairosvg
except ImportError:
    sys.exit("Install renderer with: python3 -m pip install cairosvg")
root = Path(__file__).resolve().parents[1]
names = [
    "symbol-primary", "icon-b-dark", "cover-es", "cover-en",
    "social-preview", "logo-es-light", "logo-es-dark",
    "logo-en-light", "logo-en-dark"
]
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
parser.add_argument("--only", nargs="+", choices=names + ["mark"], help="Render or check only the named assets")
args = parser.parse_args()
selected = args.only or names + ["mark"]
for name in selected:
    source = root / (name + ".svg")
    target = root / ("mark-512.png" if name == "mark" else name + ".png")
    data = cairosvg.svg2png(url=str(source))
    if args.check:
        if not target.exists() or target.read_bytes() != data:
            sys.exit("STALE BRAND PNG: " + target.name + " (run assets/src/render.py)")
    else:
        target.write_bytes(data)
        print("png", target.name)
if args.check:
    print(f"BRAND PNG: PASS ({len(selected)} assets)")
