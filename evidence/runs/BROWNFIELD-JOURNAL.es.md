# C2 · Journal duradero de admisión/UNKNOWN — evidencia original

**Tramo técnico verificado, 1 de noviembre de 2026.** La [ejecución real de Actions #41342450730](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41342450730) terminó correctamente sobre HEAD exacto `8dc391d276724726eca68373150dfceaf1e291e0`; job original `124955148855`.

- El [JSON extraído del log original](brownfield-c2-pr66-ci-log-extracted.json) conserva los controles y ambos oráculos SQL. **Procede del texto del log**; no se presenta como copia binaria del ZIP original.
- Artefacto subido ID **13098480178**, nombre `brownfield-c2-journal-synthetic-g6-block`, tamaño **3145 bytes**. SHA-256 del ZIP informado por GitHub: `e0479df604fd607825a794b2b00a3487d9103cbc46aa8887d897f6f1a6175827`.
- La ejecución mostró `status=PASS` y **11 controles completados**: caídas reales de proceso, reintento sin duplicar tras pérdida de ACK, rechazo de decisión falsificada, fallo del controlador, admisión estricta en ambos adaptadores y detección del bypass al desactivarla.
- El resultado final `lastJournalAudit.passed=false` es un **control negativo intencionado**, no un PASS falso: `J-ADMIT-DEAD` y `J-DISPATCH-DEAD` permanecen UNKNOWN y `J-DIRECT-BYPASS` se detecta sin journal. Los oráculos contables de los dos almacenes fueron verdaderos.

**Límites:** tres contenedores PostgreSQL desechables en UN runner Linux; no se prueban dominios físicos independientes ni fencing CICS/Db2. El modo estricto es opt-in, las dos épocas cambian en transacciones no atómicas y no existe aprobación bancaria real. G2=INCONCLUSIVE, G6=BLOCK. Issues #64/#58 abiertas y #53 congelada. La evidencia corresponde a ese HEAD histórico; los cambios documentales posteriores tienen otros SHA. No se publica nueva release.
