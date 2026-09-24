---
source_hash: a29c9d30090b
title: "Funciones"
number: 10
slug: funcoes
part: p1
kicker: "Una regla que vive en diez lugares cambia en nueve. El décimo es siempre el que genera el comprobante."
goal: >-
  Extraer una regla a una función, usar parámetros y retorno con intención,
  entender el alcance sin recurrir a `global`, pasar comportamiento como
  argumento, y probar que la regla está bien sin subir nada.
---

:::story Cincuenta centavos
La dirección de la Casa Amarela aprobó, en acta, el aumento de la multa
diaria de R$ 0,50 a R$ 0,80. Seu Juvenal mandó un mensaje el sábado:

> *"Es solo cambiar el número, ¿no? ¿Para el lunes está?"*

Dedé abrió el Sistema y buscó `0.5`.

Siete resultados.

El cálculo de la pantalla de devolución. El del informe de pendientes. El
del recibo impreso. El del correo de cobranza. Uno dentro de un `if` que
solo corre en diciembre, por algún motivo. Uno comentado, con la fecha
`// 2014` al lado. Y un séptimo, en `funciones2_NUEVO_final.php`, escrito
como `50/100`.

Cambió los seis que estaban en uso y lo subió el domingo.

El lunes, Vera llamó diciendo que el recibo impreso seguía con el valor
viejo.

El recibo no usaba ninguno de los siete. Tenía el suyo, escrito como
`$dias * 0.50`, en medio de un string de HTML, en una línea de
cuatrocientos doce caracteres.
:::

## Una regla en diez lugares

El código duplicado no da error. No aparece en el log, no rompe nada, no se
queja en la revisión — sobre todo cuando las copias son levemente
distintas, como `0.5`, `50/100` y `0.50`.

Solo se manifiesta cuando la regla cambia. Y las reglas siempre cambian: es
el único requisito garantizado de cualquier sistema.

:::key
La pregunta que identifica la duplicación problemática no es "¿este código
se parece?". Es: **"cuando esta regla cambie, ¿de cuántos lugares tengo que
acordarme?"**

Si la respuesta es mayor que uno, hay una función esperando nacer.
:::

:::art caption="Cambiar el número es fácil. Lo difícil es encontrar todos los lugares donde vive."
src="trocar-o-numero-e-facil-dificil-e-achar-todos-os-lugares-onde-ele-mora.png"
Viñeta editorial minimalista sobre fondo blanco: un desarrollador de
treinta y pocos años, con sudadera, sostiene una lupa sobre un enorme mapa
de archivos desplegado en la mesa. Siete marcas rojas muestran el mismo
número escrito de maneras distintas — "0.5", "0.50", "50/100" — y todas ya
están tachadas con una X. Fuera del mapa, en la punta de la mesa, una
pequeña impresora de recibos suelta una tira de papel con el valor viejo,
que nadie está mirando. Detrás de él, una pasante con el cuaderno abierto
señala la tira. Pocos elementos, humor seco, estética de revista de
tecnología.
:::

## Ponerle nombre a la decisión

```php title="multa.php" numbered
<?php

function multaEnCentavos(int $dias_de_atraso): int
{
    if ($dias_de_atraso <= 0) {
        return 0;
    }

    return min($dias_de_atraso * 80, 2000);
}

echo multaEnCentavos(0), "\n";
echo multaEnCentavos(3), "\n";
echo multaEnCentavos(90), "\n";
```

```text
0
240
2000
```

La palabra `function`, el nombre, los parámetros entre paréntesis, el tipo
de lo que vuelve, y el cuerpo entre llaves.

`return` hace dos cosas a la vez: devuelve el valor **y termina la función
en el acto**. Nada después de él se ejecuta. Por eso el primer `if` no
necesita `else`: si el atraso es cero o negativo, la función ya terminó.

`min()` devuelve el menor de los valores recibidos, lo que aquí funciona
como techo: la multa nunca pasa de dos mil centavos.

Y fíjate dónde están los dos números de la regla — `80` y `2000`. En un
solo lugar. Es la diferencia entre que la búsqueda de Dedé devuelva siete
resultados o uno.

:::anatomy title="Las partes de una función"
lang: php
code: |
  function multaEnCentavos(
      int $dias,
      int $por_dia = 80,
  ): int {
      return min($dias * $por_dia, 2000);
  }
