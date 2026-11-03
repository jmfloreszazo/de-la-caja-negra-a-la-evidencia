**Español** · [English](../../en/part-2-archaeology-and-authority/07a-decomposing-a-mainframe-with-evidence.md)

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

## Entrevista y assessment de la plataforma de origen

La arqueología comienza con una entrevista estructurada y continúa contrastando cada respuesta con evidencia. La plataforma puede ser IBM Z con z/OS, IBM i sobre Power, Fujitsu BS2000 u otra; el lenguaje COBOL no identifica por sí solo ni el sistema operativo ni el gestor de datos. Registrar fabricante, modelo, versión, partición y productos realmente instalados evita inferencias prematuras.

La entrevista reúne a negocio, desarrollo, operaciones, datos, seguridad e infraestructura. Identifica capacidades y propietarios; lenguajes y fuentes; gestores de datos y archivos; transacciones y bloqueos; trabajos y ventanas batch; interfaces, transferencias, sucursales, continuidad, métricas y costes. Para cada respuesta se registra responsable, fecha, fuente, alcance y limitaciones. Una afirmación del experto es una hipótesis hasta contrastarla con código, configuración, observación y pruebas representativas; una traza que no muestra una dependencia no demuestra su inexistencia.

| Entorno o tecnología | Pregunta inicial |
|---|---|
| IBM Z y z/OS | ¿Se utilizan CICS, IMS DB o TM, Db2 for z/OS, VSAM y JCL? |
| IBM i | ¿Qué programas RPG, COBOL y CL acceden a Db2 for i y a archivos físicos y lógicos? |
| Fujitsu BS2000 | ¿Qué versiones de COBOL2000, openUTM, UDS/SQL, SESAM/SQL u openFT están instaladas? |
| Otros productos | ¿Existen Natural, Adabas, IDMS, Datacom o una plataforma Unisys y qué versiones e interfaces se usan? |

La presencia de cada producto debe comprobarse: son ejemplos, no componentes obligatorios de una arquitectura. IMS DB e IMS TM cumplen funciones diferentes. VSAM organiza y proporciona acceso a conjuntos de datos; sus claves, orden y codificación deben investigarse antes de seleccionar una estructura de destino.

### De la entrevista a una decisión verificable

Para cada capacidad se identifican reglas, datos, autoridad de escritura, límites de transacción, consumidores y criterios de aceptación. El equipo registra las incógnitas y decide qué puede mantenerse, encapsularse, sustituirse progresivamente o retirarse, con una justificación y una prueba para cada decisión. Una saga o un actor no sustituyen automáticamente una transacción atómica.

La comparación de alternativas local, cloud e híbrida usa cargas y periodos equivalentes, volúmenes, latencias, ventana batch, recuperación, seguridad, costes fechados y restricciones. MIPS, MSU y CPW no son unidades intercambiables ni se convierten directamente en núcleos. Las pruebas diferenciales utilizan entradas controladas, casos límite y resultados de referencia; las diferencias se investigan y aprueban. No se presume que un experimento sintético o un runner compartido represente una medición del mainframe o una prueba productiva.

## Contrato de evidencia

Este capítulo es una explicación de método apoyada por un **modelo sintético**, no por trazas de un banco, mediciones IBM Z ni aceptación productiva. Las pruebas del laboratorio sólo examinan decisiones estructurales. Véase [investigación detallada](../../../docs/research/mainframe-decomposition.es.md) y [laboratorio](../../../lab/decomposition/README.md).
