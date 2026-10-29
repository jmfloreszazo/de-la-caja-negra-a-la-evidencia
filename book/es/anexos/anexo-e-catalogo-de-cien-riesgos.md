**Español** · [English](../../en/annexes/annex-e-catalog-of-one-hundred-risks.md)

[← Anexo D · Decisiones de arquitectura](anexo-d-decisiones-de-arquitectura.md) · [Índice](../README.md) · [Anexo F · Glosario operativo →](anexo-f-glosario-operativo.md)

# Anexo E · Catálogo de cien riesgos

La numeración identifica cada riesgo; no expresa frecuencia, gravedad ni prioridad. Cada fila propone una opción de aplicación, una capacidad de infraestructura y la evidencia que podría refutarlas. El laboratorio incluye la versión en inglés, en JSON y Markdown, con los campos de responsable y evidencia vacíos para usarla en un assessment real.

## Datos y representaciones

Ámbito principal de esta familia: COBOL y formatos. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R001 Datos no numéricos en campos numéricos | Validación de frontera y cuarentena | Conservar originales y rechazos | Inyectar bytes inválidos y comprobar rechazo |
| R002 Packed decimal y signo incompatibles | Codec COMP 3 explícito | Staging binario con esquema versionado | Comparar bytes signo escala y extremos |
| R003 Signo zoned decimal mal interpretado | Adaptador de representación DISPLAY | Conversión trazable por dataset | Probar signos y variantes del origen |
| R004 Memoria compartida mediante REDEFINES | Modelo de layout y unión discriminada si procede | Versionar copybook y codec | Comprobar vistas del mismo bloque |
| R005 OCCURS DEPENDING ON pierde longitud | Colección con cardinalidad validada | Almacenamiento de longitud y versión | Probar cero máximo y longitud inválida |
| R006 Parámetros BY REFERENCE pierden aliasing | Adaptador de llamadas y propiedad explícita | Inventario de contratos binarios | Observar mutación compartida entre llamadas |
| R007 Espacios de relleno cambian comparaciones | Tipo de campo con política explícita | Conservar valor crudo durante transición | Comparar blancos longitud y cadenas vacías |
| R008 Orden EBCDIC cambia al ordenar Unicode | Comparador y collation definidos | Staging con CCSID identificado | Comparar secuencias de claves y empates |
| R009 Longitud de bytes confundida con caracteres | Separar buffer binario de texto | Metadatos de encoding por interfaz | Probar acentos longitudes y truncamiento |
| R010 Opciones de compilador cambian resultados | Perfil semántico por toolchain | Compilación reproducible y versiones fijadas | Ejecutar corpus con opciones documentadas |

## Cálculo monetario y tiempo

Ámbito principal de esta familia: Semántica de negocio. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R011 Rango PICTURE excede tipo de destino | Tipo de dominio con rango explícito | Esquema con precisión y restricciones | Probar mínimo máximo y desbordamiento |
| R012 Redondeo usa una regla diferente | Política de redondeo por operación | Versionar reglas aprobadas | Probar empates y valores adyacentes |
| R013 Redondear parciales altera el total | Pipeline de cálculo con etapas definidas | Guardar traza de cálculo permitida | Comparar parciales y agregado final |
| R014 Importes negativos tienen otra semántica | Tipos para reverso cargo y abono | Restricciones por tipo de movimiento | Probar negativos cero y reversos |
| R015 Monedas mezcladas en un mismo saldo | Money con moneda y escala | Particiones e índices por moneda cuando proceda | Rechazar agregados entre monedas distintas |
| R016 Fecha de negocio usa fecha del servidor | Reloj de negocio inyectado | Calendario y zona versionados | Repetir cierres con reloj controlado |
| R017 Fechas abreviadas tienen pivotes ocultos | Adaptador de calendario explícito | Conservar fecha original y regla | Probar cambio de siglo y bisiestos |
| R018 Cero espacios y NULL se confunden | Modelo explícito de ausencia | Migración reversible y restricciones | Comprobar los tres valores por separado |
| R019 Tabla de tasas cambia durante un lote | Snapshot de reglas por ejecución | Configuración con vigencia y versión | Repetir lote con la misma regla |
| R020 División por cero altera el flujo | Resultado tipado y política de excepción | Registrar errores sin perder entrada | Probar divisor cero y estado posterior |

