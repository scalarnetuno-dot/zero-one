---
title: "Paginação e ordenação"
number: 27
part: p5
kicker: "`GET /products` com um milhão de itens é um ataque de negação de serviço que você escreveu sozinho."
goal: >-
  Paginar e ordenar uma listagem com `Pageable`, entender o custo de `OFFSET`
  e devolver metadados de paginação ao cliente.
---

O `GET /products` do capítulo 23 devolve tudo. Com cem produtos ninguém nota;
com cem mil, a consulta demora, o JSON tem trinta megabytes e a memória do
servidor sobe até o limite. Este capítulo resolve com dois parâmetros.

## `Pageable`: o Spring já sabe fazer

```java title="ProductController.java" numbered
@GetMapping
public Page<ProductResponse> listar(Pageable pageable) {
    return service.listar(pageable);
}
```

```java title="ProductService.java" numbered
@Transactional(readOnly = true)
public Page<ProductResponse> listar(Pageable pageable) {
    return repository.findAll(pageable)
            .map(ProductResponse::of);
}
```

Nenhuma anotação nova. O Spring reconhece o parâmetro `Pageable`, lê
`page`, `size` e `sort` da query string e monta o objeto:

:::http title="Três parâmetros que você não precisou declarar"
GET /products?page=0&size=10&sort=price,desc
---
200 OK

{
  "content": [
    { "id": 7, "name": "Monitor 27", "price": 1899.00 },
    { "id": 3, "name": "Teclado", "price": 349.90 }
  ],
  "pageable": { "pageNumber": 0, "pageSize": 10 },
  "totalElements": 342,
  "totalPages": 35,
  "first": true,
  "last": false,
  "numberOfElements": 2
}
:::

`Page` não é só a lista: é a lista **mais** os metadados que o cliente precisa
para desenhar a navegação. O `.map()` no serviço converte cada entidade em DTO
sem perder nenhum desses campos.

## O SQL que sai disso

```sql title="Duas consultas, não uma" numbered
SELECT * FROM product
ORDER BY price DESC
LIMIT 10 OFFSET 0;

SELECT count(*) FROM product;
```

A segunda consulta existe para preencher `totalElements`. Se você não precisa
do total — e muitas telas não precisam —, troque `Page` por `Slice` e economize
uma contagem em cada requisição:

```java
Slice<Product> findByStatus(Status status, Pageable pageable);
```

| Tipo | Traz | Custo |
|---|---|---|
| `List` | tudo | perigoso |
| `Slice` | página + "tem próxima?" | uma consulta |
| `Page` | página + total + nº de páginas | duas consultas |

Tabela: `Page` é o padrão confortável. `Slice` é a escolha consciente quando a
contagem custa caro.

## Defina o padrão e o teto

```java title="ProductController.java" numbered
@GetMapping
public Page<ProductResponse> listar(
        @PageableDefault(size = 20, sort = "name")
        Pageable pageable) {
    return service.listar(pageable);
}
```

```properties title="application.properties"
spring.data.web.pageable.default-page-size=20
spring.data.web.pageable.max-page-size=100
```

:::pitfall
Sem `max-page-size`, `GET /products?size=1000000` volta a ser o problema que
você acabou de resolver — e agora com um parâmetro que qualquer pessoa pode
descobrir. O teto não é detalhe de configuração: é uma medida de segurança.
:::

:::story A Black Friday do GET /products
À meia-noite da Black Friday, onze mil produtos estavam cadastrados e o
aplicativo fazia exatamente o que tinha sido programado para fazer: pedir a
lista de produtos.

`GET /products`. Sem parâmetro nenhum. Sem limite nenhum. Onze mil itens, com
descrição completa, a cada abertura de tela.

O primeiro minuto teve quatro mil aberturas.

A API não caiu por falta de processador. Caiu por memória: cada requisição
carregava onze mil objetos para montar um JSON de trinta megabytes, e o
coletor de lixo passou a trabalhar mais que a aplicação.

Marina subiu a correção às 00h19 — um `Pageable` no controlador e um teto de
cem itens por página. Três linhas.

Roberto perguntou, na retrospectiva, por que aquelas três linhas não estavam
lá desde o começo.

Foi a melhor pergunta que ele fez no trimestre.
:::

## O custo escondido do `OFFSET`

:::diagram type="flowchart" caption="O banco descarta tudo que vem antes do OFFSET — e cobra por isso."
nodes:
  - { id: q,   type: io,      text: "LIMIT 10 OFFSET 100000" }
  - { id: ord, type: process, text: "ordena as 100.010 primeiras" }
  - { id: sk,  type: process, text: "descarta 100.000" }
  - { id: r,   type: start,   text: "devolve 10" }
edges:
  - { from: q,   to: ord }
  - { from: ord, to: sk }
  - { from: sk,  to: r }
