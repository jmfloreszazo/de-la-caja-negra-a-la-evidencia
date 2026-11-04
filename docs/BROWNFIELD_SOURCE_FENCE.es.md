# Brownfield CAP-007/005: demostrar la autoridad del origen antes del cutover

**Estado: contrato de ingeniería y evaluación estructural, NO prueba ejecutada de fencing sobre el sistema legado real.** [English](BROWNFIELD_SOURCE_FENCE.md) · [Issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58). Nuestro C2 sintético dispone de un controlador y de almacenes PostgreSQL separados para legacy y candidato, con adaptadores que **cooperan**. Esto **no** acredita que podamos retirar la capacidad de escritura a un CICS/IMS real, una actualización Db2/VSAM, un batch, una oficina desconectada, un reintento asíncrono o un procesador externo de pagos.

## 1. «Un solo escritor» se aplica a todos los caminos, no únicamente al gateway

La frontera de autoridad incluye **toda entrada capaz de confirmar, repetir, contabilizar o provocar un efecto irreversible**, no solo el canal web. Una operación puede llegar al libro mayor desde una transacción online, el cierre nocturno, un switch ATM/POS, una oficina, una cola de ficheros, un scheduler, herramientas de operador o SQL privilegiado. La siguiente tabla es una **lista para descubrir**, no una afirmación de que un banco concreto use todas esas tecnologías. El cliente debe demostrar cuáles son aplicables.

| Familia del inventario | Evidencia que hay que obtener del origen | Riesgo si se omite |
| --- | --- | --- |
| `online_legacy` | CICS, IMS u otras transacciones online; enrutamiento y COMMIT real | El core antiguo sigue contabilizando tras cambiar la ruta |
| `batch_scheduler` | JCL, planificador, cierres diarios/mensuales, procesos diferidos | El batch reabre autoridad antigua de madrugada |
| `channels` | ATM/POS, móvil, web, oficina/back-office y frontera de posting | Un reintento de canal genera un segundo efecto |
| `branches_offline` | Store-and-forward, colas locales, reconexión y épocas | Se entrega una orden de una época antigua tras la promoción |
| `asynchronous_replay` | MQ, CDC, ficheros, DLQ, duplicados y secuenciación | Reproceso con doble apunte o fuera de época |
| `privileged_operations` | Correcciones manuales, utilidades, acceso directo Db2/SQL y recuperación | Un bypass privilegiado invalida el fencing |
| `external_effects` | Settlement, red de pagos, efectivo, procesador externo, outbox | Revertir el ledger local no revierte un pago externo |

Cada familia debe clasificarse como `UNKNOWN`, `IN_SCOPE` o `OUT_OF_SCOPE`. La exclusión exige evidencia del responsable del origen; **no** se puede asumir por defecto. Para cada familia incluida se necesita inventario, fencing **impuesto en el origen**, reconciliación de operaciones en vuelo/UNKNOWN, repetición idempotente, conciliación del ledger y de efectos externos. Si no hay efectos externos, esa ausencia también debe estar justificada y revisada.

## 2. Qué tenemos que implementar realmente en la infraestructura del cliente

### A. Control de admisión y revocación del origen

El **procesador que puede confirmar la transacción** —o una frontera que no pueda eludir— debe comprobar la autorización para escribir antes de aceptar un nuevo CAP-007. Un interruptor del API Gateway no sirve cuando batch y aplicaciones internas pueden escribir por otros caminos. La revocación debe ser duradera, ordenada, observable y aplicable a todos los actores. Un token/epoch no basta si una operación antigua ya dispone de una conexión capaz de confirmar un COMMIT después del cambio.

El responsable de la plataforma deberá estudiar qué mecanismo real admite el sistema: bloqueo de admisión transaccional, desactivación controlada de determinadas transacciones CICS/IMS, guardas verificadas en Db2/VSAM, drenaje coordinado u otras alternativas. **No son opciones equivalentes**, ni se presupone una transacción XA/2PC global entre mainframe y PostgreSQL. Documentar la frontera exacta de COMMIT/visibilidad y las herramientas privilegiadas capaces de eludir el control.

