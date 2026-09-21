---
title: "O que é o FastAPI"
number: 15
slug: o-que-e-fastapi
part: p3
kicker: "Um framework é um monte de decisões já tomadas. Vale saber quais são antes de aceitá-las."
goal: >-
  Entender o que um framework web resolve, o que é ASGI, de que peças o
  FastAPI é feito, e ler linha a linha as oito linhas do primeiro capítulo.
---

Um servidor HTTP recebe bytes de uma rede e precisa devolver bytes. Entre
uma coisa e outra existe uma quantidade enorme de trabalho repetitivo:
interpretar o texto da requisição, separar caminho de query, decodificar o
corpo, escolher qual função chamar, converter o retorno em JSON, montar os
cabeçalhos, escolher o status.

Escrever isso à mão uma vez é instrutivo. Escrever em todo projeto é
desperdício. É para isso que existe um framework.

## O que o framework decide por você

```python title="sem_framework.py" numbered
import socket

servidor = socket.socket()
servidor.bind(("127.0.0.1", 8000))
servidor.listen()

while True:
    cliente, _ = servidor.accept()
    pedido = cliente.recv(1024).decode()
    print(pedido.splitlines()[0])
    cliente.send(b"HTTP/1.1 200 OK\r\n\r\n{}")
    cliente.close()
```

Isso é um servidor HTTP. Ele funciona — e só. Não sabe rotear, não lê JSON,
atende uma conexão por vez, quebra com requisição maior que 1024 bytes e não
tem ideia do que seja um `404`.

O framework preenche essa distância. Em troca, ele impõe uma forma de
escrever: onde as rotas ficam, como os dados entram, o que a sua função pode
devolver.

:::key
Framework não é biblioteca. Biblioteca é código que **você chama**;
framework é código que **chama o seu**. Essa inversão é o que dá poder e é
também o que dá o incômodo: quando algo não encaixa, você não consegue
simplesmente pular a parte que atrapalha.
:::

## WSGI e ASGI: a fronteira entre servidor e aplicação

Em 2003, a comunidade Python padronizou a conversa entre servidor e
aplicação num documento chamado WSGI. Graças a ele, qualquer aplicação
Django ou Flask roda em qualquer servidor compatível — Gunicorn, uWSGI,
mod_wsgi.

O WSGI tem uma limitação de nascença: ele é **síncrono**. Cada requisição
ocupa um trabalhador do começo ao fim. Se a requisição espera meio segundo
por um banco de dados, o trabalhador fica meio segundo parado, sem poder
atender mais ninguém.

O ASGI é o sucessor, e a única mudança conceitual é essa: uma requisição
pode **ceder a vez** enquanto espera. O capítulo @cap:async trata do assunto
a sério; por ora, basta o mapa:

:::diagram type="blocks" caption="Cada camada acrescenta decisões já tomadas — e cobra por elas em abstração."
rows:
  - [{ text: "A sua aplicação", note: "rotas, regras, banco" }]
  - [{ text: "FastAPI", note: "validação, conversão, documentação" }]
  - [{ text: "Starlette", note: "roteamento, middleware, WebSocket" }]
  - [{ text: "ASGI", note: "o contrato entre servidor e aplicação" }]
  - [{ text: "Uvicorn", note: "abre a porta, fala TCP e HTTP" }]
:::

## De que o FastAPI é feito

O FastAPI é, literalmente, duas bibliotecas costuradas:

**Starlette** cuida do lado HTTP: roteamento, middleware, WebSocket, tarefas
de fundo, arquivos estáticos. É um framework ASGI completo e minimalista, e
quando você lê na documentação que "o FastAPI herda de Starlette", é
literal.

**Pydantic** cuida do lado dos dados: lê anotações de tipo, valida,
converte, e gera o esquema JSON. É o assunto do capítulo
@cap:modelando-com-pydantic.

O FastAPI é a cola entre os dois, e a cola é a parte interessante: ele
inspeciona a assinatura de cada função de rota e deduz, de cada parâmetro, se
ele vem do caminho, da query, do corpo, do cabeçalho ou de uma dependência.

:::trivia
O FastAPI nasceu em 2018, escrito por Sebastián Ramírez. A ideia não era
nova — vários projetos já tinham tentado usar anotações de tipo para gerar
validação. O que estava faltando era o Python 3.6, com anotação de variável,
e uma biblioteca de validação madura o bastante. O framework é, em boa
medida, o reconhecimento de uma oportunidade que já estava na mesa havia dois
anos.
:::

## Comparado com o que existia

| Framework | Filosofia | Quando escolher |
|---|---|---|
| Django | traz tudo: ORM, admin, templates | sistema com telas e painel |
| Flask | traz o mínimo; você monta | projeto pequeno, controle total |
| FastAPI | API tipada, documentação gerada | API para outro programa consumir |

Tabela: Não há vencedor. Há adequação — e uma API REST sem telas é o caso
mais claro a favor do FastAPI.

A diferença prática mais visível é a documentação. Em Flask, descrever os
endpoints é trabalho manual, feito à parte, que desatualiza. Em FastAPI, a
descrição **é** o código.

## As oito linhas, agora por inteiro

```python title="main.py" numbered
from fastapi import FastAPI

app = FastAPI()


@app.get("/saude")
def saude():
    return {"status": "de pé"}
```

