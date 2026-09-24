---
source_hash: a6f6540e699f
title: "The first program"
number: 3
slug: primeiro-programa
part: p1
kicker: "Two lines of PHP, three different installations on the same machine and a blank page that is no error at all."
goal: >-
  Write, save and run PHP from the terminal and from the browser; comment
  code; print in four different ways; and find the error message the server
  swallowed.
---

:::story The nephew's hosting
"I got the hosting," announced Mr. Juvenal, with the satisfaction of
someone who had solved the month's problem before ten in the morning.

"Vertexo was going to rent a server," said Márcia.

"But this one is free. Mrs. Marlene's nephew. He has a company."

The control panel opened in a window straight out of 2011, with gradient
buttons and a floppy-disk icon in the menu. In the corner, a field:

```text
PHP Version: 5.6.40    [Change]
```

Dedé clicked **Change**. The options were 5.4, 5.6 and 7.0.

"Is there 8?"

"The nephew said 8 is unstable."

PHP 8 had been released six years earlier. 5.6 had stopped receiving
security fixes nine years earlier.

"And access? Is there SSH?"

"There's FTP."

Mr. Juvenal handed over a folded piece of paper with the username, the
password and — handwritten, in a corner, in a different color pen — the note
*"don't touch the old folder"*.

Márcia put the paper away in the project folder.

"Is this a risk for March?"

"This is a risk for today."
:::

Running PHP looks like the simplest part of the job, and it is where the
trap that eats the most time from beginners lives: **the PHP running in
your terminal is almost never the same one running on the server.**

## Two PHPs on the same machine

```text
$ which php
/usr/bin/php
$ php -v
PHP 8.3.14 (cli)
```

The `(cli)` at the end of the first line is the detail that matters. It
says this is the **command-line** PHP — the one that answers when you type
`php` in a terminal.

There is another one, the one that serves the browser. It can be a
different version, with a different configuration file and a different set
of extensions, on the same machine, at the same time.

:::term SAPI
*Server API*: the way PHP was attached to whatever calls it. `cli` is the
terminal. `fpm` is the process that sits waiting for Nginx to send it work.
`apache2handler` is PHP embedded inside Apache. The same `.php` file can
behave differently in each one, because each one reads its own `php.ini`.
:::

:::pitfall
The classic symptom: you install an extension, `php -m` shows it is there,
and the page in the browser keeps saying it does not exist.

There are two PHPs. Confirming it takes ten seconds — create a file with
`<?php phpinfo();` inside, open it **through the browser** and compare the
version and the `php.ini` path with what `php -v` said in the terminal. Then
delete the file: `phpinfo()` shows the server's entire configuration, and
that is not information to leave public.
:::

## One tag, one output

```php title="hello.php" numbered
<?php

echo "Hello, Casa Amarela\n";
```

```text
$ php hello.php
Hello, Casa Amarela
```

Done. You programmed.

It is worth unpacking the three lines, because each one has a decision
inside it.

**`<?php`** switches PHP mode on. Everything before that tag — including a
blank space or an empty line — is sent straight to whoever asked for the
page, without going through the interpreter. That looks irrelevant and it
will matter two paragraphs from now.

**`echo`** prints. It is not a function, it is a language construct, and
that is why it works without parentheses.

**`"\n"`** is a line break. Inside double quotes, the backslash turns on
"the next character is special" mode: `\n` becomes a line break, `\t`
becomes a tab. Inside single quotes that does not happen — `'\n'` is two
characters, a backslash and an n.

And the **semicolon** at the end closes the statement. Forgetting one is
the number one beginner's mistake, and the message it produces has a quirk
worth knowing before you run into it.

## Commenting

Three forms, and you will use two:

```php title="comments.php" numbered
<?php

// one line, the standard form

# also one line, inherited from the shell, rare today

/*
   several lines
   for when the explanation doesn't fit in one
*/

echo "Casa Amarela\n"; // a comment at the end of a line works too
```

`//` is the one people use. `#` works and shows up in old code. The
`/* */` block is for long explanations — and it has a variant with two
asterisks at the opening, `/** */`, which analysis tools read as
documentation.

:::key
A comment that explains **what** the line does is noise: the line already
says it. A comment that explains **why** the decision was that one is the
most valuable thing you can leave in a file.

`// add 1 to the counter` helps nobody. `// Vera asked that Sunday not
count as late; the library doesn't open` will still be doing its job five
years from now.
:::

## The tag you are not going to close

