---
title: "Variáveis e tipos"
number: 3
slug: variaveis-e-tipos
part: p1
kicker: "Trinta e um pendentes na tela, vinte e sete no papel. Os quatro extras deviam exatamente zero real."
goal: >-
  Usar os tipos básicos com consciência, distinguir ausência de vazio e de
  zero, entender a conversão automática do PHP e saber por que a multa da
  biblioteca não é `float`.
---

:::story Vinte e sete
Vera imprimiu o relatório de pendências e conferiu na mão, com uma régua,
como faz desde 1995.

O relatório dizia trinta e um. A régua dizia vinte e sete.

— Tem quatro sobrando aí.

— Talvez a senhora tenha pulado alguma linha — arriscou a Tainá.

Vera conferiu de novo. Vinte e sete.

Os quatro nomes extras tinham uma coisa em comum, que levou a Tainá uma hora
para encontrar: todos haviam devolvido **no prazo**. A multa deles tinha
sido calculada, registrada e gravada com o valor R$ 0,00.

O Sistema perguntava assim se a multa já tinha sido processada:

```php
if (!$multa) {
    $pendentes[] = $emprestimo;
}
```

E zero, em PHP, é falso.

— A conta está certa — disse Dedé, quando viu. — O relatório é que não sabe
a diferença entre "não deve nada" e "ninguém calculou".

Vera anotou no caderno. Depois riscou e escreveu de novo, com outra letra:

> *"o sistema precisa saber a diferença entre zero e nada"*
:::

Essa frase é a regra que falta ao relatório: zero é um valor; nada é uma
ausência.

## Quando zero vira ausência

```php
$devolvido_em = null;   // ainda não devolveu
$observacao = "";       // devolveu, sem observação
$multa = 0;             // devolveu, sem multa
```

Três valores, três significados completamente diferentes. E, para um `if`
simples, os três são a mesma coisa: falsos.

Isso não é defeito do PHP — toda linguagem dinâmica tem uma lista de valores
"falsos". O que torna o caso do PHP mais perigoso é o tamanho da lista, que
inclui um item que surpreende quase todo mundo.

## Dê um tipo ao que você sabe

Em PHP, toda variável começa com `$` e nenhuma precisa ser declarada. Isso é
pouca cerimônia e tem um efeito colateral bom: `$titulo` é sempre uma
variável, em qualquer contexto, inclusive dentro de uma string. Não há
ambiguidade entre nome de variável, nome de função e palavra reservada.

```php title="tipos.php" numbered
<?php

$titulo = "O Cortiço";
$exemplares = 3;
$peso_kg = 0.42;
$disponivel = true;
$devolvido_em = null;

var_dump($titulo, $exemplares, $peso_kg, $disponivel,
    $devolvido_em);
```

```text
string(10) "O Cortiço"
int(3)
float(0.42)
bool(true)
NULL
```

Repare no `string(10)` para uma palavra de nove letras: o `ç` ocupa dois
bytes. Esse detalhe tem um capítulo próprio, o @cap:strings, e já vale como
aviso.

| Tipo | Exemplo | Onde aparece no projeto |
|---|---|---|
| `string` | `"O Cortiço"` | título, ISBN, nome |
| `int` | `3` | tombo, identificador, dias de atraso |
| `float` | `0.42` | peso, percentual — **não** dinheiro |
| `bool` | `true` | `ativo`, `renovavel` |
| `array` | `[1, 2, 3]` | tudo, e é o capítulo @cap:arrays |
| `null` | `null` | "não informado", "ainda não aconteceu" |
| `object` | `new Livro()` | uma entidade com estado e comportamento |

Tabela: `true`, `false` e `null` não diferenciam maiúsculas, mas a convenção
da PSR-12 é minúscula.

## Uma experiência curta

```php title="o_teste_que_explica.php" numbered
<?php

$valores = [null, "", "0", 0, 0.0, [], "a", 1];

foreach ($valores as $v) {
    printf(
        "%-6s isset:%d  empty:%d  is_null:%d  bool:%d\n",
        var_export($v, true),
        isset($v), empty($v), is_null($v), (bool) $v
    );
}
```

