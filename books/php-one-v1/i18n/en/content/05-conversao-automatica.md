---
source_hash: b4e41d704334
title: "When PHP converts on its own"
number: 5
slug: conversao-automatica
part: p1
kicker: "Mr. Juvenal typed the wrong password and logged in as the head librarian. The culprit is two characters long."
goal: >-
  Predict automatic type conversion instead of being surprised by it,
  choose between `==` and `===` on purpose, and know why money is not stored
  in a `float`.
---

:::story I got in by accident
Friday, 10:20. Mr. Juvenal called in the tone of someone who has
discovered something good.

"Listen, I managed to get into the system!"

"Great. Did the new password work?"

"No, I got the password wrong. But I got in anyway. And I got in as Vera."

Dedé asked him to repeat it slowly.

Mr. Juvenal had tried Vera's username with some random password —
according to him, "something with 240 in it". The System accepted it and
opened the head librarian's dashboard, with permission to delete the
catalog.

"Is that normal?"

"No."

"Because if it is, it's very handy."
:::

The System had not been hacked. It was doing exactly what the code told it
to, and the code told it with two characters fewer than it should have.

To get there, you first need to understand what PHP does when it receives
two different types in the same operation.

## `"10" + 5` is fifteen

```text
$ php -r 'var_dump("10" + 5);'
int(15)
$ php -r 'var_dump("10" . 5);'
string(3) "105"
$ php -r 'var_dump(true + true);'
int(2)
```

PHP converts automatically when the operation demands a different type from
the one it received. That has a name: **type coercion**, or, in the
community's jargon, *type juggling*.

Notice that the decision belongs not to the value but to the **operator**.
`+` is arithmetic, so it demands numbers and the string `"10"` becomes the
number `10`. `.` is concatenation, so it demands text and the number `5`
becomes `"5"`. The same pair of values, two different results, because the
question was a different one.

`true + true` looks like a joke and is not: `true` converted to a number is
`1`, and `false` is `0`. This behavior is used on purpose to count how many
conditions in a list were met.

When the conversion makes no sense at all, PHP 8 refuses:

```text
$ php -r 'var_dump("abc" + 5);'
PHP Fatal error: Uncaught TypeError: Unsupported operand
types: string + int
```

In PHP 7 that returned `5` with a warning nobody read. The language started
refusing the absurd instead of improvising, and that is the most important
difference between the PHP with a bad reputation and the PHP you are
learning.

:::pitfall
One leftover survived, and it is best never to use it:

```text
$ php -r 'var_dump("10 books" + 5);'
PHP Warning: A non-numeric value encountered
int(15)
```

The string **starts** with a number, so PHP uses the beginning and throws
away the rest, with a warning that is usually turned off in production.

This matters because everything that arrives from a form arrives as text.
The "quantity" field filled in with `3 boxes` will not raise an error: it
will become `3`, silently, and the difference will show up in the stock two
weeks later.
:::

## The closed list of what is false

When any value is used where the language expects true or false — inside
an `if`, for example — it gets converted. The list of what becomes `false`
is short and closed:

| Value | Becomes `false`? |
|---|---|
| `false` | yes |
| `0` and `0.0` | yes |
| `""` (empty text) | yes |
| `"0"` (the text with a single zero) | **yes** |
| `[]` (empty list) | yes |
| `null` | yes |
| anything else | no |

Table: Seven rows. Everything that is not here is true, including `-1`,
`"false"` and `"0.0"`.

The row that surprises almost everyone is the fourth. **The string `"0"` is
false in PHP** — and it is the only non-empty string that is.

```text
$ php -r 'var_dump((bool) "0", (bool) "0.0", (bool) "false");'
bool(false)
bool(true)
bool(true)
```

The text `"0"` is false; the text `"0.0"` is true; the text `"false"` is
true. There is no logic to deduce here, just a rule to know: it exists
because, at a time when everything coming from a form was text, `"0"` had
to mean zero.

It is a real trap. A form field filled in with `0` arrives as `"0"`, and
`if ($quantity)` decides it was not filled in.

## `==` converts, `===` does not

```text
$ php -r 'var_dump(1 == "1");'
bool(true)
$ php -r 'var_dump(1 === "1");'
bool(false)
```

