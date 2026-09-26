---
source_hash: 8013b49beb4b
title: "Relaciones"
number: 12
slug: relacionamentos
part: p3
kicker: "El listado del acervo tardaba cuatro segundos. El log mostró 143 consultas para mostrar 47 libros."
goal: >-
  Modelar las conexiones del dominio con el tipo correcto de relación,
  reconocer el N+1 contando consultas, y corregirlo probando la corrección
  con el mismo contador.
---

:::story Ciento cuarenta y tres
La pantalla del acervo tardaba. No se trababa: tardaba, unos cuatro
segundos, lo suficiente para que Vera hiciera clic otra vez creyendo que no
lo había tomado.

Dedé había activado el registro de consultas la semana anterior, por otro
motivo. Abrió el log después de cargar la pantalla una vez y subió hasta el
principio.

```text
$ grep -c "select" storage/logs/laravel.log
143
```

—Ciento cuarenta y tres consultas.

—¿Para cuántos libros?

—Cuarenta y siete. Es la primera página.

Tainá hizo la cuenta en voz alta.

—Cuarenta y siete por tres, más dos.

—Más dos.

—¿Y qué son las tres?

—Autor, ejemplares y préstamos abiertos. Una por libro, una a la vez.
:::

## La clave foránea vive del lado que tiene muchos

Antes de cualquier código, la pregunta que decide todo: **¿quién apunta a
quién?**

Un libro tiene varios ejemplares; un ejemplar pertenece a un libro. La
columna `libro_id` está en `ejemplares`, porque es ahí donde hay muchos. Lo
contrario exigiría una columna con una lista adentro, que es lo que el
modelo relacional no hace.

| Del lado de la tabla | En el model | Quién tiene la columna |
|---|---|---|
| un libro tiene varios ejemplares | `hasMany` | `ejemplares` |
| un ejemplar pertenece a un libro | `belongsTo` | `ejemplares` |

Tabla: Los dos métodos describen la **misma** clave foránea, desde puntos
de vista opuestos. Quien tiene la columna usa `belongsTo`.

```php title="app/Models/Libro.php" numbered
public function ejemplares(): HasMany
{
    return $this->hasMany(Ejemplar::class);
}
```

```php title="app/Models/Ejemplar.php" numbered
public function libro(): BelongsTo
{
    return $this->belongsTo(Libro::class);
}
```

Laravel adivina el nombre de la columna a partir del nombre del método y de
la clase: `libro()` con `Libro::class` busca `libro_id`. Cuando el nombre se
salga del estándar, el segundo argumento dice cuál es.

```php
$libro->ejemplares;
```

```sql
SELECT * FROM ejemplares WHERE libro_id = ?
```

```php
$ejemplar->libro;
```

```sql
SELECT * FROM libros WHERE id = ? LIMIT 1
```

:::key
Fíjate en que leer `$libro->ejemplares` **dispara una consulta**. No es un
campo: es una llamada con cara de propiedad.

Ese es el origen del problema de este capítulo, y la razón por la que el
defecto es difícil de ver: no parece una consulta. Parece una flecha.
:::

## Muchos a muchos

Un libro puede tener dos autores; un autor escribió varios libros. Ninguna
de las dos tablas puede guardar la columna, así que la relación recibe una
tabla propia:

```php title="..._create_autor_libro_table.php" numbered
Schema::create('autor_libro', function (Blueprint $t) {
    $t->foreignId('autor_id')->constrained('autores');
    $t->foreignId('libro_id')->constrained();
    $t->string('rol', 20)->default('autor');
    $t->primary(['autor_id', 'libro_id']);
});
```

El nombre `autor_libro` no es una elección: es la convención, los dos
nombres en singular, en orden alfabético, separados por un guion bajo.
Salirse de ella cuesta un argumento más de cada lado.

```php title="app/Models/Libro.php" numbered
public function autores(): BelongsToMany
{
    return $this->belongsToMany(Autor::class)
        ->withPivot('rol')
        ->withTimestamps();
}
```

```php
$libro->autores;
```

```sql
SELECT autores.*, autor_libro.libro_id AS pivot_libro_id,
       autor_libro.autor_id AS pivot_autor_id,
       autor_libro.rol AS pivot_rol
FROM autores
INNER JOIN autor_libro ON autores.id = autor_libro.autor_id
WHERE autor_libro.libro_id = ?
```

:::pitfall
Sin el `withPivot('rol')`, la columna existe en la tabla, se graba
correctamente y **no viene** en la consulta.
`$libro->autores->first()->pivot->rol` devuelve `null`, y nada se queja.

