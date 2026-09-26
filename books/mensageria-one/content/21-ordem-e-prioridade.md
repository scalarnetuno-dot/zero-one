---
title: "Ordem, prioridade e a fila que nunca esvazia"
number: 21
slug: ordem-e-prioridade
part: p5
kicker: "O cancelamento chegou depois do pagamento e foi processado antes. A nota saiu dois segundos mais tarde, para um pedido que não existia mais."
goal: >-
  Saber o que o RabbitMQ garante de ordem e o que desfaz essa garantia,
  escrever consumidores que não dependem da ordem de chegada, usar single
  active consumer quando a ordem é inegociável, e separar urgências com
  filas de prioridade ou, de preferência, com filas diferentes.
---

:::story O espeto, de novo
Em novembro, o Seu Antenor ligou para cancelar um pedido que tinha feito
dez minutos antes. O Kaique cancelou no painel da loja. No dia seguinte,
o Seu Norberto mandou um print: uma nota fiscal emitida para o pedido
cancelado.

— O cancelamento foi feito antes da nota — disse o Kaique. — Eu vi.

— O cancelamento foi **processado** antes — disse a Júlia, com o log
aberto. — O pagamento chegou primeiro, falhou por causa da SEFAZ e foi
para o retry. Enquanto ele esperava, o cancelamento chegou, e não tinha
nota para cancelar. Dois segundos depois, o pagamento voltou e emitiu.

A Dona Cida, que ouvia da cozinha, riu baixinho.

— O Seu Antenor de novo por último.

— Dessa vez ele foi o primeiro — disse o Kaique. — Por isso deu errado.
:::

O espeto da Dona Cida atendia o mais novo primeiro, e o capítulo
@cap:do-espeto-de-papel-ao-broker trocou o espeto por uma fila, que
atende o mais antigo. A fila do RabbitMQ é FIFO — mas "a fila é FIFO" e
"as mensagens são processadas na ordem em que foram publicadas" são
frases diferentes, e a distância entre elas é onde a nota do Seu Antenor
nasceu.

## O que o RabbitMQ garante

A garantia é estreita e precisa: mensagens publicadas **por um mesmo
canal**, que chegam **a uma mesma fila**, são **entregues** nessa ordem.
Tudo o que acontece depois da entrega pode embaralhar:

| O que acontece | Por que embaralha |
|---|---|
| dois ou mais consumidores | cada um processa no seu ritmo; o segundo pode terminar antes do primeiro |
| retry com espera | a mensagem que falhou sai da fila e volta depois das que chegaram atrás dela |
| `nack` com requeue | a mensagem volta, mas as outras já foram entregues |
| publicação por canais diferentes | dois produtores não têm ordem entre si |

Tabela: A Doce Mirabel tem as quatro: consumidores concorrentes, retry,
e o checkout e o painel publicando por conexões diferentes.

A cena reproduz em três linhas de log. O fiscal escuta `pedido.pago` e
`pedido.cancelado`, com retry de dois segundos, e a SEFAZ falha na
primeira tentativa:

```text
00:25:16 pago 40117: SEFAZ fora
00:25:16 cancelado 40117: nenhuma nota para cancelar
00:25:18 pago 40117: NF-e emitida
```

Um consumidor só, e a ordem quebrou mesmo assim. O pagamento foi
publicado primeiro, entregue primeiro — e processado por último, porque
passou dois segundos na `.retry`.

## Não depender da ordem

Na maioria dos casos, a saída não é forçar a ordem: é escrever o
consumidor de modo que ela não importe. O consumidor guarda o **estado**
do que já viu, e cada mensagem é tratada à luz desse estado, não da
anterior.

Com a tabela `notas` do capítulo @cap:idempotencia-o-pedido-40117, o
cancelamento que chega antes do pagamento deixa uma marca:

```php
// pedido.cancelado
$marca = $this->banco->prepare(
    "INSERT OR IGNORE INTO notas VALUES (?, 'cancelado')",
);
$marca->execute([$pedido]);

if ($marca->rowCount() === 0) {
    // já existe nota emitida ou em emissão: é preciso cancelá-la
    throw new \RuntimeException("nota do {$pedido} a cancelar");
}
```

