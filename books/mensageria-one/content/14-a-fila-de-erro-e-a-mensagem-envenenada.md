---
title: "A fila de erro e a mensagem envenenada"
number: 14
slug: a-fila-de-erro-e-a-mensagem-envenenada
part: p4
kicker: "Duzentas e catorze mensagens na fila de erro numa segunda de manhã, e a primeira sugestão foi apagar."
goal: >-
  Tratar a fila de erro como uma caixa de pendências, separar falha
  temporária de permanente e de mensagem envenenada, ler o motivo de cada
  mensagem parada, e devolvê-las à fila principal sem herdar a contagem de
  tentativas antigas.
---

:::story Duzentas e catorze
Na segunda de manhã, o painel mostrava 214 mensagens em
`fiscal.pedidos-pagos.error`. O fim de semana tinha sido de promoção.

— O que é isso? — perguntou o Rafa.

— Pedidos pagos cuja nota não saiu — disse a Júlia.

— Duzentos e catorze?

— Duzentos e catorze.

— Então apaga e manda de novo.

— Apagar é perder. Mandar de novo, sem saber por que falhou, é mandar
para lá outra vez.

O Seu Norberto, que tinha vindo buscar um café, parou na porta.

— Duzentas e catorze vendas sem nota fiscal?

— Por enquanto.

— "Por enquanto" tem prazo. A nota tem que sair até o fim do dia seguinte
à venda.

O Kaique abriu a primeira mensagem da fila no painel. Leu os headers em
voz alta.

— CEP inválido. — Abriu a segunda. — CEP inválido. — A terceira. — CEP
inválido.

— Todos do mesmo lugar?

O Kaique rolou a tela.

— 37704. Todos. É o loteamento novo do lado da rodovia.
:::

A fila de erro do capítulo @cap:workers-com-mirabel parecia, até aqui, um
detalhe: um lugar onde paravam os testes com CEP 00000-000. Na segunda de
manhã, ela virou o que é de verdade — a lista de trabalho que o sistema não
conseguiu fazer sozinho. Ela tem três perguntas: **por que** cada mensagem
está lá, **o que** precisa mudar para ela dar certo, e **como** devolvê-la
sem repetir o erro.

## Três tipos de falha

Toda mensagem na fila de erro caiu num destes três casos, e cada um pede
uma coisa diferente.

| Tipo | Exemplo | Tentar de novo resolve? | O que fazer |
|---|---|---|---|
| temporária | SEFAZ fora, ERP travado | sim, se esperar | tentativas com `delay`; se esgotaram, reprocessar depois |
| permanente | CEP que não existe, produto fora de linha | não | `reject()`; corrigir a causa; decidir se reprocessa |
| envenenada | corpo que não é JSON, schema desconhecido | nunca | investigar quem publicou aquilo |

Tabela: A fila de erro junta os três, e o header de motivo é o que os
separa.

A falha **temporária** só chega à fila de erro quando a janela de
tentativas foi menor que a queda. As 214 da segunda poderiam ser
temporárias — um fim de semana de SEFAZ instável — e aí bastaria
devolvê-las.

A **permanente** é a que o código sabe reconhecer: um CEP fora de
qualquer faixa válida não vai passar a existir na décima tentativa. O
`handle()` deveria chamar `$envelope->reject()` e poupar todas as
tentativas. Mas "permanente" é relativo ao código: o CEP 37704 existe; ele
só não estava na tabela de CEPs do worker fiscal, que era de 2024. A falha
é permanente **até alguém atualizar a tabela**.

A **envenenada** é a que nem chega ao código: um produtor antigo, um teste
manual pelo painel, um sistema de outra equipe publicando texto em vez de
JSON. A Mirabel a manda direto para a fila de erro com o motivo `poison`,
sem chamar o `handle()`. Ela não se conserta com reprocessamento; se
conserta com uma conversa com quem publicou.

:::term Mensagem envenenada
Uma mensagem que nenhuma tentativa consegue processar, porque o problema
está nela mesma — formato inválido, versão desconhecida, campo obrigatório
faltando. Se voltar para a fila, ela falha de novo, e com `requeue` ela
trava a fila inteira num laço. O nome vem de *poison message*.
:::

## Lendo antes de agir

Duzentas mensagens não se leem uma a uma no painel. O primeiro passo é
**agrupar pelo motivo**, e é o que os headers `x-mirabel-*` permitem. O
painel mostra os headers de cada mensagem em *Get messages*; para a fila
inteira, um script lê sem tirar nada do lugar — com *Nack message requeue
true*, o equivalente no código é pegar e devolver.

Na segunda de manhã, o agrupamento dizia:

| `x-mirabel-exception` | Mensagens |
|---|---|
| `RuntimeException: CEP inválido` | 211 |
| `JsonException: Syntax error` | 3 |

