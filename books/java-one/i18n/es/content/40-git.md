---
source_hash: 031640f7d604
title: "Git"
number: 40
part: p9
kicker: "El código dice qué hace el sistema. El historial dice por qué, y es la única parte que no puedes reconstruir."
goal: >-
  Versionar el proyecto con commits que explican la intención, trabajar con
  ramas y *pull requests*, y resolver un conflicto sin pánico.
---

Este es el capítulo que debería haber sido el primero y es el penúltimo, a
propósito: Git solo tiene sentido cuando existe algo con una historia que
contar. El proyecto de Aurora tiene cuarenta capítulos de decisiones.

## Los cuatro comandos del día

```bash title="El ciclo entero" numbered
git status                      # qué cambió
git add src/main/java/...       # elegir lo que entra
git commit -m "mensaje"         # registrar
git push                        # publicar
```

```bash title="Empezando el proyecto"
git init
echo "target/" > .gitignore
git add .
git commit -m "primer commit: esqueleto del catálogo"
git remote add origin git@github.com:aurora/catalog.git
git push -u origin main
```

:::pitfall
`target/`, `.idea/`, `*.class` y cualquier archivo con contraseñas **nunca**
entran al repositorio. Un `.gitignore` olvidado el primer día significa,
seis meses después, un repositorio de 400 MB con binarios compilados. Y un
`application.properties` versionado con la contraseña de la base significa
que la contraseña se filtró: aunque la borres después, sigue en el historial
para siempre.
:::

## El commit es un mensaje para el futuro

:::compare left="Lo que no ayuda" right="Lo que explica"
ajustes

correcciones

fix

wip

update final
---
corrige N+1 en el
listado de productos

usa @EntityGraph para
cargar la categoría
junto: 4.032 consultas
pasaron a ser 1
:::

El primer grupo aparece en todos los repositorios del mundo y es inútil el
día en que alguien necesita entender por qué existe una línea. El segundo
responde a la única pregunta que el código no responde solo: **por qué**.

```text title="El formato que adopta la mayoría de los equipos"
tipo: resumen en imperativo, hasta 50 caracteres

Cuerpo opcional, que explica el motivo y el contexto, no lo
que el diff ya muestra. Corta en 72 columnas.

Closes #42
```

| Tipo | Cuándo |
|---|---|
| `feat` | funcionalidad nueva |
| `fix` | corrección de un defecto |
| `refactor` | cambia la forma, no el comportamiento |
| `test` | agrega o corrige una prueba |
| `docs` | documentación |
| `chore` | build, dependencia, configuración |

Tabla: La convención *Conventional Commits*. Permite generar el *changelog*
automáticamente y, más importante, obliga a quien escribe a clasificar su
propio cambio.

:::key
Un buen commit es **pequeño y coherente**: un cambio, un motivo. Si el
mensaje necesita la palabra "y" dos veces, son dos commits. Separarlos
cuesta treinta segundos; el beneficio es poder revertir uno sin deshacer el
otro.
:::

## Ramas

```bash title="El flujo de una funcionalidad" numbered
git switch -c feat/busqueda-por-nombre  # crea la rama y entra

# ... trabaja, hace commits ...

git push -u origin feat/busqueda-por-nombre
# abre el pull request en la interfaz de GitHub

git switch main
git pull
git branch -d feat/busqueda-por-nombre  # borra la rama local
```

:::diagram type="flowchart" caption="Una rama por funcionalidad, revisión antes de entrar."
nodes:
  - { id: m,  type: start,   text: "main" }
  - { id: b,  type: process, text: "feat/busqueda-por-nombre" }
  - { id: c,  type: process, text: "commits" }
  - { id: pr, type: decision,text: "¿revisión aprobada?" }
  - { id: mg, type: process, text: "merge en main" }
  - { id: fx, type: process, text: "ajusta y hace commit" }
edges:
  - { from: m,  to: b }
  - { from: b,  to: c }
  - { from: c,  to: pr }
  - { from: pr, to: mg, label: "sí" }
  - { from: pr, to: fx, label: "no" }
  - { from: fx, to: pr }
:::

La rama protegida —un `main` que solo acepta cambios por *pull request*
aprobado, con las pruebas de los capítulos 34 a 37 pasando— es la
configuración de calidad más barata que existe. Son dos clics en la interfaz
de GitHub.

## Conflicto: qué es y cómo salir

```text title="El mensaje que asusta y no debería"
Auto-merging ProductService.java
CONFLICT (content): Merge conflict in ProductService.java
Automatic merge failed; fix conflicts and commit the result.
```

```java title="El archivo queda así" numbered
<<<<<<< HEAD
    return repository.findAll(pageable)
            .map(ProductResponse::of);
=======
    return repository.findAll(spec, pageable)
            .map(ProductResponse::of);
>>>>>>> feat/busqueda-por-nombre
```

Entre `<<<<<<<` y `=======` está tu versión; entre `=======` y `>>>>>>>`, la
de la otra rama. Borras los marcadores y dejas el código correcto, que puede
ser uno de los dos, o una tercera cosa que junta los dos.

