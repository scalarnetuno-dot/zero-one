---
title: "Workers que não morrem"
number: 18
slug: workers-que-nao-morrem
part: p5
kicker: "O RabbitMQ reiniciou às 00h12. O worker da expedição tentou cinco vezes, esperou cada vez o dobro, e às 00h12min57 estava imprimindo de novo."
goal: >-
  Pôr workers para rodar sob um supervisor que os levanta quando caem,
  entender o que o worker faz sozinho quando o broker reinicia, parar um
  worker no meio de um deploy sem perder nem repetir trabalho, e reciclar
  processos longos antes que a memória cresça.
---

:::story O terminal da Júlia
Em novembro, a expedição passou a depender do worker. A Denise não
imprimia mais etiqueta pelo site da transportadora: a Zebrinha recebia os
pedidos sozinha.

Numa segunda de manhã, a Zebrinha não imprimiu nada.

— A fila está com quatrocentos pedidos — disse o Kaique, olhando o painel.
— E zero consumidores.

A Júlia abriu o notebook dela. O terminal onde o worker rodava desde
sexta estava fechado.

— O Windows atualizou no domingo.

— O worker roda no seu notebook?

— Rodava. Para testar.

— E ficou testando por três dias?

Ela não respondeu. Abriu outro terminal e digitou
`php artisan rabbitmq:consume ImprimirEtiqueta`. A Zebrinha começou a
imprimir, uma a cada um vírgula oito segundo.

— Quatrocentos pedidos — disse a Denise, da porta. — Doze minutos.

— Treze — disse o Kaique.
:::

Um worker é um programa que precisa rodar **sempre**: de dia, de noite,
depois de um restart do servidor, depois de um deploy, depois de uma
queda do broker. Nenhum terminal aberto faz isso. O capítulo junta as
peças que fazem: um supervisor de processos, a reconexão da biblioteca, o
encerramento gracioso e a reciclagem.

## Quem levanta o worker

Um **supervisor de processos** é um programa cuja função é manter outros
programas rodando: ele os inicia no boot, os reinicia quando morrem e os
para com o sinal certo quando alguém pede. Em servidores Linux, os mais
comuns são o **Supervisor** e o **systemd**; em contêineres, o próprio
Docker faz esse papel.

A Doce Mirabel roda em contêineres. O worker da expedição é um serviço a
mais no Compose de produção, construído sobre a imagem oficial do PHP:

```dockerfile title="Dockerfile"
FROM php:8.4-cli
RUN docker-php-ext-install sockets pcntl
WORKDIR /app
COPY . /app
CMD ["php", "expedicao.php"]
```

A imagem oficial não traz as extensões `sockets` — que a `php-amqplib`
exige — nem `pcntl`, que é a que permite ao PHP receber sinais do sistema
operacional; `docker-php-ext-install` compila as duas. O `expedicao.php`
cria o worker e chama `subscribe()`, como o `consumir.php` da Parte 3.

```yaml title="docker-compose.yml"
services:
  rabbitmq:
    image: rabbitmq:4-management
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 5s
      retries: 20

  expedicao:
    build: .
    environment:
      MB_RABBITMQ_HOST: rabbitmq
      MB_RABBITMQ_EXCHANGE: doce.eventos
    depends_on:
      rabbitmq:
        condition: service_healthy
    restart: unless-stopped
    stop_grace_period: 30s
```

Três linhas fazem do contêiner um processo supervisionado.
`restart: unless-stopped` reinicia o worker sempre que ele terminar,
exceto se alguém o parou de propósito. `depends_on` com
`service_healthy` espera o broker responder ao `ping` antes de subir o
worker. `stop_grace_period` diz quanto tempo o Docker espera o worker
terminar sozinho antes de matá-lo — e ele volta daqui a pouco.

Dentro do contêiner, o host do broker é `rabbitmq`, o nome do serviço: o
Compose cria uma rede em que cada serviço é alcançado pelo nome.

:::note
Num servidor sem contêineres, o mesmo papel é do Supervisor, com um
arquivo por worker em `/etc/supervisor/conf.d/`:

```ini title="/etc/supervisor/conf.d/expedicao.conf"
[program:expedicao]
command=php /srv/loja/artisan rabbitmq:consume ImprimirEtiqueta
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
stopsignal=TERM
stopwaitsecs=30
user=www-data
stdout_logfile=/var/log/expedicao.log
```

`numprocs=2` sobe dois consumidores concorrentes — o capítulo sobre
prefetch mostrou que dividem a fila pela capacidade de cada um.
`stopwaitsecs` é o `stop_grace_period` do Docker com outro nome.
:::

