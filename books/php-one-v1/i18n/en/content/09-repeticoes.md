---
source_hash: a4884acb311f
title: "Loops"
number: 9
slug: repeticoes
part: p1
kicker: "It works with twelve. The problem is that nobody tests with eight thousand."
goal: >-
  Walk through arrays with `foreach`, repeat under a condition without
  freezing the server, accumulate results, and measure the cost of a loop
  before it reaches production.
---

:::story It was supposed to be a little report
Thursday, 4:40 p.m. Cléber appeared at the corner of Dedé's desk with the
posture of someone about to ask for something small.

"It's quick. Just a little list of overdue books."

"That's all?"

"That's all. With the reader's name next to it."

Dedé wrote it in eleven minutes. He ran it on his machine, with the twelve
test loans Tainá had entered before lunch: instant.

He deployed it at 5:20 p.m. Friday was still a long way off, so technically
it was not a Friday deploy.

At 5:50 p.m. Vera called to say the report screen had been blank for twenty
minutes and there were people waiting at the counter.

Casa Amarela has 8,412 open loans and 1,204 registered readers.
:::

Dedé's report was not wrong. It was **right twelve times**, which is a far
more interesting — and far more expensive — category of bug than code that
is simply broken.

## `foreach` is the loop

```php title="list.php" numbered
<?php

$overdue = [
    ['title' => 'O Cortiço', 'days' => 9],
    ['title' => 'Vidas Secas', 'days' => 2],
    ['title' => 'Grande Sertão', 'days' => 41],
];

foreach ($overdue as $loan) {
    echo $loan['title'], ' - ',
         $loan['days'], " days\n";
}
```

```text
O Cortiço - 9 days
Vidas Secas - 2 days
Grande Sertão - 41 days
```

Read it as it is written: *for each item in `$overdue`, call it `$loan` and
run the block*.

There is no index, no `$i`, no `count()`. Where there is no index there is
no way to get the index wrong, and a whole class of classic bugs simply has
nowhere to happen.

When the key matters, it comes along:

```php title="with_key.php" numbered
<?php

$by_subject = [
    'literature' => 1240,
    'children' => 870,
    'reference' => 91,
];

foreach ($by_subject as $subject => $total) {
    echo $subject, ': ', $total, "\n";
}
```

```text
literature: 1240
children: 870
reference: 91
```

The same form works for lists and maps, because the two are the same type.
In a list, the key is the numeric position.

:::pitfall
`foreach` works on a **copy** of the array. Changing `$loan` inside the
loop does not change the original array:

```php
foreach ($overdue as $loan) {
    $loan['days'] = 0;   // changes nothing out there
}
```

There is the form `foreach ($overdue as &$loan)`, with `&`, which works by
reference and changes the original. It works and brings a classic problem
with it: after the loop, `$loan` still points to the last item, and the
next `foreach` that reuses that name overwrites the last position of the
array.

If you use `&`, write `unset($loan);` on the line after the loop. If you can
avoid it, do: building a new array is more predictable.
:::

## `for` and `while`

```php title="for.php" numbered
<?php

for ($page = 1; $page <= 3; $page++) {
    echo "Page ", $page, "\n";
}
```

```text
Page 1
Page 2
Page 3
```

`for` has three parts separated by semicolons: where it starts, how long it
keeps going, and what to do at the end of each round. It is for when the
**number** is the subject — pagination, a fixed number of repetitions, a
countdown — not when there is a collection to walk through.

```php title="while.php" numbered
<?php

$attempts = 0;
$connected = false;

while ($attempts < 3 && !$connected) {
    $attempts++;
    echo "Attempt ", $attempts, "\n";
    $connected = ($attempts === 3);
}
```

```text
Attempt 1
Attempt 2
Attempt 3
```

`while` repeats as long as the condition is true. It is for when stopping
does not depend on a collection: try again, read until it ends, wait until
it answers.

:::warning
Every `while` needs a written answer to the question *"what, in here, makes
the condition false some day?"*. In the example above, it is `$attempts++`.

