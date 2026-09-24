---
source_hash: a29c9d30090b
title: "Functions"
number: 10
slug: funcoes
part: p1
kicker: "A rule that lives in ten places changes in nine. The tenth is always the one that prints the receipt."
goal: >-
  Extract a rule into a function, use parameters and return values with
  intent, understand scope without resorting to `global`, pass behavior as
  an argument, and prove the rule is right without deploying anything.
---

:::story Fifty cents
Casa Amarela's board approved, in the minutes, raising the daily fine from
R$ 0,50 to R$ 0,80. Mr. Juvenal sent a message on Saturday:

> *"It's just changing the number, right? Can it be done by Monday?"*

Dedé opened the System and searched for `0.5`.

Seven results.

The calculation on the return screen. The one in the outstanding-items
report. The one on the printed receipt. The one in the collection e-mail.
One inside an `if` that only runs in December, for some reason. One
commented out, with the date `// 2014` next to it. And a seventh, in
`functions2_NEW_final.php`, written as `50/100`.

He changed the six that were in use and deployed on Sunday.

On Monday, Vera called to say the printed receipt still showed the old
amount.

The receipt used none of the seven. It had its own, written as
`$days * 0.50`, in the middle of an HTML string, on a line four hundred and
twelve characters long.
:::

## One rule in ten places

Duplicated code does not raise errors. It does not show up in the log, it
breaks nothing, it does not complain in review — especially when the copies
are slightly different, like `0.5`, `50/100` and `0.50`.

It only shows itself when the rule changes. And rules always change: it is
the one guaranteed requirement of any system.

:::key
The question that identifies problematic duplication is not "is this code
similar?". It is: **"when this rule changes, how many places do I need to
remember?"**

If the answer is more than one, there is a function waiting to be born.
:::

:::art caption="Changing the number is easy. The hard part is finding every place it lives."
src="trocar-o-numero-e-facil-dificil-e-achar-todos-os-lugares-onde-ele-mora.png"
Minimalist editorial cartoon on a white background: a developer in his
early thirties, in a hoodie, holds a magnifying glass over an enormous map
of files unfolded on the desk. Seven red marks show the same number written
in different ways — "0.5", "0.50", "50/100" — and all of them have already
been crossed out with an X. Off the map, at the edge of the desk, a small
receipt printer spits out a strip of paper with the old amount, which nobody
is looking at. Behind him, an intern with an open notebook points at the
strip. Few elements, dry humor, tech-magazine aesthetic.
:::

## Give the decision a name

```php title="fine.php" numbered
<?php

function fineInCents(int $days_late): int
{
    if ($days_late <= 0) {
        return 0;
    }

    return min($days_late * 80, 2000);
}

echo fineInCents(0), "\n";
echo fineInCents(3), "\n";
echo fineInCents(90), "\n";
```

```text
0
240
2000
```

The word `function`, the name, the parameters in parentheses, the type of
what comes back, and the body between braces.

`return` does two things at once: it hands back the value **and ends the
function on the spot**. Nothing after it runs. That is why the first `if`
does not need an `else`: if the delay is zero or negative, the function is
already over.

`min()` returns the smallest of the values it receives, which here works as
a ceiling: the fine never goes past two thousand cents.

And notice where the rule's two numbers are — `80` and `2000`. In one place.
It is the difference between Dedé's search returning seven results and
returning one.

:::anatomy title="The parts of a function"
lang: php
code: |
  function fineInCents(
      int $days,
      int $per_day = 80,
  ): int {
      return min($days * $per_day, 2000);
  }
notes:
  - { line: 1, text: "The name is a verb or a question. `fine()` is ambiguous; `fineInCents()` even states the unit." }
  - { line: 2, text: "`int $days` is required: the caller has to provide it, and it has to be an integer." }
  - { line: 3, text: "`= 80` is the default value. Parameters with defaults always come after the required ones." }
  - { line: 3, text: "The comma after the last parameter is allowed since PHP 8 and avoids noise when someone adds another." }
  - { line: 4, text: "`: int` is the return type. Without it, the function promises anything." }
:::

The types are not decoration. With them, this happens:

```text
$ php -r 'function f(int $d): int { return $d * 80; } echo f("three");'
PHP Fatal error: Uncaught TypeError: f(): Argument #1 ($d)
must be of type int, string given
```

