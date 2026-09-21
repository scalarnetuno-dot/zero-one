---
title: "Condicionais"
number: 5
slug: condicionais
part: p1
kicker: "Escolher um caminho é assumir o outro — inclusive quando ele não está escrito."
goal: >-
  Escrever decisões com `if`, `elif` e `match`, escolher entre eles por
  intenção, e reconhecer o caminho implícito que todo `if` sem `else` deixa
  para trás.
---

Até agora o programa fazia sempre a mesma coisa. A partir daqui ele olha um
valor e escolhe. É a menor unidade de inteligência que um programa pode ter,
e cabe em três linhas.

```python title="entrada.py" numbered
estoque = 0

if estoque > 0:
    print("Disponível")
else:
    print("Em falta")
```

Dois-pontos no fim da condição, corpo indentado, `else` no mesmo nível do
`if`. Sem parênteses em volta da condição — eles são aceitos, mas escrevê-los
denuncia quem chegou de outra linguagem na semana passada.

## O caminho que você não escreveu

```python
if estoque > 0:
    print("Disponível")
```

Sem `else`, o caminho do "não" continua existindo — ele apenas não faz nada.
Ter consciência disso é o que separa o programa correto do programa que só
parece correto.

:::diagram type="flowchart" caption="Toda decisão tem dois caminhos, mesmo quando você escreve só um."
nodes:
  - { id: ini, type: start,    text: "Início" }
  - { id: d1,  type: decision, text: "estoque > 0?" }
  - { id: sim, type: process,  text: "Disponível" }
  - { id: nao, type: process,  text: "(nada)" }
  - { id: fim, type: start,    text: "Fim" }
edges:
  - { from: ini, to: d1 }
  - { from: d1,  to: sim, label: "sim" }
  - { from: d1,  to: nao, label: "não" }
  - { from: sim, to: fim }
  - { from: nao, to: fim }
:::

No capítulo @cap:tratamento-de-erros, quando a API tiver de responder `404`,
esse caminho vazio vira o defeito mais visível que existe: o cliente pede um
produto que não existe e recebe silêncio, ou pior, recebe `200` com corpo
vazio.

:::key
Antes de escrever um `if`, responda em voz alta: *"e se não?"*. Se a resposta
for "não acontece nada", escreva isso num comentário. Se for "não sei", você
acabou de encontrar um requisito que ninguém definiu.
:::

## A escada de `elif`

```python title="faixa.py" numbered
nota = 7.5

if nota >= 9:
    conceito = "Excelente"
elif nota >= 7:
    conceito = "Bom"
elif nota >= 5:
    conceito = "Regular"
else:
    conceito = "Insuficiente"

print(conceito)
```

É `elif`, não `else if` — e a abreviação existe por um motivo estrutural: em
Python, `else if` aninharia de verdade, aumentando um nível de indentação a
cada degrau, e uma escada de cinco faixas terminaria com vinte espaços de
recuo.

A ordem importa: o primeiro teste verdadeiro vence e os demais nem são
avaliados. Por isso a escada vai do valor mais alto para o mais baixo — na
ordem inversa, `nota >= 5` engoliria todos os casos acima dele.

:::pitfall
Uma escada com mais de quatro degraus é sinal de que falta um conceito. No
capítulo @cap:classes-e-objetos essa mesma faixa de notas vira um tipo com
nome próprio e a escada some. Quando você se pegar escrevendo o sexto
`elif`, pare e pergunte que tipo está faltando.
:::

:::story As trinta e sete combinações
Era para ser uma regra só.

— Se o produtor for certificado, a margem cai para oito por cento — disse
Dona Neuza.

Bia escreveu o `if`. Levou quatro minutos.

— E se for da agricultura familiar? — perguntou Rafa, na quinta-feira.

— Também oito.

Bia escreveu o segundo. Agora tinha um `elif`.

— E se for certificado **e** familiar?

Silêncio.

— Acumula? — arriscou Rafa.

— Não sei — disse Dona Neuza. — Pergunta pro conselho.

O conselho respondeu na terça seguinte: acumula, com teto de quinze por
cento, exceto em produto de fora do estado, exceto na primeira entrega do
produtor, exceto em safra de pico.

