# W01 — Una proyección de lectura no es dueña del saldo

**Issue #32 · Nota de implementación brownfield · 4 de noviembre de 2026.** [English](w01-projection.en.md). **Alcance:** dos servidores PostgreSQL 16.13 separados, ambos en contenedores de **un único host Linux**; uno representa el ledger legado sintético y el otro una proyección no autoritativa. Es un ensayo ejecutable sobre PostgreSQL real, **no** sobre IBM Z, CICS, IMS, Db2 ni datos bancarios de un cliente. Tampoco demuestra HA física o aceptación de negocio.

## Por qué empezamos por CAP-005

W01 toma la consulta de saldos CAP-005 del catálogo de 30 **hipótesis todavía no observadas**. Podemos estudiar cómo desacoplar la lectura sin mover el escritor de transferencias CAP-007. Pero **saldo contable, disponible, autorización y dispensación de un cajero ATM son contratos diferentes**. W01 entrega únicamente el saldo contable de una demostración sintética, **nunca fondos disponibles para gastar**. Para usar una proyección real hace falta conocer permisos, retraso permitido, excepciones, SLO y semántica de versiones aprobados por el cliente.

El origen es una base PostgreSQL con un esquema legado ficticio, **no un mainframe emulado**. Un escritor separado y exclusivo de las pruebas simula una transferencia: modifica saldos, dos apuntes, outbox y secuencia del origen en **una única transacción SQL**. El **código del proyector** solo puede leer el origen con `REPEATABLE READ READ ONLY`.

## Experimento de alimentación incremental independiente

El [journal transaccional sintético del origen](w01-source-journal.es.md) vive en **otro laboratorio**. No modifica esta implementación de snapshot/fallback W01 ni acredita CDC de Db2 o un contrato productivo de frescura.

## Identidad SQL del origen — ampliación de mínimo privilegio

La primera ejecución de 16 casos utilizaba el superusuario de la base de pruebas, aunque la aplicación ejecutara transacciones READ ONLY. La [ampliación de mínimo privilegio](w01-reader-identity.es.md) exige un login PostgreSQL efectivo `w01_reader` con SELECT exclusivamente en cuentas/reloj, y prueba que ni cambiando la transacción a READ WRITE puede modificarse el ledger. El harness conserva **otras credenciales administrativas desechables**; esto no acredita aislamiento de secretos bancarios ni fencing de un mainframe real.

## Arquitectura y ejecución

```text
 Escritor sintético de pruebas
       │  COMMIT financiero y secuencia de origen
       ▼
 PostgreSQL bf_legacy (puerto 55438) ← autoridad real del fixture
   legacy.accounts + legacy.clock
       │
       ├── snapshot consistente READ ONLY ──► refresco
       │                                       │
       │                                 único COMMIT destino
       │                                       ▼
       │                                PostgreSQL bf_projection
       │                                    puerto 55442
       │                          cuentas + watermark + digest
       │                                       │
       └── observación de reloj origen ───────► decisión de lectura
                                               ├─ actual y íntegra: proyección
                                               └─ obsoleta/dañada: fallback
                                                  a origen o bloqueo
```

**No existe CDC ni consumo incremental de eventos.** Cada refresco copia las 16 cuentas y el reloj desde una única instantánea consistente, y sustituye proyección y watermark juntos en una transacción del destino. Repetir el mismo refresco es idempotente. Si el origen cambia saldos **sin incrementar el reloj**, el siguiente refresco detecta el digest distinto a igual secuencia y se bloquea. Un retroceso de reloj también se rechaza. Una proyección manipulada no se sirve: se comprueba el digest completo, se usa el origen si está disponible y solo se repara mediante reconstrucción explícita.

### Decisiones de lectura

