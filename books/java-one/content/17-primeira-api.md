---
title: "A primeira API"
number: 17
part: p3
kicker: "Quatro verbos, um caminho e uma decisão sobre o que devolver em cada caso."
goal: >-
  Escrever endpoints para os cinco verbos do CRUD, receber dados pelo caminho,
  pela query e pelo corpo, e escolher o código de status correto.
---

Este é o capítulo em que o projeto passa a ser uma API. Os dados ainda moram
em um `Map` na memória — o banco chega no capítulo 19 —, mas o contrato HTTP
que nasce aqui é o mesmo que vai ao ar no capítulo 42.

## HTTP em uma página

Toda requisição tem quatro partes, e você vai mexer nas quatro:

:::anatomy title="As partes de uma requisição HTTP"
lang: http
code: |
  POST /products?notify=true HTTP/1.1
  Content-Type: application/json
  Authorization: Bearer eyJhbGci...

  {"nome": "Teclado", "preco": 349.90}
notes:
  - { line: 1, text: "**Verbo**: a intenção. `POST` cria, `GET` lê, `PUT` substitui, `DELETE` apaga." }
  - { line: 1, text: "**Caminho**: o recurso. Substantivo no plural, sem verbo dentro." }
  - { line: 1, text: "**Query**: parâmetros opcionais, depois do `?`." }
  - { line: 2, text: "**Cabeçalhos**: metadados — tipo do conteúdo, autenticação, idioma." }
  - { line: 5, text: "**Corpo**: os dados. Só em `POST`, `PUT` e `PATCH`." }
:::

E toda resposta tem um número de três dígitos que resume tudo:

| Faixa | Significado | Você vai usar |
|---|---|---|
| `2xx` | deu certo | `200`, `201`, `204` |
| `4xx` | o cliente errou | `400`, `401`, `403`, `404`, `409` |
| `5xx` | o servidor errou | `500` (e você vai querer evitar) |

Tabela: O primeiro dígito conta a história. Se você devolve `200` com uma
mensagem de erro dentro, está mentindo para o cliente.

## O controlador

```java title="ProductController.java" numbered
package com.loja.catalog.product;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final Map<Long, Product> banco = new LinkedHashMap<>();
    private final AtomicLong sequencia = new AtomicLong();

    @GetMapping
    public List<Product> listar() {
        return new ArrayList<>(banco.values());
    }
}
```

:::anatomy title="As anotações que transformam método em endpoint"
lang: java
code: |
  @RestController
  @RequestMapping("/products")
  public class ProductController {

      @GetMapping
      public List<Product> listar() {
          return new ArrayList<>(banco.values());
      }
  }
notes:
  - { line: 1, text: "`@RestController` = `@Controller` + `@ResponseBody`: o retorno vira o corpo da resposta." }
  - { line: 2, text: "`@RequestMapping` define o prefixo do caminho para todos os métodos da classe." }
  - { line: 5, text: "`@GetMapping` sem argumento herda o caminho da classe: `GET /products`." }
  - { line: 6, text: "O retorno é convertido em JSON pelo Jackson — sem uma linha de conversão sua." }
:::

:::trivia
Aquela conversão automática para JSON é feita pelo Jackson, uma biblioteca que
não faz parte do Spring. Ela entra pela porta do `spring-boot-starter-web` e
é escolhida por autoconfiguração: se estiver no classpath, o Spring a usa. É a
filosofia do Boot em ação — a decisão já foi tomada, e você só discute se
quiser.
:::

## Ler dados: três origens, três anotações

```java title="De onde vem cada dado" numbered
// 1. do caminho:  GET /products/7
@GetMapping("/{id}")
public Product buscar(@PathVariable Long id) {
    return banco.get(id);
}

// 2. da query:  GET /products/search?nome=teclado
@GetMapping("/search")
public List<Product> buscarPorNome(@RequestParam String nome) {
    return banco.values().stream()
            .filter(p -> p.getNome().contains(nome))
            .toList();
}

// 3. do corpo:  POST /products
@PostMapping
public Product criar(@RequestBody Product novo) {
    novo.setId(sequencia.incrementAndGet());
    banco.put(novo.getId(), novo);
    return novo;
}
```

| Anotação | Lê de | Obrigatório? |
|---|---|---|
| `@PathVariable` | um pedaço do caminho | sim, faz parte da rota |
| `@RequestParam` | a query string | opcional com `required = false` |
| `@RequestBody` | o corpo | sim, e precisa de `Content-Type` |

Tabela: As três portas de entrada de dados em um controlador.

## O CRUD completo

```java title="ProductController.java (o resto)" numbered
@PutMapping("/{id}")
public ResponseEntity<Product> atualizar(
        @PathVariable Long id,
        @RequestBody Product dados) {

    Product atual = banco.get(id);
    if (atual == null) {
        return ResponseEntity.notFound().build();
    }
    dados.setId(id);
    banco.put(id, dados);
    return ResponseEntity.ok(dados);
}

@DeleteMapping("/{id}")
public ResponseEntity<Void> apagar(@PathVariable Long id) {
    if (banco.remove(id) == null) {
        return ResponseEntity.notFound().build();
    }
    return ResponseEntity.noContent().build();
}
```

`ResponseEntity` é o objeto que carrega **status, cabeçalhos e corpo**. Use-o
sempre que a resposta puder variar — e em uma API real ela quase sempre pode.

## Os cinco diálogos, em ordem

:::http title="Criar — devolve 201 e o recurso criado"
POST /products
Content-Type: application/json

{
  "nome": "Teclado mecânico",
  "preco": 349.90,
  "estoque": 12
}
---
201 Created
Location: /products/1

