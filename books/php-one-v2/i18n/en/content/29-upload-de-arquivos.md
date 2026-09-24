---
source_hash: 9f28e7c33628
title: "File uploads"
number: 29
slug: upload-de-arquivos
part: p8
kicker: "Vera photographed three hundred covers with her new phone. Half didn't upload. The other half uploaded lying on their side."
goal: >-
  Receive large files without being stopped by a limit you didn't
  configure, validate images by content and dimensions, choose between a
  private and a public disk, process the image outside the request, replace
  a file without leaving orphans, and test everything without touching the
  disk.
---

:::story On their side
In the first week of April, the association gave Vera a new phone and she
decided the collection would have covers. She spent three afternoons in the
storeroom, photographing book after book on top of a sheet of white card.

On Thursday, she opened the panel and started uploading. From the first to
the ninetieth, they all gave the same message:

```text
The cover failed to upload.
```

— In English — she told Tainá, over the phone. — And I don't even know what
*failed* means.

On Friday, Tainá ran the photos through the computer, which shrank them, and
the covers uploaded. All of them. On their side.

— On their side how?

— On their side. *Vidas Secas* with the title running top to bottom.
*O Cortiço* facing left. On the phone they're upright.

Dedé opened one of the original photos.

— Twelve megabytes — he said. — The server accepts two. And the phone doesn't
rotate the photo: it saves it sideways and writes a note in a corner of the
file saying "show upright". The browser reads the note. Our code doesn't.

Vera sighed.

— I took three hundred.
:::

## Three limits before your code

Chapter @cap:requests-e-responses covered upload security: name and
extension generated on our side, content checked, folder outside `public/`.
All of that happens inside Laravel. Vera's twelve-megabyte photo never got
there.

Between the phone and the controller there are three gatekeepers, and each
refuses in its own way:

| Where | Setting | Common default | What the client sees |
|---|---|---|---|
| web server | `client_max_body_size` (nginx) | 1 MB | `413` in HTML, before PHP |
| PHP | `upload_max_filesize` | 2 MB | the file arrives with an error: *failed to upload* |
| PHP | `post_max_size` | 8 MB | the whole body is discarded: Laravel's `413` |

Table: Three limits, three symptoms. Vera's was the second: PHP received the
request, discarded the file and told Laravel.

The second and third live in `php.ini`. `post_max_size` needs to be
**larger** than `upload_max_filesize`, because the request body carries the
file and the other fields along with it:

```ini title="/etc/php/8.3/fpm/conf.d/99-casa-amarela.ini"
upload_max_filesize = 12M
post_max_size = 14M
```

And nginx needs to agree with both:

```text title="/etc/nginx/sites-available/casa-amarela"
client_max_body_size 14m;
```

Those numbers open the door. What decides what gets in is validation, which
returns `422` with a message the app knows how to show — instead of a `413`
nobody knows how to read.

:::key
Configure the three gatekeepers with **headroom**, and put the real limit in
validation. The gatekeeper blocks with a generic error page; validation
blocks with a sentence on the right field, in the client's language.
:::

## Validating the image by what it is

The `'image'` rule from chapter @cap:requests-e-responses checks that the
file is an image. For a book cover, Casa Amarela needs more: a format the
browser displays, a maximum size, and a minimum resolution — a 100×150 pixel
cover becomes a smudge on screen.

```php title="app/Http/Requests/CoverRequest.php" numbered
public function rules(): array
{
    return [
        'cover' => [
            'required',
            File::image()
                ->types(['jpg', 'png', 'webp'])
                ->max('10mb')
                ->dimensions(
                    Rule::dimensions()->minWidth(300)->minHeight(400),
                ),
        ],
    ];
}
```

`File` is Laravel's fluent file rule, in
`Illuminate\Validation\Rules\File`. Each method adds a condition, and the
response carries one message for each one that fails:

```text
{"cover":["The cover field has invalid image dimensions."]}

{"cover":["The cover field must not be greater than 10000
kilobytes."]}
```

Notice the "10000". `'10mb'` is counted in multiples of a thousand — ten
thousand kilobytes, not 10,240. The difference is small and shows up exactly
on the 10.1 MB file someone swears is under ten.