And when stopping depends on something external — the network, a file,
another system — the loop **also** needs a limit on attempts. Notice the
`$attempts < 3`: without it, a network hiccup turns into a PHP process
spinning forever, tying up a server worker that never serves anyone again.
:::

## `break` and `continue`

```php title="control.php" numbered
<?php

$copies = [
    ['accession' => 812, 'status' => 'in_repair'],
    ['accession' => 907, 'status' => 'available'],
    ['accession' => 344, 'status' => 'available'],
];

$chosen = null;

foreach ($copies as $copy) {
    if ($copy['status'] !== 'available') {
        continue;
    }

    $chosen = $copy['accession'];
    break;
}

echo $chosen ?? 'none free', "\n";
```

```text
907
```

`continue` skips to the next round. `break` abandons the whole loop.

Notice `$chosen = null` **before** the loop. Without that line, an empty or
entirely unavailable list would leave the variable nonexistent, and the
final line would print a warning instead of a message.

:::pitfall
PHP accepts `break 2` and `continue 2`, to leave two levels of loop at
once. It is syntactically valid and humanly unreadable: whoever reads it
has to count braces to know where the code will jump out to, and on the day
someone adds an `if` in the middle, the number is still `2` and starts
pointing somewhere else, with no error at all.
:::

## The accumulator

A good share of loops print nothing: they build a value.

```php title="accumulator.php" numbered
<?php

$overdue = [
    ['title' => 'O Cortiço', 'days' => 9],
    ['title' => 'Vidas Secas', 'days' => 2],
    ['title' => 'Grande Sertão', 'days' => 41],
];

$total_days = 0;
$critical = 0;

foreach ($overdue as $loan) {
    $total_days = $total_days + $loan['days'];

    if ($loan['days'] > 30) {
        $critical++;
    }
}

echo $total_days, " days in total\n";
echo $critical, " critical case(s)\n";
```

```text
52 days in total
1 critical case(s)
```

Adding, counting and filtering are the same skeleton: a variable created
**before** the loop, modified **inside**, read **after**. Creating the
accumulator inside the loop is the mistake that resets the result on every
round and returns, at the end, only the last item.

PHP already ships some ready-made accumulators for the most common cases:

```php title="ready_made.php" numbered
<?php

$days = [9, 2, 41, 0, 15];

echo array_sum($days), "\n";
echo max($days), "\n";
echo min($days), "\n";
echo count($days), "\n";
```

```text
67
41
0
5
```

## Twelve records lie

Now for that Thursday's report. Stripped to the bone, it was this: for each
loan, find the matching reader in the list of readers.

```php title="slow_report.php" numbered
<?php

$loans = [];
for ($i = 0; $i < 8412; $i++) {
    $loans[] = ['reader_id' => $i % 1204];
}

$readers = [];
for ($i = 0; $i < 1204; $i++) {
    $readers[] = ['id' => $i, 'name' => "Reader {$i}"];
}

$start = microtime(true);
$lines = 0;

foreach ($loans as $loan) {
    foreach ($readers as $reader) {
        if ($reader['id'] === $loan['reader_id']) {
            $lines++;
            break;
        }
    }
}

printf("%d lines in %.3f s\n", $lines, microtime(true) - $start);
```

```text
8412 lines in 0.412 s
```

The first two parts generate test data with the `for` you just saw. `%`
returns the remainder of the division, which makes the reader IDs wrap
around between 0 and 1203.

`microtime(true)` returns the current time as a number with decimal places.
Store it before, subtract it after, and you have measured a piece of code.
It is the cheapest measuring tool there is and it settles most doubts.

Run it on your machine. The number will be different from mine; the order
of magnitude will be similar.

Notice what is happening: for each of the 8,412 loans, the program walks
through the list of readers until it finds the right one. On average, six
hundred comparisons per loan. **Five million comparisons** to print eight
thousand lines.

With Tainá's twelve test loans it was 7,200 comparisons, which PHP does
without blinking. The difference between the two cases is not the code. It
is the scale.

