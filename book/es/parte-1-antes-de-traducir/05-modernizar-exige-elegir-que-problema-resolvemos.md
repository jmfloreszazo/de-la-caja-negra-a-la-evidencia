**Español** · [English](../../en/part-1-before-translating/05-modernizing-means-choosing-which-problem-we-solve.md)

[← Capítulo 4 · Lo que comparto con otros autores y dónde discrepo](04-lo-que-comparto-con-otros-autores-y-donde-discrepo.md) · [Índice](../README.md) · [Parte II · Arqueología, conocimiento y autoridad →](../parte-2-arqueologia-y-autoridad/README.md)

# Capítulo 5 · Modernizar exige elegir qué problema resolvemos

> [!IMPORTANT]
> **Tesis del capítulo.** «Pasarlo a .NET» describe un destino tecnológico, no un resultado. Cada objetivo exige evidencias distintas, y cada alternativa debe explicar su coste de verificación y su forma de volver atrás.

## El destino no sustituye al diagnóstico

«Pasarlo a .NET» describe una tecnología de destino. Todavía no describe el resultado que necesita la organización. Podemos terminar con el mismo proceso difícil de cambiar, ahora escrito en C#. También podemos conservar COBOL y mejorar de manera importante la operación, las pruebas o la exposición de capacidades.

Antes de seleccionar una ruta, fijaría el resultado buscado. Puede ser retirar una dependencia, recuperar capacidad de mantenimiento, reducir una ventana batch o permitir una nueva integración. Cada objetivo requiere evidencias distintas. Un tiempo de compilación menor no demuestra una mejor continuidad de servicio; una API nueva no demuestra que el proceso interno sea más fácil de evolucionar.

Existen decisiones que pueden combinarse. Conservar y documentar puede ser la acción correcta para un componente estable. Encapsular permite ofrecer una interfaz controlada. Refactorizar mejora la estructura manteniendo el comportamiento. Reemplazar una capacidad puede tener sentido cuando el beneficio supera el coste y podemos verificar la transición. Un producto estándar puede resolver otra parte, siempre que aceptemos y evaluemos sus diferencias.

No establecería una preferencia universal antes de estudiar el sistema. Sí exigiría que cada alternativa explicase su coste de verificación, sus dependencias y su forma de retorno. Una opción aparentemente barata puede desplazar el gasto hacia la reconciliación de datos o hacia años de convivencia.

## La unidad de corte debe poder sostenerse sola

En el laboratorio elegiremos un cálculo y una decisión sin persistencia. Es una unidad deliberadamente pequeña. Permite observar entradas y salidas sin introducir bloqueos de base de datos, mensajes pendientes o recuperaciones a mitad de un proceso.

En un sistema real, esa comodidad no viene dada. Una función que parece autónoma puede leer un fichero preparado por un job anterior o depender de una variable compartida. Un programa llamado desde varias transacciones puede interpretar de forma distinta el mismo registro. La primera tarea consiste en descubrir esas dependencias, no en ignorarlas para que encajen en el diagrama.

Una frontera útil describe entradas, salidas, estado previo, efectos laterales y condiciones de fallo. También identifica quién puede escribir y cuándo. Si durante la convivencia dos sistemas modifican los mismos datos sin una estrategia de consistencia, la dificultad puede superar el beneficio de haber dividido el código.

Mi criterio sería empezar donde la evidencia sea recuperable y el impacto esté contenido. Eso no significa elegir únicamente casos triviales. Significa elegir un caso que permita aprender sobre el sistema y que pueda detenerse sin convertir cada incertidumbre en una urgencia de producción.

## El éxito necesita una medida de negocio

El proyecto debe medir algo más que código producido. Importan los defectos que escapan, el tiempo de revisión, el esfuerzo de aclarar reglas, el coste de operación y la capacidad de recuperar el servicio. La IA puede reducir una parte y aumentar otra.

La comparación justa incluye el coste de construir y mantener los oráculos. Es un trabajo real. Si lo ocultamos, convertimos TODM en una promesa comercial difícil de sostener. Mi interés está en averiguar cuándo ese coste se compensa con una reducción de incertidumbre y de errores aceptados.

> **Una opción aparentemente barata puede desplazar el gasto a años de reconciliación.**

---

[← Capítulo 4 · Lo que comparto con otros autores y dónde discrepo](04-lo-que-comparto-con-otros-autores-y-donde-discrepo.md) · [Índice](../README.md) · [Parte II · Arqueología, conocimiento y autoridad →](../parte-2-arqueologia-y-autoridad/README.md)
