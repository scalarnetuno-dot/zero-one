---
source_hash: 90fd81b7fe75
title: "Feature tests, HTTP and the database"
number: 26
slug: testes-de-feature-http-e-banco
part: p7
kicker: "The pipeline stayed red for three days on a test that passed on every local machine. An ORDER BY was missing — in the test and in the code."
goal: >-
  Verify the API's contract end to end and the guarantees only the database
  gives: real requests against real routes, a database isolated for every
  test, permissions proven from the refusal side, and infrastructure fakes
  that don't hide what they should be testing.
---

:::story Three days red
The pipeline went red on a Monday afternoon, on a test nobody had touched.

```text
FAILED  Tests\Feature\LoanListingTest
  > lists the reader's loans
  Failed asserting that '2117' is identical to '2118'.
```

Tainá ran it on her machine: green. Dedé ran it: green. Cléber ran it three
times in a row: green, green, green.

— It's the pipeline — said Cléber. — Must be the cache.

They cleared the pipeline's cache. Red. They ran it again without changing
anything. Green. Again. Red.

On Tuesday, someone suggested marking the test as "flaky" and moving on.
Tainá wouldn't let them, and couldn't explain why — she just felt that a
test that sometimes fails was trying to say something.

On Wednesday, she read the test line by line, with the listing code open
beside it.

```php
$this->getJson('/api/loans')
    ->assertJsonPath('data.0.copy.accession', 2117);
```

— Why does the first one have to be 2117? — she asked.

— Because it was the first one the test created — said Dedé.

— And the listing orders by what?

Dedé opened the controller. It ordered by `borrowed_at`, descending. And the
factory created the test's three loans in the same second.

— Three loans with the same date — said Tainá. — No tie-breaker.

— On our machines, MySQL returns them in insertion order.

— And on the pipeline?

— On the pipeline, MySQL runs with a different memory configuration.
:::

## `getJson`, `postJson` and the verified contract

The previous chapter tested the rule in isolation: a function receives
values and decides. But the isolated rule does not prove the API works.
Between the app's request and the lending policy there are the route, the
middleware, the Form Request, the policy, the service, the transaction, the
resource and the error handler — and any of them may be wired wrong.

A feature test walks the whole path. It sends a real request to the
application, with no web server in between, and checks the response:

```php title="tests/Feature/BookTest.php" numbered
test('creates a book and returns 201 with Location', function () {
    $clerk = User::factory()->clerk()->create();

    $response = $this->actingAs($clerk)
        ->postJson('/api/books', [
            'title' => 'Vidas Secas',
            'author' => 'Graciliano Ramos',
            'subject' => 'literature',
            'isbn' => '978-85-01-00032-5',
        ]);

    $response->assertCreated()
        ->assertHeader('Location')
        ->assertJsonPath('data.title', 'Vidas Secas')
        ->assertJsonPath('data.isbn', '9788501000325');
});
```

`postJson` builds the request with the JSON headers, hands it to Laravel's
kernel and returns the response as an object. The assertions that follow
check the **contract**: the status, the header, and two fields of the body —
one of them, the ISBN, already normalized by the `prepareForValidation` from
chapter @cap:validation-e-form-requests.

The most used assertions:

| Assertion | Checks |
|---|---|
| `assertCreated()`, `assertOk()`, `assertNoContent()` | the status |
| `assertJsonPath('data.title', 'x')` | one field, by path |
| `assertJsonStructure([...])` | that the keys exist |
| `assertJsonValidationErrors(['isbn'])` | the `422` and the guilty field |
| `assertJsonMissingPath('data.x')` | that a key is **not** there |

Table: The last one is the least used and the most important of the five. It
is what guarantees that what must not go out keeps not going out.

## `RefreshDatabase`: isolation without `TRUNCATE`

A feature test uses a real database. And each test needs to start with the
database in a known state, or one test's result depends on what another
left behind.

```php title="tests/Pest.php" numbered
pest()->extend(Tests\TestCase::class)
    ->use(Illuminate\Foundation\Testing\RefreshDatabase::class)
    ->in('Feature');
```

