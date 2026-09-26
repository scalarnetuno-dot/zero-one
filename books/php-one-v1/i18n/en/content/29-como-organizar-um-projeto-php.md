---
source_hash: 5b3271c0cdf2
title: "How to organize a PHP project"
number: 29
slug: como-organizar-um-projeto-php
part: p5
kicker: "On Friday, Márcia announced that the web part started on Monday. Dedé asked for the weekend to tidy the house before the visit."
goal: >-
  Give the project a folder structure in which everything has a place, take
  passwords and configuration out of the code, assemble the system's
  objects in a single spot, and recognize, piece by piece, the structure
  Laravel will propose in volume 2.
---

:::story The same password eleven times
"Monday the web starts," said Márcia, at Friday's meeting. "Vera wants to
see screens. The grant wants to see screens. I want to see screens."

"Before the screens," said Dedé, "I'd like an afternoon."

"For what?"

He turned his laptop towards the table. A terminal, and a command:

```text
$ grep -rl "'root', 'secret'" --include=*.php . | wc -l
11
```

"Eleven files with the database password written inside. If the password
changes, that's eleven places. If someone publishes the repository, that's
eleven copies of the password on the internet."

Tainá looked at the project folder on her own laptop. It had started with
one file, in the PDO chapter. Now it had `import.php`, `import2.php`,
`lend.php`, `report.php`, a `bootstrap.php`, a `scripts/` folder with half
the scripts, and the other half in the root.

"It looks like the System," she said, quietly.

"It looks like the System in 2010," said Nonato, from the next desk,
without taking his eyes off the screen. "By 2011 it already had
`functions2_NEW_final.php`. Tidy it up now."
:::

## The folder as it is

Twenty-eight chapters of work left this:

:::tree title="The catalog, on Friday"
catalog/
  composer.json, composer.lock
  vendor/
  src/                   # the classes: well organized since 18
  bootstrap.php          # errors and logging, from chapter 28
  filters.php            # loose functions, from chapter 25
  import.php             # password inside
  import2.php            # password inside, "the one that works"
  lend.php               # password inside
  report.php             # password inside
  scripts/
    import-donations.php # password inside
    overdue.php          # password inside
    ...
  var/log/
  phpstan.neon
:::

Nothing here is wrong on its own. The problem is the sum, and it has three
parts.

**There is no right place for a new file.** A script goes into the root or
into `scripts/` depending on the mood of the day. Whoever joins the project
does not know where to look, and whoever writes does not know where to put
things.

**Configuration and secrets are in the code.** The password, the time zone,
the fourteen-day period. Changing any of them requires editing PHP — and the
code goes to Git, with everything written in it.

**Each script builds its own objects.** The `new PDO(...)` appears eleven
times; the `new SystemClock(...)`, four; the `new Logger(...)`, with three
different log paths.

The tidying solves all three, one per section.

## A place for everything

:::tree title="The catalog, on Monday"
catalog/
  bin/                   # command-line scripts
    import-donations.php
    overdue.php
  config/                # configuration: arrays, no secrets
    app.php
  public/                # the only folder the web server sees
  src/                   # all the domain code
    Catalog/ Circulation/ Loans/ Import/
    Readers/ Time/
    Logger.php
    Services.php
    functions.php
  tests/
  var/                   # what the program generates: logs, cache
    log/
  vendor/                # Composer's; never edited by hand
  bootstrap.php          # assembles everything, in one place
  .env                   # this machine's secrets; outside Git
  .env.example           # the .env template; in Git
  .gitignore
  composer.json, composer.lock
  phpstan.neon
:::

The rule behind the tree: **each folder answers one question.**

| Folder | Question |
|---|---|
| `src/` | What does the system **know how to do**? |
| `config/` | How is it **tuned**? |
| `bin/` | How is it **called** from the command line? |
| `public/` | How is it **called** from the browser? |
| `var/` | What has it **produced** while running? |
| `tests/` | How do we know it **works**? |

Table: One question per folder. A new file goes into the folder whose
question it answers.

`public/` is empty, and it stays empty until volume 2. It exists now for a
security reason worth understanding before there is anything to put in it:
the web server hands the browser **any file** in the folder it sees. If it
saw the project root, `https://.../.env` would hand out the database
password, and `https://.../var/log/app.log` would hand out the log. With the
server pointed at `public/`, only what was put there on purpose exists on the
web.

