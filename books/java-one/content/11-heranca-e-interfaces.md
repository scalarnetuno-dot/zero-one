---
title: "Herança e interfaces"
number: 11
part: p2
kicker: "Herança é um parentesco que você não pode desfazer. Interface é um contrato que você pode assinar com quem quiser."
goal: >-
  Escrever uma hierarquia com `extends`, declarar e implementar uma
  `interface`, usar polimorfismo e decidir entre herança e composição.
---

Duas classes parecidas pedem alguma forma de reaproveitamento. Java oferece
duas, e escolher errado é o erro de projeto mais caro que existe — porque ele
só aparece dois anos depois, quando o requisito muda.

## Herança: `extends`

```java title="Uma família de produtos" numbered
public class Product {
    protected String nome;
    protected double preco;

    public Product(String nome, double preco) {
        this.nome = nome;
        this.preco = preco;
    }

    public double precoFinal() {
        return preco;
    }
}

public class DigitalProduct extends Product {
    public DigitalProduct(String nome, double preco) {
        super(nome, preco);
    }

    @Override
    public double precoFinal() {
        return preco * 0.9;   // isento de frete, 10% menor
    }
}
```

:::anatomy title="Os quatro sinais de herança"
lang: java
code: |
  public class DigitalProduct extends Product {
      public DigitalProduct(String n, double p) {
          super(n, p);
      }

      @Override
      public double precoFinal() {
          return preco * 0.9;
      }
  }
notes:
  - { line: 1, text: "`extends` cria o parentesco: DigitalProduct **é um** Product." }
  - { line: 3, text: "`super(...)` chama o construtor do pai. Tem de ser a primeira linha." }
  - { line: 6, text: "`@Override` avisa o compilador: estou substituindo um método herdado." }
  - { line: 8, text: "`preco` é acessível porque o pai o declarou `protected`, não `private`." }
:::

## Polimorfismo: o mesmo comando, respostas diferentes

```java title="A lista não sabe qual é qual — e não precisa saber" numbered
List<Product> catalogo = List.of(
        new Product("Teclado", 100),
        new DigitalProduct("E-book", 100));

for (Product p : catalogo) {
    System.out.println(p.precoFinal());
}
```

```text title="Saída"
100.0
90.0
```

A variável é do tipo `Product`, mas o método que roda é o do objeto real.
Isso se chama **polimorfismo** e é a razão de ser da herança: você escreve o
laço uma vez e ele funciona para tipos que ainda não existem.

:::trivia
Essa escolha "em tempo de execução" tem nome: *dynamic dispatch*. Em Java ela
é o padrão para todo método de instância — e custa uma consulta a uma tabela
de ponteiros por chamada. A JVM otimiza isso de forma agressiva: quando
percebe que só um tipo aparece ali, ela substitui a chamada pelo código
direto. É por isso que Java "esquenta": as primeiras mil execuções são mais
lentas que as seguintes.
:::

:::story A herança que ninguém pediu
No segundo mês, Carlos herdou o sistema antigo de estoque.

Tecnicamente, não era herança. Era uma maldição familiar.

O autor original tinha saído da empresa em 2019 e deixado uma hierarquia de
seis níveis. A quinta classe se chamava
`ItemFisicoEstocavelPerecivelImportado`. A sexta se chamava `ItemLegado`, o
que já era um bom aviso.

A última classe existia porque, em algum ponto, alguém precisou de um item
importado que **não** fosse perecível — e a hierarquia não permitia. A
solução foi criar um filho que sobrescrevia o método do avô para desfazer o
que o pai fazia.

— Por que ninguém reescreveu isso? — perguntou Carlos.

— Porque funciona — disse Marina. — E porque ninguém sabe qual das seis
classes o financeiro usa.
:::

:::art caption="Herança profunda é um parentesco que você não pode desfazer."
src="heranca-profunda-e-um-parentesco-que-voce-nao-pode-desfazer.png"
Charge editorial minimalista: desenvolvedor jovem recebendo das mãos de outro
desenvolvedor uma caixa de papelão enorme e pesada, rotulada "SISTEMA
LEGADO". Da caixa saltam fios emaranhados, papéis amarelados e um monitor de
tubo antigo. Quem entrega já está de mochila nas costas, indo embora. Quem
recebe tem os joelhos dobrando sob o peso. Fundo branco, poucos elementos,
humor visual seco, estética de revista de tecnologia, sem estética infantil.
:::

## Interface: o contrato sem implementação

```java title="Um contrato" numbered
public interface Discountable {
    double aplicarDesconto(double percentual);
}

public class Product implements Discountable {
    @Override
    public double aplicarDesconto(double percentual) {
        return preco * (1 - percentual / 100);
    }
}
```

A interface diz **o que** precisa existir, não **como**. Uma classe pode
implementar quantas interfaces quiser — e só pode estender uma classe. Essa
assimetria é deliberada: contrato acumula, parentesco não.

| | Herança (`extends`) | Interface (`implements`) |
|---|---|---|
| Relação | "é um" | "sabe fazer" |
| Quantidade | uma classe pai | quantas quiser |
| Traz código? | sim, atributos e métodos | só assinatura (e `default`) |
| Acoplamento | alto | baixo |

