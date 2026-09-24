---
source_hash: 1d8c44d47373
title: "Excepciones"
number: 13
part: p2
kicker: "Un error tratado es un requisito. Un error tragado es una deuda con intereses."
epigraph: "Lo llamo mi error de mil millones de dólares. La invención de la referencia nula, en 1965."
epigraph_by: "Tony Hoare, creador de Quicksort"
goal: >-
  Lanzar y capturar excepciones, elegir entre *checked* y *unchecked*, crear
  una excepción propia y no volver a escribir nunca un `catch` vacío.
---

Los programas salen mal por tres motivos: el programador se equivocó, el
usuario mandó basura, o el mundo de afuera falló. La excepción es el
mecanismo con el que Java avisa que algo se salió de los rieles, y la forma
en que la tratas define la calidad de tu API.

## El error más famoso de la plataforma

```java title="NullPointerException" numbered
String nombre = null;
System.out.println(nombre.length());
```

```text title="Terminal"
Exception in thread "main" java.lang.NullPointerException:
  Cannot invoke "String.length()" because "nombre" is null
        at Tienda.main(Tienda.java:3)
```

Fíjate en el detalle: el mensaje dice **qué** variable era nula y **qué**
método intentaste llamar. Es una conquista reciente (Java 14, *helpful
NullPointer messages*); antes solo venía el número de línea, y quien tenía
cinco llamadas encadenadas en la misma línea se quedaba adivinando.

:::history
Tony Hoare introdujo la referencia nula en ALGOL W, en 1965, porque "era
fácil de implementar". En 2009 pidió disculpas públicamente en una charla,
llamándola su error de mil millones de dólares. Java heredó `null` de C++,
y el lenguaje pasó treinta años creando remedios: `Optional` (Java 8),
mensajes detallados (Java 14) y anotaciones de nulidad en las bibliotecas.
:::

:::story El bug que solo reproduce don Antônio
—Da error cuando hago clic —dijo don Antônio.

—¿Error en qué pantalla?

—En la pantalla.

Carlos pidió una captura. Llegó una foto del monitor, tomada con el
celular, en diagonal, con el reflejo de la ventana cubriendo la mitad del
mensaje. Se podían leer tres palabras: `NullPointerException`, `at` y
`ProductService`.

Intentó reproducirlo durante dos horas. Registró un producto, lo editó, lo
borró, hizo clic en todo. Nada.

Marina preguntó lo único que faltaba preguntar:

—Don Antônio, ¿usted completa el campo "apodo del producto"?

—No, joven, ese es opcional, ¿no?

Era opcional. Y era el único campo que el código leía sin verificar si
existía.

Ningún otro empleado de la empresa dejaba ese campo vacío, porque todo el
mundo había aprendido, sin ponerse de acuerdo, a completarlo todo. Don
Antônio no había aprendido nada de eso. Solo usaba el sistema como estaba
escrito.
:::

## `try`, `catch`, `finally`

```java title="La forma completa" numbered
try {
    int cantidad = Integer.parseInt(args[0]);
    System.out.println(100 / cantidad);
} catch (NumberFormatException e) {
    System.out.println("Eso no es un número: " + args[0]);
} catch (ArithmeticException e) {
    System.out.println("No puedo dividir por cero");
} finally {
    System.out.println("Esto corre siempre");
}
```

El `try` delimita el tramo de riesgo. Cada `catch` trata **un tipo** de
problema. El `finally` corre con o sin error: es donde se cierra un archivo,
una conexión, cualquier recurso.

:::pitfall
El pecado capital:

```java
try {
    guardar(producto);
} catch (Exception e) {
    // después lo veo
}
```

Eso no trata el error: borra la evidencia. El programa sigue como si
hubiera funcionado, el dato no se guardó y nadie se entera. Si de verdad no
puedes tratarlo, **relánzalo** o al menos regístralo en el log. Un `catch`
vacío es la única línea de código que yo reprobaría en cualquier revisión,
sin discusión.
:::

