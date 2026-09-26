---
source_hash: 2e8897e6dffe
title: "Strings"
number: 11
slug: strings
part: p1
kicker: "Half the bugs in a Brazilian system live in the distance between a character and a byte."
goal: >-
  Choose between single and double quotes on purpose, handle accented text
  without breaking it, format values for human reading, and treat all input
  as text until proven otherwise.
---

:::story The three José de Alencars
Vera called Tainá to the counter with the expression of someone about to
show something she is tired of showing.

"Search for Alencar."

Tainá typed it. Three authors came up:

```text
José de Alencar          412 titles
JosÃ© de Alencar          38 titles
JOSE DE ALENCAR           11 titles
```

"They're the same person," said Vera. "It's been about six years."

The first came from normal registration. The second appeared after a
database migration in 2019, when someone exported in UTF-8 and imported as
if it were Latin-1. The third came from the four computers in the reading
room, which have had keyboards without a cedilla since a 2021 procurement —
the clerks learned to type everything in capitals and without accents,
because "that way it always finds it".

"And nobody merged them?"

"They merged them once. Then it came back."
:::

The three José de Alencars are the same bug in three outfits: a text saved
with one encoding and read with another, a text typed without accents, and
a text with an extra space. None of the three raises an error. All three
break Vera's search into pieces.

## The name that arrived broken

```text
$ php -r 'echo strlen("José"), "\n";'
5
```

Four letters, five bytes. The `é` in UTF-8 takes up two.

That is not academic trivia. It is the direct cause of titles cut in half,
database fields overflowing, misaligned reports and that diamond with a
question mark inside.

```text
$ php -r 'echo substr("José de Alencar", 0, 4), "\n";'
Jos�
```

`substr` cut through the middle of the `é`. Half a character was left,
which is no character at all, and the terminal draws the replacement
symbol.

:::term Mojibake
The name of the phenomenon in which `José` becomes `JosÃ©`: a UTF-8 encoded
text being interpreted as Latin-1. The two bytes of the `é` are read as two
separate characters. The word is Japanese and means, literally, "character
transformation".
:::

## One character can take two bytes

PHP has two families of text functions. The old one works with **bytes**.
The `mb_` family — for *multibyte* — works with **characters**.

| Byte (avoid) | Character (use) |
|---|---|
| `strlen` | `mb_strlen` |
| `substr` | `mb_substr` |
| `strtoupper` | `mb_strtoupper` |
| `strtolower` | `mb_strtolower` |
| `str_pad` | no direct equivalent |

Table: The `mbstring` extension needs to be installed. That is why chapter
@cap:o-que-vamos-construir asked you to check the `php -m` list before
anything else.

```text
$ php -r 'echo mb_strlen("José"), "\n";'
4
$ php -r 'echo mb_substr("José de Alencar", 0, 4), "\n";'
José
$ php -r 'echo mb_strtoupper("josé"), "\n";'
JOSÉ
```

The last one is the one that catches people off guard the most:
`strtoupper("josé")` returns `JOSé`, with the accented letter still in
lower case, because the function only knows the ASCII alphabet.

:::key
Operating rule: **in text that may have accents, use `mb_`**. Names,
titles, addresses, notes. The byte functions are still right for what is
guaranteed to be ASCII — an ISBN, a code, a hash — and they are faster,
which only matters at very high volume.
:::

## Text with intent

```php title="quotes.php" numbered
<?php

$title = 'O Cortiço';

echo 'Title: $title', "\n";
echo "Title: $title", "\n";
echo "Title: {$title}", "\n";
```

```text
Title: $title
Title: O Cortiço
Title: O Cortiço
```

**Single** quotes interpret nothing: what is written is what comes out —
including a literal `$title` and `\n`. **Double** quotes interpolate
variables and recognize escape sequences.

The braces in `{$title}` are optional in the simple case and required as
soon as the expression grows:

```php title="braces.php" numbered
<?php

echo "Accession: {$copy['accession']}\n";
echo "First: {$values[0]}\n";
echo "Fine: {$fines['total_in_cents']}\n";
```

:::key
The practical recommendation: use `{$...}` **always** when interpolating,
even when you could leave it out. It costs two characters, eliminates the
whole category of doubt about where the variable name ends, and avoids the
classic bug of `"$title_full"` looking for a variable called `$title_full`
when you wanted `$title` followed by `_full`.
:::

