---
source_hash: fa505c78eaba
title: "Enums, dates and value objects"
number: 23
slug: enums-datas-e-valores
part: p4
kicker: "Vera stayed until eleven closing the inventory. Seven readers woke up owing eighty cents."
goal: >-
  Close sets of options with `enum`, store dates with a time zone and
  without surprises using `DateTimeImmutable`, and give money a type with
  rules of its own instead of a loose integer.
---

:::story Eleven on a Tuesday night
February's inventory ran late, and Vera stayed until eleven recording the
pile of returns that had built up at the counter.

On Thursday, seven readers received a notice for an eighty-cent fine.

"They returned on time," said Vera. "I recorded everything on Tuesday."

Dedé opened the table.

```text
mysql> SELECT id, due_on, returned_at FROM loans
    ->  WHERE id IN (4471, 4472, 4473);
+------+------------+---------------------+
| id   | due_on     | returned_at         |
+------+------------+---------------------+
| 4471 | 2026-03-10 | 2026-03-11 02:03:11 |
| 4472 | 2026-03-10 | 2026-03-11 02:03:47 |
| 4473 | 2026-03-10 | 2026-03-11 02:04:12 |
+------+------------+---------------------+
```

"Two in the morning? I left at eleven."

"The server thinks it was two."

"Where is the server?"

Dedé checked the hosting configuration before answering, which was a good
idea.

"In Virginia."
:::

## A loose string is an `if` waiting for a typo

The project's `Copy` stores its status like this:

```php
private string $status = 'good';
```

The constructor checks the list, and that takes care of birth. But inside
the class, and anywhere that receives this value, `'good'` is just one
string among all possible strings:

```php
if ($copy->status() === 'on_laon') {
```

PHP accepts it. The type is right — it is a string. The condition is never
true, the block never runs, and nothing ever complains.

This is the hole left after three chapters of closing holes: the `string`
type says the format and does not say the **set**.

## `enum`: the set becomes a type

```php title="src/Catalog/CopyStatus.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Catalog;

enum CopyStatus: string
{
    case Good = 'good';
    case OnLoan = 'on_loan';
    case InRepair = 'in_repair';
    case Lost = 'lost';
}
```

Each `case` is a value, and there are only four. There is no fifth, there is
no way to invent one, and a typo no longer compiles:

```php
if ($copy->status() === CopyStatus::OnLaon) {
```

```text
Fatal error: Undefined constant CopyStatus::OnLaon
```

The `: string` after the name makes it a **backed enum**: each case carries
a text, which is what goes to the database.

| | When to use |
|---|---|
| `enum Status` (pure) | the set only exists inside the program |
| `enum Status: string` | the value needs to be stored or transmitted |

Table: When in doubt, backed. A pure enum that one day needs to go to the
database forces you to invent the conversion by hand, and that is where
someone stores the case's name instead of the value.

Three operations cover daily use:

```php
$status = CopyStatus::from('in_repair');
echo $status->name, ' / ', $status->value, "\n";
```

```text
InRepair / in_repair
```

`name` is the case's name in the code; `value` is the attached text. Both
exist, and mixing them up is the mistake in the next section.

```php
var_dump(CopyStatus::tryFrom('on_laon'));
```

```text
NULL
```

```php
CopyStatus::from('on_laon');
```

```text
Fatal error: Uncaught ValueError: "on_laon" is not a valid backing
value for enum CopyStatus
```

:::key
`from()` when the value **has** to be valid — it came from your own table,
and if it is not valid the database is corrupt and you want to know now.

`tryFrom()` when the value came from outside — a form, a search parameter,
the publisher's file. Then `null` is a possible answer, and the place to
handle it is input validation.

Swapping the two is the most common mistake with enums: `from()` on a URL
parameter turns a curious user into a fatal error.
:::

And `cases()` returns all of them, in the order they were written — which is
what builds a `<select>` without anyone repeating the list in the HTML:

```php
foreach (CopyStatus::cases() as $case) {
    echo $case->value, "\n";
}
```

## Behavior next to the option

An enum is not just a list. It accepts methods:

```php title="src/Catalog/CopyStatus.php" numbered
    public function isAvailable(): bool
    {
        return $this === self::Good;
    }

    public function label(): string
    {
        return match ($this) {
            self::Good => 'Available',
            self::OnLoan => 'On loan',
            self::InRepair => 'In repair',
            self::Lost => 'Lost',
        };
    }
```

```php
echo CopyStatus::InRepair->label(), "\n";
```

```text
In repair
```

