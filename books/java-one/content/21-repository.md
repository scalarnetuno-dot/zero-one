---
title: "Repository"
number: 21
part: p4
kicker: "Uma interface vazia que ganha vinte métodos. Vale entender de onde eles vêm antes de confiar neles."
goal: >-
  Criar um repositório com `JpaRepository`, usar os métodos prontos, escrever
  *query methods* pelo nome e explicar quem implementa a interface.
---

Este capítulo tem o melhor custo-benefício do livro: três linhas de código
entregam o acesso completo ao banco.

```java title="ProductRepository.java" numbered
package com.loja.catalog.product;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ProductRepository
        extends JpaRepository<Product, Long> {
}
```

É isso. Uma interface, sem nenhum método declarado, sem nenhuma classe que a
implemente. E a partir daqui você pode salvar, buscar, listar, contar e apagar
produtos.

## O que acabou de acontecer

Na partida, o Spring Data encontra toda interface que estende
`JpaRepository`, gera uma classe em tempo de execução que implementa cada
método e registra o resultado como um bean. O `@Repository` é implícito.

:::diagram type="blocks" caption="Você declara a interface; o Spring Data fabrica a implementação na partida."
rows:
  - [{ text: "ProductRepository", note: "interface que você escreveu" }]
  - [{ text: "SimpleJpaRepository", note: "implementação genérica do Spring Data" }]
  - [{ text: "EntityManager", note: "API do JPA" }]
  - [{ text: "Hibernate → JDBC → PostgreSQL", note: "o SQL de verdade" }]
:::

:::anatomy title="Os dois parâmetros que o JpaRepository exige"
lang: java
code: |
  public interface ProductRepository
          extends JpaRepository<Product, Long> {
  }
notes:
  - { line: 2, text: "`Product` é a entidade que este repositório administra." }
  - { line: 2, text: "`Long` é o tipo da chave primária — o mesmo do campo `@Id`." }
  - { line: 2, text: "Errar o segundo parâmetro (`Integer` em vez de `Long`) só falha na partida, com uma mensagem longa." }
:::

## Os métodos que vêm de graça

```java title="Tudo isto existe sem você escrever" numbered
Product salvo = repository.save(novo);          // INSERT ou UPDATE
Optional<Product> um = repository.findById(1L);  // SELECT by id
List<Product> todos = repository.findAll();     // SELECT *
long total = repository.count();
boolean existe = repository.existsById(1L);
repository.deleteById(1L);
repository.saveAll(listaDeProdutos);            // lote
```

Três detalhes que economizam horas de depuração:

`save` faz `INSERT` **ou** `UPDATE`: se o id é nulo, insere; se tem valor,
atualiza. É conveniente e esconde uma pegadinha — salvar um objeto com um id
que não existe no banco gera um `INSERT` com aquele id, não um erro.

`findById` devolve `Optional` (capítulo 13), não `null`. A API está
comunicando no tipo que o produto pode não existir.

`deleteById` de um id inexistente lança
`EmptyResultDataAccessException` — não é um "não fez nada" silencioso.

## Query methods: a consulta que nasce do nome

Aqui está o recurso que parece mágica e é só convenção:

```java title="ProductRepository.java" numbered
public interface ProductRepository
        extends JpaRepository<Product, Long> {

    List<Product> findByStatus(Status status);

    List<Product> findByNameContainingIgnoreCase(String termo);

    List<Product> findByPriceBetween(BigDecimal min, BigDecimal max);

    Optional<Product> findByNameIgnoreCase(String name);

    boolean existsByName(String name);

    long countByStatus(Status status);

    List<Product> findByStatusOrderByPriceDesc(Status status);
}
```

O Spring Data **lê o nome do método**, quebra em palavras-chave e monta a
consulta. `findByNameContainingIgnoreCase` vira:

```sql
SELECT * FROM product WHERE upper(name) LIKE upper('%' || ? || '%')
```

| Palavra no nome | Vira em SQL |
|---|---|
| `findBy`, `countBy`, `existsBy` | `SELECT`, `COUNT`, `EXISTS` |
| `Containing` | `LIKE %...%` |
| `IgnoreCase` | `upper(campo) = upper(?)` |
| `Between`, `GreaterThan`, `LessThan` | comparadores |
| `And`, `Or` | conectores |
| `OrderBy...Desc` | `ORDER BY ... DESC` |
| `Top10`, `First` | `LIMIT` |

Tabela: O vocabulário dos *query methods*. A lista completa está na
documentação do Spring Data, e cabe em uma página.

:::pitfall
O nome tem de casar com o **campo da entidade**, não com a coluna do banco.
`findByCreatedAt` funciona; `findByCreated_at` não. E, se você errar o nome do
campo, o erro aparece na partida com a mensagem `No property 'xyz' found for
type 'Product'` — o que é ótimo: é um erro de digitação pego antes da primeira
requisição.
:::

