---
source_hash: 002b96c07acb
title: "Migrations, seeders and factories"
number: 10
slug: migrations-seeders-e-factories
part: p3
kicker: "Eleven forty on a Thursday. The terminal wrote Dropping all tables and he read the database address on the line above."
goal: >-
  Version the database schema in files that tell the story of the changes,
  alter a column without taking the application down, and have development
  data anyone on the team can reproduce.
---

:::story Dropping all tables
Dedé was going to recreate the staging database to test the collection
migration from scratch. He ran the usual command.

```text
$ php artisan migrate:fresh --seed

  Dropping all tables ................................ 214ms DONE
```

He looked at the line above the output while it scrolled. The open terminal
was the one from the morning session, the one where he had logged into the
server to check something.

```text
DB_HOST=db.casaamarela.org.br
```

He said nothing for about two seconds.

— Tainá.

— Yes.

— How much backup do we have?

She looked. Daily routine, three in the morning.

— Yesterday's, at three.

— Then we lost the morning.

— The morning and the eight hundred copies Vera catalogued yesterday
afternoon.
:::

## A migration is not a backup

A migration describes **the structure**: which tables exist, with which
columns and which constraints. It does not keep a single row of data.

That sounds obvious and is the most expensive confusion there is, because a
command with a friendly name — `migrate:fresh` — deletes everything and
recreates the empty skeleton, and finishes the way it started: with no error
at all.

:::key
Migrations recreate the **database**. The backup recreates the **system**.

They are two different guarantees, and the second is the only one that
answers for a Thursday morning.
:::

:::art caption="The command was the usual one. The terminal was production's."
src="o-comando-era-o-de-sempre-o-terminal-era-o-de-producao.png"
Minimalist editorial cartoon on a white background: a developer in his
early thirties, in a hoodie, frozen in front of his laptop, hand still on
the keyboard, while the screen shows "Dropping all tables ... DONE" with a
green check mark. Behind the laptop, a library bookcase drawn in fine lines
empties itself: the books dissolve into dots, from the top shelf down.
Beside him, an intern looks at a wall clock showing 3 o'clock, with a label
"backup". Few elements, dry humor, tech-magazine aesthetic.
:::

## The schema becomes a file

```text
$ php artisan make:migration create_books_table
```

```text
   INFO  Migration [database/migrations/
   2026_01_14_103211_create_books_table.php] created successfully.
```

The name starts with the date and time, and that is what gives the
**order**. The copies table must exist after the books table, because it
points to it — and what guarantees that is the stamp in the file name.

```php title="..._create_books_table.php" numbered
<?php

declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('books', function (Blueprint $t) {
            $t->id();
            $t->string('title', 200);
            $t->string('author', 150);
            $t->char('isbn', 13)->nullable()->unique();
            $t->string('subject', 40);
            $t->smallInteger('year')->nullable();
            $t->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('books');
    }
};
```

It is the `CREATE TABLE` from chapter @cap:duas-tabelas-conversando, written
in PHP. Side by side:

```sql
CREATE TABLE books (
  id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  title   VARCHAR(200) NOT NULL,
  author  VARCHAR(150) NOT NULL,
  isbn    CHAR(13)     NULL,
  subject VARCHAR(40)  NOT NULL,
  year    SMALLINT     NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  PRIMARY KEY (id),
  UNIQUE KEY books_isbn_unique (isbn)
) ENGINE=InnoDB;
```

`$t->id()` is the auto-increment primary key. `$t->timestamps()` creates the
two date columns the hand-written schema did not have — and they come in now
for two reasons: Eloquent maintains them on its own, and "when did this copy
enter the collection" is a question Vera is going to ask.

The foreign key fits on one line:

```php
$t->foreignId('book_id')->constrained();
```

The column name ends in `_id`, so Laravel deduces the table `books` and the
column `id`. It is convention doing the work — and when the name does not
follow the pattern, `constrained('books')` says it explicitly.

## The database's state lives in a table

```text
$ php artisan migrate
```

