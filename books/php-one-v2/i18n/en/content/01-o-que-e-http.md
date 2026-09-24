---
source_hash: bf2645547715
title: "What HTTP is"
number: 1
slug: o-que-e-http
part: p1
kicker: "The app sent the data. The server received the data. And $_POST was empty."
goal: >-
  Read a whole HTTP exchange with `curl -v`, know exactly what PHP sees of a
  request, understand why `$_POST` is empty with JSON and write a raw
  endpoint that receives and returns JSON with no framework.
---

:::story It isn't sending anything
Tainá had hooked a copy of Kauã's app up to the catalog, to test it. It
registered a loan and always got the same answer: *"copy not provided"*.

"It isn't sending anything," said Tainá. "Look, `$_POST` arrives empty."

"Empty how?"

"Empty. `array(0)`."

Dedé asked her to run the request again, but from the command line, with an
option he spelled out letter by letter.

```text
> POST /loans HTTP/1.1
> Content-Type: application/json
> Content-Length: 30
>
{"copy_id":812,"reader_id":47}
```

"It is sending," said Tainá.

"It is."

"But `$_POST`..."

"`$_POST` isn't what the app sent. It's what PHP decided to put in there."
:::

## The whole exchange, in text

HTTP is text going out and text coming back. `curl`'s `-v` option shows both
halves: the lines starting with `>` left your machine, the ones starting
with `<` came back from the server.

```text
$ curl -v -X POST http://localhost:8000/loans \
       -H "Content-Type: application/json" \
       -d '{"copy_id":812}'
```

```text
> POST /loans HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/8.18.0
> Accept: */*
> Content-Type: application/json
> Content-Length: 15
>
< HTTP/1.1 201 Created
< Date: Mon, 21 Sep 2026 20:29:51 GMT
< X-Powered-By: PHP/8.4.2
< Content-Type: application/json
<
```

Both halves have the same shape: a distinct first line, a list of headers, a
blank line and an optional body.

On the way out, the first line carries the verb, the path and the version.
On the way back, it carries the version, the number and the name of the
status.

:::key
The blank line is not formatting: it is the border. Everything before it is
headers; everything after is body.

That is why any accidental `echo` before a `header()` ruins the whole
response — PHP understands that the body has started, and the headers that
come afterwards have nowhere left to go.
:::

## The seven statuses you will use

```text
< HTTP/1.1 201 Created
```

The number is what the other program reads; the text beside it is a
courtesy for humans.

| Code | When | The body |
|---|---|---|
| `200` | it worked, here it is | the resource |
| `201` | created it, here it is | the created resource |
| `204` | done, nothing to say | empty |
| `400` | the request is malformed | the reason |
| `401` | I don't know who you are | the reason |
| `404` | it doesn't exist | the reason |
| `422` | I understood the request and it is invalid | which fields |

Table: Seven cover this book's entire API. The others exist and are rare.

## What PHP sees

All that text reaches your program already split into three variables that
exist on their own, without you declaring anything.

```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

echo json_encode([
    'method' => $_SERVER['REQUEST_METHOD'],
    'path' => $_SERVER['REQUEST_URI'],
    'type' => $_SERVER['CONTENT_TYPE'] ?? '(missing)',
    'get' => $_GET,
    'post' => $_POST,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
```

Run the server that ships with PHP and send an ordinary form:

```text
$ php -S localhost:8000 api.php
```

```text
$ curl -X POST http://localhost:8000/loans \
       -d "copy_id=812&reader_id=47"
```

```text
{
    "method": "POST",
    "path": "/loans",
    "type": "application/x-www-form-urlencoded",
    "get": [],
    "post": {
        "copy_id": "812",
        "reader_id": "47"
    }
}
```

:::term Superglobal
A variable that exists anywhere in the program without being declared or
received: `$_GET`, `$_POST`, `$_SERVER`, `$_FILES`, `$_COOKIE`.

They are PHP's oldest way of handing over the request, and the most
fragile, because any line in any file can read them — and write to them.
:::

Notice the values: `"812"`, in quotes. Everything that arrives over HTTP is
text, including what looks like a number. The conversion is your job, and
its place is the input border.

## Why `$_POST` was empty

Now the same request, with JSON:

```text
$ curl -X POST http://localhost:8000/loans \
       -H "Content-Type: application/json" \
       -d '{"copy_id":812,"reader_id":47}'
```

```text
{
    "method": "POST",
    "path": "/loans",
    "type": "application/json",
    "get": [],
    "post": []
}
```

Kauã's app was right, and so was `$_POST`.

