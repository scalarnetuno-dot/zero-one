---
source_hash: c0434fa9c399
title: "From include to Composer"
number: 16
slug: do-include-ao-composer
part: p3
kicker: "Two functions with the same name in two files. The page works or dies depending on which one gets in first."
goal: >-
  Understand what `include` and `require` do, what `_once` solves and what
  it does not, create a project with Composer, install the first dependency
  and explain the difference between `install` and `update` to someone on
  the team.
---

:::story Depends on which gets in first
Casa Amarela's receipt printed the date as `12/03/26`. The overdue report,
generated the same day, printed `12/03/2026`.

Tainá asked which of the two was right.

"Both," said Dedé. "In different files."

`functions2.php` had a `formatDate()`. `functions2_NEW_final.php` had
another one, with one character less in the format. No page of the System
included both, and that is how fifteen years went by without anyone having
to choose.

Until the new renewal screen, which needed both.

"And then?"

"And then, on Wednesday, it worked. On Thursday, after someone swapped the
order of two `include`s, it stopped."

"Stopped how?"

Dedé turned the monitor around.

```text
Fatal error: Cannot redeclare function formatDate()
(previously declared in /app/functions2_NEW_final.php:3)
in /app/functions2.php on line 2
```

"And why did it work on Wednesday?"

"Because on Wednesday the order was the other way round."
:::

## One file becomes two, and two become thirty

The Casa Amarela project already has the same problem, on a smaller scale.

Every program that talks to the database starts with the same line:

```php
require 'connection.php';
```

There are six files today. There will be thirty before March. And
`connection.php` is not the only candidate for sharing: `fineInCents()` will
be used by the receipt, the report and the return screen.

One thing has changed in `connection.php` since it was born: it lost the
`echo "connected\n"` at the end. It was a friendly line while the file ran
on its own, and it is a line that dirties the output of all six the moment
it starts being included by all six.

```php title="connection.php" numbered
<?php

$dsn = 'mysql:host=127.0.0.1;port=3306'
     . ';dbname=casa_amarela;charset=utf8mb4';

$pdo = new PDO($dsn, 'root', 'secret', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,
]);
```

:::key
A file made to be included prints nothing. It defines — variables,
functions, configuration — and hands control back.

An `echo` in an included file shows up in the output of everyone who
includes it, including in the middle of a JSON and before an HTTP header.
:::

## include and require

The two words do the same thing: they take the contents of another file and
run it right there, as if it were written in place. The difference is what
happens when the file does not exist.

With `include`:

```php title="receipt.php" numbered
<?php

include 'rates.php';
echo "made it here\n";
```

```text
Warning: include(rates.php): Failed to open stream: No such file or
directory in /app/receipt.php on line 3

Warning: include(): Failed opening 'rates.php' for inclusion
(include_path='.:/usr/share/php') in /app/receipt.php on line 3
made it here
```

Two warnings — and the program **carried on**. It printed "made it here"
without the rates it was going to use.

Change one word:

```php title="receipt.php" numbered
<?php

require 'rates.php';
echo "made it here\n";
```

```text
Warning: require(rates.php): Failed to open stream: No such file or
directory in /app/receipt.php on line 3

Fatal error: Uncaught Error: Failed opening required 'rates.php'
(include_path='.:/usr/share/php') in /app/receipt.php:3
```

The program stopped. It printed nothing afterwards.

| | File does not exist | The program |
|---|---|---|
| `include` | warning | carries on |
| `require` | fatal error | stops |

Table: The choice is not about style. It is the answer to a question: *does
this program make sense without that file?*

For `connection.php` the answer is no — a lending program without a
database has nothing to do, and `require` is right. For an optional
translation file, or a `config.local.php` that only exists on your machine,
`include` is honest.

:::pitfall
The temptation is to use `include` "so it doesn't break". The result is a
program that carries on without half of what it needed and fails thirty
lines later, with a message about an undefined variable that has no visible
connection to the file that was missing.

