---
source_hash: 33e749a08ae9
title: "Rutas y controllers"
number: 7
slug: rotas-e-controllers
part: p2
kicker: "El índice del Sistema tenía 137 líneas, y cada línea era un nombre de archivo. Nadie leyó nunca ese índice entero."
goal: >-
  Registrar las rutas de la API diseñadas antes, con nombre, restricción y
  búsqueda automática del registro, manteniendo pequeños los controllers y
  sabiendo justificar el formato elegido para cada uno.
---

:::story Ciento treinta y siete
Tainá intentó dibujar el mapa del Sistema para entender lo que faltaba
migrar. Empezó listando las pantallas.

```text
$ ls *.php | wc -l
137
```

—¿Ciento treinta y siete pantallas?

—Ciento treinta y siete archivos —dijo Dedé—. Algunos son pantallas,
algunos son pedazos de pantalla, y unos quince no los llama nadie.

—¿Cómo sabemos cuáles quince?

Dedé se quedó un rato mirando la lista.

—No lo sabemos. Nadie los borra porque nadie está seguro.
:::

## El archivo de rutas es el índice

En el Sistema, el índice de la aplicación es la salida del `ls`. En un
proyecto Laravel, es un archivo que alguien escribió a propósito, y es la
diferencia entre saber lo que existe y adivinar.

El esqueleto viene con `routes/web.php` y `routes/console.php`. El archivo
de la API no viene: se instala cuando lo necesitas.

```text
$ php artisan install:api
```

```text
   INFO  API scaffolding installed. Please add the
   [Laravel\Sanctum\HasApiTokens] trait to your User model.
```

El comando crea `routes/api.php`, registra el archivo en el
`bootstrap/app.php` e instala el paquete de autenticación por token.

## `web.php` y `api.php`: dos mundos

Los dos archivos existen porque atienden a clientes distintos, y la
diferencia no es organizativa: es de comportamiento.

| | `web.php` | `api.php` |
|---|---|---|
| prefijo en la URL | ninguno | `/api` |
| sesión y cookie | sí | no |
| protección CSRF | sí | no tiene sentido |
| quién consume | navegador | aplicación, script, otro sistema |
| el error devuelve | página HTML | JSON |

Tabla: Una ruta en el archivo equivocado no da error. Se comporta de una
forma que nadie explica: una API que exige el token de un formulario, o una
pantalla que pierde el inicio de sesión en cada clic.

:::key
La pregunta que decide el archivo no es "¿esto devuelve JSON?". Es:
**¿quien llama a esto tiene una sesión abierta en un navegador?**

El panel de Vera la tiene. La aplicación del lector no: lleva la credencial
en cada petición, como describió el capítulo @cap:o-que-e-http.
:::

## Las rutas de la Casa Amarela

El diseño del capítulo @cap:o-que-e-uma-api-rest, ahora escrito:

```php title="routes/api.php" numbered
<?php

declare(strict_types=1);

use App\Http\Controllers\DevolucionController;
use App\Http\Controllers\EjemplarController;
use App\Http\Controllers\LibroController;
use App\Http\Controllers\PrestamoController;
use Illuminate\Support\Facades\Route;

Route::apiResource('libros', LibroController::class);

Route::get('libros/{libro}/ejemplares', [
    EjemplarController::class, 'porLibro',
])->name('libros.ejemplares');

Route::post('prestamos', [PrestamoController::class, 'store'])
    ->name('prestamos.store');

Route::post(
    'prestamos/{prestamo}/devolucion',
    DevolucionController::class,
)->name('prestamos.devolucion');
```

```text
$ php artisan route:list --path=api
```

```text
  GET|HEAD   api/libros ................... libros.index
  POST       api/libros ................... libros.store
  GET|HEAD   api/libros/{libro} ........... libros.show
  PUT|PATCH  api/libros/{libro} ........... libros.update
  DELETE     api/libros/{libro} ........... libros.destroy
  GET|HEAD   api/libros/{libro}/ejemplares  libros.ejemplares
  POST       api/prestamos ................ prestamos.store
  POST       api/prestamos/{prestamo}/devolucion
                                           prestamos.devolucion
```

Cuatro líneas de archivo se volvieron ocho rutas, y la tabla de arriba es
el índice que el Sistema nunca tuvo.

`Route::apiResource` registra las cinco operaciones de un recurso de una
vez. Es hermano de `Route::resource`, que registra siete: las dos extra
devuelven formularios HTML, y una API no tiene formularios.

## Parámetros y restricciones

`{libro}` coincide con cualquier cosa que no sea una barra. Eso es
demasiado generoso cuando el parámetro es un número:

```php
Route::get('libros/{libro}', [LibroController::class, 'show'])
    ->whereNumber('libro');
```

