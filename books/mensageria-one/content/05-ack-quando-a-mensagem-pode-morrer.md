---
title: "Ack: quando a mensagem pode morrer"
number: 5
slug: ack-quando-a-mensagem-pode-morrer
part: p2
kicker: "Cinco pedidos publicados, um consumidor derrubado no segundo, e a fila zerada como se nada tivesse acontecido."
goal: >-
  Ver uma mensagem sumir com no_ack, trocar para confirmação manual, ler as
  colunas Ready e Unacked, reconhecer uma reentrega pela flag redelivered e
  evitar os dois defeitos do ack manual: esquecer de confirmar e devolver
  para a fila para sempre.
---

:::story Cadê os quatro?
A Júlia deixou o `consumidor.php` rodando a manhã inteira no notebook,
consumindo a fila `fiscal.pedidos` de teste. Às onze, o Windows resolveu
reiniciar para instalar uma atualização.

Quando ela voltou do café, o Kaique estava olhando o painel.

— Você publicou cinco pedidos de teste às onze, né?

— Publiquei.

— O consumidor só imprimiu um. E a fila está vazia.

— Vazia como?

— Zero. *Ready* zero, *Unacked* zero. Os outros quatro não estão em lugar
nenhum.

A Júlia abriu o terminal. A última linha era `emitindo NF-e do pedido
40118`. Nada de "autorizada".

— O 40118 estava no meio — disse ela. — E os outros três nem começaram.

— Então o RabbitMQ perdeu?

— O RabbitMQ fez exatamente o que eu pedi.
:::

O `consumidor.php` do capítulo @cap:conexao-canal-e-a-primeira-mensagem
consome com `no_ack` ligado: o broker considera cada mensagem resolvida no
instante em que a manda pelo socket. Num dia sem quedas, a diferença é
invisível. Com uma reinicialização no meio, ela é a diferença entre um
pedido atrasado e um pedido que não existe mais.

Este capítulo reproduz o sumiço, conserta, e depois mostra os dois jeitos
de errar com o conserto.

## Preparando a bancada

Os experimentos daqui em diante precisam publicar vários pedidos de uma
vez e abrir a mesma conexão em vários scripts. A conexão vai para um
arquivo próprio:

```php title="conexao.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();
$canal->queue_declare('fiscal.pedidos', false, true, false, false);
```

E um publicador de lote, que abre a conexão uma vez só:

```php title="lote.php" numbered
<?php

declare(strict_types=1);

use PhpAmqpLib\Message\AMQPMessage;

require __DIR__ . '/conexao.php';

$primeiro = (int) $argv[1];
$quantos = (int) ($argv[2] ?? 1);

for ($numero = $primeiro; $numero < $primeiro + $quantos; $numero++) {
    $corpo = json_encode(['pedido' => $numero, 'quantidade' => 2]);
    $canal->basic_publish(new AMQPMessage($corpo, [
        'content_type' => 'application/json',
        'delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT,
    ]), '', 'fiscal.pedidos');
}
echo "pedidos publicados: {$quantos}", PHP_EOL;

$canal->close();
$conexao->close();
```

`require __DIR__ . '/conexao.php'` executa o outro arquivo como se ele
estivesse escrito ali, e as variáveis `$conexao` e `$canal` ficam
disponíveis. `php lote.php 40117 5` publica do 40117 ao 40121.

O consumidor agora demora, como a SEFAZ demora, e aceita um argumento que
liga a confirmação manual:

```php title="consumidor-lento.php" numbered
<?php

declare(strict_types=1);

use PhpAmqpLib\Message\AMQPMessage;

require __DIR__ . '/conexao.php';

$comAck = ($argv[1] ?? '') === 'ack';

$emitirNota = function (AMQPMessage $mensagem) use ($comAck): void {
    $pedido = json_decode($mensagem->getBody(), true);
    $numero = $pedido['pedido'];
    $de_novo = $mensagem->isRedelivered() ? ' (de novo)' : '';
    echo "emitindo NF-e do pedido {$numero}{$de_novo}", PHP_EOL;
    sleep(2); // a SEFAZ num dia bom
    echo "  nota do {$pedido['pedido']} autorizada", PHP_EOL;

    if ($comAck) {
        $mensagem->ack();
    }
};

$canal->basic_consume(
    'fiscal.pedidos', '', false, !$comAck, false, false, $emitirNota,
);

while ($canal->is_consuming()) {
    $canal->wait();
}
```