The `match` here does a job the `if` does not: if someone adds a fifth case
to the enum and forgets about `label()`, the call with that case throws
`UnhandledMatchError` on the spot. The `if/else` would return the last
option silently.

:::key
Comparing enums is done with `===`, and it works because each case is a
unique object: there is **one** `CopyStatus::Good` in the whole program, and
every variable holding it points to it.

It is the same identity that got in the way when comparing two `Reader`s
loaded from the database, now working in your favor.
:::

## The enum in the database

Writing uses `value`; reading uses `tryFrom` or `from`:

```php title="src/Catalog/repository.php" numbered
$q = $pdo->prepare(
    'UPDATE copies SET status = ? WHERE accession = ?'
);

$q->execute([$status->value, $accession]);
```

```php
$status = CopyStatus::from($row['status']);
```

:::pitfall
Never store `$status->name`.

The `name` is the identifier in the code: `InRepair`, capitalized, written
in PHP. Renaming a case is a normal code change — and, the day someone
renames one, the database is left with thousands of rows pointing to a name
that no longer exists.

The `value` is the contract with the outside world. It does not change
because someone found a better name.
:::

## A date without a time zone is incomplete information

Casa Amarela's table stores `2026-03-11 02:03:11`. That is not a time: it is
a number waiting for someone to say where.

At eleven on Tuesday night in São Paulo, it is already two on Wednesday
morning on the server in Virginia. Both are right, and the report comparing
the return date with the due date is wrong by one day.

```php title="timezone.php" numbered
<?php

declare(strict_types=1);

$saoPaulo = new DateTimeZone('America/Sao_Paulo');

$returned = new DateTimeImmutable('2026-03-10 23:00:00', $saoPaulo);

$inUtc = $returned->setTimezone(new DateTimeZone('UTC'));

echo 'local: ', $returned->format('Y-m-d H:i T'), "\n";
echo 'utc:   ', $inUtc->format('Y-m-d H:i T'), "\n";
```

```text
local: 2026-03-10 23:00 -03
utc:   2026-03-11 02:00 UTC
```

It is the same instant, written two ways. Casa Amarela's bug was not the
server being in Virginia — it was the program storing a time without saying
where from, and then comparing that time with a São Paulo date.

:::key
The rule that avoids the whole class of problem, and that almost every
serious system follows:

**store in UTC, convert on display.** The database receives the instant in
UTC; the screen receives the time zone of whoever is looking.

Due dates, birthdays and holidays are different: they are dates without a
time, and converting time zones on them is what breaks them. `due_on` is a
`DATE` for that reason.
:::

:::art caption="For Vera it was eleven at night; for the server, two in the morning."
src="para-a-vera-eram-onze-da-noite-para-o-servidor-duas-da-manha.png"
Minimalist editorial cartoon on a white background, composition split by a
vertical dashed line. On the left, an older librarian locks the door of a
small neighborhood library under a lit street lamp, and a wall clock on the
front reads 11 p.m. On the right, very far away, a lonely rack server in a
cold warehouse, with a discreet sign reading "VIRGINIA" and a digital clock
showing 02:03. Between the two, a fine-notice envelope already flying
towards a mailbox. Few elements, dry humor, tech-magazine aesthetic.
:::

## `DateTimeImmutable`, and why the other one causes trouble

PHP has two date classes. One changes; the other does not.

```php title="mutable.php" numbered
<?php

$due = new DateTime('2026-03-10');
$notice = $due;

$notice->modify('+14 days');

echo $due->format('Y-m-d'), "\n";
```

```text
2026-03-24
```

`$due` changed, and nobody asked it to. `$notice = $due` copied nothing —
they are two variables with the same object, like any PHP object, and
`modify()` changed the original.

The immutable version answers the same call differently:

```php title="immutable.php" numbered
<?php

$due = new DateTimeImmutable('2026-03-10');
$notice = $due->add(new DateInterval('P14D'));

echo 'due:    ', $due->format('Y-m-d'), "\n";
echo 'notice: ', $notice->format('Y-m-d'), "\n";
```

```text
due:    2026-03-10
notice: 2026-03-24
```

`add()` changed nothing: it returned **another** object. Storing the result
stops being optional, and that is what makes the class safe to pass along.

`DateInterval` describes a duration with a short text: `P14D` is "a period of
fourteen days", `P1M` is one month, `PT2H` is two hours — the `T` separates
the date part from the time part.

:::pitfall
A function that receives a `DateTime` can modify the caller's date, and
nothing in the signature warns you.

