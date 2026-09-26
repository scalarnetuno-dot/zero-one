---
source_hash: bcb494e6f209
title: "What a REST API is"
number: 2
slug: o-que-e-uma-api-rest
part: p1
kicker: "Mr. Juvenal wants a button that renews everything. The hard question is not how to do it — it is what happens when someone presses it twice."
goal: >-
  Design an API's addresses from its resources, separate what is safe from
  what is idempotent, choose the status that already answers half the
  question, and know what can and cannot change once someone has started
  consuming it.
---

:::story Renew everything
"One little thing," said Mr. Juvenal. "A button that renews everything at
once. Mrs. Marlene takes six books."

"Doable," said Dedé.

"Great."

"The question is what happens when she presses it twice."

Mr. Juvenal thought it was a joke and waited for the rest.

"Seriously: her phone is bad. She presses, the screen keeps spinning, she
presses again. Do the six books renew twice?"

"Renew for twenty-eight days?"

"Or the system refuses the second one and she thinks it didn't work."

Tainá looked up from her notebook.

"And what if she closes the app halfway through?"

"Then it's even better: nobody knows whether it renewed."
:::

## The address names a thing, not an action

An API is designed by listing **the domain's nouns** and deciding which of
them deserve an address of their own. Casa Amarela has five: book, copy,
reader, loan and reservation.

Each noun yields two addresses:

| Address | What it is |
|---|---|
| `/books` | the whole collection |
| `/books/12` | one item in it |

And when a thing only exists inside another, it becomes a nested address:

```text
/books/12/copies
```

That means "the copies of **that** book", and it is different from
`/copies?book_id=12`, which means "the collection of all copies, filtered".
Both forms work; the first says a copy does not make sense on its own, and
in the catalog it really does not.

:::pitfall
A filter is not a resource. `/books/children` looks organized and creates a
problem the next day, when someone wants children's books from 2020 on, or
children's books on loan, or children's books by one author.

Each combination would become a new address, and the list grows like the
class whiteboard from chapter @cap:heranca-interfaces-e-traits. A filter
lives in the query: `/books?classification=children&min_year=2020`.

The rule: **if you can imagine combining it with another filter, it is a
filter.**
:::

:::art caption="The button the person presses twice is the only one that matters."
src="o-botao-que-a-pessoa-aperta-duas-vezes-e-o-unico-que-importa.png"
Minimalist editorial cartoon on a white background: a seventy-nine-year-old
lady, in a cardigan and glasses, holds an old phone very close to her face
and presses, for the second time, a big button reading "RENEW ALL", while a
loading icon spins on the screen. Out of the phone, two identical arrows set
off at the same time towards a pile of six books, and above the pile float
two calendars, one reading "14 DAYS" and the other "28 DAYS", with a
question mark between them. Beside her, an enthusiastic older man in a cap
gives a thumbs-up, noticing nothing. Few elements, dry humor, tech-magazine
aesthetic.
:::

## Safe, idempotent, and neither

Here is the part almost nobody teaches and that decides how your API behaves
over a bad network.

:::term Safe and idempotent
**Safe** is a request that changes nothing on the server. It can be repeated
at will, in any order, by anyone.

**Idempotent** is a request that can be repeated without changing the
result: doing it once and doing it five times leave the system in the same
state.

Every safe request is idempotent. The reverse does not hold.
:::

| Verb | Safe | Idempotent |
|---|---|---|
| `GET` | yes | yes |
| `PUT` | no | yes |
| `DELETE` | no | yes |
| `POST` | no | **no** |
| `PATCH` | no | depends on what is written |

Table: This is not a style convention. It is what browsers, network
intermediaries and client libraries assume about your API without asking.

`PUT /books/12` is idempotent because it sends the whole book: repeating it
saves the same content. `DELETE /books/12` is idempotent because the final
**state** is the same — the book does not exist — even if the second call
answers `404` instead of `204`.

