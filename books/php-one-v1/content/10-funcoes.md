---
title: "Funções"
number: 10
slug: funcoes
part: p1
kicker: "Uma regra que mora em dez lugares muda em nove. O décimo é sempre o que gera o comprovante."
goal: >-
  Extrair regra para função, usar parâmetros e retorno com intenção,
  entender escopo sem recorrer a `global`, passar comportamento como
  argumento, e provar que a regra está certa sem subir nada.
---

:::story Cinquenta centavos
A diretoria da Casa Amarela aprovou, em ata, o aumento da multa diária de
R$ 0,50 para R$ 0,80. Seu Juvenal mandou mensagem no sábado:

> *"É só trocar o número, né? Pra segunda dá?"*

Dedé abriu o Sistema e buscou por `0.5`.

Sete resultados.

O cálculo da tela de devolução. O do relatório de pendências. O do recibo
impresso. O do e-mail de cobrança. Um dentro de um `if` que só roda em
dezembro, por algum motivo. Um comentado, com a data `// 2014` do lado. E um
sétimo, em `funcoes2_NOVO_final.php`, escrito como `50/100`.

Ele trocou os seis que estavam em uso e subiu no domingo.

Na segunda, a Vera ligou dizendo que o recibo impresso continuava com o
valor antigo.

O recibo não usava nenhum dos sete. Tinha o próprio, escrito como
`$dias * 0.50`, no meio de uma string de HTML, numa linha com quatrocentos e
doze caracteres.
:::

## Uma regra em dez lugares

Código duplicado não dá erro. Não aparece no log, não quebra nada, não
reclama na revisão — especialmente quando as cópias são levemente
diferentes, como `0.5`, `50/100` e `0.50`.

Ele só se manifesta quando a regra muda. E regra sempre muda: é o único
requisito garantido de qualquer sistema.

:::key
A pergunta que identifica duplicação problemática não é "esse código é
parecido?". É: **"quando essa regra mudar, de quantos lugares eu preciso
lembrar?"**

Se a resposta for maior que um, existe uma função esperando para nascer.
:::

:::art caption="Trocar o número é fácil. Difícil é achar todos os lugares onde ele mora."
src="trocar-o-numero-e-facil-dificil-e-achar-todos-os-lugares-onde-ele-mora.png"
Charge editorial minimalista em fundo branco: um desenvolvedor de trinta e
poucos anos, de moletom, segura uma lupa sobre um enorme mapa de arquivos
desdobrado na mesa. Sete marcas vermelhas mostram o mesmo número escrito de
jeitos diferentes — "0.5", "0.50", "50/100" — e todas já estão riscadas com
um X. Fora do mapa, na ponta da mesa, uma pequena impressora de recibo
solta uma tira de papel com o valor antigo, que ninguém está olhando.
Atrás dele, uma estagiária de caderno aberto aponta para a tira. Poucos
elementos, humor seco, estética de revista de tecnologia.
:::

## Dar nome à decisão

```php title="multa.php" numbered
<?php

function multaEmCentavos(int $dias_de_atraso): int
{
    if ($dias_de_atraso <= 0) {
        return 0;
    }

    return min($dias_de_atraso * 80, 2000);
}

echo multaEmCentavos(0), "\n";
echo multaEmCentavos(3), "\n";
echo multaEmCentavos(90), "\n";
```

```text
0
240
2000
```

A palavra `function`, o nome, os parâmetros entre parênteses, o tipo do que
volta, e o corpo entre chaves.

`return` faz duas coisas ao mesmo tempo: devolve o valor **e encerra a
função na hora**. Nada depois dele roda. É por isso que o primeiro `if` não
precisa de `else`: se o atraso for zero ou negativo, a função já acabou.

O `min()` devolve o menor entre os valores recebidos, o que aqui funciona
como teto: a multa nunca passa de dois mil centavos.

E repare onde estão os dois números da regra — `80` e `2000`. Num lugar só.
É a diferença entre a busca do Dedé devolver sete resultados e devolver um.

:::anatomy title="As partes de uma função"
lang: php
code: |
  function multaEmCentavos(
      int $dias,
      int $por_dia = 80,
  ): int {
      return min($dias * $por_dia, 2000);
  }
