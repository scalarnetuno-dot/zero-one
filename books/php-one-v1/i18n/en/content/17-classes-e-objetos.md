---
source_hash: b1e0df09c391
title: "Classes and objects"
number: 17
slug: classes-e-objetos
part: p3
kicker: "The report showed a copy of no book at all. The data was right in the database — it was the array that had lost the key."
goal: >-
  Swap the associative array for a named type when the format is known:
  declare a class, create objects with a promoted constructor, use typed
  properties, compare objects and recognize when an object is not worth it.
---

:::story A copy of no book at all
Vera printed the report of copies in repair to take to the association's
meeting. Eleven lines. On the sixth, accession 2117 appeared with a blank
title.

"What book is this?"

"That's..." Dedé scrolled the screen, "...none."

"What do you mean, none?"

In the database, 2117 was a hardcover *Vidas Secas*, with the right
`book_id` and the foreign key in place. The problem was thirty lines up, in
the PHP. The report built an index of titles with a separate query, and that
query only fetched literature books.

*Vidas Secas* had been classified as a textbook since 2011.

"And the system didn't complain?"

"It did." Dedé opened the log and read it out loud. "*Warning: Undefined
array key 431.*"

"Did that show up on my screen?"

"That showed up in a file nobody opens."
:::

## The array accepts any key

An associative array has no format. It accepts whatever you ask for, and
whatever you ask for wrong.

```php title="keys.php" numbered
<?php

$book = ['id' => 12, 'title' => 'Dom Casmurro', 'year' => 1899];

echo '[', $book['tilte'], "]\n";
```

```text
Warning: Undefined array key "tilte" in /app/keys.php on line 5
[]
```

A warning, a null value and the program carries on. If that `echo` is inside
an eleven-line report, the result is a blank line in the middle of ten right
ones.

Writing is worse, because it does not even warn you:

```php
$book['price'] = 39.90;
$book['title_'] = 'Dom Casmurro';
```

Silence in both cases. The array now has five keys, two of them made up, and
nothing in the program knows that is a problem.

:::key
The array is the right structure when the format is **unknown or
variable**: the rows that came back from a query, the filters the user
ticked, a list of any size.

It turns bad when the format is **known and repeated** — when the same four
keys travel through seven functions, and each function has to trust that
the other six wrote the right name.
:::

## A class is a format with a name

```php title="Book.php" numbered
<?php

class Book
{
    public string $title;
    public int $year;
}
```

Three new words, and none of them is complicated.

`class` declares a format. `Book` is its name. Inside the braces are the
**properties**: the fields every book has, each with the type it accepts.

Creating one is `new`:

```php title="catalog.php" numbered
<?php

require 'Book.php';

$book = new Book();
$book->title = 'Dom Casmurro';
$book->year = 1899;

echo $book->title, "\n";
```

```text
Dom Casmurro
```

The arrow `->` is how you reach a property. It is not a dot: in PHP the dot
joins text, and that is the first thing the memory of someone coming from
another language insists on getting wrong.

:::term Class and object
The **class** is the blank catalog card: it says which fields exist and what
fits in each. The **object** is a filled-in card.

One class, many objects. The template stores no data at all; each object
stores its own.
:::

Now repeat the mistake from the previous section:

```php
echo '[', $book->tilte, "]\n";
```

```text
Warning: Undefined property: Book::$tilte
in /app/catalog.php on line 10
[]
```

It is still a warning — but notice the difference in the message: it gives
the name of the class. It is no longer "some key in some array": it is
`Book::$tilte`, and the `Book` class is in a single file, with its
properties listed in five lines.

And writing changed its behavior:

```php
$book->price = 39.90;
```

```text
Deprecated: Creation of dynamic property Book::$price is deprecated
in /app/catalog.php on line 11
```

PHP warns you that creating a property outside the list is a feature on its
way out. The array never warned you about anything.

## The object born halfway

There is a problem in the code above, and it shows up when someone forgets a
line:

```php title="catalog.php" numbered
<?php

require 'Book.php';

$book = new Book();
$book->title = 'Dom Casmurro';

echo $book->year;
```

```text
Fatal error: Uncaught Error: Typed property Book::$year must not be
accessed before initialization in /app/catalog.php:8
```

