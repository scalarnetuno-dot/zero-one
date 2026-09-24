---
title: "Mail e notificações"
number: 30
slug: mail-e-notificacoes
part: p8
kicker: "O primeiro e-mail da Casa Amarela foi assinado por um tal de Laravel, de hello@example.com. A Dona Marlene imprimiu e levou ao balcão como prova do golpe."
goal: >-
  Separar e-mail que é documento de aviso que é notificação, configurar
  quem assina o que sai, levar o mesmo aviso por e-mail, WhatsApp e
  histórico no aplicativo com uma classe só, pôr cada canal na fila sem que
  a falha de um repita o outro, falar português, chegar à caixa de entrada
  e testar sem mandar nada.
---

:::story Um tal de Laravel
A conta do provedor de WhatsApp chegou em abril: nove centavos por
mensagem, trezentas mensagens por dia. A Márcia fez a conta na frente do
Seu Juvenal, que fez a mesma conta de novo, mais devagar.

— E-mail é de graça? — perguntou ele.

— Quase — disse o Dedé.

Na segunda seguinte, o aviso de "seu livro vence amanhã" passou a sair
também por e-mail. Na terça, às nove e cinco, a Dona Marlene estava no
balcão com uma folha impressa, dobrada em quatro.

— Vera, olha isso. Meu neto disse que é golpe.

A Vera desdobrou a folha. No alto, em letras grandes: **Laravel**.
Embaixo, *Hello!* Depois, em português, o título do livro e um botão
*Renovar*. No fim: *Regards, Laravel*. E o remetente:
`hello@example.com`.

— Quem é Laravel? — perguntou a Dona Marlene.

— É... — a Vera procurou a palavra — ...o sistema.

— O sistema se chama Laravel?

— O sistema se chama Casa Amarela.

— Então por que ele assina Laravel?

A Vera fotografou a folha e mandou para a Tainá, com uma única palavra:
*"Laravel?"*

A Tainá abriu o `.env` de produção.

```text
APP_NAME=Laravel
MAIL_FROM_ADDRESS="hello@example.com"
MAIL_FROM_NAME="${APP_NAME}"
```

— São os valores de fábrica — disse ela ao Dedé. — A gente nunca trocou.
Ninguém nunca tinha recebido um e-mail nosso.
:::

## Documento ou aviso

O Laravel tem duas formas de mandar mensagem, e elas respondem a perguntas
diferentes.

Um **Mailable** é um e-mail. Tem assunto, corpo e anexos, e vai para um
endereço. Serve para o que é **documento**: o termo de doação assinado, a
declaração de nada consta que o estudante leva à escola.

Uma **notificação** é um fato que precisa chegar a uma **pessoa**, pelo
canal que ela usa: e-mail, WhatsApp, o sininho do aplicativo. "Seu livro
vence amanhã" é notificação. A Dona Marlene quer por e-mail; o Seu Juvenal
quer por WhatsApp; os dois querem ver no aplicativo do Kauã.

| Pergunta | Mailable | Notificação |
|---|---|---|
| O que é? | um e-mail | um fato sobre alguém |
| Para quem? | um endereço | um objeto que recebe avisos |
| Por onde? | e-mail | quantos canais a pessoa tiver |
| Exemplo | termo de doação em PDF | "vence amanhã", "reserva disponível" |

Tabela: Quando o texto só faz sentido como e-mail, Mailable. Quando o fato
precisa chegar de qualquer jeito, notificação.

:::art caption="O sistema se chama Casa Amarela. O e-mail assinava Laravel."
src="o-sistema-se-chama-casa-amarela-o-e-mail-assinava-laravel.png"
Charge editorial minimalista em fundo branco: uma senhora de setenta e
nove anos, de cardigã, estende sobre um balcão de biblioteca uma folha
impressa, desdobrada em quatro, onde se lê no topo, em letras grandes,
"Laravel", e no rodapé "Regards, Laravel". Uma bibliotecária mais velha,
de óculos, olha a folha com as sobrancelhas erguidas, o celular na mão
pronto para fotografar. Atrás do balcão, uma casinha amarela desenhada
num cartaz na parede. Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## Quem assina o que sai

Antes de qualquer classe, o `.env` — que é onde o problema da Dona Marlene
estava:

