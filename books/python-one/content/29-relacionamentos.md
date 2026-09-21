---
title: "Relacionamentos"
number: 29
slug: relacionamentos
part: p6
kicker: "O ORM faz parecer que o objeto já tem tudo dentro. A conta chega uma consulta por vez."
goal: >-
  Modelar um-para-muitos e muitos-para-muitos, escolher a estratégia de
  carregamento, e reconhecer o problema N+1 antes de ele chegar à produção.
---

Até aqui o catálogo tinha uma tabela. A cooperativa tem produtores, e cada
produto vem de um — que é o relacionamento mais comum que existe.

:::diagram type="er" caption="O domínio do livro ao fim da Parte 6."
columns: 2
entities:
  - name: "Produtor"
    fields: ["id (PK)", "nome", "cidade", "email"]
  - name: "Produto"
    fields: ["id (PK)", "nome", "preco", "estoque", "produtor_id (FK)"]
  - name: "Tag"
    fields: ["id (PK)", "nome"]
  - name: "produto_tag"
    fields: ["produto_id (FK)", "tag_id (FK)"]
relations:
  - { from: "Produtor", to: "Produto", label: "1:N" }
  - { from: "Produto", to: "produto_tag", label: "1:N" }
:::

## Um para muitos

```python title="app/models/produtor.py" numbered
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Produtor(Base):
    __tablename__ = "produtor"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(100))
    cidade: Mapped[str] = mapped_column(String(100))

    produtos: Mapped[list["Produto"]] = relationship(
        back_populates="produtor",
        cascade="all, delete-orphan",
    )


class Produto(Base):
    __tablename__ = "produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    produtor_id: Mapped[int] = mapped_column(
        ForeignKey("produtor.id"), index=True
    )

    produtor: Mapped["Produtor"] = relationship(
        back_populates="produtos"
    )
```

Duas coisas diferentes acontecem aqui, e confundi-las atrasa muita gente.

`ForeignKey("produtor.id")` é a **coluna** no banco: ela existe na tabela,
garante integridade referencial e impede um produto de apontar para um
produtor que não existe.

`relationship(...)` é a **navegação em Python**: ela não cria coluna nenhuma.
É o que permite escrever `produto.produtor.nome` e
`produtor.produtos[0].nome`.

`back_populates` liga as duas pontas: acrescentar um produto à lista do
produtor também preenche `produto.produtor`, na memória, sem ida ao banco.

:::key
A chave estrangeira mora do lado que tem **muitos**. Um produtor tem vários
produtos, então a coluna `produtor_id` fica na tabela `produto`. Essa regra
não tem exceção em um-para-muitos, e errá-la é a forma mais rápida de
descobrir que o modelo estava invertido.
:::

:::pitfall
O `index=True` na chave estrangeira não é opcional na prática. A maioria dos
bancos **não** cria índice automático para chave estrangeira — só para chave
primária. Sem ele, `SELECT * FROM produto WHERE produtor_id = 7` varre a
tabela, e apagar um produtor varre a tabela uma vez por dependência.
:::

## O problema N+1

```python title="o_defeito.py" numbered
produtos = session.scalars(select(Produto).limit(100)).all()

for p in produtos:
    print(p.nome, p.produtor.nome)
```

Esse laço parece inofensivo e dispara **101 consultas**: uma para trazer os
cem produtos, e mais uma por produto, na primeira vez que `p.produtor` é
tocado.

:::diagram type="sequence" caption="Cada `p.produtor` de um campo preguiçoso é uma ida ao banco."
actors:
  - { id: a, name: "App" }
  - { id: d, name: "Banco" }
messages:
  - { from: a, to: d, text: "SELECT produto LIMIT 100" }
  - { from: d, to: a, text: "100 linhas", dashed: true }
  - { from: a, to: d, text: "SELECT produtor WHERE id=1" }
  - { from: a, to: d, text: "SELECT produtor WHERE id=2" }
  - { from: a, to: d, text: "… mais 98 vezes" }
:::

Em desenvolvimento, com três produtos e o banco na mesma máquina, isso é
instantâneo. Em produção, com o banco a dois milissegundos de distância, são
duzentos milissegundos gastos em espera pura — por requisição.

