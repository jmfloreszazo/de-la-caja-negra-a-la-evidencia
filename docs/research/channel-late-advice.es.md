# Advice tardío en ATM: por qué la respuesta de red no acredita el efectivo entregado

**Issue #30 · 5 de noviembre de 2026 · investigación y prueba sintética falsable.** [English](channel-late-advice.en.md) · [Acta anterior del laboratorio .NET/PostgreSQL](../CHANNELS_CHECKPOINT_2026-11-03.es.md) · [Código de correlación](../../lab/channels/advice_gate.py).

## Cuatro autoridades diferentes y cinco identificadores

El **dispositivo ATM** observa el movimiento físico de los billetes y puede mantener su journal electrónico; el **switch o la red** transporta autorizaciones, advices y solicitudes de reverso; el **core emisor** conserva la autoridad sobre retenciones, asientos y estado de la operación; el **procesador o esquema** puede tener obligaciones diferentes de autorización, compensación, liquidación y disputas. Los registros no tienen por qué llegar en orden. Una autorización no demuestra ni dispensación ni liquidación.

El fixture separa deliberadamente **operationId**, **authorizationId**, **terminalId**, **networkTrace** (campo ilustrativo tipo STAN) y **retrievalReference** (campo ilustrativo tipo RRN). Un número corto de seguimiento puede repetirse entre terminales o intervalos: **no es por sí solo una clave financiera única y duradera**. La correlación real requiere el contexto del mensaje, la encarnación del origen y el perfil del proveedor. Este JSON sintético **no** implementa ISO 8583, NDC/DDC ni un protocolo de marca homologado.

La [guía pública de disputas Visa (2024)](https://www.visa.mn/content/dam/VCOM/global/support-legal/documents/merchants-dispute-management-guidelines.pdf) contempla el supuesto de efectivo ATM no recibido o recibido parcialmente y exige documentación de dispensación o de abono/reverso. Esto justifica conservar y conciliar el journal físico, **no** aprobar automáticamente un resultado de red. El [aviso de seguridad de NCR (2021)](https://assets-global.website-files.com/64a2be73942e1d57fed077f3/65296c8ffb7b891a9f5d48d5_NCR_Security_Advisory_2021_02_TRF_Rev_1.0.pdf) advierte del riesgo de políticas de reverso cuando el efectivo realmente pudo estar accesible. Ninguna de esas fuentes define la política contable de un banco no identificado.

## Contrato adversarial del escenario

| Autorización / dispositivo / mensaje | Dictamen | Inferencia prohibida |
| --- | --- | --- |
| CORE autoriza 10.000 unidades menores; dispositivo acredita 6.000; ledger registra 6.000; advice idéntico repetido | `MATCHED_PARTIAL_CASH` | No segundo cargo ni segunda dispensación por duplicado |
| CORE autoriza 8.000; dispositivo informa `UNKNOWN`; llega advice de 8.000 | `UNKNOWN_REQUIRES_DEVICE_EVIDENCE` | El advice no demuestra entrega ni autoriza contabilizar cero o todo |
| CORE autoriza 5.000; journal definitivo acredita cero; llega solicitud de reverso | `FINAL_ZERO_CASH` | Solicitar reverso no significa que el ledger haya efectuado el abono |
| Core inaccesible; el switch propone *stand-in* **sin delegación del emisor** | `STAND_IN_DENIED` | Prohibido autorizar, cargar o entregar efectivo offline automáticamente |

Un **reverso íntegro después de entregar efectivo parcialmente** obliga a revisión y bloquea la conciliación automática. También se rechazan advices contradictorios, un mismo ID de mensaje con contenido distinto, asientos duplicados, terminal o autorización desajustados, ausencia de journal y un supuesto stand-in autoaprobado. La política bancaria para dispensación parcial y disputas debe establecerla el propietario y el esquema correspondiente.

Las [reglas publicadas de Mastercard (edición 2025)](https://www.mastercard.us/content/dam/public/mastercardcom/na/global-site/documents/transaction-processing-rules.pdf) describen rutas de stand-in por timeout según reglas de red/emisor; [CSFi](https://www.csfi.com/ezswitch-2/) documenta un producto que puede utilizar límites y un fichero de saldos positivos. **Ninguna fuente prueba que un banco determinado haya delegado autoridad stand-in para efectivo.** El fixture se mantiene explícitamente en *DENIED*.

## Alcance de la prueba

Las [33 pruebas positivas y negativas preparadas](../../lab/channels/test_advice_gate.py) cubren identidades, repetición, amounts, journal desconocido frente a cero, asientos, revisión de reversos y rechazo de falsa delegación. No usan red de tarjetas, ATM físico, firmas verificadas ni datos originales del banco; no escriben en el ledger. **Un fixture inventado pero internamente coherente podría pasar.** Incluso con PASS, `safeToAutoPost=false`, `safeToAutoReverse=false`, `safeToAutoDispense=false` y `productionApproved=false`; **TODM G2 INCONCLUSIVE / G6 BLOCK**.

Esta prueba **complementa**, no sustituye, el laboratorio anterior con .NET 10 y dos bases PostgreSQL en Podman, ni sus siete grupos de oráculos financieros. Para aceptación real hacen falta reglas aprobadas por el emisor, journal de dispositivo original autenticado, entrega/retracción física, campos y ventanas reales de la red, eventos del procesador, particiones y recuperación reales, disputas externas y límites HSM/PCI. El repositorio público usará siempre datos ficticios. Sin release nueva ni autorización de corte.
