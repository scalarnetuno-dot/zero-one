---
source_hash: b1e0df09c391
title: "Clases y objetos"
number: 17
slug: classes-e-objetos
part: p3
kicker: "El informe mostró un ejemplar de ningún libro. El dato estaba bien en la base: el array era el que había perdido la clave."
goal: >-
  Cambiar el array asociativo por un tipo con nombre cuando el formato es
  conocido: declarar una clase, crear objetos con constructor promovido,
  usar propiedades tipadas, comparar objetos y reconocer cuándo el objeto
  no compensa.
---

:::story Un ejemplar de ningún libro
Vera imprimió el informe de los ejemplares en restauración para llevarlo a
la reunión de la asociación. Once líneas. En la sexta, el registro 2117
aparecía con el título en blanco.

—¿Qué libro es este?

—Este es... —Dedé bajó por la pantalla— ...ninguno.

—¿Cómo que ninguno?

En la base, el 2117 era un *Vidas Secas* de tapa dura, con el `libro_id`
correcto y la clave foránea en su lugar. El problema estaba treinta líneas
más arriba, en el PHP. El informe armaba un índice de títulos con una
consulta aparte, y esa consulta traía solo los libros de literatura.

*Vidas Secas* estaba clasificado como libro de texto desde 2011.

—¿Y el sistema no se quejó?

—Se quejó. —Dedé abrió el log y leyó en voz alta—. *Warning: Undefined
array key 431.*

—¿Eso apareció en mi pantalla?

—Eso apareció en un archivo que nadie abre.
:::

## El array acepta cualquier clave

Un array asociativo no tiene formato. Acepta lo que le pidas, y lo que le
pidas mal.

```php title="claves.php" numbered
<?php

$libro = ['id' => 12, 'titulo' => 'Dom Casmurro', 'anio' => 1899];

echo '[', $libro['titlo'], "]\n";
```

```text
Warning: Undefined array key "titlo" in /app/claves.php on line 5
[]
```

Un aviso, un valor nulo y el programa sigue. Si ese `echo` está dentro de
un informe de once líneas, el resultado es una línea en blanco en medio de
diez correctas.

La escritura es peor, porque ni siquiera avisa:

```php
$libro['precio'] = 39.90;
$libro['titulo_'] = 'Dom Casmurro';
```

Silencio en los dos casos. El array ahora tiene cinco claves, dos de ellas
inventadas, y nada en el programa sabe que eso es un problema.

:::key
El array es la estructura correcta cuando el formato es **desconocido o
variable**: las filas que volvieron de una consulta, los filtros que marcó
el usuario, una lista de cualquier tamaño.

Se vuelve malo cuando el formato es **conocido y repetido**: cuando las
mismas cuatro claves atraviesan siete funciones, y cada función tiene que
confiar en que las otras seis escribieron bien el nombre.
:::

## Una clase es un formato con nombre

```php title="Libro.php" numbered
<?php

class Libro
{
    public string $titulo;
    public int $anio;
}
```

Tres palabras nuevas, y ninguna es complicada.

`class` declara un formato. `Libro` es su nombre. Dentro de las llaves
están las **propiedades**: los campos que tiene todo libro, cada uno con el
tipo que acepta.

Crear uno es `new`:

```php title="catalogo.php" numbered
<?php

require 'Libro.php';

$libro = new Libro();
$libro->titulo = 'Dom Casmurro';
$libro->anio = 1899;

echo $libro->titulo, "\n";
```

```text
Dom Casmurro
```

La flecha `->` es como se llega a una propiedad. No es un punto: en PHP el
punto une texto, y eso es lo primero que la memoria de quien viene de otro
lenguaje insiste en equivocar.

:::term Clase y objeto
La **clase** es la ficha de catalogación en blanco: dice qué campos existen
y qué cabe en cada uno. El **objeto** es una ficha llena.

Una clase, muchos objetos. El molde no guarda ningún dato; cada objeto
guarda los suyos.
:::

Ahora repite el error de la sección anterior:

```php
echo '[', $libro->titlo, "]\n";
```

```text
Warning: Undefined property: Libro::$titlo
in /app/catalogo.php on line 10
[]
```

