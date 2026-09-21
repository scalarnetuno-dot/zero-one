---
title: "Repetições"
number: 6
slug: repeticoes
part: p1
kicker: "Em Python não se conta índice. Se percorre — e essa diferença muda o que você consegue escrever."
goal: >-
  Percorrer coleções com `for`, repetir com `while`, sair no meio com
  `break`, e reconhecer quando um laço deveria ser uma expressão.
---

Quase toda outra linguagem ensina o laço assim: crie um contador, teste o
contador, incremente o contador, use o contador como índice. Python ensina
diferente, e a diferença não é cosmética.

```python title="catalogo.py" numbered
produtos = ["Tomate", "Alface", "Cenoura"]

for produto in produtos:
    print(produto)
```

```text
Tomate
Alface
Cenoura
```

Não há índice, não há `i`, não há `len`. O `for` do Python percorre os
**itens** diretamente. Onde não há índice, não há como errar o índice — e
metade dos defeitos clássicos de laço simplesmente não tem onde existir.

:::pitfall
Se você escreveu `for i in range(len(produtos)):` e depois usou
`produtos[i]`, você trouxe o hábito de outra linguagem. Funciona, é mais
longo e é a única forma de escrever um `IndexError` num laço Python. Só use
índice quando o índice for o assunto — e mesmo aí existe `enumerate`.
:::

## `range`: quando o assunto é o número

```python title="range.py" numbered
for n in range(3):
    print(n)
```

```text
0
1
2
```

`range(3)` produz `0, 1, 2`: começa no zero e **exclui** o fim. Essa
exclusão parece arbitrária e não é — ela faz `range(len(x))` cobrir
exatamente os índices válidos, e faz `range(a, b)` ter sempre `b - a`
elementos.

| Escrita | Produz |
|---|---|
| `range(5)` | `0 1 2 3 4` |
| `range(2, 5)` | `2 3 4` |
| `range(0, 10, 2)` | `0 2 4 6 8` |
| `range(5, 0, -1)` | `5 4 3 2 1` |

Tabela: Início incluído, fim excluído, passo opcional. A mesma regra vale
para fatias de lista, no capítulo @cap:estruturas-de-dados.

:::trivia
Por que o fim é excluído? Edsger Dijkstra escreveu um bilhete de uma página
sobre isso em 1982, o EWD831, defendendo a convenção `a <= i < b` com dois
argumentos: só ela deixa o intervalo vazio sem usar número negativo, e só
ela faz intervalos adjacentes se encaixarem sem sobreposição —
`range(0,3)` e `range(3,6)` cobrem tudo, sem repetir o 3. Python, C, Java e
Go seguem esse bilhete até hoje.
:::

## `enumerate` e `zip`

Quando você precisa do item **e** da posição:

```python title="enumerate.py" numbered
produtos = ["Tomate", "Alface", "Cenoura"]

for i, produto in enumerate(produtos, start=1):
    print(f"{i}. {produto}")
```

```text
1. Tomate
2. Alface
3. Cenoura
```

E quando precisa percorrer duas listas em paralelo:

```python title="zip.py" numbered
nomes = ["Tomate", "Alface"]
precos = [8.90, 3.50]

for nome, preco in zip(nomes, precos):
    print(f"{nome}: R$ {preco:.2f}")
```

:::pitfall
Duas listas paralelas, mantidas à mão, é um problema esperando acontecer: no
dia em que alguém apagar um item de uma e esquecer a outra, o `zip` vai
parar na mais curta, sem reclamar, e o catálogo vai ficar com preço trocado.
A solução estrutural — uma lista de objetos, em vez de várias listas
paralelas — é o assunto do capítulo @cap:classes-e-objetos.
:::

## O acumulador

O padrão mais comum de laço não imprime nada: ele constrói um valor.

```python title="totais.py" numbered
precos = [8.90, 3.50, 12.00, 5.25]

total = 0.0
caros = 0

for preco in precos:
    total += preco
    if preco > 10:
        caros += 1

print(f"total R$ {total:.2f}, {caros} acima de 10")
```

