---
title: "O PHP que você ouviu falar"
number: 1
slug: o-php-que-voce-ouviu-falar
part: p1
kicker: "Uma linguagem feita para contar visitas num currículo, e que hoje atende uma parte enorme da web — com tipos, enums e uma versão nova todo novembro."
epigraph: "Eu não sabia como parar. Eu não tinha ideia de como escrever uma linguagem de programação. Eu só fui acrescentando o próximo passo lógico no caminho."
epigraph_by: "Rasmus Lerdorf, criador do PHP"
goal: >-
  Saber de onde vem o PHP, o que causou a fama antiga e quando cada causa
  foi removida, o que a linguagem tem hoje, o que ela resolve bem, quem a
  usa e por que ela não vai morrer tão cedo.
---

:::story Não dava pra fazer em Node?
O Dr. Aurélio tinha visto uma palestra na quinta e voltou com uma pergunta
na sexta.

— Esse projeto da biblioteca. Por que PHP?

— O sistema atual é PHP — disse Dedé. — A hospedagem é PHP. A Vera usa PHP
desde 2009.

— Mas a gente não ia modernizar?

— Vamos. De PHP 5.4 para PHP 8.

O Dr. Aurélio fez o gesto de quem tira uma coisa da frente do rosto.

— Não dava pra fazer em Node?

— Dava.

— Então.

— Aí a gente reescreve tudo, joga fora quinze anos de regra de negócio que
não está documentada em lugar nenhum, e entrega em 31 de março.

Pausa.

— É que PHP é meio... — ele procurou a palavra — ...antigo.

— A versão atual saiu em novembro.

Márcia falou sem levantar os olhos da planilha.

— A folha de pagamento da Vertexo roda em quê?

Cléber pigarreou.

— PHP.

— Qual versão?

— Cinco ponto seis.
:::

Essa conversa acontece em algum lugar do mundo todo dia, e o mal-entendido é
sempre o mesmo: a fama do PHP descreve, com precisão, uma linguagem que
deixou de existir há mais de dez anos.

Os defeitos que a geraram foram reais, tinham nome e tinham data — e todos
eles foram removidos, um a um, entre 2012 e 2021. O PHP que você vai
aprender aqui não é aquele com remendos: é uma linguagem tipada, rápida e
previsível, com calendário de versões público e uma década de correções
feitas.

Vale gastar um capítulo entendendo essa diferença por dois motivos. O
primeiro é que ela explica as decisões estranhas que você vai encontrar em
código antigo — e você vai encontrar, porque quinze anos de PHP continuam
rodando. O segundo é que ela é o argumento que você vai querer ter na ponta
da língua quando alguém repetir a piada numa reunião.

## Um currículo, em 1994

Rasmus Lerdorf era um programador dinamarquês-canadense que queria saber
quantas pessoas visitavam o currículo dele na internet. Escreveu, em C, um
punhado de programinhas que faziam isso e chamou o conjunto de **Personal
Home Page Tools**.

Não era uma linguagem. Era um utilitário pessoal, publicado em 1995 porque
outras pessoas pediram.

O que aconteceu depois é a coisa mais importante da história do PHP: ele
**cresceu por demanda, não por projeto**. Alguém precisava falar com banco
de dados, então apareceu uma função. Alguém precisava processar formulário,
então apareceu um jeito. Cada pedido virou uma função nova, com o nome que
pareceu razoável naquele dia, na ordem de argumentos que pareceu razoável
naquele dia.

Vinte e cinco anos depois, é por isso que `strlen($texto)` recebe o texto
primeiro e `in_array($agulha, $palheiro)` recebe a agulha primeiro. Ninguém
decidiu isso. Isso aconteceu.

:::trivia
O nome é um acrônimo recursivo: **PHP: Hypertext Preprocessor**. Ele começa
por uma sigla que se refere a si mesma, o que é uma piada de programador dos
anos 1990, e substituiu o nome original — *Personal Home Page* — quando ficou
claro que a coisa tinha passado do currículo do Rasmus.
:::

