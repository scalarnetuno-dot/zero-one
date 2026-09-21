---
title: "Repetições"
number: 6
slug: repeticoes
part: p1
kicker: "Funciona com doze. O problema é que ninguém testa com oito mil."
goal: >-
  Percorrer coleções com `foreach`, repetir sob condição sem travar o
  servidor, e reconhecer — antes de existir banco de dados — a forma do
  defeito que vai custar quatro horas de madrugada no capítulo 30.
---

:::story Era para ser um relatorinho
Quinta-feira, 16h40. Cléber apareceu no canto da mesa do Dedé com aquela
postura de quem vai pedir uma coisa pequena.

— É rapidinho. Uma listinha dos livros atrasados.

— Só isso?

— Só isso. Com o nome do leitor do lado.

Dedé escreveu em onze minutos. Rodou na máquina dele com os doze empréstimos
de teste da Tainá: instantâneo.

Subiu às 17h20 — sexta-feira ainda estava longe, então tecnicamente não era
deploy na sexta.

Às 17h50 a Vera ligou dizendo que a tela do relatório estava branca há vinte
minutos.

São 8.412 empréstimos em aberto na Casa Amarela.
:::

O relatório do Dedé não estava errado. Ele estava **certo doze vezes**, o
que é uma categoria de erro bem mais interessante — e bem mais cara — do que
código simplesmente quebrado.

Um laço que funciona com doze registros pode falhar com oito mil. A diferença
entre os dois casos é a escala.

## Doze registros mentem

Um laço faz o que você mandou, o número de vezes que você mandou, sem
opinar. Se dentro dele houver uma operação que custa vinte milissegundos, e
o laço rodar oito mil vezes, são dois minutos e quarenta segundos. Ninguém
escreveu "espere dois minutos" em lugar nenhum — isso simplesmente
aconteceu.

E a razão de isso pegar todo mundo é que o dado de desenvolvimento é sempre
pequeno. Doze registros. Trinta. A Tainá cadastrou os que deu tempo antes do
almoço.

:::key
Toda vez que você escrever um laço, responda duas perguntas: **quantas
voltas ele vai dar em produção** e **quanto custa uma volta**. Multiplique.
Se o resultado passar de um segundo, você tem uma decisão a tomar — não um
detalhe.
:::

## Repetir sem perder o controle

```php title="listar.php" numbered
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas Secas', 'dias' => 2],
    ['titulo' => 'Grande Sertão', 'dias' => 41],
];

foreach ($atrasados as $emprestimo) {
    echo $emprestimo['titulo'], ' — ',
         $emprestimo['dias'], " dias\n";
}
```

```text
O Cortiço — 9 dias
Vidas Secas — 2 dias
Grande Sertão — 41 dias
```

Não há índice, não há `$i`, não há `count()`. Onde não existe índice, não
existe como errar o índice — e uma classe inteira de defeitos clássicos
simplesmente não tem onde acontecer.

Quando você precisa da chave, ela vem junto:

```php title="com_chave.php" numbered
<?php

$por_assunto = [
    'literatura' => 1240,
    'infantil' => 870,
    'referencia' => 91,
];

foreach ($por_assunto as $assunto => $total) {
    printf("%-12s %5d\n", $assunto, $total);
}
```

```text
literatura    1240
infantil       870
referencia      91
```

Essa forma funciona igual para lista e para mapa, porque em PHP as duas são
a mesma estrutura — assunto do capítulo @cap:arrays.

### `for` e `while`, e quando eles ainda servem

```php title="outros_lacos.php" numbered
<?php

for ($pagina = 1; $pagina <= 5; $pagina++) {
    echo "Processando página {$pagina}\n";
}

$tentativas = 0;
while ($tentativas < 3 && !conectar()) {
    $tentativas++;
    sleep(1);
}
```

`for` serve quando o **número** é o assunto: paginação, repetição fixa,
contagem regressiva. `while` serve quando a condição de parada não é uma
coleção: tentar de novo, ler até acabar, esperar até responder.

:::warning
Todo `while` precisa de uma resposta escrita para a pergunta *"o que, aqui
dentro, torna a condição falsa algum dia?"*. Se a resposta depender de algo
externo — rede, arquivo, outro sistema —, o laço precisa **também** de um
limite de tentativas. Repare no `$tentativas < 3` do exemplo: sem ele, uma
instabilidade de rede vira um processo PHP girando para sempre, consumindo
um trabalhador do servidor que nunca mais atende ninguém.
:::

