# Acta editorial · Revisión narrativa del libro (10-11-2026)

[English](EDITORIAL_RESTRUCTURE_2026-11-10.md) · **Español** · [Libro](../book/es/README.md)

## Decisión de edición

El manuscrito debe poder leerse como el razonamiento de José María Flores Zazo, no como una sucesión de entregas de GitHub. Mantengo las afirmaciones técnicas, los resultados adversariales y sus límites. Separo **qué problema observo → qué decisión de arquitectura propongo → qué evidencia puede contradecirla → quién puede aceptarla**.

No he cambiado las versiones de código ni inventado experiencias productivas o pruebas inexistentes. Los ejemplos bancarios siguen marcados como sintéticos y las campañas de CI no son homologaciones de hardware, redes ATM ni mainframes.

## Recorrido que debe seguir el lector

1. **Parte I · Antes de traducir:** qué es el sistema y qué garantías aporta el entorno.
2. **Parte II · Arqueología:** cómo descubrir capacidades, hipótesis y autoridad de las fuentes.
3. **Parte III · TODM:** pasar de hipótesis a baseline, oráculo independiente y autorización.
4. **Parte IV · Patrones:** sustituir responsabilidades, no nombres de programas.
5. **Parte V · Capacidad:** confrontar hardware, concurrencia, red, recuperación y TCO.
6. **Parte VI · Laboratorio:** ejecutar, romper y verificar mecanismos concretos.
7. **Parte VII · Decisión:** convertir evidencia en SDLC, plan, go/no-go y retirada o convivencia.

He reescrito las aperturas de las siete partes en primera persona para unir los bloques. El capítulo 32 conserva el caso sintético de la cuenta, ahora con tres momentos diferenciados: demo, pruebas que cambian el diseño y responsabilidades extraídas.

## Consolidación y ubicación canónica

| Tema | Capítulo que asume la explicación | Cambio |
|---|---|---|
| Quién puede escribir los datos | Cap. 16 · Propiedad de los datos | Refuerza dueño de escritura, convivencia y retorno; deja de volver a explicar Outbox |
| Outbox, compensación y límites financieros | Cap. 18 · Distribuir sin romper la contabilidad | Explicación técnica canónica. Los caps. 16 y 21 remiten aquí |
| Cuándo elegir Event Sourcing, CQRS o Saga | Cap. 21 | Criterio de elección y condiciones de uso, sin duplicar el funcionamiento de las compensaciones |
| Qué aporta Orleans frente a lo que se debe probar | Cap. 19 | Se distingue garantía del runtime de aceptación del servicio; título sin promesa de trabajo abierto |
| Condiciones de salida y plan de inversión | Cap. 33 | Abre con el criterio de detenerse, no repite palabra por palabra la tesis |
| Decisión explícita de no migrar | Cap. 35 | Se justifica en un solo lugar, con condiciones revisables |
| Descomposición basada en capacidades | Capítulo complementario de la Parte II | Retirada la etiqueta heredada «borrador para revisión editorial»; el alcance sintético sigue declarado |

### Expediente experimental conservado

El [anexo I](../book/es/anexos/anexo-i-campanas-de-evidencia-y-limites.md) recoge la evidencia extensa que antes interrumpía el argumento:

- **I:** canales: advice tardío, reversos, H01–H07, TCP loopback y ACK retenido; antes en el capítulo complementario de canales, apartados 7–10.
- **II:** Orleans E2: C01, C04, C05/C06, partición larga, activaciones y prueba dirigida; antes en el capítulo 28.
- **III:** brownfield C2: control persistente, fallos direccionales y conciliación; antes en el capítulo 28.
- **IV:** diagnóstico B05, cohortes, límites de admisión y procedimiento de validación externa; antes en el capítulo 28.

Los originales se conservan con sus enlaces de evidencia. **E1/E2 no reciben PASS global**; **E3/E4 conservan su carácter de demostraciones acotadas no aceptadas**; G2/G6 permanecen bloqueados donde corresponde. La reubicación no promociona el valor científico de ningún ensayo.

## Voz editorial y límites

Busco la voz del arquitecto que enseña un caso, comprueba una afirmación y explica por qué elegiría o rechazaría un patrón. Predominan primera persona, decisiones condicionales y ejemplos reproducibles, sin atribuir al autor recuerdos, clientes, métricas o anécdotas no sustentadas.

No se han modificado el laboratorio, los scripts de pruebas ni las evidencias originales. Sí se ha actualizado el test de orden del libro para comprobar expresamente que el nuevo anexo I sigue al H; no se ha desactivado la validación.

## Revisión pendiente del autor

La estructura nueva es una **propuesta editorial en PR**, no una edición aprobada. Revisar en particular el capítulo 16 frente al 18, el diálogo entre 21 y canales, las siete aperturas de parte, el capítulo 32 y el peso del anexo I. Los PDF temporales de Actions sirven para revisar continuidad, paginación, diagramas y tablas. La fusión y la publicación de una release requieren una decisión separada.