### Heredoc

For long text, there is a form that spares you from escaping quotes:

```php title="heredoc.php" numbered
<?php

$name = 'Marlene';
$days = 9;

$message = <<<TEXT
    Hello, {$name}.

    The book "O Cortiço" is {$days} days overdue.
    The accumulated fine is R$ 7,20.

    Casa Amarela
    TEXT;

echo $message, "\n";
```

The closing identifier sets the indentation: everything aligned with it is
removed from each line. That lets you keep the text indented along with the
code, without the indentation showing up in the output.

There is also `<<<'TEXT'`, with single quotes — the **nowdoc** — which
interpolates nothing. It is the single-quote equivalent for long text.

:::warning
Heredoc is far too comfortable for building SQL, and that is exactly where
it kills. This is a security flaw, not bad style:

```php
$sql = <<<SQL
    SELECT * FROM books WHERE title LIKE '%{$term}%'
    SQL;
```

If `$term` comes from a search field, whoever types `' OR 1=1 --` closes
the quote, adds their own condition and reads the entire table. The command
stopped being a command and became a blank form for the visitor to fill in.

The correct way sends the value **separately** from the command, so that it
can never be read as an instruction. The rule holds from now on and holds
for everything: **do not interpolate external data into SQL, HTML or shell
commands.**
:::

## The receipt cut in half

```php title="receipt.php" numbered
<?php

function receiptLine(string $title, int $cents): string
{
    $title = str_pad(substr($title, 0, 30), 30);
    $value = number_format($cents / 100, 2, ',', '.');

    return $title . str_pad($value, 10, ' ', STR_PAD_LEFT);
}

echo receiptLine('Memórias Póstumas de Brás Cubas', 720), "\n";
echo receiptLine('O Cortiço', 720), "\n";
```

```text
Memórias Póstumas de Brás Cub      7,20
O Cortiço                       7,20
```

Two things wrong in the same output.

The first title was cut at thirty **bytes**, not thirty characters — which
is why it ends earlier than expected, and, with another title, it would cut
an accent in half.

And the alignment of the second line is visibly off. `str_pad` padded up to
thirty bytes; since `Cortiço` has one two-byte character, the column came
out one character shorter than the one above. On a counter's thermal
printer, that is a misaligned column on every receipt with an accent — in
other words, on almost all of them.

## Why the alignment came out crooked

Because **alignment is a visual operation on characters**, and the two
functions used count bytes. The two things coincide in English and diverge
in Portuguese, which is why the bug gets through any test written with
`"Test"` and `"Example"`.

And there is a second layer: even `mb_str_pad` — which only exists from PHP
8.3 on — does not solve the general case, because some characters take up
**two columns** on screen even though they are a single character. Emoji and
ideograms do this. For perfect alignment there is `mb_strwidth`.

## Normalize on input, escape on output

```php title="receipt_fixed.php" numbered
<?php

function receiptLine(string $title, int $cents): string
{
    if (mb_strlen($title) > 30) {
        $title = mb_substr($title, 0, 29) . '…';
    }

    $value = number_format($cents / 100, 2, ',', '.');

    return sprintf('%-30s %9s', $title, $value);
}
```

```text
Memórias Póstumas de Brás Cub…      7,20
O Cortiço                          7,20
```

Three changes. The cut uses `mb_substr` and leaves an ellipsis character,
which signals the truncation to the reader. The alignment uses `sprintf`
with a declared width, which is more readable than two chained `str_pad`s.
And `%-30s` aligns left, `%9s` aligns right — the receipt's format is
declared on a single line, instead of spread over three.

:::anatomy title="The `sprintf` mini-language"
lang: text
code: |
  sprintf('%-30s %9s %05d %.2f %%', $t, $v, $n, $f)
notes:
  - { line: 1, text: "`%s` is text, `%d` an integer, `%f` a decimal." }
  - { line: 1, text: "The number is the minimum width: `%9s` reserves nine columns." }
  - { line: 1, text: "The `-` aligns left; without it, it aligns right." }
  - { line: 1, text: "`%05d` pads with zeros: useful for accession numbers and codes." }
  - { line: 1, text: "`%%` prints a literal `%`." }
