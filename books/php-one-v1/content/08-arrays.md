---
title: "Arrays"
number: 8
slug: arrays
part: p1
kicker: "A estrutura mais usada do PHP é também a mais mal usada — e uma linha dela já derrubou o aplicativo de mil e duzentas pessoas."
goal: >-
  Guardar várias coisas numa variável só, escolher entre lista e mapa,
  entender por que as duas são o mesmo tipo em PHP, e saber quando essa
  igualdade vira defeito.
---

Até aqui, cada variável guardou uma coisa: um título, um número de dias, um
valor em centavos. O acervo da Casa Amarela tem oito mil exemplares, e
`$exemplar1`, `$exemplar2`, `$exemplar3` para de ser engraçado no quarto.

## Várias coisas numa variável só

```php title="lista.php" numbered
<?php

$tombos = [812, 907, 344];

echo $tombos[0], "\n";
echo $tombos[2], "\n";
echo count($tombos), "\n";
```

```text
812
344
3
```

Os colchetes criam um **array**. Os valores ficam separados por vírgula, e
cada um ganha uma posição, contada a partir de **zero** — por isso
`$tombos[0]` é o primeiro e `$tombos[2]` é o terceiro.

`count()` responde quantos itens existem. Repare que `count($tombos)` é `3`
e a última posição é `2`: essa diferença de um é a origem de uma quantidade
impressionante de defeitos, e a forma de nunca mais errar é lembrar que a
contagem começa em zero e a contagem de itens não.

Para acrescentar no fim, colchetes vazios:

```php title="acrescentar.php" numbered
<?php

$tombos = [812, 907];

$tombos[] = 344;
$tombos[] = 501;

print_r($tombos);
```

```text
Array
(
    [0] => 812
    [1] => 907
    [2] => 344
    [3] => 501
)
```

`$tombos[] = 344` quer dizer "coloque na próxima posição livre". Você não
precisa saber qual é.

E apareceu uma ferramenta nova: `print_r` imprime a estrutura de um array de
forma legível. O `var_dump` também funciona e mostra os tipos, o que é mais
informação do que costuma ser útil quando se quer só conferir o conteúdo.

## Chaves com nome

A posição numérica serve quando a ordem é o que importa. Quando o que
importa é **o que cada valor significa**, a chave vira texto:

```php title="mapa.php" numbered
<?php

$exemplar = [
    'tombo' => 812,
    'titulo' => 'O Cortiço',
    'status' => 'disponivel',
];

echo $exemplar['titulo'], "\n";

$exemplar['status'] = 'emprestado';

echo $exemplar['status'], "\n";
```

```text
O Cortiço
emprestado
```

A seta `=>` liga a chave ao valor. O acesso e a alteração usam a mesma
sintaxe de colchetes, com o nome da chave no lugar do número.

Isso resolve o problema que a Vera tinha com o formulário de dezoito campos:
em vez de dezoito variáveis soltas, um exemplar inteiro cabe numa variável
que se lê em voz alta.

:::key
Use **chave numérica** quando os itens forem intercambiáveis e a ordem
importar — uma fila, uma lista de resultados, um histórico.

Use **chave de texto** quando cada posição tiver um significado próprio — um
registro, uma configuração, um conjunto de opções.

A pergunta que decide: faz sentido perguntar "qual é o terceiro"? Se fizer,
é lista. Se não fizer, é mapa.
:::

## As duas são a mesma coisa

Em quase toda linguagem existem duas estruturas separadas. Python tem `list`
e `dict`. JavaScript tem `Array` e `Object`. Java tem `List` e `Map`.

PHP tem `array`. Um só, para os dois usos.

```php title="dois_usos.php" numbered
<?php

$tombos = [812, 907, 344];

var_dump($tombos);
```

```text
array(3) {
  [0]=> int(812)
  [1]=> int(907)
  [2]=> int(344)
}
```

Repare nas chaves `0`, `1`, `2`. Elas estão lá — você é que não as escreveu.
Uma "lista" em PHP é um mapa cujas chaves por acaso são os inteiros
começando em zero, em ordem, sem buraco.

