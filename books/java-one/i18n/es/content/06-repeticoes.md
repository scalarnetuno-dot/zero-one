---
source_hash: 91580175e207
title: "Repeticiones"
number: 6
part: p1
kicker: "Escribir la misma línea diez veces es un error de diseño, no de tipeo."
goal: >-
  Elegir entre `for`, `for-each` y `while` según el problema, escribir un
  acumulador correcto y salir de un bucle sin romper la lógica.
---

La repetición es lo primero que una computadora hace mejor que una persona.
Y es también donde vive el primer defecto difícil: el bucle que corre una
vez de más, o una de menos.

## Una lista de valores

```java title="Precios.java" numbered
double[] precios = { 19.90, 4.50, 32.00 };

System.out.println(precios.length);   // 3
System.out.println(precios[0]);       // 19.9
```

Un array tiene tamaño fijo, definido en el momento en que nace, y
posiciones numeradas desde **cero**. El último índice es siempre
`length - 1`: esa aritmética de uno de menos es el origen de la mitad de los
errores de bucle.

:::diagram type="cells" caption="Tres valores, índices de 0 a 2. El índice 3 no existe."
items: ["19.90", "4.50", "32.00"]
index: 0
orientation: horizontal
notes:
  - { at: 2, text: "length - 1" }
:::

:::trivia
Contar desde cero no es un capricho: en C, `v[i]` significa literalmente "la
dirección de `v` más `i` posiciones", así que el primer ítem está a cero
posiciones del inicio. Java heredó la convención sin heredar la aritmética
de punteros. Edsger Dijkstra escribió un texto famoso de dos páginas, en
1982, defendiendo que el cero es matemáticamente más elegante, y ganó la
discusión, al menos entre los lenguajes de llaves.
:::

## El bucle que vas a usar casi siempre

```java title="for-each"
for (double precio : precios) {
    System.out.println(precio);
}
```

Se lee "para cada precio en precios". No hay índice, no hay contador, no hay
forma de pasarse del final. Cuando solo necesitas visitar todos los
elementos, que es casi siempre, esta es la forma correcta.

## El bucle con contador

```java title="for clásico" numbered
for (int i = 0; i < precios.length; i++) {
    System.out.println(i + ": " + precios[i]);
}
```

:::anatomy title="Las tres partes del for, separadas por punto y coma"
lang: java
code: |
  for (int i = 0; i < precios.length; i++) {
      System.out.println(precios[i]);
  }
notes:
  - { line: 1, text: "**Inicio**: corre una vez, antes de todo. `i` solo existe dentro del bucle." }
  - { line: 1, text: "**Condición**: se prueba antes de cada vuelta. ¿Falsa la primera vez? El cuerpo nunca corre." }
  - { line: 1, text: "**Avance**: corre al final de cada vuelta. Olvidarlo es el bucle infinito clásico." }
  - { line: 2, text: "El cuerpo usa `i` como índice: es el único motivo para elegir esta forma." }
:::

Usa el `for` clásico cuando el índice forma parte de lo que quieres:
numerar la salida, comparar con el elemento anterior, avanzar de dos en
dos.

:::diagram type="flowchart" caption="El bucle es una decisión que vuelve sobre sí misma."
nodes:
  - { id: ini,   type: start,    text: "i = 0" }
  - { id: test,  type: decision, text: "¿i < length?" }
  - { id: corpo, type: process,  text: "usa precios[i]" }
  - { id: inc,   type: process,  text: "i++" }
  - { id: fim,   type: start,    text: "Fin" }
edges:
  - { from: ini,   to: test }
  - { from: test,  to: corpo, label: "sí" }
  - { from: corpo, to: inc }
  - { from: inc,   to: test }
  - { from: test,  to: fim,   label: "no" }
:::

:::pitfall
`i <= precios.length` revienta con
`ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3`.
El signo es `<`, sin el igual. Esa excepción tiene el nombre más honesto de
la plataforma: dice qué índice pediste y cuál era el tamaño.
:::

## `while` y `do while`

```java title="Mientras no se acabe" numbered
int intentos = 0;
while (intentos < 3) {
    System.out.println("intento " + intentos);
    intentos++;
}
```

El `while` sirve cuando **no sabes cuántas vueltas** vas a necesitar: leer
líneas de un archivo hasta que se acabe, intentar una conexión hasta
lograrla, procesar una cola hasta vaciarla. Si sabes el número de vueltas,
el `for` lo dice mejor.

El `do while` prueba **después** de correr, así que el cuerpo se ejecuta al
menos una vez:

```java
do {
    System.out.println("corre aun con la condición falsa");
} while (false);
```

En la práctica vas a usarlo una vez cada dos años, en un menú de terminal.
Está aquí para que lo reconozcas cuando lo encuentres.

:::story El viernes del informe
El informe de stock corría todos los viernes a las seis de la tarde. Nunca
había dado problemas, lo que solo significa que nadie lo había mirado.

Ese viernes, Carlos ajustó una línea. Una sola: cambió el `i++` de lugar
para "dejarlo más legible". Hizo el commit a las 17:52 y se fue a su casa.

A las 18:03, el servidor de homologación empezó a calentarse.

A las 19:20, Marina recibió la alerta en su casa, abrió la notebook en la
mesa de la cena y encontró un bucle que contaba hasta diez sin llegar nunca
a diez. El contador avanzaba dentro de un `if` que casi nunca era
verdadero.