### B. Cesión segura de autoridad y versión/epoch

1. Acotar la **capacidad y cohorte de cuentas** junto con moneda, fecha valor, ID estable de operación y reglas aprobadas.
2. Inventariar online, batch, colas, ficheros, offline y accesos privilegiados. Bloquear nuevas entradas en **todas** las rutas del origen incluidas en la migración, con procedimiento de recuperación.
3. Persistir la intención del corte, localizar operaciones admitidas y todos los `UNKNOWN`. El candidato **no** puede escribir mientras no conste un fencing efectivo e independiente del origen.
4. Drenar, resolver o reconciliar operaciones del origen ya iniciadas y efectos externos. **Ausencia de ACK no es prueba de ROLLBACK**. Para colas de sucursal desconectadas, definir validación de versión/epoch, rechazo o transformación segura de órdenes tardías mediante política aprobada.
5. Preparar y conciliar saldos, decisiones, postings, outbox, eventos pendientes y marcas de agua. Un snapshot aislado no vale sin frontera consistente de captura/CDC y catch-up.
6. Activar el candidato **una sola vez**, únicamente tras revocar la autoridad del legacy y superar el gate de conciliación; registrar el epoch efectivo y la evidencia independiente.
7. No afirmar COMMIT atómico entre almacenes. Tras nuevas decisiones del candidato, volver al origen es **otra migración**, con catch-up, fencing y conciliación; no un cambio de bandera.

Si no podemos acreditar el fencing, la salida correcta es extraer una capacidad/cohorte menor o **mantener el legacy como único escritor** mientras creamos proyecciones de lectura. Nunca activar los dos escritores financieros para comparar resultados.

### C. Golden Master, TODM y responsabilidades

- Un **Golden Master observado** describe el comportamiento existente; también puede capturar errores o reglas obsoletas. Mantenerlo separado de la **política funcional intencionada y aprobada**.
- Recoger trazas autorizadas y minimizadas: petición, respuesta, decisiones, ledger, settlement, efectos físicos, auditoría, fecha, versión y procedencia; nunca depositar datos financieros reales del cliente en un repositorio público.
- TODM G2 permanece `INCONCLUSIVE` hasta aprobar baseline y excepciones por la autoridad de negocio. G5 necesita oráculos independientes con mutaciones negativas; G6 sigue en `BLOCK` hasta la autorización explícita sobre SHA, entorno y evidencias exactas.
- Una URI y un SHA escritos en un cuestionario **no prueban** la autenticidad del archivo, una firma válida ni el permiso del responsable. El validador estructural no concede G2 ni G6.

## 3. Matriz de fallos y contraejemplos obligatorios

| Caso | Incidente que debemos reproducir | Resultado y evidencia exigidos |
| --- | --- | --- |
| F01 | Llega una transferencia online antigua después de cambiar el escritor | El origen la rechaza **antes del COMMIT** y no altera contabilización/efectos |
| F02 | Arranca el batch nocturno con programación antigua | Ruta de escritura bloqueada o redirigida de forma segura, sin posting oculto |
| F03 | Una oficina offline se reconecta y reenvía un ID antiguo | Se respeta política/epoch, sin duplicación ni COMMIT tardío ilegal |
| F04 | Origen confirma COMMIT, pero se pierde respuesta del gateway/controlador | `UNKNOWN` hasta reconciliación independiente; nunca asumir rollback |
| F05 | Caída entre el fencing del origen y la activación del candidato | Intención duradera y recuperación sin doble autoridad |
| F06 | Candidato confirma COMMIT, pierde ACK; se reenvía mismo ID y payload distinto | Replay idempotente; conflicto rechazado; postings/outbox exactos |
| F07 | Una utilidad privilegiada intenta escribir saltándose el gateway | Debe impedirse en el origen o provocar fallo explícito que **bloquea el corte** |
| F08 | Salió instrucción de pago/efectivo, llega respuesta tardía o duplicada | Conciliar referencias externas, compensaciones y settlement, no solo SQL local |
| F09 | Snapshot y watermark de CDC/ficheros discrepan | El origen continúa autoritativo; G6 BLOCK |
| F10 | Se solicita rollback tras nuevos commits del candidato | Prohibir cambio simple; exigir nueva migración reconciliada |
| F11 | Operador desactiva el controlador o reenvía un epoch anterior | Rechazo en todas las entradas legacy/candidato; logs conservados |
| F12 | Partición de red/host y restauración posterior | Solo afirmar HA/RPO/RTO con dominios físicos y evidencias reales |

