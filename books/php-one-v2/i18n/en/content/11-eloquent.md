---
source_hash: 89c547b7688c
title: "Eloquent"
number: 11
slug: eloquent
part: p3
kicker: "The reader sign-up accepted a field the form didn't have. Whoever found it became head librarian in nine seconds."
goal: >-
  Use the ORM knowing which query each method produces, protect sign-up
  against fields nobody asked for, convert values on the way into and out
  of the database, and recognize when a model has become a storeroom.
---

:::story Admin role
Tainá was testing the public reader sign-up with `curl`, because a form hides
fields and she wanted to see what the API really accepted.

```text
$ curl -s -X POST localhost:8000/api/readers \
       -H "Content-Type: application/json" \
       -d '{"name":"Test","document":"11122233344",
            "role":"admin"}'
```

```text
{"id":4102,"name":"Test","document":"11122233344",
 "role":"admin"}
```

She read it twice.

— Dedé, does the sign-up form have a role field?

— No. Only Vera changes roles, on her screen.

— Then why did it accept it?

Dedé opened the model. The class's second line was:

```php
protected $guarded = [];
```

— That means nothing is protected.

— That means I'm an administrator now.
:::

## Eloquent is not magic SQL

Every Eloquent method produces a query, and you can write all of them by
hand — that is what the chapters of Part 2 of volume 1 did.

This whole chapter follows one rule: **no method appears without the query
beside it.**

```php
Book::where('subject', 'children')->orderBy('title')->get();
```

```sql
SELECT * FROM books WHERE subject = ? ORDER BY title ASC
```

The `?` is not decoration: Eloquent builds a prepared statement, always, for
the reason in chapter @cap:pdo. The value travels separately from the
command.

:::key
The ORM does not spare you from knowing SQL. It spares you from **writing**
the repetitive SQL — the five-column `SELECT`, the `INSERT` with eight
fields, the obvious `JOIN`.

The SQL that matters is still written by someone. The difference is that,
with the ORM, you only need to write what is interesting.
:::

## The model and the conventions

```php title="app/Models/Book.php" numbered
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Book extends Model
{
    protected $fillable = [
        'title', 'author', 'isbn', 'subject', 'year',
    ];
}
```

Six useful lines, and the model already knows how to read and write. The
conventions it assumed:

| Convention | Assumed value |
|---|---|
| table | plural of the class name |
| primary key | `id` |
| dates | `created_at` and `updated_at` |

Table: All of them can be adjusted, and the first often needs adjusting.

:::pitfall
Laravel's pluralizer speaks English. With this project's names it gets it
right — `Book` becomes `books`, `Copy` becomes `copies` —, but the original
Casa Amarela code was named in Portuguese, and there it guesses wrong:

| Class | Laravel looks for | The table is called |
|---|---|---|
| `Livro` | `livros` | `livros` |
| `Exemplar` | `exemplars` | `exemplares` |
| `Leitor` | `leitors` | `leitores` |
| `Emprestimo` | `emprestimos` | `emprestimos` |

Table: Two hits and two misses, and the miss shows up as
`Table 'casa_amarela.exemplars' doesn't exist` on the first query.

The fix is one line, and it is worth declaring **in every model** of any
project whose names are not plain English — including the ones that would
work, so nobody has to remember which are which:

```php
protected $table = 'copies';
```
:::

## Active Record: the object that knows how to save itself

```php
$book = new Book();
$book->title = 'Vidas Secas';
$book->author = 'Graciliano Ramos';
$book->subject = 'literature';
$book->save();
```

```sql
INSERT INTO books (title, author, subject, updated_at, created_at)
VALUES (?, ?, ?, ?, ?)
```

```php
$book->year = 1938;
$book->save();
```

```sql
UPDATE books SET year = ?, updated_at = ? WHERE id = ?
```

The same method does both things, and the object decides which by whether
the key exists. That is the **Active Record** pattern: the record and the
behavior in the same object.

It is convenient and has a cost that shows up in two places. The object
carries a dependency on the database everywhere it goes — and testing the
rule that lives inside it requires a database. That is why this book keeps
business rules in services, and uses the model for what it does well: going
to and from the table.

## Fetching, and the `null` that slips through

