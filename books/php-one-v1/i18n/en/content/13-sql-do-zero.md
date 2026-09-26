---
source_hash: 7df1dd3c4dd5
title: "SQL: the five sentences that get you through the day"
number: 13
slug: sql-do-zero
part: p2
kicker: "An UPDATE without a WHERE on a Friday returned eight thousand books nobody had returned."
goal: >-
  Create a table choosing each column's type on purpose, insert, query with
  filtering and sorting, and change exactly the rows you meant to change.
---

:::story Nonato is back
Nonato came back from vacation on a Monday, and at 9:40 he was in a room
with four people and a projector showing the structure of Casa Amarela's
database.

He had written it in 2009, over a weekend, at twenty-three, for twelve
hundred reais.

"This column here," said Tainá, pointing. "`returned`. Is it just a zero or
a one?"

"It is."

"And where is the return date stored?"

Nonato looked at the screen for a while.

"It isn't."

"And if someone asks when a book came back?"

"Nobody's asked in fifteen years."

Márcia, without looking up:

"The grant's accountability report asks for the catalog's movement by
month."

Nonato looked at the screen again, longer this time.

"Then now someone's asked."
:::

A field that stores "yes or no" costs one byte and throws away the date. A
field that stores the date costs three bytes and answers both questions:
whoever has a date returned the book; whoever does not, did not.

That two-byte decision is the subject of this chapter. It is called
**choosing the column type**, it happens once, and Casa Amarela lived with
the wrong version of it for fifteen years.

## Design the card before filling it in

```sql
mysql> USE casa_amarela;
Database changed

mysql> CREATE TABLE books (
    ->   id      INT UNSIGNED NOT NULL AUTO_INCREMENT,
    ->   title   VARCHAR(200) NOT NULL,
    ->   author  VARCHAR(150) NOT NULL,
    ->   isbn    CHAR(13)     NULL,
    ->   subject VARCHAR(40)  NOT NULL,
    ->   year    SMALLINT     NULL,
    ->   PRIMARY KEY (id),
    ->   UNIQUE KEY uk_books_isbn (isbn)
    -> ) ENGINE=InnoDB;
Query OK, 0 rows affected (0.04 sec)
```

Ten lines that decide a lot. It is worth unpacking them in four parts.

**The name and the list of columns.** `CREATE TABLE books` creates the stack
of cards; each line inside the parentheses is a field printed on the card,
with a name and a type.

**`NOT NULL` and `NULL`.** `NOT NULL` means "this column can never be left
blank" — the database refuses to save. `NULL` means "it can be left blank",
and it is a statement about the business: not every book has an ISBN,
because the ISBN only exists since 1970 and Casa Amarela has older
editions.

**`PRIMARY KEY (id)`.** A column that identifies the row, never repeated and
never empty. It is the paper accession number, promoted to a database rule.

**`UNIQUE KEY`.** Says there cannot be two rows with the same ISBN. It is
different from a primary key: a table has one primary key and can have as
many uniqueness constraints as it wants.

:::term DDL and DML
SQL commands split into two families. **DDL** (*Data Definition Language*)
touches the structure: `CREATE`, `ALTER`, `DROP`. **DML** (*Data
Manipulation Language*) touches the data: `INSERT`, `SELECT`, `UPDATE`,
`DELETE`.

The practical difference is that DDL is expensive to undo and DML is not.
Creating a wrong table costs an afternoon; inserting a wrong row costs a
`DELETE`.
:::

`AUTO_INCREMENT` makes the database assign the next free number on its
own: you insert a book without giving an `id` and it becomes 1, the next
becomes 2. That spares you the question "what was the last one?", which in
a system with two clerks is the race from chapter @cap:do-arquivo-ao-banco
all over again.

And the `ENGINE=InnoDB` at the end chooses the storage engine. It is the
default in MySQL 8 and it is what you want: it is the only one that does
transactions and guarantees foreign keys. Writing it explicitly costs twelve
characters and avoids inheriting an old server's default.

To check what was saved:

```sql
mysql> DESCRIBE books;
+---------+------------------+------+-----+---------+----------------+
| Field   | Type             | Null | Key | Default | Extra          |
+---------+------------------+------+-----+---------+----------------+
| id      | int unsigned     | NO   | PRI | NULL    | auto_increment |
| title   | varchar(200)     | NO   |     | NULL    |                |
| author  | varchar(150)     | NO   |     | NULL    |                |
| isbn    | char(13)         | YES  | UNI | NULL    |                |
| subject | varchar(40)      | NO   |     | NULL    |                |
| year    | smallint         | YES  |     | NULL    |                |
+---------+------------------+------+-----+---------+----------------+
6 rows in set (0.00 sec)
```

`DESCRIBE` shows a table's structure. It is the first command to run when
you open a database you do not know — before reading any code.

## The type is a business decision

Each type was chosen deliberately, and each one answers a question about
Casa Amarela.

| Type | Holds | When to use |
|---|---|---|
| `INT` | integer up to ~2.1 billion | identifier, count, cents |
| `SMALLINT` | integer up to 32,767 | year, small quantity |
| `VARCHAR(n)` | variable-length text, up to `n` | title, name, address |
| `CHAR(n)` | **fixed**-length text | ISBN, state code, known-length code |
| `TEXT` | long text, no practical limit | note, description |
| `DATE` | the date only | publication date, due date |
| `DATETIME` | date and time | when the loan happened |
| `DECIMAL(p,s)` | exact number with decimals | monetary value |
| `BOOLEAN` | true or false | alias for `TINYINT(1)` |

Table: There is no `FLOAT` on this list on purpose. It exists and it is for
physical measurements — weight, temperature, coordinates — and never for
money, for the reason in chapter @cap:conversao-automatica.

Four of these choices deserve an explanation, because they are where people
get it wrong.

**`VARCHAR(200)` and not `VARCHAR(255)`.** The number 255 became a habit
for a historical reason that no longer exists: until MySQL 5.0, a `VARCHAR`
of up to 255 characters used one fewer control byte. Today that changes
nothing on disk, and the number you write has become what it looks like: a
**statement about the business**. `VARCHAR(200)` says "a book title does not
exceed two hundred characters". If it does, the database refuses — and it
is good that it refuses, because an eight-hundred-character title is almost
always an import error.

**`CHAR(13)` for ISBN.** An ISBN has thirteen digits, always. `CHAR` is for
fixed length and is slightly more efficient in that case. And notice that it
is text, not a number: an ISBN can start with zero, and a leading zero dies
in a numeric column.

**`DATETIME` and not `TIMESTAMP`.** Both store date and time. The difference
is that `TIMESTAMP` converts to UTC when saving and converts back when
reading, using the time zone configured on the server — which is great for
an international system and a trap when someone changes the server's
configuration and all the old dates change value. `DATETIME` stores what you
sent. For a neighborhood library, `DATETIME` is more predictable.

**`DECIMAL(10,2)` for money, if you keep money in the database.** It stores
the number in base ten, exactly, with ten digits in total and two after the
decimal point. It is the right choice when the value lives in the database.

:::pitfall
There is a PHP detail that decides this choice and is almost never
mentioned: a `DECIMAL` column **comes back to PHP as a string**. PHP has no
exact decimal type, so the driver returns `"7.20"` instead of a number —
because converting it to a `float` would undo the exactness the column
guaranteed.

That means you have to decide what to do with that string everywhere it
shows up. The alternative is to store an `INT` in cents, which comes back as
an integer and makes the math add up on both sides. That is this book's
choice, and the column is called `fine_in_cents`.

`DECIMAL` is still right — in serious financial systems it is what people
use, with a class that handles the string. The choice here is about
consistency, not superiority.
:::

:::key
The rule that avoids most schema problems: **`NOT NULL` by default, `NULL`
by justified exception.**

Every column starts out forbidden to be empty. When you want to allow it,
stop and write in one sentence why that piece of data might not exist. "Not
every book has an ISBN" is a justification. "Just in case it's missing one
day" is not — that is the road to a table where half the columns accept
null and no query can trust anything.
:::