```text
   INFO  Running migrations.

  2026_01_14_103211_create_books_table ........... 34ms DONE
  2026_01_14_103245_create_copies_table .......... 41ms DONE
  2026_01_14_103302_create_readers_table ......... 28ms DONE
  2026_01_14_103330_create_loans_table ........... 52ms DONE
```

Laravel keeps what has already run in a table called `migrations`:

```text
mysql> SELECT * FROM migrations;
+----+------------------------------------+-------+
| id | migration                          | batch |
+----+------------------------------------+-------+
|  1 | 2026_01_14_103211_create_books_t...|     1 |
|  2 | 2026_01_14_103245_create_copies_...|     1 |
+----+------------------------------------+-------+
```

That is why running `migrate` twice does nothing the second time: it
compares the folder with the table and runs only what is missing.

The `batch` column groups what went up together, and it is what `rollback`
uses — `migrate:rollback` undoes the whole last batch, not the last
migration.

| Command | What it does |
|---|---|
| `migrate` | runs what has not run yet |
| `migrate:status` | shows what ran and what is missing |
| `migrate:rollback` | undoes the last batch |
| `migrate:fresh` | **drops all tables** and runs everything again |

Table: The first three are safe in any environment. The fourth is the one
from the story.

## An honest `down()`

Every `up()` has a `down()`, and the temptation is to fill it in out of
obligation.

```php
public function down(): void
{
    Schema::table('books', function (Blueprint $t) {
        $t->dropColumn('subject');
    });
}
```

That undoes the structure and **deletes the data in that column**. If the
migration has already run in production, the `down` is data loss dressed up
as regret.

:::pitfall
Some migrations have no honest way back: those that merge two columns into
one, those that convert formats, those that delete duplicate records.

For those, the right `down` is to refuse:

```php
public function down(): void
{
    throw new RuntimeException(
        'This migration cannot be undone: restore the backup.'
    );
}
```

It is more honest than a `down` that pretends. Whoever runs the `rollback`
gets the truth instead of a database that looks rolled back and lost half a
column.
:::

## Altering a column without taking the application down

The association asked that a book's subject stop being free text and point
to a subjects table instead.

The temptation is a migration that swaps the column. The problem is the gap:
if the application is live, there is a moment when the old code looks for
the old column in a database that has already changed.

The path that does not take anything down has two stages, and takes two
deploys.

**Expand.** A migration adds the new column, without touching the old one.
The code starts **writing to both** and reading from the new one when it is
filled. Nothing breaks, because nothing was removed.

**Contract.** After all the data has been converted and no code reads the
old column anymore, a second migration removes it.

| Stage | Migration | Code |
|---|---|---|
| 1 | creates `subject_id` | writes to both, reads the new |
| 2 | — | converts the history |
| 3 | removes `subject` | reads and writes only the new |

Table: Three steps for what looked like one. It is the price of having no
maintenance window — and it is the standard procedure in any system that
cannot stop.

:::pitfall
Never edit a migration that has already run in production.

It is recorded in the `migrations` table, so Laravel will not run it again —
and your machine, where you dropped the database and recreated it, ends up
with a schema different from production's without anything warning you.

Altering an existing table is always a **new** migration.
:::

## Seeder: the data every environment needs

Some data is not test data: the collection's list of subjects, the initial
admin user, the possible statuses. Without it the system does not work
anywhere.

```php title="database/seeders/SubjectSeeder.php" numbered
<?php

declare(strict_types=1);

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class SubjectSeeder extends Seeder
{
    public function run(): void
    {
        $subjects = [
            'literature', 'textbook', 'children',
            'reference', 'history', 'science',
        ];

        foreach ($subjects as $name) {
            DB::table('subjects')->updateOrInsert(['name' => $name]);
        }
    }
}
```

`updateOrInsert` is the difference between a seeder that can run twice and
one that duplicates everything the second time. An essential-data seeder
must be repeatable — it will run on every new environment's deploy, and more
than once in the life of someone distracted.

## Factory: fake data that looks real

To develop and test, you need a collection. Four thousand books typed by
hand is not an option.

