---
source_hash: 89c547b7688c
title: "Eloquent"
number: 11
slug: eloquent
part: p3
kicker: "El registro de lectores aceptaba un campo que el formulario no tenía. Quien lo descubrió se volvió bibliotecaria jefa en nueve segundos."
goal: >-
  Usar el ORM sabiendo qué consulta produce cada método, proteger el
  registro contra campos que nadie pidió, convertir valores a la entrada y a
  la salida de la base, y reconocer cuándo un model se volvió un depósito.
---

:::story Perfil admin
Tainá estaba probando el registro público de lectores con `curl`, porque
el formulario esconde campos y quería ver qué aceptaba la API de verdad.

```text
$ curl -s -X POST localhost:8000/api/lectores \
       -H "Content-Type: application/json" \
       -d '{"nombre":"Prueba","documento":"11122233344",
            "perfil":"admin"}'
```

```text
{"id":4102,"nombre":"Prueba","documento":"11122233344",
 "perfil":"admin"}
```

Lo leyó dos veces.

—Dedé, ¿el formulario de registro tiene un campo de perfil?

—No. El perfil solo lo cambia Vera, en su pantalla.

—¿Entonces por qué lo aceptó?

Dedé abrió el model. La segunda línea de la clase era:

```php
protected $guarded = [];
```

—Eso quiere decir que nada está protegido.

—Eso quiere decir que ahora soy administradora.
:::

## Eloquent no es SQL mágico

Cada método de Eloquent produce una consulta, y puedes escribirlas todas a
mano: es lo que hicieron los capítulos de la Parte 2 del volumen 1.

Todo este capítulo sigue una regla: **ningún método aparece sin la
consulta al lado.**

```php
Libro::where('tema', 'infantil')->orderBy('titulo')->get();
```

```sql
SELECT * FROM libros WHERE tema = ? ORDER BY titulo ASC
```

El `?` no es un adorno: Eloquent arma una consulta preparada, siempre, por
el motivo del capítulo @cap:pdo. El valor viaja separado del comando.

:::key
El ORM no te ahorra saber SQL. Te ahorra **escribir** el SQL repetitivo:
el `SELECT` de cinco columnas, el `INSERT` con ocho campos, el `JOIN`
obvio.

El SQL que importa lo sigue escribiendo alguien. La diferencia es que, con
el ORM, solo tienes que escribir lo interesante.
:::

## El model y las convenciones

```php title="app/Models/Libro.php" numbered
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Libro extends Model
{
    protected $fillable = [
        'titulo', 'autor', 'isbn', 'tema', 'anio',
    ];
}
```

Seis líneas útiles, y el model ya sabe leer y grabar. Las convenciones que
asumió:

| Convención | Valor asumido |
|---|---|
| tabla | plural del nombre de la clase |
| clave primaria | `id` |
| fechas | `created_at` y `updated_at` |

Tabla: Todas se pueden ajustar, y la primera hay que ajustarla con
frecuencia en un proyecto en español.

:::pitfall
El pluralizador de Laravel habla inglés. Resuelve `Libro` como `libros`
por casualidad —porque agregar una `s` funciona—, y se equivoca en el
resto:

| Clase | Laravel busca | La tabla se llama |
|---|---|---|
| `Libro` | `libros` | `libros` |
| `Ejemplar` | `ejemplars` | `ejemplares` |
| `Lector` | `lectors` | `lectores` |
| `Prestamo` | `prestamos` | `prestamos` |

Tabla: Dos aciertos y dos errores, y el error aparece como
`Table 'casa_amarela.ejemplars' doesn't exist` en la primera consulta.

La corrección es una línea, y vale la pena declararla **en todos los
models** de un proyecto en español, incluso en los que saldrían bien, para
que nadie tenga que recordar cuáles son cuáles:

```php
protected $table = 'ejemplares';
```
:::

## Active Record: el objeto que sabe guardarse

```php
$libro = new Libro();
$libro->titulo = 'Vidas Secas';
$libro->autor = 'Graciliano Ramos';
$libro->tema = 'literatura';
$libro->save();
```

```sql
INSERT INTO libros (titulo, autor, tema, updated_at, created_at)
VALUES (?, ?, ?, ?, ?)
```

