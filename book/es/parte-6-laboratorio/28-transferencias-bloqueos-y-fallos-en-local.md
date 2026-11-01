**Español** · [English](../../en/part-6-lab/28-transfers-locks-and-failures-locally.md)

[← Capítulo 27 · Hacer que el error se vea](27-hacer-que-el-error-se-vea.md) · [Índice](../README.md) · [Capítulo 29 · Incorporar agentes sin permitir que escriban el aprobado →](29-incorporar-agentes-sin-permitir-que-escriban-el-aprobado.md)

# Capítulo 28 · Transferencias, bloqueos y fallos en local

> [!IMPORTANT]
> **Tesis del capítulo.** La equivalencia funcional aislada no dice nada sobre concurrencia. El módulo bancario lleva el razonamiento de los capítulos 17 y 18 a procesos reales que compiten por un saldo, se caen después del débito y reenvían peticiones cuya respuesta perdieron.

## El laboratorio que acompaña esta decisión

El módulo bancario ejecuta procesos .NET separados sobre una base SQLite real con WAL y confirmación FULL. Comprueba carreras por saldo, reenvíos concurrentes, reutilización conflictiva de claves, rollback, caída de proceso después del débito y commit con respuesta perdida. Fuerza una espera de bloqueo, verifica reintentos limitados y reconcilia saldos, asientos y filas outbox. Una mutación deliberada del historial comprueba que el oráculo la rechaza.

SQLite serializa las escrituras y no representa el bloqueo por fila de SQL Server o PostgreSQL [29]. Por eso este módulo permite aprender sobre atomicidad e idempotencia en local; no acredita un deadlock de filas, un cluster bancario, tolerancia a caída de máquina ni capacidad equivalente al mainframe.

Las pequeñas medidas con uno, dos, cuatro y ocho procesos sirven para observar cómo cambian latencia y contención en esta máquina. Son ensayos locales de circuito cerrado, con calentamiento y duración insuficientes para dimensionar producción. El código conserva los resultados para hacer explícito ese límite.

**Evidencia ampliada: de SQLite a PostgreSQL y SQL Server (30 de octubre de 2026).** El laboratorio conserva intacta la referencia SQLite y prueba dos implementaciones adicionales de .NET 10 sobre motores transaccionales reales en contenedores Podman. En PostgreSQL, [E1b](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41034420329) completó ocho escenarios de carga lógica —1, 2, 4 y 8 trabajadores, con distribución uniforme y cuenta caliente—, 960 transferencias confirmadas por cada candidato y estados persistidos equivalentes. En SQL Server 2022 Developer, [E1c](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41042317263) reprodujo la misma matriz con otros 960 movimientos confirmados por cada candidato, comparación de las cuatro tablas y siete invariantes contables independientes en todos los casos. Los [resultados originales de SQL Server](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/blob/main/evidence/runs/e1c-sqlserver-worker-parity.json) incluyen la configuración, los casos y los hashes de los ejecutables.

**Lo que cambia no es el contrato, sino el protocolo de concurrencia.** SQLite serializa escritores, PostgreSQL admite bloqueos explícitos por fila y SQL Server combina `UPDLOCK` con `sp_getapplock` en esta implementación. En pruebas separadas sobre SQL Server, [la ejecución transaccional](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41041573996) observó una víctima real de deadlock (`1205`) con reintento de toda la transacción, bloqueos agotados (`1222`), tiempo de espera del cliente distinto (`-2`), idempotencia, rechazo de una clave duplicada y un control negativo de *write skew*: `SNAPSHOT` rompió la regla de mantener un operador activo, mientras `SERIALIZABLE` la preservó. El oráculo independiente detectó un asiento suprimido deliberadamente y validó su restauración.

**Límite obligatorio.** Los 960 movimientos de cada matriz se ejecutaron bajo modelos de procesos diferentes: los trabajadores SQLite permanecen vivos y el candidato SQL Server inicia un proceso .NET por transferencia. Por ello no hay una comparación válida de throughput, p99 o eficiencia entre motores; tampoco se han demostrado recuperación ante corte eléctrico, alta disponibilidad, latencia WAN, equivalencia CICS/Db2 ni capacidad MIPS de mainframe. Aquí la evidencia acredita **comportamiento contable bajo los escenarios ensayados**, no la capacidad de la arquitectura destino.

