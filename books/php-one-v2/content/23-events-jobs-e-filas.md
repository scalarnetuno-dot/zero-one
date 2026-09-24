---
title: "Events, jobs e filas"
number: 23
slug: events-jobs-e-filas
part: p6
kicker: "O aviso de devolução foi enviado 1.400 vezes para a mesma pessoa. O job não era idempotente, e o worker reiniciou no meio."
goal: >-
  Tirar da requisição o trabalho que não precisa acontecer antes da
  resposta, desacoplar com eventos sem esconder o fluxo, rodar filas com
  worker que reinicia no deploy, e escrever jobs que podem falhar, voltar e
  rodar de novo sem repetir o efeito.
---

:::story Mil e quatrocentas
O telefone da Casa Amarela tocou às 7h10 de um sábado. A Vera não estava; o
número desviava para o celular da Márcia, que não sabia disso até aquele
dia.

— Aqui é o filho da Dona Iolanda. O celular da minha mãe não para de
tocar. É uma mensagem de vocês. Ela recebeu — ele fez uma pausa, contando —
mil e trezentas. Mil e trezentas e poucas. Agora mesmo chegou outra.

Márcia ligou para Dedé. Dedé abriu o notebook na cozinha, de pijama, e
entrou no servidor.

```text
$ php artisan queue:failed
No failed jobs found.

$ tail -f storage/logs/laravel.log | grep AvisarDevolucao
... processando AvisarDevolucaoProxima
... processando AvisarDevolucaoProxima
... processando AvisarDevolucaoProxima
```

— Não falhou nenhum — disse ele ao telefone. — Esse é o problema. Está
dando certo. Toda vez.

— Então para!

Ele parou o worker. As mensagens pararam. A contagem final, no painel do
provedor, foi 1.412.

Na segunda, a investigação levou vinte minutos. O job enviava um aviso para
cada empréstimo que vencia no dia seguinte — trezentos e poucos — e só
marcava o trabalho como concluído no fim, depois do último envio. Na sexta
à noite, o provedor ficou lento, o job passou do tempo limite no envio de
número 212, e a fila fez o que foi configurada para fazer: tentou de novo.
Do começo.

— Quantas tentativas estavam configuradas? — perguntou Márcia.

Dedé abriu o arquivo.

— Nenhuma. Sem limite.
:::

:::art caption="Nenhum job falhou. Esse era o problema."
src="nenhum-job-falhou-esse-era-o-problema.png"
Charge editorial minimalista em fundo branco, composição dividida ao meio.
À esquerda, uma senhora idosa em casa, de roupão, segura com as duas mãos
um celular que vibra sem parar, com um balão de notificação empilhado sobre
outro até o teto e o número "1.412". À direita, um desenvolvedor de
pijama, na mesa da cozinha com uma caneca de café, olha o notebook onde
uma seta circular fechada gira em volta da palavra "tentar de novo". No
canto do notebook, um visto verde e a frase "No failed jobs". Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## O que não precisa acontecer antes da resposta

O `EmprestimoService` do capítulo @cap:services envia o aviso ao leitor
depois de confirmar a transação. O envio passa pelo provedor de mensagens,
que responde em trezentos milissegundos num dia bom e em oito segundos num
dia ruim.

Nos dias ruins, a Vera fica oito segundos olhando para a tela, com o leitor
na frente dela, esperando uma confirmação que **já aconteceu** — o
empréstimo está gravado desde o primeiro milissegundo. O que falta é uma
mensagem de WhatsApp que o leitor nem precisa ter recebido para ir embora
com o livro.

A pergunta que separa o trabalho: **quem está esperando por isto precisa
do resultado para continuar?**

| Trabalho | Quem espera precisa? | Onde |
|---|---|---|
| gravar o empréstimo | sim, é a operação | na requisição |
| travar o exemplar | sim, senão é outro empréstimo | na requisição |
| avisar o leitor | não | na fila |
| atualizar "mais emprestados" | não | na fila |
| gerar o comprovante em PDF | não, chega depois | na fila |

Tabela: A fila existe porque esperar custa caro — o tempo de quem está no
balcão, e o risco de uma falha do provedor derrubar uma operação que já
tinha dado certo.

## Event e listener: desacoplar sem esconder

