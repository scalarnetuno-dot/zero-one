---
source_hash: 7485400f7adf
title: "Validation and Form Requests"
number: 14
slug: validation-e-form-requests
part: p4
kicker: "The same book was in the collection three times. The ISBN was the same in all three — except for the hyphens."
goal: >-
  Refuse invalid input at the door, take the format rules out of the
  controller, make a partial PATCH work without erasing fields, and be able
  to say what is not validation and therefore does not go there.
---

:::story Three Dom Casmurros
Vera asked for the duplicate titles report because the collection count did
not match the paper inventory's. Dedé ran the query expecting zero.

```text
mysql> SELECT title, isbn FROM books
    ->  WHERE title LIKE 'Dom Casmurro%';
+--------------+-------------------+
| title        | isbn              |
+--------------+-------------------+
| Dom Casmurro | 9788535910667     |
| Dom Casmurro | 978-85-359-1066-7 |
| Dom Casmurro | 978 8535910667    |
+--------------+-------------------+
```

— But the ISBN is `unique` — said Tainá. — I saw it in the migration.

— It is. And the three are different.

— They're the same number.

— To you.

Vera looked over his shoulder.

— The first one was me. The second was Neide, who copies from the
catalogue card. The third I don't know, but it has a space, so it was
someone in a hurry.

— And which one is right?

— The book — said Vera. — All three are the same book. I have two copies of
it on the shelf, not six.
:::

## Validation is not a business rule

Before any code, a separation this whole chapter depends on. There are two
different questions a request needs to answer before becoming a write:

**Is the request well formed?** Did the title come? Is it text? Does it fit
in two hundred characters? Does the ISBN have thirteen digits? Is the
`copy_id` a number that exists in the table?

**Is the request allowed right now?** Is the copy available? Does the reader
already have three books? Do they owe a fine above five reais?

The first question is about **the format of what arrived**, and can be
answered by looking only at the request body and, at most, at whether a
record exists. The second is about **the state of the world**, and depends
on things that change from one second to the next.

| Question | Example | Wrong answer | Where it lives |
|---|---|---|---|
| well formed? | ISBN with 13 digits | `422` | validation |
| allowed now? | copy available | `409` | business rule |

Table: The two statuses from chapter @cap:o-que-e-uma-api-rest, now with an
address in the code. `422` says "fix what you sent"; `409` says "what you
sent is right and the world won't allow it".

:::key
Validation looks at **the request**. A business rule looks at **the world**.

When you do not know where a check goes, ask: if the client sends exactly
the same body five minutes from now, can the answer change? If it can, it is
not validation.
:::

This separation matters because the two things have different lives. The
format rule almost never changes — an ISBN will keep having thirteen digits.
The business rule changes every time Vera remembers an exception, and it
needs to be tested without HTTP, which is the subject of chapter
@cap:services.

## Rules where the data comes in

In the previous chapter, validation stayed inside the controller:

```php title="app/Http/Controllers/BookController.php" numbered
public function store(Request $request)
{
    $data = $request->validate([
        'title' => ['required', 'string', 'max:200'],
        'author' => ['required', 'string', 'max:150'],
        'subject' => ['required', 'string', 'max:40'],
        'isbn' => ['nullable', 'string', 'size:13', 'unique:books'],
        'year' => ['nullable', 'integer', 'min:1400'],
    ]);

    // ...
}
```

It works. `validate()` checks, and, if something fails, throws a
`ValidationException` that Laravel turns into `422` without your method
continuing. It is the same interruption as the binding that returns `404`:
the code after the line only runs if the line passed.

What is wrong is not the behavior, it is the **address**. There are three
problems, and they get worse over time.

**The controller grows on the wrong side.** The `store` method has one
responsibility — receive the request and deliver the response — and now it
has fifteen lines of format rules before it starts doing that.

**The rules repeat.** `update` has almost the same ones, with a difference
in `unique` that someone will forget to keep in sync. And Vera's screen, in
the Blade panel, has a third copy.

**The rules have no name.** To know what the API accepts on a
`POST /books`, someone has to open the controller and read an array in the
middle of a method. There is no place called "what a valid book is".

## Form Request: the controller that gets back to four lines

Laravel has a class whose only job is to answer the first question:

```text
$ php artisan make:request StoreBookRequest

   INFO  Request [app/Http/Requests/StoreBookRequest.php]
         created successfully.
```

