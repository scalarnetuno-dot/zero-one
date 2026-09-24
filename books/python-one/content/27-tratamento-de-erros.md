---
title: "Tratamento de erros"
number: 27
slug: tratamento-de-erros
part: p5
kicker: "A resposta de erro é a parte da API que mais gente lê e menos gente projeta."
goal: >-
  Substituir os `try` espalhados por tratadores globais, padronizar o corpo
  de erro, registrar o que interessa e nunca vazar detalhe interno.
---

O capítulo @cap:o-crud-completo deixou cinco blocos `try` idênticos nas
rotas. Eles funcionam e são o tipo de código que se multiplica: cada rota
nova traz os seus, cada exceção nova exige revisitar todas as rotas, e
basta alguém esquecer um para que um `409` vire `500`.

O FastAPI permite registrar o tratamento uma vez.

## Um tratador por exceção de domínio

```python title="app/errors.py" numbered
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.services.produto import (
    EstoqueInsuficiente,
    ProdutoJaExiste,
    ProdutoNaoEncontrado,
)


def registrar_tratadores(app: FastAPI) -> None:

    @app.exception_handler(ProdutoNaoEncontrado)
    async def _nao_encontrado(
        request: Request, exc: ProdutoNaoEncontrado
    ):
        return JSONResponse(
            status_code=404,
            content={
                "tipo": "produto_nao_encontrado",
                "mensagem": str(exc),
                "recurso_id": exc.produto_id,
            },
        )

    @app.exception_handler(ProdutoJaExiste)
    async def _ja_existe(request: Request, exc: ProdutoJaExiste):
        return JSONResponse(
            status_code=409,
            content={
                "tipo": "produto_ja_existe",
                "mensagem": str(exc),
                "nome": exc.nome,
            },
        )

    @app.exception_handler(EstoqueInsuficiente)
    async def _estoque(
        request: Request, exc: EstoqueInsuficiente
    ):
        return JSONResponse(
            status_code=409,
            content={
                "tipo": "estoque_insuficiente",
                "mensagem": str(exc),
                "disponivel": exc.disponivel,
                "pedido": exc.pedido,
            },
        )
```

```python title="app/main.py" numbered
from app.errors import registrar_tratadores

app = FastAPI(title=config.app_nome)
registrar_tratadores(app)
```

E as rotas voltam a ser o que deveriam ser:

```python title="app/routers/produtos.py" numbered
@router.get("/{produto_id}", response_model=ProdutoLer)
def buscar(produto_id: int, servico: ServicoDep):
    return servico.buscar(produto_id)
```

Uma linha. A exceção do serviço sobe, ninguém a captura no caminho, e o
tratador registrado a converte na saída.

:::key
Os campos anexados às exceções no capítulo @cap:excecoes — `produto_id`,
`disponivel`, `pedido` — se pagam exatamente aqui. O tratador monta a
resposta a partir dos **dados**, não do texto da mensagem. É o que permite
traduzir, mudar o texto e acrescentar campos sem tocar em quem levanta.
:::

## O formato do erro

Quatro formatos convivem no mundo, e o pior é não escolher nenhum:

| Formato | Exemplo |
|---|---|
| FastAPI padrão | `{"detail": "..."}` |
| Lista de validação | `{"detail": [{...}, {...}]}` |
| Problem Details (RFC 9457) | `{"type": "...", "title": "...", "status": 404}` |
| Próprio | `{"tipo": "...", "mensagem": "..."}` |

Tabela: O que importa não é qual — é que **todas** as respostas de erro da
sua API tenham o mesmo formato.

O Problem Details é um padrão de verdade, com `Content-Type` próprio
(`application/problem+json`), e vale a pena quando a API é pública ou quando
há vários serviços na empresa. O formato próprio vale quando a API é interna
e o time inteiro concorda.

:::pitfall
O erro comum não é escolher errado: é ter **três** formatos na mesma API. Os
`422` do Pydantic vêm com `detail` em lista, os `HTTPException` vêm com
`detail` em texto, e os tratadores novos vêm com `tipo` e `mensagem`. Quem
consome precisa de três caminhos de tratamento para a mesma API. Padronize
sobrescrevendo também o tratador de validação.
:::

