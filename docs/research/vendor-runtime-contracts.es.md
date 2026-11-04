# Contratos de ejecución por fabricante: ¿qué sobrevive realmente a la migración?

[English](vendor-runtime-contracts.en.md) · [Catálogo de fuentes](../../research/vendor-runtime-contracts/catalog.json) · [Capítulos 1](../../book/es/parte-1-antes-de-traducir/01-el-mainframe-no-es-una-caja-rapida.md) y [13](../../book/es/parte-4-patrones/13-antes-de-elegir-un-patron-identifica-el-contrato.md).

**Corte de investigación: 4 de noviembre de 2026 · #17/#18/#28 · SIN ejecución nativa ni aceptación bancaria.** Este incremento contiene **11 registros y 10 referencias**, no completa todos los fabricantes ni las 236 entradas del plan. Desconocemos el hardware, SO y motor de datos de una instalación real. Las fechas y límites de recuperación se conservan: la documentación IBM se recuperó por índice, pero devolvió HTTP 403 al abrirla directamente; las páginas técnicas Unisys y el anuncio archivado de Fujitsu sí se pudieron leer. Cada afirmación queda limitada a la fuente concreta.

## Entrevistar al operador y al DBA, no convertir MIPS en vCPU

Pedir al cliente, con autorización: fabricante/modelo/año/firmware, CPC/LPAR o particiones, SO y versión; monitor, UOW, base de datos, registros, seguridad, batch/JCL/scheduler, efectos externos, journals/recovery, topología de E/S y de canal, WAN/terminales, clases de servicio, codificación de registros, contrato de soporte y licencia. Exigir **trazas de operación y recuperación autorizadas**, ventanas normal/pico, p50/p95/p99 de la **transacción completa**, demora de cola y COMMIT duradero, retención, RPO/RTO y propietario de cada ruta de escritura. Nunca subir datos bancarios o secretos al laboratorio público.

### Matriz de atribución

