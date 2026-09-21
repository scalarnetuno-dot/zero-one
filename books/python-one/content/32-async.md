---
title: "Assíncrono"
number: 32
slug: async
part: p6
kicker: "Concorrência não é velocidade. É deixar de ficar parado esperando."
goal: >-
  Entender o laço de eventos, escrever rotas `async` sem travá-lo, decidir
  entre rota síncrona e assíncrona, e saber o que muda no acesso ao banco.
---

Uma requisição que consulta o banco passa a maior parte do tempo **sem fazer
nada**: ela mandou a pergunta e espera a resposta viajar de volta. Se o
processo fica parado junto, ele desperdiça o recurso mais caro que tem.

`async` é a forma de o Python dizer "enquanto eu espero, atenda outro".

## O laço de eventos

```python title="laco.py" numbered
import asyncio


async def cozinhar(prato: str, minutos: int) -> str:
    print(f"começando {prato}")
    await asyncio.sleep(minutos)
    print(f"{prato} pronto")
    return prato


async def main() -> None:
    await asyncio.gather(
        cozinhar("arroz", 2),
        cozinhar("feijão", 3),
        cozinhar("salada", 1),
    )


asyncio.run(main())
```

```text
começando arroz
começando feijão
começando salada
salada pronto
arroz pronto
feijão pronto
```

Seis segundos de trabalho terminaram em três. Não houve paralelismo: há um
processo, uma thread, um único fluxo de execução. O que houve foi **cessão
de vez** — cada `await` devolveu o controle ao laço de eventos, que foi
tocar outra coisa enquanto aquela esperava.

:::term Corrotina
A função declarada com `async def`. Chamá-la **não executa nada**: devolve
um objeto que precisa ser aguardado com `await` ou entregue ao laço. Esse é
o engano número um de quem começa — a função "não roda" e não há erro.
:::

:::term Laço de eventos
O agendador que roda as corrotinas. Ele tem uma thread só e executa uma
corrota por vez, trocando sempre que uma delas cede a vez num `await`.
:::

:::key
Concorrência é fazer progresso em várias coisas alternadamente.
Paralelismo é executar várias ao mesmo tempo, em processadores diferentes.
`asyncio` dá concorrência, não paralelismo — e é exatamente o que uma API
precisa, porque ela espera muito mais do que calcula.
:::

## O pecado capital: travar o laço

```python title="o_erro.py" numbered
@app.get("/relatorio")
async def relatorio():
    time.sleep(5)          # NÃO
    return {"ok": True}
```

Esse `time.sleep` não cede a vez. Durante cinco segundos, o laço inteiro
fica parado — **todas** as requisições de todos os usuários esperam, mesmo
as que não têm nada a ver com o relatório. Uma rota lenta derrubou a
aplicação inteira.

| Trava o laço | Cede a vez |
|---|---|
| `time.sleep(5)` | `await asyncio.sleep(5)` |
| `requests.get(...)` | `await client.get(...)` (httpx) |
| `session.execute(...)` síncrono | `await session.execute(...)` |
| laço de cálculo pesado | `await run_in_threadpool(...)` |

Tabela: A regra: dentro de `async def`, toda operação que espera precisa ser
aguardada com `await`.

:::warning
Chamar uma biblioteca síncrona dentro de uma rota `async` é o defeito mais
comum e mais perigoso desse modelo. Ele não gera erro, não aparece em
teste com um usuário, e se manifesta em produção como uma lentidão geral que
não corresponde a nenhuma rota específica.
:::

## O que o FastAPI faz com `def` e com `async def`

Esta é a parte que mais confunde, e ela é simples:

```python
@app.get("/a")
def rota_sincrona():        # roda numa thread separada
    ...


@app.get("/b")
async def rota_assincrona():  # roda no laço de eventos
    ...
```

Uma rota declarada com `def` comum **não** roda no laço: o FastAPI a envia
para um pool de threads. Ela pode chamar biblioteca síncrona à vontade sem
travar ninguém — o preço é o custo de uma thread por requisição, e um limite
de quantas cabem.

Uma rota `async def` roda no laço e não pode bloquear.

:::key
Esta é a decisão prática, e ela é mais importante que a teoria:

