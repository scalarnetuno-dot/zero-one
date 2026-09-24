---
source_hash: 2e8897e6dffe
title: "Strings"
number: 11
slug: strings
part: p1
kicker: "La mitad de los defectos de un sistema en portugués o en español vive en la distancia entre un carácter y un byte."
goal: >-
  Elegir entre comillas simples y dobles con criterio, manipular texto con
  acentos sin romperlo, formatear valores para lectura humana, y tratar toda
  entrada como texto hasta demostrar lo contrario.
---

:::story Los tres José de Alencar
Vera llamó a Tainá al mostrador con la expresión de quien va a mostrar algo
que ya se cansó de mostrar.

— Busca Alencar ahí.

Tainá lo tecleó. Aparecieron tres autores:

```text
José de Alencar          412 títulos
JosÃ© de Alencar          38 títulos
JOSE DE ALENCAR           11 títulos
```

— Son la misma persona — dijo Vera. — Hace unos seis años.

El primero vino del registro normal. El segundo apareció después de una
migración de base de datos en 2019, cuando alguien exportó en UTF-8 e
importó como si fuera Latin-1. El tercero vino de las cuatro computadoras de
la sala de lectura, que tienen un teclado sin cedilla desde una licitación
de 2021 — los encargados aprendieron a escribir todo en mayúsculas y sin
acento, porque "así siempre lo encuentra".

— ¿Y nadie los unificó?

— Los unificaron una vez. Después volvió.
:::

Los tres José de Alencar son el mismo defecto con tres ropas distintas: un
texto grabado con una codificación y leído con otra, un texto escrito sin
acento, y un texto con un espacio de más. Ninguno de los tres da error. Los
tres parten en pedazos la búsqueda de Vera.

## El nombre que llegó roto

```text
$ php -r 'echo strlen("José"), "\n";'
5
```

Cuatro letras, cinco bytes. La `é` en UTF-8 ocupa dos.

Esto no es una curiosidad académica. Es la causa directa de títulos
cortados a la mitad, campos de base de datos desbordados, alineaciones de
informe equivocadas y ese rombo con un signo de interrogación adentro.

```text
$ php -r 'echo substr("José de Alencar", 0, 4), "\n";'
Jos�
```

`substr` cortó en medio de la `é`. Quedó medio carácter, que no es ningún
carácter, y la terminal dibuja el símbolo de reemplazo.

:::term Mojibake
El nombre del fenómeno en que `José` se vuelve `JosÃ©`: un texto codificado
en UTF-8 interpretado como Latin-1. Los dos bytes de la `é` pasan a leerse
como dos caracteres separados. La palabra es japonesa y significa,
literalmente, "transformación de caracteres".
:::

## Un carácter puede ocupar dos bytes

PHP tiene dos familias de funciones de texto. La antigua trabaja con
**bytes**. La familia `mb_` — de *multibyte* — trabaja con **caracteres**.

| Byte (evítalas) | Carácter (úsalas) |
|---|---|
| `strlen` | `mb_strlen` |
| `substr` | `mb_substr` |
| `strtoupper` | `mb_strtoupper` |
| `strtolower` | `mb_strtolower` |
| `str_pad` | no tiene equivalente directo |

Tabla: La extensión `mbstring` tiene que estar instalada. Por eso el
capítulo @cap:o-que-vamos-construir pidió revisar la lista de `php -m` antes
que nada.

```text
$ php -r 'echo mb_strlen("José"), "\n";'
4
$ php -r 'echo mb_substr("José de Alencar", 0, 4), "\n";'
José
$ php -r 'echo mb_strtoupper("josé"), "\n";'
JOSÉ
```

El último es el que agarra desprevenida a más gente: `strtoupper("josé")`
devuelve `JOSé`, con el acento en minúscula, porque la función solo conoce
el alfabeto ASCII.

:::key
Regla operativa: **en texto que puede tener acentos, usa `mb_`**. Nombre,
título, dirección, observación. Las funciones de byte siguen siendo
correctas para lo que es garantizadamente ASCII — un ISBN, un código, un
hash — y son más rápidas, lo que solo importa en volúmenes muy altos.
:::