## El contrato está en el esquema

Antes que el código, el esquema. Las restricciones de la base son la primera línea del oráculo: un saldo no puede ser negativo, una operación tiene una identidad única, cada asiento pertenece a una operación y cada operación confirmada tiene su fila outbox.

**Listado 28.1 · Esquema creado por Bank/Program.cs** — *Ejecutado*

```sql
CREATE TABLE accounts(id INTEGER PRIMARY KEY,balance INTEGER NOT NULL CHECK(balance>=0));
CREATE TABLE operations(id TEXT PRIMARY KEY,src INTEGER NOT NULL,dst INTEGER NOT NULL,
                        amount INTEGER NOT NULL CHECK(amount>0),status TEXT NOT NULL);
CREATE TABLE postings(op TEXT REFERENCES operations(id),account INTEGER REFERENCES accounts(id),
                      delta INTEGER NOT NULL CHECK(delta<>0),PRIMARY KEY(op,account));
CREATE TABLE outbox(op TEXT PRIMARY KEY REFERENCES operations(id),event TEXT NOT NULL);
```

![Figura 28.1 · El esquema del módulo bancario: las restricciones son la primera línea del oráculo.](../../figures/es/bank_er.png)

*Figura 28.1 · El esquema del módulo bancario: las restricciones son la primera línea del oráculo.*

## Idempotencia: el mismo mandato, una sola vez

Dentro de la misma transacción que ejecutará el movimiento, el servicio busca la identidad de la operación. Si existe y el contenido coincide, devuelve la decisión anterior. Si existe con otro contenido, es un conflicto.

**Listado 28.2 · Bank/Program.cs: reenvío frente a conflicto de identidad** — *Ejecutado*

```csharp
   var existing=db.Rows($"SELECT src,dst,amount,status FROM operations WHERE id='{id}'");
   if(existing.Count>0) {
    var e=existing[0];
    var same=e["src"]==src.ToString()&&e["dst"]==dst.ToString()&&e["amount"]==amount.ToString();
    db.Exec("COMMIT");begun=false;
    return new(same?"DUPLICATE_"+e["status"]:"ID_CONFLICT",retries,clock.Elapsed.TotalMilliseconds);
   }
```

Una nota de oficio: el laboratorio construye SQL interpolando valores porque llama a la biblioteca nativa sin capa intermedia, y lo hace después de validar la identidad con una expresión regular estricta y de tipar los números. En un servicio real usaría parámetros siempre. La regla de negocio que demuestra es la misma.

## Fallos sembrados donde más duelen

**Listado 28.3 · Bank/Program.cs: tres fallos inyectados y el reintento acotado** — *Ejecutado*

```csharp
   if(approved) {
    if(fault=="crash-after-debit")Environment.Exit(91);
    if(fault=="throw-after-debit")throw new InvalidOperationException("Injected failure after debit");
    db.Exec($"UPDATE accounts SET balance=balance+{amount} WHERE id={dst}");
   }
   // ... operación, asientos y outbox ...
   db.Exec("COMMIT");begun=false;
   if(fault=="lost-response")Environment.Exit(92);
   return new(status,retries,clock.Elapsed.TotalMilliseconds);
  } catch(SqlFailure e) when(e.Code==5||e.Code==6) {
   if(begun)db.Exec("ROLLBACK");retries++;
   Thread.Sleep(Math.Min(50,2*(attempt+1))+Random.Shared.Next(1,8));
  }
```

El proceso que muere después del débito y antes del commit no deja cargo parcial, porque el débito nunca se confirmó. El proceso que muere después del commit sin responder deja una decisión durable: el reenvío con la misma identidad la recupera como `DUPLICATE_COMMITTED` en lugar de cobrar dos veces. Y el bloqueo mantenido por otro proceso produce esperas y reintentos acotados; al agotar doce intentos, el servicio informa `RETRY_EXHAUSTED` y no toca los saldos.

![Figura 28.2 · Dos fallos sembrados en el laboratorio: caída antes del commit y respuesta perdida después del commit.](../../figures/es/bank_faults.png)