notes:
  - { line: 1, text: "O nome é um verbo ou uma pergunta. `multa()` é ambíguo; `multaEmCentavos()` diz até a unidade." }
  - { line: 2, text: "`int $dias` é obrigatório: quem chama precisa informar, e precisa ser inteiro." }
  - { line: 3, text: "`= 80` é o valor padrão. Parâmetro com padrão vem sempre depois dos obrigatórios." }
  - { line: 3, text: "A vírgula no último parâmetro é permitida desde o PHP 8 e evita ruído quando alguém acrescenta outro." }
  - { line: 4, text: "`: int` é o tipo do retorno. Sem ele, a função promete qualquer coisa." }
:::

Os tipos não são enfeite. Com eles, isto acontece:

```text
$ php -r 'function m(int $d): int { return $d * 80; } echo m("tres");'
PHP Fatal error: Uncaught TypeError: m(): Argument #1 ($d)
must be of type int, string given
```

A função recusou o argumento errado na porta, com uma mensagem que diz qual
argumento, qual tipo era esperado e qual chegou. Sem a declaração `int`, o
PHP tentaria converter `"tres"` e produziria um resultado sem sentido, em
silêncio.

## Tratar o caso ruim e sair

O `return` no meio da função abre uma forma de escrever decisões que não
existia antes:

:::compare left="Aninhado" right="Cláusula de guarda" lang="php"
function emprestar($l, $e) {
    if ($l !== null) {
        if ($l['ativo']) {
            if (!$e['preso']) {
                return 'ok';
            }
        }
    }
    return 'recusado';
}
---
function emprestar($l, $e) {
    if ($l === null) {
        return 'sem leitor';
    }
    if (!$l['ativo']) {
        return 'inativo';
    }
    if ($e['preso']) {
        return 'indisponivel';
    }
    return 'ok';
}
:::

Isso se chama **cláusula de guarda**: trate o caso ruim, saia, e deixe o
caminho principal encostado na margem esquerda.

O lado esquerdo cresce para a direita a cada regra nova. Com as onze regras
da Vera, o `return 'ok'` ficaria a quarenta e quatro espaços da margem, e
quem lê precisaria segurar onze condições na cabeça para entender como
chegou lá.

E repare no ganho que não é de formatação: cada motivo de recusa ficou
**ao lado da sua condição**, em vez de num `return` genérico a doze linhas
de distância. A versão da direita consegue dizer por que recusou; a da
esquerda, não.

:::key
Se o corpo principal da sua função está com três níveis de indentação, quase
sempre faltam guardas no começo. Indentação profunda não é problema
estético: é o número de condições que o leitor precisa manter na cabeça ao
mesmo tempo.
:::

## Parâmetros que se leem

```php title="chamadas.php" numbered
<?php

function registrarDevolucao(
    int $emprestimo_id,
    int $dias_de_atraso,
    bool $isentar_multa = false,
    bool $notificar_leitor = true,
): void {
    echo $emprestimo_id, ' ', $dias_de_atraso, ' ',
         var_export($isentar_multa, true), ' ',
         var_export($notificar_leitor, true), "\n";
}

registrarDevolucao(812, 9);
registrarDevolucao(812, 9, true, false);
registrarDevolucao(812, 9, isentar_multa: true);
```

```text
812 9 false true
812 9 true false
812 9 true true
```

`: void` diz que a função não devolve nada — ela faz alguma coisa e pronto.
`var_export($x, true)` devolve o valor como texto, o que aqui serve para
enxergar `true` e `false`, que o `echo` imprimiria como `1` e nada.

A terceira chamada usa **argumentos nomeados**, um recurso do PHP 8. Compare
com a segunda: `registrarDevolucao(812, 9, true, false)` obriga quem lê a
abrir a função para descobrir o que são aquele `true` e aquele `false`.

:::key
Quando uma chamada tiver um `true` ou um `false` solto, nomeie o argumento.
É o ganho de legibilidade mais barato que existe — zero custo de execução,
zero linhas a mais — e resolve para sempre a dúvida de quem lê o código daqui
a seis meses, que provavelmente é você.
:::

Argumentos nomeados também deixam pular os do meio: na terceira chamada,
`$isentar_multa` foi informado sem mencionar `$notificar_leitor`.

:::pitfall
Ao adotar argumentos nomeados, o **nome do parâmetro vira contrato
público**. Renomear `$isentar_multa` para `$sem_multa` passa a quebrar quem
chama, e o erro só aparece em execução, com uma mensagem sobre argumento
desconhecido.

