---
source_hash: 0772deb72155
title: "Arrays"
number: 8
slug: arrays
part: p1
kicker: "La estructura más usada de PHP es también la peor usada — y una línea suya ya tumbó la aplicación de mil doscientas personas."
goal: >-
  Guardar varias cosas en una sola variable, elegir entre lista y mapa,
  entender por qué las dos son el mismo tipo en PHP, y saber cuándo esa
  igualdad se vuelve un defecto.
---

Hasta aquí, cada variable guardó una cosa: un título, una cantidad de días,
un valor en centavos. El acervo de la Casa Amarela tiene ocho mil
ejemplares, y `$ejemplar1`, `$ejemplar2`, `$ejemplar3` deja de ser gracioso
en el cuarto.

## Varias cosas en una sola variable

```php title="lista.php" numbered
<?php

$registros = [812, 907, 344];

echo $registros[0], "\n";
echo $registros[2], "\n";
echo count($registros), "\n";
```

```text
812
344
3
```

Los corchetes crean un **array**. Los valores van separados por comas, y
cada uno recibe una posición, contada desde **cero** — por eso
`$registros[0]` es el primero y `$registros[2]` es el tercero.

`count()` responde cuántos elementos hay. Fíjate en que `count($registros)`
es `3` y la última posición es `2`: esa diferencia de uno es el origen de
una cantidad impresionante de defectos, y la forma de no volver a
equivocarse es recordar que la numeración de posiciones empieza en cero y el
conteo de elementos no.

Para agregar al final, corchetes vacíos:

```php title="agregar.php" numbered
<?php

$registros = [812, 907];

$registros[] = 344;
$registros[] = 501;

print_r($registros);
```

```text
Array
(
    [0] => 812
    [1] => 907
    [2] => 344
    [3] => 501
)
```

`$registros[] = 344` quiere decir "ponlo en la próxima posición libre". No
necesitas saber cuál es.

Y apareció una herramienta nueva: `print_r` imprime la estructura de un
array de forma legible. `var_dump` también funciona y muestra los tipos, lo
que es más información de la que suele servir cuando solo quieres revisar
el contenido.

## Claves con nombre

La posición numérica sirve cuando lo que importa es el orden. Cuando lo que
importa es **qué significa cada valor**, la clave se vuelve texto:

```php title="mapa.php" numbered
<?php

$ejemplar = [
    'registro' => 812,
    'titulo' => 'O Cortiço',
    'status' => 'disponible',
];

echo $ejemplar['titulo'], "\n";

$ejemplar['status'] = 'prestado';

echo $ejemplar['status'], "\n";
```

```text
O Cortiço
prestado
```

La flecha `=>` une la clave con el valor. El acceso y el cambio usan la
misma sintaxis de corchetes, con el nombre de la clave en lugar del número.

Eso resuelve el problema que Vera tenía con el formulario de dieciocho
campos: en vez de dieciocho variables sueltas, un ejemplar entero cabe en
una variable que se lee en voz alta.

:::key
Usa **clave numérica** cuando los elementos sean intercambiables y el orden
importe — una fila, una lista de resultados, un historial.

Usa **clave de texto** cuando cada posición tenga un significado propio — un
registro, una configuración, un conjunto de opciones.

La pregunta que decide: ¿tiene sentido preguntar "cuál es el tercero"? Si lo
tiene, es una lista. Si no, es un mapa.
:::

## Las dos son la misma cosa

En casi todos los lenguajes existen dos estructuras separadas. Python tiene
`list` y `dict`. JavaScript tiene `Array` y `Object`. Java tiene `List` y
`Map`.

PHP tiene `array`. Uno solo, para los dos usos.

```php title="dos_usos.php" numbered
<?php

$registros = [812, 907, 344];

var_dump($registros);
```

```text
array(3) {
  [0]=> int(812)
  [1]=> int(907)
  [2]=> int(344)
}
```

Fíjate en las claves `0`, `1`, `2`. Están ahí — lo que pasa es que tú no las
escribiste. Una "lista" en PHP es un mapa cuyas claves resultan ser los
enteros desde cero, en orden, sin huecos.

