---
source_hash: cf351d8098a6
title: "Errors and debugging"
number: 28
slug: erros-e-debug
part: p5
kicker: "The nightly import imported nothing and finished successfully. PHP had warned three times, to nobody."
goal: >-
  Tell PHP's error levels apart, turn the warning the program ignores into
  an exception it cannot ignore, set up a script's error configuration in
  one place, read a call stack from the bottom up, and log errors with
  enough context for someone to fix them.
---

:::story Zero books, exit code zero
The first nightly import of Mr. Juvenal's donations ran at 2 a.m. In the
morning, the books table had the same four thousand titles as the day
before.

"Was there an error?" asked Márcia.

"No," said Tainá. "It finished successfully. Exit code zero."

"So it imported."

"It imported zero."

Dedé opened the server scheduler's configuration.

```text
0 2 * * * php /srv/catalog/scripts/import-donations.php \
    > /dev/null 2>&1
```

"That `> /dev/null 2>&1` at the end," he said, "sends everything the script
prints to nowhere. The normal messages and the error ones."

"And was there an error?"

"Let's see."

He ran the script by hand, from the root, the way the scheduler ran it:

```text
Warning: fopen(donations.csv): Failed to open stream: No such
file or directory in /srv/catalog/scripts/import-donations.php
on line 7
```

"PHP warned us," said Dedé. "Every night. To `/dev/null`."
:::

:::art caption="PHP warned every night. The warning went nowhere."
src="o-php-avisou-todas-as-noites-o-aviso-ia-para-lugar-nenhum.png"
Minimalist editorial cartoon on a white background, composition split
between night and morning. On the left, at night, a small server on a
table, with a clock reading 2 a.m.; out of it comes a speech bubble with the
word "Warning", which slides straight into a round hole in the floor with a
little sign reading "/dev/null". Inside the hole, a pile of identical
bubbles, one per night. On the right, in the morning, an intern looks at a
screen that shows only "exit code: 0" with a green check mark, and next to
her a manager holding a spreadsheet smiles, satisfied. Few elements, dry
humor, tech-magazine aesthetic.
:::

## The error levels

Not everything PHP calls an error stops the program. The same file can show
three problems and reach the last line:

```php title="levels.php" numbered
<?php

declare(strict_types=1);

$book = ['title' => 'Vidas Secas'];

echo $book['author'], "\n";
echo $total, "\n";
$file = fopen('/does/not/exist.csv', 'r');
var_dump($file);
echo "made it to the end\n";
```

```text
$ php levels.php

Warning: Undefined array key "author" in levels.php on line 7

Warning: Undefined variable $total in levels.php on line 8

Warning: fopen(/does/not/exist.csv): Failed to open stream: No
such file or directory in levels.php on line 9
bool(false)
made it to the end
```

Three warnings, and the program carries on with `null` where it expected an
author, `null` where it expected a total and `false` where it expected a
file. It is the behavior PHP inherited from the days when a half-built page
was better than none.

| Level | What it means | The program |
|---|---|---|
| `Deprecated` | this will stop working in a future version | carries on |
| `Warning` | something went wrong, and PHP improvised a value | carries on |
| `Fatal error` | there is no way to continue | stops |
| uncaught exception | chapter @cap:excecoes | stops |

Table: The levels you will run into. There used to be a fourth, `Notice`,
which PHP 8 promoted almost entirely to `Warning`.

`Deprecated` shows up when you use a feature with a departure date:

```text
$ php -r 'echo strlen(null);'

Deprecated: strlen(): Passing null to parameter #1 ($string)
of type string is deprecated in Command line code on line 1
0
```

It works today. In a future version of PHP, it is a `TypeError`. A
`Deprecated` in the log is a task with a deadline, and the deadline is the
next version upgrade — which, in a project's life, usually comes sooner than
it seems.

:::key
**A warning is not "everything's fine, just a heads-up".** It is PHP saying
it could not do what you asked and put another value in its place. A program
that lets a warning through keeps running with a value nobody chose.
:::

## The warning becomes an exception

Chapter @cap:excecoes taught how to handle exceptions: one stops the program
if nobody catches it, and it carries the call stack. A warning has neither
of those qualities. The solution is to turn one into the other.

