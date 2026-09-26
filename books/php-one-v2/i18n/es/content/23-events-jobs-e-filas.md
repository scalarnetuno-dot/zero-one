---
source_hash: 6711707cdf77
title: "Events, jobs y colas"
number: 23
slug: events-jobs-e-filas
part: p6
kicker: "El aviso de devolución se envió 1.400 veces a la misma persona. El job no era idempotente, y el worker se reinició a la mitad."
goal: >-
  Sacar de la petición el trabajo que no necesita ocurrir antes de la
  respuesta, desacoplar con eventos sin esconder el flujo, correr colas con
  un worker que se reinicia en el deploy, y escribir jobs que pueden fallar,
  volver y correr de nuevo sin repetir el efecto.
---

:::story Mil cuatrocientos
El teléfono de la Casa Amarela sonó a las 7:10 de un sábado. Vera no
estaba; el número desviaba al celular de Márcia, que no lo sabía hasta ese
día.

—Habla el hijo de doña Iolanda. El celular de mi mamá no para de sonar. Es
un mensaje de ustedes. Le llegaron —hizo una pausa, contando— mil
trescientos. Mil trescientos y pico. Ahora mismo llegó otro.

Márcia llamó a Dedé. Dedé abrió el portátil en la cocina, en pijama, y
entró al servidor.

```text
$ php artisan queue:failed
No failed jobs found.

$ tail -f storage/logs/laravel.log | grep AvisarDevolucion
... procesando AvisarDevolucionProxima
... procesando AvisarDevolucionProxima
... procesando AvisarDevolucionProxima
```

—No falló ninguno —dijo él al teléfono—. Ese es el problema. Está
funcionando. Todas las veces.

—¡Entonces páralo!

Detuvo el worker. Los mensajes pararon. El conteo final, en el panel del
proveedor, fue 1.412.

El lunes, la investigación tomó veinte minutos. El job enviaba un aviso por
cada préstamo que vencía al día siguiente —trescientos y pico— y solo
marcaba el trabajo como terminado al final, después del último envío. El
viernes en la noche el proveedor se puso lento, el job pasó el tiempo
límite en el envío número 212, y la cola hizo lo que estaba configurada
para hacer: intentó de nuevo. Desde el principio.

—¿Cuántos intentos estaban configurados? —preguntó Márcia.

Dedé abrió el archivo.

—Ninguno. Sin límite.
:::

:::art caption="Ningún job falló. Ese era el problema."
src="nenhum-job-falhou-esse-era-o-problema.png"
Charge editorial minimalista em fundo branco, composição dividida ao meio.
À esquerda, uma senhora idosa em casa, de roupão, segura com as duas mãos
um celular que vibra sem parar, com um balão de notificação empilhado sobre
outro até o teto e o número "1.412". À direita, um desenvolvedor de
pijama, na mesa da cozinha com uma caneca de café, olha o notebook onde
uma seta circular fechada gira em volta da palavra "tentar de novo". No
canto do notebook, um visto verde e a frase "No failed jobs". Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## Lo que no necesita ocurrir antes de la respuesta

El `PrestamoService` del capítulo @cap:services envía el aviso al lector
después de confirmar la transacción. El envío pasa por el proveedor de
mensajes, que responde en trescientos milisegundos en un buen día y en ocho
segundos en un mal día.

En los días malos, Vera se queda ocho segundos mirando la pantalla, con el
lector enfrente, esperando una confirmación que **ya ocurrió**: el préstamo
está grabado desde el primer milisegundo. Lo que falta es un mensaje de
WhatsApp que el lector ni siquiera necesita haber recibido para irse con el
libro.

La pregunta que separa el trabajo: **¿quien está esperando esto necesita
el resultado para continuar?**

| Trabajo | ¿Quien espera lo necesita? | Dónde |
|---|---|---|
| grabar el préstamo | sí, es la operación | en la petición |
| bloquear el ejemplar | sí, si no es otro préstamo | en la petición |
| avisar al lector | no | en la cola |
| actualizar "más prestados" | no | en la cola |
| generar el comprobante en PDF | no, llega después | en la cola |

Tabla: La cola existe porque esperar cuesta caro: el tiempo de quien está
en el mostrador, y el riesgo de que una falla del proveedor tumbe una
operación que ya había salido bien.

## Event y listener: desacoplar sin esconder

