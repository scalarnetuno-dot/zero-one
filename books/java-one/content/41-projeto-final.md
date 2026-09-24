---
title: "Projeto final"
number: 41
part: p10
kicker: "Agora sem mastigar. Você recebe os requisitos e constrói a loja inteira."
epigraph: "Eu não sabia o que estava fazendo, então fiz. E aí eu soube."
epigraph_by: "Ditado de programador, atribuído a todo mundo"
goal: >-
  Construir sozinho, do zero, a API completa da loja — com as decisões de
  modelagem, arquitetura, segurança e teste tomadas por você.
---

Os quarenta capítulos anteriores mostraram cada peça sendo encaixada. Este
capítulo não mostra nada: ele **pede**.

Você recebe os requisitos, como receberia de uma Cláudia qualquer, e
constrói. Quando travar, volte ao capítulo que trata do assunto — eles
continuam onde estavam.

## Os requisitos

A Aurora Comércio quer a loja inteira, não só o catálogo.

```text title="O que o sistema precisa fazer"
1.  Cadastrar, listar, buscar, editar e remover produtos.
2.  Organizar produtos em categorias.
3.  Cadastrar clientes com e-mail único.
4.  Registrar pedidos com vários itens.
5.  Calcular o total do pedido no momento da compra.
6.  Baixar o estoque ao confirmar o pedido.
7.  Recusar pedido com item sem estoque suficiente.
8.  Listar os pedidos de um cliente.
9.  Só ADMIN cadastra, edita e remove produto e categoria.
10. Cliente vê apenas os próprios pedidos.
```

E as regras que não estão na lista — as que Cláudia diria na terceira
reunião:

```text title="As regras de negócio"
· Produto com estoque zero fica ESGOTADO automaticamente.
· Categoria com produtos não pode ser removida.
· O preço do item do pedido é o do momento da compra.
· Pedido confirmado não pode ser alterado nem cancelado.
· E-mail de cliente é único e não muda depois de criado.
```

## O modelo

:::diagram type="er" caption="Cinco entidades. Todas apareceram no livro; agora elas convivem."
columns: 2
entities:
  - name: "Category"
    fields: ["id (PK)", "name (unique)", "description"]
  - name: "Product"
    fields: ["id (PK)", "name", "price", "quantity", "status", "category_id (FK)"]
  - name: "Customer"
    fields: ["id (PK)", "name", "email (unique)", "created_at"]
  - name: "Order"
    fields: ["id (PK)", "customer_id (FK)", "status", "total", "created_at"]
  - name: "OrderItem"
    fields: ["id (PK)", "order_id (FK)", "product_id (FK)", "quantity", "unit_price"]
relations:
  - { from: "Category", to: "Product", label: "1:N" }
  - { from: "Customer", to: "Order", label: "1:N" }
  - { from: "Order", to: "OrderItem", label: "1:N" }
:::

## O contrato da API

| Verbo | Caminho | Quem pode |
|---|---|---|
| `POST` | `/auth/login` | todos |
| `GET` | `/products` | todos |
| `POST` `PUT` `DELETE` | `/products` | ADMIN |
| `GET` | `/categories` | todos |
| `POST` `DELETE` | `/categories` | ADMIN |
| `POST` | `/customers` | todos |
| `POST` | `/orders` | autenticado |
| `GET` | `/orders/meus` | autenticado (só os seus) |
| `GET` | `/orders/{id}` | dono ou ADMIN |

Tabela: Nove linhas que descrevem o sistema inteiro. Escreva-as antes do
código.

## O pedido, que é a parte nova

:::http title="Criar um pedido"
POST /orders
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

{
  "items": [
    { "productId": 7, "quantity": 2 },
    { "productId": 3, "quantity": 1 }
  ]
}
---
201 Created
Location: /orders/15

{
  "id": 15,
  "status": "CONFIRMADO",
  "total": 789.70,
  "createdAt": "2026-03-20T14:02:11Z",
  "items": [
    { "productName": "Teclado mecânico",
      "quantity": 2, "unitPrice": 349.90 },
    { "productName": "Mouse", "quantity": 1, "unitPrice": 89.90 }
  ]
}
:::

:::http title="E quando falta estoque"
POST /orders
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...

{ "items": [ { "productId": 7, "quantity": 500 } ] }
---
409 Conflict

{
  "status": 409,
  "message": "estoque insuficiente para Teclado mecânico",
  "path": "/orders"
}
:::

:::key
O `POST /orders` é a operação mais difícil do projeto e a que melhor mede se
você entendeu o livro. Ela envolve: validação de entrada, busca de várias
entidades, regra de negócio com exceção, alteração de estado de outra
entidade, cálculo de dinheiro, e **tudo isso em uma transação**. Se a baixa
do terceiro item falhar, os dois primeiros têm de voltar.
:::

## A ordem sugerida

```text title="Quinze passos, do vazio ao pronto"
 1. Projeto no Initializr: web, jpa, postgres, security,
    validation, flyway, springdoc, test.
 2. Docker: subir o PostgreSQL.
 3. Flyway: V1 com as cinco tabelas.
 4. Entidades e repositórios.
 5. Category: service, controller, DTOs, testes.
 6. Product: service, controller, DTOs, testes.
 7. Tratamento de erros centralizado.
 8. Validação nos DTOs de entrada.
 9. Paginação, ordenação e filtros em produtos.
10. Customer: cadastro com e-mail único.
11. User, login e JWT.
12. Autorização por papel e por dono do recurso.
13. Order: a operação transacional inteira.
14. Testes: unidade, web e repositório com Testcontainers.
15. OpenAPI, README e arquivo .http.
```