## Flujo y estado de programas

Ámbito principal de esta familia: COBOL y diseño. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R021 GO TO oculta caminos de negocio | Grafo de control y refactorización gradual | Herramientas estáticas con procedencia | Cubrir ramas antes y después del cambio |
| R022 PERFORM o párrafos dependen de fallthrough | Extracción de funciones con fronteras explícitas | Baseline de rutas ejecutadas | Comparar orden y efectos de ejecución |
| R023 Variable reutilizada mezcla conceptos | Contextos tipados y nombres de dominio | Trazabilidad de lecturas y escrituras | Ejecutar secuencias que reutilizan almacenamiento |
| R024 CALL dinámico no aparece en dependencias | Registro de dispatch y adaptadores | Inventario de módulos y versiones cargadas | Probar cada destino y destino desconocido |
| R025 WORKING STORAGE conserva estado entre llamadas | Estado explícito por sesión o entidad | Afinidad temporal solo cuando esté justificada | Comparar dos invocaciones en secuencia |
| R026 Rutina no reentrante recibe peticiones paralelas | Contexto por invocación o serialización acotada | Aislar workers del runtime heredado | Forzar llamadas concurrentes al mismo módulo |
| R027 Valor sin inicializar parece estable | Inicialización y contrato de valores válidos | Diagnósticos del compilador en descubrimiento | Repetir con distinto estado inicial |
| R028 Código aparentemente muerto tiene consumidores | Análisis de alcanzabilidad y retirada gradual | Telemetría de uso y ventana de observación | Cubrir rutas raras antes de eliminar |
| R029 Código de retorno se vuelve excepción genérica | Mapa explícito de errores y decisiones | Métricas por clase de resultado | Comparar retorno efecto y recuperación |
| R030 Regla duplicada evoluciona de forma distinta | Módulo de dominio o tabla versionada | Propiedad y despliegue coordinado de reglas | Contrastar todos los consumidores de la regla |

## Ficheros y datasets

Ámbito principal de esta familia: Entorno mainframe. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R031 Acceso VSAM KSDS pierde semántica de clave | Repositorio con clave y recorridos explícitos | Índices y almacenamiento según acceso | Comparar clave ausente duplicada y rangos |
| R032 RBA o posición física se usa como identidad | Identificador estable y tabla de correspondencia | Conservar mapping durante migración | Verificar referencias después de reordenar |
| R033 Registros variables pierden metadatos de longitud | Codec de registros con framing | Manifiesto de formato y bloques | Probar límites registros vacíos y truncados |
| R034 Reinicio secuencial repite registros confirmados | Checkpoint más procesamiento idempotente | Checkpoint durable junto al progreso acordado | Caer y reanudar en límites de commit |
| R035 Dos jobs escriben el mismo fichero | Propietario de escritura con fencing | Lease verificado por el destino | Simular dueño antiguo tras relevo |
| R036 Consumidor lee fichero todavía incompleto | Publicación con manifiesto de completitud | Objetos inmutables y marcador final | Interrumpir subida y prohibir consumo parcial |
| R037 Dataset completo se carga en memoria | Streaming y lotes acotados | Límites de memoria y almacenamiento temporal | Procesar volumen superior al working set |
| R038 SORT MERGE cambia orden o estabilidad | Ordenación externa y contrato de desempate | Disco temporal dimensionado y recuperable | Comparar claves repetidas y totales |
| R039 Lectura secuencial se convierte en azarosa | Acceso por bloques o rango estable | Índices y layout según el recorrido | Comparar orden completitud y coste I O |
| R040 Spool o informe pierde formato contractual | Servicio de render con plantilla versionada | Archivo de salidas con retención definida | Comparar contenido paginación y consumidores |

