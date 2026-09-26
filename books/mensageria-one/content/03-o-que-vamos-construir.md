---
title: "O que vamos construir"
number: 3
slug: o-que-vamos-construir
part: p1
kicker: "Uma etiqueta a cada 1,8 segundo, nem um décimo mais rápido — e o primeiro publish do livro é um clique."
goal: >-
  Conhecer a arquitetura que o livro vai construir, subir o RabbitMQ com
  Docker, reconhecer as partes do painel de gerenciamento e publicar e
  consumir a primeira mensagem sem escrever código.
---

:::story A velocidade
A expedição fica no fundo da fábrica, depois da linha de envase, numa sala
que cheira a papelão e a açúcar queimado. A Denise mostrou a impressora
como quem apresenta um parente.

— Essa é a Zebrinha.

Uma impressora térmica de etiquetas, do tamanho de uma caixa de sapato,
com um adesivo de zebra colado na tampa. Ela imprimiu uma etiqueta de
teste, cortou, e ficou em silêncio de novo.

— Uma a cada um vírgula oito segundo — disse a Denise. — Eu cronometrei.

— E se chegar mais pedido que isso? — perguntou Júlia.

— Chega. Na Black Friday chegaram dois mil em uma hora.

O Kaique fez a conta de cabeça e depois no celular.

— Dá umas duas mil etiquetas por hora, no máximo. Então empatou.

— Empatou das dez às onze — disse a Denise. — Das onze ao meio-dia
chegaram cinco mil.

— E aí?

— Aí o sistema da agência mandava imprimir do mesmo jeito. A Zebrinha
engasgou, travou, e eu passei a tarde imprimindo etiqueta pelo site da
transportadora, uma por uma, com o mouse.

— Não dava para comprar outra impressora?

A Denise olhou para ele como se ele tivesse sugerido comprar outra avó.

— A impressora não é lenta. Ela é a velocidade.
:::

A Denise acabou de descrever, sem nenhuma palavra técnica, o problema mais
comum de um sistema com fila: um **consumidor mais lento que o produtor**.
Na hora do pico, os pedidos chegam mais rápido do que a Zebrinha imprime.
Não há o que fazer com a velocidade dela; o que dá para fazer é não
empurrar etiquetas para dentro dela mais depressa do que ela aguenta, e
deixar o resto **esperando em algum lugar que não esqueça**.

Esse lugar é o que este capítulo põe de pé.

## O desenho do fim

O checkout, ao fim do livro, faz uma coisa só: grava o pedido e publica que
ele aconteceu. Todo o resto — nota, etiqueta, estoque, e-mail — vira um
consumidor independente, cada um com a sua fila e o seu ritmo.

:::diagram type="blocks" caption="O pedido é publicado uma vez; cada setor tem a sua fila e o seu ritmo."
rows:
  - [{ text: "Loja", note: "grava o pedido e publica pedido.pago" }]
  - [{ text: "RabbitMQ", note: "exchange doce.eventos, uma cópia por fila interessada" }]
  - [{ text: "fiscal", note: "NF-e na SEFAZ" }, { text: "expedição", note: "a Zebrinha" }, { text: "estoque", note: "ERP da fábrica" }, { text: "avisos", note: "e-mail e WhatsApp" }]
:::

Se a SEFAZ cair, a fila do fiscal cresce e as outras três seguem andando.
Se a Zebrinha engasgar, a fila da expedição cresce e a nota fiscal continua
saindo. Nenhum setor espera o outro, e o cliente não espera nenhum deles.

Isso é o desenho, e ele não sai pronto. Nas próximas partes, cada peça
aparece quando um defeito a exige: a mensagem que some, o consumidor que
trava, a nota emitida duas vezes, o banco que confirma e a mensagem que não
sai.

## Subindo o RabbitMQ

O RabbitMQ roda como um servidor à parte, e o jeito mais simples de tê-lo
na sua máquina sem instalar nada é o Docker. Crie uma pasta para o projeto
do livro e, dentro dela, um arquivo de configuração do Docker Compose — a
ferramenta que sobe contêineres descritos num arquivo:

```yaml title="doce-mirabel/docker-compose.yml" numbered
services:
  rabbitmq:
    image: rabbitmq:4-management
    ports:
      - "5672:5672"
      - "15672:15672"
```

Seis linhas, e cada uma importa.

A imagem `rabbitmq:4-management` é o RabbitMQ 4 com o **painel de
gerenciamento** já ligado. Sem o sufixo `-management`, o broker funciona do
mesmo jeito, mas não tem interface web.

As duas portas são os dois jeitos de falar com ele. A **5672** é a porta do
protocolo AMQP: é por ela que os programas publicam e consomem. A **15672**
é a porta do painel, em HTTP, para você olhar. `"5672:5672"` quer dizer
"a porta 5672 da minha máquina leva à porta 5672 do contêiner".

Suba:

```text
$ docker compose up -d
[+] Running 2/2
 ✔ Network doce-mirabel_default       Created
 ✔ Container doce-mirabel-rabbitmq-1  Started
```

