**Español** · [English](../../en/part-2-archaeology-and-authority/06-rea-and-archaeology-that-leaves-a-trail.md)

[← Parte II · Arqueología, conocimiento y autoridad](README.md) · [Índice](../README.md) · [Capítulo 7 · Legacy Archaeology asistida por agentes →](07-legacy-archaeology-asistida-por-agentes.md)

# Capítulo 6 · REA y la arqueología que deja rastro

> [!IMPORTANT]
> **Tesis del capítulo.** Las herramientas investigan, los agentes proponen y la evidencia sostiene las afirmaciones. REA aporta una disciplina —procedencia, cobertura y desconocidos explícitos— más valiosa para COBOL que cualquier promesa de traducción.

La pérdida de documentación y la acumulación de reglas son problemas reales. Pero conviene añadir una precisión de ingeniería: el código fuente no es la única evidencia. Hay copybooks compartidos, definiciones de datasets, control de versiones, despliegues históricos, JCL, configuraciones CICS, DDL, catálogos, estadísticas de carga, incidencias, tickets y, sobre todo, comportamientos que el sistema todavía ejecuta. Algunas reglas están en una tabla de parametrización. Otras viven en una rutina no llamada desde hace años. Algunas son errores históricos de los que dependen sistemas consumidores.

Por eso no empezaría pidiendo «conviérteme estos dos millones de líneas». Empezaría por un **mapa de evidencias**. Cada artefacto recibe identidad, versión, hash, origen, propietario y restricciones. Un parser específico construye dependencias entre programas y copybooks; analizadores de JCL reconstruyen cadenas batch; un extractor de SQL localiza tablas y transacciones; un sistema de observación captura entradas, salidas y efectos de ejecución. Los agentes correlacionan esa información, pero no la convierten automáticamente en verdad.

## Qué aporta Reverse Engineer Anything

REA conecta agentes con herramientas de investigación de software mediante MCP y una interfaz de línea de comandos. Su documentación describe análisis de binarios nativos, ensamblados .NET, aplicaciones JavaScript y otros objetivos, con evidencia y limitaciones asociadas a los resultados. El análisis nativo profundo depende de proveedores como Ghidra, Hopper o IDA [3].

Lo sitúo en la fase de descubrimiento. Un agente puede recorrer hallazgos, formular preguntas y relacionar resultados de distintas herramientas. Eso ayuda a investigar. No convierte automáticamente una reconstrucción en una implementación equivalente, ni acredita soporte especializado para todo dialecto COBOL, copybook, JCL o entorno transaccional.

La documentación consultada no me permite presentar REA como traductor nativo COBOL a .NET. Para un sistema COBOL con fuentes, empezaría por herramientas que entiendan esas fuentes y su dialecto. Para un binario sin fuentes, el recorrido cambia y exige capacidades de análisis distintas.

Esta diferencia importa porque «ingeniería inversa» agrupa problemas muy diferentes. Recuperar relaciones entre variables de un fuente no equivale a reconstruirlas desde instrucciones de máquina. Un ensamblado con metadatos tampoco plantea el mismo problema que un ejecutable nativo. La herramienta debe elegirse según el artefacto disponible.

## Lo que aprendí con el caso VB6

Antes de escribir este libro me tocó mirar REA de cerca por un motivo muy práctico: aplicaciones VB6 sin fuentes que siguen en producción [35]. Me descargué el repositorio, leí el código y contrasté los casos que se citaban como prueba. Tres lecciones de aquel trabajo se trasladan casi literalmente a COBOL.

La primera es que lo interesante no es la lista de formatos, sino **el contrato de salida**. Cada resultado va atado a una evidencia: ruta, tamaño y SHA-256 del artefacto, el proveedor que lo produjo, la cobertura y, sobre todo, lo que no sabe. Los estados `unknown`, `partial`, `unsupported` o `truncated` nunca se agregan como un éxito. Es una herramienta diseñada para que el modelo no rellene huecos con imaginación.

La segunda es su registro de obligaciones de reconstrucción. Una afirmación del tipo «esta parte está reconstruida» solo se cierra si tiene un responsable, casos de prueba, un verificador que pasa y una autoridad del verificador comparable a la de la observación original. Si falta cualquiera de las cuatro, la obligación queda abierta. Es exactamente la disciplina que necesita una regla de negocio recuperada de un programa COBOL.

La tercera es que el conocimiento difícil suele estar ya en herramientas especializadas. En VB6, el formato del proyecto y el P-Code los resuelven herramientas con veinte años de historia; el agente aporta conducirlas, cruzar resultados y verificar. En COBOL ocurre lo mismo con los parsers de dialecto, los analizadores de JCL y los catálogos de Db2. **Lo que faltaba no era otro parser: era un agente capaz de usar los existentes con disciplina de evidencia.**

Pero COBOL no es VB6. En un mainframe solemos tener fuentes, copybooks y metadatos; el problema rara vez es decompilar y casi siempre es reconstruir la semántica de un sistema repartido entre programas, datos y operación. Por eso no traslado la cadena *VBDec + REA + Ghidra* tal cual. Traslado su principio.

