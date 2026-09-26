---
source_hash: 659960bc942e
title: "Authorization: Gates and Policies"
number: 22
slug: autorizacao
part: p5
kicker: "The reader called, excited: he had discovered that, by changing a number in the address, he could see everyone's books."
goal: >-
  Answer "what are you allowed to do" — including when the resource is
  someone else's: separate role from permission, write Policies per
  resource, restrict listings by who is asking, and test every permission,
  because nobody tests by hand.
---

:::story The number in the address
The reader's name was Caio, he was sixteen and doing a technical course in
computing. He called on a Thursday, at five in the afternoon.

— Hi, it's just that I found something in the app. I don't know if it's
supposed to be like this.

Tainá put him on speaker.

— On my loans screen, if I open it in the browser, the address shows
`reader_id=212`. Which is me. So I changed it to 211.

— And?

— Dona Iolanda's books showed up. She has three. One's a cookbook. Then I
kept changing it. There are people with books overdue since November.

Dedé, across the table, already had the route open.

```php
public function index(Request $request)
{
    return LoanResource::collection(
        Loan::where('reader_id', $request->reader_id)
            ->paginate(),
    );
}
```

— Caio — said Tainá —, did you note down how many numbers you tried?

— About thirty. I stopped because I thought it might cause trouble.

— It did.

— For me?

— No. For us. Thanks for calling.
:::

## Authentication says who; authorization says what

Caio's route was behind `auth:sanctum`. It knew exactly who was asking —
reader 212, with a valid token. And it answered about reader 211, because
the number came from the client and nobody checked whether whoever was
asking had a right to the answer.

There are two questions, asked in sequence:

**Authentication:** who are you? Answered by the token. Failed, `401`.

**Authorization:** can you do **this**, with **this thing**? Answered by a
rule. Failed, `403` — or `404`, by the criterion from chapter
@cap:erros-padronizados.

The previous chapter solved the first. This one is the second, and it is
harder for one reason: authentication is the same for the whole API, and
authorization is **different for each resource**.

:::term Object-level authorization
Checking, for each record accessed, whether whoever is asking has a right
**to that specific record** — and not only to that type of record.

Its failure has a name on the most cited list of API risks in the industry,
and it is the list's first item: *Broken Object Level Authorization*. It is
Caio's defect: the reader was entitled to see loans, and the system did not
check **which**.
:::

:::art caption="The system knew who was asking. It didn't check what he could see."
src="o-sistema-sabia-quem-estava-perguntando-nao-conferiu-o-que-ele-podia-ver.png"
Minimalist editorial cartoon on a white background: a teenager in a hoodie
and headphones, sitting with a laptop on his lap, turns with his finger a
small number dial, like a padlock's, switching "212" to "211". With each
number, a different door opens in a row of identical doors in the
background, each with a stack of books and a reader's name on the little
plate; behind one of them a cookbook appears. The teenager, instead of going
in, picks up the phone to report it. Few elements, dry humor, tech-magazine
aesthetic.
:::

## A Gate for the loose rule, a Policy for the resource

Laravel offers two places to write permissions.

A **Gate** is a named, loose rule that belongs to no model:

```php title="app/Providers/AppServiceProvider.php" numbered
public function boot(): void
{
    Gate::define(
        'view-reports',
        fn (User $u) => $u->role !== Role::Reader,
    );
}
```

```php
Gate::authorize('view-reports');
```

A **Policy** is a class that gathers all the permissions **over one type of
resource**:

```text
$ php artisan make:policy LoanPolicy --model=Loan
```

```php title="app/Policies/LoanPolicy.php" numbered
<?php

declare(strict_types=1);

namespace App\Policies;

use App\Auth\Role;
use App\Models\Loan;
use App\Models\User;

class LoanPolicy
{
    public function view(User $u, Loan $l): bool
    {
        return $this->isStaff($u)
            || $l->reader_id === $u->reader_id;
    }

    public function create(User $u): bool
    {
        return $this->isStaff($u);
    }

    public function renew(User $u, Loan $l): bool
    {
        return $this->isStaff($u)
            || $l->reader_id === $u->reader_id;
    }

    public function returnLoan(User $u, Loan $l): bool
    {
        return $this->isStaff($u);
    }

    private function isStaff(User $u): bool
    {
        return in_array(
            $u->role,
            [Role::Clerk, Role::Admin],
            true,
        );
    }
}
```

Each method is a question: can they view this one? Can they create? Can
they renew this one? The ones that receive the `Loan` are about **one
record**; `create` does not receive it, because the record does not exist
yet.

Laravel finds the policy on its own by name: `Loan` → `LoanPolicy`, in the
`app/Policies` folder. Nothing to register.

