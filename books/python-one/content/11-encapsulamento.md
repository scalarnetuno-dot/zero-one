---
title: "Encapsulamento"
number: 11
slug: encapsulamento
part: p2
kicker: "Python não tranca a porta. Ele coloca uma placa — e a placa funciona melhor do que quase ninguém espera."
goal: >-
  Proteger a coerência de um objeto com convenção e `@property`, entender por
  que Python não tem `private`, e projetar a superfície pública de uma classe.
---

Em Java, um atributo `private` é inacessível de fora: o compilador recusa.
Em Python, não existe `private`. Existe uma convenção — um sublinhado na
frente do nome — e ela é obedecida por praticamente todo o ecossistema.

Parece frágil. Na prática, é uma das decisões de design mais interessantes
da linguagem.

## A placa: um sublinhado

```python title="produto.py" numbered
class Produto:
    def __init__(self, nome, preco):
        self.nome = nome          # público
        self._preco = preco       # interno, por convenção
        self._historico = []      # interno
```

O sublinhado diz: *"isto é detalhe de implementação; pode mudar sem aviso;
não construa nada em cima"*. O Python não impede o acesso — `produto._preco`
funciona — mas o editor esconde da lista de sugestões, o `from x import *`
ignora, e a revisão de código cobra.

:::key
A frase que resume a filosofia é conhecida no meio: *"somos todos adultos
aqui"*. Em vez de impedir o acesso, a linguagem informa a intenção. Em
troca, você ganha a possibilidade de depurar, testar e adaptar código de
terceiros sem brigar com o compilador. A escolha tem custo e tem benefício,
e é honesta sobre os dois.
:::

## Dois sublinhados: uma coisa diferente do que parece

```python title="mangling.py" numbered
class Produto:
    def __init__(self):
        self.__segredo = 42


p = Produto()
print(p.__segredo)      # AttributeError
print(p._Produto__segredo)   # 42
```

Dois sublinhados no começo ativam o *name mangling*: o Python renomeia o
atributo para `_NomeDaClasse__atributo`. Não é privacidade — é **prevenção
de colisão**, pensada para que uma subclasse não sobrescreva por acidente um
atributo interno da classe de cima.

:::pitfall
Muita gente usa `__` achando que é `private` de Java. O efeito colateral é
ruim: o atributo fica difícil de inspecionar na depuração, atrapalha teste e
confunde quem herda. A regra prática: **use um sublinhado**. Dois, só no caso
raro em que uma subclasse pode realmente colidir com o seu nome.
:::

## `@property`: um atributo que é uma função

Aqui está a resposta do Python para o problema que em outras linguagens
gerou milhares de `getPreco()` e `setPreco()`.

```python title="property.py" numbered
from decimal import Decimal


class Produto:
    def __init__(self, nome, preco):
        self.nome = nome
        self._preco = Decimal(preco)

    @property
    def preco(self):
        return self._preco

    @preco.setter
    def preco(self, valor):
        valor = Decimal(valor)
        if valor <= 0:
            raise ValueError("preço deve ser positivo")
        self._preco = valor
```

E o uso:

```text
>>> p = Produto("Tomate", "8.90")
>>> p.preco
Decimal('8.90')
>>> p.preco = "9.50"
>>> p.preco = "-1"
ValueError: preço deve ser positivo
```

Repare no que **não** mudou: quem usa continua escrevendo `p.preco`, sem
parênteses, como se fosse um atributo comum. A validação entrou sem que a
interface mudasse.

:::key
Essa é a razão pela qual Python não escreve `getPreco()` desde o começo "por
precaução". Em Java, transformar um atributo público em método é uma mudança
que quebra quem chama, e por isso o `get/set` nasce preventivo. Em Python,
essa transformação é invisível — então você começa simples e adiciona a
`property` **no dia em que precisar**.
:::

:::compare left="O reflexo do Java" right="O jeito Python" lang="python"
class P:
    def get_preco(self):
        return self._preco

    def set_preco(self, v):
        self._preco = v
---
class P:
    @property
    def preco(self):
        return self._preco
:::

## Propriedade calculada

Nem toda `property` guarda valor. Muitas apenas respondem:

```python title="calculada.py" numbered
class Produto:
    def __init__(self, nome, preco, estoque):
        self.nome = nome
        self.preco = preco
        self.estoque = estoque

    @property
    def disponivel(self):
        return self.estoque > 0

    @property
    def valor_em_estoque(self):
        return self.preco * self.estoque
```

`produto.disponivel` lê como um fato sobre o objeto, e não como um pedido de
trabalho. A regra de bolso: se a resposta é **barata e sem efeito colateral**,
`property`; se envolve consulta, rede ou cálculo pesado, método com
parênteses — porque os parênteses avisam o leitor de que algo acontece ali.

:::warning
Nunca coloque consulta a banco dentro de uma `property`. Um `for` que
imprime `produto.categoria` vira uma consulta por volta, e ninguém que lê o
laço consegue suspeitar disso. É o defeito N+1 do capítulo
@cap:relacionamentos, disfarçado de atributo.
:::

## Invariante: o que nunca pode deixar de ser verdade

Encapsular não é esconder atributo. É **garantir uma verdade**.

