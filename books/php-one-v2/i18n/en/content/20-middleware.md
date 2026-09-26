---
source_hash: 09d75611f2f8
title: "Middleware"
number: 20
slug: middleware
part: p5
kicker: "The logging middleware recorded the whole body of every request. For three months, that included the password field."
goal: >-
  Understand the pipeline that wraps every route, choose between global,
  group and route middleware, put the order on your side, limit attempts,
  and write your own middleware knowing what does not belong in it.
---

:::story The password field
Cléber had written the middleware in October, on a previous Vertexo
project, and brought it to Casa Amarela because "it was already tested". It
logged every request that arrived: method, path, response time and the
body.

— The body what for? — asked Tainá, reading the file.

— For debugging. When the client says they sent something, we see what
they sent.

Tainá opened the staging log and searched for `/auth/login`. The first
occurrence was from three days before.

```text
[2026-02-12 09:41:03] local.INFO: request
{"method":"POST","path":"api/auth/login","ms":212,
 "body":{"email":"vera@casaamarela.org.br",
          "password":"marmelada1994"}}
```

She turned the screen toward Cléber without saying anything.

— Oh — he said. — But it's staging.

— Vera uses the same password for everything — said Tainá. — She told me.

Cléber was quiet for a while.

— On the other project it's been in production since October.

— With login?

— With login.
:::

## The onion

Every request that reaches Laravel goes through a sequence of layers before
reaching the controller, and goes through the same layers on the way back,
in reverse order. Chapter @cap:um-framework-de-quarenta-linhas built that
sequence with an `array_reduce` and called it an onion before it had a
name.

```php title="app/Http/Middleware/MeasuresTime.php" numbered
final class MeasuresTime
{
    public function handle(Request $request, Closure $next): Response
    {
        $start = hrtime(true);

        $response = $next($request);

        $ms = (hrtime(true) - $start) / 1_000_000;
        $response->headers->set(
            'Server-Timing', "app;dur={$ms}",
        );

        return $response;
    }
}
```

`$next($request)` is the line that splits the middleware in two. Everything
before it happens **on the way in**, before the controller. Everything after
it happens **on the way back**, with the response ready in hand.

:::diagram type="flowchart" caption="The request goes down through the layers to the controller; the response comes up through the same layers, in reverse order."
nodes:
  - { id: req,  type: io,      text: "request" }
  - { id: m1,   type: process, text: "MeasuresTime (in)" }
  - { id: m2,   type: process, text: "auth:sanctum (in)" }
  - { id: ctl,  type: process, text: "controller" }
  - { id: m2v,  type: process, text: "auth:sanctum (out)" }
  - { id: m1v,  type: process, text: "MeasuresTime (out)" }
  - { id: resp, type: io,      text: "response" }
edges:
  - { from: req, to: m1 }
  - { from: m1, to: m2 }
  - { from: m2, to: ctl }
  - { from: ctl, to: m2v }
  - { from: m2v, to: m1v }
  - { from: m1v, to: resp }
:::

A middleware can also **not call** `$next`. In that case, the request stops
there, and the response it returns is the one the client receives. That is
how the authentication middleware refuses whoever has no token: the
controller never runs.

:::term Middleware
A layer that wraps a route's execution, with access to the request on the
way in and to the response on the way out, and with the power to cut the
path short. It is for what applies to **many routes at once** and belongs to
none of them.
:::

## Global, group and route

Laravel 11 configures middleware in `bootstrap/app.php`, and there are three
scopes.

**Global** runs on every request, web and API:

```php title="bootstrap/app.php" numbered
->withMiddleware(function (Middleware $middleware) {
    $middleware->append(MeasuresTime::class);
})
```

**Group** runs on every route in a group. Laravel already has two — `web`,
which turns on session, cookies and CSRF, and `api`, which turns on none of
that, because the API has no session:

```php title="bootstrap/app.php" numbered
$middleware->api(prepend: [
    ForcesJson::class,
    LogsRequest::class,
]);
```

**Route** runs where it is asked for:

```php title="routes/api.php" numbered
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');

Route::middleware('auth:sanctum')->group(function () {
    Route::apiResource('loans', LoanController::class);
});
```

