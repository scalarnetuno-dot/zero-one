---
source_hash: 5b27c5ecb3de
title: "Operators and expressions"
number: 4
part: p1
kicker: "The equals sign does not mean equal, and the double equals sign lies about text."
goal: >-
  Predict the result of any arithmetic, logical or comparison expression,
  and explain why `==` is no good for comparing text in Java.
---

An operator is a symbol that takes values and returns another one. You used
three in the last chapter without thinking. This chapter is short and dense
on purpose: almost every logic defect you will hunt later is born from a
misunderstood operator.

## Arithmetic

```java title="Five symbols" numbered
int sum = 7 + 2;       // 9
int sub = 7 - 2;       // 5
int mult = 7 * 2;      // 14
int div = 7 / 2;       // 3  ← integer, the remainder vanishes
int rest = 7 % 2;      // 1  ← the remainder that vanished
```

The `%` is the **modulo**: the remainder of the division. It looks useless
until you need to know whether a number is even (`n % 2 == 0`), paginate a
list or distribute items into columns — and then it shows up every week.

:::trivia
`%` in Java can return a negative number: `-7 % 2` gives `-1`, not `1`. The
language follows C's rule, where the sign of the remainder follows the
dividend. Python chose the opposite (`-7 % 2` gives `1`). Two languages,
two defensible mathematics — and a guaranteed bug for anyone who switches
from one to the other without noticing.
:::

## Assignment and the short form

The `=` does not ask whether two values are equal: it **sends** the one on
the right to the name on the left. Reading `total = total + price` as an
equation is the fastest way to confusion; read it as "the new total becomes
the previous total plus the price".

```java
total = total + price;
total += price;          // identical, and shorter
```

There are `+=`, `-=`, `*=`, `/=` and `%=`. They all do the same: operate and
assign.

## Increment: the `++` and its position

```java title="The position changes the value of the expression" numbered
int i = 5;
System.out.println(i++);   // prints 5, then i is 6
System.out.println(i);     // 6

int j = 5;
System.out.println(++j);   // prints 6
```

`i++` returns the value **before** adding; `++i` adds and **then** returns.
In a loop, alone on the line (`i++;`), it makes no difference at all. Inside
a larger expression, it does — and that is why professional code avoids
mixing an increment with anything else on the same line.

## Comparison

| Operator | Question |
|---|---|
| `==` | are they the same? |
| `!=` | are they different? |
| `>` `<` | greater, less |
| `>=` `<=` | greater or equal, less or equal |

Table: The six comparators. They all return `boolean` — never a number.

And here lives the most famous trap in the language.

## `==` compares identity, `.equals()` compares content

```java title="This may not work" numbered
String password = new String("abc");

if (password == "abc") {
    System.out.println("Allowed");
}
```

It prints nothing. The `==` asks whether the two names point to **the same
object in memory** — and they do not: `new String` created a new object. The
right question is about content:

```java title="This always works"
if (password.equals("abc")) {
    System.out.println("Allowed");
}
```

:::diagram type="cells" caption="Two variables, two objects, the same content: `==` says no, `equals` says yes."
items: ["password →", "object A: \"abc\"", "literal →", "object B: \"abc\""]
orientation: horizontal
:::

:::pitfall
Sometimes `==` works with `String` — and that is worse than if it never
worked. The compiler keeps identical literals in one place (the *string
pool*), so `String a = "abc"; String b = "abc";` makes `a == b` give
`true`. The test passes on your computer and fails when the text comes from
the keyboard, a file or an HTTP request. **For text, always use
`equals`.**
:::

:::tip Flip the comparison with literals
`"abc".equals(password)` does the same test and does not blow up if
`password` is `null`. It is a two-keystroke habit that erases a whole class
of errors — you will meet it again in chapter 13, when
`NullPointerException` becomes the topic.
:::

For primitives (`int`, `double`, `boolean`, `char`), `==` is the right
tool: there is no object at all, only the value. The practical rule is
short: **primitives use `==`, objects use `equals`.**

:::story The coupon that only worked on Carlos's machine
The coupon was simple: type PROMO10 and get ten percent off.

