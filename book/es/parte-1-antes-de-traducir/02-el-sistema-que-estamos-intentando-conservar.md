**Español** · [English](../../en/part-1-before-translating/02-the-system-we-are-trying-to-preserve.md)

[← Capítulo 1 · El mainframe no es una caja rápida](01-el-mainframe-no-es-una-caja-rapida.md) · [Índice](../README.md) · [Capítulo 3 · Por qué la conversión uno a uno no es modernización →](03-por-que-la-conversion-uno-a-uno-no-es-modernizacion.md)

# Capítulo 2 · El sistema que estamos intentando conservar

> [!IMPORTANT]
> **Tesis del capítulo.** El comportamiento que importa atraviesa programas, datos, procesos nocturnos y personas. Y no todo lo que el sistema hace hoy merece convertirse en requisito mañana.

## La memoria está repartida

Una aplicación heredada contiene decisiones que quizá nadie tomaría hoy de la misma manera. Algunas siguen siendo necesarias. Otras fueron soluciones temporales. Hay comportamientos que el negocio considera esenciales y otros que simplemente lleva décadas tolerando. A menudo todos están mezclados en el mismo recorrido de ejecución.

Por eso me resulta insuficiente empezar una modernización preguntando cuántas líneas de código tenemos. Necesito saber qué compromisos cumple el sistema, con quién los cumple y qué ocurre cuando deja de cumplirlos. El código es una parte de la respuesta. También lo son los datos, las tablas de parametrización, los procesos nocturnos, las interfaces y las personas que conocen las excepciones.

Imaginemos una liquidación que se ejecuta al cierre del día. Un programa calcula importes, otro agrupa movimientos y un tercero genera un fichero para una entidad externa. Una pantalla permite corregir incidencias antes del envío. El comportamiento que debemos conservar atraviesa todos esos elementos. Traducir correctamente la primera rutina no demuestra que hayamos conservado la liquidación.

Es una de las ideas que encuentro más valiosas en lo que se ha escrito sobre COBOL: devuelve la atención al conocimiento que sostiene la operación. Una organización puede seguir dependiendo de un sistema mientras pierde la capacidad de explicarlo. Para mi propuesta, esa observación tiene una consecuencia directa: la recuperación del conocimiento debe producir artefactos utilizables para decidir y verificar.

Una explicación legible ayuda. Una explicación vinculada a una regla, un responsable y una prueba permite avanzar más. La documentación deja de ser una narración paralela y comienza a formar parte del mecanismo de aceptación.

## Conservar comportamiento no significa conservar cualquier resultado

Supongamos que el sistema cobra una comisión incorrecta desde hace años. Una reimplementación que reproduce ese cobro es compatible con el comportamiento observado. Eso no la convierte en correcta respecto de la política del negocio.

Necesitamos separar dos preguntas. ¿Qué hace el sistema actual? ¿Qué debe hacer el sistema que vamos a aceptar? La primera se responde mediante observación, análisis y pruebas de caracterización. La segunda exige una decisión autorizada sobre reglas y excepciones. Cuando las respuestas difieren, el proyecto incluye un cambio de comportamiento que debe quedar identificado.

Esta distinción evita dos errores frecuentes. El primero consiste en corregir silenciosamente algo que parecía un defecto, sin saber qué consumidor dependía de ello. El segundo consiste en elevar todo comportamiento histórico a requisito permanente. Ambos pueden introducir problemas que una comparación superficial no detectará.

Mi unidad de trabajo preferida es una capacidad delimitada: un cálculo, una decisión, un intercambio o una transición de estado que podamos observar y explicar. Su tamaño debe permitir construir evidencia suficiente y controlar el cambio. No tiene por qué coincidir con un programa completo ni con el microservicio que alguien dibujó al principio.

Al terminar esta fase deberíamos poder describir qué conservamos, qué cambiamos expresamente y qué todavía desconocemos. La última categoría también tiene valor. Una incertidumbre registrada puede investigarse; una incertidumbre disfrazada de certeza acaba entrando en el diseño.

> **Una incertidumbre registrada se puede investigar. Una incertidumbre disfrazada de certeza acaba en el diseño.**

---

[← Capítulo 1 · El mainframe no es una caja rápida](01-el-mainframe-no-es-una-caja-rapida.md) · [Índice](../README.md) · [Capítulo 3 · Por qué la conversión uno a uno no es modernización →](03-por-que-la-conversion-uno-a-uno-no-es-modernizacion.md)
