---
source_hash: 2a294adbbba8
title: "Del archivo a la base de datos"
number: 12
slug: do-arquivo-ao-banco
part: p2
kicker: "Dos encargadas, un archivo, un préstamo. Deberían ser dos."
goal: >-
  Guardar datos que sobrevivan al final del programa, reproducir en tu
  máquina el defecto que un archivo no puede evitar, entender qué hace
  distinto una base de datos, e instalar una.
---

Todo lo que el programa guardó hasta aquí — el acervo, los préstamos, las
multas — desaparece cuando el programa termina. Cada ejecución empieza de
cero, y el único lugar donde el acervo de la Casa Amarela existe de verdad
es dentro del Sistema de 2009 y en el cajón de Vera.

Este es el capítulo en que los datos pasan a vivir en algún lugar.

## El acervo que desaparece

```php title="volatil.php" numbered
<?php

$acervo = [
    ['registro' => 812, 'titulo' => 'O Cortiço'],
    ['registro' => 907, 'titulo' => 'Vidas Secas'],
];

echo count($acervo), " ejemplares\n";
```

```text
$ php volatil.php
2 ejemplares
$ php volatil.php
2 ejemplares
```

Siempre dos. Si el programa registra un tercero, existe durante la ejecución
y desaparece en el punto y coma final. La memoria del proceso se le devuelve
al sistema operativo, y con ella se va todo.

:::term Persistencia
La propiedad de que un dato siga existiendo después de que el programa que
lo creó terminó. Un dato en memoria es volátil; un dato grabado en disco es
persistente. Todo lo que hace este capítulo es cruzar esa frontera.
:::

## Grabar en un archivo

PHP lee y escribe archivos con dos funciones de nombre descriptivo:

```php title="guardar.php" numbered
<?php

$acervo = [
    ['registro' => 812, 'titulo' => 'O Cortiço'],
    ['registro' => 907, 'titulo' => 'Vidas Secas'],
];

$json = json_encode(
    $acervo,
    JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE
);

file_put_contents('acervo.json', $json);

echo "grabado\n";
```

```text
$ php guardar.php
grabado
$ cat acervo.json
[
    {
        "registro": 812,
        "titulo": "O Cortiço"
    },
    {
        "registro": 907,
        "titulo": "Vidas Secas"
    }
]
```

`json_encode` transforma el array en texto en formato JSON, que presentó el
capítulo @cap:arrays. `file_put_contents` escribe ese texto en un archivo,
creándolo si no existe y **reemplazando el contenido** si existe.

Las dos constantes después de la coma cambian el formato de la salida.
`JSON_PRETTY_PRINT` rompe las líneas y aplica sangría, lo que hace el
archivo legible para la gente. `JSON_UNESCAPED_UNICODE` mantiene los
acentos como acentos — sin ella, `O Cortiço` se volvería `O Cortiço`,
que es válido e ilegible. El `|` entre las dos combina las opciones.

Leer de vuelta es el camino inverso:

```php title="cargar.php" numbered
<?php

$json = file_get_contents('acervo.json');
$acervo = json_decode($json, true);

echo count($acervo), " ejemplares\n";
echo $acervo[0]['titulo'], "\n";
```

```text
$ php cargar.php
2 ejemplares
O Cortiço
```

El `true` en el segundo argumento de `json_decode` es importante y fácil de
olvidar: sin él, el JSON se vuelve un objeto en lugar de un array, y todos
los `$acervo[0]['titulo']` de tu programa dejan de funcionar.

:::pitfall
`file_get_contents` devuelve `false` cuando el archivo no existe, y además
emite un aviso. Como `false` es falso y un array vacío también, el código
que hace `if (!$datos)` trata "el archivo no existe" y "el acervo está
vacío" como la misma cosa — otra vez el defecto del informe de Vera.

La forma honesta lo verifica antes:

```php
if (!file_exists('acervo.json')) {
    $acervo = [];
} else {
    $acervo = json_decode(file_get_contents('acervo.json'), true);
}
```
:::

