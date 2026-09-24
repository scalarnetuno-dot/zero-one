---
source_hash: 3aaf2e0591f4
title: "Mail and notifications"
number: 30
slug: mail-e-notificacoes
part: p8
kicker: "Casa Amarela's first e-mail was signed by someone called Laravel, from hello@example.com. Dona Marlene printed it and brought it to the counter as proof of the scam."
goal: >-
  Separate e-mail that is a document from a notice that is a notification,
  configure who signs what goes out, carry the same notice by e-mail,
  WhatsApp and in-app history with a single class, put each channel on the
  queue without one's failure repeating another, speak the readers'
  language, reach the inbox and test without sending anything.
---

:::story Someone called Laravel
The WhatsApp provider's bill arrived in April: nine centavos per message,
three hundred messages a day. Márcia did the math in front of Seu Juvenal,
who did the same math again, more slowly.

— Is e-mail free? — he asked.

— Almost — said Dedé.

The following Monday, the "your book is due tomorrow" notice started going
out by e-mail too. On Tuesday, at five past nine, Dona Marlene was at the
counter with a printed sheet, folded in four.

— Vera, look at this. My grandson says it's a scam.

Vera unfolded the sheet. At the top, in big letters: **Laravel**. Below,
*Hello!* Then, in Portuguese, the book's title and a *Renovar* button. At the
end: *Regards, Laravel*. And the sender: `hello@example.com`.

— Who's Laravel? — asked Dona Marlene.

— It's... — Vera searched for the word — ...the system.

— The system is called Laravel?

— The system is called Casa Amarela.

— Then why does it sign Laravel?

Vera photographed the sheet and sent it to Tainá, with a single word:
*"Laravel?"*

Tainá opened the production `.env`.

```text
APP_NAME=Laravel
MAIL_FROM_ADDRESS="hello@example.com"
MAIL_FROM_NAME="${APP_NAME}"
```

— They're the factory defaults — she told Dedé. — We never changed them.
Nobody had ever received an e-mail from us.
:::

## Document or notice

Laravel has two ways of sending a message, and they answer different
questions.

A **Mailable** is an e-mail. It has a subject, a body and attachments, and
goes to an address. It is for what is a **document**: the signed donation
form, the clearance certificate the student takes to school.

A **notification** is a fact that needs to reach a **person**, through the
channel they use: e-mail, WhatsApp, the app's bell icon. "Your book is due
tomorrow" is a notification. Dona Marlene wants it by e-mail; Seu Juvenal
wants it by WhatsApp; both want to see it in Kauã's app.

| Question | Mailable | Notification |
|---|---|---|
| What is it? | an e-mail | a fact about someone |
| To whom? | an address | an object that receives notices |
| Through what? | e-mail | as many channels as the person has |
| Example | donation form as PDF | "due tomorrow", "reservation available" |

Table: When the text only makes sense as an e-mail, Mailable. When the fact
needs to arrive one way or another, notification.

:::art caption="The system is called Casa Amarela. The e-mail was signed Laravel."
src="o-sistema-se-chama-casa-amarela-o-e-mail-assinava-laravel.png"
Minimalist editorial cartoon on a white background: a seventy-nine-year-old
lady in a cardigan spreads across a library counter a printed sheet,
unfolded in four, which reads at the top, in big letters, "Laravel", and at
the bottom "Regards, Laravel". An older librarian in glasses looks at the
sheet with raised eyebrows, phone in hand ready to take a picture. Behind
the counter, a little yellow house drawn on a poster on the wall. Few
elements, dry humor, tech-magazine aesthetic.
:::

## Who signs what goes out

Before any class, the `.env` — which is where Dona Marlene's problem was:

```text title=".env (production)"
APP_NAME="Biblioteca Casa Amarela"
APP_LOCALE=pt_BR

MAIL_MAILER=smtp
MAIL_HOST=smtp.provider.com.br
MAIL_PORT=587
MAIL_USERNAME=notices@casaamarela.org.br
MAIL_PASSWORD=
MAIL_FROM_ADDRESS="notices@casaamarela.org.br"
MAIL_FROM_NAME="${APP_NAME}"
```

`APP_NAME` appears in three places in the default e-mail — the header, the
signature and the *copyright* footer — and had become "Laravel" in all
three. `MAIL_FROM_ADDRESS` is the sender; `example.com` is a domain reserved
for examples, and no serious provider delivers e-mail claiming to come from
there.

On your machine, e-mail does not go out:

```text title=".env (local)"
MAIL_MAILER=log
```

The `log` driver writes the whole e-mail into `storage/logs/laravel.log`,
instead of sending it. To see the e-mail rendered, a tool like Mailpit
pretends to be a mail server and shows everything on a local page.

:::warning
Never copy the production `.env` to your machine "to test with real data".
With it comes `MAIL_MAILER=smtp`, and the first scheduled command you run
tells a thousand readers their book is due tomorrow — a book they returned in
March.
:::

## The notification

```text
$ php artisan make:notification ReturnTomorrow
```

The reader starts receiving notices with a trait:

```php title="app/Models/Reader.php" numbered
class Reader extends Model
{
    use Notifiable;

    // ...
}
```

`Notifiable` gives the model the `notify()` method and knows, by default,
that the e-mail address is in the `email` column. And the notification says
what to say and through where:

```php title="app/Notifications/ReturnTomorrow.php" numbered
final class ReturnTomorrow extends Notification implements
    ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly Loan $loan,
    ) {
        $this->afterCommit();
    }

    public function via(Reader $reader): array
    {
        return array_values(array_filter([
            $reader->email !== null ? 'mail' : null,
            $reader->accepts_whatsapp ? WhatsAppChannel::class : null,
            'database',
        ]));
    }

    public function toMail(Reader $reader): MailMessage
    {
        $title = $this->loan->copy->book->title;

        return (new MailMessage)
            ->subject("\"{$title}\" is due tomorrow")
            ->greeting("Hello, {$reader->name}!")
            ->line("The loan period for \"{$title}\" ends tomorrow.")
            ->line('If you need more time, you can renew it.')
            ->action('Renew', $this->renewalLink());
    }

    public function toWhatsApp(Reader $reader): string
    {
        return sprintf(
            '"%s" is due tomorrow. Renew it in the app.',
            $this->loan->copy->book->title,
        );
    }

    public function toArray(Reader $reader): array
    {
        return [
            'loan_id' => $this->loan->id,
            'due_on' => $this->loan->due_on
                ->toDateString(),
        ];
    }
}
```

Four methods, one responsibility each.

**`via`** chooses the channels **for that person**. Whoever has no e-mail
gets no e-mail; whoever did not accept WhatsApp — a new boolean column on
`readers`, `accepts_whatsapp` — gets no WhatsApp; everyone gets it in their
history.

**`toMail`** builds the e-mail with a `MailMessage`: subject, greeting,
lines and a button. Laravel renders the HTML, with the plain-text version
alongside.

**`toWhatsApp`** is the text the custom channel, just below, will send.

**`toArray`** is what the `database` channel writes into the
`notifications` table, created by `php artisan make:notifications-table`.
Kauã's app lists `$reader->notifications` and draws the bell.

And the schedule from chapter @cap:events-jobs-e-filas now notifies instead
of calling the sender directly:

```php title="routes/console.php" numbered
Schedule::call(function () {
    Loan::open()
        ->whereDate('due_on', today()->addDay())
        ->with('reader', 'copy.book')
        ->each(fn (Loan $l) => $l->reader->notify(
            new ReturnTomorrow($l),
        ));
})->dailyAt('09:00')->name('return-notices');
```

## A channel Laravel doesn't have

