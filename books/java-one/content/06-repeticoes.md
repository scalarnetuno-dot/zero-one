---
title: "Repetições"
number: 6
part: p1
kicker: "Escrever a mesma linha dez vezes é um erro de projeto, não de digitação."
goal: >-
  Escolher entre `for`, `for-each` e `while` conforme o problema, escrever um
  acumulador correto e sair de um laço sem quebrar a lógica.
---

Repetição é a primeira coisa que um computador faz melhor que uma pessoa. E é
também onde mora o primeiro defeito difícil: o laço que roda uma vez a mais,
ou uma a menos.

## Uma lista de valores

```java title="Precos.java" numbered
double[] precos = { 19.90, 4.50, 32.00 };

System.out.println(precos.length);   // 3
System.out.println(precos[0]);       // 19.9
```

Um array tem tamanho fixo, definido no momento em que nasce, e posições
numeradas a partir de **zero**. O último índice é sempre `length - 1` — essa
aritmética de um a menos é a origem de metade dos erros de laço.

:::diagram type="cells" caption="Três valores, índices de 0 a 2. O índice 3 não existe."
items: ["19.90", "4.50", "32.00"]
index: 0
orientation: horizontal
notes:
  - { at: 2, text: "length - 1" }
:::

:::trivia
A contagem a partir de zero não é capricho: em C, `v[i]` significa
literalmente "o endereço de `v` mais `i` posições", então o primeiro item
está a zero posições do início. Java herdou a convenção sem herdar a
aritmética de ponteiro. Edsger Dijkstra escreveu um texto famoso de duas
páginas, em 1982, defendendo que zero é matematicamente mais elegante — e
venceu a discussão, ao menos entre linguagens de chave.
:::

## O laço que você vai usar quase sempre

```java title="for-each"
for (double preco : precos) {
    System.out.println(preco);
}
```

Lê-se "para cada preço em preços". Não há índice, não há contador, não há
como passar do fim. Quando você só precisa visitar todos os elementos — que
é quase sempre —, esta é a forma certa.

## O laço com contador

```java title="for clássico" numbered
for (int i = 0; i < precos.length; i++) {
    System.out.println(i + ": " + precos[i]);
}
```

:::anatomy title="As três partes do for, separadas por ponto e vírgula"
lang: java
code: |
  for (int i = 0; i < precos.length; i++) {
      System.out.println(precos[i]);
  }
notes:
  - { line: 1, text: "**Início**: roda uma vez, antes de tudo. `i` só existe dentro do laço." }
  - { line: 1, text: "**Condição**: testada antes de cada volta. Falsa na primeira vez? O corpo nunca roda." }
  - { line: 1, text: "**Avanço**: roda ao fim de cada volta. Esquecer isto é o laço infinito clássico." }
  - { line: 2, text: "O corpo usa `i` como índice — é o único motivo para escolher esta forma." }
:::

Use o `for` clássico quando o índice fizer parte do que você quer: numerar a
saída, comparar com o elemento anterior, andar de dois em dois.

:::diagram type="flowchart" caption="O laço é uma decisão que volta para si mesma."
nodes:
  - { id: ini,   type: start,    text: "i = 0" }
  - { id: test,  type: decision, text: "i < length?" }
  - { id: corpo, type: process,  text: "usa precos[i]" }
  - { id: inc,   type: process,  text: "i++" }
  - { id: fim,   type: start,    text: "Fim" }
edges:
  - { from: ini,   to: test }
  - { from: test,  to: corpo, label: "sim" }
  - { from: corpo, to: inc }
  - { from: inc,   to: test }
  - { from: test,  to: fim,   label: "não" }
:::

:::pitfall
`i <= precos.length` estoura com
`ArrayIndexOutOfBoundsException: Index 3 out of bounds for length 3`.
O sinal é `<`, sem o igual. Essa exceção tem o nome mais honesto da
plataforma: ela diz qual índice você pediu e qual era o tamanho.
:::

## `while` e `do while`

```java title="Enquanto não acabar" numbered
int tentativas = 0;
while (tentativas < 3) {
    System.out.println("tentativa " + tentativas);
    tentativas++;
}
```

O `while` serve quando você **não sabe quantas voltas** serão necessárias:
ler linhas de um arquivo até acabar, tentar uma conexão até conseguir,
processar uma fila até esvaziar. Se você sabe o número de voltas, o `for` diz
isso melhor.

O `do while` testa **depois** de rodar, então o corpo executa pelo menos uma
vez:

```java
do {
    System.out.println("roda mesmo com a condição falsa");
} while (false);
```

Na prática você vai usá-lo uma vez a cada dois anos, em menu de terminal. Ele
está aqui para você reconhecer quando encontrar.

:::story A sexta-feira do relatório
O relatório de estoque rodava toda sexta às seis da tarde. Nunca tinha dado
problema, o que significa apenas que ninguém tinha olhado.

Naquela sexta, Carlos ajustou uma linha. Uma linha só: trocou o `i++` de
lugar para "deixar mais legível". Fez o commit às 17h52 e foi embora.

Às 18h03, o servidor de homologação começou a esquentar.

Às 19h20, Marina recebeu o alerta em casa, abriu o notebook na mesa de jantar
e encontrou um laço que contava até dez sem nunca chegar a dez. O contador
avançava dentro de um `if` que quase nunca era verdadeiro.