Em 1997, dois estudantes em Haifa, Andi Gutmans e Zeev Suraski, resolveram
reescrever o interpretador porque queriam usar PHP num trabalho de faculdade
e ele não aguentava. Dessa reescrita saiu o PHP 3, e da empresa que os dois
fundaram saiu o motor que roda a linguagem até hoje.

## Os marcos que ainda afetam o seu código

:::diagram type="timeline" caption="Por que a linguagem é assim: os marcos que você vai encontrar em código real."
width: 112
events:
  - { year: "1995", text: "Rasmus Lerdorf publica o PHP Tools: contar visitas num currículo" }
  - { year: "1998", text: "PHP 3, reescrito por Gutmans e Suraski — a linguagem começa aqui", mark: true }
  - { year: "2004", text: "PHP 5: objetos de verdade, exceções e PDO" }
  - { year: "2009", text: "PHP 5.3 traz namespaces e closures, dez anos atrasado", mark: true }
  - { year: "2010", text: "PHP 6 é abandonado sem nunca existir; o número foi pulado" }
  - { year: "2012", text: "Composer: dependências resolvidas por ferramenta, não por FTP", mark: true }
  - { year: "2015", text: "PHP 7: cerca de duas vezes mais rápido, e tipos em parâmetros", mark: true }
  - { year: "2020", text: "PHP 8: match, enums a caminho, argumentos nomeados, JIT", mark: true }
  - { year: "2021", text: "PHP 8.1: enums e readonly — a linguagem fica tipada de verdade" }
  - { year: "2024", text: "PHP 8.4: property hooks; uma versão nova por ano, todo novembro" }
:::

Repare em duas datas.

**2009** é quando o PHP ganhou namespaces — a forma de organizar código em
pacotes sem que dois arquivos briguem pelo mesmo nome. Até então, a saída
era escrever classes chamadas `Zend_Db_Table_Row_Abstract`. Todo código PHP
anterior a essa data tem essa cara, e ele ainda está rodando em algum lugar.

**2015** é quando a linguagem ficou rápida. O PHP 7 trouxe um motor novo e
cerca do dobro do desempenho da versão anterior, sem que ninguém precisasse
mudar uma linha. Foi a maior atualização de graça da história da web, e boa
parte da economia de servidores daquela década saiu dali.

:::trivia
O **PHP 6** existiu por cinco anos em forma de tentativa: uma reescrita para
tratar texto em Unicode de ponta a ponta. Ela se provou grande demais e foi
abandonada por volta de 2010.

Quando a versão seguinte ficou pronta, a comunidade votou por pular o número
6 e chamá-la de 7 — porque já existiam livros publicados sobre "PHP 6" que
descreviam uma linguagem que nunca foi lançada. É a única linguagem popular
que pulou uma versão inteira para não confundir quem tinha comprado o livro
errado.
:::

## De onde veio a fama, e o que foi feito de cada coisa

A reputação antiga não foi preconceito: teve quatro causas concretas, e as
quatro eram verdade. Elas estão aqui por dois motivos práticos — para você
reconhecê-las quando abrir um sistema de 2009, e para saber, de cada uma,
em que versão ela deixou de existir.

**`register_globals`.** Até o PHP 4.2, ligado por padrão: qualquer parâmetro
que chegasse na URL virava automaticamente uma variável dentro do seu
programa. Uma página que checava `if ($admin)` podia ser acessada com
`?admin=1`. Foi removido só no PHP 5.4, em 2012.

**`magic_quotes`.** O PHP escapava sozinho tudo que vinha de formulário, na
esperança de evitar ataques de injeção. O efeito real foi produzir uma
geração de programadores que achava estar protegida sem estar, e um banco de
dados cheio de `O\'Brien`. Removido na mesma versão.

