---
source_hash: b1a701cf24e5
title: "Services: where the business rule lives"
number: 19
slug: services
part: p5
kicker: "Vera read the method aloud and corrected a rule the team had misunderstood for four months. It took eighteen seconds."
goal: >-
  Decide where each rule lives, take the loan rule out of the controller and
  put it in a service that is a transaction boundary and knows nothing about
  HTTP, and know how many layers the project really needs.
---

## An eight-hundred-line controller starts with twenty

The `LoanController::store` from chapter @cap:o-crud-completo had two rules
— copy available and per-reader limit — and fit on one screen. Since then:

- the Form Request took the validation out of it;
- the handler from chapter @cap:erros-padronizados took out building the
  error;
- the sender from the previous chapter added the notice.

And nine of Vera's eleven rules are still missing. If each one goes into
the controller, the method reaches a hundred and fifty lines before the end
of the part. The Blade panel, which also lends, has a copy. The
`library:fines` command, which needs to know whether a reader has pending
items, has a third version of one of the rules.

No controller is born with eight hundred lines. It gets there twenty lines
at a time, each one reasonable, and each one put there because it was the
place closest to where the person was editing.

:::key
The symptom is not the size. It is **the same rule in two places**. The
moment the panel and the API check the loan limit each in their own way, the
rule is already wrong in one of them — nobody just knows which.
:::

## A rule involving two entities does not fit in the model

The first attempt to take the rule out of the controller is usually the
model. It seems natural: the loan knows how to lend itself.

```php
class Loan extends Model
{
    public static function make(
        Copy $copy,
        Reader $reader,
    ): self {
        // ...
    }
}
```

Look at what "making a loan" needs to consult:

| Rule | Ask whom |
|---|---|
| copy available | `Copy` |
| not from the reference section | `Copy` |
| not the title's last copy | `Book`, counting `Copy` |
| limit of three | `Loan`, filtering by `Reader` |
| nothing overdue | `Loan`, filtering by `Reader` |
| fine above five reais | `Fine`, filtering by `Reader` |
| active reader | `Reader` |

Table: Seven of the eleven rules, and they cut across five entities. None of
them owns the operation.

`Loan::make` would need to know all the other models, and `Loan` would
become the place where the library's entire circulation rule lives. It is
the "giant model" from chapter @cap:eloquent, and it gets there by the same
path as the controller: one reasonable rule at a time.

The yardstick that works:

**A rule about a single entity stays in it.** "Is the copy available?" is a
question about the copy — `$copy->available()`. "Is the loan overdue?" is
about the loan — `$l->isOverdue()`.

**A rule that coordinates several entities goes to a service.** "Can this
reader take this copy now?" belongs to neither.

## The service

```php title="app/Loans/LoanService.php" numbered
<?php

declare(strict_types=1);

namespace App\Loans;

use App\Notices\NoticeSender;
use App\Models\Loan;
use App\Models\Copy;
use App\Models\Reader;
use Illuminate\Support\Facades\DB;

final class LoanService
{
    public function __construct(
        private readonly CirculationRules $rules,
        private readonly NoticeSender $notices,
    ) {}

    public function create(
        int $copyId,
        int $readerId,
        ?Authorization $authorization = null,
    ): Loan {
        $loan = DB::transaction(function () use (
            $copyId, $readerId, $authorization,
        ) {
            $copy = Copy::with('book')
                ->lockForUpdate()
                ->findOrFail($copyId);

            $reader = Reader::lockForUpdate()
                ->findOrFail($readerId);

            $this->requireLendableCopy(
                $copy, $authorization,
            );
            $this->requireReaderInGoodStanding($reader);

            $days = $this->rules->loanDaysFor($reader);

            $loan = Loan::create([
                'copy_id' => $copy->id,
                'reader_id' => $reader->id,
                'borrowed_at' => now(),
                'due_on' => now()->addDays($days),
                'authorized_by' => $authorization?->userId,
            ]);

            $copy->markOnLoan();

            return $loan;
        });

        $this->notices->send(
            $loan->reader,
            "Loan made. Return by "
                . $loan->due_on->format('d/m') . '.',
        );

        return $loan;
    }

    // ...
}
```

