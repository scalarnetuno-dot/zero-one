---
title: "O broker não sabe que língua você fala"
number: 24
slug: o-broker-nao-sabe-que-lingua-voce-fala
part: p5
kicker: "O pedido saiu de um PHP em Minas, foi lido por um Java numa transportadora em Campinas, e a resposta voltou para o PHP com a mesma correlação. Ninguém combinou nada além do formato da mensagem."
goal: >-
  Consumir em Java, com o cliente oficial do RabbitMQ, o evento que a
  Mirabel publica em PHP; ler propriedades e headers que a biblioteca
  escreve; publicar a resposta de volta; e tratar o formato da mensagem
  como o contrato entre dois sistemas que não se conhecem.
---

:::story A transportadora
Em outubro, a transportadora que coleta as caixas da Doce Mirabel mandou
um e-mail: tinham um sistema novo, em Java, e queriam receber os pedidos
"por fila", em vez da planilha que a Denise mandava todo fim de tarde.

A reunião foi por vídeo. Do outro lado, o Otávio, desenvolvedor da
transportadora, com um fone de ouvido enorme.

— Vocês usam o quê? — perguntou ele.

— RabbitMQ — disse Júlia. — E PHP.

— A gente usa Java. Tem problema?

— Nenhum. O broker não sabe em que língua a mensagem foi escrita.

— E o formato?

— JSON. E uns headers. Eu te mando um exemplo.

O Rafa, que tinha entrado na chamada sem câmera, ligou o microfone.

— Não precisa de uma API? De um contrato? De um documento?

— A mensagem é o contrato — disse Júlia. — O documento é ela, com uma
explicação do lado.

O Otávio concordou com a cabeça, o que numa chamada de vídeo com fone de
ouvido enorme parece um sim convicto.
:::

O capítulo @cap:do-espeto-de-papel-ao-broker contou por que o AMQP
nasceu: para que o **protocolo** deixasse de pertencer a quem vendia o
servidor, e dois sistemas de fornecedores diferentes conversassem. A
transportadora é o teste disso. O produtor é PHP com a Mirabel; o
consumidor é Java com o cliente oficial do RabbitMQ; eles não
compartilham uma linha de código — só o broker e o formato.

## O que o Java recebe

Antes de escrever o consumidor, vale listar o que a Mirabel põe em cada
`pedido.pago`, do ponto de vista de quem não usa a Mirabel:

| Onde | O quê | Para o consumidor Java |
|---|---|---|
| corpo | JSON com pedido, total, entrega, itens | `byte[]`, que o Jackson lê |
| `content_type` | `application/json` | confirma o formato |
| `message_id` | a identidade da mensagem | chave de idempotência técnica |
| `correlation_id` | a conversa do checkout | repassada na resposta |
| `type` | `DoceMirabel\Eventos\PedidoPago` | só informativo: é o nome de uma classe PHP |
| header `x-schema-version` | `2` | decide se o consumidor sabe ler o corpo |
| header `x-idempotency-key` | `pedido-40117` | chave de idempotência de negócio |

Tabela: Tudo isso é AMQP padrão: propriedades e headers que qualquer
cliente, em qualquer linguagem, lê do mesmo jeito.

O `type` merece uma nota. A Mirabel preenche com o nome da classe PHP do
evento, e para o Java ele é uma string sem significado. O que identifica o
evento de forma estável, para qualquer linguagem, é a **routing key** —
`pedido.pago` —, e é por ela que a transportadora se inscreve.

## O projeto Java

O consumidor usa duas bibliotecas: o `amqp-client`, cliente oficial do
RabbitMQ para Java, e o Jackson, para ler JSON. As dependências, no
`pom.xml` do Maven:

```xml title="pom.xml"
  <dependencies>
    <dependency>
      <groupId>com.rabbitmq</groupId>
      <artifactId>amqp-client</artifactId>
      <version>5.25.0</version>
    </dependency>
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>2.18.2</version>
    </dependency>
    <dependency>
      <groupId>org.slf4j</groupId>
      <artifactId>slf4j-nop</artifactId>
      <version>1.7.36</version>
    </dependency>
  </dependencies>
```

O `slf4j-nop` silencia o log interno do cliente, que usa a biblioteca de
log SLF4J; num sistema de verdade, ele seria trocado pelo log da
aplicação.

## O consumidor

