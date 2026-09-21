---
title: "Variáveis e tipos"
number: 4
slug: variaveis-e-tipos
part: p1
kicker: "Trinta e um pendentes na tela, vinte e sete no papel. Os quatro extras deviam exatamente zero real."
goal: >-
  Guardar valores nos cinco tipos do dia a dia, inspecioná-los com
  `var_dump`, escolher entre aspas simples e duplas, e distinguir ausência
  de vazio e de zero.
---

:::story Vinte e sete
Vera imprimiu o relatório de pendências e conferiu na mão, com uma régua,
como faz desde 1995.

O relatório dizia trinta e um. A régua dizia vinte e sete.

— Tem quatro sobrando aí.

— Talvez a senhora tenha pulado uma linha — arriscou a Tainá.

Vera conferiu de novo, com a régua, sem pressa nenhuma, enquanto a Tainá
olhava. Vinte e sete.

Levou uma hora para a Tainá achar o que os quatro nomes extras tinham em
comum: todos haviam devolvido **no prazo**. A multa deles tinha sido
calculada, registrada e gravada com o valor R$ 0,00.

O Sistema perguntava assim se a multa já tinha sido processada:

```php
if (!$multa) {
    $pendente = true;
}
```

E zero, em PHP, é falso.

— A conta está certa — disse Dedé, quando viu. — O relatório é que não sabe
a diferença entre "não deve nada" e "ninguém calculou".

Vera anotou no caderno dela. Depois riscou e escreveu de novo, com outra
letra, maior:

> *"o sistema precisa saber a diferença entre zero e nada"*

— Isso aí vale pra quantos sistemas? — perguntou a Tainá.

— Pra todos que eu já usei.
:::

Este capítulo é sobre guardar valores e saber o que foi guardado. A história
acima é sobre a segunda parte, que é a que costuma faltar.

## `$` na frente de tudo

Em PHP, toda variável começa com `$`, e nenhuma precisa ser declarada antes
de receber um valor:

```php title="primeiras.php" numbered
<?php

$titulo = "O Cortiço";
$exemplares = 3;

echo $titulo, "\n";
echo $exemplares, "\n";
```

```text
O Cortiço
3
```

Não existe uma linha dizendo "vou criar uma variável chamada `$titulo` do
tipo texto". A atribuição cria a variável e o tipo vem junto com o valor.

O `$` tem pouca cerimônia e um efeito colateral bom: `$titulo` é sempre uma
variável, em qualquer lugar do arquivo. Não existe ambiguidade entre nome de
variável, nome de função e palavra reservada da linguagem. Em compensação,
esquecer o `$` é um erro que o PHP demora a perceber, porque `titulo` sem
cifrão é sintaxe válida — é o nome de uma constante que ele vai procurar e
não achar.

Sobre nomes: valem letras, números e sublinhado, e o primeiro caractere não
pode ser número. Maiúsculas e minúsculas são diferentes — `$titulo` e
`$Titulo` são duas variáveis. A convenção em PHP moderno é
`$nomeComposto`, em *camelCase*, ainda que muito código antigo use
`$nome_composto`.

## Os cinco tipos do dia a dia

```php title="tipos.php" numbered
<?php

$titulo = "O Cortiço";
$exemplares = 3;
$peso_kg = 0.42;
$disponivel = true;
$devolvido_em = null;

var_dump($titulo);
var_dump($exemplares);
var_dump($peso_kg);
var_dump($disponivel);
var_dump($devolvido_em);
```

```text
string(10) "O Cortiço"
int(3)
float(0.42)
bool(true)
NULL
```

Cinco valores, cinco tipos. O `var_dump` imprime o tipo e o valor, e é por
isso que ele é a ferramenta mais usada em depuração de PHP: com `echo`, os
cinco sairiam como `O Cortiço`, `3`, `0.42`, `1` e nada.

| Tipo | O que guarda | No acervo |
|---|---|---|
| `string` | texto | título, autor, ISBN, nome do leitor |
| `int` | número inteiro | tombo, dias de atraso, quantidade |
| `float` | número com casas decimais | peso, percentual, média |
| `bool` | `true` ou `false` | se o exemplar está disponível |
| `null` | a ausência de valor | data de devolução de quem não devolveu |

