---
source_hash: b354432f96ad
title: "Fechas y horarios"
number: 27
slug: datas-e-horarios
part: p5
kicker: "El defecto del domingo tenía cuatro años. El arreglo tenía nueve líneas. La prueba del arreglo fallaba después de las nueve de la noche."
goal: >-
  Calcular un plazo que no cae en un día cerrado, contar los días de atraso
  sin equivocarse por la hora, tratar "ahora" como una dependencia que se
  pasa y se cambia en la prueba, hacer cuentas con meses sin caer en el día
  31, y leer la fecha que escribe una persona.
---

:::story El defecto del domingo
En la primera semana del proyecto, Vera había listado los defectos del
Sistema sin quitar los ojos de la etiqueta que pegaba: "cuando alguien
devuelve el domingo, cobra multa, y el domingo ni abrimos". Desde hacía
cuatro años.

Tainá tomó el defecto.

—El plazo es de catorce días —explicó Vera—. Si el decimocuarto cae en
domingo, la persona solo puede devolver el lunes. Y el Sistema cobra el
lunes. Un día de multa, cada vez. Yo devuelvo el dinero de mi bolsillo
cuando se quejan.

—¿De su bolsillo?

—Es más rápido que explicar.

Tainá escribió la corrección, escribió la prueba, y la prueba pasó. A las
diez y media de la noche, ejecutando todo otra vez antes de abrir el pedido
de revisión, la misma prueba falló.

```text
Préstamo con plazo hoy no debería estar atrasado.
Esperado: false. Obtenido: true.
```

La ejecutó otra vez. Falló. A la mañana siguiente, pasó.

—No toqué nada —le dijo a Dedé.

—Tú no. El reloj sí.
:::

## El plazo que no cae en un día cerrado

El capítulo @cap:enums-datas-e-valores dejó tres reglas: fecha con zona
horaria, `DateTimeImmutable` siempre, y UTC en la base con conversión en la
pantalla. Este capítulo usa las tres y agrega lo que falta para calcular un
plazo de verdad.

La regla de Vera, escrita:

```php title="plazo.php" numbered
<?php

declare(strict_types=1);

const DOMINGO = 7;

function proximoDiaAbierto(
    DateTimeImmutable $dia,
    array $feriados,
): DateTimeImmutable {
    while (
        (int) $dia->format('N') === DOMINGO
        || in_array($dia->format('Y-m-d'), $feriados, true)
    ) {
        $dia = $dia->modify('+1 day');
    }
    return $dia;
}

$feriados = ['2026-04-03', '2026-04-21'];
$zona = new DateTimeZone('America/Sao_Paulo');

foreach (['2026-03-22', '2026-04-03', '2026-04-21'] as $fecha) {
    $plazo = new DateTimeImmutable($fecha, $zona);
    $abierto = proximoDiaAbierto($plazo, $feriados);
    echo $plazo->format('D d/m'), ' -> ';
    echo $abierto->format('D d/m'), "\n";
}
```

```text
$ php plazo.php
Sun 22/03 -> Mon 23/03
Fri 03/04 -> Sat 04/04
Tue 21/04 -> Wed 22/04
```

`format('N')` devuelve el día de la semana como número, de 1, lunes, a 7,
domingo. El `while`, y no un `if`, es lo que trata el feriado que cae el
sábado antes de un domingo: el bucle avanza hasta encontrar un día abierto,
sean cuantos sean los cerrados seguidos.

Los feriados están en un array porque cambian cada año y cada ciudad tiene
los suyos. En el volumen 2, pasan a una tabla, y Vera registra los del año
en enero.

## Días de atraso, sin la hora en el medio

El plazo es una **fecha**: día 24. La devolución es un **instante**: día
27, a las 9:15. Restar uno del otro directamente mezcla las dos cosas, y el
resultado cambia según la hora en que el libro llegó al mostrador.

```php title="atraso.php" numbered
<?php

declare(strict_types=1);

function diasDeAtraso(
    DateTimeImmutable $plazo,
    DateTimeImmutable $devueltoEn,
): int {
    $dia = $devueltoEn->setTimezone($plazo->getTimezone())
        ->setTime(0, 0);
    $intervalo = $plazo->diff($dia);

    return $intervalo->invert === 1 ? 0 : $intervalo->days;
}

$zona = new DateTimeZone('America/Sao_Paulo');
$plazo = new DateTimeImmutable('2026-03-24', $zona);

foreach (['2026-03-20 15:00', '2026-03-24 17:50',
          '2026-03-27 09:15'] as $cuando) {
    $devuelto = new DateTimeImmutable($cuando, $zona);
    echo $cuando, ': ', diasDeAtraso($plazo, $devuelto), "\n";
}

$utc = new DateTimeImmutable(
    '2026-03-25 01:30',
    new DateTimeZone('UTC'),
);
echo 'utc 25/03 01:30: ', diasDeAtraso($plazo, $utc), "\n";
```

