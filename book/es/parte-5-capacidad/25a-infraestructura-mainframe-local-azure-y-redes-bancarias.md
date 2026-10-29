**Español** · [English](../../en/part-5-capacity/25a-mainframe-on-prem-azure-and-banking-network-infrastructure.md)

[← Capítulo 25 · Azure o una máquina enorme en el cliente](25-azure-o-una-maquina-enorme-en-el-cliente.md) · [Índice](../README.md) · [Parte VI · El laboratorio →](../parte-6-laboratorio/README.md)

# Capítulo 25 bis · Infraestructura frente a un mainframe actual: local, Azure y la red de oficinas

> **Tesis.** No se sustituye un mainframe con una máquina de más núcleos. Se sustituye un servicio operacional completo: procesamiento transaccional, I/O, aislamiento, commit duradero, continuidad y respuesta desde una oficina situada quizá a miles de kilómetros. La equivalencia es una prueba de extremo a extremo, no una comparación de fichas comerciales.

Este capítulo complementa el [capítulo 25](25-azure-o-una-maquina-enorme-en-el-cliente.md) con referencias comerciales identificables y un protocolo para falsar el diseño. **Datos de producto consultados en octubre de 2026; resultados de rendimiento propios frente a esos equipos: ninguno.**

## Equipos reales, números reales y una comparación que todavía no podemos hacer