El `withPivot` es la lista de lo que devuelve la tabla del medio. Es el
mismo comportamiento del `$fillable`, en la otra dirección: Laravel solo
trae lo que declaraste.

Cuando la tabla del medio recibe columnas —rol, orden, fecha, quién lo
registró—, dejó de ser una conexión y se volvió una entidad. Ahí vale la
pena considerar un model propio para ella, en lugar de empujar todo al
pivot.
:::

Para grabar:

```php
$libro->autores()->attach($autor->id, ['rol' => 'traductor']);
$libro->autores()->detach($autor->id);
$libro->autores()->sync([3, 7, 12]);
```

El `sync` es el que más asusta: deja la lista **exactamente** como la
mandaste, quitando lo que no esté ahí. Es lo correcto para un formulario
con casillas de selección, y es una pérdida de datos cuando se usa creyendo
que agrega.

## N+1: cien consultas detrás de una flecha

```php title="app/Http/Controllers/AcervoController.php" numbered
$libros = Libro::orderBy('titulo')->paginate(47);

foreach ($libros as $libro) {
    echo $libro->titulo;
    echo $libro->autores->pluck('nombre')->join(', ');
    echo $libro->ejemplares->count();
}
```

Cada `$libro->autores` y cada `$libro->ejemplares` dispara su propia
consulta. Para 47 libros:

| Consultas | De dónde vienen |
|---|---|
| 1 | el conteo del `paginate` |
| 1 | la lista de libros |
| 47 | los autores, un libro a la vez |
| 47 | los ejemplares, un libro a la vez |
| 47 | los préstamos abiertos, un libro a la vez |
| **143** | |

Tabla: Es la cuenta que hizo Tainá en voz alta. Su nombre es **N+1**: una
consulta para traer la lista, más una por ítem.

:::term N+1
El patrón en el que una consulta que trae N registros provoca N consultas
adicionales, una por cada uno.

No da error, no aparece en una prueba con tres registros y crece
linealmente con la base. Es el defecto de rendimiento más común de
cualquier proyecto con ORM, en cualquier lenguaje.
:::

## `with`, `load` y `withCount`

La corrección es decir **antes** lo que vas a necesitar:

```php
$libros = Libro::with(['autores', 'ejemplares'])
    ->withCount('ejemplares')
    ->orderBy('titulo')
    ->paginate(47);
```

```sql
SELECT COUNT(*) FROM libros;

SELECT *, (SELECT COUNT(*) FROM ejemplares
           WHERE ejemplares.libro_id = libros.id) AS ejemplares_count
FROM libros ORDER BY titulo ASC LIMIT 47 OFFSET 0;

SELECT autores.*, ... FROM autores
INNER JOIN autor_libro ON ...
WHERE autor_libro.libro_id IN (1, 2, 3, ..., 47);

SELECT * FROM ejemplares WHERE libro_id IN (1, 2, 3, ..., 47);
```

Cuatro consultas. Laravel trae la lista, junta los identificadores y busca
los relacionados de una vez, con `IN`.

| | Antes | Después |
|---|---|---|
| consultas | 143 | 4 |
| tiempo | ~4 s | ~40 ms |

Tabla: Y el número **deja de crecer** con el tamaño de la página. Con 200
libros por página siguen siendo cuatro.

Tres métodos, tres momentos:

**`with()`** carga junto, antes de que exista la colección. Es lo normal.

**`load()`** carga después, en un objeto que ya tienes en la mano. Sirve
cuando la decisión de necesitar la relación llega después de la consulta.

**`withCount()`** trae solo el número, sin los registros. Para mostrar "3
ejemplares", traer los tres es un desperdicio.

:::pitfall
El N+1 más difícil de encontrar no está en el controller: está en la
**serialización**.

Un resource que hace `'autores' => $this->autores->pluck('nombre')`
dispara la consulta en el momento en que se arma la respuesta, después de
que el controller terminó, lejos de donde alguien buscaría.

Por eso la herramienta de diagnóstico es el contador de consultas, y no la
lectura del controller.
:::