*Figura 28.2 · Dos fallos sembrados en el laboratorio: caída antes del commit y respuesta perdida después del commit.*

## El oráculo no le pregunta al servicio

El verificador es un proceso Python distinto que abre la base y comprueba invariantes sobre los datos persistidos. No consulta la respuesta del servicio, porque un servicio puede contestar «OK» y haber dejado otra cosa detrás.

**Listado 28.4 · bank_test.py: invariantes contables sobre el estado persistido** — *Ejecutado*

```python
tests={
 'nonnegative':s('SELECT MIN(balance) FROM accounts')>=0,
 'conserved':s('SELECT SUM(balance) FROM accounts')==s('SELECT COUNT(*)*100000 FROM accounts'),
 'balancedPostings':s('SELECT COUNT(*) FROM (SELECT op FROM postings GROUP BY op '
                      'HAVING SUM(delta)<>0 OR COUNT(*)<>2)')==0,
 'projectionAgrees':s('SELECT COUNT(*) FROM accounts a WHERE balance<>100000+COALESCE('
                      '(SELECT SUM(delta) FROM postings p WHERE p.account=a.id),0)')==0,
 # ... twoPostingsPerCommit y outboxAtomic
}
```

Conservar el total es necesario y no suficiente: un movimiento cargado a la cuenta equivocada también conserva el total. Por eso el oráculo exige además dos asientos balanceados por operación y que cada saldo se pueda reconstruir desde su historial. El control negativo borra un asiento de una copia de la base, y el oráculo debe rechazarla. Lo hace.

## Medidas locales, y por qué no son capacidad

| Patrón | Procesos | Operaciones | Op/s incl. arranque | p50 ms | p95 ms | p99 ms | Reintentos |
|---|---|---|---|---|---|---|---|
| uniforme | 1 | 32 | 221,9 | 1,52 | 1,99 | 2,03 | 0 |
| uniforme | 2 | 64 | 348,4 | 1,27 | 1,82 | 10,51 | 0 |
| uniforme | 4 | 128 | 509,4 | 0,93 | 1,90 | 41,70 | 1 |
| uniforme | 8 | 256 | 693,3 | 0,77 | 27,22 | 124,90 | 4 |
| caliente | 1 | 32 | 259,9 | 1,17 | 1,61 | 1,79 | 0 |
| caliente | 2 | 64 | 351,3 | 1,13 | 3,82 | 11,77 | 0 |
| caliente | 4 | 128 | 495,6 | 0,81 | 2,04 | 42,08 | 0 |
| caliente | 8 | 256 | 624,4 | 0,85 | 28,40 | 109,78 | 5 |

![Figura 28.3 · Ejecución de referencia: la mediana baja y la cola se dispara al añadir procesos que compiten por un único escritor.](../../figures/es/measures_chart.png)

*Figura 28.3 · Ejecución de referencia: la mediana baja y la cola se dispara al añadir procesos que compiten por un único escritor.*

La tabla enseña una cosa verdadera y nada más: al añadir procesos que compiten por un recurso serializado, la mediana mejora y la cola se dispara. Es el mismo fenómeno que aparecerá con una cuenta caliente o con un log saturado. Pero son 32 operaciones por proceso, en circuito cerrado, incluyendo el arranque de cada proceso .NET, sobre un motor que serializa escrituras, en una sola máquina. No hay calentamiento ni duración suficiente, no hay baseline del mainframe y no hay Azure. Esta tabla no puede aprobar capacidad, y el código lo deja escrito en el propio resumen de resultados.

> **El servicio puede contestar OK y dejar otra cosa detrás. El oráculo mira lo que queda.**

## Del débito atómico al traspaso de autoridad entre dos almacenes

La siguiente dificultad no consiste en hacer funcionar una transferencia con
PostgreSQL. Consiste en **trasladar la autoridad contable de un sistema heredado
a otro nuevo**, sin que los dos escriban al mismo tiempo ni que una caída de
red convierta una respuesta desconocida en un débito duplicado.

