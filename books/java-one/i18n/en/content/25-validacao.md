---
source_hash: ac0e4775dead
title: "Validation"
number: 25
part: p5
kicker: "All input is hostile until proven otherwise — and the proof is an annotation."
goal: >-
  Validate input with Bean Validation, switch validation on with `@Valid`,
  write your own constraint and decide what to validate in each layer.
---

The API from chapter 24 accepts a product with an empty name, a negative
price and a stock of minus two hundred units. It saves it all without
complaint, because nothing checks anything. This chapter closes that door
with four annotations.

## The problem, in one request

:::http title="What the API accepts today"
POST /products
Content-Type: application/json

{
  "name": "",
  "price": -50,
  "quantity": -200
}
---
201 Created

{ "id": 8, "name": "", "price": -50, "quantity": -200 }
:::

A product that doesn't exist in the real world has just come into
existence in your database. And it will show up in the listing, the report
and the invoice.

:::story Minus fifty reais
Mr. Antônio got registration access to put his shop's products on Aurora's
marketplace. He registered eighteen items in one afternoon, alone, without
anyone's help. He was proud of himself.

On the nineteenth, he typed the price into the wrong field — he put the
discount where the amount went — and saved a product for minus fifty
reais.

The API accepted it. The database accepted it. The storefront showed it.
And, since a negative price sorts before all the others, the product ended
up in first place in the "lowest price" listing.

Eleven people bought it. The system calculated, for each of them, a
negative order total — and the payment gateway, which was better written
than Aurora's API, rejected all eleven transactions with the same polite
message.

"He didn't make a mistake," said Marina, at the meeting. "We let him."
:::

## Bean Validation

```xml title="pom.xml"
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

```java title="dto/ProductRequest.java" numbered
package com.store.catalog.product.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;

