# E2 — Protocolo ejecutable para obtener un PASS científico distribuido

**Versión del protocolo:** 1.0 · **Fecha:** 4 de noviembre de 2026  
**Naturaleza:** plan de una campaña futura, **no** evidencia de ejecución.  
**Estado actual:** campaña E2 acotada cerrada administrativamente; afirmación científica `partially_verified`. [Acta E2](E2_CLOSEOUT.es.md) · [English](E2_FULL_PASS_PROTOCOL.md).

> **Una campaña cerrada no significa E2 = PASS.** El issue [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) se cerró como `not_planned` para la validación externa fuera del alcance ejecutado. Si se decide buscar un PASS científico global, se debe autorizar **otra campaña**, con su propio issue, infraestructura, contrato, código instrumental, evidencias y evaluación independiente. Este texto **no reactiva** E2 como trabajo del roadmap actual.

## 1. Qué PASS queremos demostrar

**E2-TECH-PASS (científico, sobre el escenario contratado):** con Orleans y la transacción financiera autoritativa en PostgreSQL, la solución respeta el contrato funcional y los siete invariantes de contabilidad; bajo cargas ofrecidas reproducibles y fallos de silos, hosts, red y base de datos, demuestra los límites medidos de capacidad, recuperación, idempotencia, durabilidad y resultados de servicio. Los límites y el alcance se fijan **antes** de ejecutar las pruebas.

**E2-BANK-PASS (fuera de alcance):** además exige semántica y trazas de un sistema legado autorizado, criterios de negocio/seguridad/operaciones aprobados, SLO de producción, costes y decisión TODM. Ni E2-TECH-PASS ni el actor model demuestran equivalencia con MIPS, capacidad de un IBM Z, CICS/IMS o preparación bancaria sin esa evidencia adicional.

**No confundir:** paso de un job CI, PASS de un caso sintético, pruebas en dos contenedores de un runner, cierre administrativo de #8, aceptación de E2 y aprobación bancaria.

### Reglas de decisión

- `PASS`: todos los gates obligatorios aplicables tienen evidencias originales completas, repetidas y auditadas; contrato previo aprobado y métricas dentro de umbrales; controles negativos rechazados.
- `FAIL`: se rompe un invariante, se pierde una operación confirmada contra la política contratada, se duplican efectos financieros, falla un SLO obligatorio, hay split-brain con escrituras contradictorias o el auditor detecta falsificación/incoherencia. Las condiciones de FAIL no se convierten en INCONCLUSIVE para evitar rechazo.
- `INCONCLUSIVE`: falta una prueba, instrumento, topología, captura, aprobación previa o certeza temporal para afirmar PASS/FAIL. Nunca es PASS.
- `BLOCK`: no se autoriza cambio de estado global, release ni despliegue si falta un gate obligatorio. El estado en [evidence/claims.json](../evidence/claims.json) continúa `partially_verified` hasta evaluación independiente y autorización explícita.

La aprobación de una **campaña de investigación** puede utilizar un contrato sintético autorizado por su responsable. La declaración de equivalencia a un banco real necesita **otro contrato del cliente**; no se exige inventar ese cliente para cerrar un experimento técnico.

## 2. Precondiciones imprescindibles: antes de ejecutar nada

El fichero existente [`lab/performance-contract.json`](../lab/performance-contract.json) está `UNCONFIGURED` y no puede justificar PASS. Crear una **copia versionada, aprobada e inmutable por campaña** (no cambiar silenciosamente el baseline) que defina como mínimo:

| Campo / decisión | Qué debe contener | Motivo de bloqueo |
| --- | --- | --- |
| `campaignId`, alcance, responsable y firmantes | Pregunta concreta y vigencia; TECH o BANK | Sin mandato, resultado no aprobable |
| `sourceSha` y artefactos | SHA de código/oráculo, digest de imágenes, versiones .NET/Orleans/PostgreSQL y configuración | Sin reproducibilidad |
| Carga y población | Dataset, saldos iniciales, mezcla de transferencias válidas/rechazadas, cuentas calientes, distribución uniforme/5% hot/single hot, tamaño de claves e IDs | Comparación no equivalente |
| Oferta y límites | RPS ofrecidas, TPS COMMIT mínimas, p99 de servicio extremo a extremo, error/deadline máximo, duración, calentamiento, drenaje | Sin criterio cuantitativo |
| Garantías financieras | Siete invariantes, ACK vs COMMIT, duplicados, payload conflictivo, UNKNOWN y ventanas de resolución; orden lógico por ID | No se puede medir corrección |
| Durabilidad y HA | Política WAL/replicación, RPO, RTO, pérdida tolerada de un host/zona, carga mínima degradada, política de standby/quorum | No se puede aprobar fallo físico |
| Estadística y observabilidad | Número de repeticiones, regla de decisión, distribución de muestras, margen temporal y tratamiento de datos censurados | PASS por selección de mejor corrida |
| Infraestructura y seguridad | Redes, regiones/zonas, límites CPU/RAM/IOPS, secretos, identidad, transporte cifrado y presupuesto | Entorno no comparable o inseguro |

