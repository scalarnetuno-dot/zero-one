---
title: "Serviço"
number: 22
slug: service
part: p4
kicker: "A camada onde mora a cooperativa — e não o HTTP, nem o SQL."
goal: >-
  Concentrar as regras de negócio numa camada própria, definir a fronteira da
  transação, levantar exceções de domínio e escrever código que pode ser
  testado sem servidor e sem banco.
---

O repositório sabe guardar. A rota sabe falar HTTP. Entre os dois falta
quem saiba **o que a cooperativa decidiu**: que não existem dois produtos
com o mesmo nome, que não se vende mais do que se tem, que preço abaixo do
custo precisa de aprovação.

Essas frases não são sobre banco nem sobre HTTP. Elas são o sistema.

## A regra sem casa

Sem uma camada de serviço, cada regra vai parar em um destes três lugares —
e os três são ruins:

| Onde acaba | O que dá errado |
|---|---|
| na rota | não dá para reusar fora do HTTP; teste precisa de servidor |
| no repositório | mistura decisão com armazenamento; não dá para trocar o banco |
| no modelo | a regra que envolve dois objetos não tem onde morar |

Tabela: A regra que envolve mais de uma entidade é o caso que decide: ela
não cabe em nenhum dos três.

## O serviço

```python title="app/services/produto.py" numbered
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.repositories.produto import ProdutoRepositorio


class ProdutoJaExiste(Exception):
    def __init__(self, nome: str):
        self.nome = nome
        super().__init__(f"produto '{nome}' já cadastrado")


class ProdutoNaoEncontrado(Exception):
    def __init__(self, produto_id: int):
        self.produto_id = produto_id
        super().__init__(f"produto {produto_id} não encontrado")


class EstoqueInsuficiente(Exception):
    def __init__(self, disponivel: int, pedido: int):
        self.disponivel = disponivel
        self.pedido = pedido
        super().__init__("estoque insuficiente")


class QuantidadeInvalida(Exception):
    def __init__(self, quantidade: int):
        self.quantidade = quantidade
        super().__init__("a quantidade deve ser maior que zero")


class ProdutoServico:
    def __init__(self, session: Session, repo: ProdutoRepositorio):
        self.session = session
        self.repo = repo

    def criar(
        self, nome: str, preco: Decimal, estoque: int
    ) -> Produto:
        nome = " ".join(nome.split())

        if self.repo.buscar_por_nome(nome) is not None:
            raise ProdutoJaExiste(nome)

        produto = Produto(nome=nome, preco=preco, estoque=estoque)
        self.repo.criar(produto)
        self.session.commit()
        return produto

    def vender(self, produto_id: int, quantidade: int) -> Produto:
        if quantidade <= 0:
            raise QuantidadeInvalida(quantidade)

        produto = self.repo.buscar(produto_id)
        if produto is None:
            raise ProdutoNaoEncontrado(produto_id)

        if quantidade > produto.estoque:
            raise EstoqueInsuficiente(produto.estoque, quantidade)

        produto.estoque -= quantidade
        self.session.commit()
        return produto
```

Três características valem nome.

O serviço **não importa nada de FastAPI**. Não há `HTTPException`, não há
`status_code`, não há `Request`. Ele poderia ser chamado por uma rota, por
um script de importação ou por uma tarefa agendada, sem uma linha diferente.

Ele **confirma a transação**, porque é ele quem conhece a operação inteira.
Essa é a resposta ao exercício do capítulo @cap:repository.

E ele **fala a língua do negócio**: `ProdutoJaExiste`, não `IntegrityError`;
`EstoqueInsuficiente`, não `ValueError`.

:::diagram type="blocks" caption="Cada camada só conhece a de baixo — e só faz uma coisa."
rows:
  - [{ text: "Router", note: "HTTP: status, corpo, cabeçalho" }]
  - [{ text: "Service", note: "regras, transação, exceções do domínio" }]
  - [{ text: "Repository", note: "consultas e escritas" }]
  - [{ text: "Model / Banco", note: "a estrutura do dado" }]
:::

## A rota fica curta

```python title="app/routers/produtos.py" numbered
@router.post("", response_model=ProdutoLer, status_code=201)
def criar(
    dados: ProdutoCriar,
    servico: ProdutoServico = Depends(get_produto_servico),
):
    try:
        return servico.criar(dados.nome, dados.preco, dados.estoque)
    except ProdutoJaExiste as erro:
        raise HTTPException(409, str(erro)) from erro
```

