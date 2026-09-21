---
title: "Filtros e buscas"
number: 28
slug: filtros-e-buscas
part: p5
kicker: "Toda busca começa com uma comparação injusta: o usuário digita sem acento e o banco guarda com."
goal: >-
  Montar consultas com filtros opcionais sem escadas de `if`, ordenar por
  campo escolhido pelo cliente com segurança, e escolher entre `LIKE`, busca
  sem acento e busca textual de verdade.
---

A listagem do capítulo @cap:paginacao devolve tudo, em ordem de nome. A
primeira pergunta que qualquer pessoa faz depois disso é: *e se eu quiser só
as verduras abaixo de dez reais?*

## O objeto de filtro

A tentação é acrescentar um parâmetro por vez na assinatura da rota. Com
seis filtros, a assinatura tem oito parâmetros e o serviço tem seis `if`.

```python title="app/schemas/filtro.py" numbered
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import Query
from pydantic import BaseModel, Field


class ProdutoFiltro(BaseModel):
    q: str | None = None
    categoria: Categoria | None = None
    preco_min: Annotated[Decimal | None, Field(ge=0)] = None
    preco_max: Annotated[Decimal | None, Field(ge=0)] = None
    apenas_disponiveis: bool = False
    ordenar_por: Literal["nome", "preco", "criado_em"] = "nome"
    ordem: Literal["asc", "desc"] = "asc"
```

```python title="app/routers/produtos.py" numbered
@router.get("", response_model=Pagina[ProdutoLer])
def listar(
    servico: ServicoDep,
    filtro: Annotated[ProdutoFiltro, Query()],
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return servico.listar(filtro, pagina, tamanho)
```

`Annotated[ProdutoFiltro, Query()]` faz o FastAPI espalhar os campos do
modelo pelos parâmetros de query. A rota volta a ter quatro parâmetros
mesmo que o filtro cresça para vinte campos — e cada campo novo entra na
documentação sozinho.

```text
GET /produtos?q=tomate&categoria=legume&preco_max=10&ordem=desc
```

:::key
O `Literal` em `ordenar_por` não é estilo: é segurança. Ele fecha a lista de
campos ordenáveis, e é o que impede o cliente de pedir ordenação por uma
coluna que não deveria ser exposta — ou de injetar texto arbitrário num
`ORDER BY` montado por concatenação.
:::

## Montando a consulta em partes

```python title="app/repositories/produto.py" numbered
def listar(
    self, filtro: ProdutoFiltro, limite: int, deslocamento: int
) -> list[Produto]:
    stmt = select(Produto)
    stmt = self._aplicar_filtros(stmt, filtro)
    stmt = self._aplicar_ordem(stmt, filtro)
    return list(
        self.session.scalars(
            stmt.limit(limite).offset(deslocamento)
        )
    )


def contar(self, filtro: ProdutoFiltro) -> int:
    stmt = select(func.count()).select_from(Produto)
    stmt = self._aplicar_filtros(stmt, filtro)
    return self.session.scalar(stmt) or 0


def _aplicar_filtros(self, stmt, filtro: ProdutoFiltro):
    if filtro.q:
        stmt = stmt.where(Produto.nome.ilike(f"%{filtro.q}%"))
    if filtro.categoria is not None:
        stmt = stmt.where(Produto.categoria == filtro.categoria)
    if filtro.preco_min is not None:
        stmt = stmt.where(Produto.preco >= filtro.preco_min)
    if filtro.preco_max is not None:
        stmt = stmt.where(Produto.preco <= filtro.preco_max)
    if filtro.apenas_disponiveis:
        stmt = stmt.where(Produto.estoque > 0)
    return stmt
```

Cada `.where()` devolve uma consulta **nova**, com a condição acrescentada.
As condições se somam com `AND`, e um filtro não informado simplesmente não
acrescenta nada.

Reparar que `_aplicar_filtros` é usado pela listagem **e** pela contagem é o
ponto do desenho: sem essa função compartilhada, o `total` do envelope
contaria a tabela inteira enquanto os itens vêm filtrados — um defeito que
aparece em produção com frequência desconfortável.

:::pitfall
`preco_min` e `preco_max` precisam do `is not None`, não de `if
filtro.preco_min:`. Um preço mínimo de zero é falso em Python, e o filtro
seria silenciosamente ignorado — a mesma armadilha do capítulo
@cap:operadores, agora numa consulta.
:::

