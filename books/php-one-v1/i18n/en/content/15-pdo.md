---
source_hash: 5a5e168d5042
title: "PDO: PHP talking to the database"
number: 15
slug: pdo
part: p2
kicker: "The intern typed five characters into the search box and the screen returned the entire catalog."
goal: >-
  Connect PHP to MySQL, read and write with prepared statements, understand
  in practice why concatenation is a security bug, and handle a connection
  failure without giving away the password.
---

The database exists, the tables exist, the queries work in the terminal.
What is missing is the part where PHP asks the questions.

## Connecting

```php title="connection.php" numbered
<?php

$dsn = 'mysql:host=127.0.0.1;port=3306'
     . ';dbname=casa_amarela;charset=utf8mb4';

$pdo = new PDO($dsn, 'root', 'secret', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,
]);

echo "connected\n";
```

```text
$ php connection.php
connected
```

`PDO` is PHP's standard interface for databases. The same code works with
MySQL, PostgreSQL and SQLite by changing only the first line — which does
not mean the SQL is the same, and that is why this book taught SQL first.

:::term DSN
*Data Source Name*: the text that describes where the database is. It
starts with the driver's name (`mysql:`), followed by `key=value` pairs
separated by semicolons.

The `charset=utf8mb4` is not optional. Without it, the connection may
negotiate an encoding different from the database's, and the accent that
was right in MySQL arrives wrong in PHP — the second José de Alencar from
chapter @cap:strings, being born on the other end of the cable.
:::

The three options in the array deserve a sentence each, because all three
change behavior in an important way.

**`ERRMODE_EXCEPTION`** makes PDO throw an exception when something goes
wrong. The historical default was to stay quiet and return `false`, which
produces the program that carries on with a database error nobody saw.
Always turn it on.

**`FETCH_ASSOC`** makes each row come back as an array with named keys —
`['title' => 'O Cortiço']`. Without it, the default brings **every value
twice**, once by name and once by position, which doubles the size of the
result and confuses every `foreach`.

**`EMULATE_PREPARES => false`** makes PDO send the prepared statement to
the actual server, instead of assembling it in PHP and sending finished
text. The difference shows up three sections from now, and it is about
security.

## Asking

```php title="list.php" numbered
<?php

require 'connection.php';

$sql = 'SELECT id, title, year FROM books ORDER BY title';

foreach ($pdo->query($sql) as $book) {
    echo $book['id'], ' - ', $book['title'], "\n";
}
```

```text
$ php list.php
3 - Grande Sertão
1 - O Cortiço
4 - O Pequeno Príncipe
2 - Vidas Secas
```

`query()` runs a query and returns something you can walk through with
`foreach`, one row at a time. Each row is an array with the columns the
`SELECT` asked for.

Notice that `query()` is for queries **with no outside value**. The instant
there is a value coming from the user, it stops being suitable — and that
is what the rest of the chapter is about.

## Five characters

:::story Five characters
On Thursday, in staging, Tainá was testing the old System's search screen,
to document what needed to be redone.

She typed "sertao". Two books came up.

She typed "xxxxx". Nothing came up.

She typed `' OR '1'='1`.

Four thousand came up.

She called Cléber, who looked at the screen for a while and said the
sentence that sums up the problem:

"But you can't type that."

"The field let me."

"But you can't."

"Cléber, the field let me."

He asked her not to do it again. Tainá asked whether she could do it in
production, to show Dr. Aurélio.

The answer took a while.

"No. But put it in an e-mail to me."
:::

The System's `login.php` has already made an appearance. The search is the
same problem with a different consequence:

```php title="system_search.php" numbered
<?php

require 'connection.php';

$term = $_GET['q'] ?? '';

$sql = "SELECT id, title FROM books
        WHERE title LIKE '%{$term}%'";

foreach ($pdo->query($sql) as $book) {
    echo $book['title'], "\n";
}
```

With `$term = 'sertao'`, the query that reaches the database is:

```sql
SELECT id, title FROM books WHERE title LIKE '%sertao%'
```

With `$term = "' OR '1'='1"`, the query that reaches the database is:

```sql
SELECT id, title FROM books WHERE title LIKE '%' OR '1'='1%'
```

Read it calmly. The single quote Tainá typed **closed** the quote the
program had opened. From that point on, what she typed stopped being a value
being searched for and became part of the command. `OR '1'='1'` is a
condition that is always true, and the `WHERE` started accepting every row.

:::term SQL injection
When data coming from outside is interpreted as part of the command instead
of as a value. The name describes the mechanism: the attacker **injects**
instructions into a sentence that should have been just text.

