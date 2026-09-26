---
title: "Outbox: o banco confirmou, a mensagem não"
number: 17
slug: outbox
part: p4
kicker: "Com o RabbitMQ parado, o checkout respondeu 201. A nota saiu quando ele voltou, e ninguém precisou fazer nada."
goal: >-
  Reconhecer o problema da escrita dupla entre banco e broker, gravar o
  evento na mesma transação do pedido numa tabela de outbox, publicar essa
  tabela com o despachante da Mirabel, e ver um checkout que continua
  vendendo com o RabbitMQ parado.
---

:::story Quatro horas, de novo
A Júlia apresentou o desenho novo numa quarta à tarde, na mesa da
cozinha. Checkout grava o pedido, publica `pedido.pago`, responde. Tudo o
mais em filas, com retry, fila de erro, idempotência.

O Rafa ouviu tudo com atenção e fez a pergunta que ninguém tinha feito.

— E se o RabbitMQ cair?

— O publish tenta de novo por alguns segundos e desiste.

— E o pedido?

— O pedido já foi gravado. O evento, não.

— Então o cliente pagou e a nota não sai.

— Nem a etiqueta, nem o e-mail.

O Rafa encostou na cadeira.

— Então a gente trocou sete coisas que podiam cair por uma coisa que pode
cair.

— Trocamos — disse Júlia. — E ela é a única que a gente controla.

— Ano passado a gente também achava que controlava.

O Kaique virou uma etiqueta e não escreveu nada. Ficou só olhando.
:::

O Rafa encontrou o último buraco do desenho, e ele tem nome: **escrita
dupla**. O checkout grava num sistema — o banco — e publica em outro — o
broker. Não existe transação que abrace os dois. O exercício do capítulo
@cap:mirabel-dentro-do-laravel mostrou que as duas ordens falham: gravar e
depois publicar perde o evento se o broker cair; publicar e depois gravar
anuncia um pedido que talvez não exista.

## Um lugar só para escrever

A saída é deixar de escrever em dois lugares. O checkout grava o pedido
**e o evento** no banco, na **mesma transação**: ou os dois entram, ou
nenhum. O evento fica numa tabela própria, a **outbox** — a caixa de saída
—, esperando. Outro processo lê essa tabela e publica no broker o que
estiver pendente.

:::term Outbox transacional
Um padrão em que a aplicação grava as mensagens que precisa publicar numa
tabela do próprio banco, dentro da transação que altera os dados. Um
processo separado, o despachante, publica essas mensagens no broker e as
marca como publicadas. A transação do banco passa a ser a única que
importa.
:::

O banco já sabe fazer o que o broker e o banco juntos não sabem: gravar
duas coisas atomicamente. E o despachante só precisa de uma propriedade —
tentar de novo até conseguir —, que a Parte 4 inteira ensinou a fazer sem
perder nem inventar mensagens.

## A tabela

```php title="database/migrations/2026_09_08_000000_create_outbox_table.php" numbered
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('outbox', function (Blueprint $table) {
            $table->string('id')->primary();
            $table->json('mensagem');
            $table->timestamp('criada_em');
            $table->timestamp('publicada_em')->nullable();
            $table->unsignedInteger('falhas')->default(0);
            $table->text('ultimo_erro')->nullable();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('outbox');
    }
};
```

A chave primária é o `message_id` — o mesmo pedido não entra duas vezes
na outbox. `mensagem` guarda tudo o que é preciso para publicar depois:
exchange, routing key, corpo e propriedades, em JSON. `publicada_em` nula
quer dizer pendente. `falhas` e `ultimo_erro` servem a quem vai investigar
por que uma linha está pendente há uma hora.

## O store

A Mirabel define o contrato da outbox numa interface de quatro métodos, e
a aplicação implementa sobre o banco dela:

```php title="app/Mensageria/OutboxNoBanco.php" numbered
<?php

declare(strict_types=1);

namespace App\Mensageria;

use Illuminate\Support\Facades\DB;
use Mirabel\RabbitMQ\Outbox\OutboxMessage;
use Mirabel\RabbitMQ\Outbox\OutboxStoreInterface;

final class OutboxNoBanco implements OutboxStoreInterface
{
    public function add(OutboxMessage $message): void
    {
        DB::table('outbox')->insert([
            'id' => $message->id,
            'mensagem' => json_encode($message->toArray()),
            'criada_em' => now(),
        ]);
    }

    public function pending(int $limit): iterable
    {
        $linhas = DB::table('outbox')
            ->whereNull('publicada_em')
            ->orderBy('criada_em')
            ->limit($limit)
            ->get();

        foreach ($linhas as $linha) {
            $dados = json_decode($linha->mensagem, true);
            yield OutboxMessage::fromArray($dados);
        }
    }

    public function markPublished(string $id): void
    {
        DB::table('outbox')->where('id', $id)
            ->update(['publicada_em' => now()]);
    }

    public function markFailed(string $id, \Throwable $erro): void
    {
        DB::table('outbox')->where('id', $id)->update([
            'falhas' => DB::raw('falhas + 1'),
            'ultimo_erro' => $erro->getMessage(),
        ]);
    }
}
```

