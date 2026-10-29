# E3 · Protocolo de medida WAN de oficinas (sin resultados todavía)

**No existe en el repositorio una medición de WAN de sucursales reales.** La [comparación del capítulo 25 bis](../book/es/parte-5-capacidad/25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md) incluye cálculos explicativos, no un resultado de un banco. [English](NETWORK_PROTOCOL.md).

## Registro mínimo por escenario

- Clase de sede (urbana, regional, internacional), zona horaria, ruta de fibra/ISP cuando esté disponible, red SD-WAN/MPLS/VPN y circuito redundante.
- Identificadores técnicos seudonimizados, nunca nombres de clientes, IP privadas o credenciales en un repo público.
- Región Azure, zona, gateway, FastPath activado o desactivado, NVA/firewall, subred, límites de la VM y del motor SQL.
- Operación bancaria medida, tamaño de petición/respuesta, canal (TN3270, HTTP/2, gRPC), reutilización de TLS, autenticación, idempotencia y resultado de commit.
- **De teclado a pantalla**: traza correlacionada con tiempos p50, p95 y p99, además de pérdidas, jitter, timeout y fallback.
- Distribución con online+batch, claves calientes, porcentaje de errores y colas, oráculo contable independiente, failover N-1 y recuperación.

## Aceptación

1. Ejecutar el candidato local, Azure e híbrido con **misma carga, datos representativos y política de durabilidad**.
2. Capturar al menos un ciclo pico, una ventana batch y pérdida controlada de un enlace; medir recuperación y operaciones ambiguas.
3. Diferenciar RTT a red, tiempo interno CICS y tiempo completo percibido; no sumar percentiles de componentes para inventar un p99.
4. Publicar un informe reproducible con herramientas/versiones, SHA, resultados, inconclusos y condiciones; exigir aprobación del contrato de capacidad.
5. **No promover E3 a verificado** sin mediciones de despliegues reales y los controles de negocio.

## Modelo educativo, no benchmark

```bash
python3 lab/network/test_wan_model.py
python3 lab/network/wan_model.py
```

`illustrative_scenarios.json` está etiquetado `ILLUSTRATIVE_ASSUMPTIONS`. Ningún valor corresponde a la latencia observada de un banco. La columna de ahorro modelado muestra el coste de las llamadas secuenciales; no representa un SLA y no es p99. El experimento de campo E3 continúa pendiente.
