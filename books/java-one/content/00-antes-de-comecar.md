---
title: "Antes de começar"
matter: front
numbered: false
kicker: "Um livro curto sobre uma linguagem que costuma ser ensinada longa demais."
---

Java tem trinta anos e uma reputação pesada. Quem chega perto ouve falar de
máquina virtual, de classes abstratas, de injeção de dependência e de um
arquivo XML que ninguém sabe explicar. Nada disso é necessário para escrever
o seu primeiro programa útil — e nada disso aparece neste volume.

O que aparece é o essencial: um arquivo, um método `main`, valores com tipo,
uma decisão, uma repetição, um método com retorno. Seis ideias. Com elas você
escreve um programa que faz um trabalho de verdade, e é isso que sustenta a
vontade de aprender o resto.

## Como este livro funciona

Cada capítulo abre com uma pergunta prática e fecha com um resumo curto e
exercícios. O código é curto de propósito: se um exemplo não cabe em meia
página, ele está ensinando duas coisas ao mesmo tempo.

:::key
Você vai usar `javac` e `java` no terminal. Não porque IDE seja errado, mas
porque o botão verde esconde exatamente a parte que você precisa entender
agora.
:::

Os erros do compilador aparecem no livro inteiros, como você vai vê-los na
tela. Eles não são castigo: são a revisão gratuita de um colega que leu o
seu código antes de rodar.

## O que você precisa

Um JDK 21 ou mais novo, um editor de texto e um terminal. Mais nada.

```bash title="Confirme que está tudo no lugar"
java -version
javac -version
```

Se os dois comandos respondem com um número de versão, você está pronto.
Se não respondem, instale o JDK antes de virar a página — o resto do livro
supõe que eles funcionam.

:::warning
`java -version` respondendo e `javac -version` não respondendo é o sintoma
clássico de ter instalado um JRE em vez de um JDK. O JRE só executa; o JDK
compila, e é dele que você precisa.
:::

## Convenções

Trechos como `System.out.println` aparecem na fonte de código quando citados
no meio da frase. Blocos maiores vêm com o nome do arquivo no alto — esse
nome importa em Java mais do que em quase qualquer outra linguagem, e o
capítulo 1 explica por quê.
