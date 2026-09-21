---
title: "SQLAlchemy"
number: 20
slug: sqlalchemy
part: p4
kicker: "O ORM não esconde o banco. Ele traduz — e quem não sabe a língua de origem não percebe quando a tradução ficou ruim."
goal: >-
  Mapear uma tabela para uma classe, abrir e fechar sessões corretamente,
  escrever consultas com `select()` e entender a diferença entre `flush` e
  `commit`.
---

Um ORM — *object-relational mapper* — faz duas coisas: transforma linhas em
objetos e objetos em comandos SQL. A promessa é escrever Python em vez de
SQL. O preço é que, quando algo fica lento, você precisa saber qual SQL foi
gerado.

Este livro usa o SQLAlchemy 2.0, cuja sintaxe difere bastante da versão 1.x
que ainda domina os tutoriais antigos. Se você encontrar `session.query(...)`
na internet, é código da era anterior: funciona, mas está sendo aposentado.

## Instalar e conectar

```text
$ pip install sqlalchemy "psycopg[binary]"
```

SQLAlchemy não instala o driver do PostgreSQL por conta própria. O primeiro
pacote traduz o código Python para SQL; o segundo abre a conexão com o
PostgreSQL.

```python title="app/database.py" numbered
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_config

config = get_config()

engine = create_engine(
    config.database_url,
    echo=config.app_ambiente == "dev",
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
```

Três argumentos merecem explicação.

`echo=True` imprime no terminal **todo** SQL gerado. Ligue em
desenvolvimento e desligue em produção — é a ferramenta que transforma o ORM
de caixa-preta em caixa de vidro.

`pool_pre_ping=True` testa a conexão antes de entregá-la. Sem isso, uma
conexão que o banco derrubou por inatividade volta do pool morta e produz um
erro aleatório na primeira requisição depois de um período parado.

`expire_on_commit=False` faz os objetos continuarem legíveis depois do
`commit`. Sem ele, ler `produto.nome` após confirmar a transação dispara uma
consulta nova — e, se a sessão já tiver fechado, levanta exceção. É a
primeira pedra do caminho de quem usa SQLAlchemy com FastAPI.

## A tabela vira classe

```python title="app/models/produto.py" numbered
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Produto(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120), index=True)
    preco: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    estoque: Mapped[int] = mapped_column(default=0)
    ativo: Mapped[bool] = mapped_column(default=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"Produto(id={self.id}, nome={self.nome!r})"
```

:::anatomy title="O que o SQLAlchemy lê nesta declaração"
lang: python
code: |
  class Produto(Base):
      __tablename__ = "produto"

      id: Mapped[int] = mapped_column(primary_key=True)
      nome: Mapped[str] = mapped_column(String(120))
      obs: Mapped[str | None]
notes:
  - { line: 1, text: "Herdar de `Base` registra a classe no catálogo de tabelas." }
  - { line: 2, text: "Sem `__tablename__`, não há tabela — é o único campo obrigatório." }
  - { line: 4, text: "`primary_key=True` implica identificador gerado pelo banco." }
  - { line: 5, text: "`String(120)` vira `VARCHAR(120)`; sem tamanho, vira `TEXT`." }
  - { line: 6, text: "`Mapped[str | None]` é o que decide `NULL`; sem o `None`, sai `NOT NULL`." }
:::

:::key
A nulidade da coluna vem da **anotação de tipo**, não de um argumento.
`Mapped[str]` gera `NOT NULL`; `Mapped[str | None]` gera coluna anulável.
É a mesma ideia do capítulo @cap:tipagem-e-dataclasses levada ao banco: a
anotação deixa de ser decoração e passa a ter consequência.
:::

Para criar as tabelas em desenvolvimento:

```python
Base.metadata.create_all(engine)
```

:::warning
`create_all` só cria o que não existe. Ele **não** altera tabela existente:
acrescentar uma coluna ao modelo e rodar de novo não faz nada, e o erro
aparece depois, como "coluna não existe". Ele serve para protótipo e para
teste. A ferramenta de verdade é o Alembic, do capítulo @cap:migrations.
:::

## A sessão

```python title="app/database.py" numbered
from collections.abc import Generator

from sqlalchemy.orm import Session


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
```

