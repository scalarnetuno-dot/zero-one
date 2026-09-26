---
source_hash: 0772deb72155
title: "Arrays"
number: 8
slug: arrays
part: p1
kicker: "PHP's most used structure is also its most misused — and one line of it once took down the app of twelve hundred people."
goal: >-
  Store several things in a single variable, choose between list and map,
  understand why the two are the same type in PHP, and know when that
  sameness becomes a bug.
---

So far, each variable has held one thing: a title, a number of days, a
value in cents. The Casa Amarela catalog has eight thousand copies, and
`$copy1`, `$copy2`, `$copy3` stops being funny by the fourth.

## Several things in a single variable

```php title="list.php" numbered
<?php

$accessions = [812, 907, 344];

echo $accessions[0], "\n";
echo $accessions[2], "\n";
echo count($accessions), "\n";
```

```text
812
344
3
```

The square brackets create an **array**. The values are separated by
commas, and each one gets a position, counted from **zero** — which is why
`$accessions[0]` is the first and `$accessions[2]` is the third.

`count()` answers how many items there are. Notice that `count($accessions)`
is `3` and the last position is `2`: that off-by-one difference is the
source of an impressive number of bugs, and the way to never get it wrong
again is to remember that positions start at zero and the item count does
not.

To add at the end, empty brackets:

```php title="append.php" numbered
<?php

$accessions = [812, 907];

$accessions[] = 344;
$accessions[] = 501;

print_r($accessions);
```

```text
Array
(
    [0] => 812
    [1] => 907
    [2] => 344
    [3] => 501
)
```

`$accessions[] = 344` means "put it in the next free position". You do not
need to know which one it is.

And a new tool appeared: `print_r` prints the structure of an array in a
readable way. `var_dump` works too and shows the types, which is more
information than is usually useful when you just want to check the
contents.

## Keys with names

The numeric position works when order is what matters. When what matters
is **what each value means**, the key becomes text:

```php title="map.php" numbered
<?php

$copy = [
    'accession' => 812,
    'title' => 'O Cortiço',
    'status' => 'available',
];

echo $copy['title'], "\n";

$copy['status'] = 'on_loan';

echo $copy['status'], "\n";
```

```text
O Cortiço
on_loan
```

The arrow `=>` links the key to the value. Reading and changing use the
same bracket syntax, with the key's name in place of the number.

That solves the problem Vera had with the eighteen-field form: instead of
eighteen loose variables, a whole copy fits in one variable that reads
aloud.

:::key
Use a **numeric key** when the items are interchangeable and order matters
— a queue, a list of results, a history.

Use a **text key** when each position has a meaning of its own — a record,
a configuration, a set of options.

The deciding question: does it make sense to ask "which is the third one"?
If it does, it is a list. If it does not, it is a map.
:::

## The two are the same thing

In almost every language there are two separate structures. Python has
`list` and `dict`. JavaScript has `Array` and `Object`. Java has `List` and
`Map`.

PHP has `array`. Just one, for both uses.

```php title="two_uses.php" numbered
<?php

$accessions = [812, 907, 344];

var_dump($accessions);
```

```text
array(3) {
  [0]=> int(812)
  [1]=> int(907)
  [2]=> int(344)
}
```

Notice the keys `0`, `1`, `2`. They are there — you just did not write
them. A "list" in PHP is a map whose keys happen to be the integers
starting at zero, in order, with no gaps.

:::term Array in PHP
An **ordered map**: key→value pairs that keep their insertion order. The
key is an `int` or a `string`. There is no separate list type — what we call
a list is a convention about the keys.
:::

:::history
The decision dates from 1997, when PHP 3 was being written by Andi Gutmans
and Zeev Suraski. A single structure simplified the interpreter and the
lives of the people writing code, at a time when most of the world's PHP
processed forms — where everything arrives as name→value pairs.

It worked for twenty years. What nobody foresaw was that this same
structure would be sent to other programs in a format that **does**
distinguish the two cases.
:::

Since PHP 8.1 there is a function that tells you which of the two you are
holding:

```text
$ php -r 'var_dump(array_is_list([812, 907]));'
bool(true)
$ php -r 'var_dump(array_is_list([0 => 812, 2 => 907]));'
bool(false)
```

