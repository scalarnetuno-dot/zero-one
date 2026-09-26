---
source_hash: a3a5ad5e76a8
title: "Methods"
number: 7
part: p2
kicker: "Giving a name to a piece of code is the cheapest form of documentation there is."
goal: >-
  Extract a method with parameters and a return value, understand what scope
  is and recognize when an overload helps and when it confuses.
---

Until now all the code lived inside `main`. That works for twenty lines and
becomes a nightmare at two hundred. A method is a piece of code with a
name, input and output — and the name is the most important part.

## From repetition to method

:::compare left="Before: the calculation scattered" right="After: the calculation with a name"
double t1 = p1 * 1.08;
double t2 = p2 * 1.08;
double t3 = p3 * 1.08;
---
double t1 = withTax(p1);
double t2 = withTax(p2);
double t3 = withTax(p3);
:::

The version on the right has two advantages that are not aesthetic. If the
tax rate changes, you edit one place. And whoever reads `withTax(p1)`
understands the intent without rebuilding the multiplication.

```java title="The method" numbered
static double withTax(double value) {
    return value * 1.08;
}
```

:::anatomy title="Each part of a method declaration"
lang: java
code: |
  static double withTax(double value) {
      return value * 1.08;
  }
notes:
  - { line: 1, text: "`static` because we are still calling it from `main`, without an object. In chapter 9 this changes." }
  - { line: 1, text: "`double` is the **return type**: the kind of value that comes out." }
  - { line: 1, text: "`withTax` is the name. A verb or a noun, always in camelCase." }
  - { line: 1, text: "`double value` is the **parameter**: the name the value gets in here." }
  - { line: 2, text: "`return` gives back the value and ends the method in the same statement." }
:::

## `void` and `return`

A method that returns nothing declares `void`. In it, `return` with no
value is for leaving early:

```java title="Leaving early works for methods too" numbered
static void printLabel(String name, double price) {
    if (name == null || name.isBlank()) {
        return;                     // nothing to print
    }
    System.out.println(name + " — R$ " + price);
}
```

:::key
A method with more than one `return` is not a problem; a method with more
than one *reason to exist* is. If you need "and" to explain what it does
("validates **and** saves **and** notifies"), it is three methods.
:::

:::story The tax rate that lived in nine places
The tax went from 8% to 8.5%. One line, said Roberto. Five minutes.

Carlos opened the project and used search: `1.08`. Nine results.

He changed all nine. Ran it. It worked.

On Wednesday, Cláudia said the closing report still had the old value.
Carlos searched again, this time for `* 1.0`: a tenth place showed up,
written as `0.08 + 1`, which the previous search had not caught.

Marina showed up with her mug and asked the question that was not about
taxes:

"How many times does this calculation need to exist?"

"Once."

"And how many times does it exist?"

"Ten." Carlos thought for a moment. "Ten that I found."
:::

## Scope: where a name exists

```java title="Each brace opens a world" numbered
static void example() {
    int a = 1;
    if (a == 1) {
        int b = 2;
        System.out.println(a + b);   // ok: a and b exist
    }
    // System.out.println(b);        // error: b died at the brace
}
```

The rule is simple: a name exists from its declaration to the brace that
closes it. The compiler does not let you use what no longer exists — nor
declare two variables with the same name in the same scope.

:::pitfall
A parameter is a **copy**. Changing `value` inside the method does not
change the caller's variable. For primitives this is always true; for
objects, the copy is of the *reference* — you cannot swap the caller's
object, but you can change its contents. That distinction comes back in
chapter 9 and explains many shared-list bugs.
:::

## Overloading: same name, different signatures

```java title="Three ways to call the same idea" numbered
static double total(double price) {
    return total(price, 1);
}

static double total(double price, int quantity) {
    return total(price, quantity, 0.08);
}

static double total(double price, int quantity, double tax) {
    return price * quantity * (1 + tax);
}
```

