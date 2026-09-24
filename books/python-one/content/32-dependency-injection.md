---
title: "Injeção de dependência"
number: 32
slug: dependency-injection
part: p6
kicker: "O framework monta o grafo de objetos a cada requisição — e você o descreve com anotações de tipo."
goal: >-
  Entender decoradores por dentro, escrever dependências com e sem `yield`,
  encadeá-las, e substituí-las em teste sem tocar no código de produção.
---

`Depends` parece pequeno na rota, mas esconde um grafo de objetos. Para
entendê-lo, comece um degrau abaixo: o decorador, a construção Python sobre a
qual todo o mecanismo se apoia.

## Decorador: uma função que recebe uma função

```python title="decorador.py" numbered
def registrar(funcao):
    def dentro(*args, **kwargs):
        print(f"chamando {funcao.__name__}")
        return funcao(*args, **kwargs)
    return dentro


@registrar
def somar(a, b):
    return a + b


print(somar(2, 3))
```

```text
chamando somar
5
```

`@registrar` acima de `def somar` é exatamente isto:

```python
somar = registrar(somar)
```

`registrar` recebe a função original, cria uma nova que faz algo a mais, e
devolve essa nova no lugar do nome antigo. Não há palavra-chave mágica — há
uma função devolvendo outra função.

:::pitfall
A função devolvida perde o nome e a documentação da original:
`somar.__name__` passa a ser `"dentro"`. O conserto é uma linha,
`@functools.wraps(funcao)` acima do `def dentro`, e a ausência dela quebra
tudo que inspeciona funções — inclusive o próprio FastAPI.
:::

Quando o decorador aceita argumento, há um nível a mais:

```python title="com_argumento.py" numbered
def repetir(vezes):
    def decorador(funcao):
        def dentro(*args, **kwargs):
            for _ in range(vezes):
                resultado = funcao(*args, **kwargs)
            return resultado
        return dentro
    return decorador


@repetir(3)
def avisar():
    print("oi")
```

`@repetir(3)` chama `repetir`, que devolve `decorador`, que recebe `avisar`.
É por isso que `@app.get("/saude")` tem parênteses e `@registrar` não: o
primeiro precisa do caminho antes de saber o que fazer com a função.

## `Depends`: o framework monta o que a função pediu

```python title="dependencia.py" numbered
from typing import Annotated

from fastapi import Depends


def paginacao(pagina: int = 1, tamanho: int = 20) -> dict:
    return {
        "pagina": max(1, pagina),
        "tamanho": max(1, min(tamanho, 100)),
    }


PaginacaoDep = Annotated[dict, Depends(paginacao)]


@router.get("")
def listar(servico: ServicoDep, pag: PaginacaoDep):
    return servico.listar(**pag)
```

O FastAPI lê a assinatura de `listar`, vê que `pag` é `Depends(paginacao)`,
e **chama `paginacao` antes**. E como `paginacao` também tem parâmetros com
tipos simples, eles viram parâmetros de query da rota — e aparecem na
documentação de `/docs` como se estivessem escritos ali.

:::key
Uma dependência é uma função comum que o framework chama por você, passando
o que ela pedir, antes de chamar a sua rota. Não há registro, não há
contêiner de configuração, não há XML. A declaração é a anotação de tipo.
:::

## Dependência com `yield`: abrir e fechar

```python title="app/dependencies.py" numbered
def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

O que vem antes do `yield` roda **antes** da rota; o que vem depois roda
**depois da resposta ser montada**. É o `with` do capítulo @cap:excecoes
aplicado ao ciclo de vida da requisição.

Isso vale para qualquer recurso que precise ser devolvido: sessão de banco,
cliente HTTP, trava distribuída, arquivo temporário.

:::warning
Código depois do `yield` roda **depois** que a resposta foi gerada, mas
ainda dentro da requisição. Se ele levantar exceção, a resposta já não pode
ser alterada — e o cliente recebe algo inconsistente. Mantenha essa parte
curta e à prova de falha: fechar, liberar, e nada mais.
:::

## Encadeamento

```python title="cadeia.py" numbered
def get_session() -> Generator[Session, None, None]:
    ...


