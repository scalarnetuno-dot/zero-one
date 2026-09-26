---
source_hash: 6e7af7f9cebd
title: "Paginación, filtros y búsquedas"
number: 16
slug: paginacao-filtros-e-buscas
part: p4
kicker: "La búsqueda de \"acafrao\" no encontraba \"Açafrão\". La mitad del acervo se había registrado con teclados de licitación, sin cedilla."
goal: >-
  Entregar un listado que aguante el acervo entero: paginado con techo del
  servidor, ordenado de forma estable, filtrable sin escalera de if, y con
  una búsqueda que encuentre el libro que la persona escribió como pudo.
---

:::story Solo un cambiecito
—Es solo un cambiecito —dijo don Juvenal, y Tainá, sin levantar los ojos,
dio vuelta una página del cuaderno.

—La búsqueda. Tiene que encontrar por todo. Título, autor, tema. Y la
gente escribe sin tildes, así que tiene que encontrar sin tildes también.

—¿Sin tildes cómo?

—Una muchacha buscó "acafrao" ayer y no lo encontró. Yo sé que está, lo
doné yo.

Dedé escribió en la pantalla de homologación: `acafrao`. Cero resultados.
Escribió `açafrão`. Un resultado: *O Açafrão e Outras Especiarias*.

—Lo encontró —dijo don Juvenal.

—Con tilde.

Vera, desde el mostrador, sin darse vuelta:

—Busca "acafrao" otra vez, pero en el Sistema.

Dedé abrió el Sistema de 2009. Escribió. Cuatro resultados: el libro de
don Juvenal y otros tres, todos con "acafrao" en el título, sin cedilla y
sin tilde.

—Las computadoras de 2012 vinieron de una licitación —dijo Vera—. Teclado
americano. Durante dos años nadie pudo escribir la cedilla. Yo registré
unos mil quinientos libros así.

—Entonces la búsqueda tiene que encontrar las dos formas en los dos
sentidos —dijo Tainá—. Quien escribe sin tilde encuentra los que tienen
tilde, y quien escribe con tilde encuentra los que no.

Don Juvenal sonrió.

—¿Viste? Un cambiecito.
:::

## Un listado sin límite es una denegación de servicio que publicaste

El `index` del capítulo @cap:o-crud-completo empezó así:

```php
return Libro::all();
```

Con cuarenta libros, funciona. Con los cuatro mil del acervo, la respuesta
tiene algunos megabytes, tarda segundos en salir, y cada petición carga
cuatro mil objetos en la memoria del servidor. Con ocho mil ejemplares y
quinientos mil préstamos en el historial, la ruta de préstamos tumba el
proceso.

Y no hace falta mala intención. Basta con que la aplicación cargue la lista
al abrirse, y que cien personas abran la aplicación a las nueve de la
mañana.

:::key
Toda ruta que devuelve una colección tiene un **techo**, y quien decide el
techo es el servidor. Un listado sin techo es una denegación de servicio
que publicaste tú mismo, esperando que alguien la llame.
:::

## Tres paginadores

Laravel tiene tres formas de cortar una consulta, y cada una responde una
pregunta distinta.

**`paginate`** trae la página y **cuenta el total**:

```php
Libro::orderBy('titulo')->paginate(20);
```

```sql
SELECT COUNT(*) AS aggregate FROM libros;
SELECT * FROM libros ORDER BY titulo LIMIT 20 OFFSET 40;
```

Dos consultas. El `meta` de la respuesta tiene `total` y `last_page`, y la
aplicación puede mostrar "página 3 de 202".

**`simplePaginate`** trae la página y **no cuenta**:

```sql
SELECT * FROM libros ORDER BY titulo LIMIT 21 OFFSET 40;
```

Una consulta. Pide 21 para saber si existe una página siguiente, y
devuelve 20. El cliente sabe si hay "siguiente", pero no cuántas páginas
son.

**`cursorPaginate`** no usa `OFFSET`:

```sql
SELECT * FROM libros
WHERE (titulo, id) > ('Memórias Póstumas', 1832)
ORDER BY titulo, id LIMIT 21;
```

