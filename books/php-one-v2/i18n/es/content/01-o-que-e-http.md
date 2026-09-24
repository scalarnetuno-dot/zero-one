---
source_hash: bf2645547715
title: "Qué es HTTP"
number: 1
slug: o-que-e-http
part: p1
kicker: "La aplicación enviaba los datos. El servidor recibía los datos. Y el $_POST estaba vacío."
goal: >-
  Leer un intercambio HTTP entero con `curl -v`, saber exactamente qué ve
  PHP de una petición, entender por qué `$_POST` queda vacío con JSON y
  escribir un endpoint crudo que recibe y devuelve JSON sin framework.
---

:::story No manda nada
Tainá había conectado una copia de la aplicación de Kauã al acervo, para
probar. Registraba un préstamo y recibía siempre la misma respuesta:
*"ejemplar no informado"*.

—No manda nada —dijo Tainá—. Mira aquí, el `$_POST` llega vacío.

—¿Vacío cómo?

—Vacío. `array(0)`.

Dedé le pidió que ejecutara el pedido otra vez, pero desde la línea de
comandos, con una opción que deletreó letra por letra.

```text
> POST /prestamos HTTP/1.1
> Content-Type: application/json
> Content-Length: 34
>
{"ejemplar_id":812,"lector_id":47}
```

—Sí está mandando —dijo Tainá.

—Sí.

—Pero el `$_POST`...

—El `$_POST` no es lo que mandó la aplicación. Es lo que PHP decidió
guardar ahí.
:::

## El intercambio entero, en texto

HTTP es texto que va y texto que vuelve. La opción `-v` de `curl` muestra
las dos mitades: las líneas que empiezan con `>` salieron de tu máquina,
las que empiezan con `<` volvieron del servidor.

```text
$ curl -v -X POST http://localhost:8000/prestamos \
       -H "Content-Type: application/json" \
       -d '{"ejemplar_id":812}'
```

```text
> POST /prestamos HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/8.18.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 19
>
< HTTP/1.1 201 Created
< Date: Mon, 21 Sep 2026 20:29:51 GMT
< X-Powered-By: PHP/8.4.2
< Content-Type: application/json
<
```

Las dos mitades tienen la misma forma: una primera línea distinta, una
lista de cabeceras, una línea en blanco y un cuerpo opcional.

A la ida, la primera línea trae verbo, ruta y versión. A la vuelta, trae la
versión, el número y el nombre del status.

:::key
La línea en blanco no es formato: es la frontera. Todo lo anterior son
cabeceras; todo lo posterior es cuerpo.

Por eso cualquier `echo` accidental antes de un `header()` estropea la
respuesta entera: PHP entiende que el cuerpo empezó, y las cabeceras que
vengan después ya no tienen adónde ir.
:::

## Los siete status que vas a usar

```text
< HTTP/1.1 201 Created
```

El número es lo que lee el otro programa; el texto de al lado es una
cortesía para humanos.

| Código | Cuándo | El cuerpo |
|---|---|---|
| `200` | salió bien, aquí está | el recurso |
| `201` | lo creé, y aquí está | el recurso creado |
| `204` | hecho, nada que decir | vacío |
| `400` | el pedido está mal formado | el motivo |
| `401` | no sé quién eres | el motivo |
| `404` | no existe | el motivo |
| `422` | entendí el pedido y es inválido | qué campos |

Tabla: Siete cubren toda la API de este libro. Los demás existen y son
raros.

## Lo que ve PHP

Todo ese texto llega a tu programa ya separado en tres variables que
existen solas, sin que declares nada.

```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

echo json_encode([
    'metodo' => $_SERVER['REQUEST_METHOD'],
    'ruta' => $_SERVER['REQUEST_URI'],
    'tipo' => $_SERVER['CONTENT_TYPE'] ?? '(ausente)',
    'get' => $_GET,
    'post' => $_POST,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
```

Levanta el servidor que viene con PHP y manda un formulario común:

```text
$ php -S localhost:8000 api.php
```

```text
$ curl -X POST http://localhost:8000/prestamos \
       -d "ejemplar_id=812&lector_id=47"
```

```text
{
    "metodo": "POST",
    "ruta": "/prestamos",
    "tipo": "application/x-www-form-urlencoded",
    "get": [],
    "post": {
        "ejemplar_id": "812",
        "lector_id": "47"
    }
}
```