## Acceso a bases de datos

Ámbito principal de esta familia: Datos y concurrencia. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R041 Unidad CICS Db2 se fragmenta en llamadas | Frontera de unidad de trabajo explícita | Un motor transaccional cuando sea viable | Caer entre escrituras y revisar atomicidad |
| R042 Un cursor se transforma en consultas N más uno | Operaciones de conjunto y batching | Índices y presupuesto de viajes | Medir consultas por operación y p99 |
| R043 Consulta de saldo carece de índice selectivo | Modelo de acceso y query tuning | Índices basados en planes medidos | Contrastar planes con volumen representativo |
| R044 NULL y espacios alteran predicados SQL | Capa de traducción semántica | Esquema de destino con reglas explícitas | Comparar filtros joins y agregados |
| R045 Leer comprobar y actualizar permite carreras | Actualización condicionada o control de versión | Restricciones y transacción en el motor | Lanzar débitos incompatibles en paralelo |
| R046 Predicado global sufre write skew | Aislamiento o bloqueo que cubra la invariante | Diseñar índices y fronteras de consistencia | Probar historiales concurrentes sobre varias filas |
| R047 Transacción espera red o intervención humana | Reducir sección crítica y mover preparación | Timeouts y observabilidad de transacciones | Forzar dependencia lenta y medir bloqueos |
| R048 Orden variable de locks genera deadlocks | Orden consistente y reintento completo limitado | Recoger gráficos y víctimas del motor | Forzar ciclo y comprobar recuperación |
| R049 Espera de bloqueo consume todo el presupuesto | Deadline y admisión limitada | Timeouts alineados entre capas | Sostener un lock y verificar salida acotada |
| R050 Réplica de lectura muestra saldo desactualizado | Lectura de confirmación con consistencia requerida | Enrutamiento de lectura según criticidad | Leer después de confirmar y durante retraso |

## Transacciones y mensajería financiera

Ámbito principal de esta familia: Garantías de negocio. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R051 Commit ocurre pero se pierde respuesta | Identidad de operación y consulta de resultado | Registro durable de decisiones | Reenviar después de confirmar sin respuesta |
| R052 Clave idempotente se reutiliza con otro mandato | Comparar identidad y contenido del mandato | Unicidad y retención de decisiones | Rechazar mismo ID con importe diferente |
| R053 Cambio y evento se guardan por separado | Transactional outbox | Guardar intención en la misma transacción | Caer entre commit y publicación |
| R054 Evento entregado de nuevo repite efecto | Inbox o consumidor idempotente | Persistir deduplicación junto al efecto | Repetir entrega y contar efectos confirmados |
| R055 Commit incluye recursos de gestores distintos | Conservar coordinación compatible o redefinir frontera | Coordinador y participantes recuperables | Probar estados preparados y recuperación |
| R056 Compensación sustituye atomicidad sin aprobación | Elegir transacción o saga según contrato | Workflow durable y reconciliación | Observar estados intermedios permitidos |
| R057 Reserva expira sin liberar disponible | Máquina de estados de reserva | Persistencia temporizadores y reconciliación | Caer al vencer confirmar y liberar |
| R058 Concurrencia permite sobregiro | Invariante en el motor y débito condicionado | Transacción y restricción de saldo | Competir por un saldo insuficiente para ambos |
| R059 Propietario obsoleto sigue escribiendo | Fencing con época validada en destino | Autoridad de escritura y token monotónico | Reactivar dueño anterior y rechazar escrituras |
| R060 Saldo y asientos dejan de corresponder | Ledger inmutable y proyección reconciliable | Historial durable e índices por operación | Recalcular saldos y balance por movimiento |

