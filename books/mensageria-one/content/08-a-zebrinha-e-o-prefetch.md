---
title: "A Zebrinha e o prefetch"
number: 8
slug: a-zebrinha-e-o-prefetch
part: p2
kicker: "Uma impressora nova, dez vezes mais rápida, passou oito segundos parada enquanto a velha trabalhava."
goal: >-
  Pôr dois consumidores na mesma fila, ver o rodízio cego entregar metade do
  trabalho ao mais lento, usar basic_qos para limitar quantas mensagens cada
  consumidor segura, e escolher um prefetch com critério.
---

:::story A segunda impressora
Em outubro, a Denise ganhou uma segunda impressora. Veio de um fornecedor
de embalagens, como brinde, e imprimia uma etiqueta a cada dois décimos de
segundo.

— Não vou aposentar a Zebrinha — avisou ela, antes que alguém perguntasse.

— Ninguém falou nisso — disse Júlia. — As duas vão consumir a mesma fila.
Quem estiver livre, imprime.

No primeiro teste, o Kaique publicou vinte pedidos e ficou olhando as duas
impressoras. A nova cuspiu dez etiquetas em dois segundos e parou. A
Zebrinha seguiu imprimindo, uma a uma, com o ruído de sempre.

— A nova quebrou? — perguntou a Denise.

— Não — disse o Kaique, olhando o painel. — Ela terminou a parte dela.

— E por que ela não ajuda a Zebrinha?

— Porque os outros dez já estão com a Zebrinha.

A Denise olhou para a Zebrinha, que continuava imprimindo.

— Ela nunca pediu ajuda mesmo.
:::

Dois consumidores numa fila é o jeito mais simples de dobrar a capacidade
de trabalho, e o exercício do capítulo
@cap:conexao-canal-e-a-primeira-mensagem mostrou que o RabbitMQ reveza as
mensagens entre eles. O que ele não mostrou é **quando** o revezamento
acontece — e a resposta explica por que a impressora nova ficou parada.

## A bancada

O experimento usa uma fila `expedicao.etiquetas`, um publicador de lote e
uma impressora simulada que recebe um nome, o tempo por etiqueta e,
opcionalmente, um prefetch. A Zebrinha simulada leva 0,9 segundo — a real
leva o dobro; a simulação roda em câmera rápida para o experimento caber
em poucos segundos.

```php title="impressora.php" numbered
<?php

declare(strict_types=1);

use PhpAmqpLib\Exception\AMQPTimeoutException;
use PhpAmqpLib\Message\AMQPMessage;

require __DIR__ . '/conexao.php';

[, $nome, $segundos] = $argv;
$prefetch = (int) ($argv[3] ?? 0);
$impressas = 0;
$inicio = null;
$ultima = null;

if ($prefetch > 0) {
    $canal->basic_qos(0, $prefetch, false);
}

$imprimir = function (AMQPMessage $mensagem) use (
    $segundos, &$impressas, &$inicio, &$ultima,
): void {
    $inicio ??= microtime(true);
    usleep((int) ($segundos * 1_000_000));
    $mensagem->ack();
    $impressas++;
    $ultima = microtime(true);
};

$canal->basic_consume(
    'expedicao.etiquetas', '', false, false, false, false, $imprimir,
);

while ($canal->is_consuming()) {
    try {
        $canal->wait(null, false, 2);
    } catch (AMQPTimeoutException) {
        break;
    }
}
printf(
    "%s: %d etiquetas, a última em %.1f s\n",
    $nome, $impressas, $ultima - $inicio,
);
```

`$inicio ??= microtime(true)` só atribui se `$inicio` ainda for `null`:
guarda o instante da **primeira** etiqueta e nunca mais muda. O laço
termina quando passam dois segundos sem mensagem nova, e o script imprime
quantas etiquetas fez e quanto tempo levou da primeira à última. O
`conexao.php` é o do capítulo anterior, declarando `expedicao.etiquetas`
em vez de `fiscal.pedidos`, e o `lote.php` publica nela quantos pedidos o
argumento pedir.

## O rodízio cego