Guarda, en un token opaco, el último registro de la página actual, y pide
"los siguientes después de este". El `OFFSET` desaparece.

| | `paginate` | `simplePaginate` | `cursorPaginate` |
|---|---|---|---|
| total y última página | sí | no | no |
| saltar a la página 50 | sí | sí | no |
| costo en la página 1 | medio | bajo | bajo |
| costo en la página 2.000 | alto | alto | bajo |
| estable con inserciones | no | no | sí |

Tabla: La columna del medio rara vez es la correcta: tiene el costo del
`OFFSET` sin la ventaja del total.

El costo alto del `OFFSET` en la página lejana es lo que mostraría el
`EXPLAIN` del capítulo @cap:duas-tabelas-conversando: para devolver las
filas 40.000 a 40.020, la base **lee y descarta** las primeras 40.000. La
página 1 es rápida, y cada página siguiente es un poco más lenta que la
anterior.

Para el acervo, que una persona hojea y en el que "página 3 de 202" ayuda,
`paginate`. Para el historial de préstamos de un lector, que la aplicación
desplaza infinitamente hacia abajo, `cursorPaginate`.

## Orden estable: el desempate que nadie recuerda

```php
Libro::orderBy('anio')->paginate(20);
```

Cuarenta libros se publicaron en 1938. La página 1 muestra veinte de ellos;
la página 2 muestra... **veinte de ellos**, posiblemente los mismos.

Cuando la columna del `ORDER BY` tiene valores repetidos, la base no
promete ningún orden entre los empates. Puede devolver los cuarenta en un
orden en la primera consulta y en otro en la segunda, y con `LIMIT` y
`OFFSET` eso significa un libro repetido en una página y un libro
desaparecido en la otra.

La corrección es siempre la misma: **terminar el `ORDER BY` con una
columna única**.

```php
Libro::orderBy('anio')->orderBy('id')->paginate(20);
```

:::pitfall
Este defecto no aparece en desarrollo. Con los cuarenta libros de la
factory, MySQL tiende a devolver los empates en el orden de inserción,
todas las veces. Con el acervo real, después de algunos meses de cambios y
de un `OPTIMIZE TABLE`, el orden de los empates cambia.

Es el defecto de la integración en rojo del capítulo
@cap:testes-de-feature-http-e-banco, que pasaba en toda máquina local.
:::

## Filtro opcional sin escalera de `if`

El listado acepta filtros, todos opcionales:

```text
GET /api/libros?tema=literatura&disponible=1&anio_min=1900
```

La primera versión suele ser esta:

```php
$consulta = Libro::query();

if ($request->tema) {
    $consulta->where('tema', $request->tema);
}

if ($request->anio_min) {
    $consulta->where('anio', '>=', $request->anio_min);
}

if ($request->disponible) {
    $consulta->whereHas('ejemplares', fn ($q) =>
        $q->where('condicion', EstadoEjemplar::Bueno));
}
```

Tiene un defecto que ya mostró el capítulo @cap:conversao-automatica:
`if ($request->anio_min)` es falso cuando `anio_min` es `0`. Para el año,
nadie lo nota. Para `?multa_min=0` o `?disponible=0`, el filtro desaparece
cuando el cliente pidió cero explícitamente.

El query builder tiene un método para "aplica esto solo si":

```php
$consulta = Libro::query()
    ->when(
        $request->filled('tema'),
        fn ($q) => $q->where('tema', $request->tema),
    )
    ->when(
        $request->filled('anio_min'),
        fn ($q) => $q->where(
            'anio', '>=', $request->integer('anio_min'),
        ),
    )
    ->when(
        $request->has('disponible'),
        fn ($q) => $request->boolean('disponible')
            ? $q->whereHas('ejemplaresDisponibles')
            : $q->whereDoesntHave('ejemplaresDisponibles'),
    );
```

`filled` revisa si el campo vino **y no está vacío**, y el `0` cuenta como
lleno. `has` revisa solo si vino, lo que permite distinguir
`?disponible=0` ("solo los no disponibles") de ningún filtro ("todos").

### El filtro recibe una clase

