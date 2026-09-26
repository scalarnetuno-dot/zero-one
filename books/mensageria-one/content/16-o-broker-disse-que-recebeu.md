---
title: "O broker disse que recebeu?"
number: 16
slug: o-broker-disse-que-recebeu
part: p4
kicker: "Três publicações sem erro nenhum, e só duas mensagens na fila. A terceira não falhou: ninguém perguntou."
goal: >-
  Ligar publisher confirms para saber quando o broker aceitou uma mensagem,
  provocar uma recusa de verdade, medir quanto a confirmação custa,
  reconhecer a mensagem sem rota que o broker confirma e descarta, e
  decidir o que o checkout faz quando o publish não é confirmado.
---

:::story A fila de avisos
Em novembro, o provedor de e-mail avisou que ia cobrar por mensagem acima
de um limite. A Júlia pôs um teto na fila de avisos: no máximo cinquenta
mil mensagens esperando. Passou disso, o broker recusa as novas — é melhor
perder um e-mail de "seu pedido foi enviado" do que a fila crescer sem
controle.

Uma semana depois, o Kaique estava olhando o painel e franziu a testa.

— O checkout publicou 1.212 pedidos hoje. A fila de avisos recebeu 1.212.

— Certo.

— E a fila do fiscal recebeu 1.212.

— Certo.

— E a fila de avisos está no limite desde as três.

A Júlia parou.

— Desde as três ela está recusando?

— Desde as três ela está recusando.

— E o checkout?

— O checkout não sabe. Para ele, publicou.
:::

O capítulo @cap:o-que-sobrevive-a-um-restart deixou uma janela aberta: o
`basic_publish` manda os bytes e volta, sem esperar o broker dizer nada. O
checkout nunca sabe se a mensagem chegou, se foi gravada ou se foi
recusada. Na maior parte dos dias, isso não importa. No dia em que importa,
não há nenhum registro de que aconteceu.

## Uma recusa de verdade

Para ver uma recusa, é preciso que o broker **tenha** motivo para recusar.
Uma fila com limite é o jeito mais simples de dar esse motivo: com os
argumentos `x-max-length` e `x-overflow` igual a `reject-publish`, a fila
aceita até o limite e recusa o que passar dele.

```php title="fila-cheia.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Wire\AMQPTable;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();

$canal->exchange_declare('doce.eventos', 'topic', false, true, false);
$limite = new AMQPTable([
    'x-max-length' => 2,
    'x-overflow' => 'reject-publish',
]);
$canal->queue_declare(
    'teste.lotada', false, true, false, false, false, $limite,
);
$canal->queue_bind('teste.lotada', 'doce.eventos', 'teste.lotada');
echo 'fila teste.lotada: no máximo 2 mensagens', PHP_EOL;
```

Os dois argumentos a mais de `queue_declare` — `nowait` e os argumentos da
fila — aparecem pela primeira vez aqui. `AMQPTable` empacota o array PHP
no formato de tabela do protocolo.

Um evento de teste com a routing key `teste.lotada` e um script que
publica três vezes, avisando o que aconteceu com cada uma:

```php title="tres.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use DoceMirabel\Eventos\Teste;

for ($i = 1; $i <= 3; $i++) {
    try {
        (new Teste(['n' => $i]))->publish();
        echo "mensagem {$i}: publicada", PHP_EOL;
    } catch (Throwable $erro) {
        echo "mensagem {$i}: ", $erro::class, PHP_EOL;
    }
}
```

`$erro::class` devolve o nome completo da classe da exceção. Rode primeiro
como o livro rodou até aqui:

```text
$ php fila-cheia.php
fila teste.lotada: no máximo 2 mensagens
$ php tres.php
mensagem 1: publicada
mensagem 2: publicada
mensagem 3: publicada
$ docker compose exec rabbitmq rabbitmqctl list_queues name messages
teste.lotada	2
```

Três "publicada", duas mensagens. A terceira foi recusada pela fila, e o
produtor não ficou sabendo.

## Publisher confirms

O AMQP tem um modo em que o broker **responde** a cada publicação. O canal
entra nesse modo com `confirm_select`, e daí em diante toda mensagem
recebe de volta um `basic.ack` — aceita, e gravada, se era persistente numa
fila durável — ou um `basic.nack` — recusada. O produtor espera a resposta
antes de seguir.

:::term Publisher confirm
A confirmação que o broker manda ao produtor depois de assumir a
responsabilidade por uma mensagem publicada. Não tem relação com o ack do
consumidor: um é o broker dizendo ao produtor "está comigo"; o outro é o
consumidor dizendo ao broker "terminei".
:::

