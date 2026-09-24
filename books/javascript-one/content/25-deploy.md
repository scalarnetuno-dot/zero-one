---
title: "Deploy"
number: 25
slug: deploy
part: p8
kicker: "Sexta, 16h52. Na máquina da Bia, Node 24, tudo verde. No servidor, Node 20, o rodapé nem carregava. O Neto apareceu na porta antes de alguém chamar."
goal: >-
  Dizer o que tem de ser igual entre a máquina local e o servidor — versão
  do Node, variáveis de ambiente, o comando que sobe o processo —, achar a
  diferença concreta que quebra o Node 20, e recusar um horário.
---

:::story Quem falou produção?
Sexta, 24 de abril, 16h52. A Bia tinha terminado o rodapé por cidade, que
a Lívia pediu na quarta: quantas entregas e quanto de frete, Franca,
Ribeirão, São Carlos. Os testes estavam verdes. A Cláudia tinha visto na
tela da Bia e dito "perfeito, sobe".

A Bia abriu o terminal do servidor de homologação e rodou o comando que o
Marcos tinha deixado num arquivo de texto. O painel subiu. O rodapé ficou
em branco. No log:

```text
TypeError: Object.groupBy is not a function
```

O Neto apareceu na porta. Ninguém tinha chamado.

— Quem falou produção?

— É homologação — disse a Bia. — Produção é depois.

— Depois quando?

A Cláudia, da mesa dela:

— Hoje. A Lívia quer o rodapé segunda às 5h40.

O Neto olhou para o relógio da parede.

— Sexta, 16h52. O servidor está no Node 20. O seu notebook, no 24. Você
descobriu isso agora, em homologação, com o rodapé em branco. Se tivesse
descoberto em produção, quem estaria aqui às 5h40 de segunda?

Ninguém respondeu.

O Rafael fechou o notebook.

— Segunda.
:::

## O que funciona na minha máquina

O capítulo @cap:primeiro-programa mostrou o Neto na porta pela primeira
vez, com a mesma pergunta: qual máquina? O `node` da Bia responde 24. O do
servidor responde 20. Os dois se chamam Node, e não são o mesmo programa.

O rodapé usava isto:

```javascript title="rodape.js" numbered
const entregas = [
  { codigo: "E-6001", cidade: "Franca", frete: 1890 },
  { codigo: "E-6002", cidade: "Franca", frete: 2160 },
  { codigo: "E-6003", cidade: "São Carlos", frete: 2290 },
];

const porCidade = Object.groupBy(entregas, (e) => e.cidade);

for (const [cidade, lista] of Object.entries(porCidade)) {
  const total = lista.reduce((s, e) => s + e.frete, 0);
  console.log(`${cidade}: ${lista.length} entrega(s), ${total}`);
}
```

```text
$ node --version
v24.9.0
$ node rodape.js
Franca: 2 entrega(s), 4050
São Carlos: 1 entrega(s), 2290
```

`Object.groupBy` agrupa uma lista num objeto, pela chave que a função
devolve — o agrupamento que o capítulo @cap:arrays-e-objetos teria feito
com `reduce`. Ele entrou na linguagem em 2024, e no Node a partir da linha
21.

No servidor:

```text
$ node --version
v20.20.2
$ node rodape.js
file:///srv/borba/rodape.js:7
const porCidade = Object.groupBy(entregas, (e) => e.cidade);
                         ^

TypeError: Object.groupBy is not a function
```

A linguagem é a mesma. O motor é outro, mais velho, e não tem o método. É a
diferença concreta: não uma opinião sobre versão, mas uma linha que roda
num e quebra no outro.

:::key
"Funciona na minha máquina" quer dizer: funciona com a versão do Node, as
dependências, as variáveis e o comando **da minha máquina**. O deploy é
tornar essas quatro coisas iguais no servidor — e descobrir, antes de
publicar, qual delas não é.
:::

## O que tem de ser igual

**A versão do Node.** O `package.json` pode dizer qual o projeto exige:

```json title="package.json"
{
  "name": "borba",
  "type": "module",
  "engines": {
    "node": ">=22"
  },
  "scripts": {
    "start": "node servidor.js",
    "test": "node --test"
  }
}
```

`engines` declara a linha. O npm avisa quando alguém instala num Node que
não atende. E um arquivo `.nvmrc` com `24` deixa as ferramentas que
instalam várias linhas do Node lado a lado — o `nvm` é a mais conhecida —
trocarem sozinhas ao entrar na pasta.

**As dependências.** `npm ci`, do capítulo @cap:npm: exatamente o
lockfile, sem resolver nada de novo no servidor.

**As variáveis de ambiente.** O painel novo lê o endereço do servidor de
entregas de fora do código:

```javascript
const API = process.env.BORBA_API;
if (!API) {
  throw new Error("BORBA_API não definida");
}
```

`process.env` é o objeto com as variáveis de ambiente do processo — valores
que o sistema operacional entrega ao programa na hora de rodar. Na máquina
da Bia, elas vêm do `.env`, que o capítulo @cap:git deixou fora do
repositório. No servidor, alguém precisa defini-las. O `throw` na partida é
de propósito: um painel que sobe sem saber onde está o servidor e falha no
primeiro pedido às 5h40 é pior que um que não sobe às 14h.

**O comando.** `npm start`, e não o comando que o Marcos deixou num
arquivo de texto. O `scripts.start` está no `package.json`, versionado, e
é o mesmo em toda máquina.

