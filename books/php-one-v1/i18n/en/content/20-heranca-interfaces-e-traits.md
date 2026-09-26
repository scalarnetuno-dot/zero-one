---
source_hash: b2dc06b01945
title: "Inheritance, interfaces and traits"
number: 20
slug: heranca-interfaces-e-traits
part: p4
kicker: "The whiteboard had three boxes when Vera arrived. It had ten when she left, and she didn't draw any of them."
goal: >-
  Choose between inheritance, interface, trait and composition with a
  criterion you can defend — and recognize, before drawing the third box,
  when the hierarchy is going to explode.
---

:::story And the imported children's textbook
On the whiteboard there was a box that said `Book` and three arrows coming
out of it: `ChildrensBook`, `Textbook`, `ReferenceBook`.

"Children's books don't go out for fourteen days, they go out for seven,"
Dedé explained. "Reference books don't go out."

Vera was there for another reason, waiting for Tainá to check a list, and
looked at the whiteboard the way you look at a new road sign.

"And the children's textbook?"

Dedé drew a fourth box.

"And the imported ones? Imported books don't go out, whatever they are."

The fourth box got a fifth one next to it.

"And the imported children's textbook," said Vera, without the intonation
of a question.

Tainá counted the boxes.

"Eight."

"Ten," said Vera. "You forgot the reference ones."
:::

:::art caption="Every class hierarchy fits on the whiteboard until the librarian arrives."
src="toda-hierarquia-de-classes-cabe-no-quadro-ate-a-bibliotecaria-chegar.png"
Minimalist editorial cartoon on a white background: a whiteboard where a
clean diagram begins — a "Book" box with three arrows to "Children's",
"Textbook" and "Reference" — which, on the right half, degenerates into ever
smaller and more cramped boxes: "ChildrensTextbook", "ChildrensImported",
"ChildrensTextbookImported", with crossed arrows escaping over the edge. The
developer, marker in hand, has run out of room and is writing on the frame.
Leaning against the door frame, an older librarian with glasses and folded
arms dictates the next combination without changing her expression. An
intern counts the boxes on her fingers. Few elements, dry humor,
tech-magazine aesthetic.
:::

## `extends` is a kinship you cannot undo

Inheritance is the oldest of the three mechanisms and the easiest to write:

```php title="src/Catalog/ChildrensBook.php" numbered
<?php

namespace CasaAmarela\Catalog;

class ChildrensBook extends Book
{
    public function loanDays(): int
    {
        return 7;
    }
}
```

`extends` says: this class starts with everything the one above has —
properties, methods, constructor — and adds or replaces whatever it wants.

The problem does not show up at the first box. It shows up at the third.

Children's, textbook and imported are three **independent**
characteristics: a book can have any combination of them. Since each class
can only extend one other — PHP has no multiple inheritance, and `extends`
accepts a single name — covering every combination requires one class per
combination.

| Characteristics | Classes needed |
|---|---|
| 1 | 2 |
| 2 | 4 |
| 3 | 8 |
| 4 | 16 |

Table: Each new characteristic **doubles** the whiteboard. That is what Vera
did in forty seconds without knowing what a class was.

:::key
Inheritance works well for variation along **a single axis**, when the
options are exclusive: it is either one or the other, never both.

If two characteristics can appear together, they are not subclasses. They
are data.
:::

## What a subclass promises

There is a rule more important than counting boxes, and it is easy to
state: **wherever the parent is accepted, the child has to work**.

If a function receives a `Book` and the program passes a `ReferenceBook`,
the function cannot break. It does not know, and should not need to know,
which of the two arrived.

See what happens when the rule is broken:

```php title="src/Catalog/ReferenceBook.php" numbered
<?php

namespace CasaAmarela\Catalog;

class ReferenceBook extends Book
{
    public function loanDays(): int
    {
        throw new \RuntimeException('Reference books stay here');
    }
}
```

It looks reasonable: reference books really do not go out. But now every
function that received a `Book` and asked for the loan period has a new way
to die — and the only way to protect itself is to check the type first:

```php
if ($book instanceof ReferenceBook) {
    continue;
}
```

That `if` is going to show up in five places, and the sixth will be missing
it. The inheritance that promised to remove conditionals has just spread
one around.

