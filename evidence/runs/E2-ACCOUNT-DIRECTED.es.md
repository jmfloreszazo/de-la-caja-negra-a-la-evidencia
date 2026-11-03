# E2 · Llamadas dirigidas sobre activaciones del AccountGrain normal

**Estado actual: 2 positivos dirigidos / 4 INCONCLUSIVE en tres campañas archivadas.**

**Primer ensayo mixto: testigo positivo al bloquear salida secundaria e INCONCLUSIVE al bloquear primaria. E2 sigue parcial.**

[Ejecución original #41634279617](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41634279617),
código/checkout `bfc7662df377632a34d1fb076cdc2de0291e4021`.
El workflow agregado falló porque el objetivo primario devolvió el código 2
predeclarado. Ese caso no se reclasifica retrospectivamente como PASS.

| Observación original | Salida del primario bloqueada | Salida del secundario bloqueada |
| --- | --- | --- |
| Trabajo / artefacto | 125911380313 / 13230102837 | 125911380060 / 13230017227 |
| Bytes ZIP / hashes de código auditados | 47665 / 84 | 53204 / 84 |
| Objetivo dirigido | INCONCLUSIVE_NO_LIVE_OVERLAP | PASS_DIRECTED_REQUEST_OVERLAP |
| Intervalos completos / respuestas de clientes adicionales | 37 / 19 | 51 / 25 |
| Intervalos incompletos / solapamientos observados | 0 / 0 | 0 / 1 |
| Solapamiento del testigo del grain normal | Ninguno | 5,059981 ms |
| Operaciones / asientos / outbox finales; invariantes independientes | 3 / 6 / 3; 7/7 | 3 / 6 / 3; 7/7 |
| Recuperación | Recreación explícita de ambos silos | Recreación explícita de ambos silos |
| Criterios de recuperación tras retirar regla, segundos | 59,802 | 60,059 |
| 14 parejas de replay: intervalo real, segundos | 66,301 | 66,266 |

## Qué acredita el testigo positivo

El `AccountGrain` financiero normal, ledger SQL y colocación predeterminada no
cambian. Un filtro de prueba separado retiene deliberadamente una petición
secundaria **antes** de invocar el método financiero. Bajo el OUTPUT DROP
secundario verificado, otra activación alojada en el primario aceptó una llamada
para `account/2`. Se conservan IDs reales distintos de activación/sesión, ambos
procesos originales muestreados en ejecución y la regla DROP original presente.
Los dos intervalos concretos se solapan y terminan satisfactoriamente. SQL
conserva una operación disputada por importe 31: la petición primaria devolvió
COMMITTED; la antigua, al liberarse, DUPLICATE_COMMITTED. Los intentos con
importe 37 se reconciliaron contra el mismo ganador persistente, sin asientos
ni outbox adicionales aceptados. Cada ACK registrado se contrasta con SQL.

Esto acredita un **testigo dirigido de intervalos de llamadas entrantes**, no
ejecución simultánea de ambas transacciones SQL. La pausa previa cambia los
tiempos y no demuestra comportamiento natural sin instrumentación ni ciclos
de vida globalmente Active simultáneos. Cada trabajo usa un host físico.

## Límites e historia negativa conservada

El caso primario no produjo el testigo exigido y sigue INCONCLUSIVE. Sus
comprobaciones financieras y de recuperación no convierten ese objetivo en PASS.
Ambos casos observaron después el silo bloqueado terminado con **código 139**;
su causa no está comprobada aquí. El primer colector guardó stdout completo
pero **no stderr** de los silos. Los ZIP permanecen intactos y el hueco queda
explícito: no se afirma diagnóstico completo de procesos ni aceptación global
de particiones. Una corrección captura ambos flujos antes de cada eliminación;
su repetición necesita evidencia original y auditoría separadas. No se rebajan criterios.

## Repetición conservando ambos flujos de logs

La [ejecución #41635681137](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41635681137),
código/checkout `c1d174d263b453c9e1a55420f90ad42f091ef88a`, guarda stdout
**y stderr** antes de eliminar cada silo antiguo o nuevo. Ambos sentidos
devolvieron INCONCLUSIVE_NO_LIVE_OVERLAP: 37 intervalos completos por caso,
cero incompletos y cero solapamientos; 21/19 respuestas de clientes adicionales.
SQL y recuperación conservaron 3/6/3, 7/7 invariantes independientes y 14 parejas
de replay. El testigo anterior de 5,06 ms **no se reprodujo en esta repetición**.

En ambos trabajos, stderr primario registra que MembershipTableManager detecta
al silo local como Dead según membresía y entra en KillMyselfLocally /
FatalErrorHandler. SQL registra esa generación primaria como Dead (6) y el
contenedor después aparece con código 139. La traza identifica esa ruta fatal
de membresía en las repeticiones. No determina por qué se seleccionó esa víctima
en todos los sentidos ni explica retrospectivamente el stderr perdido del
primer ensayo. La recuperación recreó expresamente ambos silos.

| Artefacto de repetición | Bytes | SHA-256 ZIP |
| --- | --- | --- |
| Primario 13231480372 | 51039 | 5a40e80ef394005b3e6dbffb9299472fd5204a64750488ed7ae79d961b28b375 |
| Secundario 13230786131 | 50537 | a25d19553937f309801eeb094b048c48203a6ac40a823822510a44ea9b6231f1 |

Se conservan intactos [ZIP primario](e2-account-directed-primary-stderr-original.zip) /
[resumen](e2-account-directed-primary-stderr-original.json) y
[ZIP secundario](e2-account-directed-secondary-stderr-original.zip) /
[resumen](e2-account-directed-secondary-stderr-original.json). El auditor comprueba
ambos flujos, 84 hashes por repetición, reconciliación financiera y evidencia
de la ruta fatal. Los cuatro originales suman **un positivo dirigido y tres
INCONCLUSIVE**. El workflow experimental sigue rojo donde se exigió salida 2;
el PASS de auditoría de archivos es independiente. La aceptación de particiones
y ciclos de vida sigue abierta. Capacidad #25 puede avanzar de forma independiente.

## Tercera campaña: reaparece el testigo con stderr conservado

La [ejecución #41649646557](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41649646557),
código/checkout `9590bc3f663ea965394f84ddad4a1748677dee54`, observó otro
testigo con salida secundaria bloqueada: **4,683800 ms**, conservando ambos
flujos. La llamada antigua devolvió DUPLICATE_COMMITTED y la nueva COMMITTED.
El sentido primario siguió INCONCLUSIVE. Ambos casos conservaron aceptación
financiera y recuperación completas, SQL 3/6/3, 7/7 invariantes y cero llamadas
incompletas. stderr vuelve a registrar la ruta fatal de membresía local: el
primario en el caso primario y el secundario en el caso secundario, con salida
139 después de quedar su generación como Dead.

| Original de tercera campaña | Bytes | SHA-256 ZIP |
| --- | --- | --- |
| Artefacto primario 13236768340 | 51487 | 9bef85e4ef088a8d6925ce2a0a6b90efdb3341b72dc7ef974407ad175f580a62 |
| Artefacto secundario 13237051743 | 55383 | ff4ef9352bd77527012bf7ce217b974b6ae440fe67e5962b50c75dcbe26fb332 |

Se conservan intactos [ZIP primario](e2-account-directed-primary-repeat3-original.zip) /
[resumen](e2-account-directed-primary-repeat3-original.json) y
[ZIP secundario](e2-account-directed-secondary-repeat3-original.zip) /
[resumen](e2-account-directed-secondary-repeat3-original.json). El auditor verifica
los seis originales y los 84 hashes por trabajo. El testigo reapareció en dos
de los tres casos secundarios: reproducción parcial, no éxito consistente en
ambos sentidos ni prueba natural de ciclos de vida Active simultáneos. Los
tres casos primarios siguen inconclusos. El primer positivo sin stderr se
distingue del posterior que sí lo conserva. No se descartan ni reclasifican resultados.

## Ejecución de campañas y CI de código

Las nuevas campañas se lanzan explícitamente mediante workflow_dispatch, con
los mismos criterios y salida 2 para INCONCLUSIVE. Las PR compilan el host,
ejecutan controles adversariales y auditan los originales automáticamente.
Así, editar el libro no lanza otra campaña. Una matriz viva omitida no es un
experimento satisfactorio; se conservan las conclusiones rojas históricas.

## Bytes originales y reproducción

- [ZIP primario](e2-account-directed-primary-original.zip) / [resumen idéntico en bytes](e2-account-directed-primary-original.json): SHA-256 `d1543a98505cef134efab17dedc263678ba1fc2cb09c1343787f1f85233ea5ac`.
- [ZIP secundario](e2-account-directed-secondary-original.zip) / [resumen idéntico en bytes](e2-account-directed-secondary-original.json): SHA-256 `e018ad1f5d738ba3c1f21e119dd08b63dd60dc47f5dc29c95899b9423f61e5e5`.

El [auditor offline](../../scripts/check_e2_account_directed.py) comprueba hashes
de ambos ZIP, identidad del resumen, los 84 hashes originales de código,
stdout e intervalos, IDs de testigo/procesos, bytes PCAP, reconciliación SQL/ACK
y recuperación muestreada. Su PASS valida las observaciones archivadas; no
aprueba ambos objetivos ni recupera stderr inexistente. Siguen separados la
semántica natural de ciclos de vida, capacidad #25, recuperación autónoma y HA física.

[English](E2-ACCOUNT-DIRECTED.md) · [Protocolo predeclarado](../../lab/e2_account_directed/README.md)
