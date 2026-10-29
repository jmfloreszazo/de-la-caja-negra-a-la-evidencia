#!/usr/bin/env python3
"""Illustrative branch-WAN latency model. NOT a network measurement or a bank SLA.

The tool refuses to label modeled values as measured. Feed real traces to E3 only
after instrumenting each bank's actual representative locations.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EXAMPLE=ROOT/"lab/network/illustrative_scenarios.json"


def projection(rtt_ms:float, sequential_extra_roundtrips:int, local_work_ms:float):
    if rtt_ms < 0 or sequential_extra_roundtrips < 0 or local_work_ms < 0:
        raise ValueError("RTT, extra round trips and local work must be non-negative")
    return {
      "classification":"MODELED_ONLY_NOT_OBSERVED",
      "wan_rtt_ms_assumption":rtt_ms,
      "serial_extra_roundtrips":sequential_extra_roundtrips,
      "wan_wait_ms_assumption":round(rtt_ms*sequential_extra_roundtrips,3),
      "local_work_ms_assumption":local_work_ms,
      "critical_path_ms_assumption":round(rtt_ms*sequential_extra_roundtrips+local_work_ms,3),
      "disclaimer":"Deterministic arithmetic only; not p95/p99 and not measured branch performance."
    }


def scenarios(path:Path):
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("classification")!="ILLUSTRATIVE_ASSUMPTIONS":
        raise ValueError("Example input must have ILLUSTRATIVE_ASSUMPTIONS classification")
    rows=[]
    for case in data["cases"]:
        baseline=projection(case["assumed_wan_rtt_ms"],case["extra_serial_roundtrips"],case["assumed_local_work_ms"])
        coarse=projection(case["assumed_wan_rtt_ms"],case["optimized_roundtrips"],case["assumed_local_work_ms"])
        rows.append({
           "name":case["name"],"classification":"MODELED_ONLY_NOT_OBSERVED",
           "chatty":baseline,"single_operation":coarse,
           "difference_ms_assumption":round(baseline["critical_path_ms_assumption"]-coarse["critical_path_ms_assumption"],3)
        })
    return {"classification":"MODELED_ONLY_NOT_OBSERVED","cases":rows}


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--scenarios",type=Path,default=EXAMPLE)
    args=parser.parse_args()
    print(json.dumps(scenarios(args.scenarios),indent=2))
