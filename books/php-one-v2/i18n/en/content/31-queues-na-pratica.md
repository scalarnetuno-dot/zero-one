---
source_hash: e5a77fa80cb2
title: "Queues in practice"
number: 31
slug: queues-na-pratica
part: p8
kicker: "The nine o'clock notice arrived at three in the afternoon. Ahead of it, in the same queue, were Seu Juvenal's two hundred thousand books."
goal: >-
  Measure the queue by waiting time, split work into queues with priority
  and their own workers, import in batches with progress, chain steps that
  depend on each other, respect the provider's pace without wasting
  attempts, prevent double work and get right the timeout and retry_after
  pair that causes most repeats.
---

:::story The nine o'clock notice
The state school finally sent the donations spreadsheet — the same
two-hundred-thousand-line one from volume 1 —, and Tainá turned the import
into jobs: one job per thousand lines, two hundred jobs, dispatched at 8:50
on a Monday.

At 9:00, the scheduler dispatched the three hundred "your book is due
tomorrow" notices. They entered the queue. **Behind** the two hundred import
jobs.

At 15:10, Seu Juvenal called.

— A message just arrived saying my book is due tomorrow. The library closes
at six. I'm in Guarulhos.

Tainá opened the server.

```text
$ php artisan queue:monitor database:default
  database:default ........................... [312] OK
```

— Three hundred and twelve jobs, and it says OK — she said.

— It says OK because the default limit is a thousand — said Dedé. — Three
hundred and twelve looks like little. What it doesn't say is that each
import job takes almost two minutes, that there's only one worker, and that
the nine o'clock notice is at the end of the queue.

— So the problem is the number of workers?

— The problem is that the notice and the import are in the same queue. One
is for right now. The other is for whenever.
:::

## The metric is the wait

Chapter @cap:events-jobs-e-filas got the queue up and running: the
`database` driver, a worker with a supervisor, retries, `failed_jobs` and
idempotent jobs. All of that is still right. What it did not need to answer
is what happens when work with **different urgencies** shares the same
worker.

The first thing to change is what gets measured. The queue's size misleads:
three hundred one-second jobs are five minutes; three hundred two-minute jobs
are ten hours. What the reader feels is **how long the oldest job has been
waiting**:

```sql
SELECT queue,
       COUNT(*) AS jobs,
       TIMESTAMPDIFF(MINUTE, FROM_UNIXTIME(MIN(available_at)), NOW())
           AS wait_min
FROM jobs
WHERE reserved_at IS NULL
GROUP BY queue;
```

```text
+---------+------+----------+
| queue   | jobs | wait_min |
+---------+------+----------+
| default |  312 |      380 |
+---------+------+----------+
```

Three hundred and eighty minutes. That is the sentence that would have woken
someone up at 9:30, and not at 15:10.

`queue:monitor` also works, with the right limit and scheduled: when a queue
goes past `--max`, it fires the `QueueBusy` event, and whoever listens to it
alerts the team.

```php title="routes/console.php" numbered
Schedule::command('queue:monitor', [
    'database:notices,database:default', '--max' => 50,
])->everyFiveMinutes();
```

```php title="app/Providers/AppServiceProvider.php" numbered
Event::listen(function (QueueBusy $event) {
    Log::warning('queue-busy', [
        'queue' => $event->queue,
        'jobs' => $event->size,
    ]);
});
```

## One queue per urgency

Queues have names. A job chooses its own when dispatched, or in the class
itself:

```php
ImportBatch::dispatch($rows)->onQueue('import');
```

And the notification from chapter @cap:mail-e-notificacoes, which becomes
one job per channel, chooses each channel's queue:

```php title="app/Notifications/ReturnTomorrow.php" numbered
public function viaQueues(): array
{
    return [
        'mail' => 'notices',
        WhatsAppChannel::class => 'notices',
        'database' => 'notices',
    ];
}
```

The worker reads the queues **in the order they were listed**:

```text
$ php artisan queue:work --queue=notices,default,import
```

