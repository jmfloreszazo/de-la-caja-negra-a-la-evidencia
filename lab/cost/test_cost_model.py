#!/usr/bin/env python3
"""Prove that subtotal scenarios do not masquerade as comparable TCO."""
import json
from pathlib import Path
from cost_model import scenarios

d=json.loads(Path(__file__).with_name("dated_prices.json").read_text(encoding="utf-8"))
s=scenarios(d)
assert d["captured_on"]=="2026-10-29"
assert d["cloud"]["source_published"]=="2026-10-29"
assert d["cloud"]["region"]=="westeurope"
assert d["cloud"]["currency"]=="EUR"
assert d["cloud"]["source_type"]=="DIRECT_AZURE_PUBLIC_RETAIL_API_SNAPSHOT_NOT_CONTRACT_QUOTE"
api=json.loads(Path(__file__).with_name("official_retail_snapshot.json").read_text(encoding="utf-8"))
assert api["run_id"]==d["cloud"]["source_run_id"]
assert api["retrieved_at_utc"]==d["cloud"]["retrieved_at_utc"]
for item in d["cloud"]["items"]:
    published=next(x for x in api["meters"] if x["sku"]==item["sku"])
    assert item["retail_eur_per_hour"]==published["retail_eur_per_hour"]
    assert item["meter_id"]==published["meter_id"]
assert all(x["estimated_tco"] is None for x in s["cases"])
vmss,aks,intel,aca,app,onprem=s["cases"]
assert vmss["minimum_compute_eur_per_730h"]=="400.77"
assert vmss["peak_full_month_compute_eur_if_all_max_replicas"]=="801.54"
assert aks["minimum_compute_eur_per_730h"]=="400.77"
assert intel["minimum_compute_eur_per_730h"]=="443.26"
assert aca["minimum_compute_eur_per_730h"] is None
assert app["estimated_tco"] is None
assert onprem["cpu_only_1ku_usd"]=="47952"
assert all(x["price_status"].startswith("RFQ") for x in d["private_mainframes"])
print("DATED COMPONENT COST MODEL: PASS (no fabricated complete TCO)")
