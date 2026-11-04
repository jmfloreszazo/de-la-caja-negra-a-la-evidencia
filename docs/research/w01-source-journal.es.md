# W01 — De snapshots completos a un journal transaccional del origen

**Issue #58 · 4 de noviembre de 2026 · Investigación brownfield, NO CDC de mainframe ni aceptación bancaria.** [English](w01-source-journal.en.md). Se apoya en la [proyección PostgreSQL W01 ya ejecutada](w01-projection.es.md) y en las [pruebas de permisos del lector](w01-reader-identity.es.md).

## Qué problema resuelve

El primer W01 reconstruía la proyección con snapshots completos, comprobaba un reloj muestreado en el origen y recurría a fallback cuando faltaba frescura o integridad. La ampliación de 20 pruebas demostró una **identidad PostgreSQL con permisos exclusivamente de lectura**. Todavía no existía un journal completo y reproducible, una frontera verificable entre instantánea inicial y cambios posteriores, ni pruebas de que una caída no publicase saldos parciales.

Este incremento añade un **journal transaccional sintético en el PostgreSQL del origen**, con veinte escenarios sobre bases reales. No usa parser COBOL ni presupone que IBM Z, IBM i, Fujitsu, BS2000, IMS, CICS o Db2 implementen el mismo mecanismo de captura.

## Frontera de COMMIT y responsabilidades

```text
           Escritor autorizado SOLO DEL FIXTURE DE PRUEBAS
                               │
                   UN COMMIT SQL en origen
         saldos + 2 apuntes + outbox + reloj + evento
                               │
              instantánea RR READ ONLY en origen
          16 cuentas + watermark + cadena de eventos
                               │
           instalación atómica del corte en destino
                               │
     lectura secuencial seq+1 ... seq+n y validación de cadena
                               │
       UN COMMIT SQL en destino: saldos + cursor + digest
                               │
          auditoría independiente del historial completo
```

La entrada del journal incorpora la secuencia comprometida, ID de operación, ambas imágenes anterior/posterior de cuentas y hash encadenado. El escritor de pruebas incrementa `legacy.clock` **en la misma transacción** que operaciones financieras, outbox y evento. No empleamos `BIGSERIAL` como secuencia supuestamente sin huecos: en PostgreSQL una transacción abortada puede consumir números de secuencia.

El lector de cambios solo posee `SELECT` de saldos, reloj y journal. Cada lote actualiza saldos proyectados, cursor, hash y digest **en una única transacción del destino**; si falla después de cambiar filas y antes de publicar el cursor, todo el lote se revierte.

La captura inicial lee saldos, reloj e historial **en la misma instantánea `REPEATABLE READ`**. Si el origen confirma otra transferencia después del corte, la recibimos mediante catch-up, sin confundirla con el snapshot. El replay comprueba huecos, orden, digest, enlace al evento anterior, imágenes previas y consistencia del destino; rechaza historias incompletas en lugar de saltar silenciosamente al último saldo.

Un **oráculo independiente y explícito** reconstruye el historial sintético desde 16 cuentas de 100.000 unidades menores y compara la situación del origen y destino cuando sus cursores coinciden. La eliminación de eventos antiguos y una modificación privilegiada del origen sin nueva versión se detectan durante esta auditoría, **no necesariamente al consultar solo el tail**. Un administrador privilegiado podría falsificar toda la cadena de hashes: SHA-256 aquí sirve de comprobación de integridad, **no de autenticidad del origen**.

## Controles negativos obligatorios

| Incidente | Decisión exigida |
| --- | --- |
| Falta una secuencia antes del reloj de origen | **BLOCK**, cursor sin avanzar |
| Evento manipulado o enlace anterior inválido | **BLOCK** y rollback del lote |
| COMMIT de origen entre captura y publicación inicial | Nueva entrega **en catch-up** |
| Caída del destino entre cambios de cuentas y actualización del cursor | **Rollback conjunto**; repetición segura |
| Transacción de origen abortada | Sin apuntes, outbox, reloj ni evento |
| Se modifica la proyección fuera del contrato | **BLOCK** por digest o imagen previa |
| Escritura privilegiada sin nueva versión del origen | **BLOCK en auditoría explícita**; tail-only puede no verlo |
| Eliminación de historial ya consumido | **BLOCK en auditoría**, aunque un poll vacío no lo detecte |
| Lector intenta escritura o consultar transacciones privadas | **Rechazo PostgreSQL por privilegios** |
| Intento de reinstalar snapshot sobre cursor ya aplicado | **BLOCK**, sin retroceso |

## Límites que no convierten esto en CDC bancario

No hemos implementado decodificación de WAL, replication slots, lector de logs Db2, integración MQ, hooks de IMS/CICS, garantía de retención, recuperación de suscripciones, elección de dueño de checkpoint, firma independiente ni HA de dominios físicos. Se admiten **como máximo 256 operaciones sintéticas**, con 16 cuentas, para facilitar la reconstrucción exhaustiva: **no es un benchmark**.

Un CDC real debe estudiarse por fabricante, versión y acceso permitido. Exige sincronización snapshot/log, orden de COMMIT, borrados, cambios de esquema, recuperación/gaps, offline/batch/privilegios, auditoría externa, seguridad y conciliación contable. Un workflow verde no demuestra que el mainframe pueda proporcionar ese contrato.

La lectura de reloj seguida de consulta de proyección sigue siendo **no linealizable**, porque el origen puede confirmar entre ambas. El servicio W01 anterior **no cambia**: este es un laboratorio hermano para estudiar el mecanismo incremental, no una sustitución de su API.

Los gates reales siguen en [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) y en el [protocolo de fencing del origen](../BROWNFIELD_SOURCE_FENCE.es.md). **TODM G2 INCONCLUSIVE / G6 BLOCK**; sin autorización de producción. E2 conserva `partially_verified`, #8 cerrado administrativamente y #53 congelado.

## Cómo reproducirlo

Véase el [laboratorio Podman (código y README en inglés)](../../lab/brownfield/w01_feed/README.md). El resultado original de CI y los artifacts deben enlazarse aquí **una vez ejecutados**, con SHA y negativos observados; la mera existencia del protocolo no es un PASS.
