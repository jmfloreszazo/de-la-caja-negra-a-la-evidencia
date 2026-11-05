# Fallos lógicos por salto ATM–switch–core — acta sintética de 40 controles

[English](CHANNEL-HOP-FAULTS.md) · [Investigación ES](../../docs/research/channel-hop-failures.es.md) · [PR #99](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/99).

**Resultado original del 5 de noviembre de 2026: 40/40 pruebas Python PASS sobre siete trazas de saltos ficticios. Sin cortes físicos de red ni autorización bancaria.**

## Procedencia exacta de la ejecución

- [Actions #42028436325](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42028436325), job `127248415098`, SHA original de código y checkout `8bec46074a50daa5d08ecc174662e837cad8ab8c`.
- El log original registra **40 controles nombrados superados**, `Ran 40 tests`, cero errores inesperados y estado `PASS_40_SYNTHETIC_HOP_CONTROLS`. El [extracto literal con timestamps](CHANNEL-HOP-PR99-ORIGINAL-CI-EXCERPT.log) no es el ZIP íntegro de GitHub.
- GitHub informa artifact `13415051431`, `channel-hop-faults-synthetic-original-not-physical`, tamaño **2.637 bytes**, SHA-256 `3ac341c70ccf4a17db27a8218f299768ff64f7c782cedb5cebec62ed66ad2101`, caducidad inicial 3 de febrero de 2027. **No se ha descargado ni recalculado de forma independiente el ZIP**. La suma es un dato de GitHub, no una verificación independiente. [Registro JSON](channel-hop-pr99-original-ci-summary.json).
- Una primera ejecución de Book falló **MD012** por dos líneas en blanco duplicadas en los roadmaps. Se corrigieron posteriormente; no se reetiqueta el fallo histórico como PASS.

## Siete trazas y sus límites

| Caso | Situación ficticia | Dictamen |
| --- | --- | --- |
| H01 | Solicitud perdida en ATM→switch antes de su recepción | `NO_CORE_AUTHORIZATION_EVIDENCE` |
| H02 | Solicitud descartada en switch→core antes de su recepción | `NO_CORE_AUTHORIZATION_EVIDENCE` |
| H03 | COMMIT del emisor, respuesta perdida, enlace recuperado y consulta de estado original | `AUTHORIZATION_RECOVERED_BY_STATUS` |
| H04 | Comando a dispensador enviado, cae ATM↔switch; estado físico UNKNOWN y advice tardío | `CASH_UNKNOWN_NO_REDISPENSE` |
| H05 | Cambia la época del escritor; llega respuesta del anterior | `QUARANTINED_OLD_OWNER_REPLY` |
| H06 | Efectivo parcial sintético (6.000 de 10.000) y asiento de igual importe | `PARTIAL_CASH_RECONCILED_SYNTHETICALLY` |
| H07 | Switch no alcanza al core e intenta stand-in sin delegación | `STAND_IN_DENIED` |

Los negativos rechazan entrega con enlace DOWN, COMMIT o consulta sin solicitud original, órdenes duplicadas de dispensación, asientos repetidos, cambio arbitrario de UNKNOWN, respuestas de escritor antiguo, supuesta prueba de cutover y autoaprobaciones de banco o dispositivo.

**Jamás concede permiso financiero:** `physicalLinkCutTested=false`, `nativeIssuerLogAuthenticated=false`, `physicalCashJournalAuthenticated=false`, `delegatedStandInAuthority=false`, `automaticAuthorizationAllowed=false`, `automaticDispenseAllowed=false`, `automaticPostingAllowed=false`, `automaticReversalAllowed=false`, `cohortWriterCutoverAuthorized=false`, `productionApproved=false`, TODM **G2 INCONCLUSIVE / G6 BLOCK**.

Es **un oráculo de traza lógica**, no una partición TCP, failover medido, journal físico, protocolo de tarjetas homologado, fencing del origen, COMMIT auténtico CICS/Db2/IMS o aceptación bancaria. Un historial completamente inventado pero coherente puede superar la prueba. El laboratorio nativo .NET 10/dos PostgreSQL y el oráculo anterior de 33 advices mantienen evidencias y alcances **independientes**. #30 sigue abierto para pruebas reales de enlaces y L01–L16, #53 congelado, E2 `partially_verified`. Sin nueva release.
