---
title: "Conexão, canal e a primeira mensagem"
number: 4
slug: conexao-canal-e-a-primeira-mensagem
part: p2
kicker: "Cinco booleanos seguidos numa linha, e cada um deles decide se o pedido sobrevive."
goal: >-
  Escrever com php-amqplib um produtor e um consumidor que trocam pedidos,
  distinguir conexão de canal, ler os argumentos de queue_declare e
  basic_consume, e reconhecer os dois primeiros erros que todo mundo
  encontra: a fila declarada de outro jeito e o broker que não responde.
---

O painel do capítulo @cap:o-que-vamos-construir provou que o caminho existe:
a mensagem entra pelo *default exchange*, espera na fila e sai quando
alguém a pede. Agora o mesmo caminho vai ser feito por dois programas PHP,
e o painel vira o lugar onde se confere o que eles fizeram.

O código deste capítulo é de propósito o mais cru possível. Ele usa a
`php-amqplib`, a biblioteca PHP que implementa o protocolo AMQP 0-9-1 — a
língua nativa do RabbitMQ — e não esconde nada. Cada argumento é visível, e
alguns deles são booleanos sem nome que decidem se o pedido sobrevive a um
restart.

## O projeto

Na pasta `doce-mirabel/`, ao lado do `docker-compose.yml`, instale a
biblioteca com o Composer:

```bash
composer require php-amqplib/php-amqplib:^3.7
```

O Composer baixa a biblioteca para a pasta `vendor/` e cria um arquivo
`vendor/autoload.php`. Incluir esse arquivo é o que faz as classes da
biblioteca ficarem disponíveis no seu script, sem um `require` para cada
uma. `^3.7` quer dizer "qualquer versão 3 a partir da 3.7".

:::pitfall
Se o `composer require` reclamar de `ext-sockets` ou `ext-mbstring`, a
biblioteca não vai instalar: ela exige as duas extensões. Volte à seção "O
que você precisa" da abertura e ligue-as no `php.ini`.
:::

## Conexão e canal

Um programa fala com o RabbitMQ por uma **conexão**: um socket TCP aberto
com o broker, com usuário, senha e um aperto de mão no começo. Abrir uma
conexão custa alguns milissegundos e alguma memória no broker — pouco para
um programa, muito se cada requisição da loja abrir e fechar a sua.

Dentro de uma conexão, o trabalho acontece em **canais**. Um canal é uma
conversa independente que viaja pelo mesmo socket: dá para ter vários
numa conexão só, cada um publicando ou consumindo por conta própria. Quase
toda operação do AMQP — declarar fila, publicar, consumir, confirmar — é
feita num canal, não na conexão.

:::term Canal
Uma conexão lógica dentro de uma conexão TCP. Os canais compartilham o
socket, mas têm estado próprio, e um erro de protocolo fecha **o canal**,
não a conexão inteira. É por isso que existem: para que várias conversas
dividam um socket sem que o erro de uma derrube as outras.
:::

A analogia útil é a de uma linha telefônica com várias ligações em espera:
a linha é a conexão, cada ligação é um canal. Para os programas deste
capítulo basta um canal por conexão; o número de canais só passa a
importar quando um mesmo processo publica e consome ao mesmo tempo.

## O produtor

```php title="produtor.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();

$canal->queue_declare('fiscal.pedidos', false, true, false, false);

$pedido = [
    'pedido' => (int) $argv[1],
    'produto' => 'geleia de ameixa',
    'quantidade' => 2,
];
$mensagem = new AMQPMessage(json_encode($pedido), [
    'content_type' => 'application/json',
    'delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT,
]);

$canal->basic_publish($mensagem, '', 'fiscal.pedidos');
echo "publicado: pedido {$pedido['pedido']}", PHP_EOL;

$canal->close();
$conexao->close();
```

As linhas 7 e 8 usam `use` para poder escrever `AMQPStreamConnection` em
vez do nome completo da classe, com o namespace inteiro na frente. As
linhas 10 a 13 abrem a conexão — host, porta, usuário, senha — e, dentro
dela, um canal.

A linha 15 é a mais importante do arquivo, e a menos legível.

