**Español** · [English](../../en/part-4-patterns/17-from-mainframe-locks-to-explicit-concurrency-control.md)

[← Capítulo 16 · La propiedad de los datos](16-la-propiedad-de-los-datos.md) · [Índice](../README.md) · [Capítulo 18 · Distribuir sin romper la contabilidad →](18-distribuir-sin-romper-la-contabilidad.md)

# Capítulo 17 · De los locks del mainframe al control explícito de concurrencia

> [!IMPORTANT]
> **Tesis del capítulo.** Los bloqueos, el aislamiento y la unidad de trabajo no son propiedades de COBOL: los aporta el entorno, y no viajan al traducir. Hay que formular el invariante, elegir el mecanismo que lo protege y demostrarlo con historias concurrentes.

Este capítulo debería estar abierto junto al código, no únicamente en una reunión de arquitectura. El usuario ve una retirada aprobada o denegada. El ingeniero tiene que saber qué ocurre cuando llegan dos retiradas al mismo tiempo, cuando el proceso muere justo antes del commit o cuando un cliente reintenta porque perdió la respuesta.

En Db2 for z/OS, los niveles UR, CS, RS y RR ofrecen compromisos de aislamiento y contención distintos [37]. En CICS, el concepto de unidad de trabajo organiza qué recursos recuperables se confirman conjuntamente [16]. No son propiedades intrínsecas de COBOL y no viajan automáticamente al convertirlo a C#. Por eso, antes de elegir la tecnología, formulo el invariante: «no se confirma una retirada que deje la cuenta por debajo del saldo permitido», «un identificador de operación solo origina un asiento», «el total de cargos y abonos de una transferencia se conserva».

## De la instrucción COBOL a la unidad de trabajo

COBOL expresa lógica y representaciones. Las garantías transaccionales que experimenta una aplicación pueden proceder de CICS, Db2, IMS, VSAM recuperable, gestores de recursos y sus configuraciones. IBM describe unidades de trabajo y syncpoints que permiten confirmar o deshacer cambios sobre recursos recuperables [16]. La migración debe descubrir dónde empieza y termina esa unidad y quién coordina su recuperación.

Si traduzco las instrucciones y sustituyo cada acceso por una llamada remota independiente, puedo perder una garantía que antes estaba implícita en el entorno. El programa nuevo devolverá resultados parecidos en los ejemplos normales y fallará en el momento en que una operación intermedia no termine.

Tomemos una transferencia. El débito, el crédito, los asientos y la identificación de la operación deben pertenecer a una frontera coherente. Si la operación debe ser atómica, el sistema no puede dejar un cargo confirmado sin su abono correspondiente. Si el diseño permite estados intermedios, debemos representarlos y restringir cómo afectan al disponible.

El primer artefacto que pediría al equipo es el mapa transaccional, además del mapa de llamadas. Debe mostrar recursos participantes, orden, aislamiento, commit, rollback, timeouts, puntos de reinicio y comportamiento cuando se pierde la respuesta.

## Cuatro mecanismos y lo que no garantizan

**Pessimistic locking** es una opción cuando hay alta probabilidad de conflicto y debemos impedir actualizaciones concurrentes antes de ejecutar. **Optimistic concurrency** usa una versión y rechaza escrituras sobre un estado que ha cambiado. **Serializable** protege ciertas invariantes compuestas, a cambio de más contención, abortos o reintentos; sus garantías concretas dependen del motor. **Locks distribuidos** pueden coordinar trabajo externo, pero no reemplazan por sí solos una transacción de la base: ante expiraciones, particiones o pausas necesitamos *fencing tokens* para impedir que un propietario antiguo siga escribiendo. **Actors** serializan normalmente la ejecución por identidad, pero esa serialización en memoria no equivale a commit duradero.

Para una transferencia contable dentro de una misma base relacional elegiría inicialmente una transacción corta que incluya: validación, registro idempotente, asientos de cargo y abono, actualización de saldos derivados si procede y outbox. Si las cuentas residen en bancos o ledgers diferentes, hay que reconocer otra frontera y utilizar una cámara de compensación, coordinador u otro protocolo de negocio adecuado. No introduciría una saga para simular que una transferencia interbancaria ya es atómica.

![Figura 17.1 · Una transferencia como unidad de trabajo local: idempotencia, débito condicionado, crédito, asientos y outbox se confirman juntos o no se confirma nada.](../../figures/es/transfer_seq.png)