## Padronizando o `422`

```python title="app/errors.py" numbered
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def _validacao(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "tipo": "requisicao_invalida",
            "mensagem": "Um ou mais campos estão inválidos.",
            "campos": [
                {
                    "campo": ".".join(str(p) for p in e["loc"][1:]),
                    "erro": e["type"],
                    "detalhe": e["msg"],
                }
                for e in exc.errors()
            ],
        },
    )
```

:::http title="Agora todo erro tem a mesma cara"
POST /produtos
Content-Type: application/json

{"preco": "-5"}
---
422 Unprocessable Entity

{
  "tipo": "requisicao_invalida",
  "mensagem": "Um ou mais campos estão inválidos.",
  "campos": [
    {"campo": "nome", "erro": "missing",
     "detalhe": "Field required"},
    {"campo": "preco", "erro": "greater_than",
     "detalhe": "Input should be greater than 0"}
  ]
}
:::

O `e["loc"][1:]` corta o primeiro elemento, que é sempre `"body"`, `"query"`
ou `"path"`. Se essa informação for útil para o seu cliente, mantenha-a num
campo separado em vez de descartá-la.

## O `500`: o único erro que é seu

```python title="app/errors.py" numbered
import logging
import uuid

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def _nao_tratado(request: Request, exc: Exception):
    incidente = uuid.uuid4().hex[:12]

    logger.exception(
        "erro nao tratado incidente=%s metodo=%s caminho=%s",
        incidente, request.method, request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "tipo": "erro_interno",
            "mensagem": (
                "Erro inesperado. Informe o código ao suporte."
            ),
            "incidente": incidente,
        },
    )
```

Duas decisões, e as duas são de segurança.

O corpo **não** contém o traceback, nem a mensagem original, nem o nome da
exceção. Um `IntegrityError` devolvido ao cliente entrega o nome da tabela,
o nome da restrição e às vezes o valor de outra linha. Mensagens de erro são
uma fonte clássica de vazamento de informação.

E o `incidente` costura as duas pontas: o cliente tem um código para
informar, o log tem o mesmo código junto do traceback inteiro. Sem ele, o
suporte recebe "deu erro às três da tarde" e precisa adivinhar qual das
quatro mil linhas de log é a certa.

:::warning
Esse tratador captura `Exception`, nunca `BaseException` — pelo motivo do
capítulo @cap:excecoes. E ele precisa ser o **último** registrado: os
tratadores mais específicos ganham, mas depender da ordem de registro para
isso é frágil. Registre do mais específico para o mais genérico.
:::

## Identificador de correlação

```python title="app/middleware.py" numbered
@app.middleware("http")
async def correlacao(request: Request, call_next):
    rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex
    request.state.request_id = rid

    resposta = await call_next(request)
    resposta.headers["X-Request-Id"] = rid
    return resposta
```

Quando a requisição atravessa três serviços, esse cabeçalho é o que permite
juntar os logs dos três numa linha do tempo só. Se o cliente enviou um, use
o dele; se não, gere.

## Que status para quê

| Situação | Status |
|---|---|
| campo inválido ou faltando | `422` |
| requisição malformada (JSON quebrado) | `400` |
| sem credencial ou credencial inválida | `401` |
| credencial válida, sem permissão | `403` |
| recurso não existe | `404` |
| conflito com o estado atual | `409` |
| erro do servidor | `500` |

Tabela: `401` e `403` são os mais confundidos: um é "não sei quem você é",
o outro é "sei quem você é e não pode". O capítulo @cap:usuarios-e-permissoes
volta a isso.

:::story O código que não existia
O produtor ligou reclamando que o cadastro não salvava.

— Que erro aparece? — perguntou Rafa.

— Diz "Erro inesperado".

— Só isso?

— Só isso.

Rafa abriu o log das últimas duas horas. Quatro mil e duzentas linhas. Três
`500`, todos com traceback, todos parecidos, nenhum com hora exata que
batesse — o produtor não lembrava o minuto.