:::term Superglobal
Variable que existe en cualquier lugar del programa sin declararla ni
recibirla: `$_GET`, `$_POST`, `$_SERVER`, `$_FILES`, `$_COOKIE`.

Son la forma más antigua en que PHP entrega la petición, y la más frágil,
porque cualquier línea de cualquier archivo puede leerlas, y escribirlas.
:::

Fíjate en los valores: `"812"`, entre comillas. Todo lo que llega por HTTP
es texto, incluso lo que parece número. La conversión es trabajo tuyo, y su
lugar es la frontera de entrada.

## Por qué el `$_POST` estaba vacío

Ahora el mismo pedido, con JSON:

```text
$ curl -X POST http://localhost:8000/prestamos \
       -H "Content-Type: application/json" \
       -d '{"ejemplar_id":812,"lector_id":47}'
```

```text
{
    "metodo": "POST",
    "ruta": "/prestamos",
    "tipo": "application/json",
    "get": [],
    "post": []
}
```

La aplicación de Kauã estaba bien, y el `$_POST` también.

PHP llena el `$_POST` a partir del cuerpo **solo cuando el `Content-Type`
es uno de los dos formatos de formulario**:
`application/x-www-form-urlencoded`, que es el del ejemplo anterior, y
`multipart/form-data`, que es el del envío de archivos. Con cualquier otro
tipo, no intenta adivinar: deja el cuerpo intacto y el `$_POST` vacío.

El cuerpo sigue ahí, entero, en un lugar con un nombre raro:

```php title="api.php" numbered
$crudo = file_get_contents('php://input');

$datos = json_decode($crudo, true);

echo $datos['ejemplar_id'], "\n";
```

```text
812
```

`php://input` es un flujo de lectura con el cuerpo crudo de la petición,
del primer al último byte, sin ninguna interpretación. `json_decode` con el
segundo argumento `true` devuelve un array asociativo en lugar de un
objeto.

:::pitfall
Este es, de lejos, el primer defecto de quien escribe una API en PHP: la
aplicación manda JSON, el servidor lee `$_POST`, y la respuesta es "campo
obligatorio" para un campo que sí se envió.

El síntoma engaña porque **el error está en el servidor y la sospecha cae
sobre el cliente**. Antes de acusar a quien manda, ejecuta `curl -v`: si la
línea `Content-Type` y el cuerpo están ahí, el problema es de quien lee.
:::

## Cabeceras que cambian el comportamiento

La mayoría de las cabeceras son información. Tres deciden lo que pasa.

**`Content-Type`** dice en qué formato **está escrito** el cuerpo. Es la
que acaba de decidir si el `$_POST` se llenaría.

**`Accept`** dice qué **acepta recibir** el cliente. Un cliente que manda
`Accept: application/json` está diciendo que no quiere tu página de error
en HTML, y devolver HTML de todas formas es lo que hace que una aplicación
muestre una pantalla en blanco en lugar del mensaje.

**`Authorization`** lleva la credencial. Sale así, y el `$_SERVER` traduce
el nombre cambiando el guion por un guion bajo y agregando el prefijo
`HTTP_`:

```text
> Authorization: Bearer abc123
```

```php
$_SERVER['HTTP_AUTHORIZATION']
```

En la respuesta, quien escribe las cabeceras es la función `header()`, y el
status es `http_response_code()`:

```php
header('Content-Type: application/json');
http_response_code(201);
```

## El servidor no se acuerda de ti

HTTP es **sin estado**: cada petición llega sola, sin ningún recuerdo de la
anterior. El servidor no sabe quién eres, qué acabas de hacer ni que existe
una pantalla abierta del otro lado.

Es el mismo modelo que el capítulo @cap:o-php-que-voce-ouviu-falar
describió por dentro —cada petición empieza de cero y muere al final—,
ahora visto desde fuera, en el protocolo.

La consecuencia práctica: **todo lo que el servidor necesita recordar tiene
que venir junto con el pedido, o estar guardado en algún lugar fuera de
él.** El navegador lo resuelve reenviando una cookie en cada petición; PHP
usa esa cookie para reencontrar un archivo de sesión en el disco del
servidor. Una API suele resolverlo de otra forma, mandando la credencial en
`Authorization` en cada llamada.