The `scripts/` folder became `bin/`, the name most PHP projects use for
command-line programs, and the scripts in the root went there. `import2.php`,
"the one that works", was compared with `import.php` over an afternoon, the
differences ended up in the `Importer` and the two became
`bin/import-donations.php`. The functions in `filters.php` went into
`src/functions.php`, which Composer starts loading on its own:

```json title="composer.json"
{
    "name": "casa-amarela/catalog",
    "type": "project",
    "require": {
        "php": "^8.3"
    },
    "autoload": {
        "psr-4": {
            "CasaAmarela\\": "src/"
        },
        "files": [
            "src/functions.php"
        ]
    },
    "scripts": {
        "analyse": "phpstan analyse",
        "import": "php bin/import-donations.php"
    }
}
```

The `psr-4` from chapter @cap:namespaces-e-autoload loads classes when
someone uses them. Functions do not get that chance — PHP has no way of
guessing which file they live in — and `files` solves it the simple way:
these files are always included, by `vendor/autoload.php`. Keep the list
short.

The `scripts` block gives names to the commands the team runs:
`composer analyse`, `composer import`. Nobody needs to remember the path to
PHPStan or to the script.

## Configuration outside the code

Configuration has two halves, and they live in different places.

**What changes from machine to machine** — password, database address, the
server's time zone — goes into a `.env` file in the root, which **does not
go to Git**:

```text title=".env"
APP_TIMEZONE=America/Sao_Paulo
DB_DSN="mysql:host=127.0.0.1;dbname=casa_amarela;charset=utf8mb4"
DB_USER=casa_amarela
DB_PASSWORD=the-real-password
LOAN_DAYS=14
```

What goes to Git is `.env.example`, identical and with the secrets left
blank, so whoever arrives knows what they need to fill in. And `.gitignore`
makes sure the real one does not get in by accident:

```text title=".gitignore"
/vendor/
/var/
/.env
```

**What the program reads** — with a name, a type and a default value — goes
into `config/`, in PHP files that return an array:

```php title="config/app.php" numbered
<?php

declare(strict_types=1);

use function CasaAmarela\env;

return [
    'timezone' => env('APP_TIMEZONE', 'America/Sao_Paulo'),
    'loan_days' => (int) env('LOAN_DAYS', '14'),
    'database' => [
        'dsn' => env('DB_DSN'),
        'user' => env('DB_USER'),
        'password' => env('DB_PASSWORD'),
    ],
];
```

`require` of a file that ends in `return` gives back the value of that
`return` — that is how `$config = require 'config/app.php'` receives the
array. `use function` is chapter @cap:namespaces-e-autoload's `use`, for
functions.

The two functions that read the `.env`:

```php title="src/functions.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela;

function loadEnv(string $path): void
{
    if (!is_file($path)) {
        return;
    }
    $values = parse_ini_file($path, false, INI_SCANNER_RAW);
    foreach ($values as $key => $value) {
        $_ENV[$key] ??= $value;
    }
}

function env(string $key, ?string $default = null): ?string
{
    return $_ENV[$key] ?? $default;
}
```

`parse_ini_file` reads a `key=value` file and returns an array;
`INI_SCANNER_RAW` asks it not to try to interpret the values, and `??=` does
not overwrite a value that was already set. It is a small version of what
`.env` libraries do more carefully.

:::key
**Secrets in `.env`, outside Git. Shape in `config/`, inside Git.** The
system's code never reads `.env` directly: it reads
`$config['database']['dsn']`. That way there is a single place that knows
where each value comes from, and a single place to give it a default.
:::

:::pitfall
If a password has gone to Git even once, removing it from the file does not
remove it from the history: anyone with a copy of the repository finds the
old commit. After moving the password to `.env`, **change the password**. At
Casa Amarela, it was Monday's first task, before any screen.
:::

## Assemble everything in one place

The `bootstrap.php` from chapter @cap:erros-e-debug configured errors. Now it
also assembles the objects the system uses, and hands them over ready:

```php title="bootstrap.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Logger;
use CasaAmarela\Services;
use CasaAmarela\Time\Clock;
use CasaAmarela\Time\SystemClock;

use function CasaAmarela\loadEnv;

require __DIR__ . '/vendor/autoload.php';

loadEnv(__DIR__ . '/.env');
$config = require __DIR__ . '/config/app.php';

// ...error_reporting and the two handlers from chapter 28...

$services = new Services();

$services->register(PDO::class, fn() => new PDO(
    $config['database']['dsn'],
    $config['database']['user'],
    $config['database']['password'],
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION],
));

$services->register(Clock::class, fn() => new SystemClock(
    new DateTimeZone($config['timezone']),
));

$services->register(Logger::class, fn() => new Logger(
    __DIR__ . '/var/log/app.log',
));

return $services;
```

