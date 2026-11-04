# Vendor runtime contracts — bounded source-backed assessment

Research scope: #17 (IBM Z/OS/hardware/Db2), #18 (vendor-specific contracts), #28 (cross-layer patterns). English-only machine data and checks; research and book prose in **paired ES/EN**. The original vendor machines and customer workload **have not been accessed or executed**.

## Current increment

- [`catalog.json`](catalog.json) has **11 entries** across IBM Z/z/OS, Db2 for z/OS, IBM i, ClearPath MCP, ClearPath OS 2200, historical Fujitsu GS21, and **explicitly unknown** NEC ACOS/GCOS. The ten citations record source product/version scope, access date, publication date if known, and `SEARCH_INDEX_DIRECT_403` versus actual `FULL_TEXT`. The archived Fujitsu announcement dated 2018 is labeled `HISTORICAL_VENDOR_ANNOUNCEMENT`; it is not a source for current product support or semantic equivalence.
- [`scripts/check_vendor_runtime_contracts.py`](../../scripts/check_vendor_runtime_contracts.py) rejects unsourced vendor-feature mappings, inflated parity or execution claims, unknown → unsupported transitions, missing semantic gaps, negative scenarios or independent oracles. It performs **25 metadata controls**, *not* native vendor tests, benchmarks or an assessment of an actual customer.
- [Research EN](../../docs/research/vendor-runtime-contracts.en.md) · [Research ES](../../docs/research/vendor-runtime-contracts.es.md) · [Chapter 1 EN](../../book/en/part-1-before-translating/01-the-mainframe-is-not-a-fast-box.md) · [Chapter 13 EN](../../book/en/part-4-patterns/13-before-choosing-a-pattern-identify-the-contract.md). Chapters 1 and 13 have full paired Spanish content.

## Run

```bash
python3 scripts/check_vendor_runtime_contracts.py
python3 scripts/check_vendor_runtime_contracts.py --self-test
```

Expected catalog status: `VALID_METADATA_ONLY` with `nativePlatformTested=false`, `bankApproved=false`, `todmG2=INCONCLUSIVE` and `todmG6=BLOCK`. A passing test says only the **authored metadata** meets our conservative schema. It cannot authenticate manuals, installed OS/DB components, clocks, Db2 locking parity, Fujitsu GS21 support, financial throughput or bank signoff.

## Next evidence

Have the source owner/operations team provide a permitted, versioned inventory: platform model, partitions, OS/DB/monitor versions, terminals/channels, log and recoverability, batch and privileged writers, contention and WLM/RMF or equivalent measurements, application service objectives and source-side disaster-recovery exercise. Reconcile an independently approved behavior/Golden Master with original traces and negative scenarios. Do **not** upload regulated bank records, credentials or proprietary manuals into this public repository.

**Tracking:** #17/#18/#28 remain open for their wider scope. #58 remains open for source-owned bank fencing and signoff. #53 frozen. E2 partially verified. No release/version approval from this increment.