```php
function dueDate(DateTime $borrowedAt): DateTime
{
    return $borrowedAt->modify('+14 days');
}
```

This function returns the due date **and** ruins the caller's
`$borrowedAt`. The bug shows up far away: on the line where someone prints
the borrow date and it is fourteen days in the future.

Use `DateTimeImmutable` in everything new. `DateTime` still exists because
PHP does not break old code, not because anyone recommends it.
:::

## Money is not a loose `int`

The project has stored fines in cents since chapter
@cap:conversao-automatica, and that decision is right. The problem is a
different one: `int` is everybody's type. An `int` of cents and an `int` of
days are the same type to PHP and to PHPStan.

```php
$total = $fineInCents + $daysLate;
```

That passes everything. It adds cents to days, returns an integer, and the
number reaches the receipt.

A **value object** closes that door:

```php title="src/Loans/Money.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Loans;

final class Money
{
    private function __construct(
        public readonly int $cents,
    ) {
        if ($cents < 0) {
            throw new \InvalidArgumentException('Negative amount');
        }
    }

    public static function inCents(int $cents): self
    {
        return new self($cents);
    }

    public static function zero(): self
    {
        return new self(0);
    }

    public function plus(self $other): self
    {
        return new self($this->cents + $other->cents);
    }

    public function times(int $factor): self
    {
        return new self($this->cents * $factor);
    }

    public function formatted(): string
    {
        $reais = $this->cents / 100;

        return 'R$ ' . number_format($reais, 2, ',', '.');
    }
}
```

```php
$fine = Money::inCents(80)->times(9);

echo $fine->formatted(), "\n";
```

```text
R$ 7,20
```

Three decisions, and each one pays a bill.

**The constructor is private**, and whoever creates it is `inCents()`. The
method's name states the unit — nobody is going to pass `7.20` thinking it
is reais, because there is no door that accepts reais.

**The methods return `self`**, a new object. Adding changes neither side,
exactly like the immutable date.

**Addition only accepts `Money`.** `$fine->plus($daysLate)` does not compile
— and that was the line the loose `int` let through.

:::term Value object
A type defined by what it is **worth**, not by which one it is: two `Money`
objects of 720 cents are interchangeable, and neither has an identity of
its own.

That is why it is born immutable and compared by content — unlike a
`Reader`, which has an `id` and is still the same person even when they
change their name.
:::

:::note In your career
"Too many types" is a criticism you will hear, and sometimes it is right.
The defense that works is not theoretical: it is showing the line that
stopped being possible.

For `Money`, the line is `$fine + $days`. For the enum, it is
`=== 'on_laon'`. For the immutable date, it is the function that changes
the caller's argument.

Bring the line. In code review, an example of a prevented bug is worth more
than any argument about design — and, if you cannot find the line, maybe the
type really does not need to exist yet.
:::

:::tree title="Where we are now"
catalog/
  src/
    Catalog/
      CopyStatus.php        # backed enum
      Copy.php              # stores CopyStatus, not string
      Book.php
      Classification.php
    Loans/
      LoanStatus.php        # enum
      Money.php             # value object, immutable
      Fine.php
    Circulation/
    Readers/
:::

:::milestone
End of Part 4. The project has declared contracts, errors with domain names,
types checked before running and values that refuse meaningless operations.
None of this is decoration: it is the exact list of things Laravel will
assume you already have.
:::

:::summary
- `string` says the format and not the set; `enum` says both.
- A backed enum (`enum X: string`) has `value` for the outside world and
  `name` for the code.
- `from()` for values that have to be valid; `tryFrom()` for values that came
  from outside.
- `cases()` returns the list; `match` inside the enum flags the new case
  instead of hiding it.
- Store `value` in the database, never `name`.
- A date without a time zone is a number: store the instant in UTC, convert
  on display.
- A due date is a `DATE`, with no time and no time zone.
- `DateTimeImmutable` returns a new object; `DateTime` changes the caller's,
  and nothing in the signature warns you.
- Cents in an `int` is still right — and a loose `int` adds up with any other
  `int`. A value object closes that door.
:::

:::checkpoint
You replace loose strings with backed enums, choose between `from` and
`tryFrom` by where the value came from, explain why Vera's return turned into
Wednesday, and write an immutable value object that refuses meaningless
operations.
:::

:::exercise level=1
Write `LoanStatus` as a backed enum, with the cases: open, returned, renewed
and overdue.

Then answer: why is "overdue" a problematic case on that list?

:::answer
```php title="src/Loans/LoanStatus.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Loans;

enum LoanStatus: string
{
    case Open = 'open';
    case Returned = 'returned';
    case Renewed = 'renewed';
    case Overdue = 'overdue';
}
```