The second one has keys `0` and `2`. The `1` is missing. To PHP, it is
still an array like any other — and that is where the story begins.

## We didn't change anything

:::story We didn't change anything
Monday, 8:50. Tainá opened the Casa Amarela chat and there were fourteen
messages from Vera, all from before eight in the morning.

The readers' app no longer showed the catalog. Empty screen, no error, no
message, nothing.

"We didn't change anything over the weekend," said Dedé.

Technically true. On Friday he had removed the copies in repair from the
list. One line. The server kept responding normally, the data kept
arriving, the fields kept their right names.

Except that on Friday what came out was this:

```text
[{"accession":812},{"accession":907}]
```

And on Monday it was this:

```text
{"0":{"accession":812},"2":{"accession":344}}
```

The app expected a list. It received something else. It did not break — it
just found nothing to iterate over, and drew the empty screen very
competently.

Márcia found out at 9:15. Her first question was not about the bug.

"How long has it been like this?"

"Since Friday, 6 p.m."

"So that's two and a half days. Put it in the minutes."
:::

:::term JSON
The format in which two programs exchange data over the network. It is
text, and it has two structures: **list**, between `[ ]`, and **object**,
between `{ }` with name→value pairs. The two things PHP decided to call an
array are, in JSON, different types — and whoever receives them treats each
one differently.
:::

PHP converts an array to JSON with `json_encode`, and the decision to
become a list or an object is made on its own, by a rigid criterion:

```php title="the_rule.php" numbered
<?php

echo json_encode([812, 907, 344]), "\n";
echo json_encode([0 => 812, 1 => 907]), "\n";
echo json_encode([0 => 812, 2 => 344]), "\n";
echo json_encode(['accession' => 812]), "\n";
```

```text
[812,907,344]
[812,907]
{"0":812,"2":344}
{"accession":812}
```

It becomes a JSON list **only** if the keys are exactly `0, 1, 2, …, n-1`,
in that order, with no gaps. Anything else becomes an object — it is the
same question `array_is_list` answers.

## The gap `unset` leaves behind

What Dedé wrote on Friday was this:

```php title="fridays_filter.php" numbered
<?php

$copies = [
    ['accession' => 812, 'status' => 'available'],
    ['accession' => 907, 'status' => 'in_repair'],
    ['accession' => 344, 'status' => 'available'],
];

unset($copies[1]);

echo json_encode($copies), "\n";
```

```text
{"0":{"accession":812,"status":"available"},
 "2":{"accession":344,"status":"available"}}
```

`unset()` removes an item from the array. What it does **not** do is
renumber the ones that are left: position `1` simply stopped existing, and
the item that was at `2` is still at `2`.

The array now has keys `0` and `2`. `json_encode` looked, did not find the
sequence and produced an object.

Neither side got it wrong. PHP did exactly what it has documented doing for
twenty years; the app treated an object as an object. The bug happened
**at the boundary** — and the boundary is where the problems nobody can
reproduce live, because each side, tested on its own, is right.

The fix is one word:

```php title="the_fix.php" numbered
<?php

$copies = [
    ['accession' => 812, 'status' => 'available'],
    ['accession' => 907, 'status' => 'in_repair'],
    ['accession' => 344, 'status' => 'available'],
];

unset($copies[1]);

$copies = array_values($copies);

echo json_encode($copies), "\n";
```

```text
[{"accession":812,"status":"available"},
 {"accession":344,"status":"available"}]
```

`array_values()` throws the keys away and renumbers from zero. The array is
a list again, and the JSON is a list again.

:::key
**Every time an array is going to leave PHP as a list — for JSON, for
another program, for a screen that expects order — make sure of the keys
with `array_values()`.**

The rule looks excessive until you remember that the line that breaks the
contract is rarely the one you are writing now. It is the one someone else
will add along the way, in March, with every reason in the world.
:::

:::note In your career
"We didn't change anything" is almost always false and almost never a lie.
The person changed something that, according to their mental model, could
not have caused that.

The skill that develops over time is not remembering every possible side
effect — it is **narrowing the search fast**. In this case: did the app
change? No. Did the server change? Yes, on Friday. What changed on Friday?
One line. What does that line touch? The shape of the response.

