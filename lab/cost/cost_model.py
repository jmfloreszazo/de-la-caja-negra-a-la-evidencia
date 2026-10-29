#!/usr/bin/env python3
"""Transparent component-cost comparison. Never present a partial sum as TCO."""
from __future__ import annotations
import argparse
import json
from decimal import Decimal
from pathlib import Path

HERE=Path(__file__).resolve().parent
CATALOG=HERE/"dated_prices.json"

def scenarios(data):
    vm={v["sku"]:v for v in data["cloud"]["items"]}
    def vm_case(name,sku,min_nodes,max_nodes,platform):
        monthly=Decimal(str(vm[sku]["reported_monthly_eur"]))
        return {
            "scenario":name,"platform":platform,
            "currency":"EUR","region":data["cloud"]["region"],
            "baseline_replicas":min_nodes,"maximum_replicas":max_nodes,
            "minimum_compute_eur_per_730h":str(monthly*min_nodes),
            "peak_full_month_compute_eur_if_all_max_replicas":str(monthly*max_nodes),
            "variable_scaling_cost":"NOT COMPUTABLE without observed time per replica",
            "other_costs":"NOT PRICED: database, storage, egress, networking, HA, monitoring, operations and platform charges",
            "estimated_tco":None,"price_source_date":data["cloud"]["source_published"],
            "price_checked_on":data["cloud"]["source_checked_on"],
            "quote_status":"ILLUSTRATIVE_COMPUTE_SUBTOTAL_ONLY",
        }
    cases=[
      vm_case("VM Scale Sets, 3-to-6 Linux workers","Standard_D4as_v5",3,6,"VMSS"),
      vm_case("AKS, 3-to-6 equivalent Linux nodes","Standard_D4as_v5",3,6,"AKS"),
      vm_case("Alternative Intel VMSS, 3-to-6 Linux workers","Standard_D4s_v5",3,6,"VMSS"),
      {"scenario":"Azure Container Apps Consumption","platform":"ACA","currency":"EUR",
       "estimated_tco":None,"minimum_compute_eur_per_730h":None,
       "quote_status":"NEEDS_ACTIVE_IDLE_CPU_MEMORY_SECONDS_AND_REQUESTS",
       "other_costs":"Consumption, dedicated management where applicable, networking, data and observability"},
      {"scenario":"Azure App Service Premium v3","platform":"AppService","currency":"EUR",
       "estimated_tco":None,"minimum_compute_eur_per_730h":None,
       "quote_status":"NEEDS_REGION_PLAN_SKU_AND_REPLICA_QUOTE",
       "other_costs":"Instance plan, networking, database, HA and monitoring"},
      {"scenario":"On-premises 2 nodes x 2 AMD EPYC 9965 sockets","platform":"onprem",
       "currency":"USD","physical_cpus":4,
       "cpu_only_1ku_usd":str(Decimal(str(data["onprem"]["unit_cpu_usd"]))*4),
       "estimated_tco":None,
       "quote_status":"CPU_1KU_REFERENCE_ONLY_NOT_A_SERVER_RFQ",
       "other_costs":"Chassis, RAM, networking, NVMe, redundancy, energy, facility, licences, support, staff and DR"},
    ]
    return {
      "classification":"PRICING_REFERENCE_NO_TCO_OR_BENCHMARK",
      "checked_on":data["captured_on"],
      "cloud_date":data["cloud"]["source_published"],
      "units":"730h reference month; rounded published EUR amounts",
      "cases":cases,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",type=Path,default=CATALOG)
    args=p.parse_args()
    catalog=json.loads(args.catalog.read_text(encoding="utf-8"))
    print(json.dumps(scenarios(catalog),indent=2,ensure_ascii=False))

if __name__=="__main__":main()