```php title="bootstrap.php" numbered
<?php

declare(strict_types=1);

error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', __DIR__ . '/var/log/php.log');

set_error_handler(
    function (int $level, string $msg, string $file, int $ln): bool {
        if ($level === E_DEPRECATED || $level === E_USER_DEPRECATED) {
            error_log("deprecated: {$msg} in {$file}:{$ln}");
            return true;
        }
        throw new ErrorException($msg, 0, $level, $file, $ln);
    },
);

set_exception_handler(function (Throwable $e): void {
    error_log((string) $e);
    fwrite(STDERR, "failed: {$e->getMessage()}\n");
    exit(1);
});
```

One file, four decisions, and every script in the `scripts/` folder starts
with it:

```php
require __DIR__ . '/../bootstrap.php';
```

**`error_reporting(E_ALL)`** turns on every level. A level turned off is not
one problem fewer: it is a problem you do not see.

**The three `ini_set` lines** are the ones from chapter
@cap:primeiro-programa, now in code: do not show errors on the screen, and
write everything to a file the team knows the location of. Written here,
they hold even on a server whose `php.ini` nobody has checked.

**`set_error_handler`** registers a function PHP calls instead of printing
the warning. This one does two things: `Deprecated` goes to the log and the
program carries on — it is not wrong **today**, and a third-party library
with an old feature cannot be allowed to bring the import down. Everything
else becomes an `ErrorException`, an exception PHP already ships for this
purpose, with the level, file and line of the original warning.

**`set_exception_handler`** is the last safety net from chapter
@cap:excecoes: log everything, show little, exit with a non-zero code.

The same script from the story, now with `bootstrap.php`:

```text
$ php /srv/catalog/scripts/import-donations.php > /dev/null
failed: fopen(donations.csv): Failed to open stream: No such
file or directory
$ echo $?
1
```

The message goes to the error output, which `> /dev/null` on its own does
not hide, and exit code 1 tells the scheduler that the night went wrong. In
the log, the whole story:

```text
[26-Sep-2025 02:00:03 UTC] ErrorException: fopen(donations.csv):
Failed to open stream: No such file or directory in
/srv/catalog/scripts/import-donations.php:7
Stack trace:
#0 [internal function]: {closure}(2, 'fopen(donations...', ...)
#1 /srv/catalog/scripts/import-donations.php(7):
   fopen('donations.csv', 'r')
#2 {main}
```

:::pitfall
The `@` operator in front of a call — `@fopen(...)` — silences the warning
on that line. It shows up a lot in old code, always for the same reason: the
warning was annoying. It is the empty `catch` from chapter @cap:excecoes in a
single character.

If a call can fail in an expected way, check its return value, like the
`if ($file === false)` from chapter @cap:manipulacao-de-arquivos. If it
cannot, let the warning become an exception.
:::

## The stack, read from the bottom up

With warnings becoming exceptions, failures start coming with a **call
stack** — the path the program took to reach the error. In the import, one
spreadsheet row had the year written out in words:

```text
Fatal error: Uncaught InvalidArgumentException: invalid year:
eighteen hundred in /srv/catalog/src/Importer.php:26
Stack trace:
#0 /srv/catalog/src/Importer.php(18):
   Importer->year('eighteen hundred')
#1 /srv/catalog/src/Importer.php(11): Importer->save(Array)
#2 /srv/catalog/import.php(12): Importer->import(Array)
#3 {main}
  thrown in /srv/catalog/src/Importer.php on line 26
```

The first line says **what**: the exception, the message, and the file and
line where it was thrown. The stack says **by which route**, and it reads
better from the bottom up, which is the order in which things happened:

1. `{main}` — the program started;
2. `import.php`, line 12, called `import`;
3. `import`, on line 11 of `Importer`, called `save`;
4. `save`, on line 18, called `year` with `'eighteen hundred'`;
5. `year` threw the exception, on line 26.

The argument in parentheses, `'eighteen hundred'`, is often the whole
answer. When it is not, the next question is: **what is the first line, from
the bottom up, that is my code and that I did not expect to see there?** In a
project with a framework, the stack has sixty lines, and fifty-five belong
to the framework. The five that are yours are the ones that matter.

:::key
The message says what; the stack says by which route; the arguments say
with what. Read all three before opening the code. Half the time, the fix
shows up first.
:::

## Investigating: `var_dump`, and a step further

