---
source_hash: eec1d3cb7a38
title: "Real JPA problems"
number: 30
part: p6
kicker: "The ORM does exactly what you told it to. The problem is that you told it without knowing."
epigraph: "All non-trivial abstractions, to some degree, are leaky."
epigraph_by: "Joel Spolsky, the law of leaky abstractions"
goal: >-
  Diagnose the N+1 problem from the log, choose between `JOIN FETCH` and
  `@EntityGraph`, and explain `LazyInitializationException` without
  guesswork.
---

This is the chapter in which many people give up on JPA — and it is also
the chapter that, once understood, turns JPA into a tool. Every problem
here has the same root: **Java hides when a query happens**.

## The N+1 problem

```java title="It looks harmless" numbered
List<Product> products = repository.findAll();

for (Product p : products) {
    System.out.println(p.getName() + " — "
            + p.getCategory().getName());
}
```

```text title="The log with show-sql on"
select ... from product
select ... from category where id = 1
select ... from category where id = 2
select ... from category where id = 1
select ... from category where id = 3
... 11,996 more times
```

**One** query to bring the list, plus **N** queries — one per item — to
fetch each one's category. Hence the name: N+1.

:::diagram type="sequence" caption="Every `getCategory()` on a LAZY field is a trip to the database."
actors:
  - { id: s, name: "Service" }
  - { id: h, name: "Hibernate" }
  - { id: d, name: "Database" }
messages:
  - { from: s, to: h, text: "findAll()" }
  - { from: h, to: d, text: "select * from product" }
  - { from: d, to: h, text: "11,000 rows", dashed: true }
  - { from: s, to: h, text: "getCategory() of item 1" }
  - { from: h, to: d, text: "select ... category" }
  - { from: s, to: h, text: "getCategory() of item 2" }
  - { from: h, to: d, text: "select ... category" }
:::

:::key
N+1 is invisible in Java code. `p.getCategory().getName()` looks like a
field access and is a database query. The only way to see it is **reading
the SQL log** — and that is why this book has asked for `show-sql=true`
since chapter 20.
:::

## The three solutions

```java title="1. JOIN FETCH — brings everything in one query" numbered
@Query("""
       SELECT p FROM Product p
       JOIN FETCH p.category
       """)
List<Product> findAllWithCategory();
```

```java title="2. @EntityGraph — the same, without writing JPQL" numbered
@EntityGraph(attributePaths = "category")
List<Product> findAll();
```

```java title="3. Don't navigate: fetch only what the screen shows" numbered
@Query("""
       SELECT new com.store.catalog.product.dto.ProductSummary(
              p.id, p.name, c.name)
       FROM Product p JOIN p.category c
       """)
List<ProductSummary> summary();
```

The third is the fastest of the three, because it doesn't even assemble
entities: the database returns exactly the three columns the screen needs
and Hibernate builds the record directly.

| Solution | Queries | When |
|---|---|---|
| `JOIN FETCH` | 1 | you need the complete entity |
| `@EntityGraph` | 1 | the same, declaratively |
| DTO projection | 1 | the screen only reads |
| nothing | N+1 | never on purpose |

Table: Three ways to solve the same problem — and the fourth row, which is
the natural state of anyone who hasn't looked at the log.

:::pitfall
`JOIN FETCH` with pagination is a specific trap: Hibernate warns
`firstResult/maxResults specified with collection fetch; applying in
memory` and brings **the whole table** to paginate in Java. With a
collection (`@OneToMany`), use `@EntityGraph` with `Pageable` or make two
queries — one for the ids, paginated, and one for the data.
:::

## `LazyInitializationException`

```java title="The error that only shows up outside the transaction" numbered
@Transactional(readOnly = true)
public Product find(Long id) {
    return repository.findById(id).orElseThrow();
}

// in the controller, OUTSIDE the transaction:
product.getCategory().getName();
// → LazyInitializationException: could not initialize proxy
```

A `LAZY` field is not the category: it is a **proxy**, an empty object that
knows how to fetch the category when someone asks. It can only fetch while
the Hibernate session is open — that is, inside the transaction. Outside
it, the proxy has no one to ask.

:::diagram type="flowchart" caption="The proxy only works while the session exists."
nodes:
  - { id: t1, type: start,    text: "opens transaction" }
  - { id: q,  type: process,  text: "loads Product (category = proxy)" }
  - { id: t2, type: process,  text: "closes transaction" }
  - { id: g,  type: decision, text: "getCategory()?" }
  - { id: ok, type: process,  text: "inside: queries the database" }
  - { id: er, type: process,  text: "outside: LazyInitializationException" }