They are two different operators, not two ways of writing the same one.

**`==` compares after converting.** It takes both sides, finds a common
type and compares the results. That is why the number `1` and the text
`"1"` are equal as far as it is concerned.

**`===` compares value and type, converting nothing.** Different types
already answer `false`, without even looking at the value.

| Comparison | `==` | `===` |
|---|---|---|
| `1` and `"1"` | `true` | `false` |
| `0` and `""` | `false` (since PHP 8) | `false` |
| `"abc"` and `0` | `false` (since PHP 8) | `false` |
| `null` and `false` | `true` | `false` |
| `"1e3"` and `"1000"` | `true` | `false` |

Table: The fourth row produces a silent bug — `null == false` lets "not
provided" pass for "denied". The fifth is the one that opened Casa
Amarela's door.

:::trivia
In PHP 7, `0 == "abc"` was **true**: the non-numeric string became `0`. Any
loose comparison between zero and text passed.

PHP 8 reversed the rule — now it is the number that becomes text when the
text is not numeric — and `0 == "abc"` became `false`. It was one of the
few compatibility breaks in PHP's history that practically nobody
complained about. The proposal was called *Saner string to number
comparisons*, and the name already said what the community thought of the
previous behavior.
:::

The recommendation fits in one line: **use `===` by default**. Write `==`
only when the conversion is exactly what you want, and leave a comment
saying why.

## Two characters at the door

With that in mind, you can read the System's `login.php`.

```php title="login.php (the System, 2009)" numbered
<?php

$sent_password = md5($_POST['password']);

if ($sent_password == $stored_password) {
    log_in();
}
```

`md5()` scrambles a text into a 32-character code, always the same way: the
same password always produces the same code. That is how passwords were
stored in 2009 — you did not store the password, you stored the scramble.

Now look at what happens with two specific passwords:

```text
$ php -r 'echo md5("240610708"), "\n";'
0e462097431906509019562988736854
$ php -r 'echo md5("QNKCDZO"), "\n";'
0e830400451993494058024219903391
```

They are two different codes. And even so:

```text
$ php -r 'var_dump(md5("240610708") == md5("QNKCDZO"));'
bool(true)
```

Both start with `0e` and have only digits after that. That is how
scientific notation is written: `0e462...` is **zero times ten to the power
of 462...**, which is zero. `==` saw two numeric strings, converted both to
the number `0.0` and compared the numbers.

The code for Vera's password, saved in 2009, had that format. Any password
whose `md5` also had it got into her account — and there are thousands of
texts like that, catalogued in public lists for more than a decade.

Mr. Juvenal hit one by chance.

:::story Four minutes
Dedé wrote a twenty-line program that tested a public list of texts whose
code has the `0e` format.

In four minutes, he had found two vulnerable desk-clerk accounts.

Vera's was one of them.

"Since when?" she asked.

"Since 2009."

Vera was quiet for a while, smoothing the label on a book that was already
stuck on.

"And how many people knew?"

"Nobody. It was Mr. Juvenal, getting his password wrong."

"So we were lucky."

"We had Mr. Juvenal."
:::

The bug had three layers, and it is worth separating them because the fix
for each one is different.

**First: `==` between secrets.** The loose comparison turned two distinct
values into equal ones. A `===` would have prevented this specific
incident.

**Second: MD5 for passwords.** Even with `===`, MD5 is too fast — an
ordinary graphics card computes billions per second, which makes it viable
to test passwords in bulk until one hits. Passwords call for a deliberately
slow algorithm, which is what `password_hash()` uses.

**Third: variable-time comparison.** Even with `===`, PHP's text comparison
stops at the first differing character. A guess that gets the first five
characters right takes measurably longer than one that gets the first one
wrong — and, with enough requests, you can discover a secret character by
character without ever guessing it whole.

:::key
Comparing a secret — a password, a token, a signature — uses neither `==`
nor `===`. It uses `hash_equals()`, which always walks the entire length, no
matter where the difference is:

```php
if (hash_equals($expected, $received)) {
```

The order matters: the **known** value comes first.

