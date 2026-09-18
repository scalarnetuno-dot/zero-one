---
title: "Repetir"
number: 4
kicker: "Escrever a mesma linha dez vezes é um erro de projeto, não de digitação."
---

Repetição é a primeira coisa que um computador faz melhor que uma pessoa.
E é também onde mora o primeiro defeito difícil: o laço que roda uma vez a
mais, ou a menos.

## Uma lista de valores

```java title="Precos.java" numbered
double[] precos = { 19.90, 4.50, 32.00 };

System.out.println(precos.length);   // 3
System.out.println(precos[0]);       // 19.9
```

Um array tem tamanho fixo, definido no momento em que nasce, e posições
numeradas a partir de **zero**. O último índice é sempre `length - 1` — e
essa aritmética de um a menos é a origem da metade dos erros de laço.

:::diagram type="cells" caption="Três valores, índices de 0 a 2. O quarto índice não existe."
items: ["19.90", "4.50", "32.00"]
index: 0
orientation: horizontal
notes:
  - { at: 2, text: "length - 1" }
:::

## O laço que você vai usar quase sempre

```java title="for-each"
for (double preco : precos) {
    System.out.println(preco);
}
```

Lê-se "para cada preço em preços". Não há índice, não há contador, não há
como passar do fim. Quando você só precisa visitar todos os elementos —
que é quase sempre —, esta é a forma certa.

## O laço com contador

```java title="for clássico" numbered
for (int i = 0; i < precos.length; i = i + 1) {
    System.out.println(i + ": " + precos[i]);
}
```

Três partes separadas por ponto e vírgula: onde começa, até quando
continua, e como avança. Use esta forma quando o índice fizer parte do que
você quer — numerar a saída, comparar com o elemento anterior, andar de
dois em dois.

:::diagram type="flowchart" caption="O laço é uma decisão que volta para si mesma."
nodes:
  - { id: ini,  type: start,    text: "i = 0" }
  - { id: test, type: decision, text: "i < length?" }
  - { id: corpo,type: process,  text: "usa precos[i]" }
  - { id: inc,  type: process,  text: "i = i + 1" }
  - { id: fim,  type: start,    text: "Fim" }
edges:
  - { from: ini,   to: test }
  - { from: test,  to: corpo, label: "sim" }
  - { from: corpo, to: inc }
  - { from: inc,   to: test }
  - { from: test,  to: fim,   label: "não" }
:::

:::warning
`i <= precos.length` estoura com
`ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3`.
O sinal é `<`, sem o igual. Guarde a mensagem: ela vai aparecer de novo,
e ela sempre diz exatamente qual índice você tentou usar.
:::

## Acumular um resultado

```java title="Soma.java" numbered
double total = 0;

for (double preco : precos) {
    total = total + preco;
}

System.out.println("Total: R$ " + total);
```

A variável `total` nasce **fora** do laço e sobrevive a ele; `preco` nasce
dentro e morre a cada volta. Trocar os dois de lugar é o erro que faz o
total voltar sempre zerado.

:::example Contar sem somar
```java
int caros = 0;
for (double preco : precos) {
    if (preco > 20) {
        caros = caros + 1;
    }
}
System.out.println(caros + " item(ns) acima de R$ 20");
```
O mesmo esqueleto do acumulador, com uma decisão dentro. Somar, contar e
filtrar são a mesma estrutura com corpos diferentes.
:::

:::key
Todo laço útil tem três perguntas respondidas antes da primeira linha: o
que acumula, o que varia e quando para. Se você não consegue responder às
três em voz alta, o laço ainda não está pronto para ser escrito.
:::

:::summary
- Array tem tamanho fixo e índices de `0` a `length - 1`.
- `for-each` percorre tudo sem índice: é a forma certa para o caso comum.
- O `for` clássico serve quando o índice faz parte do problema.
- O acumulador mora fora do laço; a variável da volta mora dentro.
:::

:::exercise level=1
Percorra um array de cinco notas e imprima apenas as que forem maiores ou
iguais a 7.

:::answer
```java
double[] notas = { 5.0, 7.0, 9.5, 6.4, 8.0 };
for (double nota : notas) {
    if (nota >= 7) {
        System.out.println(nota);
    }
}
```
:::

:::exercise level=3
Encontre o maior preço de um array sem usar nenhuma biblioteca. Pense em
qual deve ser o valor inicial da variável que guarda o máximo — e por que
começar em zero é uma armadilha.

:::answer
```java
double maior = precos[0];
for (double preco : precos) {
    if (preco > maior) {
        maior = preco;
    }
}
```
Começar em `0` só funciona por acidente, quando todos os valores são
positivos. Começar pelo primeiro elemento funciona sempre — inclusive com
temperaturas negativas, que é onde a versão preguiçosa quebra.
:::
