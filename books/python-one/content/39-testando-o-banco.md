---
title: "Testando o banco"
number: 39
slug: testando-o-banco
part: p8
kicker: "Um teste verde em outro banco é uma opinião sobre outro sistema."
goal: >-
  Rodar testes contra um PostgreSQL de verdade, isolar cada teste por
  transação, subir o banco com contêiner e testar o que só o banco garante.
---

Os capítulos anteriores testaram sem banco de propósito. Mas há coisas que
**só** o banco decide: a restrição `UNIQUE`, o `CHECK`, a chave estrangeira,
o SQL que o ORM gerou, e o comportamento sob concorrência.

Nada disso aparece no repositório falso. Por isso existe esta faixa da
pirâmide.

## SQLite não serve

A tentação é rodar os testes em SQLite, que não precisa de instalação. Ele é
rápido, é um arquivo, e mente em vários pontos:

| Comportamento | PostgreSQL | SQLite |
|---|---|---|
| `NUMERIC(10,2)` | decimal exato | vira ponto flutuante |
| Tipos de coluna | exigidos | quase sugestões |
| `ALTER TABLE` | completo | muito limitado |
| Chave estrangeira | sempre | desligada por padrão |
| Concorrência de escrita | por linha | trava o arquivo |
| `ILIKE`, `tsvector`, `JSONB` | existem | não existem |

Tabela: Cada linha dessa tabela é um teste que passa em SQLite e quebra em
produção.

:::key
Teste de banco roda no **mesmo** banco da produção, na mesma versão
principal. Qualquer outra escolha troca a garantia do teste por comodidade
de ambiente — e a comodidade se resolve com um contêiner, enquanto a
garantia não se resolve com nada.
:::

## O banco de teste

```python title="tests/conftest.py" numbered
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base

URL = "postgresql+psycopg://catalogo:senha@localhost/catalogo_test"


@pytest.fixture(scope="session")
def engine():
    eng = create_engine(URL)
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()
```

`scope="session"` faz isso acontecer **uma vez** para toda a execução.
Criar o esquema a cada teste é a causa número um de suíte lenta, como o
exercício do capítulo @cap:testando-a-api apontou.

## Isolamento por transação

```python title="tests/conftest.py" numbered
@pytest.fixture
def session(engine):
    conexao = engine.connect()
    transacao = conexao.begin()
    Session = sessionmaker(bind=conexao, expire_on_commit=False)
    sessao = Session()

    yield sessao

    sessao.close()
    transacao.rollback()
    conexao.close()
```

Esta é a fixture mais valiosa do capítulo, e o truque merece ser entendido.

A sessão é ligada a uma **conexão** com uma transação já aberta, e não ao
engine. Tudo que o teste gravar acontece dentro dela. No fim, o `rollback`
desfaz — inclusive o que o código de produção confirmou com `commit`, porque
aquele `commit` encerrou apenas a transação interna, aninhada na externa que
o teste abriu.

O resultado: cada teste começa com o banco no mesmo estado, sem `DELETE`,
sem recriar tabela, sem ordem de execução importando. E é rápido — um
`rollback` custa menos que qualquer limpeza.

:::pitfall
`TRUNCATE` entre testes também funciona e é mais lento, porque toca disco e
reinicia sequências. O que **não** funciona é apagar com `DELETE FROM` em
laço: com chave estrangeira, a ordem passa a importar, e no dia em que
alguém acrescentar uma tabela, o conjunto quebra em um teste que não tem
relação com a mudança.
:::

## Testando o que só o banco garante

```python title="tests/test_banco.py" numbered
from sqlalchemy.exc import IntegrityError


def test_nome_duplicado_viola_restricao(session):
    session.add(Produto(nome="Tomate", preco=Decimal("8.90")))
    session.flush()

    session.add(Produto(nome="Tomate", preco=Decimal("9.10")))

    with pytest.raises(IntegrityError):
        session.flush()


def test_estoque_negativo_e_recusado(session):
    produto = Produto(
        nome="Tomate", preco=Decimal("8.90"), estoque=0
    )
    session.add(produto)
    session.flush()

    produto.estoque = -1

    with pytest.raises(IntegrityError):
        session.flush()


def test_preco_mantem_duas_casas(session):
    session.add(
        Produto(nome="Tomate", preco=Decimal("8.905"))
    )
    session.flush()
    session.expire_all()

    lido = session.scalars(select(Produto)).one()
    assert lido.preco == Decimal("8.91")
```

