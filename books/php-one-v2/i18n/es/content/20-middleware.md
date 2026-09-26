---
source_hash: 09d75611f2f8
title: "Middleware"
number: 20
slug: middleware
part: p5
kicker: "El middleware de log grababa el cuerpo entero de cada petición. Durante tres meses, eso incluyó el campo contraseña."
goal: >-
  Entender la pipeline que envuelve toda ruta, elegir entre middleware
  global, de grupo y de ruta, poner el orden a favor, limitar los intentos,
  y escribir un middleware propio sabiendo lo que no le pertenece.
---

:::story El campo contraseña
Cléber había escrito el middleware en octubre, en un proyecto anterior de
Vertexo, y lo trajo a la Casa Amarela porque "ya estaba probado". Grababa
en el log cada petición que llegaba: método, ruta, tiempo de respuesta y
el cuerpo.

—¿El cuerpo para qué? —preguntó Tainá, leyendo el archivo.

—Para depurar. Cuando el cliente dice que mandó algo, vemos qué mandó.

Tainá abrió el log de homologación y buscó `/auth/login`. La primera
aparición era de tres días antes.

```text
[2026-02-12 09:41:03] local.INFO: peticion
{"metodo":"POST","ruta":"api/auth/login","ms":212,
 "cuerpo":{"email":"vera@casaamarela.org.br",
           "contrasena":"marmelada1994"}}
```

Giró la pantalla hacia Cléber sin decir nada.

—Ah —dijo él—. Pero es homologación.

—Vera usa la misma contraseña para todo —dijo Tainá—. Me lo contó.

Cléber se quedó callado un rato.

—En el otro proyecto está en producción desde octubre.

—¿Con inicio de sesión?

—Con inicio de sesión.
:::

## La cebolla

Toda petición que llega a Laravel atraviesa una secuencia de capas antes
de llegar al controller, y atraviesa las mismas capas en el camino de
vuelta, en orden inverso. El capítulo @cap:um-framework-de-quarenta-linhas
construyó esa secuencia con un `array_reduce` y la llamó cebolla antes de
que tuviera nombre.

```php title="app/Http/Middleware/MideTiempo.php" numbered
final class MideTiempo
{
    public function handle(Request $request, Closure $next): Response
    {
        $inicio = hrtime(true);

        $respuesta = $next($request);

        $ms = (hrtime(true) - $inicio) / 1_000_000;
        $respuesta->headers->set(
            'Server-Timing', "app;dur={$ms}",
        );

        return $respuesta;
    }
}
```

El `$next($request)` es la línea que divide el middleware en dos. Todo lo
anterior ocurre **a la ida**, antes del controller. Todo lo posterior
ocurre **a la vuelta**, con la respuesta lista en la mano.

:::diagram type="flowchart" caption="La petición baja por las capas hasta el controller; la respuesta sube por las mismas capas, en orden inverso."
nodes:
  - { id: req,  type: io,      text: "petición" }
  - { id: m1,   type: process, text: "MideTiempo (ida)" }
  - { id: m2,   type: process, text: "auth:sanctum (ida)" }
  - { id: ctl,  type: process, text: "controller" }
  - { id: m2v,  type: process, text: "auth:sanctum (vuelta)" }
  - { id: m1v,  type: process, text: "MideTiempo (vuelta)" }
  - { id: resp, type: io,      text: "respuesta" }
edges:
  - { from: req, to: m1 }
  - { from: m1, to: m2 }
  - { from: m2, to: ctl }
  - { from: ctl, to: m2v }
  - { from: m2v, to: m1v }
  - { from: m1v, to: resp }
:::

Un middleware también puede **no llamar** al `$next`. En ese caso, la
petición se detiene ahí, y la respuesta que devuelva es la que recibe el
cliente. Así es como el middleware de autenticación rechaza a quien no
tiene token: el controller nunca se ejecuta.

:::term Middleware
Una capa que envuelve la ejecución de una ruta, con acceso a la petición a
la ida y a la respuesta a la vuelta, y con el poder de interrumpir el
camino. Sirve para lo que vale para **muchas rutas al mismo tiempo** y no
le pertenece a ninguna.
:::

## Global, de grupo y de ruta

