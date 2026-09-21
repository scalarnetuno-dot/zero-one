---
title: "O primeiro projeto"
number: 16
slug: primeiro-projeto-fastapi
part: p3
kicker: "Um arquivo `main.py` de mil linhas nunca foi uma decisão. Foi a ausência de uma."
goal: >-
  Montar a estrutura de pastas do projeto, separar rotas com `APIRouter`,
  carregar configuração de variáveis de ambiente e deixar tudo rodando com um
  comando.
---

O FastAPI não impõe estrutura de pastas. Isso é liberdade e é também uma
armadilha: sem uma decisão tomada no começo, todo projeto converge para o
mesmo destino, um `main.py` com trezentas rotas, quinze imports de banco e
nenhuma fronteira.

Esta é a estrutura que o catálogo vai usar: pequena o bastante para caber na
cabeça, explícita o bastante para não virar um `main.py` de trezentas linhas.

## A estrutura

:::tree title="A estrutura inicial do projeto"
catalogo/
  app/
    __init__.py
    main.py              # cria o app e inclui os routers
    config.py            # lê o ambiente
    routers/
      __init__.py
      produtos.py        # as rotas de /produtos
  tests/
    __init__.py
  .env                   # nunca versionado
  .env.example           # versionado, sem valor real
  requirements.txt
:::

Quatro pastas vão nascer nos próximos capítulos — `models`, `schemas`,
`repositories`, `services` —, cada uma no capítulo em que ganhar sentido.
Criar as sete de uma vez, vazias, é cerimônia sem conteúdo.

:::key
A regra que organiza tudo: **uma pasta por responsabilidade, e a pasta só
nasce quando tiver o que guardar**. Estrutura criada antes do problema é
suposição; estrutura criada junto com o problema é desenho.
:::

## As dependências

```text title="requirements.txt"
fastapi[standard]==0.115.6
pydantic-settings==2.7.0
```

```text
$ python -m venv .venv
$ source .venv/bin/activate
$ pip install -r requirements.txt
```

O `fastapi[standard]` traz junto o Uvicorn, o cliente HTTP usado nos testes
e as ferramentas de linha de comando. Os colchetes são **extras**: pacotes
opcionais que o autor da biblioteca agrupou sob um nome.

## Configuração: o ambiente, não o código

```text title=".env"
APP_NOME=Catálogo Sabiá
APP_AMBIENTE=dev
DATABASE_URL=postgresql+psycopg://catalogo:senha@localhost/catalogo
SECRET_KEY=nao-use-isto-em-producao
```

```text title=".env.example"
APP_NOME=Catálogo Sabiá
APP_AMBIENTE=dev
DATABASE_URL=
SECRET_KEY=
```

O `.env.example` entra no repositório; o `.env` nunca. Quem clona o projeto
copia um para o outro e preenche. Sem esse par de arquivos, a lista de
variáveis necessárias mora na cabeça de quem configurou o servidor pela
primeira vez.

```python title="app/config.py" numbered
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="", extra="ignore"
    )

    app_nome: str = "Catálogo"
    app_ambiente: str = "dev"
    database_url: str = ""
    secret_key: str = ""


@lru_cache
def get_config() -> Config:
    return Config()
```

Três coisas acontecem aqui, e todas são conquistas.

A classe lê o `.env` **e** as variáveis de ambiente de verdade, com as
segundas ganhando da primeira — que é exatamente o que se quer em produção,
onde não existe arquivo `.env` e sim variáveis injetadas pelo orquestrador.

Os tipos são conferidos: se alguém escrever `APP_PORTA=oitenta` e o campo
for `int`, a aplicação **não sobe**, e o erro diz qual variável e por quê.
Falhar na partida é infinitamente melhor que falhar na primeira requisição
do dia.

E o `@lru_cache` faz a configuração ser lida uma vez só. Toda chamada
seguinte a `get_config()` devolve o mesmo objeto.

:::pitfall
Não crie `config = Config()` solto no módulo. Isso lê o ambiente **na
importação**, o que quebra teste — que precisa trocar variáveis antes de
carregar a aplicação — e transforma um erro de configuração numa falha de
import, com traceback indecifrável. A função com cache resolve os dois casos.
:::

## `APIRouter`: rotas fora do `main`

```python title="app/routers/produtos.py" numbered
from fastapi import APIRouter

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get("")
def listar():
    return []


@router.get("/{produto_id}")
def buscar(produto_id: int):
    return {"id": produto_id}
```

Um `APIRouter` é um `app` em miniatura: ele registra rotas do mesmo jeito,
mas não sabe servir sozinho. O `prefix` evita repetir `/produtos` em cada
rota, e `tags` agrupa os endpoints na documentação — o que faz diferença
visível quando o projeto passar de vinte rotas.

```python title="app/main.py" numbered
from fastapi import FastAPI

from app.config import get_config
from app.routers import produtos

config = get_config()

app = FastAPI(
    title=config.app_nome,
    version="0.1.0",
    summary="API do catálogo da Cooperativa Sabiá",
)

app.include_router(produtos.router)


@app.get("/saude", tags=["infra"])
def saude():
    return {"status": "de pé", "ambiente": config.app_ambiente}
```

```text
$ fastapi dev app/main.py
```

:::practice
Abra `/docs`. Os endpoints agora aparecem em dois grupos, **produtos** e
**infra**, com o título e o resumo que você escreveu no `FastAPI(...)`.
Nenhuma linha de documentação foi escrita — só metadados no lugar certo.
:::

## O detalhe do caminho vazio

Repare em `@router.get("")`, com aspas vazias, e não `@router.get("/")`. Com
o prefixo `/produtos`, a segunda forma produziria `/produtos/`, com barra no
fim — um endereço diferente de `/produtos` para qualquer cliente HTTP
rigoroso.

