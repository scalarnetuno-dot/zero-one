---
source_hash: 1edb60318594
title: "Namespaces y autoload"
number: 18
slug: namespaces-e-autoload
part: p3
kicker: "La importación necesitaba el libro antiguo y el libro nuevo en el mismo programa. El segundo se llamó LibroNuevo2."
goal: >-
  Darle una dirección al código con `namespace`, importar nombres con
  `use`, declarar el autoload PSR-4 en Composer y no volver a escribir un
  `require` de clase, incluido el motivo por el que eso se rompe solo en el
  servidor.
---

:::story LibroNuevo2
Tainá estaba leyendo el `importar.php`, que lee el volcado del Sistema y lo
graba en la base nueva.

—¿Por qué hay un `LibroNuevo2`?

—Porque ya había un `LibroNuevo`.

—¿Y el `LibroNuevo` qué es?

—El del Sistema. Con `cantidad`.

Tainá subió hasta el principio del archivo. Tres clases: `Libro`,
`LibroNuevo` y `LibroNuevo2`.

—¿Y el `Libro`?

—Ese es de 2019. Ya no se usa.

—Entonces el nuevo es el dos.

—El nuevo es el dos.

Lo anotó en el cuaderno, en la página que ya tenía
`funciones2_NUEVO_final.php` escrito con la misma letra apretada de quien
intenta no reírse.
:::

## Dos nombres iguales en el mismo programa

El problema del `LibroNuevo2` no es falta de imaginación. Es que PHP solo
acepta un `Libro` a la vez:

```php title="importar.php" numbered
<?php

require 'Libro.php';        // el del acervo nuevo
require 'legado/Libro.php'; // el del volcado del Sistema
```

```text
Fatal error: Cannot redeclare class Libro
(previously declared in /app/Libro.php:3)
in /app/legado/Libro.php on line 3
```

Estar en carpetas distintas no lo resuelve. Para PHP, los dos se llaman
`Libro`, y un nombre solo puede apuntar a una cosa.

Es el mismo error de `formatearFecha()`, y durante mucho tiempo la salida
fue la misma: un prefijo en el nombre. Así el PHP de los años 2000 produjo
clases como `Zend_Db_Table_Row_Abstract`, que es un namespace escrito a
mano, con guiones bajos en lugar de la barra.

## Un namespace es una dirección

```php title="Libro.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Libro
{
    public function __construct(
        public string $titulo,
        public int $anio,
    ) {}
}
```

Una línea nueva, y el nombre de la clase cambió:

```php
echo Libro::class, "\n";
```

```text
CasaAmarela\Acervo\Libro
```

`Nombre::class` devuelve el nombre completo de una clase, y es la forma
honesta de descubrir con qué estás tratando. El nombre real de esta clase
no es `Libro`: es `CasaAmarela\Acervo\Libro`. `Libro` es solo el pedazo
final.

:::term Nombre completo
*Fully Qualified Class Name*, abreviado FQCN en la documentación y en los
mensajes de error. Es la dirección entera, con las barras invertidas:
primero el namespace, después el nombre de la clase.

Dos clases con el mismo nombre final y direcciones distintas son dos clases
distintas, y pueden convivir en el mismo programa sin verse.
:::

La regla de sintaxis es corta: `namespace` es la primera instrucción del
archivo, después del `<?php`, y vale para todo lo que el archivo declara.

Y la regla de lectura es más corta todavía: **un namespace no es una
carpeta**. Es un nombre con puntuación, como una dirección postal. Nada en
PHP obliga a `CasaAmarela\Acervo\Libro` a vivir en `src/Acervo/Libro.php`.

Vas a hacer exactamente eso de todas formas, por un motivo que aparece
dentro de tres secciones.

## Dentro de un namespace, el resto del mundo desaparece

Pon `namespace CasaAmarela\Acervo;` al principio de un archivo que se
conecta a la base y ejecuta:

```php
$pdo = new PDO($dsn, 'root', 'contrasena');
```

```text
Fatal error: Uncaught Error: Class "CasaAmarela\Acervo\PDO" not found
```

