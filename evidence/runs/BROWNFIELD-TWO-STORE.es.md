# BROWNFIELD-COEXISTENCE-C01 — evidencia original de dos almacenes

**Clasificación:** SYNTHETIC_TWO_POSTGRESQL_CONTAINERS_SINGLE_RUNNER.
**Decisión:** verificación técnica limitada; **no** prueba convivencia real
con IBM Z/COBOL, aceptación de negocio, cutover productivo, HA ni rollback
aprobado.

## Identidad de la CI original

- [Ejecución original #41339443735](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41339443735): **PASS**, 1 de noviembre de 2026.
- SHA exacto del código probado:
  `d0abda29878d66d5276247ac4e32ac879e110b6d`.
- El fichero original `provenance.txt` confirma que `source_head_sha` y
  `checkout_sha` coinciden; el workflow falla si difieren.
- Artefacto original ID `13096162996`,
  `brownfield-two-store-synthetic-not-mainframe-g6`.
  SHA-256 del ZIP original:
  `32b860aa24ea057b1faf25f3181fc9981dd8e2fcc3facc3d637cc8d2e76945cc`.
- [JSON original versionado](brownfield-two-store-pr63-original-summary.json),
  transcrito literalmente del log. Su contenido dentro del ZIP tiene SHA-256
  `d26ae90fd73e6647400cd4e3812a8e7ca1bb37521bb0a88f7ad4dc28fbbfeabb`.
  El ZIP también contiene `build.log` y `provenance.txt` con versiones,
  contenedores Podman y procedencia del código.

## Resultados observados

| Observación independiente | Resultado |
| --- | --- |
| Libro contable de origen (adaptador legado) | 8 decisiones |
| Libro contable de destino (.NET 10) | 10 decisiones |
| Oráculo contable de origen | 10/10 verdaderos |
| Oráculo contable de destino | 10/10 verdaderos |
| Cambio del legado / outbox ausente | Cutover rechazado |
| Shadow solo lectura | Sin dobles apuntes; diferencia visible |
| Operación con época antigua | Bloqueada por el controlador cooperante |
| Antes de escribir en destino | Rollback sintético posible tras conciliación |
| Tras dos decisiones nuevas del candidato | Rollback bloqueado: `FORWARD_FIX_REQUIRED` |
| Escritura SQL directa sin pasar por el controlador | Detectada por el oráculo; **no** impedida |
| TODM G2 / G6 | INCONCLUSIVE / BLOCK |

## Conservar la anomalía inicial de procedencia

La primera [ejecución #41339301269](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41339301269)
también superó las pruebas, pero GitHub hizo checkout de un *commit de
integración temporal* (`checkout_sha=78d1140f14540561a18a84f69aa3ffa079e79c25`),
mientras el SHA de la rama era
`6f1edc4183808a43e70b7bc0343ebae2cd378607`.
No debe citarse como ejecución del SHA exacto de la rama.
Se corrigió el workflow para comprobar obligatoriamente esa identidad;
la segunda ejecución es la evidencia válida del SHA exacto.

**Pendiente:** fencing real en IBM Z; registro persistente de admisión y
resultados UNKNOWN; recuperación de copias interrumpidas; HA entre nodos;
reglas del cliente y Golden Master aprobados; TODM G2/G6. Continúa abierta
la [issue #58](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/issues/58).
No se modifica la release.

## Ampliación C3: enrutamiento y aislamiento de fixtures — 1 nov 2026

La [ejecución original #41343867961 de la PR #68](https://github.com/jmfloreszazo/de-la-caja-negra-a-la-evidencia/actions/runs/41343867961)
terminó en **PASS** sobre el SHA exacto
`437ab93ca28765ba05cd49d02021b24f850a6e68`.
El checkout coincidió con ese SHA y el informe incluye las huellas de los
ficheros, entre ellos el nuevo gateway. El
[JSON original sin modificar](brownfield-gateway-pr68-original-summary.json)
conserva 12 controles positivos/negativos, **8 decisiones en origen** y
**10 en destino** después de operaciones nuevas del candidato, 10/10
invariantes contables independientes en cada almacén, dos identificadores
distintos de clúster PostgreSQL y `G6=BLOCK`.
El artefacto original de Actions tiene ID `13097984744` y SHA-256 del ZIP
`4f967de09ea97b1e3e66b58bc03b0f049af7dbf7466b9c5ba8103a9c2ca8e6cb`.

Se ha probado el gateway contra el CLI legado antes de la promoción, contra
.NET 10 después, su rechazo de versiones mínimas de saldo que el legado no
garantiza, el shadow solo lectura y el enrutamiento tras rollback admisible.
Los procesos de laboratorio rechazan bases, hosts o puertos no previstos antes
de abrirlas y antes de cualquier reinicialización destructiva.

**Sin nuevas garantías de producción:** un escritor legado con acceso SQL
directo aún puede evitar el fencing cooperativo. Las evidencias anteriores
de la PR #63 y del journal C2 conservan su propia procedencia; esta prueba
no demuestra cutover real IBM Z, HA física ni aprobación G2/G6.