:::term Array en PHP
Un **mapa ordenado**: pares clave→valor que mantienen el orden de inserción.
La clave es `int` o `string`. No existe un tipo de lista separado — lo que
llamamos lista es una convención sobre las claves.
:::

:::history
La decisión es de 1997, cuando Andi Gutmans y Zeev Suraski estaban
escribiendo PHP 3. Una sola estructura simplificaba el intérprete y la vida
de quien escribía, en una época en que la mayor parte del PHP del mundo
procesaba formularios — donde todo llega como pares nombre→valor.

Funcionó durante veinte años. Lo que nadie previó fue que esa misma
estructura se iba a enviar a otros programas en un formato que **sí
distingue** los dos casos.
:::

Desde PHP 8.1 existe una función que responde cuál de los dos tienes en la
mano:

```text
$ php -r 'var_dump(array_is_list([812, 907]));'
bool(true)
$ php -r 'var_dump(array_is_list([0 => 812, 2 => 907]));'
bool(false)
```

El segundo tiene claves `0` y `2`. Falta el `1`. Para PHP, sigue siendo un
array como cualquier otro — y ahí empieza la historia.

## No cambiamos nada

:::story No cambiamos nada
Lunes, 8:50. Tainá abrió el chat de la Casa Amarela y había catorce
mensajes de Vera, todos antes de las ocho de la mañana.

La aplicación del lector ya no mostraba el acervo. Pantalla vacía, sin
error, sin mensaje, sin nada.

— No cambiamos nada el fin de semana — dijo Dedé.

Técnicamente cierto. El viernes él había sacado de la lista los ejemplares
en restauración. Una línea. El servidor seguía respondiendo normalmente, los
datos seguían llegando, los campos seguían con los nombres correctos.

Solo que el viernes lo que salía era esto:

```text
[{"registro":812},{"registro":907}]
```

Y el lunes era esto:

```text
{"0":{"registro":812},"2":{"registro":344}}
```

La aplicación esperaba una lista. Recibió otra cosa. No se rompió —
simplemente no encontró nada que recorrer, y dibujó la pantalla vacía con
mucha competencia.

Márcia se enteró a las 9:15. Su primera pregunta no fue sobre el defecto.

— ¿Hace cuánto está así?

— Desde el viernes, 18 h.

— Entonces fueron dos días y medio. Ponlo en el acta.
:::

:::term JSON
El formato en que dos programas intercambian datos por la red. Es texto, y
tiene dos estructuras: **lista**, entre `[ ]`, y **objeto**, entre `{ }` con
pares nombre→valor. Las dos cosas que PHP decidió llamar array son, en JSON,
tipos distintos — y quien las recibe trata cada una de una manera.
:::

PHP convierte un array a JSON con `json_encode`, y la decisión de volverlo
lista u objeto la toma solo, con un criterio rígido:

```php title="la_regla.php" numbered
<?php

echo json_encode([812, 907, 344]), "\n";
echo json_encode([0 => 812, 1 => 907]), "\n";
echo json_encode([0 => 812, 2 => 344]), "\n";
echo json_encode(['registro' => 812]), "\n";
```

```text
[812,907,344]
[812,907]
{"0":812,"2":344}
{"registro":812}
```

Se vuelve lista JSON **solo** si las claves son exactamente
`0, 1, 2, …, n-1`, en ese orden, sin huecos. Cualquier otra cosa se vuelve
objeto — es la misma pregunta que responde `array_is_list`.

## El hueco que deja `unset`

Lo que Dedé escribió el viernes fue esto:

```php title="el_filtro_del_viernes.php" numbered
<?php

$ejemplares = [
    ['registro' => 812, 'status' => 'disponible'],
    ['registro' => 907, 'status' => 'restauracion'],
    ['registro' => 344, 'status' => 'disponible'],
];

unset($ejemplares[1]);

echo json_encode($ejemplares), "\n";
```

```text
{"0":{"registro":812,"status":"disponible"},
 "2":{"registro":344,"status":"disponible"}}
```

