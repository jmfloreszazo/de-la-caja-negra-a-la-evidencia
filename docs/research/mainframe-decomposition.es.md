# Investigación: cómo descomponer un mainframe sin romper el negocio

> **Estado:** contrato de investigación y diseño; no es un experimento ejecutado ni una recomendación universal. Vinculado al issue #32. Esta propuesta no modifica la edición publicada v2026.10.29.

## La unidad de extracción no es el programa COBOL

Los límites de un sistema heredado se descubren cruzando el mapa de capacidades del negocio con sus invariantes transaccionales y su topología real de ejecución. Un programa CICS puede participar en varios procesos; varias aplicaciones y jobs JCL pueden compartir una misma regla o saldo. Traducir programas, COPYBOOKs o tablas uno a uno conserva acoplamientos y puede introducir duplicidades de autoridad.

## Cinco fuentes de evidencia independientes

| Fuente | Qué aporta | Qué no demuestra |
|---|---|---|
| Event Storming con expertos | Eventos de negocio, decisiones, excepciones y responsables | La topología técnica real ni el derecho a particionar una transacción |
| DDD estratégico | Bounded contexts, lenguaje ubicuo, contratos y responsables | Que un contexto deba ser un microservicio |
| Análisis estático | CALL dinámico/estático, copybooks, SQL, LINK/XCTL, JCL, datasets, MQ | Dependencias reflejadas sólo en ejecución |
| Trazas operativas | CICS/IMS, Db2, SMF autorizado, batch, colas, picos y cierre contable | Que las muestras cubran todos los períodos |
| Oráculos independientes | Conservación, autorización, idempotencia, orden, reconciliación y recuperación | Que una prueba sintética reproduzca producción |

## Hipótesis falsable de extracción

**Hipótesis:** separar la consulta de movimientos de la contabilización puede reducir el acoplamiento sin duplicar la autoridad del saldo. **Refutación:** si la consulta requiere una vista transaccional inseparable de un UPDATE/COMMIT síncrono, o si el SLA y las reglas de autorización no toleran el desfase observado, la extracción propuesta no supera el gate.

### Ejemplo bancario: transferencia y extractos

1. **Comando**: TransferRequested con operationId estable; autenticación, autorización, límites y antifraude siguen siendo obligaciones explícitas.
2. **Límite ACID**: la transferencia modifica dos apuntes compensados, estado de operación y outbox en una única autoridad transaccional. Un actor Orleans no sustituye ese COMMIT.
3. **Proyección**: LedgerEntryCommitted alimenta un extracto de sólo lectura; un consumidor idempotente puede reintentar y reordenar sólo dentro del contrato publicado.
4. **Reconciliación**: si el read model se atrasa, el contrato exige watermark visible, lectura consistente alternativa o rechazo; nunca se presenta una proyección atrasada como balance autorizado.
5. **Rollback**: ante pérdida de idempotencia, balances incorrectos, incompatibilidad de latencia o imposibilidad de reconstruir eventos, se devuelve el tráfico a la ruta heredada mediante un cambio de enrutado versionado.

## Decision record: conservar, encapsular, extraer o retirar

| Decisión | Aplicar cuando | Gate de salida |
|---|---|---|
| Conservar en mainframe | ACID compartido opaco o criticidad sin oráculo independiente | Inventario de riesgos y propietario de operación |
| Encapsular con API/ACL | Contrato estable, dependencia antigua necesaria | Trazas, latencia, seguridad y conciliación |
| Extraer lectura/proyección | Consistencia eventual tolerada y demostrada | Watermark, idempotencia, reconstrucción, SLA |
| Extraer comando/dominio | Autoridad única, invariantes y rollback demostrables | Pruebas dual-run, shadow, canary y reversión |
| Retirar | Ninguna ruta, job o consumidor requiere el activo | Evidencia de uso nulo por ventana representativa y autorización |

## Orden de trabajo del laboratorio (código y README, exclusivamente en inglés)

1. Crear un grafo sintético trazable: programas COBOL, transacciones CICS, tablas, jobs JCL, colas y capacidades; cada arista identifica fuente, timestamp y confianza.
2. Combinar aristas estáticas con trazas y discrepancias explícitas; las dependencias desconocidas no desaparecen por falta de observación.
3. Proponer candidatos de bounded context mediante reglas versionadas, no un corte automático de servicios.
4. Exportar contratos de comandos/eventos, matriz de estado propietario, invariantes, ventanas batch, latencia y rollback.
5. Gate negativo: impedir un corte que divide una transacción sin estrategia de consistencia aprobada.
6. Comparar alternativas: conservar, modular monolith, strangler, coexistencia híbrida y microservicios; registrar ADR y costes.
7. Vincular cada decisión con evidencias E1/E2 cuando existan, distinguiendo prototipo, CI real y producción.

**Pendiente:** corpus reproducible sintético y casos con controles negativos; validación independiente del grafo; revisión de expertos de dominio; datos de carga y costes fechados. Nada de lo anterior está aceptado como resultado experimental.