Três detalhes novos. O `use ($comAck)` na linha 11 deixa a função anônima
enxergar uma variável de fora dela — sem ele, `$comAck` não existiria lá
dentro. `isRedelivered()` diz se o broker já tinha entregado esta mensagem
antes; ele volta daqui a pouco. E o quarto argumento de `basic_consume`, o
`no_ack`, agora é `!$comAck`: sem o argumento `ack`, o comportamento é o
do capítulo anterior.

## O sumiço, reproduzido

Publique cinco pedidos e confira que estão na fila:

```text
$ php lote.php 40117 5
pedidos publicados: 5
$ docker compose exec rabbitmq rabbitmqctl list_queues \
    name messages_ready messages_unacknowledged
name	messages_ready	messages_unacknowledged
fiscal.pedidos	5	0
```

Ligue o consumidor **sem** ack e, depois que a segunda nota começar,
derrube-o com `Ctrl+C` — o mesmo efeito de uma reinicialização, de um
deploy ou de falta de memória:

```text
$ php consumidor-lento.php
emitindo NF-e do pedido 40117
  nota do 40117 autorizada
emitindo NF-e do pedido 40118
^C
```

E a fila:

```text
fiscal.pedidos	0	0
```

Zero pronto, zero pendente. O 40118 foi interrompido no meio e os pedidos
40119, 40120 e 40121 **nunca começaram** — e sumiram também.

A primeira surpresa é essa: por que os três que nem começaram? Porque o
RabbitMQ não entrega uma mensagem de cada vez. Um consumidor registrado
recebe tudo o que o broker conseguir mandar pelo socket, e as mensagens
ficam num buffer do processo, na memória, esperando a vez. Com `no_ack`,
ao mandar, o broker apagou as cinco da fila. Quando o processo morreu, o
buffer morreu junto.

:::key
Com `no_ack`, a mensagem sai da fila quando **chega** ao consumidor, não
quando o trabalho **termina**. Tudo o que estiver em trânsito ou esperando
na memória do consumidor se perde se ele cair — e, por padrão, isso pode
ser a fila inteira.
:::

## O ack manual

A confirmação manual inverte a responsabilidade: o broker entrega, mas
mantém a mensagem guardada até o consumidor dizer, explicitamente, que
terminou. Esse "terminei" é o **ack** — a mesma palavra da tabela da pasta
de arquivos, agora com o protocolo por trás.

:::term Ack
*Acknowledgement*, confirmação. O consumidor manda ao broker a mensagem
`basic.ack` com o número de entrega daquela mensagem, e só então o broker
a apaga. Em `php-amqplib`, é `$mensagem->ack()`. Enquanto o ack não chega,
a mensagem fica **Unacked**: entregue, mas não resolvida.
:::

Publique os cinco de novo e ligue o consumidor com `ack`. Enquanto a
primeira nota está sendo emitida, olhe a fila:

```text
$ php lote.php 40117 5
$ php consumidor-lento.php ack
emitindo NF-e do pedido 40117
```

```text
fiscal.pedidos	0	5
```

Zero prontas, **cinco Unacked**. As cinco já estão no buffer do consumidor,
exatamente como antes — mas agora o broker ainda as guarda. Derrube o
consumidor no segundo pedido:

```text
  nota do 40117 autorizada
emitindo NF-e do pedido 40118
^C
```

```text
fiscal.pedidos	4	0
```

Quatro de volta em *Ready*. Quando a conexão cai, o broker devolve para a
fila tudo o que estava entregue e sem ack. Ligue de novo:

```text
$ php consumidor-lento.php ack
emitindo NF-e do pedido 40118 (de novo)
  nota do 40118 autorizada
emitindo NF-e do pedido 40119 (de novo)
  nota do 40119 autorizada
```

