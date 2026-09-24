---
source_hash: 00b716fd79d2
title: "Inheritance and interfaces"
number: 11
part: p2
kicker: "Inheritance is a kinship you cannot undo. An interface is a contract you can sign with whoever you want."
goal: >-
  Write a hierarchy with `extends`, declare and implement an `interface`,
  use polymorphism and decide between inheritance and composition.
---

Two similar classes call for some form of reuse. Java offers two, and
choosing wrong is the most expensive design mistake there is — because it
only shows up two years later, when the requirement changes.

## Inheritance: `extends`

```java title="A family of products" numbered
public class Product {
    protected String name;
    protected double price;

    public Product(String name, double price) {
        this.name = name;
        this.price = price;
    }

    public double finalPrice() {
        return price;
    }
}

public class DigitalProduct extends Product {
    public DigitalProduct(String name, double price) {
        super(name, price);
    }

    @Override
    public double finalPrice() {
        return price * 0.9;   // no shipping, 10% cheaper
    }
}
```

:::anatomy title="The four signs of inheritance"
lang: java
code: |
  public class DigitalProduct extends Product {
      public DigitalProduct(String n, double p) {
          super(n, p);
      }

      @Override
      public double finalPrice() {
          return price * 0.9;
      }
  }
notes:
  - { line: 1, text: "`extends` creates the kinship: DigitalProduct **is a** Product." }
  - { line: 3, text: "`super(...)` calls the parent's constructor. It has to be the first line." }
  - { line: 6, text: "`@Override` warns the compiler: I am replacing an inherited method." }
  - { line: 8, text: "`price` is accessible because the parent declared it `protected`, not `private`." }
:::

## Polymorphism: the same command, different answers

```java title="The list doesn't know which is which — and doesn't need to" numbered
List<Product> catalog = List.of(
        new Product("Keyboard", 100),
        new DigitalProduct("E-book", 100));

for (Product p : catalog) {
    System.out.println(p.finalPrice());
}
```

```text title="Output"
100.0
90.0
```

The variable is of type `Product`, but the method that runs is the real
object's. This is called **polymorphism** and it is the reason inheritance
exists: you write the loop once and it works for types that do not exist
yet.

:::trivia
That "at run time" choice has a name: *dynamic dispatch*. In Java it is
the default for every instance method — and it costs a lookup in a pointer
table per call. The JVM optimizes this aggressively: when it notices that
only one type shows up there, it replaces the call with the code directly.
That is why Java "warms up": the first thousand executions are slower than
the following ones.
:::

:::story The inheritance nobody asked for
In his second month, Carlos inherited the old stock system.

Technically, it was not inheritance. It was a family curse.

The original author had left the company in 2019 and left behind a
six-level hierarchy. The fifth class was called
`PhysicalStockablePerishableImportedItem`. The sixth was called
`LegacyItem`, which was already a good warning.

The last class existed because, at some point, someone needed an imported
item that was **not** perishable — and the hierarchy did not allow it. The
solution was to create a child that overrode the grandparent's method to
undo what the parent did.

"Why did nobody rewrite this?" asked Carlos.

"Because it works," said Marina. "And because nobody knows which of the
six classes finance uses."
:::

:::art caption="Deep inheritance is a kinship you cannot undo."
src="heranca-profunda-e-um-parentesco-que-voce-nao-pode-desfazer.png"
Charge editorial minimalista: desenvolvedor jovem recebendo das mãos de outro
desenvolvedor uma caixa de papelão enorme e pesada, rotulada "SISTEMA
LEGADO". Da caixa saltam fios emaranhados, papéis amarelados e um monitor de
tubo antigo. Quem entrega já está de mochila nas costas, indo embora. Quem
recebe tem os joelhos dobrando sob o peso. Fundo branco, poucos elementos,
humor visual seco, estética de revista de tecnologia, sem estética infantil.
:::

## Interface: the contract without implementation

```java title="A contract" numbered
public interface Discountable {
    double applyDiscount(double percent);
}

public class Product implements Discountable {
    @Override
    public double applyDiscount(double percent) {
        return price * (1 - percent / 100);
    }
}
```

The interface says **what** has to exist, not **how**. A class can
implement as many interfaces as it wants — and can extend only one class.
That asymmetry is deliberate: contracts accumulate, kinship does not.

| | Inheritance (`extends`) | Interface (`implements`) |
|---|---|---|
| Relationship | "is a" | "knows how to" |
| How many | one parent class | as many as you want |
| Brings code? | yes, attributes and methods | only signatures (and `default`) |
| Coupling | high | low |

