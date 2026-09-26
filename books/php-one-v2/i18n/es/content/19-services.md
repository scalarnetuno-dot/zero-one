---
source_hash: b1a701cf24e5
title: "Services: donde vive la regla de negocio"
number: 19
slug: services
part: p5
kicker: "Vera leyó el método en voz alta y corrigió una regla que el equipo había entendido mal hacía cuatro meses. Tardó dieciocho segundos."
goal: >-
  Decidir dónde vive cada regla, sacar la regla de préstamo del controller y
  ponerla en un service que es una frontera de transacción y no conoce
  HTTP, y saber cuántas capas necesita realmente el proyecto.
---

## Un controller de ochocientas líneas empieza con veinte

El `PrestamoController::store` del capítulo @cap:o-crud-completo tenía dos
reglas —ejemplar disponible y límite por lector— y cabía en una pantalla.
Desde entonces:

- el Form Request le sacó la validación;
- el handler del capítulo @cap:erros-padronizados le sacó el armado del
  error;
- el enviador del capítulo anterior le agregó el aviso.

Y todavía faltan nueve de las once reglas de Vera. Si cada una entra en el
controller, el método llega a ciento cincuenta líneas antes del final de la
parte. El panel Blade, que también presta, tiene una copia. El comando
`biblioteca:multas`, que necesita saber si un lector tiene pendientes,
tiene una tercera versión de una de las reglas.

Ningún controller nace con ochocientas líneas. Llega ahí veinte líneas a
la vez, cada una razonable, y cada una puesta ahí porque era el lugar más
cercano a donde la persona estaba editando.

:::key
El síntoma no es el tamaño. Es **la misma regla en dos lugares**. En el
momento en que el panel y la API revisan el límite de préstamos cada uno a
su manera, la regla ya está mal en uno de ellos: solo no se sabe en cuál.
:::

## La regla que involucra dos entidades no cabe en el model

El primer intento de sacar la regla del controller suele ser el model.
Parece natural: el préstamo sabe prestarse.

```php
class Prestamo extends Model
{
    public static function realizar(
        Ejemplar $ejemplar,
        Lector $lector,
    ): self {
        // ...
    }
}
```

Mira lo que necesita consultar "realizar un préstamo":

| Regla | Pregunta a quién |
|---|---|
| ejemplar disponible | `Ejemplar` |
| no es de referencia | `Ejemplar` |
| no es el último del título | `Libro`, contando `Ejemplar` |
| límite de tres | `Prestamo`, filtrando por `Lector` |
| ninguno atrasado | `Prestamo`, filtrando por `Lector` |
| multa de más de cinco reales | `Multa`, filtrando por `Lector` |
| lector activo | `Lector` |

Tabla: Siete de las once reglas, y atraviesan cinco entidades. Ninguna de
ellas es dueña de la operación.

El `Prestamo::realizar` tendría que conocer a todos los otros models, y
`Prestamo` pasaría a ser el lugar donde vive toda la regla de circulación
de la biblioteca. Es el "model gigante" del capítulo @cap:eloquent, y llega
ahí por el mismo camino que el controller: una regla razonable a la vez.

La regla que funciona:

**La regla que habla de una sola entidad queda en ella.** "¿El ejemplar
está disponible?" es una pregunta sobre el ejemplar:
`$ejemplar->disponible()`. "¿El préstamo está atrasado?" es sobre el
préstamo: `$p->conAtraso()`.

**La regla que coordina varias entidades va a un service.** "¿Este lector
puede llevarse este ejemplar ahora?" no pertenece a ninguna de las dos.

## El service