:::term Array em PHP
Um **mapa ordenado**: pares chave→valor que mantêm a ordem de inserção. A
chave é `int` ou `string`. Não existe um tipo de lista separado — o que
chamamos de lista é uma convenção sobre as chaves.
:::

:::history
A decisão é de 1997, quando o PHP 3 estava sendo escrito por Andi Gutmans e
Zeev Suraski. Uma estrutura só simplificava o interpretador e a vida de quem
escrevia, numa época em que a maior parte do PHP do mundo processava
formulários — onde tudo chega como pares nome→valor.

Funcionou por vinte anos. O que ninguém previu foi que essa mesma estrutura
seria enviada para outros programas num formato que **distingue** os dois
casos.
:::

Desde o PHP 8.1 existe uma função que responde qual dos dois você tem na
mão:

```text
$ php -r 'var_dump(array_is_list([812, 907]));'
bool(true)
$ php -r 'var_dump(array_is_list([0 => 812, 2 => 907]));'
bool(false)
```

O segundo tem chaves `0` e `2`. Falta o `1`. Para o PHP, continua sendo um
array como qualquer outro — e é aí que começa a história.

## A gente não mudou nada

:::story A gente não mudou nada
Segunda-feira, 8h50. Tainá abriu o chat da Casa Amarela e havia catorze
mensagens da Vera, todas antes das oito da manhã.

O aplicativo do leitor não mostrava mais o acervo. Tela vazia, sem erro, sem
mensagem, sem nada.

— A gente não mudou nada no fim de semana — disse Dedé.

Tecnicamente verdade. Na sexta ele tinha tirado da lista os exemplares em
restauro. Uma linha. O servidor continuava respondendo normalmente, os dados
continuavam chegando, os campos continuavam com os nomes certos.

Só que na sexta o que saía era isto:

```text
[{"tombo":812},{"tombo":907}]
```

E na segunda era isto:

```text
{"0":{"tombo":812},"2":{"tombo":344}}
```

O aplicativo esperava uma lista. Recebeu outra coisa. Não quebrou — só não
achou nada para percorrer, e desenhou a tela vazia com muita competência.

Márcia soube às 9h15. A primeira pergunta dela não foi sobre o defeito.

— Tem quanto tempo que está assim?

— Desde sexta, 18h.

— Então foram dois dias e meio. Coloca na ata.
:::

:::term JSON
O formato em que dois programas trocam dados pela rede. É texto, e tem
duas estruturas: **lista**, entre `[ ]`, e **objeto**, entre `{ }` com pares
nome→valor. As duas coisas que o PHP resolveu chamar de array são, em JSON,
tipos diferentes — e quem recebe trata cada um de um jeito.
:::

O PHP converte um array para JSON com `json_encode`, e a decisão de virar
lista ou objeto é tomada sozinha, por um critério rígido:

```php title="a_regra.php" numbered
<?php

echo json_encode([812, 907, 344]), "\n";
echo json_encode([0 => 812, 1 => 907]), "\n";
echo json_encode([0 => 812, 2 => 344]), "\n";
echo json_encode(['tombo' => 812]), "\n";
```

```text
[812,907,344]
[812,907]
{"0":812,"2":344}
{"tombo":812}
```

Vira lista JSON **apenas** se as chaves forem exatamente `0, 1, 2, …, n-1`,
nessa ordem, sem buraco. Qualquer outra coisa vira objeto — é a mesma
pergunta que o `array_is_list` responde.

## O buraco que o `unset` deixa

O que o Dedé escreveu na sexta foi isto:

```php title="o_filtro_da_sexta.php" numbered
<?php

$exemplares = [
    ['tombo' => 812, 'status' => 'disponivel'],
    ['tombo' => 907, 'status' => 'restauro'],
    ['tombo' => 344, 'status' => 'disponivel'],
];

unset($exemplares[1]);

echo json_encode($exemplares), "\n";
```

```text
{"0":{"tombo":812,"status":"disponivel"},
 "2":{"tombo":344,"status":"disponivel"}}
```

