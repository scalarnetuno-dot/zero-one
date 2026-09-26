---
source_hash: caacd823bc76
title: "Errores estandarizados"
number: 17
slug: erros-padronizados
part: p4
kicker: "El lector llamó diciendo que dio error. El log tenía 4.200 líneas y ninguna pista de cuál era la suya."
goal: >-
  Hacer que toda respuesta de error de la API tenga el mismo formato,
  traducir las excepciones del dominio en un status en una línea, no filtrar
  nunca un detalle interno, y entregarle al soporte un número que lleva
  directo a la línea correcta del log.
---

:::story Dio error
El teléfono de la biblioteca sonó a las 10:20. Vera atendió, escuchó, y se
lo pasó a Tainá sin decir nada, lo que ya era una forma de decir algo.

—Hola, soy Wellington. Intenté sacar un libro por la aplicación y dio
error.

—¿Qué error?

—Dio error. Apareció "Server Error". Lo intenté otra vez y dio otra vez.

—¿A qué hora fue eso?

—Ahora. Bueno, hace unos diez minutos. O quince.

Tainá abrió el `laravel.log` de homologación, que esa semana también
atendía las primeras pruebas con lectores de verdad. Cuatro mil doscientas
líneas desde las nueve. Buscó "Wellington": nada; el log no tenía el
nombre de nadie. Buscó "ERROR": treinta y una apariciones entre las 10:00
y las 10:20.

Eligió la que más se parecía a un préstamo. Una `QueryException` con un
*stack trace* de ochenta líneas. Pasó cuarenta minutos en ella, encontró la
causa, abrió la tarea.

Dedé leyó la tarea después del almuerzo.

—Ese error es del importador nocturno. Corrió otra vez a las diez porque
Cléber lo disparó a mano.

—¿Y el de Wellington?

—Debe de ser uno de los otros treinta.

Wellington llamó otra vez a las 14 h. Había conseguido sacar el libro en el
mostrador. Quería saber si la aplicación le iba a cobrar dos veces.
:::

## Tres formatos de error en la misma API

Haz el inventario de lo que devuelve hoy la API de la Casa Amarela cuando
algo sale mal. Son cuatro situaciones, y cada una sale de una forma:

```json
// 422, validación del Form Request
{"message": "El título es obligatorio.",
 "errors": {"titulo": ["El título es obligatorio."]}}

// 409, abort() en el controller
{"message": "Ejemplar no disponible"}

// 404, route model binding
{"message": "No query results for model [App\\Models\\Libro] 99999"}

// 500, con APP_DEBUG=true
{"message": "SQLSTATE[23000]: Integrity constraint violation...",
 "exception": "Illuminate\\Database\\QueryException",
 "file": "/var/www/vendor/laravel/framework/...",
 "line": 822,
 "trace": [ ... 80 ítems ... ]}
```

Cuatro formatos lo bastante parecidos para engañar y lo bastante distintos
para romper. La aplicación necesita un `if` para cada uno, y el `if` que lee
`message` para decidir qué hacer se rompe el día en que alguien traduzca la
frase.

Y el último filtra, en orden: el SQL con el nombre de la tabla y de la
restricción, el nombre de la clase interna, la ruta del proyecto en el
servidor, la versión del framework por la estructura de carpetas, y ochenta
líneas de camino de ejecución. Es un mapa del sistema entregado a quien
hizo la petición.

:::key
Un formato de error, para toda la API, es más importante que que el
formato sea perfecto. El cliente escribe el tratamiento **una vez** y
confía en él.

Tres formatos correctos, cada uno en un rincón, son peores que un solo
formato, imperfecto, en todas partes.
:::

## El formato

La Casa Amarela adopta un formato con cuatro claves:

```json
{
  "tipo": "ejemplar-no-disponible",
  "mensaje": "El ejemplar 2117 está prestado.",
  "campos": { "ejemplar_id": ["Ejemplar no disponible."] },
  "incidente": "01JHQ4Z8K3M2X9V7B5N1P0R6TW"
}
```

