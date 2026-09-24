---
title: "Orientação a objetos"
number: 9
part: p2
kicker: "Até aqui o código tinha verbos soltos. Agora ele ganha substantivos."
epigraph: "Eu inventei o termo orientação a objetos, e posso dizer que não tinha C++ em mente."
epigraph_by: "Alan Kay, criador do Smalltalk"
goal: >-
  Escrever uma classe com atributos, construtor e métodos, criar objetos a
  partir dela e explicar a diferença entre classe e instância.
---

Um programa cresce e a pergunta muda. Deixa de ser "que conta eu faço" e
passa a ser "de quem é essa informação". Uma classe responde à segunda: ela
junta os dados que andam juntos e os métodos que sabem o que fazer com eles.

## Do dado solto ao objeto

:::compare left="Antes: quatro variáveis paralelas" right="Depois: um objeto"
String nome = "Teclado";
double preco = 349.90;
int estoque = 12;
boolean ativo = true;
---
Product p = new Product(
    "Teclado", 349.90, 12);
p.getPreco();
p.podeVender();
:::

A versão da esquerda funciona com um produto. Com dois, você duplica as
quatro variáveis; com mil, precisa de quatro arrays paralelos e de reza para
que os índices não desalinhem. A da direita escala sem esforço — é para isso
que a classe existe.

## A primeira classe

```java title="Product.java" numbered
public class Product {
    String nome;
    double preco;
    int estoque;

    Product(String nome, double preco, int estoque) {
        this.nome = nome;
        this.preco = preco;
        this.estoque = estoque;
    }

    boolean podeVender() {
        return estoque > 0;
    }

    double totalEmEstoque() {
        return preco * estoque;
    }
}
```

:::anatomy title="As quatro partes de uma classe"
lang: java
code: |
  public class Product {
      String nome;

      Product(String nome) {
          this.nome = nome;
      }

      boolean podeVender() {
          return estoque > 0;
      }
  }
notes:
  - { line: 1, text: "A **classe** é a planta: descreve o que todo produto tem e faz." }
  - { line: 2, text: "**Atributo** (ou campo): o dado que cada objeto carrega, um valor por objeto." }
  - { line: 4, text: "**Construtor**: mesmo nome da classe, sem tipo de retorno. Roda uma vez, no nascimento." }
  - { line: 5, text: "`this.nome` é o atributo; `nome` sozinho é o parâmetro. `this` desfaz a ambiguidade." }
  - { line: 8, text: "**Método de instância**: sem `static`, ele enxerga os atributos do objeto." }
:::

## Classe e instância não são a mesma coisa

```java title="Uma planta, três casas" numbered
Product teclado = new Product("Teclado", 349.90, 12);
Product mouse   = new Product("Mouse", 89.90, 0);

System.out.println(teclado.podeVender());   // true
System.out.println(mouse.podeVender());     // false
```

A classe é uma; os objetos são muitos. Cada `new` reserva um espaço novo na
memória com uma cópia dos atributos — e é por isso que `teclado.estoque` e
`mouse.estoque` são valores independentes.

:::diagram type="blocks" caption="Uma classe, dois objetos: mesma estrutura, valores próprios."
flow: false
rows:
  - [{ text: "class Product", note: "nome · preco · estoque · podeVender()" }]
  - [{ text: "teclado", note: "Teclado · 349.90 · 12" }, { text: "mouse", note: "Mouse · 89.90 · 0" }]
:::

:::story Os quatro arrays paralelos
Antes de existir a classe `Product`, existiam quatro arrays.

`nomes`, `precos`, `estoques` e `ativos`. Tudo funcionava desde que a posição
3 de um correspondesse à posição 3 dos outros três.

Na terça, Cláudia pediu para remover um produto descontinuado. Carlos removeu
do array de nomes e esqueceu dos outros três.

Naquela tarde, a loja passou a vender um teclado com o preço de um cabo HDMI.

Seu Antônio comprou quatro.
:::

## `static` finalmente explicado

Agora a palavra do capítulo 2 faz sentido. Um membro `static` pertence à
**classe**; um membro sem `static` pertence ao **objeto**.

```java title="Contador de produtos criados" numbered
public class Product {
    static int criados = 0;     // um só, compartilhado
    String nome;                // um por objeto

    Product(String nome) {
        this.nome = nome;
        criados++;
    }
}
```

```java
new Product("Teclado");
new Product("Mouse");
System.out.println(Product.criados);   // 2 — acessado pela classe
```

E é por isso que `main` é `static`: quando o programa começa, ainda não existe
objeto nenhum para chamar um método.

:::pitfall
Um método `static` não pode acessar atributo de instância — não há instância.
A mensagem é `non-static variable nome cannot be referenced from a static
context`, e ela confunde todo mundo na primeira semana. A tradução é: "você
pediu o nome de um produto sem dizer de qual produto".
:::

