---
title: "Modelando com Pydantic"
number: 18
slug: modelando-com-pydantic
part: p3
kicker: "A mesma classe que descreve o dado também o recusa quando ele chega errado."
goal: >-
  Substituir `dict` por modelos Pydantic, validar entrada com tipos e
  restrições, escrever validadores próprios e entender o que muda na
  documentação e nas mensagens de erro.
---

O capítulo anterior terminou com uma rota que aceita qualquer coisa:

```python
@router.post("")
def criar(produto: dict):
    ...
```

Troque `dict` por uma classe e a API inteira muda de qualidade — sem que
nenhuma outra linha se mexa.

```python title="app/schemas/produto.py" numbered
from decimal import Decimal

from pydantic import BaseModel


class ProdutoCriar(BaseModel):
    nome: str
    preco: Decimal
    estoque: int = 0
```

```python title="app/routers/produtos.py" numbered
@router.post("", status_code=201)
def criar(produto: ProdutoCriar):
    ...
```

## O que aconteceu

```python title="o_teste.py" numbered
ProdutoCriar(nome="Tomate", preco="8.90")
```

```text
ProdutoCriar(nome='Tomate', preco=Decimal('8.90'), estoque=0)
```

Repare no `preco`: entrou texto, saiu `Decimal`. O Pydantic **converte**
quando a conversão é segura — e recusa quando não é:

```text
>>> ProdutoCriar(nome="Tomate", preco="muito caro")
pydantic_core.ValidationError: 1 validation error for ProdutoCriar
preco
  Input should be a valid decimal
  [type=decimal_parsing, input_value='muito caro']
```

A diferença para a `dataclass` do capítulo @cap:tipagem-e-dataclasses é
exatamente esta: lá a anotação era metadado inerte; aqui ela é executada.

:::key
Pydantic é a `dataclass` que leva as anotações a sério. Mesma cara, mesmo
jeito de declarar, e três serviços a mais: **valida**, **converte** e
**descreve** — este último gerando o esquema JSON que alimenta a
documentação.
:::

## A resposta que o cliente recebe

Com o modelo no lugar, um corpo inválido não chega na sua função:

:::http title="Erro de validação, sem uma linha escrita por você"
POST /produtos
Content-Type: application/json

{"preco": "muito caro"}
---
422 Unprocessable Entity

{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "nome"],
      "msg": "Field required"
    },
    {
      "type": "decimal_parsing",
      "loc": ["body", "preco"],
      "msg": "Input should be a valid decimal"
    }
  ]
}
:::

Dois detalhes que valem ouro em uma API de verdade. Os erros vêm **todos de
uma vez**, e não um por requisição — quem preenche um formulário vê os três
campos errados juntos. E cada erro tem `loc`, o caminho exato até o campo,
o que permite ao cliente destacar o campo certo na tela.

## Restrições nos tipos

Tipo certo não é o mesmo que valor aceitável. Preço `-5` é um `Decimal`
perfeitamente válido.

```python title="restricoes.py" numbered
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field


class ProdutoCriar(BaseModel):
    nome: Annotated[str, Field(min_length=2, max_length=120)]
    preco: Annotated[Decimal, Field(gt=0, decimal_places=2)]
    estoque: Annotated[int, Field(ge=0)] = 0
```

| Restrição | Significa |
|---|---|
| `gt` / `ge` | maior que / maior ou igual |
| `lt` / `le` | menor que / menor ou igual |
| `min_length` / `max_length` | tamanho de texto ou lista |
| `pattern` | expressão regular |
| `decimal_places` | casas decimais de um `Decimal` |

Tabela: Escritas no tipo, essas regras aparecem na documentação e na
mensagem de erro automaticamente.

:::pitfall
Existem duas formas de escrever isso: `Annotated[Decimal, Field(gt=0)]` e
`preco: Decimal = Field(gt=0)`. As duas funcionam. A segunda ocupa o lugar
do valor padrão, o que gera confusão na hora de dar um padrão de verdade e
não sobrevive bem a campos opcionais. Use `Annotated` — é a forma
recomendada e a única que se combina com dependências no capítulo
@cap:dependency-injection.
:::

## Tipos que carregam regra

```python title="tipos_ricos.py" numbered
from datetime import date

from pydantic import BaseModel, EmailStr, HttpUrl


class Produtor(BaseModel):
    nome: str
    email: EmailStr
    site: HttpUrl | None = None
    desde: date
```

