**Español** · [English](../../en/annexes/annex-a-a-lab-that-can-prove-us-wrong.md)

[← Anexos](README.md) · [Índice](../README.md) · [Anexo B · Contrato del laboratorio →](anexo-b-contrato-del-laboratorio.md)

# Anexo A · Un laboratorio que pueda contradecirnos

> [!NOTE]
> En este repositorio el laboratorio está en la carpeta [`lab/`](../../../lab/README.md). Los comandos de este texto se ejecutan desde ella.

## Qué pretende demostrar

El laboratorio no está hecho para convencer, sino para que se pueda contradecir. Sostiene tres afirmaciones, y cada una puede caerse si alguien encuentra el contraejemplo.

La primera: un programa COBOL ejecutable y una implementación .NET 10 pueden compararse contra una **tercera expectativa aprobada**, de modo que dos programas que coinciden en un error también fallan. La segunda: un gate que distingue **PASS, FAIL e INCONCLUSIVE**, y que separa lo correcto de lo autorizado, bloquea cada defecto deliberado y cada ausencia de evidencia del conjunto. La tercera: **la equivalencia funcional aislada no dice nada sobre concurrencia**; el módulo de transferencias muestra lo que tiene que cumplirse cuando dos procesos compiten por un saldo, un cliente reenvía o un proceso muere después del débito.

## Qué necesitas

La ruta recomendada solo necesita **Podman**. En Linux se instala desde el gestor de paquetes; en macOS y Windows, con Podman Desktop o `podman machine`. Podman funciona sin demonio y sin privilegios de administrador, de modo que los ficheros que el contenedor escribe en `results/` pertenecen a tu usuario.

La ruta nativa necesita Ubuntu 24.04 o WSL2 con el SDK de .NET 10, GnuCOBOL 3, Python 3 y la biblioteca nativa de SQLite. El módulo bancario carga `libsqlite3.so.0` mediante P/Invoke, así que en Windows debe ejecutarse en WSL2 o en el contenedor.

Para las comprobaciones offline basta con Python 3.

## Ejecución con Podman

**Listado A.1 · Arranque con Podman** — *Ejecutado en diseño · receta no construida aquí*

```bash
# Linux, macOS o WSL
bash scripts/run-podman.sh          # recorrido guiado, con pausas
bash scripts/run-podman.sh --auto   # todo, incluido el módulo bancario

# Windows PowerShell
pwsh scripts/run-podman.ps1
pwsh scripts/run-podman.ps1 -Auto

# A mano
podman build -t cobol-modernization-lab -f Containerfile .
podman run --rm -it --network=none -v "$PWD/results:/work/results:Z" cobol-modernization-lab
```

La construcción necesita red una vez: la imagen base, los paquetes y la restauración de .NET. El laboratorio en sí se ejecuta con `--network=none`: sin modelo, sin clave y sin llamadas remotas. La opción `:Z` reetiqueta el volumen en sistemas con SELinux y es inocua en los demás. La etiqueta de la imagen base es mutable; fija un digest antes de medir nada que quieras reproducir.

La ejecución de referencia es nativa en Linux. La receta de Podman la construye y ejecuta el job `podman` de la integración continua; si en tu máquina se comporta de otra forma, ese informe de reproducción es justo la evidencia que el laboratorio pide.

## Ejecución nativa

```bash
sudo apt-get update
sudo apt-get install -y gnucobol3 python3 libsqlite3-0 gcc
python3 walkthrough.py                 # guiado
python3 walkthrough.py --auto --bank   # todo
```

Las variables `DOTNET` y `COBC` permiten usar otros ejecutables.

## El recorrido, paso a paso

| Paso | Comando | Qué deberías ver |
|---|---|---|
| 0 | `python3 tools/verify_offline.py` | `VERIFY: PASS`: ancla correcta, 58/58 casos coinciden con la implementación independiente, control negativo rechazado |
| 1 | `walkthrough.py`, paso 1 | El fuente `fee.cob` con su `REDEFINES` |
| 2 | `python3 cobol_local.py legacy/fee.cob --input 0000002500200Y` | El comando `cobc -x -free` y la salida `APPROVE\|00000001` |
| 3 | `walkthrough.py`, paso 3 | El candidato C# y sus modos de mutación |
| 4 | `python3 run.py` | Diez controles con los veredictos del capítulo [27](../parte-6-laboratorio/27-hacer-que-el-error-se-vea.md) y código de salida 0 |
| 5 | `walkthrough.py`, paso 5 | La tabla de veredictos y entregas |
| 6 | `python3 bank_test.py` | `status: PASS`, nueve controles y seis invariantes verdaderas |
| 7 | `python3 tools/coordinated_omission_demo.py` | p99 de 1 ms en circuito cerrado frente a 451 ms en circuito abierto |

Los códigos de salida del gate son parte del contrato: 0 para el permiso sintético, 2 para FAIL, 3 para INCONCLUSIVE y 4 para comportamiento correcto sin mandato. `run.py` termina con 0 cuando todos los controles, incluidos los bloqueos esperados, se comportan como deben.

## El calentamiento opcional

`examples/commission-three-way/` contiene el primer laboratorio, más pequeño: una comisión con punto decimal implícito (`PIC 9(8)V99`), una baseline CSV aprobada, un oráculo Python que compara baseline contra COBOL, baseline contra .NET y COBOL contra .NET, un mutante de redondeo que debe salir con código 2 y una carrera en memoria donde `SemaphoreSlim` protege dos retiradas dentro de un proceso y nada más. Se ejecuta con `bash examples/commission-three-way/run.sh`. No forma parte de la ejecución de referencia; su baseline es coherente con la política escrita y el mutante difiere en cuatro de los ocho casos.

## Lo que no acredita

No hay integración de REA, ni agente autónomo, ni cluster de actores, ni motor SQL de producción, ni bloqueo por fila, ni deadlock SQL, ni commit en dos fases, ni failover, ni prueba de pérdida eléctrica, ni despliegue en Azure, ni publicador real de la outbox. No existe una baseline medida de un mainframe. No se demuestra eficacia industrial ni independencia entre personas: los componentes son procesos distintos, pero se construyeron en el mismo trabajo.

El hash de la baseline y su ancla viven en el mismo paquete escribible. En producción deben quedar fuera del alcance del constructor y vincularse a una aprobación real. El mandato es sintético.

## Hacia dónde crece

El fichero `docs/EXPERIMENT_PROTOCOL.md` describe cuatro experimentos diseñados y no ejecutados. E1 porta el módulo bancario a un motor con bloqueo por fila y añade víctimas de deadlock, write skew y agotamiento del pool. E2 implementa el mismo contrato con actores de Orleans que coordinan y un ledger que confirma, bajo distribuciones uniformes, sesgadas y con una cuenta que recibe la mitad del tráfico. E3 compara Azure, un servidor local con su segunda unidad y una configuración híbrida con el mismo contrato de rendimiento. E4 pone a un agente a construir el candidato con escritura limitada a `Candidate/` y compara pruebas escritas por el agente, oráculo independiente y oráculo cualificado por mutaciones.

---

[← Anexos](README.md) · [Índice](../README.md) · [Anexo B · Contrato del laboratorio →](anexo-b-contrato-del-laboratorio.md)
