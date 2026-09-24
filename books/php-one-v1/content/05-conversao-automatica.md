---
title: "Quando o PHP converte sozinho"
number: 5
slug: conversao-automatica
part: p1
kicker: "Seu Juvenal digitou a senha errada e entrou como bibliotecária-chefe. O culpado tem dois caracteres."
goal: >-
  Prever a conversão automática de tipos em vez de ser surpreendido por ela,
  escolher entre `==` e `===` com critério, e saber por que dinheiro não se
  guarda em `float`.
---

:::story Entrei sem querer
Sexta, 10h20. Seu Juvenal ligou com o tom de quem descobriu uma coisa boa.

— Ó, eu consegui entrar no sistema!

— Ótimo. A senha nova funcionou?

— Não, eu errei a senha. Mas entrei do mesmo jeito. E entrei como a Vera.

Dedé pediu para ele repetir devagar.

Seu Juvenal tinha tentado o usuário da Vera com uma senha qualquer —
segundo ele, "alguma coisa com 240". O Sistema aceitou e abriu o painel da
bibliotecária-chefe, com permissão para apagar acervo.

— Isso é normal?

— Não.

— Porque se for, é bem prático.
:::

O Sistema não tinha sido invadido. Ele estava fazendo exatamente o que o
código mandava, e o código mandava com dois caracteres a menos do que devia.

Para chegar lá, primeiro é preciso entender o que o PHP faz quando recebe
dois tipos diferentes na mesma operação.

## `"10" + 5` dá quinze

```text
$ php -r 'var_dump("10" + 5);'
int(15)
$ php -r 'var_dump("10" . 5);'
string(3) "105"
$ php -r 'var_dump(true + true);'
int(2)
```

O PHP converte automaticamente quando a operação exige um tipo diferente do
que recebeu. Isso tem nome: **coerção de tipo**, ou, no jargão da
comunidade, *type juggling*.

Repare que a decisão não é do valor, é do **operador**. O `+` é aritmético,
então ele exige números e a string `"10"` vira o número `10`. O `.` é
concatenação, então ele exige texto e o número `5` vira `"5"`. O mesmo par
de valores, dois resultados diferentes, porque a pergunta foi outra.

O `true + true` parece brincadeira e não é: `true` convertido para número é
`1`, e `false` é `0`. Esse comportamento é usado de propósito para contar
quantas condições de uma lista foram satisfeitas.

Quando a conversão não faz sentido nenhum, o PHP 8 recusa:

```text
$ php -r 'var_dump("abc" + 5);'
PHP Fatal error: Uncaught TypeError: Unsupported operand
types: string + int
```

No PHP 7 isso devolvia `5` com um aviso que ninguém lia. A linguagem passou
a recusar o absurdo em vez de improvisar, e essa é a diferença mais
importante entre o PHP que tem má fama e o PHP que você está aprendendo.

:::pitfall
Um resquício sobreviveu, e convém nunca usá-lo:

```text
$ php -r 'var_dump("10 livros" + 5);'
PHP Warning: A non-numeric value encountered
int(15)
```

A string **começa** com número, então o PHP aproveita o começo e descarta o
resto, com um aviso que costuma estar desligado em produção.

Isso importa porque tudo que chega de um formulário chega como texto. O
campo "quantidade" preenchido com `3 caixas` não vai dar erro: vai virar
`3`, silenciosamente, e a diferença vai aparecer no estoque duas semanas
depois.
:::

## A lista fechada do que é falso

Quando um valor qualquer é usado onde a linguagem espera verdadeiro ou
falso — dentro de um `if`, por exemplo —, ele é convertido. A lista do que
vira `false` é curta e fechada:

| Valor | Vira `false`? |
|---|---|
| `false` | sim |
| `0` e `0.0` | sim |
| `""` (texto vazio) | sim |
| `"0"` (o texto com um zero) | **sim** |
| `[]` (lista vazia) | sim |
| `null` | sim |
| qualquer outra coisa | não |

