# Reconstruir el negocio para programar un sistema nuevo

> **Documento de investigación ES — issue #32.** Esta guía reemplaza el enfoque de «parsear COBOL para obtener microservicios» por **descubrir funcionalidades y reescribir la solución desde cero**. El catálogo anexo contiene hipótesis bancarias ilustrativas, no observaciones de una entidad financiera ni requisitos aprobados.

## La pregunta que hay que responder

No preguntamos «¿qué líneas, programas o copybooks hay que portar?», sino **«¿qué capacidades presta el sistema, qué consecuencias producen y qué garantías necesitan los usuarios y el negocio?»**. Podemos reemplazar toda la implementación y mantener los contratos de negocio, siempre que entendamos tanto los casos habituales como las excepciones que pueden llevar años escondidas en operaciones y procesos batch.

El mainframe existente puede ser una fuente de **observaciones**, nunca la autoridad única sobre lo correcto: un error heredado no se convierte automáticamente en requisito. Una persona responsable de negocio, política aprobada u oráculo independiente debe arbitrar discrepancias.

## Doce dominios y treinta hipótesis de capacidades

La versión inicial está en [functional_capabilities.json](../../lab/decomposition/functional_capabilities.json) y contiene 30 capacidades candidatas en 12 dominios: identidad y clientes; cuentas; pagos; tarjetas y ATM; precios e intereses; préstamos; libro mayor; operaciones y batch; riesgo y cumplimiento; operaciones y resiliencia; canales; e integración exterior.

Cada ficha registra objetivo, disparador, resultado, errores, invariante, consistencia esperada, criticidad, criterios Given/When/Then, lagunas, propietario y procedencia. **Todas** comienzan en estado `HYPOTHESIS_NOT_OBSERVED`. No es un análisis real del patrimonio mainframe.

## Cómo recuperar la funcionalidad sin analizar sintaxis

1. **Mapa de capacidades y responsables.** Entrevistas estructuradas a operaciones, contabilidad, fraude, canales, servicio al cliente, auditoría y responsables de producto. Separar reglas documentadas, prácticas informales y decisiones discrecionales.
2. **Jornadas y excepciones.** Event Storming para reconstruir qué ocurre en una retirada, transferencia, devolución, cierre diario o resolución de una incidencia; identificar comandos, eventos, decisiones, actores humanos y calendarios.
3. **Contratos externos reales.** APIs, mensajes, formatos, pantallas, recibos, estados visibles, protocolos con switches ATM y entidades de clearing. No confundir una confirmación de recepción con liquidación final.
4. **Evidencia de caja negra autorizada.** Ejecuciones de referencia con datos anonimizados o sintéticos representativos; entradas/salidas, tiempos, asientos, conciliaciones y estados tras fallo. Correlacionar por identificadores de operación. No volcar datos bancarios sensibles al repositorio.
5. **Oráculos independientes.** Reglas aprobadas para dinero, autorización, límites, consistencia, idempotencia, cierres y recuperación. Comparar el legado y la nueva implementación contra el mismo contrato aprobado, no entre sí como única prueba.
6. **Validación contradictoria.** Buscar contraejemplos: doble petición, caída tras COMMIT, terminal desconectado, efectivo no dispensado, transacción retroactiva, batch parcialmente terminado, horario internacional y cierre contable.
7. **Diseño desde cero.** Elegir límites de dominio, estructura de módulos, modelos de datos y arquitectura operativa sólo después de tener contratos suficientes. Un monolito modular puede ser una mejor primera solución que 30 microservicios.

## Ejemplo 1 — Transferencia interna (CAP-007)

**Contrato de negocio:** ante una transferencia válida con identificador estable, saldo suficiente y autorización, deben persistir asientos balanceados, estado de operación y evento de outbox bajo una autoridad transaccional. El cliente puede recibir `UNKNOWN` si se pierde el acuse, sin que ello signifique rollback.

| Caso | Resultado requerido | Prueba/oráculo independiente |
|---|---|---|
| Transferencia admitida | Dos apuntes compensados y una operación duradera | Suma de importes conservada; dos apuntes; un outbox |
| Mismo `operationId` repetido | Mismo efecto durable, sin segundo cargo | Cardinalidad por ID y saldo final |
| Fondos insuficientes | Rechazo sin movimientos contables | Estado inicial/final y auditoría |
| Fallo tras COMMIT antes del ACK | Respuesta incierta; consulta/reintento seguro | Estado real SQL y operación única |

**Decisión de implementación candidata:** servicio de dominio .NET 10 con PostgreSQL como autoridad contable, outbox transaccional e idempotencia. Orleans sólo si aporta una coordinación demostrada; no sustituye ACID. REST para canales externos y gRPC interno sólo si la medición y el contrato de plataforma lo justifican. Todo ello es **propuesta**, no decisión universal.

## Ejemplo 2 — Cajero ATM (CAP-011/012)

Autorizar fondos, reservarlos y **dispensar billetes** son hechos distintos. Cuando el cajero comunica que no pudo dispensar, la solución necesita reversión o reconciliación bajo la semántica y plazos de la red. Un ACK de autorización no es prueba de efectivo entregado. El contrato debe describir el protocolo de respuesta, operación ambigua, timeout, efectivo parcial, compensación, límites antifraude y evidencias del switch.

## Ejemplo 3 — Cierre diario (CAP-020/021/022)

El cierre involucra calendario de negocio, zona horaria, dependencias, importes de control, procesos incompletos, reinicios, reintentos y mensajes tardíos. Reescribir un job como cron no reproduce necesariamente sus garantías. Debemos documentar el estado de cada etapa, los checkpoints, si un libro cerrado admite correcciones y cómo se reabre o ajusta sin destruir el historial.

## Plantilla de especificación que habilita programación nueva

Una capacidad pasa a *lista para diseñar* sólo cuando existe: propietario y política vigente; comandos/consultas/eventos; estructura de datos bajo una autoridad; ejemplos positivos y negativos; transacciones y consistencia; fallos/reintentos/compensaciones; seguridad y trazabilidad; requisitos medibles (volumen, concurrencia, latencia, RTO/RPO, calendario y coste); dependencias con otros dominios; criterios de aceptación y oráculos **independientes**; evidencia aprobada y ADR de límites.

La salida se materializará como `intent.md`, `spec.md`, escenarios Gherkin en inglés, contratos de API/eventos, ADR y suites de Oracle Gates. El objetivo no es transcribir comportamiento accidental: las discrepancias se elevan al propietario funcional para decidir si son **regla a preservar, fallo a corregir o cambio deliberado**.

## Progreso y límites

El gate [functional_contract_gate.py](../../lab/decomposition/functional_contract_gate.py) comprueba estructura y procedencia sin aprobar funcionalidad. Un estado `READY_FOR_INDEPENDENT_REVIEW` sigue requiriendo evaluación humana y pruebas reales. El estado inicial esperado son treinta `NEEDS_EVIDENCE`. No hay aquí trazas reales, resultados de un banco, normativa particular validada ni equivalencia de rendimiento con IBM Z.

**Siguiente experimento útil:** seleccionar dos capacidades relacionadas (transferencia interna y extracto de movimientos), obtener una política y escenarios autorizados, construir un oráculo de negocio independiente y desarrollar una implementación nueva con pruebas diferenciales y de recuperación; sólo después extender al resto.
