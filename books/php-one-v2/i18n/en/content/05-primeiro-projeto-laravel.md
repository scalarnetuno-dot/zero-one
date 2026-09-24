---
source_hash: cf5a05017d71
title: "The first project"
number: 5
slug: primeiro-projeto-laravel
part: p2
kicker: "Mr. Juvenal saw the welcome screen, read the framework's name in big letters and asked whether he could start registering the books."
goal: >-
  Create the Casa Amarela project with Laravel, understand the role of each
  top-level folder, know what `.env` holds and why it does not go to Git,
  and get the first route to answer.
---

:::story Is it ready yet?
Dedé projected the screen onto the wall of the association's room to show
that the environment was up. Light background, the framework's name in the
middle, a few documentation links around it.

Mr. Juvenal looked at it for a few seconds.

"Pretty. Is it ready yet?"

"That's the screen that comes out of the box."

"But the system's name is there."

"The framework's name is there."

Mr. Juvenal pointed at the wall with his chin, the way Vera points at the
monitor.

"As far as I'm concerned, it says it works."
:::

## `composer create-project`

One command creates the whole project:

```text
$ composer create-project laravel/laravel casa-amarela
```

```text
Creating a "laravel/laravel" project at "./casa-amarela"
Installing laravel/laravel (v12.0.0)
Created project in /home/dede/casa-amarela

> @php -r "file_exists('.env') || copy('.env.example', '.env');"

Loading composer repositories with package information
Updating dependencies
Package operations: 107 installs, 0 updates, 0 removals
  - Installing symfony/polyfill-mbstring (v1.31.0)
  - Installing illuminate/support (v12.0.0)
  ...
Generating optimized autoload files

> @php artisan key:generate --ansi

   INFO  Application key set successfully.
```

One hundred and seven packages. That is a lot more than `var-dumper`'s
three, and the difference is what the previous chapter listed: queues,
e-mail, sessions, validation, console, cache and the rest.

Notice the last two lines, because they are not installation: they are the
project getting itself ready. `.env` was created from `.env.example`, and an
application key was generated. You will hear about both in five minutes.

## The route that answers in two minutes

```text
$ cd casa-amarela
$ php artisan serve
```

```text
   INFO  Server running on [http://127.0.0.1:8000].

  Press Ctrl+C to stop the server
```

Open `routes/web.php` and add four lines:

```php title="routes/web.php" numbered
Route::get('/health', function () {
    return [
        'status' => 'ok',
        'time' => now()->toIso8601String(),
    ];
});
```

```text
$ curl -s localhost:8000/health
{"status":"ok","time":"2026-01-13T09:41:12-03:00"}
```

Three things happened without you asking.

The route returned an **array**, and JSON arrived. Laravel converts arrays
and objects automatically, and already sends the right `Content-Type`.

`now()` exists without any `use`. It is one of the convenience functions the
framework registers globally — and it returns a date object, not text.

And the address is `/health`, not `/health.php`. The front controller from
chapter @cap:um-framework-de-quarenta-linhas is there, in
`public/index.php`, doing exactly what yours did.

:::trivia
The skeleton already comes with a health route, at `/up`, configured in
`bootstrap/app.php`. It exists for the monitoring service to hit and find
out whether the application is alive.

This chapter's `/health` is yours, so you can see the route working. In a
real project, whoever answers the monitoring is `/up`.
:::

## The folders that matter

The project has twelve top-level folders. Six of them you will open every
day.

:::tree title="What exists after create-project"
casa-amarela/
  app/          # your code
  bootstrap/    # app.php assembles the application; cache/ is generated
  config/       # one file per subject
  database/     # migrations, seeders and factories
  public/       # index.php and files served directly
  resources/    # Blade views, source CSS and JS
  routes/       # web.php and console.php
  storage/      # logs, cache, uploaded files, sessions
  tests/
  vendor/       # Composer's, outside Git
  .env          # this machine's configuration, outside Git
  artisan       # the project's terminal command
:::

Three deserve a paragraph now.

**`app/`** starts almost empty: a base controller, a user model and a
provider. That is on purpose — Laravel does not guess your architecture, and
the folders you create in here are your decision.

**`storage/`** is the only folder the application **writes** to. Logs, the
views' compiled cache, sessions and uploads live here. It is also the source
of almost everyone's first error.

