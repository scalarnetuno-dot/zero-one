---
source_hash: 5b3271c0cdf2
title: "Cómo organizar un proyecto PHP"
number: 29
slug: como-organizar-um-projeto-php
part: p5
kicker: "El viernes, Márcia anunció que la parte web empezaba el lunes. Dedé pidió el fin de semana para ordenar la casa antes de la visita."
goal: >-
  Darle al proyecto una estructura de carpetas en la que cada cosa tenga su
  lugar, sacar la contraseña y la configuración del código, armar los
  objetos del sistema en un solo punto, y reconocer, pieza por pieza, la
  estructura que Laravel va a proponer en el volumen 2.
---

:::story Once veces la misma contraseña
—El lunes empieza la web —dijo Márcia, en la reunión del viernes—. Vera
quiere ver pantallas. La convocatoria quiere ver pantallas. Yo quiero ver
pantallas.

—Antes de las pantallas —dijo Dedé—, quería una tarde.

—¿Para qué?

Giró el portátil hacia la mesa. Una terminal, y un comando:

```text
$ grep -rl "'root', 'contrasena'" --include=*.php . | wc -l
11
```

—Once archivos con la contraseña de la base escrita dentro. Si la
contraseña cambia, son once lugares. Si alguien publica el repositorio, son
once copias de la contraseña en internet.

Tainá miró la carpeta del proyecto en su propio portátil. Había empezado
con un archivo, en el capítulo de PDO. Ahora tenía `importar.php`,
`importar2.php`, `prestar.php`, `informe.php`, un `bootstrap.php`, una
carpeta `scripts/` con la mitad de los scripts, y la otra mitad en la raíz.

—Parece el Sistema —dijo, en voz baja.

—Parece el Sistema en 2010 —dijo Nonato, desde la mesa de al lado, sin
quitar los ojos de la pantalla—. En 2011 ya tenía el
`funciones2_NUEVO_final.php`. Ordénenlo ahora.
:::

## La carpeta como está

Veintiocho capítulos de trabajo dejaron esto:

:::tree title="El acervo, el viernes"
acervo/
  composer.json, composer.lock
  vendor/
  src/                   # las clases: bien organizadas desde el 18
  bootstrap.php          # errores y log, del capítulo 28
  filtros.php            # funciones sueltas, del capítulo 25
  importar.php           # contraseña dentro
  importar2.php          # contraseña dentro, "el que funciona"
  prestar.php            # contraseña dentro
  informe.php            # contraseña dentro
  scripts/
    importar-donaciones.php  # contraseña dentro
    atrasados.php        # contraseña dentro
    ...
  var/log/
  phpstan.neon
:::

Nada de esto está mal por sí solo. El problema es la suma, y tiene tres
partes.

**No hay un lugar correcto para un archivo nuevo.** Un script entra en la
raíz o en `scripts/` según el humor del día. Quien llega al proyecto no
sabe dónde buscar, y quien escribe no sabe dónde poner.

**La configuración y los secretos están en el código.** La contraseña, la
zona horaria, el plazo de catorce días. Cambiar cualquiera exige editar
PHP, y el código va a Git, con todo lo que esté escrito en él.

**Cada script arma sus propios objetos.** El `new PDO(...)` aparece once
veces; el `new RelojDelSistema(...)`, cuatro; el `new Bitacora(...)`, con
tres rutas de log distintas.

El orden resuelve las tres, una por sección.

## Un lugar para cada cosa

:::tree title="El acervo, el lunes"
acervo/
  bin/                   # scripts de línea de comandos
    importar-donaciones.php
    atrasados.php
  config/                # configuración: arrays, sin secretos
    app.php
  public/                # la única carpeta que ve el servidor web
  src/                   # todo el código del dominio
    Acervo/ Circulacion/ Prestamos/ Importacion/
    Lectores/ Tiempo/
    Bitacora.php
    Servicios.php
    funciones.php
  tests/
  var/                   # lo que genera el programa: log, caché
    log/
  vendor/                # de Composer; nunca se edita a mano
  bootstrap.php          # arma todo, en un solo lugar
  .env                   # secretos de esta máquina; fuera de Git
  .env.example           # el molde del .env; en Git
  .gitignore
  composer.json, composer.lock
  phpstan.neon
:::

La regla detrás del árbol: **cada carpeta responde a una pregunta.**