**As funções `mysql_*`.** O jeito antigo de falar com banco de dados era
montar a consulta grudando texto. Isso funciona e convida ao maior buraco de
segurança da história da web. Foram desaconselhadas em 2013 e removidas em
2015 — vinte anos depois de terem ensinado o hábito a todo mundo.

**A falha silenciosa da biblioteca padrão.** Funções internas devolviam
`false` quando davam errado, em vez de reclamar — e um programa que não
conferia o retorno seguia em frente com um valor inválido na mão. Isso
acabou no PHP 8.0, em 2020: essas funções passaram a lançar exceção, e o
erro parou de poder ser ignorado.

Sobrou a parte cosmética dessa história — `strlen($texto)` recebe o texto
primeiro e `in_array($agulha, $palheiro)` recebe a agulha primeiro. Os nomes
e as ordens continuam como estão porque mudá-los quebraria milhões de sites
que funcionam, e essa é a decisão certa. Na prática, é um detalhe que o
editor de código resolve enquanto você digita.

| A causa | Quando deixou de existir |
|---|---|
| `register_globals` | PHP 5.4, em 2012 |
| `magic_quotes` | PHP 5.4, em 2012 |
| funções `mysql_*` | PHP 7.0, em 2015 |
| falha silenciosa nas funções internas | PHP 8.0, em 2020 |
| ausência de tipos declarados | PHP 7.0 em 2015; enums e `readonly` em 2021 |

Tabela: Nenhum item desta lista descreve o PHP que você vai instalar. Todos
descrevem código que ainda pode estar rodando em algum servidor.

Em 2012, um texto chamado *"PHP: a Fractal of Bad Design"* catalogou tudo
isso e virou a referência de quem quer atacar a linguagem. Ele é longo,
detalhado e estava certo quando foi escrito.

O que raramente se menciona é o que aconteceu depois: a comunidade leu,
concordou com boa parte e passou uma década consertando, item por item, na
ordem em que eles apareciam na crítica. Hoje o texto é documento histórico —
e a linha do tempo da coluna acima é a resposta a ele.

## O que mudou de verdade

Quatro coisas, e só a primeira é sobre sintaxe.

**A linguagem ficou tipada.** Você pode declarar o tipo de cada parâmetro,
de cada retorno e de cada propriedade, e pedir que o PHP recuse o que não
encaixar. Existem `enum`, `readonly`, `match` e tipos que combinam outros
tipos. Não é Java, e não é mais a terra sem lei de 2009.

**Apareceu um jeito de instalar código dos outros.** Antes de 2012, usar uma
biblioteca significava baixar um `.zip`, copiar numa pasta e torcer. O
Composer trouxe o que Ruby, Python e Node já tinham: um arquivo declarando o
que o projeto usa, e um comando que resolve o resto.

**Apareceram convenções compartilhadas.** Um grupo de mantenedores de
projetos grandes passou a publicar padrões — as PSR — dizendo como nomear
arquivos, como carregá-los, como registrar log, como representar uma
requisição HTTP. Isso soa burocrático e é o motivo de bibliotecas de autores
diferentes hoje funcionarem juntas.

**Apareceram ferramentas que leem o seu código.** Analisadores estáticos
como o PHPStan e o Psalm encontram, sem rodar nada, o erro de digitação que
antes só aparecia em produção às três da manhã.

Vale parar um segundo no que essa lista significa, porque é o argumento mais
forte a favor da linguagem e quase nunca é feito.

Uma linguagem com trinta anos de vida acumula decisões ruins — todas
acumulam. O que distingue uma ferramenta em que vale a pena investir uma
carreira não é nunca ter errado: é o que ela faz com o erro depois de
descoberto.

O PHP removeu os próprios recursos perigosos, em versões numeradas, com data
e aviso prévio. Trocou o motor inteiro e entregou o dobro de desempenho sem
cobrar reescrita. Adotou gerenciador de pacotes, tipos, padrões de
interoperabilidade e análise estática — cada um depois de uma discussão
pública, com voto registrado.

