---
title: "Repetições"
number: 7
slug: repeticoes
part: p2
kicker: "O papel tinha quatro entregas para Franca. O painel mostrava três. O laço pulava a que tinha a cidade em branco."
goal: >-
  Percorrer a lista com for...of, saber o que o for clássico acrescenta,
  somar e contar com um acumulador, e ver um continue pular a entrega que
  não devia ser pulada.
---

:::story Três de quatro
Sexta, 20 de março, 5h41. A Lívia ligou para o celular da Cláudia, que
atendeu no carro.

— Franca. No papel tem quatro. Na tela, três. O caminhão sai em quatro
minutos.

— Qual falta?

— A da padaria do Jardim Paulista. E-5033.

O caminhão saiu pelo papel. Às 9h, a Bia estava com o trecho que monta a
lista por cidade:

```javascript
for (var i = 0; i < entregas.length; i++) {
  var e = entregas[i];
  if (!e.cidade) continue;
  if (e.cidade !== cidade) continue;
  linhas.push(e);
}
```

A E-5033 estava no banco com `cidade: ""`. O endereço dizia "Franca".

— Quem pôs esse primeiro `continue`? — perguntou ela.

O Rafael olhou o `git blame`.

— Diego. 2022. Mensagem: "evita erro de cidade nula".

— E evitou.

— Evitou o erro. A entrega foi junto.
:::

## `for...of`

A manhã é uma lista, e percorrer a lista é o que o painel mais faz. A forma
padrão:

```javascript title="lista.js" numbered
const entregas = [
  { codigo: "E-5030", cidade: "Franca" },
  { codigo: "E-5031", cidade: "Franca" },
  { codigo: "E-5032", cidade: "Franca" },
  { codigo: "E-5033", cidade: "" },
];

for (const e of entregas) {
  console.log(`${e.codigo} | ${e.cidade}`);
}
```

```text
$ node lista.js
E-5030 | Franca
E-5031 | Franca
E-5032 | Franca
E-5033 | 
```

`for (const e of entregas)` dá a `e` cada item da lista, um por volta, do
primeiro ao último. O `const` vale: a cada volta nasce um `e` novo, e
ninguém o reatribui dentro do bloco.

A lista entre colchetes é um array — o capítulo @cap:arrays-e-objetos
volta a ela com calma. Por enquanto: uma sequência em ordem, com
`entregas.length` itens.

## O `for` clássico

O laço do painel antigo é a forma anterior:

```javascript
for (let i = 0; i < entregas.length; i++) {
  console.log(i, entregas[i].codigo);
}
```

Três partes entre parênteses, separadas por ponto e vírgula: começa em
`i = 0`; continua enquanto `i < entregas.length`; ao fim de cada volta,
`i++`. `entregas[i]` lê o item da posição `i`, contando do zero.

Ele acrescenta uma coisa ao `for...of`: **o número da volta**. Quando o
número importa — numerar a lista impressa, alternar a cor das linhas —,
ele é a ferramenta. Quando não importa, é três lugares a mais para errar:
um `<=` no lugar de `<` lê uma posição que não existe e devolve
`undefined`.

:::pitfall
Existe também `for...in`, com uma letra de diferença. Ele percorre os
**nomes** das propriedades, não os valores. Numa lista, devolve as
posições como texto — `"0"`, `"1"`, `"2"` — e, em código antigo, às vezes
propriedades que alguém acrescentou ao array. Para lista, `for...of`.
:::

## `while`

O `while` repete enquanto uma condição for verdadeira, sem lista nenhuma:

```javascript title="tentativas.js" numbered
let tentativa = 1;

while (tentativa <= 3) {
  console.log(`tentativa ${tentativa} de entrega`);
  tentativa++;
}
```

```text
tentativa 1 de entrega
tentativa 2 de entrega
tentativa 3 de entrega
```

A condição é conferida **antes** de cada volta. Se ninguém mudar
`tentativa` dentro do bloco, a condição nunca fica falsa e o laço não
termina: o terminal trava, e `Ctrl+C` o interrompe. No painel, um
`while` sem fim trava a aba inteira da Lívia.

## O acumulador

Somar, contar e filtrar têm o mesmo esqueleto: um valor que começa antes
do laço e muda dentro dele.

```javascript title="totais.js" numbered
const entregas = [
  { codigo: "E-5030", cidade: "Franca", frete: 1890 },
  { codigo: "E-5031", cidade: "Franca", frete: 2300 },
  { codigo: "E-5032", cidade: "São Carlos", frete: 1550 },
];

let total = 0;
let deFranca = 0;
const codigos = [];

for (const e of entregas) {
  total += e.frete;
  if (e.cidade === "Franca") {
    deFranca++;
  }
  codigos.push(e.codigo);
}

console.log(total, deFranca, codigos);
```

```text
5740 2 [ 'E-5030', 'E-5031', 'E-5032' ]
```

`total` começa em `0` e soma. `deFranca` conta. `codigos` começa vazio e
recebe cada código com `push`, que acrescenta no fim da lista. O
`console.log` de um array mostra os itens entre colchetes, com aspas
simples — é o jeito do Node de mostrar texto dentro de lista.

## `continue` e `break`

`continue` pula para a próxima volta. `break` sai do laço inteiro.

