---
source_hash: 63fdb25c80ae
title: "The PHP you've heard about"
number: 1
slug: o-php-que-voce-ouviu-falar
part: p1
kicker: "A language made to count visits to a résumé, which today serves a huge part of the web — with types, enums and a new release every November."
epigraph: "I don't know how to stop it, there was never any intent to write a programming language. I have absolutely no idea how to write a programming language, I just kept adding the next logical step on the way."
epigraph_by: "Rasmus Lerdorf, creator of PHP"
goal: >-
  Know where PHP comes from, what caused its old reputation and when each
  cause was removed, what the language has today, what it does well, who
  uses it and why it is not going to die any time soon.
---

:::story Couldn't we do it in Node?
Dr. Aurélio had seen a talk on Thursday and came back with a question on
Friday.

"This library project. Why PHP?"

"The current system is PHP," said Dedé. "The hosting is PHP. Vera has been
using PHP since 2009."

"But weren't we going to modernize?"

"We are. From PHP 5.4 to PHP 8."

Dr. Aurélio made the gesture of someone brushing something away from his
face.

"Couldn't we do it in Node?"

"We could."

"Well, then."

"Then we rewrite everything, throw away fifteen years of business rules
that aren't documented anywhere, and deliver on March 31."

Pause.

"It's just that PHP is kind of..." he looked for the word, "...old."

"The current version came out in November."

Márcia spoke without looking up from her spreadsheet.

"What does Vertexo's payroll run on?"

Cléber cleared his throat.

"PHP."

"Which version?"

"Five point six."
:::

This conversation happens somewhere in the world every day, and the
misunderstanding is always the same: PHP's reputation describes, precisely,
a language that stopped existing more than ten years ago.

The defects that created it were real, had names and had dates — and all of
them were removed, one by one, between 2012 and 2021. The PHP you are going
to learn here is not the patched-up one: it is a typed, fast and predictable
language, with a public release calendar and a decade of fixes behind it.

It is worth spending a chapter on that difference for two reasons. The
first is that it explains the strange decisions you will find in old code —
and you will find them, because fifteen years of PHP are still running. The
second is that it is the argument you will want on the tip of your tongue
when someone repeats the joke in a meeting.

## A résumé, in 1994

Rasmus Lerdorf was a Danish-Canadian programmer who wanted to know how many
people visited his résumé on the internet. He wrote, in C, a handful of
small programs that did that and called the set **Personal Home Page
Tools**.

It was not a language. It was a personal utility, published in 1995
because other people asked for it.

What happened next is the most important thing in PHP's history: it **grew
by demand, not by design**. Someone needed to talk to a database, so a
function appeared. Someone needed to process a form, so a way appeared.
Every request became a new function, with the name that seemed reasonable
that day, in the argument order that seemed reasonable that day.

Twenty-five years later, that is why `strlen($text)` takes the text first
and `in_array($needle, $haystack)` takes the needle first. Nobody decided
that. It happened.

:::trivia
The name is a recursive acronym: **PHP: Hypertext Preprocessor**. It starts
with an abbreviation that refers to itself, which is a 1990s programmer
joke, and it replaced the original name — *Personal Home Page* — once it was
clear the thing had outgrown Rasmus's résumé.
:::

In 1997, two students in Haifa, Andi Gutmans and Zeev Suraski, decided to
rewrite the interpreter because they wanted to use PHP for a university
project and it could not cope. That rewrite became PHP 3, and the company
the two founded produced the engine that runs the language to this day.

## The milestones that still affect your code

:::diagram type="timeline" caption="Why the language is the way it is: the milestones you will run into in real code."
width: 112
events:
  - { year: "1995", text: "Rasmus Lerdorf releases PHP Tools: counting visits to a résumé" }
  - { year: "1998", text: "PHP 3, rewritten by Gutmans and Suraski — the language starts here", mark: true }
  - { year: "2004", text: "PHP 5: real objects, exceptions and PDO" }
  - { year: "2009", text: "PHP 5.3 brings namespaces and closures, ten years late", mark: true }
  - { year: "2010", text: "PHP 6 is abandoned without ever existing; the number was skipped" }
  - { year: "2012", text: "Composer: dependencies resolved by a tool, not by FTP", mark: true }
  - { year: "2015", text: "PHP 7: about twice as fast, and types on parameters", mark: true }
  - { year: "2020", text: "PHP 8: match, enums on the way, named arguments, JIT", mark: true }
  - { year: "2021", text: "PHP 8.1: enums and readonly — the language becomes truly typed" }
  - { year: "2024", text: "PHP 8.4: property hooks; a new version every year, every November" }