## Texto con intención

```php title="comillas.php" numbered
<?php

$titulo = 'O Cortiço';

echo 'Título: $titulo', "\n";
echo "Título: $titulo", "\n";
echo "Título: {$titulo}", "\n";
```

```text
Título: $titulo
Título: O Cortiço
Título: O Cortiço
```

Las comillas **simples** no interpretan nada: lo que está escrito es lo que
sale — incluidos `$titulo` y `\n` literales. Las comillas **dobles**
interpolan variables y reconocen secuencias de escape.

Las llaves en `{$titulo}` son opcionales en el caso simple y obligatorias
en cuanto la expresión crece:

```php title="llaves.php" numbered
<?php

echo "Registro: {$ejemplar['registro']}\n";
echo "Primero: {$valores[0]}\n";
echo "Multa: {$multas['total_en_centavos']}\n";
```

:::key
La recomendación práctica: usa `{$...}` **siempre** que interpoles, aunque
puedas omitirlo. Cuesta dos caracteres, elimina la categoría entera de dudas
sobre dónde termina el nombre de la variable, y evita el defecto clásico de
que `"$titulo_completo"` busque una variable llamada `$titulo_completo`
cuando querías `$titulo` seguido de `_completo`.
:::

### Heredoc

Para texto largo, existe una forma que evita escapar comillas:

```php title="heredoc.php" numbered
<?php

$nombre = 'Marlene';
$dias = 9;

$mensaje = <<<TEXTO
    Hola, {$nombre}.

    El libro "O Cortiço" lleva {$dias} días de atraso.
    La multa acumulada es de R$ 7,20.

    Casa Amarela
    TEXTO;

echo $mensaje, "\n";
```

El identificador de cierre define la sangría: todo lo que esté alineado con
él se quita de cada línea. Eso permite mantener el texto sangrado junto con
el código, sin que la sangría aparezca en la salida.

Existe también `<<<'TEXTO'`, con comillas simples — el **nowdoc** —, que no
interpola nada. Es el equivalente de las comillas simples para texto largo.

:::warning
El heredoc es demasiado cómodo para armar SQL, y es exactamente ahí donde
mata. Esto es una falla de seguridad, no un mal estilo:

```php
$sql = <<<SQL
    SELECT * FROM libro WHERE titulo LIKE '%{$termino}%'
    SQL;
```

Si `$termino` viene de un campo de búsqueda, quien escriba `' OR 1=1 --`
cierra la comilla, agrega su propia condición y lee la tabla entera. El
comando dejó de ser un comando y se volvió un formulario en blanco para que
lo complete el visitante.

La forma correcta manda el valor **separado** del comando, de modo que
nunca pueda leerse como instrucción. La regla vale desde ya y vale para
todo: **no interpoles datos externos dentro de SQL, de HTML ni de comandos
de terminal.**
:::

## El recibo cortado al medio

```php title="recibo.php" numbered
<?php

function lineaDelRecibo(string $titulo, int $centavos): string
{
    $titulo = str_pad(substr($titulo, 0, 30), 30);
    $valor = number_format($centavos / 100, 2, ',', '.');

    return $titulo . str_pad($valor, 10, ' ', STR_PAD_LEFT);
}

echo lineaDelRecibo('Memórias Póstumas de Brás Cubas', 720), "\n";
echo lineaDelRecibo('O Cortiço', 720), "\n";
```

```text
Memórias Póstumas de Brás Cub      7,20
O Cortiço                       7,20
```

Dos cosas mal en la misma salida.

El primer título se cortó en treinta **bytes**, no treinta caracteres — por
eso desaparece antes de lo esperado, y, con otro título, cortaría un acento
por la mitad.

Y la alineación de la segunda línea está visiblemente corrida. `str_pad`
completó hasta treinta bytes; como `Cortiço` tiene un carácter de dos bytes,
la columna quedó un carácter más corta que la de arriba. En una impresora
térmica de mostrador, eso es una columna desalineada en cada recibo con
acento — es decir, en casi todos.

## Por qué la alineación salió torcida