```java title="src/main/java/br/com/transportadora/Coletas.java" numbered
package br.com.transportadora;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.Delivery;
import java.io.IOException;
import java.util.Date;
import java.util.Map;

public class Coletas {

    static final String EXCHANGE = "doce.eventos";
    static final String FILA = "transportadora.coletas";
    static final ObjectMapper JSON = new ObjectMapper();

    public static void main(String[] args) throws Exception {
        var env = System.getenv();
        var fabrica = new ConnectionFactory();
        var host = env.getOrDefault("RABBITMQ_HOST", "localhost");
        var porta = env.getOrDefault("RABBITMQ_PORT", "5672");
        fabrica.setHost(host);
        fabrica.setPort(Integer.parseInt(porta));
        Channel canal = fabrica.newConnection().createChannel();

        canal.exchangeDeclare(EXCHANGE, "topic", true);
        canal.queueDeclare(FILA, true, false, false, null);
        canal.queueBind(FILA, EXCHANGE, "pedido.pago");
        canal.basicQos(1);

        canal.basicConsume(FILA, false,
            (tag, entrega) -> agendar(canal, entrega), tag -> { });
        System.out.println("transportadora esperando pedidos pagos");
    }

    static void agendar(Channel canal, Delivery entrega)
            throws IOException {
        var props = entrega.getProperties();
        var headers = props.getHeaders();
        var tag = entrega.getEnvelope().getDeliveryTag();
        var versao = (Number) headers.getOrDefault(
            "x-schema-version", 1);

        if (versao.intValue() != 2) {
            System.out.println("versao " + versao + " desconhecida");
            canal.basicReject(tag, false);
            return;
        }

        var pedido = JSON.readTree(entrega.getBody());
        long numero = pedido.get("pedido").asLong();
        String cep = pedido.get("entrega").get("cep").asText();
        System.out.println("coleta do pedido " + numero
            + " para o CEP " + cep
            + " (chave " + headers.get("x-idempotency-key") + ")");

        byte[] corpo = JSON.writeValueAsBytes(Map.of(
            "pedido", numero,
            "coleta", "2026-11-27T18:00:00-03:00"));
        var resposta = new AMQP.BasicProperties.Builder()
            .contentType("application/json")
            .deliveryMode(2)
            .messageId("coleta-" + numero)
            .correlationId(props.getCorrelationId())
            .type("br.com.transportadora.ColetaAgendada")
            .timestamp(new Date())
            .headers(Map.of("x-schema-version", 1))
            .build();

        canal.basicPublish(
            EXCHANGE, "coleta.agendada", resposta, corpo);
        canal.basicAck(tag, false);
    }
}
```

Quem leu a Parte 2 reconhece cada linha, com outros nomes. O
`ConnectionFactory` abre a conexão e o canal; `exchangeDeclare`,
`queueDeclare` e `queueBind` são os mesmos `exchange_declare`,
`queue_declare` e `queue_bind` da `php-amqplib`, com os mesmos argumentos
na mesma ordem. `basicQos(1)` é o prefetch 1. `basicConsume` com `false`
no segundo argumento é o ack manual.

O método `agendar` é o `handle()` da transportadora. Ele faz, à mão, o
que a Mirabel faz no PHP: lê a versão do header **antes** de tocar no
corpo, e rejeita sem requeue o que não sabe ler; lê o corpo com o
Jackson; e confirma com `basicAck` só depois de publicar a resposta —
ack depois do efeito, a regra do capítulo
@cap:ack-quando-a-mensagem-pode-morrer, que vale em qualquer linguagem.

A resposta é um evento novo, `coleta.agendada`, no mesmo exchange, com as
mesmas convenções que a Mirabel usa: JSON, persistente, `message_id`
estável, `type`, `timestamp`, `x-schema-version`. E o `correlation_id` do
pedido é **copiado** para a resposta: é assim que a conversa atravessa a
fronteira entre as duas empresas.

## A volta, em PHP

Do lado da Doce Mirabel, a coleta agendada é consumida por um worker
comum:

```php title="src/Workers/ColetaAgendada.php"
final class ColetaAgendada extends Worker
{
    public static string $queue = 'expedicao.coletas';
    public static array $routingKeys = ['coleta.agendada'];

    public function handle(Envelope $envelope): void
    {
        $pedido = $envelope->body['pedido'];
        $coleta = $envelope->body['coleta'];
        echo "coleta do {$pedido}: {$coleta}", PHP_EOL;
    }
}
```

Com o consumidor Java, o worker PHP e dois pedidos publicados pelo
checkout — um na versão 2 do contrato, outro na versão 1:

```text
$ mvn -q package dependency:copy-dependencies
$ java -cp "target/classes:target/libs/*" \
    br.com.transportadora.Coletas
transportadora esperando pedidos pagos
coleta do pedido 40119 para o CEP 37701-000 (chave pedido-40119)
versao 1 desconhecida
```

E, no worker PHP, a resposta do Java:

```text
coleta do 40119: 2026-11-27T18:00:00-03:00
```