Antes de la cola, una separación. El service, hoy, sabe que después de un
préstamo alguien tiene que ser avisado. Mañana, también tiene que
actualizar un contador. Después, registrar para la rendición de cuentas de
la convocatoria. Cada necesidad nueva es una línea más en `realizar()`, y
cada línea es una dependencia más en el constructor.

La alternativa es que el service **anuncie lo que ocurrió** y deje que los
interesados reaccionen:

```php title="app/Prestamos/Eventos/PrestamoRealizado.php" numbered
final class PrestamoRealizado implements ShouldDispatchAfterCommit
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public readonly Prestamo $prestamo,
    ) {}
}
```

```php title="app/Prestamos/PrestamoService.php" numbered
$prestamo = DB::transaction(function () use (/* ... */) {
    // ... las verificaciones y la grabación ...

    PrestamoRealizado::dispatch($prestamo);

    return $prestamo;
});
```

Y quien reacciona:

```php title="app/Listeners/EnviarComprobanteDePrestamo.php" numbered
final class EnviarComprobanteDePrestamo implements ShouldQueue
{
    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function handle(PrestamoRealizado $evento): void
    {
        $p = $evento->prestamo->load('lector', 'ejemplar.libro');

        $this->avisos->enviar(
            $p->lector,
            sprintf(
                'Te llevaste "%s". Devuélvelo antes del %s.',
                $p->ejemplar->libro->titulo,
                $p->devolver_hasta->format('d/m'),
            ),
        );
    }
}
```

Laravel conecta uno con otro por el tipo del parámetro de `handle`: quien
recibe `PrestamoRealizado` escucha `PrestamoRealizado`. El `ShouldQueue` en
el listener manda la ejecución a la cola, y el service no la espera.

:::pitfall
El evento se dispara **dentro** de la transacción. Sin
`ShouldDispatchAfterCommit`, el listener va a la cola en el acto, y el
worker puede tomarlo **antes** de que ocurra el `COMMIT`. Busca el préstamo
por id y no lo encuentra, porque para el resto de la base la fila todavía
no existe.

El defecto es intermitente, depende de la velocidad del worker, y aparece
como `ModelNotFoundException` en un job que "a veces falla". La interfaz
`ShouldDispatchAfterCommit` retiene el disparo hasta que la transacción se
confirma, y lo descarta si se deshace, lo que evita avisar de un préstamo
que no ocurrió.
:::

La ganancia del evento es que el service ya no conoce el aviso. El costo es
que quien lee `realizar()` ya no ve, ahí, todo lo que pasa después de un
préstamo. La última sección del capítulo vuelve a ese costo.

## Job: la unidad de trabajo que puede fallar y volver

No todo trabajo de cola es reacción a un evento. El aviso de "tu libro
vence mañana" no lo dispara nada que haya ocurrido: lo dispara el
calendario. Para eso existe el **job**, una clase que representa un trabajo
por hacer:

```text
$ php artisan make:job AvisarDevolucionProxima
```

```php title="app/Jobs/AvisarDevolucionProxima.php" numbered
final class AvisarDevolucionProxima implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly int $prestamoId,
    ) {}

    public function handle(EnviadorDeAviso $avisos): void
    {
        $p = Prestamo::with('lector', 'ejemplar.libro')
            ->find($this->prestamoId);

        if ($p === null || $p->devuelto()) {
            return;
        }

        $avisos->enviar($p->lector, sprintf(
            '"%s" vence mañana. Renuévalo en la aplicación.',
            $p->ejemplar->libro->titulo,
        ));
    }
}
```

Y lo que dispara los jobs es un comando programado, como el
`biblioteca:multas` del capítulo @cap:configuracao-ambiente-e-artisan:

```php title="routes/console.php" numbered
Schedule::call(function () {
    Prestamo::abiertos()
        ->whereDate('devolver_hasta', today()->addDay())
        ->pluck('id')
        ->each(fn ($id) => AvisarDevolucionProxima::dispatch($id));
})->dailyAt('09:00')->name('avisos-de-devolucion');
```

Compáralo con el job de la historia. Aquel era **un** job que recorría
trescientos préstamos. Este es **un job por préstamo**. La diferencia
parece de estilo y es lo que habría salvado a doña Iolanda: cuando el envío
número 212 falla, solo el job 212 lo intenta de nuevo. Los 211 anteriores
ya terminaron y no vuelven.