:::

For money, however, `sprintf` is not enough. `number_format` is the one
that knows about thousands and decimal separators:

```php
echo number_format(123456.7, 2, ',', '.');   // 123.456,70
```

:::pitfall
`number_format` returns a **string**, and it rounds. Formatting is the last
thing that happens to a value, on output — never in the middle of the
calculation. Adding `"123.456,70"` to another formatted value is the kind of
mistake that produces a plausible, wrong total.
:::

## Search, replace and normalize

```php title="search.php" numbered
<?php

$title = '  O   Cortiço  ';

$clean = trim($title);
$clean = preg_replace('/\s+/u', ' ', $clean);

var_dump($clean);
var_dump(str_contains($clean, 'Cort'));
var_dump(str_starts_with($clean, 'O '));
var_dump(str_ends_with($clean, 'ço'));
```

```text
string(10) "O Cortiço"
bool(true)
bool(true)
bool(true)
```

`str_contains`, `str_starts_with` and `str_ends_with` arrived in PHP 8 and
replaced the old idiom `strpos($a, $b) !== false`, which was correct and
confused everyone because of position zero.

`preg_replace('/\s+/u', ' ', ...)` collapses repeated spaces. The `u`
modifier at the end of the expression is required when the text has
accents — without it, the expression works byte by byte and can split a
character.

And the normalization that would solve the three José de Alencars:

```php title="normalize.php" numbered
<?php

function searchKey(string $text): string
{
    $text = mb_strtolower(trim($text));
    $text = preg_replace('/\s+/u', ' ', $text);

    return transliterator_transliterate(
        'Any-Latin; Latin-ASCII; Lower()',
        $text
    );
}

var_dump(searchKey('JOSÉ  DE ALENCAR'));
var_dump(searchKey('José de Alencar'));
```

```text
string(15) "jose de alencar"
string(15) "jose de alencar"
```

`transliterator_transliterate` comes from the `intl` extension and removes
accents correctly — far more reliable than the `str_replace` tables
circulating on the internet, which forget half the cases.

:::key
The search key is **stored alongside** the original text, never in its
place. Casa Amarela shows "José de Alencar" and searches for "jose de
alencar".

Two fields, two jobs: one is for the person to read, the other is for the
program to compare. Trying to do both with a single field is exactly what
produced the three records.
:::

:::note In your career
A system in Portuguese — or in any language with accents — has a class of
bugs that a system in English does not, and it almost never shows up in
tutorials. Accents, cedillas, upper-case Ç, alphabetical sorting that puts
"Ávila" after "Zanetti", a tax ID with a leading zero turned into a number,
postal codes likewise.

That is local-market knowledge and it is worth more than it looks in an
interview. When someone asks "what hard problem have you solved?", "three
records for the same author because of encoding" is a much better answer
than a binary-tree algorithm — because it is real, it is specific, and it
shows you have dealt with genuinely dirty data.
:::

## Everything that comes in is text

```php
$_GET['page'];        // string "2"
$_POST['days'];       // string "9"
file_get_contents();  // string
fgetcsv();            // array of strings
```

Forms, query strings, files, request bodies, environment variables:
everything arrives as text. The `"2"` that looks like a number is a
`string`, and it will behave like a string everywhere it is not converted.

Converting at the **edge** — right at the entrance, once, in one place — is
what lets the rest of the program work with real types:

```php
$page = (int) ($_GET['page'] ?? 1);
$days = (int) ($_POST['days'] ?? 0);
```

After those two lines, `$page` and `$days` are numbers throughout the rest
of the program, and no function further on needs to be suspicious. Without
them, the `"2"` travels as text until it meets the first `===` and answers
wrong.

:::summary
- Single quotes are literal; double quotes interpolate. Always use
	`{$var}`.
- Heredoc for long text — and never for building SQL.
- `strlen` counts bytes; `mb_strlen` counts characters.
- In text that may have accents, use the `mb_` family.
- `sprintf` declares the format in one line; `number_format` formats money.
- Formatting is the last operation, on output, never in the middle of the
	calculation.
- Store the normalized search key **alongside** the original text.
- Everything that comes in is text; convert at the edge.
:::

:::milestone
End of Part 1. You have types, decisions, loops, functions, arrays and text
— all the PHP a program needs before it becomes a project. From the next
chapter on, one file is no longer enough.
:::