**`tipo`** es un identificador estable, en texto, que el cliente usa para
decidir. **Nunca cambia**, ni cuando se reescribe el mensaje. Es lo que
compara el `if` de la aplicación.

**`mensaje`** es para que lo lea una persona. Puede cambiar, traducirse,
recibir tildes. Ningún código debe decidir nada a partir de él.

**`campos`** es opcional y aparece cuando el error tiene un campo culpable:
siempre en el `422`, a veces en el `409`. Es el mismo mapa del `errors` del
capítulo @cap:validation-e-form-requests.

**`incidente`** es opcional y aparece cuando la falla es del servidor. Es
el número que Wellington le lee a Tainá por teléfono.

:::trivia
Existe una especificación para esto, la RFC 9457, *Problem Details for
HTTP APIs*, con las claves `type`, `title`, `status`, `detail` e
`instance`. El formato de la Casa Amarela es una versión en español de la
misma idea.

Si tu API la van a consumir muchos equipos que no conoces, seguir la RFC al
pie de la letra ahorra una conversación en cada integración. Si es la
aplicación de una biblioteca, las claves en español son más fáciles de
leer, y lo que importa es la disciplina: un formato, siempre.
:::

## El handler, donde termina toda excepción

En Laravel 11, el lugar al que llega toda excepción no capturada es el
`bootstrap/app.php`, en el bloque `withExceptions`. Es el
`set_exception_handler` del capítulo @cap:excecoes, con el framework
alrededor.

```php title="bootstrap/app.php" numbered
->withExceptions(function (Exceptions $exceptions) {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $r) => $r->is('api/*') || $r->expectsJson(),
    );

    $exceptions->render(
        fn (Throwable $e, Request $r) => $r->is('api/*')
            ? RespuestaDeError::para($e)
            : null,
    );
})
```

El `render` recibe toda excepción. Si la petición es de la API, una clase
decide la respuesta. Si no lo es, devuelve `null`, y Laravel hace lo que
haría normalmente: muestra la página de error del panel Blade.

La clase que decide es una traducción, y una traducción es un `match`:

```php title="app/Http/RespuestaDeError.php" numbered
final class RespuestaDeError
{
    public static function para(Throwable $e): JsonResponse
    {
        return match (true) {
            $e instanceof ValidationException
                => self::validacion($e),
            $e instanceof ExcepcionDeDominio
                => self::dominio($e),
            $e instanceof ModelNotFoundException,
            $e instanceof NotFoundHttpException
                => self::cuerpo(404, 'no-encontrado',
                    'El recurso pedido no existe.'),
            $e instanceof AuthenticationException
                => self::cuerpo(401, 'no-autenticado',
                    'Hay que iniciar sesión para continuar.'),
            $e instanceof AuthorizationException
                => self::cuerpo(403, 'sin-permiso',
                    'No tienes permiso para eso.'),
            $e instanceof ThrottleRequestsException
                => self::cuerpo(429, 'demasiadas-peticiones',
                    'Demasiados intentos. Espera un poco.'),
            default => self::falloInterno($e),
        };
    }

    // ...
}
```

Una lista, una lectura. Quien quiere saber qué responde la API para cada
tipo de falla lee un archivo.

## La excepción de dominio se vuelve status en una línea

Las tres excepciones del capítulo @cap:excecoes —`EjemplarNoDisponible`,
`LimiteDePrestamosAlcanzado`, `LectorConPendiente`— ya llevan datos. Lo que
les falta es decir, cada una, su `tipo`. Una clase madre lo resuelve:

```php title="app/Prestamos/ExcepcionDeDominio.php" numbered
abstract class ExcepcionDeDominio extends RuntimeException
{
    abstract public function tipo(): string;

    public function status(): int
    {
        return 409;
    }

    public function campos(): ?array
    {
        return null;
    }
}
```

