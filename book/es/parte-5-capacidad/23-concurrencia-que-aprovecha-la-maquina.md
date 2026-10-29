**Español** · [English](../../en/part-5-capacity/23-concurrency-that-makes-use-of-the-machine.md)

[← Capítulo 22 · Los MIPS no caben en una conversión de vCPU](22-los-mips-no-caben-en-una-conversion-de-vcpu.md) · [Índice](../README.md) · [Capítulo 24 · El benchmark que vale: carga, contención, fallo y coste →](24-el-benchmark-que-vale-carga-contencion-fallo-y-coste.md)

# Capítulo 23 · Concurrencia que aprovecha la máquina

> [!IMPORTANT]
> **Tesis del capítulo.** Paralelizar lo independiente, limitar lo que satura y no confundir asincronía con capacidad. La cuenta caliente y los viajes de red marcan techos que ningún hardware elimina.

## Async no añade capacidad al recurso saturado

En .NET, la espera asíncrona puede liberar hilos mientras una dependencia responde. No reduce por sí sola el tiempo que una transacción retiene un bloqueo ni aumenta los commits que soporta el almacenamiento.

Abrir miles de tareas sobre una base de datos limitada desplaza la espera a conexiones, memoria y timeouts. Prefiero una admisión limitada y observable: cuántas operaciones aceptamos en curso, cuánto pueden esperar y qué respuesta damos al superar el presupuesto.

Una cola acotada permite aplicar presión hacia el productor. `Channel` ofrece una construcción local para ello [23]. Si necesitamos supervivencia a la caída del proceso, la cola necesita persistencia o un protocolo que permita reconstruir el trabajo. Una cola en memoria no es un broker durable.

También conviene distinguir el paralelismo de cálculo de la concurrencia de I/O. Ejecutar cada consulta SQL dentro de `Task.Run` no convierte el motor en más rápido. Bloquear hilos con `.Result` o `.Wait()` puede empeorar la capacidad del servicio. El perfilador debe mostrar dónde consumimos CPU y dónde esperamos.

## Admisión acotada en .NET

Este es el patrón que pondría en el borde de un servicio de transferencias: una cola acotada, una respuesta explícita cuando no cabe y un número de consumidores ajustado a lo que el motor puede confirmar, no al número de núcleos.

**Listado 23.1 · Backpressure con Channel acotado y rechazo explícito** — *Ilustrativo*

```csharp
var queue = Channel.CreateBounded<TransferCommand>(
    new BoundedChannelOptions(capacity: 2_000)
{
    FullMode = BoundedChannelFullMode.Wait,   // presión hacia el productor
    SingleReader = false,
    SingleWriter = false
});

// En el borde HTTP: si no cabe ahora, se dice ahora.
app.MapPost("/transfers", (TransferCommand cmd) =>
    queue.Writer.TryWrite(cmd)
        ? Results.Accepted($"/transfers/{cmd.OperationId}")
        : Results.StatusCode(StatusCodes.Status429TooManyRequests));

// Consumidores limitados por la capacidad de confirmación del ledger.
for (var i = 0; i < ledgerConcurrency; i++)
{
    _ = Task.Run(async () =>
    {
        await foreach (var cmd in queue.Reader.ReadAllAsync(stoppingToken))
            await ledger.TransferAsync(cmd, stoppingToken);
    });
}
```

![Figura 23.1 · Admisión acotada: lo que no cabe se rechaza ahora, en lugar de agotar el tiempo después.](../../figures/es/admission.png)

*Figura 23.1 · Admisión acotada: lo que no cabe se rechaza ahora, en lugar de agotar el tiempo después.*

Una advertencia honesta: este fragmento responde `202 Accepted` sobre una cola en memoria. Si el proceso cae, las peticiones admitidas y no confirmadas se pierden. Solo es aceptable si el cliente reenvía con la misma identidad de operación —y el ledger la deduplica— o si la cola es durable. Admitir no es confirmar, y el contrato debe decir qué significa cada respuesta.

## La cuenta caliente marca un techo

Supongamos que una entidad exige cuatro milisegundos de trabajo secuencial por operación. Sin solapar ese trabajo ni cambiar el contrato, su techo ideal se acerca a 250 operaciones por segundo. Añadir nodos para otras entidades no elimina ese tramo serial de la misma entidad.

Podemos reducir la sección crítica, mover cálculos previos fuera de ella o agrupar trabajo cuando sea semánticamente válido. También podemos descubrir que la entidad estaba definida de manera demasiado amplia. Lo que no haría es dividirla solo para que el benchmark mejore si con ello dejamos de proteger la regla.

La ley de Amdahl ofrece una advertencia parecida sobre un programa: una parte secuencial limita la mejora obtenible al añadir procesadores. Con un diez por ciento estrictamente secuencial, el límite ideal de aceleración se acerca a diez veces incluso con una cantidad enorme de procesadores. El sistema real añade comunicación y coordinación.

## Pocas llamadas que hagan trabajo útil

Si una operación realiza cincuenta viajes de red estrictamente secuenciales de dos milisegundos cada uno, consume alrededor de cien milisegundos solo en esos viajes, antes de sumar el procesamiento. Es un ejemplo aritmético, no una medición de Azure.

La respuesta puede ser reducir viajes, usar operaciones de conjunto, revisar el contrato o acercar aplicación y datos. El servidor más potente no elimina la latencia de una dependencia que seguimos consultando de la misma manera.

Al optimizar evitaría acumular el conjunto entero en memoria sin un límite. Lectura por lotes, streaming, cancelación, límites de memoria e índices adecuados pueden aportar más que una máquina mayor. Cada cambio debe conservar el resultado y pasar de nuevo por los oráculos.

> **Async libera hilos. No añade commits al almacenamiento ni acorta el tiempo que una transacción retiene un bloqueo.**

---

[← Capítulo 22 · Los MIPS no caben en una conversión de vCPU](22-los-mips-no-caben-en-una-conversion-de-vcpu.md) · [Índice](../README.md) · [Capítulo 24 · El benchmark que vale: carga, contención, fallo y coste →](24-el-benchmark-que-vale-carga-contencion-fallo-y-coste.md)