The function rejected the wrong argument at the door, with a message that
says which argument, what type was expected and what arrived. Without the
`int` declaration, PHP would try to convert `"three"` and produce a
meaningless result, silently.

## Handle the bad case and leave

A `return` in the middle of a function opens up a way of writing decisions
that did not exist before:

:::compare left="Nested" right="Guard clause" lang="php"
function lend($r, $c) {
    if ($r !== null) {
        if ($r['active']) {
            if (!$c['held']) {
                return 'ok';
            }
        }
    }
    return 'refused';
}
---
function lend($r, $c) {
    if ($r === null) {
        return 'no reader';
    }
    if (!$r['active']) {
        return 'inactive';
    }
    if ($c['held']) {
        return 'unavailable';
    }
    return 'ok';
}
:::

This is called a **guard clause**: handle the bad case, leave, and let the
main path hug the left margin.

The left side grows to the right with every new rule. With Vera's eleven
rules, the `return 'ok'` would end up forty-four spaces from the margin,
and whoever reads it would have to hold eleven conditions in their head to
understand how they got there.

And notice the gain that is not about formatting: each reason for refusal
ended up **next to its condition**, instead of in a generic `return` twelve
lines away. The version on the right can say why it refused; the one on the
left cannot.

:::key
If the main body of your function sits at three levels of indentation,
guards are almost always missing at the top. Deep indentation is not an
aesthetic problem: it is the number of conditions the reader has to keep in
their head at the same time.
:::

## Parameters that read well

```php title="calls.php" numbered
<?php

function recordReturn(
    int $loan_id,
    int $days_late,
    bool $waive_fine = false,
    bool $notify_reader = true,
): void {
    echo $loan_id, ' ', $days_late, ' ',
         var_export($waive_fine, true), ' ',
         var_export($notify_reader, true), "\n";
}

recordReturn(812, 9);
recordReturn(812, 9, true, false);
recordReturn(812, 9, waive_fine: true);
```

```text
812 9 false true
812 9 true false
812 9 true true
```

`: void` says the function returns nothing — it does something and that is
it. `var_export($x, true)` returns the value as text, which here serves to
see `true` and `false`, which `echo` would print as `1` and nothing.

The third call uses **named arguments**, a PHP 8 feature. Compare it with
the second: `recordReturn(812, 9, true, false)` forces whoever reads it to
open the function to find out what that `true` and that `false` are.

:::key
When a call has a loose `true` or `false`, name the argument. It is the
cheapest readability gain there is — zero run-time cost, zero extra lines —
and it settles forever the doubt of whoever reads the code six months from
now, which is probably you.
:::

Named arguments also let you skip the ones in the middle: in the third
call, `$waive_fine` was given without mentioning `$notify_reader`.

:::pitfall
Once you adopt named arguments, the **parameter name becomes a public
contract**. Renaming `$waive_fine` to `$no_fine` starts breaking the
callers, and the error only shows up at run time, with a message about an
unknown argument.

In library code that is serious. In application code, it is a manageable
nuisance. It is worth knowing before renaming, not after.
:::

## Promise a single type

```php title="return.php" numbered
<?php

function findReader(int $id): ?array
{
    $readers = [
        47 => ['name' => 'Marlene'],
        12 => ['name' => 'Juvenal'],
    ];

    return $readers[$id] ?? null;
}

var_dump(findReader(47));
var_dump(findReader(99));
```

```text
array(1) { ["name"]=> string(7) "Marlene" }
NULL
```

The question mark in `?array` means "array or `null`". It is an honest
contract: the caller knows, by looking at the signature, that they need to
handle the absence.

What you do **not** want is a function that returns things of different
kinds depending on the day:

:::compare left="Broken promise" right="Honest promise" lang="php"
function find($id) {
    if (!$id) {
        return false;
    }
    if ($error) {
        return "error";
    }
    return $data;
}
---
function find(int $id): ?array
{
    return $this_catalog[$id]
        ?? null;
}
:::

On the left, the caller has to test three different types and still tell
`false` from `"error"` from an empty array. It is the kind of function that
produces, at every call site, a five-line `if` — and what happens in
practice is that someone writes `if (!$result)` and goes back to the bug in
Vera's report.

On the right there is a single answer: the record, or nothing.

## The report that came out zero

:::story The report that came out zero
Tainá wrote the monthly report's totals. She tested it. It came out zero.

```php
$grand_total = 0;

function add(int $value): void
{
    $grand_total = $grand_total + $value;
}

foreach ($fines as $f) {
    add($f);
}

echo $grand_total;
```

