---
source_hash: 04fb68b9083d
title: "The complete CRUD"
number: 13
slug: o-crud-completo
part: p4
kicker: "Seu Juvenal asked whether that wasn't just a CRUD. The answer had eleven items and was in the intern's notebook."
goal: >-
  Wire routes, controllers, models and database with the five operations
  returning the right status, make a business operation fit in one commit,
  and finish knowing how to list what is still wrong.
---

:::story Just a CRUD
The book registration screen was ready on Wednesday. Dedé showed it: list,
open, edit, delete.

— Nice — said Seu Juvenal. — But isn't that just a CRUD?

Tainá turned her notebook to the first week's page and read aloud.

— If she's a member. If she has no overdue book. If she doesn't owe a fine
over five reais. If she doesn't already have three books. If the copy isn't
from the reference section. If it isn't the title's last copy. If she's
under twelve, a guardian signs. If the book arrived this week, it stays on
display. If it's exam season, the loan drops to seven days. If it's from
your collection, sir, it doesn't go out. And if it's Dona Marlene, it goes
out.

She stopped.

— Eleven.

— Right — said Dedé. — Which of the five screens does that fit on?

Seu Juvenal thought for a moment.

— The lending one.

— The lending one isn't there.
:::

:::art caption="The CRUD fits on five screens. The lending rule doesn't."
src="o-crud-cabe-em-cinco-telas-a-regra-de-emprestar-nao.png"
Minimalist editorial cartoon on a white background: a whiteboard with five
small, tidy boxes labeled "list", "open", "create", "edit" and "delete". In
front of the board, an intern reads aloud from an open notebook from which a
long strip of paper, like a receipt roll, runs down to the floor and across
the room, full of lines starting with "IF". An older man in a cap looks at
the five boxes and then at the strip, scratching his head. A developer,
arms crossed, points at the empty space where a sixth box would be missing.
Few elements, dry humor, tech-magazine aesthetic.
:::

## The five routes and what each one promises

The collection's CRUD is five operations, and their design was done in
chapter @cap:o-que-e-uma-api-rest. Now they become code.

```php title="routes/api.php" numbered
Route::apiResource('books', BookController::class);
```

| Method | Route | Promises | Returns |
|---|---|---|---|
| `index` | `GET /books` | the list, paginated | `200` |
| `store` | `POST /books` | create a new one | `201` + `Location` |
| `show` | `GET /books/{book}` | one item | `200` or `404` |
| `update` | `PUT/PATCH /books/{book}` | change | `200` or `404` |
| `destroy` | `DELETE /books/{book}` | remove | `204` or `404` |

Table: Five rows anyone who has ever consumed an API can guess without
documentation. That is the whole value of the convention.

## Create

```php title="app/Http/Controllers/BookController.php" numbered
public function store(Request $request)
{
    $data = $request->validate([
        'title' => ['required', 'string', 'max:200'],
        'author' => ['required', 'string', 'max:150'],
        'subject' => ['required', 'string', 'max:40'],
        'isbn' => ['nullable', 'string', 'size:13', 'unique:books'],
        'year' => ['nullable', 'integer', 'min:1400'],
    ]);

    $book = Book::create($data);

    return response()
        ->json($book, 201)
        ->header('Location', route('books.show', $book));
}
```

:::http title="Creation, end to end"
POST /api/books
Content-Type: application/json

{"title": "Vidas Secas", "author": "Graciliano Ramos",
 "subject": "literature", "year": 1938}
---
201 Created
Location: /api/books/4031
Content-Type: application/json

{
  "id": 4031,
  "title": "Vidas Secas",
  "author": "Graciliano Ramos",
  "subject": "literature",
  "year": 1938,
  "created_at": "2026-01-21T14:02:55.000000Z"
}
:::

Three decisions are in those ten lines.

**The resource comes back in the body.** The client has just created
something and needs the `id` to continue. Returning nothing would force a
second request.

**`Location` points to where it lives.** It is what lets the client look it
up later without building the URL by hand.

**Validation is in the controller.** It works, and it is the first thing
this chapter will list as a problem at the end.

## Reading one: `404` is an answer

```php
public function show(Book $book)
{
    return $book;
}
```

Two lines, and the `404` is already handled: the binding from chapter
@cap:rotas-e-controllers looks up the record and stops before entering the
method when it does not find it.

:::key
`404` is not an application failure. It is the correct answer to a question
about something that does not exist.

The distinction matters for monitoring: a system that treats `404` as an
error fills the dashboard with alerts every time someone types a wrong
address, and the alert that matters gets lost in the middle.
:::

## `PUT` and `PATCH` are not the same thing

`apiResource` points both verbs to the same method. The difference between
them is yours to implement — and ignoring it produces a specific defect.

**`PUT` replaces the whole resource.** Whatever is not in the body ceases to
exist.

**`PATCH` changes what came.** Whatever did not come stays as it was.

```text
PATCH /api/books/4031
{"subject": "textbook"}
```

If the method treats that as `PUT`, the book loses its author, ISBN and year
— because they did not come.