Con cinco filtros, el controller vuelve a quedar grande. Y los filtros son
**entrada**, así que también necesitan validación. Las dos cosas se
resuelven juntas: un Form Request que valida y entrega un objeto tipado.

```php title="app/Http/Requests/ListarLibrosRequest.php" numbered
class ListarLibrosRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'busqueda' => ['nullable', 'string', 'max:100'],
            'tema' => ['nullable', 'string', 'max:40'],
            'disponible' => ['nullable', 'boolean'],
            'anio_min' => ['nullable', 'integer', 'min:1400'],
            'sort' => ['nullable', Rule::in(FiltroDeLibros::ORDENES)],
            'por_pagina' => ['nullable', 'integer', 'between:1,100'],
        ];
    }

    public function filtro(): FiltroDeLibros
    {
        return new FiltroDeLibros(
            busqueda: $this->validated('busqueda'),
            tema: $this->validated('tema'),
            disponible: $this->has('disponible')
                ? $this->boolean('disponible')
                : null,
            anioMin: $this->validated('anio_min'),
            orden: $this->validated('sort') ?? 'titulo',
            porPagina: $this->validated('por_pagina') ?? 20,
        );
    }
}
```

```php title="app/Acervo/FiltroDeLibros.php" numbered
final readonly class FiltroDeLibros
{
    public const ORDENES = [
        'titulo', '-titulo', 'anio', '-anio', 'recientes',
    ];

    public function __construct(
        public ?string $busqueda,
        public ?string $tema,
        public ?bool $disponible,
        public ?int $anioMin,
        public string $orden,
        public int $porPagina,
    ) {}
}
```

El `?bool $disponible` tiene tres estados, y los tres significan cosas
distintas: `true`, `false` y "no filtrar". Es la distinción entre `null` y
`false` del capítulo @cap:variaveis-e-tipos, con una consecuencia de
negocio.

Y el model recibe un scope que toma el filtro entero:

```php title="app/Models/Libro.php" numbered
public function scopeFiltrar(
    Builder $q,
    FiltroDeLibros $f,
): void {
    $q->when($f->tema, fn ($q, $t) =>
            $q->where('tema', $t))
      ->when($f->anioMin !== null, fn ($q) =>
            $q->where('anio', '>=', $f->anioMin))
      ->when($f->disponible !== null, fn ($q) =>
            $f->disponible
                ? $q->whereHas('ejemplaresDisponibles')
                : $q->whereDoesntHave('ejemplaresDisponibles'))
      ->when($f->busqueda, fn ($q, $b) => $q->buscar($b))
      ->ordenarPor($f->orden);
}
```

El controller queda con el tamaño que debería tener:

```php title="app/Http/Controllers/LibroController.php" numbered
public function index(ListarLibrosRequest $request)
{
    $filtro = $request->filtro();

    $libros = Libro::filtrar($filtro)
        ->with('autores')
        ->paginate($filtro->porPagina)
        ->withQueryString();

    return LibroResource::collection($libros);
}
```

El `withQueryString()` hace que los enlaces de página siguiente y anterior
lleven los filtros. Sin él, el enlace de la página 2 pierde el
`tema=literatura`, y la persona que filtró vuelve a ver el acervo entero.

## Búsqueda por texto: `LIKE`, tildes y el índice que no se usa

La búsqueda de la Casa Amarela busca un término en el título o en el
nombre del autor. La forma directa:

```php
public function scopeBuscar(Builder $q, string $termino): void
{
    $q->where(fn ($q) => $q
        ->where('titulo', 'like', "%{$termino}%")
        ->orWhereHas('autores', fn ($q) =>
            $q->where('nombre', 'like', "%{$termino}%")));
}
```

Dos cosas en ese fragmento, una buena y una mala.

La buena: el `where` interno con una función agrupa las dos condiciones
entre paréntesis. Sin él, el `orWhere` se escaparía de los otros filtros:

```sql
-- sin el agrupamiento
WHERE tema = 'literatura' AND titulo LIKE '%x%'
   OR EXISTS (autor LIKE '%x%')

-- con el agrupamiento
WHERE tema = 'literatura'
  AND (titulo LIKE '%x%' OR EXISTS (autor LIKE '%x%'))
```