notes:
  - { line: 1, text: "El nombre es un verbo o una pregunta. `multa()` es ambiguo; `multaEnCentavos()` dice hasta la unidad." }
  - { line: 2, text: "`int $dias` es obligatorio: quien llama tiene que informarlo, y tiene que ser entero." }
  - { line: 3, text: "`= 80` es el valor por defecto. Un parámetro con valor por defecto va siempre después de los obligatorios." }
  - { line: 3, text: "La coma en el último parámetro está permitida desde PHP 8 y evita ruido cuando alguien agrega otro." }
  - { line: 4, text: "`: int` es el tipo del retorno. Sin él, la función promete cualquier cosa." }
:::

Los tipos no son adorno. Con ellos, pasa esto:

```text
$ php -r 'function m(int $d): int { return $d * 80; } echo m("tres");'
PHP Fatal error: Uncaught TypeError: m(): Argument #1 ($d)
must be of type int, string given
```

La función rechazó el argumento equivocado en la puerta, con un mensaje que
dice qué argumento, qué tipo se esperaba y cuál llegó. Sin la declaración
`int`, PHP intentaría convertir `"tres"` y produciría un resultado sin
sentido, en silencio.

## Tratar el caso malo y salir

El `return` en medio de la función abre una forma de escribir decisiones que
antes no existía:

:::compare left="Anidado" right="Cláusula de guarda" lang="php"
function prestar($l, $e) {
    if ($l !== null) {
        if ($l['activo']) {
            if (!$e['preso']) {
                return 'ok';
            }
        }
    }
    return 'rechazado';
}
---
function prestar($l, $e) {
    if ($l === null) {
        return 'sin lector';
    }
    if (!$l['activo']) {
        return 'inactivo';
    }
    if ($e['preso']) {
        return 'no disponible';
    }
    return 'ok';
}
:::

Esto se llama **cláusula de guarda**: trata el caso malo, sal, y deja el
camino principal pegado al margen izquierdo.

El lado izquierdo crece hacia la derecha con cada regla nueva. Con las once
reglas de Vera, el `return 'ok'` quedaría a cuarenta y cuatro espacios del
margen, y quien lee tendría que sostener once condiciones en la cabeza para
entender cómo llegó ahí.

Y fíjate en la ganancia que no es de formato: cada motivo de rechazo quedó
**al lado de su condición**, en lugar de en un `return` genérico a doce
líneas de distancia. La versión de la derecha puede decir por qué rechazó;
la de la izquierda, no.

:::key
Si el cuerpo principal de tu función está en tres niveles de sangría, casi
siempre faltan guardas al principio. La sangría profunda no es un problema
estético: es la cantidad de condiciones que el lector tiene que mantener en
la cabeza al mismo tiempo.
:::

## Parámetros que se leen

```php title="llamadas.php" numbered
<?php

function registrarDevolucion(
    int $prestamo_id,
    int $dias_de_atraso,
    bool $eximir_multa = false,
    bool $notificar_lector = true,
): void {
    echo $prestamo_id, ' ', $dias_de_atraso, ' ',
         var_export($eximir_multa, true), ' ',
         var_export($notificar_lector, true), "\n";
}

registrarDevolucion(812, 9);
registrarDevolucion(812, 9, true, false);
registrarDevolucion(812, 9, eximir_multa: true);
```

```text
812 9 false true
812 9 true false
812 9 true true
```

`: void` dice que la función no devuelve nada — hace algo y listo.
`var_export($x, true)` devuelve el valor como texto, lo que aquí sirve para
ver `true` y `false`, que `echo` imprimiría como `1` y nada.

La tercera llamada usa **argumentos con nombre**, un recurso de PHP 8.
Compárala con la segunda: `registrarDevolucion(812, 9, true, false)` obliga
a quien lee a abrir la función para descubrir qué son ese `true` y ese
`false`.

:::key
Cuando una llamada tenga un `true` o un `false` suelto, nombra el argumento.
Es la ganancia de legibilidad más barata que existe — cero costo de
ejecución, cero líneas de más — y resuelve para siempre la duda de quien lea
el código dentro de seis meses, que probablemente seas tú.
:::

Los argumentos con nombre también permiten saltarse los del medio: en la
tercera llamada, `$eximir_multa` se informó sin mencionar
`$notificar_lector`.

:::pitfall
Al adoptar argumentos con nombre, el **nombre del parámetro se vuelve
contrato público**. Renombrar `$eximir_multa` a `$sin_multa` pasa a romper a
quien llama, y el error solo aparece en ejecución, con un mensaje sobre un
argumento desconocido.

