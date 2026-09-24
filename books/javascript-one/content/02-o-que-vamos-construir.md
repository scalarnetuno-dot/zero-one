---
title: "O que vamos construir"
number: 2
slug: o-que-vamos-construir
part: p1
kicker: "Segunda-feira, 8h17. Três jeitos de pedir a mesma entrega, e um histórico que sabe o nome de quem tentou."
goal: >-
  Ler o package.json e um git log o bastante para saber o que há na pasta,
  descrever o que o dia 6 de maio cobra do painel, e terminar com o Node 24
  instalado e conferido.
---

:::story Não mexe nisso
Bia chegou mais cedo.

O repositório já estava aberto. Ela tinha recebido acesso na sexta e
passado o fim de semana tentando entender o projeto.

Abriu o `package.json`.

Leu as dependências.

Rolou.

Continuou rolando.

Parou.

— Rafael?

— Hm?

— Por que temos três bibliotecas para fazer requisição HTTP?

Rafael continuou olhando para o monitor.

— Temos?

— Axios, uma chamada direta de `fetch` e uma pasta chamada `http`.

— Ah.

— "Ah" o quê?

— Não mexe nisso.

— Por quê?

— Porque ninguém sabe.

Bia ficou olhando para ele.

— Mas alguém colocou.

— Sim.

— Quem?

Rafael apontou para o histórico do Git.

— Descubra.
:::

O repositório é a pasta do painel com a história de cada mudança guardada
pelo Git. O histórico é a lista dessas mudanças. A Bia acabou de descobrir
que a pasta pede a mesma coisa de três jeitos, e que a sala não tem uma
frase pronta para dizer qual dos três vale.

Dá para descobrir quem colocou. Não dá, só com essa conversa, para
descobrir qual chamada é segura. As duas perguntas não são a mesma.

## O que o `package.json` está contando

O arquivo é JSON: chaves, e nomes entre aspas duplas. O nome do projeto e
a lista do que ele precisa para funcionar.

```json title="package.json"
{
  "name": "painel",
  "dependencies": {
    "axios": "0.21.1"
  }
}
```

`name` é o nome da pasta como projeto. `dependencies` é o mapa das
bibliotecas que alguém instalou e quis registrar. Cada nome aponta para um
número de versão. `"axios": "0.21.1"` quer dizer: esta pasta foi montada
com o Axios na versão 0.21.1.

O Axios não vem com a linguagem. É uma biblioteca de pedido HTTP publicada
no registro npm. A versão anotada é a de um tutorial que já era antigo
quando o arquivo foi criado, e o arquivo não se atualizou sozinho.

`fetch` não aparece nesse mapa. Não é biblioteca: é uma função que o
navegador e o Node, a partir da linha 18, já trazem. O `lista.js` chama
essa função. A pasta `http/` também não é dependência de ninguém. É código
da própria Borba, um cliente escrito à mão.

:::term HTTP
O protocolo com que um programa pede um dado a outro computador. Uma
requisição sai, uma resposta volta.

Axios, `fetch` e a pasta `http/` fazem essa requisição. Três textos, um
protocolo.
:::

:::term npm
O registro público de bibliotecas JavaScript, e também o comando que
instala uma delas a partir do que o `package.json` anotou. Vem junto com
o Node.

Não há nada para instalar agora. A lista acima é a da produção, e a
instrução da manhã foi não mexer nela.
:::

Três clientes não são três opiniões iguais. São três épocas encostadas:

| Onde está | O que é | Quando entrou |
|---|---|---|
| `http/client.js` | código da casa, escrito à mão | março de 2022 |
| Axios em `entrega.js` | biblioteca, versão 0.21.1 | março de 2024 |
| `fetch` em `lista.js` e em `entrega.js` | função da própria linguagem | agosto de 2025 |

Tabela: A pasta guarda as três. A manhã da Lívia usa o que estiver sendo
chamado no caminho que a tela percorre hoje — e isso não está escrito no
`package.json`.

## O histórico que ele apontou