Porque **alinear es una operación visual sobre caracteres**, y las dos
funciones usadas cuentan bytes. Las dos cosas coinciden en inglés y divergen
en portugués o en español, lo que hace que el defecto pase cualquier prueba
escrita con `"Test"` y `"Example"`.

Y hay una segunda capa: incluso `mb_str_pad` — que solo existe desde PHP
8.3 — no resuelve el caso general, porque algunos caracteres ocupan **dos
columnas** en pantalla aunque sean un solo carácter. Los emoji y los
ideogramas lo hacen. Para una alineación perfecta existe `mb_strwidth`.

## Normaliza en la entrada, escapa en la salida

```php title="recibo_correcto.php" numbered
<?php

function lineaDelRecibo(string $titulo, int $centavos): string
{
    if (mb_strlen($titulo) > 30) {
        $titulo = mb_substr($titulo, 0, 29) . '…';
    }

    $valor = number_format($centavos / 100, 2, ',', '.');

    return sprintf('%-30s %9s', $titulo, $valor);
}
```

```text
Memórias Póstumas de Brás Cub…      7,20
O Cortiço                          7,20
```

Tres cambios. El corte usa `mb_substr` y deja un carácter de puntos
suspensivos, que señala el recorte a quien lee. La alineación usa `sprintf`
con ancho declarado, lo que es más legible que dos `str_pad` encadenados. Y
`%-30s` alinea a la izquierda, `%9s` a la derecha — el formato del recibo
queda declarado en una sola línea, en lugar de repartido en tres.

:::anatomy title="El mini-idioma de `sprintf`"
lang: text
code: |
  sprintf('%-30s %9s %05d %.2f %%', $t, $v, $n, $f)
notes:
  - { line: 1, text: "`%s` es texto, `%d` entero, `%f` decimal." }
  - { line: 1, text: "El número es el ancho mínimo: `%9s` reserva nueve columnas." }
  - { line: 1, text: "El `-` alinea a la izquierda; sin él, alinea a la derecha." }
  - { line: 1, text: "`%05d` completa con ceros: útil para números de registro y códigos." }
  - { line: 1, text: "`%%` imprime un `%` literal." }
:::

Para dinero, sin embargo, `sprintf` no alcanza. `number_format` es quien
conoce el separador de miles y el decimal:

```php
echo number_format(123456.7, 2, ',', '.');   // 123.456,70
```

:::pitfall
`number_format` devuelve un **string**, y redondea. Formatear es lo último
que le pasa a un valor, en la salida — nunca en medio del cálculo. Sumar
`"123.456,70"` con otro valor formateado es el tipo de error que produce un
total plausible y equivocado.
:::

## Buscar, reemplazar y normalizar

```php title="busqueda.php" numbered
<?php

$titulo = '  O   Cortiço  ';

$limpio = trim($titulo);
$limpio = preg_replace('/\s+/u', ' ', $limpio);

var_dump($limpio);
var_dump(str_contains($limpio, 'Cort'));
var_dump(str_starts_with($limpio, 'O '));
var_dump(str_ends_with($limpio, 'ço'));
```

```text
string(10) "O Cortiço"
bool(true)
bool(true)
bool(true)
```

`str_contains`, `str_starts_with` y `str_ends_with` llegaron en PHP 8 y
reemplazaron el idioma antiguo `strpos($a, $b) !== false`, que era correcto
y confundía a todo el mundo por culpa de la posición cero.

El `preg_replace('/\s+/u', ' ', ...)` colapsa los espacios repetidos. El
modificador `u` al final de la expresión es obligatorio cuando el texto
tiene acentos — sin él, la expresión trabaja byte por byte y puede partir un
carácter.

Y la normalización que resolvería los tres José de Alencar:

```php title="normalizar.php" numbered
<?php

function claveDeBusqueda(string $texto): string
{
    $texto = mb_strtolower(trim($texto));
    $texto = preg_replace('/\s+/u', ' ', $texto);

    return transliterator_transliterate(
        'Any-Latin; Latin-ASCII; Lower()',
        $texto
    );
}

var_dump(claveDeBusqueda('JOSÉ  DE ALENCAR'));
var_dump(claveDeBusqueda('José de Alencar'));
```

