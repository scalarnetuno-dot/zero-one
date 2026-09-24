---
title: "Paginação"
number: 28
slug: paginacao
part: p5
kicker: "Toda listagem sem limite é uma promessa que o servidor não consegue cumprir para sempre."
goal: >-
  Paginar com `limit`/`offset`, devolver metadados úteis, garantir ordenação
  estável e saber quando trocar por paginação por cursor.
---

A rota de listagem do capítulo @cap:o-crud-completo já tem um teto. Este
capítulo transforma esse teto numa funcionalidade: o cliente escolhe a
página, sabe quantas existem e consegue percorrer o catálogo inteiro sem
nunca pedir tudo.

## O envelope

```python title="app/schemas/pagina.py" numbered
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    itens: list[T]
    total: int
    pagina: int
    tamanho: int

    @property
    def paginas(self) -> int:
        if self.tamanho == 0:
            return 0
        return -(-self.total // self.tamanho)
```

`Pagina[ProdutoLer]` é um esquema genérico: o mesmo envelope serve para
qualquer recurso, e a documentação mostra o tipo certo dentro de `itens`.

O `-(-a // b)` é a divisão com arredondamento para cima escrita sem
importar nada: nega, divide para baixo, nega de volta. Sete itens em páginas
de três dão três páginas, não duas.

:::http title="A listagem com envelope"
GET /produtos?pagina=2&tamanho=3
---
200 OK

{
  "itens": [
    {"id": 4, "nome": "Cenoura", "preco": "5.25"},
    {"id": 5, "nome": "Couve", "preco": "3.10"},
    {"id": 6, "nome": "Escarola", "preco": "4.00"}
  ],
  "total": 47,
  "pagina": 2,
  "tamanho": 3
}
:::

:::key
Devolver uma lista pura é mais simples e tira do cliente a informação de que
ele precisa: se há mais, quantas páginas existem, quantos itens ao todo. O
envelope é um campo a mais para quem escreve e três decisões a menos para
quem consome.
:::

## Os parâmetros

```python title="app/routers/produtos.py" numbered
from typing import Annotated

from fastapi import Query


@router.get("", response_model=Pagina[ProdutoLer])
def listar(
    servico: ServicoDep,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return servico.listar(pagina=pagina, tamanho=tamanho)
```

`Query(ge=1, le=100)` faz três coisas de uma vez: valida, documenta e impede
o pedido abusivo. `?tamanho=999999` recebe `422` antes de a função rodar —
e não uma tentativa de carregar a tabela inteira.

:::pitfall
Confiar no cliente para o tamanho da página é uma negação de serviço
autoinfligida. Não é preciso má intenção: basta um laço mal escrito no
cliente, ou um teste de carga. O teto é do servidor, sempre, e vale também
para o parâmetro interno do serviço — o `min(limite, 100)` continua lá,
porque o serviço também é chamado por scripts.
:::

## O serviço e o repositório

```python title="app/services/produto.py" numbered
def listar(self, pagina: int = 1, tamanho: int = 20) -> Pagina:
    tamanho = max(1, min(tamanho, 100))
    pagina = max(1, pagina)

    itens = self.repo.listar(
        limite=tamanho, deslocamento=(pagina - 1) * tamanho
    )
    total = self.repo.contar()

    return Pagina(
        itens=itens, total=total, pagina=pagina, tamanho=tamanho
    )
```

```python title="app/repositories/produto.py" numbered
def listar(self, limite: int, deslocamento: int) -> list[Produto]:
    stmt = (
        select(Produto)
        .order_by(Produto.nome, Produto.id)
        .limit(limite)
        .offset(deslocamento)
    )
    return list(self.session.scalars(stmt))


def contar(self) -> int:
    return self.session.scalar(
        select(func.count()).select_from(Produto)
    ) or 0
```

## A ordenação precisa ser total

Repare no `order_by(Produto.nome, Produto.id)`, com dois campos.

Se dois produtos tiverem o mesmo nome, a ordem entre eles não é definida —
e o banco pode devolvê-los em ordens diferentes em consultas diferentes. O
resultado é um produto que aparece na página 1 e de novo na página 2,
enquanto outro nunca aparece.

:::warning
Toda paginação exige ordenação **total**: um critério, ou uma combinação de
critérios, que nunca empata. Acrescentar a chave primária como último
critério de desempate resolve o caso geral e custa nada. Sem isso, a
paginação parece funcionar e perde registros de forma intermitente — o tipo
de defeito que ninguém consegue reproduzir.
:::

## O custo do `OFFSET`

```sql
SELECT * FROM produto ORDER BY nome LIMIT 20 OFFSET 100000;
```

O banco não pula as cem mil linhas: ele as **lê, ordena e descarta**, para
então devolver as vinte seguintes. A página 1 é instantânea; a página 5.000
é um problema.

:::diagram type="flowchart" caption="O banco descarta tudo que vem antes do OFFSET — e cobra por isso."
nodes:
  - { id: q, type: io,      text: "LIMIT 20 OFFSET 100000" }
  - { id: l, type: process, text: "lê e ordena 100.020 linhas" }
  - { id: d, type: process, text: "descarta as 100.000 primeiras" }
  - { id: r, type: io,      text: "devolve 20" }
edges:
  - { from: q, to: l }
  - { from: l, to: d }
  - { from: d, to: r }
:::

E há um segundo problema, mais sutil: entre a página 1 e a página 2, alguém
pode ter inserido um produto. O deslocamento se desloca, e um item que
estava na posição 20 vai para a 21 — e aparece de novo.

## Paginação por cursor

A solução para os dois problemas é não contar posições, e sim dizer onde
parou:

```python title="cursor.py" numbered
def listar_apos(
    self, depois_de: int | None, limite: int
) -> list[Produto]:
    stmt = select(Produto).order_by(Produto.id).limit(limite)
    if depois_de is not None:
        stmt = stmt.where(Produto.id > depois_de)
    return list(self.session.scalars(stmt))
```

```text
GET /produtos?depois_de=140&tamanho=20
```

O banco usa o índice da chave primária para saltar direto ao ponto: o custo
da página 5.000 é igual ao da página 1. E a inserção de um produto no meio
não desloca nada, porque não há posição — há uma fronteira.

| Critério | `offset` | cursor |
|---|---|---|
| "ir para a página 37" | sim | não |
| custo em página alta | cresce | constante |
| item repetido ou perdido | acontece | não acontece |
| ordenação arbitrária | fácil | exige o campo no cursor |

Tabela: `offset` para interface com números de página e poucas páginas;
cursor para rolagem infinita, exportação e volume grande.

:::key
Comece com `offset`. Ele é simples, atende telas com paginador numerado e
funciona bem até dezenas de milhares de registros. Troque por cursor quando
medir lentidão nas páginas altas, ou quando a listagem for consumida por um
processo que percorre tudo — ali o `offset` é sempre a escolha errada.
:::

## `Link` e `X-Total-Count`

Há uma escola que prefere os metadados nos cabeçalhos, mantendo o corpo como
uma lista pura:

```text
HTTP/1.1 200 OK
X-Total-Count: 47
Link: </produtos?pagina=3>; rel="next",
      </produtos?pagina=1>; rel="prev"
```

É o estilo da API do GitHub. Funciona, é elegante e tem um custo prático:
cliente em navegador não enxerga cabeçalho personalizado sem configuração de
CORS (`expose_headers`), e muita biblioteca de cliente ignora cabeçalhos por
padrão. O envelope no corpo é mais chato e nunca some pelo caminho.

:::summary
- O teto do tamanho da página é do servidor, não do cliente.
- O envelope devolve `total`, `pagina` e `tamanho` — três decisões a menos
  para quem consome.
- Paginação exige ordenação total; desempate pela chave primária.
- `OFFSET` lê e descarta: o custo cresce com o número da página.
- Cursor tem custo constante e não repete nem perde itens; não permite
  pular para a página 37.
- Metadado no corpo sobrevive melhor que metadado em cabeçalho.
:::

:::exercise level=1
Acrescente à listagem os parâmetros `pagina` e `tamanho` com validação, e
devolva o envelope `Pagina[ProdutoLer]`.

:::answer
```python
@router.get("", response_model=Pagina[ProdutoLer])
def listar(
    servico: ServicoDep,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return servico.listar(pagina=pagina, tamanho=tamanho)
```
:::

:::exercise level=2
Acrescente ao envelope os campos `tem_proxima` e `tem_anterior`, calculados
no servidor.

:::answer
```python
class Pagina(BaseModel, Generic[T]):
    itens: list[T]
    total: int
    pagina: int
    tamanho: int

    @computed_field
    @property
    def tem_proxima(self) -> bool:
        return self.pagina * self.tamanho < self.total

    @computed_field
    @property
    def tem_anterior(self) -> bool:
        return self.pagina > 1
```
`@computed_field` faz a propriedade aparecer no JSON e na documentação — sem
ele, ela existe em Python e some na serialização. Calcular isso no servidor
evita que cada cliente reimplemente a mesma conta, e evita que um deles a
implemente errado.
:::

:::exercise level=2
Implemente o cursor da listagem: a rota recebe `depois_de` e `tamanho`, e a
resposta traz `proximo_cursor` — ou `null` quando acabou.

:::answer
```python
class PaginaCursor(BaseModel, Generic[T]):
    itens: list[T]
    proximo_cursor: int | None


def listar_apos(self, depois_de: int | None, tamanho: int):
    itens = self.repo.listar_apos(depois_de, tamanho + 1)
    tem_mais = len(itens) > tamanho
    itens = itens[:tamanho]
    return PaginaCursor(
        itens=itens,
        proximo_cursor=itens[-1].id if tem_mais else None,
    )
```
O truque é pedir **um item a mais** do que o cliente quer. Se ele vier,
existe próxima página; se não vier, acabou. É a forma de saber que há mais
sem executar um `COUNT` — e é por isso que a paginação por cursor dispensa o
total.
:::

:::exercise level=3
O `contar()` da listagem executa um `COUNT(*)` a cada requisição. Numa
tabela de oito milhões de linhas com filtros, ele passou a custar mais que a
consulta principal. Proponha três saídas e diga o que cada uma custa.

:::answer
**Primeira: não contar.** Devolver `tem_proxima` sem `total`, pedindo
`tamanho + 1` itens e verificando se veio o extra. Custa quase nada e a
interface perde o "página 3 de 412". É a escolha certa para rolagem infinita
e a errada para uma tela com paginador numerado.

**Segunda: contagem aproximada.** O PostgreSQL mantém uma estimativa em
`pg_class.reltuples`, atualizada pelo `ANALYZE`. Ela é instantânea e pode
errar por milhares em tabela com muita escrita. Serve para "cerca de 8
milhões de produtos"; não serve para paginador, porque a última página pode
não existir.

**Terceira: contagem em cache.** Guardar o total por combinação de filtros,
com validade curta. Custa a complexidade de invalidar — e invalidação de
cache por filtro arbitrário é um problema difícil, que costuma ser resolvido
por tempo em vez de por evento.

A resposta que eu daria depende de quem consome. Se for tela com paginador,
a segunda, deixando explícito na documentação que `total` é aproximado. Se
for API consumida por programa, a primeira: quem percorre tudo não precisa
do total, precisa do cursor do capítulo — e nesse caminho o `COUNT` some
junto com o `OFFSET`.
:::