Ahora el acervo sobrevive. Registra un ejemplar, vuelve a ejecutar, y está
ahí. Para un programa que usa una persona a la vez, eso resuelve.

La Casa Amarela tiene dos computadoras.

## 10:12

:::story El ejemplar que salió una vez
La Casa Amarela atiende en dos lugares al mismo tiempo. Está el mostrador de
la entrada, donde está Vera, y está la computadora de la sala del fondo,
donde Neide hace el registro de lectores nuevos y, cuando la fila aprieta,
también presta.

Un martes por la mañana, a las 10:12, las dos prestaron.

Vera le prestó el ejemplar 812 a Dona Marlene. Neide le prestó el 344 a un
muchacho que estaba apurado.

A las 10:30 el archivo tenía un préstamo.

— Desapareció el de Marlene — dijo Vera.

— O desapareció el mío — dijo Neide.

Desapareció el de Marlene. Se sabía porque el del muchacho estaba ahí, y no
porque alguien tuviera registro de nada.

Vera lo resolvió en el momento, como lo resuelve desde 1995: agarró una
ficha de papel, escribió 812, escribió Marlene, escribió la fecha, y la
puso en el cajón.

— Mientras la computadora no decide, decide el cajón.
:::

Este defecto no es de programación descuidada. Es una consecuencia directa
de cómo se escribe en un archivo, y se puede reproducir en tu máquina en dos
minutos.

```php title="prestar.php" numbered
<?php

$archivo = 'prestamos.json';

$prestamos = file_exists($archivo)
    ? json_decode(file_get_contents($archivo), true)
    : [];

echo "lei el archivo: ", count($prestamos), " prestamos\n";

sleep(5);

$prestamos[] = [
    'ejemplar' => (int) $argv[1],
    'lector' => $argv[2],
];

file_put_contents($archivo, json_encode($prestamos));

echo "grabe: ", count($prestamos), " prestamos\n";
```

Dos cosas nuevas. `$argv` es un array con lo que vino en la línea de
comandos: `$argv[0]` es el nombre del archivo, `$argv[1]` es el primer
argumento. Y `sleep(5)` hace que el programa espere cinco segundos — aquí
solo sirve para volver visible una ventana de tiempo que, en la vida real,
dura milisegundos.

Abre **dos terminales** y ejecuta uno en cada una, con menos de cinco
segundos de diferencia:

```text
Terminal 1                          Terminal 2
$ php prestar.php 812 Marlene
lei el archivo: 0 prestamos
                                    $ php prestar.php 344 Muchacho
                                    lei el archivo: 0 prestamos
grabe: 1 prestamos
                                    grabe: 1 prestamos
```

Los dos grabaron. Los dos dijeron que salió bien. Y el archivo:

```text
$ cat prestamos.json
[{"ejemplar":344,"lector":"Muchacho"}]
```

Un préstamo.

:::art caption="Dos préstamos en el mismo minuto; el archivo guardó uno."
src="dois-emprestimos-no-mesmo-minuto-o-arquivo-guardou-um.png"
Viñeta editorial minimalista sobre fondo blanco, composición dividida al
medio. A la izquierda, una bibliotecaria mayor en el mostrador de la
entrada; a la derecha, una encargada en la computadora de una sala del
fondo. De las dos pantallas sale, al mismo tiempo, una hoja de papel volando
hacia una única carpeta de archivo en el centro, demasiado pequeña, donde
solo cabe una hoja: la otra choca contra el borde y cae al piso. En primer
plano, el cajón de madera del mostrador entreabierto, con una ficha de papel
escrita a mano: "812 — Marlene". Pocos elementos, humor seco, estética de
revista de tecnología.
:::

## Por qué desaparece

Cada ejecución hizo tres cosas, en este orden: **leyó** el archivo entero,
**cambió** el array en memoria, **grabó** el archivo entero encima.

