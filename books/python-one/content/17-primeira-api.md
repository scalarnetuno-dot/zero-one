---
title: "A primeira API"
number: 17
slug: primeira-api
part: p3
kicker: "Cinco rotas, uma lista na memória, e a primeira vez que outro programa consegue usar o seu."
goal: >-
  Escrever o CRUD completo com armazenamento em memória, receber parâmetros
  de caminho, de query e de corpo, e devolver os códigos de status certos.
---

O catálogo vai morar numa lista, dentro do processo, e sumir quando o
servidor reiniciar. É uma escolha deliberada: aqui isolamos HTTP; persistir
o dado exigirá outra decisão e outro componente.

## O esqueleto

```python title="app/routers/produtos.py" numbered
from fastapi import APIRouter

router = APIRouter(prefix="/produtos", tags=["produtos"])

_catalogo: list[dict] = [
    {"id": 1, "nome": "Tomate italiano",
     "preco": 8.90, "estoque": 120},
    {"id": 2, "nome": "Alface crespa",
     "preco": 3.50, "estoque": 40},
]
_proximo_id = 3
```

O sublinhado nos dois nomes é a convenção do capítulo @cap:encapsulamento:
isto é detalhe de implementação e vai desaparecer no capítulo
@cap:repository.

## Listar

```python title="listar" numbered
@router.get("")
def listar():
    return _catalogo
```

:::http title="A rota mais simples do CRUD"
GET /produtos
---
200 OK
Content-Type: application/json

[
  {"id": 1, "nome": "Tomate italiano", "preco": 8.9, "estoque": 120},
  {"id": 2, "nome": "Alface crespa", "preco": 3.5, "estoque": 40}
]
:::

Devolver uma lista de dicionários basta: o FastAPI converte para JSON e
escolhe `200`. Repare no `8.9` — o mesmo detalhe do capítulo
@cap:primeiro-programa, e mais um argumento a favor do `Decimal` no
capítulo @cap:schemas.

:::warning
Uma listagem sem limite é uma promessa que você não pode cumprir. Com dois
produtos, tudo bem; com oitenta mil, essa rota derruba o servidor e o cliente
junto. A paginação é o capítulo @cap:paginacao, e a hora certa de colocá-la
é antes de precisar.
:::

## Buscar um: parâmetro de caminho

```python title="buscar" numbered
from fastapi import HTTPException


@router.get("/{produto_id}")
def buscar(produto_id: int):
    for produto in _catalogo:
        if produto["id"] == produto_id:
            return produto
    raise HTTPException(
        status_code=404, detail="produto não encontrado"
    )
```

O nome entre chaves no caminho precisa ser **igual** ao nome do parâmetro na
função. A anotação `: int` faz o FastAPI converter — e recusar o que não
converte:

:::http title="Três respostas da mesma rota"
GET /produtos/1
---
200 OK

{"id": 1, "nome": "Tomate italiano", "preco": 8.9, "estoque": 120}
:::

:::http
GET /produtos/999
---
404 Not Found

{"detail": "produto não encontrado"}
:::

:::http
GET /produtos/abc
---
422 Unprocessable Entity

{
  "detail": [
    {
      "type": "int_parsing",
      "loc": ["path", "produto_id"],
      "msg": "Input should be a valid integer"
    }
  ]
}
:::

Essa terceira resposta merece atenção: a função `buscar` **nunca rodou**. A
conversão falhou antes, e o FastAPI montou uma resposta que diz onde
(`["path", "produto_id"]`), o quê (`int_parsing`) e por quê. Você não
escreveu uma linha para isso.

:::key
`404` e `422` dizem coisas diferentes. `404` é "a requisição estava bem
formada e o recurso não existe"; `422` é "a requisição está malformada e eu
nem cheguei a procurar". Confundir os dois é a forma mais rápida de deixar
quem consome a API sem saber se deve tentar de novo.
:::

## Parâmetros de query

Todo parâmetro que **não** está no caminho e é de tipo simples vira query:

```python title="listar com filtro" numbered
@router.get("")
def listar(
    q: str | None = None,
    apenas_disponiveis: bool = False,
):
    itens = _catalogo

    if q:
        termo = q.lower()
        itens = [p for p in itens if termo in p["nome"].lower()]

    if apenas_disponiveis:
        itens = [p for p in itens if p["estoque"] > 0]

    return itens
```

