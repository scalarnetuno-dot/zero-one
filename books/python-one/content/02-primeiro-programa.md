---
title: "O primeiro programa"
number: 2
slug: primeiro-programa
part: p1
kicker: "Oito caracteres, um arquivo e a descoberta de que o computador é literal."
goal: >-
  Escrever, salvar e rodar um programa Python; entender o que acontece entre
  o `Enter` e a saída; e ler as três mensagens de erro que todo iniciante vê.
---

O menor programa Python útil tem uma linha:

```python title="ola.py" numbered
print("Olá, Sabiá")
```

Salve isso num arquivo chamado `ola.py`, abra o terminal na pasta onde ele
está e rode:

```text
$ python ola.py
Olá, Sabiá
```

Pronto. Você programou. O resto do livro é sobre o que fazer quando uma
linha não basta.

## O que aconteceu entre o Enter e a saída

Quando você digitou `python ola.py`, quatro coisas aconteceram em sequência,
e vale conhecer as quatro porque cada uma delas tem um jeito próprio de
falhar.

:::diagram type="flowchart" caption="Do texto à saída: o Python compila, sim — só não guarda o resultado onde você veja."
nodes:
  - { id: src, type: io,      text: "ola.py" }
  - { id: cmp, type: process, text: "compilação para bytecode" }
  - { id: pyc, type: io,      text: "__pycache__/ola.pyc" }
  - { id: vm,  type: process, text: "máquina virtual Python" }
  - { id: out, type: io,      text: "Olá, Sabiá" }
edges:
  - { from: src, to: cmp }
  - { from: cmp, to: pyc, label: "guarda" }
  - { from: cmp, to: vm }
  - { from: vm,  to: out }
:::

Primeiro o interpretador leu o arquivo e verificou se aquilo era Python
válido — se tem parêntese fechando, aspas fechando, indentação coerente.
Essa etapa não executa nada; ela só julga a forma. Um erro aqui é um
`SyntaxError`, e ele impede o programa inteiro de rodar, mesmo que o erro
esteja na última linha.

Depois, o texto virou **bytecode**: uma lista de instruções pequenas, mais
próximas da máquina que do seu texto, mas ainda não específicas do seu
processador. Em seguida a máquina virtual executou esse bytecode instrução
por instrução. E, por fim, `print` empurrou os caracteres para a saída
padrão.

:::term Interpretador
O programa chamado `python`. Ele lê seu arquivo, compila para bytecode e
executa esse bytecode. A palavra sugere que ele lê linha a linha durante a
execução — não é o que acontece desde os anos 1990.
:::

:::term Bytecode
A forma intermediária do seu código: instruções da máquina virtual do
Python, guardadas em arquivos `.pyc` dentro de `__pycache__/`. Você nunca
precisa abrir essa pasta; pode apagá-la sem medo.
:::

:::trivia
Aquela pasta `__pycache__` que aparece sozinha ao lado do seu código não é
sujeira: é cache. Na segunda execução do mesmo arquivo sem alteração, o
Python pula a etapa de compilação e ganha alguns milissegundos. Ela é
descartável — e por isso a primeira linha de todo `.gitignore` de projeto
Python, que você vai escrever no capítulo @cap:git, é exatamente ela.
:::

## O REPL: um Python que responde na hora

Digite `python` sem nome de arquivo:

```text
$ python
Python 3.12.4 (main, Jun  6 2026, 18:26:44)
>>> 2 + 2
4
>>> "Sabiá" * 3
'SabiáSabiáSabiá'
>>> exit()
```

Esse `>>>` é o **REPL** — sigla de *read, eval, print, loop*: ele lê o que
você digita, avalia, imprime o resultado e repete. Repare que você não
precisou de `print`: no REPL, o valor de cada expressão aparece sozinho.

Isso tem uma consequência que confunde quem começa: no REPL, `2 + 2` mostra
`4`; num arquivo, `2 + 2` não mostra nada. O arquivo calcula e descarta. Só
`print` escreve.

:::practice
Abra o REPL e digite `"Sabiá" * 3` e depois `"Sabiá" + 3`. A segunda linha
vai falhar. Leia a mensagem inteira antes de continuar — ela é a primeira de
muitas que vão te dizer exatamente o que está errado, com um vocabulário que
em dois capítulos você vai achar óbvio.
:::

O REPL é a ferramenta de dúvida rápida: "como é mesmo que arredonda?", "esse
método existe?". Nada que se escreve nele sobrevive ao fechamento da janela,
e é justamente por isso que ele é seguro.

