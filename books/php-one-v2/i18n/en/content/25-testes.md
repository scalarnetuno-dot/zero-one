---
source_hash: a7ac311435dc
title: "Tests: what we are trying to prove"
number: 25
slug: testes
part: p7
kicker: "The fine for early returns had been fixed in October. In February, it came back by another path. There was a fix; there was no test."
goal: >-
  Write fast tests of the business rule, without a database and without
  HTTP: separate the decision from the query, cover the eleven conditions
  with a table of cases, choose the right test double, and turn each fixed
  defect into a test that stops it from coming back.
---

:::story Three days early
Dona Marlene returned *O Tempo e o Vento* three days before it was due, on a
Friday, through the drop box outside. On Monday, Neide recorded the drop
box's returns in the panel, entering the date the books had been left.

On Tuesday, Dona Marlene received a fine notice in the app for R$ 2.40.

— Three days of fines — said Vera, with Dona Marlene's phone in her hand —
for returning it three days early.

Dedé recognized the number before opening the code. So did Tainá.

— The unsigned `diff` — she said. — We fixed that. In October. I remember,
it was the `LoanPeriod` exercise.

— We fixed it in `LoanPeriod` — said Dedé, opening the new file. — This is
the drop box return recorder. Someone wrote the calculation again.

— Who?

Dedé looked at the history.

— Me. In January. In a hurry.

He read the snippet aloud:

```php
$days = $dueOn->diff($leftAt)->days;
$fine = $days * config('library.daily_fine_in_cents');
```

— And why didn't anything break when you wrote it? — asked Vera.

— Because there was nothing to break. October's fix was in the code. It
wasn't in any test.
:::

## A test does not prove it's right

There is an expectation about automated tests that makes them
disappointing: that they prove the code is correct. They don't. A test
checks **one case**, and the program has infinitely many.

What a test proves is more modest and more useful: **that a specific
behavior keeps happening**. Today, tomorrow, after anyone's next change.
October's fix was a behavior — "an early return generates no fine" — that
existed only in the memory of whoever fixed it. A test would have turned
that memory into something the pipeline checks on every commit.

:::key
A test is a sentence about the system, written in a way the computer can
check. "An early return generates no fine." If the sentence stops being
true, someone finds out **before** Dona Marlene does.
:::

The question that organizes this chapter and the next is not "how to test".
It is **what are we trying to prove** — and the answer to that question
decides what kind of test to write, and where.

## Pest or PHPUnit: pick one and stick with it

PHP has a dominant testing framework, PHPUnit, and Laravel comes with a
layer on top of it, Pest, which swaps classes and methods for functions:

```php title="tests/Unit/MoneyTest.php" numbered
<?php

use App\Loans\Money;

test('adds cents without losing precision', function () {
    $total = Money::inCents(10)
        ->plus(Money::inCents(20));

    expect($total->cents)->toBe(30);
});
```

The same thing in PHPUnit:

```php title="tests/Unit/MoneyTest.php" numbered
final class MoneyTest extends TestCase
{
    public function test_adds_cents_without_losing_precision(): void
    {
        $total = Money::inCents(10)
            ->plus(Money::inCents(20));

        $this->assertSame(30, $total->cents);
    }
}
```

Both run with the same command, produce the same report and test the same
thing. Pest is shorter and reads better, because the test's name is a
sentence in quotes. PHPUnit is what you will find in most older PHP code.

Casa Amarela uses Pest. The right choice is the one the project already
uses; the wrong one is mixing the two.

```text
$ php artisan test

   PASS  Tests\Unit\MoneyTest
  ✓ adds cents without losing precision                  0.01s

  Tests:    1 passed (1 assertions)
  Duration: 0.08s
```

## Arrange, act, assert

Every test has three parts, and it is worth writing them separated by a
blank line:

```php title="tests/Unit/LoanPeriodTest.php" numbered
test('an early return has no days late', function () {
    $period = new LoanPeriod(
        borrowedAt: new DateTimeImmutable('2026-02-02 10:00'),
        days: 14,
    );

    $days = $period->daysLate(
        new DateTimeImmutable('2026-02-13 18:00'),
    );

    expect($days)->toBe(0);
});
```

**Arrange**: set up the world the test happens in — the loan period, with
fixed dates.

**Act**: do **one** thing, the thing being tested.

**Assert**: check the result.

