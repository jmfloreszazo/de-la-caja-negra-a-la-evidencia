**Español** · [English](../../en/part-1-before-translating/03-why-one-to-one-conversion-is-not-modernization.md)

[← Capítulo 2 · El sistema que estamos intentando conservar](02-el-sistema-que-estamos-intentando-conservar.md) · [Índice](../README.md) · [Capítulo 4 · Lo que comparto con otros autores y dónde discrepo →](04-lo-que-comparto-con-otros-autores-y-donde-discrepo.md)

# Capítulo 3 · Por qué la conversión uno a uno no es modernización

> [!IMPORTANT]
> **Tesis del capítulo.** No hay que copiar el diseño heredado: hay que preservar sus obligaciones y rediseñar los mecanismos que las satisfacen. Una traducción literal puede ser un puente legítimo, nunca el destino.

Traducir instrucciones puede ser una actividad útil. La crítica empieza cuando confundimos esa actividad con el objetivo final. Si conservamos los mismos límites de programa, el mismo acoplamiento a datos, el mismo modelo de estados globales y el mismo orden imperativo de operaciones, pero cambiamos COBOL por C#, habremos fabricado un monolito heredado en otro lenguaje. Lo que algunos llaman «JOBOL» en Java también puede existir en .NET. El problema no es el lenguaje de destino: es el diseño que arrastramos.

La copia literal falla por seis motivos. Primero, **hereda particiones accidentales**: los módulos respondían a limitaciones de memoria, equipos y compilación de otra época, no necesariamente a capacidades de negocio. Segundo, **preserva acoplamientos** que ahora atraviesan redes y bases de datos. Una lectura de área común que costaba nanosegundos puede convertirse en una llamada remota. Tercero, **replica estados implícitos** que dejan de ser seguros al escalar horizontalmente. Cuarto, **traslada semánticas de almacenamiento** —EBCDIC, `COMP-3`, `REDEFINES`, campos sobrepuestos, formatos de signo— a representaciones que no comparten sus supuestos. Quinto, **mantiene problemas de entrega**: despliegues masivos, cambios inseparables y ventanas rígidas. Sexto, **impide aprovechar el nuevo entorno**, porque obliga a la tecnología moderna a imitar las decisiones de una arquitectura distinta.

Pero afirmar que «nunca» debemos hacer una conversión 1:1 sería tan dogmático como afirmar que siempre debemos hacerla. Existe un papel legítimo para una traducción mecánica y conservadora: puede crear una plataforma de transición, reducir dependencia de un compilador, mantener un contrato temporal o permitir tests diferenciales antes de rediseñar. En ese caso no la vendería como estado final. La declararía **fase de compatibilidad**, con fecha, criterios de salida y deuda técnica identificada. También contemplaría conservar COBOL en producción mientras extraemos servicios nuevos. La modernización no se mide por el porcentaje de código reescrito.

La frase que guía este libro es la siguiente: **no hay que copiar el diseño heredado; hay que preservar sus obligaciones y rediseñar los mecanismos que las satisfacen**. Eso exige preguntar qué garantiza realmente cada bloque antiguo. El informe que generaba un programa nocturno puede convertirse en un pipeline particionado. El bloqueo de un registro puede convertirse en una transacción SQL corta, un control optimista o una cola por clave. La sesión conversacional puede convertirse en una máquina de estados explícita. Pero nunca sin identificar primero qué propiedad protegía.

## Lo que se dice y lo que hay

La conversación pública sobre traducción automática mezcla afirmaciones que conviene separar. Las pongo frente a frente porque es la forma más rápida de saber qué estamos comprando.

| Lo que se dice | Lo que hay |
|---|---|
| «La IA convierte COBOL a C# en horas» | Puede generar C# plausible en horas. La equivalencia funcional, de datos, operacional y de capacidad no viene incluida |
| «Si compila y pasa los tests, está migrado» | Depende de quién escribió los tests y de dónde salió el resultado esperado. Si los escribió el mismo agente a partir del mismo código, verifican su interpretación |
| «Usamos decimal, así que el dinero cuadra» | El tipo es el comienzo. La escala, el momento del redondeo y el desempate deciden el céntimo |
| «Ya no hay mainframe, ahora es cloud native» | Si conservamos los límites de programa, el estado global y el acoplamiento a datos, tenemos el mismo monolito con más viajes de red |
| «Lo pasamos 1:1 y luego refactorizamos» | Puede ser una buena estrategia si la fase de compatibilidad tiene fecha, criterios de salida y deuda identificada. Sin ellos, el «luego» no llega |

## Un ejemplo engañosamente sencillo

Supongamos un programa COBOL que lee una cuenta, comprueba saldo, lo decrementa y escribe el registro. Una IA produce un método `WithdrawAsync`, utiliza `decimal` y obtiene el resultado correcto para un caso. Suena razonable. Si dos instancias del servicio leen el saldo antes de que ninguna confirme su escritura, ambas pueden aprobar la retirada. Los datos son correctos en cada ejecución aislada; el sistema es incorrecto cuando funciona como sistema. A ese fallo no se llega necesariamente ampliando la ventana de contexto del LLM. Se llega analizando el contrato de concurrencia.

