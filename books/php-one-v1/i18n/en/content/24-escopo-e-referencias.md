---
source_hash: e0d853d7372d
title: "Scope and references"
number: 24
slug: escopo-e-referencias
part: p5
kicker: "The day's returns list had Dom Casmurro twice. Iracema, which had come back at ten, was not on it."
goal: >-
  Know exactly what a function receives when you pass it a variable, an
  array and an object; use a reference only when it is the answer; and
  recognize the two bugs the & leaves behind.
---

:::story Dom Casmurro twice
Vera printed the day's returns list at five thirty, as she did every
afternoon, and checked it against the pile on the cart.

"Dom Casmurro shows up twice," she said. "And Iracema doesn't show up. I
took Iracema back at ten."

Tainá opened the script that generated the list. It was hers, from
Tuesday.

```php
foreach ($returned as &$r) {
    $r['title'] = mb_strtoupper($r['title']);
}

foreach ($returned as $r) {
    echo $r['title'], "\n";
}
```

"I just put them in capitals," she said. "The second loop only prints."

Dedé looked at the `&` in the first loop for a while.

"The second loop doesn't only print."

"It doesn't have an `&`."

"It doesn't. The first one left one open."
:::

## Scope, again, more carefully

Chapter @cap:funcoes showed the rule: a function does not see the
variables outside it, and the ones inside die when it ends. Whoever wants a
value from outside receives it as a parameter; whoever wants to hand one
back uses `return`.

That rule has a hidden question, which PHP answers in three different ways
depending on the value's type: **what exactly does the function receive?** A
copy of the value, or the very value that was outside?

The short answer:

| You pass | The function receives | Does changing it inside change the outside one? |
|---|---|---|
| `int`, `string`, `bool`, `float` | a copy | no |
| array | a copy | no |
| object | the same object | **yes** |
| anything with `&` | the variable itself | yes |

Table: The third row is the one that surprises people coming from the
arrays chapter. The fourth is the one this chapter asks you to use rarely.

The rest of the chapter is that table, one row at a time.

## Values and arrays: the copy

```php title="copy.php" numbered
<?php

declare(strict_types=1);

function applyDiscount(array $loan): array
{
    $loan['fine'] = intdiv($loan['fine'], 2);
    return $loan;
}

$l = ['reader' => 47, 'fine' => 720];
$discounted = applyDiscount($l);

echo $l['fine'], "\n";
echo $discounted['fine'], "\n";
```

```text
$ php copy.php
720
360
```

The function received a copy of the array, changed the copy and returned
it. The outside `$l` still has 720. It is the behavior from chapter
@cap:arrays: an array assigned to another variable — or passed to a
function — is copied.

Copying eight thousand copies on every call sounds expensive, and it is not.
PHP only really copies **at the moment someone writes** to the copy. While
the function only reads, both variables point to the same data in memory.
That is called *copy-on-write*, and it is the reason passing arrays by value
is the safe and cheap default.

## The reference: `&`

An `&` before the parameter changes the deal. The function starts receiving
the caller's **very variable**:

```php title="reference.php" numbered
<?php

declare(strict_types=1);

function applyDiscount(array &$loan): void
{
    $loan['fine'] = intdiv($loan['fine'], 2);
}

$l = ['reader' => 47, 'fine' => 720];
applyDiscount($l);

echo $l['fine'], "\n";
```

```text
$ php reference.php
360
```

There is no `return`. The function changed the outside `$l` directly.

:::term Reference
A second name for the same variable. With `&`, the function's parameter and
the caller's variable stop being two things: changing one changes the
other.

PHP uses references in very few functions of its own library — `sort` is the
best known: it sorts the array you passed, in place, and returns just
`true`.
:::

Both versions do the same math. The first says, in its signature, that it
returns a new array. The second says it changes what it received — and
whoever reads the call `applyDiscount($l);`, with nothing on the left, has to
open the function to know that `$l` changed.

:::key
A reference trades one fewer line for one more question at every call. The
default in this book — and in Laravel — is to receive, calculate and
return. `&` is for the rare case in which returning does not work.
:::

## The `&` that stays open

The bug in Vera's list has a single cause, and it explains why the rule
above is a rule.

```php title="returns.php" numbered
<?php

declare(strict_types=1);

$returned = [
    ['title' => 'O Cortiço'],
    ['title' => 'Dom Casmurro'],
    ['title' => 'Iracema'],
];

foreach ($returned as &$r) {
    $r['title'] = mb_strtoupper($r['title']);
}

foreach ($returned as $r) {
    echo $r['title'], "\n";
}
```

```text
$ php returns.php
O CORTIÇO
DOM CASMURRO
DOM CASMURRO
```

The first loop, with `&$r`, makes `$r` a second name for each item, one at a
time. When it ends, `$r` **is still** the second name of the last item —
Iracema's. The reference does not come undone when the loop ends.

