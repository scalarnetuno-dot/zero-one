---
source_hash: dc9ef9f22525
title: "Orientación a objetos"
number: 9
part: p2
kicker: "Hasta aquí el código tenía verbos sueltos. Ahora gana sustantivos."
epigraph: "Yo inventé el término orientado a objetos, y puedo decir que no tenía C++ en mente."
epigraph_by: "Alan Kay, creador de Smalltalk"
goal: >-
  Escribir una clase con atributos, constructor y métodos, crear objetos a
  partir de ella y explicar la diferencia entre clase e instancia.
---

Un programa crece y la pregunta cambia. Deja de ser "qué cuenta hago" y pasa
a ser "de quién es esta información". Una clase responde a la segunda: junta
los datos que andan juntos y los métodos que saben qué hacer con ellos.

## Del dato suelto al objeto

:::compare left="Antes: cuatro variables paralelas" right="Después: un objeto"
String nombre = "Teclado";
double precio = 349.90;
int stock = 12;
boolean activo = true;
---
Product p = new Product(
    "Teclado", 349.90, 12);
p.getPrecio();
p.puedeVender();
:::

La versión de la izquierda funciona con un producto. Con dos, duplicas las
cuatro variables; con mil, necesitas cuatro arrays paralelos y rezar para
que los índices no se desalineen. La de la derecha escala sin esfuerzo: para
eso existe la clase.

## La primera clase

```java title="Product.java" numbered
public class Product {
    String nombre;
    double precio;
    int stock;

    Product(String nombre, double precio, int stock) {
        this.nombre = nombre;
        this.precio = precio;
        this.stock = stock;
    }

    boolean puedeVender() {
        return stock > 0;
    }

    double totalEnStock() {
        return precio * stock;
    }
}
```

:::anatomy title="Las cuatro partes de una clase"
lang: java
code: |
  public class Product {
      String nombre;

      Product(String nombre) {
          this.nombre = nombre;
      }

      boolean puedeVender() {
          return stock > 0;
      }
  }
notes:
  - { line: 1, text: "La **clase** es el plano: describe lo que todo producto tiene y hace." }
  - { line: 2, text: "**Atributo** (o campo): el dato que carga cada objeto, un valor por objeto." }
  - { line: 4, text: "**Constructor**: mismo nombre que la clase, sin tipo de retorno. Corre una vez, al nacer." }
  - { line: 5, text: "`this.nombre` es el atributo; `nombre` solo es el parámetro. `this` deshace la ambigüedad." }
  - { line: 8, text: "**Método de instancia**: sin `static`, ve los atributos del objeto." }
:::

## Clase e instancia no son lo mismo

```java title="Un plano, tres casas" numbered
Product teclado = new Product("Teclado", 349.90, 12);
Product mouse   = new Product("Mouse", 89.90, 0);

System.out.println(teclado.puedeVender());   // true
System.out.println(mouse.puedeVender());     // false
```

La clase es una; los objetos son muchos. Cada `new` reserva un espacio nuevo
en memoria con una copia de los atributos, y por eso `teclado.stock` y
`mouse.stock` son valores independientes.

:::diagram type="blocks" caption="Una clase, dos objetos: la misma estructura, valores propios."
flow: false
rows:
  - [{ text: "class Product", note: "nombre · precio · stock · puedeVender()" }]
  - [{ text: "teclado", note: "Teclado · 349.90 · 12" }, { text: "mouse", note: "Mouse · 89.90 · 0" }]
:::

:::story Los cuatro arrays paralelos
Antes de que existiera la clase `Product`, existían cuatro arrays.

`nombres`, `precios`, `stocks` y `activos`. Todo funcionaba mientras la
posición 3 de uno correspondiera a la posición 3 de los otros tres.

El martes, Cláudia pidió quitar un producto descontinuado. Carlos lo quitó
del array de nombres y se olvidó de los otros tres.

Esa tarde, la tienda empezó a vender un teclado con el precio de un cable
HDMI.

Don Antônio compró cuatro.
:::

## `static`, por fin explicado

Ahora la palabra del capítulo 2 tiene sentido. Un miembro `static` pertenece
a la **clase**; un miembro sin `static` pertenece al **objeto**.

```java title="Contador de productos creados" numbered
public class Product {
    static int creados = 0;     // uno solo, compartido
    String nombre;              // uno por objeto

    Product(String nombre) {
        this.nombre = nombre;
        creados++;
    }
}
```

```java
new Product("Teclado");
new Product("Mouse");
System.out.println(Product.creados);   // 2, accedido por la clase
```

Y por eso `main` es `static`: cuando el programa empieza, todavía no existe
ningún objeto sobre el cual llamar a un método.

:::pitfall
Un método `static` no puede acceder a un atributo de instancia: no hay
instancia. El mensaje es `non-static variable nombre cannot be referenced
from a static context`, y confunde a todo el mundo la primera semana. La
traducción es: "pediste el nombre de un producto sin decir de qué
producto".
:::

