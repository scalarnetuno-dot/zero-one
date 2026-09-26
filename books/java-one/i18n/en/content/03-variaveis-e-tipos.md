---
source_hash: 37a2056cdba0
title: "Variables and types"
number: 3
part: p1
kicker: "Declaring a type is hiring a reviewer who works for free."
goal: >-
  Declare variables of the five everyday types, predict the result of a
  conversion and know when to use `var` without losing the compiler's
  protection.
---

A program stores things: a price, a name, a yes-or-no answer. In Java,
storing requires saying what kind of thing is being stored. That
requirement looks like red tape for the first ten minutes and becomes a
safety net for the rest of the project.

## The shape of a declaration

```java title="Three declarations" numbered
double price = 19.90;
String customer = "Ana";
boolean paid = false;
```

Each line has four parts: the type, the name, the equals sign and the
value. The type is on the left because it is the first question the
compiler asks — and the one it answers for you later, when you make a
mistake.

:::diagram type="cells" caption="A variable is a name stuck on a box of known size."
items: ["19.90", "\"Ana\"", "false"]
orientation: horizontal
notes:
  - { at: 0, text: "double · 8 bytes" }
  - { at: 2, text: "boolean" }
:::

## The types that solve almost everything

| Type | Holds | Range or example |
|---|---|---|
| `int` | integer | from −2.1 billion to 2.1 billion |
| `long` | large integer | up to 9.2 quintillion |
| `double` | decimal | `19.90` |
| `boolean` | true or false | `true` |
| `String` | text | `"Ana"` |
| `char` | one character | `'A'` |

Table: The six everyday types. The others — `byte`, `short`, `float` —
exist and can wait until you have a memory reason to use them.

The first five, except `String`, are **primitive types**: the value lives
right in the variable. `String` is a class, and the variable holds a
*reference* to the text. That distinction looks theoretical now and, in
chapter 4, explains the most common mistake of people coming from another
language.

:::key
Types are not about the computer, they are about you. When you write
`double price`, you are warning the next person who reads the code —
probably you, in March — that a customer's name will never show up there.
:::

## The compiler checks before running

```java title="Error caught before running"
int quantity = 3;
quantity = "three";
```

```text title="Terminal"
Store.java:3: error: incompatible types:
    String cannot be converted to int
        quantity = "three";
                   ^
```

Notice the timing: this did not happen with the program running in front of
a customer. It happened in your terminal, three seconds after you wrote the
line. In a dynamic language, the same defect would wait for request number
one thousand and one to show up.

## Conversions: when the type changes its mind

Java automatically converts what loses no information — an `int` fits in a
`double`. The opposite requires you to take responsibility in writing:

:::compare left="Automatic (widening)" right="Explicit (casting)"
int i = 42;
double d = i;
// 42.0
---
double d = 42.9;
int i = (int) d;
// 42, truncated
:::

The `(int)` is a **cast**: you are saying "I know it may lose something, do
it anyway". And it does: `42.9` becomes `42`, not `43`. Java truncates, it
does not round.

:::pitfall
`int average = 7 / 2;` stores `3`, not `3.5`. Division between two
integers discards the remainder without any warning. If you want decimal
places, at least one side has to be decimal: `7.0 / 2`. This is, by far,
the most common type error in billing code.
:::

:::story Mr. Antônio's cent
The first test invoice came out at R$ 56.40. The second, at R$ 56.39.

The same products. The same cart. One cent of difference.

Cláudia took the case to the meeting with the face of someone bringing a
bomb wrapped in gift paper.

"The customer is going to ask."

"It's rounding," said Carlos.

"The customer is going to ask *why*," Cláudia insisted.

Marina opened the code, looked for three seconds and pointed at the line:
`double price`.

"It's not rounding. It's that we asked the computer to store money in a box
that doesn't know how to store money."

Mr. Antônio, who was testing the store that same day, called in the
afternoon to say he had bought a R$ 19.90 cable and the total said
R$ 19.89. He could not explain float, floating point or IEEE 754. He could
count money.
:::