And, for passwords specifically, not even that: the pair `password_hash()`
and `password_verify()` already takes care of algorithm, salt and constant
time in one go. Storing passwords any other way, in 2026, is a decision that
needs to be defended in writing.
:::

## Converting on purpose

When you **want** the conversion, ask for it. A **cast** is a type in
parentheses in front of the value:

```php title="casts.php" numbered
<?php

$text = "42.7";

var_dump((int) $text);
var_dump((float) $text);
var_dump((string) 42);
var_dump((bool) $text);
```

```text
int(42)
float(42.7)
string(2) "42"
bool(true)
```

Notice the first one: `(int) "42.7"` returned `42`, not `43`. The cast to
integer **throws away** the decimal part, it does not round. For rounding
there is `round()`, and the one-cent difference between the two choices is
the source of a disproportionate number of customer complaints.

The advantage of a cast over automatic conversion is not technical, it is
about reading: whoever reviews the code sees that the conversion was a
decision, not an accident.

## The cent that disappears

There is one last place where PHP answers an imprecise question precisely.

```text
$ php -r 'var_dump(0.1 + 0.2);'
float(0.30000000000000004)
$ php -r 'var_dump(0.1 + 0.2 == 0.3);'
bool(false)
```

This is not a PHP bug, and it is not specific to PHP: it is how every
computer represents numbers with a decimal point, in base 2. The value
`0.1` in base 2 is an infinitely repeating fraction, the same way `1/3` is
infinite in base 10. At some point the computer cuts it off, and what is
left is a very good approximation, not an exact value.

At the seventeenth decimal place nobody cares. The problem is that the
error accumulates:

```php title="why_not_float.php" numbered
<?php

$total = 0.0;
$i = 0;

while ($i < 1000) {
    $total = $total + 0.50;
    $i = $i + 1;
}

var_dump($total);
var_dump($total === 500.0);
```

```text
float(500.0000000000171)
bool(false)
```

A thousand fines of fifty cents should add up to five hundred reais. They
added up to five hundred reais and an invisible error — which only shows up
in the comparison, or at the month-end close, when the system's total and
the till's total differ by a few cents and nobody knows which of the two is
right.

:::history
The standard that governs `float` — IEEE 754, from 1985 — was the work of a
committee led by William Kahan, who won the Turing Award for it. Before it,
each processor manufacturer rounded its own way, and the same calculation
gave different results on different machines.

The `0.30000000000000004` is not a flaw in the standard: it is the standard
working, and working the same way everywhere. The flaw is using a type
designed for physical measurement for a value that needs to be exact.
:::

The way out is not to store reais. Store **cents**, as an integer:

```php title="money.php" numbered
<?php

const FINE_PER_DAY_IN_CENTS = 80;
const FINE_CAP_IN_CENTS = 2000;

$days = 12;
$total_in_cents = $days * FINE_PER_DAY_IN_CENTS;

if ($total_in_cents > FINE_CAP_IN_CENTS) {
    $total_in_cents = FINE_CAP_IN_CENTS;
}

$reais = number_format($total_in_cents / 100, 2, ',', '.');
echo 'R$ ', $reais, "\n";
```

```text
R$ 9,60
```

`number_format` builds the text for display: it takes the value, the
number of decimal places, the decimal separator and the thousands
separator. With `','` and `'.'` in those positions, it comes out in the
Brazilian format.

:::key
An integer in cents is exact, adds up without error, compares with `===`
and fits in an `int` up to ninety quadrillion — enough headroom for a
neighborhood library. The division by 100 happens **only at display time**,
never in the middle of a calculation.

And the convention that holds the rule up is the name: **every money
variable ends in `_in_cents`.** The name carries the unit, and a whole
category of error disappears — including somebody adding a value in reais to
one in cents six months from now.
:::

Use `float` for weight, temperature, percentage and averages. For money,
never.

:::note In your career
Finding a security flaw in a system that is not yours is a socially
uncomfortable situation, and the way you communicate it changes the
outcome.

What works: writing to the person in charge, with **the impact in business
language first** and the technical detail afterwards. "It is possible to
get into the head librarian's account without knowing the password, and
delete the catalog" communicates better than "there is a loose comparison
of an MD5 hash".

