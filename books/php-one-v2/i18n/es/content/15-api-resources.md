---
source_hash: 4602a92843c3
title: "API Resources"
number: 15
slug: api-resources
part: p4
kicker: "La columna se creó para que el equipo anotara lo que no decía delante del lector. Durante once días, el lector lo leyó."
goal: >-
  Separar el formato de la respuesta de la estructura de la tabla, decidir
  campo por campo lo que sale, cargar relaciones sin volver al N+1, y tratar
  la respuesta como un contrato que otra persona ya está usando.
---

:::story Once días
El mensaje llegó por el formulario de contacto de la aplicación, un lunes.

> Buen día. Quería saber quién escribió en mi registro que "devuelve
> mojado, revisar siempre". No devolví mojado. Fue la lluvia de diciembre y
> avisé. Saludos, Rosângela.

Tainá lo leyó en voz alta. Dedé abrió la aplicación en el celular de ella,
entró al perfil, y ahí estaba, justo debajo del teléfono, en un campo que
la pantalla mostraba sin ninguna etiqueta:

```text
devuelve mojado, revisar siempre
```

—Esa es la `observacion_interna` —dijo—. Cléber creó la columna hace dos
semanas, para que Vera anotara esas cosas.

—¿Y por qué aparece en la aplicación?

—Porque el `show` devuelve el model. Y el model tiene la columna.

—¿Desde cuándo?

Dedé miró la fecha de la migration.

—Once días.

Vera, que estaba en la puerta, preguntó cuántas personas tenían una
anotación.

—Treinta y ocho.

—Entonces son treinta y ocho llamadas —dijo—. La de Rosângela la hago yo
personalmente.
:::

## El model no es el JSON

Hasta aquí, los controllers devuelven el model directamente:

```php
public function show(Lector $lector)
{
    return $lector;
}
```

Laravel sabe convertir un model en JSON, y lo hace incluyendo **todas las
columnas de la tabla**. Es cómodo el primer día y es una trampa a partir
del segundo, porque ata dos cosas que cambian por motivos distintos:

**La tabla cambia por motivos internos.** El equipo necesita una columna
para anotaciones, una columna para controlar la importación, un campo
nuevo para un informe. Esos cambios los decide el equipo, cuando quiera.

**La respuesta es un contrato externo.** La aplicación del lector se
publicó en la tienda con un formato en mente, y su versión vieja sigue
instalada en celulares que no se actualizan hace meses. El formato de la
respuesta solo puede cambiar con aviso, y a veces no puede cambiar.

Cuando el JSON es el retrato de la tabla, **toda migration se vuelve un
cambio de contrato**, sin que nadie lo note. La `observacion_interna` fue
una migration de tres líneas, revisada y aprobada. Nadie pensó en la API,
porque no había nada en el cambio que dijera "API".

:::key
La respuesta de una API es una **lista de permisos**, escrita campo por
campo. Lo que no está en la lista no sale, incluido lo que se cree
después.

Es la misma lógica del `rules()` del capítulo anterior, en la otra
dirección. La entrada tiene una lista de lo que puede entrar; la salida
necesita una lista de lo que puede salir.
:::

Existe el `$hidden` en el model, que esconde columnas de la serialización.
Resuelve el caso de la contraseña, y es lo primero que aprende todo el
mundo. Pero es una **lista de prohibiciones**: esconde lo que te acordaste
de esconder. La columna creada la semana que viene no está en ella.

## `JsonResource`

```text
$ php artisan make:resource LectorResource
```

```php title="app/Http/Resources/LectorResource.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class LectorResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'nombre' => $this->nombre,
            'telefono' => $this->telefono,
            'miembro_desde' => $this->created_at->toDateString(),
        ];
    }
}
```

```php title="app/Http/Controllers/LectorController.php" numbered
public function show(Lector $lector)
{
    return new LectorResource($lector);
}
```

:::http title="El mismo lector, ahora con lista de permisos"
GET /api/lectores/47
---
200 OK
Content-Type: application/json

{
  "data": {
    "id": 47,
    "nombre": "Rosângela Pires",
    "telefono": "21987654321",
    "miembro_desde": "2014-03-11"
  }
}
:::

Cuatro campos. La `observacion_interna` no está, el `documento` no está, el
`perfil` no está, el `updated_at` no está. Y la columna que alguien cree el
mes que viene tampoco va a estar.

