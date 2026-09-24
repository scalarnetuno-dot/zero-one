---
title: "O CRUD completo"
number: 24
slug: o-crud-completo
part: p4
kicker: "As quatro camadas ligadas, as cinco rotas no ar, e o primeiro dia em que o dado sobrevive ao reinício."
goal: >-
  Ligar router, service, repository e modelo com o sistema de dependências do
  FastAPI, e ter o CRUD inteiro funcionando sobre PostgreSQL.
---

Agora as peças se encontram: router, service, repository e modelo deixam de
ser exemplos separados e passam a sustentar o catálogo de ponta a ponta.

## Como as peças se encontram

O router precisa de um serviço. O serviço precisa de um repositório e de uma
sessão. O repositório precisa da mesma sessão. Alguém tem de montar essa
corrente a cada requisição, e o FastAPI tem um mecanismo para isso.

```python title="app/dependencies.py" numbered
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.repositories.produto import ProdutoRepositorioSQL
from app.services.produto import ProdutoServico


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


SessaoDep = Annotated[Session, Depends(get_session)]


def get_produto_servico(session: SessaoDep) -> ProdutoServico:
    return ProdutoServico(session, ProdutoRepositorioSQL(session))


ServicoDep = Annotated[ProdutoServico, Depends(get_produto_servico)]
```

As duas últimas linhas de cada bloco são o truque que deixa as rotas
legíveis: `Annotated[Tipo, Depends(funcao)]` cria um **apelido de tipo** que
carrega a dependência junto. A rota passa a declarar só o apelido.

O mecanismo inteiro é o assunto do capítulo @cap:dependency-injection. Aqui
basta a forma.

## As rotas

```python title="app/routers/produtos.py" numbered
from fastapi import APIRouter, HTTPException, status

from app.dependencies import ServicoDep
from app.schemas.produto import ProdutoCriar, ProdutoLer
from app.services.produto import (
    EstoqueInsuficiente,
    ProdutoJaExiste,
    ProdutoNaoEncontrado,
)

router = APIRouter(prefix="/produtos", tags=["produtos"])


@router.get("", response_model=list[ProdutoLer])
def listar(servico: ServicoDep, limite: int = 20, pagina: int = 1):
    return servico.listar(limite=limite, pagina=pagina)


@router.get("/{produto_id}", response_model=ProdutoLer)
def buscar(produto_id: int, servico: ServicoDep):
    try:
        return servico.buscar(produto_id)
    except ProdutoNaoEncontrado as erro:
        raise HTTPException(404, str(erro)) from erro


@router.post(
    "", response_model=ProdutoLer, status_code=status.HTTP_201_CREATED
)
def criar(dados: ProdutoCriar, servico: ServicoDep):
    try:
        return servico.criar(
            dados.nome, dados.preco, dados.estoque
        )
    except ProdutoJaExiste as erro:
        raise HTTPException(409, str(erro)) from erro


@router.put("/{produto_id}", response_model=ProdutoLer)
def atualizar(
    produto_id: int, dados: ProdutoCriar, servico: ServicoDep
):
    try:
        return servico.atualizar(produto_id, dados)
    except ProdutoNaoEncontrado as erro:
        raise HTTPException(404, str(erro)) from erro
    except ProdutoJaExiste as erro:
        raise HTTPException(409, str(erro)) from erro


@router.delete("/{produto_id}", status_code=204)
def apagar(produto_id: int, servico: ServicoDep):
    try:
        servico.apagar(produto_id)
    except ProdutoNaoEncontrado as erro:
        raise HTTPException(404, str(erro)) from erro
```

Compare com o capítulo @cap:primeira-api. Sumiram a lista global, o `for`, o
`_proximo_id` e o `global`. Cada rota agora faz três coisas: receber, chamar,
traduzir erro.

:::pitfall
Esses cinco blocos `try` são repetição, e repetição é sintoma. Escrevê-los
uma vez é aceitável; escrevê-los em cada router do projeto, não. O capítulo
@cap:tratamento-de-erros troca os cinco por um tratador registrado uma vez,
e as rotas ficam com uma linha de corpo.
:::

## O que faltava no serviço

