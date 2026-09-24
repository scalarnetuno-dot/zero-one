---
title: "Queues na prática"
number: 31
slug: queues-na-pratica
part: p8
kicker: "O aviso das nove chegou às três da tarde. Na frente dele, na mesma fila, estavam duzentos mil livros do Seu Juvenal."
goal: >-
  Medir a fila pelo tempo de espera, separar trabalhos em filas com
  prioridade e workers próprios, importar em lote com progresso, encadear
  passos que dependem um do outro, respeitar o ritmo do provedor sem gastar
  tentativas, impedir trabalho em dobro e acertar o par timeout e
  retry_after que causa a maior parte das repetições.
---

:::story O aviso das nove
A escola estadual finalmente mandou a planilha das doações — a mesma de
duzentas mil linhas do volume 1 —, e a Tainá transformou a importação em
jobs: um job para cada mil linhas, duzentos jobs, disparados às 8h50 de uma
segunda-feira.

Às 9h, o agendador disparou os trezentos avisos de "seu livro vence
amanhã". Eles entraram na fila. **Atrás** dos duzentos jobs de importação.

Às 15h10, o Seu Juvenal ligou.

— Chegou agora uma mensagem dizendo que meu livro vence amanhã. A
biblioteca fecha às seis. Eu estou em Guarulhos.

A Tainá abriu o servidor.

```text
$ php artisan queue:monitor database:default
  database:default ........................... [312] OK
```

— Trezentos e doze jobs, e ele diz OK — disse ela.

— Ele diz OK porque o limite padrão é mil — disse o Dedé. — Trezentos
e doze parece pouco. O que ele não diz é que cada job da importação leva
quase dois minutos, que só tem um worker, e que o aviso das nove está no
fim da fila.

— Então o problema é a quantidade de workers?

— O problema é que o aviso e a importação estão na mesma fila. Um é para
agora. O outro é para quando der.
:::

## A métrica é a espera

O capítulo @cap:events-jobs-e-filas pôs a fila de pé: driver `database`,
um worker com supervisor, retentativa, `failed_jobs` e jobs idempotentes.
Tudo isso continua certo. O que ele não precisou responder é o que
acontece quando trabalhos com **urgências diferentes** dividem o mesmo
worker.

A primeira coisa a mudar é o que se mede. O tamanho da fila engana:
trezentos jobs de um segundo são cinco minutos; trezentos de dois minutos
são dez horas. O que o leitor sente é **quanto tempo o job mais antigo está
esperando**:

```sql
SELECT queue,
       COUNT(*) AS jobs,
       TIMESTAMPDIFF(MINUTE, FROM_UNIXTIME(MIN(available_at)), NOW())
           AS espera_min
FROM jobs
WHERE reserved_at IS NULL
GROUP BY queue;
```

```text
+---------+------+------------+
| queue   | jobs | espera_min |
+---------+------+------------+
| default |  312 |        380 |
+---------+------+------------+
```

Trezentos e oitenta minutos. Essa é a frase que teria acordado alguém às
9h30, e não às 15h10.

O `queue:monitor` também serve, com o limite certo e agendado: quando uma
fila passa do `--max`, ele dispara o evento `QueueBusy`, e quem o escuta
avisa a equipe.

```php title="routes/console.php" numbered
Schedule::command('queue:monitor', [
    'database:avisos,database:default', '--max' => 50,
])->everyFiveMinutes();
```

```php title="app/Providers/AppServiceProvider.php" numbered
Event::listen(function (QueueBusy $evento) {
    Log::warning('fila-cheia', [
        'fila' => $evento->queue,
        'jobs' => $evento->size,
    ]);
});
```

## Uma fila por urgência

Filas têm nome. Um job escolhe a sua ao ser disparado, ou na própria
classe:

```php
ImportarLote::dispatch($linhas)->onQueue('importacao');
```