```bash
git add ProductService.java
git commit          # el mensaje de merge ya viene listo
```

:::pitfall
Un conflicto no es un error: es Git diciendo que dos personas cambiaron la
misma línea y que no tiene cómo adivinar cuál vale. Aceptar a ciegas "mi
versión" para sacarse la pantalla de encima es como borrar el trabajo de un
colega sin leerlo, y pasa todo el tiempo. Lee los dos lados. Ante la duda,
llama a la persona.
:::

## Deshacer, sin drama

```bash title="Los cuatro deshacer útiles" numbered
git restore ProductService.java     # descarta un cambio sin commit
git restore --staged archivo.java   # lo saca del "add"
git commit --amend                  # corrige el último (¡local!)
git revert a1b2c3d                  # deshace creando otro commit
```

:::pitfall
`git reset --hard` borra el trabajo sin commit y no tiene vuelta atrás. Y
`git push --force` reescribe la historia del servidor: si alguien ya había
traído esa rama, su repositorio pasa a divergir del tuyo de una forma
confusa. En una rama compartida, deshaz con `revert`, que crea un commit
nuevo y preserva el historial.
:::

## El historial como herramienta

```bash title="Lo que vas a usar cuando algo se rompa" numbered
git log --oneline -20
git log -p ProductService.java    # la historia de un archivo
git blame ProductService.java     # quién escribió cada línea
git bisect start                  # encuentra el commit que rompió
```

`git blame` tiene una fama injusta de herramienta para acusar. En la
práctica, es el camino más rápido hacia **el mensaje de commit** que explica
por qué existe esa línea rara, y ahí es donde la calidad de los mensajes
deja de ser etiqueta y pasa a ser ahorro de tiempo.

:::story En mi máquina funciona
El bug apareció el jueves y solo pasaba en el entorno de pruebas.

Carlos lo corrió en local: funcionaba. Lo corrió de nuevo: funcionaba. Pasó
la mañana comparando configuración, versión de Java, versión de PostgreSQL.

A las once y media, Marina le pidió ver su `git status`.

```text
On branch feat/filtros
Changes not staged for commit:
  modified:   src/main/resources/application.properties
  modified:   src/main/java/.../ProductSpecs.java
  modified:   src/main/java/.../SecurityConfig.java
```

Tres archivos cambiados y sin commit. Funcionaba en la máquina de Carlos
porque la corrección existía solo en la máquina de Carlos, en archivos que
había tocado el martes y olvidado.

—No es que funcione en tu máquina —dijo Marina—. Es que tu máquina tiene un
software que no existe en ningún otro lado. Ni en el repositorio.

En el commit de esa tarde, Carlos escribió el mensaje más largo de su vida.
Marina lo aprobó sin comentarios.
:::

:::summary
- `status`, `add`, `commit`, `push` resuelven el día; el resto es para
  cuando algo sale mal.
- `.gitignore` el primer día; contraseñas nunca, en ningún commit.
- El mensaje explica el **porqué**; el diff ya muestra el qué.
- Una rama por funcionalidad, `main` protegido por *pull request* y
  pruebas.
- Un conflicto es una pregunta, no un error. `revert` en rama compartida,
  nunca `push --force`.
:::

:::checkpoint
Versionas el proyecto, escribes commits que explican la intención, trabajas
en ramas con revisión y resuelves un conflicto leyendo los dos lados.
:::

:::milestone
Fin de la Parte 9. El proyecto tiene historial, documentación que se
actualiza sola y peticiones versionadas. Todo lo que faltaba para que otra
persona se hiciera cargo del código, y eso es exactamente lo que la Parte 10
te va a pedir.
:::

:::exercise level=1
Inicializa el repositorio, crea el `.gitignore` y haz el primer commit con
un mensaje que explique qué es el proyecto.

:::answer
Un detalle que casi nadie hace y vale mucho: escribe en el cuerpo del primer
commit **por qué** existe el proyecto y qué problema resuelve. Es el mensaje
que más gente va a leer, y el único que nadie puede reconstruir después.
:::

:::exercise level=2
Crea una rama, cambia una línea, vuelve a `main`, cambia la misma línea de
otra forma y provoca un conflicto a propósito. Resuélvelo.

:::answer
Hacerlo a propósito, con calma, en un proyecto que no importa, es la
diferencia entre quedarse paralizado y resolverlo en dos minutos el día en
que pase de verdad, que será un viernes, con prisa.
:::

:::exercise level=3
Usa `git bisect` para encontrar el commit que introdujo un defecto. Arma el
escenario: diez commits, uno de ellos rompiendo una prueba.

:::answer
`git bisect start`, `git bisect bad`, `git bisect good <commit viejo>`, y
Git hace una búsqueda binaria: diez commits se vuelven tres o cuatro
verificaciones. Con un script de prueba, `git bisect run ./mvnw test`
encuentra al culpable solo. Es la herramienta más subestimada de Git y la
que más impresiona cuando la usas delante de alguien.
:::
