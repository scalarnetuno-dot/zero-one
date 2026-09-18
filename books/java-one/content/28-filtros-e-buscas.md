---
title: "Filtros e buscas"
number: 28
part: p5
kicker: "Filtrar no banco é uma consulta. Filtrar em memória é trazer tudo e jogar quase tudo fora."
goal: >-
  Escrever filtros combináveis com Specification, entender por que `LIKE
  '%termo%'` ignora o índice e decidir entre *query method*, `@Query` e busca
  dinâmica.
---

A listagem está paginada. Falta o que todo mundo pede em seguida: procurar.
E procurar é onde uma API bem escrita e uma API lenta se separam.

## O jeito errado, que funciona por seis meses

```java title="Filtrar depois de trazer tudo" numbered
public List<ProductResponse> buscar(String termo) {
    return repository.findAll().stream()
            .filter(p -> p.getName()
                    .toLowerCase()
                    .contains(termo.toLowerCase()))
            .map(ProductResponse::of)
            .toList();
}
```

Isso traz **todos** os produtos do banco para a memória da aplicação e
descarta quase todos. Com cem produtos, ninguém percebe. Com cem mil, cada
busca move cem mil linhas pela rede para devolver três.

:::key
A pergunta que separa as duas implementações: *quem filtra?* Se a resposta é
"o Java", você já perdeu. Quem filtra tem de ser o banco — ele tem índice,
estatística e trinta anos de otimizador. A sua aplicação tem um `for`.
:::

## Filtro simples: o nome do método resolve

```java title="ProductRepository.java" numbered
Page<Product> findByNameContainingIgnoreCase(
        String termo, Pageable pageable);

Page<Product> findByStatusAndPriceBetween(
        Status status, BigDecimal min, BigDecimal max,
        Pageable pageable);
```

:::http title="A busca do catálogo"
GET /products?name=teclado&page=0&size=20
---
200 OK

{
  "content": [
    { "id": 3, "name": "Teclado mecânico", "price": 349.90 }
  ],
  "totalElements": 1
}
:::

Funciona bem enquanto os filtros são **fixos**. O problema aparece quando
eles se combinam.

## A explosão combinatória dos filtros opcionais

Quatro filtros opcionais — nome, status, preço mínimo, preço máximo —
produzem dezesseis combinações possíveis. Escrever um método para cada é
inviável, e escrever `if` aninhado é pior:

:::compare left="Um método por combinação" right="Um filtro que se monta"
if (nome != null
    && status != null) {
  return repo
    .findByNameAndStatus(...);
}
if (nome != null) {
  return repo.findByName(...);
}
// ... mais 14
---
var filtro = Specification
    .where(nomeContem(nome))
    .and(statusIgual(status))
    .and(precoEntre(min, max));

return repo.findAll(
    filtro, pageable);
:::

## Specification: o filtro como objeto

```java title="ProductSpecs.java" numbered
public class ProductSpecs {

    public static Specification<Product> nomeContem(String termo) {
        return (root, query, cb) -> termo == null ? null
                : cb.like(cb.lower(root.get("name")),
                          "%" + termo.toLowerCase() + "%");
    }

    public static Specification<Product> statusIgual(Status s) {
        return (root, query, cb) -> s == null ? null
                : cb.equal(root.get("status"), s);
    }

    public static Specification<Product> precoAte(BigDecimal teto) {
        return (root, query, cb) -> teto == null ? null
                : cb.lessThanOrEqualTo(root.get("price"), teto);
    }
}
```

:::anatomy title="Por que devolver `null` é o truque central"
lang: java
code: |
  public static Specification<Product> nomeContem(
          String termo) {
      return (root, query, cb) ->
          termo == null ? null
              : cb.like(root.get("name"), "%" + termo + "%");
  }
