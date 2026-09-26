---
source_hash: 6711707cdf77
title: "Events, jobs and queues"
number: 23
slug: events-jobs-e-filas
part: p6
kicker: "The return reminder was sent 1,400 times to the same person. The job wasn't idempotent, and the worker restarted halfway through."
goal: >-
  Take out of the request the work that does not need to happen before the
  response, decouple with events without hiding the flow, run queues with a
  worker that restarts on deploy, and write jobs that can fail, come back
  and run again without repeating the effect.
---

:::story One thousand four hundred
Casa Amarela's phone rang at 7:10 on a Saturday. Vera was not there; the
number forwarded to Márcia's mobile, which she had not known until that day.

— This is Dona Iolanda's son. My mother's phone won't stop ringing. It's a
message from you. She's received — he paused, counting — thirteen hundred.
Thirteen hundred and something. Another one just arrived.

Márcia called Dedé. Dedé opened his laptop in the kitchen, in his pajamas,
and logged into the server.

```text
$ php artisan queue:failed
No failed jobs found.

$ tail -f storage/logs/laravel.log | grep NotifyUpcoming
... processing NotifyUpcomingReturn
... processing NotifyUpcomingReturn
... processing NotifyUpcomingReturn
```

— None failed — he said on the phone. — That's the problem. It's working.
Every time.

— Then stop it!

He stopped the worker. The messages stopped. The final count, on the
provider's dashboard, was 1,412.

On Monday, the investigation took twenty minutes. The job sent a notice for
each loan due the next day — three hundred or so — and only marked the work
as done at the end, after the last send. On Friday night, the provider got
slow, the job hit its time limit on send number 212, and the queue did what
it was configured to do: try again. From the beginning.

— How many attempts were configured? — asked Márcia.

Dedé opened the file.

— None. No limit.
:::

:::art caption="No job failed. That was the problem."
src="nenhum-job-falhou-esse-era-o-problema.png"
Minimalist editorial cartoon on a white background, composition split down
the middle. On the left, an elderly lady at home, in a bathrobe, holds with
both hands a phone that keeps vibrating, with notification bubbles stacked
one on top of another up to the ceiling and the number "1,412". On the
right, a developer in pajamas, at the kitchen table with a mug of coffee,
looks at a laptop where a closed circular arrow spins around the words "try
again". In the laptop's corner, a green check mark and the phrase "No failed
jobs". Few elements, dry humor, tech-magazine aesthetic.
:::

## What doesn't need to happen before the response

The `LoanService` from chapter @cap:services sends the notice to the reader
after committing the transaction. The send goes through the messaging
provider, which responds in three hundred milliseconds on a good day and in
eight seconds on a bad one.

On the bad days, Vera spends eight seconds looking at the screen, with the
reader in front of her, waiting for a confirmation that **has already
happened** — the loan has been recorded since the first millisecond. What is
missing is a WhatsApp message the reader does not even need to have
received to leave with the book.

The question that separates the work: **does whoever is waiting for this
need the result to continue?**

| Work | Does the waiter need it? | Where |
|---|---|---|
| recording the loan | yes, it is the operation | in the request |
| locking the copy | yes, otherwise it's another loan | in the request |
| notifying the reader | no | in the queue |
| updating "most borrowed" | no | in the queue |
| generating the PDF receipt | no, it arrives later | in the queue |

Table: The queue exists because waiting is expensive — the time of whoever
is at the counter, and the risk of a provider failure bringing down an
operation that had already succeeded.

## Event and listener: decoupling without hiding

Before the queue, a separation. The service, today, knows that after a loan
someone needs to be notified. Tomorrow, it also needs to update a counter.
After that, record it for the grant's accountability report. Each new need
is one more line in `create()`, and each line is one more dependency in the
constructor.

The alternative is for the service to **announce what happened** and let
the interested parties react:

```php title="app/Loans/Events/LoanCreated.php" numbered
final class LoanCreated implements ShouldDispatchAfterCommit
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public readonly Loan $loan,
    ) {}
}
```

```php title="app/Loans/LoanService.php" numbered
$loan = DB::transaction(function () use (/* ... */) {
    // ... the checks and the write ...

    LoanCreated::dispatch($loan);

    return $loan;
});
```

And whoever reacts:

```php title="app/Listeners/SendLoanReceipt.php" numbered
final class SendLoanReceipt implements ShouldQueue
{
    public function __construct(
        private readonly NoticeSender $notices,
    ) {}

    public function handle(LoanCreated $event): void
    {
        $l = $event->loan->load('reader', 'copy.book');

        $this->notices->send(
            $l->reader,
            sprintf(
                'You took "%s". Return it by %s.',
                $l->copy->book->title,
                $l->due_on->format('d/m'),
            ),
        );
    }
}
```

Laravel connects one to the other by the type of `handle`'s parameter —
whoever receives `LoanCreated` listens to `LoanCreated`. The `ShouldQueue`
on the listener sends the execution to the queue, and the service does not
wait for it.

:::pitfall
The event is dispatched **inside** the transaction. Without
`ShouldDispatchAfterCommit`, the listener goes to the queue immediately —
and the worker may pick it up **before** the `COMMIT` happens. It looks up
the loan by id and does not find it, because for the rest of the database
the row does not exist yet.

The defect is intermittent, depends on the worker's speed, and shows up as a
`ModelNotFoundException` in a job that "sometimes fails". The
`ShouldDispatchAfterCommit` interface holds the dispatch until the
transaction commits — and discards it if it is rolled back, which avoids
notifying about a loan that did not happen.
:::

The gain from the event is that the service no longer knows about the
notice. The cost is that whoever reads `create()` no longer sees, there,
everything that happens after a loan. The chapter's last section comes back
to that cost.

## Job: the unit of work that can fail and come back

Not all queue work is a reaction to an event. The "your book is due
tomorrow" notice is not triggered by anything that happened — it is
triggered by the calendar. For that there is the **job**, a class that
represents a piece of work to be done:

```text
$ php artisan make:job NotifyUpcomingReturn
```

```php title="app/Jobs/NotifyUpcomingReturn.php" numbered
final class NotifyUpcomingReturn implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly int $loanId,
    ) {}

    public function handle(NoticeSender $notices): void
    {
        $l = Loan::with('reader', 'copy.book')
            ->find($this->loanId);

        if ($l === null || $l->returned()) {
            return;
        }

        $notices->send($l->reader, sprintf(
            '"%s" is due tomorrow. Renew it in the app.',
            $l->copy->book->title,
        ));
    }
}
```

And what dispatches the jobs is a scheduled command, like `library:fines`
from chapter @cap:configuracao-ambiente-e-artisan:

```php title="routes/console.php" numbered
Schedule::call(function () {
    Loan::open()
        ->whereDate('due_on', today()->addDay())
        ->pluck('id')
        ->each(fn ($id) => NotifyUpcomingReturn::dispatch($id));
})->dailyAt('09:00')->name('return-notices');
```

Compare it with the job in the story. That was **one** job that went through
three hundred loans. This is **one job per loan**. The difference looks like
style and is what would have saved Dona Iolanda: when send number 212 fails,
only job 212 tries again. The 211 before it have already finished and do not
come back.

:::key
A job should be the **smallest unit of work that makes sense to repeat**.

A job that does three hundred things, when repeated, redoes the three
hundred. A job that does one, when repeated, redoes one.
:::

Notice also what the job receives: the **id**, not the model. `$l` is
fetched inside `handle`, at the moment the job runs — which may be seconds
or hours after the dispatch. If the reader returned the book in the
meantime, the job finds out and sends nothing.

## Queue driver: `sync`, `database`, `redis`

The queue needs to live somewhere between dispatch and execution. `.env`
chooses where:

```text
QUEUE_CONNECTION=database
```

**`sync`** is not a queue: it runs the job right away, inside the request.
It is the default in development and testing, and it hides every problem
that only exists when the job runs in another process.

**`database`** stores the jobs in a `jobs` table. It needs nothing beyond
the MySQL the project already has. It comfortably handles a neighborhood
library's volume — a few hundred jobs a day.

**`redis`** stores the jobs on a Redis server, in memory. It is faster and
handles much larger volumes, and it is one more piece to install, monitor
and maintain.

Casa Amarela uses `database`. The yardstick is the one in Tainá's notebook,
back in chapter @cap:o-que-vamos-construir: ask about size before choosing
the tool.

## Worker, supervisor and the process that needs restarting

