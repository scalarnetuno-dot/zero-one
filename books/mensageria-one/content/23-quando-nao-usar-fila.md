---
title: "Quando a fila é a resposta errada"
number: 23
slug: quando-nao-usar-fila
part: p5
kicker: "O frete saiu em um milissegundo e meio pela fila. Quando o consumidor caiu, o carrinho ficou três segundos esperando uma resposta que ninguém ia dar."
goal: >-
  Reconhecer os casos em que uma fila piora o sistema — perguntas que
  precisam de resposta, consistência que o cliente vê, trabalho pequeno
  demais para justificar um broker — e decidir, com critério, o que fica
  síncrono.
---

:::story O frete
Com o checkout desmontado, o Rafa ficou animado.

— Agora põe o frete na fila também. A cotação da transportadora é lenta.

— O frete aparece no carrinho — disse Júlia. — O cliente digita o CEP e
espera o valor.

— Então ele espera na fila.

— Ele espera **a fila**. E a fila espera um consumidor. E o consumidor
espera a transportadora.

— Mas não é mais rápido?

A Júlia abriu um terminal e rodou um teste. Duzentas cotações pela fila,
um milissegundo e meio de mediana.

— É rápido — disse ela. — Agora olha isso.

Ela parou o consumidor e rodou de novo.

*sem resposta em 3 s*

— O carrinho do cliente ficou três segundos parado — disse o Kaique. —
E depois?

— Depois nada. A cotação ficou na fila. Quando o consumidor voltar, ele
vai responder para um carrinho que já foi fechado.
:::

Depois de vinte e dois capítulos a favor da fila, este é contra ela — nos
lugares em que ela não serve. A fila resolve um problema específico:
trabalho que precisa ser feito, mas não precisa ser feito **agora**, por
alguém que não precisa estar de pé **agora**. Quando o problema é outro,
ela troca uma dependência simples por uma complicada.

## Perguntas que precisam de resposta

O frete no carrinho é uma **pergunta**: o cliente só segue depois de saber
o valor. Dá para fazer uma pergunta pelo RabbitMQ — o padrão se chama
**RPC** sobre mensageria, *remote procedure call*: o cliente publica o
pedido com o endereço de resposta na propriedade `reply_to` e um
`correlation_id`, e espera a resposta chegar. O RabbitMQ tem até um
endereço especial para isso, `amq.rabbitmq.reply-to`, que entrega a
resposta direto no canal de quem perguntou, sem fila nenhuma.

O servidor da cotação consome, calcula e responde para o `reply_to`:

```php title="frete-servidor.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();
$canal->queue_declare('frete.cotacoes', false, true, false, false);

$responder = function (AMQPMessage $pedido) use ($canal): void {
    $cep = json_decode($pedido->getBody(), true)['cep'];
    $valor = json_encode(['cep' => $cep, 'frete_centavos' => 1890]);
    $canal->basic_publish(
        new AMQPMessage($valor, [
            'correlation_id' => $pedido->get('correlation_id'),
        ]),
        '',
        $pedido->get('reply_to'),
    );
    $pedido->ack();
};

$canal->basic_consume(
    'frete.cotacoes', '', false, false, false, false, $responder,
);
while ($canal->is_consuming()) {
    $canal->wait();
}
```

O cliente publica e espera, com um limite de três segundos:

```php title="frete-cliente.php" numbered
<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Exception\AMQPTimeoutException;
use PhpAmqpLib\Message\AMQPMessage;

$conexao = new AMQPStreamConnection(
    'localhost', 5672, 'guest', 'guest',
);
$canal = $conexao->channel();
$resposta = null;

$canal->basic_consume(
    'amq.rabbitmq.reply-to', '', false, true, false, false,
    function (AMQPMessage $m) use (&$resposta): void {
        $resposta = json_decode($m->getBody(), true);
    },
);

$tempos = [];
for ($i = 0; $i < (int) ($argv[1] ?? 100); $i++) {
    $resposta = null;
    $inicio = microtime(true);
    $pergunta = new AMQPMessage(json_encode(['cep' => '37701-000']), [
        'reply_to' => 'amq.rabbitmq.reply-to',
        'correlation_id' => (string) $i,
    ]);
    $canal->basic_publish($pergunta, '', 'frete.cotacoes');
    try {
        while ($resposta === null) {
            $canal->wait(null, false, 3);
        }
    } catch (AMQPTimeoutException) {
        echo 'sem resposta em 3 s', PHP_EOL;
        exit(1);
    }
    $tempos[] = (microtime(true) - $inicio) * 1000;
}
sort($tempos);
$mediana = $tempos[intdiv(count($tempos), 2)];
printf("%d cotações: mediana %.1f ms, pior %.1f ms\n",
    count($tempos), $mediana, end($tempos));
```

