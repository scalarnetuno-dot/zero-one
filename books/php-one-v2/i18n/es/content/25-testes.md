---
source_hash: a7ac311435dc
title: "Pruebas: qué estamos intentando probar"
number: 25
slug: testes
part: p7
kicker: "La multa por devolución adelantada se había corregido en octubre. En febrero volvió por otro camino. Había corrección; no había prueba."
goal: >-
  Escribir pruebas rápidas sobre la regla de negocio, sin base y sin HTTP:
  separar la decisión de la consulta, cubrir las once condiciones con una
  tabla de casos, elegir el doble correcto, y convertir cada defecto
  corregido en una prueba que impide que vuelva.
---

:::story Tres días antes
Doña Marlene devolvió *El tiempo y el viento* tres días antes del plazo, un
viernes, por el buzón de devolución que está afuera. El lunes, Neide
registró las devoluciones del buzón en el panel, indicando la fecha en que
los libros se habían dejado.

El martes, doña Marlene recibió por la aplicación un aviso de multa de
R$ 2,40.

—Tres días de multa —dijo Vera, con el celular de doña Marlene en la
mano— por devolver tres días antes.

Dedé reconoció el número antes de abrir el código. Tainá también.

—El `diff` sin signo —dijo ella—. Eso lo corregimos. En octubre. Me
acuerdo, fue el ejercicio del `PlazoDePrestamo`.

—Se corrigió en el `PlazoDePrestamo` —dijo Dedé, abriendo el archivo
nuevo—. Este es el registro de devolución del buzón. Alguien escribió el
cálculo otra vez.

—¿Quién?

Dedé miró el historial.

—Yo. En enero. Con prisa.

Leyó el fragmento en voz alta:

```php
$dias = $devolverHasta->diff($dejadoEn)->days;
$multa = $dias * config('biblioteca.multa_diaria_en_centavos');
```

—¿Y por qué no se rompió nada cuando lo escribiste? —preguntó Vera.

—Porque no había nada que romper. La corrección de octubre estaba en el
código. No estaba en ninguna prueba.
:::

## Una prueba no demuestra que esté bien

Hay una expectativa sobre las pruebas automatizadas que las vuelve
decepcionantes: la de que demuestran que el código es correcto. No lo
demuestran. Una prueba verifica **un caso**, y el programa tiene infinitos.

Lo que la prueba demuestra es más modesto y más útil: **que un
comportamiento específico sigue ocurriendo**. Hoy, mañana, después del
próximo cambio de cualquier persona. La corrección de octubre era un
comportamiento —"una devolución adelantada no genera multa"— que existía
solo en la memoria de quien lo corrigió. Una prueba habría convertido esa
memoria en algo que la cadena verifica en cada commit.

:::key
Una prueba es una frase sobre el sistema, escrita de modo que la
computadora pueda verificarla. "Una devolución adelantada no genera
multa." Si la frase deja de ser verdad, alguien se entera **antes** que
doña Marlene.
:::

La pregunta que organiza este capítulo y el siguiente no es "cómo probar".
Es **qué estamos intentando probar**, y la respuesta a esa pregunta decide
qué tipo de prueba escribir, y dónde.

## Pest o PHPUnit: elige uno y síguelo

PHP tiene un framework de pruebas dominante, PHPUnit, y Laravel viene con
una capa sobre él, Pest, que cambia clases y métodos por funciones:

```php title="tests/Unit/DineroTest.php" numbered
<?php

use App\Prestamos\Dinero;

test('suma centavos sin perder precisión', function () {
    $total = Dinero::enCentavos(10)
        ->mas(Dinero::enCentavos(20));

    expect($total->centavos)->toBe(30);
});
```

Lo mismo en PHPUnit:

```php title="tests/Unit/DineroTest.php" numbered
final class DineroTest extends TestCase
{
    public function test_suma_centavos_sin_perder_precision(): void
    {
        $total = Dinero::enCentavos(10)
            ->mas(Dinero::enCentavos(20));

        $this->assertSame(30, $total->centavos);
    }
}
```

Los dos corren con el mismo comando, producen el mismo informe y prueban lo
mismo. Pest es más corto y se lee mejor en español, porque el nombre de la
prueba es una frase entre comillas, con tildes. PHPUnit es lo que vas a
encontrar en la mayor parte del código PHP más antiguo.

La Casa Amarela usa Pest. La elección correcta es la que el proyecto ya
usa; la equivocada es mezclar las dos.

