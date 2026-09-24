---
title: "Estruturas de dados"
number: 9
slug: estruturas-de-dados
part: p1
kicker: "Quatro coleções e uma pergunta: o que você vai precisar perguntar a esses dados depois?"
goal: >-
  Escolher entre lista, tupla, dicionário e conjunto por critério; fatiar,
  ordenar e transformar coleções; e saber o que acontece quando duas
  variáveis apontam para a mesma lista.
---

:::story O açafrão com preço de beterraba
A planilha da feira tinha duas abas: uma de nomes, uma de preços. Alguém
inseriu uma linha no meio da primeira e esqueceu a segunda.

— O açafrão está a três e cinquenta — disse a Dona Neuza. — Açafrão não custa
três e cinquenta. Beterraba custa.

A Bia alinhou as linhas no olho. A partir do açafrão, cada nome estava com o
preço do de baixo.

— São duas listas — ela disse.

— Era uma ficha — disse a Dona Neuza. — Nome e preço na mesma linha. Ninguém
inseriu preço sem inserir nome, porque não tinha onde.

O Elias passou, olhou a aba, e seguiu.

— Separar o que vive junto é que cria o trabalho de juntar de novo.
:::

Python tem quatro coleções embutidas. O critério para escolher não é o que
você quer guardar: é o que você vai querer **perguntar** depois. A ficha da
Dona Neuza pergunta "qual o preço deste nome?". Duas abas paralelas perguntam
"qual é o décimo terceiro de cada uma?" — e essa pergunta é a que deu errado.

| Coleção | Escrita | Guarda | Pergunta que responde rápido |
|---|---|---|---|
| `list` | `[1, 2, 3]` | em ordem, repetível | "qual é o terceiro?" |
| `tuple` | `(1, 2, 3)` | em ordem, imutável | "qual é o par completo?" |
| `dict` | `{"a": 1}` | pares chave→valor | "qual é o valor de X?" |
| `set` | `{1, 2, 3}` | únicos, sem ordem | "isso já apareceu?" |

Tabela: Lista e dicionário resolvem noventa por cento dos casos. Os outros
dez por cento são exatamente os que dão trabalho quando resolvidos errado.

## Lista: a coleção padrão

```python title="lista.py" numbered
produtos = ["Tomate", "Alface", "Cenoura"]

produtos.append("Beterraba")
produtos.insert(0, "Abobrinha")
produtos.remove("Alface")

print(produtos)
print(len(produtos))
print(produtos[0], produtos[-1])
```

```text
['Abobrinha', 'Tomate', 'Cenoura', 'Beterraba']
4
Abobrinha Beterraba
```

O índice `-1` é o último, `-2` o penúltimo. Não existe `produtos[4]` numa
lista de quatro — isso levanta `IndexError`, e é um dos poucos erros que o
Python não consegue explicar melhor do que dizendo `list index out of
range`.

### Fatias

```python title="fatias.py" numbered
p = ["a", "b", "c", "d", "e"]

print(p[1:3])    # ['b', 'c']
print(p[:2])     # ['a', 'b']
print(p[2:])     # ['c', 'd', 'e']
print(p[-2:])    # ['d', 'e']
print(p[::2])    # ['a', 'c', 'e']
print(p[::-1])   # ['e', 'd', 'c', 'b', 'a']
```

A mesma regra do `range`: início incluído, fim excluído. `p[1:3]` tem
`3 - 1 = 2` itens — a conta é direta e é por isso que a convenção existe.

Fatiar **sempre devolve uma cópia**, nunca a lista original. Por isso
`copia = p[:]` é a forma curta de copiar, e por isso devolver só os vinte
primeiros (`p[0:20]`) não mexe em quem ficou de fora.

### Ordenar

```python title="ordenar.py" numbered
precos = [8.90, 3.50, 12.00, 5.25]

print(sorted(precos))                 # cópia ordenada
print(sorted(precos, reverse=True))   # decrescente
precos.sort()                         # ordena no lugar, devolve None
```