## A ordenação

```python title="ordem.py" numbered
_CAMPOS = {
    "nome": Produto.nome,
    "preco": Produto.preco,
    "criado_em": Produto.criado_em,
}


def _aplicar_ordem(self, stmt, filtro: ProdutoFiltro):
    coluna = _CAMPOS[filtro.ordenar_por]
    if filtro.ordem == "desc":
        coluna = coluna.desc()
    return stmt.order_by(coluna, Produto.id)
```

O dicionário é uma **lista de permissão**: só existe ordenação pelos três
campos mapeados. O `Literal` do esquema já garantia isso, e a duplicação é
deliberada — o repositório também é chamado por código que não passa pelo
esquema.

E o `Produto.id` no fim é o desempate obrigatório do capítulo
@cap:paginacao.

## `LIKE`, `ILIKE` e o problema do acento

```python
Produto.nome.ilike(f"%{filtro.q}%")
```

`ILIKE` é a versão do PostgreSQL que ignora maiúsculas. Ela resolve
`"TOMATE"` e não resolve o problema real do português:

```text
digitado: "acafrao"
guardado: "Açafrão"
resultado: nada
```

O conserto no banco é a extensão `unaccent`:

```sql
CREATE EXTENSION IF NOT EXISTS unaccent;

SELECT * FROM produto
WHERE unaccent(nome) ILIKE unaccent('%acafrao%');
```

```python title="sem_acento.py" numbered
from sqlalchemy import func

termo = f"%{filtro.q}%"
stmt = stmt.where(
    func.unaccent(Produto.nome).ilike(func.unaccent(termo))
)
```

:::warning
`ILIKE '%termo%'` com `%` no **começo** não usa índice comum: o banco varre a
tabela. Até algumas dezenas de milhares de linhas, ninguém percebe. Depois
disso, é preciso um índice trigrama (`pg_trgm`) ou a busca textual da seção
seguinte. Envolver a coluna em `unaccent(...)` também anula o índice — a
menos que exista um índice sobre a própria expressão.
:::

```sql
ALTER TABLE produto ADD COLUMN nome_busca TEXT NOT NULL DEFAULT '';
CREATE INDEX idx_produto_nome_busca_trgm
    ON produto USING gin (nome_busca gin_trgm_ops);
```

Preencha `nome_busca` normalizado ao criar ou alterar o produto, por exemplo
com `unicodedata` no serviço. A coluna materializada evita depender de uma
função `unaccent` imutável dentro do índice e deixa explícita a política de
normalização.

## Quando o `LIKE` não basta

:::diagram type="blocks" caption="Três estratégias de busca por texto, em ordem de custo e de capacidade."
rows:
  - [{ text: "ILIKE '%x%'", note: "simples · sem índice · pequeno volume" }]
  - [{ text: "pg_trgm + unaccent", note: "tolera erro de digitação · indexável" }]
  - [{ text: "tsvector (full-text)", note: "radical, relevância, vários campos" }]
  - [{ text: "motor externo", note: "OpenSearch · sincronização e operação" }]
:::

A busca textual do PostgreSQL entende que "tomates" e "tomate" são a mesma
palavra, ordena por relevância e pesquisa em vários campos de uma vez:

```sql
ALTER TABLE produto ADD COLUMN busca tsvector
  GENERATED ALWAYS AS (
    to_tsvector('portuguese',
      unaccent(nome) || ' ' || unaccent(coalesce(descricao,'')))
  ) STORED;

CREATE INDEX idx_produto_busca ON produto USING gin (busca);
```

```python
stmt = stmt.where(
    Produto.busca.op("@@")(
        func.plainto_tsquery("portuguese", filtro.q)
    )
)
```

:::key
A ordem de escolha é sempre a mesma: comece no `ILIKE`, vá para trigrama
quando ficar lento, vá para `tsvector` quando o usuário reclamar de
resultado ruim, e vá para um motor externo quando o produto **for** a busca.
Cada degrau custa operação, e pular degraus é a forma mais comum de
acrescentar um servidor que ninguém sabe manter.
:::

:::story A busca que não achava o açafrão
— O produto está cadastrado — disse Dona Neuza. — Eu cadastrei ontem.

Rafa digitou "acafrao" na busca. Nada.

Digitou "Açafrão", com cedilha e til. Apareceu.

— A senhora digita com acento?