Three things to read carefully.

**The signature takes numbers, not a `Request`.** The service does not know
whether it was called by the API, by the panel, by the Artisan command or by
a test.

**The public method is the transaction.** Everything that needs to be true
together is inside the `DB::transaction`. The notice is **outside** — and
that is a decision: if the messaging provider goes down, the loan should not
be undone. The reader has the book in her hand.

**The checks have names.** `requireLendableCopy` and
`requireReaderInGoodStanding` are private methods that throw the domain
exceptions from chapter @cap:erros-padronizados:

```php title="app/Loans/LoanService.php" numbered
private function requireReaderInGoodStanding(Reader $reader): void
{
    if (!$reader->active()) {
        throw new ReaderInactive($reader->id);
    }

    if ($reader->loans()->overdue()->exists()) {
        throw new ReaderHasOverdue($reader->id);
    }

    $fine = $reader->outstandingFine();

    if ($fine->greaterThan($this->rules->maxFine())) {
        throw new ReaderHasPendingItems($reader->id, $fine);
    }

    $open = $reader->loans()->open()->count();
    $limit = $this->rules->limitFor($reader, now());

    if ($open >= $limit) {
        throw new LoanLimitReached(
            $reader->id, $limit, $open,
        );
    }
}
```

Each `if` is one of Vera's sentences. Read from top to bottom and it is
chapter @cap:condicionais, with guard clauses, no `else` at all.

And `CirculationRules` holds the numbers — loan period, limit, maximum fine
— that depend on configuration and the calendar:

```php title="app/Loans/CirculationRules.php" numbered
final class CirculationRules
{
    public function limitFor(
        Reader $reader,
        DateTimeInterface $when,
    ): int {
        return (int) $when->format('n') === 1
            ? config('library.limit_in_january')
            : config('library.limit_per_reader');
    }

    public function loanDaysFor(Reader $reader): int
    {
        return $reader->isChild()
            ? config('library.loan_days_children')
            : config('library.loan_days');
    }

    public function maxFine(): Money
    {
        return Money::inCents(500);
    }
}
```

It is pure — it receives what it needs, does not query the database, keeps
no state. It is what chapter @cap:testes will test in milliseconds.

:::story Eighteen seconds
Dedé projected `LoanService` on the meeting room wall. Vera had come to hand
in the month's paper cards and stayed at the door.

— Read it to me — she said.

— All of it?

— The copy part.

Dedé scrolled to `requireLendableCopy` and read it, translating the code
aloud:

— If it's not available, it doesn't go out. If it's from the reference
section, it doesn't go out. If it's from Seu Juvenal's collection, it
doesn't go out. If it arrived less than seven days ago, it doesn't go out.
If it's the title's last copy, it doesn't go out.

— Stop.

Dedé stopped.

— The last one isn't "doesn't go out". It's "goes out with authorization".
I authorize it, or Neide when I'm not here. If the person needs it for a
school project, it goes out.

Tainá opened her notebook to the first week's page. It said: *"last copy —
only w/ authoriz."*. She had written it down right. Someone, on the way
from the notebook to the code, had lost the second half of the sentence.

— Since when has it been like this? — asked Márcia.

— Since October — said Dedé. — Four months.

Vera was already leaving.

— And Dona Marlene?

— What about Dona Marlene?

— That's authorization too. I look at her and I authorize it.
:::

## The corrected rule, and the rule that wasn't a rule

Vera's correction fit in eighteen seconds because the rule fit on one
screen and was written in the order she thinks. In an eight-hundred-line
controller, with the rule split across three files, nobody would have read
it to her — and she would not have found it.

```php title="app/Loans/LoanService.php" numbered
private function requireLendableCopy(
    Copy $copy,
    ?Authorization $authorization,
): void {
    if (!$copy->available()) {
        throw new CopyUnavailable(
            $copy->accession, $copy->status,
        );
    }

    if ($copy->isReference() || $copy->inClosedCollection()) {
        throw new CopyDoesNotCirculate($copy->accession);
    }

    if ($copy->onDisplay(now())) {
        throw new CopyOnDisplay(
            $copy->accession, $copy->displayUntil(),
        );
    }

    if ($copy->book->lastAvailable($copy)
        && $authorization === null) {
        throw new LastCopyRequiresAuthorization(
            $copy->accession,
        );
    }
}
```

