---
source_hash: 9277a9c032ff
title: "Two tables talking"
number: 14
slug: duas-tabelas-conversando
part: p2
kicker: "Four million rows read to return three results. Since 2011."
goal: >-
  Link tables with a foreign key, answer questions that cross more than one
  with `JOIN` and `GROUP BY`, find out why a query is slow with `EXPLAIN`,
  and save two things or neither.
---

The `loans` table from the previous chapter has a `reader_id` column and no
guarantee that the number stored there matches a reader who exists. Nothing
stops you from saving `reader_id = 99999` in a library with twelve hundred
readers.

And, once saved, nobody finds out — until the day a report shows a loan
without a name.

## The link the database guarantees

```sql
mysql> CREATE TABLE copies (
    ->   id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ->   book_id   INT UNSIGNED NOT NULL,
    ->   accession INT UNSIGNED NOT NULL,
    ->   status    VARCHAR(20)  NOT NULL DEFAULT 'good',
    ->   PRIMARY KEY (id),
    ->   UNIQUE KEY uk_copies_accession (accession),
    ->   CONSTRAINT fk_copies_book
    ->     FOREIGN KEY (book_id) REFERENCES books (id)
    -> ) ENGINE=InnoDB;
Query OK, 0 rows affected (0.05 sec)
```

The last three lines before the closing parenthesis are what is new. They
say: *this table's `book_id` column points to the `id` column of the
`books` table, and the database takes care of keeping that true.*

Test it:

```sql
mysql> INSERT INTO copies (book_id, accession) VALUES (99999, 5000);
ERROR 1452 (23000): Cannot add or update a child row: a foreign
key constraint fails (`casa_amarela`.`copies`, CONSTRAINT
`fk_copies_book` FOREIGN KEY (`book_id`) REFERENCES
`books` (`id`))
```

The database refused. There was no warning, no half-saved row, no bad data
waiting to be discovered in 2029.

And the protection works both ways:

```sql
mysql> DELETE FROM books WHERE id = 1;
ERROR 1451 (23000): Cannot delete or update a parent row: a
foreign key constraint fails
```

You cannot delete a book that has copies. The database protects the link
regardless of which program is touching it — including you, in the
terminal, at six in the evening.

:::term Referential integrity
The guarantee that every reference points to something that exists. It is
what separates a database from a set of spreadsheets: the rule belongs to
the database, not to the program, and so it applies to every program at the
same time — including the import script someone wrote in a hurry.
:::

You can choose what happens when the side being pointed to is removed:

| Clause | What it does |
|---|---|
| `ON DELETE RESTRICT` | refuses the removal (the default) |
| `ON DELETE CASCADE` | deletes, in cascade, the rows that pointed to it |
| `ON DELETE SET NULL` | clears the column, if it accepts null |

Table: `CASCADE` solves one problem and creates a bigger one — deleting a
book by mistake starts silently deleting all its copies and all its loans.

:::key
Use `RESTRICT` by default, which is the default. `CASCADE` only when the row
being pointed to **does not exist without** the row that points: an order
item does not exist without the order, and deleting the order can take it
along.

A copy is not of that kind. It is a physical object that stays on the shelf
even if someone deletes the title's record.
:::

:::pitfall
A difference between databases that costs dearly when switching from one to
the other: **in MySQL with InnoDB, creating a foreign key automatically
creates an index on the column**, if there is not one already. In
PostgreSQL, it does not — and there the absence of that index is one of the
most common causes of slow `DELETE`s, because each removal has to scan the
entire child table looking for references.

If you come from one and go to the other, check.
:::

## The whole schema

With that, Casa Amarela's domain fits in four tables:

