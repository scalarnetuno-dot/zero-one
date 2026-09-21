---
title: "Funções"
number: 7
slug: funcoes
part: p1
kicker: "Dar nome a um pedaço de trabalho é a primeira decisão de arquitetura que alguém toma."
goal: >-
  Escrever funções com parâmetros, valores padrão e retorno; entender o
  escopo dos nomes; e evitar a armadilha de valor padrão mutável, que é a
  mais famosa da linguagem.
---

Uma regra que mora em dez lugares muda em nove. Função é o instrumento que
impede isso: um nome, um lugar, uma definição.

```python title="precos.py" numbered
def com_margem(preco):
    return preco * 1.12


print(com_margem(8.90))
print(com_margem(3.50))
```

```text
9.968
3.92
```

`def`, nome, parênteses, dois-pontos, corpo indentado. `return` devolve o
valor e encerra a função na hora — o que vier depois dele não roda.

:::anatomy title="As partes de uma função"
lang: python
code: |
  def com_margem(preco, taxa=0.12):
      """Aplica a margem da cooperativa."""
      return preco * (1 + taxa)
notes:
  - { line: 1, text: "`def` abre a definição; o nome é `snake_case` e costuma ser um verbo." }
  - { line: 1, text: "`preco` é obrigatório: quem chama precisa informar." }
  - { line: 1, text: "`taxa=0.12` é opcional: o valor padrão vale se ninguém disser nada." }
  - { line: 2, text: "A *docstring* é a primeira linha do corpo e vira documentação de verdade." }
  - { line: 3, text: "`return` devolve e sai; sem ele, a função devolve `None`." }
:::

## Toda função devolve alguma coisa

Em Python não existe `void`. Uma função sem `return` devolve `None` — e isso
é visível:

```text
>>> def avisar(msg):
...     print(msg)
...
>>> x = avisar("oi")
oi
>>> print(x)
None
```

Essa é a origem de um erro comum e confuso:

```text
Traceback (most recent call last):
  File "app.py", line 8, in <module>
    print(total.quantidade)
AttributeError: 'NoneType' object has no attribute 'quantidade'
```

`'NoneType' object has no attribute` quase sempre significa: *uma função que
você chamou esqueceu o `return`*. Guarde essa tradução; ela economiza muito
tempo.

## Argumentos por nome

```python title="chamadas.py" numbered
def registrar(produto, quantidade, conferido=False):
    ...


registrar("Tomate", 12)
registrar("Tomate", 12, True)
registrar("Tomate", quantidade=12, conferido=True)
registrar(quantidade=12, produto="Tomate")
```

Os argumentos podem ser passados por **posição** ou por **nome**. Os
nomeados podem vir em qualquer ordem, desde que venham depois dos
posicionais.

:::key
Quando uma chamada tem um `True` ou um `False` solto, nomeie o argumento.
`registrar("Tomate", 12, True)` obriga quem lê a abrir a função para saber o
que é esse `True`. `registrar("Tomate", 12, conferido=True)` não obriga
ninguém a nada. É o melhoramento de legibilidade mais barato que existe.
:::

Você pode **exigir** isso de quem chama, com um `*` solitário na assinatura:

```python title="so_por_nome.py" numbered
def registrar(produto, quantidade, *, conferido=False):
    ...


registrar("Tomate", 12, True)            # TypeError
registrar("Tomate", 12, conferido=True)  # ok
```

Tudo que vier depois do `*` só pode ser passado por nome. Em código de
biblioteca isso é quase obrigatório: impede que alguém dependa da ordem dos
parâmetros, e te deixa livre para reordená-los depois.

## A armadilha do padrão mutável

Esta é a pegadinha mais famosa do Python, e vale conhecer antes de cair
nela.

```python title="defeito.py" numbered
def adicionar(item, lista=[]):
    lista.append(item)
    return lista


print(adicionar("Tomate"))
print(adicionar("Alface"))
```

O esperado seria `['Tomate']` e depois `['Alface']`. O que sai é:

```text
['Tomate']
['Tomate', 'Alface']
```

