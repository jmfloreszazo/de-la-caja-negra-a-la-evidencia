# W01 — Journal transaccional sintético: integrado, sin pruebas ejecutadas

**Fecha del corte: 4 de noviembre de 2026.** [English](W01_SOURCE_JOURNAL_CHECKPOINT.md) · [PR #94](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/pull/94) · [Issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).

## Estado verificable

El código está integrado en `main`, commit `69bb2e92fbfac66038d6ce1ca3234b020feb2d52`. La cabeza exacta del PR era `80c45437312030a8abe90e0c3fdaa85a00c3056a`. En el momento de la fusión, GitHub Actions mantenía todos los workflows **en cola**. Estado científico: **IMPLEMENTADO / NO EJECUTADO**. No afirmamos 22/22 PASS.

Ejecuciones programadas: [W01 Journal #41864738886](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738886), [Premerge #41864738991](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738991), [Lab #41864739021](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739021), [Book #41864739153](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739153), [Evidence #41864739038](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739038), [W01 anterior #41864739079](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864739079) y [Brand #41864738914](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41864738914). Son referencias a trabajos en cola, no resultados.

La [matriz ES](EVIDENCE.es.md) y [EN](EVIDENCE.md) registra por separado este incremento como `BROWNFIELD-W01-FEED`, sin reutilizar las ejecuciones históricas de 16/16 y 20/20 de la proyección anterior.

## Alcance técnico del laboratorio

El [código y procedimiento Podman](../lab/brownfield/w01_feed/README.md) incorporan un journal transaccional de prueba con secuencias, snapshot `REPEATABLE READ`, replay, comprobación de integridad y cursor confirmado junto con los saldos del destino. Hay **22 pruebas preparadas**: huecos, modificaciones imprevistas, imágenes previas incorrectas, rollback, repetición y escritores concurrentes.

La secuencia y el hash anterior se obtienen mientras el escritor de pruebas mantiene un bloqueo del reloj en PostgreSQL. Evita una carrera del fixture, pero crea un punto de contención. El ensayo se limita a 16 cuentas y un máximo de 256 operaciones, no a cargas bancarias.

## Ejecución y decisión

Para obtener un **PASS técnico acotado** es necesario ejecutar el [procedimiento Podman](../lab/brownfield/w01_feed/README.md) en dos bases PostgreSQL desechables, validar las **22 pruebas**, conservar logs originales, JSON, SHA del código, identidad de imagen y resultados adversariales. El harness restablece esquemas y **no debe usarse con datos reales de clientes**. El último caso adversarial deja un journal intencionadamente inconsistente; no hay que interpretar una auditoría posterior como si partiera de un fixture limpio.

Si los workflows no llegan a ejecutarse, permanecerá `NOT_EXECUTED`. Si aparecen fallos, deben conservarse y corregirse antes de atribuir cualquier PASS. No se ha demostrado CDC de plataforma real, alta disponibilidad, linealizabilidad, seguridad de origen bancario ni autenticidad del journal frente a administradores privilegiados.

**TODM G2 = INCONCLUSIVE; G6 = BLOCK.** E2 continúa `partially_verified`. #32 cerrado como investigación, #58 abierto para aceptación del cliente, #53 congelado. Este incremento no constituye una release.
