---
title: "Operadores"
number: 6
slug: operadores
part: p1
kicker: "O totem informou à Dona Marlene que ela tinha menos três dias de atraso e uma multa de R$ 2,40 negativos."
goal: >-
  Calcular, concatenar e combinar valores sem surpresa — e conhecer os quatro
  pontos em que a ordem de avaliação do PHP não é a que você leu.
---

:::story Menos três dias
O totem da entrada era o único pedaço novo do Sistema. Tinha sido instalado
em 2019, com um teclado de números e uma tela pequena, e servia para o
leitor digitar a carteirinha e ver a própria situação.

Dona Marlene digitou a dela numa terça de manhã e chamou a Vera.

— Ó aqui, minha filha.

```text
LEITOR: 1183 - MARLENE S. COUTINHO
ATRASO: -3 dias
MULTA:  R$ -2,40
```

— A senhora devolveu antes do prazo.

— Eu sei. Mas está escrito que a biblioteca me deve dois e quarenta.

— Não deve.

— Está escrito.

Vera olhou para a tela por um tempo. Depois olhou para a Dona Marlene, que
tinha setenta e nove anos e uma paciência infinita para esse tipo de
conversa.

— A senhora quer em livro ou em dinheiro?

— Em livro está bom.
:::

A conta do totem estava certa. Faltava uma pergunta antes dela.

:::art caption="Menos três dias de atraso, e a biblioteca devendo dois e quarenta."
src="menos-tres-dias-de-atraso-e-a-biblioteca-devendo-dois-e-quarenta.png"
Charge editorial minimalista em fundo branco: um totem de autoatendimento
antigo, com teclado numérico e uma tela pequena onde se lê apenas
"MULTA: R$ -2,40". Diante dele, uma senhora de setenta e nove anos, de
cardigã e bolsa no braço, aponta a tela com o indicador, serena e
interessada. Ao lado, uma bibliotecária mais velha, de óculos, estende um
livro de capa dura na direção da senhora, como quem paga um troco. Poucos
elementos, humor seco, estética de revista de tecnologia.
:::

## Aritmética, e as três divisões

Os quatro operadores de sempre funcionam como você espera:

```php title="aritmetica.php" numbered
<?php

$exemplares = 8000;
$prateleiras = 37;

echo $exemplares + $prateleiras, "\n";
echo $exemplares - $prateleiras, "\n";
echo $exemplares * $prateleiras, "\n";
echo $exemplares / $prateleiras, "\n";
```

```text
8037
7963
296000
216.21621621622
```

Repare na última. A divisão com `/` devolve `float` sempre que não for
exata — e você não pode pendurar 216,216 livros numa prateleira. Quando a
pergunta é sobre coisas inteiras, existem dois outros operadores:

```php title="divisoes.php" numbered
<?php

$exemplares = 8000;
$por_prateleira = 37;

var_dump($exemplares / $por_prateleira);
var_dump(intdiv($exemplares, $por_prateleira));
var_dump($exemplares % $por_prateleira);
```

```text
float(216.21621621622)
int(216)
int(8)
```

`intdiv` devolve quantas vezes cabe inteiro: **216 prateleiras cheias**. O
`%`, chamado de módulo ou resto, devolve o que sobrou: **8 livros** para a
prateleira 217.

As duas respostas juntas contam a história completa, e é quase sempre isso
que se quer: quantas caixas preciso, e quanto sobra na última.

:::pitfall
O `%` fica estranho com números negativos, e a razão é que ele segue o sinal
do **dividendo**, não do divisor:

```text
$ php -r 'var_dump(-7 % 3);'
int(-1)
```

Muita gente espera `2`. Se o seu cálculo pode receber negativo e você
precisa de um resto sempre positivo — para distribuir em ciclos, por
exemplo —, a forma segura é `(($a % $b) + $b) % $b`.
:::

Existe ainda a potência, `**`:

```text
$ php -r 'echo 2 ** 10;'
1024
```

E, para acrescentar ou tirar um, o atalho `++` e `--`:

```php title="incremento.php" numbered
<?php

$paginas = 10;

$paginas++;
echo $paginas, "\n";

$paginas--;
echo $paginas, "\n";
```

```text
11
10
```

Existe a forma `++$paginas`, antes do nome, que incrementa e só depois
devolve o valor. A diferença entre as duas só aparece quando você usa o
resultado na mesma expressão, o que é uma economia de uma linha em troca de
uma leitura mais difícil. Prefira incrementar numa linha e usar na seguinte.