Breaking early, with the name of the missing file, is cheaper.
:::

## What `_once` solves

There are `include_once` and `require_once`. They keep the list of files
already loaded and ignore the repeated request.

The real problem this solves shows up as soon as your files start including
one another:

```php title="report.php"
<?php

require 'connection.php';
require 'fine.php';   // fine.php also does require 'connection.php'
```

Without `_once`, `connection.php` runs twice: two open connections, and the
second overwriting the first one's `$pdo`. With `require_once`, it runs
once.

```php title="report.php"
<?php

require_once 'connection.php';
require_once 'fine.php';
```

## What `_once` does not solve

This is where the confusion that cost Dedé his Wednesday lives.

`_once` compares **files**, not names. Two different files that declare the
same function are still two different files — and both will be loaded.

Reproduce it. Three small files, in the same folder:

```php title="functions2.php" numbered
<?php

function formatDate(string $iso): string
{
    return date('d/m/Y', strtotime($iso));
}
```

```php title="functions2_NEW_final.php" numbered
<?php

function formatDate(string $iso): string
{
    return date('d/m/y', strtotime($iso));
}
```

The only difference is in the format: `Y` prints the year with four digits,
`y` with two. The `date()` function takes that format and an instant in
seconds; `strtotime()` converts the text `2026-03-12` into that number of
seconds.

```php title="renew.php" numbered
<?php

include_once 'functions2.php';
include_once 'functions2_NEW_final.php';

echo formatDate('2026-03-12'), "\n";
```

```text
Fatal error: Cannot redeclare function formatDate()
(previously declared in /app/functions2.php:3)
in /app/functions2_NEW_final.php on line 3
```

`_once` prevented nothing, because nothing was included twice. There were
two files, once each, with the same function inside.

## The patch that froze the bug

The way out someone found in the System, in 2017, was to fence the second
declaration with a question:

```php title="functions2_NEW_final.php" numbered
<?php

if (!function_exists('formatDate')) {
    function formatDate(string $iso): string
    {
        return date('d/m/y', strtotime($iso));
    }
}
```

`function_exists()` returns `true` if a function with that name has already
been declared. The `!` inverts it: *declare it only if it does not exist
yet*.

Run `renew.php` again:

```text
12/03/2026
```

It works. And it works with one of the two versions silently discarded,
because the other one got there first.

Now swap the two lines in `renew.php`:

```php title="renew.php" numbered
<?php

include_once 'functions2_NEW_final.php';
include_once 'functions2.php';

echo formatDate('2026-03-12'), "\n";
```

```text
Fatal error: Cannot redeclare function formatDate()
(previously declared in /app/functions2_NEW_final.php:3)
in /app/functions2.php on line 2
```

It died — because only one of the two files got the fence.

:::pitfall
`function_exists()` around a declaration is almost always the mark of a
conflict nobody wanted to resolve. It trades a fatal error, which points to
both files and both lines, for behavior that depends on the loading order —
and the loading order is the thing that changes most when someone touches an
`include` without looking.

When you find one, the question is not "can I remove it?". It is: **what are
the two versions, and which one is the system using today?**
:::

## Composer is not an installer

With thirty files, "who includes whom" becomes a full-time job. With a
third-party library, it becomes impossible: the library has its own files,
which include other files of its own, and it does not know where you put
the folder.

Composer solves three problems at once, and only the first is "downloading
things":

1. **Working out what to install.** You ask for a library; it depends on
   two others; one of them demands a version that clashes with what you
   already have. Choosing the set that fits together is a math problem, not
   a download.
2. **Recording exactly what was installed**, so that your machine, Tainá's
   and the server run the same code.
3. **Loading the files** without you writing a `require` per library.

:::term Dependency
Code your project uses and did not write. A dependency has a name, a
version and, almost always, dependencies of its own — which become yours
too, without you having asked.
:::

## The project gets a name

Until now the project folder was a folder.

```text
$ composer init
```

The command asks questions. The answers for our project:

```text
Package name (<vendor>/<name>): casa-amarela/catalog
Description []: Catalog system for the Casa Amarela Library
Author [n to skip]: n
Minimum Stability []:
Package Type []: project
License []: proprietary

Would you like to define your dependencies interactively [yes]? no
Would you like to define your dev dependencies interactively [yes]? no
Add PSR-4 autoload mapping? [src/, n to skip]: n
```

The last answer stayed at `n` because the project has nothing to map yet.
The two before it stayed at `no` because installing from the command line
is simpler than filling in a form.

The result is a file:

```json title="composer.json"
{
    "name": "casa-amarela/catalog",
    "description": "Catalog system for the Casa Amarela Library",
    "type": "project",
    "license": "proprietary",
    "require": {}
}
```

Nine lines, no magic. An empty `require` means: this project does not
depend on anything yet.

## The first dependency

For four chapters the catalog data has been showing up on screen like this:

```php
var_dump($books);
```

```text
array(2) { [0]=> array(3) { ["id"]=> int(12) ["title"]=>
string(12) "Dom Casmurro" ["year"]=> int(1899) } [1]=> array(3) {
["id"]=> int(31) ["title"]=> string(18) "Memórias Póstumas"
["year"]=> int(1881) } }
```

Complete information, impossible reading. There is a library that does the
same thing, formatted, and it is the project's first request:

```text
$ composer require --dev symfony/var-dumper
```

```text
./composer.json has been updated
Running composer update symfony/var-dumper
Lock file operations: 3 installs, 0 updates, 0 removals
  - Locking symfony/deprecation-contracts (v3.5.1)
  - Locking symfony/polyfill-mbstring (v1.31.0)
  - Locking symfony/var-dumper (v7.2.3)
Writing lock file
Installing dependencies from lock file (including require-dev)
Package operations: 3 installs, 0 updates, 0 removals
  - Installing symfony/deprecation-contracts (v3.5.1)
  - Installing symfony/polyfill-mbstring (v1.31.0)
  - Installing symfony/var-dumper (v7.2.3)
Generating autoload files
```

You asked for one package and got three. The other two are dependencies of
the first: `var-dumper` needs them, and Composer brought them without asking
because the alternative would be to ask forty times.

```text
$ composer show --tree
```

```text
casa-amarela/catalog project
`--symfony/var-dumper v7.2.3
    |--php >=8.2
    |--symfony/deprecation-contracts ^2.5|^3
    `--symfony/polyfill-mbstring ~1.0
```

To use it, one new line at the start of the program:

```php title="list.php" numbered
<?php

require 'vendor/autoload.php';
require 'connection.php';

$books = $pdo->query(
    'SELECT id, title, year FROM books ORDER BY title LIMIT 2'
)->fetchAll();

dump($books);
```

```text
array:2 [
  0 => array:3 [
    "id" => 12
    "title" => "Dom Casmurro"
    "year" => 1899
  ]
  1 => array:3 [
    "id" => 31
    "title" => "Memórias Póstumas"
    "year" => 1881
  ]
]
```

`vendor/autoload.php` is the file Composer generated on the last line of the
installation. It knows where everything Composer downloaded lives, and it is
the only library `require` you will write in the whole project.

:::key
`dump()` shows and carries on. `dd()` shows and stops — *dump and die*. The
second is the one you want when you are hunting a value in the middle of a
loop and do not want to scroll through three hundred lines of output.
:::

## `composer.json` asks, `composer.lock` remembers

The installation touched two files. They look redundant and they are not.

`composer.json` gained three lines:

```json title="composer.json"
    "require-dev": {
        "symfony/var-dumper": "^7.2"
    }
```

That is a **request**: any 7-point-something will do.

`composer.lock` now has a few hundred lines, and among them:

```json title="composer.lock"
        {
            "name": "symfony/var-dumper",
            "version": "v7.2.3",
            "source": {
                "type": "git",
                "reference": "a75bf8b0f8b9d0a92f0cb4e6c6b8"
            }
        }
```