And Vera's second sentence solves a problem the team had carried since
chapter @cap:condicionais: Dona Marlene's rule. It was never a rule. It was
Vera **exercising judgment** — and judgment is not programmed, it is
recorded.

The `Authorization` object is that record:

```php title="app/Loans/Authorization.php" numbered
final readonly class Authorization
{
    public function __construct(
        public int $userId,
        public string $reason,
    ) {}
}
```

Who authorized it and why. It is stored on the loan (`authorized_by`), and
the end-of-month report can answer "how many loans went out through
authorization, and whose". Dona Marlene's exception became data, with a
name, and stopped being a counter legend.

:::key
Not every rule from the expert is a system rule. Some are **judgment** —
decisions the person makes looking at the case. Trying to program them
produces `if ($reader->name === 'Marlene')`.

The system does not need to make the judgment. It needs to **allow** it to
be exercised by whoever has authority and **record** that it was.
:::

## The service knows nothing about HTTP

With the service ready, the controller goes back to the size it should
have:

```php title="app/Http/Controllers/LoanController.php" numbered
public function store(
    CreateLoanRequest $request,
    LoanService $loans,
) {
    $loan = $loans->create(
        $request->integer('copy_id'),
        $request->integer('reader_id'),
    );

    return (new LoanResource($loan))
        ->response()
        ->setStatusCode(201)
        ->header(
            'Location',
            route('loans.show', $loan),
        );
}
```

The controller translates HTTP into a method call, and the method's result
into HTTP. The exceptions the service throws pass through the controller
untouched and reach the handler, which turns them into `409`.

The list of what the service **cannot** have:

- `Request` or `$request` anywhere;
- `abort()`, `response()`, HTTP statuses;
- `session()`, `redirect()`, `back()`;
- `auth()->user()` — who the user is is a parameter, not a lookup.

The last one is the most tempting. `auth()->user()` works inside the service
when it is called by the API, and returns `null` when it is called by the
Artisan command at three in the morning. The service starts depending on
being inside a request, and nobody notices until the command fails.

The Blade panel from chapter @cap:blade called a `LoanRecorder`, which was a
sketch of this. It now calls the same `LoanService` — and passes the
`Authorization` when Vera ticks the "authorized by me" box. The app's API
never passes one: the reader does not authorize themselves.

## One public method, one transaction

`renew()` and `returnLoan()` follow the same mold:

```php title="app/Loans/LoanService.php" numbered
public function returnLoan(
    int $loanId,
    DateTimeImmutable $when,
): Loan {
    return DB::transaction(function () use (
        $loanId, $when,
    ) {
        $loan = Loan::with('copy')
            ->lockForUpdate()
            ->findOrFail($loanId);

        if ($loan->returned()) {
            throw new LoanAlreadyReturned($loanId);
        }

        $fine = $this->rules->fineFor(
            $loan->period(), $when,
        );

        $loan->recordReturn($when, $fine);
        $loan->copy->markAvailable();

        return $loan;
    });
}
```

The `$when` comes from outside for the reason in chapter
@cap:enums-datas-e-valores: the caller decides what time it is. The API
passes `now()`; the test passes a fixed date; Vera, typing in on Monday the
returns from the weekend drop box, passes the date the book was left in the
box.

:::pitfall
`DB::transaction` inside a **private** method is the most common way of
breaking the boundary.

```php
public function returnMany(array $ids): void
{
    foreach ($ids as $id) {
        $this->returnOne($id); // transaction in there
    }
}
```

If the fifth fails, the first four have already been committed. Whoever
called `returnMany` receives an exception and does not know that half of it
happened. The rule: **the transaction belongs to the public method**,
because it is the one that promises a whole operation to the caller.
:::

## Repository: when it helps and when it's bureaucracy

In almost every PHP architecture tutorial an extra layer appears:

```php
interface LoanRepository
{
    public function find(int $id): ?Loan;
    public function save(Loan $l): void;
    public function openForReader(int $readerId): Collection;
}

class EloquentLoanRepository implements LoanRepository
{
    public function find(int $id): ?Loan
    {
        return Loan::find($id);
    }
    // ...
}
```

