---
title: "Medir a fila"
number: 19
slug: medir-a-fila
part: p5
kicker: "Duzentas mensagens na fila não diz nada. Quinze segundos de espera e crescendo dez por segundo diz tudo."
goal: >-
  Responder, para qualquer fila, as quatro perguntas que importam —
  quantas esperam, quantas estão em trabalho, quem consome e há quanto
  tempo a mais antiga espera —, ler ritmo de entrada e saída, levar as
  métricas do broker ao Prometheus e escrever os alertas que acordam
  alguém na hora certa.
---

:::story Está tudo verde
O Rafa passou a abrir o painel do RabbitMQ toda manhã, como abria o
Instagram. Numa quinta, mandou um print para a Júlia com a mensagem:
"tudo verde".

O print mostrava a aba **Overview**, com os gráficos de mensagens
subindo e descendo. Tudo, de fato, verde.

A Júlia abriu a aba **Queues and Streams**. A fila `avisos.pedidos` tinha
3.412 mensagens.

— Rafa, o e-mail de confirmação está saindo com quanto de atraso?

— Não sei. Por quê?

— Porque tem três mil e quatrocentos na frente.

— Mas está verde.

— Está verde porque o painel não sabe o que é atraso. Quem sabe é o
cliente que comprou às nove e recebeu o e-mail ao meio-dia.

O Kaique, que ouviu da mesa ao lado, abriu o WhatsApp do SAC. Tinha seis
mensagens perguntando se a compra tinha dado certo.
:::

O painel do RabbitMQ mostra tudo, e isso é parte do problema: ele não diz
o que olhar. Uma fila com 3.412 mensagens pode estar ótima — um lote de
e-mails de marketing, sem pressa — ou pode ser seis clientes no SAC. O
número sozinho não distingue. Este capítulo escolhe as métricas que
distinguem e as leva para onde alguém vai vê-las antes do cliente.

## As quatro perguntas

Para qualquer fila, quatro números respondem quase tudo:

| Pergunta | Métrica | O que ela revela |
|---|---|---|
| quantas esperam? | `messages_ready` | o tamanho do atraso, em mensagens |
| quantas estão em trabalho? | `messages_unacknowledged` | consumidores ocupados — ou ack esquecido |
| quem consome? | `consumers` | zero é o alerta mais importante que existe |
| há quanto tempo a mais antiga espera? | `head_message_timestamp` | o atraso que o cliente sente |

Tabela: As três primeiras vêm de graça. A quarta depende de a mensagem
ter `timestamp` — e a Mirabel põe em todas.

A quarta é a que o Rafa precisava. Profundidade é contagem; **espera** é
tempo, e tempo é o que o cliente sente. Trezentas mensagens de um segundo
cada são cinco minutos; trezentas de dez segundos são quase uma hora. A
API do painel informa o `timestamp` da primeira mensagem da fila, e a
diferença para agora é a espera dela.

E um quinto número, que é uma comparação: o **ritmo** de entrada contra o
de saída. Se entram vinte por segundo e saem dez, a fila cresce dez por
segundo, e não há capacidade de consumo que se recupere sozinha.

## Perguntando à API

O painel é construído sobre uma API HTTP, e ela responde em JSON o mesmo
que a tela mostra. Um script lê as quatro perguntas e o ritmo de uma fila:

```php title="medir-fila.php" numbered
<?php

declare(strict_types=1);

$fila = $argv[1];
$painel = getenv('RABBITMQ_PAINEL') ?: 'http://localhost:15672';
$url = $painel . '/api/queues/%2F/' . rawurlencode($fila);

$credencial = base64_encode('guest:guest');
$contexto = stream_context_create(['http' => [
    'header' => "Authorization: Basic {$credencial}",
]]);
$q = json_decode(file_get_contents($url, false, $contexto), true);

$maisAntiga = $q['head_message_timestamp'] ?? null;
$espera = $maisAntiga === null ? 0 : time() - $maisAntiga;
$entrada = $q['message_stats']['publish_details']['rate'] ?? 0;
$saida = $q['message_stats']['ack_details']['rate'] ?? 0;

printf("%-22s %s\n", 'fila', $fila);
printf("%-22s %d\n", 'esperando (ready)', $q['messages_ready']);
printf("%-22s %d\n", 'em trabalho', $q['messages_unacknowledged']);
printf("%-22s %d\n", 'consumidores', $q['consumers']);
printf("%-22s %d s\n", 'espera da mais antiga', $espera);
printf("%-22s %.1f/s entrando, ", 'ritmo', $entrada);
printf("%.1f/s saindo\n", $saida);
```

