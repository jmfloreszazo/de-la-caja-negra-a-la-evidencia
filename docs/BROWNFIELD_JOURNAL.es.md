# Brownfield C2 — journal de admisión, UNKNOWN y conciliación tras caídas

**Contrato experimental, 1 de noviembre de 2026. Sin aceptación bancaria.**

El riesgo que sigue a la convivencia de dos almacenes es la operación
ambigua: PostgreSQL confirma el COMMIT, pero el gateway no recibe el ACK.
La ausencia de respuesta **no equivale a rollback**, ni permite reenviar
la misma transferencia a otro escritor.

La nueva base PostgreSQL `bf_control` conserva el identificador CAP-007,
la huella canónica de la petición, escritor y época, referencias sintéticas
de tenant, actor y mandato, y estados `ADMITTED`, `DISPATCHING`,
`UNKNOWN`, `COMMITTED`, `REJECTED` y `RECONCILIATION_REQUIRED`.
El gateway serializa por identificador entre clientes cooperativos y puede
morir antes o después del COMMIT remoto. Un oráculo SQL independiente y
de solo lectura inspecciona ambos almacenes y únicamente confirma decisiones
persistidas y concordantes. Si no observa una decisión, mantiene UNKNOWN;
nunca inventa REJECTED.

## Controles negativos obligatorios

- Caída tras la admisión antes del envío: sin promoción a rechazo.
- Caída después de COMMIT y antes de actualizar el journal: recuperación
  de una sola transferencia duradera.
- Misma operación con huella diferente: conflicto.
- Decisión terminal falsificada en el journal: el oráculo debe rechazarla.
- Cutover bloqueado ante admisiones inciertas o efectos sin journal.
- Rollback vetado después de operaciones originadas en el candidato.
- Divergencia de épocas entre controlador y candidato: nuevas admisiones bloqueadas.

## Estado integrado y límites pendientes

La PR #69 añade inscripción SQL persistida en ambos adaptadores. Después de
inscribirse, quitar la variable de entorno no permite escribir sin admisión;
el CLI independiente de cambio de autoridad también debe rechazar el bypass.
Antes de cambiar épocas se confirma una intención PREPARED y un estado
SWITCHING que congela el tráfico. SIGKILL externos ensayan la recuperación
hacia adelante entre los dos COMMIT de autoridad. No es COMMIT distribuido.

La [CI sobre main #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630)
superó 20 controles en `279ca566`; ambos oráculos SQL 10/10. La
[evidencia anterior de 19 controles](../evidence/runs/BROWNFIELD-C2-RECOVERY.es.md)
se conserva como observación de su propio SHA, incluido el primer fallo.

Quedan pendientes particiones durante operaciones en curso, pérdida de
bloqueos, otras ventanas de proceso/respuesta y conciliación de efectos
externos. El SQL directo con privilegios y un mainframe no cooperativo siguen
fuera del fence de aplicación. Los tres contenedores comparten un runner;
no se acredita HA física, RTO/RPO ni autoridad bancaria real. G2=INCONCLUSIVE,
G6=BLOCK; #64/#58 abiertas y #53 congelada. No cambia ninguna release.