```python title="app/services/produto.py" numbered
    def listar(
        self, limite: int = 20, pagina: int = 1
    ) -> list[Produto]:
        limite = max(1, min(limite, 100))
        pagina = max(1, pagina)
        return self.repo.listar(
            limite=limite, deslocamento=(pagina - 1) * limite
        )

    def atualizar(
        self, produto_id: int, dados: ProdutoCriar
    ) -> Produto:
        produto = self.buscar(produto_id)

        existente = self.repo.buscar_por_nome(dados.nome)
        if existente is not None and existente.id != produto.id:
            raise ProdutoJaExiste(dados.nome)

        produto.nome = dados.nome
        produto.preco = dados.preco
        produto.estoque = dados.estoque
        self.session.commit()
        return produto

    def apagar(self, produto_id: int) -> None:
        produto = self.buscar(produto_id)
        self.repo.remover(produto)
        self.session.commit()
```

Duas decisões merecem destaque.

O `min(limite, 100)` é um **teto imposto pelo servidor**. Sem ele, um
cliente pede `?limite=999999` e a sua API tenta carregar a tabela inteira na
memória — uma negação de serviço que você mesmo publicou. O capítulo
@cap:paginacao formaliza isso.

E o `existente.id != produto.id` em `atualizar` é o detalhe que quase todo
mundo esquece: sem ele, salvar um produto **sem mudar o nome** dispara
"produto já cadastrado", porque o produto encontrado é ele mesmo.

## O esquema de saída

```python title="app/schemas/produto.py" numbered
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ProdutoCriar(BaseModel):
    nome: Annotated[str, Field(min_length=2, max_length=120)]
    preco: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    estoque: Annotated[int, Field(ge=0)] = 0


class ProdutoLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco: Decimal
    estoque: int
    ativo: bool
    criado_em: datetime
```

O `from_attributes=True` é o que permite ao FastAPI converter o objeto
`Produto` do SQLAlchemy — que tem atributos, não chaves — no JSON da
resposta.

## Criando as tabelas e subindo

```python title="app/main.py" numbered
from app.database import Base, engine
from app.models import produto as _  # registra o modelo

Base.metadata.create_all(engine)
```

:::warning
Esse `create_all` no `main` serve para ver a tabela nascer hoje. Ele não
serve para produção: roda a cada partida e não altera tabela que já existe.
Mudança de tabela pede migração com histórico — um arquivo que diz o que
mudou e pode ser desfeito —, não um create escondido na subida do servidor.
:::

```text
$ fastapi dev app/main.py
```

## O passeio completo

:::http title="1. Criar"
POST /produtos
Content-Type: application/json

{"nome": "Tomate italiano", "preco": "8.90", "estoque": 120}
---
201 Created

{
  "id": 1,
  "nome": "Tomate italiano",
  "preco": "8.90",
  "estoque": 120,
  "ativo": true,
  "criado_em": "2026-03-14T18:22:41.102Z"
}
:::

:::http title="2. Criar de novo, com o mesmo nome"
POST /produtos
Content-Type: application/json

{"nome": "Tomate italiano", "preco": "9.10"}
---
409 Conflict

{"detail": "produto 'Tomate italiano' já cadastrado"}
:::

:::http title="3. Buscar o que não existe"
GET /produtos/999
---
404 Not Found

{"detail": "produto 999 não encontrado"}
:::

:::http title="4. Apagar"
DELETE /produtos/1
---
204 No Content
:::

Repare no `"preco": "8.90"` — texto, entre aspas. O `Decimal` viaja como
string em JSON, de propósito: o tipo `number` do JSON é ponto flutuante, e
mandar `8.90` como número desfaria toda a precisão que o `NUMERIC` do banco
garantiu. É feio na primeira vez e é a decisão correta.

:::practice
Reinicie o servidor e chame `GET /produtos`. Os produtos continuam lá. É a
primeira vez no livro que isso acontece, e vale parar um instante nessa
diferença: o programa deixou de ser uma sessão e passou a ser um sistema.
:::

:::story A primeira vez que alguém de fora usou
Dona Neuza cadastrou três produtos pelo `/docs`, sem que ninguém explicasse
como.

— Esse botão azul aí embaixo é o que manda? — perguntou.

— É.

Ela clicou. Apareceu o `201` e o produto de volta, com um número na frente.

— E esse número?

— É o código que o sistema deu. Dali em diante, ele é esse produto.

Dona Neuza olhou para a tela por um tempo. Depois abriu a planilha, na aba
de novembro, e comparou.

