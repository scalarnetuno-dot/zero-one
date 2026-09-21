---
title: "Esquemas"
number: 24
slug: schemas
part: p5
kicker: "O esquema é o contrato público. A tabela é assunto interno — e confundir os dois é publicar o seu banco."
goal: >-
  Desenhar os esquemas de entrada, saída e alteração parcial; distinguir
  campo ausente de campo nulo; e manter o contrato estável enquanto o modelo
  muda.
---

O capítulo @cap:modelando-com-pydantic introduziu os modelos; o
@cap:o-crud-completo os usou. Agora vale tratá-los como o que eles são: o
**contrato público** da sua API, a única parte do sistema que outras pessoas
programam em cima.

Contrato tem uma propriedade desconfortável: quebrar um custa caro para quem
não tem culpa.

## A família de esquemas

Uma entidade costuma precisar de três a quatro esquemas, e o desenho que
evita repetição é este:

```python title="app/schemas/produto.py" numbered
class ProdutoBase(BaseModel):
    nome: Annotated[str, Field(min_length=2, max_length=120)]
    preco: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    estoque: Annotated[int, Field(ge=0)] = 0


class ProdutoCriar(ProdutoBase):
    pass


class ProdutoAtualizar(BaseModel):
    nome: Annotated[str | None, Field(min_length=2)] = None
    preco: Annotated[Decimal | None, Field(gt=0)] = None
    estoque: Annotated[int | None, Field(ge=0)] = None


class ProdutoLer(ProdutoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ativo: bool
    criado_em: datetime
```

| Esquema | Para quê | Quem preenche |
|---|---|---|
| `ProdutoBase` | os campos comuns | ninguém, é só herança |
| `ProdutoCriar` | corpo do `POST` | o cliente |
| `ProdutoAtualizar` | corpo do `PATCH` | o cliente, em parte |
| `ProdutoLer` | corpo da resposta | o servidor |

Tabela: Quatro classes para uma tabela parece exagero até a primeira vez em
que a tabela ganha uma coluna que não pode aparecer na resposta.

:::pitfall
Herdar `ProdutoLer` de `ProdutoBase` é conveniente e tem um risco: qualquer
campo acrescentado à base entra automaticamente na resposta. Num projeto em
que a base representa "o que o cliente envia", isso é seguro. Se a base
começar a acumular campos internos, quebre a herança — conveniência não
justifica vazamento.
:::

## Ausente e nulo não são a mesma coisa

Esta é a distinção que faz o `PATCH` funcionar de verdade.

```text
PATCH /produtos/1
{"preco": "9.50"}            → mude só o preço

PATCH /produtos/1
{"categoria": null}          → apague a categoria

PATCH /produtos/1
{}                           → não mude nada
```

Nos três casos, o campo `categoria` do modelo Python vale `None`. O que
distingue o segundo do primeiro não é o valor: é **ter vindo ou não**.

```python title="exclude_unset.py" numbered
@router.patch("/{produto_id}", response_model=ProdutoLer)
def alterar(
    produto_id: int, dados: ProdutoAtualizar, servico: ServicoDep
):
    campos = dados.model_dump(exclude_unset=True)
    return servico.alterar(produto_id, campos)
```

`exclude_unset=True` devolve **apenas os campos que o cliente enviou**. O
que não veio não aparece no dicionário, e o serviço só altera o que está
lá:

```python title="app/services/produto.py" numbered
def alterar(self, produto_id: int, campos: dict) -> Produto:
    produto = self.buscar(produto_id)

    for campo, valor in campos.items():
        setattr(produto, campo, valor)

    self.session.commit()
    return produto
```

:::key
Sem `exclude_unset`, um `PATCH` com só o preço manda `nome=None` junto — e
apaga o nome do produto. Esse é o defeito mais comum de `PATCH` em API
Python, e ele não dá erro: ele grava.
:::