Duas causas, dois tratamentos. As 211 são o loteamento novo: a causa está
**no fiscal**, que não conhece a faixa 37704, e o corpo das mensagens está
certo. As 3 envenenadas vieram de um teste de carga que o Kaique fez
publicando texto pelo painel na sexta, no exchange de produção — e essas
podem, depois de conferidas, ser apagadas.

:::key
A fila de erro é lida por **motivo**, não por mensagem. O motivo diz onde
está a causa — no consumidor, no dado, no produtor ou num serviço externo —
e cada causa tem um dono diferente.
:::

## Devolver sem repetir

Corrigida a causa — a tabela de CEPs do fiscal atualizada e o worker
reiniciado —, as 211 precisam voltar à fila principal. O RabbitMQ não
move mensagens de uma fila para outra sozinho; alguém precisa ler da fila
de erro e publicar de novo na principal, pelo default exchange, com o nome
da fila.

A primeira versão desse script é óbvia, e errada — o miolo de um
`reprocessar-ingenuo.php`:

```php
while ($mensagem = $canal->basic_get("{$fila}.error")) {
    $copia = new AMQPMessage(
        $mensagem->getBody(),
        $mensagem->get_properties(),
    );
    $canal->basic_publish($copia, '', $fila);
    $mensagem->ack();
}
```

`basic_get` pega **uma** mensagem da fila, sem registrar um consumidor, e
devolve `null` quando a fila está vazia — o que encerra o `while`. O corpo
e as propriedades são copiados, a cópia é publicada na fila principal, e a
original é confirmada.

Rode isso com um pedido que ainda vai falhar — a causa não foi corrigida:

```text
$ php reprocessar-ingenuo.php fiscal.pedidos-pagos
devolvidas: 1
```

E, no worker:

```text
tentativa 3 do 40118: falhou
```

Direto para a tentativa **3**, e de volta para a fila de erro na primeira
falha. A cópia levou junto o header `x-death`, com as duas expirações da
primeira rodada; para o worker, esta é a terceira tentativa, e três é o
limite. Uma falha temporária devolvida assim não ganha nenhuma espera nova:
uma SEFAZ ainda instável manda tudo de volta para a fila de erro em
segundos.

A cópia precisa sair **limpa** — sem o histórico de mortes nem o bilhete
de erro:

```php title="reprocessar.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;
use PhpAmqpLib\Wire\AMQPTable;

[, $fila] = $argv;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();
$historico = [
    'x-death', 'x-first-death', 'x-last-death', 'x-mirabel-',
];

[, $total] = $canal->queue_declare("{$fila}.error", true);
$movidas = 0;

for ($i = 0; $i < $total; $i++) {
    $mensagem = $canal->basic_get("{$fila}.error");
    if ($mensagem === null) {
        break;
    }

    $propriedades = $mensagem->get_properties();
    $headers = $propriedades['application_headers']->getNativeData();
    foreach (array_keys($headers) as $nome) {
        foreach ($historico as $prefixo) {
            if (str_starts_with($nome, $prefixo)) {
                unset($headers[$nome]);
            }
        }
    }
    $propriedades['application_headers'] = new AMQPTable($headers);

    $copia = new AMQPMessage($mensagem->getBody(), $propriedades);
    $canal->basic_publish($copia, '', $fila);
    $mensagem->ack();
    $movidas++;
}
echo "devolvidas: {$movidas} de {$total}", PHP_EOL;
```

A linha 21 pergunta ao broker quantas mensagens a fila de erro tem
**agora**: `queue_declare` com `passive` em `true` não cria nada, só
devolve o nome e a contagem. O laço vai até esse número e para. Sem esse
limite, um `while` que lê até a fila esvaziar pode não terminar nunca: uma
mensagem devolvida que falha de novo — uma envenenada, uma causa não
corrigida — volta para a fila de erro enquanto o script ainda está lendo,
e ele a devolve outra vez, e outra.

`getNativeData()` transforma os headers da mensagem num array PHP comum;
`AMQPTable` faz o caminho inverso. `str_starts_with()` confere se um texto
começa com outro. Os headers que começam com `x-death`, `x-first-death` e
`x-last-death` são o histórico que o broker escreve; os `x-mirabel-` são o
bilhete da biblioteca. Os de negócio — `x-idempotency-key`,
`x-schema-version` — ficam.

Com a causa corrigida:

```text
$ php reprocessar.php fiscal.pedidos-pagos
devolvidas: 1 de 1
```

```text
tentativa 1 do 40118: NF-e emitida
```

Tentativa 1, com todas as tentativas e esperas de volta, e a fila de erro
em zero.

:::pitfall
O script confirma a mensagem da fila de erro **depois** de publicar a
cópia. Se ele cair entre as duas linhas, a mensagem fica nas duas filas, e
o pedido é processado duas vezes. Na ordem inversa, cair no meio perde o
pedido. É a janela de sempre entre "fiz" e "apaguei" — e é por isso que o
consumidor precisa aguentar receber o mesmo pedido de novo.
:::