:::exercise level=1
Write a function that formats cents as Brazilian currency, returning
`R$ 1.234,56`.

:::answer
```php
<?php

function reais(int $cents): string
{
    return 'R$ ' . number_format($cents / 100, 2, ',', '.');
}

echo reais(123456), "\n";
```
```text
R$ 1.234,56
```
:::

:::exercise level=2
Write `summarize(string $text, int $limit): string`, which cuts the text at
the **character** limit without splitting a word, adding `…`. If it fits
whole, return it as is.

:::answer
```php
<?php

function summarize(string $text, int $limit): string
{
    $text = trim($text);

    if (mb_strlen($text) <= $limit) {
        return $text;
    }

    $cut = mb_substr($text, 0, $limit);
    $lastSpace = mb_strrpos($cut, ' ');

    if ($lastSpace !== false) {
        $cut = mb_substr($cut, 0, $lastSpace);
    }

    return rtrim($cut) . '…';
}
```
The `!== false` instead of `if ($lastSpace)` is required: `mb_strrpos`
returns `0` when the space is in the first position, and zero is false. A
title that starts with a one-letter word would lose the cut — and that is
why PHP's position functions have a reputation for confusing people.
:::

:::exercise level=3
Casa Amarela wants to merge the three "José de Alencar"s without losing
anything. Describe the procedure, including what you would do **before**
changing any record.

:::answer
**Before anything: a backup, and a restored backup.** Not the generated
file — the restore tested on a separate database. A wrong merge is
irreversible, and "we have a backup" is a sentence that only means
something after someone has restored one.

**Step 1 — measure, without changing anything.** Run the normalization over
the whole list of authors, in memory, and group by the generated key:

```php
$by_key = [];

foreach ($authors as $author) {
    $key = searchKey($author['name']);
    $by_key[$key][] = $author['name'];
}

foreach ($by_key as $key => $names) {
    if (count($names) > 1) {
        echo $key, ': ', implode(' | ', $names), "\n";
    }
}
```

`implode` joins the items of an array into a text, separated by whatever
you pass. The result answers how many cases really exist — and the answer is
usually uncomfortable. There may be three José de Alencars and two hundred
more nobody noticed.

**Step 2 — choose the canonical record, with a written rule.** The rule I
would use: the name with correct accents and the largest number of linked
titles wins. It needs to be written down because someone will audit it, and
because ambiguous cases will show up.

**Step 3 — repoint the references, in a transaction.** All titles of the
duplicate records now point to the canonical one, and the duplicates are
**deactivated**, not deleted. Keeping them makes it possible to undo and to
answer "why did title X change author in November".

**Step 4 — stop it from coming back.** This is the step that was missing
last time, and it is the reason Vera said "then it came back". Without it,
the merge is a cleanup drive that repeats every two years:

- a `key` column generated by the normalization, with a `UNIQUE`
  constraint;
- normalization happening at the input **edge**, in one place;
- and registration suggesting the existing author when the key matches —
  which solves the social problem, not just the technical one. The clerk
  with the cedilla-less keyboard keeps typing without a cedilla, and the
  system takes them to the right record.

**What I would not do:** fix the mojibake with `str_replace('Ã©', 'é')`. That
fixes the cases you saw and leaves the ones you did not, and it creates a
second wrong format when someone runs it again on already-fixed text. The
right conversion is `mb_convert_encoding` at import — and, if the data is
already stored wrong, a one-off migration that identifies exactly the
affected records before touching them.
:::

:::story Four hundred and sixty-one
A month later, with the search key live, Vera tested it.

She typed "alencar". 461 titles came up, from a single author.

She typed "ALENCAR". Same thing.

She typed "  alencar  ", with spaces on both sides, looking at Tainá.

Same thing.

"Now type it wrong," said Tainá.

Vera typed "alencr".

Nothing.

"That one doesn't find it."

"But I know who I want."

"The system doesn't."

Vera wrote it down in her notebook, in the "ask later" section, which
already had four lines.

On Friday, Márcia read the whole section out loud at the status meeting,
lingering at the end of each item.

"That's four. We deliver two by March."

"And the other two?"

"They stay written down. Written down is better than in Vera's head."
:::