`unset()` remove um item do array. O que ele **não** faz é renumerar os que
ficaram: a posição `1` simplesmente deixou de existir, e o item que estava
na `2` continua na `2`.

O array agora tem chaves `0` e `2`. O `json_encode` olhou, não encontrou a
sequência e produziu um objeto.

Nenhum dos dois lados errou. O PHP fez exatamente o que documenta fazer há
vinte anos; o aplicativo tratou um objeto como objeto. O defeito aconteceu
**na fronteira** — e fronteira é onde moram os problemas que ninguém
consegue reproduzir, porque cada lado, testado sozinho, está certo.

O conserto tem uma palavra:

```php title="o_conserto.php" numbered
<?php

$exemplares = [
    ['tombo' => 812, 'status' => 'disponivel'],
    ['tombo' => 907, 'status' => 'restauro'],
    ['tombo' => 344, 'status' => 'disponivel'],
];

unset($exemplares[1]);

$exemplares = array_values($exemplares);

echo json_encode($exemplares), "\n";
```

```text
[{"tombo":812,"status":"disponivel"},
 {"tombo":344,"status":"disponivel"}]
```

`array_values()` joga as chaves fora e renumera a partir de zero. O array
volta a ser uma lista, e o JSON volta a ser uma lista.

:::key
**Toda vez que um array for sair do PHP como lista — para JSON, para outro
programa, para uma tela que espera ordem —, garanta as chaves com
`array_values()`.**

A regra parece exagerada até você lembrar que a linha que quebra o contrato
raramente é a que você está escrevendo agora. É a que outra pessoa vai
acrescentar no meio do caminho, em março, com toda a razão do mundo.
:::

:::note Na sua carreira
"A gente não mudou nada" é quase sempre falso e quase nunca mentira. A
pessoa mudou algo que, segundo o modelo mental dela, não podia causar
aquilo.

A habilidade que se desenvolve com o tempo não é lembrar de todos os efeitos
colaterais possíveis — é **estreitar a busca rápido**. Neste caso: o
aplicativo mudou? Não. O servidor mudou? Sim, na sexta. O que mudou na
sexta? Uma linha. O que essa linha toca? A forma da resposta.

Quatro perguntas, dois minutos. É a diferença entre uma investigação de meia
hora e uma manhã inteira, e é treinável.
:::

## Perguntar se está lá

Três funções parecidas que respondem perguntas diferentes:

```php title="existe.php" numbered
<?php

$exemplar = [
    'tombo' => 812,
    'observacao' => null,
];

var_dump(isset($exemplar['tombo']));
var_dump(isset($exemplar['observacao']));
var_dump(array_key_exists('observacao', $exemplar));
var_dump(in_array(812, $exemplar));
```

```text
bool(true)
bool(false)
bool(true)
bool(true)
```

A segunda e a terceira linhas são o ponto. A chave `observacao` **existe** no
array — ela só tem valor `null`. O `isset` responde `false`, porque a
pergunta dele é "existe e não é nulo?". O `array_key_exists` responde
`true`, porque a pergunta dele é só "existe?".

É a mesma distinção entre ausência e nulo do capítulo
@cap:variaveis-e-tipos, agora com uma consequência prática: se o seu código
decide se deve gravar uma observação com base em `isset`, ele nunca vai
gravar uma observação em branco de propósito.

O `in_array` procura pelo **valor**, não pela chave. Existe também
`array_search`, que devolve a chave em que encontrou.

:::pitfall
`in_array` sem o terceiro argumento compara com `==`:

```text
$ php -r 'var_dump(in_array(0, ["a", "b"]));'
bool(false)
$ php -r 'var_dump(in_array("1", [1, 2]));'
bool(true)
```

O segundo caso é o que morde: o texto `"1"` foi encontrado numa lista de
números. Use sempre `in_array($x, $lista, true)`, com o terceiro argumento,
que mudam para comparação estrita.
:::

## Copiar um array copia mesmo

```php title="copia.php" numbered
<?php

$a = ['tombo' => 812];
$b = $a;

$b['tombo'] = 907;

echo $a['tombo'], "\n";
echo $b['tombo'], "\n";
```

