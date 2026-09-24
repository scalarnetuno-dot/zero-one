---
source_hash: 02f09545a66c
title: "Authentication with Sanctum"
number: 21
slug: autenticacao
part: p5
kicker: "The Sistema stored passwords as MD5, unsalted. Over lunch, on a developer's machine, sixty percent fell in four minutes."
goal: >-
  Answer "who are you" safely: store passwords the right way, migrate the
  ones stored wrong, issue and revoke tokens with Sanctum, and write a login
  whose error response gives nothing away — neither in the text nor in the
  timing.
---

:::story Four minutes
Dedé had exported the Sistema's `usuarios` table to plan the migration. Two
columns mattered: `email` and `senha`, the password. The second had
thirty-two hexadecimal characters on every row.

— MD5 — he said.

— Is that bad? — asked Tainá.

— Give me four minutes.

He downloaded a public list of leaked passwords — a few million lines, the
kind of file that has been circulating for a decade —, wrote an eight-line
loop and ran it. The laptop's fan sped up.

```text
$ php crack.php users.csv common-passwords.txt
tested: 14,344,391
cracked: 1,047 of 1,731 (60.5%)
time: 3min52s
```

Tainá watched the list as it appeared. `123456`. `casaamarela`.
`biblioteca`. `marmelada1994`. The name of a dog she knew from a photo at the
counter.

— Can you delete that now? — she said.

— I'm already deleting it.

— And what if someone has that table?

— The Sistema has been online for fifteen years, with backups on a hard
drive in the back room and the FTP password on a piece of paper — said
Dedé. — I don't know who has that table.
:::

## A password is never stored

The Sistema made a mistake that looks technical and is one of principle. It
stored **something derived from the password** that made it possible to
find out the password.

What a login system needs is not to know the password. It is to **check**
whether the password typed now is the same one registered before. For that,
it is enough to store something that:

1. is always the same for the same password;
2. does not allow, in practice, getting back to the original password.

A function with those two properties is called a *hash*. MD5 is one — and
that is why the Sistema thought it was protected.

The problem is in the words "in practice". MD5 was designed to be **fast**:
checking the integrity of large files, millions of times a second. An
ordinary graphics card computes billions of MD5s a second. At that speed,
there is no need to go back from the hash to the password: just compute the
hash of every likely password and compare.

And without **salt** — a random value different for each user, mixed into
the password before the calculation —, people with the same password have
the same hash. The list of hashes of common passwords, computed once, works
for every system in the world that used plain MD5.

| Storing | Whoever leaks the table gets |
|---|---|
| the password | every password, instantly |
| unsalted MD5 | the common passwords, in minutes |
| unsalted SHA-256 | the same, a bit more slowly |
| salted MD5 | the common ones, one account at a time |
| `bcrypt` / `argon2` | very little, very slowly |

Table: What changes from one row to the next is not the function's math; it
is how much time **each attempt** costs.

## `bcrypt`, `argon2` and the cost that is on purpose

Functions made for passwords do the opposite of MD5: they are **slow on
purpose**, with the amount of slowness adjustable through a cost factor.

```php
$hash = Hash::make('marmelada1994');
```

```text
$2y$12$Qm1S3pTjXe4K8b0vYzN1ZuQ4rW7pX2... (60 characters)
```

The hash already carries inside it everything needed to check later: the
algorithm (`2y` is `bcrypt`), the cost (`12`), the salt (the next 22
characters) and the result. None of that is secret, and none of it helps
find out the password.

```php
Hash::check('marmelada1994', $hash); // true
Hash::check('marmelada1995', $hash); // false
```

At cost 12, each check takes something like two hundred and fifty
milliseconds on an ordinary machine. For someone logging in, it is
imperceptible. For someone trying fourteen million passwords, it is the
difference between four minutes and **a hundred and eleven days** — per
account, because each one has its own salt.

