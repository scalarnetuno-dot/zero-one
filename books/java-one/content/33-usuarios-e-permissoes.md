---
title: "Usuários e permissões"
number: 33
part: p7
kicker: "Saber quem é a pessoa é metade do trabalho. A outra metade é decidir o que ela pode fazer."
goal: >-
  Proteger rotas por papel com `@PreAuthorize` e por regra de dono do recurso,
  e saber por que autorização também mora no serviço.
---

O token do capítulo 32 carrega um papel: `USER` ou `ADMIN`. Falta usá-lo.
Hoje, qualquer pessoa autenticada ainda apaga qualquer produto — o que é uma
melhoria pequena em relação a "qualquer pessoa".

## O mapa de permissões da Aurora

| Operação | USER | ADMIN |
|---|---|---|
| `GET /products` | público | público |
| `POST /products` | não | sim |
| `PUT /products/{id}` | não | sim |
| `DELETE /products/{id}` | não | sim |
| `GET /orders/meus` | só os próprios | todos |
| `GET /users` | não | sim |

Tabela: O contrato de autorização. Escrevê-lo antes de programar é o que
evita descobrir uma regra faltando em produção.

## Dois lugares para declarar a regra

```java title="1. Na cadeia de filtros — por rota" numbered
.authorizeHttpRequests(auth -> auth
    .requestMatchers(HttpMethod.GET, "/products/**").permitAll()
    .requestMatchers(HttpMethod.POST, "/products/**")
        .hasRole("ADMIN")
    .requestMatchers(HttpMethod.PUT, "/products/**")
        .hasRole("ADMIN")
    .requestMatchers(HttpMethod.DELETE, "/products/**")
        .hasRole("ADMIN")
    .anyRequest().authenticated())
```

```java title="2. No método — por anotação" numbered
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void apagar(@PathVariable Long id) {
    service.apagar(id);
}
```

Para a segunda forma funcionar, uma anotação na configuração:

```java
@Configuration
@EnableMethodSecurity
public class SecurityConfig { ... }
```

:::key
As duas formas coexistem, e a escolha não é de gosto. Regra **por rota** é
um mapa: quem lê a configuração vê o sistema inteiro. Regra **por método**
fica perto do código que ela protege e sobrevive a uma mudança de URL. Em
projetos reais, use a primeira para o desenho geral e a segunda para as
exceções.
:::

:::pitfall
`hasRole("ADMIN")` procura a autoridade `ROLE_ADMIN` — o prefixo é
acrescentado automaticamente. `hasAuthority("ADMIN")` procura exatamente
`ADMIN`. Misturar os dois resulta em `403` para quem deveria passar, e o log
não explica. Escolha um estilo e mantenha.
:::

## A regra que o filtro não consegue expressar

"Um usuário vê os próprios pedidos" não é uma regra de rota: depende do
**dado**, não do caminho.

```java title="OrderService.java" numbered
@Transactional(readOnly = true)
public OrderResponse buscar(Long id, String emailLogado) {
    Order order = repository.findById(id)
            .orElseThrow(() -> new OrderNotFoundException(id));

    boolean dono = order.getCustomer()
            .getEmail().equals(emailLogado);

    if (!dono && !ehAdmin()) {
        throw new AccessDeniedException("pedido de outro cliente");
    }
    return OrderResponse.of(order);
}
```

:::pitfall
Repare no que este método **não** faz: ele não devolve `404` quando o pedido
é de outra pessoa. Devolver `404` em vez de `403` esconde a existência do
recurso — o que é mais seguro — mas também impede o cliente legítimo de
distinguir "não existe" de "não é seu". Para dados sensíveis, prefira `404`;
para o resto, `403` é mais honesto. É uma decisão consciente, não um
descuido.
:::

## Quem está logado, dentro do código

```java title="Três formas de obter o usuário atual" numbered
// 1. parâmetro do controlador
@GetMapping("/meus")
public List<OrderResponse> meus(Authentication auth) {
    return service.doCliente(auth.getName());
}

// 2. anotação
@GetMapping("/meus")
public List<OrderResponse> meus(
        @AuthenticationPrincipal UserDetails user) {
    return service.doCliente(user.getUsername());
}

// 3. em qualquer lugar (inclusive no serviço)
String email = SecurityContextHolder.getContext()
        .getAuthentication().getName();
```

A terceira funciona em qualquer camada porque o contexto fica em uma variável
de thread — a mesma thread que atende a requisição. É prática e tem um preço:
o serviço passa a depender do Spring Security, o que dificulta testá-lo
isoladamente. Preferir passar o e-mail como parâmetro mantém o serviço
ignorante do framework.

## Autorização também é regra de negócio

