---
source_hash: 24ac46e11d3d
title: "Before you start"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Fifteen years online, half a million loans and a file called functions2_NEW_final.php."
---

This is the folder that runs the front desk of a neighborhood library:

```text
backup_16-03-2019.sql
config.php
connection.php
functions.php
functions2.php
functions2_NEW.php
functions2_NEW_final.php
index.php
loan.php
login.php
report.php
report_new_OK.php
test.php
```

Fourteen thousand lines of PHP written in 2009 and patched ever since by
whoever happened to be available. The most recent backup is from 2019 and
lives in the same folder as the website, which means anyone with the right
address can download the whole catalog.

And it works.

Fifteen years online, half a million loans recorded, not one book lost
because of the software. Vera opens the system at nine, lends, takes
returns, charges fines and closes at six. In those fifteen years it went
down twice, both times because of the hosting.

You are going to replace that system. Not because it is bad — because it has
nowhere left to grow. And the PHP that takes its place barely resembles the
PHP that wrote that folder: this is the PHP of today, taught by someone who
knows the PHP of yesterday.

## The library, the company and the date

The **Casa Amarela Community Library** has four thousand titles and eight
thousand copies. **Vertexo Systems** — one hundred and eighty people,
specialists in digital transformation for clients who cannot describe what
they have today — signed the contract to replace the System. The person who
is going to do the work is you.

And there is a date nobody can push back.

None of this is set dressing. A deadline that does not move, a budget that
shrinks, a requirement that arrives at the worst possible moment and a
legacy system that has to keep serving the front desk while its replacement
is being built — that is what turns a technical choice into a decision.
Choosing between two ways of writing the same thing only gets interesting
when one of them costs you a Tuesday.

## Who shows up

**Dedé** has seven years in the trade, three of them at Vertexo, and is the
voice that explains the why. He has spent eight months hearing that his
promotion will come through next cycle.

**Tainá** is an intern in her third semester. She asks the questions that
take a hurried explanation apart — not out of naivety, but because she is
the only person in the room who loses nothing by saying she did not
understand. She writes everything down in a notebook.

**Vera** has been the librarian at Casa Amarela for thirty-one years. She
knows every lending rule by heart and has never written a single one down.

**Márcia** manages the schedule. Her real job is to receive an impossible
date from above and reissue it downwards in the shape of a sprint.

**Dr. Aurélio** is the chief technology officer. He has never written code
and does not pretend he has.

**Mr. Juvenal** chairs the residents' association. He always brings the new
requirement at the worst possible moment, always wrapped in "it's just a
tiny change", and he is always right about the need.

And the **System**, capital S, is that folder from the beginning. It is not
the villain. Every modern thing that appears here will be measured against
it — and in some of those measurements, the System wins.

## How the book shows things

Code looks like this, sometimes with the file name:

```php title="fine.php"
$fine_in_cents = 720;
echo 'R$ ' . number_format($fine_in_cents / 100, 2, ',', '.');
```

What the terminal answers appears with no file name and no highlighting:

```text
R$ 7,20
```

And when the program breaks — which will happen a lot, on purpose — the
error comes in full, from beginning to end, because the lines in the middle
are the ones that matter.

:::key
A terminal command appears with a `$` in front. The `$` stands for the
prompt and is not part of the command: do not type it. In PHP this is more
confusing than in other languages, because `$` also starts every variable —
inside a PHP code block it is code; in the first column of a terminal
block, it is the prompt.
:::

You do not need to install anything to start reading. When the first
program needs to run, the installation comes with it, along with the test
that confirms it worked.

:::practice
Read with a terminal open. Run the examples, change the values and try to
break them. Memory of a language is born faster from an unexpected output
than from a memorized definition.
:::

The date nobody can push back is March 31. Until then, Vera opens at nine
and the System keeps the desk running.
