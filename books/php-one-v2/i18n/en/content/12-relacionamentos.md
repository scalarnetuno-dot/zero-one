---
source_hash: 8013b49beb4b
title: "Relationships"
number: 12
slug: relacionamentos
part: p3
kicker: "The catalog listing took four seconds. The log showed 143 queries to display 47 books."
goal: >-
  Model the domain's links with the right kind of relationship, recognize
  N+1 by counting queries, and fix it while proving the fix with the same
  counter.
---

:::story One hundred and forty-three
The catalog screen was slow. It did not freeze — it was slow, about four
seconds, enough for Vera to click again thinking it had not registered.

Dedé had turned on query logging the week before, for another reason. He
opened the log after loading the screen once and scrolled to the top.

```text
$ grep -c "select" storage/logs/laravel.log
143
```

— One hundred and forty-three queries.

— For how many books?

— Forty-seven. It's the first page.

Tainá did the math out loud.

— Forty-seven times three, plus two.

— Plus two.

— And what are the three?

— Authors, copies and open loans. One per book, one at a time.
:::

## The foreign key lives on the "many" side

Before any code, the question that decides everything: **who points to
whom?**

A book has several copies; a copy belongs to one book. The `book_id` column
is in `copies`, because that is where the many are. The opposite would
require a column with a list inside, which is what the relational model does
not do.

| From the table's side | In the model | Who has the column |
|---|---|---|
| a book has many copies | `hasMany` | `copies` |
| a copy belongs to a book | `belongsTo` | `copies` |

Table: The two methods describe the **same** foreign key, from opposite
points of view. Whoever has the column uses `belongsTo`.

```php title="app/Models/Book.php" numbered
public function copies(): HasMany
{
    return $this->hasMany(Copy::class);
}
```

```php title="app/Models/Copy.php" numbered
public function book(): BelongsTo
{
    return $this->belongsTo(Book::class);
}
```

Laravel guesses the column name from the method and class names: `book()`
with `Book::class` looks for `book_id`. When the name strays from the
pattern, the second argument says which one it is.

```php
$book->copies;
```

```sql
SELECT * FROM copies WHERE book_id = ?
```

```php
$copy->book;
```

```sql
SELECT * FROM books WHERE id = ? LIMIT 1
```

:::key
Notice that reading `$book->copies` **fires a query**. It is not a field: it
is a call that looks like a property.

That is the origin of this chapter's problem, and the reason the defect is
hard to see: it does not look like a query. It looks like an arrow.
:::

## Many to many

A book may have two authors; an author has written several books. Neither
table can hold the column, so the relationship gets a table of its own:

```php title="..._create_author_book_table.php" numbered
Schema::create('author_book', function (Blueprint $t) {
    $t->foreignId('author_id')->constrained();
    $t->foreignId('book_id')->constrained();
    $t->string('role', 20)->default('author');
    $t->primary(['author_id', 'book_id']);
});
```

The name `author_book` is not a choice: it is the convention — both names in
the singular, in alphabetical order, separated by an underscore. Straying
from it costs an extra argument on each side.

```php title="app/Models/Book.php" numbered
public function authors(): BelongsToMany
{
    return $this->belongsToMany(Author::class)
        ->withPivot('role')
        ->withTimestamps();
}
```

```php
$book->authors;
```

```sql
SELECT authors.*, author_book.book_id AS pivot_book_id,
       author_book.author_id AS pivot_author_id,
       author_book.role AS pivot_role
FROM authors
INNER JOIN author_book ON authors.id = author_book.author_id
WHERE author_book.book_id = ?
```

:::pitfall
Without `withPivot('role')`, the column exists in the table, is written
correctly and **does not come back** in the query.
`$book->authors->first()->pivot->role` returns `null`, and nothing
complains.

`withPivot` is the list of what the middle table returns. It is the same
behavior as `$fillable`, in the other direction: Laravel only brings what
you declared.

When the middle table gains columns — role, order, date, who registered it —
it has stopped being a link and become an entity. Then it is worth
considering a model of its own for it, instead of pushing everything into
the pivot.
:::

To write:

```php
$book->authors()->attach($author->id, ['role' => 'translator']);
$book->authors()->detach($author->id);
$book->authors()->sync([3, 7, 12]);
```

`sync` is the scariest one: it leaves the list **exactly** as you sent it,
removing whatever is not there. It is right for a form with checkboxes, and
it is data loss when used thinking it adds.

## N+1: a hundred queries behind an arrow

```php title="app/Http/Controllers/CatalogController.php" numbered
$books = Book::orderBy('title')->paginate(47);

foreach ($books as $book) {
    echo $book->title;
    echo $book->authors->pluck('name')->join(', ');
    echo $book->copies->count();
}
```

Each `$book->authors` and each `$book->copies` fires its own query. For 47
books:

| Queries | Where they come from |
|---|---|
| 1 | `paginate`'s count |
| 1 | the list of books |
| 47 | the authors, one book at a time |
| 47 | the copies, one book at a time |
| 47 | the open loans, one book at a time |
| **143** | |

