# E2 · Cortes largos programados y recuperación asistida muestreada

**Evidencia original acotada verificada, 3 de noviembre de 2026. E2 sigue parcial.**

[Ejecución original #41607407356](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41607407356),
fuente y checkout `ee1e883e5e23d651e3408a90f8ec12fd9f7a2d58`.
Dos jobs nuevos; **un host físico por caso**, sin dominios de fallo independientes.

| Case / caso | Job | Artifact | Bytes | ZIP SHA-256 |
| --- | --- | --- | --- | --- |
| primary outbound | 125820594636 | 13217388632 | 28255 | 999f2612e6a032305e0a7dc58b30e7cecbe8670626ce976f924e06c5141b46d0 |
| secondary outbound | 125820594983 | 13217885893 | 28677 | a0f2ed8039afae94eadf2bb1f255f0887c4fa69553cb16717229233aa201f922 |

ZIP sin modificar y extracciones del resumen idénticas byte a byte:
[ZIP primario](e2-long-primary-original.zip) / [JSON](e2-long-primary-original.json),
[ZIP secundario](e2-long-secondary-original.zip) / [JSON](e2-long-secondary-original.json).
Se recalcularon los digests y los 70 hashes de fuentes de cada job contra el
commit exacto. El auditor interpreta los PCAP originales: hay paquetes TCP
idénticos en ambos extremos en la dirección permitida y ninguna llegada en la
bloqueada durante la captura inicial de 45 segundos. Esa captura no cubre todo
el corte programado.

## Resultados observados

| Observación | Salida del primario bloqueada | Salida del secundario bloqueada |
| --- | --- | --- |
| Corte programado, segundos | 120.000110 | 120.000121 |
| Última muestra con secundario vivo, inicio–fin segundos | 65.844–66.205 | 66.486–66.786 |
| Primera muestra con secundario terminado, inicio–fin segundos | 68.205–68.475 | 68.786–69.081 |
| Contador DROP final en namespace retenido | 125 | 135 |
| Destino al retirar regla | Primario vivo | Secundario terminado |
| Dos intentos pareados sin recreación | Gateway secundario no disponible antes del envío | Gateway secundario no disponible antes del envío |
| Recuperación | Ambos silos recreados expresamente | Ambos silos recreados expresamente |
| Primer ACK pareado tras retirar regla, segundos | 58.484 | 59.211 |
| Criterios de recuperación satisfechos, segundos | 58.484 | 59.211 |
| Muestras de replay estable | 14 parejas | 14 parejas |
| Intervalo real primera–última muestra, segundos | 66.152 | 66.129 |
| Operaciones / apuntes / outbox finales | 3 / 6 / 3 | 3 / 6 / 3 |
| Invariantes SQL en cada muestra de recuperación | 7/7 | 7/7 |

Los intervalos inicio/fin describen lecturas, no el instante exacto de salida del
proceso. Ambos casos observaron la terminación del secundario antes de acabar
los 120 segundos. Los observadores existentes retuvieron los namespaces y las
reglas DROP. Por tanto, **120 segundos describe la programación del fallo, no
120 segundos con ambos silos vivos**. Restaurar el namespace con el destino
terminado no recupera la aplicación. Los registros de diagnóstico conservan
identidad y estado antes/después: ninguno registra un destino terminado que
pase a vivo durante la orden de diagnóstico.

Cada caso comenzó con colocación controlada 8/8, solo de identidad, sobre las
claves 1..16. SQL inicial 0/0/0 y baseline 1/2/1. Las solicitudes contendientes
usaron el mismo ID con importes 31 y 37 por gateways distintos; SQL conservó
solo 37. Todos los ACK se concilian con ese ganador; una respuesta incierta
tras el envío no demuestra rollback. El replay idéntico devolvió
DUPLICATE_COMMITTED; el payload cambiado, ID_CONFLICT; un ID nuevo, COMMITTED.

Tras dos intentos acotados sin recreación, el protocolo eligió recrear ambos
silos. Cambiaron sus IDs de contenedor y generaciones de membresía; el ledger
persistió. Esto demuestra esa vía asistida, no que reiniciar fuera necesario,
que recuperar sin intervención fuera imposible, failover automático o RTO
productivo. El C#, oráculo SQL, política predeterminada y helpers del caso breve
siguen intactos. Se retiraron dependencias de captura y observadores antes de
recrear; los nuevos observadores se unieron a sustitutos ya preparados.

Las 14 parejas conservaron los mismos contenedores/PID recuperados, dos miembros
Active, SQL 3/6/3 y siete invariantes. Cada pareja respondió
DUPLICATE_COMMITTED; los huecos reales entre muestras no superaron 10 segundos.
Es **estabilidad muestreada**, no disponibilidad continua, carga sostenida,
activación exclusiva, ausencia de split brain, HA PostgreSQL o resiliencia entre
hosts. Los catálogos no son observaciones atómicas.

## Los fallos originales siguen siendo fallos

[Primera ejecución #41605736830](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41605736830),
fuente `62d78fbddc206babbe3cbd28630f33464271d619`: ambos casos fallaron.
[ZIP primario](e2-long-first-primary-original.zip) / [JSON](e2-long-first-primary-original.json):
Podman rechazó la recreación por dependencias de contenedores de captura terminados.
[ZIP secundario](e2-long-first-secondary-original.zip) / [JSON](e2-long-first-secondary-original.json):
un helper transitorio y la restauración notificaron regla ausente después de
observar la salida del secundario. No está demostrada la causa exacta de esa
transición. Ninguno acredita recuperación. El [protocolo](../../lab/e2_orleans/LONG_PARTITION_PROTOCOL.md)
conserva hashes y auditoría de fuentes. La corrección separó las vidas de los
diagnósticos y su limpieza sin rebajar SQL, tiempos ni estabilidad muestreada.

Siguiente subpaso de #24: observar explícitamente activaciones concurrentes y su
aceptación SQL; no asumir exclusividad global del actor. Siguen abiertos #25,
los dominios físicos independientes y la causa de colocación natural #74.
G2 INCONCLUSIVE/G6 BLOCK; #53 congelado; sin release ni tag nuevos.

[English](E2-LONG-PARTITION.md) · [Auditor](../../scripts/check_e2_long_partition_observations.py)