:::pitfall
`sorted(lista)` devolve uma lista nova. `lista.sort()` ordena no lugar e
devolve `None`. Escrever `precos = precos.sort()` transforma a lista em
`None` — e o erro só aparece algumas linhas depois, quando alguém tenta usar
`precos`. Essa é a regra geral da linguagem: método que modifica no lugar
devolve `None`, de propósito, para que você não encadeie por engano.
:::

Ordenar por um critério usa `key`, que recebe uma função:

```python title="ordenar_por.py" numbered
produtos = [
    {"nome": "Tomate", "preco": 8.90},
    {"nome": "Alface", "preco": 3.50},
]

por_preco = sorted(produtos, key=lambda p: p["preco"])
por_nome = sorted(produtos, key=lambda p: p["nome"])
```

`lambda` é uma função anônima de uma expressão só. Ela existe para casos
exatamente assim — um critério curto, usado uma vez. Se o corpo do `lambda`
passar de uma linha simples, escreva um `def` com nome.

## Tupla: o registro fixo

```python title="tupla.py" numbered
coordenada = (-23.55, -46.63)
dimensoes = (30, 20, 15)

print(coordenada[0])
coordenada[0] = 0   # TypeError
```

Tupla é uma lista que não muda. A pergunta útil não é "quero proteger isso?",
e sim: **os itens têm papéis diferentes?**

- `["Tomate", "Alface", "Cenoura"]` — três coisas do mesmo tipo, quantidade
  variável. Lista.
- `(-23.55, -46.63)` — latitude e longitude, papéis diferentes, quantidade
  fixa. Tupla.

E há um uso que aparece o tempo todo, o desempacotamento:

```python title="desempacotar.py" numbered
nome, preco = ("Tomate", 8.90)

a, b = b, a           # troca sem variável temporária
primeiro, *resto = [1, 2, 3, 4]
```

`a, b = b, a` funciona porque o lado direito vira uma tupla antes de
qualquer atribuição acontecer. É a troca mais limpa de qualquer linguagem
popular.

## Dicionário: a estrutura da API

Se você tivesse de escolher uma estrutura só para trabalhar com APIs, seria
esta. JSON é dicionário. Corpo de requisição é dicionário. Resposta é
dicionário.

```python title="dicionario.py" numbered
produto = {
    "nome": "Tomate italiano",
    "preco": 8.90,
    "estoque": 120,
}

print(produto["nome"])
produto["organico"] = True
del produto["estoque"]

for chave, valor in produto.items():
    print(f"{chave} = {valor}")
```

:::diagram type="cells" caption="Um dicionário é uma tabela de duas colunas com busca instantânea pela primeira."
items: ["nome", "preco", "organico"]
orientation: horizontal
notes:
  - { at: 0, text: "\"Tomate italiano\"" }
  - { at: 1, text: "8.90" }
  - { at: 2, text: "True" }
:::

A busca por chave é praticamente instantânea, independentemente do tamanho
do dicionário — mil ou um milhão de chaves custam o mesmo. Isso não é mágica:
é uma tabela de espalhamento, e o preço dela é que as chaves precisam ser
imutáveis. Texto, número e tupla podem ser chave; lista não pode.

### Chave que não existe

```text
>>> produto["categoria"]
KeyError: 'categoria'
```

Três formas de lidar com isso, em ordem de preferência:

```python title="chave_ausente.py" numbered
categoria = produto.get("categoria")
categoria = produto.get("categoria", "sem categoria")

if "categoria" in produto:
    categoria = produto["categoria"]
```

:::key
`get` é o modo seguro e devolve `None` quando a chave falta. O acesso com
colchete é o modo **exigente**: ele levanta `KeyError`, e às vezes é
exatamente o que você quer — falhar alto quando um campo obrigatório não
veio, em vez de propagar um `None` silencioso até o banco de dados.
:::

## Conjunto: o que já apareceu