Todavía es un aviso, pero fíjate en la diferencia del mensaje: dice el
nombre de la clase. Ya no es "alguna clave en algún array": es
`Libro::$titlo`, y la clase `Libro` está en un solo archivo, con las
propiedades listadas en cinco líneas.

Y la escritura cambió de comportamiento:

```php
$libro->precio = 39.90;
```

```text
Deprecated: Creation of dynamic property Libro::$precio is deprecated
in /app/catalogo.php on line 11
```

PHP avisa que crear una propiedad fuera de la lista es un recurso en vías
de extinción. El array nunca avisó nada.

## El objeto que nace a medias

Hay un problema en el código de arriba, y aparece cuando alguien se olvida
de una línea:

```php title="catalogo.php" numbered
<?php

require 'Libro.php';

$libro = new Libro();
$libro->titulo = 'Dom Casmurro';

echo $libro->anio;
```

```text
Fatal error: Uncaught Error: Typed property Libro::$anio must not be
accessed before initialization in /app/catalogo.php:8
```

Una propiedad tipada no tiene valor predeterminado. No es `null`, no es
`0`: **todavía no existe**, y PHP prefiere detenerse antes que inventar un
valor.

Eso es bueno, y es insuficiente. El error ocurre en el momento de la
lectura, que puede estar treinta líneas —o tres pantallas— después del
lugar donde el objeto se armó mal.

El lugar correcto para exigir los datos es el nacimiento del objeto.

## El constructor

```php title="Libro.php" numbered
<?php

class Libro
{
    public string $titulo;
    public int $anio;

    public function __construct(string $titulo, int $anio)
    {
        $this->titulo = $titulo;
        $this->anio = $anio;
    }
}
```

`__construct` es un método con nombre reservado: PHP lo llama solo, cada
vez que alguien escribe `new Libro(...)`, pasándole los argumentos.

`$this` es el objeto en el que el método se está ejecutando en ese
momento. Dentro del constructor de un libro, `$this` es ese libro, y
`$this->titulo` es su propiedad, no el parámetro.

```php
$libro = new Libro('Dom Casmurro', 1899);
```

Ahora el objeto nace entero o no nace:

```php
$libro = new Libro('Dom Casmurro');
```

```text
Fatal error: Uncaught ArgumentCountError: Too few arguments
to function Libro::__construct(), 1 passed and exactly 2 expected
```

Y nace con los tipos correctos:

```php
$libro = new Libro('Dom Casmurro', 'mil ochocientos');
```

```text
Fatal error: Uncaught TypeError: Libro::__construct():
Argument #2 ($anio) must be of type int, string given
```

:::pitfall
`'mil ochocientos'` fue rechazado. `'1899'` no lo sería: un texto que *es*
un número entero pasa por la puerta y llega al otro lado convertido, como
`int(1899)`.

Es la conversión automática de PHP trabajando donde no la pediste. No te va
a salvar de recibir `'1899'` de un formulario: te va a entregar el entero
correcto, y esa es justamente la razón por la que no notas cuando entrega
el equivocado.
:::

## El constructor en una línea

Escribir el nombre de cada propiedad tres veces —en la declaración, en el
parámetro y en la asignación— es trabajo de mecanógrafo. PHP 8 lo resuelve:

```php title="Libro.php" numbered
<?php

class Libro
{
    public function __construct(
        public string $titulo,
        public int $anio,
    ) {}
}
```

Esto hace **exactamente** lo que hacía la versión anterior. Escribir
`public` antes del parámetro le dice a PHP: declara esta propiedad y guarda
este valor en ella. Las tres líneas del cuerpo desaparecen porque no quedó
nada por hacer.

La coma después del último parámetro está permitida y es recomendable:
agregar un campo mañana se vuelve una línea nueva en lugar de dos líneas
modificadas.

:::term Promoción de propiedades
*Constructor property promotion*, en su nombre oficial. Está en PHP desde
la versión 8.0 y es la forma normal de escribir una clase de datos hoy.

Vas a encontrar mucho código con la versión larga: no está mal, solo es
anterior. Las dos producen el mismo objeto.
:::

## Un ejemplar sin libro deja de ser posible

