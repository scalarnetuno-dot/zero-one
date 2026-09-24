---
title: "Modelando a aplicação"
number: 18
part: p4
kicker: "Antes de escolher a tecnologia, decidir os substantivos. Um modelo errado sobrevive a todas as refatorações."
goal: >-
  Identificar entidades, atributos e relações de um domínio, escolher a chave
  primária e justificar cada tipo de campo.
---

O capítulo 17 entregou uma API que guarda produtos em memória. Antes de
trocar a memória por um banco, é preciso decidir **o que** guardar. Essa
decisão é a mais duradoura do projeto: tecnologias mudam, modelos ficam.

## Entidade: o substantivo que tem identidade

Um produto não é um valor — é uma coisa. Dois produtos com o mesmo nome e o
mesmo preço são produtos diferentes, porque são itens diferentes no estoque.
Isso tem nome: `Product` é uma **entidade**, e entidade tem **identidade**.

:::key
O teste é este: *se todos os atributos forem iguais, ainda são coisas
diferentes?* Se sim, é entidade e precisa de id. Se não — como um endereço,
uma cor, um dinheiro — é um **valor**, e um `record` do capítulo 12 resolve.
:::

## O modelo do livro

:::diagram type="er" caption="O domínio completo: começa em Product e cresce até aqui na Parte 6."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name", "description"]
  - name: "Product"
    fields: ["id (PK)", "name", "description", "price", "quantity", "status", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email", "created_at"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "created_at", "total"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
:::

A Parte 4 constrói apenas `Product`. `Category` entra no capítulo 29,
`Customer` e `Order` no projeto final. Construir tudo de uma vez é a receita
mais confiável de não terminar nada.

## Os atributos, um por um

```java title="Product.java — o rascunho" numbered
public class Product {
    private Long id;
    private String name;
    private String description;
    private BigDecimal price;
    private Integer quantity;
    private Status status;
    private Instant createdAt;
}
```

Cada tipo aí é uma decisão, e vale defender todas.

| Campo | Tipo | Por quê |
|---|---|---|
| `id` | `Long` | cabe 9 quintilhões; `Integer` estoura em 2,1 bi |
| `name` | `String` | com limite de tamanho no banco |
| `price` | `BigDecimal` | dinheiro não é `double` (capítulo 3) |
| `quantity` | `Integer` | objeto, não `int`: permite nulo enquanto não definido |
| `status` | `Status` | enum, não texto (capítulo 12) |
| `createdAt` | `Instant` | momento absoluto, sem fuso |

Tabela: Tipos escolhidos por motivo, não por hábito.

:::pitfall
`Long` e `long`, `Integer` e `int` não são a mesma coisa. Os primeiros são
objetos e aceitam `null`; os segundos são primitivos e começam em zero. Em uma
entidade de banco, use sempre os objetos: um `long id` já vale `0` antes de
salvar, e `0` é indistinguível de "ainda não tem id".
:::

## A chave primária

Três estratégias, e você vai encontrar as três em código real:

| Estratégia | Exemplo | Quando |
|---|---|---|
| Sequencial | `1, 2, 3` | padrão; simples e legível |
| UUID | `9f1c...` | dados distribuídos, id gerado pelo cliente |
| Natural | `cpf`, `sku` | quase nunca: dado de negócio muda |

Tabela: Chave sequencial resolve a maioria dos casos. É a escolha do livro.

:::pitfall
Usar um dado de negócio como chave primária parece elegante e cobra a conta
depois. O SKU do fornecedor muda; o CPF é digitado errado; o e-mail do cliente
é atualizado. Quando isso acontece, você descobre que a chave está copiada em
seis tabelas. Chave primária deve ser um número sem significado — é a única
coisa que nunca precisa mudar.
:::

## Relações: quem conhece quem

```text title="A frase que define a relação"
Uma categoria tem muitos produtos.
Um produto pertence a uma categoria.
```

Essas duas frases descrevem a mesma relação vista dos dois lados — e essa é a
essência do capítulo 29. Em banco de dados, ela se materializa como uma
**chave estrangeira** na tabela do lado "muitos":

:::diagram type="blocks" caption="A chave estrangeira mora do lado que tem muitos."
flow: false
rows:
  - [{ text: "category", note: "id · name" }]
  - [{ text: "product", note: "id · name · category_id →" }]
:::

| Cardinalidade | Exemplo | Onde fica a FK |
|---|---|---|
| 1:N | categoria → produtos | no produto |
| N:1 | produto → categoria | no produto (mesma coisa) |
| N:N | produto ↔ etiqueta | em uma tabela de junção |
| 1:1 | usuário → perfil | em qualquer um dos dois |

Tabela: As quatro cardinalidades. A maioria das relações reais é 1:N.

:::story O produto que também é serviço
A reunião de modelagem durou duas horas e produziu um desenho no quadro.

Aos noventa minutos, Cláudia lembrou de uma coisa.

— Ah, e tem os serviços.

— Serviços?

— Instalação, configuração, garantia estendida. A gente vende também.

— E isso é um produto?

— É e não é. Não tem estoque. Mas tem preço. E aparece no catálogo junto com
os outros. E o cliente coloca no carrinho igual.

Marina virou o marcador na mão por alguns segundos.

— Quantos serviços existem hoje?

— Três.

— E quantos produtos?

— Onze mil.

Ela desenhou uma caixa no canto do quadro, escreveu `Product` dentro e um
campo `type` embaixo. Depois desenhou uma hierarquia de classes ao lado, com
`Product` como pai, e riscou.

— A gente começa com um campo. Se um dia os serviços tiverem regra própria de
verdade, a gente separa. Modelar o futuro que talvez não venha custa mais que
mudar depois.
:::

## Três perguntas que evitam refatoração

Antes de escrever a primeira linha de SQL, responda:

1. **O que identifica isto?** Se a resposta for "o nome", pense duas vezes —
   nomes se repetem.
2. **Este campo pode ser nulo?** Cada campo opcional é um `if` a mais no
   código, para sempre.
3. **Este dado é histórico ou atual?** Preço atual é um campo. Preço na data
   do pedido é outro campo, no pedido. Confundir os dois é o defeito clássico
   de qualquer sistema de vendas.

:::trivia
A pergunta 3 tem nome em sistemas reais: *snapshot*. Quando um cliente compra
por R$ 100 e o preço sobe para R$ 120, o pedido antigo tem de continuar
mostrando R$ 100. Lojas grandes copiam o preço, o nome e até a descrição para
dentro do item do pedido — uma duplicação intencional, porque o pedido é um
documento histórico e não um espelho do catálogo.
:::

## Estrutura de pacotes

A partir daqui o projeto passa a ter pacotes por **funcionalidade**, não por
tipo técnico:

:::tree title="Pacote por domínio, não por camada"
com/loja/catalog/
  CatalogApplication.java
  product/
    Product.java              # entidade
    ProductRepository.java    # acesso a dados
    ProductService.java       # regra
    ProductController.java    # HTTP
    dto/
      ProductRequest.java
      ProductResponse.java
  category/
    Category.java
  shared/
    exception/
:::

:::compare left="Por camada (evite)" right="Por domínio (prefira)"
controller/
  ProductController
  OrderController
service/
  ProductService
  OrderService
---
product/
  ProductController
  ProductService
order/
  OrderController
  OrderService
:::

A diferença aparece quando o sistema cresce. Na organização por camada, mexer
em produto exige abrir quatro pastas distantes; na por domínio, tudo que fala
de produto está em uma. E apagar uma funcionalidade passa a ser apagar uma
pasta.

:::summary
- Entidade tem identidade e precisa de id; valor não.
- `BigDecimal` para dinheiro, `Instant` para momento, enum para conjunto
  fechado, `Long` (não `long`) para id.
- Chave primária é número sem significado de negócio.
- Relação 1:N põe a chave estrangeira do lado "muitos".
- Organize pacotes por domínio, não por camada.
:::

:::checkpoint
Você distingue entidade de valor, escolhe tipo e chave com justificativa,
identifica a cardinalidade de uma relação e organiza pacotes por domínio.
:::

:::milestone
O modelo está no papel: `Product` com sete campos, e um mapa do domínio que
vai até `Order`. O capítulo 19 transforma isso em tabelas de verdade.
:::

:::exercise level=1
Liste os campos de `Customer` com tipo e justificativa. Inclua um campo que
possa ser nulo e explique por quê.

:::answer
`id: Long`, `name: String`, `email: String` (único), `phone: String` (pode
ser nulo: não todo cliente informa), `createdAt: Instant`. Cada campo nulo é
uma decisão: `phone` nulo significa "não informado", e o código que envia SMS
vai precisar tratar isso — para sempre.
:::

:::exercise level=2
Modele um carrinho de compras. Decida se `CartItem` é entidade ou valor e
justifique.

:::answer
É entidade, com uma ressalva. Dois itens do mesmo produto no mesmo carrinho
poderiam ser fundidos (somando a quantidade), o que sugere valor. Mas, se o
sistema precisa saber *quando* cada item foi adicionado, ou permitir preços
diferentes por item (promoção aplicada só a um), cada item ganha identidade
própria. A resposta depende do requisito — e é por isso que modelagem é
conversa, não técnica.
:::

:::exercise level=3
O preço de um produto muda. Desenhe como o seu modelo preserva o valor
histórico dos pedidos já feitos.

:::answer
`OrderItem` guarda `unitPrice` copiado no momento da compra, além de
`product_id`. A chave estrangeira serve para rastrear qual produto foi
vendido; o preço copiado serve para o documento histórico. Sem essa
duplicação, um reajuste de preço reescreveria o passado de toda a base — e é
um dos bugs mais caros que um sistema de vendas pode ter.
:::