It is not a MySQL flaw or a PHP flaw. It is a consequence of building
commands by gluing text together — and it happens the same way in any
language and any database.
:::

Four thousand titles leaking is the friendly case. The same door accepts
`'; DROP TABLE loans; --`, accepts reading the users table, and accepts a
condition that returns someone's password character by character. The limit
is not what the search box does: it is what the database user is allowed to
do.

:::warning
Do not test this on a system that is not yours, nor in production — not to
prove a point, not with good intentions. Running the query above against a
third party's system is unauthorized access, and the fact that the field
let you does not change that.

The right place is the `casa_amarela` database you created on your machine.
Run it there, watch it happen, and then fix it.
:::

## The value is never a command

```php title="safe_search.php" numbered
<?php

require 'connection.php';

$term = $_GET['q'] ?? '';

$sql = 'SELECT id, title FROM books WHERE title LIKE ?';

$query = $pdo->prepare($sql);
$query->execute(['%' . $term . '%']);

foreach ($query as $book) {
    echo $book['title'], "\n";
}
```

The `?` is a **placeholder**. The query goes to the server **without** the
value, is parsed and turned into an execution plan, and only then is the
value sent — separately, already as a value.

With `$term = "' OR '1'='1"`, the database looks for books whose title
literally contains the text `' OR '1'='1`. It finds none. The quote closes
nothing because, by the time it arrives, there is no command left to close:
it has already been parsed.

:::key
This is the central idea, and it holds for the rest of your career:
**a prepared statement does not escape the value — it separates the value
from the command.**

There are escaping functions, and they work, and they are not the way.
Escaping depends on you remembering to do it everywhere, with the right
function for the right database, with the right encoding. Separating
depends on you using `prepare` — and the day you forget, the mistake is
visible in the code, not invisible in the result.
:::

Notice the detail of the `%`: it is in the **value**, in
`'%' . $term . '%'`, not in the query. It is part of what is being searched
for, not of the command.

Placeholders can also have names, which pays off from the third one on:

```php title="named.php" numbered
<?php

require 'connection.php';

$sql = 'SELECT title, year FROM books
        WHERE subject = :subject
          AND year >= :since
        ORDER BY year';

$query = $pdo->prepare($sql);
$query->execute([
    'subject' => 'literature',
    'since' => 1900,
]);

foreach ($query as $book) {
    echo $book['year'], ' ', $book['title'], "\n";
}
```

```text
1938 Vidas Secas
1956 Grande Sertão
```

With `?`, the order of the array has to match the order of the
placeholders. With `:name`, it does not — and the call reads well without
looking at the query.

:::pitfall
There is one place where placeholders do **not** work: table and column
names.

```php
// does not work
$query = $pdo->prepare('SELECT * FROM books ORDER BY ?');
$query->execute([$_GET['order']]);
```

The database needs to know which column to sort by **to build the plan**,
and the plan is built before the value arrives. What the code above does is
sort by a text constant, which sorts nothing.

Since the sort order often comes from outside — the user clicks the table
header — the way out is an **allow list**:

```php
$columns = ['title', 'year', 'author'];
$order = $_GET['order'] ?? 'title';

if (!in_array($order, $columns, true)) {
    $order = 'title';
}

$sql = "SELECT * FROM books ORDER BY {$order}";
```

It is the only case in this book in which an external value enters the
query by concatenation — and it is only safe because the value was
**replaced** by an item from a fixed list, not validated. The difference
matters: validating accepts whatever passed the test; replacing only lets
through what you wrote.
:::

## The shape of what comes back

Three ways of receiving the result, for three different questions:

```php title="shapes.php" numbered
<?php

require 'connection.php';

$q = $pdo->prepare('SELECT id, title FROM books WHERE id = ?');
$q->execute([1]);
$book = $q->fetch();

print_r($book);

$q = $pdo->prepare('SELECT id, title FROM books WHERE year > ?');
$q->execute([1900]);
$books = $q->fetchAll();

echo count($books), " books\n";

$q = $pdo->prepare('SELECT COUNT(*) FROM books WHERE subject = ?');
$q->execute(['literature']);
$total = $q->fetchColumn();

echo $total, "\n";
```

```text
Array
(
    [id] => 1
    [title] => O Cortiço
)
3 books
3
```

`fetch()` brings **one** row and moves forward; it returns `false` when it
is done. `fetchAll()` brings all of them at once, in an array of arrays.
`fetchColumn()` brings a single value — made for `COUNT`, `SUM`, `MAX` and
for when you want one field from one row.

