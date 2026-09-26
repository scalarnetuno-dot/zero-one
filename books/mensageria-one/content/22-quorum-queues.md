---
title: "Quorum queues e o broker que cai"
number: 22
slug: quorum-queues
part: p5
kicker: "Três servidores, uma fila clássica e uma quorum. Um servidor caiu, e só uma das filas continuou existindo."
goal: >-
  Entender o que um cluster RabbitMQ replica e o que não replica, ver uma
  fila clássica sumir com o nó dela e uma quorum queue sobreviver, usar
  quorum queues com a Mirabel, e comparar RabbitMQ, Kafka e SQS o bastante
  para responder ao Rafa.
---

:::story Só coloca um Kafka
Em novembro, o Rafa voltou de um evento em São Paulo com um adesivo novo
no notebook e uma pergunta.

— E se o RabbitMQ cair na Black Friday?

— O checkout continua vendendo — disse Júlia. — A outbox guarda os
eventos, e o despachante publica quando ele voltar.

— E se ele não voltar? Se o servidor queimar?

— Aí o que estava nas filas vai junto. Se o disco for junto.

O Rafa apontou para o adesivo.

— O pessoal do evento usa Kafka. Disseram que Kafka não perde nada,
porque replica em três máquinas.

— RabbitMQ também replica em três máquinas.

— Então por que a gente não replica?

A Júlia ficou um tempo olhando o adesivo.

— Porque até agora ninguém tinha perguntado.

O Kaique anotou no verso de uma etiqueta: *só coloca um Kafka → só
coloca três RabbitMQ?*
:::

A pergunta do Rafa é a certa, pela primeira vez sem ressalva. Tudo o que
o livro construiu até aqui roda num broker só, e um broker só é um
servidor que pode perder o disco. O capítulo
@cap:o-que-sobrevive-a-um-restart garantiu que um **restart** não perde
nada; ele não disse nada sobre um servidor que não volta.

## Um cluster

Um **cluster** RabbitMQ são vários servidores — chamados **nós** — que
compartilham usuários, exchanges, bindings e a definição das filas. Um
cliente pode se conectar a qualquer um deles e enxerga a mesma topologia.
Três nós é o número mínimo que faz sentido, pelo motivo que aparece daqui
a pouco.

Com Docker, três nós cabem num Compose. O que os une é um segredo
compartilhado, o **cookie** do Erlang — a senha que os nós usam para
confiar uns nos outros:

```yaml title="docker-compose.yml"
x-rabbit: &rabbit
  image: rabbitmq:4-management
  environment:
    RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS: "-setcookie doce-mirabel"
    RABBITMQ_CTL_ERL_ARGS: "-setcookie doce-mirabel"
services:
  rabbit1:
    <<: *rabbit
    hostname: rabbit1
    ports: ["5681:5672", "15681:15672"]
  rabbit2:
    <<: *rabbit
    hostname: rabbit2
    ports: ["5682:5672"]
  rabbit3:
    <<: *rabbit
    hostname: rabbit3
    ports: ["5683:5672"]
```

`x-rabbit: &rabbit` define um bloco reaproveitável, e `<<: *rabbit` o
copia para cada serviço. O `hostname` fixo importa: o nome de um nó é
`rabbit@` mais o nome da máquina, e ele precisa ser o mesmo a cada
reinício.

Os nós sobem separados e são unidos com o `rabbitmqctl`:

```bash
docker compose exec rabbit2 rabbitmqctl stop_app
docker compose exec rabbit2 rabbitmqctl join_cluster rabbit@rabbit1
docker compose exec rabbit2 rabbitmqctl start_app
```

O mesmo para o `rabbit3`. Depois disso, `rabbitmqctl cluster_status`
lista os três em *Running Nodes*.

:::pitfall
Um cluster replica a **topologia**, não as mensagens. Uma fila clássica
existe em um nó só, o nó em que foi criada; os outros sabem que ela
existe, e só. É o erro de leitura mais comum sobre clusters RabbitMQ: três
servidores não querem dizer três cópias de cada pedido.
:::

## O teste que importa

Conectado ao `rabbit3`, um script declara duas filas — uma clássica e uma
com o argumento `x-queue-type` igual a `quorum` — e publica três pedidos
persistentes em cada:

