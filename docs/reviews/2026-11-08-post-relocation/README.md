# Revisión posterior a la reubicación de evidencias — 8 de noviembre de 2026

> **Estado del informe: completado.** Reubicación verificada y revisiones editorial y de arquitectura recibidas. Las evidencias locales inspeccionadas están preservadas; quedan defectos de verificadores, coherencia editorial y cobertura por resolver. No es una aprobación global del libro ni de E1–E4.

## Alcance y cambios realizados

Petición del autor: sacar de `dist/` las evidencias, preservarlas y ejecutar los agentes revisores para distinguir OK, KO, pendientes y mejoras. La revisión no autoriza corregir sus hallazgos, publicar ni ejecutar nuevas campañas.

- Revisión sobre el commit `5dd04444da43c9d65604fcc2173731cb81bba6fa` y los cambios locales de reubicación.
- **29 archivos, 232.494.270 bytes**, copiados y comparados por tamaño y SHA-256 antes de retirar sus originales.
- Destino: `evidence/archives/preserved-dist/`. Se conservaron doce ZIP de primer nivel y la carpeta histórica de reproducción, incluido su ZIP duplicado y sus PDF históricos. No se recomprimió ni deduplicó nada.
- `dist/` conserva únicamente los dos PDF actuales y sus metadatos de maquetación.
- `lab/results/` no se movió. El log E3 señalado por el autor se conserva: `lab/results/azure-e1-e4-20261108/e3-run-01.log`, SHA-256 `7d4351e8798d99a4114a9c31c66706ad380070c88d3e253d4b316ce1523eb5cb`.
- Los payloads siguen ignorados por Git; su inventario es versionable. Esto **no equivale a tener una copia de seguridad externa o un canal público de descarga**.

Referencias: [inventario de reubicación](../../../evidence/archives/relocation-2026-11-08.json), [guía de conservación](../../../evidence/archives/README.md), [manifiesto de ZIP](../../DIST_MANIFEST.md).

## OK — comprobado

| ID | Comprobación | Evidencia y límite |
|---|---|---|
| OK-01 | Todos los archivos trasladados coinciden con su hash previo | 29 verificaciones independientes después del traslado; lectura de todas las entradas de los 13 ZIP, incluido el duplicado histórico. No prueba autenticidad externa. |
| OK-02 | Los puntos de entrada actuales señalan la nueva carpeta | Guía de archivos, mapa del proyecto, manifiesto y utilidad de inventario actualizados. Los nombres históricos dentro de recibos y paquetes no se alteraron. |
| OK-03 | Estructura y paridad del libro | `scripts/check.py`: PASS; 3.518 enlaces relativos, 61 pares de unidades, manuscritos generados sincronizados y 48 figuras por idioma. Son 61 unidades, no 61 capítulos. |
| OK-04 | Política de idioma | `scripts/check_language_policy.py`: PASS. No certifica calidad completa de traducción. |
| OK-05 | Inventario de ZIP | `scripts/evidence/dist_manifest.py --verify`: PASS sobre los doce ZIP de primer nivel en su nueva ubicación. No certifica todos los aspectos de los recibos. |
| OK-06 | Los banners ya distinguen demostración y aceptación | `README.md:14`, `README.es.md:14`. El revisor descarta la antigua acusación de que niegan toda ejecución E3/E4. |
| OK-07 | Cifras de E3/E4 y TODM consistentes en los pasajes revisados | 720 ofertas = 668 commits + 48 fallos + 4 omisiones; 16 pruebas propias, 58 casos, 3 mutantes; TODM 134 archivos/108 vínculos/8 controles/12 casos sintéticos. Verificación técnica, metodología y autorización permanecen separadas. |
| OK-08 | Documentos históricos conservados | El cierre del 5 de noviembre y el roadmap tienen notas posteriores fechadas. No se deben cambiar retrospectivamente sus conteos o resultados. |