And `Services` is a twenty-line class that stores closures — the ones from
chapter @cap:funcoes-anonimas-e-closures — and only calls them when someone
asks:

```php title="src/Services.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela;

use Closure;
use RuntimeException;

final class Services
{
    /** @var array<string, Closure> */
    private array $factories = [];

    /** @var array<string, object> */
    private array $ready = [];

    public function register(string $name, Closure $factory): void
    {
        $this->factories[$name] = $factory;
    }

    public function get(string $name): object
    {
        if (!isset($this->factories[$name])) {
            throw new RuntimeException("unknown: {$name}");
        }
        $factory = $this->factories[$name];
        return $this->ready[$name] ??= $factory($this);
    }
}
```

Three ideas in little code.

**One factory per service.** Each closure knows how to create one object.
Registering creates nothing: the `new PDO` only runs when someone asks for
the PDO. A script that only reads a CSV never opens a connection to the
database.

**Created once.** The `??=` stores the ready object on the first call and
returns the same one on the following ones. One connection per run, not one
per request.

**The name is the class.** `PDO::class` is the text `'PDO'`; `Clock::class`,
the interface's full name. Whoever asks for the `Clock` does not know — and
does not need to know — that they get a `SystemClock`. In the test, the same
name returns a `FrozenClock`.

The script, after the tidying:

```php title="bin/import-donations.php" numbered
<?php

declare(strict_types=1);

use CasaAmarela\Import\Importer;

$services = require __DIR__ . '/../bootstrap.php';

$importer = $services->get(Importer::class);
$importer->import(__DIR__ . '/../var/donations.csv');
```

No password, no `new PDO`, no log path. The script says what it does;
`bootstrap.php` knows how.

:::term Composition root
The single point in the program where objects are created and wired to one
another. Outside it, classes receive what they need through the constructor
and do not know where it came from.

`Services` is a **container**: the object that stores the factories and
hands over ready-made services. This chapter's one needs someone to register
each factory by hand.
:::

## From the catalog to Laravel

This structure was not invented for Casa Amarela. It is, with a few
differences in naming, the one almost every modern PHP project uses — and
the one Laravel creates when you type the first command in volume 2.

| Here, in volume 1 | In Laravel, in volume 2 |
|---|---|
| `src/`, namespace `CasaAmarela\` | `app/`, namespace `App\` |
| `config/app.php` returning an array | `config/`, one file per subject |
| `.env` and `.env.example` | `.env` and `.env.example` |
| `env()` only inside `config/` | `env()` only inside `config/` |
| `bin/import-donations.php` | an Artisan command |
| `bootstrap.php` | `bootstrap/app.php` |
| `Services` with hand-written factories | the container, which assembles on its own |
| `var/log/` | `storage/logs/` |
| `public/`, empty | `public/index.php`, the web's front door |
| `Logger` with context | `Log`, from PSR-3 |
| injected `Clock` | `now()`, freezable in tests |

Table: The map of the move. What changes is the name; the reason for each
folder is this chapter's.

The container row is the one volume 2 opens first. `Services` needs each
factory to be written; Laravel's container reads the class's constructor,
sees that it asks for a `PDO` and a `Logger`, and assembles both on its own.
Chapter 3 of volume 2 writes that version by hand, in forty lines, before
opening the framework.

:::note In your career
Every project starts as a script, and nobody wakes up deciding it will turn
into `functions2_NEW_final.php`. It gets there little by little, one file in
the root at a time, each with a good reason on the day it was created.

This chapter's tidying took an afternoon because the project had thirty
files. With three hundred, it would take a month, and no company gives a
month for that. Organize while it hurts a little: the right time is when you
think "this is starting to get messy".
:::

## What is still missing

On Monday morning, Tainá opened her notebook to the page that already had
`functions2_NEW_final.php` and wrote underneath:

```text
v1 - what I know how to do
  types, arrays, functions, strings
  SQL by hand, JOIN, indexes, transactions, PDO
  Composer, namespaces, classes, interfaces
  exceptions, strict typing, enums, value objects
  references, closures, generators
  large files, dates with time zones, errors that warn
  a project with a place for everything

v2 - what I don't know
  what gets from the browser to PHP?