E a notificação do capítulo @cap:mail-e-notificacoes, que vira um job por
canal, escolhe a fila de cada canal:

```php title="app/Notifications/DevolucaoAmanha.php" numbered
public function viaQueues(): array
{
    return [
        'mail' => 'avisos',
        CanalWhatsApp::class => 'avisos',
        'database' => 'avisos',
    ];
}
```

O worker lê as filas **na ordem em que foram listadas**:

```text
$ php artisan queue:work --queue=avisos,default,importacao
```

A cada job, ele olha primeiro `avisos`; só se estiver vazia, `default`; só
se as duas estiverem vazias, `importacao`. Os avisos das nove passam na
frente dos duzentos lotes, porque o worker nunca pega um lote enquanto
houver aviso esperando.

:::pitfall
A ordem é prioridade estrita. Se `avisos` nunca esvazia — um dia de muito
movimento, um provedor lento —, a `importacao` nunca roda. Para trabalho
que não pode passar fome, dê a ele um worker próprio.
:::

Na Casa Amarela, dois programas no supervisor:

```ini title="/etc/supervisor/conf.d/casa-amarela.conf" numbered
[program:casa-amarela-urgente]
command=php artisan queue:work --queue=avisos,default
    --tries=3 --max-time=3600
numprocs=2

[program:casa-amarela-pesado]
command=php artisan queue:work database-longa
    --queue=importacao,capas --tries=2 --timeout=300
    --max-time=3600
numprocs=1
```

(As linhas de `command` estão quebradas para caber na página; no arquivo,
cada uma é uma linha só. O `database-longa` é explicado mais adiante.)

Dois workers para o que é urgente, um para o que é pesado. O pesado pode
levar a tarde inteira, e o aviso das nove sai às nove.

## Importar em lote, com progresso

Duzentos jobs soltos não respondem a uma pergunta que a Vera fez no
terceiro minuto: **já foi quanto?** Um **lote** — *batch* — agrupa jobs,
acompanha o progresso e chama alguém quando tudo termina.

O lote precisa de uma tabela, criada uma vez:

```text
$ php artisan make:queue-batches-table
$ php artisan migrate
```

E a importação passa a montar o lote com o gerador `lerCsv` do capítulo
@cap:manipulacao-de-arquivos — que veio do projeto antigo para
`app/Importacao/funcoes.php`, carregado pelo `files` do Composer como no
capítulo @cap:como-organizar-um-projeto-php —, agora dentro de uma
`LazyCollection`:

```php title="app/Importacao/ImportarDoacoes.php" numbered
public function __invoke(string $caminho): Batch
{
    $leitura = fn () => yield from lerCsv($caminho);

    $lotes = LazyCollection::make($leitura)
        ->chunk(1000)
        ->map(fn ($linhas) => new ImportarLote(
            $linhas->values()->all(),
        ));

    return Bus::batch($lotes->all())
        ->name('doacoes ' . basename($caminho))
        ->onConnection('database-longa')
        ->onQueue('importacao')
        ->allowFailures()
        ->then(fn (Batch $lote) => Log::info('importacao-ok', [
            'lote' => $lote->id,
        ]))
        ->finally(fn (Batch $lote) => Cache::forget('acervo'))
        ->dispatch();
}
```

A leitura continua uma linha por vez: a `LazyCollection` pede ao gerador
mil linhas, cria um job com elas, e só então pede as próximas mil. Mas
repare no `$lotes->all()`: o `Bus::batch` precisa da lista de jobs, e
cada job carrega as suas mil linhas. No momento do disparo, a planilha
inteira está na memória, dividida em duzentos pedaços — os trinta
megabytes do capítulo @cap:manipulacao-de-arquivos, por alguns segundos.
Para nove megabytes de CSV, é um preço aceitável. Para noventa, o lote
nasce vazio e um job de leitura vai acrescentando os lotes aos poucos,
com `$lote->add([...])`.