:::pitfall
The "**is a**" test is the one taught first and the one that fails most. A
reference book *is a* book, in everyday language — and even so it does not
work as one.

The test that works is a different one: *if I swap the parent for the child,
does something that used to work stop working?* If the answer is yes, the
inheritance is lying, and the lie will send its bill through an `if` someone
forgot.
:::

## Interface: the contract without the kinship

Not everything that behaves the same needs to be related.

During the migration, Casa Amarela has two catalogs live at the same time:
the System's, which keeps serving the front desk, and the new one. The
circulation report needs to count copies from both.

The two classes have nothing in common on the inside — one reads
`accession` and the other reads `copy_code` — and they need to answer the
same three questions.

```php title="src/Circulation/Lendable.php" numbered
<?php

namespace CasaAmarela\Circulation;

interface Lendable
{
    public function identifier(): string;

    public function isAvailable(): bool;

    public function loanDays(): int;
}
```

An interface is a list of signatures without any body. It does not say how
things are done; it says what must exist.

```php title="src/Catalog/Copy.php" numbered
<?php

namespace CasaAmarela\Catalog;

use CasaAmarela\Circulation\Lendable;

class Copy implements Lendable
{
    // ... constructor from the previous chapter

    public function identifier(): string
    {
        return "accession {$this->accession}";
    }

    public function isAvailable(): bool
    {
        return $this->status === 'good';
    }

    public function loanDays(): int
    {
        return $this->book->classification->loanDays();
    }
}
```

PHP enforces the whole contract, at the moment the class is loaded:

```text
Fatal error: Class Copy contains 1 abstract method and must
therefore be declared abstract or implement the remaining methods
(Lendable::loanDays)
```

And the code that uses it does not need to know which catalog the item came
from:

```php title="report.php" numbered
<?php

use CasaAmarela\Circulation\Lendable;

function countAvailable(array $items): int
{
    $total = 0;

    foreach ($items as $item) {
        if ($item instanceof Lendable && $item->isAvailable()) {
            $total++;
        }
    }

    return $total;
}
```

:::key
An interface is the mechanism Laravel is going to use for almost everything,
and this is why: it lets you write code against **what something does**
instead of against **what it is**.

A class can implement as many interfaces as it wants. The limit of one only
applies to `extends`.
:::

## Abstract class: a contract with part of the how

An interface holds no code. When the implementations share a real piece,
there is a middle ground:

```php title="src/Circulation/CatalogItem.php" numbered
<?php

namespace CasaAmarela\Circulation;

abstract class CatalogItem implements Lendable
{
    abstract public function loanDays(): int;

    public function loanPeriodText(): string
    {
        $days = $this->loanDays();

        return $days === 1 ? '1 day' : "{$days} days";
    }
}
```

An `abstract class` cannot be instantiated: `new CatalogItem()` is an
error. An `abstract public function` has no body — whoever inherits is
obliged to write it.

The difference fits in a line: **an interface says what; an abstract class
says what and part of how**. And the abstract class uses up your single
`extends`, which is a real price.

## Trait: copy-and-paste done by the compiler

The third mechanism is the most literal of the three. A `trait` is a block
of code that is **copied into** the classes that use it.

```php title="src/Circulation/RecordsHistory.php" numbered
<?php

namespace CasaAmarela\Circulation;

trait RecordsHistory
{
    private array $history = [];

    public function record(string $event): void
    {
        $this->history[] = date('Y-m-d H:i:s') . ' ' . $event;
    }

    public function history(): array
    {
        return $this->history;
    }
}
```

```php title="src/Catalog/Copy.php" numbered
class Copy implements Lendable
{
    use \CasaAmarela\Circulation\RecordsHistory;
```

:::pitfall
This `use` is **not** the `use` at the top of the file.

At the top, outside any class, `use` imports a name — it is an alias and
loads nothing. Inside a class's body, `use` copies a trait into it.

Same word, two jobs with no relation at all. It is the most unfortunate
vocabulary choice in modern PHP, and you will read code with both kinds in
the same file.
:::

When two traits bring a method with the same name, PHP does not choose for
you:

```text
Fatal error: Trait method RecordsAudit::record has not been
applied as Copy::record, because of collision with
RecordsHistory::record
```

The way out is to declare who wins, and optionally give the loser an alias:

```php
    use RecordsHistory, RecordsAudit {
        RecordsHistory::record insteadof RecordsAudit;
        RecordsAudit::record as recordAudit;
    }
```

It works. And it is the best warning PHP can give that the two traits wanted
to be the same thing, or that the class is doing two jobs.

:::key
The trait in the example brought a property along: `$history`. It becomes a
property of the class, like any other — and it does not appear in the
class's body, where someone would look for it.

A trait with state is the easiest way for a class to gain properties nobody
remembers declaring. Prefer stateless traits; when you need shared state,
the right mechanism is the one in the next section.
:::

## Composition: "has a" instead of "is a"

Vera's whiteboard had ten boxes because three characteristics became types.
They are not types. They are data:

```php title="src/Catalog/Classification.php" numbered
<?php

namespace CasaAmarela\Catalog;

final class Classification
{
    public function __construct(
        public readonly bool $children = false,
        public readonly bool $textbook = false,
        public readonly bool $reference = false,
        public readonly bool $imported = false,
    ) {}

    public function lendable(): bool
    {
        return !$this->reference && !$this->imported;
    }

    public function loanDays(): int
    {
        return $this->children ? 7 : 14;
    }
}
```

And the `Book` **has a** classification:

```php title="src/Catalog/Book.php" numbered
<?php

namespace CasaAmarela\Catalog;

class Book
{
    public function __construct(
        public readonly string $title,
        public readonly int $year,
        public readonly Classification $classification,
    ) {}
}
```

```php
$vidasSecas = new Book('Vidas Secas', 1938, new Classification(
    textbook: true,
));

echo $vidasSecas->classification->loanDays(), "\n";
```

```text
14
```

Ten boxes became one class and four fields. And when Mr. Juvenal shows up
with the audiobooks — which go out for twenty-one days, because Mrs. Marlene
takes her time — the cost is **one line**, not doubling the whiteboard.

:::term Composition
Building behavior by putting objects together, instead of inheriting from
them. "The book has a classification" instead of "the book is a children's
book".

The trade is always the same: you write one more line to delegate, and you
earn the right to change your mind without touching the tree.
:::

Four booleans are not the last word in modeling — the day Casa Amarela has
fifteen flags, this becomes a list. What is already right is the direction:
grow by adding fields, not by adding classes.

## How to choose

| You want | Use |
|---|---|
| unrelated classes to answer the same calls | interface |
| a contract plus a piece of shared implementation | abstract class |
| to repeat a stateless block of code in different classes | trait |
| to vary behavior along more than one axis | composition |
| to vary along a single axis, with exclusive options | inheritance |

Table: When in doubt between inheritance and composition, start with
composition. Swapping composition for inheritance later is an afternoon; the
reverse is a month.

:::note In your career
In an interview, "what is the difference between an abstract class and an
interface?" is a question to memorize. The version that separates those who
understood is the following, and you can ask it of yourself before drawing
any hierarchy:

*If tomorrow a combination I didn't foresee shows up, do I add a field or do
I add a class?*

Whoever answers "a field" is composing. Whoever answers "a class" is in a
tree that is going to double — and it is worth saying so in the meeting
**before** the third box, because after the eighth the conversation is no
longer technical, it is about the deadline.
:::

:::tree title="Where we are now"
catalog/
  src/
    Catalog/
      Book.php             # has a Classification
      Classification.php   # final, readonly
      Copy.php             # implements Lendable, use RecordsHistory
    Circulation/
      Lendable.php         # interface
      RecordsHistory.php   # trait
    Readers/
      Reader.php
    Loans/
      Fine.php
    Legacy/
      Book.php
  report.php
:::

:::summary
- `extends` copies everything from the class above and uses up the class's
  only kinship.
- Independent characteristics double the tree: three become eight classes.
- The subclass's rule is to work in the parent's place; if it throws where
  the parent answered, the inheritance is lying.
- An interface is a contract without code; a class implements as many as it
  wants.
- An abstract class is a contract with part of the implementation, and it
  costs the `extends`.
