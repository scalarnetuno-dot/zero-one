---
source_hash: 25834ca1a1ed
title: "Variables y tipos"
number: 4
slug: variaveis-e-tipos
part: p1
kicker: "Treinta y un pendientes en pantalla, veintisiete en el papel. Los cuatro de más debían exactamente cero reales."
goal: >-
  Guardar valores en los cinco tipos del día a día, inspeccionarlos con
  `var_dump`, elegir entre comillas simples y dobles, y distinguir la
  ausencia del vacío y del cero.
---

:::story Veintisiete
Vera imprimió el informe de pendientes y lo revisó a mano, con una regla,
como hace desde 1995.

El informe decía treinta y uno. La regla decía veintisiete.

— Aquí sobran cuatro.

— Quizás usted se saltó una línea — arriesgó Tainá.

Vera volvió a revisar, con la regla, sin ningún apuro, mientras Tainá
miraba. Veintisiete.

Le llevó una hora a Tainá encontrar lo que los cuatro nombres extra tenían
en común: todos habían devuelto **a tiempo**. Su multa se había calculado,
registrado y guardado con el valor R$ 0,00.

El Sistema preguntaba así si la multa ya se había procesado:

```php
if (!$multa) {
    $pendiente = true;
}
```

Y cero, en PHP, es falso.

— La cuenta está bien — dijo Dedé, cuando lo vio. — El que no sabe la
diferencia entre "no debe nada" y "nadie lo calculó" es el informe.

Vera lo anotó en su cuaderno. Después lo tachó y lo volvió a escribir, con
otra letra, más grande:

> *"el sistema tiene que saber la diferencia entre cero y nada"*

— ¿Eso vale para cuántos sistemas? — preguntó Tainá.

— Para todos los que usé.
:::

Este capítulo trata de guardar valores y saber qué se guardó. La historia
de arriba es sobre la segunda parte, que es la que suele faltar.

## `$` delante de todo

En PHP, toda variable empieza con `$`, y ninguna necesita declararse antes
de recibir un valor:

```php title="primeras.php" numbered
<?php

$titulo = "O Cortiço";
$ejemplares = 3;

echo $titulo, "\n";
echo $ejemplares, "\n";
```

```text
O Cortiço
3
```

No existe una línea que diga "voy a crear una variable llamada `$titulo` de
tipo texto". La asignación crea la variable y el tipo viene con el valor.

El `$` tiene poca ceremonia y un efecto secundario bueno: `$titulo` es
siempre una variable, en cualquier parte del archivo. No hay ambigüedad
entre nombre de variable, nombre de función y palabra reservada del
lenguaje. A cambio, olvidar el `$` es un error que PHP tarda en notar,
porque `titulo` sin signo es sintaxis válida — es el nombre de una
constante que va a buscar y no va a encontrar.

Sobre los nombres: valen letras, números y guion bajo, y el primer carácter
no puede ser un número. Mayúsculas y minúsculas son distintas — `$titulo` y
`$Titulo` son dos variables. La convención en PHP moderno es
`$nombreCompuesto`, en *camelCase*, aunque mucho código antiguo usa
`$nombre_compuesto`.

## Los cinco tipos del día a día

```php title="tipos.php" numbered
<?php

$titulo = "O Cortiço";
$ejemplares = 3;
$peso_kg = 0.42;
$disponible = true;
$devuelto_en = null;

var_dump($titulo);
var_dump($ejemplares);
var_dump($peso_kg);
var_dump($disponible);
var_dump($devuelto_en);
```

```text
string(10) "O Cortiço"
int(3)
float(0.42)
bool(true)
NULL
```

Cinco valores, cinco tipos. `var_dump` imprime el tipo y el valor, y por
eso es la herramienta más usada para depurar PHP: con `echo`, los cinco
saldrían como `O Cortiço`, `3`, `0.42`, `1` y nada.

| Tipo | Qué guarda | En el acervo |
|---|---|---|
| `string` | texto | título, autor, ISBN, nombre del lector |
| `int` | número entero | número de registro, días de atraso, cantidad |
| `float` | número con decimales | peso, porcentaje, promedio |
| `bool` | `true` o `false` | si el ejemplar está disponible |
| `null` | la ausencia de valor | fecha de devolución de quien no devolvió |