Git guarda cada mudança registrada do repositório. Cada registro é um
**commit**: um conjunto de alterações com autor, data e uma mensagem que o
autor escreveu na hora. `git log` imprime esses registros, do mais novo
para o mais antigo.

O comando que lista esse histórico, só no arquivo da função e só nos três
registros mais recentes que o tocaram, produz isto:

```text
$ git log -3 -- entrega.js
commit 91ab220
Author: Marcos Teixeira
Date:   Tue Aug 12 18:03:44 2025 -0300

    troca axios por fetch

commit 4b21877
Author: Diego Pacheco
Date:   Mon Mar 18 19:41:12 2024 -0300

    ajustes

commit c77e014
Author: Diego Pacheco
Date:   Mon Mar 14 22:16:05 2022 -0300

    cliente http
```

`-3` pede só três registros. `-- entrega.js` pede só os que mexeram nesse
arquivo. O `--` separa as opções do nome do arquivo, para o Git não tentar
ler `entrega.js` como se fosse mais uma opção.

Cada bloco tem quatro partes. `commit` e o código curto identificam o
registro: aquele código é um apelido de um número grande que o Git
calculou a partir do conteúdo. `Author` é quem registrou. `Date` é quando.
O texto recuado embaixo é a mensagem.

A mensagem do Marcos diz que ele trocou Axios por `fetch`. O commit mexeu
em `entrega.js` e em `lista.js`: o `fetch` ficou nos dois. A pasta ainda
tem Axios, e ainda tem `http/`. A mensagem descreve a intenção. A pasta
descreve o que sobrou. Ninguém voltou num registro posterior para escrever
que a troca tinha ficado pela metade.

O commit de março de 2024, mensagem `ajustes`, é o que deixou no fim de
`entrega.js` o comentário que pede para não mexer. A mensagem não diz
isso. O arquivo diz.

:::term Git
Programa que guarda o histórico de uma pasta: o que mudou, quem mudou,
quando, e a mensagem escrita na hora. O `git log` lê esse histórico. Não
altera o arquivo.

Quem colocou está no `Author`. O que a pessoa achou que estava fazendo
está na mensagem. O que ela fez está no arquivo.
:::

## O que o dia 6 de maio está cobrando

Não é uma plataforma. Não são três caixas no quadro. São duas frases que a
Lívia consegue conferir sem ajuda.

A primeira: cada status que o motorista marca aparece no painel em até
trinta segundos. A segunda: a lista que está na tela às 5h35 é a mesma
lista que sai na impressora. Se as duas forem verdade na quarta-feira, 6
de maio, a cláusula está de pé. O resto é caminho.

:::story Uns dois mil e quatrocentos
A Cláudia chegou às 11h40 com a folha da Lívia.

— Ela contou. Uns dois mil e quatrocentos por dia, fora da janela.

O Marcos já estava no quadro. Três caixas: frete, status, notificação.

— A gente separa. Cada caixa vira um serviço.

O Rafael olhou para a folha.

— Hoje é um arquivo. A cláusula é quarta, 6 de maio.

— E se a gente não separar?

— Aí a tela diz a verdade de manhã. É isso que os R$ 3,50 estão cobrando.
:::

Serviço, na frase do Marcos, seria outro programa, rodando à parte, só
para aquela caixa. Dá para chegar lá. Não é o que a folha pede para esta
quarta-feira. A folha pede que o número que a Lívia contou caia, e que o
papel pare de ganhar do painel às 5h40.

O programa que você vai escrever cabe numa pasta sua, chamada `borba`. O
painel de produção continua no servidor, intocado. O que cresce na sua
máquina é a versão que dá para rodar, quebrar e mostrar para alguém sem
pedir licença ao caminhão.

## Instalando

Baixe o Node em <https://nodejs.org>. Escolha a linha **LTS**. Nesta
edição, essa linha é a 24, com correção publicada até 30 de abril de 2028.
A 22 também roda o que está neste livro, e recebe correção até 30 de abril
de 2027. A linha Current — em 2026, a 26 — muda toda semana. Não é a linha
da sua pasta.

