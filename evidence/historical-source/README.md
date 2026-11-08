# Historical source byte contracts

These files preserve exact Git blob bytes from the commit named by each directory.
They are audit inputs, not runnable current implementations or new observations.
Existing evidence records and their expected SHA-256 values remain unchanged.

| Original commit | Preserved source | SHA-256 |
|---|---|---|
| `b175041e411db5033aa25596d8c1f99f6f535680` | `lab/e1_pg/test_oracle_vectors.py` | `a6e258c4e0535c735837ef56ce96669953d76b77864a435fa475cbd43a610459` |
| `338ef0292c67812cadfb3e9ab7436dad590dbcf8` | `lab/e1_pg/test_oracle_vectors.py` | `a6e258c4e0535c735837ef56ce96669953d76b77864a435fa475cbd43a610459` |
| `c547c3f34badda0cb57ab0b496917dadb1485b04` | `lab/e2_orleans/test_multiprocess.py` | `07cab6fdf4b213210a13b4ba1bacafab42732749cd71ae399c58724aa891a525` |
| `c547c3f34badda0cb57ab0b496917dadb1485b04` | `lab/e2_orleans/setup_adonet_membership.py` | `8c63468d04e4e41886826347287ef8b14cf1a5c9d6ec99dc92feef460fb42af8` |

The E1 oracle-vector and runtime-manifest records precede dynamic host reporting.
The E2 placement negative controls precede source-archive provenance and the
labelled disposable-container checks used by newer reproduction workflows.
Reverting current implementations would remove those changes; treating their new
bytes as the old observations would misrepresent the evidence.

`check_e1_observations.py` and `check_e2_placement_observation.py` select these
historical files explicitly for the affected paths. Every other source comparison
retains its current policy. `historical_source.py` requires the original digest;
a missing or changed snapshot fails with no current-worktree fallback. The root
`.gitattributes` preserves all `evidence/**` bytes without newline conversion.
No Git history fetch is needed for these snapshots in a shallow checkout.

Run from the repository root:

```bash
python3 scripts/test_historical_source.py
python3 -O scripts/test_historical_source.py
python3 scripts/check_e1_observations.py
python3 scripts/check_e2_placement_observation.py
```

Passing validates the recorded historical byte contracts and observation checks.
It does not qualify newer implementations or rerun PostgreSQL, Orleans, or Azure.