Tabla: `true`, `false` y `null` se pueden escribir en mayúsculas, pero la
convención es en minúsculas.

Fíjate en el `string(10)` de la salida, para una palabra de nueve letras. El
número entre paréntesis no es la cantidad de letras: es la cantidad de
**bytes**, y la `ç` ocupa dos. Es consecuencia de cómo se almacena el
texto, y por ahora basta con saber que el número existe y que no siempre
coincide con lo que cuentas a ojo.

Hay otros dos tipos importantes — `array` y `object` —, que guardan varias
cosas a la vez en lugar de una sola. Entran cuando haya varias cosas que
guardar.

:::key
Siempre que no estés seguro de lo que hay dentro de una variable, la
respuesta cuesta una línea: `var_dump($x);`. Es más rápido que razonar, más
confiable que recordar, y la única forma de distinguir el número `3` del
texto `"3"` — que se parecen en pantalla y se comportan de formas distintas.
:::

## Las comillas simples y dobles guardan cosas distintas

Las dos crean texto, y dejan de ser equivalentes en cuanto pones una
variable adentro:

```php title="comillas.php" numbered
<?php

$titulo = "O Cortiço";

echo "Tenemos: $titulo\n";
echo 'Tenemos: $titulo\n';
```

```text
Tenemos: O Cortiço
Tenemos: $titulo\n
```

La primera línea usa **comillas dobles**. Dentro de ellas, PHP busca
nombres de variables y cambia cada uno por su valor. Eso se llama
**interpolación**. La barra invertida también se interpreta: `\n` se volvió
un salto de línea de verdad.

La segunda línea usa **comillas simples**. Dentro de ellas, casi nada se
interpreta: `$titulo` salió como siete caracteres literales, y `\n` salió
como dos. Por eso la salida quedó toda en una sola línea.

Cuando el nombre de la variable queda pegado a otra letra, PHP no puede
adivinar dónde termina:

```php title="llaves.php" numbered
<?php

$tipo = "ejemplar";

echo "Tres {$tipo}es\n";
```

```text
Tres ejemplares
```

Sin las llaves, PHP buscaría una variable llamada `$tipoes`, no la
encontraría y avisaría. Con `{}`, el límite queda explícito. Usar llaves
siempre que haya interpolación te ahorra esa decisión.

:::key
Regla práctica: **comillas simples cuando el texto es literal, comillas
dobles cuando hay una variable adentro.** No es una cuestión de rendimiento
— la diferencia es imperceptible. Es una cuestión de expresar la intención:
las comillas simples avisan a quien lee que ahí no hay nada que sustituir.
:::

## `null` no es vacío, y vacío no es cero

```php title="tres_afirmaciones.php" numbered
<?php

$devuelto_en = null;    // todavía no devolvió
$observacion = "";      // devolvió, y no había nada que observar
$multa = 0;             // devolvió, y no debe nada
```

Tres valores, tres afirmaciones completamente distintas sobre el mundo. Y,
para un `if` simple, los tres se comportan igual: ninguno entra.

```php title="el_defecto.php" numbered
<?php

$multa = 0;

if ($multa) {
    echo "tiene multa\n";
} else {
    echo "no tiene multa\n";
}
```

```text
no tiene multa
```

El `if` no recibió `true` ni `false`: recibió el número cero. Cuando eso
pasa, PHP convierte el valor a verdadero o falso antes de decidir — y cero
es falso.

Es exactamente el defecto del informe de Vera, escrito al revés. El Sistema
preguntaba `if (!$multa)`, que es "si la multa es falsa", creyendo que
preguntaba "si la multa no existe".

Hay tres herramientas para hacer la pregunta correcta, y no son
intercambiables:

```php title="tres_preguntas.php" numbered
<?php

$multa = 0;

var_dump(isset($multa));    // ¿la variable existe y no es null?
var_dump(empty($multa));    // ¿el valor es uno de los "falsos"?
var_dump(is_null($multa));  // ¿el valor es exactamente null?
```

```text
bool(true)
bool(true)
bool(false)
```

Léelo despacio, porque las tres respuestas son distintas para el mismo
valor.

