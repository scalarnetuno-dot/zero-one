---
source_hash: c0434fa9c399
title: "Del include a Composer"
number: 16
slug: do-include-ao-composer
part: p3
kicker: "Dos funciones con el mismo nombre en dos archivos. La página funciona o muere según cuál de los dos entre primero."
goal: >-
  Entender qué hacen `include` y `require`, qué resuelve el `_once` y qué
  no resuelve, crear un proyecto con Composer, instalar la primera
  dependencia y explicarle a alguien del equipo la diferencia entre
  `install` y `update`.
---

:::story Depende de cuál entre primero
El recibo de la Casa Amarela imprimía la fecha como `12/03/26`. El informe
de atrasados, generado el mismo día, imprimía `12/03/2026`.

Tainá preguntó cuál de los dos estaba bien.

—Los dos —dijo Dedé—. En archivos distintos.

El `funciones2.php` tenía una `formatearFecha()`. El
`funciones2_NUEVO_final.php` tenía otra, con un carácter menos en el
formato. Ninguna página del Sistema incluía las dos, y así pasaron quince
años sin que nadie tuviera que elegir.

Hasta la pantalla nueva de renovación, que necesitaba las dos.

—¿Y entonces?

—Entonces, el miércoles, funcionaba. El jueves, después de que alguien
cambió el orden de dos `include`, dejó de funcionar.

—¿Dejó de funcionar cómo?

Dedé giró el monitor.

```text
Fatal error: Cannot redeclare function formatearFecha()
(previously declared in /app/funciones2_NUEVO_final.php:3)
in /app/funciones2.php on line 2
```

—¿Y el miércoles por qué funcionaba?

—Porque el miércoles el orden era el otro.
:::

## Un archivo se vuelve dos, y dos se vuelven treinta

El proyecto de la Casa Amarela ya tiene el mismo problema, a menor escala.

Todo programa que habla con la base empieza con la misma línea:

```php
require 'conexion.php';
```

Hoy son seis archivos. Serán treinta antes de marzo. Y el `conexion.php` no
es el único candidato a compartirse: la `multaEnCentavos()` la van a usar
el recibo, el informe y la pantalla de devolución.

Una cosa cambió en el `conexion.php` desde que nació: perdió el
`echo "conectado\n"` del final. Era una línea simpática mientras el archivo
corría solo, y es una línea que ensucia la salida de los seis en cuanto
pasa a ser incluido por los seis.

```php title="conexion.php" numbered
<?php

$dsn = 'mysql:host=127.0.0.1;port=3306'
     . ';dbname=casa_amarela;charset=utf8mb4';

$pdo = new PDO($dsn, 'root', 'contrasena', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,
]);
```

:::key
Un archivo hecho para ser incluido no imprime nada. Define —variables,
funciones, configuración— y devuelve el control.

Un `echo` en un archivo incluido aparece en la salida de todos los que lo
incluyen, incluso en medio de un JSON y antes de una cabecera HTTP.
:::

## include y require

Las dos palabras hacen lo mismo: toman el contenido de otro archivo y lo
ejecutan ahí, como si estuviera escrito en ese lugar. La diferencia es qué
pasa cuando el archivo no existe.

Con `include`:

```php title="recibo.php" numbered
<?php

include 'tasas.php';
echo "llegué aquí\n";
```

```text
Warning: include(tasas.php): Failed to open stream: No such file or
directory in /app/recibo.php on line 3

Warning: include(): Failed opening 'tasas.php' for inclusion
(include_path='.:/usr/share/php') in /app/recibo.php on line 3
llegué aquí
```

Dos avisos, y el programa **siguió**. Imprimió "llegué aquí" sin las tasas
que iba a usar.

Cambia una palabra:

```php title="recibo.php" numbered
<?php

require 'tasas.php';
echo "llegué aquí\n";
```

```text
Warning: require(tasas.php): Failed to open stream: No such file or
directory in /app/recibo.php on line 3

Fatal error: Uncaught Error: Failed opening required 'tasas.php'
(include_path='.:/usr/share/php') in /app/recibo.php:3
```