Em código de biblioteca isso é sério. Em código de aplicação, é um incômodo
administrável. Vale saber antes de renomear, não depois.
:::

## Prometa um tipo só

```php title="retorno.php" numbered
<?php

function buscarLeitor(int $id): ?array
{
    $leitores = [
        47 => ['nome' => 'Marlene'],
        12 => ['nome' => 'Juvenal'],
    ];

    return $leitores[$id] ?? null;
}

var_dump(buscarLeitor(47));
var_dump(buscarLeitor(99));
```

```text
array(1) { ["nome"]=> string(7) "Marlene" }
NULL
```

A interrogação em `?array` significa "array ou `null`". É um contrato
honesto: quem chama sabe, olhando a assinatura, que precisa tratar a
ausência.

O que você **não** quer é uma função que devolve coisas de naturezas
diferentes conforme o dia:

:::compare left="Promessa quebrada" right="Promessa honesta" lang="php"
function buscar($id) {
    if (!$id) {
        return false;
    }
    if ($erro) {
        return "erro";
    }
    return $dados;
}
---
function buscar(int $id): ?array
{
    return $this_acervo[$id]
        ?? null;
}
:::

Do lado esquerdo, quem chama precisa testar três tipos diferentes e ainda
distinguir `false` de `"erro"` de array vazio. É o tipo de função que produz,
em cada ponto de uso, um `if` de cinco linhas — e o que acontece na prática é
que alguém escreve `if (!$resultado)` e volta ao defeito do relatório da
Vera.

Do lado direito há uma resposta só: o registro, ou nada.

## O relatório que zerou

:::story O relatório que zerou
Tainá escreveu a totalização do relatório mensal. Testou. Deu zero.

```php
$total_geral = 0;

function somar(int $valor): void
{
    $total_geral = $total_geral + $valor;
}

foreach ($multas as $m) {
    somar($m);
}

echo $total_geral;
```

— Não faz sentido — ela disse. — Eu somei oito mil reais e ele imprime zero.

Dedé olhou por dois segundos.

— Ele imprime zero porque a `$total_geral` de dentro da função não é a de
fora. São duas variáveis com o mesmo nome, e a de dentro morre quando a
função termina.

— Mas em Python isso daria erro.

— Em PHP dá um aviso e continua.

— Isso é pior.

— É muito pior.
:::

```text
PHP Warning: Undefined variable $total_geral in /app/rel.php
on line 5
```

Um aviso, não um erro fatal. O programa seguiu, somou zero com zero oito mil
vezes, e imprimiu um número perfeitamente plausível.

Em PHP, o escopo de função é **fechado**. Diferente de JavaScript e de
Python, uma função não enxerga as variáveis de fora — nem para ler:

```php title="escopo.php" numbered
<?php

$prazo = 14;

function diasDeEmprestimo(): int
{
    return $prazo;
}

echo diasDeEmprestimo(), "\n";
```

```text
PHP Warning: Undefined variable $prazo
PHP Fatal error: Uncaught TypeError: diasDeEmprestimo():
Return value must be of type int, null returned
```

Repare que o tipo de retorno salvou o dia. Sem o `: int`, a função devolveria
`null` em silêncio e o problema apareceria três telas adiante.

Existe uma palavra-chave que quebra a regra do escopo:

```php
function somar(int $valor): void
{
    global $total_geral;
    $total_geral = $total_geral + $valor;
}
```

Isso funciona, e é quase sempre a resposta errada.

:::warning
Uma função que lê ou escreve variável global não pode ser testada sozinha,
não pode ser chamada duas vezes com confiança, e não pode ser entendida sem
conhecer o programa inteiro.

Pior: ela cria uma dependência **invisível**. Nada na assinatura diz que
aquela função precisa de `$total_geral` — quem lê `somar(int $valor): void`
não tem como saber.

A regra que evita isso cabe numa frase: **tudo que a função precisa entra
por parâmetro; tudo que ela produz sai por retorno.**
:::

A versão correta não usa nada que você ainda não tenha visto:

```php title="correto.php" numbered
<?php

function somarMultas(array $multas): int
{
    $total = 0;

    foreach ($multas as $valor) {
        $total = $total + $valor;
    }

    return $total;
}

echo somarMultas([50, 240, 2000]), "\n";
```

```text
2290
```

## Uma função que dá para provar

