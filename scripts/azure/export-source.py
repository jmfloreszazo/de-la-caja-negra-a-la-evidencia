#!/usr/bin/env python3
"""Export an explicit local lab snapshot without committing or contacting GitHub."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "lab/tools"))
from reproduce_campaign import SCOPES, overlay_worktree, source_paths


def export(output):
    if output.exists():
        raise ValueError("Source archive already exists; choose a fresh run directory")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", *SCOPES], cwd=ROOT).strip())
    with tempfile.TemporaryDirectory(prefix="book-source-export-") as directory:
        checkout = Path(directory) / "source"
        subprocess.run(["git", "-c", "core.autocrlf=false", "clone", "--quiet", "--no-checkout",
                        "--no-hardlinks", str(ROOT), str(checkout)], check=True)
        subprocess.run(["git", "-c", "core.autocrlf=false", "checkout", "--quiet", "--detach", commit],
                       cwd=checkout, check=True)
        overlay_worktree(ROOT, checkout, source_paths(ROOT))
        hashes = {}
        with tarfile.open(output, "x") as archive:
            for relative in source_paths(checkout):
                path = checkout / relative
                if path.is_file():
                    if path.is_symlink():
                        raise ValueError(f"Source symlink is not supported: {relative}")
                    hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
                    archive.add(path, arcname=relative, recursive=False)
    report = {"sourceCommit": commit, "worktreeDirty": dirty, "sourceSha256": hashes,
              "archiveSha256": hashlib.sha256(output.read_bytes()).hexdigest(),
              "classification": "EXPLICIT_LOCAL_SOURCE_SNAPSHOT_NOT_A_COMMITTED_RELEASE"}
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sourceCommit": commit, "worktreeDirty": dirty,
                      "archiveSha256": report["archiveSha256"], "files": len(hashes)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    export(parser.parse_args().output.resolve())
