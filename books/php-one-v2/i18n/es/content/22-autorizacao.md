---
source_hash: 659960bc942e
title: "Autorización: Gates y Policies"
number: 22
slug: autorizacao
part: p5
kicker: "El lector llamó entusiasmado: había descubierto que, cambiando un número en la dirección, se podían ver los libros de todo el mundo."
goal: >-
  Responder "qué puedes hacer", incluso cuando el recurso es de otra
  persona: separar el rol del permiso, escribir Policies por recurso,
  restringir los listados según quién pregunta, y probar cada permiso,
  porque nadie los prueba a mano.
---

:::story El número en la dirección
El lector se llamaba Caio, tenía dieciséis años y hacía un curso técnico de
informática. Llamó un jueves, a las cinco de la tarde.

—Hola, es que encontré una cosa en la aplicación. No sé si tiene que ser
así.

Tainá lo puso en altavoz.

—En la pantalla de mis préstamos, si la abro desde el navegador, aparece en
la dirección `lector_id=212`. Que soy yo. Entonces lo cambié a 211.

—¿Y?

—Aparecieron los libros de doña Iolanda. Tiene tres. Uno es de recetas.
Entonces fui cambiando. Hay gente con libros atrasados desde noviembre.

Dedé, del otro lado de la mesa, ya tenía la ruta abierta.

```php
public function index(Request $request)
{
    return PrestamoResource::collection(
        Prestamo::where('lector_id', $request->lector_id)
            ->paginate(),
    );
}
```

—Caio —dijo Tainá—, ¿anotaste cuántos números probaste?

—Unos treinta. Me detuve porque pensé que podía dar problemas.

—Dio.

—¿Para mí?

—No. Para nosotros. Gracias por llamar.
:::

## La autenticación dice quién; la autorización dice qué

La ruta de Caio estaba detrás del `auth:sanctum`. Sabía exactamente quién
estaba preguntando: el lector 212, con un token válido. Y respondió sobre
el lector 211, porque el número vino del cliente y nadie revisó si quien
preguntaba tenía derecho a la respuesta.

Son dos preguntas, hechas en secuencia:

**Autenticación:** ¿quién eres? La responde el token. Si falla, `401`.

**Autorización:** ¿puedes hacer **esto**, con **esta cosa**? La responde
una regla. Si falla, `403`, o `404`, según el criterio del capítulo
@cap:erros-padronizados.

El capítulo anterior resolvió la primera. Esta es la segunda, y es más
difícil por un motivo: la autenticación es igual para toda la API, y la
autorización es **distinta para cada recurso**.

:::term Autorización a nivel de objeto
Revisar, para cada registro al que se accede, si quien pregunta tiene
derecho **a ese registro específico**, y no solo a ese tipo de registro.

La falla de eso tiene nombre en la lista de riesgos de API más citada del
mercado, y es su primer ítem: *Broken Object Level Authorization*. Es el
defecto de Caio: el lector tenía derecho a ver préstamos, y el sistema no
revisó **cuáles**.
:::

:::art caption="El sistema sabía quién estaba preguntando. No revisó lo que podía ver."
src="o-sistema-sabia-quem-estava-perguntando-nao-conferiu-o-que-ele-podia-ver.png"
Viñeta editorial minimalista sobre fondo blanco: un adolescente de buzo y
auriculares, sentado con el portátil en las rodillas, gira con el dedo un
pequeño selector numérico, como el de un candado, que cambia "212" por
"211". Con cada número, se abre una puerta distinta en una fila de puertas
idénticas al fondo, cada una con una pila de libros y el nombre de un
lector en la plaquita; detrás de una de ellas aparece un libro de recetas.
El adolescente, en lugar de entrar, toma el teléfono para avisar. Pocos
elementos, humor seco, estética de revista de tecnología.
:::

## Gate para la regla suelta, Policy para el recurso

Laravel ofrece dos lugares para escribir permisos.

**Gate** es una regla con nombre, suelta, que no pertenece a ningún model:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Gate::define(
        'ver-informes',
        fn (Usuario $u) => $u->rol !== Rol::Lector,
    );
}
```

```php
Gate::authorize('ver-informes');
```

**Policy** es una clase que reúne todos los permisos **sobre un tipo de
recurso**:

```text
$ php artisan make:policy PrestamoPolicy --model=Prestamo
```

```php title="app/Policies/PrestamoPolicy.php" numbered
<?php

declare(strict_types=1);

namespace App\Policies;

use App\Auth\Rol;
use App\Models\Prestamo;
use App\Models\Usuario;

