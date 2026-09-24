---
source_hash: 0e5d4ae2e609
title: "Un framework de cuarenta líneas"
number: 3
slug: um-framework-de-quarenta-linhas
part: p1
kicker: "Después de escribir el enrutador, la pregunta de la pasante fue la mejor del proyecto: ¿por qué no usar este y listo?"
goal: >-
  Escribir a mano lo mínimo de un framework —front controller, enrutador,
  contenedor y middleware— para poder explicar el ciclo de una petición en
  cualquier framework PHP, señalando dónde entra cada pieza.
---

:::story Veinte minutos
La carpeta `public/`, vacía al final del volumen 1, tenía diecinueve
archivos `.php` dos semanas después, y la dirección de cada pantalla
terminaba en uno de ellos.

—Esto queda como `/prestar.php?registro=2117` —dijo Tainá—. ¿La aplicación
lo va a consumir así?

—No. Queda como `POST /prestamos`.

—¿Y cómo?

Dedé tomó el teclado y empezó a escribir. Veinte minutos después había un
archivo con cuarenta y tantas líneas, y las tres rutas de la biblioteca
respondían JSON.

Tainá leyó el archivo entero, de arriba abajo, sin interrumpir.

—Bueno. ¿Por qué no usamos este y listo?
:::

## Un archivo por página

El proyecto de la Casa Amarela creció de la forma más natural del mundo:
una pantalla, un archivo. Es como se hizo PHP para funcionar, y es el
motivo por el que el lenguaje conquistó la web.

Tres cosas se rompen cuando el proyecto pasa de una docena de archivos.

**La dirección se vuelve un mapa del disco.** `/prestar.php` le cuenta a
quien esté afuera cómo está organizada la carpeta, y ata la URL al nombre
del archivo. Renombrar se vuelve un cambio de contrato.

**Cada archivo repite el principio.** Conexión, autoload, cabecera de
respuesta, revisión de la credencial. Diecinueve veces, y el día en que
una de ellas cambie, diecinueve lugares que recordar.

**No existe un lugar para lo que vale para todos.** Registrar cuánto tardó
cada petición, rechazar a quien no está autenticado, devolver JSON cuando
el programa se rompe: cada uno es una línea que tendría que estar en los
diecinueve archivos.

## Front controller: una sola puerta

La salida es antigua y tiene nombre: **toda petición entra por el mismo
archivo**, que decide qué hacer.

```text
antes                          después
/prestar.php?registro=2117     POST /prestamos
/listar.php                    GET  /libros
/recibo.php?id=4471            GET  /prestamos/4471/recibo
                               ↓
                               todo entra por index.php
```

Para que el servidor le entregue todo a un solo archivo, necesita una
instrucción. En Apache, es un archivo de configuración en la carpeta
pública:

```text title=".htaccess"
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.php [L]
```

Las dos últimas líneas dicen: si la ruta pedida **no** es un archivo que
existe —una imagen, un CSS—, mándala al `index.php`. Por eso todo proyecto
PHP moderno tiene una carpeta `public/` con casi nada dentro: solo el
`index.php` y los archivos que de verdad deben servirse directamente.

En el servidor integrado de PHP, lo mismo se hace desde la línea de
comandos:

```text
$ php -S localhost:8000 mini.php
```

## Un enrutador en veinte líneas

Con todo entrando por una puerta, falta decidir adónde va. Dos clases, y la
primera tiene tres líneas:

```php title="mini.php" numbered
<?php

declare(strict_types=1);

final class Respuesta
{
    public function __construct(
        public readonly int $status,
        public readonly array $cuerpo,
    ) {}
}
```

```php title="mini.php" numbered
final class Enrutador
{
    public function __construct(private array $rutas) {}

    public function despachar(
        string $metodo,
        string $ruta,
    ): Respuesta {
        foreach ($this->rutas as [$verbo, $patron, $accion]) {
            if ($verbo !== $metodo) {
                continue;
            }

            $regex = '#^' . preg_replace(
                '#\{(\w+)\}#',
                '(?<$1>[^/]+)',
                $patron,
            ) . '$#';

            if (preg_match($regex, $ruta, $hallados) === 1) {
                $parametros = array_filter(
                    $hallados,
                    'is_string',
                    ARRAY_FILTER_USE_KEY,
                );

                return $accion(...array_values($parametros));
            }
        }

        return new Respuesta(404, ['error' => 'Ruta no encontrada']);
    }
}
```

