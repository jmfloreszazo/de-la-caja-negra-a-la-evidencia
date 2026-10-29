# Launch guide

Maintainer guide for the first publication. It can be deleted after edition v2026.10.29. The guide is in English; each communication piece is in the language of its audience.

## 1. Decisions only the author can make

- [ ] **Licenses.** The proposal is CC BY-SA 4.0 for the text and MIT for the code. If that changes, update `LICENSE.md`, `CITATION.cff` and the last section of `CONTRIBUTING.md`.
- [ ] **Contact email** in `CODE_OF_CONDUCT.md` (search for `TO BE COMPLETED`).
- [ ] **Repository name.** Assumed to be `jmfloreszazo/de-la-caja-negra-a-la-evidencia`. If it is different: `grep -rl "de-la-caja-negra-a-la-evidencia" --include=*.md --include=*.cff --include=*.json --include=*.yml .`
- [ ] **Read the English.** At least the prologue and chapters 3, 10 and 37. The rest stays in the seven `i18n` issues created by the setup script.

## 2. Publish in ten minutes

```bash
unzip de-la-caja-negra-a-la-evidencia.zip
cd de-la-caja-negra-a-la-evidencia

python3 scripts/check.py                 # must print CHECK: PASS
git init -b main
git add .
git commit -m "docs: first open edition v2026.10.29"
gh repo create jmfloreszazo/de-la-caja-negra-a-la-evidencia --public --source . --push

# Labels, Discussions, topics, milestone and the 17 seed issues
bash scripts/setup_github.sh jmfloreszazo/de-la-caja-negra-a-la-evidencia
```

Wait for the **Book** and **Lab** workflows. If the `podman` or `native` job fails, fix it before tagging: the governance you are publishing requires every workflow to be green for an edition. Then:

```bash
# Protect main with the book checks and CODEOWNERS review
PROTECT_MAIN=1 bash scripts/setup_github.sh jmfloreszazo/de-la-caja-negra-a-la-evidencia

# First edition: the release workflow attaches book/es.md and book/en.md
git tag v2026.10.29
git push origin v2026.10.29
```

Finally, upload `assets/social-preview.png` as the social preview in **Settings → General**, optionally use `assets/mark-512.png` as the avatar of the project's channels, and pin the welcome message below in **Discussions**.

## 3. Welcome message for Discussions (Announcements)

**Title:** Bienvenida · Welcome

```text
Español. Este repositorio es un libro y un laboratorio sobre cómo modernizar COBOL sin apostar el negocio a una equivalencia que no sabemos demostrar. Está en abierto porque un libro que defiende la evidencia no puede pedir que se le crea por fe. Si es tu primera vez: elige un issue «good first issue», lee CONTRIBUTING.md o pregunta aquí mismo, en español o en inglés.

English. This repository is a book and a lab on modernizing COBOL without betting the business on an equivalence we cannot demonstrate. It is open because a book that argues for evidence cannot ask to be believed on faith. If this is your first time: pick a "good first issue", read CONTRIBUTING.md or just ask here, in Spanish or English.
```

## 4. LinkedIn posts

Each post is in a block so it can be pasted as is.

### Spanish

```text
Hoy libero en GitHub *De la caja negra a la evidencia*: un libro abierto, en español y en inglés, sobre cómo modernizar COBOL sin apostar el negocio a una equivalencia que no sabemos demostrar.

La tesis cabe en una línea: la IA puede investigar, proponer y construir; aceptar el resultado exige contratos, oráculos independientes y una autoridad explícita.

Dentro hay 37 capítulos, 41 diagramas C4 y UML en Mermaid y un laboratorio que ejecuta COBOL real con GnuCOBOL, lo compara con .NET 10 y deja que un gate bloquee los errores. Incluido el caso en que COBOL y C# coinciden… y los dos se equivocan.

Lo publico en abierto porque un libro que defiende la evidencia no puede pedir que se le crea por fe. Si has migrado un core, mantenido un batch de cierre o simplemente tienes Podman y media hora, me ayudas mucho llevándome la contraria.

Una modernización 1:1 puede ser un puente. No la confundamos con la ciudad a la que queremos llegar.

#COBOL #Mainframe #Modernización #AgenticAI #Arquitectura #dotnet
```

### English

```text
Today I am releasing *From Black Box to Evidence* on GitHub: an open book, in Spanish and English, on modernizing COBOL without betting the business on an equivalence we cannot demonstrate.

The thesis fits in one line: AI can investigate, propose and build; accepting the result requires contracts, independent oracles and explicit authority.

Inside there are 37 chapters, 41 C4 and UML diagrams in Mermaid and a lab that runs real COBOL with GnuCOBOL, compares it with .NET 10 and lets a gate block the errors. Including the case where COBOL and C# agree… and both are wrong.

It is open because a book that argues for evidence cannot ask to be believed on faith. If you have migrated a core, kept a closing batch alive or simply have Podman and half an hour, you help me a lot by proving me wrong.

A 1:1 modernization can be a bridge. Let's not mistake it for the city we want to reach.

#COBOL #Mainframe #Modernization #AgenticAI #SoftwareArchitecture #dotnet
```

## 5. Blog post for jmfloreszazo.com (Spanish)

### De la caja negra a la evidencia: libero el libro (y el laboratorio) para que me lleves la contraria

*Un libro abierto, en español y en inglés, sobre COBOL, agentes de IA, patrones de arquitectura y oráculos. Con un laboratorio que puedes ejecutar en tu máquina y romper a propósito.*