O terceiro teste é o que ninguém escreve e todo mundo deveria: ele verifica
que o `NUMERIC(10,2)` do PostgreSQL arredonda e, principalmente, **como**
arredonda. O PostgreSQL usa arredondamento para o valor mais próximo; em
SQLite o teste pode passar por acidente, com outro resultado.

O `expire_all()` é necessário: sem ele, a sessão devolveria o objeto que
ainda está em memória, com o valor original, e o teste verificaria Python em
vez de banco.

## Contêiner: o banco que nasce com a suíte

```text
$ pip install testcontainers[postgres]
```

```python title="tests/conftest.py" numbered
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def engine():
    with PostgresContainer("postgres:16") as pg:
        eng = create_engine(pg.get_connection_url())
        Base.metadata.create_all(eng)
        yield eng
```

O contêiner sobe antes do primeiro teste, serve todos, e é destruído no fim.
Quem clona o projeto roda `pytest` e funciona — sem instalar PostgreSQL, sem
`README` com cinco passos, sem "na minha máquina".

:::diagram type="flowchart" caption="O contêiner sobe uma vez, serve todos os testes e some no fim."
nodes:
  - { id: i, type: start,   text: "pytest" }
  - { id: c, type: process, text: "sobe postgres:16" }
  - { id: m, type: process, text: "cria o esquema" }
  - { id: t, type: process, text: "cada teste: transação + rollback" }
  - { id: f, type: start,   text: "destrói o contêiner" }
edges:
  - { from: i, to: c }
  - { from: c, to: m }
  - { from: m, to: t }
  - { from: t, to: t }
  - { from: t, to: f }
:::

:::warning
O contêiner exige Docker na máquina e na esteira, e acrescenta alguns
segundos ao início da execução. Esse custo é pago uma vez por sessão — mas
significa que a suíte de banco não deve rodar a cada salvamento. Ela é a
faixa do meio da pirâmide: roda antes do commit e na integração contínua.
:::

## Esquema por `create_all` ou por migração?

| | `create_all` | Alembic |
|---|---|---|
| Velocidade | instantâneo | alguns segundos |
| Testa as migrações | não | sim |
| Reflete produção | quase | exatamente |

Tabela: O "quase" da última linha é onde mora o problema.

`create_all` monta o esquema a partir dos modelos. Se uma migração estiver
errada — faltou um índice, faltou um `CHECK`, alguém editou um arquivo já
aplicado —, o teste não percebe: ele testa o banco que **deveria** existir,
não o que existe.

:::key
O arranjo que funciona bem: `create_all` na suíte do dia a dia, pela
velocidade, e um trabalho separado na integração contínua que roda `alembic
upgrade head` num banco vazio e compara o resultado com `Base.metadata`. O
Alembic tem o comando para isso — uma migração gerada contra o banco
migrado precisa vir **vazia**. Se vier com conteúdo, modelo e migrações
divergiram.
:::

## Testando concorrência

```python title="tests/test_concorrencia.py" numbered
from threading import Barrier, Thread


def test_duas_vendas_simultaneas(engine):
    largada = Barrier(2)

    def vender():
        with Session(engine) as sessao:
            largada.wait()
            with sessao.begin():
                produto = sessao.scalars(
                    select(Produto)
                    .where(Produto.id == 1)
                    .with_for_update()
                ).one()
                if produto.estoque >= 10:
                    produto.estoque -= 10

    threads = [Thread(target=vender) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    with Session(engine) as sessao:
        produto = sessao.get(Produto, 1)
        assert produto.estoque == 80
```

Testar concorrência é difícil e vale a pena nos poucos pontos em que o
dinheiro depende disso. As duas threads começam juntas e cada sessão adquire
uma conexão independente. `with_for_update()` faz a segunda esperar pela
primeira; quando ela lê o estoque atualizado, a soma final é 80, não 90 nem
70. O teste não usa a fixture `session`: a transação externa do isolamento
impediria as duas sessões de enxergar o comportamento real.

