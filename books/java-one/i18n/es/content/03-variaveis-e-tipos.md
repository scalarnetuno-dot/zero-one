---
source_hash: 37a2056cdba0
title: "Variables y tipos"
number: 3
part: p1
kicker: "Declarar un tipo es contratar a un revisor que trabaja gratis."
goal: >-
  Declarar variables de los cinco tipos del día a día, prever el resultado
  de una conversión y saber cuándo usar `var` sin perder la protección del
  compilador.
---

Un programa guarda cosas: un precio, un nombre, una respuesta de sí o no.
En Java, guardar exige decir de qué especie es la cosa guardada. Esa
exigencia parece burocracia los primeros diez minutos y se vuelve red de
seguridad para el resto del proyecto.

## La forma de la declaración

```java title="Tres declaraciones" numbered
double precio = 19.90;
String cliente = "Ana";
boolean pagado = false;
```

Cada línea tiene cuatro partes: el tipo, el nombre, el signo igual y el
valor. El tipo va a la izquierda porque es la primera pregunta que hace el
compilador, y la que te responde más tarde, cuando te equivoques.

:::diagram type="cells" caption="Una variable es un nombre pegado a una caja de tamaño conocido."
items: ["19.90", "\"Ana\"", "false"]
orientation: horizontal
notes:
  - { at: 0, text: "double · 8 bytes" }
  - { at: 2, text: "boolean" }
:::

## Los tipos que resuelven casi todo

| Tipo | Guarda | Rango o ejemplo |
|---|---|---|
| `int` | entero | de −2.100 millones a 2.100 millones |
| `long` | entero grande | hasta 9,2 trillones |
| `double` | decimal | `19.90` |
| `boolean` | verdadero o falso | `true` |
| `String` | texto | `"Ana"` |
| `char` | un carácter | `'A'` |

Tabla: Los seis tipos del día a día. Los otros —`byte`, `short`, `float`—
existen y pueden esperar hasta que tengas un motivo de memoria para usarlos.

Los cinco primeros, menos `String`, son **tipos primitivos**: el valor vive
directo en la variable. `String` es una clase, y la variable guarda una
*referencia* al texto. Esa distinción parece teórica ahora y explica, en el
capítulo 4, el error más común de quien viene de otro lenguaje.

:::key
El tipo no es para la computadora, es para ti. Cuando escribes
`double precio`, estás avisándole a la próxima persona que lea el código
—probablemente tú, en marzo— que ahí nunca va a aparecer el nombre de un
cliente.
:::

## El compilador verifica antes de correr

```java title="Error atrapado antes de correr"
int cantidad = 3;
cantidad = "tres";
```

```text title="Terminal"
Tienda.java:3: error: incompatible types:
    String cannot be converted to int
        cantidad = "tres";
                   ^
```

Fíjate en el momento: esto no pasó con el programa corriendo frente a un
cliente. Pasó en tu terminal, tres segundos después de que escribiste la
línea. En un lenguaje dinámico, el mismo defecto esperaría a la petición
número mil uno para aparecer.

## Conversiones: cuando el tipo cambia de idea

Java convierte automáticamente lo que no pierde información: un `int` cabe
en un `double`. Lo contrario exige que asumas la responsabilidad por
escrito:

:::compare left="Automático (widening)" right="Explícito (casting)"
int i = 42;
double d = i;
// 42.0
---
double d = 42.9;
int i = (int) d;
// 42, truncado
:::

El `(int)` es un **cast**: estás diciendo "sé que puede perder algo, hazlo
igual". Y pierde: `42.9` se vuelve `42`, no `43`. Java trunca, no redondea.

:::pitfall
`int promedio = 7 / 2;` guarda `3`, no `3.5`. La división entre dos enteros
descarta el resto sin ningún aviso. Si quieres decimales, al menos uno de
los lados tiene que ser decimal: `7.0 / 2`. Este es, de lejos, el error de
tipo más común en código de cobro.
:::

:::story El centavo de don Antônio
La primera factura de prueba salió con R$ 56,40. La segunda, con R$ 56,39.

Los mismos productos. El mismo carrito. Un centavo de diferencia.

Cláudia llevó el caso a la reunión con la cara de quien trae una bomba
envuelta en papel de regalo.

—El cliente va a preguntar.

—Es redondeo —dijo Carlos.

—El cliente va a preguntar *por qué* —insistió Cláudia.

Marina abrió el código, miró tres segundos y señaló la línea:
`double precio`.

—No es redondeo. Es que le pedimos a la computadora que guardara dinero en
una caja que no sabe guardar dinero.

Don Antônio, que estaba probando la tienda ese mismo día, llamó por la
tarde para avisar que había comprado un cable de R$ 19,90 y el total decía
R$ 19,89. No sabía explicar float, punto flotante ni IEEE 754. Sabía contar
dinero.
:::