Esa era la pregunta de Vera. En el Sistema, un ejemplar es un array, y un
array al que le falta la clave `libro_id` es un array normal.

Con una clase, el problema cambia de lugar:

```php title="Ejemplar.php" numbered
<?php

class Ejemplar
{
    public function __construct(
        public int $registro,
        public Libro $libro,
        public string $condicion = 'bueno',
    ) {}
}
```

Dos cosas para notar.

La primera: el tipo de `$libro` es `Libro`. Una clase es un tipo tan válido
como `int` o `string`, y PHP lo fiscaliza de la misma forma.

La segunda: `$condicion` tiene `= 'bueno'`, un valor predeterminado. Quien
no lo informe recibe `'bueno'`, que es la condición en la que un ejemplar
entra al acervo. Lo predeterminado es para lo que tiene respuesta obvia;
`$registro` y `$libro` no la tienen.

```php
$ejemplar = new Ejemplar(2117);
```

```text
Fatal error: Uncaught ArgumentCountError: Too few arguments to
function Ejemplar::__construct(), 1 passed and exactly 2 expected
```

Ya no es una cuestión de disciplina del equipo. Es una cuestión de que el
programa corra.

## De la base al objeto

Las consultas siguen devolviendo arrays: eso es lo que hace PDO, y está
bien, porque en ese punto el formato todavía es el de la base.

La traducción ocurre en una función, en un solo lugar:

```php title="acervo.php" numbered
<?php

require 'Libro.php';
require 'Ejemplar.php';

function libroDeFila(array $fila): Libro
{
    return new Libro($fila['titulo'], (int) $fila['anio']);
}
```

```php title="listar.php" numbered
<?php

require 'conexion.php';
require 'acervo.php';

$filas = $pdo->query(
    'SELECT titulo, anio FROM libros ORDER BY titulo'
)->fetchAll();

$libros = [];

foreach ($filas as $fila) {
    $libros[] = libroDeFila($fila);
}

echo $libros[0]->titulo, "\n";
```

El `(int)` en la conversión del año no es decoración: MySQL devuelve
números como texto, y `'1899'` se volvería `int` en la puerta del
constructor de todos modos. Escribir la conversión deja visible la
intención y hace que el programa se comporte igual el día en que el tipado
se vuelva estricto.

:::key
La frontera es siempre la misma: **array hasta la traducción, objeto
después de ella**.

Una función que recibe `array $fila` y devuelve un objeto es el único lugar
del programa que necesita saber cómo se llaman las columnas. Cuando una
columna cambie de nombre, es ahí adonde vas a ir.
:::

## Comparar objetos

Dos signos, dos preguntas distintas.

```php title="comparar.php" numbered
<?php

require 'Libro.php';

$a = new Libro('Dom Casmurro', 1899);
$b = new Libro('Dom Casmurro', 1899);
$c = $a;

var_dump($a == $b);
var_dump($a === $b);
var_dump($a === $c);
```

```text
bool(true)
bool(false)
bool(true)
```

- `==` pregunta: **¿son iguales?** Misma clase y propiedades iguales una
  por una.
- `===` pregunta: **¿son el mismo?** El mismo objeto, no una copia con el
  mismo contenido.

`$c = $a` no copió nada. Las dos variables apuntan al mismo objeto, y por
eso `$a === $c` es verdadero.

:::pitfall
Para las cosas que la base identifica por `id`, ninguna de las dos
preguntas es la que quieres. Dos objetos `Lector` cargados en momentos
distintos pueden tener el mismo `id` y nombres distintos, porque alguien
corrigió el registro en el medio.

`==` diría que son distintos. `===` también. Y son la misma persona.

Cuando la identidad viene de un `id`, compara el `id`.
:::

## `__toString`, y el atajo que cobra después

Un objeto no se vuelve texto solo:

```php
echo $libro;
```

```text
Fatal error: Uncaught Error: Object of class Libro could not be
converted to string
```

Puedes enseñarle:

```php title="Libro.php" numbered
<?php

class Libro
{
    public function __construct(
        public string $titulo,
        public int $anio,
    ) {}

    public function __toString(): string
    {
        return "{$this->titulo} ({$this->anio})";
    }
}
```

