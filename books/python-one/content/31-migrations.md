---
title: "Migrações"
number: 31
slug: migrations
part: p6
kicker: "O banco de produção não pode ser recriado. Ele só pode ser transformado, um passo por vez, na mesma ordem em todo lugar."
goal: >-
  Trocar `create_all` pelo Alembic, gerar e revisar migrações, escrever
  migração de dados, e planejar uma alteração que não derruba a aplicação.
---

O `create_all` do capítulo @cap:o-crud-completo tem um limite claro: ele
cria o que falta e **não altera o que existe**. Acrescente uma coluna ao
modelo, rode de novo, e nada acontece — até a primeira consulta falhar com
"coluna não existe".

Em desenvolvimento, apagar o banco e recriar resolve. Em produção, apagar o
banco é o fim da empresa.

## Alembic

```text
$ pip install alembic
$ alembic init -t async migracoes
```

Para este livro, que usa sessão síncrona, o modelo comum basta:

```text
$ alembic init migracoes
```

```text title="alembic.ini"
script_location = migracoes
```

```python title="migracoes/env.py" numbered
from app.config import get_config
from app.database import Base
from app.models import produto, produtor  # registra os modelos

config.set_main_option(
    "sqlalchemy.url", get_config().database_url
)
target_metadata = Base.metadata
```

Aquele import dos modelos parece supérfluo e é obrigatório. O Alembic
compara o banco com `Base.metadata`, e um modelo que nunca foi importado não
está lá — a migração gerada apagaria a tabela dele.

:::warning
Esse é o erro mais destrutivo do Alembic. Se você esquecer de importar um
modelo em `env.py`, o `autogenerate` vê uma tabela no banco que "não existe"
no código e gera um `drop_table`. Rodar isso sem ler é apagar dados de
produção com um comando que você mesmo gerou.
:::

## Gerar e revisar

```text
$ alembic revision --autogenerate -m "cria produto e produtor"
```

```python title="migracoes/versions/a1b2c3_cria_produto.py" numbered
revision = "a1b2c3"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "produtor",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("nome", sa.String(100), nullable=False),
        sa.Column("cidade", sa.String(100), nullable=False),
    )
    op.create_table(
        "produto",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("preco", sa.Numeric(10, 2), nullable=False),
        sa.Column("produtor_id", sa.BigInteger(), nullable=False),
    )
    op.create_foreign_key(
        "fk_produto_produtor", "produto", "produtor",
        ["produtor_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_table("produto")
    op.drop_table("produtor")
```

```text
$ alembic upgrade head
$ alembic current
$ alembic downgrade -1
```

O `head` é a última migração; `-1` volta uma. O Alembic guarda a posição
atual numa tabela chamada `alembic_version`, dentro do próprio banco — é
assim que ele sabe o que já rodou.

:::key
`--autogenerate` produz um rascunho, não uma migração. **Leia sempre antes
de rodar.** Ele não detecta renomeação (vê um `drop` e um `add`), erra com
tipos personalizados, ignora alterações que dependem de dados, e às vezes
propõe recriar um índice que já existe com outro nome.
:::

## O que o autogenerate não vê

| Mudança | O Alembic detecta? |
|---|---|
| coluna nova, coluna removida | sim |
| tipo da coluna alterado | quase sempre |
| coluna **renomeada** | não — vê remoção + criação |
| índice e restrição | sim, com configuração |
| `CHECK` e valor padrão do servidor | frequentemente não |
| qualquer coisa sobre os **dados** | nunca |

Tabela: A última linha é a mais importante: migração de dado é sempre
escrita à mão.

## Renomear sem perder dado

```python title="renomear.py" numbered
def upgrade() -> None:
    op.alter_column(
        "produto",
        "estoque",
        new_column_name="quantidade_disponivel",
    )


def downgrade() -> None:
    op.alter_column(
        "produto",
        "quantidade_disponivel",
        new_column_name="estoque",
    )
```

Duas linhas escritas à mão no lugar do `drop_column` + `add_column` que o
autogenerate propôs — e que teria apagado o estoque de todos os produtos.

## Migração de dados

```python title="dados.py" numbered
from sqlalchemy import table, column, String
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column(
        "produto",
        sa.Column("categoria", sa.String(20), nullable=True),
    )

    produto = table("produto", column("categoria", String))
    op.execute(
        produto.update().values(categoria="legume")
    )

    op.alter_column("produto", "categoria", nullable=False)
```

Três passos, e a ordem é obrigatória: criar a coluna aceitando nulo,
preencher as linhas existentes, e só então exigir preenchimento. Tentar
criar `NOT NULL` direto numa tabela com dados falha imediatamente.

:::pitfall
Repare que a migração define a tabela localmente, com `table(...)` e
`column(...)`, em vez de importar o modelo `Produto`. É deliberado: o modelo
de hoje tem colunas que não existiam quando essa migração foi escrita, e
importá-lo faria a migração antiga quebrar no dia em que o modelo mudasse.
**Migração não importa modelo.**
:::

## Alteração sem derrubar a aplicação

Durante uma implantação, por alguns minutos, a versão antiga e a nova do
código rodam ao mesmo tempo. Uma migração que quebra a versão antiga derruba
metade das requisições.

| Mudança | Segura? |
|---|---|
| acrescentar coluna anulável | sim |
| acrescentar coluna `NOT NULL` com padrão | sim, em PostgreSQL recente |
| remover coluna | **não** — o código antigo ainda a seleciona |
| renomear coluna | **não** |
| acrescentar índice | sim, com `CONCURRENTLY` |

Tabela: A regra geral: acrescentar é seguro, remover e renomear não são.

