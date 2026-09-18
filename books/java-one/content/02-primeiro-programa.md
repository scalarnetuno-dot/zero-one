---
title: "Primeiro programa em Java"
number: 2
part: p1
kicker: "Dois comandos, um arquivo e a linha mais famosa da programação."
goal: >-
  Escrever, compilar e executar um programa Java pelo terminal, explicar
  cada palavra da assinatura do `main` e ler uma mensagem de erro do
  compilador sem entrar em pânico.
---

Em Python você escreve e roda. Em Java você escreve, **compila** e roda. Essa
etapa extra é a primeira coisa que assusta quem vem de outra linguagem, e é
também a que devolve mais valor: a compilação é onde alguém lê o seu código
antes de você.

:::diagram type="flowchart" caption="Do texto ao programa: o compilador entra no meio de propósito."
nodes:
  - { id: src, type: io,      text: "App.java" }
  - { id: cc,  type: process, text: "javac App.java" }
  - { id: cls, type: io,      text: "App.class (bytecode)" }
  - { id: jvm, type: process, text: "java App" }
  - { id: out, type: start,   text: "Saída no terminal" }
edges:
  - { from: src, to: cc }
  - { from: cc,  to: cls, label: "sem erros" }
  - { from: cls, to: jvm }
  - { from: jvm, to: out }
:::

O arquivo `.class` não é código de máquina: é **bytecode**, um formato
intermediário que qualquer JVM sabe executar. É por isso que o mesmo arquivo
compilado roda no seu Windows e no servidor Linux sem recompilar — a promessa
de 1995 que ainda se cumpre.

## O arquivo

Crie um arquivo chamado `App.java`. O nome não é decoração: uma classe
pública precisa morar em um arquivo com o mesmo nome dela.

```java title="App.java" numbered
public class App {
    public static void main(String[] args) {
        System.out.println("O primeiro programa");
    }
}
```

Compile e execute:

```bash
javac App.java
java App
```

O primeiro comando cria `App.class` na mesma pasta. O segundo entrega esse
arquivo à máquina virtual, que procura um método chamado `main` e começa por
ele. Repare que `java App` não tem extensão: você não está executando um
arquivo, está pedindo a uma classe que comece.

## A assinatura mais copiada da história

Cinco palavras antes do nome do método, e cada uma resolve um problema
concreto. Vale gastar uma página nisso porque você vai escrever essa linha
até o fim da vida.

:::anatomy title="A assinatura do main, palavra por palavra"
lang: java
code: |
  public class App {
      public static void main(String[] args) {
          System.out.println("O primeiro programa");
      }
  }
notes:
  - { line: 1, text: "`public class App` — a classe é o invólucro; em Java nada vive fora de uma." }
  - { line: 2, text: "`public` deixa a JVM enxergar o método de fora do arquivo." }
  - { line: 2, text: "`static` permite chamá-lo sem criar um objeto — no início do programa não existe nenhum." }
  - { line: 2, text: "`void` porque ele não devolve nada a quem chamou." }
  - { line: 2, text: "`String[] args` recebe o que você digitou depois do nome do programa." }
  - { line: 3, text: "`System.out` é a saída padrão; `println` escreve e pula a linha." }
:::

:::trivia
`System.out.println` tem 18 caracteres para fazer o que Python faz com 5.
A razão é consistência: `System` é uma classe, `out` é um campo dela e
`println` é um método desse campo. Java preferiu não abrir exceção na
gramática nem para a linha mais escrita do mundo. Em 2023, trinta anos
depois, a linguagem finalmente ganhou `println` solto em classes implícitas
— e a comunidade ainda discute se foi uma boa ideia.
:::

:::story Já está em produção?
Carlos rodou `javac App.java`. Esperou. Nada aconteceu.

Ficou olhando para o terminal por uns dez segundos, convencido de que tinha
travado. Digitou `java App`. E então, na tela preta, apareceu:

```text
O primeiro programa
```

Ele girou na cadeira e anunciou, alto demais para um escritório aberto:

— COMPILOU!

Roberto, que passava com um café na mão, parou.

— Compilou? Então já está em produção?

— Não. Ele imprime uma frase.

— Uma frase para o cliente?

— Uma frase para mim.

Roberto assentiu devagar, do jeito de quem não entendeu mas vai repetir a
informação na próxima reunião como se tivesse entendido.
:::

:::art caption="O silêncio do javac é a coisa mais parecida com um elogio que um compilador oferece."
src="o-silencio-do-javac-e-a-coisa-mais-parecida-com-um-elogio-que-um-compilador-oferece.png"
Ilustração editorial minimalista: desenvolvedor jovem girando na cadeira com
os braços erguidos em comemoração exagerada diante de um monitor onde se lê
apenas uma linha de texto minúscula. Atrás dele, um gerente de camisa social
parado com uma xícara de café, sobrancelha erguida, expressão de dúvida
educada. Escritório open space desenhado com pouquíssimos elementos. Humor
seco, composição limpa, fundo branco, estética de revista de tecnologia.
:::

