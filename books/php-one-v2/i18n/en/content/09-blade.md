---
source_hash: 5f8758badba3
title: "Blade, when the screen is still the answer"
number: 9
slug: blade
part: p2
kicker: "Vera doesn't want an app. She wants a search field and a button, like the one in the Sistema, which worked."
goal: >-
  Deliver the panel the librarian uses at the counter — listing, form and
  action — understanding automatic escaping, the form token and where the
  line between Blade and real front-end lies.
---

:::story A field and a button
Dr. Aurélio presented the reader app at Tuesday's meeting, with the screens
on the projector, and asked Vera what she thought.

— Pretty. Where do I lend?

— Lending is here, see. The reader opens it on their phone and...

— No. Me. At the counter. With the person in front of me and the book in my
hand.

The silence of people who had not thought about that.

— We can make a screen.

— It's what I use today — said Vera. — One field, I type the accession
number, press the button, it's lent. Takes four seconds.

— The Sistema's?

— The Sistema's. That one worked.
:::

## Not everything is an API

An app makes sense for someone browsing the collection from the couch. It
makes none for someone standing behind a counter, with a queue.

Vera's panel has three screens, and the rest of the book remains an API.
This is the only web part, and it exists because the system's real client
works on a computer that is already switched on at the desk.

:::key
The question that decides between a screen and an API is not "what is more
modern?". It is: **who uses this, in what situation?**

A queue at the counter, four seconds per person and a keyboard call for a
form. The reader on the bus, wanting to know whether the book came back,
calls for an app. The same system serves both, and neither serves both.
:::

:::art caption="The app was pretty. Vera wanted a field and a button."
src="o-aplicativo-era-bonito-a-vera-queria-um-campo-e-um-botao.png"
Minimalist editorial cartoon on a white background: in a meeting room, a
projector shows a giant, colorful phone app on the wall, full of icons,
cards and gradients. A director in a suit points at the projection with
pride. In the foreground, with her back to the wall, an older librarian in
glasses stands behind a wooden counter with a book in her hand and a reader
waiting in front of her, looking at an old monitor that shows only a text
field and a button. Few elements, dry humor, tech-magazine aesthetic.
:::

## Blade is PHP with less ceremony

A view is a file in `resources/views/` with the `.blade.php` extension. The
controller assembles the data and picks the view:

```php title="app/Http/Controllers/DeskController.php" numbered
public function index(Request $request)
{
    $loans = Loan::open()
        ->withBookAndReader()
        ->orderBy('due_on')
        ->get();

    return view('desk.index', [
        'loans' => $loans,
        'today' => now(),
    ]);
}
```

```blade title="resources/views/desk/index.blade.php" numbered
<h1>Open loans</h1>

<table>
    @forelse ($loans as $loan)
        <tr>
            <td>{{ $loan->copy->accession }}</td>
            <td>{{ $loan->copy->book->title }}</td>
            <td>{{ $loan->reader->name }}</td>
            <td>{{ $loan->due_on->format('d/m/Y') }}</td>
        </tr>
    @empty
        <tr><td colspan="4">Nothing on loan right now.</td></tr>
    @endforelse
</table>
```

`@forelse` is a `foreach` with one fewer case to forget: it already brings
the `@empty` for the empty list. Without it, the screen of a library with no
loans would be a table with no rows and no explanation.

The directives that cover almost everything:

| Blade | PHP |
|---|---|
| `{{ $x }}` | `echo e($x)` |
| `@if` / `@else` / `@endif` | `if` / `else` |
| `@foreach` / `@endforeach` | `foreach` |
| `@forelse` / `@empty` | `foreach` with an empty test |
| `@php ... @endphp` | a block of plain PHP |

Table: The last one exists, is legitimate in rare cases and is usually the
sign that the calculation should have been done in the controller.

## `{{ }}` escapes, and that is the feature

Suppose someone registers a book with this title:

```text
<script>alert('hi')</script>
```

