---
source_hash: a7a80fc4abf9
title: "Repository"
number: 21
part: p4
kicker: "An empty interface that gains twenty methods. It is worth understanding where they come from before trusting them."
goal: >-
  Create a repository with `JpaRepository`, use the ready-made methods,
  write *query methods* by name and explain who implements the interface.
---

This chapter has the best cost-benefit ratio in the book: three lines of
code deliver complete access to the database.

```java title="ProductRepository.java" numbered
package com.store.catalog.product;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository
        extends JpaRepository<Product, Long> {
}
```

That's it. An interface, with no declared method, with no class
implementing it. And from here on you can save, find, list, count and
delete products.

## What just happened

At startup, Spring Data finds every interface that extends
`JpaRepository`, generates a class at run time that implements each method
and registers the result as a bean. The `@Repository` is implicit.

:::diagram type="blocks" caption="You declare the interface; Spring Data manufactures the implementation at startup."
rows:
  - [{ text: "ProductRepository", note: "the interface you wrote" }]
  - [{ text: "SimpleJpaRepository", note: "Spring Data's generic implementation" }]
  - [{ text: "EntityManager", note: "the JPA API" }]
  - [{ text: "Hibernate → JDBC → PostgreSQL", note: "the real SQL" }]
:::

:::anatomy title="The two parameters JpaRepository requires"
lang: java
code: |
  public interface ProductRepository
          extends JpaRepository<Product, Long> {
  }
notes:
  - { line: 2, text: "`Product` is the entity this repository manages." }
  - { line: 2, text: "`Long` is the primary key's type — the same as the `@Id` field." }
  - { line: 2, text: "Getting the second parameter wrong (`Integer` instead of `Long`) only fails at startup, with a long message." }
:::

## The methods that come for free

```java title="All of this exists without you writing it" numbered
Product saved = repository.save(newOne);        // INSERT or UPDATE
Optional<Product> one = repository.findById(1L); // SELECT by id
List<Product> all = repository.findAll();       // SELECT *
long total = repository.count();
boolean exists = repository.existsById(1L);
repository.deleteById(1L);
repository.saveAll(productList);                // batch
```

Three details that save hours of debugging:

`save` does `INSERT` **or** `UPDATE`: if the id is null, it inserts; if it
has a value, it updates. It is convenient and hides a gotcha — saving an
object with an id that doesn't exist in the database generates an `INSERT`
with that id, not an error.

`findById` returns an `Optional` (chapter 13), not `null`. The API is
communicating in the type that the product may not exist.

`deleteById` of a nonexistent id throws
`EmptyResultDataAccessException` — it is not a silent "did nothing".

## Query methods: the query born from the name

Here is the feature that looks like magic and is just convention:

```java title="ProductRepository.java" numbered
public interface ProductRepository
        extends JpaRepository<Product, Long> {

    List<Product> findByStatus(Status status);

    List<Product> findByNameContainingIgnoreCase(String term);

    List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);

    Optional<Product> findByNameIgnoreCase(String name);

    boolean existsByName(String name);

    long countByStatus(Status status);

    List<Product> findByStatusOrderByPriceDesc(Status status);
}
```

Spring Data **reads the method's name**, breaks it into keywords and builds
the query. `findByNameContainingIgnoreCase` becomes:

```sql
SELECT * FROM product WHERE upper(name) LIKE upper('%' || ? || '%')
```

| Word in the name | Becomes in SQL |
|---|---|
| `findBy`, `countBy`, `existsBy` | `SELECT`, `COUNT`, `EXISTS` |
| `Containing` | `LIKE %...%` |
| `IgnoreCase` | `upper(field) = upper(?)` |
| `Between`, `GreaterThan`, `LessThan` | comparators |
| `And`, `Or` | connectors |
| `OrderBy...Desc` | `ORDER BY ... DESC` |
| `Top10`, `First` | `LIMIT` |

Table: The vocabulary of *query methods*. The complete list is in the
Spring Data documentation, and it fits on one page.

