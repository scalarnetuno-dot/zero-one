---
source_hash: 2a294adbbba8
title: "From file to database"
number: 12
slug: do-arquivo-ao-banco
part: p2
kicker: "Two clerks, one file, one loan. There should have been two."
goal: >-
  Save data that survives the end of the program, reproduce on your machine
  the bug a file cannot prevent, understand what a database does
  differently, and install one.
---

Everything the program has stored so far — the catalog, the loans, the
fines — disappears when the program ends. Each run starts from zero, and the
only place where Casa Amarela's catalog really exists is inside the 2009
System and in Vera's drawer.

This is the chapter in which the data starts living somewhere.

## The catalog that vanishes

```php title="volatile.php" numbered
<?php

$catalog = [
    ['accession' => 812, 'title' => 'O Cortiço'],
    ['accession' => 907, 'title' => 'Vidas Secas'],
];

echo count($catalog), " copies\n";
```

```text
$ php volatile.php
2 copies
$ php volatile.php
2 copies
```

Always two. If the program registers a third one, it exists during the run
and disappears at the final semicolon. The process's memory is handed back
to the operating system, and everything goes with it.

:::term Persistence
The property of data continuing to exist after the program that created it
has ended. Data in memory is volatile; data written to disk is persistent.
Everything this chapter does is cross that border.
:::

## Writing to a file

PHP reads and writes files with two functions with descriptive names:

```php title="save.php" numbered
<?php

$catalog = [
    ['accession' => 812, 'title' => 'O Cortiço'],
    ['accession' => 907, 'title' => 'Vidas Secas'],
];

$json = json_encode(
    $catalog,
    JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE
);

file_put_contents('catalog.json', $json);

echo "saved\n";
```

```text
$ php save.php
saved
$ cat catalog.json
[
    {
        "accession": 812,
        "title": "O Cortiço"
    },
    {
        "accession": 907,
        "title": "Vidas Secas"
    }
]
```

`json_encode` turns the array into text in JSON format, which chapter
@cap:arrays introduced. `file_put_contents` writes that text to a file,
creating it if it does not exist and **replacing the contents** if it does.

The two constants after the comma change the output format.
`JSON_PRETTY_PRINT` breaks lines and indents, which makes the file readable
by people. `JSON_UNESCAPED_UNICODE` keeps accents as accents — without it,
`O Cortiço` would become `O Cortiço`, which is valid and unreadable.
The `|` between the two combines the options.

Reading it back is the reverse path:

```php title="load.php" numbered
<?php

$json = file_get_contents('catalog.json');
$catalog = json_decode($json, true);

echo count($catalog), " copies\n";
echo $catalog[0]['title'], "\n";
```

```text
$ php load.php
2 copies
O Cortiço
```

The `true` in `json_decode`'s second argument is important and easy to
forget: without it, the JSON becomes an object instead of an array, and all
the `$catalog[0]['title']`s in your program stop working.

:::pitfall
`file_get_contents` returns `false` when the file does not exist, and also
emits a warning. Since `false` is falsy and so is an empty array, code that
does `if (!$data)` treats "file does not exist" and "empty catalog" as the
same thing — the bug in Vera's report all over again.

The honest way checks first:

```php
if (!file_exists('catalog.json')) {
    $catalog = [];
} else {
    $catalog = json_decode(file_get_contents('catalog.json'), true);
}
```
:::

Now the catalog survives. Register a copy, run it again, it is there. For a
program used by one person at a time, that settles it.

Casa Amarela has two computers.

## 10:12

:::story The copy that went out once
Casa Amarela serves people in two places at the same time. There is the
front desk by the entrance, where Vera sits, and there is the computer in
the back room, where Neide registers new readers and, when the queue gets
long, also lends books.

On a Tuesday morning, at 10:12, both of them lent a book.

Vera lent copy 812 to Mrs. Marlene. Neide lent 344 to a young man who was in
a hurry.

At 10:30 the file had one loan.

"Marlene's is gone," said Vera.

"Or mine is gone," said Neide.

Marlene's was gone. You could tell because the young man's was there, not
because anyone had a record of anything.

Vera sorted it out on the spot, the way she has since 1995: she took a paper
card, wrote 812, wrote Marlene, wrote the date, and put it in the drawer.

"Until the computer makes up its mind, the drawer decides."
:::

This bug is not about careless programming. It is a direct consequence of
how you write to a file, and you can reproduce it on your machine in two
minutes.

```php title="lend.php" numbered
<?php

$file = 'loans.json';

$loans = file_exists($file)
    ? json_decode(file_get_contents($file), true)
    : [];

echo "read the file: ", count($loans), " loans\n";

sleep(5);

$loans[] = [
    'copy' => (int) $argv[1],
    'reader' => $argv[2],
];

file_put_contents($file, json_encode($loans));

echo "saved: ", count($loans), " loans\n";
```

