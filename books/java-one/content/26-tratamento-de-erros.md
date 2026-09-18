---
title: "Tratamento de erros"
number: 26
part: p5
kicker: "O erro é parte do contrato. Uma API que responde 500 para tudo é uma API que não conta o que aconteceu."
goal: >-
  Traduzir exceções de negócio em status HTTP com `@ControllerAdvice`, montar
  uma resposta de erro padronizada e escolher entre `400`, `404`, `409` e
  `500` com critério.
---

O capítulo 23 terminou com um problema: `GET /products/999` devolve `500`. O
serviço lançou `ProductNotFoundException` e ninguém traduziu. Este capítulo
escreve o tradutor — uma classe, e todos os erros da API passam a ter forma.

## Um lugar para traduzir tudo

```java title="shared/exception/ApiExceptionHandler.java" numbered
package com.loja.catalog.shared.exception;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(ProductNotFoundException.class)
    public ResponseEntity<ApiError> naoEncontrado(
            ProductNotFoundException e, HttpServletRequest req) {
        return resposta(HttpStatus.NOT_FOUND, e.getMessage(), req);
    }

    @ExceptionHandler(DuplicateProductException.class)
    public ResponseEntity<ApiError> conflito(
            DuplicateProductException e, HttpServletRequest req) {
        return resposta(HttpStatus.CONFLICT, e.getMessage(), req);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiError> requisicaoRuim(
            IllegalArgumentException e, HttpServletRequest req) {
        return resposta(HttpStatus.BAD_REQUEST, e.getMessage(), req);
    }

    private ResponseEntity<ApiError> resposta(
            HttpStatus status, String mensagem,
            HttpServletRequest req) {
        ApiError corpo = new ApiError(
                Instant.now(), status.value(),
                status.getReasonPhrase(), mensagem,
                req.getRequestURI(), List.of());
        return ResponseEntity.status(status).body(corpo);
    }
}
```

:::anatomy title="Como o Spring encontra o tradutor certo"
lang: java
code: |
  @RestControllerAdvice
  public class ApiExceptionHandler {

      @ExceptionHandler(ProductNotFoundException.class)
      public ResponseEntity<ApiError> naoEncontrado(
              ProductNotFoundException e) {
          return ...;
      }
  }
notes:
  - { line: 1, text: "`@RestControllerAdvice` vale para **todos** os controladores da aplicação." }
  - { line: 4, text: "`@ExceptionHandler` registra este método para aquele tipo de exceção." }
  - { line: 4, text: "A busca é pelo tipo mais específico: um handler de `RuntimeException` só entra se não houver um mais próximo." }
  - { line: 6, text: "O Spring injeta a própria exceção como parâmetro — e, se você pedir, a requisição também." }
:::

## A resposta de erro padronizada

```java title="shared/exception/ApiError.java" numbered
public record ApiError(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path,
        List<FieldError> fields) {

    public record FieldError(String field, String message) { }
}
```

:::http title="O mesmo 404 de antes, agora honesto"
GET /products/999
---
404 Not Found
Content-Type: application/json

{
  "timestamp": "2026-03-14T18:35:00Z",
  "status": 404,
  "error": "Not Found",
  "message": "produto não encontrado: 999",
  "path": "/products/999",
  "fields": []
}
:::

## Erro de validação com o campo que falhou

O capítulo 25 deixou a mensagem de validação no formato do framework. Agora
ela entra no mesmo molde:

```java title="ApiExceptionHandler.java (trecho)" numbered
@ExceptionHandler(MethodArgumentNotValidException.class)
public ResponseEntity<ApiError> validacao(
        MethodArgumentNotValidException e,
        HttpServletRequest req) {

    List<ApiError.FieldError> campos = e.getBindingResult()
            .getFieldErrors().stream()
            .map(f -> new ApiError.FieldError(
                    f.getField(), f.getDefaultMessage()))
            .toList();

    ApiError corpo = new ApiError(
            Instant.now(), 400, "Bad Request",
            "dados inválidos", req.getRequestURI(), campos);

    return ResponseEntity.badRequest().body(corpo);
}
```

:::http title="Erro de validação com endereço do problema"
POST /products
Content-Type: application/json

{ "name": "", "price": -50 }
---
400 Bad Request

{
  "status": 400,
  "message": "dados inválidos",
  "path": "/products",
  "fields": [
    { "field": "name",  "message": "nome é obrigatório" },
    { "field": "price", "message": "preço deve ser maior que zero" }
  ]
}
:::

Essa resposta é utilizável por um cliente: o aplicativo pode pintar de
vermelho exatamente o campo `price` e mostrar a mensagem ao lado dele. É a
diferença entre uma API que recusa e uma API que ensina.

## Escolhendo o status

| Status | Significa | Exemplo no projeto |
|---|---|---|
| `400` | requisição malformada ou inválida | preço negativo, JSON quebrado |
| `401` | não sei quem você é | token ausente (capítulo 32) |
| `403` | sei quem você é, e não pode | usuário tentando apagar (capítulo 33) |
| `404` | não existe | id inexistente |
| `409` | conflito com o estado atual | nome duplicado, estoque insuficiente |
| `422` | semanticamente inválido | opcional; muitos usam `400` |
| `500` | **eu** tenho um bug | qualquer coisa não prevista |