```text
$ php artisan test

   PASS  Tests\Unit\DineroTest
  ✓ suma centavos sin perder precisión                   0.01s

  Tests:    1 passed (1 assertions)
  Duration: 0.08s
```

## Preparar, actuar, afirmar

Toda prueba tiene tres partes, y vale escribirlas separadas por una línea
en blanco:

```php title="tests/Unit/PlazoDePrestamoTest.php" numbered
test('devolución adelantada no genera días de atraso', function () {
    $plazo = new PlazoDePrestamo(
        retiro: new DateTimeImmutable('2026-02-02 10:00'),
        dias: 14,
    );

    $dias = $plazo->diasDeAtraso(
        new DateTimeImmutable('2026-02-13 18:00'),
    );

    expect($dias)->toBe(0);
});
```

**Preparar**: montar el mundo en que ocurre la prueba; el plazo, con fechas
fijas.

**Actuar**: hacer **una** cosa, la que se está probando.

**Afirmar**: verificar el resultado.

Una prueba con dos acciones está probando dos cosas, y cuando falle no va
a decir cuál. Una prueba sin afirmación pasa siempre, y es peor que ninguna
prueba, porque da la sensación de cobertura.

Fíjate en las fechas. Fijas, escritas en la prueba. Una prueba que usa
`now()` pasa hoy y falla el día 31 de un mes, o en el cambio de horario de
verano, o cuando corre cerca de la medianoche, y cada una de esas fallas
cuesta una mañana entenderla. El `PlazoDePrestamo` recibe la fecha de
afuera desde el capítulo @cap:enums-datas-e-valores, y esta es la razón.

## Probar la regla sin base y sin HTTP

El `PrestamoService` del capítulo @cap:services tiene las once condiciones
de Vera. Probarlo tal como está exige base: busca el ejemplar, cuenta
préstamos, suma multas. Cada prueba tendría que insertar libro, ejemplar,
lector y préstamos, y correr dentro de una transacción. Funciona, y cada
prueba tarda cien milisegundos. Con los cincuenta casos que piden las once
reglas, son cinco segundos, y la persona deja de correr la suite antes de
cada commit.

Pero fíjate en lo que hace el service: **consulta** y después **decide**.
La consulta necesita la base. La decisión no: solo necesita los números que
trajo la consulta. Lo que impide la prueba rápida es que las dos cosas
están en el mismo método.

La separación:

```php title="app/Prestamos/SituacionDelPedido.php" numbered
final readonly class SituacionDelPedido
{
    public function __construct(
        public EstadoEjemplar $estadoDelEjemplar,
        public bool $deReferencia,
        public bool $deColeccionCerrada,
        public ?DateTimeImmutable $adquiridoEn,
        public bool $ultimoDisponible,
        public bool $lectorActivo,
        public bool $lectorInfantil,
        public int $prestamosAbiertos,
        public int $prestamosAtrasados,
        public Dinero $multaPendiente,
    ) {}
}
```

```php title="app/Prestamos/PoliticaDePrestamo.php" numbered
final class PoliticaDePrestamo
{
    public function __construct(
        private readonly ReglasDeCirculacion $reglas,
    ) {}

    public function exigirPermitido(
        SituacionDelPedido $s,
        DateTimeImmutable $cuando,
        ?Autorizacion $autorizacion,
    ): void {
        // las mismas guardas del capítulo de services,
        // leyendo de $s en vez de consultar la base
    }
}
```

El service pasa a tener dos etapas: dentro de la transacción, arma la
`SituacionDelPedido` con las consultas bloqueadas; después, se la entrega a
la política, que decide. La política no conoce la base, no conoce
Eloquent, no conoce HTTP. Recibe un objeto y una fecha, y lanza una
excepción o no la lanza.

:::key
El código difícil de probar suele estar diciendo algo sobre el diseño.
Aquí decía que consulta y decisión estaban mezcladas.

La separación no se hizo **para** la prueba. Deja la regla más clara para
que Vera la lea, y la prueba se volvió rápida como consecuencia.
:::

## Las once condiciones en menos de un segundo

Con la decisión aislada, una tabla de casos cubre todas las condiciones.
Pest lo llama *dataset*:

```php title="tests/Unit/PoliticaDePrestamoTest.php" numbered
function situacion(array $cambia = []): SituacionDelPedido
{
    return new SituacionDelPedido(...array_merge([
        'estadoDelEjemplar' => EstadoEjemplar::Bueno,
        'deReferencia' => false,
        'deColeccionCerrada' => false,
        'adquiridoEn' => new DateTimeImmutable('2020-01-01'),
        'ultimoDisponible' => false,
        'lectorActivo' => true,
        'lectorInfantil' => false,
        'prestamosAbiertos' => 0,
        'prestamosAtrasados' => 0,
        'multaPendiente' => Dinero::cero(),
    ], $cambia));
}
```

