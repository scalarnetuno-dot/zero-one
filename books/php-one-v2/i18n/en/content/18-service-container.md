---
source_hash: aa29a4f7cfaa
title: "Service Container and dependency injection"
number: 18
slug: service-container
part: p5
kicker: "Dedé opened the twenty-line container next to Laravel's. The intern recognized the reflection before he pointed at it."
goal: >-
  Understand the mechanism that assembles the application's objects,
  declare dependencies through the constructor, choose between bind,
  singleton and scoped, and swap an implementation in a test without
  touching whoever uses it.
---

:::story The same line
Dedé split the screen in two. On the left, the `mini.php` from the
forty-line chapter. On the right, a file from Laravel itself, inside
`vendor/`, with more than fifteen hundred lines.

— Look for it — he said.

Tainá scrolled the right one for a while. She stopped at a method called
`build`.

```php
$reflector = new ReflectionClass($concrete);
// ...
$constructor = $reflector->getConstructor();
// ...
$dependencies = $constructor->getParameters();
```

— It's ours.

— It's ours with fifteen years of people complaining.

— What are the other fourteen hundred lines?

— Each complaint.

She scrolled a bit more.

— There's a `singleton` here.

— Ours had one too. Remember `$built`?

— It kept everything.

— Right. Ours only knew how to do singletons.
:::

## The `new` scattered through the code is the problem

The `LoanController` needs to notify the reader when a loan is made. The
first version is direct:

```php
public function store(CreateLoanRequest $request)
{
    // ... the loan ...

    $sender = new WhatsAppSender(
        new Client(['timeout' => 5]),
        'https://api.provider.com.br',
        'key-hard-coded',
    );

    $sender->send($reader->phone, 'Loan made.');
}
```

It works, and it has three problems that grow in different directions.

**The controller knows too much.** It knows the notice goes by WhatsApp,
which HTTP library the sender uses, the timeout, the provider's URL. None of
that is the business of whoever records a loan.

**Switching costs a search.** When the library changes provider — and it
will, because the grant only covers one year of messages —, the
`new WhatsAppSender` needs to be found and replaced everywhere it appears.
There are four today.

**Testing is impossible.** Every test that goes through this method sends a
real message to someone's phone. Or it fails, because the test server has no
internet — and the test fails for a reason that has nothing to do with what
it wanted to prove.

The problem is not the `new`. It is **who** does the `new`. The class that
uses the sender should not be the class that assembles it.

## Asking instead of assembling

The change is small in the code and big in the design: the class **declares
what it needs**, and someone from outside delivers it.

```php title="app/Http/Controllers/LoanController.php" numbered
public function __construct(
    private readonly NoticeSender $notices,
) {}

public function store(CreateLoanRequest $request)
{
    // ... the loan ...

    $this->notices->send($reader, 'Loan made.');
}
```

The controller no longer knows anything about WhatsApp. It knows there is
someone who sends notices, and that this someone has a `send` method.

:::term Dependency injection
Handing an object the things it needs, instead of letting it create them.
The name is grand for an idea that fits in one sentence: **ask in the
constructor, don't build inside**.
:::

Who delivers? Someone has to do the `new` at some point. In a small program,
it is `index.php`, by hand. In a Laravel project, it is the **Service
Container** — the same mechanism that delivered the `StoreBookRequest` to
`store` in chapter @cap:validation-e-form-requests, and the `Book` to `show`
in chapter @cap:rotas-e-controllers.

## The container assembles the graph

When Laravel needs a `LoanController`, it does what the twenty-line
container from chapter @cap:um-framework-de-quarenta-linhas did:

1. Looks at the constructor through reflection.
2. Sees that it asks for a `NoticeSender`.
3. Tries to build a `NoticeSender`, looking at **its** constructor.
4. Repeats, going down, until it reaches classes with no dependencies.
5. Assembles everything bottom-up and delivers.

The result is a **graph**: the controller depends on the sender, which
depends on the HTTP client, which depends on the configuration. Nobody
writes that graph by hand. Each class declares only its immediate neighbor,
and the container chains them.

:::diagram type="flowchart" caption="Each class declares only the neighbor below. The container walks the whole chain."
nodes:
  - { id: c, type: process, text: "LoanController" }
  - { id: s, type: process, text: "LoanService" }
  - { id: e, type: process, text: "NoticeSender" }
  - { id: h, type: process, text: "HTTP client" }
  - { id: r, type: io,      text: "config('notices')" }
edges:
  - { from: c, to: s }
  - { from: c, to: e }
  - { from: s, to: e }
  - { from: e, to: h }
  - { from: e, to: r }
