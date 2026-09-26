---
source_hash: 6e7af7f9cebd
title: "Pagination, filters and search"
number: 16
slug: paginacao-filtros-e-buscas
part: p4
kicker: "Searching for \"acafrao\" didn't find \"Açafrão\". Half the collection had been registered on keyboards from a public tender, with no cedilla."
goal: >-
  Deliver a listing that can handle the whole collection: paginated with a
  server-side ceiling, stably ordered, filterable without a staircase of
  ifs, and with a search that finds the book the person typed however they
  managed to.
---

:::story Just a tiny change
— It's just a tiny change — said Seu Juvenal, and Tainá, without looking up,
turned a page of her notebook.

— The search. It has to find by everything. Title, author, subject. And
people type without accents, so it has to find without accents too.

— Without accents how?

— A young woman searched for "acafrao" yesterday and didn't find it. I know
it's there, I donated it.

Dedé typed on the staging screen: `acafrao`. Zero results. He typed
`açafrão`. One result: *O Açafrão e Outras Especiarias*.

— Found it — said Seu Juvenal.

— With the accent.

Vera, from the counter, without turning around:

— Search for "acafrao" again, but in the Sistema.

Dedé opened the 2009 Sistema. Typed it. Four results — Seu Juvenal's book
and three others, all with "acafrao" in the title, without the cedilla and
without the tilde.

— The 2012 computers came from a public tender — said Vera. — American
keyboards. For two years nobody could type a cedilla. I registered about
fifteen hundred books like that.

— So the search needs to find both spellings in both directions — said
Tainá. — Whoever types without accents finds the ones with, and whoever
types with accents finds the ones without.

Seu Juvenal smiled.

— See? Tiny change.
:::

## A listing without a limit is a denial of service you published

The `index` from chapter @cap:o-crud-completo started like this:

```php
return Book::all();
```

With forty books, it works. With the collection's four thousand, the
response is a few megabytes, takes seconds to go out, and each request loads
four thousand objects into the server's memory. With eight thousand copies
and half a million loans in the history, the loans route takes the process
down.

And no ill intent is needed. It is enough for the app to load the list on
open, and a hundred people to open the app at nine in the morning.

:::key
Every route that returns a collection has a **ceiling**, and the server
decides the ceiling. A listing without a ceiling is a denial of service you
published yourself, waiting for someone to call it.
:::

## Three paginators

Laravel has three ways to slice a query, and each answers a different
question.

**`paginate`** brings the page and **counts the total**:

```php
Book::orderBy('title')->paginate(20);
```

```sql
SELECT COUNT(*) AS aggregate FROM books;
SELECT * FROM books ORDER BY title LIMIT 20 OFFSET 40;
```

Two queries. The response's `meta` has `total` and `last_page`, and the app
can show "page 3 of 202".

**`simplePaginate`** brings the page and **does not count**:

```sql
SELECT * FROM books ORDER BY title LIMIT 21 OFFSET 40;
```

One query. It asks for 21 to know whether there is a next page, and returns
20. The client knows whether there is a "next", but not how many pages
there are.

**`cursorPaginate`** does not use `OFFSET`:

```sql
SELECT * FROM books
WHERE (title, id) > ('Memórias Póstumas', 1832)
ORDER BY title, id LIMIT 21;
```

It keeps, in an opaque token, the last record of the current page, and asks
for "the next ones after this". The `OFFSET` disappears.

| | `paginate` | `simplePaginate` | `cursorPaginate` |
|---|---|---|---|
| total and last page | yes | no | no |
| jump to page 50 | yes | yes | no |
| cost on page 1 | medium | low | low |
| cost on page 2,000 | high | high | low |
| stable with inserts | no | no | yes |

Table: The middle column is rarely the right one: it has the cost of
`OFFSET` without the advantage of the total.

The high cost of `OFFSET` on a distant page is what the `EXPLAIN` from
chapter @cap:duas-tabelas-conversando would show: to return rows 40,000 to
40,020, the database **reads and discards** the first 40,000. Page 1 is fast,
and each following page is a little slower than the previous one.

