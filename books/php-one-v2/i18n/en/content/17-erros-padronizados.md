---
source_hash: caacd823bc76
title: "Standardized errors"
number: 17
slug: erros-padronizados
part: p4
kicker: "The reader called saying there was an error. The log had 4,200 lines and no clue which one was his."
goal: >-
  Make every API error response have the same format, translate domain
  exceptions into statuses in one line, never leak internal detail, and
  hand support a number that leads straight to the right log line.
---

:::story There was an error
The library phone rang at 10:20. Vera answered, listened, and passed it to
Tainá without saying anything, which was already a way of saying something.

— Hi, it's Wellington. I tried to borrow a book through the app and there
was an error.

— What error?

— An error. It said "Server Error". Then I tried again and it happened
again.

— What time was that?

— Just now. I mean, about ten minutes ago. Or fifteen.

Tainá opened the staging `laravel.log`, which that week was also serving the
first tests with real readers. Four thousand two hundred lines since nine.
She searched for "Wellington": nothing — the log had nobody's name. She
searched for "ERROR": thirty-one occurrences between 10:00 and 10:20.

She picked the one that looked most like a loan. A `QueryException` with an
eighty-line *stack trace*. She spent forty minutes on it, found the cause,
opened the ticket.

Dedé read the ticket after lunch.

— That error is from the nightly importer. It ran again at ten because
Cléber triggered it by hand.

— And Wellington's?

— Must be one of the other thirty.

Wellington called again at 2 p.m. He had managed to get the book at the
counter. He wanted to know whether the app was going to charge him twice.
:::

## Three error formats in the same API

Take inventory of what Casa Amarela's API returns today when something goes
wrong. There are four situations, and each one comes out differently:

```json
// 422, Form Request validation
{"message": "The title field is required.",
 "errors": {"title": ["The title field is required."]}}

// 409, abort() in the controller
{"message": "Copy unavailable"}

// 404, route model binding
{"message": "No query results for model [App\\Models\\Book] 99999"}

// 500, with APP_DEBUG=true
{"message": "SQLSTATE[23000]: Integrity constraint violation...",
 "exception": "Illuminate\\Database\\QueryException",
 "file": "/var/www/vendor/laravel/framework/...",
 "line": 822,
 "trace": [ ... 80 items ... ]}
```

Four formats similar enough to deceive and different enough to break. The
app needs an `if` for each one — and the `if` that reads `message` to decide
what to do breaks the day someone rewords the sentence.

And the last one leaks, in order: the SQL with the table and constraint
names, the internal class name, the project's path on the server, the
framework version through the folder structure, and eighty lines of
execution path. It is a map of the system handed to whoever made the
request.

:::key
One error format, for the whole API, matters more than the format being
perfect. The client writes the handling **once** and trusts it.

Three correct formats, each in its own corner, are worse than a single
imperfect format, everywhere.
:::

## The format

Casa Amarela adopts a format with four keys:

```json
{
  "type": "copy-unavailable",
  "message": "Copy 2117 is on loan.",
  "fields": { "copy_id": ["Copy unavailable."] },
  "incident": "01JHQ4Z8K3M2X9V7B5N1P0R6TW"
}
```

**`type`** is a stable identifier, in text, that the client uses to decide.
It **never changes**, not even when the message is rewritten. It is what the
app's `if` compares.

**`message`** is for a person to read. It can change, be translated, gain
accents. No code should decide anything based on it.

**`fields`** is optional and appears when the error has a guilty field —
always on `422`, sometimes on `409`. It is the same map as the `errors` from
chapter @cap:validation-e-form-requests.

**`incident`** is optional and appears when the failure is the server's. It
is the number Wellington reads to Tainá over the phone.

:::trivia
There is a specification for this, RFC 9457, *Problem Details for HTTP
APIs*, with the keys `type`, `title`, `status`, `detail` and `instance`.
Casa Amarela's format is a simplified version of the same idea.

If your API will be consumed by many teams you do not know, following the
RFC to the letter saves a conversation on every integration. If it is a
library's app, fewer keys are easier to read, and what matters is the
discipline — one format, always.
:::

## The handler, where every exception ends up

In Laravel 11, the place where every uncaught exception arrives is
`bootstrap/app.php`, in the `withExceptions` block. It is the
`set_exception_handler` from chapter @cap:excecoes, with the framework
around it.

```php title="bootstrap/app.php" numbered
->withExceptions(function (Exceptions $exceptions) {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $r) => $r->is('api/*') || $r->expectsJson(),
    );

    $exceptions->render(
        fn (Throwable $e, Request $r) => $r->is('api/*')
            ? ErrorResponse::for($e)
            : null,
    );
})
```