| Scope | Cost of a mistake | Example |
|---|---|---|
| global | every request, including `/up` | measuring time |
| group | the whole API, or the whole panel | forcing JSON |
| route | only where asked | limiting login |

Table: The bigger the scope, the cheaper the middleware needs to be. A
database query in a global middleware is one more query on every request of
the whole application — including the health check monitoring makes every
ten seconds.

## Order matters more than it seems

In the onion, the outer layer sees everything the inner one does, and the
inner one sees nothing the outer one did afterwards. That turns order into
behavior.

The middleware that measures time needs to be the **outermost**, to measure
everything. If it is inside the authentication one, the token lookup is not
included in the measurement — and the number it shows is optimistic.

The middleware that logs the request needs to be **outside the
authentication one** to also log requests refused with `401`. And it needs
to be **inside** if it wants to know who the user is. The two things do not
fit in a single place, and that is why the correlation log in the next
section does the job in two halves.

:::pitfall
The most expensive wrong order is authorization before authentication. A
middleware that checks "is this user an admin?" before the user has been
identified sees `null`, and what it does with `null` depends on how it was
written:

```php
if ($request->user()?->role !== Role::Admin) {
    abort(403);
}
```

That one refuses everyone — including the admin, and the route looks
broken. The hurried version does the opposite:

```php
if ($request->user() && !$request->user()->isAdmin()) {
    abort(403);
}
```

That one **lets through whoever is not authenticated**, because the `if`
only refuses an existing user who is not an admin. Laravel resolves the
order among its own middleware with a priority list; yours, you resolve.
:::

## `ForcesJson`: the API that always answers in JSON

The handler from chapter @cap:erros-padronizados answers in JSON when the
request **asks** for JSON — when the `Accept` header says
`application/json`. A client that forgets the header receives, on a
validation error, a **redirect** to the previous page, which is the web
panel's behavior.

```php title="app/Http/Middleware/ForcesJson.php" numbered
final class ForcesJson
{
    public function handle(Request $request, Closure $next): Response
    {
        $request->headers->set('Accept', 'application/json');

        return $next($request);
    }
}
```

Three lines, and every API route behaves like an API, regardless of what the
client sent. It is the ideal middleware example: it applies to a whole
group, depends on no business rule, and queries nothing.

## `LogsRequest`: the incident born at the start

In chapter @cap:erros-padronizados, the incident code was born at the moment
of the error. With a middleware, it is born at the start of every request —
and every log line written during it carries the same number.

```php title="app/Http/Middleware/LogsRequest.php" numbered
final class LogsRequest
{
    private const SENSITIVE_FIELDS = [
        'password', 'password_confirmation', 'token', 'document',
    ];

    public function handle(Request $request, Closure $next): Response
    {
        $id = $request->header('X-Request-Id')
            ?? (string) Str::ulid();

        Context::add('incident', $id);

        $response = $next($request);

        $response->headers->set('X-Request-Id', $id);

        return $response;
    }

    public function terminate(
        Request $request,
        Response $response,
    ): void {
        Log::info('request', [
            'method' => $request->method(),
            'path' => $request->path(),
            'status' => $response->getStatusCode(),
            'user' => $request->user()?->id,
            'fields' => array_keys(
                $request->except(self::SENSITIVE_FIELDS),
            ),
        ]);
    }
}
```

Four decisions in this file, and each one answers Cléber's scene.

**The body does not go to the log.** The field **names** go, without the
values. To debug "the client said they sent the title", knowing that the
`title` field came is enough most of the time. For the rest, there is the
incident and reproduction.

**Even the names go through an exclusion list.** Not for security — the name
`password` is no secret — but because the list exists to be remembered: it
is where someone looks when adding a new sensitive field.

**Logging happens in `terminate`.** A middleware with a `terminate` method
is called **after the response has been sent** to the client. The log
delays nobody's response.

**The identifier accepts what came from outside.** If the app sends an
`X-Request-Id`, it is used. The app can then show the same number that is in
the server's log — and, when there is a load balancer in front, it can
generate the number first, and the trail crosses both machines.

:::warning
The sensitive-field list protects **your** middleware. It does not protect
the rest.