Tabela: Sete linhas. Tudo que não está aqui é verdadeiro, inclusive `-1`,
`"false"` e `"0.0"`.

A linha que surpreende quase todo mundo é a quarta. **A string `"0"` é falsa
em PHP** — e é a única string não vazia que é.

```text
$ php -r 'var_dump((bool) "0", (bool) "0.0", (bool) "false");'
bool(false)
bool(true)
bool(true)
```

O texto `"0"` é falso; o texto `"0.0"` é verdadeiro; o texto `"false"` é
verdadeiro. Não há lógica a deduzir aqui, só uma regra a conhecer: ela
existe porque, numa época em que tudo que vinha de formulário era texto,
`"0"` precisava significar zero.

É uma armadilha real. Um campo de formulário preenchido com `0` chega como
`"0"`, e `if ($quantidade)` decide que não foi preenchido.

## `==` converte, `===` não

```text
$ php -r 'var_dump(1 == "1");'
bool(true)
$ php -r 'var_dump(1 === "1");'
bool(false)
```

São dois operadores diferentes, não duas formas de escrever o mesmo.

**`==` compara depois de converter.** Ele pega os dois lados, encontra um
tipo comum e compara os resultados. Por isso o número `1` e o texto `"1"`
são iguais para ele.

**`===` compara valor e tipo, sem converter nada.** Tipos diferentes já
respondem `false`, sem nem olhar o valor.

| Comparação | `==` | `===` |
|---|---|---|
| `1` e `"1"` | `true` | `false` |
| `0` e `""` | `false` (desde o PHP 8) | `false` |
| `"abc"` e `0` | `false` (desde o PHP 8) | `false` |
| `null` e `false` | `true` | `false` |
| `"1e3"` e `"1000"` | `true` | `false` |

Tabela: A quarta linha produz defeito silencioso — `null == false` faz "não
informado" passar por "negado". A quinta é a que abriu a porta da Casa
Amarela.

:::trivia
No PHP 7, `0 == "abc"` era **verdadeiro**: a string não numérica virava `0`.
Qualquer comparação frouxa entre zero e texto passava.

O PHP 8 inverteu a regra — agora é o número que vira texto quando o texto
não é numérico — e `0 == "abc"` passou a ser `false`. Foi uma das poucas
quebras de compatibilidade da história do PHP de que praticamente ninguém
reclamou. A proposta se chamava *Saner string to number comparisons*, e o
nome já dizia o que a comunidade achava do comportamento anterior.
:::

A recomendação cabe numa linha: **use `===` por padrão**. Escreva `==` só
quando a conversão for exatamente o que você quer, e deixe um comentário
dizendo por quê.

## Dois caracteres na porta

Com isso na cabeça, dá para ler o `login.php` do Sistema.

```php title="login.php (o Sistema, 2009)" numbered
<?php

$senha_enviada = md5($_POST['senha']);

if ($senha_enviada == $senha_guardada) {
    entrar();
}
```

O `md5()` embaralha um texto num código de 32 caracteres, sempre do mesmo
jeito: a mesma senha gera sempre o mesmo código. Era assim que se guardava
senha em 2009 — não se guardava a senha, guardava-se o embaralhado.

Agora olhe o que acontece com duas senhas específicas:

```text
$ php -r 'echo md5("240610708"), "\n";'
0e462097431906509019562988736854
$ php -r 'echo md5("QNKCDZO"), "\n";'
0e830400451993494058024219903391
```

São dois códigos diferentes. E mesmo assim:

```text
$ php -r 'var_dump(md5("240610708") == md5("QNKCDZO"));'
bool(true)
```

Os dois começam com `0e` e têm só dígitos depois. Isso é a forma como se
escreve notação científica: `0e462...` é **zero elevado a 462...**, que é
zero. O `==` viu duas strings numéricas, converteu as duas para o número
`0.0` e comparou os números.

O código da senha da Vera, gravado em 2009, tinha esse formato. Qualquer
senha cujo `md5` também tivesse entrava na conta dela — e existem milhares
de textos assim, catalogados em listas públicas há mais de uma década.