```text
812
907
```

Atribuir um array a outra variável **copia** o conteúdo. Mexer na cópia não
mexe no original.

Isso parece óbvio e não é: em Python e em JavaScript, a mesma sequência
deixaria as duas variáveis apontando para a mesma lista, e o `812` teria
virado `907` nas duas. Quem chega de uma dessas linguagens costuma descobrir
a diferença de um jeito ruim.

O PHP é econômico por dentro — ele só duplica de verdade quando um dos dois
lados muda —, então o custo é menor do que parece. Mas ele existe, e para um
array de cem mil itens ele aparece.

## Arrays dentro de arrays

O valor guardado num array pode ser outro array, e é assim que se representa
uma coleção de registros:

```php title="acervo.php" numbered
<?php

$acervo = [
    ['tombo' => 812, 'titulo' => 'O Cortiço'],
    ['tombo' => 907, 'titulo' => 'Vidas Secas'],
];

echo $acervo[0]['titulo'], "\n";
echo count($acervo), "\n";
```

```text
O Cortiço
2
```

Dois colchetes seguidos: o primeiro escolhe o registro, o segundo escolhe o
campo. É a estrutura em que a maioria dos dados chega e sai de um sistema
PHP.

Ela funciona bem em dois níveis, tolera três, e depois disso vira outra
coisa. Esta linha existe no Sistema:

```php
$dados['livro'][3]['exemplares'][0]['emprestimo']['leitor']['nome']
```

Ela funciona. E tem quatro problemas que nenhuma ferramenta consegue
apontar: o editor não sugere nada, um erro de digitação em qualquer nível
devolve `null` com um aviso, não há como saber quais chaves existem sem
rodar o programa, e a estrutura inteira é um contrato que não está escrito
em lugar nenhum.

:::key
Quando o array tem três ou mais níveis e o formato é **conhecido e fixo**,
ele está pedindo para virar outra coisa. Guarde o sintoma; o remédio aparece
quando a linguagem tiver como aplicá-lo.
:::

## Desempacotar e juntar

```php title="desempacotar.php" numbered
<?php

$par = [812, 907];

[$primeiro, $segundo] = $par;

echo $primeiro, " e ", $segundo, "\n";

$exemplar = ['tombo' => 344, 'status' => 'disponivel'];

['tombo' => $t, 'status' => $s] = $exemplar;

echo $t, " esta ", $s, "\n";
```

```text
812 e 907
344 esta disponivel
```

O desempacotamento por chave, na segunda forma, é o mais útil do conjunto:
extrai só os campos que interessam e documenta, na própria linha, o que o
trecho seguinte usa.

E para juntar dois arrays existem três pontinhos:

```php title="juntar.php" numbered
<?php

$disponiveis = [812, 907];
$reservados = [344];

$todos = [...$disponiveis, ...$reservados];

print_r($todos);
```

```text
Array
(
    [0] => 812
    [1] => 907
    [2] => 344
)
```

O `...` é chamado de **spread**. Repare que as chaves foram renumeradas
automaticamente — para listas, ele já entrega o resultado no formato certo.
Com chaves de texto, ele também funciona desde o PHP 8.1, com a regra de que
o último repetido vence.

:::summary
- `[]` cria um array; `$a[] = $x` acrescenta na próxima posição livre.
- A contagem de posições começa em zero; `count()` devolve a quantidade.
- Chave numérica para lista, chave de texto para registro.
- Array em PHP é um mapa ordenado — lista é só uma convenção sobre as
	chaves.
- Vira lista em JSON só com chaves `0..n-1` sem buraco; `unset` abre buraco
	e `array_values` fecha.
- `isset` diz "existe e não é nulo"; `array_key_exists` diz só "existe".
- `in_array` compara com `==` a menos que você passe `true` no terceiro
	argumento.
- Array é copiado por valor, diferente de Python e JavaScript.
- Três níveis de profundidade é sintoma de que falta outra estrutura.
:::

:::checkpoint
Você cria listas e mapas, acrescenta e remove itens, sabe dizer se um array
vai virar lista ou objeto em JSON, e consegue explicar por que `isset` e
`array_key_exists` discordam.
:::