A typed property has no default value. It is not `null`, it is not `0`: it
**does not exist yet**, and PHP would rather stop than invent a value.

That is good, and it is not enough. The error happens at reading time, which
may be thirty lines — or three screens — after the place where the object
was assembled wrong.

The right place to demand the data is the object's birth.

## The constructor

```php title="Book.php" numbered
<?php

class Book
{
    public string $title;
    public int $year;

    public function __construct(string $title, int $year)
    {
        $this->title = $title;
        $this->year = $year;
    }
}
```

`__construct` is a method with a reserved name: PHP calls it on its own,
whenever someone writes `new Book(...)`, passing the arguments along.

`$this` is the object the method is running on at that moment. Inside a
book's constructor, `$this` is that book — and `$this->title` is its
property, not the parameter.

```php
$book = new Book('Dom Casmurro', 1899);
```

Now the object is born whole or not at all:

```php
$book = new Book('Dom Casmurro');
```

```text
Fatal error: Uncaught ArgumentCountError: Too few arguments
to function Book::__construct(), 1 passed and exactly 2 expected
```

And it is born with the right types:

```php
$book = new Book('Dom Casmurro', 'eighteen ninety-nine');
```

```text
Fatal error: Uncaught TypeError: Book::__construct():
Argument #2 ($year) must be of type int, string given
```

:::pitfall
`'eighteen ninety-nine'` was refused. `'1899'` would not be: a text that
*is* an integer gets through the door and arrives on the other side
converted, as `int(1899)`.

That is PHP's automatic conversion working where you did not ask it to. It
will not save you from receiving `'1899'` from a form — it will hand you the
right integer, and that is precisely why you will not notice when it hands
you the wrong one.
:::

## The constructor in one line

Writing each property's name three times — in the declaration, in the
parameter and in the assignment — is typist's work. PHP 8 solves it:

```php title="Book.php" numbered
<?php

class Book
{
    public function __construct(
        public string $title,
        public int $year,
    ) {}
}
```

This does **exactly** what the previous version did. Writing `public`
before the parameter tells PHP: declare this property and store this value
in it. The three lines of the body disappear because there is nothing left
to do.

The comma after the last parameter is allowed and recommended: adding a
field tomorrow becomes one new line instead of two changed lines.

:::term Property promotion
*Constructor property promotion*, by its official name. It has been in PHP
since version 8.0 and it is the normal way of writing a data class today.

You will find a lot of code with the long version — it is not wrong, it is
just older. Both produce the same object.
:::

## A copy without a book stops being possible

That was Vera's question. In the System, a copy is an array, and an array
with the `book_id` key missing is a perfectly normal array.

With a class, the problem moves:

```php title="Copy.php" numbered
<?php

class Copy
{
    public function __construct(
        public int $accession,
        public Book $book,
        public string $status = 'good',
    ) {}
}
```

Two things to notice.

The first: the type of `$book` is `Book`. A class is as valid a type as
`int` or `string`, and PHP enforces it the same way.

The second: `$status` has `= 'good'`, a default value. Whoever does not
provide it gets `'good'` — which is the status a copy enters the catalog
with. Defaults are for things with an obvious answer; `$accession` and
`$book` do not have one.

```php
$copy = new Copy(2117);
```

```text
Fatal error: Uncaught ArgumentCountError: Too few arguments to
function Copy::__construct(), 1 passed and exactly 2 expected
```

It is no longer a matter of team discipline. It is a matter of the program
running.

## From the database to the object

The queries still return arrays — that is what PDO does, and it is right: at
that point the format is still the database's.

The translation happens in a function, in one place:

```php title="catalog.php" numbered
<?php

require 'Book.php';
require 'Copy.php';

function bookFromRow(array $row): Book
{
    return new Book($row['title'], (int) $row['year']);
}
```

```php title="list.php" numbered
<?php

require 'connection.php';
require 'catalog.php';

$rows = $pdo->query(
    'SELECT title, year FROM books ORDER BY title'
)->fetchAll();

$books = [];

foreach ($rows as $row) {
    $books[] = bookFromRow($row);
}

echo $books[0]->title, "\n";
```

