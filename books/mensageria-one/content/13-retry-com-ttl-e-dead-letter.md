---
title: "Retry com TTL e dead-letter"
number: 13
slug: retry-com-ttl-e-dead-letter
part: p4
kicker: "A SEFAZ caiu às dez e catorze. A nota do 40117 saiu às dez e catorze e quatro segundos, na terceira tentativa, sem nenhum sleep."
goal: >-
  Configurar novas tentativas com espera num worker, entender como o
  RabbitMQ faz essa espera sozinho com dead-letter exchange e TTL, ler o
  header x-death, e saber por que a mensagem tem que voltar pelo default
  exchange e não pelo exchange principal.
---

:::story Três etiquetas
Numa terça de outubro, a homologação da SEFAZ passou a tarde instável. A
Júlia tinha acabado de configurar tentativas no worker do fiscal, e ficou
satisfeita: as notas saíam na segunda ou na terceira tentativa, sem
ninguém fazer nada.

Às cinco, a Denise apareceu na mesa dela com um bolo de etiquetas na mão.

— A Zebrinha imprimiu três etiquetas para o 40117.

— Três?

— Três. E duas para o 40121. E quatro para o 40126.

A Júlia abriu o log do fiscal. O 40117 tinha falhado duas vezes antes de
a nota sair. O 40121, uma. O 40126, três.

— A expedição recebe uma etiqueta a mais para cada vez que o fiscal
tenta de novo — disse ela, devagar.

— A expedição não tem nada a ver com o fiscal — disse a Denise.

— Não deveria ter.
:::

O capítulo @cap:ack-quando-a-mensagem-pode-morrer terminou com dois
pedidos para uma falha temporária: esperar antes de tentar de novo, e
desistir depois de algumas tentativas. O `requeue` não faz nenhum dos
dois. Este capítulo monta as duas coisas — primeiro pela biblioteca,
depois abrindo o mecanismo por baixo —, e é no mecanismo que mora o
defeito da tarde de terça.

## Tentativas no worker

Na Mirabel, tentar de novo é uma propriedade a mais no worker:

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
    public static array $retry = [
        'delay' => 2000, 'max_attempts' => 3,
    ];

    public function handle(Envelope $envelope): void
    {
        $pedido = $envelope->body['pedido'];
        $hora = date('H:i:s');
        $n = $envelope->attempt;

        if ($n < 3) {
            echo "{$hora} tentativa {$n}: SEFAZ fora", PHP_EOL;
            throw new \RuntimeException('SEFAZ não respondeu');
        }

        echo "{$hora} tentativa {$n}: NF-e {$pedido}", PHP_EOL;
    }
}
```

`delay` é a espera entre tentativas, em milissegundos. `max_attempts` é o
número total de tentativas, contando a primeira. `$envelope->attempt` diz
em qual tentativa esta entrega está — o exemplo o usa para simular uma
SEFAZ que falha duas vezes e volta.

Ligue o worker e publique um pedido:

```text
$ php consumir.php
fiscal esperando pedidos pagos. Ctrl+C para sair.
23:54:21 tentativa 1: SEFAZ fora
23:54:23 tentativa 2: SEFAZ fora
23:54:25 tentativa 3: NF-e 40117
```

Três tentativas, dois segundos entre elas, e a nota saiu. Se a terceira
também falhasse, a mensagem iria para `.error` com
`x-mirabel-attempts = 3`.

Olhe a fila no meio do processo, durante uma das esperas:

```text
fiscal.pedidos-pagos.error	0
fiscal.pedidos-pagos.retry	1
fiscal.pedidos-pagos	0
```

O pedido não está na fila principal, nem com o worker. Está na fila
`.retry`. E o worker, durante esses dois segundos, está livre para
processar outros pedidos — nenhum `sleep` segurou o processo.

## Quem faz a espera

A espera é feita pelo **broker**, com duas peças do próprio RabbitMQ.

A primeira é o **dead-letter exchange**. Uma fila pode ter um argumento,
`x-dead-letter-exchange`, que diz para onde vão as mensagens que
**morrem** nela. Uma mensagem morre quando é recusada sem requeue, quando
expira, ou quando a fila está cheia e a descarta. Em vez de sumir, ela é
republicada no exchange indicado.

:::term Dead-letter exchange
O exchange para onde uma fila manda as mensagens que morrem nela —
recusadas sem requeue, expiradas ou descartadas por limite. Configurado
pelos argumentos `x-dead-letter-exchange` e, opcionalmente,
`x-dead-letter-routing-key`, que troca a routing key na passagem. É a
resposta à pergunta do fim do capítulo sobre ack: para onde vai o
`nack(false)`.
:::

A segunda é o **TTL** — *time to live* —, o tempo de vida de uma mensagem
numa fila. Com o argumento `x-message-ttl`, toda mensagem que ficar mais
que aquele tempo na fila expira. E, se a fila tiver dead-letter exchange,
expirar é morrer — e a mensagem é republicada.

Juntas, as duas peças fazem um relógio. Os argumentos que a Mirabel
declarou contam a história toda:

```text
fiscal.pedidos-pagos
  x-dead-letter-exchange     fiscal.pedidos-pagos.retry
  x-dead-letter-routing-key  fiscal.pedidos-pagos