`EmailStr` valida o formato do e-mail de verdade — e substitui aquele
`"@" in valor` do capítulo @cap:encapsulamento, que aceitava `"@"` sozinho.
`HttpUrl` exige esquema e domínio. `date` aceita `"2026-03-14"` e recusa
`"14/03/2026"`, porque o padrão de data em JSON é o ISO 8601 e não o
brasileiro.

:::warning
`EmailStr` exige uma dependência extra: `pip install "pydantic[email]"`. Sem
ela, o erro aparece na importação do módulo, com uma mensagem clara — e é o
tipo de falha que quebra o servidor em produção se o `requirements.txt` foi
montado à mão.
:::

## Validador próprio

Quando a regra não cabe numa restrição:

```python title="validador.py" numbered
from pydantic import BaseModel, field_validator, model_validator


class ProdutoCriar(BaseModel):
    nome: str
    preco: Decimal
    preco_promocional: Decimal | None = None

    @field_validator("nome")
    @classmethod
    def nome_sem_espaco_sobrando(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("nome muito curto")
        return v

    @model_validator(mode="after")
    def promocao_menor_que_preco(self):
        if self.preco_promocional is None:
            return self
        if self.preco_promocional >= self.preco:
            raise ValueError("promoção precisa ser menor que o preço")
        return self
```

A diferença entre os dois é o alcance. `field_validator` vê **um campo** e
pode transformá-lo — repare que ele devolve o valor limpo, e essa limpeza
vale para todo o resto do programa. `model_validator(mode="after")` vê o
**objeto inteiro**, já validado campo a campo, e é o único lugar onde se
pode comparar dois campos entre si.

:::key
Levante `ValueError` dentro do validador, não `HTTPException`. O Pydantic
captura o `ValueError` e o transforma em item da lista de erros `422`, com
`loc` correto. Um `HTTPException` aí dentro atravessa a validação e produz
uma resposta sem o campo que falhou — perdendo justamente a informação mais
útil.
:::

## Entrada e saída são modelos diferentes

Esta é a decisão que evita o vazamento mais comum de API:

```python title="app/schemas/produto.py" numbered
class ProdutoCriar(BaseModel):
    nome: str
    preco: Decimal
    estoque: int = 0


class ProdutoLer(BaseModel):
    id: int
    nome: str
    preco: Decimal
    estoque: int
    criado_em: datetime
```

`ProdutoCriar` não tem `id` — quem cria não escolhe o identificador. E
`ProdutoLer` tem `criado_em`, que ninguém envia.

```python title="response_model" numbered
@router.post("", response_model=ProdutoLer, status_code=201)
def criar(dados: ProdutoCriar):
    ...


@router.get("", response_model=list[ProdutoLer])
def listar():
    ...
```

O `response_model` faz duas coisas: descreve a resposta na documentação e
**filtra** o que sai. Se a função devolver um objeto com campos a mais — uma
senha, um custo interno, um campo de auditoria —, eles não atravessam.

:::warning
Sem `response_model`, a resposta é o que a função devolver, inteiro. No dia
em que a tabela `produto` ganhar uma coluna `custo_de_compra`, ela aparece
na API pública sem que ninguém tenha decidido isso. Esse é o argumento
inteiro a favor de escrever o modelo de saída, e o capítulo @cap:schemas
volta a ele.
:::

## Convertendo objetos do banco

```python title="from_attributes.py" numbered
class ProdutoLer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco: Decimal
```

Por padrão, o Pydantic lê dicionários. `from_attributes=True` faz ele ler
também **atributos de objeto** — que é o formato em que o SQLAlchemy vai
devolver os dados a partir do capítulo @cap:sqlalchemy. Sem essa linha, o
erro é `Input should be a valid dictionary`, e é uma das primeiras pedras do
caminho.

## Apelidos: quando o JSON não fala a sua língua

```python title="alias.py" numbered
class ProdutoLer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    criado_em: datetime = Field(alias="createdAt")
```

O Python usa `snake_case`; muita API pública usa `camelCase`. O apelido
separa as duas convenções: o atributo continua `criado_em` no seu código e
vira `createdAt` no JSON.

