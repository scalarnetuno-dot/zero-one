---
title: "O que vamos construir"
number: 2
slug: o-que-vamos-construir
part: p1
kicker: "Onze caixas num slide, sessenta e oito mil reais de prazo, e ninguém na sala capaz de dizer o que o sistema faz hoje."
epigraph: "Andar sobre as águas e desenvolver software a partir de uma especificação são fáceis — desde que ambas estejam congeladas."
epigraph_by: "Edward V. Berard"
goal: >-
  Entender o que é uma API e por que a Casa Amarela precisa de uma, separar
  livro de exemplar de empréstimo, e terminar com PHP, Composer e editor
  instalados e conferidos.
---

:::story Jornada de Modernização 360°
O slide tinha onze caixas ligadas por setas e, no meio, uma caixa maior,
escrita **CORE**.

— É simples — disse o Dr. Aurélio. — A gente moderniza o core, expõe via
API, plugga o mobile e escala.

Ele tinha vendido o projeto a uma associação de moradores em quarenta
minutos usando essas quatro palavras, o que é um talento de verdade.

Dedé levantou a mão.

— O que o core faz hoje?

Houve um silêncio de três segundos, que numa reunião de doze pessoas dá
tempo de alguém tossir de propósito.

— Ele... processa — disse Cléber.

— Processa o quê?

Cléber tinha oito anos de Vertexo e já havia aprendido que resposta precisa
vira tarefa com o seu nome. Olhou para a Márcia.

— O Nonato sabe — disse Márcia.

— O Nonato está de férias.

— Volta dia 28.

— E a gente entrega quando?

Márcia respondeu sem consultar nada, porque administrava datas do jeito que
um bombeiro administra fósforo.

— A prestação de contas do edital é 31 de março.

— E se passar de 31 de março?

— A gente devolve sessenta e oito mil reais para a prefeitura.

A reunião durou mais cinquenta minutos e produziu três decisões
arquiteturais sobre um sistema que ninguém presente conseguia descrever.
:::

Às sete da noite daquela mesma terça, Dedé passou na Casa Amarela para
devolver um livro atrasado e ver, com os próprios olhos, o que a Vertexo
tinha acabado de se comprometer a substituir.

:::story Quarenta segundos
— Você é o do computador? — perguntou a Vera, sem levantar os olhos da
etiqueta.

— Sou.

— O Sistema tá ruim.

— Ruim como?

Ela apontou o monitor com o queixo. Tela cinza, formulário de dezoito
campos, três deles chamados `obs`, `obs2` e `obs_nova`.

— Quando duas pessoas emprestam ao mesmo tempo, some um. Quando eu imprimo
o relatório de atrasados, ele trava na terceira página. Quando alguém
devolve no domingo, ele cobra multa, e domingo a gente nem abre. E o de
sempre: se você procurar "Machado de Assis" com dois espaços no meio, ele
diz que não tem.

— Há quanto tempo?

— O do domingo, uns quatro anos. Os outros eu já nem lembro.

— E ninguém arrumou?

Vera colou a etiqueta, alisou com o polegar e pegou o próximo livro.

— Todo ano vem um moço e diz que vai arrumar. Você é o quarto.
:::

## A pergunta que trava o projeto

A reunião da manhã não foi um caso de incompetência. Aconteceu o que
acontece em empresa de qualquer tamanho: o sistema é antigo, quem escreveu
saiu ou está de férias, e a cobrança por um cronograma chega antes do
entendimento.

O resultado é sempre o mesmo — decisões de arquitetura tomadas em cima de
uma caixa escrita **CORE**.

Repare em quem, das doze pessoas da reunião, conseguiu descrever o
comportamento do sistema: ninguém. E repare em quanto tempo a Vera levou
para descrever o dela: quarenta segundos, sem parar de etiquetar, com quatro
defeitos, uma frequência e uma data aproximada para cada um.

:::note Na sua carreira
"O que esse sistema faz hoje?" é a pergunta mais barata e mais impopular de
qualquer projeto de modernização. Ela costuma travar a reunião — e travar a
reunião é exatamente o serviço que ela presta.

