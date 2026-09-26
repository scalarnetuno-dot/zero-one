---
source_hash: e4ac87e75414
title: "API documentation"
number: 27
slug: documentacao-da-api
part: p7
kicker: "Integrating the app took three weeks. The API's only documentation was one sentence: \"ask Dedé\"."
goal: >-
  Publish documentation that is born from the code and therefore does not
  go stale: an OpenAPI schema generated from the routes, the Form Requests
  and the resources, with the errors described, runnable examples, and a
  written plan for taking a field offline without breaking whoever uses it.
---

:::story Ask Dedé
The reader app was not made by Vertexo. The association had secured, through
another grant, a small studio in Recife that made apps for nonprofits. They
had one developer, Lívia, and three weeks.

On the first day, Lívia sent a polite e-mail asking for the API
documentation. Márcia forwarded it to Dedé. Dedé replied with the staging
address and the sentence "any questions, just ask me".

On the second day, Lívia asked. She wanted to know the format of
`POST /loans`. Dedé explained. On the third, she wanted to know why the `422`
had `errors` and the `409` didn't. Dedé explained it was changing. On the
fifth, she wanted to know whether `due_on` came with a time. Dedé didn't
remember and went to look.

In the second week, Lívia sent a spreadsheet. It had forty-one rows, one per
route she had discovered by testing, with what she thought each one received
and returned. Eleven were wrong. Three were routes Dedé had deleted the week
before.

— She wrote the documentation — said Tainá, looking at the spreadsheet.

— She wrote the documentation for the API that existed last Tuesday — said
Dedé.

Márcia appeared at the door.

— The studio says the delay is because of our API.

— It is — said Dedé.

— What do you mean, it is?

— She's right. Every time I change something, she finds out by testing.
:::

## Documentation that isn't born from the code starts lying

Lívia's spreadsheet is the fate of all hand-written documentation about an
API that changes. On the day it is written, it is right. The following week,
a route is renamed, a field gets a format, a new validation appears — and
nobody remembers to update the document, because the document is not in the
same place as the code and nobody is warned when the two diverge.

Documentation in a wiki, a PDF, a Notion page has the same defect as the
stored number in chapter @cap:o-que-vamos-construir: it is a copy of
something that already exists elsewhere, and copies diverge.

The way out is the same: don't keep the copy. **Generate** the documentation
from what already exists — the routes, the Form Requests, the resources — so
that changing the code changes the document, without anyone having to
remember.

## OpenAPI: the schema that generates everything else

There is a standard format for describing an HTTP API, and it is called
OpenAPI. It is a JSON or YAML file with each route, what it receives, what
it returns for each status, and the shape of each object:

```yaml
paths:
  /api/loans:
    post:
      summary: Creates a loan
      security: [{ bearer: [] }]
      requestBody:
        content:
          application/json:
            schema:
              type: object
              required: [copy_id, reader_id]
              properties:
                copy_id: { type: integer }
                reader_id: { type: integer }
      responses:
        '201':
          description: Loan created
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Loan' }
        '409':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/Error' }
```

The file is verbose and nobody should write it by hand. Its value lies in
what is made **from** it:

- a browsable page, with each route, each field and a button to try it;
- clients generated automatically for the app — in Kotlin, Swift,
  TypeScript —, with the right types;
- automatic validation, in the test suite, that real responses follow the
  schema.

The schema is the contract from chapter @cap:o-que-e-uma-api-rest, in a
format machines can read.

## Generating from routes, requests and resources

There are two families of tools in PHP for producing OpenAPI.

**Annotations in the code.** You write, in PHP attributes above each method,
the route's description. The tool reads the attributes and builds the
schema. The schema comes out precise and as up to date as the attributes —
which are, again, a hand-written copy, now closer to the code.

**Inference.** The tool reads the code itself — the route, the Form
Request's type and its rules, the resource the method returns — and deduces
the schema. Scramble is the most used in the Laravel ecosystem:

```text
$ composer require dedoc/scramble
```

Without a single other line, the `/docs/api` route exists in development,
and `/docs/api.json` returns the schema. It reads:

| From | What it deduces |
|---|---|
| `routes/api.php` | the paths and verbs |
| the Form Request | the input fields, types, which are required |
| `Rule::enum` | the list of accepted values |
| the `JsonResource` | the response's fields |
| `auth:sanctum` | that the route requires a token |
| `abort`, exceptions and the Form Request | the possible error statuses |

Table: Everything this book wrote carefully over the last thirteen chapters
becomes documentation, for free — and it comes out right because it was
written carefully.

Notice the side effect. `validated()` and `JsonResource` were defended, in
chapters @cap:validation-e-form-requests and @cap:api-resources, for
security and for the contract. They are also what lets the documentation be
inferred: a controller that does `$request->all()` and `return $model` says
nothing a tool can read.

Inference does not guess everything. What it does not deduce, you add — and
the right place is the method's docblock, which sits beside the code:

```php title="app/Http/Controllers/LoanController.php" numbered
/**
 * Creates a loan.
 *
 * Only staff lend; the reader does not lend to themselves
 * through the app. The loan period depends on the reader's
 * profile and is given in `due_on`.
 */
public function store(
    CreateLoanRequest $request,
    LoanService $loans,
) {
    // ...
}
```

The text appears on the page, alongside what was inferred. It is the only
hand-written piece, and it is three lines from the code it describes.

## Documenting the error is documenting half the contract

Documentation that only shows the happy path is the most common kind and is
half the contract. Lívia did not ask three times about the `201`. She asked
about the `422`, the `409`, what comes when the token expires.

The single format from chapter @cap:erros-padronizados enters the schema as
a component. Scramble accepts a hook, registered in the provider, that
receives the schema after it is generated and lets you add what inference did
not see. The result, in `openapi.json`, is this:

```yaml
components:
  schemas:
    Error:
      type: object
      required: [type, message]
      properties:
        type: { type: string }
        message: { type: string }
        fields:
          type: object
          nullable: true
          additionalProperties:
            type: array
            items: { type: string }
        incident: { type: string, nullable: true }
```

Every error response on every route points to it, and the client generated
from the schema gets an `Error` class with the four fields typed.

And each possible `type` gets a row in a table, which is the part of the
documentation the app consults most:

| `type` | Status | The app should |
|---|---|---|
| `unauthenticated` | `401` | go to login |
| `forbidden` | `403` | show "not allowed" |
| `not-found` | `404` | show "not found" |
| `validation` | `422` | highlight the `fields` |
| `copy-unavailable` | `409` | offer a reservation |
| `loan-limit-reached` | `409` | list what to return |
| `reader-has-pending-items` | `409` | show the amount and how to pay |
| `too-many-requests` | `429` | wait for `Retry-After` |
| `internal-failure` | `500` | show the `incident` |

Table: The table is written by hand, and it is the exception that proves the
rule: it only changes when a new domain exception appears, and the test in
the next section flags when that happens.

## Examples the person clicks and runs

The page Scramble generates has, on each route, a button to send a real
request, with a field for the token. Lívia, on the first day, would have
typed the staging token and tested each route through the page, seeing the
response's real format — instead of building the spreadsheet by hand.

Runnable examples have one requirement: an environment where running them is
safe. The page points to **staging**, with the database from the factories
in chapter @cap:migrations-seeders-e-factories, and with the `LogSender` from
chapter @cap:service-container — no notice goes out to a real phone when
someone clicks "try it" on `POST /loans`.

### The test that compares the schema with reality

Documentation generated from the code can still diverge from behavior: the
resource declares a field as an integer, and a rare code path returns text.
One last layer closes that gap — checking, **in the feature tests**, that
each response obeys the published schema:

```php title="tests/Feature/ContractTest.php" numbered
test('responses follow the OpenAPI schema', function (
    string $method,
    string $route,
    array $body,
    int $status,
) {
    $response = $this->actingAs(User::factory()->admin()->create())
        ->json($method, $route, $body)
        ->assertStatus($status);

    expect($response)->toMatchOpenApi(
        base_path('docs/openapi.json'),
    );
})->with('contract-routes');
```

The `toMatchOpenApi` here is a project-specific expectation, built on top of
an OpenAPI validation library: it reads the schema, finds the route and the
status, and checks each field of the response. The `docs/openapi.json` file
is **generated in the pipeline** and versioned — and a change to it shows up
in the code review's *diff*, where someone can ask whether that change breaks
the app.

