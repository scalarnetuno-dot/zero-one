---
source_hash: 696ff888e952
title: "Service"
number: 22
part: p4
kicker: "The layer where the rules live. If it is empty, the rules are scattered somewhere else — and you will find them the hard way."
goal: >-
  Move the business rules from the controller into a service, inject the
  repository through the constructor and use `@Transactional` knowing what
  it does.
---

The controller from chapter 17 knew HTTP **and** knew rules. While the rule
is "put it in the map", that passes. When it becomes "don't allow two
products with the same name, and when decreasing stock mark it sold out if
it reaches zero", the controller stops being a translator and becomes the
whole system.

## The three responsibilities, separated

:::diagram type="blocks" caption="Each layer only knows the one below — and does only one thing."
rows:
  - [{ text: "Controller", note: "HTTP: path, status, JSON" }]
  - [{ text: "Service", note: "business rules and transactions" }]
  - [{ text: "Repository", note: "queries and writes" }]
:::

| Layer | Knows | Doesn't know |
|---|---|---|
| Controller | verb, path, status | rules, database |
| Service | rules, order of operations | HTTP, JSON |
| Repository | SQL, entity | rules, HTTP |

Table: The smell test: if the `Service` imports anything from `http`, the
separation has been broken.

:::key
The `Service` must not have any `import` from `org.springframework.http`
or `jakarta.servlet`. If it does, the business rules have come to depend on
the protocol — and testing them will require starting a server.
:::

## The service

```java title="ProductService.java" numbered
package com.store.catalog.product;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProductService {

    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    @Transactional(readOnly = true)
    public List<Product> list() {
        return repository.findAll();
    }

    @Transactional(readOnly = true)
    public Product find(Long id) {
        return repository.findById(id)
                .orElseThrow(() -> new ProductNotFoundException(id));
    }

    @Transactional
    public Product create(Product newOne) {
        if (repository.existsByNameIgnoreCase(newOne.getName())) {
            throw new DuplicateProductException(newOne.getName());
        }
        return repository.save(newOne);
    }

    @Transactional
    public Product update(Long id, Product data) {
        Product current = find(id);
        current.setName(data.getName());
        current.setDescription(data.getDescription());
        current.setPrice(data.getPrice());
        current.setQuantity(data.getQuantity());
        return current;        // no save: managed entity
    }

    @Transactional
    public void delete(Long id) {
        Product current = find(id);
        repository.delete(current);
    }
}
```

Five methods and four decisions worth explaining.

:::anatomy title="The decisions hidden in five methods"
lang: java
code: |
  @Transactional(readOnly = true)
  public Product find(Long id) {
      return repository.findById(id)
              .orElseThrow(() ->
                  new ProductNotFoundException(id));
  }

  @Transactional
  public Product update(Long id, Product data) {
      Product current = find(id);
      current.setPrice(data.getPrice());
      return current;
  }
notes:
  - { line: 1, text: "`readOnly = true` tells the database there will be no writes: it allows optimization." }
  - { line: 4, text: "`orElseThrow` turns absence into a named exception — chapter 26 converts it into a `404`." }
  - { line: 10, text: "It reuses `find`: the \"doesn't exist\" rule lives in a single place." }
  - { line: 12, text: "No `save`: the entity is managed and the `UPDATE` goes out at the end of the transaction." }
:::

## `@Transactional`: what this annotation really does

It wraps the method in a database transaction: it opens one before,
confirms it (`commit`) if it ends well, undoes it (`rollback`) if an
exception escapes.

:::diagram type="sequence" caption="Spring intercepts the call and takes care of the beginning and the end."
actors:
  - { id: c, name: "Controller" }
  - { id: p, name: "Proxy" }
  - { id: s, name: "Service" }
  - { id: d, name: "Database" }
messages:
  - { from: c, to: p, text: "create(product)" }
  - { from: p, to: d, text: "BEGIN" }
  - { from: p, to: s, text: "create(product)" }
  - { from: s, to: d, text: "INSERT" }
  - { from: s, to: p, text: "returns", dashed: true }
  - { from: p, to: d, text: "COMMIT" }
  - { from: p, to: c, text: "saved product", dashed: true }
:::

Notice the **proxy**. Spring does not modify your method: it creates an
object that wraps your service and intercepts the call. That explains the
annotation's two most common gotchas.

:::pitfall
**An internal call doesn't go through the proxy.** If `create()` calls
`this.validate()` and only `validate()` has `@Transactional`, the
annotation is ignored — the call never left the object, so the proxy saw
nothing. The solution is to put the transaction on the public method that
starts the operation.
:::

:::pitfall
**Only an *unchecked* exception rolls back the transaction, by default.**
An `IOException` (checked) escaping from a `@Transactional` method makes
Spring commit the transaction anyway. To change that:
`@Transactional(rollbackFor = Exception.class)`.
:::

:::story The transaction that didn't exist
The stock decrease worked. Except when it didn't.

Once in every two hundred times, the product left the stock and the order
was not saved. The customer paid, the item disappeared from the shelf and
the order didn't exist anywhere.

Carlos had put `@Transactional` on the method. It was there, written,
visible, with the correct import.