```php title="app/Http/Requests/StoreBookRequest.php" numbered
<?php

declare(strict_types=1);

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class StoreBookRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'title' => ['required', 'string', 'max:200'],
            'author' => ['required', 'string', 'max:150'],
            'subject' => ['required', 'string', 'max:40'],
            'isbn' => [
                'nullable', 'digits:13', 'unique:books,isbn',
            ],
            'year' => [
                'nullable', 'integer', 'min:1400',
                'max:' . now()->year,
            ],
        ];
    }
}
```

And the controller:

```php title="app/Http/Controllers/BookController.php" numbered
public function store(StoreBookRequest $request)
{
    $book = Book::create($request->validated());

    return response()
        ->json($book, 201)
        ->header('Location', route('books.show', $book));
}
```

The change is in the **parameter type**. When Laravel is about to call
`store`, it sees that the method asks for a `StoreBookRequest`, builds that
object from the request and **runs the validation before handing it
over**. If it fails, the method is never called.

It is the container from chapter @cap:um-framework-de-quarenta-linhas
reading the parameter type through reflection, with one more step in the
middle. Chapter @cap:service-container opens that box completely.

:::term Form Request
A class that represents a kind of request — "create book", "create loan" —
and carries its format rules. The controller declares that it receives that
type, and validation happens before the method starts.
:::

`validated()` returns **only the fields that have a rule**. If the client
sends `internal_note` or `role`, they are not in `rules()` and do not reach
`create`. It is a second layer of protection behind the `$fillable` from
chapter @cap:eloquent, and the more important of the two: it stops things at
the door, before the data gets near the model.

:::pitfall
`$request->all()` after a Form Request returns **everything that came**, not
only what passed. The validation happened, but its result was ignored.

```php
Book::create($request->all());       // the whole body
Book::create($request->validated()); // only what has a rule
```

The two lines are the same length, and the first undoes half of this
chapter's work. In a code review, `all()` after a Form Request is a defect,
not a style.
:::

### The `authorize()` that returns `true`

The `authorize()` method asks whether **this person** may make **this
request**. For now, it returns `true` for everyone — there is no "this
person" yet, because the API has no login.

Leaving it as `true` is an honest decision for this chapter, and a debt
written down: chapter @cap:autorizacao comes back to it. If `authorize()`
returns `false`, Laravel responds `403` without calling the controller, and
that is why it exists here and not somewhere else.

## Normalize before checking

The three *Dom Casmurro* rows passed `unique` because `unique` compares text,
and `9788535910667` and `978-85-359-1066-7` are different texts. The rule
was right. The data arrived in three shapes.

The fix is the lesson from chapter @cap:strings, now with an address:
**normalize on input**. The Form Request has a hook that runs before the
rules:

```php title="app/Http/Requests/StoreBookRequest.php" numbered
protected function prepareForValidation(): void
{
    $this->merge([
        'isbn' => $this->filled('isbn')
            ? preg_replace('/\D/', '', $this->input('isbn'))
            : null,
        'title' => $this->filled('title')
            ? $this->normalizeSpaces($this->input('title'))
            : $this->input('title'),
    ]);
}

private function normalizeSpaces(string $text): string
{
    return trim(preg_replace('/\s+/u', ' ', $text));
}
```

`\D` is "anything that is not a digit". Hyphens, spaces and dots go, and the
three ISBNs become the same — which `unique` then refuses.

:::http title="The second Dom Casmurro, now"
POST /api/books
Content-Type: application/json

{"title": "Dom  Casmurro", "author": "Machado de Assis",
 "subject": "literature", "isbn": "978-85-359-1066-7"}
---
422 Unprocessable Content
Content-Type: application/json

{
  "message": "The isbn has already been taken.",
  "errors": {
    "isbn": ["The isbn has already been taken."]
  }
}
:::

Two things in this response. The message is Laravel's generic one — the fix
comes two sections from now. And the `422` came back having checked the
**normalized** ISBN: the database never saw the hyphen.

:::key
The order is **normalize, then check, then write**. Checking before
normalizing lets variations through; normalizing after writing leaves the
database dirty and forces every query to clean it again.

And the data the database stores is always the normalized one. Formatting
with hyphens, if the screen wants to show it, is the output's job — from
chapter @cap:api-resources.
:::

The three records already there do not disappear on their own. They need a
data migration that normalizes the column, merges the copies into the
record that remains and deletes the others — and that migration needs to be
checked with Vera before running, because "which of the three stays" is a
business question.

## `sometimes`, `nullable` and the `PATCH` that erases fields

Two words that look like synonyms and that produce, when confused, the
previous chapter's defect.

**`nullable`** says: the field may come with the value `null`. It says
nothing about the field **not coming**.

