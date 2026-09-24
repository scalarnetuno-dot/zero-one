---
title: "Operadores"
number: 5
slug: operadores
part: p1
kicker: "Os símbolos são os de sempre. As regras por trás deles é que não são."
goal: >-
  Calcular, comparar e combinar condições sem surpresa — inclusive nos três
  pontos em que o Python se comporta de um jeito que nenhuma outra linguagem
  popular se comporta.
---

:::story Três engradados e meio
— Sete caixas, de dois em dois — disse a Dona Neuza. — Quantos engradados?

A Bia escreveu `7 / 2` e mostrou a tela.

— Três e meio.

— Engradado não vem meio. O caminhão não leva meio. Me dá o inteiro e me diz
quantas caixas sobraram.

O Rafa, do lado, já tinha aberto o Python do galpão para conferir.

```text
$ python
Python 3.6.9
>>> 7 / 2
3
```

— Aqui dá três — ele disse, satisfeito.

— Na minha dá três e meio — disse a Bia.

O Elias nem virou a cadeira.

— Os dois estão certos. São dois Pythons. E o dela é o que a gente vai
entregar. Arruma a conta antes que o rótulo saia com meio engradado.
:::

Somar é `+`, subtrair é `-`, e isso qualquer planilha faz. O que muda a
manhã da Dona Neuza são os cantos: a divisão que devolve um tipo diferente
do que entrou, o `and` que não devolve verdadeiro ou falso, e a comparação
encadeada que só o Python tem.

## Aritmética: a divisão é o ponto

```python title="aritmetica.py" numbered
caixas = 7
por_engradado = 2

print(caixas / por_engradado)   # 3.5
print(caixas // por_engradado)  # 3
print(caixas % por_engradado)   # 1
print(caixas ** 2)              # 49
```

O primeiro resultado surpreende quem aprendeu a dividir em outra linguagem,
ou no Python 2 do galpão: `7 / 2` dá `3.5`, não `3`. Desde o Python 3, a
divisão com uma barra **sempre** devolve `float`, mesmo quando a conta é
exata:

```text
>>> 10 / 5
2.0
```

Repare no `2.0`. Isso importa quando o resultado vira índice de lista ou
identificador de banco, porque `float` não serve para nenhum dos dois.

Para dividir e continuar inteiro, use duas barras — a **divisão inteira**:

```text
>>> 10 // 3
3
>>> 7 // 2
3
```

E `%` devolve o resto, que é muito mais útil do que parece:

| Uso | Escrita | Resultado |
|---|---|---|
| É par? | `n % 2 == 0` | `True` / `False` |
| Últimos dois dígitos | `n % 100` | `1234` → `34` |
| Quantas sobram | `7 % 2` | `1` |
| Ciclo de tamanho N | `i % 7` | `0..6` |

Tabela: O resto é o operador que responde "sobrou?". Sete caixas de dois em
dois sobram uma — a conta que a Dona Neuza pediu quando a divisão deu meio
engradado.

:::trivia
A divisão com uma barra nem sempre devolveu `float`. No Python 2, `7 / 2`
dava `3`, e a mudança para `3.5` foi uma das decisões mais discutidas da
migração para o Python 3, em 2008. O argumento que venceu foi de quem ensina:
quase todo iniciante escrevia `media = soma / n` e recebia um número errado
sem nenhum aviso. Hoje a versão errada é a que precisa ser pedida, com duas
barras.
:::

:::pitfall
`//` arredonda **para baixo**, não para o zero. Com número negativo, isso
surpreende: `-7 // 2` é `-4`, e não `-3`. Se o que você quer é truncar em
direção ao zero, use `int(-7 / 2)`.
:::

## Atribuição composta

```python title="estoque.py" numbered
estoque = 120

estoque += 30    # 150
estoque -= 12    # 138
estoque *= 2     # 276
estoque //= 4    # 69
```

Não existe `++` em Python. Quem vem do C tenta, e o resultado é silencioso e
inútil: `++estoque` é lido como "positivo do positivo de estoque", que é o
próprio valor. O programa não quebra, só não faz nada — e é por isso que
esse engano sobrevive tanto tempo quando acontece.