**Nunca introducir en la documentación valores de RPS, p99, RPO o RTO como si fueran objetivos aprobados.** Los ejemplos siguientes son un diseño de experimento, no umbrales de aceptación del cliente. Registrar el contrato con firma/revisión antes de abrir la campaña.

## 3. Topología física mínima creíble

```text
  Generador A ──┐
                ├── TLS / endpoint de prueba / gateways ── Silo A (host/zona A)
  Generador B ──┘                                  └─────── Silo B (host/zona B)
                         │                              │
                         └──────── transacciones ────────┘
                                        │
                                 PostgreSQL primario (dominio C)
                                        │ replicación según contrato
                                 PostgreSQL standby (dominio D)
                                        │
                           Quorum/gestor de failover externo
                                        │
                         Control de fallos + observabilidad + oráculo
                           (dominio aislado / lectura independiente)
```

- **Generadores** fuera de los hosts de silos/SQL. Para alta oferta, dos generadores y un sink de calibración para probar que pueden sostener el tráfico programado sin saturarse ellos.
- **Al menos dos hosts físicos o dominios de fallo genuinamente independientes para silos**, con anti-affinity efectiva y prueba de colocación real. Un Podman con dos contenedores en el mismo host **no** sirve.
- **PostgreSQL en dominios separados**, con standby y un mecanismo de elección/fencing que evite dos primarios. Puede ser infraestructura dedicada o un servicio gestionado que **demuestre** esos dominios y permita registrar las operaciones de failover; no basta un nombre comercial «HA».
- **Plano de control ajeno a la ruta sometida a fallo**: no perder los registros cuando se corta el enlace que se estudia. Captura de ambos extremos, SQL y reloj; el auditor no utiliza la respuesta de la app como fuente única.
- Fijar ServiceId/ClusterId, provider de membership (ADO.NET), DNS, puertos anunciados, certificados, límites y persistencia de estado. No usar clustering de desarrollo para atribuir HA.

**Ejemplo de despliegue, no obligación:** 2 o más hosts de silos, 2 nodos PostgreSQL más componente de quorum/fencing, 1–2 generadores y un host/control externo. Si se usan varias VM sobre el mismo hipervisor o almacenamiento común, **no son dominios de fallo independientes**. Si solo hay una AZ/host real, limitar el resultado a proceso/red, no físico.

## 4. Cambios de código que hay que implementar

No modificar los casos históricos ni su oráculo; implementar nuevos adaptadores en una ruta sugerida **`lab/e2_external/`** (ruta propuesta, no creada por este documento).

| Componente nuevo | Base actual y cambio real requerido | Entregable verificable |
| --- | --- | --- |
| `contract.py` y preflight | Leer contrato firmado, validar digest, alcance, hosts permitidos, DNS, TLS, fuente, topología y capacidad de generador. Rechazar valores nulos y entorno desconocido antes de enviar transacciones | `preflight.json` con `READY/INCONCLUSIVE/FAIL` |
| `remote_driver/` | **No** cambiar el `127.0.0.1` forzado de [B05 `run.py`](../lab/e2_b05_dispatch/run.py) ni el cliente protegido; crear driver externo open-loop con RPS programadas y reloj monotónico local, control de ráfagas, cola, deadlines, retry con mismo ID y trazas **por cada oferta** | CSV/JSONL de `scheduled→admitted→dispatched→ACK/UNKNOWN/reject→SQL COMMIT` |
| `distributed_fixture/` | Sustituir las suposiciones de `podman exec`, `podman inspect` y carpetas locales de [`run_probe.py`](../lab/e2_account_directed/run_probe.py) por controladores remotos autenticados, IDs de host/proceso/generación y capturas originales antes de eliminar procesos | Manifiesto de hosts y logs de todos los silos/clientes |
| `activation_observer/` | Instrumentar grain ordinario sin puerta `pre-invoke` ni trucos de colocación, registrar grain key, activation ID, silo, epoch/generación, BEGIN/END/error, membership, y transiciones de directorio | Traza causal de vida/colocación real |
| `metrics/` | Añadir OpenTelemetry con IDs correlacionados; medir oferta/admisión, espera de pool y locks SQL, WAL/flush/replicación, CPU, GC, memoria, sockets, paquetes, colas, SQL COMMIT y rechazo de gateway | Telemetría sincronizada, cruda y exportable |
| `fault_controller/` | Control explícito y reversible de corte de proceso, interfaz/red direccional, host/zona y failover de SQL, con lista de destino permitida, reloj del experimento y restauración | Eventos de inyección y PCAP en ambos extremos |
| `sql_oracle/` y `auditor/` | **Reutilizar sin debilitamiento** los siete predicados SQL; auditor independiente cruza IDs ofrecidos, ACK, COMMIT y estado post-failover; controles corruptos obligatorios | Informe de reconciliación + `PASS/FAIL/INCONCLUSIVE` por gate |
| `runner/` y `archive/` | Campañas nuevas con IDs únicos, SHA/digest fijado, directorios nunca reutilizados, originales FAIL y éxito conservados, hash de todos los archivos | Manifiestos firmables, artifacts verificables y resultado global independiente |