```php title="app/Prestamos/EjemplarNoDisponible.php" numbered
final class EjemplarNoDisponible extends ExcepcionDeDominio
{
    public function __construct(
        public readonly int $registro,
        public readonly EstadoEjemplar $estado,
    ) {
        parent::__construct(sprintf(
            'El ejemplar %d está %s.',
            $registro,
            mb_strtolower($estado->etiqueta()),
        ));
    }

    public function tipo(): string
    {
        return 'ejemplar-no-disponible';
    }

    public function campos(): array
    {
        return ['ejemplar_id' => ['Ejemplar no disponible.']];
    }
}
```

Y la traducción, en el `RespuestaDeError`, es genérica:

```php
private static function dominio(ExcepcionDeDominio $e): JsonResponse
{
    return self::cuerpo(
        $e->status(),
        $e->tipo(),
        $e->getMessage(),
        $e->campos(),
    );
}
```

Una excepción nueva del dominio —`ReservaVencida`, digamos— hereda de
`ExcepcionDeDominio`, declara su `tipo`, y sale de la API en el formato
correcto sin que nadie toque el handler.

:::http title="El mismo error, antes y ahora"
POST /api/prestamos
Content-Type: application/json

{"ejemplar_id": 2117, "lector_id": 47}
---
409 Conflict
Content-Type: application/json

{
  "tipo": "ejemplar-no-disponible",
  "mensaje": "El ejemplar 2117 está prestado.",
  "campos": { "ejemplar_id": ["Ejemplar no disponible."] }
}
:::

Es la respuesta que prometió el ejercicio 3 del capítulo
@cap:validation-e-form-requests: el status dice la verdad, y la pantalla
sabe qué campo resaltar.

Con esto, los `abort(409, ...)` del controller del capítulo
@cap:o-crud-completo se pueden cambiar por `throw new
EjemplarNoDisponible(...)`. Y el controller deja de conocer status HTTP
para las reglas de negocio, lo que el capítulo @cap:services va a
convertir en principio.

:::pitfall
La tentación, después de tener el handler, es usar excepciones para todo,
incluso para lo que no es un error. "El libro no tiene ejemplares" no es
una excepción; es una lista vacía. "Lector sin préstamos" es `[]`, con
`200`.

La regla es la del capítulo @cap:excecoes: la excepción es para cuando la
operación **no puede continuar**. Una consulta que no encontró nada
continuó y terminó bien.
:::

## El `404` del binding: útil y demasiado genérico

El `404` automático del route model binding es un regalo, y viene con un
mensaje que no debería salir:

```text
No query results for model [App\Models\Libro] 99999
```

Revela el namespace y el nombre de la clase interna. No es una falla grave
—no abre ninguna puerta—, pero es información que el cliente no necesita y
que un curioso anota.

El `match` de arriba ya cambia el mensaje por el genérico. Y hay una
decisión que tomar sobre **cuándo el `404` es la respuesta correcta para
otra cosa**: el lector 47 pide el préstamo 312, que existe y es de otra
persona. ¿La respuesta es `403` o `404`?

| Respuesta | Le dice al cliente |
|---|---|
| `403` | "esto existe, y no es tuyo" |
| `404` | "esto no existe para ti" |

Tabla: Los dos son correctos en HTTP. El primero confirma la existencia
del recurso, y eso a veces es demasiada información.

Para los préstamos, confirmar que el número 312 existe dice poco. Para una
ruta como `/lectores?documento=...`, confirmar que un CPF está registrado
en la biblioteca dice mucho. La regla de la Casa Amarela: `404` cuando la
existencia del recurso es, en sí misma, un dato personal. El capítulo
@cap:autorizacao la aplica.

## El `500` no filtra nada

La última línea del `match` —el `default`— es la más importante, porque es
la que nadie planificó:

```php title="app/Http/RespuestaDeError.php" numbered
private static function falloInterno(Throwable $e): JsonResponse
{
    $status = $e instanceof HttpExceptionInterface
        ? $e->getStatusCode()
        : 500;

    return self::cuerpo(
        $status,
        'fallo-interno',
        'Algo salió mal de nuestro lado. Informa el '
            . 'código al soporte.',
        incidente: Incidente::actual(),
    );
}
```

La respuesta tiene una frase honesta y un número. Ninguna línea de SQL,
ningún nombre de clase, ninguna ruta de archivo.

El detalle sigue existiendo, **en el log**, donde quien lo necesita puede
leerlo. Laravel registra la excepción antes de llamar al `render`, y lo que
va al cliente y lo que va al log son decisiones separadas.

:::warning
Nada de esto vale con `APP_DEBUG=true`. Con él activado, Laravel agrega a
la respuesta la excepción, el archivo, la línea y el *trace* completo,
encima de lo que armó el handler, para ayudar en desarrollo.

En producción, `APP_DEBUG=false` es la primera línea de la lista del
capítulo @cap:git-ci-e-deploy, y la que más aparece en los informes de
intrusiones. Hay buscadores que indexan páginas de error de Laravel con el
modo depuración activado, y con frecuencia traen el contenido del `.env`.
:::

## El código de incidente: el número que pide el soporte

Wellington no tenía cómo decir cuál de las 31 líneas era la suya. Con el
incidente, lo tiene: está en la pantalla de la aplicación, y la aplicación
hasta puede ofrecer un botón para copiarlo.

```php title="app/Support/Incidente.php" numbered
final class Incidente
{
    public static function actual(): string
    {
        if (!Context::has('incidente')) {
            Context::add('incidente', (string) Str::ulid());
        }

        return Context::get('incidente');
    }
}
```

`Context` es un área de datos que vive durante la petición, y Laravel
**agrega todo lo que esté en ella a cada línea de log** escrita después.
Cuando se registra la excepción, la línea sale con el incidente adjunto:

```text
[2026-02-10 10:14:07] production.ERROR: SQLSTATE[23000]...
{"exception":"...","incidente":"01JHQ4Z8K3M2X9V7B5N1P0R6TW"}
```

Y la búsqueda que tardó cuarenta minutos pasa a tardar un comando:

```text
$ grep 01JHQ4Z8K3M2X9V7B5N1P0R6TW storage/logs/laravel.log
```

El ULID es un identificador único que empieza por el instante en que se
generó, así que los incidentes del mismo minuto quedan cerca en un
ordenamiento. Es un detalle pequeño que ayuda cuando alguien dice "fue más
o menos a las diez".

Por ahora, el incidente nace en el momento del error. En el capítulo
@cap:middleware, pasa a nacer **al principio de toda petición**, y cada
línea de log de esa petición —no solo la del error— lleva el mismo número.
Es la diferencia entre encontrar la excepción y encontrar toda la historia
que llevó hasta ella.

## `401` y `403` no son lo mismo

La lista del handler tiene los dos, y se confunden lo suficiente como para
merecer una sección propia.

**`401 Unauthorized`** quiere decir: **no sé quién eres**. Faltó el token,
o venció, o es inválido. El cliente debe mandar a la persona a iniciar
sesión otra vez.

**`403 Forbidden`** quiere decir: **sé quién eres, y no puedes**. El token
es válido. Iniciar sesión otra vez no resuelve nada.

El nombre oficial del `401` es desafortunado: dice *unauthorized* y
significa "no autenticado". La confusión viene de ahí, y la consecuencia es
concreta: una aplicación que recibe `401` cuando debería recibir `403`
manda a la persona a la pantalla de inicio de sesión, ella entra, lo
intenta otra vez, vuelve a la pantalla de inicio de sesión. Ciclo
infinito, con la persona convencida de que la contraseña está mal.