## Regras para a segunda de manhã

Reprocessar é uma operação de produção, e vale a mesma disciplina de um
deploy:

1. **Agrupe por motivo antes de tocar em qualquer coisa.** Cada grupo tem
	uma causa e um dono.
2. **Corrija a causa antes de devolver.** Devolver sem corrigir é mandar
	a mensagem de volta, gastando as tentativas dela de novo.
3. **Devolva limpo**, sem `x-death` nem `x-mirabel-*`.
4. **Devolva aos poucos**, se forem milhares: o worker vai processá-las
	junto com o tráfego normal, e duzentas notas de uma vez na SEFAZ pesam.
5. **Apague só o que foi lido e entendido** — as envenenadas, depois de
	saber de onde vieram.

E a regra que evita a segunda de manhã: **a fila de erro tem que estar
vazia**. Uma mensagem nela é trabalho parado com prazo. Um alerta quando o
número passa de zero vale mais do que qualquer painel bonito, porque a
pergunta do Seu Norberto — quantas vendas estão sem nota? — é exatamente
o tamanho dessa fila.

:::milestone
Você tem: a fila de erro tratada como caixa de pendências, lida por
motivo; o `reprocessar.php`, que devolve mensagens à fila principal sem o
histórico de tentativas; e a regra de que ela deve ficar em zero, com
alguém avisado quando não fica.
:::

:::summary
- Falhas são temporárias (tentar de novo resolve), permanentes (não
	resolve até corrigir a causa) ou envenenadas (a própria mensagem é
	inválida); a fila de erro junta as três.
- `x-mirabel-failure-reason` e `x-mirabel-exception` permitem agrupar a
	fila por motivo, e o motivo diz quem é o dono da causa.
- Reprocessar é ler da `.error` e publicar na fila principal pelo default
	exchange; o RabbitMQ não move mensagens sozinho.
- Uma cópia com `x-death` herda a contagem antiga e volta para a fila de
	erro na primeira falha; é preciso remover o histórico e o bilhete.
- A fila de erro deve ficar em zero, com alerta quando não fica.
:::

:::exercise level=1
A fila de erro tem três mensagens com `x-mirabel-failure-reason = poison`.
Por que reprocessá-las, com ou sem limpeza, não adianta, e o que você
precisa descobrir antes de apagá-las?

:::answer
O corpo delas não é JSON válido, e o reprocessamento publica o mesmo
corpo. A biblioteca vai tentar decodificar de novo, falhar de novo, e
mandá-las de volta para a fila de erro na hora — limpeza de headers não
muda os bytes do corpo.

Antes de apagar, é preciso saber **quem publicou** e **o que elas
deveriam ser**. O `type`, o `timestamp` e o `message_id` das propriedades
ajudam a achar o produtor. Se forem um teste esquecido, apagar resolve. Se
forem pedidos reais de um sistema que publica num formato errado, apagar
perde vendas — e a correção é no produtor, com as mensagens reconstruídas
a partir da origem.
:::

:::exercise level=2
Modifique o `reprocessar.php` para receber um terceiro argumento, um
texto, e só devolver as mensagens cujo `x-mirabel-exception` contenha esse
texto; as outras continuam na fila de erro.

:::answer
O laço limitado pela contagem já resolve metade do problema: basta não
responder às mensagens que não casam. Uma mensagem pega com `basic_get` e
sem ack fica *Unacked* no canal do script, e volta sozinha para a fila de
erro quando o canal fecha:

```php
[, $fila, $filtro] = $argv;
// ... conexão, canal e $historico como antes

[, $total] = $canal->queue_declare("{$fila}.error", true);
for ($i = 0; $i < $total; $i++) {
    $mensagem = $canal->basic_get("{$fila}.error");
    if ($mensagem === null) {
        break;
    }

    $propriedades = $mensagem->get_properties();
    $headers = $propriedades['application_headers']->getNativeData();
    $erro = (string) ($headers['x-mirabel-exception'] ?? '');
    if (!str_contains($erro, $filtro)) {
        continue; // sem resposta: volta quando o canal fechar
    }
    // ... limpa, publica na fila principal e dá ack, como antes
}

$canal->close();
$conexao->close();
```

Com duas mensagens de CEP inválido e uma envenenada na fila,
`php reprocessar.php fiscal.pedidos-pagos "CEP inválido"` devolve duas de
três, e a envenenada continua na fila de erro.

A tentação é responder `nack(true)` às que não casam. Não funciona: o
RabbitMQ devolve uma mensagem com requeue para a **posição original**, na
frente da fila, e o `basic_get` seguinte pega exatamente a mesma — o
script para de avançar na primeira mensagem que não casa.
:::