É uma década de dívida técnica paga à vista, em público, por um projeto que
poderia ter escolhido só não mexer. Muita linguagem que hoje é citada como
"a escolha segura" nunca precisou fazer isso, e ninguém sabe como ela se
comportaria se precisasse.

:::key
Escolher uma tecnologia é apostar no que ela vai ser daqui a cinco anos, não
no que ela foi há quinze.

Os sinais que importam nessa aposta são três, e o PHP tem os três: **versão
nova em calendário fixo**, **processo de decisão público** e **histórico de
consertar o que estava errado em vez de defender**.
:::

## O que o PHP resolve bem

Vale ser específico, porque "é bom para web" não explica nada.

**Cada requisição começa do zero.** Quando alguém pede uma página, o PHP
monta tudo, responde e joga tudo fora. Nada sobrevive para a requisição
seguinte.

Isso parece desperdício e é uma vantagem enorme: não existe vazamento de
memória que se acumula durante uma semana, não existe estado compartilhado
entre usuários, não existe variável global contaminada pela requisição
anterior. Uma categoria inteira de defeitos difíceis simplesmente não tem
onde acontecer. Quem já caçou um vazamento num processo que roda há trinta
dias sabe exatamente o tamanho desse presente.

**Publicar é copiar arquivo.** Não há compilação obrigatória, não há
processo para reiniciar, não há servidor de aplicação para configurar.
Projeto moderno acrescenta etapas por bons motivos, mas o mínimo continua
sendo o mínimo — e é por isso que existe hospedagem de PHP por quinze reais
por mês em qualquer lugar do mundo.

**Vem com pilhas para web.** Sessão, upload, data, texto, JSON, cliente
HTTP, drivers de banco: está tudo na caixa, sem instalar nada.

**É rápido o bastante.** A pergunta relevante em aplicação web quase nunca é
a velocidade da linguagem — é quanto tempo o banco de dados demora. O PHP 8
com cache de código compilado atende bem a esmagadora maioria dos sistemas
que alguém vai escrever.

:::term OPcache
O PHP lê o seu arquivo `.php` e o converte para instruções internas antes de
executar. O OPcache guarda essa conversão na memória, para que ela não
aconteça de novo a cada requisição. Vem junto com o PHP e é ligado por
padrão desde a versão 5.5 — e é boa parte do motivo de a linguagem ser
rápida hoje.
:::

## E o que ele não resolve

A mesma lista, ao contrário, e ela é curta e honesta.

**Processo que fica vivo.** WebSocket, conexão aberta por horas, milhares de
conexões simultâneas esperando: isso vai contra o modelo de "começa do zero
e morre". Existem projetos que resolvem, e todos eles estão remando contra a
maré.

**Conta pesada.** Processamento numérico, treinamento de modelo,
transformação de vídeo. A resposta certa é outra linguagem, chamada a partir
do PHP.

**Estado compartilhado na memória.** Como nada sobrevive entre requisições,
tudo que precisa ser lembrado vai para fora — banco, Redis, arquivo. É
trabalho a mais, e é o preço direto da vantagem do item anterior.

Nenhum desses itens é um defeito. São o contorno da ferramenta, e saber onde
ele passa é o que separa escolher de repetir.

## Quem usa

A **Wikipédia** roda em MediaWiki, que é PHP. O **WordPress**, que sustenta
uma fatia enorme dos sites do mundo, é PHP. **Etsy**, **Tumblr**,
**Mailchimp** e **Vimeo** têm PHP no núcleo — a equipe do Vimeo, aliás,
escreveu um dos analisadores estáticos mais usados da linguagem.

O **Facebook** foi escrito em PHP e cresceu nele até o ponto em que passou a
manter o próprio dialeto, o Hack, que roda num motor próprio. O mesmo
caminho foi seguido pelo **Slack**. Isso costuma ser citado como prova de
que o PHP não escala; a leitura mais honesta é que duas das maiores
aplicações web do mundo foram construídas em PHP e só precisaram de outra
coisa depois de ultrapassar um tamanho que o seu sistema provavelmente não
vai ter.

