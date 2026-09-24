---
source_hash: ae39e83296a4
title: "Condicionales"
number: 7
slug: condicionais
part: p1
kicker: "Once reglas de préstamo, cuarenta segundos de habla, cero líneas escritas en treinta y un años."
goal: >-
  Escribir decisiones legibles con `if`, `elseif` y `match`, convertir el
  anidamiento en escalera, y reconocer el momento en que la escalera está
  pidiendo otra cosa.
---

:::story Las once condiciones
— ¿Cuándo puede una persona llevarse un libro? — preguntó Tainá, con el
cuaderno abierto.

Vera respondió sin dejar de etiquetar:

— Si es socia. Si no tiene libros atrasados. Si no debe una multa de más de
cinco reales. Si no tiene ya tres libros. Si el ejemplar no es de consulta.
Si no es el último ejemplar del título, entonces solo sale con
autorización. Si es menor de doce, firma el responsable. Si el libro llegó
esta semana, queda una semana en exhibición. Si es época de exámenes, el
plazo baja a siete días. Si es de la colección de Seu Juvenal, no sale de
ninguna manera, pero eso nadie lo escribió.

Pausa.

— Y si es Dona Marlene, sale. Porque ella siempre devuelve.

Tainá contó las rayas en el cuaderno. Eran once.

— ¿Usted se sabe todo eso de memoria?

— Hago esto hace treinta y un años.

— ¿Y dónde está escrito?

Vera dejó de etiquetar por primera vez.

— En ninguna parte.

En la reunión del martes, Márcia preguntó cuántos días costaba la pantalla
de préstamo. Tainá dijo once reglas. Márcia oyó "once" y escribió "2 días"
en la planilla, porque su pregunta era sobre días.
:::

## La regla que vive en la cabeza de alguien

Esto no es una particularidad de las bibliotecas. En toda empresa existe al
menos una regla que:

- se aplica decenas de veces por día;
- tiene excepciones que nadie enumeró;
- vive en la cabeza de una o dos personas;
- y desaparece cuando esas personas se van de vacaciones.

El sistema suele implementar la versión simplificada — la que alguien logró
describir en una reunión de una hora — y el resto se sigue resolviendo en el
mostrador, por quien sabe.

:::note En tu carrera
Extraer requisitos de quien no sabe que tiene requisitos es una habilidad
específica, y casi nunca se enseña.

Lo que **no** funciona: "mándame la regla de préstamo por escrito". La
persona va a escribir las tres condiciones obvias y olvidar las ocho que
aplica en automático.

Lo que funciona:

1. **Pídele que narre un caso concreto**, de principio a fin, con nombre y
	 fecha. Lo concreto arrastra los detalles que la abstracción esconde.
2. **Pregunta por las excepciones en lugar de por las reglas**: "¿alguna vez
	 dejó que alguien se lo llevara con un libro atrasado?". Ahí aparece Dona
	 Marlene.
3. **Léele la regla de vuelta, en voz alta**, y espera la corrección. La
	 persona te va a corregir en un detalle que no habría recordado sola.
4. **Muéstrale el código funcionando.** Nada extrae requisitos como ver al
	 sistema rechazar a alguien que ella dejaría pasar.

Los pasos 3 y 4 valen más que los dos primeros, y son los que la mayoría de
los equipos se salta porque parecen retrabajo.
:::

## Toda decisión deja dos caminos

```php title="prestamo.php" numbered
<?php

$disponible = true;

if ($disponible) {
    echo "Se puede prestar\n";
} else {
    echo "Ejemplar no disponible\n";
}
```

```text
Se puede prestar
```

Paréntesis obligatorios alrededor de la condición, llaves delimitando el
bloque. A quien viene de Python le extrañan las llaves; quien viene de Java
se siente en casa.

Cuando omites el `else`, el camino del "no" sigue existiendo — simplemente
no hace nada. Tener conciencia de eso es lo que separa el programa correcto
del programa que solo parece correcto.