## KO — hallazgos editoriales verificados

Prioridad alta significa corregir antes de presentar el texto como coherente; no equivale a invalidar la campaña.

| ID | Prioridad / confianza | Localización | Hallazgo y corrección propuesta, no aplicada |
|---|---|---|---|
| ED-01 | Alta / alta | [25 bis ES](../../../book/es/parte-5-capacidad/25a-infraestructura-mainframe-local-azure-y-redes-bancarias.md):107; [EN](../../../book/en/part-5-capacity/25a-mainframe-on-prem-azure-and-banking-network-infrastructure.md):109 | Un párrafo en presente dice que Bicep solo se ha comprobado localmente y no se ha desplegado/medido en Azure. Contradice el despliegue `Succeeded` y las secciones posteriores. Identificar el estado previo y enlazar el resultado posterior sin afirmar aceptación de capacidad. |
| ED-02 | Media / alta | [EXPERIMENT_ROADMAP](../../EXPERIMENT_ROADMAP.md):24–25,40–41 | Persisten pendientes de validación Azure y autenticación caducada antes de narrar la ejecución posterior. Fechar ese bloqueo y separarlo de los requisitos aún abiertos. |
| ED-03 | Media / alta | Capítulos 7 y 8 ES/EN, navegación inicial; [índice EN](../../../book/en/README.md):24–26 | El índice coloca 7 bis entre 7 y 8, pero los enlaces siguiente/anterior saltan el complemento. Decidir recorrido y alinear ambos idiomas. |
| ED-04 | Baja / alta | [Parte V ES](../../../book/es/parte-5-capacidad/README.md):3,19; [EN](../../../book/en/part-5-capacity/README.md):3,19 | El enlace anterior vuelve a 21 en vez de 21 bis. Alinear con el índice o declarar que es un atajo. |
| ED-05 | Baja / alta | [AUTHOR_VOICE](../../AUTHOR_VOICE.md):21–24; [política de idioma](../../LANGUAGE_POLICY.md):12,29 | El perfil generaliza README inglés y bloques idénticos, sin las excepciones para README raíz bilingüe y diagramas narrativos `text`. Evitar que el revisor produzca falsos positivos por estas excepciones. |
| ED-06 | Media / alta | [índice de evidencias EN](../../../evidence/runs/README.md):3–21 y [ES](../../../evidence/runs/README.es.md):3–21 | Tras anteponer Azure/TODM, el párrafo histórico afirma que los JSON acompañantes se extrajeron de Actions. Delimitarlo a E1a/E1b: las campañas nuevas declaran Actions `NOT_EXECUTED`. |

## KO — verificadores y cobertura técnica

Hallazgos de **Architecture and AI reviewer**. Confianza alta por inspección estática; los escenarios de fallo siguientes **no se ejecutaron** durante esta revisión. No describen corrupción actual de los paquetes.

