---
source_hash: 25834ca1a1ed
title: "Variables and types"
number: 4
slug: variaveis-e-tipos
part: p1
kicker: "Thirty-one outstanding on the screen, twenty-seven on paper. The four extras owed exactly zero reais."
goal: >-
  Store values in the five everyday types, inspect them with `var_dump`,
  choose between single and double quotes, and tell absence apart from
  empty and from zero.
---

:::story Twenty-seven
Vera printed the outstanding-items report and checked it by hand, with a
ruler, as she has done since 1995.

The report said thirty-one. The ruler said twenty-seven.

"There are four extra here."

"Maybe you skipped a line," ventured Tainá.

Vera checked again, with the ruler, in no hurry at all, while Tainá
watched. Twenty-seven.

It took Tainá an hour to find what the four extra names had in common: all
of them had returned **on time**. Their fine had been calculated, recorded
and saved with the value R$ 0,00.

This is how the System asked whether the fine had already been processed:

```php
if (!$fine) {
    $outstanding = true;
}
```

And zero, in PHP, is false.

"The math is right," said Dedé, when he saw it. "It's the report that
doesn't know the difference between 'owes nothing' and 'nobody calculated
it'."

Vera wrote it down in her notebook. Then she crossed it out and wrote it
again, in different, bigger handwriting:

> *"the system needs to know the difference between zero and nothing"*

"How many systems does that apply to?" asked Tainá.

"Every one I've ever used."
:::

This chapter is about storing values and knowing what was stored. The
story above is about the second part, which is the part that usually goes
missing.

## `$` in front of everything

In PHP, every variable starts with `$`, and none of them needs to be
declared before receiving a value:

```php title="first.php" numbered
<?php

$title = "O Cortiço";
$copies = 3;

echo $title, "\n";
echo $copies, "\n";
```

```text
O Cortiço
3
```

There is no line saying "I am going to create a variable called `$title`
of type text". The assignment creates the variable and the type comes along
with the value.

The `$` has little ceremony and a good side effect: `$title` is always a
variable, anywhere in the file. There is no ambiguity between a variable
name, a function name and a reserved word of the language. On the other
hand, forgetting the `$` is a mistake PHP is slow to notice, because
`title` without the dollar sign is valid syntax — it is the name of a
constant it will look for and not find.

About names: letters, digits and underscores are allowed, and the first
character cannot be a digit. Upper and lower case are different — `$title`
and `$Title` are two variables. The convention in modern PHP is
`$compoundName`, in *camelCase*, even though a lot of old code uses
`$compound_name`.

## The five everyday types

```php title="types.php" numbered
<?php

$title = "O Cortiço";
$copies = 3;
$weight_kg = 0.42;
$available = true;
$returned_at = null;

var_dump($title);
var_dump($copies);
var_dump($weight_kg);
var_dump($available);
var_dump($returned_at);
```

```text
string(10) "O Cortiço"
int(3)
float(0.42)
bool(true)
NULL
```

Five values, five types. `var_dump` prints the type and the value, and that
is why it is the most used tool for debugging PHP: with `echo`, the five
would come out as `O Cortiço`, `3`, `0.42`, `1` and nothing.

| Type | What it holds | In the catalog |
|---|---|---|
| `string` | text | title, author, ISBN, reader's name |
| `int` | whole number | accession, days late, quantity |
| `float` | number with decimal places | weight, percentage, average |
| `bool` | `true` or `false` | whether the copy is available |
| `null` | the absence of a value | return date of someone who hasn't returned |

Table: `true`, `false` and `null` can be written in upper case, but the
convention is lower case.

Notice the `string(10)` in the output, for a nine-letter word. The number
in parentheses is not the letter count: it is the **byte** count, and the
`ç` takes up two. That is a consequence of how text is stored, and for now
it is enough to know that the number exists and that it does not always
match what you count by eye.

There are two other important types — `array` and `object` — which hold
several things at once instead of just one. They come in when there are
several things to hold.

:::key
Whenever you are not sure what is inside a variable, the answer costs one
line: `var_dump($x);`. It is faster than reasoning, more reliable than
remembering, and the only way to tell the number `3` from the text `"3"` —
which look alike on screen and behave differently.
:::

## Single and double quotes hold different things

Both create text, and they stop being equivalent as soon as you put a
variable inside:

```php title="quotes.php" numbered
<?php

$title = "O Cortiço";

echo "We have: $title\n";
echo 'We have: $title\n';
```

```text
We have: O Cortiço
We have: $title\n
```

