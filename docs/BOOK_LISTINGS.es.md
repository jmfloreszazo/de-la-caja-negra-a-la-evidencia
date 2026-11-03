# Inventario y alcance de validación de los listados

[English](BOOK_LISTINGS.md) · **Español**

El [inventario verificable](../evidence/editorial/book-listings.json) registra los 32 bloques de cada edición con ubicación, SHA256, etiqueta y dependencias pendientes. Los 27 bloques ejecutables/de configuración deben ser idénticos y estar en inglés en ES y EN. Los otros cinco contienen topología narrativa, salidas registradas o una plantilla de evidencia; su prosa puede traducirse.

Se han alineado 17 bloques que conservaban comentarios o descripciones traducidos. No se altera el código financiero del laboratorio ni los oráculos protegidos. Corregir el idioma del ejemplo no genera un resultado experimental nuevo.

## Comprobaciones y límites

| Tipo | Qué se comprueba | Qué no demuestra |
| --- | --- | --- |
| JSON | Cuatro documentos en tres bloques; 27.3 contiene dos registros separados | Veracidad de las observaciones o aprobaciones de ejemplo |
| YAML | Sintaxis de dos mapas | Esquema de mandato, autorización o ejecución del workflow |
| Bash | Sintaxis de ambos bloques mediante `bash -n` | Instalación, ejecución PowerShell o construcción del contenedor |
| SQLite/Python | Esquema exacto 28.1 y cuatro predicados 28.4; rechazan corrupción de saldo y apuntes | La suite financiera completa de siete invariantes |
| COBOL/C# seleccionados | CI compila el programa completo 26.1, idéntico al original, y compara 58 casos fijados; ejecuta cuatro expresiones de redondeo 12.2 y el decodificador 15.1 con nueve casos positivos y seis negativos | Integración de todos los fragmentos, producción o portabilidad universal; el primer resultado original queda pendiente hasta archivarse |
| Resto de COBOL/C#/T-SQL | Se identifican dependencias y contexto ausentes | No se inventan tipos ni stubs para afirmar que una aplicación completa compila |

No se promueven etiquetas por comprobar sintaxis o una función auxiliar aislada. Se conservan las etiquetas publicadas y el límite de integración completa. Las reproducciones reales Linux/macOS/Windows/WSL siguen pendientes en #11. El [detalle técnico](BOOK_LISTINGS.md) enumera los 32 bloques y sus comandos reproducibles.

Cada ejecución nativa conserva checkout exacto, run ID, hashes del código, versiones, los 58 resultados esperados/observados y las salidas originales del compilador y de ejecución, también ante fallo. Una prueba omitida o solo sintáctica no se cuenta como ejecución nativa satisfactoria.
