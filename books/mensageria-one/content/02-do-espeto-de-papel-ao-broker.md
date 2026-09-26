---
title: "Do espeto de papel ao broker"
number: 2
slug: do-espeto-de-papel-ao-broker
part: p1
kicker: "Trinta anos de pedidos num prego da cozinha, e o Seu Antenor sempre por último."
goal: >-
  Distinguir fila de pilha, construir a fila mais ingênua possível com
  arquivos, ver os três defeitos dela acontecerem, e usar o vocabulário da
  mensageria — produtor, consumidor, broker, store-and-forward — sabendo de
  onde cada palavra veio.
---

:::story O prego da cozinha
— Como a senhora fazia com os pedidos, antes da loja? — perguntou Júlia.

A Dona Cida apontou para a parede ao lado do fogão. Tinha um prego grande,
de ponta para cima, espetado numa tábua. Em volta dele, trinta anos de
furinhos de papel.

— O telefone tocava, eu anotava no papel e espetava. Quando dava, tirava um
e fazia.

— Tirava qual?

— O de cima, ué. Os outros estão embaixo.

O Kaique, que estava encostado na pia, parou de mexer no celular.

— Então quem ligou primeiro ficava por último.

— O Seu Antenor ligava toda segunda às sete — disse a Dona Cida. — Era
sempre o último que eu fazia. Ele reclamou por vinte anos.

— E a senhora nunca trocou o prego?

— Por quê? Nunca perdi um pedido.
:::

A Dona Cida tem razão no que ela mediu: o prego nunca perdeu um papel.
Ele guardava os pedidos enquanto ela não podia atendê-los, e era isso que
o checkout do capítulo @cap:a-black-friday-que-durou-quatro-horas não
tinha — um lugar para anotar o trabalho que fica para depois.

Mas o prego guarda na ordem errada, e o Seu Antenor passou vinte anos
pagando por isso. Antes de chegar ao RabbitMQ, vale construir o prego em
PHP, ver o que dá errado nele e dar nome a cada defeito. Cada nome é uma
peça que o broker vai resolver.

## Fila e pilha

Duas estruturas guardam coisas para depois, e a diferença entre elas é só
de onde se tira.

Numa **pilha**, o último a entrar é o primeiro a sair: é o prego, o monte de
pratos na pia, o botão de desfazer do editor. O nome técnico é **LIFO**, de
*last in, first out*.

Numa **fila**, o primeiro a entrar é o primeiro a sair: é a fila do banco, a
esteira da fábrica, a caixa onde se põe o papel novo no fundo. O nome
técnico é **FIFO**, de *first in, first out*.

Em PHP, as duas são o mesmo array. O que muda é a função que tira:

```php title="espeto.php" numbered
<?php

$pedidos = [
    'Seu Antenor', 'Dona Lurdes', 'Padaria Estrela', 'Hotel Serra',
];

$espeto = [];
foreach ($pedidos as $pedido) {
    $espeto[] = $pedido;          // espetar: o novo fica por cima
}

$caixa = [];
foreach ($pedidos as $pedido) {
    $caixa[] = $pedido;           // a caixa: o novo vai para o fundo
}

echo 'do espeto: ', array_pop($espeto), PHP_EOL;
echo 'da caixa:  ', array_shift($caixa), PHP_EOL;
```

`$lista[] = $valor` acrescenta um item ao fim do array. `array_pop()` tira
e devolve o **último** item; `array_shift()` tira e devolve o **primeiro**.
`PHP_EOL` é a quebra de linha do sistema operacional.

```text
$ php espeto.php
do espeto: Hotel Serra
da caixa:  Seu Antenor
```

O Hotel Serra ligou por último e foi atendido primeiro. Numa cozinha com um
fogão, isso custa a paciência do Seu Antenor. Num sistema de pedidos, custa
coisa pior: uma pilha sob carga **pode nunca atender o primeiro da fila**,
porque sempre chega alguém novo em cima dele.

Quando se fala em mensageria, "fila" quer dizer FIFO. E ela precisa de mais
duas propriedades que um array não tem.

## A fila mais ingênua possível

Um array vive na memória do processo PHP e morre com ele. O pedido
anotado precisa sobreviver ao fim da requisição, então ele tem que ir para
fora do processo. O lugar mais simples é um arquivo.

