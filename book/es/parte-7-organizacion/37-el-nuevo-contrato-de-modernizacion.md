**Español** · [English](../../en/part-7-organization/37-the-new-modernization-contract.md)

[← Capítulo 36 · Cien riesgos para elegir patrones con criterio](36-cien-riesgos-para-elegir-patrones-con-criterio.md) · [Índice](../README.md) · [Epílogo →](../epilogo.md)

# Capítulo 37 · El nuevo contrato de modernización

> [!IMPORTANT]
> **Tesis del capítulo.** Antes de mover una capacidad COBOL, cualquier responsable técnico debería poder firmar siete cláusulas, y cada una debería poder demostrarse con un artefacto concreto.

Para cerrar, propongo un contrato sencillo que debería poder firmar cualquier responsable técnico antes de mover una capacidad COBOL. **Primero**: tenemos evidencia identificable de lo que hace el sistema. **Segundo**: sus invariantes y excepciones están registrados en una baseline aprobada. **Tercero**: sabemos qué responsabilidades antiguas necesitan un mecanismo nuevo y por qué. **Cuarto**: las implementaciones se someten a oráculos independientes, incluyendo concurrencia y fallos. **Quinto**: el entorno seleccionado supera una prueba de carga realista, con coste y capacidad documentados. **Sexto**: existe una transición controlada de ownership de datos, soporte y recuperación. **Séptimo**: sabemos qué parte del legado retiramos y cómo verificaremos que ya no se necesita.

La ingeniería asistida por IA cambia radicalmente la velocidad a la que podemos investigar, proponer y construir. REA muestra el valor de la evidencia en ingeniería inversa; quienes piden prudencia advierten contra la pérdida del conocimiento del negocio; TODM propone separar autoridad y aceptación; los patrones arquitectónicos permiten reconstituir garantías en entornos diferentes. El resultado es una disciplina, no una herramienta mágica.

Hay una frase que resume mi posición: **la modernización 1:1 puede ser un puente, pero nunca deberíamos confundir el puente con la ciudad a la que queremos llegar**. Si después de cambiar el lenguaje seguimos desplegando igual, bloqueando igual, acumulando dependencias igual y sin saber demostrar qué hace el sistema, no lo hemos modernizado. Solo hemos cambiado el idioma de sus problemas.

## El contrato, con su evidencia

| Cláusula | Artefacto que la demuestra | Dónde aparece en el libro |
|---|---|---|
| Evidencia identificable de lo que hace el sistema | Inventario con hashes y EvidenceItems | Capítulos [6](../parte-2-arqueologia-y-autoridad/06-rea-y-la-arqueologia-que-deja-rastro.md) y [7](../parte-2-arqueologia-y-autoridad/07-legacy-archaeology-asistida-por-agentes.md) |
| Invariantes y excepciones en una baseline aprobada | Baseline versionada con ancla protegida | Capítulos [10](../parte-3-oraculos/10-todm-y-el-problema-de-aceptar-lo-que-construimos.md) y [12](../parte-3-oraculos/12-cobol-y-c-deben-acordar-el-significado.md) |
| Responsabilidades antiguas con mecanismo nuevo justificado | Matriz de sustitución y ADR | Capítulo [13](../parte-4-patrones/13-antes-de-elegir-un-patron-identifica-el-contrato.md) y anexo [D](../anexos/anexo-d-decisiones-de-arquitectura.md) |
| Oráculos independientes, también para concurrencia y fallos | Gate cualificado y oráculo contable | Capítulos [17](../parte-4-patrones/17-de-los-locks-del-mainframe-al-control-explicito-de.md), [27](../parte-6-laboratorio/27-hacer-que-el-error-se-vea.md) y [28](../parte-6-laboratorio/28-transferencias-bloqueos-y-fallos-en-local.md) |
| Prueba de carga realista con coste documentado | Contrato de rendimiento rellenado y aprobado | Capítulos [22](../parte-5-capacidad/22-los-mips-no-caben-en-una-conversion-de-vcpu.md) a [25](../parte-5-capacidad/25-azure-o-una-maquina-enorme-en-el-cliente.md) |
| Transición controlada de datos, soporte y recuperación | Registro de ownership y plan de retorno ensayado | Capítulos [16](../parte-4-patrones/16-la-propiedad-de-los-datos.md) y [30](30-del-laboratorio-a-un-sistema-que-sigue-operando.md) |
| Retiro verificado del legado | Telemetría sin dependencias residuales | Capítulos [14](../parte-4-patrones/14-strangler-fig-cambiar-el-borde-antes-que-el-corazon.md) y [33](33-plan-de-modernizacion-primero-una-prueba-de-capacidad.md) |

> **Si después de cambiar el lenguaje seguimos desplegando igual, bloqueando igual y sin saber demostrar qué hace el sistema, no lo hemos modernizado. Solo hemos cambiado el idioma de sus problemas.**

---

[← Capítulo 36 · Cien riesgos para elegir patrones con criterio](36-cien-riesgos-para-elegir-patrones-con-criterio.md) · [Índice](../README.md) · [Epílogo →](../epilogo.md)
