---
source_hash: a034f93d8d59
title: "El primer proyecto"
number: 5
slug: primeiro-projeto-laravel
part: p2
kicker: "Don Juvenal vio la pantalla de bienvenida, leyó el nombre del framework en letras grandes y preguntó si ya se podían registrar los libros."
goal: >-
  Crear el proyecto de la Casa Amarela con Laravel, entender el papel de
  cada carpeta de primer nivel, saber qué guarda el `.env` y por qué no va
  a Git, y hacer que responda la primera ruta.
---

:::story ¿Ya está listo?
Dedé proyectó la pantalla en la pared de la sala de la asociación para
mostrar que el entorno estaba funcionando. Fondo claro, el nombre del
framework en el medio, algunos enlaces a la documentación alrededor.

Don Juvenal miró unos segundos.

—Lindo. ¿Ya está listo?

—Esta es la pantalla que viene de fábrica.

—Pero ahí está el nombre del sistema.

—Está el nombre del framework.

Don Juvenal señaló la pared con el mentón, como Vera señala el monitor.

—Para mí ahí dice que funciona.
:::

## `composer create-project`

Un comando crea el proyecto entero:

```text
$ composer create-project laravel/laravel casa-amarela
```

```text
Creating a "laravel/laravel" project at "./casa-amarela"
Installing laravel/laravel (v12.0.0)
Created project in /home/dede/casa-amarela

> @php -r "file_exists('.env') || copy('.env.example', '.env');"

Loading composer repositories with package information
Updating dependencies
Package operations: 107 installs, 0 updates, 0 removals
  - Installing symfony/polyfill-mbstring (v1.31.0)
  - Installing illuminate/support (v12.0.0)
  ...
Generating optimized autoload files

> @php artisan key:generate --ansi

   INFO  Application key set successfully.
```

Ciento siete paquetes. Son bastantes más que los tres del `var-dumper`, y
la diferencia es lo que listó el capítulo anterior: cola, correo, sesión,
validación, consola, caché y el resto.

Fíjate en las dos últimas líneas, porque no son instalación: son el
proyecto preparándose. El `.env` se creó a partir del `.env.example`, y se
generó una clave de aplicación. Vas a oír hablar de las dos en cinco
minutos.

## La ruta que responde en dos minutos

```text
$ cd casa-amarela
$ php artisan serve
```

```text
   INFO  Server running on [http://127.0.0.1:8000].

  Press Ctrl+C to stop the server
```

Abre `routes/web.php` y agrega cuatro líneas:

```php title="routes/web.php" numbered
Route::get('/salud', function () {
    return [
        'status' => 'ok',
        'hora' => now()->toIso8601String(),
    ];
});
```

```text
$ curl -s localhost:8000/salud
{"status":"ok","hora":"2026-01-13T09:41:12-03:00"}
```

Pasaron tres cosas sin que las pidieras.

La ruta devolvió un **array**, y llegó JSON. Laravel convierte arrays y
objetos automáticamente, y ya manda el `Content-Type` correcto.

El `now()` existe sin ningún `use`. Es una de las funciones de conveniencia
que el framework registra globalmente, y devuelve un objeto de fecha, no un
texto.

Y la dirección es `/salud`, no `/salud.php`. El front controller del
capítulo @cap:um-framework-de-quarenta-linhas está ahí, en
`public/index.php`, haciendo exactamente lo que hacía el tuyo.

:::trivia
El esqueleto ya viene con una ruta de salud lista, en `/up`, configurada en
el `bootstrap/app.php`. Existe para que el servicio de monitoreo la
consulte y sepa si la aplicación está viva.

La `/salud` de este capítulo es tuya, para que veas funcionar la ruta. En
un proyecto de verdad, quien le responde al monitoreo es `/up`.
:::

## Las carpetas que importan

El proyecto tiene doce carpetas de primer nivel. Seis de ellas las vas a
abrir todos los días.