- A trait is code copied into the class; a name clash is a fatal error,
  resolved with `insteadof`.
- The `use` at the top of the file imports a name; the `use` inside the
  class copies a trait.
- Composition swaps "is a" for "has a", and grows by adding fields instead of
  classes.
:::

:::checkpoint
You can say why Vera's whiteboard reached ten boxes, declare and implement
an interface, recognize a trait that brought hidden state, and justify in
writing — in two sentences — when you inherit, when you compose and when
you declare a contract.
:::

:::exercise level=1
Besides books, Casa Amarela lends three screen readers donated by an NGO.
They have an asset tag instead of an accession number, go out for thirty
days and cannot be renewed.

Decide: `ScreenReader extends Copy`, `ScreenReader implements Lendable`, or
neither? Justify it in two sentences.

:::answer
`implements Lendable`.

A screen reader is not a copy of a book: it has no accession number, no
`Book` inside, no paper-condition status. Inheriting from `Copy` would bring
all of that along and force the class to pretend it has a book.

What it has in common with a copy is **behavior** — it identifies itself, it
is available or not, it has a loan period. That is exactly what the
interface describes, and that is why the circulation report can count both
without knowing the difference.
:::

:::exercise level=2
Write the `Classification` with a fifth case: audiobook, which goes out for
twenty-one days.

Casa Amarela's rule is: reference and imported books do not go out; among
those that do, the longest applicable period wins — audio (21) before
regular (14), and children's (7) only when the book is not an audiobook.

Write `loanDays()` and explain why the order of the conditions matters.

:::answer
```php title="src/Catalog/Classification.php" numbered
    public function loanDays(): int
    {
        if ($this->audio) {
            return 21;
        }

        if ($this->children) {
            return 7;
        }

        return 14;
    }
```

The order matters because the conditions **are not exclusive**: a
children's audiobook satisfies both. Whoever wrote `children` first would
return 7 for it, contradicting Vera's rule.

It is the same trap as the class hierarchy, now inside a method — and that is
why it is preferable here: an ambiguous rule in an `if` is one line to fix,
and the same ambiguity in a class tree is a `ChildrensAudiobook` class to
delete, along with everything that already depended on it.

A detail worth writing in a comment or a test: the "longest period wins"
rule and the order of the conditions need to agree. If tomorrow someone adds
a 30-day case at the end of the line, it will never be reached.
:::

:::exercise level=3
You receive this code to review. It works, it has passing tests and it was
written by someone experienced.

```php
abstract class Report
{
    use ConnectsToDatabase;
    use FormatsCurrency;
    use SendsEmail;
    use GeneratesPdf;

    abstract public function query(): array;

    public function run(): void
    {
        $rows = $this->query();
        $pdf = $this->generatePdf($rows);
        $this->send($pdf);
    }
}

class CirculationReport extends Report { /* ... */ }
class FinesReport extends Report { /* ... */ }
```

Point out the two structural problems and propose the minimal change that
improves it without rewriting everything.

:::answer
**First problem: the abstract class became a storeroom.** It does four
unrelated things — talks to the database, formats money, sends e-mail and
generates PDFs — and every report inherits all four, whether it uses them or
not. A report that only prints to the screen carries e-mail sending along,
and nobody can test the query without dragging the rest.

**Second problem: the traits hide dependencies.** Looking at
`CirculationReport`, nothing says it needs a database connection and a
configured mail server. That is three files up, inside traits, and it only
shows up when it breaks.

**The minimal change** is not deleting the hierarchy. It is removing the two
heaviest traits — `SendsEmail` and `ConnectsToDatabase` — and passing what
they do as objects received in the constructor:

```php
abstract class Report
{
    use FormatsCurrency;

    public function __construct(
        private readonly Database $database,
        private readonly Mailer $mailer,
    ) {}

    abstract public function query(): array;
}
```

What you gain is visible on the first line: the class now **declares** what
it depends on. What you lose is the convenience of passing nothing — and
that convenience was what made the test need a real database.

`FormatsCurrency` can stay: it is a stateless trait, with no external
dependency, and its cost is zero. Not every trait is a problem; the problem
is a trait that brings the world along with it.
:::
