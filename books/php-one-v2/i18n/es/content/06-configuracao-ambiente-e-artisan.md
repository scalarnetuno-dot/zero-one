---
source_hash: 9fbee50e4cc4
title: "Configuración, entorno y Artisan"
number: 6
slug: configuracao-ambiente-e-artisan
part: p2
kicker: "La multa empezó a salir en cero en producción, y en ninguna otra máquina. La causa fue un comando de optimización ejecutado en el deploy."
goal: >-
  Configurar el proyecto sin esparcir `env()` por el código, entender por
  qué la caché de configuración tumba a quien lo hace, y usar Artisan como
  modelo mental en lugar de una lista de comandos memorizada.
---

:::story Ochenta centavos por cero
La pantalla de devolución empezó a imprimir una multa de R$ 0,00 para
todo el mundo. Solo en producción. En la máquina de Dedé, en la de Tainá y
en el entorno de homologación, el valor salía bien.

—¿Qué cambió en el deploy del viernes?

Tainá abrió el paso a paso de la publicación. Había una línea nueva,
agregada la semana anterior por recomendación de un artículo sobre
rendimiento.

```text
php artisan config:cache
```

—Eso es optimización. No cambia el comportamiento.

—Cambia el comportamiento de quien lee el `.env` en el lugar equivocado.

Dedé buscó en el código. Estaba en la calculadora de multas, línea 14:

```php
$centavos = env('MULTA_CENTAVOS', 0);
```

—El valor predeterminado es cero.

—El valor predeterminado es cero.
:::

## `config()` y `env()`: la diferencia que tumba producción

Laravel tiene dos formas de leer la configuración, y parecen sinónimas
hasta el día en que no lo son.

**`env('CLAVE')`** lee directamente del archivo `.env`.

**`config('archivo.clave')`** lee de un archivo PHP dentro de `config/`,
que se cargó cuando arrancó la aplicación.

La regla que asume todo el framework es corta:

:::key
**`env()` solo dentro de `config/`. `config()` en todo lo demás.**

No es una preferencia de estilo. Es lo que hace que la aplicación siga
funcionando después del `config:cache`, que es el comando que corre casi
todo deploy.
:::

El motivo está en lo que hace `config:cache`: lee todos los archivos de
`config/`, resuelve todo —incluidas las llamadas a `env()` que estén ahí
dentro— y graba el resultado en un solo archivo. A partir de ahí, la
aplicación ni siquiera abre el `.env`.

Y `env()` llamado fuera de `config/` pasa a devolver `null`.

```php
// dentro de config/biblioteca.php: correcto
'multa_diaria_en_centavos' => (int) env('MULTA_CENTAVOS', 80),

// dentro de un service: devuelve null después del config:cache
$centavos = env('MULTA_CENTAVOS', 0);
```

En el caso de la Casa Amarela, `null` se volvió el valor predeterminado
`0`, y el cero predeterminado no dio error: dio una multa en cero, que es
peor, porque un error alguien lo ve.

:::pitfall
El detalle que hace que este defecto atraviese la revisión es que
**funciona en tu máquina**. En desarrollo nadie corre `config:cache`, el
`.env` está ahí, y `env()` responde bien.

Solo aparece donde no estás mirando. Por eso la regla es una regla y no
una recomendación: no existe un caso en que `env()` fuera de `config/` sea
la elección correcta.
:::

## El archivo de configuración del proyecto

Las reglas de la Casa Amarela estaban esparcidas en constantes y números
sueltos. Ahora tienen dirección:

```php title="config/biblioteca.php" numbered
<?php

declare(strict_types=1);

return [
    'plazo_en_dias' => (int) env('BIBLIOTECA_PLAZO_DIAS', 14),

    'plazo_en_dias_infantil' => 7,

    'limite_por_lector' => (int) env('BIBLIOTECA_LIMITE', 3),

    'limite_en_enero' => 5,

    'multa_diaria_en_centavos' => (int) env('MULTA_CENTAVOS', 80),
];
```

```php
$plazo = config('biblioteca.plazo_en_dias');
$multa = config('biblioteca.multa_diaria_en_centavos');
```

El nombre del archivo se vuelve el primer pedazo de la clave, y el punto
baja por el array. Cualquier archivo nuevo en `config/` se encuentra solo,
sin registrar nada.

Fíjate en qué valores pasaron por `env()` y cuáles no. **Va al `.env` lo
que cambia de entorno**; queda fijo en el archivo lo que es regla del
negocio. El plazo de los infantiles es de siete días en cualquier servidor
del mundo, y volverlo variable de entorno solo crea un lugar más donde la
regla puede divergir.