La [prueba brownfield de convivencia](../../../lab/brownfield/coexistence/README.md)
añade dos instancias PostgreSQL 16.13, cada una en un contenedor Podman
distinto, pero **ambas dentro de un único runner Linux**. Una representa un
legado sintético, expuesto mediante un ejecutable de caja negra y tablas con
nombres y estructuras diferentes. La otra contiene el candidato .NET 10.
Ninguna depende de un parser COBOL. Las reglas de negocio reales siguen
siendo una incógnita: escribir código nuevo desde cero no convierte una
migración brownfield en greenfield.

El control de escritor se representa mediante una fila de autoridad y una
época. Ambos adaptadores cooperan: mantienen un bloqueo compartido mientras
confirman sus respectivas transacciones. El cambio de escritor adquiere el
bloqueo exclusivo, espera a los comandos que ya estaban dentro y aumenta
la época. Así podemos demostrar que un comando tardío con una época antigua
es rechazado. **No hemos demostrado que un programa CICS o una transacción
Db2 fuera de este controlador respeten ese bloqueo**; el ensayo adversarial
de escritura directa prueba que el desvío se detecta, pero no se impide.

El protocolo está organizado en cuatro decisiones separadas:

1. **Observar sin escribir dos veces.** El shadow calcula respuestas a partir
   de lecturas; no publica ni un segundo asiento ni otro evento outbox.
   Si la réplica está desfasada, se declara la discrepancia.
2. **Preparar sin declarar autoridad nueva.** Bajo el bloqueo de transición
   se copia un snapshot consistente del legado al destino, incluidas las
   operaciones rechazadas, los identificadores, huellas, apuntes,
   eventos, versiones y contador de decisiones.
3. **Conciliar independientemente.** El oráculo normaliza ambos modelos
   de datos y compara cinco familias: cuentas, operaciones, apuntes,
   outbox y watermark. Comprueba, además, la conservación monetaria,
   la pareja de asientos y la ausencia de efectos de operaciones rechazadas.
4. **Cambiar o bloquear.** Solo si el estado completo coincide se
   aumenta la época y se acepta el cambio sintético de escritor.
   Un apunte o evento ausente, o una decisión nueva después del snapshot,
   debe bloquear la transición. No basta con que el saldo total coincida.

La [ejecución original sobre SHA exacto](../../../evidence/runs/BROWNFIELD-TWO-STORE.es.md)
del 1 de noviembre de 2026 superó los controles sintéticos. El legado terminó
con ocho decisiones y el candidato con diez, dos de ellas posteriores al
cutover. Los diez invariantes de cada almacén fueron verdaderos, pero las
dos bases dejaron de ser idénticas; por eso el rollback quedó **bloqueado
con `FORWARD_FIX_REQUIRED`**. La conclusión no es «ya podemos volver atrás»,
sino la contraria: una vez que el nuevo escritor ha confirmado operaciones,
el antiguo estado deja de ser automáticamente válido.

### Qué falta antes de permitir un cutover real

Un contrato de caja negra simulado no concede al proveedor acceso a los
bloqueos del banco. Necesitamos un mecanismo verificable que retire al
incumbente su autoridad de escritura, más un registro persistente de
admisiones y resultados inciertos, conciliación ante interrupciones entre
almacenes, detección de efectos en sistemas terceros y protocolos de
reanudación o reparación hacia adelante. También hacen falta políticas
aprobadas por el propietario del negocio: un Golden Master observado no
basta para aprobar una política.

En TODM, este ensayo aporta evidencia técnica para G4/G5; **G2 permanece
inconcluso y G6 sigue bloqueado**. Tampoco prueba dominios físicos de fallo,
RTO/RPO productivos, equivalencia CICS/Db2, capacidad MIPS ni viabilidad
económica de Azure. Ese es precisamente el propósito del laboratorio:
convertir los supuestos de arquitectura en afirmaciones que podamos
refutar antes de prometer una migración.

---

[← Capítulo 27 · Hacer que el error se vea](27-hacer-que-el-error-se-vea.md) · [Índice](../README.md) · [Capítulo 29 · Incorporar agentes sin permitir que escriban el aprobado →](29-incorporar-agentes-sin-permitir-que-escriban-el-aprobado.md)
