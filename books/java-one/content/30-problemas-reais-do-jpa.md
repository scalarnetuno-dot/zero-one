---
title: "Problemas reais do JPA"
number: 30
part: p6
kicker: "O ORM faz exatamente o que você mandou. O problema é que você mandou sem saber."
epigraph: "Toda abstração não trivial vaza."
epigraph_by: "Joel Spolsky, lei das abstrações vazadas"
goal: >-
  Diagnosticar o problema N+1 pelo log, escolher entre `JOIN FETCH` e
  `@EntityGraph`, e explicar `LazyInitializationException` sem adivinhação.
---

Este é o capítulo em que muita gente desiste do JPA — e é também o capítulo
que, entendido, transforma o JPA em ferramenta. Todos os problemas aqui têm
a mesma raiz: **o Java esconde quando uma consulta acontece**.

## O problema N+1

```java title="Parece inofensivo" numbered
List<Product> produtos = repository.findAll();

for (Product p : produtos) {
    System.out.println(p.getName() + " — "
            + p.getCategory().getName());
}
```

```text title="O log com show-sql ligado"
select ... from product
select ... from category where id = 1
select ... from category where id = 2
select ... from category where id = 1
select ... from category where id = 3
... mais 11.996 vezes
```

**Uma** consulta para trazer a lista, mais **N** consultas — uma por item —
para buscar a categoria de cada um. Daí o nome: N+1.

:::diagram type="sequence" caption="Cada `getCategory()` de um campo LAZY é uma ida ao banco."
actors:
  - { id: s, name: "Service" }
  - { id: h, name: "Hibernate" }
  - { id: d, name: "Banco" }
messages:
  - { from: s, to: h, text: "findAll()" }
  - { from: h, to: d, text: "select * from product" }
  - { from: d, to: h, text: "11.000 linhas", dashed: true }
  - { from: s, to: h, text: "getCategory() do item 1" }
  - { from: h, to: d, text: "select ... category" }
  - { from: s, to: h, text: "getCategory() do item 2" }
  - { from: h, to: d, text: "select ... category" }
:::

:::key
O N+1 é invisível no código Java. `p.getCategory().getName()` parece um
acesso a campo e é uma consulta ao banco. A única forma de vê-lo é **ler o
log de SQL** — e é por isso que este livro pediu `show-sql=true` desde o
capítulo 20.
:::

## As três soluções

```java title="1. JOIN FETCH — traz tudo em uma consulta" numbered
@Query("""
       SELECT p FROM Product p
       JOIN FETCH p.category
       """)
List<Product> findAllComCategoria();
```

```java title="2. @EntityGraph — o mesmo, sem escrever JPQL" numbered
@EntityGraph(attributePaths = "category")
List<Product> findAll();
```

```java title="3. Não navegar: buscar só o que a tela mostra" numbered
@Query("""
       SELECT new com.loja.catalog.product.dto.ProductSummary(
              p.id, p.name, c.name)
       FROM Product p JOIN p.category c
       """)
List<ProductSummary> resumo();
```

A terceira é a mais rápida das três, porque nem monta entidades: o banco
devolve exatamente as três colunas que a tela precisa e o Hibernate constrói
o record direto.

| Solução | Consultas | Quando |
|---|---|---|
| `JOIN FETCH` | 1 | precisa da entidade completa |
| `@EntityGraph` | 1 | o mesmo, declarativo |
| projeção em DTO | 1 | a tela só lê |
| nada | N+1 | nunca de propósito |

Tabela: Três formas de resolver o mesmo problema — e a quarta linha, que é o
estado natural de quem não olhou o log.

:::pitfall
`JOIN FETCH` com paginação é uma armadilha específica: o Hibernate avisa
`firstResult/maxResults specified with collection fetch; applying in memory`
e traz **a tabela inteira** para paginar em Java. Com coleção (`@OneToMany`),
use `@EntityGraph` com `Pageable` ou faça duas consultas — a de ids,
paginada, e a dos dados.
:::

## `LazyInitializationException`

```java title="O erro que aparece só fora da transação" numbered
@Transactional(readOnly = true)
public Product buscar(Long id) {
    return repository.findById(id).orElseThrow();
}

// no controlador, FORA da transação:
produto.getCategory().getName();
// → LazyInitializationException: could not initialize proxy
```

Um campo `LAZY` não é a categoria: é um **proxy**, um objeto vazio que sabe
como buscar a categoria quando alguém pedir. Ele só consegue buscar enquanto
a sessão do Hibernate estiver aberta — ou seja, dentro da transação. Fora
dela, o proxy não tem a quem perguntar.

:::diagram type="flowchart" caption="O proxy só funciona enquanto a sessão existe."
nodes:
  - { id: t1, type: start,    text: "abre transação" }
  - { id: q,  type: process,  text: "carrega Product (categoria = proxy)" }
  - { id: t2, type: process,  text: "fecha transação" }
  - { id: g,  type: decision, text: "getCategory()?" }
  - { id: ok, type: process,  text: "dentro: consulta o banco" }
  - { id: er, type: process,  text: "fora: LazyInitializationException" }
edges:
  - { from: t1, to: q }
  - { from: q,  to: t2 }
  - { from: t2, to: g }
  - { from: g,  to: ok, label: "antes" }
  - { from: g,  to: er, label: "depois" }
:::

As três saídas, em ordem de qualidade:

1. **Converter para DTO dentro da transação** — a solução do capítulo 24, que
   por acaso já resolve isto.
2. **`JOIN FETCH`** quando a navegação é sempre necessária.
3. **`open-in-view`** — a configuração que mantém a sessão aberta até o fim
   da requisição. É o padrão do Spring Boot, e é uma má ideia.

