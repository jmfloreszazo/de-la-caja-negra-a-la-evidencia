# C2: supresión direccional del flujo al controlador — observación original

[English](BROWNFIELD-CONTROLLER-PARTITION.md). Sigue #58/#32. Es un ensayo sintético de ingeniería acotado, no aprobación de corte bancario.

La [ejecución original 41792899739](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41792899739), fuente/checkout `a9ae65dcf0704147d99b2af16fae4a538daa0189`, pasó los cuatro casos nuevos. El [ZIP sin modificar](../brownfield/c2-directional-original.zip), artefacto `13303828084`, tiene SHA-256 `7c402c85cdee0b3481edeac5a2a6518f2843b419887d7537014c256ec373a523`. Conserva también las salidas del journal y pérdida de sesión TCP ejecutadas en el mismo job; no se reasignan experimentos históricos a esta fuente.

El [protocolo declarado](../../lab/brownfield/journal/PARTITION_CONTRACT.md) cruza legado Python/candidato .NET con dos direcciones de supresión del flujo opaco de aplicación. El relay consume/descarta bytes sin cerrar los sockets existentes. TCP confirma las lecturas del proxy: no emula pérdida de paquetes del kernel ni un fallo físico independiente de red.

## Qué se observó

| Escritor | Dirección suprimida | Consulta marcada en servidor | Estado del controlador tras COMMIT financiero separado | Efecto financiero final |
|---|---|---|---|---|
| Legado | Cliente a servidor | No recibida | idle in transaction | 1 decisión / 2 apuntes / 1 outbox |
| Legado | Servidor a cliente | Recibida; respuesta ausente al cliente | idle | 1 / 2 / 1 |
| Candidato | Cliente a servidor | No recibida | idle in transaction | 1 / 2 / 1 |
| Candidato | Servidor a cliente | Recibida; respuesta ausente al cliente | idle | 1 / 2 / 1 |

Antes de liberar la barrera SQL financiera, una sesión independiente observó la espera real del adaptador y cero decisiones/apuntes/outbox visibles. Las sesiones del controlador que mantenían autoridad siguieron vivas y en transacción durante una muestra de al menos un segundo; se conservan PIDs, consultas y contadores por dirección. La admisión nueva y el cambio de escritor fallaron durante la supresión sin cambiar la autoridad. El gateway recibió SIGKILL externo (-9), mientras su hijo financiero seguía en vuelo.

Liberar la barrera permitió un efecto financiero duradero en el ledger separado mientras seguía activa la supresión. La admisión permanecía DISPATCHING antes de recuperar. Por tanto, la respuesta ausente no significaba ausencia de COMMIT financiero. La diferencia idle/idle in transaction corresponde a estos cuatro intentos; no garantiza comportamiento universal de drivers o timeouts.

La recuperación cerró explícitamente todas las sesiones del relay y permitió conexiones nuevas. La conciliación encontró COMMITTED; repetir la instrucción devolvió DUPLICATE_COMMITTED sin apuntes adicionales. Ambos snapshots pasan diez predicados SQL originales cada uno. Se rechazaron dos copias alteradas: falsa ausencia de efecto financiero y falsa recuperación automática; los originales siguen intactos.

## Reproducción y auditoría

El workflow C2 ejecuta el journal original y el ensayo de pérdida de conexiones antes del script nuevo de cuatro casos. La [guía en inglés](../../lab/brownfield/journal/README.md) describe el entorno desechable. El entorno original incluye .NET SDK 10.0.403, Python 3.12, PostgreSQL 16.13, Ubuntu 24.04 y un runner; versiones e identidades exactas de imagen/contenedores están en `provenance.txt` dentro del ZIP.

`python3 scripts/check_c2_directional_observations.py` audita archivo, trece hashes históricos, observaciones de PIDs/consultas, snapshots y ambos mutantes rechazados. Un checkout superficial necesita descargar primero el commit original. El auditor extrae la función pura histórica del archivo original sin importar código de conexión ni modificar el oráculo protegido.

## Aceptación pendiente

G2 sigue INCONCLUSIVE y G6 BLOCK. No se afirma recuperación transparente, cancelación financiera inmediata, HA física, comportamiento nativo mainframe, capacidad sostenida ni fencing bancario real. Quedan pérdida/retransmisión de paquetes reales, presupuestos de keepalive/timeout/duración de locks, fallos simétricos, hosts independientes, fencing en origen, efectos externos y políticas aprobadas en #58. La validación externa no bloquea integrar este incremento acotado.