edges:
  - { from: t1, to: q }
  - { from: q,  to: t2 }
  - { from: t2, to: g }
  - { from: g,  to: ok, label: "before" }
  - { from: g,  to: er, label: "after" }
:::

The three ways out, in order of quality:

1. **Convert to a DTO inside the transaction** — chapter 24's solution,
   which happens to solve this already.
2. **`JOIN FETCH`** when the navigation is always needed.
3. **`open-in-view`** — the setting that keeps the session open until the
   end of the request. It is Spring Boot's default, and it is a bad idea.

:::pitfall
`spring.jpa.open-in-view=true` comes **on** by default. It makes the
`LazyInitializationException` disappear — and, along with it, makes the N+1
happen during JSON serialization, far from any code of yours. Turn it off:

```properties
spring.jpa.open-in-view=false
```

You will break a few screens the next day. Every break is a place where
your code was querying the database without knowing.
:::

:::story Four thousand queries for one screen
The catalog screen got slow in a strange way: fast at the beginning of the
month, unbearable at the end.

Carlos opened the production log and took six minutes to find the request
— not because it was hard, but because there were four thousand and
thirty-two lines of `select ... from category` between its start and its
end.

The chart matched the story: the slowness grew with the number of
registered products. It was the N+1 growing along with the catalog.

The interesting part wasn't the defect. It was the discussion that came
afterwards.

Roberto wanted to switch databases. A vendor had called offering a
solution "optimized for high volume". The chart in the presentation was
very convincing.

Marina asked for fifteen minutes and one annotation: `@EntityGraph`.

The screen went from 4,032 queries to one. The response time dropped from
eleven seconds to forty milliseconds. The vendor kept calling for two more
weeks.
:::

## Transactions: where they start and where they end

```java title="Two operations, one transaction" numbered
@Transactional
public Order finish(Long orderId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));

    for (OrderItem item : order.getItems()) {
        Product p = item.getProduct();
        p.decreaseStock(item.getQuantity());
    }

    order.setStatus(OrderStatus.CONFIRMED);
    return order;
}
```

If decreasing the third item's stock fails for insufficient stock, the
exception goes up, the transaction undoes **everything** — including the
two decreases already made — and the order stays pending. That
"all or nothing" behavior is what justifies the annotation.

:::pitfall
An open transaction is a locked resource: while it lives, a connection
from the *pool* is reserved. A `@Transactional` around an HTTP call to an
external service — which can take thirty seconds — exhausts the pool in
minutes. Rule: **no slow input and output inside a transaction**.
:::

## The JPA-in-production checklist

```properties title="application.properties — what's worth it"
spring.jpa.open-in-view=false
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.properties.hibernate.jdbc.batch_size=30
logging.level.org.hibernate.SQL=DEBUG
```

And the habit worth more than the four lines: **open the SQL log after
writing any new query** and count how many lines showed up. If it's more
than one, you have something to understand before moving on.

:::summary
- N+1 is invisible in Java and obvious in the SQL log.
- `JOIN FETCH`, `@EntityGraph` or a DTO projection solve it — in that
  order of effort.
- `LazyInitializationException` means accessing a proxy outside the
  transaction.
- `open-in-view` hides the problem and is the default: turn it off.
- A transaction is all or nothing; never put an external call inside it.
:::

:::checkpoint
You identify an N+1 by reading the log, choose the appropriate solution,
explain what a LAZY proxy is and know why `open-in-view` turned off is
better.
:::

:::milestone
End of Part 6. The API has relationships and queries that don't multiply
trips to the database. It is also still completely open: anyone with the
URL can delete any product. Part 7 closes the door.
:::

:::exercise level=1
Turn on `show-sql`, call `GET /products` with ten products from different
categories and count the queries. Then add `@EntityGraph` and count again.

:::answer
Eleven queries become one. It is the cheapest experiment in this book and
the one that most changes how you write queries from here on.
:::

:::exercise level=2
Cause a `LazyInitializationException` on purpose: return the `Product`
entity straight from the controller with `open-in-view=false` and a LAZY
field. Then fix it with a DTO.

:::answer
The DTO fix is not a patch: it is the right way. Converting inside the
transaction guarantees that everything the JSON needs has already been
loaded, and the controller starts working with an object that has no
connection to the database whatsoever.
:::

:::exercise level=3
Write the `ProductSummary(Long id, String name, String category)`
projection with `SELECT new` and compare the generated SQL with the
`JOIN FETCH` one. Which brings less data?

:::answer
The projection brings three columns; the `JOIN FETCH` brings every column
of both tables, including `description`, which can have two thousand
characters per row. In a hundred-item listing, the difference is
megabytes. Bringing only what the screen shows is the most underrated
optimization in data access.
:::