```text
$ php atraso.php
2026-03-20 15:00: 0
2026-03-24 17:50: 0
2026-03-27 09:15: 3
utc 25/03 01:30: 0
```

Tres pasos, cada uno por un motivo.

**`setTimezone` antes que nada.** La última línea es la misma devolución
que la base guardaría en UTC: la 1:30 del día 25 en UTC son las 22:30 del
día 24 en São Paulo. Dentro del plazo. Sin la conversión, sería un día de
multa para quien devolvió a tiempo.

**`setTime(0, 0)`** borra la hora y deja solo el día. Es lo que hace que la
devolución de las 17:50 del día 24 valga "día 24", y no "día 24 y diecisiete
horas después del plazo".

**`diff`** devuelve un `DateInterval`. `days` es el total de días entre las
dos fechas, siempre positivo; `invert` vale `1` cuando la segunda fecha es
**anterior** a la primera: cuando el libro volvió antes del plazo.

:::key
Plazo, cumpleaños, feriado: **fecha**. Retiro, devolución, pago:
**instante**. Antes de comparar uno con otro, convierte el instante a la
zona horaria de la fecha y descarta la hora. La mayor parte de los defectos
de "un día de más" en los sistemas brasileños nace de saltarse uno de los
dos pasos.
:::

## "Ahora" es una dependencia

De vuelta a la prueba que fallaba de noche. La versión que había escrito
Tainá le preguntaba a PHP qué día era:

```php
public function estaAtrasado(): bool
{
    $hoy = new DateTimeImmutable('today');
    return $hoy > $this->devolverHasta;
}
```

Dos problemas en una línea.

**La zona horaria.** `new DateTimeImmutable('today')` sin zona usa la zona
predeterminada de PHP, y en el contenedor de pruebas de Vertexo era la de
fábrica:

```text
$ php -r 'echo date_default_timezone_get();'
UTC
```

A las 21 h en São Paulo, ya es medianoche en UTC. A partir de ahí, "hoy"
para PHP es el día siguiente, y el préstamo con plazo hoy aparece atrasado.
A la mañana, las dos zonas vuelven a coincidir y la prueba pasa.

**El reloj.** Aun con la zona correcta, la prueba depende de la hora en que
corre. Una prueba que da un resultado distinto según la hora no prueba
nada, y lo que dice "hoy" dentro del método no deja que ninguna prueba elija
la hora.

La salida es la misma del capítulo @cap:heranca-interfaces-e-traits para
todo lo que viene de fuera: una interfaz, y quien la necesita la recibe
por el constructor.

```php title="reloj.php" numbered
<?php

declare(strict_types=1);

interface Reloj
{
    public function ahora(): DateTimeImmutable;
}

final class RelojDelSistema implements Reloj
{
    public function __construct(private DateTimeZone $zona)
    {
    }

    public function ahora(): DateTimeImmutable
    {
        return new DateTimeImmutable('now', $this->zona);
    }
}

final class RelojDetenido implements Reloj
{
    public function __construct(private DateTimeImmutable $instante)
    {
    }

    public function ahora(): DateTimeImmutable
    {
        return $this->instante;
    }
}
```

El sistema en producción usa el `RelojDelSistema`, con la zona horaria de
São Paulo viniendo de la configuración. La prueba usa el `RelojDetenido`, y
elige la hora:

```php title="reloj.php (continuación)" numbered
final class Prestamo
{
    public function __construct(
        private DateTimeImmutable $devolverHasta,
        private Reloj $reloj,
    ) {
    }

    public function estaAtrasado(): bool
    {
        $hoy = $this->reloj->ahora()->setTime(0, 0);
        return $hoy > $this->devolverHasta;
    }
}

$zona = new DateTimeZone('America/Sao_Paulo');
$plazo = new DateTimeImmutable('2026-03-24', $zona);

$noche = new RelojDetenido(
    new DateTimeImmutable('2026-03-24 22:30', $zona),
);
$despues = new RelojDetenido(
    new DateTimeImmutable('2026-03-25 08:00', $zona),
);

var_dump((new Prestamo($plazo, $noche))->estaAtrasado());
var_dump((new Prestamo($plazo, $despues))->estaAtrasado());
```

```text
bool(false)
bool(true)
```

Ahora la prueba de las diez y media de la noche corre a las diez y media de
la noche de cualquier día, incluso a las nueve de la mañana.

:::term Reloj inyectado
"Ahora" tratado como dependencia: un objeto que responde qué hora es,
recibido por el constructor. En el sistema, le pregunta al sistema
operativo; en la prueba, responde siempre el mismo instante.