```blade
<td>{{ $book->title }}</td>
```

```text
<td>&lt;script&gt;alert('hi')&lt;/script&gt;</td>
```

The browser shows the text and runs nothing. `{{ }}` converts the characters
that would mean something in HTML before printing — it is what stops a form
field from becoming code on another person's screen.

And there is the other form:

```blade
<td>{!! $book->title !!}</td>
```

```text
<td><script>alert('hi')</script></td>
```

:::pitfall
`{!! !!}` is not "the version that doesn't break the HTML". It is a security
decision, and the question it forces is a single one: **who wrote this
content?**

If the answer includes "a user", the right answer is `{{ }}`. If you really
need to print HTML coming from outside — a rich text editor, for example —,
the content must first go through a cleanup that removes what is not
allowed, and that is a library, not a choice of braces.

The attack has a name, XSS, and its most common form is exactly this: a
registration field nobody looked at, printed on a screen someone else opens.
:::

## Layout and component

Three screens already repeat the header, footer and menu. The modern way to
solve that in Blade is a layout component:

```blade title="resources/views/components/layout.blade.php" numbered
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{{ $title ?? 'Casa Amarela' }}</title>
</head>
<body>
    <header>
        <strong>Casa Amarela Library</strong>
        <nav>
            <a href="{{ route('desk.index') }}">Loans</a>
            <a href="{{ route('desk.catalog') }}">Catalog</a>
        </nav>
    </header>

    <main>
        {{ $slot }}
    </main>
</body>
</html>
```

```blade title="resources/views/desk/index.blade.php" numbered
<x-layout title="Open loans">
    <h1>Open loans</h1>

    <table>
        ...
    </table>
</x-layout>
```

The file in `components/` becomes the `<x-layout>` tag. Whatever is inside
the tag arrives in `$slot`; whatever is written as an attribute arrives as a
variable.

:::key
There is also `@include('partials.menu')`, older, and it ages badly for a
specific reason: the included file sees **all** the variables of whoever
included it.

That works until the day two screens include the same partial and one of
them lacks the variable the partial uses. The error shows up on the screen,
and the cause is in another file.

The component declares what it receives. It is the same difference as
between the array and the class in chapter @cap:classes-e-objetos, now in
HTML.
:::

## The form and the token you don't see

The screen Vera asked for:

```blade title="resources/views/desk/lend.blade.php" numbered
<x-layout title="Lend">
    <form method="POST" action="{{ route('desk.lend') }}">
        @csrf

        <label for="accession">Accession</label>
        <input id="accession" name="accession"
               value="{{ old('accession') }}" autofocus>

        @error('accession')
            <p class="error">{{ $message }}</p>
        @enderror

        <label for="document">Reader's document</label>
        <input id="document" name="document"
               value="{{ old('document') }}">

        @error('document')
            <p class="error">{{ $message }}</p>
        @enderror

        <button>Lend</button>
    </form>
</x-layout>
```

Three directives do the boring work.

**`@csrf`** inserts a hidden field with a token. When the form comes back,
Laravel checks whether the token matches the session's — and refuses if it
does not.

:::term CSRF
*Cross-Site Request Forgery*: any site, open in another tab, builds a form
that points at **your** system and makes the browser submit it. Since the
browser sends the session cookies along, the request arrives authenticated.

The token solves it because the outside site has no way of knowing it. That
is why it exists in `web.php` and not in `api.php`: without a session in a
cookie, there is nothing to forge.
:::

**`old('accession')`** returns what the person had typed before the form
was refused. Without it, a validation error wipes the input — and Vera types
it all again, with the queue waiting.

**`@error('accession')`** only prints when there is an error on that field.

And the controller on the other side:

```php title="app/Http/Controllers/DeskController.php" numbered
public function lend(
    Request $request,
    LoanRecorder $loans,
) {
    $data = $request->validate([
        'accession' => ['required', 'integer'],
        'document' => ['required', 'string'],
    ]);

    try {
        $loans->recordByAccession(
            $data['accession'],
            $data['document'],
        );
    } catch (CopyUnavailable $e) {
        return back()
            ->withInput()
            ->withErrors(['accession' => $e->getMessage()]);
    }

    return redirect()
        ->route('desk.lend')
        ->with('success', 'Lent.');
}
```

`back()->withInput()` returns the person to the form with what they typed,
and it is what feeds `old()`. The `redirect()` on the success path exists so
that refreshing the page does not lend the same book again — the browser
would resend the `POST`.

:::key
This pair — redirect after saving, return with the data after refusing — is
the basis of every form screen. It solves "refreshing the page duplicated
the record" without any cleverness.

It is the poor relative of the idempotency in chapter
@cap:o-que-e-uma-api-rest, and it solves the same problem: someone pressed
twice.
:::

## When to stop

Blade delivers screens rendered on the server. That covers listing, form,
filter and report — which is what almost every admin panel is.

It stops being the right tool when the screen needs to change **without
reloading**: dragging items, updating on its own, editing in several tabs at
once.

| The screen needs | Blade handles it |
|---|---|
| listing, filtering, paging | yes |
| form with validation | yes |
| report and printing | yes |
| a section that updates on its own | with help |
| an interface that never reloads | no |

Table: The middle column has a gray zone, and that is where most projects'
architecture decision lives.

:::pitfall
The worst place to be is the middle: a Blade full of JavaScript that builds
pieces of the screen and talks to the API, but is neither a front-end
application nor a server screen.

You end up with two places that know how to build the same list, two copies
of the display rule and none of the advantages of either side.

The honest decision is to choose per screen: this one is served by the
server, that one is a front-end application consuming the API. The two live
together in the same project without trouble — what does not live well is
the mixture inside one.
:::

:::note In your career
Vera did not ask for a screen out of conservatism. She asked because she
measures her work in seconds per person served, and nobody on the project
had that unit in their head.

Take this to any requirements gathering: **ask how many times a day the
person does that**. The answer changes the technical decision more than any
architectural preference — an operation done six hundred times a day
justifies a dedicated screen, and one done three times a month does not
justify even a button.

It is also the argument that works when you need to defend the choice in a
meeting where someone wants everything in the app.
:::

:::tree title="Where we are now"
casa-amarela/
  resources/views/
    components/
      layout.blade.php      # <x-layout>
    desk/
      index.blade.php       # open loans
      lend.blade.php        # the field and the button
      catalog.blade.php
  routes/
    web.php                 # the panel, with session and CSRF
    api.php                 # the reader app
:::

:::milestone
End of Part 2. Laravel is up, configured, with the designed routes
registered, controllers that translate instead of deciding, and the screen
the librarian will use at the counter. What is missing now is what sits
behind it: the data.
:::

:::summary
- Screen and API serve different situations; the question is who uses it and
  in what situation.
- A view is a `.blade.php` file; the controller assembles the data and
  chooses.
- `@forelse` brings the empty-list case along.
- `{{ }}` escapes the content and is what prevents XSS; `{!! !!}` is a
  security decision, not a formatting one.
- A component declares what it receives; `@include` sees everything of
  whoever included it.
- `@csrf` protects session forms; in an API it makes no sense because there
  is no cookie to forge.
- `old()` and `@error` give the form back filled in after a refusal.
- Redirecting after saving stops a page refresh from repeating the
  operation.
- Blade covers listing, form and report; an interface that never reloads is
  another job, and mixing the two is the worst of both worlds.
:::

:::checkpoint
You deliver a working screen with a listing and a form, explain what `{{ }}`
does and why `{!! !!}` is a decision, know why the form token exists in the
panel and not in the API, and can defend why the rest of the book remains an
API.
:::

:::exercise level=1
Say what is wrong in each piece of Blade:

```blade
<td>{!! $reader->name !!}</td>
```

