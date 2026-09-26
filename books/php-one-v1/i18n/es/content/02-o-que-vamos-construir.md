---
source_hash: 1612a9ab7f2e
title: "Lo que vamos a construir"
number: 2
slug: o-que-vamos-construir
part: p1
kicker: "Once cajas en una diapositiva, sesenta y ocho mil reales en juego, y nadie en la sala capaz de decir qué hace el sistema hoy."
epigraph: "Caminar sobre el agua y desarrollar software a partir de una especificación son fáciles — siempre que ambas estén congeladas."
epigraph_by: "Edward V. Berard"
goal: >-
  Entender qué es una API y por qué la Casa Amarela necesita una, separar
  libro de ejemplar y de préstamo, y terminar con PHP, Composer y editor
  instalados y comprobados.
---

:::story Jornada de Modernización 360°
La diapositiva tenía once cajas unidas por flechas y, en el medio, una caja
más grande que decía **CORE**.

— Es simple — dijo el Dr. Aurélio. — Modernizamos el core, lo exponemos vía
API, enchufamos el mobile y escalamos.

Le había vendido el proyecto a una asociación de vecinos en cuarenta
minutos usando esas cuatro palabras, lo cual es un talento de verdad.

Dedé levantó la mano.

— ¿Qué hace el core hoy?

Hubo un silencio de tres segundos, que en una reunión de doce personas da
tiempo para que alguien tosa a propósito.

— Él... procesa — dijo Cléber.

— ¿Procesa qué?

Cléber llevaba ocho años en Vertexo y ya había aprendido que una respuesta
precisa se convierte en una tarea con su nombre. Miró a Márcia.

— Nonato sabe — dijo Márcia.

— Nonato está de vacaciones.

— Vuelve el 28.

— ¿Y cuándo entregamos?

Márcia respondió sin consultar nada, porque administraba fechas como un
bombero administra fósforos.

— La rendición de cuentas de la subvención es el 31 de marzo.

— ¿Y si pasa del 31 de marzo?

— Le devolvemos sesenta y ocho mil reales a la municipalidad.

La reunión duró cincuenta minutos más y produjo tres decisiones de
arquitectura sobre un sistema que nadie de los presentes sabía describir.
:::

A las siete de la tarde de ese mismo martes, Dedé pasó por la Casa Amarela
para devolver un libro atrasado y ver, con sus propios ojos, lo que Vertexo
acababa de comprometerse a reemplazar.

:::story Cuarenta segundos
— ¿Tú eres el de la computadora? — preguntó Vera, sin levantar los ojos de
la etiqueta.

— Sí.

— El Sistema anda mal.

— ¿Mal cómo?

Señaló el monitor con el mentón. Pantalla gris, formulario de dieciocho
campos, tres de ellos llamados `obs`, `obs2` y `obs_nueva`.

— Cuando dos personas prestan al mismo tiempo, desaparece uno. Cuando
imprimo el informe de atrasados, se traba en la tercera página. Cuando
alguien devuelve el domingo, cobra multa, y el domingo ni abrimos. Y lo de
siempre: si buscas "Machado de Assis" con dos espacios en el medio, dice
que no hay.

— ¿Desde cuándo?

— Lo del domingo, unos cuatro años. Lo demás ya ni me acuerdo.

— ¿Y nadie lo arregló?

Vera pegó la etiqueta, la alisó con el pulgar y agarró el siguiente libro.

— Todos los años viene un muchacho y dice que lo va a arreglar. Tú eres el
cuarto.
:::

## La pregunta que traba el proyecto

La reunión de la mañana no fue un caso de incompetencia. Pasó lo que pasa
en empresas de cualquier tamaño: el sistema es viejo, quien lo escribió se
fue o está de vacaciones, y la presión por un cronograma llega antes que el
entendimiento.

El resultado es siempre el mismo — decisiones de arquitectura tomadas sobre
una caja que dice **CORE**.

Fíjate en quién, de las doce personas de la reunión, logró describir el
comportamiento del sistema: nadie. Y fíjate en cuánto tardó Vera en
describir el suyo: cuarenta segundos, sin dejar de etiquetar, con cuatro
defectos, una frecuencia y una fecha aproximada para cada uno.