```php title="app/Http/Controllers/BookController.php" numbered
public function update(Request $request, Book $book)
{
    $rules = [
        'title' => ['string', 'max:200'],
        'author' => ['string', 'max:150'],
        'subject' => ['string', 'max:40'],
        'isbn' => ['nullable', 'string', 'size:13'],
        'year' => ['nullable', 'integer', 'min:1400'],
    ];

    if ($request->isMethod('PUT')) {
        $rules['title'][] = 'required';
        $rules['author'][] = 'required';
        $rules['subject'][] = 'required';
    }

    $book->update($request->validate($rules));

    return $book;
}
```

With `PUT`, the required fields are required again — whoever sends the whole
resource must send it whole. With `PATCH`, `update` only touches what came.

:::pitfall
Most APIs implement only one of the two and accept both verbs, which
produces the worst possible result: the client reads in the documentation
that `PUT` replaces, sends a partial `PUT` expecting the rest to be erased —
and the rest stays.

If you are going to implement only one, **implement `PATCH` and refuse
`PUT`** with `405`. A clear refusal is better than a verb that lies.
:::

## Delete

```php
public function destroy(Book $book)
{
    $book->delete();

    return response()->noContent();
}
```

Four lines, and one question behind them: **really delete?**

A book with a loan history should not vanish, for the reason in chapter
@cap:relacionamentos. With `SoftDeletes`, the `delete()` above starts
filling `deleted_at`, and the `204` response stays the same for the caller.

The client does not need to know the difference. The API promises that the
resource leaves the listings, and it keeps that promise.

## One business operation, one `commit`

The loan is not one of the five. It writes in two places, and both must
happen together:

```php title="app/Http/Controllers/LoanController.php" numbered
public function store(Request $request)
{
    $data = $request->validate([
        'copy_id' => [
            'required', 'integer', 'exists:copies,id',
        ],
        'reader_id' => [
            'required', 'integer', 'exists:readers,id',
        ],
    ]);

    $loan = DB::transaction(function () use ($data) {
        $copy = Copy::lockForUpdate()
            ->findOrFail($data['copy_id']);

        if ($copy->status !== CopyStatus::Good) {
            abort(409, 'Copy unavailable');
        }

        $open = Loan::open()
            ->where('reader_id', $data['reader_id'])
            ->count();

        if ($open >= config('library.limit_per_reader')) {
            abort(409, 'Loan limit reached');
        }

        $loan = Loan::create([
            'copy_id' => $copy->id,
            'reader_id' => $data['reader_id'],
            'borrowed_at' => now(),
            'due_on' => now()->addDays(
                config('library.loan_days'),
            ),
        ]);

        $copy->update(['status' => CopyStatus::OnLoan]);

        return $loan;
    });

    return response()
        ->json($loan, 201)
        ->header('Location', route('loans.show', $loan));
}
```

`DB::transaction` opens the transaction, runs the function and commits at
the end. If any exception bubbles up — including the `abort` —, it rolls
everything back and the exception carries on.

`lockForUpdate()` is the `SELECT ... FOR UPDATE` from chapter @cap:pdo,
written in Eloquent. It locks the copy's row until the end of the
transaction, and it is what stops Vera and Neide from lending the same copy
in the same second.

:::key
The yardstick for a transaction is not "how many queries". It is: **how many
of these writes need to be true at the same time?**

Creating the loan without changing the copy produces a lent book the system
thinks is available. Changing the copy without creating the loan produces an
unavailable book nobody took. Either half alone is worse than none.
:::

## "It's just a CRUD"

The collection is live. The five routes work, the loan respects two rules
and the transaction closes. It is a good place to stop and be honest about
what this chapter left wrong — on purpose, because writing the wrong version
first is the only way the fix makes sense.

**Validation is in the controller.** Fifteen lines of rules in the middle of
a method that should have three. And they repeat in `store` and `update`,
with a difference someone will forget to keep in sync.

**The response is the raw model.** The returned JSON is a picture of the
table: `created_at`, `updated_at`, `book_id`. The day the column is renamed,
the published app breaks — and it should not even know columns exist.

**The business rule is in the controller.** Two of Vera's eleven rules are
in there, and they cannot be tested without sending a request. The other
nine are nowhere.

**The error is a sentence.** `abort(409, 'Copy unavailable')` returns text.
The consumer cannot decide anything without reading the sentence, and the
sentence changes.

**There is no authentication.** Anyone with the address can create a loan in
any reader's name.

Five items. None of them is a slip of the keyboard — each one is the subject
of a decision that has not been made yet.

:::note In your career
"It's just a CRUD" gets said often and is almost always wrong, but the
answer "it isn't" convinces nobody.

What convinces is Tainá's notebook: a list of real rules, spoken by the
people who do the work, and the question of where each one will live. Eleven
rules do not fit on five screens — and when you show that in a meeting, the
conversation about deadlines changes subject on its own.