:::anatomy
lang: php
title: "Cinco argumentos, quatro deles booleanos"
code: |
  $canal->queue_declare(
      'fiscal.pedidos', // nome da fila
      false,            // passive
      true,             // durable
      false,            // exclusive
      false,            // auto_delete
  );
notes:
  - { line: 2, text: "O nome. Declarar uma fila que já existe não cria outra: confere que a existente é igual." }
  - { line: 3, text: "passive = true só pergunta se a fila existe, sem criá-la. Aqui, false: crie se não existir." }
  - { line: 4, text: "durable = true: a fila sobrevive a um restart do broker. O pedido também precisa ser persistente." }
  - { line: 5, text: "exclusive = true prende a fila a esta conexão e a apaga quando ela fecha. Não para pedidos." }
  - { line: 6, text: "auto_delete = true apaga a fila quando o último consumidor sai. Também não para pedidos." }
:::

`queue_declare` é **idempotente**: rodar de novo com os mesmos argumentos
não faz nada. Por isso o produtor e o consumidor declaram a mesma fila —
quem chegar primeiro cria, o outro só confere. Nenhum dos dois precisa
saber quem subiu antes.

As linhas 17 a 25 montam a mensagem. O corpo é o pedido em JSON, e o
segundo argumento são as **propriedades**: `content_type` avisa quem lê
que aquele texto é JSON, e `delivery_mode` com a constante
`DELIVERY_MODE_PERSISTENT` pede ao broker que grave a mensagem em disco —
o oposto do *1 - Non-persistent* que o painel usa por padrão.

A linha 27 publica: a mensagem, o exchange e a **routing key**. O exchange
é `''`, o de nome vazio. A routing key é o endereço que o exchange usa para
decidir o destino, e o *default exchange* a interpreta como nome de fila.

Suba o RabbitMQ, se ele não estiver no ar, e publique dois pedidos:

```text
$ docker compose up -d
$ php produtor.php 40117
publicado: pedido 40117
$ php produtor.php 40118
publicado: pedido 40118
```

Ninguém consumiu ainda. Os dois estão esperando no broker:

```text
$ docker compose exec rabbitmq rabbitmqctl list_queues \
    name messages_ready messages_unacknowledged
Listing queues for vhost / ...
name	messages_ready	messages_unacknowledged
fiscal.pedidos	2	0
```

## O consumidor

```php title="consumidor.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();

$canal->queue_declare('fiscal.pedidos', false, true, false, false);

$emitirNota = function (AMQPMessage $mensagem): void {
    $pedido = json_decode($mensagem->getBody(), true);
    echo "emitindo NF-e do pedido {$pedido['pedido']}", PHP_EOL;
};

$canal->basic_consume(
    'fiscal.pedidos', '', false, true, false, false, $emitirNota,
);

echo 'esperando pedidos. Ctrl+C para sair.', PHP_EOL;
while ($canal->is_consuming()) {
    $canal->wait();
}
```

As linhas 17 a 20 definem uma **função anônima** — uma função sem nome,
guardada numa variável — que recebe cada mensagem. `getBody()` devolve o
corpo como texto, exatamente os bytes que o produtor mandou.

As linhas 22 a 24 registram essa função como consumidora da fila. São sete
argumentos, na ordem: a fila; um nome para este consumidor (vazio: o broker
inventa um); `no_local`, que o RabbitMQ ignora; **`no_ack`**; `exclusive`,
que impediria outros consumidores na mesma fila; `nowait`, que dispensa a
resposta do broker; e a função.

O quarto argumento merece atenção agora. Com `no_ack` igual a `true`, o
broker considera a mensagem **entregue e resolvida** no instante em que a
manda pelo socket. Ele não espera o consumidor dizer que terminou. Se o
consumidor cair com a mensagem na mão, ela não volta: o broker já a
apagou. É o jeito mais curto de consumir, e o mais perigoso.

As linhas 27 a 29 são o motor. `basic_consume` só avisa o broker de que há
um interessado; quem de fato recebe as mensagens é o `wait()`, que bloqueia
até chegar alguma coisa pelo socket e então chama a função registrada.
`is_consuming()` diz se ainda existe algum consumidor ativo no canal. É um
laço infinito de propósito: um consumidor é um processo que fica vivo.

