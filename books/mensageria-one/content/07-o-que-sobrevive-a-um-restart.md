---
title: "O que sobrevive a um restart"
number: 7
slug: o-que-sobrevive-a-um-restart
part: p2
kicker: "A fila voltou do restart inteira, com o nome certo e os bindings no lugar. Só faltava o pedido dentro dela."
goal: >-
  Separar durabilidade da fila de persistência da mensagem, reiniciar o
  broker e conferir o que voltou, entender por que o RabbitMQ 4 recusa filas
  temporárias compartilhadas, e saber o que "persistente" ainda não
  garante.
---

:::story Atualização de segurança
Na quarta-feira, a hospedagem mandou um e-mail: o servidor do RabbitMQ de
homologação ia reiniciar às 22h para uma atualização de segurança.

Na quinta de manhã, a fila `expedicao.pedidos-pagos` estava lá, com o
nome certo, o binding certo, o consumidor conectado de novo.

E vazia.

— Tinha trinta e dois pedidos de teste nela ontem às nove — disse o
Kaique. — Eu contei, porque ia testar a Zebrinha hoje.

— A fila voltou — disse Júlia. — As mensagens não.

— Mas a fila não era durável?

— Era. A fila é que era.
:::

O restart da quarta é o teste mais barato que existe para mensageria, e a
hospedagem fez de graça. O RabbitMQ guarda duas coisas diferentes — a
**definição** da fila e o **conteúdo** dela —, e cada uma tem o seu
interruptor. Ligar um e esquecer o outro dá exatamente a manhã de quinta.

## Dois interruptores

O primeiro é o terceiro argumento de `queue_declare`, o `durable`. Ele diz
se a **fila** — o nome, os argumentos, os bindings — sobrevive a um
restart do broker.

O segundo é a propriedade `delivery_mode` de **cada mensagem**. Com `2`,
persistente, o broker grava a mensagem em disco. Com `1`, transiente, ela
vive só na memória. É uma decisão de quem publica, mensagem por mensagem —
e o painel publica como `1` por padrão, como o capítulo
@cap:o-que-vamos-construir mostrou.

:::term Durável e persistente
**Durável** é uma propriedade da fila (e do exchange): a definição
sobrevive a um restart. **Persistente** é uma propriedade da mensagem: o
conteúdo é gravado em disco. Uma mensagem só sobrevive a um restart se as
duas coisas forem verdade ao mesmo tempo.
:::

## O experimento

O script abaixo tenta criar as quatro combinações — fila durável ou não,
mensagem persistente ou não — com uma mensagem em cada:

```php title="quatro-casos.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();

$persistente = AMQPMessage::DELIVERY_MODE_PERSISTENT;
$transiente = AMQPMessage::DELIVERY_MODE_NON_PERSISTENT;

$casos = [
    'teste.duravel-persistente' => [true, $persistente],
    'teste.duravel-transiente' => [true, $transiente],
    'teste.temporaria-persistente' => [false, $persistente],
    'teste.temporaria-transiente' => [false, $transiente],
];

foreach ($casos as $fila => [$duravel, $modo]) {
    $canal->queue_declare($fila, false, $duravel, false, false);
    $canal->basic_publish(
        new AMQPMessage('{"pedido":1}', ['delivery_mode' => $modo]),
        '',
        $fila,
    );
}
echo 'quatro filas, uma mensagem em cada', PHP_EOL;
```

O `foreach ($casos as $fila => [$duravel, $modo])` desmonta cada par do
array direto em duas variáveis, sem índices.

Rode:

```text
$ php quatro-casos.php
PHP Fatal error:  Uncaught
PhpAmqpLib\Exception\AMQPConnectionClosedException: INTERNAL_ERROR -
Feature `transient_nonexcl_queues` is deprecated.
By default, this feature is not permitted anymore.
```

O terceiro caso nem chegou a existir. Os dois primeiros, sim:

```text
$ docker compose exec rabbitmq rabbitmqctl list_queues \
    name durable messages
name	durable	messages
teste.duravel-persistente	true	1
teste.duravel-transiente	true	1
```

## A fila temporária que não existe mais

O erro é do RabbitMQ 4, e ele muda o que quase todo tutorial antigo
ensina. Uma fila **não durável e não exclusiva** — que qualquer conexão
pode usar e que some no restart — foi descontinuada. O broker a recusa, e
com um erro que fecha a **conexão** inteira, não só o canal.

Na prática, uma fila compartilhada que evapora num restart raramente é o
que alguém quer — e as filas replicadas, que o RabbitMQ moderno recomenda
para dado importante, só existem na versão durável. Os tutoriais escritos antes de 2024
mostram as quatro combinações como escolhas legítimas; hoje, duas delas
estão fora do cardápio.

