# Registro de revisión editorial y evidencia

[English](EDITORIAL_REVIEW.md) · **Español**

Este documento pertenece a la **siguiente revisión editorial**. No modifica la edición ya publicada [v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29), su atribución ni sus resultados. Su función es convertir las críticas en hipótesis comprobables, no dar por verdaderas afirmaciones desactualizadas.

## Estado comprobado

| Afirmación | Estado a 29-10-2026 | Evidencia y límite |
|---|---|---|
| El repositorio y la release son accesibles | Verificado | [Release v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29), con PDF ES/EN y Markdown ES/EN |
| La CI del libro se ejecutó | Verificado | [Book PR #2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252122) completó Markdown, enlaces, sincronía y diagramas |
| El laboratorio corrió en GitHub Actions | Verificado | [Lab PR #2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252152) pasó los jobs offline, native y Podman en runners Linux |
| Ambos PDF se generan | Verificado | [Book PDF preview](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252098) y assets de la release |
| Portabilidad en cada equipo Linux/macOS/Windows | Pendiente de reproducción | La CI alojada en Linux no equivale a pruebas manuales en todos los sistemas |
| Listados marcados *Ilustrativo* compilados | No acreditado | Hacer inventario, compilar y publicar resultados antes de cambiar su etiqueta |
| E1: motor SQL con bloqueos por fila | Diseñado, no ejecutado | [Protocolo E1–E4](../lab/docs/EXPERIMENT_PROTOCOL.md) |
| E2: Orleans; E3: Azure/local; E4: agentes bajo oráculo | Diseñados, no ejecutados | No equivalen a mediciones de capacidad o garantías en producción |
| Calidad idiomática integral del inglés | Revisión especializada pendiente | `scripts/check.py` verifica estructura, no calidad lingüística |

## Plan por puertas de calidad

| Prioridad | Trabajo | Criterio de cierre | Estado |
|---|---|---|---|
| P0 | Corregir los hechos obsoletos sobre release, Podman y CI | Enlaces a ejecuciones y distinción entre CI Linux y otras plataformas | Hecho en esta rama |
| P0 | Ruta de siete capítulos, sin alterar el manuscrito | Navegación funcional, correspondencia ES/EN y tesis intacta | Hecho en esta rama |
| P1 | Revisar reiteraciones de locks, transferencias, equivalencia y mandato | Matriz de solapes con capítulos concretos y propuesta de cortes; autor aprueba cada supresión | Pendiente |
| P1 | Verificar afirmaciones atribuidas a artículos del autor | Fuente primaria leída, pasaje identificable y alcance preciso; registrar corrección o respaldo | Pendiente |
| P1 | Revisión idiomática nativa de inglés (prólogo y parte I primero) | Observaciones con ejemplos, sin modificar unilateralmente la voz | Pendiente |
| P2 | E1 PostgreSQL o SQL Server | Mismo contrato contable y controles SQLite + deadlocks/write skew/pool, evidencias reproducibles | Pendiente |
| P2 | Compilar los fragmentos *Ilustrativo* | Registro por fragmento: compilador, prueba y veredicto; sin promover ejemplos sin ejecución | Pendiente |
| P2 | Reproducciones fuera de la CI | Linux, macOS y Windows/WSL, versiones fijadas y artefactos con procedencia | Pendiente |

## Criterio editorial: precisión antes que porcentaje

No se establece un recorte automático del 15–20 %. La extensión por sí sola no prueba redundancia. Primero se documentará **qué párrafos repiten la misma idea sin aportar otra condición de decisión**. Mantener tratamientos distintos de un mismo problema cuando cambian los invariantes, la capa arquitectónica o el experimento. Ninguna edición global sin revisión del autor y sincronización bilingüe.

## Auditoría de citas: comenzar por las fuentes propias

- **[44], AHP.** El [artículo](https://jmfloreszazo.com/agent-host-protocol-ahp-por-que-el-host-y-no-tu-editor-es-el-dueno-del-estado-de-la-sesion/) sí sostiene que el host posee el estado y los clientes son vistas. Comprobar que el capítulo 8 lo usa como analogía y no como prueba de autoridad de un registro de modernización.
- **[45], Hosted Agents .NET/Python.** El [artículo](https://jmfloreszazo.com/benchmark-dos-hosted-agents-mismo-foundry-net-10-lts-vs-python-3-12/) mide latencia secuencial bajo baja carga; explícitamente **no** acredita throughput máximo ni saturación. Evitar extrapolarlo a MIPS o velocidad de una migración.
- **[1], De Leviatán al Autopilot** y **[41], harness gobernado**: contrastar cada formulación del libro con el pasaje original, no solo el título o resumen.
- El anexo G contiene referencias con alcances diferentes: documentación técnica, experimentos externos, opiniones y resultados del laboratorio. Revisar cada conclusión respecto al tipo de evidencia disponible.

## Autoría y responsabilidad editorial

El autor confirma que ha leído el libro. La revisión editorial restante es una actividad de precisión y calidad, **no prueba de que el autor no lo haya leído**. No es válido inferir quién escribió una obra a partir de las herramientas utilizadas durante su preparación. Cualquier declaración pública sobre procesos de escritura corresponde al autor y no debe añadirse por presunción.

**No cambiar `CITATION.cff`, el identificador de edición, la atribución, la licencia ni la release** desde esta rama.