class PrestamoPolicy
{
    public function view(Usuario $u, Prestamo $p): bool
    {
        return $this->esEquipo($u)
            || $p->lector_id === $u->lector_id;
    }

    public function create(Usuario $u): bool
    {
        return $this->esEquipo($u);
    }

    public function renovar(Usuario $u, Prestamo $p): bool
    {
        return $this->esEquipo($u)
            || $p->lector_id === $u->lector_id;
    }

    public function devolver(Usuario $u, Prestamo $p): bool
    {
        return $this->esEquipo($u);
    }

    private function esEquipo(Usuario $u): bool
    {
        return in_array(
            $u->rol,
            [Rol::Encargado, Rol::Admin],
            true,
        );
    }
}
```

Cada método es una pregunta: ¿puede ver este? ¿Puede crear? ¿Puede renovar
este? Los que reciben el `Prestamo` son sobre **un registro**; el `create`
no lo recibe, porque el registro todavía no existe.

Laravel encuentra la policy solo por el nombre: `Prestamo` →
`PrestamoPolicy`, en la carpeta `app/Policies`. Nada que registrar.

Fíjate en el `create`. El lector **no** puede crear un préstamo por la API:
quien presta es el mostrador, con el libro en la mano. La aplicación
muestra el acervo, reserva, renueva. Es una decisión de Vera que el
capítulo @cap:o-que-e-uma-api-rest no tenía cómo saber, y que la policy
registra en una línea.

## `authorize`, `can` y el `403` que sale solo

En el controller:

```php title="app/Http/Controllers/PrestamoController.php" numbered
public function show(Prestamo $prestamo)
{
    Gate::authorize('view', $prestamo);

    return new PrestamoResource($prestamo);
}
```

`Gate::authorize` llama al método `view` de la policy de `Prestamo` con el
usuario autenticado. Si devuelve `false`, lanza `AuthorizationException`,
que el handler del capítulo @cap:erros-padronizados convierte en `403`.

Existe la forma que pregunta sin lanzar, para cuando la respuesta cambia el
comportamiento en lugar de interrumpir:

```php
if ($request->user()->can('renovar', $prestamo)) {
    // muestra el botón
}
```

Y el Form Request tiene el `authorize()` que el capítulo
@cap:validation-e-form-requests dejó en `true`, con una deuda anotada:

```php title="app/Http/Requests/RealizarPrestamoRequest.php" numbered
public function authorize(): bool
{
    return $this->user()->can('create', Prestamo::class);
}
```

Para el `create`, que no tiene registro, se pasa la **clase**, y Laravel
sabe qué policy usar por ella.

Deuda pagada. Y con una ventaja de orden: el `authorize()` corre **antes**
de las reglas de validación. Quien no tiene permiso recibe `403` sin
descubrir qué campos espera la ruta.

## ¿El recurso es suyo?

La corrección de la ruta de Caio tiene dos partes, porque la ruta tenía dos
defectos.

El primero es la pregunta sobre **un registro**, y la policy lo resuelve:
`GET /prestamos/312` pasa a revisar si el 312 es del lector.

El segundo es más sutil. El listado `GET /prestamos?lector_id=211`
aceptaba un **filtro** que venía del cliente, y el filtro decidía de quién
eran los datos. La policy no ayuda aquí: no hay un registro sobre el que
preguntar, hay una consulta.

:::key
En el listado, quien decide el alcance es el servidor, a partir de quién
está autenticado. **Nunca** un parámetro.

El `lector_id` que viene del cliente puede ser un filtro más —para que la
bibliotecaria elija de qué lector ver—, pero solo después de que la
consulta ya esté restringida a lo que quien pregunta tiene derecho a ver.
:::

## Listado con alcance

```php title="app/Models/Prestamo.php" numbered
public function scopeVisiblePara(Builder $q, Usuario $u): void
{
    if ($u->rol === Rol::Lector) {
        $q->where('lector_id', $u->lector_id);
    }
}
```

```php title="app/Http/Controllers/PrestamoController.php" numbered
public function index(ListarPrestamosRequest $request)
{
    $prestamos = Prestamo::visiblePara($request->user())
        ->when(
            $request->filled('lector_id'),
            fn ($q) => $q->where(
                'lector_id',
                $request->integer('lector_id'),
            ),
        )
        ->with('ejemplar.libro')
        ->orderByDesc('retirado_en')
        ->orderByDesc('id')
        ->cursorPaginate(20);

    return PrestamoResource::collection($prestamos);
}
```

El orden de las dos restricciones es el punto. El `visiblePara` va
**primero** y restringe al lector autenticado. El filtro de `lector_id` va
**después**, y para un lector común solo puede estrechar lo que ya estaba
restringido. Caio pidiendo `?lector_id=211` recibe:

```sql
WHERE lector_id = 212 AND lector_id = 211
```

Una lista vacía. No un error, no una confirmación de que el 211 existe:
nada. La bibliotecaria, sin la primera restricción, recibe los préstamos
del 211.

:::pitfall
El alcance tiene que estar en **toda** consulta que devuelve datos del
lector, y eso incluye las que nadie llama listado: la exportación en CSV,
la búsqueda por registro, el contador de "tienes tres libros" en la
cabecera, el endpoint de estadísticas.

El defecto de Caio suele volver por una de esas puertas secundarias, meses
después, en una ruta nueva que alguien escribió copiando la consulta sin el
`visiblePara`. Por eso existe la prueba del final del capítulo, y por eso
hay que escribirla para toda ruta nueva, no solo para las que parecen
sensibles.
:::

## `before`: el admin, y el cuidado con él

Una policy puede tener un método que corre antes que todos los demás:

```php title="app/Policies/LibroPolicy.php" numbered
class LibroPolicy
{
    public function before(Usuario $u, string $habilidad): ?bool
    {
        return $u->rol === Rol::Admin ? true : null;
    }