A sessão é três coisas ao mesmo tempo, e confundi-las é a origem de quase
todo problema com ORM:

- uma **conexão** emprestada do pool;
- uma **transação** aberta;
- um **cache de identidade** — o mesmo produto lido duas vezes na mesma
  sessão é o mesmo objeto Python.

:::key
A regra que vale para o livro inteiro: **uma sessão por requisição**. Ela
abre quando a requisição chega, fecha quando a resposta sai, e nunca é
compartilhada entre requisições. Sessão global é a receita para dado de um
usuário aparecer na resposta de outro.
:::

## Escrever

```python title="escrever.py" numbered
from decimal import Decimal

from app.database import SessionLocal
from app.models.produto import Produto

with SessionLocal() as session:
    produto = Produto(
        nome="Cenoura", preco=Decimal("5.25"), estoque=60
    )

    session.add(produto)
    session.commit()

    print(produto.id)
```

Repare no que acontece com `produto.id`: antes do `commit`, ele é `None`;
depois, tem o valor gerado pelo banco. O objeto Python foi atualizado a
partir da resposta do `INSERT`.

### `flush` e `commit`

```python
session.add(produto)
session.flush()    # manda o INSERT, ainda dentro da transação
session.commit()   # confirma tudo
```

`flush` envia os comandos ao banco sem confirmar. É o que se usa quando você
precisa do `id` gerado para inserir outra coisa que depende dele — tudo
dentro da mesma transação, e tudo desfeito junto se algo falhar.

`commit` encerra a transação. Depois dele não há volta.

:::pitfall
Chamar `commit` dentro de uma função de repositório é um erro de desenho que
custa caro. O repositório não sabe se a operação dele é a última da
transação — quem sabe é a camada de serviço, do capítulo @cap:service. Um
`commit` no meio quebra a atomicidade sem que ninguém perceba: a primeira
metade da operação fica gravada e a segunda falha.
:::

## Ler

```python title="ler.py" numbered
from sqlalchemy import select

with SessionLocal() as session:
    # um, pela chave primária
    produto = session.get(Produto, 1)

    # um, por outro critério
    stmt = select(Produto).where(Produto.nome == "Cenoura")
    produto = session.scalars(stmt).first()

    # vários
    stmt = (
        select(Produto)
        .where(Produto.estoque > 0)
        .order_by(Produto.nome)
        .limit(20)
    )
    produtos = session.scalars(stmt).all()
```

`select(Produto)` monta a consulta; `session.scalars(...)` a executa e
devolve objetos `Produto`. Sem o `scalars`, o retorno seriam tuplas de uma
posição — um detalhe que confunde bastante na primeira semana.

O encadeamento `.where().order_by().limit()` espelha o SQL do capítulo
@cap:banco-de-dados na mesma ordem, e é o mesmo objeto sendo refinado. Isso
permite montar a consulta em partes, que é exatamente o que o capítulo
@cap:filtros-e-buscas vai fazer.

| Escrita | Devolve |
|---|---|
| `.first()` | o primeiro ou `None` |
| `.all()` | lista, possivelmente vazia |
| `.one()` | exatamente um — erro se zero ou vários |
| `.one_or_none()` | um ou `None` — erro se vários |

Tabela: `one()` e `one_or_none()` transformam "eu esperava um só" numa
garantia executada, em vez de uma suposição.

## Alterar e apagar

```python title="alterar.py" numbered
with SessionLocal() as session:
    produto = session.get(Produto, 1)
    if produto is None:
        raise ValueError("não existe")

    produto.preco = Decimal("9.50")
    session.commit()
```

Não existe `session.update()`. Você altera o atributo do objeto, e a sessão
percebe. Isso se chama *dirty checking*: no `commit`, o SQLAlchemy compara o
estado atual com o estado carregado e gera o `UPDATE` apenas das colunas que
mudaram.

```python
session.delete(produto)
session.commit()
```

:::trivia
Esse rastreamento automático é a maior conveniência e a maior pegadinha do
ORM. Um objeto carregado e modificado por engano — numa função que só queria
ler — é gravado no `commit` seguinte, sem nenhuma chamada explícita. É o
famoso "quem alterou esse preço?" cuja resposta é: ninguém mandou gravar,
mas alguém atribuiu.
:::