Two new things. `$argv` is an array with whatever came on the command line:
`$argv[0]` is the file name, `$argv[1]` is the first argument. And
`sleep(5)` makes the program wait five seconds — here it only serves to
make visible a window of time that, in real life, lasts milliseconds.

Open **two terminals** and run one in each, less than five seconds apart:

```text
Terminal 1                          Terminal 2
$ php lend.php 812 Marlene
read the file: 0 loans
                                    $ php lend.php 344 Guy
                                    read the file: 0 loans
saved: 1 loans
                                    saved: 1 loans
```

Both saved. Both said it worked. And the file:

```text
$ cat loans.json
[{"copy":344,"reader":"Guy"}]
```

One loan.

:::art caption="Two loans in the same minute; the file kept one."
src="dois-emprestimos-no-mesmo-minuto-o-arquivo-guardou-um.png"
Minimalist editorial cartoon on a white background, composition split down
the middle. On the left, an older librarian at the front desk; on the right,
a clerk at the computer in a back room. From both screens, at the same time,
a sheet of paper flies towards a single file folder in the center, too
small, with room for only one sheet: the other one hits the edge and falls
to the floor. In the foreground, the counter's wooden drawer half open, with
a handwritten paper card: "812 — Marlene". Few elements, dry humor,
tech-magazine aesthetic.
:::

## Why it vanishes

Each run did three things, in this order: it **read** the whole file,
**changed** the array in memory, **wrote** the whole file over the top.

The problem is in the interval between reading and writing. In that
interval, the second program read the same old contents. When it wrote, it
wrote over what the first had just saved — without knowing there was
anything there to write over.

:::term Race condition
When the result of an operation depends on which of two processes gets
there first, and nothing guarantees the order. That is where the name comes
from: two participants, one finish line, and a different result on each
run. It is the hardest category of bug to reproduce, because it disappears
when you stop to watch.
:::

Neither of the two programs is wrong. Both do exactly what anyone would
write. What is missing is not in the code: what is missing is someone to
**coordinate** the two.

:::pitfall
There is a partial way out in PHP itself: `flock()`, which asks the
operating system to lock the file while a process works on it. It works, and
it solves this specific case.

What it does not solve: while one process holds the lock, all the others
wait — for the whole file, not for the line they care about. With two
clerks, it is imperceptible. With twenty, the library grinds to a halt. And
if the file is on a network folder, the lock may simply not work, silently.

`flock` is worth knowing to fix a small script today. It is not worth
building a system on top of it.
:::

## What a database does differently

The race is the first item on a list, and it is the whole list that
justifies switching tools.

| Question | File | Database |
|---|---|---|
| Two writing at the same time | one overwrites the other | both write, in order |
| "I only want the 20 overdue ones" | loads all 8,412 and filters | brings back 20 |
| "Does this accession already exist?" | scans everything, every time | answers by index |
| "Can this reader be deleted?" | nobody checks | the database refuses |
| "Save both things or neither" | doesn't exist | transaction |
| Access from another machine | shared folder and faith | that's what it's for |

Table: Each row is a problem someone has already had. The database is not
more sophisticated for sport — it is the sum of forty years of people
solving these six rows.

:::term DBMS
*Database Management System*: a program that keeps running all the time,
stores data on disk and serves requests from other programs. It is the one
that coordinates who writes, who reads and in what order — the coordinator
the two terminals in the previous section were missing.

MySQL, PostgreSQL, SQLite and SQL Server are DBMSs. This book uses MySQL,
because it is what Casa Amarela has had running since 2009.
:::

The important point is that the database is **another program**. It is not
a library your PHP loads: it is a separate process, which may be on another
machine, and which your program talks to. That is why it can coordinate two
PHPs — it is outside both of them.

## Install and log in

| System | How to install |
|---|---|
| Ubuntu / Debian | `sudo apt install mysql-server` |
| macOS | `brew install mysql` and `brew services start mysql` |
| Windows | official installer at `dev.mysql.com/downloads`, or WSL2 |
| Any of them, with Docker | `docker run -d -p 3306:3306 -e MYSQL_ROOT_PASSWORD=secret mysql:8` |

Table: The Docker line starts an isolated MySQL that disappears when you
tell it to, without installing anything on the machine. If you already use
Docker, it is the cleanest path.

Once installed, there is a client program that talks to it from the
terminal:

```text
$ mysql -u root -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.

mysql>
```

`-u root` says which user to log in as; `-p` asks for the password. The
`mysql>` at the end is the **database prompt**: from here on, what you type
is not a terminal command, it is a database command.

