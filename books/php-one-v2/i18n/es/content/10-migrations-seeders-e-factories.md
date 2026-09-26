---
source_hash: 002b96c07acb
title: "Migrations, seeders y factories"
number: 10
slug: migrations-seeders-e-factories
part: p3
kicker: "Las once y cuarenta de un jueves. La terminal escribió Dropping all tables y él leyó la dirección de la base en la línea de arriba."
goal: >-
  Versionar el esquema de la base en archivos que cuentan la historia de
  los cambios, modificar una columna sin tumbar la aplicación, y tener
  datos de desarrollo que cualquier persona del equipo pueda reproducir.
---

:::story Dropping all tables
Dedé iba a recrear la base de homologación para probar la migración del
acervo desde cero. Ejecutó el comando de siempre.

```text
$ php artisan migrate:fresh --seed

  Dropping all tables ................................ 214ms DONE
```

Miró la línea de arriba de la salida mientras se desplazaba. La terminal
abierta era la de la sesión de la mañana, esa en la que había entrado al
servidor para revisar algo.

```text
DB_HOST=db.casaamarela.org.br
```

Se quedó unos dos segundos sin hablar.

—Tainá.

—¿Sí?

—¿Cuánto respaldo tenemos?

Ella buscó. Rutina diaria, a las tres de la mañana.

—De ayer, a las tres.

—Entonces perdimos la mañana.

—La mañana y los ochocientos ejemplares que Vera catalogó ayer a la
tarde.
:::

## Una migration no es un respaldo

Una migration describe **la estructura**: qué tablas existen, con qué
columnas y qué restricciones. No guarda ni una fila de datos.

Parece obvio y es la confusión más cara que existe, porque un comando con
nombre amable —`migrate:fresh`— borra todo y recrea el esqueleto vacío, y
sale como entró: sin ningún error.

:::key
Las migrations recrean la **base**. El respaldo recrea el **sistema**.

Son dos garantías distintas, y la segunda es la única que responde por un
jueves a la mañana.
:::

:::art caption="El comando era el de siempre. La terminal era la de producción."
src="o-comando-era-o-de-sempre-o-terminal-era-o-de-producao.png"
Viñeta editorial minimalista sobre fondo blanco: un desarrollador de
treinta y pocos años, de buzo, congelado frente al portátil, la mano
todavía en el teclado, mientras la pantalla muestra "Dropping all tables
... DONE" con un visto verde. Detrás del portátil, un estante de biblioteca
dibujado con trazo fino se vacía: los libros se deshacen en puntos, de la
repisa de arriba hacia abajo. Al lado, una pasante mira un reloj de pared
que marca las 3 h, con una etiqueta "respaldo". Pocos elementos, humor
seco, estética de revista de tecnología.
:::

## El esquema se vuelve archivo

```text
$ php artisan make:migration create_libros_table
```

```text
   INFO  Migration [database/migrations/
   2026_01_14_103211_create_libros_table.php] created successfully.
```

El nombre empieza con la fecha y la hora, y eso es lo que da el **orden**.
La tabla de ejemplares tiene que existir después de la de libros, porque
apunta a ella, y quien lo garantiza es el sello en el nombre del archivo.

```php title="..._create_libros_table.php" numbered
<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('libros', function (Blueprint $t) {
            $t->id();
            $t->string('titulo', 200);
            $t->string('autor', 150);
            $t->char('isbn', 13)->nullable()->unique();
            $t->string('tema', 40);
            $t->smallInteger('anio')->nullable();
            $t->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('libros');
    }
};
```

Es el `CREATE TABLE` del capítulo @cap:duas-tabelas-conversando, escrito en
PHP. Lado a lado:

```sql
CREATE TABLE libros (
  id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  titulo  VARCHAR(200) NOT NULL,
  autor   VARCHAR(150) NOT NULL,
  isbn    CHAR(13)     NULL,
  tema    VARCHAR(40)  NOT NULL,
  anio    SMALLINT     NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY libros_isbn_unique (isbn)
) ENGINE=InnoDB;
```