:::note En tu carrera
"¿Qué hace este sistema hoy?" es la pregunta más barata y más impopular de
cualquier proyecto de modernización. Suele trabar la reunión — y trabar la
reunión es exactamente el servicio que presta.

Cuando seas tú quien pregunte, pide un **ejemplo**, no una definición:
*"muéstrame algo que un usuario hace en este sistema, de principio a fin"*.
Una definición la improvisa cualquiera. Un ejemplo, no.

Y anota la respuesta delante de quien respondió. Una descripción de sistema
que no se escribió en el momento se convierte, dos semanas después, en dos
descripciones distintas.
:::

## Tres programas queriendo el mismo dato

Antes de decidir nada técnico, vale entender por qué la Casa Amarela
necesita más que una pantalla nueva.

Hoy existe un solo programa: ese monitor gris, en esa mesa, detrás de ese
mostrador. Es el sistema entero. Quien no esté parado frente a Vera no puede
consultar nada.

Lo que la asociación compró con los sesenta y ocho mil son tres cosas:

| Quién lo usa | Qué necesita hacer |
|---|---|
| Vera, en el mostrador | registrar libros, prestar, recibir devoluciones |
| el vecino, en el celular | ver el acervo y sus propios préstamos |
| el tótem de la entrada | buscar un título y decir si hay ejemplar libre |

Tabla: Tres pantallas distintas, un solo acervo.

Son tres programas distintos, escritos por personas distintas, posiblemente
en lenguajes distintos. Y los tres necesitan la misma información y las
mismas reglas. Si cada uno habla con los datos a su manera, la regla de
"¿se puede prestar?" va a existir en tres versiones — y van a divergir a
tres velocidades distintas.

La salida es tener **un** programa que sabe las reglas, y acordar una forma
de que los otros tres le pidan cosas.

Esa "forma acordada" tiene nombre.

:::term API
*Application Programming Interface*, interfaz de programación. Es un
contrato entre dos programas: uno sabe hacer algo, el otro necesita que se
haga, y existe una forma acordada de pedir y de responder.
:::

Vera es una API desde hace treinta y un años y nadie la llamó nunca así.
Llegas al mostrador, dices el nombre del libro y muestras el carnet; ella
responde con el libro, o con "está prestado, vuelve el jueves". No
necesitas saber dónde está el estante, ni cómo decide el plazo. Necesitas
saber **qué pedir** y **en qué formato responde**.

Es exactamente eso lo que vamos a escribir. La diferencia es que el pedido
va a llegar por la red, y la respuesta va a salir en un texto que otro
programa puede leer.

## Cómo un programa le pide algo a otro

Cuando la aplicación del vecino quiere registrar un préstamo, manda por la
red un bloque de texto parecido a este:

```text
POST /prestamos
Content-Type: application/json

{"ejemplar_id": 812, "lector_id": 47}
```

Son tres partes, y todas tienen sentido.