```sql title="schema.sql"
CREATE TABLE books (
  id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
  title   VARCHAR(200) NOT NULL,
  author  VARCHAR(150) NOT NULL,
  isbn    CHAR(13)     NULL,
  subject VARCHAR(40)  NOT NULL,
  year    SMALLINT     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_books_isbn (isbn)
) ENGINE=InnoDB;

CREATE TABLE copies (
  id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  book_id   INT UNSIGNED NOT NULL,
  accession INT UNSIGNED NOT NULL,
  status    VARCHAR(20)  NOT NULL DEFAULT 'good',
  PRIMARY KEY (id),
  UNIQUE KEY uk_copies_accession (accession),
  FOREIGN KEY (book_id) REFERENCES books (id)
) ENGINE=InnoDB;

CREATE TABLE readers (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name          VARCHAR(120) NOT NULL,
  document      CHAR(11)     NOT NULL,
  registered_at DATE         NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_readers_document (document)
) ENGINE=InnoDB;

CREATE TABLE loans (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  copy_id           INT UNSIGNED NOT NULL,
  reader_id         INT UNSIGNED NOT NULL,
  borrowed_at       DATETIME     NOT NULL,
  due_on            DATE         NOT NULL,
  returned_at       DATETIME     NULL,
  fine_in_cents     INT UNSIGNED NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (copy_id) REFERENCES copies (id),
  FOREIGN KEY (reader_id) REFERENCES readers (id)
) ENGINE=InnoDB;
```

Notice what does **not** exist here: there is no `quantity` column in
`books`, and no `available` column in `copies`. Both can be calculated from
`loans`, and a calculated number does not drift from reality.

:::key
The tidying rule the schema above follows has a pompous name —
*normalization* — and three practical questions:

1. **Does each column hold one thing only?** An `author` field with
	 `"Machado de Assis; Aluísio Azevedo"` holds two, and no query will be
	 able to separate them reliably.
2. **Does each table talk about one subject only?** If `loans` had
	 `reader_name`, the name would exist in two places and they would drift
	 apart at the first spelling correction.
3. **Is nothing stored that could be calculated?** `quantity` can be. Out.

Answering yes to all three covers the overwhelming majority of cases. The
rest of the theory exists and rarely changes a practical decision.
:::

## The question that involves two tables

The schema is tidy and it created a problem: the book's title is no longer
in the same table as the copy. To list copies with their titles, you have
to join the two.

```sql
mysql> SELECT c.accession, b.title
    -> FROM copies c
    -> JOIN books b ON b.id = c.book_id;
+-----------+---------------+
| accession | title         |
+-----------+---------------+
|       812 | O Cortiço     |
|       907 | O Cortiço     |
|       344 | Vidas Secas   |
|      1120 | Grande Sertão |
+-----------+---------------+
4 rows in set (0.00 sec)
```

Read it from the `FROM`: *start with the copies, and for each of them find
the book whose `id` equals the copy's `book_id`.*

The `c` and the `b` after the table names are **aliases**. They exist so
that `c.accession` and `b.title` say which table each column came from —
which stops being a convenience and becomes an obligation when two tables
have columns with the same name, like `id`.

The `ON` is the join condition, and it is the part nobody may forget:

:::pitfall
A `JOIN` without `ON` — or with an `ON` that links nothing — produces the
**Cartesian product**: every row on one side combined with every row on
the other.

With 8,000 copies and 4,000 books, that is 32 million rows. The command does
not raise an error. It starts returning results, and the machine grinds to a
halt.

When a query that should bring back dozens brings back millions, look at the
`ON` before anything else.
:::

Three tables follow the same form:

```sql
mysql> SELECT b.title, r.name, lo.due_on
    -> FROM loans lo
    -> JOIN copies c ON c.id = lo.copy_id
    -> JOIN books b ON b.id = c.book_id
    -> JOIN readers r ON r.id = lo.reader_id
    -> WHERE lo.returned_at IS NULL
    -> ORDER BY lo.due_on;
+---------------+------------------+------------+
| title         | name             | due_on     |
+---------------+------------------+------------+
| O Cortiço     | Marlene Coutinho | 2027-02-18 |
| Grande Sertão | Juvenal Pereira  | 2027-02-24 |
+---------------+------------------+------------+
2 rows in set (0.00 sec)
```