```text
$ php catalogo.php
Dom Casmurro (1899)
```

`__toString` es útil para logs y mensajes de error. Es uno de varios
métodos con dos guiones bajos delante que PHP llama solo en situaciones
específicas.

Y es aquí donde conviene detenerse.

:::pitfall
Existe uno de esos métodos, `__get`, que intercepta la lectura de
cualquier propiedad que no exista y te deja decidir qué devolver. Con él,
un objeto vuelve a aceptar `$libro->titlo` sin quejarse.

Es decir: deshace, en cuatro líneas, exactamente lo que este capítulo
entero vino a hacer. Un error que PHP señalaba con nombre y línea vuelve a
ser una pantalla en blanco.

Eso no quiere decir que `__get` nunca sirva. Quiere decir que es la
respuesta a un problema muy específico, y que "no quiero declarar las
propiedades" no es ese problema.
:::

## Cuándo el objeto no vale la pena

No toda estructura merece una clase, y la regla es la misma del principio
del capítulo, al revés.

**Formato que no controlas.** El JSON de una integración, un CSV cuyas
columnas cambian en cada exportación, los filtros que vinieron de un
formulario. Ahí el array es honesto: el formato de verdad es variable, y
fingir que no lo es solo empuja la sorpresa a otro lugar.

**Clase que no rechaza nada.** Si la clase tiene seis propiedades públicas,
ninguna regla, ningún cálculo y ningún tipo interesante, es un array con
más líneas y una ficha de catalogación. La ganancia aparece cuando el tipo
**impide** algo, como el `Ejemplar` que no nace sin `Libro`.

**Script de una sola vez.** El programa que corre una tarde para revisar
una importación no necesita modelado. Necesita terminar.

:::note En tu carrera
"Vamos a crear una clase para esto" es una propuesta que suele aceptarse
sin discusión y ejecutarse sin ganancia, y, tres meses después, el
proyecto tiene cuarenta clases que solo guardan y devuelven.

Cuando propongas el cambio, trae junto la falla concreta que impide. "Una
clase `Ejemplar` habría impedido el informe en blanco de la sexta línea" es
un argumento. "Queda más organizado" es una preferencia, y la preferencia
no sobrevive a la primera semana apretada.

Lo mismo vale al revés: cuando alguien lo proponga, pregunta qué error real
desaparece. Si la respuesta tarda, la clase probablemente todavía no tiene
trabajo que hacer.
:::

:::tree title="Dónde estamos ahora"
acervo/
  composer.json
  composer.lock
  vendor/
  .gitignore
  Libro.php       # clase, con __toString
  Ejemplar.php    # clase, exige un Libro
  acervo.php      # traduce fila de la base en objeto
  conexion.php
  multa.php
  listar.php
  buscar.php
  registrar.php
  prestar.php
  devolver.php
  recibo.php
:::

:::summary
- El array no tiene formato: acepta una clave equivocada en la lectura con
  un aviso y en la escritura en silencio.
- `class` declara un formato con nombre; `new` crea un objeto; `->` llega a
  una propiedad.
- Una propiedad tipada no tiene valor predeterminado: leerla antes de
  asignarla es un error fatal, y eso juega a favor.
- `__construct` lo llama el `new`; `$this` es el objeto que se está
  ejecutando.
- La promoción de propiedades escribe el constructor y las propiedades en
  una sola declaración.
- Una clase es un tipo: `Ejemplar` puede exigir un `Libro`, y PHP lo
  cobra.
- Array hasta la traducción, objeto después de ella, y la traducción vive
  en un solo lugar.
- `==` compara contenido, `===` compara identidad; para una entidad con
  `id`, compara el `id`.
- Una clase sin ninguna regla es un array con más líneas.
:::

:::checkpoint
Declaras una clase con constructor promovido, creas objetos a partir de las
filas de la base, sabes por qué un `Ejemplar` no puede nacer sin `Libro`,
distingues `==` de `===` entre objetos y puedes defender —o rechazar— el
cambio de un array por una clase con un ejemplo concreto.
:::

