**Español** · [English](../../en/annexes/annex-h-beyond-cobol.md)

[← Anexo G · Fuentes y alcance de la investigación](anexo-g-fuentes-y-alcance-de-la-investigacion.md) · [Índice](../README.md)

# Anexo H · Más allá de COBOL

## Qué se transfiere con el método

COBOL aporta problemas concretos a este libro, no un ámbito exclusivo. Un servicio Java, una aplicación VB6 o un proceso por lotes RPG también pueden ocultar reglas, depender de interfaces indocumentadas y discrepar de su sustituto. La pregunta transferible no es «¿puede traducirse este lenguaje?», sino «¿qué comportamiento observable debe sobrevivir, quién lo acepta y qué evidencia podría contradecir al candidato?».

La [metodología de oráculos del capítulo 10](../parte-3-oraculos/10-todm-y-el-problema-de-aceptar-lo-que-construimos.md) no exige un lenguaje determinado: recuperar evidencia, establecer una baseline aprobada independientemente, cualificar al evaluador, vincular observaciones al candidato y separar aceptación técnica de autorización de entrega. El golden master registra lo ocurrido; no decide automáticamente qué debería ocurrir. Una corrección aprobada debe quedar visible como diferencia intencional.

La implementación del método no se transfiere automáticamente. Un parser COBOL no se convierte en parser PL/I; comparar JSON no captura una interfaz gráfica, un dispositivo mapeado en memoria ni un commit distribuido. Cada frontera nueva necesita un adaptador de observación, expectativas fiables y controles negativos. El método puede ser portable mientras cada adaptador sigue siendo específico.

## Matriz de aplicabilidad: contratos antes que sintaxis

Las filas siguientes son **orientaciones de evaluación**, no un catálogo de migraciones ejecutadas ni de adaptadores certificados. Agrupar lenguajes ahorra espacio; no equipara sus semánticas.

| Lenguaje o entorno | Qué puede reutilizarse | Qué debe especificarse y verificarse de nuevo |
|---|---|---|
| Java / C# | Contratos de capacidad, ejemplos independientes, invariantes de estado y contabilidad, escenarios de fallo | Representación decimal y redondeo; desbordamiento entero; excepciones y nulabilidad; versiones JVM/CLR, bibliotecas, JIT y recolección de memoria; propagación transaccional |
| VB6 / VB.NET | Resultados visibles aprobados, trazas de eventos, comparación con referencia | Distinguir ambos entornos; `Variant`, `Empty` y `Null`, conversiones implícitas, configuración regional y fechas; vida de objetos COM, orden de eventos gráficos y proveedor de datos |
| RPG / IBM i | Capacidades de negocio, conciliación por lotes, criterios de escritor único y transición | Campos decimales, CCSID, indicadores, acceso a registros, estado del trabajo, control de compromiso y fronteras del diario; dialecto y plataforma instalados |
| PL/I | Reglas, casos límite, resultados esperados independientes, invariantes transaccionales | Precisión fija/binaria, manejo de condiciones, disposición de almacenamiento, opciones de compilación y enlace; servicios del host e integración con datos |
| C / C++ | Contratos de protocolo, máquinas de estados, pruebas diferenciales y de propiedades | Anchura, signo, propiedad de memoria, ABI, alineación, orden de bytes, concurrencia y comportamiento indefinido; compilador, optimización y dependencias nativas |
| Python / JavaScript | Separación del oráculo, casos explícitos, comprobación de esquemas y controles negativos | Conversiones dinámicas y valores ausentes; contexto decimal y extensiones nativas de Python; `Number`/`BigInt` de JavaScript; serialización, planificación asíncrona y versiones de dependencias |
| Sistemas embebidos / tiempo real | Trazabilidad de requisitos, invariantes de estado, escenarios de fallo y aceptación independiente | Hardware, interrupciones, plazos, recursos, reinicio y pérdida de alimentación; evidencia con hardware real en el circuito y garantías de seguridad exigibles |

Cada fila sirve tanto para actualizar dentro del mismo lenguaje como para reescribir. Cambiar compilador, controlador de datos o runtime puede alterar el comportamiento sin modificar el código fuente. Hay que registrar el entorno completo, no solo el lenguaje.

## Fronteras semánticas que necesitan su propio oráculo

**Números.** Especificar precisión, escala, modo y momento del redondeo. La aritmética decimal no es intercambiable con la coma flotante binaria. Definir rangos intermedios y finales: el desbordamiento modular de enteros Java, la aritmética comprobada o no de C#, los enteros Python y las representaciones JavaScript no ofrecen el mismo contrato. Probar negativos, puntos medios, magnitudes máximas y serialización. Una visualización coincidente puede ocultar importes almacenados diferentes.

**Texto y ausencia.** Codificación, normalización, ordenación, relleno y longitud en bytes son decisiones distintas. El [ejercicio EBCDIC](../../../lab/examples/ebcdic-boundaries/README.md) muestra que una ida y vuelta correcta puede conservar el significado equivocado; no valida todas las páginas de códigos del host. Hay que distinguir campos ausentes, null, cadenas vacías, cero y valores centinela cuando el dominio lo haga. Recortar o rellenar datos silenciosamente puede fabricar concordancia.