`INSERT OR IGNORE` não reclama se a chave já existir, e `rowCount()`
diz quantas linhas o comando realmente gravou: 1 se o cancelamento chegou
primeiro, 0 se já havia uma nota. No primeiro caso, o pagamento que vier
depois tenta reservar o pedido, encontra a linha `cancelado` e é recusado
pela mesma chave primária que já impedia notas duplicadas — nenhuma nota
sai. No segundo, a nota existe ou está saindo, e cancelá-la é outra
operação na SEFAZ; a exceção manda a mensagem para o retry e, se ninguém
resolver, para a fila de erro, com o motivo escrito.

:::key
Um consumidor que depende da ordem de chegada quebra com retry, com
consumidores concorrentes e com produtores diferentes — isto é, em
produção. Um consumidor que decide pelo **estado** do que já processou
funciona em qualquer ordem, e é mais fácil de testar: basta publicar as
mensagens embaralhadas.
:::

Quando o estado não basta — duas atualizações de endereço do mesmo
cliente, por exemplo —, o evento carrega uma **versão** ou o momento em
que o fato aconteceu, e o consumidor ignora a mensagem que for mais velha
do que a última que ele aplicou.

## Quando a ordem é inegociável

Há casos raros em que a ordem precisa ser garantida no processamento, e
não só na entrega — o saldo de estoque de um produto, em que baixas e
reposições precisam ser aplicadas uma a uma, na sequência. O RabbitMQ
oferece para isso o **single active consumer**: vários consumidores se
inscrevem na fila, mas só **um** recebe mensagens de cada vez; os outros
ficam de reserva e assumem se ele cair.

É um argumento da fila, `x-single-active-consumer`. Com dois consumidores,
A e B, e cinco baixas de estoque — as três primeiras publicadas com os
dois no ar, as duas últimas depois de A sair:

```text
A: baixa 1
A: baixa 2
A: baixa 3
B: baixa 4
B: baixa 5
```

B estava conectado o tempo todo e não recebeu nada enquanto A estava no
ar. Quando A saiu, B assumiu, na ordem.

O preço é o óbvio: a fila anda na velocidade de **um** consumidor. Não
adianta pôr dez — nove esperam. E a ordem ainda quebra com retry: se a
baixa 2 falhar e for para a `.retry`, a 3 é processada antes. Para ordem
estrita de verdade, a falha de uma mensagem precisa parar a fila, não
desviar a mensagem — o que é um desenho diferente, e raramente o que se
quer.

A Mirabel declara a fila com os argumentos dela — dead-letter para o
retry — e não expõe `x-single-active-consumer`. Uma fila que precisa dele
é declarada antes, com a `php-amqplib` ou pelo painel, e o worker a
encontra pronta. Como os argumentos de uma fila existente não mudam, a
declaração do worker precisa ter exatamente os mesmos argumentos, ou o
broker recusa com 406.

## Prioridade

A outra face da ordem é a urgência. A fila de avisos mistura o e-mail de
"seu pedido foi confirmado", que o cliente espera agora, com a newsletter
de Natal, que pode sair amanhã. Numa segunda de promoção, trinta mil
newsletters na frente de um e-mail de confirmação é a história do
capítulo @cap:medir-a-fila de novo.

O RabbitMQ tem **filas de prioridade**: com o argumento `x-max-priority`,
a fila aceita mensagens com a propriedade `priority`, e entrega as de
prioridade maior primeiro. Com cinco avisos publicados sem consumidor —
três de marketing com prioridade 1, dois de pedido pago com prioridade 5 —
e lidos depois:

```text
2 pedido pago
4 pedido pago
0 marketing
1 marketing
3 marketing
```

Os de pedido pago furaram a fila, e dentro de cada prioridade a ordem de
chegada se manteve.

Funciona, e tem dois limites. A prioridade só reordena mensagens que
estão **esperando** na fila: com prefetch alto, as de marketing já estão
no buffer do consumidor e não são ultrapassadas. E uma fila com
prioridade continua sendo **uma** fila, com um ritmo: se o marketing não
parar de chegar, a prioridade 1 pode esperar para sempre.