— Eu digito. — Dona Neuza apontou para a sala ao lado. — Eles não digitam.

Rafa foi ver. Dos onze computadores do armazém, quatro tinham teclado sem
cedilha, comprados numa licitação de 2021. As pessoas tinham aprendido a
cadastrar sem acento — e a buscar sem acento, o que funcionava, porque o que
elas mesmas tinham cadastrado também estava sem.

— Então tem duas bases aí dentro — disse Rafa. — A com acento e a sem.

— Tem quatro anos de duas bases — disse Dona Neuza.
:::

:::pitfall
Normalizar a busca sem normalizar o que já está gravado resolve metade do
problema. Se `"Açafrão"` e `"Acafrao"` convivem na tabela, a busca sem
acento acha os dois e a listagem mostra duas linhas que são o mesmo produto.
A correção completa envolve uma migração de dados — e é o tipo de dívida que
começa no dia em que a normalização do capítulo @cap:validacao foi adiada.
:::

:::summary
- Um objeto de filtro tipado mantém a rota curta e a documentação completa.
- Filtro opcional compara com `is not None`, nunca por veracidade.
- A mesma função de filtros serve a listagem e à contagem.
- Ordenação por campo do cliente exige lista de permissão, nunca
  concatenação.
- `ILIKE '%x%'` não usa índice; `unaccent` anula índice sem índice de
  expressão.
- Suba os degraus de busca por necessidade medida, não por antecipação.
:::

:::checkpoint
Você monta consultas dinâmicas sem escada de `if`, ordena com segurança, e
sabe qual estratégia de busca por texto o seu volume justifica.
:::

:::exercise level=1
Acrescente ao filtro um campo `produtor_id` opcional e aplique-o na consulta.

:::answer
```python
class ProdutoFiltro(BaseModel):
    produtor_id: int | None = None


# em _aplicar_filtros
if filtro.produtor_id is not None:
    stmt = stmt.where(Produto.produtor_id == filtro.produtor_id)
```
:::

:::exercise level=2
Faça a busca `q` procurar no nome **e** na descrição, com `OR`.

:::answer
```python
from sqlalchemy import or_

if filtro.q:
    termo = f"%{filtro.q}%"
    stmt = stmt.where(
        or_(
            Produto.nome.ilike(termo),
            Produto.descricao.ilike(termo),
        )
    )
```
`or_` é necessário porque vírgulas dentro de `where` significam `AND`.
Esquecer disso produz uma busca que exige o termo nos dois campos — e devolve
quase nada, sem erro nenhum.
:::

:::exercise level=3
O cliente pediu um filtro `tags` que aceite várias tags e devolva produtos
que tenham **todas** elas. As tags estão numa tabela de relacionamento.
Descreva a consulta e o problema de desempenho que ela traz.

:::answer
A forma direta é agrupar e contar:

```python
stmt = (
    select(Produto)
    .join(Produto.tags)
    .where(Tag.nome.in_(filtro.tags))
    .group_by(Produto.id)
    .having(func.count(Tag.id) == len(filtro.tags))
)
```

O `JOIN` traz uma linha por par produto-tag; o `GROUP BY` volta a uma linha
por produto; e o `HAVING` exige que o número de tags casadas seja igual ao
número pedido. É a tradução literal de "tem todas".

O problema de desempenho tem duas partes. A primeira é o `GROUP BY` sobre o
resultado do `JOIN`: ele não pode ser resolvido pelo índice, porque a
condição depende de uma agregação — o banco precisa materializar os pares
antes de decidir. Com muitas tags populares, esse conjunto intermediário
fica grande.

A segunda é a interação com a paginação do capítulo @cap:paginacao: o
`COUNT` do envelope precisa repetir a mesma agregação, dobrando o custo. E
`LIMIT` sobre consulta agrupada não permite ao banco parar cedo — ele
precisa agrupar tudo para saber quem passou no `HAVING`.

As saídas usuais, em ordem de esforço: limitar o número de tags por
requisição (três ou quatro, validado no esquema); manter uma coluna
desnormalizada com as tags do produto, indexada como array ou `tsvector`; ou
levar a busca por facetas para um motor externo, que é o que ela é. Vale
também perguntar ao cliente se "todas" é mesmo o que ele quer — muitas vezes
"qualquer uma, ordenado por quantas casaram" é a funcionalidade desejada, e
ela é bem mais barata.
:::
