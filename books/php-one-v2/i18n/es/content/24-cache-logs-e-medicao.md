---
source_hash: 61aec468041c
title: "Caché, logs y lo que se mide"
number: 24
slug: cache-logs-e-medicao
part: p6
kicker: "La página del acervo se volvió rápida y empezó a mostrar como disponible un libro que estaba prestado. Durante seis horas, que era el tiempo de validez de la caché."
goal: >-
  Hacer la aplicación observable y rápida, en ese orden: medir antes de
  optimizar, cachear con una estrategia de invalidación escrita, y registrar
  logs estructurados en los que se pueda buscar, sin grabar nunca lo que no
  se puede grabar.
---

:::story Seis horas
La queja llegó por Vera, que la oyó en el mostrador.

—La muchacha dice que la aplicación mostró *La hora de la estrella*
disponible. Cruzó el barrio para ir a buscarlo. Está prestado desde ayer en
la mañana.

Dedé abrió la aplicación. Ahí estaba: *La hora de la estrella*, "1
disponible", en verde.

Abrió el panel de Vera, que consultaba la base directamente. Cero
disponibles. Prestado a las 9:14 del día anterior.

—Caché —dijo él.

—¿Qué? —preguntó Vera.

—La semana pasada el listado del acervo estaba lento. Cléber puso una
caché. La lista queda guardada y solo se rehace de vez en cuando.

—¿Cada cuánto?

Dedé buscó.

```php
Cache::remember('acervo', 60 * 60 * 6, fn () => /* ... */);
```

—Seis horas.

—Entonces durante seis horas la aplicación miente.

—Hasta seis horas.

—¿Y quién decidió seis horas?

Dedé buscó en la tarea, en el commit, en la conversación del grupo. No
había nada.

—Creo que nadie —dijo él—. Creo que es un número que parecía razonable.

—A la que cruzó el barrio no le pareció —dijo Vera.
:::

## Una cola existe porque esperar cuesta caro; una caché también

El capítulo anterior sacó de la petición el trabajo que no necesitaba
ocurrir antes de la respuesta. La caché ataca el mismo costo por otro lado:
**no rehacer** el trabajo que ya se hizo y cuyo resultado no cambió.

El listado de los más prestados del mes agrupa quinientos mil préstamos,
los junta con ejemplares y libros, y ordena. Tarda ochocientos
milisegundos. El resultado cambia algunas decenas de veces al día, y se
consulta algunos miles. Calcularlo en cada consulta es pagar ochocientos
milisegundos miles de veces para obtener, casi siempre, la misma
respuesta.

La caché guarda la respuesta y la devuelve hasta que haya que recalcularla.
Y toda la dificultad está en ese "hasta que".

:::key
Cachear es fácil. Lo difícil es responder: **¿cuándo deja de ser verdad
este valor, y quién le avisa a la caché?**

Una caché sin respuesta para esa pregunta es un lugar donde la aplicación
guarda mentiras con fecha de vencimiento.
:::

## Medir antes de optimizar

La historia tiene un detalle que no está en ella: nadie midió por qué el
listado del acervo estaba lento antes de poner la caché. La caché resolvió
la lentitud y creó la mentira. Con una medición, quizá la respuesta habría
sido otra.

Laravel da tres formas de medir, en orden creciente de esfuerzo.

**Contar consultas**, con el `DB::listen` del capítulo
@cap:relacionamentos:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    if ($this->app->isLocal()) {
        DB::listen(function (QueryExecuted $q) {
            if ($q->time > 100) {
                Log::channel('lentas')->warning('consulta lenta', [
                    'sql' => $q->sql,
                    'ms' => $q->time,
                ]);
            }
        });
    }
}
```

**El *slow query log* de MySQL**, que registra toda consulta que pase de
cierto tiempo, en producción, sin tocar el código:

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.5;
```

**Herramientas de inspección en desarrollo.** Telescope, del propio
Laravel, graba cada petición con las consultas, los jobs, los logs y las
excepciones que produjo, y lo muestra en un panel. Debugbar pone el mismo
resumen en una barra al pie de cada página del panel Blade. Los dos son
para desarrollo, y van en `require-dev` por el motivo del capítulo
@cap:do-include-ao-composer.

Tainá encendió Telescope y abrió el listado del acervo. La petición tardaba
1,9 segundos y hacía cuatro consultas. Tres tardaban dos milisegundos cada
una. La cuarta tardaba 1,8 segundos:

```sql
SELECT COUNT(*) FROM ejemplares
WHERE libro_id = libros.id AND condicion = 'bueno'
```

El conteo de ejemplares disponibles, sin índice compuesto. El `EXPLAIN`
del capítulo @cap:duas-tabelas-conversando mostró que la base leía los
ocho mil ejemplares por cada libro de la página.

```php
$t->index(['libro_id', 'condicion']);
```

Una migration de una línea. El listado bajó a cuarenta milisegundos, **sin
caché**, y sin mentir.

:::pitfall
La caché esconde la lentitud, y esconder no es resolver. La consulta de
1,8 segundos sigue ahí, corriendo cada seis horas, y corriendo en la
primera petición después de que la caché expira, que es la que paga la
cuenta entera. Si diez personas llegan en ese segundo, las diez pagan: diez
consultas de 1,8 segundos al mismo tiempo.

Optimizar a partir de la medición es cambiar la causa. Cachear sin medir es
barrer debajo de la alfombra.
:::

## `Cache::remember` y la pregunta difícil

Hay lugares donde la caché es la respuesta correcta, y los más prestados
del mes son uno: la consulta es cara por naturaleza —agregar medio millón
de filas— y el resultado puede estar unos minutos atrasado sin que nadie
cruce el barrio por eso.

```php title="app/Acervo/MasPrestados.php" numbered
final class MasPrestados
{
    public function delMes(CarbonImmutable $mes): Collection
    {
        return Cache::remember(
            $this->clave($mes),
            now()->addDay(),
            fn () => $this->calcular($mes),
        );
    }

    public function olvidar(CarbonImmutable $mes): void
    {
        Cache::forget($this->clave($mes));
    }

    private function clave(CarbonImmutable $mes): string
    {
        return 'mas-prestados:' . $mes->format('Y-m');
    }

    private function calcular(CarbonImmutable $mes): Collection
    {
        return Libro::query()
            ->withCount(['prestamos' => fn ($q) => $q
                ->whereBetween('retirado_en', [
                    $mes->startOfMonth(),
                    $mes->endOfMonth(),
                ])])
            ->orderByDesc('prestamos_count')
            ->orderBy('id')
            ->limit(10)
            ->get();
    }
}
```

`remember` busca la clave. Si la encuentra, la devuelve. Si no, ejecuta la
función, guarda el resultado con la validez indicada y lo devuelve. Es el
patrón de caché más usado, y el nombre en inglés lo describe bien:
recuerda esto.

Fíjate en que la clave incluye el mes. El ranking de febrero y el de marzo
son entradas distintas, y el de febrero, una vez que febrero termina, no
cambia nunca más.

### Invalidación por tiempo y por evento

Hay dos formas en que un valor en caché deja de valer.

**Por tiempo.** La validez expira, y la siguiente consulta recalcula. Es
simple y es **ciega**: no sabe si el valor cambió. Seis horas de validez
significan hasta seis horas de mentira, aunque el valor haya cambiado un
segundo después de guardarse.

**Por evento.** Cuando ocurre algo que afecta el valor, alguien borra la
entrada. El siguiente acceso recalcula con el dato nuevo.

```php title="app/Listeners/OlvidarMasPrestados.php" numbered
final class OlvidarMasPrestados
{
    public function __construct(
        private readonly MasPrestados $ranking,
    ) {}

    public function handle(PrestamoRealizado $evento): void
    {
        $this->ranking->olvidar(
            CarbonImmutable::parse(
                $evento->prestamo->retirado_en,
            ),
        );
    }
}
```

El evento del capítulo @cap:events-jobs-e-filas ganó un segundo oyente, y
el ranking pasa a estar siempre bien: la caché vale **hasta el próximo
préstamo**, y nunca más allá.

Y la validez de un día sigue ahí, como red de seguridad: si algún camino
cambia préstamos sin disparar el evento —una corrección manual en la base,
un script de importación—, el error dura como máximo un día. El evento como
regla, el tiempo como seguro.

| Estrategia | El valor puede estar mal durante | Costo |
|---|---|---|
| solo tiempo | hasta la validez entera | ningún código extra |
| solo evento | para siempre, si un camino se olvida | un listener por causa |
| evento + tiempo | hasta la validez, solo en el camino olvidado | los dos |

Tabla: La tercera fila es la que usa la Casa Amarela. El número de la
validez pasa a ser una decisión sobre el peor caso, no sobre el caso común.