A test with two actions is testing two things, and when it fails, it will
not say which. A test without an assertion always passes, and is worse than
no test, because it gives a feeling of coverage.

Notice the dates. Fixed, written in the test. A test that uses `now()`
passes today and fails on the 31st of a month, or at the daylight saving
change, or when it runs near midnight — and each of those failures costs a
morning to understand. `LoanPeriod` has received the date from outside since
chapter @cap:enums-datas-e-valores, and this is why.

## Testing the rule without a database and without HTTP

The `LoanService` from chapter @cap:services has Vera's eleven conditions.
Testing it as it is requires a database: it fetches the copy, counts loans,
adds up fines. Each test would need to insert a book, a copy, a reader and
loans, and run inside a transaction. It works, and each test takes a hundred
milliseconds. With the fifty cases the eleven rules call for, that is five
seconds — and people stop running the suite before each commit.

But look at what the service does: it **queries** and then **decides**. The
query needs the database. The decision does not — it only needs the numbers
the query brought back. What is preventing the fast test is that the two
things are in the same method.

The separation:

```php title="app/Loans/RequestStatus.php" numbered
final readonly class RequestStatus
{
    public function __construct(
        public CopyStatus $copyStatus,
        public bool $isReference,
        public bool $inClosedCollection,
        public ?DateTimeImmutable $acquiredOn,
        public bool $lastAvailable,
        public bool $readerActive,
        public bool $readerIsChild,
        public int $openLoans,
        public int $overdueLoans,
        public Money $outstandingFine,
    ) {}
}
```

```php title="app/Loans/LendingPolicy.php" numbered
final class LendingPolicy
{
    public function __construct(
        private readonly CirculationRules $rules,
    ) {}

    public function requirePermitted(
        RequestStatus $s,
        DateTimeImmutable $when,
        ?Authorization $authorization,
    ): void {
        // the same guards as in the services chapter,
        // reading from $s instead of querying the database
    }
}
```

The service now has two steps: inside the transaction, it builds the
`RequestStatus` with the locked queries; then, it hands it to the policy,
which decides. The policy knows no database, no Eloquent, no HTTP. It
receives an object and a date, and throws an exception or doesn't.

:::key
Code that is hard to test is usually saying something about the design.
Here, it was saying that query and decision were mixed together.

The separation was not made **for** the test. It makes the rule clearer for
Vera to read, and the test became fast as a consequence.
:::

## The eleven conditions in under a second

With the decision isolated, a table of cases covers all the conditions.
Pest calls it a *dataset*:

```php title="tests/Unit/LendingPolicyTest.php" numbered
function requestStatus(array $change = []): RequestStatus
{
    return new RequestStatus(...array_merge([
        'copyStatus' => CopyStatus::Good,
        'isReference' => false,
        'inClosedCollection' => false,
        'acquiredOn' => new DateTimeImmutable('2020-01-01'),
        'lastAvailable' => false,
        'readerActive' => true,
        'readerIsChild' => false,
        'openLoans' => 0,
        'overdueLoans' => 0,
        'outstandingFine' => Money::zero(),
    ], $change));
}
```

The `requestStatus()` function builds a request **that passes**, and each
test changes only what matters. That is what makes the table readable: each
row says what is different from the normal case.

```php title="tests/Unit/LendingPolicyTest.php" numbered
test('refuses the request', function (
    array $change,
    string $exception,
) {
    $policy = new LendingPolicy(new CirculationRules());

    $policy->requirePermitted(
        requestStatus($change),
        new DateTimeImmutable('2026-03-10'),
        authorization: null,
    );
})->throws(DomainError::class)->with([
    'copy on loan' => [
        ['copyStatus' => CopyStatus::OnLoan],
        CopyUnavailable::class,
    ],
    'reference copy' => [
        ['isReference' => true],
        CopyDoesNotCirculate::class,
    ],
    'arrived three days ago' => [
        ['acquiredOn' => new DateTimeImmutable('2026-03-07')],
        CopyOnDisplay::class,
    ],
    'last one without authorization' => [
        ['lastAvailable' => true],
        LastCopyRequiresAuthorization::class,
    ],
    'reader with overdue loan' => [
        ['overdueLoans' => 1],
        ReaderHasOverdue::class,
    ],
    'fine of R$ 5.01' => [
        ['outstandingFine' => Money::inCents(501)],
        ReaderHasPendingItems::class,
    ],
    'three open in March' => [
        ['openLoans' => 3],
        LoanLimitReached::class,
    ],
    // ... and the others
]);
```

