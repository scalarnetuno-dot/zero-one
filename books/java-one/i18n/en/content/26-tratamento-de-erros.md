---
source_hash: 767c174d772f
title: "Error handling"
number: 26
part: p5
kicker: "The error is part of the contract. An API that answers 500 to everything is an API that doesn't tell what happened."
goal: >-
  Translate business exceptions into HTTP statuses with
  `@ControllerAdvice`, build a standardized error response and choose
  between `400`, `404`, `409` and `500` with judgment.
---

Chapter 23 ended with a problem: `GET /products/999` returns `500`. The
service threw `ProductNotFoundException` and nobody translated it. This
chapter writes the translator — one class, and every error in the API
takes shape.

## One place to translate everything

```java title="shared/exception/ApiExceptionHandler.java" numbered
package com.store.catalog.shared.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<ApiError> notFound(
            ProductNotFoundException e, HttpServletRequest req) {
        return response(HttpStatus.NOT_FOUND, e.getMessage(), req);
    }

    @ExceptionHandler(DuplicateProductException.class)
    public ResponseEntity<ApiError> conflict(
            DuplicateProductException e, HttpServletRequest req) {
        return response(HttpStatus.CONFLICT, e.getMessage(), req);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiError> badRequest(
            IllegalArgumentException e, HttpServletRequest req) {
        return response(HttpStatus.BAD_REQUEST, e.getMessage(), req);
    }

    private ResponseEntity<ApiError> response(
            HttpStatus status, String message,
            HttpServletRequest req) {
        ApiError body = new ApiError(
                Instant.now(), status.value(),
                status.getReasonPhrase(), message,
                req.getRequestURI(), List.of());
        return ResponseEntity.status(status).body(body);
    }
}
```

:::anatomy title="How Spring finds the right translator"
lang: java
code: |
  @RestControllerAdvice
  public class ApiExceptionHandler {

      @ExceptionHandler(ProductNotFoundException.class)
      public ResponseEntity<ApiError> notFound(
              ProductNotFoundException e) {
          return ...;
      }
  }
notes:
  - { line: 1, text: "`@RestControllerAdvice` applies to **every** controller in the application." }
  - { line: 4, text: "`@ExceptionHandler` registers this method for that type of exception." }
  - { line: 4, text: "The lookup is by the most specific type: a `RuntimeException` handler only steps in if there is no closer one." }
  - { line: 6, text: "Spring injects the exception itself as a parameter — and, if you ask, the request too." }
:::

## The standardized error response

```java title="shared/exception/ApiError.java" numbered
public record ApiError(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path,
        List<FieldError> fields) {

    public record FieldError(String field, String message) { }
}
```

:::http title="The same 404 as before, now honest"
GET /products/999
---
404 Not Found
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:35:00Z",
  "status": 404,
  "error": "Not Found",
  "message": "product not found: 999",
  "path": "/products/999",
  "fields": []
}
:::

## A validation error with the field that failed

Chapter 25 left the validation message in the framework's format. Now it
fits the same mold:

```java title="ApiExceptionHandler.java (excerpt)" numbered
@ExceptionHandler(MethodArgumentNotValidException.class)
public ResponseEntity<ApiError> validation(
        MethodArgumentNotValidException e,
        HttpServletRequest req) {

    List<ApiError.FieldError> fields = e.getBindingResult()
            .getFieldErrors().stream()
            .map(f -> new ApiError.FieldError(
                    f.getField(), f.getDefaultMessage()))
            .toList();

    ApiError body = new ApiError(
            Instant.now(), 400, "Bad Request",
            "invalid data", req.getRequestURI(), fields);

    return ResponseEntity.badRequest().body(body);
}
```

:::http title="A validation error with the problem's address"
POST /products
Content-Type: application/json

{ "name": "", "price": -50 }
---
400 Bad Request

{
  "status": 400,
  "message": "invalid data",
  "path": "/products",
  "fields": [
    { "field": "name",  "message": "name is required" },
    { "field": "price", "message": "price must be positive" }
  ]
}
:::

That response is usable by a client: the app can paint exactly the `price`
field red and show the message next to it. It is the difference between an
API that refuses and an API that teaches.

## Choosing the status

