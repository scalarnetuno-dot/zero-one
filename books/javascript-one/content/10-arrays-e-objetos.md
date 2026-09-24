---
title: "Arrays e objetos"
number: 10
slug: arrays-e-objetos
part: p3
kicker: "O aplicativo do motorista manda status. O sistema antigo manda situacao. As duas estão certas, cada uma no sistema de onde veio."
goal: >-
  Modelar uma entrega como objeto e a manhã como array, ler e escrever
  propriedades sem ser enganado por um nome que não existe, percorrer e
  transformar a lista com os métodos de array, e levar dois formatos da
  mesma entrega para um só.
---

:::story Status e situação
Quarta, 25 de março. A Cláudia trouxe duas capturas para a mesa da Bia. A
primeira, a entrega E-5140 como o aplicativo novo do motorista a mandava
para o servidor:

```json
{ "id": "E-5140", "status": "entregue", "cidade": "Franca",
  "freteCentavos": 2160 }
```

A segunda, a mesma entrega como o sistema antigo de roteirização, que a
Borba usa desde 2019, a mandava:

```json
{ "codigo": "E-5140", "situacao": "ENTREGUE", "municipio": "FRANCA",
  "frete": "21,60" }
```

— O painel lê qual? — perguntou a Cláudia.

— Os dois — disse a Bia. — Em lugares diferentes.

O Rafael olhou por cima.

— E nenhum está errado. Cada um é o formato do sistema que o escreveu.

— Então qual é o certo?

— O que o painel decidir que é. Uma vez, na porta.
:::

## Objeto: a entrega

Um objeto guarda pares de nome e valor. O nome é a **propriedade**:

```javascript title="entrega.js" numbered
const entrega = {
  codigo: "E-5140",
  status: "entregue",
  cidade: "Franca",
  freteCentavos: 2160,
};

console.log(entrega.codigo);
console.log(entrega["cidade"]);
```

```text
$ node entrega.js
E-5140
Franca
```

`entrega.codigo` lê a propriedade `codigo`. A forma com colchetes,
`entrega["cidade"]`, faz o mesmo, e serve quando o nome está num texto
montado em tempo de execução. A vírgula depois da última propriedade é
permitida e poupa ruído quando alguém acrescenta uma linha.

Escrever é igual, com `=`:

```javascript
entrega.status = "cancelada";
entrega.motivo = "loja fechada";
```

Propriedade que não existia passa a existir. E o `const` não impede: ele
prende o **nome** `entrega` ao objeto; o objeto em si continua aceitando
mudança. O capítulo seguinte volta a isso, porque é a origem de um
defeito.

## O nome que não existe

Ler uma propriedade que não existe devolve `undefined`, sem erro — o
capítulo @cap:variaveis-e-tipos já mostrou. Com dois formatos na mesa, esse
é o defeito mais provável da semana:

```javascript
const antiga = { codigo: "E-5140", situacao: "ENTREGUE" };

console.log(antiga.status);           // undefined
console.log(antiga.status === "entregue");   // false
```

O painel lia `status` num formato que só tem `situacao`. A comparação dá
falso, a entrega aparece "a caminho", e nenhuma linha reclamou.

Ler dentro de algo que não existe, sim, quebra:

```javascript
console.log(antiga.endereco.cidade);
```

```text
TypeError: Cannot read properties of undefined (reading 'cidade')
```

`antiga.endereco` é `undefined`, e `undefined` não tem propriedades. Para
ler um caminho que pode estar incompleto, existe o `?.`:

```javascript
console.log(antiga.endereco?.cidade);   // undefined
```

`?.` para no primeiro `undefined` ou `null` e devolve `undefined`, em vez
de quebrar. Serve para dado opcional. Para dado obrigatório que sumiu, a
quebra é melhor que o silêncio.

## Array: a manhã

A lista de entregas é um array: valores em ordem, entre colchetes.

```javascript
const manha = ["E-5140", "E-5141", "E-5142"];

console.log(manha[0]);       // "E-5140"
console.log(manha.length);   // 3
console.log(manha[5]);       // undefined
manha.push("E-5143");
```

