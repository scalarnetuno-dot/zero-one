---
source_hash: d78f4a5a5b69
title: "Conditionals"
number: 5
part: p1
kicker: "Choosing one path means taking responsibility for the other — even when it isn't written."
goal: >-
  Write decisions with `if`, `else if` and `switch`, choose among them with
  good judgment and recognize the path you left implicit.
---

Until now the program always did the same thing. From here on it looks at
a value and chooses. It is the smallest unit of intelligence a program can
have, and it fits in three lines.

## `if` requires a `boolean`

```java title="Adulthood.java" numbered
int age = 18;

if (age >= 18) {
    System.out.println("You may enter");
} else {
    System.out.println("You may not enter");
}
```

The condition in parentheses has to result in `true` or `false`. In
languages where `0` counts as false, `if (age)` compiles; in Java, it does
not. The compiler demands that you say **what** you are comparing.

:::diagram type="flowchart" caption="Every decision has two paths, even when you write only one."
nodes:
  - { id: ini, type: start,    text: "Start" }
  - { id: d1,  type: decision, text: "age >= 18?" }
  - { id: sim, type: process,  text: "You may enter" }
  - { id: nao, type: process,  text: "You may not enter" }
  - { id: fim, type: start,    text: "End" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "yes" }
  - { from: d1,  to: nao, label: "no" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

When you leave out the `else`, the "no" path still exists: it just does
nothing. Being aware of that is what separates a correct program from one
that only looks correct — and in chapter 26, when an API has to answer
`404`, that empty path becomes the most visible defect there is.

:::key
Before writing an `if`, answer out loud: *"and if not?"*. If the answer is
"nothing happens", write the comment saying so. If it is "I don't know",
you have found a requirement nobody defined.
:::

:::story The thirty-seven combinations
It was supposed to be a single rule.

"If the customer is premium, apply ten percent," said Roberto.

Carlos wrote the `if`. It took four minutes.

"And if it's an employee?" asked Cláudia, on Thursday.

"Also ten."

Carlos wrote the second `if`. It took six minutes, because now there was an
`else if`.

"And if it's premium **and** an employee?"

Silence.

"They stack?" Carlos ventured.

"I don't know," said Roberto. "Ask finance."

Finance answered the following Tuesday: they stack, but with a fifteen
percent cap, except on products from outsourced suppliers, except if it is
the customer's birthday, except on the first purchase.

Marina went to the whiteboard and drew a table with every combination.
There were thirty-seven.

"The problem isn't Java," she said, capping the marker. "The problem is
that nobody ever wrote this whole rule down anywhere. We're going to be the
first people in the company's history to find out what it is."
:::

:::art caption="Every `else if` ladder starts with a single rule."
src="toda-escada-de-else-if-comeca-com-uma-regra-so.png"
Charge editorial minimalista: quadro branco corporativo inteiramente tomado
por uma tabela de condições "SE... E SE... MAS SE...", com dezenas de células
e setas se cruzando. Uma desenvolvedora sênior de pé ao lado do quadro,
marcador na mão, expressão resignada. Sentado, um desenvolvedor jovem abraça
o notebook contra o peito com olhar vazio. Um gerente, de costas, já saindo
pela porta com o celular no ouvido. Poucos elementos, fundo branco,
composição limpa, humor visual seco, estética de revista de tecnologia.
:::

## Braces: the case where saving costs a lot

Java lets you leave out the braces when the block has a single line:

```java
if (age >= 18)
    System.out.println("You may enter");
```

And allowing that has already cost the world a lot of money. The code below
compiles and is wrong:

:::compare left="What it looks like" right="What the compiler reads"
if (ok)
    allow();
    log();
---
if (ok) {
    allow();
}
log();
:::

`log()` always runs, because indentation means nothing to the compiler.
**Always use braces**, including in one-line blocks. It is the easiest
style rule to justify in a code review.

:::history
In February 2014 Apple fixed the flaw nicknamed *goto fail*: an `if`
without braces, in C, with one line accidentally duplicated. The result was
that the TLS certificate check always passed — anyone on the same network
could impersonate any website. Two braces would have prevented the most
talked-about security flaw of that year.
:::

## The `else if` ladder

```java title="Range.java" numbered
double grade = 7.5;

if (grade >= 9) {
    System.out.println("Excellent");
} else if (grade >= 7) {
    System.out.println("Good");
} else if (grade >= 5) {
    System.out.println("Fair");
} else {
    System.out.println("Insufficient");
}
```

The order matters: the first true test wins and the rest are not even
evaluated. That is why the ladder goes from the highest value to the
lowest — in the reverse order, `grade >= 5` would swallow every case above
it.

:::pitfall
A ladder with more than four rungs is a sign that a concept is missing. In
chapter 12 this same grade range becomes an `enum`, and the ladder
disappears. When you find yourself writing the sixth `else if`, stop and
ask which type is missing.
:::

## `switch`: when the question is "which of these?"

If every test compares the **same variable** with exact values, `switch`
says it better:

```java title="Switch with an arrow (Java 14+)" numbered
String type = "PIX";

String term = switch (type) {
    case "PIX" -> "immediate";
    case "CARD" -> "2 days";
    case "BOLETO" -> "3 business days";
    default -> "unknown";
};

System.out.println(term);
```

Three things deserve attention here. The arrow `->` replaces `case:` with
`break`. The `switch` **returns a value** — it is an expression, not just a
branch. And the `default` is mandatory when you assign the result to a
variable: the compiler demands that every path produce something.

:::compare left="old switch (up to Java 13)" right="modern switch (14+)"
switch (type) {
  case "PIX":
    term = "immediate";
    break;
  case "CARD":
    term = "2 days";
    break;
  default:
    term = "?";
}
---
term = switch (type) {
  case "PIX" -> "immediate";
  case "CARD" -> "2 days";
  default -> "?";
};
:::

:::trivia
That mandatory `break` in the old form exists because of a feature called
*fall-through*: without it, execution slides into the next `case`. It was
intentional in C, to group cases, and became the number one source of bugs
in `switch`. The arrow form does not fall through — and that is why it was
created.
:::

## Which one to use

| Situation | Choice |
|---|---|
| One condition with a range (`>=`, `&&`) | `if` |
| Two or three ordered ranges | `else if` ladder |
| Many exact values of the same variable | `switch` |
| Choosing **one value** out of two | ternary |
| Many exact values + behavior | `enum` (chapter 12) |

Table: It is not a matter of taste: each form communicates a different
intent to whoever reads it later.

:::practice
Run the grade ladder with `9`, `7`, `5` and `4.9`. Then invert the order of
the tests and run it again with the same values. Keep both outputs: it is
the shortest demonstration that the order of conditions is logic, not
style.
:::

:::story
Two weeks later, Marina deleted the thirty-seven `if`s and left four lines
in their place. Carlos asked how.

"The rule didn't change," she said. "It just stopped living in thirty-seven
places."

The how is in chapter 12.
:::

## An `if` you are going to write a lot

The book's project is an API, and an API spends the day answering a single
question: *does this exist?* The shape of that decision in modern Java is
this:

```java title="The shape that comes back in chapter 22" numbered
Optional<Product> found = repository.findById(id);

if (found.isEmpty()) {
    throw new ProductNotFoundException(id);
}
return found.get();
```

You do not know `Optional`, or `throw`, or a repository yet. Just keep the
shape: **handle the bad case first and leave**. That pattern, called
*early return*, keeps the code shallow — without it, a real API piles up
five levels of nested `if`.

:::summary
- `if` requires a `boolean`; a number does not count as a condition.
- Always use braces — indentation means nothing to the compiler.
- In a ladder, the first true test wins: order from the most restrictive to
  the most general.
- A `switch` with arrows returns a value and does not fall into the next
  case.
- Handle the bad case first and leave: the code stays shallow.
:::

:::checkpoint
You write simple and chained decisions, choose among `if`, `switch` and the
ternary by intent, and recognize the implicit path of an `if` without
`else`.
:::

:::milestone
The program now decides. It does not store anything or answer anyone yet —
but the logic that will reject a negative price in chapter 25 is exactly
this.
:::

:::exercise level=1
Write a program that takes a temperature as an argument and prints
`"Fever"` above 37.8 and `"Normal"` otherwise.

:::answer
```java
double temperature = Double.parseDouble(args[0]);
if (temperature > 37.8) {
    System.out.println("Fever");
} else {
    System.out.println("Normal");
}
```
:::

:::exercise level=2
Compute a parking fee: the first hour costs R$ 8, each following hour costs
R$ 5 and the daily maximum is R$ 40. Test with 1, 3 and 12 hours.

:::answer
```java
int hours = Integer.parseInt(args[0]);
double fee = 8 + (hours - 1) * 5;
if (fee > 40) {
    fee = 40;
}
System.out.println("R$ " + fee);
```
The cap comes **after** the calculation, as a second decision. Trying to
solve the limit inside the same expression is the shortest path to a
hard-to-spot mistake.
:::

:::exercise level=3
Rewrite the grade ladder using a `switch` with arrows and the integer
result of dividing by 10 (`(int) grade / 10`). Then decide which of the two
versions you would keep in the project and justify it.

:::answer
```java
String label = switch ((int) grade / 10) {
    case 10, 9 -> "Excellent";
    case 8, 7 -> "Good";
    case 6, 5 -> "Fair";
    default -> "Insufficient";
};
```
It works and it is shorter. But the `if` version says `grade >= 9`
explicitly, while this one requires the reader to rebuild the range from a
division. For ranges, `if` communicates better; for exact values, `switch`.
The right answer is knowing why.
:::
