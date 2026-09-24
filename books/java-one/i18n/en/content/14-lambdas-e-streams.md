---
source_hash: 4293094912bb
title: "Lambdas and streams"
number: 14
part: p2
kicker: "The loop says how to go through. The stream says what you want. The second sentence is shorter."
goal: >-
  Write a lambda, chain `filter`, `map`, `sorted` and `collect`, and
  recognize when a stream helps and when it gets in the way.
---

In 2014 Java 8 added functions as values. It was not a facelift: it changed
the style of Java code and is the foundation of half of the modern APIs —
including some Spring will ask of you in Part 4.

## Lambda: a function without a name

```java title="The same idea, two ways of writing it" numbered
// before Java 8: anonymous class
Comparator<String> byLength = new Comparator<String>() {
    @Override
    public int compare(String a, String b) {
        return a.length() - b.length();
    }
};

// Java 8: lambda
Comparator<String> byLength2 =
        (a, b) -> a.length() - b.length();
```

Eight lines became two. The lambda is the same thing: the implementation of
an interface that has **a single abstract method**. Java calls that a
*functional interface*, and that is how the lambda knows which method it is
implementing.

:::anatomy title="Lambda syntax, in three forms"
lang: java
code: |
  p -> p.getPrice() > 100
  (a, b) -> a.length() - b.length()
  p -> {
      log(p);
      return p.getName();
  }
notes:
  - { line: 1, text: "One parameter, no parentheses; a one-expression body, no `return`." }
  - { line: 2, text: "Two parameters require parentheses. The type is inferred from the context." }
  - { line: 3, text: "A body with braces needs an explicit `return`." }
:::

## Method reference: the lambda that already exists

```java title="Four forms of the same idea" numbered
products.forEach(p -> System.out.println(p));   // lambda
products.forEach(System.out::println);          // reference

names.sort((a, b) -> a.compareTo(b));           // lambda
names.sort(String::compareTo);                  // reference
```

When the lambda only calls an existing method, `::` says it more briefly.
You will see `Product::getName` in almost all modern Java code.

## Stream: the sequence of operations

```java title="The loop from chapter 6, rewritten" numbered
List<Product> expensive = products.stream()
        .filter(p -> p.getPrice() > 100)
        .toList();
```

:::compare left="Imperative loop" right="Declarative stream"
List<Product> expensive =
    new ArrayList<>();
for (Product p : products) {
  if (p.getPrice() > 100) {
    expensive.add(p);
  }
}
---
var expensive = products
    .stream()
    .filter(p ->
        p.getPrice() > 100)
    .toList();
:::

The difference is not the size, it is what you read. On the left you
rebuild the intent from the mechanism; on the right the intent is written
down: *filter the expensive ones*.

## The five operations that solve almost everything

```java title="A complete pipeline" numbered
List<String> names = products.stream()
        .filter(p -> p.getStock() > 0)            // selects
        .sorted(Comparator.comparing(Product::getPrice))
        .map(Product::getName)                    // transforms
        .limit(10)                                // cuts
        .toList();                                // materializes
```

| Operation | What it does | Returns |
|---|---|---|
| `filter` | keeps whoever passes the test | stream |
| `map` | transforms each item | stream |
| `sorted` | sorts | stream |
| `limit` / `skip` | cuts | stream |
| `toList` / `count` / `sum` | finishes | result |

Table: The first four are **intermediate** — they return a stream and
execute nothing. The last is **terminal**: it is what makes the pipeline
run.

:::key
A stream without a terminal operation **does not execute**. If your
`filter` seems not to have run, look for the missing `toList`. That lazy
evaluation is what lets Java go through the collection a single time,
applying every step item by item.
:::

## Reducing to a number

```java title="Sum, count, average" numbered
long active = products.stream()
        .filter(Product::isActive)
        .count();

double total = products.stream()
        .mapToDouble(Product::getPrice)
        .sum();

OptionalDouble average = products.stream()
        .mapToDouble(Product::getPrice)
        .average();
```

`mapToDouble` trades the stream of objects for one of primitive numbers,
which has `sum`, `average`, `max` and `min` ready to use. And notice the
`OptionalDouble`: the average of an empty list does not exist, and the API
is honest about it — chapter 13's lesson showing up again.

## Grouping: chapter 8's `Map` in one line

```java title="Count by status" numbered
Map<Status, Long> byStatus = products.stream()
        .collect(Collectors.groupingBy(
                Product::getStatus,
                Collectors.counting()));
```

Compare with the five `getOrDefault` lines of chapter 8. Same output,
another way of writing it — and the stream version stays readable when the
grouping has two levels.