Someone needs to take the jobs off the queue and run them. That is the
**worker**:

```text
$ php artisan queue:work --tries=3 --max-time=3600
```

It is a PHP process that does not end: it takes a job, runs it, takes the
next, forever. And that changes something the whole book has assumed until
now.

In a web request, PHP loads the code, serves and dies. Changing a file and
reloading the page is enough. The worker **loaded the code when it started**
and keeps that version in memory. A deploy that changes `NoticeSender`
changes nothing in the running worker — it keeps sending with yesterday's
code, until someone restarts it.

```text
$ php artisan queue:restart
```

That command does not restart anything directly. It writes a signal to the
cache, and each worker, on finishing its current job, checks the signal and
shuts itself down. For it to **come back**, you need a supervisor — an
operating system program whose job is to keep processes alive:

```ini title="/etc/supervisor/conf.d/casa-amarela.conf" numbered
[program:casa-amarela-worker]
directory=/var/www/casa-amarela
command=php artisan queue:work --tries=3 --max-time=3600
autostart=true
autorestart=true
user=www-data
numprocs=1
stopwaitsecs=120
```

`--max-time=3600` makes the worker shut itself down every hour, and the
supervisor brings it back up. That clears accumulated memory and guarantees
that, even if someone forgets `queue:restart`, the new code gets in within
an hour at most.

:::warning
A deploy without `queue:restart` is the most common defect for people
starting out with queues. The site shows the new version, the tests passed,
and the notices keep going out with the old text — or failing, because the
old code looks for a column today's migration renamed.

Chapter @cap:git-ci-e-deploy puts `queue:restart` in the deploy script, in an
order that is not by chance.
:::

## Retries, `backoff` and `failed_jobs`

A job that throws an exception goes back to the queue and is tried again.
How many times, and at what interval, is the job's decision:

```php title="app/Jobs/NotifyUpcomingReturn.php" numbered
public int $tries = 3;

public int $timeout = 30;

public function backoff(): array
{
    return [60, 300];
}

public function failed(Throwable $e): void
{
    Log::warning('return-notice-failed', [
        'loan' => $this->loanId,
        'error' => $e->getMessage(),
    ]);
}
```

Three attempts. The second one minute after the first, the third five
minutes after the second — giving the provider time to recover, instead of
insisting in the same second. `timeout` kills an attempt that goes past
thirty seconds.

After the third failure, the job goes to the `failed_jobs` table, with the
whole exception recorded, and `failed()` is called. It does not retry: it is
the place to log, alert someone, or mark in the database that the reader was
not notified.

```text
$ php artisan queue:failed
+----+----------------------+----------------------+
| ID | Job                  | Failed at            |
+----+----------------------+----------------------+
| 41 | NotifyUpcomingReturn | 2026-03-02 09:00:44  |
+----+----------------------+----------------------+

$ php artisan queue:retry 41
```

`queue:retry` puts the job back on the queue, after the problem has been
fixed. It is what makes a job's failure something manageable, and not a lost
message.

:::pitfall
The job in the story had no `$tries`. Without it, the worker uses the
command line's value — and if the command line has none either, retries are
**unlimited**. A job that always fails halfway runs forever, and if what it
does before failing is send a message, the message is sent forever.
:::

## A job needs to be idempotent

`$tries = 3` would limit the damage to three messages per person, and three
identical messages are still two too many. The underlying defect is not the
number of attempts. It is that **repeating the job repeats the effect**.

:::term Idempotent
An operation is idempotent when running it twice produces the same result
as running it once. The `DELETE` from chapter @cap:o-que-e-uma-api-rest is;
sending a message, by nature, is not.
:::

The queue **does not guarantee** a job runs only once. It guarantees it runs
**at least** once. A worker can die after sending the message and before
telling the queue it finished — and the queue, without that notice, delivers
the job again. No configuration eliminates that. The job is the one that
has to deal with the repetition.

The technique is to record the effect **in a way the second attempt can
discover** it already happened:

```php title="database/migrations/..._create_sent_notices.php" numbered
Schema::create('sent_notices', function (Blueprint $t) {
    $t->id();
    $t->foreignId('loan_id')->constrained();
    $t->string('type', 40);
    $t->date('refers_to');
    $t->timestamps();

    $t->unique(['loan_id', 'type', 'refers_to']);
});
```