En código de biblioteca eso es serio. En código de aplicación, es una
molestia manejable. Vale saberlo antes de renombrar, no después.
:::

## Promete un solo tipo

```php title="retorno.php" numbered
<?php

function buscarLector(int $id): ?array
{
    $lectores = [
        47 => ['nombre' => 'Marlene'],
        12 => ['nombre' => 'Juvenal'],
    ];

    return $lectores[$id] ?? null;
}

var_dump(buscarLector(47));
var_dump(buscarLector(99));
```

```text
array(1) { ["nombre"]=> string(7) "Marlene" }
NULL
```

El signo de interrogación en `?array` significa "array o `null`". Es un
contrato honesto: quien llama sabe, mirando la firma, que tiene que tratar
la ausencia.

Lo que **no** quieres es una función que devuelva cosas de naturalezas
distintas según el día:

:::compare left="Promesa rota" right="Promesa honesta" lang="php"
function buscar($id) {
    if (!$id) {
        return false;
    }
    if ($error) {
        return "error";
    }
    return $datos;
}
---
function buscar(int $id): ?array
{
    return $this_acervo[$id]
        ?? null;
}
:::

Del lado izquierdo, quien llama tiene que probar tres tipos distintos y
además distinguir `false` de `"error"` y de un array vacío. Es el tipo de
función que produce, en cada punto de uso, un `if` de cinco líneas — y lo
que pasa en la práctica es que alguien escribe `if (!$resultado)` y vuelve
al defecto del informe de Vera.

Del lado derecho hay una sola respuesta: el registro, o nada.

## El informe que dio cero

:::story El informe que dio cero
Tainá escribió la totalización del informe mensual. La probó. Dio cero.

```php
$total_general = 0;

function sumar(int $valor): void
{
    $total_general = $total_general + $valor;
}

foreach ($multas as $m) {
    sumar($m);
}

echo $total_general;
```

— No tiene sentido — dijo. — Sumé ocho mil reales y me imprime cero.

Dedé miró dos segundos.

— Imprime cero porque la `$total_general` de adentro de la función no es la
de afuera. Son dos variables con el mismo nombre, y la de adentro muere
cuando la función termina.

— Pero en Python eso daría error.

— En PHP da un aviso y sigue.

— Eso es peor.

— Es mucho peor.
:::

```text
PHP Warning: Undefined variable $total_general in /app/inf.php
on line 5
```

Un aviso, no un error fatal. El programa siguió, sumó cero con cero ocho mil
veces, e imprimió un número perfectamente plausible.

En PHP, el alcance de una función es **cerrado**. A diferencia de
JavaScript y de Python, una función no ve las variables de afuera — ni
siquiera para leerlas:

```php title="alcance.php" numbered
<?php

$plazo = 14;

function diasDePrestamo(): int
{
    return $plazo;
}

echo diasDePrestamo(), "\n";
```

```text
PHP Warning: Undefined variable $plazo
PHP Fatal error: Uncaught TypeError: diasDePrestamo():
Return value must be of type int, null returned
```

Fíjate en que el tipo de retorno salvó el día. Sin el `: int`, la función
devolvería `null` en silencio y el problema aparecería tres pantallas más
adelante.

Existe una palabra clave que rompe la regla del alcance:

```php
function sumar(int $valor): void
{
    global $total_general;
    $total_general = $total_general + $valor;
}
```

Esto funciona, y es casi siempre la respuesta equivocada.

:::warning
Una función que lee o escribe una variable global no se puede probar sola,
no se puede llamar dos veces con confianza, y no se puede entender sin
conocer el programa entero.

Peor: crea una dependencia **invisible**. Nada en la firma dice que esa
función necesita `$total_general` — quien lee `sumar(int $valor): void` no
tiene forma de saberlo.

La regla que lo evita cabe en una frase: **todo lo que la función necesita
entra por parámetro; todo lo que produce sale por el retorno.**
:::

La versión correcta no usa nada que no hayas visto todavía:

```php title="correcto.php" numbered
<?php

function sumarMultas(array $multas): int
{
    $total = 0;

    foreach ($multas as $valor) {
        $total = $total + $valor;
    }

    return $total;
}

echo sumarMultas([50, 240, 2000]), "\n";
```

```text
2290
```

## Una función que se puede probar

