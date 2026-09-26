---
source_hash: 1612a9ab7f2e
title: "What we are going to build"
number: 2
slug: o-que-vamos-construir
part: p1
kicker: "Eleven boxes on a slide, sixty-eight thousand reais on a deadline, and nobody in the room able to say what the system does today."
epigraph: "Walking on water and developing software from a specification are easy if both are frozen."
epigraph_by: "Edward V. Berard"
goal: >-
  Understand what an API is and why Casa Amarela needs one, tell a book from
  a copy from a loan, and finish with PHP, Composer and an editor installed
  and checked.
---

:::story 360° Modernization Journey
The slide had eleven boxes connected by arrows and, in the middle, a
bigger box that said **CORE**.

"It's simple," said Dr. Aurélio. "We modernize the core, expose it through
an API, plug in the mobile app and scale."

He had sold the project to a residents' association in forty minutes using
those four words, which is a genuine talent.

Dedé raised his hand.

"What does the core do today?"

There was a three-second silence, which in a meeting of twelve people is
enough time for someone to cough on purpose.

"It... processes," said Cléber.

"Processes what?"

Cléber had eight years at Vertexo and had already learned that a precise
answer turns into a task with your name on it. He looked at Márcia.

"Nonato knows," said Márcia.

"Nonato is on vacation."

"He's back on the 28th."

"And we deliver when?"

Márcia answered without checking anything, because she handled dates the
way a firefighter handles matches.

"The grant's accountability report is due March 31."

"And if we go past March 31?"

"We give sixty-eight thousand reais back to the city."

The meeting went on for another fifty minutes and produced three
architectural decisions about a system nobody present could describe.
:::

At seven in the evening that same Tuesday, Dedé stopped by Casa Amarela to
return an overdue book and see, with his own eyes, what Vertexo had just
committed to replacing.

:::story Forty seconds
"You're the computer guy?" asked Vera, without looking up from the label.

"I am."

"The System's bad."

"Bad how?"

She pointed at the monitor with her chin. Gray screen, an eighteen-field
form, three of the fields called `obs`, `obs2` and `obs_new`.

"When two people lend at the same time, one disappears. When I print the
overdue report, it freezes on the third page. When someone returns a book
on Sunday, it charges a fine, and we're not even open on Sunday. And the
usual one: if you search for 'Machado de Assis' with two spaces in the
middle, it says we don't have it."

"Since when?"

"The Sunday one, about four years. The others I don't even remember."

"And nobody fixed it?"

Vera stuck the label on, smoothed it with her thumb and picked up the next
book.

"Every year a young man comes and says he's going to fix it. You're the
fourth."
:::

## The question that stalls the project

The morning meeting was not a case of incompetence. What happened is what
happens in companies of every size: the system is old, whoever wrote it has
left or is on vacation, and the pressure for a schedule arrives before the
understanding does.

The result is always the same — architecture decisions made on top of a box
that says **CORE**.

Notice who, of the twelve people in the meeting, managed to describe the
system's behavior: nobody. And notice how long it took Vera to describe
hers: forty seconds, without stopping her labeling, with four defects, a
frequency and an approximate date for each one.

:::note In your career
"What does this system do today?" is the cheapest and most unpopular
question in any modernization project. It tends to stall the meeting — and
stalling the meeting is exactly the service it provides.

When you are the one asking, ask for an **example**, not a definition:
*"show me one thing a user does in this system, from start to finish"*.
Everyone improvises a definition. Nobody improvises an example.

And write the answer down in front of the person who gave it. A system
description that was not written down on the spot becomes, two weeks later,
two different descriptions.
:::

## Three programs wanting the same data

Before deciding anything technical, it is worth understanding why Casa
Amarela needs more than a new screen.

Today there is just one program: that gray monitor, on that desk, behind
that counter. It is the entire system. Anyone not standing in front of Vera
cannot look anything up.

What the association bought with the sixty-eight thousand is three things:

| Who uses it | What they need to do |
|---|---|
| Vera, at the front desk | register books, lend, take returns |
| the resident, on a phone | see the catalog and their own loans |
| the kiosk at the entrance | search for a title and say whether a copy is free |

Table: Three different screens, one catalog.

They are three distinct programs, written by different people, possibly in
different languages. And all three need the same information and the same
rules. If each one talks to the data in its own way, the "can this be
lent?" rule will exist in three versions — and they will drift apart at
three different speeds.

The way out is to have **one** program that knows the rules, and to agree
on a way for the other three to ask it for things.

That "agreed way" has a name.

:::term API
*Application Programming Interface*. It is a contract between two programs:
one knows how to do something, the other needs it done, and there is an
agreed way of asking and of answering.
:::

Vera has been an API for thirty-one years and nobody ever called her that.
You come to the desk, say the name of the book and show your library card;
she answers with the book, or with "it's out, back on Thursday". You do not
need to know where the shelf is, or how she decides the loan period. You
need to know **what to ask for** and **in what format she answers**.

That is exactly what we are going to write. The difference is that the
request will arrive over the network, and the answer will go out as text
another program can read.

## How one program asks another for something

When the resident's app wants to record a loan, it sends over the network a
block of text similar to this one:

```text
POST /loans
Content-Type: application/json

{"copy_id": 812, "reader_id": 47}
```

There are three parts, and all of them make sense in plain English.