:::pitfall
El segundo argumento de `env()` es el valor predeterminado, y es una
decisión de seguridad cuando la clave es un secreto.

```php
// peligroso
'clave_api' => env('SOCIO_API_KEY', 'prueba'),
'exigir_https' => env('EXIGIR_HTTPS', false),
```

Un valor predeterminado permisivo convierte "me olvidé de configurarlo" en
"salió inseguro y nadie se dio cuenta". Para un secreto y para un
interruptor de seguridad, el valor predeterminado correcto es `null` o el
valor más restrictivo, y que la aplicación falle ruidosamente al arrancar
es el comportamiento deseado.
:::

## Entornos

`APP_ENV` dice en qué entorno está corriendo la aplicación, y tres nombres
son convención:

| `APP_ENV` | Dónde | Qué suele cambiar |
|---|---|---|
| `local` | tu máquina | errores en pantalla, log detallado, el correo no sale |
| `testing` | durante las pruebas | base aparte, no se llama a nada externo |
| `production` | servidor | errores solo en el log, caché activada, todo optimizado |

Tabla: El valor lo lee el framework, que ajusta el comportamiento solo, y
tu código puede leerlo con `app()->environment('production')`.

Para ver qué cree la aplicación que es su realidad:

```text
$ php artisan about
```

```text
  Environment .................................................
  Application Name ............................... Casa Amarela
  Laravel Version ...................................... 12.0.0
  PHP Version ........................................... 8.3.14
  Environment ........................................ production
  Debug Mode ......................................... OFF
  Maintenance Mode ................................... OFF

  Cache .......................................................
  Config ............................................... CACHED
  Routes ............................................. NOT CACHED
```

Dos líneas de esa salida habrían cerrado el viernes de la historia en
treinta segundos: **Config: CACHED**.

## Artisan: tres herramientas con un solo nombre

`artisan` es un archivo en la raíz del proyecto, y lo que ofrece se
organiza en tres familias.

**Es un generador.** `make:controller`, `make:model`, `make:migration`,
`make:command`. Escribe el archivo en el lugar correcto, con el nombre
correcto y el esqueleto correcto, ahorrando menos tecleo de lo que parece
y más dudas de lo que parece.

**Es un inspector.** `about`, `route:list`, `config:show`, `db:show`. Estos
responden preguntas sobre el estado del proyecto, y son los que vas a usar
en un servidor ajeno a las dos de la tarde.

**Es un control remoto.** `migrate`, `queue:work`, `schedule:run`,
`cache:clear`, y los comandos que escribas tú. Estos **hacen** algo.

```text
$ php artisan route:list
```

```text
  GET|HEAD   /                    ......................
  GET|HEAD   salud                ......................
  GET|HEAD   up                   ......................
```

:::key
`route:list` es la única documentación de API que nunca miente, porque no
se escribe: se lee del código que está corriendo.

Al entrar en un proyecto Laravel desconocido, es el primer comando que hay
que correr. En diez segundos tienes el índice de toda la aplicación.
:::

## `tinker`: la consola que conoce el proyecto

```text
$ php artisan tinker
```

```text
Psy Shell v0.12.4 (PHP 8.3.14 — cli)

> config('biblioteca.multa_diaria_en_centavos')
= 80

> now()->addDays(config('biblioteca.plazo_en_dias'))->toDateString()
= "2026-01-27"

> app()->environment()
= "local"
```

Es una consola PHP con **toda** la aplicación cargada: configuración, base,
tus clases, todo resuelto por el contenedor. Sirve para revisar una regla,
mirar un dato y probar una expresión sin crear un archivo.

:::pitfall
`tinker` en producción es una herramienta legítima y peligrosa por el
mismo motivo: ejecuta cualquier cosa, con las credenciales de la
aplicación, sin dejar registro de lo que se hizo.

Consultar es razonable. Modificar datos por ahí es un cambio sin revisión,
sin historial y sin forma de repetirlo, y al día siguiente nadie sabe
explicar por qué ese préstamo tiene una fecha distinta.

Cuando necesites corregir datos en producción, escribe un comando. Tiene
nombre, tiene código revisado y deja rastro.
:::

## Un comando propio

Cada madrugada, la Casa Amarela tiene que recalcular las multas de los
préstamos vencidos.

```text
$ php artisan make:command CerrarMultasDelDia
```