```text
GET /produtos?q=tomate
GET /produtos?apenas_disponiveis=true
GET /produtos?q=al&apenas_disponiveis=true
```

O `bool` aceita `true`, `1`, `yes`, `on` e as variantes em maiúsculas — e
recusa o resto com `422`. O `str | None = None` torna o parâmetro opcional,
exatamente pelo motivo do capítulo @cap:tipagem-e-dataclasses: o que torna
opcional é o **valor padrão**.

## Criar: o corpo da requisição

```python title="criar" numbered
from fastapi import status


@router.post("", status_code=status.HTTP_201_CREATED)
def criar(produto: dict):
    global _proximo_id

    novo = {
        "id": _proximo_id,
        "nome": produto["nome"],
        "preco": produto["preco"],
        "estoque": produto.get("estoque", 0),
    }
    _catalogo.append(novo)
    _proximo_id += 1
    return novo
```

:::http title="Criar devolve 201 e o recurso criado"
POST /produtos
Content-Type: application/json

{"nome": "Cenoura", "preco": 5.25, "estoque": 60}
---
201 Created

{"id": 3, "nome": "Cenoura", "preco": 5.25, "estoque": 60}
:::

O `status_code` no decorador muda o padrão de `200` para `201`. Usar a
constante `status.HTTP_201_CREATED` em vez do número cru é o mesmo argumento
do `Enum` do capítulo @cap:tipagem-e-dataclasses: o número errado não
reclama, o nome errado reclama.

:::pitfall
`produto: dict` aceita **qualquer coisa**. Um corpo sem `nome` derruba a
rota com `KeyError`, que vira `500` — a API culpando a si mesma por um erro
de quem chamou. Um corpo com `{"preco": "muito caro"}` entra no catálogo e
só explode depois, em outro lugar. O conserto é o capítulo
@cap:modelando-com-pydantic, e é o próximo.
:::

## Atualizar e apagar

```python title="atualizar e apagar" numbered
@router.put("/{produto_id}")
def atualizar(produto_id: int, dados: dict):
    for produto in _catalogo:
        if produto["id"] == produto_id:
            produto["nome"] = dados["nome"]
            produto["preco"] = dados["preco"]
            produto["estoque"] = dados.get("estoque", 0)
            return produto
    raise HTTPException(404, "produto não encontrado")


@router.delete("/{produto_id}", status_code=204)
def apagar(produto_id: int):
    for i, produto in enumerate(_catalogo):
        if produto["id"] == produto_id:
            del _catalogo[i]
            return None
    raise HTTPException(404, "produto não encontrado")
```

:::http title="Apagar não devolve corpo"
DELETE /produtos/3
---
204 No Content
:::

`204` significa "deu certo e não há nada para devolver". A função retorna
`None`, e o FastAPI respeita o status declarado. Devolver `{"ok": true}` com
`204` é um erro: o padrão HTTP proíbe corpo nessa resposta, e alguns clientes
se comportam de forma imprevisível quando ele aparece.

| Operação | Verbo | Status de sucesso |
|---|---|---|
| criar | `POST` | `201 Created` |
| listar / buscar | `GET` | `200 OK` |
| substituir | `PUT` | `200 OK` |
| alterar em parte | `PATCH` | `200 OK` |
| apagar | `DELETE` | `204 No Content` |

Tabela: Um `200` em tudo funciona e desperdiça informação que o cliente
poderia usar sem ler o corpo.

## `PUT` e `PATCH` não são a mesma coisa

`PUT` **substitui** o recurso inteiro: o que não veio no corpo deveria ser
apagado ou voltar ao padrão. `PATCH` altera **só os campos enviados**.

A implementação acima é um `PUT` honesto — ela exige `nome` e `preco` e
zera o estoque se ele não vier. A armadilha é escrever um `PUT` que se
comporta como `PATCH`: quem chama manda só o preço, supõe que o resto ficou
intacto, e descobre em produção que o nome virou `None`.

:::key
Escolha um dos dois e implemente o que escolheu. `PATCH` parcial de verdade
precisa distinguir "campo ausente" de "campo enviado como nulo" — e isso
exige o recurso do capítulo @cap:schemas, `exclude_unset`. Até lá, `PUT`
completo é a escolha honesta.
:::