El bucle es simple; la única línea que merece atención es la que arma la
expresión regular. Cambia `{id}` por un grupo con nombre que coincide con
cualquier cosa que no sea una barra. `/libros/{id}` se vuelve
`#^/libros/(?<id>[^/]+)$#`.

Después de la coincidencia, `$hallados` trae los pedazos dos veces: con
índice numérico y con el nombre. El `array_filter` con
`ARRAY_FILTER_USE_KEY` se queda solo con los de nombre, y esos se vuelven
los argumentos de la función de la ruta.

:::term Despachar
Elegir qué código corre para una petición y llamarlo. Es lo único que hace
un enrutador, y es la pieza que todo framework tiene en el medio.

La tabla de rutas de un lado, la petición del otro, una función al final.
:::

La tabla de rutas es un array, y cada línea tiene verbo, patrón y qué
hacer:

```php title="mini.php" numbered
$acervo = [
    12 => ['titulo' => 'Dom Casmurro', 'anio' => 1899],
    31 => ['titulo' => 'Vidas Secas', 'anio' => 1938],
];

$rutas = [
    ['GET', '/libros',
        fn(): Respuesta => new Respuesta(200, $acervo)],

    ['GET', '/libros/{id}',
        function (string $id) use ($acervo): Respuesta {
            $id = (int) $id;

            if (!isset($acervo[$id])) {
                return new Respuesta(404, [
                    'error' => "El libro {$id} no existe",
                ]);
            }

            return new Respuesta(200, ['id' => $id] + $acervo[$id]);
        }],

    ['POST', '/prestamos',
        fn(): Respuesta => new Respuesta(201, ['id' => 4471])],
];
```

Y el front controller, que es el final del archivo, tiene seis líneas:

```php title="mini.php" numbered
function enviar(Respuesta $r): void
{
    http_response_code($r->status);
    header('Content-Type: application/json');
    echo json_encode($r->cuerpo, JSON_UNESCAPED_UNICODE);
}

$enrutador = new Enrutador($rutas);

enviar($enrutador->despachar(
    $_SERVER['REQUEST_METHOD'],
    parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH),
));
```

Levántalo y prueba:

```text
$ php -S localhost:8000 mini.php
```

```text
$ curl -s localhost:8000/libros/31
{"id":31,"titulo":"Vidas Secas","anio":1938}

$ curl -s localhost:8000/libros/99
{"error":"El libro 99 no existe"}

$ curl -s localhost:8000/nada
{"error":"Ruta no encontrada"}
```

:::key
Fíjate en lo que el enrutador **no** es: un `switch` gigante con `$_SERVER`
adentro.

La diferencia no es estética. Un `switch` mezcla la decisión de la ruta con
el trabajo de cada ruta, y crece junto con los dos. Aquí la decisión está
en una clase que no sabe nada de libros, y el trabajo está en una tabla que
no sabe nada de expresiones regulares.

Cambiar el enrutador por otro no toca ninguna ruta. Es esa separación la
que hace que la palabra "framework" signifique algo.
:::

## El contenedor ingenuo

El proyecto tiene clases que dependen de otras: un servicio de préstamo
necesita un repositorio, que necesita una conexión. Armar eso a mano en
cada ruta es la repetición de siempre:

```php
$servicio = new ServicioDePrestamo(
    new RepositorioDeLibros(
        new Conexion()
    )
);
```

El `Servicios` del capítulo @cap:como-organizar-um-projeto-php lo resolvió
con una fábrica escrita a mano para cada clase, y el ejercicio 2 de ese
capítulo ya señalaba lo que las fábricas tienen de mecánico: leer el
constructor, pedir cada tipo, pasarlos en orden. Un contenedor que lee el
constructor solo hace innecesarias las fábricas. Quince líneas lo resuelven
para siempre:

```php title="mini.php" numbered
final class Contenedor
{
    private array $hechos = [];

    public function obtener(string $clase): object
    {
        if (isset($this->hechos[$clase])) {
            return $this->hechos[$clase];
        }

        $constructor = (new ReflectionClass($clase))
            ->getConstructor();

        $argumentos = [];

        foreach ($constructor?->getParameters() ?? [] as $p) {
            $tipo = $p->getType();

            if (!$tipo instanceof ReflectionNamedType
                || $tipo->isBuiltin()) {
                throw new RuntimeException(
                    "No sé construir \${$p->getName()}"
                );
            }

            $argumentos[] = $this->obtener($tipo->getName());
        }

        return $this->hechos[$clase]
            = new $clase(...$argumentos);
    }
}
```

`ReflectionClass` es la parte de PHP que le permite al programa **mirar su
propio código**: qué métodos tiene una clase, qué parámetros recibe un
método, de qué tipo es cada uno. El contenedor lo usa para leer la lista de
parámetros del constructor y resolver cada uno, recursivamente.

```php
$c = new Contenedor();

$servicio = $c->obtener(ServicioDePrestamo::class);
```

```text
  (conexión creada)
```

Una línea, y se armó la cadena entera. Pídelo otra vez:

```php
$otro = $c->obtener(ServicioDePrestamo::class);

var_dump($servicio === $otro);
```

```text
bool(true)
```

Ninguna conexión nueva. El contenedor guarda lo que ya construyó, y por eso
una sola `Conexion` atiende todo el programa sin que nadie pase el `$pdo`
de función en función.

:::pitfall
El contenedor de arriba es ingenuo a propósito, y el límite aparece rápido:

```text
No sé construir $status
```

Solo sabe resolver parámetros que son **clases**. Un `int`, un `string` o
una configuración que viene de un archivo no se pueden adivinar: alguien
tiene que decir qué poner ahí.

Guardar esa frase vale más que el código: cuando un framework se queje de
que no puede resolver una dependencia, casi siempre es esto. Un parámetro
que no es una clase, o una interfaz sin que nadie haya dicho qué
implementación usar.
:::

## Middleware: la cebolla antes de tener nombre

Falta el lugar donde poner lo que vale para todas las rutas. La idea es
envolver la acción en capas: cada capa recibe la petición, hace su parte,
llama a la de adentro y todavía ve la respuesta volviendo.

```php title="mini.php" numbered
$accion = fn(string $pet): string => "[accion:{$pet}]";

$middlewares = [
    fn(string $pet, callable $siguiente): string
        => 'log(' . $siguiente($pet) . ')',

    fn(string $pet, callable $siguiente): string
        => 'auth(' . $siguiente($pet) . ')',
];

$pipeline = array_reduce(
    array_reverse($middlewares),
    fn(callable $siguiente, callable $actual): callable
        => fn(string $pet): string => $actual($pet, $siguiente),
    $accion,
);

echo $pipeline('GET /libros'), "\n";
```

```text
log(auth([accion:GET /libros]))
```

La salida **es** el dibujo. El `log` envuelve al `auth`, que envuelve a la
acción. La petición entra de afuera hacia adentro y la respuesta sale de
adentro hacia afuera, pasando por las mismas capas en orden inverso.

El `array_reduce` con la lista invertida es lo que arma esa muñeca rusa.
Cada paso toma lo que ya se armó —el "siguiente"— y lo envuelve en la capa
actual.

Y la ganancia práctica aparece cuando una capa decide **no** llamar a la
siguiente:

```php
fn(string $pet, callable $siguiente): string
    => autenticado($pet) ? $siguiente($pet) : '401',
```

Ahí la acción nunca corre. Así funcionan la autenticación, el límite de
peticiones y el rechazo por permisos en todo framework PHP, y a partir de
aquí ninguno de ellos necesita explicarte el mecanismo.

## Lo que todavía falta

El archivo tiene unas cien líneas contando todo, y atiende tres rutas. Vale
la pena listar, sin prisa, lo que no hace:

| Falta | Qué sale mal sin eso |
|---|---|
| validación de la entrada | cada ruta revisa a mano, y una se olvida |
| tratamiento central de errores | un `TypeError` se vuelve HTML en medio del JSON |
| capa de base con migraciones | el esquema vive en la cabeza de alguien |
| autenticación de verdad | no hay sesión, token ni hash de contraseña |
| respuestas estandarizadas | cada ruta inventa el formato del error |
| pruebas con petición falsa | solo se puede probar levantando el servidor |
| tareas fuera de la petición | el correo atrasa la respuesta al usuario |
| caché, log, cola | todo se vuelve un archivo en `/tmp` |
| documentación | el contrato existe solo en el código |