`POST /loans` is neither, and that is where Mrs. Marlene lives.

## The report that corrected things

The System has a screen you already know: the report that, when it finds a
strange row, fixes it. Its address is this:

```text
GET /report.php?month=02&action=fix
```

A `GET` that changes data breaks a promise nobody wrote in the code and
everyone depends on:

- **the browser may fetch it before you click**, so the page opens faster;
- **the network may keep the response** and hand it back to someone else;
- **the client may repeat it on its own** when the connection drops, because
  repeating a `GET` is safe by definition;
- **the whole address goes into the log**, with the parameters, on every
  machine it passes through.

The classic bug in this family is the system that lost content because an
indexing robot followed every link on the admin screen, and the delete links
were `GET`s. Nobody had written anything wrong — everybody had written
`<a href>`.

:::key
The question that separates `GET` from everything else is not "does it read
or write?". It is: **can some intermediary repeat this on its own without
telling me?**

If the answer is yes, and repeating causes harm, the verb is wrong.
:::

## The repetition you don't control

Back to Mrs. Marlene's phone, because her problem is not that she presses
twice. It is worse.

```text
> POST /renewals
> (the connection drops before the response arrives)
```

The app does not know what happened. Maybe the request never arrived; maybe
it arrived, was processed, and it was the response that got lost. The two
situations are identical from outside.

A well-written client tries again. And if your API is not ready for it, the
second attempt creates the second renewal.

There are two ways out, and the order matters.

**The first is to design the operation to be idempotent.** "Renew" can mean
"add fourteen days to the due date" — which doubles when repeated — or "set
the due date to fourteen days from today" — which gives the same result on
both calls. The second definition is the same Vera rule, costs the same and
solves the problem on its own.

**The second, when the operation cannot be idempotent by nature**, is to let
the client stamp the attempt:

```text
POST /loans
Idempotency-Key: 7f3a9c-attempt-1
```

The server stores the key along with the response. If the same key comes
back, it returns the stored response instead of creating again. It is the
mechanism payment providers use, and for the same reason: nobody wants to
charge twice because the phone froze.

## So what is "renew everything"

Neither `PUT /loans`, nor `GET`.

`PUT` on a collection means "replace the whole collection with what I am
sending" — which, read literally, would delete every loan not in the body.
Nobody does that, and that is exactly why the verb does not fit: it promises
something you are not going to deliver.

The way out is to remember that **the renewal is a thing**. It has a date, an
author, a quantity, and Vera is going to want a report on it at some point.
If it is a thing, it has a collection:

```text
POST /readers/47/renewals
Content-Type: application/json

{"loans": [4471, 4472, 4473]}
```

```text
201 Created
Location: /readers/47/renewals/91

{
  "id": 91,
  "renewed": [4471, 4472, 4473],
  "refused": []
}
```

Creating a resource called a renewal solves three things at once: the verb
becomes honest, the operation gets an identifier the client can look up
after a dropped connection, and the response can say that two books renewed
and one did not — which `PUT` would have no way of expressing.

:::key
When an action does not fit into create, read, update or delete, the
question is not "which verb do I invent?". It is: **what noun is hiding
here?**

Renewing hides a renewal. Returning hides a return. Cancelling hides a
cancellation. Almost always the noun is something the business already
counts, already files and already wants in a report.
:::

## The status already answers half

```text
201 Created
Location: /readers/47/renewals/91
```

The `Location` in a `201` response says where the created thing went to live.
It is what lets the client look it up later without guessing the address —
and it is what makes Mrs. Marlene's lost renewal recoverable.

Two status choices tend to be decided by arm-wrestling and deserve a rule:

**`409` versus `422`.** `422` is about the **request's content**: a missing
field, a date in the wrong format, a negative quantity. `409` is about the
**system's state**: the request is flawless and reality does not allow it —
the copy is already on loan, the reader has a fine, the reservation was
already cancelled.

