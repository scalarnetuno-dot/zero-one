---
source_hash: 5b27c5ecb3de
title: "Operadores y expresiones"
number: 4
part: p1
kicker: "El signo igual no significa igual, y el doble signo igual engaña con el texto."
goal: >-
  Prever el resultado de cualquier expresión aritmética, lógica o de
  comparación, y explicar por qué `==` no sirve para comparar texto en Java.
---

Un operador es un símbolo que toma valores y devuelve otro. Usaste tres en
el capítulo pasado sin pensar. Este capítulo es corto y denso a propósito:
casi todo defecto de lógica que vas a cazar más adelante nace de un
operador mal entendido.

## Aritméticos

```java title="Cinco símbolos" numbered
int suma = 7 + 2;      // 9
int resta = 7 - 2;     // 5
int mult = 7 * 2;      // 14
int div = 7 / 2;       // 3  ← entero, el resto desaparece
int resto = 7 % 2;     // 1  ← el resto que desapareció
```

El `%` es el **módulo**: el resto de la división. Parece inútil hasta que
necesitas saber si un número es par (`n % 2 == 0`), paginar una lista o
distribuir ítems en columnas, y entonces aparece todas las semanas.

:::trivia
`%` en Java puede devolver un negativo: `-7 % 2` da `-1`, no `1`. El
lenguaje sigue la regla de C, donde el signo del resto acompaña al
dividendo. Python eligió lo contrario (`-7 % 2` da `1`). Dos lenguajes, dos
matemáticas defendibles, y un bug garantizado para quien cambia de uno a
otro sin fijarse.
:::

## Asignación y la forma corta

El `=` no pregunta si dos valores son iguales: **manda** el de la derecha al
nombre de la izquierda. Leer `total = total + precio` como una ecuación es
el camino más rápido a la confusión; léelo como "el nuevo total pasa a ser
el total anterior más el precio".

```java
total = total + precio;
total += precio;         // idéntico, y más corto
```

Existen `+=`, `-=`, `*=`, `/=` y `%=`. Todos hacen lo mismo: operan y
asignan.

## Incremento: el `++` y su posición

```java title="La posición cambia el valor de la expresión" numbered
int i = 5;
System.out.println(i++);   // imprime 5, después i vale 6
System.out.println(i);     // 6

int j = 5;
System.out.println(++j);   // imprime 6
```

`i++` devuelve el valor **antes** de sumar; `++i` suma y **después**
devuelve. En un bucle, solo en la línea (`i++;`), no hace ninguna
diferencia. Dentro de una expresión más grande, sí la hace, y por eso el
código profesional evita mezclar el incremento con otra cosa en la misma
línea.

## Comparación

| Operador | Pregunta |
|---|---|
| `==` | ¿son el mismo? |
| `!=` | ¿son distintos? |
| `>` `<` | mayor, menor |
| `>=` `<=` | mayor o igual, menor o igual |

Tabla: Los seis comparadores. Todos devuelven `boolean`, nunca un número.

Y aquí vive la trampa más famosa del lenguaje.

## `==` compara identidad, `.equals()` compara contenido

```java title="Esto puede no funcionar" numbered
String contrasena = new String("abc");

if (contrasena == "abc") {
    System.out.println("Acceso permitido");
}
```

No imprime nada. El `==` pregunta si los dos nombres apuntan **al mismo
objeto en memoria**, y no apuntan: `new String` creó un objeto nuevo. La
pregunta correcta es sobre el contenido:

```java title="Esto funciona siempre"
if (contrasena.equals("abc")) {
    System.out.println("Acceso permitido");
}
```

:::diagram type="cells" caption="Dos variables, dos objetos, el mismo contenido: `==` dice que no, `equals` dice que sí."
items: ["contrasena →", "objeto A: \"abc\"", "literal →", "objeto B: \"abc\""]
orientation: horizontal
:::

:::pitfall
A veces `==` funciona con `String`, y eso es peor que si nunca funcionara.
El compilador guarda los literales iguales en un mismo lugar (el *string
pool*), así que `String a = "abc"; String b = "abc";` hace que `a == b` dé
`true`. La prueba pasa en tu computadora y falla cuando el texto viene del
teclado, de un archivo o de una petición HTTP. **Para texto, usa siempre
`equals`.**
:::

:::tip Invierte la comparación con literales
`"abc".equals(contrasena)` hace la misma prueba y no revienta si
`contrasena` es `null`. Es un hábito de dos teclas que borra toda una clase
de errores; vas a reencontrarlo en el capítulo 13, cuando el
`NullPointerException` se vuelva tema.
:::

Para los primitivos (`int`, `double`, `boolean`, `char`), `==` es la
herramienta correcta: no hay ningún objeto, solo el valor. La regla práctica
es corta: **el primitivo usa `==`, el objeto usa `equals`.**

:::story El cupón que solo funcionaba en la máquina de Carlos
El cupón era simple: escribe PROMO10 y ganas diez por ciento.

