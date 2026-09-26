---
title: "Exchanges e bindings"
number: 6
slug: exchanges-e-bindings
part: p2
kicker: "Um pedido pago interessa a quatro setores, e o checkout não precisa saber o nome de nenhum deles."
goal: >-
  Publicar num exchange próprio em vez do default, ligar filas a ele com
  bindings, escolher entre direct, fanout, topic e headers, escrever padrões
  com * e #, e prever para onde uma routing key vai antes de publicar.
---

:::story Mais um setor
Na reunião de segunda, a Denise pediu para a expedição receber os pedidos
pagos direto, sem esperar a nota fiscal.

— A etiqueta não depende da nota — disse ela. — Eu consigo separar o
pedido antes.

— Tranquilo — disse Júlia. — O checkout publica também na fila da
expedição.

Na terça, o Rafa pediu que o pedido pago fosse para o sistema de e-mail
marketing. Na quarta, o Seu Norberto pediu uma cópia de tudo para
auditoria, "porque em janeiro alguém vai perguntar".

Na quinta, o Kaique abriu o `produtor.php` do checkout e contou.

— Ele publica quatro vezes o mesmo pedido, em quatro filas.

— E na semana que vem vão ser cinco — disse Júlia.

— E se uma das filas não existir?

— A mensagem daquela vai para lugar nenhum. As outras três chegam.

O Kaique virou uma etiqueta.

— Então o checkout é o único sistema da empresa que precisa saber o nome
de todos os setores.
:::

É o terceiro defeito da pasta de arquivos do capítulo
@cap:do-espeto-de-papel-ao-broker, agora com um broker de verdade por
baixo. Enquanto o produtor publica no *default exchange*, ele endereça
**filas** — e passa a conhecer cada interessado pelo nome. Cada setor novo
é uma mudança no checkout, o sistema que ninguém quer mexer em novembro.

A saída é o produtor parar de endereçar filas e passar a **descrever o que
aconteceu**: "um pedido foi pago". Quem se interessa por isso se inscreve.

## Exchange, binding, routing key

Três peças, e cada uma tem um dono diferente.

O **exchange** recebe as mensagens publicadas. Ele não guarda nada: decide,
na hora, para quais filas cada mensagem vai, e se nenhuma servir, descarta.

A **routing key** é uma etiqueta que o produtor põe na mensagem ao
publicar. Na Doce Mirabel, ela descreve o evento: `pedido.pago`,
`pedido.cancelado`, `nfe.rejeitada`.

O **binding** é uma regra que liga uma fila a um exchange: "mande para
esta fila as mensagens cuja routing key for assim". Quem cria o binding é
quem **consome** — o fiscal declara que quer pedidos pagos; o checkout nem
fica sabendo.

:::term Binding
A ligação entre um exchange e uma fila, com um padrão de routing key. Uma
fila pode ter vários bindings, em vários exchanges; um exchange pode ter
bindings para muitas filas. Uma mensagem chega a uma fila se **algum**
binding daquela fila casar com ela — e chega uma vez só, mesmo que dois
bindings casem.
:::

## Os quatro tipos

O tipo do exchange é a regra que ele usa para comparar a routing key com
os bindings.

| Tipo | Regra | Quando usar |
|---|---|---|
| direct | a routing key é **igual** à do binding | um evento, destinos por nome exato |
| fanout | ignora a routing key: copia para **todas** as filas ligadas | "todo mundo precisa saber" |
| topic | a routing key casa com um **padrão** de palavras | eventos com hierarquia; o caso comum |
| headers | compara **cabeçalhos** da mensagem, não a routing key | raro; quando o critério não cabe numa chave |

Tabela: O *default exchange* é um direct em que toda fila está ligada pelo
próprio nome.

O **topic** é o que a Doce Mirabel vai usar, e o que a maioria dos sistemas
de eventos usa. A routing key é dividida em **palavras** separadas por
ponto — `pedido.pago` tem duas, `nfe.rejeitada.cep` tem três — e o binding
pode usar dois curingas:

| Curinga | Casa com | `pedido.*` casa com | `pedido.#` casa com |
|---|---|---|---|
| `*` | exatamente **uma** palavra | `pedido.pago` | — |
| `#` | **zero ou mais** palavras | — | `pedido`, `pedido.pago`, `pedido.pago.pix` |

