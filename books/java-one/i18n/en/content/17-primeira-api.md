---
source_hash: 7d5a0eaa2014
title: "The first API"
number: 17
part: p3
kicker: "Four verbs, one path and a decision about what to return in each case."
goal: >-
  Write endpoints for the five CRUD verbs, receive data through the path,
  the query and the body, and choose the correct status code.
---

This is the chapter in which the project becomes an API. The data still
lives in a `Map` in memory — the database arrives in chapter 19 — but the
HTTP contract born here is the same one that goes live in chapter 42.

## HTTP on one page

Every request has four parts, and you are going to touch all four:

:::anatomy title="The parts of an HTTP request"
lang: http
code: |
  POST /products?notify=true HTTP/1.1
  Content-Type: application/json
  Authorization: Bearer eyJhbGci...

  {"name": "Keyboard", "price": 349.90}
notes:
  - { line: 1, text: "**Verb**: the intent. `POST` creates, `GET` reads, `PUT` replaces, `DELETE` deletes." }
  - { line: 1, text: "**Path**: the resource. A plural noun, with no verb inside." }
  - { line: 1, text: "**Query**: optional parameters, after the `?`." }
  - { line: 2, text: "**Headers**: metadata — content type, authentication, language." }
  - { line: 5, text: "**Body**: the data. Only in `POST`, `PUT` and `PATCH`." }
:::

And every response has a three-digit number that sums it all up:

| Range | Meaning | You will use |
|---|---|---|
| `2xx` | it worked | `200`, `201`, `204` |
| `4xx` | the client got it wrong | `400`, `401`, `403`, `404`, `409` |
| `5xx` | the server got it wrong | `500` (and you will want to avoid it) |

Table: The first digit tells the story. If you return `200` with an error
message inside, you are lying to the client.

## The controller

```java title="ProductController.java" numbered
package com.store.catalog.product;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final Map<Long, Product> db = new LinkedHashMap<>();
    private final AtomicLong sequence = new AtomicLong();

    @GetMapping
    public List<Product> list() {
        return new ArrayList<>(db.values());
    }
}
```

:::anatomy title="The annotations that turn a method into an endpoint"
lang: java
code: |
  @RestController
  @RequestMapping("/products")
  public class ProductController {

      @GetMapping
      public List<Product> list() {
          return new ArrayList<>(db.values());
      }
  }
notes:
  - { line: 1, text: "`@RestController` = `@Controller` + `@ResponseBody`: the return value becomes the response body." }
  - { line: 2, text: "`@RequestMapping` defines the path prefix for every method in the class." }
  - { line: 5, text: "`@GetMapping` with no argument inherits the class's path: `GET /products`." }
  - { line: 6, text: "The return value is converted to JSON by Jackson — without a line of conversion from you." }
:::

:::trivia
That automatic conversion to JSON is done by Jackson, a library that is not
part of Spring. It comes in through `spring-boot-starter-web` and is chosen
by autoconfiguration: if it is on the classpath, Spring uses it. It is Boot's
philosophy in action — the decision has already been made, and you only
argue if you want to.
:::

## Reading data: three sources, three annotations

```java title="Where each piece of data comes from" numbered
// 1. from the path:  GET /products/7
@GetMapping("/{id}")
public Product find(@PathVariable Long id) {
    return db.get(id);
}

// 2. from the query:  GET /products/search?name=keyboard
@GetMapping("/search")
public List<Product> searchByName(@RequestParam String name) {
    return db.values().stream()
            .filter(p -> p.getName().contains(name))
            .toList();
}

// 3. from the body:  POST /products
@PostMapping
public Product create(@RequestBody Product newOne) {
    newOne.setId(sequence.incrementAndGet());
    db.put(newOne.getId(), newOne);
    return newOne;
}
```

| Annotation | Reads from | Required? |
|---|---|---|
| `@PathVariable` | a piece of the path | yes, it is part of the route |
| `@RequestParam` | the query string | optional with `required = false` |
| `@RequestBody` | the body | yes, and it needs a `Content-Type` |

Table: The three entry doors for data in a controller.

## The complete CRUD

```java title="ProductController.java (the rest)" numbered
@PutMapping("/{id}")
public ResponseEntity<Product> update(
        @PathVariable Long id,
        @RequestBody Product data) {

    Product current = db.get(id);
    if (current == null) {
        return ResponseEntity.notFound().build();
    }
    data.setId(id);
    db.put(id, data);
    return ResponseEntity.ok(data);
}

@DeleteMapping("/{id}")
public ResponseEntity<Void> delete(@PathVariable Long id) {
    if (db.remove(id) == null) {
        return ResponseEntity.notFound().build();
    }
    return ResponseEntity.noContent().build();
}
```

`ResponseEntity` is the object that carries **status, headers and body**.
Use it whenever the response can vary — and in a real API it almost always
can.

## The five dialogues, in order

:::http title="Create — returns 201 and the created resource"
POST /products
Content-Type: application/json

