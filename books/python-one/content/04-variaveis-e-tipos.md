---
title: "Variáveis e tipos"
number: 4
slug: variaveis-e-tipos
part: p1
kicker: "O Python não pergunta o tipo. Isso não quer dizer que ele não se importe."
goal: >-
  Usar os tipos básicos com consciência, converter entre eles sem perder
  dado, saber por que `float` não serve para dinheiro e nomear variáveis
  como quem escreve para outra pessoa.
---

:::story O relatório que não fechava
— A diferença é de três reais e quarenta — disse a Dona Neuza, com o extrato
na mão. — Em doze mil.

A Bia conferiu a soma três vezes. O código estava certo. As entradas estavam
certas. A saída estava errada.

Foi o Elias quem olhou por cima do ombro, de passagem, e falou sem parar de
andar:

— Você está somando `float`.

— E daí?

— E daí que `float` é bom para peso de caminhão. Para dinheiro, ele inventa
sozinho a partir da décima casa, e você só descobre no fim do mês.

A Bia trocou quatro linhas. A diferença virou zero.

— Isso está escrito em algum lugar?

— Está em todo lugar — disse o Elias. — Só não está no tutorial.
:::

Em Python você não anuncia o tipo antes de usar o nome. Mesmo assim os tipos
existem, são rígidos e param o programa quando você os mistura.

A diferença não é *ter* ou *não ter* tipo. É **quando** a conferência
acontece. No relatório da Dona Neuza, ela acontece tarde demais: a soma
roda, o número sai, e o erro só aparece no extrato.

```python title="tipos.py" numbered
nome = "Tomate italiano"
preco = 8.90
estoque = 120
organico = True
produtor = None

print(type(nome), type(preco), type(estoque))
print(type(organico), type(produtor))
```

```text
<class 'str'> <class 'float'> <class 'int'>
<class 'bool'> <class 'NoneType'>
```

Cada valor carrega seu tipo consigo. A variável é só um nome apontando para
ele.

:::term Tipagem dinâmica
O tipo pertence ao **valor**, não ao nome. `x = 1` e depois `x = "um"` é
legal: o nome passou a apontar para outro valor, de outro tipo.
:::

:::term Tipagem forte
Valores de tipos diferentes não se misturam sozinhos. `"total: " + 120`
falha em Python, enquanto em JavaScript viraria `"total: 120"`. Dinâmico e
forte são coisas independentes — Python é as duas.
:::

## Os cinco tipos do dia a dia

| Tipo | Exemplo | Onde aparece no projeto |
|---|---|---|
| `str` | `"Tomate italiano"` | nome, descrição, e-mail |
| `int` | `120` | estoque, identificador, página |
| `float` | `8.90` | peso, percentual — **não** preço |
| `bool` | `True` | `ativo`, `organico` |
| `NoneType` | `None` | "não informado", "não encontrado" |

Tabela: Há muitos outros tipos em Python. Estes cinco cobrem quase todo
campo de uma tabela de banco de dados.

Repare em `True` com T maiúsculo. É uma das poucas maiúsculas obrigatórias
da linguagem, junto com `False` e `None`, e errá-la dá `NameError`.

## `None` não é zero, nem vazio, nem falso

`None` é o valor que significa *"não há valor"*. Ele merece um parágrafo
próprio porque o descuido com ele é a causa número um de quedas de API em
produção.

```python
estoque = 0       # sei o estoque: é zero
estoque = None    # não sei o estoque
```

São afirmações completamente diferentes, e um relatório que soma as duas
como se fossem a mesma coisa está mentindo. Quando o dado vier de fora,
alguém vai ter que decidir se o campo é obrigatório, se pode faltar, ou se
tem um valor padrão. As três decisões produzem três programas diferentes. O
`None` é o jeito de dizer "este aqui falta", e misturá-lo com zero é
decidir, em silêncio, que falta é o mesmo que nada devido.

:::pitfall
`if estoque:` é falso quando o estoque é `0` **e** quando é `None`. Se as
duas situações exigem respostas diferentes — e quase sempre exigem —,
escreva `if estoque is None:`. Use `is`, não `==`: `None` é único no
programa inteiro, e comparar identidade é mais barato e mais honesto.
:::

## O caso do dinheiro

Abra o REPL e digite isto:

```text
>>> 0.1 + 0.2
0.30000000000000004
>>> 8.90 * 3
26.700000000000003
```