```php title="app/Prestamos/PrestamoService.php" numbered
<?php

declare(strict_types=1);

namespace App\Prestamos;

use App\Avisos\EnviadorDeAviso;
use App\Models\Ejemplar;
use App\Models\Lector;
use App\Models\Prestamo;
use Illuminate\Support\Facades\DB;

final class PrestamoService
{
    public function __construct(
        private readonly ReglasDeCirculacion $reglas,
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function realizar(
        int $ejemplarId,
        int $lectorId,
        ?Autorizacion $autorizacion = null,
    ): Prestamo {
        $prestamo = DB::transaction(function () use (
            $ejemplarId, $lectorId, $autorizacion,
        ) {
            $ejemplar = Ejemplar::with('libro')
                ->lockForUpdate()
                ->findOrFail($ejemplarId);

            $lector = Lector::lockForUpdate()
                ->findOrFail($lectorId);

            $this->exigirEjemplarPrestable(
                $ejemplar, $autorizacion,
            );
            $this->exigirLectorAlDia($lector);

            $plazo = $this->reglas->plazoPara($lector);

            $prestamo = Prestamo::create([
                'ejemplar_id' => $ejemplar->id,
                'lector_id' => $lector->id,
                'retirado_en' => now(),
                'devolver_hasta' => now()->addDays($plazo),
                'autorizado_por' => $autorizacion?->usuarioId,
            ]);

            $ejemplar->marcarPrestado();

            return $prestamo;
        });

        $this->avisos->enviar(
            $prestamo->lector,
            'Préstamo hecho. Devuélvelo hasta el '
                . $prestamo->devolver_hasta->format('d/m') . '.',
        );

        return $prestamo;
    }

    // ...
}
```

Tres cosas para leer con atención.

**La firma recibe números, no un `Request`.** El service no sabe si lo
llamó la API, el panel, el comando Artisan o una prueba.

**El método público es la transacción.** Todo lo que tiene que ser verdad
junto está dentro del `DB::transaction`. El aviso está **afuera**, y eso es
una decisión: si se cae el proveedor de mensajes, el préstamo no debe
deshacerse. La lectora tiene el libro en la mano.

**Las revisiones tienen nombre.** `exigirEjemplarPrestable` y
`exigirLectorAlDia` son métodos privados que lanzan las excepciones de
dominio del capítulo @cap:erros-padronizados:

```php title="app/Prestamos/PrestamoService.php" numbered
private function exigirLectorAlDia(Lector $lector): void
{
    if (!$lector->activo()) {
        throw new LectorInactivo($lector->id);
    }

    if ($lector->prestamos()->conAtraso()->exists()) {
        throw new LectorConAtraso($lector->id);
    }

    $multa = $lector->multaAbierta();

    if ($multa->mayorQue($this->reglas->multaMaxima())) {
        throw new LectorConPendiente($lector->id, $multa);
    }

    $abiertos = $lector->prestamos()->abiertos()->count();
    $limite = $this->reglas->limitePara($lector, now());

    if ($abiertos >= $limite) {
        throw new LimiteDePrestamosAlcanzado(
            $lector->id, $limite, $abiertos,
        );
    }
}
```

Cada `if` es una frase de Vera. Léelo de arriba abajo y es el capítulo
@cap:condicionais, con cláusulas de guarda, sin ningún `else`.

Y `ReglasDeCirculacion` guarda los números —plazo, límite, multa máxima—
que dependen de la configuración y del calendario:

```php title="app/Prestamos/ReglasDeCirculacion.php" numbered
final class ReglasDeCirculacion
{
    public function limitePara(
        Lector $lector,
        DateTimeInterface $cuando,
    ): int {
        return (int) $cuando->format('n') === 1
            ? config('biblioteca.limite_en_enero')
            : config('biblioteca.limite_por_lector');
    }

    public function plazoPara(Lector $lector): int
    {
        return $lector->infantil()
            ? config('biblioteca.plazo_en_dias_infantil')
            : config('biblioteca.plazo_en_dias');
    }

    public function multaMaxima(): Dinero
    {
        return Dinero::enCentavos(500);
    }
}
```

Es pura: recibe lo que necesita, no consulta la base, no guarda estado. Es
lo que el capítulo @cap:testes va a probar en milisegundos.

:::story Dieciocho segundos
Dedé proyectó el `PrestamoService` en la pared de la sala de reuniones.
Vera había venido a entregar las fichas en papel del mes y se quedó en la
puerta.

—Léemelo —dijo.

—¿Todo?

—La parte del ejemplar.

Dedé bajó hasta el `exigirEjemplarPrestable` y lo leyó, traduciendo el
código en voz alta:

—Si no está disponible, no sale. Si es de referencia, no sale. Si es de la
colección de don Juvenal, no sale. Si llegó hace menos de siete días, no
sale. Si es el último ejemplar del título, no sale.

—Para.

Dedé se detuvo.

—El último no es "no sale". Es "sale con autorización". Yo autorizo, o
Neide cuando no estoy. Si la persona lo necesita para el trabajo de la
escuela, sale.