```text title=".env (produção)"
APP_NAME="Biblioteca Casa Amarela"
APP_LOCALE=pt_BR

MAIL_MAILER=smtp
MAIL_HOST=smtp.provedor.com.br
MAIL_PORT=587
MAIL_USERNAME=avisos@casaamarela.org.br
MAIL_PASSWORD=
MAIL_FROM_ADDRESS="avisos@casaamarela.org.br"
MAIL_FROM_NAME="${APP_NAME}"
```

O `APP_NAME` aparece em três lugares do e-mail padrão — o cabeçalho, a
assinatura e o rodapé de *copyright* — e virou "Laravel" nos três. O
`MAIL_FROM_ADDRESS` é o remetente; `example.com` é um domínio reservado
para exemplos, e nenhum provedor sério entrega e-mail que diz vir de lá.

Na sua máquina, e-mail não sai:

```text title=".env (local)"
MAIL_MAILER=log
```

O driver `log` escreve o e-mail inteiro no `storage/logs/laravel.log`, em
vez de mandá-lo. Para ver o e-mail desenhado, uma ferramenta como o
Mailpit finge ser um servidor de e-mail e mostra tudo numa página local.

:::warning
Nunca copie o `.env` de produção para a sua máquina "para testar com os
dados de verdade". Com ele vem o `MAIL_MAILER=smtp`, e o primeiro comando
agendado que você rodar avisa mil leitores de que o livro deles vence
amanhã — de um livro que eles devolveram em março.
:::

## A notificação

```text
$ php artisan make:notification DevolucaoAmanha
```

O leitor passa a receber avisos com uma trait:

```php title="app/Models/Leitor.php" numbered
class Leitor extends Model
{
    use Notifiable;

    // ...
}
```

`Notifiable` dá ao model o método `notify()` e sabe, por padrão, que o
endereço de e-mail está na coluna `email`. E a notificação diz o que dizer
e por onde:

```php title="app/Notifications/DevolucaoAmanha.php" numbered
final class DevolucaoAmanha extends Notification implements
    ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly Emprestimo $emprestimo,
    ) {
        $this->afterCommit();
    }

    public function via(Leitor $leitor): array
    {
        return array_values(array_filter([
            $leitor->email !== null ? 'mail' : null,
            $leitor->aceita_whatsapp ? CanalWhatsApp::class : null,
            'database',
        ]));
    }

    public function toMail(Leitor $leitor): MailMessage
    {
        $titulo = $this->emprestimo->exemplar->livro->titulo;

        return (new MailMessage)
            ->subject("\"{$titulo}\" vence amanhã")
            ->greeting("Olá, {$leitor->nome}!")
            ->line("O prazo de \"{$titulo}\" termina amanhã.")
            ->line('Se precisar de mais tempo, dá para renovar.')
            ->action('Renovar', $this->linkDeRenovacao());
    }

    public function toWhatsApp(Leitor $leitor): string
    {
        return sprintf(
            '"%s" vence amanhã. Renove pelo aplicativo.',
            $this->emprestimo->exemplar->livro->titulo,
        );
    }

    public function toArray(Leitor $leitor): array
    {
        return [
            'emprestimo_id' => $this->emprestimo->id,
            'devolver_ate' => $this->emprestimo->devolver_ate
                ->toDateString(),
        ];
    }
}
```

Quatro métodos, uma responsabilidade cada.

**`via`** escolhe os canais **para aquela pessoa**. Quem não tem e-mail não
recebe e-mail; quem não aceitou WhatsApp — uma coluna booleana nova em
`leitores`, `aceita_whatsapp` — não recebe WhatsApp; todo mundo recebe no
histórico.

**`toMail`** monta o e-mail com uma `MailMessage`: assunto, saudação,
linhas e um botão. O Laravel desenha o HTML, com a versão em texto puro
junto.

**`toWhatsApp`** é o texto que o canal próprio, logo abaixo, vai enviar.

**`toArray`** é o que o canal `database` grava na tabela `notifications`,
criada por `php artisan make:notifications-table`. O aplicativo do Kauã
lista `$leitor->notifications` e desenha o sininho.

E o agendamento do capítulo @cap:events-jobs-e-filas passa a notificar em
vez de chamar o enviador direto:

```php title="routes/console.php" numbered
Schedule::call(function () {
    Emprestimo::emAberto()
        ->whereDate('devolver_ate', today()->addDay())
        ->with('leitor', 'exemplar.livro')
        ->each(fn (Emprestimo $e) => $e->leitor->notify(
            new DevolucaoAmanha($e),
        ));
})->dailyAt('09:00')->name('avisos-de-devolucao');
```

