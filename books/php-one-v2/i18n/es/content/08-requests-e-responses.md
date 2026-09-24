---
source_hash: 5c6517ab9e0d
title: "Requests y responses"
number: 8
slug: requests-e-responses
part: p2
kicker: "La pasante envió una portada de libro llamada ../prueba.php. El Sistema la guardó, y el servidor la ejecutó."
goal: >-
  Entrar y salir de la aplicación con objetos: leer el dato correcto del
  `Request`, devolver una respuesta con el status y la cabecera correctos,
  y recibir un archivo sin confiar en nada de lo que mandó el cliente.
---

:::story La portada que era un programa
El Sistema dejaba que la bibliotecaria adjuntara la portada del libro.
Dedé le pidió a Tainá que intentara romperlo, antes de decidir cómo hacer
lo mismo en el proyecto nuevo.

Ella creó un archivo de una línea:

```php
<?php echo 'hola, soy una portada';
```

Lo renombró a `../prueba.php`, lo adjuntó como portada y guardó. El
Sistema respondió que la portada se había enviado con éxito.

Después abrió la dirección del sitio con `/prueba.php` al final.

```text
hola, soy una portada
```

—Dedé.

—Dime.

—Acabo de subir un programa al servidor de la biblioteca.

Dedé miró por encima del monitor.

—¿Por el formulario de portada?

—Por el formulario de portada.
:::

## `Request` es un objeto

Dentro de Laravel, no tocas `$_GET`, `$_POST` ni `$_SERVER`. Todo lo que
llegó está en un objeto que el contenedor le entrega a quien declare el
tipo:

```php title="app/Http/Controllers/LibroController.php" numbered
use Illuminate\Http\Request;

public function index(Request $request)
{
    $busqueda = $request->query('q');
    $pagina = $request->integer('pagina', 1);

    return Libro::buscar($busqueda)->paginate(20, page: $pagina);
}
```

La diferencia no es cosmética. El objeto sabe responder preguntas que las
superglobales no saben:

| Método | Responde |
|---|---|
| `input('campo')` | el valor, venga de la URL o del cuerpo |
| `query('campo')` | solo lo que vino en la URL |
| `post('campo')` | solo lo que vino en el cuerpo |
| `header('Accept')` | una cabecera, con su nombre real |
| `bearerToken()` | el token del `Authorization`, ya separado |
| `expectsJson()` | si el cliente quiere JSON de vuelta |
| `file('portada')` | el archivo enviado, como objeto |

Tabla: `input()` es el más usado y el menos preciso; busca en los dos
lugares. Cuando importa de dónde vino el valor, usa `query()` o `post()`.

Y el cuerpo JSON —que en PHP crudo exigía `php://input`— ya está ahí:

```php
$request->input('ejemplar_id');
```

Laravel lee el `Content-Type`, decodifica el JSON y pone todo en el mismo
lugar. La piedra del capítulo @cap:o-que-e-http deja de existir dentro del
framework; sigue existiendo en todo PHP que no usa framework, y por eso
valía la pena conocer el mecanismo.

## El dato correcto, ya en el tipo correcto

```php
$request->string('condicion')->toString();
$request->integer('pagina');
$request->boolean('solo_disponibles');
$request->date('devuelto_en');
$request->enum('estado', EstadoEjemplar::class);
```

Todo lo que llega por HTTP es texto. Estos métodos hacen la conversión en
la frontera, que es donde debe ocurrir, y el `enum()` rechaza un valor que
no es uno de los casos, en lugar de dejar que el string suelto siga viaje.

Y hay un tercer grupo, el único que **filtra**:

```php
$datos = $request->validate([
    'ejemplar_id' => ['required', 'integer'],
    'lector_id' => ['required', 'integer'],
]);
```

`validate()` devuelve **solo los campos declarados**, ya revisados. Si el
pedido no pasa, se detiene ahí y responde `422` con la lista de problemas,
sin entrar en el resto del método.

:::pitfall
La diferencia entre `$request->all()` y el retorno de `validate()` es una
falla de seguridad esperando el día indicado.

```php
Libro::create($request->all());
```