## Batch y planificación

Ámbito principal de esta familia: Operación mainframe. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R061 JCL oculta dependencias entre jobs | DAG con entradas y salidas declaradas | Scheduler con historial durable | Reproducir orden y precondiciones |
| R062 Return codes deciden ramas no documentadas | Workflow con decisiones explícitas | Registro de códigos y transiciones | Probar cada rama y salida inesperada |
| R063 Restart batch vuelve a aplicar movimientos | Chunk idempotente con checkpoint | Persistir progreso y versión del dataset | Reiniciar antes y después de cada commit |
| R064 Generaciones GDG se confunden al moverlas | Identidad de dataset por generación | Objetos versionados y manifiesto de lote | Reprocesar una generación sin mezclar otra |
| R065 Ventana batch depende de un paso serial | Optimizar camino crítico antes de escalar | Recursos reservados por fase | Medir DAG completo y fecha límite |
| R066 Una partición de lote concentra el trabajo | Particionamiento por coste y work stealing seguro | Métricas por partición y límites de workers | Inyectar sesgo y medir duración máxima |
| R067 Tamaño de commit maximiza locks o reejecución | Chunk con atomicidad definida | Log y checkpoints dimensionados | Medir tiempo de lock y trabajo perdido |
| R068 Batch consume recursos del tráfico interactivo | Bulkheads y prioridades explícitas | Pools cuotas y capacidad separada | Ejecutar mezcla batch y online |
| R069 Calendario de cierre difiere entre plataformas | Calendario de negocio versionado | Servicio o configuración con vigencia | Probar festivos zona y cambio de día |
| R070 Cancelar un job deja trabajo no rastreable | Cancelación cooperativa y reanudación | Estado durable y drenaje de workers | Cancelar durante cada etapa y reconciliar |

## Integración y coexistencia

Ámbito principal de esta familia: Contratos y sistemas. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R071 COMMAREA se expone como DTO sin contrato | Anti corruption layer con esquema versionado | Gateway y límites de payload | Comparar layout rangos y respuestas |
| R072 Mensaje supera límite del transporte | Referencia a payload con integridad | Objeto durable con acceso temporal | Probar expiración tamaño e integridad |
| R073 Encoding se convierte dos veces | Codec único en una frontera definida | Metadatos de conversión y origen | Round trip de caracteres representativos |
| R074 Confirmación MQ se desacopla del negocio | Protocolo de recepción y efecto idempotente | Gestor transaccional o inbox según alcance | Caer antes y después del reconocimiento |
| R075 Operaciones de una entidad llegan desordenadas | Secuencia de negocio y consumidor por clave | Sesiones o particiones más estado durable | Enviar fuera de orden y detectar huecos |
| R076 Mensaje venenoso bloquea una entidad entera | Cuarentena con política de resolución | DLQ métricas y reanudación controlada | Verificar continuidad sin saltar reglas críticas |
| R077 Reintentos en varias capas amplifican carga | Un presupuesto de retry con jitter | Límites de admisión y circuit breaker | Cortar dependencia y medir amplificación |
| R078 Dependencia externa lenta retiene todo el pool | Bulkhead y timeout por dependencia | Pools aislados y capacidad de reserva | Saturar un destino y observar los demás |
| R079 Pantalla mantiene estado conversacional oculto | Estado de sesión o workflow explícito | Persistencia y caducidad según contrato | Reanudar sesión tras cambio de instancia |
| R080 Identidad técnica sustituye permisos de negocio | Contexto de autorización y mínimo privilegio | Identidad de workload y políticas verificadas | Probar accesos permitidos y denegados |

## Rendimiento y capacidad