A rota faz três coisas e só: recebe o modelo validado, chama o serviço, e
traduz a exceção de domínio em código HTTP. Esse `try` vai sumir no capítulo
@cap:tratamento-de-erros, substituído por um tratador global — e a rota vai
ficar com duas linhas.

:::key
A pergunta que separa as camadas: *se amanhã esta funcionalidade precisar
rodar por uma tarefa agendada, sem HTTP, o que eu teria de reescrever?* Se a
resposta for "nada, chamo o serviço", as camadas estão certas. Se for
"preciso copiar a lógica da rota", elas não estão.
:::

## A fronteira da transação

```python title="transacao.py" numbered
def transferir(self, de_id: int, para_id: int, caixas: int) -> None:
    origem = self.repo.buscar(de_id)
    destino = self.repo.buscar(para_id)

    if origem is None:
        raise ProdutoNaoEncontrado(de_id)
    if destino is None:
        raise ProdutoNaoEncontrado(para_id)
    if origem.estoque < caixas:
        raise EstoqueInsuficiente(origem.estoque, caixas)

    origem.estoque -= caixas
    destino.estoque += caixas
    self.session.commit()
```

Um método público do serviço é **uma** transação. Ela começa quando o método
começa e termina no `commit` — ou no `rollback`, se uma exceção escapar.

:::diagram type="sequence" caption="A operação inteira dentro de uma transação: ou as duas escritas, ou nenhuma."
actors:
  - { id: r, name: "Router" }
  - { id: s, name: "Service" }
  - { id: p, name: "Repo" }
  - { id: d, name: "Banco" }
messages:
  - { from: r, to: s, text: "transferir(1, 2, 10)" }
  - { from: s, to: p, text: "buscar(1)" }
  - { from: p, to: d, text: "SELECT" }
  - { from: s, to: p, text: "buscar(2)" }
  - { from: p, to: d, text: "SELECT" }
  - { from: s, to: d, text: "UPDATE ×2 + COMMIT" }
  - { from: s, to: r, text: "pronto", dashed: true }
:::

:::warning
Um serviço que chama outro serviço, e cada um com seu `commit`, quebra a
atomicidade sem aviso. Quando duas operações precisam acontecer juntas, ou
elas são um método só, ou os métodos internos recebem a transação em aberto e
só o método de entrada confirma. A convenção deste livro: **métodos privados
não confirmam**.
:::

## Onde o rollback acontece

```python title="app/dependencies.py" numbered
def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

Se uma exceção escapar do serviço, a sessão desfaz. É o `finally` do
capítulo @cap:excecoes fazendo o trabalho de sempre — e é por isso que o
serviço pode levantar exceção no meio de uma operação sem limpar nada à mão.

## Regra no serviço ou no banco?

Algumas regras cabem nos dois lugares, e a resposta quase sempre é **nos
dois**.

| Regra | Serviço | Banco |
|---|---|---|
| nome não repetido | consulta antes, erro amigável | `UNIQUE` |
| estoque não negativo | recusa com mensagem | `CHECK (estoque >= 0)` |
| preço positivo | validação no Pydantic | `CHECK (preco > 0)` |

Tabela: O serviço dá a mensagem boa; o banco dá a garantia. Os dois juntos
dão as duas coisas.

A razão é a janela entre a consulta e a escrita. O serviço verifica que o
nome não existe; entre essa verificação e o `INSERT`, outra requisição pode
inserir o mesmo nome. A restrição `UNIQUE` fecha a janela — e o serviço
precisa estar preparado para capturar o `IntegrityError` que ela produz:

```python title="a_corrida.py" numbered
from sqlalchemy.exc import IntegrityError

try:
    self.repo.criar(produto)
    self.session.commit()
except IntegrityError as erro:
    self.session.rollback()
    raise ProdutoJaExiste(nome) from erro
