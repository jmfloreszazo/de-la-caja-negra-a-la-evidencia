# Brownfield C2 — journal de admisión, UNKNOWN y conciliación tras caídas

**Contrato experimental, 1 de noviembre de 2026. Sin aceptación bancaria.**

El riesgo que sigue a la convivencia de dos almacenes es la operación
ambigüa: PostgreSQL confirma el COMMIT, pero el gateway no recibe el ACK.
La ausencia de respuesta **no equivale a rollback**, ni permite reenviar
la misma transferencia a otro escritor.

La nueva base PostgreSQL \`bf_control\` conserva el identificador CAP-007,
la huella canónica de la petición, escritor y época, referencias sintéticas
de tenant, actor y mandato, y estados \`ADMITTED\`, \`DISPATCHING\`,
\`UNKNOWN\`, \`COMMITTED\`, \`REJECTED\` y \`RECONCILIATION_REQUIRED\`.
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

## Garantías todavía ausentes

Los CLI existentes del legado sintético (Python) y del candidato (.NET 10)
pueden invocarse directamente, evitando el gateway: **todavía no obedecen
obligatoriamente al tercer controlador**. El bloqueo \`FOR SHARE\` de la base
del candidato sigue siendo cooperativo. Las dos épocas de autoridad cambian
en transacciones distintas: faltan una actualización atómica distribuida
y un protocolo validado de reparación del estado intermedio. Un escritor
externo no cooperativo y los procesadores de pagos quedan fuera.

Los tres PostgreSQL ejecutan contenedores **en un único runner**; no existe
prueba entre dominios físicos independientes. Las referencias de autorización
son ficticias. No se demuestra una migración CICS/Db2, 2PC, capacidad bancaria,
RTO/RPO ni aprobación de negocio. TODM G2=INCONCLUSIVE y G6=BLOCK.

**Estado de evidencia:** CANDIDATO DE CÓDIGO, no evidencia CI aceptada
hasta obtener una ejecución original ligada al SHA exacto con artefactos.
Continúan abiertas las issues #64 y #58. No se modifica la release ni
se reactiva #53.