:::pitfall
`fetchAll()` loads the whole result into PHP's memory. For a query that
returns twenty rows, that is what you want. For one that returns eight
hundred thousand, it is `Allowed memory size exhausted` showing up with its
full name.

When the result is large, walk through it with `foreach` directly on the
query object, which brings one row at a time. And when the result is large
because the query has no filter, memory was not the problem.
:::

And `fetch()` returning `false` deserves care:

```php
$book = $q->fetch();

if ($book === false) {
    echo "book not found\n";
}
```

The `=== false` is required. An `if (!$book)` would treat any falsy result
as "not found". A database row is never falsy, so here it would work — and
the habit is the same one that made four readers with no fine show up on
Vera's outstanding report.

## Writing

```php title="register.php" numbered
<?php

require 'connection.php';

$sql = 'INSERT INTO books (title, author, subject, year)
        VALUES (:title, :author, :subject, :year)';

$query = $pdo->prepare($sql);
$query->execute([
    'title' => 'Memórias Póstumas de Brás Cubas',
    'author' => 'Machado de Assis',
    'subject' => 'literature',
    'year' => 1881,
]);

$id = (int) $pdo->lastInsertId();

echo "book ", $id, " registered\n";
```

```text
book 5 registered
```

`lastInsertId()` returns the value `AUTO_INCREMENT` assigned. It comes back
as text, hence the `(int)` — the same reason as the `DECIMAL` column: PHP
receives from the database whatever fits safely in text.

For `UPDATE` and `DELETE`, what matters is how many rows were affected:

```php title="return.php" numbered
<?php

require 'connection.php';

$sql = 'UPDATE loans
        SET returned_at = NOW()
        WHERE id = ? AND returned_at IS NULL';

$query = $pdo->prepare($sql);
$query->execute([3315]);

if ($query->rowCount() === 0) {
    echo "loan doesn't exist or was already returned\n";
} else {
    echo "return recorded\n";
}
```

`rowCount()` returns the number of rows changed. Zero is not an error — it
is information, and here it is the information that separates "doesn't
exist" from "was already returned". Without this check, the program would
say "return recorded" for a loan that does not exist.

And the transaction from the previous chapter, in PHP:

```php title="lend.php" numbered
<?php

require 'connection.php';

$pdo->beginTransaction();

try {
    $q = $pdo->prepare(
        'INSERT INTO loans
           (copy_id, reader_id, borrowed_at, due_on)
         VALUES (?, ?, NOW(), ?)'
    );
    $q->execute([1, 1, '2027-02-18']);

    $q = $pdo->prepare(
        'UPDATE copies SET status = ? WHERE id = ?'
    );
    $q->execute(['on_loan', 1]);

    $pdo->commit();
    echo "loan recorded\n";
} catch (PDOException $e) {
    $pdo->rollBack();
    throw $e;
}
```

The `try` runs the block; if anything in there throws an error, the `catch`
receives the error object and runs `rollBack()`, undoing both writes. The
`throw $e` at the end passes the problem on instead of hiding it — undoing
the transaction and pretending nothing happened would be worse than the
original bug.

This `try`/`catch` structure is the subject of a stretch of the book further
ahead; for now it appears because a transaction without it is a transaction
that protects nothing.

## When the connection fails

```php title="bad_connection.php" numbered
<?php

$dsn = 'mysql:host=127.0.0.1;dbname=casa_amarela;charset=utf8mb4';

$pdo = new PDO($dsn, 'root', 'wrong_password');
```

```text
PHP Fatal error: Uncaught PDOException: SQLSTATE[HY000] [1045]
Access denied for user 'root'@'localhost' (using password: YES)
in /app/bad_connection.php:5
Stack trace:
#0 /app/bad_connection.php(5): PDO->__construct('mysql:host=127....',
'root', 'wrong_password')
```

Read the last line of the trace. **The password is right there.**

PDO receives the password as a constructor argument, and PHP's stack trace
shows functions' arguments. If this message ends up on a screen with errors
turned on, the database password has been published.

:::warning
Two rules, and the second is the one that saves you.

**First:** `display_errors` off in production, as chapter
@cap:primeiro-programa established. That stops the message from reaching the
browser.

**Second:** wrap the connection and swap the exception for one of your own:

```php
try {
    $pdo = new PDO($dsn, $user, $password, $options);
} catch (PDOException $e) {
    throw new RuntimeException(
        'Failed to connect to the database',
        0
    );
}
```

The new exception does not carry the constructor's arguments. The real
reason is still available in PHP's log, which is where the team looks, and
it disappears from the trace any other part of the system might display.

And the reason the second rule exists even with the first: `display_errors`
is a server setting, and server settings change when someone migrates
hosting on a Friday.
:::