## El dinero no es `double`

Guarda esta, porque el capítulo 19 la va a cobrar: `double` es binario y no
representa `0.1` exactamente.

```java title="La cuenta que no cierra" numbered
double total = 0.1 + 0.2;
System.out.println(total);
```

```text title="Salida"
0.30000000000000004
```

No es un bug de Java: así funcionan los números de punto flotante en
cualquier lenguaje. Para dinero existe `BigDecimal`, que guarda el valor en
base decimal y cobra más verbosidad a cambio de exactitud. El proyecto del
libro va a usar `BigDecimal` en el precio del producto a partir del
capítulo 18.

:::trivia
El estándar IEEE 754, que define este comportamiento, es de 1985 y lo
diseñó un comité que incluía a William Kahan, que ganó el premio Turing por
eso. La imprecisión no es descuido: es el precio de representar números
enormes y minúsculos con 64 bits. Java solo no te deja olvidar que existe.
:::

## Constantes

Cuando el valor no debe cambiar, `final` convierte el intento en error de
compilación:

```java
final double TASA = 0.08;
// TASA = 0.09;
// error: cannot assign a value to final variable TASA
```

La convención de nombre en mayúsculas con guion bajo (`TASA_MAXIMA`) es solo
una convención, pero es universal en Java, y el código que la ignora parece
extranjero.

## `var`: dejar que el compilador escriba el tipo

Desde Java 10 puedes omitir el tipo cuando es obvio por el valor:

```java
var precio = 19.90;    // double
var cliente = "Ana";   // String
```

El tipo sigue existiendo y sigue verificándose: solo no está escrito. Usa
`var` cuando la línea ya lo dice todo; escribe el tipo cuando el valor viene
de lejos, de una llamada a un método cuyo retorno no es evidente.

:::pitfall
`var` no es el `var` de JavaScript. No crea una variable sin tipo: *infiere*
el tipo y lo fija ahí. Después de `var x = 10;`, la línea `x = "diez";` no
compila. Y `var` sin valor inicial (`var x;`) tampoco compila: no hay de
dónde inferir.
:::

:::example Un nombre que explica, un tipo que protege
```java
double t = 56.4;              // ¿qué es t?
double totalDelPedido = 56.4; // ahora el humano también entiende
```
El compilador acepta los dos. Solo uno de ellos sigue teniendo sentido
dentro de seis meses.
:::

:::term Variable
Un nombre ligado a un espacio de memoria de tipo conocido. En Java el tipo
es fijo: el valor cambia, la especie no.
:::

:::summary
- Declarar es decir el tipo antes del nombre; el tipo se verifica al
  compilar.
- `int`, `long`, `double`, `boolean`, `String` y `char` cubren casi todo.
- La división entre enteros descarta el resto; uno de los lados tiene que
  ser decimal.
- `double` no sirve para dinero: el proyecto va a usar `BigDecimal`.
- `var` infiere el tipo sin renunciar a él.
:::

:::checkpoint
Declaras variables de los seis tipos básicos, prevés lo que pasa en una
conversión, sabes por qué `0.1 + 0.2` no da `0.3` y usas `final` y `var` en
el lugar correcto.
:::

:::milestone
El proyecto todavía es un puñado de archivos `.java` sueltos, pero ahora
guardan datos con tipo declarado. Es el vocabulario mínimo de la entidad
`Product` que nace en el capítulo 18.
:::

:::exercise level=1
Declara las cuatro variables que describen un producto de tienda: nombre,
precio, cantidad en stock y si está activo. Imprime las cuatro en una
línea.

:::answer
```java
String nombre = "Teclado mecánico";
double precio = 349.90;
int cantidad = 12;
boolean activo = true;
System.out.println(nombre + " · R$ " + precio
        + " · " + cantidad + " un · activo: " + activo);
```
Esas cuatro líneas son el borrador de la entidad `Product`. Guarda el
archivo.
:::

:::exercise level=2
Calcula el promedio de `7`, `8` y `10` primero con `int` y después con
`double`. Explica la diferencia en una frase.

:::answer
Con `int`, `(7 + 8 + 10) / 3` da `8`: el resto se descarta. Con
`(7 + 8 + 10) / 3.0` da `8.333...`. La cuenta es la misma; el tipo del
divisor decide si la parte fraccionaria sobrevive.
:::

:::exercise level=3
Suma `0.1` diez veces en un bucle e imprime el resultado. Después hazlo de
nuevo con `BigDecimal` (`new BigDecimal("0.1")` y el método `add`). Compara
las salidas.

:::answer
El `double` imprime `0.9999999999999999`. El `BigDecimal` imprime `1.0`. La
diferencia es invisible en un informe y catastrófica en una factura, y por
eso los sistemas financieros prohíben `double` por política, no por gusto.
:::
