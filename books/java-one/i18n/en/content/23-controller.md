---
source_hash: 7b18bda34f43
title: "Controller"
number: 23
part: p4
kicker: "The thinnest layer of the system — and the only one the client sees."
goal: >-
  Write the complete CRUD with the three layers, return the correct status
  in each case and test the whole API from the command line.
---

With the service ready, the controller becomes what it always should have
been: a translator. It receives HTTP, calls a method, returns HTTP. This
chapter closes the CRUD and is the first point in the book at which the
API is complete from end to end.

## The whole CRUD

```java title="ProductController.java" numbered
package com.store.catalog.product;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<Product> list() {
        return service.list();
    }

    @GetMapping("/{id}")
    public Product find(@PathVariable Long id) {
        return service.find(id);
    }

    @PostMapping
    public ResponseEntity<Product> create(@RequestBody Product newOne) {
        Product saved = service.create(newOne);
        URI location = URI.create("/products/" + saved.getId());
        return ResponseEntity.created(location).body(saved);
    }

    @PutMapping("/{id}")
    public Product update(@PathVariable Long id,
                          @RequestBody Product data) {
        return service.update(id, data);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        service.delete(id);
    }
}
```

Thirty lines for five endpoints. Notice what does **not** exist here: no
`if`, no existence check, no `try/catch`. All of that is another layer's
job.

## Two ways to declare the status

```java title="ResponseEntity or @ResponseStatus" numbered
// 1. when the status varies or there is a header to include
@PostMapping
public ResponseEntity<Product> create(@RequestBody Product newOne) {
    Product saved = service.create(newOne);
    return ResponseEntity
            .created(URI.create("/products/" + saved.getId()))
            .body(saved);
}

// 2. when the status is always the same
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void delete(@PathVariable Long id) {
    service.delete(id);
}
```

`ResponseEntity` gives full control and costs verbosity. `@ResponseStatus`
is declarative and clean, and only works when the response is always the
same. Use the second by default and the first when you need the `Location`
header or more than one possible status.

## The operation that isn't CRUD

Pure CRUD can't handle the business. Decreasing stock is not "updating a
product": it is an **action**.

```java title="A business action as a sub-resource" numbered
@PostMapping("/{id}/stock-withdrawals")
public Product decreaseStock(
        @PathVariable Long id,
        @RequestParam int quantity) {
    return service.decreaseStock(id, quantity);
}
```

:::http title="An action with a resource's name"
POST /products/7/stock-withdrawals?quantity=3
---
200 OK
Content-Type: application/json

{ "id": 7, "name": "Keyboard", "quantity": 9, "status": "ACTIVE" }
:::

:::key
REST talks about **resources** (nouns), not actions (verbs). A path like
`/products/7/withdraw-stock` works and gives away the wrong intent. The
convention that ages best: turn the action into a resource —
`stock-withdrawals` is a record of a withdrawal, and creating that record
is a `POST`.
:::

## The complete API, in one table

| Verb | Path | Success status | Error status |
|---|---|---|---|
| `GET` | `/products` | `200` | — |
| `GET` | `/products/{id}` | `200` | `404` |
| `POST` | `/products` | `201` + `Location` | `400`, `409` |
| `PUT` | `/products/{id}` | `200` | `400`, `404` |
| `DELETE` | `/products/{id}` | `204` | `404` |
| `POST` | `/products/{id}/stock-withdrawals` | `200` | `404`, `409` |

Table: The contract of the book's API. That table is the specification —
and chapter 38 will generate it automatically from the code.

## Proving it works

```bash title="The whole CRUD in six commands"
# create
curl -i -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Keyboard","price":349.90,"quantity":12}'

# list
curl localhost:8080/products

# fetch
curl localhost:8080/products/1

# update
curl -X PUT localhost:8080/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Mechanical keyboard","price":299.90,"quantity":10}'

# decrease stock
curl -X POST \
  "localhost:8080/products/1/stock-withdrawals?quantity=3"

# delete
curl -i -X DELETE localhost:8080/products/1
```

:::checkpoint
If the `POST` returns `201` with `Location`, the `DELETE` returns `204` and
the `GET` of a deleted id returns... well, see the next paragraph. That is
where this chapter reveals the next problem.
:::

:::story Five hundred for everything
The customer's app started getting slow on a Tuesday afternoon.

It wasn't the database. It wasn't the network. It was the app itself,
which tried to fetch a product, got a `500` and — following the rule every
well-written HTTP client follows — tried again. Three times, with
exponential backoff.

The product didn't exist. It never had. An old link, shared in the
WhatsApp group of Mr. Antônio's neighborhood, pointed to id 4821.

Each person who clicked generated three requests instead of one. Two
hundred people clicked.

"The API is lying," said Marina. "It's saying 'I failed', and the client is
doing what you do when a server fails: insist. If it said 'that doesn't
exist', nobody would insist."
:::

## What is still ugly

```bash
curl -i localhost:8080/products/999
```

```text title="Today's response"
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:22:10.123+00:00",
  "status": 500,
  "error": "Internal Server Error",
  "path": "/products/999"
}
```

The service threw `ProductNotFoundException` and nobody translated it.
Spring did what it does with an unknown exception: `500`. And `500` means
"I have a bug", when in fact the client asked for something that doesn't
exist — which is `404`.

:::pitfall
A `500` that should be a `404` is not merely cosmetic. Monitoring counts
`5xx` to fire alarms; a well-written client doesn't repeat a request that
got a `4xx` but does repeat one that got a `5xx`. Returning the wrong
status makes your system lie to the tools that look after it.
:::

What is also missing is handling the two remaining defects from chapter
17: the entity is being exposed directly (chapter 24) and nothing is
validated (chapter 25). The next three chapters exist to close that list.

:::summary
- The controller only translates: no `if`, no `try`, no rules.
- `@ResponseStatus` for a fixed status; `ResponseEntity` when it varies or
  there is a header.
- A business action becomes a sub-resource with `POST`, not a verb in the
  path.
- A business exception without a translator becomes a `500` — and `500` is
  a lie about who got it wrong.
:::

:::checkpoint
You write the five endpoints delegating to the service, model an action as
a sub-resource, choose the correct status and test the complete API with
`curl`.
:::

:::milestone
The API is complete: five endpoints, three layers, data in PostgreSQL. It
works and it still lies about errors, exposes the internal model and
accepts garbage. Part 5 solves all three.
:::

:::exercise level=1
Write the complete `CategoryController`, delegating everything to
`CategoryService`.

:::answer
The same structure as `ProductController`, with `/categories` in the
`@RequestMapping`. If your version came out similar line by line, that is a
good sign: consistency across controllers is what lets someone new to the
project guess where things are.
:::

:::exercise level=2
Add `GET /products?status=ACTIVE` that filters by status when the
parameter comes in, and lists everything when it doesn't.

:::answer
```java
@GetMapping
public List<Product> list(
        @RequestParam(required = false) Status status) {
    return status == null
            ? service.list()
            : service.listByStatus(status);
}
```
The `if` here is acceptable because it is a **protocol** decision (did the
parameter come or not), not a business one. That is the dividing line.
:::

:::exercise level=3
Find out what happens if you send `{"name":"X","price":"abc"}` in the
`POST` and explain why the returned status makes sense — or doesn't.

:::answer
Jackson fails to convert `"abc"` into a `BigDecimal` and Spring returns
`400 Bad Request` with a deserialization message. The status is correct
(the client got it wrong), but the body exposes the library's internal
details — class name, character position. Chapter 26 standardizes this
case too.
:::