    public function create(Usuario $u): bool
    {
        return $u->rol === Rol::Encargado;
    }

    public function update(Usuario $u, Libro $libro): bool
    {
        return $u->rol === Rol::Encargado;
    }

    public function delete(Usuario $u, Libro $libro): bool
    {
        return false;
    }
}
```

`before` devolviendo `true` libera todo; devolviendo `null`, deja que
decida el método específico. El admin puede todo sobre los libros; el
encargado registra y edita; nadie más borra.

El `before` es cómodo y es un lugar donde las reglas desaparecen. Si mañana
Vera dice que ni el admin puede borrar un libro con un préstamo abierto,
esa regla **no puede** vivir en el `delete`: el `before` libera antes de
que se consulte el `delete`. O el `before` recibe una excepción, o la regla
va al service. Es el tipo de cosa que tiene que estar escrita en el propio
archivo, en un comentario corto, para que la siguiente persona no caiga.

## El rol no es un permiso

Las policies de arriba preguntan directamente por el **rol**:
`Rol::Encargado`, `Rol::Admin`. Funciona con tres roles, y envejece mal
por un motivo previsible: el día en que la Casa Amarela contrate a una
voluntaria que puede registrar libros y **no** puede ver el documento de
los lectores.

La voluntaria no es encargada ni lectora. Un cuarto rol obliga a revisar
todas las policies, buscando cada `Rol::Encargado` y decidiendo si vale
para ella.

La separación que envejece bien: el rol es una **colección de permisos**, y
las policies preguntan por el permiso.

```php title="app/Auth/Rol.php" numbered
enum Rol: string
{
    case Lector = 'lector';
    case Encargado = 'encargado';
    case Admin = 'admin';

    public function permite(Permiso $p): bool
    {
        return in_array($p, $this->permisos(), true);
    }

    /** @return list<Permiso> */
    public function permisos(): array
    {
        return match ($this) {
            self::Lector => [],
            self::Encargado => [
                Permiso::RegistrarAcervo,
                Permiso::VerDatosDeLector,
                Permiso::RegistrarCirculacion,
            ],
            self::Admin => Permiso::cases(),
        };
    }
}
```

```php
public function create(Usuario $u): bool
{
    return $u->rol->permite(Permiso::RegistrarAcervo);
}
```

La voluntaria se vuelve un caso nuevo en el enum, con su lista. Ninguna
policy cambia. El `match` del capítulo @cap:enums-datas-e-valores garantiza
que el caso nuevo no queda sin lista: sin la línea, la llamada lanza
`UnhandledMatchError`.

Y el `habilidades()` que llamaba el `createToken` del capítulo anterior
viene de aquí: son los nombres de los permisos, grabados en el token. Un
token de lector no lleva `registrar-circulacion`, y el `tokenCan` puede
revisarlo incluso antes de consultar el rol.

:::pitfall
Grabar el rol o las habilidades **en el token** tiene un costo: el token se
emite al iniciar sesión y dura treinta días. Si Vera le quita el permiso a
un encargado el lunes, su token sigue con las habilidades viejas hasta que
vence.

Dos salidas, y las dos se usan juntas. La policy revisa el rol **actual**
en la base —`$u->rol` se lee en cada petición—, y el token es solo una
segunda restricción. Y cambiar el rol de alguien revoca los tokens de esa
persona, como el cambio de contraseña del capítulo anterior.
:::

## Probar los permisos es obligatorio

Nadie prueba los permisos a mano, porque probarlos a mano exige tres
cuentas, dos roles y la paciencia de cambiar de sesión en cada intento.
Caio lo probó porque tenía dieciséis años y una tarde libre.

La suite del capítulo @cap:testes-de-feature-http-e-banco se ocupa de eso
en detalle. El formato ya cabe aquí:

```php title="tests/Feature/PrestamoAutorizacionTest.php" numbered
test('el lector no ve el préstamo de otro lector', function () {
    $caio = Usuario::factory()->lector()->create();
    $iolanda = Lector::factory()->create();
    $ajeno = Prestamo::factory()
        ->for($iolanda)
        ->create();

    $this->actingAs($caio)
        ->getJson("/api/prestamos/{$ajeno->id}")
        ->assertForbidden();
});