El cliente manda `titulo`, `anio`, y `id`, `creado_en` o cualquier columna
que descubra que existe. Con `all()`, todo eso llega a la base.

Usa el retorno de `validate()`, que solo contiene lo que declaraste. Es la
diferencia entre "lo que mandó el cliente" y "lo que acepto recibir".
:::

## Devolver: array, model o respuesta

La forma más corta ya apareció: devuelve un array o un objeto, y Laravel lo
convierte.

```php
return $libro;                    // 200, JSON del model
return Libro::all();              // 200, JSON de la colección
return ['status' => 'ok'];        // 200, JSON del array
```

Cuando necesitas decidir el status o una cabecera, el camino es explícito:

```php
return response()->json($prestamo, 201)
    ->header('Location', route('prestamos.show', $prestamo));
```

```php
return response()->noContent();   // 204, cuerpo vacío
```

```php
abort(404, 'Ejemplar no encontrado');
```

| Situación | Qué devolver |
|---|---|
| lectura que salió bien | el model o la colección |
| creación | `response()->json($x, 201)` con `Location` |
| modificación sin cuerpo de vuelta | `response()->noContent()` |
| error de estado del sistema | `abort(409, ...)` o la excepción de dominio |

Tabla: La regla del capítulo @cap:o-que-e-uma-api-rest sigue valiendo, y
ahora tiene sintaxis.

:::key
`response()->noContent()` existe porque `return null` desde un método de
controller devuelve `200` con el cuerpo `""`, y un cuerpo vacío con `200`
es una respuesta que el cliente tiene que interpretar.

El `204` dice lo mismo en el lugar donde el cliente ya está mirando: el
número.
:::

## La misma ruta, dos respuestas

El panel de Vera y la aplicación del lector pueden llamar a la misma ruta.
Lo que cambia es lo que cada uno sabe mostrar.

```php
if ($request->expectsJson()) {
    return response()->json(['error' => 'Ejemplar no disponible'], 409);
}

return back()->withErrors(['ejemplar' => 'Ejemplar no disponible']);
```

`expectsJson()` mira la cabecera `Accept` que mandó el cliente. Es la misma
negociación que describió el capítulo de HTTP, ahora con una pregunta en
lugar de leer la cabecera a mano.

En la práctica, vas a escribir ese `if` pocas veces: separar las rutas en
`api.php` y `web.php` ya resuelve la mayor parte. Sirve para el caso en que
la ruta de verdad es una sola.

## Subida de archivos: no confíes en nada de lo que vino

Vuelve a la portada de Tainá. El Sistema hacía el equivalente a esto:

```php
$nombre = $_FILES['portada']['name'];

move_uploaded_file($_FILES['portada']['tmp_name'], 'portadas/' . $nombre);
```

Hay tres decisiones equivocadas en dos líneas, y todas tienen la misma
raíz: **las eligió el cliente**.

**El nombre del archivo vino del cliente.** `../prueba.php` sube un nivel y
sale de la carpeta de portadas.

**La extensión vino del cliente.** Un `.php` guardado dentro de la carpeta
pública es un programa que el servidor ejecuta cuando alguien lo pide.

**El contenido nunca se revisó.** Nada garantizó que el archivo fuera de
verdad una imagen.

La versión de Laravel decide las tres cosas de este lado:

```php title="app/Http/Controllers/PortadaController.php" numbered
public function __invoke(Request $request, Libro $libro)
{
    $request->validate([
        'portada' => ['required', 'image', 'max:2048'],
    ]);

    $ruta = $request->file('portada')->store('portadas', 'public');

    $libro->update(['portada' => $ruta]);

    return response()->json(['portada' => $ruta], 201);
}
```

```text
{"portada":"portadas/kR8mZ2qXv1nB7dLp0sYw.jpg"}
```

`store()` **genera** el nombre, a partir de un valor aleatorio, y elige la
extensión a partir del tipo real del archivo, no de lo que vino escrito.
El nombre original del cliente se descarta.

La regla `image` revisa el contenido, no el nombre. Y `max:2048` es el
tamaño en kilobytes, que es el límite que impide que alguien llene el disco
con una petición.