## Um canal que o Laravel não tem

O WhatsApp da Casa Amarela já existia: é o `EnviadorDeAviso` do capítulo
@cap:service-container, com o provedor atrás de uma interface. Um canal
próprio é uma classe com um método `send`:

```php title="app/Notifications/Canais/CanalWhatsApp.php" numbered
final class CanalWhatsApp
{
    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function send(Leitor $leitor, Notification $aviso): void
    {
        $this->avisos->enviar($leitor, $aviso->toWhatsApp($leitor));
    }
}
```

O `via` devolve o nome da classe, e o Laravel a constrói pelo contêiner —
com o `EnviadorDeAviso` que o `AvisoServiceProvider` já registra. Nenhuma
linha do enviador mudou: ele ganhou mais um cliente.

## Um job por canal

A notificação implementa `ShouldQueue`, e isso faz mais do que parece.
Para a Dona Marlene, com e-mail, WhatsApp e histórico, o `notify()` não
cria **um** job: cria **três**, um por canal.

É a regra do capítulo @cap:events-jobs-e-filas — o job é a menor unidade
que faz sentido repetir — aplicada sem você escrever nada. Se o provedor de
WhatsApp cair, só o job do WhatsApp volta para a fila. O e-mail, que já
saiu, não sai de novo. A Dona Iolanda, das mil e quatrocentas mensagens,
agradeceria.

O `afterCommit()` no construtor é o mesmo cuidado dos eventos daquele
capítulo: se a notificação for disparada dentro de uma transação, ela só
entra na fila depois do `commit`. Um aviso de "reserva disponível" não pode
sair para uma reserva que o `rollback` desfez.

:::key
Notificação na fila vira um job por canal. Escreva cada `toX` como se ele
pudesse rodar sozinho, horas depois, e mais de uma vez: busque o que
precisar, confira se o aviso ainda faz sentido, e não dependa do que outro
canal fez.
:::

## Em português

Com o `APP_NAME` certo, o e-mail ainda sai metade em inglês. A saudação é
nossa, mas o molde padrão do Laravel traz três frases próprias: a
despedida, o rodapé e a instrução para quem não consegue clicar no botão.

Elas passam pela função de tradução, e o `APP_LOCALE=pt_BR` manda procurar
em `lang/pt_BR.json`:

```json title="lang/pt_BR.json"
{
    "Regards,": "Até logo,",
    "All rights reserved.": "Todos os direitos reservados.",
    "If you're having trouble clicking ...": "Se o botão ..."
}
```

A chave é o texto original **exato**. As duas primeiras são curtas. A
terceira — abreviada acima — é a frase inteira do botão, com uma quebra de
linha `\n` no meio, aspas escapadas e o marcador `:actionText`, que o
Laravel troca pelo rótulo do botão nas duas línguas. Copie-a do molde, em
`vendor/laravel/framework/src/Illuminate/Notifications/resources/views/email.blade.php`,
em vez de digitar: uma vírgula a menos na chave, e a frase continua em
inglês, sem erro nenhum.

As mensagens de validação do capítulo @cap:upload-de-arquivos, *"The capa
field has invalid image dimensions"*, têm a mesma causa e o mesmo remédio,
em `lang/pt_BR/validation.php`. Pacotes da comunidade trazem as duas
traduções prontas; vale conferi-las antes do primeiro e-mail, e não depois
da primeira Dona Marlene.

## Chegar à caixa de entrada

O e-mail com o nome certo e em português ainda pode cair no spam. Os
provedores de e-mail decidem com base em quem diz ter mandado, e conferem
isso no DNS do domínio:

| Registro | O que diz ao provedor |
|---|---|
| SPF | quais servidores podem mandar e-mail por `casaamarela.org.br` |
| DKIM | uma assinatura que prova que a mensagem não foi alterada |
| DMARC | o que fazer com o e-mail que falha nos dois anteriores |

Tabela: Os três registros vêm prontos do provedor de envio; alguém com
acesso ao DNS do domínio precisa colá-los.

Na Casa Amarela, o acesso ao DNS estava no papel dobrado do Nonato. Levou
uma semana para achar o login do registro do domínio, e dez minutos para
colar os três registros.

E uma regra de convivência: aviso de prazo é mensagem de **serviço**, e o
leitor pode desligá-la no aplicativo — a coluna `aceita_whatsapp` e uma
irmã para o e-mail. Mensagem de **divulgação** — o bazar de livros, a
oficina de sábado — só vai para quem pediu para receber. Essa diferença
não é gentileza: é a LGPD.

