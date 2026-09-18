---
title: "A porta"
number: 1
kicker: "Para que Java existe — e o primeiro programa que faz um trabalho de verdade."
---

Toda linguagem começa com uma promessa. A de Java foi escrita em 1995 e cabe
em cinco palavras: *escreva uma vez, rode em qualquer lugar*. Trinta anos
depois, a promessa continua de pé — e é ela que explica por que existe uma
etapa a mais entre o seu arquivo de texto e o programa rodando.

## Dois comandos, não um

Em Python você escreve e roda. Em Java você escreve, **compila** e roda. A
compilação não é burocracia: é onde alguém lê o seu código antes de você.

:::diagram type="flowchart" caption="Do texto ao programa: o compilador entra no meio de propósito."
nodes:
  - { id: src,  type: io,       text: "App.java" }
  - { id: cc,   type: process,  text: "javac App.java" }
  - { id: cls,  type: io,       text: "App.class (bytecode)" }
  - { id: jvm,  type: process,  text: "java App" }
  - { id: out,  type: start,    text: "Saída no terminal" }
edges:
  - { from: src, to: cc }
  - { from: cc,  to: cls,  label: "sem erros" }
  - { from: cls, to: jvm }
  - { from: jvm, to: out }
:::

O arquivo `.class` não é código de máquina: é *bytecode*, um formato
intermediário que qualquer JVM sabe executar. É por isso que o mesmo
`.class` roda no seu Windows e no servidor Linux sem recompilar.

## O primeiro arquivo

Crie um arquivo chamado `App.java`. O nome não é decoração: uma classe
pública precisa morar num arquivo com o mesmo nome dela.

```java title="App.java" numbered
public class App {
    public static void main(String[] args) {
        System.out.println("O primeiro programa");
    }
}
```

Compile e rode:

```bash
javac App.java
java App
```

O primeiro comando cria `App.class` na mesma pasta. O segundo entrega esse
arquivo à máquina virtual, que procura um método chamado `main` e começa
por ele.

:::note Por que `main` tem essa assinatura enorme
`public` para a JVM enxergar, `static` para rodar sem que exista um objeto,
`void` porque não devolve nada, e `String[] args` para receber o que você
digitar depois do nome do programa. Cada palavra está resolvendo um problema
concreto — e você vai reencontrar todas elas nos próximos capítulos.
:::

## Um programa que faz um trabalho

"Olá, mundo" não prova nada. O menor programa honesto é aquele que recebe
dados, calcula e responde. Este soma uma lista de preços e mostra o total:

```java title="Total.java" numbered
public class Total {
    public static void main(String[] args) {
        double[] precos = { 19.90, 4.50, 32.00 };
        double total = 0;

        for (double preco : precos) {
            total = total + preco;
        }

        System.out.println("Total: R$ " + total);
    }
}
```

```text title="Saída"
Total: R$ 56.4
```

Seis linhas de lógica e três conceitos que ocupam os próximos três
capítulos: valor com tipo (`double`), repetição (`for`) e acumulação
(`total = total + preco`).

:::tip Leia a saída com desconfiança
`56.4` e não `56.40`. Java imprimiu o número, não o dinheiro. Formatar
moeda é outro assunto — e o capítulo 6 mostra por que misturar os dois cedo
demais estraga o cálculo.
:::

## Quando o compilador reclama

Apague o ponto e vírgula da linha 4 e compile de novo. A resposta é esta:

```text title="Terminal"
Total.java:4: error: ';' expected
        double total = 0
                        ^
1 error
```

Três informações em quatro linhas: o arquivo e a linha, o que faltou, e
uma seta apontando o lugar exato. Um erro de compilação custa dez segundos.
O mesmo defeito numa linguagem sem essa etapa custaria uma execução
quebrada na frente de um usuário.

:::practice
Estrague o programa de propósito três vezes: troque `double` por `dooble`,
apague uma chave `}` e escreva `Systemout.println`. Leia as três mensagens
com calma antes de consertar. Você está aprendendo a língua do compilador,
e ela tem menos palavras do que parece.
:::

![Composição de exemplo](exemplo-1.png "Arte provisória: o lugar da ilustração do capítulo.")

## O que a JVM faz por você

| Etapa | Quem faz | O que acontece se der errado |
|---|---|---|
| Compilar | `javac` | Erro de compilação: nada roda |
| Carregar | JVM | `ClassNotFoundException` |
| Executar | JVM | Exceção em tempo de execução |
| Otimizar | JIT | Nada: o programa só fica mais rápido |

Table: As quatro etapas entre o seu texto e o processador.

O compilador pega os erros de escrita. A JVM pega os erros de montagem.
Sobram para você os erros de raciocínio — e é neles que este livro insiste.

:::summary
- Java compila antes de rodar: `javac` produz bytecode, `java` executa.
- Uma classe pública mora num arquivo com o mesmo nome.
- `main` é onde a JVM começa, e a assinatura dele explica quatro conceitos.
- O erro de compilação é a revisão mais barata que existe: leia, não feche.
:::

:::exercise level=1
Escreva um `Recibo.java` que declare três preços, some os três e imprima o
total junto de uma linha com o nome da loja.

:::answer
A soma é a mesma do `Total.java`; a diferença é a segunda impressão, que
pode vir antes do cálculo.

```java title="Recibo.java"
public class Recibo {
    public static void main(String[] args) {
        System.out.println("Padaria do Zé");
        double[] precos = { 7.50, 12.00, 3.25 };
        double total = 0;
        for (double preco : precos) {
            total = total + preco;
        }
        System.out.println("Total: R$ " + total);
    }
}
```
:::

:::exercise level=2
Compile um arquivo cujo nome do arquivo e nome da classe sejam diferentes
de propósito. Leia a mensagem e explique em uma frase o que o compilador
está protegendo.

:::answer
A mensagem é `class Recibo is public, should be declared in a file named
Recibo.java`. O compilador está garantindo que qualquer pessoa — e qualquer
ferramenta — consiga encontrar uma classe pública só pelo nome do arquivo,
sem abrir a pasta inteira.
:::
