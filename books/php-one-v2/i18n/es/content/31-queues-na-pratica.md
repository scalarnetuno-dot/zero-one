---
source_hash: e5a77fa80cb2
title: "Queues en la práctica"
number: 31
slug: queues-na-pratica
part: p8
kicker: "El aviso de las nueve llegó a las tres de la tarde. Delante de él, en la misma cola, estaban doscientos mil libros de don Juvenal."
goal: >-
  Medir la cola por el tiempo de espera, separar trabajos en colas con
  prioridad y workers propios, importar por lotes con progreso, encadenar
  pasos que dependen uno del otro, respetar el ritmo del proveedor sin
  gastar intentos, impedir trabajo por duplicado y acertar el par timeout y
  retry_after que causa la mayoría de las repeticiones.
---

:::story El aviso de las nueve
La escuela estatal por fin mandó la planilla de las donaciones —la misma
de doscientas mil filas del volumen 1—, y Tainá convirtió la importación en
jobs: un job por cada mil filas, doscientos jobs, disparados a las 8:50 de
un lunes.

A las 9:00, el programador disparó los trescientos avisos de "tu libro
vence mañana". Entraron en la cola. **Detrás** de los doscientos jobs de
importación.

A las 15:10, llamó don Juvenal.

—Me acaba de llegar un mensaje diciendo que mi libro vence mañana. La
biblioteca cierra a las seis. Estoy en Guarulhos.

Tainá abrió el servidor.

```text
$ php artisan queue:monitor database:default
  database:default ........................... [312] OK
```

—Trescientos doce jobs, y dice OK —dijo ella.

—Dice OK porque el límite por defecto es mil —dijo Dedé—. Trescientos doce
parece poco. Lo que no dice es que cada job de la importación tarda casi
dos minutos, que hay un solo worker, y que el aviso de las nueve está al
final de la cola.

—¿Entonces el problema es la cantidad de workers?

—El problema es que el aviso y la importación están en la misma cola. Uno
es para ahora. El otro es para cuando se pueda.
:::

## La métrica es la espera

El capítulo @cap:events-jobs-e-filas puso la cola en pie: driver
`database`, un worker con supervisor, reintentos, `failed_jobs` y jobs
idempotentes. Todo eso sigue estando bien. Lo que no tuvo que responder es
qué pasa cuando trabajos con **urgencias distintas** comparten el mismo
worker.

Lo primero que hay que cambiar es lo que se mide. El tamaño de la cola
engaña: trescientos jobs de un segundo son cinco minutos; trescientos de
dos minutos son diez horas. Lo que siente el lector es **cuánto tiempo
lleva esperando el job más antiguo**:

```sql
SELECT queue,
       COUNT(*) AS jobs,
       TIMESTAMPDIFF(MINUTE, FROM_UNIXTIME(MIN(available_at)), NOW())
           AS espera_min
FROM jobs
WHERE reserved_at IS NULL
GROUP BY queue;
```

```text
+---------+------+------------+
| queue   | jobs | espera_min |
+---------+------+------------+
| default |  312 |        380 |
+---------+------+------------+
```

Trescientos ochenta minutos. Esa es la frase que habría despertado a
alguien a las 9:30, y no a las 15:10.

El `queue:monitor` también sirve, con el límite correcto y programado:
cuando una cola pasa del `--max`, dispara el evento `QueueBusy`, y quien lo
escucha le avisa al equipo.

```php title="routes/console.php" numbered
Schedule::command('queue:monitor', [
    'database:avisos,database:default', '--max' => 50,
])->everyFiveMinutes();
```

```php title="app/Providers/AppServiceProvider.php" numbered
Event::listen(function (QueueBusy $evento) {
    Log::warning('cola-llena', [
        'cola' => $evento->queue,
        'jobs' => $evento->size,
    ]);
});
```

## Una cola por urgencia

Las colas tienen nombre. Un job elige la suya al dispararse, o en la
propia clase:

```php
ImportarLote::dispatch($filas)->onQueue('importacion');
```

Y la notificación del capítulo @cap:mail-e-notificacoes, que se vuelve un
job por canal, elige la cola de cada canal:

```php title="app/Notifications/DevolucionManana.php" numbered
public function viaQueues(): array
{
    return [
        'mail' => 'avisos',
        CanalWhatsApp::class => 'avisos',
        'database' => 'avisos',
    ];
}
```

El worker lee las colas **en el orden en que se listaron**:

```text
$ php artisan queue:work --queue=avisos,default,importacion
```

En cada job, mira primero `avisos`; solo si está vacía, `default`; solo si
las dos están vacías, `importacion`. Los avisos de las nueve pasan delante
de los doscientos lotes, porque el worker nunca toma un lote mientras haya
un aviso esperando.

:::pitfall
El orden es prioridad estricta. Si `avisos` nunca se vacía —un día de
mucho movimiento, un proveedor lento—, la `importacion` nunca corre. Al
trabajo que no puede pasar hambre, dale un worker propio.
:::

En la Casa Amarela, dos programas en el supervisor:

```ini title="/etc/supervisor/conf.d/casa-amarela.conf" numbered
[program:casa-amarela-urgente]
command=php artisan queue:work --queue=avisos,default
    --tries=3 --max-time=3600
numprocs=2

[program:casa-amarela-pesado]
command=php artisan queue:work database-larga
    --queue=importacion,portadas --tries=2 --timeout=300
    --max-time=3600
numprocs=1
```

(Las líneas de `command` están cortadas para que quepan en la página; en el
archivo, cada una es una sola línea. El `database-larga` se explica más
adelante.)

Dos workers para lo urgente, uno para lo pesado. Lo pesado puede tardar la
tarde entera, y el aviso de las nueve sale a las nueve.

## Importar por lotes, con progreso

Doscientos jobs sueltos no responden a una pregunta que Vera hizo en el
tercer minuto: **¿cuánto va?** Un **lote** —*batch*— agrupa jobs, sigue el
progreso y llama a alguien cuando todo termina.

El lote necesita una tabla, creada una vez:

```text
$ php artisan make:queue-batches-table
$ php artisan migrate
```

Y la importación pasa a armar el lote con el generador `leerCsv` del
capítulo @cap:manipulacao-de-arquivos —que vino del proyecto viejo a
`app/Importacion/funciones.php`, cargado por el `files` de Composer como en
el capítulo @cap:como-organizar-um-projeto-php—, ahora dentro de una
`LazyCollection`:

```php title="app/Importacion/ImportarDonaciones.php" numbered
public function __invoke(string $ruta): Batch
{
    $lectura = fn () => yield from leerCsv($ruta);

    $lotes = LazyCollection::make($lectura)
        ->chunk(1000)
        ->map(fn ($filas) => new ImportarLote(
            $filas->values()->all(),
        ));

    return Bus::batch($lotes->all())
        ->name('donaciones ' . basename($ruta))
        ->onConnection('database-larga')
        ->onQueue('importacion')
        ->allowFailures()
        ->then(fn (Batch $lote) => Log::info('importacion-ok', [
            'lote' => $lote->id,
        ]))
        ->finally(fn (Batch $lote) => Cache::forget('acervo'))
        ->dispatch();
}
```

La lectura sigue siendo de a una fila: la `LazyCollection` le pide al
generador mil filas, crea un job con ellas, y solo entonces pide las mil
siguientes. Pero fíjate en el `$lotes->all()`: `Bus::batch` necesita la
lista de jobs, y cada job lleva sus mil filas. En el momento del disparo,
la planilla entera está en memoria, dividida en doscientos pedazos: los
treinta megabytes del capítulo @cap:manipulacao-de-arquivos, durante unos
segundos. Para nueve megabytes de CSV, es un precio aceptable. Para
noventa, el lote nace vacío y un job de lectura va agregando los lotes de
a poco, con `$lote->add([...])`.