:::pitfall
`spring.jpa.open-in-view=true` vem **ligado** por padrão. Ele faz o
`LazyInitializationException` desaparecer — e, junto, faz o N+1 acontecer na
serialização do JSON, longe de qualquer código seu. Desligue:

```properties
spring.jpa.open-in-view=false
```

Você vai quebrar algumas telas no dia seguinte. Cada quebra é um lugar onde
o seu código estava consultando o banco sem saber.
:::

:::story Quatro mil consultas para uma tela
A tela de catálogo ficou lenta de um jeito estranho: rápida no começo do
mês, insuportável no fim.

Carlos abriu o log de produção e levou seis minutos para localizar a
requisição — não porque fosse difícil, mas porque havia quatro mil e
trinta e duas linhas de `select ... from category` entre o início e o fim
dela.

O gráfico batia com a história: a lentidão crescia com o número de produtos
cadastrados. Era o N+1 crescendo junto com o catálogo.

O interessante não foi o defeito. Foi a discussão que veio depois.

Roberto queria trocar o banco. Um fornecedor tinha ligado oferecendo uma
solução "otimizada para alto volume". O gráfico da apresentação era muito
convincente.

Marina pediu quinze minutos e uma anotação: `@EntityGraph`.

A tela passou de 4.032 consultas para uma. O tempo de resposta caiu de onze
segundos para quarenta milissegundos. O fornecedor continuou ligando por
mais duas semanas.
:::

:::art caption="Antes de trocar o banco, leia o log."
src="antes-de-trocar-o-banco-leia-o-log.png"
Charge editorial minimalista: desenvolvedora sênior de pé ao lado de um
monitor dividido ao meio; à esquerda, uma coluna interminável de linhas
idênticas de SQL descendo pela tela e escorrendo pelo chão como uma fita; à
direita, uma única linha curta. Ao lado, um gerente segura um folheto
colorido de fornecedor com um gráfico de foguete. Fundo branco, poucos
elementos, humor visual seco, estética editorial de tecnologia.
:::

## Transação: onde ela começa e onde termina

```java title="Duas operações, uma transação" numbered
@Transactional
public Order finalizar(Long orderId) {
    Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));

    for (OrderItem item : order.getItems()) {
        Product p = item.getProduct();
        p.baixarEstoque(item.getQuantity());
    }

    order.setStatus(OrderStatus.CONFIRMADO);
    return order;
}
```

Se a baixa do terceiro item falhar por estoque insuficiente, a exceção sobe,
a transação desfaz **tudo** — inclusive as duas baixas já feitas — e o pedido
continua pendente. É esse comportamento de "tudo ou nada" que justifica a
anotação.

:::pitfall
Transação aberta é recurso preso: enquanto ela vive, uma conexão do *pool*
está reservada. Um `@Transactional` em volta de uma chamada HTTP a um
serviço externo — que pode demorar trinta segundos — esgota o pool em
minutos. Regra: **nada de entrada e saída lenta dentro de transação**.
:::

## O checklist do JPA em produção

```properties title="application.properties — o que vale a pena"
spring.jpa.open-in-view=false
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.properties.hibernate.jdbc.batch_size=30
logging.level.org.hibernate.SQL=DEBUG
```

E o hábito que vale mais que as quatro linhas: **abrir o log de SQL depois de
escrever qualquer consulta nova** e contar quantas linhas apareceram. Se for
mais de uma, você tem algo a entender antes de seguir.

:::summary
- N+1 é invisível no Java e óbvio no log de SQL.
- `JOIN FETCH`, `@EntityGraph` ou projeção em DTO resolvem — nessa ordem de
  esforço.
- `LazyInitializationException` significa acesso a proxy fora da transação.
- `open-in-view` esconde o problema e é o padrão: desligue.
- Transação envolve tudo ou nada; nunca coloque chamada externa dentro dela.
:::

:::checkpoint
Você identifica um N+1 lendo o log, escolhe a solução adequada, explica o que
é um proxy LAZY e sabe por que `open-in-view` desligado é melhor.
:::

:::milestone
Fim da Parte 6. A API tem relacionamentos e consultas que não multiplicam
idas ao banco. Ela também continua completamente aberta: qualquer pessoa com
a URL apaga qualquer produto. A Parte 7 fecha a porta.
:::

:::exercise level=1
Ligue `show-sql`, chame `GET /products` com dez produtos de categorias
diferentes e conte as consultas. Depois acrescente `@EntityGraph` e conte de
novo.

:::answer
Onze consultas viram uma. É o experimento mais barato deste livro e o que
mais muda a forma de escrever consulta daqui para frente.
:::

:::exercise level=2
Provoque um `LazyInitializationException` de propósito: devolva a entidade
`Product` direto do controlador com `open-in-view=false` e um campo LAZY.
Depois conserte com DTO.

:::answer
A correção com DTO não é um remendo: é a forma certa. Converter dentro da
transação garante que tudo que o JSON precisa já foi carregado, e o
controlador passa a trabalhar com um objeto que não tem ligação nenhuma com
o banco.
:::

:::exercise level=3
Escreva a projeção `ProductSummary(Long id, String name, String category)`
com `SELECT new` e compare o SQL gerado com o do `JOIN FETCH`. Qual traz
menos dados?

:::answer
A projeção traz três colunas; o `JOIN FETCH` traz todas as colunas das duas
tabelas, inclusive `description`, que pode ter dois mil caracteres por linha.
Em uma listagem de cem itens, a diferença é de megabytes. Trazer só o que a
tela mostra é a otimização mais subestimada do acesso a dados.
:::