Laravel uses `bcrypt` by default, with the cost set in `.env`. `argon2id` is
more modern and resists graphics cards better; both are correct choices. The
wrong choice is anything that was not made for passwords.

:::key
The cost is not a defect to optimize. If someone on the team "speeds up
login" by lowering the cost factor to 4, login gets fifty times faster for
everyone — including whoever stole the table.

`Hash::needsRehash($hash)` says whether a hash was generated with a lower
cost than the configured one. It is what lets you **raise** the cost over
the years, as machines get faster.
:::

### Migrating the Sistema's passwords

The Sistema's 1,731 accounts cannot be converted all at once: generating the
`bcrypt` requires the password, and nobody has the password. The way out is
to convert **on each person's next login**, when the password passes
through the application:

```php title="app/Auth/PasswordChecker.php" numbered
final class PasswordChecker
{
    public function check(User $u, string $password): bool
    {
        if ($this->isLegacyMd5($u->password)) {
            if (!hash_equals($u->password, md5($password))) {
                return false;
            }

            $u->forceFill(['password' => Hash::make($password)])
                ->save();

            return true;
        }

        if (!Hash::check($password, $u->password)) {
            return false;
        }

        if (Hash::needsRehash($u->password)) {
            $u->forceFill(['password' => Hash::make($password)])
                ->save();
        }

        return true;
    }

    private function isLegacyMd5(string $hash): bool
    {
        return (bool) preg_match('/^[a-f0-9]{32}$/', $hash);
    }
}
```

`hash_equals` compares two strings always taking the same time, regardless
of where they differ. Comparing with `===` stops at the first different
character — and that, measured millions of times, leaks information.

:::warning
Migrating at login protects the accounts **from now on**. It does not
protect what has already leaked.

The Sistema's passwords must be considered compromised: it was online for
fifteen years with the table in MD5, and nobody knows who had access to the
backups. The right decision — which Vera needs to make with the
association, because it involves notifying everyone — is to **force a
password change** on first access to the new system. `PasswordChecker` is
still useful: it recognizes the old password one last time, to allow the
change.

And accounts that never log in again keep MD5 forever. After a deadline,
they are wiped — the hash, not the account —, and the next access goes
through password recovery.
:::

## Session and token: two different problems

After checking the password, the server needs to **remember** that it did.
HTTP does not remember — chapter @cap:o-que-e-http showed that each request
arrives on its own. There are two ways to solve it, and each serves one kind
of client.

**Session with a cookie.** The server stores "user 12 signed in" in its own
storage, and sends the browser a cookie with a random identifier. The
browser returns the cookie on every request, on its own. It is what the
Blade panel uses.

**Token.** The server hands the client a long random string, and the client
sends it in the `Authorization` header of each request. Nothing is automatic
— the client stores it and sends it. It is what the reader app uses.

| | Session | Token |
|---|---|---|
| who stores it | the browser, on its own | the app, on purpose |
| how it comes back | cookie, automatic | `Authorization` header |
| for | pages on the same domain | apps, integrations |
| main risk | CSRF | a leaked token |

Table: The cookie being automatic is both the advantage and the risk. The
CSRF from chapter @cap:blade exists precisely because the browser sends the
cookie even when the request was triggered by another site.

## Sanctum

Sanctum is the Laravel package that solves both things in the same place:
tokens for apps and session authentication for a front-end on the same
domain. Casa Amarela uses the first half.

```text
$ php artisan install:api
```

The command installs Sanctum, creates the `personal_access_tokens` table and
the `routes/api.php` file, if it does not exist yet. The user model gains a
trait:

```php title="app/Models/User.php" numbered
class User extends Authenticatable
{
    use HasApiTokens;

    protected $fillable = ['name', 'email'];

    protected $hidden = ['password'];

    protected function casts(): array
    {
        return [
            'role' => Role::class,
            'password' => 'hashed',
        ];
    }
}
```

