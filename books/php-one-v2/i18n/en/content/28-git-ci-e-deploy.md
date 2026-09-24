---
source_hash: 432000fd71a5
title: "Git, CI and deploy day"
number: 28
slug: git-ci-e-deploy
part: p7
kicker: "On the 31st of March, at seven in the morning, the folded paper with the FTP password left the project folder for the last time."
goal: >-
  Leave "works on my machine" behind: a history you can read, a pipeline
  that refuses what doesn't pass, an ordered deploy with migration, caches
  and worker in the right place, an honest health check — and, at the end,
  a new requirement implemented end to end, on your own.
---

## `.gitignore` before the first `git add`

The `casa-amarela/` project has been in a repository since chapter
@cap:primeiro-projeto-laravel, and Laravel came with a `.gitignore`. It
deserves to be read once, line by line, because each line is an incident
someone has already had:

```text title=".gitignore"
/vendor
/node_modules
/public/build
/public/storage
/storage/*.key
.env
.env.backup
.env.production
.phpunit.result.cache
```

**`/vendor`** is recreated by `composer install` from `composer.lock` — the
lesson from chapter @cap:do-include-ao-composer.

**`.env`** has the database password, the application key, the messaging
provider's token. It is the most important file on the list.

**`.env.backup`** and **`.env.production`** exist because someone, on some
project, made a copy of `.env` under another name "just to keep it", and the
copy went into the repository.

What **does** go into the repository is `.env.example`, with every key and
no real value. It is the documentation of which variables the application
needs, and it is what a new person copies on day one.

## A secret in the history is solved by changing the secret

The rule exists and, at some point, someone will break it. `.env` will get
into a commit, through a hurried `git add .`, before `.gitignore` is right.

The instinctive reaction is to delete the file and make another commit. It
does not solve it: Git keeps **the whole history**, and `.env` is still in
the previous commit, readable by anyone with access to the repository — and
by any copy of it that has already been made.

There are tools to rewrite history and remove the file from every commit.
They are useful and **are not the solution**, because they do not reach the
clones that already exist, the *forks*, the hosting service's cache, the
machine of the person who pulled the repository yesterday.

:::key
A secret that entered the history has leaked. The only fix is **changing the
secret**: generate a new password for the database, a new key for the
provider, revoke the token.

Rewriting history is cleanup. Changing the secret is the fix. In the right
order: first change, then clean.
:::

It is the same answer as chapter @cap:middleware's for the passwords that
went into the log, and chapter @cap:autenticacao's for the Sistema's
passwords. It repeats because the principle is a single one: a secret
someone else may have seen has stopped being a secret.

## A commit that tells a story

A project's history is read far more often than it is written, and almost
always by someone looking for **why** a line is the way it is.

```text
$ git log --oneline
a3f9c21 tweaks
7be4d02 wip
c01e8f5 fix
9d2a6b7 more tweaks
e44f1a0 now it works
```

Five commits, no information. Compare:

```text
$ git log --oneline
a3f9c21 Drop box return uses LoanPeriod
7be4d02 Test reproduces fine on early return
c01e8f5 Loan listing breaks ties by id
9d2a6b7 Last copy requires authorization, not refusal
e44f1a0 Limit of 5 loans in January
```

Each line says what changed, in the imperative or as a fact, in under
seventy characters. Whoever looks for why the drop box return changed in
February finds it in seconds — and the commit just below shows the test came
before the fix, as chapter @cap:testes asked.

For changes that need explaining, the commit body, after a blank line,
tells the why:

```text
Last copy requires authorization, not refusal

The rule was noted as "only w/ authoriz." and implemented
as a refusal. Corrected with Vera on 18 Feb. Authorization
records who authorized it and why, and also covers the
cases that used to be handled from memory at the counter.
```

:::note
Branches and review come in here in one sentence, because they are more a
team matter than a code one: each change is born on a branch, becomes a
*pull request*, and someone reads it before it enters the main branch. The
main branch is always publishable. Review is not for catching typos — the
pipeline does that — but for asking "why this way?", which only a person
asks.
:::

## The pipeline: Pint, PHPStan, tests

The continuous integration pipeline is a set of checks that runs on its own
at every *push*, on a clean machine, and says whether the code can go in.
For Casa Amarela, four:

```yaml title=".github/workflows/pipeline.yml" numbered
name: pipeline

on: [push, pull_request]

jobs:
  check:
    runs-on: ubuntu-latest

    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_DATABASE: casa_amarela_test
          MYSQL_ROOT_PASSWORD: test
        ports: ['3306:3306']
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=5s --health-retries=10

    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'
          coverage: none

      - run: composer install --no-interaction --prefer-dist

      - name: Style
        run: vendor/bin/pint --test

      - name: Static analysis
        run: vendor/bin/phpstan analyse --no-progress

      - name: No forgotten dd()
        run: "! grep -rnE '\\b(dd|dump|var_dump)\\(' app/"

      - name: Tests
        run: php artisan test --parallel
        env:
          DB_HOST: 127.0.0.1
          DB_PASSWORD: test
```

**Pint** checks code style — spacing, the order of `use` statements,
braces. With `--test`, it only reports, without changing anything. The
discussion about style leaves code review and goes to a tool, where it
offends nobody.

**PHPStan**, at the level 5 from chapter @cap:tipagem-estrita, reads the
code without running it and flags what doesn't add up: a method that doesn't
exist, a type that doesn't match, `null` where it can't be. For Laravel
projects, the Larastan extension teaches PHPStan to understand models and
*facades*.

**The search for `dd(`** is chapter @cap:cache-logs-e-medicao's rule, in one
line.

**The tests** run on **the same MySQL** as production — the service declared
at the top —, for the reason in chapter @cap:testes-de-feature-http-e-banco.

A red pipeline blocks the *merge*. It is not a recommendation: it is
repository configuration. The main branch only receives what passed.

## A production migration is a separate step

Deploying a Laravel application has an order, and the order exists because
each step depends on the previous one:

```bash title="deploy.sh" numbered
#!/usr/bin/env bash
set -euo pipefail

cd /var/www/casa-amarela

git fetch --tags
git checkout "$1"

composer install --no-dev --optimize-autoloader

php artisan down --retry=15

php artisan migrate --force

php artisan config:cache
php artisan route:cache
php artisan view:cache

php artisan queue:restart

php artisan up
```

`set -euo pipefail` makes the script **stop at the first error**. Without
it, a migration that fails is followed by `config:cache` and `up`, and the
application comes back online with the database half done.

`$1` is the version — a Git *tag*, like `v1.0.0`. The deploy publishes a
named version, not "whatever is on the main branch right now". Going back is
running the same script with the previous *tag*.

`--no-dev` does not install Telescope, Pest or Debugbar.
`--optimize-autoloader` generates the class map from chapter
@cap:namespaces-e-autoload, which the production autoloader uses instead of
looking for a file for every class.

The migration is a **separate, single** step: it runs once, in one place.
When the application grows and starts running on five servers, the
temptation is to put `migrate` at the start of each one — and the five
machines try to alter the same table at the same time. `migrate`'s
`--isolated` locks execution so that only one runs, and the rule still
holds: migrating is a deploy step, not part of each machine's startup.

:::pitfall
`--force` exists because Laravel, in production, **asks before migrating**,
and a script does not answer questions. It is necessary in the script and
dangerous outside it: typed by hand, in the wrong terminal, with the wrong
`.env`, it is the Thursday `migrate:fresh` from chapter
@cap:migrations-seeders-e-factories under another name.

A deploy is a script, versioned, reviewed. Nobody runs a production
migration by typing.
:::

## `down`, caches and the worker that needs restarting

`artisan down` puts the application in maintenance: every request gets
`503` with the `Retry-After` header, and the reader app shows "under
maintenance, come back in a few minutes". It exists so that nobody makes a
loan **during** the migration, with half the columns in the old format.

The three caches come **after** the migration and the new code, because they
freeze whatever exists at that moment — chapter @cap:cache-logs-e-medicao
explained what happens when they run before. And they come **before** `up`,
so the first request already finds everything ready.

`queue:restart` is the most forgotten step and the one chapter
@cap:events-jobs-e-filas asked not to forget: without it, the worker keeps
yesterday's code in memory, and the notices go out with the old text — or
break, looking for the column today's migration renamed.

:::note
Deploying **without** taking the application offline exists, and it has a
name: *zero downtime*. The most common technique is to prepare the new
version in a folder alongside, with everything ready, and switch a symlink
from one to the other in an instant.