`RefreshDatabase` does two things. The first time the suite runs, it runs
all the migrations on an empty test database. After that, **each test runs
inside a transaction that is rolled back at the end**. Nothing the test
wrote survives it.

It is fast — rolling back a transaction costs almost nothing — and it has a
consequence: inside the test, everything happens in a single transaction.
`LoanService`'s `DB::transaction` becomes a **nested** transaction, and
Laravel simulates it with *savepoints*. It works for almost everything. It
does not work for testing two connections competing for the same row,
because both would see the same outer transaction.

The test database is **another database**, configured in `phpunit.xml`:

```xml title="phpunit.xml" numbered
<env name="APP_ENV" value="testing"/>
<env name="DB_DATABASE" value="casa_amarela_test"/>
<env name="QUEUE_CONNECTION" value="sync"/>
<env name="CACHE_STORE" value="array"/>
```

:::warning
`RefreshDatabase` wipes the database on the first run. If the test `.env`
points to the development database — or, like the Thursday in chapter
@cap:migrations-seeders-e-factories, to production's —, it wipes the wrong
database.

`phpunit.xml` with an explicit `DB_DATABASE` is the protection. And one more
check in `TestCase` is worth it: if the database name does not end in
`_test`, the test refuses to run.
:::

### In-memory SQLite, and where it lies

Many projects run their tests on in-memory SQLite, because it is faster and
needs no server:

```xml
<env name="DB_CONNECTION" value="sqlite"/>
<env name="DB_DATABASE" value=":memory:"/>
```

And SQLite is not MySQL. The differences that have already crossed this
book:

- the `utf8mb4_0900_ai_ci` collation from chapter
  @cap:paginacao-filtros-e-buscas does not exist; accent-free search passes
  on one and fails on the other;
- SQLite accepts text in an `INTEGER` column without complaining;
- `lockForUpdate` is ignored — there is no row locking;
- the length of `VARCHAR(200)` is not checked.

A test that passes on SQLite and fails on production MySQL is worse than a
slow test, because it gives the wrong certainty. Casa Amarela runs its tests
on **the same MySQL** as production, in the same version. The pipeline in
chapter @cap:git-ci-e-deploy starts a MySQL service for that, and it costs a
few seconds per run.

## `actingAs` and testing a protected route

The API's routes are behind `auth:sanctum`. The test does not need to log in
and keep a token:

```php
$this->actingAs($user)->getJson('/api/me');
```

`actingAs` tells Laravel the following requests come from that user. To test
the token's abilities, Sanctum has its own form:

```php
Sanctum::actingAs($user, ['view-catalog']);
```

And the test that the route **is** protected is the simplest of all, and
needs to exist for each group:

```php title="tests/Feature/ProtectionTest.php" numbered
test('reader routes require authentication', function (
    string $method,
    string $route,
) {
    $this->json($method, $route)->assertUnauthorized();
})->with([
    ['GET', '/api/me'],
    ['GET', '/api/loans'],
    ['POST', '/api/loans/1/renewal'],
    ['POST', '/api/reservations'],
]);
```

If someone moves a route out of the protected group, by mistake, while
rearranging the routes file, this test flags it.

## Testing `403` is testing what nobody tests by hand

Chapter @cap:autorizacao ended with two tests of Caio's case. The full suite
follows the same mold for each resource, and the mold has three questions:

1. Can the owner?
2. Can another user with the same role **not**?
3. Can staff?

```php title="tests/Feature/LoanAuthorizationTest.php" numbered
beforeEach(function () {
    $this->owner = User::factory()->reader()->create();
    $this->other = User::factory()->reader()->create();
    $this->clerk = User::factory()->clerk()->create();

    $this->loan = Loan::factory()
        ->for($this->owner->reader)
        ->create();
});

test('the owner sees their own loan', function () {
    $this->actingAs($this->owner)
        ->getJson("/api/loans/{$this->loan->id}")
        ->assertOk();
});

test('another reader does not', function () {
    $this->actingAs($this->other)
        ->getJson("/api/loans/{$this->loan->id}")
        ->assertForbidden();
});

test('a clerk does', function () {
    $this->actingAs($this->clerk)
        ->getJson("/api/loans/{$this->loan->id}")
        ->assertOk();
});
```

