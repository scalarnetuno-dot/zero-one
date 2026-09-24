---
source_hash: aa29a4f7cfaa
title: "Service Container e inyección de dependencias"
number: 18
slug: service-container
part: p5
kicker: "Dedé abrió el contenedor de veinte líneas al lado del contenedor de Laravel. La pasante reconoció la reflexión antes de que él la señalara."
goal: >-
  Entender el mecanismo que arma los objetos de la aplicación, declarar las
  dependencias por el constructor, elegir entre bind, singleton y scoped, y
  cambiar una implementación en la prueba sin tocar a quien la usa.
---

:::story La misma línea
Dedé partió la pantalla en dos. A la izquierda, el `mini.php` del capítulo
de las cuarenta líneas. A la derecha, un archivo del propio Laravel, dentro
de `vendor/`, con más de mil quinientas líneas.

—Busca —dijo.

Tainá bajó por la de la derecha un rato. Se detuvo en un método llamado
`build`.

```php
$reflector = new ReflectionClass($concrete);
// ...
$constructor = $reflector->getConstructor();
// ...
$dependencies = $constructor->getParameters();
```

—Es el nuestro.

—Es el nuestro con quince años de gente quejándose.

—¿Qué son las otras mil cuatrocientas líneas?

—Cada queja.

Bajó un poco más.

—Aquí hay un `singleton`.

—El nuestro también tenía. ¿Te acuerdas del `$hechos`?

—Guardaba todo.

—Entonces. El nuestro solo sabía hacer singleton.
:::

## El `new` esparcido por el código es el problema

El `PrestamoController` tiene que avisarle al lector cuando se hace un
préstamo. La primera versión es directa:

```php
public function store(RealizarPrestamoRequest $request)
{
    // ... el préstamo ...

    $enviador = new EnviadorDeWhatsApp(
        new Client(['timeout' => 5]),
        'https://api.proveedor.com.br',
        'clave-fija-en-el-codigo',
    );

    $enviador->enviar($lector->telefono, 'Préstamo hecho.');
}
```

Funciona, y tiene tres problemas que crecen en direcciones distintas.

**El controller sabe demasiado.** Sabe que el aviso es por WhatsApp, qué
biblioteca HTTP usa el enviador, cuál es el timeout, cuál es la URL del
proveedor. Nada de eso es asunto de quien registra un préstamo.

**Cambiarlo cuesta una búsqueda.** Cuando la biblioteca cambie de
proveedor —y va a cambiar, porque el dinero de la convocatoria cubre solo
un año de mensajes—, el `new EnviadorDeWhatsApp` hay que buscarlo y
cambiarlo en todos los lugares donde aparece. Hoy son cuatro.

**Probarlo es imposible.** Toda prueba que pasa por este método manda un
mensaje de verdad al teléfono de alguien. O falla, porque el servidor de
pruebas no tiene internet, y la prueba falla por un motivo que no tiene
nada que ver con lo que quería probar.

El problema no es el `new`. Es **quién** hace el `new`. La clase que usa
el enviador no debería ser la clase que lo arma.

## Pedir en lugar de armar

El cambio es pequeño en el código y grande en el diseño: la clase
**declara lo que necesita**, y alguien de afuera se lo entrega.

```php title="app/Http/Controllers/PrestamoController.php" numbered
public function __construct(
    private readonly EnviadorDeAviso $avisos,
) {}

public function store(RealizarPrestamoRequest $request)
{
    // ... el préstamo ...

    $this->avisos->enviar($lector, 'Préstamo hecho.');
}
```

El controller ya no sabe nada de WhatsApp. Sabe que existe alguien que
envía avisos, y que ese alguien tiene un método `enviar`.

:::term Inyección de dependencias
Entregarle a un objeto las cosas que necesita, en lugar de dejar que las
cree. El nombre es pomposo para una idea que cabe en una frase: **pide en
el constructor, no construyas adentro**.
:::

¿Quién entrega? Alguien tiene que hacer el `new` en algún momento. En un
programa pequeño, es el `index.php`, a mano. En un proyecto Laravel, es el
**Service Container**: el mismo mecanismo que le entregó el
`StoreLibroRequest` al `store` en el capítulo
@cap:validation-e-form-requests, y el `Libro` al `show` en el capítulo
@cap:rotas-e-controllers.

## El contenedor arma el grafo

Cuando Laravel necesita un `PrestamoController`, hace lo que hacía el
contenedor de veinte líneas del capítulo
@cap:um-framework-de-quarenta-linhas:

1. Mira el constructor por reflexión.
2. Ve que pide un `EnviadorDeAviso`.
3. Intenta construir un `EnviadorDeAviso`, mirando el constructor **de
   él**.
4. Repite, bajando, hasta llegar a clases sin dependencias.
5. Arma todo de abajo hacia arriba y lo entrega.

El resultado es un **grafo**: el controller depende del enviador, que
depende del cliente HTTP, que depende de la configuración. Nadie escribe
ese grafo a mano. Cada clase declara solo a su vecino inmediato, y el
contenedor encadena.

:::diagram type="flowchart" caption="Cada clase declara solo al vecino de abajo. El contenedor recorre la cadena entera."
nodes:
  - { id: c, type: process, text: "PrestamoController" }
  - { id: s, type: process, text: "PrestamoService" }
  - { id: e, type: process, text: "EnviadorDeAviso" }
  - { id: h, type: process, text: "cliente HTTP" }
  - { id: r, type: io,      text: "config('avisos')" }
edges:
  - { from: c, to: s }
  - { from: c, to: e }
  - { from: s, to: e }
  - { from: e, to: h }
  - { from: e, to: r }
:::

### Autowiring, y dónde se detiene

Cuando el tipo pedido es una **clase concreta** con dependencias que
también son clases concretas, el contenedor lo resuelve solo. Eso tiene
nombre: *autowiring*. La mayor parte de las clases de un proyecto Laravel
nunca necesita ninguna configuración para inyectarse.

Se detiene en dos lugares, y los dos son los mismos donde se detenía el
contenedor de veinte líneas:

**Tipos primitivos.** Un constructor que pide `string $clave` no se puede
adivinar. ¿Qué string?

**Interfaces.** `EnviadorDeAviso` es una interfaz. El contenedor no sabe
cuál de las implementaciones quieres, ni si existe alguna.

```text
Target [App\Avisos\EnviadorDeAviso] is not instantiable while
building [App\Http\Controllers\PrestamoController].
```

El mensaje es bueno: dice qué intentó construir y para quién. La
respuesta es decirle al contenedor qué hacer.

## `bind`, `singleton` y `scoped`

El contenedor acepta instrucciones: "cuando pidan X, entrega Y". Hay tres
formas, y la diferencia entre ellas es **cuántas veces se crea el objeto**.

```php
$this->app->bind(EnviadorDeAviso::class, EnviadorDeWhatsApp::class);
```

**`bind`** crea un objeto nuevo **cada vez** que alguien lo pide. Dos
clases que piden `EnviadorDeAviso` en la misma petición reciben dos
instancias distintas.

```php
$this->app->singleton(ClienteDelProveedor::class, fn () =>
    new ClienteDelProveedor(
        config('avisos.url'),
        config('avisos.clave'),
    ));
```

**`singleton`** crea **una vez** y entrega la misma instancia para
siempre: para todas las peticiones que atienda ese proceso.

```php
$this->app->scoped(LectorActual::class);
```

**`scoped`** crea una vez **por petición** y la descarta al final.

| | Instancias | Sirve para |
|---|---|---|
| `bind` | una por pedido | objetos baratos, sin estado |
| `singleton` | una por proceso | conexiones, clientes caros de crear |
| `scoped` | una por petición | estado de la petición actual |

Tabla: La elección equivocada entre `singleton` y `scoped` no da error.
Da un comportamiento que solo aparece con dos usuarios al mismo tiempo.

:::pitfall
Un `singleton` que guarda el estado de la petición es el defecto clásico
del contenedor.

```php
$this->app->singleton(LectorActual::class);
```

Con el PHP tradicional, cada petición empieza de cero y el proceso muere
al final: el singleton vive una sola petición, y el defecto no aparece.
Pero los workers de cola del capítulo @cap:events-jobs-e-filas y los
servidores de aplicación que mantienen el proceso vivo **reutilizan el
proceso**. El lector de la primera petición sigue ahí en la segunda.

Rosângela abre la aplicación y ve los préstamos de Wellington. No por una
intrusión: por un `singleton` que debía ser `scoped`.
:::

## Service Provider: donde viven las instrucciones

Las instrucciones al contenedor tienen que quedar en algún lugar que corra
antes de cualquier petición. Ese lugar es el **service provider**, y el
capítulo @cap:o-que-e-o-laravel ya lo presentó de pasada.

```text
$ php artisan make:provider AvisoServiceProvider
```