```text
$ php consumidor.php
esperando pedidos. Ctrl+C para sair.
emitindo NF-e do pedido 40117
emitindo NF-e do pedido 40118
```

As duas notas saem na ordem de chegada, e o processo continua parado no
`wait()`. Deixe-o rodando e, em outro terminal, publique o 40119: ele
aparece na mesma hora, sem nenhum `sleep` e sem ninguém perguntar à fila se
há novidade. Isso é o consumo por **push** que a pasta de arquivos não
tinha — o broker empurra a mensagem para quem está esperando.

Com o consumidor ainda no ar, olhe o que o broker sabe dele:

```text
$ docker compose exec rabbitmq rabbitmqctl list_consumers \
    queue_name consumer_tag ack_required prefetch_count
Listing consumers in vhost / ...
queue_name	consumer_tag	ack_required	prefetch_count
fiscal.pedidos	amq.ctag-gdei986IwJjr6TltaxxsZw	false	0
```

`consumer_tag` é o nome que o broker inventou. `ack_required` em `false` é
o `no_ack` visto do lado do servidor: ele não espera confirmação nenhuma.
No painel, as abas **Connections** e **Channels** mostram uma linha cada,
e a fila `fiscal.pedidos` mostra **1** na coluna *Consumers*.

## Quebrar de propósito

Dois erros aparecem na primeira semana de qualquer pessoa com RabbitMQ.
Vale provocá-los agora, com calma, em vez de encontrá-los numa sexta à
noite.

### A fila que já existe de outro jeito

No `produtor.php`, troque o terceiro argumento de `queue_declare` de
`true` para `false` — como se alguém tivesse decidido que a fila não
precisa ser durável — e publique:

```text
$ php produtor.php 40119
PHP Fatal error:  Uncaught
PhpAmqpLib\Exception\AMQPProtocolChannelException:
PRECONDITION_FAILED - inequivalent arg 'durable' for queue
'fiscal.pedidos' in vhost '/': received 'false' but current is 'true'
```

Leia a mensagem inteira, porque ela diz tudo: o argumento `durable` da fila
`fiscal.pedidos` não bate — o programa mandou `false`, a fila existente é
`true`. Declarar uma fila **não altera** a fila que já existe; é uma
afirmação — "a fila é assim" — e o broker recusa uma afirmação falsa.

O código de erro é o **406**, `PRECONDITION_FAILED`, e ele fecha **o
canal**. Qualquer operação seguinte naquele canal falha. É o comportamento
que o termo canal prometeu: o erro não derruba a conexão, mas aquela
conversa acabou.

:::key
Uma fila, depois de criada, não muda de configuração pela declaração.
Mudar `durable`, os argumentos ou o tipo de uma fila existente exige
apagá-la e criá-la de novo — com as mensagens que estiverem nela. Por isso
a configuração de uma fila é decidida uma vez, com calma, e escrita num
lugar só.
:::

Desfaça a mudança antes de seguir.

### O broker que não está lá

Pare o RabbitMQ e rode o produtor:

```text
$ docker compose stop rabbitmq
$ php produtor.php 40120
PHP Fatal error:  Uncaught PhpAmqpLib\Exception\AMQPIOException:
stream_socket_client(): Unable to connect to tcp://localhost:5672
(Connection refused)
```

`AMQPIOException` é a família de erros de rede da biblioteca: não havia
ninguém escutando na porta 5672. No Windows, o texto entre parênteses vem
traduzido e mais longo, mas a classe da exceção é a mesma.

Repare no que isso significa para o checkout. O RabbitMQ tirou a SEFAZ do
caminho do cliente e se pôs no lugar dela: se o **broker** cair, publicar
falha do mesmo jeito que a nota falhava. A diferença é que agora existe
uma dependência só, que você controla, em vez de sete de sete empresas.
Ela ainda precisa de cuidado.

Suba o broker de novo com `docker compose start rabbitmq`.

:::story Quinhentos pedidos
O Kaique gostou do produtor e quis ver a fila encher. Escreveu um laço no
terminal que chamava `php produtor.php` quinhentas vezes.

