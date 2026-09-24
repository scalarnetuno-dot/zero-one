---
source_hash: fa505c78eaba
title: "Enums, fechas y objetos de valor"
number: 23
slug: enums-datas-e-valores
part: p4
kicker: "Vera se quedó hasta las once cerrando el inventario. Siete lectores amanecieron debiendo ochenta centavos."
goal: >-
  Cerrar conjuntos de opciones con `enum`, guardar fechas con zona horaria
  y sin sorpresas usando `DateTimeImmutable`, y darle al dinero un tipo con
  reglas propias en lugar de un entero suelto.
---

:::story Las once de la noche del martes
El inventario de febrero se atrasó, y Vera se quedó hasta las once
registrando la pila de devoluciones que se había acumulado en el
mostrador.

El jueves, siete lectores recibieron un aviso de multa de ochenta
centavos.

—Devolvieron a tiempo —dijo Vera—. Yo registré todo el martes.

Dedé abrió la tabla.

```text
mysql> SELECT id, devolver_hasta, devuelto_en FROM prestamos
    ->  WHERE id IN (4471, 4472, 4473);
+------+----------------+---------------------+
| id   | devolver_hasta | devuelto_en         |
+------+----------------+---------------------+
| 4471 | 2026-03-10     | 2026-03-11 02:03:11 |
| 4472 | 2026-03-10     | 2026-03-11 02:03:47 |
| 4473 | 2026-03-10     | 2026-03-11 02:04:12 |
+------+----------------+---------------------+
```

—¿Las dos de la mañana? Yo me fui a las once.

—El servidor cree que son las dos.

—¿Y el servidor dónde está?

Dedé revisó la configuración del hosting antes de responder, lo que fue
buena idea.

—En Virginia.
:::

## Un string suelto es un `if` esperando un error de tipeo

El `Ejemplar` del proyecto guarda la condición así:

```php
private string $condicion = 'bueno';
```

El constructor revisa la lista, y eso resuelve el nacimiento. Pero dentro
de la clase, y en cualquier lugar que reciba ese valor, `'bueno'` es solo
un string entre todos los strings posibles:

```php
if ($ejemplar->condicion() === 'prestad') {
```

PHP lo acepta. El tipo está bien: es un string. La condición nunca es
verdadera, el bloque nunca corre, y nada se queja nunca.

Este es el agujero que quedó después de tres capítulos cerrando agujeros:
el tipo `string` dice el formato y no dice el **conjunto**.

## `enum`: el conjunto se vuelve tipo

```php title="src/Acervo/EstadoEjemplar.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Acervo;

enum EstadoEjemplar: string
{
    case Bueno = 'bueno';
    case Prestado = 'prestado';
    case Restauracion = 'restauracion';
    case Extraviado = 'extraviado';
}
```

Cada `case` es un valor, y solo existen cuatro. No hay un quinto, no hay
cómo inventar uno, y el error de tipeo deja de compilar:

```php
if ($ejemplar->estado() === EstadoEjemplar::Prestad) {
```

```text
Fatal error: Undefined constant EstadoEjemplar::Prestad
```

El `: string` después del nombre lo vuelve un **enum con valor asociado**:
cada caso lleva un texto, que es lo que va a la base.

| | Cuándo usarlo |
|---|---|
| `enum Estado` (puro) | el conjunto solo existe dentro del programa |
| `enum Estado: string` | el valor tiene que guardarse o transmitirse |

Tabla: En la duda, asociado. Un enum puro que un día tiene que ir a la
base obliga a inventar la conversión a mano, y ahí es donde alguien guarda
el nombre del caso en lugar del valor.

Tres operaciones cubren el uso diario:

```php
$estado = EstadoEjemplar::from('restauracion');
echo $estado->name, ' / ', $estado->value, "\n";
```

```text
Restauracion / restauracion
```

`name` es el nombre del caso en el código; `value` es el texto asociado.
Existen los dos, y confundirlos es el error de la sección siguiente.

```php
var_dump(EstadoEjemplar::tryFrom('prestadoo'));
```

```text
NULL
```

```php
EstadoEjemplar::from('prestadoo');
```

```text
Fatal error: Uncaught ValueError: "prestadoo" is not a valid backing
value for enum EstadoEjemplar
```

:::key
`from()` cuando el valor **tiene** que ser válido: vino de tu propia tabla,
y si no es válido la base está corrupta y quieres saberlo ahora.

