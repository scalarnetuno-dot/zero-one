---
source_hash: e4ac87e75414
title: "Documentación de la API"
number: 27
slug: documentacao-da-api
part: p7
kicker: "La integración de la aplicación tardó tres semanas. La única documentación de la API era una frase: \"pregúntale a Dedé\"."
goal: >-
  Publicar una documentación que nace del código y por eso no se
  desactualiza: un esquema OpenAPI generado de las rutas, los Form Requests
  y los resources, con los errores descritos, ejemplos ejecutables, y un
  plan escrito para retirar un campo sin romper a quien lo usa.
---

:::story Pregúntale a Dedé
La aplicación del lector no la hacía Vertexo. La asociación había
conseguido, por otra convocatoria, un estudio pequeño de Recife que hacía
aplicaciones para ONG. Tenían una desarrolladora, Lívia, y tres semanas.

El primer día, Lívia mandó un e-mail educado preguntando por la
documentación de la API. Márcia se lo reenvió a Dedé. Dedé respondió con la
dirección de homologación y la frase "cualquier duda, me escribes".

El segundo día, Lívia escribió. Quería saber el formato del
`POST /prestamos`. Dedé se lo explicó. El tercero, quería saber por qué el
`422` tenía `errors` y el `409` no. Dedé le explicó que eso estaba
cambiando. El quinto, quería saber si `devolver_hasta` venía con hora. Dedé
no se acordaba y fue a mirar.

La segunda semana, Lívia mandó una planilla. Tenía cuarenta y una filas,
una por cada ruta que había descubierto probando, con lo que creía que
cada una recibía y devolvía. Once estaban mal. Tres eran rutas que Dedé
había borrado la semana anterior.

—Ella hizo la documentación —dijo Tainá, mirando la planilla.

—Hizo la documentación de la API que existía el martes pasado —dijo Dedé.

Márcia apareció en la puerta.

—El estudio dice que el retraso es por culpa de nuestra API.

—Sí —dijo Dedé.

—¿Cómo que sí?

—Tiene razón. Cada vez que cambio algo, ella lo descubre probando.
:::

## La documentación que no nace del código empieza a mentir

La planilla de Lívia es el destino de toda documentación escrita a mano
sobre una API que cambia. El día en que se escribe, está bien. La semana
siguiente, una ruta cambia de nombre, un campo gana un formato, aparece una
validación nueva, y nadie se acuerda de actualizar el documento, porque el
documento no está en el mismo lugar que el código y a nadie se le avisa
cuando los dos divergen.

La documentación en una wiki, en un PDF, en una página de Notion tiene el
mismo defecto que el número guardado del capítulo
@cap:o-que-vamos-construir: es una copia de algo que ya existe en otro
lugar, y las copias divergen.

La salida es la misma: no guardar la copia. **Generar** la documentación a
partir de lo que ya existe —las rutas, los Form Requests, los resources—
de modo que cambiar el código cambie el documento, sin que nadie tenga que
acordarse.

## OpenAPI: el esquema que genera todo lo demás

Existe un formato estándar para describir una API HTTP, y se llama
OpenAPI. Es un archivo JSON o YAML con cada ruta, lo que recibe, lo que
devuelve en cada status, y los formatos de cada objeto:

```yaml
paths:
  /api/prestamos:
    post:
      summary: Realiza un préstamo
      security: [{ bearer: [] }]
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [ejemplar_id, lector_id]
              properties:
                ejemplar_id: { type: integer }
                lector_id: { type: integer }
      responses:
        '201':
          description: Préstamo creado
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Prestamo' }
        '409':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }
```

El archivo es verboso y nadie debería escribirlo a mano. Su valor está en
lo que se hace **a partir** de él:

- una página navegable, con cada ruta, cada campo y un botón para probar;
- clientes generados automáticamente para la aplicación —en Kotlin, Swift,
  TypeScript—, con los tipos correctos;
- validación automática, en la suite de pruebas, de que las respuestas
  reales siguen el esquema.

El esquema es el contrato del capítulo @cap:o-que-e-uma-api-rest, en un
formato que leen las máquinas.

## Generarlo a partir de rutas, requests y resources

