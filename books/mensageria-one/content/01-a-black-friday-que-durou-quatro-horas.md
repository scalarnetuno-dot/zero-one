---
title: "A Black Friday que durou quatro horas"
number: 1
slug: a-black-friday-que-durou-quatro-horas
part: p1
kicker: "O gateway cobrou, a SEFAZ não respondeu, e 311 pessoas pagaram por uma página de erro."
goal: >-
  Medir quanto tempo uma cadeia de chamadas síncronas custa, calcular a
  disponibilidade dela, reproduzir a falha que cobra o cliente sem entregar
  o pedido e separar o trabalho que precisa ser feito agora do trabalho que
  só precisa ser feito.
---

:::story Trezentos e onze estornos
A reconstituição aconteceu na mesa da cozinha da fábrica, porque era a
única sala com tomada para três notebooks.

O Seu Norberto abriu a planilha que ele tinha montado em dezembro, com o
extrato do gateway de um lado e a lista de pedidos da loja do outro.

— Das 9h52 às 13h50, o gateway aprovou 1.140 cobranças. A loja registrou
829 pedidos completos. A diferença são 311 pessoas que pagaram e não
receberam nada. Estornamos todas até o dia 3.

— Por que a loja não registrou? — perguntou Júlia.

— Isso eu não sei. Eu sei o que saiu do banco.

O Rafa virou o notebook dele para a mesa. Tinha um print do painel da
hospedagem: CPU em 100% das 10h às 14h.

— O servidor não aguentou. Era só ter comprado um servidor maior.

— O servidor estava esperando — disse Júlia. — Cem por cento de CPU com
quatrocentos processos parados, cada um segurando um cliente enquanto a
SEFAZ não respondia.

O Kaique levantou a mão, o que ninguém mais fazia na cozinha.

— Teve um senhor que pagou três vezes. Pedido 40.117. Ele me ligou às duas
da tarde falando que tinha apertado o botão até aparecer alguma coisa.

— E apareceu?

— Apareceu. O erro 500.

A Dona Cida, que estava do outro lado da cozinha mexendo uma panela, falou
sem se virar.

— Na época do caderno, o pedido estava feito quando eu anotava. Fazer a
geleia era outra coisa.
:::

A frase da Dona Cida é o capítulo inteiro, e ela não sabe disso. O checkout
da Doce Mirabel não separa as duas coisas: para ele, o pedido só está feito
quando a geleia foi cobrada, baixada do estoque, faturada, etiquetada,
avisada por e-mail, avisada por WhatsApp e convertida em pontos. Se
qualquer uma das sete falhar, o pedido não existe — mesmo que o dinheiro já
tenha saído da conta do cliente.

Antes de falar de fila, vale medir o que esse desenho custa. São três
números: o tempo, a disponibilidade e o estrago de uma falha no meio.

## Sete chamadas em fila indiana

Chamada **síncrona** é aquela em que quem chama fica parado esperando a
resposta. O `CheckoutController` faz sete, uma depois da outra, e o
navegador do cliente espera todas.

Dá para reproduzir isso sem banco, sem Laravel e sem nenhuma das sete
empresas. Cada chamada vira uma espera do tamanho que ela costuma levar:

```php title="checkout.php" numbered
<?php

declare(strict_types=1);

$foraDoAr = $argv[1] ?? '';

$passos = [
    'pagamento' => 400,
    'estoque' => 900,
    'nfe' => 1200,
    'etiqueta' => 600,
    'email' => 300,
    'whatsapp' => 500,
    'fidelidade' => 200,
];

function chamar(string $passo, int $ms, bool $noAr): void
{
    usleep($ms * 1000);
    if (!$noAr) {
        throw new RuntimeException(
            "{$passo}: sem resposta depois de {$ms} ms",
        );
    }
    printf("%-12s %5d ms\n", $passo, $ms);
}

$inicio = microtime(true);
foreach ($passos as $passo => $ms) {
    chamar($passo, $ms, $passo !== $foraDoAr);
}
printf("%-12s %5d ms\n", 'total', (microtime(true) - $inicio) * 1000);
```

Três funções da biblioteca padrão fazem o trabalho. `usleep()` para o
programa pelo número de **micro**ssegundos que recebe — por isso o `* 1000`,
que converte milissegundos. `microtime(true)` devolve o instante atual em
segundos, com casas decimais; a diferença entre dois instantes, vezes mil,
é o tempo gasto em milissegundos. E `printf()` imprime com formato:
`%-12s` é um texto alinhado à esquerda em doze colunas, `%5d` é um inteiro
em cinco.

A linha 5 lê o primeiro argumento da linha de comando. `$argv` é o array
que o PHP monta com o que veio depois do nome do script; se nada veio, o
`?? ''` deixa a variável vazia e nenhum passo fica fora do ar.