## O relatório dos atrasados

Aqui está o que ele escreveu naquela quinta-feira, simplificado ao osso:

```php title="relatorio_atrasados.php" numbered
<?php

$emprestimos = buscarEmprestimosAbertos();

foreach ($emprestimos as $emprestimo) {
    $leitor = buscarLeitor($emprestimo['leitor_id']);
    $exemplar = buscarExemplar($emprestimo['exemplar_id']);
    $livro = buscarLivro($exemplar['livro_id']);

    echo $livro['titulo'], ' — ', $leitor['nome'], "\n";
}
```

Leia de novo e conte as idas ao banco. São **três por empréstimo**, mais a
consulta inicial.

Com 12 empréstimos: 37 consultas. Rápido.

Com 8.412 empréstimos: **25.237 consultas**. Na máquina do Dedé, com o banco
local, isso levava oito segundos. No servidor da Casa Amarela, com o banco
em outra máquina e dois milissegundos de ida e volta, passou de cinquenta
segundos — e o PHP desistiu antes, no limite de tempo.

```text
PHP Fatal error: Maximum execution time of 30 seconds
exceeded in /app/relatorio.php on line 7
```

Trinta segundos, linha 7. A linha 7 é `buscarLeitor()`, e ela não tem defeito
nenhum. O defeito é ela estar **ali dentro**.

:::key
Esse padrão tem nome — **N+1** — e é provavelmente o defeito de desempenho
mais comum em aplicações web. Uma consulta para trazer a lista, mais uma
consulta por item da lista. Ele nasce aqui, num laço inocente, muito antes
de existir ORM. No capítulo @cap:relacionamentos ele volta disfarçado de
ponto: `$emprestimo->leitor->nome`.
:::

## A pequena mudança de escopo

O Dedé consertou o relatório às 18h10 e foi embora. Na terça seguinte,
Cléber voltou.

:::story Uma pequena mudança de escopo
— Ficou ótimo o relatório. Tivemos só uma pequena mudança de escopo.

Dedé esperou.

— A diretoria quer o histórico junto. Quantas vezes cada leitor atrasou no
ano.

— Isso é outro relatório.

— É a mesma tela. Só uma coluninha a mais.

A "coluninha a mais" era uma consulta por leitor, dentro do laço que já
percorria oito mil empréstimos. O Dedé fez a conta em voz alta e Cléber
ouviu o número.

— Mas na sua máquina funciona, né?

— Funciona. Na minha máquina tem doze.

Cléber pensou por um instante.

— E se a gente colocar doze na produção também?
:::

## O custo escondido de uma volta

Três coisas aconteceram ao mesmo tempo, e vale separar, porque as três têm
conserto diferente.

**A primeira é de custo por volta.** A operação dentro do laço não era
aritmética — era rede. Uma operação de memória custa nanossegundos; uma
consulta ao banco em outra máquina custa milissegundos. A diferença é de um
milhão de vezes, e ela não aparece em nenhum lugar do código.

**A segunda é de volume desconhecido.** Ninguém sabia quantos empréstimos
abertos existiam. Não é que alguém tenha estimado errado: ninguém estimou.

**A terceira é de forma.** O dado necessário — título e nome — podia ter sido
trazido de uma vez só, com uma consulta que junta as tabelas. O laço estava
fazendo, um por um, o que o banco de dados faz de uma vez e muito melhor.

:::note Na sua carreira
"Funciona na minha máquina" quase nunca é desonestidade — é **ausência de
dado**. A pergunta que resolve isso, e que vale levar para qualquer reunião
de refinamento, tem doze palavras:

> *"Quantos registros isso vai percorrer em produção, no pior mês do ano?"*

Se ninguém souber responder, essa é a primeira tarefa — e ela leva dez
minutos com um `SELECT COUNT(*)`. Perguntar isso antes de estimar é uma das
diferenças concretas entre um júnior e um pleno, e não tem nada a ver com
saber mais sintaxe.
:::

## Traga os dados antes do laço

Três correções, em ordem de quanto cada uma resolve.

**1. Tire a consulta de dentro do laço.** Por enquanto, sem banco, a versão
didática é buscar tudo de uma vez e indexar na memória:

```php title="sem_n_mais_um.php" numbered
<?php

$emprestimos = buscarEmprestimosAbertos();

$ids = array_column($emprestimos, 'leitor_id');
$leitores = buscarLeitoresPorIds(array_unique($ids));

foreach ($emprestimos as $emprestimo) {
    $leitor = $leitores[$emprestimo['leitor_id']];
    echo $leitor['nome'], "\n";
}
```

Duas consultas em vez de 8.413. `array_column` extrai uma coluna do array de
arrays, e `array_unique` evita pedir o mesmo leitor doze vezes.

**2. Imponha um teto.** Relatório de tela não mostra oito mil linhas —
ninguém lê oito mil linhas. Ele mostra as primeiras cinquenta e oferece o
resto por outro caminho. Isso é a paginação do capítulo
@cap:paginacao-filtros-e-buscas, e a hora certa de colocá-la é **antes** de
precisar.

**3. Se for grande de verdade, saia da requisição.** Um relatório de oito
mil linhas com exportação é trabalho de fila, não de página — capítulo
@cap:events-jobs-e-filas. O usuário pede, a resposta é imediata, e o arquivo
chega depois.

### O acumulador

Boa parte dos laços não imprime nada: constrói um valor.

```php title="acumulador.php" numbered
<?php

$total = 0;
$criticos = 0;

foreach ($atrasados as $emprestimo) {
    $total += $emprestimo['dias'];

    if ($emprestimo['dias'] > 30) {
        $criticos++;
    }
}

printf("%d dias no total, %d casos críticos\n",
    $total, $criticos);
```

Somar, contar e filtrar são o mesmo esqueleto: uma variável criada **antes**
do laço, modificada **dentro**, lida **depois**. Criar o acumulador dentro do
laço é o erro que zera o resultado a cada volta.

E o PHP já traz vários acumuladores prontos:

```php title="prontos.php" numbered
<?php

$dias = array_column($atrasados, 'dias');

echo array_sum($dias), "\n";
echo max($dias), "\n";
echo count($dias), "\n";
```

### Quando o laço vira expressão

```php title="expressao.php" numbered
<?php

$criticos = array_filter(
    $atrasados,
    fn(array $e): bool => $e['dias'] > 30
);

$titulos = array_map(
    fn(array $e): string => $e['titulo'],
    $atrasados
);
```

A régua é simples: se o laço **transforma** uma coleção em outra,
`array_map` e `array_filter` dizem isso melhor. Se ele **faz coisas** —
grava, envia, registra —, o `foreach` é mais claro. As duas funções voltam
com calma no capítulo @cap:arrays.

## `break`, `continue` e o resto

```php title="controle.php" numbered
<?php

foreach ($exemplares as $exemplar) {
    if ($exemplar['status'] !== 'disponivel') {
        continue;
    }

    emprestar($exemplar);
    break;
}
```

`continue` pula para a volta seguinte; `break` abandona o laço. Os dois
servem à mesma ideia da cláusula de guarda do capítulo @cap:condicionais:
resolver o caso chato cedo e manter o corpo principal raso.

O PHP também aceita `break 2` e `continue 2`, para sair de dois níveis de
uma vez.

:::pitfall
`break 2` é sintaticamente válido e humanamente ilegível. Quem lê precisa
contar chaves para saber de onde o código vai sair — e, no dia em que alguém
acrescentar um `if` no meio, o número continua `2` e passa a apontar para
outro lugar, sem erro nenhum. Se você precisou de `break 2`, o laço interno
provavelmente quer ser uma função com `return`.
:::

:::summary
- `foreach` percorre itens; `for` é para número; `while` é para condição.
- Todo `while` precisa de algo que torne a condição falsa — e de um limite
  de tentativas, quando depende de fora.
- Consulta dentro de laço é o N+1, e ele nasce muito antes do ORM.
- Estime o custo do laço: voltas × custo por volta.
- Acumulador nasce antes do laço, muda dentro, é lido depois.
- Laço que transforma coleção quer ser `array_map` ou `array_filter`.
- `break 2` é legível pelo interpretador e não por pessoas.
:::

:::checkpoint
Você percorre coleções, repete sob condição com segurança, e consegue
estimar em voz alta quantas operações um laço vai executar em produção.
:::