## Comparação, e uma forma que só o Python tem

```python
print(preco > 10)
print(preco >= 10)
print(nome == "Tomate")
print(nome != "Tomate")
```

Até aqui, nada novo. O que é novo é isto:

```python title="faixa.py" numbered
preco = 8.90

if 5 <= preco <= 15:
    print("faixa popular")
```

A comparação encadeada existe e funciona como na matemática. Em quase toda
outra linguagem seria preciso escrever `preco >= 5 && preco <= 15`. Aqui, a
forma curta é também a forma correta — e `preco` é avaliado uma vez só, o
que importa quando o valor vem de uma chamada cara.

:::key
Comparação encadeada é uma das poucas coisas que o Python tem e as outras
linguagens não. Use — ela é mais legível, e legibilidade é o único argumento
de design que o Python aceita sem discutir.
:::

## `and`, `or`, `not` — e o que eles realmente devolvem

```python title="logica.py" numbered
ativo = True
estoque = 0

print(ativo and estoque > 0)   # False
print(ativo or estoque > 0)    # True
print(not ativo)               # False
```

Palavras, não símbolos: `and`, `or`, `not`, sem `&&`, `||` ou `!`. Até aí é
só sintaxe. O que é diferente de verdade está aqui:

```text
>>> "Tomate" and "Alface"
'Alface'
>>> "" or "sem nome"
'sem nome'
>>> 0 or None
None
```

`and` e `or` **não devolvem booleano**. Eles devolvem um dos dois operandos:
o que decidiu a questão. `a or b` entrega `a` se `a` for verdadeiro, senão
entrega `b`. E os dois **curto-circuitam**: se o primeiro já resolve, o
segundo nem é avaliado.

Isso vira um idioma muito usado:

```python
nome_exibido = nome or "(sem nome)"
```

:::pitfall
Esse idioma tem uma armadilha exatamente igual à do `if estoque:` do
capítulo @cap:variaveis-e-tipos. `desconto = desconto or 10` transforma um
desconto legítimo de `0` em `10`, porque `0` é falso. Quando o zero é um
valor válido — e em preço, estoque e desconto ele sempre é —, escreva a
condição inteira: `if desconto is None: desconto = 10`.
:::

O curto-circuito também é uma técnica de proteção:

```python
if produto is not None and produto.preco > 10:
    ...
```

Se `produto` for `None`, o Python nunca chega a `produto.preco` e o
`AttributeError` não acontece. A ordem dos dois lados, aqui, é o que separa
o código que roda do código que quebra.

## O que é verdadeiro

Todo valor Python responde a uma pergunta de verdade ou mentira. A regra
completa cabe numa frase: **vazio é falso, zero é falso, `None` é falso,
todo o resto é verdadeiro.**

| Falso | Verdadeiro |
|---|---|
| `False`, `None` | `True` |
| `0`, `0.0`, `Decimal("0")` | qualquer outro número |
| `""`, `[]`, `{}`, `()`, `set()` | qualquer coleção com um item |

Tabela: Os valores falsos formam uma lista curta e fechada. Vale decorá-la —
ela explica noventa por cento das condições que "funcionam quase sempre".

:::example Verificar lista vazia sem cerimônia
```python
produtos = []

if not produtos:
    print("catálogo vazio")
```
Escrever `if len(produtos) == 0:` funciona igual e é mais longo. A forma
curta é a idiomática, e em Python idiomático não é sinônimo de esperto: é
sinônimo de esperado.
:::

## `in`: a pergunta mais barata que existe

```python title="pertence.py" numbered
categorias = ["fruta", "legume", "verdura"]

print("fruta" in categorias)        # True
print("carne" not in categorias)    # True
print("mate" in "Tomate italiano")  # True
```

O mesmo operador pergunta "está na lista?", "é chave deste dicionário?" e "é
trecho deste texto?". Uma palavra, três perguntas — e é a forma como toda
busca simples é escrita em Python.

## O ternário, escrito ao contrário

Python tem expressão condicional, mas com a ordem das palavras invertida em
relação a quase todas as linguagens:

```python
selo = "orgânico" if organico else "convencional"
```

