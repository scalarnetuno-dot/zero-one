---
title: "Eventos com Mirabel"
number: 10
slug: eventos-com-mirabel
part: p3
kicker: "O total do pedido saiu do checkout como 89,90 e chegou ao fiscal como 89,9. Ninguém mentiu; o JSON arredondou."
goal: >-
  Ler, propriedade por propriedade, o que um publish da Mirabel manda pelo
  fio, desenhar o corpo de um evento sem armadilhas de número, dar à
  mensagem uma identidade estável, versionar o contrato e saber o que
  acontece quando o broker não responde.
---

Um evento publicado é a única coisa que o checkout e o fiscal têm em
comum. O fiscal não lê o banco da loja, não chama a API dela e não sabe em
que linguagem ela foi escrita: tudo o que ele sabe sobre o pedido está
**dentro da mensagem**. Este capítulo abre uma mensagem da Mirabel e
decide, campo por campo, o que precisa estar lá.

## A mensagem aberta

Com o consumidor do fiscal desligado, publique um pedido e peça ao painel
para mostrá-lo: em **Queues and Streams**, a fila `fiscal.pedidos-pagos`,
*Get messages* com *Nack message requeue true*. A mesma informação sai da
API do painel em JSON, que é como ela aparece abaixo:

```json
{
  "exchange": "doce.eventos",
  "routing_key": "pedido.pago",
  "redelivered": false,
  "properties": {
    "type": "DoceMirabel\\Eventos\\PedidoPago",
    "timestamp": 1790379711,
    "message_id": "a7a36dcc8e685341aed0fd59ecc39088",
    "delivery_mode": 2,
    "headers": { "x-schema-version": 1 },
    "content_type": "application/json"
  },
  "payload": "{\"pedido\":40119,\"total\":89.9}"
}
```

Tudo o que não está em `payload` foi a biblioteca que pôs. Vale ler cada
um, porque cada um responde a uma pergunta que alguém vai fazer numa
madrugada.

| Propriedade | Valor | Responde |
|---|---|---|
| `delivery_mode` | `2` | a mensagem sobrevive a um restart? |
| `content_type` | `application/json` | como eu leio o corpo? |
| `message_id` | 32 caracteres aleatórios | esta é a mesma mensagem que eu já vi? |
| `type` | a classe PHP do evento | que tipo de coisa aconteceu? |
| `timestamp` | segundos desde 1970 | quando foi publicada? |
| `x-schema-version` | `1` | em que versão do contrato o corpo está? |

Tabela: As propriedades são o envelope; o payload é a carta.

O `timestamp` é um número Unix: segundos contados desde a meia-noite de 1º
de janeiro de 1970, em UTC. `date('c', 1790379711)` o transforma em data
legível no PHP.

## A carta: o que vai no corpo

O payload acima traz uma surpresa. O checkout publicou `'total' => 89.90`;
a mensagem diz `89.9`.

Não é defeito da biblioteca. `89.90` e `89.9` são o **mesmo número** em
ponto flutuante, e o `json_encode` escreve a forma mais curta. O zero não
tinha significado para o PHP — tinha para o Seu Norberto, e tem para
qualquer conta de dinheiro. Um `float` também não representa exatamente
valores como `0.1`, e somas de centavos acumulam erros minúsculos que viram
um real de diferença no fechamento do mês.

A regra para mensagens é a mesma dos bancos de dados: **dinheiro vai em
centavos, como inteiro**.

```php
$pedido = ['pedido' => 40117, 'total_centavos' => 8990];
```

O nome do campo carrega a unidade, e nenhum consumidor, em nenhuma
linguagem, precisa adivinhar se `8990` são reais ou centavos.

A segunda decisão sobre o corpo é **quanto** colocar nele. Há dois
extremos:

- o evento **magro** leva só o identificador — `{"pedido": 40117}` — e
	quem consome busca o resto na loja;
- o evento **gordo** leva tudo o que os consumidores precisam — itens,
	endereço, CPF, total — e ninguém precisa perguntar nada a ninguém.

O magro parece econômico e reintroduz a dependência que a fila veio tirar:
se a loja estiver fora do ar quando o fiscal consumir, o fiscal para. E o
pedido pode ter mudado entre a publicação e o consumo, e a nota sai com o
endereço novo de um pedido antigo. Para a Doce Mirabel, o evento leva o
que a nota, a etiqueta e o e-mail precisam, **como era no momento em que o
pedido foi pago**:

```php
$pedido = [
    'pedido' => 40117,
    'pago_em' => '2026-11-27T10:04:12-03:00',
    'total_centavos' => 8990,
    'cliente' => ['nome' => 'Antenor Lima', 'cpf' => '...'],
    'entrega' => ['cep' => '37701-000', 'cidade' => 'Serra Clara'],
    'itens' => [['sku' => 'GEL-AMX-320', 'quantidade' => 2]],
];
```