## Dos familias: *checked* y *unchecked*

:::diagram type="blocks" caption="La jerarquía que decide si el compilador te va a obligar a tratarla."
flow: false
rows:
  - [{ text: "Throwable", note: "todo lo que puede lanzarse" }]
  - [{ text: "Error", note: "la JVM se rindió: no lo trates" }, { text: "Exception", note: "checked: el compilador la exige" }]
  - [{ text: "RuntimeException", note: "unchecked: el compilador no la exige" }]
:::

| | *Checked* | *Unchecked* |
|---|---|---|
| Ejemplo | `IOException`, `SQLException` | `IllegalArgumentException`, `NPE` |
| Compilador | obliga a `try` o `throws` | no obliga nada |
| Significa | falla esperada del mundo externo | defecto de programación o de uso |

Tabla: La regla práctica: si quien llamó puede hacer algo al respecto,
*checked*; si es un bug, *unchecked*.

```java title="Checked: el compilador exige una decisión" numbered
// no compila sin tratarla:
Files.readString(Path.of("config.txt"));

// opción 1: tratarla aquí
try {
    Files.readString(Path.of("config.txt"));
} catch (IOException e) {
    System.out.println("no encontré el archivo");
}

// opción 2: declarar que no es mi problema
static String leer() throws IOException {
    return Files.readString(Path.of("config.txt"));
}
```

:::trivia
Las excepciones *checked* son una idea exclusiva de Java: ningún lenguaje
popular posterior repitió el experimento. El motivo es el efecto secundario
observado en el campo: para librarse de la obligación, generaciones de
programadores escribieron `catch (Exception e) {}`. El remedio creó la
enfermedad que quería curar. Los frameworks modernos, Spring incluido,
convierten casi todo a *unchecked*.
:::

## `throw`: avisar en vez de mentir

```java title="Rechazar es mejor que corregir a escondidas" numbered
public void descontarStock(int cantidad) {
    if (cantidad <= 0) {
        throw new IllegalArgumentException(
                "la cantidad debe ser positiva: " + cantidad);
    }
    if (cantidad > stock) {
        throw new IllegalStateException(
                "stock insuficiente: " + stock);
    }
    this.stock -= cantidad;
}
```

Dos excepciones distintas porque son dos problemas distintos:
`IllegalArgumentException` es culpa de quien llamó;
`IllegalStateException` es una situación del objeto. En el capítulo 26 esa
distinción se vuelve la diferencia entre responder `400 Bad Request` y
`409 Conflict`.

## Excepción propia: el nombre que lleva el significado

```java title="ProductNotFoundException.java" numbered
public class ProductNotFoundException extends RuntimeException {
    private final Long id;

    public ProductNotFoundException(Long id) {
        super("producto no encontrado: " + id);
        this.id = id;
    }

    public Long getId() {
        return id;
    }
}
```

Tres decisiones en esas diez líneas. Extiende `RuntimeException`
(*unchecked*), porque quien llamó no tiene cómo "tratar" un id que no
existe: quien lo trata es la capa HTTP. El mensaje incluye el id, para que
el log sirva de algo. Y el id queda guardado, para que quien la capture
pueda armar la respuesta.

:::key
El nombre de la excepción es su parte más valiosa.
`ProductNotFoundException` en el log dice lo que pasó sin que nadie tenga
que leer el mensaje. `Exception` y `RuntimeException` genéricas tiran ese
valor a la basura.
:::

## `Optional`: la alternativa al `null`

```java title="Decir que puede no haber nada" numbered
Optional<Product> encontrado = repository.findById(7L);

if (encontrado.isPresent()) {
    System.out.println(encontrado.get().getNombre());
}

// mejor: sin if
String nombre = encontrado
        .map(Product::getNombre)
        .orElse("desconocido");

// o lanzando la excepción correcta
Product p = encontrado
        .orElseThrow(() -> new ProductNotFoundException(7L));
```

