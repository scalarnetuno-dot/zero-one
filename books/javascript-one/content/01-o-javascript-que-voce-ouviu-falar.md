---
title: "Do Mocha ao Node"
number: 1
slug: do-mocha-ao-node
part: p1
kicker: "Dez dias em maio de 1995, um acordo com a Sun em dezembro, e um padrão que não pôde herdar o nome comercial."
epigraph: "JavaScript is an easy-to-use object scripting language designed for creating live online applications that link together objects and resources on both clients and servers."
epigraph_by: "Comunicado conjunto da Netscape e da Sun, 4 de dezembro de 1995"
goal: >-
  Contar a história documentada do JavaScript: a encomenda de 1995, o
  padrão que recebeu outro nome, a edição 4 que não saiu, o V8, o Node e o
  calendário de versões que o servidor da Borba ainda obedece.
---

:::story Por que JavaScript?
O Renato tinha visto uma palestra na quarta e voltou com três frases na
quinta.

— Esse painel da Borba. Por que JavaScript?

— Porque é o que está no ar — disse a Bia. — A página é JavaScript. O
servidor é JavaScript. A Lívia usa isso desde 2022.

— Mas a gente não ia modernizar?

— Vamos. De um arquivo que só o Diego sabia mexer para um programa que a
Mercado Leste consiga cobrar em trinta segundos.

O Renato fez o gesto de quem tira uma coisa da frente do rosto.

— Não dava pra fazer um aplicativo de verdade?

— Dava.

— Então.

— Aí a gente joga fora quatro anos de regra que não estão escritas em lugar
nenhum, e entrega em 6 de maio.

Pausa.

— É que JavaScript é meio... — ele procurou a palavra — ...de botão.

O Rafael não levantou os olhos da tela.

— Temporário dura três anos. Esse está com quatro.

A Cláudia falou sem tirar o olho da planilha da semana.

— O painel da manhã roda em quê?

— Node — disse o Marcos.

— Qual versão?

O Rafael respondeu antes.

— Vinte. No servidor. Para de receber correção em 30 de abril.
:::

A reunião foi na quinta, 12 de março, véspera do acesso da Bia ao
repositório. Ela repetiu o que a sala já dizia. O Rafael falou a versão
que estava instalada no servidor.

Node é o programa que executa essa linguagem fora do navegador. A versão
20 é a da Borba. A data de 30 de abril faz parte do calendário público
dessa linha, e o calendário tem uma origem: em 2015 o projeto do Node
passou a publicar até quando cada versão recebe correção.

A linguagem em si começa antes, num navegador, com outro nome.

## Maio de 1995

Brendan Eich chegou à Netscape em abril de 1995. A empresa tinha pouco mais
de um ano. O Netscape Navigator era o navegador mais usado, e uma página,
naquele ano, era um documento: texto, link, figura. A Netscape queria uma
linguagem dentro do navegador para o documento reagir a um clique sem pedir
a página inteira de novo.

Havia duas pressões em cima da mesa. Uma era Java, da Sun, que a Netscape
ia licenciar: linguagem da moda, com compilação, classe e tipo
declarado, feita para programa grande. A outra era o que tinham oferecido
ao Eich na contratação: algo leve, no espírito de Scheme, para quem
escrevia página. Scheme é uma linguagem em que função é um valor, pequena o
bastante para uma pesquisa de laboratório. O acordo que saiu dali não foi
nenhuma das duas propostas inteiras.

O protótipo, escrito em maio, levou o nome interno de Mocha. Eich depois
descreveu o prazo como cerca de dez dias. Nesses dias entrou o núcleo que
a linguagem ainda tem.

Uma função era um valor. Dava para guardar esse valor num nome e entregar
a outra função. Isso vinha de Scheme. O navegador, dali em diante, pôde
tratar um clique assim: o botão recebe uma função e a chama quando o
clique acontece.

Um objeto era um conjunto de propriedades, e podia apontar para outro
objeto. Se a propriedade não está nele, a busca continua no outro. Esse
outro se chama protótipo. O modelo veio de Self, uma linguagem de objetos
sem classe. Java, ao contrário, começa pela classe: o molde existe antes
do objeto. No Mocha, o objeto existe primeiro. O `new` e as funções
construtoras entraram para a sintaxe lembrar Java de longe — chave, ponto
e vírgula, nome com inicial maiúscula — sem adotar o molde.

:::term Protótipo
O objeto para o qual outro objeto aponta quando não acha uma propriedade
em si mesmo. A busca segue esse ponteiro.