:::key
Un job debe ser la **unidad de trabajo más pequeña que tiene sentido
repetir**.

Un job que hace trescientas cosas, al repetirse, rehace las trescientas.
Un job que hace una, al repetirse, rehace una.
:::

Fíjate también en lo que recibe el job: el **id**, no el model. `$p` se
busca dentro de `handle`, en el momento en que el job corre, que puede ser
segundos u horas después del disparo. Si el lector devolvió el libro
mientras tanto, el job lo descubre y no envía nada.

## Driver de cola: `sync`, `database`, `redis`

La cola necesita vivir en algún lugar entre el disparo y la ejecución. El
`.env` elige dónde:

```text
QUEUE_CONNECTION=database
```

**`sync`** no es cola: ejecuta el job en el acto, dentro de la petición. Es
el valor por defecto en desarrollo y en pruebas, y esconde todo problema
que solo existe cuando el job corre en otro proceso.

**`database`** guarda los jobs en una tabla `jobs`. No exige nada más que
el MySQL que el proyecto ya tiene. Aguanta con holgura el volumen de una
biblioteca de barrio: algunos cientos de jobs por día.

**`redis`** guarda los jobs en un servidor Redis, en memoria. Es más rápido
y aguanta volúmenes mucho mayores, y es una pieza más que instalar,
monitorear y mantener.

La Casa Amarela usa `database`. La regla es la del cuaderno de Tainá, del
capítulo @cap:o-que-vamos-construir: preguntar el tamaño antes de elegir la
herramienta.

## Worker, supervisor y el proceso que hay que reiniciar

Alguien tiene que sacar los jobs de la cola y ejecutarlos. Es el
**worker**:

```text
$ php artisan queue:work --tries=3 --max-time=3600
```

Es un proceso PHP que no termina: toma un job, lo ejecuta, toma el
siguiente, para siempre. Y eso cambia algo que el libro entero dio por
sentado hasta aquí.

En la petición web, PHP carga el código, atiende y muere. Cambiar un
archivo y recargar la página basta. El worker **cargó el código cuando
arrancó** y sigue con esa versión en memoria. Un deploy que cambia el
`EnviadorDeAviso` no cambia nada en el worker que está corriendo: sigue
enviando con el código de ayer, hasta que alguien lo reinicie.

```text
$ php artisan queue:restart
```

Ese comando no reinicia nada directamente. Graba una señal en la caché, y
cada worker, al terminar el job actual, revisa la señal y se cierra solo.
Para que **vuelva**, hace falta un supervisor: un programa del sistema
operativo cuya función es mantener procesos vivos:

```ini title="/etc/supervisor/conf.d/casa-amarela.conf" numbered
[program:casa-amarela-worker]
directory=/var/www/casa-amarela
command=php artisan queue:work --tries=3 --max-time=3600
autostart=true
autorestart=true
user=www-data
numprocs=1
stopwaitsecs=120
```

El `--max-time=3600` hace que el worker se cierre solo cada hora, y el
supervisor lo levanta de nuevo. Eso limpia la memoria acumulada y garantiza
que, aunque alguien olvide el `queue:restart`, el código nuevo entra en una
hora como máximo.

:::warning
Deploy sin `queue:restart` es el defecto más común de quien empieza a usar
colas. El sitio muestra la versión nueva, las pruebas pasaron, y los avisos
siguen saliendo con el texto viejo, o fallando, porque el código viejo
busca una columna que la migration de hoy renombró.

El capítulo @cap:git-ci-e-deploy pone el `queue:restart` en el guion de
deploy, en un orden que no es casual.
:::

## Reintento, `backoff` y `failed_jobs`

Un job que lanza una excepción vuelve a la cola y se intenta de nuevo.
Cuántas veces, y con qué intervalo, es una decisión del job:

```php title="app/Jobs/AvisarDevolucionProxima.php" numbered
public int $tries = 3;

public int $timeout = 30;

public function backoff(): array
{
    return [60, 300];
}

public function failed(Throwable $e): void
{
    Log::warning('aviso-de-devolucion-fallo', [
        'prestamo' => $this->prestamoId,
        'error' => $e->getMessage(),
    ]);
}
```