```php title="app/Providers/AvisoServiceProvider.php" numbered
<?php

declare(strict_types=1);

namespace App\Providers;

use App\Avisos\EnviadorDeAviso;
use App\Avisos\EnviadorDeWhatsApp;
use App\Avisos\ClienteDelProveedor;
use Illuminate\Support\ServiceProvider;

class AvisoServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(
            ClienteDelProveedor::class,
            fn () => new ClienteDelProveedor(
                url: config('avisos.url'),
                clave: config('avisos.clave'),
                timeout: config('avisos.timeout', 5),
            ),
        );

        $this->app->bind(
            EnviadorDeAviso::class,
            EnviadorDeWhatsApp::class,
        );
    }
}
```

Laravel 11 registra el provider nuevo en `bootstrap/providers.php`, y el
`make:provider` ya agrega la línea.

Fíjate adónde fueron a parar los primitivos: la URL, la clave y el timeout
vienen del `config()`, que viene del `.env`: el camino del capítulo
@cap:configuracao-ambiente-e-artisan. El provider es el **único** lugar del
proyecto que sabe cómo armar el cliente del proveedor. Cambiar de
proveedor es cambiar este archivo.

### `register` y `boot`

Un provider tiene dos métodos, y la diferencia entre ellos es de orden.

**`register`** corre primero, en todos los providers, y sirve **solo** para
enseñarle al contenedor. En él, todavía no puedes pedirle nada al
contenedor, porque otros providers pueden no haber registrado lo que
necesitas.

**`boot`** corre después de todos los `register`. En él, el contenedor
está completo, y puedes usarlo: registrar eventos, configurar el
`preventLazyLoading`, conectar observadores.

La regla práctica: si la línea empieza con `$this->app->bind` o
`singleton`, va en el `register`. Si usa algo, va en el `boot`.

## Interfaz en el constructor, implementación en el provider

La ganancia de todo esto está en un cambio de una línea. La interfaz:

```php title="app/Avisos/EnviadorDeAviso.php" numbered
interface EnviadorDeAviso
{
    public function enviar(Lector $lector, string $texto): void;
}
```

Y dos implementaciones. La real conversa con el proveedor. La otra existe
para desarrollo:

```php title="app/Avisos/EnviadorEnLog.php" numbered
final class EnviadorEnLog implements EnviadorDeAviso
{
    public function enviar(Lector $lector, string $texto): void
    {
        Log::info('aviso', [
            'lector' => $lector->id,
            'texto' => $texto,
        ]);
    }
}
```

```php title="app/Providers/AvisoServiceProvider.php" numbered
$this->app->bind(
    EnviadorDeAviso::class,
    $this->app->isProduction()
        ? EnviadorDeWhatsApp::class
        : EnviadorEnLog::class,
);
```

En desarrollo, ningún aviso sale de la computadora de nadie. En
producción, sale. Ningún controller, ningún service y ninguna línea de
regla de negocio sabe la diferencia.

Es la interfaz del capítulo @cap:heranca-interfaces-e-traits cumpliendo lo
que prometió ese capítulo: un contrato que Laravel pide todo el tiempo. El
contenedor es el motivo por el que las interfaces valen tanto en un
proyecto Laravel: sin él, alguien tendría que elegir la implementación a
mano en cada lugar.

:::key
La pregunta que decide si vale la pena crear una interfaz: **¿existe, o va
a existir, una segunda implementación?** Una real y una de prueba cuentan
como dos.

`EnviadorDeAviso` tiene tres: WhatsApp, log y el falso de la prueba. Vale.
`CalculadoraDeMulta` tiene una, y la de prueba sería igual a la real,
porque es pura. No vale: inyecta la clase concreta, y el autowiring lo
resuelve.
:::

## Cambiar la implementación en la prueba

El tercer problema del principio del capítulo era probar. Con el enviador
viniendo del contenedor, la prueba puede poner otro en su lugar:

```php title="tests/Feature/PrestamoTest.php" numbered
test('avisa al lector al prestar', function () {
    $falso = new EnviadorFalso();
    $this->app->instance(EnviadorDeAviso::class, $falso);

    $this->postJson('/api/prestamos', [
        'ejemplar_id' => 2117,
        'lector_id' => 47,
    ])->assertCreated();

    expect($falso->enviados)->toHaveCount(1)
        ->and($falso->enviados[0]['lector'])->toBe(47);
});
```

```php title="tests/Fakes/EnviadorFalso.php" numbered
final class EnviadorFalso implements EnviadorDeAviso
{
    public array $enviados = [];

    public function enviar(Lector $lector, string $texto): void
    {
        $this->enviados[] = [
            'lector' => $lector->id,
            'texto' => $texto,
        ];
    }
}
```

