---
source_hash: 7485400f7adf
title: "Validation y Form Requests"
number: 14
slug: validation-e-form-requests
part: p4
kicker: "El mismo libro estaba tres veces en el acervo. El ISBN era igual en los tres, salvo por los guiones."
goal: >-
  Rechazar la entrada inválida en la puerta, sacar las reglas de formato de
  dentro del controller, hacer que el PATCH parcial funcione sin borrar
  campos, y saber decir qué no es validación y por eso no va ahí.
---

:::story Tres Dom Casmurro
Vera pidió el informe de títulos duplicados porque el conteo del acervo no
coincidía con el del inventario en papel. Dedé ejecutó la consulta
esperando cero.

```text
mysql> SELECT titulo, isbn FROM libros
    ->  WHERE titulo LIKE 'Dom Casmurro%';
+--------------+-------------------+
| titulo       | isbn              |
+--------------+-------------------+
| Dom Casmurro | 9788535910667     |
| Dom Casmurro | 978-85-359-1066-7 |
| Dom Casmurro | 978 8535910667    |
+--------------+-------------------+
```

—Pero el ISBN es `unique` —dijo Tainá—. Lo vi en la migration.

—Lo es. Y los tres son distintos.

—Son el mismo número.

—Para ti.

Vera miró por encima de su hombro.

—El primero fui yo. El segundo fue Neide, que copia de la ficha
catalográfica. El tercero no sé, pero tiene un espacio, así que fue
alguien apurado.

—¿Y cuál es el correcto?

—El libro —dijo Vera—. Los tres son el mismo libro. Tengo dos ejemplares
en el estante, no seis.
:::

## La validación no es regla de negocio

Antes de cualquier código, una separación de la que depende todo este
capítulo. Hay dos preguntas distintas que una petición tiene que responder
antes de volverse una escritura:

**¿El pedido está bien formado?** ¿Vino el título? ¿Es texto? ¿Cabe en
doscientos caracteres? ¿El ISBN tiene trece dígitos? ¿El `ejemplar_id` es
un número que existe en la tabla?

**¿El pedido está permitido ahora?** ¿El ejemplar está disponible? ¿El
lector ya tiene tres libros? ¿Debe una multa de más de cinco reales?

La primera pregunta es sobre **el formato de lo que llegó**, y se puede
responder mirando solo el cuerpo de la petición y, como mucho, la
existencia de un registro. La segunda es sobre **el estado del mundo**, y
depende de cosas que cambian de un segundo a otro.

| Pregunta | Ejemplo | Respuesta de error | Dónde vive |
|---|---|---|---|
| ¿bien formado? | ISBN con 13 dígitos | `422` | validación |
| ¿permitido ahora? | ejemplar disponible | `409` | regla de negocio |

Tabla: Los dos status del capítulo @cap:o-que-e-uma-api-rest, ahora con
dirección en el código. El `422` dice "corrige lo que mandaste"; el `409`
dice "lo que mandaste está bien y el mundo no lo deja".

:::key
La validación mira **el pedido**. La regla de negocio mira **el mundo**.

Cuando no sepas adónde va una revisión, hazte la pregunta: si el cliente
manda exactamente el mismo cuerpo dentro de cinco minutos, ¿puede cambiar
la respuesta? Si puede, no es validación.
:::

Esa separación importa porque las dos cosas tienen vidas distintas. La
regla de formato casi nunca cambia: un ISBN va a seguir teniendo trece
dígitos. La regla de negocio cambia cada vez que Vera se acuerda de una
excepción, y tiene que probarse sin HTTP, que es el tema del capítulo
@cap:services.

## Las reglas donde entra el dato

En el capítulo anterior, la validación quedó dentro del controller:

```php title="app/Http/Controllers/LibroController.php" numbered
public function store(Request $request)
{
    $datos = $request->validate([
        'titulo' => ['required', 'string', 'max:200'],
        'autor' => ['required', 'string', 'max:150'],
        'tema' => ['required', 'string', 'max:40'],
        'isbn' => ['nullable', 'string', 'size:13', 'unique:libros'],
        'anio' => ['nullable', 'integer', 'min:1400'],
    ]);

    // ...
}
```

