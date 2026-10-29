# Ruta rápida · siete capítulos

[English](READING_PATH.md) · **Español** · [Libro completo](../book/es/README.md)

Esta selección es una **ruta de lectura**, no una edición abreviada ni un resumen que sustituya los capítulos. Conserva la progresión desde el riesgo de traducir hasta la decisión verificable.

| Orden | Lectura | Pregunta que responde |
|---|---|---|
| 1 | [Capítulo 3 · Por qué la conversión uno a uno no es modernización](../book/es/parte-1-antes-de-traducir/03-por-que-la-conversion-uno-a-uno-no-es-modernizacion.md) | ¿Qué problema resuelve realmente un cambio de lenguaje? |
| 2 | [Capítulo 6 · REA y la arqueología que deja rastro](../book/es/parte-2-arqueologia-y-autoridad/06-rea-y-la-arqueologia-que-deja-rastro.md) | ¿Cómo convertimos interpretaciones del legado en evidencias trazables? |
| 3 | [Capítulo 10 · TODM y el problema de aceptar lo que construimos](../book/es/parte-3-oraculos/10-todm-y-el-problema-de-aceptar-lo-que-construimos.md) | ¿Quién decide qué constituye una salida correcta? |
| 4 | [Capítulo 17 · De los locks del mainframe al control explícito de concurrencia](../book/es/parte-4-patrones/17-de-los-locks-del-mainframe-al-control-explicito-de.md) | ¿Qué garantía transaccional debemos conservar? |
| 5 | [Capítulo 24 · El benchmark que vale: carga, contención, fallo y coste](../book/es/parte-5-capacidad/24-el-benchmark-que-vale-carga-contencion-fallo-y-coste.md) | ¿Por qué los MIPS no se sustituyen por una cifra aislada de vCPU? |
| 6 | [Capítulo 28 · Transferencias, bloqueos y fallos en local](../book/es/parte-6-laboratorio/28-transferencias-bloqueos-y-fallos-en-local.md) | ¿Qué controles podemos ejecutar y refutar ahora? |
| 7 | [Capítulo 37 · El nuevo contrato de modernización](../book/es/parte-7-organizacion/37-el-nuevo-contrato-de-modernizacion.md) | ¿Qué evidencia exige la decisión de migrar? |

## Complemento ejecutable

El [laboratorio](../lab/README.md) demuestra mecanismos concretos con GnuCOBOL, .NET 10 y SQLite. Para comprobarlo sin compiladores, ejecuta:

```bash
python3 lab/tools/verify_offline.py
```

Para recorrer el caso completo con Podman en un entorno compatible:

```bash
cd lab
bash scripts/run-podman.sh --auto
```

**No extrapoles:** la prueba local valida mecanismos e invariantes, no la capacidad de un mainframe. Los experimentos E1–E4 se encuentran diseñados, pero no ejecutados. Consulta el [registro de evidencia y revisión](EDITORIAL_REVIEW.es.md) antes de citar resultados.

Para seguir profundizando: capítulos 12 (equivalencia), 19 (actores) y 35 (cuándo no migrar).
