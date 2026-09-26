---
title: "Idempotência: o pedido 40.117"
number: 15
slug: idempotencia-o-pedido-40117
part: p4
kicker: "O senhor apertou o botão três vezes. O sistema novo tem que entender que foi uma compra só — mesmo com dois consumidores trabalhando ao mesmo tempo."
goal: >-
  Entender de onde vêm as mensagens repetidas, usar o store de idempotência
  da Mirabel para descartar repetições, ver ele falhar com dois consumidores
  concorrentes, e fechar a porta com uma reserva no banco de dados,
  incluindo o caso do consumidor que morre no meio.
---

:::story O senhor do 40117
Em outubro, o Kaique atendeu de novo o senhor do pedido 40117. Ele ia
comprar para o Natal e queria saber se "aquilo do ano passado" não ia
acontecer de novo.

— O senhor apertou o botão três vezes, lembra?

— Apertei porque não aparecia nada.

— E foi cobrado três vezes.

— Foi. E recebi uma geleia.

O Kaique anotou tudo e levou para a mesa da Júlia.

— Ele vai apertar três vezes de novo — disse ele. — Todo mundo aperta.

— O checkout novo responde em meio segundo. Ele vai apertar menos.

— Menos não é nenhuma.

A Júlia abriu o painel. Três `pedido.pago` com a mesma chave de
idempotência, publicados no teste da véspera, tinham virado uma nota
fiscal só.

— Com um consumidor, está resolvido.

— E com dois?

Ela não respondeu. Ligou o segundo consumidor e publicou os três de novo.
:::

O capítulo @cap:ack-quando-a-mensagem-pode-morrer terminou com uma troca:
com ack manual, o RabbitMQ nunca perde, e às vezes repete. O Seu Norberto
deixou claro que "às vezes repete" não serve para nota fiscal. Este
capítulo é a outra metade da troca: um consumidor que recebe a mesma coisa
duas vezes e faz uma só.

:::term Idempotente
Uma operação é idempotente quando fazê-la duas vezes tem o mesmo efeito
que fazê-la uma. Apertar o botão do elevador é idempotente; pedir uma
pizza, não. Um consumidor idempotente pode receber a mesma mensagem
quantas vezes o broker quiser, e o mundo muda uma vez só.
:::

## De onde vêm as repetições

Numa fila com ack manual, uma mensagem chega mais de uma vez por quatro
caminhos, e só um deles depende do cliente:

| Caminho | Quem repete | O que se repete |
|---|---|---|
| o consumidor cai depois do efeito e antes do ack | o broker | a mesma mensagem, mesmo `message_id` |
| a conexão cai entre o publish e a resposta, e o produtor tenta de novo | o produtor | a mesma mensagem, mesmo `message_id` |
| o reprocessamento da fila de erro morre no meio | quem reprocessa | a mesma mensagem |
| o cliente aperta o botão três vezes | o cliente | **mensagens diferentes**, mesma operação |

Tabela: Os três primeiros repetem a mensagem; o último repete a
intenção.

A última linha é a do 40117, e é por isso que o capítulo
@cap:eventos-com-mirabel separou `message_id` de chave de idempotência. Três
cliques geram três publicações — três `message_id` diferentes, se ninguém
tomar cuidado —, mas é **um pagamento**. A chave que o checkout passa,
`pedido-40117`, é o que as três têm em comum.

## O clique triplo começa no checkout

Uma chave só identifica a operação se for **a mesma nos três cliques**. No
checkout do capítulo @cap:mirabel-dentro-do-laravel, ela vem do id do
pedido — e cada clique cria um pedido novo, com um id novo. Três cliques
seriam três pedidos, três chaves, três notas, e nenhum consumidor teria
como saber.

A correção começa antes da mensagem. A página do carrinho manda, junto
com o formulário, o identificador do **carrinho**, e a tabela `pedidos`
ganha uma coluna `carrinho` com índice único. O checkout cria o pedido uma
vez por carrinho:

```php
$pedido = Pedido::createOrFirst(
    ['carrinho' => $dados['carrinho']],
    $dados,
);
if (!$pedido->wasRecentlyCreated) {
    return $pedido; // segundo clique: o mesmo pedido
}
```

