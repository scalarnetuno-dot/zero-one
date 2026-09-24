---
title: "Repetições"
number: 9
slug: repeticoes
part: p1
kicker: "Funciona com doze. O problema é que ninguém testa com oito mil."
goal: >-
  Percorrer arrays com `foreach`, repetir sob condição sem travar o
  servidor, acumular resultados, e medir o custo de um laço antes que ele
  chegue a produção.
---

:::story Era para ser um relatorinho
Quinta-feira, 16h40. Cléber apareceu no canto da mesa do Dedé com a postura
de quem vai pedir uma coisa pequena.

— É rapidinho. Uma listinha dos livros atrasados.

— Só isso?

— Só isso. Com o nome do leitor do lado.

Dedé escreveu em onze minutos. Rodou na máquina dele, com os doze
empréstimos de teste que a Tainá tinha cadastrado antes do almoço:
instantâneo.

Subiu às 17h20. Sexta-feira ainda estava longe, então tecnicamente não era
deploy na sexta.

Às 17h50 a Vera ligou dizendo que a tela do relatório estava branca havia
vinte minutos e que tinha gente esperando no balcão.

Na Casa Amarela há 8.412 empréstimos em aberto e 1.204 leitores
cadastrados.
:::

O relatório do Dedé não estava errado. Ele estava **certo doze vezes**, que
é uma categoria de defeito bem mais interessante — e bem mais cara — do que
código simplesmente quebrado.

## `foreach` é o laço

```php title="listar.php" numbered
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas Secas', 'dias' => 2],
    ['titulo' => 'Grande Sertão', 'dias' => 41],
];

foreach ($atrasados as $emprestimo) {
    echo $emprestimo['titulo'], ' - ',
         $emprestimo['dias'], " dias\n";
}
```

```text
O Cortiço - 9 dias
Vidas Secas - 2 dias
Grande Sertão - 41 dias
```

Leia como está escrito: *para cada item de `$atrasados`, chame-o de
`$emprestimo` e execute o bloco*.

Não há índice, não há `$i`, não há `count()`. Onde não existe índice não
existe como errar o índice, e uma classe inteira de defeitos clássicos
simplesmente não tem onde acontecer.

Quando a chave importa, ela vem junto:

```php title="com_chave.php" numbered
<?php

$por_assunto = [
    'literatura' => 1240,
    'infantil' => 870,
    'referencia' => 91,
];

foreach ($por_assunto as $assunto => $total) {
    echo $assunto, ': ', $total, "\n";
}
```

```text
literatura: 1240
infantil: 870
referencia: 91
```

A mesma forma serve para lista e para mapa, porque as duas são o mesmo tipo.
Numa lista, a chave é a posição numérica.

:::pitfall
`foreach` trabalha sobre uma **cópia** do array. Alterar `$emprestimo` dentro
do laço não altera o array original:

```php
foreach ($atrasados as $emprestimo) {
    $emprestimo['dias'] = 0;   // não muda nada lá fora
}
```

Existe a forma `foreach ($atrasados as &$emprestimo)`, com `&`, que trabalha
por referência e altera o original. Ela funciona e traz um problema clássico
junto: depois do laço, `$emprestimo` continua apontando para o último item,
e o próximo `foreach` que reutilizar esse nome sobrescreve a última posição
do array.

Se usar `&`, escreva `unset($emprestimo);` na linha seguinte ao laço. Se
puder não usar, não use: montar um array novo é mais previsível.
:::

## `for` e `while`

```php title="for.php" numbered
<?php

for ($pagina = 1; $pagina <= 3; $pagina++) {
    echo "Pagina ", $pagina, "\n";
}
```

```text
Pagina 1
Pagina 2
Pagina 3
```

O `for` tem três partes separadas por ponto e vírgula: onde começa, até
quando continua, e o que fazer ao fim de cada volta. Ele serve quando o
**número** é o assunto — paginação, repetição fixa, contagem regressiva —,
não quando há uma coleção para percorrer.

```php title="while.php" numbered
<?php

$tentativas = 0;
$conectado = false;

while ($tentativas < 3 && !$conectado) {
    $tentativas++;
    echo "Tentativa ", $tentativas, "\n";
    $conectado = ($tentativas === 3);
}
```

```text
Tentativa 1
Tentativa 2
Tentativa 3
```

O `while` repete enquanto a condição for verdadeira. Serve quando a parada
não depende de uma coleção: tentar de novo, ler até acabar, esperar até
responder.

:::warning
Todo `while` precisa de uma resposta escrita para a pergunta *"o que, aqui
dentro, torna a condição falsa algum dia?"*. No exemplo acima é o
`$tentativas++`.

