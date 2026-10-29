**Español** · [English](../en/00b-prologue.md)

[← Convenciones](00a-convenciones.md) · [Índice](README.md) · [Cómo leer este libro →](00c-como-leer-este-libro.md)

# Prólogo

> Una traducción puede conservar las instrucciones. Una modernización debe conservar las garantías que hacen posible el negocio y cambiar aquello que impide su evolución.

Hay una escena que resume buena parte de la conversación actual sobre modernización. Un agente recibe un programa antiguo, produce una versión en un lenguaje moderno y ejecuta una demostración. La aplicación arranca. La pantalla responde. Los ejemplos salen bien. Alguien pregunta cuánto tardaríamos en hacer lo mismo con el sistema de una empresa.

Mi primera pregunta sería otra: ¿qué acabamos de demostrar?

No es una forma de quitar mérito al resultado. Es la pregunta que permite darle un valor. Hemos demostrado que una herramienta puede producir una implementación que supera determinados ejemplos, bajo unas condiciones concretas. Para avanzar necesitamos identificar esas condiciones, comprobar qué queda fuera y decidir quién tiene autoridad para aceptar el riesgo que permanece.

Adelanto la conclusión sin ceremonia: **la IA puede investigar, proponer y construir; aceptar el resultado exige contratos, oráculos independientes y una autoridad explícita.** Y hay una segunda conclusión, que me ha costado más formular: **una modernización 1:1 puede ser un puente, pero nunca deberíamos confundir el puente con la ciudad a la que queremos llegar.**

Este libro nace de esa distancia entre una posibilidad técnica y una decisión de arquitectura. Reúne tres líneas de trabajo que he venido desarrollando: la modernización de aplicaciones, la construcción con agentes de IA y el gobierno del software mediante evidencia independiente. Mi propuesta, Test Oracle-Driven Methodology, o TODM, intenta convertir esa relación en un proceso que se pueda inspeccionar, ejecutar y discutir. La he ido desarrollando en público: en el repositorio de TODM [2], en «De Leviatán al Autopilot» [1], en «Agentes al vuelo frente a un harness gobernado» [41] y en mi análisis de REA, «Más allá del hype» [35].

COBOL es un caso especialmente útil para hacerlo. Obliga a hablar de datos, precisión, contratos, operación y conocimiento de negocio. No permite esconder una migración detrás de una interfaz más atractiva. Si el saldo es incorrecto, el hecho de haberlo calculado con un framework reciente aporta poco consuelo.

Leer a varios autores sobre la modernización de COBOL y la IA ayuda a situar el problema. La defensa del conocimiento acumulado merece atención. También merece discusión la frontera que algunos establecen entre lo que la IA puede comprender y lo que puede transformar. En estas páginas tomo esa discusión en serio y la convierto en decisiones verificables.

La capacidad también forma parte de esta discusión. Debemos conservar la atomicidad de las transacciones, entender los bloqueos y sostener la carga con la política de durabilidad y recuperación acordada. Un servidor mayor o más actores solo ayudan si resuelven el recurso que limita ese compromiso.

El recorrido termina en código. El laboratorio acompaña un pequeño servicio COBOL desde su ejecución local hasta la comparación con una implementación en .NET 10. Incluye errores deliberados, evidencia incompleta y una entrega bloqueada pese a que el comportamiento sea correcto. Su tamaño permite entender el mecanismo. Su alcance explícito evita confundirlo con una migración empresarial terminada.

Quiero que el lector pueda reproducir la demostración y, después, formular mejores preguntas ante la siguiente. La facilidad de ejecutar el ejemplo debe ayudarnos a ver la dificultad real con más claridad.

---

[← Convenciones](00a-convenciones.md) · [Índice](README.md) · [Cómo leer este libro →](00c-como-leer-este-libro.md)
