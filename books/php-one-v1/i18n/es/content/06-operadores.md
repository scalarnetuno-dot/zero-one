---
source_hash: b71768a05326
title: "Operadores"
number: 6
slug: operadores
part: p1
kicker: "El tótem le informó a Dona Marlene que tenía menos tres días de atraso y una multa de R$ 2,40 negativos."
goal: >-
  Calcular, concatenar y combinar valores sin sorpresas — y conocer los
  cuatro puntos en que el orden de evaluación de PHP no es el que leíste.
---

:::story Menos tres días
El tótem de la entrada era la única parte nueva del Sistema. Lo habían
instalado en 2019, con un teclado numérico y una pantalla pequeña, y servía
para que el lector tecleara su carnet y viera su propia situación.

Dona Marlene tecleó el suyo un martes por la mañana y llamó a Vera.

— Mira esto, hija.

```text
LECTOR: 1183 - MARLENE S. COUTINHO
ATRASO: -3 dias
MULTA:  R$ -2,40
```

— Usted devolvió antes del plazo.

— Ya sé. Pero aquí dice que la biblioteca me debe dos con cuarenta.

— No le debe.

— Aquí lo dice.

Vera miró la pantalla un rato. Después miró a Dona Marlene, que tenía
setenta y nueve años y una paciencia infinita para ese tipo de
conversaciones.

— ¿Lo quiere en libros o en dinero?

— En libros está bien.
:::

La cuenta del tótem estaba bien. Faltaba una pregunta antes de ella.

:::art caption="Menos tres días de atraso, y la biblioteca debiendo dos con cuarenta."
src="menos-tres-dias-de-atraso-e-a-biblioteca-devendo-dois-e-quarenta.png"
Viñeta editorial minimalista sobre fondo blanco: un tótem de autoservicio
antiguo, con teclado numérico y una pantalla pequeña donde solo se lee
"MULTA: R$ -2,40". Frente a él, una señora de setenta y nueve años, con
chaqueta de punto y cartera al brazo, señala la pantalla con el índice,
serena e interesada. A su lado, una bibliotecaria mayor, con anteojos,
extiende un libro de tapa dura hacia la señora, como quien paga un vuelto.
Pocos elementos, humor seco, estética de revista de tecnología.
:::

## Aritmética, y las tres divisiones

Los cuatro operadores de siempre funcionan como esperas:

```php title="aritmetica.php" numbered
<?php

$ejemplares = 8000;
$estantes = 37;

echo $ejemplares + $estantes, "\n";
echo $ejemplares - $estantes, "\n";
echo $ejemplares * $estantes, "\n";
echo $ejemplares / $estantes, "\n";
```

```text
8037
7963
296000
216.21621621622
```

Fíjate en la última. La división con `/` devuelve `float` siempre que no sea
exacta — y no puedes colgar 216,216 libros en un estante. Cuando la pregunta
es sobre cosas enteras, existen otros dos operadores:

```php title="divisiones.php" numbered
<?php

$ejemplares = 8000;
$por_estante = 37;

var_dump($ejemplares / $por_estante);
var_dump(intdiv($ejemplares, $por_estante));
var_dump($ejemplares % $por_estante);
```

```text
float(216.21621621622)
int(216)
int(8)
```

`intdiv` devuelve cuántas veces cabe entero: **216 estantes llenos**. El
`%`, llamado módulo o resto, devuelve lo que sobró: **8 libros** para el
estante 217.

Las dos respuestas juntas cuentan la historia completa, y casi siempre es
eso lo que se quiere: cuántas cajas necesito, y cuánto sobra en la última.

:::pitfall
El `%` se vuelve raro con números negativos, y la razón es que sigue el
signo del **dividendo**, no del divisor:

```text
$ php -r 'var_dump(-7 % 3);'
int(-1)
```

Mucha gente espera `2`. Si tu cálculo puede recibir un negativo y necesitas
un resto siempre positivo — para distribuir en ciclos, por ejemplo —, la
forma segura es `(($a % $b) + $b) % $b`.
:::

Existe además la potencia, `**`:

```text
$ php -r 'echo 2 ** 10;'
1024
```

Y, para sumar o restar uno, el atajo `++` y `--`:

```php title="incremento.php" numbered
<?php

$paginas = 10;

$paginas++;
echo $paginas, "\n";

$paginas--;
echo $paginas, "\n";
```

```text
11
10
```

Existe la forma `++$paginas`, antes del nombre, que incrementa y solo
después devuelve el valor. La diferencia entre las dos solo aparece cuando
usas el resultado en la misma expresión, lo que es un ahorro de una línea a
cambio de una lectura más difícil. Prefiere incrementar en una línea y usar
el valor en la siguiente.