**`sometimes`** says: only apply the other rules **if the field is present**
in the body.

| Body | `['required']` | `['nullable']` | `['sometimes', 'required']` |
|---|---|---|---|
| `{}` | fails | passes | passes |
| `{"author": null}` | fails | passes | fails |
| `{"author": ""}` | fails | passes, becomes `null` | fails |
| `{"author": "Machado"}` | passes | passes | passes |

Table: The third column is the correct `PATCH`: an absent field is ignored;
a present field must be valid. The second column is the `PATCH` that erases
the author when the form sends the field empty.

The `""` row is surprising. Laravel has a global middleware that **converts
empty strings into `null`** before validation runs, and that is why
`nullable` accepts an empty string and stores null. It is convenient in an
HTML form, and it is exactly the path by which a required field disappears.

With that, the previous chapter's `update` gets its own class:

```php title="app/Http/Requests/UpdateBookRequest.php" numbered
class UpdateBookRequest extends FormRequest
{
    public function rules(): array
    {
        $required = $this->isMethod('PUT')
            ? 'required'
            : 'sometimes';

        return [
            'title' => [$required, 'string', 'max:200'],
            'author' => [$required, 'string', 'max:150'],
            'subject' => [$required, 'string', 'max:40'],
            'isbn' => [
                'sometimes', 'nullable', 'digits:13',
                Rule::unique('books', 'isbn')
                    ->ignore($this->route('book')),
            ],
            'year' => ['sometimes', 'nullable', 'integer'],
        ];
    }
}
```

`$this->route('book')` is the model the binding already loaded — the Form
Request can see the route parameters. And `ignore` solves the classic
`unique` defect on edit.

:::pitfall
Without `ignore`, editing a book's title and resending the same ISBN
produces `422`: "The isbn has already been taken". Taken **by the book
itself**.

It is the error every Laravel project finds on its first edit screen, and
the hurried fix is to remove `unique` from `update`. Then `PATCH` starts
accepting another book's ISBN, and the duplicate this chapter started out
fixing comes back through the other door.
:::

## Your own rule, and when it already exists

Laravel's built-in rules cover more than it seems, and it is worth looking
before writing:

```php
'status' => ['required', Rule::enum(CopyStatus::class)],
'copy_id' => ['required', 'integer', 'exists:copies,id'],
'due_on' => ['required', 'date', 'after:today'],
'cover' => ['nullable', 'image', 'max:2048'],
```

`Rule::enum` is the most valuable of the four: it uses the enum from chapter
@cap:enums-datas-e-valores as the source of truth. If a new case is added to
the enum, validation starts accepting it without anyone remembering to
update a list of strings.

When no built-in rule fits, a class solves it. An ISBN has a check digit —
the last number is calculated from the other twelve —, and any thirteen
digits are not an ISBN:

```php title="app/Rules/Isbn13.php" numbered
<?php

declare(strict_types=1);

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class Isbn13 implements ValidationRule
{
    public function validate(
        string $attribute,
        mixed $value,
        Closure $fail,
    ): void {
        if (!preg_match('/^\d{13}$/', (string) $value)) {
            $fail('The :attribute must have 13 digits.');
            return;
        }

        $sum = 0;

        foreach (str_split(substr($value, 0, 12)) as $i => $d) {
            $sum += (int) $d * ($i % 2 === 0 ? 1 : 3);
        }

        $check = (10 - $sum % 10) % 10;

        if ($check !== (int) $value[12]) {
            $fail('The :attribute is not a valid ISBN.');
        }
    }
}
```

```php
'isbn' => ['nullable', new Isbn13(), 'unique:books,isbn'],
```

The rule is a small class, testable on its own and reused in both Form
Requests. Notice that it **does not query the database**: checking whether
the ISBN exists in the collection is `unique`'s job, and mixing the two
would produce a rule that only works with the database on.

:::note
`:attribute` is a placeholder Laravel replaces with the field's name. The
name can be customized, which leads to the next section.
:::

## `422`, `errors` and the field the client highlights

The validation error response has a fixed format, and it is the format the
reader app is going to read:

```json
{
  "message": "The title field is required. (and 1 more error)",
  "errors": {
    "title": ["The title field is required."],
    "isbn": ["The ISBN is not a valid ISBN."]
  }
}
```

The `errors` key is a map from **field name** to **list of messages**. It is
how the screen knows which box to paint red — and that is why the field name
is a contract: renaming `title` to `name` breaks the highlighting in every
published client.