A `multaEmCentavos()` do começo do capítulo tem uma propriedade que vale
nomear: dado o mesmo número de dias, ela devolve **sempre** o mesmo
resultado, e não mexe em nada fora dela. Isso se chama **função pura**.

A consequência prática é que dá para conferir a regra inteira sem banco, sem
servidor e sem abrir o navegador:

```php title="conferir_multa.php" numbered
<?php

function multaEmCentavos(int $dias): int
{
    if ($dias <= 0) {
        return 0;
    }

    return min($dias * 80, 2000);
}

$casos = [
    [-3, 0],
    [0, 0],
    [1, 80],
    [24, 1920],
    [25, 2000],
    [90, 2000],
];

foreach ($casos as [$dias, $esperado]) {
    $obtido = multaEmCentavos($dias);
    $marca = $obtido === $esperado ? 'ok    ' : 'FALHOU';

    echo $marca, ' ', $dias, ' dias -> ', $obtido, "\n";
}
```

```text
ok     -3 dias -> 0
ok     0 dias -> 0
ok     1 dias -> 80
ok     24 dias -> 1920
ok     25 dias -> 2000
ok     90 dias -> 2000
```

Seis casos, um arquivo, milissegundos. Isso é um teste — sem framework, sem
biblioteca, sem configuração. O `foreach ($casos as [$dias, $esperado])`
desempacota cada par direto nas duas variáveis, e a comparação com `===`
confere valor e tipo.

Repare nos casos escolhidos: `24` e `25` cercam o ponto em que o teto passa
a valer, e `-3` cobre a devolução adiantada. Testar a **borda**, e não só um
valor qualquer no meio, é o que faz esse arquivo valer alguma coisa.

Agora compare com o que seria conferir a mesma regra dentro daquela string
de HTML de quatrocentos e doze caracteres do recibo. Não é que fosse
difícil: é que não existe ponto de entrada. A função não é formalidade — é o
que torna a regra **alcançável**.

:::note Na sua carreira
"Extrair função" é a refatoração mais segura que existe e a mais
subestimada em entrevista técnica. Quando pedirem para você melhorar um
trecho de código, comece por aí, antes de propor arquitetura, padrão de
projeto ou microsserviço.

E há um efeito colateral valioso em código legado: você não precisa de
permissão para extrair uma função. Não muda comportamento, não muda banco,
não muda contrato com ninguém. É a única melhoria que dá para fazer numa
terça-feira comum, enquanto conserta outra coisa, sem abrir reunião.
:::

## Uma função também pode ser um valor

```php title="closure.php" numbered
<?php

$formatar = function (int $centavos): string {
    return 'R$ ' . number_format($centavos / 100, 2, ',', '.');
};

echo $formatar(2000), "\n";
```

```text
R$ 20,00
```

Uma função sem nome, guardada numa variável. Chama-se **closure**, e a
variável passa a ser chamável como se fosse o nome de uma função.

Closures seguem a mesma regra de escopo: não enxergam o que está fora. Para
capturar uma variável, você pede:

```php title="use.php" numbered
<?php

$multa_por_dia = 80;

$calcular = function (int $dias) use ($multa_por_dia): int {
    return $dias * $multa_por_dia;
};

echo $calcular(3), "\n";

$multa_por_dia = 150;
echo $calcular(3), "\n";
```

```text
240
240
```

Olhe as duas saídas. `use ($x)` captura **por valor**, no momento em que a
closure é criada — mudar a variável depois não muda nada lá dentro. Existe
`use (&$x)`, por referência, que é raro e quase sempre um sintoma.

As **arrow functions** encurtam o caso comum:

```php title="arrow.php" numbered
<?php

$multa_por_dia = 80;

$calcular = fn(int $dias): int => $dias * $multa_por_dia;

echo $calcular(3), "\n";
```

```text
240
```

Uma expressão só, sem chaves, sem `return`, sem `use` — a arrow function
captura automaticamente o que precisa, sempre por valor. É a forma que cabe
confortavelmente dentro de outra chamada, e é aí que ela ganha o dia.

## O laço que virou expressão

Lembra do acumulador do capítulo @cap:repeticoes? Quando o laço só
transforma uma coleção em outra, existe uma forma mais curta de dizer isso:

```php title="map_filter.php" numbered
<?php

$atrasados = [
    ['titulo' => 'O Cortiço', 'dias' => 9],
    ['titulo' => 'Vidas', 'dias' => 2],
    ['titulo' => 'Sertão', 'dias' => 41],
];

$criticos = array_filter(
    $atrasados,
    fn(array $e): bool => $e['dias'] > 30
);

$multas = array_map(
    fn(array $e): int => multaEmCentavos($e['dias']),
    $atrasados
);

print_r(array_column($criticos, 'titulo'));
print_r($multas);
```

```text
Array
(
    [0] => Sertão
)
Array
(
    [0] => 720
    [1] => 160
    [2] => 2000
)
```

`array_filter` recebe a coleção e uma função que responde sim ou não para
cada item; devolve os que passaram. `array_map` recebe uma função e a
coleção — nessa ordem, que é invertida em relação à outra, porque foi assim
que aconteceu em 1999 — e devolve o resultado de aplicar a função a cada
item.

:::pitfall
`array_filter` **preserva as chaves originais**. No exemplo, o item que
sobrou estava na posição 2 e continuaria na posição 2 — foi só a impressão
que veio depois de `array_column`, que renumera.

É exatamente o defeito que deixou o aplicativo da Casa Amarela com a tela
vazia no capítulo @cap:arrays. Antes de mandar um resultado de
`array_filter` para fora do PHP, `array_values`.
:::

A régua para escolher entre laço e expressão é simples: se o código
**transforma** uma coleção em outra, `array_map` e `array_filter` dizem isso
melhor. Se ele **faz coisas** — grava, envia, imprime, registra —, o
`foreach` é mais claro.

## Comportamento como argumento

O que torna `array_map` possível é que uma função pode receber outra função:

```php title="callable.php" numbered
<?php

function aplicarEm(array $itens, callable $operacao): array
{
    $saida = [];

    foreach ($itens as $item) {
        $saida[] = $operacao($item);
    }

    return $saida;
}

$centavos = [50, 240, 2000];

print_r(aplicarEm($centavos, fn(int $c): float => $c / 100));
```

```text
Array
(
    [0] => 0.5
    [1] => 2.4
    [2] => 20
)
```

O tipo `callable` diz "aqui entra algo que pode ser chamado". A função
`aplicarEm` não sabe o que será feito com os itens — só sabe que algo será.
Ela é, de propósito, uma cópia caseira do `array_map`, e escrevê-la uma vez
é o que faz o `array_map` deixar de parecer mágica.

:::summary
- Extraia uma função quando a resposta a "de quantos lugares preciso
	lembrar?" for maior que um.
- `return` devolve o valor e encerra a função na hora.
- Tipos em parâmetro e retorno recusam o erro na porta, com mensagem útil.
- Cláusula de guarda trata o caso ruim e sai, mantendo o caminho principal
	na margem.
- Nomeie o argumento sempre que ele for um `true` ou `false` solto.
- Prometa um tipo só; `?array` é honesto, três tipos diferentes não são.
- O escopo de função é fechado: o que entra, entra por parâmetro.
- `global` cria dependência invisível e impede conferir a função sozinha.
- Função pura pode ser provada num arquivo, sem framework nenhum.
- Closure captura por valor com `use`; arrow function captura sozinha.
- `array_map` e `array_filter` para transformar; `foreach` para fazer
	coisas.
:::

:::checkpoint
Você extrai uma regra para função com tipos declarados, escreve guardas em
vez de aninhar, explica por que `global` é sintoma, e monta um arquivo de
conferência que prova a regra nas bordas.
:::

:::exercise level=1
Escreva uma função que receba o número de dias de empréstimo e devolva a
data de devolução formatada, usando 14 dias como valor padrão. Chame-a de
três formas: sem argumento, com argumento posicional e com argumento
nomeado.

:::answer
```php
<?php

function prazoEmDias(int $dias = 14): string
{
    return "Devolver em {$dias} dias";
}

echo prazoEmDias(), "\n";
echo prazoEmDias(7), "\n";
echo prazoEmDias(dias: 21), "\n";
```

```text
Devolver em 14 dias
Devolver em 7 dias
Devolver em 21 dias
```

Com um parâmetro só, o argumento nomeado não ganha nada. Ele começa a valer
a partir do terceiro parâmetro, e vale muito quando algum deles é booleano.
:::

:::exercise level=2
A função abaixo está fazendo duas coisas. Separe-a em duas e explique o que
você ganhou.

