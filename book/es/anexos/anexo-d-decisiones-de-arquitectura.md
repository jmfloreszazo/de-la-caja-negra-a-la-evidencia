**Español** · [English](../../en/annexes/annex-d-architecture-decisions.md)

[← Anexo C · Ejecución de referencia](anexo-c-ejecucion-de-referencia.md) · [Índice](../README.md) · [Anexo E · Catálogo de cien riesgos →](anexo-e-catalogo-de-cien-riesgos.md)

# Anexo D · Decisiones de arquitectura

## Decisiones para una modernización

**ADR-001: Golden master no es la única verdad.** Se contrastará con reglas aprobadas e invariantes; una diferencia intencional tendrá decisión explícita de negocio.

**ADR-002: Una cuenta no es necesariamente una frontera ACID.** El actor coordina una identidad; el ledger define la fuente de verdad y el commit de operaciones relacionadas.

**ADR-003: Evitar doble escritura no coordinada.** La convivencia se apoya en un único escritor, outbox, CDC controlado y reconciliación.

**ADR-004: No mover funcionalidad por equivalencia de programas.** Las costuras se diseñan alrededor de capacidades de negocio y ownership de datos.

**ADR-005: El benchmark incluye fallos.** No existe aceptación de capacidad sin durabilidad, consistencia, carga sesgada y recuperación ensayadas.

**ADR-006: La IA no aprueba sus propios tests.** La baseline y los verificadores confiables tienen propietarios y permisos diferentes del agente constructor.

**ADR-007: Un traductor 1:1 puede ser temporal.** Se conserva una excepción documentada con alcance, fecha de revisión y criterios de salida.

## Decisiones del laboratorio

**Conservar dos referencias.** La ejecución COBOL aporta comportamiento observado; los casos aprobables aportan expectativa normativa. Una discrepancia entre ellas debe resolverse, no ocultarse.

**Separar procesos.** Candidato y gate se ejecutan como programas distintos. Esto permite comprender la separación y preparar una futura frontera de permisos. En el paquete local no hay aislamiento de seguridad entre sus autores.

**Usar una política pequeña.** La comisión y el umbral permiten comprobar errores concretos. El caso no intenta representar un core bancario.

**Mantener la reproducción sin un modelo remoto.** La ejecución determinista facilita repetir resultados. La construcción autónoma con agentes requiere un experimento separado.

**Registrar el entorno.** El resumen conserva versiones de herramientas y hashes de los fuentes. Una nueva ejecución debe generar su propio expediente.

**No publicar a producción.** SIMULATED_ALLOW es una etiqueta del laboratorio. No despliega, no concede privilegios y no representa una firma humana.

---

[← Anexo C · Ejecución de referencia](anexo-c-ejecucion-de-referencia.md) · [Índice](../README.md) · [Anexo E · Catálogo de cien riesgos →](anexo-e-catalogo-de-cien-riesgos.md)