El programa se detuvo. No imprimió nada después.

| | El archivo no existe | El programa |
|---|---|---|
| `include` | aviso | sigue |
| `require` | error fatal | se detiene |

Tabla: La elección no es de estilo. Es la respuesta a una pregunta: *¿este
programa tiene sentido sin ese archivo?*

Para el `conexion.php` la respuesta es no —un programa de préstamo sin base
no tiene nada que hacer—, y `require` es lo correcto. Para un archivo de
traducción opcional, o un `config.local.php` que solo existe en tu
máquina, `include` es honesto.

:::pitfall
La tentación es usar `include` "para que no se rompa". El resultado es un
programa que sigue adelante sin la mitad de lo que necesitaba y falla
treinta líneas después, con un mensaje sobre una variable indefinida que no
tiene ninguna relación visible con el archivo que faltó.

Romperse temprano, con el nombre del archivo que faltó, sale más barato.
:::

## Lo que el `_once` resuelve

Existen `include_once` y `require_once`. Guardan la lista de archivos ya
cargados e ignoran el pedido repetido.

El problema real que esto resuelve aparece en cuanto tus archivos empiezan
a incluirse unos a otros:

```php title="informe.php"
<?php

require 'conexion.php';
require 'multa.php';  // multa.php también requiere conexion.php
```

Sin `_once`, el `conexion.php` corre dos veces: dos conexiones abiertas, y
la segunda sobrescribiendo el `$pdo` de la primera. Con `require_once`,
corre una.

```php title="informe.php"
<?php

require_once 'conexion.php';
require_once 'multa.php';
```

## Lo que el `_once` no resuelve

Aquí vive la confusión que le costó el miércoles a Dedé.

El `_once` compara **archivos**, no nombres. Dos archivos distintos que
declaran la misma función siguen siendo dos archivos distintos, y los dos
se van a cargar.

Reprodúcelo. Tres archivos pequeños, en la misma carpeta:

```php title="funciones2.php" numbered
<?php

function formatearFecha(string $iso): string
{
    return date('d/m/Y', strtotime($iso));
}
```

```php title="funciones2_NUEVO_final.php" numbered
<?php

function formatearFecha(string $iso): string
{
    return date('d/m/y', strtotime($iso));
}
```

La única diferencia está en el formato: `Y` imprime el año con cuatro
dígitos, `y` con dos. La función `date()` recibe ese formato y un instante
en segundos; `strtotime()` convierte el texto `2026-03-12` en ese número de
segundos.

```php title="renovar.php" numbered
<?php

include_once 'funciones2.php';
include_once 'funciones2_NUEVO_final.php';

echo formatearFecha('2026-03-12'), "\n";
```

```text
Fatal error: Cannot redeclare function formatearFecha()
(previously declared in /app/funciones2.php:3)
in /app/funciones2_NUEVO_final.php on line 3
```

El `_once` no impidió nada, porque nada se incluyó dos veces. Fueron dos
archivos, una vez cada uno, con la misma función dentro.

## El parche que congeló el defecto

La salida que alguien encontró en el Sistema, en 2017, fue rodear la
segunda declaración con una pregunta:

```php title="funciones2_NUEVO_final.php" numbered
<?php

if (!function_exists('formatearFecha')) {
    function formatearFecha(string $iso): string
    {
        return date('d/m/y', strtotime($iso));
    }
}
```

`function_exists()` devuelve `true` si ya se declaró una función con ese
nombre. El `!` lo invierte: *declárala solo si todavía no existe*.

Ejecuta el `renovar.php` otra vez:

```text
12/03/2026
```

Funciona. Y funciona con una de las dos versiones descartada en silencio,
porque la otra llegó primero.

Ahora invierte las dos líneas del `renovar.php`:

```php title="renovar.php" numbered
<?php

include_once 'funciones2_NUEVO_final.php';
include_once 'funciones2.php';

echo formatearFecha('2026-03-12'), "\n";
```

```text
Fatal error: Cannot redeclare function formatearFecha()
(previously declared in /app/funciones2_NUEVO_final.php:3)
in /app/funciones2.php on line 2
```

