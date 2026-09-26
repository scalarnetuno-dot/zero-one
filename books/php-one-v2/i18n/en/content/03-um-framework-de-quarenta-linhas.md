---
source_hash: 0e5d4ae2e609
title: "A forty-line framework"
number: 3
slug: um-framework-de-quarenta-linhas
part: p1
kicker: "After writing the router, the intern's question was the best one in the project: why not just use this one?"
goal: >-
  Write by hand the minimum of a framework — front controller, router,
  container and middleware — so you can explain a request's life cycle in
  any PHP framework, pointing out where each piece comes in.
---

:::story Twenty minutes
The `public/` folder, empty at the end of volume 1, had nineteen `.php`
files two weeks later, and the address of every screen ended in one of them.

"That becomes `/lend.php?accession=2117`," said Tainá. "Is the app going to
consume it like that?"

"No. It becomes `POST /loans`."

"And how?"

Dedé pulled the keyboard over and started typing. Twenty minutes later there
was a file with forty-odd lines, and the library's three routes answered in
JSON.

Tainá read the whole file, top to bottom, without interrupting.

"OK. Why don't we just use this one?"
:::

## One file per page

The Casa Amarela project grew in the most natural way in the world: one
screen, one file. It is how PHP was made to work, and it is the reason the
language conquered the web.

Three things break once the project goes past a dozen files.

**The address becomes a map of the disk.** `/lend.php` tells whoever is
outside how the folder is organized, and ties the URL to the file's name.
Renaming becomes a contract change.

**Every file repeats the beginning.** Connection, autoload, response header,
credential check. Nineteen times, and on the day one of them changes,
nineteen places to remember.

**There is no place for what applies to everyone.** Recording how long each
request took, refusing whoever is not authenticated, returning JSON when the
program breaks: each of these is a line that would need to be in all
nineteen files.

## Front controller: a single door

The way out is old and has a name: **every request comes in through the same
file**, which decides what to do.

```text
before                         after
/lend.php?accession=2117       POST /loans
/list.php                      GET  /books
/receipt.php?id=4471           GET  /loans/4471/receipt
                               ↓
                               everything comes in through index.php
```

For the server to hand everything to a single file, it needs an instruction.
In Apache, it is a configuration file in the public folder:

```text title=".htaccess"
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^ index.php [L]
```

The last two lines say: if the requested path is **not** a file that exists
— an image, a CSS file — send it to `index.php`. That is why every modern PHP
project has a `public/` folder with almost nothing in it: just `index.php`
and the files that really should be served directly.

With PHP's built-in server, the same thing is done on the command line:

```text
$ php -S localhost:8000 mini.php
```

## A router in twenty lines

With everything coming in through one door, what is left is deciding where
it goes. Two classes, and the first has three lines:

```php title="mini.php" numbered
<?php

declare(strict_types=1);

final class Response
{
    public function __construct(
        public readonly int $status,
        public readonly array $body,
    ) {}
}
```

```php title="mini.php" numbered
final class Router
{
    public function __construct(private array $routes) {}

    public function dispatch(
        string $method,
        string $path,
    ): Response {
        foreach ($this->routes as [$verb, $pattern, $action]) {
            if ($verb !== $method) {
                continue;
            }

            $regex = '#^' . preg_replace(
                '#\{(\w+)\}#',
                '(?<$1>[^/]+)',
                $pattern,
            ) . '$#';

            if (preg_match($regex, $path, $matches) === 1) {
                $params = array_filter(
                    $matches,
                    'is_string',
                    ARRAY_FILTER_USE_KEY,
                );

                return $action(...array_values($params));
            }
        }

        return new Response(404, ['error' => 'Route not found']);
    }
}
```

The loop is simple; the only line that deserves attention is the one that
builds the regular expression. It swaps `{id}` for a named group that
matches anything that is not a slash. `/books/{id}` becomes
`#^/books/(?<id>[^/]+)$#`.

After the match, `$matches` holds the pieces twice: with a numeric index and
with the name. The `array_filter` with `ARRAY_FILTER_USE_KEY` keeps only the
named ones — and they become the route function's arguments.

:::term Dispatch
Choosing which code runs for a request and calling it. It is the only thing a
router does, and it is the piece every framework has in the middle.

A route table on one side, a request on the other, a function at the end.
:::