Funciona. El `validate()` revisa, y, si algo falla, lanza una
`ValidationException` que Laravel convierte en `422` sin que tu método
continúe. Es la misma interrupción del binding que devuelve `404`: el
código después de la línea solo corre si la línea pasó.

Lo que está mal no es el comportamiento, es la **dirección**. Son tres
problemas, y empeoran con el tiempo.

**El controller crece por el lado equivocado.** El método `store` tiene una
responsabilidad —recibir el pedido y entregar la respuesta— y ahora tiene
quince líneas de reglas de formato antes de empezar a hacerlo.

**Las reglas se repiten.** El `update` tiene casi las mismas, con una
diferencia en el `unique` que alguien se va a olvidar de sincronizar. Y la
pantalla de Vera, en el panel Blade, tiene una tercera copia.

**Las reglas no tienen nombre.** Para saber qué acepta la API en un `POST
/libros`, alguien tiene que abrir el controller y leer un array en medio de
un método. No existe un lugar que se llame "qué es un libro válido".

## Form Request: el controller que vuelve a tener cuatro líneas

Laravel tiene una clase cuyo único trabajo es responder la primera
pregunta:

```text
$ php artisan make:request StoreLibroRequest

   INFO  Request [app/Http/Requests/StoreLibroRequest.php]
         created successfully.
```

```php title="app/Http/Requests/StoreLibroRequest.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreLibroRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'titulo' => ['required', 'string', 'max:200'],
            'autor' => ['required', 'string', 'max:150'],
            'tema' => ['required', 'string', 'max:40'],
            'isbn' => [
                'nullable', 'digits:13', 'unique:libros,isbn',
            ],
            'anio' => [
                'nullable', 'integer', 'min:1400',
                'max:' . now()->year,
            ],
        ];
    }
}
```

Y el controller:

```php title="app/Http/Controllers/LibroController.php" numbered
public function store(StoreLibroRequest $request)
{
    $libro = Libro::create($request->validated());

    return response()
        ->json($libro, 201)
        ->header('Location', route('libros.show', $libro));
}
```

El cambio está en el **tipo del parámetro**. Cuando Laravel va a llamar al
`store`, ve que el método pide un `StoreLibroRequest`, construye ese objeto
a partir de la petición y **corre la validación antes de entregarlo**. Si
falla, el método nunca se llama.

Es el contenedor del capítulo @cap:um-framework-de-quarenta-linhas leyendo
el tipo del parámetro por reflexión, con un paso más en el medio. El
capítulo @cap:service-container abre esa caja por completo.

:::term Form Request
Una clase que representa un tipo de pedido —"crear libro", "realizar
préstamo"— y lleva sus reglas de formato. El controller declara que recibe
ese tipo, y la validación ocurre antes de que empiece el método.
:::

El `validated()` devuelve **solo los campos que tienen regla**. Si el
cliente manda `observacion_interna` o `perfil`, no están en `rules()` y no
llegan al `create`. Es una segunda capa de protección detrás del
`$fillable` del capítulo @cap:eloquent, y la más importante de las dos:
frena en la puerta, antes de que el dato se acerque al model.

:::pitfall
`$request->all()` después de un Form Request devuelve **todo lo que vino**,
no solo lo que pasó. La validación ocurrió, pero su resultado se ignoró.

```php
Libro::create($request->all());       // el cuerpo entero
Libro::create($request->validated()); // solo lo que tiene regla
```

Las dos líneas tienen el mismo tamaño, y la primera deshace la mitad del
trabajo del capítulo. En una revisión de código, `all()` después de un Form
Request es un defecto, no un estilo.
:::

### El `authorize()` que devuelve `true`

El método `authorize()` pregunta si **esta persona** puede hacer **este
pedido**. Por ahora, devuelve `true` para todo el mundo: todavía no existe
"esta persona", porque la API no tiene inicio de sesión.

