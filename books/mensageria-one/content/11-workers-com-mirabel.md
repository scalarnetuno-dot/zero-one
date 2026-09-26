---
title: "Workers com Mirabel"
number: 11
slug: workers-com-mirabel
part: p3
kicker: "Um método, duas propriedades, e três filas aparecem no painel sem ninguém ter pedido a terceira."
goal: >-
  Escrever um consumidor como uma classe que estende Worker, entender o
  contrato do handle (retornou, lançou, rejeitou), reconhecer a topologia
  que o worker declara sozinho e ler, na fila de erro, por que uma mensagem
  foi parar lá.
---

:::story Três filas
O Kaique escreveu o primeiro worker da Mirabel sozinho, na hora do almoço,
copiando do README. Quando a Júlia voltou, ele estava olhando o painel com
a testa franzida.

— Eu pedi uma fila.

— E?

— Apareceram três. `fiscal.pedidos-pagos`, `fiscal.pedidos-pagos.retry` e
`fiscal.pedidos-pagos.error`.

— E dois exchanges a mais — disse a Júlia, abrindo a aba **Exchanges**.

— Isso é normal?

— É a parte que a gente ia escrever na mão na semana que vem.

O Kaique olhou para a fila `.error`. Tinha uma mensagem.

— E essa aqui? Eu não publiquei nada com erro.

— Você publicou o pedido do CEP 00000-000 para testar?

— Publiquei.

— Então publicou com erro.
:::

O produtor da Doce Mirabel já é uma classe de três linhas, desde o
capítulo @cap:por-que-uma-biblioteca. O consumidor é o lado em que a Parte
2 mais escreveu — ack, prefetch, laço de `wait()`, o que fazer quando cai —
e é o lado em que a biblioteca mais tira do caminho. Também é o lado em
que ela mais decide por você, e cada decisão precisa ficar à vista.

## Um worker

```php title="src/Workers/EmitirNotaFiscal.php" numbered
<?php

declare(strict_types=1);

namespace DoceMirabel\Workers;

use Mirabel\RabbitMQ\Envelope;
use Mirabel\RabbitMQ\Worker;

final class EmitirNotaFiscal extends Worker
{
    public static string $queue = 'fiscal.pedidos-pagos';
    public static array $routingKeys = ['pedido.pago'];

    public function handle(Envelope $envelope): void
    {
        $pedido = $envelope->body['pedido'];

        if ($envelope->body['entrega']['cep'] === '00000-000') {
            throw new \RuntimeException("CEP inválido: {$pedido}");
        }

        echo "NF-e do pedido {$pedido} emitida", PHP_EOL;
    }
}
```

Duas propriedades estáticas dizem **de onde** o worker consome: a fila e
as routing keys que ela escuta no exchange de `MB_RABBITMQ_EXCHANGE`. Um
método diz **o que** ele faz com cada mensagem. O `Envelope` entrega o
corpo já decodificado do JSON em `$envelope->body`, como array.

Para rodar, um script de três linhas:

```php title="consumir.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use DoceMirabel\Workers\EmitirNotaFiscal;

echo 'fiscal esperando pedidos pagos. Ctrl+C para sair.', PHP_EOL;
(new EmitirNotaFiscal())->subscribe();
```

`subscribe()` não retorna: ele conecta, declara, consome e fica no laço,
exatamente como o `consumidor.php` da Parte 2.

O `publicar.php` agora aceita um CEP como segundo argumento, para
simular o endereço errado:

```php title="publicar.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use DoceMirabel\Eventos\PedidoPago;

[, $numero, $cep] = $argv + [2 => '37701-000'];

(new PedidoPago([
    'pedido' => (int) $numero,
    'total_centavos' => 8990,
    'entrega' => ['cep' => $cep],
]))->publish();
echo "pedido.pago publicado: {$numero}", PHP_EOL;
```

O `+` entre arrays preenche as posições que faltam: se o terminal não
passou o CEP, a posição 2 vem do array da direita.

Ligue o worker e, em outro terminal, publique um pedido bom e um ruim:

```text
$ php publicar.php 40117
$ php publicar.php 40118 00000-000
```

```text
fiscal esperando pedidos pagos. Ctrl+C para sair.
NF-e do pedido 40117 emitida
```

O 40117 saiu. O 40118 não aparece na saída do worker, e não voltou para a
fila: ele está na terceira fila que o Kaique não pediu.