The difference is useful to whoever consumes it: `422` asks the user to fix
what they typed; `409` asks them to look at the screen again, because the
world has changed.

**`200` with an error inside.** It does not exist. A `{"success": false}`
body with a `200` status forces every client to open and interpret every
response before knowing whether it worked — and the first one that forgets
will silently treat an error as a success.

## The contract with people you don't control

The day the readers' app is published in the store, your API stops being
yours. There are phones out there with the old version installed, and they
are not going to update because you asked.

| Change | Breaks? |
|---|---|
| adding a field to the response | no |
| adding an **optional** field to the request | no |
| adding a new address | no |
| renaming a field | **yes** |
| removing a field | **yes** |
| changing a field's type | **yes** |
| making a previously optional field required | **yes** |
| changing the status returned in an existing case | **yes** |

Table: The left column is all additions; the right, all changes and
removals. That is the whole rule, and it fits in one sentence.

:::pitfall
The most forgotten item is the last one. Swapping a `200` for a `204`
because "it had no body anyway" looks like tidying up and brings down every
client that did `if (status == 200)`.

The same goes for the error format. If today errors come out as
`{"error": "text"}` and tomorrow as `{"errors": [...]}`, it does not matter
that the second is better: the published app expects the first.
:::

When the change is unavoidable, the known path is to live with both for a
while — a new address in parallel, or a version number in the path — and
switch off the old one on an announced date while measuring who still uses
it.

## REST is not law

REST is a style, not a specification with an inspector. It is worth
something because it creates shared expectations: someone who has never
seen your API can guess half of it.

Where it does not fit, force less and document more. A search with fifteen
filters, a batch operation, a calculation that stores nothing — they all
exist, and none of them gets better by being twisted until it looks like a
resource.

The serious mistake is not straying from the style. It is straying **in
silence**, leaving the client to find out by trial and error.

## Casa Amarela's design

Written before the first route, and that is what makes it a design:

| Verb and address | Returns | Idempotent |
|---|---|---|
| `GET /books` | `200` with the list | yes |
| `GET /books/12` | `200` or `404` | yes |
| `POST /books` | `201` + `Location` | no |
| `PUT /books/12` | `200` or `404` | yes |
| `DELETE /books/12` | `204` or `404` | yes |
| `GET /books/12/copies` | `200` with the list | yes |
| `POST /loans` | `201`, `409` or `422` | no |
| `POST /loans/7/return` | `201` or `409` | no |
| `POST /readers/47/renewals` | `201` or `409` | no |
| `GET /readers/47/loans` | `200` with the list | yes |

Table: Ten lines cover the whole system. None of them has a verb in the
address, and the last three circulation operations are nouns Vera already
uses at the counter.

:::note In your career
Designing the table above takes forty minutes and saves weeks — but the
reason is not technical.

An address written after the code carries the code's decisions: the column's
name, the order of the parameters, what was easy to query that day. An
address written before carries the **business**'s decisions, and that is why
it survives the first database swap.

When you join a project that already has an API, ask for that table. If it
does not exist, putting it together by reading the routes is the best first
week you can have: nobody gets to know a system as fast as whoever wrote its
index.
:::

:::summary
- A resource is a noun; collection and item are two addresses of the same
  noun.
- Nest when the thing does not exist on its own; filter in the query when
  the combination with another filter is imaginable.
- Safe means changing nothing; idempotent means being able to repeat without
  changing the result. `POST` is neither.
- A `GET` that changes state breaks the assumption of whoever repeats on
  their own — and someone always repeats on their own.
- A network drop after the request is indistinguishable from an undelivered
  request: design the operation to be idempotent or accept an idempotency
  key.
- An action that is not CRUD hides a noun; creating it solves the verb, the
  identifier and the report at once.
- `201` carries `Location`; `422` is invalid content; `409` is an
  incompatible state; `200` with an error inside does not exist.
- Adding does not break; renaming, removing, changing types and changing
  statuses break.
