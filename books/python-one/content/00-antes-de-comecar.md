---
title: "Antes de começar"
slug: antes-de-comecar
matter: front
numbered: false
kicker: "Python é fácil de começar e difícil de terminar. Este livro é sobre a segunda parte."
---

Python tem a reputação de linguagem amigável, e a reputação é merecida: em
dez minutos alguém que nunca programou faz o computador responder. O que
quase ninguém avisa é que essa facilidade cobra a conta depois, no dia em
que o script de dez linhas virou um sistema de dez mil e ninguém sabe mais
o que acontece quando o arquivo não existe.

Este livro trata das duas coisas na mesma ordem em que elas aparecem na
vida real: primeiro o programa que roda, depois o programa que aguenta.

## A Cooperativa Sabiá

O projeto nasce numa planilha compartilhada com trinta e uma abas. A
Cooperativa Sabiá reúne produtores de hortifrúti, registra preços e tenta
acompanhar o estoque enquanto duas pessoas editam a mesma célula.

Você vai trocar essa planilha por uma API. Primeiro, um programa que roda.
Depois, dados com nomes, regras que podem ser testadas, um banco, rotas,
autenticação e documentação. A linguagem entra quando a situação pede: um
`for` para percorrer o estoque, uma classe quando o dado ganha identidade,
uma dependência quando abrir e fechar uma conexão deixa de ser detalhe.

:::key
O livro não é uma referência de Python. É um caminho até uma API
funcionando — e a referência oficial, que é excelente e gratuita, está em
<https://docs.python.org/pt-br/3/>.
:::

O foco aqui não é ciência de dados. É o Python que recebe uma requisição,
guarda um dado e devolve JSON. O caminho é cumulativo: os arquivos de uma
etapa viram o chão da seguinte. Quando um exercício pedir uma decisão, não
procure apenas a linha certa; escreva por que aquela regra pertence àquele
lugar.

:::practice
Deixe um terminal aberto ao lado do livro desde a primeira página. Python
recompensa quem testa a frase em vez de acreditar nela.
:::

## Para quem chegou até aqui

Para quem já escreveu um script e quer saber como se constrói um sistema;
para quem aprendeu outra linguagem e precisa do Python de produção; e para
quem nunca programou, desde que aceite ler a mensagem de erro em vez de
pular para a próxima linha.

Se você vem do Java One, o primeiro volume desta coleção, vai reconhecer o
formato e estranhar o conteúdo: são duas linguagens com filosofias opostas
sobre o que o computador deve exigir de você antes de rodar. Esse contraste
aparece de propósito algumas vezes.

## O ambiente

Você precisa de três coisas, e as três são gratuitas:

| O quê | Versão | Para quê |
|---|---|---|
| Python | 3.12 ou mais novo | a linguagem e o `pip` |
| Um editor | qualquer um | VS Code, PyCharm, Vim — tanto faz |
| PostgreSQL | 16 ou mais novo | a partir do capítulo @cap:banco-de-dados |

O PostgreSQL só aparece quando o catálogo precisar persistir dados. Não
instale agora.

A instalação passo a passo está no capítulo @cap:o-que-vamos-construir,
junto com o teste que confirma que deu certo.

:::warning Uma armadilha de Windows
Se você instalar o Python pela Microsoft Store, algumas versões deixam um
`python.exe` falso no caminho, que abre a loja em vez de rodar o programa.
Baixe do site oficial, <https://python.org>, e marque a caixa
*Add python.exe to PATH* na primeira tela do instalador.
:::

## Convenções

Código aparece assim, às vezes com o nome do arquivo:

```python title="exemplo.py"
preco = 19.90
print(f"R$ {preco:.2f}")
```

O que o terminal responde aparece sem nome de arquivo e sem realce:

```text
R$ 19.90
```

E quando o programa quebra — o que vai acontecer muito, de propósito — o
erro vem inteiro, do começo ao fim, porque as linhas do meio são as que
importam.

:::key
Comando de terminal aparece com `$` na frente. O `$` não faz parte do
comando: ele representa o prompt. Copiar o `$` junto é o erro número um de
quem está começando.
:::