`throws` checks the parent class; to check each case's exact class, the test
body catches and compares — one more line, left to exercise 2.

And the **edges**, which is where rules go wrong:

```php title="tests/Unit/LendingPolicyTest.php" numbered
test('allows at the exact limit of each rule', function (
    array $change,
    string $when,
) {
    $policy = new LendingPolicy(new CirculationRules());

    $policy->requirePermitted(
        requestStatus($change),
        new DateTimeImmutable($when),
        authorization: null,
    );

    expect(true)->toBeTrue();
})->with([
    'fine of exactly R$ 5.00' => [
        ['outstandingFine' => Money::inCents(500)],
        '2026-03-10',
    ],
    'two open in March' => [
        ['openLoans' => 2], '2026-03-10',
    ],
    'four open in January' => [
        ['openLoans' => 4], '2026-01-15',
    ],
    'arrived exactly seven days ago' => [
        ['acquiredOn' => new DateTimeImmutable('2026-03-03')],
        '2026-03-10',
    ],
    'last one with authorization' => [
        ['lastAvailable' => true], '2026-03-10',
    ],
]);
```

"Above five reais" — R$ 5.00 passes, R$ 5.01 doesn't. "Three books" — two
pass, three don't. "A week on display" — is the seventh day the first on
which it goes out, or the last on which it doesn't? Vera answered: it goes
out on the eighth. The edge test is where the sentence's ambiguity becomes a
written decision.

:::pitfall
The last case on the list, "last one with authorization", is **wrong** as
written: it passes `authorization: null` in the call, like the others, and so
it should fail. The test will flag it on the first run.

It is on purpose, and it is a common defect in case tables: when one case
needs a parameter the others don't, the table needs another column. Without
it, the case's name promises one thing and the body tests another. Exercise
2 fixes it.
:::

```text
$ php artisan test --filter=LendingPolicy

   PASS  Tests\Unit\LendingPolicyTest
  ✓ refuses the request with (copy on loan)             0.01s
  ✓ refuses the request with (reference copy)
  ...
  ✗ allows at the exact limit of each rule with
    (last one with authorization)

  Tests:    1 failed, 22 passed (23 assertions)
  Duration: 0.14s
```

Twenty-three cases, fourteen hundredths of a second — and the red the
pitfall above promised. The time is the number that matters here: it is
what makes it possible to run the suite every time the file is saved.

## Test doubles: fake, stub, spy, mock

Not everything the code uses can be separated out like the policy.
`LoanService` uses `NoticeSender`, and the test should not send WhatsApp
messages. An object that replaces another in a test is called a **test
double**, and there are four kinds, which differ in what they know how to
do:

| Double | What it is | Example |
|---|---|---|
| stub | returns ready-made answers | a clock that always says 10 a.m. |
| fake | a simple real implementation | `FakeSender`, which stores in a list |
| spy | records calls to check later | `Log::spy()` |
| mock | expects specific calls, and fails if they don't come | `Mockery::mock()` |

Table: The names get mixed up in conversation and in documentation. The
distinction that matters is the last column: what the test checks
afterwards.

The `FakeSender` from chapter @cap:service-container is a fake. The test
checks the **result** — what ended up in the list:

```php
expect($fake->sent)->toHaveCount(1);
```

The same test with a mock checks the **call**:

```php
$mock = Mockery::mock(NoticeSender::class);
$mock->shouldReceive('send')
    ->once()
    ->with(
        Mockery::type(Reader::class),
        Mockery::pattern('/Return/'),
    );
```

Both test the same thing today. The difference shows up on the next change:
if someone swaps `send($reader, $text)` for
`send(new Notice($reader, $text))`, the mock breaks — it was tied to the
call's shape. The fake, if updated along with the interface, keeps checking
what matters: a notice was sent.

:::key
Prefer checking **what happened** to checking **how it happened**. A test
tied to the "how" breaks on every refactoring that changed nothing, and a
test that breaks for no reason teaches the team to ignore red tests.

The fake wins in most cases. The mock is the right tool when **the call is
the behavior** — "the payment system was called once and only once" is a
statement about the call.
:::

## Factory as fixture

