**Español** · [English](../../en/part-1-before-translating/04-what-i-share-with-other-authors-and-where-i-disagree.md)

[← Capítulo 3 · Por qué la conversión uno a uno no es modernización](03-por-que-la-conversion-uno-a-uno-no-es-modernizacion.md) · [Índice](../README.md) · [Capítulo 5 · Modernizar exige elegir qué problema resolvemos →](05-modernizar-exige-elegir-que-problema-resolvemos.md)

# Capítulo 4 · Lo que comparto con otros autores y dónde discrepo

> [!IMPORTANT]
> **Tesis del capítulo.** La advertencia sobre el conocimiento perdido es valiosa. Convertirla en una imposibilidad general no lo es: un generador probabilístico puede alimentar una verificación determinista.

## Una advertencia útil

Después de leer a varios autores, encuentro ideas que comparto. Proponen proteger el conocimiento de negocio, refactorizar de manera gradual y utilizar la IA para comprender código que resulta difícil de mantener. También cuestionan las promesas de sustitución automática y subrayan el valor de los especialistas que conocen estos sistemas. Comparto la necesidad de examinar esas promesas y de evitar que una transformación destruya conocimiento que todavía necesitamos.

Los mejores de esos textos tienen además una cualidad que quiero conservar: plantean una tesis, la conectan con historias y conducen al lector hacia una decisión. Un libro técnico puede tener voz. Puede discutir. Puede explicar por qué al autor le preocupa una determinada forma de trabajar. No necesita convertirse en una sucesión de diapositivas.

Mi desacuerdo aparece cuando una advertencia razonable se convierte en una imposibilidad general. Que una traducción automática sin control sea peligrosa no demuestra que cualquier construcción asistida por IA sea inviable. Que un monolito dependa de estado no lo hace incompatible con cualquier servicio cloud. Que muchos sistemas estén poco documentados no significa que carezcan de estructura analizable.

Conviene separar los problemas para poder resolverlos. El lenguaje, el runtime, la arquitectura, los datos y la operación introducen restricciones distintas. Si los tratamos como una única incompatibilidad, perdemos capacidad de elección.

## La nube no obliga a elegir una única arquitectura

La documentación de arquitectura de Microsoft describe alternativas para ejecutar aplicaciones COBOL mediante compiladores y entornos compatibles en máquinas virtuales o contenedores de Azure [5]. Esa documentación no acredita por sí sola una migración concreta ni sus ahorros. Sí basta para cuestionar la afirmación general de que COBOL y cloud son incompatibles.

Trasladar una carga puede conservar acoplamientos y restricciones. También puede resolver un problema de infraestructura sin reescribir toda la aplicación. La decisión debe responder a un objetivo explícito. Si queremos reducir el tiempo necesario para cambiar una regla de negocio, mover el mismo ejecutable a otra máquina quizá no sea suficiente. Si queremos retirar un entorno específico, puede ser una pieza relevante.

Tampoco un destino Java o C# obliga a distribuir todas las transacciones, eliminar el batch o sustituir cada función por un microservicio. Esas son decisiones arquitectónicas. Mezclarlas con el cambio de lenguaje añade variables a una transformación que ya es difícil de comprobar.

## Un generador probabilístico puede alimentar una verificación determinista

Un modelo puede producir código incorrecto. Un humano también. La cuestión de ingeniería es qué mecanismos detectan el error antes de aceptar el resultado y cuáles son sus límites.

La naturaleza probabilística del generador no determina por sí sola la naturaleza de la implementación generada. Un programa compilado puede ejecutar una regla determinista. A su vez, una prueba determinista puede estar mal especificada. Por eso mi propuesta no termina en ejecutar tests: exige examinar quién definió el resultado esperado, de dónde procede y qué errores puede detectar el evaluador.

Aquí amplío la tesis de la IA como motor de comprensión. La comprensión asistida es valiosa, pero también puede equivocarse. Una explicación incorrecta de una regla puede contaminar las especificaciones y todas las pruebas posteriores. La frontera útil no está entre permitir a la IA explicar y prohibirle construir. Está entre proponer y aceptar con evidencia adecuada.

## Mi posición, en una tabla

Para que el desacuerdo sea útil tiene que ser concreto. Esta es la comparación, punto por punto.

| Cuestión | Lo que suele defenderse | Mi posición |
|---|---|---|
| IA para comprender COBOL | Muy favorable | Coincido, con evidencia vinculada a cada afirmación |
| IA para generar Java o C# | Muy crítica | Viable con restricciones, contrato y validación independiente |
| Mantener COBOL | Opción preferente | Depende del objetivo, la carga y el coste de verificar |
| Refactorización incremental | Recomendable | Coincido |
| Equivalencia funcional | Riesgo principal | Debe convertirse en un criterio de aceptación verificable |
| Modelos privados | Recomendados | Importa el control de los datos, no necesariamente entrenar un modelo propio |

> **La frontera útil no está entre dejar a la IA explicar y prohibirle construir. Está entre proponer y aceptar con evidencia.**

---

[← Capítulo 3 · Por qué la conversión uno a uno no es modernización](03-por-que-la-conversion-uno-a-uno-no-es-modernizacion.md) · [Índice](../README.md) · [Capítulo 5 · Modernizar exige elegir qué problema resolvemos →](05-modernizar-exige-elegir-que-problema-resolvemos.md)