The `hashed` cast hashes on its own when someone assigns a plain-text
password — and does not hash again if the value is already a hash, which
avoids the hash of a hash. The column is called `password`, which is what
Laravel expects; a legacy table with another name — the Sistema's `senha`,
say — would declare it with `$authPasswordName`.

`Role` is an enum with three cases, and the next chapter depends on it:

```php title="app/Auth/Role.php" numbered
enum Role: string
{
    case Reader = 'reader';
    case Clerk = 'clerk';
    case Admin = 'admin';
}
```

A `User` with the `Reader` role has a `reader_id` pointing to the reader
record. Clerks and admins do not: they are the staff.

## Login, logout and `GET /me`

```php title="app/Http/Controllers/Auth/LoginController.php" numbered
public function __invoke(
    LoginRequest $request,
    PasswordChecker $checker,
) {
    $user = User::where(
        'email',
        mb_strtolower($request->string('email')),
    )->first();

    $valid = $user !== null
        && $checker->check($user, $request->password);

    if (!$user) {
        Hash::check($request->password, self::FAKE_HASH);
    }

    if (!$valid) {
        throw new InvalidCredentials();
    }

    $token = $user->createToken(
        name: $request->string('device', 'app'),
        abilities: $user->role->abilities(),
        expiresAt: now()->addDays(30),
    );

    return response()->json([
        'token' => $token->plainTextToken,
        'expires_at' => $token->accessToken->expires_at
            ->toIso8601String(),
        'user' => new UserResource($user),
    ], 201);
}
```

`createToken` generates a random string, stores its **hash** in the
`personal_access_tokens` table and returns the original text only once.
After this response, not even the server knows what the token is anymore —
it can only check it.

:::anatomy title="The parts of a Sanctum token"
lang: text
code: |
  Authorization: Bearer 7|kX9vQ2mT8pLr4wYz6nB1cD3fG5hJ0sA2eR7tU9iO
notes:
  - { line: 1, text: "`Bearer` is the scheme: \"whoever bears this is authorized\". That is why the token is treated like a password." }
  - { line: 1, text: "`7` is the row's id in `personal_access_tokens`. It is for finding the row without scanning the table." }
  - { line: 1, text: "The `|` separates the id from the secret." }
  - { line: 1, text: "The rest is 40 random characters. The database stores only their SHA-256, and SHA is safe here: the value is random, not a password someone chose." }
:::

Notice the last note. SHA-256 is wrong for passwords and right for tokens,
and the difference is in who chose the value. A password is chosen by a
person, and there is a list of the likely ones. A token of forty random
characters has no list: trying them all would take longer than the age of
the universe, at any computing speed.

The protected routes use the previous chapter's middleware:

```php title="routes/api.php" numbered
Route::post('auth/login', LoginController::class)
    ->middleware('throttle:login');

Route::middleware('auth:sanctum')->group(function () {
    Route::get('me', MeController::class);
    Route::post('auth/logout', LogoutController::class);
    // ... the rest of the reader API
});
```

```php title="app/Http/Controllers/MeController.php" numbered
public function __invoke(Request $request)
{
    return new UserResource(
        $request->user()->load('reader'),
    );
}
```

`$request->user()` returns the user who owns the token that came in the
header. It is the `null` the `ReaderResource` from chapter
@cap:api-resources was waiting to stop being.

## Revoking for real

```php title="app/Http/Controllers/Auth/LogoutController.php" numbered
public function __invoke(Request $request)
{
    $request->user()->currentAccessToken()->delete();

    return response()->noContent();
}
```

Logout deletes **the token's row** in the database. On the next request with
that token, Sanctum looks it up by id, does not find it, and responds `401`.

It is the advantage of a token that lives in the database over a
self-contained token, like a JWT, which carries the data inside and is
checked only by its signature: the JWT stays valid until it expires, and
"signing out" in the app deletes the phone's copy without invalidating the
others. With Sanctum, signing out is signing out.

Three situations call for revoking **all** of a person's tokens:

```php
$user->tokens()->delete();
```