That is Vera's outstanding list, in one query, with no loop at all. It is
literally the report that took four tenths of a second walking through lists
in memory, now done by the database — which was built for this and does not
get slower as the library grows.

## The row with no partner

```sql
mysql> SELECT b.title, COUNT(c.id) AS copies
    -> FROM books b
    -> JOIN copies c ON c.book_id = b.id
    -> GROUP BY b.id, b.title;
```

This query has a silent bug: books **without any copy** do not appear.
`JOIN` only returns rows that found a partner on both sides, and a newly
registered book, whose copies have not arrived yet, simply disappears from
the report.

The fix is one word:

```sql
mysql> SELECT b.title, COUNT(c.id) AS copies
    -> FROM books b
    -> LEFT JOIN copies c ON c.book_id = b.id
    -> GROUP BY b.id, b.title
    -> ORDER BY copies DESC;
+--------------------+--------+
| title              | copies |
+--------------------+--------+
| O Cortiço          |      2 |
| Vidas Secas        |      1 |
| Grande Sertão      |      1 |
| O Pequeno Príncipe |      0 |
+--------------------+--------+
4 rows in set (0.00 sec)
```

`LEFT JOIN` brings **all** rows from the table on the left, whether they
have a partner or not. When they do not, the columns on the right come back
null.

:::key
The difference between `JOIN` and `LEFT JOIN` is not technical, it is about
the question.

`JOIN` answers *"which pairs exist?"*. `LEFT JOIN` answers *"what does the
left table have, with whatever there is on the right?"*.

The classic mistake is using `JOIN` when the question was the second one —
and the symptom is a report missing exactly the most interesting rows: the
book with no copy, the reader who never borrowed anything, the month with no
activity.
:::

Notice the `COUNT(c.id)` and not `COUNT(*)`. In a `LEFT JOIN`, the row for
the book with no copy exists, so `COUNT(*)` would count `1`. `COUNT(c.id)`
ignores nulls and returns `0`, which is the right answer.

## Grouping to count

```sql
mysql> SELECT b.subject,
    ->        COUNT(*) AS loans
    -> FROM loans lo
    -> JOIN copies c ON c.id = lo.copy_id
    -> JOIN books b ON b.id = c.book_id
    -> WHERE lo.borrowed_at >= '2027-02-01'
    ->   AND lo.borrowed_at <  '2027-03-01'
    -> GROUP BY b.subject
    -> ORDER BY loans DESC;
+------------+-------+
| subject    | loans |
+------------+-------+
| children   |   214 |
| literature |   188 |
| reference  |    12 |
+------------+-------+
3 rows in set (0.01 sec)
```

`GROUP BY` gathers the rows that have the same value in the given column
and produces **one row per group**. The aggregate functions — `COUNT`,
`SUM`, `AVG`, `MIN`, `MAX` — work within each group.

That is the answer the grant's accountability report asks for, and it
replaces the PHP program with three nested loops from chapter
@cap:repeticoes with nine lines the database resolves in hundredths of a
second.

Notice also the date filter: `>= '2027-02-01' AND < '2027-03-01'`, instead
of `BETWEEN '2027-02-01' AND '2027-02-28'`. The second form loses the loans
made on the 28th after 00:00, because the column is `DATETIME` and
`'2027-02-28'` means midnight sharp. The half-open interval — includes the
start, excludes the end — does not have that problem and does not even need
to know how many days the month has.

:::pitfall
To filter **after** grouping, `WHERE` is no good: it runs before `GROUP BY`
and does not see the result of the count. There is `HAVING` for that:

```sql
GROUP BY b.subject
HAVING COUNT(*) > 50
```

The rule: `WHERE` filters rows, `HAVING` filters groups. Putting
`COUNT(*) > 50` in the `WHERE` is an error; putting `subject = 'children'`
in the `HAVING` works and is slower, because the database groups everything
only to throw it away afterwards.
:::

## Four million rows