Murió, porque solo uno de los dos archivos recibió la cerca.

:::pitfall
`function_exists()` alrededor de una declaración es casi siempre la marca
de un conflicto que nadie quiso resolver. Cambia un error fatal, que señala
los dos archivos y las dos líneas, por un comportamiento que depende del
orden de carga, y el orden de carga es lo que más cambia cuando alguien
toca un `include` sin mirar.

Cuando encuentres uno, la pregunta no es "¿lo puedo quitar?". Es: **¿cuáles
son las dos versiones, y cuál de ellas está usando el sistema hoy?**
:::

## Composer no es un instalador

Con treinta archivos, "quién incluye a quién" se vuelve trabajo de jornada
completa. Con una biblioteca de terceros, se vuelve imposible: la
biblioteca tiene sus propios archivos, que incluyen otros archivos suyos, y
no sabe dónde pusiste la carpeta.

Composer resuelve tres problemas de una vez, y solo el primero es
"descargar cosas":

1. **Averiguar qué instalar.** Pides una biblioteca; ella depende de otras
   dos; una de ellas exige una versión que choca con lo que ya tienes.
   Elegir el conjunto que cierra es un problema de cuentas, no de descarga.
2. **Registrar exactamente lo que se instaló**, para que tu máquina, la de
   Tainá y el servidor ejecuten el mismo código.
3. **Cargar los archivos** sin que escribas un `require` por biblioteca.

:::term Dependencia
Código que tu proyecto usa y no escribió. Una dependencia tiene nombre,
versión y, casi siempre, dependencias propias, que pasan a ser tuyas
también, sin que las hayas pedido.
:::

## El proyecto recibe un nombre

Hasta ahora la carpeta del proyecto era una carpeta.

```text
$ composer init
```

El comando hace preguntas. Las respuestas de nuestro proyecto:

```text
Package name (<vendor>/<name>): casa-amarela/acervo
Description []: Sistema del acervo de la Biblioteca Casa Amarela
Author [n to skip]: n
Minimum Stability []:
Package Type []: project
License []: proprietary

Would you like to define your dependencies interactively [yes]? no
Would you like to define your dev dependencies interactively [yes]? no
Add PSR-4 autoload mapping? [src/, n to skip]: n
```

La última respuesta quedó en `n` porque el proyecto todavía no tiene nada
que mapear. Las dos anteriores quedaron en `no` porque instalar desde la
línea de comandos es más simple que responder un formulario.

El resultado es un archivo:

```json title="composer.json"
{
    "name": "casa-amarela/acervo",
    "description": "Sistema del acervo de la Biblioteca Casa Amarela",
    "type": "project",
    "license": "proprietary",
    "require": {}
}
```

Nueve líneas, nada de magia. `require` vacío quiere decir: este proyecto
todavía no depende de nada.

## La primera dependencia

Hace cuatro capítulos que los datos del acervo aparecen en pantalla así:

```php
var_dump($libros);
```

```text
array(2) { [0]=> array(3) { ["id"]=> int(12) ["titulo"]=>
string(12) "Dom Casmurro" ["anio"]=> int(1899) } [1]=> array(3) {
["id"]=> int(31) ["titulo"]=> string(18) "Memórias Póstumas"
["anio"]=> int(1881) } }
```

Información completa, lectura imposible. Existe una biblioteca que hace lo
mismo con formato, y es el primer pedido del proyecto:

```text
$ composer require --dev symfony/var-dumper
```

```text
./composer.json has been updated
Running composer update symfony/var-dumper
Lock file operations: 3 installs, 0 updates, 0 removals
  - Locking symfony/deprecation-contracts (v3.5.1)
  - Locking symfony/polyfill-mbstring (v1.31.0)
  - Locking symfony/var-dumper (v7.2.3)
Writing lock file
Installing dependencies from lock file (including require-dev)
Package operations: 3 installs, 0 updates, 0 removals
  - Installing symfony/deprecation-contracts (v3.5.1)
  - Installing symfony/polyfill-mbstring (v1.31.0)
  - Installing symfony/var-dumper (v7.2.3)
Generating autoload files
```

