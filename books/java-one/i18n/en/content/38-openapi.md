---
source_hash: 7f29ca09590b
title: "Swagger and OpenAPI"
number: 38
part: p9
kicker: "An API nobody knows how to use doesn't exist. And hand-written documentation goes stale in a week."
goal: >-
  Generate OpenAPI documentation from the code, enrich it with annotations
  and understand why documentation kept apart from the code always lies.
---

Aurora Comércio's API has eleven endpoints, four possible statuses per
route, three optional filters and two access roles. None of it is written
down anywhere — except in this book.

## One dependency, and the documentation exists

```xml title="pom.xml"
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.6.0</version>
</dependency>
```

Restart and open `http://localhost:8080/swagger-ui.html`. It's all there:
every endpoint, every parameter, every field of every DTO, with type and
whether it's required.

Nobody wrote a thing.

:::key
springdoc reads what already exists — `@GetMapping`, `@RequestBody`,
`@NotBlank`, the return type — and builds the specification from it. It is
documentation **derived from the code**, and that's why it has no way of
being out of date with the code.
:::

## OpenAPI, Swagger and the name confusion

| Name | What it is |
|---|---|
| **OpenAPI** | the specification: a JSON that describes the API |
| **Swagger UI** | the page that reads that JSON and draws the interface |
| **springdoc** | the library that generates the JSON from your code |

Table: Swagger was the format's name until 2016, when it was donated and
renamed OpenAPI. The old name stuck to the tool.

```text title="Two addresses that now exist"
/swagger-ui.html          the interface
/v3/api-docs              the specification JSON
```

The second is the one that really matters: with it, a client generates
code automatically in any language, a contract test checks whether the API
changed, and an API *gateway* tool imports the routes.

## Enriching what the code doesn't say

The code states the format. It doesn't state the meaning:

```java title="ProductController.java" numbered
@Tag(name = "Products",
     description = "The store's catalog")
@RestController
@RequestMapping("/products")
public class ProductController {

    @Operation(
        summary = "Finds a product by id",
        description = "Returns the product, active or inactive. "
                    + "No authentication required.")
    @ApiResponses({
        @ApiResponse(responseCode = "200",
                     description = "found"),
        @ApiResponse(responseCode = "404",
                     description = "id does not exist",
                     content = @Content(schema =
                         @Schema(implementation = ApiError.class)))
    })
    @GetMapping("/{id}")
    public ProductResponse find(
            @Parameter(description = "product id", example = "7")
            @PathVariable Long id) {
        return service.find(id);
    }
}
```

:::pitfall
Annotating every endpoint with `@Operation`, `@ApiResponse` and
`@Parameter` doubles the size of the controller and drowns the code in
metadata. The practical balance: let springdoc infer the common stuff and
annotate only what it **has no way of knowing** — the meaning of the
resource, the reason for a `409`, an example value.
:::

## Documenting the DTO, which is where the client looks

```java title="dto/ProductRequest.java" numbered
@Schema(description = "Data to register a product")
public record ProductRequest(

        @Schema(description = "Name shown in the catalog",
                example = "Mechanical keyboard ABNT2")
        @NotBlank @Size(max = 120)
        String name,

        @Schema(description = "Sale price in reais",
                example = "349.90")
        @NotNull @Positive
        BigDecimal price,

        @Schema(description = "Units in stock", example = "12")
        @NotNull @PositiveOrZero
        Integer quantity) {
}
```

Chapter 25's validation annotations already showed up in the documentation
on their own — `@NotBlank` becomes `required: true`, `@Size(max = 120)`
becomes `maxLength: 120`. `@Schema` adds what's missing: the example and
the human sentence.

## The authorize button

```java title="config/OpenApiConfig.java" numbered
@Configuration
public class OpenApiConfig {

    @Bean
    OpenAPI api() {
        return new OpenAPI()
            .info(new Info()
                .title("Aurora Comércio — Catalog")
                .version("1.0")
                .description("Products, orders and customers API."))
            .addSecurityItem(
                new SecurityRequirement().addList("bearer"))
            .components(new Components()
                .addSecuritySchemes("bearer",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }
}
```

With that, the interface gets an **Authorize** button: you paste chapter
32's token and every test call starts sending it. That's what makes the
page truly useful — you can exercise the whole API without `curl`.

:::pitfall
`/swagger-ui.html` and `/v3/api-docs` are routes like any other: with
Spring Security on, they require authentication and the browser shows a
blank `401`. Open them up explicitly — and, in production, consider turning
off the interface and keeping only the JSON, or protecting both. A detailed
map of your API is useful to whoever integrates with it, and to whoever
attacks it too.
:::

```java title="SecurityConfig.java (addition)"
.requestMatchers("/swagger-ui/**", "/swagger-ui.html",
                 "/v3/api-docs/**").permitAll()
```

## What generated documentation doesn't solve

It describes **what** each endpoint receives and returns. It doesn't
describe:

- in which order to call things (create the customer before the order);
- what each business status means;
- usage limits, versioning, deprecation policy.

That is still text written by people — but in a `README.md` in the
repository, versioned alongside the code, not in a loose document nobody
knows where to find.

:::story The documentation in Word
There was a file. `API_Aurora_v3_FINAL_revisado_2.docx`, in a shared
folder, forty-one pages long.

It was written with care by someone who no longer works at the company.

The partner integrating the catalog used that file as a reference and sent
polite emails every week asking why the `stock` field didn't exist in the
response. It did exist — it had been called `quantity` since chapter 24,
and the document never found out.

When springdoc came in, Marina sent the partner the `/swagger-ui.html` link
and deleted the `.docx` from the shared folder.

Roberto asked whether deleting the documentation wasn't risky.

"We didn't delete the documentation," she said. "We deleted a fiction
about the system that thirty people believed was documentation."
:::

:::summary
- springdoc generates the OpenAPI specification from the code and the
  validation annotations.
- Swagger UI is the interface; `/v3/api-docs` is what tools consume.
- Annotate only what the code has no way of saying: meaning, example,
  reason for the error.
- Set up the `bearer` scheme so you can test authenticated on the page
  itself.
- Open up the documentation routes in security — and think twice before
  exposing them in production.
:::

:::checkpoint
You generate the documentation automatically, enrich the points that
matter, open up the routes and can exercise the whole API from the
browser.
:::

:::milestone
The API documents itself. Anyone with the link can understand and test the
eleven endpoints without talking to you — which is the practical definition
of an API ready to be used.
:::

:::exercise level=1
Add springdoc, open up the routes and open the interface. Register a
product from the browser, without `curl`.

:::answer
Notice the form already comes with the right fields and refuses to submit
if a required one is missing — all derived from chapter 25's validation
annotations. The documentation and the validation are the same truth,
written once.
:::

:::exercise level=2
Document the duplicate-name `409` with `@ApiResponse`, pointing to the
`ApiError` schema. Then check the JSON at `/v3/api-docs`.

:::answer
The gain isn't in the pretty page: it's in the JSON. A client that reads
the specification now knows, in code, that `409` returns an object with
`message` and `fields` — and can handle it without guessing.
:::

:::exercise level=3
Download `/v3/api-docs` into a file and version it in the repository. Then
write a test that compares the file with the one generated on the fly. What
does this test protect?

:::answer
It detects a **contract change**: if someone renames a field, changes a
status or removes an endpoint, the generated file no longer matches the
versioned one and the build fails. It's a contract test — the same idea as
chapter 36, raised to the level of the whole API, and the cheapest defense
against the `NaN` incident.
:::