Ámbito principal de esta familia: Aplicación e infraestructura. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R081 MIPS se convierte directamente a vCPU | Modelo de demanda por transacción | Candidatos de hardware ensayados | Replay de mezcla con durabilidad equivalente |
| R082 Asignaciones por registro disparan el GC | Streaming y reducción medida de asignaciones | Presupuesto de memoria y telemetría GC | Medir pausas con el volumen objetivo |
| R083 Esperas síncronas agotan el ThreadPool | Async de extremo a extremo cuando aplique | Instrumentar cola y hilos disponibles | Forzar I O lento y observar latencia |
| R084 Más workers aumentan conflictos y CPU | Concurrencia limitada por recurso | Pools y límites medidos | Barrido de concurrencia con errores y p99 |
| R085 Cola sin límite oculta una caída de servicio | Backpressure y rechazo explícito | Cola durable con capacidad y alarmas | Sostener tasa mayor al consumo y drenar |
| R086 Disco rápido queda limitado por la VM | Modelo de I O completo | Verificar límites de VM disco y red | Medir IOPS ancho de banda y colas |
| R087 Log o réplica síncrona domina el commit | Reducir trabajo y agrupar solo si es válido | Almacenamiento y réplica con contrato durable | Medir commits con réplica y fallo |
| R088 Actor caliente impone un techo serial | Reducir sección crítica o revisar agregado | Distribuir otras claves y observar colas | Concentrar carga en una sola identidad |
| R089 Prueba solo con caché caliente engaña | Diseño de prueba fría y caliente | Dataset y memoria representativos | Medir arranque calentamiento y steady state |
| R090 Microservicios multiplican viajes de red | Operaciones de grano adecuado y localidad | Ubicar cómputo y datos según latencia | Contar viajes y medir con red real |

## SDLC recuperación y gobierno

Ámbito principal de esta familia: Ingeniería y operación. Las medidas de infraestructura requieren el contrato del motor o servicio elegido.

| Identificador y riesgo | Opción de aplicación | Opción de infraestructura | Evidencia a exigir |
|---|---|---|---|
| R091 No se sabe qué versión está en producción | Inventario y manifiesto de artefactos | Build y despliegue trazables | Reconciliar binarios configuraciones y hashes |
| R092 Cambio de runtime altera el comportamiento | Dependencias fijadas y regresión diferencial | Imágenes verificadas y plan de actualización | Repetir corpus al cambiar toolchain |
| R093 Incidente no se puede reconstruir | Trazas correlacionadas y eventos de negocio | Telemetría durable con minimización de datos | Seguir una operación entre todos los componentes |
| R094 Alta disponibilidad carece de recuperación probada | Diseño de fallo y reconciliación | Réplicas backups y restauración ensayados | Medir RTO RPO y consistencia bajo carga |
| R095 Nuevo esquema impide ejecutar la versión anterior | Expand contract y compatibilidad de lectores | Migración versionada de esquema | Ensayar convivencia y lectura cruzada |
| R096 Rollback de código no revierte datos ni eventos | Plan de retorno con reparación o compensación | Snapshots y registro de decisiones aplicadas | Ensayar retorno después de escrituras reales |
| R097 Apagado corta operaciones en curso | Graceful shutdown y drenaje con plazo | Sondas y terminación coordinada | Terminar worker durante un commit |
| R098 Credenciales compartidas amplían el impacto | Identidad por servicio y autorización explícita | Secret store o identidad administrada según entorno | Rotar revocar y comprobar denegación efectiva |
| R099 Se entrega otro artefacto distinto al verificado | Aprobación vinculada a digest y alcance | Repositorio protegido y promoción inmutable | Sustituir artefacto y bloquear entrega |
| R100 Todos los tests heredan la misma suposición falsa | Oráculo independiente y cualificación | Baseline protegida y verificador controlado | Sembrar fallo común y comprobar rechazo |

---

[← Anexo D · Decisiones de arquitectura](anexo-d-decisiones-de-arquitectura.md) · [Índice](../README.md) · [Anexo F · Glosario operativo →](anexo-f-glosario-operativo.md)