:::

### Autowiring, and where it stops

When the requested type is a **concrete class** whose dependencies are also
concrete classes, the container resolves it on its own. That has a name:
*autowiring*. Most classes in a Laravel project never need any
configuration to be injected.

It stops in two places, and both are the same ones where the twenty-line
container stopped:

**Primitive types.** A constructor that asks for `string $key` cannot be
guessed. Which string?

**Interfaces.** `NoticeSender` is an interface. The container does not know
which of the implementations you want — or whether any exists.

```text
Target [App\Notices\NoticeSender] is not instantiable while
building [App\Http\Controllers\LoanController].
```

The message is good: it says what it tried to build and for whom. The
answer is to tell the container what to do.

## `bind`, `singleton` and `scoped`

The container accepts instructions: "when someone asks for X, deliver Y".
There are three forms, and the difference between them is **how many times
the object is created**.

```php
$this->app->bind(NoticeSender::class, WhatsAppSender::class);
```

**`bind`** creates a new object **every time** someone asks. Two classes
that ask for `NoticeSender` in the same request receive two different
instances.

```php
$this->app->singleton(ProviderClient::class, fn () =>
    new ProviderClient(
        config('notices.url'),
        config('notices.key'),
    ));
```

**`singleton`** creates **once** and delivers the same instance forever —
for every request that process handles.

```php
$this->app->scoped(CurrentReader::class);
```

**`scoped`** creates once **per request** and discards it at the end.

| | Instances | For |
|---|---|---|
| `bind` | one per ask | cheap objects, no state |
| `singleton` | one per process | connections, clients expensive to create |
| `scoped` | one per request | state of the current request |

Table: The wrong choice between `singleton` and `scoped` throws no error.
It produces behavior that only appears with two users at the same time.

:::pitfall
A `singleton` holding request state is the container's classic defect.

```php
$this->app->singleton(CurrentReader::class);
```

With traditional PHP, each request starts from zero and the process dies at
the end — the singleton lives for a single request, and the defect does not
show. But the queue workers from chapter @cap:events-jobs-e-filas and
application servers that keep the process alive **reuse the process**. The
first request's reader is still there on the second.

Rosângela opens the app and sees Wellington's loans. Not through an
intrusion — through a `singleton` that should have been `scoped`.
:::

## Service Provider: where the instructions live

The container's instructions need to live somewhere that runs before any
request. That place is the **service provider**, and chapter
@cap:o-que-e-o-laravel already introduced it in passing.

```text
$ php artisan make:provider NoticeServiceProvider
```

```php title="app/Providers/NoticeServiceProvider.php" numbered
<?php

declare(strict_types=1);

namespace App\Providers;

use App\Notices\NoticeSender;
use App\Notices\WhatsAppSender;
use App\Notices\ProviderClient;
use Illuminate\Support\ServiceProvider;

class NoticeServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(
            ProviderClient::class,
            fn () => new ProviderClient(
                url: config('notices.url'),
                key: config('notices.key'),
                timeout: config('notices.timeout', 5),
            ),
        );

        $this->app->bind(
            NoticeSender::class,
            WhatsAppSender::class,
        );
    }
}
```

Laravel 11 registers the new provider in `bootstrap/providers.php`, and
`make:provider` already adds the line.

Notice where the primitives went: the URL, the key and the timeout come from
`config()`, which comes from `.env` — the path from chapter
@cap:configuracao-ambiente-e-artisan. The provider is the **only** place in
the project that knows how to assemble the provider client. Switching
provider is changing this file.

### `register` and `boot`

A provider has two methods, and the difference between them is one of
order.

**`register`** runs first, in every provider, and serves **only** to teach
the container. In it, you cannot ask the container for anything yet,
because other providers may not have registered what you need.

**`boot`** runs after all the `register`s. In it, the container is complete,
and you can use it — register events, configure `preventLazyLoading`, hook
up observers.

The practical rule: if the line starts with `$this->app->bind` or
`singleton`, it goes in `register`. If it uses something, it goes in
`boot`.

## Interface in the constructor, implementation in the provider

The gain from all this is in a one-line swap. The interface:

```php title="app/Notices/NoticeSender.php" numbered
interface NoticeSender
{
    public function send(Reader $reader, string $text): void;
}
```

And two implementations. The real one talks to the provider. The other
exists for development:

```php title="app/Notices/LogSender.php" numbered
final class LogSender implements NoticeSender
{
    public function send(Reader $reader, string $text): void
    {
        Log::info('notice', [
            'reader' => $reader->id,
            'text' => $text,
        ]);
    }
}
```

