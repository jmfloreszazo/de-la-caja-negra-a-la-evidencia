**Español** · [English](../../en/part-7-organization/31-the-sdlc-as-part-of-the-migration-engine.md)

[← Capítulo 30 · Del laboratorio a un sistema que sigue operando](30-del-laboratorio-a-un-sistema-que-sigue-operando.md) · [Índice](../README.md) · [Capítulo 32 · Una historia de migración: la cuenta que parecía fácil →](32-una-historia-de-migracion-la-cuenta-que-parecia-facil.md)

# Capítulo 31 · El SDLC como parte del motor de migración

> [!IMPORTANT]
> **Tesis del capítulo.** Las buenas prácticas del SDLC juegan a nuestro favor cuando convierten incertidumbres en comprobaciones repetibles. Sería un error apagarlas justo cuando la IA nos permite generar código más rápido que nunca.

Una de las ironías de modernizar COBOL es que la organización puede disponer hoy de una disciplina de ingeniería mucho más rica que la que existía cuando se escribió el sistema. Sería un error apagar esa ventaja justo porque queremos que la IA genere código rápido. La infraestructura del SDLC moderno permite convertir la velocidad de los agentes en evidencias repetibles.

## Empezar antes de tener el sistema completo

Las buenas prácticas del SDLC juegan a nuestro favor cuando convierten incertidumbres en comprobaciones repetibles. Un contrato de entrada permite ejecutar el mismo caso contra dos implementaciones. Un ADR conserva por qué elegimos aislamiento o partición. Una prueba de regresión evita reintroducir una diferencia que ya habíamos resuelto.

Incorporaría objetivos de rendimiento y recuperación desde el descubrimiento. El marco Well-Architected de Microsoft recomienda establecer criterios medibles y probar de manera continua en condiciones representativas [28]. Para TODM, eso se traduce en oráculos de capacidad y recuperación además de los funcionales.

No fijaría los objetivos del proyecto copiando cifras del ejemplo. El dueño del servicio debe establecer el trabajo necesario, los tiempos, los estados permitidos durante un fallo y el presupuesto. Esos criterios necesitan aprobación y una versión, igual que una regla de comisión.

## Una cadena de evidencias durante el desarrollo

| Momento | Práctica | Evidencia útil para migración |
|---|---|---|
| Descubrimiento | Inventario y caracterización | Qué hace el sistema y dónde dudamos |
| Diseño | ADR de transacción y concurrencia | Qué garantías conserva cada frontera |
| Construcción | Tests, análisis y revisión | Defectos locales y cambios de contrato |
| Integración | Pruebas diferenciales y de historias | Equivalencia y conflictos concurrentes |
| Rendimiento | Carga, estrés y duración | Capacidad bajo condiciones fijadas |
| Resiliencia | Fallos y recuperación | Estado confirmado y tiempo de retorno |
| Entrega | Artefactos inmutables y autorización | Exactamente qué se verificó y entrega |
| Operación | Telemetría y reconciliación | Deriva, colas y reglas que deben revisarse |

Una prueba rápida puede ejecutarse con cada cambio. Las pruebas largas o costosas pueden ejecutarse por hitos y sobre infraestructura controlada. La frecuencia debe responder al riesgo de regresión y al coste. Ejecutar una carga ruidosa durante treinta segundos en cualquier runner no produce una puerta de capacidad fiable.

El repositorio debe versionar fuentes y especificaciones, controlar permisos y separar las ramas de propuesta de las baselines aprobadas. Los pipelines ejecutan parsing, linters, SAST, SBOM, pruebas de caracterización, tests de contrato, mutación, concurrencia, carga y verificación de artefactos. Los agentes pueden abrir PR y explicar diferencias, pero no deben poder rebajar los thresholds ni editar el verificador confiable para conseguir una build verde. Firmas, hashes y control de cambios son útiles para atribuir de manera razonable qué artefactos se evaluaron; no sustituyen una identidad humana verificable ni el juicio de negocio.

La observabilidad deja de ser un producto de operaciones y entra en el oráculo. Definiría trazas correladas para una transacción de negocio, métricas de latencia y bloqueo, cardinalidad controlada, reconciliación de saldos, errores de validación, lag de CDC y estado del outbox. Un defecto de modernización puede no manifestarse como excepción; puede ser una desviación estadística de importes, un aumento de reintentos o una cola que no termina antes de abrir el banco.