```php
$libro->anio = 1938;
$libro->save();
```

```sql
UPDATE libros SET anio = ?, updated_at = ? WHERE id = ?
```

El mismo método hace las dos cosas, y el objeto decide cuál según exista o
no la clave. Eso es el patrón **Active Record**: el registro y el
comportamiento en el mismo objeto.

Es cómodo y tiene un costo que aparece en dos puntos. El objeto lleva una
dependencia de la base adondequiera que vaya, y probar la regla que vive
dentro de él exige base. Es la razón por la que este libro mantiene la
regla de negocio en servicios, y usa el model para lo que hace bien: ir y
volver de la tabla.

## Buscar, y el `null` que se escapa

| Método | SQL | Cuando no encuentra |
|---|---|---|
| `find(12)` | `WHERE id = ?` | devuelve `null` |
| `findOrFail(12)` | `WHERE id = ?` | lanza, y se vuelve `404` |
| `first()` | `LIMIT 1` | devuelve `null` |
| `firstOrFail()` | `LIMIT 1` | lanza, y se vuelve `404` |
| `value('titulo')` | `SELECT titulo ... LIMIT 1` | devuelve `null` |

Tabla: Los cuatro primeros difieren en una sola cosa, y es la más
importante.

```php
$libro = Libro::find($id);

echo $libro->titulo;
```

```text
Attempt to read property "titulo" on null
```

El `find` devolvió `null` y el error aparece en la línea siguiente, o
treinta líneas después, o en la vista. La versión con `OrFail` falla en el
lugar correcto, con la respuesta correcta:

```php
$libro = Libro::findOrFail($id);
```

```text
404 Not Found
```

:::key
Usa `find` cuando `null` sea **una respuesta posible** que vas a tratar
ahí mismo. Usa `findOrFail` cuando la ausencia sea un error.

En la práctica, dentro de un controller con el route model binding del
capítulo @cap:rotas-e-controllers, rara vez escribes cualquiera de los dos:
el framework ya buscó.
:::

Y el método que parece inofensivo y no lo es:

```php
Libro::all();
```

```sql
SELECT * FROM libros
```

Cuatro mil filas en memoria para mostrar veinte. En una tabla de préstamos
con años de historial, es la consulta que tumba el servidor un martes a la
tarde. El `paginate(20)` existe para eso.

## Mass assignment

Volvamos al `perfil=admin`.

```php
Lector::create($request->all());
```

El `create` recibe un array y llena el registro con él. La pregunta es:
**¿qué campos acepta?**

```php
protected $fillable = ['nombre', 'documento', 'telefono'];
```

Con `$fillable`, acepta esos tres e **ignora en silencio** cualquier otro.
El `perfil` que mandó Tainá se descarta.

La alternativa, `$guarded`, es la lista de lo que **no** se puede llenar, y
`$guarded = []` quiere decir "nada está prohibido", que es exactamente lo
que decía el model de `Lector`.

:::pitfall
`$guarded = []` aparece en los tutoriales porque quita un obstáculo de
quien está aprendiendo. Convierte cada columna de la tabla en un campo
público de formulario.

El daño depende de lo que exista en la tabla: `perfil`, `saldo`,
`aprobado`, `id_de_la_empresa`. En cualquier sistema con más de un nivel de
acceso, esa línea es una escalada de privilegios esperando a alguien
curioso.

La regla: **`$fillable` siempre, con la lista escrita a mano.** Escribir la
lista es el momento en que decides, campo por campo, qué puede llenar el
mundo de fuera.
:::

Y existe una protección más, que convierte el descarte silencioso en un
error:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Model::preventSilentlyDiscardingAttributes(
        ! $this->app->isProduction()
    );
}
```

En desarrollo, mandar un campo que no está en el `$fillable` pasa a lanzar
una excepción. Es como descubres, en tu máquina, que el formulario está
enviando un campo que el model ignora, en lugar de descubrirlo por la
ausencia del dato tres semanas después.

## Casts: el tipo correcto de los dos lados

La base guarda texto, números y fechas. Tu código quiere enums y objetos de
valor. El `casts()` es la traducción, en los dos sentidos:

```php title="app/Models/Ejemplar.php" numbered
protected function casts(): array
{
    return [
        'condicion' => EstadoEjemplar::class,
        'adquirido_en' => 'immutable_date',
    ];
}
```

```php
$ejemplar = Ejemplar::find(1);

