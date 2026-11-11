# De la caja negra a la evidencia

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/icon-b-dark.svg">
    <img src="assets/mark.svg" alt="Icono variante B: caja negra, puerta de verificación y rastro rojo de evidencia" width="150">
  </picture>
</p>

[English](README.md) · **Español**

**Modernizar COBOL más allá de la traducción: agentes de IA, patrones de arquitectura, transacciones y oráculos verificables.**

> **Edición del libro e investigación cerrada el 5 de noviembre de 2026.** [Acta final y veredictos experimentales](docs/FINAL_CLOSEOUT.es.md) · [Notas de la release de archivo](docs/releases/v2026.11.05.md). La nueva etiqueta identifica el snapshot final; las cubiertas conservan el identificador histórico de primera edición. E1/E2 quedan parcialmente verificados. **Estado posterior al cierre (8 de noviembre de 2026):** E3 y E4 se ejecutaron como *demostraciones acotadas en una sola VM de Azure* —un ensayo exploratorio de ledger con carga abierta y la reproducción aislada de una respuesta real de un modelo— registradas en [`evidence/runs/azure-e1-e4-2026-11-08.json`](evidence/runs/azure-e1-e4-2026-11-08.json) y validadas con el [adaptador TODM](evidence/runs/todm-azure-2026-11-08.json). Siguen **sin aceptarse** como estudios E3/E4: sin contrato de capacidad aprobado, sin comparación con mainframe, sin población comparativa de agentes, entrega `BLOCK`.