## The catalog, read by PHP

Putting it all together, Casa Amarela's search:

```php title="search.php" numbered
<?php

require 'connection.php';

function searchBooks(
    PDO $pdo,
    string $term,
    int $limit = 20,
): array {
    $sql = 'SELECT b.id, b.title, b.author,
                   COUNT(c.id) AS copies
            FROM books b
            LEFT JOIN copies c ON c.book_id = b.id
            WHERE b.title LIKE :term OR b.author LIKE :term
            GROUP BY b.id, b.title, b.author
            ORDER BY b.title
            LIMIT :limit';

    $query = $pdo->prepare($sql);
    $query->bindValue('term', '%' . $term . '%');
    $query->bindValue('limit', $limit, PDO::PARAM_INT);
    $query->execute();

    return $query->fetchAll();
}

foreach (searchBooks($pdo, 'assis') as $book) {
    printf("%-35s %s (%d)\n",
        $book['title'], $book['author'], $book['copies']);
}
```

```text
Memórias Póstumas de Brás Cubas     Machado de Assis (0)
```

Three new things in this version.

The same placeholder `:term` appears **twice** in the query and is given
only once. That only works with named placeholders; with `?`, it would be
two placeholders and two values.

`bindValue()` gives one value at a time, instead of passing the whole array
to `execute()`. It is here because of the third novelty.

`PDO::PARAM_INT` on `limit` is required and is one of PDO's most irritating
traps. With `EMULATE_PREPARES => false`, every value is sent as text by
default — and `LIMIT '20'`, with quotes, is a syntax error in MySQL.
`PARAM_INT` tells the driver to send it as a number.

:::pitfall
The symptom of this trap is misleading: the query works perfectly while you
test with `execute([...])` and `EMULATE_PREPARES` on, and breaks when
someone turns emulation off for security.

The message is `You have an error in your SQL syntax near ''20''` — with two
quotes, which is the clue. Whenever a syntax error points to a value inside
double quotes, the problem is a number being sent as text.
:::

:::note In your career
When you find an SQL injection in a system, the hardest part is not the fix:
it is the conversation.

Three things that work, learned in practice. **Record it in writing, with
date and time.** **Describe the impact in business language** — "you can
read the complete records of twelve hundred residents" communicates; "there
is a string concatenation in the `WHERE`" does not. And **bring the fix
along with the problem**, because a flaw reported without a solution
becomes a task for someone else and goes into the queue.

And one that does not work: demonstrating it in production. Tainá asked
first, and that is the part of the story worth copying. After the
demonstration, the conversation stops being about the flaw and becomes
about your access.
:::

:::summary
- `PDO` connects with a DSN; the `charset=utf8mb4` is not optional.
- Turn on `ERRMODE_EXCEPTION`, `FETCH_ASSOC` and
	`EMULATE_PREPARES => false`.
- Concatenating an external value into SQL lets it become a command.
- A prepared statement does not escape the value: it separates the value
	from the command.
- Table and column names do not accept placeholders — only an allow list.
- `fetch` brings one row, `fetchAll` brings all, `fetchColumn` brings one
	value; `rowCount` says how many were changed.
- `lastInsertId` returns the generated identifier, as text.
- `beginTransaction` + `try`/`catch` + `rollBack` turn two writes into one.
- A connection failure's trace contains the password: swap the exception.
:::

:::milestone
End of Part 2. Casa Amarela's catalog lives in a database, with rules the
database guarantees, and PHP reads and writes without opening a hole. From
here on the project has real data — and a single file can no longer cope.
:::

:::checkpoint
You connect to MySQL from PHP, write prepared statements with positional
and named placeholders, can recognize and fix a dangerous concatenation, and
handle a connection failure without leaking credentials.
:::

:::exercise level=1
Write a program that receives a subject on the command line and lists the
books on that subject, with title and year, sorted by year. Use a prepared
statement.

:::answer
```php
<?php

require 'connection.php';

$subject = $argv[1] ?? 'literature';

$sql = 'SELECT title, year FROM books
        WHERE subject = ?
        ORDER BY year';

$query = $pdo->prepare($sql);
$query->execute([$subject]);

foreach ($query as $book) {
    echo $book['year'] ?? '????', ' ', $book['title'], "\n";
}
```

```text
$ php by_subject.php literature
1881 Memórias Póstumas de Brás Cubas
1890 O Cortiço
1938 Vidas Secas
1956 Grande Sertão
```

The `?? '????'` covers the `year` column, which accepts null. Without it, a
book with no year would print nothing and the line would be crooked — and
PHP would still emit a warning when concatenating null.
:::

