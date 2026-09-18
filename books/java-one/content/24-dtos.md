---
title: "DTOs"
number: 24
part: p4
kicker: "O cliente não precisa saber como a sua tabela é desenhada. E você não quer que ele dependa disso."
goal: >-
  Separar entidade de contrato com records de entrada e saída, converter entre
  os dois e listar três problemas concretos que a exposição direta causa.
---

Até agora o `ProductController` devolve a entidade `Product`. Funciona, é
menos código e cria um acoplamento que cobra caro. Este capítulo é sobre uma
fronteira.

## Três problemas concretos

**1. Renomear uma coluna quebra o cliente.** Se `name` vira `title` no banco,
o JSON muda com ele — e o aplicativo de celular que está na loja há seis meses
para de funcionar.

**2. Você expõe o que não queria.** Todo campo novo na entidade aparece na
resposta automaticamente. Um dia alguém acrescenta `custoDeCompra` e a
margem da loja passa a ser pública.

**3. A entrada aceita o que não deveria.** `POST /products` com
`{"id": 9999}` tenta gravar um id escolhido pelo cliente. Com
`{"createdAt": "1990-01-01"}`, reescreve a data de criação.

:::pitfall
O problema 3 tem nome e histórico: *mass assignment*. Em 2012, alguém o usou
no GitHub para se adicionar como administrador de um repositório público — via
um campo que a API aceitava sem querer. A correção não é validar mais: é
**não aceitar** o campo.
:::

:::story O campo que ninguém queria mostrar
O campo se chamava `custoDeCompra` e foi acrescentado à entidade numa
terça-feira, para um relatório interno de margem.

O relatório ficou pronto. Ninguém lembrou que a API devolvia a entidade
inteira.

Na quinta, um desenvolvedor de um parceiro — daqueles que integram o catálogo
em um comparador de preços — mandou um e-mail simpático perguntando se o
campo `custoDeCompra` era mesmo o custo de compra, porque, se fosse, ficava
fácil calcular a margem da Aurora em cada item.

O e-mail era educado. Era também o pior e-mail que Roberto recebeu naquele
trimestre.
:::

:::art caption="Expor a entidade é publicar toda coluna que alguém acrescentar no futuro."
src="expor-a-entidade-e-publicar-toda-coluna-que-alguem-acrescentar-no-futuro.png"
Charge editorial minimalista: janela de resposta JSON desenhada como se fosse
a vitrine de uma loja, com vários campos visíveis em prateleiras; um deles,
destacado em vermelho, diz "custoDeCompra". Do lado de fora da vitrine, um
desenvolvedor de outra empresa observa com sorriso discreto e uma calculadora
na mão. Do lado de dentro, um gerente de camisa social tenta cobrir aquele
campo com as duas mãos. Fundo branco, poucos elementos, humor seco, estética
editorial de tecnologia.
:::

## Dois records, dois contratos

```java title="dto/ProductRequest.java" numbered
package com.loja.catalog.product.dto;

import java.math.BigDecimal;

public record ProductRequest(
        String name,
        String description,
        BigDecimal price,
        Integer quantity) {
}
```

```java title="dto/ProductResponse.java" numbered
public record ProductResponse(
        Long id,
        String name,
        String description,
        BigDecimal price,
        Integer quantity,
        Status status,
        Instant createdAt) {

    public static ProductResponse of(Product p) {
        return new ProductResponse(
                p.getId(),
                p.getName(),
                p.getDescription(),
                p.getPrice(),
                p.getQuantity(),
                p.getStatus(),
                p.getCreatedAt());
    }
}
```

Repare na assimetria: a **entrada** não tem `id`, `status` nem `createdAt` —
esses três não são do cliente. A **saída** tem tudo que o cliente precisa e
nada além.

:::key
Entrada e saída são contratos diferentes e merecem tipos diferentes. Usar o
mesmo record para os dois é a versão elegante do mesmo erro: ou a entrada
aceita campos que não deveria, ou a saída esconde campos que deveria mostrar.
:::

:::diagram type="blocks" caption="O DTO é a fronteira: o formato do JSON para de ser o formato da tabela."
rows:
  - [{ text: "Cliente", note: "JSON" }]
  - [{ text: "ProductRequest / ProductResponse", note: "contrato público, estável" }]
  - [{ text: "Product (entidade)", note: "desenho interno, livre para mudar" }]
  - [{ text: "tabela product", note: "colunas" }]
:::

## A conversão

```java title="ProductService.java (com DTO na fronteira)" numbered
@Transactional(readOnly = true)
public List<ProductResponse> listar() {
    return repository.findAll().stream()
            .map(ProductResponse::of)
            .toList();
}

@Transactional
public ProductResponse criar(ProductRequest dados) {
    if (repository.existsByNameIgnoreCase(dados.name())) {
        throw new DuplicateProductException(dados.name());
    }
    Product novo = new Product(
            dados.name(), dados.price(), dados.quantity());
    novo.setDescription(dados.description());
    return ProductResponse.of(repository.save(novo));
}
```

`ProductResponse::of` é a referência de método do capítulo 14 fazendo o
trabalho: um stream de entidades vira um stream de respostas em uma linha.

