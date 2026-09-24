---
source_hash: ff0799823adf
title: "Lo que vamos a construir"
number: 1
part: p1
kicker: "Antes de la primera línea de código, el destino. Nadie aprende bien un viaje sin saber dónde termina."
epigraph: "No tenía idea de que estaba escribiendo un lenguaje de programación para internet. Estaba escribiendo uno para tostadoras."
epigraph_by: "James Gosling, creador de Java"
goal: >-
  Explicar, con las palabras correctas, qué es una API REST, qué es un CRUD y
  cuál es la diferencia entre Java, Spring y Spring Boot, y tener el entorno
  instalado y probado.
---

Al final de este libro hay un programa corriendo. No tiene pantalla, no
tiene botones y nadie va a elogiar su aspecto. Se queda esperando, y cuando
alguien pregunta lo correcto, responde:

:::http title="La pregunta y la respuesta que vas a construir"
GET /products/7
Accept: application/json
---
200 OK
Content-Type: application/json

{
  "id": 7,
  "name": "Teclado mecánico",
  "price": 349.90,
  "quantity": 12
}
:::

Eso es una **API**. La sigla no tiene misterio: *Application Programming
Interface*, una interfaz para programas en vez de para personas. El
navegador, la aplicación del celular y el sitio del cliente hablan con ella
por el mismo protocolo que usas para leer noticias: HTTP.

## Un programa que atiende, en vez de uno que corre

Un programa común empieza, hace su trabajo y termina. Un servidor no
termina: arranca, abre un puerto y se queda esperando. Esa diferencia cambia
cómo piensas el código.

:::diagram type="blocks" caption="El camino de una petición: cada capa resuelve un problema y la pasa adelante."
rows:
  - [{ text: "Cliente", note: "navegador, app, curl" }]
  - [{ text: "Controller", note: "traduce HTTP en llamada a método" }]
  - [{ text: "Service", note: "las reglas del negocio" }]
  - [{ text: "Repository", note: "habla con la base de datos" }]
  - [{ text: "PostgreSQL", note: "donde vive el dato cuando nadie mira" }]
:::

Esas cuatro capas son el esqueleto del proyecto. Aparecen en el capítulo 21
y se quedan hasta el final. Guarda el orden: la petición baja, la respuesta
sube.

:::story La reunión de veinte minutos
La reunión estaba programada para veinte minutos y duró una hora y diez.

—Necesitamos una API —dijo Roberto en la pizarra, escribiendo la palabra
API y subrayándola dos veces, como si subrayar resolviera algo.

—¿Una API para qué? —preguntó Marina.

—Para que la aplicación hable con el sistema.

—¿Y qué necesita preguntar la aplicación?

Roberto se quedó callado tres segundos, que en su escala es una eternidad.
Después miró a Cláudia, que miró su cuaderno, que tenía once post-its y
ninguna respuesta.

—Productos —se arriesgó Cláudia—. Necesita listar productos. Y
registrarlos. Y editarlos. Y... borrarlos, creo.

—Eso tiene nombre —dijo Marina—. Se llama CRUD.

—¡Perfecto! —Roberto escribió CRUD en la pizarra y lo subrayó dos veces—.
En tres semanas sale, ¿no?

Carlos, que tenía tres semanas en la empresa y cero líneas de Java
escritas, levantó la mano despacio. Nadie lo vio.
:::

## CRUD: cuatro verbos y nada más

La mayor parte de cualquier sistema es guardar cosas, mostrar cosas,
cambiar cosas y borrar cosas. Alguien lo bautizó **CRUD** —*create, read,
update, delete*— y HTTP ya tenía un verbo para cada una:

| Operación | Verbo HTTP | Ruta | Qué devuelve |
|---|---|---|---|
| Crear | `POST` | `/products` | `201` y el recurso creado |
| Listar | `GET` | `/products` | `200` y una página de ítems |
| Buscar uno | `GET` | `/products/{id}` | `200` o `404` |
| Actualizar | `PUT` | `/products/{id}` | `200` o `404` |
| Borrar | `DELETE` | `/products/{id}` | `204` o `404` |