Esta es la primera piedra con la que tropieza todo el mundo, y el mensaje
entrega la causa: PHP buscó un `PDO` **dentro de la dirección actual**. No
lo encontró y se detuvo. No sale a buscar por el edificio entero.

La barra invertida delante dice "desde la raíz":

```php
$pdo = new \PDO($dsn, 'root', 'contrasena');
```

```text
conectado
```

:::key
Para las **clases**, un nombre sin barra es relativo al namespace del
archivo.

Para las **funciones y constantes**, no: si PHP no encuentra la función en
el namespace actual, la busca en la raíz. Por eso `strtoupper()`, `date()`
y `count()` siguen funcionando sin ninguna barra dentro de un archivo con
namespace.

Esa diferencia es la razón por la que tu código antiguo sigue corriendo
después de recibir la primera línea de `namespace`, y por la que `new PDO`
es lo único que se rompe.
:::

## `use`: alias para todo el archivo

Escribir `\CasaAmarela\Acervo\Libro` cada vez sería peor que el
`LibroNuevo2`. El `use` resuelve el nombre una vez, al principio:

```php title="importar.php" numbered
<?php

use CasaAmarela\Acervo\Libro;
use CasaAmarela\Legado\Libro as LibroDelSistema;

$nuevo = new Libro('Vidas Secas', 1938);
$viejo = new LibroDelSistema('Vidas Secas', 1938, 3);
```

Tres cosas para recordar.

El `use` **no carga nada**. Solo dice: en este archivo, cuando escriba
`Libro`, quiero decir `CasaAmarela\Acervo\Libro`. Es un alias local.

El `as` da un alias distinto, y es la salida para el caso de las dos clases
con el mismo nombre final. Las dos conviven en el mismo archivo, con
nombres que elegiste, y el nombre verdadero de cada una sigue siendo la
dirección completa.

Y el `use` vale por archivo. No vale para el archivo que lo incluyó, no
vale para el que se incluya. Cada uno declara los suyos.

:::pitfall
El error más común con `use` no parece un error de `use`:

```text
Fatal error: Uncaught Error:
Class "CasaAmarela\Acervo\Prestamo" not found
```

El nombre del mensaje está bien, el archivo existe, la clase está ahí, y la
causa es que olvidaste el `use` en un archivo de otro namespace, así que
PHP buscó en la dirección equivocada.

Lee el mensaje por el **principio**, no por el final. El pedazo de delante
es la dirección donde buscó, y es ese el que está mal.
:::

## PSR-4: la convención que hace el resto sola

Un namespace no es una carpeta, pero si finges que lo es, una herramienta
puede adivinar dónde vive cada clase, y entonces nadie necesita volver a
escribir un `require` de clase.

Eso es PSR-4: una convención publicada por el grupo que estandariza el
ecosistema PHP, y que sigue casi todo proyecto moderno.

```json title="composer.json"
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        }
    }
```

Esto dice: todo lo que empieza con `CasaAmarela\` vive dentro de `src/`. El
resto de la dirección se vuelve ruta, y el nombre de la clase se vuelve
nombre de archivo con `.php` al final.

| Nombre completo | Archivo |
|---|---|
| `CasaAmarela\Acervo\Libro` | `src/Acervo/Libro.php` |
| `CasaAmarela\Acervo\Ejemplar` | `src/Acervo/Ejemplar.php` |
| `CasaAmarela\Lectores\Lector` | `src/Lectores/Lector.php` |
| `CasaAmarela\Legado\Libro` | `src/Legado/Libro.php` |

Tabla: El prefijo `CasaAmarela\` se cambia por la carpeta `src/`; lo que
queda se vuelve ruta, pedazo por pedazo.

De ahí salen dos reglas prácticas. **Un archivo, una clase**: el autoload
busca un archivo por nombre, y dos nombres en el mismo archivo dejan uno de
ellos inalcanzable. Y **el archivo se llama como la clase**, con las mismas
mayúsculas y minúsculas.

Después de declararlo, avísale a Composer:

```text
$ composer dump-autoload
```

```text
Generating autoload files
Generated autoload files containing 4 classes
```

Y el `importar.php` entero queda así:

```php title="importar.php" numbered
<?php

