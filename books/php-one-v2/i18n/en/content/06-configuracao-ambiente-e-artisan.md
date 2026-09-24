---
source_hash: 9fbee50e4cc4
title: "Configuration, environment and Artisan"
number: 6
slug: configuracao-ambiente-e-artisan
part: p2
kicker: "Fines started coming out as zero in production, and on no other machine. The cause was an optimization command run during deploy."
goal: >-
  Configure the project without scattering `env()` through the code,
  understand why the configuration cache takes down whoever does that, and
  use Artisan as a mental model instead of a memorized list of commands.
---

:::story Eighty cents times zero
The return screen started printing a fine of R$ 0,00 for everybody. Only in
production. On Dedé's machine, on Tainá's and in the staging environment,
the amount came out right.

"What changed in Friday's deploy?"

Tainá opened the publishing checklist. It had a new line, added the previous
week on the advice of an article about performance.

```text
php artisan config:cache
```

"That's an optimization. It doesn't change behavior."

"It changes the behavior of whoever reads `.env` in the wrong place."

Dedé searched the code. It was in the fine calculator, line 14:

```php
$cents = env('FINE_CENTS', 0);
```

"The default is zero."

"The default is zero."
:::

## `config()` and `env()`: the difference that takes production down

Laravel has two ways of reading configuration, and they look like synonyms
until the day they are not.

**`env('KEY')`** reads straight from the `.env` file.

**`config('file.key')`** reads from a PHP file inside `config/`, which was
loaded when the application started.

The rule the whole framework assumes is short:

:::key
**`env()` only inside `config/`. `config()` everywhere else.**

It is not a style preference. It is what keeps the application working after
`config:cache`, which is the command almost every deploy runs.
:::

The reason is in what `config:cache` does: it reads every file in `config/`,
resolves everything — including the `env()` calls inside them — and writes
the result into a single file. From then on, the application does not even
open `.env`.

And `env()` called outside `config/` starts returning `null`.

```php
// inside config/library.php — right
'daily_fine_in_cents' => (int) env('FINE_CENTS', 80),

// inside a service — returns null after config:cache
$cents = env('FINE_CENTS', 0);
```

In Casa Amarela's case, `null` became the default value `0`, and the zero
default did not raise an error: it produced a zero fine, which is worse,
because someone sees errors.

:::pitfall
The detail that lets this bug get through review is that it **works on your
machine**. In development nobody runs `config:cache`, `.env` is there, and
`env()` answers correctly.

It only shows up where you are not looking. That is why the rule is a rule
and not a recommendation: there is no case in which `env()` outside
`config/` is the right choice.
:::

## The project's configuration file

Casa Amarela's rules were scattered in constants and loose numbers. Now they
have an address:

```php title="config/library.php" numbered
<?php

declare(strict_types=1);

return [
    'loan_days' => (int) env('LIBRARY_LOAN_DAYS', 14),

    'loan_days_children' => 7,

    'limit_per_reader' => (int) env('LIBRARY_LIMIT', 3),

    'limit_in_january' => 5,

    'daily_fine_in_cents' => (int) env('FINE_CENTS', 80),
];
```

```php
$period = config('library.loan_days');
$fine = config('library.daily_fine_in_cents');
```

The file's name becomes the first piece of the key, and the dot goes down
through the array. Any new file in `config/` is found on its own, with
nothing to register.

Notice which values went through `env()` and which did not. **What changes
per environment goes to `.env`**; what is a business rule stays fixed in the
file. The children's loan period is seven days on every server in the world,
and turning it into an environment variable only creates one more place for
the rule to diverge.

:::pitfall
`env()`'s second argument is the default value, and it is a security
decision when the key is a secret.

```php
// dangerous
'api_key' => env('PARTNER_API_KEY', 'test'),
'require_https' => env('REQUIRE_HTTPS', false),
```

A permissive default turns "I forgot to configure it" into "it went live
insecure and nobody noticed". For secrets and security switches, the right
default is `null` or the most restrictive value — and the application failing
loudly at startup is the desired behavior.
:::

## Environments

`APP_ENV` says which environment the application is running in, and three
names are conventional:

| `APP_ENV` | Where | What usually changes |
|---|---|---|
| `local` | your machine | errors on screen, verbose logs, e-mail doesn't go out |
| `testing` | during tests | separate database, nothing external is called |
| `production` | server | errors only in the log, cache on, everything optimized |

Table: The value is read by the framework, which adjusts behavior on its own —
and it can be read by your code with `app()->environment('production')`.

To see what the application thinks its reality is:

```text
$ php artisan about
```

```text
  Environment .................................................
  Application Name ............................... Casa Amarela
  Laravel Version ...................................... 12.0.0
  PHP Version ........................................... 8.3.14
  Environment ........................................ production
  Debug Mode ......................................... OFF
  Maintenance Mode ................................... OFF

  Cache .......................................................
  Config ............................................... CACHED
  Routes ............................................. NOT CACHED
```

