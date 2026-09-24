---
title: "Relacionamentos JPA"
number: 29
part: p6
kicker: "Duas tabelas que se conhecem viram duas classes que se apontam — e é aí que o JPA fica poderoso e perigoso na mesma medida."
goal: >-
  Mapear `@ManyToOne`, `@OneToMany` e `@ManyToMany`, escolher o lado dono da
  relação e evitar as três armadilhas clássicas do mapeamento bidirecional.
---

Até agora o projeto tem uma entidade só. O mundo real não tem: produto
pertence a categoria, pedido pertence a cliente, pedido tem itens. Este
capítulo liga as caixas do diagrama do capítulo 18.

## A relação mais comum: `@ManyToOne`

```java title="Product.java (trecho)" numbered
@ManyToOne(fetch = FetchType.LAZY, optional = false)
@JoinColumn(name = "category_id")
private Category category;
```

Cinco palavras e a tabela ganha uma coluna `category_id` com chave
estrangeira. Repare em `fetch = LAZY` — é a decisão mais importante da linha,
e o capítulo 30 explica por quê.

:::anatomy title="A anotação que cria a chave estrangeira"
lang: java
code: |
  @ManyToOne(fetch = FetchType.LAZY, optional = false)
  @JoinColumn(name = "category_id")
  private Category category;
notes:
  - { line: 1, text: "`@ManyToOne`: muitos produtos para uma categoria. Este é o lado **dono** da relação." }
  - { line: 1, text: "`LAZY` só carrega a categoria quando alguém chamar `getCategory()`." }
  - { line: 1, text: "`optional = false` vira `NOT NULL` na coluna: todo produto precisa de categoria." }
  - { line: 2, text: "`@JoinColumn` nomeia a coluna; sem ela, o Hibernate inventa `category_id` mesmo assim." }
:::

:::key
O **lado dono** é sempre onde está a chave estrangeira — o lado
`@ManyToOne`. É ele que o banco consulta para saber quem aponta para quem.
Todo o resto do mapeamento é conveniência de navegação em Java.
:::

## O outro lado: `@OneToMany`

```java title="Category.java (trecho)" numbered
@OneToMany(mappedBy = "category")
private List<Product> products = new ArrayList<>();
```

`mappedBy = "category"` diz: *"a dona desta relação é o campo `category` de
`Product`; eu sou só o espelho"*. Sem ele, o Hibernate cria uma **terceira
tabela** para a relação — e você descobre isso pelo erro de esquema na
partida.

:::pitfall
`@OneToMany` sem `mappedBy` gera uma tabela de junção que ninguém pediu:
`category_products`. O sintoma é o `ddl-auto=validate` falhando com "missing
table". A causa é sempre a mesma: você declarou dois lados donos.
:::

## Bidirecional cobra disciplina

Quando os dois lados existem em Java, eles podem discordar entre si:

:::compare left="Só metade" right="Os dois lados"
produto.setCategory(cat);
// cat.getProducts()
// continua sem o produto
---
public void adicionar(
    Product p) {
  products.add(p);
  p.setCategory(this);
}
:::

O objeto em memória fica inconsistente até alguém recarregar do banco — e a
diferença entre o que está na memória e o que está na tabela é uma das fontes
de bug mais desconcertantes do JPA. Um método auxiliar em um lado só resolve.

:::tip
Só mapeie o lado `@OneToMany` se você **realmente navega** por ele. Uma
categoria com onze mil produtos em uma `List` é um convite ao desastre. Se a
navegação for rara, esqueça o campo e use
`productRepository.findByCategoryId(id)` — a informação é a mesma, o risco é
outro.
:::

## `@OneToMany` com dono próprio: os itens do pedido

```java title="Order.java" numbered
@Entity
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "customer_id")
    private Customer customer;

    @OneToMany(mappedBy = "order",
               cascade = CascadeType.ALL,
               orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    public void adicionar(OrderItem item) {
        items.add(item);
        item.setOrder(this);
    }
}
```

Aqui `cascade` e `orphanRemoval` fazem sentido: um item de pedido **não
existe** sem o pedido. Salvar o pedido salva os itens; remover um item da
lista o apaga do banco.

:::pitfall
`CascadeType.ALL` entre `Product` e `Category` seria um desastre: apagar uma
categoria apagaria todos os produtos dela. Cascade só se justifica quando o
filho é **parte** do pai — itens de um pedido, endereços de um cliente. Se o
filho tem vida própria, nada de cascade.
:::

:::trivia
A tabela se chama `orders`, no plural, por um motivo prosaico: `ORDER` é
palavra reservada em SQL (`ORDER BY`). Mapear uma entidade chamada `Order`
para uma tabela `order` gera um erro de sintaxe no `CREATE TABLE` que já
confundiu muita gente. Outros nomes na lista negra: `user`, `group`,
`table`, `select`.
:::

## `@ManyToMany`: quando os dois lados são muitos

```java title="Product.java (trecho)" numbered
@ManyToMany
@JoinTable(
    name = "product_tag",
    joinColumns = @JoinColumn(name = "product_id"),
    inverseJoinColumns = @JoinColumn(name = "tag_id"))
private Set<Tag> tags = new HashSet<>();
```

