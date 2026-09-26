---
source_hash: b354432f96ad
title: "Dates and times"
number: 27
slug: datas-e-horarios
part: p5
kicker: "The Sunday bug was four years old. The fix was nine lines long. The fix's test failed after nine at night."
goal: >-
  Calculate a due date that never falls on a closed day, count days late
  without being thrown off by the time of day, treat "now" as a dependency
  you pass in and swap in tests, do month arithmetic without landing on the
  31st, and read the date a person types.
---

:::story The Sunday bug
In the first week of the project, Vera had listed the System's bugs without
taking her eyes off the label she was sticking on: "when someone returns a
book on Sunday, it charges a fine, and we're not even open on Sunday". For
four years.

Tainá took the bug for herself.

"The loan period is fourteen days," Vera explained. "If the fourteenth falls
on a Sunday, the person can only return it on Monday. And the System charges
for Monday. One day of fine, every time. I pay the money back out of my own
pocket when people complain."

"Out of your own pocket?"

"It's faster than explaining."

Tainá wrote the fix, wrote the test, and the test passed. At ten thirty at
night, running everything again before opening the review request, the same
test failed.

```text
A loan due today should not be overdue.
Expected: false. Got: true.
```

She ran it again. It failed. The next morning, it passed.

"I didn't touch anything," she told Dedé.

"You didn't. The clock did."
:::

## The due date that never falls on a closed day

Chapter @cap:enums-datas-e-valores left three rules: dates with a time zone,
`DateTimeImmutable` always, and UTC in the database with conversion on the
screen. This chapter uses all three and adds what is missing to calculate a
real due date.

Vera's rule, written down:

```php title="due.php" numbered
<?php

declare(strict_types=1);

const SUNDAY = 7;

function nextOpenDay(
    DateTimeImmutable $day,
    array $holidays,
): DateTimeImmutable {
    while (
        (int) $day->format('N') === SUNDAY
        || in_array($day->format('Y-m-d'), $holidays, true)
    ) {
        $day = $day->modify('+1 day');
    }
    return $day;
}

$holidays = ['2026-04-03', '2026-04-21'];
$tz = new DateTimeZone('America/Sao_Paulo');

foreach (['2026-03-22', '2026-04-03', '2026-04-21'] as $date) {
    $due = new DateTimeImmutable($date, $tz);
    $open = nextOpenDay($due, $holidays);
    echo $due->format('D d/m'), ' -> ';
    echo $open->format('D d/m'), "\n";
}
```

```text
$ php due.php
Sun 22/03 -> Mon 23/03
Fri 03/04 -> Sat 04/04
Tue 21/04 -> Wed 22/04
```

`format('N')` returns the day of the week as a number, from 1, Monday, to 7,
Sunday. The `while`, and not an `if`, is what handles the holiday that falls
on the Saturday before a Sunday: the loop walks forward until it finds an
open day, however many closed ones come in a row.

The holidays are in an array because they change every year and each city
has its own. In volume 2, they go into a table, and Vera enters the year's
holidays in January.

## Days late, without the time of day in the middle

The due date is a **date**: the 24th. The return is an **instant**: the
27th, at 9:15. Subtracting one from the other directly mixes the two, and
the result changes with the time the book reached the counter.

```php title="late.php" numbered
<?php

declare(strict_types=1);

function daysLate(
    DateTimeImmutable $due,
    DateTimeImmutable $returnedAt,
): int {
    $day = $returnedAt->setTimezone($due->getTimezone())
        ->setTime(0, 0);
    $interval = $due->diff($day);

    return $interval->invert === 1 ? 0 : $interval->days;
}

$tz = new DateTimeZone('America/Sao_Paulo');
$due = new DateTimeImmutable('2026-03-24', $tz);

foreach (['2026-03-20 15:00', '2026-03-24 17:50',
          '2026-03-27 09:15'] as $when) {
    $returned = new DateTimeImmutable($when, $tz);
    echo $when, ': ', daysLate($due, $returned), "\n";
}

$utc = new DateTimeImmutable(
    '2026-03-25 01:30',
    new DateTimeZone('UTC'),
);
echo 'utc 25/03 01:30: ', daysLate($due, $utc), "\n";
```