"It doesn't make sense," she said. "I added up eight thousand reais and it
prints zero."

Dedé looked for two seconds.

"It prints zero because the `$grand_total` inside the function isn't the
one outside. They're two variables with the same name, and the one inside
dies when the function ends."

"But in Python that would be an error."

"In PHP it's a warning and it carries on."

"That's worse."

"It's much worse."
:::

```text
PHP Warning: Undefined variable $grand_total in /app/rep.php
on line 5
```

A warning, not a fatal error. The program carried on, added zero to zero
eight thousand times, and printed a perfectly plausible number.

In PHP, function scope is **closed**. Unlike JavaScript and Python, a
function does not see the variables outside it — not even to read them:

```php title="scope.php" numbered
<?php

$period = 14;

function loanDays(): int
{
    return $period;
}

echo loanDays(), "\n";
```

```text
PHP Warning: Undefined variable $period
PHP Fatal error: Uncaught TypeError: loanDays():
Return value must be of type int, null returned
```

Notice that the return type saved the day. Without the `: int`, the
function would return `null` silently and the problem would show up three
screens later.

There is a keyword that breaks the scope rule:

```php
function add(int $value): void
{
    global $grand_total;
    $grand_total = $grand_total + $value;
}
```

That works, and it is almost always the wrong answer.

:::warning
A function that reads or writes a global variable cannot be tested on its
own, cannot be called twice with confidence, and cannot be understood
without knowing the whole program.

Worse: it creates an **invisible** dependency. Nothing in the signature says
that the function needs `$grand_total` — whoever reads
`add(int $value): void` has no way of knowing.

The rule that prevents this fits in one sentence: **everything the function
needs comes in as a parameter; everything it produces goes out as a return
value.**
:::

The correct version uses nothing you have not already seen:

```php title="correct.php" numbered
<?php

function sumFines(array $fines): int
{
    $total = 0;

    foreach ($fines as $value) {
        $total = $total + $value;
    }

    return $total;
}

echo sumFines([50, 240, 2000]), "\n";
```

```text
2290
```

## A function you can prove

The `fineInCents()` from the beginning of the chapter has a property worth
naming: given the same number of days, it **always** returns the same
result, and it touches nothing outside itself. That is called a **pure
function**.

The practical consequence is that you can check the entire rule without a
database, without a server and without opening the browser:

```php title="check_fine.php" numbered
<?php

function fineInCents(int $days): int
{
    if ($days <= 0) {
        return 0;
    }

    return min($days * 80, 2000);
}

$cases = [
    [-3, 0],
    [0, 0],
    [1, 80],
    [24, 1920],
    [25, 2000],
    [90, 2000],
];

foreach ($cases as [$days, $expected]) {
    $actual = fineInCents($days);
    $mark = $actual === $expected ? 'ok    ' : 'FAILED';

    echo $mark, ' ', $days, ' days -> ', $actual, "\n";
}
```

```text
ok     -3 days -> 0
ok     0 days -> 0
ok     1 days -> 80
ok     24 days -> 1920
ok     25 days -> 2000
ok     90 days -> 2000
```

Six cases, one file, milliseconds. That is a test — no framework, no
library, no configuration. The `foreach ($cases as [$days, $expected])`
unpacks each pair straight into the two variables, and the comparison with
`===` checks value and type.

Notice the cases chosen: `24` and `25` surround the point where the ceiling
kicks in, and `-3` covers the early return. Testing the **edge**, and not
just any value in the middle, is what makes this file worth something.

Now compare that with checking the same rule inside that
four-hundred-and-twelve-character HTML string on the receipt. It is not
that it would be hard: it is that there is no entry point. The function is
not a formality — it is what makes the rule **reachable**.

:::note In your career
"Extract function" is the safest refactoring there is and the most
underrated in technical interviews. When someone asks you to improve a
piece of code, start there, before proposing architecture, design patterns
or microservices.

And there is a valuable side effect in legacy code: you do not need
permission to extract a function. It does not change behavior, it does not
change the database, it does not change a contract with anyone. It is the
only improvement you can make on an ordinary Tuesday, while fixing
something else, without calling a meeting.
:::

## A function can also be a value

```php title="closure.php" numbered
<?php

$format = function (int $cents): string {
    return 'R$ ' . number_format($cents / 100, 2, ',', '.');
};

echo $format(2000), "\n";
```