```

Every program in this volume ran in the terminal, called by someone who
typed `php` and a file name. Vera is not going to type `php`. She is going
to open the browser, click a button, and the browser is going to send a text
to the server — a text with a format that has a name, rules and thirty years
of history.

The `$_GET` and `$_POST` you saw in passing at the start of the book are what
PHP understands of that text. Almost always, that is enough. In the first
week of volume 2, it will not be — and Tainá will spend a morning staring at
an empty `$_POST`, with the app swearing it sent everything.

:::tree title="Where we are now"
catalog/
  bin/          config/       public/ (empty)
  src/          tests/        var/
  bootstrap.php               # config, errors, services
  .env (outside Git)          .env.example
  composer.json               # psr-4, files, scripts
:::

:::milestone
End of Part 5. The project has a folder for each question, no secrets in the
code and a single place where objects are born. References, closures,
generators, dates and errors are no longer surprises — and each of them
comes back in volume 2 under another name.

End of volume 1. The language is all on the table: types, functions, SQL,
PDO, Composer, classes, exceptions, strict typing, enums, closures, files,
dates and errors, inside a project anyone on the team knows how to navigate.
Volume 2 starts with what happens between the browser and PHP — and only
after that opens Laravel, which will look, in every folder, like a bigger
version of what is in this tree.
:::

:::summary
- Each folder answers one question: `src/` does, `config/` tunes, `bin/` and
  `public/` are the doors, `var/` keeps what was produced, `tests/` checks.
- The web server sees only `public/`. Everything else stays off the web.
- `autoload.files` loads loose functions; `scripts` gives names to commands.
- Secrets in `.env`, outside Git; shape in `config/`. A password that has
  been to Git needs to be changed.
- `bootstrap.php` is the composition root: it creates and wires the objects,
  and the scripts only ask.
- A container stores factories and hands over ready-made services, created
  once.
:::

:::checkpoint
You organize a PHP project into folders with a purpose, take configuration
and secrets out of the code, assemble objects at a single point with a
simple container, and can point out, in a Laravel project's structure, the
equivalent of each folder in this chapter.
:::

:::exercise level=1
Say which catalog folder each file should go into:

1. `Reader.php`, the reader class;
2. `recalculate-fines.php`, run once a month by the scheduler;
3. `report-2026-03.csv`, generated by that script;
4. `library.php`, with the days of the week Casa Amarela opens;
5. the library's logo, which will appear on the screen.

:::answer
1. `src/Readers/` — it is what the system knows how to do.
2. `bin/` — it is a command-line door.
3. `var/` — it was produced by the program, and it does not go to Git.
4. `config/` — it is tuning, not a secret. It goes to Git.
5. `public/` — it is the only folder the browser can reach. The logo is
   meant to be seen.
:::

:::exercise level=2
Register in `bootstrap.php` a factory for the `Importer`, which receives a
`PDO` and a `Logger` through its constructor. Use the `$services` the
closure receives as its argument.

:::answer
```php
$services->register(
    Importer::class,
    fn(Services $s) => new Importer(
        $s->get(PDO::class),
        $s->get(Logger::class),
    ),
);
```

`Services`'s `get` calls each factory passing the container itself — the
`$factory($this)` on the `??=` line. That is how a factory asks for other
services without knowing their factories.

Notice how mechanical this factory is: read the constructor, ask the
container for each type, pass them in order. A program could do that on its
own, by reading the constructor's signature. That is exactly what the
container in chapter 3 of volume 2 does.
:::

:::exercise level=3
Cléber needs to run the catalog on his machine for the first time. He clones
the repository and runs `php bin/import-donations.php`. List, in order, the
errors he will run into and what fixes each one. Then write the
instructions you would put in a `README.md` so the next person runs into none
of them.

:::answer
In order:

1. `Failed opening required '.../vendor/autoload.php'` — `vendor/` does not
   go to Git. Fixed with `composer install`.
2. A PDO error from an empty DSN — `.env` does not go either. `env()`
   returns `null`, and `new PDO` receives nothing. Fixed with
   `cp .env.example .env` and the values filled in.
3. An access-denied or unknown-database error — `.env` points to a database
   that does not exist on his machine yet. Fixed by creating the database
   and running the tables' SQL.
4. Possibly, an error writing to `var/log/` — the folder is also outside
   Git. Fixed with `mkdir -p var/log`, or with `bootstrap.php` creating the
   folder if it is missing.

The `README.md`:

```text
To run
1. composer install
2. cp .env.example .env    and fill in DB_*
3. mysql -u root -p < sql/schema.sql
4. mkdir -p var/log
5. composer import
```

Five lines. The test of a good `README` is to hand it to someone who has
never seen the project and not help them. Laravel automates a good part of
this — volume 2 shows how much — but the `README` is still yours.
:::
