---
source_hash: 1cc4d0141f18
title: "DTOs"
number: 24
part: p4
kicker: "The client doesn't need to know how your table is designed. And you don't want it to depend on that."
goal: >-
  Separate the entity from the contract with input and output records,
  convert between the two and list three concrete problems that direct
  exposure causes.
---

So far `ProductController` returns the `Product` entity. It works, it is
less code and it creates a coupling that charges dearly. This chapter is
about a border.

## Three concrete problems

**1. Renaming a column breaks the client.** If `name` becomes `title` in
the database, the JSON changes with it — and the phone app that has been
in the store for six months stops working.

**2. You expose what you didn't want to.** Every new field in the entity
shows up in the response automatically. One day someone adds
`purchaseCost` and the store's margin becomes public.

**3. The input accepts what it shouldn't.** `POST /products` with
`{"id": 9999}` tries to save an id chosen by the client. With
`{"createdAt": "1990-01-01"}`, it rewrites the creation date.

:::pitfall
Problem 3 has a name and a history: *mass assignment*. In 2012, someone
used it on GitHub to add himself as an administrator of a public repository
— through a field the API accepted unintentionally. The fix is not to
validate more: it is to **not accept** the field.
:::

:::story The field nobody wanted to show
The field was called `purchaseCost` and was added to the entity on a
Tuesday, for an internal margin report.

The report was ready. Nobody remembered that the API returned the whole
entity.

On Thursday, a developer from a partner — one of those who integrate the
catalog into a price comparison site — sent a friendly e-mail asking
whether the `purchaseCost` field really was the purchase cost, because, if
it was, it made it easy to calculate Aurora's margin on every item.

The e-mail was polite. It was also the worst e-mail Roberto received that
quarter.
:::

:::art caption="Exposing the entity means publishing every column anyone adds in the future."
src="expor-a-entidade-e-publicar-toda-coluna-que-alguem-acrescentar-no-futuro.png"
Charge editorial minimalista: janela de resposta JSON desenhada como se fosse
a vitrine de uma loja, com vários campos visíveis em prateleiras; um deles,
destacado em vermelho, diz "custoDeCompra". Do lado de fora da vitrine, um
desenvolvedor de outra empresa observa com sorriso discreto e uma calculadora
na mão. Do lado de dentro, um gerente de camisa social tenta cobrir aquele
campo com as duas mãos. Fundo branco, poucos elementos, humor seco, estética
editorial de tecnologia.
:::

## Two records, two contracts

```java title="dto/ProductRequest.java" numbered
package com.store.catalog.product.dto;

import java.math.BigDecimal;

public record ProductRequest(
        String name,
        String description,
        BigDecimal price,
        Integer quantity) {
}
```

```java title="dto/ProductResponse.java" numbered
public record ProductResponse(
        Long id,
        String name,
        String description,
        BigDecimal price,
        Integer quantity,
        Status status,
        Instant createdAt) {

    public static ProductResponse of(Product p) {
        return new ProductResponse(
                p.getId(),
                p.getName(),
                p.getDescription(),
                p.getPrice(),
                p.getQuantity(),
                p.getStatus(),
                p.getCreatedAt());
    }
}
```

Notice the asymmetry: the **input** has no `id`, `status` or `createdAt` —
those three don't belong to the client. The **output** has everything the
client needs and nothing else.

:::key
Input and output are different contracts and deserve different types.
Using the same record for both is the elegant version of the same mistake:
either the input accepts fields it shouldn't, or the output hides fields it
should show.
:::

:::diagram type="blocks" caption="The DTO is the border: the JSON's shape stops being the table's shape."
rows:
  - [{ text: "Client", note: "JSON" }]
  - [{ text: "ProductRequest / ProductResponse", note: "public, stable contract" }]
  - [{ text: "Product (entity)", note: "internal design, free to change" }]
  - [{ text: "product table", note: "columns" }]
:::

## The conversion

```java title="ProductService.java (with DTOs at the border)" numbered
@Transactional(readOnly = true)
public List<ProductResponse> list() {
    return repository.findAll().stream()
            .map(ProductResponse::of)
            .toList();
}

@Transactional
public ProductResponse create(ProductRequest data) {
    if (repository.existsByNameIgnoreCase(data.name())) {
        throw new DuplicateProductException(data.name());
    }
    Product newOne = new Product(
            data.name(), data.price(), data.quantity());
    newOne.setDescription(data.description());
    return ProductResponse.of(repository.save(newOne));
}
```