The second loop uses the same name, `$r`, without `&`. On each round it
**assigns** the current item to `$r`. But `$r` is Iracema. On the first
round, Iracema becomes O Cortiço. On the second, it becomes Dom Casmurro. On
the third, the loop reads Iracema's position — which is now Dom Casmurro —
and writes it onto itself.

The list did not lose a book to a typo. It lost it because a variable kept
being an alias for another after nobody remembered it anymore.

The minimal fix is to undo the reference as soon as the loop ends:

```php
foreach ($returned as &$r) {
    $r['title'] = mb_strtoupper($r['title']);
}
unset($r);
```

`unset($r)` deletes the name `$r`, and the alias with it. Iracema's item is
not touched.

The fix this book prefers does not use `&`:

```php
$returned = array_map(
    fn(array $r): array => [
        ...$r,
        'title' => mb_strtoupper($r['title']),
    ],
    $returned,
);
```

The `array_map` from chapter @cap:funcoes returns a new array. No alias is
left behind for the next loop to trip over.

:::pitfall
The bug only shows up when the **same name** is reused afterwards, in the
same scope. That is why it passes every test that runs the first loop on
its own, and shows up the day someone adds, thirty lines below, an innocent
`foreach` with the name that was lying around.

The PHPStan from chapter @cap:tipagem-estrita does not flag it. The house
rule does: a `foreach` with `&` ends with `unset`, always, on the line right
after it closes.
:::

## Objects: the same object

Now the table row that changes everything that comes in volume 2.

```php title="object.php" numbered
<?php

declare(strict_types=1);

final class Copy
{
    public function __construct(
        public readonly int $accession,
        public string $status = 'good',
    ) {}
}

function markOnLoan(Copy $c): void
{
    $c->status = 'on_loan';
}

$copy = new Copy(2117);
markOnLoan($copy);

echo $copy->status, "\n";
```

```text
$ php object.php
on_loan
```

There is no `&` anywhere, and the outside `$copy` changed.

An object is not copied when it is passed to a function, nor when it is
assigned to another variable. What the variable holds is an **identifier**
for the object — a number that tells PHP where it is. Passing `$copy` to the
function passes a copy of that number, and the copy points to the same
object.

```php
$a = new Copy(2117);
$b = $a;
$b->status = 'in_repair';

echo $a->status;   // in_repair
var_dump($a === $b);   // bool(true)
```

`$a === $b` between objects asks whether it is **the same** object — the
comparison from chapter @cap:classes-e-objetos. Here it is: there is one
object, with two names.

:::key
An array passed along is copied; an object passed along is shared. A
function that receives an object and changes one of its properties changes
the caller's object, with no `&` and no `return`.

In volume 2, this is everyday life: Laravel hands your code the request
object, the database model, the authenticated user. All of them are
objects, and all of them are the same object the framework and the other
parts of your code are holding.
:::

It is also the reason for the `readonly` in chapter @cap:encapsulamento. A
shared object that nobody can change from outside — like the `Money` from
chapter @cap:enums-datas-e-valores — does not have this problem: any
"change" returns a new object.

## `clone`, and the copy that only goes one level deep

When you really do need an independent copy of an object, there is
`clone`:

```php title="clone.php" numbered
<?php

declare(strict_types=1);

final class Reader
{
    public function __construct(public string $name) {}
}

final class Loan
{
    public function __construct(
        public Reader $reader,
        public int $days,
    ) {}
}

$original = new Loan(new Reader('Marlene'), 14);
$copy = clone $original;

$copy->days = 7;
$copy->reader->name = 'Iolanda';

echo $original->days, ' ', $original->reader->name, "\n";
```

```text
$ php clone.php
14 Iolanda
```

`days` was copied: changing it on the copy did not change the original.
`reader` was not: `clone` copies the properties, and the `reader` property
holds an object's identifier. The copy received the same identifier — and,
with it, the same reader.

To go one level down, the class declares what `clone` should do:

```php
public function __clone(): void
{
    $this->reader = clone $this->reader;
}
```

`__clone` runs on the copy, right after it is made. In practice, this book
hardly uses `clone`: immutable value objects, which return another object on
every change, make the question unnecessary.

## `static` and `global`: the scope that lasts too long

There are two ways for a variable to survive the end of a function, and
chapter @cap:encapsulamento already warned about one of them.

`global` pulls a variable from the file into the function:

```php
function accumulate(int $value): void
{
    global $total;
    $total += $value;
}
```

The function now depends on a name that does not appear in its signature,
and any other file can change it. It is the `$grand_total` from chapter
@cap:funcoes, "fixed" the wrong way.

`static` inside a function keeps the value between one call and the next:

```php title="cache.php" numbered
<?php

declare(strict_types=1);

function dailyFine(): int
{
    static $value = null;

    if ($value === null) {
        echo "(reading config)\n";
        $value = 80;
    }

    return $value;
}

echo dailyFine(), "\n";
echo dailyFine(), "\n";
```