The messages come from two places. The project's default language goes in
`.env`, and the translation file is published once — which is also how a
project in another language, like the original Casa Amarela in Portuguese,
gets its messages:

```text
$ php artisan lang:publish
```

And the field's name, which appears inside the message, is declared by the
Form Request:

```php title="app/Http/Requests/StoreBookRequest.php" numbered
public function attributes(): array
{
    return [
        'title' => 'title',
        'isbn' => 'ISBN',
    ];
}

public function messages(): array
{
    return [
        'isbn.unique' => 'This ISBN is already in the collection.',
    ];
}
```

The `unique` message deserves its own text because it is the only one that
asks for a different action: the person does not need to fix what they
typed; they need to look for the book that already exists.

:::pitfall
Laravel's `422` format is **different** from the format of the other errors
the API returns today. The previous chapter's `abort(409, ...)` produces
`{"message": "..."}`, with no `errors`; `404` produces another format; a
`500`, a third.

Three error formats in the same API is the whole subject of chapter
@cap:erros-padronizados. For now, note it down: the client will have to
handle each one differently, and that will be fixed.
:::

## The loan, and what does **not** go into the Form Request

```php title="app/Http/Requests/CreateLoanRequest.php" numbered
class CreateLoanRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'copy_id' => [
                'required', 'integer', 'exists:copies,id',
            ],
            'reader_id' => [
                'required', 'integer', 'exists:readers,id',
            ],
        ];
    }
}
```

That is all. None of Vera's eleven rules is here, and the temptation to put
them in is huge — the Form Request has access to the database, and the rule
"the copy must be available" fits in a three-line closure.

Three reasons to resist.

**The check would be false.** The Form Request runs before the controller,
outside the transaction and without a lock on the row. Between validation
saying "available" and the loan being written, Neide may have lent the same
copy at the counter. The check that counts is the one that runs **inside**
the transaction, with the previous chapter's `lockForUpdate`.

**The status would be wrong.** A validation rule that fails returns `422`,
which says "fix your request". But the request is right — the copy exists,
the number is an integer. It is the world that won't allow it. It is `409`.

**The rule would be tied to HTTP.** The `library:fines` command, the Blade
panel and an import script also lend books. If the rule lives in the Form
Request, each of those paths needs to rewrite it.

:::key
`exists` stays in the Form Request because it answers "does this identifier
point to something?" — it is format, with one foot in the database. "Can
this thing be lent right now?" stays out, because the answer changes every
second and needs a lock to be true.

The boundary is uncomfortable, and it is uncomfortable in every framework.
When in doubt, leave the check in the service: it will sometimes be
redundant, but it will never be false.
:::

## Validating what goes out, too

A short note, because the tool arrives in the next chapter. Validating the
input protects the database from the client; nobody is protecting the client
from the database.

`BookController::show` returns the whole model. If tomorrow someone adds an
`internal_note` column to the table, it goes out in the response without a
single line of the controller changing. The input has an allow-list — the
`rules()`. The output does not have one yet.

:::note In your career
Validation is the first place an experienced reviewer looks in a new
project, because it says a lot in little space.

Rules in the controller say the project grew without a pause to tidy up.
`$request->all()` says someone trusts the client. `unique` without `ignore`
in `update` says nobody tested editing. And a business rule inside the Form
Request says the team has not yet separated "format" from "state" — which is
the most productive conversation you can start in a first week.

None of these observations requires knowing the domain. That is why they are
a good way in to contributing to a project you do not understand yet.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Http/Requests/
    StoreBookRequest.php          # rules + normalization
    UpdateBookRequest.php         # PUT × PATCH, unique with ignore
    CreateLoanRequest.php         # format only
  app/Rules/
    Isbn13.php                    # check digit
  app/Http/Controllers/
    BookController.php            # store and update with 4 lines
  lang/en/validation.php
:::

:::summary
- Validation answers whether the request is well formed; a business rule,
  whether the world allows it. The first gives `422`; the second, `409`.
- The boundary test: if the same body, five minutes from now, can get a
  different answer, it is not validation.
- A Form Request is one class per kind of request; the controller receives
  it by type, and validation runs before the method.
- `validated()` returns only what has a rule; `all()` after a Form Request
  undoes the protection.
- `prepareForValidation` normalizes before checking; the database always
  stores the normalized form.
- `nullable` accepts `null`; `sometimes` ignores what is absent. `PATCH`
  calls for `sometimes`.
- `unique` in `update` needs `ignore`, or it accuses the record itself.
- `Rule::enum` uses the enum as the source of truth; your own rule is a small
  class without a database.