A saída, sempre a mesma, é a expansão-e-contração em três implantações:

:::diagram type="timeline" caption="Remover uma coluna sem derrubar ninguém leva três implantações, não uma."
width: 112
events:
  - { year: "1", text: "Migração: cria a coluna nova. O código escreve nas duas e lê da antiga", mark: true }
  - { year: "2", text: "Código: passa a ler da coluna nova; continua escrevendo nas duas" }
  - { year: "3", text: "Código: para de escrever na antiga" }
  - { year: "4", text: "Migração: remove a coluna antiga", mark: true }
:::

Parece exagero para uma coluna. É o que permite implantar no meio da tarde
em vez de às três da manhã de domingo — e esse é o único critério que
importa.

## Regras de convivência

```text
$ alembic heads
```

Se esse comando devolver **duas** linhas, duas pessoas criaram migrações a
partir da mesma base. O conserto é `alembic merge`, e a prevenção é
combinar: migração entra em sequência, revisada, e ninguém edita a de
outro.

:::warning
**Nunca edite uma migração que já rodou em produção.** O Alembic registra
apenas o identificador, não o conteúdo: mudar o arquivo depois faz o banco
e o código divergirem em silêncio, e a próxima pessoa a criar o ambiente do
zero vai ter um banco diferente do de produção. Migração errada se conserta
com migração nova.
:::

:::summary
- `create_all` cria o que falta; ele nunca altera o que existe.
- `env.py` precisa importar todos os modelos, ou o autogenerate propõe
  apagá-los.
- `--autogenerate` produz rascunho: leia antes de rodar.
- Renomear e migrar dados é sempre à mão; migração não importa modelo.
- Acrescentar é seguro; remover e renomear exigem expansão e contração.
- Migração que já rodou não se edita — se corrige com outra.
:::

:::milestone
O banco passou a ter histórico. Qualquer pessoa cria o ambiente do zero com
um comando, e toda alteração de estrutura é um arquivo revisável, igual a
qualquer outra mudança de código.
:::

:::exercise level=1
Gere a migração que acrescenta a coluna `ativo` (booleano, padrão
verdadeiro) à tabela `produto`, e confira o arquivo gerado.

:::answer
```python
def upgrade() -> None:
    op.add_column(
        "produto",
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column("produto", "ativo")
```
O `server_default` é o que permite criar a coluna já como `NOT NULL` numa
tabela com dados: o banco preenche as linhas existentes. Sem ele, é preciso
o caminho de três passos.
:::

:::exercise level=1
Escreva a migração que renomeia a tabela `produto_tag` para
`produto_etiqueta`, preservando os dados e as restrições.

:::answer
```python
def upgrade() -> None:
    op.rename_table("produto_tag", "produto_etiqueta")


def downgrade() -> None:
    op.rename_table("produto_etiqueta", "produto_tag")
```
Uma linha, e ela preserva tudo — dados, índices e chaves estrangeiras — que
o `drop_table` + `create_table` proposto pelo autogenerate teria destruído.

O que a migração **não** faz é renomear as restrições: o índice continua se
chamando `uq_produto_tag_nome`. Isso funciona e envelhece mal, porque daqui
a um ano ninguém vai saber a que tabela aquele nome se refere. Acrescentar
os `op.execute("ALTER ... RENAME CONSTRAINT ...")` correspondentes é a parte
que separa uma migração que roda de uma migração que se lê.
:::

:::exercise level=2
Escreva a migração que cria a tabela `tag` e a tabela de associação
`produto_tag`.

:::answer
```python
def upgrade() -> None:
    op.create_table(
        "tag",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("nome", sa.String(40), nullable=False),
        sa.UniqueConstraint("nome", name="uq_tag_nome"),
    )
    op.create_table(
        "produto_tag",
        sa.Column("produto_id", sa.BigInteger(), nullable=False),
        sa.Column("tag_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["produto_id"], ["produto.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.PrimaryKeyConstraint("produto_id", "tag_id"),
    )
```
O `ondelete="CASCADE"` só na primeira chave é deliberado: apagar um produto
remove suas associações, mas apagar uma tag em uso deve falhar — a tag está
sendo usada, e alguém precisa decidir.
:::

:::exercise level=3
A tabela `produto` tem 8 milhões de linhas. O time precisa acrescentar um
índice em `produtor_id`, que hoje não tem. Descreva o risco e o comando
correto.

:::answer
`CREATE INDEX` comum trava a tabela para escrita durante toda a criação. Em
oito milhões de linhas, isso são minutos — e durante esses minutos, toda
requisição que grava produto fica esperando, o pool de conexões enche, e a
API para de responder mesmo para quem só lê.

O comando correto:

```sql
CREATE INDEX CONCURRENTLY idx_produto_produtor
  ON produto (produtor_id);
```

`CONCURRENTLY` constrói o índice sem travar escrita. Ele é mais lento, faz
duas varreduras em vez de uma, e pode falhar deixando um índice inválido —
que precisa ser removido e recriado.

O detalhe que quase todo mundo esbarra: `CONCURRENTLY` **não pode rodar
dentro de uma transação**, e o Alembic envolve cada migração numa. A
migração precisa sair do modo transacional explicitamente:

```python
def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.create_index(
            "idx_produto_produtor",
            "produto",
            ["produtor_id"],
            postgresql_concurrently=True,
        )
```

E vale registrar a consequência: essa migração não tem rollback automático.
Se ela falhar no meio, o banco fica com um índice inválido e a
`alembic_version` não avança — é preciso limpar à mão antes de tentar de
novo. Migração sem transação é uma decisão consciente, e merece um
comentário no arquivo dizendo por que ela está ali.
:::