## Money is not `double`

Keep this one in mind, because chapter 19 will ask for it: `double` is
binary and does not represent `0.1` exactly.

```java title="The sum that doesn't add up" numbered
double total = 0.1 + 0.2;
System.out.println(total);
```

```text title="Output"
0.30000000000000004
```

It is not a Java bug: it is how floating-point numbers work in any
language. For money, there is `BigDecimal`, which stores the value in
decimal base and charges more verbosity in exchange for exactness. The
book's project will use `BigDecimal` for the product price from chapter 18
on.

:::trivia
The IEEE 754 standard, which defines this behavior, dates from 1985 and was
designed by a committee that included William Kahan — who won the Turing
Award for it. The imprecision is not carelessness: it is the price of
representing huge and tiny numbers with 64 bits. Java just does not let you
forget it exists.
:::

## Constants

When the value must not change, `final` turns the attempt into a compile
error:

```java
final double TAX = 0.08;
// TAX = 0.09;
// error: cannot assign a value to final variable TAX
```

The naming convention in uppercase with underscores (`MAX_TAX`) is only a
convention — but it is universal in Java, and code that ignores it looks
foreign.

## `var`: letting the compiler write the type

Since Java 10 you can omit the type when it is obvious from the value:

```java
var price = 19.90;     // double
var customer = "Ana";  // String
```

The type still exists and is still checked — it is just not written. Use
`var` when the line already says everything; write the type when the value
comes from far away, from a method call whose return type is not obvious.

:::pitfall
`var` is not JavaScript's `var`. It does not create an untyped variable: it
*infers* the type and locks it there. After `var x = 10;`, the line
`x = "ten";` does not compile. And `var` without an initial value
(`var x;`) does not compile either — there is nothing to infer from.
:::

:::example A name that explains, a type that protects
```java
double t = 56.4;           // what is t?
double orderTotal = 56.4;  // now a human understands too
```
The compiler accepts both. Only one of them still makes sense six months
from now.
:::

:::term Variable
A name bound to a memory space of known type. In Java the type is fixed:
the value changes, the kind does not.
:::

:::summary
- Declaring means stating the type before the name; the type is checked at
  compile time.
- `int`, `long`, `double`, `boolean`, `String` and `char` cover almost
  everything.
- Division between integers discards the remainder; one side has to be
  decimal.
- `double` is no good for money — the project will use `BigDecimal`.
- `var` infers the type without giving it up.
:::

:::checkpoint
You declare variables of the six basic types, predict what happens in a
conversion, know why `0.1 + 0.2` is not `0.3` and use `final` and `var` in
the right place.
:::

:::milestone
The project is still a handful of loose `.java` files, but now they store
data with a declared type. It is the minimum vocabulary of the `Product`
entity born in chapter 18.
:::

:::exercise level=1
Declare the four variables that describe a store product: name, price,
quantity in stock and whether it is active. Print all four on one line.

:::answer
```java
String name = "Mechanical keyboard";
double price = 349.90;
int quantity = 12;
boolean active = true;
System.out.println(name + " · R$ " + price
        + " · " + quantity + " units · active: " + active);
```
These four lines are the draft of the `Product` entity. Keep the file.
:::

:::exercise level=2
Compute the average of `7`, `8` and `10` first with `int` and then with
`double`. Explain the difference in one sentence.

:::answer
With `int`, `(7 + 8 + 10) / 3` gives `8` — the remainder is discarded.
With `(7 + 8 + 10) / 3.0` it gives `8.333...`. The arithmetic is the same;
the type of the divisor decides whether the fractional part survives.
:::

:::exercise level=3
Add `0.1` ten times in a loop and print the result. Then redo it with
`BigDecimal` (`new BigDecimal("0.1")` and the `add` method). Compare the
outputs.

:::answer
The `double` prints `0.9999999999999999`. The `BigDecimal` prints `1.0`.
The difference is invisible in a report and catastrophic on an invoice —
and that is why financial systems forbid `double` by policy, not by taste.
:::
