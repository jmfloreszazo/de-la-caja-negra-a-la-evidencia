# C01 · Colocación controlada, rechazo unilateral y recuperación

**Evidencia sintética original, 2 de noviembre de 2026. E2 sigue parcialmente verificado.**

La [ejecución #41523019075](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41523019075)
superó las tres cohortes sobre source/checkout
`47ed0a087717ec6c02f64a173a63ee597a919f75`. Los jobs originales fueron
`125543545505`, `125543544991` y `125543546197`.

## Originales y auditoría

| Cohorte | Runner ID asignado | Artefacto original | Bytes | SHA-256 del ZIP |
| --- | --- | --- | --- | --- |
| 1 | 1000006956 | 13179390478 | 21020 | 7b426f22055aa3567b5055f0ba9edf20c975282848d335a5a84f8fc8f1790898 |
| 2 | 1000006953 | 13177724656 | 21623 | 451da1a89d243bed2b8d4829ac93c4c4a0feb1b327201658e234098c4a50ccb5 |
| 3 | 1000006961 | 13177439210 | 21299 | da90c8a0be90c534ddd4f5c7eea9474b1cc22f1e243ef5f78be9ea0e193a3dcc |

Se conservan los ZIP sin modificar: [1](e2-c01-controlled-1-original.zip),
[2](e2-c01-controlled-2-original.zip), [3](e2-c01-controlled-3-original.zip),
y los JSON extraídos: [1](e2-c01-controlled-1-original.json),
[2](e2-c01-controlled-2-original.json), [3](e2-c01-controlled-3-original.json).
Se recomputaron los tres digests y los 61 hashes completos de procedencia de
cada cohorte. La [captura de la API de jobs](e2-c01-controlled-jobs-api.json)
es metadato de asignación, **no un artefacto del experimento**. Los runner IDs
son distintos, pero los tres hostname son `runnervm48cm3`: no se infiere
independencia física. Se observaron 24 IDs distintos de contenedores iniciales
para los seis fixtures nuevos, más los tres secundarios recreados.

## Resultado de las tres cohortes

| Control | Resultado en las tres cohortes |
| --- | --- |
| 16 cuentas activadas solo en secundario; ambos miembros Active | Rechazo correcto del criterio dual; 0 operaciones/0 apuntes/0 outbox; oráculo 7/7 |
| Nuevo cliente con hints alternos sobre las mismas activaciones | Las 16 siguen en secundario; el criterio dual sigue rechazado |
| Fixture nuevo con activación alterna de cuentas 1..16 | 8 en primario y 8 en secundario, comprobadas con un cliente normal sin hints |
| Dos transferencias desde sus hosts originales | COMMITTED en secundario y primario; 2/4/2 efectos SQL |
| SIGKILL del secundario tras respuesta | Salida 137; reactivación en primario; membresía secundaria Active 3 a Dead 6 |
| Replay de ID estable y transferencia nueva | DUPLICATE_COMMITTED y COMMITTED; estado 3 operaciones/6 apuntes/3 outbox; oráculo 7/7 |
| Reincorporación del secundario | Contenedor, PID y generación nuevos; generación anterior Dead retenida; ledger sin cambios |

## El fallo histórico no se reescribe

El [ZIP original fallido](e2-c01-original-one-sided.zip), artefacto
`13046077362`, 2520 bytes, SHA-256
`91e19d4c5e2d84874b0f4c79ce0afde57dae43b9dc1d21a4861bfadfcc5ae097`,
y su [JSON sin modificar](e2-c01-original-one-sided.json) pertenecen al run
`41210325811`, source `ba4aa1d783e8698bfc7e047fec389f8ef0e82f13`.
El campo error conserva las 16 cuentas en secundario. El campo stage quedó
obsoleto en `adonet-membership-setup`: aquel código no actualizaba la fase
antes de probe_hosts. No demuestra un fallo de arranque SQL ni un defecto
contable. No se cambia ese metadato original.

## Interpretación y límites

Se acredita la **alternativa de fixture controlado** prevista en #44. Las
indicaciones de colocación de Orleans 10.4.0 solo siembran nuevas activaciones
compatibles; no cambian AccountGrain, su no reentrancia, el ledger aceptado o
la política predeterminada observada ResourceOptimizedPlacement. Los clientes
financieros posteriores no usan hints.

**La causa de la concentración original sigue sin demostrarse.** La prueba
de colocación predeterminada y su rechazo permanecen intactos. Tres jobs con
fixtures nuevos no prueban HA entre dominios físicos, particiones asimétricas,
fallos en vuelo durante COMMIT/ACK, RTO/RPO, capacidad sostenida ni equivalencia
mainframe. G2=INCONCLUSIVE y G6=BLOCK. #53 congelada; sin cambio de release.

[English](E2-C01-CONTROLLED.md) · [Protocolo y fuentes oficiales fijadas](../../lab/e2_orleans/C01_CONTROLLED_PROTOCOL.md)
