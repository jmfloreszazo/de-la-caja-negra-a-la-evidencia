# Protocolo de ejecución H01/H02 entre hosts externos (pendiente)

**Estado:** diseño y protocolo reproducible. La prueba distribuida permanece NOT_EXECUTED. Vinculado a #30; se conservan las pruebas anteriores de 14 casos nativos en un solo host.

## Preparación
- Separar cliente sintético, gateway/inyector y core .NET 10 en hosts distintos, declarando también los roles de PostgreSQL y del observador SQL independiente. Varias máquinas virtuales en un mismo servidor no demuestran dominios físicos independientes.
- Utilizar cuentas ficticias y una red reservada exclusivamente al laboratorio, sin equipos ATM reales, datos bancarios, PIN/HSM ni endpoints de producción.
- Exigir listas de acceso y autenticación de transporte a nivel de red/host. **No convertir el proxy `OneShotTransportFault`, limitado a loopback, en un servicio remoto expuesto sin autenticación.** Esa restricción debe mantenerse.
- Registrar SHA exacto (40 caracteres en Git SHA-1 actual o 64 en Git SHA-256), digests de imágenes, versiones, incertidumbre de sincronización de relojes y marcas temporales. Los relojes monótonos de hosts diferentes no son directamente comparables.
- Preparar consultas SQL de solo lectura independientes sobre identidad/fingerprint, decisión, dos apuntes, outbox, holds y saldos.

## Secuencia
1. Comprobar aislamiento de la red, seguridad y estado inicial.
2. H01-a: pérdida cliente→gateway antes de la recepción; verificar ausencia de transacción observada por el propietario.
3. H01-b: COMMIT del core y pérdida posterior de respuesta; guardar SQL antes del replay.
4. H02-a: pérdida gateway→core antes de entrega; registrar sockets y observaciones del core.
5. H02-b: pérdida de respuesta core→gateway después del COMMIT; consultar autoridad y repetir exactamente el mismo ID/fingerprint.
6. Probar replay idéntico y conflicto de fingerprint. Prohibir duplicación financiera, autorizaciones automáticas de efectivo o cambio de escritor en UNKNOWN.
7. Conservar resultados FAIL/INCONCLUSIVE y originales sin modificar, con seis archivos por caso y SHA-256.
8. Ejecutar `python3 scripts/check_channel_hop_campaign.py <bundle>/manifest.json` para verificar la recepción. Un resultado estructural satisfactorio requiere todavía auditoría independiente: no es PASS distribuido.

## Límites
Actions solo ejecuta controles del verificador. No existe todavía una campaña ejecutada entre hosts físicos, pruebas de mainframe CICS/Db2, ISO 8583, equipos bancarios, HA independiente ni autorización de cliente. TODM G2 INCONCLUSIVE y G6 BLOCK. Sin nueva release.
