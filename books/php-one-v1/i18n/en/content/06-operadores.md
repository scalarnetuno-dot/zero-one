---
source_hash: b71768a05326
title: "Operators"
number: 6
slug: operadores
part: p1
kicker: "The kiosk told Mrs. Marlene she was minus three days late, with a fine of negative R$ 2,40."
goal: >-
  Calculate, concatenate and combine values without surprises — and know the
  four places where PHP's evaluation order is not the one you read.
---

:::story Minus three days
The kiosk at the entrance was the only new piece of the System. It had
been installed in 2019, with a number pad and a small screen, and it let
readers type in their library card number and see their own status.

Mrs. Marlene typed hers on a Tuesday morning and called Vera over.

"Look here, dear."

```text
READER: 1183 - MARLENE S. COUTINHO
LATE:   -3 days
FINE:   R$ -2,40
```

"You returned it before the due date."

"I know. But it says the library owes me two forty."

"It doesn't."

"It says so."

Vera looked at the screen for a while. Then she looked at Mrs. Marlene,
who was seventy-nine years old and had infinite patience for this kind of
conversation.

"Would you like it in books or in cash?"

"Books will do."
:::

The kiosk's math was right. There was a question missing before it.

:::art caption="Minus three days late, and the library owing two forty."
src="menos-tres-dias-de-atraso-e-a-biblioteca-devendo-dois-e-quarenta.png"
Minimalist editorial cartoon on a white background: an old self-service
kiosk, with a number pad and a small screen that reads only
"FINE: R$ -2,40". In front of it, a seventy-nine-year-old lady, in a
cardigan with a handbag on her arm, points at the screen with her index
finger, serene and interested. Beside her, an older librarian with glasses
holds out a hardcover book towards the lady, like someone handing over
change. Few elements, dry humor, tech-magazine aesthetic.
:::

## Arithmetic, and the three divisions

The usual four operators work the way you expect:

```php title="arithmetic.php" numbered
<?php

$copies = 8000;
$shelves = 37;

echo $copies + $shelves, "\n";
echo $copies - $shelves, "\n";
echo $copies * $shelves, "\n";
echo $copies / $shelves, "\n";
```

```text
8037
7963
296000
216.21621621622
```

Notice the last one. Division with `/` returns a `float` whenever it is not
exact — and you cannot hang 216.216 books on a shelf. When the question is
about whole things, there are two other operators:

```php title="divisions.php" numbered
<?php

$copies = 8000;
$per_shelf = 37;

var_dump($copies / $per_shelf);
var_dump(intdiv($copies, $per_shelf));
var_dump($copies % $per_shelf);
```

```text
float(216.21621621622)
int(216)
int(8)
```

`intdiv` returns how many times it fits whole: **216 full shelves**. `%`,
called modulo or remainder, returns what is left over: **8 books** for
shelf 217.

The two answers together tell the whole story, and that is almost always
what you want: how many boxes do I need, and how much is left in the last
one.

:::pitfall
`%` gets strange with negative numbers, and the reason is that it follows
the sign of the **dividend**, not of the divisor:

```text
$ php -r 'var_dump(-7 % 3);'
int(-1)
```

Many people expect `2`. If your calculation can receive a negative number
and you need a remainder that is always positive — to distribute things in
cycles, for example — the safe form is `(($a % $b) + $b) % $b`.
:::

There is also exponentiation, `**`:

```text
$ php -r 'echo 2 ** 10;'
1024
```

And, to add or subtract one, the shortcuts `++` and `--`:

```php title="increment.php" numbered
<?php

$pages = 10;

$pages++;
echo $pages, "\n";

$pages--;
echo $pages, "\n";
```

```text
11
10
```

There is the form `++$pages`, before the name, which increments first and
only then returns the value. The difference between the two only shows up
when you use the result in the same expression, which saves one line in
exchange for harder reading. Prefer incrementing on one line and using the
value on the next.

## Concatenation is `.`, never `+`

```php title="concatenate.php" numbered
<?php

$title = "O Cortiço";
$year = 1890;

$line = $title . ' (' . $year . ')';

echo $line, "\n";
```

```text
O Cortiço (1890)
```

The dot glues two texts together. Notice that `$year` is a number and it
was glued on without complaint: `.` demands text, so the number becomes
text.

In PHP, `+` is **always** arithmetic. There is no adding of texts:

```text
$ php -r 'var_dump("a" + "b");'
PHP Fatal error: Uncaught TypeError: Unsupported operand
types: string + string
```

That bothers people coming from JavaScript and is, in practice, an
advantage. In PHP, `"10" + 5` will never return `"105"` by accident: it is
either math or an error.

## Assign and operate at once

```php title="compound.php" numbered
<?php

$total = 0;
$total += 80;       // the same as $total = $total + 80
$total += 80;
echo $total, "\n";

$report = "Overdue:\n";
// the same as $report = $report . "- Marlene..."
$report .= "- Marlene\n";
$report .= "- Juvenal\n";
echo $report;
```