Quando for você a perguntar, peça um **exemplo**, não uma definição: *"me
mostra uma coisa que um usuário faz nesse sistema, do começo ao fim"*.
Definição todo mundo improvisa. Exemplo, não.

E anote a resposta na frente de quem respondeu. Uma descrição de sistema que
não foi escrita na hora vira, duas semanas depois, duas descrições
diferentes.
:::

## Três programas querendo o mesmo dado

Antes de decidir qualquer coisa técnica, vale entender por que a Casa
Amarela precisa de mais do que uma tela nova.

Hoje existe um programa só: aquele monitor cinza, naquela mesa, atrás
daquele balcão. Ele é o sistema inteiro. Quem não está de pé na frente da
Vera não consegue consultar nada.

O que a associação comprou com os sessenta e oito mil são três coisas:

| Quem usa | O que precisa fazer |
|---|---|
| a Vera, no balcão | cadastrar livro, emprestar, receber devolução |
| o morador, no celular | ver o acervo e os próprios empréstimos |
| o totem da entrada | buscar um título e dizer se tem exemplar livre |

Tabela: Três telas diferentes, um acervo só.

São três programas distintos, escritos por pessoas distintas, possivelmente
em linguagens distintas. E os três precisam da mesma informação e das mesmas
regras. Se cada um conversar com os dados do seu jeito, a regra de "pode
emprestar?" vai existir em três versões — e elas vão divergir em três
velocidades diferentes.

A saída é ter **um** programa que sabe as regras, e combinar um jeito de os
outros três pedirem as coisas a ele.

Esse "jeito combinado" tem nome.

:::term API
*Application Programming Interface*, interface de programação. É um contrato
entre dois programas: um sabe fazer alguma coisa, o outro precisa que ela
seja feita, e existe uma forma acordada de pedir e de responder.
:::

A Vera é uma API há trinta e um anos e ninguém nunca a chamou assim. Você
chega ao balcão, diz o nome do livro e mostra a carteirinha; ela responde
com o livro, ou com "está emprestado, volta quinta". Você não precisa saber
onde fica a estante, nem como ela decide o prazo. Você precisa saber **o que
pedir** e **em que formato ela responde**.

É exatamente isso que vamos escrever. A diferença é que o pedido vai chegar
pela rede, e a resposta vai sair em texto que outro programa consegue ler.

## Como um programa pede uma coisa a outro

Quando o aplicativo do morador quer registrar um empréstimo, ele manda pela
rede um bloco de texto parecido com este:

```text
POST /emprestimos
Content-Type: application/json

{"exemplar_id": 812, "leitor_id": 47}
```

São três partes, e todas fazem sentido em português.