| Method | SQL | When nothing is found |
|---|---|---|
| `find(12)` | `WHERE id = ?` | returns `null` |
| `findOrFail(12)` | `WHERE id = ?` | throws, and becomes `404` |
| `first()` | `LIMIT 1` | returns `null` |
| `firstOrFail()` | `LIMIT 1` | throws, and becomes `404` |
| `value('title')` | `SELECT title ... LIMIT 1` | returns `null` |

Table: The first four differ in one thing only, and it is the most important
one.

```php
$book = Book::find($id);

echo $book->title;
```

```text
Attempt to read property "title" on null
```

`find` returned `null` and the error appears on the next line — or thirty
lines later, or in the view. The `OrFail` version fails in the right place,
with the right response:

```php
$book = Book::findOrFail($id);
```

```text
404 Not Found
```

:::key
Use `find` when `null` is **a possible answer** you are going to handle
right there. Use `findOrFail` when absence is an error.

In practice, inside a controller with the route model binding from chapter
@cap:rotas-e-controllers, you rarely write either: the framework has already
fetched it.
:::

And the method that looks harmless and is not:

```php
Book::all();
```

```sql
SELECT * FROM books
```

Four thousand rows in memory to show twenty. On a loans table with years of
history, it is the query that takes the server down on a Tuesday afternoon.
`paginate(20)` exists for that.

## Mass assignment

Back to `role=admin`.

```php
Reader::create($request->all());
```

`create` receives an array and fills the record with it. The question is:
**which fields does it accept?**

```php
protected $fillable = ['name', 'document', 'phone'];
```

With `$fillable`, it accepts those three and **silently ignores** any other.
The `role` Tainá sent is discarded.

The alternative, `$guarded`, is the list of what **cannot** be filled — and
`$guarded = []` means "nothing is forbidden", which is exactly what the
Reader model said.

:::pitfall
`$guarded = []` shows up in tutorials because it removes an obstacle for
people who are learning. It turns every column in the table into a public
form field.

The damage depends on what exists in the table: `role`, `balance`,
`approved`, `company_id`. In any system with more than one access level,
that line is a privilege escalation waiting for someone curious.

The rule: **`$fillable` always, with the list written by hand.** Writing the
list is the moment you decide, field by field, what the outside world may
fill in.
:::

And there is one more protection, which turns the silent discard into an
error:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Model::preventSilentlyDiscardingAttributes(
        ! $this->app->isProduction()
    );
}
```

In development, sending a field that is not in `$fillable` starts throwing
an exception. That is how you discover, on your machine, that the form is
sending a field the model ignores — instead of discovering it from the
missing data, three weeks later.

## Casts: the right type on both sides

The database stores text, numbers and dates. Your code wants enums and value
objects. `casts()` is the translation, in both directions:

```php title="app/Models/Copy.php" numbered
protected function casts(): array
{
    return [
        'status' => CopyStatus::class,
        'acquired_on' => 'immutable_date',
    ];
}
```

```php
$copy = Copy::find(1);

$copy->status;              // CopyStatus::Good
$copy->status->label();     // 'Available'
$copy->acquired_on;         // DateTimeImmutable
```

The column is still a `VARCHAR(20)` with `'good'` inside. What changes is
that no point in your code compares a loose string again — the lesson from
chapter @cap:enums-datas-e-valores now also holds at the database boundary.

For `Money`, which is neither an enum nor a date, the conversion is a class:

```php title="app/Casts/MoneyCast.php" numbered
<?php

declare(strict_types=1);

namespace App\Casts;

use App\Loans\Money;
use Illuminate\Contracts\Database\Eloquent\CastsAttributes;

class MoneyCast implements CastsAttributes
{
    public function get($model, $key, $value, $attributes): ?Money
    {
        return $value === null
            ? null
            : Money::inCents((int) $value);
    }

    public function set($model, $key, $value, $attributes): ?int
    {
        return $value?->cents;
    }
}
```

```php
'fine_in_cents' => MoneyCast::class,
```

Now `$loan->fine_in_cents` returns a `Money`, with `formatted()` and
`plus()` — and adding an integer number of days, which chapter
@cap:enums-datas-e-valores closed off, stays closed after going through the
database.

## Accessor: a computed value that looks like a column

```php title="app/Models/Loan.php" numbered
use Illuminate\Database\Eloquent\Casts\Attribute;