Notice `create`. The reader **cannot** create a loan through the API — the
counter lends, with the book in hand. The app shows the collection,
reserves, renews. It is a decision of Vera's that chapter
@cap:o-que-e-uma-api-rest had no way of knowing, and which the policy
records in one line.

## `authorize`, `can` and the `403` that comes out on its own

In the controller:

```php title="app/Http/Controllers/LoanController.php" numbered
public function show(Loan $loan)
{
    Gate::authorize('view', $loan);

    return new LoanResource($loan);
}
```

`Gate::authorize` calls the `view` method of `Loan`'s policy with the
authenticated user. If it returns `false`, it throws
`AuthorizationException`, which the handler from chapter
@cap:erros-padronizados turns into `403`.

There is a form that asks without throwing, for when the answer changes the
behavior instead of interrupting it:

```php
if ($request->user()->can('renew', $loan)) {
    // show the button
}
```

And the Form Request has the `authorize()` that chapter
@cap:validation-e-form-requests left as `true`, with a debt written down:

```php title="app/Http/Requests/CreateLoanRequest.php" numbered
public function authorize(): bool
{
    return $this->user()->can('create', Loan::class);
}
```

For `create`, which has no record, you pass the **class**, and Laravel knows
which policy to use from it.

Debt paid. And with an ordering advantage: `authorize()` runs **before** the
validation rules. Whoever lacks permission gets `403` without finding out
which fields the route expects.

## Is the resource theirs?

The fix for Caio's route has two parts, because the route had two defects.

The first is the question about **one record**, and the policy solves it:
`GET /loans/312` now checks whether 312 belongs to the reader.

The second is subtler. The listing `GET /loans?reader_id=211` accepted a
**filter** coming from the client, and the filter decided whose data it
was. The policy does not help here: there is no record to ask about, there
is a query.

:::key
In a listing, the server decides the scope, from who is authenticated.
**Never** a parameter.

A `reader_id` coming from the client can be an extra filter — for the
librarian to choose which reader to see —, but only after the query is
already restricted to what the person asking has a right to see.
:::

## Listing with a scope

```php title="app/Models/Loan.php" numbered
public function scopeVisibleTo(Builder $q, User $u): void
{
    if ($u->role === Role::Reader) {
        $q->where('reader_id', $u->reader_id);
    }
}
```

```php title="app/Http/Controllers/LoanController.php" numbered
public function index(ListLoansRequest $request)
{
    $loans = Loan::visibleTo($request->user())
        ->when(
            $request->filled('reader_id'),
            fn ($q) => $q->where(
                'reader_id',
                $request->integer('reader_id'),
            ),
        )
        ->with('copy.book')
        ->orderByDesc('borrowed_at')
        ->orderByDesc('id')
        ->cursorPaginate(20);

    return LoanResource::collection($loans);
}
```

The order of the two restrictions is the point. `visibleTo` comes **first**
and restricts to the authenticated reader. The `reader_id` filter comes
**after**, and for an ordinary reader it can only narrow what was already
restricted. Caio asking for `?reader_id=211` gets:

```sql
WHERE reader_id = 212 AND reader_id = 211
```

An empty list. Not an error, not a confirmation that 211 exists — nothing.
The librarian, without the first restriction, gets 211's loans.

:::pitfall
The scope has to be on **every** query that returns reader data, and that
includes the ones nobody calls a listing: the CSV export, the search by
accession number, the "you have three books" counter in the header, the
statistics endpoint.

Caio's defect usually comes back through one of those side doors, months
later, on a new route someone wrote by copying the query without
`visibleTo`. That is why the test at the end of the chapter exists — and why
it needs to be written for every new route, not just the ones that look
sensitive.
:::

## `before`: the admin, and the care it needs

A policy can have a method that runs before all the others:

```php title="app/Policies/BookPolicy.php" numbered
class BookPolicy
{
    public function before(User $u, string $ability): ?bool
    {
        return $u->role === Role::Admin ? true : null;
    }

    public function create(User $u): bool
    {
        return $u->role === Role::Clerk;
    }

    public function update(User $u, Book $book): bool
    {
        return $u->role === Role::Clerk;
    }

    public function delete(User $u, Book $book): bool
    {
        return false;
    }
}
```

`before` returning `true` allows everything; returning `null`, it lets the
specific method decide. The admin can do anything with books; the clerk
registers and edits; nobody else deletes.

`before` is convenient and it is a place where rules vanish. If tomorrow
Vera says not even the admin can delete a book with an open loan, that rule
**cannot** live in `delete` — `before` allows it before `delete` is
consulted. Either `before` gets an exception, or the rule goes to the
service. It is the kind of thing that needs to be written in the file
itself, in a short comment, so the next person does not fall for it.

