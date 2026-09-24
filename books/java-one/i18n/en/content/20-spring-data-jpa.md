---
source_hash: c96c680175ba
title: "Spring Data JPA"
number: 20
part: p4
kicker: "A layer that translates objects into table rows. Powerful, convenient and full of traps this book is going to name."
goal: >-
  Annotate a class as an entity, map fields and enums, understand what
  Hibernate is and what JPA is, and know when the automatic translation
  gets in the way.
---

You have a Java class and an SQL table describing the same thing. Writing
the conversion between the two by hand — `SELECT` into `Product`,
`Product` into `INSERT` — is repetitive, mechanical work. JPA does it.

## Three names, three roles

| Name | What it is |
|---|---|
| **JPA** | the specification: the annotations and the contract |
| **Hibernate** | the implementation that runs it (Boot's default) |
| **Spring Data JPA** | the layer that saves you from writing the repository |

Table: You program against JPA, Hibernate does the work, and Spring Data
spares you the repetitive code. Confusing the three is common and gets in
the way when you search for a solution online.

:::trivia
Before JPA (2006), each project wrote its own data access layer, or used
the raw JDBC API — in which a three-column query took twenty lines with
`ResultSet`, `try/finally` and manual type conversion. Hibernate appeared
in 2001 as an independent project and became so dominant that the official
specification was written **afterwards**, on top of it. It is one of the
few cases in which the standard followed the practice.
:::

## The entity

```java title="Product.java" numbered
package com.store.catalog.product;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "product")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 120)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal price;

    @Column(nullable = false)
    private Integer quantity = 0;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Status status = Status.ACTIVE;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    protected Product() { }   // required by JPA

    public Product(String name, BigDecimal price, Integer quantity) {
        this.name = name;
        this.price = price;
        this.quantity = quantity;
    }

    // getters and setters omitted
}
```

:::anatomy title="The annotations that do the translation"
lang: java
code: |
  @Entity
  @Table(name = "product")
  public class Product {
      @Id
      @GeneratedValue(strategy = GenerationType.IDENTITY)
      private Long id;

      @Enumerated(EnumType.STRING)
      private Status status;
  }
notes:
  - { line: 1, text: "`@Entity` tells Hibernate: this class becomes a table row." }
  - { line: 2, text: "`@Table` names the table. Without it, the class name is used." }
  - { line: 4, text: "`@Id` marks the primary key — mandatory in every entity." }
  - { line: 5, text: "`IDENTITY` delegates generation to the database's `BIGSERIAL`." }
  - { line: 8, text: "`EnumType.STRING` writes `'ACTIVE'`. Never use `ORDINAL`." }
:::

:::pitfall
`@Enumerated(EnumType.ORDINAL)` — which is the **default** when you declare
nothing — writes the enum's **position**: `0`, `1`, `2`. If someone inserts
a new value in the middle of the list, every record in the database starts
meaning something else, silently. Always declare `EnumType.STRING`. This
is, without competition, the most expensive defect in this chapter.
:::

## Why the entity needs an empty constructor

That `protected Product() { }` looks useless and is mandatory: Hibernate
creates the object through reflection, knowing nothing about your
constructors, and then fills in the fields. `protected` is enough — it
does not need to be public, and that way nobody creates an empty product by
accident.

It is also why **an entity cannot be a `record`** (chapter 12): a record
has neither an empty constructor nor setters.

:::story The day INACTIVE became ON_SALE
The enum had three values and was stored as a number in the database — the
default configuration, which nobody had consciously chosen.

Zero was `ACTIVE`, one was `INACTIVE`, two was `SOLD_OUT`.

In March, Cláudia asked for a new status: `ON_SALE`. Carlos opened the enum
and added the value where it made sense semantically — between `ACTIVE`
and `INACTIVE`, because a product on sale is closer to active than to
inactive.

The deploy was on Wednesday. On Thursday, four thousand inactive products
showed up in the storefront with a sale tag.

Nobody had changed any data. The numbers in the database were exactly the
same. What had changed was what they meant.
:::

## An entity's life cycle

:::diagram type="flowchart" caption="An entity's four states — and why a change can be saved without you asking."
nodes:
  - { id: novo,  type: io,      text: "new Product(): transient" }
  - { id: save,  type: process, text: "save(): managed" }
  - { id: dirty, type: process, text: "setPrice(): dirty" }
  - { id: flush, type: process, text: "flush: automatic UPDATE" }
  - { id: fim,   type: start,   text: "end of transaction: detached" }
edges:
  - { from: novo,  to: save }
  - { from: save,  to: dirty }
  - { from: dirty, to: flush }
  - { from: flush, to: fim }
:::

This is the behavior that most surprises newcomers: inside a transaction,
changing a **managed** object generates an `UPDATE` at the end, even
without calling `save`. Hibernate compares the current state with what it
read from the database (*dirty checking*) and writes the difference.

:::key
A managed entity is not an ordinary object: it is an object Hibernate is
watching. That is why chapter 24 insists on not letting the entity leave
the service layer — outside it, nobody knows whether a change will become
an `UPDATE` or not.
:::

## Checking the mapping

```properties title="application.properties"
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
```

`validate` compares the entity with the table at startup and **fails if
they don't match**. It is the setting you want: if you added a field to the
class and forgot the column, you find out in two seconds, not in
production.

```text title="Output with show-sql, when saving"
Hibernate:
    insert into product
        (created_at, description, name, price, quantity, status)
    values
        (?, ?, ?, ?, ?, ?)
```

:::tip
Keep `show-sql=true` throughout development. Seeing the SQL Hibernate
generates is the habit that avoids chapter 30's N+1 problem — and it is the
only way to notice that a simple listing fired 200 queries.
:::

## When the automatic translation gets in the way

JPA is great for per-entity operations — loading a product, saving,
deleting. It is bad at:

- **reports** with aggregation and joins across five tables;
- **bulk updates** (`UPDATE product SET status = 'INACTIVE'` on a million
  rows);
- queries in which the **shape of the result** is not an entity.

For those cases, Spring offers `JdbcTemplate` and native queries — and
using SQL directly is not defeat, it is choosing the right tool. A mature
application has both.

:::history
The organized criticism of this kind of tool has a name: the
*object-relational impedance mismatch*. Objects have inheritance and
references; tables have keys and joins. The translation works in 90% of
cases and charges the remaining 10% with interest — the famous "the ORM is
slow" which, almost always, is the ORM doing exactly what it was told.
:::

:::term Managed entity
An object Hibernate is tracking inside a transaction. Changes to it are
written automatically at the end.
:::

:::summary
- JPA is the specification; Hibernate runs it; Spring Data saves code.
- `@Entity`, `@Id`, `@GeneratedValue` and `@Column` do the mapping.
- Always use `@Enumerated(EnumType.STRING)`.
- An entity needs an empty constructor — and that is why it can't be a
  `record`.
- Inside the transaction, changing a managed entity generates an automatic
  `UPDATE`.
- `ddl-auto=validate` and `show-sql=true` are the healthy defaults.
:::

:::checkpoint
You annotate a complete entity, know which annotation does what, explain
an entity's life cycle and recognize the cases in which JPA is not the
right tool.
:::

:::milestone
`Product` is now a JPA entity mapped to the `product` table. What is
missing is someone to run the queries — and the next chapter shows that
this is an empty interface.
:::

:::exercise level=1
Annotate the `Category` class as an entity, with a unique, required
`name`. Confirm with `ddl-auto=validate` that the table matches the class.

:::answer
```java
@Entity
@Table(name = "category")
public class Category {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 80)
    private String name;

    protected Category() { }
}
```
:::

:::exercise level=2
Add an `updatedAt` field that is filled in automatically on every change.
Look up `@PreUpdate`.

:::answer
```java
@Column(name = "updated_at")
private Instant updatedAt;

@PreUpdate
void onUpdate() {
    this.updatedAt = Instant.now();
}
```
`@PreUpdate` and `@PrePersist` are life-cycle hooks. Useful, with a catch:
they run inside Hibernate, which means they don't run when you do a bulk
update through native SQL.
:::

:::exercise level=3
Change `@Enumerated` to `ORDINAL`, save two products, add a value in the
**middle** of the enum and read the data again. Describe what happened.

:::answer
The products stored as `1` (which was `INACTIVE`) start being read as the
new value that took position 1. No error, no warning: just data that
changed meaning. It is the kind of defect only discovered by a customer
complaining, months later — and fixing it requires a hand-written migration
script.
:::