Tainá abrió el cuaderno en la página de la primera semana. Decía:
*"último ejemplar — solo c/ autoriz."*. Lo había anotado bien. Alguien, en
el camino entre el cuaderno y el código, había perdido la segunda mitad de
la frase.

—¿Desde cuándo está así? —preguntó Márcia.

—Desde octubre —dijo Dedé—. Cuatro meses.

Vera ya se iba.

—¿Y doña Marlene?

—¿Doña Marlene qué es?

—Es autorización también. La miro y autorizo.
:::

## La regla corregida, y la regla que no era regla

La corrección de Vera cupo en dieciocho segundos porque la regla cabía en
una pantalla y estaba escrita en el orden en que ella piensa. En un
controller de ochocientas líneas, con la regla repartida entre tres
archivos, nadie se la habría leído, y ella no la habría encontrado.

```php title="app/Prestamos/PrestamoService.php" numbered
private function exigirEjemplarPrestable(
    Ejemplar $ejemplar,
    ?Autorizacion $autorizacion,
): void {
    if (!$ejemplar->disponible()) {
        throw new EjemplarNoDisponible(
            $ejemplar->registro, $ejemplar->condicion,
        );
    }

    if ($ejemplar->deReferencia()
        || $ejemplar->deColeccionCerrada()) {
        throw new EjemplarNoCircula($ejemplar->registro);
    }

    if ($ejemplar->enExhibicion(now())) {
        throw new EjemplarEnExhibicion(
            $ejemplar->registro, $ejemplar->exhibicionHasta(),
        );
    }

    if ($ejemplar->libro->ultimoDisponible($ejemplar)
        && $autorizacion === null) {
        throw new UltimoEjemplarExigeAutorizacion(
            $ejemplar->registro,
        );
    }
}
```

Y la segunda frase de Vera resuelve un problema que el equipo cargaba desde
el capítulo @cap:condicionais: la regla de doña Marlene. Nunca fue una
regla. Era Vera **ejerciendo su criterio**, y el criterio no se programa,
se registra.

El objeto `Autorizacion` es ese registro:

```php title="app/Prestamos/Autorizacion.php" numbered
final readonly class Autorizacion
{
    public function __construct(
        public int $usuarioId,
        public string $motivo,
    ) {}
}
```

Quién autorizó y por qué. Se graba en el préstamo (`autorizado_por`), y el
informe de fin de mes puede responder "cuántos préstamos salieron por
autorización, y de quién". La excepción de doña Marlene se volvió un dato,
con nombre, y dejó de ser una leyenda del mostrador.

:::key
No toda regla del especialista es una regla del sistema. Algunas son
**criterio**: decisiones que la persona toma mirando el caso. Intentar
programarlas produce `if ($lector->nombre === 'Marlene')`.

El sistema no necesita decidir el criterio. Necesita **permitir** que lo
ejerza quien tiene autoridad y **registrar** que se ejerció.
:::

## El service no conoce HTTP

Con el service listo, el controller vuelve al tamaño que debía tener:

```php title="app/Http/Controllers/PrestamoController.php" numbered
public function store(
    RealizarPrestamoRequest $request,
    PrestamoService $prestamos,
) {
    $prestamo = $prestamos->realizar(
        $request->integer('ejemplar_id'),
        $request->integer('lector_id'),
    );

    return (new PrestamoResource($prestamo))
        ->response()
        ->setStatusCode(201)
        ->header(
            'Location',
            route('prestamos.show', $prestamo),
        );
}
```

El controller traduce HTTP en una llamada de método, y el resultado del
método en HTTP. Las excepciones que lanza el service atraviesan el
controller sin que las toque y llegan al handler, que las convierte en
`409`.

La lista de lo que el service **no** puede tener:

- `Request` o `$request` en ningún lugar;
- `abort()`, `response()`, status HTTP;
- `session()`, `redirect()`, `back()`;
- `auth()->user()`: quién es el usuario es un parámetro, no una consulta.

El último es el más tentador. `auth()->user()` funciona dentro del service
cuando lo llama la API, y devuelve `null` cuando lo llama el comando
Artisan a las tres de la mañana. El service pasa a depender de estar dentro
de una petición, y nadie lo nota hasta que el comando falla.

