#!/usr/bin/env python3
"""Prove that subtotal scenarios do not masquerade as comparable TCO."""
import json
from pathlib import Path
from cost_model import scenarios

d=json.loads(Path(__file__).with_name("dated_prices.json").read_text(encoding="utf-8"))
s=scenarios(d)
assert d["captured_on"]=="2026-10-29"
assert d["cloud"]["source_published"]=="2026-10-06"
assert d["cloud"]["region"]=="westeurope"
assert d["cloud"]["currency"]=="EUR"
assert d["cloud"]["source_type"]=="third_party_reproduction_of_retail_prices__not_direct_api_observation"
assert all(x["estimated_tco"] is None for x in s["cases"])
vmss,aks,intel,aca,app,onprem=s["cases"]
assert vmss["minimum_compute_eur_per_730h"]=="402"
assert vmss["peak_full_month_compute_eur_if_all_max_replicas"]=="804"
assert aks["minimum_compute_eur_per_730h"]=="402"
assert intel["minimum_compute_eur_per_730h"]=="444"
assert aca["minimum_compute_eur_per_730h"] is None
assert app["estimated_tco"] is None
assert onprem["cpu_only_1ku_usd"]=="47952"
assert all(x["price_status"].startswith("RFQ") for x in d["private_mainframes"])
print("DATED COMPONENT COST MODEL: PASS (no fabricated complete TCO)")