`tryFrom()` cuando el valor vino de fuera: formulario, parámetro de
búsqueda, archivo de la editorial. Ahí `null` es una respuesta posible, y
el lugar para tratarlo es la validación de la entrada.

Intercambiarlos es el defecto más común con enums: `from()` en un
parámetro de URL convierte a un usuario curioso en un error fatal.
:::

Y `cases()` devuelve todos, en el orden en que se escribieron: es lo que
arma un `<select>` sin que nadie repita la lista en el HTML:

```php
foreach (EstadoEjemplar::cases() as $caso) {
    echo $caso->value, "\n";
}
```

## El comportamiento junto a la opción

Un enum no es solo una lista. Acepta métodos:

```php title="src/Acervo/EstadoEjemplar.php" numbered
    public function disponible(): bool
    {
        return $this === self::Bueno;
    }

    public function etiqueta(): string
    {
        return match ($this) {
            self::Bueno => 'Disponible',
            self::Prestado => 'Prestado',
            self::Restauracion => 'En restauración',
            self::Extraviado => 'Extraviado',
        };
    }
```

```php
echo EstadoEjemplar::Restauracion->etiqueta(), "\n";
```

```text
En restauración
```

El `match` aquí hace un trabajo que el `if` no hace: si alguien agrega un
quinto caso al enum y se olvida de `etiqueta()`, la llamada con ese caso
lanza `UnhandledMatchError` en el acto. El `if/else` devolvería la última
opción en silencio.

:::key
Un enum se compara con `===`, y funciona porque cada caso es un objeto
único: existe **un** `EstadoEjemplar::Bueno` en todo el programa, y todas
las variables que lo contienen apuntan a él.

Es la misma identidad que molestaba al comparar dos `Lector` cargados de
la base, ahora trabajando a favor.
:::

## El enum en la base

La escritura usa `value`; la lectura usa `tryFrom` o `from`:

```php title="src/Acervo/repositorio.php" numbered
$c = $pdo->prepare(
    'UPDATE ejemplares SET condicion = ? WHERE registro = ?'
);

$c->execute([$estado->value, $registro]);
```

```php
$estado = EstadoEjemplar::from($fila['condicion']);
```

:::pitfall
Nunca guardes `$estado->name`.

El `name` es el identificador en el código: `Restauracion`, con
mayúscula, escrito en PHP. Renombrar un caso es un cambio de código normal,
y el día que alguien lo renombre, la base queda con miles de filas
apuntando a un nombre que ya no existe.

El `value` es el contrato con el mundo de fuera. No cambia porque a
alguien se le ocurrió un nombre mejor.
:::

## Una fecha sin zona horaria es información incompleta

La tabla de la Casa Amarela guarda `2026-03-11 02:03:11`. Eso no es una
hora: es un número esperando que alguien diga dónde.

A las once de la noche del martes en São Paulo, ya son las dos de la
mañana del miércoles en el servidor de Virginia. Los dos tienen razón, y
el informe que compara la fecha de devolución con el plazo está
equivocado por un día.

```php title="zona.php" numbered
<?php

declare(strict_types=1);

$saoPaulo = new DateTimeZone('America/Sao_Paulo');

$devolucion = new DateTimeImmutable('2026-03-10 23:00:00', $saoPaulo);

$enUtc = $devolucion->setTimezone(new DateTimeZone('UTC'));

echo 'local: ', $devolucion->format('Y-m-d H:i T'), "\n";
echo 'utc:   ', $enUtc->format('Y-m-d H:i T'), "\n";
```

```text
local: 2026-03-10 23:00 -03
utc:   2026-03-11 02:00 UTC
```

Es el mismo instante, escrito de dos formas. El defecto de la Casa Amarela
no fue que el servidor estuviera en Virginia: fue que el programa guardara
una hora sin decir de dónde, y después comparara esa hora con una fecha de
São Paulo.

:::key
La regla que evita toda esta clase de problemas, y que sigue casi todo
sistema serio:

**guarda en UTC, convierte al mostrar.** La base recibe el instante en UTC;
la pantalla recibe la zona horaria de quien está mirando.

La fecha de vencimiento, el cumpleaños y el feriado son distintos: son
fechas sin hora, y convertirles la zona horaria es lo que las estropea.
`devolver_hasta` es un `DATE` por ese motivo.
:::