For the collection, which a person leafs through and where "page 3 of 202"
helps, `paginate`. For a reader's loan history, which the app scrolls down
endlessly, `cursorPaginate`.

## Stable ordering: the tie-breaker nobody remembers

```php
Book::orderBy('year')->paginate(20);
```

Forty books were published in 1938. Page 1 shows twenty of them; page 2
shows... **twenty of them**, possibly the same ones.

When the `ORDER BY` column has repeated values, the database promises no
order among the ties. It may return the forty in one order on the first
query and in another on the second — and with `LIMIT` and `OFFSET`, that
means a book repeated on one page and a book missing on the other.

The fix is always the same: **end the `ORDER BY` with a unique column**.

```php
Book::orderBy('year')->orderBy('id')->paginate(20);
```

:::pitfall
This defect does not show up in development. With the factory's forty books,
MySQL tends to return the ties in insertion order, every time. With the real
collection, after a few months of changes and an `OPTIMIZE TABLE`, the order
of the ties changes.

It is the red-pipeline defect in chapter @cap:testes-de-feature-http-e-banco,
which passed on every local machine.
:::

## Optional filters without a staircase of `if`s

The listing accepts filters, all optional:

```text
GET /api/books?subject=literature&available=1&min_year=1900
```

The first version is usually this:

```php
$query = Book::query();

if ($request->subject) {
    $query->where('subject', $request->subject);
}

if ($request->min_year) {
    $query->where('year', '>=', $request->min_year);
}

if ($request->available) {
    $query->whereHas('copies', fn ($q) =>
        $q->where('status', CopyStatus::Good));
}
```

It has a defect chapter @cap:conversao-automatica already showed:
`if ($request->min_year)` is false when `min_year` is `0`. For a year,
nobody notices. For `?min_fine=0` or `?available=0`, the filter disappears
when the client explicitly asked for zero.

The query builder has a method for "apply this only if":

```php
$query = Book::query()
    ->when(
        $request->filled('subject'),
        fn ($q) => $q->where('subject', $request->subject),
    )
    ->when(
        $request->filled('min_year'),
        fn ($q) => $q->where(
            'year', '>=', $request->integer('min_year'),
        ),
    )
    ->when(
        $request->has('available'),
        fn ($q) => $request->boolean('available')
            ? $q->whereHas('availableCopies')
            : $q->whereDoesntHave('availableCopies'),
    );
```

`filled` checks whether the field came **and is not empty** — and `0` counts
as filled. `has` only checks whether it came, which lets you tell
`?available=0` ("only the unavailable ones") from no filter ("all").

### The filter gets a class

With five filters, the controller gets big again. And filters are **input**,
so they also need validation. Both things are solved together — a Form
Request that validates and hands over a typed object:

```php title="app/Http/Requests/ListBooksRequest.php" numbered
class ListBooksRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'search' => ['nullable', 'string', 'max:100'],
            'subject' => ['nullable', 'string', 'max:40'],
            'available' => ['nullable', 'boolean'],
            'min_year' => ['nullable', 'integer', 'min:1400'],
            'sort' => ['nullable', Rule::in(BookFilter::ORDERS)],
            'per_page' => ['nullable', 'integer', 'between:1,100'],
        ];
    }

    public function filter(): BookFilter
    {
        return new BookFilter(
            search: $this->validated('search'),
            subject: $this->validated('subject'),
            available: $this->has('available')
                ? $this->boolean('available')
                : null,
            minYear: $this->validated('min_year'),
            order: $this->validated('sort') ?? 'title',
            perPage: $this->validated('per_page') ?? 20,
        );
    }
}
```

```php title="app/Catalog/BookFilter.php" numbered
final readonly class BookFilter
{
    public const ORDERS = [
        'title', '-title', 'year', '-year', 'recent',
    ];

    public function __construct(
        public ?string $search,
        public ?string $subject,
        public ?bool $available,
        public ?int $minYear,
        public string $order,
        public int $perPage,
    ) {}
}
```

`?bool $available` has three states, and the three mean different things:
`true`, `false` and "don't filter". It is the distinction between `null` and
`false` from chapter @cap:variaveis-e-tipos, with a business consequence.

