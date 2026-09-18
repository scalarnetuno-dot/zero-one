---
title: "Controller"
number: 23
part: p4
kicker: "A camada mais fina do sistema — e a única que o cliente vê."
goal: >-
  Escrever o CRUD completo com as três camadas, devolver o status correto em
  cada caso e testar a API inteira pela linha de comando.
---

Com o serviço pronto, o controlador vira o que sempre deveria ter sido: um
tradutor. Ele recebe HTTP, chama um método, devolve HTTP. Este capítulo fecha
o CRUD e é o primeiro ponto do livro em que a API está completa de ponta a
ponta.

## O CRUD inteiro

```java title="ProductController.java" numbered
package com.loja.catalog.product;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;

@RestController
@RequestMapping("/products")
public class ProductController {

    private final ProductService service;

    public ProductController(ProductService service) {
        this.service = service;
    }

    @GetMapping
    public List<Product> listar() {
        return service.listar();
    }

    @GetMapping("/{id}")
    public Product buscar(@PathVariable Long id) {
        return service.buscar(id);
    }

    @PostMapping
    public ResponseEntity<Product> criar(@RequestBody Product novo) {
        Product salvo = service.criar(novo);
        URI local = URI.create("/products/" + salvo.getId());
        return ResponseEntity.created(local).body(salvo);
    }

    @PutMapping("/{id}")
    public Product atualizar(@PathVariable Long id,
                             @RequestBody Product dados) {
        return service.atualizar(id, dados);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void apagar(@PathVariable Long id) {
        service.apagar(id);
    }
}
```

Trinta linhas para cinco endpoints. Repare no que **não** existe aqui: nenhum
`if`, nenhuma verificação de existência, nenhum `try/catch`. Tudo isso é
trabalho de outra camada.

## Duas formas de declarar o status

```java title="ResponseEntity ou @ResponseStatus" numbered
// 1. quando o status varia ou há cabeçalho a incluir
@PostMapping
public ResponseEntity<Product> criar(@RequestBody Product novo) {
    Product salvo = service.criar(novo);
    return ResponseEntity
            .created(URI.create("/products/" + salvo.getId()))
            .body(salvo);
}

// 2. quando o status é sempre o mesmo
@DeleteMapping("/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void apagar(@PathVariable Long id) {
    service.apagar(id);
}
```

`ResponseEntity` dá controle total e custa verbosidade. `@ResponseStatus` é
declarativo e limpo, e só serve quando a resposta é sempre igual. Use a
segunda por padrão e a primeira quando precisar do cabeçalho `Location` ou de
mais de um status possível.

## A operação que não é CRUD

Um CRUD puro não dá conta do negócio. Baixar estoque não é "atualizar um
produto": é uma **ação**.

```java title="Ação de negócio como sub-recurso" numbered
@PostMapping("/{id}/stock-withdrawals")
public Product baixarEstoque(
        @PathVariable Long id,
        @RequestParam int quantidade) {
    return service.baixarEstoque(id, quantidade);
}
```

:::http title="Uma ação com nome de recurso"
POST /products/7/stock-withdrawals?quantidade=3
---
200 OK
Content-Type: application/json

{ "id": 7, "nome": "Teclado", "quantity": 9, "status": "ATIVO" }
:::

:::key
REST fala de **recursos** (substantivos), não de ações (verbos). Um caminho
como `/products/7/withdraw-stock` funciona e denuncia a intenção errada. A
convenção que envelhece melhor: transforme a ação em um recurso —
`stock-withdrawals` é um registro de baixa, e criar esse registro é um `POST`.
:::

## A API completa, em uma tabela

| Verbo | Caminho | Status de sucesso | Status de erro |
|---|---|---|---|
| `GET` | `/products` | `200` | — |
| `GET` | `/products/{id}` | `200` | `404` |
| `POST` | `/products` | `201` + `Location` | `400`, `409` |
| `PUT` | `/products/{id}` | `200` | `400`, `404` |
| `DELETE` | `/products/{id}` | `204` | `404` |
| `POST` | `/products/{id}/stock-withdrawals` | `200` | `404`, `409` |

Tabela: O contrato da API do livro. Essa tabela é a especificação — e o
capítulo 38 vai gerá-la automaticamente a partir do código.

## Provando que funciona