:::art caption="Para Vera eran las once de la noche; para el servidor, las dos de la mañana."
src="para-a-vera-eram-onze-da-noite-para-o-servidor-duas-da-manha.png"
Viñeta editorial minimalista sobre fondo blanco, composición dividida por
una línea discontinua vertical. A la izquierda, una bibliotecaria mayor
cierra con llave la puerta de una pequeña biblioteca de barrio bajo un
farol encendido, y un reloj de pared en la fachada marca las 23 h. A la
derecha, muy lejos, un servidor de rack solitario en un galpón frío, con
un cartel discreto que dice "VIRGINIA" y un reloj digital que marca 02:03.
Entre los dos, un sobre de aviso de multa ya volando hacia un buzón. Pocos
elementos, humor seco, estética de revista de tecnología.
:::

## `DateTimeImmutable`, y por qué la otra da problemas

PHP tiene dos clases de fecha. Una cambia; la otra, no.

```php title="mutable.php" numbered
<?php

$plazo = new DateTime('2026-03-10');
$aviso = $plazo;

$aviso->modify('+14 days');

echo $plazo->format('Y-m-d'), "\n";
```

```text
2026-03-24
```

El `$plazo` cambió, y nadie lo pidió. `$aviso = $plazo` no copió nada: son
dos variables con el mismo objeto, como cualquier objeto de PHP, y
`modify()` modificó el original.

La versión inmutable responde a la misma llamada de otra forma:

```php title="inmutable.php" numbered
<?php

$plazo = new DateTimeImmutable('2026-03-10');
$aviso = $plazo->add(new DateInterval('P14D'));

echo 'plazo: ', $plazo->format('Y-m-d'), "\n";
echo 'aviso: ', $aviso->format('Y-m-d'), "\n";
```

```text
plazo: 2026-03-10
aviso: 2026-03-24
```

`add()` no modificó nada: devolvió **otro** objeto. Guardar el resultado
deja de ser opcional, y eso es lo que vuelve segura la clase para pasarla
de mano en mano.

`DateInterval` describe una duración con un texto corto: `P14D` es
"período de catorce días", `P1M` es un mes, `PT2H` son dos horas; la `T`
separa la parte de fecha de la parte de hora.

:::pitfall
Una función que recibe `DateTime` puede modificar la fecha de quien la
llamó, y nada en la firma lo avisa.

```php
function vencimiento(DateTime $retiro): DateTime
{
    return $retiro->modify('+14 days');
}
```

Esa función devuelve el plazo **y** estropea el `$retiro` de quien lo
pasó. El defecto aparece lejos: en la línea en que alguien imprime la
fecha de retiro y está catorce días en el futuro.

Usa `DateTimeImmutable` en todo lo nuevo. `DateTime` sigue existiendo
porque PHP no rompe el código antiguo, no porque alguien la recomiende.
:::

## El dinero no es un `int` suelto

El proyecto guarda la multa en centavos desde el capítulo
@cap:conversao-automatica, y esa decisión es correcta. El problema es
otro: `int` es el tipo de todo. Un `int` de centavos y un `int` de días son
el mismo tipo para PHP y para PHPStan.

```php
$total = $multaEnCentavos + $diasDeAtraso;
```

Eso pasa por todo. Suma centavos con días, devuelve un entero, y el número
llega al recibo.

Un **objeto de valor** cierra esa puerta:

```php title="src/Prestamos/Dinero.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Prestamos;

final class Dinero
{
    private function __construct(
        public readonly int $centavos,
    ) {
        if ($centavos < 0) {
            throw new \InvalidArgumentException('Valor negativo');
        }
    }

    public static function enCentavos(int $centavos): self
    {
        return new self($centavos);
    }

    public static function cero(): self
    {
        return new self(0);
    }

    public function mas(self $otro): self
    {
        return new self($this->centavos + $otro->centavos);
    }

    public function por(int $factor): self
    {
        return new self($this->centavos * $factor);
    }

    public function formateado(): string
    {
        $reales = $this->centavos / 100;

        return 'R$ ' . number_format($reales, 2, ',', '.');
    }
}
```

```php
$multa = Dinero::enCentavos(80)->por(9);

echo $multa->formateado(), "\n";
```

```text
R$ 7,20
```

Tres decisiones, y cada una paga una cuenta.

**El constructor es privado**, y quien crea es `enCentavos()`. El nombre
del método dice la unidad: nadie va a pasar `7.20` creyendo que son reales,
porque no existe una puerta que acepte reales.

**Los métodos devuelven `self`**, un objeto nuevo. Sumar no modifica
ninguno de los dos lados, exactamente como la fecha inmutable.