:::warning
O `setattr` em laço aceita qualquer campo que estiver no dicionário. Como o
dicionário veio de um esquema com campos fixos, isso é seguro **aqui**. Se
algum dia o corpo virar `dict` cru, esse mesmo laço deixa um cliente
escrever em `id`, `criado_em` ou qualquer atributo do modelo. Mantenha o
esquema tipado entre os dois.
:::

## Esquemas aninhados

```python title="aninhado.py" numbered
class ProdutorResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cidade: str


class ProdutoLer(ProdutoBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
    produtor: ProdutorResumo
```

:::http title="A resposta com o produtor embutido"
GET /produtos/1
---
200 OK

{
  "id": 1,
  "nome": "Tomate italiano",
  "preco": "8.90",
  "produtor": {
    "id": 7,
    "nome": "Seu Onofre",
    "cidade": "Ibiúna"
  }
}
:::

Repare no nome `ProdutorResumo`. Embutir o esquema **completo** do produtor
dentro do produto acopla os dois contratos: um campo novo em `ProdutorLer`
aparece, sem aviso, dentro de toda listagem de produtos. Um esquema de
resumo, com os três campos que fazem sentido ali, é uma decisão explícita.

:::pitfall
Esquema aninhado é a porta de entrada do problema N+1 do capítulo
@cap:relacionamentos: listar cem produtos com o produtor embutido dispara
cem consultas se o carregamento não for preparado. O esquema não causa o
problema — ele o torna invisível, que é pior.
:::

## Apelidos e convenções de nome

```python title="alias.py" numbered
from pydantic.alias_generators import to_camel


class RespostaBase(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
```

Todo esquema que herdar dessa base passa a publicar `criadoEm` em vez de
`criado_em`, sem mudar uma linha do código Python. `populate_by_name=True`
mantém os dois nomes aceitos na entrada — o que evita quebrar clientes
antigos durante uma migração.

:::key
Escolha a convenção **antes** do primeiro cliente e não mude mais. Trocar
`snake_case` por `camelCase` depois é quebrar o contrato de todo mundo de
uma vez. Se já é tarde, `populate_by_name` permite aceitar os dois na
entrada por um tempo — mas a saída só pode ter um.
:::

## Exemplos na documentação

```python title="exemplos.py" numbered
class ProdutoCriar(ProdutoBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nome": "Tomate italiano",
                    "preco": "8.90",
                    "estoque": 120,
                }
            ]
        }
    )
```

O `/docs` passa a mostrar esse corpo preenchido no botão **Try it out**.
Custa cinco linhas e economiza, em cada integração nova, a pergunta "mas o
que exatamente eu mando aqui?".

## O que quebra um contrato

| Mudança | Quebra? |
|---|---|
| acrescentar campo na resposta | não, se o cliente ignorar desconhecidos |
| remover campo da resposta | **sim** |
| renomear campo | **sim** |
| tornar obrigatório um campo opcional da entrada | **sim** |
| tornar opcional um campo obrigatório da entrada | não |
| acrescentar valor a um `Enum` de resposta | **sim**, na prática |

Tabela: A última linha surpreende: um cliente que faz `match` sobre os
valores conhecidos quebra ao receber um valor novo.

:::story O campo que ninguém usava
— Ninguém usa `preco_antigo` — disse Rafa. — Está `null` em noventa e oito
por cento das linhas. Posso tirar da resposta?

— Quem consome a API hoje?

— O app dos produtores e... o painel da contabilidade.

— Pergunta para os dois.

O app não usava. A contabilidade usava — uma vez por mês, na conferência de
reajuste, num relatório que uma pessoa rodava à mão e que ninguém no time de
desenvolvimento sabia que existia.

— Se eu tivesse tirado — disse Rafa —, o que ia acontecer?

— O relatório sairia com a coluna vazia. Sem erro nenhum. — Bia fechou o
editor. — E alguém ia descobrir em dezembro.
:::

