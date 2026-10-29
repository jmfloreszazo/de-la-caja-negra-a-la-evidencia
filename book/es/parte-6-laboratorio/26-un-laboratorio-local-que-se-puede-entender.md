**Español** · [English](../../en/part-6-lab/26-a-local-lab-you-can-understand.md)

[← Parte VI · El laboratorio: de la demo a la evidencia](README.md) · [Índice](../README.md) · [Capítulo 27 · Hacer que el error se vea →](27-hacer-que-el-error-se-vea.md)

# Capítulo 26 · Un laboratorio local que se puede entender

> [!IMPORTANT]
> **Tesis del capítulo.** Un COBOL real, un candidato C#, un gate independiente y un contrato fijado, ejecutados en local sin llamar a ningún modelo. La facilidad de reproducirlo debe ayudarnos a ver la dificultad real con más claridad.

> [!NOTE]
> En este repositorio el laboratorio está en la carpeta [`lab/`](../../../lab/README.md). Los comandos de este texto se ejecutan desde ella.

## El caso didáctico

El servicio recibe un registro de catorce caracteres. Los ocho primeros representan el importe en céntimos; los cinco siguientes, la tasa en puntos básicos; el último indica si el cliente está activo. Los valores admitidos son de cero a 99 999 999 céntimos, de cero a 10 000 puntos básicos y los estados Y o N.

Un cliente inactivo recibe REJECT con comisión cero. Un cliente activo recibe REVIEW cuando el importe supera 1 000 000 de céntimos; en el umbral exacto recibe APPROVE. La comisión se calcula para los clientes activos con el redondeo descrito en el capítulo [12](../parte-3-oraculos/12-cobol-y-c-deben-acordar-el-significado.md). Los registros de anchura fija que contienen caracteres inválidos o una tasa fuera del rango devuelven INVALID y comisión cero.

La política es ficticia y la elegimos porque permite estudiar prioridad de reglas, frontera de comparación, representación y redondeo dentro de un programa pequeño.

El contrato incluye 58 casos: catorce casos explícitos de frontera y comportamiento, cuarenta casos generados con semilla fija y cuatro registros inválidos de catorce caracteres. Son entradas de una única capacidad sintética, no 58 proyectos independientes ni una muestra de aplicaciones empresariales.

Este es el programa completo. Merece la pena leerlo despacio: en 40 líneas aparecen `REDEFINES`, un campo `COMP-3`, `ROUNDED`, `ON SIZE ERROR` y una prioridad de reglas que no es la que uno escribiría intuitivamente.

**Listado 26.1 · legacy/fee.cob** — *Ejecutado*

```cobol
identification division.
program-id. fee.
environment division.
configuration section.
repository. function all intrinsic.
data division.
working-storage section.
01 raw-input pic x(14).
01 request-fields redefines raw-input.
   05 amount-cents pic 9(8).
   05 rate-bps pic 9(5).
   05 customer-active pic x.
01 fee-cents pic 9(8) comp-3.
01 fee-display pic 9(8).
01 result-code pic x(7).
procedure division.
    accept raw-input
    move 0 to fee-cents fee-display
    evaluate true
      when amount-cents is not numeric
      when rate-bps is not numeric
      when customer-active not = 'Y' and not = 'N'
        move 'INVALID' to result-code
      when rate-bps > 10000
        move 'INVALID' to result-code
      when customer-active = 'N'
        move 'REJECT' to result-code
      when other
        compute fee-cents rounded = amount-cents * rate-bps / 10000
          on size error
            move 'INVALID' to result-code
          not on size error
            move fee-cents to fee-display
            if amount-cents > 1000000
              move 'REVIEW' to result-code
            else
              move 'APPROVE' to result-code
            end-if
        end-compute
    end-evaluate
    display trim(result-code) '|' fee-display
    goback.
```

## Qué significa ejecutar COBOL en local

GnuCOBOL proporciona el compilador y el entorno de ejecución utilizados en el laboratorio. El comando `cobc -x -free` genera un ejecutable a partir del fuente [10]. No lo presento como intérprete puro. El recorrido guiado oculta parte de la mecánica repetitiva, pero muestra el comando y el resultado para que el lector sepa qué está ocurriendo.

El paquete contiene el fuente COBOL, una implementación candidata C#, un gate independiente como proceso .NET, los casos fijados y un orquestador Python. Python lanza los programas y conserva las observaciones. La decisión de aceptación la calcula el gate .NET.