— Olha — disse ele, virando a tela. — Quinhentos em quarenta segundos.

A Júlia olhou o gráfico da aba **Connections** no painel. Tinha um serrote:
sobe uma, desce uma, sobe uma, desce uma.

— Cada pedido abriu uma conexão, fez o aperto de mão, publicou e fechou.

— E daí? Funcionou.

— Funcionou. Na Black Friday, cada clique no checkout vai fazer isso. Às
dez da manhã, com a collab da Tia Bia, são uns trinta por segundo.

O Kaique fez a conta no verso de uma etiqueta.

— Então o RabbitMQ vai passar o dia abrindo e fechando porta.

— Vai passar o dia cumprimentando gente que vai embora na mesma frase.
:::

A observação da Júlia não pede mudança agora — um produtor que roda uma
vez por requisição e fecha a conexão é correto e é o ponto de partida mais
seguro. Mas ela deixa registrado um custo real: a conexão é cara, e um
processo que publica muito deve abrir uma e reaproveitá-la.

:::milestone
Você tem: `produtor.php`, que declara a fila durável `fiscal.pedidos` e
publica um pedido persistente pelo *default exchange*, e `consumidor.php`,
que recebe pedidos por push e emite a nota — com `no_ack` ligado, o que
quer dizer que um consumidor que cai perde o que tinha na mão.
:::

:::summary
- A `php-amqplib` fala AMQP 0-9-1 sem esconder nada; instala com
	`composer require php-amqplib/php-amqplib` e exige `ext-sockets` e
	`ext-mbstring`.
- Conexão é o socket TCP, cara de abrir; canal é uma conversa dentro dela, e
	um erro de protocolo fecha o canal, não a conexão.
- `queue_declare` é idempotente e é uma afirmação: se a fila existe com
	outra configuração, o broker responde 406 `PRECONDITION_FAILED`.
- Publicar é mandar corpo, propriedades, exchange e routing key; no *default
	exchange*, a routing key é o nome da fila.
- `basic_consume` registra a função; `wait()` recebe por push. Com `no_ack`
	em `true`, o broker esquece a mensagem assim que a entrega.
:::

:::exercise level=1
Rode dois `consumidor.php` em dois terminais e publique seis pedidos, do
40121 ao 40126. Quais pedidos cada consumidor recebe? Confira no painel
quantos consumidores a fila tem.

:::answer
Os pedidos se alternam entre os dois: um consumidor recebe 40121, 40123 e
40125; o outro, 40122, 40124 e 40126. O RabbitMQ entrega cada mensagem de
uma fila a **um** consumidor só, revezando entre os que estão conectados —
é a distribuição em rodízio, ou *round-robin*.

É a resposta ao segundo defeito da pasta de arquivos: dois consumidores
nunca recebem o mesmo pedido. A fila mostra **2** na coluna *Consumers*.
:::

:::exercise level=2
Mude o `produtor.php` para abrir **uma** conexão e publicar, num laço, os
pedidos de 1 a 500, fechando a conexão só no fim. Meça as duas versões com
`time` (no Linux e no macOS) ou `Measure-Command` (no PowerShell) e explique
a diferença.

:::answer
A versão com laço fica assim, trocando as linhas 17 a 28:

```php
for ($numero = 1; $numero <= 500; $numero++) {
    $pedido = [
        'pedido' => $numero,
        'produto' => 'geleia de ameixa',
        'quantidade' => 2,
    ];
    $canal->basic_publish(new AMQPMessage(json_encode($pedido), [
        'content_type' => 'application/json',
        'delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT,
    ]), '', 'fiscal.pedidos');
}
```

Ela termina em uma fração de segundo; quinhentas execuções de
`php produtor.php` levam dezenas de segundos. Quase todo o tempo da
primeira versão não é publicar: é iniciar o PHP, abrir o socket, autenticar
e fechar, quinhentas vezes. Publicar uma mensagem num canal aberto custa
microssegundos.

O número exato depende da máquina, e é por isso que o exercício pede para
medir. A conclusão não depende: para volume, a conexão é aberta uma vez e
reaproveitada.
:::