## La concatenación es `.`, nunca `+`

```php title="concatenar.php" numbered
<?php

$titulo = "O Cortiço";
$anio = 1890;

$linea = $titulo . ' (' . $anio . ')';

echo $linea, "\n";
```

```text
O Cortiço (1890)
```

El punto pega dos textos. Fíjate en que `$anio` es un número y se pegó sin
quejas: el `.` exige texto, así que el número se vuelve texto.

En PHP, `+` es **siempre** aritmético. No existe la suma de textos:

```text
$ php -r 'var_dump("a" + "b");'
PHP Fatal error: Uncaught TypeError: Unsupported operand
types: string + string
```

Eso molesta a quien viene de JavaScript y es, en la práctica, una ventaja.
En PHP, `"10" + 5` nunca va a devolver `"105"` por accidente: o es una
cuenta, o es un error.

## Asignar y operar a la vez

```php title="compuesta.php" numbered
<?php

$total = 0;
$total += 80;       // lo mismo que $total = $total + 80
$total += 80;
echo $total, "\n";

$informe = "Atrasados:\n";
// lo mismo que $informe = $informe . "- Marlene..."
$informe .= "- Marlene\n";
$informe .= "- Juvenal\n";
echo $informe;
```

```text
160
Atrasados:
- Marlene
- Juvenal
```

Todos los operadores aritméticos tienen su forma compuesta: `+=`, `-=`,
`*=`, `/=`, `%=`, `**=`. Y el `.` tiene la suya, `.=`, que es como se arma
un texto de a poco.

El `.=` tiene un uso que aparece todo el tiempo: armar un informe línea por
línea, agregando al final de una variable que empezó vacía.

## Cuando el valor puede no estar

```php title="coalescencia.php" numbered
<?php

$tema = null;

$etiqueta = $tema ?? 'General';

echo $etiqueta, "\n";
```

```text
General
```

El `??` es la **fusión de null** (*null coalescing*): devuelve el lado
izquierdo si existe y no es nulo; si no, devuelve el derecho. Existe porque
la alternativa es una escalera de tres líneas para cada valor opcional.

Existe también `??=`, que solo asigna si lo que había era nulo:

```php
$estado ??= 'disponible';
```

Hay un primo parecido y peligroso, el `?:`, llamado ternario corto. La
diferencia entre los dos es exactamente la trampa del capítulo
@cap:variaveis-e-tipos:

:::compare left="`?:` mira si es falso" right="`??` mira si es nulo" lang="php"
$m = $multa ?: 500;
// multa = 0 se vuelve 500
---
$m = $multa ?? 500;
// multa = 0 sigue siendo 0
:::

El `?:` pregunta "¿este valor es falso?", y cero es falso. El `??` pregunta
"¿este valor es nulo?", y cero no es nulo. Cuando el valor en juego sea un
número o un texto que legítimamente puede ser cero o vacío, `??` es el
operador correcto y `?:` es un defecto esperando el día indicado.

## El ternario completo

```php title="ternario.php" numbered
<?php

$dias = 3;

$mensaje = $dias > 0 ? 'con atraso' : 'al dia';

echo $mensaje, "\n";
```

```text
con atraso
```

Se lee: si la condición es verdadera, el valor es el del medio; si no, el
del final. Es un `if/else` que **devuelve un valor** en lugar de ejecutar
bloques, y sirve bien cuando la decisión cabe cómodamente en una línea.

:::pitfall
El ternario anidado está prohibido por consecuencia, no por gusto. Desde
PHP 8, escribir uno dentro de otro sin paréntesis es un **error de
sintaxis**:

```text
$ php -r 'echo true ? 1 : true ? 2 : 3;'
PHP Fatal error: Unparenthesized `a ? b : c ? d : e` is not
supported
```

El lenguaje pasó a rechazar la construcción porque su orden de evaluación
sorprendía a todos, incluida la persona que la había escrito. Cuando la
decisión tiene tres salidas, merece un `if` con nombre.
:::

## Comparar devolviendo un número

```php title="nave.php" numbered
<?php

$dias = 9;
$limite = 14;

var_dump($dias <=> $limite);
var_dump($limite <=> $dias);
var_dump($dias <=> 9);
```

```text
int(-1)
int(1)
int(0)
```

El `<=>` se llama **nave espacial** por su forma. Devuelve `-1` si el lado
izquierdo es menor, `1` si es mayor y `0` si son iguales.