Isso não é bug do Python. É como todo computador representa número com
vírgula: em base 2, e `0.1` em base 2 é uma dízima infinita, do mesmo jeito
que `1/3` é infinita em base 10. O computador guarda uma aproximação boa, e
a aproximação erra na décima sétima casa.

Na décima sétima casa ninguém se importa. O problema é que o erro se acumula
e chega na segunda:

```python title="por_que_nao_float.py" numbered
total = 0.0
for _ in range(1000):
    total += 8.90

print(total)
```

```text
8900.000000000226
```

Duzentos e vinte e seis bilionésimos de real. Somados numa fatura de mil
itens, viram a reunião em que alguém pergunta por que o sistema e a planilha
discordam em centavos.

A resposta é `Decimal`:

```python title="com_decimal.py" numbered
from decimal import Decimal

total = Decimal("0.00")
for _ in range(1000):
    total += Decimal("8.90")

print(total)
```

```text
8900.00
```

:::key
`Decimal` recebe o valor como **texto**: `Decimal("8.90")`, com aspas.
`Decimal(8.90)` sem aspas nasce do `float` que já está errado e carrega o
erro junto — é o engano clássico de quem acabou de descobrir o `Decimal`.
:::

:::history
O padrão que rege o `float` do Python, o IEEE 754, é de 1985 e foi obra de
um comitê liderado por William Kahan, que ganhou o prêmio Turing por isso.
Ele resolveu um caos: antes, cada fabricante de processador arredondava do
seu jeito e o mesmo cálculo dava resultados diferentes em máquinas
diferentes. O `0.30000000000000004` não é um defeito do padrão — é o padrão
funcionando, e funcionando igual em toda parte.
:::

Todo preço da cooperativa, daqui em diante, é `Decimal`. Use `float` para
peso, temperatura, percentual e média. Para dinheiro, nunca. O banco, quando
entrar, guarda esse valor como número de precisão marcada — não como o
`float` que acabou de mentir três reais e quarenta.

## Conversão explícita

O Python não converte sozinho — mas converte quando você pede:

```python title="conversao.py" numbered
entrada = "120"

estoque = int(entrada)
print(estoque + 5)
```

```text
125
```

E quando o texto não é um número, ele recusa com clareza:

```text
Traceback (most recent call last):
  File "conversao.py", line 3, in <module>
    estoque = int("cento e vinte")
ValueError: invalid literal for int() with base 10: 'cento e vinte'
```

`ValueError` é o erro de "tipo certo, valor impossível". Quem mandou
`"cento e vinte"` não mandou um número. A resposta honesta é recusar o
pedido e dizer o que está errado — não deixar a falha seguir até virar um
erro genérico lá na frente.

| Conversão | O que acontece com o resto |
|---|---|
| `int("120")` | `120` |
| `int(8.90)` | `8` — trunca, não arredonda |
| `round(8.90)` | `9` — arredonda |
| `float("8.9")` | `8.9` |
| `str(120)` | `"120"` |

Tabela: `int()` corta a parte decimal fora. Quem quer arredondar pede
`round`; confundir os dois já custou estoque a muita gente.

:::diagram type="cells" caption="Uma variável é um nome preso a um valor — e o tipo mora no valor, não no nome."
items: ["\"Tomate\"", "8.90", "120", "True", "None"]
orientation: horizontal
notes:
  - { at: 0, text: "str" }
  - { at: 1, text: "float" }
  - { at: 4, text: "NoneType" }
:::

## Texto é imutável

Uma propriedade que surpreende: em Python, `str` não pode ser alterada no
lugar.

```text
>>> nome = "tomate"
>>> nome[0] = "T"
TypeError: 'str' object does not support item assignment
```

O que se faz é criar outro texto:

```python
nome = "tomate"
nome = nome.capitalize()   # "Tomate"
```

Os métodos de texto **nunca** alteram o original; todos devolvem um novo. Os
que você vai usar o tempo todo:

```python title="metodos_de_texto.py" numbered
bruto = "  Tomate Italiano \n"

print(bruto.strip())          # tira espaço e quebra das pontas
print(bruto.strip().lower())  # tudo minúsculo
print("8,90".replace(",", "."))
print("tomate,120,8.90".split(","))
```

```text
Tomate Italiano
tomate italiano
8.90
['tomate', '120', '8.90']
```

:::practice
Rode `"  Tomate ".strip()` e, na linha seguinte, imprima a variável
original. Ela continua com os espaços. Essa é a demonstração de um segundo:
o método devolve, não modifica.
:::

## `==` compara valor, `is` compara identidade