La primera devuelve libros de **cualquier** tema cuyo autor coincida con
el término. Es el `OR` fuera de paréntesis, el defecto de precedencia del
capítulo @cap:operadores, ahora en SQL.

La mala: `LIKE '%termino%'` **no usa índice**. Un índice en `titulo`
funciona como el orden alfabético de un diccionario, y permite encontrar
lo que **empieza** con una palabra. Encontrar lo que **contiene** una
palabra en el medio obliga a la base a leer todas las filas.

| Patrón | ¿Usa índice? |
|---|---|
| `titulo = 'Dom Casmurro'` | sí |
| `titulo LIKE 'Dom%'` | sí |
| `titulo LIKE '%Casmurro%'` | no |

Tabla: El `%` al principio es lo que mata el índice.

Con cuatro mil libros, leer todas las filas tarda milisegundos y no
importa. Con cuatro millones, importa. La respuesta para el volumen es el
índice `FULLTEXT` de MySQL, que parte el texto en palabras e indexa cada
una:

```php
$t->fullText(['titulo']);
```

```php
$q->whereFullText('titulo', $termino);
```

Para el acervo de la Casa Amarela, `LIKE` alcanza, y vale la pena saber en
qué número deja de alcanzar. Medir es el tema del capítulo
@cap:cache-logs-e-medicao.

### La tilde

MySQL tiene una respuesta lista para el problema de don Juvenal, y vive en
la **collation** de la columna: la regla que usa la base para comparar
texto:

```sql
SELECT 'acafrao' = 'Açafrão' COLLATE utf8mb4_0900_ai_ci;
-- 1
```

El `ai` es *accent insensitive*; el `ci`, *case insensitive*. Con esa
collation, `a`, `á` y `A` son iguales para la comparación, y el `LIKE`
también pasa a ignorar tildes y mayúsculas.

Laravel crea las tablas con `utf8mb4_unicode_ci` por defecto, que ignora
las mayúsculas y es **parcialmente** insensible a las tildes, con
diferencias entre versiones de MySQL que ya costaron muchas tardes
perdidas. La decisión explícita es declarar la collation en la columna que
se va a buscar:

```php title="..._ajustar_collation_de_titulo.php" numbered
Schema::table('libros', function (Blueprint $t) {
    $t->string('titulo', 200)
        ->collation('utf8mb4_0900_ai_ci')
        ->change();
});
```

:::pitfall
La collation resuelve la comparación y **no resuelve lo que se grabó**.
Los mil quinientos títulos de la licitación siguen sin cedilla en la base,
y la pantalla sigue mostrando "O Acafrao e Outras Especiarias" a quien lo
encuentre.

Corregir el texto grabado es otro trabajo, manual, que Vera hace de a
poco, cuando el libro pasa por el mostrador. Que la búsqueda deje de
depender de eso es lo que le permite hacerlo de a poco.

Y un segundo cuidado: la prueba que corre en SQLite no tiene esa
collation. La búsqueda sin tildes pasa en MySQL y falla en SQLite, o al
revés. El capítulo @cap:testes-de-feature-http-e-banco se ocupa de dónde
miente SQLite.
:::

## Ordenar por un campo del cliente sin abrirle la base

El cliente quiere elegir el orden: `?sort=-anio`. La tentación es pasarlo
directo:

```php
$q->orderBy($request->sort);
```

Laravel escapa el nombre de la columna, así que esto no es una inyección
de SQL en el sentido clásico. Pero el cliente puede ordenar por
**cualquier columna** —incluida `observacion_interna`, o `documento`— y
deducir por el resultado lo que no debería ver. Puede ordenar por una
columna sin índice en una tabla grande y hacer que cada petición cueste un
segundo.

La respuesta es una lista de permisos que traduce el nombre del contrato a
la consulta:

```php title="app/Models/Libro.php" numbered
public function scopeOrdenarPor(Builder $q, string $orden): void
{
    match ($orden) {
        'titulo' => $q->orderBy('titulo'),
        '-titulo' => $q->orderByDesc('titulo'),
        'anio' => $q->orderBy('anio'),
        '-anio' => $q->orderByDesc('anio'),
        'recientes' => $q->orderByDesc('created_at'),
    };

    $q->orderBy('id');
}
```

