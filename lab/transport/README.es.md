# M1 · gRPC/Protobuf frente a REST/JSON: experimento reproducible de transporte

**Estado: implementación pendiente de evidencia CI. No es rendimiento bancario.** [English](README.md).

El mismo servicio .NET 10 expone una decisión de transferencia **sin persistencia**, mediante REST/JSON y gRPC/Protobuf. Ambos usan **HTTP/2 en localhost sin TLS (h2c)** para comparar transporte y serialización bajo el mismo host; no se mide aún la WAN, TLS, Kubernetes, Azure ni el ledger PostgreSQL.

El oráculo de pruebas comprueba todas las respuestas, además de rechazar deliberadamente una respuesta incorrecta. Se registran p50, p95, p99, respuestas/s, errores, concurrencia, orden de ensayos, versión de runtime y commit. Hay calentamiento y dos rondas por protocolo alternando A/B/B/A. En CI se ejecutan 2.500 peticiones por ronda con concurrencia 8 y 32, guardadas en informes distintos; son cargas *closed-loop*.

```bash
dotnet restore lab/transport/TransportLab/TransportLab.csproj
dotnet build lab/transport/TransportLab/TransportLab.csproj -c Release --no-restore
dotnet lab/transport/TransportLab/bin/Release/net10.0/TransportLab.dll benchmark 5088 2500 8 lab/results/transport/report-c8.json
python3 lab/transport/check_report.py lab/results/transport/report-c8.json
```

Son métricas **closed-loop** del transporte, no operaciones contables confirmadas ni una medición representativa de sucursal bancaria. **No se afirma que gRPC sea más rápido sin resultados.** Tampoco se contrapone gRPC a HTTPS: gRPC funciona normalmente sobre HTTP/2 y TLS.

**Siguientes puertas**: repetir con TLS/mTLS; cargas, conexiones y tamaños variados; comparar ingress/mesh de AKS y ACA; ensayar 1/2/4/8/16 réplicas; conectar ambos protocolos al mismo PostgreSQL con claves calientes, oráculo independiente y coste por commit. El issue #12 contiene los criterios. Los resultados CI se publicarán como artefactos y solo se promoverán a evidencias versionadas tras verificarlos.