What does not work: demonstrating it publicly. Getting into someone's
account to prove the point, even with the best of intentions, transfers the
problem to you — and the conversation stops being about the flaw and
becomes about your access.

And there is a practical rule that holds for your whole career: **record
the date**. If the fix takes six months and something happens, the distance
between "I warned you" and "I warned you on March 14, in this e-mail" is
enormous.
:::

:::summary
- PHP converts types when the operator demands it: `+` pulls toward number,
	`.` pulls toward text.
- Text that starts with a number is used halfway, with a warning.
- The list of false values is closed and has seven rows — `"0"` is on it.
- `==` compares after converting; `===` compares value and type. Use `===`.
- Secrets are not compared with `===`, but with `hash_equals`; passwords use
	`password_verify`.
- A cast is a conversion requested in writing, and `(int)` throws away the
	decimal part instead of rounding.
- Money is an `int` in cents, divided by 100 only for display, with the unit
	in the variable's name.
:::

:::checkpoint
You predict the result of an operation between different types, choose
between `==` and `===` and justify the choice, and can explain in a review
why the fine is an integer.
:::

:::exercise level=1
Without running them, give the result and type of each expression. Then
check with `var_dump`.

```php
"7" + 3
"7" . 3
"7" == 7
"7" === 7
(int) "9 books"
(bool) "0"
```

:::answer
```text
int(10)
string(2) "73"
bool(true)
bool(false)
int(9)
bool(false)
```

The fifth is the most dangerous of the six: `(int) "9 books"` returns `9`
without any complaint, because an explicit cast does not emit the warning
the addition would. You asked for the conversion; PHP did its best.
:::

:::exercise level=2
The snippet below checks a discount coupon sent in a form. It has two bugs.
Find both and write the correct version.

```php
$coupon = $_POST['coupon'];

if ($coupon == 0) {
    echo "no coupon";
}
```

:::answer
**Bug 1: `==` with a number on the right-hand side.** Before PHP 8, any
non-numeric text would become `0` and get into the `if`. In PHP 8 that was
fixed, but the code still says one thing and means another.

**Bug 2: the question is wrong.** "No coupon" is the absence of the field,
not the value zero. The field may not even have been sent, and then
`$_POST['coupon']` produces an undefined-index warning before any
comparison.

```php
$coupon = $_POST['coupon'] ?? '';

if ($coupon === '') {
    echo "no coupon";
}
```

`?? ''` returns the left-hand side if it exists and is not null; otherwise,
it returns the right-hand side. It takes care of the warning and guarantees
that the next comparison compares text with text.

It is worth noticing what the corrected version stopped accepting: the
coupon `"0"`. If there is a coupon with that code, the original version
would reject it silently — and that is precisely the category of bug that
only shows up when someone in sales registers one.
:::

:::exercise level=3
Casa Amarela charges 80 cents per day late, capped at R$ 20,00. Write the
calculation for 0, 1, 25 and 100 days, keeping everything in cents, and
explain why the 25-day case is the most important one to test.

:::answer
```php
<?php

const FINE_PER_DAY_IN_CENTS = 80;
const FINE_CAP_IN_CENTS = 2000;

$cases = [0, 1, 25, 100];

foreach ($cases as $days) {
    $total = $days * FINE_PER_DAY_IN_CENTS;

    if ($total > FINE_CAP_IN_CENTS) {
        $total = FINE_CAP_IN_CENTS;
    }

    echo $days, " days: ", $total, " cents\n";
}
```

```text
0 days: 0 cents
1 days: 80 cents
25 days: 2000 cents
100 days: 2000 cents
```

`foreach` walks through a list of values, one at a time — here it only
serves to avoid repeating the calculation four times.

The 25-day case is the important one because 25 × 80 is exactly 2000, the
cap. It is the **boundary**: the point where the behavior changes. A
one-character mistake in the condition — `>` instead of `>=`, or vice versa
— does not show up at 1 day or at 100 days, and it shows up at 25.

Testing a value below, one above and **the exact value at the edge** is the
habit that separates people who test from people who glance.

And it is worth noticing what the exercise did not ask for: at no point did
`0.80` appear. The entire calculation is done with integers, and the decimal
comma would only come in when printing the receipt.
:::