:::pitfall
Onde converter é uma decisão de projeto com duas escolas. Converter no
**serviço** (como aqui) mantém o controlador trivial e faz o serviço falar o
vocabulário do contrato. Converter no **controlador** deixa o serviço puro em
termos de domínio, e é a escolha preferida em projetos maiores. Escolha uma e
seja consistente: o que dói de verdade é metade em cada lugar.
:::

## O controlador final da Parte 4

```java title="ProductController.java" numbered
@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<ProductResponse> listar() {
        return service.listar();
    }

    @GetMapping("/{id}")
    public ProductResponse buscar(@PathVariable Long id) {
        return service.buscar(id);
    }

    @PostMapping
    public ResponseEntity<ProductResponse> criar(
            @RequestBody ProductRequest dados) {
        ProductResponse criado = service.criar(dados);
        return ResponseEntity
                .created(URI.create("/products/" + criado.id()))
                .body(criado);
    }
}
```

:::http title="O contrato público, agora estável"
POST /products
Content-Type: application/json

{
  "name": "Teclado mecânico",
  "description": "ABNT2, switch marrom",
  "price": 349.90,
  "quantity": 12
}
---
201 Created
Location: /products/7

{
  "id": 7,
  "name": "Teclado mecânico",
  "description": "ABNT2, switch marrom",
  "price": 349.90,
  "quantity": 12,
  "status": "ATIVO",
  "createdAt": "2026-03-14T18:22:10Z"
}
:::

Repare: o cliente enviou quatro campos e recebeu sete. O `id`, o `status` e o
`createdAt` foram decididos pelo servidor — é assim que deve ser.

## Ajustando o JSON sem tocar na entidade

```java title="Anotações do Jackson no DTO" numbered
public record ProductResponse(
        Long id,
        @JsonProperty("nome") String name,
        BigDecimal price,
        @JsonInclude(JsonInclude.Include.NON_NULL)
        String description) {
}
```

Como o DTO é uma classe só sua, você pode renomear campos, esconder nulos e
formatar datas sem que nada disso encoste na entidade ou no banco. Essa
liberdade é o ganho concreto da separação.

:::trivia
A sigla DTO vem de *Data Transfer Object*, catalogada por Martin Fowler em
2002 para um problema diferente: reduzir o número de chamadas remotas em
sistemas distribuídos. O nome ficou, o motivo mudou. Hoje ninguém usa DTO
para economizar chamada — usa para desacoplar contrato de modelo.
:::

## Quando o DTO não vale a pena

Seja honesto sobre o custo: são duas classes, duas conversões e mais linhas por
endpoint. Em um projeto interno pequeno, com um único cliente que você mesmo
mantém, expor a entidade é uma decisão defensável.

A pergunta que decide: **existe alguém do outro lado que você não controla?**
Se a resposta é sim — um app publicado, um parceiro, um time diferente —, o
DTO deixa de ser opcional.

:::summary
- Expor a entidade acopla o cliente ao banco, vaza campos e aceita campos que
  não deveria.
- Entrada e saída são contratos diferentes: dois records.
- Entrada não tem `id`, `status` nem datas de sistema.
- Converta em um só lugar, e sempre no mesmo.
- Anotação do Jackson mora no DTO, nunca na entidade.
:::

:::checkpoint
Você separa entidade de contrato com records, converte com um método de
fábrica, justifica a separação com três problemas concretos e sabe quando ela
não se paga.
:::

:::milestone
Fim da Parte 4. A API tem CRUD completo, três camadas, banco PostgreSQL e um
contrato público que não é o desenho da tabela. Três dos quatro defeitos do
capítulo 17 estão resolvidos — falta a validação, que abre a Parte 5.
:::

:::exercise level=1
Escreva `CategoryRequest` e `CategoryResponse` e ajuste o
`CategoryController` para usá-los.

:::answer
```java
public record CategoryRequest(String name, String description) { }

public record CategoryResponse(Long id, String name,
                               String description) {
    public static CategoryResponse of(Category c) {
        return new CategoryResponse(c.getId(), c.getName(),
                c.getDescription());
    }
}
```
:::

:::exercise level=2
Crie `ProductSummary`, um record com apenas `id`, `name` e `price`, para a
listagem. Explique o ganho.

:::answer
Um `GET /products` de mil itens deixa de trafegar descrição, data e status —
talvez metade dos bytes. Em uma listagem de catálogo aberta em rede móvel,
isso é a diferença entre rápido e lento. É comum uma API ter um DTO "resumo"
para lista e um "completo" para o detalhe.
:::

:::exercise level=3
Envie `POST /products` com `{"name":"X","price":10,"id":9999}` e observe o
que acontece com o campo `id`. Depois explique por que este é o resultado
correto.

:::answer
O campo é **ignorado**: `ProductRequest` não o declara, e o Jackson descarta
propriedades desconhecidas por padrão. O produto é criado com o id da
sequência do banco. Correto porque o servidor é a autoridade sobre a
identidade dos seus recursos — aceitar um id do cliente abriria a porta para
colisão e para escrita em cima de registro existente.
:::