```

:::key
Verificar antes é para dar uma boa mensagem no caso comum. A restrição no
banco é para a verdade. Escrever só a primeira é aceitar uma corrida rara;
escrever só a segunda é entregar uma mensagem técnica ao usuário. Escreva as
duas e converta uma na outra.
:::

:::story A terceira verificação
— Já tem `UNIQUE` no banco — disse Rafa. — Por que conferir de novo no
serviço?

— Porque a mensagem do banco é essa aqui. — Bia colou no chat:

```text
duplicate key value violates unique constraint
"produto_nome_key"
DETAIL: Key (nome)=(Tomate italiano) already exists.
```

— E a do serviço é "produto 'Tomate italiano' já cadastrado".

— A do banco diz mais.

— Diz mais para você. — Ela apontou para a tela onde a Dona Neuza estaria. —
O suporte que atende o produtor não sabe o que é `produto_nome_key`. E se
um dia a gente renomear a restrição, a mensagem muda sozinha, no meio do
expediente, sem ninguém ter decidido nada.
:::

:::summary
- O serviço é onde as regras do negócio moram, e ele não conhece HTTP.
- Um método público do serviço é uma transação; ele confirma, o repositório
  não.
- Exceções do domínio falam a língua do negócio, não do banco.
- Método privado não confirma; só o de entrada.
- O `rollback` fica na dependência da sessão, não espalhado nos serviços.
- Regra crítica vive no serviço **e** no banco: mensagem boa e garantia real.
:::

:::milestone
As quatro camadas existem. Daqui em diante, toda funcionalidade nova entra
sempre pelo mesmo caminho — e a pergunta "onde eu escrevo isso?" passa a ter
resposta.
:::

:::exercise level=1
Escreva `ProdutoServico.buscar(produto_id)`, levantando
`ProdutoNaoEncontrado` quando não existir.

:::answer
```python
def buscar(self, produto_id: int) -> Produto:
    produto = self.repo.buscar(produto_id)
    if produto is None:
        raise ProdutoNaoEncontrado(produto_id)
    return produto
```
Repare no tipo de retorno: `Produto`, sem `| None`. O serviço converteu a
ausência em exceção, e quem chama não precisa mais tratar o nulo. Essa
diferença de assinatura entre repositório e serviço é intencional.
:::

:::exercise level=2
Implemente `repor(produto_id, caixas)` que aumente o estoque, recusando
quantidade menor ou igual a zero, e registre a operação num log.

:::answer
```python
import logging

logger = logging.getLogger(__name__)


def repor(self, produto_id: int, caixas: int) -> Produto:
    if caixas <= 0:
        raise ValueError("reposição precisa ser positiva")

    produto = self.repo.buscar(produto_id)
    if produto is None:
        raise ProdutoNaoEncontrado(produto_id)

    produto.estoque += caixas
    self.session.commit()

    logger.info(
        "reposicao produto=%s caixas=%s total=%s",
        produto.id, caixas, produto.estoque,
    )
    return produto
```
O log vem **depois** do `commit`: registrar antes é prometer algo que ainda
pode ser desfeito. E os valores vão como argumentos, não interpolados na
mensagem — assim o sistema de log pode agrupar por formato e você consegue
buscar "todas as reposições" sem expressão regular.
:::

:::exercise level=3
A cooperativa decidiu: quando um produto chega a estoque zero, ele passa
automaticamente para o status `ESGOTADO`, e quando é reposto, volta para
`ATIVO` — exceto se estiver `DESCONTINUADO`, quando nada muda. Implemente e
explique por que essa regra não pode morar no modelo nem no repositório.

:::answer
```python
def _atualizar_status(self, produto: Produto) -> None:
    if produto.status is StatusProduto.DESCONTINUADO:
        return
    if produto.estoque == 0:
        produto.status = StatusProduto.ESGOTADO
    else:
        produto.status = StatusProduto.ATIVO


def vender(self, produto_id: int, quantidade: int) -> Produto:
    produto = self.repo.buscar(produto_id)
    if produto is None:
        raise ProdutoNaoEncontrado(produto_id)
    if quantidade > produto.estoque:
        raise EstoqueInsuficiente(produto.estoque, quantidade)

    produto.estoque -= quantidade
    self._atualizar_status(produto)
    self.session.commit()
    return produto
```

**Por que não no repositório:** ele guarda e recupera. Uma regra que decide
um valor a partir de outro é decisão, e decisão não é armazenamento. Pior:
colocada ali, ela sumiria da implementação em memória, e o teste passaria
enquanto a produção se comportaria de outro jeito.

**Por que não no modelo:** aqui a resposta é mais delicada, porque *poderia*.
`Produto.atualizar_status()` seria legítimo — a regra envolve um objeto só e
usa apenas dados dele. Duas coisas empurram para o serviço neste projeto: no
capítulo @cap:sqlalchemy o modelo virou uma classe do ORM, e encher a classe
de regra amarra o domínio ao SQLAlchemy; e a regra vai crescer — "avisar o
produtor quando esgotar" envolve outro objeto e um envio de e-mail, que não
têm nada que fazer dentro de uma linha de tabela.

O `_atualizar_status` com sublinhado é privado e **não confirma**, seguindo
a convenção do capítulo. Ele é chamado por `vender` e por `repor`, e a
transação continua sendo uma só.
:::