:::summary
- O esquema é o contrato público; a tabela é assunto interno.
- Entrada, alteração parcial e saída são esquemas diferentes.
- `exclude_unset=True` distingue campo ausente de campo nulo — é o que faz
  o `PATCH` funcionar.
- Esquema aninhado usa um resumo, não o esquema completo do outro recurso.
- Apelidos separam a convenção do Python da convenção do JSON.
- Remover ou renomear campo quebra contrato; acrescentar valor a um `Enum`
  também.
:::

:::exercise level=1
Escreva `ProdutorAtualizar` com todos os campos opcionais e a rota `PATCH`
usando `exclude_unset`.

:::answer
```python
class ProdutorAtualizar(BaseModel):
    nome: str | None = None
    cidade: str | None = None
    email: EmailStr | None = None


@router.patch("/{produtor_id}", response_model=ProdutorLer)
def alterar(
    produtor_id: int,
    dados: ProdutorAtualizar,
    servico: ProdutorServicoDep,
):
    return servico.alterar(
        produtor_id, dados.model_dump(exclude_unset=True)
    )
```
:::

:::exercise level=1
Escreva o esquema de resposta de uma operação de conferência que devolva
apenas `id`, `status` e `conferida_em` — nada mais, mesmo que o objeto
tenha vinte campos.

:::answer
```python
class EntregaConferida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: StatusEntrega
    conferida_em: datetime
```
Um esquema por resposta, e não um por entidade, é o que permite que a mesma
tabela tenha superfícies diferentes em rotas diferentes. O custo é uma
classe pequena; o ganho é que acrescentar coluna nunca muda uma resposta
sem que alguém decida.
:::

:::exercise level=2
Crie um esquema `ProdutoLerPublico` que **não** inclua `custo` nem
`margem` — campos que existem no modelo e não podem sair da empresa.

:::answer
```python
class ProdutoLerPublico(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco: Decimal
    estoque: int


@router.get("/publico", response_model=list[ProdutoLerPublico])
def listar_publico(servico: ServicoDep):
    return servico.listar()
```
O `response_model` filtra: mesmo que `servico.listar()` devolva objetos com
`custo` e `margem`, os dois não atravessam. Essa é a diferença entre
esquecer de tirar um campo e não ter como deixá-lo passar.
:::

:::exercise level=3
Sua API está em produção há um ano, com quatro clientes. O time precisa
renomear `estoque` para `quantidade_disponivel`, porque o nome atual gera
confusão com o estoque do armazém. Proponha o plano.

:::answer
Renomear de uma vez quebra os quatro. O plano em quatro etapas, que leva
semanas e não derruba ninguém:

**1. Publicar os dois.** A resposta passa a trazer `estoque` **e**
`quantidade_disponivel`, com o mesmo valor. Na entrada, os dois são aceitos,
com o antigo tendo precedência se ambos vierem. Nenhum cliente muda nada.

```python
class ProdutoLer(BaseModel):
    quantidade_disponivel: int

    @computed_field
    @property
    def estoque(self) -> int:
        return self.quantidade_disponivel
```

**2. Avisar e marcar.** O campo antigo vira `deprecated` na documentação,
com uma data. Os quatro clientes recebem aviso por escrito, com a data e o
que precisa mudar.

**3. Medir.** Registre no log toda requisição que ainda **envia** `estoque`.
Sem essa medição, a etapa 4 é um chute — e a pergunta "alguém ainda usa?" foi
exatamente a que a história mostrou não se responder por
intuição.

**4. Remover**, quando o log estiver zerado por um período combinado, e não
antes da data anunciada.

Se o prazo for curto demais para isso, a alternativa é versionar: `/v2` com
o nome novo, `/v1` congelado. É mais caro de manter — duas superfícies, dois
conjuntos de teste — e é a saída quando a mudança é grande demais para caber
numa transição por campo.
:::