— Aqui ele é a linha 47 — ela disse. — Mas se eu apagar a linha 12, ele vira
a 46.

— No sistema ele continua sendo o 3.

— Ah. — Ela fechou a planilha. — Então é isso que vocês estavam tentando
fazer esse tempo todo.
:::

:::summary
- `Annotated[Tipo, Depends(f)]` cria um apelido que carrega a dependência.
- Uma sessão por requisição, com `rollback` quando a exceção escapa.
- Teto de página imposto pelo servidor, não pelo cliente.
- Na atualização, a checagem de nome duplicado precisa ignorar o próprio
  registro.
- `from_attributes=True` converte objeto do ORM em resposta.
- `Decimal` viaja como texto em JSON, e isso é proposital.
:::

:::milestone
O CRUD está completo, com banco, camadas e validação. A partir daqui o livro
para de construir o esqueleto e passa a tratar do que separa um CRUD de
exercício de uma API que outra pessoa usa.
:::

:::exercise level=1
Acrescente uma rota `PATCH /produtos/{id}/estoque` que receba
`{"caixas": 30}` e chame `servico.repor`.

:::answer
```python
class ReposicaoEntrada(BaseModel):
    caixas: Annotated[int, Field(gt=0)]


@router.patch("/{produto_id}/estoque", response_model=ProdutoLer)
def repor(
    produto_id: int, dados: ReposicaoEntrada, servico: ServicoDep
):
    try:
        return servico.repor(produto_id, dados.caixas)
    except ProdutoNaoEncontrado as erro:
        raise HTTPException(404, str(erro)) from erro
```
O `gt=0` no esquema tira do serviço a validação de quantidade — mas não
completamente: o serviço continua precisando dela, porque ele também é
chamado por scripts que não passam pelo Pydantic.
:::

:::exercise level=2
Monte o `ProdutorServico` e o router de produtores, com criação e busca,
recusando e-mail repetido com `409`.

:::answer
```python
class ProdutorServico:
    def __init__(self, session, repo):
        self.session = session
        self.repo = repo

    def criar(self, dados: ProdutorCriar) -> Produtor:
        if self.repo.buscar_por_email(dados.email):
            raise ProdutorJaExiste(dados.email)
        produtor = Produtor(**dados.model_dump())
        self.repo.criar(produtor)
        self.session.commit()
        return produtor
```
`Produtor(**dados.model_dump())` expande o dicionário em argumentos
nomeados. É conciso e tem um risco: se o esquema ganhar um campo que o
modelo não tem, o erro aparece só em execução. Em projeto grande, vale
escrever os campos.
:::

:::exercise level=3
Duas requisições `POST /produtos` com o mesmo nome chegam no mesmo
milissegundo. O serviço confere duplicidade antes de inserir. Descreva o que
acontece, e escreva a correção completa.

:::answer
As duas consultas de verificação rodam antes de qualquer inserção. As duas
não encontram nada. As duas inserem. O resultado depende do banco: sem
restrição `UNIQUE`, ficam dois produtos com o mesmo nome; com a restrição, a
segunda transação falha com `IntegrityError` e o cliente recebe `500` — a
API culpando a si mesma por um conflito que ela sabe explicar.

A correção tem duas metades, e nenhuma das duas basta sozinha.

No banco:

```python
nome: Mapped[str] = mapped_column(String(120), unique=True)
```

No serviço:

```python
def criar(self, nome, preco, estoque) -> Produto:
    nome = " ".join(nome.split())
    if self.repo.buscar_por_nome(nome) is not None:
        raise ProdutoJaExiste(nome)

    produto = Produto(nome=nome, preco=preco, estoque=estoque)
    try:
        self.repo.criar(produto)
        self.session.commit()
    except IntegrityError as erro:
        self.session.rollback()
        raise ProdutoJaExiste(nome) from erro
    return produto
```

A verificação inicial atende o caso comum com uma mensagem boa e sem custo
de transação abortada. O `try` atende a corrida rara, converte o erro técnico
na mesma exceção de domínio, e o cliente recebe `409` nos dois caminhos — sem
saber qual dos dois aconteceu, que é exatamente o que se quer.

O `rollback` antes de relançar não é opcional: depois de um `IntegrityError`,
a transação fica inutilizável, e qualquer comando seguinte na mesma sessão
falha com uma mensagem que não tem nada a ver com o problema original.
:::
