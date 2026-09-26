---
source_hash: 04fb68b9083d
title: "El CRUD completo"
number: 13
slug: o-crud-completo
part: p4
kicker: "Don Juvenal preguntó si eso no era solo un CRUD. La respuesta tenía once ítems y estaba en el cuaderno de la pasante."
goal: >-
  Conectar rutas, controllers, models y base con las cinco operaciones
  devolviendo el status correcto, hacer que una operación de negocio quepa
  en un commit, y terminar sabiendo listar lo que todavía está mal.
---

:::story Solo un CRUD
La pantalla de registro de libros quedó lista el miércoles. Dedé la
mostró: listar, abrir, editar, borrar.

—Linda —dijo don Juvenal—. ¿Pero eso no es solo un CRUD?

Tainá dio vuelta el cuaderno hasta la página de la primera semana y leyó en
voz alta.

—Si es socia. Si no tiene libros atrasados. Si no debe una multa de más de
cinco reales. Si no tiene ya tres libros. Si el ejemplar no es de
referencia. Si no es el último ejemplar del título. Si es menor de doce, el
responsable firma. Si el libro llegó esta semana, queda en exhibición. Si
es período de exámenes, el plazo baja a siete. Si es de la colección del
señor, no sale. Y si es doña Marlene, sale.

Se detuvo.

—Once.

—Así es —dijo Dedé—. ¿En cuál de las cinco pantallas cabe eso?

Don Juvenal lo pensó un poco.

—En la de prestar.

—La de prestar no está ahí.
:::

:::art caption="El CRUD cabe en cinco pantallas. La regla de prestar, no."
src="o-crud-cabe-em-cinco-telas-a-regra-de-emprestar-nao.png"
Viñeta editorial minimalista sobre fondo blanco: una pizarra con cinco
cajas pequeñas y ordenadas, rotuladas "listar", "abrir", "crear", "editar"
y "borrar". Frente a la pizarra, una pasante lee en voz alta un cuaderno
abierto del que cae, hasta el suelo y por la sala, una tira de papel larga
como un rollo de recibo, llena de líneas que empiezan con "SI". Un señor de
gorra mira las cinco cajas y después la tira, rascándose la cabeza. Un
desarrollador, de brazos cruzados, señala el espacio vacío donde faltaría
una sexta caja. Pocos elementos, humor seco, estética de revista de
tecnología.
:::

## Las cinco rutas y lo que promete cada una

El CRUD del acervo son cinco operaciones, y su diseño se hizo en el
capítulo @cap:o-que-e-uma-api-rest. Ahora se vuelven código.

```php title="routes/api.php" numbered
Route::apiResource('libros', LibroController::class);
```

| Método | Ruta | Promete | Devuelve |
|---|---|---|---|
| `index` | `GET /libros` | la lista, paginada | `200` |
| `store` | `POST /libros` | crear uno nuevo | `201` + `Location` |
| `show` | `GET /libros/{libro}` | un ítem | `200` o `404` |
| `update` | `PUT/PATCH /libros/{libro}` | modificar | `200` o `404` |
| `destroy` | `DELETE /libros/{libro}` | quitar | `204` o `404` |

Tabla: Cinco líneas que cualquier persona que ya consumió una API puede
adivinar sin documentación. Es el valor entero de la convención.