Las dos son la misma idea: la petición lleva la identidad, porque la
conexión no lleva nada.

## Un endpoint crudo

Junta todo. Sin framework, sin biblioteca, sesenta líneas de nada:

```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Usa POST']);
    exit;
}

$tipo = $_SERVER['CONTENT_TYPE'] ?? '';

if (!str_starts_with($tipo, 'application/json')) {
    http_response_code(415);
    echo json_encode(['error' => 'Envía application/json']);
    exit;
}

$datos = json_decode(file_get_contents('php://input'), true);

if (!is_array($datos)) {
    http_response_code(400);
    echo json_encode(['error' => 'JSON inválido']);
    exit;
}

$faltan = [];

foreach (['ejemplar_id', 'lector_id'] as $campo) {
    if (!isset($datos[$campo])) {
        $faltan[] = $campo;
    }
}

if ($faltan !== []) {
    http_response_code(422);
    echo json_encode([
        'error' => 'Campos obligatorios',
        'campos' => $faltan,
    ]);
    exit;
}

http_response_code(201);

echo json_encode([
    'id' => 4471,
    'ejemplar_id' => (int) $datos['ejemplar_id'],
    'lector_id' => (int) $datos['lector_id'],
]);
```

:::http title="El intercambio que atiende ese archivo"
POST /prestamos
Content-Type: application/json

{"ejemplar_id": 812, "lector_id": 47}
---
201 Created
Content-Type: application/json

{
  "id": 4471,
  "ejemplar_id": 812,
  "lector_id": 47
}
:::

Dos cosas para notar antes de seguir.

La primera: el `405` y el `415` existen porque el archivo responde a **una**
ruta y **un** verbo. Un programa que atiende varias tiene que decidir qué
código corre, y esa decisión tiene nombre: es lo único que falta aquí para
que esto se vuelva un sistema.

La segunda: los `(int)` en la respuesta. Lo que llegó era texto; lo que
sale es número. La frontera convierte, y por eso es el único lugar del
programa que necesita saber que HTTP existe.

:::note En tu carrera
"El cliente no está mandando" y "el servidor no está recibiendo" son la
misma discusión vista desde dos lados, y consume tardes enteras porque cada
lado mira solo su propio log.

Lo que la cierra en dos minutos es un intercambio de `curl -v`: quien acusa
pega la salida entera, con la línea de la petición, las cabeceras y el
cuerpo. A partir de ahí ya no hay opinión: o el `Content-Length` es cero, o
no lo es.

Aprende a leer esa salida antes de necesitarla en una reunión con el equipo
de la aplicación. Es la diferencia entre participar de la conversación y
esperar la conclusión.
:::

:::summary
- La petición y la respuesta son texto con la misma forma: primera línea,
  cabeceras, línea en blanco, cuerpo.
- La línea en blanco es la frontera; un `echo` antes de `header()` la
  adelanta y estropea la respuesta.
- Siete status cubren toda la API: `200`, `201`, `204`, `400`, `401`,
  `404` y `422`.
- `$_GET`, `$_POST` y `$_SERVER` son superglobales, y todo lo que llega por
  ellas es texto.
- El `$_POST` solo se llena con `x-www-form-urlencoded` y
  `multipart/form-data`; con JSON, el cuerpo está en `php://input`.
- `Content-Type` dice cómo está escrito el cuerpo; `Accept`, qué acepta
  recibir el cliente; `Authorization` lleva la credencial.
- HTTP es sin estado: la identidad viaja en cada petición, porque la
  conexión no guarda nada.
- `header()` escribe una cabecera y `http_response_code()` define el
  status.
:::

:::checkpoint
Lees un intercambio entero en `curl -v` y explicas cada línea, sabes decir
sin probar si un `$_POST` va a llegar lleno, lees el cuerpo crudo de una
petición JSON y escribes un endpoint que devuelve el status correcto para
un pedido mal formado, un campo faltante y el éxito.
:::

:::exercise level=1
Para cada situación, di qué status debe tener la respuesta:

1. El préstamo se registró con éxito.
2. El lector 913 no existe en el registro.
3. El cuerpo llegó con `lector_id` pero sin `ejemplar_id`.
4. El cliente mandó el cuerpo en XML.
5. La devolución se registró y no hay nada que devolver en el cuerpo.

