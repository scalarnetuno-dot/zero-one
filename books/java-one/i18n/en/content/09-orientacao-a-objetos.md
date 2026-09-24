---
source_hash: dc9ef9f22525
title: "Object orientation"
number: 9
part: p2
kicker: "Until now the code had loose verbs. Now it gets nouns."
epigraph: "I made up the term object-oriented, and I can tell you I did not have C++ in mind."
epigraph_by: "Alan Kay, creator of Smalltalk"
goal: >-
  Write a class with attributes, a constructor and methods, create objects
  from it and explain the difference between a class and an instance.
---

A program grows and the question changes. It stops being "what calculation
do I do" and becomes "whose information is this". A class answers the
second one: it brings together the data that travel together and the
methods that know what to do with them.

## From loose data to an object

:::compare left="Before: four parallel variables" right="After: one object"
String name = "Keyboard";
double price = 349.90;
int stock = 12;
boolean active = true;
---
Product p = new Product(
    "Keyboard", 349.90, 12);
p.getPrice();
p.canSell();
:::

The version on the left works for one product. With two, you duplicate the
four variables; with a thousand, you need four parallel arrays and a prayer
that the indexes don't get out of line. The one on the right scales
effortlessly — that is what a class is for.

## The first class

```java title="Product.java" numbered
public class Product {
    String name;
    double price;
    int stock;

    Product(String name, double price, int stock) {
        this.name = name;
        this.price = price;
        this.stock = stock;
    }

    boolean canSell() {
        return stock > 0;
    }

    double totalInStock() {
        return price * stock;
    }
}
```

:::anatomy title="The four parts of a class"
lang: java
code: |
  public class Product {
      String name;

      Product(String name) {
          this.name = name;
      }

      boolean canSell() {
          return stock > 0;
      }
  }
notes:
  - { line: 1, text: "The **class** is the blueprint: it describes what every product has and does." }
  - { line: 2, text: "**Attribute** (or field): the data each object carries, one value per object." }
  - { line: 4, text: "**Constructor**: same name as the class, no return type. Runs once, at birth." }
  - { line: 5, text: "`this.name` is the attribute; `name` alone is the parameter. `this` removes the ambiguity." }
  - { line: 8, text: "**Instance method**: without `static`, it sees the object's attributes." }
:::

## Class and instance are not the same thing

```java title="One blueprint, three houses" numbered
Product keyboard = new Product("Keyboard", 349.90, 12);
Product mouse    = new Product("Mouse", 89.90, 0);

System.out.println(keyboard.canSell());   // true
System.out.println(mouse.canSell());      // false
```

The class is one; the objects are many. Each `new` reserves a new space in
memory with a copy of the attributes — and that is why `keyboard.stock` and
`mouse.stock` are independent values.

:::diagram type="blocks" caption="One class, two objects: the same structure, their own values."
flow: false
rows:
  - [{ text: "class Product", note: "name · price · stock · canSell()" }]
  - [{ text: "keyboard", note: "Keyboard · 349.90 · 12" }, { text: "mouse", note: "Mouse · 89.90 · 0" }]
:::

:::story The four parallel arrays
Before the `Product` class existed, there were four arrays.

`names`, `prices`, `stocks` and `actives`. Everything worked as long as
position 3 of one matched position 3 of the other three.

On Tuesday, Cláudia asked to remove a discontinued product. Carlos removed
it from the names array and forgot about the other three.

That afternoon, the store started selling a keyboard at the price of an
HDMI cable.

Mr. Antônio bought four.
:::

## `static`, finally explained

Now the word from chapter 2 makes sense. A `static` member belongs to the
**class**; a member without `static` belongs to the **object**.

```java title="Counter of created products" numbered
public class Product {
    static int created = 0;     // only one, shared
    String name;                // one per object

    Product(String name) {
        this.name = name;
        created++;
    }
}
```

```java
new Product("Keyboard");
new Product("Mouse");
System.out.println(Product.created);   // 2, via the class
```

And that is why `main` is `static`: when the program starts, there is no
object yet to call a method on.

