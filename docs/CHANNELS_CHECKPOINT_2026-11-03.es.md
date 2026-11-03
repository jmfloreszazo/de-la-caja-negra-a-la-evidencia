# Checkpoint de canales/core — 3 de noviembre de 2026

Sigue [#30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30), incluido el alcance conservado de #29. Es el primer incremento acotado de canales; #30 sigue abierto. [English](CHANNELS_CHECKPOINT_2026-11-03.md).

## Evidencia nativa original

| Campaña original | Fuente | Resultado y límite |
|---|---|---|
| [41710509139](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41710509139) | `b057a875fc1485ae804222d7035e4d602271bbaf` | FAIL antes de los casos: el helper Python ocultaba el módulo HTTP; la compilación nativa fue correcta |
| [41711114693](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41711114693) | `dd6cbb5c455907d6555fd1196f504be73eadc7eb` | PASS: diez casos, siete grupos de oráculo SQL independiente y dos mutantes rechazados |
| [41711512319](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41711512319) | `1b206b137074c3ab175c4234d8f69780217fbb97` | FAIL antes de los casos: la disponibilidad por socket Unix coincidió con el servidor temporal de inicialización PostgreSQL; se cambió a disponibilidad TCP |
| [41711792802](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41711792802) | `065b82b3b1b6ac2f8b7a1dab0622afbf08719732` | FAIL antes de los casos: puerto HTTP ocupado; la PR del mismo SHA pasó. Se cambió a un puerto libre dentro de un rango loopback acotado, sin terminar procesos ajenos |

Los cuatro ZIP sin modificar están en [evidence/channels](../evidence/channels/). `scripts/check_channel_observations.py` verifica sus SHA-256, cuarenta hashes de fuentes históricas, resultados originales, importes reales y snapshots SQL, y reproduce independientemente los siete grupos de oráculo y ambos mutantes. Una repetición verde no sustituye ninguno de los fallos.

El entorno de la ejecución original correcta fue .NET SDK 10.0.403, Python 3.12.16, Podman 4.9.3 y PostgreSQL 16.13. Dos contenedores comparten un host de GitHub Actions. El informe conserva identidad de imagen resuelta, durabilidad SQL, instrucciones ofrecidas, observaciones HTTP reales, salida del compilador, marcadores de proceso, logs del core/dispositivo y snapshots de ambos almacenes.

## Funcionalidad observada

- Efectivo completo, parcial (solicitados 6.000 / entregados 4.000) y cero final; un efecto financiero al reintentar y rechazo de intenciones cambiadas.
- Proceso del dispositivo terminado externamente tras su commit; UNKNOWN del core y retención persisten hasta conciliar la orden original.
- Proceso del core terminado externamente antes del commit financiero; sus cambios SQL se deshacen mientras sobrevive el resultado separado del dispositivo. El reinicio contabiliza una vez.
- Pérdida real de respuesta por socket tras COMMIT de contabilización/transferencia digital; consulta/reintento resuelven la operación sin otro cargo.
- Peticiones ATM/móvil de 6.000 contra 10.000: una ganadora financiera y una denegada.
- Caducidad sin orden preparada libera; caducidad pendiente y journal ausente conservan UNKNOWN y retención.
- El oráculo independiente rechaza efectivo contabilizado de más conservando el total y una falsa decisión final sin asientos/outbox. Los mutantes alteran copias; los originales permanecen intactos.

El capítulo complementario en ambos idiomas incorpora seis variantes, seis diagramas por edición (dos arquitecturas/cuatro secuencias), decisiones de retirada, compensaciones de patrones, correspondencia con siete oráculos y matriz canal/retirada. Las fuentes primarias distinguen el Bank of Z educativo de IBM, la semántica tarea/UOW de CICS y el ejemplo comercial stand-in de CSFi. No se afirma una arquitectura desplegada en un banco sin identificar.

## Validación pendiente, sin bloquear este incremento

El emulador registra atómicamente inventario y resultado final en SQL del dispositivo. Los billetes físicos no participan en esa transacción. No se ejercitan terminal real, perfil switch/red, homologación ISO 8583/NDC/DDC, HSM/PIN/EMV, transporte autenticado ni plan contable aprobado. Hay cero requisitos de negocio aprobados y ninguna autorización de puesta en producción. Stand-in se deniega por diseño; la política permitida de un emisor real queda fuera. El script inicial todavía no ejecuta una campaña completa de indisponibilidad del core/stand-in.

Para validar externamente, sustituir el supuesto del dispositivo por resultados instrumentados de entrega/retractado/rechazo y journals autoritativos; obtener reglas aprobadas de entrega parcial/nula/caducidad/reverso/disputa y presupuestos delegados; probar saltos de red separados, correlación de protocolo y mensajes tardíos; y ejercitar fencing en origen, corte por cohorte y operadores de recuperación. Preregistrar plazos y resultados esperados, conservar fallos originales y conciliar registros físicos, de red y contables. Capacidad, costes WAN, HA física, aprobación diferencial/Golden Master y el resto de #30/#29 siguen pendientes. La release/versión del libro no cambia.