The closing tag, `?>`, is **optional at the end of a file**. More than
optional: in a file that contains only PHP, it is avoided by convention, and
the reason is concrete.

:::compare left="The file that will cause trouble" right="The right way" lang="php"
<?php
function fine(): int
{
    return 80;
}
?>
---
<?php
function fine(): int
{
    return 80;
}
:::

Notice the line break after the `?>` on the left. It is outside PHP mode,
so it is content — and it is sent to the browser as if it were part of the
page.

Months later, when someone tries to redirect the user or send any other
header information, they will get this:

```text
Warning: Cannot modify header information - headers already
sent by (output started at /app/functions.php:7) in
/app/index.php on line 3
```

The message is generous: it gives the file and the exact line where the
output started. The cause is a blank space after a `?>` that did not need
to exist.

:::key
A file that contains only PHP does not get a `?>`. It is one of the few
style rules justified by a technical consequence, not by taste.
:::

## Four ways to print

```php title="output.php" numbered
<?php

$title = "O Cortiço";
$copies = 3;

echo "We have ", $copies, " copies of ", $title, "\n";
echo "We have {$copies} copies of {$title}\n";
printf("We have %d copies of %s\n", $copies, $title);
```

```text
We have 3 copies of O Cortiço
We have 3 copies of O Cortiço
We have 3 copies of O Cortiço
```

The first line uses `echo` with several pieces separated by commas. They
come out glued together, in order.

The second uses **interpolation**: inside double quotes, PHP replaces the
variable's name with its value. The braces in `{$title}` are not required
when the name clearly ends, but they are required when it does not — and
always using them saves you the decision.

The third uses `printf`, which takes a template and the values to fit into
it. `%d` says "an integer goes here" and `%s` says "a piece of text goes
here". The values come afterwards, in the order of the placeholders. It is
more work for a short sentence and it is what you will want when you need
to align columns or control decimal places.

There is also `print`, which does almost the same as `echo` and accepts a
single value. The practical difference is irrelevant; use `echo`.

And there is a fourth one, which is not output for the user — it is for
you:

```text
$ php -r 'var_dump(3, "3", 3.0, true, null);'
int(3)
string(1) "3"
float(3)
bool(true)
NULL
```

`var_dump` prints the **type** along with the value. Notice the difference
between `int(3)` and `string(1) "3"`: for `echo`, both would come out as
`3`, and you would never know which is which. This is the tool that answers
instead of making you guess, and it will appear on almost every page from
here on.

## From the terminal to the browser

PHP was born for the web, and the second way to run it is over HTTP. There
is no need to install Apache or Nginx: PHP itself ships with a small
server.

```text
$ php -S localhost:8000
[Thu Nov 21 10:02:11 2026] PHP 8.3.14 Development Server
(http://localhost:8000) started
```

The command keeps running and takes over the terminal — that is how it is
supposed to be. It serves the files in the folder you were in when you
started it. Open <http://localhost:8000/hello.php> and the same sentence
appears, now inside a page. To stop it, `Ctrl+C`.

:::diagram type="flowchart" caption="Two paths, the same file: what changes is who calls it and where the output goes."
nodes:
  - { id: arq, type: io,      text: "hello.php" }
  - { id: cli, type: process, text: "php hello.php (CLI)" }
  - { id: web, type: process, text: "php -S (server)" }
  - { id: t,   type: io,      text: "terminal" }
  - { id: n,   type: io,      text: "browser" }
edges:
  - { from: arq, to: cli }
  - { from: arq, to: web }
  - { from: cli, to: t }
  - { from: web, to: n }
:::

:::warning
The name it prints is literal: **Development Server**. It handles one
request at a time, has no decent URL rewriting and cannot take any load at
all. For learning and investigating, it is enough. Production is another
conversation — and it is certainly not Mrs. Marlene's nephew's hosting.
:::

## The right file, on the wrong server

:::story Two servers
Tainá edited the file, saved, reloaded. Nothing changed.

She saved again. Reloaded again. Nothing.

She added a giant `echo "TEST"` at the top, with thirty exclamation marks.
Reloaded. Nothing.

She deleted the entire file. Reloaded. The page was still there, working
perfectly, displaying content that technically no longer existed.

That was the point at which she called Dedé, already doubting the nature of
reality.

He asked for the URL and opened her terminal history. There were two
`php -S` running: one on port 8000, opened that morning, and another on
8080, left open and forgotten two weeks earlier, serving an old copy of the
folder.

The browser was on 8080.

"It'll happen again," he said. "When it does, the first question isn't
'what did I write wrong'. It's 'what's running'."