`isset` respondió `true`: la variable existe y no es nula. `empty` respondió
`true`: cero es un valor falso. `is_null` respondió `false`: cero no es
nulo, cero es cero.

Si cambias el valor por `null`, las tres respuestas se invierten:

```text
bool(false)   isset  — no existe, o existe y es null
bool(true)    empty  — null es falso
bool(true)    is_null
```

:::key
`isset()` pregunta "¿existe y no es nulo?". `empty()` pregunta "¿es un valor
falso?". Y **ninguna de las dos** pregunta "¿tiene contenido?".

Cuando lo que necesitas es distinguir ausencia de cero — que es el caso de
la multa de Vera —, la pregunta es `=== null`, y ninguna otra sirve.
:::

La corrección del informe son dos preguntas separadas, cada una diciendo lo
que quiere saber:

```php title="explicito.php" numbered
<?php

$multa = 0;

if ($multa === null) {
    echo "nadie la calculo todavia\n";
}

if ($multa === 0) {
    echo "calculada, y no debe nada\n";
}
```

```text
calculada, y no debe nada
```

Los tres signos de igual comparan valor **y** tipo, sin convertir nada. Dos
signos harían otra cosa, y esa diferencia da para una historia lo bastante
buena como para ocupar el próximo capítulo entero.

:::practice
Ejecuta el `tres_preguntas.php` de arriba cambiando el valor de `$multa`
por: `null`, `0`, `""`, `"0"`, `false` y `"a"`. Anota las tres respuestas de
cada uno.

Seis líneas de notas que responden, de una vez, unas quince dudas que van a
aparecer en las próximas semanas — y son más rápidas de consultar que la
documentación.
:::

## Valores que no pueden cambiar

```php title="constantes.php" numbered
<?php

const DIAS_DE_PRESTAMO = 14;
const LIMITE_POR_LECTOR = 3;

echo "Plazo: ", DIAS_DE_PRESTAMO, " días\n";
```

```text
Plazo: 14 días
```

Una **constante** es un valor con nombre que no se puede reasignar. Fíjate
en dos diferencias: no lleva `$` delante, y el nombre va en mayúsculas con
guion bajo — convención universal en PHP, no obligación del lenguaje.

Intentar cambiar una da error:

```text
PHP Fatal error: Cannot redefine constant DIAS_DE_PRESTAMO
```

Existe también `define('DIAS_DE_PRESTAMO', 14)`, que hace casi lo mismo. La
diferencia práctica: `const` se resuelve cuando se lee el archivo y solo
acepta un valor fijo; `define()` se ejecuta durante la ejecución y acepta un
nombre o un valor calculado en el momento. Usa `const` por defecto.

El valor de cambiar `14` por `DIAS_DE_PRESTAMO` no es evitar tipear. Es que
el número pasa a existir **en un solo lugar**. Cuando Vera decida cambiar
el plazo a veintiún días durante las vacaciones escolares, el cambio es una
línea — y no vas a pasar la tarde buscando todos los `14` del sistema,
descubriendo que algunos eran días de préstamo y otros eran la cantidad de
estantes.

:::note En tu carrera
Cuando alguien del negocio dice que el número del sistema está mal, la
probabilidad de que tenga razón es alta — y la probabilidad de que el
sistema esté técnicamente funcionando también. Las dos cosas a la vez.

Vera no sabe programar y encontró un defecto que pasó quince años en
producción, porque tenía dos cosas que ningún test automatizado tiene: el
número correcto, contado a mano, y la terquedad de revisarlo.

El reflejo correcto al recibir ese tipo de reporte no es explicar por qué
el sistema está bien. Es pedir **los dos números y la lista**. La diferencia
entre 31 y 27 es una abstracción; los cuatro nombres extra son un camino
directo a la línea de código.
:::

:::summary
- Toda variable empieza con `$` y no necesita declararse: la asignación crea
	la variable y define el tipo.
- Los cinco tipos del día a día son `string`, `int`, `float`, `bool` y
	`null`.
- `var_dump` muestra tipo y valor; `echo` muestra solo el valor.
- Las comillas dobles interpolan variables e interpretan `\n`; las simples
	no.
- `null` es ausencia, `""` es vacío, `0` es cero — tres afirmaciones
	distintas que un `if` simple trata como una sola.