## Quando o broker reinicia

Com o worker supervisionado, reinicie o **broker** — uma atualização de
segurança, uma troca de versão:

```text
$ docker compose restart rabbitmq
```

E o log do worker:

```text
00:12:10 WARNING RabbitMQ worker connection will retry.
00:12:11 WARNING RabbitMQ worker connection will retry.
00:12:13 WARNING RabbitMQ worker connection will retry.
00:12:17 WARNING RabbitMQ worker connection will retry.
00:12:29 WARNING RabbitMQ worker connection will retry.
00:12:57 imprimindo etiqueta do 40118
00:13:00 etiqueta do 40118 pronta
```

O worker não morreu, e o supervisor nem precisou agir. Quando a conexão
caiu, a Mirabel tentou reconectar, esperando 1, 2, 4, 8 e 16 segundos
entre as tentativas — o mesmo backoff exponencial do `publish()`, limitado
por `MB_RABBITMQ_RECONNECT_MAX_DELAY_MS` —, até o broker terminar de subir.
A mensagem publicada depois disso foi impressa normalmente. As linhas de
log vêm de um logger de terminal simples, passado ao worker pelo
`logger()`, como o do Laravel no capítulo @cap:mirabel-dentro-do-laravel.

Por padrão, as tentativas são ilimitadas: um worker não tem para onde ir
enquanto o broker não volta. `MB_RABBITMQ_RECONNECT_ATTEMPTS` limita o
número de **quedas seguidas**; a contagem zera depois de cada conexão bem
sucedida. Quando o limite estoura, `subscribe()` lança a exceção, o
processo termina, e o supervisor decide o que fazer — com
`restart: unless-stopped`, começar de novo.

:::term Heartbeat
Uma mensagem que cliente e broker trocam periodicamente para provar que a
conexão está viva. Sem ela, uma conexão TCP que morreu no meio do caminho
— um cabo, um firewall que fechou a sessão — pode parecer aberta por
minutos, com o worker esperando mensagens que nunca vão chegar. A Mirabel
negocia um heartbeat de 30 segundos (`MB_RABBITMQ_HEARTBEAT`); duas batidas
perdidas e a conexão é dada como morta, o que dispara a reconexão.
:::

## Parar sem quebrar

Todo deploy para os workers antigos e sobe os novos. A pergunta é o que
acontece com a mensagem que o worker está processando **no instante** em
que o deploy começa.

O Docker, o Supervisor e o systemd param um processo do mesmo jeito:
mandam o sinal `SIGTERM` — "por favor, termine" — e esperam. Se o processo
não terminar no prazo, mandam `SIGKILL`, que não pode ser ignorado. Com a
extensão `pcntl`, a Mirabel transforma o `SIGTERM` em `stop()`: o worker
termina a mensagem em mãos, confirma, e sai.

Publique um pedido e, com a etiqueta ainda sendo impressa, pare o worker:

```text
$ docker compose stop expedicao
```

```text
00:13:03 imprimindo etiqueta do 40119
00:13:05 etiqueta do 40119 pronta
00:13:05 INFO RabbitMQ worker stopped gracefully.
```

O `stop` chegou no meio da impressão. O worker terminou a etiqueta, deu
ack, e só então saiu. Nada ficou pela metade, nada voltou para a fila.

O prazo importa. Se a impressão levasse mais que o `stop_grace_period`, o
Docker mandaria `SIGKILL` no meio dela; a mensagem ficaria sem ack e
voltaria para a fila — nada perdido, mas uma etiqueta possivelmente
impressa duas vezes, que é o caso do capítulo sobre idempotência.

| Situação | O que acontece com a mensagem em mãos |
|---|---|
| `SIGTERM` e o `handle()` termina no prazo | concluída e confirmada; nada se repete |
| `SIGKILL`, falta de energia, falta de memória | sem ack; volta para a fila e é entregue de novo |
| sem `pcntl` (Windows, imagem sem a extensão) | o `SIGTERM` mata na hora; igual à linha de cima |

Tabela: O prazo de parada deve ser maior que o `handle()` mais lento que
você aceita esperar.

:::pitfall
A imagem oficial do PHP sem `pcntl` é a causa mais comum de "o worker
perdeu o encerramento gracioso depois que passou a rodar em contêiner".
Não há erro: o `SIGTERM` simplesmente mata o processo. Confira com
`php -m | grep pcntl` dentro do contêiner.
:::

## Reciclar antes de engordar

