---
title: "Repositório"
number: 21
slug: repository
part: p4
kicker: "A camada que conhece o banco — e a única do projeto que tem esse direito."
goal: >-
  Isolar o acesso a dados numa camada própria, definir o contrato com
  `Protocol`, e entender por que o repositório não confirma transação nem
  decide regra.
---

O capítulo anterior deixou consultas espalhadas pelo script. Se elas forem
para dentro das rotas, o projeto volta a ter o mesmo problema do capítulo
@cap:primeira-api, só que com SQL: a regra de negócio, a tradução HTTP e o
acesso ao banco todos no mesmo lugar.

O repositório é a fronteira. Ele responde a uma pergunta só: *como se
guarda e se recupera um produto?*

## O contrato

```python title="app/repositories/produto.py" numbered
from typing import Protocol

from app.models.produto import Produto


class ProdutoRepositorio(Protocol):
    def buscar(self, produto_id: int) -> Produto | None: ...
    def listar(
        self, limite: int, deslocamento: int
    ) -> list[Produto]: ...
    def buscar_por_nome(self, nome: str) -> Produto | None: ...
    def contar(self) -> int: ...
    def criar(self, produto: Produto) -> Produto: ...
    def remover(self, produto: Produto) -> None: ...
```

O `Protocol` do capítulo @cap:heranca-e-protocolos escreve o contrato sem
exigir herança. Quem implementa não precisa saber que ele existe — e é isso
que vai permitir, no capítulo @cap:testando-services, trocar a
implementação de banco por uma de memória sem tocar em nada acima.

## A implementação

```python title="app/repositories/produto.py" numbered
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.produto import Produto


class ProdutoRepositorioSQL:
    def __init__(self, session: Session):
        self.session = session

    def buscar(self, produto_id: int) -> Produto | None:
        return self.session.get(Produto, produto_id)

    def buscar_por_nome(self, nome: str) -> Produto | None:
        stmt = select(Produto).where(Produto.nome == nome)
        return self.session.scalars(stmt).first()

    def listar(
        self, limite: int = 20, deslocamento: int = 0
    ) -> list[Produto]:
        stmt = (
            select(Produto)
            .order_by(Produto.nome)
            .limit(limite)
            .offset(deslocamento)
        )
        return list(self.session.scalars(stmt))

    def contar(self) -> int:
        return self.session.scalar(
            select(func.count()).select_from(Produto)
        ) or 0

    def criar(self, produto: Produto) -> Produto:
        self.session.add(produto)
        self.session.flush()
        return produto

    def remover(self, produto: Produto) -> None:
        self.session.delete(produto)
```

A sessão entra pelo construtor. O repositório não a cria, não a fecha e não
decide o tempo de vida dela — quem faz isso é a dependência do capítulo
@cap:dependency-injection, uma por requisição.

## Três coisas que o repositório não faz

**Não confirma a transação.** Não há `commit` em nenhum método. O
repositório não sabe se a operação dele é a última; quem sabe é o serviço.

**Não decide regra de negócio.** "Não pode haver dois produtos com o mesmo
nome" é regra, e mora no serviço. O repositório oferece `buscar_por_nome`
para que a regra possa ser conferida — a diferença entre oferecer a
informação e tomar a decisão.

**Não levanta exceção de domínio.** `buscar` devolve `None` quando não acha.
Transformar isso em `ProdutoNaoEncontrado` é decisão de quem pediu, e às
vezes não achar é o resultado desejado — numa verificação de duplicidade,
por exemplo.

:::key
Se você precisou importar `HTTPException` dentro do repositório, a camada
está errada. O repositório não sabe que existe HTTP, não sabe que existe
FastAPI e não sabe para que os dados vão ser usados. Essa ignorância é o
produto que ele entrega.
:::

## Não devolva `Query`, devolva dados

```python title="o_vazamento.py" numbered
def listar(self):
    return select(Produto)     # NÃO
```

Devolver uma consulta não executada parece flexível: quem chama refina como
quiser. Na prática, isso muda o repositório de lugar — ele deixa de ser uma
fronteira e passa a ser um gerador de fragmentos SQL que o serviço precisa
montar. A camada de cima passa a conhecer o ORM, e a substituição por uma
implementação em memória deixa de ser possível.

Repositório devolve **objetos do domínio**, ou listas deles, ou `None`.
Nunca consulta, nunca cursor, nunca sessão.

:::pitfall
O caso em que isso é tentador é a busca com muitos filtros opcionais. A
solução não é devolver a consulta, e sim aceitar os filtros como parâmetros
— que é exatamente o que o capítulo @cap:filtros-e-buscas faz, com um objeto
de filtro tipado.
:::

## A implementação em memória

```python title="app/repositories/memoria.py" numbered
class ProdutoRepositorioMemoria:
    def __init__(self):
        self._dados: dict[int, Produto] = {}
        self._proximo = 1

    def buscar(self, produto_id: int) -> Produto | None:
        return self._dados.get(produto_id)

    def buscar_por_nome(self, nome: str) -> Produto | None:
        for p in self._dados.values():
            if p.nome == nome:
                return p
        return None

    def listar(self, limite=20, deslocamento=0) -> list[Produto]:
        todos = sorted(self._dados.values(), key=lambda p: p.nome)
        return todos[deslocamento : deslocamento + limite]

    def criar(self, produto: Produto) -> Produto:
        produto.id = self._proximo
        self._dados[produto.id] = produto
        self._proximo += 1
        return produto

    def remover(self, produto: Produto) -> None:
        self._dados.pop(produto.id, None)
```

