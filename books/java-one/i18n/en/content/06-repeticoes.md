---
source_hash: 91580175e207
title: "Loops"
number: 6
part: p1
kicker: "Writing the same line ten times is a design mistake, not a typo."
goal: >-
  Choose between `for`, `for-each` and `while` according to the problem,
  write a correct accumulator and leave a loop without breaking the logic.
---

Repetition is the first thing a computer does better than a person. And it
is also where the first hard defect lives: the loop that runs once too
many, or once too few.

## A list of values

```java title="Prices.java" numbered
double[] prices = { 19.90, 4.50, 32.00 };

System.out.println(prices.length);   // 3
System.out.println(prices[0]);       // 19.9
```

An array has a fixed size, defined the moment it is born, and positions
numbered from **zero**. The last index is always `length - 1` — that
off-by-one arithmetic is the origin of half of all loop errors.

:::diagram type="cells" caption="Three values, indexes 0 to 2. Index 3 does not exist."
items: ["19.90", "4.50", "32.00"]
index: 0
orientation: horizontal
notes:
  - { at: 2, text: "length - 1" }
:::

:::trivia
Counting from zero is not a whim: in C, `v[i]` literally means "the address
of `v` plus `i` positions", so the first item is zero positions from the
start. Java inherited the convention without inheriting pointer arithmetic.
Edsger Dijkstra wrote a famous two-page note, in 1982, arguing that zero is
mathematically more elegant — and he won the argument, at least among
curly-brace languages.
:::

## The loop you will use almost always

```java title="for-each"
for (double price : prices) {
    System.out.println(price);
}
```

Read it as "for each price in prices". There is no index, no counter, no
way to run past the end. When you just need to visit every element — which
is almost always — this is the right form.

## The loop with a counter

```java title="classic for" numbered
for (int i = 0; i < prices.length; i++) {
    System.out.println(i + ": " + prices[i]);
}
```

:::anatomy title="The three parts of the for, separated by semicolons"
lang: java
code: |
  for (int i = 0; i < prices.length; i++) {
      System.out.println(prices[i]);
  }
notes:
  - { line: 1, text: "**Start**: runs once, before everything. `i` only exists inside the loop." }
  - { line: 1, text: "**Condition**: tested before every round. False the first time? The body never runs." }
  - { line: 1, text: "**Step**: runs at the end of every round. Forgetting it is the classic infinite loop." }
  - { line: 2, text: "The body uses `i` as the index — the only reason to choose this form." }
:::

Use the classic `for` when the index is part of what you want: numbering
the output, comparing with the previous element, stepping two at a time.

:::diagram type="flowchart" caption="A loop is a decision that comes back to itself."
nodes:
  - { id: ini,   type: start,    text: "i = 0" }
  - { id: test,  type: decision, text: "i < length?" }
  - { id: corpo, type: process,  text: "use prices[i]" }
  - { id: inc,   type: process,  text: "i++" }
  - { id: fim,   type: start,    text: "End" }
edges:
  - { from: ini,   to: test }
  - { from: test,  to: corpo, label: "yes" }
  - { from: corpo, to: inc }
  - { from: inc,   to: test }
  - { from: test,  to: fim,   label: "no" }
:::

:::pitfall
`i <= prices.length` blows up with
`ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3`.
The sign is `<`, without the equals. That exception has the most honest
name on the platform: it tells you which index you asked for and what the
size was.
:::

## `while` and `do while`

```java title="Until it's over" numbered
int attempts = 0;
while (attempts < 3) {
    System.out.println("attempt " + attempts);
    attempts++;
}
```

`while` is for when you **don't know how many rounds** it will take:
reading lines from a file until it ends, trying a connection until it
works, processing a queue until it empties. If you know the number of
rounds, `for` says it better.

`do while` tests **after** running, so the body executes at least once:

```java
do {
    System.out.println("runs even with a false condition");
} while (false);
```

In practice you will use it once every two years, in a terminal menu. It is
here so you recognize it when you find it.

:::story The Friday report
The stock report ran every Friday at six in the evening. It had never
caused a problem, which only means nobody had looked.

That Friday, Carlos tweaked one line. Just one: he moved the `i++` "to make
it more readable". He committed at 5:52 p.m. and went home.

At 6:03 p.m., the staging server started to heat up.

At 7:20 p.m., Marina got the alert at home, opened her laptop on the dinner
table and found a loop that counted to ten without ever reaching ten. The
counter advanced inside an `if` that was almost never true.