:::trivia
Streams were designed with a second goal: parallelism. Swapping `.stream()`
for `.parallelStream()` distributes the work across the cores. It looks
like a free optimization and it almost never is: for small collections, the
cost of coordinating the threads is greater than the gain. The Java team's
own rule of thumb is not to consider parallelism below ten thousand
elements.
:::

:::story The one-line pull request
Carlos discovered streams on a Thursday and rewrote the whole report on
Friday.

The method had eighteen lines. It became one.

One line of four hundred and twelve characters, with four `filter`s, two
`map`s, one `flatMap`, one `sorted` with a reversed comparator and a
`collect` grouping by two keys. He opened the *pull request* with the title
"simplification".

Marina answered with a single comment, on line 1:

> "Explain out loud, without reading, what this line does. If you can, I'll
> approve it."

Carlos tried. He got as far as the third `filter`.

The approved version had six lines and three named methods: `active()`,
`bestSellers()` and `byCategory()`. Each with a short stream inside.

"Streams aren't for writing less," said Marina. "They're for writing what
you want instead of how to go through it."
:::

:::art caption="A four-hundred-character line isn't concise code: it's compressed code."
src="uma-linha-com-quatrocentos-caracteres-nao-e-codigo-conciso-e-codigo-comprimido.png"
Charge editorial minimalista: tela de editor de código mostrando uma única
linha absurdamente longa que atravessa o monitor e continua por uma fita de
papel que sai da tela, cai no chão e se enrola pela sala. Um desenvolvedor
jovem, orgulhoso, segura a ponta da fita. Uma desenvolvedora sênior, ao lado,
segura uma tesoura pequena com expressão paciente. Fundo branco, poucos
elementos, humor visual seco, estética de revista de tecnologia.
:::

## When the loop is still better

Streams don't replace everything. The loop is still clearer when:

- you need the **index** of each item;
- you need to **leave in the middle** knowing where you stopped;
- the body has several lines with side effects (logging, writing,
  sending);
- you are debugging — stepping through a stream is uncomfortable.

:::pitfall
A stream with a side effect inside `map` is a trap:
`.map(p -> { save(p); return p; })`. It works, and it misleads the reader:
`map` says "I transform", not "I write to the database". To act on each
item, use `forEach` — the name warns that something is going to happen.
:::

## The pipeline the project will use

```java title="A slice of chapter 28" numbered
public List<ProductResponse> searchByName(String term) {
    return repository.findAll().stream()
            .filter(p -> p.getName()
                    .toLowerCase()
                    .contains(term.toLowerCase()))
            .map(ProductResponse::of)
            .toList();
}
```

This version filters **in memory** — and that is exactly why chapter 28
will replace it with a query that filters in the database. Keep the
difference in mind: a stream is great for transforming what you already
have, and terrible for avoiding bringing in what you don't need.

:::summary
- A lambda is the implementation of an interface with a single abstract
  method.
- `::` refers to a method that already exists.
- An intermediate operation returns a stream; only the terminal one runs
  the pipeline.
- `groupingBy` does in one line what the `Map` did in five.
- The loop still wins when there is an index, an early exit or a side
  effect.
:::

:::checkpoint
You write lambdas, chain `filter`, `map`, `sorted` and `collect`, reduce a
stream to a number and can justify when you prefer a loop.
:::

:::milestone
End of Part 2. The project has vocabulary (`Product`, `Status`, DTOs),
named rules, typed errors and a style of data transformation. That is
enough Java for Spring — and it is exactly where Part 3 begins.
:::

:::exercise level=1
Given a `List<Product>`, write a stream that returns the names of the
products with zero stock, in alphabetical order.

:::answer
```java
List<String> outOfStock = products.stream()
        .filter(p -> p.getStock() == 0)
        .map(Product::getName)
        .sorted()
        .toList();
```
:::

:::exercise level=2
Compute the total value of the stock (price × quantity of each product)
using a stream. Compare with the loop version from chapter 9.

:::answer
```java
double total = products.stream()
        .mapToDouble(p -> p.getPrice() * p.getStock())
        .sum();
```
Four lines against six, and a more important difference: the stream
version has no mutable variable at all. Without an accumulator, there is
no way to forget to initialize it.
:::

:::exercise level=3
Group the products by price range (up to 50, from 50 to 200, above 200)
and return a `Map<String, List<String>>` with the names in each range.

:::answer
```java
Map<String, List<String>> ranges = products.stream()
        .collect(Collectors.groupingBy(
                p -> p.getPrice() <= 50 ? "cheap"
                        : p.getPrice() <= 200 ? "mid" : "expensive",
                Collectors.mapping(Product::getName,
                        Collectors.toList())));
```
That chained ternary is the limit of good taste — in practice, it deserves
to become a `rangeOf(Product p)` method, or better, an `enum Range` with
the criterion inside, as in chapter 12. If you thought of that before
reading, Part 2 has done its job.
:::