:::diagram type="blocks" caption="Três camadas de autorização — e a de baixo é a única que conhece o dado."
rows:
  - [{ text: "Cadeia de filtros", note: "por rota e verbo: o mapa geral" }]
  - [{ text: "@PreAuthorize", note: "por método: papel exigido" }]
  - [{ text: "Service", note: "por dado: é seu? está no seu setor?" }]
:::

:::pitfall
Proteger só no controlador é proteger só a porta da frente. No dia em que
outro ponto de entrada existir — uma fila de mensagens, um agendador, um
comando de terminal — a regra do controlador não vale mais. Regra que
depende do dado pertence ao serviço.
:::

## O que o cliente recebe

:::http title="Autenticado, mas sem permissão"
DELETE /products/7
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
---
403 Forbidden

{
  "status": 403,
  "error": "Forbidden",
  "message": "acesso negado",
  "path": "/products/7"
}
:::

Para que a resposta saia nesse formato — o `ApiError` do capítulo 26 —, falta
um handler:

```java title="ApiExceptionHandler.java (acréscimo)" numbered
@ExceptionHandler(AccessDeniedException.class)
public ResponseEntity<ApiError> negado(
        AccessDeniedException e, HttpServletRequest req) {
    return resposta(HttpStatus.FORBIDDEN,
            "acesso negado", req);
}
```

:::story O estagiário com ADMIN
A tabela de usuários tinha uma coluna `role` e um valor padrão: `ADMIN`.

Não foi decisão. Foi o primeiro registro criado à mão durante o
desenvolvimento, copiado como modelo para o script de criação de usuários, e
o script ficou.

Todo mundo que entrou na Aurora nos quatro meses seguintes entrou como
administrador do catálogo. O time de atendimento, o time de marketing, dois
estagiários e um consultor externo que passou três semanas.

Ninguém fez nada de errado. Esse é o ponto: a segurança não foi testada
porque nunca foi exercitada.

A descoberta veio pelo lado mais burocrático possível — uma auditoria de
conformidade pediu a lista de quem podia apagar produto. A resposta foi
"trinta e uma pessoas", em uma empresa de quarenta.

Marina acrescentou três coisas no mesmo dia: o padrão da coluna virou `USER`,
o script passou a exigir o papel explicitamente, e um teste automatizado
passou a verificar que um `USER` recebe `403` no `DELETE`.

O teste é o capítulo 36. Foi o que impediu isso de voltar a acontecer.
:::

:::summary
- Regra por rota desenha o mapa; `@PreAuthorize` protege o método; o serviço
  decide o que depende do dado.
- `hasRole` acrescenta `ROLE_`; `hasAuthority` não.
- `401` é "não sei quem você é"; `403` é "sei, e você não pode".
- Devolver `404` em vez de `403` esconde a existência do recurso — decisão
  consciente.
- Valor padrão de permissão deve ser o menor possível.
:::

:::checkpoint
Você protege rotas por papel, escreve autorização por dono do recurso no
serviço, obtém o usuário logado e devolve `403` no formato padrão da API.
:::

:::milestone
Fim da Parte 7. A API sabe quem entra, o que cada um pode fazer e responde
com o status certo quando não pode. Ela também nunca foi testada por nada
além de um `curl` digitado à mão — e é isso que a Parte 8 resolve.
:::

:::exercise level=1
Proteja `POST`, `PUT` e `DELETE` de `/products` com `ADMIN` e teste com um
token de `USER`. Confirme o `403`.

:::answer
Se vier `401` em vez de `403`, o token não chegou ao filtro — provavelmente
falta o prefixo `Bearer ` ou o filtro não foi registrado na cadeia. Os dois
status apontam para problemas diferentes, e confundi-los custa meia hora.
:::

:::exercise level=2
Implemente `GET /orders/meus` devolvendo apenas os pedidos do usuário
autenticado, sem receber id nenhum na URL.

:::answer
```java
@GetMapping("/meus")
public List<OrderResponse> meus(Authentication auth) {
    return service.doCliente(auth.getName());
}
```
Repare que o cliente **não consegue** pedir os pedidos de outra pessoa: o
identificador não está na URL. Desenhar o endpoint assim elimina uma classe
inteira de falha de autorização — a melhor proteção é a que não depende de
verificação.
:::

:::exercise level=3
Acrescente o papel `MANAGER`, que pode criar e editar produto mas não
apagar. Depois responda: em que ponto uma lista de papéis deixa de escalar?

:::answer
Quando as combinações crescem mais rápido que os cargos — "pode editar preço
mas não estoque", "pode apagar só da própria categoria". Aí o modelo deixa de
ser papel e passa a ser **permissão**: o usuário tem um conjunto de
autoridades granulares (`PRODUCT_WRITE`, `PRODUCT_DELETE`) e os papéis viram
apenas atalhos para conjuntos. É a mesma virada do capítulo 12: quando a
escada de `if` cresce demais, falta um tipo.
:::
