---
source_hash: 1720405ffbbc
title: "What Laravel is"
number: 4
slug: o-que-e-o-laravel
part: p1
kicker: "The answer to the intern's question has two parts: what the framework does for you, and what it decides without asking."
goal: >-
  Describe a Laravel request's life cycle pointing out, at each stage, the
  equivalent in the previous chapter's micro-framework — and be able to name
  what the convention charges in exchange for what it delivers.
---

*"Why don't we just use this one?"*

Because the hundred-line file serves three routes and does not validate
input, handle errors, talk to a database, authenticate anyone, standardize
responses, have tests or have documentation. Completing that list is a
year's work, and the result would be a framework with a single maintainer.

The long answer is this chapter — and it does not start at "Laravel is
great". It starts at what, exactly, a framework is.

## A framework is code that calls yours

A **library** is code you call. You decide when, pass the arguments and get
the result. `symfony/var-dumper` is a library: you write `dump()` wherever
you want.

A **framework** is the opposite: it is the program, and your code is the
pieces it calls. You do not write the main loop, do not handle the request,
do not decide the order of the stages. You fill in gaps someone has already
numbered.

:::term Inversion of control
The name for that. With a library, control is yours and you ask for help;
with a framework, control is its and it asks for your code.

It is not a question of size. There are small frameworks and enormous
libraries. The difference is who calls whom.
:::

That has a practical consequence that shows up on day one: **you do not
choose the folder structure, the file names or the shape of the classes.**
The framework chose, and the price of disagreeing is higher than the price
of accepting.

## The pieces

Laravel was not written from scratch in 2011. It is an assembly, and a good
share of the pieces underneath come from Symfony:

| Piece | Origin | Job |
|---|---|---|
| `Illuminate\Http\Request` | extends Symfony's | the request as an object |
| `Illuminate\Http\Response` | extends Symfony's | the response as an object |
| `Illuminate\Console\Command` | extends Symfony's | terminal commands |
| `Illuminate\Container` | its own | resolves dependencies |
| `Illuminate\Routing` | its own | the route table |
| Eloquent | its own | objects that talk to the database |
| Blade | its own | generating HTML |

Table: `Illuminate` is the name of Laravel's set of components. Each of them
can be installed on its own, outside the framework.

That is useful and rarely stated: when you read `Request` in a Laravel
project's code, you are looking at a class that inherits from a Symfony
piece with more than fifteen years of use. The framework's "magic" part is
thinner than it looks — and the tested part, thicker.

## A request's life cycle

Here is the whole chapter in one table. On the left, what you wrote by hand;
on the right, who does the same job in Laravel.

| In your `mini.php` | In Laravel |
|---|---|
| the whole file | `public/index.php` |
| — | `bootstrap/app.php` assembles the application |
| — | *service providers* register and boot |
| `Container::get` | `Illuminate\Container\Container` |
| the layers' `array_reduce` | `Illuminate\Pipeline\Pipeline` |
| `$routes`, the array | `routes/api.php` and `routes/web.php` |
| `Router::dispatch` | `Illuminate\Routing\Router` |
| the route's function | your controller |
| `Response` | `Illuminate\Http\Response` |
| `send()` | `$response->send()` |

Table: Two rows have no equivalent in your file, and they are exactly the two
that let a framework grow without turning into a mess.

**`bootstrap/app.php`** is the place where the application is assembled
before any request arrives: which route files exist, which layers run in
each group, what to do with an unhandled exception. In your file, that was
mixed in with the routes because there were three of them.

A **service provider** is the piece you do not have yet and will want. Each
part of the framework — database, queue, cache, session — has a file that
tells the container how to build it. They run in two phases: first they all
*register* what they know how to do, then they all *boot*.

:::key
The split into two phases exists for a reason you will recognize from the
previous chapter's container: when booting, one provider may need something
another one registered.

Registering is cheap and depends on nobody. Booting may depend on everybody.
Doing both in a single pass would create a loading order — and loading order
is the `functions2_NEW_final.php` problem, in a bigger building.
:::