## La protección que convierte el N+1 en error

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Model::preventLazyLoading(! $this->app->isProduction());
}
```

Con eso, leer una relación que no se cargó **lanza una excepción** fuera de
producción:

```text
Attempted to lazy load [autores] on model [App\Models\Libro]
but lazy loading is disabled.
```

El efecto es convertir un problema de rendimiento, que nadie ve, en un
error de desarrollo, que nadie puede ignorar. Es la misma idea del
`preventSilentlyDiscardingAttributes` del capítulo anterior, aplicada a
otro silencio.

En producción queda apagado a propósito: una consulta de más es mejor que
una pantalla rota.

## Un salto más, y el polimórfico

Un lector tiene préstamos; cada préstamo es de un ejemplar; cada ejemplar
es de un libro. Para llegar del lector al libro son dos saltos, y existe un
método que los hace de una vez.

Vale la pena cuando la pregunta se hace con frecuencia —"¿qué libros ya se
llevó este lector?"— y no vale cuando aparece una vez en un informe. En la
duda, escribe la consulta con `JOIN`, que sabes leer.

La relación **polimórfica** es para cuando el mismo tipo de registro
apunta a cosas distintas: un comentario que puede ser sobre un libro o
sobre un autor, un adjunto que puede pertenecer a cualquier cosa.

Resuelve un problema real y cobra caro: la columna que guarda el tipo es
texto, no hay clave foránea posible, y la base deja de garantizar la
integridad que garantizaba. Úsala cuando la ganancia sea clara, y sabe que
la revisión pasó a ser tuya.

## Borrar en cascada

```php
$t->foreignId('libro_id')->constrained()->cascadeOnDelete();
```

Eso le dice a la base: borrar un libro borra sus ejemplares. Y, si los
préstamos también están en cascada, borra el historial junto.

:::pitfall
Borrar un libro del acervo no debería borrar el registro de que doña
Marlene se llevó ese ejemplar en 2019.

El préstamo es un **hecho histórico**. La rendición de cuentas de la
convocatoria cuenta préstamos, y un libro quitado del acervo no deshace lo
que pasó.

Para las entidades con historial, el borrado correcto casi nunca es el
físico. Laravel ofrece el lógico:

```php
use Illuminate\Database\Eloquent\SoftDeletes;

class Libro extends Model
{
    use SoftDeletes;
}
```

El `delete()` pasa a llenar una columna `deleted_at`, y todas las consultas
pasan a ignorar a quien la tiene llena. El registro sale de las pantallas y
sigue en la base, junto con todo lo que apunta a él.
:::

La cascada sigue siendo la elección correcta para lo que es **parte** de
otra cosa y no tiene vida propia: los ítems de un pedido, las opciones de
una encuesta, las líneas de una configuración.

:::note En tu carrera
"La pantalla está lenta" es un relato, no un diagnóstico, y la diferencia
entre quien lo resuelve en diez minutos y quien pasa la tarde es tener un
número antes de tener una hipótesis.

Cuenta las consultas primero. Si son decenas para una pantalla, es N+1, y
la corrección es una línea. Si son tres consultas que tardan cuatro
segundos, es un índice o el volumen, y la corrección es otra. Las dos
parecen iguales para quien está esperando que cargue la pantalla.

Y vale como respuesta en una entrevista: cuando te pregunten qué haces con
una página lenta, "primero mido" es una respuesta mejor que cualquier lista
de optimizaciones.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Models/
    Libro.php        # hasMany ejemplares, belongsToMany autores
    Autor.php
    Ejemplar.php     # belongsTo libro, hasMany prestamos
    Lector.php       # hasMany prestamos
    Prestamo.php     # belongsTo ejemplar, belongsTo lector
  database/migrations/
    ..._create_autores_table.php
    ..._create_autor_libro_table.php
:::

:::milestone
Fin de la Parte 3. El acervo tiene models con tipos, scopes y relaciones;
las consultas que produce el ORM son las mismas que escribirías a mano; y
el listado que tardaba cuatro segundos tarda cuarenta milisegundos, con la
prueba contada en consultas.
:::

:::summary
- La clave foránea vive en la tabla que tiene muchos; quien tiene la
  columna usa `belongsTo`.
- Leer una relación dispara una consulta: es una llamada con cara de
  propiedad.
- Muchos a muchos usa una tabla del medio con nombre convenido: los dos
  singulares en orden alfabético.
- `withPivot` declara qué columnas de la tabla del medio vuelven; sin él,
  llegan nulas en silencio.
- `sync` deja la lista exactamente como se mandó, quitando el resto.
- N+1 es una consulta para la lista más una por ítem; no da error y crece
  con la base.
- `with` carga antes, `load` carga después, `withCount` trae solo el
  número.
- El N+1 más escondido está en la serialización, no en el controller.
- `preventLazyLoading` convierte el problema silencioso en un error fuera
  de producción.
- La cascada sirve para lo que es parte de otra cosa; el historial pide un
  borrado lógico.
:::

:::checkpoint
Modelas relaciones en los dos sentidos y el muchos a muchos con atributos,
identificas un N+1 contando consultas en lugar de leyendo código, lo
corriges con `with` y `withCount`, y pruebas la corrección con el mismo
contador.
:::

:::exercise level=1
Di qué relación declarar en cada model, y en qué tabla queda la clave
foránea:

1. Un lector tiene varios préstamos.
2. Un préstamo tiene una multa; la multa pertenece a un préstamo.
3. Un ejemplar pasó por varios préstamos.

:::answer
1. `Lector::prestamos()` es `hasMany`; `Prestamo::lector()` es
   `belongsTo`. La columna `lector_id` queda en `prestamos`.
2. `Prestamo::multa()` es `hasOne`; `Multa::prestamo()` es `belongsTo`. La
   columna `prestamo_id` queda en `multas`: del lado que apunta, aunque sea
   uno a uno.
3. `Ejemplar::prestamos()` es `hasMany`; `Prestamo::ejemplar()` es
   `belongsTo`. La columna `ejemplar_id` queda en `prestamos`.

El caso 2 es el que confunde. En una relación uno a uno, los dos lados
podrían tener la columna, y la elección es de diseño: queda del lado
**opcional**. No todo préstamo genera multa, así que `prestamos` no debe
cargar una columna casi siempre nula apuntando a una fila que no existe.
:::

:::exercise level=2
Esta pantalla muestra los préstamos abiertos con el nombre del lector, el
título del libro y el registro. Hace un N+1 doble.

```php
$prestamos = Prestamo::whereNull('devuelto_en')->get();