Hay dos familias de herramientas en PHP para producir el OpenAPI.

**Anotaciones en el código.** Escribes, en atributos PHP encima de cada
método, la descripción de la ruta. La herramienta lee los atributos y arma
el esquema. El esquema queda preciso y tan actualizado como los atributos,
que son, otra vez, una copia escrita a mano, ahora más cerca del código.

**Inferencia.** La herramienta lee el propio código —la ruta, el tipo del
Form Request y sus reglas, el resource que devuelve el método— y deduce el
esquema. Scramble es la más usada en el ecosistema Laravel:

```text
$ composer require dedoc/scramble
```

Sin ninguna otra línea, la ruta `/docs/api` pasa a existir en desarrollo, y
`/docs/api.json` devuelve el esquema. Lee:

| De dónde | Qué deduce |
|---|---|
| `routes/api.php` | las rutas y los verbos |
| el Form Request | los campos de entrada, tipos, obligatorios |
| `Rule::enum` | la lista de valores aceptados |
| el `JsonResource` | los campos de la respuesta |
| `auth:sanctum` | que la ruta exige token |
| `abort`, excepciones y el Form Request | los status de error posibles |

Tabla: Todo lo que este libro escribió con cuidado en los últimos trece
capítulos se vuelve, gratis, documentación, y sale bien precisamente porque
se escribió con cuidado.

Fíjate en el efecto colateral. El `validated()` y el `JsonResource` se
defendieron, en los capítulos @cap:validation-e-form-requests y
@cap:api-resources, por seguridad y por contrato. También son lo que
permite inferir la documentación: un controller que hace `$request->all()`
y `return $model` no dice nada que una herramienta pueda leer.

La inferencia no lo adivina todo. Lo que no deduce, lo agregas tú, y el
lugar correcto es el docblock del método, que queda al lado del código:

```php title="app/Http/Controllers/PrestamoController.php" numbered
/**
 * Realiza un préstamo.
 *
 * Solo el equipo presta; el lector no se presta a sí
 * mismo por la aplicación. El plazo depende del perfil
 * del lector y se informa en `devolver_hasta`.
 */
public function store(
    RealizarPrestamoRequest $request,
    PrestamoService $prestamos,
) {
    // ...
}
```

El texto aparece en la página, junto a lo que se infirió. Es la única
pieza escrita a mano, y está a tres líneas del código que describe.

## Documentar el error es documentar la mitad del contrato

La documentación que solo muestra el camino feliz es la más común y es la
mitad del contrato. Lívia no preguntó tres veces por el `201`. Preguntó
por el `422`, el `409`, lo que llega cuando el token expira.

El formato único del capítulo @cap:erros-padronizados entra en el esquema
como un componente. Scramble acepta un gancho, registrado en el provider,
que recibe el esquema ya generado y permite agregar lo que la inferencia no
vio. El resultado, en el `openapi.json`, es este:

```yaml
components:
  schemas:
    Error:
      type: object
      required: [tipo, mensaje]
      properties:
        tipo: { type: string }
        mensaje: { type: string }
        campos:
          type: object
          nullable: true
          additionalProperties:
            type: array
            items: { type: string }
        incidente: { type: string, nullable: true }
```

Toda respuesta de error de toda ruta apunta a él, y el cliente generado a
partir del esquema gana una clase `Error` con los cuatro campos tipados.

Y cada `tipo` posible gana una fila en una tabla, que es la parte de la
documentación que la aplicación más consulta:

| `tipo` | Status | La aplicación debe |
|---|---|---|
| `no-autenticado` | `401` | llevar al login |
| `sin-permiso` | `403` | mostrar "sin permiso" |
| `no-encontrado` | `404` | mostrar "no encontrado" |
| `validacion` | `422` | resaltar los `campos` |
| `ejemplar-no-disponible` | `409` | ofrecer la reserva |
| `limite-de-prestamos` | `409` | listar lo que hay que devolver |
| `lector-con-pendiente` | `409` | mostrar el monto y cómo pagar |
| `demasiadas-peticiones` | `429` | esperar el `Retry-After` |
| `fallo-interno` | `500` | mostrar el `incidente` |