A ideia é: quem anota escreve um arquivo numa pasta; quem atende lê o
arquivo mais antigo, faz o trabalho e apaga. Duas peças, e elas já têm
nome.

:::term Produtor e consumidor
**Produtor** é o programa que cria a mensagem e a deixa em algum lugar.
**Consumidor** é o programa que a retira de lá e faz o trabalho. Um não
chama o outro; os dois conversam só com o lugar do meio.
:::

O produtor anota um pedido por execução:

```php title="produtor.php" numbered
<?php

declare(strict_types=1);

$pedido = [
    'id' => (int) $argv[1],
    'produto' => 'geleia de ameixa',
    'quantidade' => 2,
];
$nome = sprintf('fila/%d-%d.json', hrtime(true), $pedido['id']);

file_put_contents($nome, json_encode($pedido));
echo "anotado: {$nome}", PHP_EOL;
```

`hrtime(true)` devolve um relógio em nanossegundos que só anda para a
frente. Usado no começo do nome do arquivo, ele faz a ordem alfabética dos
nomes ser a ordem de chegada — é o que transforma a pasta numa fila, e não
numa pilha. `json_encode()` transforma o array em texto JSON, e
`file_put_contents()` grava esse texto no arquivo.

O consumidor fica rodando, olhando a pasta:

```php title="consumidor.php" numbered
<?php

declare(strict_types=1);

$morrer = ($argv[1] ?? '') === 'morrer';

while (true) {
    $arquivos = glob('fila/*.json');
    if ($arquivos === []) {
        usleep(500_000);
        continue;
    }

    sort($arquivos);
    $arquivo = $arquivos[0];
    $pedido = json_decode(file_get_contents($arquivo), true);

    echo "emitindo NF-e do pedido {$pedido['id']}", PHP_EOL;
    usleep(300_000);

    if ($morrer) {
        exit(1);
    }
    unlink($arquivo);
}
```

`glob()` devolve a lista de arquivos que casam com o padrão. `sort()` põe a
lista em ordem, e o primeiro é o mais antigo. `json_decode(..., true)`
transforma o texto de volta em array. `unlink()` apaga o arquivo. O
`500_000` é só `500000` com um separador para ler melhor — meio segundo de
espera quando a pasta está vazia, para não girar a CPU à toa. O argumento
`morrer` existe para simular uma queda; ele volta daqui a pouco.

Crie a pasta e anote três pedidos:

```text
$ mkdir fila
$ php produtor.php 40117
anotado: fila/36029065926200-40117.json
$ php produtor.php 40118
anotado: fila/36029236708800-40118.json
$ php produtor.php 40119
anotado: fila/36029440240600-40119.json
```

Repare no que acabou de acontecer: três pedidos foram aceitos e **nenhuma
nota fiscal foi emitida**. O produtor terminou em milissegundos. Se a SEFAZ
estivesse fora do ar agora, ninguém ficaria sabendo — os pedidos esperariam
na pasta.

Agora ligue o consumidor e deixe-o esvaziar a pasta:

```text
$ php consumidor.php
emitindo NF-e do pedido 40117
emitindo NF-e do pedido 40118
emitindo NF-e do pedido 40119
```

`Ctrl+C` para parar. A pasta está vazia, e os três pedidos foram atendidos
na ordem em que chegaram. O desenho funciona — num dia bom.

:::term Store-and-forward
Guardar e encaminhar: o intermediário recebe a mensagem, guarda, e só
entrega quando o destino pode receber. Quem manda não precisa que quem
recebe esteja de pé no mesmo instante — que é exatamente o acoplamento
temporal que derrubou o checkout.
:::

## Os três defeitos da pasta

A pasta é uma fila de verdade, e quebra em três lugares. Cada um é uma
peça do RabbitMQ.

### O consumidor que morre no meio

Anote os três pedidos de novo e rode o consumidor com `morrer`. Ele emite
uma nota e cai antes de apagar o arquivo — como um `kill`, uma falta de
memória ou um deploy no meio do trabalho:

```text
$ php consumidor.php morrer
emitindo NF-e do pedido 40117
$ ls fila
36029065926200-40117.json
36029236708800-40118.json
36029440240600-40119.json
```

O arquivo do 40117 continua lá. Ligue o consumidor normal:

```text
$ php consumidor.php
emitindo NF-e do pedido 40117
emitindo NF-e do pedido 40118
emitindo NF-e do pedido 40119
```

A nota do 40117 foi emitida **duas vezes**. O Seu Norberto já avisou o que
acha disso.

Inverter a ordem — apagar antes, emitir depois — troca o defeito: se o
consumidor cair entre o `unlink()` e a emissão, o pedido some sem nota
nenhuma. Não existe ordem certa entre "fiz" e "apaguei" quando os dois
passos são separados e o processo pode morrer entre eles.

O que falta é um jeito de o consumidor dizer "terminei" **depois** do
trabalho, e de o intermediário devolver a mensagem para a fila se esse
"terminei" nunca chegar. No RabbitMQ, isso se chama **ack**, e ele não
elimina a duplicata: ele escolhe, de propósito, entregar de novo em vez de
perder.

### Dois consumidores, o mesmo arquivo

Se a SEFAZ está lenta, o natural é ligar dois consumidores. Os dois fazem
`glob()`, os dois ordenam a lista, os dois pegam o **mesmo** primeiro
arquivo e emitem a mesma nota. Nada na pasta impede isso: ler um arquivo
não o tira da vista dos outros.

O intermediário precisa **entregar** cada mensagem a um consumidor só, e
não deixá-la exposta para quem chegar primeiro. É a diferença entre uma
pasta compartilhada e alguém que distribui os papéis.

### Quem mais precisa saber?

O pedido pago interessa à nota fiscal, à etiqueta, ao e-mail e ao estoque.
Com a pasta, ou o produtor escreve quatro arquivos em quatro pastas — e
passa a conhecer cada interessado pelo nome —, ou os quatro consumidores
disputam o mesmo arquivo, e só um deles atende.

O que falta é separar **publicar** de **entregar**: o produtor diz "um
pedido foi pago" uma vez, e o intermediário decide quantas cópias fazer e
para quem. No RabbitMQ, essa decisão mora no **exchange**.

| O defeito da pasta | O que falta | O nome no RabbitMQ |
|---|---|---|
| consumidor morre entre fazer e apagar | confirmar depois do trabalho | ack |
| dois consumidores leem o mesmo arquivo | entregar cada mensagem a um só | fila com consumidores concorrentes |
| o produtor conhece cada interessado | publicar uma vez, copiar para quem quiser | exchange e binding |
| o consumidor pergunta a cada meio segundo | ser avisado quando chega | consumo por push |

Tabela: A pasta tem os conceitos certos e nenhuma das garantias. Um broker
é a pasta com as garantias.

:::term Broker
O intermediário de mensagens: um servidor que recebe mensagens de
produtores, guarda, e entrega a consumidores segundo regras. O RabbitMQ é
um broker. A palavra vem do inglês para "corretor" — quem fica no meio de
uma negociação para que as partes não precisem se encontrar.
:::

## Cinquenta anos de gente com o mesmo problema

A pasta com arquivos não é uma ideia boba; é a ideia de todo mundo. O
problema de mandar uma mensagem para quem pode não estar lá é mais velho
que o computador, e a solução foi reinventada várias vezes, sempre com um
intermediário que guarda.

:::diagram type="timeline" caption="De onde vêm as palavras que o RabbitMQ usa."
width: 112
events:
  - { year: "1850", text: "Telégrafo: estações que recebem, guardam e retransmitem — store-and-forward" }
  - { year: "1986", text: "Ericsson cria o Erlang para centrais telefônicas que não podem parar", mark: true }
  - { year: "1993", text: "IBM MQSeries: filas de mensagem para bancos e mainframes" }
  - { year: "1998", text: "JMS: uma API comum em Java, mas cada fornecedor com seu protocolo" }
  - { year: "2003", text: "John O'Hara, no JPMorgan, começa o AMQP: um protocolo aberto", mark: true }
  - { year: "2007", text: "RabbitMQ, da LShift e da CohesiveFT, escrito em Erlang", mark: true }
  - { year: "2010", text: "SpringSource, da VMware, compra a Rabbit Technologies" }
  - { year: "2011", text: "O LinkedIn abre o código do Kafka: um log, não uma fila" }
  - { year: "2019", text: "RabbitMQ 3.8 traz as quorum queues, replicadas por consenso" }
  - { year: "2024", text: "RabbitMQ 4.0: sem espelhamento clássico, AMQP 1.0 nativo" }