| ID | Prioridad | Localización | Hallazgo y criterio de corrección propuesto |
|---|---|---|---|
| AR-01 | Alta | [Verificador Azure](../../../scripts/evidence/verify_azure_e1_e4.py):130 y [resumidor TODM](../../../scripts/evidence/summarize_todm_azure.py) | Usan `assert` para integridad, condiciones y comparación final. `python -O` o `PYTHONOPTIMIZE` elimina esas comprobaciones. Sustituir controles de aceptación por errores explícitos y probar también el intérprete optimizado. No se ejecutó el bypass. |
| AR-02 | Media | [Inventario de archivos](../../../scripts/evidence/dist_manifest.py):74 | `--verify` compara el Markdown con su regeneración, pero no exige que todos los recibos tengan estado `matches`. Un manifiesto regenerado que contiene `MISMATCH` o recibos ausentes puede terminar en PASS. Separar consistencia del inventario y verificación de recibos; rechazar discordancia y declarar ausencia. Los bytes actuales movidos sí coinciden con el inventario de reubicación. |
| AR-03 | Alta | [Validador de claims](../../../scripts/check_evidence.py):46 | Un objeto de evidencia no vacío con `kind` desconocido puede no caer en ninguna rama de rechazo para `ci_verified`/`published`; la ruta online tampoco lo verifica. Exigir tipos cerrados y campos obligatorios por estado. No se encontró que los registros actuales usen ese hueco. |
| AR-04 | Media | [README de verificadores](../../../scripts/evidence/README.md):19 | La garantía «un archivo ausente es un error» contradice la generación inicial del registro si no existe. Separar los modos de verificar sin escritura y generar, ambos explícitos. |
| AR-05 | Baja | [Resumidor TODM](../../../scripts/evidence/summarize_todm_azure.py):6 | Declara identidad byte a byte pero compara objetos JSON deserializados. La igualdad semántica permite diferencias de formato. El hash de claims es otro control; no convertir una comparación semántica en binaria por descripción. |
| AR-06 | Media | [Resumidor TODM](../../../scripts/evidence/summarize_todm_azure.py):43 | Los recuentos 134 y 108 son constantes, no recalculados por este helper. Explicar que resume resultados retenidos y no sustituye la validación completa del bundle, o derivar dichos recuentos de entradas verificadas. |
| AR-07 | Media, condicionado | [Verificador Azure](../../../scripts/evidence/verify_azure_e1_e4.py):105 | Depende de archivos `lab/` del checkout actual. Hoy coinciden seis hashes protegidos; un cambio legítimo futuro podría impedir verificar una campaña intacta. Usar la fuente archivada o exigir claramente el checkout correspondiente. |
| AR-08 | Media | [Pruebas del destino de membresía](../../../lab/e2_orleans/test_membership_target.py):1 | No se encontró invocación directa ni indirecta en los workflows/colectores inspeccionados. Añadir cobertura explícita de estos controles offline del destino desechable. |
| AR-09 | Media | [Índice de evidencias](../../../evidence/runs/README.md):3 | Cuatro registros locales posteriores a la release siguen sin indexación/relación explícita: `local-reproduction-2026-11-07.json`, `local-public-campaign-2026-11-07.json`, `local-e2-cluster-2026-11-07.json` y `local-e4-qualification-2026-11-07.json`. Existen sus bytes y límites; falta descubribilidad, no ejecución. |

ED-06 también fue detectado por arquitectura; se conserva una sola fila para no duplicar el hallazgo sobre procedencia GitHub Actions.

### Confirmaciones independientes adicionales

- **29/29 archivos**: tamaño y SHA-256 coinciden; ninguna ruta fuente inventariada permanece en `dist/`. La comprobación independiente confirma el estado actual, no observa retrospectivamente el orden del traslado.
- Los **cinco hashes de fuentes y cinco de archivos raw** Azure coinciden; todos los miembros de los TAR de fuentes y los **250 archivos regulares** de los cinco TAR de resultados coinciden con las copias locales.
- El log E3 señalado existe y su copia dentro del ZIP es idéntica. Se conserva también el primer replay E4 fallido.
- Coinciden los cuatro vínculos TODM comprobados: archivo de entrada, archivo raw, validación y cualificación. **No se ejecutó otra vez TODM.**
- E4 inspecciona controles reales del contenedor: usuario no root, red `none`, raíz de solo lectura, capacidades y privilegios limitados, recursos acotados. No depende solo de un prompt.
- Las rutas públicas inspeccionadas del kit de modelos mantienen `productionApproved: false`; el resultado de negocio `APPROVE` no es autorización de producción.
- El Bicep inspeccionado limita los roles del runner a los contenedores de fuentes y evidencia. Es comprobación estática, no consulta del estado Azure actual.

### Afirmaciones de revisiones anteriores que no deben repetirse