The route table is an array, and each row has a verb, a pattern and what to
do:

```php title="mini.php" numbered
$catalog = [
    12 => ['title' => 'Dom Casmurro', 'year' => 1899],
    31 => ['title' => 'Vidas Secas', 'year' => 1938],
];

$routes = [
    ['GET', '/books',
        fn(): Response => new Response(200, $catalog)],

    ['GET', '/books/{id}',
        function (string $id) use ($catalog): Response {
            $id = (int) $id;

            if (!isset($catalog[$id])) {
                return new Response(404, [
                    'error' => "Book {$id} doesn't exist",
                ]);
            }

            return new Response(200, ['id' => $id] + $catalog[$id]);
        }],

    ['POST', '/loans',
        fn(): Response => new Response(201, ['id' => 4471])],
];
```

And the front controller, which is the end of the file, has six lines:

```php title="mini.php" numbered
function send(Response $r): void
{
    http_response_code($r->status);
    header('Content-Type: application/json');
    echo json_encode($r->body, JSON_UNESCAPED_UNICODE);
}

$router = new Router($routes);

send($router->dispatch(
    $_SERVER['REQUEST_METHOD'],
    parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH),
));
```

Start it up and try it:

```text
$ php -S localhost:8000 mini.php
```

```text
$ curl -s localhost:8000/books/31
{"id":31,"title":"Vidas Secas","year":1938}

$ curl -s localhost:8000/books/99
{"error":"Book 99 doesn't exist"}

$ curl -s localhost:8000/nothing
{"error":"Route not found"}
```

:::key
Notice what the router is **not**: a giant `switch` with `$_SERVER` inside.

The difference is not aesthetic. A `switch` mixes the routing decision with
each route's work, and grows along with both. Here the decision lives in a
class that knows nothing about books, and the work lives in a table that
knows nothing about regular expressions.

Swapping the router for another touches no route at all. That separation is
what makes the word "framework" mean something.
:::

## The naive container

The project has classes that depend on others: a loan service needs a
repository, which needs a connection. Building that by hand in every route is
the usual repetition:

```php
$service = new LoanService(
    new BookRepository(
        new Connection()
    )
);
```

The `Services` from chapter @cap:como-organizar-um-projeto-php solved this
with a hand-written factory for each class — and exercise 2 of that chapter
already pointed out what is mechanical about factories: read the
constructor, ask for each type, pass them in order. A container that reads
the constructor on its own makes the factories unnecessary. Fifteen lines
solve it for good:

```php title="mini.php" numbered
final class Container
{
    private array $built = [];

    public function get(string $class): object
    {
        if (isset($this->built[$class])) {
            return $this->built[$class];
        }

        $constructor = (new ReflectionClass($class))
            ->getConstructor();

        $arguments = [];

        foreach ($constructor?->getParameters() ?? [] as $p) {
            $type = $p->getType();

            if (!$type instanceof ReflectionNamedType
                || $type->isBuiltin()) {
                throw new RuntimeException(
                    "Don't know how to build \${$p->getName()}"
                );
            }

            $arguments[] = $this->get($type->getName());
        }

        return $this->built[$class]
            = new $class(...$arguments);
    }
}
```

`ReflectionClass` is the part of PHP that lets a program **look at its own
code**: which methods a class has, which parameters a method receives, what
type each one is. The container uses it to read the constructor's parameter
list and resolve each one, recursively.

```php
$c = new Container();

$service = $c->get(LoanService::class);
```

```text
  (connection created)
```

One line, and the whole chain has been built. Ask again:

```php
$other = $c->get(LoanService::class);

var_dump($service === $other);
```

```text
bool(true)
```

No new connection. The container keeps what it has already built, and that
is why a single `Connection` serves the whole program without anyone passing
`$pdo` from function to function.

:::pitfall
The container above is naive on purpose, and its limit shows up fast:

```text
Don't know how to build $status
```

It only knows how to resolve parameters that are **classes**. An `int`, a
`string` or a setting coming from a file cannot be guessed — someone has to
say what goes there.

Remembering that sentence is worth more than the code: when a framework
complains that it cannot resolve a dependency, it is almost always this. A
parameter that is not a class, or an interface nobody has said which
implementation to use for.
:::

## Middleware: the onion before it had a name