:::warning
On a fresh install, the `root` user usually has an empty password or uses
your system user's password. That is convenient and it is for development
only. A MySQL with a passwordless root exposed on the network is found by
automated scanning within hours.

On your machine, with no external exposure, that is fine. On Casa Amarela's
server, it is not.
:::

First command:

```text
mysql> SHOW DATABASES;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
4 rows in set (0.01 sec)
```

`SHOW DATABASES` lists the databases that exist on this server. The four
that showed up belong to MySQL itself — it uses databases to store
information about databases, which is circular and works.

Notice the semicolon. In the MySQL client, it is **required**: it is what
says "I'm done writing, you can run it". Forgetting the `;` is the number
one beginner's mistake, and the symptom is the prompt changing to `->` and
waiting for you to finish the sentence.

Now Casa Amarela's database:

```text
mysql> CREATE DATABASE casa_amarela
    -> CHARACTER SET utf8mb4
    -> COLLATE utf8mb4_unicode_ci;
Query OK, 1 row affected (0.02 sec)

mysql> USE casa_amarela;
Database changed

mysql> SHOW TABLES;
Empty set (0.00 sec)
```

Three commands and a lesson in each.

`CREATE DATABASE` creates the database. Notice the `->` on lines 2 and 3:
it is the continuation prompt, because the command only ended at the `;` on
the third line.

`CHARACTER SET utf8mb4` says in what encoding the database will store text.
That choice is the same one from chapter @cap:strings, now from the other
side: without it, you may end up with a `latin1` database and the second
José de Alencar being born all on its own.

:::trivia
The name `utf8mb4` exists because MySQL spent ten years calling `utf8` an
encoding that was **not** full UTF-8: it supported at most three bytes per
character, which covers accents and does not cover emoji or some
ideograms. When they fixed it, there were already too many databases in the
world using the wrong name for it to be corrected.

The way out was to create `utf8mb4` — "UTF-8, for real, up to four bytes" —
and leave the old `utf8` as a synonym for the wrong one. Today `utf8` is an
alias for `utf8mb4` in newer versions, but writing `utf8mb4` explicitly is
still the right thing.
:::

`USE casa_amarela` chooses which database the next commands will work on.
Without it, MySQL does not know which database you are talking about.

`SHOW TABLES` lists the tables. It is empty, because none exists yet.

## Table, row, column

The vocabulary is missing, and it is already in Vera's drawer.

The drawer has a stack of cards of the same kind: all with the same printed
fields — accession, title, author, condition — each filled in with different
values.

| In the drawer | In the database |
|---|---|
| the stack of copy cards | a **table** called `copies` |
| one card | a **row** (or record) |
| the "accession" field printed on the card | a **column** called `accession` |
| what is written in the field | the **value** of that row in that column |
| the whole drawer | the **database** `casa_amarela` |

Table: The metaphor is not approximate: the relational model was designed
in 1970 by Edgar Codd with exactly this in mind.

Two differences between the card and the table, and both are advantages of
paper that the database gives up on purpose.

On the card, Vera can write anything in any field — including "don't know"
in the date field. In a table, each column has a declared **type**, and the
database rejects whatever does not fit.

And in the drawer, if two cards have the same accession number, nobody
notices. In a table, you can ask the database to prevent it.

:::key
That is the trade this whole chapter proposes: you give up the freedom to
write anything anywhere, and you get a program that rejects invalid data at
the door, instead of discovering it two years later in a report that does
not add up.

The name for this is **schema** — the description of which tables exist,
which columns each has and what fits in each column.
:::

:::note In your career
"Why not store it in a file?" is a legitimate question, and the honest
answer is: sometimes, do.

Configuration, logs, cached results, spreadsheet imports, a file one person
edits at a time — all of that lives well in a file, and putting a database
in the middle is extra work for no gain.

The question that separates the two cases has three parts: **do two people
write at the same time? do you need to search without loading everything?
does some rule need to be guaranteed even when the program has a bug?** A
"yes" to any of them already calls for a database.

Being able to justify the choice in those terms — and not in "a database is
more professional" — is what separates an architecture decision from a
habit.
:::

:::summary
- Data in memory is volatile; it only exists while the program runs.
- `json_encode` + `file_put_contents` writes; `file_get_contents` +
	`json_decode` with `true` reads it back as an array.
- Reading, changing and writing the whole file produces a race: whoever
	writes last erases the other's work, with no error at all.
- `flock` solves the small case and does not solve the list.
- A DBMS is another program, which coordinates the writers because it is
	outside all of them.
- A table is the stack of cards, a row is the card, a column is the printed
	field.
- A schema is the description of what fits where — the freedom you trade
	for guarantees.
:::

:::checkpoint
You write and read data in a file, can reproduce the race in two terminals
and explain why it happens, have a MySQL running, and have created the
`casa_amarela` database with the right encoding.
:::