## La ficha de evidencia de cada pull request

Cada PR debería incluir una **ficha de evidencia**: cambio propuesto, reglas afectadas, fixtures añadidos, resultados de oráculos, cobertura, efectos de rendimiento, dependencias y criterio de rollback. La revisión humana debe centrarse en las diferencias materiales y en la integridad del proceso, no en aprobar miles de líneas generadas a ciegas.

Así es la plantilla que pondría en el repositorio. La escribe el autor del cambio —persona o agente— y la valida el pipeline, no la buena fe.

**Listado 31.1 · Plantilla de ficha de evidencia para un PR de modernización** — *Ilustrativo*

```markdown
## Ficha de evidencia
- Capacidad: fee-calculation · Mandato: MND-2026-114
- Reglas afectadas: R-FEE-003 (redondeo), sin cambios de baseline
- Baseline: contracts/cases.json @ 976d7127… (ancla verificada por CI, no por el autor)
- Candidato: sha256 del binario publicado por el build, no del local
- Oráculos: G5 funcional PASS 58/58 · controles G3 10/10 · bank invariants 6/6
- Rendimiento: sin cambios en la ruta crítica / ensayo de capacidad no requerido
- Divergencias autorizadas respecto del legado: ninguna
- Retorno: revertir el PR; sin migración de datos
- Preguntas abiertas: comportamiento con opciones de compilación de producción (EV-0142)
```

![Figura 31.1 · La baseline vive en su propia rama protegida: el candidato se integra cuando pasa G5 y G6, y un cambio de regla abre una revisión G7.](../../figures/es/gitgraph.png)

*Figura 31.1 · La baseline vive en su propia rama protegida: el candidato se integra cuando pasa G5 y G6, y un cambio de regla abre una revisión G7.*

Y así la integración continua que la respalda. Es la plantilla incluida en el laboratorio; está preparada para copiarse a `.github/workflows/`, pero no se ha activado en ningún repositorio.

**Listado 31.2 · ci/github-actions.yml del laboratorio** — *Plantilla · no activada*

```yaml
name: COBOL and transactional evidence
on: [push, pull_request, workflow_dispatch]
permissions:
  contents: read
jobs:
  acceptance:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'
      - run: sudo apt-get update && sudo apt-get install -y gnucobol3 libsqlite3-0
      - run: python3 tools/verify_offline.py
      - run: python3 walkthrough.py --auto --bank
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: execution-evidence
          path: results/
```

![Figura 31.2 · El pipeline como motor de migración: cada etapa deja evidencia y la autorización consume el artefacto exacto.](../../figures/es/pipeline.png)

*Figura 31.2 · El pipeline como motor de migración: cada etapa deja evidencia y la autorización consume el artefacto exacto.*

Fíjate en `permissions: contents: read` y en `if: always()`. El primero impide que el pipeline modifique el repositorio que evalúa. El segundo conserva la evidencia también cuando el gate bloquea, que es precisamente cuando más se necesita.

## Hacer que la optimización rinda cuentas

Cuando cambiamos un índice, el tamaño de lote, el aislamiento o el número de workers, la mejora debe pasar por dos preguntas: cuánto mejora la métrica y qué garantía conserva. Una caída de latencia conseguida desactivando confirmación durable no es una optimización equivalente si el contrato exigía esa durabilidad.

Versionaría el generador, la mezcla, los datos, las configuraciones y los criterios de aprobación. Conservaría resultados crudos, no solo la gráfica final. El expediente debe permitir distinguir una mejora de código de un cambio de infraestructura o de una base de datos ya caliente.

Los agentes pueden preparar pruebas, resumir discrepancias y proponer optimizaciones. El gate debe utilizar la evidencia observada y mantener fuera del alcance de escritura del constructor el criterio protegido. La autorización de entrega incluye también las condiciones bajo las que se ha medido la capacidad.

> **Los agentes pueden abrir PR y explicar diferencias. No deben poder rebajar los umbrales ni editar el verificador para conseguir una build verde.**

---

[← Capítulo 30 · Del laboratorio a un sistema que sigue operando](30-del-laboratorio-a-un-sistema-que-sigue-operando.md) · [Índice](../README.md) · [Capítulo 32 · Una historia de migración: la cuenta que parecía fácil →](32-una-historia-de-migracion-la-cuenta-que-parecia-facil.md)