O FastAPI redireciona de um para o outro com `307`, o que funciona e tem um
custo: uma ida e volta a mais em toda chamada, e problemas conhecidos quando
a API está atrás de um proxy que reescreve o esquema. Escolha uma forma e
mantenha.

## A ordem das rotas importa

```python title="ordem.py" numbered
@router.get("/{produto_id}")
def buscar(produto_id: int):
    ...


@router.get("/destaques")     # nunca é alcançada
def destaques():
    ...
```

O FastAPI testa as rotas na ordem em que foram registradas. `/destaques`
casa com `/{produto_id}` primeiro, e a requisição chega em `buscar` com
`produto_id="destaques"` — que falha na conversão para inteiro e devolve
`422`.

:::key
Rotas com caminho fixo vêm **antes** das rotas com parâmetro. Essa é uma das
poucas regras do FastAPI em que a ordem do código muda o comportamento, e é
a causa de um `422` misterioso que aparece em quase todo projeto uma vez.
:::

## Middleware: o que acontece em toda requisição

```python title="app/main.py" numbered
import time

from fastapi import Request


@app.middleware("http")
async def medir_tempo(request: Request, call_next):
    inicio = time.perf_counter()
    resposta = await call_next(request)
    duracao = time.perf_counter() - inicio
    resposta.headers["X-Tempo"] = f"{duracao:.4f}"
    return resposta
```

Middleware envolve **todas** as rotas. Ele é o lugar de coisas transversais:
medir tempo, registrar log de acesso, acrescentar um identificador de
correlação. O `await` aí é o assunto do capítulo @cap:async; por enquanto,
copie a forma.

:::warning
Middleware roda em toda requisição, inclusive nas que falham. Colocar
consulta ao banco, chamada de rede ou qualquer coisa lenta aí dentro é
multiplicar esse custo pelo número de requisições do dia. Se a operação só
interessa a algumas rotas, ela é uma dependência do capítulo
@cap:dependency-injection, não um middleware.
:::

## CORS, para quando houver um navegador

```python title="cors.py" numbered
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Se a API for consumida por uma página web servida de outro endereço, o
navegador exige essa permissão — e a ausência dela produz o erro mais
frustrante da vida de quem começa: a requisição funciona no `curl`, funciona
no `/docs`, e falha no navegador sem explicação útil.

:::pitfall
`allow_origins=["*"]` combinado com `allow_credentials=True` é recusado pelo
próprio padrão, e muita gente perde uma tarde nisso. Liste as origens
explicitamente. Em produção, `*` é uma decisão de segurança que quase nunca
é a certa.
:::

:::summary
- A pasta nasce quando tem o que guardar, não antes.
- `.env` fica fora do repositório; `.env.example` fica dentro.
- Configuração tipada falha na partida, não na primeira requisição.
- `APIRouter` com `prefix` e `tags` tira as rotas do `main` e organiza a
  documentação.
- Caminho fixo antes de caminho com parâmetro.
- Middleware é para o que vale para todas as rotas.
:::

:::milestone
O projeto tem estrutura, configuração e rotas separadas. Ele ainda não
guarda nada — mas já tem o formato que vai manter por mais vinte e cinco
capítulos.
:::

:::exercise level=1
Crie um `APIRouter` para produtores, com prefixo `/produtores` e tag
`produtores`, com uma rota que devolva uma lista vazia. Inclua no `main`.

:::answer
```python title="app/routers/produtores.py"
from fastapi import APIRouter

router = APIRouter(prefix="/produtores", tags=["produtores"])


@router.get("")
def listar():
    return []
```

```python title="app/main.py"
from app.routers import produtores

app.include_router(produtores.router)
```
:::

:::exercise level=2
Acrescente ao `Config` um campo `app_porta: int = 8000` e escreva no `.env`
o valor `oitenta`. Suba a aplicação e leia o erro.

:::answer
```text
pydantic_settings.exceptions.SettingsError: error parsing
value for field "app_porta" from source "DotEnvSettingsSource"
...
Input should be a valid integer, unable to parse string as
an integer [type=int_parsing, input_value='oitenta']
```
A aplicação não sobe, e a mensagem diz o campo, a origem e o motivo. Compare
com o que aconteceria se `app_porta` fosse lida como texto e convertida só
no momento de usar: a falha apareceria em outro lugar, em outro momento, sem
dizer que a origem era o `.env`.
:::

:::exercise level=3
Você recebeu um projeto com um `main.py` de novecentas linhas e quarenta
rotas. Descreva, em passos, como quebrá-lo em routers sem parar o
desenvolvimento do time por uma semana.

:::answer
1. **Nada de reescrita.** Crie `app/routers/` e mova **um** grupo de rotas,
   o menos movimentado, para um arquivo próprio. Rode a aplicação e confira
   o `/docs`: a lista de endpoints precisa ficar idêntica.
2. **Congele o contrato.** Antes de mover qualquer coisa, salve o
   `/openapi.json` atual num arquivo. Depois de cada movimentação, compare.
   Se o esquema não mudou, nada quebrou para quem consome.
3. **Um grupo por vez, um commit por grupo.** Mover é copiar e apagar, não
   editar: a tentação de "já que estou aqui, melhoro essa rota" é o que faz
   a migração virar uma semana parada.
4. **Deixe o `main.py` com o que é dele**: criar o app, ler configuração,
   incluir routers, middleware. Se sobrar regra de negócio lá, ela ainda
   não tem casa — e a casa dela é o capítulo @cap:service.

O passo 2 é o que permite fazer isso com o time trabalhando: enquanto o
esquema público não muda, a reorganização é invisível de fora.
:::
