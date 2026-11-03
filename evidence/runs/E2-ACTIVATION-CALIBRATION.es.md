# E2 · Calibración positiva real del observador de activaciones

**Solo calibración; sigue abierta la concurrencia del AccountGrain normal bajo partición.**

[Ejecución original #41630777280](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41630777280),
trabajo 125899472499, código/checkout exacto `75dfccb8513d38f7fa70386be47c64014a981996`.
Se añade un grain de diagnóstico separado con `StatelessWorker(maxLocalWorkers: 2)`
y una barrera acotada de dos participantes antes del ledger. Ese tipo de prueba
permite deliberadamente varias activaciones. El AccountGrain y ledger aceptados no cambian.

| Caso original | Observación real | Efecto SQL persistente |
| --- | --- | --- |
| Una petición, proceso/base nuevos | Timeout esperado en la barrera; un BEGIN/ERROR; cero solapamientos | 0 operaciones / 0 asientos / 0 outbox; 7/7 invariantes |
| Dos peticiones, proceso/base nuevos | Dos IDs reales de activación distintos, misma clave de diagnóstico; solapamiento de 197,293967 ms | 1 operación / 2 asientos / 1 outbox; 7/7 invariantes |
| Replay / payload diferente | DUPLICATE_COMMITTED / ID_CONFLICT | Sin efectos adicionales |

El ID disputado confirmó el importe 37; el importe 31 recibió ID_CONFLICT.
Las cuentas, asientos y outbox coinciden independientemente con el ganador.
El comprobador offline también reconcilia las respuestas originales con SQL.
El negativo comprueba sensibilidad; no es un fallo accidental de infraestructura.

El [resumen versionado](e2-activation-calibration-original.json) reproduce el
JSON exacto que el driver original escribió en stdout y `summary.json`.
Identidad del blob Git: `0c65ed626a5edbf211116235ef3b673b10819751`.
La [auditoría offline](../../scripts/check_e2_activation_calibration.py) fija
esos bytes, contrasta los 39 hashes con el commit original, recalcula intervalos
de logs y comprueba independientemente cada fila persistente y ACK.
El artefacto CI completo 13228386871 ocupa 15771 bytes; GitHub informa SHA-256
del ZIP `a0a52f20d7a417a677a8a8b8b39daea75c2688c30bf9a9d85bf9c82e58a9e6c8`.
Se registran sus metadatos; aquí no se afirma una auditoría de los bytes del ZIP.

Es un silo/proceso sobre un host físico, con cliente Orleans dentro del proceso
y PostgreSQL desechable. El solapamiento mide llamadas, no COMMIT SQL simultáneo
ni capacidad. Calibra la detección de activaciones de diagnóstico reales y
deliberadamente múltiples. No demuestra activaciones concurrentes del AccountGrain
normal durante C05/F10, split brain natural, exclusividad del actor, HA física
ni aceptación bancaria. E2 sigue parcial.

[English](E2-ACTIVATION-CALIBRATION.md) · [Protocolo](../../lab/e2_activation_calibration/README.md)
