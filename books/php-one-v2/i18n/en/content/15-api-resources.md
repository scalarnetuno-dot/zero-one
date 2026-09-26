---
source_hash: 4602a92843c3
title: "API Resources"
number: 15
slug: api-resources
part: p4
kicker: "The column was created for the team to note down what it wouldn't say in front of the reader. For eleven days, the reader read it."
goal: >-
  Separate the shape of the response from the structure of the table,
  decide field by field what goes out, load relationships without going back
  to N+1, and treat the response as a contract someone else is already
  using.
---

:::story Eleven days
The message arrived through the app's contact form, on a Monday.

> Good morning. I'd like to know who wrote on my record that I "return it
> wet, always check". I didn't return it wet. It was the December rain and
> I told you. Regards, Rosângela.

Tainá read it aloud. Dedé opened the app on her phone, went into the
profile, and there it was, right below the phone number, in a field the
screen showed with no label at all:

```text
returns it wet, always check
```

— That's the `internal_note` — he said. — Cléber created the column the week
before last, for Vera to note these things down.

— And why does it show up in the app?

— Because `show` returns the model. And the model has the column.

— Since when?

Dedé checked the migration's date.

— Eleven days.

Vera, who was at the door, asked how many people had a note.

— Thirty-eight.

— Then it's thirty-eight phone calls — she said. — Rosângela's I'll make
myself.
:::

## The model is not the JSON

Up to now, the controllers return the model directly:

```php
public function show(Reader $reader)
{
    return $reader;
}
```

Laravel knows how to turn a model into JSON, and it does so including **all
the table's columns**. It is convenient on day one and a trap from day two
on, because it ties together two things that change for different reasons:

**The table changes for internal reasons.** The team needs a column for
notes, a column to control imports, a new field for a report. Those changes
are decided by the team, whenever it wants.

**The response is an external contract.** The reader app was published in
the store with a format in mind, and its old version is still installed on
phones that have not updated in months. The response's format can only
change with notice, and sometimes cannot change at all.

When the JSON is a picture of the table, **every migration becomes a
contract change**, without anyone noticing. `internal_note` was a three-line
migration, reviewed and approved. Nobody thought about the API, because
nothing in the change said "API".

:::key
An API's response is an **allow-list**, written field by field. Whatever is
not on the list does not go out — including whatever is created later.

It is the same logic as the previous chapter's `rules()`, in the other
direction. The input has a list of what may come in; the output needs a
list of what may go out.
:::

There is `$hidden` on the model, which hides columns from serialization. It
solves the password case, and it is the first thing everyone learns. But it
is a **deny-list**: it hides what you remembered to hide. The column created
next week is not on it.

## `JsonResource`

```text
$ php artisan make:resource ReaderResource
```

```php title="app/Http/Resources/ReaderResource.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

class ReaderResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'phone' => $this->phone,
            'member_since' => $this->created_at->toDateString(),
        ];
    }
}
```

```php title="app/Http/Controllers/ReaderController.php" numbered
public function show(Reader $reader)
{
    return new ReaderResource($reader);
}
```

:::http title="The same reader, now with an allow-list"
GET /api/readers/47
---
200 OK
Content-Type: application/json

{
  "data": {
    "id": 47,
    "name": "Rosângela Pires",
    "phone": "21987654321",
    "member_since": "2014-03-11"
  }
}
:::

Four fields. `internal_note` is not there, `document` is not there, `role` is
not there, `updated_at` is not there. And the column someone creates next
month will not be there either.

Inside `toArray`, `$this->id` reads the property of the model the resource
wraps. The resource is a **wrapper**: it passes reads on to the model and
decides what to return.

Notice `member_since`. The table has `created_at`, which is a database name
— it says when the row was inserted. The contract has `member_since`, which
is a domain name — it says what that means for the reader. The day the old
records are imported from the Sistema with their original date, the column
will change and the contract's name will still make sense.

### The `data` envelope

The resource returns the object inside a `data` key. It looks like
ceremony, and it is a decision with a reason: it leaves room at the top
level for things that are not the resource — pagination, links, deprecation
notices.

```json
{
  "data": [ ... ],
  "links": { "next": "..." },
  "meta": { "total": 4031 }
}
```

An API that starts without an envelope and needs to add metadata later has
two bad choices: break every client by changing the root format; or cram
the metadata into HTTP headers, where nobody looks. With the envelope from
day one, the decision never has to be made.