What it requires is that **both versions work with the same database** at
the same time — which forces migrations to follow the expand and contract
from chapter @cap:migrations-seeders-e-factories: add first, remove in a
later deploy. It is more work on every migration. For a library that opens
at nine, one minute of maintenance at seven in the morning is the honest
choice.
:::

## Health check: alive is not the same as ready

Chapter @cap:primeiro-projeto-laravel introduced `/up`, which Laravel ships
ready-made. It responds `200` if the application can serve a request. It is
a useful question — **is the process alive?** — and not the only one.

The application can be alive and without a database. Alive and with a full
disk. Alive and with the queue stuck for six hours. `/up` responds `200` in
all three cases.

```php title="app/Http/Controllers/ReadyController.php" numbered
public function __invoke(): JsonResponse
{
    $checks = [
        'database' => $this->tries(fn () => DB::select('SELECT 1')),
        'cache' => $this->tries(fn () => Cache::put('ready', 1, 5)),
        'queue' => $this->tries(fn () => $this->queueMoving()),
        'disk' => $this->tries(fn () => $this->diskHasRoom()),
    ];

    $ok = !in_array(false, $checks, true);

    return response()->json(
        ['ready' => $ok, 'checks' => $checks],
        $ok ? 200 : 503,
    );
}

private function queueMoving(): bool
{
    $oldest = DB::table('jobs')->min('created_at');

    return $oldest === null
        || now()->diffInMinutes($oldest) < 15;
}
```

| Route | Question | Who asks |
|---|---|---|
| `/up` | does the process respond? | the load balancer, every few seconds |
| `/ready` | can it do the work? | monitoring, every minute |

Table: The first should be cheap and depend on nothing. The second may query
the database, and that is why it is not called every two seconds.

`/ready` does not tell **what** broke to whoever should not know: it sits
behind a monitoring token, or answers just `200` and `503` to the world and
the detail to whoever authenticates. The lesson from chapter
@cap:erros-padronizados applies to it too.

## The list before publishing

A short list, checked the day before, by a person with the list in hand —
and not from memory:

- `APP_ENV=production` and `APP_DEBUG=false`.
- `APP_KEY` generated **on the server**, different from development's.
- HTTPS with a valid certificate, and HTTP redirecting to HTTPS.
- The server's `.env` outside the repository, readable only by the
  application's user.
- Permissions on `storage/` and `bootstrap/cache/` as in chapter
  @cap:primeiro-projeto-laravel.
- Worker under a supervisor, restarting on deploy.
- Scheduler in `cron`: `* * * * * php artisan schedule:run`.
- Logs in JSON, with rotation, and no sensitive fields — checked with a
  search.
- `/ready` being polled by monitoring, with an alert to someone.
- A daily database backup **and a tested restore**.

The last item is the only one that deserves explanation, because it is the
one most often skipped. A backup that has never been restored is a
hypothesis. The file may be corrupt, incomplete, encrypted with a key nobody
has, or be the backup of another database. The only way to know is to
restore it on a separate machine and open the collection.

Nonato ran an `UPDATE` without a `WHERE` on a Friday in 2013, in chapter
@cap:sql-do-zero, and that is why there has been a daily backup ever since.
What nobody had done, in thirteen years, was restore one.

:::warning
Docker enters this list only where it adds something. For Casa Amarela — one
application, one database, one worker, one server —, a server with PHP,
MySQL and supervisor installed is simpler to understand, maintain and fix at
seven in the morning. Docker makes sense when there are many applications on
the same machine, environments that are hard to reproduce, or a team that
already operates everything that way. Adopting it "because it's
professional" is chapter @cap:primeiro-projeto-laravel's mistake, with more
parts.
:::

:::story The folded paper
At seven in the morning on the 31st, Márcia took out of the project folder
the folded paper Seu Juvenal had handed over in October. Username, password,
and in the corner, in a different-colored pen: *"don't touch the old
folder"*.

The new system was going to a new server. The paper was for the last thing
that still needed doing on the old hosting: take a final copy of the Sistema
and replace the home page with a notice pointing to the new address.

Nonato took the paper, read it, and stood still for a while.

— That handwriting is mine.

— The password? — asked Tainá.

— The "don't touch the old folder". I wrote that in 2011. The old folder was
the 2009 version, which I left there in case the new one had problems.

— And did it?

— No. But I never had the nerve to delete it.

