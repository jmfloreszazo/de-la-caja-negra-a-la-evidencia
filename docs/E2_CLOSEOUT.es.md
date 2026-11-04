# E2 Orleans — cierre de la campaña de alcance acotado (4 de noviembre de 2026)

**Decisión:** queda **cerrada la campaña experimental E2 ejecutable en CI alojada, dentro de su alcance acotado**. La aceptación científica sigue siendo **PARTIALLY_VERIFIED (parcialmente verificado)**. **No** significa que hayan superado las pruebas de capacidad distribuida, recuperación natural, alta disponibilidad física o preparación bancaria para producción. El seguimiento [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) se cierra como **no planificado dentro de esta campaña**, no como ejecución satisfactoria de todos sus criterios externos.

## Evidencia conservada y aceptada dentro del alcance

| Escenario | Evidencia / observación original | Límite de lo demostrado |
| --- | --- | --- |
| Membresía ADO.NET en PostgreSQL, muerte de proceso y libro mayor autoritativo | [Ejecución 41098437285](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41098437285): dos miembros activos, caída del secundario, ruta superviviente, repetición idempotente y 7/7 invariantes financieros independientes | Los dos silos comparten un runner y una base de datos |
| Transacción SQL en curso y repetición posterior a COMMIT | [Ejecución 41102529778](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41102529778): terminación real antes de COMMIT, repetición y oráculo SQL independiente | Caída de proceso, **no** corte eléctrico del almacenamiento ni HA distribuida |
| Fallos direccionales de red y conciliación | [Informe C05/C06](../evidence/runs/E2-C05-C06-DIRECTIONAL.es.md): PCAP, dirección y conciliación SQL 7/7 | Fallos controlados y acotados; no exclusividad global demostrada |
| Activaciones y recuperación controladas | [C01](../evidence/runs/E2-C01-CONTROLLED.es.md) y [observaciones dirigidas](../evidence/runs/E2-ACCOUNT-DIRECTED.es.md): **dos testigos positivos y cuatro INCONCLUSIVE** conservados | Sin acreditar colocación natural ni recuperación continua sin intervención |
| Partición larga programada | [Informe auditado](../evidence/runs/E2-LONG-PARTITION.es.md), [ejecución 41607407356](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41607407356): dos casos acotados tras recrear silos, 14 muestras pareadas durante unos 66 segundos | El programa de 120 s incluyó la salida anterior del secundario: **no** prueba 120 s de servicio dual continuo, recuperación automática ni RTO productivo |
| Diagnósticos de admisión/carga | [B05](../evidence/runs/B05-DISPATCH-DIAGNOSTIC.md): 119.040 ofertas, 118.887 COMMIT SQL, 153 omisiones con límite 32 y 42 controles financieros | Sin knee de capacidad aceptado, escalado Orleans comparable ni p99 productivo |
| Integridad de observaciones negativas | [Informe de colocación](../evidence/runs/E2-PLACEMENT-OBSERVATION.es.md) con errores y controles de efectos cero preservados | Nunca se convierte FAIL/INCONCLUSIVE en PASS |

Se conservan los SHA originales, ejecuciones de CI, manifiestos, resultados negativos y evidencias auditadas. Son experimentos **sintéticos**, no observaciones de un mainframe bancario real.

## Criterios no superados, expresamente fuera de esta campaña

1. **Capacidad sostenida:** generador, silos y SQL en hosts separados, driver externo, carga reproducible, p99 comparable direct/Orleans, espera del pool y claves calientes.
2. **Ciclo de vida y recuperación natural:** grain ordinario sin puertas artificiales, relojes con incertidumbre medida, activación observada y recuperación sin recreación asistida tras particiones largas.
3. **Dominios físicos y durabilidad:** hosts o zonas independientes, replicación/failover SQL, pérdidas de nodo/zona y conciliación de operaciones confirmadas.
4. **Aceptación del cliente:** contratos de negocio, trazas aprobadas y mandato para despliegue.

El procedimiento y los cambios necesarios en infraestructura, driver, telemetría y experimentos están documentados en [EXTERNAL_VALIDATION.md](EXTERNAL_VALIDATION.md). Siguen siendo requisitos **para futuras afirmaciones de mayor alcance**, pero no tareas entregadas. Se desconoce la causa histórica de determinadas incidencias de arranque/colocación. TODM **G2 = INCONCLUSIVE**, **G6 = BLOCK** y el contrato de rendimiento permanece **UNCONFIGURED**. Este cierre no autoriza una release ni un despliegue bancario, ni demuestra equivalencia MIPS/vCPU.

## PR #89 — independiente de la aceptación E2

El [PR #89](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/89), fusionado como `1f2fbe6172b850a6758bc629c6d9f4ff26b4d0f4`, añadió la reproducción de **otro** walkthrough sintético. La [ejecución Linux Podman 41814281042](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41814281042) obtuvo PASS y guardó el artifact y la auditoría SQLite. macOS/Windows ejecutaron las pruebas unitarias del recolector, no el laboratorio completo. **El PASS de #89 no mejora el estado de HA, capacidad ni colocación de E2.**

## Cierre administrativo definitivo de este alcance

- Los incrementos E2 implementados y sus diagnósticos quedan integrados, manteniendo las evidencias originales.
- El issue [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) se cierra con motivo **NOT_PLANNED** para su validación externa en esta campaña: **no** es una aceptación E2 completa.
- No se desactiva ni debilita ningún gate. El estado de evidencia continúa `partially_verified`.
- Una nueva aceptación de capacidad, recuperación natural o HA física requiere campaña externa separada, autorización, infraestructura adecuada, pruebas originales e issue específico.
- [English closeout](E2_CLOSEOUT.md).