Na Mirabel, confirms são uma variável de ambiente:

```bash
export MB_RABBITMQ_PUBLISHER_CONFIRMS=true
```

Com ela, o `publish()` põe o canal em modo de confirmação, espera a
resposta por até `MB_RABBITMQ_READ_WRITE_TIMEOUT` segundos e, se o broker
responder `nack`, lança `PublishNotConfirmedException`. Esvazie a fila e
rode de novo:

```text
$ docker compose exec rabbitmq rabbitmqctl purge_queue teste.lotada
$ php tres.php
mensagem 1: publicada
mensagem 2: publicada
mensagem 3: Mirabel\RabbitMQ\Exception\PublishNotConfirmedException
```

A mesma recusa, agora visível. O `purge_queue` esvazia uma fila sem
apagá-la.

:::key
Sem confirms, `publish()` sem erro quer dizer "os bytes saíram da minha
máquina". Com confirms, quer dizer "o broker aceitou e se responsabilizou
pela mensagem". Só a segunda frase fecha a janela entre publicar e gravar.
:::

## Quanto custa

Esperar uma resposta tem preço, e vale medir em vez de supor. Mil
publicações, no mesmo notebook, em três configurações:

| Configuração | 1000 publicações |
|---|---|
| conexão reaproveitada, sem confirms | 0,15 s |
| conexão reaproveitada, com confirms | 1,14 s |
| uma conexão por publicação, com confirms | 11,30 s |

Tabela: Reaproveitar a conexão é `MB_RABBITMQ_REUSE_CONNECTION=true`,
para processos que publicam muito — um comando de importação, um worker
que publica eventos.

Confirmar custa cerca de um milissegundo por mensagem, porque cada
publicação espera uma ida e volta ao broker e a gravação em disco. Para o
checkout, que publica **um** evento por requisição, um milissegundo não
aparece em lugar nenhum. O que pesa na terceira linha não é a
confirmação: é abrir uma conexão nova a cada publicação, o custo que o
capítulo @cap:conexao-canal-e-a-primeira-mensagem já tinha medido.

Para a Doce Mirabel, a decisão é fácil: confirms ligados em todo produtor.
O custo de um pedido pago sem evento é uma nota que não sai; o de um
milissegundo a mais é nada.

## A mensagem que o broker confirma e joga fora

Confirms respondem a uma pergunta específica — "o broker aceitou?" —, e há
um caso em que a resposta é sim e a mensagem some mesmo assim. Publique
com uma routing key que ninguém escuta, com confirms ligados:

```text
$ php -r 'require "vendor/autoload.php";
  (new DoceMirabel\Eventos\PedidoPago(["pedido" => 1]))
      ->publish(routingKey: "pedido.pagoo");
  echo "publicado sem erro\n";'
publicado sem erro
```

`pedido.pagoo` não casa com binding nenhum. O exchange descarta a
mensagem — e o broker confirma, porque aceitar e descartar uma mensagem
sem rota é um resultado válido do ponto de vista dele. O `ack` quer dizer
"cuidei dela"; descartar é um jeito de cuidar.

O AMQP tem uma resposta para isso também: a flag **mandatory** no
`basic_publish`. Com ela, uma mensagem sem rota é **devolvida** ao
produtor, em vez de descartada. A Mirabel ainda não usa essa flag — é uma
das limitações que a documentação dela lista —, mas a `php-amqplib` mostra
como ela funciona:

```php title="obrigatoria.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();
$canal->confirm_select();

$devolvidas = [];
$canal->set_return_listener(
    function (int $codigo, string $motivo, string $ex, string $chave)
        use (&$devolvidas): void {
        $devolvidas[] = "{$codigo} {$motivo}: {$chave}";
    },
);

$corpo = '{"pedido":40117}';
$mensagem = new AMQPMessage($corpo, ['delivery_mode' => 2]);
$canal->basic_publish(
    $mensagem, 'doce.eventos', 'pedido.pagoo', true,
);
$canal->wait_for_pending_acks_returns(3);

echo $devolvidas === [] ? 'entregue' : 'devolvida: ' . $devolvidas[0];
echo PHP_EOL;
```

O quarto argumento de `basic_publish`, `true`, é o `mandatory`.
`set_return_listener` registra a função que recebe as devoluções, e
`wait_for_pending_acks_returns` espera, por até três segundos, tanto as
confirmações quanto as devoluções.

```text
$ php obrigatoria.php
devolvida: 312 NO_ROUTE: pedido.pagoo
```

O código 312, `NO_ROUTE`, é o broker dizendo: aceitei, mas não havia
nenhuma fila para ela.