`createOrFirst` tenta criar o pedido; se o índice único recusar — outro
clique chegou antes —, ele busca e devolve o que já existe.
`wasRecentlyCreated` diz qual dos dois aconteceu, e só o primeiro clique
segue para publicar. O segundo e o terceiro recebem o mesmo pedido e não
publicam nada.

Isso fecha a última linha da tabela na origem. As três primeiras —
reentrega do broker, novas tentativas do produtor, reprocessamento —
continuam existindo, e é para elas que o consumidor precisa se proteger.
O script abaixo simula o pior caso: o mesmo pagamento publicado três
vezes, venha de onde vier.

## O store de idempotência

A Mirabel aceita, no worker, um **store de idempotência**: um objeto que
responde duas perguntas — "já vi esta chave?" e "anote esta chave". A
biblioteca consulta antes do `handle()`; se a chave já foi vista, confirma
a mensagem sem chamar o método. Se não, chama, e anota depois do sucesso.
A chave é a `x-idempotency-key` ou, na falta dela, o `message_id`.

O store precisa guardar as chaves em algum lugar que sobreviva a restart e
que todos os consumidores enxerguem — um banco de dados. A interface tem
dois métodos:

```php title="src/Mensageria/ChavesProcessadas.php" numbered
<?php

declare(strict_types=1);

namespace DoceMirabel\Mensageria;

use Mirabel\RabbitMQ\Idempotency\IdempotencyStoreInterface;
use PDO;

final class ChavesProcessadas implements IdempotencyStoreInterface
{
    public function __construct(private readonly PDO $banco)
    {
        $this->banco->exec(
            'CREATE TABLE IF NOT EXISTS chaves_processadas (
                chave TEXT PRIMARY KEY,
                em TEXT NOT NULL
            )',
        );
    }

    public function has(string $key): bool
    {
        $consulta = $this->banco->prepare(
            'SELECT 1 FROM chaves_processadas WHERE chave = ?',
        );
        $consulta->execute([$key]);

        return $consulta->fetchColumn() !== false;
    }

    public function remember(string $key): void
    {
        $this->banco->prepare(
            'INSERT OR IGNORE INTO chaves_processadas VALUES (?, ?)',
        )->execute([$key, date('c')]);
    }
}
```

O exemplo usa SQLite, o banco num arquivo só que o PHP já traz, pela PDO —
a mesma camada de acesso a banco que funciona com MySQL e PostgreSQL. O
`?` na consulta é um marcador que `execute()` preenche com segurança.
`PRIMARY KEY` impede duas linhas com a mesma chave, e `INSERT OR IGNORE`,
do SQLite, não reclama se a chave já existir.

O worker liga o store sobrescrevendo um método:

```php
protected function idempotencyStore(): ?IdempotencyStoreInterface
{
    return new ChavesProcessadas($this->banco);
}
```

E um script publica o mesmo pagamento três vezes, como o senhor do 40117:

```php title="clique-triplo.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use DoceMirabel\Eventos\PedidoPago;

$pedido = ['pedido' => 40117, 'total_centavos' => 8990];

for ($clique = 1; $clique <= 3; $clique++) {
    (new PedidoPago($pedido))
        ->publish(idempotencyKey: 'pedido-40117');
    echo "clique {$clique}: pedido.pago publicado", PHP_EOL;
}
```

Com um consumidor:

```text
$ php clique-triplo.php
clique 1: pedido.pago publicado
clique 2: pedido.pago publicado
clique 3: pedido.pago publicado
```

```text
fiscal esperando pedidos pagos. Ctrl+C para sair.
NF-e do pedido 40117 (pedido-40117)
```

Três mensagens, uma nota. As outras duas foram confirmadas sem passar pelo
`handle()`.

## Dois consumidores

Agora o que a Júlia fez no fim da cena: ligar um segundo consumidor. Para
o defeito aparecer, basta que a emissão demore — e ela demora; a SEFAZ
leva um segundo num dia bom. Com um `sleep(1)` no `handle()`, dois
consumidores e o mesmo clique triplo:

```text
consumidor A
NF-e do pedido 40117 (pedido-40117)

consumidor B
NF-e do pedido 40117 (pedido-40117)
```