Tabela: `true`, `false` e `null` podem ser escritos em maiúsculas, mas a
convenção é minúscula.

Repare no `string(10)` da saída, para uma palavra de nove letras. O número
entre parênteses não é a contagem de letras: é a contagem de **bytes**, e o
`ç` ocupa dois. Isso é consequência de como o texto é armazenado, e por ora
basta saber que o número existe e que ele nem sempre bate com o que você
conta no olho.

Existem outros dois tipos importantes — `array` e `object` —, que guardam
várias coisas de uma vez em vez de uma só. Eles entram quando houver várias
coisas para guardar.

:::key
Sempre que você não tiver certeza do que tem dentro de uma variável, a
resposta custa uma linha: `var_dump($x);`. É mais rápido que raciocinar,
mais confiável que lembrar, e a única forma de distinguir o número `3` do
texto `"3"` — que se parecem na tela e se comportam de formas diferentes.
:::

## Aspas simples e aspas duplas guardam coisas diferentes

As duas criam texto, e param de ser equivalentes assim que você coloca uma
variável dentro:

```php title="aspas.php" numbered
<?php

$titulo = "O Cortiço";

echo "Temos: $titulo\n";
echo 'Temos: $titulo\n';
```

```text
Temos: O Cortiço
Temos: $titulo\n
```

A primeira linha usa **aspas duplas**. Dentro delas, o PHP procura nomes de
variável e troca cada um pelo valor. Isso se chama **interpolação**. A barra
invertida também é interpretada: `\n` virou quebra de linha de verdade.

A segunda linha usa **aspas simples**. Dentro delas, quase nada é
interpretado: `$titulo` saiu como cinco caracteres literais, e `\n` saiu
como dois. Por isso a saída ficou tudo em uma linha só.

Quando o nome da variável encosta em outra letra, o PHP não consegue
adivinhar onde ele termina:

```php title="chaves.php" numbered
<?php

$tipo = "exemplar";

echo "Três {$tipo}es\n";
```

```text
Três exemplares
```

Sem as chaves, o PHP procuraria uma variável chamada `$tipoes`, não a
encontraria e avisaria. Com `{}`, a fronteira fica explícita. Usar chaves
sempre que houver interpolação poupa essa decisão.

:::key
Regra prática: **aspas simples quando o texto é literal, aspas duplas
quando há variável dentro.** Não é questão de desempenho — a diferença é
imperceptível. É questão de dizer a intenção: aspas simples avisam a quem lê
que ali não tem nada para ser substituído.
:::

## `null` não é vazio, e vazio não é zero

```php title="tres_afirmacoes.php" numbered
<?php

$devolvido_em = null;   // ainda não devolveu
$observacao = "";       // devolveu, e não havia nada a observar
$multa = 0;             // devolveu, e não deve nada
```

Três valores, três afirmações completamente diferentes sobre o mundo. E,
para um `if` simples, os três se comportam do mesmo jeito: nenhum deles
entra.

```php title="o_defeito.php" numbered
<?php

$multa = 0;

if ($multa) {
    echo "tem multa\n";
} else {
    echo "nao tem multa\n";
}
```

```text
nao tem multa
```

O `if` não recebeu `true` nem `false`: recebeu o número zero. Quando isso
acontece, o PHP converte o valor para verdadeiro ou falso antes de decidir —
e zero é falso.

É exatamente o defeito do relatório da Vera, escrito de trás para frente. O
Sistema perguntava `if (!$multa)`, que é "se a multa for falsa", achando que
estava perguntando "se a multa não existir".

Há três ferramentas para fazer a pergunta certa, e elas não são
intercambiáveis:

```php title="tres_perguntas.php" numbered
<?php

$multa = 0;

var_dump(isset($multa));    // a variável existe e não é null?
var_dump(empty($multa));    // o valor é um dos "falsos"?
var_dump(is_null($multa));  // o valor é exatamente null?
```

```text
bool(true)
bool(true)
bool(false)
```

Leia devagar, porque as três respostas são diferentes para o mesmo valor.

