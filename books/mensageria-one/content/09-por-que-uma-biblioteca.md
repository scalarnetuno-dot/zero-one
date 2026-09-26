---
title: "Por que uma biblioteca"
number: 9
slug: por-que-uma-biblioteca
part: p3
kicker: "Setenta linhas para dizer que um pedido foi pago. Três para dizer a mesma coisa, e nenhuma delas é mágica."
goal: >-
  Contar o que se repete em todo produtor e consumidor escrito à mão,
  decidir o que uma biblioteca de mensageria pode esconder e o que não pode,
  instalar a Mirabel RabbitMQ, configurá-la pelo ambiente e publicar o
  primeiro evento com ela.
---

:::story Só coloca uma biblioteca
Na segunda de manhã, o Rafa encontrou a Júlia com o `topologia.php`, o
`lote.php`, o `consumidor-lento.php` e a `impressora.php` abertos lado a
lado.

— Isso tudo é para mandar um pedido para a nota fiscal?

— Isso tudo é para mandar um pedido para a nota fiscal **sem perder** —
disse ela. — Conexão, canal, fila durável, mensagem persistente, ack,
prefetch.

— E cada setor vai ter um desses?

— Cada setor vai ter um desses.

O Rafa rolou a tela do `consumidor-lento.php` até o fim.

— Li uma coisa ontem. O cara diz que ninguém escreve protocolo na mão, que
todo mundo usa uma biblioteca.

— Ele tem razão.

— Então só coloca uma biblioteca.

A Júlia virou o notebook para ele. Na tela, o README de um projeto de
código aberto: *Mirabel RabbitMQ*.

O Rafa leu o nome duas vezes.

— Você fez isso de propósito.

— Achei ontem. É coincidência.

Da cozinha, a Dona Cida, que não costumava ouvir conversa de computador,
falou sem se virar:

— Não existe coincidência com ameixa.
:::

O Rafa está certo pela segunda vez no livro, e de novo pelo motivo
errado. Ninguém escreve protocolo na mão em produção — mas não porque é
feio: porque tudo o que a Parte 2 construiu se **repete**, e o que se
repete em cinco lugares é esquecido em um deles.

## O que se repete

Olhe os scripts da Parte 2 e separe as linhas em duas pilhas: as que
dizem **o que** a Doce Mirabel faz e as que dizem **como** falar com o
RabbitMQ.

| Todo produtor precisa | Todo consumidor precisa |
|---|---|
| abrir conexão e canal com host, porta, usuário e senha | o mesmo |
| declarar o exchange, durável | declarar a fila, durável, e os bindings |
| serializar o corpo em JSON | decodificar o JSON |
| marcar `delivery_mode` persistente | `basic_qos` com prefetch 1 antes de consumir |
| pôr `content_type` e um identificador | ack depois do trabalho, nunca antes |
| fechar canal e conexão | o laço de `wait()` e o que fazer quando a conexão cai |

Tabela: Nenhuma dessas linhas é sobre geleia.

Cada linha da tabela é uma decisão que a Parte 2 tomou com calma, depois
de ver o defeito. E cada uma é uma decisão que o sexto consumidor da
empresa, escrito às pressas em novembro, pode esquecer: um `delivery_mode`
que falta e o pedido some no restart; um ack antes do trabalho e a nota
não sai; um prefetch esquecido e a Zebrinha segura a fila.

Uma biblioteca, aqui, não serve para economizar digitação. Serve para que
essas decisões sejam tomadas **uma vez**, num lugar testado, e que o
código de cada setor só diga o que é dele.

## O que ela pode esconder, e o que não pode

Uma biblioteca de mensageria que esconde demais é pior que nenhuma: ela
deixa o desenvolvedor sem saber por que a mensagem sumiu. A régua que este
livro usa tem duas colunas.

| Pode esconder | Não pode esconder |
|---|---|
| abrir conexão, canal e reconectar | que existe um broker, e que ele pode cair |
| serializar e decodificar JSON | o formato da mensagem, que é um contrato |
| `delivery_mode`, `content_type`, identificador | a routing key e o nome da fila |
| declarar exchange, fila e bindings | o tipo do exchange e o que casa com o quê |
| o laço de consumo, o ack no lugar certo | que a entrega é at-least-once |
| prefetch 1 por padrão | que um consumidor lento acumula fila |