Casa Amarela's WhatsApp already existed: it is the `NoticeSender` from
chapter @cap:service-container, with the provider behind an interface. A
custom channel is a class with a `send` method:

```php title="app/Notifications/Channels/WhatsAppChannel.php" numbered
final class WhatsAppChannel
{
    public function __construct(
        private readonly NoticeSender $notices,
    ) {}

    public function send(Reader $reader, Notification $notice): void
    {
        $this->notices->send($reader, $notice->toWhatsApp($reader));
    }
}
```

`via` returns the class name, and Laravel builds it through the container —
with the `NoticeSender` that `NoticeServiceProvider` already registers. Not
one line of the sender changed: it gained one more client.

## One job per channel

The notification implements `ShouldQueue`, and that does more than it seems.
For Dona Marlene, with e-mail, WhatsApp and history, `notify()` does not
create **one** job: it creates **three**, one per channel.

It is the rule from chapter @cap:events-jobs-e-filas — a job is the smallest
unit that makes sense to repeat — applied without you writing anything. If
the WhatsApp provider goes down, only the WhatsApp job goes back to the
queue. The e-mail, which already went out, does not go out again. Dona
Iolanda, of the fourteen hundred messages, would be grateful.

The `afterCommit()` in the constructor is the same care as that chapter's
events: if the notification is dispatched inside a transaction, it only
enters the queue after the `commit`. A "reservation available" notice cannot
go out for a reservation the `rollback` undid.

:::key
A queued notification becomes one job per channel. Write each `toX` as if it
could run alone, hours later, and more than once: fetch what it needs, check
whether the notice still makes sense, and don't depend on what another
channel did.
:::

## In the readers' language

With the right `APP_NAME`, the e-mail still goes out half in English. Casa
Amarela's readers are Brazilian, and the lines the project writes itself go
out in Portuguese — in this edition they appear in English, like the rest of
the code. But Laravel's default template brings three phrases of its own:
the sign-off, the footer and the instruction for whoever cannot click the
button.

They pass through the translation function, and `APP_LOCALE=pt_BR` tells it
to look in `lang/pt_BR.json`:

```json title="lang/pt_BR.json"
{
    "Regards,": "Até logo,",
    "All rights reserved.": "Todos os direitos reservados.",
    "If you're having trouble clicking ...": "Se o botão ..."
}
```

The key is the **exact** original text. The first two are short. The third
— abbreviated above — is the button's whole sentence, with a `\n` line break
in the middle, escaped quotes and the `:actionText` placeholder, which
Laravel replaces with the button's label in both languages. Copy it from the
template, in
`vendor/laravel/framework/src/Illuminate/Notifications/resources/views/email.blade.php`,
instead of typing it: one comma fewer in the key, and the sentence stays in
English, with no error at all.

The validation messages from chapter @cap:upload-de-arquivos, *"The cover
field has invalid image dimensions"*, have the same cause and the same
remedy, in `lang/pt_BR/validation.php`. Community packages bring both
translations ready-made; it is worth checking them before the first e-mail,
and not after the first Dona Marlene.

## Reaching the inbox

An e-mail with the right name and in the right language can still land in
spam. Mail providers decide based on who claims to have sent it, and check
that in the domain's DNS:

| Record | What it tells the provider |
|---|---|
| SPF | which servers may send e-mail for `casaamarela.org.br` |
| DKIM | a signature proving the message was not altered |
| DMARC | what to do with e-mail that fails the previous two |

Table: The three records come ready from the sending provider; someone with
access to the domain's DNS needs to paste them in.

At Casa Amarela, the DNS access was on Nonato's folded paper. It took a week
to find the login for the domain registrar, and ten minutes to paste the
three records.

And a rule of good manners: a due-date notice is a **service** message, and
the reader can turn it off in the app — the `accepts_whatsapp` column and a
sibling for e-mail. A **promotional** message — the book fair, the Saturday
workshop — only goes to those who asked to receive it. That difference is
not courtesy: it is the LGPD, Brazil's data protection law.

