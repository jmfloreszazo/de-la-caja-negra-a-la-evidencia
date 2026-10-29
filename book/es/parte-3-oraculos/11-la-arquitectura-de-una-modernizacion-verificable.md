**Español** · [English](../../en/part-3-oracles/11-the-architecture-of-a-verifiable-modernization.md)

[← Capítulo 10 · TODM y el problema de aceptar lo que construimos](10-todm-y-el-problema-de-aceptar-lo-que-construimos.md) · [Índice](../README.md) · [Capítulo 12 · COBOL y C# deben acordar el significado →](12-cobol-y-c-deben-acordar-el-significado.md)

# Capítulo 11 · La arquitectura de una modernización verificable

> [!IMPORTANT]
> **Tesis del capítulo.** Cuatro responsabilidades —descubrir, gobernar, construir y verificar— y una autorización de entrega que consume sus resultados. La separación tiene que existir en los permisos, no solo en el diagrama.

## Cuatro responsabilidades

Organizaría la solución alrededor de cuatro responsabilidades: descubrir evidencia, gobernar el comportamiento esperado, construir candidatos y verificar observaciones. La autorización de entrega consume sus resultados y aplica las condiciones de publicación.

![Figura 11.1 · Contexto de una modernización verificable: personas, sistemas y responsabilidades.](../../figures/es/c4_context.png)

*Figura 11.1 · Contexto de una modernización verificable: personas, sistemas y responsabilidades.*

La capa de descubrimiento accede a fuentes, binarios, configuraciones y capturas autorizadas. Los agentes de comprensión trabajan sobre ese material. Sus conclusiones conservan referencias y dudas. El COBOL Evidence Adapter propuesto sirve de frontera para normalizar los hallazgos sin borrar su procedencia.

La factoría de oráculos convierte las decisiones de negocio en contratos ejecutables. Un experto puede revisar una tabla de decisiones con más facilidad que una colección de aserciones dispersas. Pero la tabla necesita una interpretación ejecutable conocida y probada. Dibujar un proceso BPMN no convierte su imagen en un motor que comprueba trazas.

La factoría de construcción recibe el contrato público y un alcance de escritura limitado. Produce código y pruebas de desarrollo. Esas pruebas son útiles para trabajar, aunque no sustituyen el conjunto de aceptación independiente. Si no permitimos ningún feedback, dificultamos la corrección; si exponemos todos los casos reservados, podemos convertir la evaluación en un ejercicio de memorización. El diseño debe decidir qué información comparte.

El verificador ejecuta o consume observaciones obtenidas de forma controlada, comprueba la identidad de los artefactos y emite un informe. En una arquitectura de producción, no debería aceptar sin más un fichero redactado por el candidato que afirme haber cumplido todas las propiedades.

![Figura 11.2 · Responsabilidades y evidencia vinculada. El constructor no modifica unilateralmente la baseline; separar carpetas en la demo no impone permisos de producción.](../../figures/es/c4_containers.png)

*Figura 11.2 · Responsabilidades y evidencia vinculada. El constructor no modifica unilateralmente la baseline; separar carpetas en la demo no impone permisos de producción.*

## Las fronteras que importan

| Componente | Puede escribir | Necesita leer | No debe controlar por sí solo |
|---|---|---|---|
| Investigación | Hallazgos y propuestas | Artefactos autorizados | Aprobación del comportamiento |
| Autoridad de dominio | Baseline y decisiones | Evidencia y discrepancias | Resultado de ejecuciones ajenas |
| Constructor | Candidato y tests propios | Contrato y feedback permitido | Oráculos protegidos |
| Verificador | Informes de ejecución | Baseline y artefactos fijados | Autorización de entrega |
| Servicio de entrega | Registro de publicación | Verificación y aprobación | Redefinición silenciosa de reglas |

Esta tabla es una propuesta de control, no una descripción de permisos ya implantados en la demo. Para hacerla efectiva se necesitan identidades, repositorios o rutas protegidas, runners aislados y puntos de ejecución que comprueben autorización. Separar carpetas en un ZIP ayuda a entender el diseño, pero no constituye una frontera de seguridad.

## Un expediente vinculante

El informe debería relacionar al menos el hash del candidato, la baseline, el evaluador, los datos de prueba y el entorno relevante. La aprobación de entrega debe referirse a ese conjunto. Si cambiamos el binario después de verificarlo, la evidencia anterior no acredita el nuevo artefacto.

La misma precaución se aplica a la política. Un cambio en una regla puede invalidar una aprobación aunque el código no haya cambiado. El gate debe poder detectar esa situación y solicitar una evaluación nueva.

Al principio no necesitamos desplegar cinco servicios. Un pipeline controlado y varios procesos pueden bastar para probar la separación lógica. La distribución física debe responder al riesgo y a la necesidad de aislamiento. Añadir agentes o contenedores sin una frontera clara multiplica componentes sin resolver la autoridad.

![Figura 11.3 · Del legado a la entrega: qué gate produce cada evidencia.](../../figures/es/gates.png)

*Figura 11.3 · Del legado a la entrega: qué gate produce cada evidencia.*

> **Añadir agentes o contenedores sin una frontera clara multiplica componentes sin resolver la autoridad.**

---

[← Capítulo 10 · TODM y el problema de aceptar lo que construimos](10-todm-y-el-problema-de-aceptar-lo-que-construimos.md) · [Índice](../README.md) · [Capítulo 12 · COBOL y C# deben acordar el significado →](12-cobol-y-c-deben-acordar-el-significado.md)
