# Revisión editorial acotada — 3 de noviembre de 2026

[English](EDITORIAL_CHECKPOINT_2026-11-03.md) · **Español**

La base revisada es main `3e0a949976391e0711795e8302afb63cb65bc045`. Es una revisión técnica/editorial acotada, no certificación idiomática integral ni autorización de publicación.

## Corregido

- Diecisiete bloques de código/configuración conservaban comentarios o valores traducidos. Ahora los 27 bloques ejecutables/de configuración son idénticos y están en inglés en ambas ediciones. La comprobación de idioma exige esa igualdad; los diagramas narrativos y las plantillas siguen traducibles.
- El capítulo 24 atribuía únicamente al runtime la comparación de Foundry. El artículo compara stacks completos, incluidos SDK y serialización, con una petición en vuelo y poca carga. Se corrige el alcance en ES/EN: no mide saturación ni throughput máximo.
- Se sustituye la etiqueta ambigua «Ejecutado en diseño» del anexo A por comandos de reproducción con requisitos. Se añaden etiquetas A.2 y 25a.1 y un inventario de los 32 bloques.
- Las convenciones distinguen comprobación sintáctica, prueba auxiliar y aceptación de una integración completa. No se cambian el código financiero, los oráculos protegidos ni los originales experimentales.

## Fuentes y solapes

[45] se ha contrastado con los apartados de metodología y alcance del artículo original; [44] respalda la analogía de estado de sesión controlado por el host, no la autoridad de aprobación bancaria. Las páginas primarias [1]/[41] no estaban disponibles mediante el lector de investigación: no se declaran revalidadas ni se concluye que sus enlaces estén rotos. El [registro técnico](EDITORIAL_CHECKPOINT_2026-11-03.md) identifica enlaces, pasajes y límites.

| Pasajes revisados | Diferencia que justifica conservarlos |
| --- | --- |
| Capítulos 3, 17 y 28: transferencias y locks | Traducción que pierde la reserva, propuesta T-SQL y laboratorio SQLite ejecutado son criterios distintos |
| Capítulos 10, 11 y 27: oráculos | Semántica/ataques al evaluador, responsabilidades del pipeline y mutación real de igualdad incorrecta |
| Capítulos 9 y 31: autoridad | Mandato de negocio y vinculación de evidencias durante la revisión |
| Capítulos 24 y 28: capacidad | Diseño experimental y observaciones locales con límites explícitos |

No se propone un recorte porcentual ni se afirma haber revisado cada frase. Siguen pendientes la revisión idiomática especializada, la bibliografía completa y una matriz de solapes de todo el libro.

## PDF

Se verificó por SHA256 el artefacto original 13240919909 de la ejecución 41660337335, código `7a74a9f1cdc781b348d681fb7795202c064b68ad`: ES, 144 páginas; EN, 141. El código del libro no cambió entre esa ejecución y la base main revisada. La inspección visual muestreada comprende índice EN página 2, continuación de tabla EN 106, benchmark ES 78 y tabla de validación externa ES 108. En esas muestras no se observa recorte ni texto ilegible y la tabla conserva su cabecera al continuar. No acredita todas las páginas.

El registro inglés conserva los hashes y la procedencia exacta. La revisión de los PDF corregidos se registra abajo; los PDF de referencia no se usan para aprobar esa salida nueva. El [inventario de listados](BOOK_LISTINGS.es.md) detalla las pruebas y sus dependencias pendientes.

## Ejecución nativa y ajuste de impresión

El resultado original y su ZIP auditado están registrados en el [inventario](BOOK_LISTINGS.es.md): 58 casos COBOL, cuatro expresiones de redondeo y nueve valores/seis negativos COMP-3, sin promover la integración completa.

La primera vista previa corregida todavía divide bloques cortos al pie de página: la simulación del capítulo 24 empieza con solo dos líneas de salida. Se ajusta el estilo para conservar entero un listado cuando cabe en una página. La regeneración y la inspección aceptadas se registran abajo.

La primera maquetación de bloques completos redujo los fragmentos de código de EN 48 / ES 45 a 32 por edición, pero dejó una etiqueta sola al pie de la página del capítulo 24. Se añade una vinculación de impresión entre cada una de las 32 etiquetas y su bloque inmediato; la inspección completada se registra abajo. No se elimina código ni prosa.

La revisión visual detectó además dos pies ingleses que aún describían una serie azul. El tema común usa `#9AA0A6` (gris) para la segunda serie y sustituye las paletas locales. Se alinean pies/textos alternativos de las figuras 24.1 y 28.3 e índices de diagramas en ES/EN. No cambian imágenes, datos de simulación ni código financiero protegido.

## Corte de impresión corregido

Se descargó y verificó el original de la ejecución [41683984327](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41683984327), código `e5275e93a03a3c9e0cc74e29b847fa63cec9e588`, artefacto 13255081028. SHA256 del ZIP: `dfa5ed7791a5e9acddbfbfd89363e051c1916899c086670927e2485729c45329`. El [registro verificable](../evidence/editorial/pdf-layout-review.json) conserva hashes de PDF/entradas, posiciones de código/títulos y páginas muestreadas.

| Edición | Páginas | Fragmentos de código antes/después | Títulos con su código | Páginas inspeccionadas visualmente |
| --- | --- | --- | --- | --- |
| ES | 146 | 45 / 32 | 32 / 32 | 4, 40, 48, 79, 80 |
| EN | 142 | 48 / 32 | 32 / 32 | 4, 38, 46, 77, 78 |

Cada edición tiene 32 bloques lógicos. Tras el ajuste, cada uno ocupa una caja completa dentro de los márgenes y conserva el título en la misma página. Las diez páginas inspeccionadas permiten comprobar legibilidad de código/tablas/figuras, alcance corregido del benchmark, código inglés en la edición española y pies que describen la serie gris real. No se observa recorte ni texto ilegible en esas muestras. No acredita cada párrafo, referencia ni la calidad idiomática integral.

Se conservan capturas: [decodificador ES](../evidence/editorial/pdf-layout-es-code.png), [decodificador EN](../evidence/editorial/pdf-layout-en-code.png), [simulación ES](../evidence/editorial/pdf-layout-es-simulation.png), [simulación EN](../evidence/editorial/pdf-layout-en-simulation.png). El artefacto PDF completo tiene retención limitada de CI; permanecen registrados su SHA y las identidades exactas de código/entradas. Los commits posteriores solo documentales no cambian las entradas de render revisadas.

Siguen pendientes revisión especializada de inglés, fuentes [1]/[41] no revalidadas, solapes de todo el libro y pulido de la portada interna para impresión (el PDF aún hereda la nota de lectura del fichero fuente). Este corte no los declara terminados. La checklist de plataformas/EBCDIC/integración contextual de #11 permanece abierta. No cambia versión, release ni código financiero protegido.