## Filas por urgência

Para a Doce Mirabel, a solução mais simples é a que não usa recurso
nenhum do broker: **filas diferentes**. O aviso transacional e o
marketing têm routing keys diferentes — `aviso.pedido.*` e
`aviso.marketing.*` —, filas diferentes e workers diferentes, cada um com
o número de consumidores que a urgência pede.

| Critério | Fila com prioridade | Filas separadas |
|---|---|---|
| urgente passa na frente | sim, se estiver esperando | sim, sempre: tem consumidor próprio |
| o menos urgente pode esperar para sempre | pode | não, se tiver consumidor |
| medir cada urgência | uma métrica misturada | uma fila, uma métrica |
| suporte na Mirabel | não | sim, é só outro worker |

Tabela: Prioridade é um remendo dentro de uma fila; separação é um
desenho.

:::pitfall
Filas separadas por urgência só funcionam se cada uma tiver consumidor.
Uma fila de marketing sem worker nenhum acumula para sempre — e a
newsletter de Natal sai em março, sem erro em lugar nenhum.
:::

:::milestone
Você tem: consumidores do fiscal que decidem pelo estado do pedido e não
pela ordem de chegada; o cancelamento que chega antes do pagamento
impedindo a nota; single active consumer reservado para os raros casos de
ordem estrita; e avisos transacionais separados do marketing, em filas e
workers próprios.
:::

:::summary
- O RabbitMQ entrega na ordem de publicação dentro de uma fila; retry,
	requeue, consumidores concorrentes e produtores diferentes embaralham o
	processamento.
- O consumidor robusto decide pelo estado do que já processou — ou por
	versões nos eventos —, e não pela ordem de chegada.
- `x-single-active-consumer` garante um consumidor ativo por vez, ao preço
	da vazão de um; retry ainda quebra a ordem.
- Filas de prioridade (`x-max-priority`) reordenam o que está esperando;
	o menos urgente pode esperar para sempre.
- Separar urgências em filas e workers diferentes é mais simples de medir
	e de garantir.
:::

:::exercise level=1
O fiscal roda com três consumidores e sem retry nenhum. O checkout publica
`pedido.pago` e, um segundo depois, o cliente cancela e o painel publica
`pedido.cancelado`. É possível o cancelamento ser processado antes do
pagamento?

:::answer
Sim. O pagamento é entregue ao consumidor A, que começa a emitir a nota
e espera a SEFAZ. O cancelamento é entregue ao consumidor B, que está
livre e o processa em milissegundos — antes de A terminar. Sem retry, a
ordem de entrega é a de publicação; a de processamento, não, porque são
dois processos em paralelo.

Com a reserva na tabela `notas`, o resultado ainda é correto nos dois
casos. Se o cancelamento chega antes de A reservar, ele grava
`cancelado`, e a reserva de A é recusada: nenhuma nota. Se A já tinha
reservado, o cancelamento não consegue gravar, e vai para o retry dizendo
que há uma nota a cancelar.
:::

:::exercise level=2
O estoque da fábrica recebe `estoque.baixado` e `estoque.reposto` de
vários produtos. Proponha um desenho em que as mensagens de um mesmo
produto sejam aplicadas em ordem, sem que a fila inteira ande na
velocidade de um consumidor.

:::answer
Partir a fila por produto: várias filas — `estoque.p0` a `estoque.p7`, por
exemplo —, cada uma com single active consumer. O produtor escolhe a fila
pelo código do produto, com um cálculo fixo, como o resto da divisão de um
hash do código por 8, e publica com a routing key correspondente. Todas as
mensagens de um produto caem sempre na mesma fila, e são aplicadas em
ordem por um consumidor; produtos diferentes andam em paralelo, em até oito
filas.

O RabbitMQ tem um tipo de exchange para exatamente isso, o *consistent
hash exchange*, num plugin que vem com o broker. O custo é saber que a
ordem vale **por produto**, e só enquanto nenhuma mensagem for para o
retry.
:::