notes:
  - { line: 3, text: "A Specification é uma lambda: recebe a raiz, a consulta e um construtor de critérios." }
  - { line: 4, text: "`null` significa *sem restrição* — o Spring Data simplesmente ignora este filtro." }
  - { line: 5, text: "`cb.like` monta o `WHERE` em árvore, não em texto: nada de concatenar SQL." }
:::

O repositório precisa de uma interface a mais:

```java
public interface ProductRepository extends
        JpaRepository<Product, Long>,
        JpaSpecificationExecutor<Product> {
}
```

E o serviço monta o filtro conforme o que chegou:

```java title="ProductService.java" numbered
@Transactional(readOnly = true)
public Page<ProductResponse> buscar(ProductFilter f,
                                    Pageable pageable) {
    Specification<Product> spec = Specification
            .where(ProductSpecs.nomeContem(f.name()))
            .and(ProductSpecs.statusIgual(f.status()))
            .and(ProductSpecs.precoAte(f.maxPrice()));

    return repository.findAll(spec, pageable)
            .map(ProductResponse::of);
}
```

```java title="dto/ProductFilter.java"
public record ProductFilter(
        String name, Status status, BigDecimal maxPrice) {
}
```

O controlador recebe o record direto da query string, sem nenhuma anotação:

```java
@GetMapping
public Page<ProductResponse> listar(
        ProductFilter filtro, Pageable pageable) {
    return service.buscar(filtro, pageable);
}
```

:::story A busca igual à do Google
— A busca está ruim — disse Roberto, na segunda-feira.

— Ruim como?

— Eu digitei "teclad" e não achou nada.

— O senhor digitou incompleto.

— O Google acha.

Marina explicou que o Google tem vinte anos de investimento em indexação,
correção ortográfica, sinônimos e um data center por continente. Roberto
ouviu tudo e fez a pergunta que já estava formada antes da resposta:

— Mas dá para fazer parecido até quinta?

Ficou combinado o possível: busca por trecho do nome, ignorando maiúsculas e
acentos. Levou dois dias.

Na quinta, Roberto testou "tecladdo", com dois dês, não achou nada, e voltou
a mencionar o Google.
:::

:::art caption="Toda busca começa com uma comparação injusta."
src="toda-busca-comeca-com-uma-comparacao-injusta.png"
Charge editorial minimalista: gerente de camisa social apontando para um
monitor onde se lê apenas a palavra "tecladdo" em um campo de busca vazio.
Ao lado, sobre a mesa, uma miniatura de data center gigantesco com o rótulo
"a concorrência", desproporcional em relação a um único servidor pequeno
rotulado "a gente". Uma desenvolvedora sênior observa a cena com expressão
paciente. Fundo branco, poucos elementos, humor visual seco, estética de
revista de tecnologia.
:::

## Por que `LIKE '%termo%'` é lento

```sql
SELECT * FROM product WHERE name LIKE '%teclado%';
```

O índice de um banco relacional é uma estrutura **ordenada pelo início** do
valor. `LIKE 'teclado%'` usa o índice: o banco salta direto para a faixa que
começa com essas letras. `LIKE '%teclado%'` não: o termo pode estar em
qualquer posição, e não há ordenação que ajude. O banco lê tudo.

:::diagram type="blocks" caption="Três estratégias de busca por texto, em ordem de custo e de capacidade."
flow: false
rows:
  - [{ text: "LIKE 'termo%'", note: "usa índice · só prefixo" }]
  - [{ text: "LIKE '%termo%'", note: "varre a tabela · qualquer posição" }]
  - [{ text: "Full-text (tsvector)", note: "índice próprio · radical, ranking" }]
:::

:::tip
Até algumas dezenas de milhares de linhas, `LIKE '%termo%'` é perfeitamente
aceitável — e muito mais simples que a alternativa. Quando deixar de ser, o
PostgreSQL oferece busca *full-text* nativa com `to_tsvector` e índice GIN, e
só então vale considerar um Elasticsearch. Trocar de ferramenta antes de ter
o problema é a forma mais cara de otimizar.
:::