```text
string(15) "jose de alencar"
string(15) "jose de alencar"
```

`transliterator_transliterate` viene de la extensión `intl` y quita los
acentos de forma correcta — bastante más confiable que las tablas de
`str_replace` que circulan por internet, que olvidan la mitad de los casos.

:::key
La clave de búsqueda se **guarda al lado** del texto original, nunca en su
lugar. La Casa Amarela muestra "José de Alencar" y busca "jose de alencar".

Dos campos, dos trabajos: uno sirve para que lo lea una persona, el otro
sirve para que el programa compare. Intentar hacer las dos cosas con un solo
campo es exactamente lo que produjo los tres registros.
:::

:::note En tu carrera
Un sistema en portugués o en español tiene una clase de defectos que un
sistema en inglés no tiene, y casi nunca aparece en los tutoriales. Acentos,
cedilla o eñe, mayúsculas acentuadas, orden alfabético que pone "Ávila"
después de "Zanetti", documentos con ceros a la izquierda que se vuelven
números, códigos postales ídem.

Eso es conocimiento del mercado local y vale más de lo que parece en una
entrevista. Cuando alguien pregunte "¿qué problema difícil resolviste?",
"tres registros del mismo autor por culpa de la codificación" es una
respuesta mucho mejor que un algoritmo de árbol binario — porque es real, es
específica, y muestra que ya lidiaste con datos sucios de verdad.
:::

## Todo lo que entra es texto

```php
$_GET['pagina'];      // string "2"
$_POST['dias'];       // string "9"
file_get_contents();  // string
fgetcsv();            // array de strings
```

Formulario, query string, archivo, cuerpo de la petición, variable de
entorno: todo llega como texto. El `"2"` que parece un número es un
`string`, y se va a comportar como string en cada lugar donde no se
convierta.

Convertir en el **borde** — justo en la entrada, una vez, en un solo lugar —
es lo que hace que el resto del programa trabaje con tipos de verdad:

```php
$pagina = (int) ($_GET['pagina'] ?? 1);
$dias = (int) ($_POST['dias'] ?? 0);
```

Después de esas dos líneas, `$pagina` y `$dias` son números en todo el resto
del programa, y ninguna función más adelante tiene que desconfiar. Sin
ellas, el `"2"` viaja como texto hasta encontrar el primer `===` y responder
mal.

:::summary
- Las comillas simples son literales; las dobles interpolan. Usa `{$var}`
	siempre.
- Heredoc para texto largo — y nunca para armar SQL.
- `strlen` cuenta bytes; `mb_strlen` cuenta caracteres.
- En texto que puede tener acentos, usa la familia `mb_`.
- `sprintf` declara el formato en una línea; `number_format` formatea
	dinero.
- Formatear es la última operación, en la salida, nunca en medio del
	cálculo.
- Guarda la clave de búsqueda normalizada **al lado** del texto original.
- Todo lo que entra es texto; conviértelo en el borde.
:::

:::milestone
Fin de la Parte 1. Tienes tipos, decisiones, bucles, funciones, arrays y
texto — todo el PHP que un programa necesita antes de volverse un proyecto.
A partir del próximo capítulo, un solo archivo deja de alcanzar.
:::

:::exercise level=1
Escribe una función que formatee centavos como moneda brasileña,
devolviendo `R$ 1.234,56`.

:::answer
```php
<?php

function reales(int $centavos): string
{
    return 'R$ ' . number_format($centavos / 100, 2, ',', '.');
}

echo reales(123456), "\n";
```
```text
R$ 1.234,56
```
:::

:::exercise level=2
Escribe `resumen(string $texto, int $limite): string`, que corte el texto en
el límite de **caracteres** sin partir una palabra, agregando `…`. Si cabe
entero, devuélvelo como está.

:::answer
```php
<?php

function resumen(string $texto, int $limite): string
{
    $texto = trim($texto);

    if (mb_strlen($texto) <= $limite) {
        return $texto;
    }

    $corte = mb_substr($texto, 0, $limite);
    $ultimoEspacio = mb_strrpos($corte, ' ');

    if ($ultimoEspacio !== false) {
        $corte = mb_substr($corte, 0, $ultimoEspacio);
    }

    return rtrim($corte) . '…';
}
```
El `!== false` en lugar de `if ($ultimoEspacio)` es obligatorio:
`mb_strrpos` devuelve `0` cuando el espacio está en la primera posición, y
cero es falso. Un título que empiece con una palabra de una sola letra
perdería el corte — y por eso las funciones de posición de PHP tienen fama
de confundir.
:::