```text
$ docker compose exec rabbit1 rabbitmqctl list_queues \
    name type leader members
teste.classica	classic	rabbit@rabbit3	[rabbit@rabbit3]
teste.quorum	quorum	rabbit@rabbit3	[rabbit@rabbit3,
    rabbit@rabbit1, rabbit@rabbit2]
```

A clássica mora no `rabbit3` e em mais lugar nenhum. A quorum também tem
o `rabbit3` como **líder**, mas tem três **membros**: uma cópia em cada
nó. Agora, o que o Rafa perguntou — o servidor da fila não volta:

```text
$ docker compose stop rabbit3
$ docker compose exec rabbit1 rabbitmqctl list_queues \
    name type state messages leader
teste.classica	rabbit_classic_queue	down
teste.quorum	quorum	running	3	rabbit@rabbit1
```

A clássica está `down`. A quorum está `running`, com as três mensagens e
um líder novo, o `rabbit1`, eleito em segundos. Lendo das duas, pelo
`rabbit1`:

```text
teste.quorum: pedido 1
teste.classica: NOT_FOUND - queue 'teste.classica' in vhost '/'
process is stopped by supervisor
```

Os pedidos da fila clássica não se perderam — estão no disco do `rabbit3`
—, mas ficam inacessíveis até ele voltar. Se o disco não voltar, eles
também não.

:::term Quorum queue
Uma fila replicada em vários nós, que usa um algoritmo de consenso — o
Raft — para decidir, a cada mensagem, que a maioria dos membros a gravou.
Com três membros, a fila aguenta a perda de um; com cinco, de dois. É por
isso que três é o mínimo: com dois, perder um é perder a maioria.
:::

A contrapartida está na palavra consenso. Cada mensagem só é confirmada
depois de gravada na maioria dos nós, então a quorum é mais lenta que a
clássica e usa mais disco e rede. Ela é sempre durável — não existe quorum
temporária —, e alguns recursos da clássica não existem nela, ou existem
de outro jeito. Para pedidos pagos, a troca é óbvia; para uma fila de
métricas que pode perder alguns pontos, nem tanto.

## Quorum com a Mirabel

Na Mirabel, o tipo da fila é uma opção do worker:

```php title="src/Workers/EmitirNotaFiscal.php"
final class EmitirNotaFiscal extends Worker
{
    public static string $queue = 'fiscal.pedidos-pagos';
    public static array $routingKeys = ['pedido.pago'];
    public static array $retry = [
        'delay' => 1000, 'max_attempts' => 3,
    ];
    public static array $options = ['queue_type' => 'quorum'];

    // handle() como antes
}
```

Com `queue_type` igual a `quorum`, a fila, a `.retry` e a `.error` são
criadas replicadas nos três nós — na saída abaixo, resumida, a lista de
membros de cada uma tem os três:

```text
fiscal.pedidos-pagos        quorum  rabbit@rabbit1  [3 membros]
fiscal.pedidos-pagos.retry  quorum  rabbit@rabbit1  [3 membros]
fiscal.pedidos-pagos.error  quorum  rabbit@rabbit1  [3 membros]
```

E o retry com espera funciona igual — a espera por TTL e dead-letter
existe nas quorum queues. Com o `rabbit2` parado no meio do teste, o
worker seguiu processando:

```text
tentativa 1: falhou
warning RabbitMQ message sent to retry.
tentativa 2: pedido 40118 ok
```

:::warning
Uma fila não muda de tipo. Se `fiscal.pedidos-pagos` já existe como
clássica, o worker com `queue_type` quorum recebe `PRECONDITION_FAILED`
do broker. A Mirabel trata esse erro como defeito de configuração, e não
como queda: o worker para com a mensagem de erro, em vez de ficar
reconectando para sempre. Migrar uma fila de clássica para quorum é criar
a nova com outro nome, apontar os bindings para ela, esvaziar a antiga e
apagá-la — com calma, fora da Black Friday.
:::

A Mirabel conecta num host só, configurado em `MB_RABBITMQ_HOST`. Para
que um worker sobreviva à queda do **nó a que está conectado**, o host
precisa ser um nome que leve a qualquer nó vivo — um balanceador de carga
na frente dos três, ou um nome de DNS com os três endereços. Com isso, a
reconexão do capítulo @cap:workers-que-nao-morrem encontra outro nó, e a
fila quorum, com o líder novo, está lá esperando.