test('el filtro de lector no amplía el alcance', function () {
    $caio = Usuario::factory()->lector()->create();
    Prestamo::factory()->count(3)->create();

    $this->actingAs($caio)
        ->getJson('/api/prestamos?lector_id=211')
        ->assertOk()
        ->assertJsonCount(0, 'data');
});
```

Dos pruebas, y las dos reproducen lo que hizo Caio. Si alguien, dentro de
seis meses, reescribe el listado y se olvida del `visiblePara`, la
integración queda en rojo antes de que se publique la aplicación.

:::note En tu carrera
La autorización a nivel de objeto es el defecto de seguridad más común en
una API, y el más fácil de explicar a quien no es técnico: "cambiando el
número en la dirección, se puede ver el dato de otra persona".

Cuando hagas una revisión de código en una ruta que recibe un
identificador, haz dos preguntas, siempre: **¿quién garantiza que ese
registro es de quien pregunta?** y **¿quién garantiza que esa lista solo
tiene lo que puede ver?** Si la respuesta es "la aplicación solo muestra
los suyos", la ruta está abierta: la aplicación es el único cliente que no
va a probar otro número.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Auth/
    Rol.php                     # rol → lista de permisos
    Permiso.php                 # enum
  app/Policies/
    PrestamoPolicy.php          # ver y renovar solo los propios
    LibroPolicy.php             # el encargado registra, nadie borra
    LectorPolicy.php
  app/Models/
    Prestamo.php                # scopeVisiblePara
  tests/Feature/
    PrestamoAutorizacionTest.php
:::

:::milestone
Fin de la Parte 5. La regla de préstamo vive en un service que Vera puede
leer; la API sabe quién está preguntando, guarda las contraseñas de la
forma correcta, revoca los tokens en el acto; y cada recurso revisa si
quien pide tiene derecho a ese registro, con una prueba para el número
cambiado en la dirección.

En el cuaderno de Tainá: *"la aplicación es el único cliente que no va a
cambiar el número"*.
:::

:::summary
- La autenticación responde quién eres (`401`); la autorización, qué
  puedes hacer con esta cosa (`403`).
- La autorización a nivel de objeto revisa el registro, no solo el tipo; su
  falla es el primer riesgo de una API.
- El Gate es una regla suelta con nombre; la Policy reúne los permisos de
  un recurso y se descubre por el nombre.
- `Gate::authorize` lanza y se vuelve `403`; `can` pregunta sin lanzar; el
  `authorize()` del Form Request corre antes de la validación.
- El listado se restringe por el usuario autenticado, en el servidor; un
  parámetro del cliente solo estrecha.
- `before` libera antes del método específico, y una regla que vale
  incluso para el admin no puede vivir después de él.
- El rol es una colección de permisos; las policies preguntan por el
  permiso.
- La habilidad grabada en el token envejece; la policy revisa el rol
  actual, y cambiar el rol revoca los tokens.
- Los permisos se prueban con una prueba para cada caso, porque nadie los
  prueba a mano.
:::

:::checkpoint
El lector ve y renueva solo sus propios préstamos, el encargado registra y
el admin administra, todo listado se restringe según quién pregunta antes
de cualquier filtro, y existe una prueba para el número cambiado en la
dirección, y otra para el filtro que intenta ampliar el alcance.
:::

:::exercise level=1
Para cada petición, di el status esperado y qué mecanismo lo produce:

1. El lector 212 pide `GET /prestamos/900`, que es del lector 211.
2. El lector 212 pide `POST /prestamos`.
3. El encargado pide `DELETE /libros/12`.
4. Una petición sin token pide `GET /yo`.
5. El lector 212 pide `GET /prestamos?lector_id=211`.

:::answer
1. `403`, por la `PrestamoPolicy::view` llamada en el `show`, o `404`, si
   el equipo decide que la existencia de un préstamo ajeno no debe
   confirmarse.
2. `403`, por el `authorize()` del `RealizarPrestamoRequest`, antes de
   cualquier validación.
3. `403`, por la `LibroPolicy::delete`, que devuelve `false`: el `before` no
   libera, porque no es admin.
4. `401`, por el `auth:sanctum`, antes de llegar a cualquier policy.
5. `200` con una lista vacía, por el `scopeVisiblePara`. No es `403`: la
   pregunta está permitida, y la respuesta es que no hay nada que pueda ver
   ahí.

El ítem 5 suele responderse como `403`. La diferencia importa: un `403` le
diría a Caio que el filtro se entendió y se rechazó; la lista vacía no dice
nada.
:::

:::exercise level=2
Escribe la `LectorPolicy` con las reglas: el lector ve y edita solo su
propio registro; el equipo ve a todos; solo el equipo edita el perfil de
otro lector; el documento solo lo puede cambiar el admin. Y escribe cómo el
`UpdateLectorRequest` usa la policy para el campo documento.

:::answer
```php title="app/Policies/LectorPolicy.php" numbered
class LectorPolicy
{
    public function view(Usuario $u, Lector $l): bool
    {
        return $u->lector_id === $l->id
            || $u->rol->permite(Permiso::VerDatosDeLector);
    }