Um processo PHP de requisição web vive milissegundos; um worker vive
semanas. Pequenos vazamentos que nunca aparecem numa requisição — um
array de cache que só cresce, uma conexão de banco que ninguém fecha, uma
biblioteca que guarda referências — aparecem num worker como memória
subindo devagar até o processo ser morto pelo sistema.

A defesa é simples e não depende de achar o vazamento: o worker se
encerra sozinho depois de um número de mensagens, e o supervisor sobe um
novo.

```php title="src/Workers/Avisos.php" numbered
<?php

declare(strict_types=1);

namespace DoceMirabel\Workers;

use Mirabel\RabbitMQ\Envelope;
use Mirabel\RabbitMQ\Worker;

final class Avisos extends Worker
{
    public static string $queue = 'avisos.pedidos';
    public static array $routingKeys = ['pedido.*'];

    private int $atendidas = 0;

    public function __construct(private readonly int $limite = 1000)
    {
    }

    public function handle(Envelope $envelope): void
    {
        echo "e-mail do pedido {$envelope->body['pedido']}", PHP_EOL;

        if (++$this->atendidas >= $this->limite) {
            $this->stop();
        }
    }
}
```

`++$this->atendidas` soma um antes de comparar. Com um limite de três e
cinco pedidos na fila:

```text
e-mail do pedido 40201
e-mail do pedido 40202
e-mail do pedido 40203
```

O processo termina com código 0, e os dois pedidos restantes continuam na
fila, esperando o processo novo que o supervisor vai subir. Para o
supervisor, um worker que sai com código 0 não é uma falha — é só mais um
reinício.

:::key
Um worker de produção tem quatro garantias, e cada uma é de um lugar
diferente: **o supervisor** o levanta quando ele morre; **a biblioteca**
reconecta quando o broker cai; **o `SIGTERM` com `pcntl`** o deixa
terminar a mensagem antes do deploy; **a reciclagem** o renova antes que a
memória o mate.
:::

:::milestone
Você tem: workers em contêineres com `restart: unless-stopped` e prazo de
parada, reconectando sozinhos quando o broker reinicia, terminando a
mensagem em mãos antes de sair num deploy, e se reciclando depois de mil
mensagens. Nenhum deles roda no notebook de ninguém.
:::

:::summary
- Workers rodam sob um supervisor — Docker com `restart`, Supervisor ou
	systemd —, que os inicia, reinicia e para com `SIGTERM`.
- Quando o broker cai, a Mirabel reconecta com backoff exponencial, sem
	limite por padrão; o heartbeat detecta conexões mortas no caminho.
- Com `pcntl`, `SIGTERM` vira `stop()`: a mensagem em mãos termina e é
	confirmada antes de o processo sair. Sem `pcntl`, ou depois do prazo,
	ela volta para a fila.
- O prazo de parada precisa ser maior que o `handle()` mais lento.
- Um worker que chama `stop()` depois de N mensagens é renovado pelo
	supervisor antes que vazamentos de memória o matem.
:::

:::exercise level=1
O `handle()` do fiscal pode levar até 45 segundos quando a SEFAZ está
lenta, e o Compose usa o `stop_grace_period` padrão do Docker, de 10
segundos. O que acontece com uma nota sendo emitida durante um deploy?

:::answer
O Docker manda `SIGTERM`; o worker marca que precisa parar, mas continua
esperando a SEFAZ. Dez segundos depois, o Docker manda `SIGKILL` e o
processo morre no meio da emissão. A mensagem, sem ack, volta para a fila
e é entregue ao worker novo — que pode emitir a nota de novo, se a SEFAZ
tiver autorizado a primeira. A reserva por pedido do capítulo sobre
idempotência impede a segunda emissão, mas deixa a nota em `emitindo`.

A correção é `stop_grace_period: 60s` no serviço do fiscal: maior que o
pior `handle()`.
:::

:::exercise level=2
A Denise pergunta por que não basta pôr `restart: always` e deixar o
worker cair quando quiser, já que o Docker o levanta de novo. Responda
com o que se perde em cada caso.

:::answer
O Docker levanta o processo, mas não protege a mensagem que estava no
meio. Um worker que "cai quando quiser" morre com uma mensagem sem ack,
que é entregue de novo — trabalho repetido, e às vezes um efeito
repetido, como uma etiqueta a mais. Se ele cai por um defeito que se
repete a cada mensagem, o `restart` vira um laço: sobe, pega a mesma
mensagem, morre, sobe de novo, sem nunca chegar ao retry nem à fila de
erro, porque o erro não é uma exceção que a biblioteca capture.

O supervisor é a última linha de defesa, não a primeira. As primeiras são
a biblioteca tratando exceções, o encerramento gracioso e a reciclagem.
:::
