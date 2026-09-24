---
source_hash: 64faa6f2fbb2
title: "Funciones anónimas y closures"
number: 25
slug: funcoes-anonimas-e-closures
part: p5
kicker: "El informe funcionó hasta que alguien le puso un namespace al archivo. Después de eso, PHP ya no encontraba una función que estaba tres líneas más arriba."
goal: >-
  Pasar funciones como valor sin depender del nombre escrito en un texto,
  usar $this y static dentro de closures, fabricar funciones a partir de
  otras, y combinar reglas pequeñas en una sola: el formato en que el
  volumen 2 va a entregar rutas, filtros y middlewares.
---

:::story Tres líneas más arriba
Tainá había hecho lo que mandaba el capítulo de namespaces: puso
`namespace CasaAmarela\Informes;` al principio del script de atrasados,
junto con los demás. Lo ejecutó para comprobar.

```text
PHP Fatal error: Uncaught TypeError: array_filter(): Argument #2
($callback) must be a valid callback or null, function
"estaAtrasado" not found or invalid function name
```

—La función está ahí —dijo, señalando la pantalla—. Tres líneas más
arriba. `function estaAtrasado`.

Dedé leyó la línea del `array_filter`.

```php
$atrasados = array_filter($prestamos, 'estaAtrasado');
```

—Pasaste un texto.

—Pasé el nombre de la función.

—Pasaste un texto con el nombre. PHP busca ese texto como nombre de
función global. La tuya ahora se llama
`CasaAmarela\Informes\estaAtrasado`.

—Y antes funcionaba.

—Antes el archivo no tenía dirección.
:::

## Una función es un valor

El capítulo @cap:funcoes mostró lo esencial: una función puede guardarse
en una variable, pasarse a otra y llamarse después. `array_map` y
`array_filter` reciben funciones, y el `callable` en la firma dice que el
parámetro acepta "cualquier cosa que se pueda llamar".

El problema del script de Tainá está en esa expresión, "cualquier cosa".
Para PHP, `callable` acepta varias formas distintas:

| Forma | Ejemplo | Se resuelve cuando |
|---|---|---|
| texto con nombre de función | `'estaAtrasado'` | en la llamada, como nombre global |
| texto con clase y método | `'Informe::generar'` | en la llamada |
| array objeto + método | `[$informe, 'filtrar']` | en la llamada |
| closure | `fn($p) => ...` | ya es la función |
| sintaxis de primera clase | `estaAtrasado(...)` | donde está escrita |

Tabla: Las tres primeras son nombres escritos en texto, que PHP busca en el
momento de llamar. Las dos últimas son la propia función.

Un nombre escrito en texto no sabe en qué archivo fue escrito. No pasa por
el `use` ni por el `namespace` del capítulo @cap:namespaces-e-autoload, no
lo encuentra el "renombrar" del editor, y PHPStan no puede comprobar si la
función existe.

## `(...)`: la función, no el nombre

Desde PHP 8.1, cualquier función o método se vuelve un valor escribiendo
`(...)` después del nombre, en lugar de los argumentos:

```php title="atrasados.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Informes;

function estaAtrasado(array $p): bool
{
    return $p['dias'] > 14;
}

$prestamos = [
    ['lector' => 'Marlene', 'dias' => 20],
    ['lector' => 'Iolanda', 'dias' => 3],
];

$atrasados = array_filter($prestamos, estaAtrasado(...));
echo count($atrasados), "\n";

var_dump(estaAtrasado(...) instanceof \Closure);
```

```text
$ php atrasados.php
1
bool(true)
```

`estaAtrasado(...)` no llama a la función: devuelve un objeto `Closure`
que la representa. El nombre se resuelve **ahí**, en la línea en que está
escrito, con el namespace del archivo, igual que una llamada normal.
Renombrar la función renombra esta línea; borrar la función hace que
PHPStan acuse esta línea.

Con métodos, lo mismo:

```php
array_map($formateador->reales(...), $multas);
array_map(Dinero::enCentavos(...), $valores);
```

:::key
Para pasarle una función a otra, pasa la **función**: `nombre(...)`,
`$objeto->metodo(...)`, `Clase::metodo(...)`, o una closure. Nunca su
nombre en un texto. El texto funciona hasta el día en que el archivo recibe
una dirección, y ahí se rompe en la ejecución, no en la lectura.
:::

## `Closure` como tipo

La firma también puede ser más exigente que `callable`:

```php
function aplicarA(array $items, \Closure $operacion): array
{
    return array_map($operacion, $items);
}
```

`\Closure` acepta solo objetos de función —closures y `(...)`—, y rechaza
texto y array. Quien llame a `aplicarA($x, 'strtoupper')` recibe un
`TypeError` en la llamada, con la línea correcta, en lugar de un error
dentro del `array_map`.

La barra antes de `Closure` es la del capítulo @cap:namespaces-e-autoload:
en un archivo con namespace, `Closure` sin barra se buscaría como
`CasaAmarela\Informes\Closure`, que no existe.

## `$this` dentro de la closure

Una closure creada dentro de un método ve el objeto en que nació:

```php title="informe.php" numbered
<?php

declare(strict_types=1);

final class InformeDeAtraso
{
    public function __construct(private int $limiteEnDias) {}

    public function filtro(): \Closure
    {
        return fn(array $p): bool => $p['dias'] > $this->limiteEnDias;
    }
}

$informe = new InformeDeAtraso(14);
$prestamos = [['dias' => 20], ['dias' => 3], ['dias' => 15]];

echo count(array_filter($prestamos, $informe->filtro())), "\n";
```

```text
$ php informe.php
2
```

`$this->limiteEnDias` dentro de la arrow function es el objeto `$informe`.
La closure **se lleva el objeto consigo**: la función devuelta sigue ligada
a él después de que el método terminó.

A veces eso no es lo que se quiere. Una closure que no necesita el objeto,
pero lo carga, mantiene el objeto vivo en memoria mientras ella exista.
Para decir que no usa `$this`, existe `static`:

```php
public function filtroSinObjeto(): \Closure
{
    return static fn(array $p): bool => $p['dias'] > 14;
}
```

Una closure `static` no recibe `$this`. Si intentas usarlo, se rompe:

```text
Error: Using $this when not in object context
```

La regla práctica: la closure que usa el objeto, normal; la que no lo usa,
`static`. En el volumen 2, el framework guarda closures durante mucho
tiempo —rutas, eventos, colas—, y la closure que carga un objeto sin
necesitarlo carga también todo lo que él sostiene.

## Fabricar funciones

Una función puede **devolver** una closure. El resultado es una fábrica:
pasas la configuración una vez, y recibes una función lista para usar
muchas.

Márcia pidió el informe de atrasados con cortes distintos: más de 7 días
para el aviso amable, más de 14 para el cobro, más de 30 para bloquear al
lector. La primera versión tenía tres funciones casi iguales. La segunda
tiene una que fabrica las tres:

```php title="filtros.php" numbered
<?php

declare(strict_types=1);

function atrasadoMasDe(int $dias): \Closure
{
    return fn(array $p): bool => $p['dias'] > $dias;
}

$paraAviso = atrasadoMasDe(7);
$paraCobro = atrasadoMasDe(14);
$paraBloqueo = atrasadoMasDe(30);

$prestamos = [['dias' => 9], ['dias' => 20], ['dias' => 41]];

echo count(array_filter($prestamos, $paraAviso)), "\n";
echo count(array_filter($prestamos, $paraCobro)), "\n";
echo count(array_filter($prestamos, $paraBloqueo)), "\n";
```

```text
$ php filtros.php
3
2
1
```

Cada closure devuelta guardó su `$dias`. Es el `use` por valor del
capítulo @cap:funcoes, solo que la arrow function hace la captura sola, y
cada llamada a `atrasadoMasDe` crea una captura nueva.