:::exercise level=3
La Casa Amarela quiere unificar los tres "José de Alencar" sin perder nada.
Describe el procedimiento, incluyendo lo que harías **antes** de cambiar
cualquier registro.

:::answer
**Antes que nada: backup, y un backup restaurado.** No el archivo generado —
la restauración probada en una base separada. Una unificación equivocada es
irreversible, y "tenemos backup" es una frase que solo significa algo
después de que alguien restauró uno.

**Paso 1 — medir, sin cambiar nada.** Aplica la normalización a la lista
entera de autores, en memoria, y agrupa por la clave generada:

```php
$por_clave = [];

foreach ($autores as $autor) {
    $clave = claveDeBusqueda($autor['nombre']);
    $por_clave[$clave][] = $autor['nombre'];
}

foreach ($por_clave as $clave => $nombres) {
    if (count($nombres) > 1) {
        echo $clave, ': ', implode(' | ', $nombres), "\n";
    }
}
```

`implode` junta los elementos de un array en un texto, separados por lo que
le pases. El resultado responde cuántos casos existen de verdad — y la
respuesta suele ser incómoda. Pueden ser tres José de Alencar y otros
doscientos que nadie notó.

**Paso 2 — elegir el registro canónico, con una regla escrita.** La regla
que usaría: gana el nombre con acentuación correcta y mayor número de
títulos vinculados. Tiene que estar escrita porque alguien va a auditarla, y
porque van a aparecer casos ambiguos.

**Paso 3 — volver a apuntar las referencias, en una transacción.** Todos los
títulos de los registros duplicados pasan a apuntar al canónico, y los
duplicados se **desactivan**, no se borran. Conservarlos permite deshacer y
permite responder "¿por qué el título X cambió de autor en noviembre?".

**Paso 4 — impedir que vuelva.** Este es el paso que faltó la otra vez, y es
la razón de que Vera dijera "después volvió". Sin él, la unificación es un
operativo que se repite cada dos años:

- una columna `clave` generada por la normalización, con restricción
  `UNIQUE`;
- la normalización ocurriendo en el **borde** de entrada, en un solo lugar;
- y el registro sugiriendo el autor existente cuando la clave coincide — lo
  que resuelve el problema social, no solo el técnico. El encargado del
  teclado sin cedilla sigue escribiendo sin cedilla, y el sistema lo lleva
  al registro correcto.

**Lo que no haría:** corregir el mojibake con `str_replace('Ã©', 'é')`. Eso
resuelve los casos que viste y deja los que no viste, y crea un segundo
formato equivocado cuando alguien lo vuelve a ejecutar sobre texto ya
corregido. La conversión correcta es `mb_convert_encoding` en la
importación — y, si el dato ya está grabado mal, una migración única que
identifique exactamente los registros afectados antes de tocarlos.
:::

:::story Cuatrocientos sesenta y uno
Un mes después, con la clave de búsqueda en línea, Vera la probó.

Escribió "alencar". Vinieron 461 títulos, de un solo autor.

Escribió "ALENCAR". Lo mismo.

Escribió "  alencar  ", con espacios a los dos lados, mirando a Tainá.

Lo mismo.

— Ahora escríbelo mal — dijo Tainá.

Vera escribió "alencr".

Nada.

— Ese no lo encuentra.

— Pero yo sé a quién quiero.

— El sistema no.

Vera lo anotó en el cuaderno, en la sección "para preguntar después", que ya
tenía cuatro líneas.

El viernes, Márcia leyó la sección entera en voz alta en la reunión de
estado, demorándose al final de cada punto.

— Son cuatro. Entregamos dos antes de marzo.

— ¿Y las otras dos?

— Quedan escritas. Escrito es mejor que en la cabeza de Vera.
:::