## Acento: o detalhe que ninguém lembra

Em português, `cafe` precisa encontrar `café`. O PostgreSQL resolve com a
extensão `unaccent`:

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;

SELECT * FROM product
WHERE unaccent(lower(name)) LIKE unaccent(lower('%cafe%'));
```

```java title="A mesma ideia com @Query nativa" numbered
@Query(value = """
       SELECT * FROM product
       WHERE unaccent(lower(name))
             LIKE unaccent(lower(concat('%', :termo, '%')))
       """, nativeQuery = true)
Page<Product> buscarSemAcento(@Param("termo") String termo,
                              Pageable pageable);
```

:::pitfall
Nunca monte a consulta concatenando texto:

```java
// JAMAIS
"SELECT * FROM product WHERE name = '" + termo + "'"
```

Um termo com `'; DROP TABLE product; --` deixa de ser uma busca e passa a ser
uma instrução. Isso se chama **injeção de SQL** e é a vulnerabilidade mais
antiga que ainda derruba sistemas em produção. Use sempre parâmetro (`:termo`
ou `?`) — o driver envia o valor separado do comando, e ele nunca é
interpretado como código.
:::

## Qual das três formas usar

| Situação | Ferramenta |
|---|---|
| um ou dois filtros fixos | *query method* pelo nome |
| consulta complexa, mas fixa | `@Query` (JPQL) |
| filtros opcionais combináveis | `Specification` |
| recurso específico do banco | `@Query` nativa |

Tabela: A ordem da tabela é a ordem em que você deve tentar. Só suba um
degrau quando o anterior não couber.

:::summary
- Quem filtra é o banco; filtrar em memória é trazer tudo para descartar
  quase tudo.
- `Specification` monta o `WHERE` por partes e ignora o filtro que veio
  nulo.
- Um `record` de filtro chega direto da query string, sem anotação.
- `LIKE '%termo%'` não usa índice; *full-text* só quando o volume exigir.
- Nunca concatene texto em SQL: use parâmetro.
:::

:::checkpoint
Você escreve filtros combináveis com `Specification`, sabe quando o nome do
método basta, explica por que a busca por trecho é lenta e não escreve SQL
por concatenação.
:::

:::milestone
Fim da Parte 5. A API lista com página, ordena, filtra por três critérios
opcionais, recusa lixo e erra com honestidade. É uma API que outra pessoa
consegue usar sem conversar com você.
:::

:::exercise level=1
Acrescente um filtro opcional por `status` na busca e teste as quatro
combinações: sem filtro, só nome, só status, os dois.

:::answer
A graça está no teste sem filtro nenhum: como as duas `Specification`
devolvem `null`, o `WHERE` sai vazio e a consulta vira um `findAll`
paginado. Nenhum `if` foi necessário para isso acontecer.
:::

:::exercise level=2
Escreva uma `Specification` `comEstoque()` que filtre `quantity > 0` e
combine-a com as outras. Depois ative `show-sql` e confira o `WHERE` gerado.

:::answer
```java
public static Specification<Product> comEstoque() {
    return (root, query, cb) ->
            cb.greaterThan(root.get("quantity"), 0);
}
```
No log você vê um único `SELECT` com todas as condições unidas por `and` — a
prova de que o filtro foi para o banco e não para o `for`.
:::

:::exercise level=3
Meça. Cadastre cinquenta mil produtos, rode a busca por trecho com
`EXPLAIN ANALYZE` e depois crie um índice GIN com `pg_trgm`. Compare.

:::answer
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_product_name_trgm
    ON product USING gin (name gin_trgm_ops);
```
O `pg_trgm` indexa trigramas — pedaços de três letras — e é uma das poucas
formas de fazer `LIKE '%termo%'` usar índice. O plano deixa de ser `Seq Scan`
e passa a `Bitmap Index Scan`. Medir antes e depois é o hábito que separa
otimização de superstição.
:::