## Ver o SQL gerado

```text
INFO sqlalchemy.engine.Engine SELECT produto.id, produto.nome,
produto.preco FROM produto WHERE produto.estoque > %(estoque_1)s
ORDER BY produto.nome LIMIT %(param_1)s
INFO sqlalchemy.engine.Engine [generated in 0.00018s]
{'estoque_1': 0, 'param_1': 20}
```

Repare nos `%(estoque_1)s`: o ORM usa parâmetros, e por isso não existe
injeção de SQL pelo caminho normal. Repare também que ele pediu só as três
colunas do modelo — não um `SELECT *`.

:::practice
Deixe `echo=True` ligado durante os próximos capítulos. Toda vez que uma
rota responder, olhe quantas consultas apareceram no terminal. Esse hábito é
o que faz você perceber o problema N+1 do capítulo @cap:relacionamentos no
dia em que ele nascer, e não seis meses depois.
:::

:::summary
- SQLAlchemy 2.0 usa `select()`; `session.query()` é da era anterior.
- `Mapped[str]` gera `NOT NULL`; `Mapped[str | None]` gera coluna anulável.
- `expire_on_commit=False` evita consulta extra ao ler depois do `commit`.
- Sessão é conexão, transação e cache de identidade — uma por requisição.
- `flush` manda sem confirmar; `commit` encerra e não tem volta.
- Alterar atributo já é a alteração: a sessão grava no `commit`.
- `echo=True` em desenvolvimento transforma o ORM em caixa de vidro.
:::

:::exercise level=1
Escreva o modelo `Produtor` com `id`, `nome`, `cidade`, `email` único e
`criado_em` com padrão do servidor.

:::answer
```python
class Produtor(Base):
    __tablename__ = "produtor"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    cidade: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```
:::

:::exercise level=2
Escreva a consulta que devolve os cinco produtos mais caros com estoque
disponível — a mesma do capítulo @cap:banco-de-dados, agora com `select()`.

:::answer
```python
stmt = (
    select(Produto)
    .where(Produto.estoque > 0, Produto.ativo.is_(True))
    .order_by(Produto.preco.desc())
    .limit(5)
)
produtos = session.scalars(stmt).all()
```
Duas condições separadas por vírgula dentro do `where` são combinadas com
`AND`. E `ativo.is_(True)` em vez de `ativo == True` porque o segundo dispara
aviso das ferramentas de estilo — em SQL, comparar com nulo exige `IS`, e o
SQLAlchemy prefere que você use a forma que sempre funciona.
:::

:::exercise level=3
O código abaixo roda sem erro e deixa o banco inconsistente uma vez a cada
muitas execuções. Explique e conserte.

```python
def transferir_estoque(session, de_id, para_id, qtd):
    origem = session.get(Produto, de_id)
    origem.estoque -= qtd
    session.commit()

    destino = session.get(Produto, para_id)
    destino.estoque += qtd
    session.commit()
```

:::answer
São **duas** transações. Entre o primeiro `commit` e o segundo, o estoque
saiu da origem e não chegou ao destino. Se o processo cair ali — ou se o
segundo `get` devolver `None` porque o produto foi apagado —, as caixas
desaparecem do sistema, e a conferência do mês não fecha por uma diferença
que nenhum log explica.

```python
def transferir_estoque(session, de_id, para_id, qtd):
    origem = session.get(Produto, de_id)
    destino = session.get(Produto, para_id)

    if origem is None or destino is None:
        raise ValueError("produto não encontrado")
    if origem.estoque < qtd:
        raise ValueError("estoque insuficiente")

    origem.estoque -= qtd
    destino.estoque += qtd
    session.commit()
```

Um `commit` só, no fim, depois de todas as verificações. É a aplicação
direta da regra do capítulo: o `commit` pertence a quem conhece a operação
inteira.

Vale notar o que **não** está resolvido: duas requisições simultâneas ainda
podem ler o mesmo estoque e subtrair as duas. Resolver isso exige travar a
linha — `with_for_update()` — ou uma restrição no banco que recuse estoque
negativo. O `commit` único garante atomicidade; não garante isolamento contra
concorrência, e são problemas diferentes.
:::
