# Registro de revisión editorial y evidencia

[English](EDITORIAL_REVIEW.md) · **Español**

Este documento pertenece a la **siguiente revisión editorial**. No modifica la edición ya publicada [v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29), su atribución ni sus resultados. Su función es convertir las críticas en hipótesis comprobables, no dar por verdaderas afirmaciones desactualizadas.

## Estado comprobado

| Afirmación | Estado a 30-10-2026 | Evidencia y límite |
|---|---|---|
| El repositorio y la release son accesibles para colaboradores autorizados | Verificado | El repositorio continúa privado; la [release v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29) incluye PDF y Markdown ES/EN. No está aprobada su apertura pública. |
| La CI del libro se ejecutó | Verificado | [Book PR #2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252122) completó Markdown, enlaces, sincronía y diagramas |
| El laboratorio corrió en GitHub Actions | Verificado | [Lab PR #2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252152) pasó los jobs offline, native y Podman en runners Linux |
| Ambos PDF se generan | Verificado | [Book PDF preview](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252098) y assets de la release |
| Portabilidad en cada equipo Linux/macOS/Windows | Pendiente de reproducción | La CI alojada en Linux no equivale a pruebas manuales en todos los sistemas |
| Listados marcados *Ilustrativo* compilados | No acreditado | Hacer inventario, compilar y publicar resultados antes de cambiar su etiqueta |
| E1a: bloqueo por filas PostgreSQL y oráculo contable persistido | Ejecutado en CI | [Ejecución #40919268337](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919268337): PostgreSQL real con controles negativos independientes; prueba sintética, no paridad productiva. |
| E1b: paridad de estado y fallos con .NET 10/Npgsql | Subconjunto ejecutado | [Ejecución #40919773614](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40919773614): subconjunto comparado frente al candidato Python/PostgreSQL; paridad SQLite completa pendiente [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6). |
| E1 global | Parcialmente verificado | Falta SQL Server E1c [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) y completar la paridad funcional. No hay PASS global de E1. |
| Pruebas M1/M2 de transporte local | Ejecutadas en CI | [M1](../evidence/runs/M1.es.md) aísla el protocolo; [M2](../evidence/runs/M2.es.md) ejecuta 20 casos durables en un runner, sin demostrar Azure, TLS, WAN ni escala distribuida. |
| E2: Orleans; E3: Azure/local; E4: agentes bajo oráculo | Diseñados, no ejecutados | No equivalen a mediciones de capacidad o garantías en producción |
| Calidad idiomática integral del inglés | Revisión especializada pendiente | `scripts/check.py` verifica estructura, no calidad lingüística |

**Límite de publicación:** estos resultados están en la [PR #5 en borrador](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/5), no en la release `v2026.10.29`. Sus artefactos y versión permanecen intactos.

## Plan por puertas de calidad

| Prioridad | Trabajo | Criterio de cierre | Estado |
|---|---|---|---|
| P0 | Corregir los hechos obsoletos sobre release, Podman y CI | Enlaces a ejecuciones y distinción entre CI Linux y otras plataformas | Hecho en esta rama |
| P0 | Ruta de siete capítulos, sin alterar el manuscrito | Navegación funcional, correspondencia ES/EN y tesis intacta | Hecho en esta rama |
| P1 | Revisar reiteraciones de locks, transferencias, equivalencia y mandato | Matriz de solapes con capítulos concretos y propuesta de cortes; autor aprueba cada supresión | Pendiente |
| P1 | Verificar afirmaciones atribuidas a artículos del autor | Fuente primaria leída, pasaje identificable y alcance preciso; registrar corrección o respaldo | Pendiente |
| P1 | Revisión idiomática nativa de inglés (prólogo y parte I primero) | Observaciones con ejemplos, sin modificar unilateralmente la voz | Pendiente |
| P2 | Completar paridad E1 y cobertura SQL Server | Conservar E1a/E1b parcial y ejecutar los casos de equivalencia SQLite pendientes [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) y controles SQL Server [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) | Parcialmente ejecutado; cierre pendiente |
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