| Status | Means | Example in the project |
|---|---|---|
| `400` | malformed or invalid request | negative price, broken JSON |
| `401` | I don't know who you are | missing token (chapter 32) |
| `403` | I know who you are, and you can't | a user trying to delete (chapter 33) |
| `404` | doesn't exist | nonexistent id |
| `409` | conflict with the current state | duplicate name, insufficient stock |
| `422` | semantically invalid | optional; many use `400` |
| `500` | **I** have a bug | anything unforeseen |

Table: The master rule: `4xx` is the client, `5xx` is you. Swapping them
breaks monitoring and the clients' retry policies.

:::key
`401` means *unauthenticated* even though it is called `Unauthorized`;
`403` means *unauthorized* (no permission). The name in the protocol has
been swapped since 1997 and is not going to be fixed. Memorize it.
:::

## The safety net

```java title="The last handler — and the most important" numbered
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiError> unexpected(
        Exception e, HttpServletRequest req) {

    log.error("unhandled error at {}", req.getRequestURI(), e);

    ApiError body = new ApiError(
            Instant.now(), 500, "Internal Server Error",
            "internal error", req.getRequestURI(), List.of());

    return ResponseEntity.internalServerError().body(body);
}
```

Two decisions in that method. It **logs** the complete exception, with the
stack trace — it is the only copy of what happened. And it returns a
generic message to the client, without a stack trace and without internal
details.

:::pitfall
Never return an unexpected exception's `e.getMessage()` to the client.
Database exception messages carry table names, column names and,
sometimes, the whole SQL — valuable information for anyone looking for a
gap. Log everything; show little in the response.
:::

## The problem with the well-intentioned generic error

:::compare left="Swallow and cover up" right="Translate honestly"
try {
  return service.find(id);
} catch (Exception e) {
  return null;
}
---
// no try in the controller:
// the handler translates
return service.find(id);
:::

The left column returns `200` with an empty body — the client has no way of
knowing whether the product doesn't exist or the server failed. The right
one has no `try` at all: the controller trusts the central translator.

:::trivia
There is an error response pattern published as a standard: RFC 9457,
*Problem Details for HTTP APIs*, with the fields `type`, `title`,
`status`, `detail` and `instance`. Spring 6 brings native support through
`ProblemDetail`. If you are starting a new project today, it is worth
adopting the standardized format instead of inventing your own — this
chapter's `ApiError` exists to show the mechanics.
:::

:::summary
- `@RestControllerAdvice` centralizes translating exceptions into HTTP
  responses.
- `@ExceptionHandler` matches by the most specific type.
- A validation error should say **which field** failed.
- `4xx` is the client's fault, `5xx` is yours; `401` is authentication and
  `403` is permission.
- Log the complete exception and return a generic message on a `500`.
:::

:::checkpoint
You translate business exceptions into the correct statuses, return
validation errors per field, keep a safety net for the unexpected and don't
leak internal details.
:::

:::milestone
The API now fails well: `404` for nonexistent, `409` for conflict, `400`
with the offending field, `500` only when it's your fault. The four defects
from chapter 17 are solved.
:::

:::exercise level=1
Add a handler for `InsufficientStockException` that returns `409`.

:::answer
```java
@ExceptionHandler(InsufficientStockException.class)
public ResponseEntity<ApiError> stock(
        InsufficientStockException e, HttpServletRequest req) {
    return response(HttpStatus.CONFLICT, e.getMessage(), req);
}
```
`409` and not `400`: the request was correct; it is the resource's
**current state** that prevents the operation. That distinction helps the
client decide whether it is worth trying again.
:::

:::exercise level=2
Make the `500` handler include a trace identifier in the body and in the
log (a `UUID` generated on the spot). Explain the gain.

:::answer
```java
String traceId = UUID.randomUUID().toString();
log.error("error {} at {}", traceId, req.getRequestURI(), e);
```
With the identifier in the response, the user can quote it to support and
you find the exact stack trace in the log in seconds — without having to
expose anything. It is standard practice in a production API.
:::

:::exercise level=3
Find out what happens to an `@ExceptionHandler(RuntimeException.class)`
declared **alongside** the others. Then explain why the declaration order
doesn't matter.

:::answer
It is only called for a `RuntimeException` that has no more specific
handler. Spring resolves by **proximity in the type hierarchy**, not by
order in the file: `ProductNotFoundException` has its own handler, so it
wins. That lets you have a generic handler without fear of it hijacking the
handled cases.
:::