Ahora `/api/libros/abc` no coincide con esa ruta, y el `404` ocurre en el
enrutador, antes de que exista una consulta a la base con un texto en
lugar de un identificador.

:::pitfall
El orden de las rutas importa, y el defecto es silencioso.

```php
Route::get('libros/{libro}', [LibroController::class, 'show']);
Route::get('libros/destacados', [LibroController::class, 'destacados']);
```

La segunda ruta nunca corre. El enrutador prueba en el orden en que se
registraron, y `destacados` coincide con `{libro}`: entonces la aplicación
va a buscar un libro cuyo identificador es la palabra `destacados`, y a
devolver `404` para una ruta que existe.

Dos salidas: **la ruta fija antes que la ruta con parámetro**, siempre; o
restringir el parámetro, que resuelve los dos problemas con una línea.
:::

## El parámetro que ya llega convertido en registro

El controller podría recibir el número y buscar el libro:

```php
public function show(int $id)
{
    $libro = Libro::findOrFail($id);
    // ...
}
```

Tres líneas iguales a esas en cada método, en cada controller. Laravel
ofrece otro camino: si el nombre del parámetro de la ruta coincide con el
nombre del parámetro del método, y el tipo es un model, lo busca solo.

```php
public function show(Libro $libro)
{
    return $libro;
}
```

```text
GET /api/libros/12   → el libro 12
GET /api/libros/999  → 404, sin entrar al método
```

:::term Route model binding
El framework lee el tipo del parámetro, busca el registro por la clave
primaria y entrega el objeto listo. Cuando no lo encuentra, devuelve `404`
antes de llamar a tu código.

Es una comodidad con un efecto secundario bueno: el `404` de un registro
inexistente pasa a tratarse en un solo lugar, en lugar de depender de que
cada método se acuerde.
:::

Se puede buscar por otra columna, cuando el identificador público no es el
número:

```php
Route::get('ejemplares/{ejemplar:registro}', ...);
```

Entonces `{ejemplar:registro}` busca por la columna `registro`, que es el
número pegado en la etiqueta y el que escribe Vera.

## El nombre de la ruta: la URL que cambia sin romper nada

Todas las rutas del ejemplo tienen `->name()`, y el `apiResource` genera
los nombres solo. La ganancia aparece cuando alguien necesita armar una
URL:

```php
route('libros.show', ['libro' => 12]);
// http://localhost:8000/api/libros/12
```

En lugar de escribir la ruta a mano en diecisiete lugares. El día en que
`/api/libros` se vuelva `/api/acervo`, los diecisiete siguen funcionando, y
el `route:list` sigue siendo el índice.

El nombre también es lo que permite referenciar la ruta en otros puntos del
framework: redirección, autorización, y la cabecera `Location` de un
`201`.

## Tres formatos de controller, y lo que comunica cada uno

```text
$ php artisan make:controller LibroController --api
```

**El controller de recurso** agrupa las operaciones de un sustantivo. Los
nombres de los métodos son convención —`index`, `store`, `show`, `update`,
`destroy`— y quien abra el archivo ya sabe qué va a encontrar.

```php title="app/Http/Controllers/LibroController.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Libro;

class LibroController extends Controller
{
    public function index()
    {
        return Libro::query()->orderBy('titulo')->paginate(20);
    }

    public function show(Libro $libro)
    {
        return $libro;
    }
}
```

**El controller invocable** tiene un solo método, el `__invoke`, y se
registra por el nombre de la clase. Comunica una cosa: *esta clase hace
una acción, y solo una*.

```php title="app/Http/Controllers/DevolucionController.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Prestamo;
use App\Services\RegistroDeDevolucion;
use Illuminate\Http\Request;

class DevolucionController extends Controller
{
    public function __construct(
        private readonly RegistroDeDevolucion $devoluciones,
    ) {}

    public function __invoke(Request $req, Prestamo $prestamo)
    {
        $this->devoluciones->registrar(
            $prestamo,
            $req->string('condicion', 'bueno')->toString(),
        );

        return response()->noContent();
    }
}
```

**El controller común**, con métodos de nombre libre, es lo que queda: útil
cuando las acciones no forman un recurso ni son una sola.

:::key
La elección entre los tres es un mensaje para quien lea después.

El recurso dice "aquí viven las operaciones de un sustantivo". El invocable
dice "esta es una acción aislada, con nombre propio". El común no dice
nada, y por eso es el que se usa cuando no hay nada que decir.
:::

## El controller no necesita saberlo todo

Fíjate en el `DevolucionController`: recibe el préstamo listo, llama a un
servicio y devuelve `204`. Siete líneas útiles.

