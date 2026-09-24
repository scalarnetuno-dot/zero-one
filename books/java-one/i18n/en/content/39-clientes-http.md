---
source_hash: 4e7a8145ee01
title: "HTTP clients"
number: 39
part: p9
kicker: "The tool matters less than the habit of keeping the request next to the code that serves it."
goal: >-
  Exercise the API with `curl`, `.http` files and Postman collections, and
  organize it all in a way that survives the departure of whoever wrote it.
---

You've used `curl` since chapter 17 and the Swagger interface since chapter
38. This chapter is short and deals with one thing only: where those
requests live.

## `curl`: the common denominator

```bash title="What you need to know about curl" numbered
# simple GET
curl localhost:8080/products/1

# with the response headers
curl -i localhost:8080/products/999

# POST with JSON
curl -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Cable","price":19.90,"quantity":3}'

# with a token
curl localhost:8080/orders/mine \
  -H "Authorization: Bearer $TOKEN"

# saving the token in a variable
TOKEN=$(curl -s -X POST localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aurora.com","password":"admin123"}' \
  | jq -r .token)
```

The last line uses `jq`, which reads JSON on the command line. It's worth
installing: it turns "copy the token with the mouse" into a step that can
be automated.

:::tip
`curl` is everywhere: in your terminal, on the production server, in the
container, in the example someone is going to paste into a ticket. That's
why it remains the most universal way to describe a request — even for
people who use a graphical tool day to day.
:::

## `.http` files: the versioned request

```http title="src/test/http/products.http"
@host = http://localhost:8080
@token = {{login.response.body.token}}

### login
# @name login
POST {{host}}/auth/login
Content-Type: application/json

{ "email": "admin@aurora.com", "password": "admin123" }

### list products
GET {{host}}/products?page=0&size=5

### create product
POST {{host}}/products
Content-Type: application/json
Authorization: Bearer {{token}}

{
  "name": "Mechanical keyboard",
  "price": 349.90,
  "quantity": 12
}

### delete
DELETE {{host}}/products/1
Authorization: Bearer {{token}}
```

IntelliJ and VS Code (with the REST Client extension) run that file with a
click on each `###`. And it has the property no graphical tool has: **it
lives in the repository**, next to the controller that serves the routes.

:::key
A request versioned with the code is executable documentation. Whoever
joins the project tomorrow opens the file, runs it and sees the API
working — without installing anything, without asking anyone for a
collection, without guessing the body format.
:::

## Postman and Insomnia

Graphical tools win on three things: response history, one-click
environments (local, staging, production) and chained tests that extract
values from one response for the next request.

```javascript title="Postman: storing the token after login"
// Tests tab of the login request
const json = pm.response.json();
pm.environment.set("token", json.token);

pm.test("login returns 200", function () {
    pm.response.to.have.status(200);
});
```

And they lose on one, which tends to be costly:

:::pitfall
The collection lives on the machine of whoever created it. When that person
goes on vacation — or leaves the company —, the team finds out the only
working description of the API was in a personal account on a third-party
tool. Export the collection as JSON and **version it with the project**, or
use the `.http` file, which is versioned from birth.
:::

| Tool | Wins on | Loses on |
|---|---|---|
| `curl` | universal, automatable | unreadable as it grows |
| `.http` | versioned, inside the IDE | no history, no GUI |
| Postman | environments, chaining, team | lives outside the repository |
| Swagger UI | always current, zero setup | only what the API exposes |

Table: Don't pick one. Use `curl` for the example in the ticket, `.http`
for the everyday, Postman when there's a team and Swagger for outsiders.

## One step further: generating the client

```bash title="From chapter 38's /v3/api-docs"
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8080/v3/api-docs \
  -g typescript-axios \
  -o ./client
```

The front-end team gets a typed library, with one method per endpoint,
generated from the specification. When a field changes name, the front-end
code stops compiling — instead of showing `undefined` on the screen, as in
chapter 36's incident.

:::story Carlos's collection
The integration with the partner had been stuck for three days.

The partner said `POST /orders` returned `400`. Aurora said it worked. Both
were right: the partner sent `customerId` as text, and the API expected a
number.

Nobody could compare because nobody had the same request. Each person had
their own, put together from memory, in a different tool.

Carlos had a Postman collection with everything working — the one he'd
used since chapter 17. Except the collection was in his personal account,
which was logged in only on his computer, which was at the repair shop with
a broken screen.

On the fourth day, Marina created the `products.http` file in the
repository, with the eleven requests. It took twenty minutes. The partner
cloned the project, opened the file, ran it, saw the correct body and fixed
it in five minutes.

The file is still there. It has been used by seven people who never talked
to Carlos.
:::

:::summary
- `curl` is universal; `jq` turns the response into something automatable.
- An `.http` file lives in the repository, next to the code it exercises.
- Postman wins on environments and chaining, and vanishes with whoever
  created it — export and version it.
- Chapter 38's specification generates typed clients automatically.
:::

:::checkpoint
You exercise the API through all four routes, keep the requests in the
repository and know why a personal collection is a single point of
failure.
:::

:::milestone
The API can be exercised by anyone on any machine, without a prior
conversation. One last piece of tooling is missing — the one that records
why the code is the way it is.
:::

:::exercise level=1
Create `src/test/http/products.http` with the five CRUD requests and run
them from the editor.

:::answer
Start with the login and use `{{login.response.body.token}}` in the rest.
The chaining is what turns the file into a script: one run from top to
bottom exercises the whole API.
:::

:::exercise level=2
Write a `bash` script that logs in, creates a product, finds it, deletes it
and confirms the `404`. Make it fail with a non-zero exit code if any step
doesn't return the expected status.

:::answer
`curl -f -s -o /dev/null -w "%{http_code}"` returns the status and lets you
compare. A script like that is a smoke test: it runs against staging after
every deploy and answers, in ten seconds, whether the application came up
whole.
:::

:::exercise level=3
Generate a TypeScript client from `/v3/api-docs` and inspect the code it
produces. Then rename a field in the DTO, generate it again and compare.

:::answer
The diff shows exactly what broke for the consumer. It is the most
concrete way to see the cost of a contract change — and the most
convincing argument there is in favor of API versioning, a topic this book
leaves as the next step.
:::
