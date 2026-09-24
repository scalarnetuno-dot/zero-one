---
source_hash: 697b83e54152
title: "Manejo de archivos"
number: 26
slug: manipulacao-de-arquivos
part: p5
kicker: "La planilla de donaciones tenía doscientas mil filas. El script que la leía de una vez se detuvo en la línea tres, sin leer ninguna."
goal: >-
  Leer y escribir archivos sin depender de la carpeta desde la que se
  llamó el script, leer un archivo grande una línea a la vez, separar la
  lectura del procesamiento con un generador, tratar la codificación y el
  BOM, y grabar sin dejar medio archivo atrás.
---

:::story En la línea tres
Don Juvenal llegó con un pendrive y una sonrisa.

—La donación de la escuela estatal. Todo en una planilla. Doscientos mil
libros.

—¿Doscientos mil? —preguntó Vera—. La biblioteca tiene cuatro mil.

—Doscientas mil filas. Es el acervo entero de ellos, están cerrando.
Nosotros elegimos lo que queremos.

Tainá exportó la planilla a CSV —nueve megabytes— y ejecutó el script de
importación que había escrito para las donaciones pequeñas, de cincuenta
filas. El servidor de homologación de Vertexo tenía un límite de memoria
bajo, configurado a propósito por Nonato años antes.

```text
PHP Fatal error: Allowed memory size of 16777216 bytes exhausted
(tried to allocate 4096 bytes) in /srv/importar.php on line 3
```

—Línea tres —dijo—. Es la línea que lee el archivo.

Dedé miró la línea.

```php
$filas = file('donaciones.csv');
```

—Lee el archivo entero en memoria antes de que mires la primera fila.

—¿Y los libros de don Juvenal?

—Están todos en memoria. Por eso se acabó.
:::

## La ruta relativa a qué

Antes de la memoria, una trampa que el script de Tainá tenía y todavía no
había mostrado. `file('donaciones.csv')` busca el archivo **en la carpeta
desde la que se llamó a PHP**, no en la carpeta donde está el script:

```text
$ cd /srv && php importar.php
(funciona)

$ cd / && php /srv/importar.php
Warning: file(donaciones.csv): Failed to open stream: No such
file or directory in /srv/importar.php on line 5
```

El programador de tareas del servidor, que corre la importación de
madrugada, llama a los scripts desde la raíz. Toda ruta relativa se rompe
ahí, y no en la máquina de quien probó.

PHP da la carpeta del propio archivo en una constante:

```php
$ruta = __DIR__ . '/donaciones.csv';
```

`__DIR__` es la carpeta del archivo PHP en el que está escrita la línea:
siempre, desde donde sea que se lo llame. Toda ruta de este capítulo en
adelante empieza por ella, o por una configuración que diga dónde viven
los archivos.

:::key
Una ruta relativa es relativa a la carpeta de quien **llamó**, y eso cambia
entre la terminal, el programador de tareas y el servidor web. Arma la ruta
a partir de `__DIR__`, y el script encuentra los archivos desde donde sea
que corra.
:::

## Leer todo y leer una línea a la vez

El capítulo @cap:do-arquivo-ao-banco usó `file_get_contents` y
`file_put_contents`: el archivo entero se vuelve un texto, o un texto se
vuelve el archivo entero. Para un JSON de cincuenta libros, es lo correcto.
Para una planilla de doscientas mil filas, es el error de la historia.

Midiendo, en el servidor sin el límite:

```php title="todo.php" numbered
<?php

declare(strict_types=1);

$filas = file(__DIR__ . '/donaciones.csv');

echo count($filas), " filas\n";
echo round(memory_get_peak_usage() / 1048576, 1), " MB\n";
```

```text
$ php todo.php
200001 filas
28.5 MB
```

Un archivo de nueve megabytes ocupa veintiocho y medio en memoria:
doscientos mil textos separados, cada uno con el costo de ser un valor de
PHP. `memory_get_peak_usage()` devuelve el máximo de memoria que usó el
script hasta ese punto, en bytes.

La alternativa es abrir el archivo y leer **una línea a la vez**:

```php title="linea-a-linea.php" numbered
<?php

declare(strict_types=1);

$archivo = fopen(__DIR__ . '/donaciones.csv', 'r');
if ($archivo === false) {
    throw new RuntimeException('donaciones.csv no se abrió');
}

$total = 0;
try {
    while (($linea = fgets($archivo)) !== false) {
        $total++;
    }
} finally {
    fclose($archivo);
}

echo "{$total} líneas\n";
```