SessaoDep = Annotated[Session, Depends(get_session)]


def get_repo(session: SessaoDep) -> ProdutoRepositorioSQL:
    return ProdutoRepositorioSQL(session)


RepoDep = Annotated[ProdutoRepositorioSQL, Depends(get_repo)]


def get_servico(
    session: SessaoDep, repo: RepoDep
) -> ProdutoServico:
    return ProdutoServico(session, repo)


ServicoDep = Annotated[ProdutoServico, Depends(get_servico)]
```

Uma dependência pode depender de outra, e o FastAPI resolve o grafo inteiro
na ordem certa.

:::diagram type="blocks" caption="O framework monta o grafo a cada requisição, de baixo para cima."
rows:
  - [{ text: "rota", note: "declara ServicoDep" }]
  - [{ text: "get_servico", note: "pede sessão e repositório" }]
  - [{ text: "get_repo", note: "pede sessão" }]
  - [{ text: "get_session", note: "abre, entrega, fecha" }]
:::

Repare que `get_session` aparece em dois caminhos — como dependência de
`get_repo` e de `get_servico`. Ela é chamada **uma vez só** por requisição:
o FastAPI guarda o resultado em cache durante a requisição, o que garante que
serviço e repositório compartilhem a mesma sessão, e portanto a mesma
transação.

:::key
Esse cache é o que faz o desenho funcionar. Se cada camada recebesse uma
sessão diferente, o `commit` do serviço não confirmaria o que o repositório
escreveu — estariam em transações distintas. Para desligar esse
comportamento existe `Depends(f, use_cache=False)`, que quase nunca é o que
se quer.
:::

## Dependência que não devolve nada

```python title="guarda.py" numbered
import secrets

def exigir_api_key(x_api_key: Annotated[str | None, Header()] = None):
    esperada = get_config().api_key
    if x_api_key is None or not secrets.compare_digest(
        x_api_key, esperada
    ):
        raise HTTPException(401, "chave inválida")


@router.post("", dependencies=[Depends(exigir_api_key)])
def criar(dados: ProdutoCriar, servico: ServicoDep):
    ...
```

Quando a dependência só verifica, ela não precisa ser um parâmetro: entra na
lista `dependencies` do decorador. O valor é descartado; o efeito é a
exceção que ela pode levantar.

O mesmo vale para um router inteiro, ou para a aplicação:

```python
router = APIRouter(
    prefix="/admin", dependencies=[Depends(exigir_api_key)]
)
```

Essa é a base do capítulo @cap:usuarios-e-permissoes.

## Dependência como classe

```python title="classe.py" numbered
class Paginacao:
    def __init__(self, pagina: int = 1, tamanho: int = 20):
        self.pagina = max(1, pagina)
        self.tamanho = max(1, min(tamanho, 100))

    @property
    def deslocamento(self) -> int:
        return (self.pagina - 1) * self.tamanho


PaginacaoDep = Annotated[Paginacao, Depends(Paginacao)]
```

`Depends(Paginacao)` funciona porque a classe é chamável: o FastAPI lê a
assinatura do `__init__` do mesmo jeito que leria a de uma função. O ganho é
que a dependência passa a ter métodos — e o `.deslocamento` some da rota e
do serviço.

## A recompensa: substituir em teste

```python title="tests/conftest.py" numbered
from app.main import app
from app.dependencies import get_session


def session_de_teste():
    with SessionTeste() as s:
        yield s