*Figura 17.1 · Una transferencia como unidad de trabajo local: idempotencia, débito condicionado, crédito, asientos y outbox se confirman juntos o no se confirma nada.*

## Bloqueo no es interbloqueo

Un bloqueo hace esperar a una operación porque otra mantiene un recurso incompatible. Puede ser el mecanismo correcto para proteger una regla. Un interbloqueo, o deadlock, aparece cuando las dependencias forman un ciclo que impide progresar.

Imaginemos que una transferencia de A a B bloquea primero A y otra de B a A bloquea primero B. Si ambas esperan después la otra cuenta, tenemos el ciclo. Acceder a las cuentas en un orden global consistente reduce esta causa de deadlock. No elimina todos los posibles ciclos de un motor: también participan índices, claves y otros recursos.

![Figura 17.2 · Un interbloqueo y su salida: víctima, reintento completo con la misma identidad y orden global para que el ciclo no se forme.](../../figures/es/deadlock_seq.png)

*Figura 17.2 · Un interbloqueo y su salida: víctima, reintento completo con la misma identidad y orden global para que el ciclo no se forme.*

PostgreSQL documenta la detección de deadlocks y recomienda mantener un orden consistente al adquirir varios bloqueos [17]. El protocolo debe prever que el motor aborte una víctima. La aplicación decide si puede repetir la operación completa, con la misma identidad y un presupuesto limitado. Reintentar indefinidamente convierte un conflicto en una tormenta.

Un timeout tiene una ambigüedad adicional: quizá el commit ocurrió y se perdió la respuesta. Repetir con una identidad nueva puede duplicar el efecto. Por eso la idempotencia de negocio debe permitir consultar el resultado y distinguir un reenvío de una petición diferente que reutiliza la misma clave.

En el laboratorio de concurrencia distinguiremos **seguridad** (nunca violar un invariante), **vivacidad** (terminar sin bloquearse indefinidamente) y **rendimiento** (progresar a una tasa suficiente). Son propiedades distintas y todas deben verificarse.

## La transferencia escrita para un motor con bloqueo por fila

El laboratorio usa SQLite, que serializa las escrituras y por tanto no puede mostrar un deadlock de filas. Así escribiría la misma operación en SQL Server o Azure SQL, ampliando el boceto `architecture/ledger_transaction.sql` del laboratorio. Las decisiones están comentadas en el propio código.

**Listado 17.1 · Transferencia en T-SQL: idempotencia, orden global de bloqueo, débito condicionado y outbox** — *Ilustrativo*

```sql
CREATE OR ALTER PROCEDURE dbo.Transfer
    @OperationId uniqueidentifier, @From nvarchar(64), @To nvarchar(64),
    @Amount decimal(19,4)
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;               -- cualquier error deshace la transacción completa
    BEGIN TRANSACTION;

    -- 1. Idempotencia: un reenvío con la misma identidad ve la decisión anterior.
    IF EXISTS (SELECT 1 FROM dbo.Operations WITH (UPDLOCK, HOLDLOCK)
               WHERE OperationId = @OperationId)
    BEGIN
        COMMIT;  SELECT 'DUPLICATE' AS Result;  RETURN;
    END;

    -- 2. Orden global: siempre se bloquea primero la cuenta de menor clave.
    DECLARE @First nvarchar(64)  = IIF(@From < @To, @From, @To),
            @Second nvarchar(64) = IIF(@From < @To, @To, @From),
            @Touch int;
    SELECT @Touch = 1 FROM dbo.Accounts WITH (UPDLOCK, ROWLOCK) WHERE AccountId = @First;
    SELECT @Touch = 1 FROM dbo.Accounts WITH (UPDLOCK, ROWLOCK) WHERE AccountId = @Second;

    -- 3. La regla se evalúa donde se confirma.
    UPDATE dbo.Accounts SET Balance = Balance - @Amount
     WHERE AccountId = @From AND Balance >= @Amount;
    IF @@ROWCOUNT = 0
    BEGIN
        INSERT dbo.Operations (OperationId, OperationType, Status)
        VALUES (@OperationId, 'TRANSFER', 'REJECTED');
        COMMIT;  SELECT 'REJECTED' AS Result;  RETURN;
    END;

    UPDATE dbo.Accounts SET Balance = Balance + @Amount WHERE AccountId = @To;

    -- 4. Operación, doble asiento y evento pendiente: todo o nada.
    INSERT dbo.Operations (OperationId, OperationType, Status)
    VALUES (@OperationId, 'TRANSFER', 'COMMITTED');
    INSERT dbo.LedgerEntries (OperationId, AccountId, SignedAmount)
    VALUES (@OperationId, @From, -@Amount), (@OperationId, @To, @Amount);
    INSERT dbo.Outbox (OperationId, Payload)
    VALUES (@OperationId, N'{"type":"TransferCommitted"}');

    COMMIT;
    SELECT 'COMMITTED' AS Result;
END;
```

