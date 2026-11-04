# Oleadas de extracción brownfield desde las capacidades del negocio

**Issue #32 · Protocolo de investigación y pruebas · 4 de noviembre de 2026.** [English](mainframe-extraction-waves.en.md). Método sintético y refutable para **sustituir progresivamente capacidades de un sistema existente**; no es un parser de COBOL, un generador automático de microservicios DDD, un estudio real de un banco ni una aceptación funcional. Se apoya en las [30 hipótesis de capacidades](../../lab/decomposition/functional_capabilities.json), el [gate de contratos](../../lab/decomposition/functional_contract_gate.py) y el [oráculo de límites](../../lab/decomposition/oracle.py).

## La unidad de migración es una promesa del negocio

Event Storming ayuda a descubrir comandos, decisiones, reversiones y cierres; DDD estratégico propone bounded contexts. Después, las observaciones reales y los propietarios del sistema deben refutar o validar las hipótesis. **Event Storming no equivale a Event Sourcing.** Una llamada COBOL, tabla Db2 o tarea JCL no es por sí misma un dominio de negocio. Un módulo nuevo en .NET 10 forma parte de una **modernización brownfield**: el patrimonio, las operaciones, las interfaces y la autoridad sobre los datos ya existen.

Hay **tres decisiones distintas**:

1. **Descubrir la funcionalidad:** qué parece hacer el origen, qué debería hacer y quién aprueba las reglas. Las 30 capacidades iniciales siguen siendo `HYPOTHESIS_NOT_OBSERVED`.
2. **Refutar límites peligrosos:** ¿la oleada atraviesa un COMMIT contable indivisible, cierre batch, dependencia desconocida o efecto externo? Un grafo incompleto puede encontrar contradicciones, **no demostrar por ausencia que todo es seguro**.
3. **Autorizar operacionalmente:** fencing en el escritor legado real, conciliación de `UNKNOWN`, pruebas de carga/recuperación, criterios de negocio y TODM independiente. Un algoritmo de agrupación **nunca** concede esta autoridad.

## Decisiones estructurales y contratos

| Modo | Qué se pretende extraer | Restricción no negociable |
| --- | --- | --- |
| `READ_ONLY_PROJECTION` | Consulta desacoplada con el mainframe como autoridad | Sin nuevos apuntes; watermark, reconstrucción idempotente, clasificación no autoritativa y fallback a la fuente; no usar un saldo retrasado para autorizar efectivo |
| `EXPOSE_LEGACY` | API/ACL o nuevo canal sobre el core existente | La autoridad sobre las escrituras sigue en el legado; una fachada no bloquea rutas directas CICS/IMS, batch, offline o privilegiadas |
| `COMMAND_REPLACEMENT` | Sustituir un comando cuyo dueño está controlado | Rechazar cortes que separen la misma unidad ACID, cierre batch, efecto externo no conciliado o consumidor financiero indispensable |
| `RETIRE` | Retirar un proceso o interfaz realmente inutilizado | Rechazar consumidores declarados, tareas estacionales desconocidas, cortes contables, escrituras pendientes y efectos irreversibles |

**`CANDIDATE_ONLY` no es una aprobación de migración.** Solo significa que el pequeño modelo sintético todavía no ha refutado esa frontera. No demuestra completitud de trazas, calidad de reglas, rendimiento ni autorización de despliegue. Incluso con un catálogo rellenado artificialmente, G2 sigue `INCONCLUSIVE` y G6 en `BLOCK`.

## Cuatro oleadas sintéticas reproducibles

El [fixture](../../lab/decomposition/wave_fixture.json) vincula identificadores CAP, dependencias tipadas y preguntas concretas a resolver con responsables reales. **Sus relaciones son hipótesis, no trazas de un mainframe.**

| Oleada | Hipótesis | Resultado estructural esperado | Justificación |
| --- | --- | --- | --- |
| **W01** consulta de saldo `CAP-005` | Crear proyección de lectura manteniendo el origen autoritativo | **CANDIDATE_ONLY** | Exige watermark, fallback consistente a origen, reconstrucción idempotente y prohibición de efectos financieros. Saldo contable, disponible y autorización ATM son contratos distintos |
| **W02** transferencia interna `CAP-007` | Trasladar solo el comando de transferencia a .NET | **REJECT** | Se rompería la relación atómica hipotética con `CAP-019` (subledger/GL); un microservicio por programa puede romper la promesa contable |
| **W03** planificador batch `CAP-021` | Retirar el scheduler antes de sustituir sus obligaciones | **REJECT** | El cierre `CAP-020` depende de él y queda sin resolver una posible ruta estacional/retroactiva `CAP-022` |
| **W04** operaciones de sucursal `CAP-027` | Exponer una fachada de sucursal manteniendo autoridad del legado | **CANDIDATE_ONLY** | Una ACL puede ser buena frontera inicial, pero faltan evidencias de offline, permisos, seguridad, latencia y reinicios |

