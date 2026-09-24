---
source_hash: d80c6b1356a3
title: "Enums and records"
number: 12
part: p2
kicker: "Two features that delete code: one for the closed set, another for pure data."
goal: >-
  Replace text constants with `enum`, write a `record` in one line and
  explain why both let the compiler do more of the work.
---

This chapter has a rare side effect: it **deletes** code you wrote in
chapters 5 and 10. Enum and record are features that solve two cases so
common that the language decided to give them their own syntax.

## The problem with `String` as a category

```java title="What goes wrong with loose text" numbered
String status = "ACTIVE";

if (status.equals("active")) {    // doesn't enter: different case
    ...
}
status = "ACITVE";                // compiles. and it's wrong.
```

Text accepts any value, including wrong ones. The compiler has no way to
help because, to it, `"ACITVE"` is a perfectly valid text.

## `enum`: the closed set

```java title="Status.java" numbered
public enum Status {
    ACTIVE,
    INACTIVE,
    SOLD_OUT
}
```

```java
Status status = Status.ACTIVE;

if (status == Status.ACTIVE) {     // here == is correct!
    System.out.println("for sale");
}
```

Three immediate gains. `Status.ACITVE` **does not compile**. Comparing with
`==` is safe again, because there is exactly one instance of each value.
And the `switch` becomes exhaustive:

```java title="The compiler demands the missing cases" numbered
String label = switch (status) {
    case ACTIVE -> "For sale";
    case INACTIVE -> "Discontinued";
    case SOLD_OUT -> "Out of stock";
};
```

No `default`. If someone adds `PRE_SALE` to the enum tomorrow, this
`switch` stops compiling — and the compiler points to the exact place where
the new case is not handled. That is a compile error you **want** to have.

:::key
Every time you write an `if` comparing text with a constant, there is an
enum waiting to be born. The signal is clear: if the set of values is known
and does not change at run time, it is a type, not a text.
:::

:::story ACITVE
The status was a text. `"ACTIVE"`, `"INACTIVE"`, `"SOLD_OUT"` — agreed in a
meeting, written in the minutes, followed by everybody.

Until the Tuesday someone imported four hundred products from a
spreadsheet and the column came out as `"ACITVE"`.

Nothing broke. No exception, no log, no alert. The four hundred products
simply stopped showing up in the store, because the filter looked for
`"ACTIVE"` and they were nothing.

It took eleven days for anyone to notice. The one who noticed was Mr.
Antônio, who called asking why the headphone brand he always bought had
been "discontinued".

At the retrospective, Roberto suggested one more validation in the
spreadsheet import. Marina suggested something else:

"Or we stop letting the computer accept any word in a field that only has
three possible values."
:::

## Enum with data and behavior

Here is what almost nobody teaches: an enum is a complete class.

```java title="PaymentMethod.java" numbered
public enum PaymentMethod {
    PIX("Pix", 0, 0),
    BOLETO("Boleto", 3, 0),
    CARD("Card", 0, 2.99);

    private final String label;
    private final int termDays;
    private final double feePercent;

    PaymentMethod(String label, int termDays, double fee) {
        this.label = label;
        this.termDays = termDays;
        this.feePercent = fee;
    }

    public double applyFee(double value) {
        return value * (1 + feePercent / 100);
    }

    public String getLabel() {
        return label;
    }
}
```

```java
double charged = PaymentMethod.CARD.applyFee(100);   // 102.99
```

The fee table that would live in a twenty-line `switch` now lives next to
each value. Adding a payment method means adding a line — and the compiler
guarantees nobody forgot to state the fee.

:::compare left="if ladder" right="Enum with data"
if (m.equals("PIX"))
  return v;
if (m.equals("BOLETO"))
  return v;
if (m.equals("CARD"))
  return v * 1.0299;
---
return m.applyFee(v);
:::

:::trivia
Enums arrived in Java 5, in 2004. Before that, the pattern was
`public static final int ACTIVE = 1;` — and that brought a fun problem: any
`int` would do. A function expecting a status accepted `42` without
complaint. The pattern even had a name, the *Typesafe Enum Pattern*, and
took up thirty lines in Joshua Bloch's book. The language absorbed the
whole pattern into one keyword.
:::

## `record`: pure data

Remember the immutable `Product` class from chapter 10, with a constructor,
getters, `equals`, `hashCode` and `toString`? That is forty lines. Now it
is this:

