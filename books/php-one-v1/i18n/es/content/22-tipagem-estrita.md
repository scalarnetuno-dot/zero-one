---
source_hash: 789d6ce6d398
title: "Tipado estricto"
number: 22
slug: tipagem-estrita
part: p4
kicker: "La herramienta corrió dieciocho segundos y devolvió cuarenta y una sumas de fecha con texto. Ninguna había dado error en quince años."
goal: >-
  Activar el modo estricto en el lugar correcto, declarar tipos que digan
  algo, saber qué no revisa PHP en ejecución y correr análisis estático en
  un proyecto legado sin detener la empresa.
---

:::story Dieciocho segundos
Dedé instaló PHPStan un jueves por la tarde, lo apuntó a la carpeta del
Sistema y fue por un café.

Cuando volvió, la salida había dejado de desplazarse.

```text
 [ERROR] Found 1.247 errors
```

—Mil doscientos cuarenta y siete —leyó Tainá.

—En catorce mil líneas. Podría ser peor.

Filtró por un solo tipo, los que hablaban de sumas. Quedaron cuarenta y
uno.

```text
  213    Binary operation "+" between string and int
         results in an error.
```

—¿Qué hay en la 213?

—`$fecha_devolucion + 14`.

Tainá tardó un segundo.

—¿Eso funciona?

—Eso nunca dio error.

—No es lo que te pregunté.
:::

## La línea que cambia el archivo entero

Desde el capítulo @cap:classes-e-objetos, PHP viene convirtiendo texto en
número en la puerta de las funciones: `'1899'` entra como `int(1899)` y
nadie se queja. Eso se llama **modo coercitivo**, y es el predeterminado.

Una línea lo apaga:

```php title="src/Acervo/Libro.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Acervo;
```

`declare(strict_types=1)` tiene que ser la **primera instrucción** del
archivo, antes incluso del `namespace`. Solo puede haber comentarios antes
de ella.

Con el modo estricto activado, la puerta deja de convertir:

```php
multaEnCentavos('3');
```

```text
Fatal error: Uncaught TypeError: multaEnCentavos():
Argument #1 ($dias) must be of type int, string given
```

Y deja de convertir incluso lo que parece inofensivo:

```php
multaEnCentavos(2.5);
```

```text
Fatal error: Uncaught TypeError: multaEnCentavos():
Argument #1 ($dias) must be of type int, float given
```

En el modo coercitivo, ese `2.5` se volvería `2` en silencio. La multa de
dos días y medio costaría dos días, y la diferencia aparecería en la
rendición de cuentas de marzo, no en la pantalla.

:::key
Hay una excepción, y es a propósito: `int` sigue aceptándose donde se
espera `float`, incluso en modo estricto. Todo entero es un número real
exacto, así que no se pierde nada.

El camino contrario es el que pierde, y es el que el modo estricto rechaza.
:::

## El detalle que casi todos equivocan

La declaración vale para **las llamadas escritas en ese archivo**, no para
la función que declara.

Pruébalo con dos archivos:

```php title="multa.php" numbered
<?php

declare(strict_types=1);

function multaEnCentavos(int $dias): int
{
    return $dias * 80;
}
```

```php title="informe.php" numbered
<?php

require 'multa.php';

var_dump(multaEnCentavos('3'));
```

```text
int(240)
```

Pasó. El `strict_types` de `multa.php` no protegió nada: quien decide es el
archivo donde está escrita la **llamada**, y `informe.php` no declaró nada.

Pon la línea en `informe.php` y el mismo código muere con `TypeError`.

:::pitfall
La consecuencia práctica es que `strict_types` no es una configuración del
proyecto: es una decisión archivo por archivo.

Un proyecto con la línea en el 90 % de los archivos tiene un 10 % de
archivos que llaman a todo de forma laxa, y son justamente los antiguos,
que es donde viven los valores raros. Por eso la regla del equipo suele ser
simple y sin excepciones: **todo archivo nuevo empieza con la línea**.
:::

## Union, nullable y el `mixed` que es una rendición

Un parámetro puede aceptar más de un tipo:

```php
function suma(int|float $a, int|float $b): int|float
{
    return $a + $b;
}
```

Y puede aceptar la ausencia de valor:

```php
function buscarLector(int $id): ?Lector
```

