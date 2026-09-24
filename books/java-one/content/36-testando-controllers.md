---
title: "Testando controllers"
number: 36
part: p8
kicker: "O contrato HTTP é a única parte do sistema que outra pessoa depende. É a que mais merece um teste."
goal: >-
  Testar endpoints com MockMvc, verificar status, cabeçalho e JSON, e simular
  um usuário autenticado sem fazer login.
---

O teste do capítulo 35 provou que a regra funciona. Ele não prova nada sobre
o caminho, o verbo, o status ou o formato do JSON — e é exatamente isso que o
cliente enxerga.

## MockMvc: HTTP sem rede

```java title="ProductControllerTest.java" numbered
@WebMvcTest(ProductController.class)
class ProductControllerTest {

    @Autowired
    MockMvc mvc;

    @MockitoBean
    ProductService service;

    @Test
    void deveDevolver200EOProdutoQuandoExiste() throws Exception {
        when(service.buscar(1L)).thenReturn(
                new ProductResponse(1L, "Teclado", null,
                        new BigDecimal("349.90"), 12,
                        Status.ATIVO, Instant.now()));

        mvc.perform(get("/products/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(1))
                .andExpect(jsonPath("$.name").value("Teclado"))
                .andExpect(jsonPath("$.price").value(349.90));
    }
}
```

:::anatomy title="O que `@WebMvcTest` carrega — e o que ele deixa de fora"
lang: java
code: |
  @WebMvcTest(ProductController.class)
  class ProductControllerTest {

      @Autowired
      MockMvc mvc;

      @MockitoBean
      ProductService service;
  }
notes:
  - { line: 1, text: "Sobe **só** a camada web: controlador, conversores JSON, validação e segurança." }
  - { line: 1, text: "Não sobe serviço, repositório nem banco — por isso é rápido." }
  - { line: 4, text: "`MockMvc` executa a requisição dentro do processo: nenhuma porta é aberta." }
  - { line: 7, text: "`@MockitoBean` põe um dublê do serviço no contexto (era `@MockBean` até o Spring Boot 3.4)." }
:::

:::key
Este teste verifica o **contrato**: caminho, verbo, status, nomes dos campos
e formato dos valores. Se alguém renomear `name` para `title` no DTO, ele
quebra — e é exatamente para isso que ele existe.
:::

## Status e cabeçalho

```java title="O 201 com Location do capítulo 17" numbered
@Test
void deveDevolver201ELocationAoCriar() throws Exception {
    when(service.criar(any())).thenReturn(
            new ProductResponse(7L, "Mouse", null,
                    new BigDecimal("89.90"), 5,
                    Status.ATIVO, Instant.now()));

    mvc.perform(post("/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("""
                             {"name":"Mouse","price":89.90,
                              "quantity":5}
                             """))
            .andExpect(status().isCreated())
            .andExpect(header().string("Location", "/products/7"))
            .andExpect(jsonPath("$.id").value(7));
}

@Test
void deveDevolver404QuandoNaoExiste() throws Exception {
    when(service.buscar(99L))
            .thenThrow(new ProductNotFoundException(99L));

    mvc.perform(get("/products/99"))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.status").value(404))
            .andExpect(jsonPath("$.message").exists());
}
```

O segundo teste é o que garante que o `@RestControllerAdvice` do capítulo 26
está no caminho — ele verifica a tradução da exceção, não o serviço.

## Validação: o teste que prova que o `400` é `400`

```java title="Entrada inválida" numbered
@Test
void deveDevolver400EOCampoQuandoPrecoENegativo()
        throws Exception {
    mvc.perform(post("/products")
                    .contentType(MediaType.APPLICATION_JSON)
                    .content("""
                             {"name":"X","price":-5,"quantity":1}
                             """))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.fields[0].field")
                    .value("price"));

    verify(service, never()).criar(any());
}
```

Duas verificações em um teste, e as duas importam: o status certo **e** a
garantia de que o serviço não foi chamado. Validação que roda depois da regra
não é validação.

## Testando com usuário autenticado

```java title="Sem fazer login" numbered
@Test
@WithMockUser(roles = "ADMIN")
void adminDeveApagar() throws Exception {
    mvc.perform(delete("/products/1").with(csrf()))
            .andExpect(status().isNoContent());
}

@Test
@WithMockUser(roles = "USER")
void usuarioComumNaoDeveApagar() throws Exception {
    mvc.perform(delete("/products/1").with(csrf()))
            .andExpect(status().isForbidden());

    verify(service, never()).apagar(any());
}
```

O segundo teste é o do incidente do capítulo 33 — as quatro linhas que
teriam impedido trinta e uma pessoas de poder apagar o catálogo.

:::pitfall
`@WebMvcTest` **carrega** a sua `SecurityConfig`. Se o teste começar a
devolver `401` onde você espera `200`, não é bug do teste: é a segurança
funcionando. Use `@WithMockUser` ou libere a rota — e desconfie se precisar
desligar a segurança para o teste passar, porque isso significa que ela não
está sendo testada em lugar nenhum.
:::