:::

Notice two dates.

**2009** is when PHP got namespaces — the way to organize code into
packages without two files fighting over the same name. Until then, the
workaround was writing classes called `Zend_Db_Table_Row_Abstract`. All PHP
code from before that date looks like that, and it is still running
somewhere.

**2015** is when the language became fast. PHP 7 brought a new engine and
roughly double the performance of the previous version, without anyone
having to change a line. It was the biggest free upgrade in the history of
the web, and a good part of that decade's server savings came from it.

:::trivia
**PHP 6** existed for five years as an attempt: a rewrite to handle text as
Unicode from end to end. It proved too big and was abandoned around 2010.

When the next version was ready, the community voted to skip the number 6
and call it 7 — because there were already books published about "PHP 6"
describing a language that was never released. It is the only popular
language that skipped a whole version so as not to confuse people who had
bought the wrong book.
:::

## Where the reputation came from, and what became of each cause

The old reputation was not prejudice: it had four concrete causes, and all
four were true. They are here for two practical reasons — so you can
recognize them when you open a system from 2009, and so you know, for each
one, in which version it stopped existing.

**`register_globals`.** Until PHP 4.2, on by default: any parameter that
arrived in the URL automatically became a variable inside your program. A
page that checked `if ($admin)` could be accessed with `?admin=1`. It was
only removed in PHP 5.4, in 2012.

**`magic_quotes`.** PHP escaped everything coming from a form on its own,
in the hope of preventing injection attacks. The real effect was to produce
a generation of programmers who thought they were protected without being
so, and a database full of `O\'Brien`. Removed in the same version.

**The `mysql_*` functions.** The old way of talking to a database was to
build the query by gluing text together. That works, and it invites the
biggest security hole in the history of the web. They were deprecated in
2013 and removed in 2015 — twenty years after they had taught the habit to
everyone.

**The standard library's silent failure.** Internal functions returned
`false` when something went wrong, instead of complaining — and a program
that did not check the return value carried on with an invalid value in
hand. That ended in PHP 8.0, in 2020: those functions started throwing
exceptions, and the error stopped being ignorable.

What is left of that story is the cosmetic part — `strlen($text)` takes the
text first and `in_array($needle, $haystack)` takes the needle first. The
names and orders stay as they are because changing them would break
millions of sites that work, and that is the right decision. In practice it
is a detail your code editor handles while you type.

| The cause | When it stopped existing |
|---|---|
| `register_globals` | PHP 5.4, in 2012 |
| `magic_quotes` | PHP 5.4, in 2012 |
| `mysql_*` functions | PHP 7.0, in 2015 |
| silent failure in internal functions | PHP 8.0, in 2020 |
| no declared types | PHP 7.0 in 2015; enums and `readonly` in 2021 |

Table: No item on this list describes the PHP you are going to install. All
of them describe code that may still be running on some server.

In 2012, an essay called *"PHP: a Fractal of Bad Design"* catalogued all of
this and became the reference for anyone who wants to attack the language.
It is long, detailed and it was right when it was written.

What is rarely mentioned is what happened next: the community read it,
agreed with a good part of it and spent a decade fixing it, item by item,
in the order in which they appeared in the critique. Today the essay is a
historical document — and the timeline in the column above is the answer to
it.

## What really changed

Four things, and only the first is about syntax.

**The language became typed.** You can declare the type of every
parameter, every return value and every property, and ask PHP to reject
whatever does not fit. There are `enum`, `readonly`, `match` and types that
combine other types. It is not Java, and it is no longer the lawless land of
2009.

**A way to install other people's code appeared.** Before 2012, using a
library meant downloading a `.zip`, copying it into a folder and hoping.
Composer brought what Ruby, Python and Node already had: a file declaring
what the project uses, and a command that sorts out the rest.

**Shared conventions appeared.** A group of maintainers of large projects
started publishing standards — the PSRs — saying how to name files, how to
load them, how to write logs, how to represent an HTTP request. That sounds
bureaucratic, and it is the reason libraries by different authors work
together today.

**Tools that read your code appeared.** Static analyzers such as PHPStan
and Psalm find, without running anything, the typo that used to show up
only in production at three in the morning.

It is worth pausing for a second on what this list means, because it is the
strongest argument in favor of the language and it is almost never made.

A language with thirty years of life accumulates bad decisions — they all
do. What sets apart a tool worth investing a career in is not never having
been wrong: it is what it does with the mistake once it is discovered.

PHP removed its own dangerous features, in numbered versions, with dates
and advance notice. It swapped out its entire engine and delivered double
the performance without charging a rewrite. It adopted a package manager,
types, interoperability standards and static analysis — each one after a
public discussion, with a recorded vote.