O `$envelope->correlationId` dessa resposta é `checkout-91b2`, o mesmo do
checkout que publicou o pedido, e o `$envelope->type` é
`br.com.transportadora.ColetaAgendada`.

O `dependency:copy-dependencies` copia os JARs das bibliotecas para
`target/libs`, e o `-cp` os põe no classpath — no Windows, o separador
entre os caminhos é `;` em vez de `:`. O pedido 40119 foi, voltou e
trouxe a correlação do checkout. O 40120, na versão 1, foi rejeitado pelo
Java — e, como a fila da transportadora não tem dead-letter configurado,
descartado. Numa integração de verdade, a fila dela teria a sua própria
fila de erro, e alguém dos dois lados olharia para ela.

:::key
Entre dois sistemas que não compartilham código, a mensagem **é** o
contrato: routing key, formato do corpo, versão, headers e o que cada
lado faz com uma versão que não conhece. Documente isso com um exemplo
real de mensagem, e a linguagem de cada lado deixa de importar.
:::

## O contrato por escrito

A "explicação do lado" que a Júlia prometeu ao Otávio cabe numa página,
e ela é o que torna a integração mantível quando nenhum dos dois estiver
mais lá:

| Item | `pedido.pago` |
|---|---|
| exchange | `doce.eventos`, topic, durável |
| routing key | `pedido.pago` |
| versão atual | `x-schema-version: 2` |
| corpo | JSON: `pedido` (inteiro), `total_centavos` (inteiro), `entrega.cep` (texto `00000-000`), `itens[]` |
| garantias | at-least-once; `x-idempotency-key` identifica o pedido |
| versões futuras | campos novos não mudam a versão; mudança incompatível vira 3, anunciada com 30 dias |
| resposta esperada | `coleta.agendada`, com o mesmo `correlation_id` |

Tabela: O contrato da integração com a transportadora, como foi mandado
por e-mail.

A linha de garantias é a que mais evita reunião: ela diz ao Otávio, sem
rodeio, que ele vai receber repetições, e qual campo usar para
descartá-las.

:::milestone
Você tem: um consumidor Java, com o cliente oficial do RabbitMQ, lendo o
`pedido.pago` que a Mirabel publica em PHP; a resposta `coleta.agendada`
voltando com a mesma correlação e sendo consumida por um worker PHP; e o
contrato da mensagem escrito numa página.
:::

:::summary
- O broker não conhece a linguagem de ninguém: propriedades, headers e
	corpo são AMQP padrão, lidos igual em PHP e em Java.
- O cliente Java oficial tem as mesmas operações da `php-amqplib`, com os
	mesmos argumentos: declarar, ligar, prefetch, consumir, ack.
- A routing key identifica o evento entre linguagens; o `type` da Mirabel
	é um nome de classe PHP, só informativo.
- O consumidor de outra linguagem refaz o contrato da biblioteca à mão:
	versão antes do corpo, ack depois do efeito, correlação repassada.
- O contrato da integração é a mensagem mais uma página: formato, versão,
	garantias e o que fazer com o que não se entende.
:::

:::exercise level=1
A transportadora recebe o mesmo `pedido.pago` duas vezes — um retry do
despachante da outbox. Com o código deste capítulo, o que acontece do lado
dela, e o que ela deveria fazer?

:::answer
O `agendar` roda duas vezes: agenda a coleta duas vezes e publica duas
`coleta.agendada`, com o mesmo `message_id` (`coleta-40119`). A Doce
Mirabel recebe duas respostas iguais.

A transportadora deveria fazer o que o capítulo sobre idempotência fez
com a nota: reservar a coleta pelo `x-idempotency-key` — ou pelo número do
pedido — numa tabela com chave única, antes de agendar. O contrato avisa
que a entrega é at-least-once; a proteção é dela.
:::

:::exercise level=2
A Doce Mirabel precisa mudar o `cep` de texto com hífen para número sem
hífen, na versão 3 do `pedido.pago`. Escreva a sequência de passos, entre
as duas empresas, para que nenhum pedido seja rejeitado no meio da troca.

:::answer
1. A Doce Mirabel anuncia a versão 3 com antecedência, com uma mensagem de
	exemplo.
2. A transportadora muda o `agendar` para aceitar **as duas** versões — lê
	o header e interpreta o `cep` conforme a versão —, e publica em
	produção.
3. A transportadora confirma que o consumidor novo está no ar.
4. A Doce Mirabel passa a publicar na versão 3.
5. Depois de um prazo combinado sem nenhuma mensagem na versão 2, a
	transportadora remove o suporte a ela.

Na ordem inversa, entre o passo 4 e o 2, toda mensagem seria rejeitada —
e, sem fila de erro do lado dela, descartada.
:::