`$t->id()` es la clave primaria con incremento. `$t->timestamps()` crea las
dos columnas de fecha que el esquema escrito a mano no tenía, y entran
ahora por dos razones: Eloquent las mantiene solo, y "cuándo entró este
ejemplar al acervo" es una pregunta que va a hacer Vera.

La clave foránea cabe en una línea:

```php
$t->foreignId('libro_id')->constrained();
```

El nombre de la columna termina en `_id`, así que Laravel deduce la tabla
`libros` y la columna `id`. Es la convención haciendo el trabajo, y cuando
el nombre no siga el patrón, `constrained('libros')` lo dice
explícitamente.

## El estado de la base vive en una tabla

```text
$ php artisan migrate
```

```text
   INFO  Running migrations.

  2026_01_14_103211_create_libros_table .......... 34ms DONE
  2026_01_14_103245_create_ejemplares_table ...... 41ms DONE
  2026_01_14_103302_create_lectores_table ........ 28ms DONE
  2026_01_14_103330_create_prestamos_table ....... 52ms DONE
```

Laravel guarda lo que ya corrió en una tabla llamada `migrations`:

```text
mysql> SELECT * FROM migrations;
+----+------------------------------------+-------+
| id | migration                          | batch |
+----+------------------------------------+-------+
|  1 | 2026_01_14_103211_create_libros... |     1 |
|  2 | 2026_01_14_103245_create_ejemp...  |     1 |
+----+------------------------------------+-------+
```

Por eso ejecutar `migrate` dos veces no hace nada la segunda: compara la
carpeta con la tabla y corre solo lo que falta.

La columna `batch` agrupa lo que subió junto, y es lo que usa el
`rollback`: `migrate:rollback` deshace el último lote entero, no la última
migration.

| Comando | Qué hace |
|---|---|
| `migrate` | corre lo que todavía no corrió |
| `migrate:status` | muestra lo que corrió y lo que falta |
| `migrate:rollback` | deshace el último lote |
| `migrate:fresh` | **borra todas las tablas** y corre todo de nuevo |

Tabla: Los tres primeros son seguros en cualquier entorno. El cuarto es el
de la historia.

## Un `down()` honesto

Todo `up()` tiene un `down()`, y la tentación es llenarlo por obligación.

```php
public function down(): void
{
    Schema::table('libros', function (Blueprint $t) {
        $t->dropColumn('tema');
    });
}
```

Eso deshace la estructura y **borra los datos de esa columna**. Si la
migration ya corrió en producción, el `down` es una pérdida de datos con
cara de arrepentimiento.

:::pitfall
Hay migrations que no tienen vuelta honesta: las que juntan dos columnas en
una, las que convierten el formato, las que borran registros duplicados.

Para esas, el `down` correcto es negarse:

```php
public function down(): void
{
    throw new RuntimeException(
        'Esta migration no se puede deshacer: restaura el respaldo.'
    );
}
```

Es más honesto que un `down` que finge. Quien ejecute el `rollback` recibe
la verdad en lugar de una base que parece revertida y perdió la mitad de
una columna.
:::

## Modificar una columna sin tumbar la aplicación

La asociación pidió que el tema del libro dejara de ser texto libre y
pasara a apuntar a una tabla de temas.

La tentación es una migration que cambia la columna. El problema es el
intervalo: si la aplicación está en producción, existe un momento en que el
código viejo busca la columna vieja en una base que ya cambió.

El camino que no tumba tiene dos etapas, y lleva dos deploys.

**Expandir.** Una migration agrega la columna nueva, sin tocar la vieja. El
código pasa a **escribir en las dos** y a leer de la nueva cuando esté
completa. Nada se rompe, porque no se quitó nada.

**Contraer.** Después de que todo el dato se convirtió y ningún código lee
ya la columna vieja, una segunda migration la quita.

