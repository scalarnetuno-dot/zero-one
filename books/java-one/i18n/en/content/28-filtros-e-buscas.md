---
source_hash: 480b398eaec7
title: "Filters and search"
number: 28
part: p5
kicker: "Filtering in the database is a query. Filtering in memory is bringing everything and throwing almost everything away."
goal: >-
  Write combinable filters with Specification, understand why `LIKE
  '%term%'` ignores the index and decide between a *query method*,
  `@Query` and a dynamic search.
---

The listing is paginated. What's missing is what everybody asks for next:
searching. And searching is where a well-written API and a slow API part
ways.

## The wrong way, which works for six months

```java title="Filtering after bringing everything" numbered
public List<ProductResponse> search(String term) {
    return repository.findAll().stream()
            .filter(p -> p.getName()
                    .toLowerCase()
                    .contains(term.toLowerCase()))
            .map(ProductResponse::of)
            .toList();
}
```

That brings **every** product from the database into the application's
memory and discards almost all of them. With a hundred products, nobody
notices. With a hundred thousand, every search moves a hundred thousand
rows across the network to return three.

:::key
The question that separates the two implementations: *who filters?* If the
answer is "Java", you have already lost. The database has to filter — it
has indexes, statistics and thirty years of optimizer. Your application has
a `for`.
:::

## A simple filter: the method's name does the job

```java title="ProductRepository.java" numbered
Page<Product> findByNameContainingIgnoreCase(
        String term, Pageable pageable);

Page<Product> findByStatusAndPriceBetween(
        Status status, BigDecimal min, BigDecimal max,
        Pageable pageable);
```

:::http title="The catalog search"
GET /products?name=keyboard&page=0&size=20
---
200 OK

{
  "content": [
    { "id": 3, "name": "Mechanical keyboard", "price": 349.90 }
  ],
  "totalElements": 1
}
:::

It works well while the filters are **fixed**. The problem shows up when
they combine.

## The combinatorial explosion of optional filters

Four optional filters — name, status, minimum price, maximum price —
produce sixteen possible combinations. Writing a method for each is
unfeasible, and writing nested `if`s is worse:

:::compare left="One method per combination" right="A filter that assembles itself"
if (name != null
    && status != null) {
  return repo
    .findByNameAndStatus(...);
}
if (name != null) {
  return repo.findByName(...);
}
// ... 14 more
---
var filter = Specification
    .where(nameContains(name))
    .and(statusEquals(status))
    .and(priceBetween(min, max));

return repo.findAll(
    filter, pageable);
:::

## Specification: the filter as an object

```java title="ProductSpecs.java" numbered
public class ProductSpecs {

    public static Specification<Product> nameContains(String term) {
        return (root, query, cb) -> term == null ? null
                : cb.like(cb.lower(root.get("name")),
                          "%" + term.toLowerCase() + "%");
    }

    public static Specification<Product> statusEquals(Status s) {
        return (root, query, cb) -> s == null ? null
                : cb.equal(root.get("status"), s);
    }

    public static Specification<Product> priceUpTo(BigDecimal cap) {
        return (root, query, cb) -> cap == null ? null
                : cb.lessThanOrEqualTo(root.get("price"), cap);
    }
}
```

:::anatomy title="Why returning `null` is the central trick"
lang: java
code: |
  public static Specification<Product> nameContains(
          String term) {
      return (root, query, cb) ->
          term == null ? null
              : cb.like(root.get("name"), "%" + term + "%");
  }
notes:
  - { line: 3, text: "The Specification is a lambda: it receives the root, the query and a criteria builder." }
  - { line: 4, text: "`null` means *no restriction* — Spring Data simply ignores this filter." }
  - { line: 5, text: "`cb.like` builds the `WHERE` as a tree, not as text: no concatenating SQL." }
:::

The repository needs one more interface:

```java
public interface ProductRepository extends
        JpaRepository<Product, Long>,
        JpaSpecificationExecutor<Product> {
}
```

And the service assembles the filter according to what came in:

```java title="ProductService.java" numbered
@Transactional(readOnly = true)
public Page<ProductResponse> search(ProductFilter f,
                                    Pageable pageable) {
    Specification<Product> spec = Specification
            .where(ProductSpecs.nameContains(f.name()))
            .and(ProductSpecs.statusEquals(f.status()))
            .and(ProductSpecs.priceUpTo(f.maxPrice()));

    return repository.findAll(spec, pageable)
            .map(ProductResponse::of);
}
```

```java title="dto/ProductFilter.java"
public record ProductFilter(
        String name, Status status, BigDecimal maxPrice) {
}
```

The controller receives the record straight from the query string, without
any annotation:

```java
@GetMapping
public Page<ProductResponse> list(
        ProductFilter filter, Pageable pageable) {
    return service.search(filter, pageable);
}
```

:::story A search just like Google's
"The search is bad," said Roberto, on Monday.

"Bad how?"

"I typed 'keyboar' and it found nothing."