Antes da fila, uma separação. O service, hoje, sabe que depois de um
empréstimo alguém precisa ser avisado. Amanhã, precisa também atualizar um
contador. Depois, registrar para a prestação de contas do edital. Cada
necessidade nova é uma linha a mais no `realizar()`, e cada linha é uma
dependência a mais no construtor.

A alternativa é o service **anunciar o que aconteceu** e deixar que os
interessados reajam:

```php title="app/Emprestimos/Eventos/EmprestimoRealizado.php" numbered
final class EmprestimoRealizado implements ShouldDispatchAfterCommit
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public readonly Emprestimo $emprestimo,
    ) {}
}
```

```php title="app/Emprestimos/EmprestimoService.php" numbered
$emprestimo = DB::transaction(function () use (/* ... */) {
    // ... as conferências e a gravação ...

    EmprestimoRealizado::dispatch($emprestimo);

    return $emprestimo;
});
```

E quem reage:

```php title="app/Listeners/EnviarComprovanteDeEmprestimo.php" numbered
final class EnviarComprovanteDeEmprestimo implements ShouldQueue
{
    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function handle(EmprestimoRealizado $evento): void
    {
        $e = $evento->emprestimo->load('leitor', 'exemplar.livro');

        $this->avisos->enviar(
            $e->leitor,
            sprintf(
                'Você levou "%s". Devolva até %s.',
                $e->exemplar->livro->titulo,
                $e->devolver_ate->format('d/m'),
            ),
        );
    }
}
```

O Laravel liga um ao outro pelo tipo do parâmetro do `handle` — quem recebe
`EmprestimoRealizado` escuta `EmprestimoRealizado`. O
`ShouldQueue` no listener manda a execução para a fila, e o service não
espera por ela.

:::pitfall
O evento é disparado **dentro** da transação. Sem o
`ShouldDispatchAfterCommit`, o listener vai para a fila na hora — e o worker
pode pegá-lo **antes** de o `COMMIT` acontecer. Ele procura o empréstimo
pelo id e não encontra, porque para o resto do banco a linha ainda não
existe.

O defeito é intermitente, depende da velocidade do worker, e aparece como
`ModelNotFoundException` num job que "às vezes falha". A interface
`ShouldDispatchAfterCommit` segura o disparo até a transação confirmar — e
o descarta se ela for desfeita, o que evita avisar sobre um empréstimo que
não aconteceu.
:::

O ganho do evento é que o service não conhece mais o aviso. O custo é que
quem lê o `realizar()` não vê mais, ali, tudo que acontece depois de um
empréstimo. A última seção do capítulo volta a esse custo.

## Job: a unidade de trabalho que pode falhar e voltar

Nem todo trabalho de fila é reação a um evento. O aviso de "seu livro vence
amanhã" não é disparado por nada que aconteceu — é disparado pelo
calendário. Para isso existe o **job**, uma classe que representa um
trabalho a ser feito:

```text
$ php artisan make:job AvisarDevolucaoProxima
```

```php title="app/Jobs/AvisarDevolucaoProxima.php" numbered
final class AvisarDevolucaoProxima implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public readonly int $emprestimoId,
    ) {}

    public function handle(EnviadorDeAviso $avisos): void
    {
        $e = Emprestimo::with('leitor', 'exemplar.livro')
            ->find($this->emprestimoId);

        if ($e === null || $e->devolvido()) {
            return;
        }

        $avisos->enviar($e->leitor, sprintf(
            '"%s" vence amanhã. Renove pelo aplicativo.',
            $e->exemplar->livro->titulo,
        ));
    }
}
```

E o que dispara os jobs é um comando agendado, como o `biblioteca:multas`
do capítulo @cap:configuracao-ambiente-e-artisan:

```php title="routes/console.php" numbered
Schedule::call(function () {
    Emprestimo::emAberto()
        ->whereDate('devolver_ate', today()->addDay())
        ->pluck('id')
        ->each(fn ($id) => AvisarDevolucaoProxima::dispatch($id));
})->dailyAt('09:00')->name('avisos-de-devolucao');
```

Compare com o job da história. Ele era **um** job que percorria
trezentos empréstimos. Este é **um job por empréstimo**. A diferença parece
de estilo e é o que teria salvado a Dona Iolanda: quando o envio de número
212 falha, só o job 212 tenta de novo. Os 211 anteriores já terminaram e
não voltam.

