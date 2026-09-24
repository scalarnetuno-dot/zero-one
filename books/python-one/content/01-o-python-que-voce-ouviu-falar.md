---
title: "O Python que você ouviu falar"
number: 1
slug: o-python-que-voce-ouviu-falar
part: p1
kicker: "Uma linguagem escrita nas férias de Natal para substituir outra, e que hoje fecha o preço do tomate num computador que ninguém desliga."
epigraph: "Em dezembro de 1989, eu estava procurando um projeto de programação de 'hobby' que me ocupasse na semana do Natal."
epigraph_by: "Guido van Rossum, no prefácio de Programming Python, 1996"
goal: >-
  Saber de onde vem o Python, o que causou a fama de linguagem de script, o
  que a ruptura entre as versões 2 e 3 ainda cobra, o que a linguagem resolve
  bem e o que ela não resolve.
---

:::story Não dava pra deixar no Excel?
O Sérgio tinha visto uma palestra na quinta e voltou com três frases na
sexta.

— Esse projeto da cooperativa. Por que Python?

— O fechamento é Python — disse a Bia. — A planilha o notebook abre com
Python. A Dona Neuza usa isso desde 2021.

— Mas a gente não ia modernizar?

— Vamos. De um notebook que só roda numa máquina para um programa que a
Bem-Te-Vi consiga chamar.

O Sérgio fez o gesto de quem tira uma coisa da frente do rosto.

— Não dava pra deixar no Excel e colocar uma IA em cima?

— Dava.

— Então.

— Aí a gente joga fora quatro anos de margem que não estão escritas em lugar
nenhum, e entrega em 15 de abril.

Pausa.

— É que Python é meio... — ele procurou a palavra — ...de script.

— A versão atual saiu em outubro.

A Helena falou sem levantar os olhos da planilha de sprint.

— O fechamento da manhã roda em quê?

Elias pigarreou.

— Python.

— Qual versão?

— Três ponto seis. Na máquina que tem um post-it pedindo para não desligar.
:::

Essa conversa acontece em algum lugar do mundo toda semana, e o
mal-entendido é sempre o mesmo: "linguagem de script" descreve, com
precisão, o motivo pelo qual o Python foi criado — e quase nada do que ele
é capaz de carregar hoje.

Os defeitos que alimentam a fama foram reais. Um deles durou uma década e
tinha data para acabar. Outro ainda não acabou. Vale saber qual é qual,
porque o `GALPAO-02` está cheio dos dois, e porque "por que Python?" vai
voltar na próxima palestra a que o Sérgio assistir.

## Um hobby, no Natal de 1989

Guido van Rossum era pesquisador no CWI, em Amsterdã. O centro fecharia na
semana do Natal. Ele queria um projeto pequeno: um sucessor da linguagem
ABC, que ele tinha ajudado a fazer e que era boa para ensinar e ruim para
falar com o sistema operacional.

ABC não usava chaves. O bloco era o recuo da linha. Guido levou isso junto,
de propósito. A indentação do Python não é uma excentricidade estética: é
herança de uma linguagem de ensino que se recusava a ter duas verdades, a
do desenho na tela e a do que o computador executava.

O nome também não é o da cobra. Ele estava lendo os roteiros do *Monty
Python's Flying Circus* e achou que "Python" era um título curto. Os
exemplos clássicos da documentação se chamam `spam` e `eggs` por causa
disso. O logotipo da cobra veio depois, quando a comunidade precisou de um
desenho.

:::trivia
Em 20 de fevereiro de 1991 ele publicou a versão 0.9.0 no grupo
`alt.sources`. Não era um anúncio de empresa. Era um arquivo, num fórum,
com classes, exceções, funções, listas e dicionários já dentro.

Quem baixa o Python hoje está na continuidade direta daquele arquivo.
:::

A linguagem cresceu do mesmo jeito que o notebook do Cacá: alguém precisava
de uma coisa, a coisa entrava, e o projeto deixava de ser hobby sem nunca
ter tido uma reunião para decidir isso. A diferença é que, a partir de um
certo ponto, as entradas passaram a ter número, discussão pública e data.

## Os marcos que ainda afetam o seu código