**`allowFailures()`** decide qué pasa cuando un lote falla. Sin él, la
primera falla cancela el resto. Con él, los otros 199 siguen, y el lote que
falló va a `failed_jobs`, donde se puede corregir y reintentar. Para una
importación de donaciones, es el comportamiento correcto: una fila con el
año escrito en letras no debe impedir las otras 199.999.

**`then`** corre cuando todos terminan con éxito; **`finally`**, cuando
todos terminan, con o sin falla. El `Cache::forget('acervo')` es el cuidado
del capítulo @cap:cache-logs-e-medicao: la página del acervo no puede
mostrar la lista de ayer.

:::pitfall
Las closures de `then`, `catch` y `finally` se **guardan en la base** y se
ejecutan después, en otro proceso. No pueden usar `$this`, ni variables
que no sean serializables. Pasa solo valores simples —ids, textos— y busca
el resto dentro de la closure.
:::

El job del lote verifica, antes de trabajar, si alguien canceló el lote:

```php title="app/Jobs/ImportarLote.php" numbered
final class ImportarLote implements ShouldQueue
{
    use Batchable, Queueable;

    public int $timeout = 240;

    public function __construct(public readonly array $filas) {}

    public function handle(Importador $importador): void
    {
        if ($this->batch()?->cancelled()) {
            return;
        }
        $importador->importar($this->filas);
    }
}
```

Y Vera tiene la respuesta a "¿cuánto va?":

```php title="app/Http/Controllers/ImportacionController.php" numbered
public function show(string $id)
{
    $lote = Bus::findBatch($id) ?? abort(404);

    return [
        'nombre' => $lote->name,
        'progreso' => $lote->progress(),
        'pendientes' => $lote->pendingJobs,
        'fallas' => $lote->failedJobs,
        'terminado' => $lote->finished(),
    ];
}
```

```text
{"nombre":"donaciones escuela-estatal.csv","progreso":37,
 "pendientes":126,"fallas":1,"terminado":false}
```

Un detalle que aparece en el último minuto de la importación: el lote que
falló sigue contando como **pendiente**. Con 199 lotes buenos y 1 con
falla, el progreso se detiene en 99, `pendientes` y `fallas` valen 1, el
`finally` ya corrió, y `terminado` solo pasa a `true` cuando alguien
corrige la fila y reintenta el lote. El panel de Vera debe mostrarlo como
"terminó con una falla", y no como "ya casi".

## Encadenar lo que depende

El lote es para trabajos **independientes**, que pueden correr en
cualquier orden. Cuando un paso necesita el anterior, es una **cadena**:

```php
Bus::chain([
    new PrepararPortada($libro->id, $original),
    new OlvidarCacheDelAcervo(),
])->onQueue('portadas')->dispatch();
```

`OlvidarCacheDelAcervo` solo corre si el `PrepararPortada` del capítulo
@cap:upload-de-arquivos termina bien. Si la portada falla, la caché no se
borra en vano, y la cadena se detiene ahí, con el job que falló en
`failed_jobs`.

## El ritmo del proveedor

El proveedor de WhatsApp acepta sesenta mensajes por minuto. Trescientos
avisos disparados a las nueve, con dos workers, salen en cuarenta segundos,
y doscientos cuarenta vuelven con error `429`.

Laravel limita el ritmo con un **limitador con nombre** y un **middleware
de job**:

```php title="app/Providers/AppServiceProvider.php" numbered
RateLimiter::for('whatsapp', fn () => Limit::perMinute(60));
```

```php title="app/Notifications/DevolucionManana.php" numbered
public function middleware(object $lector, string $canal): array
{
    return $canal === CanalWhatsApp::class
        ? [new RateLimited('whatsapp')]
        : [];
}

public function retryUntil(): DateTime
{
    return now()->addHours(3);
}
```