## Tres aproximaciones complementarias

ProLeap ofrece un parser COBOL basado en ANTLR que construye un árbol sintáctico y un grafo semántico. Su documentación indica que extrae bloques EXEC SQL, SQLIMS y CICS como texto [4]. Es una base posible para análisis estructural; no lo tomaría como garantía de ejecución o equivalencia de todas esas extensiones.

IBM documenta un recorrido de validación COBOL–Java basado en grabaciones de entrada y salida, mapeo de recursos y generación y ejecución de pruebas JUnit [6]. Es una referencia relevante para el patrón de captura y comparación, aunque el destino documentado sea Java y su integración no sea la del laboratorio .NET de este libro.

AWS Transform documenta análisis de código, extracción de lógica y generación de requisitos para modernización de mainframe, incluyendo resultados de extracción y problemas por archivo [7]. Esto muestra otra aproximación centrada en recuperar estructura y significado. La documentación de un proveedor describe capacidades; una evaluación en nuestro entorno debe comprobar su cobertura real.

Estas aproximaciones no compiten necesariamente en una misma capa. REA puede ayudar a investigar un binario, un parser a analizar fuentes y una plataforma de modernización a organizar un recorrido específico. TODM propone cómo gobernar la aceptación del resultado de ese trabajo. La integración concreta sigue siendo una decisión de ingeniería.

## Un adaptador de evidencia COBOL

Propongo un componente que denomino COBOL Evidence Adapter. No es una capacidad que atribuya a REA ni una integración ya implementada en este laboratorio. Es una frontera de arquitectura: recibe artefactos y observaciones del entorno COBOL y los presenta mediante un contrato común.

Cada hallazgo debería identificar el artefacto, su hash, el localizador de origen, la herramienta y su versión, el método de obtención y los límites conocidos. Una relación deducida por el agente se registraría como hipótesis. Una ejecución observada conservaría entrada, estado relevante, salida y condiciones. Una regla aprobada tendría una autoridad y una versión distintas.

Imaginemos una regla de comisión hallada en un párrafo COBOL. El parser localiza la expresión. Una ejecución confirma un resultado en el límite de redondeo. El responsable de negocio confirma que esa es la política que debe mantenerse. Son tres piezas relacionadas, pero ninguna sustituye a las demás.

El grafo de conocimiento puede facilitar la navegación entre ellas. Su valor no está en usar una base de datos de grafos por principio, sino en permitir reconstruir el camino desde una conclusión hasta la evidencia que la sostiene. Una tabla bien diseñada puede ser suficiente al empezar.

Todo hallazgo debería registrar: «afirmación», «fuente», «líneas o transacción», «herramienta», «hash», «grado de certeza», «observación dinámica» y «pregunta pendiente». Si una regla de bonificación se infiere de tres ejemplos, debe quedar marcada como hipótesis. No será una baseline aprobada hasta que exista una autoridad de negocio o evidencia suficiente para asumirla. La disciplina de decir «no sabemos» es una capacidad arquitectónica.

Así se vería un hallazgo del laboratorio expresado con ese contrato. El hash es el real del fuente del laboratorio; el formato es una propuesta.

**Listado 6.1 · Un EvidenceItem: la afirmación, su procedencia y lo que todavía no sabemos** — *Ilustrativo*

```json
{
  "id": "EV-0142",
  "claim": "Cliente activo: la comisión se redondea al céntimo; el empate se aleja de cero",
  "status": "observed",
  "artifact": {
    "path": "legacy/fee.cob",
    "sha256": "136cc8c21ae514634f93b7139fb9e185b115e6b817c20890ad0e1f9265971cbf",
    "locator": "COMPUTE fee-cents ROUNDED"
  },
  "tool": { "name": "cobc", "version": "GnuCOBOL 3.1.2.0",
            "method": "ejecución con entrada fijada" },
  "observation": { "input": "0000002500200Y", "output": "APPROVE|00000001" },
  "coverage": "un empate exacto; sin negativos ni otras opciones de compilación",
  "unknowns": ["comportamiento en Enterprise COBOL con las opciones de producción"],
  "approval": null,
  "verifiedBy": []
}
```

Fíjate en los dos últimos campos. `approval` está vacío porque observar un comportamiento no lo convierte en política aprobada. `verifiedBy` está vacío porque todavía ningún candidato ha demostrado reproducirlo. Son tres piezas relacionadas, y ninguna sustituye a las otras.

![Figura 6.1 · Ciclo de vida de un EvidenceItem: observar no es aprobar, y aprobar no es verificar.](../../figures/es/evidence_states.png)

*Figura 6.1 · Ciclo de vida de un EvidenceItem: observar no es aprobar, y aprobar no es verificar.*

> **Una demo demuestra una posibilidad. La evidencia demuestra una propiedad.**

---

[← Parte II · Arqueología, conocimiento y autoridad](README.md) · [Índice](../README.md) · [Capítulo 7 · Legacy Archaeology asistida por agentes →](07-legacy-archaeology-asistida-por-agentes.md)