"You typed it incomplete."

"Google finds it."

Marina explained that Google has twenty years of investment in indexing,
spelling correction, synonyms and a data center per continent. Roberto
listened to it all and asked the question that had been formed before the
answer:

"But can we do something similar by Thursday?"

They agreed on what was possible: search by part of the name, ignoring
case and accents. It took two days.

On Thursday, Roberto tested "keybboard", with two b's, found nothing, and
mentioned Google again.
:::

## Why `LIKE '%term%'` is slow

```sql
SELECT * FROM product WHERE name LIKE '%keyboard%';
```

A relational database's index is a structure **sorted by the beginning**
of the value. `LIKE 'keyboard%'` uses the index: the database jumps
straight to the range that starts with those letters. `LIKE '%keyboard%'`
doesn't: the term can be in any position, and no sort order helps. The
database reads everything.

:::diagram type="blocks" caption="Three text search strategies, in order of cost and of capability."
flow: false
rows:
  - [{ text: "LIKE 'term%'", note: "uses the index · prefix only" }]
  - [{ text: "LIKE '%term%'", note: "scans the table · any position" }]
  - [{ text: "Full-text (tsvector)", note: "its own index · stemming, ranking" }]
:::

:::tip
Up to a few tens of thousands of rows, `LIKE '%term%'` is perfectly
acceptable — and much simpler than the alternative. When it stops being so,
PostgreSQL offers native *full-text* search with `to_tsvector` and a GIN
index, and only then is it worth considering Elasticsearch. Switching tools
before you have the problem is the most expensive way to optimize.
:::

## Accents: the detail nobody remembers

In Portuguese, as in many languages, `cafe` has to find `café`. PostgreSQL
solves it with the `unaccent` extension:

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;

SELECT * FROM product
WHERE unaccent(lower(name)) LIKE unaccent(lower('%cafe%'));
```

```java title="The same idea with a native @Query" numbered
@Query(value = """
       SELECT * FROM product
       WHERE unaccent(lower(name))
             LIKE unaccent(lower(concat('%', :term, '%')))
       """, nativeQuery = true)
Page<Product> searchIgnoringAccents(@Param("term") String term,
                                    Pageable pageable);
```

:::pitfall
Never build the query by concatenating text:

```java
// NEVER
"SELECT * FROM product WHERE name = '" + term + "'"
```

A term with `'; DROP TABLE product; --` stops being a search and becomes a
statement. That is called **SQL injection** and it is the oldest
vulnerability still taking systems down in production. Always use a
parameter (`:term` or `?`) — the driver sends the value separately from the
command, and it is never interpreted as code.
:::

## Which of the three forms to use

| Situation | Tool |
|---|---|
| one or two fixed filters | a *query method* by name |
| a complex but fixed query | `@Query` (JPQL) |
| optional combinable filters | `Specification` |
| a database-specific feature | native `@Query` |

Table: The table's order is the order in which you should try. Only go up
a step when the previous one doesn't fit.

:::summary
- The database filters; filtering in memory is bringing everything to
  discard almost everything.
- `Specification` builds the `WHERE` in parts and ignores a filter that
  came in null.
- A filter `record` arrives straight from the query string, with no
  annotation.
- `LIKE '%term%'` doesn't use the index; *full-text* only when the volume
  demands it.
- Never concatenate text into SQL: use a parameter.
:::

:::checkpoint
You write combinable filters with `Specification`, know when the method's
name is enough, explain why searching by part of a word is slow and don't
write SQL by concatenation.
:::

:::milestone
End of Part 5. The API lists with pages, sorts, filters by three optional
criteria, refuses garbage and fails honestly. It is an API someone else can
use without talking to you.
:::

:::exercise level=1
Add an optional filter by `status` to the search and test the four
combinations: no filter, name only, status only, both.

:::answer
The fun part is the test with no filter at all: since both
`Specification`s return `null`, the `WHERE` comes out empty and the query
becomes a paginated `findAll`. No `if` was needed for that to happen.
:::

:::exercise level=2
Write a `withStock()` `Specification` that filters `quantity > 0` and
combine it with the others. Then turn on `show-sql` and check the generated
`WHERE`.

:::answer
```java
public static Specification<Product> withStock() {
    return (root, query, cb) ->
            cb.greaterThan(root.get("quantity"), 0);
}
```
In the log you see a single `SELECT` with every condition joined by
`and` — proof that the filter went to the database and not to the `for`.
:::

:::exercise level=3
Measure. Register fifty thousand products, run the partial-word search with
`EXPLAIN ANALYZE` and then create a GIN index with `pg_trgm`. Compare.

:::answer
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_product_name_trgm
    ON product USING gin (name gin_trgm_ops);
```
`pg_trgm` indexes trigrams — three-letter pieces — and is one of the few
ways to make `LIKE '%term%'` use an index. The plan stops being a
`Seq Scan` and becomes a `Bitmap Index Scan`. Measuring before and after is
the habit that separates optimization from superstition.
:::