A razão: **o valor padrão é avaliado uma vez só**, quando a função é
definida — não a cada chamada. Existe uma única lista, criada na importação
do módulo, e todas as chamadas compartilham ela. Ela vai crescendo durante
todo o tempo em que o programa estiver no ar.

A forma correta usa `None` como sinal:

```python title="correto.py" numbered
def adicionar(item, lista=None):
    if lista is None:
        lista = []
    lista.append(item)
    return lista
```

:::warning
A regra é simples e não tem exceção: **valor padrão só pode ser imutável**.
Número, texto, booleano, `None`, tupla. Nunca lista, dicionário, conjunto ou
objeto. Se o seu editor tem um *linter* configurado — e ele deve ter —, essa
é uma das primeiras coisas que ele reclama.
:::

:::story A lista que crescia sozinha
O relatório de conferência da terça mostrava 8 itens. O da quarta, 19. O da
quinta, 31.

— Está entrando dado duplicado — disse Rafa.

Bia conferiu o banco. Não estava. Os dados estavam certos.

Elias abriu o arquivo do relatório, rolou até a terceira função e leu em voz
alta, sem tom nenhum:

— `def montar(item, acumulado=[])`.

— O que tem?

— Tem que essa lista nasceu na segunda-feira, quando o servidor subiu. E
nunca mais morreu.

Bia olhou por uns segundos.

— Então o relatório da quinta tem os itens de terça dentro.

— Tem os itens de terça, de quarta e de quinta. Na ordem. — Elias apontou
para a tela. — E vai ter os de sexta.
:::

## `*args` e `**kwargs`

Quando a função aceita um número variável de argumentos:

```python title="variaveis.py" numbered
def total(*precos):
    return sum(precos)


print(total(8.90, 3.50, 12.00))   # 24.4
print(total())                    # 0
```

`*precos` recolhe todos os argumentos posicionais numa tupla. O irmão dele
recolhe os nomeados num dicionário:

```python title="kwargs.py" numbered
def registrar(**campos):
    for chave, valor in campos.items():
        print(f"{chave}: {valor}")


registrar(produto="Tomate", caixas=12)
```

Os nomes `args` e `kwargs` são convenção, não sintaxe: o que importa é o `*`
e o `**`. Você vai encontrá-los muito em código de framework — e vai
encontrá-los pouco em código de aplicação, onde parâmetro explícito quase
sempre é melhor.

:::pitfall
`**kwargs` numa função sua costuma ser uma desculpa para não decidir quais
são os parâmetros. Ele apaga a assinatura: o editor para de sugerir, o
verificador de tipos para de conferir, e quem lê precisa ler o corpo inteiro
para saber o que a função aceita. Use quando estiver repassando argumentos
para outra função; não use para adiar uma decisão de projeto.
:::

## Escopo: onde um nome existe

```python title="escopo.py" numbered
taxa = 0.12


def com_margem(preco):
    resultado = preco * (1 + taxa)
    return resultado


print(com_margem(8.90))
print(resultado)   # NameError
```

`resultado` nasce dentro da função e morre com ela. `taxa`, que está fora,
pode ser **lida** de dentro. Mas atribuir a ela é outra história:

```python
def mudar():
    taxa = 0.20   # cria uma NOVA taxa, local
```

A atribuição dentro de uma função sempre cria um nome local, a menos que
você declare `global taxa` — e a necessidade de escrever `global` é quase
sempre o sinal de que aquele valor deveria ser um parâmetro, ou um atributo
de objeto.

:::key
Função que lê variável global é função que não pode ser testada sozinha,
nem chamada duas vezes com confiança. A regra que o livro segue do capítulo
@cap:service em diante: **tudo que a função precisa, entra por parâmetro;
tudo que ela produz, sai por retorno**.
:::

## Docstring: a documentação que não desatualiza sozinha

```python title="docstring.py" numbered
def com_margem(preco, taxa=0.12):
    """Aplica a margem da cooperativa sobre o preço do produtor.

    O padrão de 12% vem do estatuto; produtos certificados usam 8%.
    """
    return preco * (1 + taxa)
```