`Optional` es una caja que puede estar vacía. La diferencia respecto de
`null` no es técnica, es de comunicación: la firma del método **avisa** que
el resultado puede no existir, y el compilador te obliga a decidir qué
hacer.

La última forma, `orElseThrow`, es la que el proyecto va a usar desde el
capítulo 22 hasta el final del libro. Guárdala.

:::pitfall
`Optional` sirve para el **retorno** de un método. No lo uses como
parámetro, ni como atributo de entidad, ni en un campo de record que se va a
volver JSON. El creador de la API, Brian Goetz, fue explícito al respecto, e
internet pasó diez años ignorándolo.
:::

## `try-with-resources`

```java title="Se cierra solo, incluso con error" numbered
try (var reader = Files.newBufferedReader(Path.of("datos.csv"))) {
    System.out.println(reader.readLine());
} catch (IOException e) {
    System.out.println("falló la lectura");
}
```

Lo que está entre paréntesis se cierra automáticamente al salir del bloque,
con o sin excepción. Antes de Java 7 eso exigía un `finally` con otro `try`
dentro: el fragmento de código más feo que el lenguaje llegó a pedir.

:::summary
- `try/catch` trata por tipo; `finally` corre siempre.
- *Checked* obliga a tratarla; *unchecked* señala un defecto de
  programación.
- Nunca escribas un `catch` vacío: relanza o registra.
- Una excepción propia con un nombre específico vale más que un mensaje
  largo.
- `Optional` comunica la ausencia en el tipo de retorno; `orElseThrow` es el
  estándar del proyecto.
:::

:::checkpoint
Tratas excepciones por tipo, decides entre *checked* y *unchecked*, creas
una excepción propia con contexto y usas `Optional` en el retorno en vez de
`null`.
:::

:::milestone
El proyecto sabe rechazar: precio inválido, stock insuficiente, producto
inexistente. Falta traducir esos rechazos en respuestas HTTP, y eso lo hace
el capítulo 26, usando exactamente las clases de este capítulo.
:::

:::exercise level=1
Escribe un programa que reciba un número como argumento, divida 100 por él
y trate los dos errores posibles con mensajes distintos.

:::answer
```java
try {
    int n = Integer.parseInt(args[0]);
    System.out.println(100 / n);
} catch (NumberFormatException e) {
    System.out.println("el argumento no es un número");
} catch (ArithmeticException e) {
    System.out.println("división por cero");
}
```
Falta un tercer caso: correrlo sin ningún argumento lanza
`ArrayIndexOutOfBoundsException`, que no se captura. ¿Lo encontraste? Buena
señal.
:::

:::exercise level=2
Crea `InsufficientStockException` guardando el stock disponible y la
cantidad pedida. Úsala en `descontarStock`.

:::answer
```java
public class InsufficientStockException extends RuntimeException {
    public InsufficientStockException(int disponible, int pedido) {
        super("stock " + disponible + ", pedido " + pedido);
    }
}
```
Guardar los dos números en el mensaje es lo que convierte un log en un
diagnóstico: sin ellos, sabes que falló, pero no por cuánto.
:::

:::exercise level=3
Escribe un método `Optional<Product> buscar(Long id)` sobre un
`Map<Long, Product>` y después úsalo de tres formas: con `orElse`, con
`orElseThrow` y con `ifPresent`.

:::answer
```java
Optional<Product> buscar(Long id) {
    return Optional.ofNullable(mapa.get(id));
}
```
`Optional.ofNullable` es el puente entre una API antigua que devuelve `null`
y el mundo de `Optional`. En las tres formas de uso, fíjate en que ninguna
obliga a un `if` explícito, y en que `orElseThrow` es la única que conserva
la información de que algo salió mal.
:::