La función `situacion()` arma un pedido **que pasa**, y cada prueba cambia
solo lo que le interesa. Eso es lo que hace legible la tabla: cada fila
dice qué tiene de distinto respecto del caso normal.

```php title="tests/Unit/PoliticaDePrestamoTest.php" numbered
test('rechaza el pedido', function (
    array $cambia,
    string $excepcion,
) {
    $politica = new PoliticaDePrestamo(new ReglasDeCirculacion());

    $politica->exigirPermitido(
        situacion($cambia),
        new DateTimeImmutable('2026-03-10'),
        autorizacion: null,
    );
})->throws(ExcepcionDeDominio::class)->with([
    'ejemplar prestado' => [
        ['estadoDelEjemplar' => EstadoEjemplar::Prestado],
        EjemplarNoDisponible::class,
    ],
    'ejemplar de referencia' => [
        ['deReferencia' => true],
        EjemplarNoCircula::class,
    ],
    'llegó hace tres días' => [
        ['adquiridoEn' => new DateTimeImmutable('2026-03-07')],
        EjemplarEnExhibicion::class,
    ],
    'último sin autorización' => [
        ['ultimoDisponible' => true],
        UltimoEjemplarExigeAutorizacion::class,
    ],
    'lector con atraso' => [
        ['prestamosAtrasados' => 1],
        LectorConAtraso::class,
    ],
    'multa de R$ 5,01' => [
        ['multaPendiente' => Dinero::enCentavos(501)],
        LectorConPendiente::class,
    ],
    'tres abiertos en marzo' => [
        ['prestamosAbiertos' => 3],
        LimiteDePrestamosAlcanzado::class,
    ],
    // ... y las demás
]);
```

`throws` verifica la clase madre; para verificar la clase exacta de cada
caso, el cuerpo de la prueba la captura y la compara, una línea más que
queda a cargo del ejercicio 2.

Y los **bordes**, que es donde las reglas se equivocan:

```php title="tests/Unit/PoliticaDePrestamoTest.php" numbered
test('permite en el límite exacto de cada regla', function (
    array $cambia,
    string $cuando,
) {
    $politica = new PoliticaDePrestamo(new ReglasDeCirculacion());

    $politica->exigirPermitido(
        situacion($cambia),
        new DateTimeImmutable($cuando),
        autorizacion: null,
    );

    expect(true)->toBeTrue();
})->with([
    'multa de exactamente R$ 5,00' => [
        ['multaPendiente' => Dinero::enCentavos(500)],
        '2026-03-10',
    ],
    'dos abiertos en marzo' => [
        ['prestamosAbiertos' => 2], '2026-03-10',
    ],
    'cuatro abiertos en enero' => [
        ['prestamosAbiertos' => 4], '2026-01-15',
    ],
    'llegó hace exactamente siete días' => [
        ['adquiridoEn' => new DateTimeImmutable('2026-03-03')],
        '2026-03-10',
    ],
    'último con autorización' => [
        ['ultimoDisponible' => true], '2026-03-10',
    ],
]);
```

"Más de cinco reales": R$ 5,00 pasa, R$ 5,01 no. "Tres libros": dos pasan,
tres no. "Una semana en exhibición": ¿el séptimo día es el primero en que
sale, o el último en que no sale? Vera respondió: sale el octavo. La prueba
de borde es el lugar donde la ambigüedad de la frase se vuelve decisión
escrita.

:::pitfall
El último caso de la lista, "último con autorización", está **mal** tal como
está escrito: pasa `autorizacion: null` en la llamada, igual que los demás,
y por eso debería fallar. La prueba lo va a señalar en la primera
ejecución.

Es a propósito, y es un defecto común en las tablas de casos: cuando un
caso necesita un parámetro que los otros no necesitan, la tabla tiene que
ganar una columna. Sin ella, el nombre del caso promete una cosa y el
cuerpo prueba otra. El ejercicio 2 lo arregla.
:::

```text
$ php artisan test --filter=PoliticaDePrestamo

   PASS  Tests\Unit\PoliticaDePrestamoTest
  ✓ rechaza el pedido with (ejemplar prestado)          0.01s
  ✓ rechaza el pedido with (ejemplar de referencia)
  ...
  ✗ permite en el límite exacto de cada regla with
    (último con autorización)

  Tests:    1 failed, 22 passed (23 assertions)
  Duration: 0.14s
```

