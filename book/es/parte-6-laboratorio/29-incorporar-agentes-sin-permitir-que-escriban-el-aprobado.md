**Español** · [English](../../en/part-6-lab/29-bringing-in-agents-without-letting-them-write-the-approval.md)

[← Capítulo 28 · Transferencias, bloqueos y fallos en local](28-transferencias-bloqueos-y-fallos-en-local.md) · [Índice](../README.md) · [Parte VII · De la evidencia a la organización →](../parte-7-organizacion/README.md)

# Capítulo 29 · Incorporar agentes sin permitir que escriban el aprobado

> [!IMPORTANT]
> **Tesis del capítulo.** El siguiente paso es poner un agente a construir el candidato. Puede consultar, ejecutar y corregir; no puede tocar los casos reservados ni el evaluador. Y cada cambio de modelo, prompt o presupuesto es una condición experimental distinta.

## El siguiente paso tiene dos modos

Separaría la demostración determinista de un experimento con agentes. En el primer modo, conservamos implementaciones, entradas y expectativas fijadas para explicar el proceso. En el segundo, un agente recibe una tarea de construcción y debe producir un candidato bajo restricciones registradas.

El agente puede consultar fuentes y el contrato público, ejecutar sus tests y corregir el programa. No puede cambiar los casos reservados ni el evaluador de aceptación. Un verificador externo ejecuta el candidato en un entorno controlado. El informe devuelve información suficiente para corregir, conforme al protocolo del experimento.

![Figura 29.1 · Un agente constructor dentro de un harness gobernado: corrige contra un verificador externo que no controla.](../../figures/es/agent_loop.png)

*Figura 29.1 · Un agente constructor dentro de un harness gobernado: corrige contra un verificador externo que no controla.*

Si cambiamos modelos, presupuestos, prompts o herramientas, lo registramos como una condición experimental distinta. Decir que «lo hizo la IA» no permite explicar qué combinación produjo el resultado ni repetir el proceso.

Un agente investigador puede proponer reglas desde políticas, entrevistas y observaciones autorizadas; el COBOL es una fuente auxiliar cuando sea necesario. El constructor puede **programar desde cero** la capacidad en C# sin copiar la estructura del legado. TODM compara el resultado con oráculos independientes y reglas aprobadas; Golden Master conserva por separado el comportamiento observado. La autoridad del negocio decide qué mantener, corregir o retirar.

## REA entra cuando el problema lo necesita

Para el fuente pequeño del laboratorio no necesitamos un decompilador. Incluir REA por obligación estética añadiría complejidad sin aclarar la prueba. Su integración tiene sentido cuando la capacidad investigada reside en un artefacto que sus herramientas ayudan a examinar.

Una extensión coherente consistiría en tomar un ejecutable autorizado, fijar su hash y pedir a un agente que investigue una función concreta mediante REA. Los hallazgos alimentarían hipótesis y pruebas. La reconstrucción se evaluaría después contra un oráculo adecuado. El resultado documentaría qué se observó directamente y qué se dedujo.

Para sistemas COBOL de mayor tamaño, empezaría por las **capacidades, contratos externos, excepciones y garantías operativas**. Sólo ante una duda técnica concreta evaluaría parsers de dialecto o herramientas de dependencias. MCP puede exponer los hallazgos, pero el análisis sintáctico no es un requisito para reprogramar el sistema ni autoriza una regla de negocio.

## Los errores correlacionados siguen siendo posibles

Dos agentes pueden repetir la misma interpretación equivocada. Cambiar de modelo tampoco garantiza independencia. Si ambos reciben una especificación incorrecta y el evaluador deriva de esa misma especificación sin revisión, el circuito puede confirmar su propio error.

La defensa requiere diversidad de evidencia: comportamiento observado, reglas aprobadas, propiedades conocidas y controles adversariales. En una evaluación seria también conviene separar quién construye la solución de quien prepara los casos ocultos y adjudica los resultados.

Anthropic distingue entre flujos definidos por código y agentes que deciden dinámicamente sus pasos y herramientas [11]. Esa distinción ayuda a describir con precisión lo que hemos construido. Nuestro laboratorio es un flujo determinista. El experimento futuro puede incorporar autonomía, pero esa autonomía debe demostrar que añade valor frente a una ruta más simple.

En «Agentes al vuelo frente a un harness gobernado» comparé agentes de línea de comandos más allá de la demo y llegué a una conclusión incómoda: la detección de defectos, la fiabilidad y el control de calidad tienen un coste, y ese coste no desaparece; se paga midiendo o se paga en producción [41]. En una modernización COBOL, el harness gobernado es el que fija el mandato del capítulo [9](../parte-2-arqueologia-y-autoridad/09-de-la-autoridad-del-agente-a-la-autoridad-de-la-regla.md), protege el gate del capítulo [10](../parte-3-oraculos/10-todm-y-el-problema-de-aceptar-lo-que-construimos.md) y registra cada intento para el estudio del capítulo [34](../parte-7-organizacion/34-medir-lo-que-todavia-no-sabemos.md).

La forma concreta de ese harness la construí en «Del modelo que responde al agente que trabaja», con C#, .NET 10 y Microsoft Foundry: el harness gobierna la planificación, el estado, las herramientas y las aprobaciones, y CodeAct ejecuta de forma compacta las tareas intensivas en datos y llamadas a herramientas [43]. Y en «MCP, A2A y AHP» expliqué por qué esas tres siglas resuelven problemas distintos en capas distintas y por qué un agente debería vivir en un contenedor [46]. Es la misma razón por la que el laboratorio se ejecuta en un contenedor sin red, y por la que el experimento E4 debería encerrar al agente constructor en uno.

> **Decir que «lo hizo la IA» no permite explicar qué combinación produjo el resultado ni repetir el proceso.**

---

[← Capítulo 28 · Transferencias, bloqueos y fallos en local](28-transferencias-bloqueos-y-fallos-en-local.md) · [Índice](../README.md) · [Parte VII · De la evidencia a la organización →](../parte-7-organizacion/README.md)