```php title="app/Jobs/NotifyUpcomingReturn.php" numbered
public function handle(NoticeSender $notices): void
{
    $l = Loan::with('reader', 'copy.book')
        ->find($this->loanId);

    if ($l === null || $l->returned()) {
        return;
    }

    $record = SentNotice::firstOrCreate([
        'loan_id' => $l->id,
        'type' => 'upcoming-return',
        'refers_to' => $l->due_on->toDateString(),
    ]);

    if (!$record->wasRecentlyCreated) {
        return;
    }

    $notices->send($l->reader, /* ... */);
}
```

The `unique` in the database is the guarantee; `firstOrCreate` is the
question. If the record was just created, this is the first send. If it
already existed, a previous attempt got this far, and this one stops.

A small hole remains: if the worker dies **between** creating the record and
sending, the message does not go out, and the next attempt finds the record
and gives up. It is a conscious trade between two defects — no message,
rarely, or repeated messages. For a return reminder, the first failure is
tolerable. For a charge, perhaps not; and then the record gains a state —
`sending`, `sent` — and `failed()` resolves the ones left halfway.

:::key
The question every job needs to answer before going to production: **what
happens if it runs twice?**

If the answer is "nothing much", it is ready. If it is "the reader gets two
messages" or "the fine is charged twice", it is not.
:::

## When events become invisible spaghetti

One event with one listener is clear. The problem starts when listeners
dispatch events:

```text
LoanCreated
  → UpdateBookCounter
      → dispatches BookBecamePopular
          → RecalculateHighlights
              → dispatches HighlightsChanged
                  → ClearHomeCache
  → SendReceipt
  → RecordForAccountability
```

No file shows that tree. To know what happens after a loan, you have to look
for `LoanCreated`'s listeners, then the listeners of each event they
dispatch, and so on. A defect in `ClearHomeCache` appears to whoever
investigates as "the loan is sometimes slow", three levels away from the
cause.

Three rules keep events readable:

**A listener does not dispatch events.** It reacts and finishes. If the
reaction needs a second step, the second step is a job, called explicitly
by the listener.

**An event is a domain fact, in the past tense.** `LoanCreated`,
`CopyReturned`. Not `SendEmail` — that is an order, and an order is a job.

**The list of who listens fits in one lookup.** The
`php artisan event:list` command shows each event and its listeners. If its
output does not fit on one screen, it is time to talk.

:::story The v2
To find out how the 2009 Sistema sent the return reminder, Tainá looked in
the old server's `cron`. There was a single line, and it called
`php /home/casaamarela/public_html/notice.php`.

`notice.php` had twelve lines. The tenth included a file.

```php
include 'functions2_NEW_final_v2.php';
```

Tainá stared at the screen.

— Dedé.

— Hm.

— There's a `v2`.

He rolled his chair over to her desk and read it. Then he opened the folder.
There they were, side by side: `functions.php`, `functions2.php`,
`functions2_NEW_final.php` and `functions2_NEW_final_v2.php`. The last one
had been changed in March 2016 and had a single function,
`send_notice_email()`, which opened an SMTP connection to a server that had
not existed since 2019.

— So since 2019 nobody has received a return reminder — said Tainá.

— Since 2019.

— And nobody complained.

— Vera calls — said Dedé. — She has a list in her notebook. She calls
everyone the day before.

— Every day before?

— For five years.
:::

:::milestone
The work that does not fit in the request has left it. The loan responds
without waiting for the messaging provider; the notice goes out through a
queue with a supervised worker restarted on deploy; each job tries three
times, waits between attempts, ends up in `failed_jobs` when it can't — and
can run twice without sending two messages.

Vera can stop calling the day before.
:::

:::summary
- What goes to the queue is whatever the person waiting does not need in
  order to continue.
- An event announces a fact; a listener reacts; the service does not know
  who reacts.
- `ShouldDispatchAfterCommit` holds the event until the transaction
  commits.
- A job is the smallest unit of work that makes sense to repeat: one per
  loan, not one for all.
- A job receives the id and fetches the record when it runs.
- `sync` is not a queue; `database` is enough for small volumes; `redis`,
  for large ones.
- The worker keeps the code in memory: a deploy without `queue:restart` runs
  old code. A supervisor keeps it alive.
