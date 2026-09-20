---
title: "Spring Data JPA"
number: 20
part: p4
kicker: "Uma camada que traduz objeto em linha de tabela. Poderosa, conveniente e cheia de armadilhas que este livro vai nomear."
goal: >-
  Anotar uma classe como entidade, mapear campos e enum, entender o que é o
  Hibernate e o que é o JPA, e saber quando a tradução automática atrapalha.
---

Você tem uma classe Java e uma tabela SQL descrevendo a mesma coisa. Escrever
à mão a conversão entre as duas — `SELECT` em `Product`, `Product` em
`INSERT` — é trabalho repetitivo e mecânico. O JPA faz isso.

## Três nomes, três papéis

| Nome | O que é |
|---|---|
| **JPA** | a especificação: as anotações e o contrato |
| **Hibernate** | a implementação que executa (a padrão do Boot) |
| **Spring Data JPA** | a camada que dispensa escrever o repositório |

Tabela: Você programa contra o JPA, o Hibernate faz o trabalho, e o Spring
Data poupa o código repetitivo. Confundir os três é comum e atrapalha na hora
de procurar uma solução na internet.

:::trivia
Antes do JPA (2006), cada projeto escrevia sua própria camada de acesso a
dados, ou usava a API crua do JDBC — em que uma consulta de três colunas
ocupava vinte linhas com `ResultSet`, `try/finally` e conversão manual de
tipo. O Hibernate apareceu em 2001 como projeto independente, ficou tão
dominante que a especificação oficial foi escrita **depois**, em cima dele. É
um dos poucos casos em que o padrão seguiu a prática.
:::

## A entidade

```java title="Product.java" numbered
package com.loja.catalog.product;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;

@Entity
@Table(name = "product")
public class Product {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 120)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal price;

    @Column(nullable = false)
    private Integer quantity = 0;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Status status = Status.ATIVO;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt = Instant.now();

    protected Product() { }   // exigido pelo JPA

    public Product(String name, BigDecimal price, Integer quantity) {
        this.name = name;
        this.price = price;
        this.quantity = quantity;
    }

    // getters e setters omitidos
}
```

:::anatomy title="As anotações que fazem a tradução"
lang: java
code: |
  @Entity
  @Table(name = "product")
  public class Product {
      @Id
      @GeneratedValue(strategy = GenerationType.IDENTITY)
      private Long id;

      @Enumerated(EnumType.STRING)
      private Status status;
  }
notes:
  - { line: 1, text: "`@Entity` diz ao Hibernate: esta classe vira linha de tabela." }
  - { line: 2, text: "`@Table` nomeia a tabela. Sem ela, o nome da classe é usado." }
  - { line: 4, text: "`@Id` marca a chave primária — obrigatória em toda entidade." }
  - { line: 5, text: "`IDENTITY` delega a geração ao `BIGSERIAL` do banco." }
  - { line: 8, text: "`EnumType.STRING` grava `'ATIVO'`. Nunca use `ORDINAL`." }
:::

:::pitfall
`@Enumerated(EnumType.ORDINAL)` — que é o **padrão** quando você não declara
nada — grava a **posição** do enum: `0`, `1`, `2`. Se alguém inserir um valor
novo no meio da lista, todos os registros do banco passam a significar outra
coisa, silenciosamente. Declare sempre `EnumType.STRING`. Este é, sem
concorrência, o defeito mais caro deste capítulo.
:::

## Por que a entidade precisa de um construtor vazio

Aquele `protected Product() { }` parece inútil e é obrigatório: o Hibernate
cria o objeto por reflexão, sem saber nada dos seus construtores, e depois
preenche os campos. `protected` é o suficiente — não precisa ser público, e
assim ninguém cria um produto vazio por acidente.

É também o motivo pelo qual **entidade não pode ser um `record`** (capítulo
12): record não tem construtor vazio nem setters.

:::story O dia em que INATIVO virou PROMOCAO
O enum tinha três valores e estava gravado como número no banco — a
configuração padrão, que ninguém tinha escolhido conscientemente.

O zero era `ATIVO`, o um era `INATIVO`, o dois era `ESGOTADO`.

Em março, Cláudia pediu um status novo: `PROMOCAO`. Carlos abriu o enum e
acrescentou o valor onde fazia sentido semanticamente — entre `ATIVO` e
`INATIVO`, porque produto em promoção está mais perto de ativo do que de
inativo.

O deploy foi na quarta. Na quinta, quatro mil produtos inativos apareceram na
vitrine com etiqueta de promoção.

Ninguém tinha alterado dado nenhum. Os números no banco continuavam
exatamente os mesmos. O que mudou foi o significado deles.
:::

## O ciclo de vida de uma entidade

:::diagram type="flowchart" caption="Os quatro estados de uma entidade — e por que uma alteração pode ser gravada sem você mandar."
nodes:
  - { id: novo,  type: io,      text: "new Product(): transiente" }
  - { id: save,  type: process, text: "save(): gerenciada" }
  - { id: dirty, type: process, text: "setPrice(): suja" }
  - { id: flush, type: process, text: "flush: UPDATE automático" }
  - { id: fim,   type: start,   text: "fim da transação: desanexada" }