`isset` respondeu `true`: a variável existe e não é nula. `empty` respondeu
`true`: zero é um valor falso. `is_null` respondeu `false`: zero não é nulo,
zero é zero.

Trocando o valor por `null`, as três respostas se invertem:

```text
bool(false)   isset  — não existe, ou existe e é null
bool(true)    empty  — null é falso
bool(true)    is_null
```

:::key
`isset()` pergunta "existe e não é nulo?". `empty()` pergunta "é um valor
falso?". E **nenhuma das duas** pergunta "tem conteúdo?".

Quando o que você precisa é distinguir ausência de zero — que é o caso da
multa da Vera —, a pergunta é `=== null`, e nenhuma outra serve.
:::

A correção do relatório são duas perguntas separadas, cada uma dizendo o que
quer saber:

```php title="explicito.php" numbered
<?php

$multa = 0;

if ($multa === null) {
    echo "ninguem calculou ainda\n";
}

if ($multa === 0) {
    echo "calculado, e nao deve nada\n";
}
```

```text
calculado, e nao deve nada
```

Os três sinais de igual comparam valor **e** tipo, sem converter nada. Dois
sinais fariam uma coisa diferente, e essa diferença rende uma história boa o
bastante para ocupar o próximo capítulo inteiro.

:::practice
Rode o `tres_perguntas.php` acima trocando o valor de `$multa` por: `null`,
`0`, `""`, `"0"`, `false` e `"a"`. Anote as três respostas de cada um.

Seis linhas de anotação que respondem, de uma vez, umas quinze dúvidas que
vão aparecer nas próximas semanas — e é mais rápido de consultar do que a
documentação.
:::

## Valores que não podem mudar

```php title="constantes.php" numbered
<?php

const DIAS_DE_EMPRESTIMO = 14;
const LIMITE_POR_LEITOR = 3;

echo "Prazo: ", DIAS_DE_EMPRESTIMO, " dias\n";
```

```text
Prazo: 14 dias
```

Uma **constante** é um valor com nome que não pode ser reatribuído. Repare
em duas diferenças: não tem `$` na frente, e o nome vem em maiúsculas com
sublinhado — convenção universal em PHP, não obrigação da linguagem.

Tentar mudar uma dá erro:

```text
PHP Fatal error: Cannot redefine constant DIAS_DE_EMPRESTIMO
```

Existe também `define('DIAS_DE_EMPRESTIMO', 14)`, que faz quase o mesmo. A
diferença prática: `const` é resolvida quando o arquivo é lido e só aceita
valor fixo; `define()` roda durante a execução e aceita um nome ou um valor
calculado na hora. Use `const` por padrão.

O valor de trocar `14` por `DIAS_DE_EMPRESTIMO` não é evitar digitação. É
que o número passa a existir **num lugar só**. Quando a Vera resolver mudar
o prazo para vinte e um dias durante as férias escolares, a alteração é uma
linha — e você não vai passar a tarde procurando todos os `14` do sistema,
descobrindo que alguns eram dias de empréstimo e outros eram o número de
prateleiras.

:::note Na sua carreira
Quando alguém do negócio diz que o número do sistema está errado, a chance
de essa pessoa estar certa é alta — e a chance de o sistema estar
tecnicamente funcionando é alta também. As duas coisas ao mesmo tempo.

A Vera não sabe programar e encontrou um defeito que passou quinze anos em
produção, porque tinha duas coisas que nenhum teste automatizado tem: o
número certo, contado na mão, e a teimosia de conferir.

O reflexo certo ao receber esse tipo de relato não é explicar por que o
sistema está certo. É pedir **os dois números e a lista**. A diferença entre
31 e 27 é uma abstração; os quatro nomes extras são um caminho direto até a
linha de código.
:::

:::summary
- Toda variável começa com `$` e não precisa ser declarada: a atribuição
	cria a variável e define o tipo.
- Os cinco tipos do dia a dia são `string`, `int`, `float`, `bool` e `null`.
- `var_dump` mostra tipo e valor; `echo` mostra só o valor.
- Aspas duplas interpolam variáveis e interpretam `\n`; aspas simples não.
- `null` é ausência, `""` é vazio, `0` é zero — três afirmações diferentes
	que um `if` simples trata como uma só.
