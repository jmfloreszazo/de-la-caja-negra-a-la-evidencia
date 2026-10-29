# Comparativa económica fechada · Azure, local y mainframe

**Comprobación: 29 de octubre de 2026.** Esta es una comparación de **componentes de coste y modelos de operación**, no un TCO bancario ni una equivalencia en MIPS. [English](PRICING.md). El registro fuente está en [`lab/cost/dated_prices.json`](../lab/cost/dated_prices.json).

## Precios accesibles al público

| Concepto | Precio público | Capturado | Fuente y alcance |
|---|---:|---|---|
| Azure Linux **D4as_v5**, West Europe, consumo | **0,1830 €/h; 133,59 €/730h** | **29-10-2026 18:26 UTC** | [Microsoft Retail Prices API](https://prices.azure.com/api/retail/prices); medidor `b69c5dbc-6df2-5b78-8822-fb32b72f3d64`, tarifa vigente desde 01-11-2021 |
| Azure Linux **D4s_v5**, West Europe, consumo | **0,2024 €/h; 147,75 €/730h** | **29-10-2026 18:26 UTC** | [Microsoft Retail Prices API](https://prices.azure.com/api/retail/prices); medidor `1ab41620-5ffa-51b3-ac16-6416f9f747a9`, tarifa vigente desde 01-11-2021 |
| Azure Linux **D8as_v5**, West Europe, consumo | **0,3661 €/h; 267,25 €/730h** | **29-10-2026 18:26 UTC** | [Microsoft Retail Prices API](https://prices.azure.com/api/retail/prices); medidor `caee42fb-5e41-5ffa-8aa6-65e1d871b269`, tarifa vigente desde 01-11-2021 |
| AMD **EPYC 9965** | **11.988 USD por CPU (precio 1.000 unidades)** | Ficha consultada **29-10-2026** | [AMD](https://www.amd.com/en/products/processors/server/epyc/9005-series/amd-epyc-9965.html). **No es el precio de un servidor** |
| IBM z17 / LinuxONE, Unisys Dorado | **Sin cotización comparable pública** | **29-10-2026** | RFQ con hardware, software, capacidad, soporte y operación |

El [snapshot estructurado de la API](../lab/cost/official_retail_snapshot.json) conserva el precio por hora, el medidor, fecha de vigencia, hora de captura y [ejecución CI](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/40930736857). Su `effectiveStartDate` es el comienzo de vigencia de la tarifa, **no** el día en que hemos consultado el precio. Una referencia secundaria [AzureScan, 06-10-2026](https://www.azurescan.eu/en/insights/older-vm-generations/) daba importes redondeados cercanos; queda como contraste histórico, no como fuente vigente.

Para reproducir la consulta **directamente** contra Microsoft, el workflow [`infrastructure-pricing.yml`](../.github/workflows/infrastructure-pricing.yml) usa la [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices), región `westeurope`, moneda EUR y SKU exactos. Guarda un artefacto con fecha/hora de recuperación, `effectiveStartDate`, `meterId` y candidatos a medidor; **no modifica** automáticamente los importes editoriales hasta revisarlos. Microsoft advierte que fija sus precios en USD y que los EUR de la API son referenciales.

## Qué calculamos de verdad

Para **3 workers D4as_v5 encendidos 730 h/mes**, solo proceso: `3 × 0,1830 × 730 = 400,77 €/mes`. Para **6 workers todo el mes**, `6 × 0,1830 × 730 = 801,54 €/mes`. Un clúster AKS con 3–6 nodos equivalentes comparte **esa línea de proceso**, pero añade gestión del plano de control cuando proceda, almacenamiento, red, balanceadores, telemetría y motor de datos. Dos VMs que consuman 4 vCPU no son equivalentes a cuatro máquinas de 1 vCPU sin pruebas, ni VMSS equivale a 3 pods ni el coste de AKS equivale al de sus nodos.

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