:::tree title="Lo que existe después del create-project"
casa-amarela/
  app/          # tu código
  bootstrap/    # app.php arma la aplicación; cache/ se genera
  config/       # un archivo por tema
  database/     # migraciones, seeders y factories
  public/       # index.php y archivos servidos directamente
  resources/    # vistas Blade, CSS y JS de origen
  routes/       # web.php y console.php
  storage/      # log, caché, archivos subidos, sesión
  tests/
  vendor/       # de Composer, fuera de Git
  .env          # configuración de esta máquina, fuera de Git
  artisan       # el comando de terminal del proyecto
:::

Tres merecen un párrafo ahora.

**`app/`** empieza casi vacía: un controller base, un model de usuario y un
provider. Es a propósito: Laravel no adivina tu arquitectura, y las
carpetas que crees aquí adentro son decisión tuya.

**`storage/`** es la única carpeta en la que la aplicación **escribe**. El
log, la caché compilada de las vistas, las sesiones y las subidas viven
ahí. Es también el origen del primer error de casi todo el mundo.

**`public/`** es la única que debe ver el servidor web. Todo lo que esté
fuera de ella —el `.env`, el `vendor/`, tu código— queda inalcanzable
desde internet, y eso es lo que separa este proyecto de la carpeta del
Sistema, en la que cualquiera podía descargar el respaldo de 2019.

## El primer error de permisos

Tarde o temprano, y siempre en el servidor:

```text
The stream or file "/var/www/casa-amarela/storage/logs/laravel.log"
could not be opened in append mode: Failed to open stream:
Permission denied
```

La causa es siempre la misma: quien corre PHP en el servidor no eres tú.
Es un usuario del sistema —`www-data` en Debian y Ubuntu, `nginx` o
`apache` en otras distribuciones— y necesita poder escribir en dos
carpetas.

```text
$ sudo chown -R www-data:www-data storage bootstrap/cache
$ sudo chmod -R 775 storage bootstrap/cache
```

:::pitfall
La receta que aparece en los foros es `chmod -R 777 storage`. Funciona, y
significa "cualquier usuario del servidor puede escribir aquí".

En un servidor compartido, eso incluye los otros sitios alojados en la
misma máquina. En un servidor solo tuyo, incluye cualquier proceso que un
atacante logre correr con cualquier usuario.

El `775` con el dueño correcto resuelve el mismo problema y no abre la
puerta. La diferencia entre los dos comandos es de diez segundos para
escribirla y de años para descubrir que fue por ahí.
:::

## `.env`: la configuración de esta máquina

```text title=".env"
APP_NAME="Casa Amarela"
APP_ENV=local
APP_KEY=base64:0sT3qk9...
APP_DEBUG=true
APP_URL=http://localhost

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=casa_amarela
DB_USERNAME=root
DB_PASSWORD=contrasena
```

El `.env` guarda lo que **cambia de máquina a máquina**: dirección de la
base, contraseña, si los errores aparecen en pantalla, adónde van los
correos. Tu máquina tiene uno, el servidor tiene otro, y nunca son iguales.

Tres reglas, y las tres tienen consecuencias.

**El `.env` no entra en Git.** Ya viene en el `.gitignore` del esqueleto.
Lo que entra es el `.env.example`, con las mismas claves y sin los
valores: es el que le cuenta a quien clone el proyecto qué hay que
completar.

**La `APP_KEY` se usa para cifrar.** Las sesiones y los datos cifrados
dependen de ella. Cambiar la clave en un sistema en producción tumba todas
las sesiones abiertas; correr sin ella da error en la primera petición que
necesite cifrado. Se genera una vez, por entorno, y se guarda junto con las
contraseñas.

**`APP_DEBUG=true` nunca va a producción.** Con ella activada, un error
devuelve la página de diagnóstico de Laravel, que muestra el fragmento de
código, los valores de las variables y, según el punto, el contenido del
propio `.env`.