Tainá wrote it down in her notebook. It was the second line on the list.
:::

Half an hour later, on the right port, came the second problem: a blank
page. No error, no text, nothing. Empty page source.

## The error points to where it noticed

She had written this:

```php title="broken.php" numbered
<?php

$title = "O Cortiço"
echo $title;
```

Running it from the terminal, the message shows up:

```text
PHP Parse error:  syntax error, unexpected token "echo",
expecting "," or ";" in /app/broken.php on line 4
```

The error points to **line 4**, and the problem is on **line 3**: a
semicolon is missing. That is not a flaw in the message. The parser was
reading line 3 and it could still continue — nothing stops an expression
from spanning several lines. It only found out something was missing when
it hit, on the next line, a word that cannot appear there.

:::key
A syntax error points to where the parser **noticed**, not to where you
**made the mistake**. Rule of thumb: read the line it points to and the one
before. Nine times out of ten the problem is on the previous one — a
semicolon, a parenthesis or a brace.
:::

A `Parse error` has a characteristic that is scary the first time: it stops
the **entire** file from running. Nothing comes out, not even the lines
before the error, because PHP parses the whole file before executing the
first statement.

## Where the message went

But Tainá saw no message at all. She saw a blank page.

```text
$ php -i | grep -E "display_errors|error_log"
display_errors => Off => Off
error_log => no value => no value
```

`display_errors` off means "don't show errors to whoever asked for the
page". `error_log` with no value means "and don't write them to any file".
Together, the two settings send the message to the server process's error
output — which, with PHP-FPM, ends up in `/var/log/php8.3-fpm.log`, and not
where she was looking.

The information existed. It was produced, formatted and filed somewhere
else.

**In development, turn everything on:**

```text title="php.ini — development only"
display_errors = On
display_startup_errors = On
error_reporting = E_ALL
```

**In production, the opposite — and it is not optional:**

```text title="php.ini — production"
display_errors = Off
error_log = /var/log/php/errors.log
error_reporting = E_ALL
```

:::warning
`display_errors = On` in production is a security flaw. PHP's error message
gives away absolute file paths, function names, sometimes a piece of a
database query and variable values. It is free information for anyone
probing the site.

Notice that `error_reporting` stays at `E_ALL` in both cases. The
difference is not **logging less** — it is **showing it to whom**. In
production the detail stays in the log, for the team, and the visitor sees a
short page.
:::

And there is a check that costs nothing:

```text
$ php -l broken.php
PHP Parse error: syntax error, unexpected token "echo" ...
Errors parsing broken.php

$ php -l hello.php
No syntax errors detected in hello.php
```

The `-l` comes from *lint*: it checks the syntax without running the file.
It is the cheapest check there is and it runs in milliseconds.

### The blank page, in four hypotheses

The blank page is scary because it looks like an absence of information. It
is almost always one of these four things:

| Cause | How to confirm |
|---|---|
| Syntax error with `display_errors` off | `php -l file.php` |
| Fatal error at run time | read the PHP or server log |
| Memory or time exhausted | look for `Allowed memory size` in the log |
| Genuinely empty output, no error | `var_dump` before the suspicious spot |

Table: None of them is solved by reloading the page, which is exactly what
everyone does for the first five minutes.

:::practice
Create a file that calls a function that does not exist — `discount()`,
for example — and run it both ways: `php file.php` and through the browser
with `php -S`. Compare what shows up in each.

That difference is the same one that will exist between your machine and
the production server, and seeing it once saves hours later.
:::

:::note In your career
Before agreeing to touch a system you do not know — freelance, new project,
new company — four questions are worth more than any amount of code
reading:

1. **Which PHP version runs in production?** It defines what you can use.
2. **How do I deploy a change?** If the answer is "FTP", you have just
	 found the project's biggest risk, and it is not technical: anyone with
	 that piece of paper can publish anything, and nobody will know who did
	 it.
3. **Where are the logs?** If nobody knows, you will be debugging blind.
4. **Is there an environment identical to production where I can make
	 mistakes?** If there is not, the test environment is production — and
	 someone needs to know that in writing, before the first incident, not
	 after.

Asking these questions is not distrust. It is the equivalent of an
electrician asking where the circuit breaker is.
:::

:::summary
- There are two PHPs on your machine: the terminal's and the server's. Each
	one reads its own `php.ini`.
- A file with only PHP does not get a `?>` — a space after it becomes
	output, and breaks headers months later.
