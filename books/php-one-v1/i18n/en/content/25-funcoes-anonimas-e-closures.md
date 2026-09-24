---
source_hash: 64faa6f2fbb2
title: "Anonymous functions and closures"
number: 25
slug: funcoes-anonimas-e-closures
part: p5
kicker: "The report worked until someone added a namespace to the file. After that, PHP could no longer find a function three lines above."
goal: >-
  Pass functions as values without depending on a name written in a string,
  use $this and static inside closures, build functions out of other
  functions, and combine small rules into one — the shape in which volume 2
  will hand you routes, filters and middleware.
---

:::story Three lines above
Tainá had done what the namespaces chapter told her to: she put
`namespace CasaAmarela\Reports;` at the top of the overdue script, along
with the others. She ran it to check.

```text
PHP Fatal error: Uncaught TypeError: array_filter(): Argument #2
($callback) must be a valid callback or null, function
"isOverdue" not found or invalid function name
```

"The function is right there," she said, pointing at the screen. "Three
lines above. `function isOverdue`."

Dedé read the `array_filter` line.

```php
$overdue = array_filter($loans, 'isOverdue');
```

"You passed a string."

"I passed the function's name."

"You passed a string with the name. PHP looks that string up as a global
function name. Yours is now called `CasaAmarela\Reports\isOverdue`."

"And it used to work."

"Before, the file had no address."
:::

## A function is a value

Chapter @cap:funcoes showed the essentials: a function can be stored in a
variable, passed to another and called later. `array_map` and
`array_filter` receive functions, and the `callable` in the signature says
the parameter accepts "anything that can be called".

The problem in Tainá's script lies in that expression, "anything". To PHP,
`callable` accepts several different forms:

| Form | Example | Resolved when |
|---|---|---|
| string with a function name | `'isOverdue'` | at the call, as a global name |
| string with class and method | `'Report::generate'` | at the call |
| array of object + method | `[$report, 'filter']` | at the call |
| closure | `fn($l) => ...` | it already is the function |
| first-class callable syntax | `isOverdue(...)` | where it is written |

Table: The first three are names written as strings, which PHP looks up at
call time. The last two are the function itself.

A name written in a string does not know which file it was written in. It
does not go through the `use` or the `namespace` from chapter
@cap:namespaces-e-autoload, it is not found by the editor's "rename", and
PHPStan cannot check whether the function exists.

## `(...)`: the function, not the name

Since PHP 8.1, any function or method becomes a value by writing `(...)`
after the name, in place of the arguments:

```php title="overdue.php" numbered
<?php

declare(strict_types=1);

namespace CasaAmarela\Reports;

function isOverdue(array $l): bool
{
    return $l['days'] > 14;
}

$loans = [
    ['reader' => 'Marlene', 'days' => 20],
    ['reader' => 'Iolanda', 'days' => 3],
];

$overdue = array_filter($loans, isOverdue(...));
echo count($overdue), "\n";

var_dump(isOverdue(...) instanceof \Closure);
```

```text
$ php overdue.php
1
bool(true)
```

`isOverdue(...)` does not call the function: it returns a `Closure` object
that represents it. The name is resolved **right there**, on the line where
it is written, with the file's namespace — just like a normal call.
Renaming the function renames this line; deleting the function makes
PHPStan flag this line.

With methods, the same thing:

```php
array_map($formatter->reais(...), $fines);
array_map(Money::inCents(...), $values);
```

:::key
To pass a function to another, pass the **function**: `name(...)`,
`$object->method(...)`, `Class::method(...)`, or a closure. Never its name
in a string. The string works until the day the file gets an address, and
then it breaks at run time, not at read time.
:::

## `Closure` as a type

The signature can also be stricter than `callable`:

```php
function applyTo(array $items, \Closure $operation): array
{
    return array_map($operation, $items);
}
```

`\Closure` accepts only function objects — closures and `(...)` — and
refuses strings and arrays. Whoever calls `applyTo($x, 'strtoupper')` gets a
`TypeError` at the call, with the right line, instead of an error inside
`array_map`.

The backslash before `Closure` is the one from chapter
@cap:namespaces-e-autoload: in a file with a namespace, `Closure` without a
backslash would be looked up as `CasaAmarela\Reports\Closure`, which does
not exist.

## `$this` inside the closure

A closure created inside a method sees the object it was born in:

```php title="report.php" numbered
<?php

declare(strict_types=1);

final class OverdueReport
{
    public function __construct(private int $limitInDays) {}

    public function filter(): \Closure
    {
        return fn(array $l): bool => $l['days'] > $this->limitInDays;
    }
}

$report = new OverdueReport(14);
$loans = [['days' => 20], ['days' => 3], ['days' => 15]];

echo count(array_filter($loans, $report->filter())), "\n";
```

```text
$ php report.php
2
```

`$this->limitInDays` inside the arrow function is the `$report` object. The
closure **takes the object along** — the returned function stays tied to it
after the method has ended.

Sometimes that is not what you want. A closure that does not need the
object, but carries it, keeps the object alive in memory for as long as the
closure exists. To say it does not use `$this`, there is `static`:

```php
public function filterWithoutObject(): \Closure
{
    return static fn(array $l): bool => $l['days'] > 14;
}
```

A `static` closure does not receive `$this`. If it tries to use it, it
breaks:

```text
Error: Using $this when not in object context
```

The practical rule: a closure that uses the object, normal; a closure that
does not, `static`. In volume 2, the framework keeps closures around for a
long time — routes, events, queues — and a closure that carries an object
without needing it also carries everything that object holds.

## Building functions

A function can **return** a closure. The result is a factory: you pass the
configuration once, and get back a function ready to use many times.

Márcia asked for the overdue report with different cutoffs: more than 7 days
for the friendly notice, more than 14 for collection, more than 30 to block
the reader. The first version had three almost identical functions. The
second has one that builds all three:

```php title="filters.php" numbered
<?php

declare(strict_types=1);

function lateMoreThan(int $days): \Closure
{
    return fn(array $l): bool => $l['days'] > $days;
}

$forNotice = lateMoreThan(7);
$forCollection = lateMoreThan(14);
$forBlocking = lateMoreThan(30);

$loans = [['days' => 9], ['days' => 20], ['days' => 41]];

echo count(array_filter($loans, $forNotice)), "\n";
echo count(array_filter($loans, $forCollection)), "\n";
echo count(array_filter($loans, $forBlocking)), "\n";
```

```text
$ php filters.php
3
2
1
```

Each returned closure kept its own `$days`. It is the by-value `use` from
chapter @cap:funcoes, except that the arrow function does the capturing on
its own, and each call to `lateMoreThan` creates a new capture.

:::term Closure
A function together with the variables it captured where it was created —
through `use`, through the arrow function's automatic capture, or through
the `$this` of the object it was born in. In PHP, it is an object of the
`Closure` class.

The function factory is the use of closures that shows up most in
frameworks: a configuration becomes a ready-made function.
:::

## Combining rules

The collection report needed more than one condition at the same time:
more than 14 days late, reader not exempt, book not from the reference
section. Three small functions, and one that combines them:

```php title="combine.php" numbered
<?php

declare(strict_types=1);

function allOf(\Closure ...$rules): \Closure
{
    return function (array $l) use ($rules): bool {
        foreach ($rules as $rule) {
            if (!$rule($l)) {
                return false;
            }
        }
        return true;
    };
}

$toCharge = allOf(
    fn(array $l): bool => $l['days'] > 14,
    fn(array $l): bool => !$l['exempt'],
    fn(array $l): bool => $l['collection'] !== 'reference',
);

$loans = [
    ['days' => 20, 'exempt' => false, 'collection' => 'general'],
    ['days' => 20, 'exempt' => true, 'collection' => 'general'],
    ['days' => 3, 'exempt' => false, 'collection' => 'general'],
];

echo count(array_filter($loans, $toCharge)), "\n";
```

```text
$ php combine.php
1
```

`\Closure ...$rules` is a **variadic** parameter: the three dots before the
name say the function accepts however many arguments come in that position,
and gathers them into an array — here, an array of closures. It is the same
`...` as the unpacking from chapter @cap:arrays, in the opposite direction.
`allOf` returns a new closure that runs the item through each rule and stops
at the first one that refuses.

Each rule stays small, with a name if needed, testable on its own. The
combination is another function. Adding a fourth condition is adding an
argument.

:::pitfall
Too many closures hide what the code does. A chain of six nested anonymous
functions, each returning another, is as hard to read as the eighty-line
loop it replaced.

The rule: if the closure has more than three lines, or if someone is going
to need to search for it, it gets a name — a function, or a method on a
class. The anonymous closure is for what fits on one line and only makes
sense right there.
:::

## What volume 2 will hand you this way