:::

### Os bancos e o protocolo de cada um

Nos anos 1990, bancos e bolsas já tinham o problema do checkout da Doce
Mirabel em escala muito maior: sistemas que precisavam trocar mensagens sem
depender de estarem todos de pé ao mesmo tempo. A IBM vendia o MQSeries, e
havia outros produtos, todos bons, todos caros.

O defeito não era técnico. Cada produto falava o **seu** protocolo — o
formato dos bytes que viajam pela rede. Em 1998, o mundo Java padronizou
uma API, a JMS: o código ficava igual, mas por baixo cada fornecedor
continuava com o seu protocolo. Trocar de fornecedor era trocar de
cliente, de servidor e de contrato, e dois bancos que usavam produtos
diferentes não conversavam sem uma ponte.

:::history
Em 2003, John O'Hara, engenheiro do JPMorgan em Londres, começou a desenhar
um protocolo de mensageria **aberto**: um formato de bytes publicado, que
qualquer um pudesse implementar, para que o cliente de um fornecedor
falasse com o servidor de outro. Ele se chamou **AMQP**, *Advanced Message
Queuing Protocol*.

O banco contratou uma empresa para escrever a primeira implementação e,
depois, reuniu um consórcio que chegou a mais de vinte empresas — outros
bancos, a Cisco, a Microsoft, a Red Hat. A versão que o RabbitMQ fala como
língua nativa até hoje é a **0-9-1**, de 2008. Uma versão bem diferente, a
1.0, virou padrão da OASIS em 2012 e norma ISO depois.
:::

O ponto do AMQP não era ser mais rápido que o MQSeries. Era que a
**mensagem** e o **protocolo** deixassem de pertencer a quem vendia o
servidor — a mesma ideia que torna possível, no fim deste livro, um
consumidor Java ler o que um produtor PHP publicou.

### Um coelho escrito na língua dos telefones

Em 2007, duas empresas inglesas, a LShift e a CohesiveFT, fundaram a
Rabbit Technologies e publicaram uma implementação do AMQP com código
aberto: o **RabbitMQ**. Três anos depois, a SpringSource — a empresa do
Spring, que era da VMware — comprou a Rabbit. O projeto passou pela Pivotal
e voltou para a VMware, que em 2023 foi comprada pela Broadcom. O código
continua aberto.

A escolha técnica mais importante foi a linguagem. O RabbitMQ é escrito em
**Erlang**, criada na Ericsson a partir de 1986 para programar centrais
telefônicas: sistemas com milhares de conversas simultâneas, em que uma
linha com defeito não pode derrubar as outras e o software é atualizado sem
desligar a central. Um broker de mensagens tem exatamente esse formato —
milhares de conexões, filas independentes, e nenhuma delas pode levar as
outras junto.

:::trivia
A linguagem Erlang tem o nome de Agner Krarup Erlang, um matemático
dinamarquês que, por volta de 1909, trabalhava para a companhia telefônica
de Copenhague e quis calcular quantas linhas eram necessárias para que as
ligações não esperassem demais. As fórmulas dele fundaram a **teoria das
filas**, e a unidade de tráfego telefônico se chama *erlang* até hoje.

A homenagem da Ericsson foi de propósito. O que ninguém planejou foi o
resto: vinte anos depois, um dos brokers de mensagem mais usados do mundo seria
escrito numa linguagem batizada com o nome do pai da teoria das filas.
:::

### E o Kafka?

Em 2011, o LinkedIn abriu o código do **Kafka**, e ele aparece em toda
conversa sobre mensageria — o Rafa vai trazê-lo antes do fim do livro. A
diferença essencial cabe em duas frases.

Numa **fila**, a mensagem existe para ser consumida: quando o consumidor
confirma, ela sai. Num **log** como o do Kafka, a mensagem é gravada e fica;
cada leitor guarda até onde já leu, e vários leitores podem reler o mesmo
trecho. Um é uma caixa de pedidos; o outro é um livro-caixa. Os dois são
úteis, e o problema da Doce Mirabel — trabalho que alguém precisa fazer uma
vez — tem o formato de uma caixa.

## O que a fila compra

