---
source_hash: 5c6517ab9e0d
title: "Requests and responses"
number: 8
slug: requests-e-responses
part: p2
kicker: "The intern uploaded a book cover called ../test.php. The System stored it, and the server executed it."
goal: >-
  Get in and out of the application with objects: read the right data from
  the `Request`, return a response with the correct status and header, and
  receive a file without trusting anything the client sent.
---

:::story The cover that was a program
The System let the librarian attach a book's cover. Dedé asked Tainá to try
to break it, before deciding how to do the same in the new project.

She created a one-line file:

```php
<?php echo "hi, I'm a cover";
```

She renamed it to `../test.php`, attached it as a cover and saved. The System
replied that the cover had been uploaded successfully.

Then she opened the site's address with `/test.php` at the end.

```text
hi, I'm a cover
```

"Dedé."

"Go ahead."

"I just uploaded a program to the library's server."

Dedé looked over his monitor.

"Through the cover form?"

"Through the cover form."
:::

## `Request` is an object

Inside Laravel, you do not touch `$_GET`, `$_POST` or `$_SERVER`. Everything
that arrived is in an object the container hands to whoever declares the
type:

```php title="app/Http/Controllers/BookController.php" numbered
use Illuminate\Http\Request;

public function index(Request $request)
{
    $search = $request->query('q');
    $page = $request->integer('page', 1);

    return Book::search($search)->paginate(20, page: $page);
}
```

The difference is not cosmetic. The object knows how to answer questions the
superglobals do not:

| Method | Answers |
|---|---|
| `input('field')` | the value, whether from the URL or the body |
| `query('field')` | only what came in the URL |
| `post('field')` | only what came in the body |
| `header('Accept')` | a header, with its real name |
| `bearerToken()` | the token from `Authorization`, already split out |
| `expectsJson()` | whether the client wants JSON back |
| `file('cover')` | the uploaded file, as an object |

Table: `input()` is the most used and the least precise; it looks in both
places. When it matters where the value came from, use `query()` or
`post()`.

And the JSON body — which in raw PHP required `php://input` — is already
there:

```php
$request->input('copy_id');
```

Laravel reads the `Content-Type`, decodes the JSON and puts everything in the
same place. The stumbling block from chapter @cap:o-que-e-http stops existing
inside the framework; it still exists in every PHP that does not use a
framework, and that is why the mechanism was worth knowing.

## The right data, already in the right type

```php
$request->string('status')->toString();
$request->integer('page');
$request->boolean('only_available');
$request->date('returned_at');
$request->enum('status', CopyStatus::class);
```

Everything that arrives over HTTP is text. These methods do the conversion at
the border, which is where it should happen — and `enum()` refuses a value
that is not one of the cases, instead of letting the loose string travel on.

And there is a third group, the only one that **filters**:

```php
$data = $request->validate([
    'copy_id' => ['required', 'integer'],
    'reader_id' => ['required', 'integer'],
]);
```

`validate()` returns **only the declared fields**, already checked. If the
request does not pass, it stops right there and responds `422` with the list
of problems, without entering the rest of the method.

:::pitfall
The difference between `$request->all()` and what `validate()` returns is a
security flaw waiting for the right day.

```php
Book::create($request->all());
```

The client sends `title`, `year` — and `id`, `created_at` or any column they
find out exists. With `all()`, all of that reaches the database.

Use what `validate()` returns, which contains only what you declared. It is
the difference between "what the client sent" and "what I accept receiving".
:::

## Returning: array, model or response

The shortest way has already shown up: return an array or an object, and
Laravel converts it.

```php
return $book;                     // 200, the model's JSON
return Book::all();               // 200, the collection's JSON
return ['status' => 'ok'];        // 200, the array's JSON
```

When you need to decide the status or a header, the path is explicit:

```php
return response()->json($loan, 201)
    ->header('Location', route('loans.show', $loan));
```

```php
return response()->noContent();   // 204, empty body
```

```php
abort(404, 'Copy not found');
```

| Situation | What to return |
|---|---|
| a read that worked | the model or the collection |
| creation | `response()->json($x, 201)` with `Location` |
| a change with no body back | `response()->noContent()` |
| a system-state error | `abort(409, ...)` or the domain exception |

Table: The rule from chapter @cap:o-que-e-uma-api-rest still holds, and now
it has syntax.

