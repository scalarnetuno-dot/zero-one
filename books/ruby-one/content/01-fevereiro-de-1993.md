---
title: "Fevereiro de 1993"
number: 1
slug: fevereiro-de-1993
part: p1
kicker: "Um programador no Japão, um critério de leitura, e vinte anos até o framework que a Nortea já usa de manhã."
epigraph: "I wanted a scripting language that was more powerful than Perl, and more object-oriented than Python. That's why I decided to design my own language."
epigraph_by: "Yukihiro Matsumoto, entrevista a Bill Venners, 29 de setembro de 2003"
goal: >-
  Contar a história documentada do Ruby e a do Rails: o desenho de 1993,
  a saída do Japão, o Basecamp, o Merb, o YARV e o calendário de Natal
  que ainda marca a versão do servidor da Nortea.
---

:::story Por que Ruby?
O Rômulo tinha almoçado com um fornecedor na quarta. Na quinta parou na
sala.

— Esse módulo de contratos. Por que Ruby?

— Porque é o que está no ar — disse a Lívia. — O Sérgio me falou. Desde
2016.

— O pessoal do almoço falou que Rails é legado.

O Renato não abriu slide.

— O contrato que a Helena abre de manhã é esse código. A Serra Azul renova
em 3 de junho.

O Caio falou sem virar a cadeira.

— Três ponto três. No servidor.

A Lívia olhou para ele.

— Três ponto três do quê?

— Do Ruby. Manutenção normal até 1º de abril. Segurança até 31 de março
de 2027.
:::

A Lívia tinha entrado na segunda, 2 de março. O repositório chegou na
sexta seguinte. Na quinta ela repetiu o corredor. A versão, o Caio tirou
do servidor.

Ruby é a linguagem. Rails é um framework escrito nessa linguagem: um
conjunto de bibliotecas e de convenções que já decide a forma do programa.
Quem escreve preenche o que é da Nortea — contrato, equipamento, data. O
sistema de 2016 é Rails. A linguagem em que ele está escrito começa em
1993, no Japão, com outro autor e sem framework nenhum.

## 24 de fevereiro de 1993

Yukihiro Matsumoto, conhecido como Matz, começou o Ruby nessa data, no
Japão, como projeto pessoal, enquanto trabalhava como programador. O
critério ele declarou anos depois, na entrevista que abre este capítulo:
uma linguagem de script mais poderosa que Perl e mais orientada a objetos
que Python. As influências que ele mesmo listou foram Perl, Smalltalk,
Eiffel, Ada e Lisp.

Do Perl ele queria o trato com texto e a vontade de resolver a tarefa. De
Smalltalk, o objeto e o bloco. De Lisp, a ideia de que código pode ser
dado: um trecho de programa guardado e entregue a outro trecho. Eiffel e
Ada entraram no critério de clareza, não como sintaxe copiada.

O desenho que saiu dali ainda é o núcleo.

Tudo é objeto. O número `2` é um objeto. `nil`, o valor que significa
ausência, é um objeto. Um método é uma mensagem enviada a um objeto. Não
há um tipo especial de "valor cru" ao lado dos objetos, como havia nas
linguagens de que o Matz estava se afastando.

:::term Bloco
Um objeto que guarda um trecho de código. Dá para entregar esse objeto a
um método. O método decide quando chamar o trecho, e com qual valor.

A ideia veio de Smalltalk. No Ruby ela está desde o começo: percorrer uma
lista, filtrar, transformar, tudo isso é um método que recebe um bloco.
:::

A sintaxe foi desenhada para ser lida com pouca pontuação. Método e
variável em minúsculas, com sublinhado. Classe com inicial maiúscula. Um
método que responde sim ou não pode terminar em `?`. Nada disso é regra do
computador para existir. É regra do texto para outra pessoa conseguir ler
em voz alta. O Matz tratou a leitura como parte do desenho, não como
enfeite posterior.

A primeira versão pública foi a 0.95, em **21 de dezembro de 1995**,
anunciada em grupos de notícia japoneses. O Ruby 1.0 saiu no **Natal de
1996**, 25 de dezembro. O Natal virou, com os anos, a data em que uma
versão grande aparece. Não foi um calendário de fundação escrito de uma
vez. Foi um hábito que a 1.0 fixou e as versões posteriores repetiram.

