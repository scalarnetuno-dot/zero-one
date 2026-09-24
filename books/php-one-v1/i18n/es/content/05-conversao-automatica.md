---
source_hash: b4e41d704334
title: "Cuando PHP convierte solo"
number: 5
slug: conversao-automatica
part: p1
kicker: "Seu Juvenal escribió mal la contraseña y entró como bibliotecaria jefa. El culpable tiene dos caracteres."
goal: >-
  Prever la conversión automática de tipos en lugar de que te sorprenda,
  elegir entre `==` y `===` con criterio, y saber por qué el dinero no se
  guarda en `float`.
---

:::story Entré sin querer
Viernes, 10:20. Seu Juvenal llamó con el tono de quien descubrió algo bueno.

— ¡Oye, logré entrar al sistema!

— Genial. ¿Funcionó la contraseña nueva?

— No, me equivoqué de contraseña. Pero entré igual. Y entré como Vera.

Dedé le pidió que lo repitiera despacio.

Seu Juvenal había probado el usuario de Vera con una contraseña cualquiera —
según él, "algo con 240". El Sistema la aceptó y abrió el panel de la
bibliotecaria jefa, con permiso para borrar el acervo.

— ¿Eso es normal?

— No.

— Porque si lo es, es bien práctico.
:::

El Sistema no había sido invadido. Estaba haciendo exactamente lo que el
código le mandaba, y el código se lo mandaba con dos caracteres menos de los
que debía.

Para llegar ahí, primero hay que entender qué hace PHP cuando recibe dos
tipos distintos en la misma operación.

## `"10" + 5` da quince

```text
$ php -r 'var_dump("10" + 5);'
int(15)
$ php -r 'var_dump("10" . 5);'
string(3) "105"
$ php -r 'var_dump(true + true);'
int(2)
```

PHP convierte automáticamente cuando la operación exige un tipo distinto del
que recibió. Eso tiene nombre: **coerción de tipos**, o, en la jerga de la
comunidad, *type juggling*.

Fíjate en que la decisión no es del valor, es del **operador**. El `+` es
aritmético, así que exige números y el string `"10"` se vuelve el número
`10`. El `.` es concatenación, así que exige texto y el número `5` se vuelve
`"5"`. El mismo par de valores, dos resultados distintos, porque la pregunta
fue otra.

El `true + true` parece un chiste y no lo es: `true` convertido a número es
`1`, y `false` es `0`. Ese comportamiento se usa a propósito para contar
cuántas condiciones de una lista se cumplieron.

Cuando la conversión no tiene ningún sentido, PHP 8 la rechaza:

```text
$ php -r 'var_dump("abc" + 5);'
PHP Fatal error: Uncaught TypeError: Unsupported operand
types: string + int
```

En PHP 7 eso devolvía `5` con un aviso que nadie leía. El lenguaje pasó a
rechazar lo absurdo en vez de improvisar, y esa es la diferencia más
importante entre el PHP que tiene mala fama y el PHP que estás aprendiendo.

:::pitfall
Un resto sobrevivió, y conviene no usarlo nunca:

```text
$ php -r 'var_dump("10 libros" + 5);'
PHP Warning: A non-numeric value encountered
int(15)
```

El string **empieza** con un número, así que PHP aprovecha el principio y
descarta el resto, con un aviso que suele estar desactivado en producción.

Esto importa porque todo lo que llega de un formulario llega como texto. El
campo "cantidad" completado con `3 cajas` no va a dar error: se va a volver
`3`, en silencio, y la diferencia va a aparecer en el inventario dos semanas
después.
:::

## La lista cerrada de lo que es falso

Cuando un valor cualquiera se usa donde el lenguaje espera verdadero o falso
— dentro de un `if`, por ejemplo —, se convierte. La lista de lo que se
vuelve `false` es corta y cerrada:

| Valor | ¿Se vuelve `false`? |
|---|---|
| `false` | sí |
| `0` y `0.0` | sí |
| `""` (texto vacío) | sí |
| `"0"` (el texto con un cero) | **sí** |
| `[]` (lista vacía) | sí |
| `null` | sí |
| cualquier otra cosa | no |

