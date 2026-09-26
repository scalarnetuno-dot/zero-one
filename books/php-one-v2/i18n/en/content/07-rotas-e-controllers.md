---
source_hash: 33e749a08ae9
title: "Routes and controllers"
number: 7
slug: rotas-e-controllers
part: p2
kicker: "The System's index had 137 lines, and each line was a file name. Nobody had ever read that index all the way through."
goal: >-
  Register the API routes designed earlier, with names, constraints and
  automatic record lookup — keeping controllers small and being able to
  justify the shape chosen for each one.
---

:::story One hundred and thirty-seven
Tainá tried to draw a map of the System to understand what was left to
migrate. She started by listing the screens.

```text
$ ls *.php | wc -l
137
```

"A hundred and thirty-seven screens?"

"A hundred and thirty-seven files," said Dedé. "Some are screens, some are
pieces of screens, and about fifteen aren't called by anybody."

"How do we know which fifteen?"

Dedé stared at the list for a while.

"We don't. Nobody deletes them because nobody's sure."
:::

## The routes file is the index

In the System, the application's index is the output of `ls`. In a Laravel
project, it is a file someone wrote on purpose — and that is the difference
between knowing what exists and guessing.

The skeleton comes with `routes/web.php` and `routes/console.php`. The API
file does not: it is installed when you need it.

```text
$ php artisan install:api
```

```text
   INFO  API scaffolding installed. Please add the
   [Laravel\Sanctum\HasApiTokens] trait to your User model.
```

The command creates `routes/api.php`, registers the file in
`bootstrap/app.php` and installs the token authentication package.

## `web.php` and `api.php`: two worlds

The two files exist because they serve different clients, and the difference
is not organizational — it is behavioral.

| | `web.php` | `api.php` |
|---|---|---|
| URL prefix | none | `/api` |
| session and cookie | yes | no |
| CSRF protection | yes | makes no sense |
| who consumes it | browser | app, script, another system |
| an error returns | an HTML page | JSON |

Table: A route in the wrong file does not raise an error. It behaves in a way
nobody can explain — an API that demands a form token, or a screen that loses
the login on every click.

:::key
The question that decides the file is not "does this return JSON?". It is:
**does whoever calls this have a session open in a browser?**

Vera's dashboard does. The readers' app does not — it carries the credential
in every request, as chapter @cap:o-que-e-http described.
:::

## Casa Amarela's routes

The design from chapter @cap:o-que-e-uma-api-rest, now written down:

```php title="routes/api.php" numbered
<?php

declare(strict_types=1);

use App\Http\Controllers\ReturnController;
use App\Http\Controllers\LoanController;
use App\Http\Controllers\CopyController;
use App\Http\Controllers\BookController;
use Illuminate\Support\Facades\Route;

Route::apiResource('books', BookController::class);

Route::get('books/{book}/copies', [
    CopyController::class, 'byBook',
])->name('books.copies');

Route::post('loans', [LoanController::class, 'store'])
    ->name('loans.store');

Route::post(
    'loans/{loan}/return',
    ReturnController::class,
)->name('loans.return');
```

```text
$ php artisan route:list --path=api
```

```text
  GET|HEAD   api/books .................... books.index
  POST       api/books .................... books.store
  GET|HEAD   api/books/{book} ............. books.show
  PUT|PATCH  api/books/{book} ............. books.update
  DELETE     api/books/{book} ............. books.destroy
  GET|HEAD   api/books/{book}/copies ...... books.copies
  POST       api/loans .................... loans.store
  POST       api/loans/{loan}/return ...... loans.return
```

Four lines of file became eight routes, and the table above is the index the
System never had.

`Route::apiResource` registers a resource's five operations at once. It is
the sibling of `Route::resource`, which registers seven — the two extra ones
return HTML forms, and an API has no forms.

## Parameters and constraints

`{book}` matches anything that is not a slash. That is too generous when the
parameter is a number:

```php
Route::get('books/{book}', [BookController::class, 'show'])
    ->whereNumber('book');
```

Now `/api/books/abc` does not match this route, and the `404` happens in the
router — before there is a database query with text in place of an
identifier.

:::pitfall
Route order matters, and the bug is silent.

```php
Route::get('books/{book}', [BookController::class, 'show']);
Route::get('books/featured', [BookController::class, 'featured']);
```

The second route never runs. The router tests in the order they were
registered, and `featured` matches `{book}` — so the application will look
for a book whose identifier is the word `featured`, and return `404` for a
route that exists.

Two ways out: **fixed path before parameterized path**, always; or constrain
the parameter, which solves both problems with one line.
:::

## The parameter that arrives already turned into a record

The controller could receive the number and look up the book:

```php
public function show(int $id)
{
    $book = Book::findOrFail($id);
    // ...
}
```

Three lines like these in every method, in every controller. Laravel offers
another path: if the route parameter's name matches the method parameter's
name, and the type is a model, it looks the record up on its own.

```php
public function show(Book $book)
{
    return $book;
}
```

```text
GET /api/books/12   → book 12
GET /api/books/999  → 404, without entering the method
```