`render` receives every exception. If the request is for the API, a class
decides the response. If it is not, it returns `null`, and Laravel does what
it would normally do — shows the Blade panel's error page.

The class that decides is a translation, and a translation is a `match`:

```php title="app/Http/ErrorResponse.php" numbered
final class ErrorResponse
{
    public static function for(Throwable $e): JsonResponse
    {
        return match (true) {
            $e instanceof ValidationException
                => self::validation($e),
            $e instanceof DomainError
                => self::domain($e),
            $e instanceof ModelNotFoundException,
            $e instanceof NotFoundHttpException
                => self::body(404, 'not-found',
                    'The requested resource does not exist.'),
            $e instanceof AuthenticationException
                => self::body(401, 'unauthenticated',
                    'You need to sign in to continue.'),
            $e instanceof AuthorizationException
                => self::body(403, 'forbidden',
                    'You are not allowed to do that.'),
            $e instanceof ThrottleRequestsException
                => self::body(429, 'too-many-requests',
                    'Too many attempts. Wait a little.'),
            default => self::internalFailure($e),
        };
    }

    // ...
}
```

One list, one read. Whoever wants to know what the API answers for each
kind of failure reads one file.

## A domain exception becomes a status in one line

The three exceptions from chapter @cap:excecoes — `CopyUnavailable`,
`LoanLimitReached`, `ReaderHasPendingItems` — already carry data. What is
missing is for each one to state its `type`. A parent class solves it:

```php title="app/Loans/DomainError.php" numbered
abstract class DomainError extends RuntimeException
{
    abstract public function type(): string;

    public function status(): int
    {
        return 409;
    }

    public function fields(): ?array
    {
        return null;
    }
}
```

```php title="app/Loans/CopyUnavailable.php" numbered
final class CopyUnavailable extends DomainError
{
    public function __construct(
        public readonly int $accession,
        public readonly CopyStatus $status,
    ) {
        parent::__construct(sprintf(
            'Copy %d is %s.',
            $accession,
            mb_strtolower($status->label()),
        ));
    }

    public function type(): string
    {
        return 'copy-unavailable';
    }

    public function fields(): array
    {
        return ['copy_id' => ['Copy unavailable.']];
    }
}
```

And the translation, in `ErrorResponse`, is generic:

```php
private static function domain(DomainError $e): JsonResponse
{
    return self::body(
        $e->status(),
        $e->type(),
        $e->getMessage(),
        $e->fields(),
    );
}
```

A new domain exception — `ReservationExpired`, say — extends `DomainError`,
declares its `type`, and leaves the API in the right format without anyone
touching the handler.

:::http title="The same error, before and now"
POST /api/loans
Content-Type: application/json

{"copy_id": 2117, "reader_id": 47}
---
409 Conflict
Content-Type: application/json

{
  "type": "copy-unavailable",
  "message": "Copy 2117 is on loan.",
  "fields": { "copy_id": ["Copy unavailable."] }
}
:::

It is the response exercise 3 of chapter @cap:validation-e-form-requests
promised: the status tells the truth, and the screen knows which field to
highlight.

With that, the controller's `abort(409, ...)` calls from chapter
@cap:o-crud-completo can be swapped for
`throw new CopyUnavailable(...)`. And the controller stops knowing HTTP
statuses for business rules — which chapter @cap:services will turn into a
principle.

:::pitfall
The temptation, once you have the handler, is to use exceptions for
everything — including what is not an error. "Book has no copies" is not an
exception; it is an empty list. "Reader with no loans" is `[]`, with `200`.

The yardstick is the one from chapter @cap:excecoes: an exception is for
when the operation **cannot continue**. A query that found nothing continued
and finished well.
:::

## The binding's `404`: useful and too generic

The route model binding's automatic `404` is a gift, and it comes with a
message that should not go out:

```text
No query results for model [App\Models\Book] 99999
```

It reveals the namespace and the internal class name. It is not a serious
flaw — it opens no door —, but it is information the client does not need
and a curious person notes down.

The `match` above already swaps the message for the generic one. And there
is a decision to make about **when `404` is the right answer for something
else**: reader 47 asks for loan 312, which exists and belongs to someone
else. Is the answer `403` or `404`?

| Response | Tells the client |
|---|---|
| `403` | "this exists, and it isn't yours" |
| `404` | "this doesn't exist for you" |

Table: Both are correct HTTP. The first confirms the resource exists, and
that is sometimes too much information.

For loans, confirming that number 312 exists says little. For a route like
`/readers?document=...`, confirming that a CPF is registered at the library
says a lot. Casa Amarela's rule: `404` when the resource's existence is,
itself, personal data. Chapter @cap:autorizacao applies it.