On every job, it first looks at `notices`; only if it is empty, `default`;
only if both are empty, `import`. The nine o'clock notices get ahead of the
two hundred batches, because the worker never takes a batch while a notice is
waiting.

:::pitfall
The order is strict priority. If `notices` never empties — a very busy day,
a slow provider —, `import` never runs. For work that must not starve, give
it its own worker.
:::

At Casa Amarela, two programs in the supervisor:

```ini title="/etc/supervisor/conf.d/casa-amarela.conf" numbered
[program:casa-amarela-urgent]
command=php artisan queue:work --queue=notices,default
    --tries=3 --max-time=3600
numprocs=2

[program:casa-amarela-heavy]
command=php artisan queue:work database-long
    --queue=import,covers --tries=2 --timeout=300
    --max-time=3600
numprocs=1
```

(The `command` lines are broken to fit the page; in the file, each is a
single line. `database-long` is explained further on.)

Two workers for what is urgent, one for what is heavy. The heavy one can
take all afternoon, and the nine o'clock notice goes out at nine.

## Importing in batches, with progress

Two hundred loose jobs cannot answer a question Vera asked in the third
minute: **how far along is it?** A **batch** groups jobs, tracks progress and
calls someone when everything is done.

A batch needs a table, created once:

```text
$ php artisan make:queue-batches-table
$ php artisan migrate
```

And the import now builds the batch with the `readCsv` generator from
chapter @cap:manipulacao-de-arquivos — which came from the old project into
`app/Import/functions.php`, loaded by Composer's `files` as in chapter
@cap:como-organizar-um-projeto-php —, now inside a `LazyCollection`:

```php title="app/Import/ImportDonations.php" numbered
public function __invoke(string $path): Batch
{
    $reading = fn () => yield from readCsv($path);

    $batches = LazyCollection::make($reading)
        ->chunk(1000)
        ->map(fn ($rows) => new ImportBatch(
            $rows->values()->all(),
        ));

    return Bus::batch($batches->all())
        ->name('donations ' . basename($path))
        ->onConnection('database-long')
        ->onQueue('import')
        ->allowFailures()
        ->then(fn (Batch $batch) => Log::info('import-ok', [
            'batch' => $batch->id,
        ]))
        ->finally(fn (Batch $batch) => Cache::forget('catalog'))
        ->dispatch();
}
```

Reading is still one line at a time: the `LazyCollection` asks the generator
for a thousand lines, creates a job with them, and only then asks for the
next thousand. But notice the `$batches->all()`: `Bus::batch` needs the list
of jobs, and each job carries its thousand lines. At the moment of dispatch,
the whole spreadsheet is in memory, split into two hundred pieces — the
thirty megabytes from chapter @cap:manipulacao-de-arquivos, for a few
seconds. For nine megabytes of CSV, it is an acceptable price. For ninety,
the batch is born empty and a reading job adds the chunks bit by bit, with
`$batch->add([...])`.

**`allowFailures()`** decides what happens when a chunk fails. Without it,
the first failure cancels the rest. With it, the other 199 carry on, and the
chunk that failed goes to `failed_jobs`, where it can be fixed and retried.
For a donations import, that is the right behavior: one line with the year
spelled out should not stop the other 199,999.

**`then`** runs when all of them finish successfully; **`finally`**, when all
of them finish, with or without failure. The `Cache::forget('catalog')` is
the care from chapter @cap:cache-logs-e-medicao: the catalog page cannot
show yesterday's list.

:::pitfall
The `then`, `catch` and `finally` closures are **stored in the database** and
run later, by another process. They cannot use `$this`, nor variables that
are not serializable. Pass only simple values — ids, text — and fetch the
rest inside the closure.
:::

The chunk's job checks, before working, whether someone cancelled the
batch:

```php title="app/Jobs/ImportBatch.php" numbered
final class ImportBatch implements ShouldQueue
{
    use Batchable, Queueable;

    public int $timeout = 240;

    public function __construct(public readonly array $rows) {}

    public function handle(Importer $importer): void
    {
        if ($this->batch()?->cancelled()) {
            return;
        }
        $importer->import($this->rows);
    }
}
```

