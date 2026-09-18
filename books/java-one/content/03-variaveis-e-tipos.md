---
title: "Variáveis e tipos"
number: 3
part: p1
kicker: "Declarar um tipo é contratar um revisor que trabalha de graça."
goal: >-
  Declarar variáveis dos cinco tipos do dia a dia, prever o resultado de uma
  conversão e saber quando usar `var` sem perder a proteção do compilador.
---

Um programa guarda coisas: um preço, um nome, uma resposta de sim ou não. Em
Java, guardar exige dizer de que espécie é a coisa guardada. Essa exigência
parece burocracia nos primeiros dez minutos e vira rede de segurança para o
resto do projeto.

## A forma da declaração

```java title="Três declarações" numbered
double preco = 19.90;
String cliente = "Ana";
boolean pago = false;
```

Cada linha tem quatro partes: o tipo, o nome, o sinal de igual e o valor. O
tipo fica à esquerda porque é a primeira pergunta que o compilador faz — e a
que ele responde para você mais tarde, quando você errar.

:::diagram type="cells" caption="Uma variável é um nome colado em uma caixa de tamanho conhecido."
items: ["19.90", "\"Ana\"", "false"]
orientation: horizontal
notes:
  - { at: 0, text: "double · 8 bytes" }
  - { at: 2, text: "boolean" }
:::

## Os tipos que resolvem quase tudo

| Tipo | Guarda | Faixa ou exemplo |
|---|---|---|
| `int` | inteiro | de −2,1 bilhões a 2,1 bilhões |
| `long` | inteiro grande | até 9,2 quintilhões |
| `double` | decimal | `19.90` |
| `boolean` | verdade ou falso | `true` |
| `String` | texto | `"Ana"` |
| `char` | um caractere | `'A'` |

Tabela: Os seis tipos do dia a dia. Os outros — `byte`, `short`, `float` —
existem e podem esperar até você ter um motivo de memória para usá-los.

Os cinco primeiros, menos `String`, são **tipos primitivos**: o valor mora
direto na variável. `String` é uma classe, e a variável guarda uma
*referência* ao texto. Essa distinção parece teórica agora e explica, no
capítulo 4, o erro mais comum de quem vem de outra linguagem.

:::key
Tipo não é sobre o computador, é sobre você. Quando você escreve
`double preco`, está avisando à próxima pessoa que ler o código —
provavelmente você, em março — que ali nunca vai aparecer um nome de
cliente.
:::

## O compilador confere antes de rodar

```java title="Erro pego antes de rodar"
int quantidade = 3;
quantidade = "três";
```

```text title="Terminal"
Caixa.java:3: error: incompatible types:
    String cannot be converted to int
        quantidade = "três";
                     ^
```

Repare no momento: isso não aconteceu com o programa rodando na frente de um
cliente. Aconteceu no seu terminal, três segundos depois de você escrever a
linha. Em uma linguagem dinâmica, o mesmo defeito esperaria a requisição
número mil e uma para aparecer.

## Conversões: quando o tipo muda de ideia

Java converte automaticamente o que não perde informação — um `int` cabe em
um `double`. O contrário exige que você assuma a responsabilidade por
escrito:

:::compare left="Automático (widening)" right="Explícito (casting)"
int i = 42;
double d = i;
// 42.0
---
double d = 42.9;
int i = (int) d;
// 42, truncado
:::

O `(int)` é um **cast**: você está dizendo "eu sei que pode perder coisa,
faça assim mesmo". E perde: `42.9` vira `42`, não `43`. Java trunca, não
arredonda.

:::pitfall
`int media = 7 / 2;` guarda `3`, não `3.5`. A divisão entre dois inteiros
descarta o resto sem aviso nenhum. Se você quer casas decimais, pelo menos
um dos lados precisa ser decimal: `7.0 / 2`. Este é, com folga, o erro de
tipo mais comum em código de cobrança.
:::

:::story O centavo do Seu Antônio
A primeira nota fiscal de teste saiu com R$ 56,40. A segunda, com R$ 56,39.

Os mesmos produtos. O mesmo carrinho. Um centavo de diferença.

Cláudia levou o caso para a reunião com a cara de quem traz uma bomba
embrulhada em papel de presente.

— O cliente vai perguntar.

— É arredondamento — disse Carlos.

— O cliente vai perguntar *por que* — insistiu Cláudia.

Marina abriu o código, olhou três segundos e apontou a linha:
`double preco`.

— Não é arredondamento. É que a gente pediu para o computador guardar
dinheiro em uma caixa que não sabe guardar dinheiro.

Seu Antônio, que estava testando a loja naquele mesmo dia, ligou à tarde
para avisar que tinha comprado um cabo de R$ 19,90 e o total dizia R$ 19,89.
Ele não sabia explicar float, ponto flutuante nem IEEE 754. Sabia contar
dinheiro.
:::