`?Lector` es la abreviatura de `Lector|null`. Las dos formas son lo mismo;
la segunda es la que escribes cuando hay más tipos en la lista.

Existe también `mixed`, que acepta cualquier cosa:

```php
function procesar(mixed $dato): mixed
```

Eso no es un tipo. Es una anotación que dice que nadie decidió, y cuesta
dos veces: PHP no revisa nada, y quien lee la función no se entera de
nada.

:::key
`?Tipo` es honesto cuando el `null` **significa** algo: "no lo encontré",
"todavía no se devolvió". Una fecha de devolución nula es un préstamo
abierto, y eso es información.

`?Tipo` es pereza cuando el `null` es solo una forma de no decidir qué pasa
en el caso malo. El síntoma aparece tres líneas después de cada llamada,
siempre igual: un `if ($x === null)` que nadie sabe qué debería hacer.
:::

## Tipos de retorno

| Escribes | Quiere decir |
|---|---|
| `: void` | no devuelve nada; se permite `return;` solo |
| `: never` | no devuelve **nunca**: siempre lanza o termina |
| `: static` | devuelve un objeto de la misma clase de quien llamó |

Tabla: `void` y `never` no son sinónimos. Una función `void` termina; una
función `never` nunca termina por el camino normal.

```php title="src/Circulacion/Guardia.php" numbered
function rechazar(string $motivo): never
{
    throw new \RuntimeException($motivo);
}
```

`never` es información real para quien lee y para las herramientas: el
código después de la llamada es inalcanzable, y un `if/else` en el que uno
de los lados llama a `rechazar()` no necesita devolver nada en ese lado.

## Lo que PHP no revisa

El modo estricto revisa el tipo del valor. No revisa lo que tiene dentro.

```php
function totalDeMultas(array $multas): int
```

¿`array` de qué? ¿Multas? ¿Enteros? ¿Filas de la base? PHP acepta
cualquier array, incluido uno vacío, uno de strings y uno con tres `null`
dentro. La anotación dio la impresión de rigor y no revisó casi nada.

La salida es anotar el contenido en un comentario que las herramientas
leen:

```php title="src/Prestamos/Caja.php" numbered
/**
 * @param list<Multa> $multas
 */
function totalDeMultas(array $multas): int
{
    $total = 0;

    foreach ($multas as $multa) {
        $total += $multa->centavos();
    }

    return $total;
}
```

`list<Multa>` quiere decir: un array de índices secuenciales en el que
todo valor es una `Multa`. PHP ignora ese comentario. La herramienta de la
sección siguiente, no, y es ella la que pasa a rechazar la llamada con el
array equivocado.

## PHPStan: el error que aparece antes de ejecutar

```text
$ composer require --dev phpstan/phpstan
```

```neon title="phpstan.neon"
parameters:
    level: 5
    paths:
        - src
```

```text
$ vendor/bin/phpstan analyse
```

```text
 ------ -------------------------------------------------------------
  Line   src/Prestamos/Caja.php
 ------ -------------------------------------------------------------
  18     Parameter #1 $multas of function totalDeMultas expects
         list<CasaAmarela\Prestamos\Multa>, list<string> given.
 ------ -------------------------------------------------------------

 [ERROR] Found 1 error
```

El programa no corrió. Nadie abrió la pantalla, nadie creó datos de
prueba, y aun así el error tiene archivo, línea y la diferencia exacta
entre lo que pide la función y lo que entrega la llamada.

:::term Análisis estático
Leer el código sin ejecutarlo, para deducir lo que puede pasar. Es el
mismo trabajo que haces al revisar un *pull request*, con la diferencia de
que la herramienta lee los catorce mil archivos cada vez y no le da sueño.
:::

Los niveles van de 0 a 10, y cada uno activa una familia de revisiones:

| Nivel | Pasa a exigir |
|---|---|
| 0 | clases, funciones y métodos que no existen |
| 3 | tipo de retorno y asignación de propiedades |
| 5 | tipo de los argumentos en las llamadas |
| 6 | anotación de contenido ausente en `array` |
| 8 | llamada de método sobre algo que puede ser `null` |

Tabla: Empieza en 0 en un proyecto existente y sube un nivel a la vez.
Empezar en 9 produce un informe que nadie lee.