La modernización, por tanto, no consiste en un agente que transforma sintaxis mientras otro agente inventa tests a partir del mismo código. Consiste en construir una especificación independiente, identificar garantías y elegir patrones cuyos efectos podamos demostrar.

## El mismo ejemplo, en código

Veamos el programa antiguo. El fragmento es ilustrativo, pero el patrón aparece en muchísimas transacciones CICS sobre ficheros VSAM.

**Listado 3.1 · Retirada en COBOL con CICS: la lectura reserva el registro** — *Ilustrativo*

```cobol
           EXEC CICS READ FILE('ACCOUNTS')
                     INTO(WS-ACCOUNT)
                     RIDFLD(WS-ACCOUNT-ID)
                     UPDATE
                     RESP(WS-RESP)
           END-EXEC
           IF WS-RESP = DFHRESP(NORMAL)
              IF WS-BALANCE >= WS-AMOUNT
                 SUBTRACT WS-AMOUNT FROM WS-BALANCE
                 EXEC CICS REWRITE FILE('ACCOUNTS')
                           FROM(WS-ACCOUNT)
                           RESP(WS-RESP)
                 END-EXEC
              ELSE
                 EXEC CICS UNLOCK FILE('ACCOUNTS') END-EXEC
                 MOVE 'NSF' TO WS-RESULT
              END-IF
           END-IF
```

La palabra importante es `UPDATE`. No es una etiqueta decorativa: la lectura obtiene control exclusivo del registro, y en un fichero recuperable la modificación participa en la unidad de trabajo que se confirma o se deshace en el syncpoint [16]. La garantía no está escrita en el COBOL; la aporta el entorno en el que el COBOL se ejecuta.

Ahora, la traducción que cualquiera —persona o agente— produce en cinco minutos:

**Listado 3.2 · Traducción literal a C#: compila, pasa el caso feliz y pierde la garantía** — *Ilustrativo*

```csharp
public async Task<string> WithdrawAsync(string accountId, decimal amount)
{
    var account = await _repository.GetAsync(accountId); // sin reserva
    if (account.Balance < amount) return "NSF";
    account.Balance -= amount;                           // sobre una foto
    await _repository.SaveAsync(account);                // incondicional
    return "OK";
}
```

Con una sola instancia y un solo cliente, funciona. Con dos instancias y dos retiradas simultáneas, ambas leen el mismo saldo, ambas aprueban y la segunda escritura pisa a la primera. Ningún test unitario lo detecta, porque ningún test unitario ejecuta dos historias a la vez.

![Figura 3.1 · La traducción literal bajo concurrencia: dos instancias deciden sobre la misma foto y se entregan 1.300 de una cuenta con 1.000.](../../figures/es/race_naive.png)

*Figura 3.1 · La traducción literal bajo concurrencia: dos instancias deciden sobre la misma foto y se entregan 1.300 de una cuenta con 1.000.*

La corrección no consiste en poner un `lock` en el controlador: protegería un proceso y el servicio tendrá varios. Consiste en llevar la regla al lugar donde se confirma. Este es el fragmento real del laboratorio, que se ejecuta contra una base SQLite desde procesos independientes:

**Listado 3.3 · Débito condicionado dentro de la transacción (Bank/Program.cs)** — *Ejecutado*

```csharp
db.Exec("BEGIN IMMEDIATE"); begun = true;
// ... comprobación de idempotencia por identidad de operación ...
db.Exec($"UPDATE accounts SET balance=balance-{amount} WHERE id={src} AND balance>={amount}");
var approved = db.Changes == 1;   // 1 fila: aprobado; 0: fondos insuficientes
if (approved) {
    db.Exec($"UPDATE accounts SET balance=balance+{amount} WHERE id={dst}");
}
// ... operación, dos asientos y fila outbox en la MISMA transacción ...
db.Exec("COMMIT");
```

![Figura 3.2 · La regla vive donde se confirma: el motor serializa las escrituras sobre la fila y solo una retirada pasa la condición.](../../figures/es/race_fixed.png)

*Figura 3.2 · La regla vive donde se confirma: el motor serializa las escrituras sobre la fila y solo una retirada pasa la condición.*

El código resultante se parece menos al COBOL original. El comportamiento se parece más al que necesitamos. Esa es, en pequeño, la tesis de este libro. El capítulo [28](../parte-6-laboratorio/28-transferencias-bloqueos-y-fallos-en-local.md) muestra qué ocurre cuando dos procesos compiten de verdad por ese saldo.

> **La modernización 1:1 puede ser un puente, pero nunca deberíamos confundir el puente con la ciudad a la que queremos llegar.**

---

[← Capítulo 2 · El sistema que estamos intentando conservar](02-el-sistema-que-estamos-intentando-conservar.md) · [Índice](../README.md) · [Capítulo 4 · Lo que comparto con otros autores y dónde discrepo →](04-lo-que-comparto-con-otros-autores-y-donde-discrepo.md)
