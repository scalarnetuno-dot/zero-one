---
source_hash: 1d8c44d47373
title: "Exceptions"
number: 13
part: p2
kicker: "A handled error is a requirement. A swallowed error is a debt with interest."
epigraph: "I call it my billion-dollar mistake. It was the invention of the null reference in 1965."
epigraph_by: "Tony Hoare, creator of Quicksort"
goal: >-
  Throw and catch exceptions, choose between *checked* and *unchecked*,
  create your own exception and never again write an empty `catch`.
---

Programs go wrong for three reasons: the programmer made a mistake, the
user sent garbage, or the world outside failed. An exception is the
mechanism Java uses to warn that something went off the rails — and the way
you handle it defines the quality of your API.

## The most famous error on the platform

```java title="NullPointerException" numbered
String name = null;
System.out.println(name.length());
```

```text title="Terminal"
Exception in thread "main" java.lang.NullPointerException:
  Cannot invoke "String.length()" because "name" is null
        at Store.main(Store.java:3)
```

Notice the detail: the message says **which** variable was null and
**which** method you tried to call. That is a recent achievement (Java 14,
*helpful NullPointer messages*); before, you got only the line number, and
whoever had five chained calls on the same line was left guessing.

:::history
Tony Hoare introduced the null reference in ALGOL W, in 1965, because "it
was so easy to implement". In 2009 he publicly apologized in a talk,
calling it his billion-dollar mistake. Java inherited `null` from C++, and
the language spent thirty years creating remedies: `Optional` (Java 8),
detailed messages (Java 14) and nullability annotations in libraries.
:::

:::story The bug only Mr. Antônio can reproduce
"It gives an error when I click," said Mr. Antônio.

"An error on which screen?"

"On the screen."

Carlos asked for a screenshot. What came was a photo of the monitor, taken
with a phone, at an angle, with the window's reflection covering half the
message. Three words were legible: `NullPointerException`, `at` and
`ProductService`.

He tried to reproduce it for two hours. He registered a product, edited
it, deleted it, clicked on everything. Nothing.

Marina asked the only thing left to ask:

"Mr. Antônio, do you fill in the 'product nickname' field?"

"No, young man, that one's optional, isn't it?"

It was optional. And it was the only field the code read without checking
whether it existed.

No other employee in the company left that field empty, because everyone
had learned, without agreeing on it, to fill in everything. Mr. Antônio
had learned none of that. He just used the system the way it was written.
:::

## `try`, `catch`, `finally`

```java title="The complete form" numbered
try {
    int quantity = Integer.parseInt(args[0]);
    System.out.println(100 / quantity);
} catch (NumberFormatException e) {
    System.out.println("That's not a number: " + args[0]);
} catch (ArithmeticException e) {
    System.out.println("I can't divide by zero");
} finally {
    System.out.println("This always runs");
}
```

The `try` marks the risky section. Each `catch` handles **one type** of
problem. The `finally` runs with or without an error — it is where you
close a file, a connection, any resource.

:::pitfall
The cardinal sin:

```java
try {
    save(product);
} catch (Exception e) {
    // I'll look at it later
}
```

That does not handle the error: it erases the evidence. The program carries
on as if it had worked, the data was not saved and nobody finds out. If you
really cannot handle it, **rethrow** it or at least log it. An empty
`catch` is the one line of code I would reject in any review, no
discussion.
:::

## Two families: *checked* and *unchecked*

:::diagram type="blocks" caption="The hierarchy that decides whether the compiler will force you to handle it."
flow: false
rows:
  - [{ text: "Throwable", note: "everything that can be thrown" }]
  - [{ text: "Error", note: "the JVM gave up — don't handle it" }, { text: "Exception", note: "checked: the compiler demands it" }]
  - [{ text: "RuntimeException", note: "unchecked: the compiler doesn't demand it" }]
:::

| | *Checked* | *Unchecked* |
|---|---|---|
| Example | `IOException`, `SQLException` | `IllegalArgumentException`, `NPE` |
| Compiler | forces `try` or `throws` | forces nothing |
| Means | an expected failure of the outside world | a programming or usage defect |

Table: The practical rule: if the caller can do something about it,
*checked*; if it is a bug, *unchecked*.

```java title="Checked: the compiler demands a decision" numbered
// doesn't compile without handling:
Files.readString(Path.of("config.txt"));

// option 1: handle it here
try {
    Files.readString(Path.of("config.txt"));
} catch (IOException e) {
    System.out.println("couldn't find the file");
}

// option 2: declare it's not my problem
static String read() throws IOException {
    return Files.readString(Path.of("config.txt"));
}
```

:::trivia
*Checked* exceptions are an idea exclusive to Java — no popular language
after it repeated the experiment. The reason is the side effect observed in
the field: to get rid of the obligation, generations of programmers wrote
`catch (Exception e) {}`. The remedy created the disease it wanted to cure.
Modern frameworks, Spring included, convert almost everything to
*unchecked*.
:::