One line of that output would have ended the story's Friday in thirty
seconds: **Config: CACHED**.

## Artisan: three tools under one name

`artisan` is a file in the project's root, and what it offers falls into
three families.

**It is a generator.** `make:controller`, `make:model`, `make:migration`,
`make:command`. It writes the file in the right place, with the right name
and the right skeleton — saving less typing than it seems and more doubt than
it seems.

**It is an inspector.** `about`, `route:list`, `config:show`, `db:show`.
These answer questions about the project's state, and they are the ones you
will use on someone else's server at two in the afternoon.

**It is a remote control.** `migrate`, `queue:work`, `schedule:run`,
`cache:clear`, and the commands you write yourself. These **do** something.

```text
$ php artisan route:list
```

```text
  GET|HEAD   /                    ......................
  GET|HEAD   health               ......................
  GET|HEAD   up                   ......................
```

:::key
`route:list` is the only API documentation that never lies, because it is
not written: it is read from the code that is running.

When you join an unfamiliar Laravel project, it is the first command to run.
In ten seconds you have the index of the whole application.
:::

## `tinker`: the console that knows the project

```text
$ php artisan tinker
```

```text
Psy Shell v0.12.4 (PHP 8.3.14 — cli)

> config('library.daily_fine_in_cents')
= 80

> now()->addDays(config('library.loan_days'))->toDateString()
= "2026-01-27"

> app()->environment()
= "local"
```

It is a PHP console with the **whole application loaded**: configuration,
database, your classes, everything resolved by the container. It is for
checking a rule, looking at some data and testing an expression without
creating a file.

:::pitfall
`tinker` in production is a legitimate and dangerous tool for the same
reason: it executes anything, with the application's credentials, leaving no
record of what was done.

Querying is reasonable. Changing data through it is a change with no review,
no history and no way to repeat it — and the next day nobody can explain why
that loan has a different date.

When you need to fix data in production, write a command. It has a name,
reviewed code and it leaves a trail.
:::

## A command of your own

Every night, Casa Amarela needs to recalculate the fines for overdue loans.

```text
$ php artisan make:command CloseDailyFines
```

```php title="app/Console/Commands/CloseDailyFines.php" numbered
<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Services\FineCalculator;
use Illuminate\Console\Command;

class CloseDailyFines extends Command
{
    protected $signature = 'library:fines {--date=}';

    protected $description = 'Calculates fines for overdue loans';

    public function handle(FineCalculator $calculator): int
    {
        $date = $this->option('date') ?? now()->toDateString();

        $result = $calculator->closeDay($date);

        $this->info("Day {$date}: {$result->count} fines");
        $this->info("Total: {$result->total->formatted()}");

        return self::SUCCESS;
    }
}
```

Three things to notice.

**`handle()` receives the calculator as a parameter.** Nobody passed
anything: the container read the type and resolved it, exactly like the
naive container from chapter @cap:um-framework-de-quarenta-linhas.

**The command calculates nothing.** It reads the option, calls the service
and prints the result. All the rules live in a class that does not know a
terminal exists — and that is why the same rule serves the screen, the API
and the command.

**It returns a code.** `self::SUCCESS` is zero; `self::FAILURE` is one. It is
what the operating system's scheduler reads to know whether the night's task
worked.

```text
$ php artisan library:fines --date=2026-01-12
```

```text
Day 2026-01-12: 7 fines
Total: R$ 12,80
```

To run it on its own, the schedule goes into `routes/console.php`:

```php title="routes/console.php" numbered
use Illuminate\Support\Facades\Schedule;

Schedule::command('library:fines')
    ->dailyAt('03:00')
    ->withoutOverlapping();
```

`withoutOverlapping()` stops a run from starting while the previous one is
still going — which happens on the day the database is slow and the 3 a.m.
task has not finished by 3:01.

:::note In your career
"It works on my machine" has a modern version that is harder to spot: it
works everywhere **except** production, because production is the only
environment that runs the optimization commands.

The list is short and worth keeping in your head: `config:cache` breaks
whoever uses `env()` outside `config/`; `route:cache` breaks routes that use
an anonymous function; `view:cache` hides template changes.

When a bug only shows up in production and does not smell like data, start
with `php artisan about` and see what is cached. You will look like a
fortune-teller about three times a year.
:::

:::tree title="Where we are now"
casa-amarela/
  config/
    library.php       # loan period, limit and fine
  app/
    Console/Commands/
      CloseDailyFines.php
    Services/
      FineCalculator.php
  routes/
    console.php       # scheduled at 3 a.m.
    web.php
:::

:::summary
- `env()` only inside `config/`; `config()` in the rest of the code.
- `config:cache` merges the `config/` files into one and makes the
  application stop reading `.env` — `env()` outside there starts returning
  `null`.
- The file name in `config/` becomes the first piece of the key, and it is
  found on its own.
