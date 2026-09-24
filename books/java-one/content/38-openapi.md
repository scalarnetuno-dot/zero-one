---
title: "Swagger e OpenAPI"
number: 38
part: p9
kicker: "Uma API que ninguém sabe usar não existe. E documentação escrita à mão envelhece em uma semana."
goal: >-
  Gerar documentação OpenAPI a partir do código, enriquecê-la com anotações e
  entender por que documentação separada do código sempre mente.
---

A API da Aurora Comércio tem onze endpoints, quatro status possíveis por
rota, três filtros opcionais e dois papéis de acesso. Nada disso está escrito
em lugar nenhum — exceto neste livro.

## Uma dependência, e a documentação existe

```xml title="pom.xml"
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.6.0</version>
</dependency>
```

Reinicie e abra `http://localhost:8080/swagger-ui.html`. Está tudo lá: cada
endpoint, cada parâmetro, cada campo de cada DTO, com tipo e obrigatoriedade.

Ninguém escreveu nada.

:::key
O springdoc lê o que já existe — `@GetMapping`, `@RequestBody`, `@NotBlank`,
o tipo de retorno — e monta a especificação a partir disso. É documentação
**derivada do código**, e por isso ela não tem como estar desatualizada em
relação ao código.
:::

## OpenAPI, Swagger e a confusão de nomes

| Nome | O que é |
|---|---|
| **OpenAPI** | a especificação: um JSON que descreve a API |
| **Swagger UI** | a página que lê esse JSON e desenha a interface |
| **springdoc** | a biblioteca que gera o JSON a partir do seu código |

Tabela: Swagger era o nome do formato até 2016, quando foi doado e rebatizado
de OpenAPI. O nome antigo ficou na ferramenta.

```text title="Dois endereços que passam a existir"
/swagger-ui.html          a interface
/v3/api-docs              o JSON da especificação
```

O segundo é o que importa de verdade: com ele, um cliente gera código
automaticamente em qualquer linguagem, um teste de contrato verifica se a
API mudou, e uma ferramenta de API *gateway* importa as rotas.

## Enriquecendo o que o código não diz

O código diz o formato. Ele não diz o significado:

```java title="ProductController.java" numbered
@Tag(name = "Produtos",
     description = "Catálogo da loja")
@RestController
@RequestMapping("/products")
public class ProductController {

    @Operation(
        summary = "Busca um produto pelo id",
        description = "Devolve o produto ativo ou inativo. "
                    + "Não exige autenticação.")
    @ApiResponses({
        @ApiResponse(responseCode = "200",
                     description = "encontrado"),
        @ApiResponse(responseCode = "404",
                     description = "id não existe",
                     content = @Content(schema =
                         @Schema(implementation = ApiError.class)))
    })
    @GetMapping("/{id}")
    public ProductResponse buscar(
            @Parameter(description = "id do produto", example = "7")
            @PathVariable Long id) {
        return service.buscar(id);
    }
}
```

:::pitfall
Anotar todos os endpoints com `@Operation`, `@ApiResponse` e `@Parameter`
dobra o tamanho do controlador e afoga o código em metadado. O equilíbrio
prático: deixe o springdoc inferir o comum e anote só o que ele **não tem
como saber** — o significado do recurso, o motivo de um `409`, um exemplo de
valor.
:::

## Documentando o DTO, que é onde o cliente olha

```java title="dto/ProductRequest.java" numbered
@Schema(description = "Dados para cadastrar um produto")
public record ProductRequest(

        @Schema(description = "Nome exibido no catálogo",
                example = "Teclado mecânico ABNT2")
        @NotBlank @Size(max = 120)
        String name,

        @Schema(description = "Preço de venda em reais",
                example = "349.90")
        @NotNull @Positive
        BigDecimal price,

        @Schema(description = "Unidades em estoque", example = "12")
        @NotNull @PositiveOrZero
        Integer quantity) {
}
```

As anotações de validação do capítulo 25 já apareciam na documentação
sozinhas — `@NotBlank` vira `required: true`, `@Size(max = 120)` vira
`maxLength: 120`. O `@Schema` acrescenta o que falta: o exemplo e a frase em
português.

## O botão de autorizar

```java title="config/OpenApiConfig.java" numbered
@Configuration
public class OpenApiConfig {

    @Bean
    OpenAPI api() {
        return new OpenAPI()
            .info(new Info()
                .title("Aurora Comércio — Catálogo")
                .version("1.0")
                .description("API de produtos, pedidos e clientes."))
            .addSecurityItem(
                new SecurityRequirement().addList("bearer"))
            .components(new Components()
                .addSecuritySchemes("bearer",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }
}
```