The work of gathering that list usually falls to you, because nobody else
will do it. And it is the work that turns an estimate in days into an
estimate in rules, which is the only one that survives the second week.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Http/Controllers/
    BookController.php        # the five operations
    CopyController.php
    LoanController.php        # with the rule inside, for now
  app/Models/
    Book.php                  # SoftDeletes
    Copy.php
    Loan.php
  routes/api.php
:::

:::summary
- `apiResource` delivers five operations any consumer can guess without
  documentation.
- Creation returns `201`, the resource in the body and `Location` pointing to
  it.
- `404` is an answer, not a failure; treating it as an error pollutes
  monitoring.
- `PUT` replaces and `PATCH` changes; both reach the same method, and the
  difference is yours to implement.
- Implementing only one and accepting both verbs is worse than refusing one
  with `405`.
- Deleting an entity with history is logical, and the client does not need
  to know.
- `DB::transaction` commits at the end and rolls back on any exception;
  `lockForUpdate` locks the contested row.
- The yardstick for a transaction is how many writes need to be true at the
  same time.
- This chapter's CRUD has five named defects, and none of them is a typo.
:::

:::checkpoint
You deliver the five operations with the correct statuses, can explain the
difference between `PUT` and `PATCH` by what happens to absent fields, wrap
a business operation in a transaction with the row locked, and can list in
writing what is still wrong with what you just delivered.
:::

:::exercise level=1
For each request, say what the API should answer:

1. `POST /api/books` with the title missing.
2. `GET /api/books/99999`, which does not exist.
3. `DELETE /api/books/4031`, which exists and has loans in its history.
4. `PUT /api/books/4031` with only the `subject` field.
5. `POST /api/loans` for a copy that is already on loan.

:::answer
1. `422`, with the list of fields that failed. Not `400`: the JSON was
   correct.
2. `404`, and the binding returns it without entering the method.
3. `204`. The record leaves the listings through logical deletion, and the
   history remains. The caller sees no difference.
4. `422`. `PUT` replaces the whole resource, so the required fields are
   required — sending only `subject` is an incomplete request.
5. `409`. The request is correct and the system's state does not allow it.
   It is the difference, from chapter @cap:o-que-e-uma-api-rest, between
   invalid content and incompatible reality.

The pair people get wrong most is 4 and 5. Both refuse, and both say
different things: in 4, the client fixes what it sent; in 5, it reloads the
screen because someone else took the book first.
:::

:::exercise level=2
Write the `CopyController`'s `destroy` with the rule: a copy on loan cannot
be removed.

Then answer: why can this check **not** live only on the screen, and what
happens if it does?

:::answer
```php title="app/Http/Controllers/CopyController.php" numbered
public function destroy(Copy $copy)
{
    if ($copy->status === CopyStatus::OnLoan) {
        abort(409, 'A copy on loan cannot be removed');
    }

    $copy->delete();

    return response()->noContent();
}
```

The check cannot live only on the screen because **the screen is not the
only path to this operation**. The same route can be reached by `curl`, by
the app, by an import script and by any future integration.

If it lives only on the screen, the result is a removed copy with an open
loan: Dona Marlene has the book and the system does not know whom to charge.
And the worst part is that nobody will find out right away — they will find
out at the inventory check, months later, with a number that does not add
up.

It is the same idea as in chapter @cap:requests-e-responses about form
validation: the client checks to be kind, the server checks because it is
the only one that can.
:::

:::exercise level=3
This `update` passed review and has been in production for two weeks. A
client reported that "sometimes the book loses its author".

```php
public function update(Request $request, Book $book)
{
    $book->update($request->all());

    return $book;
}
```

Explain what happens, why it is intermittent, and write the three fixes in
order of urgency.

:::answer
**What happens.** Two defects combine.

`$request->all()` hands `update` everything that came. If the client sends
`{"author": null}` — which a form with an empty field does —, the author
becomes null. And if it sends fields that do not exist in the table,
`$fillable` silently discards them, so half of the request disappears
without warning.

**Why it is intermittent.** It depends on which screen of the app made the
call. The full edit screen sends every field and works; the quick screen for
changing the subject sends two fields, and the app's form library includes
the empty fields as `null`. Nobody reproduces the defect by testing through
the main screen.

**The three fixes, in order.**

**First, today:** swap `all()` for the validation's return value, which only
returns what was declared.

```php
$data = $request->validate([
    'title' => ['sometimes', 'required', 'string', 'max:200'],
    'author' => ['sometimes', 'required', 'string', 'max:150'],
    'subject' => ['sometimes', 'required', 'string', 'max:40'],
]);

$book->update($data);
```

`sometimes` is the piece that makes `PATCH` work: the rule is only applied
if the field **comes**. An absent `author` is ignored; a present and null
`author` is refused with `422`.

**Second, this week:** distinguish `PUT` from `PATCH`, so the verb means
something.

**Third, when possible:** a test that sends exactly the quick screen's body
— two fields and three nulls — and checks that the author is still there.
Without it, the first fix disappears with the next change to this method.

And an observation that is not a fix: the defect passed review because
`update($request->all())` is a short, familiar line. Wrong code that looks
clean gets through more reviews than right code that looks ugly.
:::