O `%2F` na URL é o virtual host `/`, codificado para caber num endereço.
`file_get_contents` com um contexto de stream faz a requisição HTTP com o
cabeçalho de autenticação básica — usuário e senha em base64, o formato
que o painel aceita. `?? null` e `?? 0` protegem contra campos que a API
omite quando a fila está vazia ou parada.

Com uma carga de vinte pedidos por segundo contra um consumidor que dá
conta de dez:

```text
$ php medir-fila.php avisos.pedidos
fila                   avisos.pedidos
esperando (ready)      205
em trabalho            1
consumidores           1
espera da mais antiga  15 s
ritmo                  19.8/s entrando, 9.6/s saindo
```

Leia de baixo para cima. Entram vinte, saem dez: a fila cresce dez por
segundo. A mais antiga espera quinze segundos, e daqui a um minuto vai
esperar setenta e cinco. Um consumidor, uma mensagem em trabalho — ele
está ocupado, não travado. O diagnóstico escreve-se sozinho: falta
capacidade de consumo, e o conserto é pôr mais consumidores, como o
capítulo @cap:a-zebrinha-e-o-prefetch mostrou.

:::key
O tempo para esvaziar uma fila é `ready ÷ (saída − entrada)`. Se a saída
não é maior que a entrada, a resposta é "nunca", e nenhuma espera vai
resolver: só mais consumo, ou menos entrada.
:::

## Levando ao Prometheus

Um script responde quando alguém pergunta. Para que alguém seja avisado
**sem** perguntar, as métricas precisam ser coletadas o tempo todo, e o
padrão de mercado para isso é o **Prometheus** — um banco de séries
temporais que visita, a cada poucos segundos, endereços HTTP que expõem
métricas em texto, e guarda o histórico.

O RabbitMQ 4 já traz esse endereço pronto: o plugin `rabbitmq_prometheus`,
ligado na imagem oficial, responde na porta **15692**. Em
`/metrics/per-object`, ele dá uma linha por fila:

```text
rabbitmq_queue_messages_ready{vhost="/",queue="avisos.pedidos"} 2
```

A resposta tem uma linha dessas para cada fila e cada métrica — a
`.retry` e a `.error` de cada worker incluídas. Cada linha é uma métrica,
com **rótulos** entre chaves que dizem de que
fila ela é, e o valor no fim. O `/metrics` sem sufixo soma tudo — útil
para o broker inteiro, inútil para saber qual fila está atrasada.

O Prometheus é configurado para visitar esse endereço:

```yaml title="prometheus.yml"
scrape_configs:
  - job_name: rabbitmq
    metrics_path: /metrics/per-object
    static_configs:
      - targets: ["rabbitmq:15692"]
```

E o **Grafana**, a ferramenta de painéis que lê do Prometheus, desenha as
curvas. O repositório companheiro do livro traz um Compose com RabbitMQ,
Prometheus e Grafana já ligados, e um painel pronto.

## Os alertas que importam

Um painel só ajuda quem está olhando. Às três da tarde de uma quinta,
ninguém está. O que ajuda é um **alerta**: uma regra que o Prometheus
avalia continuamente e que dispara uma notificação quando fica verdadeira.
Quatro regras cobrem a Doce Mirabel:

| Alerta | Regra | Por quê |
|---|---|---|
| fila sem consumidor | `consumers == 0` por 2 min, em fila de trabalho | ninguém está atendendo; tudo o mais é consequência |
| fila de erro com mensagens | `ready > 0` em fila `.error` | venda sem nota, pedido sem etiqueta |
| espera alta | espera da mais antiga acima do combinado por fila | o que o cliente sente |
| fila crescendo | `ready` subiu nos últimos 15 min e não parou | falta capacidade, antes de virar espera alta |

Tabela: O limite de espera é por fila e é uma decisão de negócio: cinco
minutos para o e-mail de confirmação, uma hora para a NF-e, meio dia para
o marketing.