El `match` del capítulo @cap:condicionais garantiza que un valor fuera de
la lista no pasa en silencio: lanza `UnhandledMatchError`. No llega a
ocurrir, porque el `Rule::in` del Form Request ya lo rechazó con `422`,
pero si alguien un día se olvida de la validación, la consulta se rompe en
lugar de ordenar mal.

Y el `orderBy('id')` al final es el desempate de la sección anterior,
aplicado a todos los órdenes de una vez.

:::key
El nombre que usa el cliente para ordenar es **contrato**, no columna. El
`recientes` del contrato es `created_at` hoy y puede ser `adquirido_en`
mañana, sin que ningún cliente lo note.
:::

## El techo es del servidor

El último parámetro es `por_pagina`. El cliente puede pedir 10, 20, 50. Y
va a pedir 999.999, por accidente o no.

```text
GET /api/libros?por_pagina=999999
```

Dos respuestas posibles, y las dos son razonables:

**Rechazar con `422`.** El `between:1,100` del Form Request lo hace. El
cliente sabe exactamente cuál es el límite y se ajusta.

**Limitar en silencio.** `min($porPagina, 100)`. El cliente pidió un
millón y recibió cien, y el `meta.per_page` de la respuesta lo dice.

La Casa Amarela rechaza, porque una aplicación que pide 999.999 tiene un
defecto que alguien tiene que ver. Lo que no es aceptable es la tercera
opción: obedecer.

:::note En tu carrera
La paginación, los filtros y el orden son las partes de la API que más usa
el cliente y que menos aparecen en la conversación de planificación. Nadie
escribe "el listado tiene que tener desempate" en una historia de usuario.

Por eso suelen ser el primer problema en producción de una API nueva: no
se rompen el primer día, se rompen cuando llega el volumen. Si estás
revisando un listado, las cuatro preguntas caben en un minuto: ¿tiene
techo? ¿El orden termina en una columna única? ¿Los filtros tratan el cero?
¿El `sort` tiene lista de permisos?
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Acervo/
    FiltroDeLibros.php          # objeto tipado, tres estados
  app/Http/Requests/
    ListarLibrosRequest.php     # valida filtros y techo
  app/Models/
    Libro.php                   # scopes filtrar, buscar, ordenarPor
  database/migrations/
    ..._ajustar_collation_de_titulo.php
:::

:::summary
- Toda colección tiene techo, y el techo es del servidor.
- `paginate` cuenta el total; `simplePaginate` no cuenta; `cursorPaginate`
  prescinde del `OFFSET` y es rápido a cualquier profundidad.
- Un `ORDER BY` en una columna con repeticiones necesita un desempate por
  columna única, o las páginas pierden y repiten registros.
- `when` aplica un filtro opcional sin escalera de `if`; `filled` trata el
  cero como valor.
- Los filtros son entrada: se validan en un Form Request y viajan en un
  objeto tipado.
- Un `orWhere` fuera de agrupamiento se escapa de los otros filtros.
- `LIKE '%x%'` no usa índice; `FULLTEXT` resuelve el volumen.
- La collation `ai_ci` ignora tildes y mayúsculas en la comparación, y no
  corrige lo que se grabó.
- El `sort` del cliente pasa por una lista de permisos que traduce el
  contrato a la columna.
:::

:::checkpoint
Entregas `GET /libros` con búsqueda sin tildes, filtros opcionales que
tratan el cero, orden por lista de permisos con desempate, y techo de cien
por página, y sabes elegir entre los tres paginadores para un listado
nuevo.
:::

:::exercise level=1
¿Qué paginador usarías en cada caso, y por qué?

1. El historial de préstamos en la aplicación, con desplazamiento
   infinito.
2. El listado del acervo en el panel de Vera, con "página 3 de 202".
3. Una exportación nocturna que recorre los quinientos mil préstamos.

:::answer
1. `cursorPaginate`. El desplazamiento infinito no necesita total ni
   saltar páginas, y el cursor no repite ni pierde registros cuando un
   préstamo nuevo entra arriba mientras la persona se desplaza.