## The document, as a Mailable

The donation form from chapter @cap:upload-de-arquivos needs to go back,
signed, to the donor. That is a document, and it goes as a Mailable:

```text
$ php artisan make:mail SignedDonationForm --markdown=mail.form
```

```php title="app/Mail/SignedDonationForm.php" numbered
final class SignedDonationForm extends Mailable implements
    ShouldQueue
{
    use Queueable, SerializesModels;

    public function __construct(public readonly Donation $donation) {}

    public function envelope(): Envelope
    {
        return new Envelope(subject: 'Your donation form');
    }

    public function content(): Content
    {
        return new Content(markdown: 'mail.form');
    }

    public function attachments(): array
    {
        return [
            Attachment::fromStorageDisk('local', $this->donation->form)
                ->as('donation-form.pdf')
                ->withMime('application/pdf'),
        ];
    }
}
```

```php
Mail::to($donation->donor_email)
    ->send(new SignedDonationForm($donation));
```

The `ShouldQueue` on the class makes `send` go to the queue. The attachment
comes from the private disk — the same one `DonationFormController` serves it
from — without passing through any public folder.

## Testing without sending

```php title="tests/Feature/ReturnNoticeTest.php" numbered
test('notifies by e-mail and WhatsApp whoever accepted both', function () {
    Notification::fake();
    $loan = Loan::factory()
        ->dueTomorrow()
        ->for(Reader::factory()->withEmail()->acceptsWhatsApp())
        ->create();

    $this->artisan('schedule:test', [
        '--name' => 'return-notices',
    ]);

    Notification::assertSentTo(
        $loan->reader,
        ReturnTomorrow::class,
        fn ($notice, array $channels) => $channels === [
            'mail', WhatsAppChannel::class, 'database',
        ],
    );
});

test('e-mail in Portuguese, signed by Casa Amarela', function () {
    config(['app.name' => 'Biblioteca Casa Amarela']);
    app()->setLocale('pt_BR');
    $loan = Loan::factory()->dueTomorrow()->create();

    $html = (string) (new ReturnTomorrow($loan))
        ->toMail($loan->reader)
        ->render();

    expect($html)
        ->toContain('Biblioteca Casa Amarela')
        ->toContain('Até logo')
        ->not->toContain('Laravel')
        ->not->toContain('Regards');
});
```

`Notification::fake()` intercepts `notify()`: nothing goes to the queue, no
channel is called, and the test asks afterwards what **would** have been
sent, to whom and through what. The second test renders the real e-mail and
checks the text — it is the test that would have spared Dona Marlene a trip
to the counter.

`Mail::fake()` does the same for Mailables, with `Mail::assertQueued`.

:::note In your career
E-mail is the only part of the system that ends up in people's homes without
them having opened anything. An error on screen, the reader closes it. An
error in an e-mail, they print it and bring it to the counter.

Before the first send in production, send the e-mail to yourself, from the
production server, and read it all on your phone — sender, subject, header,
footer, the button, and the small print below it. It takes five minutes, and
it is the only review that looks at what the reader will look at.
:::

:::tree title="Where we are now"
casa-amarela/
  app/
    Mail/SignedDonationForm.php      # document, with private attachment
    Notifications/
      ReturnTomorrow.php             # mail, WhatsApp, database
      Channels/WhatsAppChannel.php   # uses NoticeSender
    Models/Reader.php                # Notifiable
  lang/pt_BR.json                    # the e-mail template in Portuguese
  resources/views/mail/form.blade.php
:::

:::summary
- A Mailable is a document; a notification is a fact that reaches a person
  through as many channels as they have.
- `APP_NAME`, `MAIL_FROM_ADDRESS` and `MAIL_FROM_NAME` sign the e-mail. The
  factory values say "Laravel" and `hello@example.com`.