Veintitrés casos, catorce centésimas de segundo, y el rojo que prometió la
trampa de arriba. El tiempo es el número que importa aquí: es lo que hace
posible correr la suite cada vez que se guarda el archivo.

## Dobles: fake, stub, spy, mock

No todo lo que usa el código se puede separar como la política. El
`PrestamoService` usa el `EnviadorDeAviso`, y la prueba no debe mandar
WhatsApp. Un objeto que sustituye a otro en la prueba se llama **doble**, y
hay cuatro tipos, que difieren en lo que saben hacer:

| Doble | Qué es | Ejemplo |
|---|---|---|
| stub | devuelve respuestas listas | un reloj que siempre dice las 10 |
| fake | implementación simple de verdad | `EnviadorFalso`, que guarda en una lista |
| spy | registra las llamadas para verificarlas después | `Log::spy()` |
| mock | espera llamadas específicas, y falla si no llegan | `Mockery::mock()` |

Tabla: Los nombres se confunden en la conversación y en la documentación.
La distinción que importa es la de la última columna: qué verifica la
prueba después.

El `EnviadorFalso` del capítulo @cap:service-container es un fake. La
prueba verifica el **resultado**, lo que quedó en la lista:

```php
expect($falso->enviados)->toHaveCount(1);
```

La misma prueba con un mock verifica la **llamada**:

```php
$mock = Mockery::mock(EnviadorDeAviso::class);
$mock->shouldReceive('enviar')
    ->once()
    ->with(
        Mockery::type(Lector::class),
        Mockery::pattern('/Devuélvelo/'),
    );
```

Las dos prueban lo mismo hoy. La diferencia aparece en el próximo cambio:
si alguien cambia `enviar($lector, $texto)` por
`enviar(new Aviso($lector, $texto))`, el mock se rompe, porque estaba atado
al formato de la llamada. El fake, si se actualiza junto con la interfaz,
sigue verificando lo que importa: se envió un aviso.

:::key
Prefiere verificar **qué pasó** a verificar **cómo pasó**. Una prueba atada
al "cómo" se rompe en cada refactorización que no cambió nada, y una prueba
que se rompe sin motivo le enseña al equipo a ignorar las pruebas en rojo.

El fake gana en la mayoría de los casos. El mock es la herramienta
correcta cuando **la llamada es el comportamiento**: "el sistema de pago se
llamó una vez y solo una" es una afirmación sobre la llamada.
:::

## La factory como fixture

Las pruebas unitarias de la política no necesitaron ningún model. Las que
sí lo necesitan —una prueba del `LectorResource`, una regla del model
`Ejemplar`— pueden usar las factories del capítulo
@cap:migrations-seeders-e-factories **sin base**:

```php title="tests/Unit/EjemplarTest.php" numbered
test('ejemplar en exhibición hasta el séptimo día', function () {
    $ejemplar = Ejemplar::factory()->make([
        'adquirido_en' => '2026-03-03',
    ]);

    expect($ejemplar->enExhibicion(
        new DateTimeImmutable('2026-03-09'),
    ))->toBeTrue();

    expect($ejemplar->enExhibicion(
        new DateTimeImmutable('2026-03-11'),
    ))->toBeFalse();
});
```

`make()` arma el model con los datos de la factory y los que pasaste,
**sin grabar**. `create()` graba. Para una prueba unitaria, `make()`: es
instantáneo y no depende de que la base esté levantada.

La factory entrega un ejemplar plausible en todos los campos, y la prueba
declara solo lo que le importa: la fecha de adquisición. Quien la lee sabe
en el acto de qué depende la prueba.

## La prueba que reproduce el defecto de ayer

La corrección de la multa de doña Marlene tiene dos partes, y la segunda es
la que no se hizo en octubre.

La primera es el código: el registro de devolución del buzón deja de
calcular por su cuenta y pasa a usar el `PlazoDePrestamo`, que es donde vive
el cálculo.

La segunda es la prueba, escrita **antes** de la corrección, para verla
fallar:

```php title="tests/Unit/DevolucionDelBuzonTest.php" numbered
test('devolución adelantada al buzón no genera multa', function () {
    // el caso de doña Marlene, en febrero
    $reglas = new ReglasDeCirculacion();
    $plazo = new PlazoDePrestamo(
        new DateTimeImmutable('2026-02-02 10:00'),
        14,
    );

    $multa = $reglas->multaPor(
        $plazo,
        new DateTimeImmutable('2026-02-13 18:00'),
    );

    expect($multa)->toEqual(Dinero::cero());
});
```

```text
  ✗ devolución adelantada al buzón no genera multa
  Failed asserting that Dinero(240) is equal to Dinero(0).
```

Rojo. Es lo que se quiere ver: la prueba reproduce el defecto. Se aplica
la corrección, y se pone verde. A partir de aquí, doña Marlene está
protegida por una línea que corre en cada commit, y el comentario en la
prueba dice de dónde vino, para que nadie la borre creyendo que es
redundante.

:::note
La cobertura —el porcentaje de líneas del código que alguna prueba
ejecutó— es un **mapa**, no una nota. Muestra dónde no hay ninguna prueba,
y eso es útil. No muestra si las pruebas que existen verifican algo.

Un proyecto con una meta de 90% de cobertura suele ganar pruebas que
ejecutan todo y no afirman nada, escritas para alcanzar la meta. La Casa
Amarela no tiene meta de cobertura. Tiene una regla: **todo defecto
corregido gana una prueba que lo reproduce**. La cobertura sube sola, y
sube donde estaban los defectos.
:::

:::note En tu carrera
La pregunta "¿escribes pruebas?" en una entrevista tiene una respuesta que
funciona mejor que "sí": contar un defecto que volvió. Todo el que trabaja
hace algún tiempo tiene uno. Lo que el entrevistador quiere oír es que
entendiste por qué volvió —no había prueba— y qué haces hoy distinto: la
prueba va antes de la corrección, y se escribe para fallar primero.

Y si el puesto es en un proyecto sin ninguna prueba, que es más común de lo
que se admite, esa misma regla es la forma de empezar sin pedir permiso: no
hace falta una semana dedicada. Hace falta una prueba por defecto
corregido, a partir de hoy.
:::

:::tree title="Dónde estamos ahora"
casa-amarela/
  app/Prestamos/
    SituacionDelPedido.php        # lo que trajo la consulta
    PoliticaDePrestamo.php        # la decisión, sin base
    PrestamoService.php           # consulta, entrega, graba
  tests/Unit/
    DineroTest.php
    PlazoDePrestamoTest.php
    PoliticaDePrestamoTest.php    # once condiciones, bordes
    EjemplarTest.php
    DevolucionDelBuzonTest.php    # doña Marlene
  tests/Fakes/
    EnviadorFalso.php
:::

:::summary
- Una prueba no demuestra que el código esté bien; demuestra que un
  comportamiento sigue ocurriendo.
- Pest y PHPUnit hacen lo mismo; la elección correcta es la del proyecto,
  y no se mezclan.
- Preparar, actuar, afirmar: una acción por prueba, y siempre una
  afirmación.
- Fechas fijas en la prueba; `now()` produce fallas que dependen del día.
- Separar consulta de decisión vuelve la regla comprobable sin base y más
  clara para quien la lee.
- Un dataset cubre las condiciones en una tabla; las pruebas de borde
  convierten la ambigüedad de la frase en decisión.
- El stub responde, el fake funciona, el spy registra, el mock espera.
  Prefiere verificar el resultado antes que la llamada.
- `factory()->make()` arma sin grabar; es lo que usa la prueba unitaria.
- Todo defecto corregido gana una prueba escrita antes de la corrección,
  que falla primero.
- La cobertura es un mapa, no una meta.
:::

:::checkpoint
Las once condiciones de préstamo y los bordes de cada una corren en menos
de un segundo, sin base y sin HTTP; el aviso se verifica con un fake; y el
defecto de doña Marlene tiene una prueba que falló antes de la corrección y
pasa después.
:::

:::exercise level=1
Cada prueba de abajo tiene un problema. Di cuál:

```php
// 1
test('calcula multa', function () {
    $reglas = new ReglasDeCirculacion();
    $reglas->multaPor($plazo, now());
});

// 2
test('préstamo y devolución', function () {
    $p = $service->realizar(2117, 47);
    $service->devolver($p->id, now());
    expect($p->fresh()->devuelto())->toBeTrue();
});

// 3
test('plazo infantil', function () {
    $lector = Lector::factory()->create(['infantil' => true]);
    expect((new ReglasDeCirculacion())->plazoPara($lector))
        ->toBe(7);
});
```

