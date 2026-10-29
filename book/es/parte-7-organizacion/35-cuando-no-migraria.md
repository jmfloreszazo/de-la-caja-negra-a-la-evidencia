**Español** · [English](../../en/part-7-organization/35-when-i-would-not-migrate.md)

[← Capítulo 34 · Medir lo que todavía no sabemos](34-medir-lo-que-todavia-no-sabemos.md) · [Índice](../README.md) · [Capítulo 36 · Cien riesgos para elegir patrones con criterio →](36-cien-riesgos-para-elegir-patrones-con-criterio.md)

# Capítulo 35 · Cuándo NO migraría

> [!IMPORTANT]
> **Tesis del capítulo.** Conservar el mainframe, mejorarlo o combinarlo con sistemas nuevos son decisiones legítimas si los datos lo justifican. Una arquitectura híbrida bien gobernada puede ser más moderna que una reescritura total imprudente.

Hay sistemas que cumplen su función, tienen carga estable, coste asumible, soporte suficiente y garantías bien conocidas. Si la modernización no aporta valor funcional, reducción comprobable de riesgo o una economía razonable, la mejor decisión puede ser seguir en mainframe y mejorar observabilidad, automatización, documentación y exposición de capacidades. Una arquitectura híbrida bien gobernada puede ser más moderna que una reescritura total imprudente.

No migraría un ledger crítico sin acceso a perfiles operativos y sin un entorno donde ejecutar pruebas de equivalencia y recuperación. No haría un cutover irreversible mientras convivan escritores no inventariados. No aceptaría un SLA porque un benchmark sintético obtuvo un TPS llamativo. No separaría por microservicios un proceso cuya atomicidad no podemos recuperar. No utilizaría actores para simular una transacción entre dominios y llamarla segura. Y no confiaría la aceptación de una baseline a la misma IA que generó el candidato.

No se trata de conservadurismo tecnológico. Es una disciplina de decisiones reversibles. La modernización buena es la que permite aprender sin poner de rehén al sistema que paga nóminas, liquida operaciones o protege pólizas.

## Sin dogmatismo

| Tiene sentido migrar una capacidad cuando | No lo tiene cuando |
|---|---|
| Hay un objetivo de negocio medible que el sistema actual impide | El único argumento es la antigüedad del lenguaje |
| Se puede construir un oráculo de comportamiento y de capacidad | No se puede definir qué es «correcto» de forma verificable |
| Existe acceso a perfiles operativos y a un entorno de pruebas | No hay huella de carga ni forma de ensayar la recuperación |
| La propiedad de los datos se puede transferir con un protocolo | Conviven escritores no inventariados |
| La atomicidad necesaria se conserva en el destino | Habría que fragmentar una transacción que el negocio necesita atómica |
| El coste de verificar es asumible frente al beneficio | La verificación cuesta más que el problema que resuelve |

> **No se trata de conservadurismo tecnológico. Es una disciplina de decisiones reversibles.**

---

[← Capítulo 34 · Medir lo que todavía no sabemos](34-medir-lo-que-todavia-no-sabemos.md) · [Índice](../README.md) · [Capítulo 36 · Cien riesgos para elegir patrones con criterio →](36-cien-riesgos-para-elegir-patrones-con-criterio.md)