And Vera gets the answer to "how far along is it?":

```php title="app/Http/Controllers/ImportController.php" numbered
public function show(string $id)
{
    $batch = Bus::findBatch($id) ?? abort(404);

    return [
        'name' => $batch->name,
        'progress' => $batch->progress(),
        'pending' => $batch->pendingJobs,
        'failures' => $batch->failedJobs,
        'finished' => $batch->finished(),
    ];
}
```

```text
{"name":"donations state-school.csv","progress":37,
 "pending":126,"failures":1,"finished":false}
```

A detail that shows up in the import's last minute: the chunk that failed
still counts as **pending**. With 199 good chunks and 1 failed, progress
stops at 99, `pending` and `failures` are both 1, `finally` has already run
— and `finished` only becomes `true` when someone fixes the line and retries
the chunk. Vera's panel should show this as "finished with one failure", and
not as "almost there".

## Chaining what depends

A batch is for **independent** work, which can run in any order. When one
step needs the previous one, it is a **chain**:

```php
Bus::chain([
    new PrepareCover($book->id, $original),
    new ForgetCatalogCache(),
])->onQueue('covers')->dispatch();
```

`ForgetCatalogCache` only runs if chapter @cap:upload-de-arquivos's
`PrepareCover` finishes well. If the cover fails, the cache is not cleared
for nothing — and the chain stops there, with the failed job in
`failed_jobs`.

## The provider's pace

The WhatsApp provider accepts sixty messages a minute. Three hundred notices
dispatched at nine, with two workers, go out in forty seconds — and two
hundred and forty come back with a `429` error.

Laravel limits the pace with a **named limiter** and a **job middleware**:

```php title="app/Providers/AppServiceProvider.php" numbered
RateLimiter::for('whatsapp', fn () => Limit::perMinute(60));
```

```php title="app/Notifications/ReturnTomorrow.php" numbered
public function middleware(object $reader, string $channel): array
{
    return $channel === WhatsAppChannel::class
        ? [new RateLimited('whatsapp')]
        : [];
}

public function retryUntil(): DateTime
{
    return now()->addHours(3);
}
```

The middleware runs before the job. If the minute's limit has already been
used, it does not run the job: it **puts it back on the queue** with a
delay, to try again when the minute turns over. E-mail and history, which
have no limit, carry on without waiting.

`retryUntil` is not a detail. Each time `RateLimited` puts the job back on
the queue, Laravel counts **one attempt**. With `--tries=3`, a notice that
waited three minutes for its turn goes to `failed_jobs` without ever having
really failed. `retryUntil` swaps the attempt limit for a time limit: the
notice can wait its turn as many times as it needs, until three hours after
dispatch.

:::key
An attempt is a count of **trips back to the queue**, not of errors.
Anything that puts the job back on purpose — rate limiting, a lock, an
unavailable dependency — uses up an attempt. For those jobs, limit by time
(`retryUntil`), not by number.
:::

## Not doing it twice

Three tools for three situations, all in the same spirit as the idempotent
job from chapter @cap:events-jobs-e-filas:

**A job that cannot be in the queue twice.** The association's monthly
report is heavy, and the "generate" button gets pressed out of impatience.
The `ShouldBeUnique` contract blocks the second dispatch until the first has
finished:

```php title="app/Jobs/GenerateMonthlyReport.php" numbered
final class GenerateMonthlyReport implements
    ShouldQueue,
    ShouldBeUnique
{
    use Queueable;

    public int $uniqueFor = 3600;

    public function __construct(public readonly string $month) {}

    public function uniqueId(): string
    {
        return $this->month;
    }
}
```

March's and April's can be in the queue together; two of March's, no.

**Two jobs that cannot run at the same time for the same thing.**
Recalculating a reader's fine while another job records one of their returns
produces an amount neither of them wanted. The `WithoutOverlapping`
middleware puts a lock per key:

```php
public function middleware(): array
{
    return [(new WithoutOverlapping("reader:{$this->readerId}"))
        ->releaseAfter(30)];
}
```