| Afirmación anterior | Corrección tras comprobar el estado actual |
|---|---|
| «No hay CI para ninguna suite nueva» | Existen selectores para modelos, TODM, E4, herramientas y pruebas Azure, además de pasos PowerShell. Es cobertura configurada; su ejecución remota no se verificó. |
| «La ausencia de e4-replay en el colector es necesariamente un bug» | `LAUNCHER_ONLY` documenta requisitos de entradas externas y supervisor. El launcher y el operador aceptan los mismos nueve modos; distinguir el diseño deliberado de deriva accidental. |
| «No hay procedencia si falta sourceCommit en la raíz» | Algunos resúmenes la registran por ejecución. Hay que examinar la estructura completa. |
| «Los archivos ignorados ya no existen» | Se conservaron localmente y se verificaron. Que un clon no los incluya es una limitación de entrega, no pérdida. |
| «Los verificadores solo están en carpetas ignoradas» | Los tres helpers actuales están versionados, aunque necesitan las correcciones AR-01–AR-07. |

## Pendientes que no se resuelven con redacción

- Confirmar una copia de seguridad independiente y un mecanismo de entrega de los paquetes a terceros. Un clon limpio recibe inventarios, no archivos ignorados.
- Integrar los cambios locales cuando el autor lo autorice. No se ha hecho commit ni push en esta tarea.
- E3: contrato de carga aprobado, comparación pertinente, dominios físicos, WAN/TLS y mediciones de capacidad. La carga exploratoria no los sustituye.
- E4: población comparativa de tareas, revisión humana y coste medido. Reproducir una respuesta no es otra inferencia ni otra tarea independiente.
- TODM: autoridad independiente G2/G6. Un hash o un PASS técnico no la acredita.
- CI: configuración de workflows y ejecución remota son hechos distintos. No se han lanzado Actions en esta tarea. El workflow nuevo ejecuta las pruebas unitarias de E3, no su campaña PostgreSQL/.NET de integración; esa campaña sí dispone de evidencia Azure histórica.
- Faltan pruebas negativas específicas de los verificadores: recibo ausente, hash divergente, registro inexistente, optimización Python, checkout diferente y `kind` desconocido. Compilar scripts no verifica estas garantías.
- Los helpers con `hashlib.file_digest` requieren Python 3.11 o posterior: declarar ese mínimo en su documentación.
- La guía y el recibo de reubicación están creados y son versionables, pero seguían sin seguimiento en Git durante ambas revisiones. No se ha modificado el índice ni hecho commit; no describirlos aún como «ya versionados».

## Sensibilidad y custodia

Se observaron identificadores reales de suscripción, recursos, VM y principales en archivos versionados. Son metadatos operativos, no credenciales por sí solos; no se reproducen sus valores aquí. Una búsqueda textual limitada de claves privadas, AccountKey, SAS y tokens encontró un patrón detector, **no una credencial confirmada**. No acredita ausencia total de secretos ni revisión exhaustiva de todos los ZIP. La publicación o entrega externa debe revisar los contenidos y tener autorización; no se propone publicar indiscriminadamente los payloads.

## Mejoras y ejemplos que se pueden añadir — propuestas, no ejecutadas

| Propuesta | Valor para el lector | Evidencia necesaria antes de decir que funciona |
|---|---|---|
| Ficha «ejecutado / observado / aceptado» | Seguir E3 desde el rechazo de preparación hasta la prueba exploratoria sin confundir ambos | Referencias a los registros conservados y criterios de aceptación externos |
| El denominador que cambia la conclusión | Explicar las 720 ofertas y por qué p99 de ACK no describe fallos/omisiones | Recalcular desde ofertas y ledger; no fabricar nuevas mediciones |
| DMN con entradas incompletas | Contrastar positivo, negativo e inconcluso y mantener aprobación separada | Ejecutar el subconjunto soportado y conservar salidas/control negativo |
| Redondeo entre dos runtimes para anexo H | Demostrar un límite concreto de portabilidad | Expectativas independientes, versiones exactas y un mutante conocido |
| Lectura de un paquete preservado | Relacionar ruta antigua, nueva, recibo, hash y limitaciones | Copia recibida por otra persona y verificación registrada |

