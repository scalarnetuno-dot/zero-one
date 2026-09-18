---
title: "Métodos"
number: 7
part: p2
kicker: "Dar nome a um trecho de código é a forma mais barata de documentação que existe."
goal: >-
  Extrair um método com parâmetros e retorno, entender o que é escopo e
  reconhecer quando uma sobrecarga ajuda e quando ela confunde.
---

Até aqui todo o código morou dentro do `main`. Funciona para vinte linhas e
vira um pesadelo em duzentas. Um método é um trecho de código com nome,
entrada e saída — e o nome é a parte mais importante.

## Da repetição ao método

:::compare left="Antes: a conta espalhada" right="Depois: a conta com nome"
double t1 = p1 * 1.08;
double t2 = p2 * 1.08;
double t3 = p3 * 1.08;
---
double t1 = comImposto(p1);
double t2 = comImposto(p2);
double t3 = comImposto(p3);
:::

A versão da direita tem duas vantagens que não são estéticas. Se a alíquota
mudar, você altera um lugar. E quem lê `comImposto(p1)` entende a intenção
sem reconstruir a multiplicação.

```java title="O método" numbered
static double comImposto(double valor) {
    return valor * 1.08;
}
```

:::anatomy title="Cada parte da declaração de um método"
lang: java
code: |
  static double comImposto(double valor) {
      return valor * 1.08;
  }
notes:
  - { line: 1, text: "`static` porque ainda estamos chamando do `main`, sem objeto. No capítulo 9 isso muda." }
  - { line: 1, text: "`double` é o **tipo de retorno**: a espécie do valor que sai." }
  - { line: 1, text: "`comImposto` é o nome. Verbo ou substantivo, sempre em camelCase." }
  - { line: 1, text: "`double valor` é o **parâmetro**: o nome que o valor recebe aqui dentro." }
  - { line: 2, text: "`return` devolve e encerra o método na mesma instrução." }
:::

## `void` e `return`

Um método que não devolve nada declara `void`. Nele, `return` sem valor serve
para sair mais cedo:

```java title="Sair antes vale para método também" numbered
static void imprimirEtiqueta(String nome, double preco) {
    if (nome == null || nome.isBlank()) {
        return;                     // nada a imprimir
    }
    System.out.println(nome + " — R$ " + preco);
}
```

:::key
Um método com mais de um `return` não é problema; um método com mais de um
*motivo para existir* é. Se você precisa de "e" para explicar o que ele faz
("valida **e** salva **e** notifica"), ele é três métodos.
:::

:::story A alíquota que morava em nove lugares
O imposto mudou de 8% para 8,5%. Uma linha, disse Roberto. Cinco minutos.

Carlos abriu o projeto e usou a busca: `1.08`. Nove resultados.

Trocou os nove. Rodou. Funcionou.

Na quarta-feira, Cláudia avisou que o relatório de fechamento continuava com
o valor antigo. Carlos buscou de novo, agora por `* 1.0`: apareceu um décimo
lugar, escrito como `0.08 + 1`, que a busca anterior não pegava.

Marina apareceu com a caneca e fez a pergunta que não era sobre imposto:

— Quantas vezes essa conta precisa existir?

— Uma.

— E existe quantas?

— Dez. — Carlos pensou um pouco. — Dez que eu achei.
:::

:::art caption="Uma regra que mora em dez lugares muda em nove."
src="uma-regra-que-mora-em-dez-lugares-muda-em-nove.png"
Charge editorial minimalista: desenvolvedor jovem diante de um monitor com
dez janelas de busca abertas, todas mostrando a mesma linha de código
repetida. Ao lado, uma desenvolvedora sênior aponta com o dedo para uma única
caixa desenhada com o rótulo "comImposto()", enquanto as dez janelas se
dissolvem em setas convergindo para essa caixa. Fundo branco, poucos
elementos, composição limpa, humor sutil, estética editorial de tecnologia.
:::

## Escopo: onde um nome existe

```java title="Cada chave abre um mundo" numbered
static void exemplo() {
    int a = 1;
    if (a == 1) {
        int b = 2;
        System.out.println(a + b);   // ok: a e b existem
    }
    // System.out.println(b);        // erro: b morreu na chave
}
```

A regra é simples: um nome existe da declaração até a chave que a fecha. O
compilador não deixa você usar o que não existe mais — e também não deixa
declarar duas variáveis com o mesmo nome no mesmo escopo.

:::pitfall
Parâmetro é uma **cópia**. Alterar `valor` dentro do método não altera a
variável de quem chamou. Para primitivos isso é sempre verdade; para objetos,
a cópia é da *referência* — você não pode trocar o objeto de quem chamou, mas
pode mudar o conteúdo dele. Essa distinção volta no capítulo 9 e explica
muitos bugs de lista compartilhada.
:::

## Sobrecarga: mesmo nome, assinaturas diferentes