A las 19:41, escribió en la revisión del commit una frase que Carlos guardó
para siempre:

> "Todo bucle que escribes tiene que responder tres preguntas antes de la
> primera línea: qué acumula, qué varía y **cuándo se detiene**. Este
> respondía dos."

El lunes, Roberto quiso saber por qué se había caído el entorno. Marina lo
explicó. Él escuchó todo con atención e hizo la única pregunta que le
importaba:

—¿Pero esto lo podemos evitar cambiando el proceso de deploy?

Marina respondió que sí. Él se fue satisfecho. El bucle seguía mal, pero eso
era asunto de Carlos.
:::

## Acumular un resultado

```java title="Suma.java" numbered
double total = 0;

for (double precio : precios) {
    total += precio;
}

System.out.println("Total: R$ " + total);
```

La variable `total` nace **fuera** del bucle y sobrevive a él; `precio` nace
dentro y muere en cada vuelta. Cambiarlas de lugar es el error que hace que
el total vuelva siempre en cero.

:::key
Todo bucle útil responde tres preguntas antes de la primera línea: qué
acumula, qué varía y cuándo se detiene. Si no puedes responder las tres en
voz alta, el bucle todavía no está listo para escribirse.
:::

:::example Sumar, contar y filtrar son el mismo esqueleto
```java
int caros = 0;
for (double precio : precios) {
    if (precio > 20) {
        caros++;
    }
}
System.out.println(caros + " ítem(s) por encima de R$ 20");
```
La misma estructura del acumulador, con una decisión dentro. En el capítulo
14 esas tres operaciones ganan nombre propio —`reduce`, `count` y `filter`—
y se vuelven una línea cada una.
:::

## Salir antes: `break` y `continue`

```java title="Detenerse en la primera ocurrencia" numbered
int posicion = -1;
for (int i = 0; i < precios.length; i++) {
    if (precios[i] > 30) {
        posicion = i;
        break;          // lo encontró: no hace falta ver el resto
    }
}
```

`break` abandona el bucle; `continue` salta a la vuelta siguiente. Los dos
son legítimos y ahorran trabajo, pero cada uno es un desvío, y demasiados
desvíos convierten el bucle en un laberinto.

:::pitfall
`break` dentro de un bucle anidado sale **solo del bucle interno**. Quien
espera que salga de los dos suele descubrirlo después de media hora. Si
necesitas salir de los dos, la señal es clara: extrae un método y usa
`return`. Es el tema del próximo capítulo.
:::

## Bucle infinito: cómo pasa y cómo salir

```java
while (true) {
    // sin break, sin return: el programa no termina
}
```

En la terminal, `Ctrl+C` lo termina. Las tres causas más comunes: olvidar
el avance (`i++`), avanzar en la dirección equivocada (`i--` con la
condición `i < n`) o cambiar la condición dentro del cuerpo sin darte
cuenta. Si tu programa "se colgó", sospecha del bucle antes que de la
computadora.

:::tree title="Dónde estamos ahora"
java-one/
  App.java
  Saludo.java
  Suma.java       # acumulador
  Precios.java    # array + for-each
:::

:::summary
- Un array tiene tamaño fijo e índices de `0` a `length - 1`.
- `for-each` recorre todo sin índice: es la forma correcta para el caso
  común.
- El `for` clásico sirve cuando el índice es parte del problema.
- `while` es para cuando no sabes el número de vueltas.
- El acumulador vive fuera del bucle; la variable de la vuelta vive dentro.
:::

:::checkpoint
Recorres un array de las tres formas, escribes un acumulador correcto,
sabes qué causa un bucle infinito y usas `break` sin perderte.
:::

:::milestone
Fin de la Parte 1. Tienes un programa que recibe datos, decide y repite:
las tres capacidades que ofrece cualquier lenguaje. La Parte 2 cambia "un
programa que corre" por "un programa que se organiza", y ahí es donde Java
empieza a cobrar su precio y a pagar sus dividendos.
:::

:::exercise level=1
Recorre un array de cinco notas e imprime solo las que sean mayores o
iguales a 7.

:::answer
```java
double[] notas = { 5.0, 7.0, 9.5, 6.4, 8.0 };
for (double nota : notas) {
    if (nota >= 7) {
        System.out.println(nota);
    }
}
```
:::

:::exercise level=2
Encuentra el precio más alto de un array sin usar bibliotecas. Piensa cuál
debe ser el valor inicial de la variable del máximo, y por qué empezar en
cero es una trampa.

:::answer
```java
double mayor = precios[0];
for (double precio : precios) {
    if (precio > mayor) {
        mayor = precio;
    }
}
```
Empezar en `0` solo funciona por accidente, cuando todos los valores son
positivos. Empezar por el primer elemento funciona siempre, incluso con
temperaturas negativas, que es donde se rompe la versión perezosa.
:::

:::exercise level=3
Imprime las tablas de multiplicar del 1 al 5 usando dos bucles anidados,
con una línea por número. Después cuenta cuántas veces se ejecutó el cuerpo
del bucle interno.

:::answer
```java
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= 10; j++) {
        System.out.print(i * j + " ");
    }
    System.out.println();
}
```
El cuerpo interno corre 50 veces: 5 × 10. Esa multiplicación es la primera
noción de costo; en el capítulo 30 reaparece con un nombre feo, *problema
N+1*, cuando cada vuelta de un bucle se vuelva una consulta a la base de
datos.
:::