| Carpeta | Pregunta |
|---|---|
| `src/` | ¿Qué **sabe hacer** el sistema? |
| `config/` | ¿Cómo está **ajustado**? |
| `bin/` | ¿Cómo se lo **llama** desde la línea de comandos? |
| `public/` | ¿Cómo se lo **llama** desde el navegador? |
| `var/` | ¿Qué **produjo** mientras corría? |
| `tests/` | ¿Cómo sabemos que **funciona**? |

Tabla: Una pregunta por carpeta. Un archivo nuevo va a la carpeta cuya
pregunta responde.

`public/` está vacía, y queda vacía hasta el volumen 2. Existe ahora por un
motivo de seguridad que vale la pena entender antes de tener qué poner en
ella: el servidor web le entrega al navegador **cualquier archivo** de la
carpeta que ve. Si viera la raíz del proyecto, `https://.../.env` entregaría
la contraseña de la base, y `https://.../var/log/app.log` entregaría el log.
Con el servidor apuntando a `public/`, en la web solo existe lo que se puso
ahí a propósito.

La carpeta `scripts/` se volvió `bin/`, el nombre que usa la mayor parte de
los proyectos PHP para los programas de línea de comandos, y los scripts de
la raíz fueron ahí. El `importar2.php`, "el que funciona", se comparó con
el `importar.php` en una tarde, las diferencias terminaron en el
`Importador` y los dos se volvieron `bin/importar-donaciones.php`. Las
funciones de `filtros.php` fueron a `src/funciones.php`, que Composer pasa
a cargar solo:

```json title="composer.json"
{
    "name": "casa-amarela/acervo",
    "type": "project",
    "require": {
        "php": "^8.3"
    },
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        },
        "files": [
            "src/funciones.php"
        ]
    },
    "scripts": {
        "analisis": "phpstan analyse",
        "importar": "php bin/importar-donaciones.php"
    }
}
```

El `psr-4` del capítulo @cap:namespaces-e-autoload carga las clases cuando
alguien las usa. Una función no tiene esa oportunidad —PHP no tiene cómo
adivinar en qué archivo vive—, y el `files` lo resuelve de la forma simple:
estos archivos se incluyen siempre, desde el `vendor/autoload.php`. Mantén
la lista corta.

El bloque `scripts` les da nombre a los comandos que ejecuta el equipo:
`composer analisis`, `composer importar`. Nadie necesita recordar la ruta de
PHPStan ni la del script.

## La configuración fuera del código

La configuración tiene dos mitades, y viven en lugares distintos.

**Lo que cambia de máquina a máquina** —contraseña, dirección de la base,
zona horaria del servidor— va a un archivo `.env` en la raíz, que **no va a
Git**:

```text title=".env"
APP_ZONA=America/Sao_Paulo
DB_DSN="mysql:host=127.0.0.1;dbname=casa_amarela;charset=utf8mb4"
DB_USUARIO=casa_amarela
DB_CONTRASENA=la-contrasena-de-verdad
PLAZO_EN_DIAS=14
```

A Git va el `.env.example`, igual y con los secretos en blanco, para que
quien llegue sepa qué tiene que completar. Y el `.gitignore` garantiza que
el verdadero no entre por descuido:

```text title=".gitignore"
/vendor/
/var/
/.env
```

**Lo que lee el programa** —con nombre, tipo y valor predeterminado— va a
`config/`, en archivos PHP que devuelven un array:

```php title="config/app.php" numbered
<?php

declare(strict_types=1);

use function CasaAmarela\env;

return [
    'zona' => env('APP_ZONA', 'America/Sao_Paulo'),
    'plazo_en_dias' => (int) env('PLAZO_EN_DIAS', '14'),
    'base' => [
        'dsn' => env('DB_DSN'),
        'usuario' => env('DB_USUARIO'),
        'contrasena' => env('DB_CONTRASENA'),
    ],
];
```

El `require` de un archivo que termina en `return` devuelve el valor de ese
`return`: así es como `$config = require 'config/app.php'` recibe el array.
`use function` es el `use` del capítulo @cap:namespaces-e-autoload para
funciones.

Las dos funciones que leen el `.env`:

```php title="src/funciones.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela;

function cargarEnv(string $ruta): void
{
    if (!is_file($ruta)) {
        return;
    }
    $valores = parse_ini_file($ruta, false, INI_SCANNER_RAW);
    foreach ($valores as $clave => $valor) {
        $_ENV[$clave] ??= $valor;
    }
}

function env(string $clave, ?string $predeterminado = null): ?string
{
    return $_ENV[$clave] ?? $predeterminado;
}
```