```blade
<form method="POST" action="/desk/lend">
    <input name="accession">
    <button>Lend</button>
</form>
```

```blade
@php
    $total = 0;
    foreach ($loans as $l) {
        $total += $l->fine->inCents();
    }
@endphp
```

:::answer
**The first** prints, unescaped, data registered by a person. A reader's
name may contain `<` and `>` by mistake — or on purpose. It is `{{ }}`.

**The second** has no `@csrf`. The form will be refused with `419`, and —
worse than not working — if someone disables the protection to "fix" it, the
route is open to submissions from outside.

It is also worth swapping the hard-coded path for
`{{ route('desk.lend') }}`, for the reason in the previous chapter.

**The third** is a calculation in the view. It works and lives in the wrong
place: it has no test, cannot be reused by the API and forces whoever
touches the fine calculation to remember a `.blade.php` file.

The total comes ready from the controller, or from the object itself that
already knows how to add `Money`.
:::

:::exercise level=2
Write the return screen: a field for the accession number, a selector with
the copy's possible statuses and a button.

The selector must be built from the `CopyStatus` enum, without repeating the
list in the HTML.

:::answer
```blade title="resources/views/desk/return.blade.php" numbered
<x-layout title="Return">
    <form method="POST" action="{{ route('desk.return') }}">
        @csrf

        <label for="accession">Accession</label>
        <input id="accession" name="accession"
               value="{{ old('accession') }}" autofocus>

        @error('accession')
            <p class="error">{{ $message }}</p>
        @enderror

        <label for="status">Status on return</label>
        <select id="status" name="status">
            @foreach ($statuses as $status)
                <option value="{{ $status->value }}"
                    @selected(old('status') === $status->value)>
                    {{ $status->label() }}
                </option>
            @endforeach
        </select>

        <button>Return</button>
    </form>
</x-layout>
```

```php
return view('desk.return', [
    'statuses' => CopyStatus::forReturn(),
]);
```

Three decisions.

The `<option>`'s `value` is `$status->value` and the text is
`$status->label()` — exactly the separation in chapter
@cap:enums-datas-e-valores between what goes to the system and what the
person reads.

`@selected` is sugar for the `selected` attribute; it exists so that `old()`
also works on the selector, and not only on text fields.

And the list is not `CopyStatus::cases()`: it is a method that returns only
the statuses that make sense on a return. `on_loan` is not one of them, and
leaving `cases()` raw would offer Vera an option the service is going to
refuse.
:::

:::exercise level=3
The panel grew: seven screens, and each one has the same search-by-accession
block at the top. The code was copied seven times.

You get two proposals: turn the block into an `@include`, or into a
component. Choose, write the implementation and explain what would happen
with the other option six months from now.

:::answer
**Component**, and the file is anonymous — it needs no class:

```blade title="resources/views/components/accession-search.blade.php"
@props(['action', 'label' => 'Accession', 'value' => null])

<form method="GET" action="{{ $action }}" class="search">
    <label for="accession">{{ $label }}</label>
    <input id="accession" name="accession"
           value="{{ $value ?? request('accession') }}" autofocus>
    <button>Search</button>
</form>
```

```blade
<x-accession-search :action="route('desk.catalog')" />

<x-accession-search :action="route('desk.lend')"
                    label="Accession to lend" />
```

`@props` declares what the component accepts and the default value of each
thing. It is its signature — and Blade warns when something required is
missing.

**What would happen with `@include`.** It would work today, because the
seven screens happen to have the right variables in scope. The problem
arrives on the eighth.

Someone creates a new screen, includes the partial, and it uses `$action` —
which does not exist on that screen. The error appears at render time,
pointing at the partial's file, and whoever investigates will look at a file
that has been correct for six months.

After that, the common path is for the partial to gain a `?? ''` so it stops
breaking, and then the form silently points nowhere. It is the same path as
the `function_exists` in chapter @cap:do-include-ao-composer: the patch
erases the warning and keeps the defect.
:::
