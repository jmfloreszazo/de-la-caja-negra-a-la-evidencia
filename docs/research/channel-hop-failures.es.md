# Aislar los fallos de conectividad por salto de canal bancario

**5 de noviembre de 2026 · #30 · trazas sintéticas, no ejecución de red real.** [English](channel-hop-failures.en.md) · [Contrato del laboratorio de canales](../../lab/channels/CONTRACT.md) · [Ensayo previo de advice tardío](channel-late-advice.es.md).

## Por qué «timeout de red» no basta para decidir si se ha contabilizado

El cajero físico, el ATM/EFT switch, el procesador/emisor y el core pueden estar en sistemas y organizaciones diferentes. Un mensaje perdido **antes** del switch, otro perdido **entre** switch y core y una respuesta perdida **después** del COMMIT del emisor requieren procedimientos distintos. Que venza un timeout no demuestra ni COMMIT ni ROLLBACK de una unidad de trabajo CICS (UOW). IBM explica que SYNCPOINT confirma los cambios de **recursos recuperables de esa unidad de trabajo** y que una tarea puede tener más de una UOW: no deshace un billete ya entregado ni por sí solo un efecto externo. [IBM CICS syncpoints](https://www.ibm.com/docs/en/cics-ts/6.x?topic=work-synchronization-points) · [Recuperación UOW](https://www.ibm.com/docs/en/cics-ts/6.x?topic=processing-unit-work-recovery).

La [guía de fallos transitorios de Microsoft](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults) propone timeouts y reintentos acotados con backoff. Sin embargo, cuando el resultado del COMMIT financiero es ambiguo, **cambiar el identificador de operación en un reintento puede duplicar el dinero**. Hay que conservar la identidad original y consultar al propietario autoritativo antes de alterar estado, según las reglas reales del banco. El backoff no aporta *exactly once* de extremo a extremo.

La [guía Visa de disputas ATM, junio de 2024](https://usa.visa.com/dam/VCOM/global/support-legal/documents/merchants-dispute-management-guidelines.pdf) distingue la documentación original de dispensación del justificante de abono o reverso. La confirmación del switch no sustituye el journal de billetes ni los asientos posteriores.

## Siete escenarios lógicos preregistrados

| Caso | Frontera que falla o se retrasa | Resultado del fixture | Inferencia prohibida |
| --- | --- | --- | --- |
| H01 | ATM→switch: se pierde la solicitud | `NO_CORE_AUTHORIZATION_EVIDENCE` | Ni rechazo demostrado ni efectivo entregado |
| H02 | Switch→core: solicitud original descartada | `NO_CORE_AUTHORIZATION_EVIDENCE` | No se concede autorización offline |
| H03 | Core hace COMMIT y se pierde respuesta al switch; recuperación del enlace | `AUTHORIZATION_RECOVERED_BY_STATUS` | Autorizar no significa dispensar |
| H04 | Core autoriza, se envía comando al dispositivo y cae enlace ATM↔switch | `CASH_UNKNOWN_NO_REDISPENSE` | Advice tardío no demuestra entrega física |
| H05 | Cambio del propietario de escrituras; llega respuesta de época anterior | `QUARANTINED_OLD_OWNER_REPLY` | El mensaje antiguo no concede permiso para escribir dos veces |
| H06 | Journal sintético acredita 6.000 de 10.000, ledger ficticio coincide | `PARTIAL_CASH_RECONCILED_SYNTHETICALLY` | Coincidencia inventada no es evidencia física autenticada |
| H07 | Switch pierde core y pide stand-in sin delegación | `STAND_IN_DENIED` | El canal no inventa autoridad de emisión |

El [fixture en inglés](../../lab/channels/network_fault_fixture.json) contiene eventos ordenados en dos saltos lógicos diferentes, `ATM_SWITCH` y `SWITCH_CORE`, y etiquetas adicionales `DEVICE`, `ISSUER` y `CONTROL`. Cada evento tiene un paso y época del origen. El [oráculo estricto](../../lab/channels/network_fault_gate.py) contrasta estas observaciones con la decisión declarada del emisor, journal/dispositivo, asiento y propietario activo de escritura. Rechaza una entrega durante partición, COMMIT sin solicitud recibida, status sin COMMIT original, doble orden de dispensación, asiento antes del journal definitivo, respuestas de época incorrecta y falsas aprobaciones de stand-in.

**Cambiar de ruta no demuestra fencing del host antiguo.** El fixture pone en cuarentena una respuesta de época anterior; la migración real todavía necesita un [fence propiedad del origen](../BROWNFIELD_SOURCE_FENCE.es.md) y cubrir todas las escrituras online, batch, offline y privilegiadas. El oráculo no confirma mensajes del banco, no ejecuta una orden financiera y no autentica la consulta al emisor.

## Evidencia que falta para llegar a una migración bancaria real

Las **40/40 pruebas Python han superado CI** y cubren las siete trazas ([acta original ES](../../evidence/runs/CHANNEL-HOP-FAULTS.es.md) · [EN](../../evidence/runs/CHANNEL-HOP-FAULTS.md) · [Actions #42028436325](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42028436325)). `PASS_SYNTHETIC_HOP_CONSISTENCY` solo significa **consistencia interna de una traza ficticia y sus snapshots**. Un conjunto inventado pero coherente también podría pasar. **No se corta ninguna conexión TCP real**, no se aísla una red física ni se usa un ATM/switch/emisor real. Tampoco se autentican logs originales ni journal del dispositivo. El laboratorio .NET 10 + dos PostgreSQL en Podman del capítulo es otro experimento independiente, no una prueba de este evaluador.

Para validarlo con un cliente: recoger topología, contrato de identidad y presupuestos de latencia separados para **ATM↔switch**, **switch↔issuer/core** y **core↔writer/almacén**. Inyectar pérdidas, retardos, duplicaciones y desorden reales sobre extremos desechables y aislados; recoger con autorización logs de COMMIT/UOW y journals nativos, pruebas de entrega/retracción física, mensajes de switch, asientos y disputas. Demostrar identidad duradera, propietario único de escritura, fencing y recuperación ante respuestas tardías tras el cutover. La homologación de red y los controles PCI/HSM siguen fuera del alcance del fixture.

**Contrato en todos los resultados:** `physicalLinkCutTested=false`, `automaticAuthorizationAllowed=false`, `automaticDispenseAllowed=false`, `automaticPostingAllowed=false`, `automaticReversalAllowed=false`, `cohortWriterCutoverAuthorized=false`, `productionApproved=false`; TODM **G2 INCONCLUSIVE / G6 BLOCK**. E2 continúa `partially_verified`; #30 abierto, #53 congelado y sin release nueva.
