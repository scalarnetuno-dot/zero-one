---
source_hash: 3bb73ba7cc4a
title: "Pagination and sorting"
number: 27
part: p5
kicker: "`GET /products` with a million items is a denial-of-service attack you wrote yourself."
goal: >-
  Paginate and sort a listing with `Pageable`, understand the cost of
  `OFFSET` and return pagination metadata to the client.
---

Chapter 23's `GET /products` returns everything. With a hundred products
nobody notices; with a hundred thousand, the query is slow, the JSON is
thirty megabytes and the server's memory climbs to the limit. This chapter
solves it with two parameters.

## `Pageable`: Spring already knows how

```java title="ProductController.java" numbered
@GetMapping
public Page<ProductResponse> list(Pageable pageable) {
    return service.list(pageable);
}
```

```java title="ProductService.java" numbered
@Transactional(readOnly = true)
public Page<ProductResponse> list(Pageable pageable) {
    return repository.findAll(pageable)
            .map(ProductResponse::of);
}
```

No new annotation. Spring recognizes the `Pageable` parameter, reads
`page`, `size` and `sort` from the query string and builds the object:

:::http title="Three parameters you didn't have to declare"
GET /products?page=0&size=10&sort=price,desc
---
200 OK

{
  "content": [
    { "id": 7, "name": "27-inch monitor", "price": 1899.00 },
    { "id": 3, "name": "Keyboard", "price": 349.90 }
  ],
  "pageable": { "pageNumber": 0, "pageSize": 10 },
  "totalElements": 342,
  "totalPages": 35,
  "first": true,
  "last": false,
  "numberOfElements": 2
}
:::

`Page` is not just the list: it is the list **plus** the metadata the
client needs to draw the navigation. The `.map()` in the service converts
each entity into a DTO without losing any of those fields.

## The SQL that comes out of it

```sql title="Two queries, not one" numbered
SELECT * FROM product
ORDER BY price DESC
LIMIT 10 OFFSET 0;

SELECT count(*) FROM product;
```

The second query exists to fill `totalElements`. If you don't need the
total — and many screens don't — swap `Page` for `Slice` and save one count
on every request:

```java
Slice<Product> findByStatus(Status status, Pageable pageable);
```

| Type | Brings | Cost |
|---|---|---|
| `List` | everything | dangerous |
| `Slice` | page + "is there a next one?" | one query |
| `Page` | page + total + number of pages | two queries |

Table: `Page` is the comfortable default. `Slice` is the conscious choice
when counting is expensive.

## Set the default and the cap

```java title="ProductController.java" numbered
@GetMapping
public Page<ProductResponse> list(
        @PageableDefault(size = 20, sort = "name")
        Pageable pageable) {
    return service.list(pageable);
}
```

```properties title="application.properties"
spring.data.web.pageable.default-page-size=20
spring.data.web.pageable.max-page-size=100
```

:::pitfall
Without `max-page-size`, `GET /products?size=1000000` brings back the
problem you just solved — and now with a parameter anyone can discover. The
cap is not a configuration detail: it is a security measure.
:::

:::story The Black Friday of GET /products
At midnight on Black Friday, eleven thousand products were registered and
the app was doing exactly what it had been programmed to do: asking for
the product list.

`GET /products`. No parameters at all. No limit at all. Eleven thousand
items, with full descriptions, every time a screen opened.

The first minute had four thousand screen openings.

The API didn't go down for lack of CPU. It went down from memory: each
request loaded eleven thousand objects to build a thirty-megabyte JSON,
and the garbage collector started working harder than the application.

Marina shipped the fix at 12:19 a.m. — a `Pageable` in the controller and
a cap of a hundred items per page. Three lines.

Roberto asked, at the retrospective, why those three lines hadn't been
there from the start.

It was the best question he asked all quarter.
:::

## The hidden cost of `OFFSET`

:::diagram type="flowchart" caption="The database discards everything before the OFFSET — and charges for it."
nodes:
  - { id: q,   type: io,      text: "LIMIT 10 OFFSET 100000" }
  - { id: ord, type: process, text: "sorts the first 100,010" }
  - { id: sk,  type: process, text: "discards 100,000" }
  - { id: r,   type: start,   text: "returns 10" }