`fopen` abre el archivo y devuelve un **recurso**: un identificador que PHP
usa para leer de a poco. La `'r'` es el modo: lectura. `fgets` lee hasta el
final de la línea siguiente y devuelve `false` cuando el archivo se acaba.
`fclose` le devuelve el archivo al sistema.

El `finally` del capítulo @cap:excecoes está ahí a propósito: si algo
falla en medio de la lectura, el archivo se cierra igual.

## CSV, y el generador que separa leer de usar

Una planilla en CSV tiene campos separados —por punto y coma, cuando viene
de un Excel en portugués o español— y comillas alrededor de los que tienen
el separador dentro. Separar a mano con `explode(';', $linea)` se rompe en
el primer título con punto y coma. `fgetcsv` lee una línea y ya la devuelve
separada en campos.

Y hay una forma de escribir "leer el CSV línea a línea" una sola vez, y
usarlo en cualquier lugar como si fuera un array:

```php title="csv.php" numbered
<?php

declare(strict_types=1);

function leerCsv(string $ruta): Generator
{
    $archivo = fopen($ruta, 'r');
    if ($archivo === false) {
        throw new RuntimeException("no se abrió: {$ruta}");
    }

    $leer = fn() => fgetcsv($archivo, separator: ';', escape: '');

    try {
        $cabecera = $leer();
        while (($campos = $leer()) !== false) {
            yield array_combine($cabecera, $campos);
        }
    } finally {
        fclose($archivo);
    }
}

$total = 0;
$restauracion = 0;

foreach (leerCsv(__DIR__ . '/donaciones.csv') as $libro) {
    $total++;
    if ($libro['estado'] === 'restauracion') {
        $restauracion++;
    }
}

echo "{$total} libros, {$restauracion} para restauración\n";
echo round(memory_get_peak_usage() / 1048576, 1), " MB\n";
```

```text
$ php csv.php
200000 libros, 28571 para restauración
0.4 MB
```

Cero coma cuatro megabytes, contra veintiocho y medio. Y el mismo
resultado con el límite de dieciséis del servidor de homologación.

`yield` es lo que hace de `leerCsv` un **generador**. Una función con
`yield` no corre entera cuando se la llama: devuelve un objeto `Generator`,
que el `foreach` recorre. En cada vuelta, la función corre hasta el
siguiente `yield`, entrega ese valor, y se **pausa** ahí, con el archivo
abierto, hasta que el `foreach` pide el siguiente.

:::term Generador
Una función con `yield`. Al llamarla, no corre: devuelve un `Generator`.
Cada vuelta del `foreach` sobre él ejecuta la función hasta el siguiente
`yield` y recibe el valor entregado. Solo existe un valor en memoria a la
vez.

Quien usa el generador escribe un `foreach` común, sin saber si los
valores vienen de un array, de un archivo de nueve megabytes o de una
consulta a la base.
:::

`array_combine($cabecera, $campos)` junta las dos listas en un array con
nombres: `['titulo' => 'Libro 1', 'autor' => ...]`. El resto del programa
lee `$libro['estado']`, y no `$libro[3]`.

Los argumentos con nombre —`separator: ';'`— son los del capítulo
@cap:funcoes. `escape: ''` apaga un carácter de escape antiguo del CSV de
PHP que no existe en el CSV de Excel, y que PHP 8.4 pasa a exigir que se
informe.

:::key
El generador separa **de dónde vienen los datos** de **lo que se hace con
ellos**. La importación, el conteo y el informe usan el mismo `leerCsv`. Si
mañana las donaciones llegan en otro formato, cambia el generador, y ningún
`foreach`.

En el volumen 2, Eloquent tiene la misma idea con otro nombre: recorrer una
tabla de millones de filas sin cargarla entera.
:::

## Codificación, y tres bytes al principio

Los títulos de la planilla de don Juvenal llegaron así:

```text
Libro nÃºmero 1
```

Es la `ú` de "número" en UTF-8, leída como si fuera otra codificación: el
defecto del capítulo @cap:strings, ahora viniendo de un archivo. Dos causas
aparecen con frecuencia en planillas exportadas de Excel.