| Status | Pregunta que falló | El cliente hace |
|---|---|---|
| `401` | ¿quién eres? | pide iniciar sesión |
| `403` | ¿puedes? | muestra "sin permiso" |
| `404` | ¿esto existe? | muestra "no encontrado" |
| `409` | ¿el mundo lo permite? | explica y ofrece una salida |
| `422` | ¿el pedido está bien? | resalta los campos |

Tabla: Cinco status, cinco preguntas, cinco comportamientos de la
pantalla. Es la tabla que implementa la aplicación del lector, y es la
razón por la que existe cada uno.

:::note En tu carrera
El formato de error de una API es la parte del contrato que más cuesta
cambiar después, porque todo cliente lo trata en un lugar central, y
cambiar ese lugar central cambia el comportamiento de todas las pantallas
al mismo tiempo.

Si estás al principio de una API, dedícale una tarde antes de tener veinte
rutas. Si estás en una API que ya tiene tres formatos, el camino es el de
siempre: el formato nuevo pasa a salir en todas las rutas, con los campos
viejos mantenidos al lado hasta que migre el último cliente. Es trabajoso y
es invisible, y es el tipo de cosa que diferencia a quien mantiene un
sistema de quien solo escribe rutas.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  bootstrap/app.php            # withExceptions → RespuestaDeError
  app/Http/
    RespuestaDeError.php       # un match, toda la API
  app/Support/
    Incidente.php              # ULID en el Context
  app/Prestamos/
    ExcepcionDeDominio.php     # tipo(), status(), campos()
    EjemplarNoDisponible.php
    LimiteDePrestamosAlcanzado.php
    LectorConPendiente.php
:::

:::milestone
Fin de la Parte 4. La API de la Casa Amarela rechaza la entrada mal
formada en la puerta, devuelve solo lo que decidió devolver, lista el
acervo entero con búsqueda, filtros y techo, y responde todo error en el
mismo formato, con un número que lleva al soporte a la línea correcta del
log.

En el cuaderno de Tainá, una línea nueva: *"el cliente no lee el mensaje,
lee el tipo"*.
:::

:::summary
- Un formato de error para toda la API vale más que tres formatos
  correctos.
- `tipo` es estable y el cliente decide por él; `mensaje` es para las
  personas y puede cambiar.
- El `render` en el `withExceptions` recibe toda excepción; un `match`
  traduce el tipo en respuesta.
- Las excepciones de dominio heredan de una clase madre con `tipo`,
  `status` y `campos`; una nueva sale en el formato correcto sin tocar el
  handler.
- El `404` del binding necesita un mensaje genérico; `403` o `404` para un
  recurso ajeno es una decisión sobre lo que revela la existencia.
- El `500` no lleva SQL, clase, archivo ni *trace*; el detalle va al log.
- `APP_DEBUG=true` en producción anula el handler y filtra el sistema.
- El incidente en el `Context` aparece en toda línea de log y en la
  respuesta, y convierte una búsqueda de cuarenta minutos en un `grep`.
- `401` es "no sé quién eres"; `403` es "lo sé, y no puedes".
:::

:::checkpoint
Toda respuesta de error de la API tiene el mismo formato, las excepciones
de dominio se vuelven `409` sin `abort` en el controller, ninguna falla
interna filtra detalles, y puedes explicar, para cada uno de los cinco
status de error, qué debe hacer la pantalla del cliente al recibirlo.
:::

:::exercise level=1
Para cada situación, da el status y el `tipo` que devuelve la API de la
Casa Amarela:

1. El token de la aplicación venció.
2. El lector intenta renovar un préstamo que ya se renovó dos veces.
3. El cuerpo del `POST /prestamos` vino sin `lector_id`.
4. La base de datos está caída.
5. Una encargada del mostrador intenta borrar un libro, y solo el admin
   puede.

:::answer
1. `401`, `no-autenticado`. La aplicación lleva a la persona al inicio de
   sesión.
2. `409`, con un tipo de dominio, algo como `renovacion-agotada`. El pedido
   está bien; la regla no lo deja.