Dejarlo en `true` es una decisión honesta para este capítulo, y una deuda
anotada: el capítulo @cap:autorizacao vuelve a él. Si `authorize()`
devuelve `false`, Laravel responde `403` sin llamar al controller, y por
eso existe aquí y no en otro lugar.

## Normalizar antes de revisar

Las tres filas de *Dom Casmurro* pasaron por el `unique` porque `unique`
compara texto, y `9788535910667` y `978-85-359-1066-7` son textos
distintos. La regla estaba bien. El dato llegó en tres formas.

La corrección es la lección del capítulo @cap:strings, ahora con
dirección: **normalizar a la entrada**. El Form Request tiene un gancho que
corre antes de las reglas:

```php title="app/Http/Requests/StoreLibroRequest.php" numbered
protected function prepareForValidation(): void
{
    $this->merge([
        'isbn' => $this->filled('isbn')
            ? preg_replace('/\D/', '', $this->input('isbn'))
            : null,
        'titulo' => $this->filled('titulo')
            ? $this->normalizarEspacios($this->input('titulo'))
            : $this->input('titulo'),
    ]);
}

private function normalizarEspacios(string $texto): string
{
    return trim(preg_replace('/\s+/u', ' ', $texto));
}
```

`\D` es "cualquier cosa que no sea un dígito". Guiones, espacios y puntos
salen, y los tres ISBN se vuelven el mismo, que entonces el `unique`
rechaza.

:::http title="El segundo Dom Casmurro, ahora"
POST /api/libros
Content-Type: application/json

{"titulo": "Dom  Casmurro", "autor": "Machado de Assis",
 "tema": "literatura", "isbn": "978-85-359-1066-7"}
---
422 Unprocessable Content
Content-Type: application/json

{
  "message": "The isbn has already been taken.",
  "errors": {
    "isbn": ["The isbn has already been taken."]
  }
}
:::

Dos cosas en esa respuesta. El mensaje está en inglés: la corrección llega
dentro de dos secciones. Y el `422` volvió **con el ISBN normalizado**
revisado: la base nunca vio el guion.

:::key
El orden es **normalizar, después revisar, después grabar**. Revisar antes
de normalizar deja pasar variaciones; normalizar después de grabar deja la
base sucia y obliga a toda consulta a limpiar otra vez.

Y el dato que guarda la base es siempre el normalizado. El formato con
guiones, si la pantalla quiere mostrarlo, es trabajo de la salida: del
capítulo @cap:api-resources.
:::

Los tres registros que ya están ahí no desaparecen solos. Necesitan una
migración de datos que normalice la columna, junte los ejemplares en el
registro que quede y borre los otros, y esa migración hay que revisarla con
Vera antes de ejecutarla, porque "cuál de los tres queda" es una pregunta
de negocio.

## `sometimes`, `nullable` y el `PATCH` que borra campos

Dos palabras que parecen sinónimas y que producen, cuando se confunden, el
defecto del capítulo anterior.

**`nullable`** dice: el campo puede venir con el valor `null`. No dice nada
sobre que el campo **no venga**.

**`sometimes`** dice: aplica las otras reglas solo **si el campo está
presente** en el cuerpo.

| Cuerpo | `['required']` | `['nullable']` | `['sometimes', 'required']` |
|---|---|---|---|
| `{}` | falla | pasa | pasa |
| `{"autor": null}` | falla | pasa | falla |
| `{"autor": ""}` | falla | pasa, se vuelve `null` | falla |
| `{"autor": "Machado"}` | pasa | pasa | pasa |

Tabla: La tercera columna es el `PATCH` correcto: un campo ausente se
ignora; un campo presente tiene que ser válido. La segunda columna es el
`PATCH` que borra el autor cuando el formulario manda el campo vacío.