`OutboxMessage` é a mensagem pronta para publicar, como a Mirabel a
monta: `toArray()` a transforma em array — os headers incluídos — para
virar JSON, e `fromArray()` faz o caminho de volta. `yield` devolve as
mensagens uma a uma, em vez de montar a lista inteira na memória.
`DB::raw('falhas + 1')` manda a expressão para o SQL como está, para o
banco somar.

## O checkout, pela última vez

```php title="app/Http/Controllers/CheckoutController.php" numbered
<?php

namespace App\Http\Controllers;

use App\Eventos\PedidoPago;
use App\Mensageria\OutboxNoBanco;
use App\Models\Pedido;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class CheckoutController extends Controller
{
    public function finalizar(Request $request, OutboxNoBanco $outbox)
    {
        $dados = $request->validate([
            'carrinho' => ['required', 'string', 'max:64'],
            'total_centavos' => ['required', 'integer', 'min:1'],
            'cep' => ['required', 'regex:/^\d{5}-\d{3}$/'],
        ]);

        $pedido = DB::transaction(function () use ($dados, $outbox) {
            $pedido = Pedido::createOrFirst(
                ['carrinho' => $dados['carrinho']],
                $dados,
            );
            if (!$pedido->wasRecentlyCreated) {
                return $pedido; // segundo clique: o mesmo pedido
            }

            $evento = new PedidoPago([
                'pedido' => $pedido->id,
                'total_centavos' => $pedido->total_centavos,
                'entrega' => ['cep' => $pedido->cep],
            ]);
            $outbox->add($evento->toOutboxMessage(
                messageId: "pedido-{$pedido->id}-pago",
                idempotencyKey: "pedido-{$pedido->id}",
            ));

            return $pedido;
        });

        return response()->json(['pedido' => $pedido->id], 201);
    }
}
```

`DB::transaction()` executa a função dentro de uma transação: se qualquer
linha lançar exceção, nada do que ela gravou fica no banco. As linhas 21 a
41 são a transação inteira — o pedido e o evento, juntos. O
`createOrFirst` por carrinho é o do capítulo sobre idempotência: um
segundo clique recebe o mesmo pedido e não grava um segundo evento.

`toOutboxMessage()` é o irmão do `publish()` que não toca na rede: monta
a mensagem exatamente como o `publish()` mandaria — as mesmas
propriedades, o mesmo `message_id`, os mesmos headers — e a devolve. O
checkout não fala mais com o RabbitMQ. Ele só fala com o banco, como
fazia antes de existir mensageria.

## O despachante

```php title="app/Console/Commands/DespacharOutbox.php" numbered
<?php

namespace App\Console\Commands;

use App\Mensageria\OutboxNoBanco;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;
use Mirabel\RabbitMQ\ConnectionConfig;
use Mirabel\RabbitMQ\Outbox\AmqpOutboxPublisher;
use Mirabel\RabbitMQ\Outbox\OutboxDispatcher;

class DespacharOutbox extends Command
{
    protected $signature = 'outbox:despachar';

    protected $description = 'Publica os eventos guardados na outbox';

    public function handle(OutboxNoBanco $outbox): int
    {
        $config = ConnectionConfig::fromEnvironment();
        $despachante = new OutboxDispatcher(
            $outbox,
            new AmqpOutboxPublisher($config),
            Log::channel(),
        );

        while (true) {
            $publicadas = $despachante->dispatch(limit: 100);
            if ($publicadas > 0) {
                $hora = now()->format('H:i:s');
                $this->line("{$hora} publicadas: {$publicadas}");
            }
            sleep(1);
        }
    }
}
```

O `OutboxDispatcher` da Mirabel faz o trabalho: pega até cem pendentes,
publica cada uma e marca como publicada **depois** de publicar; se a
publicação falhar, chama `markFailed` e segue para a próxima. O
`AmqpOutboxPublisher` usa as mesmas variáveis de ambiente de sempre — com
`MB_RABBITMQ_PUBLISHER_CONFIRMS=true`, "publicada" quer dizer confirmada
pelo broker.

## O teste que o Rafa pediu

Pare o broker e faça um checkout:

```text
$ docker compose stop rabbitmq
$ curl -X POST localhost:8000/api/checkout ...
{"pedido":1} 201
```

Status 201. O checkout não percebeu nada — ele não fala com o broker. Ligue o
despachante e olhe a outbox depois de alguns segundos:

```text
$ php artisan outbox:despachar
```

```text
pedido-1-pago | publicada: não | falhas: 2 | stream_socket_client():
Unable to connect to tcp://127.0.0.1
```

Pendente, com as falhas contadas e o motivo escrito. Suba o broker e o
worker do fiscal:

```text
$ docker compose start rabbitmq
$ php artisan rabbitmq:consume EmitirNotaFiscal
```

```text
00:07:38 publicadas: 1
[2026-09-26 00:07:40] local.INFO: NF-e emitida {"pedido":1}
```

