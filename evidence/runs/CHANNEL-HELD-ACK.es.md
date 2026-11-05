# Evidencia original: ACK de TCP retenido y ocho recuperaciones concurrentes

[English](CHANNEL-HELD-ACK.md) · [Contrato técnico ES](../../docs/research/channel-held-ack.es.md) · [GitHub Actions original #42052288542](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/42052288542) · [PR #101](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/101).

**5 de noviembre de 2026: PASS acotado de sockets TCP localhost y core financiero .NET 10/PostgreSQL ficticio; NO es una prueba de WAN, ATM real o aceptación bancaria.**

## Ejecución original, no simplemente un diseño

- **SHA de fuente y checkout:** `67981c24d9164f8952e1e24ce8ecd1ec4bb582ff`; run `42052288542`, job `127331264991`.
- **18/18** controles de seguridad del proxy real y barrera de ACK **PASS**; **14/14** casos nativos de .NET 10 con dos PostgreSQL desechables **PASS** (diez históricos, tres TCP ya existentes y el nuevo escenario de concurrencia).
- **Oráculo SQL y transporte independiente:** `PASS_BOUNDED_LIVE_LOOPBACK_TRANSPORT`.
- **27/27** controles de evidencias originales **PASS**: un informe original válido y **26 modificaciones deliberadamente corruptas rechazadas**. Entre los negativos están el ACK liberado antes de tiempo, reintentos ausentes, duplicados falsos, cambio de ID de operación, asientos repetidos antes del ACK antiguo, supuesta aprobación de un importe distinto y una barrera de ocho clientes falsificada. Los resultados nombrados con timestamps se conservan en el [extracto del log original](CHANNEL-HELD-ACK-PR101-ORIGINAL-CI-EXCERPT.log); la salida completa permanece en el artifact de Actions.

El artifact original `channels-synthetic-original`, ID `13426084608`, contiene **23.371 bytes** y GitHub informa SHA-256 `d012bf14f8e6e58a724df819d413dc0b765ecad4cb0ec4788078f400c281fa6b`, con expiración inicial el **3 de febrero de 2027**. El digest es **metadato de GitHub, no un hash recalculado de manera independiente sobre el ZIP descargado**. [Procedencia estructurada](channel-held-ack-pr101-original-ci-summary.json).

## Qué comprueba el nuevo cuarto escenario TCP

1. El proxy acepta el `POST /transfer` original, lo reenvía al servidor .NET real y observa HTTP 200 tras su COMMIT en PostgreSQL, pero **retiene esa respuesta antigua**.
2. El primer cliente recibe timeout TCP y observa UNKNOWN. SQL ya contiene **una operación COMMITTED, dos apuntes compensados y un outbox**.
3. Una consulta de estado devuelve COMMITTED. **Ocho clientes TCP arrancan sincronizados mediante una barrera de ocho participantes** y repiten exactamente el mismo ID e intención. Todos devuelven COMMITTED y `duplicate=true`.
4. La petición con ese ID pero importe distinto devuelve `ID_CONFLICT`. El oráculo revisa SQL **antes de liberar el ACK antiguo**: una sola decisión, dos apuntes y un outbox.
5. Solo entonces se libera la respuesta inicial. Los timestamps monotónicos en **el mismo host** demuestran HTTP 200 anterior a la recuperación y liberación posterior. El estado final mantiene saldos ficticios **4.000 / 16.000 / 0 céntimos**, sin orden a un dispensador.

Se prueba una política de idempotencia sobre un core sintético **realmente ejecutado**, no una garantía general de exactly-once en pagos y redes externas.

## Límites independientes

Son **sockets TCP localhost reales**, .NET 10 y PostgreSQL transaccional, pero no una partición WAN entre hosts, pérdidas del kernel con `tc netem`, ATM/switch real, CICS/IMS/Db2 del emisor, PIN/HSM, journal de billetes físicos, política aprobada por banco, conciliación de terceros, fencing del host antiguo, capacidad productiva ni cutover. La respuesta se retiene en un proxy de pruebas controlado; no se reproduce un protocolo homologado de fabricante. Ocho clientes locales tampoco son un benchmark de MIPS.

El issue #30 sigue **ABIERTO**, igual que #58 para fencing real. TODM **G2 INCONCLUSIVE / G6 BLOCK**, E2 `partially_verified` y #53 congelado. Sin nueva release ni autoridad bancaria.