Gastou quarenta minutos e escolheu um por eliminação. Era o errado.

Na semana seguinte, a mensagem passou a terminar com um código de doze
caracteres. O próximo telefonema durou três minutos.
:::

:::summary
- Registre tratadores uma vez; rotas não capturam exceção de domínio.
- O tratador monta a resposta a partir dos campos da exceção, não do texto.
- Toda resposta de erro da API precisa do mesmo formato — inclusive o `422`.
- `500` nunca vaza traceback, nome de tabela ou mensagem interna.
- Código de incidente na resposta, traceback no log, o mesmo código nos dois.
- `401` é "não sei quem você é"; `403` é "sei e você não pode".
:::

:::milestone
A API parou de contar sobre si mesma para quem não deveria saber — e passou
a dizer, para quem precisa, exatamente o que aconteceu.
:::

:::exercise level=1
Registre um tratador para `ProdutorNaoEncontrado` devolvendo `404` no mesmo
formato dos demais.

:::answer
```python
@app.exception_handler(ProdutorNaoEncontrado)
async def _produtor_nao_encontrado(
    request: Request, exc: ProdutorNaoEncontrado
):
    return JSONResponse(
        status_code=404,
        content={
            "tipo": "produtor_nao_encontrado",
            "mensagem": str(exc),
            "recurso_id": exc.produtor_id,
        },
    )
```
Três tratadores com o mesmo formato já pedem uma função auxiliar que receba
status, tipo e campos extras. Quatro exigem.
:::

:::exercise level=2
Crie uma exceção base `ErroDoCatalogo` com `status` e `tipo` como atributos
de classe, e um único tratador para todas as exceções do domínio.

:::answer
```python
class ErroDoCatalogo(Exception):
    status = 400
    tipo = "erro_do_catalogo"

    def detalhes(self) -> dict:
        return {}


class ProdutoNaoEncontrado(ErroDoCatalogo):
    status = 404
    tipo = "produto_nao_encontrado"

    def __init__(self, produto_id: int):
        self.produto_id = produto_id
        super().__init__(f"produto {produto_id} não encontrado")

    def detalhes(self) -> dict:
        return {"recurso_id": self.produto_id}


@app.exception_handler(ErroDoCatalogo)
async def _dominio(request: Request, exc: ErroDoCatalogo):
    return JSONResponse(
        status_code=exc.status,
        content={
            "tipo": exc.tipo,
            "mensagem": str(exc),
            **exc.detalhes(),
        },
    )
```
Um tratador para toda a família. Exceção nova só precisa declarar `status`,
`tipo` e o que quer expor — e não exige tocar em `errors.py`.
:::

:::exercise level=3
Um colega propõe devolver o traceback no corpo do `500` "só em ambiente de
desenvolvimento", controlado por variável de ambiente. Avalie a proposta.

:::answer
A ideia é boa e a implementação proposta é o problema.

O que se ganha é real: em desenvolvimento, ver o traceback na resposta
economiza a ida ao terminal, principalmente quando quem chama é um front-end
em outra máquina.

O que se arrisca é a variável. `APP_AMBIENTE` é uma string, definida por
configuração, e um dia ela vai estar errada em produção — por um `.env`
copiado, por uma variável não definida que caiu no padrão, por um contêiner
promovido de homologação. No dia em que isso acontecer, a API passa a
publicar tracebacks, e ninguém vai perceber, porque nada quebra.

A versão defensável inverte o padrão: o comportamento seguro é o que vale
quando a configuração falta, e o inseguro exige um valor explícito e
improvável.

```python
mostrar = config.app_ambiente == "dev" and config.debug_erros
```

Duas condições, uma delas sem valor padrão permissivo. E, ainda assim, eu
prefiro a alternativa que não corre risco nenhum: deixar o traceback só no
log e rodar o log em primeiro plano no terminal durante o desenvolvimento.
Ganha-se a mesma informação, no mesmo segundo, e não existe configuração
capaz de vazá-la.
:::
