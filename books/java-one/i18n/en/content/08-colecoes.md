---
source_hash: 5ae48da56ae3
title: "Arrays and collections"
number: 8
part: p2
kicker: "An array has a size. A list has a life. A map has a key. Choosing wrong is expensive."
goal: >-
  Choose between `List`, `Set` and `Map` by the problem, go through each of
  them and explain why you declare the interface and not the
  implementation.
---

An array solves the case where you know the size. An API does not know:
the customer may register three products today and three hundred tomorrow.
For that there is the collections *framework* — the part of the standard
library you will use most for the rest of your life.

## The three questions

| Question | Structure | Characteristic |
|---|---|---|
| In what order? | `List` | accepts duplicates, has an index |
| Is it here? | `Set` | no duplicates, no guaranteed order |
| What is the value of? | `Map` | key → value pairs |

Table: Choosing the collection is choosing the question you are going to
ask a thousand times a second.

## `List`: order and repetition

```java title="A list that grows" numbered
List<String> products = new ArrayList<>();
products.add("Keyboard");
products.add("Mouse");
products.add("Keyboard");       // a duplicate, and that's fine

System.out.println(products.size());     // 3
System.out.println(products.get(0));     // Keyboard
System.out.println(products.contains("Mouse"));  // true

for (String p : products) {
    System.out.println(p);
}
```

:::anatomy title="The most important line of the chapter"
lang: java
code: |
  List<String> products = new ArrayList<>();
notes:
  - { line: 1, text: "`List` is the **interface**: the contract, what can be done." }
  - { line: 1, text: "`<String>` is the generic type: the compiler starts rejecting anything that isn't text." }
  - { line: 1, text: "`ArrayList` is the **implementation**: how it is done in memory." }
  - { line: 1, text: "The empty `<>` (*diamond*) infers the type from the left side — since Java 7." }
:::

Declaring `List` on the left and `ArrayList` on the right is a convention
with a practical consequence: if tomorrow you need to switch to
`LinkedList`, you change one word and nothing else breaks. It is the first
encounter with an idea Spring takes to the extreme in Part 3 — **depend on
the interface, not the implementation.**

:::trivia
Before Java 5 there were no generics: a `List` held `Object`, and you had
to write `(String) list.get(0)` to get the text back. A type error only
showed up in production, as a `ClassCastException`. Generics exist to turn
that runtime defect into a compile error — the same trade this book has
been praising since chapter 3.
:::

## `Set`: in or out

```java title="No repetition" numbered
Set<String> categories = new HashSet<>();
categories.add("peripheral");
categories.add("peripheral");    // ignored
System.out.println(categories.size());   // 1
```

`Set` is the right structure for "have I seen this one?", "which ones are
distinct?", "does the user have this permission?" — and that last question
is exactly the one chapter 33 is going to ask.

:::pitfall
`HashSet` guarantees no order at all — not even insertion order. If you
print a `HashSet` expecting the order you inserted, you are in for a
fright. When order matters, use `LinkedHashSet` (insertion order) or
`TreeSet` (natural order).
:::

:::story The report with a mind of its own
"The report is coming out in random order," said Cláudia.

"There's no such thing as random order," Carlos replied. "It must be
registration order."

It was not. It was a `HashSet`.

They ran it again: another order. They ran it a third time: the same order
as the first, which confused everyone for another twenty minutes.

Roberto, walking by, heard "unpredictable order" and had an idea:

"Isn't that a good sign? Like, the system is choosing on its own. It looks
like artificial intelligence."

Marina slowly raised her head and said, without raising her voice:

"Roberto, it's a hash table. It doesn't choose. It doesn't have opinions.
It has the remainder of a division."
:::

## `Map`: key and value

```java title="Stock by product" numbered
Map<String, Integer> stock = new HashMap<>();
stock.put("Keyboard", 12);
stock.put("Mouse", 3);

System.out.println(stock.get("Keyboard"));           // 12
System.out.println(stock.get("Monitor"));            // null
System.out.println(stock.getOrDefault("Monitor", 0));  // 0

for (Map.Entry<String, Integer> item : stock.entrySet()) {
    System.out.println(item.getKey() + ": " + item.getValue());
}
```

`get` of a missing key returns `null` — and `null` is the origin of the
most famous error on the platform. `getOrDefault` exists precisely so you
don't have to think about it.