3. `422`, con `campos.lector_id`. El tipo puede ser `validacion`.
4. `500` —o `503`, si la falla se detecta como indisponibilidad—,
   `fallo-interno`, con `incidente`. Ninguna mención a la base en el
   mensaje.
5. `403`, `sin-permiso`. Está autenticada; su rol no lo permite.

El ítem 4 es el que más tienta a filtrar: "base de datos no disponible"
parece un mensaje honesto y útil. Le dice a quien está atacando que el
ataque funcionó.
:::

:::exercise level=2
Escribe `LectorConPendiente` heredando de `ExcepcionDeDominio`. Lleva el id
del lector y la multa abierta como `Dinero`, y el mensaje debe decir el
valor formateado.

Después responde: ¿el valor de la multa debe aparecer en la respuesta de la
API? ¿Para quién?

:::answer
```php title="app/Prestamos/LectorConPendiente.php" numbered
final class LectorConPendiente extends ExcepcionDeDominio
{
    public function __construct(
        public readonly int $lectorId,
        public readonly Dinero $multa,
    ) {
        parent::__construct(sprintf(
            'Hay una multa de %s pendiente.',
            $multa->formateado(),
        ));
    }

    public function tipo(): string
    {
        return 'lector-con-pendiente';
    }
}
```

**¿Debe aparecer?** Para el propio lector y para el equipo, sí: es la
información que permite resolverlo. El lector quiere saber cuánto pagar.

El cuidado es que el mensaje va a **quien hizo la petición**, y en el panel
de la encargada quien hizo la petición es la encargada, que tiene derecho
al dato. En la aplicación, solo el propio lector puede pedir un préstamo a
su nombre, así que solo él lo ve.

Si algún día existe una ruta en la que un lector actúe en nombre de otro
—una reserva para un dependiente, por ejemplo—, ese mensaje pasa a filtrar
la deuda de una persona a otra. Vale la pena anotar el riesgo en la clase,
porque es el tipo de cosa que la persona que cree la ruta nueva no se va a
acordar de revisar.
:::

:::exercise level=3
Una persona del equipo propone quitar el `RespuestaDeError` y, en su lugar,
poner un `try/catch` en cada controller, "para que cada ruta tenga control
total de su respuesta de error".

Escribe los argumentos a favor que probablemente tiene, los tres costos
concretos de la propuesta, y el caso en que un `try/catch` en el controller
es, de hecho, la elección correcta.

:::answer
**A favor, probablemente.** Localidad: quien lee el controller ve lo que
pasa con cada falla, sin abrir otro archivo. Flexibilidad: una ruta
específica puede querer una respuesta distinta para la misma excepción.

**Costo uno: el formato diverge.** Treinta controllers con `try/catch` son
treinta lugares armando el JSON de error, y en seis meses son cuatro
formatos distintos. Es el problema que el capítulo empezó resolviendo.

**Costo dos: el `default` desaparece.** El handler central garantiza que
**toda** excepción no prevista se vuelva un `500` seguro con incidente. El
`try/catch` en el controller trata las que el autor recordó; la que no
recordó sube sin tratamiento, o, peor, la atrapa un
`catch (\Throwable $e)` que devuelve el mensaje crudo.

**Costo tres: el controller vuelve a crecer y a conocer status.** Cada
método recibe diez líneas de `catch` que no son su responsabilidad.

**Cuándo el `try/catch` en el controller es correcto:** cuando la
excepción cambia **el camino** y no solo la respuesta. El panel Blade del
capítulo @cap:blade atrapa `EjemplarNoDisponible` para devolver a la
persona al formulario con el error en el campo: ahí, el comportamiento es
otro, no solo el formato. Y cuando una ruta tiene que intentar una
alternativa: si la portada no se encuentra en el almacenamiento, devolver
la portada predeterminada.

La regla: el controller atrapa cuando **hace algo distinto** con la falla.
Cuando solo va a formatear, el handler ya lo hace.
:::