Tabla: Cada línea de esta tabla es un trabajo de días, y ninguna es
específica de la Casa Amarela: es exactamente la misma lista en cualquier
proyecto web del mundo.

## Lo que acabas de entender

Las cuatro piezas de este capítulo no son una simplificación didáctica de
un framework. Son la **forma** de todos ellos.

```text
petición
   ↓
front controller        index.php
   ↓
middlewares             capa, capa, capa
   ↓
enrutador               qué función corre
   ↓
contenedor              arma lo que la función necesita
   ↓
tu función              la única parte que es tuya
   ↓
respuesta               vuelve por las capas
```

Cuando un framework hable de *kernel*, *pipeline*, *service provider* o
*route model binding*, el vocabulario va a ser nuevo y el dibujo no. Va a
ser este, con más cuidado, más casos tratados y más años de corrección
encima.

:::note En tu carrera
Vas a oír, en algún momento, que "el framework es para quien no sabe
hacerlo a mano". La respuesta no es discrepar: es estar de acuerdo y
continuar la frase.

Hacerlo a mano llevó veinte minutos y produjo cien líneas que atienden tres
rutas y no tratan errores, no validan, no autentican y no tienen una sola
prueba. Completar la tabla de la sección anterior es un año de trabajo, y
el resultado sería un framework peor y con un solo mantenedor.

Lo que compró este capítulo no fue independencia: fue la capacidad de
**leer** el framework. Cuando algo salga mal tres capas por debajo de tu
código, vas a saber qué capas son esas, y esa es la diferencia entre abrir
un ticket y abrir el archivo.
:::

:::tree title="Dónde estamos ahora"
acervo/
  mini.php          # front controller, enrutador, contenedor, middleware
  src/
    Acervo/
    Circulacion/
    Prestamos/
    Lectores/
  composer.json
  phpstan.neon
:::

:::summary
- Un archivo por página ata la URL al disco, repite el principio en todo
  archivo y no deja lugar para lo que vale para todos.
- El front controller hace que todo entre por `index.php`; el servidor
  necesita una regla de reescritura para eso.
- El enrutador es una tabla de rutas, una coincidencia de patrón y una
  llamada, y no sabe nada del dominio.
- `{id}` en el patrón se vuelve un grupo con nombre en la expresión, y el
  grupo se vuelve un argumento.
- El contenedor usa reflexión para leer los parámetros del constructor y
  armar la cadena de dependencias, guardando lo que ya construyó.
- El contenedor ingenuo solo resuelve parámetros que son clases; el resto
  alguien tiene que declararlo.
- El middleware envuelve la acción en capas; la capa que no llama a la
  siguiente interrumpe la petición.
- Lo que falta en el archivo de cien líneas es, ítem por ítem, lo que
  entrega un framework.
:::

:::checkpoint
Explicas el ciclo de una petición en cualquier framework PHP señalando
dónde entran el front controller, el middleware, el enrutador y el
contenedor; escribes un enrutador con parámetro de ruta; y sabes decir por
qué un contenedor no puede resolver cierta dependencia.
:::

:::exercise level=1
Agrega al `mini.php` la ruta `DELETE /libros/{id}`, que devuelve `204` sin
cuerpo cuando el libro existe y `404` cuando no existe.

Después explica por qué el `enviar()` necesita un ajuste.

:::answer
```php
    ['DELETE', '/libros/{id}',
        function (string $id) use ($acervo): Respuesta {
            $id = (int) $id;

            if (!isset($acervo[$id])) {
                return new Respuesta(404, [
                    'error' => "El libro {$id} no existe",
                ]);
            }

            return new Respuesta(204, []);
        }],
```

El `enviar()` necesita un ajuste porque, tal como está, siempre imprime el
cuerpo, y `json_encode([])` produce `[]`, dos caracteres. Una respuesta
`204` con dos bytes de cuerpo contradice su propio status, y algunos
clientes la tratan como una respuesta mal formada.

