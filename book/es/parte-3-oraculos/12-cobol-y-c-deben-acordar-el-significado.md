**Español** · [English](../../en/part-3-oracles/12-cobol-and-c-must-agree-on-meaning.md)

[← Capítulo 11 · La arquitectura de una modernización verificable](11-la-arquitectura-de-una-modernizacion-verificable.md) · [Índice](../README.md) · [Parte IV · Patrones que sustituyen responsabilidades, no sintaxis →](../parte-4-patrones/README.md)

# Capítulo 12 · COBOL y C# deben acordar el significado

> [!IMPORTANT]
> **Tesis del capítulo.** Usar `decimal` es el comienzo. La escala, el momento del redondeo, el desempate, el rango y la memoria compartida forman parte del contrato, y una demostración con valores redondos no los pone a prueba.

## El tipo correcto es solo el comienzo

Una migración puede usar `decimal` y seguir calculando mal. La escala, el momento del redondeo, el rango del campo y el tratamiento del desbordamiento forman parte del comportamiento. Si redondeamos cada línea y después sumamos, podemos obtener un resultado distinto de sumar primero y redondear al final.

La documentación de .NET indica que `Math.Round` utiliza por defecto el redondeo al par en las sobrecargas que no especifican otro modo [8]. Por tanto, escribir `Round` sin más no es una decisión neutral cuando intentamos conservar un comportamiento existente.

En COBOL, las cláusulas de redondeo y de error de tamaño influyen en el resultado que se almacena. IBM documenta que, cuando se especifica ROUNDED, el redondeo precede a la comprobación de SIZE ERROR, y que ON SIZE ERROR cambia el tratamiento del resultado fuera de rango [9]. El dialecto y las opciones del compilador deben registrarse; no extrapolaría una prueba GnuCOBOL a todos los runtimes.

En el laboratorio reducimos el dominio a importes no negativos expresados en céntimos y tasas enteras en puntos básicos. El resultado también es un entero de céntimos. Esta elección hace visible el redondeo sin exigir una infraestructura financiera completa.

## Una diferencia de medio céntimo

Tomemos un importe de 25 céntimos y una tasa de 200 puntos básicos, equivalente al dos por ciento. La comisión exacta antes de redondear es medio céntimo. Si redondeamos al par obtenemos cero céntimos. Si redondeamos al entero más próximo alejándonos de cero en el empate obtenemos un céntimo.

Ambos métodos son deterministas. Ambos pueden ser apropiados en algún contexto. La pregunta es cuál establece nuestro contrato. En este ejemplo hemos fijado el segundo para valores no negativos y lo comprobamos contra el programa COBOL ejecutado.

El caso es pequeño, pero revela por qué una demostración con valores redondos puede resultar engañosa. Para 100 euros con una tasa que produce una cantidad exacta, las dos implementaciones coinciden. El defecto solo aparece cuando elegimos una entrada que distingue los criterios.

Así se ve la diferencia en los dos lenguajes. En COBOL, la cláusula `ROUNDED` del programa del laboratorio:

**Listado 12.1 · El cálculo en legacy/fee.cob** — *Ejecutado*

```cobol
        compute fee-cents rounded = amount-cents * rate-bps / 10000
          on size error
            move 'INVALID' to result-code
          not on size error
            move fee-cents to fee-display
```

En .NET, la trampa está en la sobrecarga que no dice nada:

**Listado 12.2 · Comportamiento documentado de Math.Round [8]** — *Ilustrativo*

```csharp
Math.Round(0.5m);                                  // 0 -> al par, por defecto
Math.Round(1.5m);                                  // 2 -> también al par
Math.Round(0.5m, MidpointRounding.AwayFromZero);   // 1
decimal.Round(25m * 200m / 10000m, 0,
              MidpointRounding.AwayFromZero);      // 1 -> caso C003 del laboratorio
```

Ninguna de las dos líneas por defecto es un error de .NET. Es una política distinta. El error aparece cuando nadie decide cuál es la nuestra.

## La memoria también es parte del contrato

REDEFINES permite describir una misma región de datos con otra estructura. Una traducción que convierte cada nombre en una variable independiente puede perder esa relación. En nuestro programa, el registro de entrada se interpreta mediante un grupo redefinido. El ejemplo es sencillo y visible: los mismos caracteres representan importe, tasa y estado del cliente.

![Figura 12.1 · REDEFINES: los mismos catorce bytes leídos como tres campos. Una traducción que crea tres variables independientes pierde esa relación.](../../figures/es/fee_record.png)

*Figura 12.1 · REDEFINES: los mismos catorce bytes leídos como tres campos. Una traducción que crea tres variables independientes pierde esa relación.*

No utilizo esa demostración para afirmar que ya resolvemos layouts arbitrarios. Quedan fuera estructuras variables, overlays complejos, conversiones entre páginas de códigos y datos persistidos en formatos específicos. El adaptador de un proyecto real debe describirlos y probarlos con registros representativos.

También hay que observar efectos que no aparecen en el valor devuelto: escrituras, mensajes, cambios de estado, códigos de retorno, orden de operaciones y recuperación tras un fallo. Dos funciones pueden devolver el mismo número y dejar sistemas distintos detrás.

La equivalencia que nos interesa pertenece a un contrato de observación. Cuanto más pobre sea ese contrato, más diferencias relevantes podremos dejar sin detectar.

> **El defecto solo aparece cuando elegimos una entrada que distingue los criterios.**

---

[← Capítulo 11 · La arquitectura de una modernización verificable](11-la-arquitectura-de-una-modernizacion-verificable.md) · [Índice](../README.md) · [Parte IV · Patrones que sustituyen responsabilidades, no sintaxis →](../parte-4-patrones/README.md)