PHP fills `$_POST` from the body **only when the `Content-Type` is one of
the two form formats**: `application/x-www-form-urlencoded`, which is the
previous example's, and `multipart/form-data`, which is the file upload one.
With any other type, it does not try to guess: it leaves the body untouched
and `$_POST` empty.

The body is still there, whole, in a place with a strange name:

```php title="api.php" numbered
$raw = file_get_contents('php://input');

$data = json_decode($raw, true);

echo $data['copy_id'], "\n";
```

```text
812
```

`php://input` is a read stream with the request's raw body, from the first
byte to the last, with no interpretation at all. `json_decode` with `true` as
its second argument returns an associative array instead of an object.

:::pitfall
This is, by a wide margin, the first bug of anyone writing an API in PHP:
the app sends JSON, the server reads `$_POST`, and the response is "required
field" for a field that was sent.

The symptom is misleading because **the error is on the server and the
suspicion falls on the client**. Before blaming whoever sends, run
`curl -v`: if the `Content-Type` line and the body are there, the problem is
whoever reads.
:::

## Headers that change behavior

Most headers are information. Three decide what happens.

**`Content-Type`** says what format the body **is written in**. It is what
just decided whether `$_POST` would be filled.

**`Accept`** says what the client **accepts receiving**. A client that sends
`Accept: application/json` is saying it does not want your HTML error page —
and returning HTML anyway is what makes an app show a blank screen instead of
the message.

**`Authorization`** carries the credential. It goes out like this, and
`$_SERVER` translates the name by swapping the dash for an underscore and
adding the `HTTP_` prefix:

```text
> Authorization: Bearer abc123
```

```php
$_SERVER['HTTP_AUTHORIZATION']
```

In the response, whoever writes headers is the `header()` function, and the
status is `http_response_code()`:

```php
header('Content-Type: application/json');
http_response_code(201);
```

## The server doesn't remember you

HTTP is **stateless**: each request arrives on its own, with no memory of the
previous one. The server does not know who you are, what you just did or that
there is a screen open on the other side.

That is the same model chapter @cap:o-php-que-voce-ouviu-falar described from
the inside — each request starts from zero and dies at the end — now seen
from the outside, in the protocol.

The practical consequence: **everything the server needs to remember has to
come along with the request, or be stored somewhere outside it.** The browser
solves this by resending a cookie with every request; PHP uses that cookie to
find a session file on the server's disk again. An API usually solves it
another way, sending the credential in `Authorization` with every call.

Both are the same idea: the request carries the identity, because the
connection carries nothing.

## A raw endpoint

Put it all together. No framework, no library, sixty lines of nothing:

```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Use POST']);
    exit;
}

$type = $_SERVER['CONTENT_TYPE'] ?? '';

if (!str_starts_with($type, 'application/json')) {
    http_response_code(415);
    echo json_encode(['error' => 'Send application/json']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);

if (!is_array($data)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

$missing = [];

foreach (['copy_id', 'reader_id'] as $field) {
    if (!isset($data[$field])) {
        $missing[] = $field;
    }
}

if ($missing !== []) {
    http_response_code(422);
    echo json_encode([
        'error' => 'Required fields',
        'fields' => $missing,
    ]);
    exit;
}

http_response_code(201);

echo json_encode([
    'id' => 4471,
    'copy_id' => (int) $data['copy_id'],
    'reader_id' => (int) $data['reader_id'],
]);
```

:::http title="The exchange this file handles"
POST /loans
Content-Type: application/json

{"copy_id": 812, "reader_id": 47}
---
201 Created
Content-Type: application/json

{
  "id": 4471,
  "copy_id": 812,
  "reader_id": 47
}
:::

Two things to notice before moving on.

The first: the `405` and the `415` exist because the file answers **one**
path and **one** verb. A program that serves several needs to decide which
code runs, and that decision has a name — it is the only thing missing here
for this to become a system.

The second: the `(int)`s in the response. What arrived was text; what leaves
is a number. The border converts, and that is why it is the only place in the
program that needs to know HTTP exists.

:::note In your career
"The client isn't sending it" and "the server isn't receiving it" are the
same discussion seen from two sides, and it eats whole afternoons because
each side looks only at its own log.

What ends it in two minutes is a `curl -v` exchange: whoever accuses pastes
the whole output, with the request line, the headers and the body. From
there on there is no more opinion — either the `Content-Length` is zero, or
it is not.

Learn to read that output before you need it in a meeting with the app team.
It is the difference between taking part in the conversation and waiting
for the conclusion.
:::

:::summary
- Request and response are text with the same shape: first line, headers,
  blank line, body.
- The blank line is the border; an `echo` before `header()` brings it forward
  and ruins the response.
- Seven statuses cover the entire API: `200`, `201`, `204`, `400`, `401`,
  `404` and `422`.