Tabla: La tabla se escribe a mano, y es la excepción que confirma la
regla: cambia solo cuando aparece una excepción de dominio nueva, y la
prueba de la sección siguiente lo señala cuando pasa.

## Ejemplos que la persona pulsa y ejecuta

La página que genera Scramble tiene, en cada ruta, un botón para enviar
una petición de verdad, con un campo para el token. Lívia, el primer día,
habría escrito el token de homologación y probado cada ruta desde la
página, viendo el formato real de la respuesta, en vez de armar la
planilla a mano.

Los ejemplos ejecutables tienen una exigencia: un entorno donde ejecutar
sea seguro. La página apunta a **homologación**, con la base de datos de
las factories del capítulo @cap:migrations-seeders-e-factories, y con el
`EnviadorEnLog` del capítulo @cap:service-container: ningún aviso sale a
un teléfono de verdad cuando alguien pulsa "probar" en el
`POST /prestamos`.

### La prueba que compara el esquema con la realidad

La documentación generada del código aún puede divergir del
comportamiento: el resource declara un campo como entero, y un camino raro
del código devuelve texto. Una última capa cierra eso: verificar, **en las
pruebas de feature**, que cada respuesta obedece al esquema publicado:

```php title="tests/Feature/ContratoTest.php" numbered
test('las respuestas siguen el esquema OpenAPI', function (
    string $metodo,
    string $ruta,
    array $cuerpo,
    int $status,
) {
    $admin = Usuario::factory()->admin()->create();

    $respuesta = $this->actingAs($admin)
        ->json($metodo, $ruta, $cuerpo)
        ->assertStatus($status);

    expect($respuesta)->toMatchOpenApi(
        base_path('docs/openapi.json'),
    );
})->with('rutas-del-contrato');
```

El `toMatchOpenApi` aquí es una expectativa propia del proyecto,
construida sobre una biblioteca de validación de OpenAPI: lee el esquema,
encuentra la ruta y el status, y verifica cada campo de la respuesta. El
archivo `docs/openapi.json` se **genera en la cadena** y se versiona, y un
cambio en él aparece en el *diff* de la revisión de código, donde alguien
puede preguntar si ese cambio rompe la aplicación.

:::key
Son tres capas, cada una protege contra un tipo de mentira:

La **inferencia** impide que la documentación olvide una ruta o un campo.

El **archivo versionado** hace que todo cambio de contrato aparezca en la
revisión.

La **prueba de contrato** impide que el código haga algo distinto de lo
que dice el documento.
:::

## Versionar y marcar lo que va a salir

El capítulo @cap:api-resources dejó un plan a medias: `devolver_hasta`,
que la aplicación 1.0 lee como `DD/MM/AAAA`, tiene que pasar a
`AAAA-MM-DD`. El campo nuevo `devolver_hasta_iso` se agregó al lado. Falta
la parte que resuelve la documentación: **avisar**.

```php title="app/Http/Resources/PrestamoResource.php" numbered
return [
    // ...

    /**
     * @deprecated Formato DD/MM/AAAA. Usa `devolver_hasta_iso`.
     *             Sale el 30/06/2026.
     */
    'devolver_hasta' => $this->devolver_hasta->format('d/m/Y'),

    'devolver_hasta_iso' => $this->devolver_hasta->toDateString(),
];
```

El esquema pasa a marcar el campo con `deprecated: true`, la página lo
muestra tachado, y los clientes generados a partir del esquema pasan a
emitir un aviso de compilación cuando alguien usa el campo.

El plan entero, escrito en la documentación y no en la cabeza de nadie:

| Fecha | Qué pasa |
|---|---|
| 01/03 | `devolver_hasta_iso` publicado; `devolver_hasta` marcado |
| 01/03 a 30/06 | el log cuenta las peticiones que aún vienen de la 1.0 |
| 01/06 | aviso en la aplicación 1.0: "actualiza antes del 30/06" |
| 30/06 | `devolver_hasta` pasa a tener el formato ISO |
| 30/09 | `devolver_hasta_iso` sale, después de tres meses marcado |

Tabla: Seis meses para cambiar el formato de un campo. Parece mucho, y es
el tiempo que tarda en desaparecer una aplicación instalada en un celular
sin actualización automática.