El problema está en el intervalo entre la lectura y la grabación. En ese
intervalo, el segundo programa leyó el mismo contenido viejo. Cuando grabó,
escribió encima de lo que el primero acababa de guardar — sin saber que
había algo encima que escribir.

:::term Condición de carrera
Cuando el resultado de una operación depende de cuál de dos procesos llega
primero, y nada garantiza el orden. El nombre viene de ahí: dos
participantes, una línea de llegada, y un resultado distinto en cada
ejecución. Es la categoría de defecto más difícil de reproducir, porque
desaparece cuando te detienes a observarla.
:::

Ninguno de los dos programas está mal. Los dos hacen exactamente lo que
escribiría cualquier persona. Lo que falta no está en el código: falta
alguien que **coordine** a los dos.

:::pitfall
Existe una salida parcial en el propio PHP: `flock()`, que le pide al
sistema operativo que bloquee el archivo mientras un proceso lo toca.
Funciona, y resuelve este caso específico.

Lo que no resuelve: mientras un proceso tiene el bloqueo, todos los demás
esperan — el archivo entero, no la línea que interesa. Con dos encargadas,
es imperceptible. Con veinte, la biblioteca se detiene. Y si el archivo está
en una carpeta de red, el bloqueo puede simplemente no funcionar, en
silencio.

Vale conocer `flock` para arreglar un script pequeño hoy. No vale construir
un sistema encima de él.
:::

## Qué hace distinto una base de datos

La carrera es el primer punto de una lista, y es la lista entera la que
justifica cambiar de herramienta.

| Pregunta | Archivo | Base de datos |
|---|---|---|
| Dos grabando a la vez | uno sobrescribe al otro | los dos graban, en orden |
| "Quiero solo los 20 atrasados" | carga los 8.412 y filtra | trae 20 |
| "¿Ya existe este número de registro?" | recorre todo, cada vez | responde por índice |
| "¿Se puede borrar este lector?" | nadie lo verifica | la base lo rechaza |
| "Graba las dos cosas o ninguna" | no existe | transacción |
| Acceso desde otra máquina | carpeta compartida y fe | para eso existe |

Tabla: Cada línea es un problema que alguien ya tuvo. La base de datos no es
más sofisticada por deporte — es la suma de cuarenta años de gente
resolviendo estas seis líneas.

:::term SGBD
*Sistema Gestor de Bases de Datos*: un programa que queda corriendo todo el
tiempo, guarda los datos en disco y atiende pedidos de otros programas. Es
quien coordina quién escribe, quién lee y en qué orden — el coordinador que
les faltaba a las dos terminales de la sección anterior.

MySQL, PostgreSQL, SQLite y SQL Server son SGBD. Este libro usa MySQL,
porque es el que la Casa Amarela ya tiene corriendo desde 2009.
:::

Lo importante es que la base de datos es **otro programa**. No es una
biblioteca que carga tu PHP: es un proceso separado, que puede estar en otra
máquina, y con el que tu programa conversa. Por eso puede coordinar dos PHP
— está fuera de los dos.

## Instalar y entrar

| Sistema | Cómo instalar |
|---|---|
| Ubuntu / Debian | `sudo apt install mysql-server` |
| macOS | `brew install mysql` y `brew services start mysql` |
| Windows | instalador oficial en `dev.mysql.com/downloads`, o WSL2 |
| Cualquiera, con Docker | `docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=clave mysql:8` |

Tabla: La línea de Docker levanta un MySQL aislado que desaparece cuando lo
ordenes, sin instalar nada en la máquina. Si ya usas Docker, es el camino
más limpio.

Una vez instalado, existe un programa cliente que conversa con él desde la
terminal:

```text
$ mysql -u root -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.

mysql>
```

El `-u root` dice con qué usuario entrar; el `-p` pide la contraseña. El
`mysql>` del final es el **prompt de la base de datos**: de aquí en
adelante, lo que escribas no es un comando de terminal, es un comando de
base de datos.

