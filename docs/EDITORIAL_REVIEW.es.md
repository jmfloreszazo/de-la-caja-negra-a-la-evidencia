# Registro de revisión editorial y evidencia

[English](EDITORIAL_REVIEW.md) · **Español**

Este documento pertenece a la **siguiente revisión editorial**. No modifica la edición ya publicada [v2026.10.29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29), su atribución ni sus resultados. Su función es convertir las críticas en hipótesis comprobables, no dar por verdaderas afirmaciones desactualizadas.

## Estado comprobado

| Afirmación | Estado a 3 de noviembre de 2026 | Evidencia y límite |
|---|---|---|
| Repositorio y publicaciones | Públicos | Edición estable v2026.10.29 y prepublicación v2026.10.31-rc1; los PDF congelan sus tags, no el main actual. |
| Libro y laboratorio en main | CI ejecutada | Main integrado `3e0a949976391e0711795e8302afb63cb65bc045`: comprobaciones de código/libro/evidencia/limpieza satisfactorias; Release omitido deliberadamente. Véase el [cierre](PROJECT_CLOSEOUT.es.md). |
| PDF publicados | Generados para sus tags | Los PDF de los tags permanecen intactos. Vista previa corregida 41683984327: ES 146 / EN 142 páginas, diez páginas inspeccionadas y 32 pares de código/título comprobados; falta aprobación visual/idiomática integral. Véase el [registro](EDITORIAL_CHECKPOINT_2026-11-03.es.md). |
| E1 PostgreSQL/SQL Server | Parcialmente verificado | Paridad, concurrencia, deadlocks y controles negativos sintéticos ejecutados; no capacidad productiva, HA ni equivalencia mainframe. |
| E2 Orleans | Parcialmente verificado | Recuperación asistida larga acotada, dos testigos dirigidos/cuatro INCONCLUSIVE y diagnóstico de admisión de tres cohortes auditados. Recuperación natural/no asistida, capacidad sostenida y HA física siguen en #8; no bloquean el libro. |
| Brownfield C2/C3 | Subconjuntos ejecutados | [C2 main #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630): 20 controles y ambos oráculos SQL 10/10. No fencing real del banco ni aceptación G2/G6. |
| M1/M2 | Ejecutados en CI local | Veinte casos durables M2; no benchmark Azure, TLS comparable, WAN ni escala distribuida. |
| E3 y E4 | Diseñados, no ejecutados como experimentos completos | Precios, modelos WAN y ejemplos de agentes no sustituyen sus gates. |
| Portabilidad y listados Ilustrativo | 32 bloques emparejados inventariados | Los 27 bloques ejecutables/de configuración son idénticos y están en inglés; validación nativa seleccionada en [el inventario](BOOK_LISTINGS.es.md). Otras plataformas e integración completa siguen sin verificar. |
| Calidad idiomática integral del inglés | Revisión especializada pendiente | La sincronía automática valida estructura; no certifica traducción ni estilo. |

**Límite de publicación:** la PR #5 está fusionada. Las publicaciones estables e históricas conservan sus artefactos originales; el manuscrito actual incorpora avances posteriores.

## Plan por puertas de calidad

| Prioridad | Trabajo | Criterio de cierre | Estado |
|---|---|---|---|
| P0 | Corregir los hechos obsoletos sobre release, Podman y CI | Enlaces a ejecuciones y distinción entre CI Linux y otras plataformas | Integrado; estado reconciliado en esta revisión |
| P0 | Ruta de siete capítulos, sin alterar el manuscrito | Navegación funcional, correspondencia ES/EN y tesis intacta | Integrado; estado reconciliado en esta revisión |
| P1 | Revisar reiteraciones de locks, transferencias, equivalencia y mandato | Matriz de solapes con capítulos concretos y propuesta de cortes; autor aprueba cada supresión | Matriz acotada de cuatro filas registrada; falta revisión de todo el libro |
| P1 | Verificar afirmaciones atribuidas a artículos del autor | Fuente primaria leída, pasaje identificable y alcance preciso; registrar corrección o respaldo | [45] corregida; alcance de [44] comprobado; [1]/[41] sin revalidar |
| P1 | Revisión idiomática nativa de inglés (prólogo y parte I primero) | Observaciones con ejemplos, sin modificar unilateralmente la voz | Pendiente |
| P2 | Completar paridad E1 y cobertura SQL Server | Conservar la evidencia E1a/E1b/E1c ejecutada y precisar las puertas globales pendientes; seguimiento histórico [#6](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/6) y SQL Server [#7](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/7) | Parcialmente ejecutado; cierre pendiente |
| P2 | Compilar los fragmentos *Ilustrativo* | Registro por fragmento: compilador, prueba y veredicto; sin promover ejemplos sin ejecución | Inventario/sintaxis entregados; resultado nativo seleccionado registrado por separado |
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

El [registro del 3 de noviembre](EDITORIAL_CHECKPOINT_2026-11-03.es.md) concreta correcciones, fuentes, solapes muestreados y procedencia de PDF. No certifica toda la bibliografía ni la calidad idiomática integral.