## Tipar el legado sin detener la empresa

Los 1.247 errores del Sistema no se van a corregir en este sprint, ni en
el siguiente. Y dejar la herramienta en rojo es lo mismo que no tenerla: en
dos semanas nadie la mira más.

El mecanismo que resuelve esto se llama **baseline**:

```text
$ vendor/bin/phpstan analyse --generate-baseline
```

```neon title="phpstan.neon"
includes:
    - phpstan-baseline.neon

parameters:
    level: 5
    paths:
        - src
```

El archivo generado es una lista de los errores que existen hoy, con el
pedido de ignorarlos. A partir de él, la herramienta vuelve a quedar en
verde y pasa a quejarse **solo de lo nuevo**.

El efecto en la práctica es lo que hace valer la técnica: la deuda deja de
crecer el día que la activas, sin que nadie tenga que aprobar un mes de
refactorización. El código antiguo va saliendo de la lista cuando alguien
lo toca por otro motivo.

:::pitfall
Un baseline sin fecha de vencimiento se vuelve alfombra. El acuerdo que
suele sostenerse es numérico y público: la lista no puede crecer, y cada
corrección real sale de ella para siempre.

Cuando el número no baja durante tres meses seguidos, no está midiendo
deuda técnica: está midiendo prioridad. Y eso también es información útil
para llevar a la reunión del martes.
:::

:::note En tu carrera
El análisis estático cambia lo que puedes prometer. "Esto no se rompe en
ningún otro lugar" es una frase que nadie debería decir sobre un sistema de
catorce mil líneas, a menos que una herramienta haya revisado las catorce
mil.

También es la respuesta más fuerte a la pregunta que vas a oír al proponer
tipos: *"¿y qué ganamos con eso?"*. La respuesta no es "código más bonito".
Es: el error que hoy aparece el martes por la mañana, en la pantalla de
Vera, pasa a aparecer en tu máquina, antes del commit, con la línea exacta.
:::

:::tree title="Dónde estamos ahora"
acervo/
  composer.json      # phpstan en require-dev
  phpstan.neon       # nivel 5, paths: src
  phpstan-baseline.neon
  src/               # todo archivo con declare(strict_types=1)
    Acervo/
    Circulacion/
    Prestamos/
    Lectores/
:::

:::summary
- `declare(strict_types=1)` es la primera instrucción del archivo y apaga
  la conversión automática en las llamadas.
- Vale para las llamadas **escritas en ese archivo**, no para la función
  declarada en él.
- De `int` a `float` sigue pasando; al revés, no.
- `?Tipo` es `Tipo|null`; úsalo cuando el `null` significa algo, no para
  aplazar la decisión.
- `mixed` no es un tipo: es la anotación de quien no decidió.
- `void` termina, `never` no termina por el camino normal.
- `array` no dice nada sobre el contenido; `@param list<Multa>` lo dice, y
  la herramienta lo lee.
- PHPStan encuentra el error antes de ejecutar; empieza en el nivel 0 y
  sube.
- El baseline congela la deuda existente y hace que la herramienta exija
  solo lo nuevo.
:::

:::checkpoint
Activas el modo estricto en el lugar correcto, explicas por qué la
declaración en un archivo no protege las llamadas hechas en otro, eliges
entre `?Tipo` y decidir, anotas el contenido de un `array` y corres
análisis estático con baseline en un proyecto que tiene mil errores.
:::

:::exercise level=1
Di qué hace cada llamada, considerando que el archivo que las escribe
tiene `declare(strict_types=1)` y la función es
`function plazo(int $dias): int`.

1. `plazo(14)`
2. `plazo('14')`
3. `plazo(14.0)`
4. `plazo(true)`
5. `plazo(null)`

Después responde qué cambia en las cinco si se borra la línea del
`strict_types`.

:::answer
Con el modo estricto:

1. pasa.
2. `TypeError`: un string no se vuelve int.
3. `TypeError`: un float no se vuelve int, ni siquiera cuando es redondo.
4. `TypeError`: un booleano no se vuelve int.
5. `TypeError`: el parámetro no es `?int`.

Sin la línea, las cuatro primeras pasan: `'14'` se vuelve `14`, `14.0` se
vuelve `14`, `true` se vuelve `1`. La quinta sigue dando `TypeError`,
porque `null` solo se acepta cuando el tipo dice que lo acepta.

