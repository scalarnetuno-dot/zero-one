---
title: "Validação"
number: 25
part: p5
kicker: "Toda entrada é hostil até prova em contrário — e a prova é uma anotação."
goal: >-
  Validar entrada com Bean Validation, ligar a validação com `@Valid`, escrever
  uma restrição própria e decidir o que validar em cada camada.
---

A API do capítulo 24 aceita um produto com nome vazio, preço negativo e
estoque de menos duzentas unidades. Ela grava tudo sem reclamar, porque nada
verifica nada. Este capítulo fecha essa porta com quatro anotações.

## O problema, em uma requisição

:::http title="O que a API aceita hoje"
POST /products
Content-Type: application/json

{
  "name": "",
  "price": -50,
  "quantity": -200
}
---
201 Created

{ "id": 8, "name": "", "price": -50, "quantity": -200 }
:::

Um produto que não existe no mundo real acabou de existir no seu banco. E ele
vai aparecer na listagem, no relatório e na fatura.

:::story Menos cinquenta reais
Seu Antônio ganhou acesso de cadastro para colocar os produtos da loja dele
no marketplace da Aurora. Cadastrou dezoito itens em uma tarde, sozinho, sem
ajuda de ninguém. Ficou orgulhoso.

No décimo nono, digitou o preço no campo errado — colocou o desconto onde ia
o valor — e salvou um produto por menos cinquenta reais.

A API aceitou. O banco aceitou. A vitrine mostrou. E, como preço negativo
ordena antes de todos os outros, o produto foi parar em primeiro lugar na
listagem "menor preço".

Onze pessoas compraram. O sistema calculou, para cada uma delas, um total de
pedido negativo — e o gateway de pagamento, que era mais bem escrito que a
API da Aurora, recusou as onze transações com a mesma mensagem educada.

— Ele não errou — disse Marina, na reunião. — A gente é que deixou.
:::

## Bean Validation

```xml title="pom.xml"
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
</dependency>
```

```java title="dto/ProductRequest.java" numbered
package com.loja.catalog.product.dto;

import jakarta.validation.constraints.*;
import java.math.BigDecimal;

public record ProductRequest(

        @NotBlank(message = "nome é obrigatório")
        @Size(max = 120, message = "nome: até 120 caracteres")
        String name,

        @Size(max = 2000)
        String description,

        @NotNull(message = "preço é obrigatório")
        @Positive(message = "preço deve ser positivo")
        @Digits(integer = 8, fraction = 2)
        BigDecimal price,

        @NotNull
        @PositiveOrZero(message = "estoque não pode ser negativo")
        Integer quantity) {
}
```

E uma palavra no controlador liga tudo:

```java title="ProductController.java" numbered
@PostMapping
public ResponseEntity<ProductResponse> criar(
        @Valid @RequestBody ProductRequest dados) {
    ...
}
```

:::anatomy title="Como a validação entra no caminho da requisição"
lang: java
code: |
  @PostMapping
  public ResponseEntity<ProductResponse> criar(
          @Valid @RequestBody ProductRequest dados) {
      return ...;
  }
notes:
  - { line: 3, text: "`@RequestBody` converte o JSON no record — isso já acontecia." }
  - { line: 3, text: "`@Valid` roda as anotações do record **antes** de o método executar." }
  - { line: 3, text: "Se falhar, o método nem é chamado: o Spring lança `MethodArgumentNotValidException`." }
  - { line: 4, text: "Dentro do método, `dados` é confiável. Nenhum `if` de validação aqui." }
:::

## As anotações que você vai usar

| Anotação | Garante | Serve para |
|---|---|---|
| `@NotNull` | não é nulo | qualquer tipo |
| `@NotBlank` | não é nulo nem só espaços | texto |
| `@NotEmpty` | não é nulo nem vazio | coleção, texto |
| `@Size(min, max)` | tamanho | texto, coleção |
| `@Positive` / `@PositiveOrZero` | sinal | número |
| `@Min` / `@Max` | faixa | número inteiro |
| `@DecimalMin` / `@Digits` | faixa e casas | decimal |
| `@Email` | formato de e-mail | texto |
| `@Pattern(regexp)` | expressão regular | texto |
| `@Past` / `@Future` | momento | data |

Tabela: As dez que resolvem quase tudo. `@NotBlank` para texto e `@NotNull`
para o resto é a regra prática que evita o erro mais comum.

:::pitfall
`@NotNull` em uma `String` aceita `""` — o texto vazio não é nulo. Para texto
obrigatório, a anotação certa é `@NotBlank`, que recusa nulo, vazio e "só
espaços". Confundir as duas é o defeito de validação número um.
:::

## O que o cliente recebe

:::http title="Agora a API recusa — mas a mensagem ainda é feia"
POST /products
Content-Type: application/json

{ "name": "", "price": -50, "quantity": -200 }
---
400 Bad Request
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:30:00.000+00:00",
  "status": 400,
  "errors": [ "nome é obrigatório", "preço deve ser maior que zero" ],
  "path": "/products"
}
:::

O status já está certo — `400` é culpa do cliente. Mas o corpo é o formato
padrão do Spring, que muda entre versões e não diz **qual campo** falhou de
forma estruturada. O capítulo 26 padroniza isso.

## Validação própria

Quando a regra não cabe em uma anotação existente, você escreve a sua. Duas
peças: a anotação e o validador.