## Dinheiro não é `double`

Guarde esta, porque o capítulo 19 vai cobrar: `double` é binário e não
representa `0.1` exatamente.

```java title="A conta que não fecha" numbered
double total = 0.1 + 0.2;
System.out.println(total);
```

```text title="Saída"
0.30000000000000004
```

Não é bug do Java: é como números de ponto flutuante funcionam em qualquer
linguagem. Para dinheiro, existe `BigDecimal`, que guarda o valor em base
decimal e cobra mais verbosidade em troca de exatidão. O projeto do livro vai
usar `BigDecimal` no preço do produto a partir do capítulo 18.

:::trivia
O padrão IEEE 754, que define esse comportamento, é de 1985 e foi desenhado
por um comitê que incluía William Kahan — que ganhou o prêmio Turing por
isso. A imprecisão não é descuido: é o preço de representar números enormes
e minúsculos com 64 bits. Java só não deixa você esquecer que ele existe.
:::

## Constantes

Quando o valor não deve mudar, `final` transforma a tentativa em erro de
compilação:

```java
final double TAXA = 0.08;
// TAXA = 0.09;
// error: cannot assign a value to final variable TAXA
```

A convenção de nome em maiúsculas com sublinhado (`TAXA_MAXIMA`) é só
convenção — mas é universal em Java, e código que a ignora parece estrangeiro.

## `var`: deixar o compilador escrever o tipo

Desde o Java 10 você pode omitir o tipo quando ele é óbvio pelo valor:

```java
var preco = 19.90;     // double
var cliente = "Ana";   // String
```

O tipo continua existindo e continua sendo verificado — ele só não está
escrito. Use `var` quando a linha já diz tudo; escreva o tipo quando o valor
vier de longe, de uma chamada de método cujo retorno não é evidente.

:::pitfall
`var` não é o `var` do JavaScript. Ele não cria uma variável sem tipo: ele
*infere* o tipo e o trava ali. Depois de `var x = 10;`, a linha `x = "dez";`
não compila. E `var` sem valor inicial (`var x;`) também não compila — não
há de onde inferir.
:::

:::example Nome que explica, tipo que protege
```java
double t = 56.4;              // o que é t?
double totalDoPedido = 56.4;  // agora o humano também entende
```
O compilador aceita os dois. Só um deles ainda faz sentido daqui a seis
meses.
:::

:::term Variável
Um nome ligado a um espaço de memória de tipo conhecido. Em Java o tipo é
fixo: o valor muda, a espécie não.
:::

:::summary
- Declarar é dizer o tipo antes do nome; o tipo é conferido na compilação.
- `int`, `long`, `double`, `boolean`, `String` e `char` cobrem quase tudo.
- Divisão entre inteiros descarta o resto; um dos lados precisa ser decimal.
- `double` não serve para dinheiro — o projeto vai usar `BigDecimal`.
- `var` infere o tipo sem abrir mão dele.
:::

:::checkpoint
Você declara variáveis dos seis tipos básicos, prevê o que acontece em uma
conversão, sabe por que `0.1 + 0.2` não dá `0.3` e usa `final` e `var` no
lugar certo.
:::

:::milestone
O projeto ainda é um punhado de arquivos `.java` soltos, mas agora eles
guardam dados com tipo declarado. É o vocabulário mínimo da entidade
`Product` que nasce no capítulo 18.
:::

:::exercise level=1
Declare as quatro variáveis que descrevem um produto de loja: nome, preço,
quantidade em estoque e se está ativo. Imprima as quatro em uma linha.

:::answer
```java
String nome = "Teclado mecânico";
double preco = 349.90;
int quantidade = 12;
boolean ativo = true;
System.out.println(nome + " · R$ " + preco
        + " · " + quantidade + " un · ativo: " + ativo);
```
Essas quatro linhas são o rascunho da entidade `Product`. Guarde o arquivo.
:::

:::exercise level=2
Calcule a média de `7`, `8` e `10` primeiro com `int` e depois com `double`.
Explique a diferença em uma frase.

:::answer
Com `int`, `(7 + 8 + 10) / 3` dá `8` — o resto é descartado. Com
`(7 + 8 + 10) / 3.0` dá `8.333...`. A conta é a mesma; o tipo do divisor
decide se a parte fracionária sobrevive.
:::

:::exercise level=3
Some `0.1` dez vezes em um laço e imprima o resultado. Depois refaça com
`BigDecimal` (`new BigDecimal("0.1")` e o método `add`). Compare as saídas.

:::answer
O `double` imprime `0.9999999999999999`. O `BigDecimal` imprime `1.0`. A
diferença é invisível em um relatório e catastrófica em uma fatura — e é por
isso que sistemas financeiros proíbem `double` por política, não por gosto.
:::