Tabela: A escolha entre as duas é a decisão de projeto mais consequente da
Parte 2.

## Por que interface é a base do Spring

Guarde esta ideia, porque a Parte 3 inteira se apoia nela: se o seu código
depende de uma **interface**, alguém pode entregar qualquer implementação em
tempo de execução — inclusive uma falsa, no teste.

```java title="Dependa do contrato" numbered
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }
}
```

`ProductRepository` vai ser uma interface. Em produção, o Spring entrega uma
implementação que fala com o PostgreSQL (capítulo 21). No teste, você entrega
uma que guarda tudo em um `Map` (capítulo 35). O `ProductService` não muda uma
linha — e essa é a definição prática de *baixo acoplamento*.

## Métodos `default`: interface com implementação

```java title="Java 8 mudou a regra" numbered
public interface Discountable {
    double getPreco();

    default double comDesconto(double percentual) {
        return getPreco() * (1 - percentual / 100);
    }
}
```

Um método `default` traz corpo dentro da interface. Ele existe para permitir
que bibliotecas cresçam sem quebrar quem já as implementava — quando o Java 8
acrescentou `forEach` à interface `Iterable`, um bilhão de linhas de código
existente continuou compilando.

## Classe abstrata: o meio do caminho

```java title="Não pode existir sozinha" numbered
public abstract class Product {
    protected double preco;

    public abstract double precoFinal();  // o filho decide

    public String etiqueta() {            // todos herdam
        return "R$ " + precoFinal();
    }
}
```

`new Product(...)` não compila: uma classe abstrata é um esqueleto. Use quando
os filhos compartilham **estado e comportamento** e você quer obrigar cada um
a decidir um detalhe.

:::pitfall
A tentação de criar hierarquias fundas é grande e o arrependimento é certo.
Se você se vê escrevendo `class A extends B extends C extends D`, cada
alteração em `D` passa a assustar quatro classes. A regra prática do mercado é
direta: **prefira composição a herança.**
:::

## Composição: quando "tem um" vence "é um"

:::compare left="Herança forçada" right="Composição"
class ProductWithTax
        extends Product {
  double precoFinal() {
    return preco * 1.08;
  }
}
---
class Product {
  private TaxPolicy tax;

  double precoFinal() {
    return tax.apply(preco);
  }
}
:::

Na direita, a política de imposto é um objeto que você troca em tempo de
execução — inclusive por uma diferente por estado, ou por uma falsa no teste.
Na esquerda, você precisaria de uma subclasse nova para cada regra, e nenhuma
delas poderia se combinar com outra.

:::key
Pergunte: *"isto é um tipo diferente, ou é o mesmo tipo com uma peça
diferente?"* Tipo diferente pede herança (raramente). Peça diferente pede
composição (quase sempre).
:::

## `final`: proibir a herança

```java
public final class Money { }   // ninguém estende
```

`final` em uma classe impede subclasses; em um método, impede sobrescrita. É
uma decisão de projeto legítima: `String` é `final` em Java exatamente para
que ninguém possa criar um texto que se comporte de forma estranha.

:::summary
- `extends` cria "é um"; `implements` cria "sabe fazer".
- Polimorfismo escolhe o método pelo objeto real, não pela variável.
- Uma classe estende uma; implementa quantas quiser.
- Depender de interface é o que permite trocar a implementação — e o que o
  Spring explora.
- Prefira composição a herança.
:::

:::checkpoint
Você escreve uma subclasse com `super` e `@Override`, declara e implementa
interfaces, explica polimorfismo com um exemplo e sabe justificar composição
em vez de herança.
:::

:::milestone
O projeto tem a forma que vai receber o Spring: `ProductService` depende da
interface `ProductRepository`, não de uma classe concreta. Falta só alguém
para entregar a implementação — e é isso que o capítulo 15 apresenta.
:::

:::exercise level=1
Crie `abstract class Payment` com `abstract double taxa()` e duas subclasses:
`PixPayment` (taxa 0) e `CardPayment` (taxa 2,99%). Imprima a taxa das duas
por uma `List<Payment>`.

:::answer
```java
public abstract class Payment {
    public abstract double taxa();
}

public class PixPayment extends Payment {
    public double taxa() { return 0; }
}

public class CardPayment extends Payment {
    public double taxa() { return 0.0299; }
}
```
:::

:::exercise level=2
Transforme `Payment` em interface e explique o que você perdeu e o que ganhou
na troca.

:::answer
Perdeu a possibilidade de guardar estado comum (um atributo `descricao`, por
exemplo) e de ter código compartilhado sem `default`. Ganhou a liberdade de
uma classe implementar `Payment` **e** outra interface qualquer — e a
possibilidade de a implementação ser uma classe que já herda de outra coisa.
:::

:::exercise level=3
Reescreva o exercício anterior com composição: uma classe `Payment` concreta
que recebe uma `FeePolicy` no construtor. Depois responda: qual das três
versões você levaria para uma API que ganha um meio de pagamento novo por
mês?

:::answer
A terceira. Um meio de pagamento novo passa a ser um objeto de política,
criado em tempo de execução — pode até vir de uma tabela do banco, sem
recompilar nada. Herança exigiria uma classe nova e um novo *deploy* a cada
mês.
:::