:::pitfall
Nome de método é bom até deixar de ser. Quando você se vê escrevendo
`findByStatusAndPriceBetweenAndQuantityGreaterThanOrderByNameAsc`, o limite
foi passado. A partir daí use `@Query` — e é o assunto do capítulo 28.
:::

## `@Query`: quando o nome não basta

```java title="JPQL e SQL nativo" numbered
@Query("SELECT p FROM Product p WHERE p.quantity = 0")
List<Product> semEstoque();

@Query("""
       SELECT p FROM Product p
       WHERE p.status = :status
         AND p.price <= :teto
       ORDER BY p.price
       """)
List<Product> baratosPorStatus(
        @Param("status") Status status,
        @Param("teto") BigDecimal teto);

@Query(value = "SELECT * FROM product WHERE price > :min",
       nativeQuery = true)
List<Product> acimaDe(@Param("min") BigDecimal min);
```

A primeira e a segunda usam **JPQL**: parecido com SQL, mas escrito em termos
de **entidades e campos** (`Product p`, `p.price`), não de tabelas e colunas.
A terceira é SQL nativo, útil para recursos específicos do PostgreSQL.

:::trivia
Aquele texto de várias linhas entre `"""` é um *text block*, do Java 15. Antes
dele, um JPQL de cinco linhas era uma concatenação com `+` e espaços no fim de
cada pedaço — e esquecer um espaço gerava `WHERE p.status = :statusORDER BY`.
Uma funcionalidade de sintaxe que apagou uma categoria inteira de bug.
:::

## Testando o repositório de verdade

```java title="ProductRepositoryTest.java" numbered
@DataJpaTest
class ProductRepositoryTest {

    @Autowired
    ProductRepository repository;

    @Test
    void deveEncontrarPorStatus() {
        repository.save(new Product("Teclado",
                new BigDecimal("349.90"), 12));

        List<Product> ativos =
                repository.findByStatus(Status.ATIVO);

        assertThat(ativos).hasSize(1);
    }
}
```

`@DataJpaTest` sobe **apenas** a camada de dados, em um banco de memória, e
desfaz tudo ao fim de cada teste. O capítulo 37 aprofunda — inclusive por que
testar em um banco diferente do de produção é uma ideia que cobra a conta.

:::summary
- `JpaRepository<Entidade, TipoDoId>` entrega o CRUD completo sem
  implementação.
- O Spring Data gera a classe na partida; o `@Repository` é implícito.
- `save` insere ou atualiza; `findById` devolve `Optional`.
- *Query methods* nascem do nome do método e falham na partida se o campo não
  existir.
- Nome longo demais é sinal de que a consulta merece `@Query`.
:::

:::checkpoint
Você cria um repositório, usa os métodos prontos, escreve consultas pelo nome
do método, sabe quando trocar para `@Query` e testa com `@DataJpaTest`.
:::

:::milestone
A API fala com o banco. Os dados sobrevivem ao reinício — o defeito número um
do capítulo 17 está resolvido. Falta tirar a regra de negócio do controlador.
:::

:::exercise level=1
Crie `CategoryRepository` e escreva um *query method* que busque categoria por
nome, ignorando maiúsculas.

:::answer
```java
public interface CategoryRepository
        extends JpaRepository<Category, Long> {
    Optional<Category> findByNameIgnoreCase(String name);
}
```
O retorno é `Optional` porque a busca por um nome específico pode não achar
nada — e a assinatura avisa isso a quem chama.
:::

:::exercise level=2
Escreva um método que devolva os cinco produtos mais caros com estoque
disponível, usando apenas o nome do método.

:::answer
```java
List<Product> findTop5ByQuantityGreaterThanOrderByPriceDesc(int min);
```
Chamado com `0`. É o limite do que o nome ainda comunica bem — um campo a
mais e a versão com `@Query` fica mais legível.
:::

:::exercise level=3
Escreva, com `@Query`, uma consulta que devolva o total em estoque (soma de
preço × quantidade) de todos os produtos ativos. Repare que o resultado não é
uma entidade.

:::answer
```java
@Query("""
       SELECT SUM(p.price * p.quantity) FROM Product p
       WHERE p.status = com.loja.catalog.product.Status.ATIVO
       """)
BigDecimal valorTotalEmEstoque();
```
O retorno é um `BigDecimal`, não um `Product` — e pode vir **nulo** se não
houver nenhum produto ativo, porque `SUM` de conjunto vazio em SQL é `NULL`.
Tratar isso é responsabilidade do serviço, que é o próximo capítulo.
:::