fiscal.pedidos-pagos.retry
  x-message-ttl              2000
  x-dead-letter-exchange     ""
  x-dead-letter-routing-key  fiscal.pedidos-pagos
```

:::diagram type="flowchart" caption="A espera é uma fila sem consumidor, com prazo de validade."
nodes:
  - { id: p,  type: process,  text: "fiscal.pedidos-pagos" }
  - { id: w,  type: decision, text: "handle() deu certo?" }
  - { id: ok, type: end,      text: "ack" }
  - { id: r,  type: process,  text: "fiscal.pedidos-pagos.retry (TTL 2 s)" }
  - { id: d,  type: process,  text: "default exchange" }
edges:
  - { from: p, to: w }
  - { from: w, to: ok, label: "sim" }
  - { from: w, to: r,  label: "nack, sem requeue" }
  - { from: r, to: d,  label: "expira" }
  - { from: d, to: p,  label: "pelo nome da fila" }
:::

Na primeira tentativa, o `handle()` lança exceção e o worker responde
`nack` sem requeue. A mensagem morre na fila principal, e o dead-letter a
leva ao exchange `.retry`, que a entrega na fila `.retry`. Lá ninguém
consome. Dois segundos depois, ela expira, morre de novo, e o dead-letter
da `.retry` a republica no **default exchange** com a routing key
`fiscal.pedidos-pagos` — que, como o capítulo @cap:o-que-vamos-construir
mostrou, entrega na fila de nome igual. Ela está de volta ao começo, e o
worker a recebe de novo.

## A contagem que sobrevive a tudo

Como o worker sabe que esta é a terceira tentativa? Ele não guarda
contador nenhum — um contador em memória se perderia num restart do
worker, e não funcionaria com dois workers dividindo a fila.

Quem conta é o broker. Toda vez que uma mensagem morre, o RabbitMQ
acrescenta ou atualiza um header chamado `x-death`, com a fila em que ela
morreu, o motivo e **quantas vezes** isso aconteceu. Na terceira entrega, resumido — o header
real tem mais campos, como o exchange e as routing keys —, ele diz:

```text
x-death = [
  { queue: fiscal.pedidos-pagos.retry, reason: expired,  count: 2 },
  { queue: fiscal.pedidos-pagos,       reason: rejected, count: 2 },
]
```

Duas expirações na fila de espera: esta é a terceira entrega. O
`$envelope->attempt` é exatamente isso, lido do header — e, como o header
viaja **dentro da mensagem**, a contagem sobrevive a restart do worker, a
troca de máquina e a quantos consumidores houver.

## A etiqueta a mais

Volte à tarde de terça. A versão da biblioteca que a Júlia usava naquele
dia tinha a `.retry` configurada de um jeito diferente: quando a mensagem
expirava, ela era republicada no **exchange principal**, `doce.eventos`,
com a routing key original, `pedido.pago`.

Parece equivalente. Não é. No exchange principal, `pedido.pago` casa com
**todos** os bindings de `pedido.pago` — o do fiscal e o da expedição. Cada
tentativa de nota fiscal virava um `pedido.pago` novo para todo mundo. O
40117 falhou duas vezes no fiscal; a expedição recebeu o original mais
duas cópias, e a Zebrinha imprimiu três etiquetas.

O defeito só aparece com **duas filas na mesma routing key e uma falha**,
que é exatamente a situação que a Parte 2 construiu de propósito. Num
teste com um consumidor só, a versão errada e a certa se comportam igual.
No teste de integração da biblioteca que reproduz o caso — dois
consumidores, uma falha —, a fila vizinha recebeu duas cópias em vez de
uma; com a correção, uma.

A correção é a linha `x-dead-letter-exchange ""` da `.retry`: voltar pelo
**default exchange**, pelo nome da fila. O default exchange só conhece
filas pelo nome, e o nome é o do fiscal. A mensagem volta para quem falhou
e para mais ninguém.

:::key
Uma mensagem em retry é um assunto **da fila que falhou**, não um evento
novo. Ela precisa voltar endereçada à fila, pelo default exchange — nunca
republicada com a routing key original, que a entregaria de novo a todos os
interessados.
:::

:::pitfall
Os argumentos de uma fila não mudam depois de criada, lembra? Mudar o
`delay` do worker muda o `x-message-ttl` da `.retry`, e o RabbitMQ
recusaria a declaração com 406. A Mirabel trata esse caso: se a `.retry`
estiver **vazia**, ela é apagada e recriada com os argumentos novos; se
tiver mensagens esperando, o worker para e diz que é preciso esvaziá-la
antes. Mudar o `delay` em produção, portanto, pede uma janela em que a
fila de espera esteja vazia.
:::

## Quanto esperar, quantas vezes

A Mirabel usa um atraso fixo: toda tentativa espera o mesmo `delay`. É o
mais simples de prever e basta para a maioria das falhas temporárias. A
escolha dos números é uma decisão sobre o serviço do outro lado, não sobre
o RabbitMQ.

| Falha típica | `delay` | `max_attempts` | Por quê |
|---|---|---|---|
| SEFAZ instável | 30 s a 2 min | 10 a 20 | quedas de minutos a uma hora; a nota tem prazo em horas |
| ERP da fábrica travado | 10 s | 6 | reinicia sozinho em um minuto |
| e-mail recusado por excesso | 1 min | 5 | o provedor libera em minutos |
| API com defeito de dados | — | 1 | tentar de novo não conserta dado; `reject()` |

Tabela: `delay × (max_attempts − 1)` é quanto tempo um pedido pode esperar
antes de ir para a fila de erro. Para o fiscal com 1 min e 20 tentativas,
cerca de vinte minutos.

A conta da legenda é a pergunta certa para a reunião: "se a SEFAZ cair
por uma hora, o que acontece com as notas?". Com uma janela menor que a
queda, todas vão para a fila de erro e alguém precisa reprocessá-las
depois. Com uma janela maior, elas saem sozinhas quando a SEFAZ voltar.

:::milestone
Você tem: o fiscal com `$retry` configurado, esperando no broker, e não no
processo, entre as tentativas; a contagem lida do `x-death`; e a
`.retry` voltando pelo default exchange, sem entregar cópias à expedição.
:::

:::summary
- `$retry = ['delay' => ms, 'max_attempts' => n]` faz o worker tentar de
	novo com espera; a primeira tentativa conta.
- A espera é do broker: `nack` sem requeue leva a mensagem, por
	dead-letter, para a fila `.retry`, que não tem consumidor e tem TTL;
	ao expirar, ela volta.
- O header `x-death` conta as mortes por fila; `$envelope->attempt` o lê, e
	a contagem sobrevive a restarts e a vários consumidores.
- A volta tem que ser pelo default exchange, endereçada à fila; pela
	routing key original, ela chega de novo a todos os interessados.
- `delay × (max_attempts − 1)` é a janela que um pedido tem antes da fila
	de erro; ela deve cobrir a queda típica do serviço.
:::

:::exercise level=1
Com `delay` 2000 e `max_attempts` 3, e um `handle()` que sempre falha, em
quanto tempo um pedido chega à fila de erro? Quantas entradas o `x-death`
dele tem, e com que contagens?

:::answer
Cerca de quatro segundos: tentativa 1 no instante zero, espera de 2 s,
tentativa 2, espera de 2 s, tentativa 3 — que falha e vai para a `.error`.
O `x-death` tem duas entradas: a fila principal com motivo `rejected` e a
`.retry` com motivo `expired`, e a contagem de expirações é 2 — duas
esperas. A rejeição da terceira tentativa não gera morte, porque o worker
publica a mensagem direto na fila de erro e confirma a original.
:::

:::exercise level=2
A Doce Mirabel quer que a SEFAZ fora do ar por até uma hora não mande
nenhuma nota para a fila de erro, sem martelar a SEFAZ com tentativas.
Proponha `delay` e `max_attempts`, calcule a janela, e diga que custo a
escolha tem para quem espera a nota.

:::answer
Uma escolha razoável é `delay` de 5 minutos e `max_attempts` de 14: a
janela é 5 × 13 = 65 minutos, com treze tentativas depois da primeira —
menos de três por quinze minutos, o que não sobrecarrega a SEFAZ.

O custo é a latência na volta: se a SEFAZ voltar dois minutos depois de
uma tentativa, a nota espera mais três até a próxima. Com 1 minuto e 61
tentativas, a nota sai no máximo um minuto depois da volta, ao preço de
sessenta tentativas por hora. A escolha depende de quanto cada minuto de
nota atrasada custa — pergunta para o Seu Norberto, não para o broker.
:::
