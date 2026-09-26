---
source_hash: d80c6b1356a3
title: "Enums y records"
number: 12
part: p2
kicker: "Dos recursos que borran código: uno para el conjunto cerrado, otro para el dato puro."
goal: >-
  Reemplazar constantes de texto por `enum`, escribir un `record` en una
  línea y explicar por qué los dos hacen que el compilador trabaje más.
---

Este capítulo tiene un efecto secundario raro: **borra** código que
escribiste en los capítulos 5 y 10. Enum y record son recursos que resuelven
dos casos tan comunes que el lenguaje decidió darles sintaxis propia.

## El problema del `String` como categoría

```java title="Lo que sale mal con texto suelto" numbered
String estado = "ACTIVO";

if (estado.equals("activo")) {    // no entra: mayúsculas distintas
    ...
}
estado = "ACTVIO";                // compila. y está mal.
```

El texto acepta cualquier valor, incluso los equivocados. El compilador no
tiene cómo ayudar porque, para él, `"ACTVIO"` es un texto perfectamente
válido.

## `enum`: el conjunto cerrado

```java title="Status.java" numbered
public enum Status {
    ACTIVO,
    INACTIVO,
    AGOTADO
}
```

```java
Status status = Status.ACTIVO;

if (status == Status.ACTIVO) {     // ¡aquí == es correcto!
    System.out.println("a la venta");
}
```

Tres ganancias inmediatas. `Status.ACTVIO` **no compila**. La comparación
con `==` vuelve a ser segura, porque existe exactamente una instancia de
cada valor. Y el `switch` pasa a ser exhaustivo:

```java title="El compilador exige los casos que faltan" numbered
String etiqueta = switch (status) {
    case ACTIVO -> "A la venta";
    case INACTIVO -> "Fuera de línea";
    case AGOTADO -> "Sin stock";
};
```

Sin `default`. Si alguien agrega `PREVENTA` al enum mañana, este `switch`
deja de compilar, y el compilador señala el lugar exacto donde falta tratar
el caso nuevo. Es un error de compilación que **quieres** tener.

:::key
Cada vez que escribes un `if` comparando texto con una constante, hay un
enum esperando nacer. La señal es clara: si el conjunto de valores es
conocido y no cambia en tiempo de ejecución, es un tipo, no un texto.
:::

:::story ACTVIO
El estado era un texto. `"ACTIVO"`, `"INACTIVO"`, `"AGOTADO"`: acordado en
reunión, escrito en el acta, seguido por todo el mundo.

Hasta el martes en que alguien cargó cuatrocientos productos por planilla y
la columna salió con `"ACTVIO"`.

Nada se rompió. Ninguna excepción, ningún log, ninguna alerta. Los
cuatrocientos productos simplemente dejaron de aparecer en la tienda,
porque el filtro buscaba `"ACTIVO"` y ellos no eran nada.

Tardaron once días en darse cuenta. Quien se dio cuenta fue don Antônio, que
llamó preguntando por qué la marca de auriculares que siempre compraba había
"salido de línea".

En la retrospectiva, Roberto sugirió una validación más en la importación
de la planilla. Marina sugirió otra cosa:

—O dejamos de permitir que la computadora acepte cualquier palabra en un
campo que solo tiene tres valores posibles.
:::

## Enum con datos y comportamiento

Esto es lo que casi nadie enseña: un enum es una clase completa.

```java title="PaymentMethod.java" numbered
public enum PaymentMethod {
    PIX("Pix", 0, 0),
    BOLETO("Boleto", 3, 0),
    TARJETA("Tarjeta", 0, 2.99);

    private final String etiqueta;
    private final int plazoDias;
    private final double tasaPorcentual;

    PaymentMethod(String etiqueta, int plazoDias, double tasa) {
        this.etiqueta = etiqueta;
        this.plazoDias = plazoDias;
        this.tasaPorcentual = tasa;
    }

    public double aplicarTasa(double valor) {
        return valor * (1 + tasaPorcentual / 100);
    }

    public String getEtiqueta() {
        return etiqueta;
    }
}
```

```java
double cobrado = PaymentMethod.TARJETA.aplicarTasa(100);  // 102.99
```

La tabla de tasas que viviría en un `switch` de veinte líneas ahora vive al
lado de cada valor. Agregar un medio de pago es agregar una línea, y el
compilador garantiza que nadie se olvidó de informar la tasa.

:::compare left="Escalera de if" right="Enum con datos"
if (m.equals("PIX"))
  return v;
if (m.equals("BOLETO"))
  return v;
if (m.equals("TARJETA"))
  return v * 1.0299;
---
return m.aplicarTasa(v);
:::

:::trivia
Los enums llegaron en Java 5, en 2004. Antes de eso, el patrón era
`public static final int ACTIVO = 1;`, y eso traía un problema divertido:
cualquier `int` servía. Una función que esperaba un estado aceptaba `42` sin
quejarse. El patrón hasta tenía nombre, *Typesafe Enum Pattern*, y ocupaba
treinta líneas en el libro de Joshua Bloch. El lenguaje incorporó el patrón
entero en una palabra clave.
:::

## `record`: el dato puro

¿Te acuerdas de la clase `Product` inmutable del capítulo 10, con
constructor, getters, `equals`, `hashCode` y `toString`? Son cuarenta
líneas. Ahora es esto:

```java title="ProductResponse.java" numbered
public record ProductResponse(
        Long id,
        String nombre,
        double precio,
        int stock) {
}
```

El compilador genera automáticamente: los atributos `private final`, el
constructor con todos los campos, un método de lectura por campo (`id()`,
`nombre()`, sin el prefijo `get`), `equals` y `hashCode` por contenido, y un
`toString` legible.

```java
var p = new ProductResponse(7L, "Teclado", 349.90, 12);
System.out.println(p.nombre());    // Teclado
System.out.println(p);
// ProductResponse[id=7, nombre=Teclado, precio=349.9, stock=12]
```

:::anatomy title="Lo que el compilador escribe por ti"
lang: java
code: |
  public record ProductResponse(Long id, String nombre) {
      public ProductResponse {
          if (nombre == null) {
              throw new IllegalArgumentException();
          }
      }
  }
notes:
  - { line: 1, text: "Los parámetros del record **son** los atributos: `private final` por definición." }
  - { line: 1, text: "La lectura es `p.nombre()`, sin `get`, y no existe `set`: el record es inmutable." }
  - { line: 2, text: "Constructor **compacto**: solo la validación, sin repetir las asignaciones." }
  - { line: 4, text: "Validar aquí garantiza lo mismo que el capítulo 10: el objeto nunca nace inválido." }
:::

## Cuándo usar record y cuándo usar clase

| Usa `record` | Usa `class` |
|---|---|
| dato que solo transporta valores | objeto con comportamiento y estado que cambia |
| petición y respuesta de una API | entidad de base de datos (JPA necesita mutarla) |
| clave compuesta, coordenada, par | cualquier cosa que necesite heredar |

Tabla: El record es para datos; la clase es para objetos. Un record no puede
extender nada, por construcción.

:::pitfall
El record parece la solución para todo y no sirve como entidad JPA.
Hibernate (capítulo 20) necesita un constructor vacío y setters para seguir
los cambios, y un record no tiene ninguno de los dos. Por eso el proyecto va
a usar una **clase** para `Product` (la entidad) y un **record** para
`ProductRequest` y `ProductResponse` (los DTO del capítulo 24).
:::

## Los dos juntos, como los va a usar el proyecto

```java title="Un recorte del capítulo 24" numbered
public record ProductResponse(
        Long id,
        String nombre,
        double precio,
        Status status,
        PaymentMethod pagoPreferido) {
}
```

El JSON que recibe el cliente va a salir exactamente con esos campos, y el
enum se vuelve texto en la serialización, sin que escribas una línea de
conversión. Es el formato de la respuesta que abrió el capítulo 1.

:::summary
- `enum` es un conjunto cerrado: un error de tipeo no compila y el `switch`
  queda exhaustivo.
- Un enum puede tener atributos, constructor y métodos: la tabla vive al
  lado del valor.
- `record` genera constructor, lectores, `equals`, `hashCode` y `toString`.
- El record es inmutable y no hereda: perfecto para un DTO, inadecuado para
  una entidad JPA.
:::

:::checkpoint
Cambias constantes de texto por enums, escribes un enum con datos y
comportamiento, declaras records y sabes cuándo no usarlos.
:::

:::milestone
El vocabulario del proyecto está completo: `Product` (clase), `Status` y
`PaymentMethod` (enums), `ProductResponse` (record). Falta qué hacer cuando
algo sale mal: el próximo capítulo.
:::

:::exercise level=1
Reemplaza la escalera de notas del capítulo 5 por un `enum Calificacion` con
`EXCELENTE`, `BUENO`, `REGULAR` e `INSUFICIENTE`, y un método estático
`de(double nota)` que devuelva la calificación.

:::answer
```java
public enum Calificacion {
    EXCELENTE, BUENO, REGULAR, INSUFICIENTE;

    public static Calificacion de(double nota) {
        if (nota >= 9) return EXCELENTE;
        if (nota >= 7) return BUENO;
        if (nota >= 5) return REGULAR;
        return INSUFICIENTE;
    }
}
```
La escalera sigue existiendo, pero ahora vive dentro del tipo que produce, y
solo existe en un lugar del sistema.
:::

:::exercise level=2
Escribe `record Money(BigDecimal valor, String moneda)` con validación en el
constructor compacto: el valor no puede ser nulo ni negativo, y la moneda
tiene que tener tres letras.

:::answer
```java
public record Money(BigDecimal valor, String moneda) {
    public Money {
        if (valor == null || valor.signum() < 0) {
            throw new IllegalArgumentException("valor inválido");
        }
        if (moneda == null || moneda.length() != 3) {
            throw new IllegalArgumentException("moneda inválida");
        }
    }
}
```
:::

:::exercise level=3
Agrega al `enum PaymentMethod` un método `plazoEnDiasHabiles()` y descubre
por tu cuenta qué pasa si llamas a `values()`, y para qué sirve eso en una
API.

:::answer
`PaymentMethod.values()` devuelve un array con todos los valores, en el
orden de declaración. En una API eso permite responder
`GET /payment-methods` listando las opciones disponibles sin mantener una
segunda lista en ningún lugar: la fuente de verdad es el propio enum.
:::