O consumidor de `amq.rabbitmq.reply-to` precisa ser registrado com
`no_ack` ligado, e **antes** do primeiro publish — é assim que o broker
sabe para onde mandar as respostas daquele canal. `intdiv()` é a divisão
inteira, e `end()` devolve o último elemento do array ordenado, o pior
tempo.

Com o servidor no ar:

```text
$ php frete-cliente.php 200
200 cotações: mediana 1.5 ms, pior 5.4 ms
```

Rápido. Agora sem o servidor:

```text
$ php frete-cliente.php 1
sem resposta em 3 s
```

Aí está o problema. Pela fila, a pergunta não **falha**: ela espera.
Uma chamada HTTP à transportadora fora do ar recusa a conexão em
milissegundos, e o carrinho mostra "frete indisponível, tente de novo".
Pela fila, o carrinho fica pendurado até o limite que alguém escolheu, e a
pergunta fica guardada no broker para ser respondida mais tarde — para
ninguém.

:::key
A fila desacopla no tempo, e é exatamente por isso que ela é ruim para
perguntas: quem pergunta **precisa** de quem responde, agora. RPC sobre
mensageria recria o acoplamento temporal com mais peças — um broker, um
consumidor, um timeout, respostas órfãs — e sem o erro rápido que o HTTP
dá de graça.
:::

RPC sobre mensageria tem lugar — quando o serviço que responde não pode
receber conexões diretas, ou quando as perguntas precisam ser dosadas por
uma fila —, mas não é o jeito padrão de perguntar. O frete da Doce
Mirabel continua uma chamada HTTP, com timeout curto e um valor de
contingência quando a transportadora não responde.

## Consistência que o cliente vê

O segundo caso é o estoque no carrinho. A página diz "restam 2 vidros de
geleia de ameixa", e o cliente compra os dois. Se a reserva desses vidros
for um evento numa fila, processado segundos depois, dois clientes podem
comprar os mesmos dois vidros no intervalo — e um deles recebe, depois de
pago, um e-mail dizendo que acabou.

O que o cliente **vê** e **decide** a partir dele precisa ser consistente
no momento em que ele decide. A reserva do estoque é uma escrita no banco,
na mesma transação do pedido, com uma condição:

```sql
UPDATE produtos
   SET reservados = reservados + 2
 WHERE sku = 'GEL-AMX-320'
   AND estoque - reservados >= 2;
```

Se o `UPDATE` não alterar nenhuma linha, não havia estoque, e o checkout
recusa antes de cobrar. A baixa no ERP da fábrica — que leva segundos e
cai às vezes — continua sendo um consumidor de `pedido.pago`. O que o
cliente vê fica síncrono; o que a fábrica precisa saber fica na fila.

## Trabalho pequeno demais

O terceiro caso não é técnico: é de tamanho. Um broker é mais um sistema
em produção — um servidor, atualizações de segurança, um painel, alertas,
alguém que entenda o que é uma fila `.error`. Para uma loja que manda
vinte e-mails por dia, o custo é maior que o problema.

O próprio framework costuma ter uma resposta menor. O Laravel tem filas
com o driver `database`: os jobs vão para uma tabela, e um `queue:work`
os processa, com retry e tabela de falhas. Sem broker, sem exchange, sem
cluster. Ela não tem roteamento, fan-out nem as garantias de um broker —
e, para vinte e-mails, não precisa.