:::key
There are three layers, each protecting against one kind of lie:

**Inference** keeps the documentation from forgetting a route or a field.

**The versioned file** makes every contract change show up in review.

**The contract test** keeps the code from doing something different from
what the document says.
:::

## Versioning and marking what will go away

Chapter @cap:api-resources left a plan half done: `due_on`, which app 1.0
reads as `DD/MM/YYYY`, needs to become `YYYY-MM-DD`. The new field
`due_on_iso` was added alongside. What is missing is the part the
documentation solves: **giving notice**.

```php title="app/Http/Resources/LoanResource.php" numbered
return [
    // ...

    /**
     * @deprecated DD/MM/YYYY format. Use `due_on_iso`.
     *             Removed on 30 Jun 2026.
     */
    'due_on' => $this->due_on->format('d/m/Y'),

    'due_on_iso' => $this->due_on->toDateString(),
];
```

The schema now marks the field with `deprecated: true`, the page shows it
struck through, and clients generated from the schema start emitting a
compile-time warning when someone uses the field.

The whole plan, written in the documentation and not in anyone's head:

| Date | What happens |
|---|---|
| 1 Mar | `due_on_iso` published; `due_on` marked |
| 1 Mar to 30 Jun | the log counts requests still coming from 1.0 |
| 1 Jun | notice in app 1.0: "update by 30 Jun" |
| 30 Jun | `due_on` takes the ISO format |
| 30 Sep | `due_on_iso` goes, after three months marked |

Table: Six months to change one field's format. It seems like a lot, and it
is the time an app installed on a phone without automatic updates takes to
disappear.

The API also warns in the response itself, for clients that don't read
documentation:

```text
Deprecation: @1740787200
Sunset: Tue, 30 Jun 2026 23:59:59 GMT
Link: </docs/api#due_on>; rel="deprecation"
```

The `Deprecation` and `Sunset` headers are standardized, and a well-written
client logs them. A route middleware adds them on the routes that return the
field — a direct application of chapter @cap:middleware.

## Exposing the documentation in production, or not

Scramble, by default, only shows the documentation in the local
environment. Opening it in production is the team's decision, and depends
on who consumes the API.

**The API is public**, for anyone to integrate: the documentation is public
too. Hiding it protects nothing — anyone can discover the routes by using
the app with a network inspector.

**The API belongs to a known client**, like the Recife studio's app: the
documentation stays behind authentication, accessible to whoever
integrates.

**The API has administrative routes**: those routes do **not** go into the
public documentation, even if the rest does. Publishing
`/api/admin/readers/export` in an open document is handing over the map of
where to look.

Casa Amarela publishes the documentation on staging, with login, and
generates two schemas: a full one, for the team, and one with only the
reader routes, for the studio.

:::note In your career
API documentation tends to be seen as an end-of-project task, and that is
why it arrives late and out of date. Treated as a consequence of the code —
generated, versioned, tested —, it stops being a task.

And it has an effect few people anticipate: it changes the conversation with
whoever consumes the API. Lívia stops asking and starts pointing — "the
schema says integer and it came back as text". A question costs an
interruption; a pointer against a document is a defect with an address.
Whoever publishes the right documentation gets, for free, an external tester
working for their project.
:::

:::tree title="Where we are now"
casa-amarela/
  config/scramble.php            # two schemas: team and reader
  docs/
    openapi.json                 # generated in the pipeline, versioned
  app/Providers/
    AppServiceProvider.php       # Error component in the schema
  app/Http/Middleware/
    WarnsDeprecation.php         # Deprecation, Sunset, Link
  tests/Feature/
    ContractTest.php             # real response × schema
:::

:::summary
- Hand-written documentation is a copy of the code, and copies diverge.
- OpenAPI describes routes, inputs, responses and errors in a format that
  generates pages, clients and validation.
- Inference reads routes, Form Requests, `Rule::enum`, resources and
  middleware; what the book wrote carefully becomes documentation.
- `$request->all()` and `return $model` document nothing.
- The error is half the contract: the `Error` component and the `type` table
  describe what the client should do.