```text
>>> a = "tomate"
>>> b = "tom" + "ate"
>>> a == b
True
>>> a is b
False
```

`==` pergunta *"têm o mesmo conteúdo?"*. `is` pergunta *"são o mesmo objeto
na memória?"*.

:::pitfall
Às vezes `is` parece funcionar com texto e número pequeno, porque o Python
reaproveita objetos iguais por otimização. Isso é detalhe de implementação,
muda entre versões e transforma um teste verde em mentira. Use `is` só para
`None`, `True` e `False`; para todo o resto, `==`.
:::

## Nomes

Python tem uma convenção forte e universal, escrita num documento chamado
PEP 8:

| O quê | Como | Exemplo |
|---|---|---|
| variável e função | minúsculas com `_` | `preco_base` |
| constante | maiúsculas com `_` | `MARGEM_PADRAO` |
| classe | inicial maiúscula | `Produto` |
| privado por convenção | começa com `_` | `_cache` |

Tabela: A convenção é `snake_case`, não `camelCase`. Quem vem do Java leva
duas semanas para se acostumar e nunca mais volta.

Sobre constante: o Python **não tem** constante de verdade. `MARGEM_PADRAO =
1.12` continua sendo uma variável que qualquer linha pode reatribuir. As
maiúsculas são um recado para o humano — e, na prática, são obedecidas.

:::summary
- O tipo pertence ao valor; a conferência acontece na execução, não antes.
- Python é dinâmico **e** forte: não converte sozinho entre tipos.
- `None` não é zero nem vazio; compare com `is None`.
- Dinheiro é `Decimal`, criado a partir de texto. `float` é para medida.
- `str` é imutável: todo método devolve um novo texto.
- `is` só para `None`, `True` e `False`.
:::

:::checkpoint
Você declara variáveis dos cinco tipos básicos, converte entre eles com
segurança, sabe o que fazer quando a conversão falha e consegue defender em
uma reunião por que o preço não é `float`.
:::

:::exercise level=1
Crie três variáveis descrevendo um produto do catálogo — nome, preço e se é
orgânico — e imprima uma linha no formato
`Tomate italiano — R$ 8,90 (orgânico)`. Use vírgula como separador decimal.

:::answer
```python
from decimal import Decimal

nome = "Tomate italiano"
preco = Decimal("8.90")
organico = True

texto = f"{preco:.2f}".replace(".", ",")
selo = "orgânico" if organico else "convencional"
print(f"{nome} — R$ {texto} ({selo})")
```
Formatar primeiro e trocar o ponto por vírgula depois é a forma mais direta.
A alternativa é usar o módulo `locale`, que depende do sistema operacional
estar configurado — em servidor, quase nunca está.
:::

:::exercise level=2
O programa abaixo deveria somar o estoque de duas entregas, mas imprime
`1218`. Explique e conserte.

```python
entrega_1 = "12"
entrega_2 = "18"
print(entrega_1 + entrega_2)
```

:::answer
Os dois valores são texto, e `+` entre textos concatena. O Python não está
errado: ele está fazendo exatamente o que você pediu para dois `str`.

```python
print(int(entrega_1) + int(entrega_2))   # 30
```

Este é o defeito mais comum de programa que lê dado de fora: **tudo que
entra é texto**. Formulário, arquivo, terminal, corpo de requisição — texto.
Converter na entrada é o trabalho do capítulo @cap:validacao.
:::

:::exercise level=3
A cooperativa cobra 12% de margem. Um produto custa `R$ 8,90` ao produtor.
Calcule o preço final de duas formas — com `float` e com `Decimal` — e
imprima as duas com quatro casas decimais. Depois decida qual delas você
mandaria para a nota fiscal, e por quê.

:::answer
```python
from decimal import Decimal

com_float = 8.90 * 1.12
com_decimal = Decimal("8.90") * Decimal("1.12")

print(f"{com_float:.4f}")     # 9.9680
print(f"{com_decimal:.4f}")   # 9.9680
```

Nas quatro casas, as duas formas concordam — e é aí que mora a armadilha: o
`float` acerta quase sempre. Ele erra pouco, erra tarde e erra acumulado,
que é o pior jeito de errar, porque o defeito não aparece no teste e sim no
fechamento do mês.

Para a nota fiscal vai o `Decimal`, e com uma decisão a mais que o exercício
não pediu: o arredondamento. `Decimal` deixa você escolher a regra
explicitamente com `quantize`, enquanto o `float` arredonda pela regra que
o processador tiver. Em dinheiro, escolher a regra é obrigação, não luxo.
:::