Rode:

```text
$ php checkout.php
pagamento      400 ms
estoque        900 ms
nfe           1200 ms
etiqueta       600 ms
email          300 ms
whatsapp       500 ms
fidelidade     200 ms
total         4103 ms
```

Quatro segundos. É a soma exata das sete esperas, mais três milissegundos
do próprio PHP. Numa chamada síncrona em sequência, **o tempo total é a
soma de todos os tempos**, e ele é tão rápido quanto a soma permitir.

Numa terça-feira, quatro segundos passam despercebidos. Na Black Friday, a
SEFAZ — o sistema da Secretaria da Fazenda que autoriza cada nota fiscal —
passou a responder em trinta segundos, depois parou de responder. Com o
mesmo desenho, cada cliente ficou esperando o pior dos sete.

## O que acontece quando uma das sete cai

O script aceita o nome de um passo para tirar do ar. Tire a nota fiscal:

```text
$ php checkout.php nfe
pagamento      400 ms
estoque        900 ms
PHP Fatal error:  Uncaught RuntimeException: nfe: sem resposta
depois de 1200 ms in checkout.php:21
```

Leia a saída de cima para baixo, porque a ordem é o defeito. O pagamento
**já foi feito**. O estoque **já foi baixado**. A exceção da nota fiscal
interrompeu o laço, e nada depois dela aconteceu: nem etiqueta, nem e-mail,
nem aviso à expedição.

No checkout de verdade, essa exceção vira uma página de erro 500. O cliente
não sabe que foi cobrado; sabe que o site deu erro. E faz o que qualquer
pessoa faz com um botão que não funcionou: aperta de novo.

:::pitfall
A reação instintiva é pôr um `try/catch` em volta de cada chamada e seguir
em frente. O `CheckoutController` tem três desses, vazios. Eles trocam uma
página de erro por um pedido pago **sem nota fiscal**, que ninguém fica
sabendo que existe até o Seu Norberto fechar o mês. Engolir a exceção não
resolve a falha: só muda quem a descobre, e quando.
:::

O pedido 40.117 foi exatamente isso, três vezes seguidas. Cada clique cobrou
o cartão no passo 1 e morreu no passo 3.

## A conta que ninguém fez

Existe um número mais incômodo que o tempo. Suponha que cada um dos sete
serviços fique no ar **99%** do tempo — o que, para uma API de terceiros, é
um número honesto. Qual é a chance de os sete estarem no ar ao mesmo tempo?

Como o checkout só funciona se todos funcionarem, as chances se
multiplicam: 0,99 × 0,99 × … sete vezes. O PHP faz a conta com o operador
`**`, que é a potência:

```text
$ php -r 'printf("%.1f%%\n", 0.99 ** 7 * 100);'
93.2%
$ php -r 'printf("%.0f horas\n", (1 - 0.99 ** 7) * 24 * 365);'
595 horas
```

O `-r` executa o código que vem entre aspas sem precisar de arquivo. O
`%%` no formato imprime um `%` literal.

Sete serviços de 99% fazem um checkout de **93,2%**: quase seiscentas horas
por ano em que pelo menos um deles está fora — e o cliente não consegue
comprar. Nenhum dos sete fornecedores está descumprindo nada. O desenho é
que multiplica.

:::key
Numa cadeia síncrona, a disponibilidade do todo é o **produto** das
disponibilidades das partes, e o tempo de resposta é a **soma** dos tempos.
Cada dependência nova piora os dois números, mesmo que ela seja excelente.
:::

Melhorar cada fornecedor ajuda pouco e custa caro. Com sete serviços de
99,9% — três noves, o nível de contrato de um provedor de nuvem sério — o
checkout chega a 99,3%, ainda sessenta e uma horas por ano. A saída não é
exigir mais de cada um. É parar de exigir que todos estejam de pé **no
mesmo segundo**.

:::term Acoplamento temporal
Dois sistemas estão acoplados no tempo quando um só consegue trabalhar se o
outro estiver disponível naquele exato momento. Uma chamada síncrona é a
forma mais forte de acoplamento temporal: quem chama para enquanto quem
responde não responde.
:::

## Agora ou só feito?

A Dona Cida separava duas coisas que o checkout junta: **aceitar o pedido**
e **atender o pedido**. Aceitar precisa acontecer enquanto o cliente está
no balcão. Atender pode acontecer depois, desde que aconteça.

Passe os sete passos por essa pergunta:

| Passo | Precisa acontecer antes de responder ao cliente? | Por quê |
|---|---|---|
| pagamento | sim | sem pagamento aprovado não existe pedido |
| estoque | depende | a reserva é imediata; a baixa no ERP pode esperar |
| nfe | não | a nota tem que sair, e sair uma vez; não precisa sair neste segundo |
| etiqueta | não | ninguém embala às onze da noite |
| email | não | o cliente já está vendo a página de obrigado |
| whatsapp | não | a expedição olha o celular às sete |
| fidelidade | não | os pontos aparecem amanhã e ninguém liga |