Tabela: A regra mestra: `4xx` é o cliente, `5xx` é você. Trocar isso quebra
monitoramento e política de repetição dos clientes.

:::key
`401` é *unauthenticated* (não autenticado) apesar de se chamar
`Unauthorized`; `403` é *unauthorized* (sem permissão). O nome no protocolo
está trocado desde 1997 e não vai ser corrigido. Decore.
:::

## A rede de segurança

```java title="O último handler — e o mais importante" numbered
@ExceptionHandler(Exception.class)
public ResponseEntity<ApiError> inesperado(
        Exception e, HttpServletRequest req) {

    log.error("erro não tratado em {}", req.getRequestURI(), e);

    ApiError corpo = new ApiError(
            Instant.now(), 500, "Internal Server Error",
            "erro interno", req.getRequestURI(), List.of());

    return ResponseEntity.internalServerError().body(corpo);
}
```

Duas decisões nesse método. Ele **registra** a exceção completa no log, com a
pilha — é a única cópia do que aconteceu. E devolve ao cliente uma mensagem
genérica, sem pilha e sem detalhe interno.

:::pitfall
Nunca devolva `e.getMessage()` de uma exceção inesperada ao cliente. Mensagens
de exceção de banco carregam nome de tabela, de coluna e, às vezes, o SQL
inteiro — informação valiosa para quem estiver procurando uma brecha. Registre
tudo no log; mostre pouco na resposta.
:::

## O problema do erro genérico bem-intencionado

:::compare left="Engolir e maquiar" right="Traduzir com honestidade"
try {
  return service.buscar(id);
} catch (Exception e) {
  return null;
}
---
// sem try no controller:
// o handler traduz
return service.buscar(id);
:::

A coluna da esquerda devolve `200` com corpo vazio — o cliente não tem como
saber se o produto não existe ou se o servidor falhou. A da direita não tem
`try` nenhum: o controlador confia no tradutor central.

:::trivia
Existe um padrão de resposta de erro publicado como norma: a RFC 9457,
*Problem Details for HTTP APIs*, com campos `type`, `title`, `status`,
`detail` e `instance`. O Spring 6 traz suporte nativo por meio de
`ProblemDetail`. Se você está começando um projeto novo hoje, vale adotar o
formato padronizado em vez de inventar o seu — o `ApiError` deste capítulo
existe para mostrar a mecânica.
:::

:::summary
- `@RestControllerAdvice` centraliza a tradução de exceção em resposta HTTP.
- `@ExceptionHandler` casa pelo tipo mais específico.
- Erro de validação deve dizer **qual campo** falhou.
- `4xx` é culpa do cliente, `5xx` é sua; `401` é autenticação e `403` é
  permissão.
- Registre a exceção completa no log e devolva mensagem genérica no `500`.
:::

:::checkpoint
Você traduz exceções de negócio nos status corretos, devolve erro de validação
por campo, mantém uma rede de segurança para o inesperado e não vaza detalhe
interno.
:::

:::milestone
A API agora erra bem: `404` para inexistente, `409` para conflito, `400` com o
campo problemático, `500` só quando a culpa é sua. Os quatro defeitos do
capítulo 17 estão resolvidos.
:::

:::exercise level=1
Acrescente um handler para `InsufficientStockException` devolvendo `409`.

:::answer
```java
@ExceptionHandler(InsufficientStockException.class)
public ResponseEntity<ApiError> estoque(
        InsufficientStockException e, HttpServletRequest req) {
    return resposta(HttpStatus.CONFLICT, e.getMessage(), req);
}
```
`409` e não `400`: a requisição estava correta; o **estado atual** do recurso
é que impede a operação. Essa distinção ajuda o cliente a decidir se vale
tentar de novo.
:::

:::exercise level=2
Faça o handler de `500` incluir um identificador de rastreio no corpo e no log
(um `UUID` gerado na hora). Explique o ganho.

:::answer
```java
String traceId = UUID.randomUUID().toString();
log.error("erro {} em {}", traceId, req.getRequestURI(), e);
```
Com o identificador na resposta, o usuário pode informá-lo no suporte e você
localiza a pilha exata no log em segundos — sem precisar expor nada. É uma
prática padrão em API de produção.
:::

:::exercise level=3
Descubra o que acontece com um `@ExceptionHandler(RuntimeException.class)`
declarado **junto** dos outros. Depois explique por que a ordem de declaração
não importa.

:::answer
Ele só é chamado para `RuntimeException` que não tenha handler mais
específico. O Spring resolve por **proximidade na hierarquia de tipos**, não
por ordem no arquivo: `ProductNotFoundException` tem handler próprio, então
vence. Isso permite ter um handler genérico sem medo de que ele sequestre os
casos tratados.
:::