## A saída do Japão

Durante os primeiros anos a conversa pública era em japonês. A lista de
correio em inglês, a ruby-talk, abriu caminho no fim da década de 1990. O
livro que tirou a linguagem desse círculo foi *Programming Ruby*, de Dave
Thomas e Andy Hunt, publicado no fim de 2000 pela Addison-Wesley. A capa
tinha uma picareta. O livro ficou conhecido como Pickaxe, e durante um
tempo foi o manual de quem aprendia Ruby fora do Japão.

Em **4 de agosto de 2003** saiu o Ruby 1.8.0. Essa linha, sobretudo o
1.8.7 no fim dela, foi a que ficou instalada em servidor por anos. É a
língua em que o primeiro Rails cresceu.

Biblioteca de terceiro, nessa época, era arquivo copiado para dentro do
projeto. Em 2004 um grupo — Chad Fowler, Rich Kilmer, Jim Weirich e outros
— publicou o RubyGems. Uma **gem** é uma biblioteca empacotada, com nome e
versão. O comando `gem` instala essa versão. O Ruby passou a ter um
registro. O arquivo do projeto ainda não dizia, sozinho, o conjunto fechado
do que devia ser instalado. Isso veio depois, com outro comando, quando o
conflito entre versões ficou cotidiano.

## Basecamp, Merb, e duas máquinas virtuais

Em 2003 e 2004 David Heinemeier Hansson, o DHH, trabalhava no Basecamp, o
produto da 37signals. Ele extraiu do Basecamp um framework e publicou o
Rails. A primeira versão pública circulou em **julho de 2004**. O Rails
1.0 saiu em **13 de dezembro de 2005**.

O desenho que ele publicou tinha decisões com nome. *Convenção sobre
configuração*: o nome da classe indica o nome da tabela, e o arquivo não
repete essa ligação se a convenção bastar. A classe `Contract` procura a
tabela `contracts`. *Active Record* é o nome de um padrão do livro de
Martin Fowler, *Patterns of Enterprise Application Architecture*, de 2002:
um objeto que representa uma linha e sabe gravá-la. O Rails implementou
esse padrão em cima da convenção de nomes. Quem abre `contract.rb` na
Nortea está olhando essa decisão de 2004, mais vinte e três colunas que
vieram depois.

:::term Rails
Framework escrito em Ruby, extraído do Basecamp e publicado em 2004. Já
traz a estrutura de um sistema web: o pedido entra por uma rota, passa
por um controller, fala com um model, e a resposta volta.

A Nortea roda um Rails desde 2016. O framework não é a linguagem. É um
programa Ruby que espera os arquivos da Nortea em pastas combinadas.
:::

Em 2006 Ezra Zygmuntowicz publicou o Merb, outro framework Ruby, mais
explícito e mais modular, usado por quem esbarrava no miolo do Rails da
época. Em **dezembro de 2008** o DHH anunciou que o Merb seria incorporado
ao Rails 3, e que os dois times passariam a trabalhar no mesmo projeto. O
Rails 3.0 saiu em **agosto de 2010**. O miolo foi reescrito: o roteador, e
a fronteira entre o framework e a biblioteca que fala com o banco. A
convenção de nomes de 2004 permaneceu. O Merb, como produto separado,
parou. O que ele disputava — um miolo em peças — entrou no Rails.

No mesmo mês de agosto de 2010 saiu o Bundler 1.0, de Yehuda Katz, Carl
Lerche e outros. O problema que ele fechava era concreto: duas gems pediam
versões diferentes de uma terceira, e o RubyGems ativava uma delas tarde
demais, com o programa já rodando. O `Gemfile` lista o que o projeto pede.
O `Gemfile.lock` grava o que foi resolvido. O comando `bundle` instala esse
conjunto. O `nortea` de 2016 tem os dois arquivos. São dessa safra.

Enquanto o framework se reescrevia, a máquina virtual também. Koichi
Sasada escreveu o YARV, *Yet Another Ruby VM*, um novo executor para o
Ruby. O Ruby 1.9.0, no **Natal de 2007**, passou a usar o YARV. Nessa linha
a string ganhou codificação: o texto carrega a informação de qual conjunto
de caracteres ele é. Código que tratava string como sequência crua de
bytes quebrou. O 1.9.0 não foi, de saída, a versão que o servidor
adotava. A linha 1.9 só ficou estável para uso geral anos depois. Muita
gente permaneceu no 1.8.7, e as duas versões conviveram, cada uma com gems
que só existiam para ela.