El caso 4 es el que suele asustar más: `plazo(true)` devolviendo un plazo
de un día es el tipo de defecto que nunca aparece en el camino feliz y
aparece el día en que una variable de configuración se vuelve booleana por
error.
:::

:::exercise level=2
Esta función existe en el Sistema y PHPStan se queja de ella en tres
niveles distintos. Típala entera, incluido el contenido de los arrays, y
explica cada decisión.

```php
function atrasados($prestamos, $hoy = null)
{
    $fuera = [];

    foreach ($prestamos as $p) {
        if ($p['devuelto_en'] == null
            && $p['devolver_hasta'] < $hoy) {
            $fuera[] = $p;
        }
    }

    return $fuera;
}
```

:::answer
```php title="src/Prestamos/consultas.php" numbered
<?php

declare(strict_types=1);

/**
 * @param list<Prestamo> $prestamos
 * @return list<Prestamo>
 */
function atrasados(
    array $prestamos,
    \DateTimeImmutable $hoy,
): array
{
    $fuera = [];

    foreach ($prestamos as $prestamo) {
        if ($prestamo->abierto()
            && $prestamo->vencidoAl($hoy)) {
            $fuera[] = $prestamo;
        }
    }

    return $fuera;
}
```

**Los arrays se volvieron objetos.** `$p['devuelto_en']` es una clave que
puede estar mal escrita sin que nadie avise; `$prestamo->abierto()` es un
método que existe o no compila. Es el cambio del capítulo
@cap:classes-e-objetos, ahora exigido por la herramienta.

**El `$hoy` perdió el valor predeterminado `null`.** Un parámetro que
acepta `null` y se compara con `<` esconde el caso en que llega nulo, y la
comparación con `null` es siempre falsa, así que la función devolvería una
lista vacía sin quejarse. Quien llama pasa la fecha; la función no la
inventa.

**Las comparaciones se volvieron métodos.** `== null` quedó como
`abierto()`, y la comparación de fechas quedó como `vencidoAl()`. Además de
decir lo que significan, los dos sacan del camino la comparación laxa y la
comparación de fechas como texto.

**El retorno recibió `list<Prestamo>`.** Sin eso, PHPStan acepta que
alguien pase el resultado a una función que espera otra cosa.
:::

:::exercise level=3
Entras en un proyecto de 40 mil líneas sin ningún tipo, sin pruebas, en
producción, con dos desarrolladores y un *roadmap* lleno.

Escribe el plan de introducción de tipado y análisis estático en cuatro
pasos, cada uno con lo que harías y lo que responderías si la gerencia
preguntara "¿cuánto tiempo le va a quitar esto al plazo?".

:::answer
**Paso 1: instalar y congelar.** PHPStan en `require-dev`, nivel 0,
baseline generado el mismo día. Costo: una tarde. Respuesta a la gerencia:
ningún tiempo del plazo, y a partir de hoy no entra código nuevo con
errores de tipo.

**Paso 2: regla de archivo nuevo.** Todo archivo creado nace con
`declare(strict_types=1)` y con tipos en todo. Costo: cero, porque es como
escribir el archivo de todas formas. Respuesta: esto no es un proyecto, es
una convención, como la indentación.

**Paso 3: subir un nivel por trimestre.** Cada subida genera errores
nuevos; entran en el baseline y salen de ahí a medida que se toca el
código. Costo: una tarde por trimestre para subir y regenerar. Respuesta:
el número de errores congelados es público, y lo vamos a mirar en la
retrospectiva.

**Paso 4: regla de contacto.** El archivo que alguien abra por cualquier
motivo sale del baseline antes de cerrarse. Costo: diluido en trabajo que
ya estaba ocurriendo. Respuesta: no le va a quitar tiempo al plazo; le va
a tomar unos veinte minutos a cada tarea que ya iba a ocurrir.

Lo que **no** entra en el plan, y vale la pena decir por qué: una tarea
llamada "tipar el sistema". Nunca se prioriza, y cuando se aprueba se
vuelve un mes de cambios sin ninguna prueba en un sistema en producción,
que es la forma más cara posible de introducir tipos.
:::