- On a local machine, `MAIL_MAILER=log`. Never the production `.env`.
- `via()` chooses the channels per person; `toMail`, `toArray` and one `toX`
  per custom channel say what to send.
- A custom channel is a class with `send`, built by the container.
- A queued notification becomes one job per channel; `afterCommit()` waits
  for the transaction.
- The default template is translated through `lang/pt_BR.json`, with the
  exact key.
- SPF, DKIM and DMARC in the DNS; service messages can be turned off,
  promotional ones only with consent.
- `Notification::fake()` and `Mail::fake()` test without sending.
:::

:::checkpoint
You choose between a Mailable and a notification, configure sender and
language before the first send, send the same notice through several
channels with one class, write a custom channel on top of a service that
already existed, put each channel on the queue without repeating the others,
and test what would be sent without sending anything.
:::

:::exercise level=1
Mailable or notification?

1. "Your reservation of *Capitães da Areia* is available until Friday."
2. The monthly donations receipt, as a PDF, for the association's
   accountant.
3. "Your fine of R$ 4.80 has been forgiven."
4. The clearance certificate the student requested through the app.

:::answer
1. Notification. It is a fact about the reader, and they want to hear it
   through the channel they use.
2. Mailable. It is a document, with an attachment, for an address — the
   accountant isn't even a reader.
3. Notification — it is the `FineForgiven` from Vera's latest request, in
   chapter @cap:git-ci-e-deploy.
4. Mailable. The student will print or forward it; what matters is the
   document, not the notice.
:::

:::exercise level=2
Write the `ReservationAvailable` notification, with e-mail and history, and a
`via` that sends **nothing** if the reservation was cancelled between the
dispatch and the execution in the queue.

:::answer
```php
final class ReservationAvailable extends Notification implements
    ShouldQueue
{
    use Queueable;

    public function __construct(public readonly Reservation $reservation)
    {
        $this->afterCommit();
    }

    public function via(Reader $reader): array
    {
        if ($this->reservation->fresh()?->cancelled()) {
            return [];
        }
        return $reader->email !== null
            ? ['mail', 'database']
            : ['database'];
    }

    public function toMail(Reader $reader): MailMessage
    {
        return (new MailMessage)
            ->subject('Your reservation is available')
            ->line(sprintf(
                '"%s" is set aside for you until %s.',
                $this->reservation->book->title,
                $this->reservation->expires_at->format('d/m'),
            ));
    }

    public function toArray(Reader $reader): array
    {
        return ['reservation_id' => $this->reservation->id];
    }
}
```

`via` returning `[]` makes the notification go out through no channel.
`fresh()` fetches the reservation from the database again: the object that
came through the queue is a snapshot of the moment of dispatch.
:::

:::exercise level=3
A month later, Márcia gets the e-mail provider's bill: 9,000 sends, for 1,200
active readers. The schedule runs once a day. List three possible causes, in
order of investigation, and what you would check to confirm each one.

:::answer
1. **The schedule runs on more than one server.** If the application gained
   a second server and both have the scheduler on, each notice goes out
   twice. Confirm in the log: two "return-notices" in the same minute, from
   different machines. Fix: `->onOneServer()` on the schedule.
2. **A channel failing and retrying the e-mail with it.** It shouldn't —
   they are separate jobs —, but a notification written as a single job that
   calls all three channels would have that effect. Confirm in `failed_jobs`
   and in the WhatsApp job's retries.
3. **The query picks up more people than it should.** A `whereDate` with the
   wrong time zone — chapter @cap:datas-e-horarios — can include those due
   today and tomorrow. Confirm by counting, for one day, how many loans the
   query returns and how many are actually due the next day.

Nine thousand for twelve hundred readers in thirty days is three hundred a
day — exactly the number of loans due per day. Before the three hypotheses,
the simplest math is worth doing: maybe there is no defect at all, and the
bill is simply the first one.
:::