The second is the one that matters. The other two almost always pass,
because the happy path is what the person tested on screen while developing.
The second only passes if someone remembered to write the policy.

## The field that must never appear

Chapter @cap:api-resources promised a test for `internal_note`. It is short
and protects against a whole category of defect:

```php title="tests/Feature/InternalFieldsTest.php" numbered
test('the internal note never leaves through the API', function (
    string $route,
) {
    $reader = Reader::factory()->create([
        'internal_note' => 'TEST-SECRET',
    ]);
    $admin = User::factory()->admin()->create();

    $body = $this->actingAs($admin)
        ->getJson(str_replace('{id}', $reader->id, $route))
        ->assertOk()
        ->getContent();

    expect($body)->not->toContain('TEST-SECRET');
})->with([
    '/api/readers/{id}',
    '/api/readers?search=',
    '/api/readers/{id}/loans',
]);
```

Three design details.

The test uses the **admin**, who sees the most. If not even the admin gets
the note through the API, nobody does.

It looks for the **value**, not the key. `assertJsonMissingPath` would check
that there is no `internal_note` key, and would let through the day someone
exposed it under another name — `notes`, `memo`.

And the value is an unmistakable marker. Ordinary text like "returns it wet"
could appear for another reason; `TEST-SECRET` cannot.

## `assertDatabaseHas` and what it proves

The loan flow needs a test that checks the database, because the service's
promise is about the database — two writes, together:

```php title="tests/Feature/LoanFlowTest.php" numbered
test('a loan writes and locks the copy together', function () {
    $copy = Copy::factory()->available()->create();
    $reader = Reader::factory()->inGoodStanding()->create();
    $clerk = User::factory()->clerk()->create();

    $this->actingAs($clerk)
        ->postJson('/api/loans', [
            'copy_id' => $copy->id,
            'reader_id' => $reader->id,
        ])
        ->assertCreated();

    $this->assertDatabaseHas('loans', [
        'copy_id' => $copy->id,
        'reader_id' => $reader->id,
        'returned_at' => null,
    ]);

    expect($copy->fresh()->status)
        ->toBe(CopyStatus::OnLoan);
});
```

`assertDatabaseHas` looks for a row with those values. It proves the row
**exists**, and does not prove it is the only one — a defect that wrote the
loan twice would pass. When that matters, `assertDatabaseCount` completes
it.

And the rolled-back transaction test, which is the other side of the same
promise:

```php
test('an unavailable copy writes nothing', function () {
    $copy = Copy::factory()->onLoan()->create();
    $reader = Reader::factory()->inGoodStanding()->create();

    $this->actingAs(User::factory()->clerk()->create())
        ->postJson('/api/loans', [
            'copy_id' => $copy->id,
            'reader_id' => $reader->id,
        ])
        ->assertConflict()
        ->assertJsonPath('type', 'copy-unavailable');

    $this->assertDatabaseCount('loans', 1);
});
```

The `1` is the loan the `onLoan()` factory already created. No new one.

Notice what this test does **not** do: check the eleven conditions. They
were proven in the unit tests, in fourteen hundredths of a second. Here one
`409` is enough to prove the domain exception passes through the controller
and reaches the handler in the right format. Repeating the eleven here would
cost two seconds and prove nothing new.

## Faking queues, e-mail and events

The loan flow dispatches `LoanCreated`, which sends a job to the queue,
which calls the sender. The feature test wants to prove the first link, and
does not need to run the others:

```php
test('a loan announces the event', function () {
    Event::fake([LoanCreated::class]);

    // ... the loan POST ...

    Event::assertDispatched(
        LoanCreated::class,
        fn ($e) => $e->loan->reader_id === $reader->id,
    );
});
```

`Event::fake` swaps the event dispatcher for one that only takes notes.
There are siblings — `Queue::fake`, `Mail::fake`, `Notification::fake`,
`Storage::fake` —, and all follow the mold of the fake from chapter
@cap:testes: check what happened, without running it.