:::summary
- SQLite mente em tipos, restrições e concorrência: teste no banco de
  produção.
- Esquema uma vez por sessão; isolamento por transação desfeita.
- `rollback` desfaz até o que o código confirmou, porque a transação do
  teste é a externa.
- Teste aqui o que só o banco garante: restrições, precisão, SQL gerado.
- Contêiner elimina o "na minha máquina" e custa segundos por sessão.
- `create_all` é rápido e não testa as migrações — confira as duas coisas.
:::

:::milestone
As três faixas da pirâmide existem. O projeto pode ser alterado com a
expectativa razoável de que, se algo importante quebrar, alguém vai saber
antes do cliente.
:::

:::exercise level=1
Escreva a fixture `session` com isolamento por transação e um teste que grave
um produto e o leia de volta.

:::answer
```python
def test_grava_e_le(session):
    session.add(
        Produto(nome="Tomate", preco=Decimal("8.90"))
    )
    session.flush()

    lido = session.scalars(select(Produto)).one()
    assert lido.nome == "Tomate"
```
`flush` em vez de `commit` é suficiente: o dado vai ao banco e continua
dentro da transação do teste.
:::

:::exercise level=2
Escreva o teste que garante que apagar um produtor com produtos é recusado
pelo banco.

:::answer
```python
def test_nao_apaga_produtor_com_produtos(session):
    produtor = Produtor(nome="Seu Onofre", cidade="Ibiúna")
    session.add(produtor)
    session.flush()

    session.add(
        Produto(
            nome="Tomate",
            preco=Decimal("8.90"),
            produtor_id=produtor.id,
        )
    )
    session.flush()

    session.execute(
        delete(Produtor).where(Produtor.id == produtor.id)
    )

    with pytest.raises(IntegrityError):
        session.flush()
```
O `delete()` direto, em vez de `session.delete(produtor)`, é deliberado: o
segundo dispararia o `cascade` configurado no relacionamento e apagaria os
produtos antes. O que se quer testar aqui é a garantia do **banco**, sem a
ajuda do ORM.
:::

:::exercise level=3
A suíte de banco leva quatro minutos na esteira e trinta segundos na máquina
dos desenvolvedores. Investigue as causas possíveis e proponha o que medir.

:::answer
A diferença de oito vezes quase nunca é o mesmo trabalho sendo mais lento:
é **trabalho a mais**.

**Primeira hipótese: a esteira sobe o banco por trabalho, não por sessão.**
Se a configuração cria um contêiner por arquivo de teste — ou pior, se o
`scope` da fixture ficou no padrão —, são dezenas de inicializações de
PostgreSQL. Medir: contar quantas vezes a linha de inicialização aparece no
log da esteira.

**Segunda: o cache de dependências não existe na esteira.** Baixar a imagem
do PostgreSQL e instalar os pacotes a cada execução custa minutos e não
aparece no tempo do `pytest`. Medir: comparar o tempo total do trabalho com
o tempo relatado pelo pytest no fim. Se a diferença for grande, o problema
não está nos testes.

**Terceira: disco e recursos.** Runners compartilhados têm disco lento e
pouca memória, e o PostgreSQL com configuração padrão faz `fsync` a cada
confirmação. Em banco descartável isso é desperdício puro: `fsync=off`,
`synchronous_commit=off` e `full_page_writes=off` são seguros aí — o banco
some no fim de qualquer jeito — e costumam cortar o tempo pela metade.

**Quarta: paralelismo ausente.** A máquina local tem oito núcleos; o runner,
dois. `pytest -n auto` ajuda numa e não na outra — e exige que o isolamento
por transação esteja correto, ou os testes passam a interferir.

**O que eu mediria, em ordem:** o tempo do trabalho inteiro contra o tempo
do `pytest`; o `--durations=20` da esteira comparado com o local; e o número
de inicializações do banco. As três medições cabem numa execução, e uma
delas costuma explicar os quatro minutos sozinha.
:::