La línea del `""` sorprende. Laravel tiene un middleware global que
**convierte el string vacío en `null`** antes de que corra la validación,
y por eso `nullable` acepta un string vacío y graba nulo. Es cómodo en un
formulario HTML, y es el camino exacto por el que desaparece un campo
obligatorio.

Con eso, el `update` del capítulo anterior recibe su propia clase:

```php title="app/Http/Requests/UpdateLibroRequest.php" numbered
class UpdateLibroRequest extends FormRequest
{
    public function rules(): array
    {
        $obligatorio = $this->isMethod('PUT')
            ? 'required'
            : 'sometimes';

        return [
            'titulo' => [$obligatorio, 'string', 'max:200'],
            'autor' => [$obligatorio, 'string', 'max:150'],
            'tema' => [$obligatorio, 'string', 'max:40'],
            'isbn' => [
                'sometimes', 'nullable', 'digits:13',
                Rule::unique('libros', 'isbn')
                    ->ignore($this->route('libro')),
            ],
            'anio' => ['sometimes', 'nullable', 'integer'],
        ];
    }
}
```

El `$this->route('libro')` es el model que el binding ya cargó: el Form
Request ve los parámetros de la ruta. Y el `ignore` resuelve el defecto
clásico del `unique` en la edición.

:::pitfall
Sin el `ignore`, editar el título de un libro y reenviar el mismo ISBN
produce `422`: "The isbn has already been taken". Tomado **por el propio
libro**.

Es el error que encuentra todo proyecto Laravel en la primera pantalla de
edición, y la corrección apurada es quitar el `unique` del `update`.
Entonces el `PATCH` pasa a aceptar el ISBN de otro libro, y el duplicado
que este capítulo empezó arreglando vuelve por la otra puerta.
:::

## Una regla propia, y cuándo ya existe

Las reglas listas de Laravel cubren más de lo que parece, y vale la pena
buscar antes de escribir:

```php
'estado' => ['required', Rule::enum(EstadoEjemplar::class)],
'ejemplar_id' => ['required', 'integer', 'exists:ejemplares,id'],
'devolver_hasta' => ['required', 'date', 'after:today'],
'portada' => ['nullable', 'image', 'max:2048'],
```

El `Rule::enum` es el más valioso de los cuatro: usa el enum del capítulo
@cap:enums-datas-e-valores como fuente de verdad. Si se agrega un caso
nuevo al enum, la validación pasa a aceptarlo sin que nadie se acuerde de
actualizar una lista de strings.

Cuando ninguna regla lista sirve, una clase lo resuelve. El ISBN tiene un
dígito verificador —el último número se calcula a partir de los otros
doce—, y trece dígitos cualesquiera no son un ISBN:

```php title="app/Rules/Isbn13.php" numbered
<?php

declare(strict_types=1);

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class Isbn13 implements ValidationRule
{
    public function validate(
        string $atributo,
        mixed $valor,
        Closure $fallar,
    ): void {
        if (!preg_match('/^\d{13}$/', (string) $valor)) {
            $fallar('El :attribute tiene que tener 13 dígitos.');
            return;
        }

        $suma = 0;

        foreach (str_split(substr($valor, 0, 12)) as $i => $d) {
            $suma += (int) $d * ($i % 2 === 0 ? 1 : 3);
        }

        $verificador = (10 - $suma % 10) % 10;

        if ($verificador !== (int) $valor[12]) {
            $fallar('El :attribute no es un ISBN válido.');
        }
    }
}
```

```php
'isbn' => ['nullable', new Isbn13(), 'unique:libros,isbn'],
```

La regla es una clase pequeña, comprobable por separado y reutilizada en
los dos Form Requests. Fíjate en que **no consulta la base**: revisar si el
ISBN existe en el acervo es trabajo del `unique`, y mezclar las dos cosas
produciría una regla que solo funciona con la base encendida.

:::note
El `:attribute` es un marcador que Laravel cambia por el nombre del campo.
El nombre se puede traducir, lo que lleva a la sección siguiente.
:::

## `422`, `errors` y el campo que el cliente resalta

