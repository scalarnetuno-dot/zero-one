---
source_hash: 330531921db4
title: "Primer programa en Java"
number: 2
part: p1
kicker: "Dos comandos, un archivo y la línea más famosa de la programación."
goal: >-
  Escribir, compilar y ejecutar un programa Java desde la terminal, explicar
  cada palabra de la firma del `main` y leer un mensaje de error del
  compilador sin entrar en pánico.
---

En Python escribes y corres. En Java escribes, **compilas** y corres. Esa
etapa extra es lo primero que asusta a quien viene de otro lenguaje, y
también es la que más devuelve: la compilación es donde alguien lee tu
código antes que tú.

:::diagram type="flowchart" caption="Del texto al programa: el compilador está en el medio a propósito."
nodes:
  - { id: src, type: io,      text: "App.java" }
  - { id: cc,  type: process, text: "javac App.java" }
  - { id: cls, type: io,      text: "App.class (bytecode)" }
  - { id: jvm, type: process, text: "java App" }
  - { id: out, type: start,   text: "Salida en la terminal" }
edges:
  - { from: src, to: cc }
  - { from: cc,  to: cls, label: "sin errores" }
  - { from: cls, to: jvm }
  - { from: jvm, to: out }
:::

El archivo `.class` no es código de máquina: es **bytecode**, un formato
intermedio que cualquier JVM sabe ejecutar. Por eso el mismo archivo
compilado corre en tu Windows y en el servidor Linux sin recompilar: la
promesa de 1995 que todavía se cumple.

## El archivo

Crea un archivo llamado `App.java`. El nombre no es decoración: una clase
pública tiene que vivir en un archivo con su mismo nombre.

```java title="App.java" numbered
public class App {
    public static void main(String[] args) {
        System.out.println("El primer programa");
    }
}
```

Compila y ejecuta:

```bash
javac App.java
java App
```

El primer comando crea `App.class` en la misma carpeta. El segundo le
entrega ese archivo a la máquina virtual, que busca un método llamado
`main` y empieza por él. Fíjate en que `java App` no tiene extensión: no
estás ejecutando un archivo, le estás pidiendo a una clase que empiece.

## La firma más copiada de la historia

Cinco palabras antes del nombre del método, y cada una resuelve un problema
concreto. Vale la pena gastar una página en esto porque vas a escribir esa
línea el resto de tu vida.

:::anatomy title="La firma del main, palabra por palabra"
lang: java
code: |
  public class App {
      public static void main(String[] args) {
          System.out.println("El primer programa");
      }
  }
notes:
  - { line: 1, text: "`public class App`: la clase es el envoltorio; en Java nada vive fuera de una." }
  - { line: 2, text: "`public` deja que la JVM vea el método desde fuera del archivo." }
  - { line: 2, text: "`static` permite llamarlo sin crear un objeto: al inicio del programa no existe ninguno." }
  - { line: 2, text: "`void` porque no le devuelve nada a quien lo llamó." }
  - { line: 2, text: "`String[] args` recibe lo que escribiste después del nombre del programa." }
  - { line: 3, text: "`System.out` es la salida estándar; `println` escribe y salta de línea." }
:::

:::trivia
`System.out.println` tiene 18 caracteres para hacer lo que Python hace con
5. La razón es la coherencia: `System` es una clase, `out` es uno de sus
campos y `println` es un método de ese campo. Java prefirió no abrir una
excepción en la gramática ni siquiera para la línea más escrita del mundo.
En 2023, treinta años después, el lenguaje por fin ganó un `println` suelto
en clases implícitas, y la comunidad todavía discute si fue una buena
idea.
:::

:::story ¿Ya está en producción?
Carlos corrió `javac App.java`. Esperó. No pasó nada.

Se quedó mirando la terminal unos diez segundos, convencido de que se había
colgado. Escribió `java App`. Y entonces, en la pantalla negra, apareció:

```text
El primer programa
```

Giró en la silla y anunció, demasiado fuerte para una oficina abierta:

—¡COMPILÓ!

Roberto, que pasaba con un café en la mano, se detuvo.

—¿Compiló? ¿Entonces ya está en producción?

—No. Imprime una frase.

—¿Una frase para el cliente?

—Una frase para mí.

Roberto asintió despacio, como quien no entendió pero va a repetir la
información en la próxima reunión como si hubiera entendido.
:::

## Argumentos: el programa recibiendo el mundo

`String[] args` no es adorno. Cambia el cuerpo del `main`:

```java title="Saludo.java" numbered
public class Saludo {
    public static void main(String[] args) {
        System.out.println("Hola, " + args[0]);
    }
}
```

