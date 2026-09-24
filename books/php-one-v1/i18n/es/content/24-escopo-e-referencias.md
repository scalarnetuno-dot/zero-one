---
source_hash: e0d853d7372d
title: "Ámbito y referencias"
number: 24
slug: escopo-e-referencias
part: p5
kicker: "La lista de devoluciones del día tenía Dom Casmurro dos veces. Iracema, que había vuelto a las diez, no estaba en ella."
goal: >-
  Saber exactamente qué recibe una función cuando le pasas una variable, un
  array y un objeto; usar una referencia solo cuando es la respuesta; y
  reconocer los dos defectos que deja atrás el &.
---

:::story Dom Casmurro dos veces
Vera imprimió la lista de devoluciones del día a las cinco y media, como
hacía cada tarde, y fue comparándola con la pila del carrito.

—Dom Casmurro aparece dos veces —dijo—. Y la Iracema no aparece. Yo recibí
la Iracema a las diez.

Tainá abrió el script que generaba la lista. Era suyo, del martes.

```php
foreach ($devueltos as &$d) {
    $d['titulo'] = mb_strtoupper($d['titulo']);
}

foreach ($devueltos as $d) {
    echo $d['titulo'], "\n";
}
```

—Solo lo pasé a mayúsculas —dijo—. El segundo bucle solo imprime.

Dedé miró el `&` del primer bucle un rato.

—El segundo bucle no solo imprime.

—No tiene `&`.

—Él no. El primero dejó uno abierto.
:::

## El ámbito, otra vez, con más cuidado

El capítulo @cap:funcoes mostró la regla: una función no ve las variables
de fuera, y las de dentro mueren cuando termina. Quien quiere un valor de
fuera lo recibe por parámetro; quien quiere devolver, devuelve con
`return`.

Esa regla tiene una pregunta escondida, que PHP responde de tres formas
distintas según el tipo del valor: **¿qué recibe exactamente la función?**
¿Una copia del valor, o el mismo valor que estaba fuera?

La respuesta corta:

| Pasas | La función recibe | ¿Cambiarlo dentro cambia el de fuera? |
|---|---|---|
| `int`, `string`, `bool`, `float` | una copia | no |
| array | una copia | no |
| objeto | el mismo objeto | **sí** |
| cualquier cosa con `&` | la propia variable | sí |

Tabla: La tercera línea es la que sorprende a quien viene del capítulo de
arrays. La cuarta es la que este capítulo pide usar poco.

El resto del capítulo es esa tabla, una línea a la vez.

## Valores y arrays: la copia

```php title="copia.php" numbered
<?php

declare(strict_types=1);

function aplicarDescuento(array $prestamo): array
{
    $prestamo['multa'] = intdiv($prestamo['multa'], 2);
    return $prestamo;
}

$p = ['lector' => 47, 'multa' => 720];
$conDescuento = aplicarDescuento($p);

echo $p['multa'], "\n";
echo $conDescuento['multa'], "\n";
```

```text
$ php copia.php
720
360
```

La función recibió una copia del array, modificó la copia y la devolvió.
El `$p` de fuera sigue con 720. Es el comportamiento del capítulo
@cap:arrays: un array asignado a otra variable —o pasado a una función— se
copia.

Copiar ocho mil ejemplares en cada llamada parece caro, y no lo es. PHP
solo copia de verdad **en el momento en que alguien escribe** en la copia.
Mientras la función solo lee, las dos variables apuntan a los mismos datos
en memoria. Eso se llama *copy-on-write*, y es la razón por la que pasar un
array por valor es lo predeterminado, seguro y barato.

## La referencia: `&`

Un `&` antes del parámetro cambia el acuerdo. La función pasa a recibir la
**propia variable** de quien llamó:

```php title="referencia.php" numbered
<?php

declare(strict_types=1);

function aplicarDescuento(array &$prestamo): void
{
    $prestamo['multa'] = intdiv($prestamo['multa'], 2);
}

$p = ['lector' => 47, 'multa' => 720];
aplicarDescuento($p);

echo $p['multa'], "\n";
```

```text
$ php referencia.php
360
```

No hay `return`. La función cambió el `$p` de fuera directamente.

:::term Referencia
Un segundo nombre para la misma variable. Con `&`, el parámetro de la
función y la variable de quien llamó dejan de ser dos cosas: cambiar una es
cambiar la otra.