```text
$ php cache.php
(reading config)
80
80
```

The second call did not read the configuration. Useful for a value that is
expensive to calculate and never changes while the program runs — and
dangerous for anything that changes, because there is no way to tell the
function that the stored value has gone stale.

:::note
In the PHP that serves the browser, every request starts from zero:
`static` and `global` die at its end. In volume 2 there are processes that
**do not** end — the queue worker, for example — and there a `static` stored
during the first job is still there on the thousandth. What looks harmless
in a request becomes one person's data showing up for another.
:::

:::note In your career
"PHP passes objects by reference" is a sentence you will hear in interviews
and read in tutorials. It is almost right, and the almost matters: PHP
passes the object's **identifier** by value. The difference shows up in only
one case — reassigning the parameter inside the function (`$c = new Copy(9)`)
does not change the outside variable; with `&`, it would.

Being able to explain that case in one sentence is the kind of detail that
separates someone who memorized from someone who understood.
:::

:::tree title="Where we are now"
catalog/
  src/
    Catalog/Copy.php         # status changes through a method, not from outside
    Loans/Money.php          # immutable: nothing to clone
  scripts/
    returns.php              # array_map instead of the foreach with &
:::

:::summary
- Scalars and arrays are passed by copy; objects, by identifier — the
  function receives the same object.
- Copying an array is cheap: PHP only really copies when someone writes.
- `&` makes the parameter a second name for the outside variable. Use it
  rarely.
- A `foreach` with `&` leaves the alias alive after the loop; `unset` on the
  next line, or `array_map` instead.
- `clone` copies one level; objects inside stay shared. `__clone` goes one
  level further.
- `global` and `static` make the variable outlive the function. In a process
  that does not end, they outlive it by far too much.
:::

:::checkpoint
You predict, by looking at the signature, whether a function can change
what it received; reproduce and fix the `foreach` with `&` that duplicates
the last item; and explain why an object passed to a function comes back
changed without `&`.
:::

:::exercise level=1
Say what each snippet prints:

```php
function a(int $x): void { $x = 10; }
$n = 1; a($n); echo $n;

function b(array $l): void { $l[] = 'new'; }
$list = []; b($list); echo count($list);

function c(Copy $c): void { $c->status = 'in_repair'; }
$copy = new Copy(1); c($copy); echo $copy->status;
```

:::answer
`1`, `0` and `in_repair`.

The integer and the array are copied: functions `a` and `b` changed the
copies. The object is not copied: `c` changed the same copy that `$copy`
identifies.
:::

:::exercise level=2
This snippet from the import adds up each reader's fine. Say what it prints,
why, and rewrite it without `&`.

```php
$readers = [
    ['name' => 'A', 'fine' => 100],
    ['name' => 'B', 'fine' => 200],
];

foreach ($readers as &$r) {
    $r['fine'] += 50;
}

$total = 0;
foreach ($readers as $r) {
    $total += $r['fine'];
}
echo $total;
```

:::answer
It prints `300`, and the right answer would be `400`.

The first loop adds 50 to each reader — A ends up with 150, B with 250 — and
leaves `$r` as an alias for the last item, B. The second loop assigns each
item to `$r`. On the first round, B becomes a copy of A: fine 150. On the
second, the loop reads B, which is now worth 150. The total comes out as
`150 + 150`, and the array ends with both readers with a fine of 150. B's
fine, 250, disappeared without any error.

```php
$readers = array_map(
    fn(array $r): array => [...$r, 'fine' => $r['fine'] + 50],
    $readers,
);
$total = array_sum(array_column($readers, 'fine'));
```

`array_sum(array_column(...))` adds up everyone's `fine` column: 400. No
alias, no loop order to worry about.
:::

:::exercise level=3
A colleague wrote, in the loan service:

```php
function renew(Loan $l, int $days): Loan
{
    $new = $l;
    $new->days += $days;
    return $new;
}
```

He says the function "doesn't change the original, because it returns a new
one". Explain what happens, and write two correct versions — one with
`clone` and one immutable.

:::answer
`$new = $l` does not create another object: it creates another name for the
same one. The function changes the loan it received **and** returns that
same loan. Whoever called it and kept the original to compare "before and
after" sees the two as identical.

With `clone`:

```php
function renew(Loan $l, int $days): Loan
{
    $new = clone $l;
    $new->days += $days;
    return $new;
}
```

Immutable, with the class designed for it:

```php
final class Loan
{
    public function __construct(
        public readonly Reader $reader,
        public readonly int $days,
    ) {}

    public function renewedBy(int $days): self
    {
        return new self($this->reader, $this->days + $days);
    }
}
```

The second makes the bug impossible: there is no way to change a
`readonly`, and the method's name says that another loan comes back.
:::
