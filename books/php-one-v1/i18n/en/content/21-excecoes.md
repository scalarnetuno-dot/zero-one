---
source_hash: 9b07f231629f
title: "Exceptions"
number: 21
slug: excecoes
part: p4
kicker: "The nightly import never raised an error. It lost two hundred and fourteen rows a night, silently, for three months."
goal: >-
  Understand the difference between `Error` and `Exception`, catch by type
  instead of catching the whole world, create the domain's error vocabulary
  with attached data and preserve the original cause of a failure.
---

:::story It never raised an error
Every night, the System imported the file the partner publisher sent with
the month's new titles. Five years running, not one ticket opened.

Tainá went to check on a book Vera swore she had registered and could not
find it. She went to check the publisher's file: it was there.

She counted the lines in October's file. Then she counted the rows that had
made it into the database.

"Two hundred and fourteen are missing."

Dedé opened `publisher_import.php` and looked for the loop. Everything was
well written, indented, with variable names in Portuguese.

```php
    } catch (Exception $e) {
        continue;
    }
```

"How old is this?"

Tainá looked through the file's history. The line had been added on a
Friday in 2019, in a *commit* called *"fixes import error"*.

"Three years."

"And the error?"

"Fixed."
:::

## `Error`, `Exception` and the `Throwable` that covers both

PHP has two families of problem, and they tell you different things.

:::tree title="The hierarchy, simplified"
Throwable            # the interface catch understands
  Error              # a defect in the program
    TypeError
    ArgumentCountError
    DivisionByZeroError
  Exception          # a condition of the world
    LogicException   # your API was used wrong
      InvalidArgumentException
      DomainException
    RuntimeException # can only be known at run time
      PDOException
      UnexpectedValueException
:::

`Error` is what happens when the **program** is wrong: you called a method
on `null`, passed text where an integer went, divided by zero. It is not a
condition of the world, it is a defect, and defects are not handled — they
are fixed.

`Exception` is what happens when the **world** does not cooperate: the
database went down, the file did not arrive, the copy is already on loan.
The program is right, it is the situation that is adverse.

That separation has a practical consequence that catches almost everyone
once:

```php title="protected.php" numbered
<?php

try {
    $copy = null;
    $copy->lend();
} catch (Exception $e) {
    echo "handled\n";
}
```

```text
Fatal error: Uncaught Error:
Call to a member function lend() on null
```

The `catch` caught nothing. `Error` is not `Exception` — the two only meet
at the top, in `Throwable`.

:::key
`catch (Exception $e)` handles problems of the world and lets defects
through. That is the right behavior in most code: you want to know when you
called a method on `null`, you do not want to swallow it.
:::

## The `catch` that gets rid of the witness

The block in `publisher_import.php` has four lines and three defects.

```php
    } catch (Exception $e) {
        continue;
    }
```

**The first is the silence.** The `$e` variable was caught and thrown away.
Whoever wrote it had in hand the file, the line, the database's message and
the entire call stack — and threw it out.

**The second is the reach.** It handles any `Exception`: the duplicate
ISBN, which is expected, and the dropped database connection, which is not.
A night when MySQL does not come up produces an imported file with zero rows
and no complaint.

**The third is the outcome.** At the end, the program finishes
successfully. The exit code is zero, the scheduler shows green, and nobody
has a reason to look.

The version that tells the truth is not more complicated:

```php title="import.php" numbered
<?php

$saved = 0;
$rejected = [];

foreach ($rows as $number => $row) {
    try {
        save($pdo, $row);
        $saved++;
    } catch (InvalidRow $e) {
        $rejected[] = "row {$number}: {$e->getMessage()}";
    }
}

echo "saved: {$saved}\n";
echo 'rejected: ' . count($rejected) . "\n";

foreach ($rejected as $reason) {
    echo "  {$reason}\n";
}

exit($rejected === [] ? 0 : 1);
```

```text
saved: 1786
rejected: 214
  row 12: ISBN 9788525406958 already exists
  row 19: year missing
  ...
```

Two changes did the work. The `catch` started naming **one specific type**
— only the invalid row is tolerated; anything else goes up and brings the
program down, which is what you want when the database is down. And the
summary came out of silence: someone, at some point, reads "214 rejected"
and opens a ticket.