## O horário

Nenhuma das quatro coisas acima estava errada às 16h52 de propósito. O
defeito era uma linha, e o conserto — trocar `Object.groupBy` por um
`reduce`, ou atualizar o servidor — levava minutos. O Rafael fechou o
notebook assim mesmo.

Um deploy às 16h52 de uma sexta tem três propriedades:

- quem publicou vai embora em uma hora, e o fim de semana começa;
- quem descobre o defeito é a Lívia, às 5h40 de segunda, sozinha, com o
  caminhão esperando;
- a volta — desfazer o que subiu — depende de alguém que está em casa.

O defeito de hoje apareceu em homologação, e ainda assim tomou quarenta
minutos. O próximo pode não aparecer lá.

:::pitfall
"É só uma linha" é a frase que acompanha a maior parte dos deploys de
sexta. O tamanho da mudança não diz o tamanho do risco: uma linha com
`Object.groupBy` derruba o rodapé inteiro num servidor mais velho. O que
diz o risco é o que tem de ser igual entre as máquinas — e quanto tempo
sobra para descobrir o que não é.
:::

## Segunda de manhã

O que a segunda precisava cumprir, escrito pelo Neto e pela Bia antes de
irem embora, numa lista de cinco linhas coladas no ticket:

```text
1. Servidor no Node 24 (o 20 perde suporte em 30/04). node --version
2. npm ci no servidor, a partir do lockfile do commit a publicar
3. BORBA_API e BORBA_CHAVE definidas; o painel recusa subir sem elas
4. npm test verde no próprio servidor, antes do npm start
5. Publicar às 14h, com a Lívia avisada e a Bia até as 18h
```

A primeira linha resolveu o `Object.groupBy` sem mudar o código, e
resolveu outra coisa: o Node 20 deixa de receber correção em 30 de abril,
seis dias antes da renovação. O servidor ia ter de subir de qualquer
jeito, e a sexta às 16h52 deu o motivo e a data.

A quarta linha é a que o Neto mais defendeu: os testes rodando **no
servidor**. Os testes verdes na máquina da Bia provavam que o código
funcionava no Node 24 dela. Rodando no servidor, provam que funciona onde
vai ficar.

Na segunda, às 14h10, o rodapé apareceu no painel de produção. A Lívia
mandou uma foto às 14h15, com a soma de Franca conferida à mão na
prancheta.

:::summary
- "Funciona na minha máquina" depende da versão do Node, das
  dependências, das variáveis e do comando. O deploy iguala os quatro.
- `Object.groupBy` existe a partir do Node 21: roda no 24 da Bia e dá
  `TypeError` no 20 do servidor.
- `engines` e `.nvmrc` declaram a versão; `npm ci` iguala as dependências;
  `process.env` lê as variáveis; `npm start` é o comando.
- Variável obrigatória ausente derruba a partida, e não o primeiro pedido.
- O horário é parte do deploy: sexta às 16h52 põe a descoberta do defeito
  nas mãos de quem não pode desfazê-lo.
:::

:::exercise level=1
Para cada item, diga se ele faz o rodapé funcionar no servidor com Node
20:

1. Trocar `Object.groupBy` por um `reduce` que agrupe por cidade.
2. Pôr `"engines": { "node": ">=22" }` no `package.json`.
3. Atualizar o servidor para o Node 24.

:::answer
1. Sim. `reduce` existe no Node 20, e o agrupamento funciona igual.
2. Não. `engines` avisa na instalação; não acrescenta o método ao Node 20.
   Serve para o problema ser descoberto no `npm ci`, e não no rodapé.
3. Sim, e é o que a segunda fez: resolve o rodapé e o fim do suporte do 20
   de uma vez.

O 1 e o 3 funcionam. O 2 transforma o próximo defeito do mesmo tipo num
aviso antecipado. As três juntas são o que a casa faz.
:::

:::exercise level=2
Escreva o `reduce` que substitui `Object.groupBy` no rodapé, para quem
precisar rodar no Node 20.

:::answer
```javascript
const porCidade = entregas.reduce((grupos, e) => {
  (grupos[e.cidade] ??= []).push(e);
  return grupos;
}, {});
```

O acumulador começa num objeto vazio. Para cada entrega, `??=` cria a
lista da cidade se ela ainda não existe — o `??` do capítulo
@cap:operadores, com atribuição —, e o `push` acrescenta a entrega. O
resto do rodapé não muda.
:::

:::exercise level=3
Na segunda, às 13h50, dez minutos antes da janela, a Cláudia pede para
incluir no deploy "uma coisinha": o rodapé mostrar também o total do dia
de todas as cidades. A mudança está pronta na máquina da Bia, com teste.
Responda.

:::answer
Não entra neste deploy. O que foi preparado, testado no servidor e
combinado com a Lívia é o rodapé por cidade, com o servidor no Node 24.
Uma mudança acrescentada dez minutos antes não passou pela quarta linha
da lista — o teste no servidor —, e mistura, no mesmo deploy, a troca de
versão do Node com uma mudança de tela. Se algo der errado às 14h10,
ninguém sabe qual das duas foi.

Ela sobe no deploy seguinte, sozinha, com a mesma lista. Se a Cláudia
precisar para terça às 5h40, a janela da tarde de segunda ainda cabe — às
16h, com a Bia até as 18h. Não às 16h52 de uma sexta.
:::