```javascript
for (const e of entregas) {
  if (e.cancelada) {
    continue;
  }
  if (e.codigo === procurado) {
    encontrada = e;
    break;
  }
}
```

A entrega cancelada não é examinada. Achada a procurada, o laço para: não
há por que ler as cento e cinquenta restantes.

Os dois são curtos e úteis, e é justamente por isso que o `continue` de
2022 passou despercebido quatro anos. Um `continue` é uma decisão sobre
**quais itens não entram**. Quem o escreve está pensando no item que
quebrava. Quem lê a lista está pensando nos que deviam estar lá.

## A E-5033, antes e depois

O laço de 2022, reproduzido na pasta `borba`:

```javascript title="franca.js" numbered
const entregas = [
  { codigo: "E-5030", cidade: "Franca" },
  { codigo: "E-5031", cidade: "Franca" },
  { codigo: "E-5032", cidade: "Franca" },
  { codigo: "E-5033", cidade: "", endereco: "R. Voluntários" },
];

const linhas = [];
for (const e of entregas) {
  if (!e.cidade) continue;
  if (e.cidade !== "Franca") continue;
  linhas.push(e.codigo);
}
console.log(linhas.length, linhas);
```

```text
$ node franca.js
3 [ 'E-5030', 'E-5031', 'E-5032' ]
```

O primeiro `continue` pula o texto vazio — que é falso, a lista de seis do
capítulo @cap:operadores. A intenção era evitar um erro com `null`. O
efeito foi tirar da lista toda entrega sem cidade preenchida, sem aviso.

A correção não é apagar o `continue`. Sem ele, a E-5033 não é de Franca
(`"" !== "Franca"`) e sai do mesmo jeito. É decidir o que fazer com a
entrega sem cidade — e a decisão da Lívia foi: ela aparece, numa seção à
parte, para alguém conferir.

```javascript title="franca.js" numbered
const deFranca = [];
const semCidade = [];

for (const e of entregas) {
  if (!e.cidade) {
    semCidade.push(e.codigo);
    continue;
  }
  if (e.cidade === "Franca") {
    deFranca.push(e.codigo);
  }
}

console.log("Franca:", deFranca);
console.log("Sem cidade:", semCidade);
```

```text
$ node franca.js
Franca: [ 'E-5030', 'E-5031', 'E-5032' ]
Sem cidade: [ 'E-5033' ]
```

Quatro entregas entraram, quatro saíram. Três de Franca e uma que precisa
de alguém. A lista impressa às 5h35 passou a ter um quadro no fim: "sem
cidade no sistema — conferir endereço".

:::key
Todo `continue` num laço de lista é uma pergunta: para onde vai o item que
foi pulado? Se a resposta é "para lugar nenhum", confira que nenhum item
de verdade cai ali. Conte: os que entraram mais os que foram separados
precisam dar o total.
:::

:::summary
- `for...of` percorre a lista, do primeiro ao último. É o laço padrão.
- O `for` clássico acrescenta o número da volta, e três lugares a mais
  para errar. `for...in` percorre nomes, não valores.
- `while` repete enquanto a condição valer; sem mudar a condição dentro,
  não termina.
- Acumulador: valor que começa antes do laço e muda dentro dele. `push`
  acrescenta à lista.
- `continue` pula, `break` sai. Todo item pulado precisa ter destino.
:::

:::exercise level=1
Com a lista do `totais.js`, escreva um laço que imprima só o código das
entregas com frete acima de R$ 20,00, e diga quantas linhas saem.

:::answer
```javascript
for (const e of entregas) {
  if (e.frete > 2000) {
    console.log(e.codigo);
  }
}
```

Uma linha: `E-5031`. O frete está em centavos, então R$ 20,00 é `2000`.
Comparar com `20` imprimiria as três.
:::

:::exercise level=2
Escreva o laço que acha a primeira entrega cancelada da lista e para.
Se nenhuma for cancelada, imprima "nenhuma cancelada".

:::answer
```javascript
let achada = null;

for (const e of entregas) {
  if (e.cancelada) {
    achada = e;
    break;
  }
}

console.log(achada ? achada.codigo : "nenhuma cancelada");
```

`achada` começa em `null` — "não encontrada ainda" — e só muda quando o
laço acha. O `break` evita ler o resto. Se a lista não tiver cancelada,
o laço termina sem mudar `achada`, e a última linha diz isso.
:::

:::exercise level=3
O painel antigo conta as entregas do dia assim:

```javascript
var total = 0;
for (var i = 1; i < entregas.length; i++) {
  total++;
}
```

A Lívia diz que o contador sempre marca uma a menos que o papel. Explique
por quê, corrija, e diga qual laço evita o erro de saída.

:::answer
O laço começa em `i = 1`. A primeira entrega está na posição `0`, e nunca
é contada. Com dez entregas, o contador dá nove.

Corrigido, `i` começa em `0`. Mas o laço inteiro é desnecessário: o total
é `entregas.length`. E, se fosse preciso percorrer, o `for...of` não tem
posição inicial para errar:

```javascript
let total = 0;
for (const e of entregas) {
  total++;
}
```

O erro de uma posição a menos — ou a mais — no `for` clássico é tão comum
que tem nome em inglês: *off by one*.
:::