É o modelo de objeto do JavaScript desde o protótipo de maio de 1995.
Classe, no sentido de Java, não fazia parte dessa encomenda.
:::

:::term Java
Linguagem da Sun, anunciada em 1995, com classe, tipo declarado e
compilação. A Netscape ia embarcá-la no navegador para aplicação grande.

O Mocha recebeu ordem de parecer com ela na superfície. O objeto, a função
e o momento em que o programa roda ficaram de outro desenho.
:::

:::history Os dez dias
O número que circula — dez dias — é o prazo do primeiro protótipo, em
maio de 1995. Entre maio e dezembro o código foi reescrito para caber no
Navigator, ganhou dois nomes públicos e foi anunciado num contrato com
outra empresa.

O núcleo de função-como-valor e de protótipo é que atravessou esse
semestre. O prazo explica a pressa do primeiro arquivo. O arquivo que a
Lívia abre saiu de trinta anos de edição em cima desse núcleo.
:::

## O nome, em dezembro

Em setembro de 1995 o beta do Netscape Navigator 2.0 levava a linguagem
com o nome LiveScript. Em 4 de dezembro a Netscape e a Sun publicaram o
comunicado que abre este capítulo. LiveScript passou a se chamar
JavaScript. Marc Andreessen, da Netscape, queria o calor da palavra Java,
que naquele mês estava em toda palestra. O comunicado vendia os dois como
par: Java para os programadores que criam componentes, JavaScript para
quem escreve página e aplicação de empresa.

A marca ficou com a Sun. Hoje está com a Oracle, que comprou a Sun. Um
padrão internacional não podia ser publicado com a marca de um fabricante.
Esse detalhe de contrato decide o nome que o comitê usa até hoje.

O comunicado também falava em cliente e servidor. Não era figura de
linguagem vazia. Em 1996 a Netscape vendeu o LiveWire, um servidor em que
JavaScript rodava fora do navegador, ao lado da página. Esse produto teve
vida curta. Não é o ancestral do Node. O Node, treze anos depois, nasce de
outro motor e de outro jeito de tratar entrada e saída. O que o comunicado
de 1995 documenta é a intenção comercial da Netscape naquela semana, mais
um servidor que não permaneceu.

O Navigator 2.0 final saiu em março de 1996, já com o nome novo. Mocha
tinha durado a primavera. LiveScript, o outono. JavaScript é o nome que
sobrou, e é o nome que o Renato usou na quinta.

## Dois implementadores, um padrão

Em agosto de 1996 a Microsoft publicou o JScript no Internet Explorer 3.
Era a linguagem refeita por engenharia reversa, com outro nome, porque
JavaScript era marca. A página passou a ter dois implementadores que não
se comprometiam a aceitar o mesmo texto. Quem escrevia para os dois
navegadores testava nos dois, e mesmo assim encontrava diferença na
árvore de objetos que representa a página — o DOM, Document Object
Model — mais do que na linguagem em si.

A Netscape precisava de um padrão que a Microsoft aceitasse implementar.
Um padrão com o nome JavaScript esbarrava na marca. Em novembro de 1996 a
linguagem foi entregue à Ecma International. A primeira edição do
ECMA-262 saiu em junho de 1997, editada por Guy Steele, com cerca de
noventa e cinco páginas. A linguagem descrita no documento se chama
ECMAScript. O comitê que a mantém é o TC39, o comitê técnico 39 da Ecma.

:::term ECMAScript
O nome da linguagem dentro do padrão ECMA-262. JavaScript continua
sendo o nome comercial, usado pelo navegador, pelo Node e por quem
escreve.

São o mesmo idioma. Quando a edição importar, ela vem com o ano, ou com o
número antigo: ES3, ES5, ES2015.
:::

A segunda edição, em 1998, foi trabalho editorial. A terceira, em dezembro
de 1999, é a ES3: expressões regulares, `try`/`catch` — um bloco que
tenta e outro que recebe a falha — e um conjunto de operações de texto
que a página já estava pedindo. Durante anos, "JavaScript" na prática
queria dizer "o que a ES3 descreve e o
que cada navegador acrescentou por conta própria".

## A edição 4, que não foi publicada

Logo depois da ES3 o comitê começou uma quarta edição muito maior. O
rascunho, ao longo dos anos 2000, tinha classe, módulo e um sistema
de tipos opcional. Era quase uma segunda linguagem, pensada para
aplicação grande, alinhada ao que o Eich e parte do grupo queriam desde o
fim dos anos 1990.

A Adobe implementou esse rascunho. O ActionScript 3, em 2006, dentro
do Flash Player, tinha classe, pacote e tipo opcional tirados da edição 4
que ainda não existia como padrão. Quem escrevia Flash escrevia um
JavaScript que o navegador, fora do plugin, não falava.