**El archivo no está en UTF-8.** El Excel antiguo graba el CSV en
Windows-1252, la codificación de antes del UTF-8 en las computadoras de
Brasil. La conversión es una línea, hecha a la entrada:

```php
$titulo = mb_convert_encoding($campos[0], 'UTF-8', 'Windows-1252');
```

**El archivo está en UTF-8 y empieza con un BOM.** El BOM son tres bytes
invisibles —`EF BB BF`— que algunos programas ponen al principio del
archivo para anunciar que es UTF-8. PHP no los quita. Se pegan al primer
campo de la cabecera, y `$libro['titulo']` pasa a no existir, porque la
clave se llama, en realidad, `"\xEF\xBB\xBFtitulo"`.

```php
$bom = fread($archivo, 3);
if ($bom !== "\xEF\xBB\xBF") {
    rewind($archivo);
}
```

`fread` lee los tres primeros bytes. Si no son el BOM, `rewind` vuelve al
principio del archivo y no se perdió nada. Esas cuatro líneas entran en
`leerCsv`, justo después del `fopen`.

:::pitfall
El BOM no aparece cuando abres el archivo en el editor, ni cuando imprimes
la cabecera en la terminal. El síntoma es una clave que "existe" y da
`Undefined array key "titulo"`. Cuando una clave que estás viendo no se
encuentra, imprímela con `var_dump(array_keys($fila))`: el `string(9)`
para una palabra de seis letras delata los tres bytes de más.
:::

## Escribir sin dejar medio archivo

El informe de donaciones elegidas vuelve a don Juvenal en CSV, para que lo
abra en Excel:

```php title="exportar.php" numbered
<?php

declare(strict_types=1);

function grabarCsv(string $ruta, array $filas): void
{
    $temporal = $ruta . '.tmp';
    $archivo = fopen($temporal, 'w');
    if ($archivo === false) {
        throw new RuntimeException("no se grabó: {$temporal}");
    }

    try {
        fwrite($archivo, "\xEF\xBB\xBF");
        foreach ($filas as $fila) {
            fputcsv($archivo, $fila, separator: ';', escape: '');
        }
    } finally {
        fclose($archivo);
    }

    rename($temporal, $ruta);
}

grabarCsv(__DIR__ . '/elegidos.csv', [
    ['titulo', 'autor'],
    ['Vidas Secas', 'Graciliano Ramos'],
    ['O Cortiço', 'Aluísio Azevedo'],
]);
```

Tres decisiones.

**El BOM va a propósito.** Aquí sí sirve: es lo que hace que Excel abra
bien las tildes.

**`fputcsv`** escribe cada fila con el separador y las comillas correctos:
lo inverso de `fgetcsv`.

**El archivo se escribe con otro nombre y se renombra al final.** Si el
script muere en el medio —memoria, corte de luz, un error en la fila ocho
mil—, lo que queda es un `elegidos.csv.tmp` a medias, y el `elegidos.csv`
del día anterior sigue entero. `rename` cambia un archivo por el otro de
una vez: quien abra el archivo nunca ve medio informe.

El capítulo @cap:do-arquivo-ao-banco mostró la otra mitad del problema:
dos personas escribiendo en el mismo archivo al mismo tiempo. Para eso
existe `flock`, que bloquea el archivo mientras alguien escribe, y existe
la base de datos, que fue la respuesta de aquel capítulo y sigue siendo la
de este. El archivo sirve para entrar y salir del sistema. El estado
compartido vive en la base.

## Lo que el volumen 2 hace con archivos

En el volumen 2, dos temas vuelven con ropa de framework.

La **subida**: la portada del libro, enviada desde la pantalla. El archivo
llega a una carpeta temporal, con un nombre elegido por quien lo envió, y
ese nombre no puede volverse ruta, porque `../../.env` también es un
nombre.

El **almacenamiento**: Laravel da una capa, `Storage`, que graba en el
disco local o en un servicio de archivos en la nube con el mismo código.
Por debajo, son los `fopen`, `fwrite` y `rename` de este capítulo.

:::note En tu carrera
"Funciona con el archivo de prueba" es la frase que antecede a la mayor
parte de los problemas con archivos: el de prueba tiene cincuenta filas,
está en UTF-8 sin BOM y queda en la misma carpeta del script. El de
producción tiene doscientas mil, vino del Excel de alguien y lo lee el
programador de tareas desde la raíz.