**Se a sua pilha é síncrona — SQLAlchemy comum, `requests`, qualquer
biblioteca sem `await` —, escreva rotas com `def`.** O FastAPI cuida do
resto, e o desempenho é bom.

**Escreva `async def` quando a pilha inteira for assíncrona.** Misturar é
pior que qualquer um dos dois puros.
:::

O livro inteiro até aqui usou `def`, de propósito, e isso não foi uma
simplificação didática: é a escolha correta para a pilha que o projeto usa.

## Chamar outro serviço

```python title="httpx_cliente.py" numbered
import httpx


async def cotacao_do_dia() -> Decimal:
    async with httpx.AsyncClient(timeout=5.0) as client:
        r = await client.get("https://api.exemplo/cotacao")
        r.raise_for_status()
        return Decimal(str(r.json()["valor"]))
```

:::pitfall
Criar um `AsyncClient` por chamada joga fora o pool de conexões e força um
aperto de mão TLS novo a cada requisição. Em chamada frequente, crie o
cliente uma vez no ciclo de vida da aplicação e reaproveite — o capítulo
@cap:projeto-final mostra onde. E **sempre** ponha `timeout`: sem ele, a
biblioteca espera para sempre, e uma dependência lenta vira uma fila que não
esvazia.
:::

Quando há várias chamadas independentes, aí o ganho é grande:

```python title="paralelo.py" numbered
async def painel(client: httpx.AsyncClient) -> dict:
    cotacao, clima, feriados = await asyncio.gather(
        client.get("https://api.exemplo/cotacao"),
        client.get("https://api.exemplo/clima"),
        client.get("https://api.exemplo/feriados"),
    )
    return {
        "cotacao": cotacao.json(),
        "clima": clima.json(),
        "feriados": feriados.json(),
    }
```

Três chamadas de 200 ms em sequência custam 600 ms; juntas, custam 200 ms.
Esse é o caso em que `async` paga sozinho o custo de existir.

## Banco de dados assíncrono

```python title="async_db.py" numbered
from sqlalchemy.ext.asyncio import (
    AsyncSession, async_sessionmaker, create_async_engine,
)

engine = create_async_engine(
    "postgresql+asyncpg://user:senha@localhost/catalogo"
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
```

```python title="repo_async.py" numbered
async def buscar(self, produto_id: int) -> Produto | None:
    return await self.session.get(Produto, produto_id)


async def listar(self, limite: int) -> list[Produto]:
    stmt = select(Produto).limit(limite)
    resultado = await self.session.scalars(stmt)
    return list(resultado)
```

A mudança é mecânica — `await` em toda operação de banco, driver `asyncpg`
no lugar do `psycopg` — e ela **contamina toda a pilha**: o repositório vira
`async`, o serviço vira `async`, a rota vira `async`.

:::warning
Num modelo assíncrono, acesso preguiçoso a relacionamento não funciona.
`produto.produtor` precisaria fazer uma consulta, e consulta exige `await`,
e `await` não cabe num acesso a atributo — o SQLAlchemy levanta
`MissingGreenlet`. O carregamento preparado do capítulo
@cap:relacionamentos deixa de ser boa prática e passa a ser obrigatório.
:::

## Quando vale a troca

| Situação | Vale? |
|---|---|
| CRUD que fala só com o próprio banco | não — `def` é mais simples |
| muitas chamadas a serviços externos | sim |
| milhares de conexões simultâneas | sim |
| WebSocket, eventos, streaming | sim |
| relatório pesado de CPU | não — nem `async` nem thread: processo |

Tabela: A última linha merece nota: cálculo pesado não se resolve com
concorrência. Ele precisa sair do processo — fila de tarefas, processo
separado — porque o laço de eventos e o GIL não o deixam dividir
processador.

:::trivia
O GIL — *global interpreter lock* — é a trava que impede duas threads
Python de executarem bytecode ao mesmo tempo no mesmo processo. Ele existe
desde sempre e é a razão de `threading` não acelerar cálculo. O Python 3.13
começou a oferecer uma construção experimental sem GIL, e a transição deve
levar anos. Para código que espera — rede, disco, banco —, o GIL nunca foi
o gargalo: a thread o libera enquanto espera.
:::