public record ProductRequest(

        @NotBlank(message = "name is required")
        @Size(max = 120, message = "name: up to 120 characters")
        String name,

        @Size(max = 2000)
        String description,

        @NotNull(message = "price is required")
        @Positive(message = "price must be positive")
        @Digits(integer = 8, fraction = 2)
        BigDecimal price,

        @NotNull
        @PositiveOrZero(message = "stock cannot be negative")
        Integer quantity) {
}
```

And one word in the controller switches everything on:

```java title="ProductController.java" numbered
@PostMapping
public ResponseEntity<ProductResponse> create(
        @Valid @RequestBody ProductRequest data) {
    ...
}
```

:::anatomy title="How validation enters the request's path"
lang: java
code: |
  @PostMapping
  public ResponseEntity<ProductResponse> create(
          @Valid @RequestBody ProductRequest data) {
      return ...;
  }
notes:
  - { line: 3, text: "`@RequestBody` converts the JSON into the record — that already happened." }
  - { line: 3, text: "`@Valid` runs the record's annotations **before** the method executes." }
  - { line: 3, text: "If it fails, the method isn't even called: Spring throws `MethodArgumentNotValidException`." }
  - { line: 4, text: "Inside the method, `data` can be trusted. No validation `if` here." }
:::

## The annotations you will use

| Annotation | Guarantees | For |
|---|---|---|
| `@NotNull` | not null | any type |
| `@NotBlank` | not null nor just spaces | text |
| `@NotEmpty` | not null nor empty | collection, text |
| `@Size(min, max)` | size | text, collection |
| `@Positive` / `@PositiveOrZero` | sign | number |
| `@Min` / `@Max` | range | integer |
| `@DecimalMin` / `@Digits` | range and places | decimal |
| `@Email` | e-mail format | text |
| `@Pattern(regexp)` | regular expression | text |
| `@Past` / `@Future` | moment | date |

Table: The ten that solve almost everything. `@NotBlank` for text and
`@NotNull` for the rest is the practical rule that avoids the most common
mistake.

:::pitfall
`@NotNull` on a `String` accepts `""` — the empty text is not null. For
required text, the right annotation is `@NotBlank`, which rejects null,
empty and "just spaces". Confusing the two is validation defect number one.
:::

## What the client receives

:::http title="Now the API refuses — but the message is still ugly"
POST /products
Content-Type: application/json

{ "name": "", "price": -50, "quantity": -200 }
---
400 Bad Request
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:30:00.000+00:00",
  "status": 400,
  "errors": [ "name is required", "price must be greater than zero" ],
  "path": "/products"
}
:::

The status is already right — `400` is the client's fault. But the body is
Spring's default format, which changes between versions and doesn't say
**which field** failed in a structured way. Chapter 26 standardizes this.

## Your own validation

When the rule doesn't fit an existing annotation, you write your own. Two
pieces: the annotation and the validator.

```java title="ValidSku.java" numbered
@Documented
@Constraint(validatedBy = SkuValidator.class)
@Target({ElementType.FIELD, ElementType.RECORD_COMPONENT})
@Retention(RetentionPolicy.RUNTIME)
public @interface ValidSku {
    String message() default "invalid SKU";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

```java title="SkuValidator.java" numbered
public class SkuValidator
        implements ConstraintValidator<ValidSku, String> {

    private static final Pattern FORMAT =
            Pattern.compile("^[A-Z]{3}-\\d{4}$");

    @Override
    public boolean isValid(String value,
                           ConstraintValidatorContext ctx) {
        if (value == null) {
            return true;      // nullness is @NotNull's business
        }
        return FORMAT.matcher(value).matches();
    }
}
```

```java
@ValidSku
private String sku;     // accepts "KEY-0042"
```

:::key
A validator must **not** check for null. Letting `null` through and
delegating mandatoriness to `@NotNull` is the specification's convention —
it lets you combine annotations without duplicating a rule.
:::

## Where to validate: the three layers

:::diagram type="blocks" caption="Each layer validates something different — and all three are needed."
rows:
  - [{ text: "DTO (@Valid)", note: "format: required, size, sign" }]
  - [{ text: "Service", note: "rules: duplicate name, enough stock" }]
  - [{ text: "Database (NOT NULL, UNIQUE)", note: "the last line of defense" }]
:::

| Layer | Validates | Example |
|---|---|---|
| DTO | the input's shape | "price is required and positive" |
| Service | business rules | "no other product has this name" |
| Database | integrity | `UNIQUE`, `NOT NULL`, `FOREIGN KEY` |

Table: The DTO doesn't query the database; the service doesn't check
format; the database doesn't know the rule. Each in its own place.

:::pitfall
The temptation is to validate uniqueness in the DTO, with a validator that
queries the database. It works and creates two problems: the DTO starts
depending on the repository (and the DTO's test starts needing a
database), and the check is still subject to a race condition — between the
check and the `INSERT`, another request can insert the same name. That is
why the database's `UNIQUE` constraint is not optional.
:::

## Validating nested objects and lists

```java title="@Valid goes down one level if you ask" numbered
public record OrderRequest(
        @NotNull Long customerId,

        @NotEmpty(message = "the order needs items")
        @Valid                     // validates each item in the list
        List<OrderItemRequest> items) {
}

public record OrderItemRequest(
        @NotNull Long productId,
        @NotNull @Positive Integer quantity) {
}
```

Without `@Valid` on the list, `OrderItemRequest`'s annotations are ignored.
It is a silent and common oversight.

:::summary
- Bean Validation validates the input's **shape** through annotations on
  the DTO.
- `@Valid` on the parameter switches validation on — without it, nothing
  runs.
- `@NotBlank` for required text; `@NotNull` for the other types.
- Your own validator doesn't check for null.
- Format in the DTO, rules in the service, integrity in the database.
- `@Valid` on a collection is required to validate its items.
:::

:::checkpoint
You validate input with the ten main annotations, switch it on with
`@Valid`, write your own constraint and know what belongs in each layer.
:::

:::milestone
The API refuses garbage: an empty name, a negative price, a negative stock.
Chapter 17's fourth defect is solved — but the error message the client
receives is still the framework's, and chapter 26 fixes that.
:::

:::exercise level=1
Validate `CategoryRequest`: a required name of at most 80 characters, an
optional description of at most 500.

:::answer
```java
public record CategoryRequest(
        @NotBlank @Size(max = 80) String name,
        @Size(max = 500) String description) {
}
```
:::

:::exercise level=2
Make the `PUT` validate too. Then answer: why does it make sense to use the
same `ProductRequest` in the `POST` and the `PUT`, and in what situation
would it stop making sense?

:::answer
It makes sense because `PUT` replaces the whole resource — the same
required fields. It would stop making sense in an API with partial updates
(`PATCH`), where every field is optional: there, the `POST`'s `@NotBlank`
would reject a legitimate price change that didn't send the name. In that
case there are two DTOs.
:::

:::exercise level=3
Write a class-level validation (not a field one) that guarantees `price`
isn't greater than `1_000_000` when `quantity` is greater than `100`. Hint:
`@Constraint` on `ElementType.TYPE`.

:::answer
The annotation goes on the type and the validator receives the whole
object, which lets it compare two fields:

```java
public class ConsistentBatchValidator implements
        ConstraintValidator<ConsistentBatch, ProductRequest> {
    public boolean isValid(ProductRequest r,
                           ConstraintValidatorContext c) {
        if (r.quantity() == null || r.price() == null) {
            return true;
        }
        BigDecimal cap = new BigDecimal("1000000");
        return r.quantity() <= 100
                || r.price().compareTo(cap) <= 0;
    }
}
```
A validation involving two fields **has to** be class-level. Trying to do
it on a field is the road to a validator that doesn't have access to what
it needs.
:::