What is missing is the place for what applies to every route. The idea is to
wrap the action in layers: each layer receives the request, does its part,
calls the one inside and still sees the response on its way back out.

```php title="mini.php" numbered
$action = fn(string $req): string => "[action:{$req}]";

$middlewares = [
    fn(string $req, callable $next): string
        => 'log(' . $next($req) . ')',

    fn(string $req, callable $next): string
        => 'auth(' . $next($req) . ')',
];

$pipeline = array_reduce(
    array_reverse($middlewares),
    fn(callable $next, callable $current): callable
        => fn(string $req): string => $current($req, $next),
    $action,
);

echo $pipeline('GET /books'), "\n";
```

```text
log(auth([action:GET /books]))
```

The output **is** the diagram. `log` wraps `auth`, which wraps the action.
The request goes in from the outside inwards and the response comes out from
the inside outwards, passing through the same layers in reverse order.

The `array_reduce` with the reversed list is what builds this nesting doll.
Each step takes what has already been built — the "next" — and wraps it in
the current layer.

And the practical gain shows up when a layer decides **not** to call the
next one:

```php
fn(string $req, callable $next): string
    => authenticated($req) ? $next($req) : '401',
```

Then the action never runs. That is how authentication, rate limiting and
permission refusals work in every PHP framework — and from here on none of
them needs to explain the mechanism to you.

## What is still missing

The file has about a hundred lines counting everything, and serves three
routes. It is worth listing, without hurry, what it does not do:

| Missing | What goes wrong without it |
|---|---|
| input validation | each route checks by hand, and one forgets |
| central error handling | a `TypeError` becomes HTML in the middle of JSON |
| a database layer with migrations | the schema lives in someone's head |
| real authentication | no session, no token, no password hashing |
| standardized responses | each route invents its error format |
| tests with a fake request | the only way to test is starting a server |
| work outside the request | e-mail delays the user's response |
| cache, logs, queues | everything becomes a file in `/tmp` |
| documentation | the contract only exists in the code |

Table: Each row of this table is days of work, and none of them is specific
to Casa Amarela — it is exactly the same list in any web project in the
world.

## What you just understood

The four pieces in this chapter are not a teaching simplification of a
framework. They are the **shape** of all of them.

```text
request
   ↓
front controller        index.php
   ↓
middlewares             layer, layer, layer
   ↓
router                  which function runs
   ↓
container               builds what the function needs
   ↓
your function           the only part that is yours
   ↓
response                goes back through the layers
```

When a framework talks about a *kernel*, a *pipeline*, a *service provider*
or *route model binding*, the vocabulary will be new and the diagram will
not. It will be this one, with more care, more cases handled and more years
of fixes on top.

:::note In your career
At some point you will hear that "frameworks are for people who can't do it
by hand". The answer is not to disagree — it is to agree and finish the
sentence.

Doing it by hand took twenty minutes and produced a hundred lines that serve
three routes and handle no errors, validate nothing, authenticate nobody and
have no tests. Completing the table in the previous section is a year of
work, and the result would be a worse framework with a single maintainer.

What this chapter bought was not independence: it was the ability to
**read** the framework. When something goes wrong three layers below your
code, you will know which layers they are — and that is the difference
between opening a ticket and opening the file.
:::

:::tree title="Where we are now"
catalog/
  mini.php          # front controller, router, container, middleware
  src/
    Catalog/
    Circulation/
    Loans/
    Readers/
  composer.json
  phpstan.neon
:::

:::summary
- One file per page ties the URL to the disk, repeats the beginning in every
  file and leaves no place for what applies to everyone.
- A front controller makes everything come in through `index.php`; the
  server needs a rewrite rule for that.
- A router is a route table, a pattern match and a call — and it knows
  nothing about the domain.
- `{id}` in the pattern becomes a named group in the expression, and the
  group becomes an argument.
- A container uses reflection to read the constructor's parameters and build
  the dependency chain, keeping what it has already built.
- A naive container only resolves parameters that are classes; the rest
  someone has to declare.
- Middleware wraps the action in layers; the layer that does not call the
  next one interrupts the request.
- What is missing from the hundred-line file is, item by item, what a
  framework delivers.
:::

:::checkpoint
You explain a request's life cycle in any PHP framework, pointing out where
the front controller, middleware, router and container come in; write a
router with a path parameter; and can say why a container cannot resolve a
certain dependency.
:::

