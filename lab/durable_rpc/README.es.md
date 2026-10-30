# M2 · Ledger persistente en REST y gRPC, escalado horizontal local

[English](README.md)

M2 extiende M1: REST/JSON y gRPC/Protobuf llaman a **la misma implementación .NET 10/Npgsql**, que confirma transacciones reales en PostgreSQL 16.13 y produce dos asientos y un evento outbox atómicos.

Se ejecutan **20 pruebas**: dos protocolos × distribución uniforme o 50 % de operaciones contra una cuenta caliente × 1, 2, 4, 8 y 16 procesos de servicio. Cada una envía 256 transferencias, concurrencia 16. Antes de cada caso se recrea **una base de datos desechable**; después un oráculo SQL independiente valida saldos, conservación, asientos y outbox. Un control negativo elimina deliberadamente un asiento para exigir rechazo y recupera luego su integridad.

Los JSON contienen commits/s, p50/p95/p99 y reparto por proceso. **Todos los procesos se ejecutan en el mismo runner Linux** con una única base de datos; se usa HTTP/2 sin TLS y carga *closed-loop*. No debe presentarse como escalado Azure/AKS ni como latencia de sucursal, ni como benchmark MIPS. Una cuenta caliente puede neutralizar cualquier aumento de réplicas por la serialización de sus bloqueos.

Ejecución local: consulta las órdenes Podman y las variables de entorno de [README en inglés](README.md). El script `python3 lab/durable_rpc/test_m2.py` **destruye las tablas**; no debe apuntarse a datos reales.

La CI exporta los resultados como artefacto. Cuando se verifique un run, se añadirá al registro de evidencias; E1 y E3 no se promueven por este ensayo parcial.

**Siguientes experimentos:** TLS/mTLS, balanceo real entre nodos, carga abierta, failover, claves calientes y coste de infraestructura Azure/servidor local.
