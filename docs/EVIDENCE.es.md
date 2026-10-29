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
| `E1` | Bloqueo por fila, deadlocks y write skew en SQL | **Diseñado, NO ejecutado** | E1a/E1b probados; E1 global aún no completado | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E2` | Orleans y ledger frente a distintas distribuciones de carga | **Diseñado, NO ejecutado** | Sin benchmark E2 ejecutado contra E1 | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E3` | Benchmark Azure frente a local e híbrido | **Diseñado, NO ejecutado** | Sin ensayo de capacidad, coste y fallo con contrato real | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `E4` | Comparativa de agentes bajo oráculo independiente | **Diseñado, NO ejecutado** | Sin evaluación E4 ejecutada de defectos y coste | [Protocolo, no resultado](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| `CROSS-PLATFORM` | Reproducción independiente en macOS/Windows | **Pendiente de reproducción** | Solo se ha verificado ejecución CI Linux | [Protocolo, no resultado](../ROADMAP.md) |
| `ILLUSTRATIVE` | Compilación de todos los ejemplos Ilustrativos | **Pendiente de reproducción** | No existe una verificación exhaustiva de esos listados | [Protocolo, no resultado](../ROADMAP.md) |

## Cómo interpretar la matriz

**Ejecutado en CI** significa que la ejecución enlazada terminó satisfactoriamente en un runner GitHub Linux. No implica garantía operativa en producción.

**Diseñado, NO ejecutado** significa que hay protocolo y criterios de aceptación, pero no hay resultados experimentales. Esto incluye explícitamente E1–E4.

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

El [protocolo E1–E4](../lab/docs/EXPERIMENT_PROTOCOL.md) define las próximas pruebas; no es evidencia de que hayan ocurrido.