```php title="app/Providers/NoticeServiceProvider.php" numbered
$this->app->bind(
    NoticeSender::class,
    $this->app->isProduction()
        ? WhatsAppSender::class
        : LogSender::class,
);
```

In development, no notice leaves anyone's computer. In production, it does.
No controller, no service and no line of business rule knows the
difference.

It is the interface from chapter @cap:heranca-interfaces-e-traits keeping
the promise that chapter made: a contract Laravel asks for all the time. The
container is the reason interfaces are worth so much in a Laravel project —
without it, someone would have to choose the implementation by hand in each
place.

:::key
The question that decides whether an interface is worth creating: **is
there, or will there be, a second implementation?** A real one and a test
one count as two.

`NoticeSender` has three: WhatsApp, log and the test fake. Worth it.
`FineCalculator` has one, and the test one would be the same as the real one
— because it is pure. Not worth it: inject the concrete class, and
autowiring resolves it.
:::

## Swapping the implementation in a test

The third problem from the start of the chapter was testing. With the sender
coming from the container, the test can put another one in its place:

```php title="tests/Feature/LoanTest.php" numbered
test('notifies the reader when lending', function () {
    $fake = new FakeSender();
    $this->app->instance(NoticeSender::class, $fake);

    $this->postJson('/api/loans', [
        'copy_id' => 2117,
        'reader_id' => 47,
    ])->assertCreated();

    expect($fake->sent)->toHaveCount(1)
        ->and($fake->sent[0]['reader'])->toBe(47);
});
```

```php title="tests/Fakes/FakeSender.php" numbered
final class FakeSender implements NoticeSender
{
    public array $sent = [];

    public function send(Reader $reader, string $text): void
    {
        $this->sent[] = [
            'reader' => $reader->id,
            'text' => $text,
        ];
    }
}
```

`$this->app->instance()` tells the container: "from now on, when someone
asks for `NoticeSender`, deliver **this object right here**". The controller
receives the fake, and the test checks what was stored in it.

Not one line of the controller changed to allow the test. That is the
difference between testable code and code that has to be adapted for
testing — and chapter @cap:testes comes back to it more calmly.

## The two ways to use the container wrong

**The *service locator*.** The container is always reachable through the
`app()` function, and that lets you write:

```php
public function store(CreateLoanRequest $request)
{
    $notices = app(NoticeSender::class);
    // ...
}
```

It works, and undoes half the gain. The dependency vanished from the
constructor, and whoever reads the class no longer knows what it needs
without reading every method. The test can still swap it, but only if it
knows the swap is necessary.

The rule: `app()` in the middle of the code is a symptom. The legitimate
places are the provider, and framework code that has no constructor under
your control.

**Facades without understanding what they are.** `Log::info()`,
`Cache::get()`, `DB::transaction()` look like static calls, and are not.
Each *facade* is a small class that, on the call, asks the container for the
real object and passes the method on to it.

```php
Log::info('x');
// is, in practice,
app('log')->info('x');
```

They are convenient and they are a *service locator* in nice clothes — the
dependency does not appear in the constructor. Laravel compensates with its
own testing methods (`Log::spy()`, `Cache::fake()`), which is why the cost is
smaller than it looks. For the dependencies **of your domain** — the sender,
the loan service —, constructor. For the framework's infrastructure, a
*facade* is acceptable and is the ecosystem's idiom.

:::note In your career
Dependency injection is one of the subjects where the distance between the
name and the idea gets in the way most. In interviews, the question comes
with "IoC", "DI", "inversion of control", and the person who knows how to
use it freezes on the vocabulary.

The answer that works in any interview is concrete: "the class asks in the
constructor for what it needs, and whoever assembles it decides which
implementation to deliver; in Laravel, the container assembles, and I
register the choices in a provider". One sentence, and it shows you use it,
not that you memorized it.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Notices/
    NoticeSender.php         # interface
    WhatsAppSender.php       # production
    LogSender.php            # development
    ProviderClient.php
  app/Providers/
    NoticeServiceProvider.php # the only choice, in one place
  config/notices.php
  tests/Fakes/
    FakeSender.php
:::

:::summary
- The problem is not the `new`; it is who does it. The class that uses
  should not be the one that assembles.
- Dependency injection is asking in the constructor instead of building
  inside.
- The container reads constructors through reflection and assembles the
  whole graph; it is the twenty-line container with fifteen years of use.
- Autowiring resolves concrete classes; for interfaces and primitives, the
  container needs instructions.