| Etapa | Migration | Código |
|---|---|---|
| 1 | crea `tema_id` | escribe en las dos, lee la nueva |
| 2 | — | convierte el historial |
| 3 | quita `tema` | lee y escribe solo la nueva |

Tabla: Tres pasos para lo que parecía uno. Es el precio de no tener una
ventana de mantenimiento, y es el procedimiento estándar en cualquier
sistema que no puede detenerse.

:::pitfall
Nunca edites una migration que ya corrió en producción.

Está registrada en la tabla `migrations`, así que Laravel no la va a correr
de nuevo, y tu máquina, donde borraste la base y la recreaste, queda con un
esquema distinto al de producción sin que nada avise.

La modificación de una tabla existente es siempre una migration **nueva**.
:::

## Seeder: el dato que necesita todo entorno

Hay datos que no son de prueba: la lista de temas del acervo, el usuario
administrador inicial, los estados posibles. Sin ellos el sistema no
funciona en ninguna parte.

```php title="database/seeders/TemaSeeder.php" numbered
<?php

declare(strict_types=1);

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class TemaSeeder extends Seeder
{
    public function run(): void
    {
        $temas = [
            'literatura', 'didactico', 'infantil',
            'referencia', 'historia', 'ciencias',
        ];

        foreach ($temas as $nombre) {
            DB::table('temas')->updateOrInsert(['nombre' => $nombre]);
        }
    }
}
```

El `updateOrInsert` es la diferencia entre un seeder que puede correr dos
veces y uno que duplica todo en la segunda. Un seeder de datos esenciales
tiene que ser repetible: va a correr en todo deploy de un entorno nuevo, y
más de una vez en la vida de alguien distraído.

## Factory: el dato falso que parece verdadero

Para desarrollar y probar, necesitas un acervo. Cuatro mil libros escritos
a mano no son una opción.

```php title="database/factories/LibroFactory.php" numbered
<?php

declare(strict_types=1);

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

class LibroFactory extends Factory
{
    public function definition(): array
    {
        return [
            'titulo' => fake()->sentence(3),
            'autor' => fake()->name(),
            'isbn' => fake()->unique()->isbn13(),
            'tema' => fake()->randomElement([
                'literatura', 'didactico', 'infantil',
            ]),
            'anio' => fake()->numberBetween(1890, 2026),
        ];
    }

    public function infantil(): static
    {
        return $this->state(fn (): array => [
            'tema' => 'infantil',
            'anio' => fake()->numberBetween(2000, 2026),
        ]);
    }
}
```

```php
Libro::factory()->count(200)->create();

Libro::factory()->infantil()->count(30)->create();

Libro::factory()->create(['titulo' => 'Dom Casmurro']);
```

El `infantil()` es un **estado**: una variación con nombre del estándar.
Existe para que una prueba sobre la regla de siete días pueda pedir
exactamente el caso que necesita, sin armar el libro campo por campo.

Para que los nombres salgan en portugués, como los de los lectores de la
Casa Amarela, una línea en el `.env`:

```text
APP_FAKER_LOCALE=pt_BR
```

:::pitfall
Una factory que solo produce el caso feliz es una trampa lenta.

Si todo `Libro` generado tiene ISBN, año y tema completos, ninguna prueba
va a ejercitar el libro antiguo sin ISBN, que existe por centenas en el
acervo real de la Casa Amarela, porque el ISBN recién empezó a usarse en
los años setenta.

La factory tiene que reflejar la **variedad** de los datos reales, no su
versión idealizada. Una buena pregunta al escribirla: *¿cuál es el registro
más raro que existe hoy en producción?*
:::

## Quién corre las migrations en producción

La pregunta tiene una respuesta técnica corta y una respuesta de proceso,
y la segunda es la que importa.

La técnica: `php artisan migrate --force`. El `--force` existe porque, en
`production`, el comando pregunta antes, y en un paso automatizado no hay
nadie para responder.

La de proceso es una lista:

1. **El comando corre en el deploy**, no a mano. La mano se equivoca de
   terminal.
2. **`migrate:fresh` no existe en producción.** La forma de garantizarlo no
   es la disciplina: es que el usuario de la base de producción no tenga
   permiso para borrar tablas.
3. **Respaldo antes**, y comprobado: un respaldo que nadie restauró nunca
   no es un respaldo, es un archivo.
4. **La terminal de producción tiene otra cara.** Prompt rojo, nombre del
   entorno visible. Cuesta cinco minutos y resuelve toda la categoría de
   error de la historia de este capítulo.

:::note En tu carrera
En algún momento vas a borrar algo importante. Prácticamente todo el que
trabaja con sistemas en producción el tiempo suficiente tiene una historia
así.

Lo que separa a las personas no es tener o no tener la historia: es lo que
pasó después. Avisar en el acto, con la hora exacta de lo que se perdió, es
la diferencia entre una mañana mala y una tarde catastrófica, porque el
equipo puede detener lo que esté escribiendo encima y restaurar con
precisión.

Esconderlo veinte minutos para "intentar resolverlo solo" es lo que
convierte ochocientos ejemplares en ochocientos ejemplares más todo lo que
se grabó mientras nadie lo sabía.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  database/
    migrations/
      ..._create_libros_table.php
      ..._create_ejemplares_table.php
      ..._create_lectores_table.php
      ..._create_prestamos_table.php
    seeders/
      DatabaseSeeder.php
      TemaSeeder.php
    factories/
      LibroFactory.php
      EjemplarFactory.php
      LectorFactory.php
:::

:::summary
- Una migration versiona la estructura, no los datos; `migrate:fresh` borra
  todo y no se queja.
- El sello de fecha en el nombre del archivo es lo que define el orden de
  ejecución.
- La tabla `migrations` registra lo que ya corrió, agrupado en lotes; el
  `rollback` deshace un lote entero.
- Un `down` que finge deshacer es peor que un `down` que se niega.
- La modificación de una columna en un sistema en producción se hace en
  dos etapas: expandir y, después, contraer.
- Nunca edites una migration que ya corrió en producción; la corrección es
  una migration nueva.
- El seeder carga datos esenciales y tiene que ser repetible.
- La factory genera datos de desarrollo, y tiene que representar la
  variedad de la base real, no el caso feliz.
- En producción, la migration corre en el deploy, con respaldo comprobado y
  sin permiso para borrar tablas.
:::

:::checkpoint
Creas el esquema con migrations, sabes qué controla el `batch` de la tabla
`migrations`, modificas una columna sin tumbar la aplicación, y generas un
acervo falso con estados que representan los casos difíciles.
:::

:::exercise level=1
Escribe la migration de la tabla `ejemplares`, con `registro` único,
`libro_id` apuntando a `libros` y `condicion` con valor predeterminado.

Después di por qué el `down()` de esa migration es honesto, al contrario
del ejemplo del capítulo.

:::answer
```php title="..._create_ejemplares_table.php" numbered
public function up(): void
{
    Schema::create('ejemplares', function (Blueprint $t) {
        $t->id();
        $t->foreignId('libro_id')->constrained();
        $t->unsignedInteger('registro')->unique();
        $t->string('condicion', 20)->default('bueno');
        $t->timestamps();
    });
}

public function down(): void
{
    Schema::dropIfExists('ejemplares');
}
```

El `down()` es honesto porque el `up()` **creó** la tabla. Deshacer la
creación de una tabla es borrarla, y ningún dato existía antes de ella:
quien revierta vuelve exactamente al estado anterior.

El ejemplo del capítulo era otro caso: `dropColumn('tema')` en una tabla
que ya existía. Ahí el `down` no devuelve el estado anterior, porque los
valores de la columna no están en ninguna parte.

La regla: **el `down` de un `create` es seguro; el `down` de un `alter`
casi nunca lo es.**
:::

