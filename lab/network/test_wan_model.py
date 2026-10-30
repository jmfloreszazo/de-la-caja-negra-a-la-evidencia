#!/usr/bin/env python3
"""Test model arithmetic and verify no hypothetical RTT is mislabeled 'measured'."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from wan_model import projection, scenarios

data=scenarios(Path(__file__).with_name("illustrative_scenarios.json"))
assert data["classification"]=="MODELED_ONLY_NOT_OBSERVED"
assert len(data["cases"])==3
assert all(x["classification"]=="MODELED_ONLY_NOT_OBSERVED" for x in data["cases"])
remote=data["cases"][1]
assert remote["chatty"]["wan_wait_ms_assumption"]==175
assert remote["single_operation"]["wan_wait_ms_assumption"]==35
assert remote["difference_ms_assumption"]==140
assert remote["chatty"]["critical_path_ms_assumption"]==193
assert projection(35,4,0)["wan_wait_ms_assumption"]==140
for vals in [(-1,1,0),(1,-1,0),(1,1,-1)]:
    try:projection(*vals)
    except ValueError:pass
    else:raise AssertionError("negative input incorrectly accepted")
print("WAN MODEL: PASS (illustrative assumptions only; no real measurements)")