| Condición | Respuesta | Límite |
| --- | --- | --- |
| Proyección íntegra, misma secuencia que el reloj observado del origen y mínimo del cliente satisfecho | `PROJECTION_OBSERVED_CURRENT` | Una nueva transacción puede confirmar **después** de observar el reloj; **no es una lectura linealizable** |
| Proyección ausente, obsoleta, corrupta o caída, origen legible | `AUTHORITATIVE_FALLBACK` | Usa snapshot consistente del origen, pero no existe autenticación ni contrato bancario aprobado |
| Secuencia mínima solicitada superior a la del origen | `BLOCKED_MINIMUM_WATERMARK` | Nunca ignorar silenciosamente la condición de frescura del solicitante |
| Reloj del origen no disponible | `BLOCKED_SOURCE_UNAVAILABLE` | No entregar saldos antiguos simulando vigencia |
| Snapshot de fallback inaccesible o inconsistente | `BLOCKED_FALLBACK_UNAVAILABLE` | Bloquear, no responder con último valor conocido |
| Escritura en origen sin actualizar su reloj | El refresco rechaza `UNVERSIONED_SOURCE_MUTATION` | **La lectura basada solo en watermark no puede detectar el bypass en el instante de la consulta**; exige pruebas de disciplina en todos los escritores reales |

La marca mínima aportada por el cliente es solo una entrada del laboratorio: no equivale a un token causal certificado de *read-your-writes*. Leer el reloj del origen y la proyección implica dos operaciones distintas: no hay transacción de lectura distribuida. Además, consultar el origen en cada petición **no demuestra mejora de TPS ni p99**. En una proyección real habría que diseñar CDC con control de gaps, instantánea inicial/catch-up, orden, versiones de fuente, identidad, autorización, latencia y SLO de obsolescencia.

## Qué pruebas se ejecutan

El [laboratorio y README en inglés](../../lab/brownfield/w01_projection/README.md) requiere Podman y dos bases desechables con nombres/puertos exactos: `bf_legacy:55438` y `bf_projection:55442`; `W01_DISPOSABLE=YES` es obligatorio. Las pruebas destruyen **solo los esquemas de estos entornos desechables**, nunca deben apuntar a datos de clientes.

Se contrastan: primer refresco, fallback tras COMMIT real del origen, repetición idempotente, marca mínima, corrupción/reparación de la proyección, escritura sin avanzar reloj, regresión, caída de lectura origen y fallback, entradas y endpoints ilegales, independencia de los clústeres PostgreSQL y ausencia de escrituras del proyector en el ledger. El oráculo SQL independiente comprueba suma de saldos, dos apuntes por transferencia, un outbox, reloj y versiones. GitHub Actions archivará SHA exacto, versiones/imagen PostgreSQL, logs originales, resultados positivos y negativos; se conservan también si el job falla.

Son **observaciones funcionales sintéticas**; no son equivalencia MIPS, benchmarking, failover automático, E1/E2 global o reglas reales del banco.

## Aceptación pendiente y límites

**TODM G2 = INCONCLUSIVE y G6 = BLOCK**, aunque CI termine en verde. No tenemos política aprobada ni Golden Master real. El [oráculo de oleadas](mainframe-extraction-waves.es.md) solo filtra cortes peligrosos; este laboratorio añade prueba técnica real de mecanismos **acotados**. Ninguno certifica la autoridad del mainframe. La [guía de fencing real](../BROWNFIELD_SOURCE_FENCE.es.md) detalla la prueba del cliente por separado.

Para un W01 bancario faltarían: asegurar que ningún escritor legado altera saldos fuera del mecanismo de versión; CDC/snapshot consistente y control de gaps; comportamiento tras reinicios, retención y recuperación; contrato de consistencia por canal; autenticación, autorización, carga/latencia y revisión independiente del responsable de negocio.

El mecanismo acotado **ya se ha ejecutado**: [GitHub Actions W01 #41853096276](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41853096276), sobre SHA exacto `730b40a241986fbd4975d60285bd1b149ec743f3`, pasó **16/16** pruebas PostgreSQL reales. Las actas permanentes [ES](../../evidence/runs/W01-PROJECTION.es.md) / [EN](../../evidence/runs/W01-PROJECTION.md) conservan extracto literal, JSON transcrito, identidad del artifact y límites. **PASS_BOUNDED_SYNTHETIC_TESTS no equivale a un contrato bancario ni PASS global**. Seguimiento actual: #32 se CERRÓ después como investigación completada, mientras #58 sigue ABIERTO para pruebas reales del origen y negocio. Esta ejecución no altera E2, releases ni #53 congelado.