PHP usa referencias en poquísimas funciones de su propia biblioteca: `sort`
es la más conocida: ordena el array que pasaste, en su lugar, y devuelve
solo `true`.
:::

Las dos versiones hacen la misma cuenta. La primera dice, en la firma, que
devuelve un array nuevo. La segunda dice que cambia lo que recibió, y quien
lee la llamada `aplicarDescuento($p);`, sin nada a la izquierda, tiene que
abrir la función para saber que el `$p` cambió.

:::key
La referencia cambia una línea menos por una pregunta más en cada llamada.
Lo predeterminado en este libro —y en Laravel— es recibir, calcular y
devolver. El `&` queda para el caso raro en que devolver no sirve.
:::

## El `&` que queda abierto

El defecto de la lista de Vera tiene una sola causa, y explica por qué la
regla de arriba es una regla.

```php title="devoluciones.php" numbered
<?php

declare(strict_types=1);

$devueltos = [
    ['titulo' => 'O Cortiço'],
    ['titulo' => 'Dom Casmurro'],
    ['titulo' => 'Iracema'],
];

foreach ($devueltos as &$d) {
    $d['titulo'] = mb_strtoupper($d['titulo']);
}

foreach ($devueltos as $d) {
    echo $d['titulo'], "\n";
}
```

```text
$ php devoluciones.php
O CORTIÇO
DOM CASMURRO
DOM CASMURRO
```

El primer bucle, con `&$d`, hace de `$d` un segundo nombre para cada ítem,
uno a la vez. Cuando termina, `$d` **sigue** siendo el segundo nombre del
último ítem: el de Iracema. La referencia no se deshace con el fin del
bucle.

El segundo bucle usa el mismo nombre, `$d`, sin `&`. En cada vuelta
**asigna** el ítem actual a `$d`. Pero `$d` es Iracema. En la primera
vuelta, Iracema se vuelve O Cortiço. En la segunda, se vuelve Dom Casmurro.
En la tercera, el bucle lee la posición de Iracema —que ahora es Dom
Casmurro— y la escribe sobre sí misma.

La lista no perdió un libro por un error de tipeo. Lo perdió porque una
variable siguió siendo alias de otra cuando ya nadie se acordaba de eso.

La corrección mínima es deshacer la referencia en cuanto termina el bucle:

```php
foreach ($devueltos as &$d) {
    $d['titulo'] = mb_strtoupper($d['titulo']);
}
unset($d);
```

`unset($d)` borra el nombre `$d`, y con él el alias. El ítem de Iracema no
se toca.

La corrección que prefiere este libro no usa `&`:

```php
$devueltos = array_map(
    fn(array $d): array => [
        ...$d,
        'titulo' => mb_strtoupper($d['titulo']),
    ],
    $devueltos,
);
```

El `array_map` del capítulo @cap:funcoes devuelve un array nuevo. No queda
ningún alias con el que pueda tropezar el bucle siguiente.

:::pitfall
El defecto solo aparece cuando el **mismo nombre** se reutiliza después, en
el mismo ámbito. Por eso pasa todas las pruebas que corren el primer bucle
solo, y aparece el día en que alguien agrega, treinta líneas más abajo, un
`foreach` inocente con el nombre que sobraba.

El PHPStan del capítulo @cap:tipagem-estrita no lo acusa. La regla de la
casa sí: un `foreach` con `&` termina con `unset`, siempre, en la línea
siguiente al cierre.
:::

## Objetos: el mismo objeto

Ahora la línea de la tabla que cambia todo lo que viene en el volumen 2.

```php title="objeto.php" numbered
<?php

declare(strict_types=1);

final class Ejemplar
{
    public function __construct(
        public readonly int $registro,
        public string $condicion = 'bueno',
    ) {}
}

function marcarPrestado(Ejemplar $e): void
{
    $e->condicion = 'prestado';
}

$ej = new Ejemplar(2117);
marcarPrestado($ej);

echo $ej->condicion, "\n";
```

```text
$ php objeto.php
prestado
```

No hay `&` en ningún lugar, y el `$ej` de fuera cambió.

Un objeto no se copia cuando se pasa a una función, ni cuando se asigna a
otra variable. Lo que guarda la variable es una **identificación** del
objeto: un número que le dice a PHP dónde está. Pasar `$ej` a la función
pasa una copia de ese número, y la copia apunta al mismo objeto.

```php
$a = new Ejemplar(2117);
$b = $a;
$b->condicion = 'restauracion';

echo $a->condicion;   // restauracion
var_dump($a === $b);  // bool(true)
```