## `500` leaks nothing

The last line of the `match` — the `default` — is the most important,
because it is the one nobody planned:

```php title="app/Http/ErrorResponse.php" numbered
private static function internalFailure(Throwable $e): JsonResponse
{
    $status = $e instanceof HttpExceptionInterface
        ? $e->getStatusCode()
        : 500;

    return self::body(
        $status,
        'internal-failure',
        'Something went wrong on our side. Give the '
            . 'code to support.',
        incident: Incident::current(),
    );
}
```

The response has an honest sentence and a number. No line of SQL, no class
name, no file path.

The detail still exists — **in the log**, where whoever needs it can read
it. Laravel records the exception before calling `render`, and what goes to
the client and what goes to the log are separate decisions.

:::warning
None of this holds with `APP_DEBUG=true`. With it on, Laravel adds the
exception, the file, the line and the full *trace* to the response, on top
of what the handler built, to help in development.

In production, `APP_DEBUG=false` is the first line of the list in chapter
@cap:git-ci-e-deploy, and the one that shows up most in breach reports.
There are search engines that index Laravel error pages with debug mode on
— and they often include the contents of `.env`.
:::

## Incident code: the number support asks for

Wellington had no way of saying which of the 31 lines was his. With the
incident, he does: it is on the app's screen, and the app can even offer a
button to copy it.

```php title="app/Support/Incident.php" numbered
final class Incident
{
    public static function current(): string
    {
        if (!Context::has('incident')) {
            Context::add('incident', (string) Str::ulid());
        }

        return Context::get('incident');
    }
}
```

`Context` is a data area that lives for the duration of the request, and
Laravel **adds everything in it to every log line** written afterwards. When
the exception is recorded, the line comes out with the incident attached:

```text
[2026-02-10 10:14:07] production.ERROR: SQLSTATE[23000]...
{"exception":"...","incident":"01JHQ4Z8K3M2X9V7B5N1P0R6TW"}
```

And the search that took forty minutes now takes one command:

```text
$ grep 01JHQ4Z8K3M2X9V7B5N1P0R6TW storage/logs/laravel.log
```

A ULID is a unique identifier that starts with the instant it was generated,
so incidents from the same minute sit close together when sorted. It is a
small detail that helps when someone says "it was around ten".

For now, the incident is born at the moment of the error. In chapter
@cap:middleware, it starts being born **at the beginning of every request**,
and every log line of that request — not just the error's — carries the
same number. It is the difference between finding the exception and finding
the whole story that led to it.

## `401` and `403` are not the same thing

The handler's list has both, and they get confused enough to deserve their
own section.

**`401 Unauthorized`** means: **I don't know who you are**. The token is
missing, or it expired, or it is invalid. The client should send the person
to sign in again.

**`403 Forbidden`** means: **I know who you are, and you can't**. The token
is valid. Signing in again solves nothing.

The official name of `401` is unfortunate — it says *unauthorized* and means
"unauthenticated". The confusion comes from there, and the consequence is
concrete: an app that receives `401` when it should receive `403` sends the
person to the login screen, they sign in, try again, back to the login
screen. An infinite loop, with the person convinced their password is
wrong.

| Status | Question that failed | The client does |
|---|---|---|
| `401` | who are you? | asks for login |
| `403` | are you allowed? | shows "not allowed" |
| `404` | does it exist? | shows "not found" |
| `409` | does the world allow it? | explains and offers a way out |
| `422` | is the request right? | highlights the fields |

Table: Five statuses, five questions, five screen behaviors. It is the table
the reader app implements, and the reason each one exists.

:::note In your career
An API's error format is the part of the contract that costs most to change
later, because every client handles it in one central place — and changing
that central place changes the behavior of every screen at once.

If you are at the start of an API, spend an afternoon on this before you
have twenty routes. If you are on an API that already has three formats, the
path is the usual one: the new format starts going out on every route, with
the old fields kept alongside until the last client migrates. It is
laborious and invisible, and it is the kind of thing that separates people
who maintain systems from people who only write routes.
:::

:::tree title="Where we are now"
casa-amarela/
  bootstrap/app.php            # withExceptions → ErrorResponse
  app/Http/
    ErrorResponse.php          # one match, the whole API
  app/Support/
    Incident.php               # ULID in the Context
  app/Loans/
    DomainError.php            # type(), status(), fields()
    CopyUnavailable.php
    LoanLimitReached.php
    ReaderHasPendingItems.php
:::

:::milestone
End of Part 4. Casa Amarela's API refuses malformed input at the door,
returns only what it decided to return, lists the whole collection with
search, filter and ceiling, and answers every error in the same format —
with a number that leads support to the right log line.