Tres respuestas en un solo operador parece una curiosidad hasta que
necesitas ordenar una lista. Todo algoritmo de ordenamiento hace la misma
pregunta miles de veces — "estos dos, ¿cuál va primero?" — y `-1`, `0` y
`1` son exactamente las tres respuestas posibles. Cuando haya una lista de
préstamos para ordenar por fecha de devolución, es este operador el que va a
responder.

## Precedencia

El orden completo de evaluación tiene veinte niveles y no vale la pena
memorizarlo. Sí vale conocer los cuatro puntos en que la gente se equivoca:

| Escrito | Leído como | La sorpresa |
|---|---|---|
| `!$a === $b` | `(!$a) === $b` | `!` va antes que `===` |
| `$a . $b + $c` | error en PHP 8 | antes era `($a . $b) + $c` |
| `$a ?? $b ? $c : $d` | error de sintaxis | `??` y `?:` no se mezclan |
| `$a = $b or $c` | `($a = $b) or $c` | `or` es más débil que `=` |

Tabla: La última línea es la razón de que existan `and` y `or` en palabras
además de `&&` y `||` — y la razón de no usarlos.

La primera línea merece atención porque produce un defecto que pasa una
revisión. Escribes `!$activo === $esperado` pensando "no es verdad que
activo sea igual a esperado". PHP lee "lo contrario de activo es igual a
esperado", que es otra pregunta y a veces da la misma respuesta — hasta el
día en que no.

:::key
Un paréntesis no cuesta nada en ejecución ni en lectura. Si dos personas en
una revisión de código tienen que detenerse a discutir el orden de
evaluación, el paréntesis ya debería estar ahí.
:::

Y hay un comportamiento de `&&` y `||` que vale conocer, porque deja de ser
una curiosidad y se vuelve protección: los dos **cortocircuitan**. El lado
derecho solo se evalúa si el izquierdo no decidió la cuestión por sí solo.

```php
if ($dias_de_atraso > 0 && calcularMulta($prestamo) > 0) {
```

Si `$dias_de_atraso` es cero, el `&&` ya sabe que el resultado es falso y la
función ni siquiera se llama. Invertir el orden de los dos lados haría que
la cuenta corriera ocho mil veces sin necesidad.

## La pregunta que faltaba en el tótem

```php title="atraso.php (el Sistema)" numbered
<?php

$dias_de_atraso = 14 - 17;
$multa_en_centavos = $dias_de_atraso * 80;

echo $dias_de_atraso, " dias, ", $multa_en_centavos, " centavos\n";
```

```text
-3 dias, -240 centavos
```

La resta es correcta. El problema es que responde "cuántos días de
diferencia", y el tótem muestra la respuesta como si fuera "cuántos días de
atraso". Devolver antes del plazo produce una diferencia negativa, y el
resto del programa se la creyó.

El arreglo tiene una línea:

```php title="atraso.php (corregido)" numbered
<?php

$diferencia = 14 - 17;
$dias_de_atraso = max(0, $diferencia);
$multa_en_centavos = $dias_de_atraso * 80;

echo $dias_de_atraso, " dias, ", $multa_en_centavos, " centavos\n";
```

```text
0 dias, 0 centavos
```

`max()` devuelve el mayor de los valores recibidos. Con `0` como uno de los
lados, se vuelve un piso: el resultado nunca baja de cero. Existe `min()`
para lo opuesto, que es como se escribe un techo — y es exactamente lo que
limita la multa a veinte reales.

:::key
Toda cuenta que puede dar negativo necesita una decisión explícita sobre qué
hacer cuando lo dé. `max(0, $x)` es una decisión; dejarlo pasar también lo
es, solo que tomada por omisión y descubierta por Dona Marlene.
:::

:::note En tu carrera
El defecto del tótem llevaba cinco años en producción y nadie había abierto
un reclamo, porque los lectores que devolvían antes miraban la pantalla, les
parecía raro y se iban. El sistema solo registra lo que alguien reclama.

Cuando heredes un sistema, la lista de reclamos abiertos no es la lista de
defectos: es la lista de defectos que molestaron a alguien lo suficiente
como para justificar una llamada. La diferencia entre las dos listas suele
ser grande, y la segunda solo aparece cuando te sientas al lado de quien lo
usa.

Una tarde de observación en el mostrador rinde más que una semana leyendo
código. Lleva un cuaderno y no sugieras nada el primer día.
:::

:::summary
- `/` devuelve `float`; `intdiv` devuelve el entero; `%` devuelve el resto,
	con el signo del dividendo.
- La concatenación es `.`; `+` es siempre aritmético y da error entre
	textos.