When the stack is not enough, the most used resource is still the one from
chapter @cap:variaveis-e-tipos: stop the program and look.

```php
var_dump($row);
exit;
```

It is fast and works on any server. The cost is that you need to know where
to put it, and remove it afterwards — a forgotten `var_dump` in code that
goes to production is a classic with casualties.

Three habits make this approach more efficient:

- **Shrink the case.** If row 81,407 of the spreadsheet breaks, make a file
  with row 81,407 and nothing else. An error that repeats in one second is
  investigated ten times faster than one that takes four minutes.
- **One hypothesis at a time.** "I think it's the BOM": print the keys. It
  wasn't? Next hypothesis. Changing three things at once and seeing it work
  does not tell you which of the three fixed it.
- **Write down what you found out.** In the notebook, in the review request.
  The same failure comes back eight months later, and the person
  investigating it may be you.

The step further is a **debugger**: Xdebug, a PHP extension that connects to
your editor and lets you stop the program on a line, see every variable and
walk one line at a time. Installation varies by system and editor, and it
can wait until `var_dump` is no longer enough. When that day comes, it is
worth the afternoon.

## Logging with context

`error_log` writes a text. A text like "import failed" answers little at
9 a.m. the next day: which book? which row? which file? The log entry that
helps has the message **and** the data.

```php title="src/Logger.php" numbered
<?php

declare(strict_types=1);

final class Logger
{
    public function __construct(private string $file)
    {
    }

    public function info(string $message, array $context = []): void
    {
        $this->write('info', $message, $context);
    }

    public function error(string $message, array $context = []): void
    {
        $this->write('error', $message, $context);
    }

    private function write(
        string $level,
        string $msg,
        array $ctx,
    ): void
    {
        $line = json_encode([
            'when' => date(DATE_ATOM),
            'level' => $level,
            'message' => $msg,
            'context' => $ctx,
        ], JSON_UNESCAPED_UNICODE);

        file_put_contents(
            $this->file,
            $line . "\n",
            FILE_APPEND | LOCK_EX,
        );
    }
}
```

And the import gains what exercise 3 of chapter
@cap:manipulacao-de-arquivos asked for — counting:

```php
$logger->error('row discarded', [
    'row' => $number,
    'reason' => $e->getMessage(),
]);

// ...at the end of the loop:
$logger->info('import finished', [
    'read' => $read,
    'imported' => $imported,
    'discarded' => $discarded,
]);

if ($read > 0 && $imported === 0) {
    exit(1);
}
```

```text
{"when":"2025-09-27T02:00:41+00:00","level":"error",
 "message":"row discarded","context":{"row":81407,
 "reason":"invalid year: eighteen hundred"}}
{"when":"2025-09-27T02:04:12+00:00","level":"info",
 "message":"import finished","context":{"read":200000,
 "imported":199312,"discarded":688}}
```

One line of JSON per event. `FILE_APPEND` adds to the end instead of wiping
the file, and `LOCK_EX` is chapter @cap:manipulacao-de-arquivos's `flock` in
a constant: two scripts logging at the same time do not mix their lines.

:::term Logging with context
A log entry with three parts: the **level** (info, error...), a **fixed
message**, which can be searched for, and a **context** with that
occurrence's data. "row discarded" is the same in all 688 entries; the row
number and the reason change.

The PHP community standardized this format in PSR-3, the `LoggerInterface`
interface, with one method per level and the `array $context` in all of
them.
:::

## What volume 2 does with errors

Laravel does all of this before your first line runs. It registers a handler
that turns warnings into `ErrorException` — the same `set_error_handler` as
in this chapter — sends `Deprecated`s to a separate log, and has a last
safety net that decides what to show: the detailed page with the stack for
whoever is developing, and a short response, with no file paths, for
whoever is using it.

Logging with context is `Log::error('message', [...])`, which implements
PSR-3. And `var_dump` followed by `exit` has its own name in the framework,
`dd()` — *dump and die*.

:::note In your career
The `> /dev/null 2>&1` in the story was not carelessness on the part of
whoever wrote it. The scheduler e-mails everything a script prints, and
someone, one day, got tired of receiving three hundred warning e-mails a
month. They silenced the output and solved the problem they had.