:::pitfall
Na Doce Mirabel, a routing key errada é o erro mais provável da lista — um
evento novo publicado antes de os consumidores existirem, uma chave
digitada com uma letra a mais. Enquanto o produtor não usar `mandatory`,
a proteção contra ele está em outro lugar: uma fila `auditoria.tudo`
ligada por `#`, como a do capítulo sobre exchanges, garante que **toda**
mensagem tenha pelo menos um destino — e o painel dela mostra o que foi
publicado com chave que ninguém mais escuta.
:::

## E quando o publish não é confirmado?

Com confirms, `publish()` pode terminar de três jeitos: confirmado,
recusado (`PublishNotConfirmedException`) ou sem resposta — o broker
fora, a rede caída, as novas tentativas esgotadas (`AMQPIOException` ou
`AMQPTimeoutException`). Os dois últimos chegam ao checkout como exceção,
e o checkout precisa decidir o que fazer com um pedido **já gravado e já
cobrado** cujo evento não saiu.

As opções honestas são poucas:

| O checkout... | Consequência |
|---|---|
| devolve erro ao cliente | o cliente foi cobrado e vê erro — o 40117 de novo |
| devolve sucesso e registra num log | alguém precisa ler o log e publicar à mão |
| devolve sucesso e guarda o evento para publicar depois | o pedido é atendido quando o broker voltar |

Tabela: Só a última trata o broker fora do ar como a SEFAZ fora do ar: um
atraso, não um erro.

A terceira linha é a certa, e ela esbarra no problema do último exercício
do capítulo @cap:mirabel-dentro-do-laravel: guardar o evento "para depois"
num lugar que não seja o broker, e que sobreviva ao mesmo que o pedido
sobrevive.
O único lugar com essa propriedade, no checkout, é o próprio banco de
dados.

:::milestone
Você tem: `MB_RABBITMQ_PUBLISHER_CONFIRMS=true` em todo produtor; recusas
do broker virando `PublishNotConfirmedException` em vez de silêncio; o
custo medido — um milissegundo por mensagem —; uma fila de auditoria por
`#` como rede de segurança para chaves sem destino; e uma pergunta aberta:
onde guardar o evento que não pôde ser publicado.
:::

:::summary
- Sem confirms, um `publish()` sem erro só garante que os bytes saíram; o
	broker pode ter recusado a mensagem — uma fila no limite, por exemplo —
	sem ninguém saber.
- Com `MB_RABBITMQ_PUBLISHER_CONFIRMS=true`, o broker responde a cada
	publicação e a Mirabel lança `PublishNotConfirmedException` numa
	recusa.
- Confirmar custa cerca de um milissegundo por mensagem; abrir uma conexão
	por publicação custa dez vezes mais.
- Uma mensagem sem rota é confirmada e descartada; a flag `mandatory` a
	devolve ao produtor com o código 312 `NO_ROUTE`.
- Um publish que falha depois de o pedido ser gravado precisa ser guardado
	para depois, num lugar que sobreviva junto com o pedido.
:::

:::exercise level=1
Com confirms ligados, publique na fila `teste.lotada` quando ela já tem
duas mensagens, com `MB_RABBITMQ_PUBLISH_RETRIES` no padrão (3). Quanto
tempo o `publish()` leva para lançar a exceção, e por quê?

:::answer
Cerca de sete segundos: a Mirabel trata a recusa como falha e tenta de
novo três vezes, esperando 1, 2 e 4 segundos entre as tentativas. As
quatro são recusadas — a fila continua cheia —, e a exceção sai no fim.

Para uma recusa por fila cheia, tentar de novo em segundos raramente
ajuda: a fila não esvazia tão rápido. É um caso a considerar ao escolher
o limite de uma fila e o número de novas tentativas do produtor que
publica nela.
:::

:::exercise level=2
A Denise pediu que eventos de pedidos da loja física, que ainda não têm
consumidor nenhum, comecem a ser publicados já, "para quando a expedição
estiver pronta". Com a topologia da Doce Mirabel, o que acontece com esses
eventos até lá, e o que você proporia?

:::answer
Com a fila `auditoria.tudo` ligada por `#`, eles chegam lá — e só lá.
Nenhuma fila de trabalho os recebe; quando o consumidor da expedição for
criado, a fila dele começa vazia, e os eventos publicados antes estão
somente na auditoria, que não foi feita para ser reprocessada.

A proposta é criar **agora** a fila da expedição para esses eventos, com o
binding certo e sem consumidor. Ela acumula tudo o que for publicado, e o
consumidor, quando existir, começa do primeiro evento. O custo é espaço em
disco no broker e uma fila crescendo no painel — que precisa de um limite,
ou de alguém de olho nela.
:::