## Crear

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

    $libro = Libro::create($datos);

    return response()
        ->json($libro, 201)
        ->header('Location', route('libros.show', $libro));
}
```

:::http title="La creación, de punta a punta"
POST /api/libros
Content-Type: application/json

{"titulo": "Vidas Secas", "autor": "Graciliano Ramos",
 "tema": "literatura", "anio": 1938}
---
201 Created
Location: /api/libros/4031
Content-Type: application/json

{
  "id": 4031,
  "titulo": "Vidas Secas",
  "autor": "Graciliano Ramos",
  "tema": "literatura",
  "anio": 1938,
  "created_at": "2026-01-21T14:02:55.000000Z"
}
:::

Hay tres decisiones en esas diez líneas.

**El recurso vuelve en el cuerpo.** El cliente acaba de crear algo y
necesita el `id` para continuar. Devolverlo vacío obligaría a una segunda
petición.

**El `Location` apunta a donde vive.** Es lo que le permite al cliente
consultarlo después sin armar la URL a mano.

**La validación está en el controller.** Funciona, y es lo primero que este
capítulo va a listar como problema al final.

## Leer uno: `404` es una respuesta

```php
public function show(Libro $libro)
{
    return $libro;
}
```

Dos líneas, y el `404` ya está tratado: el binding del capítulo
@cap:rotas-e-controllers busca el registro y se interrumpe antes de entrar
al método cuando no lo encuentra.

:::key
`404` no es una falla de la aplicación. Es la respuesta correcta a una
pregunta sobre algo que no existe.

La distinción importa en el monitoreo: un sistema que trata el `404` como
error llena el panel de alertas cada vez que alguien escribe mal una
dirección, y la alerta que importa se pierde en el medio.
:::

## `PUT` y `PATCH` no son lo mismo

El `apiResource` apunta los dos verbos al mismo método. La diferencia entre
ellos es tuya para implementar, e ignorarla produce un defecto específico.

**`PUT` reemplaza el recurso entero.** Lo que no venga en el cuerpo deja de
existir.

**`PATCH` modifica lo que vino.** Lo que no venga queda como estaba.

```text
PATCH /api/libros/4031
{"tema": "didactico"}
```

Si el método lo trata como `PUT`, el libro pierde el autor, el ISBN y el
año, porque no vinieron.

```php title="app/Http/Controllers/LibroController.php" numbered
public function update(Request $request, Libro $libro)
{
    $reglas = [
        'titulo' => ['string', 'max:200'],
        'autor' => ['string', 'max:150'],
        'tema' => ['string', 'max:40'],
        'isbn' => ['nullable', 'string', 'size:13'],
        'anio' => ['nullable', 'integer', 'min:1400'],
    ];

    if ($request->isMethod('PUT')) {
        $reglas['titulo'][] = 'required';
        $reglas['autor'][] = 'required';
        $reglas['tema'][] = 'required';
    }

    $libro->update($request->validate($reglas));

    return $libro;
}
```

Con `PUT`, los campos obligatorios vuelven a ser obligatorios: quien manda
el recurso entero tiene que mandarlo entero. Con `PATCH`, el `update` solo
toca lo que vino.

:::pitfall
La mayoría de las APIs implementan solo uno de los dos y aceptan los dos
verbos, lo que produce el peor resultado posible: el cliente lee en la
documentación que `PUT` reemplaza, manda un `PUT` parcial esperando que el
resto se borre, y el resto se queda.

Si vas a implementar uno solo, **implementa `PATCH` y rechaza `PUT`** con
`405`. Un rechazo claro es mejor que un verbo que miente.
:::

## Borrar

```php
public function destroy(Libro $libro)
{
    $libro->delete();

    return response()->noContent();
}
```

Cuatro líneas, y una pregunta detrás: **¿borrar de verdad?**

Un libro con historial de préstamos no debería desaparecer, por el motivo
del capítulo @cap:relacionamentos. Con `SoftDeletes`, el `delete()` de
arriba pasa a llenar `deleted_at`, y la respuesta `204` sigue siendo la
misma para quien llama.

El cliente no necesita saber la diferencia. La API promete que el recurso
sale de los listados, y cumple.

## Una operación de negocio, un `commit`

El préstamo no es una de las cinco. Escribe en dos lugares, y los dos
tienen que ocurrir juntos:

```php title="app/Http/Controllers/PrestamoController.php" numbered
public function store(Request $request)
{
    $datos = $request->validate([
        'ejemplar_id' => [
            'required', 'integer', 'exists:ejemplares,id',
        ],
        'lector_id' => [
            'required', 'integer', 'exists:lectores,id',
        ],
    ]);

    $prestamo = DB::transaction(function () use ($datos) {
        $ejemplar = Ejemplar::lockForUpdate()
            ->findOrFail($datos['ejemplar_id']);

        if ($ejemplar->condicion !== EstadoEjemplar::Bueno) {
            abort(409, 'Ejemplar no disponible');
        }

        $abiertos = Prestamo::abiertos()
            ->where('lector_id', $datos['lector_id'])
            ->count();

        if ($abiertos >= config('biblioteca.limite_por_lector')) {
            abort(409, 'Límite de préstamos alcanzado');
        }

        $prestamo = Prestamo::create([
            'ejemplar_id' => $ejemplar->id,
            'lector_id' => $datos['lector_id'],
            'retirado_en' => now(),
            'devolver_hasta' => now()->addDays(
                config('biblioteca.plazo_en_dias'),
            ),
        ]);

        $ejemplar->update(['condicion' => EstadoEjemplar::Prestado]);

        return $prestamo;
    });

    return response()
        ->json($prestamo, 201)
        ->header('Location', route('prestamos.show', $prestamo));
}
```

`DB::transaction` abre la transacción, ejecuta la función y confirma al
final. Si sube cualquier excepción —incluido el `abort`—, deshace todo y la
excepción sigue.

El `lockForUpdate()` es el `SELECT ... FOR UPDATE` del capítulo @cap:pdo,
escrito en Eloquent. Bloquea la fila del ejemplar hasta el final de la
transacción, y es lo que impide que Vera y Neide presten el mismo ejemplar
en el mismo segundo.

:::key
La regla de la transacción no es "cuántas consultas". Es: **¿cuántas de
estas escrituras tienen que ser verdad al mismo tiempo?**

Crear el préstamo sin cambiar el ejemplar produce un libro prestado que el
sistema cree disponible. Cambiar el ejemplar sin crear el préstamo produce
un libro no disponible que nadie se llevó. Las dos mitades solas son peores
que ninguna.
:::

## "Es solo un CRUD"

El acervo está en producción. Las cinco rutas funcionan, el préstamo
respeta dos reglas y la transacción cierra. Es un buen lugar para
detenerse y ser honesto sobre lo que este capítulo dejó mal, a propósito,
porque escribir primero la versión equivocada es la única forma de que la
corrección tenga sentido.

**La validación está en el controller.** Quince líneas de reglas en medio
de un método que debería tener tres. Y se repiten en el `store` y en el
`update`, con una diferencia que alguien se va a olvidar de sincronizar.

**La respuesta es el model crudo.** El JSON devuelto es el retrato de la
tabla: `created_at`, `updated_at`, `libro_id`. El día en que la columna
cambie de nombre, la aplicación publicada se rompe, y ni siquiera debería
saber que existen columnas.

**La regla de negocio está en el controller.** Dos de las once reglas de
Vera están ahí dentro, y no hay cómo probarlas sin levantar una petición.
Las otras nueve no están en ninguna parte.

**El error es una frase.** `abort(409, 'Ejemplar no disponible')` devuelve
texto. Quien consume no puede decidir nada sin leer la frase, y la frase
cambia.

**No hay autenticación.** Cualquier persona con la dirección crea un
préstamo a nombre de cualquier lector.

Cinco ítems. Ninguno es un accidente de escritura: cada uno es el tema de
una decisión que todavía no se tomó.

:::note En tu carrera
"Es solo un CRUD" se dice con frecuencia y casi siempre está mal, pero la
respuesta "no lo es" no convence a nadie.

Lo que convence es el cuaderno de Tainá: una lista de reglas reales,
dichas por quien hace el trabajo, y la pregunta de dónde va a vivir cada
una. Once reglas no caben en cinco pantallas, y cuando lo muestras en una
reunión, la conversación sobre el plazo cambia de tema sola.

El trabajo de relevar esa lista suele tocarte a ti, porque nadie más lo va
a hacer. Y es el trabajo que convierte una estimación en días en una
estimación en reglas, que es la única que sobrevive a la segunda semana.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Http/Controllers/
    LibroController.php       # las cinco operaciones
    EjemplarController.php
    PrestamoController.php    # con la regla adentro, por ahora
  app/Models/
    Libro.php                 # SoftDeletes
    Ejemplar.php
    Prestamo.php
  routes/api.php
:::

:::summary
- `apiResource` entrega cinco operaciones que cualquier consumidor adivina
  sin documentación.
- La creación devuelve `201`, el recurso en el cuerpo y el `Location`
  apuntando a él.
- `404` es una respuesta, no una falla; tratarlo como error ensucia el
  monitoreo.
- `PUT` reemplaza y `PATCH` modifica; los dos llegan al mismo método, y la
  diferencia es tuya para implementar.
- Implementar uno solo y aceptar los dos verbos es peor que rechazar uno
  con `405`.
- El borrado de una entidad con historial es lógico, y el cliente no
  necesita saberlo.
- `DB::transaction` confirma al final y deshace ante cualquier excepción;
  `lockForUpdate` bloquea la fila disputada.
- La regla de la transacción es cuántas escrituras tienen que ser verdad
  al mismo tiempo.
- El CRUD de este capítulo tiene cinco defectos con nombre, y ninguno es de
  tipeo.
:::

:::checkpoint
Entregas las cinco operaciones con los status correctos, sabes explicar la
diferencia entre `PUT` y `PATCH` por lo que pasa con los campos ausentes,
envuelves una operación de negocio en una transacción con la fila
bloqueada, y puedes listar por escrito lo que todavía está mal en lo que
acabas de entregar.
:::

:::exercise level=1
Para cada petición, di qué debe responder la API:

1. `POST /api/libros` sin el título.
2. `GET /api/libros/99999`, que no existe.
3. `DELETE /api/libros/4031`, que existe y tiene préstamos en el
   historial.
4. `PUT /api/libros/4031` solo con el campo `tema`.
5. `POST /api/prestamos` para un ejemplar ya prestado.

:::answer
1. `422`, con la lista de campos que fallaron. No es `400`: el JSON era
   correcto.
2. `404`, y el binding lo devuelve sin entrar al método.
3. `204`. El registro desaparece de los listados por borrado lógico, y el
   historial sigue. Quien llama no ve la diferencia.
4. `422`. `PUT` reemplaza el recurso entero, así que los campos
   obligatorios son obligatorios: mandar solo el `tema` es un pedido
   incompleto.
5. `409`. El pedido es correcto y el estado del sistema no lo permite. Es
   la diferencia del capítulo @cap:o-que-e-uma-api-rest entre contenido
   inválido y realidad incompatible.

El par que más se equivoca es el 4 y el 5. Los dos rechazan, y los dos
dicen cosas distintas: en el 4, el cliente corrige lo que mandó; en el 5,
recarga la pantalla porque otra persona se llevó el libro primero.
:::

:::exercise level=2
Escribe el `destroy` del `EjemplarController` con la regla: un ejemplar
prestado no se puede quitar.

Después responde: ¿por qué esa revisión **no** puede quedar en la pantalla,
y qué pasa si queda solo ahí?

:::answer
```php title="app/Http/Controllers/EjemplarController.php" numbered
public function destroy(Ejemplar $ejemplar)
{
    if ($ejemplar->condicion === EstadoEjemplar::Prestado) {
        abort(409, 'Un ejemplar prestado no se puede quitar');
    }

    $ejemplar->delete();

    return response()->noContent();
}
```

La revisión no puede quedar solo en la pantalla porque **la pantalla no es
el único camino hasta esa operación**. La misma ruta se alcanza con
`curl`, con la aplicación, con un script de importación y con cualquier
integración futura.

Si queda solo en la pantalla, el resultado es un ejemplar quitado con un
préstamo abierto: doña Marlene tiene el libro y el sistema no sabe a quién
cobrar. Y lo peor es que nadie lo va a descubrir en el momento: lo va a
descubrir en la revisión del inventario, meses después, con un número que
no cierra.

Es la misma idea del capítulo @cap:requests-e-responses sobre la validación
de formularios: el cliente revisa para ser amable, el servidor revisa
porque es el único que puede.
:::

:::exercise level=3
Este `update` pasó la revisión y está en producción hace dos semanas. Un
cliente informó que "a veces el libro pierde el autor".

```php
public function update(Request $request, Libro $libro)
{
    $libro->update($request->all());

    return $libro;
}
```

Explica qué pasa, por qué es intermitente, y escribe las tres correcciones
en orden de urgencia.

:::answer
**Qué pasa.** Son dos defectos que se combinan.

El `$request->all()` le entrega al `update` todo lo que vino. Si el
cliente manda `{"autor": null}` —lo que hace un formulario con el campo
vacío—, el autor queda en nulo. Y si manda campos que no existen en la
tabla, el `$fillable` los descarta en silencio, así que la mitad del pedido
desaparece sin aviso.

**Por qué es intermitente.** Depende de qué pantalla de la aplicación hizo
la llamada. La pantalla de edición completa manda todos los campos y
funciona; la pantalla rápida de cambiar el tema manda dos campos, y la
biblioteca de formularios de la aplicación incluye los campos vacíos como
`null`. Nadie reproduce el defecto probando desde la pantalla principal.

**Las tres correcciones, en orden.**

**Primera, hoy:** cambiar `all()` por el retorno de la validación, que solo
devuelve lo declarado.

```php
$datos = $request->validate([
    'titulo' => ['sometimes', 'required', 'string', 'max:200'],
    'autor' => ['sometimes', 'required', 'string', 'max:150'],
    'tema' => ['sometimes', 'required', 'string', 'max:40'],
]);

$libro->update($datos);
```

El `sometimes` es la pieza que hace funcionar el `PATCH`: la regla solo se
aplica si el campo **viene**. Un `autor` ausente se ignora; un `autor`
presente y nulo se rechaza con `422`.

**Segunda, esta semana:** distinguir `PUT` de `PATCH`, para que el verbo
signifique algo.

**Tercera, cuando se pueda:** una prueba que mande exactamente el cuerpo de
la pantalla rápida —dos campos y tres nulos— y compruebe que el autor sigue
ahí. Sin ella, la primera corrección desaparece en el próximo cambio de
este método.

Y una observación que no es una corrección: el defecto pasó la revisión
porque `update($request->all())` es una línea corta y familiar. El código
equivocado que parece limpio atraviesa más revisiones que el código
correcto y feo.
:::