Tabela: `pedido.*` não casa com `pedido.pago.pix`: são duas palavras
depois do ponto, e o `*` vale uma.

## A topologia da fábrica

A topologia — o conjunto de exchanges, filas e bindings — é declarada num
script próprio. Ela é da empresa, não do checkout:

```php title="topologia.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();

$canal->exchange_declare('doce.eventos', 'topic', false, true, false);

$filas = [
    'fiscal.pedidos-pagos' => ['pedido.pago'],
    'expedicao.pedidos-pagos' => ['pedido.pago'],
    'avisos.pedidos' => ['pedido.*'],
    'auditoria.tudo' => ['#'],
];

foreach ($filas as $fila => $chaves) {
    $canal->queue_declare($fila, false, true, false, false);
    foreach ($chaves as $chave) {
        $canal->queue_bind($fila, 'doce.eventos', $chave);
    }
}
echo 'topologia declarada', PHP_EOL;
```

`exchange_declare` na linha 14 segue a lógica de `queue_declare`: nome,
tipo, `passive`, `durable` e `auto_delete`. O exchange é durável, para
sobreviver a um restart do broker. `queue_bind` na linha 26 cria o binding:
fila, exchange, padrão.

Os nomes das filas levam o **setor** na frente e o **assunto** depois —
`fiscal.pedidos-pagos`, não `pedidos-pagos`. Duas filas com o mesmo
interesse, de setores diferentes, são filas diferentes: cada uma recebe a
sua cópia e anda no seu ritmo.

O produtor, agora, publica **um** evento, no exchange, com uma routing key:

```php title="publicar.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();

[, $chave, $pedido] = $argv;
$corpo = json_encode(['pedido' => (int) $pedido]);

$canal->basic_publish(new AMQPMessage($corpo, [
    'content_type' => 'application/json',
    'delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT,
]), 'doce.eventos', $chave);
echo "publicado {$chave} do pedido {$pedido}", PHP_EOL;
```

A linha 15 desmonta o array `$argv` em variáveis: a primeira posição, o
nome do script, é descartada pela vírgula solitária; a segunda vira
`$chave` e a terceira, `$pedido`.

Declare a topologia e publique um pedido pago:

```text
$ php topologia.php
topologia declarada
$ php publicar.php pedido.pago 40117
publicado pedido.pago do pedido 40117
$ docker compose exec rabbitmq rabbitmqctl list_queues name messages
name	messages
expedicao.pedidos-pagos	1
auditoria.tudo	1
fiscal.pedidos-pagos	1
avisos.pedidos	1
```

Um publish, quatro cópias. O checkout escreveu "pedido.pago" e não sabe
que existem quatro setores interessados — nem precisa saber.

## Prever antes de publicar

A melhor forma de aprender os curingas é prever o resultado e depois
conferir. Antes de rodar cada comando abaixo, diga quais filas vão
crescer.

```text
$ php publicar.php pedido.cancelado 40118
```

`pedido.pago` não casa com `pedido.cancelado`; `pedido.*` casa; `#` casa
com tudo. Crescem avisos e auditoria:

```text
expedicao.pedidos-pagos	1
auditoria.tudo	2
fiscal.pedidos-pagos	1
avisos.pedidos	2
```

```text
$ php publicar.php nfe.rejeitada.cep 40119
```

Só `#` casa. Cresce só a auditoria, que vai para 3.

```text
$ php publicar.php pedido.pago.pix 40120
```

Esta é a que engana. `pedido.pago` exige a chave idêntica — não casa.
`pedido.*` exige **uma** palavra depois de `pedido` — `pago.pix` são duas,
não casa. Só a auditoria cresce, para 4:

```text
expedicao.pedidos-pagos	1
auditoria.tudo	4
fiscal.pedidos-pagos	1
avisos.pedidos	2
```

Se o Rafa decidir que o Pix merece uma chave própria, o fiscal para de
receber pedidos pagos por Pix — e ninguém recebe erro nenhum. O publish
funciona, a auditoria recebe, e a nota não sai.