Fila temporária continua existindo em uma forma: **exclusiva**, o quarto
argumento de `queue_declare`. Ela pertence a uma conexão e morre com ela —
útil para respostas de uma conversa só, inútil para pedidos. Para a Doce
Mirabel, toda fila é durável, e a pergunta que sobra é só a da mensagem.

## O restart

Com os dois casos válidos criados, reinicie o broker:

```text
$ docker compose restart rabbitmq
$ docker compose exec rabbitmq rabbitmqctl list_queues \
    name durable messages
name	durable	messages
teste.duravel-transiente	true	0
teste.duravel-persistente	true	1
```

As duas filas voltaram. Só uma trouxe o pedido.

| Fila | Mensagem | Depois do restart |
|---|---|---|
| durável | persistente | a fila e o pedido voltam |
| durável | transiente | a fila volta **vazia** |
| não durável, compartilhada | qualquer | recusada no RabbitMQ 4 |
| exclusiva | qualquer | morre com a conexão, antes do restart |

Tabela: Para um pedido, só existe uma linha certa.

A manhã de quinta foi a segunda linha: filas duráveis, mensagens de teste
publicadas por um script que não definia `delivery_mode` — e o padrão da
`php-amqplib`, como o do painel, é transiente.

:::pitfall
O `delivery_mode` é da **mensagem**, então basta um produtor esquecê-lo
para que só as mensagens dele sumam no restart, e as dos outros
sobrevivam. O sintoma é uma fila que volta com *menos* mensagens, não
vazia — o mais difícil de notar.
:::

## O que "persistente" ainda não garante

Persistente quer dizer que o broker **vai gravar** a mensagem em disco.
Não quer dizer que já gravou quando o `basic_publish` retornou.

O `basic_publish` da `php-amqplib` é mandar e esquecer: ele escreve os
bytes no socket e volta, sem esperar resposta nenhuma do broker. Entre o
retorno e a gravação no disco existe uma janela — curta, de milissegundos
— em que um broker que cai leva a mensagem junto, e o produtor acha que
publicou. O mesmo vale se a mensagem nem chegou a sair da máquina do
produtor.

Para a maior parte dos restarts — os planejados, como o da hospedagem —
essa janela não importa, porque o broker desliga com calma e grava o que
tem. Ela importa no dia em que o broker cai de verdade, e fechar essa
janela exige que o broker **responda** ao produtor dizendo que a mensagem
está segura. O AMQP tem esse mecanismo; o `basic_publish` puro não o usa.

:::key
Uma mensagem sobrevive a um restart planejado se a fila for durável **e**
a mensagem for persistente. Sobreviver a uma queda no meio do publish
exige mais uma coisa: o produtor esperar o broker confirmar.
:::

:::milestone
Você tem: a certeza de que as filas da fábrica são duráveis e os pedidos
são persistentes — `delivery_mode` 2 em todo `basic_publish` —, o
experimento que prova isso com um restart, e a janela entre publicar e
gravar identificada e ainda aberta.
:::

:::summary
- `durable` na fila salva a definição; `delivery_mode = 2` na mensagem
	salva o conteúdo. Só as duas juntas trazem o pedido de volta.
- O padrão da `php-amqplib` e do painel é mensagem transiente: esquecer o
	`delivery_mode` é perder mensagens no restart sem erro nenhum.
- O RabbitMQ 4 recusa filas não duráveis e não exclusivas; fila temporária
	hoje é exclusiva, presa a uma conexão.
- `basic_publish` não espera o broker gravar: ainda há uma janela em que um
	broker que cai leva a mensagem.
:::

:::exercise level=1
Apague as filas de teste pelo painel, mude o `quatro-casos.php` para
declarar só os dois casos duráveis e publique **dez** mensagens em cada,
metade persistente e metade transiente, na mesma fila. Reinicie o broker.
Quantas voltam em cada fila?

:::answer
Cinco em cada. O broker não trata a fila como um bloco: cada mensagem é
gravada ou não conforme o próprio `delivery_mode`. Uma fila durável com
mensagens misturadas volta do restart com metade delas — o sintoma
descrito no alerta acima.
:::

:::exercise level=2
Um colega sugere publicar tudo como transiente "porque é mais rápido" e
confiar que o broker quase nunca reinicia. Escreva o argumento contra em
três frases, usando o custo de cada lado.

:::answer
Gravar em disco custa pouco num broker com SSD, e o ganho de velocidade só
aparece em volumes muito maiores que os da Doce Mirabel. O broker reinicia
em toda atualização de segurança, todo upgrade de versão e todo problema
de hardware — várias vezes por ano, e às vezes sem aviso. Cada restart com
mensagens transientes apaga pedidos pagos sem deixar erro em log nenhum, e
o custo de um pedido perdido é o valor dele mais a ligação do cliente para
o SAC.
:::