**`public/`** is the only one the web server should see. Everything outside
it — `.env`, `vendor/`, your code — is unreachable from the internet, and
that is what separates this project from the System's folder, where the 2019
backup could be downloaded by anyone.

## The first permission error

Sooner or later, and always on the server:

```text
The stream or file "/var/www/casa-amarela/storage/logs/laravel.log"
could not be opened in append mode: Failed to open stream:
Permission denied
```

The cause is always the same: whoever runs PHP on the server is not you. It
is a system user — `www-data` on Debian and Ubuntu, `nginx` or `apache` on
other distributions — and it needs to be able to write to two folders.

```text
$ sudo chown -R www-data:www-data storage bootstrap/cache
$ sudo chmod -R 775 storage bootstrap/cache
```

:::pitfall
The recipe that shows up on forums is `chmod -R 777 storage`. It works, and
it means "any user on the server can write here".

On a shared server, that includes the other sites hosted on the same
machine. On a server of your own, it includes any process an intruder
manages to run as any user.

`775` with the right owner solves the same problem and does not open the
door. The difference between the two commands is ten seconds to type and
years to find out that was the way in.
:::

## `.env`: this machine's configuration

```text title=".env"
APP_NAME="Casa Amarela"
APP_ENV=local
APP_KEY=base64:0sT3qk9... 
APP_DEBUG=true
APP_URL=http://localhost

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=casa_amarela
DB_USERNAME=root
DB_PASSWORD=secret
```

`.env` holds what **changes from machine to machine**: the database address,
the password, whether errors show on screen, where e-mails go. Your machine
has one, the server has another, and the two are never the same.

Three rules, and all three have consequences.

**`.env` does not go into Git.** It already comes in the skeleton's
`.gitignore`. What goes in is `.env.example`, with the same keys and no
values — it is what tells whoever clones the project what needs filling in.

**`APP_KEY` is used for encryption.** Sessions and encrypted data depend on
it. Changing the key on a live system drops every open session; running
without it raises an error on the first request that needs encryption. It is
generated once, per environment, and kept with the passwords.

**`APP_DEBUG=true` never goes to production.** With it on, an error returns
Laravel's diagnostic page — which shows the code snippet, the variables'
values and, depending on the point, the contents of `.env` itself.

:::key
From Laravel 11 on, the default database in `.env.example` is SQLite,
because it works without installing anything.

The Casa Amarela project has had a MySQL since chapter
@cap:do-arquivo-ao-banco, with four tables and data inside. Switch to
`mysql` and point it at the database that already exists.
:::

## Serving the project: pick one

Four ways show up in the documentation, and the only wrong decision is trying
all four on day one.

| Way | When it fits |
|---|---|
| `php artisan serve` | now, and for the whole book |
| Laravel Sail | when the team needs the same environment |
| Valet | macOS, several projects at once |
| your own Docker | when production is already Docker |

Table: `artisan serve` is PHP's built-in server with the project's routes.
It is no good for production and perfectly good for learning.

:::pitfall
The day-one temptation is to start with Docker, "because that's how it's
done professionally". It usually is, and on day one the result is two hours
debugging volumes, permissions and networking — none of which has anything
to do with PHP.

A container solves a real problem: making your machine look like the server.
That problem shows up when there is a server and there is a team. Before
that, it is just one more problem.
:::

## What `index.php` does

It is worth opening the file, because it has twelve lines and you already
know nine of them:

```php title="public/index.php" numbered
<?php

use Illuminate\Foundation\Application;
use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

require __DIR__.'/../vendor/autoload.php';

$app = require_once __DIR__.'/../bootstrap/app.php';

$app->handleRequest(Request::capture());
```

Composer's autoload, the application assembled by `bootstrap/app.php`, the
request captured from the superglobals and handed over. After that come the
layers, the router, your code and the response — the previous chapter's
diagram, with grown-up names.

:::tree title="Where we are now"
casa-amarela/
  .env              # with the project's MySQL, outside Git
  .env.example      # the same keys, no values
  bootstrap/app.php
  public/index.php
  routes/web.php    # with GET /health answering
:::

:::summary
- `composer create-project laravel/laravel` creates the skeleton, copies
  `.env` and generates the `APP_KEY`.
- A route that returns an array becomes JSON with the right header, with no
  manual conversion.