```bash title="O CRUD inteiro em seis comandos"
# criar
curl -i -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Teclado","price":349.90,"quantity":12}'

# listar
curl localhost:8080/products

# buscar
curl localhost:8080/products/1

# atualizar
curl -X PUT localhost:8080/products/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Teclado mecânico","price":299.90,"quantity":10}'

# baixar estoque
curl -X POST \
  "localhost:8080/products/1/stock-withdrawals?quantidade=3"

# apagar
curl -i -X DELETE localhost:8080/products/1
```

:::checkpoint
Se o `POST` devolve `201` com `Location`, o `DELETE` devolve `204` e o `GET`
de um id apagado devolve... bem, veja o próximo parágrafo. É aí que este
capítulo revela o próximo problema.
:::

:::story Quinhentos para tudo
O aplicativo do cliente começou a ficar lento numa terça à tarde.

Não era o banco. Não era a rede. Era o próprio aplicativo, que tentava buscar
um produto, recebia `500` e — seguindo a regra que todo cliente HTTP bem
escrito segue — tentava de novo. Três vezes, com espera exponencial.

O produto não existia. Nunca tinha existido. Um link antigo, compartilhado no
grupo de WhatsApp da vizinhança do Seu Antônio, apontava para o id 4821.

Cada pessoa que clicava gerava três requisições em vez de uma. Duzentas
pessoas clicaram.

— A API está mentindo — disse Marina. — Ela está dizendo "eu falhei", e o
cliente está fazendo o que se faz quando um servidor falha: insistir. Se ela
dissesse "isso não existe", ninguém insistiria.
:::

## O que ainda está feio

```bash
curl -i localhost:8080/products/999
```

```text title="A resposta de hoje"
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:22:10.123+00:00",
  "status": 500,
  "error": "Internal Server Error",
  "path": "/products/999"
}
```

O serviço lançou `ProductNotFoundException` e ninguém traduziu. O Spring fez o
que faz com exceção desconhecida: `500`. E `500` significa "eu tenho um bug",
quando na verdade o cliente pediu algo que não existe — o que é `404`.

:::pitfall
Um `500` que deveria ser `404` não é só cosmético. Monitoramento conta `5xx`
para disparar alarme; cliente bem-escrito não repete requisição que deu `4xx`
mas repete a que deu `5xx`. Devolver o status errado faz o seu sistema mentir
para as ferramentas que cuidam dele.
:::

Falta também tratar os dois defeitos restantes do capítulo 17: a entidade está
sendo exposta diretamente (capítulo 24) e nada é validado (capítulo 25). Os
três próximos capítulos existem para fechar essa lista.

:::summary
- O controlador só traduz: sem `if`, sem `try`, sem regra.
- `@ResponseStatus` para status fixo; `ResponseEntity` quando varia ou há
  cabeçalho.
- Ação de negócio vira sub-recurso com `POST`, não verbo no caminho.
- Exceção de negócio sem tradutor vira `500` — e `500` é uma mentira sobre
  quem errou.
:::

:::checkpoint
Você escreve os cinco endpoints delegando ao serviço, modela uma ação como
sub-recurso, escolhe o status correto e testa a API completa com `curl`.
:::

:::milestone
A API está completa: cinco endpoints, três camadas, dados no PostgreSQL. Ela
funciona e ainda mente nos erros, expõe o modelo interno e aceita lixo. Parte
5 resolve os três.
:::

:::exercise level=1
Escreva o `CategoryController` completo, delegando tudo ao
`CategoryService`.

:::answer
Mesma estrutura do `ProductController`, com `/categories` no
`@RequestMapping`. Se a sua versão ficou parecida linha por linha, isso é bom
sinal: consistência entre controladores é o que permite a alguém novo no
projeto adivinhar onde as coisas estão.
:::

:::exercise level=2
Acrescente `GET /products?status=ATIVO` que filtre por status quando o
parâmetro vier, e liste tudo quando não vier.

:::answer
```java
@GetMapping
public List<Product> listar(
        @RequestParam(required = false) Status status) {
    return status == null
            ? service.listar()
            : service.listarPorStatus(status);
}
```
O `if` aqui é aceitável porque é uma decisão **de protocolo** (o parâmetro
veio ou não), não de negócio. A linha divisória é essa.
:::

:::exercise level=3
Descubra o que acontece se você enviar `{"name":"X","price":"abc"}` no `POST`
e explique por que o status devolvido faz sentido — ou não.

:::answer
O Jackson falha ao converter `"abc"` em `BigDecimal` e o Spring devolve
`400 Bad Request` com uma mensagem de desserialização. O status está correto
(o cliente errou), mas o corpo expõe detalhes internos da biblioteca — nome
de classe, posição do caractere. O capítulo 26 padroniza também esse caso.
:::
