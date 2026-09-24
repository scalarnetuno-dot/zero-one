---
source_hash: 2927aad224a7
title: "Users and permissions"
number: 33
part: p7
kicker: "Knowing who the person is is half the job. The other half is deciding what they can do."
goal: >-
  Protect routes by role with `@PreAuthorize` and by resource-owner rules,
  and know why authorization also lives in the service.
---

Chapter 32's token carries a role: `USER` or `ADMIN`. What's missing is
using it. Today, any authenticated person can still delete any product —
which is a small improvement over "any person".

## Aurora's permission map

| Operation | USER | ADMIN |
|---|---|---|
| `GET /products` | public | public |
| `POST /products` | no | yes |
| `PUT /products/{id}` | no | yes |
| `DELETE /products/{id}` | no | yes |
| `GET /orders/mine` | only their own | all |
| `GET /users` | no | yes |

Table: The authorization contract. Writing it before programming is what
avoids finding a missing rule in production.

## Two places to declare the rule

```java title="1. In the filter chain — by route" numbered
.authorizeHttpRequests(auth -> auth
    .requestMatchers(HttpMethod.GET, "/products/**").permitAll()
    .requestMatchers(HttpMethod.POST, "/products/**")
        .hasRole("ADMIN")
    .requestMatchers(HttpMethod.PUT, "/products/**")
        .hasRole("ADMIN")
    .requestMatchers(HttpMethod.DELETE, "/products/**")
        .hasRole("ADMIN")
    .anyRequest().authenticated())
```

```java title="2. On the method — by annotation" numbered
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void delete(@PathVariable Long id) {
    service.delete(id);
}
```

For the second form to work, one annotation on the configuration:

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig { ... }
```

:::key
Both forms coexist, and the choice is not a matter of taste. A rule **by
route** is a map: whoever reads the configuration sees the whole system. A
rule **by method** sits close to the code it protects and survives a URL
change. In real projects, use the first for the overall design and the
second for the exceptions.
:::

:::pitfall
`hasRole("ADMIN")` looks for the authority `ROLE_ADMIN` — the prefix is
added automatically. `hasAuthority("ADMIN")` looks for exactly `ADMIN`.
Mixing the two results in a `403` for someone who should get through, and
the log doesn't explain it. Pick one style and stick with it.
:::

## The rule the filter can't express

"A user sees their own orders" is not a route rule: it depends on the
**data**, not the path.

```java title="OrderService.java" numbered
@Transactional(readOnly = true)
public OrderResponse find(Long id, String loggedInEmail) {
    Order order = repository.findById(id)
            .orElseThrow(() -> new OrderNotFoundException(id));

    boolean owner = order.getCustomer()
            .getEmail().equals(loggedInEmail);

    if (!owner && !isAdmin()) {
        throw new AccessDeniedException("another customer's order");
    }
    return OrderResponse.of(order);
}
```

:::pitfall
Notice what this method does **not** do: it doesn't return a `404` when the
order belongs to someone else. Returning `404` instead of `403` hides the
resource's existence — which is safer — but also prevents the legitimate
client from telling "doesn't exist" from "isn't yours". For sensitive data,
prefer `404`; for the rest, `403` is more honest. It is a conscious
decision, not an oversight.
:::

## Who is logged in, inside the code

```java title="Three ways to get the current user" numbered
// 1. controller parameter
@GetMapping("/mine")
public List<OrderResponse> mine(Authentication auth) {
    return service.ofCustomer(auth.getName());
}

// 2. annotation
@GetMapping("/mine")
public List<OrderResponse> mine(
        @AuthenticationPrincipal UserDetails user) {
    return service.ofCustomer(user.getUsername());
}

// 3. anywhere (including the service)
String email = SecurityContextHolder.getContext()
        .getAuthentication().getName();