**`allowFailures()`** decide o que acontece quando um lote falha. Sem ele,
a primeira falha cancela o resto. Com ele, os outros 199 continuam, e o
lote que falhou vai para `failed_jobs`, onde pode ser corrigido e
retentado. Para uma importação de doações, é o comportamento certo: uma
linha com o ano por extenso não deve impedir as outras 199.999.

**`then`** roda quando todos terminam com sucesso; **`finally`**, quando
todos terminam, com ou sem falha. O `Cache::forget('acervo')` é o cuidado
do capítulo @cap:cache-logs-e-medicao: a página do acervo não pode mostrar
a lista de ontem.

:::pitfall
As closures do `then`, `catch` e `finally` são **guardadas no banco** e
executadas depois, por outro processo. Elas não podem usar `$this`, nem
variáveis que não sejam serializáveis. Passe só valores simples — ids,
textos — e busque o resto dentro da closure.
:::

O job do lote confere, antes de trabalhar, se alguém cancelou o lote:

```php title="app/Jobs/ImportarLote.php" numbered
final class ImportarLote implements ShouldQueue
{
    use Batchable, Queueable;

    public int $timeout = 240;

    public function __construct(public readonly array $linhas) {}

    public function handle(Importador $importador): void
    {
        if ($this->batch()?->cancelled()) {
            return;
        }
        $importador->importar($this->linhas);
    }
}
```

E a Vera ganha a resposta para "já foi quanto?":

```php title="app/Http/Controllers/ImportacaoController.php" numbered
public function show(string $id)
{
    $lote = Bus::findBatch($id) ?? abort(404);

    return [
        'nome' => $lote->name,
        'progresso' => $lote->progress(),
        'pendentes' => $lote->pendingJobs,
        'falhas' => $lote->failedJobs,
        'terminado' => $lote->finished(),
    ];
}
```

```text
{"nome":"doacoes escola-estadual.csv","progresso":37,
 "pendentes":126,"falhas":1,"terminado":false}
```

Um detalhe que aparece no último minuto da importação: o lote que falhou
continua contando como **pendente**. Com 199 lotes bons e 1 com falha, o
progresso para em 99, `pendentes` e `falhas` valem 1, o `finally` já rodou
— e `terminado` só vira `true` quando alguém corrige a linha e retenta o
lote. O painel da Vera deve mostrar isso como "terminou com uma falha", e
não como "quase lá".

## Encadear o que depende

Lote é para trabalhos **independentes**, que podem rodar em qualquer
ordem. Quando um passo precisa do anterior, é **cadeia**:

```php
Bus::chain([
    new PrepararCapa($livro->id, $original),
    new EsquecerCacheDoAcervo(),
])->onQueue('capas')->dispatch();
```

O `EsquecerCacheDoAcervo` só roda se o `PrepararCapa` do capítulo
@cap:upload-de-arquivos terminar bem. Se a capa falhar, o cache não é
apagado à toa — e a cadeia para ali, com o job que falhou em
`failed_jobs`.

## O ritmo do provedor

O provedor de WhatsApp aceita sessenta mensagens por minuto. Trezentos
avisos disparados às nove, com dois workers, saem em quarenta segundos — e
duzentos e quarenta voltam com erro `429`.

O Laravel limita o ritmo com um **limitador nomeado** e um **middleware de
job**:

```php title="app/Providers/AppServiceProvider.php" numbered
RateLimiter::for('whatsapp', fn () => Limit::perMinute(60));
```

```php title="app/Notifications/DevolucaoAmanha.php" numbered
public function middleware(object $leitor, string $canal): array
{
    return $canal === CanalWhatsApp::class
        ? [new RateLimited('whatsapp')]
        : [];
}

public function retryUntil(): DateTime
{
    return now()->addHours(3);
}
```

O middleware roda antes do job. Se o limite do minuto já foi usado, ele
não executa o job: **devolve-o à fila** com um atraso, para tentar de novo
quando o minuto virar. O e-mail e o histórico, que não têm limite, seguem
sem esperar.