Às 19h41, ela escreveu na revisão do commit uma frase que Carlos guardou para
sempre:

> "Todo laço que você escreve precisa responder a três perguntas antes da
> primeira linha: o que acumula, o que varia e **quando para**. Esta aqui
> respondia duas."

Na segunda-feira, Roberto quis saber por que o ambiente tinha caído. Marina
explicou. Ele ouviu tudo com atenção e fez a única pergunta que importava
para ele:

— Mas isso a gente consegue evitar mudando o processo de deploy?

Marina respondeu que sim. Ele foi embora satisfeito. O laço continuava
errado, mas isso era assunto do Carlos.
:::

:::art caption="Um laço que nunca termina tem o mesmo efeito de uma reunião que nunca termina."
src="um-laco-que-nunca-termina-tem-o-mesmo-efeito-de-uma-reuniao-que-nunca-termina.png"
Charge editorial minimalista: relógio de parede com os ponteiros girando em
círculo desenhados como uma seta circular fechada, ocupando o centro da
composição. Abaixo, um servidor de rack com uma pequena chama de calor saindo
do topo. À direita, uma desenvolvedora de pijama e notebook na mesa de jantar
de casa, expressão cansada, xícara ao lado. À esquerda, uma porta de saída do
escritório se fechando, com a silhueta de alguém indo embora feliz. Fundo
branco, poucos elementos, humor seco, estética editorial de tecnologia.
:::

## Acumular um resultado

```java title="Soma.java" numbered
double total = 0;

for (double preco : precos) {
    total += preco;
}

System.out.println("Total: R$ " + total);
```

A variável `total` nasce **fora** do laço e sobrevive a ele; `preco` nasce
dentro e morre a cada volta. Trocar os dois de lugar é o erro que faz o total
voltar sempre zerado.

:::key
Todo laço útil responde a três perguntas antes da primeira linha: o que
acumula, o que varia e quando para. Se você não consegue responder às três em
voz alta, o laço ainda não está pronto para ser escrito.
:::

:::example Somar, contar e filtrar são o mesmo esqueleto
```java
int caros = 0;
for (double preco : precos) {
    if (preco > 20) {
        caros++;
    }
}
System.out.println(caros + " item(ns) acima de R$ 20");
```
Mesma estrutura do acumulador, com uma decisão dentro. No capítulo 14 essas
três operações ganham nome próprio — `reduce`, `count` e `filter` — e viram
uma linha cada.
:::

## Sair antes: `break` e `continue`

```java title="Parar na primeira ocorrência" numbered
int posicao = -1;
for (int i = 0; i < precos.length; i++) {
    if (precos[i] > 30) {
        posicao = i;
        break;          // achou: não precisa ver o resto
    }
}
```

`break` abandona o laço; `continue` pula para a volta seguinte. Os dois são
legítimos e economizam trabalho — mas cada um deles é um desvio, e desvio
demais transforma o laço em labirinto.

:::pitfall
`break` dentro de um laço aninhado sai **apenas do laço interno**. Quem
espera que ele saia dos dois costuma descobrir isso depois de meia hora. Se
você precisa sair dos dois, o sinal é claro: extraia um método e use
`return`. É o assunto do próximo capítulo.
:::

## Laço infinito: como acontece e como sair

```java
while (true) {
    // sem break, sem return: o programa não termina
}
```

No terminal, `Ctrl+C` encerra. As três causas mais comuns: esquecer o avanço
(`i++`), avançar na direção errada (`i--` com condição `i < n`) ou alterar a
condição dentro do corpo sem perceber. Se o seu programa "travou", suspeite
do laço antes de suspeitar do computador.

:::tree title="Onde estamos agora"
java-one/
  App.java
  Saudacao.java
  Soma.java       # acumulador
  Precos.java     # array + for-each
:::

:::summary
- Array tem tamanho fixo e índices de `0` a `length - 1`.
- `for-each` percorre tudo sem índice: é a forma certa para o caso comum.
- O `for` clássico serve quando o índice faz parte do problema.
- `while` é para quando você não sabe o número de voltas.
- O acumulador mora fora do laço; a variável da volta mora dentro.
:::

:::checkpoint
Você percorre um array das três formas, escreve um acumulador correto, sabe
o que causa um laço infinito e usa `break` sem se perder.
:::

:::milestone
Fim da Parte 1. Você tem um programa que recebe dados, decide e repete — as
três capacidades que qualquer linguagem oferece. A Parte 2 troca "um programa
que roda" por "um programa que se organiza", e é lá que Java começa a
cobrar seu preço e a pagar seus dividendos.
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

:::exercise level=2
Encontre o maior preço de um array sem usar biblioteca. Pense em qual deve
ser o valor inicial da variável do máximo — e por que começar em zero é uma
armadilha.

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

:::exercise level=3
Imprima a tabuada de 1 a 5 usando dois laços aninhados, com uma linha por
número. Depois conte quantas vezes o corpo do laço interno executou.

:::answer
```java
for (int i = 1; i <= 5; i++) {
    for (int j = 1; j <= 10; j++) {
        System.out.print(i * j + " ");
    }
    System.out.println();
}
```
O corpo interno roda 50 vezes: 5 × 10. Essa multiplicação é a primeira
noção de custo — no capítulo 30 ela reaparece com nome feio, *problema N+1*,
quando cada volta de um laço virar uma consulta ao banco.
:::