## Indentação não é estética

Aqui está a característica mais famosa do Python, e a que mais irrita quem
vem de outra linguagem:

```python title="maioridade.py" numbered
idade = 18

if idade >= 18:
    print("Pode entrar")
    print("Bem-vindo")

print("Fim")
```

Os quatro espaços na frente dos dois `print` do meio não são decoração. Eles
**são** o bloco. Em Java ou C, chaves delimitam e a indentação é um acordo
de cavalheiros entre humanos; em Python, a indentação é a sintaxe, e o
computador lê o mesmo desenho que você.

:::compare left="O que o C vê" right="O que o Python vê" lang="python"
if (ok) {
    libera();
}
registra();
---
if ok:
    libera()
registra()
:::

A diferença parece pequena e resolve, de uma vez, uma classe inteira de
defeitos: em Python é impossível que o código esteja indentado de um jeito e
execute de outro. O desenho na tela é a verdade.

O preço é que espaço em branco passa a quebrar programas:

```text
  File "maioridade.py", line 5
    print("Bem-vindo")
IndentationError: unindent does not match any outer indentation level
```

:::key
Use **quatro espaços** por nível e nunca misture espaço com tabulação no
mesmo arquivo. Qualquer editor configurado para Python converte a tecla Tab
em quatro espaços — confira essa opção hoje e não pense mais nisso.
:::

## Variáveis, sem cerimônia

Para guardar um valor, dê um nome a ele:

```python title="produto.py" numbered
nome = "Tomate italiano"
preco = 8.90
estoque = 120

print(nome, preco, estoque)
```

Não há declaração de tipo, não há palavra-chave, não há ponto e vírgula. O
`=` cria o nome se ele não existir e o reaponta se existir.

Repare no que `print` faz com vários argumentos: ele separa por espaço.

```text
Tomate italiano 8.9 120
```

E repare no `8.9`. Você escreveu `8.90` e o Python imprimiu `8.9`, porque
`8.90` e `8.9` são o mesmo número. O zero à direita é uma convenção de
dinheiro, não uma propriedade do valor — e quem precisa dele precisa pedir.

## `f-string`: o jeito de montar texto

```python title="produto.py" numbered
nome = "Tomate italiano"
preco = 8.90

print(f"{nome} custa R$ {preco:.2f}")
```

```text
Tomate italiano custa R$ 8.90
```

O `f` antes das aspas liga o modo de interpolação: tudo entre chaves é
avaliado como código Python e o resultado entra no texto. O `:.2f` depois
dos dois-pontos é a **forma** de apresentar: duas casas decimais, notação de
ponto flutuante.

:::anatomy title="As partes de uma f-string"
lang: python
code: |
  print(f"{nome} custa R$ {preco:.2f}")
notes:
  - { line: 1, text: "O `f` antes da aspa liga a interpolação. Sem ele, as chaves são texto literal." }
  - { line: 1, text: "Dentro das chaves vale qualquer expressão: `{preco * 2}` funciona." }
  - { line: 1, text: "Depois dos `:` vem o formato, não o valor: `.2f` são duas casas." }
:::

Outros formatos que você vai usar neste livro:

| Escrita | Resultado | Para quê |
|---|---|---|
| `f"{preco:.2f}"` | `8.90` | dinheiro |
| `f"{preco:>8.2f}"` | `␣␣␣␣8.90` | alinhar à direita |
| `f"{nome:<20}"` | preenche até 20 | colunas de tabela |
| `f"{0.153:.1%}"` | `15.3%` | porcentagem |

Tabela: O mini-idioma de formatação é grande; estas quatro formas resolvem
quase tudo que aparece numa API.

:::pitfall
Ainda existe muito código antigo com `"%s custa %.2f" % (nome, preco)` e com
`"{} custa {}".format(nome, preco)`. As duas formas funcionam e as duas são
piores: obrigam quem lê a fazer o pareamento de olho, contando posições.
Escreva `f-string` e pronto.
:::

## Comentários

Tudo depois de `#` na linha é ignorado:

```python
# o preço vem do produtor, sem a margem da cooperativa
preco_base = 8.90
```

Um comentário bom explica **por quê**; o código já explica o quê. O
comentário `# soma 1 ao contador` em cima de `contador += 1` é ruído puro.

## Três erros que você vai ver hoje