Nenhum pedido perdido. E a flag `redelivered` conta uma história
importante: ela diz que o broker **já tinha entregado** aquela mensagem a
alguém, não que alguém **já tinha processado**. O 40119 nunca começou e
também vem marcado, porque estava no buffer do consumidor que morreu.

:::warning
O 40118 foi interrompido **no meio** da emissão. Se a SEFAZ tivesse
autorizado a nota um instante antes do `Ctrl+C`, a segunda entrega
emitiria a nota **de novo**. O ack manual troca "perder" por "repetir" — é
a escolha certa para um pedido, mas repetir também tem custo, e o
consumidor precisa estar preparado para receber a mesma mensagem duas
vezes.
:::

Essa troca tem nome: entrega **pelo menos uma vez**, ou *at-least-once*.
Com `no_ack`, a entrega é **no máximo uma vez** — nunca repete, às vezes
perde. Não existe uma terceira opção grátis. A que quase todo sistema de
pedidos quer, "exatamente uma vez", não é uma configuração do broker: é
at-least-once mais um consumidor que reconhece a repetição, e é trabalho
seu.

## O primeiro jeito de errar: esquecer

O ack manual tem um contrato: **toda** mensagem recebida precisa de uma
resposta. Se o código tem um caminho que não chama `ack()` — um `return`
no meio, um `if` sem `else` —, aquela mensagem fica Unacked enquanto a
conexão viver.

O efeito é traiçoeiro porque nada quebra. O consumidor continua rodando, a
fila mostra *Ready* zero, e a coluna *Unacked* só cresce. Nada é
reprocessado até alguém reiniciar o consumidor — e aí tudo volta de uma
vez, com a flag de reentrega. É a mensagem que "some por algumas horas e
reaparece", o defeito mais difícil de explicar numa reunião.

:::pitfall
*Unacked* crescendo e *Ready* parado em zero, com o consumidor no ar e sem
erro no log, quase sempre é ack esquecido. A confirmação é: reiniciar o
consumidor faz o número voltar para *Ready*.
:::

## O segundo jeito de errar: devolver para sempre

Além do `ack()`, a mensagem tem mais duas respostas. `nack()` diz "não
consegui" e `reject()` diz praticamente o mesmo, para uma mensagem só. As
duas aceitam um argumento `requeue`: com `true`, a mensagem volta para a
fila; com `false`, ela é descartada.

Devolver para a fila parece a resposta natural a uma falha. Veja o que
acontece com um pedido que **nunca** vai dar certo — um CEP que não existe,
que a SEFAZ vai recusar hoje, amanhã e na Black Friday:

```php title="consumidor-teimoso.php" numbered
<?php

declare(strict_types=1);

use PhpAmqpLib\Exception\AMQPTimeoutException;
use PhpAmqpLib\Message\AMQPMessage;

require __DIR__ . '/conexao.php';

$tentativas = 0;

$emitirNota = function (AMQPMessage $m) use (&$tentativas): void {
    $pedido = json_decode($m->getBody(), true);
    $tentativas++;

    if ($pedido['pedido'] === 40117) {   // CEP que não existe
        $m->nack(true);                  // devolve para a fila
        return;
    }
    $m->ack();
};

$canal->basic_consume(
    'fiscal.pedidos', '', false, false, false, false, $emitirNota,
);

$fim = time() + 5;
while (time() < $fim) {
    try {
        $canal->wait(null, false, 1);
    } catch (AMQPTimeoutException) {
        // nenhuma mensagem em 1 segundo; confere o relógio
    }
}
echo "entregas em 5 segundos: {$tentativas}", PHP_EOL;
```

O `&` em `use (&$tentativas)` passa a variável **por referência**: a função
altera a própria `$tentativas` de fora, e não uma cópia. O terceiro
argumento de `wait()` é um tempo máximo em segundos; quando ele passa sem
mensagem, a biblioteca lança `AMQPTimeoutException`, e o `catch` só deixa o
laço conferir o relógio.

