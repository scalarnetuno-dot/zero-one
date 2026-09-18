---
title: "Clientes HTTP"
number: 39
part: p9
kicker: "A ferramenta importa menos que o hábito de guardar a requisição junto do código que a atende."
goal: >-
  Exercitar a API com `curl`, arquivos `.http` e coleções do Postman, e
  organizar isso de um jeito que sobreviva à saída de quem escreveu.
---

Você já usou `curl` desde o capítulo 17 e a interface do Swagger desde o 38.
Este capítulo é curto e trata de uma coisa só: onde essas requisições moram.

## `curl`: o denominador comum

```bash title="O que você precisa saber de curl" numbered
# GET simples
curl localhost:8080/products/1

# com cabeçalhos da resposta
curl -i localhost:8080/products/999

# POST com JSON
curl -X POST localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{"name":"Cabo","price":19.90,"quantity":3}'

# com token
curl localhost:8080/orders/meus \
  -H "Authorization: Bearer $TOKEN"

# salvando o token em uma variável
TOKEN=$(curl -s -X POST localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@aurora.com","password":"admin123"}' \
  | jq -r .token)
```

A última linha usa `jq`, que lê JSON na linha de comando. Vale instalar: ela
transforma "copiar o token com o mouse" em um passo automatizável.

:::tip
`curl` está em todo lugar: no seu terminal, no servidor de produção, no
contêiner, no exemplo que alguém vai colar em um chamado. Por isso ele
continua sendo a forma mais universal de descrever uma requisição — mesmo
para quem usa uma ferramenta gráfica no dia a dia.
:::

## Arquivos `.http`: a requisição versionada

```http title="src/test/http/products.http"
@host = http://localhost:8080
@token = {{login.response.body.token}}

### login
# @name login
POST {{host}}/auth/login
Content-Type: application/json

{ "email": "admin@aurora.com", "password": "admin123" }

### listar produtos
GET {{host}}/products?page=0&size=5

### criar produto
POST {{host}}/products
Content-Type: application/json
Authorization: Bearer {{token}}

{
  "name": "Teclado mecânico",
  "price": 349.90,
  "quantity": 12
}

### apagar
DELETE {{host}}/products/1
Authorization: Bearer {{token}}
```

IntelliJ e VS Code (com a extensão REST Client) executam esse arquivo com um
clique em cada `###`. E ele tem a propriedade que nenhuma ferramenta gráfica
tem: **fica no repositório**, ao lado do controlador que atende as rotas.

:::key
Requisição versionada junto do código é documentação executável. Quem chega
ao projeto amanhã abre o arquivo, roda, e vê a API funcionando — sem
instalar nada, sem pedir uma coleção a ninguém, sem adivinhar o formato do
corpo.
:::

## Postman e Insomnia

Ferramentas gráficas ganham em três coisas: histórico de respostas, ambientes
com um clique (local, homologação, produção) e testes encadeados que extraem
valores de uma resposta para a requisição seguinte.

```javascript title="Postman: guardando o token depois do login"
// aba Tests da requisição de login
const json = pm.response.json();
pm.environment.set("token", json.token);

pm.test("login devolve 200", function () {
    pm.response.to.have.status(200);
});
```

E perdem em uma, que costuma custar caro:

:::pitfall
A coleção mora na máquina de quem a criou. Quando essa pessoa sai de férias —
ou da empresa —, o time descobre que a única descrição funcional da API
estava em uma conta pessoal de uma ferramenta de terceiros. Exporte a coleção
como JSON e **versione junto do projeto**, ou use o arquivo `.http`, que já
nasce versionado.
:::

| Ferramenta | Ganha em | Perde em |
|---|---|---|
| `curl` | universal, automatizável | ilegível quando cresce |
| `.http` | versionado, dentro da IDE | sem histórico, sem gráfico |
| Postman | ambientes, encadeamento, time | fica fora do repositório |
| Swagger UI | sempre atualizado, zero setup | só o que a API expõe |

Tabela: Não escolha uma. Use `curl` para o exemplo do chamado, `.http` para o
dia a dia, Postman quando houver time e Swagger para quem chega de fora.

