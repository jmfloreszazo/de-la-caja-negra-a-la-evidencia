# Contratos de plataforma: ubicación y alcance de evidencia

[English](PLATFORM_CONTRACTS_ADR.md). Sigue #17/#18/#28; este incremento acotado no cierra esos issues.

## Decisión

Ampliar el capítulo 1 con atribución por capas, traza de observación propuesta, diseños de assessment lectura/escritura y cuestionario para operador/DBA. Ampliar el capítulo 13 con tres contextos de plataforma y decisiones de patrones. Mantener capacidad/precios/WAN en el 25 bis, canales/dispositivo en su complementario y los cien riesgos en el anexo E. Enlazar esos desarrollos en lugar de duplicarlos. Añadir referencias primarias [51]–[59] y catálogo estructurado en inglés en `research/platform-contracts/`.

Se evita otro capítulo que repetiría la introducción de plataforma/capacidad. Ambas ediciones tienen secciones, tablas, referencias y navegación equivalentes. No cambia el número de capítulos numerados/complementarios ni los 47 diagramas por edición. Se regeneran las ediciones y comprueban vistas previas sin cambiar versión o release publicada.

## Límite de evidencia

Diez filas distinguen comportamiento documentado, ejecución nativa y migración verificada. El material IBM consultado mediante índice se marca así, incluido un HTTP 403 del lector directo. Las páginas MCP/ePortal se leyeron directamente. Las fechas de publicación quedan nulas cuando no se proporcionan; la versión documental no acredita soporte, disponibilidad o configuración instalada. Las fuentes se parafrasean, no se copian como manuales.

El validador ejecuta seis mutaciones negativas del catálogo. Comprueba atribución, metadatos fuente/versión, ausencia de fallo/oráculo e inflación de evidencia. No ejecuta ni emula IBM Z, z/OS, Db2 for z/OS, MCP u OS 2200; no se afirma comparación diferencial nativa ni aprobación productiva. Las cifras de cargas son diseños que se pueden preregistrar, no tasas ni niveles de servicio observados.

## Alcance pendiente de los issues principales

El issue #17 conserva investigación profunda de ejecución/memoria/I/O/Db2/datasets/seguridad/operación, diagramas solicitados, mediciones reales y revisión de especialistas. #18 conserva cobertura completa por fabricante/subsistema, controles ejecutables de brechas semánticas y evidencia de instalación. #28 conserva sus 236 entradas, quince matrices, diagramas y ejemplos ejecutables batch/offline/CDC/internacionales. El descubrimiento sigue NOT_VERIFIED. Datos desconocidos del cliente y pruebas de hardware externo quedan documentados para después; no bloquean integrar esta investigación acotada.

El roadmap refleja ahora #83/#84 y 47 figuras, y coloca contratos de plataforma antes de descomposición/canales/editorial/refactor/agentes pendientes. #16/#53 siguen congelados.

## Original de CI

La [ejecución 41721242997](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41721242997) pasó los seis controles de integridad del catálogo. El [ZIP original](../evidence/platform-contracts/catalog-integrity-original.zip) y su [procedencia](../evidence/platform-contracts/provenance.json) conservan rama fuente `9f6d20267e137ff8de3c1559e8c2dbdc433215fa` y checkout de prueba `32a2956826ffb0ec1c0e4f0629af5f444722570c` por separado. Se archiva el objeto de commit temporal para que el control no dependa de conservar una referencia efímera de GitHub. El auditor verifica identidad del objeto, parentesco, igualdad de árboles y tres hashes históricos. El resultado sigue limitado a metadatos; no valida comportamiento nativo de fabricantes.

## Revisión visual acotada

El [PDF de la ejecución 41722105250](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41722105250) tiene 160 páginas ES y 156 EN, con 47 diagramas más portada por edición. Se revisaron diez páginas del contenido ampliado. El [registro](../evidence/platform-contracts/pdf-review.json) conserva SHA-256 de ZIP/PDF, cien entradas de render y dos muestras. El checkout de prueba `5f1e96272c25048db9cf74fe48f19bafafffea81` y la fuente `22cd0f3d650623cdcbe6b59127be0725fa409498` tienen el mismo árbol. Se corrigieron formato de citas y espacios detectados en el primer lint; esta revisión no acredita revisión editorial completa ni ejecución nativa de plataformas.
