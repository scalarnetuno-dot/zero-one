---
source_hash: 7bea13b9a37f
title: "Encapsulation"
number: 19
slug: encapsulamento
part: p3
kicker: "The report said three copies were on loan twice. Six different places wrote to that column."
goal: >-
  Choose what stays public, write an object whose invalid state is
  impossible to reach from outside, use `readonly` for what does not change
  and recognize when `static` has become a global variable under another
  name.
---

:::story Six places
February's circulation report flagged three copies on loan twice at the
same time. Physically impossible: the book was on the shelf, and Vera
brought one of them to the meeting as proof.

Dedé searched the System for whoever wrote to the copies' `status` column.

```text
$ grep -rn "status *=" *.php | wc -l
6
```

"Six," he said.

"Six functions?"

"Six places. The lending screen, the return screen, the renewal screen, the
importer, a fix-up script someone ran in 2019 and left in the folder, and
the report."

Tainá took a moment over the last one.

"The report writes?"

"The report fixes things. When it finds a strange row, it corrects it."

"Corrects it for what?"

"So it comes out looking nice."
:::

## `public` is permission forever

The `Copy` the project has today prevents nothing:

```php title="src/Catalog/Copy.php" numbered
<?php

namespace CasaAmarela\Catalog;

class Copy
{
    public function __construct(
        public int $accession,
        public Book $book,
        public string $status = 'good',
    ) {}
}
```

Every property is public, and public means that any line in any file can
write anything:

```php
$copy->status = 'on_laon';
$copy->status = 'dunno';
$copy->accession = -3;
```

No warning. Three statuses that do not exist, a negative accession number,
and the object keeps circulating through the program as if it were whole.

That is the same disease as the System's `status` column, one floor up. The
problem was never the writing itself — it was there being six places with
permission to write, and none of them with the obligation to check.

:::key
`public` is not "the default". It is a decision, and an almost
irreversible one: the day you want to close the property, you will need to
find and fix everyone who learned to write to it.

Start closed. Opening later costs one line; closing later costs a meeting.
:::

## `private`: the sign PHP enforces

Change one word:

```php title="src/Catalog/Copy.php" numbered
    public function __construct(
        public int $accession,
        public Book $book,
        private string $status = 'good',
    ) {}
```

And attempts from outside stop working:

```php
$copy->status = 'dunno';
```

```text
Fatal error: Uncaught Error: Cannot access private property
CasaAmarela\Catalog\Copy::$status
```

Reading stops too — `private` closes the door both ways.

There are three levels, and day to day you use two:

| | Who can reach it |
|---|---|
| `public` | any code, from anywhere |
| `protected` | the class itself and the ones that inherit from it |
| `private` | only the class itself |

Table: `protected` is a choice for someone who has already decided the
class will have descendants. Until it does, `private` is the right answer.

:::pitfall
PHP's visibility is enforced by the language, and that is why it works —
it is different from the convention in other languages, where an
underscore in front of the name politely asks everyone not to touch it.

But it applies per **class**, not per object. A `Copy` method can read the
private `status` of *another* `Copy` received as a parameter. That surprises
people coming from outside and it is what makes it possible to write an
honest `equals()`.
:::

## Invariant

Closing the property is useless if the object can be born wrong.

:::term Invariant
A statement about the object that has to be true **from birth until the
end**, whatever happens in between.

It is not form validation, which happens once at the entrance. It is the
class's permanent promise: if it holds, no code that receives this object
needs to check again.
:::

Casa Amarela's `Copy` has three:

1. the accession number is a positive number;
2. the status is one of the five the catalog recognizes;
3. a copy on loan cannot be lent again.

The first two are about birth. The third is about change.

## The constructor that refuses