Java chooses which one to call by the number and type of the arguments —
the **signature**. Notice the chaining: the first two versions only fill in
default values and delegate. It is a common and healthy pattern, because
the rule lives in a single place.

:::pitfall
An overload that changes the *meaning* confuses. `save(String)` writing to
a file and `save(int)` writing to the database is a trap for whoever reads
it. Different names cost three keystrokes and save an hour.
:::

:::trivia
Java does not have parameters with default values, like Python or Kotlin.
The chained overload above is the idiomatic substitute — and the reason old
Java libraries have methods with seven versions. From Part 3 on you will
see Spring solve this another way: with configuration objects.
:::

## Methods that document rules

This is the translation exercise that holds up the rest of the book: **every
business rule fits in a method named after the rule**.

```java title="The rule has a name" numbered
static boolean canSell(int stock, boolean active) {
    return active && stock > 0;
}
```

In chapter 22 this same function becomes a method of a `ProductService`
class and starts being called by an HTTP controller. The form changes; the
idea is the same: the rule lives in one place, has a name and can be tested
on its own — which is exactly what chapter 34 will do with it.

:::example A whole program, now organized
```java
public class Store {
    public static void main(String[] args) {
        double[] prices = { 19.90, 4.50, 32.00 };
        System.out.println("Total: R$ " + sum(prices));
        System.out.println("Average: R$ " + average(prices));
    }

    static double sum(double[] values) {
        double total = 0;
        for (double v : values) {
            total += v;
        }
        return total;
    }

    static double average(double[] values) {
        if (values.length == 0) return 0;
        return sum(values) / values.length;
    }
}
```
`average` uses `sum` and handles the empty-array case. Without that
`return 0`, dividing by zero would return `NaN` — and `NaN` in a report is
worse than an error, because it does not draw attention.
:::

:::summary
- A method is code with a name, parameters and a return type.
- `void` returns nothing; a bare `return` is for leaving early.
- A name exists until the brace that closes its block.
- Overloading is the same name with different signatures — use it for
  default values, not to change meaning.
- A business rule with a name is a testable rule.
:::

:::checkpoint
You extract a method from repeated code, choose between `void` and a return
value, know where each variable exists and use overloading without
confusing whoever reads it.
:::

:::milestone
The project's rules start to have names: `canSell`, `withTax`. They are
still static methods in a loose class — in chapter 9 they get an owner.
:::

:::exercise level=1
Extract a `highestPrice(double[] prices)` method from the chapter 6
exercise and call it from `main`.

:::answer
```java
static double highestPrice(double[] prices) {
    double highest = prices[0];
    for (double p : prices) {
        if (p > highest) {
            highest = p;
        }
    }
    return highest;
}
```
:::

:::exercise level=2
Write `applyDiscount(double price, double percent)` that rejects
percentages outside 0 to 100 by returning the original price. Then write
the overload `applyDiscount(double price)` with a 10% discount.

:::answer
```java
static double applyDiscount(double price) {
    return applyDiscount(price, 10);
}

static double applyDiscount(double price, double percent) {
    if (percent < 0 || percent > 100) {
        return price;
    }
    return price * (1 - percent / 100);
}
```
Returning the original price in the invalid case is a debatable decision —
it hides the error. In chapter 13 you will learn the honest alternative:
throwing an exception.
:::

:::exercise level=3
Write `static String label(String name, double price, int quantity)` that
returns `"Keyboard · R$ 349,90 · 12 units"` — with a decimal comma, as the
Brazilian store prints it. Use `String.format` and find out on your own how
to get the comma instead of the dot.

:::answer
```java
static String label(String name, double price, int quantity) {
    return String.format(Locale.of("pt", "BR"),
            "%s · R$ %.2f · %d units", name, price, quantity);
}
```
The decimal separator depends on the *locale*: `String.format` without one
uses the machine's default, so on an English-language system it prints
`349.90`, and on a Brazilian one, `349,90`. Passing the locale explicitly
makes the output the same everywhere. Environment-dependent formatting is
one of the most irritating sources of "it works on my machine".
:::
