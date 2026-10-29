**Español** · [English](../../en/part-2-archaeology-and-authority/09-from-the-agent-s-authority-to-the-rule-s-authority.md)

[← Capítulo 8 · El conocimiento del agente y el expediente del sistema](08-el-conocimiento-del-agente-y-el-expediente-del-sistema.md) · [Índice](../README.md) · [Parte III · Oráculos: el derecho a aceptar →](../parte-3-oraculos/README.md)

# Capítulo 9 · De la autoridad del agente a la autoridad de la regla

> [!IMPORTANT]
> **Tesis del capítulo.** Orquestar decide qué se ejecuta; gobernar decide quién puede aceptar una consecuencia. Una implementación puede ser correcta y no estar autorizada, y viceversa.

## Orquestar y gobernar responden a preguntas distintas

Un orquestador decide qué tarea se ejecuta a continuación, a quién se asigna y cómo se recupera un fallo. La gobernanza establece quién puede conceder permisos, qué alcance tienen y quién puede aceptar una consecuencia. Ambas funciones pueden colaborar, pero conviene distinguirlas.

En el artículo del Leviatán utilicé instituciones políticas como herramienta de razonamiento arquitectónico [1]. No atribuyo ciudadanía ni legitimidad moral a un proceso de software. Me interesa una cuestión práctica: qué límites permanecen cuando cambia el actor que ejerce una capacidad.

Un supervisor que escribe requisitos, modifica código, redefine pruebas y autoriza la entrega concentra todas las decisiones. Repartir esos pasos entre cuatro agentes no resuelve necesariamente el problema. Si comparten permisos y pueden corregir los criterios para acomodarlos al resultado, la separación existe solo en el diagrama.

La independencia que necesitamos tiene varias dimensiones. La fuente del resultado esperado debe poder cuestionar la implementación. El evaluador debe ejecutarse en condiciones conocidas. Los permisos deben impedir que el constructor cambie unilateralmente la referencia. La autorización debe corresponder al artefacto que se verificó.

## Un mandato concreto

«Eres el agente responsable de modernización» no define una autorización operativa suficiente. Un mandato útil podría permitir modificar una carpeta de candidatos, ejecutar un conjunto de herramientas en un entorno aislado y consumir un presupuesto determinado durante un intervalo. Podría prohibir modificar los contratos aprobados y publicar resultados como entregas de producción.

La restricción tiene que aplicarse donde se ejecuta la acción. Un mensaje que pide respetar el mandato ayuda a orientar al agente; no sustituye el control de escritura o la comprobación previa a una llamada crítica.

Cuando un agente delega, la nueva tarea debe quedar dentro de la autoridad que recibió. Si un constructor carece de capacidad para modificar la baseline, su subagente tampoco debería obtenerla por el simple hecho de llamarse revisor. El nombre de un rol no concede permisos.

La revocación también necesita una ruta efectiva. Un mandato caducado no debería seguir funcionando porque alguien conserva una credencial. En producción, esta exigencia afecta al proveedor de identidad, a los puntos de ejecución y a la comprobación inmediatamente anterior a una operación sensible.

Un mandato útil se puede escribir. Este ejemplo describe lo que el agente constructor puede hacer en el laboratorio. No es un control por sí mismo: es la descripción que el punto de ejecución —el sistema de ficheros, el repositorio, el runner, el proveedor de identidad— tiene que aplicar.

**Listado 9.1 · Un mandato acotado para el agente constructor** — *Ilustrativo*

```yaml
mandate:
  id: MND-2026-114
  scope: capability/fee-calculation
  grantedTo: agent/builder
  grantedBy: owner/payments-domain      # en producción, una identidad humana verificable
  validFrom: 2026-10-29T08:00:00Z
  validUntil: 2026-11-05T20:00:00Z
  allow:
    write: ["Candidate/**"]
    execute: ["dotnet build", "dotnet test", "python3 run.py"]
    budget: { tokens: 2000000, wallClockHours: 6 }
  deny:
    write: ["contracts/**", "Gate/**", "ci/**"]
    actions: ["publish", "approve-baseline", "delegate-beyond-scope"]
  revocation: "revocada en el proveedor de identidad; se comprueba antes de cada acción"
```

La línea más importante es `deny.write`. Si el constructor puede escribir en `contracts/` o en `Gate/`, el resto del mandato es literatura.

![Figura 9.1 · El mandato se aplica en el punto de ejecución, no en el prompt.](../../figures/es/mandate_seq.png)

*Figura 9.1 · El mandato se aplica en el punto de ejecución, no en el prompt.*

## Correcto no equivale a autorizado

Una implementación puede superar las pruebas y aun así no estar autorizada para publicarse. Quizá cambió el alcance, expiró la aprobación o se pretende desplegar un binario distinto. A la inversa, un equipo puede estar autorizado para trabajar y producir un resultado que incumple el contrato.

El laboratorio conserva esta separación. Incluye un caso en el que el veredicto de comportamiento es PASS y la entrega queda bloqueada por ausencia de mandato. La autorización es sintética; no hay una identidad empresarial detrás. El ejemplo enseña la lógica de la decisión, no una integración real de permisos.

Mantener las dos dimensiones visibles evita que el color verde de una prueba se convierta en una autorización implícita para cualquier acción posterior.

> **El nombre de un rol no concede permisos.**

---

[← Capítulo 8 · El conocimiento del agente y el expediente del sistema](08-el-conocimiento-del-agente-y-el-expediente-del-sistema.md) · [Índice](../README.md) · [Parte III · Oráculos: el derecho a aceptar →](../parte-3-oraculos/README.md)