It worked in Carlos's test. It worked in Carlos's test again. It worked in
Carlos's test a third time, which should have served as a warning.

The next day, Mr. Antônio called:

"Young man, this coupon of yours doesn't work."

"Did you type PROMO10, all in capitals?"

"I typed it exactly like it is on the paper."

Carlos spent forty minutes trying to reproduce it. He typed the coupon, it
worked. Marina came over, read the line `if (coupon == "PROMO10")` and asked
a single question:

"In your test, where does that text come from?"

"It's written in the code."

"And in the customer's case?"

"It comes from... the keyboard."

Marina said nothing more. She did not need to. Carlos was already swapping
the `==` for `.equals`, with that specific feeling of fixing a mistake the
compiler had let through on purpose.
:::

## Logical

```java title="Three operators and one important optimization" numbered
boolean hasTicket = true;
int age = 16;

if (hasTicket && age >= 18) { /* requires both */ }
if (hasTicket || age >= 18) { /* one is enough */ }
if (!hasTicket)             { /* inverts */ }
```

`&&` and `||` **short-circuit**: evaluation stops as soon as the result is
decided. If the left side of an `&&` is false, the right side is not even
executed. That is not a performance detail, it is a tool:

```java
if (name != null && name.equals("Ana")) { ... }
```

If `name` is `null`, the second test never runs and the program does not
blow up. In the reverse order, it blows up every time.

:::anatomy title="How the compiler reads a compound expression"
lang: java
code: |
  boolean allowed = age >= 18
          && (hasTicket || invited)
          && !blocked;
notes:
  - { line: 1, text: "Comparators first: `>=` runs before `&&`." }
  - { line: 2, text: "Parentheses first: the inner `||` is resolved before the outer `&&`." }
  - { line: 3, text: "`!` has high precedence: it inverts only `blocked`, not the whole expression." }
:::

The full precedence table has fifteen levels and nobody memorizes it. The
professional advice is different: **use parentheses** when the expression
has more than two operators. They cost nothing in performance and save an
hour of debugging.

## The ternary

```java
String status = age >= 18 ? "adult" : "minor";
```

Read it as a question: *condition ? value if yes : value if no*. It is for
choosing **a value**. It is not for executing two blocks of code — that is
what `if` is for, which is the next chapter.

:::summary
- `/` between integers discards the remainder; `%` returns the remainder.
- `=` assigns, `==` compares. `i++` returns before adding.
- Primitives compare with `==`; objects compare with `equals`.
- `&&` and `||` stop as soon as the result is decided — use that against
  `null`.
- Parentheses are executable documentation.
:::

:::checkpoint
You predict the result of arithmetic and logical expressions, you know why
`==` fails with text and you use short-circuiting to protect a call.
:::

:::milestone
Nothing new in the project, and that is intentional: this chapter is a debt
being paid in advance. The rules from here show up in every `if` for the
rest of the book.
:::

:::exercise level=1
Write a program that takes a number as an argument and prints `"even"` or
`"odd"` using `%` and the ternary operator.

:::answer
```java
int n = Integer.parseInt(args[0]);
System.out.println(n % 2 == 0 ? "even" : "odd");
```
:::

:::exercise level=2
Without running it, say what this snippet prints. Then run it and check.

```java
int i = 3;
int total = i++ + ++i;
System.out.println(total + " " + i);
```

:::answer
It prints `8 5`. The first `i++` uses `3` and leaves `i` at `4`; the `++i`
takes `i` to `5` and uses `5`. So `3 + 5 = 8`. If you got it wrong, do not
feel bad: that is exactly why this kind of line does not pass code review.
:::

:::exercise level=2
Write the condition that lets someone in if they have a ticket **and** (are
an adult **or** are accompanied). Then rewrite it without any parentheses
and explain why the meaning changes.

:::answer
`hasTicket && (age >= 18 || accompanied)`. Without parentheses,
`hasTicket && age >= 18 || accompanied` is read as
`(hasTicket && age >= 18) || accompanied` — because `&&` takes precedence
over `||`. In that version, anyone accompanied gets in even without a
ticket.
:::