El middleware corre antes del job. Si el límite del minuto ya se usó, no
ejecuta el job: **lo devuelve a la cola** con un retraso, para intentarlo
de nuevo cuando cambie el minuto. El e-mail y el historial, que no tienen
límite, siguen sin esperar.

El `retryUntil` no es un detalle. Cada vez que `RateLimited` devuelve el
job a la cola, Laravel cuenta **un intento**. Con `--tries=3`, un aviso que
esperó tres minutos su turno va a `failed_jobs` sin haber fallado nunca de
verdad. `retryUntil` cambia el límite de intentos por un límite de tiempo:
el aviso puede esperar su turno todas las veces que haga falta, hasta tres
horas después del disparo.

:::key
Un intento es un conteo de **vueltas a la cola**, no de errores. Todo lo
que devuelve el job a propósito —límite de ritmo, bloqueo, dependencia no
disponible— gasta un intento. Para esos jobs, límite por tiempo
(`retryUntil`), no por número.
:::

## No hacerlo dos veces

Tres herramientas para tres situaciones, todas con el mismo espíritu del
job idempotente del capítulo @cap:events-jobs-e-filas:

**Un job que no puede estar dos veces en la cola.** El informe mensual de
la asociación es pesado, y el botón "generar" se pulsa por impaciencia. El
contrato `ShouldBeUnique` impide el segundo disparo mientras el primero no
termine:

```php title="app/Jobs/GenerarInformeMensual.php" numbered
final class GenerarInformeMensual implements
    ShouldQueue,
    ShouldBeUnique
{
    use Queueable;

    public int $uniqueFor = 3600;

    public function __construct(public readonly string $mes) {}

    public function uniqueId(): string
    {
        return $this->mes;
    }
}
```

El de marzo y el de abril pueden estar juntos en la cola; dos de marzo, no.

**Dos jobs que no pueden correr al mismo tiempo sobre lo mismo.**
Recalcular la multa de un lector mientras otro job registra una devolución
suya produce un valor que ninguno de los dos quería. El middleware
`WithoutOverlapping` pone un bloqueo por clave:

```php
public function middleware(): array
{
    return [(new WithoutOverlapping("lector:{$this->lectorId}"))
        ->releaseAfter(30)];
}
```

**Una tarea programada que no puede correr en dos servidores.** Con el
segundo servidor web de la Casa Amarela, los dos programadores disparaban
los avisos de las nueve:

```php
Schedule::call(new DispararAvisosDeDevolucion)
    ->dailyAt('09:00')
    ->onOneServer()
    ->withoutOverlapping();
```

`onOneServer` usa la caché para elegir un servidor por ejecución, y por eso
exige una caché compartida, como `database` o `redis`, y no el `file` de
cada máquina.

## `timeout` y `retry_after`

Este es el par de números responsable de la mayoría de los mensajes
duplicados en producción, y la Casa Amarela ya pagó por él una vez.

`timeout` es cuánto tiempo deja el **worker** correr un job antes de
matarlo. `retry_after` es cuánto tiempo espera la **cola** a un job
reservado antes de concluir que el worker murió y entregárselo a otro.

```php title="config/queue.php" numbered
'database' => [
    'driver' => 'database',
    'table' => 'jobs',
    'queue' => 'default',
    'retry_after' => 90,
],
```

Un `ImportarLote` con `timeout` de 240 segundos, en esa conexión, hace
esto: a los 90 segundos, la cola cree que murió y se lo entrega a un
segundo worker. Los dos importan las mismas mil filas. Nada falló, ningún
log avisó, y el acervo tiene dos *Vidas secas* con el mismo registro, si la
base no tiene la restricción única del capítulo
@cap:migrations-seeders-e-factories.

La regla: **`retry_after` mayor que el mayor `timeout` de los jobs de esa
conexión**, con holgura. Como el `retry_after` es de la **conexión**, y no
de la cola, los jobs largos ganan una conexión propia:

```php title="config/queue.php" numbered
'database-larga' => [
    'driver' => 'database',
    'table' => 'jobs',
    'queue' => 'importacion',
    'retry_after' => 360,
],
```