La `multaEnCentavos()` del principio del capítulo tiene una propiedad que
vale nombrar: dado el mismo número de días, devuelve **siempre** el mismo
resultado, y no toca nada fuera de ella. Eso se llama **función pura**.

La consecuencia práctica es que se puede verificar la regla entera sin base
de datos, sin servidor y sin abrir el navegador:

```php title="verificar_multa.php" numbered
<?php

function multaEnCentavos(int $dias): int
{
    if ($dias <= 0) {
        return 0;
    }

    return min($dias * 80, 2000);
}

$casos = [
    [-3, 0],
    [0, 0],
    [1, 80],
    [24, 1920],
    [25, 2000],
    [90, 2000],
];

foreach ($casos as [$dias, $esperado]) {
    $obtenido = multaEnCentavos($dias);
    $marca = $obtenido === $esperado ? 'ok    ' : 'FALLO ';

    echo $marca, ' ', $dias, ' dias -> ', $obtenido, "\n";
}
```

```text
ok     -3 dias -> 0
ok     0 dias -> 0
ok     1 dias -> 80
ok     24 dias -> 1920
ok     25 dias -> 2000
ok     90 dias -> 2000
```

Seis casos, un archivo, milisegundos. Eso es un test — sin framework, sin
biblioteca, sin configuración. El `foreach ($casos as [$dias, $esperado])`
desempaqueta cada par directamente en las dos variables, y la comparación
con `===` verifica valor y tipo.

Fíjate en los casos elegidos: `24` y `25` rodean el punto en que el techo
empieza a valer, y `-3` cubre la devolución anticipada. Probar el **borde**,
y no solo un valor cualquiera del medio, es lo que hace que este archivo
valga algo.

Ahora compáralo con lo que sería verificar la misma regla dentro de aquel
string de HTML de cuatrocientos doce caracteres del recibo. No es que fuera
difícil: es que no existe un punto de entrada. La función no es una
formalidad — es lo que vuelve **alcanzable** la regla.

:::note En tu carrera
"Extraer una función" es la refactorización más segura que existe y la más
subestimada en las entrevistas técnicas. Cuando te pidan mejorar un
fragmento de código, empieza por ahí, antes de proponer arquitectura,
patrones de diseño o microservicios.

Y hay un efecto secundario valioso en código legado: no necesitas permiso
para extraer una función. No cambia el comportamiento, no cambia la base de
datos, no cambia el contrato con nadie. Es la única mejora que se puede
hacer un martes cualquiera, mientras arreglas otra cosa, sin convocar una
reunión.
:::

## Una función también puede ser un valor

```php title="closure.php" numbered
<?php

$formatear = function (int $centavos): string {
    return 'R$ ' . number_format($centavos / 100, 2, ',', '.');
};

echo $formatear(2000), "\n";
```

```text
R$ 20,00
```

Una función sin nombre, guardada en una variable. Se llama **closure**, y la
variable pasa a poder llamarse como si fuera el nombre de una función.

Las closures siguen la misma regla de alcance: no ven lo que está afuera.
Para capturar una variable, la pides:

```php title="use.php" numbered
<?php

$multa_por_dia = 80;

$calcular = function (int $dias) use ($multa_por_dia): int {
    return $dias * $multa_por_dia;
};

echo $calcular(3), "\n";

$multa_por_dia = 150;
echo $calcular(3), "\n";
```

```text
240
240
```

Mira las dos salidas. `use ($x)` captura **por valor**, en el momento en que
se crea la closure — cambiar la variable después no cambia nada adentro.
Existe `use (&$x)`, por referencia, que es raro y casi siempre un síntoma.

Las **arrow functions** acortan el caso común:

```php title="arrow.php" numbered
<?php

$multa_por_dia = 80;

$calcular = fn(int $dias): int => $dias * $multa_por_dia;

echo $calcular(3), "\n";
```

```text
240
```

Una sola expresión, sin llaves, sin `return`, sin `use` — la arrow function
captura automáticamente lo que necesita, siempre por valor. Es la forma que
cabe cómodamente dentro de otra llamada, y ahí es donde gana.

## El bucle que se volvió expresión

¿Te acuerdas del acumulador del capítulo @cap:repeticoes? Cuando el bucle
solo transforma una colección en otra, hay una forma más corta de decirlo:

```php title="map_filter.php" numbered
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas', 'dias' => 2],
    ['titulo' => 'Sertão', 'dias' => 41],
];

$criticos = array_filter(
    $atrasados,
    fn(array $e): bool => $e['dias'] > 30
);

$multas = array_map(
    fn(array $e): int => multaEnCentavos($e['dias']),
    $atrasados
);

print_r(array_column($criticos, 'titulo'));
print_r($multas);
```

```text
Array
(
    [0] => Sertão
)
Array
(
    [0] => 720
    [1] => 160
    [2] => 2000
)
```

`array_filter` recibe la colección y una función que responde sí o no para
cada elemento; devuelve los que pasaron. `array_map` recibe una función y la
colección — en ese orden, que es el inverso de la otra, porque así pasó en
1999 — y devuelve el resultado de aplicar la función a cada elemento.

:::pitfall
`array_filter` **conserva las claves originales**. En el ejemplo, el
elemento que quedó estaba en la posición 2 y seguiría en la posición 2 — fue
solo la impresión, que vino después de `array_column`, la que renumeró.

Es exactamente el defecto que dejó la aplicación de la Casa Amarela con la
pantalla vacía en el capítulo @cap:arrays. Antes de mandar el resultado de
un `array_filter` fuera de PHP, `array_values`.
:::

La regla para elegir entre bucle y expresión es simple: si el código
**transforma** una colección en otra, `array_map` y `array_filter` lo dicen
mejor. Si **hace cosas** — guarda, envía, imprime, registra —, el `foreach`
es más claro.

## Comportamiento como argumento

Lo que hace posible `array_map` es que una función puede recibir otra
función:

```php title="callable.php" numbered
<?php

function aplicarEn(array $elementos, callable $operacion): array
{
    $salida = [];

    foreach ($elementos as $elemento) {
        $salida[] = $operacion($elemento);
    }

    return $salida;
}

$centavos = [50, 240, 2000];

print_r(aplicarEn($centavos, fn(int $c): float => $c / 100));
```

```text
Array
(
    [0] => 0.5
    [1] => 2.4
    [2] => 20
)
```

El tipo `callable` dice "aquí entra algo que se puede llamar". La función
`aplicarEn` no sabe qué se va a hacer con los elementos — solo sabe que algo
se va a hacer. Es, a propósito, una copia casera de `array_map`, y
escribirla una vez es lo que hace que `array_map` deje de parecer magia.

:::summary
- Extrae una función cuando la respuesta a "¿de cuántos lugares tengo que
	acordarme?" sea mayor que uno.
- `return` devuelve el valor y termina la función en el acto.
- Los tipos en parámetros y retorno rechazan el error en la puerta, con un
	mensaje útil.
- La cláusula de guarda trata el caso malo y sale, manteniendo el camino
	principal en el margen.
- Nombra el argumento siempre que sea un `true` o `false` suelto.
- Promete un solo tipo; `?array` es honesto, tres tipos distintos no.
- El alcance de una función es cerrado: lo que entra, entra por parámetro.
- `global` crea una dependencia invisible e impide verificar la función
	sola.
- Una función pura se puede probar en un archivo, sin ningún framework.
- La closure captura por valor con `use`; la arrow function captura sola.
- `array_map` y `array_filter` para transformar; `foreach` para hacer
	cosas.
:::

:::checkpoint
Extraes una regla a una función con tipos declarados, escribes guardas en
vez de anidar, explicas por qué `global` es un síntoma, y armas un archivo
de verificación que prueba la regla en los bordes.
:::

:::exercise level=1
Escribe una función que reciba la cantidad de días de préstamo y devuelva el
plazo de devolución como texto, usando 14 días como valor por defecto.
Llámala de tres formas: sin argumento, con argumento posicional y con
argumento con nombre.

:::answer
```php
<?php

function plazoEnDias(int $dias = 14): string
{
    return "Devolver en {$dias} dias";
}

echo plazoEnDias(), "\n";
echo plazoEnDias(7), "\n";
echo plazoEnDias(dias: 21), "\n";
```

```text
Devolver en 14 dias
Devolver en 7 dias
Devolver en 21 dias
```

Con un solo parámetro, el argumento con nombre no gana nada. Empieza a valer
a partir del tercer parámetro, y vale mucho cuando alguno de ellos es
booleano.
:::

:::exercise level=2
La función de abajo está haciendo dos cosas. Sepárala en dos y explica qué
ganaste.

```php
function procesarDevolucion(array $prestamo): string
{
    $dias = $prestamo['dias_de_atraso'];
    $multa = 0;

    if ($dias > 0) {
        $multa = min($dias * 80, 2000);
    }

    return 'R$ ' . number_format($multa / 100, 2, ',', '.');
}
```