Com isso, a interface ganha um botão **Authorize**: cola-se o token do
capítulo 32 e todas as chamadas de teste passam a enviá-lo. É o que torna a
página útil de verdade — dá para exercitar a API inteira sem `curl`.

:::pitfall
`/swagger-ui.html` e `/v3/api-docs` são rotas como quaisquer outras: com o
Spring Security ligado, elas exigem autenticação e o navegador mostra um
`401` em branco. Libere-as explicitamente — e, em produção, considere
desligar a interface e manter só o JSON, ou proteger as duas. Um mapa
detalhado da sua API é útil para quem integra e também para quem ataca.
:::

```java title="SecurityConfig.java (acréscimo)"
.requestMatchers("/swagger-ui/**", "/swagger-ui.html",
                 "/v3/api-docs/**").permitAll()
```

## O que a documentação gerada não resolve

Ela descreve **o que** cada endpoint recebe e devolve. Não descreve:

- em que ordem chamar as coisas (criar cliente antes do pedido);
- o que significa cada status de negócio;
- limites de uso, versionamento, política de depreciação.

Isso continua sendo texto escrito por gente — mas em um `README.md` no
repositório, versionado junto do código, e não em um documento solto que
ninguém sabe onde mora.

:::story A documentação em Word
Existia um arquivo. `API_Aurora_v3_FINAL_revisado_2.docx`, em uma pasta
compartilhada, com quarenta e uma páginas.

Foi escrito com carinho por alguém que não trabalha mais na empresa.

O parceiro que integrava o catálogo usava aquele arquivo como referência e
mandava e-mails educados toda semana perguntando por que o campo `estoque`
não existia na resposta. Ele existia — chamava-se `quantity` desde o capítulo
24, e o documento nunca soube.

Quando o springdoc entrou, Marina mandou o link do `/swagger-ui.html` para o
parceiro e apagou o `.docx` da pasta compartilhada.

Roberto perguntou se não era arriscado apagar a documentação.

— A gente não apagou a documentação — ela disse. — A gente apagou uma ficção
sobre o sistema que trinta pessoas acreditavam ser documentação.
:::

:::summary
- O springdoc gera a especificação OpenAPI a partir do código e das
  anotações de validação.
- Swagger UI é a interface; `/v3/api-docs` é o que as ferramentas consomem.
- Anote só o que o código não tem como dizer: significado, exemplo, motivo
  do erro.
- Configure o esquema `bearer` para poder testar autenticado na própria
  página.
- Libere as rotas da documentação na segurança — e pense duas vezes antes de
  expô-las em produção.
:::

:::checkpoint
Você gera a documentação automaticamente, enriquece os pontos que importam,
libera as rotas e consegue exercitar a API inteira pelo navegador.
:::

:::milestone
A API está documentada por ela mesma. Qualquer pessoa com o link consegue
entender e testar os onze endpoints sem falar com você — que é a definição
prática de uma API pronta para ser usada.
:::

:::exercise level=1
Adicione o springdoc, libere as rotas e abra a interface. Cadastre um produto
pelo navegador, sem `curl`.

:::answer
Repare que o formulário já nasce com os campos certos e recusa o envio se
faltar um obrigatório — tudo derivado das anotações de validação do capítulo
25. A documentação e a validação são a mesma verdade, escrita uma vez.
:::

:::exercise level=2
Documente o `409` de nome duplicado com `@ApiResponse`, apontando o esquema
`ApiError`. Depois confira o JSON em `/v3/api-docs`.

:::answer
O ganho não está na página bonita: está no JSON. Um cliente que lê a
especificação passa a saber, em código, que `409` devolve um objeto com
`message` e `fields` — e pode tratar isso sem adivinhar.
:::

:::exercise level=3
Baixe o `/v3/api-docs` em um arquivo e versione-o no repositório. Depois
escreva um teste que compare o arquivo com o gerado na hora. O que esse teste
protege?

:::answer
Ele detecta **mudança de contrato**: se alguém renomear um campo, mudar um
status ou remover um endpoint, o arquivo gerado deixa de bater com o
versionado e o build falha. É um teste de contrato — a mesma ideia do
capítulo 36, elevada ao nível da API inteira, e a defesa mais barata contra
o incidente do `NaN`.
:::
