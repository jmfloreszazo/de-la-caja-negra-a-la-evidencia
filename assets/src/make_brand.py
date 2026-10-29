#!/usr/bin/env python3
"""Backward-compatible wrapper for the Node.js SVG brand generator."""
from pathlib import Path
import subprocess
import sys
script = Path(__file__).with_name("make_brand.mjs")
raise SystemExit(subprocess.call(["node", str(script), *sys.argv[1:]]))
