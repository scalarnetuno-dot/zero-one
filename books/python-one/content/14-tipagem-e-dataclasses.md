---
title: "Tipagem e dataclasses"
number: 14
slug: tipagem-e-dataclasses
part: p2
kicker: "O Python ignora as anotações de tipo em execução. Quase tudo o mais no seu projeto, não."
goal: >-
  Anotar tipos com precisão, criar tipos de dado com `dataclass` e `Enum`, e
  entender por que o FastAPI consegue validar uma requisição lendo apenas a
  assinatura de uma função.
---

Este é o capítulo que faz o resto do livro funcionar. Tudo que o FastAPI tem
de notável — validação automática, conversão de JSON, documentação gerada —
vem de uma decisão só: **ler as anotações de tipo que você escreveu e agir
sobre elas**.

Então vale entender o que exatamente essas anotações são, e o que elas não
são.

## O que a anotação faz e o que não faz

```python title="anotado.py" numbered
def com_margem(preco: float, taxa: float = 0.12) -> float:
    return preco * (1 + taxa)


print(com_margem("oito reais"))
```

```text
Traceback (most recent call last):
  File "anotado.py", line 5, in <module>
    print(com_margem("oito reais"))
  File "anotado.py", line 2, in com_margem
    return preco * (1 + taxa)
TypeError: can't multiply sequence by non-int of type 'float'
```

Repare no erro: ele **não** diz "esperava float e recebeu str". A anotação
não foi conferida. O programa rodou, entrou na função e quebrou lá dentro,
no mesmo lugar em que quebraria sem anotação nenhuma.

:::key
Anotação de tipo em Python não valida, não converte e não recusa nada em
execução. Ela é **metadado**, guardado em `__annotations__` e disponível
para quem quiser ler: o seu editor, o verificador de tipos, e bibliotecas
como o Pydantic e o FastAPI, que leem e agem.
:::

Isso soa como pouco, e é o contrário. Significa que a mesma anotação serve
para três públicos diferentes sem custo de execução — e que uma biblioteca
pode decidir levá-la a sério onde a linguagem não leva.

## A gramática dos tipos

```python title="tipos.py" numbered
nome: str = "Tomate"
preco: float = 8.90
ativo: bool = True

nomes: list[str] = ["Tomate", "Alface"]
precos: dict[str, float] = {"Tomate": 8.90}
par: tuple[str, int] = ("Tomate", 120)

categoria: str | None = None
```

Três formas valem comentário.

`list[str]` diz "lista de textos". Sem o `[str]`, `list` sozinho significa
"lista de qualquer coisa", e não ajuda ninguém.

`str | None` é a forma moderna de "texto ou nada". Em código mais antigo
você vai encontrar `Optional[str]`, importado de `typing`, que significa
exatamente a mesma coisa. A barra chegou no Python 3.10 e é a forma
preferida hoje.

:::pitfall
`Optional[str]` **não** quer dizer "opcional". Quer dizer "pode ser `None`".
Um parâmetro `nome: str | None` continua sendo obrigatório — quem chama
precisa informar alguma coisa, ainda que seja `None`. O que torna um
parâmetro opcional é ter valor padrão. Essa confusão custa horas no capítulo
@cap:schemas, onde obrigatório, opcional e anulável são três coisas
diferentes no mesmo campo.
:::

| Anotação | Significa |
|---|---|
| `x: str` | obrigatório, texto |
| `x: str ou None` | obrigatório, pode ser nulo |
| `x: str = "a"` | opcional, texto |
| `x: str ou None = None` | opcional e anulável |

Tabela: A combinação da terceira e da quarta linha é o que o FastAPI lê para
decidir se um campo é exigido no corpo da requisição.

## O verificador de tipos

As anotações passam a valer de verdade quando uma ferramenta as lê:

```text
$ pip install mypy
$ mypy app/
app/services/produto.py:14: error: Argument 1 to "com_margem"
has incompatible type "str"; expected "float"
Found 1 error in 1 file (checked 12 source files)
```

Agora o erro apareceu **antes de rodar**, apontando a linha da chamada, e
não a linha onde a multiplicação quebrou. É a conferência que o Java faz na
compilação, aqui feita por uma ferramenta opcional, quando você mandar.