## Um passo além: gerar o cliente

```bash title="A partir do /v3/api-docs do capítulo 38"
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8080/v3/api-docs \
  -g typescript-axios \
  -o ./client
```

O time de front recebe uma biblioteca tipada, com um método por endpoint,
gerada da especificação. Quando um campo mudar de nome, o código do front
deixa de compilar — em vez de mostrar `undefined` na tela, como no incidente
do capítulo 36.

:::story A coleção do Carlos
A integração com o parceiro estava travada havia três dias.

O parceiro dizia que o `POST /orders` devolvia `400`. A Aurora dizia que
funcionava. Os dois estavam certos: o parceiro enviava `customerId` como
texto, e a API esperava número.

Ninguém conseguia comparar porque ninguém tinha a mesma requisição. Cada
pessoa tinha a sua, montada de memória, em uma ferramenta diferente.

Carlos tinha uma coleção do Postman com tudo funcionando — a que ele usava
desde o capítulo 17. Só que a coleção estava na conta pessoal dele, que
estava logada apenas no computador dele, que estava na oficina com a tela
quebrada.

No quarto dia, Marina criou o arquivo `products.http` no repositório, com as
onze requisições. Levou vinte minutos. O parceiro clonou o projeto, abriu o
arquivo, rodou, viu o corpo correto e resolveu em cinco minutos.

O arquivo continua lá. Já foi usado por sete pessoas que nunca conversaram
com o Carlos.
:::

:::art caption="A requisição que resolve o problema não pode morar em uma conta pessoal."
src="a-requisicao-que-resolve-o-problema-nao-pode-morar-em-uma-conta-pessoal.png"
Charge editorial minimalista: notebook com a tela rachada em cima de uma
bancada de oficina, com uma etiqueta de conserto pendurada. Ao lado, três
desenvolvedores de empresas diferentes olham para celulares mostrando
requisições ligeiramente diferentes entre si. Ao fundo, uma pasta de
repositório aberta com um único arquivo dentro, brilhando discretamente.
Fundo branco, poucos elementos, humor visual seco, estética editorial de
tecnologia.
:::

:::summary
- `curl` é universal; `jq` transforma a resposta em algo automatizável.
- Arquivo `.http` fica no repositório, ao lado do código que ele exercita.
- Postman ganha em ambientes e encadeamento, e some com quem o criou —
  exporte e versione.
- A especificação do capítulo 38 gera clientes tipados automaticamente.
:::

:::checkpoint
Você exercita a API pelas quatro vias, guarda as requisições no repositório e
sabe por que a coleção pessoal é um ponto único de falha.
:::

:::milestone
A API pode ser exercitada por qualquer pessoa em qualquer máquina, sem
conversa prévia. Falta a última peça de ferramenta — a que registra por que o
código é assim.
:::

:::exercise level=1
Crie `src/test/http/products.http` com as cinco requisições do CRUD e rode
pelo editor.

:::answer
Comece pelo login e use `{{login.response.body.token}}` nas demais. O
encadeamento é o que transforma o arquivo em roteiro: uma execução de cima
para baixo exercita a API inteira.
:::

:::exercise level=2
Escreva um script `bash` que faça login, crie um produto, busque, apague e
confirme o `404`. Faça-o falhar com código de saída diferente de zero se
algum passo não devolver o status esperado.

:::answer
`curl -f -s -o /dev/null -w "%{http_code}"` devolve o status e permite
comparar. Um script assim é um teste de fumaça: roda contra homologação
depois de cada deploy e responde, em dez segundos, se a aplicação subiu
inteira.
:::

:::exercise level=3
Gere um cliente TypeScript a partir do `/v3/api-docs` e inspecione o código
produzido. Depois renomeie um campo do DTO, gere de novo e compare.

:::answer
O diff mostra exatamente o que quebrou para quem consome. É a forma mais
concreta de enxergar o custo de uma mudança de contrato — e o argumento mais
convincente que existe a favor da versão de API, assunto que este livro deixa
como próximo passo.
:::