```php title="app/Console/Commands/CerrarMultasDelDia.php" numbered
<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Services\CalculadoraDeMultas;
use Illuminate\Console\Command;

class CerrarMultasDelDia extends Command
{
    protected $signature = 'biblioteca:multas {--fecha=}';

    protected $description = 'Calcula las multas de los vencidos';

    public function handle(CalculadoraDeMultas $calculadora): int
    {
        $fecha = $this->option('fecha') ?? now()->toDateString();

        $resultado = $calculadora->cerrarDia($fecha);

        $this->info("Día {$fecha}: {$resultado->cantidad} multas");
        $this->info("Total: {$resultado->total->formateado()}");

        return self::SUCCESS;
    }
}
```

Tres cosas para notar.

**El `handle()` recibe la calculadora como parámetro.** Nadie pasó nada:
el contenedor leyó el tipo y lo resolvió, exactamente como el contenedor
ingenuo del capítulo @cap:um-framework-de-quarenta-linhas.

**El comando no calcula nada.** Lee la opción, llama al servicio e imprime
el resultado. Toda la regla vive en una clase que no sabe que existe una
terminal, y por eso la misma regla atiende la pantalla, la API y el
comando.

**Devuelve un código.** `self::SUCCESS` es cero; `self::FAILURE` es uno. Es
lo que lee el programador de tareas del sistema operativo para saber si la
tarea de la madrugada salió bien.

```text
$ php artisan biblioteca:multas --fecha=2026-01-12
```

```text
Día 2026-01-12: 7 multas
Total: R$ 12,80
```

Para que corra solo, la programación queda en `routes/console.php`:

```php title="routes/console.php" numbered
use Illuminate\Support\Facades\Schedule;

Schedule::command('biblioteca:multas')
    ->dailyAt('03:00')
    ->withoutOverlapping();
```

El `withoutOverlapping()` impide que una ejecución empiece mientras la
anterior todavía está corriendo, lo que pasa el día en que la base está
lenta y la tarea de las tres de la mañana todavía no terminó a las tres y
uno.

:::note En tu carrera
"En mi máquina funciona" tiene una versión moderna y más difícil de ver:
funciona en todas partes **menos** en producción, porque producción es el
único entorno que corre los comandos de optimización.

La lista es corta y vale la pena tenerla en la cabeza: `config:cache` rompe
a quien usa `env()` fuera de `config/`; `route:cache` rompe las rutas que
usan funciones anónimas; `view:cache` esconde cambios de plantilla.

Cuando un defecto aparece solo en producción y no huele a datos, empieza
por `php artisan about` y mira qué está en caché. Vas a parecer adivino unas
tres veces al año.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  config/
    biblioteca.php    # plazo, límite y multa
  app/
    Console/Commands/
      CerrarMultasDelDia.php
    Services/
      CalculadoraDeMultas.php
  routes/
    console.php       # programación a las 3 h
    web.php
:::

:::summary
- `env()` solo dentro de `config/`; `config()` en el resto del código.
- `config:cache` resuelve los archivos de `config/` en uno solo y hace que
  la aplicación deje de leer el `.env`: `env()` fuera de ahí pasa a
  devolver `null`.
- El nombre del archivo en `config/` se vuelve el primer pedazo de la
  clave, y se encuentra solo.
- Va al `.env` lo que cambia de entorno; la regla de negocio queda fija en
  el archivo de configuración.
- Un valor predeterminado permisivo en un secreto convierte un olvido en
  una falla silenciosa.
- `APP_ENV` distingue `local`, `testing` y `production`, y el framework
  ajusta el comportamiento solo.
- Artisan es generador, inspector y control remoto; `about` y `route:list`
  son las dos primeras cosas que hay que correr en un proyecto
  desconocido.
- Un comando propio lee opciones, llama al servicio y devuelve un código de
  salida: no contiene reglas.
:::

:::checkpoint
Creas un archivo de configuración y lo lees con `config()`, explicas por
qué `env()` fuera de `config/` se rompe después del deploy, inspeccionas un
proyecto desconocido con `about` y `route:list`, y escribes un comando que
delega el trabajo a un servicio y devuelve un código de salida.
:::

:::exercise level=1
Clasifica cada valor: ¿va al `.env`, queda fijo en `config/`, o no debería
estar en ninguna configuración?

1. La contraseña de la base.
2. El plazo de préstamo, catorce días.
3. El límite de tres libros por lector.
4. La dirección del servidor de correo.
5. El texto del mensaje de multa que aparece en pantalla.

:::answer
1. **`.env`.** Cambia por entorno y es secreta. Nunca con valor
   predeterminado.
2. **Fijo en `config/`.** Es una regla del negocio y es igual en todas
   partes. Tenerlo en el `.env` solo crearía la posibilidad de que
   homologación y producción discrepen sobre una regla de Vera.
