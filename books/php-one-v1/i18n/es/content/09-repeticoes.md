---
source_hash: a4884acb311f
title: "Repeticiones"
number: 9
slug: repeticoes
part: p1
kicker: "Funciona con doce. El problema es que nadie prueba con ocho mil."
goal: >-
  Recorrer arrays con `foreach`, repetir bajo una condición sin trabar el
  servidor, acumular resultados, y medir el costo de un bucle antes de que
  llegue a producción.
---

:::story Iba a ser un informecito
Jueves, 16:40. Cléber apareció en la esquina del escritorio de Dedé con la
postura de quien va a pedir algo pequeño.

— Es rapidito. Una listita de los libros atrasados.

— ¿Nada más?

— Nada más. Con el nombre del lector al lado.

Dedé lo escribió en once minutos. Lo ejecutó en su máquina, con los doce
préstamos de prueba que Tainá había cargado antes del almuerzo: instantáneo.

Lo subió a las 17:20. El viernes todavía estaba lejos, así que técnicamente
no era un deploy de viernes.

A las 17:50 Vera llamó diciendo que la pantalla del informe llevaba veinte
minutos en blanco y que había gente esperando en el mostrador.

En la Casa Amarela hay 8.412 préstamos abiertos y 1.204 lectores
registrados.
:::

El informe de Dedé no estaba mal. Estaba **bien doce veces**, que es una
categoría de defecto bastante más interesante — y bastante más cara — que el
código simplemente roto.

## `foreach` es el bucle

```php title="listar.php" numbered
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas Secas', 'dias' => 2],
    ['titulo' => 'Grande Sertão', 'dias' => 41],
];

foreach ($atrasados as $prestamo) {
    echo $prestamo['titulo'], ' - ',
         $prestamo['dias'], " dias\n";
}
```

```text
O Cortiço - 9 dias
Vidas Secas - 2 dias
Grande Sertão - 41 dias
```

Léelo como está escrito: *para cada elemento de `$atrasados`, llámalo
`$prestamo` y ejecuta el bloque*.

No hay índice, no hay `$i`, no hay `count()`. Donde no existe un índice no
existe forma de equivocarse con el índice, y una clase entera de defectos
clásicos simplemente no tiene dónde ocurrir.

Cuando la clave importa, viene con él:

```php title="con_clave.php" numbered
<?php

$por_tema = [
    'literatura' => 1240,
    'infantil' => 870,
    'referencia' => 91,
];

foreach ($por_tema as $tema => $total) {
    echo $tema, ': ', $total, "\n";
}
```

```text
literatura: 1240
infantil: 870
referencia: 91
```

La misma forma sirve para listas y para mapas, porque los dos son el mismo
tipo. En una lista, la clave es la posición numérica.

:::pitfall
`foreach` trabaja sobre una **copia** del array. Cambiar `$prestamo` dentro
del bucle no cambia el array original:

```php
foreach ($atrasados as $prestamo) {
    $prestamo['dias'] = 0;   // no cambia nada afuera
}
```

Existe la forma `foreach ($atrasados as &$prestamo)`, con `&`, que trabaja
por referencia y cambia el original. Funciona y trae un problema clásico
con ella: después del bucle, `$prestamo` sigue apuntando al último elemento,
y el próximo `foreach` que reutilice ese nombre sobrescribe la última
posición del array.

Si usas `&`, escribe `unset($prestamo);` en la línea siguiente al bucle. Si
puedes no usarlo, no lo uses: armar un array nuevo es más previsible.
:::

## `for` y `while`

```php title="for.php" numbered
<?php

for ($pagina = 1; $pagina <= 3; $pagina++) {
    echo "Pagina ", $pagina, "\n";
}
```

```text
Pagina 1
Pagina 2
Pagina 3
```

El `for` tiene tres partes separadas por punto y coma: dónde empieza, hasta
cuándo sigue, y qué hacer al final de cada vuelta. Sirve cuando el
**número** es el tema — paginación, repetición fija, cuenta regresiva —, no
cuando hay una colección que recorrer.

```php title="while.php" numbered
<?php

$intentos = 0;
$conectado = false;

while ($intentos < 3 && !$conectado) {
    $intentos++;
    echo "Intento ", $intentos, "\n";
    $conectado = ($intentos === 3);
}
```

```text
Intento 1
Intento 2
Intento 3
```

El `while` repite mientras la condición sea verdadera. Sirve cuando la
parada no depende de una colección: reintentar, leer hasta que se termine,
esperar hasta que responda.

:::warning
Todo `while` necesita una respuesta escrita a la pregunta *"¿qué, aquí
adentro, vuelve falsa la condición algún día?"*. En el ejemplo de arriba es
el `$intentos++`.