E quando a parada depender de algo externo — rede, arquivo, outro sistema —,
o laço precisa **também** de um limite de tentativas. Repare no
`$tentativas < 3`: sem ele, uma instabilidade de rede vira um processo PHP
girando para sempre, ocupando um trabalhador do servidor que nunca mais
atende ninguém.
:::

## `break` e `continue`

```php title="controle.php" numbered
<?php

$exemplares = [
    ['tombo' => 812, 'status' => 'restauro'],
    ['tombo' => 907, 'status' => 'disponivel'],
    ['tombo' => 344, 'status' => 'disponivel'],
];

$escolhido = null;

foreach ($exemplares as $exemplar) {
    if ($exemplar['status'] !== 'disponivel') {
        continue;
    }

    $escolhido = $exemplar['tombo'];
    break;
}

echo $escolhido ?? 'nenhum livre', "\n";
```

```text
907
```

`continue` pula para a volta seguinte. `break` abandona o laço inteiro.

Repare em `$escolhido = null` **antes** do laço. Sem essa linha, uma lista
vazia ou totalmente indisponível deixaria a variável sem existir, e a linha
final imprimiria um aviso em vez de uma mensagem.

:::pitfall
O PHP aceita `break 2` e `continue 2`, para sair de dois níveis de laço de
uma vez. É sintaticamente válido e humanamente ilegível: quem lê precisa
contar chaves para saber de onde o código vai sair, e no dia em que alguém
acrescentar um `if` no meio, o número continua `2` e passa a apontar para
outro lugar, sem erro nenhum.
:::

## O acumulador

Boa parte dos laços não imprime nada: constrói um valor.

```php title="acumulador.php" numbered
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas Secas', 'dias' => 2],
    ['titulo' => 'Grande Sertão', 'dias' => 41],
];

$total_de_dias = 0;
$criticos = 0;

foreach ($atrasados as $emprestimo) {
    $total_de_dias = $total_de_dias + $emprestimo['dias'];

    if ($emprestimo['dias'] > 30) {
        $criticos++;
    }
}

echo $total_de_dias, " dias no total\n";
echo $criticos, " caso(s) critico(s)\n";
```

```text
52 dias no total
1 caso(s) critico(s)
```

Somar, contar e filtrar são o mesmo esqueleto: uma variável criada **antes**
do laço, modificada **dentro**, lida **depois**. Criar o acumulador dentro do
laço é o erro que zera o resultado a cada volta e devolve, no fim, apenas o
último item.

O PHP já traz alguns acumuladores prontos para os casos mais comuns:

```php title="prontos.php" numbered
<?php

$dias = [9, 2, 41, 0, 15];

echo array_sum($dias), "\n";
echo max($dias), "\n";
echo min($dias), "\n";
echo count($dias), "\n";
```

```text
67
41
0
5
```

## Doze registros mentem

Agora o relatório daquela quinta-feira. Era isto, no osso: para cada
empréstimo, encontrar o leitor correspondente na lista de leitores.

```php title="relatorio_lento.php" numbered
<?php

$emprestimos = [];
for ($i = 0; $i < 8412; $i++) {
    $emprestimos[] = ['leitor_id' => $i % 1204];
}

$leitores = [];
for ($i = 0; $i < 1204; $i++) {
    $leitores[] = ['id' => $i, 'nome' => "Leitor {$i}"];
}

$inicio = microtime(true);
$linhas = 0;

foreach ($emprestimos as $emprestimo) {
    foreach ($leitores as $leitor) {
        if ($leitor['id'] === $emprestimo['leitor_id']) {
            $linhas++;
            break;
        }
    }
}

printf("%d linhas em %.3f s\n", $linhas, microtime(true) - $inicio);
```

```text
8412 linhas em 0.412 s
```

As duas primeiras partes geram dados de teste com o `for` que você acabou de
ver. O `%` devolve o resto da divisão, o que faz os identificadores de
leitor darem a volta entre 0 e 1203.

`microtime(true)` devolve o horário atual como número com casas decimais.
Guardar antes, subtrair depois, e você mediu um trecho de código. É a
ferramenta de medição mais barata que existe e resolve a maioria das
dúvidas.

Rode na sua máquina. O número vai ser diferente do meu; a ordem de grandeza
vai ser parecida.

Repare no que está acontecendo: para cada um dos 8.412 empréstimos, o
programa percorre a lista de leitores até achar o certo. Em média, seiscentas
comparações por empréstimo. **Cinco milhões de comparações** para imprimir
oito mil linhas.

Com os doze empréstimos de teste da Tainá eram 7.200 comparações, que o PHP
faz sem piscar. A diferença entre os dois casos não é o código. É a escala.

## Indexar antes de percorrer

O conserto é montar, uma vez só, um mapa de leitor por identificador — e
depois acessar direto, sem procurar:

```php title="relatorio_rapido.php" numbered
<?php

// mesmos $emprestimos e $leitores de antes

$inicio = microtime(true);

$leitor_por_id = [];
foreach ($leitores as $leitor) {
    $leitor_por_id[$leitor['id']] = $leitor;
}

$linhas = 0;
foreach ($emprestimos as $emprestimo) {
    $leitor = $leitor_por_id[$emprestimo['leitor_id']] ?? null;

    if ($leitor !== null) {
        $linhas++;
    }
}

printf("%d linhas em %.3f s\n", $linhas, microtime(true) - $inicio);
```

```text
8412 linhas em 0.002 s
```

Duzentas vezes mais rápido, com quatro linhas a mais.

O que mudou não foi a quantidade de trabalho aparente — os dois programas
percorrem os empréstimos uma vez. O que mudou foi o **custo de encontrar um
leitor**: de "procurar numa lista de 1.204" para "pegar direto pela chave".
Um mapa acessa por chave em tempo praticamente constante, não importa
quantos itens tenha.

O PHP faz essa indexação numa linha:

```php
$leitor_por_id = array_column($leitores, null, 'id');
```

`array_column` extrai uma coluna de um array de registros. Com `null` no
segundo argumento ela mantém o registro inteiro; o terceiro diz qual campo
usar como chave. Vale conhecer a versão manual primeiro, porque é ela que
explica o que a função está fazendo.

:::key
Toda vez que escrever um laço, responda duas perguntas: **quantas voltas ele
vai dar em produção** e **quanto custa uma volta**. Multiplique.

Se o resultado passar de um segundo, você tem uma decisão a tomar — e não um
detalhe para resolver depois.
:::

E há uma variante desse mesmo formato que é muito pior. Troque a comparação
de dentro do laço por uma ida a outra máquina pela rede, e cada volta deixa
de custar nanossegundos e passa a custar milissegundos. O mesmo laço que
levou quatro décimos de segundo passa a levar meia hora.

Esse padrão tem nome — **N+1** — e é provavelmente o defeito de desempenho
mais comum em aplicação web: uma busca para trazer a lista, mais uma busca
por item da lista. Ele nasce aqui, num laço inocente, muito antes de existir
banco de dados no projeto.

## A pequena mudança de escopo

:::story Uma pequena mudança de escopo
Na terça seguinte, Cléber voltou.

— Ficou ótimo o relatório. Tivemos só uma pequena mudança de escopo.

Dedé esperou.

— A diretoria quer o histórico junto. Quantas vezes cada leitor atrasou no
ano.

— Isso é outro relatório.

— É a mesma tela. Só uma coluninha a mais.

A "coluninha a mais" era mais uma busca por leitor, dentro do laço que já
percorria oito mil empréstimos. Dedé fez a conta em voz alta, e Cléber ouviu
o número até o fim.

— Mas na sua máquina funciona, né?

— Funciona. Na minha máquina tem doze.

Cléber pensou por um instante.

— E se a gente colocar doze na produção também?
:::

:::note Na sua carreira
"Funciona na minha máquina" quase nunca é desonestidade — é **ausência de
dado**. A pergunta que resolve isso, e que vale levar para qualquer reunião
de refinamento, tem doze palavras:

> *"Quantos registros isso vai percorrer em produção, no pior mês do ano?"*

Se ninguém souber responder, essa é a primeira tarefa, e ela leva dez
minutos. Perguntar isso **antes** de estimar é uma das diferenças concretas
entre um júnior e um pleno, e não tem nada a ver com saber mais sintaxe.

E há uma segunda pergunta, que quase ninguém faz: *"quantas linhas dessa
tela alguém vai ler de verdade?"*. Um relatório de oito mil linhas não é
lido por ninguém. Se a resposta for "as cinquenta primeiras", o problema de
desempenho tinha uma solução de produto antes de ter uma solução técnica.
:::

:::summary
- `foreach` percorre arrays; `for` é para número; `while` é para condição.
- `foreach` trabalha sobre uma cópia — `&` altera o original e exige `unset`
	depois.
- Todo `while` precisa de algo que torne a condição falsa, e de um limite de
	tentativas quando depende de fora.
- `continue` pula a volta, `break` abandona o laço; `break 2` é ilegível.
- Acumulador nasce antes do laço, muda dentro, é lido depois.
- Laço dentro de laço multiplica: meça com `microtime(true)` antes de
	acreditar.
- Indexar por chave troca busca linear por acesso direto.
- Custo do laço é voltas × custo por volta — e uma volta que sai da máquina
	custa um milhão de vezes mais.
:::

:::checkpoint
Você percorre arrays, repete sob condição com segurança, acumula resultados,
e consegue medir e estimar em voz alta quantas operações um laço vai
executar em produção.
:::