:::story The 2011 search
"How long does the System's search take?" asked Márcia.

"It depends," said Vera.

"Depends on what?"

"On the time of day. In the morning it's fast. After lunch it freezes."

Dedé asked for the query. Nonato remembered it by heart:

```sql
SELECT * FROM books WHERE title LIKE '%sertao%'
```

He ran it with one word in front:

```text
mysql> EXPLAIN SELECT * FROM books
    -> WHERE title LIKE '%sertao%';
+------+------+------+-------------+
| type | key  | rows | Extra       |
+------+------+------+-------------+
| ALL  | NULL | 4000 | Using where |
+------+------+------+-------------+
```

"`type: ALL`," he said. "It reads the whole table."

"Is four thousand rows a lot?"

"For books, no. The problem is `copies`, which does the same with eight
thousand, and `loans`, with four hundred thousand since 2009. Each search
adds up."

Márcia wrote it down.

"And after lunch?"

"After lunch there are fifteen people using it at the same time."
:::

`EXPLAIN` in front of any `SELECT` shows the execution plan: what the
database intends to do before doing it. The real output has twelve columns;
the four above are the ones that decide almost everything.

| Column | What it means |
|---|---|
| `type` | how the rows are reached. `ALL` is a full scan |
| `key` | which index was used. `NULL` is none |
| `rows` | how many rows the database estimates it will **read** |
| `Extra` | warnings, among them `Using filesort` and `Using temporary` |

Table: The quick reading: `type: ALL` with a high `rows` is a query that
will get worse on its own as the table grows.

An **index** is a separate structure the database keeps sorted, so that it
does not have to scan everything. It is the difference between looking for
a word by leafing through the whole book and looking it up in the index at
the back.

```sql
mysql> CREATE INDEX idx_loans_reader
    -> ON loans (reader_id);
Query OK, 0 rows affected (0.09 sec)

mysql> EXPLAIN SELECT * FROM loans WHERE reader_id = 47;
+------+------------------+------+
| type | key              | rows |
+------+------------------+------+
| ref  | idx_loans_reader |    7 |
+------+------------------+------+
```

From 400,000 rows read to 7. The `type` went from `ALL` to `ref`, and the
query now costs the same with four hundred thousand or with four million
loans.

But notice what the index does **not** fix: Nonato's search still reads
everything.

```sql
mysql> CREATE INDEX idx_books_title ON books (title);

mysql> EXPLAIN SELECT * FROM books WHERE title LIKE '%sertao%';
+------+------+------+
| type | key  | rows |
+------+------+------+
| ALL  | NULL | 4000 |
+------+------+------+
```

The index exists and was not used. The reason is the position of the `%`:
an index keeps values **sorted**, and sorting only helps whoever knows the
start of the word. `LIKE 'sertao%'` uses the index; `LIKE '%sertao%'`
cannot, because the piece being searched for could be in any position.

:::key
An index speeds up reading and **costs writing**: every `INSERT`, `UPDATE`
and `DELETE` has to update all of the table's indexes. A table with eight
indexes writes noticeably slower than the same table with two.

The practical rule: create indexes for the columns that appear in `WHERE`,
in `JOIN` and in `ORDER BY` of queries that run a lot. Do not create them
just in case. And check with `EXPLAIN` that it is being used — an index
created and ignored is the worst of both worlds: it costs the writes and
does not pay for the reads.
:::

For searching a piece in the middle of the text, the path in MySQL is
different: a `FULLTEXT` index, which indexes words instead of whole values.
It is the way out for Vera's search, and it pairs with the normalized search
key from chapter @cap:strings — the index finds the word, the normalization
guarantees that "SERTAO" and "Sertão" are the same word.

## All or nothing

Recording a loan is two writes: the row in `loans` and the change in the
copy's status. If the first works and the second fails, the system is left
with a loan whose copy is still marked as available — and someone lends the
same book twice.