:::term Closure
Una función junto con las variables que capturó donde fue creada: por
`use`, por la captura automática de la arrow function, o por el `$this`
del objeto en que nació. En PHP, es un objeto de la clase `Closure`.

La fábrica de funciones es el uso de closures que más aparece en los
frameworks: una configuración se vuelve una función lista.
:::

## Combinar reglas

El informe de cobro necesitaba más de una condición a la vez: atrasado más
de 14 días, lector no exento, libro que no sea de referencia. Tres
funciones pequeñas, y una que combina:

```php title="combinar.php" numbered
<?php

declare(strict_types=1);

function todos(\Closure ...$reglas): \Closure
{
    return function (array $p) use ($reglas): bool {
        foreach ($reglas as $regla) {
            if (!$regla($p)) {
                return false;
            }
        }
        return true;
    };
}

$paraCobrar = todos(
    fn(array $p): bool => $p['dias'] > 14,
    fn(array $p): bool => !$p['exento'],
    fn(array $p): bool => $p['coleccion'] !== 'referencia',
);

$prestamos = [
    ['dias' => 20, 'exento' => false, 'coleccion' => 'general'],
    ['dias' => 20, 'exento' => true, 'coleccion' => 'general'],
    ['dias' => 3, 'exento' => false, 'coleccion' => 'general'],
];

echo count(array_filter($prestamos, $paraCobrar)), "\n";
```

```text
$ php combinar.php
1
```

`\Closure ...$reglas` es un parámetro **variádico**: los tres puntos antes
del nombre dicen que la función acepta todos los argumentos que lleguen en
esa posición, y los junta en un array; aquí, un array de closures. Es el
mismo `...` del desempaquetado del capítulo @cap:arrays, en sentido
contrario. `todos` devuelve una closure nueva que pasa el préstamo por cada
regla y se detiene en la primera que lo rechaza.

Cada regla sigue siendo pequeña, con nombre si hace falta, comprobable por
separado. La combinación es otra función. Agregar una cuarta condición es
agregar un argumento.

:::pitfall
Demasiadas closures esconden lo que hace el código. Una cadena de seis
funciones anónimas encajadas, cada una devolviendo otra, es tan difícil de
leer como el bucle de ochenta líneas que reemplazó.

La regla: si la closure tiene más de tres líneas, o si alguien va a
necesitar buscarla, recibe un nombre: una función, o un método de una
clase. La closure anónima es para lo que cabe en una línea y solo tiene
sentido ahí.
:::

## Lo que el volumen 2 va a entregar así

Tres cosas de Laravel, que vas a escribir en el volumen 2, son exactamente
lo que mostró este capítulo:

```php
// una ruta: un camino y la función que responde
Route::get('/salud', fn() => ['ok' => true]);

// un filtro de colección: la misma idea del array_filter
$atrasados = $prestamos->filter(fn($p) => $p->conAtraso());

// filtro opcional: la closure solo corre si la condición se cumple
$consulta->when($ciudad, fn($q) => $q->where('ciudad', $ciudad));
```

Ninguna de las tres es sintaxis nueva. Son funciones recibiendo funciones,
y el framework, del otro lado, guardando esas closures y llamándolas en el
momento correcto, como el `todos` de este capítulo guarda las reglas y las
llama por cada préstamo.

:::note En tu carrera
En una revisión de código, `'nombreDeFuncion'` pasado como texto es uno de
los pocos patrones que se pueden señalar sin conocer el sistema: se rompe
con namespace, desaparece del "renombrar" del editor y escapa del análisis
estático. Cambiarlo por `nombreDeFuncion(...)` es un cambio de una línea,
sin riesgo, que vuelve el código comprobable. Es una buena primera
contribución en un proyecto que todavía no conoces.
:::

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Informes/
      filtros.php            # atrasadoMasDe, todos
      InformeDeAtraso.php    # filtro() devuelve closure
  scripts/
    atrasados.php            # estaAtrasado(...) en lugar del texto