## Argumentos: o programa recebendo o mundo

`String[] args` não é enfeite. Troque o corpo do `main`:

```java title="Saudacao.java" numbered
public class Saudacao {
    public static void main(String[] args) {
        System.out.println("Olá, " + args[0]);
    }
}
```

```bash
javac Saudacao.java
java Saudacao Ana
```

```text title="Saída"
Olá, Ana
```

Você acabou de escrever um programa com entrada. É pouco, mas é a diferença
entre um exercício e uma ferramenta.

:::pitfall
Rode `java Saudacao` sem o nome. A resposta é
`ArrayIndexOutOfBoundsException: Index 0 out of bounds for length 0` — você
pediu o primeiro item de uma lista vazia. Guarde essa mensagem: ela vai
voltar no capítulo 6, e sempre diz exatamente qual índice você tentou usar.
:::

## Quando o compilador reclama

Apague o ponto e vírgula da linha 3 e compile de novo:

```text title="Terminal"
Saudacao.java:3: error: ';' expected
        System.out.println("Olá, " + args[0])
                                             ^
1 error
```

Quatro informações em três linhas: o arquivo, a linha, o que faltava e uma
seta apontando o lugar exato. Um erro de compilação custa dez segundos. O
mesmo defeito, em uma linguagem sem essa etapa, custaria uma execução
quebrada na frente de um usuário.

:::key
Leia a **primeira** mensagem, não a última. Um erro de sintaxe confunde o
compilador, que passa a reclamar de coisas certas logo abaixo. Conserte o
primeiro, compile de novo, e metade da lista desaparece.
:::

## Duas palavras que você vai ouvir muito

:::term JDK
*Java Development Kit*: o pacote que compila e executa. Traz o `javac`, o
`java`, o depurador e as bibliotecas.
:::

:::term JRE
*Java Runtime Environment*: só executa. Não tem `javac`. Foi distribuído
separadamente por anos e é a causa da metade das instalações frustradas de
quem começa.
:::

:::history
Até o Java 8, instalar Java no desktop instalava um JRE com um plugin de
navegador — a origem daquelas atualizações eternas do "Java Update". Os
applets morreram, o plugin foi removido no Java 11 e hoje a distribuição
padrão é um JDK. Se algum tutorial mandar você baixar "o JRE", ele é de
outra década.
:::

## E a IDE?

Nada até aqui exigiu uma. Isso é deliberado: o botão verde de uma IDE
esconde exatamente as duas etapas que você precisava ver. A partir do
capítulo 16, quando o projeto passa a ter dezenas de arquivos e
dependências, uma IDE deixa de ser conforto e passa a ser ferramenta — e o
livro vai usar uma.

:::tree title="Onde estamos agora"
java-one/
  App.java       # imprime uma linha
  App.class      # gerado pelo javac
  Saudacao.java  # recebe um argumento
:::

:::summary
- Java compila antes de rodar: `javac` produz bytecode, `java` executa.
- Uma classe pública mora em um arquivo com o mesmo nome dela.
- `main` é onde a JVM começa, e cada palavra da assinatura resolve um
  problema concreto.
- O erro de compilação é a revisão mais barata que existe. Leia a primeira
  mensagem.
:::

:::checkpoint
Você escreve, compila e executa um programa Java pelo terminal, sabe
explicar `public static void main(String[] args)` e sabe o que fazer quando
o `javac` reclama.
:::

:::milestone
O projeto tem uma classe que imprime e uma que recebe argumento. Nenhuma
das duas sobrevive ao capítulo 16 — mas o hábito de compilar antes de rodar
sobrevive ao livro.
:::

:::exercise level=1
Escreva um `Soma.java` que receba dois números como argumento e imprima a
soma. Dica: `Integer.parseInt(args[0])` transforma texto em número.

:::answer
```java
public class Soma {
    public static void main(String[] args) {
        int a = Integer.parseInt(args[0]);
        int b = Integer.parseInt(args[1]);
        System.out.println(a + b);
    }
}
```
Sem o `parseInt`, `args[0] + args[1]` concatena texto: `2` e `3` viram
`"23"`. É o primeiro encontro com uma ideia do próximo capítulo — o tipo
decide o que o `+` significa.
:::

:::exercise level=2
Estrague o programa de propósito três vezes: troque `String[]` por
`String`, apague uma chave `}` e escreva `Sistem.out.println`. Leia as três
mensagens antes de consertar.

:::answer
A primeira compila e falha ao rodar com `NoSuchMethodError: main` — a
assinatura tem de ser exata. A segunda dá `reached end of file while
parsing`. A terceira dá `cannot find symbol`, com uma seta apontando
`Sistem`. Três mensagens, três categorias: assinatura, sintaxe e nome.
:::