:::warning
Evento gordo carrega dado pessoal — nome, CPF, endereço. Ele fica gravado
no disco do broker enquanto estiver na fila e aparece no painel para quem
tiver acesso. Mande só o que algum consumidor usa, e trate o acesso ao
painel de produção como acesso ao banco de clientes.
:::

## A identidade da mensagem

O `message_id` do exemplo é aleatório: cada `publish()` gera um novo. Isso
basta para distinguir mensagens, mas não para reconhecer uma repetição.
Se o checkout publicar o mesmo pedido pago duas vezes — um clique duplo,
um retry depois de um timeout —, as duas mensagens terão identidades
diferentes, e ninguém do outro lado vai saber que são o mesmo pagamento.

`publish()` aceita argumentos nomeados para isso:

```php title="publicar-completo.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use DoceMirabel\Eventos\PedidoPago;

$pedido = ['pedido' => 40117, 'total_centavos' => 8990];

(new PedidoPago($pedido))->publish(
    messageId: 'pedido-40117-pago',
    correlationId: 'checkout-7f3a9c',
    idempotencyKey: 'pedido-40117',
);
```

**Argumentos nomeados** — `messageId:` antes do valor — deixam passar só os
parâmetros que interessam, em qualquer ordem, sem preencher os outros com
`null`.

```json
{
  "message_id": "pedido-40117-pago",
  "correlation_id": "checkout-7f3a9c",
  "headers": {
    "x-idempotency-key": "pedido-40117",
    "x-schema-version": 1
  }
}
```

Os três identificadores respondem perguntas diferentes:

| Identificador | É | Serve para |
|---|---|---|
| `message_id` | a identidade desta mensagem | reconhecer a **mesma mensagem** entregue de novo |
| `x-idempotency-key` | a identidade da operação de negócio | reconhecer o **mesmo pagamento** publicado duas vezes |
| `correlation_id` | a identidade da conversa | juntar, no log, tudo o que aquele checkout causou |

Tabela: Uma reentrega do broker repete o `message_id`. Um checkout que
publica duas vezes repete a chave de idempotência, não o `message_id`.

O `correlation_id` é o que salva a investigação. O checkout gera um por
requisição e o repassa a tudo o que publica; cada consumidor o repassa ao
que ele mesmo publicar. Quando o Seu Norberto perguntar por que o 40117
teve duas notas, uma busca por `checkout-7f3a9c` nos logs mostra a
história inteira, de todos os setores, em ordem.

## A versão do contrato

O header `x-schema-version` diz em que versão do contrato o corpo está. Ele
começa em 1 e só muda quando o formato muda de um jeito que um consumidor
antigo não entende — um campo renomeado, uma unidade trocada.

```php title="src/Eventos/PedidoPago.php" numbered
<?php

declare(strict_types=1);

namespace DoceMirabel\Eventos;

use Mirabel\RabbitMQ\Event;

final class PedidoPago extends Event
{
    public static string $routingKey = 'pedido.pago';
    public static int $schemaVersion = 2;
}
```

Acrescentar um campo novo **não** muda a versão: consumidor antigo ignora
o que não conhece. Trocar `total` por `total_centavos`, sim — um fiscal
que lê `total` passa a ler nada. O consumidor usa a versão para decidir,
antes de tocar no corpo, se sabe lê-lo; e a troca de versão exige a mesma
ordem de deploy de uma troca de routing key: primeiro os consumidores que
entendem as duas, depois o produtor.

## Quando o publish falha

`publish()` pode falhar de dois jeitos, e eles são diferentes de propósito.

O primeiro é **erro de programação**. Um evento sem `$routingKey`:

```text
PHP Fatal error:  Uncaught LogicException: Event Esquecido must
declare "public static string $routingKey" or receive a routing key
in publish().
```

Esse erro aparece no primeiro teste e nunca em produção, e a mensagem diz
exatamente o que falta. Um payload que não vira JSON — um recurso, uma
string com bytes inválidos — também falha na hora, sem tentar de novo:
repetir não conserta dado.

O segundo é **erro de transporte**: o broker não responde. Aqui a
biblioteca tenta de novo, abrindo uma conexão nova a cada tentativa, com
espera crescente entre elas — 1 segundo, 2, 4 —, e desiste depois de
`MB_RABBITMQ_PUBLISH_RETRIES` novas tentativas, que por padrão são três.
Todas usam o **mesmo** `message_id`. Esgotadas as tentativas, ela lança a
exceção original, uma `AMQPIOException`.

O limite existe por causa de onde o `publish()` costuma morar: dentro de
uma requisição HTTP. Um publish que tentasse para sempre seria o checkout
de 2025 com outro nome — o cliente esperando uma dependência que não
volta. Com o padrão, o pior caso é alguns segundos e um erro que a
aplicação pode tratar.