:::diagram type="cells" caption="A map is a two-column table with instant lookup by the first column."
items: ["Keyboard → 12", "Mouse → 3", "Cable → 41"]
orientation: vertical
notes:
  - { at: 0, text: "unique key" }
:::

## Immutable lists: the modern shortcut

```java
List<String> fixed = List.of("PIX", "CARD", "BOLETO");
Map<String, Integer> terms = Map.of("PIX", 0, "BOLETO", 3);
```

`List.of` and `Map.of` create **immutable** collections: calling `add` on
them throws `UnsupportedOperationException`. That looks like a limitation
and is protection — a constant nobody can change by accident. Use them for
the system's fixed values.

:::pitfall
`List.of("a", "b")` is not an `ArrayList`. If you receive a list from
outside and need to change it, copy it: `new ArrayList<>(received)`.
Modifying a list that came from somewhere else is, besides a potential bug,
bad design manners.
:::

## Sorting

```java title="Two orders, one line each" numbered
List<String> names = new ArrayList<>(
        List.of("Mouse", "Cable", "Keyboard"));

Collections.sort(names);                    // alphabetical order
names.sort(Comparator.reverseOrder());      // reversed
names.sort(Comparator.comparing(String::length));  // by length
```

The last line uses two things from chapter 14 (method reference and
functional comparator). Keep it in mind: when you get there, you will have
already seen it work.

## Going through: the three forms and when to use each

```java title="The same loop, three dialects" numbered
for (String p : products) { }          // standard, almost always

for (int i = 0; i < products.size(); i++) { }  // index matters

products.forEach(System.out::println); // functional (ch. 14)
```

:::pitfall
Removing items during a `for-each` throws
`ConcurrentModificationException`. The collection detects that it changed
underneath the loop and refuses to go on. To remove, use
`products.removeIf(p -> p.isBlank())` — one line, no loop, no exception.
:::

## What the project will use

Keep this snippet: it is the in-memory version of what chapter 21 will do
with a real database.

```java title="Toy repository" numbered
Map<Long, String> products = new HashMap<>();
long nextId = 1;

products.put(nextId++, "Keyboard");          // create
String name = products.get(1L);              // read
products.put(1L, "Mechanical keyboard");     // update
products.remove(1L);                         // delete
```

Four operations, one map. When Spring Data JPA comes on stage, it will
offer exactly these four methods — `save`, `findById`, `save`,
`deleteById` — and the difference is that the data survives the machine
being turned off.

:::summary
- `List` for order, `Set` for uniqueness, `Map` for association.
- Declare the interface (`List`), instantiate the implementation
  (`ArrayList`).
- Generics (`<String>`) turn runtime errors into compile errors.
- `getOrDefault` avoids `null`; `List.of` creates an immutable collection.
- Don't remove inside a `for-each`: use `removeIf`.
:::

:::checkpoint
You choose the right collection for the problem, go through all three,
avoid `null` with `getOrDefault` and know why you declare the interface.
:::

:::milestone
The project has a fake "database": a `Map` in memory with the four CRUD
operations. It is the same design that will survive the switch to
PostgreSQL in chapter 19.
:::

:::exercise level=1
Create a `List<String>` with five product names, sort it alphabetically
and print each one on its own line.

:::answer
```java
List<String> names = new ArrayList<>(
        List.of("Mouse", "Cable", "Keyboard", "Monitor", "Webcam"));
Collections.sort(names);
names.forEach(System.out::println);
```
:::

:::exercise level=2
Use a `Map<String, Integer>` to count how many times each word appears in
an array of texts. Hint: `getOrDefault`.

:::answer
```java
Map<String, Integer> counts = new HashMap<>();
for (String word : words) {
    counts.put(word, counts.getOrDefault(word, 0) + 1);
}
```
This is probably the most rewritten snippet in the history of Java. In
chapter 14 it becomes one line with `Collectors.groupingBy` — and you will
find it beautiful precisely because you wrote the long version first.
:::

:::exercise level=3
Given a stock `Map<String, Integer>`, print only the products with fewer
than five units, in alphabetical order of name.

:::answer
```java
new TreeMap<>(stock).forEach((name, qty) -> {
    if (qty < 5) {
        System.out.println(name + ": " + qty);
    }
});
```
`TreeMap` keeps the keys sorted — passing the map to the constructor
already sorts it. Recognizing that the data structure can solve the problem
in place of the algorithm is one of the marks of someone who has been
programming for a while.
:::
