**Español** · [English](../../en/part-4-patterns/20-batch-and-parallelism-speeding-up-without-changing-the.md)

[← Capítulo 19 · Actores: una gran herramienta, un mal sustituto universal](19-actores-una-gran-herramienta-un-mal-sustituto-universal.md) · [Índice](../README.md) · [Capítulo 21 · Event sourcing, CQRS y sagas: cuándo ayudan y cuándo estorban →](21-event-sourcing-cqrs-y-sagas-cuando-ayudan-y-cuando-estorban.md)

# Capítulo 20 · Batch y paralelismo: acelerar sin cambiar el resultado

> [!IMPORTANT]
> **Tesis del capítulo.** Lanzar mil workers contra el mismo índice distribuye la espera, no el trabajo. Un lote moderno particiona por una clave defendible, confirma checkpoints idempotentes y reduce de forma determinista.

La modernización batch suele ser el lugar donde el entusiasmo por los microservicios se encuentra con la factura del almacenamiento. No basta con lanzar mil workers. Si todos compiten por el mismo índice, el mismo fichero o una tabla de control, habremos distribuido la espera en vez de distribuir el trabajo. Antes de paralelizar necesitamos entender el grafo JCL, los sort/merge, las ventanas, las dependencias por fecha y los puntos en los que se permite confirmar una parte del lote.

El patrón principal es **Partitioned Batch con checkpoint y replay**. Elegimos una clave estable —por ejemplo, un rango de cuentas—, producimos particiones sin solapamiento, fijamos la versión de reglas que debe aplicarse y procesamos cada fragmento de forma idempotente. Registramos cuándo comenzó, qué entradas utilizó, qué sumas de control obtuvo y qué commit lo hizo definitivo. Un reintento no debe duplicar intereses ni comisiones. Si cambian parámetros a mitad de ejecución, el lote necesita un snapshot lógico para que dos particiones no calculen versiones distintas del negocio.

![Figura 20.1 · Lote particionado: reglas y fecha fijadas antes de empezar, checkpoint por partición y reconciliación contra la entrada.](../../figures/es/batch_flow.png)

*Figura 20.1 · Lote particionado: reglas y fecha fijadas antes de empezar, checkpoint por partición y reconciliación contra la entrada.*

Los resultados globales exigen **reducciones deterministas**. El total de millones de registros puede ser igual matemáticamente, pero no si cambiamos el punto donde se redondean los importes. El orden de agregación puede alterar incluso cálculos decimales con precisión y escala limitadas. Para cada regla debemos decidir si la equivalencia es por registro, por lote o por agregado, y cuáles son las tolerancias; en un ledger normalmente no aceptaremos tolerancias monetarias arbitrarias.

La optimización sigue una secuencia: medir lectura, decodificación, cálculo, escritura y commit; ampliar particiones hasta hallar el cuello; fijar límites de backpressure; observar contención y latencia de almacenamiento; y repetir con distribución realista. Un pipeline con 64 workers no es necesariamente el doble de rápido que otro con 32. Puede ser más lento si dispara la contención de índices o agota el buffer pool.

## Paralelizar el trabajo que puede ser independiente

En un cálculo puro podemos repartir entradas y combinar resultados. En un libro contable compartido, las operaciones tienen dependencias. El diseño concurrente empieza identificándolas.

Una opción es particionar por entidad o por una unidad de negocio cuya independencia podamos defender. Procesamos secuencialmente los cambios que afectan al mismo estado y en paralelo las particiones independientes. La clave elegida determina el máximo paralelismo y qué operaciones vuelven a necesitar coordinación.

El patrón de convoy secuencial documentado por Microsoft utiliza este principio y advierte del límite por grupo [22]. En una transferencia entre cuentas de grupos distintos, el orden local no resuelve la atomicidad global. En un cierre consolidado, la independencia local tampoco elimina la necesidad de fijar qué datos participan en el cálculo.

Un batch puede dividirse por cliente, cartera o rango cuando no hay dependencias cruzadas no resueltas. El recorrido debe conservar puntos de reinicio, identidad de los lotes y reconciliación. Aumentar el tamaño del commit reduce ciertos costes y aumenta la cantidad de trabajo y bloqueo expuestos a un fallo. El equilibrio se mide.

## Un lote que puede caerse y volver a empezar

**Listado 20.1 · Lote particionado con checkpoint en la misma transacción que los resultados** — *Ilustrativo*

```csharp
var options = new ParallelOptions
{
    MaxDegreeOfParallelism = degree,
    CancellationToken = ct
};

await Parallel.ForEachAsync(plan.Partitions, options, async (partition, token) =>
{
    // Una partición confirmada no se vuelve a aplicar: reiniciar es seguro.
    if (await store.IsCommittedAsync(plan.RunId, partition.Id, token)) return;

    await using var tx = await store.BeginAsync(token);
    var totals = await ProcessAsync(partition, plan.RulesVersion,
                                    plan.BusinessDate, tx, token);

    // Resultados y checkpoint en la MISMA transacción, con sumas de control.
    await tx.SaveCheckpointAsync(plan.RunId, partition.Id,
                                 totals.Count, totals.Amount, token);
    await tx.CommitAsync(token);
});

// Reducción determinista sobre lo confirmado, no sobre la memoria de los workers.
var control = await store.ReconcileAsync(plan.RunId,
                                        plan.ExpectedCount, plan.ExpectedAmount, ct);
```

![Figura 20.2 · Estados de una partición: un reinicio salta lo confirmado y repite lo que no llegó al commit.](../../figures/es/batch_states.png)

*Figura 20.2 · Estados de una partición: un reinicio salta lo confirmado y repite lo que no llegó al commit.*

Tres detalles sostienen este fragmento. `plan.RulesVersion` y `plan.BusinessDate` se fijan antes de empezar, para que dos particiones no calculen con versiones distintas del negocio. `degree` no es el número de núcleos: es el número de escritores que el motor soporta sin que la contención se coma la ganancia, y se descubre midiendo. Y la reconciliación final compara contra los totales de entrada, no contra lo que los workers creen haber hecho.

## Reinicio, repetibilidad y calendario

Un batch financiero no termina cuando el proceso devuelve código cero. Debe declarar qué fecha de negocio procesó, qué periodo está cerrado, qué partes están confirmadas, qué se puede repetir y cómo se concilia contra los totales de entrada. Conviene separar reloj técnico de fecha de valor, introducir calendarios de negocio versionados y controlar cambios de horario. En la ejecución nocturna hay días de 23 o 25 horas y procesos que cruzan medianoche. Esas particularidades no aparecen en un ejemplo de cien líneas, pero sí en el cierre contable.

> **Un pipeline con 64 workers no es necesariamente el doble de rápido que otro con 32. Puede ser más lento.**

---

[← Capítulo 19 · Actores: una gran herramienta, un mal sustituto universal](19-actores-una-gran-herramienta-un-mal-sustituto-universal.md) · [Índice](../README.md) · [Capítulo 21 · Event sourcing, CQRS y sagas: cuándo ayudan y cuándo estorban →](21-event-sourcing-cqrs-y-sagas-cuando-ayudan-y-cuando-estorban.md)