:::diagram type="timeline" caption="Por que a linguagem é assim: os marcos que você encontra em código real."
width: 112
events:
  - { year: "1989", text: "Guido começa, no Natal, um sucessor da ABC" }
  - { year: "1991", text: "Python 0.9.0 publicado num fórum; classes e exceções já existem", mark: true }
  - { year: "2000", text: "Python 2.0: a linguagem vira projeto de comunidade" }
  - { year: "2008", text: "Python 3.0: de propósito incompatível com o 2", mark: true }
  - { year: "2018", text: "Guido deixa o posto de ditador benevolente; entra um conselho" }
  - { year: "2020", text: "1º de janeiro: o Python 2.7 morre, doze anos depois do aviso", mark: true }
  - { year: "2022", text: "Python 3.11: cerca de 25% mais rápido, sem reescrever código", mark: true }
  - { year: "2024", text: "Python 3.13: um modo sem GIL, ainda opcional" }
  - { year: "2025", text: "Python 3.14, em outubro: o calendário anual segue de pé" }
:::

Repare em duas datas.

**2008** é quando o Python decidiu quebrar o próprio passado. O texto deixou
de ser uma sequência de bytes ambígua e passou a ser texto de verdade. O
`print` deixou de ser uma declaração (`print "oi"`) e virou uma função
(`print("oi")`). A divisão `7 / 2`, que no Python 2 devolvia `3`, passou a
devolver `3.5`. Nenhuma dessas mudanças é detalhe. Código antigo quebra, e
o `GALPAO-02` está em 3.6 exatamente porque ninguém quis descobrir em qual
célula ele quebraria.

**2020** é o dia em que a versão antiga parou de receber correção. Não foi
surpresa: o aviso tinha doze anos. Quem ainda roda Python 2 — e ainda há
quem rode — não está numa escolha técnica. Está num computador que ninguém
teve coragem de desligar.

:::trivia
Durante anos Guido teve o título oficial de *Benevolent Dictator For Life*,
ditador benevolente vitalício. Em 2018 ele saiu do posto depois de uma
briga feia sobre um operador novo, o `:=`, que entrou na linguagem com gente
demais achando que não devia entrar.

O cargo não foi preenchido. No lugar ficou um conselho eleito. A linguagem
que tinha nascido de uma pessoa passou a mudar por votação, com o voto
registrado. Isso importa mais do que o operador.
:::

## De onde veio a fama, e o que foi feito de cada coisa

A reputação não foi preconceito. Teve causas concretas. Elas estão aqui
para você reconhecê-las quando abrir um notebook de 2021, e para saber, de
cada uma, se ela ainda descreve a linguagem que você vai instalar.

**A ruptura entre o 2 e o 3.** De 2008 a 2020 existiram duas linguagens
chamadas Python, incompatíveis, as duas vivas. Tutorial misturava as duas.
`python` e `python3` no mesmo Linux eram programas diferentes. Bibliotecas
importantes demoraram anos para atravessar. Quem aprendeu naquela década
aprendeu a desconfiar da linguagem, e a desconfiança era justa.

**O empacotamento.** Instalar a biblioteca de outra pessoa foi, por muito
tempo, um projeto à parte: `easy_install`, `pip`, `conda`, `venv`,
`poetry`, arquivos que não reproduziam a máquina do colega. Isso não foi
resolvido com uma versão. Melhorou — e continua sendo o canto mais fácil de
se machucar. O `requirements.txt` do galpão, com duas linhas comentadas e
nenhuma versão, é esse canto.

**O notebook que virou produção.** O Jupyter, herdeiro do IPython, foi
feito para explorar: rodar uma célula, ver o número, mudar, rodar de novo.
A ordem em que as células estão no arquivo não é necessariamente a ordem em
que foram executadas. Isso é ótimo para investigar e péssimo para fechar o
preço da manhã. Ninguém "lançou" o notebook do Cacá. Ele foi sendo usado
até que desligar o computador virou incidente.

**O erro que só aparece quando acontece.** O Python não recusa o programa
antes de rodar por causa de um tipo trocado. `"total: " + 120` é um arquivo
válido. Ele quebra na hora em que aquela linha executa — que, num
fechamento, pode ser a primeira terça do mês. A fama de "fácil de começar,
difícil de manter" nasce exatamente daí, e ela continua verdadeira para
quem não escreve o resto.