:::key
Um job deve ser a **menor unidade de trabalho que faz sentido repetir**.

Um job que faz trezentas coisas, ao ser repetido, refaz as trezentas. Um
job que faz uma, ao ser repetido, refaz uma.
:::

Repare também no que o job recebe: o **id**, não o model. O `$e` é buscado
dentro do `handle`, no momento em que o job roda — que pode ser segundos ou
horas depois do disparo. Se o leitor devolveu o livro nesse meio tempo, o
job descobre e não envia nada.

## Driver de fila: `sync`, `database`, `redis`

A fila precisa morar em algum lugar entre o disparo e a execução. O
`.env` escolhe onde:

```text
QUEUE_CONNECTION=database
```

**`sync`** não é fila: executa o job na hora, dentro da requisição. É o
padrão em desenvolvimento e em teste, e esconde todo problema que só
existe quando o job roda em outro processo.

**`database`** guarda os jobs numa tabela `jobs`. Não exige nada além do
MySQL que o projeto já tem. Aguenta com folga o volume de uma biblioteca de
bairro — algumas centenas de jobs por dia.

**`redis`** guarda os jobs num servidor Redis, em memória. É mais rápido e
aguenta volumes muito maiores, e é mais uma peça para instalar, monitorar e
manter.

A Casa Amarela usa `database`. A régua é a do caderno da Tainá, lá do
capítulo @cap:o-que-vamos-construir: perguntar o tamanho antes de escolher
a ferramenta.

## Worker, supervisor e o processo que precisa reiniciar

Alguém precisa tirar os jobs da fila e executá-los. É o **worker**:

```text
$ php artisan queue:work --tries=3 --max-time=3600
```

Ele é um processo PHP que não termina: pega um job, executa, pega o
próximo, para sempre. E isso muda uma coisa que o livro inteiro assumiu até
aqui.

Na requisição web, o PHP carrega o código, atende e morre. Alterar um
arquivo e recarregar a página basta. O worker **carregou o código quando
começou** e continua com aquela versão na memória. Um deploy que altera o
`EnviadorDeAviso` não muda nada no worker que está rodando — ele continua
enviando com o código de ontem, até alguém reiniciá-lo.

```text
$ php artisan queue:restart
```

Esse comando não reinicia nada diretamente. Ele grava um sinal no cache, e
cada worker, ao terminar o job atual, confere o sinal e se encerra
sozinho. Para que ele **volte**, é preciso um supervisor — um programa do
sistema operacional cuja função é manter processos vivos:

```ini title="/etc/supervisor/conf.d/casa-amarela.conf" numbered
[program:casa-amarela-worker]
directory=/var/www/casa-amarela
command=php artisan queue:work --tries=3 --max-time=3600
autostart=true
autorestart=true
user=www-data
numprocs=1
stopwaitsecs=120
```

O `--max-time=3600` faz o worker se encerrar sozinho a cada hora, e o
supervisor o sobe de novo. Isso limpa a memória acumulada e garante que,
mesmo que alguém esqueça o `queue:restart`, o código novo entra em no
máximo uma hora.

:::warning
Deploy sem `queue:restart` é o defeito mais comum de quem começa a usar
fila. O site mostra a versão nova, os testes passaram, e os avisos
continuam saindo com o texto antigo — ou falhando, porque o código velho
procura uma coluna que a migration de hoje renomeou.

O capítulo @cap:git-ci-e-deploy põe o `queue:restart` no roteiro de deploy,
numa ordem que não é por acaso.
:::

## Retentativa, `backoff` e `failed_jobs`

Um job que lança exceção volta para a fila e é tentado de novo. Quantas
vezes, e com que intervalo, é uma decisão do job:

```php title="app/Jobs/AvisarDevolucaoProxima.php" numbered
public int $tries = 3;

public int $timeout = 30;

public function backoff(): array
{
    return [60, 300];
}

public function failed(Throwable $e): void
{
    Log::warning('aviso-de-devolucao-falhou', [
        'emprestimo' => $this->emprestimoId,
        'erro' => $e->getMessage(),
    ]);
}
```

Três tentativas. A segunda um minuto depois da primeira, a terceira cinco
minutos depois da segunda — dar tempo ao provedor de se recuperar, em vez
de insistir no mesmo segundo. O `timeout` mata a tentativa que passa de
trinta segundos.