Tabela: A coluna da direita é a Parte 2 inteira. É por isso que ela veio
antes.

A **Mirabel RabbitMQ** foi escolhida para a Doce Mirabel porque respeita
essa régua. Ela é pequena — duas classes que o código da aplicação usa,
`Event` e `Worker`, e algumas peças de apoio —, é construída sobre a
mesma `php-amqplib` da Parte 2 e não esconde routing key, fila nem
exchange: a aplicação continua escrevendo `pedido.pago` e
`fiscal.pedidos-pagos` com todas as letras.

## Instalando

A biblioteca é instalada pelo Composer a partir do repositório dela no
GitHub. Acrescente ao `composer.json` do projeto:

```json title="composer.json"
{
    "require": {
        "mirabel/rabbitmq": "dev-master"
    },
    "repositories": [
        {
            "type": "vcs",
            "url": "https://github.com/pablicio/mirabel-rabbitmq"
        }
    ],
    "autoload": {
        "psr-4": { "DoceMirabel\\": "src/" }
    }
}
```

`repositories` diz ao Composer para procurar o pacote também naquele
repositório, e `dev-master` pede a versão da branch principal. `autoload`
com `psr-4` é a convenção que liga namespaces a pastas: uma classe
`DoceMirabel\Eventos\PedidoPago` mora em `src/Eventos/PedidoPago.php`.

```bash
composer update
```

A Mirabel traz a `php-amqplib` como dependência — ela continua lá, por
baixo, e os scripts da Parte 2 continuam funcionando no mesmo projeto.

## Configuração pelo ambiente

A Mirabel não recebe host, porta e senha em código. Ela lê **variáveis de
ambiente** — valores que o sistema operacional entrega ao processo —, todas
com o prefixo `MB_RABBITMQ_`:

| Variável | Padrão | O que é |
|---|---|---|
| `MB_RABBITMQ_HOST` | `localhost` | endereço do broker |
| `MB_RABBITMQ_PORT` | `5672` | porta AMQP |
| `MB_RABBITMQ_USER` / `MB_RABBITMQ_PASSWORD` | `guest` / `guest` | credenciais |
| `MB_RABBITMQ_VHOST` | `/` | virtual host |
| `MB_RABBITMQ_EXCHANGE` | `my-exchange` | o exchange em que tudo é publicado |
| `MB_RABBITMQ_EXCHANGE_TYPE` | `topic` | o tipo dele |

Tabela: Há mais variáveis, de timeout e de novas tentativas; os padrões
delas servem para começar.

Configuração pelo ambiente é o que permite o mesmo código rodar no seu
notebook, em homologação e em produção, cada um com o seu broker, sem
nenhum `if`. E mantém a senha de produção fora do repositório.

A única que a Doce Mirabel precisa mudar agora é o exchange:

```bash
export MB_RABBITMQ_EXCHANGE=doce.eventos
```

No PowerShell, `$env:MB_RABBITMQ_EXCHANGE = "doce.eventos"`. A variável
vale para o terminal em que foi definida; num servidor, ela vai para a
configuração do serviço.

:::pitfall
A Mirabel lê o ambiente com a função `getenv()` do PHP. Um arquivo `.env`
**não** é ambiente: ele só vira variável de ambiente se algum código o
carregar. Num script PHP puro, ninguém carrega, e a biblioteca usa os
padrões — publicando em `my-exchange`, onde ninguém escuta. O sintoma é
um publish sem erro e uma fila que nunca recebe nada.
:::

## O primeiro evento

Um evento, na Mirabel, é uma classe que estende `Event` e diz qual é a sua
routing key:

```php title="src/Eventos/PedidoPago.php" numbered
<?php

declare(strict_types=1);

namespace DoceMirabel\Eventos;

use Mirabel\RabbitMQ\Event;

final class PedidoPago extends Event
{
    public static string $routingKey = 'pedido.pago';
}
```