```text
NULL   isset:0  empty:1  is_null:1  bool:0
''     isset:1  empty:1  is_null:0  bool:0
'0'    isset:1  empty:1  is_null:0  bool:0
0      isset:1  empty:1  is_null:0  bool:0
0.0    isset:1  empty:1  is_null:0  bool:0
array  isset:1  empty:1  is_null:0  bool:0
'a'    isset:1  empty:0  is_null:0  bool:1
1      isset:1  empty:0  is_null:0  bool:1
```

Olhe a coluna `bool`. As seis primeiras linhas são todas `0` — todas falsas.
O relatório da Vera tratava seis situações diferentes como se fossem uma.

E a linha do `'0'` é a famosa: **a string `"0"` é falsa em PHP**. É a única
string não vazia que se comporta assim, e existe por herança de uma época em
que tudo que vinha de formulário era texto e `"0"` precisava significar
zero.

:::key
`isset()` responde "existe e não é nulo". `empty()` responde "é um dos
valores falsos". As duas perguntas são diferentes, e **nenhuma delas** é
"tem conteúdo". Quando o que você precisa é distinguir ausência de zero, a
resposta é `=== null` ou `is_null()`.
:::

:::practice
Rode o trecho acima e guarde a saída. Ela responde, de uma vez, umas quinze
dúvidas que vão aparecer nos próximos capítulos — e é bem mais rápida de
consultar do que a documentação.
:::

## O centavo que desaparece

Uma semana depois do relatório, a Vera trouxe outro papel.

```text
$ php -r 'var_dump(0.1 + 0.2);'
float(0.30000000000000004)
$ php -r 'var_dump(0.1 + 0.2 == 0.3);'
bool(false)
```

Isso não é bug. É como todo computador representa número com vírgula: em
base 2. E `0.1` em base 2 é uma dízima infinita, do mesmo jeito que `1/3` é
infinita em base 10.

Na décima sétima casa ninguém se importa. O problema é que o erro se
acumula:

```php title="por_que_nao_float.php" numbered
<?php

$total = 0.0;

for ($i = 0; $i < 1000; $i++) {
    $total += 0.50;
}

var_dump($total);
var_dump($total === 500.0);
```

```text
float(500.0000000000171)
bool(false)
```

Mil multas de cinquenta centavos deveriam dar quinhentos reais. Deram
quinhentos reais e um erro que só aparece na comparação — ou no fechamento
do mês, quando o total do sistema e o total do caixa divergem em centavos e
ninguém sabe qual dos dois está certo.

## Duas perguntas imprecisas

As duas falhas têm a mesma raiz: **o PHP aceitou uma pergunta imprecisa e
respondeu com precisão**.

`if (!$multa)` é uma pergunta imprecisa. Ela parece perguntar "a multa está
ausente?" e na verdade pergunta "a multa é um dos seis valores falsos?". O
PHP respondeu exatamente isso.

`$total += 0.50` é uma operação imprecisa. Ela parece somar cinquenta
centavos e na verdade soma a melhor aproximação binária de cinquenta
centavos. O PHP fez exatamente isso, mil vezes.

:::history
O padrão que rege o `float` — o IEEE 754, de 1985 — foi obra de um comitê
liderado por William Kahan, que ganhou o prêmio Turing por isso. Antes dele,
cada fabricante de processador arredondava do seu jeito, e o mesmo cálculo
dava resultados diferentes em máquinas diferentes.

O `0.30000000000000004` não é um defeito do padrão: é o padrão funcionando,
e funcionando igual em toda parte. O defeito é usar um tipo pensado para
medida física em um valor que precisa ser exato.
:::

## Valores que não mentem

**Para a ausência, pergunte o que você quer saber:**

```php title="explicito.php" numbered
<?php

if ($multa === null) {
    $pendentes[] = $emprestimo;
}

if ($multa > 0) {
    $devedores[] = $emprestimo;
}
```

Duas perguntas diferentes, dois `if` diferentes, nenhuma ambiguidade. Com o
tipo declarado como `?int`, um analisador estático também pode exigir que
você trate o `null` antes de comparar.