Dos matices. El laboratorio, además de detectar el duplicado, compara el contenido del mandato: la misma identidad con otro importe es un conflicto, no un reenvío. Y el orden global reduce una causa de deadlock, pero no todas: índices, escaladas de bloqueo y otros recursos pueden cerrar ciclos. Por eso el cliente necesita un reintento acotado que conserve la identidad.

**Listado 17.2 · Reintento con presupuesto y misma identidad ante una víctima de deadlock** — *Ilustrativo*

```csharp
public async Task<TransferResult> TransferAsync(TransferCommand cmd, CancellationToken ct)
{
    const int maxAttempts = 5;
    for (var attempt = 1; ; attempt++)
    {
        try
        {
            // Misma OperationId en cada intento.
            return await _ledger.ExecuteTransferAsync(cmd, ct);
        }
        catch (SqlException ex) when (ex.Number == 1205 && attempt < maxAttempts)
        {
            var backoffMs = Math.Min(200, 10 * (1 << attempt))
                            + Random.Shared.Next(0, 10);
            await Task.Delay(backoffMs, ct);    // jitter; nunca infinita
        }
    }
}
```

En PostgreSQL, el equivalente se dispara con los fallos de serialización y de deadlock (SQLSTATE `40001` y `40P01`), y su documentación insiste en repetir la transacción completa, no la última sentencia [18]. Al agotar el presupuesto, el servicio informa del fallo y no inventa un resultado: eso es exactamente lo que comprueba el control `boundedRetries` del laboratorio.

## Elegir aislamiento con una anomalía en mente

No basta con decir que usamos ACID. Hay que identificar qué observaciones concurrentes admite la operación. Dos transacciones pueden leer que existe saldo suficiente y tomar decisiones incompatibles si su validación y su escritura no quedan protegidas adecuadamente.

Un débito condicionado ejecutado por el motor, una comprobación de versión, bloqueos explícitos o un aislamiento serializable son mecanismos posibles. La elección depende del conjunto de filas y predicados que sostiene la regla. Una condición por fila no garantiza una restricción sobre un grupo de cuentas.

La documentación de PostgreSQL distingue snapshot de serializable y exige preparar el reintento completo ante fallos de serialización [18]. SQL Server ofrece sus propios modos de bloqueo y versionado [19]. No asumiría que dos opciones con nombre parecido tienen idéntico comportamiento en motores diferentes.

Separaría tres dimensiones al diseñar: qué datos puede observar una operación, qué escrituras pueden confirmar y qué resultado ve el cliente. Una prueba secuencial no revela necesariamente el incumplimiento de ninguna de ellas.

## Una secuencia de aceptación

El contrato de una transferencia debería establecer qué significa aceptar, rechazar y desconocer todavía el resultado. Definiría la clave de idempotencia y su alcance, la moneda, la escala, el tratamiento de fondos insuficientes y el orden de los estados observables.

Después escribiría historias concurrentes que puedan contradecirlo. Dos retiradas compitiendo por el mismo disponible. El mismo mandato enviado varias veces. Una caída entre el cargo y el abono. Un commit seguido de una respuesta perdida. Una recuperación que repite una petición ya aceptada.

El oráculo debe examinar el estado y el historial, no únicamente el total global. Conservar el dinero total es necesario en nuestro caso sintético, pero permite errores como cargar a una cuenta equivocada. Necesitamos también correspondencia entre cada operación y sus asientos y reconciliación de saldos con el historial.

> **Seguridad, vivacidad y rendimiento son propiedades distintas. Una prueba secuencial no demuestra ninguna de las tres bajo concurrencia.**

---

[← Capítulo 16 · La propiedad de los datos](16-la-propiedad-de-los-datos.md) · [Índice](../README.md) · [Capítulo 18 · Distribuir sin romper la contabilidad →](18-distribuir-sin-romper-la-contabilidad.md)