Four questions, two minutes. It is the difference between a half-hour
investigation and an entire morning, and it can be trained.
:::

## Asking whether it is there

Three similar functions that answer different questions:

```php title="exists.php" numbered
<?php

$copy = [
    'accession' => 812,
    'note' => null,
];

var_dump(isset($copy['accession']));
var_dump(isset($copy['note']));
var_dump(array_key_exists('note', $copy));
var_dump(in_array(812, $copy));
```

```text
bool(true)
bool(false)
bool(true)
bool(true)
```

The second and third lines are the point. The `note` key **exists** in the
array — it just has the value `null`. `isset` answers `false`, because its
question is "does it exist and is it not null?". `array_key_exists` answers
`true`, because its question is only "does it exist?".

It is the same distinction between absence and null from chapter
@cap:variaveis-e-tipos, now with a practical consequence: if your code
decides whether to save a note based on `isset`, it will never save a
deliberately blank note.

`in_array` searches by **value**, not by key. There is also `array_search`,
which returns the key where it found it.

:::pitfall
`in_array` without the third argument compares with `==`:

```text
$ php -r 'var_dump(in_array(0, ["a", "b"]));'
bool(false)
$ php -r 'var_dump(in_array("1", [1, 2]));'
bool(true)
```

The second case is the one that bites: the text `"1"` was found in a list
of numbers. Always use `in_array($x, $list, true)`, with the third
argument, which switches to strict comparison.
:::

## Copying an array really copies it

```php title="copy.php" numbered
<?php

$a = ['accession' => 812];
$b = $a;

$b['accession'] = 907;

echo $a['accession'], "\n";
echo $b['accession'], "\n";
```

```text
812
907
```

Assigning an array to another variable **copies** its contents. Changing
the copy does not change the original.

That looks obvious and it is not: in Python and in JavaScript, the same
sequence would leave both variables pointing to the same list, and the
`812` would have become `907` in both. People arriving from one of those
languages usually discover the difference the hard way.

PHP is thrifty on the inside — it only really duplicates when one of the two
sides changes — so the cost is lower than it looks. But it exists, and for
an array of a hundred thousand items it shows.

## Arrays inside arrays

The value stored in an array can be another array, and that is how you
represent a collection of records:

```php title="catalog.php" numbered
<?php

$catalog = [
    ['accession' => 812, 'title' => 'O Cortiço'],
    ['accession' => 907, 'title' => 'Vidas Secas'],
];

echo $catalog[0]['title'], "\n";
echo count($catalog), "\n";
```

```text
O Cortiço
2
```

Two brackets in a row: the first picks the record, the second picks the
field. It is the structure in which most data enters and leaves a PHP
system.

It works well at two levels, tolerates three, and after that it becomes
something else. This line exists in the System:

```php
$data['book'][3]['copies'][0]['loan']['reader']['name']
```

It works. And it has four problems no tool can point out: the editor
suggests nothing, a typo at any level returns `null` with a warning, there
is no way to know which keys exist without running the program, and the
whole structure is a contract that is not written down anywhere.

:::key
When the array has three or more levels and the format is **known and
fixed**, it is asking to become something else. Remember the symptom; the
remedy appears when the language has a way to apply it.
:::

## Unpacking and merging

```php title="unpack.php" numbered
<?php

$pair = [812, 907];

[$first, $second] = $pair;

echo $first, " and ", $second, "\n";

$copy = ['accession' => 344, 'status' => 'available'];

['accession' => $a, 'status' => $s] = $copy;

echo $a, " is ", $s, "\n";
```

```text
812 and 907
344 is available
```

Unpacking by key, in the second form, is the most useful of the set: it
pulls out only the fields you care about and documents, on the line itself,
what the following code uses.

And to merge two arrays there are three little dots:

```php title="merge.php" numbered
<?php

$available = [812, 907];
$reserved = [344];

$all = [...$available, ...$reserved];

print_r($all);
```

```text
Array
(
    [0] => 812
    [1] => 907
    [2] => 344
)
```