| Sinal | Tende a pedir |
|---|---|
| um produtor, um consumidor, pouco volume | a fila do próprio framework |
| vários sistemas interessados no mesmo fato | broker com exchange (fan-out) |
| serviços em linguagens ou equipes diferentes | broker: a mensagem é o contrato |
| falhas externas longas que não podem virar erro | broker, retry com espera, outbox |
| o usuário espera a resposta para seguir | chamada síncrona, com timeout |

Tabela: A Doce Mirabel passou a precisar de um broker na terceira linha
de baixo para cima; antes disso, a fila do Laravel teria bastado.

## O round do CheckoutController

O `CheckoutController` do Marcelão ganha, no fim, uma disputa: a
**cobrança** continua síncrona. O cliente precisa saber, antes de sair da
página, se o cartão foi aprovado — é uma pergunta, e a resposta decide o
que ele vê. Nenhum desenho deste livro pôs o pagamento numa fila, e é
isso que o separa do "só coloca uma fila" do Rafa no primeiro capítulo.

:::story O que ficou
No fim da tarde, o Kaique fez uma lista no verso de uma etiqueta: o que
ficou síncrono e o que foi para a fila.

*Síncrono: pagamento. Frete. Estoque do carrinho.*

*Fila: nota. Etiqueta. E-mail. WhatsApp. Pontos. Baixa no ERP.*

Mostrou para a Dona Cida, que leu com os óculos na ponta do nariz.

— O de cima eu fazia com o cliente no telefone — disse ela. — O de baixo
eu fazia depois de desligar.
:::

:::milestone
Você tem: a cotação de frete como chamada HTTP com timeout curto; a
reserva de estoque síncrona, na transação do pedido; o pagamento
síncrono, como sempre foi; e todo o resto em filas — com um critério
escrito para a próxima vez que alguém disser "só coloca uma fila".
:::

:::summary
- Uma fila serve para trabalho que precisa ser feito, mas não agora, por
	quem não precisa estar de pé agora.
- RPC sobre mensageria é rápido quando tudo está no ar e ruim quando não
	está: a pergunta espera, em vez de falhar, e a resposta pode chegar para
	ninguém.
- O que o cliente vê e decide — estoque, frete, pagamento — precisa ser
	consistente no momento da decisão, e fica síncrono.
- Um broker é mais um sistema em produção; para pouco volume e um
	consumidor, a fila do framework basta.
- Fan-out, várias linguagens e falhas externas longas são os sinais de que
	um broker se paga.
:::

:::exercise level=1
O Rafa quer que o cupom de desconto seja validado "pela fila", porque o
sistema de cupons é lento. O que acontece com o carrinho, e qual é a
alternativa?

:::answer
O cupom é uma pergunta: o total do carrinho depende da resposta. Pela
fila, o carrinho espera o consumidor e, se ele estiver fora, espera até o
timeout sem saber se o desconto vale — e o cliente pode pagar o valor
cheio, ou desistir.

A alternativa é chamar o sistema de cupons diretamente, com timeout
curto, e, se ele não responder, mostrar "não conseguimos validar o cupom
agora" em vez de travar. Se ele é lento sempre, o problema é de
desempenho dele — um cache dos cupons válidos resolve mais do que uma
fila na frente.
:::

:::exercise level=2
Para cada item, diga se você usaria chamada síncrona, fila do framework ou
broker, e por quê: (a) gerar o PDF de um relatório mensal que o
financeiro pede uma vez por mês; (b) avisar três sistemas diferentes que
um cliente mudou de endereço; (c) conferir se um CPF é válido no
cadastro.

:::answer
(a) Fila do framework. É trabalho demorado que não precisa bloquear a
tela, com um produtor e um consumidor, uma vez por mês. Um broker seria
maior que o problema.

(b) Broker. É um fato que interessa a três sistemas — fan-out —, e cada
um pode estar fora do ar em horas diferentes. Um evento
`cliente.endereco-alterado` num exchange, com uma fila por sistema.

(c) Síncrono, e local. Validar CPF é uma conta de dígito verificador, sem
serviço externo. Nem HTTP é preciso — muito menos fila.
:::
