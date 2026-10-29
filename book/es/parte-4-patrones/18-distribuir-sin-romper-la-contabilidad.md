**Español** · [English](../../en/part-4-patterns/18-distributing-without-breaking-the-books.md)

[← Capítulo 17 · De los locks del mainframe al control explícito de concurrencia](17-de-los-locks-del-mainframe-al-control-explicito-de.md) · [Índice](../README.md) · [Capítulo 19 · Actores: una gran herramienta, un mal sustituto universal →](19-actores-una-gran-herramienta-un-mal-sustituto-universal.md)

# Capítulo 18 · Distribuir sin romper la contabilidad

> [!IMPORTANT]
> **Tesis del capítulo.** Mantener una frontera transaccional fuerte puede simplificar mucho. Si la distribuimos, compensar tiene significado de negocio, publicar exige outbox y un propietario antiguo debe ser rechazado por el destino, no por cortesía.

## Mantener una frontera fuerte puede simplificar mucho

Mi primera alternativa para una capacidad que necesita atomicidad sería estudiar si sus escrituras pueden permanecer en una transacción de un mismo motor. La aplicación puede tener varias instancias y el núcleo contable seguir concentrando la decisión de commit. Eso limita una clase de escalabilidad y evita otra clase de coordinación distribuida.

Un monolito modular puede ser un destino inicial razonable. Permite recuperar límites internos antes de multiplicar viajes de red y propietarios de datos. No lo elegiría por nostalgia ni lo descartaría por llevar una etiqueta antigua. Lo evaluaría contra la carga, los cambios previstos y las garantías necesarias.

Si la unidad original confirma varios recursos, hay que decidir si conservamos coordinación distribuida compatible o rediseñamos el protocolo. Db2 documenta coordinación en dos fases para determinados participantes [20]. Sustituirla por una saga cambia el modelo de consistencia y debe pasar por la autoridad de negocio.

## Compensar tiene un significado de negocio

Una saga organiza pasos y acciones compensatorias. No convierte esos pasos en un rollback invisible. Una transferencia observada, una notificación enviada o una conversión aplicada pueden exigir tratamientos específicos. Durante la compensación existe un estado que otros participantes podrían observar.

Un protocolo de reservas puede proteger el disponible antes de completar el movimiento. Debe definir caducidad, confirmación, liberación, recuperación y quién puede resolver una operación dudosa. La reserva también se vuelve un recurso que consume capacidad y necesita reconciliación.

Si el contrato exige que débito y crédito sean inmediatamente atómicos para los observadores relevantes, no aceptaría una saga por la comodidad de desplegar dos servicios. Buscaría una frontera de datos o un mecanismo transaccional que conserve esa propiedad.

## Publicar después del commit sin perder el evento

La outbox permite guardar la intención de publicar junto con el cambio de negocio en una misma transacción local. Un publicador posterior entrega el evento y registra su avance. Eso evita la ventana en la que confirmamos la operación y olvidamos generar la notificación, siempre dentro de los recursos realmente incluidos en esa transacción.

Aun así, el publicador puede enviar el mensaje y fallar antes de marcarlo como enviado. El consumidor debe tolerar una repetición. Microsoft describe este patrón con entrega al menos una vez e idempotencia en el consumidor [21]. La deduplicación del broker puede ayudar dentro de sus límites; la identidad de negocio debe sobrevivir a la ventana de retención y a la recuperación que hayamos acordado.

![Figura 18.1 · Outbox con entrega al menos una vez: el publicador puede repetir, el consumidor deduplica por identidad de negocio.](../../figures/es/outbox_seq.png)

*Figura 18.1 · Outbox con entrega al menos una vez: el publicador puede repetir, el consumidor deduplica por identidad de negocio.*

En el laboratorio comprobamos que cada transferencia confirmada genera su fila outbox de manera atómica. No ejecutamos un publicador remoto ni demostramos entrega a un broker. Esa extensión requiere otra prueba: caer antes y después del envío, repetir mensajes y reconciliar recepción con efectos aplicados.

## Protegerse de un propietario antiguo

Cuando un proceso conserva un permiso temporal y pierde conectividad, otro puede asumir el trabajo. El antiguo puede volver y seguir intentando escribir. Confiar únicamente en que todos respeten una marca en memoria resulta insuficiente.

Una técnica es asociar una época o token creciente a la propiedad y exigir que el recurso rechace escrituras de propietarios anteriores. Su utilidad depende de que el almacén que recibe el cambio compruebe realmente ese token. Un bloqueo distribuido consultado por la aplicación no modifica automáticamente las garantías de la base de datos.

Esta es una de las decisiones que pondría en un ADR: dónde reside la autoridad de escritura, qué ocurre al expirar y qué evidencia demuestra que un propietario obsoleto no puede confirmar efectos.

La técnica de las épocas se entiende mejor en dos sentencias. El destino es quien la aplica: un lote que perdió su lease puede seguir vivo, pero sus escrituras dejan de confirmarse.

**Listado 18.1 · Fencing: el almacén rechaza escrituras de un propietario obsoleto** — *Ilustrativo*

```sql
-- Toma de propiedad: la época crece y solo se concede si el lease anterior caducó.
UPDATE dbo.PartitionLeases
   SET Owner = @Worker, Epoch = Epoch + 1,
       ExpiresUtc = DATEADD(second, 30, SYSUTCDATETIME())
OUTPUT inserted.Epoch
 WHERE PartitionId = @Partition AND ExpiresUtc < SYSUTCDATETIME();

-- Cada escritura lleva la época obtenida. HOLDLOCK impide que el relevo
-- se confirme mientras esta escritura está en curso.
INSERT dbo.BatchResults (PartitionId, Epoch, AccountId, Amount)
SELECT @Partition, @Epoch, @AccountId, @Amount
 WHERE EXISTS (SELECT 1 FROM dbo.PartitionLeases WITH (HOLDLOCK)
                WHERE PartitionId = @Partition AND Epoch = @Epoch);
-- 0 filas insertadas: este worker ya no es el dueño. Debe detenerse, no reintentar.
```

![Figura 18.2 · Fencing: un propietario obsoleto puede seguir vivo, pero el almacén deja de confirmar sus escrituras.](../../figures/es/fencing_seq.png)

*Figura 18.2 · Fencing: un propietario obsoleto puede seguir vivo, pero el almacén deja de confirmar sus escrituras.*

> **Una saga no es un rollback invisible. Si el contrato exige atomicidad inmediata, no se cambia por comodidad de despliegue.**

---

[← Capítulo 17 · De los locks del mainframe al control explícito de concurrencia](17-de-los-locks-del-mainframe-al-control-explicito-de.md) · [Índice](../README.md) · [Capítulo 19 · Actores: una gran herramienta, un mal sustituto universal →](19-actores-una-gran-herramienta-un-mal-sustituto-universal.md)