:::pitfall
La disponibilidad de un ejemplar **no** debe cachearse, y no por falta de
técnica. Cambia con cada préstamo y devolución, decenas de veces por hora,
y el costo de que esté mal es una persona cruzando el barrio.

La pregunta que decide qué cachear tiene dos partes: **cuánto cuesta
calcularlo** y **cuánto cuesta que esté mal**. Los más prestados cuestan
caro de calcular y casi nada si están mal unos minutos. La disponibilidad
cuesta poco de calcular —con el índice correcto— y mucho si está mal.
:::

## Caché de configuración, rutas y vistas

Hay un segundo tipo de caché en Laravel, y no guarda datos: guarda **el
propio framework ya armado**.

```text
$ php artisan config:cache
$ php artisan route:cache
$ php artisan view:cache
```

El primero junta todos los archivos de `config/` en uno solo, con los
valores del `.env` ya resueltos; el capítulo
@cap:configuracao-ambiente-e-artisan mostró lo que eso le hace a `env()`
fuera de `config/`. El segundo compila la tabla de rutas. El tercero
convierte de antemano todas las plantillas Blade en PHP.

Juntos ahorran decenas de milisegundos por petición en producción, y los
tres tienen el mismo costo: **a partir del momento en que corren, cambiar
el archivo no cambia nada**. Una ruta nueva, una configuración nueva, una
vista modificada: nada de eso entra hasta que alguien vuelva a correr el
comando.

Por eso pertenecen al **guion de deploy**, justo después de que llega el
código nuevo, y nunca al entorno de desarrollo. El capítulo
@cap:git-ci-e-deploy pone cada uno en su lugar.

## El log no es `dd()`

`dd()` —*dump and die*— imprime el valor y termina la ejecución. Es la
herramienta de depuración más usada en Laravel y lo peor que puede llegar
a producción: olvidado en un camino raro, interrumpe la petición y le
muestra al usuario el contenido de una variable interna.

```php
dd($lector);
```

La cadena del capítulo @cap:git-ci-e-deploy busca `dd(`, `dump(` y
`var_dump(` en el código y rechaza el commit. Es una regla de una línea que
evita toda una categoría de incidentes.

El log es la herramienta de producción. Graba sin interrumpir, en un lugar
que solo el equipo lee, con un nivel que dice cuánto importa aquello.

## Niveles, canales y el log en el que se puede buscar

Los niveles siguen una escala que viene de los sistemas Unix y que toda
herramienta de log entiende:

| Nivel | Cuándo | Ejemplo en la Casa Amarela |
|---|---|---|
| `debug` | detalle para desarrollo | valores intermedios |
| `info` | pasó algo normal que vale registrar | préstamo realizado |
| `warning` | algo raro que no impidió nada | proveedor lento, reintento |
| `error` | una operación falló | job en `failed_jobs` |
| `critical` | una parte del sistema está caída | base inaccesible |

Tabla: En producción, el nivel mínimo suele ser `info`. Todo lo que es
`debug` se descarta antes de escribirse.

Y el **canal** dice adónde va: archivo diario, salida estándar, un servicio
externo, un canal de Slack para los `critical`. `config/logging.php`
declara los canales, y un canal `stack` puede mandar la misma línea a
varios.

La diferencia que más importa, sin embargo, no es el nivel ni el canal. Es
el formato de la línea.

```php
// texto libre
Log::info("Lector {$lector->id} se llevó el ejemplar {$registro}");

// estructurado
Log::info('prestamo-realizado', [
    'lector' => $lector->id,
    'registro' => $registro,
    'libro' => $libro->id,
]);
```

La primera línea es fácil de leer y difícil de buscar. Para encontrar
todos los préstamos del ejemplar 2117, hace falta una expresión regular
que dependa de la frase exacta, que alguien va a cambiar.

La segunda tiene un mensaje fijo, que funciona como el `tipo` del capítulo
@cap:erros-padronizados, y los datos en campos separados. Con el log en
JSON, la búsqueda se vuelve una consulta:

```php title="config/logging.php" numbered
'diario' => [
    'driver' => 'daily',
    'path' => storage_path('logs/laravel.log'),
    'level' => env('LOG_LEVEL', 'info'),
    'formatter' => JsonFormatter::class,
    'days' => 30,
],
```

```text
$ jq 'select(.context.registro == 2117)' storage/logs/laravel-*.log
```

Y cada línea ya sale con el incidente del capítulo @cap:middleware, porque
`Context` agrega todo lo que tiene a cada línea escrita durante la
petición. Encontrar la excepción de Wellington es un `grep`; encontrar
**todo** lo que pasó en su petición, incluido lo que salió bien antes de
fallar, es el mismo `grep`.