Tabla: Siete líneas. Todo lo que no está aquí es verdadero, incluidos `-1`,
`"false"` y `"0.0"`.

La línea que sorprende a casi todos es la cuarta. **El string `"0"` es falso
en PHP** — y es el único string no vacío que lo es.

```text
$ php -r 'var_dump((bool) "0", (bool) "0.0", (bool) "false");'
bool(false)
bool(true)
bool(true)
```

El texto `"0"` es falso; el texto `"0.0"` es verdadero; el texto `"false"`
es verdadero. No hay lógica que deducir aquí, solo una regla que conocer:
existe porque, en una época en que todo lo que venía de un formulario era
texto, `"0"` tenía que significar cero.

Es una trampa real. Un campo de formulario completado con `0` llega como
`"0"`, e `if ($cantidad)` decide que no se completó.

## `==` convierte, `===` no

```text
$ php -r 'var_dump(1 == "1");'
bool(true)
$ php -r 'var_dump(1 === "1");'
bool(false)
```

Son dos operadores distintos, no dos formas de escribir lo mismo.

**`==` compara después de convertir.** Toma los dos lados, encuentra un tipo
común y compara los resultados. Por eso el número `1` y el texto `"1"` son
iguales para él.

**`===` compara valor y tipo, sin convertir nada.** Tipos distintos ya
responden `false`, sin siquiera mirar el valor.

| Comparación | `==` | `===` |
|---|---|---|
| `1` y `"1"` | `true` | `false` |
| `0` y `""` | `false` (desde PHP 8) | `false` |
| `"abc"` y `0` | `false` (desde PHP 8) | `false` |
| `null` y `false` | `true` | `false` |
| `"1e3"` y `"1000"` | `true` | `false` |

Tabla: La cuarta línea produce defectos silenciosos — `null == false` hace
que "no informado" pase por "denegado". La quinta es la que abrió la puerta
de la Casa Amarela.

:::trivia
En PHP 7, `0 == "abc"` era **verdadero**: el string no numérico se volvía
`0`. Cualquier comparación laxa entre cero y texto pasaba.

PHP 8 invirtió la regla — ahora es el número el que se vuelve texto cuando
el texto no es numérico — y `0 == "abc"` pasó a ser `false`. Fue una de las
pocas rupturas de compatibilidad de la historia de PHP de la que
prácticamente nadie se quejó. La propuesta se llamaba *Saner string to
number comparisons*, y el nombre ya decía lo que la comunidad pensaba del
comportamiento anterior.
:::

La recomendación cabe en una línea: **usa `===` por defecto**. Escribe `==`
solo cuando la conversión sea exactamente lo que quieres, y deja un
comentario que diga por qué.

## Dos caracteres en la puerta

Con esto en la cabeza, ya se puede leer el `login.php` del Sistema.

```php title="login.php (el Sistema, 2009)" numbered
<?php

$contrasena_enviada = md5($_POST['contrasena']);

if ($contrasena_enviada == $contrasena_guardada) {
    entrar();
}
```

`md5()` revuelve un texto en un código de 32 caracteres, siempre de la misma
manera: la misma contraseña genera siempre el mismo código. Así se guardaban
las contraseñas en 2009 — no se guardaba la contraseña, se guardaba el
revuelto.

Ahora mira lo que pasa con dos contraseñas específicas:

```text
$ php -r 'echo md5("240610708"), "\n";'
0e462097431906509019562988736854
$ php -r 'echo md5("QNKCDZO"), "\n";'
0e830400451993494058024219903391
```

Son dos códigos distintos. Y aun así:

```text
$ php -r 'var_dump(md5("240610708") == md5("QNKCDZO"));'
bool(true)
```

Los dos empiezan con `0e` y solo tienen dígitos después. Esa es la forma de
escribir la notación científica: `0e462...` es **cero por diez elevado a
462...**, que es cero. El `==` vio dos strings numéricos, convirtió los dos
al número `0.0` y comparó los números.

