# Hoja de ruta del libro — próximas releases

[English](TODO.md) · **Español**

Responsable y autoridad editorial: **José María Flores Zazo · [jmfloreszazo.com](https://jmfloreszazo.com)**.
Fecha del plan: **8 de noviembre de 2026**. Baseline publicada: **v2026.11.08.1**.

> **Propuesta, no evidencia de ejecución.** Esta lista organiza trabajo futuro; no autoriza un despliegue, una release, acceso a clientes ni aceptación científica. Marcar una tarea solo después de conservar su verificación. Publicar por objetivos cumplidos, no por número de páginas. Fechas y versiones son tentativas.

Este es el plan de futuro. [ROADMAP.es.md](ROADMAP.es.md) conserva el registro histórico de la edición cerrada. La [hoja de ruta de experimentos](docs/EXPERIMENT_ROADMAP.md) y la [matriz de evidencia](docs/EVIDENCE.es.md) describen resultados ejecutados y límites. Este documento no reabre issues cerrados ni reactiva investigación congelada.

## 1. Próxima revisión editorial

**Objetivo:** cerrar y ordenar lo que ya existe. Versión candidata: `v2026.11.08.2`, sujeta a autorización de publicación.

- [ ] Integrar el cambio local preparado: el anexo G cierra siempre el libro; conservar letras y navegación F → H → G en ambas ediciones. Comprobar su estado real antes de aplicarlo otra vez.
- [ ] Contrastar la [revisión posterior a la reubicación](docs/reviews/2026-11-08-post-relocation/README.md) con `main`; durante la publicación se corrigieron verificadores, por lo que no deben repetirse hallazgos ya resueltos.
- [ ] Resolver la cronología Azure ambigua y la navegación de capítulos complementarios; clasificar cada hallazgo como corregido, aceptado o aplazado con motivo.
- [ ] Unificar las entradas para leer, ejecutar ejemplos, verificar evidencias y entender limitaciones.
- [ ] Inspeccionar visualmente los PDF definitivos de CI: portadas, índices, capítulos añadidos, tablas, listados, figuras y orden final de anexos.
- [ ] Escribir notas de release con cambios, pruebas y límites pendientes.

**Criterio de cierre:** ambas ediciones coherentes, controles aprobados, PDF candidatos inspeccionados y ningún hallazgo editorial importante sin disposición explícita.

**Fuera de alcance:** nuevos experimentos, frameworks o una reescritura general. Esta lista no publica la versión candidata.

## 2. Release de reproducción independiente

**Objetivo:** otra persona puede reproducir y cuestionar el libro sin nuestro ordenador.

- [ ] Validar el recorrido documentado desde un clon limpio: requisitos, versiones, comandos, duración orientativa y resultados esperados.
- [ ] Acordar la entrega autorizada de paquetes originales, con manifiestos localizables y backup separado. Un hash no proporciona los bytes.
- [ ] Separar verificación histórica de nueva ejecución; verificar no debe sobrescribir registros por defecto.
- [ ] Obtener un informe de reproducción por un tercero con entorno, comandos, fallos y diferencias respecto de la referencia.
- [ ] Publicar una matriz de soporte que distinga pruebas de herramientas en Windows/macOS de ejecución completa del laboratorio.

**Criterio de cierre:** un tercero reproduce el recorrido mínimo y verifica un paquete; las diferencias quedan conservadas y explicadas.

**Dependencias:** baseline entregable, entradas distribuibles y participante independiente. Otra ejecución del mismo asistente no es reproducción independiente.

## 3. Una capacidad de principio a fin

**Objetivo:** conectar los mecanismos existentes en un caso completo y comprensible de modernización.

- [ ] Elegir una capacidad pequeña, representativa y reversible: por ejemplo, consulta de saldo contabilizado, distinto explícitamente del saldo disponible.
- [ ] Identificar problema de negocio, alcance, exclusiones y roles responsables.
- [ ] Separar comportamiento observado del legado de política de negocio deseada.
- [ ] Vincular vocabulario, modelos de decisión/proceso y ADR a la capacidad.
- [ ] Establecer baseline y oráculo independiente, con casos negativos e incompletos.
- [ ] Implementar y evaluar el candidato contra los criterios congelados.
- [ ] Ejercitar integraciones, fronteras de datos y efectos externos pertinentes.
- [ ] Ensayar convivencia, reconciliación y corte/reversión cuando corresponda.
- [ ] Entregar un informe de resultados: correcto, rechazado, desconocido y no probado.

**Criterio de cierre:** el lector sigue una obligación desde su definición hasta la evidencia de su verificación, incluidos los fallos.

**Dependencia y clasificación:** un piloto real exige sistema identificado, acceso autorizado y responsables reales. Sin ellos se usan entradas públicas o sintéticas y se declara así. No inventar aprobación del cliente ni exigir análisis del COBOL como prerrequisito de cualquier capacidad.

## 4. TODM aplicada a decisiones y procesos

**Objetivo:** enseñar a mantener la verdad de negocio gobernada, no solo dibujar modelos.

- [ ] Demostrar reglas solapadas, precedencia y entradas incompletas con el perfil inspirado en DMN que realmente se admite.
- [ ] Documentar revisión manual, excepción y reanudación de un proceso; separar pasos ilustrativos de semántica ejecutable.
- [ ] Seguir un cambio de regla por baseline anterior/nueva, aprobación, pruebas y resultados. La aprobación sintética sigue siendo sintética.
- [ ] Incluir un ADR con una alternativa descartada y sus consecuencias.
- [ ] Contrastar `APPROVE` de negocio, veredicto técnico y autorización productiva.
- [ ] Demostrar coincidencia entre legado y candidato que incumple, aun así, la regla especificada independientemente.

**Criterio de cierre:** casos reproducibles positivos, negativos e inconclusos, con trazabilidad entre reglas, decisiones y evidencia.

**Fuera de alcance por defecto:** construir motores completos BPMN, DMN, CMMN, SBVR y OCL. Si se requiere semántica completa, seleccionar un motor existente, justificarlo mediante ADR y cualificar su configuración exacta. Reutilizar ejemplos antes de añadir duplicados.

## 5. Arquitectura bajo fallos

**Objetivo:** ampliar los fallos de proceso en un anfitrión a un ensayo distribuido bien delimitado.

- [ ] Separar generador, servicios y base de datos según la hipótesis y los dominios de fallo declarados.
- [ ] Prerregistrar carga, durabilidad, reintentos y criterios de recuperación.
- [ ] Ejecutar carga abierta con el denominador completo: respuestas, fallos, omisiones y operaciones ambiguas.
- [ ] Probar pérdida de instancia y recuperación; no llamar pérdida de nodo físico a perder un proceso/instancia sin demostrarlo.
- [ ] Reconciliar independientemente operaciones persistidas y efectos externos tras cada fallo.
- [ ] Conservar configuraciones, costes observados, repeticiones y limitaciones estadísticas.

**Criterio de cierre:** demostrar una propiedad de recuperación identificada en una topología registrada con un oráculo independiente.

**Dependencias:** infraestructura autorizada, gasto acotado, carga adecuada y aislamiento real de fallos. Sin referencia mainframe y contrato aprobado equivalente no existe comparación válida. Esa comparación no es necesaria para publicar este avance acotado.

## 6. Evaluación comparativa de agentes — E4

**Objetivo:** medir si el oráculo independiente y su cualificación mejoran los resultados.

| Variante | Evaluación |
|---|---|
| A | Pruebas producidas junto con el candidato |
| B | Oráculo independiente congelado |
| C | Oráculo independiente con cualificación por mutaciones |

- [ ] Definir tareas, presupuestos, selección, reglas de parada y puntuación antes de ejecutar.
- [ ] Establecer defectos y expectativas adjudicados de forma independiente.
- [ ] Ejecutar variantes comparables sin filtrar casos reservados a construcción o reparación.
- [ ] Registrar defectos aceptados, falsos rechazos, inconclusos, intentos, tokens y costes.
- [ ] Medir tiempo real de revisión humana y coste por cambio aceptado; no rellenar incógnitas con estimaciones inventadas.
- [ ] Analizar por tarea con incertidumbre justificada; conservar fallos e inconclusos.

**Criterio de cierre:** protocolo previo, conjunto de tareas justificado, observaciones completas y conclusiones proporcionales a la incertidumbre. Reproducir un candidato no añade una inferencia ni una tarea independiente.

**Dependencias:** adjudicación independiente, revisores y presupuesto de modelos autorizado. Ni un test verde ni un mandato sintético conceden autoridad de negocio G2/G6.

## 7. Más allá de COBOL, respaldado por ejecución

**Objetivo:** convertir parte del anexo H en una demostración concreta entre lenguajes.

- [ ] Elegir un lenguaje/runtime adicional, no diez.
- [ ] Mantener equivalentes la capacidad y el contrato observable.
- [ ] Ejercitar diferencias reales en decimales, overflow, fechas, codificaciones o concurrencia.
- [ ] Implementar el adaptador necesario y reutilizar el oráculo solo donde sigan siendo válidas sus suposiciones.
- [ ] Incluir un defecto que el contrato independiente detecte en el nuevo runtime.
- [ ] Explicar qué se reutilizó y qué exigió un diseño nuevo.

**Criterio de cierre:** ejecución conservada y reproducible en ambos entornos. No extrapolar un caso a todos los sistemas escritos en cualquiera de esos lenguajes.

**Dependencias:** contrato estable de la capacidad y runtime apropiado. Los primeros ejemplos de fronteras entre runtimes pueden preceder al estudio E4 completo; no todo punto es un prerrequisito estricto del siguiente.

## Prioridad recomendada y puerta común de publicación

**Cierre editorial → reproducción independiente → capacidad completa → TODM aplicada → fallos distribuidos → comparación E4 → evidencia en otro lenguaje.** Es un orden de prioridad, no una exigencia de acabar todo antes de publicar cualquier release. Cada entrega responde una pregunta y enumera las que siguen abiertas.

Para cada release:

- [ ] Español e inglés completos y sincronizados; anexo G de fuentes/alcance al final.
- [ ] CI del commit publicado aprobada, con jobs omitidos explícitamente justificados.
- [ ] Evidencias originales y fallos preservados; backup y condiciones de distribución documentados.
- [ ] PDF públicos comprobados, no solo vistas locales.
- [ ] Notas con requisitos de reproducción y limitaciones.
- [ ] Ningún resultado sintético promovido a aprobación de negocio, equivalencia de capacidad o aceptación productiva.
- [ ] Autor autoriza expresamente publicación, versión y merge; este plan no lanza una release automática.

**Siguiente inversión recomendada:** cerrar la revisión editorial y obtener reproducción independiente antes de añadir más herramientas o capítulos. Un piloto real de cliente es un trabajo separado, con sus propias fronteras de acceso y aprobación.