```bash
javac Saludo.java
java Saludo Ana
```

```text title="Salida"
Hola, Ana
```

Acabas de escribir un programa con entrada. Es poco, pero es la diferencia
entre un ejercicio y una herramienta.

:::pitfall
Corre `java Saludo` sin el nombre. La respuesta es
`ArrayIndexOutOfBoundsException: Index 0 out of bounds for length 0`:
pediste el primer ítem de una lista vacía. Guarda ese mensaje: va a volver
en el capítulo 6, y siempre dice exactamente qué índice intentaste usar.
:::

## Cuando el compilador se queja

Borra el punto y coma de la línea 3 y compila de nuevo:

```text title="Terminal"
Saludo.java:3: error: ';' expected
        System.out.println("Hola, " + args[0])
                                              ^
1 error
```

Cuatro datos en tres líneas: el archivo, la línea, lo que faltaba y una
flecha apuntando al lugar exacto. Un error de compilación cuesta diez
segundos. El mismo defecto, en un lenguaje sin esta etapa, costaría una
ejecución rota frente a un usuario.

:::key
Lee el **primer** mensaje, no el último. Un error de sintaxis confunde al
compilador, que empieza a quejarse de cosas correctas justo debajo. Arregla
el primero, compila de nuevo, y la mitad de la lista desaparece.
:::

## Dos palabras que vas a oír mucho

:::term JDK
*Java Development Kit*: el paquete que compila y ejecuta. Trae `javac`,
`java`, el depurador y las bibliotecas.
:::

:::term JRE
*Java Runtime Environment*: solo ejecuta. No tiene `javac`. Se distribuyó
por separado durante años y es la causa de la mitad de las instalaciones
frustradas de quien empieza.
:::

:::history
Hasta Java 8, instalar Java en el escritorio instalaba un JRE con un plugin
de navegador: el origen de aquellas actualizaciones eternas de "Java
Update". Los applets murieron, el plugin se eliminó en Java 11 y hoy la
distribución estándar es un JDK. Si algún tutorial te manda a descargar "el
JRE", es de otra década.
:::

## ¿Y el IDE?

Nada hasta aquí exigió uno. Es deliberado: el botón verde de un IDE esconde
justamente las dos etapas que necesitabas ver. A partir del capítulo 16,
cuando el proyecto pasa a tener decenas de archivos y dependencias, un IDE
deja de ser comodidad y pasa a ser herramienta, y el libro va a usar uno.

:::tree title="Dónde estamos ahora"
java-one/
  App.java       # imprime una línea
  App.class      # generado por javac
  Saludo.java    # recibe un argumento
:::

:::summary
- Java compila antes de correr: `javac` produce bytecode, `java` lo
  ejecuta.
- Una clase pública vive en un archivo con su mismo nombre.
- `main` es donde empieza la JVM, y cada palabra de la firma resuelve un
  problema concreto.
- El error de compilación es la revisión más barata que existe. Lee el
  primer mensaje.
:::

:::checkpoint
Escribes, compilas y ejecutas un programa Java desde la terminal, sabes
explicar `public static void main(String[] args)` y sabes qué hacer cuando
`javac` se queja.
:::

:::milestone
El proyecto tiene una clase que imprime y otra que recibe un argumento.
Ninguna de las dos sobrevive al capítulo 16, pero el hábito de compilar
antes de correr sobrevive al libro.
:::

:::exercise level=1
Escribe un `Suma.java` que reciba dos números como argumentos e imprima la
suma. Pista: `Integer.parseInt(args[0])` convierte texto en número.

:::answer
```java
public class Suma {
    public static void main(String[] args) {
        int a = Integer.parseInt(args[0]);
        int b = Integer.parseInt(args[1]);
        System.out.println(a + b);
    }
}
```
Sin el `parseInt`, `args[0] + args[1]` concatena texto: `2` y `3` se
vuelven `"23"`. Es el primer encuentro con una idea del próximo capítulo:
el tipo decide qué significa el `+`.
:::

:::exercise level=2
Rompe el programa a propósito tres veces: cambia `String[]` por `String`,
borra una llave `}` y escribe `Sistem.out.println`. Lee los tres mensajes
antes de arreglarlos.

:::answer
El primero compila y falla al correr con `NoSuchMethodError: main`: la
firma tiene que ser exacta. El segundo da `reached end of file while
parsing`. El tercero da `cannot find symbol`, con una flecha apuntando a
`Sistem`. Tres mensajes, tres categorías: firma, sintaxis y nombre.
:::
