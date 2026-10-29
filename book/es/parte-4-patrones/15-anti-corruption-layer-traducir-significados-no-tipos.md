**Español** · [English](../../en/part-4-patterns/15-anti-corruption-layer-translate-meanings-not-types.md)

[← Capítulo 14 · Strangler Fig: cambiar el borde antes que el corazón](14-strangler-fig-cambiar-el-borde-antes-que-el-corazon.md) · [Índice](../README.md) · [Capítulo 16 · La propiedad de los datos →](16-la-propiedad-de-los-datos.md)

# Capítulo 15 · Anti-Corruption Layer: traducir significados, no tipos

> [!IMPORTANT]
> **Tesis del capítulo.** Un `PIC S9(11)V99 COMP-3` no es un `decimal`: es escala, representación, signo y restricciones. La capa anticorrupción impide que esas decisiones contaminen el modelo nuevo y obliga a declararlas.

Un `PIC S9(11)V99 COMP-3` no es simplemente un `decimal`. El tipo expresa escala, representación, signo y restricciones. Un registro EBCDIC puede tener collations, overpunch y campos redefinidos. Una comparación lexicográfica que funcionaba con una ordenación puede cambiar al pasar a Unicode. Y un `REDEFINES` representa varias interpretaciones del mismo almacenamiento, a menudo determinadas por un discriminador externo.

El Anti-Corruption Layer (ACL) evita que esas decisiones penetren en el modelo moderno. Sitúo aquí adaptadores de codificación, parsers de registros, validadores de escala, conversores de fechas, decodificación de packed decimal y mapeo de códigos de error. Al otro lado aparecen conceptos de negocio explícitos: `Money`, `AccountId`, `EffectiveDate`, `Posting`, `PolicyStatus`. La transformación debe ser bidireccional y verificable cuando el viejo y el nuevo conviven.

![Figura 15.1 · La capa anticorrupción como modelo de clases: los codecs traducen bytes, la cuarentena recoge lo inválido y el dominio solo ve conceptos de negocio.](../../figures/es/acl_class.png)

*Figura 15.1 · La capa anticorrupción como modelo de clases: los codecs traducen bytes, la cuarentena recoge lo inválido y el dominio solo ve conceptos de negocio.*

No llamaría «normalización» a cambiar silenciosamente un comportamiento histórico. Si el sistema original redondea cada línea antes de sumar y el nuevo suma antes de redondear, las operaciones no son equivalentes aunque ambos utilicen decimal exacto. Si la nueva regla es mejor, lo correcto es aprobar un **cambio de negocio intencional** y documentarlo como divergencia autorizada. Los oráculos de equivalencia no deben convertirse en una prisión que conserve errores por inercia, pero tampoco en una excusa para corregirlos sin control.

Los agentes pueden proponer mapeos a partir del copybook y de ejemplos, pero las conversiones críticas deben ejecutarse con bibliotecas deterministas y pruebas límite. Cada campo necesita contrato: bytes originales, interpretación, rango, nulos, signo, escala y política ante datos inválidos.

Microsoft documenta este patrón como una fachada o capa de adaptación entre subsistemas que no comparten semántica, y recuerda dos cosas que conviene no olvidar en una migración: puede convertirse en un punto único de fallo, y hay que decidir desde el principio si será permanente o se retirará cuando termine la transición [38].

## Un codec que no adivina

El ejemplo más pequeño de ACL que merece la pena escribir es el decodificador de decimal empaquetado. Cada byte guarda dos dígitos, salvo el último, que guarda un dígito y el signo. No hay punto decimal: la escala viene del copybook.

**Listado 15.1 · Decodificación explícita de COMP-3 con escala del copybook** — *Ilustrativo · lógica verificada*

```csharp
public static decimal DecodePacked(ReadOnlySpan<byte> field, int scale)
{
    if (field.IsEmpty || scale < 0 || scale > 18)
        throw new ArgumentException("Campo o escala inválidos");

    long digits = 0;
    for (int i = 0; i < field.Length; i++)
    {
        digits = checked(digits * 10 + Digit(field[i] >> 4, i));
        if (i < field.Length - 1)
            digits = checked(digits * 10 + Digit(field[i] & 0x0F, i));
    }

    bool negative = (field[^1] & 0x0F) switch
    {
        0x0D or 0x0B => true,
        0x0C or 0x0F or 0x0A or 0x0E => false,
        _ => throw new FormatException("Nibble de signo inválido")
    };

    decimal value = digits;
    for (int s = 0; s < scale; s++) value /= 10m;   // exacto: decimal es base 10
    return negative ? -value : value;

    static int Digit(int nibble, int index) => nibble <= 9
        ? nibble
        : throw new FormatException($"Nibble de dígito inválido en el byte {index}");
}
```

La lógica de este codec está comprobada con una implementación gemela independiente sobre los vectores de la tabla; el código C# es ilustrativo.

| Bytes (hex) | Copybook | Resultado esperado |
|---|---|---|
| `12 34 5C` | `PIC S9(3)V99 COMP-3` | 123.45 |
| `12 34 5D` | `PIC S9(3)V99 COMP-3` | −123.45 |
| `01 23 45 6D` | `PIC S9(5)V99 COMP-3` | −1234.56 |
| `99 9F` | `PIC 9(3) COMP-3` | 999 (signo F, sin signo) |
| `00 0C` | `PIC S9(3) COMP-3` | 0 |
| `1A 3C` | cualquiera | error: nibble de dígito inválido |
| `12 37` | cualquiera | error: nibble de signo inválido |

Las dos últimas filas son las importantes. Un codec que «tolera» bytes inválidos convirtiéndolos en cero ha tomado una decisión de negocio sin que nadie la apruebe. IBM documenta que incluso recompilar con una versión nueva de Enterprise COBOL puede hacer visibles datos numéricos inválidos que llevaban años ahí [30]. El ACL es el sitio donde esos datos se detectan, se ponen en cuarentena y se cuentan, no donde se esconden.

> **No llamaría normalización a cambiar silenciosamente un comportamiento histórico.**

---

[← Capítulo 14 · Strangler Fig: cambiar el borde antes que el corazón](14-strangler-fig-cambiar-el-borde-antes-que-el-corazon.md) · [Índice](../README.md) · [Capítulo 16 · La propiedad de los datos →](16-la-propiedad-de-los-datos.md)