`parse_ini_file` lee un archivo `clave=valor` y devuelve un array;
`INI_SCANNER_RAW` le pide que no intente interpretar los valores, y el
`??=` no sobrescribe un valor que ya estaba definido. Es una versión
pequeña de lo que hacen con más cuidado las bibliotecas de `.env`.

:::key
**Los secretos en el `.env`, fuera de Git. La forma en `config/`, dentro de
Git.** El código del sistema nunca lee el `.env` directamente: lee
`$config['base']['dsn']`. Así existe un único lugar que sabe de dónde viene
cada valor, y un único lugar para darle un valor predeterminado.
:::

:::pitfall
Si una contraseña ya fue a Git una vez, quitarla del archivo no la quita
del historial: cualquiera con una copia del repositorio encuentra el commit
antiguo. Después de mover la contraseña al `.env`, **cambia la
contraseña**. En la Casa Amarela, fue la primera tarea del lunes, antes de
cualquier pantalla.
:::

## Armar todo en un solo lugar

El `bootstrap.php` del capítulo @cap:erros-e-debug configuraba los errores.
Ahora arma también los objetos que usa el sistema, y los entrega listos:

```php title="bootstrap.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Bitacora;
use CasaAmarela\Servicios;
use CasaAmarela\Tiempo\Reloj;
use CasaAmarela\Tiempo\RelojDelSistema;

use function CasaAmarela\cargarEnv;

require __DIR__ . '/vendor/autoload.php';

cargarEnv(__DIR__ . '/.env');
$config = require __DIR__ . '/config/app.php';

// ...error_reporting y los dos manejadores del capítulo 28...

$servicios = new Servicios();

$servicios->registrar(PDO::class, fn() => new PDO(
    $config['base']['dsn'],
    $config['base']['usuario'],
    $config['base']['contrasena'],
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION],
));

$servicios->registrar(Reloj::class, fn() => new RelojDelSistema(
    new DateTimeZone($config['zona']),
));

$servicios->registrar(Bitacora::class, fn() => new Bitacora(
    __DIR__ . '/var/log/app.log',
));

return $servicios;
```

Y `Servicios` es una clase de veinte líneas que guarda closures —las del
capítulo @cap:funcoes-anonimas-e-closures— y solo las llama cuando alguien
las pide:

```php title="src/Servicios.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela;

use Closure;
use RuntimeException;

final class Servicios
{
    /** @var array<string, Closure> */
    private array $fabricas = [];

    /** @var array<string, object> */
    private array $listos = [];

    public function registrar(string $nombre, Closure $fabrica): void
    {
        $this->fabricas[$nombre] = $fabrica;
    }

    public function get(string $nombre): object
    {
        if (!isset($this->fabricas[$nombre])) {
            throw new RuntimeException("desconocido: {$nombre}");
        }
        $fabrica = $this->fabricas[$nombre];
        return $this->listos[$nombre] ??= $fabrica($this);
    }
}
```

Tres ideas en poco código.

**Una fábrica por servicio.** Cada closure sabe crear un objeto. Registrar
no crea nada: el `new PDO` solo corre cuando alguien pide el PDO. Un script
que solo lee un CSV nunca abre una conexión con la base.

**Creado una vez.** El `??=` guarda el objeto listo en la primera llamada y
devuelve el mismo en las siguientes. Una conexión por ejecución, no una por
pedido.

**El nombre es la clase.** `PDO::class` es el texto `'PDO'`;
`Reloj::class`, el nombre completo de la interfaz. Quien pide el `Reloj` no
sabe —ni necesita saber— que recibe un `RelojDelSistema`. En la prueba, el
mismo nombre devuelve un `RelojDetenido`.

El script, después del orden:

```php title="bin/importar-donaciones.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Importacion\Importador;

$servicios = require __DIR__ . '/../bootstrap.php';

$importador = $servicios->get(Importador::class);
$importador->importar(__DIR__ . '/../var/donaciones.csv');
```

Ninguna contraseña, ningún `new PDO`, ninguna ruta de log. El script dice
qué hace; el `bootstrap.php` sabe cómo.

:::term Raíz de composición
El punto único del programa en el que los objetos se crean y se conectan
unos con otros. Fuera de él, las clases reciben lo que necesitan por el
constructor y no saben de dónde vino.

`Servicios` es un **contenedor**: el objeto que guarda las fábricas y
entrega los servicios listos. El de este capítulo necesita que alguien
registre cada fábrica a mano.
:::