Trinta linhas, sem banco, sem transação, sem rede. Ela satisfaz o mesmo
protocolo — e é por isso que os testes de regra de negócio do capítulo
@cap:testando-services vão rodar em milissegundos, sem PostgreSQL instalado
na máquina de quem roda.

:::diagram type="blocks" caption="Duas implementações, um contrato: quem está acima não sabe a diferença."
rows:
  - [{ text: "Service", note: "as regras da cooperativa" }]
  - [{ text: "ProdutoRepositorio (Protocol)", note: "buscar · listar · criar · remover" }]
  - [{ text: "…SQL", note: "PostgreSQL, em produção" }, { text: "…Memória", note: "dicionário, em teste" }]
:::

:::story A pergunta que ninguém tinha feito
— Por que não chama o banco direto da rota? — perguntou Rafa. — São duas
linhas.

— São duas linhas agora.

Bia abriu o projeto antigo da cooperativa, o que rodava antes. Deu uma busca
por `SELECT`.

Cento e quarenta e sete resultados, em trinta e um arquivos.

— Quando a gente trocou o nome da coluna `preco_venda` para `preco`, eu levei
dois dias. E errei três lugares, que só apareceram em novembro.

Rafa olhou a lista rolando na tela.

— E com repositório?

— Com repositório o `SELECT` mora num arquivo só. Eu não fico mais esperta;
eu só fico com menos lugares para errar.
:::

## O custo honesto

Repositório acrescenta uma camada, e camada tem preço: mais arquivos, mais
indireção, mais código para uma consulta simples. Em um script de duzentas
linhas, ele é burocracia.

O que o justifica é a soma de três coisas: **um lugar só** onde o acesso a
dados mora, **um contrato** que permite trocar a implementação, e uma
camada de serviço que pode ser testada sem banco. Se o seu projeto não
precisa de nenhuma das três, não use.

:::summary
- O repositório é o único lugar do projeto que conhece o banco.
- O contrato vive num `Protocol`; a implementação não precisa herdar.
- A sessão entra pelo construtor; o tempo de vida dela é de quem chama.
- Repositório não confirma transação, não decide regra e não conhece HTTP.
- Devolve objetos, nunca consultas não executadas.
- A implementação em memória é o que torna o teste de regra instantâneo.
:::

:::exercise level=1
Escreva `ProdutorRepositorioSQL` com `buscar`, `buscar_por_email` e `criar`.

:::answer
```python
class ProdutorRepositorioSQL:
    def __init__(self, session: Session):
        self.session = session

    def buscar(self, produtor_id: int) -> Produtor | None:
        return self.session.get(Produtor, produtor_id)

    def buscar_por_email(self, email: str) -> Produtor | None:
        stmt = select(Produtor).where(Produtor.email == email)
        return self.session.scalars(stmt).first()

    def criar(self, produtor: Produtor) -> Produtor:
        self.session.add(produtor)
        self.session.flush()
        return produtor
```
:::

:::exercise level=2
Acrescente ao repositório de produtos um método `listar_por_categoria` que
aceite a categoria e devolva no máximo `limite` itens, ordenados por preço.

:::answer
```python
def listar_por_categoria(
    self, categoria: str, limite: int = 20
) -> list[Produto]:
    stmt = (
        select(Produto)
        .where(Produto.categoria == categoria)
        .order_by(Produto.preco)
        .limit(limite)
    )
    return list(self.session.scalars(stmt))
```
Um método por consulta é aceitável enquanto forem poucas. Quando virarem
seis variações da mesma busca com filtros diferentes, o desenho pede um
objeto de filtro — capítulo @cap:filtros-e-buscas.
:::

:::exercise level=2
O repositório precisa de um método `existe_com_nome(nome)` que responda
apenas verdadeiro ou falso. Escreva-o de forma que o banco não transporte a
linha inteira.

:::answer
```python
def existe_com_nome(self, nome: str) -> bool:
    stmt = select(
        select(Produto.id)
        .where(Produto.nome == nome)
        .exists()
    )
    return bool(self.session.scalar(stmt))
```
O `EXISTS` do SQL permite ao banco parar na primeira linha encontrada e não
devolve dado nenhum — só um booleano. `buscar_por_nome(...) is not None`
funciona e transporta o produto inteiro pela rede para depois jogá-lo fora.

Em tabela pequena, a diferença é imperceptível. A razão de escrever assim
desde o começo é outra: o método diz o que quer. Quem lê `existe_com_nome`
na camada de serviço entende a intenção sem abrir o repositório.
:::

:::exercise level=3
Um colega sugere que o método `criar` do repositório já faça `commit`,
argumentando que "é mais seguro, o dado fica salvo na hora". Escreva a
resposta, com um cenário concreto.

:::answer
O cenário: cadastrar um produto e, junto, o primeiro lote de estoque. São
duas escritas de uma operação só.

```python
produto = repo_produto.criar(produto)
repo_lote.criar(Lote(produto_id=produto.id, caixas=120))
```

Com `commit` dentro de `criar`, o produto já está gravado quando a segunda
linha roda. Se a segunda falhar — validação, chave estrangeira, queda de
conexão —, o banco fica com um produto sem lote. Nenhuma exceção aponta para
isso; o sistema simplesmente passa a ter um produto que ninguém cadastrou
inteiro.

E há um segundo efeito, menos visível: o `commit` devolve a conexão ao
estado inicial e encerra a transação. O `flush` seguinte abre **outra**. A
operação que parecia atômica virou duas, e o isolamento entre elas deixou de
existir.

A frase que resume: *quem abre a transação é quem fecha*. O repositório não
abriu nada — ele recebeu uma sessão pronta. Fechar o que não se abriu é a
definição de vazamento de responsabilidade.
:::