```php title="database/factories/BookFactory.php" numbered
<?php

declare(strict_types=1);

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

class BookFactory extends Factory
{
    public function definition(): array
    {
        return [
            'title' => fake()->sentence(3),
            'author' => fake()->name(),
            'isbn' => fake()->unique()->isbn13(),
            'subject' => fake()->randomElement([
                'literature', 'textbook', 'children',
            ]),
            'year' => fake()->numberBetween(1890, 2026),
        ];
    }

    public function children(): static
    {
        return $this->state(fn (): array => [
            'subject' => 'children',
            'year' => fake()->numberBetween(2000, 2026),
        ]);
    }
}
```

```php
Book::factory()->count(200)->create();

Book::factory()->children()->count(30)->create();

Book::factory()->create(['title' => 'Dom Casmurro']);
```

`children()` is a **state**: a named variation of the default. It exists so
that a test about the seven-day rule can ask for exactly the case it needs,
without assembling the book field by field.

For the names to come out Brazilian, like the real readers', one line in
`.env`:

```text
APP_FAKER_LOCALE=pt_BR
```

:::pitfall
A factory that only produces the happy case is a slow trap.

If every generated `Book` has its ISBN, year and subject filled in, no test
will exercise the old book with no ISBN — which exists by the hundreds in
Casa Amarela's real collection, because ISBNs only came into use in the
1970s.

The factory must reflect the **variety** of real data, not its idealized
version. A good question to ask when writing it: *what is the strangest
record in production today?*
:::

## Who runs migrations in production

The question has a short technical answer and a process answer, and the
second is the one that matters.

The technical one: `php artisan migrate --force`. `--force` exists because,
in `production`, the command asks first — and in an automated step there is
nobody to answer.

The process one is a list:

1. **The command runs in the deploy**, not by hand. Hands pick the wrong
   terminal.
2. **`migrate:fresh` does not exist in production.** The way to guarantee
   that is not discipline: it is the production database user not having
   permission to drop tables.
3. **Backup first**, and verified — a backup nobody has ever restored is not
   a backup, it is a file.
4. **The production terminal looks different.** A red prompt, the
   environment name visible. It costs five minutes and solves the whole
   category of error in this chapter's story.

:::note In your career
You are going to delete something important at some point. Practically
everyone who works with a production system long enough has a story like
that.

What separates people is not having or not having the story: it is what
happened next. Speaking up right away, with the exact time of what was lost,
is the difference between a bad morning and a catastrophic afternoon —
because the team can stop whatever is writing over it and restore
precisely.

Hiding it for twenty minutes to "try to fix it alone" is what turns eight
hundred copies into eight hundred copies plus everything recorded while
nobody knew.
:::

:::tree title="Where we are now"
casa-amarela/
  database/
    migrations/
      ..._create_books_table.php
      ..._create_copies_table.php
      ..._create_readers_table.php
      ..._create_loans_table.php
    seeders/
      DatabaseSeeder.php
      SubjectSeeder.php
    factories/
      BookFactory.php
      CopyFactory.php
      ReaderFactory.php
:::

:::summary
- A migration versions structure, not data; `migrate:fresh` deletes
  everything and does not complain.
- The date stamp in the file name is what defines the execution order.
- The `migrations` table records what has already run, grouped in batches;
  `rollback` undoes a whole batch.
- A `down` that pretends to undo is worse than a `down` that refuses.
- Altering a column in a live system is done in two stages: expand and,
  later, contract.
- Never edit a migration that has run in production; the fix is a new
  migration.
- A seeder loads essential data and must be repeatable.
- A factory generates development data, and must represent the variety of
  the real database, not the happy case.
- In production, migrations run in the deploy, with a verified backup and
  without permission to drop tables.
:::

:::checkpoint
You create the schema through migrations, know what the `migrations` table's
`batch` controls, alter a column without taking the application down, and
generate a fake collection with states that represent the hard cases.
:::

:::exercise level=1
Write the migration for the `copies` table, with a unique `accession`,
`book_id` pointing to `books` and `status` with a default value.