La API también avisa en la propia respuesta, para los clientes que no leen
documentación:

```text
Deprecation: @1740787200
Sunset: Tue, 30 Jun 2026 23:59:59 GMT
Link: </docs/api#devolver_hasta>; rel="deprecation"
```

Los encabezados `Deprecation` y `Sunset` están estandarizados, y un
cliente bien escrito los registra en el log. Un middleware de ruta los
agrega en las rutas que devuelven el campo: una aplicación directa del
capítulo @cap:middleware.

## Exponer o no la documentación en producción

Scramble, por defecto, solo muestra la documentación en el entorno local.
La decisión de abrirla en producción es del equipo, y depende de quién
consume la API.

**La API es pública**, para que cualquiera la integre: la documentación
también es pública. Esconderla no protege nada: cualquier persona descubre
las rutas usando la aplicación con un inspector de red.

**La API es de un cliente conocido**, como la aplicación del estudio de
Recife: la documentación queda detrás de autenticación, accesible para
quien integra.

**La API tiene rutas administrativas**: esas rutas **no** entran en la
documentación pública, aunque el resto entre. Publicar
`/api/admin/lectores/exportar` en un documento abierto es entregar el mapa
de dónde buscar.

La Casa Amarela publica la documentación en homologación, con login, y
genera dos esquemas: uno completo, para el equipo, y otro solo con las
rutas del lector, para el estudio.

:::note En tu carrera
La documentación de API suele verse como una tarea de fin de proyecto, y
por eso llega tarde y desactualizada. Tratada como consecuencia del código
—generada, versionada, probada—, deja de ser una tarea.

Y tiene un efecto que poca gente anticipa: cambia la conversación con quien
consume la API. Lívia deja de preguntar y pasa a señalar: "el esquema dice
entero y llegó texto". Una pregunta cuesta una interrupción; un
señalamiento contra un documento es un defecto con dirección. Quien publica
la documentación correcta gana, gratis, un probador externo que trabaja
para el propio proyecto.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  config/scramble.php            # dos esquemas: equipo y lector
  docs/
    openapi.json                 # generado en la cadena, versionado
  app/Providers/
    AppServiceProvider.php       # componente Error en el esquema
  app/Http/Middleware/
    AvisaObsolescencia.php       # Deprecation, Sunset, Link
  tests/Feature/
    ContratoTest.php             # respuesta real × esquema
:::

:::summary
- La documentación escrita a mano es una copia del código, y las copias
  divergen.
- OpenAPI describe rutas, entradas, respuestas y errores en un formato que
  genera la página, los clientes y la validación.
- La inferencia lee rutas, Form Requests, `Rule::enum`, resources y
  middleware; lo que el libro escribió con cuidado se vuelve documentación.
- `$request->all()` y `return $model` no documentan nada.
- El error es la mitad del contrato: el componente `Error` y la tabla de
  `tipo` describen lo que debe hacer el cliente.
- Los ejemplos ejecutables necesitan un entorno donde ejecutar sea seguro.
- El esquema versionado muestra los cambios de contrato en la revisión; la
  prueba de contrato verifica la respuesta real contra él.
- Un campo que sale se marca, se avisa por encabezado y se retira con un
  plan con fechas.
- Las rutas administrativas no entran en la documentación pública.
:::

:::checkpoint
La API de la Casa Amarela tiene `/docs` y `openapi.json` generados del
código, con los errores y sus `tipo` descritos, ejemplos que se ejecutan en
homologación, una prueba que verifica cada respuesta contra el esquema, y
un plan con fechas para cambiar el formato de `devolver_hasta` sin romper
la aplicación 1.0.
:::

:::exercise level=1
Di qué puede deducir sola la herramienta de inferencia y qué hay que
agregar a mano:

1. Que `POST /libros` exige `titulo`.
2. Que el lector no puede crear un préstamo por la aplicación.
3. Que la `condicion` del ejemplar acepta `bueno`, `prestado`,
   `restauracion` y `extraviado`.
4. Que `devolver_hasta` se retirará el 30/06.
5. Que el `409` de préstamo puede tener el `tipo`
   `ejemplar-no-disponible`.

