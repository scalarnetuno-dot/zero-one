---
source_hash: 61aec468041c
title: "Cache, logs and what gets measured"
number: 24
slug: cache-logs-e-medicao
part: p6
kicker: "The catalog page got fast and started showing as available a book that was on loan. For six hours, which was the cache's lifetime."
goal: >-
  Make the application observable and fast, in that order: measure before
  optimizing, cache with a written invalidation strategy, and write
  structured logs you can search — without ever recording what must not be
  recorded.
---

:::story Six hours
The complaint came through Vera, who heard it at the counter.

— The girl says the app showed *A Hora da Estrela* as available. She crossed
the neighborhood to get it. It's been on loan since yesterday morning.

Dedé opened the app. There it was: *A Hora da Estrela*, "1 available", in
green.

He opened Vera's panel, which queried the database directly. Zero
available. Lent at 9:14 the day before.

— Cache — he said.

— What? — asked Vera.

— Last week the catalog listing was slow. Cléber added a cache. The list is
kept and only rebuilt every so often.

— How often?

Dedé looked.

```php
Cache::remember('catalog', 60 * 60 * 6, fn () => /* ... */);
```

— Six hours.

— So for six hours the app lies.

— Up to six hours.

— And who decided six hours?

Dedé looked in the ticket, in the commit, in the group chat. There was
nothing.

— Nobody, I think — he said. — I think it's a number that seemed
reasonable.

— It didn't seem reasonable to the girl who crossed the neighborhood — said
Vera.
:::

## A queue exists because waiting is expensive; so does a cache

The previous chapter took out of the request the work that did not need to
happen before the response. The cache attacks the same cost from another
side: **not redoing** work that has already been done and whose result has
not changed.

The month's most-borrowed listing groups half a million loans, joins copies
and books, and sorts. It takes eight hundred milliseconds. The result
changes a few dozen times a day, and is queried a few thousand. Computing it
on every query is paying eight hundred milliseconds thousands of times to
get, almost always, the same answer.

The cache keeps the answer and returns it until it needs to be recomputed.
And all the difficulty lies in that "until".

:::key
Caching is easy. The hard part is answering: **when does this value stop
being true, and who tells the cache?**

A cache without an answer to that question is a place where the application
stores lies with an expiry date.
:::

## Measure before optimizing

The story has a detail that is not in it: nobody measured why the catalog
listing was slow before adding the cache. The cache solved the slowness and
created the lie. With a measurement, the answer might have been different.

Laravel gives three ways to measure, in increasing order of effort.

**Counting queries**, with the `DB::listen` from chapter
@cap:relacionamentos:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    if ($this->app->isLocal()) {
        DB::listen(function (QueryExecuted $q) {
            if ($q->time > 100) {
                Log::channel('slow')->warning('slow query', [
                    'sql' => $q->sql,
                    'ms' => $q->time,
                ]);
            }
        });
    }
}
```

**MySQL's *slow query log***, which records every query above a certain
time, in production, without touching the code:

```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 0.5;
```

**Inspection tools in development.** Telescope, from Laravel itself,
records each request with the queries, jobs, logs and exceptions it
produced, and shows them in a dashboard. Debugbar puts the same summary in a
bar at the bottom of each Blade panel page. Both are for development, and
live in `require-dev` for the reason in chapter @cap:do-include-ao-composer.

Tainá turned on Telescope and opened the catalog listing. The request took
1.9 seconds and made four queries. Three took two milliseconds each. The
fourth took 1.8 seconds:

```sql
SELECT COUNT(*) FROM copies
WHERE book_id = books.id AND status = 'good'
```

The count of available copies, without a composite index. The `EXPLAIN`
from chapter @cap:duas-tabelas-conversando showed the database reading all
eight thousand copies for every book on the page.

```php
$t->index(['book_id', 'status']);
```

A one-line migration. The listing dropped to forty milliseconds, **without a
cache**, and without lying.

:::pitfall
The cache hides slowness, and hiding is not solving. The 1.8-second query is
still there, running every six hours — and running on the first request
after the cache expires, which is the one that pays the whole bill. If ten
people arrive in that second, all ten pay: ten 1.8-second queries at once.

Optimizing from measurement is changing the cause. Caching without measuring
is sweeping it under a rug.
:::

## `Cache::remember` and the hard question

There are places where caching is the right answer, and the month's most
borrowed is one of them: the query is expensive by nature — aggregating half
a million rows — and the result can be a few minutes behind without anyone
crossing the neighborhood because of it.

```php title="app/Catalog/MostBorrowed.php" numbered
final class MostBorrowed
{
    public function ofMonth(CarbonImmutable $month): Collection
    {
        return Cache::remember(
            $this->key($month),
            now()->addDay(),
            fn () => $this->calculate($month),
        );
    }

