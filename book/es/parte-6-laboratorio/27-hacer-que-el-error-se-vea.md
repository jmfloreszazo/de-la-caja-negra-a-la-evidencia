**Español** · [English](../../en/part-6-lab/27-making-the-error-visible.md)

[← Capítulo 26 · Un laboratorio local que se puede entender](26-un-laboratorio-local-que-se-puede-entender.md) · [Índice](../README.md) · [Capítulo 28 · Transferencias, bloqueos y fallos en local →](28-transferencias-bloqueos-y-fallos-en-local.md)

# Capítulo 27 · Hacer que el error se vea

> [!IMPORTANT]
> **Tesis del capítulo.** Tres defectos sembrados, cuatro tipos de evidencia incompleta, una coincidencia engañosa y una entrega sin mandato. Cada uno produce un veredicto distinto, y cada veredicto deja un fichero que otra persona puede abrir.

## Una implementación correcta dentro del alcance

Primero ejecutamos el programa COBOL y el candidato C# sobre las mismas entradas. Cada salida se contrasta con el resultado esperado fijado en el contrato. Este tercer elemento es importante: la coincidencia entre dos programas no excluye que ambos estén equivocados.

El gate no se limita a contar filas iguales. Comprueba que existan los casos esperados y que las observaciones tengan las identidades correspondientes. La falta de un caso o de una salida produce INCONCLUSIVE. Una discrepancia observada produce FAIL. Un conjunto incompleto no puede ganar por haber omitido precisamente el ejemplo que fallaba.

La baseline se comprueba frente a un digest. En la demo, ese digest permanece en un archivo local y sirve para detectar modificaciones respecto de la referencia utilizada. No demuestra aprobación humana ni resistencia frente a alguien que pueda modificar ambas piezas. Su función pedagógica es mostrar el enlace; la arquitectura de producción debe proteger el anclaje.

El corazón del gate cabe en unas líneas. Cada observación se compara con la expectativa aprobada, nunca solo con la otra implementación; la ausencia y la contradicción producen veredictos distintos; y la autorización se evalúa aparte.

**Listado 27.1 · Gate/Program.cs: tres veredictos y una autorización separada** — *Ejecutado*

```csharp
foreach(var key in new[]{"legacy","candidate"})
{
    if(!row.TryGetProperty(key,out var value) || value.ValueKind!=JsonValueKind.String)
    {missing=true;findings.Add(id+": missing "+key);continue;}
    if(value.GetString()!=c.GetProperty("expected").GetString())
    {failed=true;findings.Add(id+": "+key+" violates contract");}
}
// ...
verdict=failed ? "FAIL" : missing ? "INCONCLUSIVE" : "PASS";
// ...
var release=verdict=="PASS" && authority ? "SIMULATED_ALLOW" : "BLOCK";
```

![Figura 27.1 · La lógica de decisión de Gate/Program.cs: la contradicción pesa más que la ausencia, y la autorización se evalúa aparte.](../../figures/es/gate_flow.png)

*Figura 27.1 · La lógica de decisión de Gate/Program.cs: la contradicción pesa más que la ausencia, y la autorización se evalúa aparte.*

## Tres mutaciones del candidato

La primera mutación cambia el redondeo al par. El caso de 25 céntimos permite detectar la diferencia. El código puede parecer razonable a una revisión rápida, porque usa una operación estándar de .NET. El contrato hace visible por qué esa operación no corresponde a esta regla.

La segunda eleva el umbral de revisión de 1 000 000 a 1 200 000 céntimos. El valor inmediatamente superior al umbral correcto y el caso situado entre ambos límites exponen el defecto. Probar únicamente importes muy pequeños o muy grandes dejaría pasar la modificación.

La tercera omite el rechazo de clientes inactivos. Aquí importa el orden de decisión. No queremos que el programa calcule una comisión y apruebe una operación que debía rechazarse antes. El verificador compara la salida completa, incluyendo estado e importe.

Estos controles están sembrados de forma deliberada y son conocidos por quien ha construido el laboratorio. Sirven para demostrar el mecanismo de detección. No deben describirse como defectos descubiertos en un producto real ni como una evaluación ciega de productividad.