And the model gets a scope that receives the whole filter:

```php title="app/Models/Book.php" numbered
public function scopeFilter(
    Builder $q,
    BookFilter $f,
): void {
    $q->when($f->subject, fn ($q, $s) =>
            $q->where('subject', $s))
      ->when($f->minYear !== null, fn ($q) =>
            $q->where('year', '>=', $f->minYear))
      ->when($f->available !== null, fn ($q) =>
            $f->available
                ? $q->whereHas('availableCopies')
                : $q->whereDoesntHave('availableCopies'))
      ->when($f->search, fn ($q, $s) => $q->search($s))
      ->sortBy($f->order);
}
```

The controller is the size it should be:

```php title="app/Http/Controllers/BookController.php" numbered
public function index(ListBooksRequest $request)
{
    $filter = $request->filter();

    $books = Book::filter($filter)
        ->with('authors')
        ->paginate($filter->perPage)
        ->withQueryString();

    return BookResource::collection($books);
}
```

`withQueryString()` makes the next and previous page links carry the
filters. Without it, the page 2 link loses `subject=literature`, and the
person who filtered is back to seeing the whole collection.

## Text search: `LIKE`, accents and the unused index

Casa Amarela's search looks for a term in the title or in the author's name.
The direct form:

```php
public function scopeSearch(Builder $q, string $term): void
{
    $q->where(fn ($q) => $q
        ->where('title', 'like', "%{$term}%")
        ->orWhereHas('authors', fn ($q) =>
            $q->where('name', 'like', "%{$term}%")));
}
```

Two things in that snippet, one good and one bad.

The good: the inner `where` with a function groups the two conditions in
parentheses. Without it, the `orWhere` would escape the other filters:

```sql
-- without the grouping
WHERE subject = 'literature' AND title LIKE '%x%'
   OR EXISTS (author LIKE '%x%')

-- with the grouping
WHERE subject = 'literature'
  AND (title LIKE '%x%' OR EXISTS (author LIKE '%x%'))
```

The first returns books of **any** subject whose author matches the term.
It is the `OR` outside parentheses, the precedence defect from chapter
@cap:operadores, now in SQL.

The bad: `LIKE '%term%'` **does not use an index**. An index on `title` works
like a dictionary's alphabetical order, and lets you find what **starts**
with a word. Finding what **contains** a word in the middle forces the
database to read every row.

| Pattern | Uses an index? |
|---|---|
| `title = 'Dom Casmurro'` | yes |
| `title LIKE 'Dom%'` | yes |
| `title LIKE '%Casmurro%'` | no |

Table: The `%` at the start is what kills the index.

With four thousand books, reading every row takes milliseconds and does not
matter. With four million, it does. The answer for volume is MySQL's
`FULLTEXT` index, which breaks the text into words and indexes each one:

```php
$t->fullText(['title']);
```

```php
$q->whereFullText('title', $term);
```

For Casa Amarela's collection, `LIKE` is enough, and it is worth knowing at
what number it stops being enough. Measuring is the subject of chapter
@cap:cache-logs-e-medicao.

### The accent

MySQL has a ready answer to Seu Juvenal's problem, and it lives in the
column's **collation** — the rule the database uses to compare text:

```sql
SELECT 'acafrao' = 'Açafrão' COLLATE utf8mb4_0900_ai_ci;
-- 1
```

`ai` is *accent insensitive*; `ci`, *case insensitive*. With that
collation, `a` and `á` and `A` are equal for comparison — and `LIKE` also
starts ignoring accents and case.

Laravel creates tables with `utf8mb4_unicode_ci` by default, which ignores
case and is **partially** accent insensitive, with differences between MySQL
versions that have already cost many lost afternoons. The explicit decision
is to declare the collation on the column that will be searched:

```php title="..._adjust_title_collation.php" numbered
Schema::table('books', function (Blueprint $t) {
    $t->string('title', 200)
        ->collation('utf8mb4_0900_ai_ci')
        ->change();
});
```