app.dependency_overrides[get_session] = session_de_teste
```

`dependency_overrides` é um dicionário: a chave é a função original, o valor
é a substituta. Todo `Depends(get_session)` da aplicação passa a receber a
de teste — sem variável de ambiente, sem `monkeypatch`, sem tocar no código
de produção.

:::key
Essa é a razão prática de usar injeção de dependência em vez de importar a
sessão direto no módulo. Um `from app.database import SessionLocal` dentro
do serviço funciona igual em produção e torna o teste um exercício de
remendo. A dependência declarada é um ponto de troca que já existe.
:::

:::trivia
Em Java e C#, injeção de dependência costuma exigir um contêiner — um objeto
que registra tipos e implementações, configurado à parte. O FastAPI dispensa
isso porque o Python tem introspecção em execução: ele consegue ler a
assinatura da sua função e descobrir o que ela quer. A mesma característica
que dificulta a conferência de tipos antes de rodar é a que torna esse
mecanismo possível.
:::

:::summary
- Decorador é uma função que recebe uma função e devolve outra.
- `Depends(f)` chama `f` antes da rota e entrega o resultado.
- Dependência com `yield` abre antes e fecha depois da resposta.
- Dependências se encadeiam, e o resultado é cacheado por requisição — é o
  que faz a sessão ser a mesma em todas as camadas.
- Dependência que só verifica entra em `dependencies=[...]`.
- `dependency_overrides` troca qualquer dependência em teste, sem remendo.
:::

:::exercise level=1
Escreva uma dependência `Paginacao` como classe e use-a na rota de listagem.

:::answer
```python
class Paginacao:
    def __init__(
        self,
        pagina: Annotated[int, Query(ge=1)] = 1,
        tamanho: Annotated[int, Query(ge=1, le=100)] = 20,
    ):
        self.pagina = pagina
        self.tamanho = tamanho

    @property
    def deslocamento(self) -> int:
        return (self.pagina - 1) * self.tamanho


@router.get("", response_model=Pagina[ProdutoLer])
def listar(servico: ServicoDep, pag: PaginacaoDep):
    return servico.listar(pag)
```
:::

:::exercise level=2
Escreva uma dependência que exija o cabeçalho `X-Api-Key` e aplique-a a um
router inteiro de administração.

:::answer
```python
from fastapi import Header


def exigir_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    esperada = get_config().api_key
    if not esperada or x_api_key != esperada:
        raise HTTPException(401, "chave inválida")


admin = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(exigir_api_key)],
)
```
O `not esperada` na condição é deliberado: se a chave não estiver
configurada, tudo é recusado. O contrário — liberar quando não há chave — é
como uma API de administração acaba pública num ambiente novo.

Repare também que essa comparação com `!=` é vulnerável a ataque de tempo. A
forma correta é `secrets.compare_digest`, e o capítulo @cap:jwt volta a isso.
:::

:::exercise level=3
Um colega propõe criar a sessão no topo do módulo de serviço —
`session = SessionLocal()` — argumentando que "é mais simples e evita passar
sessão para todo lado". Descreva o que acontece em produção.

:::answer
Uma sessão criada na importação do módulo existe **uma vez por processo** e
é compartilhada por todas as requisições que aquele processo atender.

A primeira consequência é a transação. A sessão mantém uma transação aberta;
se a requisição A levantar exceção e ninguém desfizer, a sessão fica em
estado de erro e **toda** requisição seguinte falha, com uma mensagem que não
tem relação nenhuma com o que elas pediram. A aplicação passa a precisar de
reinício para voltar a funcionar.

A segunda é o cache de identidade do capítulo @cap:sqlalchemy. O produto
carregado pela requisição A continua na sessão quando a requisição B chega.
B recebe o objeto de A, possivelmente com alterações não confirmadas — dado
de um usuário aparecendo na resposta de outro, que é a categoria de defeito
mais grave que uma API pode ter.

A terceira é a concorrência. A sessão não é segura para uso simultâneo por
várias threads, e o servidor usa threads para rodar rotas síncronas. Duas
requisições ao mesmo tempo produzem erros intermitentes que não se
reproduzem em desenvolvimento, porque em desenvolvimento há um usuário só.

E a quarta é que nada disso aparece nos testes. Cada teste roda sozinho, com
a sessão limpa, e passa. O defeito exige concorrência e sobreposição — ou
seja, exige produção.

A alternativa que o colega quer — não passar sessão para todo lado — existe
e é exatamente a dependência: a sessão é passada uma vez, pelo framework, no
lugar onde o grafo é montado.
:::