:::key
De Laravel 11 en adelante, la base predeterminada del `.env.example` es
SQLite, porque funciona sin instalar nada.

El proyecto de la Casa Amarela ya tiene un MySQL desde el capítulo
@cap:do-arquivo-ao-banco, con cuatro tablas y datos dentro. Cámbialo a
`mysql` y apúntalo a la base que ya existe.
:::

## Servir el proyecto: elige una

Cuatro formas aparecen en la documentación, y la única decisión equivocada
es intentar las cuatro el primer día.

| Forma | Cuándo sirve |
|---|---|
| `php artisan serve` | ahora, y para el libro entero |
| Laravel Sail | cuando el equipo necesita el mismo entorno |
| Valet | macOS, varios proyectos al mismo tiempo |
| Docker propio | cuando producción ya es Docker |

Tabla: `artisan serve` es el servidor integrado de PHP con las rutas del
proyecto. No sirve para producción y sirve perfectamente para aprender.

:::pitfall
La tentación del primer día es empezar por Docker, "porque así se hace
profesionalmente". En general es así, y el primer día el resultado son dos
horas depurando volúmenes, permisos y red, nada de lo cual tiene que ver
con PHP.

Un contenedor resuelve un problema real: hacer que tu máquina se parezca al
servidor. Ese problema aparece cuando existe un servidor y existe un
equipo. Antes de eso, es solo un problema más.
:::

## Lo que hace el `index.php`

Vale la pena abrir el archivo, porque tiene doce líneas y ya conoces nueve:

```php title="public/index.php" numbered
<?php

use Illuminate\Foundation\Application;
use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

require __DIR__.'/../vendor/autoload.php';

$app = require_once __DIR__.'/../bootstrap/app.php';

$app->handleRequest(Request::capture());
```

El autoload de Composer, la aplicación armada por el `bootstrap/app.php`,
la petición capturada de las superglobales y entregada. Después vienen las
capas, el enrutador, tu código y la respuesta: el dibujo del capítulo
anterior, con nombres de gente grande.

:::tree title="Dónde estamos ahora"
casa-amarela/
  .env              # con el MySQL del proyecto, fuera de Git
  .env.example      # las mismas claves, sin valores
  bootstrap/app.php
  public/index.php
  routes/web.php    # con GET /salud respondiendo
:::

:::summary
- `composer create-project laravel/laravel` crea el esqueleto, copia el
  `.env` y genera la `APP_KEY`.
- Una ruta que devuelve un array se vuelve JSON con la cabecera correcta,
  sin conversión a mano.
- `app/` empieza casi vacía a propósito; la arquitectura interna es tuya.
- `storage/` y `bootstrap/cache/` tienen que poder escribirse por el
  usuario del servidor web, con `775` y el dueño correcto, no con `777`.
- `public/` es la única carpeta que ve el servidor web; `.env` y `vendor/`
  quedan fuera del alcance de internet.
- El `.env` guarda lo que cambia de máquina; queda fuera de Git y el
  `.env.example` entra en su lugar.
- `APP_KEY` cifra la sesión y los datos; `APP_DEBUG=true` en producción
  muestra código y configuración en pantalla.
- `php artisan serve` basta para aprender; Docker resuelve un problema que
  todavía no existe el primer día.
:::

:::checkpoint
Creas un proyecto Laravel, levantas el servidor, escribes una ruta que
responde JSON, explicas el papel de cada carpeta de primer nivel y sabes
decir por qué el `.env` no entra en el repositorio y qué protege la
`APP_KEY`.
:::

:::exercise level=1
Un colega clonó el repositorio del proyecto y recibió, en la primera
petición:

```text
No application encryption key has been specified.
```

Di qué pasó, qué comando lo resuelve y por qué este error no se puede
evitar versionando el `.env`.

:::answer
El `.env` no vino con el repositorio, y no debería venir. Sin él, no hay
`APP_KEY`.

```text
$ cp .env.example .env
$ php artisan key:generate
```

