---
title: "Classes e objetos"
number: 10
slug: classes-e-objetos
part: p2
kicker: "Um dicionário aceita qualquer chave. Um tipo com nome recusa a chave errada — e isso é o serviço que ele presta."
goal: >-
  Criar classes com estado e comportamento, entender `self`, implementar
  `__repr__` e `__eq__`, e saber quando um dicionário já basta.
---

Até aqui o catálogo era uma lista de dicionários:

```python
produto = {"nome": "Tomate", "preco": 8.90, "estoque": 120}
```

Funciona. E funciona até o dia em que alguém escreve `produto["preço"]`, com
acento, e o Python responde `KeyError` em produção — ou pior, `get` devolve
`None` e o relatório sai com um campo vazio que ninguém notou.

O dicionário aceita qualquer chave porque essa é a função dele. Quando o
formato é conhecido e fixo, você quer o contrário: um tipo que recuse o que
não faz parte.

## A classe

```python title="produto.py" numbered
class Produto:
    def __init__(self, nome, preco, estoque=0):
        self.nome = nome
        self.preco = preco
        self.estoque = estoque

    def disponivel(self):
        return self.estoque > 0


tomate = Produto("Tomate italiano", 8.90, 120)

print(tomate.nome)
print(tomate.disponivel())
```

```text
Tomate italiano
True
```

:::anatomy title="As partes de uma classe"
lang: python
code: |
  class Produto:
      def __init__(self, nome, preco):
          self.nome = nome

      def disponivel(self):
          return self.estoque > 0
notes:
  - { line: 1, text: "Nome em `PascalCase`, substantivo no singular." }
  - { line: 2, text: "`__init__` monta o objeto; não é construtor, é inicializador." }
  - { line: 2, text: "`self` é o próprio objeto e é sempre o primeiro parâmetro." }
  - { line: 3, text: "`self.nome = nome` cria o atributo. Não existe declaração antes." }
  - { line: 5, text: "Método é função dentro da classe — e também recebe `self`." }
:::

:::term Classe
A descrição de um tipo: que dados ele carrega e que operações aceita.
:::

:::term Objeto (ou instância)
Um exemplar concreto de uma classe, com seus próprios valores, criado ao
chamar a classe: `Produto("Tomate", 8.90)`.
:::

## `self` não é mágica

`self` é apenas o primeiro parâmetro, e o Python o preenche sozinho com o
objeto à esquerda do ponto. Estas duas linhas fazem literalmente a mesma
coisa:

```python
tomate.disponivel()
Produto.disponivel(tomate)
```

A primeira é como se escreve; a segunda é o que acontece. Entender isso
dissolve a dúvida mais comum de quem começa — *por que eu escrevo `self` na
definição e não na chamada?*

:::pitfall
Esquecer `self` na definição do método dá um erro que parece não ter nada a
ver:

```text
TypeError: disponivel() takes 0 positional arguments
but 1 was given
```

"Zero argumentos, mas um foi dado": o argumento que foi dado é o próprio
objeto. A tradução do erro é *"faltou `self`"*.
:::

:::diagram type="blocks" caption="Uma classe, dois objetos: mesma estrutura, valores próprios."
rows:
  - [{ text: "class Produto", note: "nome, preço, estoque, disponivel()" }]
  - [{ text: "tomate", note: "\"Tomate\" · 8.90 · 120" }, { text: "alface", note: "\"Alface\" · 3.50 · 0" }]
:::

## Atributo de instância e atributo de classe

```python title="atributos.py" numbered
class Produto:
    TAXA_PADRAO = 0.12          # da classe: um só, compartilhado

    def __init__(self, nome, preco):
        self.nome = nome        # da instância: um por objeto
        self.preco = preco

    def preco_final(self):
        return self.preco * (1 + Produto.TAXA_PADRAO)
```

O atributo de classe é útil para constante e para valor realmente comum a
todos. E carrega a mesma armadilha do capítulo @cap:funcoes:

:::warning
Atributo de classe **mutável** é compartilhado por todos os objetos. Se você
escrever `tags = []` no corpo da classe, todo produto criado vai dividir a
mesma lista de tags, e acrescentar uma tag a um produto acrescenta a todos.
Lista, dicionário e conjunto nascem dentro do `__init__`, sempre.
:::

## Imprimir um objeto