Table: It is the math Tainá did out loud. The name for this is **N+1**: one
query to bring the list, plus one per item.

:::term N+1
The pattern in which a query that brings N records causes N additional
queries, one for each.

It throws no error, does not show up in a test with three records and grows
linearly with the database. It is the most common performance defect in any
project with an ORM, in any language.
:::

## `with`, `load` and `withCount`

The fix is to say **beforehand** what you are going to need:

```php
$books = Book::with(['authors', 'copies'])
    ->withCount('copies')
    ->orderBy('title')
    ->paginate(47);
```

```sql
SELECT COUNT(*) FROM books;

SELECT *, (SELECT COUNT(*) FROM copies
           WHERE copies.book_id = books.id) AS copies_count
FROM books ORDER BY title ASC LIMIT 47 OFFSET 0;

SELECT authors.*, ... FROM authors
INNER JOIN author_book ON ...
WHERE author_book.book_id IN (1, 2, 3, ..., 47);

SELECT * FROM copies WHERE book_id IN (1, 2, 3, ..., 47);
```

Four queries. Laravel brings the list, gathers the identifiers and fetches
the related records at once, with `IN`.

| | Before | After |
|---|---|---|
| queries | 143 | 4 |
| time | ~4 s | ~40 ms |

Table: And the number **stops growing** with the page size. With 200 books
per page it is still four.

Three methods, three moments:

**`with()`** loads alongside, before the collection exists. It is the
normal case.

**`load()`** loads afterwards, on an object you already have in hand. It
serves when the decision to need the relationship comes after the query.

**`withCount()`** brings only the number, without the records. To show "3
copies", bringing the three is waste.

:::pitfall
The hardest N+1 to find is not in the controller: it is in
**serialization**.

A resource that does `'authors' => $this->authors->pluck('name')` fires the
query at the moment the response is assembled — after the controller has
finished, far from where anyone would look.

That is why the diagnostic tool is the query counter, and not reading the
controller.
:::

## The protection that turns N+1 into an error

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Model::preventLazyLoading(! $this->app->isProduction());
}
```

With that, reading a relationship that was not loaded **throws an
exception** outside production:

```text
Attempted to lazy load [authors] on model [App\Models\Book]
but lazy loading is disabled.
```

The effect is to turn a performance problem, which nobody sees, into a
development error, which nobody can ignore. It is the same idea as the
previous chapter's `preventSilentlyDiscardingAttributes`, applied to another
silence.

In production it stays off on purpose: one extra query is better than a
broken screen.

## One more hop, and polymorphism

A reader has loans; each loan is of a copy; each copy is of a book. To get
from reader to book takes two hops, and there is a method that does them in
one go.

It is worth it when the question is asked often — "which books has this
reader ever taken?" — and not when it appears once in a report. When in
doubt, write the query with a `JOIN`, which you know how to read.

A **polymorphic** relationship is for when the same kind of record points
to different things: a comment that can be about a book or about an author,
an attachment that can belong to anything.

It solves a real problem and charges dearly: the column that stores the
type is text, no foreign key is possible, and the database stops
guaranteeing the integrity it used to. Use it when the gain is clear — and
know that the checking is now yours.

## Cascading deletes

```php
$t->foreignId('book_id')->constrained()->cascadeOnDelete();
```

That tells the database: deleting a book deletes its copies. And, if the
loans are also cascading, it deletes the history along with them.

:::pitfall
Removing a book from the collection should not delete the record that Dona
Marlene took that copy home in 2019.

A loan is a **historical fact**. The grant's accountability report counts
loans, and a book removed from the collection does not undo what happened.

For entities with history, the right delete is almost never the physical
one. Laravel offers the logical one:

```php
use Illuminate\Database\Eloquent\SoftDeletes;