Funcionó en la prueba de Carlos. Funcionó en la prueba de Carlos otra vez.
Funcionó en la prueba de Carlos por tercera vez, lo que debería haber
servido de alerta.

Al día siguiente, llamó don Antônio:

—Joven, ese cupón de ustedes no funciona.

—¿Usted escribió PROMO10, todo en mayúsculas?

—Lo escribí igualito a como está en el papel.

Carlos pasó cuarenta minutos intentando reproducirlo. Escribía el cupón, y
funcionaba. Marina se acercó, leyó la línea `if (cupon == "PROMO10")` e hizo
una sola pregunta:

—En tu prueba, ¿de dónde viene ese texto?

—Está escrito en el código.

—¿Y en el caso del cliente?

—Viene del... teclado.

Marina no dijo nada más. No hacía falta. Carlos ya estaba cambiando el `==`
por `.equals`, con esa sensación específica de estar arreglando un error que
el compilador había dejado pasar a propósito.
:::

## Lógicos

```java title="Tres operadores y una optimización importante" numbered
boolean tieneEntrada = true;
int edad = 16;

if (tieneEntrada && edad >= 18) { /* exige los dos */ }
if (tieneEntrada || edad >= 18) { /* basta uno */ }
if (!tieneEntrada)              { /* invierte */ }
```

`&&` y `||` tienen **cortocircuito**: la evaluación se detiene en cuanto el
resultado está decidido. Si el lado izquierdo de un `&&` es falso, el
derecho ni siquiera se ejecuta. Eso no es un detalle de rendimiento, es una
herramienta:

```java
if (nombre != null && nombre.equals("Ana")) { ... }
```

Si `nombre` es `null`, la segunda prueba nunca corre y el programa no
revienta. En el orden inverso, revienta siempre.

:::anatomy title="Cómo lee el compilador una expresión compuesta"
lang: java
code: |
  boolean permitido = edad >= 18
          && (tieneEntrada || invitado)
          && !bloqueado;
notes:
  - { line: 1, text: "Primero los comparadores: `>=` corre antes que `&&`." }
  - { line: 2, text: "Paréntesis primero: el `||` interno se resuelve antes que el `&&` externo." }
  - { line: 3, text: "`!` tiene precedencia alta: invierte solo `bloqueado`, no la expresión entera." }
:::

La tabla de precedencia completa tiene quince niveles y nadie la memoriza.
El consejo profesional es otro: **usa paréntesis** cuando la expresión tiene
más de dos operadores. No cuestan nada en rendimiento y ahorran una hora de
depuración.

## El ternario

```java
String estado = edad >= 18 ? "adulto" : "menor";
```

Léelo como una pregunta: *condición ? valor si sí : valor si no*. Sirve para
elegir **un valor**. No sirve para ejecutar dos bloques de código: para eso
existe el `if`, que es el capítulo siguiente.

:::summary
- `/` entre enteros descarta el resto; `%` devuelve el resto.
- `=` asigna, `==` compara. `i++` devuelve antes de sumar.
- El primitivo compara con `==`; el objeto compara con `equals`.
- `&&` y `||` se detienen en cuanto el resultado está decidido: úsalo contra
  `null`.
- Los paréntesis son documentación ejecutable.
:::

:::checkpoint
Prevés el resultado de expresiones aritméticas y lógicas, sabes por qué
`==` falla con texto y usas el cortocircuito para proteger una llamada.
:::

:::milestone
Nada nuevo en el proyecto, y es intencional: este capítulo es una deuda que
se paga por adelantado. Las reglas de aquí aparecen en cada `if` del resto
del libro.
:::

:::exercise level=1
Escribe un programa que reciba un número como argumento e imprima `"par"` o
`"impar"` usando `%` y el operador ternario.

:::answer
```java
int n = Integer.parseInt(args[0]);
System.out.println(n % 2 == 0 ? "par" : "impar");
```
:::

:::exercise level=2
Sin correrlo, di qué imprime este fragmento. Después córrelo y compruébalo.

```java
int i = 3;
int total = i++ + ++i;
System.out.println(total + " " + i);
```

:::answer
Imprime `8 5`. El primer `i++` usa `3` y deja `i` en `4`; el `++i` lleva `i`
a `5` y usa `5`. Entonces `3 + 5 = 8`. Si te equivocaste, no te sientas mal:
justamente por eso este tipo de línea no pasa una revisión de código.
:::

:::exercise level=2
Escribe la condición que deja entrar a alguien si tiene entrada **y** (es
mayor de edad **o** está acompañado). Después reescríbela sin ningún
paréntesis y explica por qué cambia el significado.

:::answer
`tieneEntrada && (edad >= 18 || acompanado)`. Sin paréntesis,
`tieneEntrada && edad >= 18 || acompanado` se lee como
`(tieneEntrada && edad >= 18) || acompanado`, porque `&&` tiene precedencia
sobre `||`. En esa versión, quien está acompañado entra aun sin entrada.
:::
