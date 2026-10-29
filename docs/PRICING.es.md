# Comparativa económica fechada · Azure, local y mainframe

**Comprobación: 29 de octubre de 2026.** Esta es una comparación de **componentes de coste y modelos de operación**, no un TCO bancario ni una equivalencia en MIPS. [English](PRICING.md). El registro fuente está en [`lab/cost/dated_prices.json`](../lab/cost/dated_prices.json).

## Precios accesibles al público

| Concepto | Valor registrado | Fecha del dato | Fuente y alcance |
|---|---:|---|---|
| Azure Linux **D4as_v5**, West Europe, pago por uso | **134 €/mes**, cifra publicada redondeada | Artículo 06-10-2026; comprobado 29-10-2026 | [AzureScan](https://www.azurescan.eu/en/insights/older-vm-generations/). Precio de VM, sin discos, BD, red, impuestos, soporte |
| Azure Linux **D4s_v5**, West Europe, pago por uso | **148 €/mes**, cifra publicada redondeada | Artículo 06-10-2026; comprobado 29-10-2026 | [AzureScan](https://www.azurescan.eu/en/insights/older-vm-generations/), mismas exclusiones |
| AMD **EPYC 9965** | **11.988 USD por CPU (precio 1.000 unidades)** | Ficha fabricante consultada 29-10-2026 | [AMD](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9965.html). **No es el precio de un servidor**, y no es precio minorista |
| IBM z17 / LinuxONE, Unisys Dorado | **No hay cotización comparable pública** | Estado comprobado 29-10-2026 | Solicitar RFQ: hardware, licencias, capacidad, mantenimiento y soporte, sin inventar cifra |

Para reproducir la consulta **directamente** contra Microsoft, el workflow [`infrastructure-pricing.yml`](../.github/workflows/infrastructure-pricing.yml) usa la [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), región `westeurope`, moneda EUR y SKU exactos. Guarda un artefacto con fecha/hora de recuperación, `effectiveStartDate`, `meterId` y candidatos a medidor; **no modifica** automáticamente los importes editoriales hasta revisarlos. Microsoft advierte que fija sus precios en USD y que los EUR de la API son referenciales.

## Qué calculamos de verdad

Para **3 workers D4as_v5 encendidos 730 h/mes**, solo proceso: `3 × 134 = 402 €/mes`. Para **6 workers todo el mes**, `6 × 134 = 804 €/mes`. Un clúster AKS con 3–6 nodos equivalentes comparte **esa línea de proceso**, pero añade gestión del plano de control cuando proceda, almacenamiento, red, balanceadores, telemetría y motor de datos. Dos VMs que consuman 4 vCPU no son equivalentes a cuatro máquinas de 1 vCPU sin pruebas, ni VMSS equivale a 3 pods ni el coste de AKS equivale al de sus nodos.

**Estos cálculos NO constituyen presupuesto total**. ACA Consumption requiere segundos activos/inactivos de vCPU y GiB y el modelo de solicitudes; App Service requiere región, plan y réplicas. La [facturación ACA](https://learn.microsoft.com/en-us/azure/container-apps/billing) incluye 180.000 vCPU-s, 360.000 GiB-s y 2 millones de solicitudes HTTP de asignación gratuita por suscripción, sujeto a condiciones. El plano de control de AKS tiene niveles [Free, Standard y Premium](https://learn.microsoft.com/en-us/azure/aks/free-standard-pricing-tiers); el coste del nodo y del plano de control se presupuestan por separado.

Para un **servidor local 2P EPYC 9965** son dos procesadores; para HA con dos nodos equivalentes son **cuatro CPUs × 11.988 USD = 47.952 USD** a precio de referencia 1KU. No incluye chasis, RAM, NVMe, switches, 25/100 GbE, segundo CPD, electricidad, mantenimiento, licencias, DBA, backups ni recuperación. **USD y EUR no se suman ni comparan sin un cambio de moneda documentado y una base temporal común**.

## Las facturas que no caben en «precio de VM»

- **Red de oficinas**: circuito ExpressRoute, proveedor, gateway, FastPath si procede, salida, NVA, inspección, NAT, VPN/SD-WAN y contingencia. [Microsoft explica los componentes y esquemas de datos de ExpressRoute](https://learn.microsoft.com/en-us/azure/expressroute/plan-manage-cost).
- **Ledger autoritativo**: SQL Managed Instance / PostgreSQL / SQL Server según diseño, IOPS y throughput de log, copia, almacenamiento y réplicas, licencias y recuperación.
- **Escala horizontal**: mínimo N-1 por zona, CPU/memoria efectiva por pod, HPA y Cluster Autoscaler, arranque en frío, sobreaprovisionamiento y reservas.
- **Operación**: observabilidad, retención de trazas, certificados y claves, respuesta a incidentes, despliegue, soporte, seguridad y cambios.
- **Precio por transacción de negocio confirmada**, no por vCPU. Incluye errores, reintentos, colas, claves calientes, latencia del terminal y degradación.

## Modelo reproducible

```bash
python3 lab/cost/test_cost_model.py
python3 lab/cost/cost_model.py
python3 lab/cost/fetch_azure_prices.py   # requiere acceso a Azure Retail API
```

El resultado solo indica subtotales modelados; su campo `estimated_tco` es **null** si faltan costes. Los **precios de fabricante y las cotizaciones contractuales deben pedirse a cada proveedor**, manteniendo soporte y licencias explícitos.

El análisis completo de escala y transporte se añade al [capítulo 25 bis](../book/es/parte-5-capacidad/25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md). **El experimento E3 de costes reales y carga representativa sigue pendiente.**
