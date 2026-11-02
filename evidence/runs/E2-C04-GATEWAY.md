# E2-F10-C04 · External-client gateway isolation

**Original synthetic evidence; 2 November 2026. E2 remains partially verified.**

[Run #41513498050](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41513498050),
job `125511013376`, passed on source/checkout
`434170ac03f63925b517992d744aae531eb38965`.

- [Original ZIP](e2-c04-gateway-original.zip): artifact `13173832507`,
  7403 bytes, SHA-256
  `ea12b2363746504e2cf3fb3095ae361156a7844435938ec3aa2951e7a840a702`.
- [Unmodified original JSON](e2-c04-gateway-original.json).
- Recomputed digest, source/checkout and five explicit source hashes verified;
  all 58 full provenance source hashes were also checked.

## Observations and meaning

| Step | Observed result | Limit |
| --- | --- | --- |
| Only primary gateway unreachable from client | COMMITTED through secondary gateway to a primary-hosted grain; source account 2, destination 1 | Fresh client, not established-session reconnect |
| Both client gateways blocked | SQL and both silo paths healthy; membership 3/3, version 4 | One machine, four namespaces, two private networks |
| Client under complete cut | Exit 74; CLIENT_STARTUP_DEADLINE before financial dispatch; observed 20.8509 s | Startup unavailability, not ACK loss after COMMIT |
| SQL during cut | No new operation, posting or outbox; three additional SQL samples agree | No rollback inferred from timeout |
| Restoration | OUTPUT rules exactly match baseline; replay COMMITTED then DUPLICATE_COMMITTED | Same stable operation ID |
| Final state | 3 operations, 6 postings, 3 outbox; each operation 1/2/1; oracle 7/7 | No sustained capacity or physical HA |

## Preserved first failure

[Initial run #41512514429](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41512514429)
on `934d6e226c300850a88c070eb633af3fe31bc562` failed to classify an outer
70-second timeout: the application phase was unknown. Preserve its
[original failed ZIP](e2-c04-first-failure-original.zip), artifact `13173492258`,
6711 bytes, SHA-256
`b549005b14e72bd10a1a6a795f366756a3a85ea34b9b3fe1162bbeb3501019f7`,
and [original JSON](e2-c04-first-failure-original.json).
The corrected C04 mode requires an internal startup deadline and structured
pre-financial-dispatch exit; unrelated failures still fail. The first failure
is neither converted to PASS nor attributed to accounting.

## Remaining gates

No asymmetric partition, in-flight COMMIT/ACK fault, explanation of the
historical C01 anomaly, physical failure domains, PostgreSQL HA, sustained
capacity, RTO/RPO or MIPS equivalence is established. E2 #8/#24/#25 remain open;
G2/G6 receive no bank approval. Later source SHAs need separate CI. #53 remains
frozen and no release changes.

[Español](E2-C04-GATEWAY.es.md) · [Protocol](../../lab/e2_orleans/F10_C04_PROTOCOL.md)