Tres intentos. El segundo un minuto después del primero, el tercero cinco
minutos después del segundo: darle tiempo al proveedor de recuperarse, en
vez de insistir en el mismo segundo. El `timeout` mata el intento que pasa
de treinta segundos.

Después de la tercera falla, el job va a la tabla `failed_jobs`, con la
excepción entera grabada, y se llama a `failed()`. Ese método no reintenta:
es el lugar para registrar, avisar a alguien, o marcar en la base que ese
lector no fue avisado.

```text
$ php artisan queue:failed
+----+-------------------------+----------------------+
| ID | Job                     | Falló en             |
+----+-------------------------+----------------------+
| 41 | AvisarDevolucionProxima | 2026-03-02 09:00:44  |
+----+-------------------------+----------------------+

$ php artisan queue:retry 41
```

El `queue:retry` devuelve el job a la cola, después de corregir el
problema. Es lo que convierte la falla de un job en algo tratable, y no en
un mensaje perdido.

:::pitfall
El job de la historia no tenía `$tries`. Sin él, el worker usa el valor de
la línea de comandos, y si la línea de comandos tampoco lo tiene, el
reintento es **ilimitado**. Un job que siempre falla a la mitad corre para
siempre, y si lo que hace antes de fallar es enviar un mensaje, el mensaje
se envía para siempre.
:::

## El job tiene que ser idempotente

El `$tries = 3` habría limitado el daño a tres mensajes por persona, y tres
mensajes iguales siguen siendo dos de más. El defecto de fondo no es el
número de intentos. Es que **repetir el job repite el efecto**.

:::term Idempotente
Una operación es idempotente cuando ejecutarla dos veces produce el mismo
resultado que ejecutarla una. El `DELETE` del capítulo
@cap:o-que-e-uma-api-rest lo es; enviar un mensaje, por naturaleza, no.
:::

La cola **no garantiza** que un job corra una sola vez. Garantiza que corre
**al menos** una vez. Un worker puede morir después de enviar el mensaje y
antes de avisarle a la cola que terminó, y la cola, sin el aviso, entrega
el job de nuevo. Ninguna configuración elimina eso. Quien tiene que lidiar
con la repetición es el job.

La técnica es registrar el efecto **de modo que el segundo intento
descubra** que ya ocurrió:

```php title="database/migrations/..._create_avisos_enviados.php" numbered
Schema::create('avisos_enviados', function (Blueprint $t) {
    $t->id();
    $t->foreignId('prestamo_id')->constrained();
    $t->string('tipo', 40);
    $t->date('referente_a');
    $t->timestamps();

    $t->unique(['prestamo_id', 'tipo', 'referente_a']);
});
```

```php title="app/Jobs/AvisarDevolucionProxima.php" numbered
public function handle(EnviadorDeAviso $avisos): void
{
    $p = Prestamo::with('lector', 'ejemplar.libro')
        ->find($this->prestamoId);

    if ($p === null || $p->devuelto()) {
        return;
    }

    $registro = AvisoEnviado::firstOrCreate([
        'prestamo_id' => $p->id,
        'tipo' => 'devolucion-proxima',
        'referente_a' => $p->devolver_hasta->toDateString(),
    ]);

    if (!$registro->wasRecentlyCreated) {
        return;
    }

    $avisos->enviar($p->lector, /* ... */);
}
```

El `unique` en la base es la garantía; el `firstOrCreate` es la pregunta.
Si el registro se acaba de crear, este es el primer envío. Si ya existía,
un intento anterior llegó hasta aquí, y este se detiene.

Queda un hueco pequeño: si el worker muere **entre** crear el registro y
enviar, el mensaje no sale, y el intento siguiente encuentra el registro y
desiste. Es el intercambio consciente entre dos defectos: ningún mensaje,
rara vez, o mensajes repetidos. Para un recordatorio de devolución, la
primera falla es tolerable. Para un cobro, quizá no; y ahí el registro gana
un estado —`enviando`, `enviado`— y `failed()` resuelve los que quedaron a
medias.

:::key
La pregunta que todo job tiene que responder antes de ir a producción:
**¿qué pasa si corre dos veces?**

Si la respuesta es "nada grave", está listo. Si es "el lector recibe dos
mensajes" o "la multa se cobra dos veces", no lo está.
:::

## Cuando el evento se vuelve espagueti invisible

Un evento con un listener es claro. El problema empieza cuando los
listeners disparan eventos:

```text
PrestamoRealizado
  → ActualizarContadorDelLibro
      → dispara LibroSeVolvioPopular
          → RecalcularDestacados
              → dispara DestacadosCambiaron
                  → LimpiarCacheDeLaPortada
  → EnviarComprobante
  → RegistrarParaRendicionDeCuentas
```

Ningún archivo muestra ese árbol. Para saber qué pasa después de un
préstamo, hay que buscar los listeners de `PrestamoRealizado`, luego los
listeners de cada evento que ellos disparan, y así sucesivamente. Un
defecto en `LimpiarCacheDeLaPortada` le aparece a quien investiga como "el
préstamo a veces tarda", a tres niveles de distancia de la causa.

Tres reglas mantienen los eventos legibles:

**Un listener no dispara eventos.** Reacciona y termina. Si la reacción
necesita una segunda etapa, la segunda etapa es un job, llamado
explícitamente por el listener.

**Un evento es un hecho del dominio, en pasado.** `PrestamoRealizado`,
`EjemplarDevuelto`. No `EnviarEmail`: eso es una orden, y una orden es un
job.

**La lista de quién escucha cabe en una consulta.** El comando
`php artisan event:list` muestra cada evento y sus listeners. Si su salida
no cabe en una pantalla, es hora de conversar.

:::story El v2
Para saber cómo el Sistema de 2009 mandaba el aviso de devolución, Tainá
buscó el `cron` del servidor viejo. Había una sola línea, y llamaba a
`php /home/casaamarela/public_html/aviso.php`.

El `aviso.php` tenía doce líneas. La décima incluía un archivo.

```php
include 'funciones2_NUEVO_final_v2.php';
```

Tainá se quedó mirando la pantalla.

—Dedé.

—Mm.

—Hay un `v2`.

Él rodó la silla hasta el escritorio de ella y leyó. Después abrió la
carpeta. Estaban ahí, uno al lado del otro: `funciones.php`,
`funciones2.php`, `funciones2_NUEVO_final.php` y
`funciones2_NUEVO_final_v2.php`. El último se había modificado en marzo de
2016 y tenía una sola función, `manda_aviso_email()`, que abría una
conexión SMTP con un servidor que no existía desde 2019.

—Entonces desde 2019 nadie recibe aviso de devolución —dijo Tainá.

—Desde 2019.

—Y nadie se quejó.

—Vera llama —dijo Dedé—. Tiene una lista en su cuaderno. Llama a todo el
mundo la víspera.

—¿Todas las vísperas?

—Hace cinco años.
:::

:::milestone
El trabajo que no cabe en la petición salió de ella. El préstamo responde
sin esperar al proveedor de mensajes; el aviso sale por una cola con un
worker supervisado y reiniciado en el deploy; cada job se intenta tres
veces, espera entre intentos, termina en `failed_jobs` cuando no se puede,
y puede correr dos veces sin mandar dos mensajes.

Vera puede dejar de llamar la víspera.
:::

:::summary
- Va a la cola lo que quien está esperando no necesita para continuar.
- Un evento anuncia un hecho; un listener reacciona; el service no conoce
  a quien reacciona.
- `ShouldDispatchAfterCommit` retiene el evento hasta que la transacción
  se confirma.
- Un job es la unidad de trabajo más pequeña que tiene sentido repetir: uno
  por préstamo, no uno para todos.
- Un job recibe el id y busca el registro al momento de correr.
- `sync` no es cola; `database` basta para volúmenes pequeños; `redis`,
  para grandes.
- El worker guarda el código en memoria: deploy sin `queue:restart` corre
  código viejo. El supervisor lo mantiene vivo.
- `$tries`, `backoff` y `timeout` son decisiones del job; sin `$tries`, el
  reintento puede ser infinito.
- La cola entrega al menos una vez; el job tiene que ser idempotente, con
  el efecto registrado bajo `unique`.
- Un listener no dispara eventos; `event:list` tiene que caber en una
  pantalla.
:::

:::checkpoint
El comprobante de préstamo y el aviso de víspera salen por la cola,
después del `COMMIT`, con un job por préstamo; el worker corre bajo
supervisor y se reinicia en el deploy; y puedes explicar qué le pasa a un
job que falla en el tercer intento, y por qué puede correr dos veces sin
que doña Iolanda lo note.
:::