:::pitfall
Mudar o formato de uma routing key é mudar um contrato com todos os
consumidores, mesmo que nenhum código de consumidor mude. Antes de
acrescentar uma palavra a uma chave, liste os bindings que dependem dela:

```text
$ docker compose exec rabbitmq rabbitmqctl list_bindings \
    source_name destination_name routing_key
doce.eventos	fiscal.pedidos-pagos	pedido.pago
doce.eventos	avisos.pedidos	pedido.*
doce.eventos	expedicao.pedidos-pagos	pedido.pago
doce.eventos	auditoria.tudo	#
```
:::

## Quem declara o quê

Com exchanges, uma pergunta aparece: se o produtor publica antes de
qualquer consumidor existir, as filas ainda não foram declaradas, os
bindings não existem, e a mensagem cai no vazio. O exchange descarta o que
não tem destino, do mesmo jeito que o *default exchange* descartou o
`fiscal.pedido` no painel.

A regra prática tem duas partes:

- **o produtor declara o exchange** em que publica, e nada mais — ele não
	sabe quem consome;
- **o consumidor declara a sua fila e os seus bindings** — ele sabe o que
	quer receber.

Com isso, cada lado sobe sozinho sem erro. O que sobra é a janela do
primeiro dia: eventos publicados antes de o consumidor novo existir se
perdem para ele. Por isso a topologia de produção é declarada **antes** do
deploy de quem publica — por um script como o `topologia.php`, rodado no
deploy, ou pelo próprio consumidor, que sobe primeiro.

:::key
O produtor conhece **eventos**; o consumidor conhece **filas**. O exchange
é o único ponto que os dois compartilham, e a routing key é o contrato
entre eles.
:::

:::milestone
Você tem: o exchange `doce.eventos`, do tipo topic, e quatro filas ligadas
a ele — fiscal, expedição, avisos e auditoria. O checkout publica
`pedido.pago` uma vez e não conhece nenhum setor.
:::

:::summary
- O produtor publica num exchange com uma routing key; bindings, criados
	por quem consome, decidem que filas recebem uma cópia.
- Direct compara a chave exata; fanout copia para todas; topic casa
	padrões de palavras; headers compara cabeçalhos.
- No topic, `*` vale exatamente uma palavra e `#` vale zero ou mais:
	`pedido.*` não casa com `pedido.pago.pix`.
- Uma chave que não casa com nenhum binding é descartada em silêncio;
	mudar o formato de uma chave é mudar um contrato.
- O produtor declara o exchange; o consumidor declara fila e bindings; a
	topologia de produção existe antes do primeiro publish.
:::

:::exercise level=1
Sem rodar, diga quais das quatro filas recebem cada publicação:
`pedido`, `pedido.pago`, `estoque.baixado`, `pedido.devolvido`.

:::answer
- `pedido`: só `auditoria.tudo`. `pedido.*` exige uma palavra depois do
	ponto, e aqui não há ponto nenhum.
- `pedido.pago`: as quatro.
- `estoque.baixado`: só `auditoria.tudo`.
- `pedido.devolvido`: `avisos.pedidos` e `auditoria.tudo`.
:::

:::exercise level=2
O Rafa quer que pedidos pagos por Pix tenham a chave `pedido.pago.pix`, e
os de cartão, `pedido.pago.cartao`, para medir cada um separadamente. Que
bindings mudam para que fiscal e expedição continuem recebendo todos os
pedidos pagos, e o que você faria na ordem do deploy?

:::answer
Fiscal e expedição passam a se ligar com `pedido.pago.*` (ou
`pedido.pago.#`, se um dia houver mais níveis). Avisos, que usa
`pedido.*`, deixa de receber pedidos pagos, e precisa de um binding a mais,
`pedido.pago.*`, se ainda quiser.

A ordem importa. Primeiro **acrescente** os bindings novos, mantendo os
antigos — uma fila pode ter os dois, e a mensagem chega uma vez só. Depois
publique com as chaves novas. Só então remova os bindings `pedido.pago`
antigos. Na ordem inversa, existe uma janela em que o checkout publica
`pedido.pago.pix` e o fiscal ainda não escuta, e as notas daquele intervalo
não saem.
:::
