---
source_hash: 697b83e54152
title: "Working with files"
number: 26
slug: manipulacao-de-arquivos
part: p5
kicker: "The donations spreadsheet had two hundred thousand rows. The script that read it all at once stopped on line three, having read none of them."
goal: >-
  Read and write files without depending on the folder the script was
  called from, read a large file one line at a time, separate reading from
  processing with a generator, deal with encoding and the BOM, and write
  without leaving half a file behind.
---

:::story On line three
Mr. Juvenal arrived with a USB stick and a smile.

"The state school's donation. All in one spreadsheet. Two hundred thousand
books."

"Two hundred thousand?" asked Vera. "The library has four thousand."

"Two hundred thousand rows. It's their whole catalog, they're closing down.
We pick what we want."

Tainá exported the spreadsheet to CSV — nine megabytes — and ran the import
script she had written for the small donations, the fifty-row ones.
Vertexo's staging server had a low memory limit, set on purpose by Nonato
years earlier.

```text
PHP Fatal error: Allowed memory size of 16777216 bytes exhausted
(tried to allocate 4096 bytes) in /srv/import.php on line 3
```

"Line three," she said. "That's the line that reads the file."

Dedé looked at the line.

```php
$rows = file('donations.csv');
```

"It reads the whole file into memory before you look at the first line."

"And Mr. Juvenal's books?"

"They're all in memory. That's why it ran out."
:::

## Relative to what

Before memory, a trap Tainá's script had and had not shown yet.
`file('donations.csv')` looks for the file **in the folder PHP was called
from**, not in the folder where the script lives:

```text
$ cd /srv && php import.php
(works)

$ cd / && php /srv/import.php
Warning: file(donations.csv): Failed to open stream: No such
file or directory in /srv/import.php on line 5
```

The server's task scheduler, which runs the import in the early hours,
calls scripts from the root. Every relative path breaks there, and not on
the machine of whoever tested it.

PHP gives you the file's own folder in a constant:

```php
$path = __DIR__ . '/donations.csv';
```

`__DIR__` is the folder of the PHP file in which the line is written —
always, wherever it is called from. Every path from this chapter on starts
from it, or from a setting that says where the files live.

:::key
A relative path is relative to the folder of whoever **called**, and that
changes between the terminal, the scheduler and the web server. Build the
path from `__DIR__`, and the script finds the files wherever it runs.
:::

## Reading everything and reading one line at a time

Chapter @cap:do-arquivo-ao-banco used `file_get_contents` and
`file_put_contents`: the whole file becomes a text, or a text becomes the
whole file. For a fifty-book JSON, that is right. For a
two-hundred-thousand-row spreadsheet, it is the mistake in the story.

Measuring, on the server without the limit:

```php title="all.php" numbered
<?php

declare(strict_types=1);

$rows = file(__DIR__ . '/donations.csv');

echo count($rows), " rows\n";
echo round(memory_get_peak_usage() / 1048576, 1), " MB\n";
```

```text
$ php all.php
200001 rows
28.5 MB
```

A nine-megabyte file takes up twenty-eight and a half in memory: two
hundred thousand separate texts, each with the cost of being a PHP value.
`memory_get_peak_usage()` returns the maximum memory the script used so
far, in bytes.

The alternative is to open the file and read **one line at a time**:

```php title="line-by-line.php" numbered
<?php

declare(strict_types=1);

$file = fopen(__DIR__ . '/donations.csv', 'r');
if ($file === false) {
    throw new RuntimeException("donations.csv didn't open");
}

$total = 0;
try {
    while (($line = fgets($file)) !== false) {
        $total++;
    }
} finally {
    fclose($file);
}

echo "{$total} lines\n";
```

`fopen` opens the file and returns a **resource**: an identifier PHP uses
to read a bit at a time. The `'r'` is the mode — reading. `fgets` reads up
to the end of the next line and returns `false` when the file ends.
`fclose` hands the file back to the system.

The `finally` from chapter @cap:excecoes is there on purpose: if something
fails in the middle of reading, the file is closed all the same.

## CSV, and the generator that separates reading from using

A CSV spreadsheet has fields separated — by semicolons, when it comes from
an Excel set to Portuguese — and quotes around the ones that contain the
separator. Splitting by hand with `explode(';', $line)` breaks on the first
title with a semicolon in it. `fgetcsv` reads a line and hands it back
already split into fields.

And there is a way to write "read the CSV line by line" just once, and use
it anywhere as if it were an array:

