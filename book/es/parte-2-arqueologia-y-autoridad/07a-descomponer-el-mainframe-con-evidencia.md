# Capítulo complementario · Descomponer el mainframe con evidencia

> **Borrador para revisión editorial.** No forma parte de la edición publicada v2026.10.29. Investigación vinculada al issue #32.

## La frontera no está en el programa

La modernización de un núcleo bancario no empieza distribuyendo párrafos COBOL entre contenedores. Debemos reconstruir la **unidad de responsabilidad empresarial**, su autoridad sobre los datos, sus dependencias temporales y el contrato transaccional realmente exigido. Un `CALL` identifica una relación técnica, no necesariamente un bounded context. Una tabla compartida no demuestra por sí sola que debamos conservarla: puede ocultar una lectura histórica, una función contable o un control de autorización.

## Método de descubrimiento

**Event Storming** facilita reconstruir qué ocurrió, quién tomó decisiones y qué excepciones importan, desde una retirada en cajero hasta una reversión al cierre del día. No equivale a **Event Sourcing**: descubrir eventos no obliga a almacenar cada cambio de estado mediante un registro de eventos.

El **DDD estratégico** identifica subdominios y contextos delimitados. Su hipótesis debe confrontarse con evidencia estática (COBOL, CICS LINK/XCTL, copybooks, SQL, JCL, Db2, VSAM y MQ), trazas de ejecución autorizadas y prácticas operativas (cierre contable, proceso nocturno, conciliación y picos). No conocemos una dependencia sólo porque un analizador no la observe.

## El ejemplo de una transferencia

Imaginemos una operación cuyo identificador gobierna dos apuntes compensados, un registro de operación y un mensaje de outbox en una única transacción duradera. Si extraemos la escritura de la cuenta a un servicio y mantenemos el segundo apunte en el mainframe sin un nuevo contrato verificable, hemos cambiado la semántica del negocio. Un actor virtual o una saga no reproduce automáticamente el mismo COMMIT.

En cambio, una proyección de movimientos puede ser una primera candidata si dispone de límites explícitos: idempotencia, marca de actualización, reconstrucción, tolerancia al retraso, seguridad y lectura alternativa consistente. El dato de un extracto eventualmente consistente nunca debe confundirse con el saldo autorizado para dispensar efectivo.

## El gate que puede decir que no

En el laboratorio sintético `lab/decomposition/`, el analizador conserva la procedencia de cada dependencia: fuente estática, traza de ejecución o afirmación del experto. Si dos fuentes discrepan sobre el carácter atómico de una relación, no se elige la versión conveniente: el corte se rechaza. Los miembros de una misma transacción se tratan como un grupo indivisible, aunque no estén unidos por una sola arista del grafo. También se rechazan cortes que cruzan dependencias desconocidas o inferidas.

El resultado `CANDIDATE_ONLY` **no autoriza una migración**. Sólo indica que esa propuesta no contradice las restricciones conocidas en el pequeño modelo sintético. Para convertirlo en decisión real faltan observaciones representativas, responsables del dominio, pruebas negativas y recuperación, rendimiento, costes con fecha y planes de reversión.

## Cinco decisiones posibles

Conservar el núcleo es una decisión legítima si todavía concentra invariantes que no sabemos reproducir. Encapsular mediante API y Anti-Corruption Layer permite mover la frontera sin mover la autoridad. Extraer consultas facilita medir la consistencia. Extraer comandos exige demostrar ownership, atomicidad o una nueva semántica de compensación expresamente autorizada. Retirar un activo requiere probar que nadie lo ejecuta, incluidos jobs estacionales, terminales remotos y recuperación operativa.

**La regla central:** primero demostrar la frontera de responsabilidad; después escoger la topología. La propuesta se invalida cuando una evidencia nueva contradice la hipótesis, no cuando el diagrama ya está dibujado.

## Contrato de evidencia

Este capítulo es una explicación de método apoyada por un **modelo sintético**, no por trazas de un banco, mediciones IBM Z ni aceptación productiva. Las pruebas del laboratorio sólo examinan decisiones estructurales. Véase [investigación detallada](../../../docs/research/mainframe-decomposition.es.md) y [laboratorio](../../../lab/decomposition/README.md).