:::pitfall
Hay un método parecido y peligroso:

```php
$request->file('portada')->storeAs('portadas', $request->file('portada')
    ->getClientOriginalName());
```

`getClientOriginalName()` devuelve exactamente el texto que mandó el
cliente, incluido `../prueba.php`. El nombre del método es honesto:
*client original*. Es un dato del cliente, como cualquier campo de
formulario.

Si de verdad necesitas conservar el nombre original —y a veces lo
necesitas, para mostrarlo—, guárdalo **en una columna**, como texto, y deja
que el nombre en el disco se genere.
:::

Y una cuarta protección, que no está en el código sino en la estructura:
la carpeta de subidas no queda dentro de `public/`. Queda en `storage/`,
fuera del alcance del servidor web, y los archivos se sirven mediante una
ruta o un enlace declarado. Un `.php` que llegue ahí no lo ejecuta nadie,
porque nadie puede pedirlo por la URL.

:::note En tu carrera
La conversación sobre subidas suele terminar en "pero el formulario solo
deja elegir imágenes". Vale la pena saber responder eso sin sonar
arrogante, porque la frase se dice de buena fe.

El formulario es HTML que corre en la máquina de quien está del otro lado.
Se puede modificar en el propio navegador, o simplemente ignorar: la
petición se puede armar con `curl`, sin ningún formulario. Todo lo que pasa
antes de llegar a tu servidor es una sugerencia.

Es la misma idea del capítulo @cap:o-que-e-http, y vale para la validación
del formato, el campo obligatorio y el límite de tamaño: **el cliente
revisa para ser amable; el servidor revisa porque es el único que puede.**
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Http/Controllers/
    LibroController.php
    PortadaController.php     # subida con nombre generado
    DevolucionController.php  # 204 sin cuerpo
    PrestamoController.php    # 201 con Location
  storage/app/public/
    portadas/                 # fuera del alcance directo de la web
:::

:::summary
- Dentro de Laravel, la petición es un objeto; las superglobales no se
  usan.
- `input()` busca en la URL y en el cuerpo; `query()` y `post()` son
  precisos.
- El cuerpo JSON ya viene decodificado, sin `php://input`.
- `string()`, `integer()`, `boolean()`, `date()` y `enum()` convierten en
  la frontera.
- `validate()` devuelve solo los campos declarados; `all()` devuelve lo que
  el cliente quiso mandar.
- El array y el model se vuelven JSON solos; `response()->json()` cuando
  importa el status o la cabecera.
- `noContent()` es el `204`; `return null` es un `200` con cuerpo vacío.
- `expectsJson()` decide el formato cuando la ruta atiende a los dos
  mundos.
- En la subida, el nombre, la extensión y el tipo vienen del cliente:
  genera el nombre, revisa el contenido y guarda fuera de `public/`.
:::

:::checkpoint
Lees datos de la petición con el método correcto para cada origen,
devuelves respuestas con el status y la cabecera correctos, recibes un
archivo sin usar nada de lo que eligió el cliente, y sabes explicar por qué
la validación del formulario no cuenta.
:::

:::exercise level=1
Para cada fragmento, di qué está mal y corrígelo:

```php
$id = $_GET['libro_id'];
```

```php
return null;  // devolución registrada, nada que devolver
```

```php
Libro::create($request->all());
```

:::answer
**Primero.** Una superglobal dentro del framework. Además de saltarse el
objeto `Request`, devuelve texto sin conversión y no se puede sustituir en
las pruebas.

```php
$id = $request->integer('libro_id');
```

**Segundo.** `return null` produce `200` con cuerpo vacío. El cliente
recibe un éxito y un cuerpo que tiene que interpretar.

```php
return response()->noContent();
```

**Tercero.** Asignación masiva de lo que mandó el cliente. Entra cualquier
columna que adivine.

```php
$datos = $request->validate([
    'titulo' => ['required', 'string', 'max:200'],
    'anio' => ['nullable', 'integer'],
]);

Libro::create($datos);
```
:::

