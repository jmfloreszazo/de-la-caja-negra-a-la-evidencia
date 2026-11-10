**Español** · [English](../../en/annexes/annex-i-evidence-campaigns-and-limits.md)

[← Anexo H · Más allá de COBOL](anexo-h-mas-alla-de-cobol.md) · [Índice](../README.md)

# Anexo I · Campañas de evidencia y límites de validación

Quiero que los capítulos cuenten qué problema encontré, qué decisión tomé y qué podría refutarla. Aquí dejo la otra mitad: el expediente de las campañas. No convierto resultados inconclusos en PASS ni escondo los fallos iniciales para que la narración quede más limpia.

Cada resultado pertenece a una versión, un host y un contrato experimental. Dos contenedores no son dos centros de datos, y SQL durable no es homologación bancaria. El relato está en [canales](../parte-4-patrones/21a-canales-atm-y-core.md) y [transferencias](../parte-6-laboratorio/28-transferencias-bloqueos-y-fallos-en-local.md); este expediente conserva la procedencia.

## I. Canales: efectivo, fallos y transporte

### 7. Advice tardío, reversos y efectivo: una correlación no es una autorización

Consideremos una retirada autorizada por 100,00 unidades monetarias: el dispositivo acredita que entregó **60,00**, pero el switch todavía conserva un advice con el importe solicitado de 100,00. El ledger registra 60,00 y aparece después una solicitud de reverso íntegro. Es incorrecto inferir automáticamente «cargo 100» o «abono 100»: hace falta identificar qué dinero fue físicamente accesible, qué cargo se confirmó, qué mensaje es una solicitud y quién puede resolver la discrepancia. Una petición de reverso no equivale a un reverso asentado.

El [dossier de investigación ES](../../../docs/research/channel-late-advice.es.md) ([EN](../../../docs/research/channel-late-advice.en.md)) contrasta este riesgo con las guías públicas de disputas ATM y reglas de stand-in. El [oráculo forense de canales](../../../lab/channels/advice_gate.py) añade una prueba **sintética, puramente local** que compara cuatro instrucciones y sus observaciones sin modificar ninguna base de datos:

| Caso sintético | Resultado correcto del oráculo | Lo que nunca permite |
| --- | --- | --- |
| Dispensación de 60 sobre autorización de 100; advice idéntico repetido | `MATCHED_PARTIAL_CASH` | Duplicar asientos o dispensación |
| Dispensador sin resultado definitivo; mensaje de red de importe 80 | `UNKNOWN_REQUIRES_DEVICE_EVIDENCE` | Convertir advice en prueba física o en cargo |
| Diario físico confirma cero, con solicitud de reverso tardía | `FINAL_ZERO_CASH` | Suponer contabilizado el reverso solicitado |
| El core no responde y no existe delegación de autorización | `STAND_IN_DENIED` | Crear un autorizador alternativo por su cuenta |

Para correlacionar no basta con STAN o RRN: hay que conservar el **ID duradero de operación**, autorización, terminal, contexto de red y encarnación de origen. Un STAN puede reutilizarse; dos mensajes con el mismo identificador de transmisión y diferente contenido son una contradicción, no un reintento idempotente. Un reverso solicitado después de una entrega parcial exige revisión explícita y oráculos que permitan detectar un abono falso.

No se introduce una nueva implementación de ISO 8583 ni un emulador de cajero certificado. El nuevo control utiliza datos inventados; **no comprueba autenticidad de journal físico, políticas del emisor, reconciliación de esquemas ni operaciones bancarias reales**. Complementa las diez pruebas nativas anteriores de .NET 10/PostgreSQL, pero no reutiliza sus resultados como evidencia de protocolos de tarjeta. Incluso si sus casos Python pasan, no autoriza de forma automática dispensar, contabilizar o revertir y conserva **TODM G2 INCONCLUSIVE / G6 BLOCK**.

### 8. No existe un único «fallo de red»: localizar el salto y la decisión

En una retirada, el mismo mensaje «timeout» puede esconder estados opuestos. Si se corta el **enlace ATM→switch** antes de la entrega, no tenemos una autorización demostrada. Si falla **switch→core** antes de llegar al emisor, el switch carece de permiso para inventar un saldo o dispensar. Si el core hizo COMMIT y solo perdió la **respuesta**, repetir la instrucción con un nuevo ID puede duplicar efectos. El camino de recuperación empieza consultando el estado **con el identificador original** en la autoridad que realmente tomó la decisión; una respuesta positiva no confirma la entrega física.

El [dossier ES sobre saltos y fallos](../../../docs/research/channel-hop-failures.es.md) ([EN](../../../docs/research/channel-hop-failures.en.md)) añade un oráculo de siete trazas ficticias y cuarenta controles adversariales. Complementa las pruebas de dispensación parcial y mensajes tardíos del apartado anterior, sin introducir un segundo simulador de core.