**Para dinheiro, guarde centavos como inteiro:**

```php title="dinheiro.php" numbered
<?php

const MULTA_POR_DIA_EM_CENTAVOS = 80;
const TETO_DE_MULTA_EM_CENTAVOS = 2000;

$dias = 1000;
$total = min($dias * MULTA_POR_DIA_EM_CENTAVOS,
    TETO_DE_MULTA_EM_CENTAVOS);

echo 'R$ ', number_format($total / 100, 2, ',', '.'), "\n";
```

```text
R$ 20,00
```

:::key
Inteiro em centavos é exato, soma sem erro, compara com `===` e cabe em
`int` até noventa quatrilhões — o que dá alguma folga para uma biblioteca de
bairro. A divisão por 100 acontece **só na hora de exibir**, nunca no meio
do cálculo.

Mais tarde, essa regra pode morar numa classe `Dinheiro`, para que ninguém
precise lembrar dela. Por ora, a convenção é: **toda variável de dinheiro
termina em `_em_centavos`.** O nome carrega a unidade, e some uma categoria
inteira de erro.
:::

Use `float` para peso, temperatura, percentual e média. Para dinheiro,
nunca.

## Type juggling

Vale conhecer o comportamento que gerou a fama da linguagem:

```text
$ php -r 'var_dump("10" + 5);'
int(15)
$ php -r 'var_dump("10" . 5);'
string(3) "105"
$ php -r 'var_dump(true + true);'
int(2)
```

O PHP converte automaticamente quando a operação exige um tipo diferente do
recebido. `+` é aritmético, então `"10"` vira `10`. `.` é concatenação,
então `5` vira `"5"`.

O que mudou — e mudou para melhor — é o que acontece quando a conversão não
faz sentido:

```text
$ php -r 'var_dump("abc" + 5);'
PHP Fatal error: Uncaught TypeError: Unsupported operand
types: string + int
```

No PHP 7 isso dava `5` com um aviso. No PHP 8 é erro fatal. A linguagem
passou a recusar o absurdo em vez de improvisar.

:::pitfall
Um resquício que sobrevive e convém nunca usar:

```text
$ php -r 'var_dump("10 livros" + 5);'
PHP Warning: A non-numeric value encountered
int(15)
```

A string começa com número, então o PHP aproveita o começo e descarta o
resto, com um aviso que ninguém lê. `declare(strict_types=1)` corta boa parte
dessas conversões — mas todo código PHP que você vai **ler** por aí depende
delas.
:::

## Constantes

```php title="constantes.php" numbered
<?php

const DIAS_DE_EMPRESTIMO = 14;
const LIMITE_POR_LEITOR = 3;

echo DIAS_DE_EMPRESTIMO, "\n";
```

Sem `$` na frente e sem reatribuição possível. `const` é resolvida na
compilação e é a forma preferida; `define()` é de execução e só faz falta
quando o nome ou o valor são dinâmicos.

Essas constantes podem virar configuração quando o prazo deixar de ser uma
decisão do programador. Por enquanto, o valor de mantê-las é estarem **num
lugar só**.

:::note Na sua carreira
Quando alguém do negócio diz que o número do sistema está errado, a chance
de essa pessoa estar certa é alta — e a chance de o sistema estar
tecnicamente funcionando é alta também. As duas coisas ao mesmo tempo.

A Vera não sabia programar e encontrou um defeito que passou quinze anos em
produção, porque ela tinha duas coisas que nenhum teste automatizado tem: o
número certo, contado na mão, e a teimosia de conferir.

O reflexo certo ao receber esse tipo de relato não é explicar por que o
sistema está certo. É pedir **os dois números e a lista**. A diferença entre
31 e 27 é uma abstração; os quatro nomes extras são um caminho direto até a
linha de código.
:::

:::summary
- Toda variável começa com `$` e não precisa ser declarada.
- `null` é ausência, `""` é vazio, `0` é zero — três afirmações diferentes.
- A string `"0"` é falsa; é a única string não vazia que é.
- `isset` pergunta "existe?", `empty` pergunta "é falso?"; nenhuma pergunta
  "tem conteúdo?".