:::exercise level=2
Escribe el método `store` del `PrestamoController` para que devuelva `201`
con la cabecera `Location`, y el `__invoke` del `DevolucionController` para
que devuelva `204`.

La devolución acepta un campo opcional `estado`, que tiene que ser uno de
los casos de `EstadoEjemplar`.

:::answer
```php title="app/Http/Controllers/PrestamoController.php" numbered
public function store(
    Request $request,
    RegistroDePrestamo $prestamos,
) {
    $datos = $request->validate([
        'ejemplar_id' => ['required', 'integer'],
        'lector_id' => ['required', 'integer'],
    ]);

    $prestamo = $prestamos->registrar(
        ejemplarId: $datos['ejemplar_id'],
        lectorId: $datos['lector_id'],
    );

    return response()
        ->json($prestamo, 201)
        ->header(
            'Location',
            route('prestamos.show', $prestamo),
        );
}
```

```php title="app/Http/Controllers/DevolucionController.php" numbered
public function __invoke(Request $request, Prestamo $prestamo)
{
    $estado = $request->enum('estado', EstadoEjemplar::class)
        ?? EstadoEjemplar::Bueno;

    $this->devoluciones->registrar($prestamo, $estado);

    return response()->noContent();
}
```

El `enum()` hace tres cosas en una línea: lee el campo, rechaza un valor
que no es uno de los casos y devuelve el objeto del enum, no texto. Cuando
el campo no viene, devuelve `null`, y el `??` pone el predeterminado.

Fíjate en lo que quedó fuera de los dos métodos: la regla. El préstamo
revisa el límite y la disponibilidad dentro del servicio; la devolución
calcula la multa y cambia la condición del ejemplar dentro del suyo. Los
controllers traducen y devuelven.
:::

:::exercise level=3
Un sistema acepta la subida de un comprobante en PDF. El código actual:

```php
$archivo = $request->file('comprobante');
$nombre = $archivo->getClientOriginalName();

if (str_ends_with($nombre, '.pdf')) {
    $archivo->move(public_path('comprobantes'), $nombre);
}
```

Enumera todos los problemas y reescríbelo. Después responde: ¿cuál de
ellos sigue existiendo aunque el nombre se genere y la extensión se
revise?

:::answer
**Los problemas.**

El nombre viene del cliente y no se limpia: `../../public/x.php.pdf` no
termina en nada útil, pero `..%2Fx.pdf` y variaciones de ruta pueden salir
de la carpeta según el sistema de archivos.

La revisión es por el **nombre**, no por el contenido. `virus.php.pdf`
termina en `.pdf` y sigue siendo lo que tiene adentro.

El destino es `public/`, es decir, dentro del alcance del servidor web.

No hay límite de tamaño: un archivo de dos gigabytes se acepta hasta que
se acabe el disco.

No hay tratamiento para el `if` falso: el archivo se descarta en silencio
y el usuario recibe un éxito.

Y `move()` en el directorio público, con un nombre previsible, permite que
un segundo envío sobrescriba el comprobante de otra persona.

**La reescritura.**

```php
$request->validate([
    'comprobante' => ['required', 'file', 'mimes:pdf', 'max:5120'],
]);

$ruta = $request->file('comprobante')
    ->store('comprobantes', 'local');

$pago->update([
    'comprobante' => $ruta,
    'comprobante_nombre' => $request->file('comprobante')
        ->getClientOriginalName(),
]);
```

El nombre original va a una **columna**, para mostrarlo, y no al disco. El
disco recibe un nombre generado, en un disco `local`, que queda fuera de
`public/`.

**Lo que sigue existiendo.** El contenido. `mimes:pdf` revisa el tipo del
archivo, y un PDF puede contener JavaScript, un adjunto incrustado o un
ataque contra el lector de quien lo abra.

Ninguna validación de subida vuelve seguro el archivo: solo garantiza que
es del **tipo** que esperabas. Servir archivos enviados por terceros a
otros usuarios es una decisión de producto, y las mitigaciones son otras:
análisis antivirus, servirlos con `Content-Disposition: attachment` para
que no se abran en el navegador, y servirlos desde un dominio distinto del
de la aplicación.
:::
