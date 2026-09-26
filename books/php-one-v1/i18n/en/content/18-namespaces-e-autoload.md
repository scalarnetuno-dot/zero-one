---
source_hash: 1edb60318594
title: "Namespaces and autoload"
number: 18
slug: namespaces-e-autoload
part: p3
kicker: "The import needed the old book and the new book in the same program. The second one was named BookNew2."
goal: >-
  Give code an address with `namespace`, import names with `use`, declare
  PSR-4 autoloading in Composer and never write a class `require` again —
  including the reason this breaks only on the server.
---

:::story BookNew2
Tainá was reading `import.php`, which reads the System's dump and writes it
into the new database.

"Why is there a `BookNew2`?"

"Because there was already a `BookNew`."

"And what's `BookNew`?"

"The System's one. With `quantity`."

Tainá scrolled to the top of the file. Three classes: `Book`, `BookNew` and
`BookNew2`.

"And `Book`?"

"That one's from 2019. Not used anymore."

"So the new one is two."

"The new one is two."

She wrote it down in her notebook, on the page that already had
`functions2_NEW_final.php` written in the same cramped handwriting of
someone trying not to laugh.
:::

## Two identical names in the same program

The problem with `BookNew2` is not a lack of imagination. It is that PHP
only accepts one `Book` at a time:

```php title="import.php" numbered
<?php

require 'Book.php';         // the new catalog's
require 'legacy/Book.php';  // the one from the System's dump
```

```text
Fatal error: Cannot redeclare class Book
(previously declared in /app/Book.php:3)
in /app/legacy/Book.php on line 3
```

Being in different folders does not help. To PHP, both are called `Book`,
and a name can only point to one thing.

It is the same error as `formatDate()` — and for a long time the way out was
the same too: a prefix in the name. That is how the PHP of the 2000s
produced classes like `Zend_Db_Table_Row_Abstract`, which is a namespace
written by hand, with underscores in place of the backslash.

## A namespace is an address

```php title="Book.php" numbered
<?php

namespace CasaAmarela\Catalog;

class Book
{
    public function __construct(
        public string $title,
        public int $year,
    ) {}
}
```

One new line, and the class's name changed:

```php
echo Book::class, "\n";
```

```text
CasaAmarela\Catalog\Book
```

`Name::class` returns a class's full name, and it is the honest way to find
out what you are dealing with. This class's real name is not `Book`: it is
`CasaAmarela\Catalog\Book`. `Book` is just the last piece.

:::term Fully qualified name
*Fully Qualified Class Name*, abbreviated FQCN in documentation and error
messages. It is the whole address, with the backslashes: first the
namespace, then the class's name.

Two classes with the same final name and different addresses are two
different classes, and they can live in the same program without seeing
each other.
:::

The syntax rule is short: `namespace` is the file's first statement, after
`<?php`, and it applies to everything the file declares.

And the reading rule is even shorter: **a namespace is not a folder**. It is
a name with punctuation, like a postal address. Nothing in PHP forces
`CasaAmarela\Catalog\Book` to live in `src/Catalog/Book.php`.

You are going to do exactly that anyway, for a reason that shows up three
sections from now.

## Inside a namespace, the rest of the world disappears

Put `namespace CasaAmarela\Catalog;` at the top of a file that connects to
the database and run it:

```php
$pdo = new PDO($dsn, 'root', 'secret');
```

```text
Fatal error: Uncaught Error: Class "CasaAmarela\Catalog\PDO" not found
```

This is the first stone everyone trips over, and the message gives away the
cause: PHP looked for a `PDO` **inside the current address**. It did not
find one, and it stopped. It does not go looking through the whole building.

The backslash in front says "from the root":

```php
$pdo = new \PDO($dsn, 'root', 'secret');
```

```text
connected
```

:::key
For **classes**, a name without a backslash is relative to the file's
namespace.

For **functions and constants**, it is not: if PHP does not find the
function in the current namespace, it looks in the root. That is why
`strtoupper()`, `date()` and `count()` keep working without any backslash
inside a file with a namespace.

That difference is the reason your old code keeps running after it gets its
first `namespace` line, and the reason `new PDO` is the only thing that
breaks.
:::