## Concatenação é `.`, nunca `+`

```php title="concatenar.php" numbered
<?php

$titulo = "O Cortiço";
$ano = 1890;

$linha = $titulo . ' (' . $ano . ')';

echo $linha, "\n";
```

```text
O Cortiço (1890)
```

O ponto gruda dois textos. Repare que o `$ano` é um número e foi grudado sem
reclamação: o `.` exige texto, então o número vira texto.

Em PHP, `+` é **sempre** aritmético. Não existe soma de textos:

```text
$ php -r 'var_dump("a" + "b");'
PHP Fatal error: Uncaught TypeError: Unsupported operand
types: string + string
```

Isso incomoda quem vem do JavaScript e é, na prática, uma vantagem. Em PHP,
`"10" + 5` nunca vai devolver `"105"` por acidente: ou é conta, ou é erro.

## Atribuir e operar de uma vez

```php title="composta.php" numbered
<?php

$total = 0;
$total += 80;       // o mesmo que $total = $total + 80
$total += 80;
echo $total, "\n";

$relatorio = "Atrasados:\n";
// o mesmo que $relatorio = $relatorio . "- Marlene..."
$relatorio .= "- Marlene\n";
$relatorio .= "- Juvenal\n";
echo $relatorio;
```

```text
160
Atrasados:
- Marlene
- Juvenal
```

Todos os operadores aritméticos têm a forma composta: `+=`, `-=`, `*=`,
`/=`, `%=`, `**=`. E o `.` tem a dele, `.=`, que é como se monta texto aos
poucos.

O `.=` tem um uso que aparece direto: montar um relatório linha a linha,
acrescentando ao final de uma variável que começou vazia.

## Quando o valor pode não estar lá

```php title="coalescencia.php" numbered
<?php

$assunto = null;

$etiqueta = $assunto ?? 'Geral';

echo $etiqueta, "\n";
```

```text
Geral
```

O `??` é a **coalescência nula**: devolve o lado esquerdo se ele existir e
não for nulo; caso contrário, devolve o direito. Ele existe porque a
alternativa é uma escada de três linhas para cada valor opcional.

Existe também `??=`, que só atribui se o que estava lá era nulo:

```php
$status ??= 'disponivel';
```

Há um primo parecido e perigoso, o `?:`, chamado de ternário curto. A
diferença entre os dois é exatamente a armadilha do capítulo
@cap:variaveis-e-tipos:

:::compare left="`?:` olha se é falso" right="`??` olha se é nulo" lang="php"
$m = $multa ?: 500;
// multa = 0 vira 500
---
$m = $multa ?? 500;
// multa = 0 continua 0
:::

O `?:` pergunta "esse valor é falso?", e zero é falso. O `??` pergunta "esse
valor é nulo?", e zero não é nulo. Quando o valor em jogo for número ou
texto que pode legitimamente ser zero ou vazio, `??` é o operador correto e
`?:` é um defeito esperando o dia certo.

## O ternário completo

```php title="ternario.php" numbered
<?php

$dias = 3;

$mensagem = $dias > 0 ? 'em atraso' : 'em dia';

echo $mensagem, "\n";
```

```text
em atraso
```

Lê-se: se a condição for verdadeira, o valor é o do meio; senão, o do fim.
É um `if/else` que **devolve um valor** em vez de executar blocos, e serve
bem quando a decisão cabe confortavelmente numa linha.

:::pitfall
Ternário aninhado é proibido por consequência, não por gosto. Desde o
PHP 8, escrever um dentro do outro sem parênteses é **erro de sintaxe**:

```text
$ php -r 'echo true ? 1 : true ? 2 : 3;'
PHP Fatal error: Unparenthesized `a ? b : c ? d : e` is not
supported
```

A linguagem passou a recusar a construção porque a ordem de avaliação dela
surpreendia todo mundo, inclusive quem a tinha escrito. Quando a decisão tem
três saídas, ela merece um `if` com nome.
:::

## Comparar devolvendo um número

```php title="nave.php" numbered
<?php

$dias = 9;
$limite = 14;

var_dump($dias <=> $limite);
var_dump($limite <=> $dias);
var_dump($dias <=> 9);
```

```text
int(-1)
int(1)
int(0)
```

O `<=>` é chamado de **nave espacial** pelo formato. Ele devolve `-1` se o
lado esquerdo for menor, `1` se for maior e `0` se forem iguais.