2. `paginate`. El total es lo que muestra la pantalla, y saltar a una
   página es útil. El costo del `COUNT` sobre cuatro mil libros es
   irrelevante.
3. Ninguno de los tres. Una exportación no es paginación de API: es el
   `chunkById` o el `lazyById` de Eloquent, que recorren la tabla en
   bloques usando el `id` como cursor, sin `OFFSET` y sin cargar todo en
   memoria.

El ítem 3 es el que engaña. El instinto de usar `paginate` en un bucle de
página en página funciona, y se vuelve más lento con cada página, por la
misma razón del `OFFSET` en la página 2.000.
:::

:::exercise level=2
Esta búsqueda de lectores está en producción. Encuentra los cuatro
defectos relacionados con el capítulo.

```php
public function index(Request $request)
{
    $q = Lector::query();

    if ($request->nombre) {
        $q->where('nombre', 'like', "%{$request->nombre}%")
          ->orWhere('documento', $request->nombre);
    }

    if ($request->bloqueado) {
        $q->whereNotNull('bloqueado_en');
    }

    return $q->orderBy($request->get('sort', 'nombre'))
        ->paginate($request->get('por_pagina', 20));
}
```

:::answer
**Uno: el `orWhere` sin agrupamiento.** Si se agregan otros filtros, la
búsqueda por documento se escapa de ellos. Hoy, el filtro de bloqueado ya
está después y se aplica con `AND` sobre solo una mitad del `OR`.

**Dos: `if ($request->bloqueado)`.** `?bloqueado=0` es falso, y el filtro
desaparece: en lugar de mostrar los no bloqueados, muestra todos.

**Tres: `orderBy` con un valor del cliente.** Cualquier columna, incluido
`documento`, y sin desempate, así que los lectores con el mismo nombre
cambian de página.

**Cuatro: `por_pagina` sin techo.** `?por_pagina=999999` devuelve la tabla
entera de lectores, con datos personales, en una petición.

Y un quinto, fuera del capítulo pero grave: la ruta devuelve el paginador
de models crudos, sin resource. El documento de todos los lectores está en
la respuesta.

La versión corregida sigue el molde del `ListarLibrosRequest`: Form Request
con `between:1,100` y `Rule::in` para el `sort`, `when` con
`has`/`boolean`, el `OR` dentro de un `where(fn ...)`, y
`LectorResource::collection`.
:::

:::exercise level=3
Vera quiere un orden nuevo: "los más prestados primero". En
`/api/libros?sort=populares`.

Escribe el caso en el `ordenarPor`, di qué tiene que existir en la base
para que funcione bien con el acervo entero, y responde: ¿ese número
debería calcularse en cada petición?

:::answer
La primera versión, correcta e ingenua:

```php
'populares' => $q
    ->withCount('prestamos')
    ->orderByDesc('prestamos_count'),
```

Eso exige una relación `prestamos` en `Libro`: un `hasManyThrough` a
través de ejemplares, que es el caso en que el capítulo
@cap:relacionamentos dijo que compensa.

**El costo.** El `withCount` se vuelve una subconsulta que cuenta préstamos
para **cada libro del acervo** antes de ordenar, porque la base no sabe
cuáles son los veinte más populares sin contarlos todos. Con quinientos mil
préstamos, cada petición cuenta quinientos mil registros. El índice en
`prestamos.ejemplar_id` ayuda a la subconsulta, y no evita el conteo
entero.

**¿Debería calcularse en cada petición? No.** La popularidad cambia algunas
decenas de veces por día, y el listado se consulta miles. Las salidas son
dos:

Una columna `total_prestamos` en `libros`, incrementada con cada préstamo
por el evento del capítulo @cap:events-jobs-e-filas, con índice. El orden
se vuelve `orderByDesc('total_prestamos')`, instantáneo.

O la caché del capítulo @cap:cache-logs-e-medicao, si "populares" es
siempre la misma lista y la paginación no importa.

La primera es mejor para ordenar, porque se combina con los filtros. Y
tiene un costo: la columna es una copia de algo que ya está en los
préstamos, y una copia puede divergir. Un comando nocturno que recalcula y
compara es el seguro.
:::
