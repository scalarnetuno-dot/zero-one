---
source_hash: 46329bbf1b5f
title: "Testing controllers"
number: 36
part: p8
kicker: "The HTTP contract is the only part of the system someone else depends on. It's the one that most deserves a test."
goal: >-
  Test endpoints with MockMvc, check status, header and JSON, and simulate
  an authenticated user without logging in.
---

Chapter 35's test proved the rule works. It proves nothing about the path,
the verb, the status or the JSON format — and that is exactly what the
client sees.

## MockMvc: HTTP without a network

```java title="ProductControllerTest.java" numbered
@WebMvcTest(ProductController.class)
class ProductControllerTest {

    @Autowired
    MockMvc mvc;

    @MockitoBean
    ProductService service;

    @Test
    void shouldReturn200AndProductWhenItExists() throws Exception {
        when(service.find(1L)).thenReturn(
                new ProductResponse(1L, "Keyboard", null,
                        new BigDecimal("349.90"), 12,
                        Status.ACTIVE, Instant.now()));

        mvc.perform(get("/products/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.name").value("Keyboard"))
                .andExpect(jsonPath("$.price").value(349.90));
    }
}
```

:::anatomy title="What `@WebMvcTest` loads — and what it leaves out"
lang: java
code: |
  @WebMvcTest(ProductController.class)
  class ProductControllerTest {

      @Autowired
      MockMvc mvc;

      @MockitoBean
      ProductService service;
  }
notes:
  - { line: 1, text: "Starts **only** the web layer: controller, JSON converters, validation and security." }
  - { line: 1, text: "It doesn't start the service, repository or database — that's why it's fast." }
  - { line: 4, text: "`MockMvc` runs the request inside the process: no port is opened." }
  - { line: 7, text: "`@MockitoBean` puts a double of the service in the context (it was `@MockBean` until Spring Boot 3.4)." }
:::

:::key
This test checks the **contract**: path, verb, status, field names and
value format. If someone renames `name` to `title` in the DTO, it breaks —
and that is exactly what it exists for.
:::

## Status and header

```java title="Chapter 17's 201 with Location" numbered
@Test
void shouldReturn201AndLocationOnCreate() throws Exception {
    when(service.create(any())).thenReturn(
            new ProductResponse(7L, "Mouse", null,
                    new BigDecimal("89.90"), 5,
                    Status.ACTIVE, Instant.now()));

    mvc.perform(post("/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("""
                             {"name":"Mouse","price":89.90,
                              "quantity":5}
                             """))
            .andExpect(status().isCreated())
            .andExpect(header().string("Location", "/products/7"))
            .andExpect(jsonPath("$.id").value(7));
}

@Test
void shouldReturn404WhenMissing() throws Exception {
    when(service.find(99L))
            .thenThrow(new ProductNotFoundException(99L));

    mvc.perform(get("/products/99"))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status").value(404))
            .andExpect(jsonPath("$.message").exists());
}
```

The second test is the one that guarantees chapter 26's
`@RestControllerAdvice` is in the path — it checks the translation of the
exception, not the service.

## Validation: the test that proves the `400` is a `400`

```java title="Invalid input" numbered
@Test
void shouldReturn400AndFieldWhenPriceIsNegative()
        throws Exception {
    mvc.perform(post("/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("""
                             {"name":"X","price":-5,"quantity":1}
                             """))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.fields[0].field")
                    .value("price"));

    verify(service, never()).create(any());
}
```

Two checks in one test, and both matter: the right status **and** the
guarantee that the service wasn't called. Validation that runs after the
rule isn't validation.

## Testing with an authenticated user

```java title="Without logging in" numbered
@Test
@WithMockUser(roles = "ADMIN")
void adminShouldDelete() throws Exception {
    mvc.perform(delete("/products/1").with(csrf()))
            .andExpect(status().isNoContent());
}

@Test
@WithMockUser(roles = "USER")
void regularUserShouldNotDelete() throws Exception {
    mvc.perform(delete("/products/1").with(csrf()))
            .andExpect(status().isForbidden());

    verify(service, never()).delete(any());
}
```

The second test is the one from chapter 33's incident — the four lines that
would have kept thirty-one people from being able to delete the catalog.