:::warning
En una instalación nueva, el usuario `root` suele tener la contraseña vacía
o usar la contraseña de tu usuario del sistema. Es cómodo y es solo para
desarrollo. Un MySQL con root sin contraseña expuesto a la red lo encuentra
un escaneo automático en cuestión de horas.

En tu máquina, sin exposición externa, está bien. En el servidor de la Casa
Amarela, no.
:::

Primer comando:

```text
mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.01 sec)
```

`SHOW DATABASES` lista las bases de datos que existen en ese servidor. Las
cuatro que aparecieron son del propio MySQL — usa bases de datos para
guardar información sobre las bases de datos, lo que es circular y
funciona.

Fíjate en el punto y coma. En el cliente de MySQL es **obligatorio**: es lo
que dice "terminé de escribir, puedes ejecutar". Olvidar el `;` es el error
número uno de quien empieza, y el síntoma es que el prompt cambia a `->` y
se queda esperando a que termines la frase.

Ahora la base de datos de la Casa Amarela:

```text
mysql> CREATE DATABASE casa_amarela
    -> CHARACTER SET utf8mb4
    -> COLLATE utf8mb4_unicode_ci;
Query OK, 1 row affected (0.02 sec)

mysql> USE casa_amarela;
Database changed

mysql> SHOW TABLES;
Empty set (0.00 sec)
```

Tres comandos y una lección en cada uno.

`CREATE DATABASE` crea la base. Fíjate en el `->` de las líneas 2 y 3: es el
prompt de continuación, porque el comando solo terminó en el `;` de la
tercera línea.

El `CHARACTER SET utf8mb4` dice en qué codificación la base va a guardar el
texto. Esta elección es la misma del capítulo @cap:strings, ahora del otro
lado: sin ella, puedes terminar con una base en `latin1` y con el segundo
José de Alencar naciendo solo.

:::trivia
El nombre `utf8mb4` existe porque MySQL pasó diez años llamando `utf8` a
una codificación que **no** era UTF-8 completo: soportaba como máximo tres
bytes por carácter, lo que cubre los acentos y no cubre los emoji ni
algunos ideogramas. Cuando lo arreglaron, ya había demasiadas bases en el
mundo usando el nombre equivocado como para poder corregirlo.

La salida fue crear `utf8mb4` — "UTF-8, de verdad, hasta cuatro bytes" — y
dejar el `utf8` antiguo como sinónimo del equivocado. Hoy `utf8` es un alias
de `utf8mb4` en las versiones nuevas, pero escribir `utf8mb4`
explícitamente sigue siendo lo correcto.
:::

`USE casa_amarela` elige en qué base van a trabajar los próximos comandos.
Sin eso, MySQL no sabe de qué base estás hablando.

`SHOW TABLES` lista las tablas. Está vacío, porque todavía no existe
ninguna.

## Tabla, fila, columna

Falta el vocabulario, y ya está en el cajón de Vera.

El cajón tiene un fajo de fichas del mismo tipo: todas con los mismos campos
impresos — número de registro, título, autor, estado —, cada una completada
con valores distintos.

| En el cajón | En la base de datos |
|---|---|
| el fajo de fichas de ejemplares | una **tabla** llamada `ejemplares` |
| una ficha | una **fila** (o registro) |
| el campo "registro" impreso en la ficha | una **columna** llamada `registro` |
| lo que está escrito en el campo | el **valor** de esa fila en esa columna |
| el cajón entero | la **base de datos** `casa_amarela` |

Tabla: La metáfora no es aproximada: el modelo relacional lo diseñó Edgar
Codd en 1970 pensando exactamente en eso.

Dos diferencias entre la ficha y la tabla, y las dos son ventajas del papel
que la base de datos cambia a propósito.

En la ficha, Vera puede escribir cualquier cosa en cualquier campo —
incluso "no sé" en el campo de fecha. En una tabla, cada columna tiene un
**tipo** declarado, y la base rechaza lo que no encaja.

Y en el cajón, si dos fichas tienen el mismo número de registro, nadie lo
nota. En una tabla, se le puede pedir a la base que lo impida.