El código de la contraseña de Vera, guardado en 2009, tenía ese formato.
Cualquier contraseña cuyo `md5` también lo tuviera entraba en su cuenta — y
existen miles de textos así, catalogados en listas públicas desde hace más
de una década.

Seu Juvenal acertó uno por casualidad.

:::story Cuatro minutos
Dedé escribió un programa de veinte líneas que probaba una lista pública de
textos con código en formato `0e`.

En cuatro minutos, había encontrado dos cuentas de encargados de mostrador
vulnerables.

La de Vera era una de ellas.

— ¿Desde cuándo? — preguntó ella.

— Desde 2009.

Vera se quedó callada un rato, alisando la etiqueta de un libro que ya
estaba pegada.

— ¿Y cuántas personas lo sabían?

— Nadie. Fue Seu Juvenal, equivocándose de contraseña.

— Entonces tuvimos suerte.

— Tuvimos a Seu Juvenal.
:::

El defecto tenía tres capas, y vale separarlas porque el arreglo de cada una
es distinto.

**Primera: `==` entre secretos.** La comparación laxa convirtió dos valores
distintos en iguales. Un `===` habría evitado este incidente específico.

**Segunda: MD5 para contraseñas.** Aun con `===`, MD5 es demasiado rápido —
una placa de video común calcula miles de millones por segundo, lo que hace
viable probar contraseñas en masa hasta acertar. Una contraseña pide un
algoritmo deliberadamente lento, que es lo que usa `password_hash()`.

**Tercera: comparación en tiempo variable.** Aun con `===`, la comparación
de texto de PHP se detiene en el primer carácter distinto. Un intento que
acierta los cinco primeros caracteres tarda mediblemente más que uno que
falla el primero — y, con suficientes peticiones, se puede descubrir un
secreto carácter por carácter sin acertarlo nunca entero.

:::key
Un secreto — contraseña, token, firma — no se compara con `==` ni con `===`.
Se usa `hash_equals()`, que recorre siempre la longitud entera, sin importar
dónde esté la diferencia:

```php
if (hash_equals($esperado, $enviado)) {
```

El orden importa: el valor **conocido** va primero.

Y, para contraseñas en concreto, ni siquiera eso: el par `password_hash()` y
`password_verify()` ya resuelve algoritmo, sal y tiempo constante de una
vez. Guardar contraseñas de cualquier otra forma, en 2026, es una decisión
que hay que defender por escrito.
:::

## Convertir a propósito

Cuando **quieres** la conversión, pídela. Un **cast** es un tipo entre
paréntesis delante del valor:

```php title="casts.php" numbered
<?php

$texto = "42.7";

var_dump((int) $texto);
var_dump((float) $texto);
var_dump((string) 42);
var_dump((bool) $texto);
```

```text
int(42)
float(42.7)
string(2) "42"
bool(true)
```

Fíjate en el primero: `(int) "42.7"` devolvió `42`, no `43`. El cast a
entero **descarta** la parte decimal, no redondea. Para redondear existe
`round()`, y la diferencia de un centavo entre las dos opciones es el origen
de una cantidad desproporcionada de reclamos de clientes.

La ventaja del cast sobre la conversión automática no es técnica, es de
lectura: quien revisa el código ve que la conversión fue una decisión, y no
un accidente.

## El centavo que desaparece

Falta el último lugar en que PHP responde con precisión a una pregunta
imprecisa.

```text
$ php -r 'var_dump(0.1 + 0.2);'
float(0.30000000000000004)
$ php -r 'var_dump(0.1 + 0.2 == 0.3);'
bool(false)
```

Esto no es un bug de PHP, ni es exclusivo de él: es como toda computadora
representa los números con decimales, en base 2. El valor `0.1` en base 2
es periódico infinito, igual que `1/3` es infinito en base 10. En algún
punto la computadora corta, y lo que queda es una aproximación muy buena y
no exacta.

En el decimoséptimo decimal a nadie le importa. El problema es que el error
se acumula:

```php title="por_que_no_float.php" numbered
<?php

$total = 0.0;
$i = 0;

while ($i < 1000) {
    $total = $total + 0.50;
    $i = $i + 1;
}

var_dump($total);
var_dump($total === 500.0);
```