O Rafa pediu "uma fila" achando que ela deixaria a loja mais rápida. Ela
deixa o checkout mais rápido, mas por um motivo específico, e o motivo
importa mais que o efeito: a fila **desacopla no tempo**. O checkout anota o
trabalho e responde; quem emite a nota faz isso quando pode. Se a SEFAZ
sumir por quarenta minutos, o que cresce é a fila, não a página de erro.

Ela não compra de graça. A pasta já mostrou o preço: agora existe um
terceiro sistema que precisa estar de pé, o trabalho acontece depois e
pode acontecer duas vezes, e alguém precisa saber quando a fila cresce
demais. Cada um desses custos tem uma resposta no RabbitMQ, e nenhuma delas
é automática.

:::key
Uma fila não faz o trabalho andar mais rápido. Ela deixa o **aceitar**
acontecer sem esperar o **atender** — e transforma "o serviço caiu" em "a
fila cresceu", que é um problema que se resolve depois, em vez de um que o
cliente vê agora.
:::

:::summary
- Pilha (LIFO) atende o último que chegou; fila (FIFO) atende o primeiro. O
	espeto da Dona Cida é uma pilha, e sob carga uma pilha pode nunca atender
	o mais antigo.
- Uma fila de verdade precisa sobreviver ao processo que a criou: produtor
	grava, consumidor lê e apaga — store-and-forward.
- A pasta de arquivos tem os três defeitos que um broker resolve: duplicar
	ou perder quando o consumidor cai (ack), dois consumidores pegando o mesmo
	item (entrega a um só) e o produtor precisando conhecer cada interessado
	(exchange).
- O AMQP nasceu em 2003 no JPMorgan para que o protocolo deixasse de
	pertencer ao fornecedor; o RabbitMQ, de 2007, o implementa em Erlang.
- Uma fila desacopla no tempo: a queda de um serviço vira fila crescendo,
	não erro para o cliente — ao custo de um sistema a mais e de trabalho que
	pode acontecer duas vezes.
:::

:::exercise level=1
Troque `array_shift()` por `array_pop()` no consumidor do espeto e diga,
sem rodar, qual pedido sai primeiro. Depois explique por que o `sort()` do
`consumidor.php` é o que faz a pasta ser uma fila e não uma pilha.

:::answer
Com `array_pop()`, sai o Hotel Serra: o último a entrar. O array é o mesmo;
só a ponta de onde se tira mudou.

No `consumidor.php`, os nomes começam com `hrtime(true)`, que cresce a cada
chamada. O `sort()` põe os nomes em ordem crescente, então `$arquivos[0]` é
sempre o mais antigo — FIFO. Se o código usasse `rsort()`, que ordena ao
contrário, ou pegasse o último elemento da lista, a pasta viraria o prego da
Dona Cida.
:::

:::exercise level=2
Abra dois terminais, anote dez pedidos e rode dois consumidores normais ao
mesmo tempo. Conte quantas notas foram emitidas. Depois proponha uma
mudança no `consumidor.php` que impeça dois consumidores de processarem o
mesmo arquivo, usando `rename()` — que, no mesmo disco, é atômico: ou
acontece inteiro ou não acontece.

:::answer
Com dois consumidores, o número de notas passa de dez com frequência,
porque os dois leem o mesmo `$arquivos[0]` antes de qualquer um apagá-lo.
Em alguns casos, um deles tenta apagar um arquivo que o outro já apagou e o
`unlink()` emite um aviso.

A correção é **reivindicar** o arquivo antes de trabalhar, movendo-o para
uma pasta só daquele consumidor:

```php
$meu = 'trabalhando/' . getmypid() . '-' . basename($arquivo);
if (!@rename($arquivo, $meu)) {
    continue; // outro consumidor chegou primeiro
}
$pedido = json_decode(file_get_contents($meu), true);
// ... emite a nota ...
unlink($meu);
```

Só um `rename()` consegue mover o arquivo; o outro falha e tenta o próximo.
`getmypid()` devolve o número do processo, e o `@` suprime o aviso da
falha, que aqui é esperada.

Repare no que sobrou: se o consumidor morrer depois do `rename()`, o
arquivo fica em `trabalhando/` para sempre, e ninguém o devolve à fila.
Resolver isso direito — perceber que o consumidor morreu e devolver o
trabalho — é justamente o que um broker faz quando uma conexão cai sem ack.
:::