The first line uses **double quotes**. Inside them, PHP looks for variable
names and replaces each one with its value. That is called
**interpolation**. The backslash is interpreted too: `\n` became a real
line break.

The second line uses **single quotes**. Inside them, almost nothing is
interpreted: `$title` came out as six literal characters, and `\n` came
out as two. That is why the output ended up all on one line.

When the variable's name touches another letter, PHP cannot guess where it
ends:

```php title="braces.php" numbered
<?php

$kind = "book";

echo "Three {$kind}s\n";
```

```text
Three books
```

Without the braces, PHP would look for a variable called `$kinds`, would not
find it and would warn you. With `{}`, the boundary is explicit. Using
braces whenever there is interpolation saves you the decision.

:::key
Rule of thumb: **single quotes when the text is literal, double quotes when
there is a variable inside.** It is not a performance question — the
difference is imperceptible. It is a question of stating intent: single
quotes tell the reader there is nothing to be replaced in there.
:::

## `null` is not empty, and empty is not zero

```php title="three_statements.php" numbered
<?php

$returned_at = null;  // hasn't returned yet
$note = "";           // returned, and there was nothing to note
$fine = 0;            // returned, and owes nothing
```

Three values, three completely different statements about the world. And,
for a simple `if`, all three behave the same way: none of them gets in.

```php title="the_bug.php" numbered
<?php

$fine = 0;

if ($fine) {
    echo "has a fine\n";
} else {
    echo "no fine\n";
}
```

```text
no fine
```

The `if` did not receive `true` or `false`: it received the number zero.
When that happens, PHP converts the value to true or false before deciding
— and zero is false.

It is exactly the bug in Vera's report, written backwards. The System asked
`if (!$fine)`, which is "if the fine is false", thinking it was asking "if
the fine does not exist".

There are three tools for asking the right question, and they are not
interchangeable:

```php title="three_questions.php" numbered
<?php

$fine = 0;

var_dump(isset($fine));    // does the variable exist and isn't null?
var_dump(empty($fine));    // is the value one of the "falsy" ones?
var_dump(is_null($fine));  // is the value exactly null?
```

```text
bool(true)
bool(true)
bool(false)
```

Read slowly, because the three answers are different for the same value.

`isset` answered `true`: the variable exists and is not null. `empty`
answered `true`: zero is a falsy value. `is_null` answered `false`: zero is
not null, zero is zero.

Changing the value to `null`, the three answers flip:

```text
bool(false)   isset  — doesn't exist, or exists and is null
bool(true)    empty  — null is falsy
bool(true)    is_null
```

:::key
`isset()` asks "does it exist and is it not null?". `empty()` asks "is it a
falsy value?". And **neither of them** asks "does it have content?".

When what you need is to tell absence from zero — which is the case of
Vera's fine — the question is `=== null`, and no other one will do.
:::

The fix for the report is two separate questions, each one saying what it
wants to know:

```php title="explicit.php" numbered
<?php

$fine = 0;

if ($fine === null) {
    echo "nobody has calculated it yet\n";
}

if ($fine === 0) {
    echo "calculated, and owes nothing\n";
}
```

```text
calculated, and owes nothing
```

The three equals signs compare value **and** type, converting nothing. Two
signs would do something different, and that difference makes for a story
good enough to fill the whole next chapter.

:::practice
Run `three_questions.php` above changing the value of `$fine` to: `null`,
`0`, `""`, `"0"`, `false` and `"a"`. Write down the three answers for each.

Six lines of notes that answer, in one go, about fifteen doubts that will
come up over the next few weeks — and it is faster to look up than the
documentation.
:::

## Values that cannot change

```php title="constants.php" numbered
<?php

const LOAN_DAYS = 14;
const LIMIT_PER_READER = 3;

echo "Loan period: ", LOAN_DAYS, " days\n";
```

```text
Loan period: 14 days
```

A **constant** is a named value that cannot be reassigned. Notice two
differences: there is no `$` in front, and the name is in upper case with
underscores — a universal convention in PHP, not a requirement of the
language.

Trying to change one is an error:

```text
PHP Fatal error: Cannot redefine constant LOAN_DAYS
```

There is also `define('LOAN_DAYS', 14)`, which does almost the same. The
practical difference: `const` is resolved when the file is read and only
accepts a fixed value; `define()` runs during execution and accepts a name
or a value computed on the spot. Use `const` by default.

