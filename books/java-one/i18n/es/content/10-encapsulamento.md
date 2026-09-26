---
source_hash: cee7d76e600e
title: "Encapsulamiento"
number: 10
part: p2
kicker: "Esconder el atributo no es ceremonia: es lo que impide que el objeto exista en un estado imposible."
goal: >-
  Proteger el estado de un objeto con `private`, exponer lo necesario con
  métodos, y validar en el constructor para que el objeto nunca nazca
  inválido.
---

La clase `Product` del capítulo anterior tiene un problema serio:

```java
teclado.precio = -500;
teclado.stock = -3;
```

Compila, corre y crea un producto con precio negativo. El error no está en
la línea que escribió el disparate: está en la clase, que lo permitió.

## `private`: cerrar la puerta

```java title="Product.java" numbered
public class Product {
    private String nombre;
    private double precio;
    private int stock;

    public Product(String nombre, double precio, int stock) {
        this.nombre = nombre;
        this.precio = precio;
        this.stock = stock;
    }
}
```

Con `private`, la línea `teclado.precio = -500;` deja de compilar:
`precio has private access in Product`. El dato pasó a ser asunto interno de
la clase, y ahora la clase puede garantizar que tenga sentido.

## Validar donde nace el objeto

```java title="Un objeto que se niega a existir mal" numbered
public Product(String nombre, double precio, int stock) {
    if (nombre == null || nombre.isBlank()) {
        throw new IllegalArgumentException("nombre obligatorio");
    }
    if (precio < 0) {
        throw new IllegalArgumentException("precio negativo");
    }
    this.nombre = nombre;
    this.precio = precio;
    this.stock = Math.max(stock, 0);
}
```

`throw` interrumpe la creación y avisa a quien llamó. El capítulo 13 se
ocupa de las excepciones en detalle; aquí basta la idea: **es más barato
rechazar el objeto que arreglarlo después**.

:::key
Si el constructor termina, el objeto es válido. Esa garantía atraviesa el
programa entero: ningún método necesita verificar si el precio es negativo,
porque no existe un producto con precio negativo. Cambiaste mil
verificaciones desparramadas por una, en el lugar correcto.
:::

## Getters y setters, con criterio

```java title="Leer siempre, escribir cuando tiene sentido" numbered
public String getNombre() {
    return nombre;
}

public double getPrecio() {
    return precio;
}

public void reajustar(double porcentaje) {
    if (porcentaje <= -100) {
        throw new IllegalArgumentException("reajuste inválido");
    }
    this.precio = precio * (1 + porcentaje / 100);
}
```

Fíjate en lo que **no** existe: `setPrecio`. En vez de un método que acepta
cualquier número, la clase expone la operación real del negocio: reajustar.
El nombre lleva la regla.

:::pitfall
Generar `get` y `set` para todos los atributos por reflejo convierte la
clase en un formulario sin reglas, y devuelve exactamente el problema que el
`private` resolvió. La pregunta antes de cada `set` es: *¿alguien de afuera
tiene derecho a cambiar esto por su cuenta?* Casi siempre la respuesta es
no.
:::

:::compare left="Setter genérico" right="Operación con nombre"
p.setStock(
    p.getStock() - 1);
---
p.descontarStock(1);
:::

La columna de la derecha puede rechazar el descuento si el stock es cero. La
de la izquierda ya grabó el `-1` antes de que alguien preguntara.

:::story El Black Friday del pasante
El campo era público. Estaba así desde el primer día y nunca le había
molestado a nadie.

La víspera del Black Friday, un pasante recibió la tarea más simple de la
lista: aplicar un 30% de descuento a una categoría. Escribió un bucle que
recorría los productos y hacía `p.precio = p.precio * 0.7`.

Funcionó perfectamente. Corrió tres veces, porque el script se colgó a la
mitad y él lo reejecutó por precaución.

A las 00:07, la tienda vendía monitores a R$ 411,00. A las 00:09, a
R$ 287,70. A las 00:11, a R$ 201,39.

Marina apagó el servicio a las 00:14 y, en la retrospectiva de la semana,
escribió en la pizarra una frase que se volvió regla del equipo:

> "Si un atributo puede ser cambiado por cualquier línea del sistema, tarde
> o temprano lo será, tres veces seguidas."

El pasante no se equivocó. El pasante hizo exactamente lo que la clase
permitía.
:::

## Los cuatro niveles de acceso

| Modificador | Ve |
|---|---|
| `private` | solo la propia clase |
| (ninguno) | clases del mismo paquete |
| `protected` | mismo paquete + subclases |
| `public` | todo el mundo |