## Collections

For a list, the same resource, applied to each item:

```php title="app/Http/Controllers/BookController.php" numbered
public function index()
{
    $books = Book::orderBy('title')->paginate(20);

    return BookResource::collection($books);
}
```

When what reaches `collection` is a paginator, the resource builds the full
envelope on its own — `data`, `links` and `meta` —, with the numbers the
paginator calculated. Chapter @cap:paginacao-filtros-e-buscas covers the
paginator itself.

There is also the `ResourceCollection` class, for when the collection needs
its own fields at the top level. In most cases, `::collection` is enough,
and it is one file fewer.

## `whenLoaded`: the relationship that only appears if it was loaded

The `BookResource` needs to show the authors and the count of available
copies. The first version is usually this:

```php
'authors' => $this->authors->pluck('name'),
```

And it is the serialization N+1 chapter @cap:relacionamentos warned about:
`$this->authors` fires a query **for each book**, at the moment the response
is assembled, after the controller has finished.

The right version asks before touching:

```php title="app/Http/Resources/BookResource.php" numbered
class BookResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'isbn' => $this->isbn,
            'year' => $this->year,
            'subject' => $this->subject,
            'authors' => AuthorResource::collection(
                $this->whenLoaded('authors'),
            ),
            'available_copies' => $this->whenCounted(
                'availableCopies',
            ),
        ];
    }
}
```

`whenLoaded('authors')` checks whether the relationship **has already been
loaded** — by `with` or `load`. If it has, it delivers it. If not, the whole
key **disappears from the response**, with no query. `whenCounted` does the
same for `withCount`.

The consequence is that **the controller decides what comes**, through the
query it made:

```php
// in the listing: authors and count
Book::with('authors')
    ->withCount(['copies as available_copies_count'
        => fn ($q) => $q->where('status', CopyStatus::Good)])
    ->paginate(20);

// in the counter's quick search: just the book
Book::where('isbn', $isbn)->first();
```

The resource is the same in both. The response changes size according to
what the controller loaded, and never through a hidden query.

:::pitfall
`whenLoaded` solves N+1, and creates a subtle kind of inconsistency: the
same resource, on two endpoints, comes with different fields. A client that
was programmed against the listing expects `authors`; in the quick search,
the key does not exist.

That is acceptable if it is **documented** — "the ISBN search does not
bring authors" — and a defect if it is accidental. When in doubt, decide per
endpoint what comes, write it in the documentation from chapter
@cap:documentacao-da-api, and test it. Chapter
@cap:testes-de-feature-http-e-banco has a test for exactly that.
:::

With the `preventLazyLoading` from chapter @cap:relacionamentos on,
touching `$this->authors` without `whenLoaded` on an unloaded relationship
throws an exception in development. The two mechanisms complement each
other: one protects the response, the other warns when someone forgets.

## The field that must never go out

Not every field is public to everyone. The reader can see their own phone
number and cannot see another reader's. The librarian sees both, and also
sees the document.

`when` includes a field under a condition:

```php title="app/Http/Resources/ReaderResource.php" numbered
public function toArray(Request $request): array
{
    $own = $request->user()?->reader_id === $this->id;
    $staff = $request->user()?->isStaff() ?? false;

    return [
        'id' => $this->id,
        'name' => $this->name,
        'phone' => $this->when(
            $own || $staff,
            $this->phone,
        ),
        'document' => $this->when($staff, $this->document),
        'member_since' => $this->created_at->toDateString(),
    ];
}
```

`$request->user()` still returns `null` — the API has no login until chapter
@cap:autenticacao. The `?->` ensures that, for now, nobody is "own" or
"staff", and both fields simply do not go out. When login arrives, the
resource is already ready for it.

:::key
There are three categories of field, and each calls for a treatment:

**Public:** always goes out. Title, year, name.

**Conditional:** goes out to whoever is entitled to it. Phone, document. It
goes in `when`.

**Internal:** never goes out, to anyone, through this API. `internal_note`,
`password`, `imported_from_sistema`. It does not appear in the resource —
and the test in chapter @cap:testes-de-feature-http-e-banco guarantees it
keeps not appearing.
:::