"Overdue" is problematic because **it is not a stored state: it is a
conclusion**. A loan becomes overdue on its own, at midnight, without anyone
running anything — and a value stored in a column does not change on its
own.

Storing `overdue` forces someone to keep it up to date: a nightly task, a
trigger, a fix when the task fails. It is the `quantity` column again, in
different clothes.

The way out is to calculate: the loan is `Open`, and `isOverdue()` is a
method that compares `due_on` with today. Three cases on the list, and the
fourth piece of information is born right every time.
:::

:::exercise level=2
Write `LoanPeriod`, a value object that receives the borrow date and the
number of days, and knows how to answer:

- what the due date is;
- whether any given date is late relative to it;
- how many days late there are up to a date.

Use `DateTimeImmutable`. Watch out for the case where there is no delay.

:::answer
```php title="src/Loans/LoanPeriod.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Loans;

final class LoanPeriod
{
    public readonly \DateTimeImmutable $dueOn;

    public function __construct(
        public readonly \DateTimeImmutable $borrowedAt,
        public readonly int $days,
    ) {
        if ($days < 1) {
            throw new \InvalidArgumentException('Invalid period');
        }

        $this->dueOn = $borrowedAt->add(
            new \DateInterval("P{$days}D")
        );
    }

    public function isLateOn(\DateTimeImmutable $when): bool
    {
        return $when > $this->dueOn;
    }

    public function daysLate(\DateTimeImmutable $when): int
    {
        if (!$this->isLateOn($when)) {
            return 0;
        }

        return $this->dueOn->diff($when)->days;
    }
}
```

The care the question asks for is in `daysLate`: without the `if`, an early
return would give a positive number, because `diff()` has no sign — it
answers the distance, not the direction. A return three days early would
become three days of fine.

Two observations about the design. `$dueOn` is calculated in the
constructor and stored as `readonly`: it is a consequence of the other two
fields and will never diverge from them. And the three methods receive the
date from outside instead of calling `new DateTimeImmutable('now')` inside —
which makes the class testable without waiting for the sun to come up.
:::

:::exercise level=3
This report runs on the first of every month and charges the previous
month's fines. Find the three bugs related to this chapter and rewrite the
snippet.

```php title="billing.php" numbered
$loans = $pdo->query(
    "SELECT * FROM loans WHERE returned_at IS NOT NULL"
)->fetchAll();

$total = 0;

foreach ($loans as $l) {
    if ($l['status'] == 'late') {
        $days = (strtotime($l['returned_at'])
              - strtotime($l['due_on'])) / 86400;

        $total = $total + ($days * 0.8);
    }
}

echo "Total: R$ " . $total;
```

:::answer
**One: the string `'late'` with a loose comparison.** If the column stores
`overdue`, the condition is never true and the report charges zero — with no
error at all. With an enum, the value comes from `LoanStatus::tryFrom()` and
the comparison is by identity.

**Two: the date difference in seconds, divided by 86,400.** That ignores the
time zone and ignores that not every day has 86,400 seconds — daylight saving
change days have 82,800 or 90,000. The result is a `float` with decimal
places nobody asked for, and rounding decides the fine. `DateTimeImmutable`
and `diff()->days` answer in calendar days.

**Three: money in a `float`.** `$days * 0.8` accumulates error with each
addition, and the total printed at the end of a month with three hundred
fines does not match the sum of the individual notices. The math is in
cents, and the type is `Money`.

```php title="billing.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Loans\Money;
use CasaAmarela\Loans\LoanStatus;

$q = $pdo->prepare(
    'SELECT due_on, returned_at, status
       FROM loans
      WHERE returned_at IS NOT NULL
        AND status = ?'
);

$q->execute([LoanStatus::Returned->value]);

$utc = new DateTimeZone('UTC');
$total = Money::zero();

foreach ($q as $row) {
    $due = new DateTimeImmutable($row['due_on'], $utc);
    $back = new DateTimeImmutable($row['returned_at'], $utc);

    if ($back <= $due) {
        continue;
    }

    $days = $due->diff($back)->days;

    $total = $total->plus(Money::inCents(80)->times($days));
}

echo 'Total: ', $total->formatted(), "\n";
```

A fourth bug, as a bonus, which is not from this chapter but becomes visible
after the rewrite: the `SELECT *` became the list of the three columns used.
A report that reads the whole table every night gets slower with every
column someone adds, for a reason that has nothing to do with it.
:::