Seu Juvenal acertou um por acaso.

:::story Quatro minutos
Dedé escreveu um programa de vinte linhas que testava uma lista pública de
textos com código no formato `0e`.

Em quatro minutos, tinha encontrado duas contas de atendente vulneráveis.

A da Vera era uma delas.

— Desde quando? — perguntou ela.

— Desde 2009.

Vera ficou quieta um tempo, alisando a etiqueta de um livro que já estava
colada.

— E quantas pessoas sabiam?

— Ninguém. Foi o Seu Juvenal, errando a senha.

— Então a gente teve sorte.

— A gente teve o Seu Juvenal.
:::

O defeito tinha três camadas, e vale separar porque o conserto de cada uma é
diferente.

**Primeira: `==` entre segredos.** A comparação frouxa transformou dois
valores distintos em iguais. Um `===` teria evitado este incidente
específico.

**Segunda: MD5 para senha.** Mesmo com `===`, o MD5 é rápido demais — uma
placa de vídeo comum calcula bilhões por segundo, o que torna viável testar
senhas em massa até acertar. Senha pede um algoritmo propositalmente lento,
que é o que `password_hash()` usa.

**Terceira: comparação em tempo variável.** Mesmo com `===`, a comparação de
texto do PHP para no primeiro caractere diferente. Um palpite que acerta os
cinco primeiros caracteres demora mensuravelmente mais que um que erra o
primeiro — e, com requisições suficientes, dá para descobrir um segredo
caractere a caractere sem nunca acertá-lo inteiro.

:::key
Comparação de segredo — senha, token, assinatura — não usa `==` nem `===`.
Usa `hash_equals()`, que percorre o comprimento inteiro sempre, não importa
onde esteja a diferença:

```php
if (hash_equals($esperado, $enviado)) {
```

A ordem importa: o valor **conhecido** vem primeiro.

E, para senha especificamente, nem isso: a dupla `password_hash()` e
`password_verify()` já resolve algoritmo, sal e tempo constante de uma vez.
Guardar senha de qualquer outro jeito, em 2026, é decisão que precisa ser
defendida por escrito.
:::

## Converter de propósito

Quando você **quer** a conversão, peça por ela. Um **cast** é um tipo entre
parênteses na frente do valor:

```php title="casts.php" numbered
<?php

$texto = "42.7";

var_dump((int) $texto);
var_dump((float) $texto);
var_dump((string) 42);
var_dump((bool) $texto);
```

```text
int(42)
float(42.7)
string(2) "42"
bool(true)
```

Repare no primeiro: `(int) "42.7"` devolveu `42`, não `43`. O cast para
inteiro **descarta** a parte decimal, não arredonda. Para arredondar existe
`round()`, e a diferença de um centavo entre as duas escolhas é a origem de
uma quantidade desproporcional de reclamações de cliente.

A vantagem do cast sobre a conversão automática não é técnica, é de leitura:
quem revisa o código vê que a conversão foi uma decisão, e não um acidente.

## O centavo que desaparece

Falta o último lugar em que o PHP responde com precisão a uma pergunta
imprecisa.

```text
$ php -r 'var_dump(0.1 + 0.2);'
float(0.30000000000000004)
$ php -r 'var_dump(0.1 + 0.2 == 0.3);'
bool(false)
```

Isso não é bug do PHP, e não é específico dele: é como todo computador
representa número com vírgula, em base 2. O valor `0.1` em base 2 é uma
dízima infinita, do mesmo jeito que `1/3` é infinita em base 10. Em algum
ponto o computador corta, e o que sobra é uma aproximação muito boa e não
exata.

Na décima sétima casa decimal ninguém se importa. O problema é que o erro se
acumula:

```php title="por_que_nao_float.php" numbered
<?php

$total = 0.0;
$i = 0;

while ($i < 1000) {
    $total = $total + 0.50;
    $i = $i + 1;
}

var_dump($total);
var_dump($total === 500.0);
```