:::term YARV
A máquina virtual escrita por Koichi Sasada. A partir do Ruby 1.9 ela é o
executor da implementação de referência, a escrita em C, no lugar do
interpretador antigo.

Máquina virtual, aqui, é o programa que lê o Ruby e o executa. Trocar a
máquina virtual não troca o nome da linguagem. Troca o que acontece por
baixo do arquivo, e às vezes o que o arquivo precisa declarar — como a
codificação do texto, no 1.9.
:::

O reencontro foi o Ruby 2.0.0, em **24 de fevereiro de 2013**, vinte anos
depois do dia em que o Matz começou. A codificação padrão do arquivo-fonte
passou a ser UTF-8. Entrou também o argumento com nome: ao chamar um
método, dá para escrever o nome do parâmetro junto do valor, em vez de
depender só da posição. A linha 1.8 chegava ao fim da manutenção estendida
no ano seguinte. Quem ainda rodava 1.8.7 em 2013 não estava numa escolha de
gosto: estava num servidor que ninguém tinha marcado data para tocar.

## O calendário de Natal

Do 2.1 em diante, a versão maior de fim de ano saiu no Natal com
regularidade: 25 de dezembro, ou a véspera quando o dia caía mal. Cada
linha passou a ter duas fases publicadas. Na **manutenção normal**, entram
correção de defeito e correção de segurança. Na **manutenção de
segurança**, só a segunda. O fim costuma cair em 31 de março, cerca de
três anos depois do Natal de lançamento. O calendário é do time do Ruby,
não de um fornecedor que almoça com o Rômulo.

:::term Manutenção
As duas fases de uma linha do Ruby. Normal: defeito e segurança.
Segurança: só segurança, até a data de fim publicada.

"Está suportado" sem dizer a fase não diz se um defeito comum ainda ganha
correção. No servidor da Nortea, em março de 2026, essa diferença tem
data.
:::

O Ruby 3.0 saiu no **Natal de 2020**. O Matz tinha anunciado, anos antes, a
meta de um Ruby 3 três vezes mais rápido que o 2.0 nessa geração. O 3.0
trouxe o Ractor, um mecanismo experimental de paralelismo, e o RBS, uma
linguagem à parte para descrever a forma das classes — não um sistema de
tipos dentro do Ruby. A linguagem continuou dinâmica: o tipo mora no valor,
e a descrição em RBS é outro arquivo, lido por outras ferramentas. A meta
de velocidade não se cumpriu no 3.0 pelo interpretador sozinho.

Quem avançou a velocidade foi um compilador escrito fora do núcleo e
depois incorporado. O YJIT, feito na Shopify — Maxime Chevalier-Boisvert,
Alan Wu e o time de lá —, entrou no Ruby 3.1, Natal de 2021, como
experimental. Ele traduz, durante a execução, o trecho que mais roda para
código de máquina. Nas versões seguintes deixou de ser experiência e passou
a ser opção estável. É um compilador com autor, empresa e Natal. Não é uma
propriedade vaga da linguagem.

O Ruby 3.3 saiu no **Natal de 2023**. É a linha do servidor da Nortea. A
manutenção normal dela vai até **1º de abril de 2026**. A de segurança, até
**31 de março de 2027**. No dia 3 de junho, data da Serra Azul, um 3.3
ainda recebe correção de segurança e já não recebe correção de defeito
comum. São duas datas diferentes. O Caio disse as duas na quinta.

O Ruby 3.4 saiu no Natal de 2024. Nessa linha o Prism, o analisador
sintático escrito sob a condução de Kevin Newton, virou o padrão: o
programa que lê o texto do arquivo antes de executar. O Ruby 4.0 saiu no
**Natal de 2025**. O núcleo — objeto, método, bloco — é o de 1993. A linha
nova é outra janela de manutenção, não outra linguagem.