Hay una razón para mantener la demo sin llamadas a un modelo remoto: la reproducción del comportamiento no debe depender de que el proveedor responda igual o de disponer de una clave. El laboratorio fue construido con asistencia de IA, pero su ejecución no incluye un agente autónomo ni una integración de REA. Esas extensiones se describen más adelante como trabajo adicional.

## Dos formas de recorrerlo

La ejecución completa prepara los binarios, ejecuta casos y controles y guarda los informes. El modo guiado se detiene entre pasos: explica el registro, muestra el COBOL, ejecuta un ejemplo, muestra la traducción candidata y termina con los gates.

La ruta nativa necesita Python, el SDK .NET 10 y GnuCOBOL. El paquete incorpora además una receta para Podman que los reúne en una imagen y ejecuta el laboratorio sin red. Los comandos exactos están en el anexo [A](../anexos/anexo-a-un-laboratorio-que-pueda-contradecirnos.md) y en el README. Es importante distinguir la ejecución nativa verificada de una receta de contenedor que debe validarse en el equipo donde se vaya a construir.

Al terminar, el lector tiene archivos de resultados que puede abrir y comparar. No necesita confiar en una captura de pantalla. Puede cambiar una implementación, repetir el recorrido y examinar qué propiedad dejó de cumplirse.

## Qué hay en la caja

**Listado 26.2 · Estructura del laboratorio (en inglés)** — *Ejecutado*

```text
legacy/fee.cob              servicio COBOL sintético
Candidate/                  implementación C# con modos de mutación deliberados
Gate/                       evaluador .NET: PASS / FAIL / INCONCLUSIVE + mandato
Bank/                       transferencias SQL con idempotencia, doble asiento y outbox
contracts/                  58 casos aprobados y su ancla SHA-256
run.py · bank_test.py       equivalencia y controles · concurrencia y recuperación
walkthrough.py              recorrido guiado
cobol_local.py              compilar y ejecutar un fuente COBOL de consola
tools/                      verificación offline y simulación de omisión coordinada
examples/                   laboratorio de calentamiento: oráculo a tres bandas
risk-catalog/               R001–R100
reference-results/          evidencia de la ejecución de referencia, sin modificar
Containerfile · scripts/    receta Podman y lanzadores
```

![Figura 26.1 · El laboratorio dentro de un contenedor Podman sin red: quién ejecuta qué y quién decide.](../../figures/es/lab_c4.png)

*Figura 26.1 · El laboratorio dentro de un contenedor Podman sin red: quién ejecuta qué y quién decide.*

## Antes de compilar nada

Hay comprobaciones que no necesitan ni GnuCOBOL ni .NET, y conviene hacerlas primero. `tools/verify_offline.py` comprueba el ancla de la baseline, recalcula los 58 resultados esperados con una tercera implementación de la política escrita, informa de qué fuentes son idénticos byte a byte a los de la ejecución de referencia y vuelve a pasar el oráculo contable sobre las bases persistidas.

**Listado 26.3 · Verificación offline (salida abreviada)** — *Ejecutado*

```text
[1] baseline anchor ............ OK
[2] independent policy ......... 58/58 cases agree
[3] provenance against the reference run (29 Oct 2026, native Linux):
    Bank/Program.cs                  identical
    Candidate/Program.cs             identical
    Gate/Program.cs                  identical
    legacy/fee.cob                   identical
    run.py                           identical
    walkthrough.py                   changed since reference run
[4] ledger oracle on reference databases:
    acceptance.db            PASS                                     as expected
    negative-control.db      REJECTED balancedPostings,twoPostingsPerCommit,projectionAgrees as expected

VERIFY: PASS (offline checks only; run.py and bank_test.py still require GnuCOBOL and .NET 10)
```

Si la implementación independiente discrepara de un caso, pararía ahí. Significaría que el contrato o mi lectura del contrato están mal, y ninguna cantidad de C# arreglaría eso.

> **No necesitas confiar en una captura de pantalla. Puedes cambiar una línea, repetir el recorrido y ver qué propiedad deja de cumplirse.**

---

[← Parte VI · El laboratorio: de la demo a la evidencia](README.md) · [Índice](../README.md) · [Capítulo 27 · Hacer que el error se vea →](27-hacer-que-el-error-se-vea.md)