Antes de dar por lista una importación, pruébala con un archivo grande,
con tildes, con BOM, y llamando al script desde otra carpeta. Son cuatro
minutos, y es lo que separa el script que funciona del que funciona en tu
máquina.
:::

:::tree title="Dónde estamos ahora"
acervo/
  src/
    Importacion/
      Csv.php              # leer(): generador, BOM, separador ;
                           # grabar(): temporal + rename
  scripts/
    importar-donaciones.php  # __DIR__, nunca ruta relativa
:::

:::summary
- Una ruta relativa es relativa a quien llamó. `__DIR__` es la carpeta del
  propio archivo.
- `file` y `file_get_contents` cargan el archivo entero; `fopen` y `fgets`
  leen una línea a la vez. `fclose` en el `finally`.
- `fgetcsv` separa los campos respetando las comillas; `fputcsv` escribe.
- Una función con `yield` es un generador: entrega un valor a la vez y se
  pausa. Separa el origen de los datos de lo que se hace con ellos.
- Convierte la codificación a la entrada; el BOM se pega al primer campo y
  tiene que salir.
- Graba en un temporal y renombra al final: nunca queda medio archivo.
:::

:::checkpoint
Lees un CSV de doscientas mil filas con memoria constante, escribes la
lectura como un generador reutilizable, reconoces el BOM por el síntoma de
la clave que no existe, y grabas un archivo sin riesgo de dejarlo a
medias.
:::

:::exercise level=1
Di qué función usarías en cada caso, y por qué:

1. Leer la configuración `biblioteca.json`, de 2 KB.
2. Contar las líneas de un log de 3 GB.
3. Grabar el informe mensual que otras personas abren a cualquier hora.

:::answer
1. `file_get_contents` y `json_decode`. El archivo es pequeño y se
   necesita entero de una vez.
2. `fopen` y `fgets` en un bucle, o un generador. `file` intentaría poner
   tres gigabytes en memoria.
3. Escribir en un temporal y renombrar. Quien lo abra durante la grabación
   ve el informe anterior entero, y no la mitad del nuevo.
:::

:::exercise level=2
Escribe un generador `soloEnRestauracion(Generator $libros): Generator`
que recibe el generador de `leerCsv` y solo entrega los libros con
`estado` igual a `restauracion`. Usa los dos juntos para grabar un CSV solo
con esos libros.

:::answer
```php
function soloEnRestauracion(Generator $libros): Generator
{
    foreach ($libros as $libro) {
        if ($libro['estado'] === 'restauracion') {
            yield $libro;
        }
    }
}

$enRestauracion = soloEnRestauracion(
    leerCsv(__DIR__ . '/donaciones.csv')
);
grabarCsv(__DIR__ . '/restauracion.csv', $enRestauracion);
```

Para que esto funcione, `grabarCsv` pasa a aceptar `iterable` en lugar de
`array`: el tipo que acepta array **y** generador. Todo el camino, de la
lectura a la grabación, sigue con un libro a la vez en memoria: ninguno de
los dos generadores guarda la lista.

Faltó la cabecera en el archivo grabado: tiene que ser la primera fila
pasada a `grabarCsv`, y queda de ejercicio dentro del ejercicio.
:::

:::exercise level=3
La importación nocturna de las donaciones corre a las 2 h, desde el
programador de tareas, y graba las elegidas en la base. La primera noche
importó cero libros y no dio ningún error. Enumera las tres causas más
probables, en el orden en que las investigarías, y lo que agregarías al
script para que la próxima falla no sea silenciosa.

:::answer
En orden:

1. **Ruta relativa.** El programador de tareas llama desde la raíz, el
   `fopen` falla con un *warning* y devuelve `false`, y, si el script no
   revisa el `false`, el bucle no corre ni una vez.
2. **BOM en la cabecera.** `$libro['titulo']` no existe; si el script se
   salta las filas sin título, se las salta todas.
3. **Codificación.** Los títulos con tildes rotas fallan en una validación
   y se descartan en silencio.

Lo que agregaría:

- revisar el `false` del `fopen` y lanzar una excepción: el capítulo
  @cap:excecoes;
- contar las filas leídas, importadas y descartadas, y registrar las tres
  al final;
- terminar con error si las leídas son más que cero y las importadas son
  cero.

La importación que "no dio error" dio tres: el sistema solo no tenía cómo
contar ninguno. El capítulo @cap:erros-e-debug se ocupa de hacer que PHP
cuente.
:::