Do outro lado, Microsoft e Yahoo consideravam o rascunho grande demais
para a página já instalada. Douglas Crockford, na Yahoo, sustentava que a
web não aguentava uma língua nova incompatível com a que já estava nos
sites. Chris Wilson, na Microsoft, estava no mesmo lado. O Eich, por um
bom tempo, esteve no lado da edição 4.

Em agosto de 2008 o impasse fechou. O grupo anunciou que a edição 4, naquela
forma, não seria publicada. O acordo recebeu o nome de Harmony. Primeiro
sairia uma edição pequena em cima da ES3, sem quebrar o que já rodava.
Depois, cada acréscimo entraria sem transformar a língua numa segunda
língua. O ActionScript 3 ficou onde estava, dentro do Flash. O JavaScript
da página não herdou aquele rascunho.

O que saiu do acordo, em dezembro de 2009, foi a ES5. Entrou o modo
estrito: uma string especial no topo de um arquivo, `"use strict"`, e o
motor passa a recusar alguns silêncios. Atribuir a um nome que ninguém
criou, por exemplo, vira erro, em vez de criar um nome visível no programa
inteiro. Entraram também operações de lista — percorrer, filtrar,
transformar — e o JSON como parte da linguagem.

:::term JSON
JavaScript Object Notation. Um texto para levar dado de um programa a
outro: chaves, nomes entre aspas duplas, listas entre colchetes. É um
recorte da forma como a linguagem já escrevia um objeto em 1995.

Douglas Crockford isolou esse recorte por volta de 2001 e publicou as
regras. Em 2009 a ES5 colocou na linguagem as funções que leem esse texto
e que o escrevem. Sistemas que não são JavaScript passaram a usá-lo como
formato neutro.
:::

## O que a página fez enquanto o padrão brigava

A ES3 ficou sozinha de 1999 até 2009. A página não ficou.

O Internet Explorer 5, ainda em 1999, tinha um objeto capaz de pedir um
dado ao servidor sem recarregar a página. O nome que grudou nesse jeito de
construir tela veio depois, num ensaio de Jesse James Garrett, em 18 de
fevereiro de 2005: Ajax. A página deixou de ser só documento. Passou a ser
um programa que conversa com um servidor e reescreve um pedaço de si.

Os objetos com que se mexe na página, porém, não eram os mesmos no
Navigator e no Internet Explorer. Em 14 de janeiro de 2006, num BarCamp em
Nova York, John Resig mostrou o jQuery: uma biblioteca que oferecia uma
escrita só para essas diferenças. A versão 1.0 saiu em agosto daquele ano.
Durante um tempo longo, aprender a fazer página dinâmica era aprender
jQuery. A linguagem e a biblioteca dividiam o mesmo arquivo, e muita gente
só via a biblioteca.

Em setembro de 2008, no mesmo ano em que o Harmony foi anunciado, o Google
publicou o Chrome. Dentro dele vinha um motor novo, o V8, escrito na
Dinamarca por um time liderado por Lars Bak. Bak tinha trabalhado no
HotSpot, o motor de Java da Sun. O V8 observa, enquanto o programa roda,
que tipos de fato passam por cada função, e compila de novo as funções que
mais rodam. JavaScript grande na página deixou de ser, por princípio, um
programa lento.

:::term V8
Motor de JavaScript do Google, publicado em 2008 com o Chrome. É o motor
que o Node usa.

O Chrome e o Node podem carregar versões diferentes desse motor. Os dois
executam a linguagem. Os dois não são obrigados a aceitar exatamente o
mesmo texto, se as versões divergirem.
:::

## Fora do navegador, de novo

Em maio de 2009 Ryan Dahl publicou a primeira versão do Node. A
apresentação que ficou conhecida é de novembro, na JSConf, em Berlim. Ele
queria um servidor capaz de segurar muitas conexões abertas ao mesmo
tempo. No modelo antigo, cada conexão ocupava uma linha de execução e
ficava parada esperando a rede. Dahl olhou para o navegador: ali o
JavaScript já vivia num laço de eventos. O programa entrega uma função,
segue, e a função roda quando a resposta chega. Uma espera de rede devolve
o controle ao laço. Uma conta longa, feita no meio, segura o clique até
terminar.