```python title="conjunto.py" numbered
categorias = {"fruta", "legume", "fruta", "verdura"}
print(categorias)          # {'fruta', 'legume', 'verdura'}
print(len(categorias))     # 3

a = {"tomate", "alface"}
b = {"alface", "cenoura"}

print(a & b)   # {'alface'}      em ambos
print(a | b)   # união
print(a - b)   # só em a
```

Duas utilidades práticas: eliminar repetições (`list(set(nomes))`) e comparar
coleções sem escrever laço aninhado. Aquele `for` dentro de `for` para
descobrir o que há em comum entre duas listas — a operação que custa `n × m`
— vira um `&` que custa quase nada.

:::pitfall
Conjunto **não tem ordem**. `list(set(nomes))` devolve os nomes únicos numa
ordem que pode mudar entre execuções. Se a ordem importa — e numa resposta
de API ela quase sempre importa —, ordene depois: `sorted(set(nomes))`.
:::

## Comprehensions

A forma curta do laço que monta outra coleção também vale para dicionário e
para conjunto. A leitura não muda: o que está na frente é o resultado, o
`for` diz de onde vem.

```python title="comprehensions.py" numbered
produtos = [
    {"nome": "Tomate", "preco": 8.90, "categoria": "fruta"},
    {"nome": "Alface", "preco": 3.50, "categoria": "verdura"},
]

por_nome = {p["nome"]: p["preco"] for p in produtos}
categorias = {p["categoria"] for p in produtos}

print(por_nome)
print(sorted(categorias))
```

```text
{'Tomate': 8.9, 'Alface': 3.5}
['fruta', 'verdura']
```

Lê-se de dentro para fora: *para cada produto em produtos*, e o que fica na
frente é o par ou o valor que entra na coleção nova. Colchete produz lista;
chave com dois-pontos produz dicionário; chave sem dois-pontos produz
conjunto. O `sorted` está ali porque conjunto não promete ordem — imprimir
direto seria apostar na ordem do dia.

:::compare left="Com laço" right="Com comprehension" lang="python"
caros = []
for p in precos:
    if p > 10:
        caros.append(p)
---
caros = [p for p in precos
         if p > 10]
:::

:::pitfall
Comprehension aninhada com condição em dois níveis é ilegível e ninguém
ganha nada com ela. A régua honesta: se você precisa parar para ler, ela já
deveria ser um `for`. Concisão é meio, não objetivo.
:::

## Duas variáveis, uma lista

Esta é a maior fonte de surpresa em Python depois do valor padrão mutável.

```python title="alias.py" numbered
a = ["Tomate", "Alface"]
b = a

b.append("Cenoura")
print(a)
```

```text
['Tomate', 'Alface', 'Cenoura']
```

`b = a` **não copia nada**. Ele cria um segundo nome para a mesma lista.
Quem modifica por um nome modifica para os dois — porque não há dois, há um.

Para copiar de verdade:

```python
b = a[:]          # cópia rasa, a forma curta
b = list(a)       # cópia rasa, a forma explícita
```

E "rasa" tem um significado preciso:

```python title="copia_rasa.py" numbered
original = [{"nome": "Tomate"}, {"nome": "Alface"}]
copia = original[:]

copia[0]["nome"] = "Beterraba"
print(original[0]["nome"])   # Beterraba
```

A cópia rasa duplicou a lista de fora, mas os dicionários lá dentro
continuam sendo os mesmos objetos. Quando a estrutura tem níveis e você
precisa de independência real, existe `copy.deepcopy` — que é lento e quase
sempre é sinal de que o desenho poderia ser melhor.

:::warning
Nunca altere uma lista enquanto a percorre. Remover item dentro de um `for`
faz o Python pular elementos silenciosamente, porque o índice interno avança
enquanto a lista encolhe. A forma correta é construir uma lista nova:
`ativos = [p for p in produtos if p["ativo"]]`.
:::

## Escolhendo