Em dois terminais, ligue as duas impressoras; num terceiro, publique vinte
pedidos:

```text
$ php impressora.php zebrinha 0.9
$ php impressora.php nova 0.1
$ php lote.php 20
```

Quando tudo termina:

```text
zebrinha: 10 etiquetas, a última em 9.0 s
nova: 10 etiquetas, a última em 1.0 s
```

Dez para cada. A nova terminou a sua parte em um segundo e passou oito
parada; a Zebrinha levou nove. O lote inteiro demorou o tempo da
impressora **mais lenta**, como se a nova nem existisse.

O motivo é o mesmo buffer que o capítulo sobre ack mostrou. O RabbitMQ
reveza as mensagens **no momento de entregar**, não no momento em que cada
consumidor fica livre. Os vinte pedidos chegaram de uma vez; o broker
mandou o primeiro para a Zebrinha, o segundo para a nova, o terceiro para
a Zebrinha — e em milissegundos as vinte já estavam distribuídas, dez em
cada buffer. Olhe a fila durante o teste: *Ready* zero e *Unacked* alto,
com a nova ociosa.

:::key
Sem limite, o broker entrega a cada consumidor tudo o que ele aceitar
receber. O rodízio divide as mensagens **por quantidade**, e não por
capacidade: o consumidor mais lento recebe a mesma parte que o mais
rápido, e o lote termina no ritmo dele.
:::

## Prefetch

O conserto é dizer ao broker quantas mensagens cada consumidor pode ter
**sem ack** ao mesmo tempo. Esse número é o **prefetch**, e é definido no
canal com `basic_qos`:

```php
$canal->basic_qos(0, 1, false);
```

Os três argumentos são o tamanho máximo em bytes (`0`, sem limite — o
RabbitMQ não implementa esse), a quantidade de mensagens (`1`) e se o
limite vale para o canal inteiro ou por consumidor (`false`, por
consumidor, que é o que se quer quase sempre). Ele precisa ser chamado
**antes** de `basic_consume`.

Com prefetch 1, o broker entrega uma mensagem e espera o ack antes de
mandar a próxima para aquele consumidor. Quem está livre recebe; quem está
ocupado espera. Rode de novo, com o terceiro argumento:

```text
$ php impressora.php zebrinha 0.9 1
$ php impressora.php nova 0.1 1
$ php lote.php 20
```

```text
zebrinha: 2 etiquetas, a última em 1.8 s
nova: 18 etiquetas, a última em 1.8 s
```

Dezoito para a nova, duas para a Zebrinha, e o lote inteiro em 1,8
segundo — cinco vezes mais rápido que antes, com as mesmas impressoras. A
divisão agora acompanha a capacidade real de cada uma, sem ninguém
precisar saber qual é a mais rápida.

:::term Prefetch
O número máximo de mensagens entregues e ainda sem ack que um consumidor
pode ter. Com prefetch 1, o consumidor segura uma de cada vez; com 50,
segura até 50 no buffer. Sem prefetch, não há limite — e o capítulo sobre
ack mostrou o que acontece com esse buffer quando o consumidor cai.
:::

Repare que o prefetch também resolve, de lado, o problema do capítulo
anterior: com prefetch 1, um consumidor que cai leva no máximo **uma**
mensagem para a reentrega, e não a fila inteira.

## Que número usar

Prefetch 1 é o mais justo e o mais lento por mensagem. Entre o ack de uma
mensagem e a chegada da próxima existe uma ida e volta pela rede — em
geral, menos de um milissegundo numa rede local. Para a Zebrinha, que leva
1,8 segundo por etiqueta, isso é nada. Para um consumidor que grava um
contador em um milissegundo, é metade do tempo.

| Trabalho por mensagem | Prefetch razoável | Por quê |
|---|---|---|
| segundos (NF-e, etiqueta, e-mail) | 1 | a ida e volta é irrelevante; a justiça importa |
| dezenas de milissegundos (gravar no banco) | 10 a 50 | esconde a latência sem acumular muito |
| menos de um milissegundo (contadores, métricas) | 100 a 300 | a rede passa a ser o gargalo |