Ele tirou o V8 do Chrome e pôs em volta as peças que um navegador não tem:
arquivo, porta, processo. A escolha da linguagem teve um motivo técnico
registrado por ele: JavaScript, fora do navegador, ainda não tinha uma
biblioteca padrão de entrada e saída. Não havia um estoque de funções que
parassem o programa à espera de disco ou de rede. Dava para construir
esse estoque inteiro em cima do laço de eventos, sem misturar com outro
estilo.

:::term Laço de eventos
A fila em que o motor registra "quando isto acontecer, chame esta
função" e, no meio-tempo, executa o que já pode ser executado.

É o desenho do navegador desde que função virou valor, e é o desenho que
o Node adotou em 2009 para o servidor. O painel da Borba espera rede a
maior parte do tempo. É esse mecanismo que segura a espera.
:::

Em 2010 Isaac Schlueter publicou o npm, o comando e o registro com que um
projeto Node declara as bibliotecas de que precisa e as instala. O
registro cresceu até virar o lugar padrão de publicar JavaScript. Em 22 de
março de 2016 um pacote de onze linhas, o `left-pad`, foi removido pelo
autor, Azer Koçulu, no meio de uma disputa de nome com uma empresa. A
cadeia de instalação de milhares de projetos passava por aquelas onze
linhas. Os builds quebraram no mesmo dia. O registro voltou a publicar o
pacote com outro responsável.

## A sexta edição, e o calendário

O Harmony tinha ficado a promessa de crescer sem quebrar. A sexta edição
do ECMA-262 saiu em junho de 2015. O nome oficial é ES2015. Muita gente
ainda diz ES6, pelo número da edição.

O que entrou ali vinha direto das brigas anteriores. `let` e `const` criam
nome visível no bloco, não na função inteira: uma correção do alcance que
`var` tinha desde 1995. Módulo entra no padrão porque já existiam dois
sistemas caseiros. O Node usava `require`, função que puxa outro arquivo e
devolve o que ele exporta. No navegador, bibliotecas como o RequireJS
usavam outro formato, o AMD, para carregar arquivo pela rede. A edição de
2015 definiu `import` e `export`. Os arquivos antigos não foram reescritos
no dia da publicação. Os dois jeitos continuaram no mundo.

Classe entrou como escrita. O mecanismo continuou sendo o protótipo de
1995. A palavra `class` organiza num bloco só o que antes se escrevia como
função construtora mais um objeto de protótipo. É açúcar de sintaxe: uma
grafia mais curta para uma estrutura que o motor já executava. A edição 4
queria classe de verdade, com tipo. A edição de 2015 publicou a grafia, e
recusou a segunda língua.

Promessa entrou como objeto que representa um resultado que ainda não
chegou.
O texto entre crases, que interpola valor, também. Nenhuma dessas formas
apagou a anterior. Edição nova, nesse padrão, acumula.

Os navegadores implementaram a edição aos poucos. Em setembro de 2014
Sebastian McKenzie tinha começado um tradutor, o 6to5, rebatizado de Babel
em 2015. Ele lia o texto da ES2015 e escrevia texto que a ES5 já executava.
Quem publicava página passou a ter um passo de tradução no meio do
caminho. O passo existiu porque o padrão e os navegadores não andavam no
mesmo mês. Muitos projetos mantiveram o passo depois que os navegadores
alcançaram a edição, porque o caminho de build já estava montado em volta
dele.

Enquanto a sexta edição saía, o Node vivia outra fusão. No fim de 2014,
parte dos mantenedores discordou da Joyent, a empresa que guardava o
projeto, sobre ritmo e governança. Em janeiro de 2015 publicaram um
fork, o io.js, com versão própria e comitê aberto. Em setembro de 2015 os
dois linhas se encontraram de novo no Node 4. A partir dessa reunião, as
linhas pares ganharam prazo público de manutenção. O nome desse prazo é
LTS.

:::term LTS
*Long Term Support*. Linha do Node que recebe correção de segurança por
um período combinado, com data de término publicada antes.

A linha chamada Current é a mais nova, ainda sem esse prazo, e muda
seguido. Servidor de operação fica numa LTS.
:::

Desde 2016 o TC39 publica uma edição por ano, em geral em junho. Uma
proposta atravessa estágios públicos. O que chega ao último estágio entra
na edição daquele ano. `async` e `await` entraram na de 2017: duas
palavras para escrever, na ordem da leitura, uma função que espera uma
promessa. O comitê deixou de guardar mudança durante uma década para
soltar uma edição gigante. A edição gigante tinha sido a 4, e ela não foi
publicada.

O Node 20, o do servidor da Borba, foi publicado em abril de 2023. A data
de fim de correção, no calendário do projeto, é 30 de abril de 2026. O
Node 24 foi publicado em maio de 2025, entrou em LTS em outubro desse
ano, e recebe correção até 30 de abril de 2028. A Cláudia perguntou "qual
versão?" na quinta. A resposta do servidor é essa linha, e essa data.