También se registran dependencias hipotéticas entre autorización y dispensación ATM, ledger y ficheros de conciliación, cierre y GL. No afirmamos que todas existan en un banco particular. Una **saga** o un **grain Orleans** no puede presumirse equivalente a ACID en W02. Reemplazar JCL por cron tampoco reproduce el checkpoint o calendario contable de W03.

### Ejecutar los controles de rechazo

```bash
python3 -m unittest discover -s lab/decomposition -p 'test_*.py' -v
python3 lab/decomposition/wave_gate.py \
  lab/decomposition/functional_capabilities.json \
  lab/decomposition/wave_fixture.json
# Exit 1 esperado: W02 y W03 deben rechazarse. Es una prueba negativa correcta.
```

Las pruebas adversariales incluyen pérdida del watermark y fallback, proyección que intenta escribir, división de la transacción, efecto externo del cajero, retirada del batch con dependencias estacionales, falsificación de aprobación y manipulación del esquema. `INVALID` usa salida 2; una propuesta rechazada usa 1; salida 0 solo indica que **todas las propuestas son candidatas estructurales**, nunca un PASS de negocio.

## Plan realista de oleadas sin puntuaciones inventadas

No debemos otorgar una nota numérica a datos todavía desconocidos. Cada decisión necesita: capacidad y dueño; Golden Master observado y política aprobada por separado; rutas online/batch/colas/oficinas; escritor autoritativo; unidad transaccional; orden temporal y calendario; watermark; consumidores y efectos externos; dependencias de ejecución sin resolver; TPS, p99, claves calientes, RPO/RTO; coste de convivencia; límites de rollback; contraejemplo y Oracle Gate independiente.

**Oleada 0 — conservar y observar:** inventariar transacciones, cierres, excepciones, propietarios y políticas sin dar permisos de escritura al candidato.

**Oleada 1 — exponer y proyectar:** crear contratos ACL versionados y proyecciones con retraso medido. El saldo proyectado no se convierte en disponible para gastar; necesita seguridad, reconstrucción, alarma de lag y lectura alternativa del origen.

**Oleada 2 — sustituir una función aislada:** avanzar solo tras contrato aprobado, fencing real en origen, conciliación de operaciones en vuelo/`UNKNOWN` y oráculo independiente con casos negativos. Un monolito modular puede ser más seguro que varios microservicios.

**Oleada 3 — mover autoridad contable o liquidación:** demostrar conjuntamente apuntes pareados, outbox, cierre batch/GL y dinero/efectos externos. Mantener intacta la unidad atómica o aprobar explícitamente nuevas garantías de consistencia. Una saga no elimina por arte de magia el problema del COMMIT.

**Oleada 4 — retirar:** comprobar ausencia de escritores y consumidores efectivos online, estacionales, offline y privilegiados durante una ventana justificada; preservar archivo legal, recuperación, auditoría y retirada de permisos. Una ruta desconocida exige **conservar e investigar**.

Cada oleada debe tener criterios previos de rechazo y una decisión independiente entre `RETAIN`, `EXPOSE`, `REPLACE`, `RETIRE` o `INCONCLUSIVE`. On-premises, Azure, híbrido, monolito modular u Orleans son **decisiones de arquitectura posteriores**, no el criterio que define los dominios.

## Entregado frente a pendiente

**Entregado en este incremento:** gate ejecutable y auditable **sobre hipótesis sintéticas**, cuatro oleadas, dependencias cruzadas, controles negativos y documento de investigación ES/EN. Las 30 capacidades históricas **no** se convierten en requisitos reales.

**Sigue pendiente:** trazas autorizadas, Golden Master y calendario aprobados, completitud de dependencias de ejecución, fencing sobre escritor real, conciliación de pagos externos, carga/HA representativas y aprobación TODM G2/G6. El issue #32 continúa abierto. La [aceptación de autoridad brownfield](../BROWNFIELD_SOURCE_FENCE.es.md) es una prueba del cliente separada; los [requisitos de PASS técnico E2](../E2_FULL_PASS_PROTOCOL.es.md) no se trasladan automáticamente a esta línea.