:::exercise level=1
Monte um array com três exemplares, cada um com tombo, título e status.
Imprima o título do segundo, a quantidade total, e depois acrescente um
quarto exemplar e imprima a quantidade de novo.

:::answer
```php
<?php

$acervo = [
    ['tombo' => 812, 'titulo' => 'O Cortiço', 'status' => 'livre'],
    ['tombo' => 907, 'titulo' => 'Vidas', 'status' => 'restauro'],
    ['tombo' => 344, 'titulo' => 'Sertão', 'status' => 'livre'],
];

echo $acervo[1]['titulo'], "\n";
echo count($acervo), "\n";

$acervo[] = [
    'tombo' => 501,
    'titulo' => 'Iracema',
    'status' => 'disponivel',
];

echo count($acervo), "\n";
```

```text
Vidas
3
4
```

O `[1]` é o segundo porque a contagem começa em zero. Essa é a única parte
do exercício que vale conferir com atenção.
:::

:::exercise level=2
Dado o array abaixo, remova o exemplar em restauro e imprima o resultado em
JSON. Faça duas versões: uma que produz um objeto e uma que produz uma
lista. Explique o que muda para quem recebe.

```php
$exemplares = [
    ['tombo' => 812, 'status' => 'disponivel'],
    ['tombo' => 907, 'status' => 'restauro'],
    ['tombo' => 344, 'status' => 'disponivel'],
];
```

:::answer
```php
unset($exemplares[1]);

echo json_encode($exemplares), "\n";
echo json_encode(array_values($exemplares)), "\n";
```

```text
{"0":{"tombo":812,"status":"disponivel"},
 "2":{"tombo":344,"status":"disponivel"}}
[{"tombo":812,"status":"disponivel"},
 {"tombo":344,"status":"disponivel"}]
```

Para quem recebe, a diferença é total. Um programa que espera uma lista vai
percorrer o primeiro resultado e encontrar zero itens, porque um objeto não
se percorre pelo índice. Não dá erro: dá tela vazia.

E repare que os dados são idênticos nos dois casos. Os mesmos dois
exemplares, os mesmos campos, os mesmos valores. O que mudou foi só a forma
— e a forma é metade do contrato.
:::

:::exercise level=3
O trecho abaixo veio do Sistema e decide se deve gravar a observação de uma
devolução. Ele tem um defeito que só aparece em um caso específico. Encontre
o caso, explique e corrija.

```php
$devolucao = [
    'tombo' => 812,
    'observacao' => null,
];

if (isset($devolucao['observacao'])) {
    gravarObservacao($devolucao['observacao']);
}
```

:::answer
O caso específico é a observação que existe e está **deliberadamente**
vazia.

O `isset` responde `false` para duas situações diferentes: a chave não
existir, e a chave existir com valor `null`. Aqui ela existe. Alguém, em
algum lugar, montou esse array com o campo presente — o que normalmente
significa que o formulário tinha o campo e a pessoa não preencheu.

Se a regra de negócio for "grave a observação quando o campo veio no
formulário, mesmo em branco", o `isset` está errado. Se for "grave só quando
houver texto", ele está certo por acaso, e vai deixar de estar no dia em que
alguém mudar o valor padrão de `null` para `''`.

A correção é escolher a pergunta e escrevê-la:

```php
if (array_key_exists('observacao', $devolucao)) {
    gravarObservacao($devolucao['observacao']);
}
```

se a regra for sobre o campo ter vindo, ou

```php
if (($devolucao['observacao'] ?? '') !== '') {
    gravarObservacao($devolucao['observacao']);
}
```

se a regra for sobre haver texto. O `??` cobre o caso de a chave nem existir,
e a comparação com `''` torna a intenção legível para quem revisar.

O que não dá para fazer é deixar `isset` e torcer para que as duas regras
nunca divirjam. Elas divergem — foi assim que quatro leitores apareceram no
relatório da Vera no capítulo @cap:variaveis-e-tipos, pelo mesmo motivo, com
outro nome.
:::