Tabela: Um passo é obrigatório agora. Um está no meio. Cinco só precisam
ser feitos.

Cinco dos sete passos são trabalho que **precisa ser feito**, mas não
**agora**. Eles estão dentro da requisição por um único motivo: foi o jeito
mais simples de garantir que fossem feitos. Quando o código termina a
requisição, o PHP esquece tudo; se o e-mail não foi mandado ali, ninguém
mais vai lembrar de mandar.

O que falta, então, é um lugar para **anotar o trabalho que ficou para
depois** — um lugar que não esqueça quando o PHP esquece, que aguente o
dia em que a SEFAZ some, e de onde alguém tire o trabalho quando puder
fazê-lo. A Dona Cida tinha um prego na parede da cozinha onde espetava os
pedidos, e ele fazia exatamente isso.

:::story Só coloca uma fila
Na segunda seguinte, às 8h30, o Rafa entrou com o celular na mão.

— Li um post ontem. O cara é arquiteto de uma fintech. Ele diz que todo
e-commerce sério usa fila.

— Ele tem razão — disse Júlia.

— Então é isso. Só coloca uma fila.

— Coloca onde?

O Rafa olhou para o celular, como se o post fosse responder.

— No checkout.

— E o que vai para a fila?

— O pedido.

— E quem tira da fila?

Silêncio. O Kaique virou uma etiqueta de envio ao contrário e escreveu, com
a caneta da expedição: *fila = ?*

— Isso aí — disse o Rafa, apontando para a etiqueta. — Descobre isso e
coloca.
:::

:::practice
Pegue um sistema em que você trabalha — ou o último que você usou para
comprar alguma coisa — e escreva a lista do que acontece quando o botão
principal é apertado. Para cada item, responda a pergunta da tabela:
precisa acontecer antes da resposta? Se você não souber, esse é o item
mais perigoso da lista.
:::

:::summary
- Chamadas síncronas em sequência somam os tempos: o checkout leva 4,1
	segundos num dia bom e o tempo do pior serviço num dia ruim.
- A disponibilidade de uma cadeia síncrona é o produto das partes: sete
	serviços de 99% fazem um todo de 93,2%, quase 600 horas por ano fora.
- Uma exceção no meio da cadeia deixa o trabalho pela metade — o cliente
	cobrado e sem pedido — e o `try/catch` vazio só esconde isso.
- Acoplamento temporal é depender de outro sistema estar de pé no mesmo
	instante; é ele que transforma a queda da SEFAZ na queda da loja.
- Separar "aceitar" de "atender": só o pagamento precisa acontecer antes da
	resposta; o resto precisa de um lugar que não esqueça.
:::

:::exercise level=1
Rode `php checkout.php whatsapp`. Quais passos aconteceram, quais não
aconteceram, e o que o cliente vê?

:::answer
```text
$ php checkout.php whatsapp
pagamento      400 ms
estoque        900 ms
nfe           1200 ms
etiqueta       600 ms
email          300 ms
PHP Fatal error:  Uncaught RuntimeException: whatsapp: sem
resposta depois de 500 ms in checkout.php:21
```

Pagamento, estoque, nota, etiqueta e e-mail aconteceram. O aviso à
expedição e os pontos de fidelidade, não. O cliente vê um erro 500 — e,
alguns segundos depois, recebe o e-mail de confirmação de um pedido que o
site disse que falhou. É o pior dos dois mundos: ele foi atendido e acha
que não foi, e provavelmente vai comprar de novo.
:::

:::exercise level=2
A Doce Mirabel quer acrescentar um oitavo passo ao checkout: avisar um
sistema de antifraude, que o fornecedor garante estar no ar 99,5% do tempo.
Calcule a disponibilidade do checkout com oito passos (os sete de 99% mais
esse) e diga quantas horas por ano isso acrescenta.

:::answer
```text
$ php -r 'printf("%.2f%%\n", 0.99 ** 7 * 0.995 * 100);'
92.74%
$ php -r 'printf("%.0f horas\n", 0.99 ** 7 * 0.005 * 8760);'
41 horas
```

O `0.005` é a fatia de disponibilidade que o antifraude tira do todo, e
`8760` são as horas de um ano.

O checkout cai de 93,21% para 92,74% — cerca de 41 horas a mais por ano
fora do ar, por causa de um serviço que, sozinho, é melhor que todos os
outros sete. O argumento para a reunião é esse: o antifraude pode ser
excelente e ainda assim piorar a loja, se entrar na fila indiana.
:::