    public function update(Usuario $u, Lector $l): bool
    {
        return $u->lector_id === $l->id
            || $u->rol->permite(Permiso::VerDatosDeLector);
    }

    public function cambiarDocumento(Usuario $u, Lector $l): bool
    {
        return $u->rol === Rol::Admin;
    }
}
```

```php title="app/Http/Requests/UpdateLectorRequest.php" numbered
public function authorize(): bool
{
    $lector = $this->route('lector');

    if (!$this->user()->can('update', $lector)) {
        return false;
    }

    return !$this->has('documento')
        || $this->user()->can('cambiarDocumento', $lector);
}
```

El `cambiarDocumento` es una habilidad que no corresponde a ninguna ruta:
es un permiso sobre **un campo**. La policy acepta métodos con cualquier
nombre, y así es como los permisos más finos que el CRUD encuentran su
lugar.

Una alternativa sería aceptar el pedido e ignorar el documento en silencio
para quien no es admin. Es peor: el cliente cree que lo cambió y no lo
cambió. El rechazo explícito dice lo que pasó.
:::

:::exercise level=3
El informe "lectores con más de treinta días de atraso" existe en el panel,
para el equipo. Una persona del equipo lo va a exponer en la API para una
futura aplicación del equipo, en `GET /informes/atrasados`.

Enumera todo lo que hay que decidir y proteger antes de publicar la ruta, y
escribe la prueba que exigirías en la revisión.

:::answer
**Decisiones y protecciones:**

**Quién puede.** Un Gate `ver-informes` o un permiso `VerInformes`, no
"cualquiera del equipo" por rol directo: la futura voluntaria
probablemente no debe ver quién está debiendo.

**Qué sale.** El informe del panel muestra nombre, teléfono y títulos. En
la API, un `InformeDeAtrasoResource` decide campo por campo. El documento
no sale. El teléfono sale solo si la aplicación va a llamar a las personas,
y entonces es una decisión de Vera, no del equipo.

**Techo y paginación.** Es una lista de personas. Sin techo, es una
exportación de la base de deudores en una petición.

**Registro de acceso.** Quién consultó y cuándo va al log, con el
incidente. Es un dato personal sensible —una deuda— y la asociación tiene
que poder responder quién lo vio.

**Token.** Un token de lector no puede tener la habilidad, aunque la policy
esté bien: las dos capas.

**La prueba que exigiría:**

```php
test('solo quien tiene permiso ve el informe', function (
    Rol $rol,
    int $status,
) {
    $u = Usuario::factory()->conRol($rol)->create();

    $this->actingAs($u)
        ->getJson('/api/informes/atrasados')
        ->assertStatus($status);
})->with([
    'lector' => [Rol::Lector, 403],
    'encargado' => [Rol::Encargado, 200],
    'admin' => [Rol::Admin, 200],
]);
```

Una más, revisando que `documento` no aparece en ningún ítem de la
respuesta. Y, cuando se cree la voluntaria, su línea entra en ese `with`, y
la prueba obliga a alguien a decidir el status esperado.
:::