E o motivo de o defeito ser tão comum é que **ele não aparece no código**.
A linha `p.produtor.nome` parece um acesso a atributo. O capítulo
@cap:encapsulamento avisou: consulta escondida atrás de propriedade é
consulta que ninguém suspeita.

## Carregamento preparado

```python title="selectinload.py" numbered
from sqlalchemy.orm import selectinload

stmt = (
    select(Produto)
    .options(selectinload(Produto.produtor))
    .limit(100)
)
produtos = session.scalars(stmt).all()
```

Duas consultas no total: uma para os produtos, outra para todos os
produtores de uma vez, com `WHERE id IN (...)`.

| Estratégia | Consultas | Quando usar |
|---|---|---|
| `lazy` (padrão) | 1 + N | acesso raro e pontual |
| `selectinload` | 2 | coleções e listagens — o padrão prático |
| `joinedload` | 1 | um-para-um e muitos-para-um |
| `raiseload` | erro | para proibir carregamento tardio |

Tabela: `selectinload` é a escolha certa na maioria das listagens; ela não
multiplica linhas como o `JOIN` faz.

:::key
`joinedload` traz tudo numa consulta só e, em um-para-muitos, multiplica as
linhas: cem produtores com dez produtos cada viram mil linhas transportadas,
com os dados do produtor repetidos dez vezes. Para **coleções**, prefira
`selectinload`; para **um objeto só do outro lado**, `joinedload`.
:::

## A defesa: proibir o carregamento tardio

```python title="raiseload.py" numbered
from sqlalchemy.orm import raiseload

stmt = select(Produto).options(raiseload("*")).limit(100)
```

Com `raiseload("*")`, qualquer acesso a um relacionamento não carregado
levanta exceção em vez de consultar. O defeito deixa de ser um problema de
desempenho invisível e vira um erro alto, na hora, no teste.

É uma configuração agressiva e vale a pena em rotas de listagem, onde o N+1
custa caro.

## Muitos para muitos

```python title="tags.py" numbered
from sqlalchemy import Column, Table

produto_tag = Table(
    "produto_tag",
    Base.metadata,
    Column(
        "produto_id", ForeignKey("produto.id"), primary_key=True
    ),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(40), unique=True)


class Produto(Base):
    tags: Mapped[list[Tag]] = relationship(
        secondary=produto_tag, back_populates="produtos"
    )
```

Muitos-para-muitos **sempre** precisa de uma terceira tabela. A chave
primária composta pelas duas colunas garante que o mesmo par não se repita.

:::pitfall
Se a associação tiver atributos próprios — a data em que a tag foi aplicada,
quem aplicou —, a tabela de associação deixa de ser detalhe e vira uma
entidade. Nesse caso, não use `secondary`: declare uma classe
`ProdutoTag` com os dois relacionamentos. Tentar pendurar atributo numa
`Table` de associação é um caminho que sempre termina em reescrita.
:::

## `cascade`: o que acontece com os filhos

```python
produtos: Mapped[list["Produto"]] = relationship(
    back_populates="produtor",
    cascade="all, delete-orphan",
)
```

`delete-orphan` significa: um produto removido da lista do produtor é
apagado do banco. `all` inclui o `delete` — apagar o produtor apaga os
produtos.

:::warning
`cascade="all, delete-orphan"` é conveniente e perigoso. Apagar um produtor
com trezentos produtos apaga trezentos produtos, sem confirmação. Em dados de
negócio, a alternativa quase sempre melhor é **não apagar**: um campo
`ativo` ou `removido_em` preserva o histórico e mantém as referências
válidas. Apagar de verdade é para dado que não tem passado.
:::

## O relacionamento no esquema de resposta

```python title="schema.py" numbered
class ProdutorResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cidade: str


class ProdutoLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    produtor: ProdutorResumo
```

E aqui as duas pontas se encontram: **esse esquema exige o
`selectinload`**. Sem ele, o Pydantic toca `produto.produtor` uma vez por
item durante a serialização, e o N+1 acontece depois que a sua função já
retornou — fora de qualquer lugar onde você pensaria em procurar.

:::story Duzentos milissegundos por produto
A listagem de produtos levava quatro segundos. Em desenvolvimento, quarenta
milissegundos.

— A diferença é o banco estar em outra máquina — disse Elias.