```java title="Três formas de chamar a mesma ideia" numbered
static double total(double preco) {
    return total(preco, 1);
}

static double total(double preco, int quantidade) {
    return total(preco, quantidade, 0.08);
}

static double total(double preco, int quantidade, double taxa) {
    return preco * quantidade * (1 + taxa);
}
```

Java escolhe qual chamar pelo número e pelo tipo dos argumentos — a
**assinatura**. Repare no encadeamento: as duas primeiras versões só
preenchem valores padrão e delegam. É um padrão comum e saudável, porque a
regra vive em um lugar só.

:::pitfall
Sobrecarga que muda o *significado* confunde. `salvar(String)` gravando em
arquivo e `salvar(int)` gravando no banco é uma armadilha para quem lê. Nomes
diferentes custam três teclas e economizam uma hora.
:::

:::trivia
Java não tem parâmetros com valor padrão, como Python ou Kotlin. A
sobrecarga encadeada acima é o substituto idiomático — e o motivo pelo qual
bibliotecas Java antigas têm métodos com sete versões. A partir da Parte 3
você vai ver o Spring resolver isso de outro jeito: com objetos de
configuração.
:::

## Métodos que documentam regras

Este é o exercício de tradução que sustenta o resto do livro: **toda regra de
negócio cabe em um método com nome de regra**.

```java title="A regra tem nome" numbered
static boolean podeVender(int estoque, boolean ativo) {
    return ativo && estoque > 0;
}
```

No capítulo 22 essa mesma função vira um método de uma classe `ProductService`
e passa a ser chamada por um controlador HTTP. A forma muda; a ideia é a
mesma: a regra mora em um lugar, tem nome e pode ser testada sozinha — é
exatamente o que o capítulo 34 vai fazer com ela.

:::example Um programa inteiro, agora organizado
```java
public class Loja {
    public static void main(String[] args) {
        double[] precos = { 19.90, 4.50, 32.00 };
        System.out.println("Total: R$ " + somar(precos));
        System.out.println("Média: R$ " + media(precos));
    }

    static double somar(double[] valores) {
        double total = 0;
        for (double v : valores) {
            total += v;
        }
        return total;
    }

    static double media(double[] valores) {
        if (valores.length == 0) return 0;
        return somar(valores) / valores.length;
    }
}
```
`media` usa `somar` e trata o caso do array vazio. Sem aquele `return 0`, a
divisão por zero devolveria `NaN` — e `NaN` em um relatório é pior que um
erro, porque não chama atenção.
:::

:::summary
- Método é código com nome, parâmetros e tipo de retorno.
- `void` não devolve nada; `return` sozinho serve para sair mais cedo.
- Um nome existe até a chave que fecha o bloco dele.
- Sobrecarga é mesmo nome com assinaturas diferentes — use para valor padrão,
  não para mudar de significado.
- Regra de negócio com nome é regra testável.
:::

:::checkpoint
Você extrai um método a partir de código repetido, escolhe entre `void` e
retorno, sabe onde cada variável existe e usa sobrecarga sem confundir quem lê.
:::

:::milestone
As regras do projeto começam a ter nome: `podeVender`, `comImposto`. Ainda
são métodos estáticos em uma classe solta — no capítulo 9 eles ganham um
dono.
:::

:::exercise level=1
Extraia um método `maiorPreco(double[] precos)` do exercício do capítulo 6 e
chame-o do `main`.

:::answer
```java
static double maiorPreco(double[] precos) {
    double maior = precos[0];
    for (double p : precos) {
        if (p > maior) {
            maior = p;
        }
    }
    return maior;
}
```
:::

:::exercise level=2
Escreva `aplicarDesconto(double preco, double percentual)` que recuse
percentuais fora de 0 a 100 devolvendo o preço original. Depois escreva a
sobrecarga `aplicarDesconto(double preco)` com 10% de desconto.

:::answer
```java
static double aplicarDesconto(double preco) {
    return aplicarDesconto(preco, 10);
}

static double aplicarDesconto(double preco, double percentual) {
    if (percentual < 0 || percentual > 100) {
        return preco;
    }
    return preco * (1 - percentual / 100);
}
```
Devolver o preço original em caso inválido é uma decisão discutível — ela
esconde o erro. No capítulo 13 você vai aprender a alternativa honesta:
lançar uma exceção.
:::

:::exercise level=3
Escreva `static String etiqueta(String nome, double preco, int quantidade)`
que devolva `"Teclado · R$ 349,90 · 12 un"`. Use `String.format` e descubra
sozinho como trocar o ponto pela vírgula decimal.

:::answer
```java
static String etiqueta(String nome, double preco, int quantidade) {
    return String.format("%s · R$ %.2f · %d un",
            nome, preco, quantidade);
}
```
A vírgula depende do *locale* da máquina: `String.format` usa o padrão do
sistema, então em português já sai `349,90`. Para garantir,
`String.format(Locale.of("pt", "BR"), ...)`. Formatação dependente de
ambiente é uma das fontes mais irritantes de "funciona na minha máquina".
:::