## `toString`: el objeto presentándose

```java title="Sin toString"
System.out.println(teclado);
// Product@2f92e0f4
```

Esa basura es el nombre de la clase y la dirección en memoria. Sobrescribe
`toString` y el objeto aprende a describirse:

```java title="Product.java (fragmento)" numbered
@Override
public String toString() {
    return nombre + " (R$ " + precio + ", " + stock + " un)";
}
```

```text title="Salida"
Teclado (R$ 349.9, 12 un)
```

`@Override` es una **anotación**: un aviso al compilador de que estás
reemplazando un método que ya existe. Si te equivocas en el nombre
(`toStrring`), el compilador se queja en vez de dejar el método huérfano.
Guarda la idea de anotación: a partir del capítulo 17 se vuelve la forma
principal de conversar con Spring.

:::history
Todo objeto en Java hereda de una clase llamada `Object`, que ofrece
`toString`, `equals` y `hashCode`. Esa decisión es de 1995 y tiene un costo:
hasta los tipos más simples arrastran tres métodos que casi nunca hacen lo
correcto por defecto. Para corregirlo, Java 16 trajo `record`, que ves en el
capítulo 12, y que genera los tres gratis, correctamente.
:::

## `equals` y `hashCode`: la lección del capítulo 4, ahora de tu lado

¿Dos productos con el mismo nombre y el mismo precio son el mismo producto?
El `==` dice que no, porque son dos objetos. Si quieres que sean iguales,
tienes que decir cómo:

```java title="Igualdad por contenido" numbered
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof Product otro)) return false;
    return nombre.equals(otro.nombre) && precio == otro.precio;
}

@Override
public int hashCode() {
    return Objects.hash(nombre, precio);
}
```

La regla que existe hace treinta años: **si sobrescribes `equals`,
sobrescribe `hashCode`**. `HashMap` y `HashSet` usan el segundo para
encontrar el objeto antes de compararlo con el primero; uno sin el otro
produce el bug más difícil de explicar: un ítem que acabas de guardar en el
`Set` y que el `Set` dice no contener.

:::tip
Nadie escribe estos dos métodos a mano en 2026. El IDE los genera, y el
`record` del capítulo 12 los hace innecesarios. Lo que necesitas es
reconocer el par y saber por qué existe.
:::

:::term Clase
La descripción de un tipo: qué datos carga y qué operaciones acepta.
:::

:::term Objeto (o instancia)
Un ejemplar concreto de una clase, con sus propios valores, creado con
`new`.
:::

:::summary
- Una clase junta los datos que andan juntos y los métodos que los operan.
- El constructor corre una vez, en el `new`, y `this` distingue el atributo
  del parámetro.
- `static` pertenece a la clase; sin `static`, al objeto.
- `toString` hace que el objeto se describa; `equals` y `hashCode` van en
  par.
:::

:::checkpoint
Escribes una clase con atributos, constructor y métodos, creas objetos,
explicas `static` y sabes por qué `equals` y `hashCode` vienen juntos.
:::

:::milestone
Nació la clase `Product`, el corazón del proyecto. Sus atributos son los
mismos que se van a volver columnas de tabla en el capítulo 19 y campos JSON
en el capítulo 24.
:::

:::exercise level=1
Escribe la clase `Category` con `nombre` y `descripcion`, un constructor y
`toString`. Crea dos categorías e imprímelas.

:::answer
```java
public class Category {
    String nombre;
    String descripcion;

    Category(String nombre, String descripcion) {
        this.nombre = nombre;
        this.descripcion = descripcion;
    }

    @Override
    public String toString() {
        return nombre + " — " + descripcion;
    }
}
```
:::

:::exercise level=2
Agrega a `Product` un método `aplicarDescuento(double porcentaje)` que cambie
el precio del propio objeto y devuelva `void`. Después escribe
`conDescuento(double porcentaje)` que devuelva un **nuevo** `Product` sin
cambiar el original. ¿Cuál de las dos versiones preferirías en una API?

:::answer
La segunda. Un método que cambia el objeto por dentro (*mutación*) obliga a
quien llama a recordar que el valor anterior se perdió; el que devuelve un
objeto nuevo puede usarse en cualquier orden y es seguro en código
concurrente. El capítulo 12 lleva esa idea al límite con `record`, que es
inmutable por construcción.
:::

:::exercise level=3
Crea una `List<Product>` con cuatro productos y calcula el valor total del
stock sumando el `totalEnStock()` de cada uno.

:::answer
```java
double total = 0;
for (Product p : productos) {
    total += p.totalEnStock();
}
```
En el capítulo 14 esto se vuelve
`productos.stream().mapToDouble(Product::totalEnStock).sum()`. Guarda las
dos versiones una al lado de la otra: la segunda solo parece magia para
quien no escribió la primera.
:::