El panel Blade del capítulo @cap:blade llamaba a un `RegistroDePrestamo`,
que era un borrador de esto. Ahora llama al mismo `PrestamoService`, y le
pasa la `Autorizacion` cuando Vera marca la casilla "autorizado por mí". La
API de la aplicación nunca la pasa: el lector no se autoriza a sí mismo.

## Un método público, una transacción

`renovar()` y `devolver()` siguen el mismo molde:

```php title="app/Prestamos/PrestamoService.php" numbered
public function devolver(
    int $prestamoId,
    DateTimeImmutable $cuando,
): Prestamo {
    return DB::transaction(function () use (
        $prestamoId, $cuando,
    ) {
        $prestamo = Prestamo::with('ejemplar')
            ->lockForUpdate()
            ->findOrFail($prestamoId);

        if ($prestamo->devuelto()) {
            throw new PrestamoYaDevuelto($prestamoId);
        }

        $multa = $this->reglas->multaPor(
            $prestamo->plazo(), $cuando,
        );

        $prestamo->registrarDevolucion($cuando, $multa);
        $prestamo->ejemplar->marcarDisponible();

        return $prestamo;
    });
}
```

El `$cuando` viene de afuera por el motivo del capítulo
@cap:enums-datas-e-valores: quien llama decide qué hora es. La API pasa
`now()`; la prueba pasa una fecha fija; Vera, escribiendo el lunes las
devoluciones del buzón del fin de semana, pasa la fecha en que dejaron el
libro en el buzón.

:::pitfall
Un `DB::transaction` dentro de un método **privado** es la forma más común
de romper la frontera.

```php
public function devolverVarios(array $ids): void
{
    foreach ($ids as $id) {
        $this->devolverUno($id); // transacción ahí adentro
    }
}
```

Si el quinto falla, los cuatro primeros ya se confirmaron. Quien llamó a
`devolverVarios` recibe una excepción y no sabe que la mitad ocurrió. La
regla: **la transacción es del método público**, porque es él quien le
promete una operación entera a quien llama.
:::

## Repository: cuándo ayuda y cuándo es burocracia

En casi todo tutorial de arquitectura en PHP aparece una capa más:

```php
interface PrestamoRepository
{
    public function find(int $id): ?Prestamo;
    public function save(Prestamo $p): void;
    public function abiertosDelLector(int $lectorId): Collection;
}

class EloquentPrestamoRepository implements PrestamoRepository
{
    public function find(int $id): ?Prestamo
    {
        return Prestamo::find($id);
    }
    // ...
}
```

La promesa es aislar la base: el service habla con el repositorio, y el
repositorio se puede cambiar por otro: otra base, otra fuente, una
implementación en memoria para las pruebas.

En un proyecto Laravel, esa promesa hay que pesarla contra lo que Eloquent
ya es. El model **ya es** un repositorio: `Prestamo::find`,
`Prestamo::abiertos()`, `$p->save()`. El repositorio de arriba es un
archivo que le pasa cada método a otro, con una interfaz delante y un
`bind` en el provider.

**Ayuda cuando** la fuente del dato de verdad puede cambiar —el acervo que
hoy está en la base y mañana viene de una API de la municipalidad—, o
cuando la consulta es lo bastante complicada como para merecer nombre y
prueba propios.

**Es burocracia cuando** existe para "seguir la arquitectura", en un
proyecto con una base que no va a cambiar, y cada método es una línea que
llama a Eloquent.

La Casa Amarela no tiene repositorio. Los scopes del capítulo @cap:eloquent
les dan nombre a las consultas, y el capítulo @cap:testes muestra cómo
probar las reglas sin necesitar un repositorio falso: separando la regla
pura de la consulta.

## No todo proyecto necesita todas las capas

```text
Route → Controller → Service → Model → Base
```

Cinco capas. Para la Casa Amarela, cada una tiene un motivo:

| Capa | Existe porque |
|---|---|
| Controller | traduce HTTP; hay dos clientes (API y panel) |
| Service | la regla atraviesa cinco entidades y tres puertas |
| Model | el dato y las preguntas de una sola entidad |

Tabla: La pregunta no es "cuál es la arquitectura correcta", es "qué
compra cada capa en este proyecto".