Dentro del `toArray`, `$this->id` lee la propiedad del model que envuelve
el resource. El resource es un **envoltorio**: le pasa las lecturas al
model y decide qué devolver.

Fíjate en el `miembro_desde`. La tabla tiene `created_at`, que es un nombre
de base: dice cuándo se insertó la fila. El contrato tiene `miembro_desde`,
que es un nombre de dominio: dice lo que eso significa para el lector. El
día en que los registros antiguos se importen del Sistema con la fecha
original, la columna va a cambiar y el nombre del contrato va a seguir
teniendo sentido.

### El sobre `data`

El resource devuelve el objeto dentro de una clave `data`. Parece
ceremonia, y es una decisión con motivo: queda espacio en el nivel de
arriba para cosas que no son el recurso: la paginación, los enlaces, los
avisos de obsolescencia.

```json
{
  "data": [ ... ],
  "links": { "next": "..." },
  "meta": { "total": 4031 }
}
```

Una API que empieza sin sobre y tiene que agregar metadatos después tiene
dos opciones malas: romper a todo cliente, cambiando el formato de la raíz;
o meter los metadatos en cabeceras HTTP, donde nadie busca. Con el sobre
desde el primer día, la decisión no hace falta tomarla.

## Colecciones

Para una lista, el mismo resource, aplicado a cada ítem:

```php title="app/Http/Controllers/LibroController.php" numbered
public function index()
{
    $libros = Libro::orderBy('titulo')->paginate(20);

    return LibroResource::collection($libros);
}
```

Cuando lo que llega al `collection` es un paginador, el resource arma el
sobre completo solo —`data`, `links` y `meta`—, con los números que
calculó el paginador. El capítulo @cap:paginacao-filtros-e-buscas se ocupa
del paginador en sí.

Existe también la clase `ResourceCollection`, para cuando la colección
necesita campos propios en el nivel de arriba. En la mayoría de los casos,
el `::collection` alcanza, y es un archivo menos.

## `whenLoaded`: la relación que solo aparece si se cargó

El `LibroResource` tiene que mostrar los autores y el conteo de ejemplares
disponibles. La primera versión suele ser esta:

```php
'autores' => $this->autores->pluck('nombre'),
```

Y es el N+1 de la serialización del que avisó el capítulo
@cap:relacionamentos: `$this->autores` dispara una consulta **por cada
libro**, en el momento en que se arma la respuesta, después de que el
controller terminó.

La versión correcta pregunta antes de tocar:

```php title="app/Http/Resources/LibroResource.php" numbered
class LibroResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'titulo' => $this->titulo,
            'isbn' => $this->isbn,
            'anio' => $this->anio,
            'tema' => $this->tema,
            'autores' => AutorResource::collection(
                $this->whenLoaded('autores'),
            ),
            'ejemplares_disponibles' => $this->whenCounted(
                'ejemplaresDisponibles',
            ),
        ];
    }
}
```

`whenLoaded('autores')` revisa si la relación **ya se cargó**, con `with` o
`load`. Si se cargó, la entrega. Si no, la clave entera **desaparece de la
respuesta**, sin consulta. El `whenCounted` hace lo mismo para el
`withCount`.

La consecuencia es que **quien decide lo que viene es el controller**, por
la consulta que hizo:

```php
// en el listado: autores y conteo
Libro::with('autores')
    ->withCount(['ejemplares as ejemplares_disponibles_count'
        => fn ($q) => $q->where('condicion', EstadoEjemplar::Bueno)])
    ->paginate(20);

// en la búsqueda rápida del mostrador: solo el libro
Libro::where('isbn', $isbn)->first();
```

El resource es el mismo en los dos. La respuesta cambia de tamaño según lo
que cargó el controller, y nunca por una consulta escondida.

:::pitfall
`whenLoaded` resuelve el N+1, y crea una forma sutil de inconsistencia: el
mismo recurso, en dos endpoints, viene con campos distintos. Un cliente que
programó contra el listado espera `autores`; en la búsqueda rápida, la
clave no existe.

Eso es aceptable si está **documentado** —"la búsqueda por ISBN no trae
autores"— y es un defecto si es accidental. En la duda, decide por
endpoint lo que viene, escríbelo en la documentación del capítulo
@cap:documentacao-da-api, y pruébalo. El capítulo
@cap:testes-de-feature-http-e-banco tiene una prueba para exactamente eso.
:::