{
  "name": "Mechanical keyboard",
  "price": 349.90,
  "stock": 12
}
---
201 Created
Location: /products/1

{
  "id": 1,
  "name": "Mechanical keyboard",
  "price": 349.90,
  "stock": 12
}
:::

:::http title="Fetch one — 200 when it exists"
GET /products/1
---
200 OK
Content-Type: application/json

{ "id": 1, "name": "Mechanical keyboard", "price": 349.90 }
:::

:::http title="Fetch one that doesn't exist — 404, no body"
GET /products/999
---
404 Not Found
:::

:::http title="Delete — 204, also without a body"
DELETE /products/1
---
204 No Content
:::

:::key
`201` on creation, with the `Location` header pointing to the new resource.
`204` on deletion, because there is nothing to return. `404` when the id
does not exist. Those three details separate an API that respects the
protocol from one that just returns `200` for everything.
:::

```java title="Returning 201 correctly" numbered
@PostMapping
public ResponseEntity<Product> create(@RequestBody Product newOne) {
    newOne.setId(sequence.incrementAndGet());
    db.put(newOne.getId(), newOne);

    URI location = URI.create("/products/" + newOne.getId());
    return ResponseEntity.created(location).body(newOne);
}
```

## Testing from the command line

```bash title="curl: the HTTP client that's already installed"
curl localhost:8080/products

curl -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Mouse","price":89.90,"stock":5}'

curl -i localhost:8080/products/999
```

`-i` shows the headers and the status — and it is what you will use to
check whether the `404` really is a `404`. Chapter 39 introduces tools with
an interface; for now, `curl` is enough and teaches more.

:::pitfall
Forgetting `-H "Content-Type: application/json"` on the `POST` returns
`415 Unsupported Media Type`. The message is obscure and the cause is
simple: without the header, Spring does not know which converter to use to
read the body.
:::

:::story Can we show it to the customer?
`GET /products` answered with an empty list — `[]` — and Carlos spent ten
seconds staring at those two characters with disproportionate emotion.

He registered a product with `curl`. He ran it again. The list had one
item.

Roberto, who had developed a sixth sense for showing up at exactly these
moments, showed up.

"Did it work?"

"It worked."

"So can we show it to the customer on Thursday?"

Marina, without looking up from her monitor:

"We can show it to the customer on Thursday if the customer accepts that
the data disappears whenever someone restarts the application."

"And when does someone restart the application?"

"Every time we deploy."

Roberto was silent for three seconds — again, an eternity — and said he
would reschedule for the following week.
:::

## What is wrong with this version

This controller works and has four serious defects, all on purpose:

1. **it keeps the data in memory** — restarting erases everything
   (chapters 19 to 21);
2. **the controller holds the rules** — filtering and numbering are not its
   job (chapter 22);
3. **it exposes the entity directly** — the client sees the internal design
   of the database (chapter 24);
4. **it validates nothing** — `price: -5` gets in (chapter 25).

Recognizing all four now is what will make the next chapters feel
inevitable rather than bureaucratic.

:::summary
- `@RestController` + `@RequestMapping` define the class; `@GetMapping` and
  its family define each route.
- `@PathVariable`, `@RequestParam` and `@RequestBody` are the three entry
  doors.
- `ResponseEntity` controls status, headers and body.
- `201` + `Location` on create, `204` on delete, `404` when it doesn't
  exist.
:::

:::checkpoint
You write the five CRUD endpoints, read data from the three sources, choose
the right status and test everything with `curl`.
:::

:::milestone
The API answers the five verbs on `/products`. The data dies when the
process ends and the controller does things that aren't its job — the two
problems Part 4 solves.
:::

:::exercise level=1
Add `GET /products/count` that returns the number of registered products.
Then answer: why shouldn't it be a separate endpoint in a well-designed
API?

:::answer
```java
@GetMapping("/count")
public long count() {
    return db.size();
}
```
Because a count is **metadata about a list**, not a resource. The correct
REST form is to return the total in a header or inside the paginated
response — which is exactly what chapter 27 does with `Page`.
:::

:::exercise level=2
Make the `POST` reject a product without a name, returning
`400 Bad Request`. Then compare your code with chapter 25's `@NotBlank`
annotation.

:::answer
```java
if (newOne.getName() == null || newOne.getName().isBlank()) {
    return ResponseEntity.badRequest().build();
}
```
It works and it doesn't scale: with ten fields you would have ten `if`s in
every endpoint. Chapter 25 swaps all of this for an annotation on the field
and a `@Valid` in the signature.
:::

:::exercise level=3
Implement `PATCH /products/{id}` that changes **only** the fields sent.
Think about how to distinguish "field absent" from "field sent as null".

:::answer
The distinction requires a type that knows the difference — usually a DTO
with `Optional` fields or a `Map<String, Object>`. That is why many mature
APIs simply don't offer `PATCH`: the semantics of partial updates are
harder to get right than they seem, and a well-documented `PUT` solves 95%
of the cases.
:::