:::exercise level=1
Dada a lista de dias de atraso `[9, 2, 41, 0, 15]`, imprima o total de dias,
a média e quantos casos passam de trinta dias.

:::answer
```php
<?php

$dias = [9, 2, 41, 0, 15];

$total = array_sum($dias);
$media = $total / count($dias);
$criticos = count(array_filter($dias, fn($d) => $d > 30));

printf("total %d, média %.1f, %d críticos\n",
    $total, $media, $criticos);
```
```text
total 67, média 13.4, 1 críticos
```
`count(array_filter(...))` é o idioma para "quantos satisfazem a condição".
Escrever o `foreach` equivalente custa cinco linhas e a mesma clareza.
:::

:::exercise level=2
Escreva um laço que percorra os exemplares e pare no primeiro disponível,
imprimindo o tombo. Se nenhum estiver disponível, imprima `"sem exemplar
livre"`. Cuidado com o caso da lista vazia.

:::answer
```php
<?php

$encontrado = null;

foreach ($exemplares as $exemplar) {
    if ($exemplar['status'] === 'disponivel') {
        $encontrado = $exemplar;
        break;
    }
}

echo $encontrado === null
    ? "sem exemplar livre\n"
    : "tombo {$encontrado['tombo']}\n";
```
A variável `$encontrado` inicializada como `null` **antes** do laço é o que
faz a lista vazia funcionar: sem ela, a linha de baixo tentaria ler uma
variável que nunca foi criada. Em PHP isso dá aviso e continua — que é pior
do que dar erro.
:::

:::exercise level=3
O trecho abaixo gera o relatório mensal da Casa Amarela. Ele leva quatro
minutos com os dados reais. Identifique os três problemas, diga qual deles
você consertaria primeiro e por quê.

```php
$total = 0;
foreach (buscarLeitores() as $leitor) {
    foreach (buscarEmprestimos($leitor['id']) as $emp) {
        $livro = buscarLivro($emp['livro_id']);
        if ($livro['assunto'] === 'infantil') {
            $total++;
        }
    }
}
echo $total;
```

:::answer
**Problema 1 — N+1 aninhado.** São 1.200 leitores, cada um disparando uma
consulta de empréstimos, cada empréstimo disparando uma consulta de livro.
Com uma média de sete empréstimos por leitor, são mais de nove mil
consultas.

**Problema 2 — filtro no lugar errado.** O código traz **todos** os
empréstimos de todos os leitores pela rede, para descartar a maioria num
`if` em PHP. O banco faria esse filtro sem transportar nada.

**Problema 3 — o laço externo não serve para nada.** Repare no resultado:
`$total` é um número só. O leitor nunca é usado. O código percorre 1.200
leitores para chegar a uma contagem que não depende de leitor nenhum.

**O que eu consertaria primeiro é o terceiro**, e essa é a parte importante
da resposta. Os problemas 1 e 2 são otimizações de um código que não deveria
existir. Consertar o N+1 aqui é deixar o mesmo algoritmo errado, só mais
rápido.

A pergunta real é "quantos empréstimos de livros infantis houve?", e ela tem
uma resposta de uma linha:

```sql
SELECT COUNT(*) FROM emprestimo e
JOIN exemplar x ON x.id = e.exemplar_id
JOIN livro l ON l.id = x.livro_id
WHERE l.assunto = 'infantil';
```

Quatro minutos viram alguns milissegundos — não porque o laço ficou mais
esperto, mas porque ele deixou de existir. É o que o capítulo
@cap:banco-de-dados-e-sql quer dizer com "aprender SQL o bastante para saber
o que não fazer em PHP".

**A regra geral, que vale para o resto do livro:** antes de otimizar um
laço, pergunte se ele deveria estar ali. Boa parte do código lento é código
correto resolvendo o problema na camada errada.
:::

:::story A piada final
Na sexta, o Dr. Aurélio passou pela mesa e viu o relatório aberto na tela.

— Isso aqui é aquele dashboard em tempo real?

— É um relatório de atrasados.

— Ótimo. A gente precisa disso em tempo real.

— Ele demora quatro minutos.

— Então em tempo real a cada quatro minutos.

Dedé abriu a boca e fechou. Anotou no caderno, na linha de baixo daquela
frase da Vera: *"o sistema precisa saber a diferença entre zero e nada"*.

Escreveu: *"e entre agora e a cada quatro minutos"*.
:::