Posição a partir de zero; `length` é o tamanho; posição que não existe
devolve `undefined`; `push` acrescenta no fim. E, no painel, o array quase
sempre guarda objetos:

```javascript
const manha = [
  { codigo: "E-5140", status: "entregue", freteCentavos: 2160 },
  { codigo: "E-5141", status: "a caminho", freteCentavos: 1890 },
  { codigo: "E-5142", status: "cancelada", freteCentavos: 1290 },
];
```

## Os métodos que substituem o laço

O capítulo @cap:repeticoes percorria a lista com `for...of` e um
acumulador. Para as formas mais comuns — transformar, filtrar, achar,
somar —, o array tem métodos que recebem uma **função** e a aplicam a cada
item. A seta do capítulo @cap:funcoes aparece aqui, como prometido:

```javascript title="manha.js" numbered
const codigos = manha.map((e) => e.codigo);
const ativas = manha.filter((e) => e.status !== "cancelada");
const e5141 = manha.find((e) => e.codigo === "E-5141");
const total = manha.reduce((soma, e) => soma + e.freteCentavos, 0);

console.log(codigos);
console.log(ativas.length);
console.log(e5141.status);
console.log(total);
```

```text
$ node manha.js
[ 'E-5140', 'E-5141', 'E-5142' ]
2
a caminho
5340
```

**`map`** devolve uma lista nova, com o resultado da função para cada item.

**`filter`** devolve uma lista nova, com os itens para os quais a função
devolveu verdadeiro.

**`find`** devolve o primeiro item para o qual a função devolveu
verdadeiro — ou `undefined`.

**`reduce`** percorre a lista carregando um acumulador: a função recebe o
acumulador e o item, e devolve o acumulador seguinte. O `0` do fim é o
valor inicial. É o acumulador do laço, escrito numa linha.

Nenhum dos quatro altera `manha`. Todos devolvem algo novo.

:::pitfall
`filter` pelo que é permitido e `filter` pelo que é proibido divergem no
valor que ninguém previu. `status !== "cancelada"` mantém uma entrega com
`status` indefinido; `status === "a caminho" || status === "entregue"` a
descarta. É a entrega sem cidade do capítulo @cap:repeticoes, com outro
nome. Antes de escolher o filtro, conte os itens que não caem em nenhum
dos valores conhecidos.
:::

## Dois formatos, uma entrega

O painel decide o formato dele — os nomes do aplicativo novo, os valores
em minúsculas, o frete em centavos — e converte o antigo **na porta**, num
lugar só:

```javascript title="normalizar.js" numbered
const SITUACOES = {
  ENTREGUE: "entregue",
  "EM ROTA": "a caminho",
  CANCELADA: "cancelada",
};

function doSistemaAntigo(a) {
  const status = SITUACOES[a.situacao];
  if (status === undefined) {
    throw new Error(`${a.codigo}: situação ${a.situacao}`);
  }
  return {
    codigo: a.codigo,
    status: status,
    cidade: a.municipio.charAt(0)
      + a.municipio.slice(1).toLowerCase(),
    freteCentavos: Math.round(
      Number(a.frete.replace(",", ".")) * 100,
    ),
  };
}

function doAplicativo(n) {
  return {
    codigo: n.id,
    status: n.status,
    cidade: n.cidade,
    freteCentavos: n.freteCentavos,
  };
}

const antiga = {
  codigo: "E-5140", situacao: "ENTREGUE",
  municipio: "FRANCA", frete: "21,60",
};
const nova = {
  id: "E-5140", status: "entregue",
  cidade: "Franca", freteCentavos: 2160,
};

console.log(doSistemaAntigo(antiga));
console.log(doAplicativo(nova));
```

```text
$ node normalizar.js
{
  codigo: 'E-5140',
  status: 'entregue',
  cidade: 'Franca',
  freteCentavos: 2160
}
{
  codigo: 'E-5140',
  status: 'entregue',
  cidade: 'Franca',
  freteCentavos: 2160
}
```

O Node quebra o objeto em várias linhas quando ele não cabe numa só.