foreach ($prestamos as $p) {
    echo $p->lector->nombre;
    echo $p->ejemplar->libro->titulo;
    echo $p->ejemplar->registro;
}
```

Cuenta las consultas para 30 préstamos, corrígelo y vuelve a contar.

:::answer
**Antes.** Una para la lista. Treinta para los lectores. Treinta para los
ejemplares. Y treinta para los libros, porque `$p->ejemplar->libro` solo
ocurre después de que llegó el ejemplar.

Total: **91 consultas**.

**La corrección** tiene que cargar dos niveles, y la notación es el punto:

```php
$prestamos = Prestamo::whereNull('devuelto_en')
    ->with(['lector', 'ejemplar.libro'])
    ->get();
```

**Después.** Una para los préstamos. Una para los lectores, con `IN`. Una
para los ejemplares, con `IN`. Una para los libros, con `IN`.

Total: **4 consultas**, y el número no cambia con trescientos préstamos.

El `ejemplar.libro` es la parte que se olvida: cargar `ejemplar` solo
resuelve dos tercios del problema y deja el tercer N+1 en su lugar, lo que
es peor que no haber corregido nada, porque ahora parece resuelto.
:::

:::exercise level=3
La asociación pidió "limpiar el acervo": quitar los libros que no se
prestan hace más de diez años.

Escribe la consulta que encuentra esos libros y responde: ¿qué pasa
exactamente con los ejemplares y con el historial de préstamos en cada una
de las tres opciones —cascada física, borrado lógico, y una tercera que
propongas?

:::answer
**La consulta:**

```php
$candidatos = Libro::whereDoesntHave(
    'ejemplares.prestamos',
    fn ($q) => $q->where('retirado_en', '>=', now()->subYears(10)),
)->get();
```

`whereDoesntHave` se vuelve un `NOT EXISTS` con subconsulta, y fíjate en
que incluye los libros que **nunca** se prestaron, lo que probablemente se
desea y hay que confirmar con Vera antes de ejecutar.

**Cascada física.** Borra el libro, los ejemplares y, si la cascada sigue,
los préstamos. El informe de "más prestados de 2019" pasa a devolver
números distintos de los que se imprimieron en 2019. Es la peor opción, y
es la que parece más limpia.

**Borrado lógico.** El libro recibe `deleted_at`, desaparece de las
pantallas y de las consultas. Los préstamos siguen, pero apuntan a un libro
que las consultas normales no traen: entonces el informe histórico pasa a
mostrar filas con el título en blanco, que es el defecto del capítulo
@cap:classes-e-objetos de vuelta.

Se resuelve, pero exige que los informes históricos pidan explícitamente
los registros quitados. Es una decisión que tiene que estar escrita en
algún lugar.

**La tercera: no borrar.** Lo que quiere la asociación no es quitar el
registro; es dejar de mostrar el libro en la pantalla de quien busca qué
llevarse a casa. Eso es un **estado**, no un borrado:

```php
$libro->update(['situacion' => SituacionLibro::Desactivado]);
```

El acervo activo filtra por situación. El historial sigue completo, el
título sigue apareciendo en los informes, y la operación tiene vuelta:
alguien puede reactivar el libro la semana siguiente sin restaurar un
respaldo.

La pregunta que lleva a esa respuesta, y que vale para casi todo pedido de
"borrar": **¿qué quiere dejar de ver la persona, y por cuánto tiempo?**
:::
