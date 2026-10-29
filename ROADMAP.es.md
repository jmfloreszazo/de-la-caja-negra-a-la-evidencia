# Hoja de ruta abierta

[English](ROADMAP.md) · **Español**

Trabajo que el libro deja planteado y que la comunidad puede hacer avanzar. Cada línea indica su etiqueta. Los issues iniciales ya están creados con `scripts/setup_github.sh` y agrupados en el hito «v2026.11 · Revisión comunitaria».

## Validar lo que no se pudo validar

| Tarea | Por qué importa | Etiqueta |
|---|---|---|
| Construir la imagen Podman en Linux, macOS y Windows y compartir el informe | La CI valida la receta; lo que cuenta son las máquinas reales | `reproduction`, `good first issue` |
| Ejecutar el laboratorio completo en CI y comparar con la ejecución de referencia | Sustituye una ejecución local por una evidencia pública y repetible | `lab` |
| Compilar los listados *Ilustrativo* en un proyecto de ejemplo y marcar los que pasen a *Verificado* | Hoy son fragmentos de razonamiento; algunos merecen ser código | `lab`, `good first issue` |

## Experimentos diseñados y no ejecutados

Descritos en [`lab/docs/EXPERIMENT_PROTOCOL.md`](lab/docs/EXPERIMENT_PROTOCOL.md).

| Experimento | Pregunta | Etiqueta |
|---|---|---|
| E1 · Motor SQL con bloqueo por fila | ¿Se sostienen los controles con víctimas de deadlock, write skew y agotamiento del pool? | `experiment` |
| E2 · Actores que coordinan, ledger que confirma | ¿Qué aporta Orleans frente a E1 con cuentas uniformes, sesgadas y una cuenta caliente? | `experiment` |
| E3 · Azure, local e híbrido con el mismo contrato | ¿Qué configuración cumple el contrato con una unidad perdida, y a qué coste? | `experiment` |
| E4 · Agentes bajo el gate | ¿Reduce el oráculo independiente los defectos aceptados frente a las pruebas del propio agente? | `experiment` |

## Laboratorio: siguientes katas

- Convertir el codec COMP-3 del capítulo 15 en un módulo con sus vectores de prueba.
- Añadir un adaptador EBCDIC con CCSID explícito y casos de ordenación.
- Ampliar el contrato con importes negativos y una matriz de opciones de compilación.
- Portar el oráculo contable a .NET para tener dos verificadores independientes.

## Libro

- Mantener sincronizadas las ediciones en español e inglés (`scripts/check.py` lo exige) y acoger otros idiomas con la misma estructura.
- Ampliar el glosario y el catálogo de riesgos (R101 en adelante) con evidencia real.
- Casos reales anonimizados, con permiso explícito y sin cifras de cliente identificables.