A outbox marca a linha com a hora da publicação. O broker ficou fora do
ar, o cliente não viu erro, e a nota saiu quando ele voltou — que é
exatamente o que a fila fez pela SEFAZ, agora aplicado ao próprio broker.

:::key
Com outbox, o checkout depende de um sistema só: o banco de dados, o mesmo
de que ele já dependia para gravar o pedido. O broker vira uma dependência
**do despachante**, e um broker fora do ar vira uma outbox crescendo — um
atraso, não um erro.
:::

## O que o outbox não resolve

Ele não inventa exatamente-uma-vez. O despachante publica e **depois**
marca como publicada; se ele cair entre as duas coisas, a linha continua
pendente e será publicada de novo. O `message_id` é o mesmo, a chave de
idempotência é a mesma, e o consumidor do capítulo
@cap:idempotencia-o-pedido-40117 descarta a repetição. O outbox e a
idempotência são as duas metades de uma mesma garantia: nunca perder, do
lado de quem publica; nunca repetir o efeito, do lado de quem consome.

Ele também não é de graça:

| Custo | O que fazer |
|---|---|
| a tabela cresce para sempre | apagar linhas publicadas há mais de alguns dias |
| um despachante a mais para manter no ar | supervisioná-lo como os workers |
| atraso de até um ciclo do despachante | um segundo, no exemplo; ajustável |
| dois despachantes publicam a mesma linha | rodar um só, ou reservar linhas com `FOR UPDATE SKIP LOCKED` |

Tabela: `FOR UPDATE SKIP LOCKED`, do PostgreSQL e do MySQL 8, faz cada
despachante pular as linhas que outro já está publicando.

:::pitfall
O despachante do exemplo tenta a cada segundo, e com o broker fora cada
tentativa espera o tempo de conexão esgotar: no teste acima, a linha
acumulou dezesseis falhas em poucos segundos de queda. Para uma queda
longa, isso é log demais. Espaçar as tentativas quando `dispatch()`
devolve zero com falhas — dobrar o `sleep` até um limite — é a mesma
lógica de backoff que a biblioteca usa no `publish()`.
:::

:::milestone
Você tem: o checkout gravando pedido e evento numa transação só, a tabela
`outbox`, o `OutboxNoBanco` implementando o contrato da Mirabel, e o
despachante publicando o que estiver pendente. O RabbitMQ pode cair durante
a Black Friday sem que um cliente veja erro ou um pedido fique sem nota.
:::

:::summary
- Gravar no banco e publicar no broker são duas escritas sem transação em
	comum; qualquer ordem perde ou inventa eventos quando um dos lados cai.
- O outbox grava o evento numa tabela do próprio banco, na mesma
	transação do pedido; `toOutboxMessage()` monta a mensagem sem tocar na
	rede.
- Um despachante lê as pendentes, publica e marca; o `OutboxDispatcher` da
	Mirabel faz isso sobre qualquer `OutboxStoreInterface`.
- Com o broker fora do ar, o checkout continua respondendo 201 e a outbox
	cresce; quando ele volta, tudo é publicado.
- O despachante pode publicar a mesma linha duas vezes; o consumidor
	idempotente é a outra metade da garantia.
:::

:::exercise level=1
Com o outbox, reescreva o teste de feature do checkout sem nenhum
publicador falso. O que o teste passa a afirmar?

:::answer
```php
public function test_checkout_guarda_o_evento_na_outbox(): void
{
    $this->postJson('/api/checkout', [
        'carrinho' => 'c-7f3a',
        'total_centavos' => 8990,
        'cep' => '37701-000',
    ])->assertCreated();

    $linha = DB::table('outbox')->first();
    $mensagem = json_decode($linha->mensagem, true);

    $this->assertSame('pedido-1-pago', $linha->id);
    $this->assertSame('pedido.pago', $mensagem['routing_key']);
    $this->assertNull($linha->publicada_em);
}
```

O teste afirma que o checkout deixou o evento certo **pendente de
publicação** no banco — que é tudo o que o checkout faz agora. Não há
nada para substituir: o controller não fala com o broker, e o teste roda
com o banco em memória que o Laravel já usa nos testes.
:::

:::exercise level=2
A validação do checkout passa, o `Pedido::create` funciona, e o
`$outbox->add()` lança exceção porque já existe uma linha com o id
`pedido-1-pago` — um banco restaurado de backup, por exemplo. O que fica
gravado, e o que o cliente vê?

:::answer
Nada fica gravado. A exceção acontece dentro do `DB::transaction()`, e o
Laravel desfaz a transação inteira — inclusive o pedido que o `create`
tinha acabado de inserir. O cliente recebe erro 500.

É o comportamento certo, e a prova de que a transação está fazendo o
trabalho: pedido e evento entram juntos ou não entram. O defeito de
verdade é o id repetido, que aqui é sintoma de um banco em estado estranho;
num banco saudável, o id do pedido é único, e o `message_id` derivado
dele também.
:::