**A scheduled task that cannot run on two servers.** With Casa Amarela's
second web server, both schedulers dispatched the nine o'clock notices:

```php
Schedule::call(new DispatchReturnNotices)
    ->dailyAt('09:00')
    ->onOneServer()
    ->withoutOverlapping();
```

`onOneServer` uses the cache to elect one server per run — and therefore
requires a shared cache, like `database` or `redis`, and not each machine's
`file` cache.

## `timeout` and `retry_after`

This is the pair of numbers responsible for most duplicate messages in
production, and Casa Amarela has already paid for it once.

`timeout` is how long the **worker** lets a job run before killing it.
`retry_after` is how long the **queue** waits for a reserved job before
concluding the worker died and handing it to another.

```php title="config/queue.php" numbered
'database' => [
    'driver' => 'database',
    'table' => 'jobs',
    'queue' => 'default',
    'retry_after' => 90,
],
```

An `ImportBatch` with a 240-second `timeout`, on that connection, does this:
at 90 seconds, the queue thinks it died and hands it to a second worker. Both
import the same thousand lines. Nothing failed, no log warned — and the
collection has two *Vidas Secas* with the same accession number, if the
database doesn't have the unique constraint from chapter
@cap:migrations-seeders-e-factories.

The rule: **`retry_after` greater than the largest `timeout` of the jobs on
that connection**, with headroom. Since `retry_after` belongs to the
**connection**, and not the queue, long jobs get a connection of their own:

```php title="config/queue.php" numbered
'database-long' => [
    'driver' => 'database',
    'table' => 'jobs',
    'queue' => 'import',
    'retry_after' => 360,
],
```

It is the `database-long` from the supervisor and the batch. Same table, same
database, different patience.

:::warning
A `retry_after` smaller than `timeout` produces no error, warning or log
line. It produces double work, now and then, only on the slowest jobs — which
are exactly the ones nobody is watching. Check both numbers whenever you
create a job that may run for more than a minute.
:::

## The worker is a process that ages

Chapter @cap:escopo-e-referencias warned: a `static` variable and an
in-memory cache last as long as the process lasts. In a web request, that is
an instant. In a worker, it is hours — and each job leaves a little memory
behind.

Three `queue:work` options put a limit on the worker's age, and the
supervisor starts a new one in its place:

| Option | Shuts the worker down after |
|---|---|
| `--max-jobs=500` | five hundred jobs |
| `--max-time=3600` | one hour |
| `--memory=256` | going over 256 MB |

Table: A worker that retires on its own needs nobody to restart it in the
middle of the night.

## When it fails in production

The `failed_jobs` table is the queue's inbox. Three commands to handle it:

```text
$ php artisan queue:failed
$ php artisan queue:retry --queue=notices
$ php artisan queue:prune-failed --hours=720
```

The first lists them, with each one's exception. The second puts back on the
queue everything that failed on the `notices` queue — after the provider
comes back, and not before. The third deletes those older than thirty days,
and is worth scheduling: a failures table with two years of junk hides
today's failure.

With Redis instead of `database`, **Horizon** gives a dashboard for all this
— queues, waits, failures, workers — and adjusts the number of workers on its
own. For Casa Amarela, the wait query and `queue:monitor` are enough; the day
they aren't is the day to switch drivers.

:::note In your career
The queue is where systems keep what they don't want to see. Work leaves the
request, the screen gets fast, and the problem starts happening in a process
with no screen, in the middle of the night, that nobody opens.

Three questions before putting any work on a queue: **how long can it
wait?** — that chooses the queue. **How long can it take?** — that chooses
the `timeout` and the connection. **Who finds out if it doesn't happen?** —
that chooses `failed()`, the monitor and the alert. If the third answer is
"nobody", it is not ready for the queue yet.
:::

:::tree title="Where we are now"
casa-amarela/
  app/
    Import/ImportDonations.php      # batch, generator, progress
    Jobs/
      ImportBatch.php               # Batchable, timeout 240
      GenerateMonthlyReport.php     # ShouldBeUnique per month
    Notifications/ReturnTomorrow.php # notices queue, WhatsApp pace
  config/queue.php                  # database and database-long
  routes/console.php                # monitor, onOneServer, prune
