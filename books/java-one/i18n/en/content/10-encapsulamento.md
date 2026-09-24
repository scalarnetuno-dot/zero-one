---
source_hash: cee7d76e600e
title: "Encapsulation"
number: 10
part: p2
kicker: "Hiding the attribute is not ceremony: it is what keeps the object from existing in an impossible state."
goal: >-
  Protect an object's state with `private`, expose what is needed through
  methods, and validate in the constructor so the object is never born
  invalid.
---

The `Product` class from the previous chapter has a serious problem:

```java
keyboard.price = -500;
keyboard.stock = -3;
```

It compiles, runs and creates a product with a negative price. The error is
not in the line that wrote the nonsense — it is in the class, which allowed
it.

## `private`: closing the door

```java title="Product.java" numbered
public class Product {
    private String name;
    private double price;
    private int stock;

    public Product(String name, double price, int stock) {
        this.name = name;
        this.price = price;
        this.stock = stock;
    }
}
```

With `private`, the line `keyboard.price = -500;` stops compiling:
`price has private access in Product`. The data has become the class's
internal business — and now the class can guarantee that it makes sense.

## Validate where the object is born

```java title="An object that refuses to exist wrong" numbered
public Product(String name, double price, int stock) {
    if (name == null || name.isBlank()) {
        throw new IllegalArgumentException("name is required");
    }
    if (price < 0) {
        throw new IllegalArgumentException("negative price");
    }
    this.name = name;
    this.price = price;
    this.stock = Math.max(stock, 0);
}
```

`throw` interrupts the creation and warns the caller. Chapter 13 covers
exceptions in detail; here the idea is enough: **it is cheaper to refuse
the object than to fix it later**.

:::key
If the constructor finishes, the object is valid. That guarantee runs
through the whole program: no method needs to check whether the price is
negative, because there is no product with a negative price. You traded a
thousand scattered checks for one, in the right place.
:::

## Getters and setters, with judgment

```java title="Always read, write when it makes sense" numbered
public String getName() {
    return name;
}

public double getPrice() {
    return price;
}

public void adjustPrice(double percent) {
    if (percent <= -100) {
        throw new IllegalArgumentException("invalid adjustment");
    }
    this.price = price * (1 + percent / 100);
}
```

Notice what does **not** exist: `setPrice`. Instead of a method that
accepts any number, the class exposes the real business operation —
adjusting the price. The name carries the rule.

:::pitfall
Generating `get` and `set` for every attribute out of reflex turns the
class into a form without rules — and brings back exactly the problem
`private` solved. The question before each `set` is: *does someone outside
have the right to change this on their own?* The answer is almost always
no.
:::

:::compare left="Generic setter" right="Named operation"
p.setStock(
    p.getStock() - 1);
---
p.decreaseStock(1);
:::

The column on the right can refuse the decrease if the stock is zero. The
one on the left has already written the `-1` before anyone asked.

:::story The intern's Black Friday
The field was public. It had been that way since day one and had never
bothered anyone.

The day before Black Friday, an intern got the simplest task on the list:
apply a 30% discount to one category. He wrote a loop that went through
the products and did `p.price = p.price * 0.7`.

It worked perfectly. It ran three times, because the script froze halfway
and he re-ran it just to be safe.

At 12:07 a.m., the store was selling monitors for R$ 411.00. At 12:09 a.m.,
for R$ 287.70. At 12:11 a.m., for R$ 201.39.

Marina shut the service down at 12:14 a.m. and, at the week's
retrospective, wrote on the board a sentence that became a team rule:

> "If an attribute can be changed by any line in the system, sooner or
> later it will be — three times in a row."

The intern did nothing wrong. The intern did exactly what the class
allowed.
:::

## The four access levels

| Modifier | Visible to |
|---|---|
| `private` | only the class itself |
| (none) | classes in the same package |
| `protected` | same package + subclasses |
| `public` | everybody |

Table: From the most closed to the most open. The practical rule: start at
`private` and open up only when it hurts.

The level without a modifier — called *package-private* — is the most
forgotten and one of the most useful: it lets classes in the same package
talk to each other without exposing anything to the rest of the world.

:::trivia
Java is one of the few languages in which the default level is neither
`public` nor `private`, but "package". The decision comes from the idea
that a package is a unit of trust — neighboring classes collaborate. In
practice, almost nobody uses it on purpose: most attributes without a
modifier are like that by oversight, which is why chapter 9 showed
`Product` that way.
:::

## Immutability: the radical version

What if nothing can change after creation?

```java title="Immutable Product" numbered
public class Product {
    private final String name;
    private final double price;

    public Product(String name, double price) {
        this.name = name;
        this.price = price;
    }

    public Product withPrice(double newPrice) {
        return new Product(name, newPrice);
    }
}
```

`final` on the attribute means "assigned once, in the constructor, and
never again". To change the price, you create another product. It looks
wasteful and it is the preferred pattern in modern code: an immutable
object has no inconsistent state, needs no defensive copy and is safe
between threads — which is exactly the situation of an API serving a
hundred requests at the same time.

:::tip
This whole class, with validation, `equals`, `hashCode` and `toString`,
becomes **one line** in chapter 12. But that line only makes sense to
someone who has seen the fifteen.
:::

## Where this shows up in the project

The `Product` entity in chapter 20 is going to need getters — because JPA
and Jackson read the data through them. What changes is the intent:
getters exist for the tools and for reading; state changes keep going
through methods named after rules.

:::tree title="Where we are now"
java-one/
  Product.java    # private + a constructor that validates
  Category.java
  Store.java      # main
:::

:::summary
- `private` closes the attribute; the constructor guarantees the object is
  born valid.
- A getter for reading; an operation named after a rule instead of a
  generic setter.
- Four access levels: start at `private` and open up when it hurts.
- `final` on the attributes creates an immutable object — the preferred
  pattern in an API.
:::

:::checkpoint
You protect attributes, validate in the constructor, choose between a
setter and a named operation, and can explain why immutability helps on a
server.
:::

:::milestone
`Product` now defends itself: a negative price and an empty name do not get
past the constructor. That validation will migrate to annotations in
chapter 25, but the rule stays the same.
:::

:::exercise level=1
Make every attribute of `Category` private and write only the getters. Then
try to change `name` from outside and read the compiler's message.

:::answer
`name has private access in Category`. The error happens at **compile
time**, not in production — the trade this book has defended since chapter
3.
:::

:::exercise level=2
Write `decreaseStock(int quantity)` in `Product`. It must reject a negative
quantity and reject a decrease larger than the available stock.

:::answer
```java
public void decreaseStock(int quantity) {
    if (quantity <= 0) {
        throw new IllegalArgumentException("invalid quantity");
    }
    if (quantity > stock) {
        throw new IllegalStateException("insufficient stock");
    }
    this.stock -= quantity;
}
```
Two different kinds of exception, on purpose: `IllegalArgumentException` is
the caller's fault; `IllegalStateException` is a situation of the object.
In chapter 26 that distinction becomes the difference between a `400` and
a `409` in the HTTP response.
:::

:::exercise level=3
Rewrite `Product` as an immutable class and adjust `decreaseStock` to
return a new product. Then list one advantage and one disadvantage of the
immutable version in an API.

:::answer
Advantage: no method can leave the object half-done, and two threads can
read it without a lock. Disadvantage: each change creates an object, which
in very large loops creates memory pressure — and, in JPA's case (chapter
20), the tool *needs* a mutable object to track changes. Knowing where
immutability does not fit is part of knowing how to use it.
:::