```php title="csv.php" numbered
<?php

declare(strict_types=1);

function readCsv(string $path): Generator
{
    $file = fopen($path, 'r');
    if ($file === false) {
        throw new RuntimeException("didn't open: {$path}");
    }

    $read = fn() => fgetcsv($file, separator: ';', escape: '');

    try {
        $header = $read();
        while (($fields = $read()) !== false) {
            yield array_combine($header, $fields);
        }
    } finally {
        fclose($file);
    }
}

$total = 0;
$inRepair = 0;

foreach (readCsv(__DIR__ . '/donations.csv') as $book) {
    $total++;
    if ($book['status'] === 'in_repair') {
        $inRepair++;
    }
}

echo "{$total} books, {$inRepair} needing repair\n";
echo round(memory_get_peak_usage() / 1048576, 1), " MB\n";
```

```text
$ php csv.php
200000 books, 28571 needing repair
0.4 MB
```

Zero point four megabytes, against twenty-eight and a half. And the same
result with the staging server's sixteen-megabyte limit.

`yield` is what makes `readCsv` a **generator**. A function with `yield`
does not run all the way through when called: it returns a `Generator`
object, which `foreach` walks through. On each round, the function runs up
to the next `yield`, hands over that value, and **pauses** there, with the
file open, until the `foreach` asks for the next one.

:::term Generator
A function with `yield`. When called, it does not run: it returns a
`Generator`. Each round of the `foreach` over it runs the function up to the
next `yield` and receives the value handed over. Only one value exists in
memory at a time.

Whoever uses the generator writes an ordinary `foreach`, without knowing
whether the values come from an array, from a nine-megabyte file or from a
database query.
:::

`array_combine($header, $fields)` joins the two lists into an array with
names: `['title' => 'Livro 1', 'author' => ...]`. The rest of the program
reads `$book['status']`, not `$book[3]`.

The named arguments — `separator: ';'` — are the ones from chapter
@cap:funcoes. `escape: ''` turns off an old escape character in PHP's CSV
handling that does not exist in Excel's CSV, and which PHP 8.4 starts
requiring you to state.

:::key
The generator separates **where the data comes from** from **what is done
with it**. The import, the count and the report use the same `readCsv`. If
tomorrow the donations arrive in another format, the generator changes, and
no `foreach` does.

In volume 2, Eloquent has the same idea under another name: walking through
a table of millions of rows without loading it all.
:::

## Encoding, and three bytes at the start

The titles in Mr. Juvenal's spreadsheet arrived like this:

```text
Livro nÃºmero 1
```

It is the `ú` of "número" in UTF-8, read as if it were another encoding —
the bug from chapter @cap:strings, now coming from a file. Two causes show
up often in spreadsheets exported from Excel.

**The file is not in UTF-8.** Old Excel writes CSV in Windows-1252, the
encoding that came before UTF-8 on Brazilian (and most Western) computers.
The conversion is one line, done at the entrance:

```php
$title = mb_convert_encoding($fields[0], 'UTF-8', 'Windows-1252');
```

**The file is in UTF-8 and starts with a BOM.** A BOM is three invisible
bytes — `EF BB BF` — that some programs put at the start of a file to
announce it is UTF-8. PHP does not remove them. They stick to the first
field of the header, and `$book['title']` stops existing, because the key is
actually called `"\xEF\xBB\xBFtitle"`.

```php
$bom = fread($file, 3);
if ($bom !== "\xEF\xBB\xBF") {
    rewind($file);
}
```

`fread` reads the first three bytes. If they are not the BOM, `rewind` goes
back to the start of the file and nothing is lost. Those four lines go into
`readCsv`, right after the `fopen`.

:::pitfall
The BOM does not show up when you open the file in the editor, nor when you
print the header in the terminal. The symptom is a key that "exists" and
gives `Undefined array key "title"`. When a key you are looking at is not
found, print it with `var_dump(array_keys($row))`: `string(8)` for a
five-letter word gives away the three extra bytes.
:::

## Writing without leaving half a file

The report of chosen donations goes back to Mr. Juvenal as a CSV, for him
to open in Excel:

```php title="export.php" numbered
<?php

declare(strict_types=1);

function writeCsv(string $path, array $rows): void
{
    $temporary = $path . '.tmp';
    $file = fopen($temporary, 'w');
    if ($file === false) {
        throw new RuntimeException("didn't write: {$temporary}");
    }

    try {
        fwrite($file, "\xEF\xBB\xBF");
        foreach ($rows as $row) {
            fputcsv($file, $row, separator: ';', escape: '');
        }
    } finally {
        fclose($file);
    }

    rename($temporary, $path);
}

writeCsv(__DIR__ . '/chosen.csv', [
    ['title', 'author'],
    ['Vidas Secas', 'Graciliano Ramos'],
    ['O Cortiço', 'Aluísio Azevedo'],
]);
```

Three decisions.

**The BOM goes in on purpose.** Here it is useful: it is what makes Excel
open the accents correctly.

**`fputcsv`** writes each line with the right separator and quotes — the
reverse of `fgetcsv`.