:::pitfall
The name has to match the **entity's field**, not the database column.
`findByCreatedAt` works; `findByCreated_at` doesn't. And if you get the
field name wrong, the error shows up at startup with the message `No
property 'xyz' found for type 'Product'` — which is great: it is a typo
caught before the first request.
:::

:::pitfall
A method name is good until it isn't. When you find yourself writing
`findByStatusAndPriceBetweenAndQuantityGreaterThanOrderByNameAsc`, the
limit has been passed. From there on use `@Query` — and that is the subject
of chapter 28.
:::

## `@Query`: when the name isn't enough

```java title="JPQL and native SQL" numbered
@Query("SELECT p FROM Product p WHERE p.quantity = 0")
List<Product> outOfStock();

@Query("""
       SELECT p FROM Product p
       WHERE p.status = :status
         AND p.price <= :cap
       ORDER BY p.price
       """)
List<Product> cheapByStatus(
        @Param("status") Status status,
        @Param("cap") BigDecimal cap);

@Query(value = "SELECT * FROM product WHERE price > :min",
       nativeQuery = true)
List<Product> above(@Param("min") BigDecimal min);
```

The first and second use **JPQL**: similar to SQL, but written in terms of
**entities and fields** (`Product p`, `p.price`), not tables and columns.
The third is native SQL, useful for PostgreSQL-specific features.

:::trivia
That multi-line text between `"""` is a *text block*, from Java 15. Before
it, a five-line JPQL was a concatenation with `+` and spaces at the end of
each piece — and forgetting a space produced
`WHERE p.status = :statusORDER BY`. A syntax feature that erased a whole
category of bug.
:::

## Testing the repository for real

```java title="ProductRepositoryTest.java" numbered
@DataJpaTest
class ProductRepositoryTest {

    @Autowired
    ProductRepository repository;

    @Test
    void shouldFindByStatus() {
        repository.save(new Product("Keyboard",
                new BigDecimal("349.90"), 12));

        List<Product> active =
                repository.findByStatus(Status.ACTIVE);

        assertThat(active).hasSize(1);
    }
}
```

`@DataJpaTest` starts **only** the data layer, on an in-memory database,
and undoes everything at the end of each test. Chapter 37 goes deeper —
including why testing on a database different from production is an idea
that sends the bill.

:::summary
- `JpaRepository<Entity, IdType>` delivers the complete CRUD without an
  implementation.
- Spring Data generates the class at startup; the `@Repository` is
  implicit.
- `save` inserts or updates; `findById` returns an `Optional`.
- *Query methods* are born from the method's name and fail at startup if
  the field doesn't exist.
- A name that's too long is a sign the query deserves `@Query`.
:::

:::checkpoint
You create a repository, use the ready-made methods, write queries through
the method name, know when to switch to `@Query` and test with
`@DataJpaTest`.
:::

:::milestone
The API talks to the database. The data survives a restart — chapter 17's
defect number one is solved. What's left is taking the business rules out
of the controller.
:::

:::exercise level=1
Create `CategoryRepository` and write a *query method* that finds a
category by name, ignoring case.

:::answer
```java
public interface CategoryRepository
        extends JpaRepository<Category, Long> {
    Optional<Category> findByNameIgnoreCase(String name);
}
```
The return type is `Optional` because searching for a specific name may
find nothing — and the signature warns the caller of that.
:::

:::exercise level=2
Write a method that returns the five most expensive products with
available stock, using only the method name.

:::answer
```java
List<Product> findTop5ByQuantityGreaterThanOrderByPriceDesc(int min);
```
Called with `0`. It is the limit of what the name still communicates well —
one more field and the `@Query` version becomes more readable.
:::

:::exercise level=3
Write, with `@Query`, a query that returns the total stock value (sum of
price × quantity) of all active products. Notice that the result is not an
entity.

:::answer
```java
@Query("""
       SELECT SUM(p.price * p.quantity) FROM Product p
       WHERE p.status = com.store.catalog.product.Status.ACTIVE
       """)
BigDecimal totalStockValue();
```
The return type is a `BigDecimal`, not a `Product` — and it may come back
**null** if there is no active product, because in SQL the `SUM` of an
empty set is `NULL`. Handling that is the service's responsibility, which
is the next chapter.
:::
