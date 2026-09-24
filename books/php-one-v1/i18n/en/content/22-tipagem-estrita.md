---
source_hash: 789d6ce6d398
title: "Strict typing"
number: 22
slug: tipagem-estrita
part: p4
kicker: "The tool ran for eighteen seconds and came back with forty-one additions of a date to text. None of them had raised an error in fifteen years."
goal: >-
  Turn strict mode on in the right place, declare types that say
  something, know what PHP does not check at run time and run static
  analysis on a legacy project without stopping the company.
---

:::story Eighteen seconds
Dedé installed PHPStan on a Thursday afternoon, pointed it at the System's
folder and went to get coffee.

When he came back, the output had stopped scrolling.

```text
 [ERROR] Found 1.247 errors
```

"One thousand two hundred and forty-seven," read Tainá.

"In fourteen thousand lines. Could be worse."

He filtered by a single kind, the ones about addition. Forty-one were left.

```text
  213    Binary operation "+" between string and int
         results in an error.
```

"What's on 213?"

"`$return_date + 14`."

Tainá took a second.

"Does that work?"

"That has never raised an error."

"That's not what I asked."
:::

## The line that changes the whole file

Since chapter @cap:classes-e-objetos, PHP has been converting text into
numbers at functions' doors: `'1899'` goes in as `int(1899)` and nobody
complains. That is called **coercive mode**, and it is the default.

One line turns it off:

```php title="src/Catalog/Book.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Catalog;
```

`declare(strict_types=1)` has to be the file's **first statement**, before
even the `namespace`. Only comments can come before it.

With strict mode on, the door stops converting:

```php
fineInCents('3');
```

```text
Fatal error: Uncaught TypeError: fineInCents():
Argument #1 ($days) must be of type int, string given
```

And it stops converting even what looks harmless:

```php
fineInCents(2.5);
```

```text
Fatal error: Uncaught TypeError: fineInCents():
Argument #1 ($days) must be of type int, float given
```

In coercive mode, that `2.5` would become `2` silently. The fine for two and
a half days would cost two days, and the difference would show up in
March's accountability report, not on the screen.

:::key
There is one exception, and it is deliberate: `int` is still accepted where
a `float` is expected, even in strict mode. Every integer is an exact real
number, so nothing is lost.

The other direction is the one that loses something, and that is what strict
mode refuses.
:::

## The detail almost everyone gets wrong

The declaration applies to **the calls written in that file** — not to the
function it declares.

Prove it with two files:

```php title="fine.php" numbered
<?php

declare(strict_types=1);

function fineInCents(int $days): int
{
    return $days * 80;
}
```

```php title="report.php" numbered
<?php

require 'fine.php';

var_dump(fineInCents('3'));
```

```text
int(240)
```

It went through. `fine.php`'s `strict_types` protected nothing: what decides
is the file where the **call** is written, and `report.php` declared
nothing.

Put the line in `report.php` and the same code dies with a `TypeError`.

:::pitfall
The practical consequence is that `strict_types` is not a project setting:
it is a file-by-file decision.

A project with the line in 90% of its files has 10% of files that call
everything loosely — and those are precisely the old ones, which is where the
strange values live. That is why the team rule is usually simple and has no
exceptions: **every new file starts with the line**.
:::

## Union, nullable and the `mixed` that is giving up

A parameter can accept more than one type:

```php
function sum(int|float $a, int|float $b): int|float
{
    return $a + $b;
}
```

And it can accept the absence of a value:

```php
function findReader(int $id): ?Reader
```

`?Reader` is short for `Reader|null`. The two forms are the same thing; the
second is the one you write when there are more types in the list.

There is also `mixed`, which accepts anything:

```php
function process(mixed $data): mixed
```

That is not a type. It is an annotation saying nobody decided, and it costs
twice: PHP checks nothing, and whoever reads the function learns nothing.

:::key
`?Type` is honest when `null` **means** something — "not found", "not
returned yet". A null return date is an open loan, and that is information.

`?Type` is laziness when `null` is just a way of not deciding what happens
in the bad case. The symptom shows up three lines after every call, always
the same: an `if ($x === null)` nobody knows what it should do.
:::

## Return types

| Write | It means |
|---|---|
| `: void` | returns nothing; a bare `return;` is allowed |
| `: never` | **never** returns — always throws or exits |
| `: static` | returns an object of the same class as the caller |

Table: `void` and `never` are not synonyms. A `void` function ends; a
`never` function never ends along the normal path.

```php title="src/Circulation/Guard.php" numbered
function refuse(string $reason): never
{
    throw new \RuntimeException($reason);
}
```