## A lista na memória é mentira

O protótipo funciona, mas não deve ser confundido com o sistema final. Seus
limites são claros:

- **O dado some.** Reiniciou, acabou. O banco resolverá isso.
- **Não há validação.** `dict` aceita qualquer coisa.
- **A busca é linear.** `for` em oitenta mil itens, a cada requisição.
- **Não é seguro com concorrência.** Dois `POST` simultâneos podem receber o
  mesmo `_proximo_id`. O banco resolve isso com sequência.
- **A regra de negócio está na rota.**

:::story O protótipo que foi para produção
— Está funcionando — disse Rafa, virando a tela.

Estava. Cinco rotas, documentação bonita, o `/docs` respondendo.

— Funciona para nós dois — disse Bia. — Quantos produtos tem aí?

— Dois.

— E quando o servidor reinicia?

Rafa recarregou a página. A lista voltou a ter dois produtos: os dois do
código.

— Ah.

— Não é "ah" — disse Bia. — É exatamente onde a gente deveria estar. O
problema é quando alguém vê isso funcionando numa reunião e pergunta se já
dá para começar a cadastrar.
:::

:::summary
- Parâmetro no caminho vira `path`; parâmetro simples fora dele vira query.
- A anotação de tipo converte e recusa antes de a sua função rodar.
- `404` é "não existe"; `422` é "nem cheguei a procurar".
- `201` para criação, `204` sem corpo para remoção.
- `PUT` substitui tudo; `PATCH` altera parte — implemente o que escolheu.
- `dict` como corpo é a ausência de um contrato.
:::

:::milestone
O CRUD está completo e outro programa já consegue usá-lo. Os cinco defeitos
listados acima são riscos conhecidos, não detalhes escondidos.
:::

:::exercise level=1
Acrescente uma rota `GET /produtos/contagem` que devolva
`{"total": <quantidade>}`. Cuidado com a ordem das rotas.

:::answer
```python
@router.get("/contagem")
def contagem():
    return {"total": len(_catalogo)}
```
Ela precisa ser registrada **antes** de `@router.get("/{produto_id}")`. Caso
contrário, `contagem` casa com o parâmetro e a resposta é `422`.
:::

:::exercise level=2
Implemente `PATCH /produtos/{id}` que altere apenas os campos presentes no
corpo, mantendo os demais.

:::answer
```python
@router.patch("/{produto_id}")
def alterar(produto_id: int, dados: dict):
    for produto in _catalogo:
        if produto["id"] == produto_id:
            for campo in ("nome", "preco", "estoque"):
                if campo in dados:
                    produto[campo] = dados[campo]
            return produto
    raise HTTPException(404, "produto não encontrado")
```
O `if campo in dados` é o coração do `PATCH`: ele distingue "não veio" de
"veio vazio". Com `dados.get(campo)`, um campo ausente viraria `None` e o
`PATCH` apagaria o dado — que é exatamente o defeito descrito no capítulo.
:::

:::exercise level=3
A rota de criação tem um defeito de concorrência. Descreva o cenário exato
em que dois clientes recebem o mesmo `id`, e explique por que o banco de
dados resolve isso e um `lock` em Python resolveria apenas em parte.

:::answer
O cenário: duas requisições chegam quase juntas. A primeira lê `_proximo_id`
(valor 3) e é suspensa antes de incrementar — porque o servidor cedeu a vez,
ou porque outro trabalhador assumiu. A segunda lê o mesmo 3, cria o produto e
incrementa para 4. A primeira retoma, cria **outro** produto com id 3 e
incrementa para 5. Dois produtos com o mesmo identificador, e o id 4 pulado.

O banco resolve porque a geração do identificador acontece **dentro** dele,
numa sequência atômica que nenhuma transação vê pela metade. É uma garantia
do banco, não do seu código, e por isso vale para todos os processos
simultaneamente.

Um `threading.Lock` protegeria o trecho dentro de **um** processo Python. Em
produção a aplicação roda com vários trabalhadores — e muitas vezes em várias
máquinas —, cada um com a sua memória e a sua trava. A trava não atravessa
processo, e o defeito volta inteiro. Essa é a diferença entre exclusão mútua
local e uma garantia compartilhada, e é o motivo pelo qual "contador em
variável global" nunca sobrevive a um servidor de verdade.
:::