The first line says **what to do** (`POST`, which means "create something
new") and **where** (`/loans`). The second says what format the request is
written in. After a blank line comes the request itself: which copy, for
which reader.

`POST` is one of the five verbs you will use throughout the book:

| Verb | Means | Example |
|---|---|---|
| `GET` | give me | `GET /books` |
| `POST` | create a new one | `POST /loans` |
| `PUT` | replace it entirely | `PUT /books/12` |
| `PATCH` | change a piece of it | `PATCH /books/12` |
| `DELETE` | remove it | `DELETE /books/12` |

Table: Five verbs cover almost everything an API does.

Notice the address: `/loans`, not `/createLoan`. The verb is already on the
outside, in the first word. Whoever puts the verb inside the address ends up
with `/createLoan`, `/renewLoan` and `/returnLoan` — three addresses for the
same thing, and none of them combinable with anything.

And every response starts with a three-digit number:

| Range | Means | The ones that show up in the project |
|---|---|---|
| `2xx` | it worked | `200` (here it is), `201` (created), `204` (done, no content) |
| `4xx` | the caller got it wrong | `404` (doesn't exist), `422` (invalid data) |
| `5xx` | the responder got it wrong | `500` (I broke) |

Table: The number is the first thing the other program reads — often the
only thing.

An app does not interpret the sentence "the operation could not be
completed". It looks at the number and decides between showing an error,
trying again or asking the user to log in. Returning `200` along with an
error message is the equivalent of saying "yes" while shaking your head.

## The field that confused everything

On Wednesday, Dedé sat down with Vera to understand how the catalog was
organized. The System's registration screen had, among its eighteen fields,
one called **Quantity**.

Lending, in the System, subtracted one from that field. Returning added
one.

It works. It worked for fifteen years.

Then he started asking questions.

:::story Five questions
"Which copy of *O Cortiço* does Mrs. Marlene have?"

Vera opened the drawer under the counter and pulled out a lined index card,
the filing-cabinet kind, with a number written in pen in the top corner:
**2.117**.

"This one."

"And does the System know that?"

"The System knows there are three."

"And which of the three is torn?"

"2.119. It has a loose page in the middle."

"And the one that went missing in 2017?"

"2.118. Someone took it and it never came back."

"Does the System know?"

"The System knows there are three."

Dedé looked at the screen again. **Quantity: 3**.

There were three paper cards in Vera's drawer and one number on the screen.
The cards answered five questions. The number answered half of one.
:::

## One thing, several things and an event

Two sentences that look the same and are not:

> "The library has *O Cortiço*."
>
> "The library has three *O Cortiço*s."

The first one is about the **book**: title, author, publisher, year,
subject. There is only one, and it cannot be lent. Nobody takes a title
home.

The second one is about the **copy**: the physical object, with an
accession number, a condition and a label stuck on its spine. That is what
walks out the door, tears, disappears and comes back.

:::term Accession number
The number that identifies each object in the catalog, one by one. It is
what Vera writes in pen in the corner of the card. Two copies of the same
book have the same title and different accession numbers.
:::

The **Quantity** field is what is left when someone merges the two concepts
into one. It keeps the *count* and throws away the *identity* — and identity
is exactly what all five questions were asking for.

A third concept is still missing, one that does not exist anywhere in the
System: the **loan**. It is not a characteristic of anything. It is an
event: such-and-such copy went out with such-and-such reader, on this day,
to come back on that one. Once it is over, it becomes history — and history
is where all the interesting questions Casa Amarela could never answer come
from.

:::diagram type="blocks" caption="One title, several objects, and an event that links an object to a person."
rows:
  - [{ text: "Book", note: "O Cortiço · Aluísio Azevedo · 1890" }]
  - [{ text: "Copy 2.117", note: "good condition" }, { text: "Copy 2.118", note: "lost in 2017" }, { text: "Copy 2.119", note: "loose page" }]
  - [{ text: "Loan", note: "copy 2.117 · Marlene · out 04/02 · due 18/02" }]
:::

Three names in place of one field. In exchange, Vera's five questions stop
depending on the drawer.

And that **Quantity** no longer needs to be stored: it becomes **counted** —
how many copies of this book are not on loan right now. It looks like more
work and it is less, for a reason worth remembering: a stored number can
drift from reality, a counted number cannot. When Dedé checked, the
Quantity field was wrong for fourteen books, and nobody knew since when.

:::art caption="One number on the screen; three different objects in the world."
src="um-numero-na-tela-tres-objetos-diferentes-no-mundo.png"
Minimalist editorial cartoon on a white background. On the left, an old CRT
monitor showing a single large field: "Quantity: 3". On the right, three
very different copies of the same book: a new one, a torn one with loose
pages, and a third represented only by an empty dotted rectangle with a
fallen label. Between the two sides, a thin arrow that only goes from right
to left. Few elements, tech-magazine line work, dry humor.
:::

## Install and check

Three things, all free, and one test for each.

First, the language:

```text
$ php -v
PHP 8.3.14 (cli) (built: Nov 21 2026 09:42:15) (NTS)
Copyright (c) The PHP Group
Zend Engine v4.3.14, Copyright (c) Zend Technologies
```

The only part that matters right now is the beginning of the first line. If
it says `8.3` or higher, you are ready. If it says `7.4`, half of what this
book teaches will not run on your machine.

| System | How to install |
|---|---|
| Ubuntu / Debian | add the `ondrej/php` PPA, then `apt install php8.3-cli` |
| macOS | `brew install php` |
| Windows | download from `windows.php.net/download`, or use WSL2 with Ubuntu |

Table: On Windows, WSL2 saves headaches once the project gets a database —
the environment ends up similar to the server's.

Then Composer, which is PHP's library installer:

```text
$ composer --version
Composer version 2.8.4 2026-10-30 12:18:44
```

It only comes on stage once the project has dependencies, but installing it
now saves you from stopping in the middle of a topic to sort out an
installation.

And an editor: VS Code, PhpStorm, Vim, Zed. Any of them will do, as long as
you can open a folder and save `.php` files.

:::practice
Run `php -m`. Out comes a list of names in a column: these are the
**extensions** compiled into your PHP, that is, the optional pieces of the
language that someone decided to include when they built that package.

Look for four: `mbstring`, `json`, `intl` and `pdo_mysql`. You use the first
two within the next few weeks of reading; the other two are missed once the
catalog leaves the program's memory and goes into a database. If any of
them is not on the list, install it now — on Ubuntu,
`apt install php8.3-mbstring`, and so on.

Finding out today that an extension is missing costs five minutes. Finding
out in the middle of a chapter costs an afternoon and the will to carry on.
:::

:::summary
- "What does this system do today?" stalls the meeting, and that is what it
	is for. Ask for an example, not a definition.
- An API is a contract: an agreed way for one program to ask and another to
	answer.
- The verb (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) states the intent; the
	address states the target. The verb does not go into the address.
- The three-digit code is the first thing the other program reads.
- A book is the title, a copy is the object, a loan is the event. Merging
	the first two costs a rewrite.
- A counted number does not drift from reality; a stored one does.
:::

:::milestone
Environment installed and checked, domain understood. From here on,
everything that appears in the book runs on your machine.
:::

:::exercise level=1
PHP accepts code straight from the command line with the `-r` option,
without creating a file. For example:

```text
$ php -r "echo 2 + 2;"
4
```

Use `-r` to print the PHP version, which is stored in a ready-made value
called `PHP_VERSION`. Then find out where your PHP's configuration file is,
with `php -i | grep "Loaded Configuration"`. Write both down.

:::answer
```text
$ php -r "echo PHP_VERSION;"
8.3.14

$ php -i | grep "Loaded Configuration"
Loaded Configuration File => /etc/php/8.3/cli/php.ini
```

`php -i` dumps the entire configuration, which is about five hundred lines;
`grep` filters the one you care about. On Windows, outside WSL, use
`php -i | findstr "Loaded"` instead.

Keep the path to `php.ini`. It is the file that decides, among other
things, whether errors show up on screen or vanish in silence.
:::

:::exercise level=2
Write the verb and the address for each catalog operation: list the books,
fetch one specific book, register, change and remove. Then write the three
loan operations: lend, renew and return.

:::answer
The five catalog ones come straight out of the verb table:

```text
GET    /books           list
GET    /books/12        fetch one
POST   /books           register
PUT    /books/12        replace
DELETE /books/12        remove
```

The three loan ones are more interesting, because renewing and returning are
not "create", "change" or "remove" — they are actions. The most common way
out is to treat the action as something you create:

```text
POST   /loans                  lend
POST   /loans/7/renewal        renew
POST   /loans/7/return         return
```

If your answer was `POST /renewLoan/7`, it works just the same. The
difference shows up at the hundredth operation, when the system has forty
addresses with verbs in their names and nobody can guess any of them
without checking the documentation.
:::

:::exercise level=3
Vera wants a "most borrowed books" report to decide what to buy with the
semester's budget. A book has several copies. If the report counts loans per
copy, does it answer the same question?

:::answer
It does not, and the difference is exactly the one in this chapter.

Counting per **copy** answers "which copy went out the most times". That is
a conservation question: the most borrowed copy is the one that will tear
first, and the one that needs rebinding.

Counting per **book** — adding up the loans of all copies of that title —
answers "what people want to read". That is an acquisition question, and it
is the one Vera asked.

Both are legitimate and serve different decisions. The problem is
delivering one while thinking you delivered the other, which happens
uncomfortably often, because the report's name tends to be the same in both
cases.

There is also a third number hidden in there, and it is the best of the
three: the most **wanted** title is not the most borrowed one. It is the one
that shows up most in reservations because there is never a free copy — and
that one is in neither count. Buying by the loan ranking means buying more
copies of what already circulates well, and none of what nobody manages to
get.
:::

:::story Scales to how many users?
On Thursday, Dr. Aurélio stopped by Dedé's desk.

"I heard you went to the library."

"I went to see the old system."

"And what's it like?"

"It's a PHP app from 2009 on a server hosted by a resident's nephew."

Dr. Aurélio nodded slowly, the way someone does while building a slide in
their head.

"Scales to how many users?"

"Twelve hundred. From the neighborhood."

"Hmm." A pause. "Have you considered microservices?"

Dedé thought about saying that the library has three concepts and one
computer.

"I'll look into it."

In Tainá's notebook, that day, went the first line of a list that would
grow until March: *"ask about the size before choosing the tool"*.
:::
