# Cierre final de investigación — 5 de noviembre de 2026

[English](FINAL_CLOSEOUT.md) · **Español**

> **Cerrar la edición no es obtener un PASS científico ni aprobar un despliegue.** Cerramos una edición acotada y reproducible del libro y laboratorio por decisión del autor. Toda validación incompleta o no ejecutada queda **excluida expresamente**, no se transforma en éxito.

## Qué entregamos

- Manuscrito completo en español e inglés con capítulos, anexos, diagramas, alternativas arquitectónicas y ediciones Markdown/PDF.
- Ejemplos y guías de laboratorio en inglés con GnuCOBOL, .NET 10, SQL y Podman; metodología de **sustitución brownfield orientada a capacidades**, sin exigir parser ni modernización 1:1.
- Resultados sintéticos observados de oráculos contables independientes, transacciones PostgreSQL/SQL Server, Orleans, coexistencia con legado y recuperación TCP local acotada.
- Investigación por fabricante de IBM Z/z/OS, Db2, CICS, IMS, VSAM, IBM i, Unisys y Fujitsu histórico, con brechas declaradas.
- Separación entre Golden Master observado, política funcional aprobada por un responsable, controles TODM/oráculo y autorización de producción.

## Decisión final sobre los experimentos

| Experimento | Cierre administrativo | Evidencia científica | Qué no se ha demostrado |
| --- | --- | --- | --- |
| **E1** PostgreSQL, SQL Server y .NET 10 | **CERRADO — investigación implementada y acotada** | CI original sobre bloqueos, deadlocks, write skew, invariantes, fallos, reintentos, concurrencia y paridad sintética | Equivalencia integral mainframe, durabilidad ante corte eléctrico, HA física, reglas bancarias aprobadas o capacidad productiva |
| **E2** Orleans/PostgreSQL | **CERRADO — campaña acotada, #8 ya cerrado** | `partially_verified`; conservar pruebas de varios procesos en un host, ledger, particiones y recuperación seleccionadas | Recuperación continua natural, hosts independientes, HA SQL o PASS global; [X00–X08](E2_FULL_PASS_PROTOCOL.es.md) se archiva como protocolo futuro |
| **E3** Azure/local/híbrido | **CERRADO — benchmark integral no ejecutado** | M1/M2, modelo WAN hipotético y precios de Azure fechados son insumos, no E3 | Carga mainframe aprobada, TPS/p99 y resiliencia comparables, DR y TCO completo; **no existe conversión demostrada de MIPS a vCPU** |
| **E4** agentes reales y Oracle Gates | **CERRADO — experimento E4 no ejecutado** | Patrones de gobernanza y oráculos/mutaciones ilustrados con laboratorio determinista | Campaña de agentes con modelo real, comparativa de defectos, coste del modelo y aceptación independiente |

**Importante:** `evidence/claims.json` conserva los estados científicos anteriores (`E1/E2: partially_verified`; `E3/E4: designed_not_executed`). El cierre de proyecto **no modifica** esas evidencias ni inventa ejecuciones.

## Límites editoriales y técnicos

| Área | Entregado | Fuera de esta edición |
| --- | --- | --- |
| Brownfield CAP-005/007, #58 | .NET/PostgreSQL durable, legado simulado, shadow, veto de rollback y pruebas acotadas de autoridad | Fencing real del sistema origen, reglas/Golden Master autenticados, efectos financieros externos y aprobación TODM G2/G6 |
| Canales, #30 | Fallos/reintentos TCP locales con oráculos SQL; protocolo de recepción H01/H02 | Campaña distribuida, ATM/switch/emisor bancario, efectivo físico, ISO 8583, CICS/Db2 y stand-in delegado |
| Fabricantes y patrones, #17/#18/#28 | Catálogo con fuentes y propuesta de sustitución semántica | Matrices exhaustivas, motores de fabricante instalados, 236 comportamientos completos y aprobación del cliente |
| Laboratorio, #11/#15 | Código y evidencias históricas reproducibles con los entornos de CI identificados | Reproducción nativa integral en macOS/Windows, compilación contextual de todos los listados y refactor masivo del árbol |

Los issues de investigación y mantenimiento activos se pueden cerrar como **no previstos en esta edición** tras publicar, sin afirmar que todas sus casillas se hayan satisfecho. Los asuntos **#16 protección de main** y **#53 Clean Rooms/confidential computing** permanecen congelados por decisión anterior; no se reactivan.

## Condiciones de publicación

1. Validar en el SHA exacto del PR de cierre los workflows aplicables, incluidos libro, evidencias y vista previa PDF.
2. Fusionar a `main` sin reescribir evidencias ni etiquetas anteriores.
3. Crear la release de archivo `v2026.11.05` con **ambos PDF ES/EN** y ambos Markdown completos. Las cubiertas e interiores mantienen el identificador editorial histórico **v2026.10.29**; la etiqueta nueva señala la **congelación final del repositorio de investigación**, no una segunda edición rediseñada.
4. Comprobar que GitHub haya publicado de verdad los cuatro archivos. CI correcta no equivale a revisión lingüística completa ni a auditoría visual página por página.
5. Cerrar después los issues activos fuera de alcance como `not planned`, manteniendo pruebas fallidas y procedimientos externos.

**Situación posterior:** el proyecto queda sin desarrollo planificado en esta edición. Toda reapertura exigirá alcance, versión, infraestructura, carga, responsable, oráculos independientes y aprobación explícita nuevos. El libro demuestra un método de investigación verificable, no la paridad con un mainframe real.