protected function daysOverdue(): Attribute
{
    return Attribute::make(
        get: fn (): int => max(
            0,
            $this->due_on->diffInDays(now(), absolute: false),
        ),
    );
}
```

```php
$loan->days_overdue;   // 3
```

It looks like a column and is not: it is computed on every read. It is worth
it when the value is derived from others already in the table — and that is
exactly why there is no `days_overdue` column, for the reason in chapter
@cap:duas-tabelas-conversando: a computed number does not drift from
reality.

## Scope: the query that gets a name

```php title="app/Models/Loan.php" numbered
use Illuminate\Database\Eloquent\Builder;

public function scopeOpen(Builder $q): void
{
    $q->whereNull('returned_at');
}

public function scopePastDue(Builder $q): void
{
    $q->whereDate('due_on', '<', now());
}
```

```php
Loan::open()->pastDue()->count();
```

```sql
SELECT COUNT(*) FROM loans
WHERE returned_at IS NULL AND date(due_on) < ?
```

The `scope` prefix disappears in the call, and the two combine in any order.

The gain is the usual one: the definition of "open" now lives in a single
place. The day a cancelled loan also counts as closed, the change is one
line — and not a search for `whereNull('returned_at')` across seventeen
files.

## See the SQL before trusting it

```php
Book::where('subject', 'children')->orderBy('title')->toSql();
```

```text
select * from `books` where `subject` = ? order by `title` asc
```

To see everything the request did, with the values and the time:

```php title="app/Providers/AppServiceProvider.php" numbered
if ($this->app->environment('local')) {
    DB::listen(function ($query): void {
        Log::debug($query->sql, [
            'values' => $query->bindings,
            'ms' => $query->time,
        ]);
    });
}
```

:::key
Turn this on on the first day of any project with an ORM and look at the log
after opening three screens.

It is the fastest way to discover that the loans listing is running two
hundred and one queries — and that number has a name, a known cause and is
the subject of the next chapter.
:::

## The giant model: the signs

The model starts with six lines and, if nobody says anything, reaches three
hundred. Three signs that this has happened:

**It has methods that do not talk to the database.** Fine calculation, limit
rule, due-date decision. None of that needs a table to exist, and all of it
starts needing one when it lives there.

**It imports things that are not data.** A model that uses `Mail`, `Http` or
`Storage` has stopped representing a row and become a process.

**It has a method you cannot test without a database.** This is the most
reliable sign, because it is verifiable: if checking the fine rule requires
inserting a loan, the rule is in the wrong place.

The way out is not to break the model into five. It is to **take out what
is not persistence**: the rule goes to the service or to the value object,
and the model keeps columns, casts, scopes and relationships.

:::note In your career
"Fat model or fat controller?" is an endless discussion, and it is the wrong
question. Both answers lump together two things that change for different
reasons: the way of storing and the business rule.

The test that settles it, and that you can apply to any project: **if Casa
Amarela swapped MySQL for something else, how much of the code would have
to change?** Everything that would have to change is persistence. The rest
is rule, and rules should not live in a file that only exists because of a
table.

It is not an argument about purity: it is about where testing gets cheap.
:::

:::tree title="Where we are now"
casa-amarela/
  app/
    Models/
      Book.php         # $table, $fillable
      Copy.php         # enum cast
      Reader.php       # $fillable without role
      Loan.php         # scopes, accessor, Money cast
    Casts/
      MoneyCast.php
    Providers/
      AppServiceProvider.php  # DB::listen and attribute protection
:::

:::summary
- Every Eloquent method produces a query, and it is a prepared one.
- The pluralizer speaks English: declare `$table` explicitly whenever names
  are not plain English.
- Active Record puts record and behavior in the same object — handy for
  persisting, expensive for testing rules.
- `find` returns `null`; `findOrFail` throws and becomes `404`.
- `all()` brings the whole table into memory.
- `$fillable` is the list of what the outside world may fill in;
  `$guarded = []` is a privilege escalation waiting for someone curious.
- `preventSilentlyDiscardingAttributes` turns discards into errors outside
  production.
- Casts convert in both directions: enum, immutable date and value object.
- An accessor is a computed value; a scope is a named query, and both live
  in one place.
- `toSql()` and `DB::listen` show what was really executed.
- A model that has rules without a database, calls external services or
  cannot be tested without a table has stopped being a model.
:::

:::checkpoint
You write queries with Eloquent and show the corresponding SQL, protect
sign-up with `$fillable`, convert enums and value objects with casts, name a
query with a scope, and recognize by the three signs when the rule has
leaked into the model.
:::

:::exercise level=1
Write the SQL each call produces:

```php
Book::where('year', '>=', 2000)->count();
Copy::where('status', 'good')->pluck('accession');
Reader::orderBy('name')->paginate(20);
Loan::whereNull('returned_at')->latest()->first();
```

:::answer
```sql
SELECT COUNT(*) FROM books WHERE year >= ?
```

```sql
SELECT accession FROM copies WHERE status = ?
```

```sql
SELECT COUNT(*) FROM readers;
SELECT * FROM readers ORDER BY name ASC LIMIT 20 OFFSET 0
```

```sql
SELECT * FROM loans
WHERE returned_at IS NULL
ORDER BY created_at DESC LIMIT 1
```

Three observations that separate those who read from those who understood.

`pluck` brings **only the requested column**, not the whole row — it is the
difference between bringing eight thousand complete rows and bringing eight
thousand numbers.

`paginate` runs **two** queries: one counts the total, to know how many
pages exist, and another brings the page. It is the most common cause of a
slow listing on a large table, and the reason `simplePaginate`, which skips
the count, exists.

And `latest()` orders by `created_at`, not by `id`. In a database where the
records were imported out of order, the two results differ.
:::

:::exercise level=2
The `Reader` model has `$guarded = []` and the table has the columns
`name`, `document`, `phone`, `role` and `blocked_at`.

Fix the model and write what changes in the public sign-up controller and in
the controller of Vera's screen, which **must** be able to change the role.

:::answer
```php title="app/Models/Reader.php" numbered
class Reader extends Model
{
    protected $table = 'readers';