require 'vendor/autoload.php';

use CasaAmarela\Acervo\Libro;
use CasaAmarela\Legado\Libro as LibroDelSistema;

$nuevo = new Libro('Vidas Secas', 1938);
$viejo = new LibroDelSistema('Vidas Secas', 1938, 3);

echo $nuevo->titulo, ' / ', $viejo->cantidad, "\n";
```

Un solo `require`, el mismo de todos los programas del proyecto. Las clases
aparecen cuando se usan.

## ¿Quién encontró esta clase?

El autoload no es magia, y desconfiar de él es sano hasta que ves el
tamaño de la cosa. Son seis líneas:

```php title="cargador.php" numbered
<?php

spl_autoload_register(function (string $clase): void {
    echo "buscando: $clase\n";
});

$x = new Noexiste();
```

```text
buscando: Noexiste

Fatal error: Uncaught Error: Class "Noexiste" not found
```

`spl_autoload_register` guarda una función para llamarla **en el momento en
que PHP encuentra un nombre de clase que todavía no conoce**. La función
recibe el nombre completo y tiene una sola obligación: si sabe dónde está,
cargar el archivo. Si no lo carga, PHP pasa a la siguiente función
registrada y, si se acaban, da el error.

Un cargador PSR-4 mínimo cabe en ocho líneas:

```php title="cargador.php" numbered
<?php

