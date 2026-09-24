---
source_hash: f52afc5d3a05
title: "Closing"
slug: encerramento
matter: back
numbered: false
kicker: "The pharmacy calendar is still on Vertexo's wall, with twenty-five Saturdays crossed out and one circled."
---

:::story The circled Saturday
In June, Vertexo moved to another floor, and someone had to decide what to
do with the pharmacy calendar in the meeting room.

It was the way Nonato had left it in October: the Saturdays up to the 31st
of March crossed out one by one, in blue pen. One of them, in March, was
circled in red, with a note in Márcia's handwriting: *1,412*.

— The weekend that goes wrong — said Tainá.

— There's always one — said Márcia.

Nonato took the calendar off the wall, rolled it up and tucked it under his
arm, together with the folded paper with the FTP password, which he had
asked to keep and nobody had had the heart to refuse.

— Twenty-five weekends — he said. — I said it was one per item.

— You said there were twenty-six items — said Dedé.

— And there were. The twenty-sixth was Laravel. — He adjusted the calendar
under his arm. — It took the other twenty-five.

It took Dedé a moment to understand that it was a compliment.
:::

:::story Five stars
Kauã's app went into the store in May, with Casa Amarela's logo finally in
the right proportions. It had forty-two reviews, averaging 4.6. The shortest
was Dona Marlene's:

*"Now the e-mail comes signed by the library. Five stars."*

The longest was Seu Juvenal's, and it ended with a feature request.

On a Saturday in June, Vera arrived at eight forty, as on every day of the
last thirty-one years. She opened the panel and checked the summary of the
day: four returns in the drop box, no new overdue items, two reservations
waiting, and the three hundred covers she had photographed — all upright.

Tainá arrived at nine, with her notebook. It was on its last page.

— Finished? — asked Vera.

— The notebook? Finished. I bought another one.

— And what's on the last line?

Tainá read:

— "Ask the person who does the work before writing the code."

Vera thought for a moment.

— That should have been on the first.

The door opened. Seu Juvenal came in with a bag of lettuce seedlings.

— Morning, morning. The kids from the vegetable garden saw the app and got
excited. They want a little something. To keep track of the beds, who plants
what, who waters on which day. — He put the bag on the counter. — How long
does it take to make a little system like that?

Tainá opened the new notebook to the first page.

— How many beds are there?
:::

:::art caption="Every system ends with someone asking for a little something."
src="todo-sistema-termina-com-alguem-pedindo-uma-coisinha.png"
Minimalist editorial illustration on a white background, a light farewell
tone: the counter of a small neighborhood library on a Saturday morning.
Behind it, an older librarian in glasses checks a monitor showing thumbnails
of book covers, all upright. An intern opens a new notebook to the first
page, pen in hand. On the other side, an older man in a cap has just put on
the counter a bag of lettuce seedlings, his hands open in the gesture of
someone about to ask for "just a little something". Few elements, subtle
humor, tech-magazine aesthetic.
:::

## The path of the two volumes

Two books, sixty chapters, one neighborhood library. Looking back, each thing
Laravel does for you has a place where you did it by hand first:

| The problem | By hand, in volume 1 | In the framework, in this volume |
|---|---|---|
| storing data | SQL, PDO, transactions | migrations, Eloquent |
| organizing code | Composer, namespaces | `app/`, autoload, service providers |
| assembling objects | the `Services` of closures | the container that reads constructors |
| configuring | `.env` and `config/` | `.env` and `config/`, with caching |
| saying it went wrong | domain exceptions | handler, `422`, `409`, a single format |
| time | an injected `Clock` | `now()` frozen in tests |
| a large file | a generator, `fgetcsv` | `LazyCollection`, a batch on the queue |
| an uploaded file | `rename` at the end | `Storage`, private and public disks |
| notifying | a `Logger` with context | `Log`, notifications per channel |
| slow work | the middle-of-the-night script | queues, workers, batches, pacing |

Table: The same list, from both sides. The framework brought no new ideas to
this project; it brought the same ideas, ready-made, tested by more people.

That is why volume 1 exists. Whoever only knows the right-hand column uses
Laravel. Whoever knows both can say why it does what it does — and what to
do on the day it doesn't.

## What this book doesn't cover, and where to look

Some tools were left out on purpose. Each one solves a real problem, and none
is needed for an API like Casa Amarela's.

**Livewire** and **Inertia** build interactive interfaces without separating
front-end and back-end; each one's official documentation is the starting
point.

**Vue** and **React** are the way forward when Vera's panel becomes a real
application in the browser; this book's API is exactly what they consume.

**Octane** keeps the application loaded in memory between requests, and
makes the `singleton` from chapter @cap:service-container — and the `static`
variables from chapter @cap:escopo-e-referencias — even more dangerous;
Laravel's documentation has a whole section on what changes.

**Horizon** and **Redis** are the next step for the queue from chapter
@cap:queues-na-pratica, on the day the `jobs` table stops being enough.

**Multitenancy** — several libraries in the same system, with separate data
— is a design problem before it is a package problem; start with articles on
shared database × database per client. The second library, in the
neighboring district, is going to ask that question.

**GraphQL** is an alternative to REST for clients that need to build their
own queries; the Lighthouse package is the reference in Laravel.

**Microservices** and **Kubernetes** solve problems of organizations with
dozens of teams; for a library with three concepts and one computer, the
answer is the one in Tainá's notebook.

## One last thing

The 2009 Sistema stayed online for fifteen years without losing a
collection. It was written over a weekend, by a twenty-three-year-old, with
the tools there were. The new system will stay online as long as someone
knows how to work on it — and that someone, from now on, can be you.

When your own Seu Juvenal arrives, with the bag of seedlings and the little
something that takes a weekend, start with Tainá's question. How many beds
are there? Who waters them? What happens when two kids water the same bed on
the same day?

The code comes after. It always did.

:::milestone
The end of PHP One. Casa Amarela has an API in production, an app in the
store, upright covers, e-mails signed by the library and a queue that sends
the nine o'clock notice at nine. It also has a folder with the 2009 Sistema,
in two copies, that nobody deleted.

And, on the counter, a new notebook, with a question on the first page.
:::