:::trivia
O Pydantic v2, lançado em 2023, reescreveu o núcleo de validação em Rust. A
diferença não é cosmética: o ganho medido ficou entre cinco e cinquenta vezes
dependendo do modelo. A consequência prática para quem escreve é que
validar deixou de ser uma decisão de desempenho — você pode validar na
entrada, na saída e entre camadas sem que isso apareça no tempo de resposta.
:::

## Serializar

```text
>>> p = ProdutoLer(id=1, nome="Tomate", preco=Decimal("8.90"))
>>> p.model_dump()
{'id': 1, 'nome': 'Tomate', 'preco': Decimal('8.90')}
>>> p.model_dump(mode="json")
{'id': 1, 'nome': 'Tomate', 'preco': '8.90'}
>>> p.model_dump_json()
'{"id":1,"nome":"Tomate","preco":"8.90"}'
```

A diferença entre as duas primeiras é sutil e importa: `model_dump()`
devolve objetos Python, com `Decimal` e `datetime` de verdade;
`mode="json"` devolve apenas tipos que o JSON conhece. Para gravar em banco,
a primeira; para mandar pela rede, a segunda.

:::summary
- Pydantic executa as anotações: valida, converte e descreve.
- Erros de validação vêm todos juntos, com o caminho até o campo.
- `Annotated[T, Field(...)]` é a forma recomendada de restringir.
- `field_validator` vê um campo; `model_validator(mode="after")` vê o objeto.
- Dentro de validador, levante `ValueError`, nunca `HTTPException`.
- Modelo de entrada e de saída são diferentes — e `response_model` filtra o
  que sai.
- `from_attributes=True` é o que permite ler objetos do ORM.
:::

:::checkpoint
Você substitui `dict` por modelos, restringe valores com `Field`, escreve
validadores próprios e sabe por que a API tem dois modelos para a mesma
tabela.
:::

:::exercise level=1
Escreva o modelo `ProdutorCriar` com `nome` (2 a 100 caracteres), `email`
validado e `cidade` obrigatória.

:::answer
```python
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field


class ProdutorCriar(BaseModel):
    nome: Annotated[str, Field(min_length=2, max_length=100)]
    email: EmailStr
    cidade: Annotated[str, Field(min_length=2)]
```
:::

:::exercise level=2
Acrescente ao `ProdutoCriar` um campo `categoria` que só aceite `"fruta"`,
`"legume"` ou `"verdura"`, e faça a documentação mostrar as três opções.

:::answer
```python
from enum import Enum


class Categoria(str, Enum):
    FRUTA = "fruta"
    LEGUME = "legume"
    VERDURA = "verdura"


class ProdutoCriar(BaseModel):
    nome: str
    categoria: Categoria
```
O `Enum` do capítulo @cap:tipagem-e-dataclasses aparece na documentação como
uma lista fechada, e o `/docs` desenha um menu suspenso. Um `Literal["fruta",
"legume", "verdura"]` faria o mesmo e não teria nome para reaproveitar — o
`Enum` ganha porque o mesmo tipo vai para o banco no capítulo
@cap:sqlalchemy.
:::

:::exercise level=3
Um colega propõe usar o **mesmo** modelo para entrada e saída, argumentando
que são os mesmos campos e que dois modelos é repetição. Responda listando
três situações concretas em que a proposta quebra.

:::answer
**Primeira: o `id`.** Na saída ele é obrigatório; na entrada ele não deveria
existir. Com um modelo só, ou o `id` é opcional na saída — e o cliente
precisa tratar a ausência de algo que sempre vem — ou é obrigatório na
entrada, e a API aceita que o cliente escolha o próprio identificador.

**Segunda: o campo que só entra.** Senha, token de confirmação, aceite de
termos. Com um modelo só, eles voltam na resposta. Uma senha ecoada na
resposta de cadastro é um incidente de segurança, e já aconteceu em APIs
grandes exatamente assim.

**Terceira: o campo que só sai.** `criado_em`, `atualizado_em`, campos
calculados. Eles precisariam ser opcionais na entrada, e aí nada impede que
um cliente mande `criado_em` e reescreva a auditoria.

E um argumento de fundo, que vale mais que os três: entrada e saída mudam por
razões diferentes e em ritmos diferentes. Acrescentar um campo interno é uma
mudança de banco; acrescentar um campo na resposta é uma mudança de contrato
público. Um modelo só amarra as duas — e faz uma migração de banco virar,
sem ninguém perceber, uma alteração de API.
:::