## Index before you walk

The fix is to build, just once, a map of readers by ID — and then access
directly, without searching:

```php title="fast_report.php" numbered
<?php

// same $loans and $readers as before

$start = microtime(true);

$reader_by_id = [];
foreach ($readers as $reader) {
    $reader_by_id[$reader['id']] = $reader;
}

$lines = 0;
foreach ($loans as $loan) {
    $reader = $reader_by_id[$loan['reader_id']] ?? null;

    if ($reader !== null) {
        $lines++;
    }
}

printf("%d lines in %.3f s\n", $lines, microtime(true) - $start);
```

```text
8412 lines in 0.002 s
```

Two hundred times faster, with four more lines.

What changed was not the apparent amount of work — both programs walk
through the loans once. What changed was the **cost of finding a reader**:
from "search a list of 1,204" to "grab it directly by key". A map accesses
by key in practically constant time, no matter how many items it has.

PHP does this indexing in one line:

```php
$reader_by_id = array_column($readers, null, 'id');
```

`array_column` extracts one column from an array of records. With `null`
as the second argument it keeps the whole record; the third says which
field to use as the key. It is worth knowing the manual version first,
because it is the one that explains what the function is doing.

:::key
Every time you write a loop, answer two questions: **how many rounds will
it do in production** and **how much does one round cost**. Multiply.

If the result goes past one second, you have a decision to make — not a
detail to sort out later.
:::

And there is a variant of this same shape that is much worse. Swap the
comparison inside the loop for a trip to another machine over the network,
and each round stops costing nanoseconds and starts costing milliseconds.
The same loop that took four tenths of a second now takes half an hour.

This pattern has a name — **N+1** — and it is probably the most common
performance bug in web applications: one lookup to fetch the list, plus one
lookup per item in the list. It is born here, in an innocent loop, long
before there is a database in the project.

## The small scope change

:::story A small scope change
The following Tuesday, Cléber came back.

"The report turned out great. We just had a small scope change."

Dedé waited.

"The board wants the history too. How many times each reader was late this
year."

"That's another report."

"It's the same screen. Just one little extra column."

The "little extra column" was one more lookup per reader, inside the loop
that already walked through eight thousand loans. Dedé did the math out
loud, and Cléber listened to the number all the way to the end.

"But it works on your machine, right?"

"It works. On my machine there are twelve."

Cléber thought for a moment.

"And what if we put twelve in production too?"
:::

:::note In your career
"It works on my machine" is almost never dishonesty — it is an **absence of
data**. The question that solves it, and that is worth taking to any
refinement meeting, is short:

> *"How many records will this walk through in production, in the worst
> month of the year?"*

If nobody knows the answer, that is the first task, and it takes ten
minutes. Asking this **before** estimating is one of the concrete
differences between a junior and a mid-level developer, and it has nothing
to do with knowing more syntax.

And there is a second question, which almost nobody asks: *"how many lines
of this screen will anyone actually read?"*. An eight-thousand-line report
is read by nobody. If the answer is "the first fifty", the performance
problem had a product solution before it had a technical one.
:::

:::summary
- `foreach` walks through arrays; `for` is for numbers; `while` is for
	conditions.
- `foreach` works on a copy — `&` changes the original and requires `unset`
	afterwards.
- Every `while` needs something that makes the condition false, and a limit
	on attempts when it depends on the outside world.
- `continue` skips the round, `break` abandons the loop; `break 2` is
	unreadable.
- An accumulator is born before the loop, changes inside it, is read after.
- A loop inside a loop multiplies: measure with `microtime(true)` before you
	believe it.
- Indexing by key trades a linear search for direct access.
- A loop's cost is rounds × cost per round — and a round that leaves the
	machine costs a million times more.
:::

:::checkpoint
You walk through arrays, repeat under a condition safely, accumulate
results, and can measure and estimate out loud how many operations a loop
will run in production.
:::