`$this->app->instance()` le dice al contenedor: "a partir de ahora, cuando
pidan `EnviadorDeAviso`, entrega **este objeto de aquí**". El controller
recibe el falso, y la prueba revisa lo que quedó guardado en él.

Ninguna línea del controller cambió para permitir la prueba. Esa es la
diferencia entre código comprobable y código que hay que adaptar para
probarlo, y el capítulo @cap:testes vuelve a ella con más calma.

## Las dos formas de usar mal el contenedor

**El *service locator*.** El contenedor está siempre accesible por la
función `app()`, y eso permite escribir:

```php
public function store(RealizarPrestamoRequest $request)
{
    $avisos = app(EnviadorDeAviso::class);
    // ...
}
```

Funciona, y deshace la mitad de la ganancia. La dependencia desapareció
del constructor, y quien lee la clase ya no sabe qué necesita sin leer
cada método. La prueba todavía puede cambiarla, pero solo si sabe que el
cambio es necesario.

La regla: `app()` en medio del código es un síntoma. Los lugares legítimos
son el provider, y el código de framework que no tiene un constructor bajo
su control.

**Las *facades* sin entender qué son.** `Log::info()`, `Cache::get()`,
`DB::transaction()` parecen llamadas estáticas, y no lo son. Cada *facade*
es una clase pequeña que, en la llamada, le pide al contenedor el objeto
real y le pasa el método.

```php
Log::info('x');
// es, en la práctica,
app('log')->info('x');
```

Son cómodas y son un *service locator* bien vestido: la dependencia no
aparece en el constructor. Laravel lo compensa con métodos de prueba
propios (`Log::spy()`, `Cache::fake()`), y por eso el costo es menor de lo
que parece. Para las dependencias **de tu dominio** —el enviador, el
service de préstamo—, constructor. Para la infraestructura del framework,
la *facade* es aceptable y es el idioma del ecosistema.

:::note En tu carrera
La inyección de dependencias es uno de los temas en los que la distancia
entre el nombre y la idea más estorba. En una entrevista, la pregunta viene
con "IoC", "DI", "inversión de control", y la persona que sabe usarla se
traba con el vocabulario.

La respuesta que funciona en cualquier entrevista es concreta: "la clase
pide en el constructor lo que necesita, y quien la arma decide qué
implementación entregar; en Laravel, quien arma es el contenedor, y yo
registro las elecciones en un provider". Una frase, y muestra que la usas,
no que la memorizaste.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Avisos/
    EnviadorDeAviso.php      # interfaz
    EnviadorDeWhatsApp.php   # producción
    EnviadorEnLog.php        # desarrollo
    ClienteDelProveedor.php
  app/Providers/
    AvisoServiceProvider.php # la única elección, en un lugar
  config/avisos.php
  tests/Fakes/
    EnviadorFalso.php
:::

:::summary
- El problema no es el `new`; es quién lo hace. La clase que usa no
  debería ser la que arma.
- La inyección de dependencias es pedir en el constructor en lugar de
  construir adentro.
- El contenedor lee los constructores por reflexión y arma el grafo
  entero; es el contenedor de veinte líneas con quince años de uso.
- El autowiring resuelve las clases concretas; para las interfaces y los
  primitivos, el contenedor necesita instrucciones.
- `bind` crea siempre; `singleton` crea una vez por proceso; `scoped`, una
  vez por petición.
- Un `singleton` con estado de la petición filtra datos entre usuarios
  cuando se reutiliza el proceso.
- Los providers le enseñan al contenedor en el `register` y usan el
  contenedor en el `boot`.
- La interfaz vale cuando hay, o va a haber, una segunda implementación, y
  la de prueba cuenta.
- `$this->app->instance()` cambia la implementación en la prueba sin tocar
  el código.
- `app()` en medio del código es un *service locator*; las *facades* son
  eso con métodos de prueba.
:::

:::checkpoint
Declaras las dependencias por el constructor, registras en un provider qué
implementación atiende a cada interfaz, eliges entre `bind`, `singleton` y
`scoped` según la vida del estado, y cambias una implementación en la
prueba sin modificar ninguna línea de quien la usa.
:::

:::exercise level=1
Di si cada registro debería ser `bind`, `singleton` o `scoped`:

1. El cliente HTTP del proveedor de mensajes, con conexión reutilizable.
2. Un objeto que guarda el usuario autenticado de la petición.
3. Una calculadora de multas sin estado, barata de crear.
4. El lector de configuración de la biblioteca, cargado de un archivo.

