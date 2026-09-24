---
source_hash: ae39e83296a4
title: "Conditionals"
number: 7
slug: condicionais
part: p1
kicker: "Eleven lending rules, forty seconds of talking, zero lines written down in thirty-one years."
goal: >-
  Write readable decisions with `if`, `elseif` and `match`, turn nesting
  into a staircase, and recognize the moment the staircase is asking for
  something else.
---

:::story The eleven conditions
"When can a person take a book home?" asked Tainá, with her notebook
open.

Vera answered without stopping her labeling:

"If she's a member. If she doesn't have an overdue book. If she doesn't owe
a fine over five reais. If she doesn't already have three books. If the
copy isn't from the reference section. If it's not the last copy of the
title — then it only goes out with authorization. If she's under twelve, a
guardian signs. If the book arrived this week, it stays on display for a
week. If it's exam season, the loan period drops to seven days. If it's
from Mr. Juvenal's collection, it doesn't go out at all, but nobody wrote
that down."

Pause.

"And if it's Mrs. Marlene, it goes out. Because she always brings it
back."

Tainá counted the lines in her notebook. There were eleven.

"You know all of that by heart?"

"I've been doing this for thirty-one years."

"And where is it written down?"

Vera stopped labeling for the first time.

"Nowhere."

At Tuesday's meeting, Márcia asked how many days the lending screen would
take. Tainá said eleven rules. Márcia heard "eleven" and wrote "2 days" in
the spreadsheet, because her question was about days.
:::

## The rule that lives in someone's head

This is not something peculiar to libraries. In every company there is at
least one rule that:

- is applied dozens of times a day;
- has exceptions nobody has listed;
- lives in the head of one or two people;
- and disappears when those people go on vacation.

The system usually implements the simplified version — the one someone
managed to describe in a one-hour meeting — and the rest keeps being
handled at the counter, by whoever knows.

:::note In your career
Extracting requirements from someone who does not know they have
requirements is a specific skill, and it is almost never taught.

What does **not** work: "send me the lending rule in writing". The person
will write down the three obvious conditions and forget the eight they
apply on autopilot.

What works:

1. **Ask them to narrate a concrete case**, from start to finish, with a
	 name and a date. The concrete pulls out the details the abstract hides.
2. **Ask about the exceptions instead of the rules**: "has it ever happened
	 that you let someone take a book even with one overdue?". That is where
	 Mrs. Marlene comes in.
3. **Read the rule back, out loud**, and wait for the correction. The person
	 will correct you on a detail they would not have remembered on their
	 own.
4. **Show the code running.** Nothing extracts requirements like watching
	 the system turn away someone they would let through.

Steps 3 and 4 are worth more than the first two, and they are the ones most
teams skip because they look like rework.
:::

## Every decision leaves two paths

```php title="loan.php" numbered
<?php

$available = true;

if ($available) {
    echo "Can lend\n";
} else {
    echo "Copy unavailable\n";
}
```

```text
Can lend
```

Parentheses are required around the condition, braces delimit the block.
People coming from Python find the braces strange; people coming from Java
feel at home.

When you leave out the `else`, the "no" path still exists — it just does
nothing. Being aware of that is what separates the correct program from the
program that only looks correct.