:::pitfall
The collation solves the comparison and **does not fix what was stored**.
The fifteen hundred titles from the tender still have no cedilla in the
database, and the screen still shows "O Acafrao e Outras Especiarias" to
whoever finds it.

Fixing the stored text is another job, manual, which Vera does bit by bit,
when the book passes through the counter. The search no longer depending on
it is what lets her do it bit by bit.

And a second caution: the test that runs on SQLite does not have that
collation. The accent-free search passes on MySQL and fails on SQLite, or
the other way round. Chapter @cap:testes-de-feature-http-e-banco covers
where SQLite lies.
:::

## Ordering by a client field without opening the database to it

The client wants to choose the order: `?sort=-year`. The temptation is to
pass it straight through:

```php
$q->orderBy($request->sort);
```

Laravel escapes the column name, so this is not SQL injection in the
classic sense. But the client can order by **any column** — including
`internal_note`, or `document`, and deduce from the result what it should
not see. It can order by an unindexed column on a large table and make each
request cost a second.

The answer is an allow-list that translates the contract's name into the
query:

```php title="app/Models/Book.php" numbered
public function scopeSortBy(Builder $q, string $order): void
{
    match ($order) {
        'title' => $q->orderBy('title'),
        '-title' => $q->orderByDesc('title'),
        'year' => $q->orderBy('year'),
        '-year' => $q->orderByDesc('year'),
        'recent' => $q->orderByDesc('created_at'),
    };

    $q->orderBy('id');
}
```

The `match` from chapter @cap:condicionais ensures that a value outside the
list does not slip through silently: it throws `UnhandledMatchError`. It
never gets that far, because the Form Request's `Rule::in` has already
refused with `422` — but if someone one day forgets the validation, the
query breaks instead of ordering wrongly.

And the `orderBy('id')` at the end is the previous section's tie-breaker,
applied to every order at once.

:::key
The name the client uses to sort is **contract**, not column. The contract's
`recent` is `created_at` today and may be `acquired_on` tomorrow, without
any client noticing.
:::

## The ceiling belongs to the server

The last parameter is `per_page`. The client can ask for 10, 20, 50. And it
will ask for 999,999, by accident or not.

```text
GET /api/books?per_page=999999
```

Two possible answers, and both are reasonable:

**Refuse with `422`.** The Form Request's `between:1,100` does that. The
client knows exactly what the limit is and adjusts.

**Cap silently.** `min($perPage, 100)`. The client asked for a million and
got a hundred, and the response's `meta.per_page` says so.

Casa Amarela refuses, because an app that asks for 999,999 has a defect
someone needs to see. What is not acceptable is the third option — obeying.

:::note In your career
Pagination, filtering and ordering are the parts of the API the client uses
most and that come up least in planning conversations. Nobody writes "the
listing needs a tie-breaker" in a user story.

That is why they are usually a new API's first problem in production: they
do not break on day one, they break when the volume arrives. If you are
reviewing a listing, the four questions fit in a minute: does it have a
ceiling? Does the order end on a unique column? Do the filters handle zero?
Does `sort` have an allow-list?
:::

:::tree title="Where we are now"
casa-amarela/
  app/Catalog/
    BookFilter.php              # typed object, three states
  app/Http/Requests/
    ListBooksRequest.php        # validates filters and ceiling
  app/Models/
    Book.php                    # scopes filter, search, sortBy
  database/migrations/
    ..._adjust_title_collation.php
:::

:::summary
- Every collection has a ceiling, and the ceiling belongs to the server.
- `paginate` counts the total; `simplePaginate` does not count;
  `cursorPaginate` does away with `OFFSET` and stays fast at any depth.
- `ORDER BY` on a column with repeats needs a tie-breaker on a unique
  column, or pages lose and repeat records.
- `when` applies an optional filter without a staircase of `if`s; `filled`
  treats zero as a value.
- Filters are input: they are validated in a Form Request and travel in a
  typed object.
- An `orWhere` outside a group escapes the other filters.
- `LIKE '%x%'` does not use an index; `FULLTEXT` handles volume.
- An `ai_ci` collation ignores accents and case in comparison, and does not
  fix what was stored.