`unset()` elimina un elemento del array. Lo que **no** hace es renumerar los
que quedaron: la posición `1` simplemente dejó de existir, y el elemento que
estaba en la `2` sigue en la `2`.

El array ahora tiene claves `0` y `2`. `json_encode` miró, no encontró la
secuencia y produjo un objeto.

Ninguno de los dos lados se equivocó. PHP hizo exactamente lo que documenta
hacer desde hace veinte años; la aplicación trató un objeto como objeto. El
defecto ocurrió **en la frontera** — y la frontera es donde viven los
problemas que nadie logra reproducir, porque cada lado, probado solo, está
bien.

El arreglo tiene una palabra:

```php title="el_arreglo.php" numbered
<?php

$ejemplares = [
    ['registro' => 812, 'status' => 'disponible'],
    ['registro' => 907, 'status' => 'restauracion'],
    ['registro' => 344, 'status' => 'disponible'],
];

unset($ejemplares[1]);

$ejemplares = array_values($ejemplares);

echo json_encode($ejemplares), "\n";
```

```text
[{"registro":812,"status":"disponible"},
 {"registro":344,"status":"disponible"}]
```

`array_values()` descarta las claves y renumera desde cero. El array vuelve
a ser una lista, y el JSON vuelve a ser una lista.

:::key
**Cada vez que un array vaya a salir de PHP como lista — hacia JSON, hacia
otro programa, hacia una pantalla que espera orden —, garantiza las claves
con `array_values()`.**

La regla parece exagerada hasta que recuerdas que la línea que rompe el
contrato rara vez es la que estás escribiendo ahora. Es la que otra persona
va a agregar a mitad de camino, en marzo, con toda la razón del mundo.
:::

:::note En tu carrera
"No cambiamos nada" es casi siempre falso y casi nunca mentira. La persona
cambió algo que, según su modelo mental, no podía causar eso.

La habilidad que se desarrolla con el tiempo no es recordar todos los
efectos secundarios posibles — es **acotar la búsqueda rápido**. En este
caso: ¿cambió la aplicación? No. ¿Cambió el servidor? Sí, el viernes. ¿Qué
cambió el viernes? Una línea. ¿Qué toca esa línea? La forma de la respuesta.

Cuatro preguntas, dos minutos. Es la diferencia entre una investigación de
media hora y una mañana entera, y se puede entrenar.
:::

## Preguntar si está

Tres funciones parecidas que responden preguntas distintas:

```php title="existe.php" numbered
<?php

$ejemplar = [
    'registro' => 812,
    'observacion' => null,
];

var_dump(isset($ejemplar['registro']));
var_dump(isset($ejemplar['observacion']));
var_dump(array_key_exists('observacion', $ejemplar));
var_dump(in_array(812, $ejemplar));
```

```text
bool(true)
bool(false)
bool(true)
bool(true)
```

La segunda y la tercera línea son el punto. La clave `observacion` **existe**
en el array — solo tiene valor `null`. `isset` responde `false`, porque su
pregunta es "¿existe y no es nulo?". `array_key_exists` responde `true`,
porque su pregunta es solo "¿existe?".

Es la misma distinción entre ausencia y nulo del capítulo
@cap:variaveis-e-tipos, ahora con una consecuencia práctica: si tu código
decide si debe guardar una observación en base a `isset`, nunca va a
guardar una observación en blanco a propósito.

`in_array` busca por el **valor**, no por la clave. Existe también
`array_search`, que devuelve la clave donde lo encontró.

:::pitfall
`in_array` sin el tercer argumento compara con `==`:

```text
$ php -r 'var_dump(in_array(0, ["a", "b"]));'
bool(false)
$ php -r 'var_dump(in_array("1", [1, 2]));'
bool(true)
```

El segundo caso es el que muerde: el texto `"1"` se encontró en una lista de
números. Usa siempre `in_array($x, $lista, true)`, con el tercer argumento,
que la cambia a comparación estricta.
:::

## Copiar un array copia de verdad

```php title="copia.php" numbered
<?php

$a = ['registro' => 812];
$b = $a;

$b['registro'] = 907;

echo $a['registro'], "\n";
echo $b['registro'], "\n";
```