:::pitfall
`Queue::fake` checks that the job was **queued**. It does not run the job —
and that is why a job that would break on its first line passes every test
that uses the fake.

The suite needs at least one test that **really runs** each job, with the
fake sender injected:

```php
test('the day-before notice is sent only once', function () {
    $fake = new FakeSender();
    $this->app->instance(NoticeSender::class, $fake);
    $l = Loan::factory()->dueTomorrow()->create();

    (new NotifyUpcomingReturn($l->id))->handle($fake);
    (new NotifyUpcomingReturn($l->id))->handle($fake);

    expect($fake->sent)->toHaveCount(1);
});
```

It is Dona Iolanda's test: the job running twice, and a single message.
:::

## A slow suite: diagnose before blaming the database

Casa Amarela's suite has three hundred tests and takes forty seconds. Before
swapping MySQL for SQLite, the question from chapter
@cap:cache-logs-e-medicao: **where is the time?**

```text
$ php artisan test --profile

  Top 10 slowest tests:
  LoanListingTest > paginates 500 loans               8.21s
  ReportTest > full annual report                     6.03s
  ...
```

Two tests add up to fourteen of the forty seconds. The first creates five
hundred loans with the factory — each one creating its own reader, copy and
book, two thousand writes — to test pagination of twenty. With fifty loans
from the same reader, pagination is proven just the same.

After fixing the slow ones, what remains gets split up:

```text
$ php artisan test --parallel
```

`--parallel` runs the tests in several processes, each with its own test
database. On a machine with eight cores, forty seconds become eight.

:::key
How long can the suite take? The practical answer: **the time someone is
willing to wait before each commit**. Past that, people stop running it
locally, and the pipeline becomes the first place the tests run — which is
too late.

For a project the size of Casa Amarela, under a minute. The unit tests in
under a second, to run every time the file is saved.
:::

## Fixing the red pipeline

Back to the story: the test expected 2117 first because the person who wrote
it saw 2117 first on their machine. The listing ordered by `borrowed_at`,
and the test's three loans had the same value. Without a tie-breaker, their
order was the database's — and the database, on the pipeline, with a
different memory configuration, sometimes chose another.

The defect was **in both places**. The code needed the tie-breaker from
chapter @cap:paginacao-filtros-e-buscas — `orderByDesc('id')` after the date
—, because in production two loans in the same second happen every Saturday
morning. And the test needed to create the loans with different dates, to
assert the order the rule promises, and not the one the database happens to
produce.

The flaky test was right. It had been saying, three days running, that the
production listing had a defect.

:::note In your career
A flaky test — one that sometimes passes and sometimes fails with no change
in the code — is almost always a real defect, just one that depends on
order, timing or concurrency. They are the three things manual testing never
catches.

The common reaction is to mark the test as flaky, skip it, and move on. The
reaction that separates people who investigate from people who just ship is
Tainá's: suspect the test is trying to say something, and read it line by
line until you find out what. It takes an afternoon. The defect it hides
usually takes a week to find in production.
:::

:::tree title="Where we are now"
casa-amarela/
  phpunit.xml                      # _test database, sync queue
  tests/Pest.php                   # RefreshDatabase in Feature
  tests/Feature/
    ProtectionTest.php             # 401 for each route in the group
    BookTest.php                   # CRUD, 201, 422
    LoanFlowTest.php               # database, transaction, 409
    LoanAuthorizationTest.php      # owner, other, staff
    InternalFieldsTest.php         # TEST-SECRET
    NoticesTest.php                # jobs really run
:::

:::summary
- A feature test walks the whole path — route, middleware, Form Request,
  policy, service, resource, handler — without a web server.
- `assertJsonMissingPath` and searching for the value guarantee what must
  not go out.
- `RefreshDatabase` migrates once and rolls back each test in a
  transaction; the test database is a different one, declared in
  `phpunit.xml`.
- In-memory SQLite lacks MySQL's collation, locking and type checking; test
  on the production database.
- `actingAs` authenticates; the `401` test protects the route group.
- Permissions are proven from the refusal side: owner, another with the same
  role, staff.