**The person changed their password.** If they changed it because they
suspected someone, that someone cannot stay signed in.

**Staff blocked the account.** A block that does not drop the open sessions
is a block that applies "on the next login".

**The person asked.** The "sign out of all devices" button exists in every
serious app for this reason.

:::pitfall
A token without expiry is a token forever. The phone lost in 2026 still
reaches the account in 2031.

The `expiresAt` in `createToken` sets each token's validity, and the
`expiration` setting in `config/sanctum.php` is the safety net for those
created without it. Thirty days, renewed on use, is a common balance for an
app; for the staff panel, hours.

Expired tokens stay in the table until someone deletes them. Sanctum has a
command for that, `sanctum:prune-expired`, and it goes into the scheduler
from chapter @cap:configuracao-ambiente-e-artisan.
:::

## The response that doesn't say whether the e-mail exists

Back to `LoginController`, there are two lines that look strange.

The first is the single exception. Both a nonexistent e-mail and a wrong
password produce **the same response**:

```json
{
  "type": "invalid-credentials",
  "message": "Incorrect e-mail or password."
}
```

The alternative — "e-mail not registered" in one case, "incorrect password"
in the other — is friendlier and hands whoever is attacking a list of who is
a Casa Amarela reader. For a library, that seems harmless. For a health,
dating or counseling service, confirming that an e-mail has an account is
already the leak.

The second is the `Hash::check` with `FAKE_HASH` when the user does not
exist. It computes a whole `bcrypt` and **throws the result away**.

The reason is time. Without that line, an attempt with a nonexistent e-mail
responds in five milliseconds — just the database query. An attempt with an
existing e-mail and a wrong password responds in two hundred and fifty — the
query plus the `bcrypt`. The message is identical, and the stopwatch tells
all.

:::key
A login response needs to be the same in **three** dimensions: the status,
the body and the time.

The first two are checked by reading the response. The third is only checked
by measuring — and that is why it is the one that usually gets left out.
:::

And HTTPS, which seems obvious and deserves to be written down: without it,
the password travels as text over the network of the café the reader is in.
And so does the token, on every following request. Nothing in this chapter
works without HTTPS, and chapter @cap:git-ci-e-deploy puts it on the list
before publishing.

:::note In your career
You will find passwords in MD5, in SHA-1, in plain text and in "reversible
encryption so we can e-mail the password". You will find them in systems at
large companies, built by competent people, years ago.

The conversation about it is rarely technical. It is about notifying users,
forcing password changes and admitting, in writing, that the old system had
a problem. Whoever handles that conversation well — with the migration plan
ready, the notice text drafted and the risk explained without alarmism — is
who the company calls the next time something similar comes up.
:::

:::tree title="Where we are now"
casa-amarela/
  app/Auth/
    Role.php                     # reader, clerk, admin
    PasswordChecker.php          # migrates MD5 at login
    InvalidCredentials.php       # one exception for both cases
  app/Models/
    User.php                     # HasApiTokens, hashed cast
  app/Http/Controllers/
    Auth/LoginController.php     # token with an expiry
    Auth/LogoutController.php    # deletes the current token
    MeController.php
  config/sanctum.php             # expiration
:::

:::summary
- A password is not stored; a hash is stored, which allows checking and does
  not allow going back.
- MD5 and SHA are fast on purpose; `bcrypt` and `argon2` are slow on
  purpose, with a per-user salt.
- The hash's cost is protection; `needsRehash` lets you raise it over the
  years.
- Legacy passwords migrate on the next login; leaked ones require a forced
  change.
- A session is an automatic cookie for pages; a token is an explicit header
  for apps.
- Sanctum stores the token's hash in the database; logout deletes the row
  and takes effect immediately.
- Password change, blocking and "sign out everywhere" revoke all tokens.
- A token without expiry is valid forever; `expiresAt` and
  `sanctum:prune-expired` solve it.
- The login error is the same in status, body and time; `hash_equals` and
  the fake hash protect the third.