:::diagram type="timeline" caption="A linguagem, do protótipo de maio de 1995 ao calendário que o servidor da Borba ainda obedece."
width: 112
events:
  - { year: "1995", text: "Maio: Mocha, na Netscape. Dezembro: o acordo com a Sun põe o nome JavaScript.", mark: true }
  - { year: "1996", text: "Agosto: JScript, no Internet Explorer. A marca impede um padrão com o mesmo nome." }
  - { year: "1997", text: "Junho: ECMA-262. No documento, a linguagem se chama ECMAScript.", mark: true }
  - { year: "1999", text: "Dezembro: ES3. Em seguida começa o rascunho da edição 4." }
  - { year: "2008", text: "Agosto: a edição 4 é abandonada. Setembro: Chrome e V8.", mark: true }
  - { year: "2009", text: "Maio: Node. Dezembro: ES5, com modo estrito e JSON.", mark: true }
  - { year: "2015", text: "Junho: ES2015. Setembro: Node 4 reúne o io.js e cria o prazo LTS.", mark: true }
  - { year: "2016", text: "Edição anual. Em março, o left-pad sai do registro npm." }
  - { year: "2026", text: "30 de abril: o Node 20 do servidor para de receber correção.", mark: true }
:::

:::summary
- Maio de 1995: Eich escreve o Mocha na Netscape. Função é valor.
  Objeto delega a um protótipo. Classe, no sentido de Java, não está
  nesse desenho.
- 4 de dezembro de 1995: a Sun e a Netscape publicam o nome JavaScript.
  A marca fica com a Sun, hoje Oracle. Por isso o padrão, em 1997, se
  chama ECMAScript.
- A edição 4 não foi publicada. Em agosto de 2008 o acordo Harmony troca
  a segunda língua por edições que não quebram a página. A ES5 sai em
  dezembro de 2009.
- O Node, em maio de 2009, tira o V8 do Chrome e adota o laço de eventos
  do navegador. O prazo LTS nasce em 2015, na reunião com o io.js.
- A ES2015, em junho de 2015, acrescenta grafia — `let`, `const`, módulo,
  classe, promessa — em cima do núcleo de 1995. O Node 20 da Borba recebe
  correção até 30 de abril de 2026.
:::

:::exercise level=1
O comunicado de 4 de dezembro de 1995 anuncia JavaScript junto com Java.
Escreva, em três linhas, quem publicou o texto, para que servia o nome
novo, e qual modelo de objeto o Mocha já tinha que não é o modelo de
classe do Java.

:::answer
A Netscape e a Sun publicaram o comunicado. O nome JavaScript foi escolhido
para acompanhar o Java, que era a linguagem da moda, num par comercial:
uma para componente, outra para página.

O Mocha, desde maio, usava protótipo. O objeto existe e aponta para outro
objeto quando lhe falta uma propriedade. Classe, o molde do Java, não era
o mecanismo. O `class` de 2015 é uma grafia posterior em cima desse
ponteiro.
:::

:::exercise level=2
Por que o padrão da linguagem não se chama JavaScript? Reconstitua os
fatos de agosto de 1996 e de junho de 1997.

:::answer
Em agosto de 1996 a Microsoft publicou o JScript no Internet Explorer 3,
uma implementação com outro nome, porque JavaScript era marca da Sun.

Um padrão que a Microsoft aceitasse implementar não podia carregar essa
marca. A Netscape entregou a linguagem à Ecma. Em junho de 1997 saiu a
primeira edição do ECMA-262. No documento, o nome é ECMAScript.
:::

:::exercise level=3
A Cláudia anotou num ticket — o registro numerado de uma tarefa — o texto
"atualizar o Node do servidor esta semana, para a versão mais nova que
existir". A semana é a de 16 de março de 2026. Você aceitaria o texto do
ticket? Justifique em três linhas, com o calendário que o projeto do Node
publica desde 2015.

:::answer
Não com esse texto. Desde a reunião com o io.js, em 2015, linha par tem
prazo LTS, e a linha Current muda sem esse prazo. "A mais nova que
existir" não diz qual das duas a Cláudia está pedindo.

O servidor está no 20, cuja correção termina em 30 de abril de 2026. Trocar
é escolher uma LTS pelo número — a 22 ou a 24 — e publicar isso num
horário em que a manhã da Lívia não dependa do resultado. O ticket não
nomeia a linha nem o horário.
:::