:::diagram type="er" caption="Muitos-para-muitos precisa de uma terceira tabela — sempre."
columns: 2
entities:
  - name: "Product"
    fields: ["id (PK)", "name", "price"]
  - name: "Tag"
    fields: ["id (PK)", "name"]
  - name: "product_tag"
    fields: ["product_id (FK)", "tag_id (FK)"]
relations:
  - { from: "Product", to: "product_tag", label: "1:N" }
  - { from: "Tag", to: "product_tag", label: "1:N" }
:::

:::pitfall
`@ManyToMany` funciona bem enquanto a relação for **apenas** uma ligação. No
instante em que alguém pedir "quando essa etiqueta foi aplicada?" ou "quem
aplicou?", a tabela de junção precisa virar uma entidade com id próprio — e
a conversão no meio do projeto é dolorosa. Antes de usar `@ManyToMany`,
pergunte se a ligação pode ganhar atributos no futuro. Quase sempre pode.
:::

Use `Set`, não `List`, em `@ManyToMany`: `List` faz o Hibernate apagar e
reinserir todas as linhas da junção a cada alteração.

## O modelo do projeto, completo

:::diagram type="er" caption="O domínio da Aurora Comércio ao fim da Parte 6."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name"]
  - name: "Product"
    fields: ["id (PK)", "name", "price", "quantity", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "created_at", "total"]
  - name: "OrderItem"
    fields: ["id (PK)", "order_id (FK)", "product_id (FK)", "quantity", "unit_price"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
  - { from: "Order", to: "OrderItem", label: "1:N" }
:::

Repare no `unit_price` dentro de `OrderItem`: é o *snapshot* do capítulo 18.
O preço do produto muda; o do pedido, não.

:::story A categoria dentro da categoria
— A gente precisa de subcategoria — disse Cláudia.

— Uma categoria dentro da outra?

— Isso. "Periféricos" tem "Teclados" e "Mouses".

Carlos mapeou em dez minutos: uma `@ManyToOne` de `Category` para a própria
`Category`. Ficou até elegante.

Na semana seguinte, Cláudia voltou:

— E dentro de "Teclados" tem "Mecânicos" e "Membrana".

O mapeamento aguentou — árvore é árvore, não importa a profundidade. O que
não aguentou foi a tela: a listagem de produtos de uma categoria passou a
precisar de todos os descendentes, e a consulta virou uma recursão.

— Quantos níveis vocês pretendem ter? — perguntou Marina.

— Uns três, acho.

— "Acho" significa cinco.

Foram sete, em quatro meses. E, no sétimo, alguém criou uma subcategoria
cujo pai era ela mesma. O banco aceitou: a chave estrangeira estava
satisfeita. A tela entrou em laço infinito.
:::

:::summary
- `@ManyToOne` é o lado dono: onde mora a chave estrangeira.
- `@OneToMany` precisa de `mappedBy`, senão vira tabela de junção.
- Em relação bidirecional, um método auxiliar mantém os dois lados
  coerentes.
- `cascade` e `orphanRemoval` só quando o filho é parte do pai.
- `@ManyToMany` com `Set`; se a ligação puder ganhar atributo, use entidade.
:::

:::checkpoint
Você mapeia as três cardinalidades, identifica o lado dono, evita a tabela de
junção acidental e sabe quando cascade é perigoso.
:::

:::milestone
O domínio está completo: categoria, produto, cliente, pedido e item. E,
junto com ele, chegou um tipo de problema que não existia antes — o próximo
capítulo é inteiro sobre ele.
:::

:::exercise level=1
Mapeie `Category` em `Product` com `@ManyToOne` e crie o *query method*
`findByCategoryId(Long id)`. Confirme a coluna no banco.

:::answer
```java
Page<Product> findByCategoryId(Long categoryId, Pageable p);
```
Repare que o nome do método navega pela relação: `Category` + `Id`. O Spring
Data entende isso e gera `WHERE category_id = ?` sem nenhum join.
:::

:::exercise level=2
Crie `Order` e `OrderItem` com cascade e `orphanRemoval`. Depois remova um
item da lista, salve o pedido e confira o `DELETE` no log.

:::answer
O `DELETE` aparece sem você tê-lo pedido: `orphanRemoval = true` entende que
um item fora da lista do pai deixou de existir. É conveniente e perigoso na
mesma medida — se alguém der `items.clear()` por engano, o pedido perde tudo.
:::

:::exercise level=3
Implemente a subcategoria da história: `Category` com `@ManyToOne` para si
mesma. Depois escreva a validação que impede uma categoria de ser pai dela
própria, direta ou indiretamente.

:::answer
A validação direta é trivial (`parent.getId().equals(this.getId())`). A
indireta exige subir a árvore até a raiz procurando o próprio id — e é por
isso que, em bases grandes, esse tipo de hierarquia costuma ganhar uma coluna
`path` (algo como `/1/7/23/`) que transforma a checagem de ciclo em uma
comparação de texto. Estrutura de dados resolvendo o que o algoritmo faria
caro: a mesma lição do capítulo 8.
:::