La idea es tan común que se volvió un estándar de la comunidad PHP: la
PSR-20, con la interfaz `ClockInterface` y un único método, `now()`. Es la
misma interfaz de este capítulo con los nombres en inglés.
:::

La zona horaria predeterminada también tiene arreglo, en la configuración
de PHP o al principio del programa:

```php
date_default_timezone_set('America/Sao_Paulo');
```

Pero fíjate en el orden: el reloj inyectado resuelve el problema **con** o
**sin** esa línea. La zona predeterminada es una red de seguridad; la zona
explícita, en el reloj y en las fechas, es la regla.

## Un mes después del día 31

El carné de la Casa Amarela se renueva cada mes. Tainá escribió lo obvio:

```php
$renovado = new DateTimeImmutable('2026-01-31');
echo $renovado->modify('+1 month')->format('Y-m-d');
```

```text
2026-03-03
```

No es un defecto de PHP. "Un mes después del 31 de enero" sería el 31 de
febrero, que no existe; PHP suma los días que sobran y llega al 3 de marzo.
Todo lenguaje tiene que elegir algo, y PHP eligió eso.

Cuando la regla es "el último día del mes siguiente", hay que decirla:

```php
echo $renovado->modify('last day of next month')->format('Y-m-d');
```

```text
2026-02-28
```

:::pitfall
`+1 month` solo sorprende del día 29 en adelante, y las pruebas suelen
usar el día 10. En cualquier regla con meses, escribe una prueba con el 31
de enero. Si la regla del negocio no dice qué hacer ese día, pregúntale a
Vera antes de elegir: es una decisión de ella, no de PHP.
:::

## La fecha que alguien escribió

En el mostrador, Vera escribe la fecha de devolución de los libros que
llegaron por el buzón de devolución el fin de semana: `24/03/2026`. El
constructor de `DateTimeImmutable` no es el lugar correcto para eso:
entiende decenas de formatos y adivina los ambiguos. Para un texto
escrito, di el formato:

```php title="entrada.php" numbered
<?php

declare(strict_types=1);

function leerFechaBr(
    string $texto,
    DateTimeZone $zona,
): ?DateTimeImmutable {
    $fecha = DateTimeImmutable::createFromFormat(
        '!d/m/Y',
        $texto,
        $zona,
    );
    $avisos = DateTimeImmutable::getLastErrors();
    if ($fecha === false || $avisos !== false) {
        return null;
    }
    return $fecha;
}

$zona = new DateTimeZone('America/Sao_Paulo');
$textos = ['24/03/2026', '31/02/2026', '2026-03-24', '24/3/2026'];
foreach ($textos as $t) {
    $f = leerFechaBr($t, $zona);
    $salida = $f?->format('Y-m-d H:i') ?? 'inválida';
    echo str_pad($t, 11), $salida, "\n";
}
```

```text
24/03/2026 2026-03-24 00:00
31/02/2026 inválida
2026-03-24 inválida
24/3/2026  2026-03-24 00:00
```

Dos detalles que hacen la diferencia.

**El `!` al principio del formato** pone en cero todo lo que el texto no
informa. Sin él, la hora que falta viene del reloj: `24/03/2026` se vuelve
"24 de marzo, a las 9:55" —la hora en que corrió el script—, y la
comparación con el plazo se equivoca según la hora del día.

**`getLastErrors()`.** `31/02/2026` **no** devuelve `false`: PHP hace la
misma cuenta del mes y devuelve el 3 de marzo, anotando un aviso. El aviso
queda en `getLastErrors()`, que devuelve `false` cuando no hubo ninguno.
Revisar solo el `false` del `createFromFormat` dejaría pasar el 31 de
febrero.

`$f?->format(...)` es el operador *nullsafe*: llama al método solo si `$f`
no es `null` y, si lo es, el resultado entero se vuelve `null`, sin error.
El `??` cambia ese `null` por el texto. Juntos, dicen en una línea
"formatea si existe; si no, escribe inválida".

:::note En tu carrera
Las fechas son el área donde más código "funciona en mi máquina": tu
máquina está en la zona de São Paulo, el servidor está en UTC, la prueba
corre a la mañana, y nadie trabaja el 31 de enero.

Tres preguntas cierran la mayor parte de los defectos antes de que
existan: **¿en qué zona horaria** está este instante? ¿esto es **fecha** o
**instante**? ¿de dónde viene el **ahora**? Cuando la respuesta a la
tercera sea "de dentro de la función", tienes una prueba que va a fallar a
las nueve de la noche.
:::

## Lo que el volumen 2 hace con las fechas