In Tainá's notebook, a new line: *"the client doesn't read the message, it
reads the type"*.
:::

:::summary
- One error format for the whole API is worth more than three correct
  formats.
- `type` is stable and the client decides by it; `message` is for people and
  can change.
- The `render` in `withExceptions` receives every exception; a `match`
  translates type into response.
- Domain exceptions extend a parent class with `type`, `status` and
  `fields`; a new one comes out in the right format without touching the
  handler.
- The binding's `404` needs a generic message; `403` or `404` for someone
  else's resource is a decision about what existence reveals.
- `500` carries no SQL, class, file or *trace*; the detail goes to the log.
- `APP_DEBUG=true` in production cancels the handler and leaks the system.
- The incident in the `Context` appears in every log line and in the
  response, and turns a forty-minute search into a `grep`.
- `401` is "I don't know who you are"; `403` is "I do, and you can't".
:::

:::checkpoint
Every API error response has the same format, domain exceptions become
`409` without `abort` in the controller, no internal failure leaks detail,
and you can explain, for each of the five error statuses, what the client's
screen should do when receiving it.
:::

:::exercise level=1
For each situation, give the status and the `type` Casa Amarela's API
returns:

1. The app's token expired.
2. The reader tries to renew a loan that has already been renewed twice.
3. The `POST /loans` body came without `reader_id`.
4. The database is down.
5. A clerk tries to delete a book, and only an admin can.

:::answer
1. `401`, `unauthenticated`. The app takes the person to login.
2. `409`, with a domain type — something like `renewals-exhausted`. The
   request is right; the rule won't allow it.
3. `422`, with `fields.reader_id`. The type can be `validation`.
4. `500` — or `503`, if the failure is detected as unavailability —,
   `internal-failure`, with `incident`. No mention of a database in the
   message.
5. `403`, `forbidden`. She is authenticated; her role does not allow it.

Item 4 is the one most tempting to leak: "database unavailable" looks like
an honest and useful message. It tells whoever is attacking that the attack
worked.
:::

:::exercise level=2
Write `ReaderHasPendingItems` extending `DomainError`. It carries the
reader's id and the outstanding fine as `Money`, and the message must state
the formatted amount.

Then answer: should the fine's amount appear in the API response? For whom?

:::answer
```php title="app/Loans/ReaderHasPendingItems.php" numbered
final class ReaderHasPendingItems extends DomainError
{
    public function __construct(
        public readonly int $readerId,
        public readonly Money $fine,
    ) {
        parent::__construct(sprintf(
            'There is an outstanding fine of %s.',
            $fine->formatted(),
        ));
    }

    public function type(): string
    {
        return 'reader-has-pending-items';
    }
}
```

**Should it appear?** For the reader themselves and for staff, yes: it is
the information that lets them resolve it. The reader wants to know how
much to pay.

The caution is that the message goes to **whoever made the request**, and in
the clerk's panel whoever made the request is the clerk — who is entitled to
the data. In the app, only the reader can request a loan in their own name,
so only they see it.

If one day there is a route where one reader acts on behalf of another — a
reservation for a dependent, for example —, this message starts leaking one
person's debt to another. It is worth noting the risk in the class, because
it is the kind of thing whoever creates the new route will not remember to
check.
:::

:::exercise level=3
A teammate proposes removing `ErrorResponse` and, instead, putting a
`try/catch` in each controller, "so each route has full control of its
error response".

Write the arguments in favor they probably have, the three concrete costs of
the proposal, and the case in which a `try/catch` in the controller is, in
fact, the right choice.

:::answer
**In favor, probably.** Locality: whoever reads the controller sees what
happens on each failure, without opening another file. Flexibility: a
specific route may want a different response for the same exception.

**Cost one: the format diverges.** Thirty controllers with `try/catch` are
thirty places building the error JSON, and in six months there are four
different formats. It is the problem the chapter started out solving.

**Cost two: the `default` disappears.** The central handler guarantees that
**every** unforeseen exception becomes a safe `500` with an incident. The
`try/catch` in the controller handles the ones the author remembered; the
one they did not remember bubbles up unhandled — or, worse, is caught by a
`catch (\Throwable $e)` that returns the raw message.

**Cost three: the controller grows again and learns statuses.** Each method
gains ten lines of `catch` that are not its responsibility.

**When the `try/catch` in the controller is right:** when the exception
changes **the path** and not just the response. The Blade panel from
chapter @cap:blade catches `CopyUnavailable` to send the person back to the
form with the error on the field — there, the behavior is different, not
just the format. And when a route needs to try an alternative: if the cover
is not found in storage, return the default cover.

The yardstick: the controller catches when it **does something different**
with the failure. When it is only going to format, the handler already does
that.
:::