## `toString`: o objeto se apresentando

```java title="Sem toString" 
System.out.println(teclado);
// Product@2f92e0f4
```

Aquele lixo é o nome da classe e o endereço em memória. Sobrescreva
`toString` e o objeto passa a saber se descrever:

```java title="Product.java (trecho)" numbered
@Override
public String toString() {
    return nome + " (R$ " + preco + ", " + estoque + " un)";
}
```

```text title="Saída"
Teclado (R$ 349.9, 12 un)
```

`@Override` é uma **anotação**: um aviso ao compilador de que você está
substituindo um método que já existe. Se você errar o nome (`toStrring`), o
compilador reclama em vez de deixar o método órfão. Guarde a ideia de
anotação: a partir do capítulo 17 ela vira a principal forma de conversar com
o Spring.

:::history
Todo objeto em Java herda de uma classe chamada `Object`, que oferece
`toString`, `equals` e `hashCode`. Essa decisão é de 1995 e tem custo: até os
tipos mais simples arrastam três métodos que quase nunca fazem o certo por
padrão. Foi para corrigir isso que o Java 16 trouxe `record`, que você vê no
capítulo 12 — e que gera os três de graça, corretamente.
:::

## `equals` e `hashCode`: a lição do capítulo 4, agora do seu lado

Dois produtos com o mesmo nome e o mesmo preço são o mesmo produto? O `==`
diz não, porque são dois objetos. Se você quer que sejam iguais, precisa
dizer como:

```java title="Igualdade por conteúdo" numbered
@Override
public boolean equals(Object o) {
    if (this == o) return true;
    if (!(o instanceof Product outro)) return false;
    return nome.equals(outro.nome) && preco == outro.preco;
}

@Override
public int hashCode() {
    return Objects.hash(nome, preco);
}
```

A regra que existe há trinta anos: **se você sobrescreve `equals`, sobrescreva
`hashCode`**. `HashMap` e `HashSet` usam o segundo para achar o objeto antes de
comparar com o primeiro; um sem o outro produz o bug mais difícil de
explicar — um item que você acabou de guardar no `Set` e que ele diz não
conter.

:::tip
Ninguém escreve esses dois métodos à mão em 2026. A IDE gera, e o `record` do
capítulo 12 dispensa. O que você precisa é reconhecer o par e saber por que
ele existe.
:::

:::term Classe
A descrição de um tipo: quais dados ele carrega e quais operações aceita.
:::

:::term Objeto (ou instância)
Um exemplar concreto de uma classe, com seus próprios valores, criado com
`new`.
:::

:::summary
- Classe junta os dados que andam juntos e os métodos que os operam.
- O construtor roda uma vez, no `new`, e `this` distingue atributo de
  parâmetro.
- `static` pertence à classe; sem `static` pertence ao objeto.
- `toString` faz o objeto se descrever; `equals` e `hashCode` andam em par.
:::

:::checkpoint
Você escreve uma classe com atributos, construtor e métodos, cria objetos,
explica `static` e sabe por que `equals` e `hashCode` vêm juntos.
:::

:::milestone
Nasceu a classe `Product` — o coração do projeto. Os atributos são os mesmos
que vão virar colunas de tabela no capítulo 19 e campos JSON no capítulo 24.
:::

:::exercise level=1
Escreva a classe `Category` com `nome` e `descricao`, um construtor e
`toString`. Crie duas categorias e imprima-as.

:::answer
```java
public class Category {
    String nome;
    String descricao;

    Category(String nome, String descricao) {
        this.nome = nome;
        this.descricao = descricao;
    }

    @Override
    public String toString() {
        return nome + " — " + descricao;
    }
}
```
:::

:::exercise level=2
Acrescente a `Product` um método `aplicarDesconto(double percentual)` que
altere o preço do próprio objeto e devolva `void`. Depois escreva
`comDesconto(double percentual)` que devolva um **novo** `Product` sem
alterar o original. Qual das duas versões você preferiria em uma API?

:::answer
A segunda. Um método que altera o objeto por dentro (*mutação*) força quem
chama a lembrar que o valor anterior foi perdido; o que devolve um objeto
novo pode ser usado em qualquer ordem e é seguro em código concorrente. O
capítulo 12 leva essa ideia ao limite com `record`, que é imutável por
construção.
:::

:::exercise level=3
Crie uma `List<Product>` com quatro produtos e calcule o valor total do
estoque somando `totalEmEstoque()` de cada um.

:::answer
```java
double total = 0;
for (Product p : produtos) {
    total += p.totalEmEstoque();
}
```
No capítulo 14 isso vira
`produtos.stream().mapToDouble(Product::totalEmEstoque).sum()`. Guarde as
duas versões lado a lado: a segunda só parece mágica para quem não escreveu a
primeira.
:::