Laravel usa una biblioteca llamada **Carbon**, que extiende
`DateTimeImmutable` con nombres más cortos: `now()->addDays(14)`,
`$plazo->isSunday()`, `$plazo->diffInDays($devolucion)`. Por debajo, cada
uno es una de las llamadas de este capítulo.

La zona horaria predeterminada se vuelve una línea de la configuración del
proyecto. Y el reloj inyectado recibe una forma lista: en las pruebas del
volumen 2, una llamada congela el `now()` de todo el framework en un
instante elegido. Es el `RelojDetenido`, aplicado a todo de una vez.

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Tiempo/
      Reloj.php              # interfaz: ahora()
      RelojDelSistema.php    # zona horaria de São Paulo
      RelojDetenido.php      # para las pruebas
    Circulacion/
      CalendarioDeLaBiblioteca.php   # domingos y feriados
:::

:::summary
- `format('N')` da el día de la semana (7 es domingo); un `while` salta
  los días cerrados seguidos.
- El plazo es una fecha; la devolución es un instante. Convierte el
  instante a la zona de la fecha, pon la hora en cero y recién entonces
  compara.
- `diff()` devuelve `days` siempre positivo e `invert` para el sentido.
- "Ahora" es una dependencia: recibe un `Reloj` por el constructor. La
  prueba pasa un reloj detenido. La PSR-20 estandariza la idea.
- `+1 month` del 31 de enero es el 3 de marzo. Di la regla con todas las
  letras.
- Fecha escrita: `createFromFormat` con `!`, y revisa `getLastErrors()`.
:::

:::checkpoint
Calculas un plazo que respeta los días cerrados, cuentas el atraso sin
equivocarte por la hora o la zona horaria, escribes código de fechas que
una prueba puede correr a cualquier hora, y validas la fecha que escribió
una persona.
:::

:::exercise level=1
Para cada valor, di si es **fecha** o **instante** y en qué columna de la
base iría: `DATE` o `DATETIME` en UTC.

1. la fecha de nacimiento del lector;
2. la hora en que se retiró el ejemplar;
3. el plazo de devolución;
4. la hora en que se pagó la multa.

:::answer
1. Fecha, `DATE`. Nadie cumple años en UTC.
2. Instante, `DATETIME` en UTC.
3. Fecha, `DATE`: el plazo es el día entero, en la ciudad de la
   biblioteca.
4. Instante, `DATETIME` en UTC.
:::

:::exercise level=2
Escribe `plazoDeDevolucion(DateTimeImmutable $retiro, int $dias,
array $feriados): DateTimeImmutable`, que suma los días a la fecha del
retiro —sin la hora— y empuja el resultado al siguiente día abierto.
Pruébalo con un retiro el sábado 7 de marzo de 2026, a las 16 h, y catorce
días.

:::answer
```php
function plazoDeDevolucion(
    DateTimeImmutable $retiro,
    int $dias,
    array $feriados,
): DateTimeImmutable {
    $plazo = $retiro->setTime(0, 0)->modify("+{$dias} days");
    return proximoDiaAbierto($plazo, $feriados);
}
```

Sábado 7 de marzo más catorce días es sábado 21 de marzo: abierto, y el
plazo queda ahí. Con quince días, caería el domingo 22 e iría al lunes 23.

El `setTime(0, 0)` va antes de la suma para que el plazo sea una fecha, y
no "día 21 a las 16 h". Sin eso, la comparación de `estaAtrasado` pasaría a
depender de la hora del retiro.
:::

:::exercise level=3
El informe de atrasados corre a la 1 h de la mañana, desde el programador
de tareas, en un servidor en UTC. Usa `new DateTimeImmutable('today')` para
saber qué día es, y lista los préstamos con plazo anterior a hoy. Vera se
queja de que, cada mañana, la lista trae gente que todavía está dentro del
plazo. Explica el defecto con horas y fechas concretas, y escribe la
corrección.

:::answer
A la 1 h de la mañana en UTC, en São Paulo son las 22 h **del día
anterior**. En la madrugada del 25 de marzo, UTC, el `today` del servidor
es 25; en São Paulo, todavía es 24. Todo préstamo con plazo el día 24 entra
en la lista como atrasado, aunque el día 24 todavía no terminó en la ciudad
de la biblioteca.

La corrección es no preguntarle al servidor qué día es:

```php
$hoy = $reloj->ahora()->setTime(0, 0);
```

con `$reloj` siendo un `RelojDelSistema` creado con la zona horaria de São
Paulo. La prueba del informe pasa un `RelojDetenido` en
`2026-03-25 01:00` UTC y comprueba que el plazo del día 24 **no** está en
la lista.

La otra mitad de la corrección es de conversación, no de código:
preguntarle a Vera si el informe debería correr a las 7 h de São Paulo, que
es cuando ella lo lee.
:::