## O documento, como Mailable

O termo de doação do capítulo @cap:upload-de-arquivos precisa voltar
assinado para o doador. Isso é documento, e vai como Mailable:

```text
$ php artisan make:mail TermoDeDoacaoAssinado --markdown=mail.termo
```

```php title="app/Mail/TermoDeDoacaoAssinado.php" numbered
final class TermoDeDoacaoAssinado extends Mailable implements
    ShouldQueue
{
    use Queueable, SerializesModels;

    public function __construct(public readonly Doacao $doacao) {}

    public function envelope(): Envelope
    {
        return new Envelope(subject: 'Seu termo de doação');
    }

    public function content(): Content
    {
        return new Content(markdown: 'mail.termo');
    }

    public function attachments(): array
    {
        return [
            Attachment::fromStorageDisk('local', $this->doacao->termo)
                ->as('termo-de-doacao.pdf')
                ->withMime('application/pdf'),
        ];
    }
}
```

```php
Mail::to($doacao->doador_email)
    ->send(new TermoDeDoacaoAssinado($doacao));
```

O `ShouldQueue` na classe faz o `send` ir para a fila. O anexo sai do disco
privado — o mesmo de onde o `TermoDeDoacaoController` o serve — sem passar
por nenhuma pasta pública.

## Testar sem mandar

```php title="tests/Feature/AvisoDeDevolucaoTest.php" numbered
test('avisa por e-mail e WhatsApp quem aceitou os dois', function () {
    Notification::fake();
    $emprestimo = Emprestimo::factory()
        ->venceAmanha()
        ->for(Leitor::factory()->comEmail()->aceitaWhatsApp())
        ->create();

    $this->artisan('schedule:test', [
        '--name' => 'avisos-de-devolucao',
    ]);

    Notification::assertSentTo(
        $emprestimo->leitor,
        DevolucaoAmanha::class,
        fn ($aviso, array $canais) => $canais === [
            'mail', CanalWhatsApp::class, 'database',
        ],
    );
});

test('e-mail em português, assinado pela Casa Amarela', function () {
    config(['app.name' => 'Biblioteca Casa Amarela']);
    app()->setLocale('pt_BR');
    $emprestimo = Emprestimo::factory()->venceAmanha()->create();

    $html = (string) (new DevolucaoAmanha($emprestimo))
        ->toMail($emprestimo->leitor)
        ->render();

    expect($html)
        ->toContain('Biblioteca Casa Amarela')
        ->toContain('Até logo')
        ->not->toContain('Laravel')
        ->not->toContain('Regards');
});
```

`Notification::fake()` intercepta o `notify()`: nada vai para a fila,
nenhum canal é chamado, e o teste pergunta depois o que **teria** sido
enviado, a quem e por onde. O segundo teste desenha o e-mail de verdade e
confere o texto — é o teste que teria poupado a Dona Marlene de uma ida ao
balcão.

`Mail::fake()` faz o mesmo para Mailables, com `Mail::assertQueued`.

:::note Na sua carreira
E-mail é o único pedaço do sistema que vai parar na casa das pessoas, sem
que elas tenham aberto nada. Um erro na tela, o leitor fecha. Um erro no
e-mail, ele imprime e leva ao balcão.

Antes do primeiro envio em produção, mande o e-mail para você mesmo, a
partir do servidor de produção, e leia inteiro no celular — remetente,
assunto, cabeçalho, rodapé, o botão, e o texto em letra pequena embaixo
dele. São cinco minutos, e é a única revisão que olha o que o leitor vai
olhar.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/
    Mail/TermoDeDoacaoAssinado.php   # documento, com anexo privado
    Notifications/
      DevolucaoAmanha.php            # mail, WhatsApp, database
      Canais/CanalWhatsApp.php       # usa o EnviadorDeAviso
    Models/Leitor.php                # Notifiable
  lang/pt_BR.json                    # o molde do e-mail em português
  resources/views/mail/termo.blade.php
:::

:::summary
- Mailable é documento; notificação é fato que chega a uma pessoa por
  quantos canais ela tiver.
- `APP_NAME`, `MAIL_FROM_ADDRESS` e `MAIL_FROM_NAME` assinam o e-mail.
  Os valores de fábrica dizem "Laravel" e `hello@example.com`.