At 7:41 p.m., she wrote on the commit review a sentence Carlos kept
forever:

> "Every loop you write has to answer three questions before the first
> line: what accumulates, what varies and **when it stops**. This one
> answered two."

On Monday, Roberto wanted to know why the environment had gone down. Marina
explained. He listened carefully and asked the only question that mattered
to him:

"But can we avoid this by changing the deploy process?"

Marina said yes. He left satisfied. The loop was still wrong, but that was
Carlos's business.
:::

## Accumulating a result

```java title="Sum.java" numbered
double total = 0;

for (double price : prices) {
    total += price;
}

System.out.println("Total: R$ " + total);
```

The `total` variable is born **outside** the loop and survives it; `price`
is born inside and dies every round. Swapping the two is the mistake that
makes the total always come back as zero.

:::key
Every useful loop answers three questions before the first line: what
accumulates, what varies and when it stops. If you cannot answer all three
out loud, the loop is not ready to be written yet.
:::

:::example Summing, counting and filtering are the same skeleton
```java
int expensive = 0;
for (double price : prices) {
    if (price > 20) {
        expensive++;
    }
}
System.out.println(expensive + " item(s) above R$ 20");
```
The same accumulator structure, with a decision inside. In chapter 14 these
three operations get their own names — `reduce`, `count` and `filter` — and
become one line each.
:::

## Leaving early: `break` and `continue`

```java title="Stop at the first occurrence" numbered
int position = -1;
for (int i = 0; i < prices.length; i++) {
    if (prices[i] > 30) {
        position = i;
        break;          // found it: no need to see the rest
    }
}
```

`break` abandons the loop; `continue` skips to the next round. Both are
legitimate and save work — but each one is a detour, and too many detours
turn the loop into a maze.

:::pitfall
`break` inside a nested loop leaves **only the inner loop**. Whoever
expects it to leave both usually finds out after half an hour. If you need
to leave both, the signal is clear: extract a method and use `return`. That
is the subject of the next chapter.
:::

## Infinite loops: how they happen and how to get out

```java
while (true) {
    // no break, no return: the program never ends
}
```

In the terminal, `Ctrl+C` ends it. The three most common causes: forgetting
the step (`i++`), stepping in the wrong direction (`i--` with the condition
`i < n`) or changing the condition inside the body without noticing. If
your program "froze", suspect the loop before suspecting the computer.

:::tree title="Where we are now"
java-one/
  App.java
  Greeting.java
  Sum.java        # accumulator
  Prices.java     # array + for-each
:::

:::summary
- An array has a fixed size and indexes from `0` to `length - 1`.
- `for-each` goes through everything without an index: it is the right form
  for the common case.
- The classic `for` is for when the index is part of the problem.
- `while` is for when you don't know the number of rounds.
- The accumulator lives outside the loop; the round's variable lives
  inside.
:::

:::checkpoint
You go through an array in all three ways, write a correct accumulator,
know what causes an infinite loop and use `break` without getting lost.
:::

:::milestone
End of Part 1. You have a program that receives data, decides and repeats
— the three abilities any language offers. Part 2 trades "a program that
runs" for "a program that organizes itself", and that is where Java starts
charging its price and paying its dividends.
:::

:::exercise level=1
Go through an array of five grades and print only those greater than or
equal to 7.

:::answer
```java
double[] grades = { 5.0, 7.0, 9.5, 6.4, 8.0 };
for (double grade : grades) {
    if (grade >= 7) {
        System.out.println(grade);
    }
}
```
:::

:::exercise level=2
Find the highest price in an array without using a library. Think about
what the initial value of the maximum variable should be — and why starting
at zero is a trap.

:::answer
```java
double highest = prices[0];
for (double price : prices) {
    if (price > highest) {
        highest = price;
    }
}
```
Starting at `0` only works by accident, when every value is positive.
Starting from the first element always works — including with negative
temperatures, which is where the lazy version breaks.
:::

:::exercise level=3
Print the multiplication tables from 1 to 5 using two nested loops, one
line per number. Then count how many times the body of the inner loop
executed.

:::answer
```java
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= 10; j++) {
        System.out.print(i * j + " ");
    }
    System.out.println();
}
```
The inner body runs 50 times: 5 × 10. That multiplication is the first
notion of cost — in chapter 30 it comes back with an ugly name, the *N+1
problem*, when each round of a loop becomes a database query.
:::