O `retryUntil` não é detalhe. Cada vez que o `RateLimited` devolve o job à
fila, o Laravel conta **uma tentativa**. Com `--tries=3`, um aviso que
esperou três minutos pela vez vai para `failed_jobs` sem nunca ter falhado
de verdade. `retryUntil` troca o limite de tentativas por um limite de
tempo: o aviso pode esperar a vez quantas vezes precisar, até três horas
depois do disparo.

:::key
Tentativa é uma contagem de **voltas à fila**, não de erros. Tudo o que
devolve o job de propósito — limite de ritmo, trava, dependência
indisponível — gasta tentativa. Para esses jobs, limite por tempo
(`retryUntil`), não por número.
:::

## Não fazer duas vezes

Três ferramentas para três situações, todas no mesmo espírito do job
idempotente do capítulo @cap:events-jobs-e-filas:

**Um job que não pode estar na fila duas vezes.** O relatório mensal da
associação é pesado, e o botão "gerar" é apertado por impaciência. O
contrato `ShouldBeUnique` impede o segundo disparo enquanto o primeiro não
terminar:

```php title="app/Jobs/GerarRelatorioMensal.php" numbered
final class GerarRelatorioMensal implements
    ShouldQueue,
    ShouldBeUnique
{
    use Queueable;

    public int $uniqueFor = 3600;

    public function __construct(public readonly string $mes) {}

    public function uniqueId(): string
    {
        return $this->mes;
    }
}
```

O de março e o de abril podem estar na fila juntos; dois de março, não.

**Dois jobs que não podem rodar ao mesmo tempo para a mesma coisa.**
Recalcular a multa de um leitor enquanto outro job registra uma devolução
dele produz um valor que nenhum dos dois quis. O middleware
`WithoutOverlapping` põe uma trava por chave:

```php
public function middleware(): array
{
    return [(new WithoutOverlapping("leitor:{$this->leitorId}"))
        ->releaseAfter(30)];
}
```

**Uma tarefa agendada que não pode rodar em dois servidores.** Com o
segundo servidor web da Casa Amarela, os dois agendadores disparavam os
avisos das nove:

```php
Schedule::call(new DispararAvisosDeDevolucao)
    ->dailyAt('09:00')
    ->onOneServer()
    ->withoutOverlapping();
```

`onOneServer` usa o cache para eleger um servidor por execução — e por
isso exige um cache compartilhado, como o `database` ou o `redis`, e não o
`file` de cada máquina.

## `timeout` e `retry_after`

Este é o par de números responsável pela maior parte das mensagens em
dobro em produção, e a Casa Amarela já pagou por ele uma vez.

`timeout` é quanto tempo o **worker** deixa um job rodar antes de matá-lo.
`retry_after` é quanto tempo a **fila** espera por um job que foi reservado
antes de concluir que o worker morreu e entregá-lo a outro.

```php title="config/queue.php" numbered
'database' => [
    'driver' => 'database',
    'table' => 'jobs',
    'queue' => 'default',
    'retry_after' => 90,
],
```

Um `ImportarLote` com `timeout` de 240 segundos, nessa conexão, faz isto:
aos 90 segundos, a fila acha que ele morreu e o entrega a um segundo
worker. Os dois importam as mesmas mil linhas. Nada falhou, nenhum log
avisou — e o acervo tem dois *Vidas Secas* com o mesmo tombo, se o banco
não tiver a restrição única do capítulo @cap:migrations-seeders-e-factories.

A regra: **`retry_after` maior que o maior `timeout` dos jobs daquela
conexão**, com folga. Como o `retry_after` é da **conexão**, e não da
fila, jobs longos ganham uma conexão própria:

```php title="config/queue.php" numbered
'database-longa' => [
    'driver' => 'database',
    'table' => 'jobs',
    'queue' => 'importacao',
    'retry_after' => 360,
],
```