```php title="src/Catalog/Copy.php" numbered
<?php

namespace CasaAmarela\Catalog;

class Copy
{
    private const STATUSES = [
        'good', 'on_loan', 'damaged', 'in_repair', 'lost',
    ];

    public function __construct(
        public int $accession,
        public Book $book,
        private string $status = 'good',
    ) {
        if ($accession <= 0) {
            throw new \InvalidArgumentException(
                "Invalid accession: {$accession}"
            );
        }

        if (!in_array($status, self::STATUSES, true)) {
            throw new \InvalidArgumentException(
                "Unknown status: {$status}"
            );
        }
    }
}
```

Three new things on the same screen, and all three are short.

`private const STATUSES` is a **class constant**: a fixed value that
belongs to the class instead of to each object. It is written once and read
with `self::STATUSES` — `self` means "this class right here".

`throw` interrupts the method on the spot and hands the problem to whoever
called it. It is the same mechanism as `PDOException`, now starting from
your code. `InvalidArgumentException` is the type PHP offers to say "the
argument you passed is outside what was agreed".

The backslash in front of `\InvalidArgumentException` is the same as in
`\PDO`: the class lives in the root, and this file has a namespace.

```php
$copy = new Copy(-3, $book);
```

```text
Fatal error: Uncaught InvalidArgumentException: Invalid accession: -3
```

The object never existed. There is not, anywhere in the program, a `Copy`
with a negative accession number — and that is a statement about the whole
system that fits in four lines.

## Getters and setters are not mandatory

The reflex of someone who learned object orientation in a course is this:

```php
public function getStatus(): string { return $this->status; }
public function setStatus(string $s): void { $this->status = $s; }
```

With those two methods, the property is public again — with two more lines,
a worse name and the appearance of being protected. `setStatus` accepts
`'dunno'` exactly as `public` did.

Ask two things before writing each one:

**Does the outside need it?** If nobody calls it, do not write it. A public
method nobody calls is still a promise someone can hold you to tomorrow.

**Does the change have a name?** A copy does not "have its status changed to
on loan". It **is lent**. The method's name is the name of the event, and
that is where the rule finds a place to live.

## `readonly`: the data that does not change its mind

An accession number does not change. Once the label is stuck on the book,
that number belongs to that copy until the end.

```php title="src/Catalog/Copy.php" numbered
    public function __construct(
        public readonly int $accession,
        public readonly Book $book,
        private string $status = 'good',
    ) {
```

```php
$copy->accession = 9;
```

```text
Fatal error: Uncaught Error: Cannot modify readonly property
CasaAmarela\Catalog\Copy::$accession
```

`readonly` allows writing once, from inside the class, and refuses
everything else. With it, `public` stops being dangerous: reading breaks
nothing, and writing is no longer possible.

It is the combination that solves most cases: **public and `readonly` for
what does not change, private for what does**.

:::key
The question that separates the two is always the same, and it is not
technical: *in the real world, does this change?*

The accession number does not. That copy's book does not. The status
changes all the time — and that is why it is the only one that needs a door
with a name.
:::

## One door for each change

The third invariant is missing, the one about change rather than birth.

```php title="src/Catalog/Copy.php" numbered
    public function status(): string
    {
        return $this->status;
    }

    public function isAvailable(): bool
    {
        return $this->status === 'good';
    }

    public function lend(): void
    {
        if ($this->status !== 'good') {
            throw new \RuntimeException(
                "Copy {$this->accession} can't go out: {$this->status}"
            );
        }

        $this->status = 'on_loan';
    }

    public function return(string $statusOnReturn = 'good'): void
    {
        if ($this->status !== 'on_loan') {
            throw new \RuntimeException(
                "Copy {$this->accession} is not on loan"
            );
        }

        if (!in_array($statusOnReturn, self::STATUSES, true)) {
            throw new \InvalidArgumentException(
                "Unknown status: {$statusOnReturn}"
            );
        }

        $this->status = $statusOnReturn;
    }
```

Now the column has a single door, and the door checks:

```php
$copy->lend();
$copy->lend();
```