- `bind` always creates; `singleton` creates once per process; `scoped`,
  once per request.
- A `singleton` with request state leaks data between users when the
  process is reused.
- Providers teach the container in `register` and use the container in
  `boot`.
- An interface is worth it when there is, or will be, a second
  implementation — and the test one counts.
- `$this->app->instance()` swaps the implementation in a test without
  touching the code.
- `app()` in the middle of the code is a *service locator*; *facades* are
  that with testing methods.
:::

:::checkpoint
You declare dependencies through the constructor, register in a provider
which implementation serves each interface, choose between `bind`,
`singleton` and `scoped` by the lifetime of the state, and swap an
implementation in a test without changing a single line of whoever uses it.
:::

:::exercise level=1
Say whether each registration should be `bind`, `singleton` or `scoped`:

1. The messaging provider's HTTP client, with a reusable connection.
2. An object that holds the request's authenticated user.
3. A stateless fine calculator, cheap to create.
4. The library's configuration reader, loaded from a file.

:::answer
1. `singleton`. Creating it costs, and reusing the connection is the goal.
2. `scoped`. It is, by definition, state of the current request. As a
   `singleton`, it would leak between requests in a worker.
3. No registration. It is a concrete class with no primitive dependencies,
   and autowiring resolves it on its own — with `bind` behavior.
4. `singleton`, **if** the content does not change while the process lives.
   If the configuration can change and the worker does not restart, the
   singleton will serve the old version until the next deploy.

Item 3 is the point of the exercise: most classes do not need to be
registered. A provider with fifty `bind`s of concrete classes is
configuration the container was already doing on its own.
:::

:::exercise level=2
This service works and cannot be tested without sending real e-mail.
Rewrite it with dependency injection and show the registration in the
provider.

```php
class ReturnReminder
{
    public function sendToOverdue(): int
    {
        $mailer = new SmtpMailer(
            env('SMTP_HOST'), env('SMTP_USER'), env('SMTP_PASS'),
        );

        $overdue = Loan::overdue()->with('reader')->get();

        foreach ($overdue as $l) {
            $mailer->send($l->reader->email, 'Return the book');
        }

        return $overdue->count();
    }
}
```

:::answer
```php title="app/Notices/ReturnReminder.php" numbered
final class ReturnReminder
{
    public function __construct(
        private readonly NoticeSender $notices,
    ) {}

    public function sendToOverdue(): int
    {
        $overdue = Loan::overdue()
            ->with('reader')
            ->get();

        foreach ($overdue as $l) {
            $this->notices->send(
                $l->reader,
                'Return the book',
            );
        }

        return $overdue->count();
    }
}
```

The registration already exists — it is the `NoticeSender` `bind` in
`NoticeServiceProvider`. `ReturnReminder` itself needs no registration at
all: it is concrete, and autowiring delivers the sender.

Three fixes came together, and the third is from another chapter: the
`env()` outside `config/`, which would return null after `config:cache`. It
disappeared because assembling the client disappeared from here — it went
to the provider, which reads from `config('notices')`.

And the channel switch came for free: the reminder now goes through the
library's sender, which today is WhatsApp, and not through an e-mail half
the readers do not have.
:::

:::exercise level=3
In production, the app started showing, rarely, another reader's name in the
loans screen's header. It cannot be reproduced on anyone's machine. The
project has, in a provider:

```php
$this->app->singleton(ReaderContext::class, function ($app) {
    return new ReaderContext(
        $app['request']->user()?->reader,
    );
});
```

Explain why the defect only appears in production, why it is rare, and fix
it. Then say what other symptom the same defect would produce in the queue
workers.

:::answer
**Why only in production.** In development, `php artisan serve` handles each
request in an environment where state does not survive between them in a
way noticeable to one person testing alone. In production, if the
application runs with a server that keeps the process alive between
requests, the singleton created on that process's first request **stays
there**. The next request, from another person, receives the
`ReaderContext` with the first one's reader.

**Why it is rare.** It depends on which process handles which request and
on who arrived first at each one. With many processes and little load, the
same person tends to land on processes they themselves "opened".

**The fix:**

```php
$this->app->scoped(ReaderContext::class, function ($app) {
    return new ReaderContext(
        $app['request']->user()?->reader,
    );
});
```

`scoped` is discarded at the end of each request and each job.

**In the queue workers:** the worker is a process that lives for hours and
runs thousands of jobs. A singleton with the first job's reader would make
the second job's return reminder go out with the name — or to the phone — of
the first reader. The defect on screen is embarrassing; in the queue, it is
a message to the wrong person, with someone else's data.
:::