- `$_GET`, `$_POST` and `$_SERVER` are superglobals, and everything that
  arrives through them is text.
- `$_POST` is only filled with `x-www-form-urlencoded` and
  `multipart/form-data`; with JSON, the body is in `php://input`.
- `Content-Type` says how the body is written; `Accept`, what the client
  accepts receiving; `Authorization` carries the credential.
- HTTP is stateless: the identity travels with each request, because the
  connection keeps nothing.
- `header()` writes a header and `http_response_code()` sets the status.
:::

:::checkpoint
You read a whole exchange in `curl -v` and explain every line, can say
without testing whether a `$_POST` will arrive filled in, read the raw body
of a JSON request and write an endpoint that returns the right status for a
malformed request, a missing field and success.
:::

:::exercise level=1
For each situation, say which status the response should have:

1. The loan was recorded successfully.
2. Reader 913 does not exist in the records.
3. The body arrived with `reader_id` but without `copy_id`.
4. The client sent the body in XML.
5. The return was recorded and there is nothing to send back in the body.

:::answer
1. `201` — it created a new resource.
2. `404` — the requested resource does not exist.
3. `422` — the request is well formed and the content is invalid. It is not
   `400`: the JSON was correct, it is the rule that was not met.
4. `415` — the body's format is not accepted. Not `400` either, and the
   difference matters for the client to know whether it should fix the data
   or the header.
5. `204` — done, no body. Returning `200` with `{}` works and forces the
   client to interpret an empty body on purpose.

The pair that confuses people most is 3 and 4 against `400`. A rule that
settles it: `400` is "I couldn't even understand the request"; `415` is "I
understood the format and I don't accept it"; `422` is "I understood
everything and the content is wrong".
:::

:::exercise level=2
Add to `api.php` handling for the `GET` verb on `/loans/{id}`, returning
`200` with the loan or `404` if the number does not exist.

Use this fixed data in place of the database:

```php
$loans = [
    4471 => ['copy_id' => 812, 'reader_id' => 47],
];
```

:::answer
```php title="api.php" numbered
<?php

declare(strict_types=1);

header('Content-Type: application/json');

$loans = [
    4471 => ['copy_id' => 812, 'reader_id' => 47],
];

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if ($_SERVER['REQUEST_METHOD'] === 'GET'
    && preg_match('#^/loans/(\d+)$#', $path, $parts)) {

    $id = (int) $parts[1];

    if (!isset($loans[$id])) {
        http_response_code(404);
        echo json_encode(['error' => "Loan {$id} doesn't exist"]);
        exit;
    }

    echo json_encode(['id' => $id] + $loans[$id]);
    exit;
}

http_response_code(404);
echo json_encode(['error' => 'Route not found']);
```

Three details decide whether this works.

`parse_url(..., PHP_URL_PATH)` separates the path from the query. Without
it, `/loans/4471?format=short` would not match the expression, and the
client would get a `404` for sending one parameter too many.

The expression requires `\d+` and anchors at both ends. Without the anchors,
`/old/loans/4471/extra` would match too.

And the `(int)` in converting the number: `$parts[1]` is text, like
everything that comes from the URL, and `$loans` has integer keys.
`isset($loans['4471'])` with a string works through automatic key
conversion — it works by accident, and an accident is not a design.
:::

:::exercise level=3
An app reports that the catalog API "sometimes returns HTML". The API team
swears it always returns JSON.

Both are right. Come up with three situations in which a PHP API returns
HTML without anyone having written HTML, and say how to prevent each one.

:::answer
**One: a fatal error with `display_errors` on.** An unhandled `TypeError`
makes PHP print the message and the stack. If the server is configured to
format that as HTML, the client receives a page in the middle of what should
have been JSON — often **after** a piece of the JSON has already been sent.

Prevented with `display_errors` off on the server and a registered exception
handler that responds in JSON with a `500` status.

**Two: the web server responding before PHP.** A `404` for a nonexistent
route, a `413` for an oversized body, a `502` when PHP did not respond — none
of these go through your code, and the server's default is an HTML page.

Prevented by configuring the server's error pages in the API's format, and it
is the kind of thing that only shows up when someone tests the bad path.

**Three: output before `header()`.** A blank line after the `?>` in an
included file, a forgotten debugging `echo`, a printed warning. PHP sends the
default headers, which include `Content-Type: text/html`, and your `header()`
arrives too late:

```text
Warning: Cannot modify header information - headers already sent
```

Prevented by not closing `?>` in a file that contains only PHP — and that is
why that rule exists.

What the three have in common is worth more than the three: **your API's
error path needs to be tested like the success path**. Almost every team
tests the `201` and discovers the `500`'s format in production.
:::