- `$tries`, `backoff` and `timeout` are the job's decisions; without
  `$tries`, retries can be infinite.
- The queue delivers at least once; the job needs to be idempotent, with the
  effect recorded under `unique`.
- A listener does not dispatch events; `event:list` needs to fit on one
  screen.
:::

:::checkpoint
The loan receipt and the day-before notice go out through the queue, after
the `COMMIT`, with one job per loan; the worker runs under a supervisor and
restarts on deploy; and you can explain what happens to a job that fails on
its third attempt — and why it can run twice without Dona Iolanda noticing.
:::

:::exercise level=1
Say whether each piece of work should happen in the request or in the
queue, and why:

1. Checking whether the reader has a fine above five reais.
2. Sending the notice that a reservation has become available.
3. Recording the return and freeing the copy.
4. Recalculating the month's most borrowed list.
5. Generating the PDF of the monthly accountability report.

:::answer
1. Request. It is a condition for the operation to happen, and needs to be
   inside the transaction.
2. Queue. The reader who returned the book does not need to wait for the
   notice to another person to go out.
3. Request. It is the operation.
4. Queue, dispatched by the loan or return event — or not even that:
   chapter @cap:cache-logs-e-medicao discusses whether it needs to be
   recalculated on every event.
5. Queue. It may take minutes. The request answers "the report is being
   generated", and a notice or link arrives when it is ready.
:::

:::exercise level=2
Write the `CopyReturned` event and the listener that notifies the first
reader in that book's reservation queue. The listener must go to the queue,
have three attempts, and be idempotent.

:::answer
```php title="app/Loans/Events/CopyReturned.php" numbered
final class CopyReturned implements ShouldDispatchAfterCommit
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public readonly Copy $copy,
    ) {}
}
```

```php title="app/Listeners/NotifyReservationAvailable.php" numbered
final class NotifyReservationAvailable implements ShouldQueue
{
    public int $tries = 3;

    public function __construct(
        private readonly NoticeSender $notices,
    ) {}

    public function handle(CopyReturned $event): void
    {
        $reservation = Reservation::active()
            ->where('book_id', $event->copy->book_id)
            ->oldest()
            ->first();

        if ($reservation === null) {
            return;
        }

        $marked = Reservation::whereKey($reservation->id)
            ->whereNull('notified_at')
            ->update(['notified_at' => now()]);

        if ($marked === 0) {
            return;
        }

        $this->notices->send(
            $reservation->reader,
            'The book you reserved is available.',
        );
    }
}
```

The idempotency comes from the `update` with `whereNull('notified_at')`: it
only marks if nobody has marked it, and returns how many rows it changed.
Two simultaneous runs cannot both change the same row — the database
guarantees it.

Notice that the reservation is looked up by **book**, not by copy, for the
same reason as `renew()` in chapter @cap:services.
:::

:::exercise level=3
After Dona Iolanda's incident, someone proposed: "let's drop the queue and go
back to sending the notices inside the scheduled command, in sequence, so it
doesn't repeat".

Respond to the proposal: what it really solves, what it makes worse, and
what you would show to defend the fixed queue.

:::answer
**What it solves.** Repetition through retries, yes: without a queue, there
is nobody to try again. And it is simpler to understand — one loop, from
start to finish.

**What it makes worse.**

A failure on send number 212 stops the whole command. Readers 213 to 300
receive nothing, and nobody finds out until someone complains — there is no
`failed_jobs`, no `queue:retry`.

The command takes the sum of all the sends. With a slow provider, that is
three hundred times eight seconds: forty minutes. If the scheduler runs the
command again before the first finishes, **it repeats** — which is the
defect the proposal wanted to avoid, coming back by another road. There is a
protection for that (`withoutOverlapping`), and someone has to remember to
add it.

And the repetition was not caused by the queue. It was caused by a job that
did three hundred things and did not record what it had already done. The
same loop, inside the command, rerun by a person after a failure halfway,
resends the first 211 all the same.

**What I would show.** The new job — one per loan, with `$tries`, `backoff`
and the `unique` record — and three tests: one that runs the job twice and
checks a single send; one that simulates a provider failure and checks the
entry in `failed_jobs`; and one that runs the schedule with three hundred
loans and checks three hundred jobs in the queue. The proposal fixed the
symptom; the tests show the cause was fixed.
:::