:::key
Ese es el intercambio que propone el capítulo entero: renuncias a la
libertad de escribir cualquier cosa en cualquier lugar, y ganas un programa
que rechaza el dato inválido en la puerta, en lugar de descubrirlo dos años
después en un informe que no cierra.

El nombre de eso es **esquema** — la descripción de qué tablas existen, qué
columnas tiene cada una y qué cabe en cada columna.
:::

:::note En tu carrera
"¿Por qué no guardarlo en un archivo?" es una pregunta legítima, y la
respuesta honesta es: a veces, guárdalo.

Configuración, logs, caché de resultados, importación de planillas, un
archivo que edita una persona a la vez — todo eso vive bien en un archivo, y
poner una base de datos en el medio es trabajo extra sin ninguna ganancia.

La pregunta que separa los dos casos tiene tres partes: **¿dos personas
escriben al mismo tiempo? ¿necesitas buscar sin cargarlo todo? ¿alguna
regla tiene que garantizarse aunque el programa tenga un defecto?** Un "sí"
en cualquiera de ellas ya pide una base de datos.

Saber justificar la elección en ese lenguaje — y no con "una base de datos
es más profesional" — es lo que diferencia una decisión de arquitectura de
un hábito.
:::

:::summary
- Un dato en memoria es volátil; solo existe mientras el programa corre.
- `json_encode` + `file_put_contents` graba; `file_get_contents` +
	`json_decode` con `true` lo lee de vuelta como array.
- Leer, cambiar y grabar el archivo entero produce una carrera: quien graba
	último borra el trabajo del otro, sin ningún error.
- `flock` resuelve el caso pequeño y no resuelve la lista.
- Un SGBD es otro programa, que coordina a quien escribe porque está fuera
	de todos ellos.
- La tabla es el fajo de fichas, la fila es la ficha, la columna es el
	campo impreso.
- El esquema es la descripción de qué cabe dónde — la libertad que cambias
	por garantía.
:::

:::checkpoint
Grabas y lees datos en un archivo, puedes reproducir la carrera en dos
terminales y explicar por qué ocurre, tienes un MySQL corriendo, y creaste
la base `casa_amarela` con la codificación correcta.
:::

:::exercise level=1
Escribe dos programas: uno que agregue un ejemplar al `acervo.json` y otro
que liste lo que está grabado. Ejecuta el primero tres veces y compruébalo
con el segundo.

:::answer
```php title="registrar.php"
<?php

$archivo = 'acervo.json';

$acervo = file_exists($archivo)
    ? json_decode(file_get_contents($archivo), true)
    : [];

$acervo[] = [
    'registro' => (int) $argv[1],
    'titulo' => $argv[2],
];

file_put_contents(
    $archivo,
    json_encode($acervo, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)
);

echo "acervo con ", count($acervo), " ejemplares\n";
```

```php title="listar.php"
<?php

$acervo = json_decode(file_get_contents('acervo.json'), true);

foreach ($acervo as $e) {
    echo $e['registro'], ' - ', $e['titulo'], "\n";
}
```

```text
$ php registrar.php 812 "O Cortiço"
acervo con 1 ejemplares
$ php registrar.php 907 "Vidas Secas"
acervo con 2 ejemplares
$ php listar.php
812 - O Cortiço
907 - Vidas Secas
```

Fíjate en las comillas en `"O Cortiço"` en la línea de comandos: sin ellas,
la terminal partiría el título en dos argumentos en el espacio, y `$argv[2]`
sería solo `O`.
:::

:::exercise level=2
Reproduce la carrera de la sección "10:12" en tu máquina, con las dos
terminales. Después usa `flock` para impedirla, y explica qué pasaste a
pagar a cambio.