    public function forget(CarbonImmutable $month): void
    {
        Cache::forget($this->key($month));
    }

    private function key(CarbonImmutable $month): string
    {
        return 'most-borrowed:' . $month->format('Y-m');
    }

    private function calculate(CarbonImmutable $month): Collection
    {
        return Book::query()
            ->withCount(['loans' => fn ($q) => $q
                ->whereBetween('borrowed_at', [
                    $month->startOfMonth(),
                    $month->endOfMonth(),
                ])])
            ->orderByDesc('loans_count')
            ->orderBy('id')
            ->limit(10)
            ->get();
    }
}
```

`remember` looks for the key. If it finds it, it returns it. If not, it runs
the function, stores the result with the given lifetime and returns it. It is
the most used caching pattern, and its name describes it well: remember
this.

Notice that the key includes the month. February's ranking and March's are
different entries, and February's, once February is over, never changes
again.

### Invalidation by time and by event

There are two ways for a cached value to stop being valid.

**By time.** The lifetime expires, and the next query recomputes. It is
simple and **blind**: it does not know whether the value changed. Six hours
of lifetime means up to six hours of lying, even if the value changed one
second after being stored.

**By event.** When something that affects the value happens, someone deletes
the entry. The next access recomputes with the new data.

```php title="app/Listeners/ForgetMostBorrowed.php" numbered
final class ForgetMostBorrowed
{
    public function __construct(
        private readonly MostBorrowed $ranking,
    ) {}