And **facades**, in one sentence, because they confuse newcomers:
`Cache::get()` is not really a static method — it is a shortcut that asks the
container which object answers for "cache" and calls the method on it.
Convenience when writing, with the real object underneath.

## Convention over configuration, and what it costs

Laravel decides a lot for you. Where controllers live, what classes are
called, which table a model uses, in what order the layers run, how an error
becomes a response.

Each of those decisions is time you do not spend — and a freedom you do not
have.

| What convention delivers | What it charges |
|---|---|
| no structural decisions on day 1 | the structure is not debatable on day 300 |
| anyone in the community can read the project | the project looks like all the others |
| version upgrades with a ready-made path | leaving the path makes upgrades pricier |
| ready answers for common problems | uncommon problems fight the default |

Table: The trade is good in most projects, and it is a trade. Whoever calls
it "all upside" has not yet had a requirement that fights the default.

:::pitfall
The expensive mistake is not choosing the convention. It is **refusing it
halfway**: keeping the framework and rewriting the part of it you did not
like.

The result is a project that neither follows the manual nor has a manual of
its own — and where every new person has to learn twice: how Laravel does it
and how we do it here.

If the convention does not fit, the honest path is to discuss that before
choosing the framework, not six months later with the deadline bearing down.
:::

## What it decides for you, and how to disagree

Not everything is imposed. It is worth knowing where there is room:

**Cannot be swapped without pain:** the top-level folder structure, the
request cycle, the container and the route file's format.

**Can be swapped, and commonly is:** the database layer — you can use
Eloquent, a hand-written query or both; the response layer; the internal
organization of `app/`, which the framework does not police.

**Just a default, and nobody cares:** folder names inside `app/`, controller
format, how many route files exist.

The rule: **the closer to the request cycle, the less negotiable.** The
closer to your business rules, the more.

## Laravel, Symfony or neither

All three are legitimate answers.

**Laravel** delivers more ready-made and decides more for you. Queues,
e-mail, authentication, scheduling and uploads come configured, and the path
for each is documented in the same place. The cost is that getting off the
rails takes work.

**Symfony** delivers looser pieces and more explicit configuration. It asks
for more decisions at the start and charges less for strange decisions
later. It is a frequent choice of large companies with a platform team.

**Neither** is the right answer in two real situations: a service with a
single route, where the framework would be more code than the service; and a
project whose problem is so specific that no convention helps — which is
rare, and almost always claimed before it is true.

For Casa Amarela, the decision fits in one line: a CRUD with business rules,
simple authentication, reports, a reminder queue and an admin screen is
exactly the shape Laravel was designed for.

:::note In your career
"Which framework is best?" is the question of someone who has not chosen one
yet. The question of someone who has shipped is a different one: **what
friction am I going to have, and is it friction I know how to pay for?**

Every technology choice has a place where it hurts. Being able to name that
place before starting is the difference between a decision and a hope — and
it is the answer that impresses in a technical interview, because it shows
you have taken a project far enough for the pain to show up.

When someone defends a choice and cannot say what it costs, it is not a
defense yet. It is enthusiasm, and enthusiasm has a short shelf life.
:::

:::milestone
End of Part 1. You read a request on the wire, designed the API's addresses
before the first route, wrote the four pieces every PHP framework has and
saw where each of them lives in a real framework. From here on, Laravel
comes in — and no part of it should look like magic.
:::

:::summary
- A library is code you call; a framework is code that calls yours.
- `Illuminate` is Laravel's set of components, and the HTTP and console
  pieces inherit from Symfony.
- The cycle is the same as the micro-framework's, with two extra pieces:
  `bootstrap/app.php` and the service providers.
- Providers register in one phase and boot in another, so as not to depend
  on loading order.
- A facade is a shortcut to an object that lives in the container, not a real
  static method.
