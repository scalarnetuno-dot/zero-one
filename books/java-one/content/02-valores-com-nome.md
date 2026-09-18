---
title: "Valores com nome"
number: 2
kicker: "Declarar um tipo é contratar um revisor que trabalha de graça."
---

Um programa guarda coisas: um preço, um nome, uma resposta de sim ou não.
Em Java, guardar exige dizer de que espécie é a coisa guardada. Essa
exigência parece burocracia nos primeiros dez minutos e vira rede de
segurança para o resto da vida.

## A forma da declaração

```java title="Três declarações" numbered
double preco = 19.90;
String cliente = "Ana";
boolean pago = false;
```

Cada linha tem quatro partes: o tipo, o nome, o sinal de igual e o valor.
O tipo fica à esquerda porque é a primeira pergunta que o compilador faz —
e a que ele responde para você mais tarde, quando você errar.

:::diagram type="cells" caption="Uma variável é um nome colado numa caixa de tamanho conhecido."
items: ["19.90", "\"Ana\"", "false"]
orientation: horizontal
notes:
  - { at: 0, text: "double · 8 bytes" }
  - { at: 2, text: "boolean" }
:::

## Os tipos que resolvem 90% dos casos

| Tipo | Guarda | Exemplo |
|---|---|---|
| `int` | número inteiro | `42` |
| `double` | número com casas decimais | `19.90` |
| `boolean` | verdadeiro ou falso | `true` |
| `String` | texto | `"Ana"` |
| `char` | um caractere só | `'A'` |

Table: Os cinco tipos do dia a dia. Os outros existem e podem esperar.

Os quatro primeiros são **tipos primitivos**: o valor mora direto na
variável. `String` é diferente — é uma classe, e a variável guarda uma
referência ao texto. Essa distinção parece teórica agora e explica, no
capítulo 3, o erro mais comum de quem vem de outra linguagem.

:::key
Tipo não é sobre o computador, é sobre você. Quando você escreve `double
preco`, está dizendo à próxima pessoa que ler o código — provavelmente
você, em março — que ali nunca vai aparecer um nome de cliente.
:::

## O compilador confere na hora

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

Repare no momento: isso não aconteceu com o programa rodando na frente de
um cliente. Aconteceu no seu terminal, três segundos depois de você
escrever a linha.

:::warning
`int` e `double` não são intercambiáveis. `int media = 7 / 2;` guarda `3`,
não `3.5` — a divisão entre dois inteiros descarta o resto sem avisar. Se
você quer casas decimais, pelo menos um dos lados precisa ser `double`:
`7.0 / 2`.
:::

## `var`: deixar o compilador escrever o tipo

Desde o Java 10 você pode omitir o tipo quando ele é óbvio pelo valor:

```java
var preco = 19.90;     // double
var cliente = "Ana";   // String
```

O tipo continua existindo e continua sendo verificado — só não está
escrito. Use `var` quando a linha já diz tudo, e escreva o tipo quando o
valor vier de longe, de uma chamada de método cujo retorno não é óbvio.

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
- Declarar é dizer o tipo antes do nome; o tipo é verificado na compilação.
- `int`, `double`, `boolean`, `String` e `char` cobrem quase tudo no começo.
- Divisão entre inteiros descarta o resto — um dos lados precisa ser `double`.
- `var` deduz o tipo sem abrir mão dele; use quando a linha for auto-explicativa.
:::

:::exercise level=1
Declare três variáveis que descrevam um produto de loja: nome, preço e se
está em estoque. Imprima as três em uma linha só.

:::answer
```java
String nome = "Caderno";
double preco = 12.90;
boolean emEstoque = true;
System.out.println(nome + " · R$ " + preco
        + " · estoque: " + emEstoque);
```
:::

:::exercise level=2
Escreva um programa que calcule a média de `7`, `8` e `10` usando `int` e
depois usando `double`. Explique a diferença entre os dois resultados.

:::answer
Com `int`, `(7 + 8 + 10) / 3` dá `8` — o resto é descartado. Com `double`,
`(7 + 8 + 10) / 3.0` dá `8.333...`. A conta é a mesma; o tipo do divisor
decide se a parte fracionária sobrevive.
:::