| Variável | Padrão | Efeito |
|---|---|---|
| `MB_RABBITMQ_PUBLISH_RETRIES` | `3` | novas tentativas depois da primeira falha |
| `MB_RABBITMQ_RECONNECT_DELAY_MS` | `1000` | espera antes da primeira nova tentativa, dobrando a cada uma |
| `MB_RABBITMQ_CONNECT_TIMEOUT` | `3` | segundos para desistir de uma conexão que não responde |

Tabela: Pior caso com os padrões: quatro conexões e 1 + 2 + 4 segundos de
espera, mais o tempo de cada tentativa de conexão.

:::pitfall
Tentar de novo com o mesmo `message_id` não impede duplicata. Se o broker
recebeu a primeira mensagem e a conexão caiu antes de a biblioteca saber
disso, a nova tentativa publica a segunda cópia. Por isso o identificador
é estável: para que o **consumidor** possa reconhecer a repetição. O
produtor, sozinho, não consegue.
:::

E o que o checkout faz quando o `publish()` desiste? Hoje, a resposta
honesta é: mostra erro ao cliente, que foi cobrado. É melhor que quatro
horas de SEFAZ, mas ainda não é o que o Seu Norberto aceita.

:::story O total do pedido
Na terça, o Seu Norberto mandou uma foto pelo WhatsApp: o espelho de uma
nota de teste, emitida em homologação a partir de um evento.

*Valor total: R$ 89,9*

— Está faltando um zero — escreveu ele.

— O valor está certo — respondeu a Júlia. — Oitenta e nove e noventa.

— Eu sei que está certo. A Receita também sabe. O cliente que recebe a
nota com um nove sozinho no fim não sabe, e liga.

À tarde, o campo virou `total_centavos` e a versão do evento foi para 2. O
Kaique anotou no verso de uma etiqueta: *dinheiro não é número*.
:::

:::milestone
Você tem: o evento `PedidoPago` na versão 2, com o corpo que a nota, a
etiqueta e o e-mail precisam, dinheiro em centavos, e publicado com
`messageId`, `idempotencyKey` e `correlationId` estáveis. Um publish que
não alcança o broker desiste em segundos, em vez de prender o cliente.
:::

:::summary
- A Mirabel põe em toda mensagem `delivery_mode` 2, `content_type`,
	`message_id`, `type`, `timestamp` e `x-schema-version`.
- Dinheiro vai em centavos, como inteiro, com a unidade no nome do campo;
	`float` em JSON perde zeros e acumula erro.
- Evento gordo, com o que os consumidores precisam no estado do momento,
	evita que o consumidor dependa de o produtor estar no ar.
- `message_id` identifica a mensagem, `x-idempotency-key` a operação,
	`correlation_id` a conversa; os três são passados a `publish()` por
	argumentos nomeados.
- Erro de programação falha na hora; erro de transporte é tentado de novo
	até `MB_RABBITMQ_PUBLISH_RETRIES` vezes, com o mesmo `message_id`.
:::

:::exercise level=1
O checkout publica `PedidoPago` para o pedido 40117 e, por um clique
duplo, publica de novo um segundo depois. Com o `publicar-completo.php`
deste capítulo, quais identificadores das duas mensagens são iguais e
quais são diferentes?

:::answer
Todos iguais: o código passa `messageId`, `idempotencyKey` e
`correlationId` fixos. Isso é conveniente para o exercício e errado para o
`correlation_id`, que deveria ser gerado por requisição — os dois cliques
são duas requisições, e merecem dois ids de conversa.

No checkout de verdade, o `messageId` e a `idempotencyKey` saem do pedido
(`pedido-40117-pago`, `pedido-40117`), e por isso se repetem no clique
duplo, e o `correlationId` sai da requisição. É justamente a repetição da
chave de idempotência que vai permitir ao fiscal perceber que se trata do
mesmo pagamento.
:::

:::exercise level=2
A transportadora parceira pediu que o evento traga o peso total em
gramas. Isso muda o `$schemaVersion`? E se, em vez de acrescentar, fosse
preciso trocar o campo `cep`, hoje texto com hífen, por um número sem
hífen?

:::answer
Acrescentar `peso_gramas` não muda a versão: um consumidor antigo ignora
um campo que não conhece, e continua funcionando.

Trocar o formato do `cep` muda. Um consumidor que faz
`str_replace('-', '', $cep)` num inteiro quebra, e um que valida o formato
com hífen passa a recusar todos os pedidos. A versão vai para 3, os
consumidores são atualizados primeiro para aceitar as duas versões — lendo
o header antes do corpo —, e só então o checkout passa a publicar a 3.
Uma alternativa mais barata costuma existir: acrescentar `cep_numero` ao
lado do `cep` antigo, sem trocar versão, e remover o antigo meses depois.
:::