:::exercise level=1
Di si cada trabajo debe ocurrir en la petición o en la cola, y por qué:

1. Verificar si el lector tiene una multa mayor a cinco reales.
2. Enviar el aviso de que una reserva quedó disponible.
3. Grabar la devolución y liberar el ejemplar.
4. Recalcular la lista de los más prestados del mes.
5. Generar el PDF del informe mensual de rendición de cuentas.

:::answer
1. Petición. Es condición para que la operación ocurra, y tiene que estar
   dentro de la transacción.
2. Cola. El lector que devolvió el libro no necesita esperar a que salga el
   aviso a otra persona.
3. Petición. Es la operación.
4. Cola, disparada por el evento de préstamo o de devolución, o ni eso: el
   capítulo @cap:cache-logs-e-medicao discute si hace falta recalcularla en
   cada evento.
5. Cola. Puede tardar minutos. La petición responde "el informe se está
   generando", y un aviso o un enlace llega cuando esté listo.
:::

:::exercise level=2
Escribe el evento `EjemplarDevuelto` y el listener que avisa al primer
lector de la lista de reservas de ese libro. El listener debe ir a la cola,
tener tres intentos, y ser idempotente.

:::answer
```php title="app/Prestamos/Eventos/EjemplarDevuelto.php" numbered
final class EjemplarDevuelto implements ShouldDispatchAfterCommit
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public readonly Ejemplar $ejemplar,
    ) {}
}
```

```php title="app/Listeners/AvisarReservaDisponible.php" numbered
final class AvisarReservaDisponible implements ShouldQueue
{
    public int $tries = 3;

    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function handle(EjemplarDevuelto $evento): void
    {
        $reserva = Reserva::activas()
            ->where('libro_id', $evento->ejemplar->libro_id)
            ->oldest()
            ->first();

        if ($reserva === null) {
            return;
        }

        $marcada = Reserva::whereKey($reserva->id)
            ->whereNull('avisada_en')
            ->update(['avisada_en' => now()]);

        if ($marcada === 0) {
            return;
        }

        $this->avisos->enviar(
            $reserva->lector,
            'El libro que reservaste está disponible.',
        );
    }
}
```

La idempotencia viene del `update` con `whereNull('avisada_en')`: solo
marca si nadie marcó, y devuelve cuántas filas cambió. Dos ejecuciones
simultáneas no pueden cambiar las dos la misma fila: la base lo garantiza.

Fíjate en que la reserva se busca por el **libro**, no por el ejemplar,
por el mismo motivo que el `renovar()` del capítulo @cap:services.
:::

:::exercise level=3
Después del incidente de doña Iolanda, alguien propuso: "quitemos la cola y
volvamos a enviar los avisos dentro del comando programado, en secuencia,
que así no se repite".

Responde a la propuesta: qué resuelve de verdad, qué empeora, y qué
mostrarías para defender la cola corregida.

:::answer
**Qué resuelve.** La repetición por reintento, sí: sin cola, no hay quien
lo intente de nuevo. Y es más simple de entender: un bucle, de principio a
fin.

**Qué empeora.**

Una falla en el envío número 212 detiene el comando entero. Los lectores
del 213 al 300 no reciben nada, y nadie se entera hasta que alguien se
queja: no hay `failed_jobs`, no hay `queue:retry`.

El comando tarda la suma de todos los envíos. Con el proveedor lento, son
trescientas veces ocho segundos: cuarenta minutos. Si el programador corre
el comando de nuevo antes de que el primero termine, **se repite**, que es
el defecto que la propuesta quería evitar, volviendo por otro camino. Hay
protección para eso (`withoutOverlapping`), y alguien tiene que acordarse
de ponerla.

Y la repetición no la causaba la cola. La causaba un job que hacía
trescientas cosas y no registraba lo que ya había hecho. El mismo bucle,
dentro del comando, reejecutado por una persona tras una falla a la mitad,
reenvía los 211 primeros igual.

**Qué mostraría.** El job nuevo —uno por préstamo, con `$tries`, `backoff`
y el registro `unique`— y tres pruebas: una que corre el job dos veces y
verifica un solo envío; una que simula la falla del proveedor y verifica
la entrada en `failed_jobs`; y una que corre la programación con
trescientos préstamos y verifica trescientos jobs en la cola. La propuesta
resolvía el síntoma; las pruebas muestran que la causa se resolvió.
:::