- `isset` pregunta "¿existe?", `empty` pregunta "¿es falso?"; para
	distinguir ausencia de cero, usa `=== null`.
- `const` le da nombre a un valor fijo y lo pone en un solo lugar.
:::

:::checkpoint
Declaras variables de los cinco tipos, descubres el tipo de cualquiera con
`var_dump`, eliges las comillas según la intención y explicas en una frase
la diferencia entre `null`, `""` y `0`.
:::

:::exercise level=1
Crea variables para describir un ejemplar — número de registro, título, si
está disponible, y la fecha de devolución — e imprime el tipo de cada una.

:::answer
```php
<?php

$registro = 2117;
$titulo = "O Cortiço";
$disponible = false;
$devuelto_en = null;

var_dump($registro, $titulo, $disponible, $devuelto_en);
```

```text
int(2117)
string(10) "O Cortiço"
bool(false)
NULL
```

`var_dump` acepta varios valores a la vez, separados por comas.

Y fíjate en la elección de `$devuelto_en`: `null` es una afirmación — el
préstamo está abierto. Si fuera `""`, estaría diciendo "devolvió en fecha
desconocida", que es otra cosa, y casi siempre un error de importación de
datos antiguos.
:::

:::exercise level=2
Sin ejecutarlo, escribe lo que imprime cada línea. Después ejecútalo y
compruébalo.

```php
<?php

$n = 5;
$texto = "libros";

echo "Tenemos $n $texto\n";
echo 'Tenemos $n $texto\n';
echo "Tenemos {$n}00 $texto\n";
```

:::answer
```text
Tenemos 5 libros
Tenemos $n $texto\nTenemos 500 libros
```

La segunda línea es la que atrapa a casi todos, y por dos motivos a la vez:
las variables salieron literales **y** el `\n` también, así que la tercera
línea empezó pegada a la segunda.

La tercera muestra por qué existen las llaves. Sin ellas, `"$n00"` haría
que PHP buscara una variable llamada `$n00`.
:::

:::exercise level=3
El fragmento de abajo vino del Sistema. Decide si un préstamo entra en la
lista de pendientes. Señala el defecto y escribe la versión correcta.

```php
$multa = calcularMulta($prestamo);

if (!$multa) {
    $pendiente = true;
} else {
    $pendiente = false;
}
```

:::answer
El defecto es el `!$multa`, que pregunta "¿la multa es un valor falso?"
cuando la intención era preguntar "¿la multa todavía no se calculó?".

Cuatro valores distintos pasan por ese `if` como si fueran el mismo: `null`
(no se calculó), `0` (se calculó y no debe nada), `""` (vino texto vacío de
algún lado) y `false` (la función falló). Solo el primero debería marcar
pendiente.

```php
$multa = calcularMulta($prestamo);

$pendiente = ($multa === null);
```

Dos observaciones sobre la versión corregida.

La primera: el `if/else` desapareció. Cuando las dos ramas solo asignan
`true` y `false` a la misma variable, la comparación ya es la respuesta — y
una comparación leída en voz alta suena como la regla de negocio: *está
pendiente cuando la multa es nula*.

La segunda, y es la más importante: si `calcularMulta` puede devolver
`false` en caso de fallo, la versión corregida marca ese préstamo como **no
pendiente**, y el problema se vuelve invisible. Una función que devuelve a
veces un número, a veces `null` y a veces `false` obliga a quien la llama a
adivinar cuál de los tres pasó. El arreglo de verdad es que la función
devuelva una sola cosa — y por eso va a volver a este libro.
:::

:::story ¿Por qué un contrato tendría valor cero?
En Vertexo, esa misma semana, Cléber pidió un indicador nuevo en el panel de
la dirección: "total de contratos pendientes".

Dedé preguntó qué contaba como pendiente.

— Los que están pendientes.

— ¿Un contrato con valor cero cuenta?

Cléber lo miró con la expresión de quien acaba de oír si el agua moja.

— ¿Por qué un contrato tendría valor cero?

Tres semanas después, el área comercial empezó a registrar contratos de
cortesía, con valor cero, para clientes en período de prueba.

El panel de la dirección pasó a mostrar diecisiete contratos pendientes.
Existían treinta y cuatro.

Dedé ya había escrito `=== null`.
:::