- `errors` is a map from field to messages, and the field name is a
  contract.
:::

:::checkpoint
You move format rules into Form Requests, normalize input before checking,
implement a `PATCH` that does not erase absent fields, and can explain to a
teammate why "copy available" is not a validation rule.
:::

:::exercise level=1
Classify each check as **validation** (Form Request, `422`) or **business
rule** (service, `409`):

1. The reader's e-mail has an e-mail format.
2. The reader has no fine above five reais.
3. The `copy_id` exists in the table.
4. The copy is not being repaired.
5. The return date provided is later than today.
6. The reader does not have three books.

:::answer
1. Validation. The format does not change over time.
2. Business rule. The fine may be paid five minutes from now.
3. Validation. It checks that the identifier points to something — format,
   with one foot in the database.
4. Business rule. The copy's status changes, and the check needs a lock to
   be true.
5. Validation. "After today" depends on the clock, but not on the state of
   any record: the same body, tomorrow, can only start failing, and for the
   right reason.
6. Business rule. It is the classic case: the reader returns a book and the
   same request passes.

Item 5 is the one that sparks discussion, and the discussion is good. The
five-minute test helps: what changes the answer there is the calendar, not
someone else's action in the system.
:::

:::exercise level=2
Write the `prepareForValidation` and the rules of a `StoreReaderRequest` with
`name`, `document` (the CPF, Brazil's taxpayer number) and `phone`. The CPF
arrives with or without dots and a hyphen; the phone, with or without
parentheses. The database stores digits only, and the document is unique.

:::answer
```php title="app/Http/Requests/StoreReaderRequest.php" numbered
class StoreReaderRequest extends FormRequest
{
    protected function prepareForValidation(): void
    {
        $this->merge([
            'document' => $this->digitsOnly('document'),
            'phone' => $this->digitsOnly('phone'),
            'name' => $this->filled('name')
                ? trim(preg_replace(
                    '/\s+/u', ' ', $this->input('name'),
                ))
                : null,
        ]);
    }

    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:150'],
            'document' => [
                'required', 'digits:11',
                'unique:readers,document',
            ],
            'phone' => ['nullable', 'digits_between:10,11'],
        ];
    }

    private function digitsOnly(string $field): ?string
    {
        return $this->filled($field)
            ? preg_replace('/\D/', '', $this->input($field))
            : null;
    }
}
```

`digits:11` checks the length and that there are only digits, but does not
check the CPF's check digit — for that, a custom rule like `Isbn13`.

And a detail that usually slips by: `digitsOnly` returns `null` when the
field did not come, not an empty string. That way the document's `required`
fails with the right message, instead of failing on `digits:11` with a
message that confuses whoever filled it in.
:::

:::exercise level=3
A teammate proposed this rule for `CreateLoanRequest`, arguing that "this way
the error shows up on the right field on the screen":

```php
'copy_id' => [
    'required',
    'exists:copies,id',
    function ($attribute, $value, $fail) {
        $c = Copy::find($value);
        if ($c->status !== CopyStatus::Good) {
            $fail('Copy unavailable.');
        }
    },
],
```

The argument has merit. Write the review response: what is right about the
motivation, the two concrete defects, and how to satisfy the wish to
highlight the field without moving the rule.

:::answer
**What is right.** The motivation is legitimate: the app knows how to
highlight a field from `errors`, and a `409` with a loose sentence forces the
screen to decide by itself where to show it. The person is thinking about
the client, which is what the API exists to serve.

**First defect: the check is not true.** The closure runs before the
transaction and without a lock. Between it saying "available" and the
`create`, the counter may have lent the copy. The rule would give a false
sense of safety — and the real check, inside the transaction, would still be
needed, now duplicated.

**Second defect: the status lies.** The client receives `422`, which says to
fix the request. The request is correct. An app that handles `422` by
clearing the field and asking for another value will tell the reader she
"typed wrong" the book she is holding in her hand.

There is a third, smaller one: if `exists` fails, the closure still runs,
`find` returns `null`, and `$c->status` blows up with a property-on-null
error. The order of the rules does not stop the list by default.

**How to satisfy the wish.** The `409` response can carry the field. Chapter
@cap:erros-padronizados defines the API's single error format, and it has
room for that:

```json
{
  "type": "copy-unavailable",
  "message": "Copy 2117 is on loan.",
  "fields": {"copy_id": ["Copy unavailable."]}
}
```

The screen highlights the field, the status tells the truth, and the rule
keeps living where there is a lock. The review ends with a proposal, not a
refusal.
:::