No reemplazar una observación faltante por logs del caso anterior; no retocar el comportamiento de Orleans para provocar una activación que solo queremos **observar**. Los filtros de test dirigidos siguen siendo diagnósticos aparte, no «natural placement».

**Cambios infra/CI:** IaC aislada o aprovisionamiento reproducible con Podman/VM/AKS según el escenario; red de pruebas controlada; identidades de servicio; PostgreSQL HA con estados verificables; workflow de verificación de esquemas sin necesidad de hosts; lanzamiento **manual autorizado** en self-hosted/dedicated o entorno externo; captura y subida de ZIPs. GitHub Actions puede **orquestar** máquinas externas, pero varios jobs hosted efímeros no demuestran por sí solos HA de la topología.

## 5. Matriz obligatoria de pruebas

| ID / gate | Ejecución que hay que hacer | PASS específico; ausencia ⇒ INCONCLUSIVE o FAIL |
| --- | --- | --- |
| **X00 · Provenance & contract** | Validar contrato, infra, identidades de máquinas, imágenes, versiones, clocks, permisos y calibración del generador | Todo identificable y firmado; sin huecos críticos |
| **X01 · Functional parity** | Mismos casos/semillas en ruta SQL directa y Orleans; sobregiro simultáneo, transferencias cruzadas, duplicado, payload conflictivo, timeout y UNKNOWN | Contratos equivalentes; 7/7 SQL; exactamente un efecto financiero por ID confirmado; controles negativos fallan |
| **X02 · Placement natural** | Grains de cuenta ordinarios sin inyección pre-invoke, enrolamiento y salida real de silos, llamadas por ambas pasarelas, observación de todas las generaciones | Ciclo de vida/reubicación observable y reconciliable; ausencia de observación suficiente ⇒ INCONCLUSIVE |
| **X03 · Partition safety** | Cortes direccionales A→B y B→A, además de bidireccional; silos vivos durante el intervalo registrado; capturas en ambos extremos y SQL intacto | No doble efecto financiero ni respuesta contradictoria; llamadas ambiguas se concilian. Concurrencia de activaciones se registra; **no** se presupone exclusividad global del actor durante una partición |
| **X04 · Recovery unassisted** | SIGKILL real, aislamiento de un silo y partición prolongada, primero SIN recreación manual; reanudación con IDs repetidos, llamadas nuevas y medida de degradación/recuperación | RTO/servicio degradado dentro del contrato, recuperación observada sin ayuda, 7/7; reinicio manual registrado implica `ASSISTED`, no PASS de este gate |
| **X05 · Capacity** | Direct vs Orleans: misma transacción SQL y contrato, 1/2/4/8/16 silos donde sea viable, uniforme, 5% hot, single-hot, cruzado; cargas ascendentes y descendentes | TPS COMMIT, p99 **sobre todas las ofertas**, errores/misses y coste de recursos cumplen objetivos; cuello de botella reproducible y atribuible; no se exige escalado lineal |
| **X06 · Physical HA / SQL failover** | Caída de host/zona de silo y caída independiente de primario SQL, reconexión al standby elegido; validar ACK antes/durante/después, elección/fencing de writer | RPO/RTO y carga degradada según contrato, ningún ACK perdido más allá del RPO contratado, sin doble primario escritor, 7/7 invariantes |
| **X07 · Negative/independent audit** | Corromper de forma aislada postings, duplicar IDs/conflictar payload, cortar manifests y omitir trazas, con estado de base de pruebas nuevo | Auditor rechaza cada control; compara SQL sin confiar en el cliente |
| **X08 · Reproducibility & signoff** | Repeticiones y revisión independiente de raws, reloj, digest, matrículas físicas y reportes | Mismos criterios prefijados, todas las campañas incluidas, sin resultados «escogidos»; firma de aceptación técnica |