Ese es el tamaño correcto. Un controller tiene tres trabajos, y ninguno es
regla de negocio:

1. **traducir la petición** en argumentos;
2. **llamar a quien sabe hacerlo**;
3. **traducir el resultado** en respuesta.

:::pitfall
El síntoma de que la regla se filtró al controller es el constructor:

```php
public function __construct(
    private Calculadora $calc,
    private Inventario $inventario,
    private Notificador $notificador,
    private Auditoria $auditoria,
    private Informe $informe,
    private Cache $cache,
    private Cola $cola,
    private Log $log,
) {}
```

Ocho dependencias no son un problema de inyección. Son el aviso de que ese
controller está orquestando un proceso de negocio, y un proceso de negocio
tiene nombre, tiene su propia prueba y no depende de HTTP para existir.

La corrección no es achicar la lista: es mover el proceso a una clase que el
controller llama con una línea.
:::

Y la lógica **dentro del archivo de rutas** es la misma enfermedad, un piso
más arriba. Una función anónima con quince líneas en `routes/api.php` no
tiene prueba, no tiene nombre e impide el `route:cache`, que rechaza las
rutas con funciones anónimas, porque no hay cómo guardar una función en un
archivo de caché.

:::note En tu carrera
En una entrevista o en una revisión, "controller gordo" es una crítica fácil
de hacer y difícil de justificar. La justificación que funciona es siempre
la misma pregunta: **¿cómo pruebo esto sin levantar una petición?**

Si la regla está en el controller, la respuesta es "no lo pruebo", y ahí la
discusión deja de ser sobre estética y pasa a ser sobre el costo de
verificar si la multa está bien.

Vale también para el caso contrario. Cuando alguien proponga partir un
controller de siete líneas en cuatro clases, la misma pregunta responde: si
ya se puede probar y ya se puede leer, la división está resolviendo un
problema que no existe.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  routes/
    api.php      # las ocho rutas de la API, con nombre
    web.php
    console.php
  app/
    Http/Controllers/
      LibroController.php       # recurso
      EjemplarController.php
      PrestamoController.php
      DevolucionController.php  # invocable
    Services/
      RegistroDeDevolucion.php
:::

:::summary
- `routes/api.php` lo instala `install:api`, recibe el prefijo `/api` y no
  tiene sesión ni CSRF.
- La pregunta que elige el archivo es si quien llama tiene una sesión de
  navegador.
- `apiResource` registra las cinco operaciones de un recurso, con nombres.
- La ruta fija va antes que la ruta con parámetro, o se restringe el
  parámetro.
- El route model binding busca el registro por el tipo del parámetro y
  devuelve `404` antes de entrar al método.
- `{ejemplar:registro}` busca por otra columna cuando el identificador
  público no es el id.
- El nombre de la ruta permite cambiar la URL sin cazar strings por el
  proyecto.
- Recurso, invocable y común le comunican cosas distintas a quien lee.
- El controller traduce, llama y devuelve; ocho dependencias en el
  constructor indican un proceso de negocio en el lugar equivocado.
:::

:::checkpoint
Registras un conjunto de rutas REST con nombres y restricciones, sabes por
qué una ruta fija después de una con parámetro nunca corre, usas el binding
para recibir el registro listo, y justificas el formato de controller que
elegiste.
:::

:::exercise level=1
Di qué está mal en cada bloque y corrígelo:

```php
Route::get('prestamos/{prestamo}', [C::class, 'show']);
Route::get('prestamos/atrasados', [C::class, 'atrasados']);
```

```php
Route::get('lectores/{lector}', function ($id) {
    $lector = Lector::find($id);

    if (!$lector) {
        return response()->json(['error' => 'no existe'], 404);
    }

    return $lector;
});
```

:::answer
**Primer bloque: el orden.** La ruta de atrasados nunca corre: `atrasados`
coincide con `{prestamo}`. Se corrige invirtiéndolas, o restringiendo:

```php
Route::get('prestamos/atrasados', [C::class, 'atrasados']);
Route::get('prestamos/{prestamo}', [C::class, 'show'])
    ->whereNumber('prestamo');
```

Con el `whereNumber`, el orden deja de importar, y esa es la corrección más
segura, porque no depende de que nadie se acuerde de ella al agregar la
siguiente ruta.

**Segundo bloque: tres problemas.**

La función anónima en el archivo de rutas impide el `route:cache` y no hay
cómo probarla por separado.

La búsqueda y el `404` a mano repiten, en cada ruta, lo que el binding hace
solo.

Y el parámetro se llama `{lector}` pero la función recibe `$id`: funciona
por posición y se rompe el día en que alguien agregue otro parámetro.