spl_autoload_register(function (string $clase): void {
    $prefijo = 'CasaAmarela\\';

    if (!str_starts_with($clase, $prefijo)) {
        return;
    }

    $resto = substr($clase, strlen($prefijo));
    $relativa = str_replace('\\', '/', $resto);
    $ruta = __DIR__ . '/src/' . $relativa . '.php';

    if (is_file($ruta)) {
        require $ruta;
    }
});
```

Esto es lo que hace el `vendor/autoload.php`, con más cuidado y para todos
los prefijos a la vez: el tuyo y el de cada biblioteca instalada.

:::trivia
La sigla PSR viene de *PHP Standard Recommendation*, numeradas por el
PHP-FIG, un grupo formado por mantenedores de proyectos grandes que se
cansaron de las bibliotecas incompatibles.

La PSR-0 vino antes y todavía aceptaba el guion bajo en el nombre de la
clase como separador de carpeta, herencia de la época de `Zend_Db_Table`.
La PSR-4 lo abandonó. Fue la última vez que el ecosistema tuvo que ponerse
de acuerdo sobre dónde quedan los archivos.
:::

## `dump-autoload`, y cuándo hace falta

Composer genera la lista de prefijos una vez y la guarda. Tienes que
regenerarla cuando **cambia el mapa**, no cuando cambia el código:

| Lo que hiciste | Necesita `dump-autoload` |
|---|---|
| creaste `src/Acervo/Autor.php` | no |
| editaste una clase | no |
| cambiaste el bloque `autoload` del `composer.json` | sí |
| instalaste un paquete | no: el `require` ya lo hace |

Tabla: En el día a día, casi nunca. El comando existe para el día en que
tocaste el mapa.

Hay una variante que aparece en las guías de deploy:

```text
$ composer dump-autoload --optimize
```

En lugar de adivinar la ruta con cada clase nueva, Composer recorre las
carpetas y arma una lista lista de nombre a archivo. Es más rápido, porque
cambia una consulta al disco por una consulta a la memoria.

El costo es la otra cara de la misma moneda: una clase creada después del
recorrido no está en la lista. En una máquina de desarrollo, eso es una
trampa gratuita. En producción, donde el código no cambia entre un deploy y
otro, es ganancia pura.

## En mi Windows funciona

Falta la piedra que solo aparece en el servidor.

:::pitfall
`CasaAmarela\Acervo\Libro` busca `src/Acervo/Libro.php`. Si el archivo se
llama `libro.php`, con `l` minúscula:

- en **Windows** y en **macOS**, el sistema de archivos ignora las
  mayúsculas y entrega el archivo igual. Funciona;
- en **Linux**, `libro.php` y `Libro.php` son dos archivos distintos. Uno
  de ellos no existe.

El resultado es el defecto que más consume una tarde de viernes: todo
funciona en la máquina de quien lo escribió, y la pantalla se rompe en el
servidor con `Class not found` señalando un nombre que está visiblemente
bien.

La regla que lo evita: el archivo se llama exactamente como la clase, y la
carpeta exactamente como el pedazo del namespace. Cuando Git ya registró el
nombre equivocado, cambiar solo las mayúsculas exige dos pasos
—`git mv libro.php Libro.php.tmp` y después
`git mv Libro.php.tmp Libro.php`—, porque Git, en tu máquina, también cree
que los dos nombres son el mismo.
:::

## La estructura que el proyecto pasa a tener

Las clases salen de la raíz y van a `src/`, divididas por **tema del
dominio** —acervo, lectores, legado—, no por tipo técnico. Una carpeta
llamada `Classes/` o `Helpers/` solo empuja la pregunta "¿dónde vive esto?"
hacia adentro.

:::tree title="Dónde estamos ahora"
acervo/
  composer.json    # con el bloque autoload
  composer.lock
  vendor/
  .gitignore
  src/
    Acervo/
      Libro.php      # CasaAmarela\Acervo\Libro
      Ejemplar.php   # CasaAmarela\Acervo\Ejemplar
    Lectores/
      Lector.php     # CasaAmarela\Lectores\Lector
    Legado/
      Libro.php      # CasaAmarela\Legado\Libro
  conexion.php
  importar.php
  listar.php
  prestar.php
  recibo.php
:::

:::note En tu carrera
En un proyecto legado vas a encontrar los dos mundos en el mismo
repositorio: una carpeta moderna con PSR-4 y una carpeta antigua llena de
`require`. La tentación es proponer "migrar todo" en un sprint.

La migración que suele aprobarse es otra: registra el autoload para el
código nuevo, escribe todo lo nuevo ahí dentro, y mueve un archivo antiguo
cada vez que tengas que tocarlo de todas formas. En seis meses la carpeta
antigua se encogió sin que nadie abriera un ticket llamado
"refactorización".

Sirve para casi toda deuda técnica: la propuesta que sobrevive a la reunión
de prioridades no es la que pide una semana, es la que pide media hora cada
vez y muestra números después.
:::

:::summary
- Dos clases con el mismo nombre no conviven; otra carpeta no ayuda.
- `namespace` le da una dirección a la clase. El nombre real pasa a ser la
  dirección entera, y `Nombre::class` muestra cuál es.
- Dentro de un namespace, un nombre de clase sin barra es relativo: por eso
  `new \PDO`. Las funciones y constantes caen solas en la raíz.
- `use` crea un alias para el archivo; `use ... as` resuelve el conflicto de
  nombres finales iguales.
- PSR-4 cambia un prefijo de namespace por una carpeta: un archivo por
  clase, con el mismo nombre y las mismas mayúsculas.
- `spl_autoload_register` es el gancho que PHP llama al encontrar un nombre
  desconocido; el `vendor/autoload.php` es eso, bien hecho.
- `dump-autoload` solo cuando cambia el mapa; `--optimize` en producción,
  nunca en tu máquina.
- Mayúsculas equivocadas en el nombre del archivo funcionan en Windows y se
  rompen en Linux.
:::

:::checkpoint
Declaras namespaces, importas clases con `use`, sabes por qué `new PDO` se
rompe dentro de un namespace, configuras el `autoload` PSR-4 en el
`composer.json` y puedes crear una clase nueva que se encuentra sin ningún
`require`.
:::

:::exercise level=1
Para cada nombre completo, di en qué archivo vive, considerando el mapeo
`"CasaAmarela\\": "src/"`:

1. `CasaAmarela\Prestamos\Prestamo`
2. `CasaAmarela\Acervo\Busqueda\Filtro`
3. `CasaAmarela\Multa`

Y después al revés: ¿qué nombre completo tiene la clase declarada en
`src/Informes/Mensual.php`?

:::answer
1. `src/Prestamos/Prestamo.php`
2. `src/Acervo/Busqueda/Filtro.php`
3. `src/Multa.php`

El prefijo `CasaAmarela\` desaparece y se vuelve `src/`; cada barra
restante se vuelve una carpeta; el último pedazo se vuelve el archivo.

En sentido contrario, `src/Informes/Mensual.php` corresponde a
`CasaAmarela\Informes\Mensual`, y el archivo tiene que declarar
`namespace CasaAmarela\Informes;` al principio. Si declara otra cosa, el
autoload carga el archivo y PHP sigue diciendo que la clase no existe,
porque cargar el archivo correcto y encontrar el nombre correcto son dos
condiciones, no una.
:::

:::exercise level=2
Mueve las clases del capítulo anterior a `src/`, siguiendo la tabla de la
sección de PSR-4, y haz que `listar.php` funcione con un solo `require`.

Después borra, a propósito, la línea `use` del `listar.php` y lee el
mensaje. Di qué pedazo de él señala la causa.

:::answer
El `composer.json` recibe:

```json title="composer.json"
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        }
    }