| A causa | O que aconteceu com ela |
|---|---|
| duas linguagens chamadas Python | o 2.7 morreu em 1º de janeiro de 2020 |
| `print` sem parêntese, divisão que truncava | acabaram no Python 3, em 2008 |
| instalar biblioteca como trabalho manual | melhorou; ainda é o ponto frágil |
| notebook usado como sistema | não é defeito da linguagem; é um uso fora do que o formato aguenta |
| tipo trocado só quebra na hora | continua verdade; ferramenta à parte é que avisa antes |

Tabela: As duas primeiras linhas não descrevem o Python que você vai
instalar. As três últimas descrevem o `GALPAO-02`, e vão continuar
descrevendo qualquer projeto que repita as decisões dele.

## O que mudou de verdade

Quatro coisas, e só a primeira é sobre velocidade.

**Dá para anotar o tipo.** Desde o Python 3.5 você pode escrever que um
preço é um número e que uma função devolve outro número. O interpretador,
na hora de rodar, ignora a anotação. Quem não ignora é o editor, o
verificador, e qualquer biblioteca que resolva ler a assinatura antes de
chamar a função. A linguagem continua dinâmica. Ganhou um jeito de
declarar a intenção sem deixar de rodar o que já rodava.

**Ficou mais rápido sem pedir reescrita.** O Python 3.11, em 2022, executa
em média cerca de 25% mais rápido que o 3.10, em código que não mudou. Não
é o tipo de velocidade de uma linguagem compilada para uma tarefa numérica
pesada. É o tipo que se recebe de graça, numa terça, porque alguém passou
anos no motor.

**O calendário ficou chato, no bom sentido.** Desde 2019 sai uma versão em
outubro, todo ano, com dois anos de correção e mais alguns de segurança. A
3.12 ainda recebe correção. A 3.9 não. A 3.6 do galpão parou em dezembro de
2021. "Qual versão?" deixou de ser uma pergunta filosófica.

**As decisões ficaram públicas.** Proposta numerada, discussão aberta,
conselho eleito. Dá para saber por que uma coisa entrou e por que outra foi
recusada. Isso não torna cada decisão boa. Torna cada decisão encontrável —
e encontrável é o que separa uma linguagem de um notebook.

:::key
Escolher uma tecnologia é apostar no que ela faz com o próprio erro.

O Python quebrou a compatibilidade uma vez, avisou por doze anos e cumpriu
a data. Acelerou o motor sem cobrar reescrita. Trocou o fundador vitalício
por um processo. O empacotamento ele ainda deve — e é honesto tratar isso
como dívida aberta, não como detalhe resolvido.
:::

## O que o Python resolve bem

Vale ser específico, porque "serve para tudo" não explica nada. Serve para
muita coisa, e mal, quando a frase é essa.

**Dá para ler no ano que vem.** A indentação obrigatória, a pouca
pontuação e o hábito de uma forma óbvia por tarefa existem para que outra
pessoa — ou você, em abril — consiga ler o arquivo sem um ritual. O notebook
do Cacá é a prova de que a linguagem não obriga ninguém a ser claro. Ela só
deixa a clareza mais barata do que em linguagens que precisam de uma página
de cerimônia antes da primeira conta.

**É boa em falar com os outros.** Arquivo, planilha, JSON, banco, página,
processo. A biblioteca padrão já sabe data, caminho, texto, JSON e CSV. O
trabalho típico não é calcular um milhão de vezes a mesma coisa: é pegar o
número de um lugar e entregar em outro, com a regra da cooperativa no meio.

**O mesmo idioma cobre o script e o serviço.** Não é obrigatório trocar de
linguagem no dia em que o `precos.py` passa a atender a rede. Dá para
crescer no mesmo arquivo até ele doer, e a dor é que avisa a hora de
dividir.

:::term GIL
*Global Interpreter Lock*: uma trava que, no Python padrão, deixa apenas uma
thread executar código Python de cada vez. Existe para o gerenciador de
memória não se perder.

