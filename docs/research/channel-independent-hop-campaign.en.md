# H01/H02 independently hosted hop campaign — evidence intake

**Status: implementation of a fail-closed intake checker, NOT execution of the campaign.** Tracks #30. Existing single-host localhost real TCP and PostgreSQL evidence is not reclassified.

## Execution design

Place a synthetic client, gateway, .NET 10 core, disposable PostgreSQL and read-only oracle on independently administered hosts or clearly identified failure domains. Record topology, process/container IDs, images/digests, TLS boundaries, time synchronization, source commit and actual injection commands. A machine/container separation is not proof of separate physical failure domains. Use Podman, not Docker. No real customer data or ATM dispensing.

H01 breaks client→gateway delivery both before request forwarding and after the owner committed but before the response is observed. H02 breaks gateway→core delivery using directional loss/reset and delayed responses. Both must demonstrate same-operation-ID recovery without additional financial effects, and must distinguish a missing response from a proven rejection. Read-only SQL accounting is mandatory, with independently observed decision, paired postings and outbox. Do not infer external cash effects.

## Raw evidence protocol

Write an external campaign manifest with `schemaVersion=1`, exact 64-hex `sourceSha`, `syntheticDisposable=true`, `productionApproved=false`, `todmG2=INCONCLUSIVE`, `todmG6=BLOCK`, named `hosts` (client/gateway/core/database/oracle with `hostId` and `failureDomain`), and two `cases` (H01, H02). Each case records `outcome` (PASS/FAIL/INCONCLUSIVE **for the named synthetic invariant only**), `operationId`, `injectionWindow`, `independentSqlOracle=true`, `unknownAutoAction=false`, `duplicateFinancialEffects=false`. Each case's `artifacts` contains a relative path and SHA-256 for `fault_log`, `client_log`, `gateway_log`, `core_log`, `sql_snapshot`, and `oracle_log`. Preserve original failing evidence rather than editing a historical run.

From the repository root, after collecting authentic originals on the independent hosts:

```bash
python3 scripts/check_channel_hop_campaign.py /path/to/bundle/manifest.json
python3 -m unittest discover -s scripts -p test_channel_hop_campaign.py -v
```

The tool checks declared structure, source identity format, bundle confinement and actual file digests; malformed/incomplete bundles return `INCONCLUSIVE` (exit 2). A complete bundle returns `READY_FOR_MANUAL_EVIDENCE_REVIEW` (exit 0), **never PASS**. An operator must authenticate host provenance, examine packet captures and injection timestamps, rerun SQL independently and validate authority. Even a fully forged bundle could pass structural intake. No production approval, physical HA claim, mainframe parity, real incumbent fencing or release authorization follows; G2 remains INCONCLUSIVE and G6 remains BLOCK. External campaigns and bilingual book integration remain open.