Con el `preventLazyLoading` del capítulo @cap:relacionamentos activado,
tocar `$this->autores` sin `whenLoaded` en una relación no cargada lanza
una excepción en desarrollo. Los dos mecanismos se complementan: uno
protege la respuesta, el otro avisa cuando alguien se olvida.

## El campo que no puede salir, nunca

No todo campo es público para todo el mundo. El lector puede ver su propio
teléfono y no puede ver el teléfono de otro lector. La bibliotecaria ve los
dos, y ve también el documento.

El `when` incluye un campo bajo condición:

```php title="app/Http/Resources/LectorResource.php" numbered
public function toArray(Request $request): array
{
    $propio = $request->user()?->lector_id === $this->id;
    $equipo = $request->user()?->esEquipo() ?? false;

    return [
        'id' => $this->id,
        'nombre' => $this->nombre,
        'telefono' => $this->when(
            $propio || $equipo,
            $this->telefono,
        ),
        'documento' => $this->when($equipo, $this->documento),
        'miembro_desde' => $this->created_at->toDateString(),
    ];
}
```

El `$request->user()` todavía devuelve `null`: la API no tiene inicio de
sesión hasta el capítulo @cap:autenticacao. El `?->` garantiza que, por
ahora, nadie es "propio" ni "equipo", y los dos campos simplemente no
salen. Cuando llegue el inicio de sesión, el resource ya está listo para
él.

:::key
Hay tres categorías de campo, y cada una pide un tratamiento:

**Público:** sale siempre. Título, año, nombre.

**Condicional:** sale para quien tiene derecho. Teléfono, documento. Va en
el `when`.

**Interno:** no sale nunca, para nadie, por esta API.
`observacion_interna`, `contrasena`, `importado_del_sistema`. No aparece
en el resource, y la prueba del capítulo
@cap:testes-de-feature-http-e-banco garantiza que siga sin aparecer.
:::

La `observacion_interna` ni siquiera pertenece al segundo grupo. El equipo
ve la anotación en el **panel Blade**, que es otra puerta, con otra
pantalla y otro permiso. La API de la aplicación nunca la necesita, y por
eso para la API no existe.

## Un formato, toda la API

El sobre, los nombres, las fechas: todo eso se vuelve convención de la
API, y vale la pena escribirlo una vez.

| Decisión | Elección de la Casa Amarela |
|---|---|
| nombres de campo | `snake_case`, en español |
| fechas | `AAAA-MM-DD` para el día; ISO 8601 con zona para el instante |
| dinero | objeto `{centavos, formateado}` |
| enum | el `value`, nunca el `name` |
| ausencia | clave presente con `null`, salvo en `whenLoaded` |

Tabla: Cinco decisiones que el equipo toma una vez y que el cliente
aprende una vez. La peor elección en cada línea es no elegir, y dejar que
cada resource decida.

El dinero merece una línea de código, porque el objeto `Dinero` del
capítulo @cap:enums-datas-e-valores no sabe volverse JSON solo:

```php title="app/Http/Resources/PrestamoResource.php" numbered
public function toArray(Request $request): array
{
    return [
        'id' => $this->id,
        'estado' => $this->estado->value,
        'retirado_en' => $this->retirado_en->toIso8601String(),
        'devolver_hasta' => $this->devolver_hasta->toDateString(),
        'devuelto_en' => $this->devuelto_en?->toIso8601String(),
        'con_atraso' => $this->conAtraso(),
        'multa' => $this->when(
            $this->multa_en_centavos !== null,
            fn () => [
                'centavos' => $this->multa_en_centavos->centavos,
                'formateado' => $this->multa_en_centavos
                    ->formateado(),
            ],
        ),
        'ejemplar' => new EjemplarResource(
            $this->whenLoaded('ejemplar'),
        ),
    ];
}
```

El `con_atraso` es el caso del ejercicio del capítulo
@cap:enums-datas-e-valores: no es una columna, es una conclusión calculada
por el model. Para el cliente, no hay diferencia: recibe un booleano y no
necesita saber si se leyó o se calculó. Es la ventaja de tener el contrato
separado de la tabla, vista por el lado bueno.

