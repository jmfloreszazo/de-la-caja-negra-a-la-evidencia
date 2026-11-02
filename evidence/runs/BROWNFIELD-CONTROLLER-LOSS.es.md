# C2 · Pérdida TCP del controlador durante una operación financiera

**Evidencia sintética acotada; 2 de noviembre de 2026. #64/#58 siguen abiertas.**

La [ejecución original #41511782428](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41511782428),
job `125505163428`, ejecutó el protocolo `C2_INFLIGHT_CONTROLLER_TCP_LOSS_V1`
sobre source/checkout `bfa0ed55e5097b6341ac4f9f01e6b4f712d0fb6c`.
La matriz C2 anterior de 20 controles pasó antes del nuevo ensayo separado.

- [ZIP original sin modificar](brownfield-c2-controller-loss-original.zip):
  artefacto `13173950917`, 6494 bytes, SHA-256
  `89fb5b8ba2a2937829ec6f65527524158e321bdb26620e5f027573d51ddaa230`.
- [JSON original extraído sin cambios](brownfield-c2-controller-loss-original.json).
- Hash del ZIP recomputado y coincidente con GitHub; diez hashes de origen
  comprobados contra la implementación ensayada. El ZIP conserva procedencia,
  compilación y resultados anteriores; no se reconstruye a partir de logs.

## Resultados observados

| Observación | Legado Python | Candidato .NET 10 |
| --- | --- | --- |
| Espera financiera independiente antes del corte | PID 543, Lock/advisory en INSERT | PID 685, Lock/advisory en INSERT |
| Sesión del controlador perdida | PID 73 desaparece | PID 109 desaparece |
| Conexiones TCP activas cortadas | 2 | 2 |
| Gateway terminado externamente | SIGKILL, -9 | SIGKILL, -9 |
| Decisión mientras la operación sigue sin COMMIT | UNKNOWN | UNKNOWN |
| Intento de cambiar escritor con incertidumbre | BLOCK | BLOCK |
| Conciliación SQL tras liberar barrera | COMMITTED | COMMITTED |
| Decisiones / apuntes / outbox | 1 / 2 / 1 | 1 / 2 / 1 |
| Oráculos independientes origen/destino | 10/10 y 10/10 | 10/10 y 10/10 |

## Qué demuestra y qué no

El relay cierra sockets TCP activos y rechaza reconexiones; el servidor SQL
confirma que las sesiones previas desaparecen. El trigger de prueba pausa la
transacción después de actualizar cuentas y antes del INSERT/COMMIT: una
sesión independiente observa la espera y todavía no ve decisión persistida.
La operación financiera puede confirmar después de perder su sesión de
control. **Perder un bloqueo remoto no equivale a cancelar el COMMIT.** La
seguridad observada depende del UNKNOWN duradero, del veto al cutover y de
la conciliación antes del replay, que no duplica los efectos.

Son dos casos en un solo runner, con barrera y relay de prueba. No se ensaya
blackhole silencioso, partición asimétrica, todos los límites temporales,
fencing de un CICS/Db2 real, dominios físicos, efectos de pago externos,
capacidad, RTO/RPO o política bancaria aprobada. G2=INCONCLUSIVE; G6=BLOCK.
Los SHA posteriores necesitan su propia CI; este original no los valida.

[English](BROWNFIELD-CONTROLLER-LOSS.md) · [Protocolo reproducible](../../lab/brownfield/journal/README.md)