```text
$ php late.php
2026-03-20 15:00: 0
2026-03-24 17:50: 0
2026-03-27 09:15: 3
utc 25/03 01:30: 0
```

Three steps, each for a reason.

**`setTimezone` before anything.** The last line is the same return the
database would store in UTC: 1:30 on the 25th in UTC is 10:30 p.m. on the
24th in São Paulo. Within the period. Without the conversion, it would be a
day's fine for someone who returned on time.

**`setTime(0, 0)`** erases the time and leaves only the day. It is what makes
the 5:50 p.m. return on the 24th count as "the 24th", and not "the 24th and
seventeen hours after the due date".

**`diff`** returns a `DateInterval`. `days` is the total number of days
between the two dates, always positive; `invert` is `1` when the second date
is **earlier** than the first — when the book came back before the due
date.

:::key
Due date, birthday, holiday: **date**. Borrowing, return, payment:
**instant**. Before comparing one with the other, convert the instant to the
date's time zone and throw away the time. Most "one extra day" bugs in
Brazilian systems are born from skipping one of those two steps.
:::

## "Now" is a dependency

Back to the test that failed at night. The version Tainá had written asked
PHP what day it was:

```php
public function isOverdue(): bool
{
    $today = new DateTimeImmutable('today');
    return $today > $this->dueOn;
}
```

Two problems in one line.

**The time zone.** `new DateTimeImmutable('today')` without a time zone uses
PHP's default time zone, and in Vertexo's test container it was the factory
default:

```text
$ php -r 'echo date_default_timezone_get();'
UTC
```

At 9 p.m. in São Paulo, it is already midnight in UTC. From then on, "today"
to PHP is the next day, and the loan due today shows up as overdue. In the
morning, the two time zones agree again and the test passes.

**The clock.** Even with the right time zone, the test depends on the time
it runs. A test that gives a different result depending on the time proves
nothing — and a method that says "today" inside itself does not let any test
choose the time.

The way out is the same as in chapter @cap:heranca-interfaces-e-traits for
everything that comes from outside: an interface, and whoever needs it
receives it through the constructor.

```php title="clock.php" numbered
<?php

declare(strict_types=1);

interface Clock
{
    public function now(): DateTimeImmutable;
}

final class SystemClock implements Clock
{
    public function __construct(private DateTimeZone $tz)
    {
    }

    public function now(): DateTimeImmutable
    {
        return new DateTimeImmutable('now', $this->tz);
    }
}

final class FrozenClock implements Clock
{
    public function __construct(private DateTimeImmutable $instant)
    {
    }

    public function now(): DateTimeImmutable
    {
        return $this->instant;
    }
}
```

The live system uses the `SystemClock`, with the São Paulo time zone coming
from configuration. The test uses the `FrozenClock`, and chooses the time:

```php title="clock.php (continued)" numbered
final class Loan
{
    public function __construct(
        private DateTimeImmutable $dueOn,
        private Clock $clock,
    ) {
    }

    public function isOverdue(): bool
    {
        $today = $this->clock->now()->setTime(0, 0);
        return $today > $this->dueOn;
    }
}

$tz = new DateTimeZone('America/Sao_Paulo');
$due = new DateTimeImmutable('2026-03-24', $tz);

$night = new FrozenClock(
    new DateTimeImmutable('2026-03-24 22:30', $tz),
);
$after = new FrozenClock(
    new DateTimeImmutable('2026-03-25 08:00', $tz),
);

var_dump((new Loan($due, $night))->isOverdue());
var_dump((new Loan($due, $after))->isOverdue());
```

```text
bool(false)
bool(true)
```

Now the ten-thirty-at-night test runs at ten thirty at night on any day,
including at nine in the morning.