Três respostas num operador só parece uma curiosidade até você precisar
ordenar uma lista. Todo algoritmo de ordenação faz a mesma pergunta milhares
de vezes — "esses dois, qual vem primeiro?" — e `-1`, `0` e `1` são
exatamente as três respostas possíveis. Quando houver uma lista de
empréstimos para ordenar por data de devolução, é esse operador que vai
responder.

## Precedência

A ordem completa de avaliação tem vinte níveis e não vale decorar. Vale
conhecer os quatro pontos em que as pessoas erram:

| Escrito | Lido como | A surpresa |
|---|---|---|
| `!$a === $b` | `(!$a) === $b` | `!` vem antes de `===` |
| `$a . $b + $c` | erro no PHP 8 | antes era `($a . $b) + $c` |
| `$a ?? $b ? $c : $d` | erro de sintaxe | `??` e `?:` não se misturam |
| `$a = $b or $c` | `($a = $b) or $c` | `or` é mais fraco que `=` |

Tabela: A última linha é a razão de existirem `and` e `or` em palavras além
de `&&` e `||` — e a razão de não usá-los.

A primeira linha merece atenção porque produz um defeito que passa em
revisão. Você escreve `!$ativo === $esperado` pensando "não é verdade que
ativo seja igual a esperado". O PHP lê "o contrário de ativo é igual a
esperado", que é outra pergunta e às vezes dá a mesma resposta — até o dia
em que não dá.

:::key
Parêntese não custa nada em execução e não custa nada em leitura. Se duas
pessoas numa revisão de código precisarem parar para discutir a ordem de
avaliação, o parêntese já deveria estar lá.
:::

E há um comportamento de `&&` e `||` que vale conhecer, porque ele deixa de
ser curiosidade e vira proteção: os dois **curto-circuitam**. O lado direito
só é avaliado se o esquerdo não tiver decidido a questão sozinho.

```php
if ($dias_de_atraso > 0 && calcularMulta($emprestimo) > 0) {
```

Se `$dias_de_atraso` for zero, o `&&` já sabe que o resultado é falso e a
função nem chega a ser chamada. Inverter a ordem dos dois lados faria a
conta rodar oito mil vezes sem necessidade.

## A pergunta que faltava no totem

```php title="atraso.php (o Sistema)" numbered
<?php

$dias_de_atraso = 14 - 17;
$multa_em_centavos = $dias_de_atraso * 80;

echo $dias_de_atraso, " dias, ", $multa_em_centavos, " centavos\n";
```

```text
-3 dias, -240 centavos
```

A subtração está correta. O problema é que ela responde "quantos dias de
diferença", e o totem mostra a resposta como se fosse "quantos dias de
atraso". Devolver antes do prazo produz diferença negativa, e o resto do
programa acreditou.

O conserto tem uma linha:

```php title="atraso.php (corrigido)" numbered
<?php

$diferenca = 14 - 17;
$dias_de_atraso = max(0, $diferenca);
$multa_em_centavos = $dias_de_atraso * 80;

echo $dias_de_atraso, " dias, ", $multa_em_centavos, " centavos\n";
```

```text
0 dias, 0 centavos
```

`max()` devolve o maior entre os valores recebidos. Com `0` como um dos
lados, ele vira um piso: o resultado nunca desce abaixo de zero. Existe
`min()` para o oposto, que é como se escreve um teto — e é exatamente o que
limita a multa a vinte reais.

:::key
Toda conta que pode dar negativo precisa de uma decisão explícita sobre o
que fazer quando der. `max(0, $x)` é uma decisão; deixar passar também é,
só que tomada por omissão e descoberta pela Dona Marlene.
:::

:::note Na sua carreira
O defeito do totem estava em produção havia cinco anos e ninguém tinha
aberto chamado, porque os leitores que devolviam adiantado olhavam a tela,
achavam estranho e iam embora. O sistema só registra o que alguém reclama.

Quando você herdar um sistema, a lista de chamados abertos não é a lista de
defeitos: é a lista de defeitos que incomodaram alguém o bastante para
justificar uma ligação. A diferença entre as duas listas costuma ser grande,
e a segunda só aparece quando você senta ao lado de quem usa.

Uma tarde de observação no balcão rende mais do que uma semana lendo código.
Leve caderno e não sugira nada no primeiro dia.
:::

:::summary
- `/` devolve `float`; `intdiv` devolve o inteiro; `%` devolve o resto, com
	o sinal do dividendo.