$ejemplar->condicion;              // EstadoEjemplar::Bueno
$ejemplar->condicion->etiqueta();  // 'Disponible'
$ejemplar->adquirido_en;           // DateTimeImmutable
```

La columna sigue siendo `VARCHAR(20)` con `'bueno'` dentro. Lo que cambia
es que ningún punto de tu código vuelve a comparar un string suelto: la
lección del capítulo @cap:enums-datas-e-valores pasa a valer también en la
frontera de la base.

Para el `Dinero`, que no es enum ni fecha, la conversión es una clase:

```php title="app/Casts/DineroCast.php" numbered
<?php

declare(strict_types=1);

namespace App\Casts;

use App\Prestamos\Dinero;
use Illuminate\Contracts\Database\Eloquent\CastsAttributes;

class DineroCast implements CastsAttributes
{
    public function get($model, $clave, $valor, $atributos): ?Dinero
    {
        return $valor === null
            ? null
            : Dinero::enCentavos((int) $valor);
    }

    public function set($model, $clave, $valor, $atributos): ?int
    {
        return $valor?->centavos;
    }
}
```

```php
'multa_en_centavos' => DineroCast::class,
```

Ahora `$prestamo->multa_en_centavos` devuelve un `Dinero`, con
`formateado()` y `mas()`, y la suma con un entero de días, que el capítulo
@cap:enums-datas-e-valores cerró, sigue cerrada después de pasar por la
base.

## Accessor: un valor calculado con cara de columna

```php title="app/Models/Prestamo.php" numbered
use Illuminate\Database\Eloquent\Casts\Attribute;

protected function diasDeAtraso(): Attribute
{
    return Attribute::make(
        get: fn (): int => max(
            0,
            $this->devolver_hasta->diffInDays(now(), absolute: false),
        ),
    );
}
```

```php
$prestamo->dias_de_atraso;   // 3
```

Parece una columna y no lo es: se calcula en cada lectura. Vale la pena
cuando el valor se deriva de otros que ya están en la tabla, y es
exactamente la razón por la que no existe una columna `dias_de_atraso`, por
el motivo del capítulo @cap:duas-tabelas-conversando: un número calculado
no diverge de la realidad.

## Scope: la consulta que recibe un nombre

```php title="app/Models/Prestamo.php" numbered
use Illuminate\Database\Eloquent\Builder;

public function scopeAbiertos(Builder $q): void
{
    $q->whereNull('devuelto_en');
}