`internal_note` does not even belong to the second group. The team sees the
note in the **Blade panel**, which is another door, with another screen and
another permission. The app's API never needs it, and so it does not exist
for the API.

## One format, the whole API

The envelope, the names, the dates: all of that becomes the API's
convention, and it is worth writing down once.

| Decision | Casa Amarela's choice |
|---|---|
| field names | `snake_case`, in English |
| dates | `YYYY-MM-DD` for a day; ISO 8601 with time zone for an instant |
| money | object `{cents, formatted}` |
| enum | the `value`, never the `name` |
| absence | key present with `null`, except in `whenLoaded` |

Table: Five decisions the team makes once and the client learns once. The
worst choice in each row is not choosing, and letting each resource decide.

Money deserves a line of code, because the `Money` object from chapter
@cap:enums-datas-e-valores does not know how to become JSON on its own:

```php title="app/Http/Resources/LoanResource.php" numbered
public function toArray(Request $request): array
{
    return [
        'id' => $this->id,
        'status' => $this->status->value,
        'borrowed_at' => $this->borrowed_at->toIso8601String(),
        'due_on' => $this->due_on->toDateString(),
        'returned_at' => $this->returned_at?->toIso8601String(),
        'overdue' => $this->isOverdue(),
        'fine' => $this->when(
            $this->fine_in_cents !== null,
            fn () => [
                'cents' => $this->fine_in_cents->cents,
                'formatted' => $this->fine_in_cents->formatted(),
            ],
        ),
        'copy' => new CopyResource(
            $this->whenLoaded('copy'),
        ),
    ];
}
```

`overdue` is the case from the exercise in chapter
@cap:enums-datas-e-valores: it is not a column, it is a conclusion
calculated by the model. For the client, there is no difference — it
receives a boolean and does not need to know whether it was read or
calculated. It is the advantage of having the contract separate from the
table, seen from the good side.

Money goes out in both forms. The app uses `cents` to add and `formatted` to
display, and never needs to format currency in JavaScript — which is where
the comma and the dot tend to swap places.

## Changing the response without breaking whoever already uses it

Version 1.0 of the app is installed. The team decided that `subject`, which
today is text, will become an object with `id` and `name`. What to do?

**Adding is safe.** A new field breaks no well-written client, because a
well-written client ignores what it does not know.

**Changing the type or the name breaks.** App 1.0 expects text in `subject`
and will receive an object.

The way out is **add alongside, then remove**:

```php
'subject' => $this->subject->name,       // kept, marked for removal
'subject_detail' => new SubjectResource($this->subject),
```

The old field stays; the new one appears alongside. The documentation marks
the old one as deprecated, with a date. When app 1.0 no longer has users —
and that is measured, not guessed —, the old field goes.

Versioning the whole API (`/api/v2/books`) because of one field is
disproportionate: it duplicates routes, controllers and tests to solve a
problem one extra key solves. Chapter @cap:documentacao-da-api comes back to
this, with the full plan.

:::note In your career
The most common data leak in an API is not an attack: it is a
`return $model` and a migration made months later by someone else.

It does not show up in review, because the migration does not touch the API
and the controller did not change. It does not show up in manual testing,
because nobody looks at the whole JSON. It shows up when a Rosângela reads
what was written about her.

If you join a project that returns raw models, the first resource you write
will look like bureaucracy to the people there. Write it anyway, and write
the test that checks the internal column does not go out. It is the kind of
contribution nobody thanks you for until the day it prevented a phone call.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Http/Resources/
    BookResource.php         # whenLoaded, whenCounted
    AuthorResource.php
    CopyResource.php
    ReaderResource.php       # conditional phone and document
    LoanResource.php         # money as an object, overdue
  app/Http/Controllers/      # none returns a raw model
:::

:::summary
- The model is the internal schema; the JSON is an external contract. The
  two change for different reasons and need different code.
- A response is a field-by-field allow-list; `$hidden` is a deny-list and
  does not protect what is created later.
- `JsonResource::toArray` declares what goes out; the `data` envelope leaves
  room for `links` and `meta`.
- `::collection` with a paginator builds the full envelope on its own.
- `whenLoaded` and `whenCounted` include the relationship only if it has
  already been loaded; the controller's query decides.
- Fields are public, conditional (`when`) or internal — and internal ones do
  not appear in the resource.
- Format conventions — dates, money, enum, absence — are decided once for
  the whole API.
