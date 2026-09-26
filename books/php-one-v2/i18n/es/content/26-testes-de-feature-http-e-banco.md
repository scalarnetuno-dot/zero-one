---
source_hash: 90fd81b7fe75
title: "Pruebas de feature, HTTP y base de datos"
number: 26
slug: testes-de-feature-http-e-banco
part: p7
kicker: "La cadena estuvo en rojo tres días por una prueba que pasaba en todas las máquinas locales. Faltaba un ORDER BY, en la prueba y en el código."
goal: >-
  Verificar el contrato de la API de punta a punta y las garantías que solo
  da la base: peticiones reales contra rutas reales, base aislada en cada
  prueba, permisos demostrados por el lado del rechazo, y fakes de
  infraestructura que no esconden lo que deberían probar.
---

:::story Tres días en rojo
La cadena se puso en rojo un lunes por la tarde, en una prueba que nadie
había tocado.

```text
FAILED  Tests\Feature\PrestamoListadoTest
  > lista los préstamos del lector
  Failed asserting that '2117' is identical to '2118'.
```

Tainá la corrió en su máquina: verde. Dedé la corrió: verde. Cléber la
corrió tres veces seguidas: verde, verde, verde.

—Es la cadena —dijo Cléber—. Debe ser la caché.

Limpiaron la caché de la cadena. Rojo. La corrieron otra vez sin cambiar
nada. Verde. Otra vez. Rojo.

El martes, alguien sugirió marcar la prueba como "inestable" y seguir
adelante. Tainá no lo permitió, y no supo explicar por qué: solo le pareció
que una prueba que a veces falla estaba intentando decir algo.

El miércoles, leyó la prueba línea por línea, con el código del listado
abierto al lado.

```php
$this->getJson('/api/prestamos')
    ->assertJsonPath('data.0.ejemplar.registro', 2117);
```

—¿Por qué el primero tiene que ser el 2117? —preguntó.

—Porque fue el primero que creó la prueba —dijo Dedé.

—¿Y el listado ordena por qué?

Dedé abrió el controller. Ordenaba por `retirado_en`, descendente. Y la
factory creaba los tres préstamos de la prueba en el mismo segundo.

—Tres préstamos con la misma fecha —dijo Tainá—. Sin desempate.

—En nuestras máquinas, MySQL devuelve en orden de inserción.

—¿Y en la cadena?

—En la cadena, MySQL corre con otra configuración de memoria.
:::

## `getJson`, `postJson` y el contrato verificado

El capítulo anterior probó la regla aislada: una función recibe valores y
decide. Pero la regla aislada no demuestra que la API funcione. Entre la
petición de la aplicación y la política de préstamo están la ruta, el
middleware, el Form Request, la policy, el service, la transacción, el
resource y el handler de errores, y cualquiera de ellos puede estar mal
conectado.

La prueba de feature hace el camino entero. Manda una petición de verdad a
la aplicación, sin servidor web de por medio, y verifica la respuesta:

```php title="tests/Feature/LibroTest.php" numbered
test('crea un libro y devuelve 201 con Location', function () {
    $encargado = Usuario::factory()->encargado()->create();

    $respuesta = $this->actingAs($encargado)
        ->postJson('/api/libros', [
            'titulo' => 'Vidas secas',
            'autor' => 'Graciliano Ramos',
            'tema' => 'literatura',
            'isbn' => '978-85-01-00032-5',
        ]);

    $respuesta->assertCreated()
        ->assertHeader('Location')
        ->assertJsonPath('data.titulo', 'Vidas secas')
        ->assertJsonPath('data.isbn', '9788501000325');
});
```

`postJson` arma la petición con los encabezados de JSON, se la entrega al
kernel de Laravel y devuelve la respuesta como objeto. Las afirmaciones que
siguen verifican el **contrato**: el status, el encabezado, y dos campos
del cuerpo; uno de ellos, el ISBN, ya normalizado por el
`prepareForValidation` del capítulo @cap:validation-e-form-requests.

Las afirmaciones más usadas:

| Afirmación | Verifica |
|---|---|
| `assertCreated()`, `assertOk()`, `assertNoContent()` | el status |
| `assertJsonPath('data.titulo', 'x')` | un campo, por la ruta |
| `assertJsonStructure([...])` | que las claves existen |
| `assertJsonValidationErrors(['isbn'])` | el `422` y el campo culpable |
| `assertJsonMissingPath('data.x')` | que una clave **no** está |

Tabla: La última es la menos usada y la más importante de las cinco. Es la
que garantiza que lo que no puede salir sigue sin salir.

## `RefreshDatabase`: aislamiento sin `TRUNCATE`

Una prueba de feature usa una base de verdad. Y cada prueba tiene que
empezar con la base en un estado conocido, o el resultado de una depende de
lo que la otra dejó atrás.

```php title="tests/Pest.php" numbered
pest()->extend(Tests\TestCase::class)
    ->use(Illuminate\Foundation\Testing\RefreshDatabase::class)
    ->in('Feature');
```

`RefreshDatabase` hace dos cosas. La primera vez que corre la suite,
ejecuta todas las migrations en una base de pruebas vacía. Después, **cada
prueba corre dentro de una transacción que se deshace al final**. Nada de
lo que la prueba grabó la sobrevive.

Es rápido —deshacer una transacción no cuesta casi nada— y tiene una
consecuencia: dentro de la prueba, todo ocurre en una sola transacción. El
`DB::transaction` del `PrestamoService` se vuelve una transacción
**anidada**, y Laravel la simula con *savepoints*. Funciona para casi todo.
No funciona para probar dos conexiones disputándose la misma fila, porque
las dos verían la misma transacción externa.

La base de pruebas es **otra base**, configurada en el `phpunit.xml`:

```xml title="phpunit.xml" numbered
<env name="APP_ENV" value="testing"/>
<env name="DB_DATABASE" value="casa_amarela_prueba"/>
<env name="QUEUE_CONNECTION" value="sync"/>
<env name="CACHE_STORE" value="array"/>
```

:::warning
`RefreshDatabase` borra la base en la primera ejecución. Si el `.env` de
pruebas apunta a la base de desarrollo —o, como el jueves del capítulo
@cap:migrations-seeders-e-factories, a la de producción—, borra la base
equivocada.

El `phpunit.xml` con `DB_DATABASE` explícito es la protección. Y vale una
verificación más en el `TestCase`: si el nombre de la base no termina en
`_prueba`, la prueba se niega a correr.
:::

### SQLite en memoria, y dónde miente

Muchos proyectos corren las pruebas en SQLite en memoria, porque es más
rápido y no necesita servidor:

```xml
<env name="DB_CONNECTION" value="sqlite"/>
<env name="DB_DATABASE" value=":memory:"/>
```

Y SQLite no es MySQL. Las diferencias que ya atravesaron este libro:

- la collation `utf8mb4_0900_ai_ci` del capítulo
  @cap:paginacao-filtros-e-buscas no existe; la búsqueda sin tildes pasa en
  uno y falla en el otro;
- SQLite acepta texto en una columna `INTEGER` sin quejarse;
- `lockForUpdate` se ignora: no hay bloqueo de fila;
- no se verifica el tamaño de `VARCHAR(200)`.

Una prueba que pasa en SQLite y falla en el MySQL de producción es peor
que una prueba lenta, porque da la certeza equivocada. La Casa Amarela
corre las pruebas en el **mismo MySQL** de producción, en la misma versión.
La cadena del capítulo @cap:git-ci-e-deploy levanta un MySQL de servicio
para eso, y cuesta algunos segundos por ejecución.

## `actingAs` y la prueba de ruta protegida

Las rutas de la API están detrás de `auth:sanctum`. La prueba no necesita
hacer login y guardar un token:

```php
$this->actingAs($usuario)->getJson('/api/yo');
```

`actingAs` le dice a Laravel que las peticiones siguientes vienen de ese
usuario. Para probar las habilidades del token, Sanctum tiene su propia
forma:

```php
Sanctum::actingAs($usuario, ['ver-acervo']);
```

Y la prueba de que la ruta **está** protegida es la más simple de todas, y
tiene que existir para cada grupo:

```php title="tests/Feature/ProteccionTest.php" numbered
test('las rutas del lector exigen autenticación', function (
    string $metodo,
    string $ruta,
) {
    $this->json($metodo, $ruta)->assertUnauthorized();
})->with([
    ['GET', '/api/yo'],
    ['GET', '/api/prestamos'],
    ['POST', '/api/prestamos/1/renovacion'],
    ['POST', '/api/reservas'],
]);
```

Si alguien saca una ruta del grupo protegido, por error, al reorganizar el
archivo de rutas, esta prueba lo señala.

## Probar el `403` es probar lo que nadie prueba a mano

El capítulo @cap:autorizacao terminó con dos pruebas del caso Caio. La
suite completa sigue el mismo molde para cada recurso, y el molde tiene
tres preguntas:

1. ¿El dueño puede?
2. ¿Otro usuario del mismo rol **no** puede?
3. ¿El equipo puede?

```php title="tests/Feature/PrestamoAutorizacionTest.php" numbered
beforeEach(function () {
    $this->dueno = Usuario::factory()->lector()->create();
    $this->otro = Usuario::factory()->lector()->create();
    $this->encargado = Usuario::factory()->encargado()->create();

    $this->prestamo = Prestamo::factory()
        ->for($this->dueno->lector)
        ->create();
});

test('el dueño ve su propio préstamo', function () {
    $this->actingAs($this->dueno)
        ->getJson("/api/prestamos/{$this->prestamo->id}")
        ->assertOk();
});

test('otro lector no lo ve', function () {
    $this->actingAs($this->otro)
        ->getJson("/api/prestamos/{$this->prestamo->id}")
        ->assertForbidden();
});

test('el encargado lo ve', function () {
    $this->actingAs($this->encargado)
        ->getJson("/api/prestamos/{$this->prestamo->id}")
        ->assertOk();
});
```

La segunda es la que importa. Las otras dos casi siempre pasan, porque el
camino feliz es el que la persona probó en pantalla mientras desarrollaba.
La segunda solo pasa si alguien se acordó de escribir la policy.

## El campo que nunca puede aparecer

El capítulo @cap:api-resources prometió una prueba para la
`observacion_interna`. Es corta y protege contra toda una categoría de
defectos:

```php title="tests/Feature/CamposInternosTest.php" numbered
test('la observación interna nunca sale por la API', function (
    string $ruta,
) {
    $lector = Lector::factory()->create([
        'observacion_interna' => 'SECRETO-DE-PRUEBA',
    ]);
    $admin = Usuario::factory()->admin()->create();

    $cuerpo = $this->actingAs($admin)
        ->getJson(str_replace('{id}', $lector->id, $ruta))
        ->assertOk()
        ->getContent();

    expect($cuerpo)->not->toContain('SECRETO-DE-PRUEBA');
})->with([
    '/api/lectores/{id}',
    '/api/lectores?busqueda=',
    '/api/lectores/{id}/prestamos',
]);
```

Tres detalles de diseño.

La prueba usa al **admin**, que es quien ve más. Si ni el admin recibe la
observación por la API, nadie la recibe.

Busca el **valor**, no la clave. `assertJsonMissingPath` verificaría que
no hay una clave `observacion_interna`, y dejaría pasar el día en que
alguien la expusiera con otro nombre: `notas`, `obs`.

Y el valor es una marca inconfundible. Un texto común como "lo devuelve
mojado" podría aparecer por otro motivo; `SECRETO-DE-PRUEBA`, no.

## `assertDatabaseHas` y lo que demuestra

El flujo de préstamo necesita una prueba que verifique la base, porque la
promesa del service es sobre la base: dos grabaciones, juntas:

```php title="tests/Feature/PrestamoFlujoTest.php" numbered
test('el préstamo graba y bloquea el ejemplar juntos', function () {
    $ejemplar = Ejemplar::factory()->disponible()->create();
    $lector = Lector::factory()->alDia()->create();
    $encargado = Usuario::factory()->encargado()->create();

    $this->actingAs($encargado)
        ->postJson('/api/prestamos', [
            'ejemplar_id' => $ejemplar->id,
            'lector_id' => $lector->id,
        ])
        ->assertCreated();

    $this->assertDatabaseHas('prestamos', [
        'ejemplar_id' => $ejemplar->id,
        'lector_id' => $lector->id,
        'devuelto_en' => null,
    ]);

    expect($ejemplar->fresh()->condicion)
        ->toBe(EstadoEjemplar::Prestado);
});
```