:::pitfall
`@WebMvcTest` **loads** your `SecurityConfig`. If the test starts returning
`401` where you expect `200`, it isn't a test bug: it's security working.
Use `@WithMockUser` or open up the route — and be suspicious if you need to
turn security off for the test to pass, because that means it isn't being
tested anywhere.
:::

## `jsonPath`: navigating the response

```java title="The forms you will use" numbered
.andExpect(jsonPath("$.name").value("Keyboard"))
.andExpect(jsonPath("$.content").isArray())
.andExpect(jsonPath("$.content.length()").value(3))
.andExpect(jsonPath("$.content[0].id").value(1))
.andExpect(jsonPath("$.totalElements").value(42))
.andExpect(jsonPath("$.password").doesNotExist())
```

The last line is the most valuable of all: it proves a sensitive field is
**not** in the response. A test like that in `UserController` is the net
that catches the day someone adds a field to the entity without thinking —
as in chapter 24.

## When to start the whole application

```java title="@SpringBootTest: the end-to-end test" numbered
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class ProductFlowTest {

    @Autowired MockMvc mvc;
    @Autowired ProductRepository repository;

    @Test
    @WithMockUser(roles = "ADMIN")
    void shouldCreateThenFind() throws Exception {
        mvc.perform(post("/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                 {"name":"Cable","price":19.90,
                                  "quantity":3}
                                 """)
                        .with(csrf()))
                .andExpect(status().isCreated());

        assertThat(repository.findByNameIgnoreCase("Cable"))
                .isPresent();
    }
}
```

| | `@WebMvcTest` | `@SpringBootTest` |
|---|---|---|
| Loads | only the web layer | the whole application |
| Speed | hundreds of ms | seconds |
| Database | none | a real one |
| Use for | each endpoint's contract | one or two complete flows |

Table: The healthy proportion is a pyramid: many unit tests, some web layer
tests, very few end-to-end.

:::story The contract that broke without anyone noticing
The change was small and well-meaning: `ProductResponse` started returning
`price` as formatted text — `"R$ 349,90"` — because the front-end team
asked not to have to format it.

The **website** front-end team asked. The mobile app, built by a partner,
expected a number.

The deploy was on Tuesday. On Wednesday, the app's cart screen started
showing `NaN` in the total for everyone. There was no error, no `500`, no
alert: the app got text where it expected a number, added it up, and the
result was "not a number" — silently, on the customer's screen.

It took twenty-nine hours for someone to connect the dots.

The test that would have caught it was one line:

```java
.andExpect(jsonPath("$.price").value(349.90))
```

It existed. Someone had changed it in the same commit, to `.value("R$
349,90")`, because "the test was breaking".
:::

:::summary
- `@WebMvcTest` starts only the web layer and tests the HTTP contract.
- Check status, header and JSON fields — including the ones that must
  **not** exist.
- `@WithMockUser` simulates a role without logging in; the `403` test is
  mandatory.
- Validation needs to prove the service wasn't called.
- Many unit tests, some web tests, very few end-to-end.
:::

:::checkpoint
You test endpoints with MockMvc, check contract and authorization, and know
how to choose between `@WebMvcTest` and `@SpringBootTest`.
:::

:::milestone
The API contract is covered: path, status, JSON and permission. What's
missing is the layer the two previous chapters avoided on purpose — the
database.
:::

:::exercise level=1
Write the `DELETE` test, checking `204` and the call to the service.

:::answer
Don't forget `.with(csrf())` even with CSRF off in production:
`@WebMvcTest` uses Spring Security's default test configuration, which may
require it. It is the number one cause of unexplained `403`s in controller
tests.
:::

:::exercise level=2
Write a test that guarantees the response of `GET /users/{id}` does **not**
contain the `password` field.

:::answer
```java
.andExpect(jsonPath("$.password").doesNotExist())
```
A four-word test that protects against a leak. Negative tests — proving
something does **not** happen — are the most underrated in the repertoire.
:::

:::exercise level=3
Write an end-to-end test that creates a product, lowers the stock to zero
and confirms the status became `SOLD_OUT` in the API's response.

:::answer
This test crosses controller, service, entity and database — it is the only
kind capable of catching an integration error, like a missing
`@Transactional` or a column with the wrong name. That's exactly why it's
slow and brittle: keep two or three, for the flows that are worth money,
and no more.
:::