:::key
`response()->noContent()` exists because `return null` from a controller
method returns `200` with the body `""` — and an empty body with a `200` is a
response the client has to interpret.

`204` says the same thing in the place the client is already looking: the
number.
:::

## The same route, two responses

Vera's dashboard and the readers' app can call the same route. What changes
is what each one knows how to display.

```php
if ($request->expectsJson()) {
    return response()->json(['error' => 'Copy unavailable'], 409);
}

return back()->withErrors(['copy' => 'Copy unavailable']);
```

`expectsJson()` looks at the `Accept` header the client sent. It is the same
negotiation the HTTP chapter described, now with a question instead of
reading the header by hand.

In practice, you will write that `if` rarely: splitting the routes into
`api.php` and `web.php` already solves most of it. It is for the case where
the route really is a single one.

## Uploads: trust nothing that came along

Back to Tainá's cover. The System did the equivalent of this:

```php
$name = $_FILES['cover']['name'];

move_uploaded_file($_FILES['cover']['tmp_name'], 'covers/' . $name);
```

There are three wrong decisions in two lines, and all have the same root:
**the client chose**.

**The file name came from the client.** `../test.php` goes up a level and
leaves the covers folder.

**The extension came from the client.** A `.php` stored inside the public
folder is a program the server executes when someone asks for it.

**The content was never checked.** Nothing guaranteed the file really is an
image.

The Laravel version decides all three things on this side:

```php title="app/Http/Controllers/CoverController.php" numbered
public function __invoke(Request $request, Book $book)
{
    $request->validate([
        'cover' => ['required', 'image', 'max:2048'],
    ]);

    $path = $request->file('cover')->store('covers', 'public');

    $book->update(['cover' => $path]);

    return response()->json(['cover' => $path], 201);
}
```

```text
{"cover":"covers/kR8mZ2qXv1nB7dLp0sYw.jpg"}
```

`store()` **generates** the name, from a random value, and chooses the
extension from the file's real type — not from what was written. The
client's original name is discarded.

The `image` rule checks the content, not the name. And `max:2048` is the size
in kilobytes, which is the limit that stops someone from filling the disk with
one request.

:::pitfall
There is a similar and dangerous method:

```php
$request->file('cover')->storeAs('covers', $request->file('cover')
    ->getClientOriginalName());
```

`getClientOriginalName()` returns exactly the text the client sent —
including `../test.php`. The method's name is honest: *client original*. It
is client data, like any form field.

If you really need to keep the original name — and sometimes you do, to
display it — store it **in a column**, as text, and let the name on disk be
generated.
:::

And a fourth protection, which is not in the code but in the structure: the
upload folder does not live inside `public/`. It lives in `storage/`, out of
the web server's reach, and files are served through a route or a declared
link. A `.php` that lands there is executed by nobody, because nobody can ask
for it through the URL.

:::note In your career
The conversation about uploads usually ends in "but the form only lets you
pick images". It is worth knowing how to answer that without sounding
arrogant, because the sentence is said in good faith.

The form is HTML running on the machine of whoever is on the other side. It
can be altered in the browser itself, or simply ignored — the request can be
built with `curl`, with no form at all. Everything that happens before it
reaches your server is a suggestion.

It is the same idea as chapter @cap:o-que-e-http, and it applies to format
validation, required fields and size limits: **the client checks to be
polite; the server checks because it is the only one that can.**
:::

:::tree title="Where we are now"
casa-amarela/
  app/Http/Controllers/
    BookController.php
    CoverController.php     # upload with a generated name
    ReturnController.php    # 204 with no body
    LoanController.php      # 201 with Location
  storage/app/public/
    covers/                 # out of the web's direct reach
:::

:::summary
- Inside Laravel, the request is an object; superglobals are not used.
- `input()` looks in the URL and the body; `query()` and `post()` are
  precise.
- The JSON body arrives already decoded, without `php://input`.
- `string()`, `integer()`, `boolean()`, `date()` and `enum()` convert at the
  border.
- `validate()` returns only the declared fields; `all()` returns whatever the
  client chose to send.
- Arrays and models become JSON on their own; `response()->json()` when the
  status or a header matters.
- `noContent()` is the `204`; `return null` is a `200` with an empty body.
- `expectsJson()` decides the format when the route serves both worlds.
- On upload, the name, extension and type come from the client: generate the
  name, check the content and store it outside `public/`.