```text
float(500.0000000000171)
bool(false)
```

Mil multas de cinquenta centavos deveriam dar quinhentos reais. Deram
quinhentos reais e um erro invisível — que só aparece na comparação, ou no
fechamento do mês, quando o total do sistema e o total do caixa divergem em
centavos e ninguém sabe qual dos dois está certo.

:::history
O padrão que rege o `float` — o IEEE 754, de 1985 — foi obra de um comitê
liderado por William Kahan, que ganhou o prêmio Turing por isso. Antes dele,
cada fabricante de processador arredondava do seu jeito, e o mesmo cálculo
dava resultados diferentes em máquinas diferentes.

O `0.30000000000000004` não é defeito do padrão: é o padrão funcionando, e
funcionando igual em toda parte. O defeito é usar um tipo pensado para
medida física num valor que precisa ser exato.
:::

A saída é não guardar reais. Guardar **centavos**, como inteiro:

```php title="dinheiro.php" numbered
<?php

const MULTA_POR_DIA_EM_CENTAVOS = 80;
const TETO_DE_MULTA_EM_CENTAVOS = 2000;

$dias = 12;
$total_em_centavos = $dias * MULTA_POR_DIA_EM_CENTAVOS;

if ($total_em_centavos > TETO_DE_MULTA_EM_CENTAVOS) {
    $total_em_centavos = TETO_DE_MULTA_EM_CENTAVOS;
}

$reais = number_format($total_em_centavos / 100, 2, ',', '.');
echo 'R$ ', $reais, "\n";
```

```text
R$ 9,60
```

O `number_format` monta o texto para exibir: recebe o valor, o número de
casas decimais, o separador decimal e o separador de milhar. Com `','` e
`'.'` nessas posições, sai no formato brasileiro.

:::key
Inteiro em centavos é exato, soma sem erro, compara com `===` e cabe em
`int` até noventa quatrilhões — folga suficiente para uma biblioteca de
bairro. A divisão por 100 acontece **só na hora de exibir**, nunca no meio
de um cálculo.

E a convenção que sustenta a regra é o nome: **toda variável de dinheiro
termina em `_em_centavos`.** O nome carrega a unidade, e some uma categoria
inteira de erro — inclusive a de alguém somar um valor em reais com um em
centavos seis meses depois.
:::

Use `float` para peso, temperatura, percentual e média. Para dinheiro,
nunca.

:::note Na sua carreira
Encontrar uma falha de segurança num sistema que não é seu é uma situação
socialmente desconfortável, e a forma de comunicar muda o resultado.

O que funciona: escrever, para a pessoa responsável, com **o impacto em
linguagem de negócio primeiro** e o detalhe técnico depois. "É possível
entrar na conta da bibliotecária-chefe sem saber a senha, e apagar o acervo"
comunica melhor do que "há uma comparação frouxa de hash MD5".

O que não funciona: demonstrar publicamente. Entrar na conta de alguém para
provar o ponto, mesmo com a melhor das intenções, transfere o problema para
você — e a conversa deixa de ser sobre a falha e passa a ser sobre o seu
acesso.

E há uma regra prática que vale para a carreira inteira: **registre a
data**. Se o conserto demorar seis meses e algo acontecer, a distância entre
"eu avisei" e "eu avisei em 14 de março, neste e-mail" é enorme.
:::

:::summary
- O PHP converte tipos quando o operador exige: `+` puxa para número, `.`
	puxa para texto.
- Texto que começa com número é aproveitado pela metade, com aviso.
- A lista de valores falsos é fechada e tem sete linhas — `"0"` está nela.
- `==` compara depois de converter; `===` compara valor e tipo. Use `===`.
- Segredo não se compara com `===`, e sim com `hash_equals`; senha usa
	`password_verify`.
- Cast é conversão pedida por escrito, e `(int)` descarta a parte decimal em
	vez de arredondar.
- Dinheiro é `int` em centavos, dividido por 100 só na exibição, com a
	unidade no nome da variável.