```text
R$ 20,00
```

A function with no name, stored in a variable. It is called a **closure**,
and the variable becomes callable as if it were a function's name.

Closures follow the same scope rule: they do not see what is outside. To
capture a variable, you ask for it:

```php title="use.php" numbered
<?php

$fine_per_day = 80;

$calculate = function (int $days) use ($fine_per_day): int {
    return $days * $fine_per_day;
};

echo $calculate(3), "\n";

$fine_per_day = 150;
echo $calculate(3), "\n";
```

```text
240
240
```

Look at the two outputs. `use ($x)` captures **by value**, at the moment
the closure is created — changing the variable afterwards changes nothing
in there. There is `use (&$x)`, by reference, which is rare and almost
always a symptom.

**Arrow functions** shorten the common case:

```php title="arrow.php" numbered
<?php

$fine_per_day = 80;

$calculate = fn(int $days): int => $days * $fine_per_day;

echo $calculate(3), "\n";
```

```text
240
```

A single expression, no braces, no `return`, no `use` — the arrow function
automatically captures what it needs, always by value. It is the form that
fits comfortably inside another call, and that is where it wins the day.

## The loop that became an expression

Remember the accumulator from chapter @cap:repeticoes? When the loop only
transforms one collection into another, there is a shorter way to say so:

```php title="map_filter.php" numbered
<?php

$overdue = [
    ['title' => 'O Cortiço', 'days' => 9],
    ['title' => 'Vidas', 'days' => 2],
    ['title' => 'Sertão', 'days' => 41],
];

$critical = array_filter(
    $overdue,
    fn(array $l): bool => $l['days'] > 30
);

$fines = array_map(
    fn(array $l): int => fineInCents($l['days']),
    $overdue
);

print_r(array_column($critical, 'title'));
print_r($fines);
```

```text
Array
(
    [0] => Sertão
)
Array
(
    [0] => 720
    [1] => 160
    [2] => 2000
)
```

`array_filter` takes the collection and a function that answers yes or no
for each item; it returns the ones that passed. `array_map` takes a
function and the collection — in that order, which is the reverse of the
other one, because that is how it happened in 1999 — and returns the result
of applying the function to each item.

:::pitfall
`array_filter` **keeps the original keys**. In the example, the item that
was left was at position 2 and would still be at position 2 — it was only
the printout that came after `array_column`, which renumbers.

It is exactly the bug that left the Casa Amarela app with an empty screen
in chapter @cap:arrays. Before sending an `array_filter` result out of PHP,
`array_values`.
:::

The rule for choosing between a loop and an expression is simple: if the
code **transforms** one collection into another, `array_map` and
`array_filter` say so better. If it **does things** — saves, sends, prints,
logs — `foreach` is clearer.

## Behavior as an argument

What makes `array_map` possible is that a function can receive another
function:

```php title="callable.php" numbered
<?php

function applyTo(array $items, callable $operation): array
{
    $out = [];

    foreach ($items as $item) {
        $out[] = $operation($item);
    }

    return $out;
}

$cents = [50, 240, 2000];

print_r(applyTo($cents, fn(int $c): float => $c / 100));
```

```text
Array
(
    [0] => 0.5
    [1] => 2.4
    [2] => 20
)
```

The `callable` type says "something that can be called goes here". The
`applyTo` function does not know what will be done with the items — it only
knows that something will. It is, on purpose, a homemade copy of
`array_map`, and writing it once is what makes `array_map` stop looking
like magic.

:::summary
- Extract a function when the answer to "how many places do I need to
	remember?" is more than one.
- `return` hands back the value and ends the function on the spot.
- Types on parameters and return values reject the error at the door, with
	a useful message.
- A guard clause handles the bad case and leaves, keeping the main path at
	the margin.
- Name the argument whenever it is a loose `true` or `false`.
- Promise a single type; `?array` is honest, three different types are not.
- Function scope is closed: whatever comes in, comes in as a parameter.
- `global` creates an invisible dependency and prevents checking the
	function on its own.
- A pure function can be proven in a file, with no framework at all.
- A closure captures by value with `use`; an arrow function captures on its
	own.
- `array_map` and `array_filter` to transform; `foreach` to do things.
:::

:::checkpoint
You extract a rule into a function with declared types, write guards
instead of nesting, explain why `global` is a symptom, and put together a
check file that proves the rule at its edges.
:::