:::diagram type="timeline" caption="Do projeto pessoal de 1993 à linha que o servidor da Nortea ainda roda."
width: 112
events:
  - { year: "1993", text: "24 de fevereiro. Matz começa o Ruby, no Japão.", mark: true }
  - { year: "1995", text: "21 de dezembro. Ruby 0.95, a primeira versão pública." }
  - { year: "1996", text: "25 de dezembro. Ruby 1.0. O Natal vira data de versão.", mark: true }
  - { year: "2000", text: "Programming Ruby, o Pickaxe, tira a linguagem do círculo japonês." }
  - { year: "2004", text: "Julho. O Rails sai do Basecamp, publicado pelo DHH.", mark: true }
  - { year: "2007", text: "Natal. Ruby 1.9 troca o executor pelo YARV." }
  - { year: "2008", text: "Dezembro. O Merb é incorporado ao que será o Rails 3." }
  - { year: "2013", text: "24 de fevereiro. Ruby 2.0, vinte anos depois do começo.", mark: true }
  - { year: "2020", text: "Natal. Ruby 3.0. RBS descreve tipos num arquivo à parte." }
  - { year: "2023", text: "Natal. Ruby 3.3, a linha do servidor da Nortea.", mark: true }
:::

:::summary
- 24 de fevereiro de 1993: Matz começa o Ruby. Tudo é objeto. Bloco é
  código que se entrega a um método. A 0.95 sai em 21 de dezembro de 1995.
  A 1.0, no Natal de 1996.
- O Pickaxe, no fim de 2000, leva o Ruby ao inglês. O RubyGems, em 2004,
  empacota biblioteca com versão. O Ruby 1.8, em agosto de 2003, é a linha
  em que o Rails nasce.
- Julho de 2004: Rails, extraído do Basecamp. Dezembro de 2008: o Merb
  entra no projeto. Agosto de 2010: Rails 3 e Bundler 1.0.
- Natal de 2007: YARV vira o executor, no Ruby 1.9. 24 de fevereiro de
  2013: Ruby 2.0, UTF-8 por padrão.
- Natal de 2023: Ruby 3.3. Na Nortea, manutenção normal até 1º de abril de
  2026 e segurança até 31 de março de 2027. O Ruby 4.0 saiu no Natal de
  2025.
:::

:::exercise level=1
O Rômulo repete o fornecedor: "Ruby é uma linguagem de script, como Perl".
Responda em três linhas, com a data em que o Matz começou e com duas
decisões de desenho que ele declarou — uma vinda de Smalltalk, outra que
separa o Ruby de um script de texto solto.

:::answer
Ele começou em 24 de fevereiro de 1993. A entrevista de 2003 diz o
critério: mais poderoso que Perl, mais orientado a objetos que Python.

De Smalltalk veio o bloco: código guardado num objeto e entregue a um
método. A outra decisão é que não há valor solto ao lado dos objetos. O
número e o `nil` também são objetos, e um método é mensagem enviada a um
deles.
:::

:::exercise level=2
O fornecedor do almoço ofereceu "tirar o Rails e pôr um framework
modular". O que aconteceu, em dezembro de 2008 e em agosto de 2010, com o
framework modular que já existia em Ruby?

:::answer
Esse framework era o Merb, de Ezra Zygmuntowicz, de 2006. Em dezembro de
2008 o DHH anunciou que o Merb seria incorporado ao Rails 3 e que os times
trabalhariam juntos.

Em agosto de 2010 saiu o Rails 3. O roteador e a fronteira com a
biblioteca de banco foram reescritos. A convenção de nomes de 2004 — a
classe `Contract` e a tabela `contracts` — ficou. O Merb, como produto
separado, não seguiu.
:::

:::exercise level=3
O Rômulo abre um ticket: "atualizar o Ruby do servidor esta semana, para a
versão mais nova". A semana é a de 9 de março de 2026. A mais nova, nessa
data, é o Ruby 4.0, de 25 de dezembro de 2025. Você aceitaria o texto?

:::answer
Não com esse texto. O servidor está no 3.3. A manutenção normal acaba em
1º de abril de 2026; a de segurança segue até 31 de março de 2027. No dia
3 de junho o 3.3 ainda recebe segurança.

"A mais nova" aponta o 4.0 sem dizer se o `Gemfile` da Nortea já foi
resolvido nessa linha. Trocar é nomear a linha — 3.4 ou 4.0 —, olhar o
lock e escolher um horário em que o pátio das 6h não dependa do resultado.
O ticket não faz nenhuma das três coisas.
:::