:::answer
1. `singleton`. Crearlo cuesta, y reutilizar la conexión es el objetivo.
2. `scoped`. Es, por definición, estado de la petición actual. Como
   `singleton`, se filtraría entre peticiones en un worker.
3. Ningún registro. Es una clase concreta sin dependencias primitivas, y
   el autowiring la resuelve sola, con el comportamiento de `bind`.
4. `singleton`, **si** el contenido no cambia mientras vive el proceso. Si
   la configuración puede cambiar y el worker no se reinicia, el singleton
   va a servir la versión vieja hasta el deploy siguiente.

El ítem 3 es el punto del ejercicio: la mayor parte de las clases no
necesita registrarse. Un provider con cincuenta `bind` de clases concretas
es configuración que el contenedor ya hacía solo.
:::

:::exercise level=2
Este service funciona y no se puede probar sin mandar correos de verdad.
Reescríbelo con inyección de dependencias y muestra el registro en el
provider.

```php
class RecordatorioDeDevolucion
{
    public function enviarAAtrasados(): int
    {
        $mailer = new SmtpMailer(
            env('SMTP_HOST'), env('SMTP_USER'), env('SMTP_PASS'),
        );

        $atrasados = Prestamo::conAtraso()->with('lector')->get();

        foreach ($atrasados as $p) {
            $mailer->send($p->lector->email, 'Devuelve el libro');
        }

        return $atrasados->count();
    }
}
```

:::answer
```php title="app/Avisos/RecordatorioDeDevolucion.php" numbered
final class RecordatorioDeDevolucion
{
    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function enviarAAtrasados(): int
    {
        $atrasados = Prestamo::conAtraso()
            ->with('lector')
            ->get();

        foreach ($atrasados as $p) {
            $this->avisos->enviar(
                $p->lector,
                'Devuelve el libro',
            );
        }

        return $atrasados->count();
    }
}
```

El registro ya existe: es el `bind` de `EnviadorDeAviso` en el
`AvisoServiceProvider`. El `RecordatorioDeDevolucion` en sí no necesita
ningún registro: es concreto, y el autowiring le entrega el enviador.

Tres correcciones vinieron juntas, y la tercera es de otro capítulo: el
`env()` fuera de `config/`, que devolvería nulo después del
`config:cache`. Desapareció porque el armado del cliente desapareció de
aquí: fue al provider, que lee de `config('avisos')`.

Y el cambio de canal vino gratis: el recordatorio ahora va por el enviador
de la biblioteca, que hoy es WhatsApp, y no por un correo que la mitad de
los lectores no tiene.
:::

:::exercise level=3
En producción, la aplicación empezó a mostrar, rara vez, el nombre de otro
lector en la cabecera de la pantalla de préstamos. No se puede reproducir
en la máquina de nadie. El proyecto tiene, en un provider:

```php
$this->app->singleton(ContextoDelLector::class, function ($app) {
    return new ContextoDelLector(
        $app['request']->user()?->lector,
    );
});
```

Explica por qué el defecto solo aparece en producción, por qué es raro, y
corrígelo. Después di qué otro síntoma produciría el mismo defecto en los
workers de cola.

:::answer
**Por qué solo en producción.** En desarrollo, `php artisan serve` atiende
cada petición en un entorno en el que el estado no sobrevive entre ellas de
forma perceptible para una persona que prueba sola. En producción, si la
aplicación corre con un servidor que mantiene el proceso vivo entre
peticiones, el singleton creado en la primera petición de ese proceso
**sigue ahí**. La petición siguiente, de otra persona, recibe el
`ContextoDelLector` con el lector de la primera.

**Por qué es raro.** Depende de qué proceso atiende qué petición y de quién
llegó primero a cada uno. Con muchos procesos y poca carga, la misma
persona tiende a caer en procesos que ella misma "inauguró".

**La corrección:**

```php
$this->app->scoped(ContextoDelLector::class, function ($app) {
    return new ContextoDelLector(
        $app['request']->user()?->lector,
    );
});
```

El `scoped` se descarta al final de cada petición y de cada job.

**En los workers de cola:** el worker es un proceso que vive horas y
ejecuta miles de jobs. Un singleton con el lector del primer job haría que
el recordatorio de devolución del segundo job se enviara con el nombre —o
al teléfono— del primer lector. El defecto en la pantalla es vergonzoso;
en la cola, es un mensaje para la persona equivocada, con datos de otra.
:::