:::

:::checkpoint
The API login issues a token with an expiry and abilities, logout revokes it
immediately, the Sistema's passwords migrate on first access, and you can
explain why the error response is generic — and why it takes the same time
when the e-mail does not exist.
:::

:::exercise level=1
Say what is wrong with each decision and what the fix is:

1. `password` stored with `hash('sha256', $password . 'casaamarela')`.
2. A token created without `expiresAt` "because readers complain about
   having to sign in again".
3. When changing the password, the system generates the new hash and saves
   it.
4. Login responds `404` when the e-mail does not exist.

:::answer
1. SHA-256 is fast, and the "salt" is the same for everyone — it is a
   constant, not a salt. Fix: `Hash::make`.
2. An eternal token. Fix: thirty days of validity **renewed on use** — an
   active reader never needs to sign in again, and the phone forgotten in a
   drawer loses access on its own.
3. It did not revoke the other tokens. Fix: `$user->tokens()->delete()`
   after saving, except, if you wish, the current request's token.
4. It confirms the e-mail has no account. Fix: the same `401` response for
   both cases, with the same timing.
:::

:::exercise level=2
Write the `POST /me/password` endpoint, which changes the authenticated
user's password. It receives the current password and the new one (with
confirmation). It must refuse if the current one is wrong, revoke all
**other** tokens, and keep the current one working.

:::answer
```php title="app/Http/Controllers/PasswordChangeController.php" numbered
public function __invoke(
    ChangePasswordRequest $request,
    PasswordChecker $checker,
) {
    $user = $request->user();

    if (!$checker->check($user, $request->current_password)) {
        throw new InvalidCredentials();
    }

    $user->password = $request->new_password;
    $user->save();

    $current = $user->currentAccessToken()->id;

    $user->tokens()
        ->where('id', '!=', $current)
        ->delete();

    return response()->noContent();
}
```

```php title="app/Http/Requests/ChangePasswordRequest.php" numbered
public function rules(): array
{
    return [
        'current_password' => ['required', 'string'],
        'new_password' => [
            'required', 'confirmed',
            Password::min(10)->uncompromised(),
        ],
    ];
}
```

The `hashed` cast hashes `new_password` on assignment.
`Password::uncompromised()` consults a public leaked-password service —
without sending the password, only the first characters of its hash — and
refuses those that appear on the list. It is the list Dedé used, turned
around to face the right way.

The route sits behind `throttle`, like login: without it, it is a second
place to test passwords.
:::

:::exercise level=3
The association's marketing team wants the app to show, on the login
screen, the message "This e-mail isn't registered. Want to sign up?" —
because many people try to sign in without having an account and give up.

The need is real. Propose a solution that satisfies marketing without going
back to revealing which e-mails have accounts, and say what it costs.

:::answer
**The real problem.** People without an account try to sign in, get
"incorrect e-mail or password", think they got the password wrong, and give
up. The generic message protects those who have an account and hurts those
who do not.

**The solution: change the flow, not the message.** The login screen gets
two steps. In the first, the person types the e-mail and taps "continue".
The response is always the same: "We sent a link to that e-mail". If the
e-mail has an account, the link leads to login. If not, the link leads to
sign-up, with the e-mail already filled in.

Whoever is attacking always gets "we sent a link", and learns nothing.
Whoever has no account receives, in their own e-mail, the invitation to sign
up — which is exactly what marketing wanted to show.

**What it costs.** One more step at login, and a dependency on e-mail
delivery working — which, with the queue from chapter
@cap:events-jobs-e-filas, is manageable. And the sign-up screen needs the
same discipline: "this e-mail is already registered" at sign-up leaks the
same data through the other door. The answer there is also "we sent a link".

**The cheaper, worse alternative:** show "No account? Sign up" **always**,
prominently, below the error message. It reveals nothing, and helps some
people. It is what can be done this week, while the two-step flow is not
ready.
:::