    public function handle(LoanCreated $event): void
    {
        $this->ranking->forget(
            CarbonImmutable::parse(
                $event->loan->borrowed_at,
            ),
        );
    }
}
```

The event from chapter @cap:events-jobs-e-filas gained a second listener,
and the ranking is now always right: the cache is valid **until the next
loan**, and never beyond.

And the one-day lifetime is still there, as a safety net: if some path
changes loans without dispatching the event — a manual fix in the database,
an import script —, the error lasts at most a day. Events as the rule, time
as insurance.

| Strategy | The value may be wrong for | Cost |
|---|---|---|
| time only | up to the whole lifetime | no extra code |
| event only | forever, if a path forgets | one listener per cause |
| event + time | up to the lifetime, only on the forgotten path | both |

Table: The third row is the one Casa Amarela uses. The lifetime number
becomes a decision about the worst case, not about the common case.

:::pitfall
A copy's availability should **not** be cached, and not for lack of
technique. It changes with every loan and return, dozens of times an hour,
and the cost of it being wrong is a person crossing the neighborhood.

The question that decides what to cache has two parts: **how much it costs
to calculate** and **how much it costs to be wrong**. The most borrowed cost
a lot to calculate and almost nothing to be wrong for a few minutes.
Availability costs little to calculate — with the right index — and a lot to
be wrong.
:::

## Config, route and view caching

There is a second kind of cache in Laravel, and it does not store data: it
stores **the framework itself, already assembled**.

```text
$ php artisan config:cache
$ php artisan route:cache
$ php artisan view:cache
```

The first merges all the files in `config/` into one, with the `.env` values
already resolved — chapter @cap:configuracao-ambiente-e-artisan showed what
that does to `env()` outside `config/`. The second compiles the route
table. The third converts all Blade templates into PHP ahead of time.

Together, they save dozens of milliseconds per request in production, and
have a cost that is the same for all three: **from the moment they run,
changing the file changes nothing**. A new route, a new setting, a changed
view — none of it gets in until someone runs the command again.

That is why they belong in the **deploy script**, right after the new code
arrives, and never in the development environment. Chapter
@cap:git-ci-e-deploy puts each one in its place.

## A log is not `dd()`

`dd()` — *dump and die* — prints the value and ends execution. It is the most
used debugging tool in Laravel and the worst thing that can go to
production: forgotten on a rare path, it interrupts the request and shows
the user the contents of an internal variable.

```php
dd($reader);
```

The pipeline in chapter @cap:git-ci-e-deploy looks for `dd(`, `dump(` and
`var_dump(` in the code and refuses the commit. It is a one-line rule that
prevents a whole category of incident.

The log is the production tool. It records without interrupting, in a place
only the team reads, with a level that says how much it matters.

## Levels, channels and a log you can search

Levels follow a scale that comes from Unix systems and that every log tool
understands:

| Level | When | Example at Casa Amarela |
|---|---|---|
| `debug` | detail for development | intermediate values |
| `info` | something normal worth recording happened | loan created |
| `warning` | something odd that did not prevent anything | slow provider, retry |
| `error` | an operation failed | job in `failed_jobs` |
| `critical` | a part of the system is down | database unreachable |

Table: In production, the minimum level is usually `info`. Everything at
`debug` is discarded before being written.

And the **channel** says where it goes: a daily file, standard output, an
external service, a Slack channel for the `critical` ones.
`config/logging.php` declares the channels, and a `stack` channel can send
the same line to several.

The difference that matters most, though, is neither the level nor the
channel. It is the line's format.

```php
// free text
Log::info("Reader {$reader->id} took copy {$accession}");

// structured
Log::info('loan-created', [
    'reader' => $reader->id,
    'accession' => $accession,
    'book' => $book->id,
]);
```

The first line is easy to read and hard to search. To find all loans of
copy 2117, you need a regular expression that depends on the exact sentence
— which someone will change.

The second has a fixed message, which works like the `type` from chapter
@cap:erros-padronizados, and the data in separate fields. With the log in
JSON, the search becomes a query:

```php title="config/logging.php" numbered
'daily' => [
    'driver' => 'daily',
    'path' => storage_path('logs/laravel.log'),
    'level' => env('LOG_LEVEL', 'info'),
    'formatter' => JsonFormatter::class,
    'days' => 30,
],
```

```text
$ jq 'select(.context.accession == 2117)' storage/logs/laravel-*.log
```

And each line already comes out with the incident from chapter
@cap:middleware, because the `Context` adds everything it holds to every
line written during the request. Finding Wellington's exception is a
`grep`; finding **everything** that happened in his request, including what
worked before it failed, is the same `grep`.

## What never goes into the log

The middleware from chapter @cap:middleware solved its own log. The general
rule is broader, and it is worth writing as a list, because it is a list
you can check:

- passwords, in any form — including wrong ones, which are usually the right
  one with one character swapped;
- tokens, API keys, session cookies, the `Authorization` header;
- documents, CPF numbers, card numbers;
- the whole body of a request or response;
- health data, debt, anything a person would not tell a stranger.

Casa Amarela logs the reader's **id**, never the name or phone number. If
someone needs to know who reader 47 is, they query the database — which has
access control. The log is read by more people, kept longer, copied to more
places.

:::warning
An exception is the most common path by which sensitive data enters the log
without anyone writing `Log::`. A `QueryException` carries the SQL **with the
values**:

```text
SQLSTATE[23000]: Duplicate entry '12345678901' for key
'readers_document_unique' (SQL: insert into readers
(name, document, ...) values (Rosângela Pires, 12345678901, ...))
```

The CPF went into the log through the exception's message. The handler can
be configured to scrub that data before logging, and it is worth checking,
every so often, with a search for patterns — eleven digits in a row, `@` —,
what is actually being recorded.
:::

:::note In your career
"Measure before optimizing" is advice everyone repeats and few follow,
because measuring seems to delay the fix. The person already has a
hypothesis, and the hypothesis looks right.

What often happens is that the hypothesis is **half** right. The screen is
slow because of the database, yes — but not because of the query that looked
heavy, rather because of a missing index on one that looked harmless. Ten
minutes with Telescope open save the afternoon of optimizing the wrong
query, and leave a number to show at the next meeting, which is worth more
than any "it's faster now".
:::

:::tree title="Where we are now"
casa-amarela/
  app/Catalog/
    MostBorrowed.php               # remember + forget
  app/Listeners/
    ForgetMostBorrowed.php         # invalidation by event
  app/Providers/
    AppServiceProvider.php         # DB::listen locally
  config/logging.php               # JSON, daily, 30 days
  database/migrations/
    ..._book_status_index_on_copies.php
:::

:::milestone
End of Part 6. What did not need to wait has left the request; what was
expensive and could be a little behind got a cache with invalidation by
event; what was slow for lack of an index became fast with no cache at all;
and every log line has an incident, fields you can search and nothing that
must not be read.

In Tainá's notebook: *"who decided that number?"*.
:::

:::summary
- Caching is easy; the hard part is saying when the value stops being true
  and who tells the cache.
- Measuring comes first: `DB::listen`, the *slow query log*, Telescope.
  Often the answer is an index, not a cache.
- A cache hides slowness; the first request after expiry pays the whole
  bill.
- `Cache::remember` with a key that includes whatever distinguishes the
  value.
- Invalidation by time is blind; by event it is precise and fragile; the two
  together cover each other.
- What to cache is decided by the cost of calculating and the cost of being
  wrong.
- `config:cache`, `route:cache` and `view:cache` freeze the framework and
  belong in the deploy.
- `dd()` does not go to production; a structured log has a fixed message and
  data in fields.
- Passwords, tokens, documents and request bodies never go into the log —
  not even through an exception's message.
:::

:::checkpoint
You measure a slow screen before touching it, add a cache only where the
cost of being wrong is small and with invalidation by event, keep
availability always fresh, and write structured logs that a `grep` for the
incident finds — without a single piece of personal data inside.
:::

:::exercise level=1
For each value, say whether it is worth caching and, if so, with which
invalidation strategy:

1. The collection's list of subjects, which changes twice a year.
2. How many copies of a book are available right now.
3. The total loans of 2025, for the annual report.
4. The authenticated reader's profile, queried on every screen.

:::answer
1. Yes, by event (on saving a subject) and by a long time as insurance. It
   is the ideal case: it changes rarely, it is read all the time.
2. No. It changes all the time and being wrong costs a lot. With the right
   index, it is a millisecond query.
3. Yes, **without invalidation**: 2025 is over. The value never changes
   again — except by a manual fix, and then whoever fixes it forgets the key
   by hand.
4. Probably not. It is a primary-key lookup, which the database answers in
   under a millisecond; the cache would save almost nothing and create the
   risk of showing an old phone number after the reader changes it.

Item 4 is the most common in real code, and the reason is that it seems
obvious: "it's queried all the time". Frequency is not enough. What decides
is the cost of each query.
:::

:::exercise level=2
Rewrite this snippet as a structured log, and point out what it records
that it should not:

```php
Log::info("Login by {$request->email} with password "
    . "{$request->password} at " . now()
    . " — result: " . ($ok ? 'ok' : 'failed'));
```

:::answer
It records the **password**. As text. Including the wrong ones, which are
usually the right one with a typo, and sometimes the password for another
service the person typed by mistake.

It also records the e-mail, which is personal data — acceptable in some
security logs, as long as with short retention and restricted access. And it
records `now()`, which is redundant: every log line already has a date.

```php
Log::info('login', [
    'result' => $ok ? 'ok' : 'failed',
    'user' => $user?->id,
    'ip' => $request->ip(),
]);
```

The user id, when it exists, identifies without exposing. For attempts with
a nonexistent e-mail, `user` stays null, and the `ip` is enough to
investigate an attack.

If the security team really needs the attempted e-mail — to detect someone
testing a list —, it goes in a **separate channel**, with retention of a few
days and restricted access, and never together with the password.
:::

:::exercise level=3
Vera's panel has a "summary of the day" screen: today's loans, today's
returns, overdue items, pending reservations. It takes 2.4 seconds. Someone
proposed caching it for five minutes.

Describe, in order, what you would do before accepting or rejecting the
proposal, and in which case you would accept it.

:::answer
**First, measure.** Open the screen with Telescope — or `DB::listen` — and
see how many queries there are and how long each takes. The screen has four
numbers; if there are four queries and one of them takes 2.3 seconds, the
problem is that one.

**Second, look at the slow query.** Run `EXPLAIN`. The usual suspects: a
missing index — `borrowed_at` without an index for "today's loans" is a
strong candidate —, a function applied to the column in the `WHERE`
(`DATE(borrowed_at) = ...` prevents index use; `borrowed_at BETWEEN start
AND end` does not), or a hidden N+1.

**Third, fix the cause and measure again.** If the screen drops to a hundred
milliseconds, the caching proposal loses its reason.

**When I would accept the cache.** If, after all that, one query remains
that is expensive by nature — the number of overdue items aggregates the
whole table of open loans and no index saves it. Then, cache **only that
number**, not the whole screen, and with the question answered for Vera:
"the number of overdue items may be up to five minutes behind; today's loans
and returns are always exact". If she says five minutes of delay in the
overdue number gets in the way of her work, the answer is different: a
counter maintained by the loan and return events.

The order matters because caching the whole screen would fix the symptom,
and Vera would see the loan she just made vanish from the summary for up to
five minutes — the *Hora da Estrela* defect, on her own panel.
:::