```text
total R$ 29.65, 1 acima de 10
```

Somar, contar e filtrar são o mesmo esqueleto: uma variável criada **antes**
do laço, modificada **dentro** dele, lida **depois**. Criar o acumulador
dentro do laço é o erro que zera o resultado a cada volta.

:::example Python já tem os acumuladores prontos
```python
print(sum(precos))
print(max(precos))
print(min(precos))
print(len(precos))
```
Somar à mão o que `sum` soma é escrever quatro linhas para não usar uma.
Escreva o laço quando a operação for sua; use a função embutida quando ela
for a de todo mundo.
:::

## `while`: repetir enquanto

`for` percorre uma coleção conhecida. `while` repete enquanto uma condição
for verdadeira — e a diferença prática é que ele pode nunca terminar.

```python title="reposicao.py" numbered
estoque = 3

while estoque > 0:
    print(f"vendendo... restam {estoque}")
    estoque -= 1

print("acabou")
```

:::diagram type="flowchart" caption="O laço é uma decisão que volta para si mesma."
nodes:
  - { id: ini, type: start,    text: "Início" }
  - { id: d1,  type: decision, text: "estoque > 0?" }
  - { id: c,   type: process,  text: "vende e decrementa" }
  - { id: fim, type: start,    text: "acabou" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: c,   label: "sim" }
  - { from: c,   to: d1 }
  - { from: d1,  to: fim, label: "não" }
:::

A linha `estoque -= 1` é a que faz o laço terminar. Apague-a e o programa
imprime para sempre — não trava, não dá erro, apenas continua, consumindo
processador até alguém interromper com `Ctrl+C`.

:::warning
Todo `while` precisa de uma resposta escrita para a pergunta *"o que, aqui
dentro, torna a condição falsa algum dia?"*. Se a resposta depender de algo
externo — rede, arquivo, usuário —, o laço precisa também de um limite de
tentativas. Laço infinito em servidor não quebra o seu programa: quebra o
servidor inteiro, e leva junto as requisições de todo mundo.
:::

:::art caption="Um laço que nunca termina tem o mesmo efeito de uma reunião que nunca termina."
Charge editorial minimalista em fundo branco: uma sala de reunião com uma
mesa oval e quatro pessoas sentadas, todas com a mesma expressão de cansaço,
e no relógio da parede os ponteiros desenhados como uma seta circular que
volta para si mesma. Na tela de projeção, um gráfico que se repete
infinitamente até sair do quadro. Uma pessoa em pé junto à porta, com a mão
na maçaneta, olhando para trás. Poucos elementos, humor seco, estética de
revista de tecnologia.
:::

## Sair no meio: `break` e `continue`

```python title="busca.py" numbered
produtos = ["Tomate", "Alface", "Cenoura", "Alface"]

for produto in produtos:
    if produto == "Cenoura":
        print("achei")
        break
```

`break` abandona o laço na hora. `continue` pula para a volta seguinte:

```python title="pulando.py" numbered
for preco in [8.90, -1, 3.50, 0, 12.00]:
    if preco <= 0:
        continue
    print(f"R$ {preco:.2f}")
```

Os dois servem à mesma ideia da cláusula de guarda do capítulo
@cap:condicionais: resolver o caso chato cedo e deixar o corpo principal
raso.

## O `else` do laço

Esta é uma peculiaridade do Python que confunde até quem programa há anos:

```python title="for_else.py" numbered
for produto in produtos:
    if produto == "Beterraba":
        print("achei")
        break
else:
    print("não existe no catálogo")
```

O `else` de um `for` roda quando o laço termina **sem** `break`. O nome é
infeliz — deveria ser `nobreak` — e por isso muita gente lê errado na
primeira vez. Mas ele resolve com elegância o problema clássico da busca,
que sem ele exige uma variável de bandeira:

:::compare left="Com bandeira" right="Com for/else" lang="python"
achou = False
for p in ps:
    if p == alvo:
        achou = True
        break
if not achou:
    aviso()
---
for p in ps:
    if p == alvo:
        break
else:
    aviso()