Tabla: El CRUD que vas a construir en la Parte 4. Memoriza la tabla y habrás
memorizado la mitad del trabajo de un backend.

:::trivia
El término CRUD apareció en 1983, en el libro *Managing the Data Base
Environment*, de James Martin: quince años antes de que existiera una API
REST a la que llamar suya. La idea es más vieja que la web y va a
sobrevivirla.
:::

## Java, Spring y Spring Boot no son lo mismo

Esta confusión les cuesta semanas a quienes empiezan. Los tres nombres
aparecen juntos en todo tutorial y resuelven problemas distintos:

- **Java** es el lenguaje. Las palabras, la gramática, los tipos. Es lo que
  aprendes en las Partes 1 y 2.
- **Spring** es un conjunto de bibliotecas que resuelve la plomería de una
  aplicación: quién crea los objetos, quién conecta uno con otro, quién abre
  la transacción de la base de datos.
- **Spring Boot** es Spring con las decisiones ya tomadas. Trae un servidor
  embebido, configuración por convención y un solo comando para correrlo
  todo.

:::diagram type="blocks" caption="Cada capa agrega decisiones ya tomadas, y las cobra en abstracción."
flow: false
rows:
  - [{ text: "Spring Boot", note: "servidor embebido, autoconfiguración" }]
  - [{ text: "Spring Framework", note: "inyección de dependencias, transacciones, MVC" }]
  - [{ text: "Java + JVM", note: "el lenguaje y la máquina que lo ejecuta" }]
:::

El orden importa: no puedes entender Spring sin entender objetos, y no
puedes entender Spring Boot sin entender Spring. Por eso este libro dedica
catorce capítulos a Java antes de instalar el framework.

:::history
Spring nació en 2003 como una reacción. El estándar de la época,
Enterprise JavaBeans, exigía tres archivos y dos descriptores XML para
escribir una clase que sumara dos números. Rod Johnson publicó un libro de
mil páginas mostrando una forma más simple, y el código de ejemplo del libro
se convirtió en el framework más usado de la plataforma.
:::

:::story
Carlos anotó en el cuaderno: *"API = programa que le responde a otro
programa"*.

Después lo tachó y escribió: *"API = el momento en que dos departamentos de
la empresa por fin intentan conversar, y descubren que hablan idiomas
distintos"*.

Marina, que pasaba por detrás, lo leyó por encima de su hombro y dijo que
la segunda definición era mejor.
:::

## Treinta años en una página

Java no se diseñó para servidores. Se diseñó para electrodomésticos, y casi
todas sus rarezas vienen de ahí.

:::diagram type="timeline" caption="Por qué el lenguaje es así: los hitos que todavía afectan el código que vas a escribir."
width: 112
events:
  - { year: "1991", text: "Proyecto Green, en Sun: un lenguaje para TV por cable y tostadoras" }
  - { year: "1995", text: "Java 1.0 y la promesa: escribe una vez, corre en cualquier lugar", mark: true }
  - { year: "2004", text: "Java 5: genéricos, enums, for-each; el lenguaje se moderniza", mark: true }
  - { year: "2006", text: "Java se vuelve software libre (proyecto OpenJDK)" }
  - { year: "2010", text: "Oracle compra Sun" }
  - { year: "2014", text: "Java 8: lambdas y streams cambian el estilo del código", mark: true }
  - { year: "2018", text: "Ciclo de seis meses: una versión nueva cada semestre" }
  - { year: "2023", text: "Java 21: records, pattern matching y hilos virtuales", mark: true }
:::