## `throw`: warn instead of lying

```java title="Refusing is better than a hidden fix" numbered
public void decreaseStock(int quantity) {
    if (quantity <= 0) {
        throw new IllegalArgumentException(
                "quantity must be positive: " + quantity);
    }
    if (quantity > stock) {
        throw new IllegalStateException(
                "insufficient stock: " + stock);
    }
    this.stock -= quantity;
}
```

Two different exceptions because they are two different problems:
`IllegalArgumentException` is the caller's fault; `IllegalStateException`
is a situation of the object. In chapter 26 that distinction becomes the
difference between answering `400 Bad Request` and `409 Conflict`.

## Your own exception: the name that carries the meaning

```java title="ProductNotFoundException.java" numbered
public class ProductNotFoundException extends RuntimeException {
    private final Long id;

    public ProductNotFoundException(Long id) {
        super("product not found: " + id);
        this.id = id;
    }

    public Long getId() {
        return id;
    }
}
```

Three decisions in those ten lines. It extends `RuntimeException`
(*unchecked*), because the caller has no way to "handle" an id that does
not exist — the HTTP layer handles it. The message includes the id, so the
log is good for something. And the id is kept, so whoever catches it can
build the response.

:::key
The name of the exception is its most valuable part.
`ProductNotFoundException` in the log says what happened without anyone
having to read the message. Generic `Exception` and `RuntimeException` throw
that value in the trash.
:::

## `Optional`: the alternative to `null`

```java title="Saying there may be nothing" numbered
Optional<Product> found = repository.findById(7L);

if (found.isPresent()) {
    System.out.println(found.get().getName());
}

// better: no if
String name = found
        .map(Product::getName)
        .orElse("unknown");

// or throwing the right exception
Product p = found
        .orElseThrow(() -> new ProductNotFoundException(7L));
```

`Optional` is a box that may be empty. The difference from `null` is not
technical, it is about communication: the method's signature **warns** that
the result may not exist, and the compiler forces you to decide what to do.

The last form — `orElseThrow` — is the one the project will use from
chapter 22 to the end of the book. Keep it in mind.

:::pitfall
`Optional` is for a method's **return value**. Do not use it as a
parameter, nor as an entity attribute, nor in a record field that will
become JSON. The API's creator, Brian Goetz, was explicit about it — and
the internet spent ten years ignoring him.
:::

## `try-with-resources`

```java title="It closes itself, even on error" numbered
try (var reader = Files.newBufferedReader(Path.of("data.csv"))) {
    System.out.println(reader.readLine());
} catch (IOException e) {
    System.out.println("reading failed");
}
```

What is inside the parentheses is closed automatically when leaving the
block, with or without an exception. Before Java 7 this required a
`finally` with another `try` inside — the ugliest piece of code the
language ever asked for.

:::summary
- `try/catch` handles by type; `finally` always runs.
- *Checked* forces handling; *unchecked* signals a programming defect.
- Never write an empty `catch`: rethrow or log.
- Your own exception with a specific name is worth more than a long
  message.
- `Optional` communicates absence in the return type; `orElseThrow` is the
  project's standard.
:::

:::checkpoint
You handle exceptions by type, decide between *checked* and *unchecked*,
create your own exception with context and use `Optional` in the return
value instead of `null`.
:::

:::milestone
The project knows how to refuse: an invalid price, insufficient stock, a
product that does not exist. What is missing is translating those refusals
into HTTP responses — and chapter 26 does it, using exactly the classes
from this chapter.
:::

:::exercise level=1
Write a program that takes a number as an argument, divides 100 by it and
handles the two possible errors with distinct messages.

:::answer
```java
try {
    int n = Integer.parseInt(args[0]);
    System.out.println(100 / n);
} catch (NumberFormatException e) {
    System.out.println("argument is not a number");
} catch (ArithmeticException e) {
    System.out.println("division by zero");
}
```
A third case is missing: running without any argument throws
`ArrayIndexOutOfBoundsException`, which is not caught. Did you spot it?
Good sign.
:::

:::exercise level=2
Create `InsufficientStockException` keeping the available stock and the
requested quantity. Use it in `decreaseStock`.

:::answer
```java
public class InsufficientStockException extends RuntimeException {
    public InsufficientStockException(int available, int requested) {
        super("stock " + available + ", requested " + requested);
    }
}
```
Keeping both numbers in the message is what turns a log into a diagnosis —
without them, you know it failed, but not by how much.
:::

:::exercise level=3
Write a method `Optional<Product> find(Long id)` over a
`Map<Long, Product>` and then use it in three ways: with `orElse`, with
`orElseThrow` and with `ifPresent`.

:::answer
```java
Optional<Product> find(Long id) {
    return Optional.ofNullable(map.get(id));
}
```
`Optional.ofNullable` is the bridge between an old API that returns `null`
and the world of `Optional`. In the three ways of using it, notice that
none of them forces an explicit `if` — and that `orElseThrow` is the only
one that preserves the information that something went wrong.
:::
