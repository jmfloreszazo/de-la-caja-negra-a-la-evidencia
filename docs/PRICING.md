# Dated cost comparison · Azure, on-premises and mainframe

**Checked on 29 October 2026.** These are **component-level prices and operating-model scenarios**, not a banking-system TCO or a MIPS-equivalence claim. [Español](PRICING.es.md). The canonical snapshot is [`lab/cost/dated_prices.json`](../lab/cost/dated_prices.json).

## Publicly available figures

| Item | Recorded figure | Data date | Provenance / boundaries |
|---|---:|---|---|
| Azure Linux **D4as_v5**, West Europe, pay-as-you-go | **€134/month**, rounded published figure | Article 6 Oct 2026; checked 29 Oct 2026 | [AzureScan](https://www.azurescan.eu/en/insights/older-vm-generations/); VM compute only |
| Azure Linux **D4s_v5**, West Europe, pay-as-you-go | **€148/month**, rounded published figure | Article 6 Oct 2026; checked 29 Oct 2026 | [AzureScan](https://www.azurescan.eu/en/insights/older-vm-generations/); excludes storage, database, networking, tax and support |
| AMD **EPYC 9965** | **USD 11,988 per CPU at 1,000-unit pricing** | Manufacturer page checked 29 Oct 2026 | [AMD](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9965.html); CPU only, **not a server quote or retail unit price** |
| IBM z17 / LinuxONE; Unisys Dorado | **No comparable public contract quote** | Checked 29 Oct 2026 | Obtain RFQ including hardware, licenses, capacity, maintenance and support |

The [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) is interrogated by [`infrastructure-pricing.yml`](../.github/workflows/infrastructure-pricing.yml), filtering exact SKU, `westeurope` and EUR. The workflow saves the retrieval timestamp, `effectiveStartDate`, meter ID and all plausible meters as a separate review artifact; it does **not automatically overwrite** the editorial snapshot. Microsoft's primary billing currency is USD; EUR rates from the API are indicative.

## Component-only calculation

At 730 hours, **three always-on D4as_v5 workers** cost a reference **€402/month in compute alone**. **Six always-on workers** are **€804/month in compute alone**. VMSS and AKS can share that same VM compute line, but AKS still needs its paid control-plane tier when applicable, plus networking, disks, logging, database, load balancing and availability. A VM is not a pod and 4 vCPU on one large VM is not automatically equivalent to four smaller replicas.

ACA Consumption instead bills allocated active/idle vCPU/GiB seconds and eligible requests; App Service requires an identified plan/region/replica count. The [ACA billing guide](https://learn.microsoft.com/en-us/azure/container-apps/billing) describes monthly free grants; [AKS management tiers](https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers) differentiate Free, Standard and Premium.

Two on-premises 2P EPYC 9965 nodes imply **four CPUs × USD 11,988 = USD 47,952** at 1KU CPU reference pricing. This is **not a purchasable HA server deployment quote**: it excludes servers, RAM, NVMe, network, redundant data centre, power, licensing, operations, DR and support. Do not compare USD upfront hardware-only with monthly EUR cloud compute without a dated FX rate and time-consistent amortisation model.

## Required missing pricing

Count branch ExpressRoute/provider/circuit/gateway/egress, VM quotas and nodes, traffic distribution, database and log IOPS, backup/replica, N-1 failure reserve, observability retention, API/WAF, licensing, security, support and operator time. [Microsoft ExpressRoute cost guidance](https://learn.microsoft.com/en-us/azure/expressroute/plan-manage-cost) documents key circuit, gateway and data-transfer charges.

**The real comparator is cost per successful, durable business operation under the same SLO** with source-of-truth ledger guarantees, branch-to-screen latency, failure/recovery and workload mix—not headline cores or a single VM's hourly rate.

```bash
python3 lab/cost/test_cost_model.py
python3 lab/cost/cost_model.py
python3 lab/cost/fetch_azure_prices.py   # requires Azure Retail API access
```

The model returns `estimated_tco: null` when costs are unknown; it cannot accidentally claim a complete TCO. See the full [Chapter 25 bis](../book/en/part-5-capacity/25a-mainframe-on-prem-azure-and-banking-network-infrastructure.md). **Field E3 remains unexecuted.**