- `isset` pergunta "existe?", `empty` pergunta "é falso?"; para distinguir
	ausência de zero, use `=== null`.
- `const` dá nome a um valor fixo e o coloca num lugar só.
:::

:::checkpoint
Você declara variáveis dos cinco tipos, descobre o tipo de qualquer uma com
`var_dump`, escolhe as aspas pela intenção e explica em uma frase a
diferença entre `null`, `""` e `0`.
:::

:::exercise level=1
Crie variáveis para descrever um exemplar — tombo, título, se está
disponível, e a data de devolução — e imprima o tipo de cada uma.

:::answer
```php
<?php

$tombo = 2117;
$titulo = "O Cortiço";
$disponivel = false;
$devolvido_em = null;

var_dump($tombo, $titulo, $disponivel, $devolvido_em);
```

```text
int(2117)
string(10) "O Cortiço"
bool(false)
NULL
```

O `var_dump` aceita vários valores de uma vez, separados por vírgula.

E repare na escolha de `$devolvido_em`: `null` é uma afirmação — o
empréstimo está aberto. Se fosse `""`, estaria dizendo "devolveu em data
desconhecida", que é outra coisa, e quase sempre um erro de importação de
dados antigos.
:::

:::exercise level=2
Sem rodar, escreva o que cada linha imprime. Depois rode e confira.

```php
<?php

$n = 5;
$texto = "livros";

echo "Temos $n $texto\n";
echo 'Temos $n $texto\n';
echo "Temos {$n}00 $texto\n";
```

:::answer
```text
Temos 5 livros
Temos $n $texto\nTemos 500 livros
```

A segunda linha é a que pega quase todo mundo, e por dois motivos ao mesmo
tempo: as variáveis saíram literais **e** o `\n` também, então a terceira
linha começou grudada na segunda.

A terceira mostra por que as chaves existem. Sem elas, `"$n00"` faria o PHP
procurar uma variável chamada `$n00`.
:::

:::exercise level=3
O trecho abaixo veio do Sistema. Ele decide se um empréstimo entra na lista
de pendências. Aponte o defeito e escreva a versão correta.

```php
$multa = calcularMulta($emprestimo);

if (!$multa) {
    $pendente = true;
} else {
    $pendente = false;
}
```

:::answer
O defeito é o `!$multa`, que pergunta "a multa é um valor falso?" quando a
intenção era perguntar "a multa ainda não foi calculada?".

Quatro valores diferentes passam por aquele `if` como se fossem o mesmo:
`null` (não calculou), `0` (calculou e não deve nada), `""` (veio texto
vazio de algum lugar) e `false` (a função falhou). Só o primeiro deveria
marcar pendência.

```php
$multa = calcularMulta($emprestimo);

$pendente = ($multa === null);
```

Duas observações sobre a versão corrigida.

A primeira: o `if/else` sumiu. Quando os dois ramos só atribuem `true` e
`false` à mesma variável, a comparação já é a resposta — e uma comparação
lida em voz alta soa como a regra de negócio: *pendente é quando a multa é
nula*.

A segunda, e é a mais importante: se `calcularMulta` puder devolver `false`
em caso de falha, a versão corrigida marca esse empréstimo como **não
pendente**, e o problema fica invisível. Uma função que devolve ora um
número, ora `null`, ora `false` obriga quem chama a adivinhar qual dos três
aconteceu. O conserto de verdade é a função devolver uma coisa só — e é por
isso que ela vai voltar a este livro.
:::

:::story Por que um contrato teria valor zero?
Na Vertexo, na mesma semana, o Cléber pediu um indicador novo no painel da
diretoria: "total de contratos pendentes".

Dedé perguntou o que contava como pendente.

— Os que estão pendentes.

— Contrato com valor zero conta?

Cléber olhou para ele com a expressão de quem foi perguntado se a água é
molhada.

— Por que um contrato teria valor zero?

Três semanas depois, a área comercial começou a cadastrar contratos de
cortesia, com valor zero, para clientes em período de teste.

O painel da diretoria passou a mostrar dezessete contratos pendentes.
Existiam trinta e quatro.

Dedé já tinha escrito `=== null`.
:::