Es la `database-larga` del supervisor y del lote. La misma tabla, la misma
base, otra paciencia.

:::warning
Un `retry_after` menor que el `timeout` no genera error, aviso ni línea de
log. Genera trabajo por duplicado, de vez en cuando, solo en los jobs más
lentos, que son justamente los que nadie está mirando. Revisa los dos
números cada vez que crees un job que pueda pasar de un minuto.
:::

## El worker es un proceso que envejece

El capítulo @cap:escopo-e-referencias lo advirtió: una variable `static` y
una caché en memoria duran lo que dura el proceso. En la petición web, es
un instante. En el worker, son horas, y cada job deja un poco de memoria
atrás.

Tres opciones de `queue:work` le ponen un límite a la edad del worker, y el
supervisor levanta uno nuevo en su lugar:

| Opción | Cierra el worker después de |
|---|---|
| `--max-jobs=500` | quinientos jobs |
| `--max-time=3600` | una hora |
| `--memory=256` | pasar de 256 MB |

Tabla: El worker que se jubila solo no necesita que nadie lo reinicie de
madrugada.

## Cuando falla en producción

La tabla `failed_jobs` es la bandeja de entrada de la cola. Tres comandos
para atenderla:

```text
$ php artisan queue:failed
$ php artisan queue:retry --queue=avisos
$ php artisan queue:prune-failed --hours=720
```

El primero los lista, con la excepción de cada uno. El segundo devuelve a
la cola todos los que fallaron en la cola `avisos`, después de que el
proveedor vuelva, y no antes. El tercero borra los de más de treinta días,
y vale la pena programarlo: una tabla de fallas con dos años de basura
esconde la falla de hoy.

Con Redis en lugar de `database`, **Horizon** da un panel para todo esto
—colas, espera, fallas, workers— y ajusta solo el número de workers. Para
la Casa Amarela, la consulta de espera y el `queue:monitor` bastan; el día
en que no basten es el día de cambiar de driver.

:::note En tu carrera
La cola es donde los sistemas guardan lo que no quieren ver. El trabajo
sale de la petición, la pantalla se vuelve rápida, y el problema pasa a
ocurrir en un proceso sin pantalla, de madrugada, que nadie abre.

Tres preguntas antes de poner cualquier trabajo en una cola: **¿cuánto
tiempo puede esperar?** Eso elige la cola. **¿Cuánto puede tardar?** Eso
elige el `timeout` y la conexión. **¿Quién se entera si no ocurre?** Eso
elige el `failed()`, el monitor y la alerta. Si la tercera respuesta es
"nadie", todavía no está listo para la cola.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/
    Importacion/ImportarDonaciones.php # lote, generador, progreso
    Jobs/
      ImportarLote.php                 # Batchable, timeout 240
      GenerarInformeMensual.php        # ShouldBeUnique por mes
    Notifications/DevolucionManana.php # cola avisos, ritmo WhatsApp
  config/queue.php                     # database y database-larga
  routes/console.php                   # monitor, onOneServer, prune
:::

:::summary
- Mide la espera del job más antiguo, no el tamaño de la cola.
- Las colas con nombre separan urgencias; `--queue=a,b,c` es prioridad
  estricta. El trabajo que no puede pasar hambre gana un worker propio.
- `Bus::batch` agrupa, muestra el progreso y llama a `then`/`finally`;
  `allowFailures()` no deja que una falla cancele el resto.
- `Bus::chain` corre en orden y se detiene en el primer error.
- `RateLimited` devuelve el job a la cola y gasta un intento: usa
  `retryUntil`.
- `ShouldBeUnique`, `WithoutOverlapping` y `onOneServer` impiden el
  trabajo por duplicado en tres situaciones distintas.
- El `retry_after` de la conexión, mayor que el `timeout` de cualquiera de
  sus jobs.