```java title="SkuValido.java" numbered
@Documented
@Constraint(validatedBy = SkuValidator.class)
@Target({ElementType.FIELD, ElementType.RECORD_COMPONENT})
@Retention(RetentionPolicy.RUNTIME)
public @interface SkuValido {
    String message() default "SKU inválido";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}
```

```java title="SkuValidator.java" numbered
public class SkuValidator
        implements ConstraintValidator<SkuValido, String> {

    private static final Pattern FORMATO =
            Pattern.compile("^[A-Z]{3}-\\d{4}$");

    @Override
    public boolean isValid(String valor,
                           ConstraintValidatorContext ctx) {
        if (valor == null) {
            return true;      // nulidade é assunto do @NotNull
        }
        return FORMATO.matcher(valor).matches();
    }
}
```

```java
@SkuValido
private String sku;     // aceita "TEC-0042"
```

:::key
Um validador **não** deve checar nulo. Deixar `null` passar e delegar a
obrigatoriedade ao `@NotNull` é a convenção da especificação — ela permite
combinar as anotações sem duplicar regra.
:::

## Onde validar: as três camadas

:::diagram type="blocks" caption="Cada camada valida uma coisa diferente — e as três são necessárias."
rows:
  - [{ text: "DTO (@Valid)", note: "formato: obrigatório, tamanho, sinal" }]
  - [{ text: "Service", note: "regra: nome duplicado, estoque suficiente" }]
  - [{ text: "Banco (NOT NULL, UNIQUE)", note: "a última linha de defesa" }]
:::

| Camada | Valida | Exemplo |
|---|---|---|
| DTO | forma da entrada | "preço é obrigatório e positivo" |
| Service | regra de negócio | "não existe outro produto com este nome" |
| Banco | integridade | `UNIQUE`, `NOT NULL`, `FOREIGN KEY` |

Tabela: O DTO não consulta o banco; o serviço não checa formato; o banco não
conhece a regra. Cada um no seu lugar.

:::pitfall
A tentação é validar unicidade no DTO, com um validador que consulta o banco.
Funciona e cria dois problemas: o DTO passa a depender do repositório (e o
teste do DTO passa a precisar de banco), e a verificação continua sujeita a
condição de corrida — entre a checagem e o `INSERT`, outra requisição pode
inserir o mesmo nome. É por isso que a restrição `UNIQUE` do banco não é
opcional.
:::

## Validando objetos aninhados e listas

```java title="@Valid desce um nível se você pedir" numbered
public record OrderRequest(
        @NotNull Long customerId,

        @NotEmpty(message = "o pedido precisa de itens")
        @Valid                     // valida cada item da lista
        List<OrderItemRequest> items) {
}

public record OrderItemRequest(
        @NotNull Long productId,
        @NotNull @Positive Integer quantity) {
}
```

Sem o `@Valid` na lista, as anotações de `OrderItemRequest` são ignoradas. É
um esquecimento silencioso e comum.

:::summary
- Bean Validation valida a **forma** da entrada por anotação no DTO.
- `@Valid` no parâmetro liga a validação — sem ele, nada roda.
- `@NotBlank` para texto obrigatório; `@NotNull` para os outros tipos.
- Validador próprio não checa nulo.
- Formato no DTO, regra no serviço, integridade no banco.
- `@Valid` em coleção é obrigatório para validar os itens.
:::

:::checkpoint
Você valida entrada com as dez anotações principais, liga com `@Valid`,
escreve uma restrição própria e sabe o que pertence a cada camada.
:::

:::milestone
A API recusa lixo: nome vazio, preço negativo, estoque negativo. O quarto
defeito do capítulo 17 está resolvido — mas a mensagem de erro que o cliente
recebe ainda é a do framework, e o capítulo 26 conserta isso.
:::

:::exercise level=1
Valide `CategoryRequest`: nome obrigatório com no máximo 80 caracteres,
descrição opcional com no máximo 500.

:::answer
```java
public record CategoryRequest(
        @NotBlank @Size(max = 80) String name,
        @Size(max = 500) String description) {
}
```
:::

:::exercise level=2
Faça o `PUT` também validar. Depois responda: por que faz sentido usar o mesmo
`ProductRequest` no `POST` e no `PUT`, e em que situação isso deixaria de
fazer sentido?

:::answer
Faz sentido porque `PUT` substitui o recurso inteiro — os mesmos campos
obrigatórios. Deixaria de fazer sentido em uma API com atualização parcial
(`PATCH`), onde todo campo é opcional: aí o `@NotBlank` do `POST` recusaria
uma alteração legítima de preço que não mandou o nome. Nesse caso são dois
DTOs.
:::

:::exercise level=3
Escreva uma validação de classe (não de campo) que garanta que `price` não
seja maior que `1_000_000` quando `quantity` for maior que `100`. Dica:
`@Constraint` em `ElementType.TYPE`.

:::answer
A anotação vai no tipo e o validador recebe o objeto inteiro, o que permite
comparar dois campos:

```java
public class LoteCoerenteValidator implements
        ConstraintValidator<LoteCoerente, ProductRequest> {
    public boolean isValid(ProductRequest r,
                           ConstraintValidatorContext c) {
        if (r.quantity() == null || r.price() == null) {
            return true;
        }
        BigDecimal teto = new BigDecimal("1000000");
        return r.quantity() <= 100
                || r.price().compareTo(teto) <= 0;
    }
}
```
Validação que envolve dois campos **precisa** ser de classe. Tentar fazê-la em
um campo é o caminho para um validador que não tem acesso ao que precisa.
:::