La respuesta de error de validación tiene un formato fijo, y es el formato
que va a leer la aplicación del lector:

```json
{
  "message": "El título es obligatorio. (y 1 error más)",
  "errors": {
    "titulo": ["El título es obligatorio."],
    "isbn": ["El ISBN no es un ISBN válido."]
  }
}
```

La clave `errors` es un mapa de **nombre del campo** a **lista de
mensajes**. Por ella la pantalla sabe qué casilla pintar de rojo, y por eso
el nombre del campo es contrato: renombrar `titulo` a `title` rompe el
resaltado en todo cliente publicado.

Los mensajes en español vienen de dos lugares. El idioma predeterminado del
proyecto va en el `.env`, y el archivo de traducción se publica una vez:

```text
$ php artisan lang:publish
```

Y el nombre del campo, que aparece dentro del mensaje, lo declara el Form
Request:

```php title="app/Http/Requests/StoreLibroRequest.php" numbered
public function attributes(): array
{
    return [
        'titulo' => 'título',
        'isbn' => 'ISBN',
    ];
}

public function messages(): array
{
    return [
        'isbn.unique' => 'Este ISBN ya está en el acervo.',
    ];
}
```

El mensaje del `unique` merece un texto propio porque es el único que pide
una acción distinta: la persona no tiene que corregir lo que escribió;
tiene que buscar el libro que ya existe.

:::pitfall
El formato del `422` de Laravel es **distinto** del formato de los otros
errores que devuelve hoy la API. El `abort(409, ...)` del capítulo anterior
produce `{"message": "..."}`, sin `errors`; el `404` produce otro formato;
un `500`, un tercero.

Tres formatos de error en la misma API es el tema entero del capítulo
@cap:erros-padronizados. Por ahora, anótalo: el cliente va a tener que
tratar cada uno de una forma distinta, y eso se va a arreglar.
:::

## El préstamo, y lo que **no** entra en el Form Request

```php title="app/Http/Requests/RealizarPrestamoRequest.php" numbered
class RealizarPrestamoRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'ejemplar_id' => [
                'required', 'integer', 'exists:ejemplares,id',
            ],
            'lector_id' => [
                'required', 'integer', 'exists:lectores,id',
            ],
        ];
    }
}
```

Es todo. Ninguna de las once reglas de Vera está aquí, y la tentación de
ponerlas es enorme: el Form Request tiene acceso a la base, y la regla "el
ejemplar tiene que estar disponible" cabe en una closure de tres líneas.

Tres motivos para resistir.

**La revisión sería falsa.** El Form Request corre antes del controller,
fuera de la transacción y sin bloqueo en la fila. Entre que la validación
dice "disponible" y que el préstamo se graba, Neide puede haber prestado el
mismo ejemplar en el mostrador. La revisión que vale es la que corre
**dentro** de la transacción, con el `lockForUpdate` del capítulo anterior.

**El status sería equivocado.** Una regla de validación que falla devuelve
`422`, que dice "corrige tu pedido". Pero el pedido está bien: el ejemplar
existe, el número es entero. Es el mundo el que no lo deja. Es `409`.

**La regla quedaría presa del HTTP.** El comando `biblioteca:multas`, el
panel Blade y un script de importación también prestan libros. Si la regla
vive en el Form Request, cada uno de esos caminos tiene que reescribirla.

:::key
El `exists` queda en el Form Request porque responde "¿este identificador
apunta a algo?": es formato, con un pie en la base. El "¿esta cosa se puede
prestar ahora?" queda afuera, porque la respuesta cambia cada segundo y
necesita un bloqueo para ser verdad.

La frontera es incómoda, y es incómoda en todo framework. En la duda, deja
la revisión en el service: va a ser redundante a veces, pero nunca va a ser
falsa.
:::

## Validar también lo que sale

Una nota corta, porque la herramienta llega en el próximo capítulo. Validar
la entrada protege la base del cliente; nadie está protegiendo al cliente
de la base.