No caso do produto, as verdades são: o preço é positivo, o estoque nunca é
negativo, e o nome não é vazio. Elas se chamam invariantes, e um objeto bem
encapsulado é aquele em que não existe caminho — nenhum — que as quebre.

```python title="invariantes.py" numbered
class Produto:
    def __init__(self, nome, preco, estoque=0):
        if not nome.strip():
            raise ValueError("nome obrigatório")
        self.nome = nome.strip()
        self._preco = Decimal(preco)
        self._estoque = int(estoque)
        if self._preco <= 0:
            raise ValueError("preço deve ser positivo")
        if self._estoque < 0:
            raise ValueError("estoque não pode ser negativo")

    @property
    def estoque(self):
        return self._estoque

    def repor(self, quantidade):
        if quantidade <= 0:
            raise ValueError("reposição deve ser positiva")
        self._estoque += quantidade

    def vender(self, quantidade):
        if quantidade > self._estoque:
            raise ValueError("estoque insuficiente")
        self._estoque -= quantidade
```

Repare que `estoque` tem `property` de leitura e **não** tem setter. É
deliberado: o estoque muda por `repor` e por `vender`, que são as duas
operações do negócio. Não existe "atribuir estoque" — existe repor e vender.

Esse é o conserto da história do capítulo @cap:classes-e-objetos: não há
mais como subtrair do estoque por fora.

:::pitfall
Validar no `__init__` e esquecer os métodos é o erro mais comum de
encapsulamento. O objeto nasce coerente e fica incoerente na terceira
operação. A invariante precisa valer **depois de toda operação pública**,
não só no nascimento.
:::

## A superfície pública

Um bom exercício antes de escrever a classe: liste o que quem usa precisa
saber, e só isso.

| Público | Interno |
|---|---|
| `nome`, `preco`, `estoque` (leitura) | `_historico` |
| `repor()`, `vender()` | `_recalcular_media()` |
| `disponivel` | `_cache_categoria` |

Tabela: A coluna da esquerda é um contrato — mudar algo ali quebra quem usa.
A da direita você reescreve numa terça-feira sem avisar ninguém.

:::key
Quanto menor a coluna da esquerda, mais liberdade você tem. Todo atributo
público é uma promessa; toda promessa é uma restrição futura. Comece com a
menor superfície que resolve, e acrescente sob demanda — o caminho inverso é
muito mais caro.
:::

:::summary
- Um sublinhado é convenção de "interno" e o ecossistema inteiro a respeita.
- Dois sublinhados são prevenção de colisão, não privacidade.
- `@property` acrescenta validação sem mudar a interface de quem usa.
- Propriedade para resposta barata; método com parênteses para trabalho.
- Encapsular é garantir invariantes depois de toda operação pública.
- Superfície pública pequena hoje é liberdade de mudar amanhã.
:::

:::exercise level=1
Transforme o atributo `estoque` de `Produto` numa `property` de leitura e
garanta que ele só mude por `repor` e `vender`.

:::answer
```python
class Produto:
    def __init__(self, nome, estoque=0):
        self.nome = nome
        self._estoque = estoque

    @property
    def estoque(self):
        return self._estoque

    def repor(self, q):
        self._estoque += q

    def vender(self, q):
        if q > self._estoque:
            raise ValueError("estoque insuficiente")
        self._estoque -= q
```
`produto.estoque = 500` agora levanta `AttributeError`, porque a property
não tem setter. Essa recusa é o objetivo, não um efeito colateral.
:::

:::exercise level=2
Crie a classe `Produtor` com uma `property` `email` que normalize a entrada
(sem espaços, tudo minúsculo) e recuse texto sem `@`.

:::answer
```python
class Produtor:
    def __init__(self, nome, email):
        self.nome = nome
        self.email = email        # passa pelo setter

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, valor):
        valor = valor.strip().lower()
        if "@" not in valor:
            raise ValueError("e-mail inválido")
        self._email = valor
```
O detalhe que faz isso funcionar está no `__init__`: escrever `self.email =
email`, e não `self._email = email`, faz a atribuição passar pelo setter — e
a validação valer desde o nascimento do objeto.

Vale registrar que validar e-mail com `"@" in valor` é grosseiro. A validação
séria é do capítulo @cap:validacao, onde o Pydantic faz isso com um tipo
chamado `EmailStr` e a regra deixa de morar na sua classe.
:::

:::exercise level=3
Um colega argumenta que, como Python não tem `private` de verdade,
encapsulamento em Python é decorativo — "qualquer um pode escrever
`p._estoque = -5`". Responda em cinco linhas, e diga o que de fato muda
quando alguém faz isso.

:::answer
Muda a responsabilidade. Com a invariante protegida, `p._estoque = -5` é um
ato deliberado de quem está ignorando uma placa explícita, feito em uma linha
que qualquer busca por `_estoque` encontra. Sem encapsulamento, o mesmo
estoque negativo aparece por acidente, espalhado em seis lugares, escrito por
gente que não sabia que havia uma regra.

O que o encapsulamento entrega não é impossibilidade — é **um lugar só onde
a regra mora** e **um rastro claro** de quem a contornou. A garantia física
do compilador é uma comodidade a mais, e nem ela impede reflexão, serialização
ou um construtor mal escrito. O argumento do seu colega vale contra a ideia
de que encapsulamento é uma tranca; não vale contra a ideia de que ele é um
contrato.
:::