The `Log::info('request', $request->all())` someone writes in a controller
to investigate a defect will record the password all the same. Chapter
@cap:cache-logs-e-medicao covers the general rule — what never goes into the
log — and how to check that it is being followed.
:::

And what to do about the three months of passwords recorded in the other
project's log? Deleting the log is not enough, because it may have been
copied to an aggregation service, to a backup, to the machine of whoever
investigated a defect. The answer is the same as chapter
@cap:git-ci-e-deploy's about secrets in Git: **change the secret**. Everyone
who logged in during that period needs to reset their password.

## Throttle: the limit that protects you from yourself

The login route accepts an e-mail and a password. Without a limit, it also
accepts a program that tries ten thousand passwords a minute against Vera's
e-mail.

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    RateLimiter::for('login', function (Request $request) {
        return [
            Limit::perMinute(5)->by(
                mb_strtolower((string) $request->input('email'))
                    . '|' . $request->ip(),
            ),
            Limit::perMinute(30)->by($request->ip()),
        ];
    });
}
```

```php
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');
```

Two limits at once. Five attempts a minute for the same combination of
e-mail and address, which stops an attack aimed at one account. And thirty
a minute per address, which stops someone trying many accounts from the
same place.

Once the limit is exceeded, the middleware does not call `$next` and
responds `429 Too Many Requests`, with the `Retry-After` header saying how
many seconds to wait — and the handler from chapter @cap:erros-padronizados
already translates it into the API's format.

The section's title is "protects you from yourself" because the limit is not
only for attacks. An app with a loop defect, resending the same request
without stopping, is more common than an attacker — and takes the server
down just the same.

:::pitfall
Limiting only by IP address seems sufficient and has a side effect at Casa
Amarela: the six computers at the counter and in the reading room go out to
the internet through the **same** address. Five attempts a minute per IP
would mean Neide getting her password wrong three times locks Vera out.

The limit's key is a business decision, and needs to be checked with the
people who use it.
:::

## What not to put in there

Middleware is tempting because it runs for many routes without anyone
having to remember. That same quality makes it invisible, and what is
invisible is forgotten when there is a problem.

**Business rules.** "A blocked reader can't do anything" looks like
middleware — it applies to all the reader's routes. But it is a rule, it
changes over time, it has exceptions ("they can return a book, of course"),
and it needs to be tested without HTTP. It belongs in the service or in the
policy from chapter @cap:autorizacao.

**A heavy query in global middleware.** A middleware that loads "the
library's settings from the database" on every request makes one more query
on the health check, on each image Laravel serves, on every `404`.

**Something only one route needs.** If only `POST /loans` needs it, it is
`POST /loans`'s code.

The yardstick: middleware is for what applies to **many routes** and is
**independent of what the route does**. Measuring time, forcing JSON,
identifying the request, rate limiting, authenticating. Anything that needs
to know what the route does is in the wrong place.

:::note In your career
Many of the security flaws you will investigate over your career will not
be in security code. They will be in a logging middleware, in a generic
error handler, in a debugging tool left switched on — support code, written
in a hurry, that nobody reviews with the attention they give a login screen.

The habit that helps is asking, for all code that **records** something —
log, cache, queue, file —: what exactly is being recorded, and who can read
it later? The question takes ten seconds and would have spared Cléber a
difficult conversation.
:::

:::tree title="Where we are now"
casa-amarela/
  bootstrap/app.php                # withMiddleware: api(prepend: ...)
  app/Http/Middleware/
    MeasuresTime.php               # global, the outermost
    ForcesJson.php                 # api group
    LogsRequest.php                # incident in Context, terminate
  app/Providers/
    AppServiceProvider.php         # RateLimiter::for('login')
  routes/api.php                   # throttle:login
:::

:::summary
- Middleware wraps the route: what comes before `$next` runs on the way in,
  what comes after runs on the way back, and not calling `$next` cuts it
  short.
- Global, group and route: the bigger the scope, the cheaper it needs to be.
- Order is behavior; authorization before authentication sees `null`.
- `ForcesJson` makes the API answer in JSON even without the `Accept`
  header.
- The incident is born at the start of the request, goes into the `Context`
  and comes back in the `X-Request-Id` header.
- A request log records field names, never the body; `terminate` logs after
  responding.
- A secret recorded in a log is solved by changing the secret.
- `throttle` with `RateLimiter::for` limits by key; the key is a business
  decision.
- Business rules, heavy queries and single-route concerns do not belong in
  middleware.
:::

:::checkpoint
The API forces JSON, identifies each request with a number that appears in
the log and in the response, logs requests without recording values, limits
login per account and per address, and you can explain why "blocked reader"
is not a middleware.
:::

:::exercise level=1
For each need, say whether it is middleware and, if so, of which scope:

1. Refuse requests without a token on the reader's routes.
2. Refuse a loan to a reader with a fine above five reais.
3. Add the `X-Request-Id` header to every API response.
4. Limit the collection search to sixty requests a minute per address.
5. Convert the book's title to uppercase before saving.

:::answer
1. Group middleware: `auth:sanctum` on the reader's route group.
2. No. It is a business rule, and it is already in `LoanService`.
3. Group middleware, on `api`. It is `LogsRequest`.
4. Route middleware: `throttle` with a `search` limiter.
5. No. Normalizing a specific field's input is the job of the Form
   Request's `prepareForValidation` — and, about uppercase, it is a decision
   Vera probably does not want: the title is stored as it is on the cover.

Item 5 often shows up as a middleware "that cleans the input", and becomes
the place where the normalization of every field of every route piles up
without anyone knowing which route depends on which cleaning.
:::

:::exercise level=2
Write a `RequiresMinimumVersion` middleware for the app's routes: if the
`X-App-Version` header comes with a version lower than the minimum set in
`config('app.min_version')`, the response is `426 Upgrade Required` in the
API's error format. Without the header, it lets the request through.

Say at which scope it should be registered.

:::answer
```php title="app/Http/Middleware/RequiresMinimumVersion.php" numbered
final class RequiresMinimumVersion
{
    public function handle(Request $request, Closure $next): Response
    {
        $version = $request->header('X-App-Version');
        $minimum = config('app.min_version');

        if ($version !== null
            && version_compare($version, $minimum, '<')) {
            return response()->json([
                'type' => 'outdated-version',
                'message' => 'Update the app to '
                    . 'continue.',
            ], 426);
        }

        return $next($request);
    }
}
```

`version_compare` is the PHP function that understands `1.10` is greater
than `1.9` — comparing as text would give the opposite.

**Scope:** group, only on the routes the app uses. Not global, because the
Blade panel and `/up` do not send the header and have no version.

Letting requests without the header through is deliberate: the oldest
versions of the app did not send the header, and refusing them would block
precisely the readers who most need a message telling them to update. A
better decision, in a second stage, is to treat its absence as "version
older than 1.2".
:::

:::exercise level=3
A teammate proposes a `LoadsReader` middleware for the app's route group: it
looks up the authenticated user's reader, with open loans and the fine, and
stores it on the `Request` for the controllers to use. "That way no
controller has to fetch it again."

Evaluate the proposal: what it solves, the three costs, and an alternative
that solves the same problem.

:::answer
**What it solves.** Real repetition: several of the app's controllers need
the current reader, and fetching it in each one is tedious.

**Cost one: a query on every route in the group.** The middleware loads
loans and fines even for `GET /books`, which uses none of that. Three more
queries on each collection search, the app's most used route.

**Cost two: stale data inside the transaction.** `LoanService` needs to read
the open loans **inside** the transaction, with a lock. If it starts using
what the middleware loaded earlier, the limit check gets back the race from
chapter @cap:do-arquivo-ao-banco. If it does not use it, the middleware
loaded it for nothing.

**Cost three: an invisible dependency.** The controller starts depending on
an attribute on the `Request` that someone put there in another file. A new
route in the wrong group receives `null`, and the error appears far from the
cause.

**Alternative.** The current reader is **one** cheap query, and only the
routes that need it should make it. A relationship on the `User` model:

```php
$reader = $request->user()->reader;
```

With the relationship, that is one query, only where it is called. Whatever
else each route needs — loans, fine — it loads with `load`, with the query
visible in the controller itself. The repetition that remains is one line,
and a repeated line that says exactly what it does is better than a layer
that does more than it seems.
:::