That is a **record**: it was this version, from this commit. It is not a
range, it is a point.

The difference shows up in the two commands:

| Command | Reads | Writes | When |
|---|---|---|---|
| `composer install` | the `.lock` | nothing | when cloning and on deploy |
| `composer update` | the `.json` | the `.lock` | when you **decide** to upgrade |

Table: `install` reproduces. `update` decides. Mixing up the two is the most
expensive configuration bug there is.

:::pitfall
`composer update` on the server is the modern version of "it works on my
machine". It ignores the `.lock`, resolves everything again, and the server
comes up with versions nobody tested — sometimes released that very
morning.

On the server, only `composer install`. And if the `.lock` is not in Git,
that command has nothing to read: you are back to the earlier problem by
another route.
:::

## The caret you accepted without reading

The `^7.2` that appeared in `composer.json` has a rule, and the rule comes
from the numbering almost every PHP package follows: **major.minor.patch**.

- **major** changes when something breaks on purpose;
- **minor** changes when something is added without breaking anything;
- **patch** changes when something is fixed.

| Written | Accepts | Refuses |
|---|---|---|
| `^7.2` | 7.2.0, 7.4.1, 7.9.9 | 8.0.0 and 7.1.9 |
| `~7.2.3` | 7.2.3, 7.2.11 | 7.3.0 |
| `7.2.3` | only 7.2.3 | everything else |

Table: `^` is `composer require`'s default because it bets that the author
respects the numbering. `~` is for when you want only fixes. The fixed
version is for when the bet has already gone wrong once.

## `require` and `require-dev`

`var-dumper` came in with `--dev`, and that has consequences.

- **`require`** is what the program needs to **work**.
- **`require-dev`** is what **you** need to work: debugger, tests,
  formatter.

On the server, the installation skips the second list:

```text
$ composer install --no-dev
```

The result is less code on disk, less surface for security problems and a
server with no debugging tool installed.

And here is the trap that comes with it:

```text
Fatal error: Uncaught Error: Call to undefined function dump()
in /app/list.php on line 9
```

A forgotten `dump()` on a line that only runs in the rare case breaks
nothing on your machine — where the package exists — and takes the page down
in production, where it does not. It is a five-second fix and a two-hour
discovery, because the rare case does not happen while you are watching.

## The folder that does not go into Git

Composer created a `vendor/` folder with the code of the three libraries. It
does not go into the repository:

```text title=".gitignore"
/vendor/
```

The logic is simple: `vendor/` is a **result**, and results can be
reproduced. Whoever clones the project runs `composer install` and gets
exactly the same contents, because the `.lock` says exactly what they were.

| File | Goes into Git | Why |
|---|---|---|
| `composer.json` | yes | it is the project's intent |
| `composer.lock` | yes | it is what makes the machines match |
| `vendor/` | no | it is a result, and it is heavy |

:::note In your career
On some project someone will propose committing `vendor/` — usually after a
deploy that failed because the network dropped in the middle of
`composer install`.

The argument against it is not "it's ugly". It is concrete: a mid-size
project's `vendor/` has tens of thousands of files, and every update becomes
a change nobody can review. The real problem was the network during deploy,
and it has its own solution: install before publishing and publish the
finished folder.

When you disagree with a decision like that, bring the problem it was trying
to solve along with your alternative. Disagreeing without it is asking the
person to admit they were wrong in front of the team, and nobody goes for
that.
:::

:::tree title="Where we are now"
catalog/
  composer.json   # what the project asks for
  composer.lock   # what the project received
  vendor/         # generated by Composer, outside Git
  .gitignore
  connection.php  # creates $pdo, prints nothing
  fine.php
  search.php
  register.php
  lend.php
  return.php
  list.php
  receipt.php
:::

:::summary
- `include` warns and carries on; `require` stops. The choice answers "does
  the program make sense without this file?".
- `_once` prevents the **same file** twice. It does not prevent two
  different files from declaring the same function.