:::

:::checkpoint
You read request data with the right method for each source, return
responses with the correct status and header, receive a file without using
anything the client chose, and can explain why the form's validation does
not count.
:::

:::exercise level=1
For each snippet, say what is wrong and fix it:

```php
$id = $_GET['book_id'];
```

```php
return null;  // return recorded, nothing to send back
```

```php
Book::create($request->all());
```

:::answer
**First.** A superglobal inside the framework. Besides bypassing the
`Request` object, it returns unconverted text and cannot be replaced in a
test.

```php
$id = $request->integer('book_id');
```

**Second.** `return null` produces `200` with an empty body. The client gets
a success and a body it has to interpret.

```php
return response()->noContent();
```

**Third.** Mass assignment of whatever the client sent. Any column they guess
gets in.

```php
$data = $request->validate([
    'title' => ['required', 'string', 'max:200'],
    'year' => ['nullable', 'integer'],
]);

Book::create($data);
```
:::

:::exercise level=2
Write `LoanController`'s `store` method to return `201` with the `Location`
header, and `ReturnController`'s `__invoke` to return `204`.

The return accepts an optional `status` field, which has to be one of
`CopyStatus`'s cases.

:::answer
```php title="app/Http/Controllers/LoanController.php" numbered
public function store(
    Request $request,
    LoanRecorder $loans,
) {
    $data = $request->validate([
        'copy_id' => ['required', 'integer'],
        'reader_id' => ['required', 'integer'],
    ]);

    $loan = $loans->record(
        copyId: $data['copy_id'],
        readerId: $data['reader_id'],
    );

    return response()
        ->json($loan, 201)
        ->header(
            'Location',
            route('loans.show', $loan),
        );
}
```

```php title="app/Http/Controllers/ReturnController.php" numbered
public function __invoke(Request $request, Loan $loan)
{
    $status = $request->enum('status', CopyStatus::class)
        ?? CopyStatus::Good;

    $this->returns->record($loan, $status);

    return response()->noContent();
}
```

`enum()` does three things in one line: it reads the field, refuses a value
that is not one of the cases and returns the enum object, not text. When the
field does not come, it returns `null`, and the `??` puts in the default.

Notice what was left out of both methods: the rule. The loan checks the limit
and availability inside the service; the return calculates the fine and
changes the copy's status inside its own. The controllers translate and
return.
:::

:::exercise level=3
A system accepts uploads of PDF receipts. The current code:

```php
$file = $request->file('receipt');
$name = $file->getClientOriginalName();

if (str_ends_with($name, '.pdf')) {
    $file->move(public_path('receipts'), $name);
}
```

List all the problems and rewrite it. Then answer: which of them still exists
even if the name is generated and the extension is checked?

:::answer
**The problems.**

The name comes from the client and is not cleaned: `../../public/x.php.pdf`
does not end in anything useful, but `..%2Fx.pdf` and other path variations
can escape the folder depending on the file system.

The check is by **name**, not by content. `virus.php.pdf` ends in `.pdf` and
is still whatever is inside it.

The destination is `public/`, that is, within the web server's reach.

There is no size limit: a two-gigabyte file is accepted until the disk runs
out.

There is no handling for the `if` being false: the file is silently discarded
and the user gets a success.

And `move()` into the public directory, with a predictable name, lets a
second upload overwrite another person's receipt.

**The rewrite.**

```php
$request->validate([
    'receipt' => ['required', 'file', 'mimes:pdf', 'max:5120'],
]);

$path = $request->file('receipt')
    ->store('receipts', 'local');

$payment->update([
    'receipt' => $path,
    'receipt_name' => $request->file('receipt')
        ->getClientOriginalName(),
]);
```

The original name goes into a **column**, to be displayed, not onto the disk.
The disk gets a generated name, on a `local` disk, which lives outside
`public/`.

**What still exists.** The content. `mimes:pdf` checks the file's type, and a
PDF can contain JavaScript, an embedded attachment or an exploit for the
reader of whoever opens it.

No upload validation makes a file safe — it only guarantees it is the
**type** you expected. Serving a file uploaded by a third party to other
users is a product decision, and the mitigations are different: antivirus
scanning, serving with `Content-Disposition: attachment` so it does not open
in the browser, and serving it from a domain different from the
application's.
:::