```text
Fatal error: Uncaught RuntimeException:
Copy 2117 can't go out: on_loan
```

The three copies lent twice in February's report stop being possible — not
because the team started being more careful, but because there is no longer
a path that leads there.

And notice `return`: it accepts the status on return, because books come
back torn. What it does not accept is any old text, and it does not accept
returning what never went out. (Yes, `return` is a reserved word — and PHP
has allowed it as a method name since version 7.)

:::note In your career
"Six places write to that column" is a sentence you will say, and the answer
is almost always "then make it seven". A seventh screen needs to change the
status, nobody wants to touch the existing six, and the deadline is Tuesday.

The path that tends to work is not asking for a refactoring: it is writing
the door, using it in the new screen, and migrating one of the six each time
someone has to open that file for another reason. The conversation changes
when you can say "it's four today" in a meeting where, last month, it was
six.

Keep the number. Technical debt without a number becomes an opinion, and
opinion loses to deadlines every single time.
:::

## `static`: a tool or a global variable in disguise

A `static` property belongs to the class, not the object: there is only
one, shared by everyone.

```php
class Copy
{
    public static int $lentToday = 0;
}
```

That is not a catalog counter. It is a global variable with a prettier name
— any code can add to it, nobody has to say why, and the value does not
belong to any particular object.

The test that separates legitimate use from disguise is short: **does the
value depend on who is using the system right now?** If it does, `static` is
the wrong place.

A `static` holding the day's currency conversion is debatable. One holding
the logged-in user is a bug waiting for a server that serves two requests at
the same time — and that is how, in production, Vera sees Neide's name in
the corner of the screen.

`static` methods have the same smell when they hold state, and they are
harmless when they do not: a conversion function that depends only on its
arguments can be `static` with no problem at all.

## The public surface is a promise

Everything public is a promise to whoever uses the class: *this will keep
existing, with this name and this behavior*.

The `Copy` we have now promises six things — `accession`, `book`,
`status()`, `isAvailable()`, `lend()`, `return()` — and hides one: that the
status is a `string`. Tomorrow it can become something else without a
single line outside changing, because nobody outside has any way of knowing
what it is.

That is what encapsulation bought. It is not organization; it is the
freedom to change your mind later.

There is a word that makes the opposite promise. `final` in front of a class
says nobody can inherit from it, and in front of a method, that nobody can
swap its behavior. It reduces what you promise, and so it increases what you
can change.

:::tree title="Where we are now"
catalog/
  src/
    Catalog/
      Book.php
      Copy.php       # readonly + private status with a door
    Readers/
      Reader.php
    Legacy/
      Book.php
  connection.php
  list.php
  lend.php
  receipt.php
:::

:::milestone
End of Part 3. The project has a name, declared dependencies, classes with
an address and objects that refuse to be born wrong. One file became thirty
— and thirty files with a contract are a different thing from thirty loose
files.
:::

:::summary
- `public` is permanent permission: start closed, open up when someone needs
  it.
- `private` is enforced by the language and applies per class, not per
  object.
- An invariant is what has to be true from birth to the end; the constructor
  is where it starts to hold.
- `throw` in the constructor stops the invalid object from existing anywhere
  in the program.
- Automatic getters and setters hand the property back to the public with
  more lines.
- `readonly` makes `public` safe for what does not change.
- A change of state goes through a method named after the event, and the
  method checks first.
- A `static` that depends on who is using the system is a global variable in
  disguise.
- What is public is a promise; what is private is the freedom to change
  later.
:::

:::checkpoint
You choose visibility with an argument, write a class whose invalid state
has no path to it, use `readonly` on what does not change, expose changes
through methods named after events and recognize a `static` that is storing
request state.
:::

:::exercise level=1
The `Reader` class has `name`, `document` and `registeredAt`. Decide the
visibility of each and justify it in one sentence.

Then answer: which of the three would you make changeable, and through which
method?