:::exercise level=1
Dada a lista de dias de atraso `[9, 2, 41, 0, 15]`, use um `foreach` para
calcular o total, a média e quantos casos passam de trinta dias. Depois
confira o total com `array_sum`.

:::answer
```php
<?php

$dias = [9, 2, 41, 0, 15];

$total = 0;
$criticos = 0;

foreach ($dias as $d) {
    $total = $total + $d;

    if ($d > 30) {
        $criticos++;
    }
}

$media = $total / count($dias);

echo "total ", $total, "\n";
echo "media ", $media, "\n";
echo "criticos ", $criticos, "\n";
echo "conferindo ", array_sum($dias), "\n";
```

```text
total 67
media 13.4
criticos 1
conferindo 67
```

Repare que a média saiu com casas decimais mesmo sendo `67 / 5`: a divisão
com `/` devolve `float` quando não é exata. Se o resultado precisasse ser
inteiro, a decisão de arredondar ou truncar teria que estar escrita.
:::

:::exercise level=2
Escreva um laço que encontre o empréstimo com mais dias de atraso e imprima
o título. Trate o caso da lista vazia.

:::answer
```php
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas Secas', 'dias' => 2],
    ['titulo' => 'Grande Sertão', 'dias' => 41],
];

$pior = null;

foreach ($atrasados as $emprestimo) {
    if ($pior === null || $emprestimo['dias'] > $pior['dias']) {
        $pior = $emprestimo;
    }
}

if ($pior === null) {
    echo "nenhum atraso\n";
} else {
    echo $pior['titulo'], " com ", $pior['dias'], " dias\n";
}
```

```text
Grande Sertão com 41 dias
```

A condição tem duas partes por um motivo: na primeira volta não existe nada
para comparar, e `$pior === null` cobre isso. Inicializar `$pior` com o
primeiro item do array também funcionaria — e quebraria com a lista vazia,
que é justamente o caso que o exercício pediu para tratar.

Repare também no curto-circuito: quando `$pior === null` é verdadeiro, o
lado direito do `||` nem chega a ser avaliado. Sem isso, a comparação
tentaria ler `$pior['dias']` de um valor nulo.
:::

:::exercise level=3
O trecho abaixo conta quantos empréstimos de livros infantis houve. Ele leva
vários segundos com os dados reais. Identifique os três problemas, diga qual
você consertaria primeiro e por quê.

```php
$total = 0;

foreach ($leitores as $leitor) {
    foreach ($emprestimos as $emp) {
        if ($emp['leitor_id'] !== $leitor['id']) {
            continue;
        }

        foreach ($livros as $livro) {
            if ($livro['id'] === $emp['livro_id']
                && $livro['assunto'] === 'infantil') {
                $total++;
            }
        }
    }
}

echo $total;
```

:::answer
**Problema 1 — três laços aninhados.** São 1.204 leitores × 8.412
empréstimos × 4.000 livros no pior caso. A conta chega perto de quarenta
bilhões de comparações, e nenhuma máquina desta década termina isso dentro
de uma requisição web.

**Problema 2 — busca linear onde caberia um mapa.** Os dois laços internos
estão procurando por identificador. Indexar `$livros` por `id` antes de
começar troca o terceiro laço por um acesso direto.

**Problema 3 — o laço externo não serve para nada.** Repare no resultado:
`$total` é um número só. A variável `$leitor` é usada apenas para comparar
com `$emp['leitor_id']` — e, como todo empréstimo pertence a algum leitor, a
comparação sempre acha um par. O laço de 1.204 voltas existe para chegar ao
mesmo número que se obteria sem ele.

**O que eu consertaria primeiro é o terceiro**, e essa é a parte importante
da resposta.

Os problemas 1 e 2 são otimizações de um código que não deveria existir.
Consertar a indexação aqui é deixar o mesmo algoritmo errado, só mais
rápido. A pergunta real — "quantos empréstimos de livros infantis houve?" —
não menciona leitor nenhum.

```php
<?php

$livro_por_id = array_column($livros, null, 'id');

$total = 0;

foreach ($emprestimos as $emp) {
    $livro = $livro_por_id[$emp['livro_id']] ?? null;

    if ($livro !== null && $livro['assunto'] === 'infantil') {
        $total++;
    }
}

echo $total, "\n";
```

Quarenta bilhões de comparações viraram oito mil. E note de onde veio o
ganho: não de o laço ter ficado mais esperto, e sim de dois laços terem
deixado de existir.

**A regra geral:** antes de otimizar um laço, pergunte se ele deveria estar
ali. Boa parte do código lento é código correto resolvendo o problema no
lugar errado.
:::