:::exercise level=1
Given the list of days late `[9, 2, 41, 0, 15]`, use a `foreach` to
calculate the total, the average and how many cases go past thirty days.
Then check the total with `array_sum`.

:::answer
```php
<?php

$days = [9, 2, 41, 0, 15];

$total = 0;
$critical = 0;

foreach ($days as $d) {
    $total = $total + $d;

    if ($d > 30) {
        $critical++;
    }
}

$average = $total / count($days);

echo "total ", $total, "\n";
echo "average ", $average, "\n";
echo "critical ", $critical, "\n";
echo "checking ", array_sum($days), "\n";
```

```text
total 67
average 13.4
critical 1
checking 67
```

Notice that the average came out with decimal places even though it is
`67 / 5`: division with `/` returns a `float` when it is not exact. If the
result needed to be an integer, the decision to round or truncate would
have to be written down.
:::

:::exercise level=2
Write a loop that finds the loan with the most days late and prints its
title. Handle the case of an empty list.

:::answer
```php
<?php

$overdue = [
    ['title' => 'O Cortiço', 'days' => 9],
    ['title' => 'Vidas Secas', 'days' => 2],
    ['title' => 'Grande Sertão', 'days' => 41],
];

$worst = null;

foreach ($overdue as $loan) {
    if ($worst === null || $loan['days'] > $worst['days']) {
        $worst = $loan;
    }
}

if ($worst === null) {
    echo "nothing overdue\n";
} else {
    echo $worst['title'], " with ", $worst['days'], " days\n";
}
```

```text
Grande Sertão with 41 days
```

The condition has two parts for a reason: on the first round there is
nothing to compare with, and `$worst === null` covers that. Initializing
`$worst` with the first item of the array would also work — and would break
with the empty list, which is exactly the case the exercise asked you to
handle.

Notice also the short-circuit: when `$worst === null` is true, the right
side of the `||` is not even evaluated. Without that, the comparison would
try to read `$worst['days']` from a null value.
:::

:::exercise level=3
The snippet below counts how many loans of children's books there were. It
takes several seconds with the real data. Identify the three problems, say
which one you would fix first and why.

```php
$total = 0;

foreach ($readers as $reader) {
    foreach ($loans as $loan) {
        if ($loan['reader_id'] !== $reader['id']) {
            continue;
        }

        foreach ($books as $book) {
            if ($book['id'] === $loan['book_id']
                && $book['subject'] === 'children') {
                $total++;
            }
        }
    }
}

echo $total;
```

:::answer
**Problem 1 — three nested loops.** That is 1,204 readers × 8,412 loans ×
4,000 books in the worst case. The count gets close to forty billion
comparisons, and no machine of this decade finishes that within a web
request.

**Problem 2 — a linear search where a map would fit.** The two inner loops
are searching by ID. Indexing `$books` by `id` before starting swaps the
third loop for direct access.

**Problem 3 — the outer loop serves no purpose.** Look at the result:
`$total` is a single number. The `$reader` variable is only used to compare
with `$loan['reader_id']` — and, since every loan belongs to some reader,
the comparison always finds a match. The 1,204-round loop exists to arrive
at the same number you would get without it.

**What I would fix first is the third one**, and that is the important part
of the answer.

Problems 1 and 2 are optimizations of code that should not exist. Fixing
the indexing here means keeping the same wrong algorithm, only faster. The
real question — "how many loans of children's books were there?" — does not
mention any reader.

```php
<?php

$book_by_id = array_column($books, null, 'id');

$total = 0;

foreach ($loans as $loan) {
    $book = $book_by_id[$loan['book_id']] ?? null;

    if ($book !== null && $book['subject'] === 'children') {
        $total++;
    }
}

echo $total, "\n";
```

Forty billion comparisons became eight thousand. And notice where the gain
came from: not from the loop getting smarter, but from two loops ceasing to
exist.

**The general rule:** before optimizing a loop, ask whether it should be
there. A good share of slow code is correct code solving the problem in the
wrong place.
:::