The value of replacing `14` with `LOAN_DAYS` is not saving keystrokes. It
is that the number now exists **in one place only**. When Vera decides to
change the loan period to twenty-one days during school holidays, the
change is one line — and you will not spend the afternoon hunting down every
`14` in the system, discovering that some were loan days and others were the
number of shelves.

:::note In your career
When someone from the business side says a number in the system is wrong,
the chance that this person is right is high — and the chance that the
system is technically working is high too. Both at the same time.

Vera cannot program and she found a bug that spent fifteen years in
production, because she had two things no automated test has: the right
number, counted by hand, and the stubbornness to check.

The right reflex when you receive this kind of report is not to explain why
the system is right. It is to ask for **both numbers and the list**. The
difference between 31 and 27 is an abstraction; the four extra names are a
direct path to the line of code.
:::

:::summary
- Every variable starts with `$` and does not need to be declared: the
	assignment creates the variable and sets its type.
- The five everyday types are `string`, `int`, `float`, `bool` and `null`.
- `var_dump` shows type and value; `echo` shows only the value.
- Double quotes interpolate variables and interpret `\n`; single quotes do
	not.
- `null` is absence, `""` is empty, `0` is zero — three different
	statements that a simple `if` treats as one.
- `isset` asks "does it exist?", `empty` asks "is it falsy?"; to tell
	absence from zero, use `=== null`.
- `const` gives a name to a fixed value and puts it in one place.
:::

:::checkpoint
You declare variables of the five types, find out the type of any of them
with `var_dump`, choose quotes by intent and explain in one sentence the
difference between `null`, `""` and `0`.
:::

:::exercise level=1
Create variables to describe a copy — accession number, title, whether it
is available, and the return date — and print the type of each one.

:::answer
```php
<?php

$accession = 2117;
$title = "O Cortiço";
$available = false;
$returned_at = null;

var_dump($accession, $title, $available, $returned_at);
```

```text
int(2117)
string(10) "O Cortiço"
bool(false)
NULL
```

`var_dump` accepts several values at once, separated by commas.

And notice the choice for `$returned_at`: `null` is a statement — the loan
is open. If it were `""`, it would be saying "returned on an unknown date",
which is something else, and almost always an error from importing old data.
:::

:::exercise level=2
Without running it, write down what each line prints. Then run it and
check.

```php
<?php

$n = 5;
$text = "books";

echo "We have $n $text\n";
echo 'We have $n $text\n';
echo "We have {$n}00 $text\n";
```

:::answer
```text
We have 5 books
We have $n $text\nWe have 500 books
```

The second line is the one that catches almost everyone, and for two
reasons at once: the variables came out literally **and** so did the `\n`,
so the third line started glued to the second.

The third shows why braces exist. Without them, `"$n00"` would make PHP look
for a variable called `$n00`.
:::

:::exercise level=3
The snippet below came from the System. It decides whether a loan goes on
the outstanding list. Point out the bug and write the correct version.

```php
$fine = calculateFine($loan);

if (!$fine) {
    $outstanding = true;
} else {
    $outstanding = false;
}
```

:::answer
The bug is the `!$fine`, which asks "is the fine a falsy value?" when the
intent was to ask "has the fine not been calculated yet?".

Four different values go through that `if` as if they were the same:
`null` (not calculated), `0` (calculated and owes nothing), `""` (empty text
came from somewhere) and `false` (the function failed). Only the first
should mark it as outstanding.

```php
$fine = calculateFine($loan);

$outstanding = ($fine === null);
```

Two observations about the corrected version.

The first: the `if/else` is gone. When both branches only assign `true` and
`false` to the same variable, the comparison already is the answer — and a
comparison read aloud sounds like the business rule: *outstanding is when
the fine is null*.

The second, and the most important: if `calculateFine` can return `false`
on failure, the corrected version marks that loan as **not outstanding**,
and the problem becomes invisible. A function that returns sometimes a
number, sometimes `null`, sometimes `false` forces the caller to guess which
of the three happened. The real fix is for the function to return one thing
only — and that is why it will come back in this book.
:::

:::story Why would a contract be worth zero?
At Vertexo, that same week, Cléber asked for a new indicator on the
executive dashboard: "total outstanding contracts".

Dedé asked what counted as outstanding.

"The ones that are outstanding."

"Does a contract worth zero count?"

Cléber looked at him with the expression of someone who has been asked
whether water is wet.

"Why would a contract be worth zero?"

Three weeks later, the sales team started registering complimentary
contracts, worth zero, for clients on a trial period.

The executive dashboard started showing seventeen outstanding contracts.
There were thirty-four.

Dedé had already written `=== null`.
:::