```text
>>> print(tomate)
<__main__.Produto object at 0x7f3c8c0d5e50>
```

Esse é o texto padrão, e ele é inútil em log, em depuração e em teste. O
conserto é um método especial:

```python title="repr.py" numbered
class Produto:
    def __init__(self, nome, preco):
        self.nome = nome
        self.preco = preco

    def __repr__(self):
        return f"Produto({self.nome!r}, {self.preco})"
```

```text
>>> tomate
Produto('Tomate italiano', 8.9)
```

O `!r` dentro da `f-string` pede a representação do valor, com aspas para
texto. A convenção do `__repr__` é ser **inequívoco**: quem lê a saída deve
saber exatamente qual objeto é aquele.

:::key
`__repr__` é o investimento de três linhas que se paga na primeira
depuração. Quando um teste falhar, a mensagem vai mostrar o que você
escreveu aqui — e a diferença entre `<Produto object at 0x7f3c>` e
`Produto('Tomate', 8.9)` é a diferença entre adivinhar e ver.
:::

## Comparar objetos

```text
>>> a = Produto("Tomate", 8.90)
>>> b = Produto("Tomate", 8.90)
>>> a == b
False
```

Por padrão, `==` entre objetos compara identidade: são o mesmo objeto na
memória? Quase nunca é o que você quer.

```python title="eq.py" numbered
class Produto:
    def __init__(self, nome, preco):
        self.nome = nome
        self.preco = preco

    def __eq__(self, outro):
        if not isinstance(outro, Produto):
            return NotImplemented
        return (self.nome, self.preco) == (outro.nome, outro.preco)

    def __hash__(self):
        return hash((self.nome, self.preco))
```

Duas observações que evitam defeito silencioso. `NotImplemented` (e não
`False`) é a resposta correta para "não sei comparar com esse tipo" — ela
deixa o Python tentar o caminho inverso antes de desistir. E definir
`__eq__` **sem** definir `__hash__` torna o objeto inutilizável como chave
de dicionário ou item de conjunto: o Python remove o hash automaticamente
para não deixar dois objetos iguais com hashes diferentes.

:::trivia
Métodos com dois sublinhados dos dois lados são chamados de *dunder*, de
*double underscore*. Eles não são privados nem secretos: são os pontos de
encaixe da linguagem. `len(x)` chama `x.__len__()`, `x + y` chama
`x.__add__(y)`, `for i in x` chama `x.__iter__()`. Aprender que `+` é um
método com nome é o que transforma a linguagem de mágica em mecanismo.
:::

Escrever `__init__`, `__repr__`, `__eq__` e `__hash__` à mão para cada
classe é repetitivo — e é exatamente o problema que o `dataclass` do
capítulo @cap:tipagem-e-dataclasses resolve em uma linha.

## Método que muda o estado

```python title="estoque.py" numbered
class Produto:
    def __init__(self, nome, preco, estoque=0):
        self.nome = nome
        self.preco = preco
        self.estoque = estoque

    def repor(self, quantidade):
        if quantidade <= 0:
            raise ValueError("quantidade deve ser positiva")
        self.estoque += quantidade

    def vender(self, quantidade):
        if quantidade > self.estoque:
            raise ValueError("estoque insuficiente")
        self.estoque -= quantidade
```

Repare no que mudou de verdade: a regra *"não se vende mais do que se tem"*
saiu do código que chama e entrou no objeto que sabe. Antes, quem quisesse
vender precisava lembrar de conferir; agora, o objeto recusa.

:::key
Esse deslocamento é a ideia central de orientação a objetos, e ela cabe numa
frase: **o dado e as regras sobre o dado moram juntos**. Uma lista de
dicionários espalha as regras por todo lugar que toca a lista. Uma classe as
concentra num arquivo só.
:::

:::story O produto com estoque negativo
O relatório de fechamento apontou quatro produtos com estoque negativo.

— Menos três alfaces — leu Dona Neuza. — A gente vendeu três alfaces que não
existiam.

Bia foi atrás. Achou seis lugares no código que subtraíam do estoque. Cinco
conferiam antes. O sexto era uma rotina de ajuste em lote, escrita às pressas
em novembro.

— Conserto o sexto — ela disse.

Elias balançou a cabeça.