:::

:::checkpoint
Você prevê o resultado de uma operação entre tipos diferentes, escolhe entre
`==` e `===` justificando a escolha, e sabe explicar numa revisão por que a
multa é inteiro.
:::

:::exercise level=1
Sem rodar, diga o resultado e o tipo de cada expressão. Depois confira com
`var_dump`.

```php
"7" + 3
"7" . 3
"7" == 7
"7" === 7
(int) "9 livros"
(bool) "0"
```

:::answer
```text
int(10)
string(2) "73"
bool(true)
bool(false)
int(9)
bool(false)
```

A quinta é a mais perigosa das seis: `(int) "9 livros"` devolve `9` sem
reclamar nada, porque um cast explícito não emite o aviso que a soma
emitiria. Você pediu a conversão; o PHP fez o melhor que deu.
:::

:::exercise level=2
O trecho abaixo confere um cupom de desconto enviado num formulário. Ele
tem dois defeitos. Encontre os dois e escreva a versão correta.

```php
$cupom = $_POST['cupom'];

if ($cupom == 0) {
    echo "sem cupom";
}
```

:::answer
**Defeito 1: `==` com um número do lado direito.** Antes do PHP 8, qualquer
texto não numérico viraria `0` e entraria no `if`. No PHP 8 isso foi
corrigido, mas o código continua dizendo uma coisa e querendo dizer outra.

**Defeito 2: a pergunta está errada.** "Sem cupom" é a ausência do campo, e
não o valor zero. O campo pode nem ter sido enviado, e aí `$_POST['cupom']`
produz um aviso de índice indefinido antes de qualquer comparação.

```php
$cupom = $_POST['cupom'] ?? '';

if ($cupom === '') {
    echo "sem cupom";
}
```

O `?? ''` devolve o lado esquerdo se ele existir e não for nulo; senão,
devolve o direito. Ele resolve o aviso e garante que a comparação seguinte
compare texto com texto.

Vale notar o que a versão corrigida deixou de aceitar: o cupom `"0"`. Se
existir um cupom com esse código, a versão original o rejeitaria
silenciosamente — e essa é precisamente a categoria de defeito que só
aparece quando o pessoal do comercial cadastra um.
:::

:::exercise level=3
A Casa Amarela cobra 80 centavos por dia de atraso, com teto de R$ 20,00.
Escreva o cálculo para 0, 1, 25 e 100 dias, guardando tudo em centavos, e
explique por que o caso de 25 dias é o mais importante de testar.

:::answer
```php
<?php

const MULTA_POR_DIA_EM_CENTAVOS = 80;
const TETO_DE_MULTA_EM_CENTAVOS = 2000;

$casos = [0, 1, 25, 100];

foreach ($casos as $dias) {
    $total = $dias * MULTA_POR_DIA_EM_CENTAVOS;

    if ($total > TETO_DE_MULTA_EM_CENTAVOS) {
        $total = TETO_DE_MULTA_EM_CENTAVOS;
    }

    echo $dias, " dias: ", $total, " centavos\n";
}
```

```text
0 dias: 0 centavos
1 dias: 80 centavos
25 dias: 2000 centavos
100 dias: 2000 centavos
```

O `foreach` percorre uma lista de valores, um por vez — aqui serve só para
não repetir o cálculo quatro vezes.

O caso de 25 dias é o importante porque 25 × 80 dá exatamente 2000, o valor
do teto. É a **fronteira**: o ponto em que o comportamento muda. Um erro de
um caractere na condição — `>` no lugar de `>=`, ou vice-versa — não aparece
em 1 dia nem em 100 dias, e aparece em 25.

Testar um valor abaixo, um acima e **o valor exato da borda** é o hábito que
separa quem testa de quem confere.

E vale reparar no que o exercício não pediu: em nenhum momento apareceu
`0.80`. A conta inteira é feita com números inteiros, e a vírgula só entraria
na hora de imprimir o comprovante.
:::