Three things in Laravel, which you will write in volume 2, are exactly what
this chapter showed:

```php
// a route: a path and the function that answers
Route::get('/health', fn() => ['ok' => true]);

// a collection filter: the same idea as array_filter
$overdue = $loans->filter(fn($l) => $l->isOverdue());

// an optional filter: the closure only runs if the condition holds
$query->when($city, fn($q) => $q->where('city', $city));
```

None of the three is new syntax. They are functions receiving functions —
and the framework, on the other side, storing those closures and calling
them at the right time, the way this chapter's `allOf` stores the rules and
calls them per item.

:::note In your career
In code review, `'functionName'` passed as a string is one of the few
patterns you can point out without knowing the system: it breaks with
namespaces, disappears from the editor's "rename" and escapes static
analysis. Swapping it for `functionName(...)` is a one-line change, with no
risk, that makes the code checkable. It is a good first contribution to a
project you do not know yet.
:::

:::tree title="Where we are now"
catalog/
  src/
    Reports/
      filters.php            # lateMoreThan, allOf
      OverdueReport.php      # filter() returns a closure
  scripts/
    overdue.php              # isOverdue(...) instead of the string
:::

:::summary
- `callable` accepts a string with a function name; the string is looked up
  as a global name at call time and breaks with a namespace.
- `name(...)` and `$obj->method(...)` return the function as a `Closure`,
  resolved where it is written.
- `\Closure` as a type refuses strings and arrays; the backslash is because
  of the namespace.
- A closure created in a method carries `$this`; `static fn` does not, and
  refuses `$this`.
- A function that returns a closure is a factory: the configuration goes in
  once.
- Small rules combine into a new closure. More than three lines, give it a
  name.
:::

:::checkpoint
You pass functions to others without strings holding names, write a filter
factory and a function that combines rules, and recognize, in a Laravel
route or filter, a closure doing what you already do by hand.
:::

:::exercise level=1
Say what each line does in a file with `namespace CasaAmarela;` and a
`format()` function declared in it:

```php
array_map('format', $fines);
array_map(format(...), $fines);
array_map('strtoupper', $titles);
```

:::answer
The first breaks: `'format'` is looked up as a global function, and the
function is called `CasaAmarela\format`.

The second works: `format(...)` is resolved with the file's namespace.

The third works, because of a detail: `strtoupper` is a global PHP function,
and the string finds it. Even so, `strtoupper(...)` is the form PHPStan
checks and that survives any change to the file.
:::

:::exercise level=2
Write `anyOf(\Closure ...$rules): \Closure`, `allOf`'s sibling, which
accepts the item if **any** rule accepts it. Use it to find loans more than
30 days late **or** from readers with a fine above R$ 5,00.

:::answer
```php
function anyOf(\Closure ...$rules): \Closure
{
    return function (array $l) use ($rules): bool {
        foreach ($rules as $rule) {
            if ($rule($l)) {
                return true;
            }
        }
        return false;
    };
}

$toReview = anyOf(
    lateMoreThan(30),
    fn(array $l): bool => $l['fine_in_cents'] > 500,
);
```

`lateMoreThan(30)` already is a closure — the factory returned it. The two
forms mix without conversion. And `allOf` and `anyOf` combine:
`allOf(anyOf(...), notExempt(...))`.
:::

:::exercise level=3
This class registers listeners for the "loan made" event:

```php
final class Notices
{
    private array $listeners = [];

    public function when(\Closure $listener): void
    {
        $this->listeners[] = $listener;
    }

    public function fire(array $loan): void
    {
        foreach ($this->listeners as $l) {
            $l($loan);
        }
    }
}
```

A colleague registers, inside a method of the monthly report, which loads
eight thousand loans into memory:

```php
$this->notices->when(fn($l) => error_log("loan {$l['id']}"));
```

Say what that line keeps alive, and fix it.

:::answer
The arrow function was created inside a method of the report, and so it
carries `$this` — the whole report, with the eight thousand loans. It stays
stored in `$listeners` for as long as `Notices` exists. The report, which
should have disappeared from memory when it finished, is stuck to a closure
that does not even use `$this`.

```php
$this->notices->when(
    static fn(array $l) => error_log("loan {$l['id']}"),
);
```

`static` says the closure does not need the object, and PHP does not capture
it. In a script that runs and ends, the difference is small. In a process
that stays up — the volume 2 worker — every closure that carries an object
without needing it is memory that only grows.
:::