:::pitfall
`catch (\Throwable $e) { return false; }` is the most complete form of this
defect, because it swallows even `Error`s. A `TypeError` in one of your
lines becomes "returned false", and the program carries on as if it were a
normal business condition.

When you find one of these in a review, the question is not "why are you
catching?". It is: **what would you do if you knew what the error was?** If
the answer is "open a ticket", the `catch` is in the wrong place.
:::

## The domain's error vocabulary

`RuntimeException('Copy unavailable')` works, and it has a problem: whoever
catches it cannot do anything with it other than show the text.

To react, the code above would need to read the sentence — and sentences
change, gain accents, become plural, get translated.

An exception is a class. It can carry data:

```php title="src/Circulation/CopyUnavailable.php" numbered
<?php

namespace CasaAmarela\Circulation;

class CopyUnavailable extends \RuntimeException
{
    public function __construct(
        public readonly int $accession,
        public readonly string $status,
    ) {
        parent::__construct(
            "Copy {$accession} unavailable: {$status}"
        );
    }
}
```

`parent::__construct(...)` calls the constructor of the class above — here,
`RuntimeException`'s, which is the one that stores the message. The two
promoted properties are your addition.

Casa Amarela needs three:

| Exception | Carries | Who reacts |
|---|---|---|
| `CopyUnavailable` | accession, status | the screen offers a reservation |
| `LoanLimitReached` | limit, open | the screen lists what to return |
| `ReaderHasPendingItems` | readerId, fineInCents | the screen shows the amount |

Table: Three foreseeable situations, three types, and in none of them does
whoever catches need to read the message to decide what to do.

And using them is direct:

```php title="lend.php" numbered
try {
    lend($pdo, $accession, $readerId);
} catch (ReaderHasPendingItems $e) {
    $amount = number_format($e->fineInCents / 100, 2, ',', '.');
    echo "Settle R$ {$amount} before taking another book.\n";
} catch (CopyUnavailable $e) {
    echo "{$e->accession} is {$e->status}. Want to reserve it?\n";
}
```

:::key
The order of the `catch` blocks matters: PHP uses the **first one that
fits**. Most specific type first, most generic afterwards.

A `catch (\RuntimeException $e)` written before the three would never let
any of them be reached — and PHP does not warn you, because there is nothing
illegal about it.
:::

## `previous`: not losing the cause along the way

A failure usually crosses layers. The database refuses, the repository
translates, the screen shows — and at each translation there is a risk of
the original information disappearing.

The third argument of any exception's constructor is the **cause**:

```php title="lend.php" numbered
try {
    $q->execute([$copyId, $readerId]);
} catch (\PDOException $e) {
    throw new \RuntimeException(
        'Failed to record the loan',
        0,
        $e,
    );
}
```

If nobody handles it, PHP prints both, in the order they happened:

```text
Fatal error: Uncaught PDOException: SQLSTATE[HY000]: conn. refused
in /app/lend.php:8
Stack trace:
#0 /app/lend.php(14): lend()
#1 {main}

Next RuntimeException: Failed to record the loan
in /app/lend.php:10
Stack trace:
#0 /app/lend.php(14): lend()
#1 {main}
```

The first is the cause; the `Next` is the translation. Without the third
argument, the log would have only the second — and "failed to record the
loan" does not say whether the database went down, the table disappeared or
the password changed.

`getPrevious()` retrieves the cause in code, and it returns `null` when there
was none.

## `finally`: what needs to be given back

There is a block that **always** runs: when the `try` ends well, when an
exception goes up and even when there is a `return` in the middle.

```php title="lend.php" numbered
function lend(PDO $pdo, int $copyId, int $readerId): int
{
    $pdo->beginTransaction();

    try {
        // ... the SELECT FOR UPDATE, the INSERT and the UPDATE

        $pdo->commit();

        return $id;
    } catch (\PDOException $e) {
        $pdo->rollBack();

        throw new \RuntimeException('Loan failed', 0, $e);
    } finally {
        $pdo->exec('SET SESSION wait_timeout = DEFAULT');
    }
}
```

`finally` is the place to give back what was borrowed: an open file, a lock,
a changed session setting. It is not the place to handle the error — it is
the place to clear the table, whatever happens.