`never` is real information for readers and for tools: the code after the
call is unreachable, and an `if/else` in which one side calls `refuse()`
does not need to return anything on that side.

## What PHP does not check

Strict mode checks the type of the value. It does not check what is inside
it.

```php
function totalFines(array $fines): int
```

An `array` of what? Fines? Integers? Database rows? PHP accepts any array,
including an empty one, one of strings and one with three `null`s inside.
The annotation gave the impression of rigor and checked almost nothing.

The way out is to annotate the contents in a comment the tools read:

```php title="src/Loans/Till.php" numbered
/**
 * @param list<Fine> $fines
 */
function totalFines(array $fines): int
{
    $total = 0;

    foreach ($fines as $fine) {
        $total += $fine->cents();
    }

    return $total;
}
```

`list<Fine>` means: an array with sequential indexes in which every value is
a `Fine`. PHP ignores that comment. The tool in the next section does not —
and it is the one that starts refusing the call with the wrong array.

## PHPStan: the error that shows up before running

```text
$ composer require --dev phpstan/phpstan
```

```neon title="phpstan.neon"
parameters:
    level: 5
    paths:
        - src
```

```text
$ vendor/bin/phpstan analyse
```

```text
 ------ -------------------------------------------------------------
  Line   src/Loans/Till.php
 ------ -------------------------------------------------------------
  18     Parameter #1 $fines of function totalFines expects
         list<CasaAmarela\Loans\Fine>, list<string> given.
 ------ -------------------------------------------------------------

 [ERROR] Found 1 error
```

The program did not run. Nobody opened the screen, nobody created test data,
and even so the error has a file, a line and the exact difference between
what the function asks for and what the call delivers.

:::term Static analysis
Reading the code without running it, to deduce what can happen. It is the
same work you do when reviewing a *pull request* — with the difference that
the tool reads all fourteen thousand files every time and does not get
sleepy.
:::

The levels go from 0 to 10, and each one turns on a family of checks:

| Level | Starts enforcing |
|---|---|
| 0 | classes, functions and methods that do not exist |
| 3 | return types and property assignments |
| 5 | argument types in calls |
| 6 | missing content annotations on `array` |
| 8 | method calls on things that may be `null` |

Table: Start at 0 on an existing project and go up one level at a time.
Starting at 9 produces a report nobody reads.

## Typing legacy code without stopping the company

The System's 1,247 errors are not going to be fixed this sprint, nor the
next one. And leaving the tool red is the same as not having it: in two
weeks nobody looks anymore.

The mechanism that solves this is called a **baseline**:

```text
$ vendor/bin/phpstan analyse --generate-baseline
```

```neon title="phpstan.neon"
includes:
    - phpstan-baseline.neon

parameters:
    level: 5
    paths:
        - src
```

The generated file is a list of the errors that exist today, with a request
to ignore them. From then on, the tool goes back to green — and starts
complaining **only about what is new**.

The effect in practice is what makes the technique worth it: the debt stops
growing on the day you turn it on, without anyone needing to approve a month
of refactoring. Old code leaves the list as someone touches it for another
reason.

:::pitfall
A baseline with no expiry date becomes a rug to sweep things under. The
agreement that tends to hold is numeric and public: the list cannot grow,
and each real fix leaves it for good.

When the number does not go down for three months in a row, it is not
measuring technical debt — it is measuring priority. And that is useful
information to take to Tuesday's meeting too.
:::

:::note In your career
Static analysis changes what you can promise. "This doesn't break anywhere
else" is a sentence nobody should say about a fourteen-thousand-line system
— unless a tool has checked all fourteen thousand.

It is also the strongest answer to the question you will hear when you
propose types: *"and what do we get out of it?"*. The answer is not "prettier
code". It is: the error that today shows up on Tuesday morning, on Vera's
screen, starts showing up on your machine, before the commit, with the exact
line.
:::

:::tree title="Where we are now"
catalog/
  composer.json      # phpstan in require-dev
  phpstan.neon       # level 5, paths: src
  phpstan-baseline.neon
  src/               # every file with declare(strict_types=1)
    Catalog/
    Circulation/
    Loans/
    Readers/
:::

:::summary
- `declare(strict_types=1)` is the file's first statement and turns off
  automatic conversion in calls.
- It applies to the calls **written in that file**, not to the function
  declared in it.
- `int` to `float` still goes through; the reverse does not.
- `?Type` is `Type|null`; use it when `null` means something, not to put off
  the decision.
