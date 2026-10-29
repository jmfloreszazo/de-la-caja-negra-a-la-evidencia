**Español** · [English](../../en/part-7-organization/36-a-hundred-risks-for-choosing-patterns-with-judgement.md)

[← Capítulo 35 · Cuándo NO migraría](35-cuando-no-migraria.md) · [Índice](../README.md) · [Capítulo 37 · El nuevo contrato de modernización →](37-el-nuevo-contrato-de-modernizacion.md)

# Capítulo 36 · Cien riesgos para elegir patrones con criterio

> [!IMPORTANT]
> **Tesis del capítulo.** No existe un catálogo canónico y verificable de los cien problemas de COBOL ordenados por frecuencia. Sí podemos tener un registro de trabajo donde cada riesgo lleve una opción de aplicación, una capacidad de infraestructura y la prueba que podría refutarlas.

He buscado un catálogo canónico de los cien problemas principales de COBOL y no he encontrado una referencia verificable con ese alcance y una clasificación por frecuencia. Sí hay fuentes útiles para construir un capítulo riguroso: IBM documenta problemas concretos de migración de compilador, AWS reúne patrones de mainframe y desacoplamiento, y Azure ofrece catálogos de patrones y arquitecturas OLTP [30–34]. No son una lista común de cien problemas ni prometen cubrir cualquier sistema.

Por eso presento un catálogo propio de cien riesgos de modernización. La numeración sirve para identificarlos y relacionarlos con evidencias; no expresa frecuencia, gravedad ni una prioridad universal. Parte del catálogo trata semántica COBOL, otra parte trata servicios mainframe y el resto reúne problemas de sistemas empresariales que también aparecen al modernizar otras tecnologías.

Cada entrada propone una combinación candidata de aplicación e infraestructura y una comprobación que podría refutarla. No afirma que la solución esté implementada, validada o sea adecuada para todos los casos. El assessment debe registrar aplicabilidad, responsable, regla original, decisión de destino y evidencia de aceptación antes de cerrar una entrada.

La documentación de IBM resulta especialmente instructiva: incluso recompilar para una versión nueva de COBOL puede hacer visibles datos numéricos inválidos, tamaños incompatibles o valores sin inicializar. No necesitamos cambiar de lenguaje para descubrir una dependencia semántica [30]. Una arquitectura nueva no corrige automáticamente esas condiciones.

## Cómo utilizar el catálogo

Empezaría con tres ejemplos. Ante un fichero con packed decimal conservaría bytes y copybook, implementaría el codec y probaría límites antes de normalizar el almacenamiento. Ante dos débitos concurrentes fijaría la unidad transaccional y una prueba de sobregiro antes de decidir si intervienen actores. Ante una ventana batch incumplida analizaría el camino crítico y el sesgo antes de añadir workers. El patrón viene después de la propiedad que queremos conservar.

Las propuestas de plataforma expresan capacidades, no equivalencias automáticas entre productos. Un broker local puede implementar orden por clave; una opción Azure puede usar sesiones si su contrato encaja. Una base de datos local y un servicio gestionado pueden proteger una transacción, pero deben compararse con las políticas reales de aislamiento, persistencia y recuperación.

Un actor, CQRS o event sourcing tampoco debe convertirse en destino obligatorio. CQRS puede separar una proyección de lectura del núcleo de escritura; la proyección necesita una política de vigencia y reconciliación. Event sourcing puede aportar un historial de cambios como fuente de verdad, pero exige evolución de eventos, replay y validación. El ledger append only es una decisión de dominio más concreta: puede existir en SQL sin adoptar event sourcing para toda la aplicación.

El laboratorio incluye el catálogo en inglés, en JSON y Markdown (`risk-catalog/`), con el estado inicial de evaluación y su relación con los controles sintéticos; el anexo [E](../anexos/anexo-e-catalogo-de-cien-riesgos.md) lo reproduce en español. Ninguno de los cien riesgos figura como resuelto en producción. Así podemos utilizarlo como registro de trabajo y ampliar cada entrada cuando dispongamos de un caso real.

El anexo [E](../anexos/anexo-e-catalogo-de-cien-riesgos.md) reproduce el catálogo completo, agrupado en diez familias: datos y representaciones, cálculo monetario y tiempo, flujo y estado de programas, ficheros y datasets, acceso a bases de datos, transacciones y mensajería financiera, batch y planificación, integración y coexistencia, rendimiento y capacidad, y SDLC, recuperación y gobierno. De los cien, once están tocados parcialmente por algún control sintético del laboratorio; ninguno figura como resuelto en producción.

## Resolver una entrada exige más que reconocer un patrón

Para cerrar R048 no basta con decir que el código adquiere locks en orden: hay que ejecutar las historias relevantes en el motor de destino, observar víctimas y reintentos y reconciliar efectos. Para cerrar R094 necesitamos restaurar y recuperar bajo las condiciones que acepta el servicio. Para cerrar R099 debemos demostrar que la plataforma impide entregar un artefacto diferente, incluso si el constructor lo intenta.

Esta disciplina convierte el catálogo en una conexión práctica entre arqueología, arquitectura y SDLC. Podemos empezar conservando COBOL, reemplazar una capacidad o cambiar infraestructura. En cada ruta queda la misma pregunta: qué evidencia demuestra que la nueva combinación conserva el compromiso que hemos decidido aceptar.

> **El patrón viene después de la propiedad que queremos conservar.**

---

[← Capítulo 35 · Cuándo NO migraría](35-cuando-no-migraria.md) · [Índice](../README.md) · [Capítulo 37 · El nuevo contrato de modernización →](37-el-nuevo-contrato-de-modernizacion.md)