:::pitfall
A `return` inside `finally` **replaces** whatever the `try` was going to
return, and discards even an exception that was on its way up.

```php
function howMuch(): int
{
    try {
        throw new \RuntimeException('I broke');
    } finally {
        return 0;
    }
}
```

That function returns zero and the exception evaporates. It is the empty
`catch` again, disguised as tidying up.
:::

## When not to catch

Catching is the exception, not the rule. Three cases where the right thing
is to let it go up.

**When you are not going to do anything but pass it on.** A `catch` that
only writes to the log and does `throw` again has added noise and no
information.

**When the problem is a defect.** `TypeError`, `ArgumentCountError`, a
method called on `null` — handling these is hiding an error that needs to be
fixed in the code.

**When the situation is foreseeable and frequent.** Exceptions are expensive
and noisy. "The reader does not exist" in a search is not a failure: it is a
possible answer, and its place is a `null` or an empty list.

:::key
The rule: exceptions for what **interrupts** what was being done; a normal
return for what is **one of the possible answers**.

"I didn't find reader 913" is an answer. "The database didn't respond" is an
interruption.
:::

## The last safety net

In a program that serves people, an exception that reaches the top cannot
become a stack dump on the screen — it shows file paths, table names and
sometimes credentials.

```php title="import.php" numbered
set_exception_handler(function (\Throwable $e): void {
    error_log((string) $e);

    fwrite(STDERR, "The import failed. Contact support.\n");

    exit(1);
});
```

`set_exception_handler` registers what to do with whatever nobody handled.
The three lines of the body are the pattern: **log everything** where the
team looks, **show little** to whoever is in front of the screen, and **exit
with a non-zero code**, so the scheduler knows something went wrong.

:::note In your career
The night job's `catch (Exception $e) { continue; }` was not laziness.
Someone had an import breaking at three in the morning, an open ticket and a
Friday. The line resolved the ticket.

It is the most common shape of technical debt: the fix that works against
the exact symptom that was reported. It passes review because the report was
"the import is breaking" and the import stopped breaking.

What would have caught it in thirty seconds is a review question that costs
little and that you can always ask: **how will we know if this happens
again?** If the answer is "it won't raise an error", the fix erased the
warning, not the cause.
:::

:::tree title="Where we are now"
catalog/
  src/
    Circulation/
      Lendable.php
      RecordsHistory.php
      CopyUnavailable.php          # with accession and status
      LoanLimitReached.php         # with limit and open
      ReaderHasPendingItems.php    # with readerId and fine
    Catalog/
      Book.php
      Classification.php
      Copy.php
    Readers/
      Reader.php
    Loans/
      Fine.php
  import.php
  lend.php
:::

:::summary
- `Error` is a program defect; `Exception` is a condition of the world; both
  are `Throwable`.
- `catch (Exception)` does not catch `Error`, and that works in your favor.
- An empty `catch` erases the only witness of the failure and makes the
  program finish successfully.
- Catch the specific type; let the rest go up.
- An exception is a class: attach the data whoever catches it needs, instead
  of forcing them to read the message.
- The order of the `catch` blocks goes from most specific to most generic.
- The constructor's third argument stores the cause, and it shows up in the
  log as `Next`.
- `finally` gives resources back and should never contain a `return`.
- Exceptions for what interrupts; a normal return for what is one of the
  possible answers.
:::

:::checkpoint
You tell `Error` from `Exception`, recognize in code under review the
`catch` that erases information, write a family of domain exceptions with
attached data, chain the original cause and can point out three situations
where the right thing is not to catch.
:::

:::exercise level=1
For each situation, say whether it deserves an exception or a normal return
— and, when it is an exception, which of the two families.

1. The reader typed a document number that does not exist in the records.
2. The configuration file was not found at startup.
3. `lend()` received a negative accession number.
4. The query for books by subject found none.
5. MySQL refused the connection.

:::answer
1. **Normal return** — `null`. Not finding is one of the possible answers of
   a search.
2. **Exception**, `Exception` family (`RuntimeException`). The program is
   right, it is the world that does not have the file — and there is no way
   to carry on.
3. **Exception**, `Exception` family (`InvalidArgumentException`). It is
   wrong use of your function, detectable at the boundary. Note that if the
   type were violated — text where an `int` goes — it would be a
   `TypeError`, `Error` family, and it is not you who throws it.