A docstring é a primeira coisa no corpo, entre três aspas. Ela não é
comentário: ela fica acessível em execução, em `com_margem.__doc__`, e é o
que aparece quando alguém digita `help(com_margem)` no REPL.

No capítulo @cap:openapi essa mesma docstring vira a descrição do endpoint
na documentação da API, sem que você escreva uma linha a mais. Essa é a
recompensa concreta de escrevê-la.

## Um aperitivo de tipos

Você pode — e, neste livro, a partir de certo ponto, **deve** — anotar o
tipo dos parâmetros e do retorno:

```python title="tipado.py" numbered
def com_margem(preco: float, taxa: float = 0.12) -> float:
    return preco * (1 + taxa)
```

O Python ignora essas anotações em execução: elas não convertem nada e não
recusam nada. Quem as usa são o seu editor, o verificador de tipos e — o que
interessa a este livro — o FastAPI, que as lê para gerar validação e
documentação. O capítulo @cap:tipagem-e-dataclasses trata disso a sério.

:::summary
- Função sem `return` devolve `None`; `'NoneType' has no attribute` quase
  sempre é isso.
- Argumento nomeado na chamada documenta o valor no lugar onde ele é lido.
- Valor padrão é avaliado uma vez só: nunca use lista ou dicionário como
  padrão.
- `*args` e `**kwargs` são para repassar, não para adiar decisão.
- Atribuição dentro da função cria nome local; precisar de `global` é um
  sintoma.
- Docstring é documentação executável — e no fim do livro vira a da API.
:::

:::exercise level=1
Escreva uma função `frete(caixas, por_caixa=4.0, minimo=12.0)` que calcule o
frete de uma entrega e nunca devolva menos que o mínimo. Teste com 1 e com
10 caixas.

:::answer
```python
def frete(caixas, por_caixa=4.0, minimo=12.0):
    return max(caixas * por_caixa, minimo)


print(frete(1))    # 12.0
print(frete(10))   # 40.0
```
`max` expressa "nunca menos que" melhor que um `if` de três linhas — desde
que o leitor faça essa tradução na cabeça, e aqui ele faz.
:::

:::exercise level=2
A função abaixo deveria devolver o nome em maiúsculas. Ela devolve `None`.
Conserte e explique.

```python
def gritar(nome):
    nome.upper()
```

:::answer
Falta o `return`. Mas há um segundo erro escondido dentro do primeiro:
mesmo que alguém "consertasse" escrevendo `nome = nome.upper()` sem
`return`, continuaria devolvendo `None` — porque métodos de texto não
alteram o original, como vimos no capítulo @cap:variaveis-e-tipos.

```python
def gritar(nome):
    return nome.upper()
```
:::

:::exercise level=3
Escreva uma função `resumo` que receba uma lista de preços e devolva total,
média e o maior valor. Decida o que ela devolve — três valores soltos, uma
tupla, um dicionário — e justifique a escolha pensando em quem vai chamar a
função daqui a seis meses.

:::answer
```python
def resumo(precos):
    if not precos:
        return {"total": 0.0, "media": 0.0, "maior": 0.0}
    total = sum(precos)
    return {
        "total": total,
        "media": total / len(precos),
        "maior": max(precos),
    }
```

Python permite `return total, media, maior`, e quem chama escreve
`t, m, x = resumo(precos)`. É conciso e tem um custo: a ordem vira contrato.
No dia em que alguém acrescentar "menor" no meio, todo código que chamava a
função passa a ler valores trocados — sem erro, sem aviso.

O dicionário nomeia cada valor e sobrevive a acréscimos. A lista vazia
merece decisão explícita: sem o `if`, `max([])` levanta `ValueError` e
`total / 0` levanta `ZeroDivisionError`.

A melhor resposta de todas é um tipo com nome próprio: o `dataclass` que
carrega os dados e o contrato no mesmo lugar. Ele tem
as vantagens do dicionário e ainda avisa quando alguém escreve `.mdia`.
:::