```

Cada clase recibe el namespace al principio:

```php title="src/Acervo/Libro.php" numbered
<?php

namespace CasaAmarela\Acervo;

class Libro
{
    public function __construct(
        public string $titulo,
        public int $anio,
    ) {}
}
```

Y el programa:

```php title="listar.php" numbered
<?php

require 'vendor/autoload.php';
require 'conexion.php';

use CasaAmarela\Acervo\Libro;

$filas = $pdo->query('SELECT titulo, anio FROM libros')->fetchAll();

foreach ($filas as $fila) {
    $libro = new Libro($fila['titulo'], (int) $fila['anio']);
    echo $libro->titulo, "\n";
}
```

Sin el `use`, el mensaje es:

```text
Fatal error: Uncaught Error: Class "Libro" not found
```

El pedazo que señala la causa es el nombre entre comillas: vino **sin
dirección**. Como `listar.php` no tiene `namespace`, PHP buscó `Libro` en
la raíz, y no existe ninguna clase llamada solo `Libro`: la que escribiste
se llama `CasaAmarela\Acervo\Libro`.
:::

:::exercise level=3
Un equipo informa lo siguiente: la pantalla de recibo funciona en la
máquina de los tres desarrolladores y se rompe en producción, siempre, con
`Class "CasaAmarela\Recibos\Generador" not found`. El archivo
`src/Recibos/Generador.php` está en el repositorio y tiene el namespace
correcto.

Enumera al menos tres causas posibles y di, para cada una, una comprobación
que la confirme o la descarte en menos de un minuto.

:::answer
**Mayúsculas del nombre.** El archivo puede estar como
`src/recibos/Generador.php` o `src/Recibos/generador.php` en el
repositorio, y las tres máquinas ser Windows o macOS. Se comprueba con
`git ls-files src/Recibos`, que muestra el nombre como Git lo guardó, no
como lo muestra el disco local.

**Autoload optimizado con lista vieja.** Si el deploy ejecuta
`dump-autoload --optimize` antes de copiar el archivo nuevo, la lista lista
no tiene la clase. Se comprueba buscando el nombre dentro de
`vendor/composer/autoload_classmap.php` en el servidor.

**Archivo fuera del paquete publicado.** Un `.gitignore` demasiado amplio
—una línea `recibos/` pensada para PDFs generados, por ejemplo— puede estar
excluyendo la carpeta entera. Se comprueba con
`git check-ignore -v src/Recibos` en la máquina de quien lo escribió.

Una cuarta, menos común, que vale la comprobación porque cuesta cinco
segundos: el bloque `autoload` del `composer.json` se modificó y no se hizo
commit. `git status` en la máquina de quien lo tocó responde.

Lo que tienen en común esas cuatro, y por eso la pregunta es útil: ninguna
es un defecto en el código de la clase. Cuando el error solo ocurre en un
entorno, el sospechoso es lo que difiere entre los entornos: sistema de
archivos, paso de build y lo que de verdad se envió.
:::