### Detalles de los escenarios críticos

**Particiones:** separar condición «los dos procesos estuvieron vivos» de «ambos sirvieron transacciones». Conservar PCAP y actividad de red reales, membership y activaciones por generación. Si aparece una doble activación, no declararla automáticamente defecto de contabilidad: demostrar qué escrituras entraron en PostgreSQL y si los efectos confirmados fueron correctos. Si no se puede demostrar el solapamiento por incertidumbre de relojes, marcar testigo `INCONCLUSIVE` y conservar el estado financiero por separado.

**SQL HA:** registrar `synchronous_commit`, `synchronous_standby_names`, WAL, replication lag, timeline/fencing y garantías de ACK en la configuración **efectiva**. La replicación asíncrona puede perder cambios recientes ante failover: no prometer RPO=0 con esa política. Ensayar también la pérdida del primario cuando existen operaciones `UNKNOWN` y después de que el cliente haya recibido ACK; reconciliarlas por ID. Si el cliente pide RPO=0, demostrar una política de commit y elección compatibles con ello. El mero cambio de endpoint no es prueba de durabilidad.

**Capacidad y p99:** utilizar generador open-loop que no reduzca automáticamente RPS al frenarse el servicio. Medir desde **hora programada de oferta** hasta resultado válido, incluyendo retrasos de cola y deadlines; los percentiles solo de ACK supervivientes están censurados y **no** sustituyen el SLO de servicio. Comparar commits correctos duraderos por segundo y conservar la mezcla de rechazos de negocio. Medir pool-wait por separado antes de atribuir saturación a CPU/grains. Repetir sin seleccionar la mejor corrida.

**Tiempo:** sincronizar relojes antes/después y guardar offset/uncertainty por host, además de tiempos monotónicos locales. No calcular solapamiento distribuido con marcas UTC sin margen medido. Si los intervalos no solapan inequívocamente bajo la incertidumbre, el testigo queda INCONCLUSIVE.

## 6. Campaña reproducible propuesta (no ejecutada)

| Fase | Trabajo | Criterio para avanzar |
| --- | --- | --- |
| **P0** | Contrato TECH firmado, datos sintéticos autorizados, threat/safety review, presupuesto, plan de fallos | X00 READY, nunca credenciales productivas |
| **P1** | Aprovisionamiento de hosts separados, PG HA/quorum, TLS, control y observabilidad | Inspección externa de dominios y source/digest |
| **P2** | Entrega del driver/fixture/oráculo externo y pruebas negativas | X01 y X07 satisfacen controles antes de medir carga |
| **P3** | Baseline directa/Orleans y lifecycle natural sin fallos | X01, X02 y telemetría completa |
| **P4** | Particiones de red direccionales, SIGKILL y recuperación natural | X03 y X04, intervalos completos y raws conservados |
| **P5** | Matriz de carga y escalado con PostgreSQL estable | X05, cada configuración repetida |
| **P6** | Host/zona + SQL failover; durabilidad y conciliación final | X06 y X07 sin discrepancia |
| **P7** | Auditoría independiente y decisión en `claims.json` | X08 y matriz completa antes de considerar TECH-PASS |

**Diseño estadístico inicial propuesto:** al menos **3 repeticiones frescas por configuración**; 5 minutos de warmup, 15 minutos de régimen estable y drenaje acotado. Alternar el orden de configuraciones, conservar warmup/overload, añadir un soak largo si el contrato lo exige. Estos valores son una **propuesta experimental**, no umbrales aprobados ni demostración de representatividad; tamaños/duración deben justificarse por variabilidad observada y potencia del estudio. No fijar SLO tras mirar los datos.

**Inyección de fallos segura:** únicamente recursos desechables etiquetados y autorizados, endpoint allowlist, separación de credenciales y plano de control, ventana acordada, backout verificable y operador capaz de parar. Nunca ensayar un corte eléctrico real en infraestructura compartida; la durabilidad ante power loss exige hardware/lab dedicado con permiso explícito.

## 7. Evidencia que debe aparecer en el repositorio

Cada combinación `campaignId/runId/configurationId/repetitionId` crea un directorio **nuevo**, sin sobrescrituras, con al menos:

```text
evidence/external-e2/<campaign-id>/<run-id>/
  contract-approved.json         # Scope, acceptance thresholds, approval
  provenance.json                # Git SHA, images, tools, OS, hash inventory
  topology.json                  # Physical host/domain, roles, DB replica map
  clocks.json                    # Offset and uncertainty before/after
  offers.jsonl                   # ALL scheduled IDs and outcome transitions
  client-logs/                   # Original stdout, stderr, traces
  silo-logs/                     # Both directions, all generations
  network/                       # PCAP, fault commands and actual counters
  postgres/                      # Membership, WAL/replication/failover, SQL snapshot
  metrics/                       # CPU, GC, pool waits, lock/commit latency
  oracle.json                    # 7 predicates, corruption negatives, ID reconciliation
  assessment.json                # Each X00-X08: PASS/FAIL/INCONCLUSIVE
  manifest.sha256                # Hashes of originals, no rewritten attempts
  review.md                      # Independent reviewer and signed conclusion
```

La ruta es **diseño de salida**, no contiene ahora resultados de estos ensayos. Artefactos grandes originales pueden archivarse fuera de Git, **pero** deben tener un URI verificable, SHA-256, política de retención y registro inmutable en el repo. Preservar FAIL, INCONCLUSIVE, timeouts, salidas 137 y ausencia de datos; no reetiquetar. Se deben poder reconstruir denominadores de ofertas/COMMIT desde datos crudos, no solo desde un resumen calculado por el servicio.

## 8. Algoritmo de aceptación independiente

```text
if contract.status != APPROVED:          INCONCLUSIVE
if any mandatory evidence is missing:   INCONCLUSIVE
if any oracle/financial/safety rule fails: FAIL
if any contractual service threshold fails: FAIL
if any critical observation is unresolved: INCONCLUSIVE
if any required negative control incorrectly passes: FAIL
if any mandatory X00..X08 is not PASS:  INCONCLUSIVE or FAIL
else:                                   E2_TECH_PASS
```

Se requieren **todos los gates obligatorios aplicables** y la evidencia de cada repetición, no solo una media. En los fallos tolerados por contrato, diferenciar `ACK/COMMITTED`, `UNKNOWN`, rechazo de negocio y deadline incumplido; la condición precisa de RPO se evalúa respecto de los ACK y de la política firmada. Una observación del orden no demostrable es INCONCLUSIVE aunque el ledger quede correcto.

**Autoridad:** el auditor técnico firma el resultado de la campaña y registra los límites. Solo tras revisión de evidencias originales se puede proponer cambiar la afirmación E2 en `evidence/claims.json`. La etiqueta histórica `partially_verified`, los experimentos anteriores y el issue #8 no se alteran retroactivamente. **E2_TECH_PASS ≠ E2_BANK_PASS ≠ autorización de release/despliegue**; TODM G2/G6 solo cambian por su proceso de decisión correspondiente.

## 9. Dependencias y trabajo futuro concreto (NO activo)

1. Aprobar contrato experimental (sin valores `null`) y el alcance de la afirmación; aportar recursos/hosts reales.
2. Crear el harness externo, driver y observabilidad en un nuevo PR/issue separado **solo si se autoriza nueva campaña**.
3. Implementar topología de fallo físico y SQL HA verificable; comparar la configuración efectiva.
4. Ejecutar matriz X00–X08 y conservar íntegros intentos, negativos y fallos.
5. Obtener auditoría independiente y decidir PASS/FAIL/INCONCLUSIVE por alcance.

**Lo que sigue cerrado:** E2 #8 y la campaña previa; no bloquear libro ni brownfield. [Acta actual](E2_CLOSEOUT.es.md) · [protocolo previo con limitaciones del runner](EXTERNAL_VALIDATION.md).

## 10. Fuentes técnicas revisadas (4 noviembre 2026)

- [Microsoft Orleans — grain placement](https://learn.microsoft.com/en-us/dotnet/orleans/grains/grain-placement): colocación, activación, sobrecarga y migración; la activación no sustituye la transacción SQL.
- [Microsoft Orleans — observabilidad](https://learn.microsoft.com/en-us/dotnet/orleans/host/monitoring/): métricas, logs y trazas distribuidas.
- [Microsoft Orleans — configuración de servidor](https://dotnet.github.io/orleans/docs/host/configuration-guide/server-configuration/): ServiceId, ClusterId y membership ADO.NET.
- [PostgreSQL — replicación y alta disponibilidad](https://www.postgresql.org/docs/current/high-availability.html) y [WAL/synchronous_commit](https://www.postgresql.org/docs/current/runtime-config-wal.html): la política de replicación condiciona durabilidad, latencia y recuperación.

Las fuentes describen capacidades de los productos; **ninguna** demuestra que esta campaña futura se haya ejecutado.