## A role is not a permission

The policies above ask about the **role** directly: `Role::Clerk`,
`Role::Admin`. It works with three roles, and ages badly for a predictable
reason: the day Casa Amarela takes on a volunteer who can register books and
**cannot** see readers' documents.

The volunteer is neither a clerk nor a reader. A fourth role forces a review
of every policy, looking for each `Role::Clerk` and deciding whether it
applies to her.

The separation that ages well: a role is a **collection of permissions**,
and policies ask about the permission.

```php title="app/Auth/Role.php" numbered
enum Role: string
{
    case Reader = 'reader';
    case Clerk = 'clerk';
    case Admin = 'admin';

    public function permits(Permission $p): bool
    {
        return in_array($p, $this->permissions(), true);
    }

    /** @return list<Permission> */
    public function permissions(): array
    {
        return match ($this) {
            self::Reader => [],
            self::Clerk => [
                Permission::ManageCatalog,
                Permission::ViewReaderData,
                Permission::RecordCirculation,
            ],
            self::Admin => Permission::cases(),
        };
    }
}
```

```php
public function create(User $u): bool
{
    return $u->role->permits(Permission::ManageCatalog);
}
```

The volunteer becomes a new case in the enum, with her list. No policy
changes. The `match` from chapter @cap:enums-datas-e-valores guarantees the
new case does not go without a list: without the line, the call throws
`UnhandledMatchError`.

And the `abilities()` that the previous chapter's `createToken` called comes
from here: they are the permissions' names, stored in the token. A reader's
token does not carry `record-circulation`, and `tokenCan` can check that
even before consulting the role.

:::pitfall
Storing the role or the abilities **in the token** has a cost: the token is
issued at login and lasts thirty days. If Vera removes a clerk's permission
on Monday, her token keeps the old abilities until it expires.

Two ways out, and both are used together. The policy checks the **current**
role in the database — `$u->role` is read on every request —, and the token
is only a second restriction. And changing someone's role revokes that
person's tokens, like the previous chapter's password change.
:::

## Testing permissions is mandatory

Nobody tests permissions by hand, because testing by hand takes three
accounts, two roles and the patience to switch logins at every attempt.
Caio tested because he was sixteen and had a free afternoon.

The suite in chapter @cap:testes-de-feature-http-e-banco covers this in
detail. The format already fits here:

```php title="tests/Feature/LoanAuthorizationTest.php" numbered
test('a reader cannot see another reader\'s loan', function () {
    $caio = User::factory()->reader()->create();
    $iolanda = Reader::factory()->create();
    $other = Loan::factory()
        ->for($iolanda)
        ->create();

    $this->actingAs($caio)
        ->getJson("/api/loans/{$other->id}")
        ->assertForbidden();
});

test('the reader filter does not widen the scope', function () {
    $caio = User::factory()->reader()->create();
    Loan::factory()->count(3)->create();

    $this->actingAs($caio)
        ->getJson('/api/loans?reader_id=211')
        ->assertOk()
        ->assertJsonCount(0, 'data');
});
```

Two tests, and both reproduce what Caio did. If someone, six months from
now, rewrites the listing and forgets `visibleTo`, the pipeline goes red
before the app is published.

:::note In your career
Object-level authorization is the most common security defect in APIs, and
the easiest to explain to non-technical people: "by changing the number in
the address, you can see someone else's data".

When you review code on a route that receives an identifier, ask two
questions, always: **who guarantees that this record belongs to the person
asking?** and **who guarantees that this list only has what they can see?**
If the answer is "the app only shows theirs", the route is open — the app is
the only client that will not try another number.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Auth/
    Role.php                    # role → list of permissions
    Permission.php              # enum
  app/Policies/
    LoanPolicy.php              # view and renew only one's own
    BookPolicy.php              # clerk registers, nobody deletes
    ReaderPolicy.php
  app/Models/
    Loan.php                    # scopeVisibleTo
  tests/Feature/
    LoanAuthorizationTest.php
:::

:::milestone
End of Part 5. The loan rule lives in a service Vera can read; the API knows
who is asking, stores passwords the right way, revokes tokens immediately;
and each resource checks whether the requester has a right to that record —
with a test for the number changed in the address.

In Tainá's notebook: *"the app is the only client that won't change the
number"*.
:::

:::summary
- Authentication answers who you are (`401`); authorization, what you may do
  with this thing (`403`).
- Object-level authorization checks the record, not just the type; its
  failure is the top API risk.
- A Gate is a named loose rule; a Policy gathers a resource's permissions and
  is found by name.
- `Gate::authorize` throws and becomes `403`; `can` asks without throwing;
  the Form Request's `authorize()` runs before validation.
