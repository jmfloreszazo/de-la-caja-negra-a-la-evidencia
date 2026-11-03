# Cierre de frentes del proyecto — 3 de noviembre de 2026

Los PR #78–#81 están integrados en main `fa0cd64355a3b75c18226ea78da149358d9531b2`. Esta limpieza administrativa no convierte pruebas parciales o INCONCLUSIVE en aceptación científica. E2 sigue parcialmente verificado y el contrato de rendimiento permanece UNCONFIGURED.

## Ramas y recuperación

El inventario inicial contiene 28 ramas remotas, incluida main. Se retiran 27 ramas de trabajo: 21 están en el historial de main y cuatro tienen un árbol idéntico al commit integrado. Otras dos corresponden a los PR duplicados #46/#67, cerrados expresamente sin fusionar; se archivan, no se incorporan como código aceptado.

El [manifiesto exacto](../evidence/maintenance/branch-closeout-2026-11-03.json) registra nombres, SHA y pruebas. Un [archivo Git recuperable](../evidence/maintenance/branch-closeout-2026-11-03.bundle) conserva las seis historias que no son ancestros de main. Las otras 21 siguen accesibles desde main. El tag publicado conserva también la referencia de la vista previa. No se eliminan tags ni releases.

La automatización comprueba el estado cerrado de cada PR, la ausencia de PR abierto y el SHA actual antes de borrar. Usa una comprobación atómica del SHA en el servidor: una rama que haya cambiado no se elimina. La rama temporal de mantenimiento solo se retira después de comprobar su propio PR fusionado. El resultado real se verifica en la ejecución y en un inventario nuevo de ramas; el plan no se presenta como una eliminación ya ejecutada. El [informe técnico](PROJECT_CLOSEOUT.md) contiene las 27 referencias y los comandos para recuperar una variante.

## Issues cerradas y obligaciones conservadas

Se cierran nueve issues y quedan trece abiertas, dos de ellas congeladas. Cerrar una tarea no convierte todas sus casillas históricas en pruebas ejecutadas.

| Cerrada | Motivo | Pendiente conservado en |
| --- | --- | --- |
| #13 | Recuperación de runners y verificaciones reales documentadas | #15: revisión de historial público, licencias e imágenes todavía no ejecutada |
| #35 | Preflight SQL y diagnóstico entregados en #36; sin afirmar ausencia futura de fallos | #8: aceptación E2 adicional |
| #75 | Anomalía de estados archivada sin explicación causal inventada | #15: registrar y escalar si reaparece |
| #74 | Persistencia de observaciones y controles negativos entregados en #76 | #8: colocación natural y ciclo de vida |
| #64 | Journal durable y recuperación/pérdida de controlador acotadas entregados | #58: ventanas restantes, fencing real y aprobación funcional |
| #29 | Duplicidad de canales consolidada, sin descartar su checklist | #30: todos los requisitos CH pendientes |
| #24 | Ensayos acotados de partición, calibración y observación entregados | #8: recuperación natural/continua y dominios físicos |
| #25 | Pilotos y diagnóstico local entregados; se retira el seguimiento duplicado | #8: capacidad sostenida, cuello de botella y p99 aún no demostrados |
| #12 | M1/M2 locales entregados; seguimiento distribuido consolidado | #9: TLS, carga distribuida, failover, WAN y TCO |

## Lo que falta y orden de trabajo

| Orden | Trabajo pendiente | Seguimiento y límite |
| --- | --- | --- |
| 1 | Semántica de SO/I-O/transacciones mainframe y catálogo de capacidades/patrones respaldado por fabricantes | #17/#18/#28; evitar laboratorios duplicados |
| 2 | Descomposición funcional y siguientes controles de coexistencia brownfield | #32/#58; trazas reales, fencing de origen y TODM G2/G6 requieren aprobación externa |
| 3 | Un capítulo completo de canales/core y laboratorio sintético ATM/digital, separando dispensación física y COMMIT | #30 incorpora #29 |
| 4 | Revisión editorial y de fuentes ES/EN: listados, citas, solapes y QA visual de PDF; reproducción en otros sistemas | #11; generar una vista previa no autoriza publicar |
| 5 | Refactor dedicado de organización/entrada al laboratorio y revisión de mantenimiento | #15; preservar rutas, hashes y evidencias protegidas |
| Validación externa | Capacidad/activaciones/HA E2 y comparación distribuida WAN/TCO E3 | #8/#9 y [protocolo](EXTERNAL_VALIDATION.md); no bloquea avanzar el libro |
| Experimento posterior | Propuesta de agente frente a Oracle Gate independiente y controles de mutación | #10; E4 sigue sin aceptación |
| Congelado | Protección de main y clean rooms/confidential computing | #16/#53; fuera del plan activo hasta nueva instrucción |

A partir de este corte, una rama breve por entregable concreto y retirada tras comprobar su integración. La procedencia experimental se conserva mediante commits, originales y archivo recuperable, sin mantener ramas de trabajo integradas como si siguieran activas.

El primer incremento de #30 incorpora el capítulo bilingüe de canales y un laboratorio nativo de efectivo/digital con almacenes separados. El [checkpoint de canales](CHANNELS_CHECKPOINT_2026-11-03.es.md) conserva éxitos/fallos originales y la matriz pendiente. No cierra #30.

Prioridad actualizada tras #83/#84: contratos de plataforma, descomposición/coexistencia, canales pendientes, revisión/reproducción completa y mantenimiento del laboratorio. El [roadmap activo](../ROADMAP.es.md) recoge agentes y validación externa.