## `jsonPath`: navegando na resposta

```java title="As formas que você vai usar" numbered
.andExpect(jsonPath("$.name").value("Teclado"))
.andExpect(jsonPath("$.content").isArray())
.andExpect(jsonPath("$.content.length()").value(3))
.andExpect(jsonPath("$.content[0].id").value(1))
.andExpect(jsonPath("$.totalElements").value(42))
.andExpect(jsonPath("$.password").doesNotExist())
```

A última linha é a mais valiosa de todas: ela prova que um campo sensível
**não** está na resposta. Um teste assim em `UserController` é a rede que
segura o dia em que alguém acrescentar um campo à entidade sem pensar — como
no capítulo 24.

## Quando subir a aplicação inteira

```java title="@SpringBootTest: o teste de ponta a ponta" numbered
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class ProductFlowTest {

    @Autowired MockMvc mvc;
    @Autowired ProductRepository repository;

    @Test
    @WithMockUser(roles = "ADMIN")
    void deveCriarEDepoisBuscar() throws Exception {
        mvc.perform(post("/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("""
                                 {"name":"Cabo","price":19.90,
                                  "quantity":3}
                                 """)
                        .with(csrf()))
                .andExpect(status().isCreated());

        assertThat(repository.findByNameIgnoreCase("Cabo"))
                .isPresent();
    }
}
```

| | `@WebMvcTest` | `@SpringBootTest` |
|---|---|---|
| Carrega | só a camada web | a aplicação inteira |
| Velocidade | centenas de ms | segundos |
| Banco | nenhum | de verdade |
| Use para | contrato de cada endpoint | um ou dois fluxos completos |

Tabela: A proporção saudável é uma pirâmide: muitos testes de unidade,
alguns de camada web, pouquíssimos de ponta a ponta.

:::story O contrato que quebrou sem ninguém perceber
A mudança foi pequena e bem-intencionada: `ProductResponse` passou a devolver
`price` como texto formatado — `"R$ 349,90"` — porque o time de front pediu
para não ter de formatar.

O time de front do **site** pediu. O aplicativo de celular, feito por um
parceiro, esperava número.

O deploy foi na terça. Na quarta, a tela de carrinho do aplicativo começou a
mostrar `NaN` no total para todo mundo. Não houve erro, não houve `500`, não
houve alerta: o aplicativo recebia um texto onde esperava número, somava, e o
resultado era "não é um número" — em silêncio, na tela do cliente.

Foram vinte e nove horas até alguém ligar os pontos.

O teste que teria pegado isso tinha uma linha:

```java
.andExpect(jsonPath("$.price").value(349.90))
```

Ela existia. Alguém a tinha alterado no mesmo commit, para `.value("R$
349,90")`, porque "o teste estava quebrando".
:::

:::summary
- `@WebMvcTest` sobe só a camada web e testa o contrato HTTP.
- Verifique status, cabeçalho e campos do JSON — inclusive os que **não**
  devem existir.
- `@WithMockUser` simula papel sem login; o teste de `403` é obrigatório.
- Validação precisa provar que o serviço não foi chamado.
- Muitos testes de unidade, alguns de web, pouquíssimos de ponta a ponta.
:::

:::checkpoint
Você testa endpoints com MockMvc, verifica contrato e autorização, e sabe
escolher entre `@WebMvcTest` e `@SpringBootTest`.
:::

:::milestone
O contrato da API está coberto: caminho, status, JSON e permissão. Falta a
camada que os dois capítulos anteriores evitaram de propósito — o banco.
:::

:::exercise level=1
Escreva o teste do `DELETE` verificando `204` e a chamada ao serviço.

:::answer
Não esqueça `.with(csrf())` mesmo com CSRF desligado na produção: o
`@WebMvcTest` usa a configuração padrão de teste do Spring Security, que
pode exigi-lo. É a causa número um de `403` inexplicável em teste de
controlador.
:::

:::exercise level=2
Escreva um teste que garanta que a resposta de `GET /users/{id}` **não**
contém o campo `password`.

:::answer
```java
.andExpect(jsonPath("$.password").doesNotExist())
```
Um teste de quatro palavras que protege contra um vazamento. Testes negativos
— provar que algo **não** acontece — são os mais subestimados do repertório.
:::

:::exercise level=3
Escreva um teste de ponta a ponta que crie um produto, baixe o estoque até
zerar e confirme que o status virou `ESGOTADO` na resposta da API.

:::answer
Este teste atravessa controlador, serviço, entidade e banco — é o único tipo
capaz de pegar um erro de integração, como um `@Transactional` ausente ou uma
coluna com o nome errado. Por isso mesmo é lento e frágil: mantenha dois ou
três, para os fluxos que valem dinheiro, e não mais.
:::