## Lo que nunca entra en el log

El middleware del capítulo @cap:middleware resolvió su propio log. La
regla general es más amplia, y vale escribirla como lista, porque es una
lista que se revisa:

- la contraseña, en cualquier forma, incluso la equivocada, que suele ser
  la correcta con un carácter cambiado;
- tokens, claves de API, la cookie de sesión, el encabezado
  `Authorization`;
- documento, CPF, número de tarjeta;
- el cuerpo entero de la petición o de la respuesta;
- datos de salud, de deudas, de cualquier cosa que la persona no le
  contaría a un desconocido.

La Casa Amarela registra el **id** del lector, nunca el nombre ni el
teléfono. Si alguien necesita saber quién es el lector 47, consulta la
base, que tiene control de acceso. El log lo lee más gente, se guarda por
más tiempo y se copia a más lugares.

:::warning
La excepción es el camino más común por el que un dato sensible entra en
el log sin que nadie escriba `Log::`. Una `QueryException` trae el SQL
**con los valores**:

```text
SQLSTATE[23000]: Duplicate entry '12345678901' for key
'lectores_documento_unique' (SQL: insert into lectores
(nombre, documento, ...) values (Rosângela Pires, 12345678901, ...))
```

El CPF entró en el log por el mensaje de la excepción. El handler se puede
configurar para limpiar esos datos antes de registrar, y vale revisar, de
vez en cuando, con una búsqueda por patrones —once dígitos seguidos, `@`—
qué se está grabando de verdad.
:::

:::note En tu carrera
"Medir antes de optimizar" es un consejo que todo el mundo repite y poca
gente sigue, porque medir parece retrasar el arreglo. La persona ya tiene
una hipótesis, y la hipótesis parece correcta.

Lo que pasa con frecuencia es que la hipótesis está bien **a medias**. La
pantalla está lenta por la base, sí, pero no por la consulta que parecía
pesada, sino por un índice que faltaba en una que parecía inofensiva. Diez
minutos con Telescope abierto ahorran la tarde de optimizar la consulta
equivocada, y dejan un número para mostrar en la reunión siguiente, que
vale más que cualquier "ahora está más rápido".
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Acervo/
    MasPrestados.php               # remember + olvidar
  app/Listeners/
    OlvidarMasPrestados.php        # invalidación por evento
  app/Providers/
    AppServiceProvider.php         # DB::listen en local
  config/logging.php               # JSON, diario, 30 días
  database/migrations/
    ..._indice_libro_condicion_en_ejemplares.php
:::

:::milestone
Fin de la Parte 6. Lo que no necesitaba esperar salió de la petición; lo
que era caro y podía estar un poco atrasado ganó caché con invalidación por
evento; lo que era lento por falta de índice se volvió rápido sin ninguna
caché; y cada línea de log tiene un incidente, campos en los que se puede
buscar y nada que no pueda leerse.

En el cuaderno de Tainá: *"¿quién decidió este número?"*.
:::

:::summary
- Cachear es fácil; lo difícil es decir cuándo el valor deja de ser verdad
  y quién avisa.
- Medir va primero: `DB::listen`, *slow query log*, Telescope. Muchas veces
  la respuesta es un índice, no una caché.
- La caché esconde la lentitud; la primera petición después de la
  expiración paga la cuenta entera.
- `Cache::remember` con una clave que incluye lo que diferencia el valor.
- La invalidación por tiempo es ciega; por evento es precisa y frágil; las
  dos juntas se cubren entre sí.
- Qué cachear se decide por el costo de calcular y el costo de estar mal.
- `config:cache`, `route:cache` y `view:cache` congelan el framework y
  pertenecen al deploy.
- `dd()` no va a producción; un log estructurado tiene mensaje fijo y datos
  en campos.
- Contraseña, token, documento y cuerpo de la petición nunca entran en el
  log, ni por el mensaje de una excepción.
:::

:::checkpoint
Mides una pantalla lenta antes de tocarla, pones caché solo donde el costo
de estar mal es pequeño y con invalidación por evento, mantienes la
disponibilidad siempre fresca, y escribes logs estructurados que un `grep`
por el incidente encuentra, sin un solo dato personal dentro.
:::

:::exercise level=1
Para cada valor, di si vale la pena cachearlo y, si es así, con qué
estrategia de invalidación:

1. La lista de temas del acervo, que cambia dos veces al año.
2. Cuántos ejemplares de un libro están disponibles ahora.
3. El total de préstamos de 2025, para el informe anual.
4. El perfil del lector autenticado, consultado en cada pantalla.

:::answer
1. Sí, por evento (al guardar un tema) y por tiempo largo como seguro. Es
   el caso ideal: cambia rara vez y se lee todo el tiempo.
2. No. Cambia todo el tiempo y estar mal cuesta caro. Con el índice
   correcto, es una consulta de milisegundos.
3. Sí, **sin invalidación**: 2025 terminó. El valor no cambia nunca más,
   salvo por una corrección manual, y entonces quien corrige olvida la
   clave a mano.
4. Probablemente no. Es una consulta por clave primaria, que la base
   responde en menos de un milisegundo; la caché ahorraría casi nada y
   crearía el riesgo de mostrar un teléfono viejo después de que el lector
   lo cambie.

El punto 4 es el más común en código real, y el motivo es que parece
obvio: "se consulta todo el tiempo". La frecuencia no basta. Lo que decide
es el costo de cada consulta.
:::

:::exercise level=2
Reescribe este fragmento como log estructurado, y señala lo que graba que
no debería:

```php
Log::info("Login de {$request->email} con contraseña "
    . "{$request->contrasena} a las " . now()
    . " — resultado: " . ($ok ? 'ok' : 'falló'));
```

:::answer
Graba la **contraseña**. En texto. Incluso las equivocadas, que suelen ser
la correcta con un error de tipeo, y a veces la contraseña de otro servicio
que la persona escribió por error.

Graba también el e-mail, que es un dato personal, aceptable en algunos
logs de seguridad, siempre que sea con plazo corto y acceso restringido. Y
graba `now()`, lo cual es redundante: toda línea de log ya tiene fecha.

```php
Log::info('login', [
    'resultado' => $ok ? 'ok' : 'fallo',
    'usuario' => $usuario?->id,
    'ip' => $request->ip(),
]);
```

El id del usuario, cuando existe, identifica sin exponer. En los intentos
con un e-mail inexistente, `usuario` queda nulo, y la `ip` basta para
investigar un ataque.

Si el equipo de seguridad realmente necesita el e-mail intentado —para
detectar a alguien probando una lista—, va en un **canal separado**, con
retención de pocos días y acceso restringido, y nunca junto con la
contraseña.
:::

:::exercise level=3
El panel de Vera tiene una pantalla "resumen del día": préstamos de hoy,
devoluciones de hoy, atrasados, reservas pendientes. Tarda 2,4 segundos.
Alguien propuso cachearla por cinco minutos.

Describe, en orden, lo que harías antes de aceptar o rechazar la
propuesta, y en qué caso la aceptarías.

:::answer
**Primero, medir.** Abrir la pantalla con Telescope —o con `DB::listen`— y
ver cuántas consultas hay y cuánto tarda cada una. La pantalla tiene cuatro
números; si son cuatro consultas y una tarda 2,3 segundos, el problema es
esa.

**Segundo, mirar la consulta lenta.** Correr el `EXPLAIN`. Los sospechosos
de siempre: un índice que falta —`retirado_en` sin índice para "préstamos
de hoy" es un candidato fuerte—, una función aplicada a la columna en el
`WHERE` (`DATE(retirado_en) = ...` impide usar el índice;
`retirado_en BETWEEN inicio AND fin` no), o un N+1 escondido.

**Tercero, corregir la causa y medir otra vez.** Si la pantalla baja a cien
milisegundos, la propuesta de caché pierde el motivo.

**Cuándo aceptaría la caché.** Si, después de todo, queda una consulta cara
por naturaleza: el número de atrasados agrega la tabla entera de préstamos
abiertos y no hay índice que la salve. Entonces, caché **solo en ese
número**, no en la pantalla entera, y con la pregunta respondida para
Vera: "el número de atrasados puede tener hasta cinco minutos de retraso;
los préstamos y devoluciones de hoy siempre son exactos". Si ella dice que
cinco minutos de retraso en el número de atrasados le estorban el trabajo,
la respuesta es otra: un contador mantenido por los eventos de préstamo y
devolución.

El orden importa porque la caché en la pantalla entera resolvería el
síntoma, y Vera vería el préstamo que acaba de hacer desaparecer del
resumen durante hasta cinco minutos: el defecto de *La hora de la
estrella*, en su propio panel.
:::