- The client's `sort` goes through an allow-list that translates contract
  into column.
:::

:::checkpoint
You deliver `GET /books` with accent-free search, optional filters that
handle zero, ordering through an allow-list with a tie-breaker, and a
ceiling of a hundred per page — and you know how to choose among the three
paginators for a new listing.
:::

:::exercise level=1
Which paginator would you use in each case, and why?

1. The loan history in the app, with infinite scrolling.
2. The collection listing in Vera's panel, with "page 3 of 202".
3. A nightly export that goes through the half-million loans.

:::answer
1. `cursorPaginate`. Infinite scrolling needs neither a total nor jumping
   between pages, and the cursor neither repeats nor loses a record when a
   new loan enters at the top while the person scrolls.
2. `paginate`. The total is what the screen shows, and jumping to a page is
   useful. The cost of `COUNT` over four thousand books is irrelevant.
3. None of the three. An export is not API pagination: it is Eloquent's
   `chunkById` or `lazyById`, which walk the table in blocks using `id` as a
   cursor, with no `OFFSET` and without loading everything into memory.

Item 3 is the catch. The instinct to use `paginate` in a page-by-page loop
works, and gets slower with every page, for the same reason as `OFFSET` on
page 2,000.
:::

:::exercise level=2
This reader search is in production. Find the four defects related to the
chapter.

```php
public function index(Request $request)
{
    $q = Reader::query();

    if ($request->name) {
        $q->where('name', 'like', "%{$request->name}%")
          ->orWhere('document', $request->name);
    }

    if ($request->blocked) {
        $q->whereNotNull('blocked_at');
    }

    return $q->orderBy($request->get('sort', 'name'))
        ->paginate($request->get('per_page', 20));
}
```

:::answer
**One: the `orWhere` without grouping.** If other filters are added, the
document search escapes them. Today, the blocked filter already comes after
it and is applied with `AND` to only one half of the `OR`.

**Two: `if ($request->blocked)`.** `?blocked=0` is false, and the filter
disappears — instead of showing the unblocked ones, it shows everyone.

**Three: `orderBy` with a client value.** Any column, including `document` —
and no tie-breaker, so readers with the same name swap pages.

**Four: `per_page` without a ceiling.** `?per_page=999999` returns the whole
readers table, with personal data, in one request.

And a fifth, outside the chapter but serious: the route returns the
paginator of raw models, with no resource. Every reader's document is in the
response.

The corrected version follows the `ListBooksRequest` mold: a Form Request
with `between:1,100` and `Rule::in` for `sort`, `when` with
`has`/`boolean`, the `OR` inside a `where(fn ...)`, and
`ReaderResource::collection`.
:::

:::exercise level=3
Vera wants a new ordering: "most borrowed first". At
`/api/books?sort=popular`.

Write the case in `sortBy`, say what needs to exist in the database for it
to work well with the whole collection, and answer: should that number be
calculated on every request?

:::answer
The first version, correct and naive:

```php
'popular' => $q
    ->withCount('loans')
    ->orderByDesc('loans_count'),
```

That requires a `loans` relationship on `Book` — a `hasManyThrough` via
copies, which is the case where chapter @cap:relacionamentos said it pays
off.

**The cost.** `withCount` becomes a subquery that counts loans for **every
book in the collection** before ordering, because the database cannot know
which twenty are the most popular without counting them all. With half a
million loans, every request counts half a million records. The index on
`loans.copy_id` helps the subquery, and does not avoid the full count.

**Should it be calculated on every request? No.** Popularity changes a few
dozen times a day, and the listing is queried thousands of times. There are
two ways out:

A `total_loans` column on `books`, incremented on every loan by the event
from chapter @cap:events-jobs-e-filas, with an index. The ordering becomes
`orderByDesc('total_loans')`, instant.

Or the cache from chapter @cap:cache-logs-e-medicao, if "popular" is always
the same list and pagination does not matter.

The first is better for ordering, because it combines with filters. And it
has a cost: the column is a copy of something already in the loans, and
copies can drift. A nightly command that recalculates and compares is the
insurance.
:::