The `...` is called **spread**. Notice that the keys were renumbered
automatically — for lists, it already delivers the result in the right
shape. With text keys it also works since PHP 8.1, with the rule that the
last duplicate wins.

:::summary
- `[]` creates an array; `$a[] = $x` appends at the next free position.
- Positions start at zero; `count()` returns how many there are.
- Numeric keys for lists, text keys for records.
- An array in PHP is an ordered map — a list is just a convention about the
	keys.
- It becomes a JSON list only with keys `0..n-1` with no gaps; `unset`
	opens a gap and `array_values` closes it.
- `isset` says "exists and is not null"; `array_key_exists` says only
	"exists".
- `in_array` compares with `==` unless you pass `true` as the third
	argument.
- Arrays are copied by value, unlike in Python and JavaScript.
- Three levels deep is a symptom that another structure is missing.
:::

:::checkpoint
You create lists and maps, add and remove items, can tell whether an array
will become a list or an object in JSON, and can explain why `isset` and
`array_key_exists` disagree.
:::

:::exercise level=1
Build an array with three copies, each with accession, title and status.
Print the title of the second one, the total count, and then add a fourth
copy and print the count again.

:::answer
```php
<?php

$catalog = [
    ['accession' => 812, 'title' => 'O Cortiço', 'status' => 'free'],
    ['accession' => 907, 'title' => 'Vidas', 'status' => 'repair'],
    ['accession' => 344, 'title' => 'Sertão', 'status' => 'free'],
];

echo $catalog[1]['title'], "\n";
echo count($catalog), "\n";

$catalog[] = [
    'accession' => 501,
    'title' => 'Iracema',
    'status' => 'available',
];

echo count($catalog), "\n";
```

```text
Vidas
3
4
```

`[1]` is the second one because positions start at zero. That is the only
part of the exercise worth checking carefully.
:::

:::exercise level=2
Given the array below, remove the copy in repair and print the result as
JSON. Write two versions: one that produces an object and one that produces
a list. Explain what changes for whoever receives it.

```php
$copies = [
    ['accession' => 812, 'status' => 'available'],
    ['accession' => 907, 'status' => 'in_repair'],
    ['accession' => 344, 'status' => 'available'],
];
```

:::answer
```php
unset($copies[1]);

echo json_encode($copies), "\n";
echo json_encode(array_values($copies)), "\n";
```

```text
{"0":{"accession":812,"status":"available"},
 "2":{"accession":344,"status":"available"}}
[{"accession":812,"status":"available"},
 {"accession":344,"status":"available"}]
```

For whoever receives it, the difference is total. A program expecting a
list will iterate over the first result and find zero items, because an
object is not iterated by index. There is no error: there is an empty
screen.

And notice that the data is identical in both cases. The same two copies,
the same fields, the same values. What changed was only the shape — and the
shape is half of the contract.
:::

:::exercise level=3
The snippet below came from the System and decides whether to save the note
attached to a return. It has a bug that only shows up in one specific case.
Find the case, explain it and fix it.

```php
$checkin = [
    'accession' => 812,
    'note' => null,
];

if (isset($checkin['note'])) {
    saveNote($checkin['note']);
}
```

:::answer
The specific case is the note that exists and is **deliberately** empty.

`isset` answers `false` for two different situations: the key not existing,
and the key existing with the value `null`. Here it exists. Someone,
somewhere, built this array with the field present — which usually means
the form had the field and the person did not fill it in.

If the business rule is "save the note when the field came in the form,
even if blank", `isset` is wrong. If it is "save only when there is text",
it is right by accident, and will stop being right the day someone changes
the default value from `null` to `''`.

The fix is to choose the question and write it down:

```php
if (array_key_exists('note', $checkin)) {
    saveNote($checkin['note']);
}
```

if the rule is about the field having arrived, or

```php
if (($checkin['note'] ?? '') !== '') {
    saveNote($checkin['note']);
}
```

if the rule is about there being text. The `??` covers the case where the
key does not even exist, and the comparison with `''` makes the intent
readable for whoever reviews it.

What you cannot do is leave `isset` and hope the two rules never diverge.
They diverge — that is how four readers showed up on Vera's report in
chapter @cap:variaveis-e-tipos, for the same reason, under another name.
:::