Laravel 11 configura los middleware en el `bootstrap/app.php`, y existen
tres alcances.

**Global** corre en toda petición, web y API:

```php title="bootstrap/app.php" numbered
->withMiddleware(function (Middleware $middleware) {
    $middleware->append(MideTiempo::class);
})
```

**De grupo** corre en todas las rutas de un grupo. Laravel ya tiene dos:
el `web`, que activa sesión, cookie y CSRF, y el `api`, que no activa nada
de eso, porque la API no tiene sesión:

```php title="bootstrap/app.php" numbered
$middleware->api(prepend: [
    FuerzaJson::class,
    RegistraPeticion::class,
]);
```

**De ruta** corre donde se pida:

```php title="routes/api.php" numbered
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');

Route::middleware('auth:sanctum')->group(function () {
    Route::apiResource('prestamos', PrestamoController::class);
});
```

| Alcance | Costo de un error | Ejemplo |
|---|---|---|
| global | toda petición, incluida `/up` | medir el tiempo |
| grupo | toda la API, o todo el panel | forzar JSON |
| ruta | solo donde se pidió | limitar el inicio de sesión |

Tabla: Cuanto mayor el alcance, más barato tiene que ser el middleware.
Una consulta a la base en un middleware global es una consulta más en cada
petición de toda la aplicación, incluida la verificación de salud que hace
el monitoreo cada diez segundos.

## El orden importa más de lo que parece

En la cebolla, la capa de afuera ve todo lo que hace la de adentro, y la
de adentro no ve nada de lo que hizo la de afuera después. Eso convierte
el orden en comportamiento.

El middleware que mide el tiempo tiene que ser el **más externo**, para
medirlo todo. Si queda adentro del de autenticación, la consulta del token
no entra en la medición, y el número que muestra es optimista.

El middleware que registra la petición tiene que estar **afuera del de
autenticación** para registrar también las peticiones rechazadas con
`401`. Y tiene que estar **adentro** si quiere saber quién es el usuario.
Las dos cosas no caben en un solo lugar, y por eso el registro de
correlación de la sección siguiente hace el trabajo en dos mitades.

:::pitfall
El orden equivocado más caro es la autorización antes de la
autenticación. Un middleware que revisa "¿este usuario es admin?" antes de
que el usuario se haya identificado ve `null`, y lo que hace con `null`
depende de cómo se escribió:

```php
if ($request->user()?->rol !== Rol::Admin) {
    abort(403);
}
```

Ese rechaza a todo el mundo, incluido el admin, y la ruta parece rota. La
versión escrita con prisa hace lo contrario:

```php
if ($request->user() && !$request->user()->esAdmin()) {
    abort(403);
}
```

Ese **deja pasar a quien no está autenticado**, porque el `if` solo
rechaza a un usuario existente que no es admin. Laravel resuelve el orden
entre sus propios middleware con una lista de prioridades; los tuyos, los
resuelves tú.
:::

## `FuerzaJson`: la API que siempre responde JSON

El handler del capítulo @cap:erros-padronizados responde en JSON cuando la
petición **pide** JSON: cuando la cabecera `Accept` dice
`application/json`. Un cliente que se olvida de la cabecera recibe, en un
error de validación, una **redirección** a la página anterior, que es el
comportamiento del panel web.

```php title="app/Http/Middleware/FuerzaJson.php" numbered
final class FuerzaJson
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        return $next($request);
    }
}
```

Tres líneas, y toda ruta de la API pasa a comportarse como API,
independientemente de lo que mandó el cliente. Es el ejemplo ideal de
middleware: vale para un grupo entero, no depende de ninguna regla de
negocio, y no consulta nada.

## `RegistraPeticion`: el incidente que nace al principio

En el capítulo @cap:erros-padronizados, el código de incidente nacía en el
momento del error. Con un middleware, nace al principio de toda petición, y
toda línea de log escrita durante ella lleva el mismo número.