**The file is written under another name and renamed at the end.** If the
script dies in the middle — memory, a power cut, an error on row eight
thousand — what is left is a half-written `chosen.csv.tmp`, and the previous
day's `chosen.csv` is still whole. `rename` swaps one file for the other in
one go: whoever opens the file never sees half a report.

Chapter @cap:do-arquivo-ao-banco showed the other half of the problem: two
people writing to the same file at the same time. For that there is
`flock`, which locks the file while someone writes — and there is the
database, which was that chapter's answer and is still this one's. Files are
for entering and leaving the system. Shared state lives in the database.

## What volume 2 does with files

In volume 2, two subjects come back dressed as framework.

**Uploads**: the book's cover, sent through the screen. The file arrives in
a temporary folder, with a name chosen by whoever sent it — and that name
cannot become a path, because `../../.env` is also a name.

**Storage**: Laravel provides a layer, `Storage`, that writes to local disk
or to a cloud file service with the same code. Underneath, it is this
chapter's `fopen`, `fwrite` and `rename`.

:::note In your career
"It works with the test file" is the sentence that precedes most problems
with files: the test file has fifty lines, is in UTF-8 without a BOM and
sits in the same folder as the script. The production one has two hundred
thousand, came from somebody's Excel and is read by the scheduler from the
root.

Before calling an import done, test it with a large file, with accents,
with a BOM, and calling the script from another folder. It is four minutes,
and it is what separates the script that works from the one that works on
your machine.
:::

:::tree title="Where we are now"
catalog/
  src/
    Import/
      Csv.php              # read(): generator, BOM, ; separator
                           # write(): temporary + rename
  scripts/
    import-donations.php   # __DIR__, never a relative path
:::

:::summary
- A relative path is relative to whoever called. `__DIR__` is the file's own
  folder.
- `file` and `file_get_contents` load the whole file; `fopen` and `fgets`
  read one line at a time. `fclose` in the `finally`.
- `fgetcsv` splits the fields respecting quotes; `fputcsv` writes.
- A function with `yield` is a generator: it hands over one value at a time
  and pauses. It separates the data's origin from what is done with it.
- Convert encoding at the entrance; the BOM sticks to the first field and
  has to go.
- Write to a temporary file and rename at the end: there is never half a
  file left over.
:::

:::checkpoint
You read a two-hundred-thousand-row CSV with constant memory, write the
reading as a reusable generator, recognize the BOM by the symptom of the key
that does not exist, and write a file without the risk of leaving it half
done.
:::

:::exercise level=1
Say which function you would use in each case, and why:

1. Reading the `library.json` configuration, 2 KB.
2. Counting the lines of a 3 GB log.
3. Writing the monthly report that other people open at any time.

:::answer
1. `file_get_contents` and `json_decode`. The file is small and is needed
   whole at once.
2. `fopen` and `fgets` in a loop — or a generator. `file` would try to put
   three gigabytes into memory.
3. Write to a temporary file and rename it. Whoever opens it during the
   write sees the whole previous report, not half of the new one.
:::

:::exercise level=2
Write a generator `onlyInRepair(Generator $books): Generator` that receives
the generator from `readCsv` and only hands over books whose `status` is
`in_repair`. Use the two together to write a CSV with just those books.

:::answer
```php
function onlyInRepair(Generator $books): Generator
{
    foreach ($books as $book) {
        if ($book['status'] === 'in_repair') {
            yield $book;
        }
    }
}

$inRepair = onlyInRepair(readCsv(__DIR__ . '/donations.csv'));
writeCsv(__DIR__ . '/in_repair.csv', $inRepair);
```

For this to work, `writeCsv` starts accepting `iterable` instead of `array`
— the type that accepts an array **and** a generator. The whole path, from
reading to writing, still has one book at a time in memory: neither of the
two generators keeps the list.

The header is missing from the written file: it has to be the first row
passed to `writeCsv`, and it is left as an exercise within the exercise.
:::

:::exercise level=3
The nightly donations import runs at 2 a.m., through the scheduler, and
saves the chosen ones in the database. On the first night, it imported zero
books and raised no error at all. List the three most likely causes, in the
order you would investigate them, and what you would add to the script so
that the next failure is not silent.

:::answer
In order:

1. **Relative path.** The scheduler calls from the root, `fopen` fails with
   a *warning* and returns `false` — and, if the script does not check the
   `false`, the loop does not run even once.
2. **BOM in the header.** `$book['title']` does not exist; if the script
   skips rows without a title, it skips all of them.
3. **Encoding.** Titles with broken accents fail a validation and are
   silently discarded.

What I would add:

- check the `false` from `fopen` and throw an exception — chapter
  @cap:excecoes;
- count rows read, imported and discarded, and log all three at the end;
- exit with an error if rows read is greater than zero and imported is zero.

The import that "raised no error" had three: the system just had no way of
counting any of them. Chapter @cap:erros-e-debug is about making PHP count.
:::