## RabbitMQ, Kafka e SQS

O Rafa trouxe o Kafka do evento, e a comparação merece uma tabela honesta,
porque as três ferramentas resolvem problemas parecidos de jeitos
diferentes:

| | RabbitMQ | Kafka | Amazon SQS |
|---|---|---|---|
| modelo | fila: a mensagem sai quando é confirmada | log: a mensagem fica; cada leitor guarda a posição | fila gerenciada |
| roteamento | exchanges, routing keys, padrões | tópicos e partições | uma fila por destino; fan-out com SNS |
| reler o passado | não, depois do ack | sim, pelo tempo de retenção | não |
| retry e fila de erro | TTL e dead-letter | escrito pela aplicação | nativos (redrive) |
| operar | um cluster pequeno, ou gerenciado | cluster maior, mais peças | nada: é serviço |
| ordem | por fila | por partição | só nas filas FIFO |

Tabela: Nenhuma coluna ganha em todas as linhas.

Para a Doce Mirabel — trabalho que alguém precisa fazer uma vez, com
retry, fila de erro e roteamento por tipo de evento —, o formato é o de
uma fila, e o RabbitMQ entrega isso com um cluster de três nós. O Kafka
brilha quando o mesmo fluxo de eventos precisa ser relido por muitos
sistemas, reprocessado desde o início ou guardado por semanas — um
histórico, não uma caixa de pedidos. O SQS brilha quando ninguém na
empresa quer operar broker nenhum.

:::key
Replicar é uma decisão por fila, não por broker. Pedidos pagos vão para
quorum queues num cluster de três nós; o resto pode continuar clássico. E
o que protege o pedido quando o broker inteiro falha não é o broker — é a
outbox, que guarda o evento no banco até alguém conseguir publicar.
:::

:::milestone
Você tem: um cluster de três nós; as filas de pedidos como quorum queues,
replicadas e sobrevivendo à queda de um nó; os workers da Mirabel com
`queue_type` quorum, conectados por um nome que leva a qualquer nó vivo; e
uma resposta para o Rafa que não depende do adesivo.
:::

:::summary
- Um cluster RabbitMQ replica usuários, exchanges e definições; uma fila
	clássica vive num nó só e fica indisponível quando ele cai.
- Quorum queues replicam as mensagens na maioria dos nós, por consenso;
	com três nós, aguentam a perda de um.
- Na Mirabel, `$options = ['queue_type' => 'quorum']` cria a fila, a
	`.retry` e a `.error` como quorum; uma fila existente não muda de tipo.
- A Mirabel conecta num host só: um balanceador ou DNS na frente do
	cluster leva a reconexão a um nó vivo.
- RabbitMQ é fila com roteamento; Kafka é log relível; SQS é fila sem
	operação. O problema escolhe, não a moda.
:::

:::exercise level=1
Num cluster de três nós, dois caem ao mesmo tempo. O que acontece com uma
quorum queue de três membros, e com o checkout que publica nela via
outbox?

:::answer
A quorum queue perde a maioria: um membro de três não decide nada
sozinho. Ela fica indisponível — nem aceita nem entrega mensagens — até um
dos outros voltar. Nada é perdido: as mensagens confirmadas estavam em
pelo menos dois nós.

O checkout não percebe: ele grava na outbox, no banco. O despachante
falha ao publicar, conta as falhas e tenta de novo. Quando a maioria
voltar, tudo é publicado. É a queda do broker do capítulo sobre outbox,
com um cluster no lugar do servidor único.
:::

:::exercise level=2
O Rafa pergunta se vale pôr **todas** as filas como quorum, "para
garantir". Responda com o custo, e diga quais filas da Doce Mirabel você
deixaria clássicas.

:::answer
Quorum custa escrita em três nós por mensagem, mais disco e mais rede, e
confirma um pouco mais devagar. Para filas de pedidos, o custo é pequeno
diante do valor de cada mensagem.

Ficariam clássicas as filas em que perder mensagens não custa nada ou
em que o conteúdo pode ser refeito: uma fila de métricas, uma de
auditoria que também é gravada em outro lugar, filas de teste de carga.
E a pergunta de volta ao Rafa é a do capítulo sobre durabilidade: se
perder esta mensagem não tem custo, por que ela está numa fila?
:::
