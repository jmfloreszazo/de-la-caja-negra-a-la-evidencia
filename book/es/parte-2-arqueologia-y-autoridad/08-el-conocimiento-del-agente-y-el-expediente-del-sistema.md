**Español** · [English](../../en/part-2-archaeology-and-authority/08-the-agent-s-knowledge-and-the-system-s-record.md)

[← Capítulo 7 · Legacy Archaeology asistida por agentes](07-legacy-archaeology-asistida-por-agentes.md) · [Índice](../README.md) · [Capítulo 9 · De la autoridad del agente a la autoridad de la regla →](09-de-la-autoridad-del-agente-a-la-autoridad-de-la-regla.md)

# Capítulo 8 · El conocimiento del agente y el expediente del sistema

> [!IMPORTANT]
> **Tesis del capítulo.** La memoria de un agente le ayuda a trabajar. El expediente del sistema permite aceptar. El conocimiento importante debe sobrevivir al modelo que lo resumió y a la sesión que lo descubrió.

## Recordar no es acreditar

Un agente puede conservar una nota que diga que una determinada comisión se redondea de cierta manera. Esa nota le ayuda a continuar trabajando. Sin embargo, alguien que deba aceptar la migración necesita más: la regla exacta, su procedencia, la aprobación vigente y las ejecuciones que la comprobaron.

En «De Leviatán al Autopilot» planteo una separación entre memoria del agente y registro institucional [1]. Aplicada a modernización, significa que el conocimiento importante debe sobrevivir al modelo que lo resumió y a la sesión que lo descubrió. La desaparición de un agente no debería borrar el motivo por el que aceptamos un cambio.

El expediente de una transformación reúne hechos, decisiones y resultados. Puede comenzar con archivos versionados. No exige una plataforma sofisticada desde el primer día. Sí necesita relaciones claras: esta versión de la regla se aprobó para este alcance; este candidato se verificó contra ella; estos resultados pertenecen a esta ejecución.

Un hash ayuda a comprobar identidad de contenido. No demuestra que ese contenido sea correcto ni que quien lo aprobó tuviera autoridad. Si un mismo actor puede sustituir el fichero y el hash esperado, ambos pueden seguir siendo consistentes después de una modificación indebida. La protección exige un anclaje fuera de su control.

Hay una idea que ya defendí al auditar agentes de Copilot en VS Code: git es la única versión que importa, y auditar no es lo mismo que prevenir [40]. Aplicada a la modernización, significa que la regla que aceptamos, el prompt que la produjo y el candidato que la cumple deben poder reconstruirse desde un repositorio versionado, no desde el recuerdo de una sesión. Y que una traza perfecta de lo que hizo un agente nos permite explicar un error, pero no evitarlo: para eso hacen falta permisos que se apliquen donde ocurre la acción.

En «Agent Host Protocol (AHP)» llegaba a una conclusión hermana: el dueño del estado de la sesión es el host, no el editor; los clientes son vistas [44]. El expediente de una modernización aplica esa idea un nivel más arriba. El estado que importa —la regla aprobada, la evidencia, la decisión— no vive en la herramienta con la que trabajamos, sino en un registro que todas consultan y ninguna posee.

## Las hipótesis deben poder perder

Un agente de comprensión propone una interpretación. Si toda la información posterior se organiza para confirmarla, tendremos una historia coherente y quizá falsa. El expediente debe conservar preguntas que podrían refutarla.

Para una comisión, buscaría valores que distingan truncamiento, redondeo al par y redondeo alejándose de cero. Para una regla de autorización, probaría el umbral exacto y el valor inmediatamente superior. Para una transición, examinaría el estado anterior y la ausencia de eventos que deberían ser obligatorios.

Estas pruebas discriminantes son más informativas que repetir cien veces un caso en el que todas las interpretaciones producen el mismo resultado. Su diseño exige entender el riesgo semántico. La cantidad de ejemplos ayuda después; antes necesitamos saber qué desacuerdo podrían revelar.

También debemos conservar la posibilidad de que falte evidencia. Un timeout puede significar que el programa falló, que la infraestructura no respondió o que nuestro adaptador no recogió el resultado. Convertir cualquier ausencia en un dato vacío y continuar destruye esa distinción.

## Cambiar de modelo sin perder el trabajo

La continuidad se vuelve más sencilla cuando los contratos no dependen de la conversación privada de un agente. Podemos sustituir el modelo encargado de construir un candidato y mantener el mismo conjunto de reglas aprobado. Podemos mejorar una herramienta de análisis y comparar sus hallazgos con los anteriores.

La identidad del modelo y su configuración siguen siendo relevantes para reproducir el proceso. Pero no deberían convertirse en la fuente de legitimidad del resultado. El criterio de aceptación pertenece al proyecto y a sus responsables.

Ese diseño también facilita la revisión humana. El experto no necesita leer cada token generado. Necesita comprender las decisiones que cambian el comportamiento y la evidencia que pretende justificarlas. Su tiempo se emplea mejor cuando el sistema le presenta discrepancias concretas y preguntas bien delimitadas.

> **Recordar no es acreditar. Un hash demuestra identidad, no corrección.**

---

[← Capítulo 7 · Legacy Archaeology asistida por agentes](07-legacy-archaeology-asistida-por-agentes.md) · [Índice](../README.md) · [Capítulo 9 · De la autoridad del agente a la autoridad de la regla →](09-de-la-autoridad-del-agente-a-la-autoridad-de-la-regla.md)