- `+=` y `.=` acumulan valores y texto.
- `??` mira si es nulo; `?:` mira si es falso — y el cero separa a los dos.
- `<=>` devuelve −1, 0 o 1, que son las tres respuestas que necesita un
	ordenamiento.
- El ternario anidado sin paréntesis es error de sintaxis desde PHP 8.
- `&&` y `||` cortocircuitan: el orden de los lados es una protección.
- Una cuenta que puede dar negativo necesita `max(0, ...)` o una decisión
	escrita sobre qué hacer.
:::

:::checkpoint
Escribes una expresión con cuatro operadores y prevés el resultado sin
ejecutarla, eliges entre `/`, `intdiv` y `%` según la pregunta que haces, y
sabes cuándo `??` y `?:` dan respuestas distintas.
:::

:::exercise level=1
La Casa Amarela recibió una donación de 250 libros y tiene cajas donde caben
18 cada una. ¿Cuántas cajas llenas salen, y cuántos libros sobran en la
última? Imprime las dos respuestas.

:::answer
```php
<?php

$libros = 250;
$por_caja = 18;

$llenas = intdiv($libros, $por_caja);
$sobra = $libros % $por_caja;

echo $llenas, " cajas llenas y ", $sobra, " libros en la ultima\n";
```

```text
13 cajas llenas y 16 libros en la ultima
```

Si la pregunta fuera "cuántas cajas necesito comprar", la respuesta sería 14
— y la cuenta sería
`intdiv($libros, $por_caja) + ($libros % $por_caja > 0 ? 1 : 0)`, o
simplemente `ceil($libros / $por_caja)`.

La diferencia entre 13 y 14 es la diferencia entre dos preguntas parecidas,
y quien entrega la respuesta equivocada normalmente no se equivocó en la
cuenta.
:::

:::exercise level=2
Sin ejecutarlo, di lo que imprime cada línea.

```php
$a = null;
$b = 0;

echo $a ?? 'vacio', "\n";
echo $b ?? 'vacio', "\n";
echo $b ?: 'vacio', "\n";
```

:::answer
```text
vacio
0
vacio
```

La primera: `$a` es nulo, así que el `??` devuelve el lado derecho.

La segunda: `$b` es cero, que **no es nulo**, así que el `??` devuelve el
propio cero.

La tercera: `$b` es cero, que **es falso**, así que el `?:` devuelve el lado
derecho — y una multa de cero reales acaba de convertirse en la palabra
"vacio" en el comprobante de alguien.
:::

:::exercise level=3
El fragmento de abajo calcula el valor a devolver a un lector que pagó una
multa por adelantado y después tuvo el atraso recalculado. Tiene dos
defectos. Señala los dos y escribe la versión correcta.

```php
$pagado = 1500;
$debido = 800;

$diferencia = $pagado - $debido;
$mensaje = $diferencia ?: 'nada que devolver';

echo "Devolver: R$ " . $diferencia / 100 . "\n";
echo $mensaje . "\n";
```

:::answer
**Defecto 1: el `?:` con un número.** Cuando `$pagado` y `$debido` sean
iguales, `$diferencia` es cero, el `?:` considera falso el cero y `$mensaje`
recibe `'nada que devolver'`. En este caso específico funciona por
casualidad — pero el mismo código, con la intención de mostrar el valor,
escondería cualquier diferencia de cero. La pregunta correcta es sobre el
valor, no sobre si es verdadero.

**Defecto 2: la cuenta puede dar negativo.** Si el recálculo aumenta la
multa, `$debido` pasa a ser mayor que `$pagado` y el sistema anuncia
"Devolver: R$ -3.5", que es otra vez el defecto del tótem, con otra ropa.

```php
$pagado = 1500;
$debido = 800;

$a_devolver = max(0, $pagado - $debido);
$a_cobrar = max(0, $debido - $pagado);

$reales = number_format($a_devolver / 100, 2, ',', '.');

if ($a_devolver > 0) {
    echo "Devolver: R$ ", $reales, "\n";
} elseif ($a_cobrar > 0) {
    echo "Cobrar la diferencia\n";
} else {
    echo "Nada que ajustar\n";
}
```

Lo que cambió de verdad no fue la cuenta: fueron las **tres salidas**. El
código original tenía dos variables y suponía un único escenario; la versión
corregida reconoce que "pagó de más", "pagó de menos" y "pagó justo" son
tres situaciones distintas, y que el programa necesita saber en cuál está.

Fíjate también en que la división por 100 aparece una sola vez, al armar el
texto. La cuenta entera se hizo en centavos.
:::