The promise is to isolate the database: the service talks to the
repository, and the repository can be swapped for another — another
database, another source, an in-memory implementation for tests.

In a Laravel project, that promise has to be weighed against what Eloquent
already is. The model **already is** a repository: `Loan::find`,
`Loan::open()`, `$l->save()`. The repository above is a file that passes
each method on to another, with an interface in front and a `bind` in the
provider.

**It helps when** the data source really can change — the collection that
today is in the database and tomorrow comes from a city hall API —, or when
the query is complicated enough to deserve its own name and test.

**It is bureaucracy when** it exists to "follow the architecture", in a
project with one database that is not going to change, and each method is a
line that calls Eloquent.

Casa Amarela has no repository. The scopes from chapter @cap:eloquent give
names to queries, and chapter @cap:testes shows how to test the rules
without needing a fake repository: by separating the pure rule from the
query.

## Not every project needs every layer

```text
Route → Controller → Service → Model → Database
```

Five layers. For Casa Amarela, each has a reason:

| Layer | Exists because |
|---|---|
| Controller | translates HTTP; there are two clients (API and panel) |
| Service | the rule cuts across five entities and three entry doors |
| Model | the data and the questions of a single entity |

Table: The question is not "what is the right architecture", it is "what
does each layer buy in this project".

And for the collection's CRUD routes? `BookController::store` receives the
Form Request and calls `Book::create`. No rule cuts across entities, there
is no second client, no transaction with two writes. A `BookService` with a
`create` method that calls `Book::create` would be a layer that only passes
things on — and would be the first thing the next section calls a symptom.

:::term Action class
An alternative to the service when it starts gathering unrelated
operations: one class per operation, with a single method.

`CreateLoan`, `RenewLoan`, `ReturnLoan` instead of a `LoanService` with the
three. It works better when each operation has different dependencies; it is
excess when all three share everything.
:::

## A service without a purpose: how to recognize it

Three signs, and one is enough:

**Every method has one line**, and the line calls the model. The service
does nothing the controller could not do directly.

**The name is a table's name** — `BookService`, `UserService` —, and the
methods are `create`, `update`, `delete`, `list`. It is the CRUD again, with
one more file.

**It receives a `Request`.** Then it is not a service; it is the controller
in another file.

`LoanService` passes all three: its methods coordinate several entities, the
name is a business operation's, and it does not know what HTTP is.

:::note In your career
Architecture in interviews tends to become a recited list of layers. What
impresses the person on the other side is the opposite: being able to say
**why not** to add a layer.

"I created a service for loans because the rule cuts across five entities
and three entry doors; I didn't create one for book registration because it
is one line of Eloquent, and a layer that only passes things on is cost
without benefit." That sentence shows judgment. "I always use Controller,
Service and Repository" shows you followed a tutorial.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Loans/
    LoanService.php             # create, renew, returnLoan
    CirculationRules.php        # pure: period, limit, fine
    Authorization.php           # judgment, recorded
    CopyDoesNotCirculate.php
    CopyOnDisplay.php
    LastCopyRequiresAuthorization.php
    ReaderInactive.php
    ReaderHasOverdue.php
    LoanAlreadyReturned.php
  app/Http/Controllers/
    LoanController.php          # translates HTTP, and that's all
:::

:::summary
- The symptom is not the controller's size; it is the same rule in two
  places.
- A single entity's rule stays in the model; a rule that coordinates
  several goes to a service.
- The service's public method is the transaction boundary; effects that
  should not undo the operation stay outside it.
- The service receives values, not a `Request`; it knows nothing of
  `abort`, sessions or `auth()`.
- Domain exceptions pass through the controller intact and the handler
  translates them.
- Some of the expert's rules are judgment: the system allows and records,
  it does not decide.
- `DB::transaction` in a private method breaks the public method's promise.
- A repository over Eloquent is pass-through, except when the data source
  really can change.
- Each layer needs a reason in the project; a simple CRUD does not need a
  service.
:::