El dinero sale con las dos formas. La aplicación usa `centavos` para sumar
y `formateado` para mostrar, y nunca tiene que formatear moneda en
JavaScript, que es el lugar donde la coma y el punto suelen cambiar de
lugar.

## Cambiar la respuesta sin romper a quien ya la usa

La aplicación de la versión 1.0 está instalada. El equipo decidió que
`tema`, que hoy es texto, se va a volver un objeto con `id` y `nombre`.
¿Qué hacer?

**Agregar es seguro.** Un campo nuevo no rompe a ningún cliente bien
escrito, porque un cliente bien escrito ignora lo que no conoce.

**Cambiar el tipo o el nombre rompe.** La aplicación 1.0 espera texto en
`tema` y va a recibir un objeto.

La salida es **agregar al lado, después quitar**:

```php
'tema' => $this->tema->nombre,   // queda, marcado para salir
'tema_detallado' => new TemaResource($this->tema),
```

El campo viejo sigue; el nuevo aparece al lado. La documentación marca el
viejo como obsoleto, con fecha. Cuando la aplicación 1.0 deje de tener
usuarios —y eso se mide, no se adivina—, el campo viejo sale.

Versionar toda la API (`/api/v2/libros`) por un campo es
desproporcionado: duplica rutas, controllers y pruebas para resolver un
problema que resuelve una clave más. El capítulo @cap:documentacao-da-api
vuelve a esto, con el plan completo.

:::note En tu carrera
La fuga de datos más común en una API no es un ataque: es un
`return $model` y una migration hecha meses después por otra persona.

No aparece en la revisión, porque la migration no toca la API y el
controller no cambió. No aparece en la prueba manual, porque nadie mira el
JSON entero. Aparece cuando una Rosângela lee lo que escribieron sobre
ella.

Si entras en un proyecto que devuelve el model crudo, el primer resource
que escribas le va a parecer burocracia a quien está ahí. Escríbelo de
todas formas, y escribe la prueba que revisa que la columna interna no
sale. Es el tipo de contribución que nadie agradece hasta el día en que
evitó una llamada.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Http/Resources/
    LibroResource.php        # whenLoaded, whenCounted
    AutorResource.php
    EjemplarResource.php
    LectorResource.php       # teléfono y documento condicionales
    PrestamoResource.php     # dinero como objeto, con_atraso
  app/Http/Controllers/      # ninguno devuelve el model crudo
:::

:::summary
- El model es el esquema interno; el JSON es un contrato externo. Los dos
  cambian por motivos distintos y necesitan código distinto.
- Una respuesta es una lista de permisos campo por campo; `$hidden` es una
  lista de prohibiciones y no protege lo que se cree después.
- `JsonResource::toArray` declara lo que sale; el sobre `data` deja
  espacio para `links` y `meta`.
- `::collection` con un paginador arma el sobre completo solo.
- `whenLoaded` y `whenCounted` incluyen la relación solo si ya se cargó;
  quien decide es la consulta del controller.
- Los campos son públicos, condicionales (`when`) o internos, y los
  internos no aparecen en el resource.
- Las convenciones de formato —fechas, dinero, enum, ausencia— se deciden
  una vez para toda la API.
- Agregar un campo es seguro; renombrar o cambiar el tipo rompe. La salida
  es agregar al lado y quitar después.
:::

:::checkpoint
Ningún controller de la API devuelve el model crudo. Escribes resources con
campos públicos, condicionales y ausentes por decisión, cargas relaciones
sin N+1 en la serialización, y sabes planificar el cambio de un campo sin
romper la aplicación que ya está instalada.
:::

:::exercise level=1
Para cada columna de la tabla `ejemplares`, di si entra en el
`EjemplarResource` como pública, condicional (¿para quién?) o no entra:

`id`, `libro_id`, `registro`, `condicion`, `adquirido_en`,
`precio_de_compra`, `proveedor`, `created_at`, `updated_at`.

:::answer
- `id`: pública. Es el identificador que usa el cliente para las otras
  rutas.
- `libro_id`: no entra como un número suelto. El libro viene como objeto
  anidado con `whenLoaded('libro')`, o por un enlace. El número de una
  clave foránea es un detalle del esquema.
- `registro`: pública. Es el número pegado en el libro, y Vera habla de él.
- `condicion`: pública, por el `value` del enum. Es lo que quiere saber el
  lector.