Mejoras editoriales opcionales: mapa inicial del capítulo 25 bis; cierre más claro de 10 bis; presentación de tesis en H si mejora su lectura. No se impone una figura ni una plantilla rígida a todas las unidades.

## Plan priorizado — propuesto, no ejecutado

| Orden | Trabajo | Criterio para darlo por cerrado |
|---|---|---|
| 1 | Corregir los controles de verificadores AR-01–AR-03 | Entradas inválidas producen salida no cero, incluso con Python optimizado; recibo regenerado discordante no pasa; tipo de procedencia desconocido se rechaza. Añadir pruebas antes de afirmarlo. |
| 2 | Separar generación, resumen e integridad AR-04–AR-07 | Verificación sin escritura, comparación binaria o semántica correctamente declarada, recuentos derivados o alcance explícito, campaña verificable con su fuente archivada. |
| 3 | Corregir ED-01, ED-02 y ED-06 | Párrafos con estado previo fechado, procedencia CI delimitada a sus campañas y concordancia con resultados posteriores, sin reescribir los originales. |
| 4 | Cerrar navegación y reglas editoriales ED-03–ED-05 | Recorrido 7 → 7 bis → 8 y 21 bis → Parte V explícito en ambos idiomas; perfil de voz compatible con las excepciones de la política. |
| 5 | Completar cobertura e índice AR-08–AR-09 | Pruebas de membresía incluidas, negativas de verificadores ejecutadas localmente y cuatro registros locales descubribles. Documentar CI configurada frente a ejecutada. |
| 6 | Integración y custodia | Autor decide versionado de guía/recibo/README, conserva payloads ignorados y establece copia independiente y entrega autorizada. Sin push automático. |
| 7 | Elegir ejemplos y mejoras opcionales | Priorizar una ficha de evidencia y un ejemplo de fallo de verificador; etiquetar propuestas hasta ejecutar y conservar resultados. No añadir herramientas por volumen. |

Ejemplos técnicos adicionales: recibo discordante que sigue fallando tras regenerar el manifiesto; `APPROVE` de negocio con `productionApproved: false`; clon sin payload que declara archivos pendientes en vez de «evidencia destruida»; replay E4 con cero nuevas inferencias. Son propuestas de explicación/validación, no experimentos nuevos realizados aquí.

## Método y límites de la revisión

Revisores invocados: **Editorial reviewer** (`c1aadc6a-176d-4fda-aac3-affe8d9a090a`) y **Architecture and AI reviewer** (`f7d88d96-9b08-4d1e-969c-3457431bbb1d`), en contextos separados y con instrucciones de solo lectura. Los hallazgos repetidos se consolidaron, y se separan defectos actuales, riesgos condicionados, gates externos y preferencias editoriales.

El revisor editorial no comprobó los bytes de los archivos ni los PDF actuales; la preservación fue comprobada por el coordinador y, de forma independiente, por arquitectura. El revisor técnico no ejecutó pruebas ni builds: los KO técnicos son conclusiones estáticas con condiciones de reproducción indicadas, no fallos experimentales recién ejecutados.

No se repitieron experimentos, no se consultó el estado actual de Azure y no se auditó exhaustivamente cada afirmación del proyecto. Los resultados de controles previos no se presentan como nuevas ejecuciones. No se aplicaron los arreglos de este plan: únicamente la reubicación solicitada, sus referencias operativas y este informe.

**Conclusión:** la evidencia inspeccionada está preservada; no procede llamarla perdida ni afirmar que el libro está perfecto. El siguiente trabajo es fortalecer la verificación y corregir las contradicciones concretas antes de ampliar ejemplos o dar por cerrada la aceptación.
