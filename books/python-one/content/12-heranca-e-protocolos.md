---
title: "Herança e protocolos"
number: 12
slug: heranca-e-protocolos
part: p2
kicker: "Em Python, parecer um pato basta. A pergunta é quando isso é liberdade e quando é armadilha."
goal: >-
  Usar herança sem criar parentesco indesejado, preferir composição quando
  ela cabe, e descrever contratos com `Protocol` e classes abstratas.
---

Herança é a ferramenta mais fácil de usar e a mais difícil de desfazer.
Há três formas de dizer "estes objetos têm algo em comum"; a primeira é a
mais ensinada e quase sempre a pior escolha.

## Herança, em quatro linhas

```python title="heranca.py" numbered
class Item:
    def __init__(self, nome, preco):
        self.nome = nome
        self.preco = preco

    def etiqueta(self):
        return f"{self.nome} — R$ {self.preco:.2f}"


class ItemPesavel(Item):
    def __init__(self, nome, preco_kg, peso_kg):
        super().__init__(nome, preco_kg)
        self.peso_kg = peso_kg

    def etiqueta(self):
        base = super().etiqueta()
        return f"{base}/kg · {self.peso_kg} kg"
```

`class ItemPesavel(Item)` diz que todo `ItemPesavel` **é um** `Item`.
`super()` chama a versão da classe de cima — tanto no `__init__` quanto no
método sobrescrito.

:::pitfall
Esquecer `super().__init__(...)` é o defeito silencioso mais comum da
herança em Python. O objeto nasce sem os atributos da classe de cima, e o
erro só aparece muito depois, como `AttributeError: 'ItemPesavel' object has
no attribute 'nome'`, numa linha que não tem nada a ver com o problema.
:::

## Sobrescrever não é "melhorar"

Um método sobrescrito precisa continuar cumprindo a promessa do original. Se
`Item.etiqueta()` devolve texto, `ItemPesavel.etiqueta()` não pode devolver
`None` em alguns casos, nem levantar exceção onde a original não levantava.

Quem chama recebeu um `Item` e vai tratar como `Item`. Essa é toda a regra,
e ela tem nome pomposo — princípio da substituição de Liskov — e uma
formulação simples: **a subclasse pode exigir menos e entregar mais, nunca
o contrário**.

:::example Sobrescrita que quebra o contrato
```python
class ItemDoado(Item):
    def etiqueta(self):
        raise RuntimeError("item doado não tem etiqueta")
```
Compila, roda, e destrói qualquer laço que percorra uma lista de itens
chamando `etiqueta()`. Se `ItemDoado` não sabe fazer o que um `Item` faz,
ele não é um `Item`.
:::

## O problema da herança: parentesco é para sempre

```python title="fundo.py" numbered
class Produto:
    ...


class ProdutoOrganico(Produto):
    ...


class ProdutoImportado(Produto):
    ...
```

Parece razoável — até chegar o produto orgânico **e** importado. Herança
múltipla resolve no papel e cria uma classe nova para cada combinação: com
quatro características, dezesseis classes.

:::diagram type="blocks" caption="A árvore que cresce por combinação: cada característica nova dobra o número de classes."
rows:
  - [{ text: "Produto", note: "a raiz" }]
  - [{ text: "Orgânico", note: "" }, { text: "Importado", note: "" }, { text: "Perecível", note: "" }]
  - [{ text: "OrgânicoImportado", note: "" }, { text: "OrgânicoPerecível", note: "" }, { text: "ImportadoPerecível", note: "" }]
:::

A alternativa é **composição**: em vez de "é um", pergunte "tem um".

```python title="composicao.py" numbered
class Produto:
    def __init__(self, nome, preco, selos=None):
        self.nome = nome
        self.preco = preco
        self.selos = selos or []

    def tem(self, selo):
        return selo in self.selos


tomate = Produto("Tomate", 8.90, selos=["organico", "importado"])
```

Uma classe, qualquer combinação, e a lista de selos cresce sem código novo.

