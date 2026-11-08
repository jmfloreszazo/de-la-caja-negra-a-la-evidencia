# Evidence verification scripts

Tracked, dependency-free Python that re-derives the records under `evidence/runs/` from the
raw campaign folders. The raw folders (`lab/results/**`) and the delivery archives (`evidence/archives/preserved-dist/*.zip`)
are ignored by Git; these scripts are what makes the derivation reproducible by someone who
holds a copy of an archive.

| Script | Input | Output / check |
|---|---|---|
| `dist_manifest.py` | `evidence/archives/preserved-dist/*.zip` and their receipt JSON | Writes or verifies `docs/DIST_MANIFEST.md` (name, bytes, entries, SHA-256, receipt match) |
| `verify_azure_e1_e4.py` | `lab/results/azure-e1-e4-20261108/` (from `azure-e1-e4-todm-2026-11-08.zip`) | Re-checks source/raw archive hashes, Azure instance metadata, E1/E2/E3/E4 assertions; compares against `evidence/runs/azure-e1-e4-2026-11-08.json` |
| `summarize_todm_azure.py` | same campaign folder | Re-derives `evidence/runs/todm-azure-2026-11-08.json` and compares parsed JSON values |

```bash
python3 scripts/evidence/dist_manifest.py --verify
python3 scripts/evidence/verify_azure_e1_e4.py --campaign <extracted-archive>/campaign
python3 scripts/evidence/summarize_todm_azure.py --campaign <extracted-archive>/campaign
```

The campaign scripts are read-only by default. A missing summary fails verification;
`--write-summary` explicitly creates it after the checks pass, but never replaces an existing
record. Summary comparison is **semantic JSON equality**, not byte equality: whitespace and
object-key order may differ. Archive/member SHA-256 checks and the hashes recorded in summaries
bind the particular bytes they cover; they do not establish an independent trusted signature.
All verification checks remain active with `python -O`.

`dist_manifest.py --verify` returns 0 only when the manifest matches and every archive receipt
contains a matching digest. A receipt mismatch returns 1 even if the manifest was regenerated
with that mismatch. A missing receipt or missing receipt digest returns 2 (**INCOMPLETE**), not
success. Legacy receipt metadata is retained as-is; do not invent missing packaging digests.
Manifest generation keeps reporting these states without certifying them. Entry counts come
from receipt metadata, not a fresh ZIP inventory.

TODM's `verifiedSnapshotFiles` (134), `artifactBindings` (108), and
`recoveredOriginalRuntimeFiles` (16) are historical constants copied into the summary, not
independently recounted by this verifier. The pinned method commit is also a declared constant,
not independently authenticated here. Qualification counts are checked against raw JSON; the
verifier does not rerun qualification or the underlying experiments. E1–E4's original model-call
count and membership-provider count likewise describe the fixed campaign, not new measurements.

None of these scripts changes `evidence/claims.json`. Its separate checker binds each
`demonstrated_not_accepted` claim to its record's SHA-256 and requires `github_actions` for
`ci_verified` and `github_release` for `published`.

These scripts do **not** rerun experiments, contact Azure, or decide acceptance. Successful
verification means the implemented checks and compared summary values match the supplied
campaign, within the limits above.