The messages are in English because the project has not published its
Portuguese translation yet — and Vera reads Portuguese. Chapter
@cap:mail-e-notificacoes takes care of that, and of the same cause somewhere
else.

:::pitfall
An iPhone photo sometimes arrives as HEIC — a format the `types()` above
refuses and PHP's image extension cannot read. The iPhone's own browser
usually converts to JPEG on upload; the app, not necessarily. Agree on it
with Kauã: the app converts before sending, and the API accepts only what it
knows how to process.
:::

## Private disk, public disk

Laravel stores files on **disks**, declared in `config/filesystems.php`. A
new project comes with three:

| Disk | Where it writes | Who reads |
|---|---|---|
| `local` | `storage/app/private` | only the code |
| `public` | `storage/app/public` | the browser, through a link |
| `s3` | a cloud file service | depends on the configuration |

Table: The default disk is `local`, and it is private on purpose.

`public` becomes visible on the web through a symlink that a command creates
once per server:

```text
$ php artisan storage:link
```

It links `public/storage` to `storage/app/public`. A cover saved at
`covers/x.webp` on the `public` disk now answers at
`/storage/covers/x.webp` — and it is the disk's `url()` that builds that
address:

```php title="app/Http/Resources/BookResource.php" numbered
'cover_url' => $this->cover
    ? Storage::disk('public')->url($this->cover)
    : null,
```

The decision is simple to state: **what is for anyone to see goes on
`public`; the rest, on `local`**. The cover of *Vidas Secas* is public.
Vera's original twelve-megabyte photo doesn't need to be — and the donation
form signed by Seu Juvenal, with his CPF, must not be.

A private file goes out through a route, after the policy:

```php title="app/Http/Controllers/DonationFormController.php" numbered
public function __invoke(Donation $donation)
{
    $this->authorize('view', $donation);

    return Storage::disk('local')->download(
        $donation->form,
        "form-{$donation->id}.pdf",
    );
}
```

Switching disks is one line of `.env`. When the cover collection outgrows the
server's disk, `FILESYSTEM_DISK` and the `s3` credentials change, and the
code above stays the same — it is `Storage` doing for uploads what `DB` did
for the database.

## Processing after responding

Vera's photo needs three things before it becomes a cover: to be upright, to
be smaller and to change to a lighter format. None of them needs to happen
while the phone waits.

The controller keeps the original on the private disk and hands the rest to
the queue:

```php title="app/Http/Controllers/CoverController.php" numbered
public function __invoke(CoverRequest $request, Book $book)
{
    $original = $request->file('cover')
        ->store('covers/originals', 'local');

    PrepareCover::dispatch($book->id, $original);

    return response()->json(['status' => 'processing'], 202);
}
```

`202 Accepted` is chapter @cap:o-que-e-uma-api-rest's status for "received
and not finished yet". The app shows the cover when the book's `cover_url`
stops being `null`.

And the job does the work with the GD extension, which comes with most PHP
installations:

```php title="app/Jobs/PrepareCover.php" numbered
public function handle(): void
{
    $book = Book::find($this->bookId);
    if ($book === null) {
        return;
    }

    $path = Storage::disk('local')->path($this->original);

    $image = imagecreatefromstring(file_get_contents($path));
    $image = $this->straighten($image, $path);
    $image = imagescale($image, 600);

    $target = 'covers/' . Str::uuid() . '.webp';
    Storage::disk('public')->put($target, $this->toWebp($image));

    $this->replaceCover($book, $target);
    Storage::disk('local')->delete($this->original);
}
```

`imagescale($image, 600)` reduces the width to 600 pixels and calculates the
height proportionally. A 3000×4000 photo becomes 600×800, and twelve
megabytes become about sixty kilobytes in WebP.

The "show upright" note is called **EXIF**: data the camera writes inside
the JPEG, including the orientation. Reading and applying it:

```php title="app/Jobs/PrepareCover.php (continued)" numbered
private function straighten(GdImage $image, string $path): GdImage
{
    if (mime_content_type($path) !== 'image/jpeg') {
        return $image;
    }

    $exif = exif_read_data($path) ?: [];
    $degrees = match ($exif['Orientation'] ?? 1) {
        3 => 180,
        6 => -90,
        8 => 90,
        default => 0,
    };

    return $degrees === 0 ? $image : imagerotate($image, $degrees, 0);
}

private function toWebp(GdImage $image): string
{
    ob_start();
    imagewebp($image, null, 80);
    return (string) ob_get_clean();
}
```

The `if` at the start is not decoration. PNG and WebP have no EXIF, and
`exif_read_data` on a PNG emits a *warning* — which, in Laravel, becomes an
exception, as chapter @cap:erros-e-debug's `bootstrap.php` did. Without the
`if`, every PNG cover would fail in the queue.

`imagewebp` writes straight to the output; `ob_start` and `ob_get_clean`
capture that output into a string, which `Storage` writes wherever the disk
says.

:::note
In projects with lots of images, a library like Intervention Image hides GD
behind a shorter interface — and handles orientation with a single method.
For one cover per book, the twenty lines above are enough, and you know what
each one does.
:::

## Replacing without leaving orphans

When Vera retakes the photo of *O Cortiço*, the new cover goes in and the
old one needs to go out. The order matters, because the database and the
disk do not take part in the same transaction:

```php title="app/Jobs/PrepareCover.php (continued)" numbered
private function replaceCover(Book $book, string $new): void
{
    $old = $book->cover;

    try {
        $book->update(['cover' => $new]);
    } catch (Throwable $e) {
        Storage::disk('public')->delete($new);
        throw $e;
    }

    if ($old !== null) {
        Storage::disk('public')->delete($old);
    }
}
```

**First the new file, then the database, last the old file.** If the
`update` fails, the new file goes and the book keeps its old cover, intact.
If deleting the old one fails, a file without an owner is left over — a
waste of space, and not a book without a cover.

It is the "write to a temporary file and rename at the end" from chapter
@cap:manipulacao-de-arquivos, now with a database in the middle: at no
instant does the system show half a cover or point to a file that doesn't
exist.

:::key
When an operation touches both the database and the disk, order the steps so
that a failure in any of them leaves **leftovers**, never **gaps**.
Leftovers get cleaned up later, with a scheduled command that compares the
disk with the table. A gap is the broken cover on the reader's screen.
:::

## Testing without a disk and without a queue

`Storage::fake` swaps a disk for a temporary folder, which disappears at the
end of the test. `UploadedFile::fake()->image()` makes a real image, with the
requested dimensions:

```php title="tests/Feature/CoverTest.php" numbered
test('accepts the cover and leaves the work to the queue', function () {
    Storage::fake('local');
    Queue::fake();
    $book = Book::factory()->create();

    $this->actingAs(User::factory()->clerk()->create())
        ->postJson("/api/books/{$book->id}/cover", [
            'cover' => UploadedFile::fake()
                ->image('cover.jpg', 800, 1200),
        ])
        ->assertStatus(202);

    Queue::assertPushed(PrepareCover::class);
    expect(Storage::disk('local')->allFiles('covers/originals'))
        ->toHaveCount(1);
});

test('prepares the cover as webp at 600 wide', function () {
    Storage::fake('local');
    Storage::fake('public');
    $book = Book::factory()->create();
    $original = UploadedFile::fake()->image('cover.jpg', 800, 1200)
        ->store('covers/originals', 'local');

    (new PrepareCover($book->id, $original))->handle();

    $cover = Storage::disk('public')->get($book->fresh()->cover);
    [$width, $height] = getimagesizefromstring($cover);

    expect([$width, $height])->toBe([600, 900]);
    Storage::disk('local')->assertMissing($original);
});
```

The first test proves the contract: `202`, original stored, job in the queue.
The second calls `handle` directly and proves the work: width 600, height in
proportion, original deleted. Neither writes anything to the real disk, and
both run in under a second.

`UploadedFile::fake()->image()` needs the GD extension in the PHP that runs
the tests — the same one the job uses. If the pipeline from chapter
@cap:git-ci-e-deploy doesn't have it, the test fails with a message that
says so.

:::note In your career
User-uploaded files are the data that grows most and that fewest people
remember to back up. The database backup runs every night; the
`storage/app` folder is left out because "it's just images".