Na Europa, boa parte dos sistemas corporativos em PHP é feita sobre o
Symfony — de companhia ferroviária a plataforma de carona. No Brasil, o PHP
está onde está o dinheiro do mercado intermediário: agências, e-commerce,
ERPs de médio porte, sistemas de gestão, edtechs e o balcão de milhares de
empresas que nunca vão aparecer numa conferência.

:::key
Você vai ver a estatística de que "cerca de três quartos dos sites da web
usam PHP". Ela é real e vem de levantamentos de tecnologia de servidor, e
merece uma ressalva honesta: ela conta **sites**, não faturamento nem
tráfego, e é fortemente puxada pelo WordPress.

Isso não a torna inútil — só muda o que ela prova. Nenhuma estatística de
adoção prova qualidade técnica, de nenhuma linguagem. O que essa prova é
mercado: existe uma quantidade gigantesca de PHP em produção, e alguém
precisa mantê-lo, evoluí-lo e substituí-lo por sistemas novos.

A qualidade técnica se argumenta pelo que a linguagem tem hoje — tipos,
enums, imutabilidade, análise estática, um dos ecossistemas de framework
mais maduros da web —, e por isso ela ocupa um capítulo inteiro em vez de
uma porcentagem.
:::

## PHP é imorrível

Anunciar a morte do PHP virou gênero literário. Sai pelo menos um texto por
ano, com epitáfio e substituto indicado, e o primeiro deles é mais velho que
boa parte da gente que trabalha com a linguagem hoje.

O mesmo acontece com Java, com C e com COBOL, por um motivo que não é
técnico: linguagem que ninguém usa não rende artigo. Na prática, o anúncio
de morte funciona como indicador de uso.

Três motivos concretos sustentam a relevância do PHP, e nenhum deles é
nostalgia.

**O primeiro é o estoque.** Software em produção não é reescrito; é mantido.
Sistemas que funcionam e dão lucro não param por cinco meses para trocar de
linguagem, e a maior parte das vagas de qualquer tecnologia existe por causa
do que já foi escrito, não do que vai ser.

**O segundo é que ainda se começa projeto novo nele.** O Laravel é um dos
frameworks web mais usados do mundo, com um ecossistema comercial em volta
que sustenta gente pagando conta. Não é nostalgia: é gente escolhendo hoje.

**O terceiro é a cadência.** Desde 2015 sai uma versão por ano, todo
novembro, com dois anos de correção ativa e mais um de correção de
segurança. A linguagem tem plano, tem calendário e tem processo de decisão
público.

E a delimitação honesta, porque ela faz parte do quadro: o PHP não é a
linguagem da moda. Isso é diferente de estar em declínio — moda mede o que
se fala em conferência; produção mede o que roda na terça-feira. Se o seu
objetivo é trabalhar com aprendizado de máquina, com sistemas de baixo nível
ou com aplicativo nativo, este é o livro errado e a ferramenta errada, e não
por defeito dela.

Se o seu objetivo é construir e manter sistemas que atendem empresas de
verdade, e ser pago por isso, você escolheu bem. A linguagem está mais
sólida do que em qualquer momento da história dela, a comunidade provou que
conserta o que quebra, e a piada de vinte anos vale exatamente o que valem
as piadas de vinte anos.

:::practice
Duas conferências de cinco minutos, para trazer este capítulo para o mundo
real.

**A primeira:** procure por "PHP supported versions" e olhe o calendário
oficial. Ele mostra, por versão, até quando há correção de defeito e até
quando há correção de segurança. Anote a data da versão que você acabou de
instalar — e, se um dia você herdar um sistema, essa é a primeira página a
abrir.