Duas notas. O store estava ligado e não impediu.

O motivo está na ordem das operações. A biblioteca **pergunta** antes do
`handle()` e **anota** depois. O consumidor A pergunta — a chave não
existe — e começa a emitir. O consumidor B, meio segundo depois, pergunta
— a chave ainda não existe, porque A não terminou — e começa a emitir
também. Os dois anotam no fim. O banco recusou a segunda anotação em
silêncio, e as duas notas já tinham saído.

:::key
"Pergunta, faz, anota" é uma corrida sempre que dois processos podem fazer
a mesma coisa ao mesmo tempo. O store de idempotência descarta repetições
**que chegam depois** da primeira terminar; ele não protege contra as que
chegam **enquanto** a primeira está trabalhando.
:::

Isso não é defeito da Mirabel, e não se resolve na biblioteca: ela não
sabe o que "fazer" significa, nem quanto tempo leva. Quem sabe é o
consumidor, e a solução é inverter a ordem — **anotar antes de fazer**, de
um jeito que só um consiga anotar.

## Reservar antes de emitir

O banco de dados já sabe resolver disputa: duas inserções com a mesma
chave primária, ao mesmo tempo, e só uma passa. O worker reserva a nota
antes de chamar a SEFAZ:

```php title="src/Workers/EmitirNotaFiscal.php" numbered
<?php

declare(strict_types=1);

namespace DoceMirabel\Workers;

use Mirabel\RabbitMQ\Envelope;
use Mirabel\RabbitMQ\Worker;
use PDO;
use PDOException;

final class EmitirNotaFiscal extends Worker
{
    public static string $queue = 'fiscal.pedidos-pagos';
    public static array $routingKeys = ['pedido.pago'];
    public static array $retry = [
        'delay' => 2000, 'max_attempts' => 3,
    ];

    public function __construct(private readonly PDO $banco)
    {
        $this->banco->exec(
            'CREATE TABLE IF NOT EXISTS notas (
                pedido INTEGER PRIMARY KEY,
                situacao TEXT NOT NULL
            )',
        );
    }

    public function handle(Envelope $envelope): void
    {
        $pedido = $envelope->body['pedido'];

        try {
            $this->banco->prepare(
                "INSERT INTO notas VALUES (?, 'emitindo')",
            )->execute([$pedido]);
        } catch (PDOException) {
            echo "pedido {$pedido}: já reservada", PHP_EOL;
            return;
        }

        sleep(1); // a SEFAZ autorizando
        echo "NF-e do pedido {$pedido} emitida", PHP_EOL;

        $this->banco->prepare(
            "UPDATE notas SET situacao = 'emitida' WHERE pedido = ?",
        )->execute([$pedido]);
    }
}
```

A chave primária agora é **o pedido**, não a mensagem: uma nota por
pedido, venha de quantas mensagens vier. As linhas 34 a 41 tentam
reservar; se o pedido já existe na tabela, o banco lança exceção — é a
PDO configurada com `ERRMODE_EXCEPTION` —, e o `catch` retorna sem fazer
nada, o que para a Mirabel é sucesso: ack.

O mesmo teste, dois consumidores e três cliques:

```text
consumidor A
pedido 40117: já reservada
pedido 40117: já reservada

consumidor B
NF-e do pedido 40117 emitida
```

Uma nota. B reservou primeiro; A tentou duas vezes e foi recusado pelo
banco nas duas.

## O consumidor que morre no meio

Falta um caso, e ele é o mais caro. B reservou, chamou a SEFAZ, a nota foi
autorizada — e B caiu antes do `UPDATE` e do ack. A mensagem volta para a
fila, alguém a recebe, tenta reservar, e ouve "já reservada, nada a
fazer". A mensagem é confirmada. Na tabela, o pedido fica para sempre em
`emitindo`.

Talvez a nota tenha saído, talvez não: B pode ter caído antes ou depois
da SEFAZ responder. O consumidor que chega depois não sabe, e "nada a
fazer" é a resposta errada nos dois casos que importam — se a nota não
saiu, ninguém mais vai emiti-la.