`$a === $b` entre objetos pregunta si es **el mismo** objeto: la
comparación del capítulo @cap:classes-e-objetos. Aquí lo es: hay un objeto,
con dos nombres.

:::key
El array que se pasa se copia; el objeto que se pasa se comparte. Una
función que recibe un objeto y cambia una de sus propiedades cambia el
objeto de quien llamó, sin `&` y sin `return`.

En el volumen 2, eso es el día a día: Laravel le entrega a tu código el
objeto de la petición, el model de la base, el usuario autenticado. Todos
son objetos, y todos son el mismo objeto que el framework y las otras
partes de tu código están sosteniendo.
:::

Es también la razón del `readonly` del capítulo @cap:encapsulamento. Un
objeto compartido que nadie puede cambiar desde fuera —como el `Dinero` del
capítulo @cap:enums-datas-e-valores— no tiene ese problema: cualquier
"cambio" devuelve un objeto nuevo.

## `clone`, y la copia que solo baja un nivel

Cuando de verdad hace falta una copia independiente de un objeto, existe
`clone`:

```php title="clone.php" numbered
<?php

declare(strict_types=1);

final class Lector
{
    public function __construct(public string $nombre) {}
}

final class Prestamo
{
    public function __construct(
        public Lector $lector,
        public int $dias,
    ) {}
}

$original = new Prestamo(new Lector('Marlene'), 14);
$copia = clone $original;

$copia->dias = 7;
$copia->lector->nombre = 'Iolanda';

echo $original->dias, ' ', $original->lector->nombre, "\n";
```

```text
$ php clone.php
14 Iolanda
```

`dias` se copió: cambiarlo en la copia no cambió el original. `lector` no:
`clone` copia las propiedades, y la propiedad `lector` guarda la
identificación de un objeto. La copia recibió la misma identificación y,
con ella, el mismo lector.

Para bajar un nivel, la clase declara qué debe hacer el `clone`:

```php
public function __clone(): void
{
    $this->lector = clone $this->lector;
}
```

`__clone` corre en la copia, justo después de hacerla. En la práctica, este
libro casi no usa `clone`: los objetos de valor inmutables, que devuelven
otro objeto en cada cambio, hacen innecesaria la pregunta.

## `static` y `global`: el ámbito que dura demasiado

Hay dos formas de que una variable sobreviva al final de la función, y el
capítulo @cap:encapsulamento ya advirtió sobre una de ellas.

`global` trae una variable del archivo hacia dentro de la función:

```php
function totalizar(int $valor): void
{
    global $total;
    $total += $valor;
}
```

La función pasa a depender de un nombre que no aparece en la firma, y
cualquier otro archivo puede cambiarlo. Es el `$total_general` del
capítulo @cap:funcoes, "arreglado" de la forma equivocada.

`static` dentro de una función guarda el valor entre una llamada y otra:

```php title="cache.php" numbered
<?php

declare(strict_types=1);

function multaDiaria(): int
{
    static $valor = null;

    if ($valor === null) {
        echo "(leyendo config)\n";
        $valor = 80;
    }

    return $valor;
}

echo multaDiaria(), "\n";
echo multaDiaria(), "\n";
```

```text
$ php cache.php
(leyendo config)
80
80
```

La segunda llamada no leyó la configuración. Útil para un valor caro de
calcular que nunca cambia durante el programa, y peligroso para cualquier
cosa que cambie, porque no hay cómo avisarle a la función de que el valor
guardado quedó viejo.

:::note
En el PHP que atiende al navegador, cada petición empieza de cero: `static`
y `global` mueren al final de ella. En el volumen 2 aparecen procesos que
**no** terminan —el worker de cola, por ejemplo—, y ahí un `static`
guardado en la primera tarea sigue ahí en la milésima. Lo que parece
inofensivo en una petición se vuelve un dato de una persona apareciéndole
a otra.
:::

:::note En tu carrera
"PHP pasa los objetos por referencia" es una frase que vas a oír en
entrevistas y leer en tutoriales. Es casi correcta, y el casi importa: PHP
pasa la **identificación** del objeto por valor. La diferencia aparece en
un solo caso: reasignar el parámetro dentro de la función
(`$e = new Ejemplar(9)`) no cambia la variable de fuera; con `&`, la
cambiaría.