```php
Route::get('lectores/{lector}', [LectorController::class, 'show'])
    ->whereNumber('lector')
    ->name('lectores.show');
```

```php
public function show(Lector $lector)
{
    return $lector;
}
```
:::

:::exercise level=2
Registra las rutas que faltan del diseño de la Casa Amarela: las
renovaciones de un lector, los préstamos de un lector y la búsqueda en el
acervo.

Ponles nombre a todas, restringe los parámetros numéricos y di en qué
archivo va cada una.

:::answer
```php title="routes/api.php" numbered
Route::get('libros', [LibroController::class, 'index'])
    ->name('libros.index');

Route::post(
    'lectores/{lector}/renovaciones',
    RenovacionController::class,
)->whereNumber('lector')->name('lectores.renovaciones');

Route::get('lectores/{lector}/prestamos', [
    PrestamoController::class, 'porLector',
])->whereNumber('lector')->name('lectores.prestamos');
```

Las tres van en `routes/api.php`: quien consume es la aplicación del
lector, que no tiene sesión de navegador.

La búsqueda **no** recibe una ruta propia. Es la `libros.index` con
parámetros de consulta —`/api/libros?q=machado&tema=literatura`—, y es la
misma decisión del capítulo de REST: un filtro combinable no se vuelve una
dirección.

La renovación es un controller invocable: es una sola acción, tiene nombre
propio y crea un recurso. Y fíjate en que es `POST` aunque sea una
operación que Vera llamaría "actualizar": el sustantivo escondido ahí es la
renovación, y nace cada vez.
:::

:::exercise level=3
Este controller llegó para revisión. Funciona y las pruebas de petición
pasan.

```php
class PrestamoController extends Controller
{
    public function store(Request $request)
    {
        $ejemplar = Ejemplar::find($request->ejemplar_id);
        $lector = Lector::find($request->lector_id);

        if (!$ejemplar || !$lector) {
            return response()->json(['error' => 'inválido'], 404);
        }

        if ($ejemplar->condicion !== 'bueno') {
            return response()->json(['error' => 'no disponible'], 409);
        }

        $abiertos = Prestamo::where('lector_id', $lector->id)
            ->whereNull('devuelto_en')->count();

        $limite = date('n') == 1 ? 5 : 3;

        if ($abiertos >= $limite) {
            return response()->json(['error' => 'límite'], 409);
        }

        $prestamo = Prestamo::create([
            'ejemplar_id' => $ejemplar->id,
            'lector_id' => $lector->id,
            'retirado_en' => now(),
            'devolver_hasta' => now()->addDays(14),
        ]);

        $ejemplar->update(['condicion' => 'prestado']);

        return response()->json($prestamo, 201);
    }
}
```

Señala los cuatro problemas y muestra cómo queda el método después.

:::answer
**Uno: toda la regla de negocio está aquí.** El límite por lector, la
regla de enero, el plazo, el cambio de condición del ejemplar. Nada de eso
depende de HTTP, y todo eso tiene que probarse sin levantar una petición:
hoy no se puede.

**Dos: los números están sueltos.** `14`, `3`, `5` y `'bueno'` son las
mismas reglas que recibieron dirección en `config/biblioteca.php`. Aquí
divergieron del archivo de configuración en el momento en que se
escribieron.

**Tres: no hay transacción.** Entre crear el préstamo y modificar el
ejemplar existe un intervalo. Si la segunda operación falla, queda un
préstamo abierto para un ejemplar que sigue marcado como disponible: la
carrera del capítulo @cap:pdo, de vuelta.

**Cuatro: la validación se hace con `if`.** Un campo ausente se vuelve
`null`, `find` devuelve `null`, y la respuesta es `404` para un pedido que
era `422`. Los dos códigos le dicen cosas distintas a quien consume.

```php title="app/Http/Controllers/PrestamoController.php" numbered
public function store(
    RegistrarPrestamoRequest $request,
    RegistroDePrestamo $prestamos,
) {
    $prestamo = $prestamos->registrar(
        ejemplarId: $request->integer('ejemplar_id'),
        lectorId: $request->integer('lector_id'),
    );

    return response()
        ->json($prestamo, 201)
        ->header('Location', route('prestamos.show', $prestamo));
}
```

El controller volvió a tener tres trabajos. La validación del formato salió
a una clase de petición; la regla salió a un servicio que abre una
transacción, lee la configuración y lanza las excepciones de dominio del
capítulo @cap:excecoes; y apareció el `Location` del `201`, que el original
no tenía.

Vale la pena decir qué **no** es un problema en el código original: no está
mal. Hace lo correcto y lo hace en un lugar donde nadie puede verificarlo
por separado, y esa es la diferencia entre funcionar hoy y seguir
funcionando en marzo.
:::