- `--max-jobs`, `--max-time` y `--memory` jubilan al worker a tiempo.
- `failed_jobs` es una bandeja de entrada: listar, reintentar, podar.
:::

:::checkpoint
Mides una cola por la espera, separas el trabajo urgente del pesado,
importas doscientas mil filas por lotes con progreso, respetas el límite
de un proveedor sin perder avisos, impides el trabajo por duplicado en los
tres lugares donde aparece, y aciertas el par `timeout` y `retry_after`.
:::

:::exercise level=1
¿En qué cola —`avisos`, `default`, `importacion` o `portadas`— pondrías
cada job, y por qué?

1. El comprobante de préstamo, por WhatsApp.
2. La reindexación de la búsqueda del acervo, después de una importación.
3. La miniatura de la portada que Vera acaba de enviar.
4. El e-mail de "tu reserva está disponible".

:::answer
1. `avisos`. El lector está en el mostrador esperando.
2. `importacion`. Puede tardar minutos y puede esperar a la madrugada.
3. `portadas`. Es pesado, y Vera acepta ver la portada en uno o dos
   minutos; no debe competir con los avisos.
4. `avisos`. La reserva tiene plazo, y cada minuto de retraso es un minuto
   menos para que el lector vaya a buscar el libro.
:::

:::exercise level=2
El job `SincronizarConCatalogoNacional` consulta una API externa que a
veces tarda hasta tres minutos en responder. Está en la conexión
`database` por defecto, con `retry_after` de 90 y `timeout` de 200.
Describe qué pasa con una respuesta lenta y escribe la configuración
corregida.

:::answer
A los 90 segundos, la cola da el job por perdido y se lo entrega a otro
worker, mientras el primero todavía espera a la API. Las dos copias
consultan la API y graban el resultado, dos veces, sin ningún error. A los
200 segundos, la primera todavía puede morir por el `timeout` y contar
como una falla.

Corrección: el job va a la conexión larga, con `retry_after` por encima
del `timeout`, y el `timeout` por encima del peor tiempo de la API:

```php
// config/queue.php, en la conexión 'database-larga'
'retry_after' => 360,

// en el job
public int $timeout = 240;

SincronizarConCatalogoNacional::dispatch()
    ->onConnection('database-larga')
    ->onQueue('importacion');
```

Y, como la API es externa, el job tiene que ser idempotente igual: grabar
con "actualiza si existe" por el identificador del catálogo, nunca un
`INSERT` a ciegas.
:::

:::exercise level=3
Diseña la cola de la Casa Amarela para el día en que la asociación abra la
segunda biblioteca, en el barrio de al lado, en el mismo sistema: el doble
de avisos, una importación por semana y portadas enviadas por las dos
bibliotecarias. Di cuántos workers de cada tipo, qué números
monitorearías, con qué límite, y en qué momento cambiarías `database` por
`redis`.

:::answer
Workers:

- **urgente** (`avisos,default`): de dos a tres. Seiscientos avisos a las
  nueve, limitados a sesenta por minuto en WhatsApp, tardan diez minutos
  de todos modos; el tercer worker es para que el e-mail y el historial no
  esperen al WhatsApp.
- **pesado** (`importacion,portadas`, conexión larga): sigue siendo uno.
  La importación semanal puede tardar toda la noche; las portadas son
  pocas.

Monitorearía:

- la espera del job más antiguo en `avisos`: alerta por encima de **5
  minutos**;
- la espera en `importacion`: alerta por encima de **12 horas**; puede
  esperar, pero no para siempre;
- `failed_jobs` nuevos por hora: alerta por encima de **10**;
- la memoria de los workers, desde el supervisor.

Cambiaría a `redis` cuando pase una de estas cosas: que la consulta de
espera se vuelva lenta sobre la tabla `jobs`, que los workers empiecen a
disputarse la misma fila con frecuencia (visible como jobs reservados y
liberados en secuencia), o que el equipo necesite el panel de Horizon para
entender lo que pasa. No antes: dos barrios todavía caben en una tabla.
:::