## O contrato do handle

O que o worker faz depois do `handle()` depende de **como** o método
terminou. É o contrato inteiro da biblioteca, e cabe numa tabela:

| O `handle()`... | O worker faz |
|---|---|
| retorna normalmente | ack |
| lança exceção | tenta de novo mais tarde; na última tentativa, fila `.error` |
| chama `$envelope->reject()` | fila `.error` na hora, sem gastar tentativas |
| chama `$envelope->nack()` | o mesmo que lançar exceção |
| recebe um corpo que não é JSON | fila `.error` na hora; o `handle()` nem roda |

Tabela: O ack acontece **depois** do método, nunca antes — a regra que o
capítulo sobre ack levou uma página para provar.

A primeira linha é a mais importante e a menos visível: não existe
`ack()` no `handle()` do fiscal. Retornar **é** confirmar. Não há como
esquecer o ack num caminho do código, porque não há ack para esquecer — o
defeito da coluna *Unacked* crescendo não tem onde acontecer.

A segunda linha diz "tenta de novo mais tarde", e o 40118 não foi tentado
de novo. É porque o fiscal não disse **quantas** tentativas quer. Sem
configuração, o padrão é uma tentativa só: a primeira exceção já é a
última, e a mensagem vai direto para `.error`.

`reject()` e exceção parecem a mesma coisa e não são. A exceção diz "não
deu **agora**" — a SEFAZ caiu, o banco estava travado —, e tentar de novo
pode dar certo. O `reject()` diz "isto **nunca** vai dar certo" — um CEP
que não existe, um produto que saiu de linha —, e cada tentativa a mais
seria só um atraso até o mesmo erro.

```php
if (!$this->cepExiste($envelope->body['entrega']['cep'])) {
    $envelope->reject();
    return;
}
```

## A topologia que ninguém pediu

Na primeira vez que `subscribe()` roda, o worker declara:

- o exchange principal, `doce.eventos`, do tipo `MB_RABBITMQ_EXCHANGE_TYPE`;
- a fila `fiscal.pedidos-pagos`, durável, e um binding por routing key;
- a fila `.retry`, onde as mensagens esperam entre uma tentativa e outra;
- a fila `.error`, onde param as mensagens que esgotaram as tentativas ou
	foram rejeitadas;
- dois exchanges auxiliares, `.retry` e `.error`, um para cada.

Em **Queues and Streams**, clique na fila `fiscal.pedidos-pagos`: em
*Features* aparecem os argumentos `x-dead-letter-exchange` e
`x-dead-letter-routing-key`, apontando para `fiscal.pedidos-pagos.retry`. É
por eles que a fila principal sabe para onde mandar o que der errado, sem
nenhum código do fiscal participar.

O worker declara também o **prefetch 1**, por padrão. O consumidor do
fiscal leva segundos por nota, e o capítulo @cap:a-zebrinha-e-o-prefetch
mostrou por que isso pede um de cada vez.

:::key
O worker é dono da sua fila. Ele a declara, com os bindings, a espera e o
desvio de erro, toda vez que sobe — o que significa que a fila existe a
partir do primeiro `subscribe()`, e que um evento publicado **antes**
disso, sem fila nenhuma ligada, é descartado.
:::

## Lendo a fila de erro

A fila `.error` não é uma lixeira. É uma caixa de pendências, e cada
mensagem nela chega com um bilhete. Pegue a do 40118 pelo painel, em
*Get messages*, e olhe os headers:

```text
{"pedido":40118,"total_centavos":8990,"entrega":{"cep":"00000-000"}}
  x-mirabel-attempts = 1
  x-mirabel-exception = RuntimeException: CEP inválido: 40118
  x-mirabel-failed-at = 1790379875
  x-mirabel-failure-reason = exception
```

O corpo está intacto: é exatamente o que o checkout publicou. Os headers
`x-mirabel-*` dizem o motivo (`exception`), a classe e a mensagem da
exceção, em que tentativa ela aconteceu e quando.

Agora publique algo que nem JSON é — um sistema antigo, um teste manual
pelo painel:

```text
pedido 40119, geleia
  x-mirabel-attempts = 1
  x-mirabel-exception = JsonException: Syntax error
  x-mirabel-failure-reason = poison
```

