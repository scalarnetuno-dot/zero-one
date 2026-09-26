---
source_hash: 876fb3fad0f7
title: "Before you start"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Twenty-five weekends until March 31. Nonato counted them on the wall calendar, and the math came up one short."
---

Volume 1 ended on a Friday, with the folder tidied up and a question in
Tainá's notebook. This one starts on Monday.

## Monday, ten past nine

The first task of the week had nothing to do with the web. Dedé changed the
database password — the one that had passed through eleven files and Git's
history — and pasted the new one into `.env`, which goes nowhere.

"What was the old one?" asked Tainá.

"`secret`."

"And the new one?"

"Not `secret`."

Nonato, at the next desk, raised his hand without taking his eyes off the
screen.

"Objection. In 2009 the password was `casaamarela2009`. Someone changed it
to `secret` after me."

At nine forty, Mr. Juvenal walked into Vertexo's meeting room with a bag of
cheese bread and an announcement.

"My grandson, Kauã, made an app. Over a weekend. For the library." He turned
his phone towards the table: a blue screen, the Casa Amarela logo stretched
horizontally and a *Renew* button. "It just needs hooking up to the system."

"Hooking up how?" asked Márcia.

"I'll leave that to you. He said it's just an API."

Tainá opened her notebook to the last written page. Below *what gets from
the browser to PHP?* a second line appeared: *and from Kauã's app?*

## Nonato's weekend

The discussion started the way technical discussions start at Vertexo: with
someone saying there was no need to discuss.

"We do it in plain PHP," said Nonato. "You've just spent an entire book
learning PHP. I built the System over a weekend, and it's been live for
fifteen years."

"With `mysql_query` and MD5 passwords," said Dedé.

"With `mysql_query` and MD5 passwords, and not one catalog lost."

Dedé went to the whiteboard.

"All right. What does Kauã's app need to do?"

"See the books. Lend. Renew. Return."

Dedé wrote four words — **books, copies, readers, loans** — and, next to
each, the same four letters.

"CRUD," said Tainá. "*Create, read, update, delete.*"

"Four tables, four operations. Sixteen endpoints. That's the easy part." He
drew a line underneath. "Now the rest."

And he wrote, one per line: *routes. read JSON. respond with JSON. validate
every field. the reader's password. the app's token. who can do what. errors
in a single format. pagination. search. notice e-mails. a queue, so the
e-mail doesn't freeze the screen. cache. logs. database migrations. tests.
documentation for Kauã. deploy.*

"Each one of those," said Nonato, "is a weekend."

"Then count them."

Nonato counted the lines out loud, adding the ones Dedé kept remembering
along the way. They came to twenty-six. Then he got up, went to the wall
calendar — a pharmacy calendar, with the months in a row — and counted the
Saturdays until March 31, with his finger.

"Twenty-five."

"One short," said Tainá.

"The weekend where it goes wrong is missing," said Márcia. "There's always
that one."

Nonato sat back down, slowly.

"In 2009 there were no apps."

## The middle ground nobody asked for

"Laravel," said Dedé. "Everything on the board comes ready-made, and tested
by more people than we'll ever meet."

"And then nobody here knows what runs underneath," replied Nonato. "It
becomes magic. And magic breaks on a Friday night."

It was Tainá who broke the tie, without realizing she was breaking a tie.

"What if we do it by hand first? Small. Just to see what it does. Then we
use the real one."

Dedé looked at the whiteboard. Nonato looked at the calendar.

"How small is small?" asked Nonato.

"Forty lines."

"Forty lines I can read."

Vera, who had only come to hand over the list of eleven rules and had
stayed for the cheese bread, picked up her bag.

"Do it however you like. On Monday at nine I open. With or without an app."

The plan stayed on the whiteboard until the end of the project, in Dedé's
handwriting, with an arrow from Tainá beside it:

```text
1. understand what the browser (and Kauã) sends  -> HTTP
2. design the conversation before the code       -> REST
3. write a small framework, by hand              -> 40 lines
4. use the real one, knowing what it does        -> Laravel
```

That is the order of this volume.

## What you bring from volume 1

Everything Laravel will assume you know: types, arrays, functions, closures,
hand-written SQL, PDO, Composer, classes, interfaces, exceptions, strict
typing, enums, dates with time zones and errors that warn you. And a project
organized the way the framework is going to organize it:

:::tree title="What volume 1 left ready"
catalog/
  bin/                 import-donations.php, overdue.php
  config/app.php       timezone, loan period, database — read from .env
  public/              empty: it is the web's door, and the web starts here
  src/
    Catalog/           Book, Copy, CopyStatus
    Loans/             Money, LoanPeriod, LoanStatus
    Circulation/       domain exceptions, LibraryCalendar
    Import/            Csv, Importer
    Time/              Clock, SystemClock, FrozenClock
    Logger.php         logging with context
    Services.php       factory container, written by hand
  var/log/
  bootstrap.php        config, errors become exceptions, services
  .env, .env.example
  composer.json        psr-4 CasaAmarela\, phpstan level 5
:::

And the `casa_amarela` database, with `books`, `copies`, `readers` and
`loans`, written in plain SQL. Every piece of Laravel is going to be compared
with something in this tree — and, in some of those comparisons, the tree
wins.

If you came straight to this volume: the **Casa Amarela Community Library**
has four thousand titles and a PHP system from 2009, the **System**, which
serves the front desk while **Vertexo Systems** builds its replacement. The
money comes from a cultural grant, with an accountability report due on
**March 31**: if it runs late, the money goes back. **Dedé** explains,
**Tainá** asks and takes notes, **Vera** knows the rules, **Márcia** guards
the deadline, **Nonato** wrote the System, **Cléber** answers "it processes"
and **Mr. Juvenal** brings the next request.

## How this volume is organized

The chapters have their own numbering, starting from 1. When the text cites
a chapter from the first book, the citation says so: "chapter 21 of volume
1". Without that indication, the chapter is from this volume.

| Part | Chapters | What happens |
|---|---|---|
| 1 · The web beneath the framework | 1–4 | HTTP, REST, forty lines and choosing the framework |
| 2 · Inside Laravel | 5–9 | project, configuration, routes, requests, Blade |
| 3 · Eloquent on top of SQL | 10–12 | migrations, Eloquent, relationships |
| 4 · The real API | 13–17 | CRUD, validation, resources, pagination, errors |
| 5 · Architecture and security | 18–22 | container, services, middleware, Sanctum, Policies |
| 6 · After the response | 23–24 | queues, caching, logs and measurement |
| 7 · Prove it and ship it | 25–28 | tests, documentation, Git, CI and deploy |
| 8 · The system in production | 29–31 | uploads, e-mail and notifications, queues in production |

Table: Eight parts, in the order the problem shows up. The framework only
comes in at chapter 4, after you have written by hand what it does; the last
part starts the day after the deploy.

:::practice
Have PHP 8.3 and Composer installed, checked with `php -v` and
`composer -V`. If you came here through volume 1, you already have both. If
not, chapters 2 and 16 of volume 1 walk through the installation step by
step.
:::

Twenty-five weekends to go. On Monday at nine, Vera opens.