```text
812
907
```

Asignar un array a otra variable **copia** el contenido. Tocar la copia no
toca el original.

Parece obvio y no lo es: en Python y en JavaScript, la misma secuencia
dejaría las dos variables apuntando a la misma lista, y el `812` se habría
vuelto `907` en las dos. Quien llega de uno de esos lenguajes suele
descubrir la diferencia de mala manera.

PHP es económico por dentro — solo duplica de verdad cuando uno de los dos
lados cambia —, así que el costo es menor de lo que parece. Pero existe, y
para un array de cien mil elementos se nota.

## Arrays dentro de arrays

El valor guardado en un array puede ser otro array, y así se representa una
colección de registros:

```php title="acervo.php" numbered
<?php

$acervo = [
    ['registro' => 812, 'titulo' => 'O Cortiço'],
    ['registro' => 907, 'titulo' => 'Vidas Secas'],
];

echo $acervo[0]['titulo'], "\n";
echo count($acervo), "\n";
```

```text
O Cortiço
2
```

Dos corchetes seguidos: el primero elige el registro, el segundo elige el
campo. Es la estructura en que la mayoría de los datos entra y sale de un
sistema PHP.

Funciona bien en dos niveles, tolera tres, y después de eso se vuelve otra
cosa. Esta línea existe en el Sistema:

```php
$datos['libro'][3]['ejemplares'][0]['prestamo']['lector']['nombre']
```

Funciona. Y tiene cuatro problemas que ninguna herramienta puede señalar: el
editor no sugiere nada, un error de tipeo en cualquier nivel devuelve `null`
con un aviso, no hay forma de saber qué claves existen sin ejecutar el
programa, y toda la estructura es un contrato que no está escrito en ninguna
parte.

:::key
Cuando el array tiene tres o más niveles y el formato es **conocido y
fijo**, está pidiendo volverse otra cosa. Guarda el síntoma; el remedio
aparece cuando el lenguaje tenga cómo aplicarlo.
:::

## Desempaquetar y juntar

```php title="desempaquetar.php" numbered
<?php

$par = [812, 907];

[$primero, $segundo] = $par;

echo $primero, " y ", $segundo, "\n";

$ejemplar = ['registro' => 344, 'status' => 'disponible'];

['registro' => $r, 'status' => $s] = $ejemplar;

echo $r, " esta ", $s, "\n";
```

```text
812 y 907
344 esta disponible
```

El desempaquetado por clave, en la segunda forma, es el más útil del
conjunto: extrae solo los campos que interesan y documenta, en la propia
línea, lo que usa el fragmento siguiente.

Y para juntar dos arrays existen tres puntitos:

```php title="juntar.php" numbered
<?php

$disponibles = [812, 907];
$reservados = [344];

$todos = [...$disponibles, ...$reservados];

print_r($todos);
```

```text
Array
(
    [0] => 812
    [1] => 907
    [2] => 344
)
```

El `...` se llama **spread**. Fíjate en que las claves se renumeraron
automáticamente — para listas, ya entrega el resultado en el formato
correcto. Con claves de texto también funciona desde PHP 8.1, con la regla
de que el último repetido gana.

:::summary
- `[]` crea un array; `$a[] = $x` agrega en la próxima posición libre.
- La numeración de posiciones empieza en cero; `count()` devuelve la
	cantidad.
- Clave numérica para una lista, clave de texto para un registro.
- Un array en PHP es un mapa ordenado — la lista es solo una convención
	sobre las claves.
- Se vuelve lista en JSON solo con claves `0..n-1` sin huecos; `unset` abre
	un hueco y `array_values` lo cierra.
- `isset` dice "existe y no es nulo"; `array_key_exists` dice solo
	"existe".
- `in_array` compara con `==` a menos que pases `true` como tercer
	argumento.
- Un array se copia por valor, a diferencia de Python y JavaScript.
- Tres niveles de profundidad son un síntoma de que falta otra estructura.
:::

:::checkpoint
Creas listas y mapas, agregas y quitas elementos, sabes decir si un array va
a volverse lista u objeto en JSON, y puedes explicar por qué `isset` y
`array_key_exists` no coinciden.
:::