public function scopeVencidos(Builder $q): void
{
    $q->whereDate('devolver_hasta', '<', now());
}
```

```php
Prestamo::abiertos()->vencidos()->count();
```

```sql
SELECT COUNT(*) FROM prestamos
WHERE devuelto_en IS NULL AND date(devolver_hasta) < ?
```

El prefijo `scope` desaparece en la llamada, y los dos se combinan en
cualquier orden.

La ganancia es la de siempre: la definición de "abierto" pasa a vivir en un
solo lugar. El día en que un préstamo cancelado también cuente como
cerrado, el cambio es una línea, y no una búsqueda de
`whereNull('devuelto_en')` en diecisiete archivos.

## Ver el SQL antes de confiar

```php
Libro::where('tema', 'infantil')->orderBy('titulo')->toSql();
```

```text
select * from `libros` where `tema` = ? order by `titulo` asc
```

Para ver todo lo que hizo la petición, con los valores y el tiempo:

```php title="app/Providers/AppServiceProvider.php" numbered
if ($this->app->environment('local')) {
    DB::listen(function ($consulta): void {
        Log::debug($consulta->sql, [
            'valores' => $consulta->bindings,
            'ms' => $consulta->time,
        ]);
    });
}
```

:::key
Activa esto el primer día de cualquier proyecto con ORM y mira el log
después de abrir tres pantallas.

Es la forma más rápida de descubrir que el listado de préstamos está
haciendo doscientas una consultas, y ese número tiene nombre, tiene una
causa conocida y es el tema del próximo capítulo.
:::

## El model gigante: las señales

El model empieza con seis líneas y, si nadie dice nada, llega a
trescientas. Tres señales de que eso pasó:

**Tiene métodos que no hablan con la base.** Cálculo de multa, regla de
límite, decisión de plazo. Nada de eso necesita una tabla para existir, y
todo eso pasa a necesitarla cuando vive ahí.

**Importa cosas que no son datos.** Un model que usa `Mail`, `Http` o
`Storage` dejó de representar una fila y se volvió un proceso.

**Tiene un método que no puedes probar sin base.** Esta es la señal más
confiable, porque es verificable: si para revisar la regla de la multa
necesitas insertar un préstamo, la regla está en el lugar equivocado.

La salida no es partir el model en cinco. Es **sacar de ahí lo que no es
persistencia**: la regla va al servicio o al objeto de valor, y el model se
queda con las columnas, los casts, los scopes y las relaciones.

:::note En tu carrera
"¿Model gordo o controller gordo?" es una discusión sin fin, y es la
pregunta equivocada. Las dos respuestas juntan dos cosas que cambian por
motivos distintos: la forma de guardar y la regla del negocio.

La prueba que lo resuelve, y que puedes aplicar en cualquier proyecto:
**si la Casa Amarela cambiara MySQL por otra cosa, ¿cuánto del código
tendría que cambiar?** Todo lo que tuviera que cambiar es persistencia. El
resto es regla, y la regla no debería estar en un archivo que solo existe
por culpa de una tabla.

No es un argumento sobre pureza: es sobre dónde la prueba sale barata.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/
    Models/
      Libro.php        # $table, $fillable
      Ejemplar.php     # cast del enum
      Lector.php       # $fillable sin perfil
      Prestamo.php     # scopes, accessor, cast de Dinero
    Casts/
      DineroCast.php
    Providers/
      AppServiceProvider.php  # DB::listen y la protección de atributos
:::

:::summary
- Todo método de Eloquent produce una consulta, y es preparada.
- El pluralizador habla inglés: declara `$table` en un proyecto en
  español.
- Active Record pone el registro y el comportamiento en el mismo objeto:
  cómodo para persistir, caro para probar la regla.
- `find` devuelve `null`; `findOrFail` lanza y se vuelve `404`.
- `all()` trae la tabla entera a la memoria.
- `$fillable` es la lista de lo que el mundo de fuera puede llenar;
  `$guarded = []` es una escalada de privilegios esperando a alguien
  curioso.
- `preventSilentlyDiscardingAttributes` convierte el descarte en un error
  fuera de producción.
- Los casts convierten en los dos sentidos: enum, fecha inmutable y objeto
  de valor.
- El accessor es un valor calculado; el scope es una consulta con nombre, y
  los dos viven en un solo lugar.
- `toSql()` y `DB::listen` muestran lo que realmente se ejecutó.
- Un model que tiene reglas sin base, que llama a un servicio externo o que
  no se prueba sin tabla dejó de ser un model.
:::

:::checkpoint
Escribes consultas con Eloquent y muestras el SQL correspondiente,
proteges el registro con `$fillable`, conviertes enums y objetos de valor
con casts, le das nombre a una consulta con un scope, y reconoces por las
tres señales cuándo la regla se filtró dentro del model.
:::

:::exercise level=1
Escribe el SQL que produce cada llamada:

```php
Libro::where('anio', '>=', 2000)->count();
Ejemplar::where('condicion', 'bueno')->pluck('registro');
Lector::orderBy('nombre')->paginate(20);
Prestamo::whereNull('devuelto_en')->latest()->first();
```

:::answer
```sql
SELECT COUNT(*) FROM libros WHERE anio >= ?
```

```sql
SELECT registro FROM ejemplares WHERE condicion = ?
```

```sql
SELECT COUNT(*) FROM lectores;
SELECT * FROM lectores ORDER BY nombre ASC LIMIT 20 OFFSET 0
```

```sql
SELECT * FROM prestamos
WHERE devuelto_en IS NULL
ORDER BY created_at DESC LIMIT 1
```

Tres observaciones que separan a quien leyó de quien entendió.

El `pluck` trae **solo la columna pedida**, no la fila entera: es la
diferencia entre traer ocho mil filas completas y traer ocho mil números.

El `paginate` hace **dos** consultas: una cuenta el total, para saber
cuántas páginas hay, y otra trae la página. Es la causa más común de un
listado lento en una tabla grande, y la razón por la que existe el
`simplePaginate`, que prescinde del conteo.

Y el `latest()` ordena por `created_at`, no por `id`. En una base en la que
los registros se importaron fuera de orden, los dos resultados difieren.
:::

:::exercise level=2
El model `Lector` tiene `$guarded = []` y la tabla tiene las columnas
`nombre`, `documento`, `telefono`, `perfil` y `bloqueado_en`.

Corrige el model y escribe qué cambia en el controller del registro público
y en el controller de la pantalla de Vera, que **necesita** poder cambiar el
perfil.

:::answer
```php title="app/Models/Lector.php" numbered
class Lector extends Model
{
    protected $table = 'lectores';