**La suma solo acepta `Dinero`.** `$multa->mas($diasDeAtraso)` no compila,
y esa era la línea que el `int` suelto dejaba pasar.

:::term Objeto de valor
Un tipo definido por lo que **vale**, no por cuál es: dos `Dinero` de 720
centavos son intercambiables, y ninguno de los dos tiene identidad propia.

Por eso nace inmutable y se compara por contenido, al contrario de un
`Lector`, que tiene `id` y sigue siendo la misma persona aunque cambie de
nombre.
:::

:::note En tu carrera
"Demasiados tipos" es una crítica que vas a oír, y a veces tiene razón. La
defensa que funciona no es teórica: es mostrar la línea que dejó de ser
posible.

Para el `Dinero`, la línea es `$multa + $dias`. Para el enum, es
`=== 'prestad'`. Para la fecha inmutable, es la función que modifica el
argumento de quien la llamó.

Trae la línea. En una revisión de código, un ejemplo de defecto impedido
vale más que cualquier argumento sobre diseño, y, si no encuentras la
línea, quizá el tipo de verdad todavía no necesite existir.
:::

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Acervo/
      EstadoEjemplar.php    # enum con valor asociado
      Ejemplar.php          # guarda EstadoEjemplar, no string
      Libro.php
      Clasificacion.php
    Prestamos/
      EstadoPrestamo.php    # enum
      Dinero.php            # objeto de valor, inmutable
      Multa.php
    Circulacion/
    Lectores/
:::

:::milestone
Fin de la Parte 4. El proyecto tiene contratos declarados, errores con
nombres del dominio, tipos revisados antes de ejecutar y valores que
rechazan la operación sin sentido. Nada de eso es adorno: es la lista
exacta de cosas que Laravel va a suponer que ya tienes.
:::

:::summary
- `string` dice el formato y no dice el conjunto; `enum` dice los dos.
- Un enum asociado (`enum X: string`) tiene `value` para el mundo de fuera
  y `name` para el código.
- `from()` para el valor que tiene que ser válido; `tryFrom()` para el
  valor que vino de fuera.
- `cases()` devuelve la lista; el `match` dentro del enum exige el caso
  nuevo en lugar de esconderlo.
- Guarda `value` en la base, nunca `name`.
- Una fecha sin zona horaria es un número: guarda el instante en UTC,
  convierte al mostrar.
- La fecha de vencimiento es `DATE`, sin hora y sin zona horaria.
- `DateTimeImmutable` devuelve un objeto nuevo; `DateTime` modifica el de
  quien llamó, y nada en la firma lo avisa.
- Los centavos en `int` siguen siendo correctos, y un `int` suelto se suma
  con cualquier otro `int`. Un objeto de valor cierra esa puerta.
:::

:::checkpoint
Sustituyes strings sueltos por enums asociados, eliges entre `from` y
`tryFrom` según el lugar de donde vino el valor, explicas por qué la
devolución de Vera se volvió miércoles, y escribes un objeto de valor
inmutable que rechaza la operación sin sentido.
:::

:::exercise level=1
Escribe `EstadoPrestamo` como enum asociado, con los casos: abierto,
devuelto, renovado y con atraso.

Después responde: ¿por qué "con atraso" es un caso problemático en esa
lista?

:::answer
```php title="src/Prestamos/EstadoPrestamo.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Prestamos;

enum EstadoPrestamo: string
{
    case Abierto = 'abierto';
    case Devuelto = 'devuelto';
    case Renovado = 'renovado';
    case ConAtraso = 'con_atraso';
}
```

"Con atraso" es problemático porque **no es un estado guardado: es una
conclusión**. Un préstamo entra en atraso solo, a medianoche, sin que
nadie ejecute nada, y un valor guardado en una columna no cambia solo.

Guardar `con_atraso` obliga a alguien a mantenerlo actualizado: una tarea
nocturna, un disparador, una corrección cuando la tarea falla. Es la
columna `cantidad` otra vez, con otra ropa.

La salida es calcular: el préstamo está `Abierto`, y `conAtraso()` es un
método que compara `devolver_hasta` con hoy. Tres casos en la lista, y la
cuarta información nace correcta todas las veces.
:::

:::exercise level=2
Escribe `PlazoDePrestamo`, un objeto de valor que recibe la fecha de
retiro y la cantidad de días, y sabe responder:

- cuál es la fecha de devolución;
- si una fecha cualquiera está atrasada respecto de él;
- cuántos días de atraso hay hasta una fecha.