Pediste un paquete y recibiste tres. Los otros dos son dependencias del
primero: el `var-dumper` los necesita, y Composer los trajo sin preguntar
porque la alternativa sería preguntar cuarenta veces.

```text
$ composer show --tree
```

```text
casa-amarela/acervo project
`--symfony/var-dumper v7.2.3
    |--php >=8.2
    |--symfony/deprecation-contracts ^2.5|^3
    `--symfony/polyfill-mbstring ~1.0
```

Para usarla, una línea nueva al principio del programa:

```php title="listar.php" numbered
<?php

require 'vendor/autoload.php';
require 'conexion.php';

$libros = $pdo->query(
    'SELECT id, titulo, anio FROM libros ORDER BY titulo LIMIT 2'
)->fetchAll();

dump($libros);
```

```text
array:2 [
  0 => array:3 [
    "id" => 12
    "titulo" => "Dom Casmurro"
    "anio" => 1899
  ]
  1 => array:3 [
    "id" => 31
    "titulo" => "Memórias Póstumas"
    "anio" => 1881
  ]
]
```

El `vendor/autoload.php` es el archivo que Composer generó en la última
línea de la instalación. Sabe dónde vive cada cosa que Composer descargó, y
es el único `require` de biblioteca que vas a escribir en todo el proyecto.

:::key
`dump()` muestra y sigue. `dd()` muestra y se detiene —*dump and die*—. El
segundo es el que quieres cuando estás cazando un valor en medio de un
bucle y no quieres recorrer trescientas líneas de salida.
:::

## `composer.json` pide, `composer.lock` recuerda

La instalación tocó dos archivos. Parecen redundantes y no lo son.

El `composer.json` ganó tres líneas:

```json title="composer.json"
    "require-dev": {
        "symfony/var-dumper": "^7.2"
    }
```

Eso es un **pedido**: cualquier 7 punto algo sirve.

El `composer.lock` tiene ahora unos cientos de líneas, y entre ellas:

```json title="composer.lock"
        {
            "name": "symfony/var-dumper",
            "version": "v7.2.3",
            "source": {
                "type": "git",
                "reference": "a75bf8b0f8b9d0a92f0cb4e6c6b8"
            }
        }
```

Eso es un **registro**: fue esta versión, de este commit. No es un rango,
es un punto.

La diferencia aparece en los dos comandos:

| Comando | Lee | Escribe | Cuándo |
|---|---|---|---|
| `composer install` | el `.lock` | nada | al clonar y en el deploy |
| `composer update` | el `.json` | el `.lock` | cuando **decides** actualizar |

Tabla: `install` reproduce. `update` decide. Confundirlos es el defecto de
configuración más caro que existe.

:::pitfall
`composer update` en el servidor es la versión moderna de "en mi máquina
funciona". Ignora el `.lock`, resuelve todo de nuevo, y el servidor arranca
con versiones que nadie probó, a veces publicadas esa misma mañana.

En el servidor, solo `composer install`. Y si el `.lock` no está en Git,
ese comando no tiene qué leer: volviste al problema anterior por otro
camino.
:::

## El acento circunflejo que aceptaste sin leer

El `^7.2` que apareció en el `composer.json` tiene regla, y la regla viene
de la numeración que sigue casi todo paquete PHP:
**mayor.menor.corrección**.

- **mayor** cambia cuando algo se rompe a propósito;
- **menor** cambia cuando se agrega algo sin romper;
- **corrección** cambia cuando se arregla algo.

| Escrito | Acepta | Rechaza |
|---|---|---|
| `^7.2` | 7.2.0, 7.4.1, 7.9.9 | 8.0.0 y 7.1.9 |
| `~7.2.3` | 7.2.3, 7.2.11 | 7.3.0 |
| `7.2.3` | solo 7.2.3 | todo lo demás |

Tabla: El `^` es el predeterminado de `composer require` porque apuesta a
que el autor respeta la numeración. El `~` es para cuando solo quieres
correcciones. La versión fija es para cuando la apuesta ya salió mal una
vez.

