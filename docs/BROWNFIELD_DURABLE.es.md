# Capacidad brownfield persistente: una autoridad SQL aún no es un cutover bancario

**Estado: subconjunto SQL sintético ejecutado en CI; sin aceptación bancaria.** Véase la [evidencia original](../evidence/runs/BROWNFIELD-DURABLE.es.md). El alcance de un almacén descrito aquí es distinto de los posteriores experimentos de [dos almacenes](BROWNFIELD_TWO_STORE.es.md) y [journal C2](BROWNFIELD_JOURNAL.es.md).

CAP-007 (transferencia interna) y CAP-005 (saldo contabilizado) se reescriben
partiendo de un **contrato de capacidad definido por el legado**, no de la
sintaxis COBOL. Es modernización brownfield: las interfaces existentes, reglas
operativas, saldos, ventanas de liquidación y el sistema incumbente determinan
qué debemos conservar. Crear un componente nuevo en .NET no transforma la
migración en greenfield.

## Delimitación explícita de las afirmaciones

El candidato del [laboratorio](../lab/brownfield/durable/README.md) mantiene
una autoridad lógica en PostgreSQL desechable, y controla el escritor y su
época dentro de la transacción SQL. La huella de la petición, los dos apuntes,
el outbox y los saldos se confirman atómicamente. Un contador independiente
versiona las decisiones y permite exigir una versión mínima al consultar el
saldo autoritativo. Un cambio simulado de escritor y su reversión esperan
a que terminen las operaciones previas mediante el bloqueo de autoridad.

**Esto no demuestra** que un CICS/Db2/COBOL real haya dejado de escribir,
que dos almacenes autoritativos estén conciliados o que revertir un cutover
productivo sea seguro. Las etiquetas `legacy` y `candidate` son dos modos
del **mismo** motor SQL sintético, no dos sistemas bancarios independientes.
El valor de G6 se mantiene siempre en `BLOCK`.

## Hipótesis de fallos que debemos intentar refutar

| Control | Observación externa requerida | Límite |
| --- | --- | --- |
| Antes de COMMIT | SIGKILL tras un débito sin confirmar; sin efecto SQL; reintento con el mismo ID una sola vez | Una instancia PostgreSQL local |
| Después de COMMIT | El proceso desaparece antes de responder; la decisión persiste y el reintento es duplicado | Pérdida de respuesta, no toda partición de red |
| Cuenta caliente | Varios procesos cliente; sin saldos negativos ni apuntes parciales | Fixture pequeño; no prueba capacidad |
| Cutover | Nueva operación con época anterior rechazada; ID ya decidido sigue siendo duplicado | No bloquea un escritor legado externo |
| Frescura | `BELOW_MINIMUM_VERSION` si no hay versión suficiente | Lectura de autoridad, **no** proyección asíncrona |
| Apunte corrupto | El oráculo SQL independiente falla antes de restaurarlo | Datos de prueba desechables |

## Escalera de aceptación independiente

1. **Revisión técnica**: orden de bloqueos, huella de petición, idempotencia,
   reintentos, rechazos, tipos y límites monetarios.
2. **CI original**: ejecución real con .NET 10 y PostgreSQL 16; SHA exacto,
   digest de imagen, logs de compilación, JSON y controles negativos.
3. **G2 de negocio**: obtener las reglas, mandatos y contratos concretos
   aprobados por el cliente. Observar un Golden Master no equivale a aprobarlo.
4. **Convivencia**: adaptadores viejo/nuevo independientes, autoridad de datos
   controlada, conciliación real entre almacenes, simulacro y vetos al rollback.
5. **TODM G6**: aprobación humana responsable del artefacto y entorno exactos,
   jamás inferida de una CI técnica satisfactoria.

El paso 2 ya cuenta con evidencia SQL sintética original. La ampliación de
dos almacenes aporta convivencia simulada cooperativa; política del cliente,
fencing real de origen y G6 siguen con **APROBACIÓN DE NEGOCIO BLOQUEADA**.
E2 sigue en estado `partially_verified` y no se modifica ninguna release
publicada.

Seguimiento en [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).