Uma propriedade **estática** pertence à classe, não a cada objeto: todo
`PedidoPago` que existir tem a mesma routing key, e ela é lida sem criar
objeto nenhum. `final` impede que alguém estenda a classe — um evento é
um contrato, não um ponto de extensão.

Publicar é criar o evento com o conteúdo e chamar `publish()`:

```php title="publicar.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use DoceMirabel\Eventos\PedidoPago;

$pedido = ['pedido' => (int) $argv[1], 'total_centavos' => 8990];

(new PedidoPago($pedido))->publish();
echo "pedido.pago publicado: {$argv[1]}", PHP_EOL;
```

```text
$ php publicar.php 40117
pedido.pago publicado: 40117
```

Compare com o `publicar.php` do capítulo @cap:exchanges-e-bindings. Tudo
o que a linha 11 fez por baixo — abrir a conexão, declarar o exchange
`doce.eventos` como topic e durável, serializar o JSON, marcar a mensagem
como persistente com `content_type`, publicar com a routing key e fechar —
está na tabela do começo do capítulo. Nada sumiu; mudou de lugar.

E, como a Parte 2 ensinou, ninguém recebeu esse pedido. O exchange existe,
mas nenhuma fila está ligada a `pedido.pago` neste broker. O publish
funcionou e a mensagem foi descartada, do mesmo jeito que seria com a
`php-amqplib` pura. A biblioteca não mudou o protocolo; só parou de
obrigar você a escrevê-lo.

:::key
Uma biblioteca boa de mensageria transforma decisões repetidas em padrões
testados — conexão, serialização, persistência, ack, prefetch — e deixa à
mostra o que é contrato: routing key, fila, exchange, formato. Se ela
esconder o contrato, esconde junto a explicação de cada defeito.
:::

:::milestone
Você tem: a Mirabel RabbitMQ instalada, `MB_RABBITMQ_EXCHANGE` apontando
para `doce.eventos`, e o evento `PedidoPago` publicando `pedido.pago` em
uma linha — ainda sem ninguém consumindo.
:::

:::summary
- Todo produtor e consumidor repete conexão, declaração, serialização,
	persistência, ack e prefetch; o que se repete em muitos lugares é
	esquecido em algum.
- Uma biblioteca pode esconder o mecanismo, mas não o contrato: routing
	key, fila, exchange, formato e a entrega at-least-once ficam visíveis.
- A Mirabel instala pelo Composer, roda sobre a `php-amqplib` e lê a
	configuração das variáveis `MB_RABBITMQ_*` do ambiente.
- Um evento é uma classe `final` que estende `Event` e declara
	`public static string $routingKey`; `publish()` faz o que a Parte 2 fazia
	à mão.
:::

:::exercise level=1
Rode o `publicar.php` sem definir `MB_RABBITMQ_EXCHANGE`. O comando
funciona? Em que exchange a mensagem foi parar, e como você confirma pelo
painel?

:::answer
Funciona: a Mirabel usa o padrão, `my-exchange`, e o cria se não existir.
Em **Exchanges**, aparece um `my-exchange` do tipo topic que ninguém
pediu, e a linha *Unroutable (drop)* do Overview conta mais um descarte.
Nenhuma fila do fiscal cresce.

É a armadilha do alerta sobre `.env` em versão reduzida: configuração
esquecida não gera erro, gera mensagem no lugar errado.
:::

:::exercise level=2
Escreva a classe do evento `PedidoCancelado`, com a routing key
`pedido.cancelado`, e diga, sem publicar, quais filas da topologia do
capítulo @cap:exchanges-e-bindings receberiam uma cópia.

:::answer
```php title="src/Eventos/PedidoCancelado.php"
<?php

declare(strict_types=1);

namespace DoceMirabel\Eventos;

use Mirabel\RabbitMQ\Event;

final class PedidoCancelado extends Event
{
    public static string $routingKey = 'pedido.cancelado';
}
```

Receberiam `avisos.pedidos`, ligada por `pedido.*`, e `auditoria.tudo`,
ligada por `#`. Fiscal e expedição, ligadas a `pedido.pago`, não. Se o
fiscal precisar cancelar a nota de um pedido cancelado, a fila dele ganha
um binding — e o evento não muda uma linha.
:::