- A listing is restricted by the authenticated user, on the server; a client
  parameter only narrows.
- `before` allows before the specific method, and a rule that applies even
  to the admin cannot live after it.
- A role is a collection of permissions; policies ask about the permission.
- An ability stored in the token ages; the policy checks the current role,
  and changing the role revokes the tokens.
- Permissions are tested with one test per case, because nobody tests by
  hand.
:::

:::checkpoint
The reader sees and renews only their own loans, the clerk registers and the
admin administers, every listing is restricted by who is asking before any
filter, and there is a test for the number changed in the address — and
another for the filter that tries to widen the scope.
:::

:::exercise level=1
For each request, say the expected status and which mechanism produces it:

1. Reader 212 requests `GET /loans/900`, which belongs to reader 211.
2. Reader 212 requests `POST /loans`.
3. A clerk requests `DELETE /books/12`.
4. A request without a token asks for `GET /me`.
5. Reader 212 requests `GET /loans?reader_id=211`.

:::answer
1. `403`, from `LoanPolicy::view` called in `show` — or `404`, if the team
   decides the existence of someone else's loan should not be confirmed.
2. `403`, from `CreateLoanRequest`'s `authorize()`, before any validation.
3. `403`, from `BookPolicy::delete`, which returns `false` — `before` does
   not allow it, because she is not an admin.
4. `401`, from `auth:sanctum`, before reaching any policy.
5. `200` with an empty list, from `scopeVisibleTo`. It is not `403`: the
   question is allowed, and the answer is that there is nothing there he can
   see.

Item 5 is often answered as `403`. The difference matters: a `403` would
tell Caio the filter was understood and refused; the empty list says
nothing.
:::

:::exercise level=2
Write the `ReaderPolicy` with the rules: a reader views and edits only their
own record; staff view everyone; only staff edit another reader's profile;
the document can only be changed by an admin. And write how
`UpdateReaderRequest` uses the policy for the document field.

:::answer
```php title="app/Policies/ReaderPolicy.php" numbered
class ReaderPolicy
{
    public function view(User $u, Reader $r): bool
    {
        return $u->reader_id === $r->id
            || $u->role->permits(Permission::ViewReaderData);
    }

    public function update(User $u, Reader $r): bool
    {
        return $u->reader_id === $r->id
            || $u->role->permits(Permission::ViewReaderData);
    }

    public function changeDocument(User $u, Reader $r): bool
    {
        return $u->role === Role::Admin;
    }
}
```

```php title="app/Http/Requests/UpdateReaderRequest.php" numbered
public function authorize(): bool
{
    $reader = $this->route('reader');

    if (!$this->user()->can('update', $reader)) {
        return false;
    }

    return !$this->has('document')
        || $this->user()->can('changeDocument', $reader);
}
```

`changeDocument` is an ability that corresponds to no route — it is a
permission over **a field**. A policy accepts methods with any name, and that
is how permissions finer than CRUD find a place.

An alternative would be to accept the request and silently ignore the
document for non-admins. It is worse: the client thinks it changed it and it
did not. An explicit refusal says what happened.
:::

:::exercise level=3
The "readers more than thirty days overdue" report exists in the panel, for
staff. A teammate is going to expose it in the API for a future staff app,
at `GET /reports/overdue`.

List everything that needs to be decided and protected before publishing
the route, and write the test you would demand in the review.

:::answer
**Decisions and protections:**

**Who can.** A `view-reports` Gate or a `ViewReports` permission, not "anyone
on staff" by role directly — the future volunteer probably should not see
who owes money.

**What goes out.** The panel's report shows name, phone and titles. In the
API, an `OverdueReportResource` decides field by field. The document does
not go out. The phone goes out only if the app is going to call people — and
then it is Vera's decision, not the team's.

**Ceiling and pagination.** It is a list of people. Without a ceiling, it is
an export of the debtors database in one request.

**Access log.** Who consulted it and when goes to the log, with the
incident. It is sensitive personal data — debt — and the association needs
to be able to answer who saw it.

**Token.** A reader's token cannot have the ability, even if the policy is
right — both layers.

**The test I would demand:**

```php
test('only those with permission see the report', function (
    Role $role,
    int $status,
) {
    $u = User::factory()->withRole($role)->create();

    $this->actingAs($u)
        ->getJson('/api/reports/overdue')
        ->assertStatus($status);
})->with([
    'reader' => [Role::Reader, 403],
    'clerk' => [Role::Clerk, 200],
    'admin' => [Role::Admin, 200],
]);
```

One more, checking that `document` does not appear in any item of the
response. And, when the volunteer is created, her row goes into that `with`
— and the test forces someone to decide the expected status.
:::