:::answer
```php title="prestar_con_bloqueo.php"
<?php

$archivo = 'prestamos.json';

$f = fopen($archivo, 'c+');
flock($f, LOCK_EX);

$contenido = stream_get_contents($f);
$prestamos = $contenido === '' ? [] : json_decode($contenido, true);

echo "lei: ", count($prestamos), " prestamos\n";
sleep(5);

$prestamos[] = ['ejemplar' => (int) $argv[1], 'lector' => $argv[2]];

ftruncate($f, 0);
rewind($f);
fwrite($f, json_encode($prestamos));

flock($f, LOCK_UN);
fclose($f);

echo "grabe: ", count($prestamos), " prestamos\n";
```

```text
Terminal 1                          Terminal 2
$ php prestar_con_bloqueo.php 812 Marlene
lei: 0 prestamos
                                    $ php ... 344 Muchacho
                                    (detenido, esperando)
grabe: 1 prestamos
                                    lei: 1 prestamos
                                    grabe: 2 prestamos
```

Dos préstamos. El defecto desapareció.

`fopen` con `'c+'` abre para lectura y escritura sin borrar el contenido.
`flock($f, LOCK_EX)` pide el bloqueo exclusivo y **se queda esperando** si
otro proceso ya lo tiene. `ftruncate` y `rewind` vacían el archivo antes de
reescribirlo, porque el bloqueo no es sobre el contenido.

**Lo que pasaste a pagar:** la Terminal 2 se quedó cinco segundos detenida,
sin hacer nada, esperando un archivo. Con dos encargadas eso es invisible.
Con veinte, cada una espera la suma de todas las anteriores — y la
operación entera, incluso la de quien solo quería consultar, entra en la
misma fila.

Además, el programa pasó de siete líneas a quince, y tres de ellas
(`ftruncate`, `rewind`, el `flock` de liberación) son las que alguien va a
olvidar en el próximo cambio.
:::

:::exercise level=3
La Casa Amarela quiere saber cuántos préstamos de libros infantiles hubo en
febrero. Los datos están en un `prestamos.json` con 8.412 registros y en un
`libros.json` con 4.000.

Escribe el programa que lo responde leyendo los archivos. Después enumera lo
que esa solución no puede hacer, y lo que exigiría cada punto de tu lista.

:::answer
```php
<?php

$json = file_get_contents('prestamos.json');
$prestamos = json_decode($json, true);

$libros = json_decode(file_get_contents('libros.json'), true);

$libro_por_id = array_column($libros, null, 'id');

$total = 0;

foreach ($prestamos as $p) {
    if (!str_starts_with($p['retirado_en'], '2027-02')) {
        continue;
    }

    $libro = $libro_por_id[$p['libro_id']] ?? null;

    if ($libro !== null && $libro['tema'] === 'infantil') {
        $total++;
    }
}

echo $total, "\n";
```

Funciona, y es la indexación del capítulo @cap:repeticoes aplicada a datos
persistidos. Cuatro cosas que no puede hacer:

**No puede responder sin cargarlo todo.** Para contar los préstamos de un
mes, se leyeron del disco los dos archivos enteros y se transformaron en
arrays en memoria — 12.412 registros para llegar a un número. Una base de
datos lee solo lo que alcanza el filtro, y con un índice ni siquiera eso.

**No puede correr mientras alguien graba.** Si se registra un préstamo en
medio de la lectura, el programa puede leer un JSON a medias y `json_decode`
devolver `null`. Eso exige la coordinación de la sección anterior.

**No puede garantizar que `libro_id` apunte a un libro que existe.** El
`?? null` está ahí justamente porque puede no apuntar. Una base de datos
rechaza la grabación de un préstamo con un libro inexistente — es la clave
foránea.

**No puede responder la pregunta siguiente sin un programa nuevo.** "¿Y en
marzo?" exige editar el código. "¿Y por tema?" exige otro programa. En SQL,
las tres preguntas son tres líneas distintas, escritas en el momento, sin
editar nada.

La cuarta es la más subestimada de las cuatro. El costo real del archivo no
es el rendimiento: es que **cada pregunta nueva se vuelve una tarea de
programación**, y Vera no va a abrir un pedido para averiguar algo que
quería saber ahora.
:::