La primera línea dice **qué hacer** (`POST`, que significa "crea algo
nuevo") y **dónde** (`/prestamos`). La segunda dice en qué formato está
escrito el pedido. Después de una línea en blanco viene el pedido en sí:
qué ejemplar, para qué lector.

El `POST` es uno de los cinco verbos que vas a usar en todo el libro:

| Verbo | Significa | Ejemplo |
|---|---|---|
| `GET` | dame | `GET /libros` |
| `POST` | crea uno nuevo | `POST /prestamos` |
| `PUT` | reemplaza entero | `PUT /libros/12` |
| `PATCH` | cambia una parte | `PATCH /libros/12` |
| `DELETE` | elimina | `DELETE /libros/12` |

Tabla: Cinco verbos cubren casi todo lo que hace una API.

Fíjate en la dirección: `/prestamos`, y no `/crearPrestamo`. El verbo ya
está afuera, en la primera palabra. Quien mete el verbo dentro de la
dirección termina con `/crearPrestamo`, `/renovarPrestamo` y
`/devolverPrestamo` — tres direcciones para la misma cosa, y ninguna
combinable con nada.

Y toda respuesta empieza con un número de tres dígitos:

| Rango | Quiere decir | Los que aparecen en el proyecto |
|---|---|---|
| `2xx` | salió bien | `200` (aquí está), `201` (lo creé), `204` (hecho, sin contenido) |
| `4xx` | se equivocó quien pidió | `404` (no existe), `422` (dato inválido) |
| `5xx` | se equivocó quien respondió | `500` (me rompí) |

Tabla: El número es lo primero que lee el otro programa — muchas veces es lo
único.

Una aplicación no interpreta la frase "no fue posible realizar la
operación". Mira el número, y decide entre mostrar un error, reintentar o
pedirle al usuario que inicie sesión. Devolver `200` junto con un mensaje de
error es el equivalente a decir "sí" negando con la cabeza.

## El campo que lo confundía todo

El miércoles, Dedé se sentó con Vera para entender cómo estaba organizado
el acervo. La pantalla de registro del Sistema tenía, entre los dieciocho
campos, uno llamado **Cantidad**.

Prestar, en el Sistema, le restaba uno a ese campo. Devolver le sumaba uno.

Funciona. Funcionó durante quince años.

Entonces empezó a preguntar.

:::story Cinco preguntas
— ¿Qué ejemplar de *O Cortiço* tiene Dona Marlene?

Vera abrió el cajón del mostrador y sacó una ficha de papel rayado, de esas
de fichero, con un número escrito a mano en la esquina superior: **2.117**.

— Este.

— ¿Y el Sistema lo sabe?

— El Sistema sabe que hay tres.

— ¿Y cuál de los tres está roto?

— El 2.119. Tiene una página suelta en el medio.

— ¿Y cuál desapareció en 2017?

— El 2.118. Se lo llevaron y no volvió.

— ¿El Sistema lo sabe?

— El Sistema sabe que hay tres.

Dedé volvió a mirar la pantalla. **Cantidad: 3**.

Había tres fichas de papel en el cajón de Vera y un número en la pantalla.
Las fichas respondían cinco preguntas. El número respondía media.
:::

## Una cosa, varias cosas y un acontecimiento

Dos frases que parecen iguales y no lo son:

> "La biblioteca tiene *O Cortiço*."
>
> "La biblioteca tiene tres *O Cortiço*."

La primera habla del **libro**: título, autor, editorial, año, tema. Existe
uno solo, y no se puede prestar. Nadie se lleva un título a casa.

La segunda habla del **ejemplar**: el objeto físico, con número de
registro, estado de conservación y una etiqueta pegada en el lomo. Es él el
que sale por la puerta, se rompe, desaparece y vuelve.

:::term Número de registro
El número que identifica cada objeto del acervo, uno por uno. Es lo que
Vera escribe a mano en la esquina de la ficha. Dos copias del mismo libro
tienen el mismo título y números de registro distintos.
:::

El campo **Cantidad** es lo que queda cuando alguien funde los dos
conceptos en uno. Guarda el *conteo* y tira la *identidad* — y la identidad
es justamente lo que pedían las cinco preguntas.

Falta un tercer concepto, que en el Sistema no existe en ninguna parte: el
**préstamo**. No es una característica de nada. Es un acontecimiento: tal
ejemplar salió con tal lector, tal día, para volver tal otro. Terminó, se
volvió historial — y el historial es de donde salen todas las preguntas
interesantes que la Casa Amarela nunca pudo responder.

:::diagram type="blocks" caption="Un título, varios objetos, y un acontecimiento que une un objeto con una persona."
rows:
  - [{ text: "Libro", note: "O Cortiço · Aluísio Azevedo · 1890" }]
  - [{ text: "Ejemplar 2.117", note: "buen estado" }, { text: "Ejemplar 2.118", note: "extraviado en 2017" }, { text: "Ejemplar 2.119", note: "página suelta" }]
  - [{ text: "Préstamo", note: "ejemplar 2.117 · Marlene · salió 04/02 · vuelve 18/02" }]
:::

Tres nombres en lugar de un campo. A cambio, las cinco preguntas de Vera
dejan de depender del cajón.

Y la tal **Cantidad** ya no necesita guardarse: pasa a **contarse** —
cuántos ejemplares de este libro no están prestados ahora. Parece más
trabajo y es menos, por un motivo que vale la pena recordar: un número
guardado puede divergir de la realidad, un número contado no. Cuando Dedé
lo revisó, el campo Cantidad estaba mal en catorce libros, y nadie sabía
desde cuándo.

:::art caption="Un número en la pantalla; tres objetos distintos en el mundo."
src="um-numero-na-tela-tres-objetos-diferentes-no-mundo.png"
Viñeta editorial minimalista sobre fondo blanco. A la izquierda, un monitor
antiguo de tubo que muestra un único campo grande: "Cantidad: 3". A la
derecha, tres ejemplares muy distintos del mismo libro: uno nuevo, uno roto
con páginas sueltas, y un tercero representado solo por un rectángulo
punteado vacío con una etiqueta caída. Entre los dos lados, una flecha fina
que solo va de derecha a izquierda. Pocos elementos, trazo de revista de
tecnología, humor seco.
:::

## Instalar y comprobar

Tres cosas, todas gratuitas, y una prueba para cada una.

Primero, el lenguaje:

```text
$ php -v
PHP 8.3.14 (cli) (built: Nov 21 2026 09:42:15) (NTS)
Copyright (c) The PHP Group
Zend Engine v4.3.14, Copyright (c) Zend Technologies
```

Lo único que importa ahora es el principio de la primera línea. Si aparece
`8.3` o superior, está listo. Si aparece `7.4`, la mitad de lo que enseña
este libro no va a correr en tu máquina.

| Sistema | Cómo instalar |
|---|---|
| Ubuntu / Debian | agrega el PPA `ondrej/php`, después `apt install php8.3-cli` |
| macOS | `brew install php` |
| Windows | descárgalo de `windows.php.net/download`, o usa WSL2 con Ubuntu |

Tabla: En Windows, WSL2 ahorra dolores de cabeza cuando el proyecto sume una
base de datos — el entorno queda parecido al del servidor.

Después, Composer, que es el instalador de bibliotecas de PHP:

```text
$ composer --version
Composer version 2.8.4 2026-10-30 12:18:44
```

Solo entra en escena cuando el proyecto tenga dependencias, pero instalarlo
ahora evita frenar todo en medio de un tema para resolver una instalación.

Y un editor: VS Code, PhpStorm, Vim, Zed. Cualquiera sirve, siempre que
puedas abrir una carpeta y guardar archivos `.php`.

:::practice
Ejecuta `php -m`. Sale una lista de nombres en columna: son las
**extensiones** compiladas en tu PHP, es decir, las partes opcionales del
lenguaje que alguien decidió incluir cuando armó ese paquete.

Busca cuatro: `mbstring`, `json`, `intl` y `pdo_mysql`. Las dos primeras las
usas ya en las próximas semanas de lectura; las otras dos hacen falta
cuando el acervo salga de la memoria del programa y pase a una base de
datos. Si falta alguna, instálala ahora — en Ubuntu,
`apt install php8.3-mbstring`, y así con las demás.

Descubrir que falta una extensión hoy cuesta cinco minutos. Descubrirlo en
medio de un capítulo cuesta una tarde y las ganas de seguir.
:::

:::summary
- "¿Qué hace este sistema hoy?" traba la reunión, y para eso sirve. Pide
	un ejemplo, no una definición.
- Una API es un contrato: una forma acordada de que un programa pida y otro
	responda.
- El verbo (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) dice la intención; la
	dirección dice el objetivo. El verbo no va en la dirección.
- El código de tres dígitos es lo primero que lee el otro programa.
- Libro es el título, ejemplar es el objeto, préstamo es el acontecimiento.
	Fundir los dos primeros cuesta una reescritura.
- Un número contado no diverge de la realidad; un número guardado, sí.
:::

:::milestone
Entorno instalado y comprobado, dominio entendido. De aquí en adelante, todo
lo que aparezca en el libro corre en tu máquina.
:::

:::exercise level=1
PHP acepta código directamente en la línea de comandos con la opción `-r`,
sin necesidad de crear un archivo. Por ejemplo:

```text
$ php -r "echo 2 + 2;"
4
```

Usa `-r` para imprimir la versión de PHP, que está guardada en un valor
predefinido llamado `PHP_VERSION`. Después averigua dónde está el archivo de
configuración de tu PHP, con `php -i | grep "Loaded Configuration"`. Anota
los dos.

:::answer
```text
$ php -r "echo PHP_VERSION;"
8.3.14

$ php -i | grep "Loaded Configuration"
Loaded Configuration File => /etc/php/8.3/cli/php.ini
```

`php -i` vuelca la configuración entera, que son unas quinientas líneas;
`grep` filtra la que interesa. En Windows, fuera de WSL, cámbialo por
`php -i | findstr "Loaded"`.

Guarda la ruta del `php.ini`. Es el archivo que decide, entre otras cosas,
si los errores aparecen en pantalla o desaparecen en silencio.
:::

:::exercise level=2
Escribe el verbo y la dirección de cada operación del acervo: listar los
libros, buscar un libro específico, registrar, modificar y eliminar. Después
escribe las tres operaciones de préstamo: prestar, renovar y devolver.

:::answer
Las cinco del acervo salen directo de la tabla de verbos:

```text
GET    /libros          lista
GET    /libros/12       busca uno
POST   /libros          registra
PUT    /libros/12       reemplaza
DELETE /libros/12       elimina
```

Las tres de préstamo son más interesantes, porque renovar y devolver no son
"crear", "modificar" ni "eliminar" — son acciones. La salida más usada es
tratar la acción como una cosa que se crea:

```text
POST   /prestamos                  presta
POST   /prestamos/7/renovacion     renueva
POST   /prestamos/7/devolucion     devuelve
```

Si tu respuesta fue `POST /renovarPrestamo/7`, funciona igual. La diferencia
aparece en la operación número cien, cuando el sistema tiene cuarenta
direcciones con verbo en el nombre y nadie puede adivinar ninguna sin
consultar la documentación.
:::

:::exercise level=3
Vera quiere un informe de "libros más prestados" para decidir qué comprar
con el presupuesto del semestre. Un libro tiene varios ejemplares. Si el
informe cuenta préstamos por ejemplar, ¿responde la misma pregunta?

:::answer
No la responde, y la diferencia es exactamente la de este capítulo.

Contar por **ejemplar** responde "qué copia salió más veces". Es una
pregunta de conservación: el ejemplar más prestado es el que se va a romper
primero, y el que necesita encuadernación.

Contar por **libro** — sumando los préstamos de todos los ejemplares de ese
título — responde "qué quiere leer la gente". Es una pregunta de
adquisición, y es la que hizo Vera.

Las dos son legítimas y sirven a decisiones distintas. El problema es
entregar una creyendo que se entregó la otra, lo que pasa con una
frecuencia incómoda, porque el nombre del informe suele ser el mismo en los
dos casos.

Hay todavía un tercer número escondido ahí, y es el mejor de los tres: el
título más **buscado** no es el más prestado. Es el que más aparece en
reservas porque nunca tiene un ejemplar libre — y ese no está en ninguno de
los dos conteos. Comprar según el ranking de préstamos significa comprar
más copias de lo que ya circula bien, y ninguna de lo que nadie logra
llevarse.
:::

:::story ¿Escala a cuántos usuarios?
El jueves, el Dr. Aurélio se detuvo en el escritorio de Dedé.

— Me dijeron que fuiste a la biblioteca.

— Fui a ver el sistema viejo.

— ¿Y cómo es?

— Es un PHP de 2009 en un servidor que hospeda el sobrino de una vecina.

El Dr. Aurélio asintió despacio, como quien está armando una diapositiva
mentalmente.

— ¿Escala a cuántos usuarios?

— Mil doscientos. Del barrio.

— Mmm. — Una pausa. — ¿Pensaste en microservicios?

Dedé pensó en decir que la biblioteca tiene tres conceptos y una
computadora.

— Lo voy a evaluar.

En el cuaderno de Tainá, ese día, entró la primera línea de una lista que
iba a crecer hasta marzo: *"preguntar el tamaño antes de elegir la
herramienta"*.
:::