- `function_exists()` around a declaration trades a clear error for a silent
  dependency on loading order.
- Composer resolves the set of versions, records what it installed and
  generates the loader. Downloading is the easy part.
- `composer.json` is the request; `composer.lock` is the record. `install`
  reproduces, `update` decides.
- `^7.2` accepts any 7.x; `~7.2.3` accepts only 7.2 fixes; a fixed version
  accepts nothing.
- `require-dev` does not go to production — and the forgotten `dump()` does.
- `vendor/` stays out of Git; `composer.lock` stays in.
:::

:::checkpoint
You create a project with `composer init`, install a dependency, can say what
each of the two configuration files holds, read a version range and
recognize from the error message when a development package was missing in
production.
:::

:::exercise level=1
A project's `composer.json` asks for `"monolog/monolog": "^3.5"`. Which of
these versions can `composer update` install: 3.5.0, 3.9.2, 4.0.0, 3.4.9?

And if, instead of `update`, someone runs `composer install` on a machine
that has just cloned the project — which version will be installed?

:::answer
`update` can install **3.5.0 and 3.9.2**. The `^` accepts from the requested
version up to the next major number, without reaching it: it refuses 4.0.0
for being a higher major and 3.4.9 for being earlier than the request.

`install` does not choose anything. It installs **the version written in
`composer.lock`** — which may be 3.5.0, even if 3.9.2 already exists. It is
that indifference to what is new that makes two machines run the same code.
:::

:::exercise level=2
Create the three files from the patch section: `functions2.php`,
`functions2_NEW_final.php` (with the `function_exists` fence) and
`renew.php`.

Before running it, write down on paper what comes out in each of the two
`include_once` orders. Then run both and check.

Next, put the fence in `functions2.php` as well and run both orders again.
Explain what changed and why that is worse.

:::answer
With the fence only in `functions2_NEW_final.php`:

- `functions2.php` first: prints `12/03/2026`. The second declaration is
  discarded by the fence.
- `functions2_NEW_final.php` first: fatal error `Cannot redeclare`, because
  `functions2.php` has no fence and tries to declare on top.

With a fence in both, both orders work — and that is where it gets worse:

```text
order A → 12/03/2026
order B → 12/03/26
```

No error, no warning, and the date format is now decided by the order of
the `include`s. The receipt and the report can diverge forever without
anything in the system complaining. The fatal error was the only thing still
telling the truth.

The real fix is to choose one of the two functions, delete the other and
fix the calls — half an hour's work nobody did in nine years because the
fence made the urgency disappear.
:::

:::exercise level=3
On Friday, Casa Amarela's deploy went out and the lending screen started
returning an error. The server log says:

```text
Fatal error: Uncaught Error: Call to undefined function dump()
in /app/lend.php on line 47
```

Line 47 is inside an `if` that only runs when the copy is marked as `lost`
— something that happens about twice a month.

Answer three things: what happened, why the check on Dedé's machine did not
catch it, and which two changes prevent it from happening again.

:::answer
**What happened.** Someone left a debugging `dump()` in the code.
`symfony/var-dumper` is in `require-dev`, and the server installs with
`--no-dev` — so the function does not exist there. The program starts up
normally and only breaks when that `if` is reached.

**Why it was not caught.** On Dedé's machine the package is installed, so
the line works. And the `lost` path is not walked by hand: it depends on
rare data nobody remembers to create before deploying.

**The two changes.**

The first is about process and costs nothing: search for `dump(` and `dd(`
before deploying. The automated version of that is a rule in the publishing
step that refuses the deploy if it finds either.

The second is about coverage: some way of walking the lost-copy path without
waiting for it to happen. As long as the only way to run that `if` is real
life, production remains the place where it gets checked.

An answer that comes up and does not solve anything: moving `var-dumper` to
`require`. That fixes the symptom by installing a debugging tool on the
server — and a debugging tool in production is a table saw in the waiting
room: it works, and that is not where it belongs.
:::