:::term Route model binding
The framework reads the parameter's type, looks up the record by primary key
and hands over the ready object. When it does not find it, it returns `404`
before calling your code.

It is convenience with a good side effect: the missing-record `404` is now
handled in one place, instead of depending on each method remembering.
:::

You can look up by another column, when the public identifier is not the
number:

```php
Route::get('copies/{copy:accession}', ...);
```

Then `{copy:accession}` searches by the `accession` column, which is the
number stuck on the label and what Vera types.

## Route names: the URL that changes without breaking anything

Every route in the example has `->name()`, and `apiResource` generates the
names on its own. The gain shows up when someone needs to build a URL:

```php
route('books.show', ['book' => 12]);
// http://localhost:8000/api/books/12
```

Instead of writing the path by hand in seventeen places. On the day
`/api/books` becomes `/api/catalog`, the seventeen keep working, and
`route:list` is still the index.

The name is also what lets the route be referenced elsewhere in the
framework — redirects, authorization, and a `201`'s `Location` header.

## Three controller shapes, and what each one says

```text
$ php artisan make:controller BookController --api
```

A **resource controller** groups a noun's operations. The method names are a
convention — `index`, `store`, `show`, `update`, `destroy` — and whoever
opens the file already knows what they will find.

```php title="app/Http/Controllers/BookController.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Book;

class BookController extends Controller
{
    public function index()
    {
        return Book::query()->orderBy('title')->paginate(20);
    }

    public function show(Book $book)
    {
        return $book;
    }
}
```

An **invokable controller** has a single method, `__invoke`, and is
registered by the class name. It says one thing: *this class does one
action, and only one*.

```php title="app/Http/Controllers/ReturnController.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Loan;
use App\Services\ReturnRecorder;
use Illuminate\Http\Request;

class ReturnController extends Controller
{
    public function __construct(
        private readonly ReturnRecorder $returns,
    ) {}

    public function __invoke(Request $req, Loan $loan)
    {
        $this->returns->record(
            $loan,
            $req->string('status', 'good')->toString(),
        );

        return response()->noContent();
    }
}
```

A **plain controller**, with freely named methods, is what is left over:
useful when the actions neither form a resource nor are a single one.

:::key
The choice between the three is a message to whoever reads it later.

Resource says "this is where a noun's operations live". Invokable says "this
is an isolated action, with its own name". Plain says nothing — and that is
why it is what you use when there is nothing to say.
:::

## The controller does not need to know everything

Look at `ReturnController`: it receives the loan ready, calls a service and
returns `204`. Seven useful lines.

That is the right size. A controller has three jobs, and none of them is
business rules:

1. **translate the request** into arguments;
2. **call whoever knows how to do it**;
3. **translate the result** into a response.

:::pitfall
The symptom that the rules have leaked into the controller is the
constructor:

```php
public function __construct(
    private Calculator $calc,
    private Stock $stock,
    private Notifier $notifier,
    private Audit $audit,
    private Report $report,
    private Cache $cache,
    private Queue $queue,
    private Log $log,
) {}
```

Eight dependencies are not an injection problem. They are the warning that
this controller is orchestrating a business process — and a business process
has a name, has its own tests and does not depend on HTTP to exist.

The fix is not shortening the list: it is moving the process into a class the
controller calls in one line.
:::

And logic **inside the routes file** is the same disease, one floor up. An
anonymous function fifteen lines long in `routes/api.php` has no tests, no
name, and blocks `route:cache` — which refuses routes with anonymous
functions, because there is no way to store a function in a cache file.

:::note In your career
In an interview or a review, "fat controller" is a criticism that is easy to
make and hard to justify. The justification that works is always the same
question: **how do I test this without firing a request?**

If the rule is in the controller, the answer is "I don't" — and then the
discussion stops being about aesthetics and becomes about the cost of
checking whether the fine is right.

It works for the opposite case too. When someone proposes splitting a
seven-line controller into four classes, the same question answers it: if it
can already be tested and already be read, the split is solving a problem
that does not exist.
:::

:::tree title="Where we are now"
casa-amarela/
  routes/
    api.php      # the API's eight routes, with names
    web.php
    console.php
  app/
    Http/Controllers/
      BookController.php        # resource
      CopyController.php
      LoanController.php
      ReturnController.php      # invokable
    Services/
      ReturnRecorder.php
:::

:::summary
- `routes/api.php` is installed by `install:api`, gets the `/api` prefix and
  has no session and no CSRF.
- The question that chooses the file is whether the caller has a browser
  session.
- `apiResource` registers a resource's five operations, with names.
- A fixed path comes before a parameterized path — or the parameter is
  constrained.
- Route model binding looks up the record by the parameter's type and returns
  `404` before entering the method.
- `{copy:accession}` looks up by another column when the public identifier is
  not the id.
- Route names let you change the URL without hunting strings through the
  project.
- Resource, invokable and plain say different things to whoever reads them.
- A controller translates, calls and returns; eight dependencies in the
  constructor signal a business process in the wrong place.
:::

:::checkpoint
You register a set of REST routes with names and constraints, know why a
fixed route after a parameterized one never runs, use binding to receive the
record ready, and justify the controller shape you chose.
:::