É a `database-longa` do supervisor e do lote. Mesma tabela, mesmo banco,
outra paciência.

:::warning
`retry_after` menor que `timeout` não gera erro, aviso nem linha de log.
Gera trabalho em dobro, de vez em quando, só nos jobs mais lentos — que
são exatamente os que ninguém está olhando. Confira os dois números sempre
que criar um job que pode passar de um minuto.
:::

## O worker é um processo que envelhece

O capítulo @cap:escopo-e-referencias avisou: variável `static` e cache em memória
duram enquanto o processo durar. Na requisição web, é um instante. No
worker, são horas — e cada job deixa um pouco de memória para trás.

Três opções do `queue:work` põem um limite na idade do worker, e o
supervisor sobe um novo no lugar:

| Opção | Encerra o worker depois de |
|---|---|
| `--max-jobs=500` | quinhentos jobs |
| `--max-time=3600` | uma hora |
| `--memory=256` | passar de 256 MB |

Tabela: O worker que se aposenta sozinho não precisa de ninguém para
reiniciá-lo de madrugada.

## Quando falha em produção

A tabela `failed_jobs` é a caixa de entrada da fila. Três comandos para
atendê-la:

```text
$ php artisan queue:failed
$ php artisan queue:retry --queue=avisos
$ php artisan queue:prune-failed --hours=720
```

O primeiro lista, com a exceção de cada um. O segundo devolve à fila todos
os que falharam na fila `avisos` — depois de o provedor voltar, e não
antes. O terceiro apaga os de mais de trinta dias, e vale agendar: uma
tabela de falhas com dois anos de lixo esconde a falha de hoje.

Com Redis no lugar do `database`, o **Horizon** dá um painel para tudo isto
— filas, espera, falhas, workers — e ajusta o número de workers sozinho.
Para a Casa Amarela, a consulta de espera e o `queue:monitor` bastam; o dia
em que não bastarem é o dia de trocar de driver.

:::note Na sua carreira
Fila é onde os sistemas guardam o que não querem ver. O trabalho sai da
requisição, a tela fica rápida, e o problema passa a acontecer num
processo sem tela, de madrugada, que ninguém abre.

Três perguntas antes de pôr qualquer trabalho numa fila: **quanto tempo
ele pode esperar?** — isso escolhe a fila. **Quanto tempo ele pode
demorar?** — isso escolhe o `timeout` e a conexão. **Quem fica sabendo se
ele não acontecer?** — isso escolhe o `failed()`, o monitor e o alerta. Se
a terceira resposta for "ninguém", ele ainda não está pronto para a fila.
:::

:::tree title="Onde estamos agora"
casa-amarela/
  app/
    Importacao/ImportarDoacoes.php  # lote, gerador, progresso
    Jobs/
      ImportarLote.php              # Batchable, timeout 240
      GerarRelatorioMensal.php      # ShouldBeUnique por mês
    Notifications/DevolucaoAmanha.php # fila avisos, ritmo WhatsApp
  config/queue.php                  # database e database-longa
  routes/console.php                # monitor, onOneServer, prune
:::

:::summary
- Meça a espera do job mais antigo, não o tamanho da fila.
- Filas com nome separam urgências; `--queue=a,b,c` é prioridade estrita.
  Trabalho que não pode passar fome ganha worker próprio.
- `Bus::batch` agrupa, mostra progresso e chama `then`/`finally`;
  `allowFailures()` não deixa uma falha cancelar o resto.
- `Bus::chain` roda em ordem e para no primeiro erro.
- `RateLimited` devolve o job à fila e gasta tentativa: use `retryUntil`.
- `ShouldBeUnique`, `WithoutOverlapping` e `onOneServer` impedem
  trabalho em dobro em três situações diferentes.
