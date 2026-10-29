# E3 · Banking branch WAN measurement protocol (no field results yet)

**This repository does not contain measured WAN timings from real bank branches.** The [chapter 25 bis comparison](../book/en/part-5-capacity/25a-mainframe-on-prem-azure-and-banking-network-infrastructure.md) uses explanatory arithmetic, not measured bank traffic. [Español](NETWORK_PROTOCOL.es.md).

## Minimum record per scenario

- Site class (urban, regional, international), time zone, fibre/ISP routing where known, SD-WAN/MPLS/VPN path and failover circuit.
- Pseudonymised technical site IDs only: do not commit customer names, private IP addresses or credentials.
- Azure region, zone, gateway, FastPath setting, NVA/firewall, subnet and VM/transactional-database limits.
- Business operation, request/response size, channel (TN3270, HTTP/2, gRPC), TLS session reuse, authentication, idempotency and commit outcome.
- **Keyboard to screen** correlated trace with p50/p95/p99, packet loss, jitter, timeouts and fallback.
- Representative online+batch mix, hot-key distribution, errors, queue age, independent accounting oracle, N-1 failover and recovery.

## Acceptance

1. Run on-premises, Azure and hybrid candidates with the **same workload, representative data and durability policy**.
2. Exercise peak traffic, batch overlap and controlled link loss, tracking recovery and ambiguous operations.
3. Separate network RTT, internal CICS time and perceived end-to-end response; never add component percentiles as if they were overall p99.
4. Publish a reproducible report with tool versions, source SHA, actual results, inconclusives and conditions; obtain workload-owner approval.
5. **Do not promote E3 to verified** without measured deployments and business-invariant checks.

## Teaching model, NOT a benchmark

```bash
python3 lab/network/test_wan_model.py
python3 lab/network/wan_model.py
```

The file `illustrative_scenarios.json` has the explicit `ILLUSTRATIVE_ASSUMPTIONS` classification. None of its RTT inputs come from measured banking networks. The modeled delta illustrates the cost of sequential calls; it is neither an SLA nor a p99. Field experiment E3 remains outstanding.