That is a decade of technical debt paid in full, in public, by a project
that could have chosen to just leave things alone. Many languages cited
today as "the safe choice" never had to do that, and nobody knows how they
would behave if they did.

:::key
Choosing a technology is a bet on what it will be five years from now, not
on what it was fifteen years ago.

The signals that matter in that bet are three, and PHP has all three: **a
new version on a fixed calendar**, **a public decision process** and **a
history of fixing what was wrong instead of defending it**.
:::

## What PHP does well

It is worth being specific, because "it's good for the web" explains
nothing.

**Every request starts from zero.** When someone asks for a page, PHP
builds everything, answers and throws everything away. Nothing survives to
the next request.

That looks wasteful and it is a huge advantage: there is no memory leak
building up over a week, no state shared between users, no global variable
contaminated by the previous request. A whole category of hard bugs simply
has nowhere to happen. Anyone who has ever hunted a leak in a process that
has been running for thirty days knows exactly how big this gift is.

**Deploying is copying files.** There is no mandatory compilation, no
process to restart, no application server to configure. Modern projects add
steps for good reasons, but the minimum is still the minimum — and that is
why there is PHP hosting for fifteen reais a month anywhere in the world.

**It comes with batteries for the web.** Sessions, uploads, dates, text,
JSON, an HTTP client, database drivers: it is all in the box, with nothing
to install.

**It is fast enough.** The relevant question in a web application is almost
never the speed of the language — it is how long the database takes. PHP 8
with a compiled-code cache serves the overwhelming majority of systems
anyone is going to write.

:::term OPcache
PHP reads your `.php` file and converts it into internal instructions
before running it. OPcache keeps that conversion in memory, so it does not
happen again on every request. It ships with PHP and has been on by default
since version 5.5 — and it is a large part of the reason the language is
fast today.
:::

## And what it does not do well

The same list, in reverse, and it is short and honest.

**Processes that stay alive.** WebSockets, connections open for hours,
thousands of simultaneous connections waiting: that goes against the
"start from zero and die" model. There are projects that solve it, and all
of them are rowing against the tide.

**Heavy computation.** Number crunching, model training, video
transformation. The right answer is another language, called from PHP.

**State shared in memory.** Since nothing survives between requests,
everything that needs to be remembered goes outside — database, Redis, a
file. It is extra work, and it is the direct price of the advantage above.

None of these items is a defect. They are the outline of the tool, and
knowing where that line runs is what separates choosing from repeating.

## Who uses it

**Wikipedia** runs on MediaWiki, which is PHP. **WordPress**, which powers
a huge slice of the world's websites, is PHP. **Etsy**, **Tumblr**,
**Mailchimp** and **Vimeo** have PHP at their core — Vimeo's team, by the
way, wrote one of the language's most widely used static analyzers.

**Facebook** was written in PHP and grew on it to the point where it started
maintaining its own dialect, Hack, which runs on its own engine. **Slack**
followed the same path. This is usually cited as proof that PHP does not
scale; the more honest reading is that two of the largest web applications
in the world were built in PHP and only needed something else after
outgrowing a size your system will probably never reach.

In Europe, a good share of corporate PHP systems are built on Symfony —
from railway companies to ride-sharing platforms. In Brazil, PHP is where
the money of the mid-market is: agencies, e-commerce, mid-size ERPs,
management systems, edtechs and the front desk of thousands of companies
that will never appear at a conference.

:::key
You will see the statistic that "about three quarters of websites use PHP".
It is real and comes from surveys of server technology, and it deserves an
honest caveat: it counts **sites**, not revenue or traffic, and it is
heavily driven by WordPress.

That does not make it useless — it just changes what it proves. No adoption
statistic proves technical quality, for any language. What this one proves
is a market: there is a gigantic amount of PHP in production, and someone
has to maintain it, evolve it and replace it with new systems.

Technical quality is argued from what the language has today — types,
enums, immutability, static analysis, one of the most mature framework
ecosystems on the web — and that is why it takes up a whole chapter instead
of a percentage.
:::

## PHP is unkillable

Announcing the death of PHP has become a literary genre. At least one
essay comes out every year, with an epitaph and a named successor, and the
first of them is older than many of the people who work with the language
today.

The same happens with Java, with C and with COBOL, for a reason that is not
technical: a language nobody uses does not get articles written about it.
In practice, the death notice works as a usage indicator.

Three concrete reasons sustain PHP's relevance, and none of them is
nostalgia.