- What changes per environment goes to `.env`; business rules stay fixed in
  the configuration file.
- A permissive default on a secret turns forgetfulness into a silent failure.
- `APP_ENV` distinguishes `local`, `testing` and `production`, and the
  framework adjusts behavior on its own.
- Artisan is a generator, an inspector and a remote control; `about` and
  `route:list` are the first two things to run on an unfamiliar project.
- A command of your own reads options, calls the service and returns an exit
  code — it contains no rules.
:::

:::checkpoint
You create a configuration file and read it with `config()`, explain why
`env()` outside `config/` breaks after deploy, inspect an unfamiliar project
with `about` and `route:list`, and write a command that delegates the work to
a service and returns an exit code.
:::

:::exercise level=1
Classify each value: does it go into `.env`, stay fixed in `config/`, or not
belong in configuration at all?

1. The database password.
2. The loan period, fourteen days.
3. The limit of three books per reader.
4. The mail server's address.
5. The text of the fine message shown on screen.

:::answer
1. **`.env`.** It changes per environment and it is a secret. Never with a
   default value.
2. **Fixed in `config/`.** It is a business rule and it is the same
   everywhere. Having it in `.env` would only create the chance of staging
   and production disagreeing about one of Vera's rules.
3. **Fixed in `config/`**, for the same reason — with one caveat: if the
   association one day wants to change that number without publishing code,
   it stops being configuration and becomes **data**, stored in the database
   and editable on a screen.
4. **`.env`.** It changes per environment, and in development it usually
   points to a fake server.
5. **Neither.** Interface text lives in translation files or in the view.
   Configuration is for values that decide behavior, not for sentences that
   show up on screen.

The criterion for all five fits in a question: *do two different machines
need different values?* If so, `.env`. If not, `config/`. If the answer is
"the client will want to change this on their own", neither.
:::

:::exercise level=2
Write the `library:overdue` command, which lists overdue loans not yet
returned, with a `--reader=` option to filter by reader.

Use `$this->table()` to print the result and return `FAILURE` when there is
any overdue loan, so the scheduler records the day as abnormal.

:::answer
```php title="app/Console/Commands/ListOverdue.php" numbered
<?php

declare(strict_types=1);

namespace App\Console\Commands;

use App\Services\OverdueQuery;
use Illuminate\Console\Command;

class ListOverdue extends Command
{
    protected $signature = 'library:overdue {--reader=}';

    protected $description = 'Lists open overdue loans';

    public function handle(OverdueQuery $query): int
    {
        $reader = $this->option('reader');

        $rows = $query->open(
            $reader === null ? null : (int) $reader,
        );

        if ($rows === []) {
            $this->info('Nothing overdue.');

            return self::SUCCESS;
        }

        $this->table(
            ['Accession', 'Title', 'Reader', 'Days'],
            $rows,
        );

        return self::FAILURE;
    }
}
```

Two decisions deserve a defense.

**The `(int)` on the option.** Every command-line option arrives as text,
like everything that comes from outside. The conversion happens at the
border, and the service receives the right type.

**The `FAILURE` with a non-empty list** is what the question asked for and
deserves an honest caveat: a non-zero exit code usually means "the command
failed", not "the command found things". If this command is scheduled along
with others, a scheduler that stops at the first failure will stop here.

The most common approach in production is to always return `SUCCESS` and
emit a separate alert when the number goes past a limit — because being
overdue is a business fact, not a program defect.
:::

:::exercise level=3
A project has thirty-one `env()` calls scattered through the code outside
`config/`. It has never run `config:cache`, and the team wants to start
running it to gain performance on deploy.

Write the migration plan in four steps, including how to find the calls and
how to make sure no new one appears.

:::answer
**Step 1 — find them.** A search does it, and the result is the work list:

```text
$ grep -rn "env(" app/ routes/ database/ | grep -v "config/"
```

**Step 2 — move, don't translate.** For each call, create the matching key
in `config/`, pointing to the same `env()` with the same default, and swap
the call in the code for `config()`. It is important that the default is
**the same** in this step: changing behavior and changing the mechanism at
the same time is how you end up not knowing which of the two broke.

**Step 3 — review the defaults, now on their own.** With everything in
`config/`, you can read the thirty-one lines together and ask of each one
whether the default makes sense. This is where `env('FINE_CENTS', 0)` shows
up — and this is where it should be fixed, not in the previous step.

**Step 4 — stop it from coming back.** Without this, call number thirty-two
gets in within two weeks. Two ways, and the second is the one that holds:

The cheap one is a line in the code review checklist. The reliable one is an
automatic rule in the verification step, which rejects the change if it
finds `env(` outside `config/`. The same search as step 1, with an exit code.

And a fifth step that is not migration: run `config:cache` **also** in the
staging environment. As long as production is the only place the command
runs, production remains the place where this kind of bug is discovered.
:::