class Book extends Model
{
    use SoftDeletes;
}
```

`delete()` now fills a `deleted_at` column, and every query starts ignoring
records that have it filled. The record leaves the screens and stays in the
database, together with everything that points to it.
:::

Cascading is still the right choice for what is **part** of something else
and has no life of its own: an order's items, a poll's options, a
configuration's lines.

:::note In your career
"The screen is slow" is a report, not a diagnosis — and the difference
between whoever solves it in ten minutes and whoever spends the afternoon is
having a number before having a hypothesis.

Count the queries first. If there are dozens for one screen, it is N+1, and
the fix is one line. If there are three queries taking four seconds, it is
an index or volume, and the fix is another. Both look the same to whoever
is waiting for the screen to load.

And it works as an interview answer: when they ask what you do with a slow
page, "I measure first" is a better answer than any list of optimizations.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Models/
    Book.php         # hasMany copies, belongsToMany authors
    Author.php
    Copy.php         # belongsTo book, hasMany loans
    Reader.php       # hasMany loans
    Loan.php         # belongsTo copy, belongsTo reader
  database/migrations/
    ..._create_authors_table.php
    ..._create_author_book_table.php
:::

:::milestone
End of Part 3. The collection has models with types, scopes and
relationships; the queries the ORM produces are the same ones you would
write by hand; and the listing that took four seconds takes forty
milliseconds, with the proof counted in queries.
:::

:::summary
- The foreign key lives in the table that has the many; whoever has the
  column uses `belongsTo`.
- Reading a relationship fires a query: it is a call that looks like a
  property.
- Many to many uses a middle table with a conventional name — both singulars
  in alphabetical order.
- `withPivot` declares which middle-table columns come back; without it,
  they arrive silently null.
- `sync` leaves the list exactly as sent, removing the rest.
- N+1 is one query for the list plus one per item; it throws no error and
  grows with the database.
- `with` loads before, `load` loads after, `withCount` brings only the
  number.
- The best-hidden N+1 is in serialization, not in the controller.
- `preventLazyLoading` turns the silent problem into an error outside
  production.
- Cascading is for what is part of something else; history calls for
  logical deletion.
:::

:::checkpoint
You model relationships in both directions and many-to-many with
attributes, identify an N+1 by counting queries instead of reading code, fix
it with `with` and `withCount`, and prove the fix with the same counter.
:::

:::exercise level=1
Say which relationship to declare in each model, and which table holds the
foreign key:

1. A reader has several loans.
2. A loan has one fine; the fine belongs to one loan.
3. A copy has gone through several loans.

:::answer
1. `Reader::loans()` is `hasMany`; `Loan::reader()` is `belongsTo`. The
   `reader_id` column is in `loans`.
2. `Loan::fine()` is `hasOne`; `Fine::loan()` is `belongsTo`. The `loan_id`
   column is in `fines` — on the side that points, even though it is one to
   one.
3. `Copy::loans()` is `hasMany`; `Loan::copy()` is `belongsTo`. The
   `copy_id` column is in `loans`.

Case 2 is the confusing one. In a one-to-one relationship, either side could
have the column, and the choice is a design one: it goes on the
**optional** side. Not every loan generates a fine, so `loans` should not
carry an almost-always-null column pointing to a row that does not exist.
:::

:::exercise level=2
This screen shows open loans with the reader's name, the book's title and
the accession number. It does a double N+1.

```php
$loans = Loan::whereNull('returned_at')->get();

foreach ($loans as $l) {
    echo $l->reader->name;
    echo $l->copy->book->title;
    echo $l->copy->accession;
}
```

Count the queries for 30 loans, fix it and count again.

:::answer
**Before.** One for the list. Thirty for the readers. Thirty for the copies.
And thirty for the books — because `$l->copy->book` only happens after the
copy has arrived.

Total: **91 queries**.

**The fix** needs to load two levels, and the notation is the point:

```php
$loans = Loan::whereNull('returned_at')
    ->with(['reader', 'copy.book'])
    ->get();
```

**After.** One for the loans. One for the readers, with `IN`. One for the
copies, with `IN`. One for the books, with `IN`.

Total: **4 queries**, and the number does not change with three hundred
loans.

`copy.book` is the part people forget: loading `copy` alone solves two
thirds of the problem and leaves the third N+1 in place — which is worse
than fixing nothing, because now it looks solved.
:::

:::exercise level=3
The association asked to "clean up the collection": remove the books that
have not been borrowed in more than ten years.

Write the query that finds those books and answer: what exactly happens to
the copies and the loan history in each of three options — physical
cascade, logical deletion, and a third one you propose?

:::answer
**The query:**

```php
$candidates = Book::whereDoesntHave(
    'copies.loans',
    fn ($q) => $q->where('borrowed_at', '>=', now()->subYears(10)),
)->get();
```

`whereDoesntHave` becomes a `NOT EXISTS` with a subquery — and notice that
it includes books that were **never** borrowed, which is probably desired
and needs to be confirmed with Vera before running.

**Physical cascade.** Deletes the book, the copies and, if the cascade goes
on, the loans. The "most borrowed of 2019" report starts returning numbers
different from those printed in 2019. It is the worst option, and it is the
one that looks cleanest.

**Logical deletion.** The book gets `deleted_at`, disappears from screens
and queries. The loans remain, but point to a book normal queries do not
bring — so the historical report starts showing rows with a blank title,
which is the defect from chapter @cap:classes-e-objetos coming back.

It can be solved, but requires historical reports to explicitly ask for
removed records. It is a decision that needs to be written down somewhere.

**The third: don't delete.** What the association wants is not to remove
the record; it is to stop showing the book on the screen of someone looking
for something to take home. That is a **state**, not a deletion:

```php
$book->update(['state' => BookState::Deactivated]);
```

The active collection filters by state. The history stays complete, the
title keeps appearing in reports, and the operation can be undone — someone
can reactivate the book the following week without restoring a backup.

The question that leads to this answer, and that applies to almost every
request to "delete": **what does the person want to stop seeing, and for
how long?**
:::
