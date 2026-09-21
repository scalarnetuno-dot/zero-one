---
title: "Testando a API"
number: 38
slug: testando-a-api
part: p8
kicker: "O teste de API não verifica a regra. Ele verifica o contrato: status, corpo e cabeçalho."
goal: >-
  Escrever testes de integração com `TestClient`, substituir dependências,
  testar rotas protegidas e evitar que o conjunto vire uma suíte lenta e
  frágil.
---

O capítulo anterior testou as regras sem HTTP. Este testa o HTTP: o
caminho certo aciona a função certa, o status é o combinado, o corpo tem os
campos prometidos e o erro sai no formato do capítulo
@cap:tratamento-de-erros.

## `TestClient`

```python title="tests/test_api_produtos.py" numbered
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_saude_responde_200():
    resposta = cliente.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json()["status"] == "de pé"
```

O `TestClient` **não abre porta e não usa rede**. Ele fala com a aplicação
ASGI diretamente, em memória, e por isso um teste de API custa milissegundos
— mais que um teste de serviço, muito menos que um navegador.

Por baixo ele é um cliente `httpx`, então a API é a de qualquer cliente HTTP
moderno: `.get`, `.post(json=...)`, `.headers`, `.json()`.

## Substituindo as dependências

```python title="tests/conftest.py" numbered
import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_produto_servico
from app.main import app
from tests.dubles import RepositorioFalso, SessaoFalsa


@pytest.fixture
def servico_falso():
    return ProdutoServico(SessaoFalsa(), RepositorioFalso())


@pytest.fixture
def cliente(servico_falso):
    app.dependency_overrides[get_produto_servico] = (
        lambda: servico_falso
    )
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

Três detalhes importam nessa fixture.

O `dependency_overrides` do capítulo @cap:dependency-injection troca a
montagem inteira: nenhuma linha do código de produção sabe que está em
teste.

O `with TestClient(app)` dispara os eventos de ciclo de vida da aplicação —
o que importa quando há `lifespan`, como o cliente HTTP compartilhado do
capítulo @cap:projeto-final. Sem o `with`, eles não rodam.

E o `clear()` depois do `yield` é obrigatório. `app` é um objeto global, e
uma substituição que sobra vaza para os testes seguintes — produzindo falhas
que dependem da ordem de execução e não se reproduzem isoladas.

## O CRUD pelo contrato

```python title="tests/test_api_produtos.py" numbered
def test_criar_devolve_201_e_o_recurso(cliente):
    resposta = cliente.post(
        "/produtos",
        json={"nome": "Tomate", "preco": "8.90", "estoque": 10},
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"] > 0
    assert corpo["nome"] == "Tomate"
    assert "senha" not in corpo


def test_buscar_inexistente_devolve_404(cliente):
    resposta = cliente.get("/produtos/999")

    assert resposta.status_code == 404
    assert resposta.json()["tipo"] == "produto_nao_encontrado"


def test_nome_repetido_devolve_409(cliente):
    dados = {"nome": "Tomate", "preco": "8.90"}
    cliente.post("/produtos", json=dados)

    resposta = cliente.post("/produtos", json=dados)

    assert resposta.status_code == 409


def test_preco_negativo_devolve_422(cliente):
    resposta = cliente.post(
        "/produtos", json={"nome": "Tomate", "preco": "-1"}
    )

    assert resposta.status_code == 422
    campos = resposta.json()["campos"]
    assert any(c["campo"] == "preco" for c in campos)
```

:::key
Repare no que **não** está sendo testado aqui: o cálculo da margem, a regra
de estoque, a normalização do nome. Tudo isso já foi coberto no capítulo
@cap:testando-services, mais rápido e com mais casos. O teste de API cobre a
**tradução**: entrou requisição, saiu status e corpo.
:::

:::pitfall
Repetir na camada de API todos os casos já testados na de serviço é o jeito
mais comum de uma suíte crescer para vinte minutos. Cada regra merece
dezenas de casos na camada barata e **um** caminho representativo na cara.
:::

## Rotas protegidas

```python title="tests/conftest.py" numbered
@pytest.fixture
def cliente_autenticado(cliente, usuario_falso):
    app.dependency_overrides[usuario_atual] = (
        lambda: usuario_falso
    )
    yield cliente
    app.dependency_overrides.pop(usuario_atual, None)
```

```python title="tests/test_api_seguranca.py" numbered
def test_criar_sem_token_devolve_401(cliente):
    resposta = cliente.post(
        "/produtos", json={"nome": "Tomate", "preco": "8.90"}
    )

    assert resposta.status_code == 401


def test_produtor_nao_apaga_produto(cliente, usuario_produtor):
    app.dependency_overrides[usuario_atual] = (
        lambda: usuario_produtor
    )

    resposta = cliente.delete("/produtos/1")

    assert resposta.status_code == 403
```

Substituir `usuario_atual` evita gerar token de verdade em cada teste — o
que é rápido e tem um custo: o caminho do JWT deixa de ser exercitado.

:::warning
Guarde **pelo menos um** teste que faça o login de verdade e use o token
recebido. Se todos os testes substituírem `usuario_atual`, um erro na
emissão ou na verificação do token passa despercebido pela suíte inteira, e
a API sobe em produção sem conseguir autenticar ninguém.
:::

```python title="tests/test_auth.py" numbered
def test_fluxo_completo_de_login(cliente_com_banco):
    cliente_com_banco.post(
        "/usuarios",
        json={
            "nome": "Bia",
            "email": "bia@sabia.coop",
            "senha": "segredo123",
        },
    )

    login = cliente_com_banco.post(
        "/auth/login",
        data={
            "username": "bia@sabia.coop",
            "password": "segredo123",
        },
    )
    token = login.json()["access_token"]

    resposta = cliente_com_banco.get(
        "/produtos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resposta.status_code == 200
```

Repare no `data=` em vez de `json=` no login: `OAuth2PasswordRequestForm`
espera formulário, não JSON. É uma exigência do padrão OAuth2 e a causa de um
`422` confuso na primeira tentativa de todo mundo.

## Testar o esquema, não só a rota

```python title="tests/test_contrato.py" numbered
def test_openapi_tem_as_rotas_esperadas(cliente):
    esquema = cliente.get("/openapi.json").json()
    caminhos = esquema["paths"]

    assert "/produtos" in caminhos
    assert "get" in caminhos["/produtos"]
    assert "post" in caminhos["/produtos"]


def test_resposta_de_produto_nao_expoe_custo(cliente):
    esquema = cliente.get("/openapi.json").json()
    modelo = esquema["components"]["schemas"]["ProdutoLer"]

    assert "custo" not in modelo["properties"]
```

O segundo teste é o tipo que se paga sozinho: ele falha no dia em que
alguém acrescentar `custo` ao esquema de saída por distração. É o contrato
do capítulo @cap:schemas virando verificação executável.

:::story O campo que apareceu sozinho
A coluna `custo_de_compra` entrou na tabela numa terça, para um relatório
interno. O modelo do SQLAlchemy ganhou o campo. O esquema `ProdutoLer`
herdava de uma base que lia os atributos do modelo.

Na quarta, o aplicativo dos produtores passou a receber o custo de compra de
cada produto na listagem pública.

Ninguém notou por onze dias. Notou-se quando um produtor perguntou, numa
reunião, por que a cooperativa ganhava tanto em cima da alface dele.
:::

:::summary
- `TestClient` fala com a aplicação em memória, sem rede.
- `dependency_overrides` troca a montagem sem tocar no código de produção —
  e precisa ser limpo depois.
- `with TestClient(app)` dispara o ciclo de vida da aplicação.
- Teste de API cobre tradução: status, corpo, cabeçalho. A regra fica na
  camada de baixo.
- Mantenha ao menos um teste com login e token de verdade.
- O `/openapi.json` é testável — e é onde vazamento de campo se pega.
:::

:::exercise level=1
Escreva os testes de `GET /produtos` vazio e com dois produtos.

:::answer
```python
def test_listar_vazio(cliente):
    resposta = cliente.get("/produtos")

    assert resposta.status_code == 200
    assert resposta.json()["itens"] == []
    assert resposta.json()["total"] == 0


def test_listar_com_dois(cliente):
    cliente.post("/produtos",
                 json={"nome": "Tomate", "preco": "8.90"})
    cliente.post("/produtos",
                 json={"nome": "Alface", "preco": "3.50"})

    corpo = cliente.get("/produtos").json()

    assert corpo["total"] == 2
    assert [i["nome"] for i in corpo["itens"]] == [
        "Alface", "Tomate"
    ]
```
A última afirmação verifica a ordenação por nome, que é parte do contrato —
e que ninguém lembra de testar até mudar o `order_by` por engano.
:::

:::exercise level=2
Escreva o teste que garante que `DELETE /produtos/{id}` devolve `204` **sem
corpo**.

:::answer
```python
def test_apagar_devolve_204_sem_corpo(cliente_autenticado):
    criado = cliente_autenticado.post(
        "/produtos", json={"nome": "Tomate", "preco": "8.90"}
    ).json()

    resposta = cliente_autenticado.delete(
        f"/produtos/{criado['id']}"
    )

    assert resposta.status_code == 204
    assert resposta.content == b""
```
`resposta.content == b""` é a verificação que pega o erro do capítulo
@cap:primeira-api — devolver `{"ok": true}` junto com um `204`, que o padrão
HTTP proíbe.
:::

:::exercise level=2
Escreva o teste que garante que o corpo de erro `404` segue o formato
padronizado no capítulo @cap:tratamento-de-erros — e não o `detail` do
FastAPI.

:::answer
```python
def test_erro_segue_o_formato_da_api(cliente):
    corpo = cliente.get("/produtos/999").json()

    assert set(corpo) >= {"tipo", "mensagem"}
    assert "detail" not in corpo
    assert corpo["tipo"] == "produto_nao_encontrado"
```
A afirmação `"detail" not in corpo` é a que tem valor real: ela falha no dia
em que alguém escrever um `HTTPException` cru numa rota nova, reintroduzindo
o segundo formato que o capítulo de erros eliminou. É um teste sobre
consistência, não sobre comportamento — e consistência é justamente o que
ninguém percebe estar perdendo.
:::

:::exercise level=3
A suíte de API demora oito minutos e ninguém mais a roda antes de enviar
código. Descreva como diagnosticar e o que você mudaria.

:::answer
**Diagnóstico primeiro, sem adivinhar.** `pytest --durations=20` lista os
vinte testes mais lentos. Em quase todo caso, uma das três causas aparece:

1. **Banco por teste.** Cada teste cria o esquema do zero ou roda as
   migrações. Dois segundos vezes duzentos testes são quase sete minutos. O
   conserto é criar o esquema uma vez por sessão e isolar cada teste com
   transação desfeita no fim — o assunto do capítulo @cap:testando-o-banco.
2. **Teste de regra escrito na camada de API.** Trinta casos de validação de
   preço passando por HTTP, quando eles custariam milissegundos no serviço.
   Mover é o ganho maior e o menos arriscado.
3. **Espera de verdade.** `time.sleep` em teste, chamada a serviço externo,
   contêiner subindo por teste. Cada um tem conserto próprio, e todos
   começam por não existir.

**O que eu mudaria, além disso.** Separaria a suíte em duas: a rápida —
serviço e domínio, que precisa rodar em menos de dez segundos e roda a cada
salvamento — e a completa, que roda na esteira. Com `pytest -m "not lento"` e
uma marcação nos testes que tocam banco, isso custa uma linha de
configuração.

E registraria o número. "Oito minutos" precisa virar um limite acordado —
por exemplo, a suíte rápida abaixo de dez segundos — porque, sem limite, ela
cresce de volta em três meses. Suíte lenta não é um problema técnico: é um
problema de hábito, e o hábito só volta quando rodar for barato.
:::