- Runnable examples need an environment where running is safe.
- The versioned schema shows contract changes in review; the contract test
  checks the real response against it.
- A field that is going away is marked, announced by header and removed on a
  dated plan.
- Administrative routes do not go into the public documentation.
:::

:::checkpoint
Casa Amarela's API has `/docs` and `openapi.json` generated from the code,
with the errors and their `type` described, examples that run on staging, a
test that checks each response against the schema, and a dated plan to
change `due_on`'s format without breaking app 1.0.
:::

:::exercise level=1
Say what the inference tool can deduce on its own and what needs to be
added by hand:

1. That `POST /books` requires `title`.
2. That the reader cannot create a loan through the app.
3. That the copy's `status` accepts `good`, `on_loan`, `in_repair` and
   `lost`.
4. That `due_on` will be removed on 30 Jun.
5. That the loan's `409` may have the `type` `copy-unavailable`.

:::answer
1. On its own, from `StoreBookRequest`'s `required`.
2. By hand, in the docblock. Inference sees `authorize()` and knows there
   may be a `403`, but not **why** or for whom.
3. On its own, from `Rule::enum(CopyStatus::class)` — and it stays right
   when a new case enters the enum.
4. By hand, in the resource's `@deprecated`.
5. Partly. The tool knows the route may return `409` if the exception is
   thrown in a way it can trace; the list of possible `type`s is the
   hand-written table.

The pattern: what is **structure** the tool deduces; what is **intent** —
why, for whom, until when — needs a sentence.
:::

:::exercise level=2
`BookResource`'s `subject` field will become the `subject_detail` object, as
chapter @cap:api-resources planned. Write: the resource snippet with the
marking, the plan's date table, and the **measured** condition that
authorizes the last step.

:::answer
```php
/**
 * @deprecated Loose text. Use `subject_detail`.
 *             Removed on 31 Oct 2026.
 */
'subject' => $this->subject->name,

'subject_detail' => new SubjectResource($this->subject),
```

| Date | What happens |
|---|---|
| 1 May | `subject_detail` published; `subject` marked |
| 1 May to 31 Oct | `Deprecation` and `Sunset` headers on the routes |
| 1 Sep | notice in the app for versions that read `subject` |
| 31 Oct | `subject` goes |

**The measured condition:** the structured log records, on each request, the
app version that came in the `X-App-Version` header. The last step only
happens if, in the two weeks before 31 Oct, the versions that still read
`subject` add up to less than, say, 1% of requests — and if Vera agrees to
personally notify whoever is still on them.

If the number doesn't drop, the date moves. The plan's date is an intention;
what authorizes the removal is the measurement.
:::

:::exercise level=3
The Recife studio asked for the API to have a version in the path —
`/api/v1/...` —, "because it's the industry standard and it makes things
easier for us". Today the API has no version in the path.

Write the reply to the studio: what a version in the path solves, what it
costs Casa Amarela, what the team already does instead, and in what
situation you would accept it.

:::answer
**What it solves.** It allows the contract to change incompatibly —
renaming, removing, changing formats — while keeping the old version live
for whoever still depends on it. The client chooses when to migrate, by
changing one part of the URL.

**What it costs.** For each live version, routes, controllers, resources and
tests exist twice, or are shared with an `if` per version. A security defect
has to be fixed in all of them. And the temptation to publish a v2 "to tidy
everything up" usually produces a v2 that sits beside v1 for years.

**What the team already does instead.** Compatible evolution: a new field
alongside the old one, marking in the schema, `Deprecation` and `Sunset`
headers, removal with a date and a measurement. That handles the changes the
API has had so far without duplicating anything, and the schema versioned in
Git shows exactly what changed and when.

**When I would accept it.** If a change appears that cannot be made
alongside — the reservation model changing from "per book" to "per copy",
for example, altering the meaning of half the routes. Then a v2 is honest:
it is another contract.

**And what I would offer the studio now:** prefix the routes with `/api/v1`
**today**, without creating any v2, as a reserved address. It costs
nothing, satisfies the request, and leaves the road open for the day an
incompatible change really appears. What I would refuse is using the
version in the path as a substitute for the discipline of compatible
evolution — because that discipline is still needed within each version.
:::