:::diagram type="flowchart" caption="Every decision has two paths, even when you only write one."
nodes:
  - { id: ini, type: start,    text: "Start" }
  - { id: d1,  type: decision, text: "available?" }
  - { id: sim, type: process,  text: "lend" }
  - { id: nao, type: process,  text: "(nothing)" }
  - { id: fim, type: start,    text: "End" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "yes" }
  - { from: d1,  to: nao, label: "no" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

An `if` without an `else` in a fine calculation means the result variable
keeps whatever value it already had — and if it had none, the program
carries on with an undefined variable and a warning nobody read.

### The braces are not optional

PHP lets you leave out the braces when the block has a single line.
Allowing that has already cost the world a lot of money:

:::compare left="What it looks like" right="What PHP reads" lang="php"
if ($ok)
    release();
    record();
---
if ($ok) {
    release();
}
record();
:::

`record()` always runs, because indentation means nothing to the
interpreter. It only means something to you.

:::key
**Always use braces**, including in one-line blocks. It is the easiest
style rule to justify in a code review, and any automatic formatter will
put them in for you.
:::

There is also an alternative syntax, with `:` and `endif`:

```php
<?php if ($available): ?>
    <span>Available</span>
<?php else: ?>
    <span>On loan</span>
<?php endif; ?>
```

It exists to be used **inside HTML**, where a stray brace in the middle of
the markup is hard to find. In pure PHP code, do not use it.

## The `elseif` staircase

```php title="situation.php" numbered
<?php

$days_late = 9;

if ($days_late <= 0) {
    $situation = 'on time';
} elseif ($days_late <= 7) {
    $situation = 'overdue';
} elseif ($days_late <= 30) {
    $situation = 'notified';
} else {
    $situation = 'suspended';
}

echo $situation, "\n";
```

```text
notified
```

Order is what makes the staircase work: the **first** true test wins, and
the following ones are not even evaluated. Nine is less than 30, but it is
also less than... no, it is not less than 7. It landed on the third step
because the first two answered no.

Reverse the order and see the damage:

```php title="situation_reversed.php" numbered
<?php

$days_late = 9;

if ($days_late <= 30) {
    $situation = 'notified';
} elseif ($days_late <= 7) {
    $situation = 'overdue';
} elseif ($days_late <= 0) {
    $situation = 'on time';
} else {
    $situation = 'suspended';
}

echo $situation, "\n";
```

```text
notified
```

The output is the same, by chance. But change `$days_late` to `0` and the
reversed version still says `notified`, because zero is also less than 30
and the first step swallows all the others. The last two `elseif`s have
become unreachable code — code that exists, is read in every review and
never runs.

:::key
An `elseif` staircase goes from the **most restrictive** case to the **most
general**. If you can swap two steps without changing the result, either
they do not overlap — and then the order really does not matter — or one of
them never runs.
:::

Notice the spelling: `elseif`, as one word. There is also `else if`, as two
words, which works in pure PHP code and **breaks** in the alternative syntax
with `endif`. Always use the single-word form.

## Nesting is expensive

Nesting an `if` inside an `if` is the most natural way to write the second
condition and the most expensive to maintain from the third one on:

:::compare left="Nested" right="As a staircase" lang="php"
if ($member) {
    if ($overdue === 0) {
        if ($fine <= 500) {
            $allowed = true;
        }
    }
}
---
if (!$member) {
    $allowed = false;
} elseif ($overdue > 0) {
    $allowed = false;
} elseif ($fine > 500) {
    $allowed = false;
} else {
    $allowed = true;
}
:::

Both do the same thing. The difference is that the left side grows to the
right with every new rule: with eleven rules, the final assignment ends up
forty-four spaces from the margin, and whoever reads it has to keep eleven
conditions in their head at once to know how they got there.

:::key
Deep indentation is not an aesthetic problem. It is a report of how many
conditions the reader has to hold at the same time to understand the line
they are reading. Three levels is the limit at which most people can still
follow.
:::

## The twelfth rule

Dedé wrote Vera's eleven rules as a staircase. It took an afternoon and
came to eighty-three lines, of which these are the first six:

```php title="can_lend.php" numbered
<?php

if (!$member) {
    $allowed = false;
} elseif ($overdue > 0) {
    $allowed = false;
} elseif ($fine_in_cents > 500) {
    $allowed = false;
} elseif ($open_loans >= 3) {
    $allowed = false;
} elseif ($is_reference) {
    $allowed = false;
} else {
    $allowed = true;
}
```

It worked. It spent a week in production without a single complaint.

The following Tuesday, Vera mentioned that in January the limit goes up
from three to five books, because it is the school holidays.

Dedé opened the file. The limit rule was on the fourth step — which he
found out by counting. To add "except in January", he had to decide whether
the exception went inside that condition or became a new step, and make
sure the order was still correct relative to the other ten.

He added an `&&` to the fourth step:

```php
} elseif ($open_loans >= 3 && !$holidays) {
```

Two weeks later, someone noticed that suspended readers were taking five
books in January.

The problem was not that the line was wrong — it was right for the question
it asked. The problem is that the staircase has no names. Eleven anonymous
conditions, told apart by position, and an `&&` added in the middle of one
of them is invisible in a review: the line keeps the same shape and no
other line changed.

:::art caption="The most complete business rule in the company usually lives in one person's head."
src="a-regra-de-negocio-mais-completa-da-empresa-costuma-morar-na-cabeca-de-uma-pessoa-so.png"
Minimalist editorial cartoon on a white background: an older librarian
behind a wooden counter, labeling books without looking, while she talks.
Coming out of her speech, an enormous flowchart draws itself in the air,
with dozens of decision diamonds and crossing arrows, filling half the
frame. Standing in front of the counter, an intern with a notebook that is
far too small, writing fast. Few elements, dry humor, tech-magazine
aesthetic.
:::

## Give the decision a name

The fix is not a better `elseif`. It is separating the decision about the
limit from the decision about lending:

```php title="can_lend.php (fixed)" numbered
<?php

$month = 1;
$suspended = true;

if ($suspended) {
    $limit = 0;
} elseif ($month === 1) {
    $limit = 5;
} else {
    $limit = 3;
}

echo "This reader's limit: ", $limit, "\n";
```

```text
This reader's limit: 0
```

Now there is a variable called `$limit`, with its own three-step staircase
that answers a single question. The lending step becomes
`$open_loans >= $limit`, and the January rule has an obvious place to live.

The suspended reader, who in the previous version was hidden in an `&&` in
the middle of a limit condition, is now the first step and returns zero.

## `match` is not `switch`

PHP has had `switch` forever, with two classic defects: it compares with
`==`, and it **falls through** — forgetting a `break` makes execution carry
on into the next case, with no warning.

Since PHP 8 there is `match`, which fixes both:

```php title="match.php" numbered
<?php

$status = 'in_transit';

$label = match ($status) {
    'available' => 'Free',
    'on_loan' => 'With a reader',
    'reserved', 'in_transit' => 'Unavailable',
    default => 'Unknown',
};

echo $label, "\n";
```

```text
Unavailable
```

Read the structure: `match` receives a value, compares it with each option
to the left of the arrow and **returns** whatever is to the right of the
first one that matches. Two options can share the same result, separated by
a comma. `default` catches whatever is left.

| | `switch` | `match` |
|---|---|---|
| Comparison | `==` | `===` |
| Falls through without `break` | yes | no |
| Returns a value | no | yes |
| Unforeseen case | ignored silently | error on the spot |

Table: There is no case where `switch` is better, except when an arm needs
to run several statements.

The last row deserves attention. A `match` with no `default` that receives
an unforeseen value does not ignore it: it breaks, with a clear message.

```text
$ php -r '$x = "new"; echo match($x) { "a" => 1, "b" => 2 };'
PHP Fatal error: Uncaught UnhandledMatchError:
Unhandled match case "new"
```

That looks hostile and it is the best part. When someone adds a new status
to the system and forgets to handle it, you find out immediately, and not
three weeks later because of a blank screen.

`match` also works without receiving any value, comparing against `true`.
Then it becomes a staircase that returns a value:

```php title="match_conditional.php" numbered
<?php

$suspended = false;
$month = 1;

$limit = match (true) {
    $suspended => 0,
    $month === 1 => 5,
    default => 3,
};

echo "Limit: ", $limit, "\n";
```

```text
Limit: 5
```

These are the same three rules as before, in five lines instead of seven,
and with a difference that matters more than size: `$limit` is assigned
**only once**, in one place. In the `if` version, it was assigned in three
places, and adding a fourth step meant remembering to assign it again.

## What counts as true

The list is worth repeating, because it is inside an `if` that it bites:

| False | True |
|---|---|
| `false`, `null` | `true` |
| `0`, `0.0` | any other number |
| `""` and `"0"` | any other text, including `"0.0"` |
| `[]` | a list with any item in it |

Table: `"0.0"` is true and `"0"` is false. It is the most arbitrary item on
the list, and the reason chapter @cap:conversao-automatica insists on
comparing explicitly.

:::summary
- Braces always; the `endif` syntax is only for inside HTML.
- Every `if` without an `else` leaves an implicit path — know which one it
	is.
- The `elseif` staircase goes from the most restrictive case to the most
	general; out of that order, steps become unreachable code.
- Deep nesting is a report of how many conditions the reader has to hold at
	once.
- An anonymous staircase hides changes: separate the decision and give it a
	name.
- `match` compares with `===`, does not fall through, returns a value and
	breaks on the unforeseen case.
- `match (true)` is a staircase that assigns the variable in one place.
:::

:::milestone
The program now decides. Vera's eleven rules are still on a staircase, but
for the first time in thirty-one years they exist somewhere other than her
head.
:::

:::exercise level=1
Write a condition that prints `"Return today"`, `"On time"` or `"Overdue"`
depending on the days left until the return. Do it in two ways, with `if`
and with `match (true)`.

:::answer
```php
<?php

$days_left = 0;

if ($days_left < 0) {
    $situation = 'Overdue';
} elseif ($days_left === 0) {
    $situation = 'Return today';
} else {
    $situation = 'On time';
}

$situation = match (true) {
    $days_left < 0 => 'Overdue',
    $days_left === 0 => 'Return today',
    default => 'On time',
};

echo $situation, "\n";
```

Order is what makes both work: `< 0` has to come before `=== 0`, because a
negative number is not equal to zero and would fall into `default` —
announcing "On time" to someone who is late.
:::

:::exercise level=2
Rewrite the nested snippet below as a staircase, keeping the messages. Then
say which of the two versions you would rather receive when adding a fourth
rule.

```php
if ($copy_exists) {
    if ($status === 'available') {
        if ($open_loans < 3) {
            $response = "Lent";
        } else {
            $response = "Limit reached";
        }
    } else {
        $response = "Unavailable";
    }
} else {
    $response = "Copy not found";
}
```

:::answer
```php
if (!$copy_exists) {
    $response = "Copy not found";
} elseif ($status !== 'available') {
    $response = "Unavailable";
} elseif ($open_loans >= 3) {
    $response = "Limit reached";
} else {
    $response = "Lent";
}
```

Notice that each condition was **inverted**: `if ($exists)` with the error
in the `else` became `if (!$exists)` with the error inside. That is what
lets you flatten the nesting.

The staircase is the version I would rather receive, for a mechanical
reason: to add the fourth rule, all it takes is a new step in the right
place. In the nested version, you have to open another level of braces in
the middle, re-indent everything inside it, and the change shows up in the
review as twelve modified lines instead of four.

And notice also what the two versions have in common, which is the defect
that remains: `$response` is text, so whoever uses that result will have to
compare sentences to know what happened.
:::

:::exercise level=3
Vera said that, in January, the limit goes up from three to five books —
but not for suspended readers. The same goes for July. Implement the limit
calculation in two ways: with `&&` inside the lending staircase, and with a
`$limit` variable of its own. Then say which one you would keep in the
project and what the choice costs.

:::answer
**Option 1 — inside the lending staircase:**

```php
} elseif ($open_loans >= (
    ($month === 1 || $month === 7) && !$suspended ? 5 : 3
)) {
    $allowed = false;
```

It works and fits on one line. It has three problems.

The holiday rule ended up hidden inside a condition whose subject is
something else. A ternary appeared inside a comparison inside an `elseif`,
which makes three levels of reasoning on one line. And the two conditions
joined with `&&` have nothing to do with each other: one is about the
calendar, the other is about the reader.

**Option 2 — with a name:**

```php
<?php

$month = 7;
$suspended = false;

$holidays = ($month === 1 || $month === 7);

$limit = match (true) {
    $suspended => 0,
    $holidays => 5,
    default => 3,
};

echo "Limit: ", $limit, "\n";
```

```text
Limit: 5
```

I would keep the second, for two concrete reasons.

**The rule got a name.** When Vera says in October that Children's Week
counts too, whoever touches it searches for `$holidays`, finds one line, and
changes one line.

**The suspended reader became explicit**, on the first step, returning
zero. In option 1 it was inside a ternary inside a comparison — which is
exactly where the real bug in this chapter's story hid.

**What it costs:** two more variables and one more indirection for whoever
reads the main flow. In a thirty-line program, that cost is real and may not
pay off. The honest question is not which version is more elegant, it is:
**how many times is this rule going to change?** This one has already
changed twice in two weeks.
:::

:::story Put an exception in there
On Thursday, Tainá showed Vera the new screen turning down a loan, with the
message *"Reader has pending items: 1 overdue book"*.

Vera read it, nodded and looked at the queue.

"Mrs. Marlene has one overdue."

"Then the system will turn her down."

Vera looked at the screen. She looked at Mrs. Marlene. She looked at the
screen again.

"Put an exception in there."

Tainá wrote it down in her notebook, in the "ask later" section, right
below *"what if the book has two authors?"*:

> *"rule no. 12: Mrs. Marlene"*
:::