Tabela: Ponto de partida, não regra. O número certo se mede com a carga
de verdade.

Para a Doce Mirabel, todo trabalho é da primeira linha: NF-e, etiqueta,
estoque no ERP, e-mail. Prefetch 1 em todos os consumidores. Um número
maior só se paga quando alguém medir e mostrar.

:::pitfall
Prefetch alto num consumidor lento é o rodízio cego de volta, com outro
nome. Um consumidor de NF-e com prefetch 100 segura cem pedidos no buffer
enquanto a SEFAZ responde um por segundo — e os outros consumidores ficam
sem trabalho, olhando uma fila com *Ready* zero.
:::

:::story A velocidade, de novo
A Denise assistiu ao segundo teste em pé, de braços cruzados.

— Agora a nova faz quase tudo.

— Faz o que dá conta — disse Júlia. — A Zebrinha pega quando está livre.

— E se a nova quebrar?

— A Zebrinha faz tudo sozinha, no ritmo dela. Ninguém precisa mudar nada.

A Denise ficou um tempo olhando as duas.

— Então agora a velocidade é a das duas juntas.

— É.

— Ela não vai gostar.
:::

:::milestone
Você tem: consumidores concorrentes na mesma fila, cada um com
`basic_qos(0, 1, false)`, recebendo trabalho na medida em que termina o
anterior. O lote termina no ritmo da soma dos consumidores, não no do mais
lento.
:::

:::summary
- Vários consumidores numa fila recebem as mensagens em rodízio, no momento
	da entrega — e, sem limite, a entrega é tudo de uma vez.
- Sem prefetch, o consumidor lento recebe a mesma parte que o rápido e o
	lote termina no ritmo dele; no experimento, 9 segundos contra 1.
- `basic_qos(0, N, false)`, antes do `basic_consume`, limita a N as
	mensagens sem ack por consumidor.
- Com prefetch 1, o trabalho se divide pela capacidade real: 18 contra 2, e
	o lote em 1,8 segundo.
- Trabalho de segundos pede prefetch 1; valores altos só para trabalho de
	milissegundos, e só depois de medir.
:::

:::exercise level=1
Rode o experimento com prefetch 5 nas duas impressoras. Antes de rodar,
estime quantas etiquetas cada uma faz e quanto tempo o lote leva.

:::answer
Na entrega inicial, cada impressora recebe cinco: dez pedidos saem de uma
vez, cinco para cada. A nova confirma as suas depressa e vai recebendo o
resto. A Zebrinha confirma a primeira aos 0,9 segundo — quando a nova ainda
não esvaziou a fila — e ganha mais uma. Na bancada deste capítulo, o
resultado foi:

```text
zebrinha: 6 etiquetas, a última em 5.4 s
nova: 14 etiquetas, a última em 1.4 s
```

O lote levou 5,4 segundos: seis etiquetas da Zebrinha. Melhor que os 9
sem prefetch, pior que o 1,8 do prefetch 1.

O número exato varia de execução para execução. O padrão não: com prefetch
N, o consumidor mais lento segura até N mensagens que outro faria mais
depressa.
:::

:::exercise level=2
A equipe de avisos quer um consumidor que manda e-mail usando um provedor
que aceita 10 envios por segundo, e pergunta se prefetch 10 faz o
consumidor mandar 10 por segundo. Responda e proponha o que resolve.

:::answer
Não. Prefetch limita quantas mensagens o consumidor **segura** sem ack, não
quantas ele **processa** por segundo. Se cada envio leva 50 ms e o código
manda um de cada vez, o consumidor faz cerca de 20 por segundo com
qualquer prefetch — e estoura o limite do provedor.

Ritmo se controla no próprio consumidor: medir o tempo entre envios e
esperar o que faltar para respeitar 100 ms, ou usar um limitador de taxa.
Se um consumidor não der conta, aumentar a vazão é pôr mais consumidores,
cada um com o seu limite somando no máximo 10 por segundo. O prefetch
continua em 1, para que nenhum deles acumule e-mails no buffer.
:::