```sql
mysql> START TRANSACTION;
Query OK, 0 rows affected (0.00 sec)

mysql> INSERT INTO loans
    ->   (copy_id, reader_id, borrowed_at, due_on)
    -> VALUES (1, 1, NOW(), '2027-02-18');
Query OK, 1 row affected (0.00 sec)

mysql> UPDATE copies SET status = 'on_loan' WHERE id = 1;
Query OK, 1 row affected (0.00 sec)

mysql> COMMIT;
Query OK, 0 rows affected (0.01 sec)
```

Between `START TRANSACTION` and `COMMIT`, nothing that was done exists for
other programs. At `COMMIT`, it all comes into existence at once. And if
something goes wrong in the middle:

```sql
mysql> ROLLBACK;
```

The database undoes everything that happened since `START TRANSACTION`, as
if nothing had been typed.

:::term Transaction
A set of operations treated as one: either all of them happen, or none of
them does. It is what stops a failure in the middle of a sequence from
leaving the database in a state the business rule forbids.

It is also the definitive answer to the race from chapter
@cap:do-arquivo-ao-banco: while a transaction touches a row, the others wait
for that row — not for the whole file.
:::

:::warning
MySQL, by default, runs in *autocommit*: each command is a transaction of
its own, committed on the spot. That means that, without
`START TRANSACTION`, the `UPDATE` without `WHERE` from Nonato's Friday **was
already committed** the instant he pressed Enter. There was nothing to undo.

With a transaction open, there would have been — and `ROLLBACK` would have
saved that Friday. It works as a practical argument for opening a
transaction for any manual change you make in production, even a one-liner.
:::

:::note In your career
"It depends on the time of day" is the kind of report that tends to be
dismissed as an impression, and it is almost always the most valuable
information in the ticket.

Vera could not say "the query does a full scan and contention shows up under
concurrency". She could say that in the morning it was fast and after lunch
it froze — which is exactly the same sentence, in the language of the person
who uses it.

When someone describes a problem by **when** it happens, instead of **what**
happens, write down the when. Time of day, day of the month, weekend,
month-end close: those patterns point to load, to a scheduled task or to
accumulated volume, and they are the half of the diagnosis that is not in
the code.
:::

:::summary
- A foreign key makes the database guarantee that every reference points to
	something that exists — for every program, not just yours.
- `RESTRICT` by default; `CASCADE` only when the child does not exist
	without the parent.
- `JOIN` brings the pairs; `LEFT JOIN` brings everything on the left, with
	null where there is no partner.
- A `JOIN` without `ON` produces a Cartesian product, with no error at all.
- `GROUP BY` produces one row per group; `WHERE` filters rows, `HAVING`
	filters groups.
- A half-open date interval (`>=` and `<`) avoids losing the last day.
- `EXPLAIN` shows the plan: `type: ALL` with a high `rows` is a scan.
- An index speeds up reads and costs writes; `LIKE '%term%'` does not use a
	regular index.
- A transaction turns two writes into one; without it, MySQL commits
	everything on the spot.
:::

:::milestone
Casa Amarela's domain exists in four linked tables, with the rules
guaranteed by the database. The five questions Vera asked at the counter now
have one-line answers each.
:::

:::exercise level=1
Write the query that lists, for each copy, the accession number, the book's
title and the status — sorted by title. Then change it to show only the
copies in repair.

:::answer
```sql
SELECT c.accession, b.title, c.status
FROM copies c
JOIN books b ON b.id = c.book_id
ORDER BY b.title;

SELECT c.accession, b.title, c.status
FROM copies c
JOIN books b ON b.id = c.book_id
WHERE c.status = 'in_repair'
ORDER BY b.title;
```

`JOIN` is the right one here, not `LEFT JOIN`: every copy has a book, and
the foreign key guarantees it. Where the link is mandatory, both return the
same result — and `JOIN` tells the reader that the obligation exists.
:::

:::exercise level=2
The five questions Vera asked at the counter were: which copy does Mrs.
Marlene have, which one is torn, which one went missing, how many are free,
and which were the most borrowed this month. Write the five queries.