Dos fechas merecen una frase más. **1995** es el origen de la JVM, la
máquina virtual que ejecuta el bytecode: la razón por la que el mismo
archivo compilado corre en tu computadora y en el servidor. **2014** es la
fecha en que Java dejó de ser un lenguaje solo de objetos y ganó funciones
como valor, que vas a usar en el capítulo 14 sin darte cuenta.

:::trivia
El nombre era **Oak**, por un roble frente a la ventana de James Gosling. El
departamento jurídico encontró una marca registrada con el mismo nombre, el
equipo salió a tomar café y volvió con *Java*: la isla de donde venía el
grano. Por eso el logotipo es una taza humeante.
:::

## Instalando el entorno

Necesitas tres cosas, y el orden es este.

**1. El JDK.** Descarga Temurin 21 (en `adoptium.net`) o usa el gestor de
paquetes de tu sistema. Confirma:

```bash
java -version
javac -version
```

**2. Un editor.** Cualquiera con resaltado de sintaxis sirve para la Parte
1. A partir del capítulo 16, un IDE ayuda de verdad: IntelliJ IDEA
Community o VS Code con la extensión de Java. Todavía no lo necesitas.

**3. Una carpeta.** Crea una carpeta para el libro y entra en ella. Todo
comando de este libro supone que estás en la raíz del proyecto.

:::tree title="Dónde estamos ahora"
java-one/
  App.java  # el próximo capítulo crea este archivo
:::

:::pitfall
No instales el JDK 8 porque un video viejo dijo que "es el más estable". La
mitad de la sintaxis de este libro —`var`, `record`, `switch` con flecha— no
existe ahí. Si tu empresa usa Java 8, vas a saber lidiar con eso después de
aprender la versión moderna; al revés es mucho más difícil.
:::

## El camino entero, en una imagen

Diez partes, cuarenta y dos capítulos, un proyecto:

```text title="La columna vertebral del libro"
Java  →  POO  →  HTTP  →  Spring Boot  →  REST  →  JPA
      →  PostgreSQL  →  CRUD  →  Validación  →  Seguridad
      →  Pruebas  →  Proyecto final
```

Si en algún momento te pierdes, vuelve a esta línea y ubica dónde estás.
Cada flecha es una decisión nueva sobre el mismo programa.

:::summary
- Una API es un programa que responde a otros programas, por HTTP.
- CRUD son cuatro operaciones; HTTP ya tenía un verbo para cada una.
- Java es el lenguaje, Spring es la plomería, Spring Boot es Spring con las
  decisiones listas.
- La arquitectura del proyecto tiene cuatro capas: controller, service,
  repository, base de datos.
:::

:::checkpoint
Sabes explicar qué es una API REST y qué es un CRUD, conoces la diferencia
entre Java, Spring y Spring Boot, y tienes un JDK instalado que compila y
ejecuta.
:::

:::milestone
Entorno listo y destino conocido. Ninguna línea de código escrita, y está
bien: el capítulo 1 de un proyecto siempre trata de decidir qué construir.
:::

:::exercise level=1
Escribe, con tus palabras y en tres frases, lo que va a hacer tu API.
Guarda el papel. En el capítulo 41 vas a compararlo con lo que
construiste.

:::answer
No hay respuesta correcta, pero hay una respuesta buena: habla de *datos* y
de *operaciones*, no de tecnología. "Guardar los productos de una tienda,
permitir buscar por nombre y precio, y solo dejar que un administrador los
registre" es una descripción mejor que "una API en Spring Boot con
PostgreSQL".
:::

:::exercise level=2
Abre la terminal y corre `java -version`. Después busca el número de versión
en la página de notas de lanzamiento de OpenJDK y descubre una
funcionalidad que tu versión tiene y la anterior no tenía.

:::answer
El objetivo del ejercicio no es la respuesta, es el hábito: saber en qué
versión estás y dónde se lee lo que cambió. Un programador Java que no sabe
su propia versión va a copiar código que no compila.
:::