Dedé ran the deploy script. `down`, `migrate`, three caches,
`queue:restart`, `up`. Four minutes. `/ready` responded `200` with four
`true`s.

Dedé's phone buzzed. Rejane: *"Congrats on the ownership on this
go-live!!! Your promotion was approved for the April cycle."* He read it
twice and put the phone away without replying.

Nonato logged into the old hosting over FTP, downloaded both folders — the
old one and the 2011 one —, checked the file sizes twice and replaced
`index.php` with a page containing one sentence and an address.

— Done — he said. — Fifteen years.

— Half a million loans — said Tainá. — I counted. No collection lost.

Nonato folded the paper again, along the same creases.

— Can I keep this?

Márcia looked at him, then at the paper.

— The password still works.

— Then change the password — said Dedé. — After that, he keeps it.
:::

:::art caption="Fifteen years, half a million loans and a folded paper."
src="quinze-anos-meio-milhao-de-emprestimos-e-um-papel-dobrado.png"
Minimalist editorial illustration on a white background, a more restrained
tone: a developer of about forty, in a plaid shirt, carefully holds a paper
folded in four, with a handwritten note in one corner in a different-colored
pen. Behind him, an old CRT monitor shows a gray screen with a form, and
next to it a new monitor shows a clean screen with a green check mark.
Standing around, a manager with a folder, a younger developer putting his
phone in his pocket without looking, and an intern with an open notebook,
all looking at the paper. Few elements, subtle and affectionate humor,
tech-magazine aesthetic.
:::

## The first request after launch

The system is live. And, like every live system, it gets its first new
request the same week — the first of a queue that Part 8 starts to serve.

Vera wants to be able to **forgive a fine**. There are cases — a flood, an
illness, a book returned wet from the December rain — in which she decides
the person should not pay. Today, she notes it in her notebook and does not
charge, and the end-of-month report shows a debt that does not exist.

This request is yours. It cuts across almost everything this book has
built, and the guide below says **where** each part lives — not **how** to
write it:

| Layer | What to decide | Chapter |
|---|---|---|
| route | `POST /fines/{fine}/forgiveness`, and why not `DELETE` | @cap:o-que-e-uma-api-rest |
| Form Request | the `reason` is required, with a minimum length | @cap:validation-e-form-requests |
| policy | who can forgive — and whether a clerk can | @cap:autorizacao |
| service | a fine already paid or forgiven cannot be forgiven | @cap:services |
| exception | the `409`'s `type` | @cap:erros-padronizados |
| event | `FineForgiven`, after the commit | @cap:events-jobs-e-filas |
| queue | notify the reader, only once | @cap:events-jobs-e-filas |
| resource | does the fine show it was forgiven, and by whom? | @cap:api-resources |
| tests | the rule in unit tests, the `403` in feature tests | @cap:testes |
| documentation | the new `type` in the error table | @cap:documentacao-da-api |

Table: Ten decisions, and none of them is about typing. Each layer's code has
between five and thirty lines.

Two questions have no technical answer, and need to be asked to Vera before
the first line. **Should the reader see the reason for the forgiveness?** —
"flood" maybe yes, "financial situation" maybe not. **Is there an amount
above which only the admin forgives?** The answer will change the policy, and
it is the kind of rule that only appears when someone asks.

:::milestone
End of Part 7. Casa Amarela is live: a collection with search, filtering and
pagination; loans with Vera's eleven rules in a service she can read;
authentication and per-resource authorization; errors in a single format;
notices through the queue, without repeats; caching where it doesn't lie;
tests that prove the rule and the contract; documentation generated from the
code; and a deploy that is a script.

The 2009 Sistema is in a folder, with two copies, and nobody deleted it. And
the new system has just met the thing no test environment simulates: real
people using it.
:::

:::summary
- `.gitignore` is a list of incidents; `.env.example` goes in, `.env` never
  does.
- A secret in the history has leaked: first change it, then clean up.
- A commit says what changed in one line and why in the body.
- The pipeline checks style, static analysis, forgotten `dd()`s and tests on
  production's MySQL, and blocks the *merge*.
- The deploy is a script that stops at the first error, publishes a *tag*,
  and follows the order: code, `down`, `migrate`, caches, `queue:restart`,
  `up`.
- A migration runs once, in one place, and is never typed by hand.
- `/up` says the process is alive; `/ready`, that it can work.
- The pre-publishing list is checked with the list in hand; a backup only
  counts once it has been restored.