| Origen y fuente | Frontera observada que interesa | Patrón candidato, sin equivalencia | Prueba que puede bloquear |
| --- | --- | --- | --- |
| IBM Z CSS, PR/SM y WLM; [CSS](https://www.ibm.com/docs/en/zos-basic-skills?topic=mainframe-channel-subsystem-css), [WLM](https://www.ibm.com/docs/en/zos/3.2.0?topic=tabs-service-classes) | CPU central, partición, clases de servicio y E/S de canales son **mecanismos diferentes** | Admisión, colas acotadas, redundancia de storage, escalado horizontal medido | Bajo presión de CPU o caída de log, p99 del canal crítico no preservado |
| Db2 for z/OS 13, [BIND ISOLATION](https://www.ibm.com/docs/en/db2-for-zos/13.0.0?topic=services-isolation) | UR/CS/RS/RR, locks, commit y opciones de paquete | SQL ACID con política de retry y oráculo financiero concurrente | Lectura sucia o asiento inconsistente bajo concurrencia |
| IBM i 7.6, [commitment control](https://www.ibm.com/docs/en/i/7.6.0?topic=database-commitment-control) | Trabajo/activation group y recursos journaled; no es CICS/Db2 z/OS | Proyección subordinada al origen y reconciliación con posición del journal | Falla un trabajo y sobrevive un apunte incompleto |
| Unisys MCP 21.0, [EDB Access](https://www.support.unisys.com/aseries/docs/ClearPath-MCP-21.0/38508198-005/section-000081944.html) | Organización, recuperación y orden de selección de registros | ACL de claves/orden + modelo canónico y contraste | Un índice SQL entrega filas en otro orden o duplicadas |
| Unisys OS 2200 ePortal TIP 10, [configuración](https://www.support.unisys.com/ePortalIC-10.0/topic/82073594_clearpath_eportal_developerhelp/html/section-000039403.htm) | Reenvío tras error de envío potencialmente inapropiado para sesiones con estado | Idempotencia por operación, consulta duradera de resultado | COMMIT sin ACK y retry produce segundo asiento |
| Fujitsu GS21 3600/3400, [anuncio de 2018](https://info.archives.global.fujitsu/global/about/resources/news/press-releases/2018/0417-01.html) | Modelos anunciados, pero **SO, DB, batch y soporte instalados desconocidos** | RETENER + inventario y manual específico | Atribuir CICS/Db2 o CDC sin evidencia del cliente |
| NEC ACOS / Bull GCOS sin modelo | **NOT_VERIFIED**: desconocido, no necesariamente ausente | RETENER, identificar release, motor y manual primario | Afirmar función presente/ausente sin fuente |

**No unir IBM Z, IBM i y Unisys en una sola fila llamada «mainframe».** MCP y OS 2200 son familias distintas, aunque tengan el mismo fabricante. Una nota comercial histórica no confirma qué producto o versión se utiliza en un banco en 2026.

## Una traza financiera que hay que preregistrar

```text
Sucursal / ATM / móvil
  -> WAN / switch o gateway de canal / autenticación
  -> admisión y prioridad en host
  -> monitor / ID durable de operación
  -> Db2, EDB, IMS, VSAM o almacén realmente instalado
  -> camino de acceso, índice, buffer pool, lock
  -> escritura de log y COMMIT duradero
  -> efectos externos: MQ, compensación, efectivo y conciliación
  -> respuesta, ACK, reintento y consulta del resultado
```

Por cada salto registrar ID de operación y de traza, época del escritor, subsistema/versión, timestamps y limitaciones de sincronización, decisión de COMMIT, reintentos, posición del log, efectos externos y estado cierto o UNKNOWN. El p99 extremo a extremo debe calcularse sobre solicitudes correlacionadas, **no sumar percentiles de tramos distintos**. Es una plantilla de entrevista, no una medición real ni una arquitectura universal.

## Tres escenarios y sus contrapruebas

**Consulta intensiva:** read model para saldo contable, caché con obsolescencia y fallback. Medir proporción lectura/escritura, fallos de caché, lag y edad. Rechazar que un saldo proyectado pueda autorizar gasto o sea linealizable por haber visto un reloj.

**Escritura intensiva:** transferencia interna con dos apuntes, outbox y propietario duradero. Medir cuentas calientes, esperas, reintentos, log flush y COMMIT. Rechazar una saga entre dos actores si el contrato bancario exige atomicidad inmediata.

**Canal y recuperación:** TIP OS 2200 o app CICS/IMS con pérdida de respuesta **después del COMMIT**. Mantener contexto, ID de operación y resultado original; un retry de transporte nunca demuestra que el asiento deba repetirse.

En ocasiones conviene **conservar** el motor original y modernizar solo una interfaz ACL o una proyección de lectura. Migrar sin conocer la frontera de recuperación puede ser peor decisión que la convivencia controlada.

## Control reproducible de integridad del catálogo

`python3 scripts/check_vendor_runtime_contracts.py --self-test` ejecuta **25 casos positivos y negativos del metadato**. El validador rechaza atribución errónea, fuente/versiones sin verificar, fechas inventadas, falta de oráculo, autoaprobación, supuestos tests nativos, falsos «no soportado» y confundir un anuncio Fujitsu de 2018 con paridad técnica. **No ejecuta un mainframe ni compara cargas de clientes.** Véase [README del catálogo](../../research/vendor-runtime-contracts/README.md).

**Pendientes:** #17 requiere investigación profunda de CPU/memoria/E/S, diagramas y trazas medidas; #18 ampliar familias/red flags; #28 completar cobertura, batch, offline, mensajería y catálogo extenso solo con fuentes; #58 demostrar fencing y aceptación del banco. #53 congelado. **TODM G2 INCONCLUSIVE / G6 BLOCK**; sin nueva release.