:::answer
```php title="src/Readers/Reader.php" numbered
<?php

namespace CasaAmarela\Readers;

class Reader
{
    public function __construct(
        private string $name,
        public readonly string $document,
        public readonly string $registeredAt,
    ) {}
}
```

`document` is `readonly`: a person's taxpayer ID does not change, and if it
was typed wrong the case is a record correction, not a data change.

`registeredAt` is `readonly` for the same reason, only stronger: it is a
historical fact. The date of something that has already happened does not
change.

`name` is the only one that really changes — marriage, spelling
corrections, a chosen name. That is why it stays private and gets a door
named after the event, `correctName()` or `rename()`, not `setName()`. The
door is the place to refuse an empty name.
:::

:::exercise level=2
Write the `Fine` class with `cents` and `daysLate`, which:

1. refuses to be born with negative days;
2. refuses to be born with negative cents;
3. exposes `formatted()` returning something like `R$ 7,20`;
4. exposes `waive()`, which zeroes the amount and cannot be undone.

Then say which invariant `waive()` needs to respect.

:::answer
```php title="src/Loans/Fine.php" numbered
<?php

namespace CasaAmarela\Loans;

class Fine
{
    public function __construct(
        private int $cents,
        public readonly int $daysLate,
    ) {
        if ($daysLate < 0) {
            throw new \InvalidArgumentException(
                "Negative days late: {$daysLate}"
            );
        }

        if ($cents < 0) {
            throw new \InvalidArgumentException(
                "Negative fine: {$cents}"
            );
        }
    }

    public function cents(): int
    {
        return $this->cents;
    }

    public function formatted(): string
    {
        $reais = $this->cents / 100;

        return 'R$ ' . number_format($reais, 2, ',', '.');
    }

    public function waive(): void
    {
        $this->cents = 0;
    }
}
```

The invariant `waive()` needs to respect is the same as the constructor's:
**cents is never negative**. Zeroing respects it.

This is where the most common mistake of people who start validating lives:
writing the checks in the constructor and forgetting that every method that
changes state has to leave the object as valid as it found it. A
`discount(int $cents)` written carelessly takes the fine to minus twenty,
and the constructor has no way of stopping it — it has already run.

`daysLate` is `readonly` because it is a fact about the loan, and waiving
the fine does not make the delay stop having existed. That distinction shows
up in Casa Amarela's report: Vera needs to know how many delays there were,
even the waived ones.
:::

:::exercise level=3
This code runs and prints a wrong number. Say which one, why, and fix it
without removing the counter.

```php title="counter.php" numbered
<?php

class Copy
{
    public static int $lent = 0;

    public function __construct(
        public readonly int $accession,
        private string $status = 'good',
    ) {}

    public function lend(): void
    {
        $this->status = 'on_loan';
        self::$lent++;
    }
}

$a = new Copy(2117);
$b = new Copy(843);

$a->lend();
$a->lend();
$b->lend();

echo Copy::$lent, "\n";
```

:::answer
It prints `3`. The catalog lent two copies.

There are two bugs, and they hide behind each other.

The first is the missing door: `lend()` does not check the status, so
calling it twice on the same copy goes through. With the chapter's check,
the second call would be refused and the counter would stop at 2 — by
accident.

The second is the counter itself. `public static` means that any line in
any file can add, subtract or reset it, and nothing forces that number to
have any relation to reality. It is a parallel total, which starts out
right and diverges at the first path someone forgets to count — exactly the
`quantity` column from chapter @cap:o-que-vamos-construir, now in memory.

The fix that keeps the counter:

```php
    public function lend(): void
    {
        if ($this->status !== 'good') {
            throw new \RuntimeException('Copy unavailable');
        }

        $this->status = 'on_loan';
        self::$lent++;
    }
```

And the fix that really solves it is not to store the total: count the open
rows in `loans` when someone asks. A counted number does not drift from
reality — and a `static` that vanishes with every new request is not even a
total, because it resets along with the process.
:::
