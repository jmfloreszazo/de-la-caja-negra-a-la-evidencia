# Inventario y alcance de validación de los listados

[English](BOOK_LISTINGS.md) · **Español**

El [inventario verificable](../evidence/editorial/book-listings.json) registra los 39 bloques de cada edición con ubicación, SHA256, etiqueta y dependencias pendientes. Los 34 bloques ejecutables/de configuración deben ser idénticos y estar en inglés en ES y EN. Los otros cinco contienen topología narrativa, salidas registradas o una plantilla de evidencia; su prosa puede traducirse.

Se han alineado 17 bloques que conservaban comentarios o descripciones traducidos. No se altera el código financiero del laboratorio ni los oráculos protegidos. Corregir el idioma del ejemplo no genera un resultado experimental nuevo.

## Comprobaciones y límites

| Tipo | Qué se comprueba | Qué no demuestra |
| --- | --- | --- |
| JSON | Seis documentos en cinco bloques; 27.3 contiene dos registros separados y 25a.3–25a.4 son respuestas fechadas de Azure CLI | Veracidad de las observaciones o aprobaciones de ejemplo |
| YAML | Sintaxis de dos mapas | Esquema de mandato, autorización o ejecución del workflow |
| Bash | Sintaxis de los siete bloques mediante `bash -n`; 10a.1–10a.3 reproducen ejemplos sintéticos locales y 10a.4/25a.2 usan rutas de salida ilustrativas, no invocaciones históricas exactas | Instalación, ejecución PowerShell o construcción del contenedor |
| SQLite/Python | Esquema exacto 28.1 y cuatro predicados 28.4; rechazan corrupción de saldo y apuntes | La suite financiera completa de siete invariantes |
| COBOL/C# seleccionados | CI compila el programa completo 26.1, idéntico al original, y compara 58 casos fijados; ejecuta cuatro expresiones de redondeo 12.2 y el decodificador 15.1 con nueve casos positivos y seis negativos | Integración de todos los fragmentos, producción o portabilidad universal; el resultado original y su auditoría independiente se registran abajo |
| Resto de COBOL/C#/T-SQL | Se identifican dependencias y contexto ausentes | No se inventan tipos ni stubs para afirmar que una aplicación completa compila |

No se promueven etiquetas por comprobar sintaxis o una función auxiliar aislada. Se conservan las etiquetas publicadas y el límite de integración completa. Las reproducciones reales Linux/macOS/Windows/WSL siguen pendientes en #11. El [detalle técnico](BOOK_LISTINGS.md) enumera los 39 bloques y sus comandos reproducibles.

Cada ejecución nativa conserva checkout exacto, run ID, hashes del código, versiones, los 58 resultados esperados/observados y las salidas originales del compilador y de ejecución, también ante fallo. Una prueba omitida o solo sintáctica no se cuenta como ejecución nativa satisfactoria.

## Observación nativa original

La ejecución [41680741456](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41680741456), código exacto `e8785e0a5c565e3b006c3d23feebc888130dce3b`, pasó. Se conservan ZIP y resumen sin modificar bajo `evidence/editorial/`; SHA256 del ZIP `9bff18d5ae6f44bcef890277d3afaa04bf98356f1eec04cb79b2e55b669f8cfa`. La auditoría independiente comprueba 43 hashes de código, las 58 salidas COBOL y el resultado C# original. Versiones: SDK .NET 10.0.403, GnuCOBOL 3.1.2.0 y Python 3.12.16, en Linux de CI. No acredita las demás plataformas ni la integración completa.