¿Y para las rutas del CRUD del acervo? `LibroController::store` recibe el
Form Request y llama a `Libro::create`. No hay una regla que atraviese
entidades, no hay un segundo cliente, no hay una transacción con dos
escrituras. Un `LibroService` con un método `crear` que llama a
`Libro::create` sería una capa que solo pasa de largo, y sería lo primero
que el capítulo siguiente llamaría síntoma.

:::term Action class
Una alternativa al service cuando empieza a juntar operaciones sin
relación entre sí: una clase por operación, con un solo método.

`RealizarPrestamo`, `RenovarPrestamo`, `DevolverPrestamo` en lugar de
`PrestamoService` con los tres. Funciona mejor cuando cada operación tiene
dependencias distintas; es un exceso cuando las tres lo comparten todo.
:::

## El service sin propósito: cómo reconocerlo

Tres señales, y basta una:

**Todo método tiene una línea**, y la línea llama al model. El service no
hace nada que el controller no pudiera hacer directamente.

**El nombre es el nombre de una tabla** —`LibroService`,
`UsuarioService`—, y los métodos son `crear`, `actualizar`, `borrar`,
`listar`. Es el CRUD otra vez, con un archivo más.

**Recibe un `Request`.** Entonces no es un service; es el controller en otro
archivo.

El `PrestamoService` pasa las tres: sus métodos coordinan varias entidades,
el nombre es el de una operación de negocio, y no sabe qué es HTTP.

:::note En tu carrera
La arquitectura en una entrevista suele volverse una lista de capas
recitada. Lo que impresiona a quien está del otro lado es lo contrario:
saber decir **por qué no** poner una capa.

"Creé un service para el préstamo porque la regla atraviesa cinco
entidades y tres puertas de entrada; no lo creé para el registro de libros
porque es una línea de Eloquent, y una capa que solo pasa de largo es costo
sin beneficio." Esa frase muestra criterio. "Siempre uso Controller,
Service y Repository" muestra que seguiste un tutorial.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Prestamos/
    PrestamoService.php          # realizar, renovar, devolver
    ReglasDeCirculacion.php      # pura: plazo, límite, multa
    Autorizacion.php             # el criterio, registrado
    EjemplarNoCircula.php
    EjemplarEnExhibicion.php
    UltimoEjemplarExigeAutorizacion.php
    LectorInactivo.php
    LectorConAtraso.php
    PrestamoYaDevuelto.php
  app/Http/Controllers/
    PrestamoController.php       # traduce HTTP, y nada más
:::

:::summary
- El síntoma no es el tamaño del controller; es la misma regla en dos
  lugares.
- La regla de una entidad queda en el model; la regla que coordina varias
  va a un service.
- El método público del service es la frontera de la transacción; los
  efectos que no deben deshacer la operación quedan fuera de ella.
- El service recibe valores, no un `Request`; no conoce `abort`, sesión ni
  `auth()`.
- Las excepciones de dominio atraviesan el controller intactas y el handler
  las traduce.
- Algunas reglas del especialista son criterio: el sistema permite y
  registra, no decide.
- `DB::transaction` en un método privado rompe la promesa del método
  público.
- Un repository sobre Eloquent es pasar de largo, salvo cuando la fuente
  del dato de verdad puede cambiar.
- Cada capa necesita un motivo en el proyecto; el CRUD simple no necesita
  service.
:::

:::checkpoint
La regla de préstamo está en un service que puedes leer en voz alta a quien
entiende del negocio, la transacción es la del método público, el
controller solo traduce HTTP, y sabes justificar, para cada capa del
proyecto, por qué existe, y por qué el registro de libros no tiene service.
:::

:::exercise level=1
Di dónde debe vivir cada regla: en el model, en `ReglasDeCirculacion`, en
`PrestamoService` o en el Form Request.

1. Un ejemplar está en exhibición si llegó hace menos de siete días.
2. El límite de préstamos es cinco en enero y tres el resto del año.
3. `lector_id` tiene que ser un entero que existe en la tabla.
4. Un lector con un préstamo atrasado no puede llevarse otro libro.
5. El plazo de devolución es de siete días para los lectores infantiles.

:::answer
1. Model `Ejemplar`, en un método `enExhibicion($cuando)`. Es una pregunta
   sobre un solo ejemplar, y depende de un dato suyo.
2. `ReglasDeCirculacion`. Es un número que depende de la configuración y
   del calendario, y no de una consulta.