- `adquirido_en`: condicional, para el equipo. Al lector no le interesa.
- `precio_de_compra`: no entra. Es información de gestión, y la muestra el
  panel.
- `proveedor`: no entra, por el mismo motivo.
- `created_at`, `updated_at`: no entran. Son fechas de control de la base;
  si algún día tiene sentido exponer "registrado el", entra con un nombre
  de dominio.

El `libro_id` es el que más divide opiniones. Exponer el número no está
mal, y muchas APIs lo hacen. El punto es decidir y ser consistente: si
`ejemplar` trae `libro_id`, `prestamo` debería traer `ejemplar_id` por el
mismo criterio.
:::

:::exercise level=2
Este listado de préstamos con atraso se volvió lento después de que el
resource recibió dos campos. Encuentra el problema y corrígelo sin cambiar
el formato de la respuesta.

```php
public function atrasados()
{
    return PrestamoResource::collection(
        Prestamo::conAtraso()->get()
    );
}
```

```php
// dentro del PrestamoResource
'lector' => $this->lector->nombre,
'libro' => $this->ejemplar->libro->titulo,
```

:::answer
Los dos campos tocan relaciones sin `whenLoaded`, y el controller no cargó
nada. Para 60 préstamos atrasados: una consulta de la lista, 60 de
lectores, 60 de ejemplares y 60 de libros: 181.

La corrección tiene dos mitades, y las dos son necesarias.

En el controller, cargar:

```php
Prestamo::conAtraso()
    ->with(['lector', 'ejemplar.libro'])
    ->get()
```

En el resource, proteger:

```php
'lector' => $this->whenLoaded(
    'lector',
    fn () => $this->lector->nombre,
),
'libro' => $this->whenLoaded(
    'ejemplar',
    fn () => $this->ejemplar->libro->titulo,
),
```

Solo el controller lo resuelve hoy; solo el resource impide que el
problema vuelva en el próximo endpoint que use el mismo resource sin
cargar. La segunda forma del `whenLoaded`, con una función, sirve para
cuando el valor se deriva de la relación y no es la relación entera.

El formato no cambió: `lector` sigue siendo un texto y `libro` también.
:::

:::exercise level=3
La aplicación del lector, versión 1.0, lee `devolver_hasta` como texto en
el formato `DD/MM/AAAA`: un error de la primera versión de la API, que
formateaba la fecha para mostrarla. El equipo quiere cambiarlo por el
formato `AAAA-MM-DD` de la convención.

Hay 1.300 instalaciones de la versión 1.0. La 1.1, que ya sabe leer los dos
formatos, está en la tienda hace tres semanas.

Escribe el plan: qué cambia en el resource hoy, cómo decidir cuándo
terminar la transición, y qué no harías.

:::answer
**Hoy: agregar al lado.**

```php
'devolver_hasta' => $this->devolver_hasta->format('d/m/Y'),
'devolver_hasta_iso' => $this->devolver_hasta->toDateString(),
```

El campo viejo sigue idéntico; el nuevo sigue la convención. La versión
1.1 se actualiza para leer `devolver_hasta_iso` cuando exista.

**Decidir cuándo terminar: medir.** La aplicación manda su propia versión
en una cabecera; si no la manda, ese es el primer ajuste, en la 1.2. Con el
log estructurado del capítulo @cap:cache-logs-e-medicao, se cuenta cuántas
peticiones por día vienen todavía de la 1.0. La transición termina cuando
el número llegue a cero, o sea lo bastante pequeño como para que la
biblioteca acepte avisarles a las personas en persona.

**Lo que pasa después, en dos pasos.** Primero, `devolver_hasta` pasa a
tener el formato nuevo y `devolver_hasta_iso` sigue existiendo, marcado
como obsoleto. Después, en una versión futura, `devolver_hasta_iso` sale.
Es ceremonia, y es lo que hace que el nombre correcto termine en el campo
correcto.

**Lo que no hay que hacer.**

Cambiar el formato de `devolver_hasta` hoy: 1.300 aplicaciones pasan a
mostrar una fecha equivocada o a romperse.

Crear `/api/v2`: duplica toda la API por un campo.

Decidir por la cabecera de versión **dentro del resource**, devolviendo
formatos distintos a cada cliente: funciona, y crea un resource con un
`if` por versión que nadie se va a animar a borrar. Un campo más es más
simple, más visible y más fácil de quitar.
:::