:::exercise level=1
Arma un array con tres ejemplares, cada uno con número de registro, título y
estado. Imprime el título del segundo, la cantidad total, y después agrega
un cuarto ejemplar e imprime la cantidad de nuevo.

:::answer
```php
<?php

$acervo = [
    ['registro' => 812, 'titulo' => 'O Cortiço', 'status' => 'libre'],
    ['registro' => 907, 'titulo' => 'Vidas', 'status' => 'restauro'],
    ['registro' => 344, 'titulo' => 'Sertão', 'status' => 'libre'],
];

echo $acervo[1]['titulo'], "\n";
echo count($acervo), "\n";

$acervo[] = [
    'registro' => 501,
    'titulo' => 'Iracema',
    'status' => 'disponible',
];

echo count($acervo), "\n";
```

```text
Vidas
3
4
```

El `[1]` es el segundo porque la numeración empieza en cero. Es la única
parte del ejercicio que vale revisar con atención.
:::

:::exercise level=2
Dado el array de abajo, elimina el ejemplar en restauración e imprime el
resultado en JSON. Haz dos versiones: una que produzca un objeto y otra que
produzca una lista. Explica qué cambia para quien lo recibe.

```php
$ejemplares = [
    ['registro' => 812, 'status' => 'disponible'],
    ['registro' => 907, 'status' => 'restauracion'],
    ['registro' => 344, 'status' => 'disponible'],
];
```

:::answer
```php
unset($ejemplares[1]);

echo json_encode($ejemplares), "\n";
echo json_encode(array_values($ejemplares)), "\n";
```

```text
{"0":{"registro":812,"status":"disponible"},
 "2":{"registro":344,"status":"disponible"}}
[{"registro":812,"status":"disponible"},
 {"registro":344,"status":"disponible"}]
```

Para quien lo recibe, la diferencia es total. Un programa que espera una
lista va a recorrer el primer resultado y encontrar cero elementos, porque
un objeto no se recorre por índice. No da error: da una pantalla vacía.

Y fíjate en que los datos son idénticos en los dos casos. Los mismos dos
ejemplares, los mismos campos, los mismos valores. Lo único que cambió fue
la forma — y la forma es la mitad del contrato.
:::

:::exercise level=3
El fragmento de abajo vino del Sistema y decide si debe guardar la
observación de una devolución. Tiene un defecto que solo aparece en un caso
específico. Encuentra el caso, explícalo y corrígelo.

```php
$devolucion = [
    'registro' => 812,
    'observacion' => null,
];

if (isset($devolucion['observacion'])) {
    guardarObservacion($devolucion['observacion']);
}
```

:::answer
El caso específico es la observación que existe y está **deliberadamente**
vacía.

`isset` responde `false` en dos situaciones distintas: que la clave no
exista, y que la clave exista con valor `null`. Aquí existe. Alguien, en
algún lugar, armó ese array con el campo presente — lo que normalmente
significa que el formulario tenía el campo y la persona no lo completó.

Si la regla de negocio es "guarda la observación cuando el campo vino en el
formulario, aunque esté en blanco", `isset` está mal. Si es "guarda solo
cuando haya texto", está bien por casualidad, y va a dejar de estarlo el día
en que alguien cambie el valor por defecto de `null` a `''`.

La corrección es elegir la pregunta y escribirla:

```php
if (array_key_exists('observacion', $devolucion)) {
    guardarObservacion($devolucion['observacion']);
}
```

si la regla es sobre que el campo haya venido, o

```php
if (($devolucion['observacion'] ?? '') !== '') {
    guardarObservacion($devolucion['observacion']);
}
```

si la regla es sobre que haya texto. El `??` cubre el caso de que la clave
ni siquiera exista, y la comparación con `''` hace legible la intención para
quien revise.

Lo que no se puede hacer es dejar `isset` y cruzar los dedos para que las
dos reglas nunca diverjan. Divergen — así aparecieron cuatro lectores de más
en el informe de Vera en el capítulo @cap:variaveis-e-tipos, por el mismo
motivo, con otro nombre.
:::