3. Form Request. Es formato, con un pie en la base.
4. `PrestamoService`. La pregunta involucra al lector y a sus préstamos, y
   tiene que hacerse dentro de la transacción.
5. `ReglasDeCirculacion`, consultando `$lector->infantil()`, que a su vez
   vive en el model `Lector`.

El ítem 5 muestra la división en dos partes: "¿este lector es infantil?" es
una pregunta del model; "¿cuál es el plazo para los infantiles?" es una
regla de circulación.
:::

:::exercise level=2
Escribe el `renovar()` del `PrestamoService` con las reglas: solo se renueva
si no está atrasado; como máximo dos renovaciones; no se renueva si hay una
reserva para el libro. La nueva fecha se cuenta a partir de hoy, con el
plazo del lector.

:::answer
```php title="app/Prestamos/PrestamoService.php" numbered
public function renovar(
    int $prestamoId,
    DateTimeImmutable $cuando,
): Prestamo {
    return DB::transaction(function () use (
        $prestamoId, $cuando,
    ) {
        $p = Prestamo::with(['lector', 'ejemplar.libro'])
            ->lockForUpdate()
            ->findOrFail($prestamoId);

        if ($p->devuelto()) {
            throw new PrestamoYaDevuelto($p->id);
        }

        if ($p->conAtraso($cuando)) {
            throw new RenovacionDeAtrasado($p->id);
        }

        if ($p->renovaciones >= 2) {
            throw new RenovacionAgotada($p->id, 2);
        }

        if ($p->ejemplar->libro->tieneReservaActiva()) {
            throw new LibroReservado($p->ejemplar->libro_id);
        }

        $dias = $this->reglas->plazoPara($p->lector);

        $p->renovarHasta($cuando->modify("+{$dias} days"));

        return $p;
    });
}
```

El `2` suelto merece ir a `ReglasDeCirculacion` la próxima vez que alguien
pase por aquí: Vera ya mencionó que en las vacaciones escolares son tres.

La reserva se revisa en el **libro**, no en el ejemplar: quien reserva
quiere "un *Dom Casmurro*", cualquiera. Revisarla en el ejemplar dejaría
renovar siempre, porque nadie reserva un registro específico.
:::

:::exercise level=3
Un proyecto que acabas de tomar tiene esta estructura para el registro de
autores:

```text
AutorController → AutorService → AutorRepositoryInterface
                                → EloquentAutorRepository → Autor
```

El `AutorService` tiene `listar`, `buscar`, `crear`, `actualizar` y
`borrar`; cada uno llama al método del mismo nombre en el repositorio, que
llama a Eloquent. Son cuatro archivos y un `bind` para un CRUD.

La persona que lo escribió defiende que "es la arquitectura del proyecto" y
que "así es fácil cambiar la base". Escribe tu posición en la revisión,
incluido lo que **no** cambiarías ahora.

:::answer
**La posición.** Las dos capas del medio no compran nada en este caso. El
service no coordina entidades, no abre una transacción con dos escrituras,
no aplica reglas; el repositorio le pasa todo a Eloquent, que ya es un
repositorio. Son dos archivos y una interfaz por donde tiene que pasar todo
cambio en el registro de autores, sin proteger nada.

**Sobre cambiar la base.** El cambio de base que necesita Laravel —de MySQL
a PostgreSQL— Eloquent ya lo hace sin repositorio. El cambio que permitiría
el repositorio —de la base a otra cosa— no está en el horizonte de nadie,
y si lo está, es más barato introducir el repositorio ese día, para esa
entidad, que mantener la capa en todas por hipótesis.

**Lo que no cambiaría ahora.** No reescribiría los otros módulos que siguen
el mismo patrón. "Es la arquitectura del proyecto" es un argumento real: la
consistencia tiene valor, y un proyecto con la mitad de las entidades en un
patrón y la mitad en otro es más difícil de leer que un proyecto entero en
un patrón excesivo.

La propuesta que llevaría al equipo es otra: **para el código nuevo**, capa
solo cuando haya un motivo escrito: "service porque la regla atraviesa X e
Y". El patrón viejo muere solo, módulo a módulo, cuando alguien tenga que
tocar uno de verdad.

Y anotaría una pregunta para hacer en privado, no en la revisión: si el
patrón vino de una decisión con un motivo que no conozco. A veces viene.
:::