**The first is the installed base.** Software in production is not
rewritten; it is maintained. Systems that work and make money do not stop
for five months to switch languages, and most of the jobs in any technology
exist because of what has already been written, not what is going to be.

**The second is that new projects still start in it.** Laravel is one of
the most used web frameworks in the world, with a commercial ecosystem
around it that pays people's bills. It is not nostalgia: it is people
choosing it today.

**The third is the cadence.** Since 2015 a version has come out every year,
every November, with two years of active fixes and one more of security
fixes. The language has a plan, a calendar and a public decision process.

And the honest boundary, because it is part of the picture: PHP is not the
fashionable language. That is different from being in decline — fashion
measures what gets talked about at conferences; production measures what
runs on a Tuesday. If your goal is to work with machine learning, low-level
systems or native apps, this is the wrong book and the wrong tool, and not
through any fault of its own.

If your goal is to build and maintain systems that serve real businesses,
and get paid for it, you chose well. The language is more solid than at any
point in its history, the community has proven that it fixes what breaks,
and the twenty-year-old joke is worth exactly what twenty-year-old jokes
are worth.

:::practice
Two five-minute checks, to bring this chapter into the real world.

**The first:** search for "PHP supported versions" and look at the official
calendar. It shows, per version, until when there are bug fixes and until
when there are security fixes. Write down the date for the version you just
installed — and if you ever inherit a system, that is the first page to
open.

**The second:** think of three websites you use every week and find out
what technology each one runs on. Browser extensions do that in one click.
The result usually surprises you with at least one of the three.
:::

:::summary
- PHP was born in 1994 as a personal utility and grew by demand, not by
	design — hence the inconsistent function names, which stayed for
	compatibility and are now a detail your editor handles.
- The old reputation has dated causes, and all of them were removed:
	`register_globals` and `magic_quotes` in 2012, `mysql_*` in 2015,
	silent failure in 2020.
- PHP 7 doubled performance in 2015 without charging a rewrite; PHP 8
	brought types, `match` and enums.
- A decade of technical debt paid in public, with recorded votes, is the
	best available signal of what the language will be five years from now.
- Every request starts from zero and dies at the end: a whole category of
	bugs disappears, and so does state shared in memory.
- It does data-driven web systems and business rules well; it does
	long-running processes and heavy computation badly.
- Wikipedia, WordPress, Etsy, Tumblr, Mailchimp and Vimeo run PHP; Facebook
	and Slack run a dialect of it.
- Its relevance comes from the installed base in production, from new
	projects still starting in it, and from one release a year on a public
	calendar.
:::

:::exercise level=1
Run `php -v` and write, in one sentence, what each part of the first line
means. Then find out whether your version still receives security fixes.

:::answer
```text
$ php -v
PHP 8.3.14 (cli) (built: Nov 21 2026 09:42:15) (NTS)
```

`8.3.14` is the version: family 8, release 3, patch 14. The `(cli)` says
this is the command-line PHP, not the one that serves the browser — that
distinction is going to cost somebody time in the next chapter. The date in
parentheses is when that executable was compiled, not when the version came
out. `NTS` means *non thread safe*, which is the normal variant on Linux.

The official release calendar says until when each family receives fixes.
The rule of thumb: a version gets two years of bug fixes plus one of
security fixes. Running a version outside that window is a decision — and
it needs to be written down somewhere as a decision, not as an oversight.
:::

:::exercise level=2
Casa Amarela runs PHP 5.6. Write, in five lines, the argument you would
present to Mr. Juvenal — who is not technical and pays for the hosting — to
justify the upgrade. Then write the same argument for Dr. Aurélio, who is
technical enough to ask "and the risk?".

:::answer
**For Mr. Juvenal**, the argument is risk and money, with no jargon:

> The version the library uses stopped receiving security fixes in 2018.
> Any flaw discovered since then is still open in our system, and the
> records hold the name, ID number and address of twelve hundred people
> from the neighborhood. The upgrade fits in the grant budget; an incident
> with residents' data does not.

**For Dr. Aurélio**, the argument is the risk of the change itself, because
that is what he is going to ask about:

> The upgrade breaks code that uses functions removed in PHP 7 — in our
> case, all of the database access. That is why we are not going to upgrade
> the old system: we are going to build the new one directly on 8.3 and
> keep the old one running until the switchover. The risk stays isolated in
> what we are writing, and the date to shut down the old one becomes a
> decision, not an accident.

Notice what changes between the two: it is not the level of technical
detail, it is **which risk each person is in charge of assessing**. One
answers for the money and the residents; the other, for the delivery.
Sending the second text to Mr. Juvenal would be talking to yourself.
:::