- `assertDatabaseHas` proves it exists, not that it is unique.
- Don't repeat in feature tests what unit tests proved; one case per path is
  enough.
- Fakes check the dispatch; at least one test really runs each job.
- `--profile` before blaming the database; `--parallel` after.
- A flaky test is, almost always, an order, timing or concurrency defect.
:::

:::checkpoint
The feature suite covers the CRUD, the loan flow with the database, the
`422`s, each group's `401`s, the `403`s by role and by ownership, and the
internal field that never goes out — and runs in under a minute, on the same
MySQL as production, failing on the day the contract changes.
:::

:::exercise level=1
Say whether each statement should be tested in a unit test or a feature
test:

1. A fine of R$ 5.01 blocks a loan.
2. `POST /loans` without a token responds `401`.
3. `ReaderResource` does not expose the document to another reader.
4. `CirculationRules` gives a limit of five in January.
5. A return frees the copy in the same transaction.

:::answer
1. Unit, in `LendingPolicy`. In a feature test, at most one `409` case to
   prove the exception reaches the client.
2. Feature. It is a statement about the middleware and the routes file.
3. Feature, with two authenticated users. You can test the resource in
   isolation, but the real guarantee is that the route uses that resource.
4. Unit. It is pure.
5. Feature, with a database. It is a statement about the transaction.
:::

:::exercise level=2
Write the loan listing feature test that would have caught the story's
defect **deterministically** — failing always, and not sometimes, while the
tie-breaker does not exist.

:::answer
The trick is to create loans with the **same** date, on purpose, in a known
id order, and assert the order the rule promises:

```php
test('loans with the same date follow the tie-breaker', function () {
    $reader = User::factory()->reader()->create();
    $sameInstant = '2026-03-07 10:00:00';

    $ids = Loan::factory()
        ->count(5)
        ->for($reader->reader)
        ->create(['borrowed_at' => $sameInstant])
        ->pluck('id')
        ->sortDesc()
        ->values()
        ->all();

    $received = $this->actingAs($reader)
        ->getJson('/api/loans')
        ->assertOk()
        ->json('data.*.id');

    expect($received)->toBe($ids);
});
```

Without `orderByDesc('id')` in the listing, the order among the five depends
on the database, and the test fails on most runs instead of one in ten —
five ties are much harder to get right by chance than three.

The underlying lesson: the story's test was asserting **what was observed**.
This one asserts **what was promised** — the contract's order — and creates
on purpose the situation in which the promise is put to the test.
:::

:::exercise level=3
A new project you have taken over has six hundred feature tests, no unit
tests, and takes eleven minutes. The team only runs the tests on the
pipeline, and a commit takes fifteen minutes to be confirmed. The proposal on
the table is to swap MySQL for in-memory SQLite.

Write the plan, in order, with what you would measure and what you would do
at each stage. Say how you would respond to the SQLite proposal.

:::answer
**About SQLite, first.** It probably cuts the time in half and trades
certainty for speed: collation, row locking and types stop being tested. I
would not refuse it outright — I would ask whether the project uses any of
those things. If it uses accent-free search, `lockForUpdate` or depends on
strict column types, the answer is no.

**Stage 1: measure.** `--profile` to find the slowest. In suites like this,
it is common for a tenth of the tests to take half the time, almost always
because of factories creating hundreds of chained records for no reason.

**Stage 2: fix the slow ones.** Reduce data volume where volume is not what
is being tested; swap `create()` for `make()` where the database does not
matter; use a shared `seed` for reference data every test needs.

**Stage 3: parallelize.** `--parallel` on the pipeline and on machines. That
alone usually divides the time by the number of cores.

**Stage 4: move rules into unit tests.** The feature tests that test twenty
variations of the same rule through HTTP become one feature test — the path
— and a unit dataset — the variations. It is the slowest stage and the one
that cuts the most time, and it only makes sense after the rule has been
separated from the query, like `LendingPolicy`.

**What I would show at the meeting:** the before and after of each stage, in
minutes. The SQLite proposal was a solution; `--profile` is the diagnosis,
and it usually points to a cheaper cause with no loss.
:::