- Na máquina local, `MAIL_MAILER=log`. Nunca o `.env` de produção.
- `via()` escolhe os canais por pessoa; `toMail`, `toArray` e um `toX` por
  canal próprio dizem o que mandar.
- Canal próprio é uma classe com `send`, construída pelo contêiner.
- Notificação na fila vira um job por canal; `afterCommit()` espera a
  transação.
- O molde padrão traduz por `lang/pt_BR.json`, com a chave exata.
- SPF, DKIM e DMARC no DNS; mensagem de serviço pode ser desligada,
  divulgação só com consentimento.
- `Notification::fake()` e `Mail::fake()` testam sem mandar.
:::

:::checkpoint
Você escolhe entre Mailable e notificação, configura remetente e idioma
antes do primeiro envio, manda o mesmo aviso por vários canais com uma
classe, escreve um canal próprio sobre um serviço que já existia, põe cada
canal na fila sem repetir os outros, e testa o que seria enviado sem
enviar nada.
:::

:::exercise level=1
Mailable ou notificação?

1. "Sua reserva de *Capitães da Areia* está disponível até sexta."
2. O recibo mensal de doações, em PDF, para o contador da associação.
3. "Sua multa de R$ 4,80 foi perdoada."
4. A declaração de nada consta que o estudante pediu pelo aplicativo.

:::answer
1. Notificação. É um fato sobre o leitor, e ele quer saber pelo canal que
   usa.
2. Mailable. É documento, com anexo, para um endereço — o contador nem é
   um leitor.
3. Notificação — é a `MultaPerdoada` do último pedido da Vera, no
   capítulo @cap:git-ci-e-deploy.
4. Mailable. O estudante vai imprimir ou encaminhar; o que importa é o
   documento, não o aviso.
:::

:::exercise level=2
Escreva a notificação `ReservaDisponivel`, com e-mail e histórico, e um
`via` que **não** manda nada se a reserva tiver sido cancelada entre o
disparo e a execução na fila.

:::answer
```php
final class ReservaDisponivel extends Notification implements
    ShouldQueue
{
    use Queueable;

    public function __construct(public readonly Reserva $reserva)
    {
        $this->afterCommit();
    }

    public function via(Leitor $leitor): array
    {
        if ($this->reserva->fresh()?->cancelada()) {
            return [];
        }
        return $leitor->email !== null
            ? ['mail', 'database']
            : ['database'];
    }

    public function toMail(Leitor $leitor): MailMessage
    {
        return (new MailMessage)
            ->subject('Sua reserva está disponível')
            ->line(sprintf(
                '"%s" está separado para você até %s.',
                $this->reserva->livro->titulo,
                $this->reserva->expira_em->format('d/m'),
            ));
    }

    public function toArray(Leitor $leitor): array
    {
        return ['reserva_id' => $this->reserva->id];
    }
}
```

`via` devolvendo `[]` faz a notificação não sair por canal nenhum. O
`fresh()` busca a reserva de novo no banco: o objeto que veio na fila é
uma fotografia do momento do disparo.
:::

:::exercise level=3
Um mês depois, a Márcia recebe a fatura do provedor de e-mail: 9.000
envios, para 1.200 leitores ativos. O agendamento roda uma vez por dia.
Liste três causas possíveis, em ordem de investigação, e o que você
consultaria para confirmar cada uma.

:::answer
1. **O agendamento roda em mais de um servidor.** Se a aplicação ganhou
   um segundo servidor e os dois têm o agendador ligado, cada aviso sai
   duas vezes. Confirme no log: dois "avisos-de-devolucao" no mesmo
   minuto, de máquinas diferentes. Conserto: `->onOneServer()` no
   agendamento.
2. **Um canal falhando e retentando o e-mail junto.** Não deveria — são
   jobs separados —, mas uma notificação escrita como job único que chama
   os três canais teria esse efeito. Confirme em `failed_jobs` e nas
   retentativas do job de WhatsApp.
3. **A consulta pega mais gente do que devia.** Um `whereDate` com fuso
   errado — o capítulo @cap:datas-e-horarios — pode incluir os que vencem hoje
   e amanhã. Confirme contando, para um dia, quantos empréstimos a
   consulta devolve e quantos vencem de fato no dia seguinte.

Nove mil para mil e duzentos leitores em trinta dias são trezentos por
dia — exatamente o número de empréstimos que vencem por dia. Antes das
três hipóteses, vale a conta mais simples: talvez não haja defeito
nenhum, e a fatura só seja a primeira.
:::