:::exercise level=1
Escribe la clase `Lector` con `nombre` (texto), `documento` (texto) y
`registradoEn` (texto en el formato `Y-m-d`), usando constructor promovido.

Después responde: ¿por qué `documento` es `string` y no `int`, si es una
secuencia de once dígitos?

:::answer
```php title="Lector.php" numbered
<?php

class Lector
{
    public function __construct(
        public string $nombre,
        public string $documento,
        public string $registradoEn,
    ) {}
}
```

`documento` es texto porque **no es un número**: es un identificador hecho
de dígitos. Dos pruebas rápidas separan una cosa de la otra.

La primera: ¿tiene sentido sumar dos documentos? No.

La segunda, más práctica: el CPF `012.345.678-90` guardado como entero se
vuelve `12345678 90` sin el cero del principio, porque el cero a la
izquierda no existe en un número. El acervo ya tuvo ese problema con el
`registro` hasta que alguien notó que los registros antiguos empezaban con
cero.
:::

:::exercise level=2
Toma el `listar.php` de la sección de la traducción y agrégale el armado
de `Ejemplar` a partir de una consulta con `JOIN`, usando la clase
`Ejemplar` que exige un `Libro`.

La consulta:

```sql
SELECT e.registro, e.condicion, l.titulo, l.anio
FROM ejemplares e
JOIN libros l ON l.id = e.libro_id
ORDER BY l.titulo
```

Después imprime cada ejemplar en una línea, usando el `__toString` de
`Libro`.

:::answer
```php title="acervo.php" numbered
<?php

require 'Libro.php';
require 'Ejemplar.php';

function ejemplarDeFila(array $fila): Ejemplar
{
    return new Ejemplar(
        (int) $fila['registro'],
        new Libro($fila['titulo'], (int) $fila['anio']),
        $fila['condicion'],
    );
}
```

```php title="listar.php" numbered
<?php

require 'conexion.php';
require 'acervo.php';

$sql = 'SELECT e.registro, e.condicion, l.titulo, l.anio
        FROM ejemplares e
        JOIN libros l ON l.id = e.libro_id
        ORDER BY l.titulo';

foreach ($pdo->query($sql) as $fila) {
    $ejemplar = ejemplarDeFila($fila);
    echo $ejemplar->registro, ' — ', $ejemplar->libro, "\n";
}
```

```text
2117 — Vidas Secas (1938)
 843 — Dom Casmurro (1899)
```

El `echo $ejemplar->libro` funciona porque `Libro` tiene `__toString`.

Y fíjate en lo que desapareció: ya no existe un índice de títulos armado
aparte, que es de donde nació el informe en blanco. El `JOIN` trae el
título junto con el ejemplar, y el constructor no deja pasar uno sin el
otro.
:::

:::exercise level=3
Este código corre sin error e imprime algo inesperado. Di qué imprime y
por qué, antes de ejecutarlo.

```php title="carrito.php" numbered
<?php

require 'Libro.php';

$original = new Libro('Dom Casmurro', 1899);
$copia = $original;

$copia->anio = 1900;

echo $original->anio, "\n";
var_dump($original == $copia);
```

Después, investiga qué hace la palabra `clone` y explica por qué tampoco
resolvería el caso en que `Libro` guardara un objeto dentro.

:::answer
Imprime `1900` y `bool(true)`.

`$copia = $original` no copió el objeto. Los objetos se asignan por
referencia: las dos variables apuntan al mismo objeto, y cambiar el año por
un extremo lo cambia por los dos. Por eso `==` responde `true`: está
comparando el objeto consigo mismo.

`clone $original` crea un objeto nuevo con las mismas propiedades. Resuelve
este caso: `$copia = clone $original` haría que el `echo` imprimiera
`1899`.

Donde no resuelve: la copia es **superficial**. Si `Libro` guardara un
objeto `Editorial` dentro, la copia recibiría la misma `Editorial`, no una
copia de ella. Cambiar el nombre de la editorial por la copia lo cambiaría
en el original, y tendrías el mismo problema un nivel más abajo, ahora más
difícil de ver.

La salida que evita toda la discusión es un objeto que no cambia después de
creado. Sin cambios, la copia y el original no tienen cómo divergir.
:::