Table: The choice between the two is the most consequential design
decision of Part 2.

## Why interfaces are the foundation of Spring

Keep this idea, because all of Part 3 rests on it: if your code depends on
an **interface**, someone can hand over any implementation at run time —
including a fake one, in a test.

```java title="Depend on the contract" numbered
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

`ProductRepository` is going to be an interface. In production, Spring
hands over an implementation that talks to PostgreSQL (chapter 21). In a
test, you hand over one that keeps everything in a `Map` (chapter 35).
`ProductService` does not change a single line — and that is the practical
definition of *loose coupling*.

## `default` methods: an interface with an implementation

```java title="Java 8 changed the rule" numbered
public interface Discountable {
    double getPrice();

    default double withDiscount(double percent) {
        return getPrice() * (1 - percent / 100);
    }
}
```

A `default` method brings a body inside the interface. It exists so that
libraries can grow without breaking whoever already implemented them — when
Java 8 added `forEach` to the `Iterable` interface, a billion lines of
existing code kept compiling.

## Abstract class: halfway there

```java title="It cannot exist on its own" numbered
public abstract class Product {
    protected double price;

    public abstract double finalPrice();  // the child decides

    public String label() {               // everyone inherits
        return "R$ " + finalPrice();
    }
}
```

`new Product(...)` does not compile: an abstract class is a skeleton. Use it
when the children share **state and behavior** and you want to force each
one to decide a detail.

:::pitfall
The temptation to create deep hierarchies is great and the regret is
certain. If you find yourself writing `class A extends B extends C extends
D`, every change to `D` starts to scare four classes. The industry's
practical rule is blunt: **prefer composition over inheritance.**
:::

## Composition: when "has a" beats "is a"

:::compare left="Forced inheritance" right="Composition"
class ProductWithTax
        extends Product {
  double finalPrice() {
    return price * 1.08;
  }
}
---
class Product {
  private TaxPolicy tax;

  double finalPrice() {
    return tax.apply(price);
  }
}
:::

On the right, the tax policy is an object you swap at run time — even for
a different one per state, or for a fake one in a test. On the left, you
would need a new subclass for each rule, and none of them could combine
with another.

:::key
Ask: *"is this a different type, or the same type with a different
part?"* A different type calls for inheritance (rarely). A different part
calls for composition (almost always).
:::

## `final`: forbidding inheritance

```java
public final class Money { }   // nobody extends it
```

`final` on a class prevents subclasses; on a method, it prevents
overriding. It is a legitimate design decision: `String` is `final` in Java
precisely so that nobody can create a text that behaves strangely.

:::summary
- `extends` creates "is a"; `implements` creates "knows how to".
- Polymorphism chooses the method by the real object, not by the variable.
- A class extends one; it implements as many as it wants.
- Depending on an interface is what allows swapping the implementation —
  and what Spring exploits.
- Prefer composition over inheritance.
:::

:::checkpoint
You write a subclass with `super` and `@Override`, declare and implement
interfaces, explain polymorphism with an example and can justify
composition instead of inheritance.
:::

:::milestone
The project has the shape that will receive Spring: `ProductService`
depends on the `ProductRepository` interface, not on a concrete class. All
that is missing is someone to hand over the implementation — and that is
what chapter 15 introduces.
:::

:::exercise level=1
Create `abstract class Payment` with `abstract double fee()` and two
subclasses: `PixPayment` (fee 0) and `CardPayment` (fee 2.99%). Print the
fee of both through a `List<Payment>`.

:::answer
```java
public abstract class Payment {
    public abstract double fee();
}

public class PixPayment extends Payment {
    public double fee() { return 0; }
}

public class CardPayment extends Payment {
    public double fee() { return 0.0299; }
}
```
:::

:::exercise level=2
Turn `Payment` into an interface and explain what you lost and what you
gained in the switch.

:::answer
You lost the ability to keep common state (a `description` attribute, for
example) and to have shared code without `default`. You gained the freedom
for a class to implement `Payment` **and** any other interface — and the
possibility of the implementation being a class that already inherits from
something else.
:::

:::exercise level=3
Rewrite the previous exercise with composition: a concrete `Payment` class
that receives a `FeePolicy` in its constructor. Then answer: which of the
three versions would you take to an API that gains a new payment method
every month?

:::answer
The third. A new payment method becomes a policy object, created at run
time — it can even come from a database table, without recompiling
anything. Inheritance would require a new class and a new *deploy* every
month.
:::