```

The third works in any layer because the context lives in a thread
variable — the same thread that serves the request. It is practical and it
has a price: the service starts depending on Spring Security, which makes
it harder to test in isolation. Preferring to pass the e-mail as a
parameter keeps the service ignorant of the framework.

## Authorization is also a business rule

:::diagram type="blocks" caption="Three layers of authorization — and the bottom one is the only one that knows the data."
rows:
  - [{ text: "Filter chain", note: "by route and verb: the overall map" }]
  - [{ text: "@PreAuthorize", note: "by method: the required role" }]
  - [{ text: "Service", note: "by data: is it yours? is it in your department?" }]
:::

:::pitfall
Protecting only in the controller is protecting only the front door. The
day another entry point exists — a message queue, a scheduler, a terminal
command — the controller's rule no longer applies. A rule that depends on
the data belongs to the service.
:::

## What the client receives

:::http title="Authenticated, but without permission"
DELETE /products/7
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
---
403 Forbidden

{
  "status": 403,
  "error": "Forbidden",
  "message": "access denied",
  "path": "/products/7"
}
:::

For the response to come out in that format — chapter 26's `ApiError` — a
handler is missing:

```java title="ApiExceptionHandler.java (addition)" numbered
@ExceptionHandler(AccessDeniedException.class)
public ResponseEntity<ApiError> denied(
        AccessDeniedException e, HttpServletRequest req) {
    return response(HttpStatus.FORBIDDEN,
            "access denied", req);
}
```

:::story The intern with ADMIN
The users table had a `role` column and a default value: `ADMIN`.

It wasn't a decision. It was the first record created by hand during
development, copied as a template into the user creation script, and the
script stayed.

Everyone who joined Aurora over the following four months joined as a
catalog administrator. The support team, the marketing team, two interns
and an outside consultant who spent three weeks there.

Nobody did anything wrong. That is the point: security wasn't tested
because it was never exercised.

The discovery came from the most bureaucratic side possible — a compliance
audit asked for the list of people who could delete a product. The answer
was "thirty-one people", in a company of forty.

Marina added three things the same day: the column's default became
`USER`, the script started requiring the role explicitly, and an automated
test started checking that a `USER` gets a `403` on `DELETE`.

The test is chapter 36. It is what kept this from happening again.
:::

:::summary
- A rule by route draws the map; `@PreAuthorize` protects the method; the
  service decides what depends on the data.
- `hasRole` adds `ROLE_`; `hasAuthority` doesn't.
- `401` is "I don't know who you are"; `403` is "I do, and you can't".
- Returning `404` instead of `403` hides the resource's existence — a
  conscious decision.
- A permission's default value should be the smallest possible.
:::

:::checkpoint
You protect routes by role, write resource-owner authorization in the
service, get the logged-in user and return `403` in the API's standard
format.
:::

:::milestone
End of Part 7. The API knows who comes in, what each one can do and
answers with the right status when they can't. It has also never been
tested by anything but a hand-typed `curl` — and that is what Part 8
solves.
:::

:::exercise level=1
Protect `POST`, `PUT` and `DELETE` on `/products` with `ADMIN` and test
with a `USER` token. Confirm the `403`.

:::answer
If you get `401` instead of `403`, the token didn't reach the filter —
probably the `Bearer ` prefix is missing or the filter wasn't registered in
the chain. The two statuses point to different problems, and confusing them
costs half an hour.
:::

:::exercise level=2
Implement `GET /orders/mine` returning only the authenticated user's
orders, without receiving any id in the URL.

:::answer
```java
@GetMapping("/mine")
public List<OrderResponse> mine(Authentication auth) {
    return service.ofCustomer(auth.getName());
}
```
Notice that the client **can't** ask for someone else's orders: the
identifier isn't in the URL. Designing the endpoint this way eliminates a
whole class of authorization failure — the best protection is the one that
doesn't depend on a check.
:::

:::exercise level=3
Add the `MANAGER` role, which can create and edit products but not delete
them. Then answer: at what point does a list of roles stop scaling?

:::answer
When the combinations grow faster than the job titles — "can edit the
price but not the stock", "can delete only from their own category". Then
the model stops being roles and becomes **permissions**: the user has a set
of granular authorities (`PRODUCT_WRITE`, `PRODUCT_DELETE`) and the roles
become mere shortcuts to sets. It is the same turn as chapter 12: when the
`if` ladder grows too much, a type is missing.
:::