`ProductResponse::of` is chapter 14's method reference doing the work: a
stream of entities becomes a stream of responses in one line.

:::pitfall
Where to convert is a design decision with two schools. Converting in the
**service** (as here) keeps the controller trivial and makes the service
speak the contract's vocabulary. Converting in the **controller** keeps the
service pure in domain terms, and is the preferred choice in larger
projects. Pick one and be consistent: what really hurts is half in each
place.
:::

## Part 4's final controller

```java title="ProductController.java" numbered
@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<ProductResponse> list() {
        return service.list();
    }

    @GetMapping("/{id}")
    public ProductResponse find(@PathVariable Long id) {
        return service.find(id);
    }

    @PostMapping
    public ResponseEntity<ProductResponse> create(
            @RequestBody ProductRequest data) {
        ProductResponse created = service.create(data);
        return ResponseEntity
                .created(URI.create("/products/" + created.id()))
                .body(created);
    }
}
```

:::http title="The public contract, now stable"
POST /products
Content-Type: application/json

{
  "name": "Mechanical keyboard",
  "description": "ABNT2 layout, brown switch",
  "price": 349.90,
  "quantity": 12
}
---
201 Created
Location: /products/7

{
  "id": 7,
  "name": "Mechanical keyboard",
  "description": "ABNT2 layout, brown switch",
  "price": 349.90,
  "quantity": 12,
  "status": "ACTIVE",
  "createdAt": "2026-03-14T18:22:10Z"
}
:::

Notice: the client sent four fields and received seven. The `id`, the
`status` and the `createdAt` were decided by the server — that is how it
should be.

## Adjusting the JSON without touching the entity

```java title="Jackson annotations on the DTO" numbered
public record ProductResponse(
        Long id,
        @JsonProperty("productName") String name,
        BigDecimal price,
        @JsonInclude(JsonInclude.Include.NON_NULL)
        String description) {
}
```

Since the DTO is a class of your own, you can rename fields, hide nulls and
format dates without any of it touching the entity or the database. That
freedom is the concrete gain of the separation.

:::trivia
The acronym DTO comes from *Data Transfer Object*, cataloged by Martin
Fowler in 2002 for a different problem: reducing the number of remote calls
in distributed systems. The name stayed, the reason changed. Today nobody
uses a DTO to save calls — they use it to decouple the contract from the
model.
:::

## When the DTO isn't worth it

Be honest about the cost: two classes, two conversions and more lines per
endpoint. In a small internal project, with a single client you maintain
yourself, exposing the entity is a defensible decision.

The deciding question: **is there someone on the other side you don't
control?** If the answer is yes — a published app, a partner, a different
team — the DTO stops being optional.

:::summary
- Exposing the entity couples the client to the database, leaks fields and
  accepts fields it shouldn't.
- Input and output are different contracts: two records.
- The input has no `id`, `status` or system dates.
- Convert in a single place, and always the same one.
- Jackson annotations live on the DTO, never on the entity.
:::

:::checkpoint
You separate the entity from the contract with records, convert with a
factory method, justify the separation with three concrete problems and
know when it doesn't pay off.
:::

:::milestone
End of Part 4. The API has a complete CRUD, three layers, a PostgreSQL
database and a public contract that isn't the table's design. Three of the
four defects from chapter 17 are solved — what's left is validation, which
opens Part 5.
:::

:::exercise level=1
Write `CategoryRequest` and `CategoryResponse` and adjust
`CategoryController` to use them.

:::answer
```java
public record CategoryRequest(String name, String description) { }

public record CategoryResponse(Long id, String name,
                               String description) {
    public static CategoryResponse of(Category c) {
        return new CategoryResponse(c.getId(), c.getName(),
                c.getDescription());
    }
}
```
:::

:::exercise level=2
Create `ProductSummary`, a record with only `id`, `name` and `price`, for
the listing. Explain the gain.

:::answer
A `GET /products` of a thousand items stops carrying description, date and
status — maybe half the bytes. In a catalog listing opened on a mobile
network, that is the difference between fast and slow. It is common for an
API to have a "summary" DTO for lists and a "full" one for the detail.
:::

:::exercise level=3
Send `POST /products` with `{"name":"X","price":10,"id":9999}` and observe
what happens to the `id` field. Then explain why this is the correct
result.

:::answer
The field is **ignored**: `ProductRequest` doesn't declare it, and Jackson
discards unknown properties by default. The product is created with the
database sequence's id. Correct because the server is the authority on the
identity of its resources — accepting an id from the client would open the
door to collisions and to overwriting an existing record.
:::
