# Campaña H01/H02 entre hosts independientes — recepción de evidencias

**Estado: verificador de recepción restrictivo implementado; campaña distribuida NO ejecutada.** Vinculado a #30. No se reinterpretan las pruebas anteriores con TCP local y PostgreSQL en una sola máquina.

## Diseño de ejecución

Separar cliente sintético, gateway, core .NET 10, PostgreSQL desechable y oráculo SQL de solo lectura en hosts administrativamente independientes, identificando los dominios de fallo. Registrar topología, identificadores, digests de imágenes, límites TLS, sincronización temporal, SHA de código y órdenes de inyección. Separar contenedores o máquinas virtuales no prueba independencia física. Usar Podman, no Docker. Sin datos de clientes ni dispensación real de efectivo.

H01 interrumpe cliente→gateway antes del envío o tras el COMMIT cuando se pierde la respuesta. H02 interrumpe gateway→core, con pérdidas direccionales, resets y respuestas retrasadas. La recuperación debe conservar el mismo ID sin doble efecto financiero. La ausencia de respuesta no demuestra rechazo. El oráculo independiente verifica decisión SQL, dos apuntes compensados y outbox; no extrapolar a efectivo físico.

## Protocolo de evidencias

El manifiesto externo requiere `schemaVersion=1`, SHA exacto de 64 caracteres, `syntheticDisposable=true`, `productionApproved=false`, `todmG2=INCONCLUSIVE`, `todmG6=BLOCK`, roles de host cliente/gateway/core/database/oracle con `hostId` y `failureDomain` y exactamente dos casos H01/H02. Cada caso indica resultado local PASS/FAIL/INCONCLUSIVE, ID de operación, ventana de inyección, observación SQL independiente y ausencia de automatismos inseguros/duplicados. Cada caso aporta rutas relativas y SHA-256 de seis archivos originales: fallo, cliente, gateway, core, snapshot SQL y salida del oráculo.

```bash
python3 scripts/check_channel_hop_campaign.py /ruta/al/bundle/manifest.json
python3 -m unittest discover -s scripts -p test_channel_hop_campaign.py -v
```

El verificador valida la estructura, confines del bundle y hashes de ficheros reales; los incompletos devuelven `INCONCLUSIVE` (salida 2). Un expediente completo solo obtiene `READY_FOR_MANUAL_EVIDENCE_REVIEW` (salida 0), **nunca PASS**. Un auditor debe verificar de forma independiente procedencia, capturas, tiempos, SQL y autoridad. Es posible falsificar un expediente internamente coherente: la comprobación estructural no autentica máquinas. Se mantienen G2 INCONCLUSIVE, G6 BLOCK, sin aprobación bancaria, equivalencia mainframe, HA física ni autorización de release. La ejecución externa y la integración editorial completa siguen pendientes.