    protected $fillable = ['nombre', 'documento', 'telefono'];

    protected function casts(): array
    {
        return ['bloqueado_en' => 'immutable_datetime'];
    }
}
```

El registro público no cambia **una línea**, y ese es el punto. Ya hacía
`Lector::create($datos)`, y ahora los campos de más se descartan.

La pantalla de Vera no usa asignación masiva para el perfil. Asigna
directamente, lo que ignora el `$fillable` a propósito:

```php
$lector->perfil = $request->enum('perfil', Perfil::class);
$lector->save();
```

Eso parece saltarse la protección y es exactamente el diseño correcto: el
`$fillable` protege contra **lo que viene de fuera en bloque**. La
asignación directa es una decisión escrita en el código, en un controller
al que solo llega quien tiene el permiso de Vera.

`bloqueado_en` queda fuera de los dos: cambia por una acción con nombre
—bloquear a un lector— y no por un formulario.
:::

:::exercise level=3
Este model llegó para revisión. Funciona.

```php
class Prestamo extends Model
{
    protected $guarded = [];

    public function calcularMulta(): float
    {
        $dias = (strtotime('now')
              - strtotime($this->devolver_hasta)) / 86400;

        if ($dias <= 0) {
            return 0;
        }

        $valor = $dias * 0.8;

        if ($this->lector->perfil === 'estudiante') {
            $valor = $valor / 2;
        }

        Mail::to($this->lector->email)
            ->send(new AvisoDeMulta($valor));

        return $valor;
    }
}
```

Señala los problemas por categoría —seguridad, corrección, diseño— y di
dónde debería vivir cada pedazo.

:::answer
**Seguridad.** `$guarded = []` otra vez, ahora en una tabla que tiene
`multa_en_centavos` y `devuelto_en`. Un cliente podría registrar un
préstamo ya devuelto, sin multa.

**Corrección.** Tres defectos, todos ya vistos:

La diferencia de fechas en segundos dividida por 86.400 ignora la zona
horaria y los días de cambio de horario, y devuelve un `float` con
decimales.

El valor en `float` acumula error con cada suma: la cuenta es en centavos.

Y `0.8` está suelto, divergiendo de `config/biblioteca.php`, que existe
desde el capítulo @cap:configuracao-ambiente-e-artisan.

**Diseño.** Dos problemas, y el segundo es grave.

El cálculo no necesita base para existir. Es regla, y está en un archivo
que solo existe por culpa de una tabla: entonces probar "media multa para
estudiantes" exige insertar préstamo, lector y ejemplar.

Y el método **manda un correo**. Un método llamado `calcularMulta` que le
manda un mensaje al lector es una sorpresa: cualquier informe que recorra
doscientos préstamos para sumar multas acaba de disparar doscientos
correos.

**Dónde va cada pedazo.**

La cuenta de días y el valor van a un servicio —`CalculadoraDeMultas`— que
recibe las fechas y la configuración y devuelve `Dinero`. Se prueba sin
base.

La regla del estudiante va junto, porque es regla de negocio, y se vuelve
un caso de prueba explícito.

El envío del aviso sale de aquí entero. Es una consecuencia de un
acontecimiento —se registró la multa—, no parte de calcular un número.

Y el model se queda con `$fillable`, los casts, los scopes y las
relaciones. Unas quince líneas.
:::