Saber explicar ese caso en una frase es el tipo de detalle que separa a
quien memorizó de quien entendió.
:::

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Acervo/Ejemplar.php      # la condición cambia por método, no por fuera
    Prestamos/Dinero.php     # inmutable: nada que clonar
  scripts/
    devoluciones.php         # array_map en lugar del foreach con &
:::

:::summary
- Los escalares y los arrays se pasan por copia; los objetos, por
  identificación: la función recibe el mismo objeto.
- Copiar un array es barato: PHP solo copia de verdad cuando alguien
  escribe.
- `&` hace del parámetro un segundo nombre para la variable de fuera. Úsalo
  poco.
- Un `foreach` con `&` deja el alias vivo después del bucle; `unset` en la
  línea siguiente, o `array_map` en su lugar.
- `clone` copia un nivel; los objetos de dentro siguen compartidos.
  `__clone` baja uno más.
- `global` y `static` hacen que la variable dure más que la función. En un
  proceso que no termina, duran demasiado.
:::

:::checkpoint
Prevés, mirando la firma, si una función puede modificar lo que recibió;
reproduces y corriges el `foreach` con `&` que duplica el último ítem; y
explicas por qué un objeto pasado a una función vuelve modificado sin `&`.
:::

:::exercise level=1
Di qué imprime cada fragmento:

```php
function a(int $x): void { $x = 10; }
$n = 1; a($n); echo $n;

function b(array $l): void { $l[] = 'nuevo'; }
$lista = []; b($lista); echo count($lista);

function c(Ejemplar $e): void { $e->condicion = 'restauracion'; }
$ej = new Ejemplar(1); c($ej); echo $ej->condicion;
```

:::answer
`1`, `0` y `restauracion`.

El entero y el array se copian: las funciones `a` y `b` cambiaron las
copias. El objeto no se copia: `c` cambió el mismo ejemplar que identifica
`$ej`.
:::

:::exercise level=2
Este fragmento de la importación suma la multa de cada lector. Di qué
imprime, por qué, y reescríbelo sin `&`.

```php
$lectores = [
    ['nombre' => 'A', 'multa' => 100],
    ['nombre' => 'B', 'multa' => 200],
];

foreach ($lectores as &$l) {
    $l['multa'] += 50;
}

$total = 0;
foreach ($lectores as $l) {
    $total += $l['multa'];
}
echo $total;
```

:::answer
Imprime `300`, y lo correcto sería `400`.

El primer bucle suma 50 a cada lector —A queda con 150, B con 250— y deja
`$l` como alias del último ítem, el B. El segundo bucle asigna cada ítem a
`$l`. En la primera vuelta, B se vuelve una copia de A: multa 150. En la
segunda, el bucle lee B, que ahora vale 150. El total sale `150 + 150`, y
el array termina con los dos lectores con multa de 150. La multa de B, 250,
desapareció sin ningún error.

```php
$lectores = array_map(
    fn(array $l): array => [...$l, 'multa' => $l['multa'] + 50],
    $lectores,
);
$total = array_sum(array_column($lectores, 'multa'));
```

`array_sum(array_column(...))` suma la columna `multa` de todos: 400. Sin
alias, sin orden de bucle que importe.
:::

:::exercise level=3
Un colega escribió, en el service de préstamo:

```php
function renovar(Prestamo $p, int $dias): Prestamo
{
    $nuevo = $p;
    $nuevo->dias += $dias;
    return $nuevo;
}
```

Dice que la función "no modifica el original, porque devuelve uno nuevo".
Explica lo que pasa, y escribe dos versiones correctas: una con `clone` y
una inmutable.

:::answer
`$nuevo = $p` no crea otro objeto: crea otro nombre para el mismo. La
función modifica el préstamo recibido **y** devuelve ese mismo préstamo.
Quien llamó y guardó el original para comparar "antes y después" ve los dos
iguales.

Con `clone`:

```php
function renovar(Prestamo $p, int $dias): Prestamo
{
    $nuevo = clone $p;
    $nuevo->dias += $dias;
    return $nuevo;
}
```

Inmutable, con la clase diseñada para eso:

```php
final class Prestamo
{
    public function __construct(
        public readonly Lector $lector,
        public readonly int $dias,
    ) {}

    public function renovadoPor(int $dias): self
    {
        return new self($this->lector, $this->dias + $dias);
    }
}
```

La segunda vuelve imposible el defecto: no hay cómo modificar un
`readonly`, y el nombre del método dice que vuelve otro préstamo.
:::