The day the server's disk dies, Vera's four thousand covers vanish, and each
one cost a photo on top of a sheet of white card. Ask, on the same day the
first upload goes to production: **who copies `storage/`, and where to?** If
the answer is `s3`, the question becomes "who copies `s3`".
:::

:::tree title="Where we are now"
casa-amarela/
  app/
    Http/Controllers/
      CoverController.php         # 202: store and enqueue
      DonationFormController.php  # private download, with policy
    Http/Requests/CoverRequest.php # type, size, dimensions
    Jobs/PrepareCover.php         # EXIF, 600px, WebP, replace
  storage/app/
    private/covers/originals/     # what Vera sent
    public/covers/                # what the reader sees
:::

:::summary
- The web server, `upload_max_filesize` and `post_max_size` block before
  Laravel. Configure them with headroom; the real limit lives in validation.
- `File::image()->types()->max()->dimensions()` validates by content;
  `'10mb'` is ten thousand kilobytes.
- The `local` disk is private; `public` appears on the web through
  `storage:link`. A sensitive file goes out through a route, after the
  policy.
- Keep the original, respond `202` and process in the queue.
- A phone photo carries its orientation in EXIF; apply it before shrinking.
- Replace files in the order new → database → old: a failure leaves
  leftovers, never gaps.
- `Storage::fake` and `UploadedFile::fake()->image()` test without a disk.
:::

:::checkpoint
You configure upload limits from the server to Laravel, validate images by
type, size and dimensions, choose between a private and a public disk,
process the image in a queue, replace files without leaving a book without a
cover, and test the whole path without touching the disk.
:::

:::exercise level=1
For each symptom, say which gatekeeper blocked it and what to change:

1. The app receives an HTML page with "413 Request Entity Too Large".
2. The API responds `422` with *"The cover failed to upload."*.
3. The API responds `413` in JSON, and the form's other fields also
   disappeared.

:::answer
1. nginx, with `client_max_body_size`. PHP never saw the request.
2. PHP, with `upload_max_filesize`. The body arrived, the file was
   discarded, and Laravel reported that it did not upload.
3. PHP, with `post_max_size`. The whole body was discarded — that is why the
   other fields disappeared —, and Laravel responded with
   `PostTooLargeException`.
:::

:::exercise level=2
The donation form is a PDF of up to 5 MB. Write the validation rule and say
which disk it goes on and why. Then write the test that proves an ordinary
reader gets `403` when trying to download it.

:::answer
```php
'form' => ['required', File::types(['pdf'])->max('5mb')],
```

The `local` disk: the form has a name, an address and a CPF. It only goes out
through `DonationFormController`'s route, after the policy.

```php
test('an ordinary reader cannot download a donation form', function () {
    Storage::fake('local');
    $donation = Donation::factory()->create([
        'form' => UploadedFile::fake()
            ->create('form.pdf', 100, 'application/pdf')
            ->store('forms', 'local'),
    ]);

    $this->actingAs(User::factory()->reader()->create())
        ->get("/api/donations/{$donation->id}/form")
        ->assertForbidden();
});
```
:::

:::exercise level=3
Six months later, the server's disk is 70% full, and the
`storage/app/public/covers` folder has 11,000 files for 4,000 books. Explain
where the extra 7,000 came from, and design the scheduled command that
cleans them up with no risk of deleting a cover in use.

:::answer
They came from the leftovers the new → database → old order accepts: deletes
of old files that failed, jobs that wrote the cover and crashed before the
`update`, covers replaced several times during Vera's tests.

The command, `covers:clean`, scheduled once a week:

1. Lists the files in `covers/` on the `public` disk.
2. Lists the values of the `cover` column in `books`.
3. Deletes the files that are in the first set and not in the second — and
   **only those modified more than a day ago**, so as not to delete the cover
   a job has just written and not yet recorded in the database.
4. Logs how many it deleted.

Step 3's rule is what makes the command safe: it never competes with a
`PrepareCover` in progress. Before running it for real, a `--dry-run` option
that only lists what would be deleted is the kind of care Vera will never
know existed.
:::
