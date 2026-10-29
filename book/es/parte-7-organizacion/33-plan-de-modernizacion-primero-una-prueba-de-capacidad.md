**Español** · [English](../../en/part-7-organization/33-modernization-plan-first-a-capability-test-then-a-bet.md)

[← Capítulo 32 · Una historia de migración: la cuenta que parecía fácil](32-una-historia-de-migracion-la-cuenta-que-parecia-facil.md) · [Índice](../README.md) · [Capítulo 34 · Medir lo que todavía no sabemos →](34-medir-lo-que-todavia-no-sabemos.md)

# Capítulo 33 · Plan de modernización: primero una prueba de capacidad, después una apuesta

> [!IMPORTANT]
> **Tesis del capítulo.** Una dirección no necesita promesas de que la IA lo convertirá todo. Necesita decisiones por etapas, inversión acotada y criterios explícitos para detenerse.

Una dirección no necesita promesas de que «la IA convertirá todo». Necesita decisiones por etapas, inversión acotada y criterios para detenerse. Propondría un **Discovery** que mida inventario, criticidad, dependencias, semántica de datos y capacidad observable. Después un **Pilot** con una costura seleccionada por riesgo y relevancia, no por facilidad para quedar bien en una demo. Después un **Parallel Run** con oráculos funcionales, operacionales y de rendimiento. Solo entonces un despliegue gradual y un retiro controlado del componente anterior.

Cada etapa cierra con tres preguntas. ¿Qué propiedad hemos demostrado? ¿Qué incertidumbre sigue abierta? ¿Qué riesgo asume la siguiente etapa? Un piloto puede concluir que mantener COBOL es mejor. También puede concluir que la migración es viable, pero necesita cambiar el modelo de datos. Un resultado negativo temprano es valioso: evita millones comprometidos sobre una hipótesis equivocada.

La gobernanza debe impedir el falso avance. No contaría líneas convertidas como progreso de negocio. Mediría capacidades liberadas de dependencias, reglas cubiertas, fallos encontrados, tiempo de cambio, coste por operación, deuda retirada y reducción real de riesgo. Para la IA incluiría porcentaje de propuestas aceptadas sin alteración, defectos detectados por oráculos independientes, coste de agentes y deriva de especificación. Ninguna métrica única resume una modernización.

Hay también una obligación de diseño organizacional: los especialistas COBOL no son un obstáculo que eliminar; son parte de la autoridad de dominio. Sus conocimientos deben transferirse al contrato de evidencia y al equipo que operará el nuevo sistema. El objetivo no es sustituir personas por agentes. Es evitar que el negocio dependa indefinidamente de conocimiento tácito imposible de auditar.

Es la inquietud que más se repitió en la Microsoft Frontier Transformation Week, donde participé como MVP y moderador: pasar de pilotos a resultados exige madurez, liderazgo, gobernanza e identidad, no más demos [47]. Una modernización COBOL es un caso extremo de esa misma distancia, porque el piloto puede salir bien y el cierre de mes no.

## Cuatro etapas con salida

| Etapa | Qué demuestra | Evidencia de salida | Puede concluir |
|---|---|---|---|
| Discovery | Qué hay, qué hace y cuánto trabajo soporta | Inventario con hashes, huella de carga, mapa transaccional | Que no merece la pena seguir |
| Piloto | Que una costura relevante se puede reconstruir y aceptar | Baseline aprobada, gate cualificado, candidato PASS | Que hay que cambiar el modelo de datos antes |
| Ejecución en paralelo | Equivalencia funcional, operacional y de capacidad con tráfico real | Informes G5, reconciliación, ensayo del peor día | Que la plataforma elegida no llega |
| Despliegue gradual y retiro | Que el legado ya no se necesita para esa capacidad | Ownership transferido, telemetría sin llamadas residuales | Que la capacidad está retirada |

![Figura 33.1 · Un plan con salidas: cada etapa puede concluir que no hay que seguir, y eso también es un resultado.](../../figures/es/plan.png)

*Figura 33.1 · Un plan con salidas: cada etapa puede concluir que no hay que seguir, y eso también es un resultado.*

> **Un resultado negativo temprano es valioso: evita comprometer millones sobre una hipótesis equivocada.**

---

[← Capítulo 32 · Una historia de migración: la cuenta que parecía fácil](32-una-historia-de-migracion-la-cuenta-que-parecia-facil.md) · [Índice](../README.md) · [Capítulo 34 · Medir lo que todavía no sabemos →](34-medir-lo-que-todavia-no-sabemos.md)
