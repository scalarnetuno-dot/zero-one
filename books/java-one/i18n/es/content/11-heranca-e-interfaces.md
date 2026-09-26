---
source_hash: 00b716fd79d2
title: "Herencia e interfaces"
number: 11
part: p2
kicker: "La herencia es un parentesco que no puedes deshacer. La interfaz es un contrato que puedes firmar con quien quieras."
goal: >-
  Escribir una jerarquía con `extends`, declarar e implementar una
  `interface`, usar el polimorfismo y decidir entre herencia y composición.
---

Dos clases parecidas piden alguna forma de reutilización. Java ofrece dos,
y elegir mal es el error de diseño más caro que existe, porque solo aparece
dos años después, cuando cambia el requisito.

## Herencia: `extends`

```java title="Una familia de productos" numbered
public class Product {
    protected String nombre;
    protected double precio;

    public Product(String nombre, double precio) {
        this.nombre = nombre;
        this.precio = precio;
    }

    public double precioFinal() {
        return precio;
    }
}

public class DigitalProduct extends Product {
    public DigitalProduct(String nombre, double precio) {
        super(nombre, precio);
    }

    @Override
    public double precioFinal() {
        return precio * 0.9;   // sin envío, 10% más barato
    }
}
```

:::anatomy title="Las cuatro señales de la herencia"
lang: java
code: |
  public class DigitalProduct extends Product {
      public DigitalProduct(String n, double p) {
          super(n, p);
      }

      @Override
      public double precioFinal() {
          return precio * 0.9;
      }
  }
notes:
  - { line: 1, text: "`extends` crea el parentesco: DigitalProduct **es un** Product." }
  - { line: 3, text: "`super(...)` llama al constructor del padre. Tiene que ser la primera línea." }
  - { line: 6, text: "`@Override` avisa al compilador: estoy reemplazando un método heredado." }
  - { line: 8, text: "`precio` es accesible porque el padre lo declaró `protected`, no `private`." }
:::

## Polimorfismo: la misma orden, respuestas distintas

```java title="La lista no sabe cuál es cuál, y no necesita saberlo" numbered
List<Product> catalogo = List.of(
        new Product("Teclado", 100),
        new DigitalProduct("E-book", 100));

for (Product p : catalogo) {
    System.out.println(p.precioFinal());
}
```

```text title="Salida"
100.0
90.0
```

La variable es de tipo `Product`, pero el método que corre es el del objeto
real. Eso se llama **polimorfismo** y es la razón de ser de la herencia:
escribes el bucle una vez y funciona para tipos que todavía no existen.

:::trivia
Esa elección "en tiempo de ejecución" tiene nombre: *dynamic dispatch*. En
Java es lo estándar para todo método de instancia, y cuesta una consulta a
una tabla de punteros por llamada. La JVM lo optimiza de forma agresiva:
cuando se da cuenta de que ahí solo aparece un tipo, reemplaza la llamada
por el código directo. Por eso Java "calienta": las primeras mil ejecuciones
son más lentas que las siguientes.
:::

:::story La herencia que nadie pidió
En su segundo mes, Carlos heredó el sistema viejo de stock.

Técnicamente no era una herencia. Era una maldición familiar.

El autor original había dejado la empresa en 2019 y había dejado una
jerarquía de seis niveles. La quinta clase se llamaba
`ItemFisicoAlmacenablePerecederoImportado`. La sexta se llamaba
`ItemLegado`, lo que ya era un buen aviso.

La última clase existía porque, en algún momento, alguien necesitó un ítem
importado que **no** fuera perecedero, y la jerarquía no lo permitía. La
solución fue crear un hijo que sobrescribía el método del abuelo para
deshacer lo que hacía el padre.

—¿Por qué nadie reescribió esto? —preguntó Carlos.

—Porque funciona —dijo Marina—. Y porque nadie sabe cuál de las seis clases
usa finanzas.
:::

:::art caption="La herencia profunda es un parentesco que no puedes deshacer."
src="heranca-profunda-e-um-parentesco-que-voce-nao-pode-desfazer.png"
Charge editorial minimalista: desenvolvedor jovem recebendo das mãos de outro
desenvolvedor uma caixa de papelão enorme e pesada, rotulada "SISTEMA
LEGADO". Da caixa saltam fios emaranhados, papéis amarelados e um monitor de
tubo antigo. Quem entrega já está de mochila nas costas, indo embora. Quem
recebe tem os joelhos dobrando sob o peso. Fundo branco, poucos elementos,
humor visual seco, estética de revista de tecnologia, sem estética infantil.
:::

## Interfaz: el contrato sin implementación

```java title="Un contrato" numbered
public interface Discountable {
    double aplicarDescuento(double porcentaje);
}

public class Product implements Discountable {
    @Override
    public double aplicarDescuento(double porcentaje) {
        return precio * (1 - porcentaje / 100);
    }
}
```

La interfaz dice **qué** tiene que existir, no **cómo**. Una clase puede
implementar todas las interfaces que quiera, y solo puede extender una
clase. Esa asimetría es deliberada: los contratos se acumulan, el parentesco
no.

| | Herencia (`extends`) | Interfaz (`implements`) |
|---|---|---|
| Relación | "es un" | "sabe hacer" |
| Cantidad | una clase padre | las que quieras |
| ¿Trae código? | sí, atributos y métodos | solo firmas (y `default`) |
| Acoplamiento | alto | bajo |