Bia foi ao quadro e desenhou a tabela de todas as combinações. Eram trinta e
sete.

— O problema não é Python — ela disse, tampando o pincel. — O problema é que
essa regra nunca foi escrita inteira em lugar nenhum. A gente vai ser a
primeira pessoa da história da cooperativa a descobrir qual ela é.
:::

:::art caption="Toda escada de `elif` começa com uma regra só."
Charge editorial minimalista em fundo branco: um quadro branco corporativo
inteiramente tomado por uma tabela de condições "SE... E SE... MAS SE...",
com dezenas de células e setas se cruzando. Uma desenvolvedora de pé ao
lado do quadro, pincel na mão, expressão resignada. Sentado, um estagiário
abraça o notebook contra o peito com olhar vazio. Uma coordenadora mais
velha, de costas, já saindo pela porta com o celular no ouvido. Poucos
elementos, composição limpa, humor visual seco.
:::

## Tratar o caso ruim primeiro

Existem duas formas de escrever a mesma decisão, e uma delas envelhece muito
melhor.

:::compare left="Aninhado" right="Cláusula de guarda" lang="python"
if produto is not None:
    if produto.ativo:
        if produto.estoque > 0:
            vender(produto)
---
if produto is None:
    return
if not produto.ativo:
    return
vender(produto)
:::

O lado direito chama-se **cláusula de guarda**: trate o caso ruim, saia, e
deixe o caminho feliz encostado na margem esquerda. O lado esquerdo cresce
para a direita a cada regra nova — e regra nova sempre aparece.

Essa forma é a espinha dorsal de todo serviço que você vai escrever a partir
do capítulo @cap:service. Uma função de API real começa com três ou quatro
guardas e termina com duas linhas de trabalho de verdade.

:::key
Se o corpo principal da sua função está com três níveis de indentação, quase
sempre faltam guardas no começo. Indentação profunda não é um problema
estético: é um relatório de quantas condições o leitor precisa manter na
cabeça ao mesmo tempo.
:::

## `match`: quando a pergunta é "qual destes?"

Python não tem `switch`. Desde a versão 3.10 ele tem algo melhor e mais
perigoso, o `match`:

```python title="prazo.py" numbered
tipo = "PIX"

match tipo:
    case "PIX":
        prazo = "imediato"
    case "CARTAO":
        prazo = "2 dias"
    case "BOLETO" | "TED":
        prazo = "3 dias úteis"
    case _:
        prazo = "desconhecido"

print(prazo)
```

Três coisas valem atenção. Não há `break`: cada `case` termina sozinho, sem
escorregar para o seguinte. O `|` agrupa valores. E o `_` é o caso padrão —
ele casa com qualquer coisa, e por convenção vem por último.

O `match` faz bem mais do que comparar valores: ele desmonta estruturas.

```python title="evento.py" numbered
evento = {"tipo": "entrega", "caixas": 12}

match evento:
    case {"tipo": "entrega", "caixas": int(n)} if n > 10:
        print(f"entrega grande: {n} caixas")
    case {"tipo": "entrega"}:
        print("entrega comum")
    case {"tipo": "devolucao"}:
        print("devolução")
```

O primeiro `case` só casa se o dicionário tiver `tipo` igual a `"entrega"`,
tiver `caixas` inteiro **e** esse inteiro for maior que dez — e ainda liga o
valor ao nome `n`. Isso se chama *pattern matching* estrutural, e é a
funcionalidade mais sofisticada que entrou no Python nesta década.

:::pitfall
Dentro de um `case`, um nome solto **não compara: atribui**. `case ativo:`
não pergunta se o valor é igual à variável `ativo` — ele captura o valor e
sobrescreve `ativo`, casando sempre. Para comparar com uma constante, ela
precisa estar qualificada: `case Status.ATIVO:`. Esse é o erro número um de
quem começa com `match`, e ele não gera erro nenhum: gera um `match` que
sempre entra no primeiro caso.
:::

## Qual usar

| Situação | Escolha |
|---|---|
| Uma condição com faixa | `if` |
| Duas ou três faixas ordenadas | escada de `elif` |
| Muitos valores exatos da mesma variável | `match` |
| Estrutura com formato a reconhecer | `match` com padrão |
| Escolher um valor entre dois | ternário |