:::exercise level=1
Say what is wrong with each block and fix it:

```php
Route::get('loans/{loan}', [C::class, 'show']);
Route::get('loans/overdue', [C::class, 'overdue']);
```

```php
Route::get('readers/{reader}', function ($id) {
    $reader = Reader::find($id);

    if (!$reader) {
        return response()->json(['error' => 'not found'], 404);
    }

    return $reader;
});
```

:::answer
**First block: order.** The overdue route never runs — `overdue` matches
`{loan}`. Fix it by swapping, or by constraining:

```php
Route::get('loans/overdue', [C::class, 'overdue']);
Route::get('loans/{loan}', [C::class, 'show'])
    ->whereNumber('loan');
```

With `whereNumber`, the order stops mattering — and that is the safest fix,
because it does not depend on anyone remembering it when adding the next
route.

**Second block: three problems.**

The anonymous function in the routes file blocks `route:cache` and cannot be
tested in isolation.

The manual lookup and `404` repeat, in every route, what binding does on its
own.

And the parameter is called `{reader}` but the function receives `$id` — it
works by position and breaks the day someone adds another parameter.

```php
Route::get('readers/{reader}', [ReaderController::class, 'show'])
    ->whereNumber('reader')
    ->name('readers.show');
```

```php
public function show(Reader $reader)
{
    return $reader;
}
```
:::

:::exercise level=2
Register the routes still missing from Casa Amarela's design: a reader's
renewals, a reader's loans and the catalog search.

Name all of them, constrain the numeric parameters and say which file each
goes in.

:::answer
```php title="routes/api.php" numbered
Route::get('books', [BookController::class, 'index'])
    ->name('books.index');

Route::post(
    'readers/{reader}/renewals',
    RenewalController::class,
)->whereNumber('reader')->name('readers.renewals');

Route::get('readers/{reader}/loans', [
    LoanController::class, 'byReader',
])->whereNumber('reader')->name('readers.loans');
```

All three go in `routes/api.php`: whoever consumes them is the readers' app,
which has no browser session.

The search does **not** get its own route. It is `books.index` with query
parameters — `/api/books?q=machado&subject=literature` — and it is the same
decision as in the REST chapter: a combinable filter does not become an
address.

The renewal is an invokable controller: it is a single action, has its own
name and creates a resource. And notice that it is a `POST` even though it is
an operation Vera would call "updating" — the noun hidden there is the
renewal, and it is born each time.
:::

:::exercise level=3
This controller came in for review. It works and the request tests pass.

```php
class LoanController extends Controller
{
    public function store(Request $request)
    {
        $copy = Copy::find($request->copy_id);
        $reader = Reader::find($request->reader_id);

        if (!$copy || !$reader) {
            return response()->json(['error' => 'invalid'], 404);
        }

        if ($copy->status !== 'good') {
            return response()->json(['error' => 'unavailable'], 409);
        }

        $open = Loan::where('reader_id', $reader->id)
            ->whereNull('returned_at')->count();

        $limit = date('n') == 1 ? 5 : 3;

        if ($open >= $limit) {
            return response()->json(['error' => 'limit'], 409);
        }

        $loan = Loan::create([
            'copy_id' => $copy->id,
            'reader_id' => $reader->id,
            'borrowed_at' => now(),
            'due_on' => now()->addDays(14),
        ]);

        $copy->update(['status' => 'on_loan']);

        return response()->json($loan, 201);
    }
}
```

Point out the four problems and show what the method looks like afterwards.

:::answer
**One: the whole business rule is in here.** The per-reader limit, the
January rule, the loan period, the copy's status change. None of it depends
on HTTP, and all of it needs to be tested without firing a request — today
it cannot be.

**Two: the numbers are loose.** `14`, `3`, `5` and `'good'` are the same
rules that got an address in `config/library.php`. Here they diverged from
the configuration file the moment they were written.

**Three: there is no transaction.** Between creating the loan and changing
the copy there is an interval. If the second operation fails, an open loan is
left for a copy still marked as available — the race from chapter @cap:pdo,
back again.

**Four: validation is done with `if`s.** A missing field becomes `null`,
`find` returns `null`, and the response is `404` for a request that was a
`422`. The two codes say different things to whoever consumes them.

```php title="app/Http/Controllers/LoanController.php" numbered
public function store(
    CreateLoanRequest $request,
    LoanRecorder $loans,
) {
    $loan = $loans->record(
        copyId: $request->integer('copy_id'),
        readerId: $request->integer('reader_id'),
    );

    return response()
        ->json($loan, 201)
        ->header('Location', route('loans.show', $loan));
}
```

The controller is back to three jobs. Format validation moved out to a
request class; the rule moved out to a service that opens a transaction,
reads the configuration and throws the domain exceptions from chapter
@cap:excecoes; and the `201`'s `Location` appeared, which the original did
not have.

It is worth saying what is **not** a problem in the original code: it is not
wrong. It does the right thing, and does it in a place where nobody can check
it on its own — and that is the difference between working today and still
working in March.
:::