- Dinheiro é `int` em centavos, dividido por 100 só na exibição.
- O nome da variável carrega a unidade: `_em_centavos`.
- O PHP 8 recusa conversão absurda com erro fatal, em vez de improvisar.
:::

:::checkpoint
Você declara e inspeciona variáveis, distingue ausência de vazio e de zero,
e consegue defender numa revisão por que a multa é `int`.
:::

:::exercise level=1
Crie variáveis para um exemplar — tombo, título, disponível, devolvido em —
e imprima o tipo de cada uma com `var_dump`.

:::answer
```php
<?php

$tombo = 812;
$titulo = "O Cortiço";
$disponivel = false;
$devolvido_em = null;

var_dump($tombo, $titulo, $disponivel, $devolvido_em);
```
`$devolvido_em` como `null` é uma afirmação: o empréstimo está aberto. Se
fosse `""`, diria "devolveu em data desconhecida" — que é outra coisa, e
provavelmente um erro de importação.
:::

:::exercise level=2
Escreva uma função que receba dias de atraso e devolva a multa em centavos,
com teto de R$ 20,00. Teste com 0, 1, 25 e 100 dias.

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

var_dump(
    multaEmCentavos(0),
    multaEmCentavos(1),
    multaEmCentavos(25),
    multaEmCentavos(100),
);
```
```text
int(0) int(80) int(2000) int(2000)
```
O caso de 25 dias é o que prova o teto: 25 × 80 = 2000, exatamente no
limite. Testar o valor da borda, e não só um acima e um abaixo, é o hábito
que o capítulo @cap:testes vai formalizar.
:::

:::exercise level=3
O trecho abaixo veio do Sistema. Ele decide se o leitor pode pegar outro
livro. Aponte os três defeitos e diga qual deles nunca aparece em teste.

```php
$emprestimos = buscar_emprestimos($leitor);
if (!$emprestimos) {
    return true;
}
if (count($emprestimos) < LIMITE) {
    return true;
}
return false;
```

:::answer
**Defeito 1 — `!$emprestimos` trata coisas diferentes como iguais.** Se
`buscar_emprestimos` devolver `[]` porque o leitor não tem empréstimo, a
resposta `true` está certa. Se devolver `null` ou `false` porque a
**consulta falhou**, a resposta continua `true` — e o sistema libera o
empréstimo porque não conseguiu verificar. Falhar liberando é a pior forma
de falhar.

**Defeito 2 — o primeiro `if` é desnecessário.** `count([])` é zero, que já
é menor que o limite. Aquele bloco existe porque quem escreveu não confiava
no bloco seguinte — e código escrito por desconfiança é código que ninguém
ousa remover depois.

**Defeito 3 — a função devolve `true`/`false` e perde o motivo.** Quem chama
não sabe se a recusa foi por limite, por multa pendente ou por falha. No
capítulo @cap:excecoes isso vira uma exceção com dados anexados, e no
@cap:services a regra inteira passa a morar num lugar só.

**O que nunca aparece em teste é o primeiro.** Um teste escreve
`buscar_emprestimos` devolvendo array — vazio ou cheio —, porque é isso que
a função devolve quando tudo vai bem. O caminho do `null` só existe quando o
banco cai, e ninguém escreve teste para o banco caindo a menos que já tenha
sido mordido uma vez.

É o mesmo padrão da história de abertura: o defeito não estava no caso
normal nem no caso de erro. Estava no caso **de fronteira**, em que o
sistema tecnicamente funcionou e respondeu a pergunta errada.
:::

:::story A piada final
Na Vertexo, na mesma semana, o Cléber pediu um indicador no painel: "total
de contratos pendentes".

Dedé perguntou o que contava como pendente.

— Os que estão pendentes.

— Contrato com valor zero conta?

Cléber olhou para ele com a expressão de quem foi perguntado se a água é
molhada.

— Por que um contrato teria valor zero?

Três semanas depois, a área comercial começou a cadastrar contratos de
cortesia, com valor zero, para clientes em período de teste.

Dedé já tinha escrito `=== null`.
:::