— Quatro segundos de rede?

— Não. Quatro segundos de *ida e volta*, vezes o número de vezes que você
pergunta.

Ele ligou o `echo=True` e recarregou a página uma vez. O terminal rolou por
quase dois segundos.

Bia olhou a contagem no fim.

— Cento e um.

— Cem produtos — disse Elias. — E uma pergunta sobre o produtor de cada um.
A sua consulta está certa. O seu laço é que conversa demais.
:::

:::summary
- `ForeignKey` é a coluna; `relationship` é a navegação em Python.
- A chave estrangeira mora do lado que tem muitos — e precisa de índice
  explícito.
- Acesso a relacionamento preguiçoso dentro de laço é o N+1.
- `selectinload` para coleções, `joinedload` para o lado singular.
- `raiseload("*")` transforma o N+1 invisível em erro imediato.
- Muitos-para-muitos exige terceira tabela; com atributos próprios, ela vira
  entidade.
- Esquema aninhado obriga carregamento preparado.
:::

:::checkpoint
Você modela os dois tipos de relacionamento, escolhe a estratégia de
carregamento pelo formato do dado, e sabe ler o terminal para descobrir
quantas consultas uma rota dispara.
:::

:::exercise level=1
Acrescente ao `Produto` o relacionamento com `Produtor` e ajuste
`ProdutoLer` para incluir `ProdutorResumo`.

:::answer
```python
class Produto(Base):
    produtor_id: Mapped[int] = mapped_column(
        ForeignKey("produtor.id"), index=True
    )
    produtor: Mapped["Produtor"] = relationship(
        back_populates="produtos"
    )
```
:::

:::exercise level=2
Ajuste o método `listar` do repositório para carregar o produtor junto e
confirme, com `echo=True`, que o número de consultas caiu para dois.

:::answer
```python
def listar(self, limite: int, deslocamento: int) -> list[Produto]:
    stmt = (
        select(Produto)
        .options(selectinload(Produto.produtor))
        .order_by(Produto.nome, Produto.id)
        .limit(limite)
        .offset(deslocamento)
    )
    return list(self.session.scalars(stmt))
```
O terminal passa a mostrar dois `SELECT`, o segundo com `IN (...)`. Vale
fazer isso com o `echo` ligado e contar as linhas antes e depois — é a forma
mais direta de tornar o problema concreto.
:::

:::exercise level=3
A cooperativa quer apagar um produtor que saiu. Ele tem 47 produtos, três
deles em pedidos já faturados. Descreva o que acontece com `cascade="all,
delete-orphan"`, o que acontece sem ele, e o que você faria.

:::answer
**Com `cascade`:** os 47 produtos são apagados. Se houver chave estrangeira
de `item_pedido` para `produto`, o banco recusa a operação inteira com
violação de integridade — e a transação toda é desfeita, incluindo a remoção
do produtor. Se **não** houver essa chave estrangeira, os itens de pedido
ficam apontando para produtos que não existem, e todo relatório histórico
passa a ter linhas sem nome. É a pior das duas saídas, porque é silenciosa.

**Sem `cascade`:** o banco recusa apagar o produtor enquanto existirem
produtos apontando para ele. A operação falha com uma mensagem técnica, e
alguém precisa decidir o que fazer com os 47.

**O que eu faria:** não apagar. O produtor saiu da cooperativa, e isso é um
fato novo, não o apagamento de um fato antigo — os pedidos de março
continuam tendo acontecido.

```python
class Produtor(Base):
    ativo: Mapped[bool] = mapped_column(default=True)
    saiu_em: Mapped[date | None] = mapped_column(default=None)
```

Os produtos dele saem da vitrine por filtro (`produtor.ativo`), o histórico
permanece íntegro, e o relatório de março continua dizendo a verdade sobre
março. O custo é que todo filtro de listagem precisa lembrar do `ativo` — e
esse custo se paga com um filtro padrão no repositório, não com um `if`
repetido em cada rota.

Apagar de verdade fica reservado para o caso em que alguém tem o direito de
exigir isso — o cadastro de uma pessoa física sob a LGPD, por exemplo. E aí
a operação não é um `DELETE`: é um processo, com anonimização do que precisa
sumir e preservação do que a legislação fiscal obriga a manter.
:::