Marina opened the file and pointed to line 61: the public method called
`this.decreaseAndProcess()`, a private method in the same class — which
was where the annotation was.

"The annotation isn't a promise the method makes," she said. "It's a
promise someone makes *around* it. If the call doesn't leave the object,
there's nobody around."

Carlos spent the rest of the day understanding what a proxy is. It was the
most useful afternoon of that month.
:::

## The business exceptions

```java title="ProductNotFoundException.java" numbered
package com.store.catalog.product;

public class ProductNotFoundException extends RuntimeException {
    public ProductNotFoundException(Long id) {
        super("product not found: " + id);
    }
}
```

```java title="DuplicateProductException.java" numbered
public class DuplicateProductException extends RuntimeException {
    public DuplicateProductException(String name) {
        super("a product already exists with the name: " + name);
    }
}
```

Two five-line classes. They know nothing about HTTP — and that is exactly
why the service can throw them. In chapter 26, a central translator
converts the first into a `404` and the second into a `409`.

## The real business rule

So far the service only orchestrates. The rule shows up when the business
has a decision:

```java title="An operation with a rule" numbered
@Transactional
public Product decreaseStock(Long id, int quantity) {
    Product product = find(id);

    if (quantity <= 0) {
        throw new IllegalArgumentException("invalid quantity");
    }
    if (product.getQuantity() < quantity) {
        throw new InsufficientStockException(
                product.getQuantity(), quantity);
    }

    product.setQuantity(product.getQuantity() - quantity);
    if (product.getQuantity() == 0) {
        product.setStatus(Status.SOLD_OUT);
    }
    return product;
}
```

This is the layer that justifies the architecture. Notice that the rule
"zero stock becomes sold out" exists in **one** place. If it lived in the
controller, every new endpoint that decreased stock would need to repeat
it — and one of them would forget.

:::tip
A well-written service reads like the description of the business: find,
validate, change, decide. If, reading it out loud, you hear "take the
request, extract the parameter, build the JSON", the code is in the wrong
layer.
:::

## The controller, now lean

```java title="ProductController.java (only what's its own)" numbered
@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping("/{id}")
    public Product find(@PathVariable Long id) {
        return service.find(id);
    }
}
```

Four useful lines per endpoint. The controller has become what it should
be: a translator between HTTP and a method call.

:::compare left="Before (ch. 17)" right="After"
@GetMapping("/{id}")
Product find(
    @PathVariable Long id) {
  Product p =
      db.get(id);
  if (p == null) {
    return null;
  }
  return p;
}
---
@GetMapping("/{id}")
Product find(
    @PathVariable Long id) {
  return service.find(id);
}
:::

:::summary
- The controller translates HTTP; the service decides; the repository
  persists.
- The service imports nothing from HTTP — that is what keeps it testable.
- `@Transactional` opens and closes a transaction through a proxy: an
  internal call doesn't count.
- A *checked* exception escaping doesn't roll back the transaction by
  default.
- Inside the transaction, changing a managed entity makes `save`
  unnecessary.
:::

:::checkpoint
You move the rules into the service, inject the repository through the
constructor, use `@Transactional` knowing what it does and throw business
exceptions without mentioning HTTP.
:::

:::milestone
Chapter 17's defect number two is solved: the rules have left the
controller. The API has three layers and a stock rule that lives in a
single place.
:::

:::exercise level=1
Write `CategoryService` with `list`, `find` and `create`, rejecting a
duplicate name.

:::answer
```java
@Service
public class CategoryService {
    private final CategoryRepository repository;

    public CategoryService(CategoryRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public Category create(Category newOne) {
        repository.findByNameIgnoreCase(newOne.getName())
                .ifPresent(c -> {
                    throw new DuplicateCategoryException(c.getName());
                });
        return repository.save(newOne);
    }
}
```
:::

:::exercise level=2
Add `adjustPrice(Long id, BigDecimal percent)` to `ProductService`,
rejecting an adjustment that takes the price to zero or below.

:::answer
```java
@Transactional
public Product adjustPrice(Long id, BigDecimal percent) {
    Product p = find(id);
    BigDecimal factor = BigDecimal.ONE
            .add(percent.divide(new BigDecimal("100")));
    BigDecimal newPrice = p.getPrice().multiply(factor);
    if (newPrice.signum() <= 0) {
        throw new IllegalArgumentException("invalid adjustment");
    }
    p.setPrice(newPrice.setScale(2, RoundingMode.HALF_UP));
    return p;
}
```
That `setScale` with `HALF_UP` at the end is not a detail: without it, the
result of the multiplication carries decimal places the database will
truncate its own way. Rounding is a business decision, not the driver's.
:::

:::exercise level=3
Imagine that creating a product must also record an event in an audit
table. Write the method and explain what happens if writing the audit
fails.

:::answer
```java
@Transactional
public Product create(Product newOne) {
    Product saved = repository.save(newOne);
    audit.record("CREATE", saved.getId());
    return saved;
}
```
If the audit throws an *unchecked* exception, the transaction undoes
**both** operations: the product is not created. That may be the desired
behavior or a disaster (losing the sale because the log failed). It is a
business decision, and the way to separate them is to publish an event and
handle it in another transaction — a subject this book leaves as the next
step.
:::