:::trivia
Essa opcionalidade é deliberada e tem nome: *gradual typing*. Você anota o
que interessa e deixa o resto sem anotação; as duas partes convivem no mesmo
arquivo. A proposta que introduziu a sintaxe, a PEP 484, de 2014, é explícita
em dizer que o Python nunca vai conferir tipos em execução — e que qualquer
uso das anotações é decisão de quem as lê. O FastAPI existe porque essa
porta ficou aberta.
:::

## `dataclass`: o tipo de dado sem cerimônia

Lembra do capítulo @cap:classes-e-objetos, em que `__init__`, `__repr__`,
`__eq__` e `__hash__` foram escritos à mão? Existe uma linha que faz os
quatro:

```python title="dataclass.py" numbered
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Produto:
    nome: str
    preco: Decimal
    estoque: int = 0
```

```text
>>> p = Produto("Tomate italiano", Decimal("8.90"), 120)
>>> p
Produto(nome='Tomate italiano', preco=Decimal('8.90'), estoque=120)
>>> p == Produto("Tomate italiano", Decimal("8.90"), 120)
True
```

Trinta linhas viraram quatro. O decorador lê as anotações da classe e gera o
inicializador, a representação e a comparação — na ordem em que você
declarou os campos.

:::anatomy title="As partes de uma dataclass"
lang: python
code: |
  @dataclass(frozen=True)
  class Produto:
      nome: str
      estoque: int = 0
      tags: list[str] = field(default_factory=list)
notes:
  - { line: 1, text: "`frozen=True` torna o objeto imutável: atribuir levanta erro." }
  - { line: 3, text: "Campo sem padrão é obrigatório e vem primeiro." }
  - { line: 4, text: "Campo com padrão vem depois — a ordem é a da assinatura." }
  - { line: 5, text: "`default_factory` cria um valor novo por objeto: a cura do padrão mutável." }
:::

:::warning
Uma `dataclass` **não valida nada**. `Produto("", Decimal("-5"))` é aceito
sem reclamar: as anotações continuam sendo metadado. Quem valida é o
Pydantic, do capítulo @cap:modelando-com-pydantic — que tem a mesma cara e
uma diferença enorme.
:::

### Validação e valores derivados

Quando precisar de uma regra, existe o gancho `__post_init__`:

```python title="post_init.py" numbered
@dataclass
class Produto:
    nome: str
    preco: Decimal
    estoque: int = 0

    def __post_init__(self):
        self.nome = self.nome.strip()
        if not self.nome:
            raise ValueError("nome obrigatório")
        if self.preco <= 0:
            raise ValueError("preço deve ser positivo")
```

### Imutável por padrão

```python title="frozen.py" numbered
@dataclass(frozen=True)
class Preco:
    valor: Decimal
    moeda: str = "BRL"
```

Um objeto congelado recusa atribuição depois de criado, e ganha `__hash__`
de graça — ou seja, pode ser chave de dicionário e item de conjunto.

:::key
Quando o objeto representa um **valor** — um preço, um endereço, um
intervalo de datas —, congele. Valor não muda: dez reais não vira doze reais,
o que existe é outro valor. Quando o objeto representa uma **entidade** com
identidade e história — o produto número 42, que teve três preços ao longo do
ano —, ele muda, e não deve ser congelado.
:::

## `Enum`: o conjunto fechado de opções

A escada de `elif` do capítulo @cap:condicionais prometia sumir. É aqui.

```python title="status.py" numbered
from enum import Enum


class StatusProduto(str, Enum):
    ATIVO = "ativo"
    ESGOTADO = "esgotado"
    DESCONTINUADO = "descontinuado"
```

```text
>>> StatusProduto.ATIVO
<StatusProduto.ATIVO: 'ativo'>
>>> StatusProduto.ATIVO.value
'ativo'
>>> StatusProduto("ativo")
<StatusProduto.ATIVO: 'ativo'>
>>> StatusProduto("vendido")
ValueError: 'vendido' is not a valid StatusProduto
```

Aquele `str` na declaração — `class StatusProduto(str, Enum)` — faz o membro
ser também um texto comum. Isso importa muito neste livro: significa que ele
vira JSON sem conversão e entra numa consulta SQL sem tradução.

:::compare left="Texto solto" right="Enum" lang="python"
if p.status == "ativoo":
    ...
---
if p.status is Status.ATIVO:
    ...
:::