4. **Normal return** — an empty list. Zero results is a result, and
   `count()` of an empty array is zero, which already takes care of the
   screen.
5. **Exception**, `Exception` family (`PDOException`, which comes ready-made).

The pattern that shows up across the five: a search that finds nothing
returns empty; something that stops the work from continuing throws.
:::

:::exercise level=2
Write `LoanLimitReached` with the attached data and adjust the lending
function to throw it.

Vera's rule: three books per reader, five in January.

Then write the `catch` that produces the final message for the front desk,
using the exception's data and not its message.

:::answer
```php title="src/Circulation/LoanLimitReached.php" numbered
<?php

namespace CasaAmarela\Circulation;

class LoanLimitReached extends \RuntimeException
{
    public function __construct(
        public readonly int $readerId,
        public readonly int $limit,
        public readonly int $open,
    ) {
        parent::__construct(
            "Reader {$readerId} has {$open} of {$limit}"
        );
    }
}
```

```php title="lend.php" numbered
$limit = (int) date('n') === 1 ? 5 : 3;

$open = (int) $pdo->query(
    'SELECT COUNT(*) FROM loans
     WHERE reader_id = ' . $readerId . ' AND returned_at IS NULL'
)->fetchColumn();

if ($open >= $limit) {
    throw new LoanLimitReached(
        $readerId,
        $limit,
        $open,
    );
}
```

```php
} catch (LoanLimitReached $e) {
    echo "Limit of {$e->limit} books reached. ";
    echo "Return 1 of the {$e->open} to take another.\n";
}
```

A note about the query: it is concatenating `$readerId`. Since the value came
from an `(int)`, it is safe — but safe by accident, and an accident is not a
policy. A prepared statement is the way for safety not to depend on someone
remembering the `(int)` in the next change.

And notice what the front-desk message does **not** use:
`$e->getMessage()`. The sentence "Reader 913 has 3 of 3" is for the log.
For the person in the queue, the screen builds its own sentence, with the
same numbers.
:::

:::exercise level=3
This code runs every night and has never complained. Find the four problems
and rewrite it.

```php title="sync.php" numbered
<?php

$file = fopen('/tmp/publisher.csv', 'r');

try {
    while (($row = fgetcsv($file)) !== false) {
        try {
            save($pdo, $row);
        } catch (Throwable $e) {
            file_put_contents(
                '/tmp/errors.log',
                $e->getMessage(),
                FILE_APPEND,
            );
        }
    }
} catch (Exception $e) {
    echo "error\n";
}

fclose($file);
```

:::answer
**One: the inner `catch (Throwable)` swallows defects.** If `save()` has a
`TypeError`, every row fails the same way and the program finishes fine. The
caught type needs to be the invalid-row one, and only that.

**Two: the log keeps only the message.** `$e->getMessage()` discards the
type, the file, the line and the chained cause. `(string) $e` keeps
everything, and `error_log()` sends it where the team already looks, instead
of a file in `/tmp` nobody opens.

**Three: nothing counts.** There is no total saved, no total rejected and no
exit code. Without numbers, the difference between a perfect night and a
night that lost two hundred rows is invisible.

**Four: the `fclose` does not always happen.** If the `while` throws
something the `catch (Exception)` does not catch — an `Error`, for example —
the program dies with the file open. The place for `fclose` is a `finally`.

```php title="sync.php" numbered
<?php

$file = fopen('/tmp/publisher.csv', 'r');

if ($file === false) {
    throw new RuntimeException("The publisher's CSV didn't arrive");
}

$saved = 0;
$rejected = [];

try {
    while (($row = fgetcsv($file)) !== false) {
        try {
            save($pdo, $row);
            $saved++;
        } catch (InvalidRow $e) {
            $rejected[] = $e->getMessage();
            error_log((string) $e);
        }
    }
} finally {
    fclose($file);
}

echo "saved: {$saved}, rejected: ", count($rejected), "\n";

exit($rejected === [] ? 0 : 1);
```

The outer `catch (Exception)` disappeared entirely, and that is the best
part of the change: there was nothing useful to do there. Any failure other
than an invalid row now brings the program down with the full message —
which is exactly what you want at three in the morning.
:::