- A good comment explains why, not what.
- `echo` prints; interpolation swaps a variable for its value inside double
	quotes; `printf` fits values into a template; `var_dump` shows the type.
- `php -S` starts a development server, and that is all it is good for.
- A syntax error points to where the parser noticed: read the line before.
- A blank page is a hidden error, not the absence of an error.
:::

:::exercise level=1
Write a file that prints the library's name, the number of titles in the
catalog and the opening hours, using variable interpolation. Then swap the
interpolation for `printf` and compare the two versions.

:::answer
```php
<?php

$name = "Casa Amarela";
$titles = 4000;
$hours = "9am to 6pm";

echo "{$name}: {$titles} titles, {$hours}\n";
printf("%s: %d titles, %s\n", $name, $titles, $hours);
```

```text
Casa Amarela: 4000 titles, 9am to 6pm
Casa Amarela: 4000 titles, 9am to 6pm
```

For a short sentence, interpolation is more readable. `printf` starts to
win when the format matters — decimal places, column width, alignment.
:::

:::exercise level=2
Reproduce the blank page on purpose: create a file with a syntax error and
serve it with errors turned off. Then find the message without turning
errors back on.

:::answer
```text
$ php -S localhost:8000 -d display_errors=0
```

Open the broken file in the browser: blank page. Now, without touching any
configuration:

```text
$ php -l broken.php
PHP Parse error: syntax error ... on line 4
```

`-d` overrides a directive just for that run, which is handy for
reproducing production behavior without editing `php.ini`.

Notice also that the built-in server writes errors to the very terminal it
was started in — in this case, the information was in the window next door
the whole time. On a real server, it would be in a log file.
:::

:::exercise level=2
Create two files: a `functions.php` that ends with `?>` followed by a blank
line, and an `index.php` that does `require 'functions.php'` and then calls
`header('Location: /dashboard')`. `require` inserts the contents of one
file into the other; `header` sends a piece of HTTP header information —
here, a redirect. Run it and read the error.

:::answer
```text
Warning: Cannot modify header information - headers already
sent by (output started at /app/functions.php:6) in
/app/index.php on line 4
```

The message hands over the culprit with file and line: `functions.php:6` is
the blank line after the `?>`. Delete the last two lines of the file and the
redirect works again.

It is worth reproducing this once because the message is frightening and
the cause is ridiculous — and because, in a legacy system with forty
`include`s, finding out which file has the extra space is exactly that
number at the end of the first line.
:::

:::exercise level=3
The file below works in your terminal and returns a blank page on Casa
Amarela's hosting. List four hypotheses, in the order you would check them,
and say how you confirm each one.

```php
<?php
require 'config.php';
$connection = connect();
echo "ok";
```

:::answer
**1. A different PHP version.** Your terminal runs 8.3; the hosting runs
5.6. Any syntax newer than 5.6 is a syntax error there and valid code here.
I confirm it with a `phpinfo()` served **through the same path as the
application**, not through the terminal.

**2. Errors turned off hiding a fatal error.** This is the most likely
hypothesis, because the symptom is exactly this one. I confirm it by reading
the log; if nobody knows where it is, the `phpinfo()` from hypothesis 1
already answers that.

**3. `config.php` not found.** A `require` with a relative path depends on
the working directory, which on the server is not the same as in the
terminal. A `require` that fails is a fatal error — and, with errors off,
that is a blank page. I confirm it with `var_dump(getcwd())`, which prints
the current directory, and fix it by switching to
`require __DIR__ . '/config.php'`, where `__DIR__` is the folder of the file
itself.

**4. A missing extension.** The `connect()` function probably talks to a
database. If the matching extension is not compiled into the server's PHP,
the function does not exist. I confirm it by looking for the extension in
the `phpinfo()` output.

The order is the valuable part of the exercise. The first two hypotheses
are thirty-second checks that reveal the other two: `phpinfo()` answers
version, errors, log path and extensions all at once. Investigating the
code before looking at that page is the most common method mistake among
beginners — the information already exists, someone just needs to read it.
:::

:::story Optimized for 5.6
Two weeks later, Mrs. Marlene's nephew replied to the ticket about PHP 8.

> *"We do not recommend it. Our infrastructure is optimized for 5.6, which
> is the most stable version on the market."*

Dedé forwarded it to Vera, without any comment.

The reply came in four minutes:

> *"He also thinks the System is great."*

He forwarded it to Márcia too. That one took longer.

> *"Put it in the minutes. If we switch hosting in March, I want it written
> down in January that I warned you."*
:::