3. **Fijo en `config/`**, por el mismo motivo, con una salvedad: si la
   asociación un día quiere cambiar ese número sin publicar código, deja de
   ser configuración y se vuelve un **dato**, guardado en la base y editable
   en una pantalla.
4. **`.env`.** Cambia por entorno, y en desarrollo suele apuntar a un
   servidor falso.
5. **Ninguno de los dos.** El texto de la interfaz vive en los archivos de
   traducción o en la vista. La configuración es para valores que deciden
   el comportamiento, no para frases que aparecen en pantalla.

El criterio de los cinco cabe en una pregunta: *¿dos máquinas distintas
necesitan valores distintos?* Si sí, `.env`. Si no, `config/`. Si la
respuesta es "el cliente va a querer cambiar esto solo", ninguno de los
dos.
:::

:::exercise level=2
Escribe el comando `biblioteca:atrasados`, que lista los préstamos vencidos
y todavía no devueltos, con una opción `--lector=` para filtrar por lector.

Usa `$this->table()` para imprimir el resultado y devuelve `FAILURE`
cuando haya algún atrasado, para que el programador de tareas registre el
día como anormal.

:::answer
```php title="app/Console/Commands/ListarAtrasados.php" numbered
<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Services\ConsultaDeAtrasos;
use Illuminate\Console\Command;

class ListarAtrasados extends Command
{
    protected $signature = 'biblioteca:atrasados {--lector=}';

    protected $description = 'Lista los vencidos abiertos';

    public function handle(ConsultaDeAtrasos $consulta): int
    {
        $lector = $this->option('lector');

        $filas = $consulta->abiertos(
            $lector === null ? null : (int) $lector,
        );

        if ($filas === []) {
            $this->info('Ningún atrasado.');

            return self::SUCCESS;
        }

        $this->table(
            ['Registro', 'Título', 'Lector', 'Días'],
            $filas,
        );

        return self::FAILURE;
    }
}
```

Dos decisiones merecen defensa.

**El `(int)` en la opción.** Toda opción de línea de comandos llega como
texto, como todo lo que viene de fuera. La conversión ocurre en la
frontera, y el servicio recibe el tipo correcto.

**El `FAILURE` con la lista no vacía** es lo que pide el enunciado y merece
una salvedad honesta: un código de salida distinto de cero suele
significar "el comando falló", no "el comando encontró cosas". Si este
comando se programa junto con otros, un programador que se detiene en la
primera falla se va a detener aquí.

La salida más usada en producción es devolver `SUCCESS` siempre y emitir
una alerta aparte cuando el número pase de un límite, porque el atraso es
un hecho del negocio, no un defecto del programa.
:::

:::exercise level=3
Un proyecto tiene, esparcidas por el código, treinta y una llamadas a
`env()` fuera de `config/`. Nunca corrió `config:cache`, y el equipo quiere
empezar a correrlo para ganar rendimiento en el deploy.

Escribe el plan de migración en cuatro pasos, incluido cómo descubrir las
llamadas y cómo garantizar que no aparezca ninguna nueva.

:::answer
**Paso 1: encontrar.** Una búsqueda lo resuelve, y el resultado es la
lista de trabajo:

```text
$ grep -rn "env(" app/ routes/ database/ | grep -v "config/"
```

**Paso 2: mover, no traducir.** Para cada llamada, crear la clave
correspondiente en `config/`, apuntando al mismo `env()` con el mismo
valor predeterminado, y cambiar la llamada en el código por `config()`. Es
importante que el valor predeterminado sea **el mismo** en este paso:
cambiar el comportamiento y cambiar el mecanismo al mismo tiempo es la
forma de no saber cuál de los dos se rompió.

**Paso 3: revisar los valores predeterminados, ahora por separado.** Con
todo en `config/`, se pueden leer las treinta y una líneas juntas y
preguntar de cada una si el valor predeterminado tiene sentido. Aquí es
donde aparece el `env('MULTA_CENTAVOS', 0)`, y aquí es donde debe
corregirse, no en el paso anterior.

**Paso 4: impedir que vuelva.** Sin esto, la llamada número treinta y dos
entra en dos semanas. Dos formas, y la segunda es la que sostiene:

La barata es una línea en la revisión de código. La confiable es una regla
automática en el paso de verificación, que rechaza el cambio si encuentra
`env(` fuera de `config/`. La misma búsqueda del paso 1, con código de
salida.

Y un quinto paso que no es migración: correr `config:cache` **también** en
el entorno de homologación. Mientras producción sea el único lugar donde
corre el comando, producción sigue siendo el lugar donde se descubre este
tipo de defecto.
:::