:::

:::summary
- `callable` acepta un texto con el nombre de una función; el texto se
  busca como nombre global al llamar y se rompe con namespace.
- `nombre(...)` y `$obj->metodo(...)` devuelven la función como `Closure`,
  resuelta donde está escrita.
- `\Closure` como tipo rechaza texto y array; la barra es por el
  namespace.
- Una closure creada en un método carga `$this`; `static fn` no lo carga, y
  rechaza `$this`.
- Una función que devuelve una closure es una fábrica: la configuración
  entra una vez.
- Las reglas pequeñas se combinan en una closure nueva. Más de tres líneas,
  dale un nombre.
:::

:::checkpoint
Pasas funciones a otras sin texto con nombre, escribes una fábrica de
filtros y una función que combina reglas, y reconoces, en una ruta o en un
filtro de Laravel, una closure haciendo lo que ya haces a mano.
:::

:::exercise level=1
Di qué hace cada línea en un archivo con `namespace CasaAmarela;` y una
función `formatear()` declarada en él:

```php
array_map('formatear', $multas);
array_map(formatear(...), $multas);
array_map('strtoupper', $titulos);
```

:::answer
La primera se rompe: `'formatear'` se busca como función global, y la
función se llama `CasaAmarela\formatear`.

La segunda funciona: `formatear(...)` se resuelve con el namespace del
archivo.

La tercera funciona, por un detalle: `strtoupper` es una función global de
PHP, y el texto la encuentra. Aun así, `strtoupper(...)` es la forma que
PHPStan comprueba y que sobrevive a cualquier cambio en el archivo.
:::

:::exercise level=2
Escribe `alguna(\Closure ...$reglas): \Closure`, la hermana de `todos`,
que acepta el préstamo si **cualquier** regla lo acepta. Úsala para
encontrar los préstamos atrasados más de 30 días **o** de lectores con
multa por encima de R$ 5,00.

:::answer
```php
function alguna(\Closure ...$reglas): \Closure
{
    return function (array $p) use ($reglas): bool {
        foreach ($reglas as $regla) {
            if ($regla($p)) {
                return true;
            }
        }
        return false;
    };
}

$paraRevisar = alguna(
    atrasadoMasDe(30),
    fn(array $p): bool => $p['multa_en_centavos'] > 500,
);
```

`atrasadoMasDe(30)` ya es una closure: la devolvió la fábrica. Las dos
formas se mezclan sin conversión. Y `todos` y `alguna` se combinan:
`todos(alguna(...), noExento(...))`.
:::

:::exercise level=3
Esta clase registra oyentes para el evento "préstamo hecho":

```php
final class Avisos
{
    private array $oyentes = [];

    public function cuando(\Closure $oyente): void
    {
        $this->oyentes[] = $oyente;
    }

    public function disparar(array $prestamo): void
    {
        foreach ($this->oyentes as $o) {
            $o($prestamo);
        }
    }
}
```

Un colega registra, dentro de un método del informe mensual, que carga
ocho mil préstamos en memoria:

```php
$this->avisos->cuando(fn($p) => error_log("prestamo {$p['id']}"));
```

Di qué mantiene vivo esa línea, y corrígela.

:::answer
La arrow function se creó dentro de un método del informe, y por eso carga
`$this`: el informe entero, con los ocho mil préstamos. Queda guardada en
`$oyentes` mientras exista `Avisos`. El informe, que debería desaparecer
de la memoria al terminar, queda atado a una closure que ni siquiera usa
`$this`.

```php
$this->avisos->cuando(
    static fn(array $p) => error_log("prestamo {$p['id']}"),
);
```

`static` dice que la closure no necesita el objeto, y PHP no lo captura. En
un script que corre y termina, la diferencia es pequeña. En un proceso que
queda en pie —el worker del volumen 2—, cada closure que carga un objeto
sin necesitarlo es memoria que solo crece.
:::