Y cuando la parada dependa de algo externo — red, archivo, otro sistema —,
el bucle necesita **también** un límite de intentos. Fíjate en el
`$intentos < 3`: sin él, una inestabilidad de red se vuelve un proceso PHP
girando para siempre, ocupando un trabajador del servidor que nunca más
atiende a nadie.
:::

## `break` y `continue`

```php title="control.php" numbered
<?php

$ejemplares = [
    ['registro' => 812, 'status' => 'restauracion'],
    ['registro' => 907, 'status' => 'disponible'],
    ['registro' => 344, 'status' => 'disponible'],
];

$elegido = null;

foreach ($ejemplares as $ejemplar) {
    if ($ejemplar['status'] !== 'disponible') {
        continue;
    }

    $elegido = $ejemplar['registro'];
    break;
}

echo $elegido ?? 'ninguno libre', "\n";
```

```text
907
```

`continue` salta a la vuelta siguiente. `break` abandona el bucle entero.

Fíjate en `$elegido = null` **antes** del bucle. Sin esa línea, una lista
vacía o totalmente no disponible dejaría la variable sin existir, y la línea
final imprimiría un aviso en lugar de un mensaje.

:::pitfall
PHP acepta `break 2` y `continue 2`, para salir de dos niveles de bucle a la
vez. Es sintácticamente válido y humanamente ilegible: quien lee tiene que
contar llaves para saber de dónde va a salir el código, y el día que alguien
agregue un `if` en el medio, el número sigue siendo `2` y pasa a apuntar a
otro lugar, sin ningún error.
:::

## El acumulador

Buena parte de los bucles no imprime nada: construye un valor.

```php title="acumulador.php" numbered
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas Secas', 'dias' => 2],
    ['titulo' => 'Grande Sertão', 'dias' => 41],
];

$total_de_dias = 0;
$criticos = 0;

foreach ($atrasados as $prestamo) {
    $total_de_dias = $total_de_dias + $prestamo['dias'];

    if ($prestamo['dias'] > 30) {
        $criticos++;
    }
}

echo $total_de_dias, " dias en total\n";
echo $criticos, " caso(s) critico(s)\n";
```

```text
52 dias en total
1 caso(s) critico(s)
```

Sumar, contar y filtrar son el mismo esqueleto: una variable creada **antes**
del bucle, modificada **dentro**, leída **después**. Crear el acumulador
dentro del bucle es el error que lo pone en cero en cada vuelta y devuelve,
al final, solo el último elemento.

PHP ya trae algunos acumuladores listos para los casos más comunes:

```php title="listos.php" numbered
<?php

$dias = [9, 2, 41, 0, 15];

echo array_sum($dias), "\n";
echo max($dias), "\n";
echo min($dias), "\n";
echo count($dias), "\n";
```

```text
67
41
0
5
```

## Doce registros mienten

Ahora, el informe de aquel jueves. Era esto, en los huesos: para cada
préstamo, encontrar el lector correspondiente en la lista de lectores.

```php title="informe_lento.php" numbered
<?php

$prestamos = [];
for ($i = 0; $i < 8412; $i++) {
    $prestamos[] = ['lector_id' => $i % 1204];
}

$lectores = [];
for ($i = 0; $i < 1204; $i++) {
    $lectores[] = ['id' => $i, 'nombre' => "Lector {$i}"];
}

$inicio = microtime(true);
$lineas = 0;

foreach ($prestamos as $prestamo) {
    foreach ($lectores as $lector) {
        if ($lector['id'] === $prestamo['lector_id']) {
            $lineas++;
            break;
        }
    }
}

printf("%d lineas en %.3f s\n", $lineas, microtime(true) - $inicio);
```

```text
8412 lineas en 0.412 s
```

Las dos primeras partes generan datos de prueba con el `for` que acabas de
ver. El `%` devuelve el resto de la división, lo que hace que los
identificadores de lector den la vuelta entre 0 y 1203.

`microtime(true)` devuelve la hora actual como un número con decimales.
Guárdala antes, réstala después, y mediste un fragmento de código. Es la
herramienta de medición más barata que existe y resuelve la mayoría de las
dudas.

Ejecútalo en tu máquina. El número va a ser distinto del mío; el orden de
magnitud va a ser parecido.

Fíjate en lo que está pasando: para cada uno de los 8.412 préstamos, el
programa recorre la lista de lectores hasta encontrar el correcto. En
promedio, seiscientas comparaciones por préstamo. **Cinco millones de
comparaciones** para imprimir ocho mil líneas.

Con los doce préstamos de prueba de Tainá eran 7.200 comparaciones, que PHP
hace sin pestañear. La diferencia entre los dos casos no es el código. Es la
escala.

## Indexar antes de recorrer

El arreglo es armar, una sola vez, un mapa de lector por identificador — y
después acceder directo, sin buscar:

```php title="informe_rapido.php" numbered
<?php

// los mismos $prestamos y $lectores de antes

$inicio = microtime(true);

$lector_por_id = [];
foreach ($lectores as $lector) {
    $lector_por_id[$lector['id']] = $lector;
}

$lineas = 0;
foreach ($prestamos as $prestamo) {
    $lector = $lector_por_id[$prestamo['lector_id']] ?? null;

    if ($lector !== null) {
        $lineas++;
    }
}

printf("%d lineas en %.3f s\n", $lineas, microtime(true) - $inicio);
```

```text
8412 lineas en 0.002 s
```

Doscientas veces más rápido, con cuatro líneas más.

Lo que cambió no fue la cantidad de trabajo aparente — los dos programas
recorren los préstamos una vez. Lo que cambió fue el **costo de encontrar un
lector**: de "buscar en una lista de 1.204" a "tomarlo directo por la
clave". Un mapa accede por clave en tiempo prácticamente constante, sin
importar cuántos elementos tenga.

PHP hace esa indexación en una línea:

```php
$lector_por_id = array_column($lectores, null, 'id');
```

`array_column` extrae una columna de un array de registros. Con `null` en el
segundo argumento mantiene el registro entero; el tercero dice qué campo
usar como clave. Vale conocer primero la versión manual, porque es la que
explica lo que está haciendo la función.

:::key
Cada vez que escribas un bucle, responde dos preguntas: **cuántas vueltas va
a dar en producción** y **cuánto cuesta una vuelta**. Multiplica.

Si el resultado pasa de un segundo, tienes una decisión que tomar — y no un
detalle para resolver después.
:::

Y hay una variante de este mismo formato que es mucho peor. Cambia la
comparación de adentro del bucle por un viaje a otra máquina por la red, y
cada vuelta deja de costar nanosegundos y pasa a costar milisegundos. El
mismo bucle que tardó cuatro décimas de segundo pasa a tardar media hora.

Ese patrón tiene nombre — **N+1** — y es probablemente el defecto de
rendimiento más común en aplicaciones web: una consulta para traer la lista,
más una consulta por cada elemento de la lista. Nace aquí, en un bucle
inocente, mucho antes de que exista una base de datos en el proyecto.

## El pequeño cambio de alcance

:::story Un pequeño cambio de alcance
El martes siguiente, Cléber volvió.

— Quedó genial el informe. Tuvimos solo un pequeño cambio de alcance.

Dedé esperó.

— La dirección quiere el historial junto. Cuántas veces se atrasó cada
lector en el año.

— Eso es otro informe.

— Es la misma pantalla. Solo una columnita más.

La "columnita más" era otra búsqueda por lector, dentro del bucle que ya
recorría ocho mil préstamos. Dedé hizo la cuenta en voz alta, y Cléber
escuchó el número hasta el final.

— Pero en tu máquina funciona, ¿no?

— Funciona. En mi máquina hay doce.

Cléber pensó un instante.

— ¿Y si ponemos doce en producción también?
:::

:::note En tu carrera
"Funciona en mi máquina" casi nunca es deshonestidad — es **falta de
datos**. La pregunta que lo resuelve, y que vale llevar a cualquier reunión
de refinamiento, tiene pocas palabras:

> *"¿Cuántos registros va a recorrer esto en producción, en el peor mes del
> año?"*

Si nadie sabe responder, esa es la primera tarea, y lleva diez minutos.
Preguntarlo **antes** de estimar es una de las diferencias concretas entre
un junior y un semisenior, y no tiene nada que ver con saber más sintaxis.

Y hay una segunda pregunta, que casi nadie hace: *"¿cuántas líneas de esta
pantalla va a leer alguien de verdad?"*. Un informe de ocho mil líneas no lo
lee nadie. Si la respuesta es "las cincuenta primeras", el problema de
rendimiento tenía una solución de producto antes de tener una solución
técnica.
:::

:::summary
- `foreach` recorre arrays; `for` es para números; `while` es para
	condiciones.
- `foreach` trabaja sobre una copia — `&` cambia el original y exige `unset`
	después.
- Todo `while` necesita algo que vuelva falsa la condición, y un límite de
	intentos cuando depende de algo externo.
- `continue` salta la vuelta, `break` abandona el bucle; `break 2` es
	ilegible.
- El acumulador nace antes del bucle, cambia dentro, se lee después.
- Un bucle dentro de otro multiplica: mide con `microtime(true)` antes de
	creer.
- Indexar por clave cambia una búsqueda lineal por un acceso directo.
- El costo de un bucle es vueltas × costo por vuelta — y una vuelta que sale
	de la máquina cuesta un millón de veces más.
:::

:::checkpoint
Recorres arrays, repites bajo una condición con seguridad, acumulas
resultados, y puedes medir y estimar en voz alta cuántas operaciones va a
ejecutar un bucle en producción.
:::