`SITUACOES` é um objeto usado como tabela de tradução: a chave é o valor
antigo, o valor é o novo. `"EM ROTA"` tem espaço, e por isso a chave
precisa de aspas. Uma situação que não estiver na tabela para o programa
com a mensagem de qual era — o desconhecido não vira `undefined` calado.

`charAt(0)` pega a primeira letra; `slice(1)` pega o resto; `toLowerCase`
põe em minúsculas. `FRANCA` vira `Franca`. Para "SÃO CARLOS", a regra
produziria "São carlos" — e o exercício 2 trata disso.

As duas saídas são iguais. A partir daqui, o resto do painel lê **um**
formato. O `doSistemaAntigo` é o único lugar do código que sabe que
`situacao` existe.

:::key
Dado de dois sistemas se converte **na porta**, uma vez, para o formato do
painel. Uma leitura de `e.status || e.situacao` espalhada pelo código é a
conversão feita em doze lugares, cada um com a sua pequena diferença.
:::

:::summary
- Objeto guarda propriedades; `e.nome` e `e["nome"]` leem. `const` prende
  o nome, não o conteúdo.
- Propriedade inexistente é `undefined`; ler dentro dela é `TypeError`. `?.`
  para dado opcional.
- Array é lista em ordem, a partir de zero. `push` acrescenta.
- `map`, `filter`, `find` e `reduce` recebem uma função e devolvem algo
  novo, sem alterar a lista.
- Dois formatos da mesma entrega se convertem na porta, num lugar só, para
  o formato do painel. O desconhecido para o programa.
:::

:::exercise level=1
Com a lista `manha` do capítulo, escreva uma linha para cada pedido:

1. Os códigos das entregas entregues.
2. O frete total das que não foram canceladas.
3. Se existe alguma entrega de Franca.

:::answer
```javascript
manha.filter((e) => e.status === "entregue").map((e) => e.codigo);

manha
  .filter((e) => e.status !== "cancelada")
  .reduce((soma, e) => soma + e.freteCentavos, 0);

manha.some((e) => e.cidade === "Franca");
```

A primeira encadeia: `filter` devolve uma lista, e `map` é chamado nela.
A terceira usa `some`, que devolve `true` se a função for verdadeira para
algum item — a pergunta "existe?" sem precisar do item.
:::

:::exercise level=2
Escreva `nomeDeCidade(texto)`, que transforma `"SÃO CARLOS"` em
`"São Carlos"` e `"RIBEIRÃO PRETO"` em `"Ribeirão Preto"`.

:::answer
```javascript
function nomeDeCidade(texto) {
  return texto
    .toLowerCase()
    .split(" ")
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(" ");
}

console.log(nomeDeCidade("SÃO CARLOS"));
console.log(nomeDeCidade("RIBEIRÃO PRETO"));
```

`split(" ")` quebra o texto numa lista de palavras. O `map` põe a primeira
letra de cada uma em maiúscula. `join(" ")` junta de volta.

A regra erra "SERRA DO CIPÓ" — "Serra Do Cipó". Para as três cidades da
Borba, basta. Para uma lista aberta de municípios, a tradução vira uma
tabela, como a de `SITUACOES`.
:::

:::exercise level=3
O sistema antigo começou a mandar, em algumas entregas, `situacao:
"DEVOLVIDA"` — mercadoria que voltou ao cais. O `doSistemaAntigo` para o
programa. A Cláudia pede que "só ignore essas por enquanto". Responda, e
diga o que você faria.

:::answer
Ignorar é o `continue` sem destino do capítulo @cap:repeticoes: a entrega
some da lista, e a Lívia, que sabe que a mercadoria voltou, não a
encontra no painel.

O que eu faria: perguntar à Lívia o que "devolvida" é para ela — um
status próprio, que aparece no painel, ou uma forma de cancelada. Se for
um status próprio, `SITUACOES` ganha `DEVOLVIDA: "devolvida"`, e a função
`situacao` e as cores do capítulo @cap:condicionais ganham o caso. Se for
cancelada, `DEVOLVIDA: "cancelada"`, com um comentário dizendo por quê.

Até a resposta, o `throw` fica. Ele é o que fez a pergunta chegar à mesa
em vez de a entrega sumir.
:::