## Del acervo a Laravel

Esta estructura no se inventó para la Casa Amarela. Es, con pocas
diferencias de nombre, la que usa casi todo proyecto PHP moderno, y la que
crea Laravel cuando escribes el primer comando del volumen 2.

| Aquí, en el volumen 1 | En Laravel, en el volumen 2 |
|---|---|
| `src/`, namespace `CasaAmarela\` | `app/`, namespace `App\` |
| `config/app.php` devolviendo un array | `config/`, un archivo por tema |
| `.env` y `.env.example` | `.env` y `.env.example` |
| `env()` solo dentro de `config/` | `env()` solo dentro de `config/` |
| `bin/importar-donaciones.php` | comando de Artisan |
| `bootstrap.php` | `bootstrap/app.php` |
| `Servicios` con fábricas a mano | el contenedor, que arma solo |
| `var/log/` | `storage/logs/` |
| `public/`, vacía | `public/index.php`, la puerta de la web |
| `Bitacora` con contexto | `Log`, de la PSR-3 |
| `Reloj` inyectado | `now()`, congelable en las pruebas |

Tabla: El mapa del cambio. Lo que cambia es el nombre; el motivo de cada
carpeta es el de este capítulo.

La línea del contenedor es la que el volumen 2 abre primero. `Servicios`
necesita que cada fábrica esté escrita; el contenedor de Laravel lee el
constructor de la clase, ve que pide un `PDO` y una `Bitacora`, y arma los
dos solo. El capítulo 3 del volumen 2 escribe esa versión a mano, en
cuarenta líneas, antes de abrir el framework.

:::note En tu carrera
Todo proyecto empieza como un script, y nadie se despierta decidiendo que
se va a volver el `funciones2_NUEVO_final.php`. Se vuelve de a poco, un
archivo en la raíz a la vez, cada uno con un buen motivo el día en que se
creó.

El orden de este capítulo llevó una tarde porque el proyecto tenía treinta
archivos. Con trescientos, llevaría un mes, y ninguna empresa da un mes
para eso. Organiza cuando duele poco: el momento correcto es cuando piensas
"esto ya se está desordenando".
:::

## Lo que todavía falta

El lunes por la mañana, Tainá abrió el cuaderno en la página que ya tenía
`funciones2_NUEVO_final.php` y escribió debajo:

```text
v1 - lo que sé hacer
  tipos, arrays, funciones, strings
  SQL a mano, JOIN, índice, transacción, PDO
  Composer, namespaces, clases, interfaces
  excepciones, tipado estricto, enums, objetos de valor
  referencias, closures, generadores
  archivos grandes, fechas con zona horaria, errores que avisan
  un proyecto con un lugar para cada cosa

v2 - lo que no sé
  ¿qué llega del navegador hasta PHP?