`assertDatabaseHas` busca una fila con esos valores. Demuestra que la fila
**existe**, y no demuestra que sea la única: un defecto que grabara el
préstamo dos veces pasaría. Cuando eso importa, `assertDatabaseCount` lo
completa.

Y la prueba de la transacción deshecha, que es el otro lado de la misma
promesa:

```php
test('un ejemplar no disponible no graba nada', function () {
    $ejemplar = Ejemplar::factory()->prestado()->create();
    $lector = Lector::factory()->alDia()->create();

    $this->actingAs(Usuario::factory()->encargado()->create())
        ->postJson('/api/prestamos', [
            'ejemplar_id' => $ejemplar->id,
            'lector_id' => $lector->id,
        ])
        ->assertConflict()
        ->assertJsonPath('tipo', 'ejemplar-no-disponible');

    $this->assertDatabaseCount('prestamos', 1);
});
```

El `1` es el préstamo que la factory `prestado()` ya creó. Ninguno nuevo.

Fíjate en lo que esta prueba **no** hace: verificar las once condiciones.
Se demostraron en la unitaria, en catorce centésimas de segundo. Aquí basta
un `409` para demostrar que la excepción de dominio atraviesa el controller
y llega al handler en el formato correcto. Repetir las once aquí costaría
dos segundos y no demostraría nada nuevo.

## Fake de cola, e-mail y evento

El flujo de préstamo dispara `PrestamoRealizado`, que manda un job a la
cola, que llama al enviador. La prueba de feature quiere demostrar el
primer eslabón, y no necesita ejecutar los demás:

```php
test('el préstamo anuncia el evento', function () {
    Event::fake([PrestamoRealizado::class]);

    // ... el POST del préstamo ...

    Event::assertDispatched(
        PrestamoRealizado::class,
        fn ($e) => $e->prestamo->lector_id === $lector->id,
    );
});
```

`Event::fake` cambia el despachador de eventos por uno que solo anota.
Existen los hermanos —`Queue::fake`, `Mail::fake`, `Notification::fake`,
`Storage::fake`—, y todos siguen el molde del fake del capítulo
@cap:testes: verificar lo que pasó, sin ejecutar.

:::pitfall
`Queue::fake` verifica que el job se **encoló**. No ejecuta el job, y por
eso un job que se rompería en la primera línea pasa todas las pruebas que
usan el fake.

La suite necesita al menos una prueba que **ejecute** cada job de verdad,
con el enviador falso inyectado:

```php
test('el aviso de víspera se envía una sola vez', function () {
    $falso = new EnviadorFalso();
    $this->app->instance(EnviadorDeAviso::class, $falso);
    $p = Prestamo::factory()->venceManana()->create();

    (new AvisarDevolucionProxima($p->id))->handle($falso);
    (new AvisarDevolucionProxima($p->id))->handle($falso);

    expect($falso->enviados)->toHaveCount(1);
});
```

Es la prueba de doña Iolanda: el job corriendo dos veces, y un solo
mensaje.
:::

## Suite lenta: diagnosticar antes de culpar a la base

La suite de la Casa Amarela tiene trescientas pruebas y tarda cuarenta
segundos. Antes de cambiar MySQL por SQLite, la pregunta del capítulo
@cap:cache-logs-e-medicao: **¿dónde está el tiempo?**

```text
$ php artisan test --profile

  Top 10 slowest tests:
  PrestamoListadoTest > pagina 500 préstamos          8.21s
  InformeTest > informe anual completo                6.03s
  ...
```

Dos pruebas suman catorce de los cuarenta segundos. La primera crea
quinientos préstamos con la factory —cada uno creando su propio lector,
ejemplar y libro, dos mil grabaciones— para probar una paginación de
veinte. Con cincuenta préstamos del mismo lector, la paginación queda
demostrada igual.

Después de arreglar las lentas, lo que queda se reparte:

```text
$ php artisan test --parallel
```

`--parallel` corre las pruebas en varios procesos, cada uno con su base de
pruebas. En una máquina con ocho núcleos, los cuarenta segundos se vuelven
ocho.