The policy's unit tests needed no model at all. The ones that do — a test of
`ReaderResource`, a rule on the `Copy` model — can use the factories from
chapter @cap:migrations-seeders-e-factories **without a database**:

```php title="tests/Unit/CopyTest.php" numbered
test('a copy is on display until the seventh day', function () {
    $copy = Copy::factory()->make([
        'acquired_on' => '2026-03-03',
    ]);

    expect($copy->onDisplay(
        new DateTimeImmutable('2026-03-09'),
    ))->toBeTrue();

    expect($copy->onDisplay(
        new DateTimeImmutable('2026-03-11'),
    ))->toBeFalse();
});
```

`make()` builds the model with the factory's data and the data you passed,
**without saving**. `create()` saves. For a unit test, `make()`: it is
instant and does not depend on the database being up.

The factory delivers a copy that is plausible in every field, and the test
declares only what matters to it — the acquisition date. Whoever reads it
knows immediately what the test depends on.

## The test that reproduces yesterday's defect

The fix for Dona Marlene's fine has two parts, and the second is the one
that was not done in October.

The first is the code: the drop box return recorder stops calculating on its
own and starts using `LoanPeriod`, which is where the calculation lives.

The second is the test, written **before** the fix, to see it fail:

```php title="tests/Unit/DropBoxReturnTest.php" numbered
test('an early drop box return generates no fine', function () {
    // Dona Marlene's case, in February
    $rules = new CirculationRules();
    $period = new LoanPeriod(
        new DateTimeImmutable('2026-02-02 10:00'),
        14,
    );

    $fine = $rules->fineFor(
        $period,
        new DateTimeImmutable('2026-02-13 18:00'),
    );

    expect($fine)->toEqual(Money::zero());
});
```

```text
  ✗ an early drop box return generates no fine
  Failed asserting that Money(240) is equal to Money(0).
```

Red. That is what you want to see: the test reproduces the defect. Apply the
fix, and it goes green. From here on, Dona Marlene is protected by a line
that runs on every commit — and the comment in the test says where it came
from, so nobody deletes it thinking it is redundant.

:::note
Coverage — the percentage of lines of code some test executed — is a
**map**, not a grade. It shows where there are no tests at all, and that is
useful. It does not show whether the tests that exist check anything.

A project with a 90% coverage target tends to gain tests that execute
everything and assert nothing, written to hit the target. Casa Amarela has
no coverage target. It has a rule: **every fixed defect gets a test that
reproduces it**. Coverage rises on its own, and rises where the defects
were.
:::

:::note In your career
The interview question "do you write tests?" has an answer that works better
than "yes": telling about a defect that came back. Everyone who has worked
for a while has one. What the interviewer wants to hear is that you
understood why it came back — there was no test — and what you do
differently today: the test comes before the fix, and is written to fail
first.

And if the job is on a project with no tests at all, which is more common
than people admit, that same rule is the way to start without asking
permission: it doesn't take a dedicated week. It takes one test per fixed
defect, starting today.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Loans/
    RequestStatus.php             # what the query brought back
    LendingPolicy.php             # the decision, without a database
    LoanService.php               # queries, hands over, writes
  tests/Unit/
    MoneyTest.php
    LoanPeriodTest.php
    LendingPolicyTest.php         # eleven conditions, edges
    CopyTest.php
    DropBoxReturnTest.php         # Dona Marlene
  tests/Fakes/
    FakeSender.php
:::

:::summary
- A test does not prove the code is right; it proves a behavior keeps
  happening.
- Pest and PHPUnit do the same thing; the right choice is the project's, and
  they are not mixed.
- Arrange, act, assert: one action per test, and always an assertion.
- Fixed dates in tests; `now()` produces failures that depend on the day.
- Separating query from decision makes the rule testable without a database
  and clearer for whoever reads it.
- A dataset covers the conditions in a table; edge tests turn the
  sentence's ambiguity into a decision.
- A stub answers, a fake works, a spy records, a mock expects. Prefer
  checking the result over the call.
- `factory()->make()` builds without saving; it is what the unit test uses.
- Every fixed defect gets a test written before the fix, which fails first.
- Coverage is a map, not a target.
:::

:::checkpoint
The eleven lending conditions and each one's edges run in under a second,
without a database and without HTTP; the notice is checked with a fake; and
Dona Marlene's defect has a test that failed before the fix and passes after
it.
:::