Depois da terceira falha, o job vai para a tabela `failed_jobs`, com a
exceção inteira gravada, e o `failed()` é chamado. Ele não retenta: é o
lugar de registrar, avisar alguém, ou marcar no banco que aquele leitor não
foi avisado.

```text
$ php artisan queue:failed
+----+------------------------+----------------------+
| ID | Job                    | Falhou em            |
+----+------------------------+----------------------+
| 41 | AvisarDevolucaoProxima | 2026-03-02 09:00:44  |
+----+------------------------+----------------------+

$ php artisan queue:retry 41
```

O `queue:retry` devolve o job à fila, depois de o problema ter sido
corrigido. É o que torna a falha de um job uma coisa tratável, e não uma
mensagem perdida.

:::pitfall
O job da história não tinha `$tries`. Sem ele, o worker usa o valor da
linha de comando — e se a linha de comando também não tiver, a
retentativa é **ilimitada**. Um job que sempre falha no meio roda para
sempre, e se o que ele faz antes de falhar é enviar mensagem, a mensagem é
enviada para sempre.
:::

## Job precisa ser idempotente

O `$tries = 3` limitaria o estrago a três mensagens por pessoa, e três
mensagens iguais ainda são duas a mais. O defeito de fundo não é o número
de tentativas. É que **repetir o job repete o efeito**.

:::term Idempotente
Uma operação é idempotente quando executá-la duas vezes produz o mesmo
resultado que executá-la uma. O `DELETE` do capítulo
@cap:o-que-e-uma-api-rest é; enviar uma mensagem, por natureza, não é.
:::

A fila **não garante** que um job rode uma vez só. Ela garante que ele roda
**pelo menos** uma vez. Um worker pode morrer depois de enviar a mensagem e
antes de avisar a fila que terminou — e a fila, sem o aviso, entrega o job
de novo. Nenhuma configuração elimina isso. Quem precisa lidar com a
repetição é o job.

A técnica é registrar o efeito **de forma que a segunda tentativa
descubra** que ele já aconteceu:

```php title="database/migrations/..._create_avisos_enviados.php" numbered
Schema::create('avisos_enviados', function (Blueprint $t) {
    $t->id();
    $t->foreignId('emprestimo_id')->constrained();
    $t->string('tipo', 40);
    $t->date('referente_a');
    $t->timestamps();

    $t->unique(['emprestimo_id', 'tipo', 'referente_a']);
});
```

```php title="app/Jobs/AvisarDevolucaoProxima.php" numbered
public function handle(EnviadorDeAviso $avisos): void
{
    $e = Emprestimo::with('leitor', 'exemplar.livro')
        ->find($this->emprestimoId);

    if ($e === null || $e->devolvido()) {
        return;
    }

    $registro = AvisoEnviado::firstOrCreate([
        'emprestimo_id' => $e->id,
        'tipo' => 'devolucao-proxima',
        'referente_a' => $e->devolver_ate->toDateString(),
    ]);

    if (!$registro->wasRecentlyCreated) {
        return;
    }

    $avisos->enviar($e->leitor, /* ... */);
}
```

O `unique` no banco é a garantia; o `firstOrCreate` é a pergunta. Se o
registro acabou de ser criado, este é o primeiro envio. Se já existia, uma
tentativa anterior chegou até aqui, e esta para.

Resta um buraco pequeno: se o worker morrer **entre** criar o registro e
enviar, a mensagem não sai, e a tentativa seguinte acha o registro e
desiste. É a troca consciente entre dois defeitos — nenhuma mensagem, raras
vezes, ou mensagens repetidas. Para um lembrete de devolução, a primeira
falha é tolerável. Para uma cobrança, talvez não; e aí o registro ganha um
estado — `enviando`, `enviado` — e o `failed()` resolve os que ficaram no
meio.

:::key
A pergunta que todo job precisa responder antes de ir para produção: **o
que acontece se ele rodar duas vezes?**

Se a resposta for "nada de mais", ele está pronto. Se for "o leitor recebe
duas mensagens" ou "a multa é cobrada duas vezes", ele não está.
:::

## Quando o evento vira espaguete invisível

Um evento com um listener é claro. O problema começa quando os listeners
disparam eventos:

```text
EmprestimoRealizado
  → AtualizarContadorDoLivro
      → dispara LivroFicouPopular
          → RecalcularDestaques
              → dispara DestaquesMudaram
                  → LimparCacheDaHome
  → EnviarComprovante
  → RegistrarParaPrestacaoDeContas
```

Nenhum arquivo mostra essa árvore. Para saber o que acontece depois de um
empréstimo, é preciso procurar os listeners de `EmprestimoRealizado`, depois
os listeners de cada evento que eles disparam, e assim por diante. Um
defeito no `LimparCacheDaHome` aparece para quem investiga como "o
empréstimo às vezes demora", três níveis de distância da causa.

Três regras mantêm os eventos legíveis:

**Listener não dispara evento.** Ele reage e termina. Se a reação
precisa de uma segunda etapa, a segunda etapa é um job, chamado
explicitamente pelo listener.

**Evento é fato do domínio, no passado.** `EmprestimoRealizado`,
`ExemplarDevolvido`. Não `EnviarEmail` — isso é uma ordem, e ordem é job.

**A lista de quem escuta cabe numa consulta.** O comando
`php artisan event:list` mostra cada evento e os seus listeners. Se a saída
dele não couber numa tela, é hora de conversar.

:::story O v2
Para saber como o Sistema de 2009 mandava o aviso de devolução, Tainá
procurou o `cron` do servidor antigo. Havia uma linha só, e ela chamava
`php /home/casaamarela/public_html/aviso.php`.

O `aviso.php` tinha doze linhas. A décima incluía um arquivo.

```php
include 'funcoes2_NOVO_final_v2.php';
```

Tainá ficou olhando a tela.

— Dedé.

— Hm.

— Tem um `v2`.

Ele rolou a cadeira até a mesa dela e leu. Depois abriu a pasta. Estavam
lá, lado a lado: `funcoes.php`, `funcoes2.php`,
`funcoes2_NOVO_final.php` e `funcoes2_NOVO_final_v2.php`. O último tinha
sido alterado em março de 2016 e tinha uma função só,
`manda_aviso_email()`, que abria uma conexão SMTP com um servidor que não
existia mais desde 2019.

— Então desde 2019 ninguém recebe aviso de devolução — disse Tainá.

— Desde 2019.

— E ninguém reclamou.

— A Vera liga — disse Dedé. — Ela tem uma lista no caderno dela. Liga pra
todo mundo na véspera.

— Toda véspera?

— Faz cinco anos.
:::

:::milestone
O trabalho que não cabe na requisição saiu dela. O empréstimo responde sem
esperar o provedor de mensagens; o aviso sai por uma fila com worker
supervisionado e reiniciado no deploy; cada job tenta três vezes, espera
entre as tentativas, termina em `failed_jobs` quando não dá — e pode rodar
duas vezes sem mandar duas mensagens.

A Vera pode parar de ligar na véspera.
:::

:::summary
- Vai para a fila o que quem está esperando não precisa para continuar.
- Evento anuncia um fato; listener reage; o service não conhece quem
  reage.
- `ShouldDispatchAfterCommit` segura o evento até a transação confirmar.
- Job é a menor unidade de trabalho que faz sentido repetir: um por
  empréstimo, não um para todos.
- Job recebe o id e busca o registro na hora de rodar.
- `sync` não é fila; `database` basta para volumes pequenos; `redis`, para
  grandes.
- O worker guarda o código na memória: deploy sem `queue:restart` roda
  código velho. Supervisor o mantém vivo.
- `$tries`, `backoff` e `timeout` são decisões do job; sem `$tries`, a
  retentativa pode ser infinita.
- A fila entrega pelo menos uma vez; o job precisa ser idempotente, com o
  efeito registrado sob `unique`.
- Listener não dispara evento; `event:list` precisa caber numa tela.
:::

:::checkpoint
O comprovante de empréstimo e o aviso de véspera saem pela fila, depois do
`COMMIT`, com um job por empréstimo; o worker roda sob supervisor e
reinicia no deploy; e você consegue explicar o que acontece com um job que
falha na terceira tentativa — e por que ele pode rodar duas vezes sem que a
Dona Iolanda perceba.
:::

:::exercise level=1
Diga se cada trabalho deve acontecer na requisição ou na fila, e por quê:

1. Conferir se o leitor tem multa acima de cinco reais.
2. Enviar o aviso de que uma reserva ficou disponível.
3. Gravar a devolução e liberar o exemplar.
4. Recalcular a lista dos mais emprestados do mês.
5. Gerar o PDF do relatório mensal da prestação de contas.

:::answer
1. Requisição. É condição para a operação acontecer, e precisa estar dentro
   da transação.
2. Fila. O leitor que devolveu o livro não precisa esperar o aviso a outra
   pessoa sair.
3. Requisição. É a operação.
4. Fila, disparada pelo evento de empréstimo ou de devolução — ou nem isso:
   o capítulo @cap:cache-logs-e-medicao discute se ela precisa ser
   recalculada a cada evento.
5. Fila. Pode levar minutos. A requisição responde "o relatório está sendo
   gerado", e um aviso ou um link chega quando ficar pronto.
:::

:::exercise level=2
Escreva o evento `ExemplarDevolvido` e o listener que avisa o primeiro
leitor da fila de reserva daquele livro. O listener deve ir para a fila,
ter três tentativas, e ser idempotente.

:::answer
```php title="app/Emprestimos/Eventos/ExemplarDevolvido.php" numbered
final class ExemplarDevolvido implements ShouldDispatchAfterCommit
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public readonly Exemplar $exemplar,
    ) {}
}
```

```php title="app/Listeners/AvisarReservaDisponivel.php" numbered
final class AvisarReservaDisponivel implements ShouldQueue
{
    public int $tries = 3;

    public function __construct(
        private readonly EnviadorDeAviso $avisos,
    ) {}

    public function handle(ExemplarDevolvido $evento): void
    {
        $reserva = Reserva::ativas()
            ->where('livro_id', $evento->exemplar->livro_id)
            ->oldest()
            ->first();

        if ($reserva === null) {
            return;
        }

        $marcada = Reserva::whereKey($reserva->id)
            ->whereNull('avisada_em')
            ->update(['avisada_em' => now()]);

        if ($marcada === 0) {
            return;
        }

        $this->avisos->enviar(
            $reserva->leitor,
            'O livro que você reservou está disponível.',
        );
    }
}
```

A idempotência vem do `update` com `whereNull('avisada_em')`: ele só marca
se ninguém marcou, e devolve quantas linhas mudou. Duas execuções
simultâneas não conseguem as duas mudar a mesma linha — o banco garante.

Repare que a reserva é buscada pelo **livro**, não pelo exemplar, pelo
mesmo motivo do `renovar()` no capítulo @cap:services.
:::

:::exercise level=3
Depois do incidente da Dona Iolanda, alguém propôs: "vamos tirar a fila e
voltar a enviar os avisos dentro do comando agendado, em sequência, que
assim não repete".

Responda à proposta: o que ela resolve de verdade, o que ela piora, e o que
você mostraria para defender a fila corrigida.

:::answer
**O que ela resolve.** A repetição por retentativa, sim: sem fila, não há
quem tente de novo. E é mais simples de entender — um laço, do começo ao
fim.

**O que ela piora.**

Uma falha no envio de número 212 para o comando inteiro. Os leitores de 213
a 300 não recebem nada, e ninguém fica sabendo até alguém reclamar — não
há `failed_jobs`, não há `queue:retry`.

O comando leva o tempo da soma de todos os envios. Com o provedor lento,
são trezentos vezes oito segundos: quarenta minutos. Se o agendador rodar
o comando de novo antes de o primeiro terminar, **ele repete** — que é o
defeito que a proposta queria evitar, voltando por outro caminho. Há
proteção para isso (`withoutOverlapping`), e alguém precisa lembrar de pôr.

E a repetição não era causada pela fila. Era causada por um job que fazia
trezentas coisas e não registrava o que já tinha feito. O mesmo laço, dentro
do comando, reexecutado por uma pessoa depois de uma falha no meio,
reenvia os 211 primeiros do mesmo jeito.

**O que eu mostraria.** O job novo — um por empréstimo, com `$tries`,
`backoff` e o registro `unique` — e três testes: um que roda o job duas
vezes e confere um envio só; um que simula falha do provedor e confere a
entrada em `failed_jobs`; e um que roda o agendamento com trezentos
empréstimos e confere trezentos jobs na fila. A proposta resolvia o
sintoma; os testes mostram que a causa foi resolvida.
:::