El `LibroController::show` devuelve el model entero. Si mañana alguien
agrega una columna `observacion_interna` a la tabla, sale en la respuesta
sin que cambie ninguna línea del controller. La entrada tiene una lista de
permisos: el `rules()`. La salida todavía no tiene ninguna.

:::note En tu carrera
La validación es el primer lugar donde mira una persona revisora con
experiencia en un proyecto nuevo, porque dice mucho en poco espacio.

Las reglas en el controller dicen que el proyecto creció sin pausa para
ordenar. `$request->all()` dice que alguien confía en el cliente. Un
`unique` sin `ignore` en el `update` dice que nadie probó la edición. Y una
regla de negocio dentro del Form Request dice que el equipo todavía no
separó "formato" de "estado", que es la conversación más productiva que
puedes empezar en una primera semana.

Ninguna de esas observaciones exige conocer el dominio. Por eso son una
buena puerta de entrada para contribuir en un proyecto que todavía no
entiendes.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Http/Requests/
    StoreLibroRequest.php         # reglas + normalización
    UpdateLibroRequest.php        # PUT × PATCH, unique con ignore
    RealizarPrestamoRequest.php   # solo formato
  app/Rules/
    Isbn13.php                    # dígito verificador
  app/Http/Controllers/
    LibroController.php           # store y update con 4 líneas
  lang/es/validation.php
:::

:::summary
- La validación responde si el pedido está bien formado; la regla de
  negocio, si el mundo lo permite. La primera da `422`; la segunda, `409`.
- La prueba de la frontera: si el mismo cuerpo, dentro de cinco minutos,
  puede tener otra respuesta, no es validación.
- El Form Request es una clase por tipo de pedido; el controller la recibe
  por tipo, y la validación corre antes del método.
- `validated()` devuelve solo lo que tiene regla; `all()` después de un
  Form Request deshace la protección.
- `prepareForValidation` normaliza antes de revisar; la base guarda siempre
  la forma normalizada.
- `nullable` acepta `null`; `sometimes` ignora lo ausente. El `PATCH` pide
  `sometimes`.
- El `unique` en el `update` necesita `ignore`, o acusa al propio registro.
- `Rule::enum` usa el enum como fuente de verdad; una regla propia es una
  clase pequeña y sin base.
- `errors` es un mapa de campo a mensajes, y el nombre del campo es
  contrato.
:::

:::checkpoint
Mueves las reglas de formato a Form Requests, normalizas la entrada antes
de revisar, implementas un `PATCH` que no borra el campo ausente, y sabes
explicarle a una persona del equipo por qué "ejemplar disponible" no es
una regla de validación.
:::

:::exercise level=1
Clasifica cada revisión como **validación** (Form Request, `422`) o **regla
de negocio** (service, `409`):

1. El correo del lector tiene formato de correo.
2. El lector no tiene una multa de más de cinco reales.
3. El `ejemplar_id` existe en la tabla.
4. El ejemplar no está en restauración.
5. La fecha de devolución informada es posterior a hoy.
6. El lector no tiene tres libros.

:::answer
1. Validación. El formato no cambia con el tiempo.
2. Regla de negocio. La multa se puede pagar dentro de cinco minutos.
3. Validación. Es una revisión de que el identificador apunta a algo:
   formato, con un pie en la base.
4. Regla de negocio. El estado del ejemplar cambia, y la revisión necesita
   un bloqueo para ser verdad.
5. Validación. "Después de hoy" depende del reloj, pero no del estado de
   ningún registro: el mismo cuerpo, mañana, solo puede empezar a fallar, y
   por el motivo correcto.
6. Regla de negocio. Es el caso clásico: el lector devuelve un libro y el
   mismo pedido pasa.

El ítem 5 es el que genera discusión, y la discusión es buena. La prueba
de los cinco minutos ayuda: lo que cambia la respuesta ahí es el
calendario, no una acción de otra persona en el sistema.
:::