:::term Injected clock
"Now" treated as a dependency: an object that answers what time it is,
received through the constructor. In the system, it asks the operating
system; in the test, it always answers the same instant.

The idea is so common that it became a PHP community standard — PSR-20,
with the `ClockInterface` interface and a single method, `now()`. It is the
same interface as in this chapter.
:::

The default time zone also has a fix, in PHP's configuration or at the start
of the program:

```php
date_default_timezone_set('America/Sao_Paulo');
```

But note the order: the injected clock solves the problem **with** or
**without** that line. The default time zone is a safety net; the explicit
time zone, in the clock and in the dates, is the rule.

## One month after the 31st

Casa Amarela's library card is renewed every month. Tainá wrote the
obvious:

```php
$renewed = new DateTimeImmutable('2026-01-31');
echo $renewed->modify('+1 month')->format('Y-m-d');
```

```text
2026-03-03
```

It is not a PHP bug. "One month after January 31" would be February 31,
which does not exist; PHP adds the leftover days and arrives at March 3.
Every language has to choose something, and PHP chose this.

When the rule is "the last day of the following month", it needs to be
said:

```php
echo $renewed->modify('last day of next month')->format('Y-m-d');
```

```text
2026-02-28
```

:::pitfall
`+1 month` only surprises from the 29th on — and tests usually use the 10th.
In any rule involving months, write a test with January 31. If the business
rule does not say what to do on that day, ask Vera before choosing: it is
her decision, not PHP's.
:::

## The date someone typed

At the counter, Vera types the return date for books that came in through
the drop box over the weekend: `24/03/2026`. The `DateTimeImmutable`
constructor is not the right place for that — it understands dozens of
formats and guesses the ambiguous ones. For typed text, state the format:

```php title="input.php" numbered
<?php

declare(strict_types=1);

function parseBrDate(
    string $text,
    DateTimeZone $tz,
): ?DateTimeImmutable {
    $date = DateTimeImmutable::createFromFormat(
        '!d/m/Y',
        $text,
        $tz,
    );
    $warnings = DateTimeImmutable::getLastErrors();
    if ($date === false || $warnings !== false) {
        return null;
    }
    return $date;
}

$tz = new DateTimeZone('America/Sao_Paulo');
$texts = ['24/03/2026', '31/02/2026', '2026-03-24', '24/3/2026'];
foreach ($texts as $t) {
    $d = parseBrDate($t, $tz);
    $out = $d?->format('Y-m-d H:i') ?? 'invalid';
    echo str_pad($t, 11), $out, "\n";
}
```

```text
24/03/2026 2026-03-24 00:00
31/02/2026 invalid
2026-03-24 invalid
24/3/2026  2026-03-24 00:00
```

Two details that make the difference.

**The `!` at the start of the format** zeroes everything the text does not
provide. Without it, the missing time comes from the clock: `24/03/2026`
becomes "March 24, at 9:55" — the time the script ran — and the comparison
with the due date goes wrong depending on the time of day.

**`getLastErrors()`.** `31/02/2026` does **not** return `false`: PHP does the
same month arithmetic and returns March 3, noting a warning. The warning
lives in `getLastErrors()`, which returns `false` when there were none.
Checking only `createFromFormat`'s `false` would let February 31 through.

`$d?->format(...)` is the *nullsafe* operator: it calls the method only if
`$d` is not `null` and, if it is, the whole result becomes `null`, with no
error. The `??` swaps that `null` for the text. Together, they say in one
line "format it if it exists; otherwise, write invalid".

:::note In your career
Dates are the area where the most code "works on my machine": your machine
is in the São Paulo time zone, the server is in UTC, the test runs in the
morning, and nobody works on January 31.

Three questions close most bugs before they exist: **what time zone** is
this instant in? is this a **date** or an **instant**? where does **now**
come from? When the answer to the third is "from inside the function", you
have a test that is going to fail at nine at night.
:::

## What volume 2 does with dates