## `require` y `require-dev`

El `var-dumper` entró con `--dev`, y eso tiene consecuencias.

- **`require`** es lo que el programa necesita para **funcionar**.
- **`require-dev`** es lo que **tú** necesitas para trabajar: depurador,
  pruebas, formateador.

En el servidor, la instalación se salta la segunda lista:

```text
$ composer install --no-dev
```

El resultado es menos código en disco, menos superficie para problemas de
seguridad y un servidor sin herramientas de depuración instaladas.

Y aquí está la trampa que viene con eso:

```text
Fatal error: Uncaught Error: Call to undefined function dump()
in /app/listar.php on line 9
```

Un `dump()` olvidado en una línea que solo corre en el caso raro no rompe
nada en tu máquina —donde el paquete existe— y tumba la página en
producción, donde no existe. Es un error de cinco segundos para arreglar y
de dos horas para descubrir, porque el caso raro no ocurre cuando estás
mirando.

## La carpeta que no va a Git

Composer creó una carpeta `vendor/` con el código de las tres bibliotecas.
No entra en el repositorio:

```text title=".gitignore"
/vendor/
```

La lógica es simple: `vendor/` es **resultado**, y el resultado se
reproduce. Quien clona el proyecto ejecuta `composer install` y recibe
exactamente el mismo contenido, porque el `.lock` dice exactamente cuál
era.

| Archivo | Va a Git | Por qué |
|---|---|---|
| `composer.json` | sí | es la intención del proyecto |
| `composer.lock` | sí | es lo que hace coincidir las máquinas |
| `vendor/` | no | es resultado, y pesa |

:::note En tu carrera
En algún proyecto alguien va a proponer versionar `vendor/`, normalmente
después de un deploy que falló porque la red se cayó en medio del
`composer install`.

El argumento en contra no es "es feo". Es concreto: la `vendor/` de un
proyecto mediano tiene decenas de miles de archivos, y cada actualización
se vuelve un cambio que nadie puede revisar. El problema real era la red
en el deploy, y tiene solución propia: instalar antes de publicar y
publicar la carpeta lista.

Cuando no estés de acuerdo con una decisión así, trae el problema que
intentaba resolver junto con tu alternativa. Discrepar sin eso es pedirle a
la persona que admita que se equivocó delante del equipo, y nadie acepta.
:::

:::tree title="Dónde estamos ahora"
acervo/
  composer.json   # lo que el proyecto pide
  composer.lock   # lo que el proyecto recibió
  vendor/         # generado por Composer, fuera de Git
  .gitignore
  conexion.php    # crea el $pdo, sin imprimir nada
  multa.php
  buscar.php
  registrar.php
  prestar.php
  devolver.php
  listar.php
  recibo.php
:::

:::summary
- `include` avisa y sigue; `require` se detiene. La elección responde "¿el
  programa tiene sentido sin ese archivo?".
- `_once` impide el **mismo archivo** dos veces. No impide que dos archivos
  distintos declaren la misma función.
- `function_exists()` alrededor de una declaración cambia un error claro
  por una dependencia silenciosa del orden de carga.
- Composer resuelve el conjunto de versiones, registra lo que instaló y
  genera el cargador. Descargar es la parte fácil.
- `composer.json` es el pedido; `composer.lock` es el registro. `install`
  reproduce, `update` decide.
- `^7.2` acepta cualquier 7.x; `~7.2.3` acepta solo correcciones de 7.2; la
  versión fija no acepta nada.
- `require-dev` no va a producción, y el `dump()` olvidado sí.
- `vendor/` queda fuera de Git; `composer.lock` queda dentro.
:::

:::checkpoint
Creas un proyecto con `composer init`, instalas una dependencia, sabes
decir qué guarda cada uno de los dos archivos de configuración, lees un
rango de versión y reconoces por el mensaje de error cuándo faltó en
producción un paquete de desarrollo.
:::

:::exercise level=1
El `composer.json` de un proyecto pide `"monolog/monolog": "^3.5"`. ¿Cuáles
de estas versiones puede instalar `composer update`: 3.5.0, 3.9.2, 4.0.0,
3.4.9?