:::exercise level=2
Vera pidió que el sistema guardara, para cada ejemplar, la fecha en que
entró al acervo, información que hoy está solo en la etiqueta.

La tabla tiene ochocientos registros y el sistema está en producción.
Escribe el plan completo, con las migrations y lo que hace el código en
cada etapa.

:::answer
**Etapa 1: expandir.** La columna nace aceptando nulos, porque los
ochocientos registros existentes no tienen valor:

```php
Schema::table('ejemplares', function (Blueprint $t) {
    $t->date('adquirido_en')->nullable()->after('condicion');
});
```

El código pasa a completar la columna en todo registro nuevo. La pantalla
muestra la fecha cuando existe y "no informado" cuando no. Nada se rompe, y
nada se perdió.

**Etapa 2: completar el historial.** Aquí hay una decisión de producto, no
técnica: ¿de dónde sale la fecha de los ochocientos antiguos?

Si Vera tiene la información en las fichas, la escribe a lo largo de las
semanas. Si no la tiene, la alternativa es usar una aproximación —la fecha
de creación del registro— y **registrar que es aproximada**, en una
columna más o en un valor convenido. Inventar un dato y presentarlo como
exacto es el origen de un informe equivocado dentro de dos años.

**Etapa 3: contraer.** Solo si y cuando la columna deje de poder ser nula:

```php
Schema::table('ejemplares', function (Blueprint $t) {
    $t->date('adquirido_en')->nullable(false)->change();
});
```

Y esta etapa tiene una condición de entrada verificable: `SELECT COUNT(*)
FROM ejemplares WHERE adquirido_en IS NULL` tiene que devolver cero. Correr
la migration antes de eso tumba el deploy.
:::

:::exercise level=3
Reescribe este seeder, señalando los cuatro problemas:

```php
class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        DB::table('usuarios')->insert([
            'nombre' => 'Administrador',
            'email' => 'admin@admin.com',
            'contrasena' => md5('123456'),
            'perfil' => 'admin',
        ]);

        Libro::factory()->count(5000)->create();

        DB::table('temas')->insert([
            ['nombre' => 'literatura'],
            ['nombre' => 'didactico'],
        ]);
    }
}
```

:::answer
**Uno: la contraseña.** `md5('123456')` es el defecto del capítulo
@cap:conversao-automatica volviendo por la puerta de atrás, ahora escrito
por nosotros. La contraseña se guarda con `Hash::make()`, y la contraseña
del administrador inicial no queda en el código: viene del entorno, o el
usuario lo crea un comando que la pide.

**Dos: datos de prueba mezclados con datos esenciales.** Los cinco mil
libros falsos están en el mismo lugar que los temas, que son reales. El día
en que alguien ejecute `db:seed` en producción para crear los temas, el
acervo recibe cinco mil títulos inventados.

Separarlos en dos seeders y llamar al de datos falsos solo donde tiene
sentido:

```php
public function run(): void
{
    $this->call(TemaSeeder::class);

    if (app()->environment('local', 'testing')) {
        $this->call(AcervoFalsoSeeder::class);
    }
}
```

**Tres: el `insert` no es repetible.** Ejecutarlo dos veces duplica los
temas, y la segunda ejecución falla si hay un índice único, dejando el
seeder a medias. `updateOrInsert` lo resuelve.

**Cuatro: cinco mil registros uno por uno.** Cada `create()` de la factory
es un `INSERT` aparte. Cinco mil inserciones tardan minutos, y el seeder se
vuelve algo que nadie ejecuta. La forma por lotes (`->make()` más una
inserción en bloques) lo resuelve, al costo de no disparar los eventos del
model, que en un dato falso no importan.

Y un quinto, que no estaba en la lista y vale la pena decir:
`admin@admin.com` con contraseña `123456` en un seeder es una credencial
predeterminada. Tienen la costumbre de sobrevivir hasta producción, y son
lo primero que prueba cualquier escaneo automático.
:::