:::answer
```php
<?php

function multaEnCentavos(int $dias): int
{
    if ($dias <= 0) {
        return 0;
    }

    return min($dias * 80, 2000);
}

function enReales(int $centavos): string
{
    return 'R$ ' . number_format($centavos / 100, 2, ',', '.');
}

echo enReales(multaEnCentavos(9)), "\n";
```

```text
R$ 7,20
```

Tres ganancias concretas.

**El cálculo se volvió verificable.** `multaEnCentavos(25)` devuelve `2000`,
un número que se puede comparar. La versión original devolvía `"R$ 20,00"`,
y verificar una regla de negocio comparando texto formateado es como medir
la temperatura por el color de la pared.

**El formato se volvió reutilizable.** `enReales()` sirve para multas, para
donaciones, para cualquier valor. En la versión original, estaba atado a la
multa.

**Las dos cambian por motivos distintos.** El valor diario cambia por
decisión de la dirección; el formato del texto cambia si algún día la
biblioteca emite comprobantes en otro idioma. Cuando dos cosas cambian por
motivos distintos, no deberían estar en la misma función.
:::

:::exercise level=3
El fragmento de abajo es del Sistema y calcula el total de multas del mes.
Tiene tres defectos: uno que impide verificar la función, uno que impide
reutilizarla, y uno que hace que el resultado quede mal por centavos.
Señala los tres y reescríbelo.

```php
$total = 0;

function acumular($prestamo)
{
    global $total;

    $dias = $prestamo['dias'];

    if ($dias > 0) {
        $total += $dias * 0.80;
    }
}

foreach ($prestamos as $p) {
    acumular($p);
}

echo "Total: R$ " . $total;
```

:::answer
**Defecto 1 — `global`.** La función depende de una variable que no está en
su firma. No se puede llamar en un archivo de verificación sin recrear el
entorno entero, y dos llamadas seguidas interfieren entre sí.

**Defecto 2 — no devuelve nada.** Una función que solo produce un efecto
secundario no se puede reaprovechar en ningún otro contexto. Ni en el
informe, ni en el comprobante, ni en ninguna parte.

**Defecto 3 — `0.80` es `float`.** Sumar ocho mil valores en coma flotante
acumula error, y el total del sistema va a diferir del total de la caja en
centavos, sin que nadie sepa cuál de los dos está bien. Y falta el techo de
R$ 20,00, que el acta de la dirección también definió.

```php
<?php

function multaEnCentavos(int $dias): int
{
    if ($dias <= 0) {
        return 0;
    }

    return min($dias * 80, 2000);
}

function totalDeMultasEnCentavos(array $prestamos): int
{
    $total = 0;

    foreach ($prestamos as $p) {
        $total = $total + multaEnCentavos($p['dias']);
    }

    return $total;
}

$prestamos = [
    ['dias' => 9],
    ['dias' => -2],
    ['dias' => 90],
];

$total = totalDeMultasEnCentavos($prestamos);

echo 'Total: R$ ', number_format($total / 100, 2, ',', '.'), "\n";
```

```text
Total: R$ 27,20
```

Fíjate en lo que permite la reescritura que la versión original no
permitía: `totalDeMultasEnCentavos([['dias' => 9]])` se puede llamar en un
archivo de verificación, con tres préstamos inventados, y comparar con un
número esperado. No hace falta que nada esté en línea.

Y fíjate también en que la regla del techo quedó en un solo lugar. Cuando la
dirección vuelva a cambiar de idea — y va a cambiar —, la búsqueda va a
devolver un resultado.
:::

:::story El octavo
El miércoles, Dedé volvió a buscar, ahora `0,50`, con coma.

Un resultado. Un archivo llamado `avisos.php`, que corría todas las
madrugadas y mandaba correos de cobranza a quien estaba atrasado.

— Este no lo abre nadie desde 2016 — dijo.

Tainá miró por encima de su hombro.

— ¿Cómo sabes?

— Tiene un `echo` de depuración comentado en el medio, con la fecha al
lado.

Márcia pasó detrás de los dos y se detuvo.

— ¿Cuánto tardaste en arreglarlo?

— Los siete primeros, cuarenta minutos.

— ¿Y en encontrar el octavo?

— Tres días.

— Pon los tres días en la planilla.
:::