- `retry_after` da conexão maior que o `timeout` de qualquer job dela.
- `--max-jobs`, `--max-time` e `--memory` aposentam o worker a tempo.
- `failed_jobs` é caixa de entrada: listar, retentar, podar.
:::

:::checkpoint
Você mede uma fila pela espera, separa trabalho urgente de trabalho
pesado, importa duzentas mil linhas em lote com progresso, respeita o
limite de um provedor sem perder avisos, impede trabalho em dobro nos três
lugares em que ele aparece, e acerta o par `timeout` e `retry_after`.
:::

:::exercise level=1
Em que fila — `avisos`, `default`, `importacao` ou `capas` — você poria
cada job, e por quê?

1. O comprovante de empréstimo, por WhatsApp.
2. A reindexação da busca do acervo, depois de uma importação.
3. A miniatura da capa que a Vera acabou de enviar.
4. O e-mail de "sua reserva está disponível".

:::answer
1. `avisos`. O leitor está no balcão esperando.
2. `importacao`. Pode levar minutos e pode esperar a madrugada.
3. `capas`. É pesado, e a Vera aceita ver a capa em um ou dois minutos;
   não deve competir com os avisos.
4. `avisos`. A reserva tem prazo, e cada minuto de atraso é um minuto a
   menos para o leitor buscar o livro.
:::

:::exercise level=2
O job `SincronizarComCatalogoNacional` consulta uma API externa que às
vezes leva até três minutos para responder. Ele está na conexão `database`
padrão, com `retry_after` de 90 e `timeout` de 200. Descreva o que
acontece numa resposta lenta e escreva a configuração corrigida.

:::answer
Aos 90 segundos, a fila dá o job por perdido e o entrega a outro worker,
enquanto o primeiro ainda espera a API. As duas cópias consultam a API e
gravam o resultado — duas vezes, sem erro nenhum. Aos 200 segundos, a
primeira ainda pode ser morta pelo `timeout` e contar uma falha.

Correção: o job vai para a conexão longa, com `retry_after` acima do
`timeout`, e o `timeout` acima do pior tempo da API:

```php
// config/queue.php, na conexão 'database-longa'
'retry_after' => 360,

// no job
public int $timeout = 240;

SincronizarComCatalogoNacional::dispatch()
    ->onConnection('database-longa')
    ->onQueue('importacao');
```

E, como a API é externa, o job deve ser idempotente do mesmo jeito: gravar
com "atualiza se existir" pelo identificador do catálogo, nunca um
`INSERT` cego.
:::

:::exercise level=3
Desenhe a fila da Casa Amarela para o dia em que a associação abrir
a segunda biblioteca, no bairro vizinho, no mesmo sistema: o dobro de
avisos, uma importação por semana e capas enviadas pelas duas
bibliotecárias. Diga quantos workers de cada tipo, que números você
monitoraria, com que limite, e em que momento você trocaria o `database`
pelo `redis`.

:::answer
Workers:

- **urgente** (`avisos,default`): de dois para três. Seiscentos avisos às
  nove, limitados a sessenta por minuto no WhatsApp, levam dez minutos de
  qualquer jeito; o terceiro worker é para o e-mail e o histórico não
  esperarem o WhatsApp.
- **pesado** (`importacao,capas`, conexão longa): continua um. A
  importação semanal pode levar a noite; capas são poucas.

Monitoraria:

- espera do job mais antigo em `avisos`: alerta acima de **5 minutos**;
- espera em `importacao`: alerta acima de **12 horas** — ela pode
  esperar, mas não para sempre;
- `failed_jobs` novos por hora: alerta acima de **10**;
- memória dos workers, pelo supervisor.

Trocaria pelo `redis` quando um destes acontecer: a consulta de espera
ficar lenta na tabela `jobs`, os workers passarem a disputar a mesma
linha com frequência (visível como jobs reservados e liberados em
sequência), ou a equipe precisar do painel do Horizon para entender o que
acontece. Não antes: dois bairros ainda cabem numa tabela.
:::