```php title="app/Http/Middleware/RegistraPeticion.php" numbered
final class RegistraPeticion
{
    private const CAMPOS_SENSIBLES = [
        'contrasena', 'contrasena_confirmation', 'token', 'documento',
    ];

    public function handle(Request $request, Closure $next): Response
    {
        $id = $request->header('X-Request-Id')
            ?? (string) Str::ulid();

        Context::add('incidente', $id);

        $respuesta = $next($request);

        $respuesta->headers->set('X-Request-Id', $id);

        return $respuesta;
    }

    public function terminate(
        Request $request,
        Response $respuesta,
    ): void {
        Log::info('peticion', [
            'metodo' => $request->method(),
            'ruta' => $request->path(),
            'status' => $respuesta->getStatusCode(),
            'usuario' => $request->user()?->id,
            'campos' => array_keys(
                $request->except(self::CAMPOS_SENSIBLES),
            ),
        ]);
    }
}
```

Cuatro decisiones en ese archivo, y cada una es una respuesta a la escena
de Cléber.

**El cuerpo no va al log.** Van los **nombres** de los campos, sin los
valores. Para depurar "el cliente dijo que mandó el título", saber que vino
el campo `titulo` alcanza la mayoría de las veces. Para el resto, existen
el incidente y la reproducción.

**Incluso los nombres pasan por una lista de exclusión.** No por seguridad
—el nombre `contrasena` no es un secreto—, sino porque la lista existe para
que la recuerden: es el lugar donde alguien busca cuando agrega un campo
sensible nuevo.

**El registro ocurre en el `terminate`.** Un middleware con un método
`terminate` se llama **después de que la respuesta se envió** al cliente.
El log no atrasa la respuesta de nadie.

**El identificador acepta lo que vino de afuera.** Si la aplicación manda
un `X-Request-Id`, se usa. La aplicación puede entonces mostrar el mismo
número que está en el log del servidor, y, cuando haya un balanceador de
carga delante, puede generar el número antes, y el rastro atraviesa las dos
máquinas.

:::warning
La lista de campos sensibles protege **tu** middleware. No protege el
resto.

El `Log::info('peticion', $request->all())` que alguien escriba en un
controller para investigar un defecto va a grabar la contraseña igual. El
capítulo @cap:cache-logs-e-medicao se ocupa de la regla general —lo que
nunca entra en el log— y de cómo revisar que se esté cumpliendo.
:::

¿Y qué hacer con los tres meses de contraseñas grabadas en el log del otro
proyecto? Borrar el log no alcanza, porque puede haberse copiado a un
servicio de agregación, a un respaldo, a la máquina de quien investigó un
defecto. La respuesta es la misma del capítulo @cap:git-ci-e-deploy sobre
un secreto en Git: **cambiar el secreto**. Toda persona que inició sesión
en el período tiene que redefinir su contraseña.

## Throttle: el límite que te protege de ti mismo