:::exercise level=2
The snippet below has two flaws: one about security and one about behavior.
Find both and rewrite it.

```php
$id = $_GET['id'];

$sql = "SELECT * FROM readers WHERE id = $id";
$reader = $pdo->query($sql)->fetch();

echo "Welcome, " . $reader['name'];
```

:::answer
**Security flaw:** `$id` comes from the URL and is glued into the command.
With `?id=1 OR 1=1`, the query returns the first reader in the table,
whoever they are. With `?id=1 UNION SELECT ...`, it returns whatever the
attacker wants.

**Behavior flaw:** `fetch()` returns `false` when it finds nobody, and the
next line reads `$reader['name']` from a `false`. The result is a warning
and the sentence "Welcome, " without a name — and, with errors off in
production, just the truncated sentence.

```php
<?php

require 'connection.php';

$id = (int) ($_GET['id'] ?? 0);

$query = $pdo->prepare(
    'SELECT id, name FROM readers WHERE id = ?'
);
$query->execute([$id]);

$reader = $query->fetch();

if ($reader === false) {
    http_response_code(404);
    echo "Reader not found";
    return;
}

echo "Welcome, ", htmlspecialchars($reader['name']);
```

Four changes, and two of them were not in the question.

The `(int)` at the edge converts the value before any use. On its own it
would already close the injection in this case — and it is not enough as a
strategy, because the next field will be text.

The `SELECT *` became `SELECT id, name`: there is no reason to fetch the
document and registration date to write a greeting.

And the `htmlspecialchars` on output escapes the name before putting it on a
page. Without it, a reader registered with `<script>` in their name runs
code in the browser of whoever opens the screen. It is the same idea as the
prepared statement, at the other border: **data does not become a
command**.
:::

:::exercise level=3
Implement the function
`lend(PDO $pdo, int $copyId, int $readerId): int`, which records a loan and
returns the created identifier. It has to refuse the loan if the copy is
already on loan, and it cannot leave an inconsistent state if something
fails in the middle.

Then explain why checking availability with a `SELECT` before the `INSERT`
is not enough.

:::answer
```php
<?php

function lend(PDO $pdo, int $copyId, int $readerId): int
{
    $dueOn = date('Y-m-d', strtotime('+14 days'));

    $pdo->beginTransaction();

    try {
        $q = $pdo->prepare(
            'SELECT id FROM copies
             WHERE id = ? AND status = ?
             FOR UPDATE'
        );
        $q->execute([$copyId, 'good']);

        if ($q->fetch() === false) {
            $pdo->rollBack();
            throw new RuntimeException('Copy unavailable');
        }

        $q = $pdo->prepare(
            'INSERT INTO loans
               (copy_id, reader_id, borrowed_at, due_on)
             VALUES (?, ?, NOW(), ?)'
        );
        $q->execute([$copyId, $readerId, $dueOn]);

        $id = (int) $pdo->lastInsertId();

        $q = $pdo->prepare(
            'UPDATE copies SET status = ? WHERE id = ?'
        );
        $q->execute(['on_loan', $copyId]);

        $pdo->commit();

        return $id;
    } catch (PDOException $e) {
        $pdo->rollBack();
        throw $e;
    }
}
```

**Why the `SELECT` alone is not enough** is the question the exercise is
worth, and the answer is the race from chapter @cap:do-arquivo-ao-banco, now
inside the database.

Between the `SELECT` that checks and the `INSERT` that writes there is an
interval. If Vera and Neide lend the same copy in that interval, both
`SELECT`s answer "available", both `INSERT`s write, and the copy goes out
twice. The interval lasts microseconds and it happens — it is exactly what
Vera described on the first day: *"when two people lend at the same time,
one disappears"*.

The `FOR UPDATE` at the end of the `SELECT` is what closes it. It tells the
database: *lock this row until the end of my transaction*. The second
request waits at the `SELECT`, and when its turn comes the status is already
`on_loan` — so it refuses, correctly.

Two honest observations about this version.

The fourteen-day period is calculated in PHP, on the first line, and reaches
the database as a value. The alternative would be
`DATE_ADD(CURDATE(), INTERVAL 14 DAY)` inside the SQL — which works and
buries a business rule in a place that is hard to check. The loan period is
Casa Amarela's decision, not the database's, and it changes in January —
and a rule that changes needs to live where someone can check it.

And the `throw` inside the `try` with a `rollBack` before it is redundant
with the `catch` below only if the exception is a `PDOException`. Since
`RuntimeException` is not one, the explicit `rollBack` before it is
necessary. It is the kind of detail that disappears once the project's
error handling is uniform.
:::
