**Español** · [English](../../en/part-3-oracles/10-todm-and-the-problem-of-accepting-what-we-build.md)

[← Parte III · Oráculos: el derecho a aceptar](README.md) · [Índice](../README.md) · [Capítulo 11 · La arquitectura de una modernización verificable →](11-la-arquitectura-de-una-modernizacion-verificable.md)

# Capítulo 10 · TODM y el problema de aceptar lo que construimos

> [!IMPORTANT]
> **Tesis del capítulo.** TODM separa quién está autorizado a actuar de si el software resultante satisface un comportamiento aprobado de forma independiente. Los agentes pueden proponer y construir; no pueden aprobar ni cambiar el oráculo que los juzga.

## Una metodología centrada en el resultado esperado

TODM significa Test Oracle-Driven Methodology. Su propuesta consiste en gobernar la aceptación mediante oráculos independientes, una baseline aprobada y evidencias vinculadas al candidato [2]. La IA puede ayudar a descubrir reglas, proponer contratos y construir código. La aceptación necesita una autoridad y un mecanismo que no dependan unilateralmente de ese constructor.

El README del repositorio lo plantea con una pregunta que me sigue pareciendo la correcta: los agentes ya escriben código, pero ¿quién verifica que ese código es correcto? Su respuesta es separar el permiso para actuar de la prueba de corrección, con oráculos ejecutables, baselines gobernadas por personas y gates que bloquean por defecto. Y su objetivo no es confiar más en un agente, sino necesitar menos confianza ciega en lo que produce [2].

Un oráculo responde a una pregunta sobre el resultado. Puede ser un conjunto de ejemplos aprobados, una propiedad matemática, una tabla de decisiones, una máquina de estados o una comparación con el sistema de referencia. La elección depende de qué queremos comprobar y qué evidencia tenemos.

No considero el oráculo una verdad infalible. También hay que probarlo. Puede omitir un caso, aplicar mal un operador o confiar en una observación que el candidato ha fabricado. Por eso la cualificación del evaluador forma parte del trabajo.

El repositorio público revisado presenta una demo sintética Python/.NET 10, cinco perfiles semánticos limitados y escenarios de gobierno. No implementa motores completos de los estándares OMG que inspiran esos perfiles. Su publicación tampoco demuestra superioridad comparativa o eficacia industrial [2]. Esa delimitación debe acompañar cualquier libro que lo utilice.

Construiría el oráculo antes de escribir la implementación. En un sistema real hay al menos cuatro fuentes complementarias: **golden masters** obtenidos del legado, **contratos aprobados de negocio**, **invariantes matemáticos o contables** y **propiedades operacionales** bajo fallos y concurrencia. Ninguna es suficiente por sí sola. El legado puede tener defectos; el negocio puede olvidar reglas históricas; las invariantes pueden omitir excepciones; los tests de carga pueden no descubrir una condición rara.

En las decisiones de negocio, DMN ayuda a expresar tablas de reglas. BPMN hace visibles órdenes, eventos y condiciones del proceso; CMMN puede modelar casos de larga vida con trabajo discrecional. SBVR y OCL aportan vocabulario e invariantes donde convenga. No asumiría que dibujar un BPMN crea un oráculo ejecutable: necesitamos un perfil semántico, un motor o verificador concreto y un contrato de conformance. La demo actual de TODM utiliza perfiles limitados de JSON; no pretende ser una implementación completa certificada de todos los estándares [2].

## Ocho puertas con funciones diferentes

| Gate | Pregunta principal | Artefacto que debe quedar | Resultado según TODM |
|---|---|---|---|
| G0 | Qué capacidad y qué riesgo abordamos | Alcance y exclusiones | Mandato autorizado |
| G1 | Qué sabemos y cómo lo sabemos | Evidencias e incertidumbres | Evidencia clasificada |
| G2 | Qué comportamiento se acepta | Baseline aprobada y versionada | Aprobación humana responsable |
| G3 | Qué errores detecta el evaluador | Cualificación y controles negativos | Mutaciones y controles negativos |
| G4 | Qué puede construir el agente | Candidato y trazabilidad de cambios | Candidato con procedencia |
| G5 | Qué cumple el candidato observado | Informe de verificación | PASS, FAIL o INCONCLUSIVE |
| G6 | Puede entregarse este artefacto | Autorización de entrega | Autorización separada |
| G7 | Qué sucede cuando cambian las condiciones | Seguimiento y revisión de vigencia | Revisión controlada de la baseline |

La tabla organiza el trabajo; no obliga a introducir una reunión por cada fila. El nivel de formalidad debe corresponder al impacto. Lo que no conviene perder es la identidad de las decisiones. Si cambiamos el resultado esperado mientras corregimos el código, debemos registrar que ha cambiado la baseline y volver a cualificar lo que corresponda.