:::diagram type="flowchart" caption="Toda decisión tiene dos caminos, aunque escribas solo uno."
nodes:
  - { id: ini, type: start,    text: "Inicio" }
  - { id: d1,  type: decision, text: "¿disponible?" }
  - { id: sim, type: process,  text: "presta" }
  - { id: nao, type: process,  text: "(nada)" }
  - { id: fim, type: start,    text: "Fin" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "sí" }
  - { from: d1,  to: nao, label: "no" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

Un `if` sin `else` en un cálculo de multa significa que la variable del
resultado se queda con el valor que ya tenía — y si no tenía ninguno, el
programa sigue con una variable indefinida y un aviso que nadie leyó.

### Las llaves no son opcionales

PHP permite omitir las llaves cuando el bloque tiene una sola línea.
Permitirlo ya le costó mucho dinero al mundo:

:::compare left="Lo que parece" right="Lo que lee PHP" lang="php"
if ($ok)
    liberar();
    registrar();
---
if ($ok) {
    liberar();
}
registrar();
:::

`registrar()` se ejecuta siempre, porque la sangría no significa nada para
el intérprete. Solo significa algo para ti.

:::key
**Usa llaves siempre**, incluso en bloques de una sola línea. Es la regla de
estilo más fácil de justificar en una revisión de código, y cualquier
formateador automático las pone por ti.
:::

Existe además una sintaxis alternativa, con `:` y `endif`:

```php
<?php if ($disponible): ?>
    <span>Disponible</span>
<?php else: ?>
    <span>Prestado</span>
<?php endif; ?>
```

Existe para usarse **dentro de HTML**, donde una llave suelta en medio del
marcado es difícil de encontrar. En código PHP puro, no la uses.

## La escalera de `elseif`

```php title="situacion.php" numbered
<?php

$dias_de_atraso = 9;

if ($dias_de_atraso <= 0) {
    $situacion = 'al dia';
} elseif ($dias_de_atraso <= 7) {
    $situacion = 'atrasado';
} elseif ($dias_de_atraso <= 30) {
    $situacion = 'notificado';
} else {
    $situacion = 'suspendido';
}

echo $situacion, "\n";
```

```text
notificado
```

El orden es lo que hace funcionar la escalera: la **primera** prueba
verdadera gana, y las siguientes ni siquiera se evalúan. Nueve es menor que
30, pero también es menor que... no, no es menor que 7. Cayó en el tercer
escalón porque los dos primeros respondieron que no.

Invierte el orden y mira el desastre:

```php title="situacion_invertida.php" numbered
<?php

$dias_de_atraso = 9;

if ($dias_de_atraso <= 30) {
    $situacion = 'notificado';
} elseif ($dias_de_atraso <= 7) {
    $situacion = 'atrasado';
} elseif ($dias_de_atraso <= 0) {
    $situacion = 'al dia';
} else {
    $situacion = 'suspendido';
}

echo $situacion, "\n";
```

```text
notificado
```

La salida es igual, por casualidad. Pero cambia `$dias_de_atraso` por `0` y
la versión invertida sigue diciendo `notificado`, porque cero también es
menor que 30 y el primer escalón se traga a todos los demás. Los dos últimos
`elseif` se volvieron código inalcanzable — código que existe, se lee en
cada revisión y nunca se ejecuta.

:::key
Una escalera de `elseif` va del caso **más restrictivo** al **más
general**. Si puedes cambiar dos escalones de lugar sin cambiar el
resultado, o no se superponen — y entonces el orden de verdad no importa —
o uno de ellos nunca se ejecuta.
:::

Fíjate en la escritura: `elseif`, junto. Existe también `else if`, separado,
que funciona en código PHP puro y **se rompe** en la sintaxis alternativa
con `endif`. Usa siempre la forma junta.

## Anidar sale caro

Anidar `if` dentro de `if` es la forma más natural de escribir la segunda
condición y la más cara de mantener a partir de la tercera:

:::compare left="Anidado" right="En escalera" lang="php"
if ($socio) {
    if ($atrasados === 0) {
        if ($multa <= 500) {
            $puede = true;
        }
    }
}
---
if (!$socio) {
    $puede = false;
} elseif ($atrasados > 0) {
    $puede = false;
} elseif ($multa > 500) {
    $puede = false;
} else {
    $puede = true;
}
:::

Los dos hacen lo mismo. La diferencia es que el lado izquierdo crece hacia
la derecha con cada regla nueva: con once reglas, la asignación final queda
a cuarenta y cuatro espacios del margen, y quien lee tiene que mantener once
condiciones en la cabeza al mismo tiempo para saber cómo llegó ahí.

:::key
La sangría profunda no es un problema estético. Es un informe de cuántas
condiciones tiene que sostener el lector a la vez para entender la línea que
está leyendo. Tres niveles es el límite en que la mayoría de las personas
todavía acompaña.
:::

## La duodécima regla

Dedé escribió las once reglas de Vera como una escalera. Le llevó una tarde
y quedaron ochenta y tres líneas, de las cuales estas son las seis primeras:

```php title="puede_prestar.php" numbered
<?php

if (!$socio) {
    $puede = false;
} elseif ($atrasados > 0) {
    $puede = false;
} elseif ($multa_en_centavos > 500) {
    $puede = false;
} elseif ($prestamos_abiertos >= 3) {
    $puede = false;
} elseif ($es_de_consulta) {
    $puede = false;
} else {
    $puede = true;
}
```

Funcionó. Pasó una semana en producción sin un reclamo.

El martes siguiente, Vera avisó que en enero el límite sube de tres a cinco
libros, porque es época de vacaciones escolares.

Dedé abrió el archivo. La regla del límite estaba en el cuarto escalón — lo
descubrió contando. Para agregar "excepto en enero", tenía que decidir si la
excepción iba dentro de esa condición o se volvía un escalón nuevo, y
garantizar que el orden siguiera siendo correcto respecto de los otros diez.

Agregó un `&&` en el cuarto escalón:

```php
} elseif ($prestamos_abiertos >= 3 && !$vacaciones) {
```

Dos semanas después, alguien notó que lectores suspendidos se estaban
llevando cinco libros en enero.

El problema no fue que la línea estuviera mal — era correcta para la
pregunta que hacía. El problema es que la escalera no tiene nombres. Once
condiciones anónimas, distinguidas por posición, y un `&&` agregado en medio
de una de ellas es invisible en una revisión: la línea sigue teniendo el
mismo formato y ninguna otra línea cambió.

:::art caption="La regla de negocio más completa de la empresa suele vivir en la cabeza de una sola persona."
src="a-regra-de-negocio-mais-completa-da-empresa-costuma-morar-na-cabeca-de-uma-pessoa-so.png"
Viñeta editorial minimalista sobre fondo blanco: una bibliotecaria mayor
detrás de un mostrador de madera, etiquetando libros sin mirar, mientras
habla. De su voz sale, dibujándose en el aire, un diagrama de flujo enorme,
con decenas de rombos de decisión y flechas que se cruzan, ocupando la mitad
del cuadro. De pie frente al mostrador, una pasante con un cuaderno
demasiado pequeño, escribiendo rápido. Pocos elementos, humor seco, estética
de revista de tecnología.
:::

## Ponerle nombre a la decisión

El arreglo no es un `elseif` mejor. Es separar la decisión del límite de la
decisión de prestar:

```php title="puede_prestar.php (corregido)" numbered
<?php

$mes = 1;
$suspendido = true;

if ($suspendido) {
    $limite = 0;
} elseif ($mes === 1) {
    $limite = 5;
} else {
    $limite = 3;
}

echo "Limite de este lector: ", $limite, "\n";
```

```text
Limite de este lector: 0
```

Ahora existe una variable llamada `$limite`, con su propia escalera de tres
escalones que responde una sola pregunta. El escalón del préstamo pasa a ser
`$prestamos_abiertos >= $limite`, y la regla de enero tiene un lugar obvio
donde vivir.

El lector suspendido, que en la versión anterior estaba escondido en un `&&`
en medio de una condición de límite, ahora es el primer escalón y devuelve
cero.

## `match` no es `switch`

PHP tiene `switch` desde siempre, con dos defectos clásicos: compara con
`==`, y **se desliza** — olvidar un `break` hace que la ejecución siga en el
caso siguiente, sin aviso.

Desde PHP 8 existe `match`, que resuelve los dos:

```php title="match.php" numbered
<?php

$estado = 'transito';

$rotulo = match ($estado) {
    'disponible' => 'Libre',
    'prestado' => 'Con lector',
    'reservado', 'transito' => 'No disponible',
    default => 'Desconocido',
};

echo $rotulo, "\n";
```

```text
No disponible
```

Lee la estructura: `match` recibe un valor, lo compara con cada opción a la
izquierda de la flecha y **devuelve** lo que esté a la derecha de la primera
que coincida. Dos opciones pueden compartir el mismo resultado, separadas
por coma. El `default` toma lo que sobra.

| | `switch` | `match` |
|---|---|---|
| Comparación | `==` | `===` |
| Se desliza sin `break` | sí | no |
| Devuelve valor | no | sí |
| Caso no previsto | lo ignora en silencio | error en el acto |

Tabla: No hay caso en que `switch` sea mejor, salvo cuando una rama tiene
que ejecutar varias instrucciones.

La última línea merece atención. Un `match` sin `default` que reciba un
valor no previsto no lo ignora: se rompe, con un mensaje claro.

```text
$ php -r '$x = "nuevo"; echo match($x) { "a" => 1, "b" => 2 };'
PHP Fatal error: Uncaught UnhandledMatchError:
Unhandled match case "nuevo"
```

Parece hostil y es la mejor parte. Cuando alguien agregue un estado nuevo al
sistema y se olvide de tratarlo, lo descubres de inmediato, y no tres
semanas después por culpa de una pantalla en blanco.

`match` también funciona sin recibir ningún valor, comparando con `true`.
Entonces se vuelve una escalera que devuelve valor:

```php title="match_condicional.php" numbered
<?php

$suspendido = false;
$mes = 1;

$limite = match (true) {
    $suspendido => 0,
    $mes === 1 => 5,
    default => 3,
};

echo "Limite: ", $limite, "\n";
```

```text
Limite: 5
```

Son las mismas tres reglas de antes, en cinco líneas en vez de siete, y con
una diferencia que importa más que el tamaño: `$limite` se asigna **una sola
vez**, en un solo lugar. En la versión con `if`, se asignaba en tres
lugares, y agregar un cuarto escalón significaba acordarse de asignarla de
nuevo.

## Lo que cuenta como verdadero

Vale repetir la lista, porque es dentro de un `if` donde cobra:

| Falso | Verdadero |
|---|---|
| `false`, `null` | `true` |
| `0`, `0.0` | cualquier otro número |
| `""` y `"0"` | cualquier otro texto, incluido `"0.0"` |
| `[]` | una lista con cualquier elemento |

Tabla: `"0.0"` es verdadero y `"0"` es falso. Es el elemento más arbitrario
de la lista, y la razón de que el capítulo @cap:conversao-automatica insista
en comparar explícitamente.

:::summary
- Llaves siempre; la sintaxis con `endif` es solo para dentro de HTML.
- Todo `if` sin `else` deja un camino implícito — sabe cuál es.
- La escalera de `elseif` va del caso más restrictivo al más general; fuera
	de ese orden, los escalones se vuelven código inalcanzable.
- El anidamiento profundo es un informe de cuántas condiciones tiene que
	sostener el lector a la vez.
- Una escalera anónima esconde los cambios: separa la decisión y ponle
	nombre.
- `match` compara con `===`, no se desliza, devuelve valor y se rompe ante
	el caso no previsto.
- `match (true)` es una escalera que asigna la variable en un solo lugar.
:::

:::milestone
El programa ahora decide. Las once reglas de Vera todavía están en una
escalera, pero por primera vez en treinta y un años existen en algún lugar
además de su cabeza.
:::

:::exercise level=1
Escribe una condición que imprima `"Devolver hoy"`, `"Al dia"` o
`"Atrasado"` según los días que faltan para la devolución. Hazlo de dos
formas, con `if` y con `match (true)`.

:::answer
```php
<?php

$dias_restantes = 0;

if ($dias_restantes < 0) {
    $situacion = 'Atrasado';
} elseif ($dias_restantes === 0) {
    $situacion = 'Devolver hoy';
} else {
    $situacion = 'Al dia';
}

$situacion = match (true) {
    $dias_restantes < 0 => 'Atrasado',
    $dias_restantes === 0 => 'Devolver hoy',
    default => 'Al dia',
};

echo $situacion, "\n";
```

El orden es lo que hace funcionar a las dos: `< 0` tiene que ir antes de
`=== 0`, porque un número negativo no es igual a cero y caería en el
`default` — anunciando "Al dia" a quien está atrasado.
:::

:::exercise level=2
Reescribe el fragmento anidado de abajo como escalera, manteniendo los
mensajes. Después di cuál de las dos versiones preferirías recibir para
agregar una cuarta regla.

```php
if ($ejemplar_existe) {
    if ($estado === 'disponible') {
        if ($prestamos_abiertos < 3) {
            $respuesta = "Prestado";
        } else {
            $respuesta = "Limite alcanzado";
        }
    } else {
        $respuesta = "No disponible";
    }
} else {
    $respuesta = "Ejemplar no encontrado";
}
```

:::answer
```php
if (!$ejemplar_existe) {
    $respuesta = "Ejemplar no encontrado";
} elseif ($estado !== 'disponible') {
    $respuesta = "No disponible";
} elseif ($prestamos_abiertos >= 3) {
    $respuesta = "Limite alcanzado";
} else {
    $respuesta = "Prestado";
}
```

Fíjate en que cada condición se **invirtió**: `if ($existe)` con el error en
el `else` se volvió `if (!$existe)` con el error adentro. Es lo que permite
aplanar el anidamiento.

La escalera es la versión que preferiría recibir, por un motivo mecánico:
para agregar la cuarta regla, basta un escalón nuevo en el lugar correcto.
En la versión anidada, hay que abrir otro nivel de llaves en el medio,
volver a sangrar todo lo que está adentro, y el cambio aparece en la
revisión como doce líneas modificadas en lugar de cuatro.

Y fíjate también en lo que las dos versiones tienen en común, que es el
defecto que queda: `$respuesta` es un texto, así que quien vaya a usar ese
resultado va a tener que comparar frases para saber qué pasó.
:::

:::exercise level=3
Vera avisó que, en enero, el límite sube de tres a cinco libros — pero no
vale para lectores suspendidos. En julio vale lo mismo. Implementa el
cálculo del límite de dos formas: con `&&` dentro de la escalera del
préstamo, y con una variable `$limite` propia. Después di cuál dejarías en
el proyecto y qué cuesta la elección.

:::answer
**Forma 1 — dentro de la escalera del préstamo:**

```php
} elseif ($prestamos_abiertos >= (
    ($mes === 1 || $mes === 7) && !$suspendido ? 5 : 3
)) {
    $puede = false;
```

Funciona y cabe en una línea. Tiene tres problemas.

La regla de vacaciones quedó escondida dentro de una condición cuyo tema es
otro. Apareció un ternario dentro de una comparación dentro de un `elseif`,
lo que da tres niveles de razonamiento en una línea. Y las dos condiciones
que se juntaron con `&&` no tienen ninguna relación entre sí: una es sobre
el calendario, la otra es sobre el lector.

**Forma 2 — con nombre:**

```php
<?php

$mes = 7;
$suspendido = false;

$vacaciones = ($mes === 1 || $mes === 7);

$limite = match (true) {
    $suspendido => 0,
    $vacaciones => 5,
    default => 3,
};

echo "Limite: ", $limite, "\n";
```

```text
Limite: 5
```

Dejaría la segunda, por dos motivos concretos.

**La regla ganó un nombre.** Cuando Vera diga en octubre que la semana del
niño también cuenta, quien vaya a tocarlo busca `$vacaciones`, encuentra una
línea, y cambia una línea.

**El lector suspendido quedó explícito**, en el primer escalón, devolviendo
cero. En la forma 1 estaba dentro de un ternario dentro de una comparación —
que es exactamente donde se escondió el defecto real de la historia de este
capítulo.

**Lo que cuesta:** dos variables más y una indirección más para quien lee el
flujo principal. En un programa de treinta líneas, ese costo es real y puede
no compensar. La pregunta honesta no es qué versión es más elegante, es:
**¿cuántas veces va a cambiar esta regla?** Esta ya cambió dos veces en dos
semanas.
:::

:::story Ponle una excepción
El jueves, Tainá le mostró a Vera la pantalla nueva rechazando un préstamo,
con el mensaje *"Lector con pendientes: 1 libro atrasado"*.

Vera lo leyó, asintió con la cabeza y miró la fila.

— Dona Marlene tiene uno atrasado.

— Entonces el sistema la va a rechazar.

Vera miró la pantalla. Miró a Dona Marlene. Volvió a mirar la pantalla.

— Ponle una excepción.

Tainá lo anotó en el cuaderno, en la sección "para preguntar después", justo
debajo de *"¿y si el libro tiene dos autores?"*:

> *"regla n.º 12: Dona Marlene"*
:::