**Fechas y tiempo.** Definir calendario, precisión, zona, desplazamiento horario, cambios estacionales, fecha de negocio y política de corte. Una fecha-hora local no identifica necesariamente un instante. Controlar el reloj cuando proceda e incluir horas locales ambiguas e inexistentes. Las referencias no deben depender accidentalmente de la configuración regional del evaluador ni de la fecha actual.

**Concurrencia y transacciones.** Especificar historiales observables, idempotencia, orden y punto de durabilidad. Un mutex, bucle de eventos, actor o anotación transaccional no establece por sí solo la frontera del commit de negocio. Probar duplicados, cancelaciones, respuestas perdidas y caídas antes y después del commit; inspeccionar independientemente el estado persistido. Transferir el razonamiento de la [arquitectura verificable](../parte-3-oraculos/11-la-arquitectura-de-una-modernizacion-verificable.md), no suponer que una API de hilos conocida lo conserva.

**FFI y comportamiento indefinido.** En interfaces con funciones externas, verificar convención de llamada, disposición de campos, propiedad, propagación de errores y vida de objetos. El comportamiento indefinido de C/C++ no tiene un resultado estable que preservar según el lenguaje. Una observación repetible puede orientar un requisito de compatibilidad acotado, pero no convierte ese comportamiento en especificación portable. Aplicar diagnósticos adecuados y rediseñar la frontera; una ejecución diferencial satisfactoria no constituye una prueba general.

## Los modelos de decisión expresan reglas, no traducciones

BPMN puede describir orden de proceso, eventos y responsabilidades; DMN expresa decisiones y tablas de reglas. Ninguno traduce código arbitrario en significado de negocio aprobado. Un diagrama extraído de un programa sigue siendo hipótesis hasta establecer su interpretación y autoridad.

Un oráculo ejecutable exige documentar el subconjunto semántico soportado: tipos, ausencia, comparaciones, prioridad o política de coincidencia, valores predeterminados, errores y transiciones pertinentes. Vincular versiones del modelo y evaluador con la evidencia. Un constructo no soportado debe bloquear o quedar inconcluso, no ignorarse. El [laboratorio de modelos de decisión](../../../lab/decision_models/README.md) documenta su alcance y reproducción; un verificador limitado no es un motor BPMN/DMN completo ni certificado. La notación no establece conformidad ni aprobación.

## Los ADR conservan la baseline y su justificación

Las [decisiones de arquitectura del anexo D](anexo-d-decisiones-de-arquitectura.md) siguen siendo útiles fuera de COBOL. Para cada frontera nueva, registrar comportamiento existente, autoridad de negocio, contrato elegido, alternativas descartadas y justificación. Incluir incertidumbres, excepciones de compatibilidad, responsable, condición de revisión y criterios de salida. Un ADR explica por qué se eligió la baseline; no sustituye casos ejecutables ni otorga aprobación por estar versionado.

Un paquete práctico de aceptación debe contener:

1. Capacidad y contrato de interfaz acotados, incluidos fallos; utilizar el [contrato del laboratorio](anexo-b-contrato-del-laboratorio.md) y la [comparación de significado](../parte-3-oraculos/12-cobol-y-c-deben-acordar-el-significado.md) como ejemplos, no esquemas universales.
2. Resultados esperados gobernados separadamente, observaciones autorizadas de referencia y diferencias intencionales explícitas.
3. Adaptadores y evaluadores cualificados, con controles correctos, candidatos defectuosos y evidencia incompleta.
4. Identidades de candidato, modelo, dependencias y runtime, observaciones brutas y procedencia original.
5. Veredicto acotado, limitaciones pendientes, autoridad de entrega independiente y control de cambios de baseline.

## Qué demuestran realmente las herramientas disponibles

El [adaptador práctico TODM](../../../lab/todm_validation/README.md) valida formatos concretos de evidencia y semántica de gobernanza fijada por versión. No es un ejecutor universal para estos lenguajes ni un servicio de autorización de producción. El [laboratorio de descomposición](../../../lab/decomposition/README.md) comprueba hipótesis sintéticas de fronteras; no descubre dependencias arbitrarias del código. El [ejercicio de comisión a tres bandas](../../../lab/examples/commission-three-way/README.md) demuestra una combinación concreta de referencia, candidato y expectativa, no certificación entre lenguajes.

Este anexo no añade ejecuciones. Los artefactos COBOL, C#/.NET y Python conservan sus alcances documentados; citar otros lenguajes o plataformas no equivale a medirlos. Las pruebas locales mínimas no se convierten en mediciones Azure, ni los experimentos Azure establecen equivalencia mainframe. Cada lenguaje, runtime o carga nueva necesita evidencia propia conservada. La aportación portable es exigirla explícitamente, no prometer que esa prueba ya existe.

---

[← Anexo G · Fuentes y alcance de la investigación](anexo-g-fuentes-y-alcance-de-la-investigacion.md) · [Índice](../README.md)