:::exercise level=1
Write a function that receives the number of loan days and returns the
formatted due message, using 14 days as the default value. Call it in three
ways: without an argument, with a positional argument and with a named
argument.

:::answer
```php
<?php

function dueIn(int $days = 14): string
{
    return "Return within {$days} days";
}

echo dueIn(), "\n";
echo dueIn(7), "\n";
echo dueIn(days: 21), "\n";
```

```text
Return within 14 days
Return within 7 days
Return within 21 days
```

With a single parameter, the named argument gains nothing. It starts paying
off from the third parameter on, and pays off a lot when one of them is a
boolean.
:::

:::exercise level=2
The function below is doing two things. Split it in two and explain what
you gained.

```php
function processReturn(array $loan): string
{
    $days = $loan['days_late'];
    $fine = 0;

    if ($days > 0) {
        $fine = min($days * 80, 2000);
    }

    return 'R$ ' . number_format($fine / 100, 2, ',', '.');
}
```

:::answer
```php
<?php

function fineInCents(int $days): int
{
    if ($days <= 0) {
        return 0;
    }

    return min($days * 80, 2000);
}

function inReais(int $cents): string
{
    return 'R$ ' . number_format($cents / 100, 2, ',', '.');
}

echo inReais(fineInCents(9)), "\n";
```

```text
R$ 7,20
```

Three concrete gains.

**The calculation became checkable.** `fineInCents(25)` returns `2000`, a
number you can compare. The original version returned `"R$ 20,00"`, and
checking a business rule by comparing formatted text is like measuring
temperature by the color of the wall.

**The formatting became reusable.** `inReais()` works for fines, for
donations, for any amount. In the original version, it was stuck to the
fine.

**The two change for different reasons.** The daily rate changes by board
decision; the text format changes if one day the library issues receipts in
another language. When two things change for different reasons, they should
not be in the same function.
:::

:::exercise level=3
The snippet below is from the System and calculates the month's total
fines. It has three bugs: one that prevents the function from being
checked, one that prevents it from being reused, and one that makes the
result wrong by a few cents. Point out all three and rewrite it.

```php
$total = 0;

function accumulate($loan)
{
    global $total;

    $days = $loan['days'];

    if ($days > 0) {
        $total += $days * 0.80;
    }
}

foreach ($loans as $l) {
    accumulate($l);
}

echo "Total: R$ " . $total;
```

:::answer
**Bug 1 — `global`.** The function depends on a variable that is not in its
signature. You cannot call it in a check file without recreating the whole
environment, and two calls in a row interfere with each other.

**Bug 2 — it returns nothing.** A function that only produces a side effect
cannot be reused in any other context. Not in the report, not on the
receipt, not anywhere.

**Bug 3 — `0.80` is a `float`.** Adding up eight thousand floating-point
values accumulates error, and the system's total will differ from the
till's total by a few cents, without anyone knowing which of the two is
right. And the R$ 20,00 cap, which the board's minutes also set, is
missing.

```php
<?php

function fineInCents(int $days): int
{
    if ($days <= 0) {
        return 0;
    }

    return min($days * 80, 2000);
}

function totalFinesInCents(array $loans): int
{
    $total = 0;

    foreach ($loans as $l) {
        $total = $total + fineInCents($l['days']);
    }

    return $total;
}

$loans = [
    ['days' => 9],
    ['days' => -2],
    ['days' => 90],
];

$total = totalFinesInCents($loans);

echo 'Total: R$ ', number_format($total / 100, 2, ',', '.'), "\n";
```

```text
Total: R$ 27,20
```

Notice what the rewrite allows that the original version did not:
`totalFinesInCents([['days' => 9]])` can be called in a check file, with
three made-up loans, and compared with an expected number. Nothing needs to
be deployed.

And notice also that the cap rule ended up in one place. When the board
changes its mind again — and it will — the search will return one result.
:::

:::story The eighth
On Wednesday, Dedé searched again, this time for `0,50`, with a comma.

One result. A file called `notices.php`, which ran every night and sent
collection e-mails to whoever was late.

"Nobody has opened this one since 2016," he said.

Tainá looked over his shoulder.

"How do you know?"

"There's a commented-out debugging `echo` in the middle, with the date next
to it."

Márcia walked past behind the two of them and stopped.

"How long did it take to fix?"

"The first seven, forty minutes."

"And to find the eighth?"

"Three days."

"Put the three days in the spreadsheet."
:::
