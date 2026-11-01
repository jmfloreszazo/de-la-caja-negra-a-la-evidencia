# Convivencia brownfield: trasladar la autoridad, no traducir COBOL

**Estado: experimento propuesto con dos almacenes.** El código está
implementado; solo la ejecución original satisfactoria de GitHub Actions
permite acreditar sus resultados.

## Arquitectura y alcance

El **legado simulado** es un proceso independiente que ofrece un pequeño
contrato de transferencias y consulta de saldos por caja negra, y persiste
en una base PostgreSQL con tablas y columnas distintas. La **nueva
capacidad** es el candidato existente en .NET 10/Npgsql, con *otra*
base y contenedor PostgreSQL. Son libros contables lógicos separados,
pero no dominios físicos independientes, semántica real de CICS/Db2 ni
políticas aprobadas por el cliente.

Una autoridad SQL compartida en el entorno candidato determina el escritor
y la época. Ambos adaptadores *cooperan* y mantienen el bloqueo hasta
confirmar sus propias transacciones. Esto no constituye 2PC: un procesador
legado real que eluda el controlador todavía podría contabilizar después
del cambio.

## Antes de cambiar el escritor

1. Descubrir el comportamiento de cada capacidad y separar las
   observaciones de las políticas expresamente aprobadas. Aquí no existe
   Golden Master real ni mandato del cliente.
2. Ejecutar predicciones *shadow* de solo lectura sin publicar un
   segundo débito ni otro evento outbox. Una réplica desactualizada debe
   producir un desacuerdo visible, no un PASS artificial.
3. Preparar un snapshot SQL consistente del origen en el destino
   todavía no autoritativo, bloqueando el cambio de escritor. Copiar
   versiones de cuentas, operaciones aceptadas y rechazadas, huellas,
   apuntes, outbox y contador de decisiones.
4. Conciliar independientemente las cinco dimensiones del estado y
   ejecutar el oráculo contable en **ambos** almacenes. Rechazar la
   transición ante cualquier diferencia o nueva operación del origen.
5. Incrementar la época de autoridad; el adaptador legado *cooperante*
   debe rechazar los comandos de una época anterior.

## El rollback no es un simple cambio de ruta

Si el candidato ya ha contabilizado nuevas decisiones, el origen mantiene
saldos obsoletos. Volver a dirigir las operaciones allí puede resucitar
datos desactualizados y duplicar contabilizaciones. El laboratorio bloquea
el retorno con `FORWARD_FIX_REQUIRED` cuando ambos estados completos
dejan de coincidir. Un banco real necesita una remediación hacia adelante
aprobada o una migración inversa explícita y verificada, incluidas las
consecuencias en terceros y procesos de liquidación.

| Control adversarial | Resultado exigido |
| --- | --- |
| El legado escribe después del snapshot | CUTOVER BLOQUEADO |
| Falta un evento outbox de destino | CUTOVER BLOQUEADO |
| Llamada del legado con época antigua | FENCED |
| Reintento tras perder una respuesta | Duplicado persistente, sin segundo apunte |
| Escritura nueva del candidato e intento de rollback | CORRECCIÓN HACIA ADELANTE OBLIGATORIA |
| Escritura SQL directa que evita el ACL | Detectada por el oráculo; **no** impedida |

## TODM y garantías todavía pendientes

G0/G1 describen un alcance y procedencia sintéticos. G2 de negocio permanece
`INCONCLUSIVE`. G4 de construcción y G5 de oráculos técnicos solo podrán
acreditarse tras una CI original sobre el SHA exacto. G6 continúa en
**BLOCK**. Quedan pendientes la interrupción entre bases independientes,
journal persistente de resultados inciertos, bloqueo real del lado IBM Z,
CDC y orden de eventos, dominios de fallo separados, evidencias de RPO/RTO,
SLA operativos y aprobación humana en la [issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).

Código, pruebas y [README reproducible](../lab/brownfield/coexistence/README.md)
solo en inglés; texto de investigación emparejado en español e inglés.
Sin modificar versión ni etiquetas de release.