The `(int)` in the year's conversion is not decoration: MySQL returns
numbers as text, and `'1899'` would become an `int` at the constructor's
door anyway. Writing the conversion makes the intent visible and makes the
program behave the same on the day typing becomes strict.

:::key
The border is always the same: **array until the translation, object after
it**.

A function that receives `array $row` and returns an object is the only
place in the program that needs to know what the columns are called. When a
column is renamed, that is where you go.
:::

## Comparing objects

Two signs, two different questions.

```php title="compare.php" numbered
<?php

require 'Book.php';

$a = new Book('Dom Casmurro', 1899);
$b = new Book('Dom Casmurro', 1899);
$c = $a;

var_dump($a == $b);
var_dump($a === $b);
var_dump($a === $c);
```

```text
bool(true)
bool(false)
bool(true)
```

- `==` asks: **are they equal?** Same class and properties equal one by one.
- `===` asks: **are they the same one?** The same object, not a copy with
  the same content.

`$c = $a` copied nothing. The two variables point to the same object, and
that is why `$a === $c` is true.

:::pitfall
For things the database identifies by `id`, neither of the two questions is
the one you want. Two `Reader` objects loaded at different moments can have
the same `id` and different names — because someone corrected the record in
between.

`==` would say they are different. So would `===`. And they are the same
person.

When identity comes from an `id`, compare the `id`.
:::

## `__toString`, and the shortcut that charges later

An object does not turn into text on its own:

```php
echo $book;
```

```text
Fatal error: Uncaught Error: Object of class Book could not be
converted to string
```

You can teach it:

```php title="Book.php" numbered
<?php

class Book
{
    public function __construct(
        public string $title,
        public int $year,
    ) {}

    public function __toString(): string
    {
        return "{$this->title} ({$this->year})";
    }
}
```

```text
$ php catalog.php
Dom Casmurro (1899)
```

`__toString` is useful for logs and error messages. It is one of several
methods with two underscores in front that PHP calls on its own in specific
situations.

And this is where it is best to stop.

:::pitfall
One of those methods, `__get`, intercepts the reading of any property that
does not exist and lets you decide what to return. With it, an object goes
back to accepting `$book->tilte` without complaint.

In other words: it undoes, in four lines, exactly what this whole chapter
set out to do. An error PHP used to point out with a name and a line becomes
a blank screen again.

That does not mean `__get` is never useful. It means it is the answer to a
very specific problem, and "I don't want to declare the properties" is not
that problem.
:::

## When the object is not worth it

Not every structure deserves a class, and the rule is the same as at the
start of the chapter, in reverse.

**A format you do not control.** The JSON from an integration, a CSV whose
columns change with each export, the filters that came from a form. There
the array is honest: the format really is variable, and pretending it is not
just pushes the surprise somewhere else.

**A class that refuses nothing.** If the class has six public properties, no
rules, no calculations and no interesting types, it is an array with more
lines and a catalog card. The gain shows up when the type **prevents**
something — like the `Copy` that is not born without a `Book`.

**A one-off script.** The program that runs for one afternoon to check an
import does not need modeling. It needs to finish.

:::note In your career
"Let's create a class for this" is a proposal that tends to be accepted
without discussion and carried out without gain — and, three months later,
the project has forty classes that only store and return.

When you propose the swap, bring along the concrete failure it prevents. "A
`Copy` class would have prevented Friday's blank report" is an argument.
"It's more organized" is a preference, and preferences do not survive the
first tight week.

The same goes the other way: when someone proposes it, ask which real error
goes away. If the answer takes a while, the class probably does not have a
job to do yet.
:::

:::tree title="Where we are now"
catalog/
  composer.json
  composer.lock
  vendor/
  .gitignore
  Book.php        # class, with __toString
  Copy.php        # class, requires a Book
  catalog.php     # turns a database row into an object
  connection.php
  fine.php
  list.php
  search.php
  register.php
  lend.php
  return.php
  receipt.php
:::

:::summary
- An array has no format: it accepts a wrong key on reading with a warning
  and on writing in silence.
- `class` declares a format with a name; `new` creates an object; `->`
  reaches a property.
