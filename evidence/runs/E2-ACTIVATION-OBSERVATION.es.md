# E2 · Intervalos de llamadas por activación y efectos persistentes

**Dos observaciones acotadas auditadas, 3 de noviembre de 2026; E2 sigue parcial.**

[Ejecución original #41619587080](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41619587080),
código/checkout `362ee5a7537e1523caad2bd7033ec7a99977ac2d`.
El host observador separado referencia el grain financiero y ledger sin cambios.
Registrar afecta a los tiempos: estos resultados describen ese host, no los anteriores.

| Observación | Salida del primario bloqueada | Salida del secundario bloqueada |
| --- | --- | --- |
| Trabajo / artefacto original | 125861600757 / 13223905279 | 125861600090 / 13223137998 |
| Bytes ZIP / hashes de código auditados | 39139 / 77 | 39919 / 77 |
| Generaciones de proceso/contenedor registradas | 4 | 4 |
| Intervalos completos de llamadas Transfer | 38 | 39 |
| Intervalos incompletos / pares candidatos no comparables | 0 / 0 | 0 / 0 |
| Solapamientos entre activaciones distintas del mismo grain | 0 | 0 |
| COMMITTED / DUPLICATE_COMMITTED / ID_CONFLICT | 3 / 30 / 5 | 3 / 30 / 6 |
| Modo de recuperación | Recreación de ambos silos | Recreación de ambos silos |
| Criterios de recuperación tras retirar la regla, segundos | 60,578 | 57,816 |
| 14 parejas de replay: intervalo real, segundos | 66,334 | 66,043 |
| Operaciones / asientos / outbox finales; invariantes SQL | 3 / 6 / 3; 7/7 | 3 / 6 / 3; 7/7 |

Los cortes programados duraron 120,000119 y 120,000090 segundos. El plazo no
demuestra que ambos silos siguieran vivos durante todo ese tiempo. Cada caso
usó **un solo host físico**. Todos los ACK tienen un resultado completo
compatible registrado y coinciden con SQL; ambos casos conservaron el importe 37.

Los logs completos se conservaron antes de eliminar cada contenedor antiguo
o nuevo. Incluyen ID real de activación Orleans, grain/llamada, sesión y
secuencia por proceso, payload/resultado, reloj monótono/frecuencia, boot ID
y namespace temporal. Las cuatro sesiones distintas por caso distinguen los
PID 1 repetidos dentro de los contenedores. Arranque del kernel, namespace y
frecuencia coincidentes permiten comparar relojes dentro de cada caso.
El observador disponible en una generación ociosa no acredita llamadas financieras.

**No se observó un caso positivo de activaciones concurrentes.** Los 38/39
intervalos completos no muestran solapamientos entre activaciones distintas
del mismo grain. Eso no acredita exclusividad global, vida completa de una
activación, ausencia de split brain ni de llamadas no observadas. Incluso un
solapamiento positivo del filtro no mediría ejecución SQL simultánea.
La siguiente condición de #24 sigue siendo un caso positivo dirigido de
activaciones concurrentes con aceptación SQL independiente. Siguen pendientes
#25, capacidad sostenida y dominios físicos independientes.

## Bytes originales y reproducción

- [ZIP primario](e2-activation-primary-original.zip) / [resumen idéntico en bytes](e2-activation-primary-original.json): SHA-256 `9ffb4ef62e7ee040a139490b3dc3dc6df46fdeff6fedbfd9a07a5b92b1213e62`.
- [ZIP secundario](e2-activation-secondary-original.zip) / [resumen idéntico en bytes](e2-activation-secondary-original.json): SHA-256 `84ee1d79ed0021dc7fb9c3e7a81f270c78076bee7ccaddd3631f5c80d5470368`.

El [auditor offline](../../scripts/check_e2_activation_observations.py) fija
los hashes de ambos ZIP, contrasta los 77 hashes con el commit original,
recalcula intervalos de logs, reconcilia resultados y ACK con SQL, comprueba
la recuperación muestreada y analiza los PCAP originales. No extrae ni reescribe ZIP.

G2 INCONCLUSIVE/G6 BLOCK; #53 congelado; sin cambio de release ni etiqueta.

[English](E2-ACTIVATION-OBSERVATION.md) · [Protocolo](../../lab/e2_activation_observer/README.md)