Do lado esquerdo, o erro de digitação é uma condição que nunca é verdadeira
e nunca reclama. Do lado direito, é um `AttributeError` na primeira
execução.

:::pitfall
Use `str, Enum` quando o valor precisar viajar — para o JSON, para o banco,
para o log. Um `Enum` puro serializa como `StatusProduto.ATIVO`, que nenhum
cliente de API sabe interpretar. E, do outro lado, use o valor para
armazenar: gravar o **nome** do membro no banco torna impossível renomear o
membro depois.
:::

## Como o FastAPI usa tudo isso

Com as três peças na mão, aquele `main.py` do capítulo
@cap:o-que-vamos-construir pode finalmente ser explicado por inteiro:

```python title="o_que_vem_por_ai.py" numbered
@app.get("/produtos/{produto_id}")
def buscar(
    produto_id: int, incluir_inativos: bool = False
) -> Produto:
    ...
```

O FastAPI lê essa assinatura e decide, sozinho:

- `produto_id: int` está no caminho → converte para inteiro; se vier
  `/produtos/abc`, responde `422` antes de a função rodar.
- `incluir_inativos: bool = False` não está no caminho e tem padrão → é um
  parâmetro de query opcional.
- `-> Produto` → é o formato da resposta, e vira o esquema da documentação.

Nenhuma dessas três decisões precisou de configuração. Elas vieram das
anotações — as mesmas que o `mypy` confere e que o seu editor usa para
sugerir.

:::summary
- Anotação de tipo é metadado: não valida nem converte em execução.
- `list[str]`, `str | None`; `Optional` significa "anulável", não "opcional".
- O que torna um parâmetro opcional é ter valor padrão.
- `mypy` transforma a anotação em conferência de verdade, antes de rodar.
- `dataclass` gera inicializador, representação e comparação — mas não
  valida.
- `frozen=True` para valores; mutável para entidades.
- `str, Enum` fecha o conjunto de opções e ainda viaja como texto.
:::

:::checkpoint
Você anota tipos com precisão, cria `dataclass` e `Enum`, e sabe explicar a
frase que abre a Parte 3: o FastAPI não adivinha nada — ele lê o que você
escreveu.
:::

:::exercise level=1
Anote os tipos da função abaixo, incluindo o retorno.

```python
def resumir(precos, com_iva=False):
    total = sum(precos)
    return {"total": total, "media": total / len(precos)}
```

:::answer
```python
def resumir(
    precos: list[float], com_iva: bool = False
) -> dict[str, float]:
    total = sum(precos)
    return {"total": total, "media": total / len(precos)}
```
O retorno `dict[str, float]` é honesto, e também é pobre: ele não diz quais
chaves existem. O exercício 3 resolve isso.
:::

:::exercise level=2
Escreva a `dataclass` `Entrega` com `produtor: str`, `caixas: int`,
`data: date` e `conferida: bool = False`, recusando entrega com zero caixas.

:::answer
```python
from dataclasses import dataclass
from datetime import date


@dataclass
class Entrega:
    produtor: str
    caixas: int
    data: date
    conferida: bool = False

    def __post_init__(self):
        if self.caixas <= 0:
            raise ValueError("entrega precisa de ao menos uma caixa")
```
:::

:::exercise level=3
Reescreva a função do exercício 1 devolvendo uma `dataclass` congelada em
vez de dicionário. Depois liste três coisas que passaram a ser possíveis
e uma que ficou mais chata.

:::answer
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Resumo:
    total: float
    media: float
    maior: float


def resumir(precos: list[float]) -> Resumo:
    if not precos:
        return Resumo(0.0, 0.0, 0.0)
    total = sum(precos)
    return Resumo(total, total / len(precos), max(precos))
```

**O que passou a ser possível.** O editor sugere `.total` e `.media`, e
acusa `.mdia` na hora de digitar. O `mypy` reclama se alguém somar `Resumo`
com número. E a assinatura passou a documentar o retorno inteiro: quem lê
`-> Resumo` sabe exatamente o que vem, sem abrir o corpo da função.

**O que ficou mais chato.** Um dicionário vira JSON sozinho; a `dataclass`
precisa de `dataclasses.asdict()` ou de um esquema. Esse atrito é pequeno
aqui e desaparece no capítulo @cap:schemas, em que o modelo do Pydantic faz
os dois papéis — tipo em memória e formato na resposta.
:::
