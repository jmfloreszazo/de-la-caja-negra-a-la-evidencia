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

El registro inglés conserva los hashes y la procedencia exacta. Hay que generar y revisar muestras de los PDF corregidos antes de dar por revisado visualmente este corte. Los PDF anteriores no se presentan como salida corregida. El [inventario de listados](BOOK_LISTINGS.es.md) detalla las pruebas y sus dependencias pendientes.

## Ejecución nativa y ajuste de impresión

El resultado original y su ZIP auditado están registrados en el [inventario](BOOK_LISTINGS.es.md): 58 casos COBOL, cuatro expresiones de redondeo y nueve valores/seis negativos COMP-3, sin promover la integración completa.

La primera vista previa corregida todavía divide bloques cortos al pie de página: la simulación del capítulo 24 empieza con solo dos líneas de salida. Se ajusta el estilo para conservar entero un listado cuando cabe en una página. Falta regenerar e inspeccionar ese cambio de impresión antes de aceptarlo.