Tabla: La elección entre las dos es la decisión de diseño con más
consecuencias de la Parte 2.

## Por qué la interfaz es la base de Spring

Guarda esta idea, porque toda la Parte 3 se apoya en ella: si tu código
depende de una **interfaz**, alguien puede entregar cualquier implementación
en tiempo de ejecución, incluso una falsa, en la prueba.

```java title="Depende del contrato" numbered
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

`ProductRepository` va a ser una interfaz. En producción, Spring entrega una
implementación que habla con PostgreSQL (capítulo 21). En la prueba,
entregas una que guarda todo en un `Map` (capítulo 35). `ProductService` no
cambia una línea, y esa es la definición práctica de *bajo acoplamiento*.

## Métodos `default`: una interfaz con implementación

```java title="Java 8 cambió la regla" numbered
public interface Discountable {
    double getPrecio();

    default double conDescuento(double porcentaje) {
        return getPrecio() * (1 - porcentaje / 100);
    }
}
```

Un método `default` trae cuerpo dentro de la interfaz. Existe para permitir
que las bibliotecas crezcan sin romper a quien ya las implementaba: cuando
Java 8 agregó `forEach` a la interfaz `Iterable`, mil millones de líneas de
código existente siguieron compilando.

## Clase abstracta: a mitad de camino

```java title="No puede existir sola" numbered
public abstract class Product {
    protected double precio;

    public abstract double precioFinal();  // el hijo decide

    public String etiqueta() {             // todos lo heredan
        return "R$ " + precioFinal();
    }
}
```

`new Product(...)` no compila: una clase abstracta es un esqueleto. Úsala
cuando los hijos comparten **estado y comportamiento** y quieres obligar a
cada uno a decidir un detalle.

:::pitfall
La tentación de crear jerarquías profundas es grande y el arrepentimiento es
seguro. Si te encuentras escribiendo `class A extends B extends C extends
D`, cada cambio en `D` pasa a asustar a cuatro clases. La regla práctica del
mercado es directa: **prefiere la composición a la herencia.**
:::

## Composición: cuando "tiene un" le gana a "es un"

:::compare left="Herencia forzada" right="Composición"
class ProductWithTax
        extends Product {
  double precioFinal() {
    return precio * 1.08;
  }
}
---
class Product {
  private TaxPolicy tax;

  double precioFinal() {
    return tax.apply(precio);
  }
}
:::

A la derecha, la política de impuestos es un objeto que cambias en tiempo
de ejecución, incluso por una distinta para cada estado, o por una falsa en
la prueba. A la izquierda, necesitarías una subclase nueva para cada regla,
y ninguna podría combinarse con otra.

:::key
Pregunta: *"¿esto es un tipo distinto, o es el mismo tipo con una pieza
distinta?"* Un tipo distinto pide herencia (rara vez). Una pieza distinta
pide composición (casi siempre).
:::

## `final`: prohibir la herencia

```java
public final class Money { }   // nadie la extiende
```

`final` en una clase impide las subclases; en un método, impide la
sobrescritura. Es una decisión de diseño legítima: `String` es `final` en
Java justamente para que nadie pueda crear un texto que se comporte de
forma extraña.

:::summary
- `extends` crea "es un"; `implements` crea "sabe hacer".
- El polimorfismo elige el método por el objeto real, no por la variable.
- Una clase extiende una; implementa las que quiera.
- Depender de una interfaz es lo que permite cambiar la implementación, y
  lo que explota Spring.
- Prefiere la composición a la herencia.
:::

:::checkpoint
Escribes una subclase con `super` y `@Override`, declaras e implementas
interfaces, explicas el polimorfismo con un ejemplo y sabes justificar la
composición en vez de la herencia.
:::

:::milestone
El proyecto tiene la forma que va a recibir a Spring: `ProductService`
depende de la interfaz `ProductRepository`, no de una clase concreta. Solo
falta alguien que entregue la implementación, y eso es lo que presenta el
capítulo 15.
:::

:::exercise level=1
Crea `abstract class Payment` con `abstract double tasa()` y dos
subclases: `PixPayment` (tasa 0) y `CardPayment` (tasa 2,99%). Imprime la
tasa de las dos a través de una `List<Payment>`.

:::answer
```java
public abstract class Payment {
    public abstract double tasa();
}

public class PixPayment extends Payment {
    public double tasa() { return 0; }
}

public class CardPayment extends Payment {
    public double tasa() { return 0.0299; }
}
```
:::

:::exercise level=2
Convierte `Payment` en una interfaz y explica qué perdiste y qué ganaste con
el cambio.

:::answer
Perdiste la posibilidad de guardar estado común (un atributo `descripcion`,
por ejemplo) y de tener código compartido sin `default`. Ganaste la
libertad de que una clase implemente `Payment` **y** cualquier otra
interfaz, y la posibilidad de que la implementación sea una clase que ya
hereda de otra cosa.
:::

:::exercise level=3
Reescribe el ejercicio anterior con composición: una clase `Payment`
concreta que recibe una `FeePolicy` en el constructor. Después responde:
¿cuál de las tres versiones llevarías a una API que gana un medio de pago
nuevo por mes?

:::answer
La tercera. Un medio de pago nuevo pasa a ser un objeto de política, creado
en tiempo de ejecución; puede incluso venir de una tabla de la base de
datos, sin recompilar nada. La herencia exigiría una clase nueva y un nuevo
*deploy* cada mes.
:::