- `mixed` is not a type: it is the annotation of someone who did not decide.
- `void` ends, `never` does not end along the normal path.
- `array` says nothing about the contents; `@param list<Fine>` does, and the
  tool reads it.
- PHPStan finds the error before running; start at level 0 and go up.
- A baseline freezes the existing debt and makes the tool enforce only what
  is new.
:::

:::checkpoint
You turn strict mode on in the right place, explain why the declaration in
one file does not protect calls made in another, choose between `?Type` and
deciding, annotate an `array`'s contents and run static analysis with a
baseline on a project that has a thousand errors.
:::

:::exercise level=1
Say what each call does, given that the file writing them has
`declare(strict_types=1)` and the function is
`function period(int $days): int`.

1. `period(14)`
2. `period('14')`
3. `period(14.0)`
4. `period(true)`
5. `period(null)`

Then answer what changes in all five if the `strict_types` line is deleted.

:::answer
With strict mode:

1. goes through.
2. `TypeError` — a string does not become an int.
3. `TypeError` — a float does not become an int, not even when it is round.
4. `TypeError` — a boolean does not become an int.
5. `TypeError` — the parameter is not `?int`.

Without the line, the first four go through: `'14'` becomes `14`, `14.0`
becomes `14`, `true` becomes `1`. The fifth still raises a `TypeError`,
because `null` is only accepted when the type says it is.

Case 4 is the one that usually scares people most: `period(true)` returning
a one-day period is the kind of bug that never shows up on the happy path
and shows up the day a configuration variable becomes a boolean by mistake.
:::

:::exercise level=2
This function exists in the System and PHPStan complains about it at three
different levels. Type it completely, including the arrays' contents, and
explain each decision.

```php
function overdue($loans, $today = null)
{
    $out = [];

    foreach ($loans as $l) {
        if ($l['returned_at'] == null
            && $l['due_on'] < $today) {
            $out[] = $l;
        }
    }

    return $out;
}
```

:::answer
```php title="src/Loans/queries.php" numbered
<?php

declare(strict_types=1);

/**
 * @param list<Loan> $loans
 * @return list<Loan>
 */
function overdue(
    array $loans,
    \DateTimeImmutable $today,
): array
{
    $out = [];

    foreach ($loans as $loan) {
        if ($loan->isOpen()
            && $loan->isDueBefore($today)) {
            $out[] = $loan;
        }
    }

    return $out;
}
```

**The arrays became objects.** `$l['returned_at']` is a key that can be
misspelled with no warning; `$loan->isOpen()` is a method that either exists
or does not compile. That is the swap from chapter @cap:classes-e-objetos,
now enforced by the tool.

**`$today` lost its `null` default.** A parameter that accepts `null` and is
compared with `<` hides the case where it arrives null — and a comparison
with `null` is always false, so the function would return an empty list
without complaint. The caller passes the date; the function does not invent
one.

**The comparisons became methods.** `== null` became `isOpen()`, and the
date comparison became `isDueBefore()`. Besides saying what they mean, both
take the loose comparison and the date-as-text comparison out of the way.

**The return got `list<Loan>`.** Without it, PHPStan accepts someone passing
the result to a function that expects something else.
:::

:::exercise level=3
You join a 40-thousand-line project with no types at all, no tests, in
production, with two developers and a full *roadmap*.

Write the plan for introducing typing and static analysis in four steps,
each with what you would do and what you would answer if management asked
"how much time will this take away from the deadline".

:::answer
**Step 1 — install and freeze.** PHPStan in `require-dev`, level 0,
baseline generated the same day. Cost: an afternoon. Answer to management:
no time from the deadline, and from today new code with a type error does
not get in.

**Step 2 — the new-file rule.** Every file created is born with
`declare(strict_types=1)` and with types on everything. Cost: zero, because
it is like writing the file any other way. Answer: this is not a project, it
is a convention — like indentation.

**Step 3 — go up one level per quarter.** Each step up generates new errors;
they go into the baseline and leave it as the code is touched. Cost: an
afternoon per quarter to go up and regenerate. Answer: the number of frozen
errors is public, and we will look at it in the retrospective.

**Step 4 — the touch rule.** A file someone opens for any reason leaves the
baseline before it is closed. Cost: diluted in work that was already
happening. Answer: it will not take time from the deadline; it will take
about twenty minutes of each task that was going to happen anyway.

What does **not** go into the plan, and it is worth saying why: a task
called "type the system". It never gets prioritized, and when it gets
approved it becomes a month of changes with no tests at all on a system in
production — which is the most expensive possible way to introduce types.
:::