:::key
¿Cuánto puede tardar la suite? La respuesta práctica: **el tiempo que
alguien acepta esperar antes de cada commit**. Si pasa de eso, la gente
deja de correrla localmente, y la cadena se vuelve el primer lugar donde
corre la prueba, que es tarde.

Para un proyecto del tamaño de la Casa Amarela, menos de un minuto. La
unitaria en menos de un segundo, para correrla cada vez que se guarda el
archivo.
:::

## La corrección de la cadena en rojo

Volviendo a la historia: la prueba esperaba el 2117 primero porque quien la
escribió vio el 2117 primero en su máquina. El listado ordenaba por
`retirado_en`, y los tres préstamos de la prueba tenían el mismo valor. Sin
desempate, el orden entre ellos lo decidía la base, y la base, en la
cadena, con otra configuración de memoria, a veces elegía otro.

El defecto estaba **en los dos lugares**. El código necesitaba el
desempate del capítulo @cap:paginacao-filtros-e-buscas
—`orderByDesc('id')` después de la fecha—, porque en producción dos
préstamos en el mismo segundo ocurren todos los sábados en la mañana. Y la
prueba tenía que crear los préstamos con fechas distintas, para afirmar el
orden que promete la regla, y no el que la base produce por casualidad.

La prueba inestable tenía razón. Estuvo diciendo, tres días seguidos, que
el listado de producción tenía un defecto.

:::note En tu carrera
Una prueba inestable —que a veces pasa y a veces falla sin cambios en el
código— es casi siempre un defecto real, solo que uno que depende del
orden, del tiempo o de la concurrencia. Son las tres cosas que la prueba
manual nunca atrapa.

La reacción común es marcar la prueba como inestable, saltarla y seguir.
La reacción que separa a quien investiga de quien solo entrega es la de
Tainá: sospechar que la prueba está intentando decir algo, y leer línea
por línea hasta descubrir qué. Toma una tarde. El defecto que esconde suele
tomar una semana en encontrarse en producción.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  phpunit.xml                      # base _prueba, cola sync
  tests/Pest.php                   # RefreshDatabase en Feature
  tests/Feature/
    ProteccionTest.php             # 401 para cada ruta del grupo
    LibroTest.php                  # CRUD, 201, 422
    PrestamoFlujoTest.php          # base, transacción, 409
    PrestamoAutorizacionTest.php   # dueño, otro, equipo
    CamposInternosTest.php         # SECRETO-DE-PRUEBA
    AvisosTest.php                 # jobs ejecutados de verdad
:::

:::summary
- La prueba de feature hace el camino entero —ruta, middleware, Form
  Request, policy, service, resource, handler— sin servidor web.
- `assertJsonMissingPath` y la búsqueda por el valor garantizan lo que no
  puede salir.
- `RefreshDatabase` migra una vez y deshace cada prueba en una transacción;
  la base de pruebas es otra, declarada en el `phpunit.xml`.
- SQLite en memoria no tiene la collation, el bloqueo ni la verificación de
  tipos de MySQL; prueba en la base de producción.
- `actingAs` autentica; la prueba de `401` protege el grupo de rutas.
- Los permisos se demuestran por el lado del rechazo: dueño, otro del mismo
  rol, equipo.
- `assertDatabaseHas` demuestra que existe, no que sea único.
- No repitas en la feature lo que demostró la unitaria; un caso por camino
  basta.
- Los fakes verifican el disparo; al menos una prueba ejecuta cada job de
  verdad.
- `--profile` antes de culpar a la base; `--parallel` después.
- Una prueba inestable es, casi siempre, un defecto de orden, tiempo o
  concurrencia.
:::

:::checkpoint
La suite de feature cubre el CRUD, el flujo de préstamo con la base, los
`422`, los `401` de cada grupo, los `403` por rol y por propiedad, y el
campo interno que nunca sale; y corre en menos de un minuto, en el mismo
MySQL de producción, fallando el día en que cambie el contrato.
:::

:::exercise level=1
Di si cada afirmación debe probarse en la unitaria o en la feature:

1. Una multa de R$ 5,01 impide el préstamo.
2. `POST /prestamos` sin token responde `401`.
3. El `LectorResource` no expone el documento a otro lector.
4. `ReglasDeCirculacion` da un límite de cinco en enero.
5. La devolución libera el ejemplar en la misma transacción.

:::answer
1. Unitaria, en la `PoliticaDePrestamo`. En la feature, como mucho un caso
   de `409` para demostrar que la excepción llega al cliente.
2. Feature. Es una afirmación sobre el middleware y el archivo de rutas.
3. Feature, con dos usuarios autenticados. Se puede probar el resource
   aislado, pero la garantía real es que la ruta usa ese resource.
4. Unitaria. Es pura.
5. Feature, con base. Es una afirmación sobre la transacción.
:::

:::exercise level=2
Escribe la prueba de feature del listado de préstamos que habría atrapado
el defecto de la historia **de forma determinista**: fallando siempre, y no
a veces, mientras no exista el desempate.

:::answer
El truco es crear préstamos con la **misma** fecha, a propósito, en un
orden de id conocido, y afirmar el orden que promete la regla:

```php
test('préstamos con la misma fecha siguen el desempate', function () {
    $lector = Usuario::factory()->lector()->create();
    $mismoInstante = '2026-03-07 10:00:00';

    $ids = Prestamo::factory()
        ->count(5)
        ->for($lector->lector)
        ->create(['retirado_en' => $mismoInstante])
        ->pluck('id')
        ->sortDesc()
        ->values()
        ->all();

    $recibidos = $this->actingAs($lector)
        ->getJson('/api/prestamos')
        ->assertOk()
        ->json('data.*.id');

    expect($recibidos)->toBe($ids);
});
```

Sin el `orderByDesc('id')` en el listado, el orden entre los cinco depende
de la base, y la prueba falla en la mayoría de las ejecuciones en vez de
una de cada diez: cinco empates son mucho más difíciles de acertar por
casualidad que tres.

La lección de fondo: la prueba de la historia afirmaba **lo que se
observó**. Esta afirma **lo que se prometió** —el orden del contrato— y
crea a propósito la situación en que la promesa se pone a prueba.
:::

:::exercise level=3
Un proyecto nuevo que asumiste tiene seiscientas pruebas de feature,
ninguna unitaria, y tarda once minutos. El equipo corre las pruebas solo
en la cadena, y un commit tarda quince minutos en confirmarse. La propuesta
sobre la mesa es cambiar MySQL por SQLite en memoria.

Escribe el plan, en orden, con lo que medirías y lo que harías en cada
etapa. Di qué responderías a la propuesta de SQLite.

:::answer
**Sobre SQLite, primero.** Probablemente reduce el tiempo a la mitad y
cambia velocidad por certeza: la collation, el bloqueo de fila y los tipos
dejan de probarse. No la rechazaría de entrada: preguntaría si el proyecto
usa alguna de esas cosas. Si usa búsqueda sin tildes, `lockForUpdate` o
depende de tipos estrictos de columna, la respuesta es no.

**Etapa 1: medir.** `--profile` para encontrar las más lentas. En suites
así, es común que una décima parte de las pruebas tome la mitad del
tiempo, casi siempre por factories creando cientos de registros
encadenados sin necesidad.

**Etapa 2: arreglar las lentas.** Reducir el volumen de datos donde el
volumen no es lo que se prueba; cambiar `create()` por `make()` donde la
base no importa; usar un `seed` compartido para los datos de referencia que
toda prueba necesita.

**Etapa 3: paralelizar.** `--parallel` en la cadena y en las máquinas. Eso
solo suele dividir el tiempo por el número de núcleos.

**Etapa 4: mover a la unitaria lo que es regla.** Las pruebas de feature
que prueban veinte variaciones de la misma regla pasando por HTTP se
vuelven una prueba de feature —el camino— y un dataset unitario —las
variaciones—. Es la etapa más larga y la que más reduce el tiempo, y solo
tiene sentido después de separar la regla de la consulta, como la
`PoliticaDePrestamo`.

**Lo que mostraría en la reunión:** el antes y el después de cada etapa, en
minutos. La propuesta de SQLite era una solución; el `--profile` es el
diagnóstico, y suele apuntar a una causa más barata y sin pérdidas.
:::