- `app/` starts almost empty on purpose; the internal architecture is yours.
- `storage/` and `bootstrap/cache/` need to be writable by the web server's
  user — with `775` and the right owner, not with `777`.
- `public/` is the only folder the web server sees; `.env` and `vendor/` stay
  out of the internet's reach.
- `.env` holds what changes per machine; it stays out of Git and
  `.env.example` goes in its place.
- `APP_KEY` encrypts sessions and data; `APP_DEBUG=true` in production shows
  code and configuration on screen.
- `php artisan serve` is enough to learn; Docker solves a problem that does
  not exist yet on day one.
:::

:::checkpoint
You create a Laravel project, start the server, write a route that answers
in JSON, explain the role of each top-level folder and can say why `.env`
does not go into the repository and what `APP_KEY` protects.
:::

:::exercise level=1
A colleague cloned the project's repository and got, on the first request:

```text
No application encryption key has been specified.
```

Say what happened, which command fixes it and why this error cannot be
avoided by committing `.env`.

:::answer
`.env` did not come along — and it should not have. Without it, there is no
`APP_KEY`.

```text
$ cp .env.example .env
$ php artisan key:generate
```

Committing `.env` would "fix" the error and create three worse problems. The
production database password would go into the repository, where it stays
forever in the history even after being removed. Every environment would
start using the same encryption key. And each person on the team would
overwrite the others' database address with every `git pull`.

`.env.example` exists exactly for this: it carries the **keys** without the
**values**, and the error above is the reminder that a ten-second step is
missing.
:::

:::exercise level=2
Add three pieces of information useful to whoever monitors to `/health`: the
PHP version, whether the application is in debug mode and whether the
database responds.

Watch what you expose: the route is public.

:::answer
```php title="routes/web.php" numbered
Route::get('/health', function () {
    try {
        DB::connection()->getPdo();
        $database = 'ok';
    } catch (\Throwable $e) {
        $database = 'failed';
    }

    return response()->json([
        'status' => $database === 'ok' ? 'ok' : 'degraded',
        'php' => PHP_VERSION,
        'debug' => config('app.debug'),
        'database' => $database,
    ], $database === 'ok' ? 200 : 503);
});
```

The care the question asks for is in two decisions.

**The `catch` does not return the exception's message.** The trace of a
connection failure contains host, user and sometimes password — and this
route is public. Whoever monitors needs to know it failed; whoever
investigates looks at the log.

**The status changes along with it.** Returning `200` with
`"status":"degraded"` forces the monitoring to interpret the body. `503` is
read by any tool with no configuration at all.

A debatable decision, left in on purpose: exposing `PHP_VERSION` on a public
route tells an attacker which version to go after. In production, the common
choice is either to protect the route or to return only `status`, leaving
the detail for an internal route.
:::

:::exercise level=3
Casa Amarela's deploy is done by copying the project folder to the server.
On the first attempt, the application came up and the page broke with a
permission error in `storage/logs`.

The intern ran `chmod -R 777 storage` and it worked.

Write what you would say in the review: why it worked, what the concrete risk
is, what the fix is, and how to stop the folder from being copied with the
wrong owner again on the next deploy.

:::answer
**Why it worked.** `777` gives write permission to everyone, which includes
the user running PHP. The error goes away because the problem — the wrong
owner — stopped mattering.

**The concrete risk.** Any process on the server can now write to
`storage/`. On shared hosting, that includes the machine's other sites. And
`storage/` does not only hold logs: it holds sessions and the compiled Blade
views, which are **PHP files the application executes**. Write permission
there is execute permission by extension.

**The fix.** The right owner and group permission:

```text
$ sudo chown -R www-data:www-data storage bootstrap/cache
$ sudo chmod -R 775 storage bootstrap/cache
```

**How not to repeat it.** The underlying problem is not the permission: it
is deploying by copying the folder, which resets the owner every time and
depends on someone remembering to fix it. Two ways out, in order of effort.

The cheap one: put both commands in the publishing step, so they always run,
without depending on memory.

The right one: do not copy `storage/` on deploy. It holds state — logs,
sessions, uploads — and state is not part of the code. The common path is to
keep it outside the versioned folder and point to it, so the deploy swaps
only the code and touches nothing the application has written.
:::
