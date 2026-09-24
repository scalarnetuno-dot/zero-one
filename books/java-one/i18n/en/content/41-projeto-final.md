---
source_hash: edf0391b87c0
title: "Final project"
number: 41
part: p10
kicker: "No more spoon-feeding. You get the requirements and build the whole store."
epigraph: "I didn't know what I was doing, so I did it. And then I knew."
epigraph_by: "Programmer's saying, attributed to everyone"
goal: >-
  Build on your own, from scratch, the store's complete API — with the
  modeling, architecture, security and testing decisions made by you.
---

The forty previous chapters showed each piece being fitted in. This
chapter shows nothing: it **asks**.

You get the requirements, as you would from any Cláudia, and you build.
When you get stuck, go back to the chapter that covers the topic — they're
still where they were.

## The requirements

Aurora Comércio wants the whole store, not just the catalog.

```text title="What the system needs to do"
1.  Register, list, find, edit and remove products.
2.  Organize products into categories.
3.  Register customers with a unique email.
4.  Record orders with several items.
5.  Calculate the order total at the moment of purchase.
6.  Decrease stock when the order is confirmed.
7.  Refuse an order with an item without enough stock.
8.  List a customer's orders.
9.  Only ADMIN creates, edits and removes products and categories.
10. A customer sees only their own orders.
```

And the rules that aren't on the list — the ones Cláudia would mention in
the third meeting:

```text title="The business rules"
· A product with zero stock becomes SOLD_OUT automatically.
· A category with products cannot be removed.
· An order item's price is the one at the moment of purchase.
· A confirmed order cannot be changed or canceled.
· A customer's email is unique and doesn't change once created.
```

## The model