:::diagram type="flowchart" caption="Quatro perguntas, quatro coleções."
nodes:
  - { id: q1, type: decision, text: "busca por chave?" }
  - { id: d,  type: process,  text: "dict" }
  - { id: q2, type: decision, text: "só precisa de únicos?" }
  - { id: s,  type: process,  text: "set" }
  - { id: q3, type: decision, text: "tamanho fixo, papéis distintos?" }
  - { id: t,  type: process,  text: "tuple" }
  - { id: l,  type: process,  text: "list" }
edges:
  - { from: q1, to: d,  label: "sim" }
  - { from: q1, to: q2, label: "não" }
  - { from: q2, to: s,  label: "sim" }
  - { from: q2, to: q3, label: "não" }
  - { from: q3, to: t,  label: "sim" }
  - { from: q3, to: l,  label: "não" }
:::

:::summary
- Lista é ordenada e mutável; tupla é ordenada e fixa, para papéis distintos.
- Dicionário busca por chave em tempo constante; é a estrutura do JSON.
- Conjunto guarda únicos e compara coleções sem laço aninhado — sem ordem.
- Fatia devolve cópia; início incluído, fim excluído.
- `sort()` devolve `None`; `sorted()` devolve a lista nova.
- `b = a` cria um apelido, não uma cópia.
- Nunca altere a coleção que você está percorrendo.
:::

:::milestone
Você já tem o suficiente para representar um catálogo inteiro na memória:
uma lista de dicionários. Também já dá para ver o limite. A lista morre
quando o programa termina. A planilha, com todos os defeitos, ao menos
continua lá amanhã.
:::

:::exercise level=1
Dada a lista `["fruta", "legume", "fruta", "verdura", "legume"]`, imprima as
categorias únicas em ordem alfabética.

:::answer
```python
cats = ["fruta", "legume", "fruta", "verdura", "legume"]
print(sorted(set(cats)))
```
```text
['fruta', 'legume', 'verdura']
```
:::

:::exercise level=2
Dada a lista de produtos abaixo, produza um dicionário que mapeie categoria
para a soma do estoque daquela categoria.

```python
produtos = [
    {"nome": "Tomate", "cat": "legume", "estoque": 120},
    {"nome": "Alface", "cat": "verdura", "estoque": 40},
    {"nome": "Cenoura", "cat": "legume", "estoque": 80},
]
```

:::answer
```python
total = {}
for p in produtos:
    total[p["cat"]] = total.get(p["cat"], 0) + p["estoque"]

print(total)
```
```text
{'legume': 200, 'verdura': 40}
```
O `get(chave, 0)` é o idioma para "some ao que já existe, começando do zero
se for a primeira vez". A biblioteca padrão tem uma versão pronta disso,
`collections.defaultdict(int)`, que dispensa o `get`.
:::

:::exercise level=3
O código abaixo deveria aplicar um desconto de 10% nos produtos caros, sem
alterar a lista original. Ele altera. Explique por quê e conserte de duas
formas diferentes.

```python
def com_desconto(produtos):
    copia = produtos[:]
    for p in copia:
        if p["preco"] > 10:
            p["preco"] *= 0.9
    return copia
```

:::answer
`produtos[:]` copiou a lista, mas não os dicionários dentro dela. `copia[0]`
e `produtos[0]` são o **mesmo** dicionário, e alterar `p["preco"]` altera o
original.

A primeira forma constrói dicionários novos:

```python
def com_desconto(produtos):
    return [
        {**p, "preco": p["preco"] * 0.9}
        if p["preco"] > 10 else {**p}
        for p in produtos
    ]
```

A segunda usa cópia profunda:

```python
from copy import deepcopy


def com_desconto(produtos):
    copia = deepcopy(produtos)
    for p in copia:
        if p["preco"] > 10:
            p["preco"] *= 0.9
    return copia
```

A primeira é mais rápida e declara o que muda. A segunda é mais fácil de
ler e paga em desempenho por copiar tudo, inclusive o que não interessa.

A terceira forma, que o exercício não pede e é a que o projeto vai usar: não
mexer em dicionário nenhum, e sim em objetos com tipo próprio, do capítulo
@cap:tipagem-e-dataclasses, onde "criar uma versão modificada" é uma
operação com nome.
:::