```text
float(500.0000000000171)
bool(false)
```

Mil multas de cincuenta centavos deberían dar quinientos reales. Dieron
quinientos reales y un error invisible — que solo aparece en la comparación,
o en el cierre del mes, cuando el total del sistema y el total de la caja
difieren en centavos y nadie sabe cuál de los dos está bien.

:::history
El estándar que rige el `float` — el IEEE 754, de 1985 — fue obra de un
comité liderado por William Kahan, que ganó el premio Turing por ello. Antes
de él, cada fabricante de procesadores redondeaba a su manera, y el mismo
cálculo daba resultados distintos en máquinas distintas.

El `0.30000000000000004` no es un defecto del estándar: es el estándar
funcionando, y funcionando igual en todas partes. El defecto es usar un tipo
pensado para medidas físicas en un valor que tiene que ser exacto.
:::

La salida es no guardar reales. Guardar **centavos**, como entero:

```php title="dinero.php" numbered
<?php

const MULTA_POR_DIA_EN_CENTAVOS = 80;
const TOPE_DE_MULTA_EN_CENTAVOS = 2000;

$dias = 12;
$total_en_centavos = $dias * MULTA_POR_DIA_EN_CENTAVOS;

if ($total_en_centavos > TOPE_DE_MULTA_EN_CENTAVOS) {
    $total_en_centavos = TOPE_DE_MULTA_EN_CENTAVOS;
}

$reales = number_format($total_en_centavos / 100, 2, ',', '.');
echo 'R$ ', $reales, "\n";
```

```text
R$ 9,60
```

`number_format` arma el texto para mostrar: recibe el valor, la cantidad de
decimales, el separador decimal y el separador de miles. Con `','` y `'.'`
en esas posiciones, sale en el formato brasileño.

:::key
Un entero en centavos es exacto, suma sin error, se compara con `===` y
cabe en un `int` hasta noventa mil billones — margen suficiente para una
biblioteca de barrio. La división por 100 ocurre **solo al mostrar**, nunca
en medio de un cálculo.

Y la convención que sostiene la regla es el nombre: **toda variable de
dinero termina en `_en_centavos`.** El nombre lleva la unidad, y desaparece
una categoría entera de errores — incluida la de que alguien sume un valor
en reales con uno en centavos seis meses después.
:::

Usa `float` para peso, temperatura, porcentaje y promedio. Para dinero,
nunca.

:::note En tu carrera
Encontrar una falla de seguridad en un sistema que no es tuyo es una
situación socialmente incómoda, y la forma de comunicarla cambia el
resultado.

Lo que funciona: escribirle a la persona responsable, con **el impacto en
lenguaje de negocio primero** y el detalle técnico después. "Es posible
entrar en la cuenta de la bibliotecaria jefa sin saber la contraseña, y
borrar el acervo" comunica mejor que "hay una comparación laxa de hash MD5".

Lo que no funciona: demostrarlo públicamente. Entrar en la cuenta de alguien
para probar el punto, aun con la mejor de las intenciones, te traslada el
problema a ti — y la conversación deja de ser sobre la falla y pasa a ser
sobre tu acceso.

Y hay una regla práctica que vale para toda la carrera: **registra la
fecha**. Si el arreglo tarda seis meses y algo pasa, la distancia entre "yo
avisé" y "yo avisé el 14 de marzo, en este correo" es enorme.
:::

:::summary
- PHP convierte tipos cuando el operador lo exige: `+` tira hacia número,
	`.` tira hacia texto.
- Un texto que empieza con un número se aprovecha a medias, con aviso.
- La lista de valores falsos es cerrada y tiene siete líneas — `"0"` está
	en ella.
- `==` compara después de convertir; `===` compara valor y tipo. Usa `===`.
- Un secreto no se compara con `===`, sino con `hash_equals`; una
	contraseña usa `password_verify`.
- Un cast es una conversión pedida por escrito, y `(int)` descarta la parte
	decimal en lugar de redondear.