:::key
A regra que salva projetos: **herde para reaproveitar contrato; componha
para reaproveitar comportamento**. Se a única razão para herdar é aproveitar
três métodos prontos, você quer um atributo, não uma superclasse.
:::

:::art caption="Herança profunda é um parentesco que você não pode desfazer."
Charge editorial minimalista em fundo branco: uma árvore genealógica
corporativa desenhada num quadro, com caixas de classe cada vez menores
descendo por seis níveis, e setas que se cruzam nos níveis de baixo. Uma
desenvolvedora olha a árvore de baixo, com a cabeça inclinada para trás, um
café na mão. No canto, uma caixa isolada com uma seta apontando para o nada.
Poucos elementos, humor seco, estética de revista de tecnologia.
:::

## Duck typing: o contrato sem declaração

Esta é a parte em que Python se separa do Java de verdade.

```python title="pato.py" numbered
class Email:
    def enviar(self, texto):
        print(f"e-mail: {texto}")


class SMS:
    def enviar(self, texto):
        print(f"sms: {texto}")


def notificar(canal, texto):
    canal.enviar(texto)
```

`Email` e `SMS` não têm superclasse comum, não implementam interface
nenhuma, não se conhecem. E `notificar` funciona com os dois — porque o
Python não pergunta o tipo, pergunta se o objeto tem o método.

A frase clássica: *se anda como pato e grasna como pato, é um pato.*

:::trivia
Esse comportamento tem uma consequência prática enorme nos testes. Em Java,
substituir o serviço de e-mail por um falso exige que os dois implementem a
mesma interface. Em Python, o falso só precisa ter um método `enviar`. É por
isso que o capítulo @cap:testando-services vai conseguir testar regras de
negócio sem banco, sem rede e sem framework — com dez linhas.
:::

## Quando o contrato precisa ser escrito

Duck typing é flexível e tem um custo: o contrato não está escrito em lugar
nenhum. Quem vai implementar o próximo canal descobre o que é preciso
fazer... lendo o código que usa.

Para escrever o contrato existem duas ferramentas, e elas resolvem problemas
diferentes.

### Classe base abstrata: herança obrigatória

```python title="abc.py" numbered
from abc import ABC, abstractmethod


class Canal(ABC):
    @abstractmethod
    def enviar(self, texto: str) -> None:
        ...


class Email(Canal):
    def enviar(self, texto: str) -> None:
        print(f"e-mail: {texto}")
```

Uma classe com `@abstractmethod` não pode ser instanciada enquanto houver
método não implementado:

```text
TypeError: Can't instantiate abstract class Email with
abstract method enviar
```

O erro acontece na criação do objeto, não na definição da classe — e isso é
tarde, mas ainda é bem antes da produção.

### `Protocol`: contrato sem parentesco

```python title="protocol.py" numbered
from typing import Protocol


class Canal(Protocol):
    def enviar(self, texto: str) -> None:
        ...


def notificar(canal: Canal, texto: str) -> None:
    canal.enviar(texto)
```

Aqui está a diferença que importa: `Email` **não precisa herdar de nada**.
Basta ter um método `enviar` com a assinatura certa, e o verificador de
tipos aceita. É duck typing com o contrato escrito — chamado de *tipagem
estrutural*.

:::compare left="ABC: exige herdar" right="Protocol: exige parecer" lang="python"
class Email(Canal):
    def enviar(self, t):
        ...
---
class Email:
    def enviar(self, t):
        ...
:::

| Use | Quando |
|---|---|
| `Protocol` | você consome objetos que outros escrevem |
| `ABC` | você fornece uma base com código compartilhado |
| nada | o projeto é pequeno e o contrato é óbvio |

Tabela: `Protocol` é a escolha padrão em código moderno; `ABC` continua útil
quando a classe base traz implementação de verdade, não só assinaturas.

## A ordem de resolução

Quando uma classe herda de duas, o Python precisa decidir qual método vence.
A resposta está no MRO — *method resolution order* —, visível em qualquer
momento:

```text
>>> ItemPesavel.__mro__
(<class 'ItemPesavel'>, <class 'Item'>, <class 'object'>)
```

A ordem é da esquerda para a direita, de baixo para cima, sem repetir. Não
vale a pena memorizar o algoritmo; vale saber que ele existe e que
`__mro__` responde a pergunta na hora.

:::warning
Toda vez que a resposta para "qual método vai rodar?" exigir consultar o
MRO, a hierarquia já está complexa demais. Herança múltipla é legítima em
biblioteca e é quase sempre um erro em código de aplicação — o mesmo que
vale para herança com mais de dois níveis.
:::

:::summary
- `super()` chama a versão de cima; esquecê-lo no `__init__` é defeito
  silencioso.
- A subclasse precisa continuar cumprindo a promessa da superclasse.
- Herança modela "é um"; composição modela "tem um" e não explode em
  combinações.
- Duck typing dispensa declaração e por isso deixa o contrato implícito.
- `Protocol` escreve o contrato sem exigir herança; `ABC` exige.
- Precisar do MRO para prever o comportamento é sinal de hierarquia demais.
:::

:::checkpoint
Você herda quando o parentesco é real, compõe quando não é, e sabe declarar
um contrato com `Protocol` — que é a forma que a injeção de dependência do
capítulo @cap:dependency-injection vai usar.
:::

:::exercise level=1
Crie `Item` com `nome` e `preco` e uma subclasse `ItemPromocional` que
sobrescreva `etiqueta()` acrescentando `"— PROMOÇÃO"` ao texto da
superclasse, usando `super()`.

:::answer
```python
class ItemPromocional(Item):
    def etiqueta(self):
        return f"{super().etiqueta()} — PROMOÇÃO"
```
:::

:::exercise level=2
Escreva um `Protocol` chamado `Repositorio` com os métodos `buscar(id)` e
`salvar(produto)`, e uma implementação em memória que satisfaça o protocolo
sem herdar dele.

:::answer
```python
from typing import Protocol


class Repositorio(Protocol):
    def buscar(self, id: int) -> dict | None: ...
    def salvar(self, produto: dict) -> dict: ...


class RepositorioEmMemoria:
    def __init__(self):
        self._dados: dict[int, dict] = {}
        self._proximo = 1

    def buscar(self, id: int) -> dict | None:
        return self._dados.get(id)

    def salvar(self, produto: dict) -> dict:
        produto["id"] = self._proximo
        self._dados[self._proximo] = produto
        self._proximo += 1
        return produto
```
Essa classe é literalmente o repositório que o capítulo @cap:repository vai
substituir por uma versão com banco — e o fato de a troca não exigir mexer
em quem usa é o argumento inteiro a favor do protocolo.
:::

:::exercise level=3
Sua equipe tem `Produto`, e precisa representar produto orgânico, importado,
perecível e em promoção. As características se combinam livremente. Proponha
dois desenhos — um com herança e um sem — e estime quantas classes cada um
exige quando surgir a quinta característica.

:::answer
**Com herança**, cada combinação precisa de uma classe: com quatro
características são até quinze combinações não vazias; com cinco, trinta e
uma. Pior: acrescentar a quinta exige escrever dezesseis classes novas, uma
para cada combinação existente.

**Sem herança**, uma classe só:

```python
class Produto:
    def __init__(self, nome, preco, selos=frozenset()):
        self.nome = nome
        self.preco = preco
        self.selos = frozenset(selos)

    def tem(self, selo: str) -> bool:
        return selo in self.selos
```

A quinta característica custa zero classe: custa uma string a mais numa
lista de valores válidos. Quando o comportamento também variar — e não só o
dado —, o passo seguinte é uma estratégia por selo, guardada num dicionário
de funções, ainda sem nenhuma subclasse.

O sinal de alarme, na hora de decidir, é a palavra **"e"**: no momento em
que aparecer um "orgânico **e** importado", a herança já perdeu.
:::
