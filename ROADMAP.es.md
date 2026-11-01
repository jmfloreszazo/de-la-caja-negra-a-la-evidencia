# Hoja de ruta abierta

[English](ROADMAP.md) · **Español**

Trabajo que el libro deja planteado y que la comunidad puede hacer avanzar. Cada línea indica su etiqueta. Las issues [#6–#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues) siguen abiertas y no tienen un hito asignado. La preparación de una futura versión pública requiere revisión y autorización expresa del autor; este documento no establece una fecha de publicación.

## Validar lo que no se pudo validar

| Tarea | Por qué importa | Etiqueta |
|---|---|---|
| Construir la imagen Podman en Linux, macOS y Windows y compartir el informe | La CI valida la receta; lo que cuenta son las máquinas reales | `reproduction`, `good first issue` |
| Repetir el laboratorio fuera de los runners Linux de CI y publicar condiciones/reporte | La [CI offline/nativa/Podman](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252152) ya pasó; faltan reproducciones independientes y entre plataformas | `reproduction` |
| Compilar los listados *Ilustrativo* en un proyecto de ejemplo y marcar los que pasen a *Verificado* | Hoy son fragmentos de razonamiento; algunos merecen ser código | `lab`, `good first issue` |

## Experimentos: evidencia obtenida y puertas pendientes

El protocolo general está en [`lab/docs/EXPERIMENT_PROTOCOL.md`](lab/docs/EXPERIMENT_PROTOCOL.md) y el plan detallado en [`docs/EXPERIMENT_ROADMAP.md`](docs/EXPERIMENT_ROADMAP.md). La [PR #5](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/5) está fusionada. Las evidencias posteriores deben asociarse al SHA y ejecución originales; fusionar una PR no modifica retrospectivamente la edición `v2026.10.29`.

| Fase | Estado comprobado y límite | Seguimiento |
|---|---|---|
| E1a · PostgreSQL 16 con Podman | Ejecutado en CI: deadlocks, aislamiento y oráculo persistente. No demuestra capacidad bancaria ni E1 completo. | [Evidencia](evidence/runs/README.es.md) |
| E1b · .NET 10/Npgsql | Pasaron los 7 controles originales, la [ampliación E1b de 10 controles](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) y [16 casos directos SQLite/PostgreSQL con desbloqueo real](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923). La [matriz PostgreSQL de 960 transferencias](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329) pasó, y SQL Server E1c superó también su propia [matriz de 960 transferencias](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) y otra [con trabajadores .NET persistentes](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791). Son verificaciones funcionales sintéticas, no benchmarks comparables de rendimiento. | [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) |
| E1c · SQL Server | [Ejecución real SQL Server 2022](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41040632819): 16 casos de referencia, deadlock 1205 con reintento, seis bloqueos 1222, control negativo SNAPSHOT, defensa SERIALIZABLE y oráculo independiente. También superó la [matriz SQL Server de 960 transferencias en ocho escenarios](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263), con las cuatro tablas coincidentes y siete invariantes independientes correctos.  La [repetición con trabajadores .NET persistentes #41043087791](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41043087791) verificó por separado los ocho escenarios, 960 operaciones confirmadas y el oráculo independiente. Siguen pendientes los fallos productivos, la alta disponibilidad y las comparaciones válidas de rendimiento. | [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) |
| M1 · gRPC/REST sin persistencia | Microbenchmark localhost ejecutado; no es una prueba bancaria ni de WAN. | [Informe](evidence/runs/M1.es.md) · [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) |
| M2 · gRPC/REST con PostgreSQL | Veinte casos durables ejecutados sobre un único runner y una base compartida; no acredita escalabilidad distribuida. | [Informe](evidence/runs/M2.es.md) · [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) |
| E2 · Orleans y ledger durable | **Ejecutado parcialmente en CI**: membresía PostgreSQL, SIGKILL, particiones de red y pilotos open-loop sintéticos. Falta rendimiento sostenido comparable, completar F10, comprobar dominios físicos independientes y aceptar E2 globalmente. C04 continúa en borrador, sin CI propio. | [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) · [#24](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/24) · [#25](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/25) |
| E3 · Azure, local e híbrido | Diseñado, no ejecutado. Hay precios fechados y modelos ilustrativos, pero no benchmark comparativo aprobado. | [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9) · [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) |
| E4 · Agentes bajo Oracle Gates | Diseñado, no ejecutado. | [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) |

**Criterio de cierre:** E1 solo podrá declararse verificado al completar su paridad funcional y las pruebas pendientes; E2, E3 y E4 requieren oráculos independientes, controles negativos y evidencias reproducibles. Los checks de CI no sustituyen la aprobación de versión.

## Prioridad: modernización brownfield CAP-007/CAP-005

La migración parte de un COBOL existente y de sus contratos de negocio: no es
un proyecto greenfield ni una traducción sintáctica 1:1. Las PR #59–#63
incorporaron .NET 10/PostgreSQL persistente, dos almacenes, conciliación SQL,
shadow sin doble contabilización y cutover/rollback sintéticos.
[La issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)
sigue abierta: no se ha demostrado fencing en un mainframe real.

La [PR #66, C2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/66)
introduce un tercer PostgreSQL para registrar admisiones y resultados UNKNOWN,
recuperar caídas con oráculos SQL y ensayar un fencing cooperativo en ambos
adaptadores. Es un avance PARCIAL: una escritura directa todavía puede omitir
el journal y la actualización de las dos autoridades no es atómica.
TODM G2=INCONCLUSIVE y G6=BLOCK. Exige CI original sobre SHA exacto y no
implica una nueva release.

Después: eliminar el bypass, tratar ventanas de crash entre autoridades
([#64](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/64)),
completar E2 y medir E3 sobre Azure, local e híbrido, comparando escalado
horizontal, gRPC y costes fechados; posteriormente E4 y agentes bajo Oracle Gates.
Clean rooms y Confidential Computing ([#53](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/53))
permanecen **congelados para una versión futura**.

## Laboratorio: siguientes katas

- Convertir el codec COMP-3 del capítulo 15 en un módulo con sus vectores de prueba.
- Añadir un adaptador EBCDIC con CCSID explícito y casos de ordenación.
- Ampliar el contrato con importes negativos y una matriz de opciones de compilación.
- Portar el oráculo contable a .NET para tener dos verificadores independientes.

## Libro

- Mantener sincronizadas las ediciones en español e inglés (`scripts/check.py` lo exige) y acoger otros idiomas con la misma estructura.
- Ampliar el glosario y el catálogo de riesgos (R101 en adelante) con evidencia real.
- Casos reales anonimizados, con permiso explícito y sin cifras de cliente identificables.