- El dinero es `int` en centavos, dividido por 100 solo al mostrarlo, con la
	unidad en el nombre de la variable.
:::

:::checkpoint
Prevés el resultado de una operación entre tipos distintos, eliges entre
`==` y `===` justificando la elección, y sabes explicar en una revisión por
qué la multa es un entero.
:::

:::exercise level=1
Sin ejecutarlo, di el resultado y el tipo de cada expresión. Después
compruébalo con `var_dump`.

```php
"7" + 3
"7" . 3
"7" == 7
"7" === 7
(int) "9 libros"
(bool) "0"
```

:::answer
```text
int(10)
string(2) "73"
bool(true)
bool(false)
int(9)
bool(false)
```

La quinta es la más peligrosa de las seis: `(int) "9 libros"` devuelve `9`
sin quejarse de nada, porque un cast explícito no emite el aviso que emitiría
la suma. Pediste la conversión; PHP hizo lo mejor que pudo.
:::

:::exercise level=2
El fragmento de abajo verifica un cupón de descuento enviado en un
formulario. Tiene dos defectos. Encuentra los dos y escribe la versión
correcta.

```php
$cupon = $_POST['cupon'];

if ($cupon == 0) {
    echo "sin cupon";
}
```

:::answer
**Defecto 1: `==` con un número del lado derecho.** Antes de PHP 8,
cualquier texto no numérico se volvería `0` y entraría en el `if`. En PHP 8
eso se corrigió, pero el código sigue diciendo una cosa y queriendo decir
otra.

**Defecto 2: la pregunta está mal.** "Sin cupón" es la ausencia del campo, y
no el valor cero. El campo puede ni siquiera haberse enviado, y entonces
`$_POST['cupon']` produce un aviso de índice indefinido antes de cualquier
comparación.

```php
$cupon = $_POST['cupon'] ?? '';

if ($cupon === '') {
    echo "sin cupon";
}
```

El `?? ''` devuelve el lado izquierdo si existe y no es nulo; si no,
devuelve el derecho. Resuelve el aviso y garantiza que la comparación
siguiente compare texto con texto.

Vale notar lo que la versión corregida dejó de aceptar: el cupón `"0"`. Si
existiera un cupón con ese código, la versión original lo rechazaría en
silencio — y esa es precisamente la categoría de defecto que solo aparece
cuando el equipo comercial registra uno.
:::

:::exercise level=3
La Casa Amarela cobra 80 centavos por día de atraso, con un tope de
R$ 20,00. Escribe el cálculo para 0, 1, 25 y 100 días, guardando todo en
centavos, y explica por qué el caso de 25 días es el más importante de
probar.

:::answer
```php
<?php

const MULTA_POR_DIA_EN_CENTAVOS = 80;
const TOPE_DE_MULTA_EN_CENTAVOS = 2000;

$casos = [0, 1, 25, 100];

foreach ($casos as $dias) {
    $total = $dias * MULTA_POR_DIA_EN_CENTAVOS;

    if ($total > TOPE_DE_MULTA_EN_CENTAVOS) {
        $total = TOPE_DE_MULTA_EN_CENTAVOS;
    }

    echo $dias, " dias: ", $total, " centavos\n";
}
```

```text
0 dias: 0 centavos
1 dias: 80 centavos
25 dias: 2000 centavos
100 dias: 2000 centavos
```

El `foreach` recorre una lista de valores, uno por vez — aquí sirve solo
para no repetir el cálculo cuatro veces.

El caso de 25 días es el importante porque 25 × 80 da exactamente 2000, el
valor del tope. Es la **frontera**: el punto en que cambia el
comportamiento. Un error de un carácter en la condición — `>` en lugar de
`>=`, o al revés — no aparece con 1 día ni con 100 días, y aparece con 25.

Probar un valor por debajo, uno por encima y **el valor exacto del borde**
es el hábito que separa a quien prueba de quien solo revisa.

Y vale fijarse en lo que el ejercicio no pidió: en ningún momento apareció
`0.80`. La cuenta entera se hace con números enteros, y la coma solo
entraría al imprimir el comprobante.
:::