:::exercise level=2
Escribe el `prepareForValidation` y las reglas de un `StoreLectorRequest`
con `nombre`, `documento` (CPF) y `telefono`. El CPF llega con o sin puntos
y guion; el teléfono, con o sin paréntesis. La base guarda solo dígitos, y
el documento es único.

:::answer
```php title="app/Http/Requests/StoreLectorRequest.php" numbered
class StoreLectorRequest extends FormRequest
{
    protected function prepareForValidation(): void
    {
        $this->merge([
            'documento' => $this->soloDigitos('documento'),
            'telefono' => $this->soloDigitos('telefono'),
            'nombre' => $this->filled('nombre')
                ? trim(preg_replace(
                    '/\s+/u', ' ', $this->input('nombre'),
                ))
                : null,
        ]);
    }

    public function rules(): array
    {
        return [
            'nombre' => ['required', 'string', 'max:150'],
            'documento' => [
                'required', 'digits:11',
                'unique:lectores,documento',
            ],
            'telefono' => ['nullable', 'digits_between:10,11'],
        ];
    }

    private function soloDigitos(string $campo): ?string
    {
        return $this->filled($campo)
            ? preg_replace('/\D/', '', $this->input($campo))
            : null;
    }
}
```

`digits:11` revisa el tamaño y que solo haya dígitos, pero no revisa el
dígito verificador del CPF: para eso, una regla propia como `Isbn13`.

Y un detalle que suele escaparse: `soloDigitos` devuelve `null` cuando el
campo no vino, y no un string vacío. Así el `required` del documento falla
con el mensaje correcto, en lugar de fallar en el `digits:11` con un
mensaje que confunde a quien completó el formulario.
:::

:::exercise level=3
Una persona del equipo propuso esta regla para el
`RealizarPrestamoRequest`, argumentando que "así el error aparece en el
campo correcto de la pantalla":

```php
'ejemplar_id' => [
    'required',
    'exists:ejemplares,id',
    function ($atributo, $valor, $fallar) {
        $e = Ejemplar::find($valor);
        if ($e->condicion !== EstadoEjemplar::Bueno) {
            $fallar('Ejemplar no disponible.');
        }
    },
],
```

El argumento tiene mérito. Escribe la respuesta de revisión: lo que está
bien en la motivación, los dos defectos concretos, y cómo atender el deseo
de resaltar el campo sin mover la regla.

:::answer
**Lo que está bien.** La motivación es legítima: la aplicación sabe
resaltar un campo a partir del `errors`, y un `409` con una frase suelta
obliga a la pantalla a decidir sola dónde mostrarlo. La persona está
pensando en el cliente, que es para lo que existe la API.

**Primer defecto: la revisión no es verdad.** La closure corre antes de la
transacción y sin bloqueo. Entre que dice "disponible" y el `create`, el
mostrador puede haber prestado el ejemplar. La regla pasaría a dar una
falsa sensación de seguridad, y la revisión real, dentro de la
transacción, seguiría siendo necesaria, ahora duplicada.

**Segundo defecto: el status miente.** El cliente recibe `422`, que manda a
corregir el pedido. El pedido está bien. Una aplicación que trata el `422`
limpiando el campo y pidiendo otro valor le va a mostrar a la lectora que
"escribió mal" el libro que tiene en la mano.

Hay un tercero, menor: si `exists` falla, la closure igual corre, `find`
devuelve `null`, y `$e->condicion` explota con un error de propiedad sobre
nulo. El orden de las reglas no interrumpe la lista por defecto.

**Cómo atender el deseo.** La respuesta `409` puede llevar el campo. El
capítulo @cap:erros-padronizados define el formato único de error de la
API, y tiene espacio para eso:

```json
{
  "tipo": "ejemplar-no-disponible",
  "mensaje": "El ejemplar 2117 está prestado.",
  "campos": {"ejemplar_id": ["Ejemplar no disponible."]}
}
```

La pantalla resalta el campo, el status dice la verdad, y la regla sigue
viviendo donde tiene bloqueo. La revisión termina con una propuesta, no con
un rechazo.
:::