## `use`: aliases for the whole file

Writing `\CasaAmarela\Catalog\Book` every time would be worse than
`BookNew2`. `use` resolves the name once, at the top:

```php title="import.php" numbered
<?php

use CasaAmarela\Catalog\Book;
use CasaAmarela\Legacy\Book as SystemBook;

$new = new Book('Vidas Secas', 1938);
$old = new SystemBook('Vidas Secas', 1938, 3);
```

Three things to remember.

`use` **loads nothing**. It only says: in this file, when I write `Book`, I
mean `CasaAmarela\Catalog\Book`. It is a local alias.

`as` gives a different alias, and it is the way out for the case of two
classes with the same final name. Both live in the same file, with names
you chose — and each one's real name is still its full address.

And `use` applies per file. It does not apply to the file that included it,
nor to the one being included. Each one declares its own.

:::pitfall
The most common mistake with `use` does not look like a `use` mistake:

```text
Fatal error: Uncaught Error:
Class "CasaAmarela\Catalog\Loan" not found
```

The name in the message is right, the file exists, the class is there — and
the cause is that you forgot the `use` in a file from another namespace, so
PHP looked at the wrong address.

Read the message from the **beginning**, not from the end. The front part
is the address where it looked, and that is what is wrong.
:::

## PSR-4: the convention that does the rest on its own

A namespace is not a folder — but if you pretend it is, a tool can guess
where each class lives, and then nobody ever needs to write a class
`require` again.

That is PSR-4: a convention published by the group that standardizes the PHP
ecosystem, and one almost every modern project follows.

```json title="composer.json"
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        }
    }
```

That says: everything that starts with `CasaAmarela\` lives inside `src/`.
The rest of the address becomes a path, and the class's name becomes a file
name with `.php` at the end.

| Full name | File |
|---|---|
| `CasaAmarela\Catalog\Book` | `src/Catalog/Book.php` |
| `CasaAmarela\Catalog\Copy` | `src/Catalog/Copy.php` |
| `CasaAmarela\Readers\Reader` | `src/Readers/Reader.php` |
| `CasaAmarela\Legacy\Book` | `src/Legacy/Book.php` |

Table: The `CasaAmarela\` prefix is swapped for the `src/` folder; what is
left becomes a path, piece by piece.

Two practical rules come from that. **One file, one class** — the
autoloader looks for a file by name, and two names in the same file leave
one of them unreachable. And **the file is named like the class**, with the
same case.

After declaring it, tell Composer:

```text
$ composer dump-autoload
```

```text
Generating autoload files
Generated autoload files containing 4 classes
```

And the whole `import.php` becomes:

```php title="import.php" numbered
<?php

require 'vendor/autoload.php';

use CasaAmarela\Catalog\Book;
use CasaAmarela\Legacy\Book as SystemBook;

$new = new Book('Vidas Secas', 1938);
$old = new SystemBook('Vidas Secas', 1938, 3);

echo $new->title, ' / ', $old->quantity, "\n";
```

A single `require`, the same one in every program of the project. The
classes show up when they are used.

## Who found that class?

Autoloading is not magic, and distrusting it is healthy until you see how
small the thing is. It is six lines:

```php title="loader.php" numbered
<?php

spl_autoload_register(function (string $class): void {
    echo "looking for: $class\n";
});

$x = new DoesNotExist();
```

```text
looking for: DoesNotExist

Fatal error: Uncaught Error: Class "DoesNotExist" not found
```

`spl_autoload_register` stores a function to be called **at the moment PHP
comes across a class name it does not know yet**. The function receives the
full name and has a single obligation: if it knows where the class is, load
the file. If it does not load it, PHP moves on to the next registered
function and, if they run out, raises the error.

A minimal PSR-4 loader fits in eight lines:

```php title="loader.php" numbered
<?php