Em PromQL, a linguagem de consulta do Prometheus, as três primeiras ficam
assim:

```text
rabbitmq_queue_consumers{queue!~".*\\.(retry|error)"} == 0

rabbitmq_queue_messages_ready{queue=~".*\\.error"} > 0

time() - rabbitmq_queue_head_message_timestamp{queue="avisos.pedidos"}
  > 300
```

`=~` casa o rótulo com uma expressão regular, e `!~` exclui: a primeira
regra ignora as filas `.retry` e `.error`, que não têm consumidor de
propósito. Na terceira, `time()` é o instante atual em segundos, e a regra
dispara quando a mensagem mais antiga dos avisos espera mais de cinco
minutos.

:::pitfall
A fila `.retry` sempre tem zero consumidores: ela é uma sala de espera,
não uma fila de trabalho. Um alerta de "fila sem consumidor" que não a
exclua dispara o tempo todo — e um alerta que dispara o tempo todo é
silenciado na primeira semana, junto com os que importavam.
:::

## E as métricas da aplicação?

O broker sabe o que entra e sai das filas; ele não sabe o que aconteceu
**dentro** do `handle()`. Quantas notas foram emitidas na primeira
tentativa, quantas publicações falharam no checkout, quantas repetições o
store de idempotência descartou — isso só a aplicação sabe.

A Mirabel registra esses eventos num coletor interno —
`TelemetryRuntime::metrics()` —, que já sabe se escrever no formato do
Prometheus. Um detalhe decide como usá-lo: o coletor vive **na memória do
processo**. Cada worker tem o seu, e ele zera a cada reinício. Para
métricas de negócio que precisam sobreviver, o lugar é o banco ou um
contador compartilhado, como o repositório companheiro faz; para as de
fila, o lugar é o broker, que já tem todas.

:::milestone
Você tem: as quatro perguntas de uma fila respondidas por um script contra
a API do painel; o ritmo de entrada e saída; as métricas por fila do
RabbitMQ indo para o Prometheus; e quatro alertas — fila sem consumidor,
fila de erro com mensagens, espera alta e fila crescendo.
:::

:::summary
- Profundidade é contagem; espera é tempo. A espera da mensagem mais
	antiga, pelo `head_message_timestamp`, é o que o cliente sente.
- Consumidores em zero é o alerta mais importante; `unacked` alto com
	consumidores ociosos é ack esquecido.
- Se a saída não supera a entrada, a fila nunca esvazia sozinha; o tempo
	para esvaziar é `ready ÷ (saída − entrada)`.
- O RabbitMQ 4 expõe métricas no formato do Prometheus na porta 15692;
	`/metrics/per-object` dá uma série por fila.
- Quatro alertas cobrem o essencial, com o limite de espera decidido por
	fila, como decisão de negócio.
:::

:::exercise level=1
Uma fila mostra `ready` 0, `unacked` 480, `consumers` 2, e o ritmo de
saída está em zero há dez minutos. O que está acontecendo, e como você
confirma?

:::answer
Os consumidores receberam 480 mensagens e não confirmaram nenhuma: ack
esquecido num caminho do código, ou um `handle()` travado esperando algo
que não responde. Com prefetch 1, 480 unacked com dois consumidores seria
impossível — o prefetch está alto, ou não está configurado.

Para confirmar, reinicie um dos consumidores: se as mensagens dele voltam
para `ready`, eram unacked presas a ele. O log do worker, com o
`correlation_id` das mensagens, mostra onde o `handle()` parou.
:::

:::exercise level=2
A fila do fiscal tem 1.800 mensagens, entram 2 por segundo e saem 5. O
Seu Norberto pergunta se as notas de hoje saem hoje. Responda com a
conta, e diga que métrica você acompanharia na próxima hora.

:::answer
A fila esvazia `1800 ÷ (5 − 2) = 600` segundos: dez minutos. Se o ritmo
se mantiver, sim, as notas saem hoje, e com folga.

A métrica a acompanhar é a espera da mais antiga, não o tamanho: ela
precisa **cair** nos próximos minutos. Se a entrada subir para 5 por
segundo — um pico de vendas —, a fila para de encolher; se a SEFAZ ficar
lenta e a saída cair para 2, ela volta a crescer. O `ready` só mostra isso
depois; a espera mostra antes.
:::