```java title="ProductResponse.java" numbered
public record ProductResponse(
        Long id,
        String name,
        double price,
        int stock) {
}
```

The compiler automatically generates: the `private final` attributes, the
constructor with every field, one read method per field (`id()`, `name()` —
without the `get` prefix), `equals` and `hashCode` by content, and a
readable `toString`.

```java
var p = new ProductResponse(7L, "Keyboard", 349.90, 12);
System.out.println(p.name());    // Keyboard
System.out.println(p);
// ProductResponse[id=7, name=Keyboard, price=349.9, stock=12]
```

:::anatomy title="What the compiler writes for you"
lang: java
code: |
  public record ProductResponse(Long id, String name) {
      public ProductResponse {
          if (name == null) {
              throw new IllegalArgumentException();
          }
      }
  }
notes:
  - { line: 1, text: "The record's parameters **are** the attributes: `private final` by definition." }
  - { line: 1, text: "Reading is `p.name()`, without `get` — and there is no `set`: a record is immutable." }
  - { line: 2, text: "**Compact** constructor: just the validation, without repeating the assignments." }
  - { line: 4, text: "Validating here guarantees the same as chapter 10: the object is never born invalid." }
:::

## When to use a record and when to use a class

| Use `record` | Use `class` |
|---|---|
| data that only carries values | an object with behavior and changing state |
| API request and response | database entity (JPA needs to mutate it) |
| composite key, coordinate, pair | anything that needs to inherit |

Table: A record is for data; a class is for objects. A record cannot extend
anything — by construction.

:::pitfall
A record looks like the answer to everything and does not work as a JPA
entity. Hibernate (chapter 20) needs an empty constructor and setters to
track changes — a record has neither. That is why the project will use a
**class** for `Product` (the entity) and a **record** for `ProductRequest`
and `ProductResponse` (the DTOs of chapter 24).
:::

## Both together, the way the project will use them

```java title="A slice of chapter 24" numbered
public record ProductResponse(
        Long id,
        String name,
        double price,
        Status status,
        PaymentMethod preferredPayment) {
}
```

The JSON the client receives will come out with exactly these fields — and
the enum becomes text during serialization, without you writing a line of
conversion. This is the shape of the response that opened chapter 1.

:::summary
- `enum` is a closed set: a typo does not compile and `switch` becomes
  exhaustive.
- An enum can have attributes, a constructor and methods: the table lives
  next to the value.
- `record` generates the constructor, readers, `equals`, `hashCode` and
  `toString`.
- A record is immutable and does not inherit — perfect for a DTO, unfit for
  a JPA entity.
:::

:::checkpoint
You replace text constants with an enum, write an enum with data and
behavior, declare records and know when not to use them.
:::

:::milestone
The project's vocabulary is complete: `Product` (class), `Status` and
`PaymentMethod` (enums), `ProductResponse` (record). What is missing is
what to do when something goes wrong — the next chapter.
:::

:::exercise level=1
Replace the grade ladder from chapter 5 with an `enum Grade` with
`EXCELLENT`, `GOOD`, `FAIR` and `INSUFFICIENT`, and a static method
`of(double score)` that returns the grade.

:::answer
```java
public enum Grade {
    EXCELLENT, GOOD, FAIR, INSUFFICIENT;

    public static Grade of(double score) {
        if (score >= 9) return EXCELLENT;
        if (score >= 7) return GOOD;
        if (score >= 5) return FAIR;
        return INSUFFICIENT;
    }
}
```
The ladder still exists, but now it lives inside the type it produces — and
it exists in only one place in the system.
:::

:::exercise level=2
Write `record Money(BigDecimal amount, String currency)` with validation in
the compact constructor: the amount cannot be null or negative, and the
currency must have three letters.

:::answer
```java
public record Money(BigDecimal amount, String currency) {
    public Money {
        if (amount == null || amount.signum() < 0) {
            throw new IllegalArgumentException("invalid amount");
        }
        if (currency == null || currency.length() != 3) {
            throw new IllegalArgumentException("invalid currency");
        }
    }
}
```
:::

:::exercise level=3
Add to the `PaymentMethod` enum a method `termInBusinessDays()` and find out
on your own what happens if you call `values()` — and what that is for in
an API.

:::answer
`PaymentMethod.values()` returns an array with every value, in declaration
order. In an API that lets you answer `GET /payment-methods` listing the
available options without keeping a second list anywhere — the source of
truth is the enum itself.
:::