- Concatenação é `.`; `+` é sempre aritmético e dá erro entre textos.
- `+=` e `.=` acumulam valor e texto.
- `??` olha se é nulo; `?:` olha se é falso — e zero separa os dois.
- `<=>` devolve −1, 0 ou 1, que são as três respostas que ordenação precisa.
- Ternário aninhado sem parênteses é erro de sintaxe desde o PHP 8.
- `&&` e `||` curto-circuitam: a ordem dos lados é proteção.
- Conta que pode dar negativo precisa de `max(0, ...)` ou de uma decisão
	escrita sobre o que fazer.
:::

:::checkpoint
Você escreve uma expressão com quatro operadores e prevê o resultado sem
rodar, escolhe entre `/`, `intdiv` e `%` pela pergunta que está fazendo, e
sabe quando `??` e `?:` dão respostas diferentes.
:::

:::exercise level=1
A Casa Amarela recebeu uma doação de 250 livros e tem caixas que comportam
18 cada. Quantas caixas cheias saem, e quantos livros sobram na última?
Imprima as duas respostas.

:::answer
```php
<?php

$livros = 250;
$por_caixa = 18;

$cheias = intdiv($livros, $por_caixa);
$sobra = $livros % $por_caixa;

echo $cheias, " caixas cheias e ", $sobra, " livros na ultima\n";
```

```text
13 caixas cheias e 16 livros na ultima
```

Se a pergunta fosse "quantas caixas preciso comprar", a resposta seria 14 —
e a conta seria `intdiv($livros, $por_caixa) + ($livros % $por_caixa > 0 ? 1 : 0)`,
ou simplesmente `ceil($livros / $por_caixa)`.

A diferença entre 13 e 14 é a diferença entre duas perguntas parecidas, e
quem entrega a resposta errada normalmente não errou a conta.
:::

:::exercise level=2
Sem rodar, diga o que cada linha imprime.

```php
$a = null;
$b = 0;

echo $a ?? 'vazio', "\n";
echo $b ?? 'vazio', "\n";
echo $b ?: 'vazio', "\n";
```

:::answer
```text
vazio
0
vazio
```

A primeira: `$a` é nulo, então o `??` devolve o lado direito.

A segunda: `$b` é zero, que **não é nulo**, então o `??` devolve o próprio
zero.

A terceira: `$b` é zero, que **é falso**, então o `?:` devolve o lado
direito — e uma multa de zero real acabou de virar a palavra "vazio" no
comprovante de alguém.
:::

:::exercise level=3
O trecho abaixo calcula o valor a devolver a um leitor que pagou multa
adiantada e depois teve o atraso recalculado. Ele tem dois defeitos. Aponte
os dois e escreva a versão correta.

```php
$pago = 1500;
$devido = 800;

$diferenca = $pago - $devido;
$mensagem = $diferenca ?: 'nada a devolver';

echo "Devolver: R$ " . $diferenca / 100 . "\n";
echo $mensagem . "\n";
```

:::answer
**Defeito 1: o `?:` com um número.** Quando `$pago` e `$devido` forem
iguais, `$diferenca` é zero, o `?:` considera zero falso e `$mensagem`
recebe `'nada a devolver'`. Nesse caso específico funciona por acaso — mas
o mesmo código, com a intenção de mostrar o valor, esconderia qualquer
diferença de zero. A pergunta correta é sobre o valor, não sobre a
verdade dele.

**Defeito 2: a conta pode dar negativo.** Se o recálculo aumentar a multa,
`$devido` passa a ser maior que `$pago` e o sistema anuncia "Devolver:
R$ -3.5", que é o defeito do totem outra vez, com outra roupa.

```php
$pago = 1500;
$devido = 800;

$a_devolver = max(0, $pago - $devido);
$a_cobrar = max(0, $devido - $pago);

$reais = number_format($a_devolver / 100, 2, ',', '.');

if ($a_devolver > 0) {
    echo "Devolver: R$ ", $reais, "\n";
} elseif ($a_cobrar > 0) {
    echo "Cobrar a diferenca\n";
} else {
    echo "Nada a acertar\n";
}
```

O que mudou de verdade não foi a conta: foram as **três saídas**. O código
original tinha duas variáveis e assumia um único cenário; a versão corrigida
reconhece que "pagou a mais", "pagou a menos" e "pagou certo" são três
situações diferentes, e que o programa precisa saber em qual delas está.

Repare também na divisão por 100 aparecendo uma vez só, na hora de montar o
texto. A conta inteira foi feita em centavos.
:::