- Adding a field is safe; renaming or changing the type breaks. The way out
  is to add alongside and remove later.
:::

:::checkpoint
No API controller returns a raw model. You write resources with public,
conditional and deliberately absent fields, load relationships without N+1
in serialization, and know how to plan a field change without breaking the
app that is already installed.
:::

:::exercise level=1
For each column of the `copies` table, say whether it goes into
`CopyResource` as public, conditional (for whom?) or not at all:

`id`, `book_id`, `accession`, `status`, `acquired_on`, `purchase_price`,
`supplier`, `created_at`, `updated_at`.

:::answer
- `id`: public. It is the identifier the client uses for the other routes.
- `book_id`: not as a loose number. The book comes as a nested object with
  `whenLoaded('book')`, or through a link. A foreign-key number is a schema
  detail.
- `accession`: public. It is the number stuck on the book, and Vera talks
  about it.
- `status`: public, through the enum's `value`. It is what the reader wants
  to know.
- `acquired_on`: conditional, for staff. The reader does not care.
- `purchase_price`: not included. It is management information, and the
  panel shows it.
- `supplier`: not included, for the same reason.
- `created_at`, `updated_at`: not included. They are database control
  dates; if one day it makes sense to expose "registered on", it goes in
  with a domain name.

`book_id` is the one that divides opinions most. Exposing the number is not
wrong, and many APIs do it. The point is to decide and be consistent: if
`copy` brings `book_id`, `loan` should bring `copy_id` by the same
criterion.
:::

:::exercise level=2
This listing of overdue loans got slow after the resource gained two fields.
Find the problem and fix it without changing the response's format.

```php
public function overdue()
{
    return LoanResource::collection(
        Loan::overdue()->get()
    );
}
```

```php
// inside LoanResource
'reader' => $this->reader->name,
'book' => $this->copy->book->title,
```

:::answer
Both fields touch relationships without `whenLoaded`, and the controller
loaded nothing. For 60 overdue loans: one query for the list, 60 for
readers, 60 for copies and 60 for books — 181.

The fix has two halves, and both are necessary.

In the controller, load:

```php
Loan::overdue()
    ->with(['reader', 'copy.book'])
    ->get()
```

In the resource, protect:

```php
'reader' => $this->whenLoaded(
    'reader',
    fn () => $this->reader->name,
),
'book' => $this->whenLoaded(
    'copy',
    fn () => $this->copy->book->title,
),
```

The controller alone solves it today; the resource alone prevents the
problem from coming back on the next endpoint that uses the same resource
without loading. The second form of `whenLoaded`, with a function, is for
when the value is derived from the relationship rather than the whole
relationship.

The format did not change: `reader` is still text and so is `book`.
:::

:::exercise level=3
The reader app, version 1.0, reads `due_on` as text in the `DD/MM/YYYY`
format — a mistake from the API's first version, which formatted the date
for display. The team wants to switch to the convention's `YYYY-MM-DD`
format.

There are 1,300 installs of version 1.0. Version 1.1, which can already read
both formats, has been in the store for three weeks.

Write the plan: what changes in the resource today, how to decide when to
end the transition, and what you would not do.

:::answer
**Today: add alongside.**

```php
'due_on' => $this->due_on->format('d/m/Y'),
'due_on_iso' => $this->due_on->toDateString(),
```

The old field stays identical; the new one follows the convention. Version
1.1 is updated to read `due_on_iso` when it exists.

**Deciding when to finish: measure.** The app sends its own version in a
header — if it does not, that is the first adjustment, in 1.2. With the
structured log from chapter @cap:cache-logs-e-medicao, you count how many
requests per day still come from 1.0. The transition ends when the number is
zero, or small enough that the library agrees to notify people in person.

**What happens next, in two steps.** First, `due_on` takes the new format
and `due_on_iso` keeps existing, marked as deprecated. Then, in a future
version, `due_on_iso` goes. It is ceremony, and it is what makes the right
name end up on the right field.

**What not to do.**

Change `due_on`'s format today: 1,300 apps start showing the wrong date or
breaking.

Create `/api/v2`: it duplicates the whole API because of one field.

Decide by the version header **inside the resource**, returning different
formats to each client: it works, and it creates a resource with an `if`
per version that nobody will have the courage to delete. One extra field is
simpler, more visible and easier to remove.
:::