```

Todos los programas de este volumen corrieron en la terminal, llamados por
alguien que escribía `php` y un nombre de archivo. Vera no va a escribir
`php`. Va a abrir el navegador, hacer clic en un botón, y el navegador va a
mandarle un texto al servidor: un texto con un formato que tiene nombre,
reglas y treinta años de historia.

El `$_GET` y el `$_POST` que viste de pasada al principio del libro son lo
que PHP entiende de ese texto. Casi siempre, es suficiente. En la primera
semana del volumen 2, no lo va a ser, y Tainá va a pasar una mañana mirando
un `$_POST` vacío, con la aplicación jurando que lo mandó todo.

:::tree title="Dónde estamos ahora"
acervo/
  bin/          config/       public/ (vacía)
  src/          tests/        var/
  bootstrap.php               # config, errores, servicios
  .env (fuera de Git)         .env.example
  composer.json               # psr-4, files, scripts
:::

:::milestone
Fin de la Parte 5. El proyecto tiene una carpeta para cada pregunta, ningún
secreto en el código y un único lugar donde nacen los objetos. Las
referencias, las closures, los generadores, las fechas y los errores
dejaron de ser una sorpresa, y cada uno de ellos vuelve en el volumen 2 con
otro nombre.

Fin del volumen 1. El lenguaje está entero sobre la mesa: tipos,
funciones, SQL, PDO, Composer, clases, excepciones, tipado estricto, enums,
closures, archivos, fechas y errores, dentro de un proyecto que cualquier
persona del equipo sabe recorrer. El volumen 2 empieza por lo que pasa
entre el navegador y PHP, y solo después de eso abre Laravel, que va a
parecer, en cada carpeta, una versión más grande de lo que está en este
árbol.
:::

:::summary
- Cada carpeta responde a una pregunta: `src/` hace, `config/` ajusta,
  `bin/` y `public/` son las puertas, `var/` guarda lo producido, `tests/`
  comprueba.
- El servidor web solo ve `public/`. Todo lo demás queda fuera de la web.
- `autoload.files` carga funciones sueltas; `scripts` les da nombre a los
  comandos.
- Los secretos en el `.env`, fuera de Git; la forma en `config/`. Una
  contraseña que ya fue a Git hay que cambiarla.
- El `bootstrap.php` es la raíz de composición: crea y conecta los objetos,
  y los scripts solo piden.
- Un contenedor guarda fábricas y entrega servicios listos, creados una
  vez.
:::

:::checkpoint
Organizas un proyecto PHP en carpetas con propósito, sacas la
configuración y los secretos del código, armas los objetos en un único
punto con un contenedor simple, y sabes señalar, en la estructura de un
proyecto Laravel, el equivalente de cada carpeta de este capítulo.
:::

:::exercise level=1
Di en qué carpeta del acervo debe quedar cada archivo:

1. `Lector.php`, la clase del lector;
2. `recalcular-multas.php`, ejecutado una vez al mes por el programador de
   tareas;
3. `informe-2026-03.csv`, generado por ese script;
4. `biblioteca.php`, con los días de la semana en que abre la Casa
   Amarela;
5. el logotipo de la biblioteca, que va a aparecer en pantalla.

:::answer
1. `src/Lectores/`: es lo que el sistema sabe hacer.
2. `bin/`: es una puerta de línea de comandos.
3. `var/`: lo produjo el programa, y no va a Git.
4. `config/`: es un ajuste, y no un secreto. Va a Git.
5. `public/`: es la única carpeta que alcanza el navegador. El logotipo
   está hecho para verse.
:::

:::exercise level=2
Registra en el `bootstrap.php` una fábrica para el `Importador`, que recibe
un `PDO` y una `Bitacora` por el constructor. Usa el `$servicios` que la
closure recibe como argumento.

:::answer
```php
$servicios->registrar(
    Importador::class,
    fn(Servicios $s) => new Importador(
        $s->get(PDO::class),
        $s->get(Bitacora::class),
    ),
);
```

El `get` de `Servicios` llama a cada fábrica pasándole el propio
contenedor: el `$fabrica($this)` de la línea del `??=`. Así es como una
fábrica pide otros servicios sin conocer sus fábricas.

Fíjate en lo que esa fábrica tiene de mecánico: leer el constructor, pedir
cada tipo al contenedor, pasarlos en orden. Un programa podría hacerlo
solo, leyendo la firma del constructor. Es exactamente lo que hace el
contenedor del capítulo 3 del volumen 2.
:::

:::exercise level=3
Cléber tiene que correr el acervo en su máquina por primera vez. Clona el
repositorio y ejecuta `php bin/importar-donaciones.php`. Enumera, en orden,
los errores que va a encontrar y qué resuelve cada uno. Después, escribe
las instrucciones que pondrías en un `README.md` para que el siguiente no
encuentre ninguno.

:::answer
En orden:

1. `Failed opening required '.../vendor/autoload.php'`: el `vendor/` no va
   a Git. Se resuelve con `composer install`.
2. Un error de PDO por DSN vacío: el `.env` tampoco va. El `env()` devuelve
   `null`, y el `new PDO` no recibe nada. Se resuelve con
   `cp .env.example .env` y los valores completados.
3. Un error de acceso denegado o de base inexistente: el `.env` apunta a
   una base que todavía no existe en su máquina. Se resuelve creando la
   base y ejecutando el SQL de las tablas.
4. Posiblemente, un error al grabar en `var/log/`: la carpeta también está
   fuera de Git. Se resuelve con `mkdir -p var/log`, o con el
   `bootstrap.php` creando la carpeta si falta.

El `README.md`:

```text
Para correrlo
1. composer install
2. cp .env.example .env    y completa DB_*
3. mysql -u root -p < sql/esquema.sql
4. mkdir -p var/log
5. composer importar
```

Cinco líneas. La prueba de un buen `README` es dárselo a alguien que nunca
vio el proyecto y no ayudarle. Laravel automatiza buena parte de esto —el
volumen 2 muestra cuánto—, pero el `README` sigue siendo tuyo.
:::
