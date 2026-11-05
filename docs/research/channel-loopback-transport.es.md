# Fallos reales de TCP en loopback sobre un core financiero .NET 10 desechable

[English](channel-loopback-transport.en.md) · [Issue #30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30) · [Contrato del laboratorio nativo](../../lab/channels/CONTRACT.md) · [Oráculo anterior de saltos ficticios](channel-hop-failures.es.md)

**Corte de investigación: 5 de noviembre de 2026. Se ejercita una conexión TCP local real; no un cajero físico, switch bancario, WAN con dominios independientes ni aceptación de producción.**

## Diferencia frente a las siete trazas JSON anteriores

El [modelo de 40 controles por salto](channel-hop-failures.es.md) validaba la *coherencia de eventos declarados*. Ahora interponemos un **proxy TCP de un solo uso** en `127.0.0.1` entre el cliente Python HTTP y el **API existente ChannelsLab en .NET 10**, respaldado por las dos bases PostgreSQL desechables originales. El proxy escucha en un puerto local dinámico, solo transmite `POST /transfer` al puerto fijo y previamente comprobado del core, y cierra después sus sockets. El oráculo SQL independiente continúa leyendo cuentas, operaciones, apuntes, outbox, retenciones y el almacén simulado del dispositivo.

El proxy conserva el mismo `operationId` y los bytes de la petición. Rechaza destinos distintos de loopback, puertos fuera del laboratorio, otras rutas, cuerpos excesivos o streaming, modos desconocidos y procesos sin autorización de entorno desechable. Almacena la huella SHA-256 de los bytes HTTP, **no el cuerpo original ni credenciales de clientes**. No permite configurar un endpoint bancario externo. La transferencia ficticia mueve **6.000 céntimos** entre las cuentas inventadas 1 y 2.

## Tres nuevos casos nativos en sockets TCP reales

| Caso | Intervención observada | Observación de la autoridad SQL | Recuperación exigida |
| --- | --- | --- | --- |
| `tcp-drop-before-forward` | El cliente envía una petición TCP; el proxy la recibe y emite un reset **sin conectarse al core** | SQL no contiene operación, apuntes ni evento outbox antes del reintento | Se reutiliza el ID original; el primer COMMIT legítimo crea un único par de apuntes |
| `tcp-drop-after-owner-response` | El proxy reenvía la petición y observa HTTP 200 de .NET **posterior a CommitAsync**; resetea el socket del cliente sin reenviar la respuesta | Antes del retry hay una sola operación COMMITTED, dos apuntes compensados y un único outbox | El cliente ve UNKNOWN; consulta de estado del propietario y replay del ID original devuelven `duplicate=true`, sin segundo cargo |
| `tcp-delay-owner-response` | El proxy ve el HTTP 200 del core después del COMMIT y retrasa la respuesta 0,8 s, frente a un timeout del cliente de 0,15 s | El COMMIT y el outbox original permanecen en SQL | Timeout del cliente, consulta autoritativa y retry del mismo ID sin duplicaciones |

Conservamos los **diez escenarios nativos anteriores** del laboratorio, incluidos efectivo parcial, pérdida de respuesta de dispositivo, SIGKILL externo del core antes del COMMIT y concurrencia ATM/móvil. Añadimos tres intervenciones distintas sin modificar la evidencia histórica ni confundir pérdida de respuesta TCP con efectivo físico perdido. Los nuevos casos son **transferencias digitales**, no comandos reales de dispensación. El [verificador independiente de evidencias](../../scripts/check_channel_transport.py) exige el testigo del proxy, el UNKNOWN del cliente, el snapshot SQL **anterior al replay**, el oráculo financiero y el estado final posterior. Además, hay 14 [pruebas de seguridad del proxy](../../lab/channels/test_transport_proxy.py).

## Qué demuestra y qué no

La ejecución proporciona evidencia de un **reset de socket TCP local o respuesta retrasada** sobre procesos .NET y PostgreSQL desechables. **No** equivale a `tc netem` sobre interfaces del kernel, pérdida de paquetes entre hosts, caída de switch, sucursal desconectada, protocolo ISO 8583 homologado, UOW real de CICS/Db2, consulta a un emisor bancario ni entrega física de billetes. Ambas bases siguen en **un único host**. La consulta de estado solo es autoritativa **dentro de la maqueta financiera**. El HTTP 200 del proxy se contrasta con SQL; no convierte un testigo sintético en un log bancario auténtico.

El ensayo *before-forward* puede demostrar que **nuestro proxy controlado no envió** una petición al servidor. En una red real, **el timeout del cliente por sí solo nunca prueba que no hubo COMMIT**. Reintentar con un **ID nuevo** sería peligroso. El banco deberá aprobar las reglas de identidad, ambigüedad, timeout, retención y disputas, autenticar los COMMIT del origen y comprobar los efectos físicos externos.

### Pendientes de aceptación operativa

Para aproximarnos al canal real se necesitan componentes ATM/switch/emisor aislados en una red de pruebas autorizada, capturas de transporte y aplicaciones independientes, inyección de fallos **entre hosts** y puertos reales, logs originales de COMMIT, journals auténticos de dispensación/retracción, reglas de tarjeta y *stand-in*, y demostración de fencing sobre todos los escritores antiguos. Las particiones físicas, la recuperación con dominios independientes y la aprobación de riesgos bancarios quedan **abiertas**, no se ocultan dentro de un PASS.

Aunque pasen todos los controles de la maqueta, **TODM G2 = INCONCLUSIVE, G6 = BLOCK**; sin permiso de cutover ni operación financiera real. E2 permanece `partially_verified`, #53 congelado y la release no cambia.