:::summary
- `async` dá concorrência, não paralelismo: um processo, uma thread, cessão
  de vez.
- Chamar `async def` sem `await` não executa nada e não dá erro.
- Operação bloqueante dentro do laço trava a aplicação inteira.
- Rota com `def` vai para um pool de threads; rota `async def` roda no laço.
- Pilha síncrona pede `def`; só vale `async` se tudo for assíncrono.
- `asyncio.gather` paga sozinho quando há chamadas externas independentes.
- No modo assíncrono, carregamento preparado deixa de ser opcional.
:::

:::checkpoint
Você explica o laço de eventos sem metáfora, sabe o que trava e o que cede
a vez, e consegue defender por que o projeto deste livro usa `def`.
:::

:::exercise level=1
Escreva uma rota assíncrona que consulte duas APIs externas em paralelo e
devolva os dois resultados.

:::answer
```python
@app.get("/painel")
async def painel():
    async with httpx.AsyncClient(timeout=5.0) as client:
        a, b = await asyncio.gather(
            client.get("https://api.exemplo/cotacao"),
            client.get("https://api.exemplo/clima"),
        )
    return {"cotacao": a.json(), "clima": b.json()}
```
:::

:::exercise level=2
A rota abaixo é `async` e faz uma leitura de arquivo grande. Explique o
problema e dê duas soluções.

```python
@app.get("/exportar")
async def exportar():
    with open("catalogo.csv") as f:
        return {"linhas": len(f.readlines())}
```

:::answer
`open` e `readlines` são operações de disco bloqueantes: elas não cedem a
vez. Durante a leitura, o laço inteiro fica parado.

A primeira solução é a mais simples e quase sempre a melhor: trocar `async
def` por `def`. O FastAPI passa a rodar a rota numa thread, e o bloqueio
deixa de afetar os outros.

A segunda mantém o `async` e empurra o trabalho para uma thread
explicitamente:

```python
from starlette.concurrency import run_in_threadpool


@app.get("/exportar")
async def exportar():
    def ler():
        with open("catalogo.csv") as f:
            return len(f.readlines())

    return {"linhas": await run_in_threadpool(ler)}
```

Há um terceiro problema que nenhuma das duas resolve: `readlines()` carrega
o arquivo inteiro na memória. Para um arquivo grande, a resposta correta é
percorrer linha a linha e contar, ou devolver um `StreamingResponse`.
:::

:::exercise level=3
Seu time quer migrar a API inteira de síncrona para assíncrona, alegando
desempenho. A API só conversa com o próprio PostgreSQL. Avalie.

:::answer
O ganho esperado provavelmente não existe, e o custo é alto.

**Sobre o ganho.** Numa API que só fala com o próprio banco, o limite quase
nunca é o número de threads do servidor: é o **pool de conexões do banco**.
Se o PostgreSQL aceita cem conexões, cem consultas simultâneas é o teto,
síncrono ou assíncrono. O `async` permite ter dez mil requisições
aguardando em vez de dez mil threads — o que é uma economia de memória real,
e não uma economia de tempo de resposta.

**Sobre o custo.** A conversão contamina toda a pilha: driver, engine,
sessão, repositório, serviço, rota, testes e fixtures. O carregamento
preguiçoso para de funcionar, e todo relacionamento precisa de
`selectinload` — o que, aliás, é um bem em si, mas é trabalho. E qualquer
biblioteca síncrona que sobrar no caminho passa a ser um travamento
silencioso, que só aparece sob carga.

**O que eu pediria antes de decidir:** o número. Qual é hoje o tempo de
resposta, em qual percentil, sob qual carga, e onde está o tempo — no banco,
na rede ou na CPU? "Desempenho" sem medição costuma significar uma consulta
sem índice ou um N+1 do capítulo @cap:relacionamentos, e os dois se
resolvem em uma tarde, sem migrar nada.

**Quando eu concordaria:** se a API passasse a chamar serviços externos em
várias rotas, se precisasse de WebSocket, ou se o número de conexões
simultâneas ociosas — não de consultas — fosse o gargalo medido. Aí o
`async` resolve algo que nenhuma otimização de consulta resolve.
:::