— Conserta, e daqui a seis meses alguém escreve o sétimo. — Ele puxou a
cadeira. — A pergunta certa não é onde está o que subtrai errado. É por que
existe algum lugar, fora do produto, que consegue subtrair.
:::

## Quando a classe não vale a pena

Nem todo agrupamento de dados merece uma classe. Três casos em que o
dicionário continua sendo a resposta certa:

- **Dado que chegou de fora e você ainda não validou.** Um JSON recém-lido é
  um dicionário, e transformá-lo em objeto é justamente o trabalho de
  validação do capítulo @cap:modelando-com-pydantic.
- **Formato que muda a cada chamada.** Se as chaves não são conhecidas de
  antemão, um tipo fixo atrapalha.
- **Estrutura usada em três linhas e descartada.** Classe para viver dentro
  de uma função é cerimônia.

:::pitfall
O sinal de que uma classe não deveria existir: ela só tem `__init__` e
métodos `get_nome`, `set_nome`, `get_preco`, `set_preco`. Isso é um
dicionário com mais digitação. Ou a classe ganha uma regra própria, ou vira
`dataclass`, ou volta a ser dicionário.
:::

:::summary
- Classe descreve um tipo; objeto é um exemplar com valores próprios.
- `self` é o primeiro parâmetro, preenchido pelo Python na chamada.
- Atributo mutável da classe é compartilhado — crie dentro do `__init__`.
- `__repr__` é três linhas que se pagam na primeira depuração.
- `__eq__` sem `__hash__` quebra uso em conjunto e dicionário.
- A regra sobre o dado mora junto com o dado.
:::

:::checkpoint
Você escreve classes com estado e comportamento, sabe explicar `self` sem
apelar para metáfora, e consegue defender quando um dicionário já bastaria.
:::

:::exercise level=1
Crie a classe `Produtor` com `nome`, `cidade` e `certificado` (booleano),
com um método `descricao()` que devolva `"Seu Onofre — Ibiúna (certificado)"`.

:::answer
```python
class Produtor:
    def __init__(self, nome, cidade, certificado=False):
        self.nome = nome
        self.cidade = cidade
        self.certificado = certificado

    def descricao(self):
        selo = "certificado" if self.certificado else "convencional"
        return f"{self.nome} — {self.cidade} ({selo})"
```
:::

:::exercise level=2
Acrescente à classe `Produto` um método `aplicar_desconto(percentual)` que
recuse percentual fora da faixa de 0 a 50 e nunca deixe o preço ficar abaixo
de um centavo.

:::answer
```python
from decimal import Decimal


class Produto:
    def __init__(self, nome, preco):
        self.nome = nome
        self.preco = Decimal(preco)

    def aplicar_desconto(self, percentual):
        if not 0 <= percentual <= 50:
            raise ValueError("desconto fora da faixa permitida")
        novo = self.preco * (1 - Decimal(percentual) / 100)
        self.preco = max(novo, Decimal("0.01"))
```
A comparação encadeada do capítulo @cap:operadores expressa a faixa numa
linha. O `max` no fim é o piso — a mesma forma do teto do frete, virada ao
contrário.
:::

:::exercise level=3
A classe abaixo tem um defeito que só aparece a partir do segundo objeto
criado. Encontre, explique e conserte.

```python
class Pedido:
    itens = []

    def __init__(self, cliente):
        self.cliente = cliente

    def adicionar(self, produto):
        self.itens.append(produto)
```

:::answer
`itens = []` está no corpo da classe, não no `__init__`. Existe **uma**
lista, criada quando o módulo foi importado, e todo pedido compartilha ela.
O pedido da Dona Neuza aparece dentro do pedido do Seu Onofre.

```python
class Pedido:
    def __init__(self, cliente):
        self.cliente = cliente
        self.itens = []
```

O detalhe cruel é o `self.itens.append(...)`: ele **lê** `self.itens`,
encontra o atributo da classe e modifica a lista compartilhada, sem nunca
criar um atributo de instância. Se o método fizesse `self.itens = [produto]`
— atribuição, não modificação —, aí sim nasceria um atributo próprio, e o
defeito ficaria ainda mais confuso, porque só alguns pedidos teriam a lista
compartilhada.

É a mesma armadilha do valor padrão mutável do capítulo @cap:funcoes, vestida
de outra roupa: **objeto mutável criado uma vez e usado como se fosse novo a
cada vez**.
:::