Tabela: Não é questão de gosto: cada forma comunica uma intenção diferente
para quem lê depois.

## `pass`, e por que ele existe

Python não aceita bloco vazio. Isto é erro de sintaxe:

```python
if estoque == 0:
```

Quando você precisa de um bloco que não faz nada — um esqueleto ainda não
preenchido, um caso deliberadamente ignorado —, existe `pass`:

```python
if estoque == 0:
    pass  # o alerta de reposição entra na camada de serviço
```

`pass` é uma instrução que não faz absolutamente nada. Ela existe só para
satisfazer a gramática — e serve como marcador honesto de trabalho pendente,
desde que o comentário ao lado diga o que falta.

:::practice
Escreva um `if` com corpo vazio e rode. Leia o `IndentationError: expected
an indented block`. Essa é a mensagem que você vai receber toda vez que
apagar o corpo de um bloco e esquecer de apagar o cabeçalho — e reconhecê-la
de primeira economiza um minuto cada vez.
:::

## Um `if` que você vai escrever muito

O projeto deste livro é uma API, e uma API passa o dia respondendo a uma
pergunta só: *isso existe?* A forma dessa decisão, em Python, é esta:

```python title="A forma que reaparece na camada de serviço" numbered
produto = repositorio.buscar(id)

if produto is None:
    raise ProdutoNaoEncontrado(id)

return produto
```

Você ainda não conhece `raise`, nem repositório, nem classe de exceção.
Guarde só a forma: **trate a ausência primeiro e saia**. Sem ela, uma API
real acumula cinco níveis de `if` aninhado e um `None` que escapa até o
navegador do usuário.

:::summary
- `if`, `elif`, `else` com dois-pontos e indentação; sem parênteses.
- Todo `if` sem `else` deixa um caminho implícito — saiba qual é.
- Cláusula de guarda: trate o caso ruim primeiro e saia.
- `match` compara valores e também desmonta estruturas; nome solto em `case`
  captura em vez de comparar.
- `pass` preenche um bloco que a gramática exige e o programa não usa.
:::

:::milestone
O programa agora decide. Ainda não guarda nada nem responde a ninguém — mas
a lógica que vai recusar um preço negativo no capítulo @cap:validacao é
exatamente esta.
:::

:::exercise level=1
Escreva um programa que receba uma temperatura e imprima `"Imprópria"` acima
de 8 graus e `"Adequada"` caso contrário — a faixa de conservação da câmara
fria da cooperativa.

:::answer
```python
temperatura = 9.4

if temperatura > 8:
    print("Imprópria")
else:
    print("Adequada")
```
:::

:::exercise level=2
Calcule o frete de uma entrega: a primeira caixa custa R$ 12, cada caixa
seguinte custa R$ 4, e o valor máximo é R$ 80. Teste com 1, 5 e 40 caixas.

:::answer
```python
caixas = 40

frete = 12 + (caixas - 1) * 4
if frete > 80:
    frete = 80

print(f"R$ {frete}")
```
O teto entra **depois** do cálculo, como uma segunda decisão. Tentar resolver
o limite dentro da mesma expressão é o caminho mais curto para um erro
difícil de enxergar — e a função `min(frete, 80)` faz a mesma coisa numa
linha, se o leitor entender `min` como "teto".
:::

:::exercise level=3
Reescreva a escada de conceitos usando `match` e a divisão inteira da nota
por 10. Depois decida qual das duas versões ficaria no projeto, e justifique.

:::answer
```python
match int(nota) // 10:
    case 10 | 9:
        conceito = "Excelente"
    case 8 | 7:
        conceito = "Bom"
    case 6 | 5:
        conceito = "Regular"
    case _:
        conceito = "Insuficiente"
```

Funciona e é mais curta. Mas a versão com `if` diz literalmente `nota >= 9`,
enquanto esta exige que o leitor reconstrua a faixa a partir de uma divisão
— e ainda esconde um detalhe: `int(9.9) // 10` é `0`, então a nota 9,9 cai
no `case _` e vira "Insuficiente".

Para **faixas**, `if` comunica melhor e erra menos. Para **valores exatos**,
`match`. A resposta certa aqui não é a forma: é ter testado com 9,9.
:::