:::answer
1. Sola, por el `required` del `StoreLibroRequest`.
2. A mano, en el docblock. La inferencia ve el `authorize()` y sabe que
   puede haber `403`, pero no sabe **por qué** ni para quién.
3. Sola, por el `Rule::enum(EstadoEjemplar::class)`, y sigue bien cuando
   entre un caso nuevo en el enum.
4. A mano, en el `@deprecated` del resource.
5. En parte. La herramienta sabe que la ruta puede devolver `409` si la
   excepción se lanza de un modo que puede rastrear; la lista de `tipo`
   posibles es la tabla escrita a mano.

El patrón: lo que es **estructura** lo deduce la herramienta; lo que es
**intención** —por qué, para quién, hasta cuándo— necesita una frase.
:::

:::exercise level=2
El campo `tema` del `LibroResource` va a pasar al objeto `tema_detallado`,
como planeó el capítulo @cap:api-resources. Escribe: el fragmento del
resource con la marca, la tabla de fechas del plan, y la condición
**medida** que autoriza el último paso.

:::answer
```php
/**
 * @deprecated Texto suelto. Usa `tema_detallado`.
 *             Sale el 31/10/2026.
 */
'tema' => $this->tema->nombre,

'tema_detallado' => new TemaResource($this->tema),
```

| Fecha | Qué pasa |
|---|---|
| 01/05 | `tema_detallado` publicado; `tema` marcado |
| 01/05 a 31/10 | encabezados `Deprecation` y `Sunset` en las rutas |
| 01/09 | aviso en la aplicación a las versiones que leen `tema` |
| 31/10 | `tema` sale |

**La condición medida:** el log estructurado registra, en cada petición, la
versión de la aplicación que vino en el encabezado `X-App-Version`. El
último paso solo ocurre si, en las dos semanas anteriores al 31/10, las
versiones que todavía leen `tema` suman menos de, digamos, el 1% de las
peticiones, y si Vera acepta avisar personalmente a quien todavía esté en
ellas.

Si el número no baja, la fecha cambia. La fecha del plan es una intención;
lo que autoriza el retiro es la medición.
:::

:::exercise level=3
El estudio de Recife pidió que la API pase a tener versión en la ruta
—`/api/v1/...`—, "porque es el estándar del mercado y nos lo facilita".
Hoy la API no tiene versión en la ruta.

Escribe la respuesta al estudio: qué resuelve la versión en la ruta, qué le
cuesta a la Casa Amarela, qué hace ya el equipo en su lugar, y en qué
situación la aceptarías.

:::answer
**Qué resuelve.** Permite cambiar el contrato de forma incompatible
—renombrar, quitar, cambiar formatos— manteniendo la versión vieja en línea
para quien todavía depende de ella. El cliente elige cuándo migrar,
cambiando una parte de la URL.

**Qué cuesta.** Por cada versión viva, las rutas, los controllers, los
resources y las pruebas existen por duplicado, o se comparten con `if` por
versión. Un defecto de seguridad hay que corregirlo en todas. Y la
tentación de publicar la v2 "para arreglarlo todo" suele producir una v2
que convive con la v1 durante años.

**Qué hace ya el equipo en su lugar.** Evolución compatible: campo nuevo al
lado del viejo, marca en el esquema, encabezados `Deprecation` y `Sunset`,
retiro con fecha y medición. Eso resuelve los cambios que la API ha tenido
hasta hoy sin duplicar nada, y el esquema versionado en Git muestra
exactamente qué cambió y cuándo.

**Cuándo la aceptaría.** Si aparece un cambio que no puede hacerse al
lado: que el modelo de reserva pase de "por libro" a "por ejemplar", por
ejemplo, alterando el significado de la mitad de las rutas. Ahí la v2 es
honesta: es otro contrato.

**Y lo que le ofrecería al estudio ahora:** prefijar las rutas con `/api/v1`
**hoy**, sin crear ninguna v2, como una dirección reservada. No cuesta
nada, atiende el pedido, y deja el camino abierto para el día en que
aparezca de verdad un cambio incompatible. Lo que rechazaría es usar la
versión en la ruta como sustituto de la disciplina de evolución
compatible, porque esa disciplina sigue siendo necesaria dentro de cada
versión.
:::