:::

:::checkpoint
You design a domain's addresses from its nouns, classify each operation as
safe, idempotent or neither, choose between `409` and `422` with an argument,
and can say which changes you can publish without telling anyone.
:::

:::exercise level=1
Classify each operation as safe, idempotent or neither:

1. `GET /books/12`
2. `DELETE /reservations/88`
3. `POST /loans`
4. `PUT /readers/47`
5. `POST /loans/7/renewal`, defined as "the due date becomes today plus
   fourteen days"

:::answer
1. **Safe** (and therefore idempotent).
2. **Idempotent**, not safe. The second call returns `404` and the state
   stays the same: the reservation does not exist.
3. **Neither.** Each call creates a new loan.
4. **Idempotent**, not safe. Sending the whole reader twice saves the same
   content.
5. **Idempotent**, not safe — and that is the point of the question. The
   operation is a `POST`, which by default is not idempotent, but the
   **chosen rule** makes it so: setting the due date gives the same result
   for any number of repetitions, whereas adding fourteen days would not.

Case 5 shows that idempotency is not a property of the verb: it is a
property of the rule. The verb only says what the client can assume when it
does not know the rule.
:::

:::exercise level=2
Vera asks for three new things. Design the address and verb for each, and
give the success status and one possible refusal status.

1. Marking a copy as lost.
2. Listing the ten most borrowed books of the month.
3. Waiving a loan's fine.

:::answer
**1. Marking as lost.**

```text
POST /copies/2117/loss      → 201, or 409
```

It is an event with a date and someone responsible, not a field edit. The
`409` covers a copy already marked as lost.

The alternative `PATCH /copies/2117` with `{"status": "lost"}` works and
loses two things: the event's date and the ability to refuse invalid
transitions clearly.

**2. The ten most borrowed.**

```text
GET /books?sort=loans&period=2026-02&limit=10   → 200
```

It is not a new resource: it is the collection of books, sorted and
filtered. A `/books/most-borrowed` address would be the filter-turned-resource
trap — next month someone wants the most borrowed among the children's
books.

No obvious refusal status; a malformed period returns `422`.

**3. Waiving the fine.**

```text
POST /fines/312/waiver      → 201, or 409
```

The `409` is for a fine already paid: the request is correct and the state
does not allow it. A waiver is an event the grant's accountability report
will want listed separately — one more noun the business already had and the
code did not yet.
:::

:::exercise level=3
The catalog API has been published for three months and has two consumers:
the readers' app, in the store, and a spreadsheet the association updates on
its own.

A request comes in: `GET /books` today returns `year` as a number, and needs
to start returning an object with `year` and `edition`.

Write the plan in four steps and say what you would answer to "can't we just
swap it?".

:::answer
**Step 1 — add, don't swap.** The response starts carrying `year`
(unchanged) and a new field, `publication`, with the object. Nobody breaks,
because adding a field is the only safe change.

**Step 2 — measure who uses the old field.** Record, per consumer, who still
reads `year`. Without that number, step 4 becomes a discussion of opinions.

**Step 3 — announce with a date.** Tell both consumers that `year` goes away
on a specific date, with at least one app-update cycle of slack. Mark the
field as deprecated in the documentation, not just in the e-mail.

**Step 4 — remove it after the number reaches zero**, and not on the
announced date if it has not reached zero. The date is a commitment to
whoever adapted; the number is reality.

**"Can't we just swap it?"** We can, and the cost has an address: every phone
with today's published version starts showing a blank year, or freezing on
the details screen, depending on how the app handles a field that became an
object. They do not update because we asked — they update when the store
pushes it, and some of them never do.

The association's spreadsheet is worse, because nobody maintains it: it will
stop working on a Tuesday and Vera will call on Thursday.

The addition costs one extra field in the response for a few months. The
direct swap costs a window in which the product is broken for a slice of
users you cannot even count.
:::
