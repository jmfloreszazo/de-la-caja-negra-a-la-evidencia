# Hoja de ruta abierta — estado basado en evidencias (2 de noviembre de 2026)

[English](ROADMAP.md) · **Español**

Esta es la hoja de ruta **del repositorio**, no una declaración de que una migración bancaria esté lista para producción. Los estados oficiales de afirmaciones están en [evidence/claims.json](evidence/claims.json) y el protocolo de aceptación detallado en [docs/EXPERIMENT_ROADMAP.md](docs/EXPERIMENT_ROADMAP.md). Diferenciamos observado, simulado, propuesto y aprobado por negocio. El código, las pruebas y los README del laboratorio van exclusivamente en inglés; el libro se mantiene en ES/EN.

## Situación actual

| Línea de trabajo | Estado contrastado | Qué falta para cerrarla |
| --- | --- | --- |
| Libro, diagramas y CI bilingüe | **Integrado**: 37 capítulos numerados más dos complementarios, 41 diagramas por idioma, capítulo 28 ampliado con convivencia y PDF de vista previa reproducibles | Revisión editorial y técnica, listados ilustrativos, reproducción multiplataforma; la vista previa no es una release |
| E1 PostgreSQL y SQL Server | **Parcialmente verificado**: CI sobre SQL real y desechable, oráculos independientes, subconjuntos de paridad .NET 10, concurrencia y controles negativos | Alcance funcional E1 completo, fallo eléctrico/HA, contrato del cliente y carga productiva |
| E2 Orleans | **Parcialmente verificado y ejecutado**: pruebas de varios procesos/silos con Podman en una máquina, membership PostgreSQL, ledger durable, fallos y carga limitada; [#8](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/8) | [Anomalía C01 #44](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/44), [PR #34 C04 en draft](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/34), particiones asimétricas, hosts físicos/HA y capacidad sostenida [#25](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/25) |
| Brownfield CAP-007/005 | **Subconjuntos sintéticos verificados en CI y fusionados**: época de escritor SQL, transacciones .NET 10, adaptador legado de caja negra, dos almacenes PostgreSQL distintos, shadow, conciliación y veto al rollback; [#58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58) | Particiones del journal persistente durante operaciones y recuperación restante [#64](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/64), fencing real en el origen, políticas/mandatos/Golden Master del cliente y aprobación TODM G2/G6 |
| Descomposición funcional | **Inventario sintético**: 30 hipótesis de capacidades y 12 dominios, reescritura functional-first; [#32](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/32) | Trazas autorizadas, reglas aprobadas, límites de dominio y aceptación independiente; sin parser COBOL obligatorio y sin conversión 1:1 |
| E3 Azure/local/híbrido | **Diseñado, sin capacidad verificada**: M1/M2, precios de referencia fechados y modelo WAN son entradas, no un PASS de E3; [#9](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/9), [#12](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/12) | Contrato de carga aprobado, saturación abierta y commits/p99, dominios de fallo, WAN, gRPC/REST con TLS comparable y TCO integral fechado |
| E4 agentes y Oracle Gates | **Diseñado, no ejecutado ni aceptado como E4**; [#10](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/10) | Alcance de escritura del agente, propuestas evaluadas reproducibles, mutaciones de oráculos, revisión y aprobación independientes |
| Investigación mainframe, canales y arquitectura | **En desarrollo**: [#17](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/17), [#18](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/18), [#28](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/28), [#29](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/29), [#30](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/30) | Contraste con fabricantes, z/OS/I-O/Db2/CICS/IMS, ATM/móvil/web/sucursal, batch, colas offline y decommissioning |
| Mantenimiento | **Abierto**: refactor del laboratorio [#15](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/15), protección de main [#16](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/16) (aplazada expresamente), reproducción [#11](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/11) | Preservar checks, enlaces, evidencias originales y SHA antes de cambiar estructura o reglas |

## Incrementos ya integrados

- [PR #59](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/59): inventario de brechas brownfield y controles sintéticos, distinguiendo pruebas de aprobación funcional.
- [PR #60](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/60): ensayo de cutover con bloqueo por defecto, **en memoria**, sin garantía duradera ni fencing real del legado.
- [PR #61](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/61) y [#62](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/62): .NET 10/Npgsql duradero con PostgreSQL, caída real de proceso, pérdida de respuesta y procedencia del SHA de `main`.
- [PR #63](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/63): legado sintético de caja negra y candidato en dos contenedores PostgreSQL diferentes, conciliación de SQL independiente, shadow sin dobles apuntes y veto al rollback tras escrituras nuevas. Capítulo 28 ampliado en ambos idiomas. SHA integrado `d04623e8c276bedda9918e87a09fa0c3f9da1f6a` y [CI original de dos almacenes en main #41340310748](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41340310748) **PASS**. Ambos oráculos 10/10, ocho decisiones en origen y diez en destino: la divergencia bloqueó correctamente el rollback.
- La [evidencia original EN](evidence/runs/BROWNFIELD-TWO-STORE.md) / [ES](evidence/runs/BROWNFIELD-TWO-STORE.es.md) conserva tanto la anomalía del primer checkout temporal de la PR como la repetición corregida sobre el SHA exacto.

Todo ello es **ingeniería sintética**. No hemos observado ningún sistema bancario real; TODM G2 permanece INCONCLUSIVE y G6 en BLOCK. Dos contenedores en un runner no representan dos dominios físicos de fallo.

- PR #66/#68/#69: journal duradero, gateway e inscripción persistida. En `279ca566`, [C2 main #41353221630](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41353221630) superó 20 controles y ambos oráculos 10/10. La [ejecución original de 19 controles](evidence/runs/BROWNFIELD-C2-RECOVERY.es.md) se conserva sin reatribuir cobertura. Siete workflows aplicables de ese main pasaron; Release omitido.

## Orden de ejecución a partir de ahora (sin fechas inventadas)

1. Consolidar libro y documentación ES/EN con las evidencias; mantener los SHA y resultados históricos.
2. Completar C2 #64: particiones en operaciones en curso, pérdida de bloqueos y ventanas de respuesta; aprobación funcional y fencing real pendientes en #58/#32.
3. Actualizar el capítulo 28 con contrato, implementación, fallo, corrección, evidencia y límites.
4. Completar los gates acotados de E2 #8/#24/#25: C01/C04, particiones, repeticiones de carga, diagnóstico y dominios físicos.
5. Preparar una vista previa de la siguiente edición: revisión inglesa, citas, solapes, listados y QA visual ES/EN; publicar solo tras el corte editorial autorizado.
6. Ejecutar E3 #9/#12 con carga, infraestructura, WAN y TCO comparables; después E4 #10.

**Congelado:** [#53](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/53), clean rooms/confidential computing, queda fuera del plan activo hasta nueva indicación. La protección de rama [#16](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/16) también está aplazada, aunque sigue abierta.

## Ediciones y releases

La edición estable publicada es [`v2026.10.29`](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.29). Existe además la **pre-release publicada** [`v2026.10.31-rc1`](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/releases/tag/v2026.10.31-rc1), distinta de la edición estable. Las fusiones posteriores y los PDF de vista previa en CI **no** publican automáticamente una nueva edición; requiere autorización y workflow de release controlado.

**Regla de evidencias:** una parte verificada no eleva toda la fase a PASS. Conservar SHA exacto, run ID, digest, controles negativos originales y procedencia; CI no equivale a aprobación bancaria.
