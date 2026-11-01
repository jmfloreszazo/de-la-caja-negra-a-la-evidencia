# SQL persistente brownfield — evidencia sintética original de la PR #61

**Alcance:** PostgreSQL 16.13 desechable, en un único runner Linux Ubuntu
24.04 de GitHub; SDK .NET 10.0.403 y Npgsql 10.0.3; sin sistemas bancarios
externos. Documentamos **lo realmente ejecutado**, no una prueba pendiente.

- [Ejecución original #41323384008](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41323384008): **PASS**, incluido el oráculo SQL independiente y la subida del artefacto.
- SHA exacto del código probado: `531a221a6f8cbd625f1c8abe2c0f7b419b6f762d` (antes de este commit documental).
- Artefacto original de Actions ID `13089779910`, nombre `brownfield-synthetic-postgresql-not-business-g6`. SHA-256 del ZIP descargado: `dc40553f52f5c7fc2d7e4e7bb6e224ea348702e1786d070bdde6b0831b4b31bb`.
- [JSON original extraído literalmente del log del runner](brownfield-durable-pr61-original-summary.json): 1.924 bytes. SHA-256 del JSON del ZIP: `dcded8e7f7bb4bdbe77fb68acb8b815521858790354c0754760591f269aa903a`.
- El ZIP contiene además `build.log` (0 errores, 0 avisos) y `provenance.txt` (SO, .NET, Podman 4.9.3, SHA de fuente/checkout y digests/IDs de la imagen PostgreSQL). Se recupera desde la ejecución original.

## Resultados observados

| Observación | Valor |
| --- | --- |
| Operaciones | 15 (11 COMMITTED, 4 REJECTED) |
| Apuntes contables / outbox | 22 / 11 |
| Watermark / escritor y época finales | 15 / `legacy`, 3 |
| Invariantes SQL independientes | 11/11 TRUE |
| Control negativo de apunte corrupto | Rechazado por el oráculo independiente y restaurado |
| `SIGKILL` real antes de COMMIT | PASS con una instancia PostgreSQL desechable |
| Salida después de COMMIT, antes de respuesta | PASS y reintento duplicado con igual ID |
| Cuenta caliente, versión, fencing y rollback simulado | PASS en el fixture |
| TODM G6 | BLOCK |

**Límites:** datos sintéticos, 16 cuentas, una autoridad SQL y una máquina.
`legacy` y `candidate` son dos modos de la misma implementación. No
acredita alta disponibilidad física, coexistencia con mainframe real,
conciliación independiente entre bases, política bancaria aprobada,
equivalencia de rendimiento ni Golden Master validado por negocio.

**Integridad:** el JSON versionado procede literalmente de la salida del
runner original. El ZIP de Actions y su SHA-256 son la prueba primaria.
Una CI posterior no cambia la identidad del código ejecutado.