Then say why this migration's `down()` is honest, unlike the example in the
chapter.

:::answer
```php title="..._create_copies_table.php" numbered
public function up(): void
{
    Schema::create('copies', function (Blueprint $t) {
        $t->id();
        $t->foreignId('book_id')->constrained();
        $t->unsignedInteger('accession')->unique();
        $t->string('status', 20)->default('good');
        $t->timestamps();
    });
}

public function down(): void
{
    Schema::dropIfExists('copies');
}
```

The `down()` is honest because the `up()` **created** the table. Undoing the
creation of a table is dropping it, and no data existed before it — whoever
reverts goes back exactly to the previous state.

The chapter's example was a different case: `dropColumn('subject')` on a
table that already existed. There the `down` does not restore the previous
state, because the column's values are nowhere.

The rule of thumb: **the `down` of a `create` is safe; the `down` of an
`alter` almost never is.**
:::

:::exercise level=2
Vera asked the system to store, for each copy, the date it entered the
collection — information that today is only on the label.

The table has eight hundred records and the system is live. Write the full
plan, with the migrations and what the code does at each stage.

:::answer
**Stage 1 — expand.** The column is born nullable, because the eight hundred
existing records have no value:

```php
Schema::table('copies', function (Blueprint $t) {
    $t->date('acquired_on')->nullable()->after('status');
});
```

The code starts filling the column on every new registration. The screen
shows the date when it exists and "not provided" when it does not. Nothing
breaks, and nothing was lost.

**Stage 2 — fill in the history.** Here there is a product decision, not a
technical one: where does the date of the eight hundred old ones come from?

If Vera has the information on the index cards, she types it in over the
weeks. If she does not, the alternative is an approximation — the record's
creation date — and **recording that it is approximate**, in an extra column
or an agreed-upon value. Inventing data and presenting it as exact is the
origin of a wrong report two years from now.

**Stage 3 — contract.** Only if and when the column can no longer be null:

```php
Schema::table('copies', function (Blueprint $t) {
    $t->date('acquired_on')->nullable(false)->change();
});
```

And this stage has a verifiable entry condition: `SELECT COUNT(*) FROM
copies WHERE acquired_on IS NULL` must return zero. Running the migration
before that brings the deploy down.
:::

:::exercise level=3
Rewrite this seeder, pointing out the four problems:

```php
class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        DB::table('users')->insert([
            'name' => 'Administrator',
            'email' => 'admin@admin.com',
            'password' => md5('123456'),
            'role' => 'admin',
        ]);

        Book::factory()->count(5000)->create();

        DB::table('subjects')->insert([
            ['name' => 'literature'],
            ['name' => 'textbook'],
        ]);
    }
}
```

:::answer
**One: the password.** `md5('123456')` is the defect from chapter
@cap:conversao-automatica coming back through the back door, now written by
us. Passwords are stored with `Hash::make()`, and the initial admin's
password does not live in the code: it comes from the environment, or the
user is created by a command that asks for it.

**Two: test data mixed with essential data.** The five thousand fake books
are in the same place as the subjects, which are real. The day someone runs
`db:seed` in production to create the subjects, the collection gains five
thousand invented titles.

Split into two seeders and call the fake-data one only where it makes sense:

```php
public function run(): void
{
    $this->call(SubjectSeeder::class);

    if (app()->environment('local', 'testing')) {
        $this->call(FakeCatalogSeeder::class);
    }
}
```

**Three: the `insert` is not repeatable.** Running it twice duplicates the
subjects — and the second run fails if there is a unique index, leaving the
seeder half done. `updateOrInsert` solves it.

**Four: five thousand records one by one.** Each factory `create()` is a
separate `INSERT`. Five thousand inserts take minutes, and the seeder
becomes something nobody runs. The batch form (`->make()` plus inserting in
chunks) solves it, at the cost of not firing model events — which do not
matter for fake data.

And a fifth, which was not on the list and is worth saying:
`admin@admin.com` with the password `123456` in a seeder is a default
credential. They have a habit of surviving all the way to production, and
they are the first thing any automated scan tries.
:::
