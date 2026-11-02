# E2-F10-C04 · Aislamiento de gateways del cliente externo

**Evidencia original sintética; 2 de noviembre de 2026. E2 sigue parcialmente verificado.**

La [ejecución #41513498050](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41513498050),
job `125511013376`, pasó sobre source/checkout
`434170ac03f63925b517992d744aae531eb38965`.

- [ZIP original](e2-c04-gateway-original.zip): artefacto `13173832507`,
  7403 bytes, SHA-256
  `ea12b2363746504e2cf3fb3095ae361156a7844435938ec3aa2951e7a840a702`.
- [JSON original sin modificar](e2-c04-gateway-original.json).
- Digest recomputado, source/checkout y cinco hashes explícitos comprobados;
  también los 58 hashes completos del archivo de procedencia.

## Resultados y significado

| Paso | Resultado observado | Límite |
| --- | --- | --- |
| Solo gateway primario inaccesible para el cliente | Transferencia COMMITTED por gateway secundario hacia grain alojado en primario; cuenta origen 2 y destino 1 | Cliente nuevo, no reconexión de una sesión establecida |
| Ambos gateways bloqueados desde el cliente | SQL y ambos silos siguen accesibles entre sí; membresía 3/3, versión 4 | Una máquina, cuatro namespaces y dos redes privadas |
| Cliente bajo corte completo | Código 74; CLIENT_STARTUP_DEADLINE antes de enviar comandos; 20,8509 s observados | Indisponibilidad de arranque, no pérdida de ACK después de COMMIT |
| SQL durante corte | Sin nueva operación, apunte ni outbox; tres observaciones adicionales coinciden | No se infiere rollback de un timeout |
| Restauración | Reglas OUTPUT idénticas a las iniciales; replay COMMITTED y después DUPLICATE_COMMITTED | Mismo identificador estable |
| Estado final | 3 operaciones, 6 apuntes, 3 outbox; cada operación 1/2/1; oráculo 7/7 | No capacidad sostenida ni HA física |

## Primer fallo conservado

La [ejecución inicial #41512514429](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41512514429)
sobre `934d6e226c300850a88c070eb633af3fe31bc562` falló al clasificar el timeout
externo de 70 s: no demostraba la fase de aplicación. Se conserva el
[ZIP original fallido](e2-c04-first-failure-original.zip), artefacto
`13173492258`, 6711 bytes, SHA-256
`b549005b14e72bd10a1a6a795f366756a3a85ea34b9b3fe1162bbeb3501019f7`,
y su [JSON original](e2-c04-first-failure-original.json).
El modo C04 corregido exige un deadline interno de arranque y una salida
estructurada anterior al envío financiero; errores ajenos siguen fallando.
El fallo inicial no se convierte en PASS ni se atribuye a la contabilidad.

## Puertas que siguen abiertas

No prueba particiones asimétricas, fallos durante COMMIT/ACK, resolución de la
anomalía histórica C01, dominios físicos, HA PostgreSQL, capacidad sostenida,
RTO/RPO o equivalencia MIPS. E2 #8/#24/#25 permanecen abiertas; G2 y G6 no
reciben aprobación bancaria. La CI de un SHA posterior debe comprobarse por
separado. #53 sigue congelada y no se cambia ninguna release.

[English](E2-C04-GATEWAY.md) · [Protocolo](../../lab/e2_orleans/F10_C04_PROTOCOL.md)
