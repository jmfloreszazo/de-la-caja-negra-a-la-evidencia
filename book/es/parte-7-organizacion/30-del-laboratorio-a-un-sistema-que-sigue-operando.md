**Español** · [English](../../en/part-7-organization/30-from-the-lab-to-a-system-that-keeps-running.md)

[← Parte VII · De la evidencia a la organización](README.md) · [Índice](../README.md) · [Capítulo 31 · El SDLC como parte del motor de migración →](31-el-sdlc-como-parte-del-motor-de-migracion.md)

# Capítulo 30 · Del laboratorio a un sistema que sigue operando

> [!IMPORTANT]
> **Tesis del capítulo.** Durante la convivencia, cada capacidad tiene un único dueño de la escritura; volver atrás puede exigir transformar datos; y cualquier cambio de reglas, compiladores o modelos obliga a renovar la evidencia de aceptación.

## La convivencia tiene un dueño de la escritura

Un cálculo sin persistencia es una buena entrada al problema. Una aplicación empresarial exige decidir cómo conviven las dos implementaciones mientras se verifica la nueva.

En una ejecución en sombra, el sistema de referencia mantiene la operación y la nueva implementación recibe entradas comparables para evaluar su respuesta. Hay que evitar que esa sombra duplique efectos externos. Una notificación, un cargo o una actualización no deben ejecutarse dos veces porque queramos comparar resultados.

La captura debe definir el estado observado. Si una implementación lee los datos antes de una actualización y la otra después, una diferencia puede deberse al momento de lectura. La evidencia debe permitir distinguir un defecto semántico de una divergencia introducida por el propio experimento.

La propiedad de la escritura necesita ser explícita por capacidad y fase. La estrategia puede incluir enrutamiento gradual, reconciliación y mecanismos de idempotencia, según el sistema. No introduciría escritura simultánea en dos modelos de datos como un detalle secundario de integración.

![Figura 30.1 · Fases de convivencia: en cada una hay un único dueño de la escritura, y volver atrás puede exigir transformar datos.](../../figures/es/coexistence.png)

*Figura 30.1 · Fases de convivencia: en cada una hay un único dueño de la escritura, y volver atrás puede exigir transformar datos.*

## Volver atrás también puede transformar datos

Un rollback de código no garantiza que el sistema anterior comprenda los datos escritos por la versión nueva. Tampoco retira un mensaje ya consumido o deshace una interacción externa. El plan de retorno debe describir las consecuencias que pueden revertirse y las que requieren compensación o reparación.

Antes de ampliar tráfico, comprobaría el mecanismo de corte, la reconciliación y la recuperación. Si la ventana de retorno depende de un volumen máximo de cambios, ese límite forma parte de la decisión de entrega. Una opción que desaparece después de unas horas no debería describirse como disponible indefinidamente.

Los oráculos operativos amplían los funcionales. Nos interesan el tiempo de proceso, el uso de recursos, la recuperación y la consistencia de datos. Sus umbrales se fijan de acuerdo con el servicio. No elegiría un porcentaje universal de equivalencia para aprobar cualquier migración.

Una discrepancia pequeña en frecuencia puede afectar a la operación más importante. Por eso la clasificación de riesgos y las reglas críticas pesan más que una media global. Cero diferencias observadas tampoco prueba ausencia de diferencias en toda la población.

## La deriva exige volver a evaluar

Después del corte cambian reglas, datos, compiladores y dependencias. También puede cambiar el modelo que ayuda a mantener el sistema. G7 conecta esos cambios con la evidencia de aceptación que debe renovarse.

Si una tasa pasa de dos decimales a cuatro, no basta con volver a ejecutar el conjunto antiguo y celebrar que sigue verde. El contrato ha cambiado. Necesitamos nuevos límites, nuevas expectativas y posiblemente otra representación.

La modernización habrá mejorado de verdad la capacidad de evolución cuando podamos hacer ese cambio sin perder el vínculo entre intención, implementación y aceptación. Esa continuidad es uno de los resultados que me interesa perseguir con TODM.

> **Un rollback de código no retira un mensaje ya consumido ni deshace una interacción externa.**

---

[← Parte VII · De la evidencia a la organización](README.md) · [Índice](../README.md) · [Capítulo 31 · El SDLC como parte del motor de migración →](31-el-sdlc-como-parte-del-motor-de-migracion.md)