edges:
  - { from: novo,  to: save }
  - { from: save,  to: dirty }
  - { from: dirty, to: flush }
  - { from: flush, to: fim }
:::

Este é o comportamento que mais surpreende quem chega: dentro de uma
transação, alterar um objeto **gerenciado** gera um `UPDATE` ao final, mesmo
sem você chamar `save`. O Hibernate compara o estado atual com o que leu do
banco (*dirty checking*) e grava a diferença.

:::key
Entidade gerenciada não é um objeto comum: é um objeto que o Hibernate está
vigiando. É por isso que o capítulo 24 insiste em não deixar a entidade sair
da camada de serviço — fora dela, ninguém sabe se uma alteração vai virar
`UPDATE` ou não.
:::

## Conferindo o mapeamento

```properties title="application.properties"
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
```

`validate` compara a entidade com a tabela na partida e **falha se não
casarem**. É a configuração que você quer: se você acrescentou um campo na
classe e esqueceu a coluna, descobre em dois segundos, não em produção.

```text title="Saída com show-sql, ao salvar"
Hibernate:
    insert into product
        (created_at, description, name, price, quantity, status)
    values
        (?, ?, ?, ?, ?, ?)
```

:::tip
Deixe `show-sql=true` durante todo o desenvolvimento. Ver o SQL que o
Hibernate gera é o hábito que evita o problema N+1 do capítulo 30 — e é a
única forma de perceber que uma listagem simples disparou 200 consultas.
:::

## Quando a tradução automática atrapalha

O JPA é ótimo para operações por entidade — carregar um produto, salvar,
apagar. Ele é ruim para:

- **relatórios** com agregação e junção de cinco tabelas;
- **atualização em massa** (`UPDATE product SET status = 'INATIVO'` em um
  milhão de linhas);
- consultas em que a **forma do resultado** não é uma entidade.

Para esses casos, Spring oferece o `JdbcTemplate` e consultas nativas — e usar
SQL direto não é derrota, é escolher a ferramenta certa. Uma aplicação madura
tem as duas coisas.

:::history
A crítica organizada a esse tipo de ferramenta tem nome: *object-relational
impedance mismatch*. Objetos têm herança e referências; tabelas têm chaves e
junções. A tradução funciona em 90% dos casos e cobra os 10% restantes com
juros — o famoso "o ORM está lento" que, quase sempre, é o ORM fazendo
exatamente o que foi mandado.
:::

:::term Entidade gerenciada
Objeto que o Hibernate está acompanhando dentro de uma transação. Alterações
nele são gravadas automaticamente ao final.
:::

:::summary
- JPA é a especificação; Hibernate executa; Spring Data poupa código.
- `@Entity`, `@Id`, `@GeneratedValue` e `@Column` fazem o mapeamento.
- Use sempre `@Enumerated(EnumType.STRING)`.
- Entidade precisa de construtor vazio — e por isso não pode ser `record`.
- Dentro da transação, alterar entidade gerenciada gera `UPDATE` automático.
- `ddl-auto=validate` e `show-sql=true` são os padrões saudáveis.
:::

:::checkpoint
Você anota uma entidade completa, sabe qual anotação faz o quê, explica o
ciclo de vida de uma entidade e reconhece os casos em que o JPA não é a
ferramenta certa.
:::

:::milestone
`Product` agora é uma entidade JPA mapeada para a tabela `product`. Falta
quem execute as consultas — e o próximo capítulo mostra que isso é uma
interface vazia.
:::

:::exercise level=1
Anote a classe `Category` como entidade, com `name` único e obrigatório.
Confirme com `ddl-auto=validate` que a tabela casa com a classe.

:::answer
```java
@Entity
@Table(name = "category")
public class Category {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 80)
    private String name;

    protected Category() { }
}
```
:::

:::exercise level=2
Acrescente um campo `updatedAt` que seja preenchido automaticamente a cada
alteração. Descubra `@PreUpdate`.

:::answer
```java
@Column(name = "updated_at")
private Instant updatedAt;

@PreUpdate
void aoAtualizar() {
    this.updatedAt = Instant.now();
}
```
`@PreUpdate` e `@PrePersist` são ganchos do ciclo de vida. Úteis, e com um
porém: eles rodam dentro do Hibernate, o que significa que não rodam quando
você faz uma atualização em massa por SQL nativo.
:::

:::exercise level=3
Mude `@Enumerated` para `ORDINAL`, salve dois produtos, acrescente um valor no
**meio** do enum e leia os dados de novo. Descreva o que aconteceu.

:::answer
Os produtos gravados como `1` (que era `INATIVO`) passam a ser lidos como o
valor novo que ocupou a posição 1. Nenhum erro, nenhum aviso: só dados que
mudaram de significado. É o tipo de defeito que só é descoberto por um
cliente reclamando, meses depois — e a correção exige um script de migração
feito à mão.
:::