A saída tem duas partes. A primeira é distinguir as situações na hora da
recusa: `emitida` é mesmo nada a fazer; `emitindo` quer dizer que alguém
começou e talvez não terminou. A segunda é ter um jeito de **perguntar ao
mundo** o que aconteceu. A SEFAZ permite consultar se já existe nota
autorizada para um número de pedido; um gateway de pagamento permite
consultar se uma cobrança com certa chave já foi feita. Quem começou e não
terminou precisa consultar antes de repetir.

```php
} catch (PDOException) {
    $situacao = $this->situacaoDaNota($pedido);
    if ($situacao === 'emitindo') {
        // alguém começou e talvez tenha caído: confira na SEFAZ
        throw new \RuntimeException("nota do {$pedido} em andamento");
    }
    return; // emitida: nada a fazer
}
```

`situacaoDaNota()` é um método do próprio worker, que faz um `SELECT
situacao FROM notas WHERE pedido = ?` e devolve o texto. Lançar exceção
aqui manda a mensagem para o retry: se o primeiro
consumidor ainda estiver trabalhando, a próxima tentativa, dois segundos
depois, encontra `emitida` e termina. Se ele morreu, as tentativas
esgotam e a mensagem vai para a fila de erro com o motivo "nota em
andamento" — que é exatamente o que alguém precisa olhar, com a consulta à
SEFAZ na mão.

:::pitfall
Idempotência se garante **no efeito**, não na mensagem. Deduplicar pelo
`message_id` protege contra reentregas do broker e nada mais: o clique
triplo gera `message_id` diferentes. A chave certa é a do negócio — o
pedido, o pagamento, a nota — e a proteção certa é uma restrição que o
banco, ou o serviço externo, faz valer.
:::

:::milestone
Você tem: o store de idempotência da Mirabel descartando repetições que
chegam depois; a reserva da nota por pedido, com chave primária no banco,
impedindo duas notas mesmo com consumidores concorrentes; e o caso
"emitindo" tratado como pendência, e não como sucesso.
:::

:::summary
- Uma fila com ack manual repete mensagens; clientes repetem intenções. A
	chave de idempotência identifica a operação; o `message_id`, a
	mensagem.
- `idempotencyStore()` faz a Mirabel confirmar sem chamar o `handle()`
	mensagens cuja chave já foi processada.
- Com consumidores concorrentes, "pergunta, faz, anota" é uma corrida: o
	experimento emitiu duas notas com o store ligado.
- Reservar antes de agir, com uma chave primária do negócio, deixa o banco
	decidir quem trabalha.
- Reserva sem conclusão é pendência: consulte o mundo antes de repetir, ou
	mande para retry e, se esgotar, para a fila de erro.
:::

:::exercise level=1
No `EmitirNotaFiscal` com reserva, o que acontece se o checkout publicar
o `pedido.pago` do 40117, o fiscal emitir a nota, e uma semana depois
alguém reprocessar por engano uma cópia antiga dessa mensagem?

:::answer
A reserva falha — o pedido 40117 já está na tabela, com situação
`emitida` —, o worker retorna sem fazer nada, e a Mirabel confirma a
mensagem. Nenhuma nota nova. A proteção não depende do tempo que passou
nem de a chave ainda estar num cache: depende de uma linha no banco, que
fica lá enquanto o pedido existir.
:::

:::exercise level=2
A expedição também não pode imprimir duas etiquetas para o mesmo pedido,
mas a Zebrinha não tem como "consultar" se já imprimiu. Proponha o que o
consumidor da expedição faz no caso "reservado e não concluído".

:::answer
A impressora não responde à pergunta "você já imprimiu isto?", então não
há como descobrir, e o consumidor precisa escolher qual erro prefere. Para
a expedição, uma etiqueta repetida é barata — a Denise joga fora a
duplicada — e uma etiqueta que não sai é um pedido parado. A escolha é
reimprimir: no caso `imprimindo`, o consumidor imprime de novo, marcando a
etiqueta como **segunda via**, para a Denise saber que pode descartar uma.

A regra geral: quando o efeito não pode ser consultado, idempotência vira
uma decisão de negócio sobre qual erro custa menos — e essa decisão tem
dono, que não é quem escreve o consumidor.
:::