Para a maior parte das APIs, o tempo está no banco e na rede, não nessa
trava. Ela importa em conta pesada, em paralelo, dentro do processo. Desde
o 3.13 existe um modo sem ela, e esse modo não é o que se instala por
padrão. Quem sofre com o GIL sabe que sofre. Quem repete a sigla numa
reunião, em geral, não mediu.
:::

## E o que ele não resolve

A lista é curta.

**Conta numérica pesada, escrita em Python puro.** O laço que faz conta o
dia inteiro fica lento. A resposta usual não é trocar de linguagem no
projeto inteiro: é chamar uma biblioteca que faz aquela conta em C, que é o
que `pandas` e o restante da pilha científica já fazem. Usar `pandas` para
somar doze células, como o notebook faz, é o extremo oposto — ferramenta de
trator para encher um copo.

**Interface de celular e de desktop.** Não é para isso que a linguagem é
escolhida, e forçar é mais caro do que admitir.

**Notebook como forma de publicar.** Célula com saída gravada, ordem de
execução implícita, estado que sobra da run anterior. Ótimo para investigar
um número. Ruim para ser o sistema de quem abre o galpão às seis.

**A regra que ninguém escreveu.** Nenhuma biblioteca, e nenhum modelo de
linguagem, sabe que orgânico e agricultura familiar acumulam até quinze por
cento exceto na primeira entrega. Isso continua sendo conversa com a Dona
Neuza.

## Quem usa

O **Instagram** foi construído em Python. O **Dropbox** também. O **YouTube**
começou nele. A **Google** usa a linguagem em escala larga, ao lado de
outras. A pilha científica — NumPy, pandas, Jupyter — é o motivo de tanta
pesquisa e tanto dado passarem por Python antes de passarem por qualquer
outra coisa.

No Brasil ele está onde está o arquivo que alguém precisa processar até
amanhã: prefeitura, laboratório, fintech integrando três sistemas que não se
falam, e cooperativa cujo fechamento mora num `.ipynb`.

:::key
"A linguagem mais popular do mundo" é uma frase de ranking. Rankings medem
busca, tutorial e resposta de questionário. Não medem sistema em produção
nem dinheiro que passa por dentro.

Popularidade não prova qualidade, de nenhuma linguagem. O que ela prova é
mercado: existe muito Python escrito, parte dele em notebook, parte dele
bom, e alguém vai ter que mantê-lo ou substituí-lo sem perder a regra que
só está na cabeça de quem usa.

A qualidade se argumenta pelo que a linguagem tem hoje — leitura barata,
calendário público, um jeito de declarar tipos, um ecossistema enorme para
falar com o resto do mundo — e pelo contorno honesto do que ela não faz.
:::

## Conferir a versão é a primeira pergunta

O Python 3.6 do galpão não recebe correção desde dezembro de 2021. Isso não
é opinião sobre o Cacá. É o calendário.

:::practice
Quando o Python estiver instalado, rode `python --version` e guarde o
número. Em seguida abra o interpretador e digite:

```text
>>> import this
```

Ele imprime o *Zen do Python*, dezenove linhas em inglês, escritas por Tim
Peters. Quatro delas bastam por hoje:

*There should be one-- and preferably only one --obvious way to do it.*

*Errors should never pass silently.*
*Unless explicitly silenced.*

A primeira é o critério para escolher entre duas formas de escrever a mesma
coisa. O par de baixo é a célula 14: ela não dá erro. Alguém silenciou, com
um comentário, e o tomate dobra.
:::

:::summary
- O Python nasceu em 1989 como sucessor da ABC. A indentação é herança
  dessa origem, não enfeite.
- De 2008 a 2020 existiram duas linguagens incompatíveis com o mesmo nome.
  O 2.7 morreu em 1º de janeiro de 2020.
- O que continua verdadeiro: empacotar dependência ainda é frágil, notebook
  não é forma de publicar, e tipo trocado só quebra quando a linha roda.
- O que mudou: tipos anotados, calendário anual em outubro, processo de
  decisão público, e um motor mais rápido sem pedir reescrita.
- O 3.6 do galpão está sem correção desde dezembro de 2021.
:::