:::answer
```sql
-- 1. which copy Mrs. Marlene has
SELECT c.accession, b.title, lo.due_on
FROM loans lo
JOIN copies c ON c.id = lo.copy_id
JOIN books b ON b.id = c.book_id
JOIN readers r ON r.id = lo.reader_id
WHERE r.name = 'Marlene Coutinho'
  AND lo.returned_at IS NULL;

-- 2. which ones are torn
SELECT c.accession, b.title
FROM copies c
JOIN books b ON b.id = c.book_id
WHERE c.status = 'damaged';

-- 3. which ones went missing
SELECT c.accession, b.title
FROM copies c
JOIN books b ON b.id = c.book_id
WHERE c.status = 'lost';

-- 4. how many copies of this book are free
SELECT COUNT(*) AS free
FROM copies c
LEFT JOIN loans lo
  ON lo.copy_id = c.id AND lo.returned_at IS NULL
WHERE c.book_id = 1
  AND c.status = 'good'
  AND lo.id IS NULL;

-- 5. the most borrowed this month
SELECT b.title, COUNT(*) AS times
FROM loans lo
JOIN copies c ON c.id = lo.copy_id
JOIN books b ON b.id = c.book_id
WHERE lo.borrowed_at >= '2027-02-01'
  AND lo.borrowed_at <  '2027-03-01'
GROUP BY b.id, b.title
ORDER BY times DESC
LIMIT 10;
```

The fourth is the most interesting one, and it deserves attention.

It uses `LEFT JOIN` with the "still open" condition **inside the `ON`**, and
then filters `lo.id IS NULL` in the `WHERE`. That is the idiom for "bring
what has **no** partner": the `LEFT JOIN` brings all the copies, with an
open loan when there is one, and the `IS NULL` keeps only the ones with
none.

If the condition `returned_at IS NULL` went into the `WHERE` instead of the
`ON`, it would eliminate precisely the rows with no partner — and the query
would always return zero.

And notice that the fifth answers the question from chapter
@cap:o-que-vamos-construir: it counts by **book**, grouping the loans of all
copies of that title. Counting by copy would be `GROUP BY c.id`, and would
answer something else.
:::

:::exercise level=3
The return operation does three things: saves the date in `loans`,
calculates the fine, and changes the copy's status to available. Write it
as a transaction and answer: what happens if the connection drops between
the second and the third? And what would happen without the transaction?

:::answer
```sql
START TRANSACTION;

UPDATE loans
SET returned_at = NOW(),
    fine_in_cents = 720
WHERE id = 3315
  AND returned_at IS NULL;

UPDATE copies
SET status = 'good'
WHERE id = (SELECT copy_id FROM loans WHERE id = 3315);

COMMIT;
```

**If the connection drops before `COMMIT`**, the database undoes everything
on its own. There is no intermediate state: the loan is still open, the copy
is still on loan, and the return can be redone from the start. The desk
repeats the operation and nobody ever knows.

**Without the transaction**, each `UPDATE` is committed the instant it runs.
A drop between the two leaves the database in a state the business rule
forbids: loan returned, copy marked as on loan. The book goes back on the
shelf and the system refuses to lend it again, forever, until someone
notices and fixes it by hand.

That state is worse than the whole failure, for a reason worth remembering:
**the failure warns you, the inconsistent state does not.** The operation
that drops in the middle shows an error on screen and someone repeats it.
The one that saves halfway ends by saying "returned successfully".

Two observations about the query.

The `AND returned_at IS NULL` in the first `UPDATE` is not decoration: it
stops a return recorded twice from overwriting the original date and
recalculating the fine. When `Rows matched` comes back `0`, it is because
someone already returned it.

And the fine appears here as a ready-made number, which is a
simplification: it depends on `due_on`, on today's date and on the rule in
force. Calculating business rules inside SQL is possible and almost always
undesirable — the calculation lives in PHP, which is where it can be checked
line by line.
:::