Tabla: Del más cerrado al más abierto. La regla práctica: empieza en
`private` y abre solo cuando duela.

El nivel sin modificador —llamado *package-private*— es el más olvidado y
uno de los más útiles: permite que las clases del mismo paquete conversen
sin exponer nada al resto del mundo.

:::trivia
Java es uno de los pocos lenguajes en que el nivel por defecto no es
`public` ni `private`, sino "del paquete". La decisión viene de la idea de
que un paquete es una unidad de confianza: las clases vecinas colaboran. En
la práctica, casi nadie lo usa a propósito: la mayoría de los atributos sin
modificador están así por olvido, y por eso el capítulo 9 mostró `Product`
de esa forma.
:::

## Inmutabilidad: la versión radical

¿Y si nada pudiera cambiar después de creado?

```java title="Product inmutable" numbered
public class Product {
    private final String nombre;
    private final double precio;

    public Product(String nombre, double precio) {
        this.nombre = nombre;
        this.precio = precio;
    }

    public Product conPrecio(double nuevoPrecio) {
        return new Product(nombre, nuevoPrecio);
    }
}
```

`final` en el atributo significa "asignado una vez, en el constructor, y
nunca más". Para cambiar el precio, creas otro producto. Parece un
desperdicio y es el patrón preferido en código moderno: un objeto inmutable
no tiene estado inconsistente, no necesita copia defensiva y es seguro entre
hilos, que es exactamente la situación de una API atendiendo cien peticiones
al mismo tiempo.

:::tip
Esta clase entera, con validación, `equals`, `hashCode` y `toString`, se
vuelve **una línea** en el capítulo 12. Pero esa línea solo tiene sentido
para quien vio las quince.
:::

## Dónde va a aparecer esto en el proyecto

La entidad `Product` del capítulo 20 va a necesitar getters, porque JPA y
Jackson leen los datos a través de ellos. Lo que cambia es la intención:
los getters existen para las herramientas y para la lectura; los cambios de
estado siguen pasando por métodos con nombre de regla.

:::tree title="Dónde estamos ahora"
java-one/
  Product.java    # private + constructor que valida
  Category.java
  Tienda.java     # main
:::

:::summary
- `private` cierra el atributo; el constructor garantiza que el objeto nazca
  válido.
- Getter para leer; una operación con nombre de regla en vez de un setter
  genérico.
- Cuatro niveles de acceso: empieza en `private` y abre cuando duela.
- `final` en los atributos crea un objeto inmutable, el patrón preferido en
  una API.
:::

:::checkpoint
Proteges atributos, validas en el constructor, eliges entre setter y
operación con nombre, y sabes explicar por qué la inmutabilidad ayuda en un
servidor.
:::

:::milestone
`Product` ahora se defiende: un precio negativo y un nombre vacío no pasan
del constructor. Esa validación va a migrar a anotaciones en el capítulo 25,
pero la regla sigue siendo la misma.
:::

:::exercise level=1
Haz privados todos los atributos de `Category` y escribe solo los getters.
Después intenta cambiar `nombre` desde afuera y lee el mensaje del
compilador.

:::answer
`nombre has private access in Category`. El error ocurre al **compilar**, no
en producción: el intercambio que este libro defiende desde el capítulo 3.
:::

:::exercise level=2
Escribe `descontarStock(int cantidad)` en `Product`. Debe rechazar una
cantidad negativa y rechazar un descuento mayor que el stock disponible.

:::answer
```java
public void descontarStock(int cantidad) {
    if (cantidad <= 0) {
        throw new IllegalArgumentException("cantidad inválida");
    }
    if (cantidad > stock) {
        throw new IllegalStateException("stock insuficiente");
    }
    this.stock -= cantidad;
}
```
Dos tipos distintos de excepción, a propósito: `IllegalArgumentException`
es culpa de quien llamó; `IllegalStateException` es una situación del
objeto. En el capítulo 26 esa distinción se vuelve la diferencia entre un
`400` y un `409` en la respuesta HTTP.
:::

:::exercise level=3
Reescribe `Product` como una clase inmutable y ajusta `descontarStock` para
que devuelva un producto nuevo. Después enumera una ventaja y una desventaja
de la versión inmutable en una API.

:::answer
Ventaja: ningún método puede dejar el objeto a medias, y dos hilos pueden
leerlo sin bloqueo. Desventaja: cada cambio crea un objeto, lo que en bucles
muy grandes genera presión de memoria, y, en el caso de JPA (capítulo 20),
la herramienta *necesita* un objeto mutable para seguir los cambios. Saber
dónde no cabe la inmutabilidad es parte de saber usarla.
:::