- A new requirement cuts across route, validation, policy, service,
  exception, event, queue, resource, tests and documentation — and starts
  with two questions to whoever does the work.
:::

:::checkpoint
The application is live with the list completed, the pipeline blocks what
doesn't pass, the deploy is a versioned script you can explain step by step,
and fine forgiveness is implemented end to end — by you, on your own, with a
test for each decision.
:::

:::exercise level=1
Put the deploy steps in the right order and say what goes wrong if the
marked step is out of place:

`queue:restart` · `migrate --force` · `up` · `config:cache` ·
`composer install --no-dev` · `down` · `git checkout v1.4.0`

:::answer
1. `git checkout v1.4.0`
2. `composer install --no-dev`
3. `down`
4. `migrate --force`
5. `config:cache` (and the other two caches)
6. `queue:restart`
7. `up`

**`config:cache` before `checkout`:** freezes the previous version's
configuration; the new key in `.env` or `config/` doesn't get in.

**`migrate` before `down`:** during the migration, the application serves
with the database half done — a loan made in that minute may be written in
the old format or fail.

**`queue:restart` forgotten:** the worker runs yesterday's code until
someone restarts it, or until `--max-time` expires.

**`up` before the caches:** the first requests find the old cache or none,
and are slow or wrong for a few seconds.
:::

:::exercise level=2
The new person on the team did `git add .` and a `push` with the production
`.env`. The repository is private, with six people who have access. Write, in
order, what to do in the next hour.

:::answer
1. **Change the secrets**, starting with those that give the most access: the
   database user's password, the messaging provider's key, any external
   service token. Update the server's `.env` and run `config:cache`.
2. **Change the `APP_KEY`** — carefully: it encrypts sessions and cookies,
   and changing it logs out whoever is signed in to the panel. At a library,
   at seven in the morning, that is acceptable; in other systems, it needs a
   plan.
3. **Remove the file** from the repository in a new commit, and add it to
   `.gitignore` if it wasn't there.
4. **Rewrite the history**, if the team decides to, telling the six people
   to clone again.
5. **Check `.gitignore`** and the person's editor configuration, to
   understand how the file got through.

And a sixth, which is not technical: treat it as an accident, not a fault.
The person who hides the next mistake because they were exposed over this
one is the bigger risk. Step 5 is about the process that let it through, not
about who typed it.
:::

:::exercise level=3
Implement the fine forgiveness described in the section "The first request
after launch". Use the layers table as a guide and the two questions to Vera
as a starting point — decide the answers and write them in a comment at the
top of the service.

When you finish, answer: which of the ten decisions would you change if Vera
answered the second question differently, and how many files would that
change touch?

:::answer
There is no single answer, and a complete solution has between eight and
twelve files. The points a good solution gets right:

**Route:** `POST /fines/{fine}/forgiveness`, and not `DELETE /fines/{fine}`
— the fine does not cease to exist; it gets an outcome. The history needs to
show there was a fine and that it was forgiven. It is the same reason as the
`POST /loans/{id}/return` from chapter @cap:o-que-e-uma-api-rest.

**Service:** `FineService::forgive(int $fineId, Authorization $a)`, with a
transaction and a lock, throwing `FineAlreadySettled` if it is already paid
or forgiven. The `Authorization` from chapter @cap:services comes back:
forgiveness is judgment, and judgment is recorded.

**Policy:** `FinePolicy::forgive`, asking about a `ForgiveFine` permission —
not about the role.

**Event and queue:** `FineForgiven` with `ShouldDispatchAfterCommit`, and a
listener that notifies the reader with a `unique` record in `sent_notices`.

**Tests:** the "doesn't forgive twice" rule in a unit test; the `403` for a
reader and the `201` for whoever has the permission in feature tests; the job
run twice with a single message.

**About the final question.** If Vera answers that fines above, say,
R$ 50 can only be forgiven by the admin, the change lives **in one place**:
`FinePolicy::forgive` starts receiving the fine and comparing the amount.
One code file and a new case in the feature test's dataset.

If your answer touched more files than that — if the limit showed up in the
service **and** the policy, or in the Form Request —, it is worth going back
and asking where the rule lives. It is the question the whole book asked,
chapter by chapter, and it is the one you will ask, from now on, without it.
:::