Cada caso requiere SHA/versiones de origen y destino, comandos, relojes e incertidumbre, logs originales, trazas de transacción en origen (o equivalente autorizado), SQL independiente del candidato, outbox/settlement, controles negativos e intentos fallidos. Cuando no se dispone de evidencia del origen, el resultado es `INCONCLUSIVE`, nunca PASS. Los artefactos del cliente se almacenan de manera segura y bajo acuerdo de retención; el repositorio público solo podrá guardar identificadores o extractos expresamente autorizados.

## 4. Entregable implementado: inventario con bloqueo por defecto

Código y pruebas (en inglés): [`lab/brownfield/owner_readiness/`](../lab/brownfield/owner_readiness/README.md).

```bash
python3 -m unittest discover -s lab/brownfield/owner_readiness -p "test_*.py" -v
python3 lab/brownfield/owner_readiness/assess.py \
  lab/brownfield/owner_readiness/intake.example.json
# Resultado intencionado: NOT_READY, exit 2. Es correcto sin datos de cliente.
```

La herramienta comprueba **estructura y completitud** de las declaraciones: siete familias de escritura, pruebas obligatorias, referencias y formato de hashes. Rechaza un `todmG6=PASS` autodeclarado, inventario duplicado, exclusiones sin justificación, falta de prueba de fencing y digest mal formado. Incluso un expediente rellenado artificialmente alcanza **solo `READY_FOR_INDEPENDENT_REVIEW`**.

**No descarga los archivos**, no verifica firmas ni inspecciona CICS/IMS/Db2, no ejecuta transferencias ni certifica un Golden Master y no autoriza producción. Es una herramienta de preparación tipo G0/G1; no un motor de aprobación de negocio. Las pruebas originales C2 y sus SHA no se modifican.

## 5. Secuencia de aceptación y estados auténticos

| Etapa | Responsable real | Entregable de aceptación | Estado actual |
| --- | --- | --- | --- |
| Descubrimiento de todos los escritores y reglas | Propietarios del sistema origen | Rutas verificadas, calendario batch y exclusiones firmadas | **UNKNOWN** |
| Fencing efectivo impuesto por el legacy | Equipo mainframe, datos y seguridad | Prueba negativa que impida el bypass y concilie in-flight | **NO DEMOSTRADO** |
| Reconciliación de efectos financieros/externos | Finanzas, ledger y operadores de pago | Operaciones, postings, outbox, settlement y efectivo independientes | **NO DEMOSTRADO** |
| Golden Master y políticas | Propietario del negocio + revisor de oráculo | Contrato funcional aprobado, contraejemplos y excepciones | **SIN APROBAR** |
| Decisión final de transición | Revisores independientes y autoridad de release | Campaña completa y decisión G2/G5/G6 | **G2 INCONCLUSIVE / G6 BLOCK** |

Este incremento **no cierra el issue #58**: el fencing real, las pruebas físicas y la aprobación funcional pertenecen al cliente y siguen pendientes. No autoriza releases, cambios de producción ni equivalencia MIPS/mainframe. La [evidencia C2 sintética original](../evidence/runs/BROWNFIELD-CONTROLLER-PARTITION.es.md) explica exactamente qué se comprobó en el runner y qué no.
