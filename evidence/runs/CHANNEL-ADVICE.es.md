# Advice tardío y efectivo incierto — ejecución sintética original de 33 casos

[English](CHANNEL-ADVICE.md) · [PR #98](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/98) · [Actions original #42024266243](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42024266243) · [Investigación ES](../../docs/research/channel-late-advice.es.md).

**5 de noviembre de 2026. Resultado: PASS_33_SYNTHETIC_ADVICE_CHECKS; NO equivale a un ATM físico, una red de tarjetas o aceptación bancaria.**

## Campaña original identificada

El job `127234409728` de GitHub Actions ejecutó **33 de 33 pruebas Python positivas y adversariales sin errores inesperados**, sobre SHA de código y checkout `291829f8cda34604f692a03dff6794f6cec0f51c`. Se han comprobado mensajes idénticos repetidos, STAN-like reutilizado entre terminales, mensajes con el mismo ID y contenido distinto, discrepancia de autorización/terminal/RRN-like/época de origen/importe, efectivo desconocido-cero-parcial, asientos duplicados o sin prueba, reverso tardío sobre dispensación parcial y falsa autoaprobación stand-in.

Los resultados del fixture original fueron:
- `CASH-001: MATCHED_PARTIAL_CASH` (10.000 solicitados; 6.000 acreditados de manera ficticia por dispositivo y ledger).
- `CASH-002: UNKNOWN_REQUIRES_DEVICE_EVIDENCE` (8.000 solicitados; sin resultado físico definitivo ni cargo, aunque llega advice).
- `CASH-003: FINAL_ZERO_CASH` (5.000 solicitados; dispositivo informa cero y aparece una **solicitud** de reverso, no un reverso contabilizado).
- `CASH-004: STAND_IN_DENIED` (sin delegación del emisor; no existe autorizador alternativo).

El [extracto literal de las 33 pruebas](CHANNEL-ADVICE-PR98-ORIGINAL-CI-EXCERPT.log) conserva timestamps originales. El [registro JSON](channel-advice-pr98-original-ci-summary.json) conserva el SHA y el alcance exacto.

GitHub publicó el artifact `channels-advice-synthetic-original-not-iso8583-or-cash` (ID `13412439030`), **2371 bytes** y SHA-256 `4cc2ea7009d514e462cab8a173bc6fae2c5c36804ef7af49c79e9441151d0950`. **No hemos descargado/recalculado de forma independiente el ZIP original**; el digest es el informado por GitHub, no una comprobación independiente de bytes.

## Garantías y límites

Todos los estados, incluido el PASS sintético, retienen `safeToAutoDispense=false`, `safeToAutoPost=false`, `safeToAutoReverse=false`, `productionApproved=false`, `realCardNetworkTested=false`, `physicalDeviceJournalAuthenticated=false` y `standInDelegationApproved=false`. **Este módulo jamás ejecuta una operación financiera.** Un conjunto inventado pero coherente de autorizaciones, journal, asientos y mensajes podría superar sus controles.

Este incremento es independiente del [experimento nativo anterior de dos bases](../../docs/CHANNELS_CHECKPOINT_2026-11-03.es.md), que ejercita HTTP .NET 10, PostgreSQL y reinicios sobre **un dispositivo ficticio**. Su resultado no acredita ATM físico, homologación ISO 8583/NDC/DDC, contrato de red, PIN/HSM, HA física ni reglas parciales/de reverso/stand-in aprobadas por un banco.

Para una aceptación real habría que obtener, con autorización, mensajes originales de switch, estado emisor y oráculo contable, registros físicos de entrega/retracción y resultados de dispositivo, retención de mensajes tardíos, delegación del emisor y fallos de equipo/red instrumentados bajo una política validada. **#30 sigue ABIERTO** para el catálogo L01–L16 y el resto de escenarios. Sin release nueva. **TODM G2 INCONCLUSIVE / G6 BLOCK**; E2 continúa `partially_verified`.