| Referencia de mercado | Capacidad anunciada por el fabricante | Qué representa y qué NO demuestra |
|---|---|---|
| [IBM z17 ME1](https://www.ibm.com/products/z17) | Hasta **208 engines**, **64 TB** de memoria y CPU Telum II a **5,5 GHz** | Mainframe IBM Z para cargas críticas; 208 engines configurables no equivalen a 208 vCPU x86 ni a TPS verificadas |
| [IBM LinuxONE Emperor 5](https://www.ibm.com/downloads/documents/us-en/1227cc9e78cb9240) | Hasta **208 engines**, **64 TB**, **5,5 GHz** | Arquitectura de clase IBM Z centrada en Linux; no sustituye automáticamente a z/OS/CICS/Db2 ni es una segunda medición de TPS |
| [Unisys ClearPath Forward Dorado 8590](https://www.unisys.com/siteassets/collateral/pi-sheet/pi-200145-clearpathforwarddorado8590.pdf) | Publica una escala de **200–8.400 MIPS/mes** y techo de **12.000 MIPS** por partición OS 2200; especifica **925 MIPS** por procesador monohilo | **MIPS propio del fabricante** y modelo comercial concreto; no comparable directamente con IBM Z ni con vCPU |
| [Azure Mdsv3 Very High Memory](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/memory-optimized/mdsv3-vhm-series) | Tamaños publicados de **896 a 1.792 vCPU**, hasta **30.400 GiB**, red hasta **185 Gbit/s** y disco remoto hasta **8 GB/s** | Ficha de VM; no implica capacidad de commit de un ledger ni que la región, cuota o coste permitan usarla |
| [Nodo local AMD EPYC 9965](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9965.html) | **192 núcleos/384 hilos por socket**, plataforma 1P/2P, 12 canales DDR5 y hasta 3,7 GHz turbo | Candidato de CPU para servidores físicos. Dos sockets podrían aportar **384 núcleos físicos**, pero no 384 motores IBM ni la resiliencia de un mainframe |

Las cifras de memoria, núcleos, frecuencia, MIPS comerciales y ancho de banda **son especificaciones de fabricante, no resultados de nuestro laboratorio**. Además, IBM z17 y LinuxONE pertenecen a familias con componentes emparentados: no deben sumarse sus capacidades como si fueran sistemas en un benchmark común. La documentación de [zPCR](https://www.ibm.com/support/pages/getting-started-ibm-z-processor-capacity-reference) permite estudiar configuraciones de capacidad de IBM Z; tampoco es una tabla universal de «MIPS por vCPU».

Una migración concreta necesita antes un **workload fingerprint**: curvas de TPS/CICS, consumo MSU y zIIP, CPU por transacción, distribución de claves, I/O de Db2/VSAM, tamaños reales de datos, p99 por operación, ventanas batch, dependencias síncronas, recuperación y coste. Sin eso, cualquier «equivalencia» de hardware es publicidad.

## La oficina bancaria está lejos: la WAN es parte de la transacción

Una pantalla 3270 puede tener un perfil de red distinto al de una SPA que hace doce peticiones REST. IBM documenta que los terminales actuales suelen llegar a z/OS mediante **TN3270/TN3270E sobre TCP/IP**, y que una métrica interna de CICS **no incluye** todo el viaje por controladores y red hasta que el usuario ve la respuesta ([conexión 3270](https://www.ibm.com/docs/en/cics-ts/6.x?topic=security-3270-connections-zos); [observación de tiempos](https://www.ibm.com/docs/en/cics-ts/6.x?topic=constraints-observing-response-time)). **No confundamos CICS internal response time con branch-to-screen response time.**

La restricción física tampoco desaparece con ExpressRoute: la luz viaja aproximadamente a 200.000 km/s en fibra. Un recorrido de **1.000 km reales de fibra** tiene un límite ideal de unos **10 ms de ida y vuelta**, antes de colas, equipos, inspección, rutas no directas y aplicación. No es una medición de una ruta bancaria. Microsoft recuerda que el **trazado físico de la fibra y la distancia** dominan la latencia WAN ([guía ExpressRoute](https://learn.microsoft.com/en-us/azure/expressroute/expressroute-troubleshooting-network-performance)).

### Presupuesto de respuesta desde el teclado hasta la pantalla

El presupuesto no termina en el `HTTP 200` del backend:

```text
Oficina / TN3270 o navegador
  | LAN + SD-WAN/MPLS/VPN + proveedor + encaminamiento + TLS
  v
Entrada / gateway / autenticación / anti-fraude
  | routing, admission control, cola, salto(s) entre servicios
  v
.NET 10 / CICS adaptador de coexistencia
  | bloqueo de clave caliente + log de commit + réplica síncrona
  v
Ledger autoritativo / outbox
  | respuesta + red de vuelta + renderizado de pantalla
  v
Empleado de la sucursal
```

Separaría los tiempos: `L_WAN-RTT`, handshake/sesión, autenticación, colas, aplicación, adquisición de locks, log duradero y renderizado. **El p99 de una suma no es, en general, la suma de los p99 individuales**: se debe medir la distribución de la operación completa, con trazas correlacionadas.

**Ejemplo ilustrativo, NO observado:** supongamos RTT de oficina de 35 ms. Si una pantalla obliga a cuatro viajes secuenciales adicionales al servidor, solo esos viajes aportan cerca de **140 ms** de espera en el camino crítico, sin contar CPU, DB ni jitter. Con una única operación gruesa de negocio se puede reducir ese coste, siempre que no se cargue la semántica transaccional o se permita una confirmación prematura. **Menos chattiness puede importar más que duplicar cores.**

### Comparar cuatro caminos de entrada

| Camino | Cómo lo probaría | Riesgo a vigilar |
|---|---|---|
| Oficina → red bancaria → centro de datos local → CICS | Transacción TN3270/host, RTT y tiempo real de pantalla, por percentiles y zona | Cabeceras antiguas, sesiones, concentradores, saltos y cuello de botella del host |
| Oficina → SD-WAN → ExpressRoute → Azure | `Connection Monitor` desde emplazamientos, HTTPS de negocio, p99 de aplicación y reintentos | Circuito y gateway, inspección, saltos y distancia hasta la región |
| Oficina → SD-WAN → hub Azure Virtual WAN → servicio | Rutas efectivas, vHub/NVA, failover de enlace, doble inspección y pérdida | *Hairpin*, concentraciones y capacidad de NVA/gateway |
| Oficina → edge de integración local → núcleo en Azure | Un solo comando validado, idempotency key, outbox y resultado visible | Enlace interrumpido, doble confirmación, estado inconsistente u operaciones pendientes |

[ExpressRoute](https://learn.microsoft.com/en-us/azure/networking/hybrid-connectivity/hybrid-connectivity) proporciona una vía privada y más predecible, **no teletransporte**. [FastPath](https://learn.microsoft.com/en-us/azure/expressroute/about-fastpath) puede reducir saltos del gateway bajo requisitos concretos. [Virtual WAN/SD-WAN](https://learn.microsoft.com/en-us/azure/virtual-wan/sd-wan-connectivity-architecture) ayuda a conectar sucursales, pero cada inspección o salto debe medirse. Evitaría *hairpin* entre VNets a través de ExpressRoute cuando exista peering adecuado ([guía de misión crítica](https://learn.microsoft.com/en-us/azure/well-architected/mission-critical/mission-critical-networking-connectivity)).

**Muy importante:** un edge de sucursal puede almacenar lectura autorizada, iniciar solicitudes y presentar estado; **no debe confirmar débitos o créditos como definitivos si el ledger autoritativo no ha confirmado el commit**. Pérdida de conectividad significa PENDING/INCONCLUSIVE, reconciliación posterior y una sola aplicación idempotente, no saldo inventado.

## Tres blueprints dimensionables

| Diseño | Topología candidata (NO sizing aprobado) | Dónde suele estar el límite |
|---|---|---|
| **On-premises crítico** | Dos o más nodos físicos x86 de alta densidad (p. ej. EPYC), dominio SQL HA, NVMe empresarial, redes 25/100 GbE, réplica y segundo CPD; acceso desde WAN del banco | Durabilidad real del log, locks, NUMA, NIC, sincronización de réplicas, mantenimiento con un nodo menos |
| **Azure transaccional** | .NET 10 en VMs/AKS/App Service según necesidad, SQL HA en misma zona/región lógica, Private Link/ExpressRoute, Front Door o gateway según el modelo de acceso, observabilidad end-to-end | VM + cuotas, IOPS de VM **y** disco, log, RTO de failover, gateway, dependencia entre zonas |
| **Híbrido de coexistencia** | CICS/Db2 existente preservado detrás de fachada autorizada; nuevas capacidades en Azure/local; gateway con contratos, outbox y ownership inequívoco del ledger | Chattiness cross-site, transacciones distribuidas, cola, reconciliación y duplicidad semántica |

No pondría la aplicación en una región y el ledger síncrono al otro lado del océano. Si los dos tienen que coordinar cada commit, esa **latencia entra en el p99 y puede limitar el throughput**, por más núcleos que compremos. El objetivo será reducir dependencias seriales, colocar el dato autoritativo cerca del cálculo crítico y diseñar particiones por dominio sin romper el grano contable. La opción local también requiere segunda ubicación y un ensayo real de pérdida de nodo.

## Un contrato medible para las sucursales

Antes de comparar, definiría una muestra representativa y aprobada: sucursal urbana cercana, sucursal regional, internacional, red degradada y operación tras failover. No fijaría RTT ni SLA desde el escritorio de arquitectura. Mediría **p50/p95/p99 por operación y por sede**, separado del tiempo interno de CICS, más loss/jitter, DNS, TLS, sesión, bloqueos, log duradero, propagación de réplica, edad de colas, timeouts y reintentos.

El ensayo se debe ejecutar con carga **online + batch**, claves calientes, replicación y picos; repetir con 0,1 % y 0,5 % de pérdida **inyectada (no observada)**, jitter parametrizado y retirada de un enlace o una instancia. Cada prueba guardará `commit SHA`, config de región/ruta, versión de cliente y servidor, percentiles, coste y veredicto del oráculo. [Azure Connection Monitor](https://learn.microsoft.com/en-us/azure/network-watcher/connection-monitor-overview) sirve para observar RTT y pérdidas, pero una prueba TCP/ICMP **no reemplaza** la latencia de la transacción real.

La aceptación exige equivalencia de **resultados de negocio, finalización durable, recuperación y latencia percibida**, no solo TPS. Una red rápida sin un ledger correcto no sirve; un ledger correcto con pantallas inaceptables tampoco.

## Evidencia propia: qué hay y qué no hay

El laboratorio de esta rama sí dispone de [resultados E1a/E1b versionados](../../../evidence/runs/README.es.md): deadlock real `40P01`, serialización `40001`, oráculo que detecta corrupción, y paridad parcial .NET 10/Npgsql frente a PostgreSQL. **No existe todavía benchmark del IBM z17, LinuxONE, Dorado 8590, Azure Mdsv3 o EPYC**, ni medida desde una oficina a cientos de kilómetros. La matriz de evidencia no puede promover esas comparativas hasta disponer de carga reproducible, SLO aprobado y mediciones in situ.

> La arquitectura que gana no es la que corre más deprisa dentro del CPD. Es la que confirma la operación correcta y se la devuelve a la oficina, incluso cuando el peor día de red coincide con el cierre contable.

---

[← Capítulo 25 · Azure o una máquina enorme en el cliente](25-azure-o-una-maquina-enorme-en-el-cliente.md) · [Índice](../README.md) · [Parte VI · El laboratorio →](../parte-6-laboratorio/README.md)