```php
function enviar(Respuesta $r): void
{
    http_response_code($r->status);

    if ($r->status === 204) {
        return;
    }

    header('Content-Type: application/json');
    echo json_encode($r->cuerpo, JSON_UNESCAPED_UNICODE);
}
```

Fíjate dónde vive la corrección: en el envío, no en la ruta. Si cada ruta
tuviera que acordarse de no imprimir nada, una se olvidaría, y es la misma
razón que justifica que exista el front controller.
:::

:::exercise level=2
El enrutador actual hace coincidir `{id}` con cualquier cosa que no sea una
barra. Eso hace que `GET /libros/abc` entre en la ruta y llegue a
`(int) 'abc'`, que es `0`.

Agrega al patrón la posibilidad de exigir un formato, para que
`/libros/{id:\d+}` solo coincida con dígitos, y `/libros/abc` devuelva
`404` sin llamar nunca a la función.

:::answer
El cambio va en la línea que arma la expresión:

```php
$regex = '#^' . preg_replace_callback(
    '#\{(\w+)(?::([^}]+))?\}#',
    fn(array $p): string
        => '(?<' . $p[1] . '>' . ($p[2] ?? '[^/]+') . ')',
    $patron,
) . '$#';
```

El patrón ahora reconoce dos formas: `{id}`, sin restricción, y
`{id:\d+}`, con ella. El `preg_replace_callback` es necesario porque el
reemplazo pasó a depender de lo que se encontró: con el `preg_replace`
simple no había cómo elegir entre el formato informado y el
predeterminado.

La ruta queda:

```php
['GET', '/libros/{id:\d+}', ...]
```

Y `/libros/abc` no coincide con ninguna ruta, y cae en el `404` del final
del bucle.

Vale la pena notar qué es esto: la primera **validación** del mini
framework, y ocurre antes de que exista la función de la ruta. Por eso todo
framework ofrece algo parecido: la alternativa es que toda ruta empiece con
un `if` que revise el formato de su propia dirección.
:::

:::exercise level=3
Junta las piezas: haz que `mini.php` use el contenedor y una cadena de dos
middlewares de verdad.

El primer middleware mide cuánto tardó la petición y agrega la cabecera
`X-Tiempo`. El segundo rechaza con `401` cualquier petición sin la cabecera
`Authorization`, **excepto** `GET`.

Escribe el código y di en qué orden deben quedar los dos en la lista, y por
qué.

:::answer
```php title="mini.php" numbered
$medirTiempo = function (array $pet, callable $sig): Respuesta {
    $inicio = hrtime(true);

    $respuesta = $sig($pet);

    $ms = (hrtime(true) - $inicio) / 1_000_000;
    header(sprintf('X-Tiempo: %.1fms', $ms));

    return $respuesta;
};

$exigirCredencial = function (array $pet, callable $sig): Respuesta {
    if ($pet['metodo'] !== 'GET'
        && !isset($_SERVER['HTTP_AUTHORIZATION'])) {
        return new Respuesta(401, ['error' => 'Credencial ausente']);
    }

    return $sig($pet);
};

$accion = fn(array $pet): Respuesta => $enrutador->despachar(
    $pet['metodo'],
    $pet['ruta'],
);

$pipeline = array_reduce(
    array_reverse([$medirTiempo, $exigirCredencial]),
    fn(callable $siguiente, callable $actual): callable
        => fn(array $pet): Respuesta => $actual($pet, $siguiente),
    $accion,
);

enviar($pipeline([
    'metodo' => $_SERVER['REQUEST_METHOD'],
    'ruta' => parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH),
]));
```

**El orden es primero la medición, después la credencial**, y el motivo es
lo que cada una hace con la respuesta.

El middleware de tiempo tiene que ser la capa más externa para medir
**todo**, incluido el tiempo gastado rechazando a alguien. Si estuviera
adentro, las peticiones rechazadas con `401` saldrían sin `X-Tiempo`, y son
justamente las que vas a querer medir el día en que alguien esté martillando
la API.

El de credencial tiene que estar afuera de la acción y adentro de la
medición: interrumpe, e interrumpir temprano es el punto. Una petición sin
credencial no debe llegar al enrutador, mucho menos a la base.

La regla general, que sirve para cualquier cadena: **lo que observa va
afuera; lo que rechaza va justo después; lo que trabaja va en el medio.**
:::