{
  "id": 1,
  "nome": "Teclado mecânico",
  "preco": 349.90,
  "estoque": 12
}
:::

:::http title="Buscar um — 200 quando existe"
GET /products/1
---
200 OK
Content-Type: application/json

{ "id": 1, "nome": "Teclado mecânico", "preco": 349.90 }
:::

:::http title="Buscar um que não existe — 404, sem corpo"
GET /products/999
---
404 Not Found
:::

:::http title="Apagar — 204, também sem corpo"
DELETE /products/1
---
204 No Content
:::

:::key
`201` na criação, com o cabeçalho `Location` apontando o recurso novo. `204`
na remoção, porque não há nada para devolver. `404` quando o id não existe.
Esses três detalhes separam uma API que respeita o protocolo de uma que só
devolve `200` para tudo.
:::

```java title="Devolvendo 201 corretamente" numbered
@PostMapping
public ResponseEntity<Product> criar(@RequestBody Product novo) {
    novo.setId(sequencia.incrementAndGet());
    banco.put(novo.getId(), novo);

    URI local = URI.create("/products/" + novo.getId());
    return ResponseEntity.created(local).body(novo);
}
```

## Testando pela linha de comando

```bash title="curl: o cliente HTTP que já está instalado"
curl localhost:8080/products

curl -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"nome":"Mouse","preco":89.90,"estoque":5}'

curl -i localhost:8080/products/999
```

O `-i` mostra os cabeçalhos e o status — e é o que você vai usar para
conferir se o `404` realmente é um `404`. O capítulo 39 apresenta ferramentas
com interface; por ora, `curl` basta e ensina mais.

:::pitfall
Esquecer o `-H "Content-Type: application/json"` no `POST` devolve
`415 Unsupported Media Type`. A mensagem é obscura e a causa é simples: sem o
cabeçalho, o Spring não sabe qual conversor usar para ler o corpo.
:::

:::story Pode mostrar para o cliente?
O `GET /products` respondeu com uma lista vazia — `[]` — e Carlos ficou dez
segundos olhando para aqueles dois caracteres com uma emoção
desproporcional.

Cadastrou um produto pelo `curl`. Rodou de novo. A lista tinha um item.

Roberto, que tinha desenvolvido um sexto sentido para aparecer exatamente
nesses momentos, apareceu.

— Funcionou?

— Funcionou.

— Então pode mostrar para o cliente na quinta?

Marina, sem levantar os olhos do monitor:

— Pode mostrar para o cliente na quinta se o cliente aceitar que os dados
desaparecem quando alguém reinicia a aplicação.

— E quando alguém reinicia a aplicação?

— Toda vez que a gente faz deploy.

Roberto ficou em silêncio por três segundos — de novo, uma eternidade — e
disse que ia remarcar para a semana seguinte.
:::

## O que está errado nesta versão

Este controlador funciona e tem quatro defeitos graves, todos de propósito:

1. **guarda os dados em memória** — reiniciar apaga tudo (capítulos 19 a 21);
2. **o controlador contém a regra** — filtrar e numerar não é trabalho dele
   (capítulo 22);
3. **expõe a entidade diretamente** — o cliente vê o desenho interno do banco
   (capítulo 24);
4. **não valida nada** — `preco: -5` entra (capítulo 25).

Reconhecer os quatro agora é o que vai fazer os próximos capítulos parecerem
inevitáveis, e não burocráticos.

:::summary
- `@RestController` + `@RequestMapping` definem a classe; `@GetMapping` e
  família definem cada rota.
- `@PathVariable`, `@RequestParam` e `@RequestBody` são as três portas de
  entrada.
- `ResponseEntity` controla status, cabeçalho e corpo.
- `201` + `Location` ao criar, `204` ao apagar, `404` quando não existe.
:::

:::checkpoint
Você escreve os cinco endpoints do CRUD, lê dados das três origens, escolhe o
status correto e testa tudo com `curl`.
:::

:::milestone
A API responde aos cinco verbos em `/products`. Os dados morrem quando o
processo encerra e o controlador faz coisa que não é dele — os dois problemas
que a Parte 4 resolve.
:::

:::exercise level=1
Acrescente `GET /products/count` que devolva a quantidade de produtos
cadastrados. Depois responda: por que ela não deveria ser um endpoint
separado em uma API bem desenhada?

:::answer
```java
@GetMapping("/count")
public long contar() {
    return banco.size();
}
```
Porque contagem é **metadado de uma lista**, não um recurso. A forma REST
correta é devolver o total no cabeçalho ou dentro da resposta paginada — que é
exatamente o que o capítulo 27 faz com `Page`.
:::

:::exercise level=2
Faça o `POST` recusar um produto sem nome, devolvendo `400 Bad Request`.
Depois compare o seu código com a anotação `@NotBlank` do capítulo 25.

:::answer
```java
if (novo.getNome() == null || novo.getNome().isBlank()) {
    return ResponseEntity.badRequest().build();
}
```
Funciona e não escala: com dez campos você teria dez `if` em cada endpoint. O
capítulo 25 troca tudo isso por uma anotação no campo e um `@Valid` na
assinatura.
:::

:::exercise level=3
Implemente `PATCH /products/{id}` que altere **apenas** os campos enviados.
Pense em como distinguir "campo ausente" de "campo enviado como nulo".

:::answer
A distinção exige um tipo que saiba a diferença — normalmente um DTO com
campos `Optional` ou um `Map<String, Object>`. É por isso que muitas APIs
maduras simplesmente não oferecem `PATCH`: a semântica de atualização parcial
é mais difícil de acertar do que parece, e um `PUT` bem documentado resolve
95% dos casos.
:::