```php
function processarDevolucao(array $emprestimo): string
{
    $dias = $emprestimo['dias_de_atraso'];
    $multa = 0;

    if ($dias > 0) {
        $multa = min($dias * 80, 2000);
    }

    return 'R$ ' . number_format($multa / 100, 2, ',', '.');
}
```

:::answer
```php
<?php

function multaEmCentavos(int $dias): int
{
    if ($dias <= 0) {
        return 0;
    }

    return min($dias * 80, 2000);
}

function emReais(int $centavos): string
{
    return 'R$ ' . number_format($centavos / 100, 2, ',', '.');
}

echo emReais(multaEmCentavos(9)), "\n";
```

```text
R$ 7,20
```

Três ganhos concretos.

**O cálculo virou conferível.** `multaEmCentavos(25)` devolve `2000`, um
número que dá para comparar. A versão original devolvia `"R$ 20,00"`, e
conferir uma regra de negócio comparando texto formatado é como medir
temperatura pela cor da parede.

**A formatação virou reutilizável.** `emReais()` serve para multa, para
doação, para qualquer valor. Na versão original, ela estava presa à multa.

**As duas mudam por motivos diferentes.** O valor da diária muda por decisão
da diretoria; o formato do texto muda se um dia a biblioteca emitir
comprovante em outro idioma. Quando duas coisas mudam por motivos
diferentes, elas não deveriam estar na mesma função.
:::

:::exercise level=3
O trecho abaixo é do Sistema e calcula o total de multas do mês. Ele tem
três defeitos: um que impede a função de ser conferida, um que a impede de
ser reutilizada, e um que faz o resultado ficar errado em centavos. Aponte
os três e reescreva.

```php
$total = 0;

function acumular($emprestimo)
{
    global $total;

    $dias = $emprestimo['dias'];

    if ($dias > 0) {
        $total += $dias * 0.80;
    }
}

foreach ($emprestimos as $e) {
    acumular($e);
}

echo "Total: R$ " . $total;
```

:::answer
**Defeito 1 — `global`.** A função depende de uma variável que não está na
assinatura dela. Não dá para chamá-la num arquivo de conferência sem
recriar o ambiente inteiro, e duas chamadas seguidas interferem uma na
outra.

**Defeito 2 — ela não devolve nada.** Uma função que só produz efeito
colateral não pode ser reaproveitada em nenhum outro contexto. Nem no
relatório, nem no comprovante, nem em lugar nenhum.

**Defeito 3 — `0.80` é `float`.** Somar oito mil valores em ponto flutuante
acumula erro, e o total do sistema vai divergir do total do caixa em
centavos, sem que ninguém saiba qual dos dois está certo. E falta o teto de
R$ 20,00, que a ata da diretoria também definiu.

```php
<?php

function multaEmCentavos(int $dias): int
{
    if ($dias <= 0) {
        return 0;
    }

    return min($dias * 80, 2000);
}

function totalDeMultasEmCentavos(array $emprestimos): int
{
    $total = 0;

    foreach ($emprestimos as $e) {
        $total = $total + multaEmCentavos($e['dias']);
    }

    return $total;
}

$emprestimos = [
    ['dias' => 9],
    ['dias' => -2],
    ['dias' => 90],
];

$total = totalDeMultasEmCentavos($emprestimos);

echo 'Total: R$ ', number_format($total / 100, 2, ',', '.'), "\n";
```

```text
Total: R$ 27,20
```

Repare no que a reescrita permite que a versão original não permitia:
`totalDeMultasEmCentavos([['dias' => 9]])` pode ser chamada num arquivo de
conferência, com três empréstimos inventados, e comparada com um número
esperado. Nada precisa estar no ar.

E repare também que a regra do teto ficou num lugar só. Quando a diretoria
mudar de ideia de novo — e vai mudar —, a busca vai devolver um resultado.
:::

:::story O oitavo
Na quarta, Dedé buscou de novo, agora por `0,50`, com vírgula.

Um resultado. Um arquivo chamado `avisos.php`, que rodava toda madrugada e
mandava e-mail de cobrança para quem estava atrasado.

— Esse aqui ninguém abre desde 2016 — disse ele.

Tainá olhou por cima do ombro.

— Como você sabe?

— Tem um `echo` de depuração comentado no meio, com a data do lado.

Márcia passou atrás dos dois e parou.

— Quanto tempo levou pra consertar?

— Os sete primeiros, quarenta minutos.

— E pra achar o oitavo?

— Três dias.

— Põe os três dias na planilha.
:::