`poison` é a **mensagem envenenada**: uma que não pode ser lida de jeito
nenhum. O `handle()` nem foi chamado, e ela não gastou tentativa — tentar
de novo leria os mesmos bytes inválidos.

| `x-mirabel-failure-reason` | Quer dizer |
|---|---|
| `exception` | o `handle()` lançou exceção na última tentativa |
| `nack` | o `handle()` chamou `nack()` na última tentativa |
| `reject` | o `handle()` chamou `reject()` |
| `poison` | o corpo não pôde ser decodificado |

Tabela: Quem abre a fila de erro às nove da manhã lê esta coluna primeiro.

## Parando o worker

`Ctrl+C` derruba o processo. A mensagem que estava no meio do `handle()`
fica sem ack e volta para a fila quando a conexão cai — nada se perde, e
ela pode ser processada de novo, como o capítulo sobre ack avisou.

Em Linux e macOS, com a extensão `pcntl` do PHP instalada, o worker
entende os sinais `SIGTERM` e `SIGINT` — o que o `kill`, o Docker e os
supervisores de processo mandam para pedir que um programa termine — e
para **com calma**: termina a mensagem em mãos, confirma, e só então sai.
O mesmo pode ser pedido por código:

```php
$worker->stop();
```

Depois de `stop()`, o worker termina a mensagem atual e sai do
`subscribe()` em até um segundo.

:::milestone
Você tem: o worker `EmitirNotaFiscal`, que consome `pedido.pago` pela fila
`fiscal.pedidos-pagos` com prefetch 1, confirma o que der certo, desvia o
que der errado para `.error` com o motivo escrito, e para com calma quando
pedem.
:::

:::summary
- Um worker estende `Worker`, declara `$queue` e `$routingKeys` e
	implementa `handle(Envelope $envelope)`; `subscribe()` fica consumindo.
- Retornar confirma; lançar exceção ou `nack()` tenta de novo até o limite;
	`reject()` e corpo inválido vão direto para `.error`.
- Sem configuração de tentativas, a primeira falha já é a última.
- O worker declara sozinho a fila, os bindings, as filas `.retry` e
	`.error`, os exchanges auxiliares e o prefetch 1.
- Mensagens na `.error` levam `x-mirabel-failure-reason`,
	`x-mirabel-attempts` e `x-mirabel-exception`.
:::

:::exercise level=1
Mude o `handle()` do fiscal para chamar `$envelope->reject()` quando o CEP
for `00000-000`, em vez de lançar exceção. Publique o 40120 com esse CEP.
O que muda no header da mensagem na fila de erro?

:::answer
`x-mirabel-failure-reason` passa a ser `reject`, e não existe
`x-mirabel-exception`, porque nenhuma exceção foi lançada. O restante é
igual: o corpo intacto, `x-mirabel-attempts` igual a 1 e a data.

A diferença aparece quando houver tentativas configuradas: com exceção, o
pedido de CEP errado passaria por todas antes de chegar à `.error`; com
`reject()`, chega na primeira.
:::

:::exercise level=2
Escreva o worker `ImprimirEtiqueta`, da expedição, que consome
`pedido.pago` pela fila `expedicao.pedidos-pagos` e imprime
`etiqueta do pedido N`. Depois responda: com o fiscal e a expedição
rodando, quantas cópias de um `pedido.pago` existem no broker, e o que
acontece com a da expedição se o fiscal lançar exceção?

:::answer
```php title="src/Workers/ImprimirEtiqueta.php"
<?php

declare(strict_types=1);

namespace DoceMirabel\Workers;

use Mirabel\RabbitMQ\Envelope;
use Mirabel\RabbitMQ\Worker;

final class ImprimirEtiqueta extends Worker
{
    public static string $queue = 'expedicao.pedidos-pagos';
    public static array $routingKeys = ['pedido.pago'];

    public function handle(Envelope $envelope): void
    {
        $pedido = $envelope->body['pedido'];
        echo "etiqueta do pedido {$pedido}", PHP_EOL;
    }
}
```

Existem duas cópias, uma em cada fila, porque cada fila tem o seu binding
para `pedido.pago`. Elas são independentes: se o fiscal lançar exceção, a
cópia **dele** vai para `fiscal.pedidos-pagos.error`, e a da expedição é
impressa normalmente. A etiqueta sai mesmo que a nota não tenha saído — e
se isso é aceitável é uma pergunta para a Denise e o Seu Norberto, não
para o broker.
:::