La ruta de inicio de sesión acepta correo y contraseña. Sin límite, acepta
también un programa que prueba diez mil contraseñas por minuto contra el
correo de Vera.

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    RateLimiter::for('login', function (Request $request) {
        return [
            Limit::perMinute(5)->by(
                mb_strtolower((string) $request->input('email'))
                    . '|' . $request->ip(),
            ),
            Limit::perMinute(30)->by($request->ip()),
        ];
    });
}
```

```php
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');
```

Dos límites al mismo tiempo. Cinco intentos por minuto para la misma
combinación de correo y dirección, que frena el ataque dirigido a una
cuenta. Y treinta por minuto por dirección, que frena a quien prueba muchas
cuentas desde un mismo lugar.

Superado el límite, el middleware no llama al `$next` y responde `429 Too
Many Requests`, con la cabecera `Retry-After` diciendo cuántos segundos
esperar, y el handler del capítulo @cap:erros-padronizados ya lo traduce al
formato de la API.

El nombre de la sección es "te protege de ti mismo" porque el límite no
sirve solo contra ataques. La aplicación con un defecto de bucle, que
rehace la misma petición sin parar, es más común que un atacante, y tumba
el servidor igual.

:::pitfall
Limitar solo por dirección IP parece suficiente y tiene un efecto
secundario en la Casa Amarela: las seis computadoras del mostrador y de la
sala de lectura salen a internet por la **misma** dirección. Cinco intentos
por minuto por IP significaría que si Neide se equivoca de contraseña tres
veces, Vera queda bloqueada.

La clave del límite es una decisión de negocio, y hay que revisarla con
quien usa el sistema.
:::

## Lo que no hay que poner ahí dentro

El middleware es tentador porque corre para muchas rutas sin que nadie
tenga que acordarse. Esa misma cualidad lo vuelve invisible, y lo invisible
se olvida cuando da problemas.

**Reglas de negocio.** "Un lector bloqueado no puede hacer nada" parece un
middleware: vale para todas las rutas del lector. Pero es una regla, cambia
con el tiempo, tiene excepciones ("puede devolver, claro"), y tiene que
probarse sin HTTP. Pertenece al service o a la policy del capítulo
@cap:autorizacao.

**Una consulta pesada en un middleware global.** Un middleware que carga
"la configuración de la biblioteca desde la base" en cada petición hace una
consulta más en la verificación de salud, en la carga de cada imagen que
sirve Laravel, en cada `404`.

**Algo que solo necesita una ruta.** Si solo lo necesita el
`POST /prestamos`, es código del `POST /prestamos`.

La regla: el middleware es para lo que vale para **muchas rutas** y es
**independiente de lo que hace la ruta**. Medir el tiempo, forzar JSON,
identificar la petición, limitar la tasa, autenticar. Todo lo que necesita
saber lo que hace la ruta está en el lugar equivocado.

:::note En tu carrera
Muchas de las fallas de seguridad que vas a investigar a lo largo de tu
carrera no van a estar en el código de seguridad. Van a estar en un
middleware de log, en un tratamiento de errores genérico, en una
herramienta de depuración olvidada encendida: código de apoyo, escrito con
prisa, que nadie revisa con la atención que le da a una pantalla de inicio
de sesión.

El hábito que ayuda es preguntar, para todo código que **graba** algo
—log, caché, cola, archivo—: ¿qué se está grabando exactamente, y quién
puede leerlo después? La pregunta tarda diez segundos y le habría ahorrado
a Cléber una conversación difícil.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  bootstrap/app.php                # withMiddleware: api(prepend: ...)
  app/Http/Middleware/
    MideTiempo.php                 # global, el más externo
    FuerzaJson.php                 # grupo api
    RegistraPeticion.php           # incidente en el Context, terminate
  app/Providers/
    AppServiceProvider.php         # RateLimiter::for('login')
  routes/api.php                   # throttle:login
:::

:::summary
- El middleware envuelve la ruta: lo que viene antes del `$next` corre a la
  ida, lo que viene después corre a la vuelta, y no llamar al `$next`
  interrumpe.
- Global, de grupo y de ruta: cuanto mayor el alcance, más barato tiene que
  ser.
- El orden es comportamiento; la autorización antes de la autenticación ve
  `null`.
- `FuerzaJson` hace que la API responda JSON aun sin la cabecera `Accept`.
- El incidente nace al principio de la petición, va al `Context` y vuelve
  en la cabecera `X-Request-Id`.
- El log de peticiones registra nombres de campos, nunca el cuerpo;
  `terminate` registra después de responder.
- Un secreto grabado en un log se resuelve cambiando el secreto.
- `throttle` con `RateLimiter::for` limita por clave; la clave es una
  decisión de negocio.
- Las reglas de negocio, las consultas pesadas y lo que es de una sola ruta
  no pertenecen a un middleware.
:::

:::checkpoint
La API fuerza JSON, identifica cada petición con un número que aparece en
el log y en la respuesta, registra las peticiones sin grabar valores,
limita el inicio de sesión por cuenta y por dirección, y sabes explicar por
qué "lector bloqueado" no es un middleware.
:::

:::exercise level=1
Para cada necesidad, di si es un middleware y, si lo es, de qué alcance:

1. Rechazar las peticiones sin token en las rutas del lector.
2. Rechazar el préstamo a un lector con una multa de más de cinco reales.
3. Agregar la cabecera `X-Request-Id` en toda respuesta de la API.
4. Limitar la búsqueda del acervo a sesenta peticiones por minuto por
   dirección.
5. Convertir el título del libro a mayúsculas antes de guardarlo.

:::answer
1. Middleware de grupo: `auth:sanctum` en el grupo de las rutas del lector.
2. No. Es una regla de negocio, y ya está en el `PrestamoService`.
3. Middleware de grupo, en el `api`. Es el `RegistraPeticion`.
4. Middleware de ruta: `throttle` con un limitador `busqueda`.
5. No. La normalización de la entrada de un campo específico es trabajo
   del `prepareForValidation` del Form Request, y, en cuanto a las
   mayúsculas, es una decisión que Vera probablemente no quiere: el título
   se guarda como está en la portada.

El ítem 5 aparece con frecuencia como un middleware "que limpia la
entrada", y se vuelve el lugar donde se acumula la normalización de todos
los campos de todas las rutas sin que nadie sepa qué ruta depende de qué
limpieza.
:::

:::exercise level=2
Escribe un middleware `ExigeVersionMinima` para las rutas de la
aplicación: si la cabecera `X-App-Version` viene con una versión menor que
la mínima configurada en `config('app.version_minima')`, la respuesta es
`426 Upgrade Required` en el formato de error de la API. Sin la cabecera,
lo deja pasar.

Di en qué alcance debe registrarse.

:::answer
```php title="app/Http/Middleware/ExigeVersionMinima.php" numbered
final class ExigeVersionMinima
{
    public function handle(Request $request, Closure $next): Response
    {
        $version = $request->header('X-App-Version');
        $minima = config('app.version_minima');

        if ($version !== null
            && version_compare($version, $minima, '<')) {
            return response()->json([
                'tipo' => 'version-desactualizada',
                'mensaje' => 'Actualiza la aplicación para '
                    . 'continuar.',
            ], 426);
        }

        return $next($request);
    }
}
```

`version_compare` es la función de PHP que entiende que `1.10` es mayor que
`1.9`: compararlas como texto daría lo contrario.

**Alcance:** grupo, solo en las rutas que usa la aplicación. No global,
porque el panel Blade y `/up` no mandan la cabecera y no tienen versión.

Dejar pasar sin cabecera es deliberado: las versiones más antiguas de la
aplicación no mandaban la cabecera, y rechazarlas impediría justamente a
los lectores que más necesitan un mensaje que les diga que actualicen. Una
decisión mejor, en una segunda etapa, es tratar la ausencia como "versión
anterior a la 1.2".
:::

:::exercise level=3
Una persona del equipo propone un middleware `CargaLector` para el grupo
de rutas de la aplicación: consulta el lector del usuario autenticado, con
los préstamos abiertos y la multa, y lo guarda en el `Request` para que lo
usen los controllers. "Así ningún controller tiene que buscarlo otra vez."

Evalúa la propuesta: lo que resuelve, los tres costos, y una alternativa
que resuelva el mismo problema.

:::answer
**Lo que resuelve.** Una repetición real: varios controllers de la
aplicación necesitan el lector actual, y buscarlo en cada uno es aburrido.

**Costo uno: una consulta en toda ruta del grupo.** El middleware carga
préstamos y multa incluso para `GET /libros`, que no usa nada de eso. Tres
consultas más en cada búsqueda del acervo, la ruta más usada de la
aplicación.

**Costo dos: datos viejos dentro de la transacción.** El `PrestamoService`
tiene que leer los préstamos abiertos **dentro** de la transacción, con
bloqueo. Si pasa a usar lo que cargó antes el middleware, la revisión del
límite vuelve a tener la carrera del capítulo @cap:do-arquivo-ao-banco. Si
no lo usa, el middleware cargó en vano.

**Costo tres: una dependencia invisible.** El controller pasa a depender de
un atributo en el `Request` que alguien puso en otro archivo. Una ruta
nueva en el grupo equivocado recibe `null`, y el error aparece lejos de la
causa.

**Alternativa.** El lector actual es **una** consulta, barata, y solo las
rutas que lo necesitan deberían hacerla. Un método en el model `Usuario`:

```php
$lector = $request->user()->lector;
```

Con la relación, eso es una consulta, solo donde se llama. Lo que cada
ruta necesite de más —préstamos, multa— lo carga con `load`, con la
consulta visible en el propio controller. La repetición que queda es una
línea, y una línea repetida que dice exactamente lo que hace es mejor que
una capa que hace más de lo que parece.
:::