edges:
  - { from: q,   to: ord }
  - { from: ord, to: sk }
  - { from: sk,  to: r }
:::

`OFFSET` is not a shortcut: the database has to sort and go through
everything that comes before to know where to start. Page 1 is instant;
page 10,000 is slow, always, in any relational database.

The alternative is called **cursor pagination** (or *keyset
pagination*):

:::compare left="By offset" right="By cursor"
SELECT * FROM product
ORDER BY id
LIMIT 10
OFFSET 100000;
---
SELECT * FROM product
WHERE id > 100000
ORDER BY id
LIMIT 10;
:::

The second uses the index and has a constant cost, no matter how far along
you are. The price is not being able to "jump to page 500" — you can only
go forward and back. For infinite feeds and exports, it is the right
choice.

:::trivia
That is why services like Twitter, Stripe and GitHub don't have numbered
pages in their APIs: they return a `next_cursor`. The decision is not
aesthetic. With billions of records, `OFFSET` would make the last page
unreachable.
:::

## Sorting and what it can expose

```text title="All of these forms work"
?sort=name                    → name ascending
?sort=price,desc              → price descending
?sort=status&sort=price,desc  → two criteria
```

:::pitfall
`sort` accepts **any field name of the entity** — including one you didn't
want to exist in the public contract. `?sort=purchaseCost` doesn't return
the field, but it reveals that it exists. In public APIs, validate the list
of sortable fields:

```java
private static final Set<String> SORTABLE =
        Set.of("name", "price", "createdAt");
```
:::

And another trap, a silent one:

:::pitfall
Paginating **without** explicit sorting doesn't guarantee a stable order.
Without `ORDER BY`, the database can return the rows in any order, and the
same record can show up on page 1 and on page 2 — or on neither. Always
sort by something unique (or end the sort with `id`).
:::

## The listing's final contract

| Parameter | Default | Cap |
|---|---|---|
| `page` | `0` | — |
| `size` | `20` | `100` |
| `sort` | `name,asc` | allowed fields |

Table: The project's listing. Documenting it is chapter 38's job.

:::summary
- `Pageable` as a controller parameter reads `page`, `size` and `sort` on
  its own.
- `Page` brings the total and the number of pages at the cost of an extra
  query; `Slice` doesn't.
- Set a default size and a **cap** — the cap is security.
- `OFFSET` gets more expensive as the page advances; a cursor has a
  constant cost.
- Pagination without a stable sort returns inconsistent results.
:::

:::checkpoint
You paginate and sort a listing, choose between `Page` and `Slice`, limit
the page size and can explain why page 10,000 is slow.
:::

:::milestone
The project's listing is paginated, sortable and capped. What's missing is
the ability to search — and that is the next chapter.
:::

:::exercise level=1
Paginate the category listing with a default size of 10, sorted by name.

:::answer
```java
@GetMapping
public Page<CategoryResponse> list(
        @PageableDefault(size = 10, sort = "name")
        Pageable pageable) {
    return service.list(pageable);
}
```
:::

:::exercise level=2
Instead of `Page`, return a record of your own with only `content`,
`page`, `size` and `totalElements`. Explain why that can be worth it.

:::answer
```java
public record PageResponse<T>(
        List<T> content, int page, int size, long totalElements) {

    public static <T> PageResponse<T> of(Page<T> p) {
        return new PageResponse<>(p.getContent(),
                p.getNumber(), p.getSize(), p.getTotalElements());
    }
}
```
It is worth it because Spring Data's `Page` JSON exposes the framework's
internal structure (`pageable.sort.sorted`, `unpaged`…) and **has changed
format between versions**. A DTO of your own is a contract you control —
chapter 24's lesson, applied to pagination.
:::

:::exercise level=3
Implement cursor pagination for `GET /products`: receive `afterId` and
return the next 20. Compare the generated SQL with the offset version's.

:::answer
```java
@Query("""
       SELECT p FROM Product p
       WHERE p.id > :afterId
       ORDER BY p.id
       """)
List<Product> page(@Param("afterId") Long afterId,
                   Pageable limit);
```
Called with `PageRequest.ofSize(20)`. The SQL becomes
`WHERE id > ? ORDER BY id LIMIT 20` — one index access, no discarding. What
you lose: knowing how many pages exist, and the ability to jump to an
arbitrary page.
:::