:::answer
1. `201`: creó un recurso nuevo.
2. `404`: el recurso pedido no existe.
3. `422`: el pedido está bien formado y el contenido es inválido. No es
   `400`: el JSON era correcto, lo que no se cumplió fue la regla.
4. `415`: el formato del cuerpo no se acepta. Tampoco es `400`, y la
   diferencia importa para que el cliente sepa si debe corregir el dato o la
   cabecera.
5. `204`: hecho, sin cuerpo. Devolver `200` con `{}` funciona y obliga al
   cliente a interpretar un cuerpo vacío a propósito.

El par que más confunde es el 3 y el 4 contra el `400`. Una regla que lo
resuelve: `400` es "ni siquiera pude entender el pedido"; `415` es "entendí
el formato y no lo acepto"; `422` es "entendí todo y el contenido está
mal".
:::

:::exercise level=2
Agrega al `api.php` el tratamiento del verbo `GET` en `/prestamos/{id}`,
devolviendo `200` con el préstamo o `404` si el número no existe.

Usa estos datos fijos en lugar de la base:

```php
$prestamos = [
    4471 => ['ejemplar_id' => 812, 'lector_id' => 47],
];
```

:::answer
```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

$prestamos = [
    4471 => ['ejemplar_id' => 812, 'lector_id' => 47],
];

$ruta = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if ($_SERVER['REQUEST_METHOD'] === 'GET'
    && preg_match('#^/prestamos/(\d+)$#', $ruta, $partes)) {

    $id = (int) $partes[1];

    if (!isset($prestamos[$id])) {
        http_response_code(404);
        echo json_encode(['error' => "El préstamo {$id} no existe"]);
        exit;
    }

    echo json_encode(['id' => $id] + $prestamos[$id]);
    exit;
}

http_response_code(404);
echo json_encode(['error' => 'Ruta no encontrada']);
```

Tres detalles que deciden si esto funciona.

`parse_url(..., PHP_URL_PATH)` separa la ruta de la consulta. Sin él,
`/prestamos/4471?formato=corto` no coincidiría con la expresión, y el
cliente recibiría `404` por haber mandado un parámetro de más.

La expresión exige `\d+` y se ancla en los dos extremos. Sin las anclas,
`/viejos/prestamos/4471/extra` también coincidiría.

Y el `(int)` en la conversión del número: `$partes[1]` es texto, como todo
lo que viene de la URL, y `$prestamos` tiene claves enteras.
`isset($prestamos['4471'])` con string funciona por conversión automática
de clave: funciona por accidente, y el accidente no es diseño.
:::

:::exercise level=3
Una aplicación informa que la API del acervo "a veces devuelve HTML". El
equipo de la API garantiza que devuelve JSON siempre.

Los dos tienen razón. Enumera tres situaciones en que una API PHP devuelve
HTML sin que nadie haya escrito HTML, y di cómo evitar cada una.

:::answer
**Uno: error fatal con `display_errors` activado.** Un `TypeError` no
tratado hace que PHP imprima el mensaje y la pila. Si el servidor está
configurado para formatear eso en HTML, el cliente recibe una página en
medio de lo que debía ser JSON, muchas veces **después** de que ya se envió
un pedazo del JSON.

Se evita con `display_errors` apagado en el servidor y un manejador de
excepciones registrado que responda en JSON con status `500`.

**Dos: el servidor web respondiendo antes que PHP.** El `404` de una ruta
inexistente, el `413` de un cuerpo demasiado grande, el `502` cuando PHP no
respondió: ninguno pasa por tu código, y lo predeterminado del servidor es
una página HTML.

Se evita configurando las páginas de error del servidor en el formato de
la API, y es el tipo de cosa que solo aparece cuando alguien prueba el
camino malo.

**Tres: salida antes del `header()`.** Una línea en blanco después del `?>`
en un archivo incluido, un `echo` de depuración olvidado, un aviso
impreso. PHP manda las cabeceras predeterminadas, que incluyen
`Content-Type: text/html`, y tu `header()` llega tarde:

```text
Warning: Cannot modify header information - headers already sent
```

Se evita no cerrando el `?>` en un archivo que solo tiene PHP, y por eso
existe esa regla.

Lo que tienen en común las tres vale más que las tres: **el camino de error
de tu API tiene que probarse como el camino de éxito**. Casi todo equipo
prueba el `201` y descubre el formato del `500` en producción.
:::