Laravel uses a library called **Carbon**, which extends
`DateTimeImmutable` with shorter names: `now()->addDays(14)`,
`$due->isSunday()`, `$due->diffInDays($returned)`. Underneath, each one is
one of this chapter's calls.

The default time zone becomes a line in the project's configuration. And the
injected clock comes ready-made: in volume 2's tests, one call freezes the
whole framework's `now()` at a chosen instant. It is the `FrozenClock`,
applied to everything at once.

:::tree title="Where we are now"
catalog/
  src/
    Time/
      Clock.php              # interface: now()
      SystemClock.php        # São Paulo time zone
      FrozenClock.php        # for tests
    Circulation/
      LibraryCalendar.php    # Sundays and holidays
:::

:::summary
- `format('N')` gives the day of the week (7 is Sunday); a `while` skips
  closed days in a row.
- A due date is a date; a return is an instant. Convert the instant to the
  date's time zone, zero the time and only then compare.
- `diff()` returns `days`, always positive, and `invert` for the direction.
- "Now" is a dependency: receive a `Clock` through the constructor. The test
  passes a frozen clock. PSR-20 standardizes the idea.
- `+1 month` from January 31 is March 3. Spell out the rule.
- A typed date: `createFromFormat` with `!`, and check `getLastErrors()`.
:::

:::checkpoint
You calculate a due date that respects closed days, count days late without
being thrown off by the time or the time zone, write date code a test can
run at any hour, and validate a date a person typed.
:::

:::exercise level=1
For each value, say whether it is a **date** or an **instant** and which
database column it would go into — `DATE` or `DATETIME` in UTC:

1. the reader's date of birth;
2. the time the copy was borrowed;
3. the due date;
4. the time the fine was paid.

:::answer
1. Date, `DATE`. Nobody has a birthday in UTC.
2. Instant, `DATETIME` in UTC.
3. Date, `DATE` — the due date is the whole day, in the library's city.
4. Instant, `DATETIME` in UTC.
:::

:::exercise level=2
Write `dueDate(DateTimeImmutable $borrowedAt, int $days,
array $holidays): DateTimeImmutable`, which adds the days to the borrowing
date — without the time — and pushes the result to the next open day. Test
it with a borrowing on Saturday, March 7, 2026, at 4 p.m., and fourteen
days.

:::answer
```php
function dueDate(
    DateTimeImmutable $borrowedAt,
    int $days,
    array $holidays,
): DateTimeImmutable {
    $due = $borrowedAt->setTime(0, 0)->modify("+{$days} days");
    return nextOpenDay($due, $holidays);
}
```

Saturday, March 7, plus fourteen days is Saturday, March 21 — open, and the
due date stays there. With fifteen days, it would fall on Sunday the 22nd
and move to Monday the 23rd.

The `setTime(0, 0)` comes before the addition so the due date is a date,
not "the 21st at 4 p.m.". Without it, the `isOverdue` comparison would start
depending on the time of the borrowing.
:::

:::exercise level=3
The overdue report runs at 1 a.m., through the scheduler, on a server in
UTC. It uses `new DateTimeImmutable('today')` to know what day it is, and
lists the loans with a due date before today. Vera complains that, every
morning, the list includes people who are still within their period. Explain
the bug with concrete times and dates, and write the fix.

:::answer
At 1 a.m. in UTC, it is 10 p.m. **the previous day** in São Paulo. In the
early hours of March 25, UTC, the server's `today` is the 25th; in São Paulo,
it is still the 24th. Every loan due on the 24th goes onto the list as
overdue, even though the 24th has not ended yet in the library's city.

The fix is not to ask the server what day it is:

```php
$today = $clock->now()->setTime(0, 0);
```

with `$clock` being a `SystemClock` created with the São Paulo time zone.
The report's test passes a `FrozenClock` at `2026-03-25 01:00` UTC and checks
that the loan due on the 24th is **not** on the list.

The other half of the fix is a conversation, not code: asking Vera whether
the report should run at 7 a.m. São Paulo time, which is when she reads it.
:::