spl_autoload_register(function (string $class): void {
    $prefix = 'CasaAmarela\\';

    if (!str_starts_with($class, $prefix)) {
        return;
    }

    $rest = substr($class, strlen($prefix));
    $relative = str_replace('\\', '/', $rest);
    $path = __DIR__ . '/src/' . $relative . '.php';

    if (is_file($path)) {
        require $path;
    }
});
```

That is what `vendor/autoload.php` does, with more care and for every prefix
at the same time — yours and each installed library's.

:::trivia
PSR stands for *PHP Standard Recommendation*, numbered by PHP-FIG, a group
formed by maintainers of large projects who were tired of incompatible
libraries.

PSR-0 came before and still accepted underscores in the class name as a
folder separator, a legacy of the `Zend_Db_Table` era. PSR-4 dropped that.
It was the last time the ecosystem needed to agree on where files go.
:::

## `dump-autoload`, and when it is needed

Composer generates the list of prefixes once and stores it. You need to
regenerate it when you **change the map**, not when you change the code:

| What you did | Needs `dump-autoload` |
|---|---|
| created `src/Catalog/Author.php` | no |
| edited a class | no |
| changed the `autoload` block in `composer.json` | yes |
| installed a package | no — `require` already does it |

Table: Day to day, almost never. The command exists for the day you touched
the map.

There is a variation that shows up in deployment guides:

```text
$ composer dump-autoload --optimize
```

Instead of guessing the path for each new class, Composer scans the folders
and builds a ready-made list from name to file. It gets faster, because it
trades a disk lookup for a memory lookup.

The cost is the other side of the same coin: a class created after the scan
is not on the list. On a development machine, that is a gratuitous trap. In
production, where the code does not change between one deploy and the
next, it is pure gain.

## Works on my Windows

What is left is the stone that only shows up on the server.

:::pitfall
`CasaAmarela\Catalog\Book` looks for `src/Catalog/Book.php`. If the file is
called `book.php`, with a lower-case `b`:

- on **Windows** and **macOS**, the file system ignores letter case and
  hands over the file anyway. It works;
- on **Linux**, `book.php` and `Book.php` are two different files. One of
  them does not exist.

The result is the bug that eats a Friday afternoon more than any other:
everything works on the machine of whoever wrote it, and the screen breaks
on the server with `Class not found` pointing to a name that is visibly
correct.

The rule that prevents it: the file is named exactly like the class, and the
folder exactly like the namespace piece. When Git has already recorded the
wrong name, renaming only the case takes two steps —
`git mv book.php Book.php.tmp` and then `git mv Book.php.tmp Book.php` —
because Git, on your machine, also thinks the two names are the same.
:::

## The structure the project now has

The classes leave the root and go into `src/`, split by **domain subject** —
catalog, readers, legacy — not by technical type. A folder called `Classes/`
or `Helpers/` just pushes the question "where does this live?" inside it.

:::tree title="Where we are now"
catalog/
  composer.json    # with the autoload block
  composer.lock
  vendor/
  .gitignore
  src/
    Catalog/
      Book.php       # CasaAmarela\Catalog\Book
      Copy.php       # CasaAmarela\Catalog\Copy
    Readers/
      Reader.php     # CasaAmarela\Readers\Reader
    Legacy/
      Book.php       # CasaAmarela\Legacy\Book
  connection.php
  import.php
  list.php
  lend.php
  receipt.php
:::

:::note In your career
In a legacy project you will find both worlds in the same repository: a
modern folder with PSR-4 and an old folder full of `require`s. The
temptation is to propose "migrating everything" in one sprint.

The migration that tends to get approved is a different one: register
autoloading for the new code, write everything new in there, and move an old
file each time you need to touch it anyway. In six months the old folder has
shrunk without anyone opening a ticket called "refactoring".

It works for almost every kind of technical debt: the proposal that survives
the prioritization meeting is not the one that asks for a week, it is the
one that asks for half an hour at a time and shows numbers afterwards.
:::

:::summary
- Two classes with the same name cannot live together; a different folder
  does not help.
- `namespace` gives the class an address. Its real name becomes the whole
  address, and `Name::class` shows what it is.
- Inside a namespace, a class name without a backslash is relative — hence
  `new \PDO`. Functions and constants fall back to the root on their own.
- `use` creates an alias for the file; `use ... as` resolves the clash of
  identical final names.
- PSR-4 swaps a namespace prefix for a folder: one file per class, with the
  same name and the same case.
- `spl_autoload_register` is the hook PHP calls when it meets an unknown
  name; `vendor/autoload.php` is that, done properly.
- `dump-autoload` only when the map changes; `--optimize` in production,
  never on your machine.
- The wrong case in a file name works on Windows and breaks on Linux.
:::

:::checkpoint
You declare namespaces, import classes with `use`, know why `new PDO`
breaks inside a namespace, configure PSR-4 `autoload` in `composer.json` and
can create a new class that is found without any `require`.
:::

:::exercise level=1
For each full name, say which file it lives in, given the mapping
`"CasaAmarela\\": "src/"`:

1. `CasaAmarela\Loans\Loan`
2. `CasaAmarela\Catalog\Search\Filter`
3. `CasaAmarela\Fine`

And then the opposite: what full name does the class declared in
`src/Reports/Monthly.php` have?

:::answer
1. `src/Loans/Loan.php`
2. `src/Catalog/Search/Filter.php`
3. `src/Fine.php`

The `CasaAmarela\` prefix disappears and becomes `src/`; each remaining
backslash becomes a folder; the last piece becomes the file.

In the opposite direction, `src/Reports/Monthly.php` corresponds to
`CasaAmarela\Reports\Monthly` — and the file needs to declare
`namespace CasaAmarela\Reports;` at the top. If it declares something else,
the autoloader loads the file and PHP keeps saying the class does not
exist, because loading the right file and finding the right name are two
conditions, not one.
:::

:::exercise level=2
Move the classes from the previous chapter into `src/`, following the table
in the PSR-4 section, and make `list.php` work with a single `require`.

Then delete, on purpose, the `use` line in `list.php` and read the message.
Say which part of it points to the cause.

:::answer
`composer.json` gets:

```json title="composer.json"
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        }
    }