O `-d` deixa o contêiner rodando em segundo plano e devolve o terminal. Na
primeira vez, o Docker baixa a imagem antes; isso leva um minuto.

Confirme que o broker respondeu:

```text
$ docker compose exec rabbitmq rabbitmqctl version
4.3.6
```

`docker compose exec rabbitmq` roda um comando **dentro** do contêiner
chamado `rabbitmq`. O `rabbitmqctl` é a ferramenta de linha de comando que
vem com o broker. O número exato da versão vai ser outro na sua máquina;
o que importa é o 4 na frente.

:::pitfall
Se a porta 5672 ou a 15672 já estiver em uso — outro RabbitMQ, de outro
projeto, esquecido rodando —, o `up` falha com *port is already allocated*.
`docker ps` lista os contêineres no ar; pare o antigo com `docker stop` e o
nome dele, ou troque a porta da esquerda no arquivo, por exemplo
`"5673:5672"`.
:::

## O painel

Abra `http://localhost:15672` no navegador. Usuário `guest`, senha `guest`.

:::warning
O usuário `guest` só consegue entrar a partir da própria máquina onde o
RabbitMQ roda — é uma trava de fábrica, porque todo mundo sabe essa senha.
No seu computador, com Docker, funciona. Num servidor, a primeira coisa a
fazer é criar outro usuário e apagar o `guest`.
:::

O painel tem seis abas no alto. Quatro delas são o vocabulário do resto do
livro:

| Aba | O que mostra | O que olhar agora |
|---|---|---|
| Overview | o broker inteiro: mensagens na fila, taxa de entrada e saída | os gráficos zerados |
| Connections | cada programa conectado, com endereço e usuário | nada, ainda |
| Channels | as conversas abertas dentro de cada conexão | nada, ainda |
| Exchanges | os pontos de entrada das mensagens | os oito que já vêm prontos |
| Queues and Streams | as filas: quantas mensagens, quantos consumidores | nenhuma fila |
| Admin | usuários, permissões e virtual hosts | o `guest` |

Tabela: O painel é o terminal do broker. Tudo o que um programa faz aparece
nele — e é por ele que você vai conferir cada capítulo.

Abra **Exchanges**. O RabbitMQ já vem com oito, e o primeiro da lista
chama a atenção porque não tem nome: aparece como **(AMQP default)**.

```text
$ docker compose exec rabbitmq rabbitmqctl list_exchanges name type
Listing exchanges for vhost / ...
name	type
	direct
amq.direct	direct
amq.fanout	fanout
amq.headers	headers
amq.match	headers
amq.rabbitmq.log	topic
amq.rabbitmq.trace	topic
amq.topic	topic
```

Aquela linha que começa em branco é ele: o exchange de nome vazio. Guarde
a existência dele — a primeira mensagem do livro passa por ali.

:::term Exchange
O ponto de entrada de uma mensagem no RabbitMQ. O produtor nunca publica
**numa fila**; publica num exchange, e o exchange decide para quais filas a
mensagem vai, de acordo com regras. É a peça que faltava na pasta do
capítulo @cap:do-espeto-de-papel-ao-broker, onde o produtor precisava
conhecer cada interessado.
:::

## A primeira mensagem é um clique

Antes de escrever uma linha de PHP, vale ver uma mensagem fazer o caminho
inteiro com as mãos. Tudo o que o código dos próximos capítulos faz é isso,
automatizado.

**1. Crie a fila.** Em **Queues and Streams**, abra *Add a new queue*.
Nome: `fiscal.pedidos`. Deixe o resto como está e clique em *Add queue*.
A fila aparece na lista com zero mensagens.

**2. Publique.** Clique no nome da fila. Na página dela, abra *Publish
message*. No campo *Payload*, escreva:

```json
{"pedido": 40117, "produto": "geleia de ameixa", "quantidade": 2}
```

e clique em *Publish message*. O painel responde *Message published.*

Repare, antes de clicar, no campo *Delivery mode*: ele vem em
**1 - Non-persistent**. Quer dizer que a mensagem fica só na memória do
broker e não sobrevive a um restart dele. Para uma mensagem de teste, tudo
bem; para um pedido, não — e é o tipo de padrão que se deixa passar sem
ler.

**3. Olhe a fila.** Volte para **Queues and Streams**. A fila
`fiscal.pedidos` mostra **1** na coluna *Ready*. A mensagem está guardada no
broker, esperando um consumidor. Confira pelo terminal:

```text
$ docker compose exec rabbitmq rabbitmqctl list_queues \
    name messages_ready messages_unacknowledged
Listing queues for vhost / ...
name	messages_ready	messages_unacknowledged
fiscal.pedidos	1	0
```

**4. Consuma.** Na página da fila, abra *Get messages*. O campo *Ack Mode*
vem com **Nack message requeue true**: o painel lê a mensagem e a devolve
para a fila, como quem olha o papel e o espeta de volta. Clique em *Get
Message(s)*: o JSON aparece na tela, e a fila continua com 1.

