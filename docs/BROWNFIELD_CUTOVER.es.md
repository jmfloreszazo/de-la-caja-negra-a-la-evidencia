# CAP-007 / CAP-005 brownfield — coexistencia, corte y reversión

**Clasificación:** diseño y simulación contractual, **no** un experimento aceptado sobre PostgreSQL. [English](BROWNFIELD_CUTOVER.md) · [Seguimiento #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58)

## La frontera arquitectónica es la autoridad financiera

Que escribamos desde cero un reemplazo en .NET 10 no convierte la modernización bancaria en un proyecto greenfield. El core existente ya gobierna transacciones visibles al cliente, calendarios de negocio, histórico, interfaces y auditoría. La unidad de migración es **una capacidad de negocio y sus datos autoritativos**, no un microservicio por programa COBOL traducido.

Un adaptador de canal o capa anticorrupción puede invocar el sistema heredado o el nuevo, pero una transferencia debe tener **un único escritor autoritativo**. Ejecutar ambos con permisos de escritura para comparar resultados duplicaría los efectos financieros. El modo sombra puede comparar solicitudes saneadas, decisiones y representaciones de lectura; el candidato no debe emitir pagos externos, asientos ni eventos de outbox.

## Contrato de simulación (Python, no gate de producción)

El código está en [`lab/brownfield/coexistence_gate.py`](../lab/brownfield/coexistence_gate.py) y las pruebas negativas independientes en [`test_coexistence_gate.py`](../lab/brownfield/test_coexistence_gate.py).

1. Un `operationId` estable y una huella íntegra distinguen duplicados, conflictos, operaciones en curso y respuestas ambiguas. Un timeout no demuestra que haya ocurrido un rollback.
2. Antes de cortar hay que drenar las solicitudes en vuelo y resolver cada `UNKNOWN` mediante observación duradera independiente. Una declaración de conciliación sin registros subyacentes **no es evidencia**.
3. Deben compararse por separado *saldos, operaciones, asientos y outbox*, además del número de operaciones y los watermarks monotónicos. La igualdad de dos hashes suministrados manualmente es solo una **premisa del escenario sintético**.
4. Una transición **simulada** cambia el único escritor en memoria e incrementa su época. Una solicitud con época obsoleta se rechaza. El fencing distribuido real exige autoridad persistida atómicamente y protección de **todos** los puntos de escritura, también batch y canales de oficinas desconectadas.
5. La reversión es **otra migración**, no un cambio de configuración. Si el candidato ha confirmado transferencias nuevas, el sistema heredado debe ponerse al día y conciliarse de manera independiente antes de recuperar la autoridad.

La simulación mantiene deliberadamente `TODM G6 = BLOCK`. Sus controles negativos al estilo G5 no prueban funcionamiento en PostgreSQL, un Golden Master aprobado por el cliente, una política firmada ni autorización de despliegue.

## Experimento duradero necesario — todavía no demostrado aquí

Preparar una instancia descartable de PostgreSQL 16 y un reemplazo .NET 10/Npgsql 10.x, reutilizando **ideas** de E1 sin alterar la evidencia histórica. Proteger en una transacción atómica los identificadores estables, débito/crédito, dos asientos, outbox y una época de escritura validada por la base de datos. La lectura CAP-005 debe separar **saldo contable** de **fondos disponibles** y rechazar una proyección obsoleta; no se deben inventar retenciones ni mandatos del cliente.

Demostrar SIGKILL antes de COMMIT, terminación después de COMMIT pero antes de la respuesta, reintento e inspección SQL persistente por un oráculo independiente. Conservar SHA de origen, entorno, digest de imagen PostgreSQL, tiempos y resultados favorables y desfavorables. Verificar que el candidato permanece en solo lectura antes de la promoción y que se impide revertir ante una operación no resuelta, divergencia de estado o época de autoridad obsoleta.

## Golden Master, TODM y responsabilidad

Golden Master caracteriza lo que **hace** el sistema heredado; también puede revelar comportamientos anómalos, obsoletos o incorrectos. **No constituye automáticamente la verdad de negocio.** El responsable funcional valida el comportamiento deseado y sus excepciones; un oráculo TODM cualificado e independiente comprueba esas decisiones. Sin aprobación de la línea base, independencia del oráculo y autorización humana G6, el resultado es **BLOCK / NOT PRODUCTION APPROVED**.

**Límite de alcance:** esta simulación no demuestra autenticación bancaria, conciliación financiera real, alta disponibilidad, equivalencia de MIPS de IBM Z, p99 con tráfico productivo ni aceptación regulatoria. La capacidad E2 Orleans y la topología F10 tienen sus propios gates experimentales.