```

Each class gets the namespace at the top:

```php title="src/Catalog/Book.php" numbered
<?php

namespace CasaAmarela\Catalog;

class Book
{
    public function __construct(
        public string $title,
        public int $year,
    ) {}
}
```

And the program:

```php title="list.php" numbered
<?php

require 'vendor/autoload.php';
require 'connection.php';

use CasaAmarela\Catalog\Book;

$rows = $pdo->query('SELECT title, year FROM books')->fetchAll();

foreach ($rows as $row) {
    $book = new Book($row['title'], (int) $row['year']);
    echo $book->title, "\n";
}
```

Without the `use`, the message is:

```text
Fatal error: Uncaught Error: Class "Book" not found
```

The part that points to the cause is the name in quotes: it came **without
an address**. Since `list.php` has no `namespace`, PHP looked for `Book` in
the root, and there is no class called just `Book` — the one you wrote is
called `CasaAmarela\Catalog\Book`.
:::

:::exercise level=3
A team reports the following: the receipt screen works on all three
developers' machines and breaks in production, always, with
`Class "CasaAmarela\Receipts\Generator" not found`. The file
`src/Receipts/Generator.php` is in the repository and has the right
namespace.

Come up with at least three possible causes and say, for each one, a check
that confirms or rules it out in under a minute.

:::answer
**The name's case.** The file may be stored as `src/receipts/Generator.php`
or `src/Receipts/generator.php` in the repository, and all three machines
may be Windows or macOS. Check with `git ls-files src/Receipts` — which
shows the name as Git stored it, not as the local disk shows it.

**Optimized autoload with a stale list.** If the deploy runs
`dump-autoload --optimize` before copying the new file, the ready-made list
does not have the class. Check by looking for the name inside
`vendor/composer/autoload_classmap.php` on the server.

**File outside the published package.** An overly broad `.gitignore` — a
`receipts/` line meant for generated PDFs, for example — may be excluding
the whole folder. Check with `git check-ignore -v src/Receipts` on the
machine of whoever wrote it.

A fourth, less common and worth checking because it costs five seconds: the
`autoload` block in `composer.json` was changed and not committed.
`git status` on the machine of whoever touched it answers that.

What these four have in common, and that is why the question is useful: none
of them is a bug in the class's code. When the error only happens in one
environment, the suspect is whatever differs between environments — the
file system, the build step and what was actually shipped.
:::