**A segunda:** pense em três sites que você usa toda semana e descubra em
que tecnologia cada um roda. Extensões de navegador fazem isso num clique.
O resultado costuma surpreender em pelo menos um dos três.
:::

:::summary
- O PHP nasceu em 1994 como utilitário pessoal e cresceu por demanda, não
	por projeto — daí os nomes de função inconsistentes, que ficaram por
	compatibilidade e hoje são um detalhe do editor.
- A fama antiga tem causas datadas, e todas foram removidas:
	`register_globals` e `magic_quotes` em 2012, `mysql_*` em 2015, falha
	silenciosa em 2020.
- O PHP 7 dobrou o desempenho em 2015 sem cobrar reescrita; o 8 trouxe
	tipos, `match` e enums.
- Uma década de dívida técnica paga em público, com voto registrado, é o
	melhor sinal disponível sobre o que a linguagem vai ser daqui a cinco
	anos.
- Cada requisição começa do zero e morre no fim: some uma categoria inteira
	de defeitos, e some também o estado compartilhado em memória.
- Ele resolve bem sistema web de dados e regra de negócio; resolve mal
	processo longo e conta pesada.
- Wikipédia, WordPress, Etsy, Tumblr, Mailchimp e Vimeo rodam PHP; Facebook
	e Slack rodam um dialeto dele.
- A relevância vem do estoque em produção, de projeto novo ainda começando
	nele, e de uma versão por ano com calendário público.
:::

:::exercise level=1
Rode `php -v` e escreva, em uma frase, o que cada parte da primeira linha
significa. Depois descubra se a sua versão ainda recebe correção de
segurança.

:::answer
```text
$ php -v
PHP 8.3.14 (cli) (built: Nov 21 2026 09:42:15) (NTS)
```

`8.3.14` é a versão: família 8, edição 3, correção 14. O `(cli)` diz que
este é o PHP de linha de comando, e não o que atende o navegador — essa
distinção vai custar tempo de alguém no próximo capítulo. A data entre
parênteses é de quando aquele executável foi compilado, não de quando a
versão saiu. `NTS` quer dizer *non thread safe*, que é a variante normal em
Linux.

O calendário oficial de versões diz até quando cada família recebe correção.
A regra prática: uma versão tem dois anos de correção de defeito e mais um
de correção de segurança. Rodar uma versão fora dessa janela é uma decisão —
e precisa estar escrita em algum lugar como decisão, não como esquecimento.
:::

:::exercise level=2
A Casa Amarela roda PHP 5.6. Escreva, em cinco linhas, o argumento que você
apresentaria ao Seu Juvenal — que não é técnico e paga a hospedagem — para
justificar a atualização. Depois escreva o mesmo argumento para o Dr.
Aurélio, que é técnico o bastante para perguntar "e o risco?".

:::answer
**Para o Seu Juvenal**, o argumento é risco e dinheiro, sem jargão:

> A versão que a biblioteca usa parou de receber correção de segurança em
> 2018. Qualquer falha descoberta de lá para cá continua aberta no nosso
> sistema, e o cadastro tem nome, documento e endereço de mil e duzentas
> pessoas do bairro. A atualização entra no orçamento do edital; um
> incidente com dados de morador, não.

**Para o Dr. Aurélio**, o argumento é o risco da própria mudança, porque é
isso que ele vai perguntar:

> A atualização quebra código que usa funções removidas no PHP 7 — no nosso
> caso, todo o acesso ao banco. Por isso não vamos atualizar o sistema
> antigo: vamos construir o novo já em 8.3 e manter o antigo no ar até a
> virada. O risco fica isolado no que estamos escrevendo, e a data de
> desligar o antigo vira uma decisão, não um acidente.

Repare no que muda entre as duas: não é o nível de detalhe técnico, é **qual
risco cada pessoa está encarregada de avaliar**. Uma responde pelo dinheiro
e pelos moradores; a outra, pela entrega. Mandar o segundo texto para o Seu
Juvenal seria falar sozinho.
:::