:::exercise level=1
Add to `mini.php` the route `DELETE /books/{id}`, which returns `204` with no
body when the book exists and `404` when it does not.

Then explain why `send()` needs an adjustment.

:::answer
```php
    ['DELETE', '/books/{id}',
        function (string $id) use ($catalog): Response {
            $id = (int) $id;

            if (!isset($catalog[$id])) {
                return new Response(404, [
                    'error' => "Book {$id} doesn't exist",
                ]);
            }

            return new Response(204, []);
        }],
```

`send()` needs an adjustment because, as it stands, it always prints the body
— and `json_encode([])` produces `[]`, two characters. A `204` response with
two bytes of body contradicts its own status, and some clients treat that as
a malformed response.

```php
function send(Response $r): void
{
    http_response_code($r->status);

    if ($r->status === 204) {
        return;
    }

    header('Content-Type: application/json');
    echo json_encode($r->body, JSON_UNESCAPED_UNICODE);
}
```

Notice where the fix lives: in the sending, not in the route. If every route
had to remember not to print anything, one of them would forget — and that
is the same reason that justifies the front controller existing.
:::

:::exercise level=2
The current router matches `{id}` with anything that is not a slash. That
makes `GET /books/abc` enter the route and arrive at `(int) 'abc'`, which is
`0`.

Add to the pattern the ability to require a format, so that
`/books/{id:\d+}` only matches digits — and `/books/abc` returns `404`
without ever calling the function.

:::answer
The change is in the line that builds the expression:

```php
$regex = '#^' . preg_replace_callback(
    '#\{(\w+)(?::([^}]+))?\}#',
    fn(array $p): string
        => '(?<' . $p[1] . '>' . ($p[2] ?? '[^/]+') . ')',
    $pattern,
) . '$#';
```

The pattern now recognizes two forms: `{id}`, unrestricted, and `{id:\d+}`,
restricted. `preg_replace_callback` is needed because the replacement now
depends on what was found — with plain `preg_replace` there was no way to
choose between the given format and the default.

The route becomes:

```php
['GET', '/books/{id:\d+}', ...]
```

And `/books/abc` matches no route, falling into the `404` at the end of the
loop.

It is worth noticing what this is: the mini framework's first
**validation**, and it happens before the route's function even exists. That
is why every framework offers something similar — the alternative is every
route starting with an `if` that checks the format of its own address.
:::

:::exercise level=3
Put the pieces together: make `mini.php` use the container and a chain of two
real middlewares.

The first middleware measures how long the request took and adds the
`X-Time` header. The second refuses with `401` any request without the
`Authorization` header, **except** `GET`.

Write the code and say in which order the two should be in the list, and
why.

:::answer
```php title="mini.php" numbered
$measureTime = function (array $req, callable $next): Response {
    $start = hrtime(true);

    $response = $next($req);

    $ms = (hrtime(true) - $start) / 1_000_000;
    header(sprintf('X-Time: %.1fms', $ms));

    return $response;
};

$requireCredential = function (array $req, callable $nx): Response {
    if ($req['method'] !== 'GET'
        && !isset($_SERVER['HTTP_AUTHORIZATION'])) {
        return new Response(401, ['error' => 'Missing credential']);
    }

    return $nx($req);
};

$action = fn(array $req): Response => $router->dispatch(
    $req['method'],
    $req['path'],
);

$pipeline = array_reduce(
    array_reverse([$measureTime, $requireCredential]),
    fn(callable $next, callable $current): callable
        => fn(array $req): Response => $current($req, $next),
    $action,
);

send($pipeline([
    'method' => $_SERVER['REQUEST_METHOD'],
    'path' => parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH),
]));
```

**The order is timing first, credential second**, and the reason is what each
one does with the response.

The timing middleware needs to be the outermost layer to measure
**everything**, including the time spent refusing someone. If it were
inside, requests rejected with `401` would leave without `X-Time` — and they
are exactly the ones you will want to measure on the day someone is
hammering the API.

The credential middleware needs to be outside the action and inside the
timing: it interrupts, and interrupting early is the point. A request with no
credential should not reach the router, much less the database.

The general rule, which works for any chain: **what observes stays outside;
what refuses comes right after; what works stays in the middle.**
:::