    protected $fillable = ['name', 'document', 'phone'];

    protected function casts(): array
    {
        return ['blocked_at' => 'immutable_datetime'];
    }
}
```

The public sign-up does not change **a single line** — and that is the
point. It already did `Reader::create($data)`, and now the extra fields are
discarded.

Vera's screen does not use mass assignment for the role. It assigns
directly, which bypasses `$fillable` on purpose:

```php
$reader->role = $request->enum('role', Role::class);
$reader->save();
```

That looks like getting around the protection and is exactly the correct
design: `$fillable` protects against **what comes from outside in bulk**.
Direct assignment is a decision written in code, in a controller that only
someone with Vera's permission can reach.

`blocked_at` stays out of both: it changes through a named action — blocking
a reader — and not through a form.
:::

:::exercise level=3
This model arrived for review. It works.

```php
class Loan extends Model
{
    protected $guarded = [];

    public function calculateFine(): float
    {
        $days = (strtotime('now')
              - strtotime($this->due_on)) / 86400;

        if ($days <= 0) {
            return 0;
        }

        $value = $days * 0.8;

        if ($this->reader->role === 'student') {
            $value = $value / 2;
        }

        Mail::to($this->reader->email)
            ->send(new FineNotice($value));

        return $value;
    }
}
```

Point out the problems by category — security, correctness, design — and say
where each piece should live.

:::answer
**Security.** `$guarded = []` again, now on a table that has
`fine_in_cents` and `returned_at`. A client could register a loan that is
already returned, with no fine.

**Correctness.** Three defects, all seen before:

The difference between dates in seconds divided by 86,400 ignores time zones
and daylight-saving days, and returns a `float` with decimal places.

The value in `float` accumulates error with every sum — the calculation is
in cents.

And `0.8` is loose, diverging from `config/library.php`, which has existed
since chapter @cap:configuracao-ambiente-e-artisan.

**Design.** Two problems, and the second is serious.

The calculation does not need a database to exist. It is a rule, and it is
in a file that only exists because of a table — so testing "half fine for
students" requires inserting a loan, a reader and a copy.

And the method **sends e-mail**. A method called `calculateFine` that sends
a message to the reader is a surprise: any report that walks through two
hundred loans to add up fines has just fired two hundred e-mails.

**Where each piece goes.**

The day count and the value go to a service — `FineCalculator` — that
receives the dates and the configuration and returns `Money`. It is tested
without a database.

The student rule goes with it, because it is a business rule, and becomes an
explicit test case.

Sending the notice leaves here entirely. It is a consequence of an event —
the fine was recorded —, not part of calculating a number.

And the model keeps `$fillable`, the casts, the scopes and the
relationships. About fifteen lines.
:::