Programar é conviver com erro. O Python erra de um jeito específico — ele
imprime um *traceback*, que é o caminho até o problema — e aprender a ler
isso agora economiza semanas depois.

O primeiro é de forma. Faltou o parêntese:

```text
  File "ola.py", line 1
    print("Olá, Sabiá"
          ^
SyntaxError: '(' was never closed
```

O `^` aponta a coluna. Repare que o erro apontado pode estar *antes* do erro
real: um parêntese esquecido na linha 1 costuma ser denunciado na linha 2.

O segundo é de nome. O Python não conhece a palavra:

```text
Traceback (most recent call last):
  File "ola.py", line 1, in <module>
    print(nomeDoProduto)
NameError: name 'nomeDoProduto' is not defined.
Did you mean: 'nome_do_produto'?
```

Essa sugestão no fim — `Did you mean` — é uma adição das versões recentes do
Python e resolve a maioria dos casos: quase sempre é digitação.

O terceiro é de tipo, e é o mais interessante:

```text
Traceback (most recent call last):
  File "ola.py", line 2, in <module>
    print("total: " + 120)
TypeError: can only concatenate str (not "int") to str
```

O Python somou texto com número e recusou. Ele não converteu sozinho, como
faz o JavaScript, nem se recusou a compilar, como faria o Java: ele deixou
rodar e parou na hora exata em que a operação impossível apareceu. Guarde
essa frase, porque ela é o caráter da linguagem inteira e vai voltar no
capítulo @cap:variaveis-e-tipos.

:::key
Leia o traceback **de baixo para cima**. A última linha diz o que houve; a
penúltima diz onde. As linhas do meio só importam quando o erro está dentro
de uma função que você chamou — e aí elas são o mapa inteiro.
:::

## O arquivo que vira comando

Uma última convenção, que aparece em quase todo arquivo Python do mundo:

```python title="ola.py" numbered
def main():
    print("Olá, Sabiá")


if __name__ == "__main__":
    main()
```

A tradução é: *"se este arquivo estiver sendo executado diretamente, rode
`main`"*. Quando o arquivo for importado por outro — coisa do capítulo
@cap:modulos-e-ambiente —, esse trecho não roda.

Ainda não é hora de entender `__name__`. É hora de reconhecer a forma,
porque você vai vê-la mil vezes antes de precisar dela.

:::summary
- `python arquivo.py` compila para bytecode e executa; o `__pycache__` é só
  cache.
- No REPL o valor aparece sozinho; num arquivo, só `print` escreve.
- Indentação é sintaxe: quatro espaços, nunca misturados com tabulação.
- `f"{valor:.2f}"` é a forma de montar texto; as antigas só sobrevivem em
  código velho.
- Traceback se lê de baixo para cima: a última linha diz o quê.
:::

:::exercise level=1
Escreva um programa que guarde o nome de um produtor e a quantidade de
caixas entregues e imprima a frase `Seu Onofre entregou 12 caixas.` usando
uma `f-string`.

:::answer
```python
produtor = "Seu Onofre"
caixas = 12

print(f"{produtor} entregou {caixas} caixas.")
```
:::

:::exercise level=2
O preço de um produto é `8.9` e a cooperativa cobra 12% de margem. Imprima
as duas linhas abaixo, com o alinhamento exato:

```text
Preço base   R$     8.90
Com margem   R$     9.97
```

:::answer
```python
base = 8.9
final = base * 1.12

print(f"Preço base   R$ {base:>8.2f}")
print(f"Com margem   R$ {final:>8.2f}")
```
O `>8` reserva oito colunas e empurra o número para a direita. Alinhar
número pela direita não é gosto: é o que permite comparar as casas decimais
de olho, numa coluna.
:::

:::exercise level=3
Rode o programa abaixo e explique, em duas frases, por que o erro aponta
para a linha 3 se o problema está na 2.

```python
nome = "Tomate"
preco = 8.90
print(f"{nome}: {precoo}")
```

:::answer
O problema não está na linha 2: a linha 2 está perfeita. O erro é um
`NameError` na linha 3, onde a `f-string` pede `precoo` — um nome que nunca
foi criado.

A lição embutida é que o Python só descobre que um nome não existe **no
momento em que tenta usá-lo**. Uma linguagem de tipagem estática recusaria o
arquivo inteiro antes de rodar; o Python roda até ali, imprime o que já
tinha para imprimir e só então para. Esse é o preço da flexibilidade, e a
resposta parcial a ele são os testes do capítulo @cap:testando-python.
:::