> **Tesis del artículo.** La IA puede investigar, proponer y construir. Aceptar el resultado exige contratos, oráculos independientes y una autoridad explícita. Un libro que defiende eso no puede pedir que se le crea por fe: por eso lo publico en abierto, con su laboratorio y sus límites escritos.

Llevo semanas dándole vueltas a una escena que se repite. Un agente recibe un programa COBOL, produce una versión en C#, la demo arranca y alguien pregunta cuánto tardaríamos en hacer lo mismo con todo el core.

Mi primera pregunta siempre es otra: ¿qué acabamos de demostrar?

Adelanto la conclusión sin ceremonia: **una modernización 1:1 puede ser un puente, pero nunca deberíamos confundir el puente con la ciudad a la que queremos llegar.** De esa idea ha salido un libro de 37 capítulos, *De la caja negra a la evidencia*, y hoy lo libero entero en GitHub, en español y en inglés.

#### Por qué otro libro sobre COBOL

Porque la conversación se ha polarizado en dos bandos que no me sirven. Uno dice que la IA traduce COBOL en horas. El otro, que la IA no puede tocar un sistema crítico. Los dos se saltan lo difícil: el comportamiento que importa no está solo en el fuente. Está en CICS, en Db2, en el batch de cierre, en un `READ UPDATE` que reserva un registro y en las personas que conocen las excepciones.

| Lo que se dice | Lo que hay |
|---|---|
| «La IA convierte COBOL a C# en horas» | Puede generar C# plausible en horas. La equivalencia funcional, de datos, operacional y de capacidad no viene incluida |
| «Si compila y pasa los tests, está migrado» | Depende de quién escribió los tests. Si fue el mismo agente, a partir del mismo código, verifican su interpretación |
| «Tenemos X MIPS: ¿cuántas vCPU necesitamos?» | Un MIPS no es una unidad de trabajo de negocio. Hay que medir transacciones confirmadas, latencias por clase y el peor día |

#### Qué hay dentro

Siete partes que siguen el orden en que se toman las decisiones. **Qué estamos conservando** de verdad. **Arqueología con agentes**, con REA como ejemplo de disciplina de evidencia, no como traductor mágico. **Oráculos y TODM**, para separar quién construye de quién acepta. **Patrones que sustituyen responsabilidades**: Strangler Fig, capa anticorrupción, transacciones, outbox, fencing, actores con Orleans, batch particionado, CQRS y sagas, cada uno con sus condiciones de uso y sus contraindicaciones. **Capacidad**, desde los MIPS hasta la omisión coordinada. **El laboratorio**. Y **la organización**: SDLC, plan con salidas y cuándo no migraría.

Hay 41 diagramas en Mermaid —C4 de contexto, contenedores y despliegue, UML de secuencia, estados y clases— que GitHub renderiza y que cualquiera puede corregir en un pull request.

#### Un laboratorio que puede contradecirme

Esto es lo que más me importa. El laboratorio ejecuta un COBOL real con GnuCOBOL, lo compara con una implementación .NET 10 contra una **tercera expectativa aprobada** y deja que un gate decida: `PASS`, `FAIL` o `INCONCLUSIVE`, con la autorización de entrega aparte.

```bash
cd lab
python3 tools/verify_offline.py
bash scripts/run-podman.sh --auto
```

Siembro tres defectos y el gate los bloquea. Hago que COBOL y C# coincidan en un resultado incorrecto y el gate también lo bloquea, porque no compara dos programas entre sí: los compara con el contrato. Y retiro el mandato a un candidato correcto: comportamiento `PASS`, entrega bloqueada. **Correcto no es lo mismo que autorizado.**

Después vienen las transferencias: procesos reales compitiendo por un saldo, caídas después del débito, respuestas perdidas tras el commit y un oráculo contable que no le pregunta al servicio, sino a lo que queda en la base de datos.

#### Lo honesto primero

El laboratorio es pequeño a propósito y tiene una sección entera sobre lo que no demuestra. No hay cluster de Orleans, ni motor SQL con bloqueo por fila, ni Azure desplegado, ni baseline medida de un mainframe. Los listados que no he compilado llevan la etiqueta *Ilustrativo*. La receta de Podman se valida en el primer push de la CI. Y la traducción al inglés la he revisado yo: necesita ojos nativos.

#### Por qué en abierto, y por qué en dos idiomas

Porque la evidencia se gana cuando otros pueden repetirla y refutarla. El repositorio tiene guía de colaboración por perfiles, gobernanza escrita, CODEOWNERS sobre el oráculo —nadie aprueba su propio oráculo, tampoco yo— y una comprobación en CI que impide que el español y el inglés se separen.

Si eres veterano de mainframe, de .NET, de arquitectura o de rendimiento, hay un sitio para ti. Si solo tienes media hora y Podman, también: ejecuta el laboratorio y cuéntame qué pasa, sobre todo si falla.

> **Antes de pedirle a un agente que reescriba tu COBOL, construye el oráculo que le diga cuándo se equivoca.**

**Enlaces:** repositorio en GitHub · el libro entero en una página (`book/es.md`) · the book in English (`book/en.md`) · laboratorio · guía de colaboración.

## 6. The first two weeks

| Day | What | Why |
|---|---|---|
| 0 | Publish, run the setup, tag `v2026.10.29` and pin the welcome | The first visit finds everything in order |
| 1 | Blog post and LinkedIn (Spanish in the morning, English in the afternoon) | Reach both communities |
| 2–5 | Answer every issue and PR within 48 hours | First experiences decide whether people come back |
| 7 | Summary in Discussions: what arrived, what was learned, what is missing | Make other people's work visible |
| 14 | Second edition with the merged contributions and its CHANGELOG entry | Show that contributing matters |