| Escenario | Dictamen del oráculo sintético | Acción que bloqueamos |
| --- | --- | --- |
| H01: ATM→switch sin entrega | `NO_CORE_AUTHORIZATION_EVIDENCE` | Presentar timeout como rechazo confirmado o éxito |
| H02: switch→core sin entrega | `NO_CORE_AUTHORIZATION_EVIDENCE` | Pasar a *stand-in* sin delegación |
| H03: COMMIT del emisor, ACK perdido y consulta tras recuperar el enlace | `AUTHORIZATION_RECOVERED_BY_STATUS` | Nueva autorización con otra identidad; asumir efectivo |
| H04: autorización y comando al dispositivo, enlace ATM↔switch caído | `CASH_UNKNOWN_NO_REDISPENSE` | Reenviar DISPENSE mientras falta journal |
| H05: respuesta de propietario antiguo tras cambio de época | `QUARANTINED_OLD_OWNER_REPLY` | Dar al antiguo host permiso para contabilizar |
| H06: efectivo parcial y ledger sintéticos coincidentes | `PARTIAL_CASH_RECONCILED_SYNTHETICALLY` | Confundir fixture con prueba física |
| H07: switch sin core solicita stand-in no delegado | `STAND_IN_DENIED` | Crear crédito o dispensación offline |

**Un cambio de ruta no es fencing.** Para mover de verdad el escritor de una capacidad del host a .NET/SQL hay que demostrar que el antiguo host **ya no puede confirmar la misma instrucción**, incluso por batch, privilegios o tareas offline. El `sourceEpoch` que etiqueta estos eventos de laboratorio es una señal de correlación, no un candado criptográfico ni una prueba de revocación del propietario anterior.