:::pitfall
A `static` method cannot access an instance attribute — there is no
instance. The message is `non-static variable name cannot be referenced
from a static context`, and it confuses everyone in their first week. The
translation is: "you asked for the name of a product without saying which
product".
:::

## `toString`: the object introducing itself

```java title="Without toString"
System.out.println(keyboard);
// Product@2f92e0f4
```

That garbage is the class name and the memory address. Override `toString`
and the object learns to describe itself:

```java title="Product.java (excerpt)" numbered
@Override
public String toString() {
    return name + " (R$ " + price + ", " + stock + " units)";
}
```

```text title="Output"
Keyboard (R$ 349.9, 12 units)
```

`@Override` is an **annotation**: a notice to the compiler that you are
replacing a method that already exists. If you misspell the name
(`toStrring`), the compiler complains instead of leaving the method
orphaned. Keep the idea of annotations in mind: from chapter 17 on it
becomes the main way of talking to Spring.

:::history
Every object in Java inherits from a class called `Object`, which offers
`toString`, `equals` and `hashCode`. That decision is from 1995 and it has
a cost: even the simplest types drag along three methods that almost never
do the right thing by default. It was to fix that that Java 16 brought
`record`, which you see in chapter 12 — and which generates all three for
free, correctly.
:::

## `equals` and `hashCode`: chapter 4's lesson, now on your side

Are two products with the same name and the same price the same product?
`==` says no, because they are two objects. If you want them to be equal,
you have to say how:

```java title="Equality by content" numbered
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof Product other)) return false;
    return name.equals(other.name) && price == other.price;
}

@Override
public int hashCode() {
    return Objects.hash(name, price);
}
```

The rule that has existed for thirty years: **if you override `equals`,
override `hashCode`**. `HashMap` and `HashSet` use the second to find the
object before comparing with the first; one without the other produces the
hardest bug to explain — an item you just put in the `Set` that it says it
does not contain.

:::tip
Nobody writes these two methods by hand in 2026. The IDE generates them,
and chapter 12's `record` makes them unnecessary. What you need is to
recognize the pair and know why it exists.
:::

:::term Class
The description of a type: what data it carries and which operations it
accepts.
:::

:::term Object (or instance)
A concrete specimen of a class, with its own values, created with `new`.
:::

:::summary
- A class brings together the data that travel together and the methods
  that operate on them.
- The constructor runs once, at `new`, and `this` tells the attribute from
  the parameter.
- `static` belongs to the class; without `static`, to the object.
- `toString` makes the object describe itself; `equals` and `hashCode` go
  in pairs.
:::

:::checkpoint
You write a class with attributes, a constructor and methods, create
objects, explain `static` and know why `equals` and `hashCode` come
together.
:::

:::milestone
The `Product` class is born — the heart of the project. Its attributes are
the same ones that will become table columns in chapter 19 and JSON fields
in chapter 24.
:::

:::exercise level=1
Write the `Category` class with `name` and `description`, a constructor and
`toString`. Create two categories and print them.

:::answer
```java
public class Category {
    String name;
    String description;

    Category(String name, String description) {
        this.name = name;
        this.description = description;
    }

    @Override
    public String toString() {
        return name + " — " + description;
    }
}
```
:::

:::exercise level=2
Add to `Product` a method `applyDiscount(double percent)` that changes the
object's own price and returns `void`. Then write
`withDiscount(double percent)` that returns a **new** `Product` without
changing the original. Which of the two would you prefer in an API?

:::answer
The second. A method that changes the object from the inside (*mutation*)
forces the caller to remember that the previous value was lost; one that
returns a new object can be used in any order and is safe in concurrent
code. Chapter 12 takes this idea to its limit with `record`, which is
immutable by construction.
:::

:::exercise level=3
Create a `List<Product>` with four products and compute the total value of
the stock by adding up each one's `totalInStock()`.

:::answer
```java
double total = 0;
for (Product p : products) {
    total += p.totalInStock();
}
```
In chapter 14 this becomes
`products.stream().mapToDouble(Product::totalInStock).sum()`. Keep both
versions side by side: the second only looks like magic to someone who
didn't write the first.
:::