:::checkpoint
The loan rule is in a service you can read aloud to someone who understands
the business, the transaction is the public method's, the controller only
translates HTTP, and you can justify, for each layer of the project, why it
exists — and why book registration has no service.
:::

:::exercise level=1
Say where each rule should live — in the model, in `CirculationRules`, in
`LoanService` or in the Form Request:

1. A copy is on display if it arrived less than seven days ago.
2. The loan limit is five in January and three the rest of the year.
3. `reader_id` must be an integer that exists in the table.
4. A reader with an overdue loan cannot take another book.
5. The loan period is seven days for child readers.

:::answer
1. The `Copy` model, in an `onDisplay($when)` method. It is a question about
   a single copy, and depends on its data.
2. `CirculationRules`. It is a number that depends on configuration and the
   calendar, not on a query.
3. Form Request. It is format, with one foot in the database.
4. `LoanService`. The question involves the reader and their loans, and
   must be asked inside the transaction.
5. `CirculationRules`, consulting `$reader->isChild()` — which in turn lives
   in the `Reader` model.

Item 5 shows the split in two: "is this reader a child?" is the model's
question; "what is the period for children?" is a circulation rule.
:::

:::exercise level=2
Write `LoanService`'s `renew()` with the rules: it only renews if not
overdue; at most two renewals; it does not renew if there is a reservation
for the book. The new date is counted from today, with the reader's loan
period.

:::answer
```php title="app/Loans/LoanService.php" numbered
public function renew(
    int $loanId,
    DateTimeImmutable $when,
): Loan {
    return DB::transaction(function () use (
        $loanId, $when,
    ) {
        $l = Loan::with(['reader', 'copy.book'])
            ->lockForUpdate()
            ->findOrFail($loanId);

        if ($l->returned()) {
            throw new LoanAlreadyReturned($l->id);
        }

        if ($l->isOverdue($when)) {
            throw new RenewalOfOverdue($l->id);
        }

        if ($l->renewals >= 2) {
            throw new RenewalsExhausted($l->id, 2);
        }

        if ($l->copy->book->hasActiveReservation()) {
            throw new BookReserved($l->copy->book_id);
        }

        $days = $this->rules->loanDaysFor($l->reader);

        $l->renewUntil($when->modify("+{$days} days"));

        return $l;
    });
}
```

The loose `2` deserves to move to `CirculationRules` the next time someone
passes by — Vera has already mentioned that during school holidays it is
three.

The reservation is checked on the **book**, not the copy: whoever reserves
wants "a *Dom Casmurro*", any one. Checking the copy would always allow the
renewal, because nobody reserves a specific accession number.
:::

:::exercise level=3
A project you have just taken over has this structure for author
registration:

```text
AuthorController → AuthorService → AuthorRepositoryInterface
                                 → EloquentAuthorRepository → Author
```

`AuthorService` has `list`, `find`, `create`, `update` and `delete`; each
calls the method of the same name on the repository, which calls Eloquent.
That is four files and a `bind` for a CRUD.

The person who wrote it argues that "it's the project's architecture" and
that "this way it's easy to switch databases". Write your position in the
review, including what you would **not** change now.

:::answer
**The position.** The two middle layers buy nothing in this case. The
service coordinates no entities, opens no transaction with two writes,
applies no rule; the repository passes on to Eloquent, which already is a
repository. They are two files and an interface that every change to author
registration has to go through, protecting nothing.

**About switching databases.** The database switch Laravel needs — MySQL to
PostgreSQL — Eloquent already does without a repository. The switch the
repository would allow — database to something else — is on nobody's
horizon, and if it is, it is cheaper to introduce the repository on that
day, for that entity, than to keep the layer on all of them on a
hypothesis.

**What I would not change now.** I would not rewrite the other modules that
follow the same pattern. "It's the project's architecture" is a real
argument: consistency has value, and a project with half its entities in one
pattern and half in another is harder to read than a whole project in one
excessive pattern.

The proposal I would take to the team is different: **for new code**, a
layer only when it has a written reason — "service because the rule cuts
across X and Y". The old pattern dies on its own, module by module, when
someone really needs to touch one of them.

And I would note down a question to ask in private, not in the review:
whether the pattern came from a decision with a reason I don't know.
Sometimes it did.
:::