:::

## Quando o laço deveria ser uma expressão

Boa parte dos laços que constroem uma lista nova a partir de outra pode
virar uma linha:

```python title="comprehension.py" numbered
precos = [8.90, 3.50, 12.00, 5.25]

com_margem = [p * 1.12 for p in precos]
caros = [p for p in precos if p > 10]
```

Isso é uma *list comprehension*, e lê-se na ordem em que foi escrita: *"o
preço vezes 1,12, para cada preço em precos"*. É a construção mais
característica do Python, e o capítulo @cap:estruturas-de-dados volta a ela
com calma.

:::key
A regra prática: se o laço **transforma** uma coleção em outra, a
comprehension é mais clara. Se ele **faz coisas** — grava, imprime, chama
serviço —, o `for` normal é mais claro. Comprehension com efeito colateral
dentro é a pior das duas opções.
:::

## Sobre laço aninhado

```python title="aninhado.py" numbered
for produtor in produtores:
    for produto in produtor.produtos:
        print(produtor.nome, produto.nome)
```

Dois níveis são legítimos e comuns. O que vale saber desde já é o custo:
cem produtores com cem produtos cada são dez mil voltas. Se dentro do laço
interno houver uma consulta ao banco, são dez mil consultas — e esse defeito
tem nome, N+1, e um capítulo inteiro reservado para ele, o
@cap:relacionamentos.

:::summary
- `for item in colecao` percorre itens, não índices.
- `range` inclui o início e exclui o fim; o mesmo vale para fatias.
- `enumerate` dá posição, `zip` percorre duas coleções em paralelo.
- Acumulador nasce antes do laço, muda dentro, é lido depois.
- Todo `while` precisa de algo que torne a condição falsa.
- `else` de laço roda quando não houve `break`.
- Laço que transforma coleção quer virar comprehension.
:::

:::checkpoint
Você percorre coleções, repete sob condição, sai no meio quando precisa e
consegue explicar por que quase nunca escreve `range(len(x))`.
:::

:::exercise level=1
Imprima a tabuada de 7, de 1 a 10, no formato `7 x 3 = 21`.

:::answer
```python
for n in range(1, 11):
    print(f"7 x {n} = {7 * n}")
```
`range(1, 11)` e não `range(1, 10)`: o fim é excluído, então parar no 10
exige pedir 11.
:::

:::exercise level=2
Dada a lista de caixas entregues por dia numa semana
`[12, 0, 8, 15, 0, 22, 4]`, imprima o total, a média, o melhor dia (pela
posição, começando em 1) e quantos dias não houve entrega.

:::answer
```python
caixas = [12, 0, 8, 15, 0, 22, 4]

total = sum(caixas)
media = total / len(caixas)
melhor = caixas.index(max(caixas)) + 1
parados = sum(1 for c in caixas if c == 0)

print(f"total {total}, média {media:.1f}")
print(f"melhor dia: {melhor}, {parados} dias parados")
```
O `sum(1 for ...)` é o jeito curto de contar quantos itens satisfazem uma
condição — vale aprender, porque aparece muito.
:::

:::exercise level=3
Escreva um programa que descubra o primeiro produto do catálogo com estoque
zerado e imprima o nome; se não houver nenhum, imprima `catálogo completo`.
Escreva de duas formas — com variável de bandeira e com `for/else` — e diga
qual você deixaria no projeto.

:::answer
```python
for produto in catalogo:
    if produto["estoque"] == 0:
        print(produto["nome"])
        break
else:
    print("catálogo completo")
```

A forma com `for/else` é mais curta e não cria uma variável que existe só
para lembrar de uma coisa. A forma com bandeira é mais explícita para quem
nunca viu `for/else` — e esse é o argumento sério contra ela.

A decisão honesta depende do time: num código que várias pessoas mantêm, uma
construção que exige explicação é uma dívida pequena e recorrente. Eu deixo
o `for/else` e escrevo um comentário de uma linha na primeira vez que ele
aparece no projeto. O que não se faz é misturar as duas no mesmo arquivo.
:::