No Windows, o instalador pergunta se inclui o Node no PATH. Deixe marcado.
PATH é a lista de pastas em que o terminal procura um comando. Sem essa
marca, `node` não é encontrado, mesmo com o programa instalado.

Feche o terminal se ele já estava aberto, abra de novo, e confira:

```text
$ node --version
v24.9.0
```

O trecho depois do segundo ponto muda conforme o mês da instalação.
Qualquer resposta que comece com `v24` está na linha. Se o comando não
existir, o terminal não viu a instalação: feche, abra, tente outra vez
antes de instalar por cima.

:::warning O terminal que já estava aberto
Um terminal guarda o PATH do momento em que foi aberto. Instalar o Node
não atualiza essa cópia. O sintoma é `node` não reconhecido numa janela, e
reconhecido na janela ao lado.
:::

:::pitfall
`node` pode existir duas vezes na mesma máquina, com versões diferentes.
O servidor da Borba responde 20. A sua máquina, se você seguiu a LTS,
responde 24. Os dois se chamam Node.

No Windows, `where.exe node` lista os caminhos. No macOS e no Linux,
`which node` mostra qual arquivo o terminal vai chamar. Descubra o seu
agora e use esse. "Eu instalei" com o terminal chamando outro arquivo é a
manhã inteira perdida num erro que não está no seu código.
:::

:::practice
Rode `node --version`. Se a resposta começar com `v24`, crie a pasta do
trabalho e entre nela:

```text
$ mkdir borba
$ cd borba
```

Não rode `npm install`. Não copie o `package.json` da Borba. A pasta
`borba` começa vazia de propósito: ainda não existe um programa.
:::

:::summary
- A pasta de produção tem três clientes HTTP: Axios 0.21.1, `fetch` e
  `http/client.js`.
- `git log` mostra autor, data e mensagem. A mensagem do Marcos não é a
  pasta que sobrou.
- O dia 6 de maio cobra trinta segundos e uma lista igual à do papel.
- O Node da sua máquina é o 24, conferido com `node --version`. O do
  servidor é o 20, até 30 de abril.
:::

:::milestone
Você tem o Node 24 instalado, a pasta `borba` criada, e as duas frases que
a Lívia vai conferir em 6 de maio. Ainda não há programa. É daqui que o
arquivo começa.
:::

:::exercise level=1
A Lívia liga às 5h50: "sumiu a entrega do mercado da Vila. No papel está."
Escreva, em duas linhas, o que ela precisa que o painel responda, e o que
ela não precisa saber para receber essa resposta.

:::answer
Ela precisa saber se a entrega está na lista da manhã e em que status.
A resposta é uma linha, ou "não está".

Ela não precisa saber se quem buscou o dado foi o Axios, o `fetch` ou a
pasta `http/`, nem em qual arquivo a função mora. Isso é o caminho. A
conferência dela é o papel na mão.
:::

:::exercise level=2
Sem olhar de novo o bloco do `git log`, diga quem registrou mudança em
`entrega.js` em agosto de 2025 e o que a mensagem afirma. Em seguida diga
uma coisa que a mensagem não prova.

:::answer
Marcos Teixeira, em 12 de agosto de 2025. A mensagem afirma: "troca axios
por fetch".

Não prova que o Axios tenha saído da pasta, nem que o `fetch` esteja
dentro de `entrega.js`. Prova o que ele escreveu na hora de registrar. O
que sobrou se vê no arquivo.
:::

:::exercise level=3
O Marcos quer, esta semana, três programas separados: um só para o frete,
um só para o status, um só para a notificação. A folha da Lívia está em
cima da mesa. Você aceitaria? Justifique em três linhas.

:::answer
Não esta semana. Separar em três programas é uma mudança de estrutura. A
folha pede que o status caiba em trinta segundos e que a lista da tela
coincida com a impressa.

Dá para fazer as duas coisas dentro do arquivo que já existe, medindo a
diferença. Três programas novos, com a cláusula em 6 de maio, trocam um
problema que a Lívia sabe contar por três problemas que ninguém rodou
ainda.
:::