## Inserting

```sql
mysql> INSERT INTO books (title, author, isbn, subject, year)
    -> VALUES ('O Cortiço', 'Aluísio Azevedo', '9788572326972',
    ->         'literature', 1890);
Query OK, 1 row affected (0.01 sec)
```

The list of columns comes first, the values afterwards, in the same order.
The `id` was not given because `AUTO_INCREMENT` takes care of it.

Text goes in **single quotes**. Numbers go without quotes. That is the only
formatting rule you need to remember right now, and it is the same one that
will cause the security problem in the next chapter.

Several rows at once:

```sql
mysql> INSERT INTO books (title, author, subject, year) VALUES
    ->   ('Vidas Secas', 'Graciliano Ramos', 'literature', 1938),
    ->   ('Grande Sertão', 'Guimarães Rosa', 'literature', 1956),
    ->   ('O Pequeno Príncipe', 'Saint-Exupéry', 'children', 1943);
Query OK, 3 rows affected (0.01 sec)
Records: 3  Duplicates: 0  Warnings: 0
```

Three rows in a single command. Notice that `isbn` was left out: since the
column accepts `NULL`, the database stores null without complaint. If you
left out `title`, which is `NOT NULL`, it would be another story:

```sql
mysql> INSERT INTO books (author, subject) VALUES ('Anon', 'misc');
ERROR 1364 (HY000): Field 'title' doesn't have a default value
```

That refusal is the schema's work showing. The error came at save time,
with the column's name, and not six months later on a screen showing a blank
title.

## Querying

```sql
mysql> SELECT id, title, year FROM books;
+----+--------------------+------+
| id | title              | year |
+----+--------------------+------+
|  1 | O Cortiço          | 1890 |
|  2 | Vidas Secas        | 1938 |
|  3 | Grande Sertão      | 1956 |
|  4 | O Pequeno Príncipe | 1943 |
+----+--------------------+------+
4 rows in set (0.00 sec)
```

`SELECT` chooses the columns, `FROM` chooses the table. There is
`SELECT *`, which brings every column, and is convenient in the terminal
and bad in a program: when someone adds a `TEXT` note column, your program
starts fetching it in every query without ever using it.

And there is `WHERE`, which is where the query starts being worth
something:

```sql
mysql> SELECT title, year FROM books
    -> WHERE subject = 'literature' AND year > 1900;
+---------------+------+
| title         | year |
+---------------+------+
| Vidas Secas   | 1938 |
| Grande Sertão | 1956 |
+---------------+------+
2 rows in set (0.00 sec)
```

`WHERE` is the line that decides which rows get in. It accepts the usual
comparisons — `=`, `<>`, `>`, `<`, `>=`, `<=` — plus three more worth
knowing:

```sql
mysql> SELECT title FROM books WHERE title LIKE '%Sert%';
mysql> SELECT title FROM books WHERE year BETWEEN 1930 AND 1950;
mysql> SELECT title FROM books
    -> WHERE subject IN ('children', 'young_adult');
mysql> SELECT title FROM books WHERE isbn IS NULL;
```

`LIKE` searches for a piece of text, with `%` standing for "anything".
`BETWEEN` is a shortcut for two comparisons. `IN` is a shortcut for several
`OR`s.

And the last one is the one that catches everyone: to compare with null,
you do **not** use `= NULL`. You use `IS NULL`. The reason is that, in SQL,
`NULL` is not a value — it is the absence of a value — and the comparison
`something = NULL` returns neither true nor false: it returns unknown, and
`WHERE` discards unknown along with false.

:::pitfall
Write `SELECT ... WHERE isbn = NULL` and MySQL gives no error at all. It
returns zero rows, quietly, even though there are three books without an
ISBN.

It is the worst kind of bug: valid syntax, execution without a warning,
wrong answer. When a query returns zero rows and you are sure it should
return some, `= NULL` is the first suspect.
:::

Sorting, counting and limiting:

```sql
mysql> SELECT title, year FROM books
    -> ORDER BY year DESC
    -> LIMIT 2;
+--------------------+------+
| title              | year |
+--------------------+------+
| Grande Sertão      | 1956 |
| O Pequeno Príncipe | 1943 |
+--------------------+------+
2 rows in set (0.00 sec)

mysql> SELECT COUNT(*) FROM books WHERE subject = 'literature';
+----------+
| COUNT(*) |
+----------+
|        3 |
+----------+
1 row in set (0.00 sec)
```

`ORDER BY` sorts — `ASC` is ascending and is the default, `DESC` is
descending. `LIMIT` cuts the result. `COUNT(*)` counts rows without fetching
them, which is the difference between asking "how many are there?" and
loading eight thousand records to count them in PHP.

:::key
The order in which SQL is **written** is not the order in which it is
**executed**. The database applies `FROM` first, then `WHERE`, then the
`SELECT` of columns, then `ORDER BY` and finally `LIMIT`.

That explains a confusing behavior: `WHERE` does not see aliases created in
the `SELECT`, because it ran before they existed. And it explains why
`LIMIT 10` on a million-row table can be slow — it cuts at the end, after
the database has already found and sorted everything the filter reached.
:::

## Changing and removing

:::story Friday, 2013
"I've done that," said Nonato, when the subject reached `UPDATE`.

Nobody had asked.

"Friday, 2013. Vera asked me to mark as returned a loan that had come back
the previous Saturday and nobody recorded it."

He wrote on the whiteboard, from memory, in the handwriting of someone who
has written it many times since:

```text
UPDATE loans SET returned = 1
```

"What was missing?"

"The `WHERE`," said Tainá.

"The `WHERE` was missing."

Eight thousand four hundred loans were returned at 5:48 p.m. on a Friday.
Among them, the twelve hundred that were actually still open.

"And then?"

"And then the library had no backup."

Nonato wiped the board.

"It has one since Saturday."
:::

```sql
mysql> UPDATE books SET subject = 'young_adult' WHERE id = 4;
Query OK, 1 row affected (0.01 sec)
Rows matched: 1  Changed: 1  Warnings: 0
```

`UPDATE` changes, `SET` says what, `WHERE` says where. Without `WHERE`, it
changes **every row in the table**, and MySQL does not ask whether you are
sure.

Notice the second line of the response: `Rows matched: 1`. That number is
your confirmation that the `WHERE` reached what you intended. When it comes
back much larger than expected, something has already happened.

```sql
mysql> DELETE FROM books WHERE id = 4;
Query OK, 1 row affected (0.00 sec)
```

`DELETE` removes rows. Without `WHERE`, it empties the table.

:::art caption="One line without a `WHERE`, at 5:48 p.m. on a Friday."
src="uma-linha-sem-where-as-17h48-de-uma-sexta-feira.png"
Minimalist editorial cartoon on a white background: a developer of about
forty, in a plaid shirt, in front of a whiteboard where he has written from
memory, in a firm hand, "UPDATE loans SET returned = 1" — and nothing after
it. On the wall, a clock reads 5:48 and a desk calendar page shows
"FRIDAY". In the background, a filing cabinet of loan cards with every card
jumping out at once, each one stamped "RETURNED". Seated, an intern with her
pen frozen in the air above her notebook. Few elements, dry humor,
tech-magazine aesthetic.
:::

:::warning
Three habits that prevent Nonato's Friday, in order of effectiveness.

**Write the `WHERE` first.** Start typing at the end: `WHERE id = 4`, and
only then go back and write `UPDATE ... SET` in front of it. It looks silly
and it is the habit that works best, because it eliminates the window in
which the command is syntactically complete and dangerous.

**Run it as a `SELECT` first.** Swap `UPDATE books SET ...` for
`SELECT * FROM books`, keeping the same `WHERE`. What shows up is exactly
what would be changed. Check it, then swap the beginning back.

**Turn on the safety net.** The MySQL client accepts the `--safe-updates`
option (or `-U`), which **refuses** `UPDATE` and `DELETE` without a `WHERE`
that uses a key:

```text
$ mysql -u root -p -U casa_amarela

mysql> DELETE FROM books;
ERROR 1175 (HY000): You are using safe update mode and you
tried to update a table without a WHERE that uses a KEY column
```

Put it in your MySQL configuration file and forget it exists. On the day it
saves you, it will have paid for all the days it got in your way.
:::

And there is a fourth protection, of a different nature: **don't delete**.
Instead of `DELETE`, many tables get a `removed_at DATETIME NULL` column,
and "removing" becomes filling in that date. Nothing disappears, you can
undo it, and you can answer "who deleted it and when". The cost is that
every query now needs `WHERE removed_at IS NULL`, and forgetting it once
brings the deleted records back onto the screen.

:::note In your career
The first time you wreck production data, there will be a strong temptation
to fix it quietly before anyone notices. Don't — and not for moral reasons,
for mathematical ones: the time between the mistake and the warning is the
variable that most decides the size of the damage.

What works, in order: **stop touching things**, tell whoever is responsible
for the system, say what happened in one sentence and what you already know
about the reach ("an `UPDATE` without `WHERE` on the loans table, at
5:48 p.m., 8,412 rows"). Only then discuss the fix.

And notice what Nonato did right in 2013: he started telling the story. A
team where the serious mistake is told by the person who made it is a team
where the next mistake shows up fast.
:::

:::summary
- `CREATE TABLE` designs the card; `DESCRIBE` shows what came out.
- The column type is a business decision: `VARCHAR(200)` states a limit,
	`CHAR(13)` states a format, `DATE` states that the time does not matter.
- `NOT NULL` by default; `NULL` only with a written justification.
- The primary key identifies the row; `AUTO_INCREMENT` fills it in on its
	own; `UNIQUE` prevents repetition in another column.
- A `DECIMAL` column comes back to PHP as text — hence the choice of `INT`
	in cents.
- `WHERE` decides which rows get in; null is compared with `IS NULL`, never
	with `= NULL`.
- `COUNT(*)` counts without fetching; `ORDER BY` sorts; `LIMIT` cuts at the
	end.
- `UPDATE` and `DELETE` without `WHERE` reach the whole table, without
	asking.
:::

:::milestone
Casa Amarela's catalog exists outside PHP. The `books` table is created,
with chosen types and rules the database guarantees, and you query and
change whatever you want from the terminal.
:::

:::exercise level=1
Create the `readers` table with: an automatic identifier, a required name of
up to 120 characters, a unique 11-character document, a registration date,
and an optional phone number. Then insert two readers and list them sorted
by name.

:::answer
```sql
CREATE TABLE readers (
  id             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name           VARCHAR(120) NOT NULL,
  document       CHAR(11)     NOT NULL,
  registered_at  DATE         NOT NULL,
  phone          VARCHAR(20)  NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_readers_document (document)
) ENGINE=InnoDB;

INSERT INTO readers (name, document, registered_at, phone)
VALUES
  ('Marlene Coutinho', '11122233344', '2009-03-14', NULL),
  ('Juvenal Pereira',  '55566677788', '2011-08-02', '31 9999-1234');

SELECT id, name, registered_at FROM readers ORDER BY name;
```

```text
+----+------------------+---------------+
| id | name             | registered_at |
+----+------------------+---------------+
|  2 | Juvenal Pereira  | 2011-08-02    |
|  1 | Marlene Coutinho | 2009-03-14    |
+----+------------------+---------------+
```

Three decisions worth defending: `CHAR(11)` because the document has a
fixed length and can start with zero; `DATE` and not `DATETIME` because
nobody cares about the time of registration; and phone as an optional
`VARCHAR`, because people without a phone exist and because phone numbers
have parentheses, dashes and spaces — they are never numbers.
:::

:::exercise level=2
Without running them, say how many rows each command below would change in
a `books` table with 4,000 records, of which 91 are reference books and 12
have no ISBN. Then say which one you would never run.

```sql
UPDATE books SET subject = 'reference' WHERE subject = 'ref';
UPDATE books SET year = 2000 WHERE isbn = NULL;
UPDATE books SET subject = 'general';
DELETE FROM books WHERE id = 99999;
```

:::answer
**The first:** zero or many, and nobody knows without looking. It depends on
how the 91 reference records were saved — with the full word or
abbreviated. It is a legitimate cleanup command, and the right way to run it
is to check first with `SELECT COUNT(*) FROM books WHERE subject = 'ref';`.

**The second:** zero rows, always, even with twelve books without an ISBN.
`= NULL` compares with nothing. The command runs, answers `Rows matched: 0`
and does nothing — and whoever wrote it will spend half an hour looking for
the bug somewhere else. The right form is `WHERE isbn IS NULL`.

**The third:** 4,000 rows. All of them. It is Nonato's command, with a
different column name.

**The fourth:** zero rows, with no consequence at all. A `DELETE` with a
`WHERE` that finds nobody simply deletes nothing.

**The one I would never run is the third** — and it is worth noting why it
is different from the second. The second is harmless by accident: it is
wrong, and its mistake makes it innocuous. The third is syntactically
perfect, and that is precisely why it destroys the table without a single
question.
:::

:::exercise level=3
The System's `loans` table, written in 2009, is this:

```sql
CREATE TABLE loans (
  id          INT NOT NULL AUTO_INCREMENT,
  book_id     INT NOT NULL,
  reader      VARCHAR(120) NOT NULL,
  date        VARCHAR(20) NOT NULL,
  returned    TINYINT(1) NOT NULL DEFAULT 0,
  fine        FLOAT NULL,
  PRIMARY KEY (id)
);
```

Point out five problems and write the version you would propose. For each
change, say what question it now makes possible.

:::answer
**1. `reader VARCHAR(120)` stores the name, not the reader.** Two readers
with the same name are the same person to this table, and a reader who
changes their name disappears from their own history. It becomes
`reader_id INT UNSIGNED NOT NULL`, pointing to the `readers` table.
*Now possible:* "which loans belong to this person?", with certainty.

**2. `date VARCHAR(20)` stores a date as text.** Sorting by that column
sorts alphabetically: `10/03/2011` comes before `09/04/2011`. And anything
fits in there, including `yesterday`. It becomes
`borrowed_at DATETIME NOT NULL`.
*Now possible:* "how many loans in February?", which is literally what the
grant's accountability report asks for.

**3. `returned TINYINT(1)` throws away the return date.** It is the column
from the opening scene. It becomes `returned_at DATETIME NULL` — whoever has
a date returned the book, whoever does not is still open.
*Now possible:* "how long are books out, on average?" and "how many days
late was this one?".

**4. `fine FLOAT` is money in floating point.** Sums accumulate error and
the month-end close is off by a few cents — the same bug as the thousand
fifty-cent fines, now saved to disk. It becomes
`fine_in_cents INT UNSIGNED NULL`.
*Now possible:* adding up eight thousand fines and arriving at the same
number as the till.

**5. The due date is missing.** The loan period is fourteen days, but
fourteen days changes — in January it is different, and the period of a
2011 loan was the 2011 one. Calculating from the borrow date applies today's
rule to the past. It becomes `due_on DATE NOT NULL`, saved at the moment of
the loan.
*Now possible:* "was it late?", answered with the rule in force at the time.

```sql
CREATE TABLE loans (
  id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  copy_id           INT UNSIGNED NOT NULL,
  reader_id         INT UNSIGNED NOT NULL,
  borrowed_at       DATETIME     NOT NULL,
  due_on            DATE         NOT NULL,
  returned_at       DATETIME     NULL,
  fine_in_cents     INT UNSIGNED NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB;
```

There is a sixth change hidden in there, and it is the biggest of all:
`book_id` became `copy_id`. You lend the physical object, not the title — it
is the distinction from chapter @cap:o-que-vamos-construir arriving at the
database, fifteen years after Vera described the problem at the counter.

And there is still one thing this version lacks: nothing stops `reader_id`
from pointing to a reader who does not exist. That is a foreign key's job.
:::