José María Flores Zazo · [jmfloreszazo.com](https://jmfloreszazo.com) · Edición v2026.10.29

**Última edición editorial (11 de noviembre de 2026):** [v2026.11.11 — PDF y Markdown en español e inglés](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.11.11). Las cubiertas conservan el identificador histórico de primera edición; las [notas de publicación](docs/releases/v2026.11.11.md) explican el contenido revisado.

> [!IMPORTANT]
> La IA puede investigar, proponer y construir. Aceptar el resultado exige contratos, oráculos independientes y una autoridad explícita. Una modernización 1:1 puede ser un puente, pero nunca deberíamos confundir el puente con la ciudad a la que queremos llegar.

Un libro abierto y un laboratorio ejecutable sobre cómo modernizar sistemas COBOL sin apostar el negocio a una equivalencia que no sabemos demostrar: qué conservar, qué patrón sustituye cada garantía del mainframe, cómo usar agentes de IA sin regalarles autoridad y cómo acercarse a la capacidad de un mainframe en Azure o en infraestructura propia. Está en abierto porque un libro que defiende la evidencia no puede pedir que se le crea por fe.

**Snapshot de investigación publicado: 5 de noviembre de 2026.** La release de archivo incluye ambos PDF y ambas ediciones Markdown en una página. Los archivos publicados congelan su etiqueta; las correcciones posteriores del código fuente no modifican esos archivos.

## Incorporaciones locales actuales

El [mapa del proyecto](docs/PROJECT_STRUCTURE.md) separa fuentes editables del
libro, laboratorios, evidencia observada y entregables generados. La edición
de trabajo añade [herramientas TODM, modelos y ADR](book/es/parte-3-oraculos/10a-herramientas-todm-modelos-y-adrs.md),
[salidas reales del CLI Azure](evidence/runs/azure-cli-2026-11-08/capture.json),
[demostraciones E1–E4 en Azure](evidence/runs/azure-e1-e4-2026-11-08.json) y un
[anexo sobre otros lenguajes](book/es/anexos/anexo-h-mas-alla-de-cobol.md).
No modifica archivos de releases históricas ni concede aceptación productiva.
Las herramientas usan perfiles JSON acotados, no motores BPMN/DMN completos.

## Leer

[Descargar PDF en español e inglés — archivo v2026.11.05](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.11.05) · [Prepublicación histórica v2026.10.31-rc1](docs/releases/v2026.10.31-rc1.md) · [Ruta rápida: siete capítulos](docs/READING_PATH.es.md) · [Ediciones PDF y proceso de publicación](docs/PDF.md).

| | Capítulo a capítulo | El libro entero en una página |
|---|---|---|
| Español (original) | [book/es](book/es/README.md) | [book/es.md](book/es.md) |
| English | [book/en](book/en/README.md) | [book/en.md](book/en.md) |

37 capítulos numerados más los complementarios 7 bis, 10 bis, 21 bis y 25 bis en siete partes, epílogo, nueve anexos (A–I) y 48 diagramas por idioma (C4, UML de secuencia, estados y clases, ER, diagrama de flujo, gitGraph), escritos en Mermaid y publicados como imágenes con el estilo visual del libro. Las dos ediciones tienen exactamente la misma estructura y la CI falla si se separan; el [catálogo de diagramas](book/es/diagramas.md) es el inventario contra el que se comprueba el PDF.

## Idiomas: libro frente a código

**El libro siempre se mantiene completo en español e inglés. Todos los proyectos ejecutables y sus README, código, comentarios, pruebas, logs y CI están exclusivamente en inglés.** Incluso los fragmentos de código incluidos en la edición española permanecen en inglés. [Política de idiomas](docs/LANGUAGE_POLICY.md).

## Ruta rápida y evidencia

[**Capítulo 25 bis: infraestructura local, Azure y latencia de oficinas bancarias**](book/es/parte-5-capacidad/25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md) · [Evidencia E1a/E1b con JSON de CI](evidence/runs/README.es.md) · [Protocolo WAN E3](docs/NETWORK_PROTOCOL.es.md).

[**Matriz de evidencia verificable**](docs/EVIDENCE.es.md): CI real, E1 y E2 parcialmente verificados, incrementos brownfield ejecutados, y E3/E4 ejecutados solo como demostraciones acotadas en Azure (no experimentos aceptados).

¿Quieres recorrer el argumento sin leer todos los capítulos de forma lineal? Sigue la [ruta de siete capítulos](docs/READING_PATH.es.md). El [registro editorial y de evidencias](docs/EDITORIAL_REVIEW.es.md) distingue lo comprobado de lo todavía hipotético.

La [CI del laboratorio](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40900252152) ya ha ejecutado las pruebas offline, nativas y Podman en runners Linux. Esto no acredita todas las plataformas ni la aceptación global de E1–E4. La PR #5 ya está fusionada. E1 PostgreSQL/SQL Server y E2 Orleans tienen evidencias sintéticas parciales; E3/E4 cuentan con demostraciones acotadas posteriores al cierre, no con una ejecución completa aceptada. El [roadmap actual](ROADMAP.es.md) y la [matriz de evidencia](docs/EVIDENCE.es.md) separan los resultados históricos, los incrementos brownfield y los gates pendientes.

## Ejecutar el laboratorio

```bash
cd lab
python3 tools/verify_offline.py        # Python-only anchor, independent policy, and accounting oracle
bash scripts/run-podman.sh --auto      # Full COBOL, .NET 10, gate, and transfer checks offline
```

El laboratorio está en inglés. La guía en español es el [anexo A del libro](book/es/anexos/anexo-a-un-laboratorio-que-pueda-contradecirnos.md).

## Estructura del repositorio

```text
README.md · README.es.md      bilingual repository entrypoints
ROADMAP.md · ROADMAP.es.md    bilingual open roadmaps
book/
  es/  en/                    chapter-by-chapter source books
  es.md  en.md                single-page generated books (scripts/build.py)
  figures/                    diagram sources and rendered artwork
lab/                          GnuCOBOL · .NET 10 · SQLite · Python · Podman
scripts/                      build.py · check.py · render_figures.py · setup_github.sh
assets/                       brand mark, covers, and social preview
docs/LAUNCH.md                release preparation instructions
.github/                      templates, CODEOWNERS, and workflows
```

El resto de documentos del proyecto (guía de colaboración, gobernanza, código de conducta) está en inglés, para que cualquiera pueda participar.

## Reproducir por alcance

Empieza desde la raíz del repositorio con Python 3.12 o posterior y Git. En Windows, utiliza `python` si `python3` no está disponible. Conserva los bytes canónicos del checkout siguiendo las [instrucciones de integridad](CONTRIBUTING.md#checkout-integrity); un estado limpio no detecta por sí solo la conversión a CRLF en clones antiguos.

**Estructura del libro y evidencia conservada (sin compilador, contenedor ni nube):**

```bash
git rev-parse HEAD
git status --short
python3 --version
python3 scripts/check_language_policy.py
python3 scripts/check.py
python3 scripts/check_evidence.py
python3 lab/tools/verify_offline.py
```

Los resultados esperados son `LANGUAGE POLICY: PASS`, `CHECK: PASS`, `EVIDENCE CHECK: PASS` y `VERIFY: PASS`. Registra cada comando y su código de salida; detente si falla. Estas comprobaciones auditan material versionado y resultados SQLite históricos. **No** ejecutan COBOL/.NET ni validan ejecuciones remotas de CI.

| Qué reproducir | Procedimiento | Límite |
|---|---|---|
| Libros en una página | `python3 scripts/build.py` y después `python3 scripts/check.py` | Regenera ambos idiomas a partir de los capítulos fuente |
| Markdown y renderizado de diagramas | Node.js 22; `npx --yes markdownlint-cli2@0.22.0 "**/*.md"`; Mermaid CLI 11.12.0 y `python3 scripts/render_figures.py --check` | Comprobaciones de sintaxis y renderizado; sigue la [guía de colaboración](CONTRIBUTING.md#diagram-rules) para actualizar imágenes de forma intencionada |
| Ediciones PDF | [Instrucciones de generación del PDF](docs/PDF.md) | Requiere dependencias Linux y fuentes; no implica una publicación ni una construcción idéntica byte a byte |
| Recorrido COBOL/.NET/SQLite nuevo | [Protocolo de reproducción por host](lab/docs/HOST_REPRODUCTION.md) | Registra host, imagen, resultados crudos y auditoría independiente; requiere Podman |
| Laboratorios ampliados de SQL, Orleans y canales | [Matriz de evidencia](docs/EVIDENCE.es.md) y procedimientos de los proyectos enlazados | Dependencias y alcances de aceptación separados; no forman parte del recorrido básico |

Conserva el commit, las versiones de las herramientas, los logs crudos, los fallos y el oráculo independiente de cada nueva ejecución. E1/E2 están parcialmente verificados; E3/E4 no son estudios de aceptación completados. Ni una comprobación del código fuente ni una prueba local básica demuestran rendimiento en Azure o mainframe.

## Colaborar

La guía es [CONTRIBUTING.md](CONTRIBUTING.md) (en inglés): caminos por perfil, una primera contribución en 15 minutos y las reglas que mantienen sincronizados los dos idiomas. Las preguntas van a [Discussions](../../discussions), en español o en inglés, y el trabajo abierto está en la [hoja de ruta](ROADMAP.es.md).

1. **Evidencia antes que opinión.** Una afirmación trae fuente, experimento o la palabra «propuesta».
2. **Lo que no sabemos también se escribe.** Un `INCONCLUSIVE` honesto vale más que un `PASS` inventado.
3. **Pasos pequeños y reversibles.** Una idea por pull request, en los dos idiomas.
4. **Nadie aprueba su propio oráculo.** Los contratos y el gate del laboratorio tienen revisores obligatorios.

## Estado de aceptación E2

La [campaña E2 acotada está cerrada](docs/E2_CLOSEOUT.es.md), pero **E2 no tiene un PASS científico global**. Para obtenerlo haría falta una nueva campaña con recursos distribuidos reales y un contrato aprobado: [protocolo completo E2 Full PASS (ES)](docs/E2_FULL_PASS_PROTOCOL.es.md) · [EN](docs/E2_FULL_PASS_PROTOCOL.md). Requiere probar X00–X08, incluir fallos físicos y SQL HA, registrar métricas crudas y obtener auditoría independiente. **No se reactiva E2 como tarea activa.**

## Autoridad del origen en una migración brownfield

El [protocolo de fencing y aceptación CAP-005/007](docs/BROWNFIELD_SOURCE_FENCE.es.md) ([EN](docs/BROWNFIELD_SOURCE_FENCE.md)) y el [inventario bloqueante](lab/brownfield/owner_readiness/README.md) especifican qué rutas de escritura del legacy y efectos externos deben estar demostrados antes de cualquier corte. La herramienta solo valida estructura, **no** comprueba el fencing en CICS/IMS/Db2 ni concede aprobación TODM G2/G6.

## Assessment CDC de plataformas originales y aceptación del cliente (#58)

La investigación [ES](docs/research/source-native-capture-assessment.es.md) / [EN](docs/research/source-native-capture-assessment.en.md) y el [gate ejecutable (en inglés)](lab/brownfield/source_capture/README.md) diferencian Db2 z/OS, VSAM CICS, batch no-RLS, IMS online/DL-I, journals IBM i y mecanismos Fujitsu/otros **sin verificar**. Son **posibilidades documentadas**, no CDC probado en cliente. Las siete rutas parten de UNKNOWN; TODM G2/G6 siguen INCONCLUSIVE/BLOCK.

## Arquitectura y patrones por fabricante (investigación #17/#18/#28)

Los capítulos 1 y 13 incorporan ahora una [comparación de contratos de IBM Z, IBM i, Unisys MCP/OS 2200 y Fujitsu GS21](docs/research/vendor-runtime-contracts.es.md) ([EN](docs/research/vendor-runtime-contracts.en.md)). El [catálogo de 11 contratos/descubrimientos](research/vendor-runtime-contracts/catalog.json) enlaza diez referencias originales con riesgos, patrones sustitutos, brechas y oráculos negativos. NEC ACOS y Bull GCOS permanecen **desconocidos**, nunca presuntamente equivalentes; las 25 pruebas automáticas verifican **solo la integridad de estos metadatos**, no ejecuciones de fabricantes ni aprobación bancaria.

## Continuidad entre snapshot y journal: oráculo sintético independiente

El método [ES](docs/research/source-capture-handoff.es.md) / [EN](docs/research/source-capture-handoff.en.md) añade un **oráculo offline de continuidad de snapshot y eventos**, con 26 controles positivos y negativos. Reutiliza el catálogo de fabricantes como clasificación, pero **no ejecuta CDC nativo** ni autoriza el corte bancario.

## Recuperación concurrente con una respuesta TCP antigua retenida (#30)

El [dossier ES](docs/research/channel-held-ack.es.md) ([EN](docs/research/channel-held-ack.en.md)) prueba **ocho reintentos HTTP concurrentes** del mismo ID mientras el proxy TCP retiene la respuesta anterior, ya confirmada en PostgreSQL. Una petición con importe distinto debe generar `ID_CONFLICT`. El oráculo SQL exige un único efecto antes de liberar el ACK viejo. Es una prueba **local y ficticia**, no una red bancaria ni una aceptación de producción.

## Caídas TCP reales en loopback y recuperación del COMMIT (#30)

La [investigación ES](docs/research/channel-loopback-transport.es.md) ([EN](docs/research/channel-loopback-transport.en.md)) incorpora tres pruebas **reales de reset/timeout TCP en localhost**, ejecutadas alrededor de .NET 10 y dos bases PostgreSQL desechables. Un oráculo SQL independiente contrasta el COMMIT, dos asientos, el outbox y la idempotencia del ID original. **No son particiones WAN físicas ni equipos bancarios.**

## Particiones y respuestas perdidas por salto de canal (#30)

El [análisis ES de fallos de ATM↔switch↔core](docs/research/channel-hop-failures.es.md) ([EN](docs/research/channel-hop-failures.en.md)) añade siete trazas ficticias con cuarenta controles adversariales de autoridad, expiración de respuesta, consulta del COMMIT y mensajes tardíos tras cambio de escritor. Son simulaciones lógicas; **no se han cortado enlaces TCP reales**, ni se concede autoridad de dispensación o contabilización.

## Incertidumbre de red en canales ATM (#30)

La investigación [ES](docs/research/channel-late-advice.es.md) / [EN](docs/research/channel-late-advice.en.md) añade un control forense *sintético* para advices tardíos y duplicados, efectivo parcial, reversos y rechazo stand-in sin delegación del emisor. El [laboratorio en inglés](lab/channels/README.md) complementa la campaña .NET 10/PostgreSQL anterior; **no** demuestra protocolos homologados ni autoridad bancaria.

## W01: journal transaccional del origen, en entorno sintético

El [laboratorio de journal incremental](lab/brownfield/w01_feed/README.md) y la investigación [ES](docs/research/w01-source-journal.es.md) / [EN](docs/research/w01-source-journal.en.md) prueban secuencia confirmada en origen, captura MVCC, replay, rechazo de huecos/corrupción y cursor atómico en dos PostgreSQL. **No** es CDC productivo, fencing de mainframe, lectura linealizable ni aceptación bancaria. La proyección anterior se mantiene independiente.

## W01: seguridad de lectura impuesta por PostgreSQL

La investigación [ES](docs/research/w01-reader-identity.es.md) / [EN](docs/research/w01-reader-identity.en.md) distingue una transacción SQL `READ ONLY` de una **identidad SQL con permisos exclusivamente de lectura**. Los controles negativos rechazan escrituras al origen, credenciales privilegiadas y destinos de reset no autorizados. No equivale al fencing del mainframe real.

## W01: proyección PostgreSQL de lectura de saldos

El [laboratorio acotado W01](lab/brownfield/w01_projection/README.md) y la investigación [ES](docs/research/w01-projection.es.md) / [EN](docs/research/w01-projection.en.md) estudian la proyección no autoritativa con watermark atómico, fallback al origen y rechazo de datos obsoletos o corruptos. No se afirma CDC, linealizabilidad, saldo disponible, aprobación bancaria ni fencing real.

## Oleadas funcionales de modernización brownfield

Los protocolos [ES](docs/research/mainframe-extraction-waves.es.md) / [EN](docs/research/mainframe-extraction-waves.en.md) y el [oráculo de oleadas](lab/decomposition/wave_gate.py) conectan capacidades del negocio con decisiones de extracción refutables sin parser COBOL. Las 30 capacidades continúan siendo hipótesis y ninguna candidata queda autorizada para producción.

## Más del autor

El libro se apoya en este trabajo:

- [TODM — Test Oracle-Driven Methodology](https://github.com/jmfloreszazo/TODM) — la metodología detrás de los oráculos y gates del libro
- [Más allá del hype: ver un vídeo en YouTube está muy bien, pero la realidad es otra](https://jmfloreszazo.com/mas-alla-del-hype-ver-un-video-en-youtube-esta-muy-bien-pero-la-realidad-es-otra/) — REA, agentes e ingeniería inversa con evidencia
- [De Leviatán al Autopilot](https://jmfloreszazo.com/de-leviatan-al-autopilot/) — gobernar agentes autónomos: autoridad frente a capacidad
- [Agentes al vuelo frente a un harness gobernado](https://jmfloreszazo.com/agentes-al-vuelo-frente-a-un-harness-gobernado/) — detección de defectos, QA, QC y el coste de medir
- [Del modelo que responde al agente que trabaja: Agent Harness y CodeAct con C#](https://jmfloreszazo.com/del-modelo-que-responde-al-agente-que-trabaja-agent-harness-y-codeact-con-c/) — un harness gobernado en C# y .NET 10
- [Auditar agentes de Copilot en VS Code: git es la única versión que importa](https://jmfloreszazo.com/auditar-agentes-de-copilot-en-vs-code-git-es-la-unica-version-que-importa-y-auditar-no-es-lo-mismo-que-prevenir/) — auditar no es lo mismo que prevenir
- [Agent Host Protocol (AHP): por qué el host, y no tu editor, es el dueño del estado de la sesión](https://jmfloreszazo.com/agent-host-protocol-ahp-por-que-el-host-y-no-tu-editor-es-el-dueno-del-estado-de-la-sesion/) — quién es dueño del estado de la sesión
- [MCP, A2A y AHP: tres protocolos y por qué tu agente debería vivir en un contenedor](https://jmfloreszazo.com/mcp-a2a-y-ahp-tres-protocolos-y-por-que-tu-agente-deberia-vivir-en-un-contenedor/) — tres protocolos, tres capas
- [Benchmark: dos Hosted Agents, mismo Foundry, .NET 10 LTS vs Python 3.12](https://jmfloreszazo.com/benchmark-dos-hosted-agents-mismo-foundry-net-10-lts-vs-python-3-12/) — un benchmark que solo cambia una cosa

## Licencia y cita

Texto y diagramas: CC BY-SA 4.0 · Código: MIT · Ver [LICENSE.md](LICENSE.md). Para citar, [CITATION.cff](CITATION.cff).