:::answer
1. No afirma nada: pasa siempre. Y usa `now()`, así que el resultado, si
   se verificara, dependería del día.
2. Prueba dos acciones. Si falla, no dice si el problema está en el
   préstamo o en la devolución. Son dos pruebas, y la de devolución prepara
   el préstamo sin pasar por el service.
3. Usa `create()` en una prueba que no necesita base. `make()` basta: la
   regla solo lee el atributo del objeto. Con `create()`, la prueba se
   vuelve más lenta y empieza a fallar si la base de pruebas no está
   levantada.
:::

:::exercise level=2
Arregla el dataset de "permite en el límite exacto" para que el caso
"último con autorización" pase una `Autorizacion` de verdad y los demás
sigan pasando `null`. Y, en la prueba de rechazo, verifica la clase
**exacta** de la excepción de cada caso, no solo la madre.

:::answer
El dataset gana una tercera columna, y los casos que no la necesitan pasan
`null`:

```php
test('permite en el límite exacto de cada regla', function (
    array $cambia,
    string $cuando,
    ?Autorizacion $autorizacion,
) {
    $politica = new PoliticaDePrestamo(new ReglasDeCirculacion());

    $politica->exigirPermitido(
        situacion($cambia),
        new DateTimeImmutable($cuando),
        $autorizacion,
    );

    expect(true)->toBeTrue();
})->with([
    'multa de exactamente R$ 5,00' => [
        ['multaPendiente' => Dinero::enCentavos(500)],
        '2026-03-10', null,
    ],
    // ...
    'último con autorización' => [
        ['ultimoDisponible' => true],
        '2026-03-10',
        new Autorizacion(usuarioId: 1, motivo: 'trabajo escolar'),
    ],
]);
```

Y el rechazo verifica la clase exacta:

```php
test('rechaza el pedido', function (array $cambia, string $esperada) {
    $politica = new PoliticaDePrestamo(new ReglasDeCirculacion());

    try {
        $politica->exigirPermitido(
            situacion($cambia),
            new DateTimeImmutable('2026-03-10'),
            null,
        );
    } catch (ExcepcionDeDominio $e) {
        expect($e)->toBeInstanceOf($esperada);
        return;
    }

    $this->fail("Esperaba {$esperada}, no se lanzó nada");
})->with([ /* los mismos casos */ ]);
```

Sin la verificación exacta, un caso de "lector con atraso" que por error
lanzara `LectorConPendiente` pasaría: la madre es la misma. Es el tipo de
defecto que solo aparece cuando la pantalla muestra "regulariza tu multa" a
alguien que no debe nada.
:::

:::exercise level=3
`PrestamoService::devolver()` graba la devolución, calcula la multa, libera
el ejemplar y dispara `EjemplarDevuelto`. El equipo quiere probarlo.

Divide lo que hay que demostrar entre prueba unitaria (sin base) y prueba
de feature con base, que es el tema del próximo capítulo, y justifica cada
elección. Di también qué **no** vale la pena probar en ese método.

:::answer
**Unitaria, sin base:**

El cálculo de la multa en todos los bordes: devolución el mismo día, un día
después, adelantada, pasado el tope. Eso ya está en
`ReglasDeCirculacion::multaPor`, y ahí vive la prueba, no en el service.

La regla "un préstamo ya devuelto no se puede devolver otra vez", si se
extrae al model o a la política. Mientras esté dentro de la transacción
del service, probarla exige base.

**Feature, con base:**

Que la devolución graba `devuelto_en` y la multa **y** libera el ejemplar,
juntas: es una afirmación sobre la transacción, y solo la base la
confirma.

Que una falla a la mitad lo deshace todo: forzar una excepción después de
grabar la devolución y verificar que el ejemplar sigue prestado.

Que el evento `EjemplarDevuelto` se dispara **después** del commit, con
`Event::fake()` y la verificación de que no sale cuando la transacción se
deshace.

**Lo que no vale la pena probar:**

Que el `DB::transaction` de Laravel funciona. Que el `update` de Eloquent
graba. Que `findOrFail` lanza cuando no encuentra. Es código del framework,
ya probado por quien lo escribió; una prueba de eso solo verifica que
Laravel está instalado.

Y volver a probar, en la prueba de feature, cada borde de la multa. Una
devolución con multa y una sin multa bastan para demostrar que el service
llama al cálculo; los bordes ya están demostrados en la unitaria. Repetir
vuelve lenta la suite sin demostrar nada nuevo, que es el error con el que
abre la discusión el próximo capítulo.
:::