:::exercise level=1
Each test below has a problem. Say which:

```php
// 1
test('calculates fine', function () {
    $rules = new CirculationRules();
    $rules->fineFor($period, now());
});

// 2
test('loan and return', function () {
    $l = $service->create(2117, 47);
    $service->returnLoan($l->id, now());
    expect($l->fresh()->returned())->toBeTrue();
});

// 3
test('children loan period', function () {
    $reader = Reader::factory()->create(['is_child' => true]);
    expect((new CirculationRules())->loanDaysFor($reader))
        ->toBe(7);
});
```

:::answer
1. It asserts nothing — it always passes. And it uses `now()`, so the
   result, if it were checked, would depend on the day.
2. It tests two actions. If it fails, it does not say whether the problem is
   in the loan or the return. They are two tests, and the return one
   arranges the loan without going through the service.
3. It uses `create()` in a test that does not need a database. `make()` is
   enough: the rule only reads the object's attribute. With `create()`, the
   test gets slower and starts failing if the test database is not up.
:::

:::exercise level=2
Fix the "allows at the exact limit" dataset so that the "last one with
authorization" case passes a real `Authorization` and the others keep
passing `null`. And, in the refusal test, check the **exact** class of each
case's exception, not only the parent.

:::answer
The dataset gains a third column, and the cases that don't need it pass
`null`:

```php
test('allows at the exact limit of each rule', function (
    array $change,
    string $when,
    ?Authorization $authorization,
) {
    $policy = new LendingPolicy(new CirculationRules());

    $policy->requirePermitted(
        requestStatus($change),
        new DateTimeImmutable($when),
        $authorization,
    );

    expect(true)->toBeTrue();
})->with([
    'fine of exactly R$ 5.00' => [
        ['outstandingFine' => Money::inCents(500)],
        '2026-03-10', null,
    ],
    // ...
    'last one with authorization' => [
        ['lastAvailable' => true],
        '2026-03-10',
        new Authorization(userId: 1, reason: 'school project'),
    ],
]);
```

And the refusal checks the exact class:

```php
test('refuses the request', function (array $change, string $expected) {
    $policy = new LendingPolicy(new CirculationRules());

    try {
        $policy->requirePermitted(
            requestStatus($change),
            new DateTimeImmutable('2026-03-10'),
            null,
        );
    } catch (DomainError $e) {
        expect($e)->toBeInstanceOf($expected);
        return;
    }

    $this->fail("Expected {$expected}, nothing was thrown");
})->with([ /* the same cases */ ]);
```

Without the exact check, a "reader with overdue loan" case that by mistake
threw `ReaderHasPendingItems` would pass — the parent is the same. It is the
kind of defect that only shows up when the screen shows "settle your fine"
to someone who owes nothing.
:::

:::exercise level=3
`LoanService::returnLoan()` records the return, calculates the fine, frees
the copy and dispatches `CopyReturned`. The team wants to test it.

Split what needs to be proven between unit tests (no database) and feature
tests with a database — the subject of the next chapter —, and justify each
choice. Also say what is **not** worth testing in this method.

:::answer
**Unit, without a database:**

The fine calculation at every edge: return on the day, one day late, early,
past the cap. That is already in `CirculationRules::fineFor`, and that is
where the test lives — not in the service.

The rule "a loan already returned cannot be returned again", if it is
extracted to the model or the policy. While it lives inside the service's
transaction, testing it requires a database.

**Feature, with a database:**

That the return records `returned_at` and the fine **and** frees the copy,
together — it is a statement about the transaction, and only the database
confirms it.

That a failure halfway rolls everything back: force an exception after
recording the return and check that the copy is still on loan.

That the `CopyReturned` event is dispatched **after** the commit — with
`Event::fake()` and a check that it does not go out when the transaction is
rolled back.

**What is not worth testing:**

That Laravel's `DB::transaction` works. That Eloquent's `update` saves. That
`findOrFail` throws when it finds nothing. That is framework code, already
tested by whoever wrote it; a test of it only checks that Laravel is
installed.

And testing again, in the feature test, each edge of the fine. One return
with a fine and one without are enough to prove the service calls the
calculation; the edges are already proven in the unit tests. Repeating them
makes the suite slow without proving anything new — which is the mistake
the next chapter opens by discussing.
:::