Troque o *Ack Mode* para **Automatic ack** e clique de novo. Agora a
mensagem foi entregue **e confirmada** no mesmo gesto — e a fila vai a
zero. Esse
"confirmada" é o ack da tabela do capítulo anterior, o "terminei" que a
pasta de arquivos não tinha. Ele vai ganhar um capítulo inteiro de defeitos.

:::checkpoint
Você publicou numa página que se chama "fila", mas o produtor nunca publica
numa fila. Por onde a mensagem passou?
:::

Ela passou pelo **exchange de nome vazio**. Quando você usa *Publish
message* na página de uma fila, o painel publica no *(AMQP default)* usando
o **nome da fila** como endereço. E o *default exchange* tem uma única
regra: entrega a mensagem na fila cujo nome é igual ao endereço.

:::term Default exchange
O exchange sem nome que todo RabbitMQ tem. Toda fila criada fica
automaticamente ligada a ele pelo próprio nome, e ele não pode ser apagado
nem reconfigurado. Publicar nele com o endereço `fiscal.pedidos` é o jeito
mais curto de pôr uma mensagem na fila `fiscal.pedidos` — e o que o
primeiro programa do livro vai fazer.
:::

Esse atalho é ótimo para começar e ruim para crescer: quem publica no
*default exchange* precisa saber o nome da fila, e voltamos ao produtor que
conhece cada interessado. O atalho serve enquanto existe um interessado
só.

:::story Quanto custa?
À tarde, o Rafa passou pela mesa da Júlia e viu o painel aberto.

— É esse o RabbitMQ?

— É.

— Quanto custa a licença?

— Nada. É código aberto.

— E o servidor?

— Por enquanto, um contêiner no meu notebook. Em produção, uma máquina
pequena. Ele é leve.

O Rafa ficou olhando o gráfico zerado do Overview.

— E por que ele não está fazendo nada?

— Porque ninguém mandou nada para ele ainda.

— Então manda.

A Júlia publicou uma mensagem pelo painel. O gráfico subiu um tracinho e
voltou.

— Só isso?

— Só isso. O resto do trabalho é fazer o seu checkout mandar esse tracinho
em vez de esperar a SEFAZ.

O Kaique, da mesa do lado, virou uma etiqueta e escreveu: *fila = lugar que
não esquece*.
:::

:::milestone
Você tem: um RabbitMQ 4 rodando no Docker, o painel aberto em
`localhost:15672`, uma fila `fiscal.pedidos` criada à mão, uma mensagem
publicada e consumida sem código, e o nome do caminho que ela fez — o
*default exchange*.
:::

:::summary
- O desenho-alvo publica o pedido uma vez; cada setor — fiscal, expedição,
	estoque, avisos — tem a sua fila e consome no próprio ritmo.
- O RabbitMQ sobe com seis linhas de Docker Compose: a imagem
	`-management`, a porta 5672 do AMQP e a 15672 do painel.
- O painel mostra conexões, canais, exchanges e filas; é por ele que se
	confere o que os programas fazem.
- Produtor nunca publica numa fila: publica num exchange, que decide o
	destino. O *default exchange*, sem nome, entrega na fila de nome igual ao
	endereço.
- "Get messages" com requeue devolve a mensagem; com ack, ela sai da fila.
:::

:::exercise level=1
Pelo painel, publique três mensagens na fila `fiscal.pedidos`, com os
pedidos 40118, 40119 e 40120. Depois use *Get messages* com *Ack Mode*
**Nack message requeue true** e *Messages* igual a 3. Em que ordem elas
aparecem? A fila é FIFO ou é o espeto da Dona Cida?

:::answer
Elas aparecem na ordem em que foram publicadas: 40118, 40119, 40120. A fila
do RabbitMQ é FIFO — quem entrou primeiro sai primeiro. E, como o modo foi
de *requeue*, as três voltam para a fila e o contador *Ready* continua em
3.

Uma ressalva: a ordem é garantida para mensagens que
entram na mesma fila e são lidas por um consumidor só. Com vários
consumidores e mensagens devolvidas, a ordem de **processamento** pode
mudar, mesmo que a ordem de **entrega** seja FIFO.
:::

:::exercise level=2
Publique uma mensagem pela página do exchange **(AMQP default)**, em
*Exchanges*, usando o *Routing key* `fiscal.pedido` — sem o "s" no fim.
O painel diz *Message published*. Onde a mensagem foi parar?

:::answer
Em lugar nenhum. O *default exchange* procura uma fila chamada exatamente
`fiscal.pedido`, não encontra, e **descarta** a mensagem. O painel avisa —
*Message published, but not routed.* —, e o gráfico do Overview conta o
descarte na linha *Unroutable (drop)*. Um programa, por padrão, não recebe
aviso nenhum: o publish "dá certo" e a mensagem some.

É o primeiro contato com uma regra que vai custar caro se for esquecida: o
RabbitMQ não guarda mensagem sem destino. Se nenhuma fila combina com o
endereço, publicar é jogar fora — e existe um jeito de o produtor ficar
sabendo disso, que só faz sentido depois de o produtor existir.
:::