:::

`OFFSET` não é um atalho: o banco precisa ordenar e percorrer tudo que vem
antes para saber onde começar. A página 1 é instantânea; a página 10.000 é
lenta, sempre, em qualquer banco relacional.

A alternativa chama-se **paginação por cursor** (ou *keyset pagination*):

:::compare left="Por offset" right="Por cursor"
SELECT * FROM product
ORDER BY id
LIMIT 10
OFFSET 100000;
---
SELECT * FROM product
WHERE id > 100000
ORDER BY id
LIMIT 10;
:::

A segunda usa o índice e tem custo constante, independentemente de quão longe
você está. O preço é não poder "saltar para a página 500" — você só avança e
retrocede. Para *feed* infinito e exportação, é a escolha certa.

:::trivia
É por isso que serviços como Twitter, Stripe e GitHub não têm páginas
numeradas nas suas APIs: eles devolvem um `next_cursor`. A decisão não é
estética. Com bilhões de registros, `OFFSET` deixaria a última página
inalcançável.
:::

## Ordenação e o que ela pode expor

```text title="Todas estas formas funcionam"
?sort=name                    → nome crescente
?sort=price,desc              → preço decrescente
?sort=status&sort=price,desc  → dois critérios
```

:::pitfall
`sort` aceita **qualquer nome de campo da entidade** — inclusive um que você
não queria que existisse no contrato público. `?sort=custoDeCompra` não
devolve o campo, mas revela que ele existe. Em APIs públicas, valide a lista
de campos ordenáveis:

```java
private static final Set<String> ORDENAVEIS =
        Set.of("name", "price", "createdAt");
```
:::

E outra armadilha, esta silenciosa:

:::pitfall
Paginar **sem** ordenação explícita não garante ordem estável. Sem `ORDER BY`,
o banco pode devolver as linhas em qualquer ordem, e um mesmo registro pode
aparecer na página 1 e na página 2 — ou em nenhuma. Sempre ordene por algo
único (ou termine a ordenação com `id`).
:::

## O contrato final da listagem

| Parâmetro | Padrão | Teto |
|---|---|---|
| `page` | `0` | — |
| `size` | `20` | `100` |
| `sort` | `name,asc` | campos permitidos |

Tabela: A listagem do projeto. Documentar isso é o trabalho do capítulo 38.

:::summary
- `Pageable` como parâmetro do controlador lê `page`, `size` e `sort` sozinho.
- `Page` traz total e número de páginas ao custo de uma consulta extra;
  `Slice` não.
- Defina tamanho padrão e **teto** — o teto é segurança.
- `OFFSET` fica mais caro conforme a página avança; cursor tem custo constante.
- Paginação sem ordenação estável devolve resultado inconsistente.
:::

:::checkpoint
Você pagina e ordena uma listagem, escolhe entre `Page` e `Slice`, limita o
tamanho da página e sabe explicar por que a página 10.000 é lenta.
:::

:::milestone
A listagem do projeto é paginada, ordenável e com teto. Falta poder procurar —
e é o próximo capítulo.
:::

:::exercise level=1
Pagine a listagem de categorias com tamanho padrão 10, ordenada por nome.

:::answer
```java
@GetMapping
public Page<CategoryResponse> listar(
        @PageableDefault(size = 10, sort = "name")
        Pageable pageable) {
    return service.listar(pageable);
}
```
:::

:::exercise level=2
Devolva, em vez de `Page`, um record próprio com apenas `content`, `page`,
`size` e `totalElements`. Explique por que isso pode valer a pena.

:::answer
```java
public record PageResponse<T>(
        List<T> content, int page, int size, long totalElements) {

    public static <T> PageResponse<T> of(Page<T> p) {
        return new PageResponse<>(p.getContent(),
                p.getNumber(), p.getSize(), p.getTotalElements());
    }
}
```
Vale porque o JSON do `Page` do Spring Data expõe a estrutura interna do
framework (`pageable.sort.sorted`, `unpaged`…) e **mudou de formato entre
versões**. Um DTO próprio é um contrato que você controla — a mesma lição do
capítulo 24, aplicada à paginação.
:::

:::exercise level=3
Implemente paginação por cursor para `GET /products`: receba `afterId` e
devolva os 20 seguintes. Compare o SQL gerado com o da versão por offset.

:::answer
```java
@Query("""
       SELECT p FROM Product p
       WHERE p.id > :afterId
       ORDER BY p.id
       """)
List<Product> pagina(@Param("afterId") Long afterId,
                     Pageable limite);
```
Chamado com `PageRequest.ofSize(20)`. O SQL vira
`WHERE id > ? ORDER BY id LIMIT 20` — um acesso por índice, sem descarte. O
que você perde: saber quantas páginas existem, e a capacidade de pular para
uma página arbitrária.
:::