Lê-se como uma frase em inglês: *o valor é X se a condição, senão Y*. É útil
em atribuição curta e vira ilegível em qualquer coisa maior — se você
precisou aninhar dois, o lugar do código é um `if` de verdade.

:::compare left="Cabe" right="Não cabe" lang="python"
selo = "org" if bio else "conv"
---
x = ("a" if p else
     "b" if q else "c")
:::

## Precedência, e a saída honesta

A ordem das operações é a da matemática, com os operadores lógicos por
último:

```text
**            potência
* / // %      multiplicação e divisões
+ -           soma e subtração
< <= > >= ==  comparações
not
and
or
```

Saber isso de cor não é o objetivo. O objetivo é reconhecer quando a
expressão ficou dependente da tabela — e, nesse momento, colocar parênteses.

:::key
Parêntese é grátis e não tem custo em execução. Se duas pessoas na revisão
de código precisarem discutir a ordem de avaliação, o parêntese já deveria
estar lá.
:::

## O operador morsa

Uma adição recente, que você vai ver em código moderno:

```python title="morsa.py" numbered
produtos = buscar_produtos()

if (total := len(produtos)) > 100:
    print(f"catálogo grande: {total} itens")
```

O `:=` atribui **e** devolve o valor, permitindo usar o resultado na mesma
linha em que ele foi calculado. O nome oficial é *expressão de atribuição*;
o apelido, morsa, vem da cara do símbolo virado de lado.

Use com parcimônia: ele serve para evitar chamar duas vezes uma função cara
ou repetir uma expressão longa. Fora disso, torna a linha mais densa sem
ganhar nada.

:::summary
- `/` devolve `float` sempre; `//` é a divisão inteira e arredonda para
  baixo.
- `and` e `or` devolvem um dos operandos, não um booleano, e curto-circuitam.
- Vazio, zero e `None` são falsos; o resto é verdadeiro.
- `5 <= preco <= 15` é sintaxe válida e avalia `preco` uma vez só.
- `in` pergunta pertencimento em lista, dicionário e texto.
- Quando a ordem de avaliação virar assunto, ponha parênteses.
:::

:::exercise level=1
Um engradado leva 12 caixas. Dado um número de caixas, imprima quantos
engradados cheios saem e quantas caixas sobram.

:::answer
```python
caixas = 100

print(f"{caixas // 12} engradados cheios")
print(f"{caixas % 12} caixas sobrando")
```
```text
8 engradados cheios
4 caixas sobrando
```
`//` e `%` andam em par: um diz quantos couberam, o outro diz o que sobrou.
:::

:::exercise level=2
Escreva uma condição que aceite um produto para a vitrine de destaque
somente se ele estiver ativo, tiver estoque acima de 10 e preço entre 5 e 50
reais. Use comparação encadeada onde ela couber.

:::answer
```python
if ativo and estoque > 10 and 5 <= preco <= 50:
    print("vai para a vitrine")
```
A ordem dos testes também é uma decisão: colocar `ativo` primeiro faz o
Python descartar produto inativo sem avaliar mais nada. Em condição com
consulta ao banco no meio, essa ordem deixa de ser estilo e passa a ser
desempenho.
:::

:::exercise level=3
O código abaixo deveria aplicar o desconto informado, ou 5% quando nenhum
for informado. Ele tem um defeito que só aparece em um caso específico.
Encontre, conserte e diga quantas vendas por ano a empresa precisaria fazer
para que ninguém percebesse.

```python
desconto = desconto or 5
preco_final = preco * (1 - desconto / 100)
```

:::answer
O defeito aparece quando o desconto informado é `0` — um valor legítimo, que
significa "esta venda não tem desconto". Como `0` é falso, o `or` substitui
por `5`, e a empresa dá um desconto que ninguém autorizou.

```python
if desconto is None:
    desconto = 5
preco_final = preco * (1 - desconto / 100)
```

A segunda parte da pergunta é a parte séria: ninguém percebe **nunca**,
porque o resultado é um preço plausível. Não há erro na tela, não há log, não
há exceção. É um defeito que só a conferência contábil encontra, meses
depois — e o `or` do atalho foi escrito em uma linha, num dia comum, por
alguém que tinha certeza de estar sendo conciso.
:::