- Convention delivers speed on day 1 and charges freedom on day 300.
- Refusing the convention halfway is worse than accepting it or not using the
  framework.
- The closer to the request cycle, the less negotiable; the closer to the
  business rules, the more.
:::

:::checkpoint
You describe a Laravel request's life cycle from `index.php` to the
response, point out each stage's equivalent in the file you wrote by hand,
explain what a facade is without using the word magic, and can say what the
framework's convention costs.
:::

:::exercise level=1
For each item, say whether it is a library or a framework, and why:

1. `symfony/var-dumper`
2. Laravel
3. PHPStan
4. Eloquent, used on its own, outside Laravel

:::answer
1. **Library.** You call `dump()` wherever you want; it calls nothing of
   yours.
2. **Framework.** It runs the cycle and calls your controller.
3. **A tool**, and the category is worth separating: PHPStan is not called by
   your program nor does it call your program — it **reads** your program,
   and runs outside execution. Analyzers, formatters and tests belong to this
   family.
4. **Library.** Outside the framework, Eloquent is a package you install,
   configure and call. It becomes part of a framework when the framework is
   the one deciding when to call it.

Case 4 is the interesting one: the same class is a library or part of a
framework depending on who is in charge. The distinction is not in the code
— it is in the direction of the call.
:::

:::exercise level=2
Take the previous chapter's `mini.php` and write, for each of its pieces, one
sentence saying what Laravel does **in addition** at the same point.

Cover: front controller, router, container and middleware.

:::answer
**Front controller.** Your `mini.php` reads the verb and the path and
dispatches. Laravel's `public/index.php` first assembles the application,
runs the service providers, resolves the environment and configuration, and
only then hands over the request — and at the end handles the exception
nobody caught, turning it into a response in the right format.

**Router.** Yours matches one regular expression per route, in order.
Laravel's compiles the routes, groups them by method, applies declared
constraints, resolves route names to URLs, and even fetches the record from
the database when the parameter is a model.

**Container.** Yours resolves parameters that are classes and keeps what it
built. Laravel's does that and more: it accepts explicit instructions for
what cannot be guessed, knows how to bind an interface to an implementation,
distinguishes what is a single instance from what is new on each resolution,
and can build the same object in different ways depending on the context.

**Middleware.** Yours is one chain. Laravel's is a chain per route group,
with per-route parameters, declared order and the ability to run work
**after** the response has already been sent.

The pattern of the four answers is the same, and it is the chapter's point:
none of them is a new idea. They are all the same idea with the hard cases
handled.
:::

:::exercise level=3
A company is about to start a new system and the team is split between
Laravel and "no framework, just the libraries we need".

Write the three strongest arguments on each side — the real ones, not the
internet ones — and say what information about the project would settle the
question.

:::answer
**For Laravel.**

The first is the cost of what is not your problem: authentication, queues,
e-mail, scheduling and uploads already exist, tested by a lot of people, and
none of them differentiates your product.

The second is hiring and continuity: there are people who already know the
structure, and whoever joins the project in two years will recognize the
design without a month of reading.

The third is security maintenance. When a flaw appears in a common piece, it
is fixed by whoever maintains the framework, and you update a dependency.
Without a framework, every piece is yours.

**For not using one.**

The first is the size of what you carry: a service with two routes runs
faster, starts faster and has less attack surface without fifty packages it
does not use.

The second is design freedom. If the project has an unusual constraint —
very low latency, its own message format, a different concurrency model —
the convention becomes a daily fight.

The third is clarity: without a framework, what happens is written in your
repository, and the request's path fits in one person's head.

**The information that decides it.** How many of these things the system
will need over the next two years: users with sessions, permissions by
profile, e-mail sending, background work, an admin screen, reports, uploads.

If the answer is "almost all of them", the framework has already won —
because the alternative is not "no framework", it is "a worse framework,
written in here, with no documentation". If the answer is "none of them, it
is a service that receives JSON and returns JSON", the team that wants to go
without is right.
:::