```text
$ php lote.php 40117 1
$ php consumidor-teimoso.php
entregas em 5 segundos: 9088
```

Nove mil entregas da **mesma** mensagem em cinco segundos, com a CPU do
consumidor e a do broker a cem por cento. A mensagem volta para a cabeça da
fila, é entregue de novo imediatamente, falha de novo — e, se houver outros
pedidos atrás dela, eles disputam a vez com um laço que nunca termina.

`requeue` serve para uma falha que **passa sozinha em milissegundos**, o
que quase nunca é o caso. A SEFAZ fora do ar não volta em milissegundos, e
um CEP inválido não volta nunca. O que falta são duas coisas: esperar antes
de tentar de novo, e desistir depois de algumas tentativas. O protocolo
tem as peças para as duas, e nenhuma delas é o `requeue`.

:::story A nota do Seu Norberto
No fim da tarde, a Júlia explicou o experimento ao Seu Norberto, porque
achou que ele ia gostar de saber que o pedido não se perde mais.

— Então, se o programa cai no meio, a nota é emitida de novo.

— Pode ser emitida de novo — disse Júlia. — Se ele cair depois da SEFAZ
autorizar e antes de confirmar.

— E a senhora acha isso bom?

— Acho melhor que perder o pedido.

O Seu Norberto tirou os óculos.

— Moça, duas notas para a mesma venda é imposto em dobro e uma carta de
correção. Uma venda sem nota é multa. Eu não escolho entre as duas. Eu
quero uma.

O Kaique anotou no verso de uma etiqueta: *pelo menos uma vez ≠ uma vez*.
:::

:::milestone
Você tem: um consumidor com ack manual que não perde pedido quando cai —
ele pode repetir. `lote.php` para publicar vários pedidos, `conexao.php`
compartilhado, e duas armadilhas conhecidas: ack esquecido e `requeue` em
laço.
:::

:::summary
- Com `no_ack`, a mensagem sai da fila ao ser entregue; um consumidor que
	cai perde o que estava processando e tudo o que estava no buffer.
- Com ack manual, a mensagem fica *Unacked* até `$mensagem->ack()`; se a
	conexão cai, ela volta para *Ready* e é entregue de novo com
	`redelivered` ligado.
- Isso é entrega at-least-once: nunca perde, às vezes repete. Exatamente
	uma vez é at-least-once mais um consumidor que reconhece a repetição.
- Ack esquecido aparece como *Unacked* crescendo sem erro no log.
- `nack` ou `reject` com `requeue` numa falha permanente viram um laço de
	milhares de entregas por segundo.
:::

:::exercise level=1
No `consumidor-lento.php` com `ack`, mova a linha `$mensagem->ack()` para
**antes** do `sleep(2)`. Publique cinco pedidos, derrube o consumidor no
segundo, e explique o que mudou.

:::answer
O 40118 é confirmado antes de a nota ser emitida. Quando o consumidor cai
durante o `sleep`, o broker já apagou o 40118: ele **não volta**, e a nota
dele nunca é emitida. Os outros três, que estavam no buffer sem ack, voltam
normalmente.

Confirmar antes do trabalho é `no_ack` com passos a mais: a mensagem pode
se perder na janela entre o ack e o fim do trabalho. O ack vai **depois**
do efeito que ele confirma.
:::

:::exercise level=2
Um colega propõe resolver o laço do `consumidor-teimoso.php` com
`$mensagem->nack(false)` — sem requeue — para pedidos com CEP inválido.
Qual é o problema, e o que você precisaria saber antes de aceitar?

:::answer
Sem requeue, e sem nenhuma configuração a mais na fila, a mensagem é
**descartada**. O laço acaba, mas o pedido com CEP errado some sem deixar
rastro: ninguém corrige o endereço, o cliente não recebe e o SAC só fica
sabendo quando ele ligar.

Antes de aceitar, é preciso saber para onde uma mensagem recusada vai. O
RabbitMQ permite configurar a fila para que mensagens recusadas sem requeue
sejam encaminhadas a outro lugar, em vez de descartadas. Sem isso
configurado, `nack(false)` é uma lixeira.
:::