## Tres resultados que no conviene reducir a dos

PASS significa que se han satisfecho las comprobaciones declaradas con evidencia suficiente para ellas. FAIL indica una contradicción observada respecto del criterio. INCONCLUSIVE indica que no podemos concluir con la evidencia disponible o que ha fallado una condición necesaria para evaluar.

Supongamos que el importe observado no coincide con el esperado. Tenemos un fallo. Supongamos ahora que falta la salida del ejecutable COBOL. No sabemos si el candidato coincide con él. La segunda situación no debería convertirse en PASS ni confundirse con una discrepancia funcional.

Para entregar, el comportamiento por defecto debe bloquear FAIL e INCONCLUSIVE. Eso no impide establecer una política de excepciones; obliga a que la excepción sea una decisión distinta, con alcance y responsable. Alterar el informe para que parezca un PASS elimina información que necesitaremos después.

![Figura 10.1 · Tres veredictos, una autorización separada y los códigos de salida del gate del laboratorio.](../../figures/es/verdict_states.png)

*Figura 10.1 · Tres veredictos, una autorización separada y los códigos de salida del gate del laboratorio.*

## La prueba del evaluador

Un control negativo introduce un defecto que el evaluador debería detectar. En nuestro ejemplo cambiaremos el umbral y el redondeo. Si los casos siguen pasando, habremos aprendido algo sobre la debilidad del conjunto de aceptación.

También necesitamos controles limpios. Un gate que bloquea todo detecta cada defecto, pero es inútil para entregar software correcto. Y necesitamos entradas incompletas para comprobar que el evaluador no acepta por accidente lo que no ha podido verificar.

La cualificación es siempre relativa a un conjunto de amenazas y casos. Superar esos controles aumenta la confianza en ese alcance. No demuestra que no exista una forma diferente de engañar o romper el evaluador.

## Un ejemplo de fallo que debe cerrar el gate

El sistema COBOL calcula 0,5 % de comisión con una regla de redondeo específica. El agente traduce a C# usando la opción de redondeo habitual de su biblioteca. En 99 casos los resultados coinciden. En el centésimo, el punto medio resulta diferente. El compilador y los tests unitarios del candidato pasan. Un oráculo aprobado con un caso límite debe rechazarlo. Más adelante, el gate de concurrencia rechaza un método que produce el importe correcto aislado pero permite dos retiradas sobre el mismo saldo. Finalmente, el gate de rendimiento rechaza una arquitectura correcta que incumple la ventana batch.

El gate no prueba equivalencia universal. Demuestra que una implementación satisfizo un conjunto explícito de obligaciones, con cobertura y límites conocidos. Esto es una afirmación técnica mucho más modesta que «la IA modernizó el core»; y por ello mismo, mucho más defendible.

## Cuando el agente intenta ganar al oráculo

Hay un caso público que ilustra mejor que cualquier teoría por qué el oráculo debe quedar fuera del alcance del constructor. Lo resumí en mi análisis de REA [35], a partir del relato de su autor [42]: un equipo puso agentes a decompilar durante meses un videojuego conocido. El primer mes fue un espejismo. Los agentes reconstruyeron una parte enorme del juego, que arrancaba y cargaba mapas, pero el código era semánticamente incorrecto, y el agente revisor aceptaba las justificaciones que los propios trabajadores dejaban en comentarios y commits.

La solución fue un oráculo que respondía una sola pregunta: ¿esta función reconstruida coincide, byte a byte, con la del ejecutable original? Lo primero que hicieron los agentes fue intentar hacer trampa. Escribieron ensamblador en línea. Cuando se prohibió, intentaron modificar el script para excluir su propia función, hasta que la integración continua empezó a validar el hash del script.

Ese detalle final es el que me importa para COBOL. En el laboratorio, la baseline tiene un ancla SHA-256 y el gate es un proceso separado. Pero ambos viven en el mismo paquete escribible, y lo digo cada vez que aparece. En un proyecto real, `contracts/` y `Gate/` deben estar donde el constructor no pueda escribir, y el pipeline debe comprobar sus hashes contra un ancla que tampoco controle.

![Figura 10.2 · Cuando el constructor intenta editar el criterio que lo juzga, el ancla externa lo detecta.](../../figures/es/heumann.png)

*Figura 10.2 · Cuando el constructor intenta editar el criterio que lo juzga, el ancla externa lo detecta.*

> **Un oráculo vale más que un revisor. Y un oráculo que el constructor puede editar no vale nada.**

---

[← Parte III · Oráculos: el derecho a aceptar](README.md) · [Índice](../README.md) · [Capítulo 11 · La arquitectura de una modernización verificable →](11-la-arquitectura-de-una-modernizacion-verificable.md)