The real fix is this chapter's: the script stays quiet when it works, and
when it goes wrong it logs in detail, exits with a non-zero code and someone
finds out. A system that speaks up only when it needs to gets listened to.
One that speaks up all the time ends up sent to `/dev/null`.
:::

:::tree title="Where we are now"
catalog/
  bootstrap.php          # E_ALL, logging, warning becomes exception
  src/
    Logger.php           # one JSON line per event
    Importer.php         # counts read, imported, discarded
  scripts/
    import-donations.php # require bootstrap; exit(1) if zero
  var/
    log/                 # outside Git
:::

:::summary
- `Warning` and `Deprecated` do not stop the program; `Fatal error` and an
  uncaught exception do.
- A warning is PHP improvising a value. Do not let it through.
- `set_error_handler` turns warnings into `ErrorException`; `Deprecated`
  goes to the log.
- `bootstrap.php` gathers in one place: `E_ALL`, `display_errors` off,
  logging on, error handler, last safety net.
- The stack reads from the bottom up; look for the first line that is yours.
- `@` is the one-character empty `catch`.
- Log with a level, a fixed message and context. PSR-3 standardizes it.
:::

:::checkpoint
You recognize PHP's error levels, make a warning stop the program instead of
letting it carry on with an improvised value, read a call stack down to the
line that matters, and let a nightly script speak up when it goes wrong —
and only when it goes wrong.
:::

:::exercise level=1
For each message, say the level and whether the program carries on
**without** this chapter's `bootstrap.php`:

1. `Undefined array key "isbn"`
2. `Passing null to parameter #1 ($string) of type string is deprecated`
3. `Uncaught TypeError: daysLate(): Argument #1 ($due) must be of
   type DateTimeImmutable, string given`
4. `file_get_contents(cover.jpg): Failed to open stream`

:::answer
1. `Warning`. It carries on, with `null` in place of the ISBN.
2. `Deprecated`. It carries on.
3. An uncaught exception (`TypeError`, an `Error`). It stops.
4. `Warning`. It carries on, with `false` in place of the contents — and the
   `false` travels on until someone tries to use it as text.

With `bootstrap.php`, items 1 and 4 stop too, and 2 goes to the log.
:::

:::exercise level=2
Read the stack and answer: in which function was the error born, with what
value, and which line **of your code** would you start investigating from?

```text
Fatal error: Uncaught ValueError: "on_loan " is not a valid
backing value for enum CopyStatus
Stack trace:
#0 /srv/catalog/src/Catalog/Copy.php(41):
   CopyStatus::from('on_loan ')
#1 /srv/catalog/src/Catalog/CopyRepository.php(58):
   Copy::fromDatabase(Array)
#2 /srv/catalog/scripts/report.php(19):
   CopyRepository->all()
#3 {main}
```

:::answer
It was born in `CopyStatus::from`, the method of the enum from chapter
@cap:enums-datas-e-valores, called with `'on_loan '` — with a space at the
end.

`from` is right to refuse: the value is not one of the cases. The first line
that is your code is `Copy.php`, line 41, but the useful question goes one
line further: **where did the space come from?** `fromDatabase` receives the
array from the repository, which read it from the database. The space is in
a row of the `copies` table — probably imported from the old System.

A fix in two parts: clean the data (`UPDATE ... SET status = TRIM(status)`)
and decide whether `fromDatabase` should accept dirt. This book's answer is
no: the error showed up, and it is good that it did.
:::

:::exercise level=3
Márcia wants "an e-mail when the import goes wrong". Describe what you would
change in `bootstrap.php` and in the import script, and say why you would
**not** send an e-mail for each discarded row.

:::answer
The e-mail goes into the last safety net, and only there:
`set_exception_handler` is already called exactly when the import has failed
for good. After the `error_log`, it calls the sending, with the message and
the script's name — without the stack, which stays in the log. The other
failure condition is the one at the end of the script: rows read greater
than zero and imported zero. Instead of `exit(1)` directly, it throws an
exception, and lands in the same net.

A discarded row does not generate an e-mail because a two-hundred-thousand-row
import with six hundred discarded would send six hundred e-mails, and by the
third night someone would create a rule to send them to the trash — the
`/dev/null` from the story, now in the inbox. What goes to Márcia is the
summary: one e-mail per night, with the three counts, and only when the
discarded ones exceed a limit she chooses.
:::
