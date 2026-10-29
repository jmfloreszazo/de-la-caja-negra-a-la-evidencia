#!/usr/bin/env python3
"""Fetch current public Azure Retail Prices API as a dated CI artifact.

This does NOT overwrite the editorial price snapshot or create a release.
Non-USD API rates are indicative reference amounts per Microsoft.
"""
import datetime as dt
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen,Request

API="https://prices.azure.com/api/retail/prices"
SKU=["Standard_D4as_v5","Standard_D4s_v5","Standard_D8as_v5"]
REGION="westeurope"
CURRENCY="EUR"

def fetch(sku):
    expression=("armRegionName eq '"+REGION+"' and armSkuName eq '"+sku+
                "' and priceType eq 'Consumption'")
    # Microsoft documents currencyCode as a quoted OData-style string.
    query=urlencode({"currencyCode":"'"+CURRENCY+"'","$filter":expression})
    url=API+"?"+query
    items=[]
    for i in range(8):
        with urlopen(Request(url,headers={"User-Agent":"COBOL-Modernization-Pricing-Audit/1.0"}),timeout=30) as r:
            result=json.load(r)
        items.extend(result.get("Items",[]))
        url=result.get("NextPageLink")
        if not url:break
        if not url.startswith("https://prices.azure.com/"):
            raise ValueError("Unexpected API pagination host")
    filtered=[x for x in items if x.get("armSkuName")==sku and x.get("armRegionName")==REGION
              and x.get("priceType")=="Consumption" and x.get("currencyCode")==CURRENCY
              and x.get("unitOfMeasure")=="1 Hour"
              and not any(v in (x.get("meterName","")+" "+x.get("skuName","")+" "+x.get("productName","")).lower()
                          for v in ("windows","spot","low priority"))]
    # Multiple primary meters may exist; record all candidates rather than picking a cheap
    # rate that might not be the intended Linux price or a different product.
    if not filtered:
        diagnostic=[{k:v.get(k) for k in ("armSkuName","armRegionName","currencyCode","priceType","unitOfMeasure","meterName","productName")} for v in items[:6]]
        raise ValueError("No candidate Linux/Consumption hourly meter for "+sku+"; total="+str(len(items))+"; candidates="+json.dumps(diagnostic))
    return sorted([{
      "armSkuName":x["armSkuName"],"meterId":x["meterId"],"meterName":x["meterName"],
      "productName":x["productName"],"skuName":x["skuName"],
      "retailPrice":x["retailPrice"],"unitPrice":x["unitPrice"],
      "unitOfMeasure":x["unitOfMeasure"],"effectiveStartDate":x["effectiveStartDate"],
      "priceType":x["priceType"],"isPrimaryMeterRegion":x.get("isPrimaryMeterRegion")
    } for x in filtered],key=lambda v:(str(v["productName"]),str(v["skuName"])))

def main():
    record={
      "classification":"DIRECT_AZURE_PUBLIC_RETAIL_API_RETRIEVAL_NOT_A_QUOTE",
      "retrieved_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
      "endpoint":API,"region":REGION,"currency":CURRENCY,"currency_warning":"Microsoft prices services in USD; EUR is indicative, not a contract.",
      "meters":{sku:fetch(sku) for sku in SKU}
    }
    folder=Path(os.environ.get("PRICE_OUTPUT_DIR","lab/results/pricing"))
    folder.mkdir(parents=True,exist_ok=True)
    path=folder/"azure-retail-api-observation.json"
    path.write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(record,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
