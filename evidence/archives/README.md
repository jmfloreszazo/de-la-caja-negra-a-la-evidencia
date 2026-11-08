# Preserved local evidence archives

Historical evidence belongs here, not in the replaceable PDF build directory.
The 8 November relocation copied and verified every file before removing its
original under `dist/`. No ZIP was recompressed, no receipt or raw observation
was edited, and no duplicate historical copy was discarded.

- `preserved-dist/`: local payloads, deliberately ignored by Git, retaining the
  original names and subdirectories. Mixed bundles retain their historical PDFs.
- [Relocation inventory](relocation-2026-11-08.json): old/new relative paths,
  sizes and SHA-256 for all 29 files, including the historical reproduction folder.
- [Archive manifest](../../docs/DIST_MANIFEST.md): ZIP names, digests and receipt status.
- [Verification tools](../../scripts/evidence/README.md): commands for holders of
  the original bundles. A manifest does not provide the bytes or public hosting.

`dist/` now contains only the two current generated PDFs and their layout metadata.
Active raw campaign directories under `lab/results/` were not moved or modified.
In particular, the original E3 execution log remains in its campaign directory.

Historical receipts and reports may still mention `dist/`: those strings record
the packaging-time location. Resolve them through the relocation inventory;
do not edit their bytes merely to update a path. Package scripts preserved inside
historical campaigns are provenance, not the current storage policy.

To check ZIP inventory after receiving the payloads:

```bash
python3 scripts/evidence/dist_manifest.py --verify
```

Keep an independent backup before deleting any local payload. Git contains the
inventory, not the ignored archives. This relocation is not a new experiment,
public release, authenticity signature or approval of the recorded conclusions.