- A typed property has no default value — reading it before assigning is a
  fatal error, and that works in your favor.
- `__construct` is called by `new`; `$this` is the object that is running.
- Property promotion writes the constructor and the properties in a single
  declaration.
- A class is a type: `Copy` can require a `Book`, and PHP enforces it.
- Array until the translation, object after it — and the translation lives
  in one place.
- `==` compares content, `===` compares identity; for an entity with an
  `id`, compare the `id`.
- A class with no rules at all is an array with more lines.
:::

:::checkpoint
You declare a class with a promoted constructor, create objects from
database rows, know why a `Copy` cannot be born without a `Book`, tell `==`
from `===` between objects and can defend — or refuse — swapping an array
for a class with a concrete example.
:::

:::exercise level=1
Write the `Reader` class with `name` (text), `document` (text) and
`registeredAt` (text in `Y-m-d` format), using a promoted constructor.

Then answer: why is `document` a `string` and not an `int`, if it is a
sequence of eleven digits?

:::answer
```php title="Reader.php" numbered
<?php

class Reader
{
    public function __construct(
        public string $name,
        public string $document,
        public string $registeredAt,
    ) {}
}
```

`document` is text because **it is not a number**: it is an identifier made
of digits. Two quick tests tell one thing from the other.

The first: does it make sense to add two documents together? No.

The second, more practical: the Brazilian taxpayer ID `012.345.678-90`
stored as an integer becomes `12345678 90` without the leading zero, because
a leading zero does not exist in a number. The catalog already had that
problem with the `accession` until someone noticed that the old accession
numbers started with zero.
:::

:::exercise level=2
Take `list.php` from the translation section and add the building of `Copy`
objects from a query with `JOIN`, using the `Copy` class that requires a
`Book`.

The query:

```sql
SELECT c.accession, c.status, b.title, b.year
FROM copies c
JOIN books b ON b.id = c.book_id
ORDER BY b.title
```

Then print each copy on one line, using the `Book`'s `__toString`.

:::answer
```php title="catalog.php" numbered
<?php

require 'Book.php';
require 'Copy.php';

function copyFromRow(array $row): Copy
{
    return new Copy(
        (int) $row['accession'],
        new Book($row['title'], (int) $row['year']),
        $row['status'],
    );
}
```

```php title="list.php" numbered
<?php

require 'connection.php';
require 'catalog.php';

$sql = 'SELECT c.accession, c.status, b.title, b.year
        FROM copies c
        JOIN books b ON b.id = c.book_id
        ORDER BY b.title';

foreach ($pdo->query($sql) as $row) {
    $copy = copyFromRow($row);
    echo $copy->accession, ' — ', $copy->book, "\n";
}
```

```text
2117 — Vidas Secas (1938)
 843 — Dom Casmurro (1899)
```

The `echo $copy->book` works because `Book` has `__toString`.

And notice what disappeared: there is no longer an index of titles built on
the side, which is where the blank report was born. The `JOIN` brings the
title along with the copy, and the constructor does not let one through
without the other.
:::

:::exercise level=3
This code runs without error and prints something unexpected. Say what it
prints and why, before running it.

```php title="cart.php" numbered
<?php

require 'Book.php';

$original = new Book('Dom Casmurro', 1899);
$copy = $original;

$copy->year = 1900;

echo $original->year, "\n";
var_dump($original == $copy);
```

Then look up what the word `clone` does and explain why it would not solve
the case in which `Book` held an object inside it either.

:::answer
It prints `1900` and `bool(true)`.

`$copy = $original` did not copy the object. Objects are assigned by
handle: both variables point to the same object, and changing the year
through one end changes it through both. That is why `==` answers `true` —
it is comparing the object with itself.

`clone $original` creates a new object with the same properties. It solves
this case: `$copy = clone $original` would make the `echo` print `1899`.

Where it does not solve things: the copy is **shallow**. If `Book` held a
`Publisher` object inside, the copy would get the same `Publisher` — not a
copy of it. Changing the publisher's name through the copy would change it
through the original, and you would have the same problem one level down,
now harder to see.

The way out that avoids the whole discussion is an object that does not
change after it is created. Without changes, copy and original have no way
of diverging.
:::