Repare que a ordem não é a do livro: aqui você constrói **uma fatia
completa** de cada vez (entidade → serviço → controlador → teste), em vez de
uma camada inteira por vez. É como se trabalha em projeto real, e é mais
difícil — porque cada fatia exige lembrar de tudo.

## O que conta como pronto

:::checkpoint
Um `git clone`, um `docker compose up` e um `./mvnw spring-boot:run` devem
ser suficientes para outra pessoa rodar o sistema na máquina dela sem falar
com você. Se for preciso explicar qualquer passo, ele deveria estar no
`README.md`.
:::

```text title="A lista de conferência"
□ Compila e sobe com um comando.
□ Os testes passam e cobrem as regras, não os getters.
□ POST /orders é transacional de verdade (teste isso!).
□ Nenhum endpoint devolve 500 para erro previsível.
□ Nenhuma senha, segredo ou token no repositório.
□ Swagger sobe e permite exercitar tudo, autenticado.
□ README explica o que é, como rodar e como testar.
□ Histórico de commits conta a evolução, não "ajustes".
```

## Três armadilhas que este projeto tem de propósito

:::pitfall
**O total do pedido.** Se você calcular somando `product.getPrice()` no
momento da leitura, o total de um pedido antigo muda quando o preço do
produto muda. O preço tem de ser copiado para `OrderItem.unitPrice` na
criação — é o *snapshot* do capítulo 18, e a maioria das primeiras
implementações erra aqui.
:::

:::pitfall
**A listagem de pedidos.** `GET /orders/meus` com os itens de cada pedido é
um N+1 esperando para acontecer: um `SELECT` para os pedidos e mais um para
os itens de cada um. Resolva com `@EntityGraph` — e confirme no log, não no
sentimento.
:::

:::pitfall
**A baixa de estoque concorrente.** Duas pessoas comprando a última unidade
ao mesmo tempo: as duas leem `quantity = 1`, as duas passam na verificação,
as duas baixam. O estoque fica `-1`. A solução envolve bloqueio otimista
(`@Version` na entidade) — assunto que este livro não cobre, e que você acaba
de descobrir sozinho que existe. É assim que se aprende o próximo nível.
:::

:::story Agora é você que revisa
Carlos recebeu a tarefa numa segunda: "a loja inteira, do zero, sozinho".

Não era um exercício. A Aurora tinha vendido o mesmo sistema para uma segunda
loja, e a segunda loja queria uma instância própria — sem os quatro meses de
gambiarra acumulada na primeira.

Ele começou pelo `docker compose`. Depois pelo Flyway. Na quarta, tinha
categoria e produto com teste. Na sexta, o pedido inteiro, transacional,
falhando corretamente quando o estoque não dava.

Na segunda seguinte, um desenvolvedor novo entrou na equipe. Chama-se Bruna,
sabe lógica, não sabe Java, e foi escalada para "aquele projetinho da API".

Carlos abriu o *pull request* dela na terça e, antes de aprovar, escreveu um
comentário na linha 14:

> "Explica em voz alta, sem ler, o que esta linha faz."

Marina viu o comentário do outro lado da sala e não disse nada. Só sorriu
para a tela, do jeito de quem reconhece a própria frase voltando.
:::

:::summary
- Dez requisitos, cinco regras de negócio e nove rotas descrevem o sistema.
- Construa em fatias completas: entidade, serviço, controlador, teste.
- `POST /orders` é o exame final: transação, regra, exceção e dinheiro.
- Pronto significa que outra pessoa roda sem falar com você.
:::

:::checkpoint
Você constrói uma API REST completa a partir de requisitos, toma as decisões
de modelagem e arquitetura sozinho, e sabe conferir se ela está pronta.
:::

:::milestone
O projeto do livro terminou. Falta colocá-lo em um lugar onde outras pessoas
possam usá-lo — e o último capítulo é sobre isso.
:::

:::exercise level=1
Escreva o `README.md` do projeto antes de escrever o código. Descreva o que o
sistema faz, como rodar e como testar.

:::answer
Escrever o README primeiro é uma técnica antiga e subestimada: ela obriga a
descrever o produto antes de construí-lo, e quase sempre revela um requisito
mal entendido enquanto a mudança ainda é de graça.
:::

:::exercise level=2
Implemente `POST /orders` e escreva o teste que prova que a transação desfaz
tudo quando o terceiro item não tem estoque.

:::answer
O teste precisa verificar **três** coisas: o status `409`, que nenhum pedido
foi criado, e que o estoque dos dois primeiros produtos continua intacto. A
terceira é a que a maioria esquece — e é a única que realmente testa a
transação.
:::

:::exercise level=3
Descubra o que é bloqueio otimista, acrescente `@Version` à entidade
`Product` e escreva um teste com duas threads comprando a última unidade.

:::answer
`@Version` faz o Hibernate incluir a versão no `WHERE` do `UPDATE`: se outra
transação alterou a linha nesse meio-tempo, zero linhas são afetadas e você
recebe `OptimisticLockException`. O teste com duas threads é difícil de
escrever e é a melhor forma de entender por que sistemas de verdade têm
retentativa. Você acabou de sair do escopo deste livro por conta própria —
que era exatamente o objetivo dele.
:::