A primeira linha diz **o que fazer** (`POST`, que significa "crie uma coisa
nova") e **onde** (`/emprestimos`). A segunda diz em que formato o pedido
está escrito. Depois de uma linha em branco vem o pedido em si: qual
exemplar, para qual leitor.

O `POST` é um dos cinco verbos que você vai usar o livro inteiro:

| Verbo | Significa | Exemplo |
|---|---|---|
| `GET` | me dê | `GET /livros` |
| `POST` | crie um novo | `POST /emprestimos` |
| `PUT` | substitua inteiro | `PUT /livros/12` |
| `PATCH` | altere um pedaço | `PATCH /livros/12` |
| `DELETE` | remova | `DELETE /livros/12` |

Tabela: Cinco verbos cobrem quase tudo que uma API faz.

Repare no endereço: `/emprestimos`, e não `/criarEmprestimo`. O verbo já
está do lado de fora, na primeira palavra. Quem coloca o verbo dentro do
endereço acaba com `/criarEmprestimo`, `/renovarEmprestimo` e
`/devolverEmprestimo` — três endereços para a mesma coisa, e nenhum deles
combinável com nada.

E toda resposta começa com um número de três dígitos:

| Faixa | Quer dizer | Os que aparecem no projeto |
|---|---|---|
| `2xx` | deu certo | `200` (aqui está), `201` (criei), `204` (feito, sem conteúdo) |
| `4xx` | quem pediu errou | `404` (não existe), `422` (dado inválido) |
| `5xx` | quem respondeu errou | `500` (quebrei) |

Tabela: O número é a primeira coisa que o outro programa lê — muitas vezes é
a única.

Um aplicativo não interpreta a frase "não foi possível realizar a operação".
Ele olha o número, e decide entre mostrar um erro, tentar de novo ou pedir
para o usuário fazer login. Devolver `200` junto com uma mensagem de erro é
o equivalente a dizer "sim" balançando a cabeça em negativo.

## O campo que confundia tudo

Na quarta-feira, Dedé sentou com a Vera para entender como o acervo estava
organizado. A tela de cadastro do Sistema tinha, entre os dezoito campos,
um chamado **Quantidade**.

Emprestar, no Sistema, subtraía um daquele campo. Devolver somava um.

Funciona. Funcionou por quinze anos.

Aí ele começou a perguntar.

:::story Cinco perguntas
— Qual exemplar do *O Cortiço* está com a Dona Marlene?

Vera abriu a gaveta do balcão e puxou uma ficha de papel pautado, dessas de
fichário, com um número escrito a caneta no canto superior: **2.117**.

— Esse.

— E o Sistema sabe disso?

— O Sistema sabe que tem três.

— E qual dos três está rasgado?

— O 2.119. Tem uma página solta no meio.

— E o que sumiu em 2017?

— O 2.118. Levaram e não voltou.

— O Sistema sabe?

— O Sistema sabe que tem três.

Dedé olhou de novo para a tela. **Quantidade: 3**.

Havia três fichas de papel na gaveta da Vera e um número na tela. As fichas
respondiam cinco perguntas. O número respondia meia.
:::

## Uma coisa, várias coisas e um acontecimento

Duas frases que parecem iguais e não são:

> "A biblioteca tem *O Cortiço*."
>
> "A biblioteca tem três *O Cortiço*."

A primeira fala do **livro**: título, autor, editora, ano, assunto. Existe
um só, e ele não pode ser emprestado. Ninguém leva um título para casa.

A segunda fala do **exemplar**: o objeto físico, com número de tombo,
estado de conservação e uma etiqueta colada na lombada. É ele que sai pela
porta, rasga, some e volta.

:::term Tombo
O número que identifica cada objeto do acervo, um por um. É o que a Vera
escreve a caneta no canto da ficha. Duas cópias do mesmo livro têm o mesmo
título e tombos diferentes.
:::

O campo **Quantidade** é o que sobra quando alguém funde os dois conceitos
em um. Ele guarda a *contagem* e joga fora a *identidade* — e identidade é
justamente o que todas as cinco perguntas pediam.

Falta ainda um terceiro conceito, que no Sistema não existe em lugar nenhum:
o **empréstimo**. Ele não é uma característica de nada. É um acontecimento:
tal exemplar saiu com tal leitor, em tal dia, para voltar em tal outro.
Acabou, virou histórico — e o histórico é de onde saem todas as perguntas
interessantes que a Casa Amarela nunca conseguiu responder.

:::diagram type="blocks" caption="Um título, vários objetos, e um acontecimento que liga um objeto a uma pessoa."
rows:
  - [{ text: "Livro", note: "O Cortiço · Aluísio Azevedo · 1890" }]
  - [{ text: "Exemplar 2.117", note: "bom estado" }, { text: "Exemplar 2.118", note: "extraviado em 2017" }, { text: "Exemplar 2.119", note: "página solta" }]
  - [{ text: "Empréstimo", note: "exemplar 2.117 · Marlene · saiu 04/02 · volta 18/02" }]
:::

Três nomes no lugar de um campo. Em troca, as cinco perguntas da Vera
deixam de depender da gaveta.

E a tal **Quantidade** não precisa mais ser guardada: ela passa a ser
**contada** — quantos exemplares deste livro não estão emprestados agora.
Parece mais trabalho e é menos, por um motivo que vale guardar: número
guardado pode divergir da realidade, número contado não. Quando Dedé
conferiu, o campo Quantidade estava errado em quatorze livros, e ninguém
sabia desde quando.

:::art caption="Um número na tela; três objetos diferentes no mundo."
src="um-numero-na-tela-tres-objetos-diferentes-no-mundo.png"
Charge editorial minimalista em fundo branco. À esquerda, um monitor antigo
de tubo mostrando um único campo grande: "Quantidade: 3". À direita, três
exemplares muito diferentes do mesmo livro: um novo, um rasgado com páginas
soltas, e um terceiro representado apenas por um retângulo pontilhado vazio
com uma etiqueta caída. Entre os dois lados, uma seta fina que só vai da
direita para a esquerda. Poucos elementos, traço de revista de tecnologia,
humor seco.
:::

## Instalar e conferir

Três coisas, todas gratuitas, e um teste para cada uma.

Primeiro, a linguagem:

```text
$ php -v
PHP 8.3.14 (cli) (built: Nov 21 2026 09:42:15) (NTS)
Copyright (c) The PHP Group
Zend Engine v4.3.14, Copyright (c) Zend Technologies
```

A única parte que importa agora é o começo da primeira linha. Se aparecer
`8.3` ou mais alto, está pronto. Se aparecer `7.4`, metade do que este livro
ensina não vai rodar na sua máquina.

| Sistema | Como instalar |
|---|---|
| Ubuntu / Debian | adicione o PPA `ondrej/php`, depois `apt install php8.3-cli` |
| macOS | `brew install php` |
| Windows | baixe em `windows.php.net/download`, ou use o WSL2 com Ubuntu |

Tabela: No Windows, o WSL2 poupa dor de cabeça quando o projeto ganhar banco
de dados — o ambiente fica parecido com o do servidor.

Depois, o Composer, que é o instalador de bibliotecas do PHP:

```text
$ composer --version
Composer version 2.8.4 2026-10-30 12:18:44
```

Ele só entra em cena quando o projeto tiver dependências, mas instalar agora
evita parar tudo no meio de um assunto para resolver instalação.

E um editor: VS Code, PhpStorm, Vim, Zed. Qualquer um serve, desde que você
consiga abrir uma pasta e salvar arquivos `.php`.

:::practice
Rode `php -m`. Sai uma lista de nomes em coluna: são as **extensões**
compiladas no seu PHP, ou seja, os pedaços opcionais da linguagem que
alguém decidiu incluir quando montou esse pacote.

Procure por quatro: `mbstring`, `json`, `intl` e `pdo_mysql`. As duas
primeiras você usa já nas próximas semanas de leitura; as outras duas fazem
falta quando o acervo sair da memória do programa e for para um banco de
dados. Se alguma não estiver na lista, instale agora — no Ubuntu,
`apt install php8.3-mbstring`, e assim por diante.

Descobrir que falta uma extensão hoje custa cinco minutos. Descobrir no meio
de um capítulo custa uma tarde e a vontade de continuar.
:::

:::summary
- "O que esse sistema faz hoje?" trava a reunião, e é para isso que serve.
	Peça exemplo, não definição.
- Uma API é um contrato: uma forma acordada de um programa pedir e outro
	responder.
- O verbo (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`) diz a intenção; o
	endereço diz o alvo. O verbo não entra no endereço.
- O código de três dígitos é a primeira coisa que o outro programa lê.
- Livro é o título, exemplar é o objeto, empréstimo é o acontecimento.
	Fundir os dois primeiros custa uma reescrita.
- Número contado não diverge da realidade; número guardado, sim.
:::

:::milestone
Ambiente instalado e conferido, domínio entendido. Daqui em diante, tudo que
aparecer no livro roda na sua máquina.
:::

:::exercise level=1
O PHP aceita código direto na linha de comando com a opção `-r`, sem
precisar criar arquivo. Por exemplo:

```text
$ php -r "echo 2 + 2;"
4
```

Use `-r` para imprimir a versão do PHP, que está guardada num valor pronto
chamado `PHP_VERSION`. Depois descubra onde fica o arquivo de configuração
do seu PHP, com `php -i | grep "Loaded Configuration"`. Anote os dois.

:::answer
```text
$ php -r "echo PHP_VERSION;"
8.3.14

$ php -i | grep "Loaded Configuration"
Loaded Configuration File => /etc/php/8.3/cli/php.ini
```

O `php -i` despeja a configuração inteira, que são umas quinhentas linhas; o
`grep` filtra a que interessa. No Windows, fora do WSL, troque por
`php -i | findstr "Loaded"`.

Guarde o caminho do `php.ini`. É o arquivo que decide, entre outras coisas,
se os erros aparecem na tela ou somem em silêncio.
:::

:::exercise level=2
Escreva o verbo e o endereço de cada operação do acervo: listar os livros,
buscar um livro específico, cadastrar, alterar e remover. Depois escreva as
três operações de empréstimo: emprestar, renovar e devolver.

:::answer
As cinco do acervo saem direto da tabela de verbos:

```text
GET    /livros          lista
GET    /livros/12       busca um
POST   /livros          cadastra
PUT    /livros/12       substitui
DELETE /livros/12       remove
```

As três de empréstimo são mais interessantes, porque renovar e devolver não
são "criar", "alterar" nem "remover" — são ações. A saída mais usada é
tratar a ação como uma coisa que se cria:

```text
POST   /emprestimos                empresta
POST   /emprestimos/7/renovacao    renova
POST   /emprestimos/7/devolucao    devolve
```

Se a sua resposta foi `POST /renovarEmprestimo/7`, ela funciona igual. A
diferença aparece na centésima operação, quando o sistema tem quarenta
endereços com verbo no nome e ninguém consegue adivinhar nenhum deles sem
consultar a documentação.
:::

:::exercise level=3
Vera quer um relatório de "livros mais emprestados" para decidir o que
comprar com a verba do semestre. Um livro tem vários exemplares. Se o
relatório contar empréstimos por exemplar, ele responde a mesma pergunta?

:::answer
Não responde, e a diferença é exatamente a deste capítulo.

Contar por **exemplar** responde "qual cópia saiu mais vezes". É uma
pergunta de conservação: o exemplar mais emprestado é o que vai rasgar
primeiro, e é o que precisa de encadernação.

Contar por **livro** — somando os empréstimos de todos os exemplares daquele
título — responde "o que as pessoas querem ler". É uma pergunta de
aquisição, e é a que a Vera fez.

As duas são legítimas e servem a decisões diferentes. O problema é entregar
uma achando que entregou a outra, o que acontece com frequência
desconfortável, porque o nome do relatório costuma ser o mesmo nos dois
casos.

Há ainda um terceiro número escondido aí, e é o melhor dos três: o título
mais **procurado** não é o mais emprestado. É o que mais aparece em reserva
porque nunca tem exemplar livre — e esse não está em nenhuma das duas
contagens. Comprar pelo ranking de empréstimos significa comprar mais cópias
do que já circula bem, e nenhuma do que ninguém consegue pegar.
:::

:::story Escala pra quantos usuários?
Na quinta, o Dr. Aurélio parou na mesa do Dedé.

— Soube que você foi na biblioteca.

— Fui ver o sistema antigo.

— E como é?

— É um PHP de 2009 num servidor que o sobrinho de uma moradora hospeda.

O Dr. Aurélio assentiu devagar, do jeito de quem está montando um slide
mentalmente.

— Escala pra quantos usuários?

— Mil e duzentos. Do bairro.

— Hmm. — Uma pausa. — Já pensou em microsserviços?

Dedé pensou em dizer que a biblioteca tem três conceitos e um computador.

— Vou avaliar.

No caderno da Tainá, naquele dia, entrou a primeira linha de uma lista que
ia crescer até março: *"perguntar o tamanho antes de escolher a ferramenta"*.
:::