```text
160
Overdue:
- Marlene
- Juvenal
```

All arithmetic operators have the compound form: `+=`, `-=`, `*=`, `/=`,
`%=`, `**=`. And `.` has its own, `.=`, which is how you build text a bit at
a time.

`.=` has a use that shows up all the time: building a report line by line,
appending to the end of a variable that started out empty.

## When the value might not be there

```php title="coalescing.php" numbered
<?php

$subject = null;

$label = $subject ?? 'General';

echo $label, "\n";
```

```text
General
```

`??` is **null coalescing**: it returns the left-hand side if it exists and
is not null; otherwise, it returns the right-hand side. It exists because
the alternative is a three-line staircase for every optional value.

There is also `??=`, which only assigns if what was there was null:

```php
$status ??= 'available';
```

There is a look-alike and dangerous cousin, `?:`, called the short ternary.
The difference between the two is exactly the trap from chapter
@cap:variaveis-e-tipos:

:::compare left="`?:` checks whether it is false" right="`??` checks whether it is null" lang="php"
$f = $fine ?: 500;
// fine = 0 becomes 500
---
$f = $fine ?? 500;
// fine = 0 stays 0
:::

`?:` asks "is this value false?", and zero is false. `??` asks "is this
value null?", and zero is not null. When the value at stake is a number or
a text that can legitimately be zero or empty, `??` is the correct operator
and `?:` is a bug waiting for the right day.

## The full ternary

```php title="ternary.php" numbered
<?php

$days = 3;

$message = $days > 0 ? 'overdue' : 'on time';

echo $message, "\n";
```

```text
overdue
```

It reads: if the condition is true, the value is the one in the middle;
otherwise, the one at the end. It is an `if/else` that **returns a value**
instead of running blocks, and it serves well when the decision fits
comfortably on one line.

:::pitfall
Nested ternaries are forbidden because of consequences, not taste. Since
PHP 8, writing one inside the other without parentheses is a **syntax
error**:

```text
$ php -r 'echo true ? 1 : true ? 2 : 3;'
PHP Fatal error: Unparenthesized `a ? b : c ? d : e` is not
supported
```

The language started refusing the construct because its evaluation order
surprised everyone, including whoever had written it. When the decision has
three outcomes, it deserves an `if` with a name.
:::

## Comparing and returning a number

```php title="spaceship.php" numbered
<?php

$days = 9;
$limit = 14;

var_dump($days <=> $limit);
var_dump($limit <=> $days);
var_dump($days <=> 9);
```

```text
int(-1)
int(1)
int(0)
```

`<=>` is called the **spaceship** because of its shape. It returns `-1` if
the left side is smaller, `1` if it is larger and `0` if they are equal.

Three answers in a single operator looks like a curiosity until you need to
sort a list. Every sorting algorithm asks the same question thousands of
times — "these two, which comes first?" — and `-1`, `0` and `1` are exactly
the three possible answers. When there is a list of loans to sort by due
date, this is the operator that will answer.

## Precedence

The full evaluation order has twenty levels and is not worth memorizing.
It is worth knowing the four places where people get it wrong:

| Written | Read as | The surprise |
|---|---|---|
| `!$a === $b` | `(!$a) === $b` | `!` comes before `===` |
| `$a . $b + $c` | error in PHP 8 | used to be `($a . $b) + $c` |
| `$a ?? $b ? $c : $d` | syntax error | `??` and `?:` don't mix |
| `$a = $b or $c` | `($a = $b) or $c` | `or` is weaker than `=` |

Table: The last row is the reason `and` and `or` exist as words in addition
to `&&` and `||` — and the reason not to use them.

The first row deserves attention because it produces a bug that gets
through review. You write `!$active === $expected` thinking "it is not true
that active equals expected". PHP reads "the opposite of active equals
expected", which is another question and sometimes gives the same answer —
until the day it does not.

:::key
Parentheses cost nothing at run time and nothing when reading. If two
people in a code review need to stop and discuss the evaluation order, the
parentheses should already have been there.
:::

And there is a behavior of `&&` and `||` worth knowing, because it stops
being a curiosity and becomes protection: both **short-circuit**. The
right-hand side is only evaluated if the left-hand side did not settle the
question on its own.

```php
if ($days_late > 0 && calculateFine($loan) > 0) {
```

If `$days_late` is zero, `&&` already knows the result is false and the
function is never even called. Swapping the two sides would make the
calculation run eight thousand times for nothing.

## The question missing from the kiosk

```php title="late.php (the System)" numbered
<?php

$days_late = 14 - 17;
$fine_in_cents = $days_late * 80;

echo $days_late, " days, ", $fine_in_cents, " cents\n";
```

```text
-3 days, -240 cents
```

The subtraction is correct. The problem is that it answers "how many days
of difference", and the kiosk shows the answer as if it were "how many days
late". Returning before the due date produces a negative difference, and
the rest of the program believed it.

The fix is one line:

```php title="late.php (fixed)" numbered
<?php

$difference = 14 - 17;
$days_late = max(0, $difference);
$fine_in_cents = $days_late * 80;

echo $days_late, " days, ", $fine_in_cents, " cents\n";
```

```text
0 days, 0 cents
```

`max()` returns the largest of the values it receives. With `0` as one of
the sides, it becomes a floor: the result never goes below zero. There is
`min()` for the opposite, which is how you write a ceiling — and it is
exactly what caps the fine at twenty reais.

:::key
Every calculation that can go negative needs an explicit decision about
what to do when it does. `max(0, $x)` is a decision; letting it through is
one too, only taken by omission and discovered by Mrs. Marlene.
:::

:::note In your career
The kiosk bug had been in production for five years and nobody had opened a
ticket, because the readers who returned early looked at the screen,
thought it was odd and left. The system only records what someone
complains about.

When you inherit a system, the list of open tickets is not the list of
bugs: it is the list of bugs that bothered someone enough to justify a
phone call. The difference between the two lists is usually large, and the
second one only shows up when you sit next to the people who use it.

An afternoon of observation at the front desk yields more than a week of
reading code. Bring a notebook and do not suggest anything on the first
day.
:::

:::summary
- `/` returns a `float`; `intdiv` returns the integer; `%` returns the
	remainder, with the sign of the dividend.
- Concatenation is `.`; `+` is always arithmetic and is an error between
	texts.
- `+=` and `.=` accumulate values and text.
- `??` checks for null; `?:` checks for false — and zero separates the two.
- `<=>` returns −1, 0 or 1, which are the three answers sorting needs.
- A nested ternary without parentheses is a syntax error since PHP 8.
- `&&` and `||` short-circuit: the order of the sides is protection.
- A calculation that can go negative needs `max(0, ...)` or a written
	decision about what to do.
:::

:::checkpoint
You write an expression with four operators and predict the result without
running it, choose between `/`, `intdiv` and `%` by the question you are
asking, and know when `??` and `?:` give different answers.
:::

:::exercise level=1
Casa Amarela received a donation of 250 books and has boxes that hold 18
each. How many full boxes come out, and how many books are left in the last
one? Print both answers.

:::answer
```php
<?php

$books = 250;
$per_box = 18;

$full = intdiv($books, $per_box);
$left = $books % $per_box;

echo $full, " full boxes and ", $left, " books in the last\n";
```

```text
13 full boxes and 16 books in the last
```

If the question were "how many boxes do I need to buy", the answer would be
14 — and the calculation would be
`intdiv($books, $per_box) + ($books % $per_box > 0 ? 1 : 0)`, or simply
`ceil($books / $per_box)`.

The difference between 13 and 14 is the difference between two similar
questions, and whoever delivers the wrong answer usually did not get the
math wrong.
:::

:::exercise level=2
Without running it, say what each line prints.

```php
$a = null;
$b = 0;

echo $a ?? 'empty', "\n";
echo $b ?? 'empty', "\n";
echo $b ?: 'empty', "\n";
```

:::answer
```text
empty
0
empty
```

The first: `$a` is null, so `??` returns the right-hand side.

The second: `$b` is zero, which **is not null**, so `??` returns the zero
itself.

The third: `$b` is zero, which **is false**, so `?:` returns the right-hand
side — and a fine of zero reais just became the word "empty" on someone's
receipt.
:::

:::exercise level=3
The snippet below calculates the amount to refund a reader who paid a fine
in advance and then had the delay recalculated. It has two bugs. Point out
both and write the correct version.

```php
$paid = 1500;
$owed = 800;

$difference = $paid - $owed;
$message = $difference ?: 'nothing to refund';

echo "Refund: R$ " . $difference / 100 . "\n";
echo $message . "\n";
```

:::answer
**Bug 1: `?:` with a number.** When `$paid` and `$owed` are equal,
`$difference` is zero, `?:` considers zero false and `$message` gets
`'nothing to refund'`. In this specific case it works by accident — but the
same code, meant to show the amount, would hide any difference of zero. The
right question is about the value, not about its truthiness.

**Bug 2: the calculation can go negative.** If the recalculation increases
the fine, `$owed` becomes larger than `$paid` and the system announces
"Refund: R$ -3.5", which is the kiosk bug again, in different clothes.

```php
$paid = 1500;
$owed = 800;

$to_refund = max(0, $paid - $owed);
$to_charge = max(0, $owed - $paid);

$reais = number_format($to_refund / 100, 2, ',', '.');

if ($to_refund > 0) {
    echo "Refund: R$ ", $reais, "\n";
} elseif ($to_charge > 0) {
    echo "Charge the difference\n";
} else {
    echo "Nothing to settle\n";
}
```

What really changed was not the calculation: it was the **three
outcomes**. The original code had two variables and assumed a single
scenario; the corrected version recognizes that "paid too much", "paid too
little" and "paid exactly" are three different situations, and that the
program needs to know which one it is in.

Notice also the division by 100 appearing only once, when building the
text. The whole calculation was done in cents.
:::