:::exercise level=1
Dada la lista de días de atraso `[9, 2, 41, 0, 15]`, usa un `foreach` para
calcular el total, el promedio y cuántos casos pasan de treinta días.
Después comprueba el total con `array_sum`.

:::answer
```php
<?php

$dias = [9, 2, 41, 0, 15];

$total = 0;
$criticos = 0;

foreach ($dias as $d) {
    $total = $total + $d;

    if ($d > 30) {
        $criticos++;
    }
}

$promedio = $total / count($dias);

echo "total ", $total, "\n";
echo "promedio ", $promedio, "\n";
echo "criticos ", $criticos, "\n";
echo "comprobando ", array_sum($dias), "\n";
```

```text
total 67
promedio 13.4
criticos 1
comprobando 67
```

Fíjate en que el promedio salió con decimales aunque sea `67 / 5`: la
división con `/` devuelve `float` cuando no es exacta. Si el resultado
tuviera que ser entero, la decisión de redondear o truncar tendría que estar
escrita.
:::

:::exercise level=2
Escribe un bucle que encuentre el préstamo con más días de atraso e imprima
el título. Trata el caso de la lista vacía.

:::answer
```php
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas Secas', 'dias' => 2],
    ['titulo' => 'Grande Sertão', 'dias' => 41],
];

$peor = null;

foreach ($atrasados as $prestamo) {
    if ($peor === null || $prestamo['dias'] > $peor['dias']) {
        $peor = $prestamo;
    }
}

if ($peor === null) {
    echo "ningun atraso\n";
} else {
    echo $peor['titulo'], " con ", $peor['dias'], " dias\n";
}
```

```text
Grande Sertão con 41 dias
```

La condición tiene dos partes por un motivo: en la primera vuelta no existe
nada con qué comparar, y `$peor === null` cubre eso. Inicializar `$peor` con
el primer elemento del array también funcionaría — y se rompería con la
lista vacía, que es justamente el caso que el ejercicio pidió tratar.

Fíjate también en el cortocircuito: cuando `$peor === null` es verdadero, el
lado derecho del `||` ni siquiera se evalúa. Sin eso, la comparación
intentaría leer `$peor['dias']` de un valor nulo.
:::

:::exercise level=3
El fragmento de abajo cuenta cuántos préstamos de libros infantiles hubo.
Tarda varios segundos con los datos reales. Identifica los tres problemas,
di cuál arreglarías primero y por qué.

```php
$total = 0;

foreach ($lectores as $lector) {
    foreach ($prestamos as $pre) {
        if ($pre['lector_id'] !== $lector['id']) {
            continue;
        }

        foreach ($libros as $libro) {
            if ($libro['id'] === $pre['libro_id']
                && $libro['tema'] === 'infantil') {
                $total++;
            }
        }
    }
}

echo $total;
```

:::answer
**Problema 1 — tres bucles anidados.** Son 1.204 lectores × 8.412
préstamos × 4.000 libros en el peor caso. La cuenta llega cerca de cuarenta
mil millones de comparaciones, y ninguna máquina de esta década termina eso
dentro de una petición web.

**Problema 2 — búsqueda lineal donde cabría un mapa.** Los dos bucles
internos están buscando por identificador. Indexar `$libros` por `id` antes
de empezar cambia el tercer bucle por un acceso directo.

**Problema 3 — el bucle externo no sirve para nada.** Fíjate en el
resultado: `$total` es un solo número. La variable `$lector` se usa solo
para compararla con `$pre['lector_id']` — y, como todo préstamo pertenece a
algún lector, la comparación siempre encuentra un par. El bucle de 1.204
vueltas existe para llegar al mismo número que se obtendría sin él.

**Lo que arreglaría primero es el tercero**, y esa es la parte importante de
la respuesta.

Los problemas 1 y 2 son optimizaciones de un código que no debería existir.
Arreglar la indexación aquí es dejar el mismo algoritmo equivocado, solo que
más rápido. La pregunta real — "¿cuántos préstamos de libros infantiles
hubo?" — no menciona a ningún lector.

```php
<?php

$libro_por_id = array_column($libros, null, 'id');

$total = 0;

foreach ($prestamos as $pre) {
    $libro = $libro_por_id[$pre['libro_id']] ?? null;

    if ($libro !== null && $libro['tema'] === 'infantil') {
        $total++;
    }
}

echo $total, "\n";
```

Cuarenta mil millones de comparaciones se volvieron ocho mil. Y fíjate de
dónde vino la ganancia: no de que el bucle se haya vuelto más astuto, sino
de que dos bucles dejaron de existir.

**La regla general:** antes de optimizar un bucle, pregunta si debería estar
ahí. Buena parte del código lento es código correcto resolviendo el problema
en el lugar equivocado.
:::