Y si, en lugar de `update`, alguien ejecuta `composer install` en una
máquina que acaba de clonar el proyecto, ¿qué versión se va a instalar?

:::answer
El `update` puede instalar **3.5.0 y 3.9.2**. El `^` acepta desde la
versión pedida hasta el siguiente número mayor, sin alcanzarlo: rechaza la
4.0.0 por ser mayor y la 3.4.9 por ser anterior a lo pedido.

El `install` no elige nada. Instala **la versión escrita en el
`composer.lock`**, que puede ser la 3.5.0 aunque la 3.9.2 ya exista. Es esa
indiferencia a lo nuevo lo que hace que dos máquinas ejecuten el mismo
código.
:::

:::exercise level=2
Crea los tres archivos de la sección del parche: `funciones2.php`,
`funciones2_NUEVO_final.php` (con la cerca de `function_exists`) y
`renovar.php`.

Antes de ejecutar, escribe en un papel qué sale en cada uno de los dos
órdenes de `include_once`. Después ejecuta los dos y compara.

Luego pon la cerca también en `funciones2.php` y ejecuta los dos órdenes
otra vez. Explica qué cambió y por qué eso es peor.

:::answer
Con la cerca solo en `funciones2_NUEVO_final.php`:

- `funciones2.php` primero: imprime `12/03/2026`. La segunda declaración
  la descarta la cerca.
- `funciones2_NUEVO_final.php` primero: error fatal `Cannot redeclare`,
  porque `funciones2.php` no tiene cerca e intenta declarar encima.

Con cerca en los dos, los dos órdenes funcionan, y ahí es donde empeora:

```text
orden A → 12/03/2026
orden B → 12/03/26
```

Ningún error, ningún aviso, y el formato de la fecha pasa a decidirlo el
orden de los `include`. El recibo y el informe pueden divergir para siempre
sin que nada en el sistema se queje. El error fatal era lo único que
todavía decía la verdad.

La corrección de verdad es elegir una de las dos funciones, borrar la otra
y ajustar las llamadas: trabajo de media hora que nadie hizo en nueve años
porque la cerca hizo desaparecer la urgencia.
:::

:::exercise level=3
El viernes, el deploy de la Casa Amarela salió y la pantalla de préstamo
empezó a devolver error. El log del servidor dice:

```text
Fatal error: Uncaught Error: Call to undefined function dump()
in /app/prestar.php on line 47
```

La línea 47 está dentro de un `if` que solo corre cuando el ejemplar está
marcado como `extraviado`, situación que ocurre unas dos veces al mes.

Responde tres cosas: qué pasó, por qué la revisión en la máquina de Dedé no
lo detectó, y qué dos cambios evitan que se repita.

:::answer
**Qué pasó.** Alguien dejó un `dump()` de depuración en el código. El
`symfony/var-dumper` está en `require-dev`, y el servidor instala con
`--no-dev`, así que la función no existe allí. El programa arranca con
normalidad y solo se rompe cuando se alcanza ese `if`.

**Por qué no se detectó.** En la máquina de Dedé el paquete está instalado,
así que la línea funciona. Y el camino del `extraviado` no se recorre a
mano: depende de un dato raro que nadie se acuerda de crear antes de
publicar.

**Los dos cambios.**

El primero es de proceso y no cuesta nada: buscar `dump(` y `dd(` antes de
publicar. La versión automatizada de eso es una regla en el paso de
publicación que rechaza el deploy si encuentra cualquiera de los dos.

El segundo es de cobertura: alguna forma de recorrer el camino del
ejemplar extraviado sin esperar a que ocurra. Mientras la única manera de
ejecutar ese `if` sea la vida real, producción sigue siendo el lugar donde
se comprueba.

Una respuesta que aparece y no resuelve: mover el `var-dumper` a `require`.
Eso arregla el síntoma instalando una herramienta de depuración en el
servidor, y una herramienta de depuración en producción es una sierra de
banco en la sala de espera: funciona, y no es ahí donde vive.
:::