:::exercise level=1
Write two programs: one that adds a copy to `catalog.json` and another that
lists what is stored. Run the first one three times and check with the
second.

:::answer
```php title="register.php"
<?php

$file = 'catalog.json';

$catalog = file_exists($file)
    ? json_decode(file_get_contents($file), true)
    : [];

$catalog[] = [
    'accession' => (int) $argv[1],
    'title' => $argv[2],
];

file_put_contents(
    $file,
    json_encode($catalog, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)
);

echo "catalog with ", count($catalog), " copies\n";
```

```php title="list.php"
<?php

$catalog = json_decode(file_get_contents('catalog.json'), true);

foreach ($catalog as $c) {
    echo $c['accession'], ' - ', $c['title'], "\n";
}
```

```text
$ php register.php 812 "O Cortiço"
catalog with 1 copies
$ php register.php 907 "Vidas Secas"
catalog with 2 copies
$ php list.php
812 - O Cortiço
907 - Vidas Secas
```

Notice the quotes around `"O Cortiço"` on the command line: without them,
the terminal would split the title into two arguments at the space, and
`$argv[2]` would be just `O`.
:::

:::exercise level=2
Reproduce the race from the "10:12" section on your machine, with the two
terminals. Then use `flock` to prevent it, and explain what you started
paying in exchange.

:::answer
```php title="lend_with_lock.php"
<?php

$file = 'loans.json';

$f = fopen($file, 'c+');
flock($f, LOCK_EX);

$contents = stream_get_contents($f);
$loans = $contents === '' ? [] : json_decode($contents, true);

echo "read: ", count($loans), " loans\n";
sleep(5);

$loans[] = ['copy' => (int) $argv[1], 'reader' => $argv[2]];

ftruncate($f, 0);
rewind($f);
fwrite($f, json_encode($loans));

flock($f, LOCK_UN);
fclose($f);

echo "saved: ", count($loans), " loans\n";
```

```text
Terminal 1                          Terminal 2
$ php lend_with_lock.php 812 Marlene
read: 0 loans
                                    $ php ... 344 Guy
                                    (stopped, waiting)
saved: 1 loans
                                    read: 1 loans
                                    saved: 2 loans
```

Two loans. The bug is gone.

`fopen` with `'c+'` opens for reading and writing without erasing the
contents. `flock($f, LOCK_EX)` asks for the exclusive lock and **waits** if
another process already has it. `ftruncate` and `rewind` empty the file
before rewriting it, because the lock is not about the contents.

**What you started paying:** Terminal 2 sat still for five seconds, doing
nothing, waiting for a file. With two clerks that is invisible. With twenty,
each one waits for the sum of all the previous ones — and every operation,
even that of someone who only wanted to look something up, joins the same
queue.

On top of that, the program went from seven lines to fifteen, and three of
them (`ftruncate`, `rewind`, the releasing `flock`) are the ones someone will
forget in the next change.
:::

:::exercise level=3
Casa Amarela wants to know how many loans of children's books there were in
February. The data is in a `loans.json` with 8,412 records and a
`books.json` with 4,000.

Write the program that answers this by reading the files. Then list what
this solution cannot do, and what each item on your list would require.

:::answer
```php
<?php

$json = file_get_contents('loans.json');
$loans = json_decode($json, true);

$books = json_decode(file_get_contents('books.json'), true);

$book_by_id = array_column($books, null, 'id');

$total = 0;

foreach ($loans as $l) {
    if (!str_starts_with($l['borrowed_at'], '2027-02')) {
        continue;
    }

    $book = $book_by_id[$l['book_id']] ?? null;

    if ($book !== null && $book['subject'] === 'children') {
        $total++;
    }
}

echo $total, "\n";
```

It works, and it is the indexing from chapter @cap:repeticoes applied to
persisted data. Four things it cannot do:

**It cannot answer without loading everything.** To count one month's
loans, both files were read in full from disk and turned into an array in
memory — 12,412 records to arrive at one number. A database reads only what
the filter reaches, and with an index not even that.

**It cannot run while someone is writing.** If a loan is recorded in the
middle of the read, the program may read half a JSON and `json_decode`
returns `null`. That calls for the coordination from the previous section.

**It cannot guarantee that `book_id` points to a book that exists.** The
`?? null` is there precisely because it might not. A database refuses to
save a loan with a nonexistent book — that is the foreign key.

**It cannot answer the next question without a new program.** "And in
March?" requires editing the code. "And by subject?" requires another
program. In SQL, the three questions are three different lines, written on
the spot, without editing anything.

The fourth is the most underrated of the four. The real cost of the file is
not performance: it is that **every new question becomes a programming
task**, and Vera is not going to open a ticket to find out something she
wanted to know right now.
:::