Versionar el `.env` "resolvería" el error y crearía tres problemas peores.
La contraseña de la base de producción entraría en el repositorio, donde
queda para siempre en el historial aunque se quite después. Todos los
entornos pasarían a usar la misma clave de cifrado. Y cada persona del
equipo sobrescribiría la dirección de la base de las demás en cada
`git pull`.

El `.env.example` existe exactamente para eso: lleva las **claves** sin los
**valores**, y el error de arriba es el recordatorio de que falta un paso
de diez segundos.
:::

:::exercise level=2
Agrega a `/salud` tres datos útiles para quien monitorea: la versión de
PHP, si la aplicación está en modo depuración y si la base responde.

Cuidado con lo que expones: la ruta es pública.

:::answer
```php title="routes/web.php" numbered
Route::get('/salud', function () {
    try {
        DB::connection()->getPdo();
        $base = 'ok';
    } catch (\Throwable $e) {
        $base = 'fallo';
    }

    return response()->json([
        'status' => $base === 'ok' ? 'ok' : 'degradado',
        'php' => PHP_VERSION,
        'debug' => config('app.debug'),
        'base' => $base,
    ], $base === 'ok' ? 200 : 503);
});
```

El cuidado que pide el enunciado está en dos decisiones.

**El `catch` no devuelve el mensaje de la excepción.** El rastro de una
falla de conexión contiene host, usuario y a veces contraseña, y esta ruta
es pública. Quien monitorea necesita saber que falló; quien investiga mira
el log.

**El status cambia junto.** Devolver `200` con `"status":"degradado"`
obliga al monitoreo a interpretar el cuerpo. El `503` lo lee cualquier
herramienta sin ninguna configuración.

Una decisión discutible, dejada a propósito: exponer `PHP_VERSION` en una
ruta pública le cuenta a un atacante qué versión atacar. En producción, lo
común es proteger la ruta, o devolver solo `status`, y dejar el detalle
para una ruta interna.
:::

:::exercise level=3
El deploy de la Casa Amarela se hace copiando la carpeta del proyecto al
servidor. En el primer intento, la aplicación arrancó y la página se rompió
con un error de permisos en `storage/logs`.

El pasante ejecutó `chmod -R 777 storage` y funcionó.

Escribe lo que dirías en la revisión: por qué funcionó, cuál es el riesgo
concreto, cuál es la corrección, y cómo evitar que la carpeta vuelva a
copiarse con el dueño equivocado en el próximo deploy.

:::answer
**Por qué funcionó.** `777` da permiso de escritura a todo el mundo, lo que
incluye al usuario que corre PHP. El error desaparece porque el problema
—el dueño equivocado— dejó de importar.

**El riesgo concreto.** Cualquier proceso del servidor pasa a poder
escribir en `storage/`. En un hosting compartido, eso incluye los otros
sitios de la máquina. Y `storage/` no guarda solo el log: guarda las
sesiones y las vistas Blade compiladas, que son **archivos PHP que ejecuta
la aplicación**. Permiso de escritura ahí es, de rebote, permiso de
ejecución.

**La corrección.** Dueño correcto y permiso de grupo:

```text
$ sudo chown -R www-data:www-data storage bootstrap/cache
$ sudo chmod -R 775 storage bootstrap/cache
```

**Cómo no repetirlo.** El problema de fondo no es el permiso: es el deploy
por copia de carpeta, que rehace el dueño cada vez y depende de que alguien
se acuerde de corregirlo. Dos salidas, en orden de esfuerzo.

La barata: poner los dos comandos en el paso de publicación, para que
corran siempre, sin depender de la memoria.

La correcta: no copiar `storage/` en el deploy. Guarda estado —log, sesión,
subidas— y el estado no es parte del código. El camino común es mantenerla
fuera de la carpeta versionada y apuntar a ella, de modo que el deploy
cambie solo el código y no toque nada de lo que escribió la aplicación.
:::