:::diagram type="er" caption="Five entities. All of them appeared in the book; now they live together."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name (unique)", "description"]
  - name: "Product"
    fields: ["id (PK)", "name", "price", "quantity", "status", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email (unique)", "created_at"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "status", "total", "created_at"]
  - name: "OrderItem"
    fields: ["id (PK)", "order_id (FK)", "product_id (FK)", "quantity", "unit_price"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
  - { from: "Order", to: "OrderItem", label: "1:N" }
:::

## The API contract

| Verb | Path | Who can |
|---|---|---|
| `POST` | `/auth/login` | everyone |
| `GET` | `/products` | everyone |
| `POST` `PUT` `DELETE` | `/products` | ADMIN |
| `GET` | `/categories` | everyone |
| `POST` `DELETE` | `/categories` | ADMIN |
| `POST` | `/customers` | everyone |
| `POST` | `/orders` | authenticated |
| `GET` | `/orders/mine` | authenticated (only their own) |
| `GET` | `/orders/{id}` | owner or ADMIN |

Table: Nine rows that describe the whole system. Write them before the
code.

## The order, which is the new part

:::http title="Creating an order"
POST /orders
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

{
  "items": [
    { "productId": 7, "quantity": 2 },
    { "productId": 3, "quantity": 1 }
  ]
}
---
201 Created
Location: /orders/15

{
  "id": 15,
  "status": "CONFIRMED",
  "total": 789.70,
  "createdAt": "2026-03-20T14:02:11Z",
  "items": [
    { "productName": "Mechanical keyboard",
      "quantity": 2, "unitPrice": 349.90 },
    { "productName": "Mouse", "quantity": 1, "unitPrice": 89.90 }
  ]
}
:::

:::http title="And when stock runs short"
POST /orders
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

{ "items": [ { "productId": 7, "quantity": 500 } ] }
---
409 Conflict

{
  "status": 409,
  "message": "not enough stock for Mechanical keyboard",
  "path": "/orders"
}
:::

:::key
`POST /orders` is the hardest operation in the project and the one that
best measures whether you understood the book. It involves: input
validation, fetching several entities, a business rule with an exception,
changing the state of another entity, money calculation, and **all of it
in one transaction**. If decreasing the third item fails, the first two
have to go back.
:::

## The suggested order

```text title="Fifteen steps, from empty to done"
 1. Project on Initializr: web, jpa, postgres, security,
    validation, flyway, springdoc, test.
 2. Docker: start PostgreSQL.
 3. Flyway: V1 with the five tables.
 4. Entities and repositories.
 5. Category: service, controller, DTOs, tests.
 6. Product: service, controller, DTOs, tests.
 7. Centralized error handling.
 8. Validation on the input DTOs.
 9. Pagination, sorting and filters on products.
10. Customer: registration with a unique email.
11. User, login and JWT.
12. Authorization by role and by resource owner.
13. Order: the whole transactional operation.
14. Tests: unit, web and repository with Testcontainers.
15. OpenAPI, README and .http file.
```

Notice the order isn't the book's: here you build **one complete slice** at
a time (entity → service → controller → test), instead of a whole layer at
a time. That's how real projects are done, and it's harder — because each
slice requires remembering everything.

## What counts as done

:::checkpoint
A `git clone`, a `docker compose up` and a `./mvnw spring-boot:run` should
be enough for someone else to run the system on their machine without
talking to you. If any step needs explaining, it should be in the
`README.md`.
:::

```text title="The checklist"
□ Compiles and starts with one command.
□ Tests pass and cover the rules, not the getters.
□ POST /orders is truly transactional (test it!).
□ No endpoint returns 500 for a predictable error.
□ No password, secret or token in the repository.
□ Swagger starts and lets you exercise it all, logged in.
□ README explains what it is, how to run and how to test.
□ Commit history tells the evolution, not "tweaks".
```

## Three traps this project has on purpose

:::pitfall
**The order total.** If you calculate it by adding up
`product.getPrice()` at read time, the total of an old order changes when
the product's price changes. The price has to be copied into
`OrderItem.unitPrice` at creation — it's chapter 18's *snapshot*, and most
first implementations get it wrong here.
:::

:::pitfall
**The order listing.** `GET /orders/mine` with each order's items is an
N+1 waiting to happen: one `SELECT` for the orders and one more for each
order's items. Solve it with `@EntityGraph` — and confirm it in the log,
not by feel.
:::

:::pitfall
**Concurrent stock decrease.** Two people buying the last unit at the same
time: both read `quantity = 1`, both pass the check, both decrease. Stock
ends up at `-1`. The solution involves optimistic locking (`@Version` on
the entity) — a topic this book doesn't cover, and that you just discovered
exists on your own. That's how you learn the next level.
:::

:::story Now you're the reviewer
Carlos got the task on a Monday: "the whole store, from scratch, alone".

It wasn't an exercise. Aurora had sold the same system to a second store,
and the second store wanted its own instance — without the four months of
hacks accumulated in the first.

He started with `docker compose`. Then Flyway. By Wednesday, he had
category and product with tests. By Friday, the whole order, transactional,
failing correctly when there wasn't enough stock.

The following Monday, a new developer joined the team: Bruna, who knows
logic, doesn't know Java, and was assigned to "that little API project".

Carlos opened Bruna's *pull request* on Tuesday and, before approving it,
wrote a comment on line 14:

> "Explain out loud, without reading, what this line does."

Marina saw the comment from across the room and said nothing. She just
smiled at the screen, like someone recognizing her own sentence coming
back.
:::

:::summary
- Ten requirements, five business rules and nine routes describe the
  system.
- Build in complete slices: entity, service, controller, test.
- `POST /orders` is the final exam: transaction, rule, exception and money.
- Done means someone else runs it without talking to you.
:::

:::checkpoint
You build a complete REST API from requirements, make the modeling and
architecture decisions on your own, and know how to check whether it's
done.
:::

:::milestone
The book's project is finished. What's left is putting it somewhere other
people can use it — and the last chapter is about that.
:::

:::exercise level=1
Write the project's `README.md` before writing the code. Describe what the
system does, how to run it and how to test it.

:::answer
Writing the README first is an old and underrated technique: it forces you
to describe the product before building it, and almost always reveals a
misunderstood requirement while the change is still free.
:::

:::exercise level=2
Implement `POST /orders` and write the test that proves the transaction
rolls everything back when the third item has no stock.

:::answer
The test needs to check **three** things: the `409` status, that no order
was created, and that the stock of the first two products is still intact.
The third is the one most people forget — and it's the only one that really
tests the transaction.
:::

:::exercise level=3
Find out what optimistic locking is, add `@Version` to the `Product` entity
and write a test with two threads buying the last unit.

:::answer
`@Version` makes Hibernate include the version in the `UPDATE`'s `WHERE`:
if another transaction changed the row in the meantime, zero rows are
affected and you get an `OptimisticLockException`. The two-thread test is
hard to write and is the best way to understand why real systems have
retries. You just stepped outside the scope of this book on your own —
which was exactly its goal.
:::