:::

:::summary
- Measure the oldest job's wait, not the queue's size.
- Named queues separate urgencies; `--queue=a,b,c` is strict priority. Work
  that must not starve gets its own worker.
- `Bus::batch` groups, shows progress and calls `then`/`finally`;
  `allowFailures()` keeps one failure from cancelling the rest.
- `Bus::chain` runs in order and stops at the first error.
- `RateLimited` puts the job back on the queue and uses up an attempt: use
  `retryUntil`.
- `ShouldBeUnique`, `WithoutOverlapping` and `onOneServer` prevent double
  work in three different situations.
- The connection's `retry_after` greater than the `timeout` of any of its
  jobs.
- `--max-jobs`, `--max-time` and `--memory` retire the worker in time.
- `failed_jobs` is an inbox: list, retry, prune.
:::

:::checkpoint
You measure a queue by its wait, separate urgent work from heavy work,
import two hundred thousand lines in a batch with progress, respect a
provider's limit without losing notices, prevent double work in the three
places it shows up, and get the `timeout` and `retry_after` pair right.
:::

:::exercise level=1
Which queue — `notices`, `default`, `import` or `covers` — would you put each
job on, and why?

1. The loan receipt, by WhatsApp.
2. Reindexing the catalog search, after an import.
3. The thumbnail of the cover Vera just uploaded.
4. The "your reservation is available" e-mail.

:::answer
1. `notices`. The reader is at the counter waiting.
2. `import`. It may take minutes and can wait until the small hours.
3. `covers`. It is heavy, and Vera accepts seeing the cover in a minute or
   two; it should not compete with the notices.
4. `notices`. The reservation has a deadline, and every minute of delay is a
   minute less for the reader to pick up the book.
:::

:::exercise level=2
The `SyncWithNationalCatalog` job queries an external API that sometimes
takes up to three minutes to answer. It is on the default `database`
connection, with a `retry_after` of 90 and a `timeout` of 200. Describe what
happens on a slow response and write the corrected configuration.

:::answer
At 90 seconds, the queue gives the job up for lost and hands it to another
worker, while the first is still waiting for the API. Both copies query the
API and write the result — twice, with no error at all. At 200 seconds, the
first may still be killed by the `timeout` and count as a failure.

Fix: the job goes to the long connection, with `retry_after` above the
`timeout`, and the `timeout` above the API's worst time:

```php
// config/queue.php, on the 'database-long' connection
'retry_after' => 360,

// in the job
public int $timeout = 240;

SyncWithNationalCatalog::dispatch()
    ->onConnection('database-long')
    ->onQueue('import');
```

And, since the API is external, the job must be idempotent all the same:
write with "update if it exists" by the catalog identifier, never a blind
`INSERT`.
:::

:::exercise level=3
Design Casa Amarela's queue for the day the association opens its second
library, in the neighboring district, on the same system: twice the notices,
one import a week and covers uploaded by both librarians. Say how many
workers of each kind, which numbers you would monitor, with what limit, and
at what point you would swap `database` for `redis`.

:::answer
Workers:

- **urgent** (`notices,default`): from two to three. Six hundred notices at
  nine, limited to sixty a minute on WhatsApp, take ten minutes no matter
  what; the third worker is so e-mail and history don't wait for WhatsApp.
- **heavy** (`import,covers`, long connection): still one. The weekly import
  can take the night; covers are few.

I would monitor:

- the oldest job's wait in `notices`: alert above **5 minutes**;
- the wait in `import`: alert above **12 hours** — it can wait, but not
  forever;
- new `failed_jobs` per hour: alert above **10**;
- the workers' memory, through the supervisor.

I would switch to `redis` when one of these happens: the wait query gets
slow on the `jobs` table, workers start fighting over the same row often
(visible as jobs reserved and released in sequence), or the team needs the
Horizon dashboard to understand what is going on. Not before: two districts
still fit in a table.
:::