Las tres mutaciones viven en el mismo candidato y se activan por argumento. La del redondeo es la más instructiva, porque a primera vista no parece un error:

**Listado 27.2 · Candidate/Program.cs: los puntos donde se siembran los defectos** — *Ejecutado*

```csharp
    if (line[13]=='N' && mode!="approve-inactive")
    { Console.WriteLine("REJECT|00000000"); continue; }
    var fee=decimal.Round(amount*(decimal)rate/10000m,0,
        mode=="round-even" ? MidpointRounding.ToEven : MidpointRounding.AwayFromZero);
    var threshold=mode=="wrong-threshold" ? 1200000 : 1000000;
```

## La igualdad también puede engañar

Otro control modifica las dos observaciones para que coincidan en un resultado incorrecto. Una comparación exclusiva COBOL–C# lo aceptaría. Nuestro gate lo rechaza porque contrasta ambas observaciones con la expectativa normativa del caso.

Este control no demuestra que el capturador sea incorruptible. Al contrario, hace visible su importancia. En producción necesitamos saber quién obtuvo la observación, qué ejecutable lanzó y qué transformaciones aplicó. Si el constructor puede fabricar toda la evidencia, una baseline correcta no basta.

Finalmente retiramos el mandato sintético. Los resultados funcionales siguen siendo correctos, pero la entrega queda bloqueada. El lector puede observar dos afirmaciones simultáneas: el candidato cumple las comprobaciones y no tiene permiso para entregarse bajo esa configuración.

Estas son dos salidas reales del gate en la ejecución de referencia. La primera bloquea el redondeo al par en el caso C003. La segunda es la coincidencia engañosa: los dos programas dicen lo mismo, y los dos se equivocan.

**Listado 27.3 · reference-results/round-even-gate.json y equal-but-wrong-gate.json** — *Ejecutado*

```json
{ "verdict": "FAIL", "authority": "DEMO_ONLY", "release": "BLOCK",
  "findings": [ "C003: candidate violates contract" ], "exitCode": 2 }

{ "verdict": "FAIL", "authority": "DEMO_ONLY", "release": "BLOCK",
  "findings": [ "C003: legacy violates contract", "C003: candidate violates contract" ],
  "exitCode": 2 }
```

Y esta es la entrega correcta pero no autorizada: comportamiento PASS, autoridad denegada, entrega bloqueada, código de salida 4.

**Listado 27.4 · reference-results/no-mandate-gate.json** — *Ejecutado*

```json
{ "verdict": "PASS", "authority": "DENY", "release": "BLOCK", "findings": [], "exitCode": 4 }
```

## Qué podemos concluir

Los resultados acreditan que el laboratorio detecta los defectos y ausencias incluidos, con las versiones ejecutadas. No prueban equivalencia universal, seguridad de un pipeline empresarial ni capacidad autónoma de modernización. Tampoco miden cuánto trabajo ahorró la IA.

Es una conclusión más pequeña que una promesa de migración automática. También es una conclusión que otra persona puede intentar reproducir y refutar.

## Rómpelo tú

El laboratorio está hecho para que lo contradigas. Cuatro experimentos de cinco minutos, con su resultado esperado:

| Cambio | Resultado esperado | Qué enseña |
|---|---|---|
| Cambiar `1000000` por `999999` en el candidato | FAIL en C008 | El umbral exacto es un caso, no un detalle |
| Eliminar la comprobación `rate>10000` | FAIL en C055 | La validación también es comportamiento |
| Añadir un caso a `cases.json` sin actualizar el ancla | `run.py` se niega a empezar | La baseline tiene identidad |
| Renombrar una variable del candidato | PASS | El gate juzga comportamiento, no estilo |

> **Es una conclusión más pequeña que una promesa de migración automática. También es una conclusión que otra persona puede reproducir y refutar.**

---

[← Capítulo 26 · Un laboratorio local que se puede entender](26-un-laboratorio-local-que-se-puede-entender.md) · [Índice](../README.md) · [Capítulo 28 · Transferencias, bloqueos y fallos en local →](28-transferencias-bloqueos-y-fallos-en-local.md)