:::anatomy title="O que cada parte faz"
lang: python
code: |
  app = FastAPI()

  @app.get("/saude")
  def saude():
      return {"status": "de pé"}
notes:
  - { line: 1, text: "`app` é a aplicação ASGI: é este objeto que o Uvicorn procura." }
  - { line: 3, text: "`@app.get` é um decorador: registra a função na tabela de rotas." }
  - { line: 3, text: "`\"/saude\"` é o caminho; o verbo está no nome do método." }
  - { line: 4, text: "O nome da função não aparece na URL — ele é só para você." }
  - { line: 5, text: "Devolver um dicionário basta: o FastAPI converte em JSON e põe `200`." }
:::

O decorador merece um parágrafo, porque é a construção Python que mais
assusta quem vê pela primeira vez. `@app.get("/saude")` acima de `def
saude()` significa, em Python puro:

```python
saude = app.get("/saude")(saude)
```

Ou seja: `app.get("/saude")` devolve uma função, e essa função recebe a sua
`saude` e faz algo com ela — no caso, guarda numa tabela de rotas. Não há
mágica; há uma função recebendo outra função. O capítulo
@cap:dependency-injection desmonta isso inteiro.

## Subir, recarregar, desligar

```text
$ fastapi dev main.py

  Server started at http://127.0.0.1:8000
  Documentation at http://127.0.0.1:8000/docs
```

O modo `dev` liga o recarregamento automático: salvou o arquivo, o servidor
reinicia. Isso é ótimo em desenvolvimento e **inaceitável** em produção — o
processo que vigia arquivos custa recursos e recarrega o servidor no pior
momento possível.

```text
$ fastapi run main.py         # produção: sem recarga
$ uvicorn main:app --workers 4
```

Na segunda forma, `main:app` significa "no módulo `main`, o objeto `app`".
É essa a forma que reaparece no capítulo @cap:projeto-final, dentro do
contêiner, com o número de trabalhadores escolhido a dedo.

:::pitfall
A porta 8000 pode estar ocupada — muitas vezes por um servidor que você
esqueceu aberto em outro terminal. O sintoma é `[Errno 98] Address already
in use`. Suba em outra porta com `--port 8001` ou encerre o processo antigo;
o que **não** funciona é rodar duas vezes e supor que a segunda vale.
:::

## As três páginas que vêm de graça

| Endereço | O que é |
|---|---|
| `/docs` | Swagger UI: documentação navegável e executável |
| `/redoc` | a mesma informação, em formato de leitura |
| `/openapi.json` | o esquema cru, que gera as duas anteriores |

Tabela: O `/openapi.json` é o que importa: é um padrão, e ferramentas
externas geram clientes em outras linguagens a partir dele.

:::practice
Abra `/docs`, expanda a rota `/saude` e clique em **Try it out** e depois em
**Execute**. A página executa a requisição de verdade e mostra o comando
`curl` equivalente. Esse botão substitui, nas primeiras semanas de um
projeto, qualquer ferramenta externa de teste de API.
:::

:::summary
- Framework é código que chama o seu; a inversão é o poder e o incômodo.
- ASGI sucede o WSGI permitindo que uma requisição ceda a vez enquanto
  espera.
- FastAPI = Starlette (HTTP) + Pydantic (dados) + a leitura das assinaturas.
- `@app.get(...)` é um decorador: uma função que recebe a sua função.
- `fastapi dev` recarrega; produção usa `run` ou Uvicorn com trabalhadores.
- `/docs`, `/redoc` e `/openapi.json` vêm do próprio código.
:::

:::exercise level=1
Acrescente uma rota `GET /versao` que devolva `{"versao": "0.1.0"}` e
confira no `/docs` que ela apareceu sozinha na documentação.

:::answer
```python
@app.get("/versao")
def versao():
    return {"versao": "0.1.0"}
```
:::

:::exercise level=2
Crie duas rotas com o mesmo caminho e verbos diferentes — `GET /ping` e
`POST /ping` — e explique por que isso não é conflito.

:::answer
```python
@app.get("/ping")
def ping_ler():
    return {"metodo": "GET"}


@app.post("/ping")
def ping_criar():
    return {"metodo": "POST"}
```
A rota, em HTTP, é o par **verbo + caminho**, não o caminho sozinho. É por
isso que o CRUD inteiro cabe em dois caminhos: `/produtos` e
`/produtos/{id}`, com verbos diferentes em cada um.
:::

:::exercise level=3
Sua equipe precisa escolher entre Django e FastAPI para um sistema que tem
uma API pública consumida por um aplicativo, um painel administrativo
interno, e relatórios em PDF. Escreva a recomendação em cinco linhas.

:::answer
Nenhum dos dois resolve os três problemas bem sozinho, e essa é a resposta
honesta. O Django entrega o painel administrativo pronto — que no FastAPI
seria um projeto inteiro — e resolve relatório com templates maduros. O
FastAPI entrega a API pública com documentação gerada e validação tipada, que
no Django exigiria o Django REST Framework e bastante configuração.

A recomendação que eu escreveria: **Django para o painel e os relatórios,
FastAPI para a API pública, com o banco compartilhado**. E registraria por
escrito o preço dessa escolha — dois projetos, duas implantações, duas
pilhas de dependência — para que a decisão seja revista se o painel encolher
ou a API crescer. Escolher uma ferramenta só, aceitando o atrito num dos
lados, é defensável; o que não é defensável é escolher sem nomear o atrito.
:::