Tampoco debemos trasladar directamente la semántica de CICS a HTTP: una tarea CICS puede tener varios *syncpoints* y la atomicidad se limita a sus recursos recuperables. La autorización de red y el dinero físico viven en otras fronteras. Véanse [syncpoints y UOW de CICS](https://www.ibm.com/docs/en/cics-ts/6.x?topic=work-synchronization-points) y la [guía de fallos transitorios de Azure](https://learn.microsoft.com/en-us/azure/architecture/best-practices/transient-faults).

El [oráculo Python](../../../lab/channels/network_fault_gate.py) **solo analiza eventos declarados en JSON**: no corta sockets, no ejecuta ISO 8583, no consulta al emisor ni escribe un asiento. Un PASS valida coherencia de una maqueta, no garantías de la red. Una aceptación real exige pérdidas y reconexiones instrumentadas por separado, logs nativos de COMMIT, identidad de reintento, journal físico, conciliación y aprobación del negocio. **Ningún resultado del fixture autoriza automáticamente una retirada, reverso, asiento, corte de escritor o stand-in.** TODM G2 `INCONCLUSIVE`, G6 `BLOCK`.

### 9. Primera prueba de transporte real: TCP local y COMMIT del core

Las pruebas anteriores de H01–H07 describían enlaces caídos mediante eventos JSON. El siguiente escalón experimental utiliza **sockets TCP reales en loopback**: un proxy efímero recibe la petición HTTP del cliente, la interrumpe o la reenvía al API **.NET 10** existente y observa la respuesta. El core escribe en PostgreSQL, mientras un oráculo Python independiente revisa sus tablas y el almacén de dispositivo. Son **procesos y sockets reales**, pero siguen ejecutándose en un único host; no es una partición física entre sucursales, switch y mainframe.

| Prueba de transporte | Intervención real | Qué comprueba el oráculo |
| --- | --- | --- |
| Solicitud descartada antes de reenviar | El proxy acepta el socket y envía TCP reset **sin abrir conexión al core** | SQL original vacío antes de la recuperación; con el mismo ID, una sola transferencia |
| Respuesta descartada después del COMMIT | El proxy reenvía la solicitud, lee HTTP 200 **emitido tras `CommitAsync`** y resetea el socket del cliente sin entregarle la respuesta | Cliente `UNKNOWN` mientras SQL ya contiene un COMMIT, dos apuntes y un outbox; consulta de estado y reintento con el mismo ID, sin segundo efecto |
| Respuesta retrasada más allá del timeout | Se retrasa 0,8 s la respuesta posterior al COMMIT; timeout real de cliente de 0,15 s | El cliente ve timeout, pero la consulta del propietario revela la decisión original y no aparece otro asiento |

Los tres casos son **transferencias digitales ficticias**, no retiradas físicas de efectivo. Conservan los diez escenarios nativos anteriores: efectivo parcial, fallo tras COMMIT, procesos eliminados con `SIGKILL`, concurrencia ATM/móvil y sus oráculos. El [protocolo ES](../../../docs/research/channel-loopback-transport.es.md) ([EN](../../../docs/research/channel-loopback-transport.en.md)) identifica los puertos, la forma de repetir las pruebas, las 14 comprobaciones de seguridad del proxy y los 18 controles positivos/adversariales que inspeccionan evidencias originales sin modificar las bases.

**Una observación de timeout no es prueba de que no hubo COMMIT.** El caso de petición no reenviada solo dispone de esa garantía adicional porque **nuestro proxy controlado atestigua que no abrió un socket al servidor y SQL está vacío**. En redes bancarias reales esta observación independiente no estará disponible necesariamente. El mismo `operationId` es indispensable para consultar estado y, cuando la política lo permita, reintentar sin inventar otra transacción.

El nuevo incremento permite medir **interrupciones reales de TCP locales** frente al commit SQL duradero. **No** implementa `tc netem`, pérdidas WAN entre máquinas, ISO 8583, CICS ni journal físico de dispensación; tampoco mide MIPS o capacidad. El libro mantiene el patrón de **un propietario financiero y varios canales**, y la aceptación del cliente exige todavía firmas, políticas, trazas reales, writer fencing y pruebas con dominios físicos independientes. **G2 INCONCLUSIVE, G6 BLOCK**, sin permiso de cortar el sistema del banco.

### 10. Respuesta retenida frente a ocho recuperaciones concurrentes

En el laboratorio anterior perdíamos o retrasábamos un ACK y, después, consultábamos al core. Quedaba sin probar una situación frecuente en arquitecturas de canales: **la respuesta original todavía está en tránsito cuando otros clientes intentan recuperar simultáneamente la operación**. No basta con probar un único reintento secuencial.

El [protocolo de investigación ES](../../../docs/research/channel-held-ack.es.md) ([EN](../../../docs/research/channel-held-ack.en.md)) introduce una barrera determinista **sobre sockets TCP locales reales**. El proxy entrega el `POST /transfer` original al API .NET 10 y lee su HTTP 200 posterior al COMMIT en PostgreSQL, pero retiene la respuesta. El cliente recibe un timeout real. Antes de liberar el ACK antiguo, el driver consulta el estado autoritativo de la maqueta y dispara **ocho clientes concurrentes con el mismo `operationId` y fingerprint**. Una novena petición con el mismo ID y otro importe debe rechazarse.

| Frontera | Evidencia observable | Oráculo exigido |
| --- | --- | --- |
| Emisor ficticio | Un COMMIT confirmado; se mantiene retenido el HTTP 200 | Una operación, dos apuntes y un outbox antes de cualquier reintento |
| Cliente inicial | Timeout y estado `UNKNOWN` | No crear otra identidad financiera |
| Ocho clientes concurrentes | Ocho respuestas `COMMITTED` con `duplicate=true` | Una sola decisión persistente; ningún nuevo cargo |
| Petición con importe distinto | `ID_CONFLICT` | Identidad ligada a intención, no solo a un identificador textual |
| Liberación del ACK anterior | Marca monotónica posterior a la recuperación | Una respuesta antigua no abre una segunda transición |

El [verificador independiente](../../../scripts/check_channel_transport.py) contrasta las observaciones HTTP originales, la identidad ofrecida, el orden temporal **antes de liberar** el ACK, los snapshots SQL y el ledger final. Las pruebas negativas falsifican ese orden, duplican asientos o cambian la identidad de una petición; deben ser rechazadas. La ejecución amplía el laboratorio a **14 escenarios nativos**, con **18 controles del proxy y 27 pruebas de evidencia**.

**Conclusión arquitectónica:** debemos desacoplar el estado observable por cada canal de la decisión financiera del propietario. Una respuesta tardía puede llegar después de la recuperación, pero **no es una nueva autorización**, ni justifica una compensación automática. La idempotencia debe abarcar identidad e intención y estar respaldada por el registro durable del propietario.

El ensayo usa conexiones de `localhost` y PostgreSQL desechable, no una red ATM, protocolo ISO 8583, CICS, hardware de dispensación o partición WAN; **ocho clientes locales tampoco demuestran capacidad o equivalencia en MIPS**. Los tiempos monotónicos solo se comparan en este host. Quedan fuera las firmas del emisor, efectos físicos, fencing del mainframe y reglas bancarias aprobadas. TODM G2 `INCONCLUSIVE` / G6 `BLOCK`.

## II. Orleans: particiones y activaciones

### C01 · Controlar la colocación para poder probar la recuperación

El [fallo original y las tres cohortes controladas](../../../evidence/runs/E2-C01-CONTROLLED.es.md)
separan una precondición del ensayo de un defecto contable. El primer caso
histórico observó las 16 cuentas en el secundario y rechazó correctamente la
exigencia de dos hosts. Repetir las mismas consultas no era una nueva muestra
de colocación: las activaciones existentes podían seguir donde estaban.

El cliente de prueba usa indicaciones de colocación solo para activar y
observar las cuentas 1..16. En el control negativo, las 16 se ubicaron en el
secundario, el criterio dual falló y no hubo operaciones financieras. Pedir
hints alternos desde otro cliente no las redistribuyó. En un fixture nuevo,
el reparto observado fue 8/8; los clientes financieros posteriores funcionaron
sin hints y con el mismo AccountGrain y ledger SQL aceptados.

Las tres cohortes confirmaron el SIGKILL real del secundario, reactivación en
primario, replay idempotente, tres operaciones/seis apuntes/tres outbox y siete
invariantes. Después se reincorporó un contenedor secundario nuevo, con otra
generación Active mientras la anterior seguía Dead, sin alterar el ledger.
Los runner IDs asignados fueron distintos; repiten hostname y cada caso
sigue usando una sola máquina. No se demuestra HA física.

Esta es la alternativa de fixture controlado prevista para C01. **La causa
de la concentración histórica no queda explicada**, la prueba antigua conserva
su rechazo y no cambia la política predeterminada del runtime. Las indicaciones
de colocación tampoco conceden autoridad financiera: los efectos siguen
siendo responsabilidad de PostgreSQL. E2 permanece parcialmente verificado.

#### Registrar el fallo sin atribuirse un PASS anterior

Un archivo aprobado de `development` no demuestra que el intento posterior
ADO.NET haya terminado bien. La [continuación de observabilidad](../../../evidence/runs/E2-PLACEMENT-OBSERVATION.es.md)
crea un diario por proveedor y ejecución, conserva cada mapa, la membresía y
los logs antes de limpiar los procesos, y registra la fase exacta del fallo.
Una consulta inaccesible sigue siendo un error; no se convierte en lista vacía.

Dos controles originales abortaron deliberadamente tras el primer probe real
de identidad 1..16. Los mapas primario/secundario fueron 7/9 y 10/6: **no
reprodujeron la concentración unilateral histórica**. Ambos hijos mantuvieron
FAIL/salida 1, sin órdenes financieras ni SIGKILL, con cero efectos y siete
oráculos SQL correctos. El padre verificó la conservación del fallo y mantuvo
el PASS anterior como entrada de control.

Esto acredita el registrador, no la política de colocación ni la recuperación.
Los fallos naturales futuros tendrán evidencia propia; la causa del histórico
sigue sin demostrarse y E2 permanece parcialmente verificado.

### C04 · El cliente pierde sus gateways, el ledger conserva la autoridad

La [prueba original C04](../../../evidence/runs/E2-C04-GATEWAY.es.md) corta
solo las salidas del cliente externo de Orleans: primero al gateway primario
y después a los dos. Con uno disponible, un cliente nuevo confirmó la
transferencia por el secundario hacia un grain alojado en el primario. Bajo
el corte doble, ambos silos y PostgreSQL siguieron accesibles entre sí.

El primer intento falló porque un timeout externo de 70 segundos no permitía
clasificar la fase de aplicación. El ZIP negativo se conserva. El modo
corregido observa un deadline de arranque antes de enviar comandos financieros:
salió con código 74 en 20,8509 segundos. No hubo efectos nuevos durante el
corte, incluidas tres muestras SQL adicionales. Restauradas las reglas de
red originales, el mismo ID se confirmó y su repetición fue duplicada; el
estado final tuvo tres operaciones, seis apuntes y tres outbox, con oráculo 7/7.

Esto es indisponibilidad de arranque de un cliente nuevo, **no pérdida de ACK
tras COMMIT**. Son cuatro namespaces en un runner; no explica el fallo
histórico de placement C01 ni demuestra dominios físicos, capacidad sostenida
o un RTO productivo. E2 sigue parcialmente verificado.

### C05/C06 · La dirección de los paquetes no decide qué se confirmó

La [prueba de partición direccional](../../../evidence/runs/E2-C05-C06-DIRECTIONAL.es.md)
parte de una colocación observada 8/8 y bloquea la salida TCP entre silos en
una dirección cada vez. SQL y gateways siguen accesibles. Las capturas de
45 segundos comprueban paquetes idénticos en ambos extremos en la dirección
permitida y ninguno recibido en la bloqueada. Que fallen conexiones TCP
iniciadas desde ambos lados no convierte el corte en simétrico: también
necesitan tráfico de retorno.

Dos clientes con gateways distintos envían el mismo ID con importes 31 y 37.
En ambas orientaciones, el primero obtiene timeout tras enviar y el segundo
COMMITTED; SQL identifica el importe 37 como ganador. Los catálogos de gestión
no responden durante el corte: **una vista inaccesible no es una lista vacía**
ni demuestra activación exclusiva.

| Salida bloqueada | Corte observado | Primeros intentos con respuesta por ambos gateways tras restaurar |
|---|---|---|
| Primario hacia secundario | 46,0143 s | 1,6926 s |
| Secundario hacia primario | 45,7963 s | 1,1831 s |

Restauradas las reglas originales, no se reinician silos ni cambian sus
contenedores, PID o generaciones. El replay idéntico devuelve
DUPLICATE_COMMITTED, el importe distinto ID_CONFLICT y una orden nueva
COMMITTED. Cada caso termina en tres operaciones, seis apuntes y tres outbox,
con siete invariantes SQL correctos. Se conservan cuatro fallos previos:
dos de preparación y dos de cierre de captura; no se convierten en aprobados.

Estos tiempos son observaciones de primeros intentos con respuesta, **no un
RTO ni servicio estable sostenido**. Un host por caso, dos cortes breves y
muestras de catálogo no acreditan ausencia de split brain, fencing o
recuperación tras particiones largas. Esas puertas, capacidad sostenida y
dominios físicos siguen abiertas. E2 permanece parcialmente verificado.

### Corte largo · Recuperación asistida con observaciones acotadas

La [evidencia original](../../../evidence/runs/E2-LONG-PARTITION.es.md) añade dos
cortes direccionales programados de 120 segundos. En ambos, el silo secundario
terminó antes de acabar el plazo: mantener la regla en un namespace retenido
no equivale a mantener ambos silos vivos. Dos intentos pareados no recuperaron
el gateway secundario; el protocolo eligió recrear expresamente ambos silos,
conservando el ledger y registrando generaciones nuevas. El primer ACK pareado
llegó a los 58,484 y 59,211 segundos desde la retirada de la regla.

Después, 14 parejas de replay durante unos 66 segundos conservaron los mismos
contenedores/PID, dos miembros Active, SQL 3/6/3 y siete invariantes. Cada replay
idéntico devolvió DUPLICATE_COMMITTED; el cambio de payload, ID_CONFLICT. Es
estabilidad muestreada tras recuperación asistida, no disponibilidad continua,
reinicio necesario, RTO productivo, activación exclusiva o HA física. Los dos
fallos iniciales de instrumentación siguen archivados como FAIL; la corrección
separó la vida de los diagnósticos sin rebajar los criterios financieros.

### Activaciones · Observar llamadas sin confundirlas con exclusividad

El [observador separado](../../../evidence/runs/E2-ACTIVATION-OBSERVATION.es.md)
añadió un filtro de llamadas entrantes al host de prueba, conservando el grain
financiero y ledger sin cambios. Dos ensayos originales registraron 38 y 39
intervalos completos de Transfer, con IDs de activación, sesión de proceso y
reloj monótono. Los logs se conservaron antes de recrear los silos. Todos los
resultados reconocidos coincidieron con SQL: tres operaciones, seis asientos,
tres eventos outbox y siete invariantes en cada caso.

No se observaron intervalos incompletos ni solapamientos entre activaciones
distintas del mismo grain. Eso no demuestra exclusividad global: el filtro
mide intervalos de llamadas, no toda la vida de una activación ni transacciones
SQL simultáneas. Sigue pendiente provocar y observar un caso positivo de
activaciones concurrentes con aceptación SQL independiente. Cada ensayo usó
un host físico y recuperación asistida; E2 permanece parcialmente verificado.

### Pausa dirigida · Un testigo positivo no demuestra repetibilidad

El [ensayo dirigido del grain normal](../../../evidence/runs/E2-ACCOUNT-DIRECTED.es.md)
retuvo una llamada antigua en un filtro separado, antes de invocar el método
financiero. No cambió el AccountGrain, ledger ni colocación predeterminada.
Un caso mostró dos intervalos completos sobre IDs de activación distintos
para la misma clave, solapados 5,06 ms con la regla de corte presente: la nueva
llamada confirmó el importe 31 y la antigua, al liberarse, devolvió
DUPLICATE_COMMITTED. SQL conservó el efecto único y rechazó payloads incompatibles.

El sentido opuesto quedó inconcluso. El primer colector omitía stderr; al
corregirlo, los dos casos repetidos también quedaron inconclusos. Hay un testigo
positivo entre esas cuatro observaciones. Una tercera campaña volvió a mostrar
un solapamiento de 4,68 ms con stderr completo: dos positivos dirigidos y cuatro
inconclusos en total, con reproducción parcial solo en el sentido secundario. En las
repeticiones, stderr y SQL identifican una ruta fatal de membresía: el primario
se descubre Dead, ejecuta KillMyselfLocally y termina con código 139. La selección
de víctima entre particiones sigue sin explicarse por completo.

Cada caso terminó con recuperación asistida, tres operaciones, seis asientos,
tres eventos outbox y siete invariantes. La pausa es artificial y mide llamadas
entrantes, no ciclos de vida Active simultáneos ni transacciones SQL simultáneas.
Los originales inconclusos se conservan como tales. E2 sigue parcial; capacidad
sostenida y dominios físicos continúan siendo puertas independientes.

## III. Brownfield: autoridad y recuperación

#### C2 · Una respuesta desconocida necesita un journal duradero

La convivencia anterior resuelve cómo comparar dos almacenes, pero deja un
problema abierto: **el COMMIT puede ser correcto aunque el ACK no llegue**.
Tratar un timeout como un rechazo y reintentar contra el otro escritor podría
producir dos efectos contables. Por eso C2 incorpora un tercer PostgreSQL
desechable, `bf_control`, con un journal de admisión independiente de los
dos ledgers. Cada petición CAP-007 registra identificador estable, huella,
escritor, época y estado antes de ejecutar el comando remoto.

El estado avanza de `ADMITTED` a `DISPATCHING` y, si la respuesta
desaparece, a `UNKNOWN`. Solo la inspección SQL independiente de la
operación persistida, sus dos apuntes y el outbox puede concluir
`COMMITTED` o `REJECTED`. La ausencia de fila en ambos almacenes
**no demuestra un rechazo**: mantiene UNKNOWN y bloquea el cutover.

El ensayo de tres contenedores mata procesos reales después de la admisión,
antes del envío y después de un COMMIT cuyo resultado no llegó al gateway.
También falsifica una decisión terminal del journal y verifica que el
oráculo rechaza el cambio de escritor. Los adaptadores cooperativos del
legado en Python y del nuevo servicio .NET 10 pueden exigir el controlador
C2 y mantener un bloqueo compartido hasta confirmar la operación. Las
[pruebas originales de C2](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41341644829)
se ejecutaron con un SHA concreto en CI. No sustituyen una homologación
bancaria.

**En aquel SHA original de C2:** en modo C2 estricto,
ambos adaptadores exigen una admisión `DISPATCHING` previa y rechazan
llamadas directas sin ella. Si se desactiva deliberadamente esa opción,
el acceso directo puede escribir sin journal: el oráculo detecta el efecto,
pero no evita ese bypass de configuración. Las épocas del controlador
y del candidato tampoco cambian atómicamente entre dos PostgreSQL.
Un bloqueo cooperativo no retira la autoridad a un CICS/Db2 real. Faltan
fencing externo, reparación ante crash entre cambios de autoridad,
conciliación de terceros, pruebas entre nodos físicos y política de
negocio aprobada. TODM G2=INCONCLUSIVE y G6=BLOCK.

#### Continuación de C2 · Persistir el control y congelar cambios interrumpidos

La [continuación del journal](../../../lab/brownfield/journal/README.md)
cambia dos supuestos técnicos sin modificar la autoridad del negocio. La
inscripción queda guardada en SQL: quitar una variable de proceso ya no
permite desactivar la admisión en ninguno de los dos adaptadores cooperativos.
Las fixtures históricas nuevas permanecen sin inscribir; el SQL directo con
privilegios sigue fuera de este control.

Antes de cambiar ninguna época, el coordinador confirma una intención
`PREPARED` y `mode=SWITCHING` duraderas. Los dos adaptadores y el gateway
rechazan nuevos comandos financieros hasta que la conciliación independiente
del ledger y del journal permita completar exactamente esa transición.

| Frontera duradera | Controlador | Autoridad del candidato | Nueva admisión |
|---|---|---|---|
| Intención preparada | legacy / e / SWITCHING | legacy / e | Bloqueada |
| Autoridad del candidato confirmada | legacy / e / SWITCHING | candidate / e+1 | Bloqueada |
| Conciliación completada | candidate / e+1 / ACTIVE | candidate / e+1 | Permitida con admisión coincidente |

El protocolo envía `SIGKILL` desde un proceso independiente después de las
dos primeras fronteras y reinicia la recuperación. Una época inesperada o un
outbox ausente deben mantener el tráfico congelado; una respuesta perdida
no decide quién escribe. Las decisiones originadas por el candidato siguen
vetando la vuelta atrás. Esto cubre ventanas concretas del modelo cooperativo
mediante intención duradera y recuperación hacia adelante,
**no mediante COMMIT atómico entre bases de datos**. La [CI original de esta continuación](../../../evidence/runs/BROWNFIELD-C2-RECOVERY.es.md)
superó 19 controles, conservando el ZIP original y el primer fallo concurrente. La ejecución posterior [#41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630), sobre el main `279ca566`, superó 20 controles y ambos oráculos SQL 10/10; es otra observación, no una ampliación retrospectiva de aquel ZIP.
Cada cambio posterior necesita CI con su SHA exacto: la observación histórica
no valida otro checkout. Las particiones de red durante operaciones en
curso, la retirada de autoridad al incumbente real, los efectos de pago
externos y la política aprobada siguen siendo puertas de aceptación separadas.
G2=INCONCLUSIVE y G6=BLOCK.

#### C2 · Perder el controlador con una operación ya iniciada

El [nuevo protocolo de corte TCP](../../../lab/brownfield/journal/README.md)
parte de una ventana distinta de «controlador inaccesible antes de empezar».
Un trigger de prueba mantiene la operación financiera sin COMMIT; una sesión
SQL independiente debe observar la espera real. Un relay cierra las conexiones
TCP del controlador y rechaza reconexiones; después se mata el gateway desde
otro proceso, dejando al adaptador en curso. No es una partición silenciosa ni
asimétrica, y los tres PostgreSQL siguen en un único runner.

El contrato exige UNKNOWN y veto al cambio de escritor mientras no se observe
una decisión duradera. Al liberar la barrera, el modelo cooperativo puede
confirmar su transacción financiera aunque haya perdido la sesión de control.
Eso debe conciliarse por SQL antes de permitir el replay: una decisión, dos
apuntes y un outbox. Perder un bloqueo de otra base no cancela atómicamente el
COMMIT financiero. Si la observación contradice el contrato, la CI debe fallar.

La [ejecución original #41511782428](../../../evidence/runs/BROWNFIELD-CONTROLLER-LOSS.es.md)
superó ambos casos: legado Python y candidato .NET. El servidor confirmó
la pérdida de sesiones; UNKNOWN bloqueó el cambio y la conciliación posterior
obtuvo una decisión, dos apuntes y un outbox en cada caso, con ambos oráculos
SQL 10/10. El ZIP original conserva source/checkout y diez hashes de origen.
Esta evidencia acotada no cierra #64 ni acredita fencing bancario, RTO/RPO o
una migración productiva.
G2=INCONCLUSIVE y G6=BLOCK.

#### C2 · Una conexión viva no significa una decisión conocida

La siguiente [campaña original](../../../evidence/runs/BROWNFIELD-CONTROLLER-PARTITION.es.md) mantiene abiertos los sockets del controlador mientras descarta bytes opacos en una dirección. Cuatro casos cruzan escritores legado/candidato con cada dirección. Una consulta SQL marcada, observada fuera del relay, distingue petición que no llega al servidor de respuesta que no llega al cliente. Este relay confirma las lecturas TCP; no emula pérdida de paquetes del kernel.

Los cuatro casos pasaron sobre su fuente registrada. Antes de liberar la barrera financiera, las sesiones del controlador seguían vivas y no había decisiones financieras visibles. La admisión nueva y el corte fallaron sin cambiar autoridad. Tras terminar externamente el gateway y liberar la barrera, cada ledger confirmó una decisión, dos apuntes y un outbox. En estos intentos, suprimir peticiones dejó la sesión del controlador en transacción; suprimir respuestas la dejó idle tras el COMMIT financiero separado. Un socket abierto o una respuesta ausente no deciden qué confirmó otra base de datos.

La recuperación restablece explícitamente conexiones antes de conciliar; no es seguro reanudar como íntegro un flujo al que faltan bytes de protocolo. Ambos oráculos SQL pasan diez comprobaciones, repetir no añade efecto y se rechazan dos observaciones deliberadamente falsas. No demuestra recuperación automática ni fencing real del origen. Retransmisión de paquetes, presupuestos de timeout/locks, fallos simétricos y hosts físicos independientes quedan para validación externa. G2=INCONCLUSIVE y G6=BLOCK.

## IV. Admisión y validación externa

#### B05: distinguir límites de admisión y capacidad del servidor

El [diagnóstico de admisión directa](../../../evidence/runs/B05-DISPATCH-DIAGNOSTIC.md) añade tres cohortes en runners a 320 ofertas/s, con fases de medición de 60 segundos. Cada pareja mantiene el pool PostgreSQL en 32 conexiones y cambia la admisión del cliente de 32 a 128 plazas; una cohorte invierte el orden. Los eventos exactos de admisión, finalización y liberación, junto con las marcas independientes de commit SQL, sustituyen las estimaciones retrospectivas de ocupación.

Las seis pruebas ofrecieron 119.040 operaciones: 118.887 commits durables y 153 rechazos por admisión, 129 durante el calentamiento y 24 durante la medición. Todos los rechazos ocurrieron exactamente con 32 plazas activas. Las tres pruebas de 128 plazas admitieron todas las ofertas. Las siete invariantes financieras se cumplieron en cada prueba. Una prueba con 32 plazas registró 319,6 commits SQL ciertos/s; las demás, 320,0000–320,0167/s dentro de la ventana SQL independiente, cuyas fronteras difieren de las fases de las ofertas.

Es evidencia de un efecto de la política de admisión en este cliente directo instrumentado; no establece un techo de capacidad ni explica los 12 rechazos antiguos. Falta medir la espera por conexión; el runner y la instrumentación afectan los tiempos. Siguen abiertos la ruta Orleans, el escalado sostenido y la atribución del cuello de botella de #25. Auditar el archivo congelado es distinto de ejecutar una campaña nueva; omitir la matriz viva no demuestra capacidad.

#### Integrar evidencia acotada y aplazar explícitamente la validación externa

El 3 de noviembre de 2026, el autor autorizó integrar las observaciones E2 y el diagnóstico B05 sin exigir que CI demuestre antes todas las afirmaciones de producción. El [protocolo de validación externa](../../../docs/EXTERNAL_VALIDATION.md) concreta el trabajo pendiente. La ausencia de mediciones externas deja de bloquear la integración del libro/laboratorio y el avance editorial. E2 sigue parcialmente verificado; esta decisión no convierte un resultado INCONCLUSIVE en PASS ni autoriza un despliegue bancario.

Un único runner permite probar SQL real, procesos distintos, particiones lógicas y conciliación independiente. No convierte esos contenedores en máquinas físicamente independientes. La capacidad y las observaciones naturales de activación no son intrínsecamente imposibles en Actions; estas campañas simplemente no las demuestran. Actions puede orquestar infraestructura dedicada o runners propios. Lo determinante es la topología y la evidencia, no el producto que ejecuta la automatización.

| Afirmación pendiente | Experimento más realista | Cambio necesario en el laboratorio |
| --- | --- | --- |
| Capacidad sostenida y cuello de botella (#25) | Hosts separados para carga, silos y SQL; mismos vectores directo/Orleans; 1/2/4/8/16 silos, durabilidad fija y barridos repetidos de tasas | Nuevo generador para endpoints externos con lista de fixtures permitidos; medir planificación, colas, adquisición de conexión, esperas SQL/WAL/almacenamiento y recursos por host |
| Activación natural y recuperación continua (#24) | Grains ordinarios sin demora artificial antes de la invocación; fallos direccionales en interfaces reales; recuperación sin intervención | Sustituir supuestos de contenedor local por identidades remotas explícitas; conservar ciclo de vida, ambas salidas de logs y PCAP; acotar la incertidumbre de reloj |
| HA física y durabilidad (#8/#9) | Dominios de fallo independientes identificados; separar pérdida de host, partición y failover SQL | Registrar política de replicación/confirmación y resolver IDs ambiguos; hardware desechable dedicado para pérdida eléctrica del almacenamiento |
| WAN, transporte y economía (#9/#12) | Rutas reales sucursal/servidor con TLS y autenticación equivalentes para gRPC y REST; coste total fechado por transferencia durable correcta | Separar degradación controlada y medición de campo; capturar DNS, gateways, canales reutilizados, plazos y costes de operación/DR |
| Cutover bancario (#32/#58/#64) | Contrato aprobado por el responsable, trazas autorizadas y fencing real del escritor en origen | Adaptador autorizado, conciliación de efectos externos y repetición de controles en curso/UNKNOWN/rollback; mantener aprobación TODM G2/G6 |

El diagnóstico B05 comprueba deliberadamente un DSN exacto en loopback: cambiar una variable no lo transforma en benchmark distribuido. Se conserva ese fixture y se añade un generador identificado por separado. Los relojes monotónicos remotos no se comparan directamente: hay que registrar desfase e incertidumbre, exigir solapamiento positivo después de aplicar sus límites y mantener INCONCLUSIVE si no puede demostrarse.

El estudio externo propuesto empieza reproduciendo 320 ofertas/s; después utiliza al menos tres repeticiones por configuración, perfiles uniformes/calientes/cruzados con semillas fijas y tasas prerregistradas alrededor de la degradación. Como diseño inicial se sugieren 5 minutos de calentamiento, 15 minutos de medición estable y drenaje acotado; son duraciones propuestas, no resultados ni umbrales de aceptación de producción. Primero se demuestra capacidad sobrante del generador, se incluyen ofertas rechazadas/tardías/ambiguas en los resultados del servicio y se conserva el calentamiento. Pool, reintentos, plazos y durabilidad permanecen fijos mientras cambia un factor. Antes de declarar un límite se miden crecimiento de colas y recursos atribuibles.

Cada intento original debe conservar código exacto, mapa de hosts/dominios, incertidumbre temporal, entorno, carga, logs y oráculos SQL independientes. Se mantienen las siete invariantes y los controles de corrupción. Las regresiones de código y archivos siguen siendo comprobaciones de integración; las campañas vivas conservan su invocación manual y sus códigos de salida. Una campaña omitida no demuestra capacidad. Las afirmaciones más amplias conservan su aceptación propia mientras continúa el desarrollo. Publicar sigue requiriendo autorización separada.

---

[← Anexo H · Más allá de COBOL](anexo-h-mas-alla-de-cobol.md) · [Índice](../README.md)
