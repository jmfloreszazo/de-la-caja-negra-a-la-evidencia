# Matriz de evidencia y límites

[English](EVIDENCE.md) · **Español**

**Principio:** publicar, ejecutar y diseñar no son lo mismo. El objetivo es que el lector sepa exactamente qué está demostrado y qué falta.

| ID | Afirmación | Estado | Límite | Procedencia |
|---|---|---|---|---|
| `BOOK-CI` | Sincronía ES/EN, enlaces, Markdown y diagramas | **Ejecutado en CI** | Validación estructural, no certificación de calidad idiomática | [Ejecución #40901043531](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043531) |
| `ORACLE-LAB` | Laboratorio de contrato COBOL/.NET y Oracle Gate | **Ejecutado en CI** | Controles sintéticos con 58 casos; no equivalencia de un sistema bancario real | [Ejecución #40901043412](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043412) |
| `SQLITE-LAB` | Invariantes contables y concurrencia en SQLite | **Ejecutado en CI** | No demuestra bloqueo por fila en PostgreSQL/SQL Server ni escala mainframe | [Ejecución #40901043412](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043412) |
| `PODMAN-CI` | Contenedor y laboratorio ejecutados con Podman en Linux CI | **Ejecutado en CI** | La CI de Ubuntu no acredita portabilidad universal | [Ejecución #40901043412](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40901043412) |
| `RELEASE-BOOK` | Ediciones ES/EN en PDF y Markdown publicadas | **Publicado** | Un artefacto publicado no acredita todas las afirmaciones que contiene | [v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29) |
| `E1A` | PostgreSQL real: locks, deadlock 40P01, write skew 40001 y oráculo | **Ejecutado en CI** | Prueba sintética en Linux/Podman, no benchmark ni implementación bancaria productiva. El conjunto E1 aún no está completo. | [Ejecución #40919268337](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337) |
| `E1B` | Candidato .NET 10/Npgsql: paridad de estados y fallos PostgreSQL | **Ejecutado en CI** | Paridad diferencial del subconjunto probado frente al candidato Python; no acredita todo el laboratorio SQLite ni SQL Server. | [Ejecución #40919773614](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614) |
| `E1B-EXT` | Extensión .NET 10/Npgsql: reintentos, recuperación y oráculo negativo independiente | **Ejecutado en CI** | Diez controles, incluido agotamiento `55P03` y rechazo de corrupción; sigue faltando paridad SQLite/SQL Server completa. | [Ejecución #41024101879](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41024101879) · [observación original](../evidence/runs/e1b-extended.json) |
| `E1B-REF` | Paridad directa del contrato .NET 10 SQLite↔PostgreSQL | **Ejecutado en CI** | 16 casos secuenciales y desbloqueo durante reintentos; coinciden las cuatro tablas persistidas tras cada operación y pasa el oráculo independiente. No acredita toda la carga concurrente ni SQL Server. | [Ejecución #41031578923](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41031578923) · [resultado original](../evidence/runs/e1b-reference-parity.json) |
| `E1B-ORACLE` | Siete invariantes del oráculo contable independiente y corrupción deliberada de un asiento | **Ejecutado en CI** | Antes y después, 7/7 PASS; la manipulación provoca exactamente tres fallos detectados. Control negativo sintético en una base de datos, no prueba de producción. | [Ejecución #41032714628](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41032714628) · [vectores originales](../evidence/runs/e1b-oracle-vectors.json) |
| `E1B-RUNTIME` | Versiones y procedencia del entorno de E1b | **Ejecutado en CI** | Versiones del runner Linux, digest de PostgreSQL, SHA de la rama y checkout temporal de merge diferenciados; no demuestra portabilidad ni rendimiento. | [Ejecución #41033595770](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41033595770) · [manifiesto](../evidence/runs/e1b-runtime-manifest.json) |
| `E1B-MP` | Matriz multiproceso sintética uniforme/caliente SQLite/PostgreSQL | **Ejecutado en CI** | 960 transferencias lógicas con 1/2/4/8 trabajadores: coinciden los estados y pasan siete invariantes en los ocho escenarios. El distinto modelo de procesos impide comparar throughput. | [Ejecución #41034420329](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329) · [resultado original](../evidence/runs/e1b-multiprocess-parity.json) |
| `E1C` | Ensayo transaccional y aislamiento SQL Server 2022 Developer | **Ejecutado en CI** | 16 casos SQLite↔SQL Server, deadlock 1205 con reintento, seis bloqueos 1222, control negativo SNAPSHOT, protección SERIALIZABLE y oráculo de siete invariantes. No acredita prestaciones mainframe. | [CI #41040632819](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41040632819) · [JSON original](../evidence/runs/e1c-sqlserver-initial.json) |
| `E1` | Bloqueo por fila, deadlocks y write skew en SQL | **Parcialmente verificado (E1a + E1b)** | E1a/E1b comprobados; falta paridad total y SQL Server | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E2` | Orleans y ledger frente a distintas distribuciones de carga | **Diseñado, NO ejecutado** | Sin benchmark E2 ejecutado contra E1 | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E3` | Benchmark Azure frente a local e híbrido | **Diseñado, NO ejecutado** | Sin ensayo de capacidad, coste y fallo con contrato real | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E4` | Comparativa de agentes bajo oráculo independiente | **Diseñado, NO ejecutado** | Sin evaluación E4 ejecutada de defectos y coste | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `CROSS-PLATFORM` | Reproducción independiente en macOS/Windows | **Pendiente de reproducción** | Solo se ha verificado ejecución CI Linux | [Protocolo, no resultado](../ROADMAP.md) |
| `ILLUSTRATIVE` | Compilación de todos los ejemplos Ilustrativos | **Pendiente de reproducción** | No existe una verificación exhaustiva de esos listados | [Protocolo, no resultado](../ROADMAP.md) |

## Observaciones experimentales complementarias en la PR #5

- **M1 (29 de octubre de 2026):** [datos originales y resultados de transporte](../evidence/runs/M1.es.md) sobre HTTP/2 local en .NET 10, sin durabilidad SQL, TLS ni WAN. **No** acredita TPS bancarias confirmadas.
- **M2 (30 de octubre de 2026):** [20 casos durables PostgreSQL con oráculo independiente](../evidence/runs/M2.es.md), ejecutados sobre **un único runner y una base de datos compartida**, mediante REST/JSON y gRPC/Protobuf. La contención local observada no acredita escalabilidad horizontal distribuida ni E3.

Estas observaciones pertenecen a la [PR #5 en borrador](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/5), no a la release `v2026.10.29`. No promueven ningún estado global de E1–E4.

## Cómo interpretar la matriz

**Ejecutado en CI** significa que la ejecución enlazada terminó satisfactoriamente en un runner GitHub Linux. No implica garantía operativa en producción.

**Diseñado, NO ejecutado** significa que hay protocolo y criterios de aceptación, pero no hay resultados experimentales aceptados. Se aplica a E2, E3 y E4; E1 está **parcialmente verificado** mediante E1a/E1b, pero no está completo.

**Parcialmente verificado** indica que algunas subpruebas cuentan con CI propia y el experimento global aún no satisface todos sus criterios; E1a/E1b no acreditan E1c ni capacidad mainframe.

**Publicado** acredita que los ficheros existen en una release; no convierte sus afirmaciones técnicas en hechos demostrados.

## Actualizar los estados con evidencia

El registro estructurado es [`evidence/claims.json`](../evidence/claims.json). Para promover E1, E2, E3 o E4 se exige ejecución reproducible, versión del código, criterios de aceptación, casos negativos y resultados accesibles. No se aceptan PASS inventados ni una demostración aislada como prueba de capacidad.

Comprobar el contrato local:

```bash
python3 scripts/check_evidence.py
```

La comprobación **en línea** verifica también los commits, los jobs satisfactorios y los assets publicados mediante la API de GitHub:

```bash
GITHUB_TOKEN=... python3 scripts/check_evidence.py --online
```

El [protocolo E1–E4](../lab/docs/EXPERIMENT_PROTOCOL.md) define criterios de aceptación, no evidencia de ejecución. Los resultados E1a/E1b y M1/M2 citados se han registrado por separado, con su alcance experimental limitado.