Usa `DateTimeImmutable`. Cuidado con el caso en que no hay atraso.

:::answer
```php title="src/Prestamos/PlazoDePrestamo.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Prestamos;

final class PlazoDePrestamo
{
    public readonly \DateTimeImmutable $devolverHasta;

    public function __construct(
        public readonly \DateTimeImmutable $retiro,
        public readonly int $dias,
    ) {
        if ($dias < 1) {
            throw new \InvalidArgumentException('Plazo inválido');
        }

        $this->devolverHasta = $retiro->add(
            new \DateInterval("P{$dias}D")
        );
    }

    public function atrasadoEn(\DateTimeImmutable $cuando): bool
    {
        return $cuando > $this->devolverHasta;
    }

    public function diasDeAtraso(\DateTimeImmutable $cuando): int
    {
        if (!$this->atrasadoEn($cuando)) {
            return 0;
        }

        return $this->devolverHasta->diff($cuando)->days;
    }
}
```

El cuidado que pide el enunciado está en `diasDeAtraso`: sin el `if`, una
devolución adelantada devolvería un número positivo, porque `diff()` no
tiene signo: responde la distancia, no la dirección. Una devolución tres
días antes se volvería tres días de multa.

Dos observaciones sobre el diseño. `$devolverHasta` se calcula en el
constructor y se guarda como `readonly`: es consecuencia de los otros dos
campos y nunca va a divergir de ellos. Y los tres métodos reciben la fecha
de fuera en lugar de llamar a `new DateTimeImmutable('now')` por dentro, lo
que hace la clase comprobable sin esperar a que amanezca.
:::

:::exercise level=3
Este informe corre cada día primero y cobra las multas del mes anterior.
Encuentra los tres defectos relacionados con este capítulo y reescribe el
fragmento.

```php title="cobranza.php" numbered
$prestamos = $pdo->query(
    "SELECT * FROM prestamos WHERE devuelto_en IS NOT NULL"
)->fetchAll();

$total = 0;

foreach ($prestamos as $p) {
    if ($p['status'] == 'atrasado') {
        $dias = (strtotime($p['devuelto_en'])
              - strtotime($p['devolver_hasta'])) / 86400;

        $total = $total + ($dias * 0.8);
    }
}

echo "Total: R$ " . $total;
```

:::answer
**Uno: el string `'atrasado'` con comparación laxa.** Si la columna guarda
`con_atraso`, la condición nunca es verdadera y el informe cobra cero, sin
ningún error. Con enum, el valor viene de `EstadoPrestamo::tryFrom()` y la
comparación es por identidad.

**Dos: la diferencia de fechas en segundos, dividida por 86.400.** Eso
ignora la zona horaria e ignora que no todo día tiene 86.400 segundos: los
días de cambio de horario tienen 82.800 o 90.000. El resultado es un
`float` con decimales que nadie pidió, y el redondeo decide la multa.
`DateTimeImmutable` y `diff()->days` responden en días de calendario.

**Tres: dinero en `float`.** `$dias * 0.8` acumula error en cada suma, y
el total impreso al final de un mes con trescientas multas no cierra con
la suma de los avisos individuales. La cuenta es en centavos, y el tipo es
`Dinero`.

```php title="cobranza.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Prestamos\Dinero;
use CasaAmarela\Prestamos\EstadoPrestamo;

$c = $pdo->prepare(
    'SELECT devolver_hasta, devuelto_en, status
       FROM prestamos
      WHERE devuelto_en IS NOT NULL
        AND status = ?'
);

$c->execute([EstadoPrestamo::Devuelto->value]);

$utc = new DateTimeZone('UTC');
$total = Dinero::cero();

foreach ($c as $fila) {
    $plazo = new DateTimeImmutable($fila['devolver_hasta'], $utc);
    $vuelta = new DateTimeImmutable($fila['devuelto_en'], $utc);

    if ($vuelta <= $plazo) {
        continue;
    }

    $dias = $plazo->diff($vuelta)->days;

    $total = $total->mas(Dinero::enCentavos(80)->por($dias));
}

echo 'Total: ', $total->formateado(), "\n";
```

Un cuarto defecto, de regalo, que no es de este capítulo pero se vuelve
visible después de reescribir: el `SELECT *` se volvió la lista de las
tres columnas usadas. Un informe que lee la tabla entera cada noche se
vuelve más lento con cada columna que alguien agrega, por un motivo que no
tiene nada que ver con él.
:::
